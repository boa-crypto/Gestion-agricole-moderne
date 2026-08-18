import asyncio
import json

from test_utils import run_event
from app.states.cartography_state import CartographyState


async def main():
    print("=== Test espace cartographie interactive ===")
    state = CartographyState()
    await run_event(state.load_map)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.shapes.length() > 0, "Les contours doivent être chargés"
    assert state.selected_parcel_id > 0, "Une parcelle doit être sélectionnée"
    first = state.shapes[0]
    assert first["positions"].length() >= 4, "Le contour doit avoir des sommets"

    await run_event(state.select_parcel, first["id"])
    assert state.parcel_detail["code"] != "—", "La fiche doit être remplie"

    center = first["center"]
    await run_event(
        state.handle_map_click,
        {"latlng": {"lat": center["lat"], "lng": center["lng"]}},
    )
    assert state.selected_parcel_id > 0, "Le clic carte doit sélectionner"

    await run_event(state.generate_draft)
    assert state.geojson_draft != "", "Un contour doit être proposé"

    await run_event(
        state.submit_geometry,
        {
            "geojson": state.geojson_draft,
            "author": "Test automatique",
            "geometry_notes": "Contour de test",
        },
    )
    if state.geometry_ready:
        assert state.geometry_error == "", (
            f"Le contour doit être accepté : {state.geometry_error}"
        )

    await run_event(
        state.submit_geometry,
        {"geojson": "{pas du json}", "author": "Test"},
    )
    assert state.geometry_error != "", "Un JSON invalide doit être refusé"

    await run_event(
        state.submit_geometry,
        {
            "geojson": json.dumps(
                {"type": "Point", "coordinates": [1.8, 48.2]}
            ),
            "author": "Test",
        },
    )
    assert state.geometry_error != "", "Un Point doit être refusé"

    await run_event(state.set_search, "Grands")
    assert state.shapes.length() >= 1, "La recherche doit trouver un îlot"
    await run_event(state.reset_filters)
    assert state.search == "", "Les filtres doivent être réinitialisés"

    print(
        f"✓ Îlots : {state.shapes.length()}, contours : {state.mapped_count}, interventions : {state.interventions.length()}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())
