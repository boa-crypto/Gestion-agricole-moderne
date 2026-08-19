"""Vérifie la vue générale CRM : agrégats SQL, alertes et synthèse locale."""

from __future__ import annotations

import asyncio
import datetime

from sqlalchemy import create_engine, text

from app.database import SYNC_DB_URL, init_crm_tables, init_local_database
from app.seed_crm import seed_crm_if_empty
from app.states.crm_state import (
    CLIENT_KINDS_SQL,
    SUPPLIER_KINDS_SQL,
    CrmState,
    _month_keys,
)


def _prepare() -> None:
    init_local_database()
    init_crm_tables()
    seed_crm_if_empty()


def test_month_keys_span_twelve_months() -> None:
    keys = _month_keys(datetime.date(2026, 3, 15))
    assert len(keys) == 12
    assert keys[-1] == "2026-03"
    assert keys[0] == "2025-04"


def test_kind_filters_match_persisted_partners() -> None:
    _prepare()
    engine = create_engine(SYNC_DB_URL, future=True)
    with engine.connect() as conn:
        clients = conn.execute(
            text(
                "SELECT COUNT(*) FROM crm_partner"
                f" WHERE is_archived = false AND UPPER(kind) IN {CLIENT_KINDS_SQL}"
            )
        ).scalar_one()
        suppliers = conn.execute(
            text(
                "SELECT COUNT(*) FROM crm_partner"
                f" WHERE is_archived = false AND UPPER(kind) IN {SUPPLIER_KINDS_SQL}"
            )
        ).scalar_one()
        turnover = conn.execute(
            text(
                "SELECT COALESCE(SUM(amount_ttc), 0) FROM crm_sale"
                " WHERE is_archived = false AND UPPER(status) <> 'ANNULEE'"
            )
        ).scalar_one()
    engine.dispose()
    assert clients >= 1
    assert suppliers >= 1
    assert float(turnover) > 0


def test_insights_are_built_from_aggregates() -> None:
    state = CrmState(_reflex_internal_init=True)
    state.kpis = {
        **state.kpis,
        "turnover_season": 1000.0,
        "purchases_season": 600.0,
        "margin": 400.0,
        "margin_rate": 40.0,
        "receivable": 500.0,
        "receivable_overdue": 250.0,
        "payable": 200.0,
        "credit_alerts": 1.0,
    }
    state.months = [
        {
            "key": "2026-01",
            "label": "janv. 26",
            "sales": 800.0,
            "purchases": 100.0,
            "sales_width": "100%",
            "purchases_width": "12%",
        }
    ]
    state._build_insights()
    titles = [item["title"] for item in state.insights]
    assert titles.contains("Équilibre commercial de la campagne")
    assert titles.contains("Recouvrement clients")
    assert titles.contains("Limites de crédit")
    assert [
        item for item in state.insights if "janv" in item["detail"]
    ].length() > 0


def test_state_tabs_cover_navigation() -> None:
    state = CrmState(_reflex_internal_init=True)
    assert [tab["key"] for tab in state.tabs] == [
        "synthese",
        "graphiques",
        "clients",
        "fournisseurs",
        "partenaires",
        "tiers",
        "alertes",
        "recherche",
    ]


def test_prepare_is_idempotent() -> None:
    asyncio.run(asyncio.sleep(0))
    _prepare()
    _prepare()
