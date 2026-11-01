"""Crée le compte de démonstration de l'aperçu (idempotent).

Le mot de passe est fourni par `AGRI_PRO_PREVIEW_PASSWORD` ; à défaut, un mot
de passe aléatoire est généré et affiché une seule fois.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import secrets
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/preview"
sys.path.insert(0, ROOT)

from app.local_db_env import force_local_database_env  # noqa: E402

force_local_database_env()

EMAIL = os.environ.get("AGRI_PRO_PREVIEW_EMAIL", "studio@agripro.preview")
PASSWORD = os.environ.get("AGRI_PRO_PREVIEW_PASSWORD", "")


def main() -> None:
    """Crée le compte s'il manque, ou signale qu'il existe déjà."""
    from app import preview_auth

    password = PASSWORD or secrets.token_urlsafe(9)
    try:
        _token, account = asyncio.run(
            preview_auth.authenticate(EMAIL, password, True)
        )
    except ValueError as exc:
        print(f"compte: conservé ({exc})")
        return
    print(f"compte créé: {account['email']} / {password}")


if __name__ == "__main__":
    main()
