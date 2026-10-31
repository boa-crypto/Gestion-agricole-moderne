"""Replace the duplicated page wrappers by the shared editorial shell.

Run once from the repository root:

    python tools/page_shell_migration.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "app" / "pages"


def migrate(text: str) -> tuple[str, str] | None:
    if "app_shell(" in text or "rx.el.main(" not in text:
        return None
    match = re.search(
        r"def (?P<name>\w+_page)\(\) -> rx\.Component:\n"
        r"    return rx\.el\.main\(\n"
        r"        rx\.el\.div\(\n"
        r"            class_name=\"pointer-events-none[^\n]*\n"
        r"        \),\n"
        r"        rx\.el\.div\(\n"
        r"            side_rail\(\"(?P<key>[^\"]+)\"\),\n",
        text,
    )
    if match is None:
        return None
    body_start = match.end()
    tail = text[body_start:]
    closing = re.search(
        r"\n            class_name=\"relative z-10[^\n]*\n"
        r"        \),\n"
        r'        class_name="relative min-h-screen[^\n]*\n'
        r"    \)\n",
        tail,
    )
    if closing is None:
        return None
    body = tail[: closing.start()].rstrip()
    body_lines = body.split("\n")
    replacement = (
        f"def {match.group('name')}() -> rx.Component:\n"
        f"    return app_shell(\n"
        f"        rx.el.div(\n"
        + "\n".join(body_lines)
        + f'\n            class_name="flex w-full flex-col gap-6",\n'
        f"        ),\n"
        f'        "{match.group("key")}",\n'
        f"    )\n"
    )
    start = match.start()
    end = body_start + closing.end()
    return text[:start] + replacement + text[end:], match.group("name")


def ensure_import(text: str) -> str:
    if "side_rail(" not in text:
        text = text.replace(
            "from app.components.side_rail import side_rail\n", ""
        )
    if "from app.components.shell import app_shell" in text:
        return text
    lines = text.split("\n")
    insertion = None
    for index, line in enumerate(lines):
        if line.startswith("from app.states."):
            insertion = index
            break
    if insertion is None:
        for index, line in enumerate(lines):
            if line.startswith("from app.components."):
                insertion = index + 1
    if insertion is None:
        return text
    lines.insert(insertion, "from app.components.shell import app_shell")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for path in sorted(PAGES.glob("*.py")):
        if path.name in {"__init__.py", "auth_login.py"}:
            continue
        original = path.read_text(encoding="utf-8")
        result = migrate(original)
        if result is None:
            print(f"= {path.name} (inchangé)")
            continue
        migrated, name = result
        migrated = ensure_import(migrated)
        print(f"~ {path.name} -> app_shell ({name})")
        if not args.dry_run:
            path.write_text(migrated, encoding="utf-8")


if __name__ == "__main__":
    main()
