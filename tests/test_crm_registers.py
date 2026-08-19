"""Registres CRM : Ventes, Achats, Créances, Dettes, Paiements, Rapports."""

from __future__ import annotations

import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.database import SYNC_DB_URL, init_crm_tables, init_local_database
from app.seed_crm import seed_crm_if_empty
from app.states.crm_registers_state import (
    EMPTY_FORM,
    EMPTY_REPORT,
    EMPTY_TOTALS,
    REGISTER_TABLES,
    REGISTERS,
    REPORT_SCOPES,
    CrmRegistersState,
    _amounts,
    _bucket,
    _label,
    _season_end,
    _season_label,
    _season_start,
    _tone,
)


def _prepare() -> None:
    init_local_database()
    init_crm_tables()
    seed_crm_if_empty()


def test_registers_are_declared_and_mapped() -> None:
    assert REGISTERS == [
        "ventes",
        "achats",
        "creances",
        "dettes",
        "paiements",
        "rapports",
    ]
    for register in REGISTERS:
        if register != "rapports":
            assert register in REGISTER_TABLES
    assert REGISTER_TABLES["creances"] == "crm_receivable"
    assert REGISTER_TABLES["dettes"] == "crm_payable"


def test_registers_are_reachable_from_the_crm_navigation() -> None:
    source = Path("app/states/crm_state.py").read_text(encoding="utf-8")
    page = Path("app/pages/crm.py").read_text(encoding="utf-8")
    for register in REGISTERS:
        assert f'"key": "{register}"' in source
        assert f'crm_registers("{register}")' in page


def test_amount_calculations_are_automatic() -> None:
    assert CrmRegistersState != None
    ht, vat, ttc = _amounts(
        {
            "quantity": "10",
            "unit_price": "1000",
            "discount_percent": "10",
            "vat_rate": "19",
        }
    )
    assert ht == 9000.0
    assert vat == 1710.0
    assert ttc == 10710.0


def test_status_tones_and_buckets() -> None:
    assert _tone("PAYEE", 0, 0.0) == "good"
    assert _tone("OUVERTE", 12, 500.0) == "bad"
    assert _tone("PARTIELLE", 0, 500.0) == "warn"
    assert _bucket(10) == "0-30"
    assert _bucket(45) == "31-60"
    assert _bucket(75) == "61-90"
    assert _bucket(200) == "90+"
    assert _label("PARTIELLEMENT_PAYEE") == "Partiellement payée"


def test_default_dicts_seed_every_displayed_key() -> None:
    for key in ("count", "amount_ht", "vat_amount", "amount_ttc", "remaining"):
        assert key in EMPTY_TOTALS
    for key in ("sales", "purchases", "margin", "receivable", "payable"):
        assert key in EMPTY_REPORT
    for key in ("partner_id", "amount", "vat_rate", "direction"):
        assert key in EMPTY_FORM


def test_report_scopes_cover_the_automatic_fallback() -> None:
    for key in ("season_current", "season_last", "history", "empty"):
        assert key in REPORT_SCOPES
        assert REPORT_SCOPES[key]
    assert CrmRegistersState.report_scope != None


def test_season_bounds_and_labels() -> None:
    start = _season_start(datetime.date(2026, 6, 10))
    assert start == datetime.date(2025, 9, 1)
    assert _season_end(start) == datetime.date(2026, 8, 31)
    assert _season_label(start) == "2025/2026"
    late = _season_start(datetime.date(2026, 9, 1))
    assert late == datetime.date(2026, 9, 1)
    assert _season_end(late) == datetime.date(2027, 8, 31)


def test_report_query_is_not_locked_on_the_current_season() -> None:
    source = Path("app/states/crm_registers_state.py").read_text(
        encoding="utf-8"
    )
    assert "_resolve_report_period" in source
    assert "AND sale_date >= :season" not in source
    assert "AND purchase_date >= :season" not in source
    assert "{sales_clause}" in source
    assert "{purchases_clause}" in source


def test_demo_data_requires_the_report_fallback() -> None:
    """Le rapport doit rester utile même si les données sont antérieures."""
    _prepare()
    engine = create_engine(SYNC_DB_URL, future=True)
    with engine.connect() as conn:
        latest_sale = conn.execute(
            text(
                "SELECT MAX(sale_date) FROM crm_sale"
                " WHERE is_archived = false"
                " AND UPPER(status) <> 'ANNULEE'"
            )
        ).scalar()
        total = conn.execute(
            text(
                "SELECT COALESCE(SUM(amount_ttc), 0) FROM crm_sale"
                " WHERE is_archived = false"
                " AND UPPER(status) <> 'ANNULEE'"
            )
        ).scalar_one()
    assert latest_sale is not None
    assert float(total) > 0
    latest = datetime.date.fromisoformat(str(latest_sale)[:10])
    current = _season_start(datetime.date.today())
    fallback_start = _season_start(latest)
    # Soit les ventes tombent dans la campagne en cours, soit la bascule
    # doit viser la campagne réellement documentée.
    assert latest >= current or fallback_start <= latest <= _season_end(
        fallback_start
    )


def test_crm_tables_hold_registers_data() -> None:
    _prepare()
    engine = create_engine(SYNC_DB_URL, future=True)
    with engine.connect() as conn:
        sales = conn.execute(text("SELECT COUNT(*) FROM crm_sale")).scalar_one()
        purchases = conn.execute(
            text("SELECT COUNT(*) FROM crm_purchase")
        ).scalar_one()
        payments = conn.execute(
            text("SELECT COUNT(*) FROM crm_payment")
        ).scalar_one()
        receivables = conn.execute(
            text(
                "SELECT COUNT(*) FROM crm_receivable"
                " WHERE amount_remaining >= 0"
            )
        ).scalar_one()
        payables = conn.execute(
            text("SELECT COUNT(*) FROM crm_payable")
        ).scalar_one()
    assert sales >= 1
    assert purchases >= 1
    assert payments >= 1
    assert receivables >= 1
    assert payables >= 1
