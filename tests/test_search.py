from test_utils import run_event
from app.states.search_state import SPECS, SearchState
import asyncio
import datetime


async def main():
    print("=== Test recherche globale ===")
    state = SearchState()
    await run_event(state.load_search)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.error == "", "Aucune erreur au chargement"
    assert state.chips.length() == len(SPECS) + 1, (
        "Chaque table doit avoir sa puce de filtre"
    )
    assert state.total_results > 0, (
        "Le balayage complet doit remonter des lignes"
    )
    assert state.sections.length() > 0, "Des sections doivent être affichées"

    await run_event(state.set_term, "blé")
    assert state.error == "", "La recherche par mot-clé doit être valide"
    assert state.total_results > 0, "Le mot-clé doit trouver des instances"

    await run_event(state.set_entity_filter, "culture")
    assert state.sections.length() <= 1, (
        "Le filtre par type doit restreindre les sections"
    )
    for section in state.sections:
        assert section["kind"] == "culture", (
            "Seules les cultures doivent rester affichées"
        )

    await run_event(state.set_entity_filter, "TOUS")
    today = datetime.date.today()
    await run_event(state.set_period, "30")
    assert state.start_date != "", "Le raccourci doit remplir la date de début"
    assert state.end_date == today.isoformat(), (
        "Le raccourci doit remplir la date de fin"
    )

    await run_event(state.set_start_date, today.isoformat())
    await run_event(
        state.set_end_date, (today - datetime.timedelta(days=5)).isoformat()
    )
    assert state.error != "", "Une plage inversée doit produire une erreur"

    await run_event(state.reset_search)
    assert state.error == "", "La réinitialisation doit effacer l'erreur"
    assert state.term == "", "Le mot-clé doit être vidé"
    assert (state.start_date == "") & (state.end_date == ""), (
        "Les dates doivent être vidées"
    )
    assert state.entity_filter == "TOUS", "Le périmètre doit être complet"
    assert state.total_results > 0, "Le balayage complet doit revenir"

    print(
        f"✓ {state.total_results} instances sur {state.tables_touched} tables, "
        f"{state.sections.length()} sections"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())
