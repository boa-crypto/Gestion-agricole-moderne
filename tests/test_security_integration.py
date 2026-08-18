"""Vérifie l'intégration transversale du module utilisateurs AgriPro."""

import asyncio

from test_utils import run_event

from app.access_control import user_by_matricule
from app.admin_users import ensure_admin_data, load_journal
from app.exports import to_csv
from app.security_audit import load_security_audit, load_security_events
from app.states.administration_state import AdministrationState
from app.states.search_state import SPEC_BY_KEY, SearchState
from app.states.security_audit_state import SecurityAuditState


async def main():
    print("=== Test intégration sécurité / recherche / audit ===")
    await ensure_admin_data()

    # --- Audit sécurité ---------------------------------------------------
    kpis, findings = await load_security_audit()
    assert kpis["users"] > 0, kpis
    assert kpis["roles"] > 0 and kpis["permissions"] > 0, kpis
    assert kpis["rbac_coverage"] > 0, kpis
    assert len(findings) >= 1, findings
    for item in findings:
        assert item["recommendation"] != ""
        assert item["tone"] in ("good", "warn", "bad", "info")
    events = await load_security_events(10)
    assert all(e["sensitive"] or e["kind"] != "" for e in events)

    security = SecurityAuditState()
    await run_event(security.load_security)
    assert security.is_loading is False
    assert security.finding_count >= 1
    assert security.verdict_label != ""

    # --- Journal filtrable ------------------------------------------------
    full = await load_journal(limit=100)
    assert len(full) >= 1, full
    sensitive = await load_journal(sensitive_only=True, limit=100)
    assert len(sensitive) <= len(full)
    assert all(item["sensitive"] for item in sensitive)
    typed = await load_journal(kind="REFUS", limit=100)
    assert all(item["kind"] == "REFUS" for item in typed)

    # --- Recherche transversale ------------------------------------------
    for key in ("utilisateur", "role", "equipe", "permission", "journal"):
        assert key in SPEC_BY_KEY, key

    search = SearchState()
    await run_event(search.load_search)
    assert search.error == "", search.error
    counts = {chip["value"]: chip["count"] for chip in search.chips}
    assert counts["utilisateur"] > 0, counts
    assert (counts["role"] > 0) & (counts["permission"] > 0), counts
    assert (counts["equipe"] > 0) & (counts["journal"] > 0), counts

    await run_event(search.set_entity_filter, "utilisateur")
    for section in search.sections:
        assert section["kind"] == "utilisateur"
    await run_event(search.reset_search)

    # --- Administration : filtres journal + exports + contrôles ----------
    state = AdministrationState()
    await run_event(state.load_administration)
    assert state.journal_count >= 1
    await run_event(state.toggle_journal_sensitive)
    assert state.journal_sensitive_only is True
    assert state.journal_sensitive_count == state.journal_count
    await run_event(state.set_journal_search, "compte")
    await run_event(state.reset_journal_filters)
    assert (state.journal_kind == "TOUS") & (state.journal_search == "")
    assert state.journal_filter_label == "Tout le journal"

    users_csv = to_csv(["a"], [["1"]])
    assert users_csv.startswith("a")

    # Contrôle serveur : impossible d'agir sur son propre compte.
    owner = await user_by_matricule("U001")
    assert owner > 0
    await run_event(state.set_user_status, owner, "SUSPENDU")
    assert state.error != "", "Le contrôle serveur doit refuser l'action"

    target = await user_by_matricule("U006")
    await run_event(state.set_user_status, target, "SUSPENDU")
    assert state.error == "", state.error
    await run_event(state.set_user_status, target, "ACTIF")
    assert state.error == "", state.error

    print(
        f"✓ {kpis['users']:.0f} comptes, MFA {kpis['mfa_coverage']:.0f}%, "
        f"{len(findings)} constat(s), journal {state.journal_count} lignes, "
        f"{counts['utilisateur']} utilisateur(s) retrouvés en recherche"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())
