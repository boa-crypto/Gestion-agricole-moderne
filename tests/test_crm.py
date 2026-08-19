"""Tests du socle métier CRM & Partenaires (modèles + règles + semis)."""

from __future__ import annotations

import datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.crm_rules import (
    aging_bucket,
    archive_partner,
    can_delete_partner,
    compute_line_amounts,
    compute_partner_balances,
    compute_score,
    derive_settlement_status,
    find_duplicate_partner,
    grade_for_score,
    next_partner_code,
    overdue_days,
    refresh_settlements,
    validate_fiscal_identifiers,
)
from app.database import CRM_MODELS
from app.models import (
    Base,
    CrmAuditLog,
    CrmContact,
    CrmDocument,
    CrmDocumentLink,
    CrmEvent,
    CrmInvoice,
    CrmPartner,
    CrmPayable,
    CrmPayment,
    CrmReceivable,
    CrmSale,
    CrmScore,
    CrmScoreKind,
    InvoiceKind,
    InvoiceStatus,
    PartnerKind,
    PartnerStatus,
    PaymentDirection,
    SettlementStatus,
)
from app.seed_crm import crm_integrity_report, crm_is_seeded, seed_crm

TODAY = datetime.date(2026, 6, 30)


def _session() -> Session:
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_crm_models_are_registered() -> None:
    names = {model.__tablename__ for model in CRM_MODELS}
    assert "crm_partner" in names
    assert "crm_receivable" in names and "crm_payable" in names
    assert len(CRM_MODELS) == 16


def test_line_amounts_and_aging() -> None:
    assert compute_line_amounts(10, 100, 10, 19) == (900.0, 171.0, 1071.0)
    assert compute_line_amounts(0, 0) == (0.0, 0.0, 0.0)
    assert (
        overdue_days(
            TODAY - datetime.timedelta(days=45), remaining=10, today=TODAY
        )
        == 45
    )
    assert overdue_days(TODAY, remaining=0, today=TODAY) == 0
    assert aging_bucket(10) == "0-30"
    assert aging_bucket(75) == "61-90"
    assert aging_bucket(400) == "90+"


def test_settlement_status_rules() -> None:
    future = TODAY + datetime.timedelta(days=10)
    past = TODAY - datetime.timedelta(days=10)
    assert derive_settlement_status(100, 100, past, today=TODAY) is (
        SettlementStatus.REGLEE
    )
    assert derive_settlement_status(100, 40, past, today=TODAY) is (
        SettlementStatus.EN_RETARD
    )
    assert derive_settlement_status(100, 40, future, today=TODAY) is (
        SettlementStatus.PARTIELLE
    )
    assert derive_settlement_status(100, 0, future, today=TODAY) is (
        SettlementStatus.OUVERTE
    )


def test_fiscal_validation_and_scoring() -> None:
    assert validate_fiscal_identifiers(nif="123", email="bad") != []
    assert (
        validate_fiscal_identifiers(nif="0123456789012345", email="a@b.dz")
        == []
    )
    client = compute_score(
        CrmScoreKind.CLIENT,
        turnover_amount=5_000_000,
        transaction_count=6,
        seniority_days=730,
        average_payment_delay_days=20,
        agreed_delay_days=30,
        margin_ratio=0.2,
        growth_ratio=0.1,
    )
    assert 0 <= client["total_score"] <= 100
    assert client["quality_score"] == 0
    supplier = compute_score(
        CrmScoreKind.FOURNISSEUR,
        turnover_amount=1_000_000,
        transaction_count=4,
        quality_ratio=0.9,
        lead_time_days=4,
        incident_count=1,
    )
    assert supplier["profitability_score"] == 0
    assert grade_for_score(90).value == "excellent"
    assert grade_for_score(10).value == "risque"


def test_seed_is_idempotent_and_consistent() -> None:
    with _session() as session:
        assert crm_is_seeded(session) is False
        seed_crm(session, today=TODAY)
        assert crm_is_seeded(session) is True

        # Aucun lien nul ni orphelin dans tout le graphe CRM.
        assert crm_integrity_report(session) == []

        partners = session.execute(select(CrmPartner)).scalars().all()
        assert len(partners) == 7
        assert all(partner.id is not None for partner in partners)
        assert all(partner.code for partner in partners)
        assert len({partner.code for partner in partners}) == len(partners)

        # Un second semis conditionnel ne doit rien réécrire.
        before = session.execute(
            select(func.count()).select_from(CrmPartner)
        ).scalar()
        if not crm_is_seeded(session):
            seed_crm(session, today=TODAY)
        after = session.execute(
            select(func.count()).select_from(CrmPartner)
        ).scalar()
        assert before == after

        # Ventes, achats, factures, règlements et timeline sont présents.
        assert (
            session.execute(select(func.count()).select_from(CrmSale)).scalar()
            == 3
        )
        assert (
            session.execute(
                select(func.count()).select_from(CrmInvoice)
            ).scalar()
            == 7
        )
        assert (
            session.execute(
                select(func.count()).select_from(CrmReceivable)
            ).scalar()
            == 3
        )
        assert (
            session.execute(
                select(func.count()).select_from(CrmPayable)
            ).scalar()
            == 4
        )
        assert (
            session.execute(select(func.count()).select_from(CrmEvent)).scalar()
            > 10
        )
        assert (
            session.execute(select(func.count()).select_from(CrmScore)).scalar()
            == 7
        )
        assert (
            session.execute(
                select(func.count()).select_from(CrmAuditLog)
            ).scalar()
            == 7
        )

        # Chaque contact, ligne et règlement pointe vers un tiers existant.
        partner_ids = {partner.id for partner in partners}
        contact_partner_ids = (
            session.execute(select(CrmContact.partner_id)).scalars().all()
        )
        assert contact_partner_ids
        assert all(value in partner_ids for value in contact_partner_ids)

        # Totaux de facture cohérents avec les lignes.
        invoice = (
            session.execute(
                select(CrmInvoice).where(CrmInvoice.kind == InvoiceKind.VENTE)
            )
            .scalars()
            .first()
        )
        assert invoice is not None
        assert round(
            float(invoice.amount_ht) + float(invoice.vat_amount), 2
        ) == round(float(invoice.amount_ttc), 2)
        assert float(invoice.remaining_amount) >= 0


def test_balances_settlements_and_archiving() -> None:
    with _session() as session:
        seed_crm(session, today=TODAY)
        partner = (
            session.execute(
                select(CrmPartner).where(
                    CrmPartner.kind == PartnerKind.GROSSISTE
                )
            )
            .scalars()
            .one()
        )

        balances = compute_partner_balances(session, partner.id, today=TODAY)
        assert balances["turnover"] > 0
        assert balances["receivable"] > 0
        assert balances["net_balance"] == round(
            balances["receivable"] - balances["payable"], 2
        )

        invoice = (
            session.execute(
                select(CrmInvoice).where(CrmInvoice.partner_id == partner.id)
            )
            .scalars()
            .one()
        )
        assert invoice.status in (
            InvoiceStatus.EMISE,
            InvoiceStatus.EN_RETARD,
        )

        # Règlement intégral : la créance passe à « réglée ».
        session.add(
            CrmPayment(
                partner_id=partner.id,
                code="PAY-TEST-0001",
                direction=PaymentDirection.ENCAISSEMENT,
                invoice_id=invoice.id,
                paid_on=TODAY,
                amount=float(invoice.amount_ttc),
            )
        )
        session.flush()
        receivable = refresh_settlements(session, invoice, today=TODAY)
        assert receivable.status is SettlementStatus.REGLEE
        assert float(receivable.amount_remaining) == 0
        assert invoice.status is InvoiceStatus.PAYEE

        # Archivage plutôt que suppression.
        assert can_delete_partner(session, partner.id) is False
        archive_partner(session, partner, reason="Fin de relation", today=TODAY)
        session.flush()
        assert partner.is_archived is True
        assert partner.status is PartnerStatus.ARCHIVE
        assert (
            session.execute(
                select(func.count()).select_from(CrmPartner)
            ).scalar()
            == 7
        )


def test_document_links_are_bound_to_documents() -> None:
    with _session() as session:
        seed_crm(session, today=TODAY)
        links = session.execute(select(CrmDocumentLink)).scalars().all()
        assert links
        document_ids = set(
            session.execute(select(CrmDocument.id)).scalars().all()
        )
        sale_ids = set(session.execute(select(CrmSale.id)).scalars().all())
        invoice_ids = set(
            session.execute(select(CrmInvoice.id)).scalars().all()
        )
        for link in links:
            assert link.document_id in document_ids
            assert link.sale_id in sale_ids
            assert link.invoice_id in invoice_ids
            assert link.payment_id is None

        # Une référence orpheline doit être détectée avant validation.
        links[0].payment_id = 999_999
        session.flush()
        anomalies = crm_integrity_report(session)
        assert any("crm_document_link.payment_id" in item for item in anomalies)


def test_codes_and_duplicate_detection() -> None:
    with _session() as session:
        first = next_partner_code(session, PartnerKind.CLIENT)
        assert first == "CLI-0001"
        session.add(
            CrmPartner(
                code=first,
                legal_name="Ferme Test",
                kind=PartnerKind.CLIENT,
                email="test@ferme.dz",
                phone="+213600000000",
            )
        )
        session.flush()
        assert next_partner_code(session, PartnerKind.CLIENT) == "CLI-0002"
        assert next_partner_code(session, PartnerKind.FOURNISSEUR) == "FRN-0001"
        assert (
            find_duplicate_partner(session, legal_name="ferme test") is not None
        )
        assert (
            find_duplicate_partner(session, email="test@ferme.dz") is not None
        )
        assert find_duplicate_partner(session, email="autre@ferme.dz") is None
