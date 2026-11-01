"""Amorce la base SQLite de la copie d'aperçu (données de démonstration)."""

from __future__ import annotations

import asyncio
import sys
import time

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/preview"
sys.path.insert(0, ROOT)

from app.local_db_env import force_local_database_env  # noqa: E402

force_local_database_env()


async def main() -> None:
    """Exécute les amorçages métier dans l'ordre des dépendances."""
    from app.catalog_link import materialize_catalog_varieties
    from app.database import (
        ensure_catalog_tables,
        ensure_crm_tables,
        ensure_phenology_tables,
        normalize_legacy_icon_names,
    )
    from app.seed import seed_dashboard_data
    from app.seed_catalog import link_legacy_varieties, seed_catalog_data
    from app.seed_corrections import seed_coherence_data
    from app.seed_crm import seed_crm_if_empty
    from app.seed_phenology import seed_phenology_data

    steps = [
        ("tables phénologie", ensure_phenology_tables()),
        ("tables référentiel", ensure_catalog_tables()),
        ("tables CRM", ensure_crm_tables()),
        ("icônes", asyncio.to_thread(normalize_legacy_icon_names)),
        ("cockpit", seed_dashboard_data()),
        ("cohérence", seed_coherence_data()),
        ("référentiel", seed_catalog_data()),
        ("variétés héritées", link_legacy_varieties()),
        ("matérialisation", materialize_catalog_varieties()),
        ("phénologie", seed_phenology_data()),
    ]
    for name, coro in steps:
        start = time.time()
        try:
            await coro
            print(f"{name}: {time.time() - start:.1f}s", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: ÉCHEC {type(exc).__name__}: {exc}", flush=True)
    try:
        seed_crm_if_empty()
        print("CRM: ok", flush=True)
    except Exception as exc:  # noqa: BLE001
        print("CRM: ÉCHEC", type(exc).__name__, exc, flush=True)


asyncio.run(main())
