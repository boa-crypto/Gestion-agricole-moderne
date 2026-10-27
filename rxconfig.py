# IMPORTANT : le verrouillage SQLite doit précéder l'import de Reflex, car la
# configuration lit les variables d'environnement (injectées par la plateforme
# avec des URL PostgreSQL) dès son instanciation.
from app.local_db_env import (  # noqa: E402
    ASYNC_DB_URL,
    SYNC_DB_URL,
    force_local_database_env,
)

force_local_database_env()

import reflex as rx  # noqa: E402

config = rx.Config(
    app_name="app",
    db_url=SYNC_DB_URL,
    async_db_url=ASYNC_DB_URL,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
