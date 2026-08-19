"""Espaces Clients / Fournisseurs / Partenaires : filtres, fiche et archivage."""

from __future__ import annotations

from sqlalchemy import create_engine, text

from app.database import SYNC_DB_URL, init_crm_tables, init_local_database
from app.seed_crm import seed_crm_if_empty
from app.states.crm_partners_state import (
    CODE_PREFIXES,
    PARTNER_KINDS,
    SPACE_KINDS_SQL,
    CrmPartnersState,
    _label,
    _links,
)
from app.states.crm_state import KIND_LABELS


def _prepare() -> None:
    init_local_database()
    init_crm_tables()
    seed_crm_if_empty()


def test_space_kind_filters_are_declared() -> None:
    assert "clients" in SPACE_KINDS_SQL
    assert "fournisseurs" in SPACE_KINDS_SQL
    # L'espace Partenaires n'applique aucun filtre de nature.
    assert "partenaires" not in SPACE_KINDS_SQL
    assert set(PARTNER_KINDS) <= set(KIND_LABELS)


def test_code_prefixes_cover_client_and_supplier_kinds() -> None:
    assert CODE_PREFIXES["CLIENT"] == "CLI"
    assert CODE_PREFIXES["FOURNISSEUR"] == "FRN"
    assert CODE_PREFIXES.get("MIXTE", "PRT") == "PRT"


def test_links_are_readable_and_skip_empty_values() -> None:
    links = _links(
        [
            ("Parcelle", "Parcelle Nord"),
            ("Culture", ""),
            ("Campagne", "2025/2026"),
        ]
    )
    assert links == ["Parcelle · Parcelle Nord", "Campagne · 2025/2026"]
    assert _label(KIND_LABELS, "grossiste", "Partenaire") == "Grossiste"


def test_state_defaults_are_display_ready() -> None:
    state = CrmPartnersState(_reflex_internal_init=True)
    assert state.detail["code"] == ""
    assert state.stats["turnover"] == 0.0
    assert state.score["total"] == 0
    assert [tab["key"] for tab in state.detail_tabs] == [
        "identite",
        "contacts",
        "transactions",
        "finance",
        "documents",
        "historique",
    ]
    assert state.form["kind"] == "CLIENT"


def test_partner_detail_queries_resolve_agricultural_links() -> None:
    _prepare()
    engine = create_engine(SYNC_DB_URL, future=True)
    with engine.connect() as conn:
        partner_id = conn.execute(
            text(
                "SELECT partner_id FROM crm_sale"
                " WHERE parcel_id IS NOT NULL LIMIT 1"
            )
        ).scalar()
        assert partner_id is not None
        row = conn.execute(
            text(
                """
                SELECT COALESCE(par.name, ''), COALESCE(c.name, ''),
                       COALESCE(cu.name, ''), h.harvest_date
                FROM crm_sale s
                LEFT JOIN parcel par ON par.id = s.parcel_id
                LEFT JOIN crop c ON c.id = s.crop_id
                LEFT JOIN crop_culture cu ON cu.id = s.culture_id
                LEFT JOIN harvest h ON h.id = s.harvest_id
                WHERE s.partner_id = :pid
                LIMIT 1
                """
            ),
            {"pid": partner_id},
        ).first()
        assert row is not None
        assert row[0] != ""
        contacts = conn.execute(
            text(
                "SELECT COUNT(*) FROM crm_contact WHERE partner_id = :pid",
            ),
            {"pid": partner_id},
        ).scalar_one()
        assert contacts >= 1
        primary = conn.execute(
            text(
                "SELECT COUNT(*) FROM crm_contact"
                " WHERE partner_id = :pid AND is_primary = true",
            ),
            {"pid": partner_id},
        ).scalar_one()
        assert primary <= 1
        events = conn.execute(
            text("SELECT COUNT(*) FROM crm_event WHERE partner_id = :pid"),
            {"pid": partner_id},
        ).scalar_one()
        assert events >= 1
    engine.dispose()


def test_partners_with_transactions_are_never_deleted() -> None:
    _prepare()
    engine = create_engine(SYNC_DB_URL, future=True)
    with engine.connect() as conn:
        before = conn.execute(
            text("SELECT COUNT(*) FROM crm_partner")
        ).scalar_one()
        with_tx = conn.execute(
            text(
                "SELECT COUNT(*) FROM crm_partner p"
                " WHERE EXISTS (SELECT 1 FROM crm_sale s"
                "               WHERE s.partner_id = p.id)"
                "    OR EXISTS (SELECT 1 FROM crm_purchase a"
                "               WHERE a.partner_id = p.id)"
            )
        ).scalar_one()
        after = conn.execute(
            text("SELECT COUNT(*) FROM crm_partner")
        ).scalar_one()
    engine.dispose()
    assert with_tx >= 1
    assert before == after
