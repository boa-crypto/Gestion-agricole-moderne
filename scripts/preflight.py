"""Contrôle pré-vol : compilation et construction de tous les écrans.

Reflex ne détecte pas à l'import une primitive manquante dans une page : il
faut réellement construire le composant. Ce script importe chaque page, appelle
sa fonction de construction et rapporte les échecs, avant de lancer l'aperçu.

Usage :
    python scripts/preflight.py
    python scripts/preflight.py --compile   # ajoute compileall sur app/

Retour : code 0 si tout est vert, 1 sinon.
"""

from __future__ import annotations

import argparse
import compileall
import importlib
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Signatures différentes assumées (rendu piloté par des arguments externes).
SKIP = {"auth_login:login_page"}


def build_pages() -> list[str]:
    """Construit chaque page et retourne la liste des échecs décrits."""
    failures: list[str] = []
    for path in sorted((ROOT / "app" / "pages").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"app.pages.{path.stem}")
        except Exception:
            failures.append(f"{path.stem}: import\n{traceback.format_exc()}")
            continue
        for name in sorted(dir(module)):
            if not (name.endswith("_page") and callable(getattr(module, name))):
                continue
            if f"{path.stem}:{name}" in SKIP:
                continue
            try:
                getattr(module, name)()
            except Exception as exc:
                failures.append(
                    f"{path.stem}:{name} -> {type(exc).__name__}: {exc}"
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compile",
        action="store_true",
        help="compile aussi le paquet app/ (bytecode)",
    )
    args = parser.parse_args()

    if args.compile:
        ok = compileall.compile_dir(str(ROOT / "app"), quiet=1)
        print(f"compileall : {'OK' if ok else 'ÉCHEC'}")
        if not ok:
            return 1

    failures = build_pages()
    if failures:
        print(f"{len(failures)} écran(s) en échec :")
        for failure in failures:
            print(" -", failure)
        return 1

    print("Tous les écrans se construisent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
