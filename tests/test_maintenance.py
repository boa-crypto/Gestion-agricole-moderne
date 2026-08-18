from test_utils import run_event
from app.states.maintenance_state import MaintenanceState
import asyncio
import datetime


async def main():
    print("=== Test espace maintenance des engins ===")
    state = MaintenanceState()
    await run_event(state.load_fleet)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.equipments.length() > 0, "La flotte doit être alimentée"
    assert state.selected_equipment_id > 0, "Un engin doit être sélectionné"
    assert state.operations.length() > 0, (
        "Le journal de maintenance doit être alimenté"
    )
    assert state.deadlines.length() > 0, (
        "Le planning d'échéances doit être alimenté"
    )
    assert state.employee_options.length() > 0, (
        "Les responsables doivent être disponibles"
    )

    await run_event(state.set_search, "Tracteur")
    assert state.equipments.length() >= 1, "La recherche doit trouver un engin"
    await run_event(state.reset_filters)
    assert state.search == "", "Les filtres doivent être réinitialisés"

    today = datetime.date.today()
    await run_event(state.open_equipment_create)
    assert state.show_equipment_form is True, (
        "Le formulaire engin doit s'ouvrir"
    )
    form = {
        "name": "Tracteur de test",
        "code": "M99",
        "category": "TRACTEUR",
        "status": "DISPONIBLE",
        "ownership": "PROPRIETE",
        "brand": "Testeur",
        "model": "T-99",
        "serial_number": "TST-99",
        "registration": "ZZ-999-ZZ",
        "year": str(today.year),
        "power_hp": "120",
        "working_width_m": "0",
        "usage_unit": "HEURES",
        "usage_counter": "100",
        "purchase_date": today.isoformat(),
        "purchase_price": "50000",
        "residual_value": "40000",
        "hourly_cost": "25",
        "fuel_consumption_l_h": "10",
        "storage_location": "Hangar test",
        "responsible_id": state.employee_options[0]["value"],
        "insurance_expiry": (today + datetime.timedelta(days=200)).isoformat(),
        "inspection_expiry": "",
        "next_service_date": (today + datetime.timedelta(days=20)).isoformat(),
        "next_service_counter": "600",
        "service_interval_days": "180",
        "service_interval_counter": "500",
        "notes": "Créé par test fonctionnel",
    }
    await run_event(state.submit_equipment, form)
    assert state.show_equipment_form is False, (
        "Le formulaire engin doit se fermer"
    )
    assert state.equipment_detail["name"] == "Tracteur de test", (
        "La fiche créée doit être sélectionnée"
    )

    await run_event(state.open_operation_create)
    operation = {
        "equipment_id": state.selected_equipment_id.to_string(),
        "schedule_id": "",
        "title": "Révision de test 100 h",
        "kind": "PREVENTIVE",
        "status": "PLANIFIEE",
        "priority": "NORMALE",
        "scheduled_date": today.isoformat(),
        "due_date": (today + datetime.timedelta(days=3)).isoformat(),
        "done_date": "",
        "counter_at_service": "100",
        "downtime_hours": "3",
        "labor_hours": "2",
        "labor_cost": "50",
        "parts_cost": "120",
        "external_cost": "0",
        "is_internal": "1",
        "provider": "",
        "invoice_reference": "",
        "responsible_id": state.employee_options[0]["value"],
        "failure_description": "",
        "work_performed": "",
        "notes": "Test",
    }
    await run_event(state.submit_operation, operation)
    assert state.show_operation_form is False, (
        "Le formulaire opération doit se fermer"
    )
    created_operations = [
        operation
        for operation in state.operations
        if operation["title"] == "Révision de test 100 h"
    ]
    assert created_operations.length() > 0, (
        "L'opération créée doit apparaître au journal"
    )

    operation_id = created_operations[0]["id"]
    cost_form = {
        "maintenance_id": operation_id.to_string(),
        "type": "PIECE",
        "label": "Filtre à huile test",
        "reference": "FLT-99",
        "supplier": "AgriParts",
        "quantity": "2",
        "unit": "u",
        "unit_price": "30",
        "incurred_on": today.isoformat(),
    }
    await run_event(state.submit_cost, cost_form)
    assert state.cost_error == "", "La ligne de coût doit être acceptée"
    assert state.costs.length() >= 1, "La ligne de coût doit apparaître"

    usage_form = {
        "used_on": today.isoformat(),
        "employee_id": state.employee_options[0]["value"],
        "counter_start": "100",
        "counter_end": "108",
        "fuel_liters": "60",
        "notes": "Relevé de test",
    }
    await run_event(state.submit_usage, usage_form)
    assert state.usage_error == "", "Le relevé doit être accepté"
    assert state.usage_logs.length() >= 1, "Le relevé d'usage doit apparaître"

    await run_event(state.mark_operation_done, operation_id)
    print(
        f"✓ Engins : {state.equipments.length()}, opérations : {state.operations.length()}, échéances : {state.deadlines.length()}, alertes : {state.fleet_alerts.length()}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())
