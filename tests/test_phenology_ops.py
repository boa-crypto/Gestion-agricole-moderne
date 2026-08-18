"""Vérifie les lectures phénologiques opérationnelles et transverses."""

import asyncio

from test_utils import run_event

from app.phenology_ops import (
    contextual_alerts,
    parcel_stage_map,
    phenology_counters,
    planned_vs_actual,
    search_phenology,
    stage_context_rows,
    stage_filter_options,
    stage_incoherences,
    stage_recommendations_for,
)
from app.seed import seed_dashboard_data
from app.seed_phenology import seed_phenology_data
from app.states.phenology_ops_state import PhenologyOpsState
from app.states.phenology_search_state import PhenologySearchState


async def main():
    print("=== Test intégration opérationnelle des stades ===")
    await seed_dashboard_data()
    await seed_phenology_data()

    rows = await stage_context_rows()
    assert len(rows) > 0, "Des cultures doivent être suivies"
    for row in rows:
        assert row["stage_name"] != ""
        assert row["next_stage"] != ""
        assert row["progress"] >= 0

    options = await stage_filter_options()
    assert any(item["value"] == "SANS_OBSERVATION" for item in options)

    mapping = await parcel_stage_map()
    assert len(mapping) > 0, "La cartographie doit connaître un stade par îlot"

    alerts = contextual_alerts(rows)
    kinds = {alert["kind"] for alert in alerts}
    assert kinds, "Des alertes contextuelles doivent être proposées"
    for alert in alerts:
        assert alert["route"].startswith("/")

    recos = await stage_recommendations_for([row["stage_id"] for row in rows])
    for reco in recos:
        assert reco["is_advisory"] is True, (
            "Aucune recommandation ne doit être prescriptive"
        )
        assert reco["source"] != ""

    planned = await planned_vs_actual()
    for item in planned:
        assert item["expected_label"] != "—"
        assert item["observed_label"] != "—"

    counters = await phenology_counters()
    assert counters["active_profiles"] > 0
    assert counters["active_stages"] > 0
    assert counters["prescriptive_recommendations"] == 0

    issues = await stage_incoherences()
    assert isinstance(issues, list)

    hits = await search_phenology("")
    kinds = {hit["kind"] for hit in hits}
    for expected in ("profil", "stade"):
        assert expected in kinds, f"L'index doit couvrir {expected}"

    ops = PhenologyOpsState()
    await run_event(ops.load_operational)
    assert ops.is_loading is False
    assert ops.row_count > 0
    assert ops.stage_options.length() > 0
    first_stage = ops.rows[0]["stage_name"]
    await run_event(ops.set_stage_filter, first_stage)
    for row in ops.rows:
        assert row["stage_name"] == first_stage
    await run_event(ops.reset_filters)
    assert ops.stage_filter == "TOUS"

    search = PhenologySearchState()
    await run_event(search.load_index)
    assert search.total_hits > 0
    assert search.sections.length() > 0
    await run_event(search.set_term, "tallage")
    await run_event(search.reset_index)
    assert search.term == ""

    print(
        f"✓ {len(rows)} culture(s) contextualisée(s), {len(alerts)} alerte(s) à "
        f"vérifier, {len(recos)} opération(s) indicative(s), "
        f"{len(planned)} comparaison(s) prévu/réel, {len(hits)} entrée(s) indexée(s)"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())
