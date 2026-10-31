"""Exécute les scripts de vérification hérités de `tests/`.

Ces fichiers ne sont pas des modules pytest : chacun expose `async def main()`
et s'exécute comme un script. Ils importent `run_event` depuis
`tests/test_utils.py` (désormais versionné) et utilisent SQLite en local.

Usage :

    python scripts/run_legacy_tests.py            # tous les scripts
    python scripts/run_legacy_tests.py stock guide  # filtre sur le nom

Le script copie la base dans un fichier temporaire avant l'exécution, de sorte
que `data/exploitation.db` n'est pas modifié.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
DB = ROOT / "data" / "exploitation.db"


def discover(filters: list[str]) -> list[Path]:
    scripts = []
    for path in sorted(TESTS.glob("test_*.py")):
        if path.name == "test_utils.py":
            continue
        source = path.read_text()
        if "from test_utils import" not in source:
            continue
        if filters and not any(item in path.stem for item in filters):
            continue
        scripts.append(path)
    return scripts


def run(script: Path, env: dict[str, str]) -> tuple[bool, str]:
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    output = (completed.stdout + completed.stderr).strip().splitlines()
    if completed.returncode == 0:
        detail = next(
            (line.strip() for line in reversed(output) if "réussi" in line.lower()),
            "terminé",
        )
    else:
        detail = next(
            (
                line.strip()
                for line in reversed(output)
                if line.strip()
                and not line.strip().startswith(("File ", "Traceback", "^^^", "await "))
                and "site-packages" not in line
            ),
            "",
        )
    return completed.returncode == 0, detail[:110]


def main() -> int:
    filters = sys.argv[1:]
    scripts = discover(filters)
    if not scripts:
        print("Aucun script à exécuter.")
        return 1

    env = {
        **__import__("os").environ,
        "PYTHONPATH": f"{ROOT}:{TESTS}",
        "REFLEX_USE_NPM": "1",
    }

    backup = None
    if DB.exists():
        backup = Path(tempfile.mkdtemp()) / "exploitation.db"
        shutil.copy2(DB, backup)

    def restore() -> None:
        """Chaque script repart d'une base identique : la suite est stateless."""
        if backup:
            for suffix in ("", "-shm", "-wal"):
                src = backup.with_name(backup.name.replace(".db", f".db{suffix}"))
                dst = DB.with_name(DB.name + suffix)
                if suffix and dst.exists():
                    dst.unlink()
                if not suffix:
                    shutil.copy2(backup, DB)

    failures = []
    print(f"{'script':38} {'état':8} détail")
    print("-" * 100)
    try:
        for script in scripts:
            restore()
            try:
                ok, detail = run(script, env)
            except subprocess.TimeoutExpired:
                ok, detail = False, "délai dépassé (180 s)"
            print(f"{script.stem:38} {'réussi' if ok else 'échec':8} {detail}")
            if not ok:
                failures.append(script.stem)
    finally:
        restore()

    print("-" * 100)
    print(
        f"{len(scripts) - len(failures)}/{len(scripts)} scripts réussis"
        + (f" — échecs : {', '.join(failures)}" if failures else "")
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
