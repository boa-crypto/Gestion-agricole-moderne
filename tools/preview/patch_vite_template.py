"""Ajoute un relais Vite vers le backend dans le template de configuration.

Reflex réécrit `.web/vite.config.js` à chaque compilation depuis
`reflex_base/compiler/templates.py` : patcher le fichier généré ne tient pas,
on patche donc le template, une fois par environnement Python.
"""

from __future__ import annotations

import pathlib
import sysconfig

TARGET = (
    pathlib.Path(sysconfig.get_paths()["purelib"])
    / "reflex_base/compiler/templates.py"
)
ANCHOR = '''    warmup_str = (
        """
    warmup: {
      clientFiles: ["./app/routes/**/*.jsx"],
    },"""
        if warmup_routes
        else ""
    )
'''
PROXY = '''
    # Aperçu : le serveur de développement relaie les événements vers le
    # backend, pour qu'un navigateur distant n'ait qu'une seule origine.
    _preview_backend = os.environ.get("AGRI_PRO_PREVIEW_BACKEND", "")
    proxy_str = (
        """
    proxy: {
      "/_event": { target: "http://127.0.0.1:%s", ws: true },
      "/_upload": { target: "http://127.0.0.1:%s" },
      "/_health": { target: "http://127.0.0.1:%s" },
      "/_all_routes": { target: "http://127.0.0.1:%s" },
      "/ping": { target: "http://127.0.0.1:%s" },
      "/auth-codespace": { target: "http://127.0.0.1:%s" },
    },""" % ((_preview_backend,) * 6)
        if _preview_backend
        else ""
    )
'''


def main() -> None:
    """Applique le patch si le marqueur est absent."""
    if not TARGET.exists():
        raise SystemExit(f"template introuvable : {TARGET}")
    text = TARGET.read_text()
    if "AGRI_PRO_PREVIEW_BACKEND" in text:
        print("template: déjà patché")
        return
    if ANCHOR not in text:
        raise SystemExit("ancre warmup introuvable dans le template Vite")
    text = text.replace(ANCHOR, ANCHOR + PROXY, 1)
    text = text.replace(
        '    hmr: {"true" if hmr else "false"},{warmup_str}',
        '    hmr: {"true" if hmr else "false"},{warmup_str}{proxy_str}',
        1,
    )
    if "\nimport os\n" not in text:
        text = text.replace(
            "from __future__ import annotations\n",
            "from __future__ import annotations\n\nimport os\n",
            1,
        )
    TARGET.write_text(text)
    print("template Vite: proxy ajouté")


if __name__ == "__main__":
    main()
