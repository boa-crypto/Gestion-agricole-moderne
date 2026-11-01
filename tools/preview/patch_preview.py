"""Applique à la copie d'aperçu les contournements d'un environnement hors ligne.

La base de menus managée (PostgreSQL reflex-enterprise) et Open-Meteo ne sont
pas joignables depuis un bac à sable sans sortie réseau. On remplace donc le
socle d'authentification par un magasin SQLite local (`preview_auth.py`), on
neutralise l'amorçage des menus et l'appel météo, et on fixe l'origine publique
du frontend comme URL d'API.

La copie vit hors du dépôt (`/tmp/preview` par défaut) : l'application
versionnée n'est jamais modifiée.
"""

from __future__ import annotations

import os
import pathlib
import shutil

ROOT = pathlib.Path(os.environ.get("PREVIEW_ROOT", "/tmp/preview"))
KIT = pathlib.Path(__file__).resolve().parent
SANDBOX = os.environ.get("E2B_SANDBOX_ID", "").strip()
FRONTEND_PORT = os.environ.get("PREVIEW_FRONTEND_PORT", "3000").strip()

MENU_STUB = '''

# --- Aperçu local : base « menus » managée indisponible, amorçage neutralisé.
import os as _os_stub  # noqa: E402

if _os_stub.environ.get("AGRI_PRO_PREVIEW_STUB") == "1":

    def bootstrap_menu_database(*args, **kwargs):  # noqa: D103
        return None

    async def ensure_menu_database(*args, **kwargs):  # noqa: D103
        return None

    @asynccontextmanager
    async def menu_database_lifespan(*args, **kwargs):  # noqa: D103
        yield
'''

POLICY_STUB = '''

# --- Aperçu local : politique d'accès lue dans le magasin SQLite d'aperçu.
import os as _os_stub  # noqa: E402

if _os_stub.environ.get("AGRI_PRO_PREVIEW_STUB") == "1":

    async def resolve_policy(token: str = ""):  # noqa: D103
        from app import preview_auth

        policy = preview_auth.policy_for(token)
        if policy is None:
            raise PermissionError("Connexion requise.")
        return policy
'''

SERVICE_STUB = '''

# --- Aperçu local : comptes et sessions dans SQLite au lieu du service managé.
import os as _os_stub  # noqa: E402

if _os_stub.environ.get("AGRI_PRO_PREVIEW_STUB") == "1":
    from app import preview_auth as _preview_auth  # noqa: E402

    async def authenticate(  # noqa: D103
        email: str, password: str, signup: bool, old_token: str = ""
    ):
        return await _preview_auth.authenticate(email, password, signup, old_token)

    async def revoke_session(token: str) -> None:  # noqa: D103
        await _preview_auth.revoke(token)
'''

GUARD_STUB = '''

# --- Aperçu local : vérification de service neutralisée (hors dépôt).
import os as _os_stub  # noqa: E402

if _os_stub.environ.get("AGRI_PRO_PREVIEW_STUB") == "1":

    async def require_service(*permissions, **kwargs):  # noqa: D103
        return None
'''

WEATHER_STUB = '''

# --- Aperçu local : aucun accès sortant vers Open-Meteo.
import os as _os_stub  # noqa: E402

if _os_stub.environ.get("AGRI_PRO_PREVIEW_STUB") == "1":

    def fetch_forecast(*args, **kwargs):  # noqa: D103
        return None
'''


def append_once(path: pathlib.Path, block: str, marker: str) -> None:
    """Ajoute un bloc de contournement s'il n'est pas déjà présent."""
    text = path.read_text()
    if marker in text:
        return
    path.write_text(text + block)
    print("patché:", path)


def install_auth_store() -> None:
    """Copie le magasin de comptes local dans la copie d'aperçu."""
    target = ROOT / "app/preview_auth.py"
    shutil.copyfile(KIT / "preview_auth.py", target)
    print("magasin de comptes:", target)


def patch_config() -> None:
    """Origine unique : le navigateur ne joint que le port du frontend.

    Le serveur de développement relaie /_event vers le backend ; l'URL d'API
    doit donc désigner l'origine du frontend, en HTTPS public.
    """
    path = ROOT / "rxconfig.py"
    text = path.read_text()
    text = "\n".join(
        line for line in text.splitlines() if "api_url=" not in line
    ) + "\n"
    if SANDBOX:
        url = f"https://{FRONTEND_PORT}-{SANDBOX}.e2b.app"
        text = text.replace(
            "    vite_allowed_hosts=True,",
            f'    api_url="{url}",\n    vite_allowed_hosts=True,',
            1,
        )
        print("api_url:", url)
    else:
        print("api_url: pas d'identifiant de bac à sable, laissé par défaut")
    path.write_text(text)


def main() -> None:
    """Applique l'ensemble des contournements à la copie d'aperçu."""
    install_auth_store()
    append_once(ROOT / "app/menu_database.py", MENU_STUB, "AGRI_PRO_PREVIEW_STUB")
    append_once(ROOT / "app/menu_policy.py", POLICY_STUB, "AGRI_PRO_PREVIEW_STUB")
    append_once(ROOT / "app/menu_service.py", SERVICE_STUB, "AGRI_PRO_PREVIEW_STUB")
    append_once(ROOT / "app/server_guard.py", GUARD_STUB, "AGRI_PRO_PREVIEW_STUB")
    append_once(
        ROOT / "app/states/weather_state.py", WEATHER_STUB, "AGRI_PRO_PREVIEW_STUB"
    )
    patch_config()


if __name__ == "__main__":
    main()
