"""Verrouillage de la base de données sur le fichier SQLite local.

La plateforme injecte des variables d'environnement PostgreSQL
(`REFLEX_DB_URL`, `REFLEX_ASYNC_DB_URL`, `DATABASE_URL`, ...) qui écrasent la
configuration de `rxconfig.py` au moment où `rx.session()` / `rx.asession()`
créent leur moteur. Ce module force, le plus tôt possible dans le cycle de vie
du processus (avant toute lecture de configuration Reflex), les URL vers le
fichier SQLite local du projet et crée le répertoire de données.

Aucune écriture n'est effectuée vers PostgreSQL ou une base managée.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Racine du projet (app/local_db_env.py -> app -> racine).
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
DB_PATH: Path = DATA_DIR / "exploitation.db"

SYNC_DB_URL: str = f"sqlite:///{DB_PATH.as_posix()}"
ASYNC_DB_URL: str = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

# Toutes les variables susceptibles de router les sessions vers PostgreSQL.
_SYNC_ENV_KEYS: tuple[str, ...] = (
    "REFLEX_DB_URL",
    "DATABASE_URL",
    "POSTGRES_URL",
    "PGDATABASE_URL",
)
_ASYNC_ENV_KEYS: tuple[str, ...] = (
    "REFLEX_ASYNC_DB_URL",
    "ASYNC_DATABASE_URL",
)

_forced: bool = False


def _patch_live_config() -> None:
    """Réaligne l'objet de configuration Reflex **s'il existe déjà**.

    Aucun import de Reflex n'est déclenché ici : appeler `get_config()` trop
    tôt provoque l'import partiel de `rxconfig` (et des plugins) et des
    erreurs bruyantes. On se contente donc de patcher l'objet déjà chargé.
    """
    module = sys.modules.get("rxconfig")
    config = getattr(module, "config", None) if module is not None else None
    if config is None:
        logging.debug(
            "Configuration Reflex non encore chargée : "
            "seules les variables d'environnement sont forcées."
        )
        return
    try:
        if getattr(config, "db_url", None) != SYNC_DB_URL:
            config.db_url = SYNC_DB_URL
        if getattr(config, "async_db_url", None) != ASYNC_DB_URL:
            config.async_db_url = ASYNC_DB_URL
    except Exception as e:  # noqa: BLE001 - configuration en lecture seule
        logging.exception("Unexpected error")
        logging.debug(f"Configuration Reflex non patchable: {e}")


def force_local_database_env() -> None:
    """Impose les URL SQLite locales et prépare le répertoire de données."""
    global _forced
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for key in _SYNC_ENV_KEYS:
        os.environ[key] = SYNC_DB_URL
    for key in _ASYNC_ENV_KEYS:
        os.environ[key] = ASYNC_DB_URL
    _patch_live_config()
    _forced = True


def is_forced() -> bool:
    return _forced


# Appliqué dès l'import du module, avant toute création de moteur.
force_local_database_env()
