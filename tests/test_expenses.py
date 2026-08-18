from test_utils import run_event
from app.states.expenses_state import ExpensesState
import asyncio
import datetime


async def main():
    print("=== Test registre des charges et dépenses ===")
    state = ExpensesState()
    await run_event(state.load_expenses)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.types.length() > 0, "Les types de dépenses doivent exister"
    assert state.expenses.length() > 0, "Des dépenses doivent être amorcées"
    assert state.kpis["total_ttc"] > 0, "Le cumul TTC doit être positif"
    assert state.months.length() > 0, "La synthèse mensuelle doit être remplie"
    assert state.type_options.length() > 0, "Des types actifs doivent exister"

    await run_event(state.set_search, "carburant")
    assert state.error == "", "La recherche doit rester valide"
    await run_event(state.reset_filters)
    assert state.search == "", "Les filtres doivent être réinitialisés"

    await run_event(state.set_status_filter, "PAYEE")
    for row in state.expenses:
        assert row["status"] == "PAYEE", "Le filtre de statut doit s'appliquer"
    await run_event(state.reset_filters)

    today = datetime.date.today()
    await run_event(state.set_start_date, today.isoformat())
    await run_event(
        state.set_end_date, (today - datetime.timedelta(days=10)).isoformat()
    )
    assert state.error != "", "Une plage inversée doit être signalée"
    await run_event(state.reset_filters)

    # Création d'un type puis d'une dépense.
    await run_event(state.open_type_create)
    await run_event(
        state.submit_type,
        {
            "name": "Type de test",
            "code": "TST",
            "category": "Test",
            "description": "Type créé par le test fonctionnel.",
            "color_hex": "#a3e635",
            "icon": "receipt-text",
            "default_payment_method": "VIREMENT",
            "default_vat_rate": "20",
            "notes": "",
        },
    )
    assert state.type_error == "", "Le type doit être accepté"
    created_types = [t for t in state.types if t["name"] == "Type de test"]
    assert created_types.length() == 1, "Le type créé doit apparaître"
    type_id = created_types[0]["id"]

    await run_event(state.open_expense_create)
    bad = {
        "expense_type_id": type_id.to_string(),
        "label": "Dépense invalide",
        "supplier": "Test",
        "reference": "",
        "invoice_reference": "",
        "status": "ENGAGEE",
        "payment_method": "VIREMENT",
        "quantity": "1",
        "unit": "u",
        "amount_ht": "-10",
        "vat_rate": "20",
        "incurred_on": today.isoformat(),
        "due_date": "",
        "paid_on": "",
        "parcel_id": "",
        "crop_id": "",
        "employee_id": "",
        "equipment_id": "",
        "intervention_id": "",
        "maintenance_id": "",
        "notes": "",
    }
    await run_event(state.submit_expense, bad)
    assert state.expense_error != "", "Un montant négatif doit être refusé"

    good = bad.copy()
    good["label"] = "Dépense de test"
    good["amount_ht"] = "100"
    good["due_date"] = (today + datetime.timedelta(days=15)).isoformat()
    await run_event(state.submit_expense, good)
    assert state.expense_error == "", "La dépense valide doit être acceptée"
    created = [e for e in state.expenses if e["label"] == "Dépense de test"]
    assert created.length() == 1, "La dépense créée doit apparaître"
    expense_id = created[0]["id"]
    assert created[0]["amount_ttc"] == 120.0, "Le TTC doit être calculé"

    await run_event(state.mark_paid, expense_id)
    paid = [e for e in state.expenses if e["id"] == expense_id]
    assert paid[0]["status"] == "PAYEE", "La dépense doit passer en payée"

    await run_event(state.cancel_expense, expense_id)
    cancelled = [e for e in state.expenses if e["id"] == expense_id]
    assert cancelled[0]["is_cancelled"] is True, "La dépense doit être annulée"

    await run_event(state.archive_expense, expense_id)
    remaining = [e for e in state.expenses if e["id"] == expense_id]
    assert remaining.length() == 0, "La dépense archivée doit être masquée"
    await run_event(state.toggle_archived)
    archived = [e for e in state.expenses if e["id"] == expense_id]
    assert archived.length() == 1, "Les archives doivent être consultables"
    await run_event(state.restore_expense, expense_id)
    await run_event(state.toggle_archived)

    await run_event(state.toggle_type_active, type_id)
    await run_event(state.archive_type, type_id)
    archived_types = [t for t in state.types if t["id"] == type_id]
    assert archived_types.length() == 1, "Le type archivé reste consultable"

    print(
        f"✓ {state.expense_count} dépenses, {state.type_count} types, "
        f"{state.kpis['total_ttc']:.0f} € TTC filtrés"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())
