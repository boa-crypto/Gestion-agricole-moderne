"""Unify page heroes and micro-labels on the editorial type scale.

Run once from the repository root:

    python tools/editorial_headers.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPLACEMENTS: list[tuple[str, str]] = [
    # Page hero: display title
    (
        "font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05]",
        "ap-display text-[clamp(2.4rem,4.6vw,4.1rem)]",
    ),
    (
        "font-['Instrument_Serif'] text-4xl sm:text-5xl",
        "ap-display text-[clamp(2.4rem,4.6vw,4.1rem)]",
    ),
    # Page hero: eyebrow
    (
        "text-[11px] font-semibold uppercase tracking-[0.32em] text-[#d8fa5e]/90",
        "ap-eyebrow text-[#D8FA5E]",
    ),
    # Page hero: description
    (
        "text-sm font-medium text-[#c9c5b4]/60 mt-3",
        "mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70",
    ),
    (
        "text-sm font-medium text-[#c9c5b4]/60 mt-3 max-w-2xl",
        "mt-4 max-w-2xl text-[13px] leading-relaxed text-[#C9C5B4]/70",
    ),
    (
        "text-sm font-medium text-[#c9c5b4]/60 mt-3 max-w-xl",
        "mt-4 max-w-xl text-[13px] leading-relaxed text-[#C9C5B4]/70",
    ),
    (
        "text-sm font-medium text-[#c9c5b4]/60 mt-3 max-w-3xl",
        "mt-4 max-w-3xl text-[13px] leading-relaxed text-[#C9C5B4]/70",
    ),
    # Hero meta pill
    (
        "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5  w-fit",
        "ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
    ),
    # Hero refresh button
    (
        "flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
        "ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
    ),
    # Hero rule
    (
        "w-full border-b border-[#f2efe4]/12 pb-8 mt-6",
        "w-full border-b border-[#F2EFE4]/12 pb-8",
    ),
    # Type families
    ("font-['Instrument_Serif']", "ap-serif"),
    ("font-['Inter_Tight']", "font-['Inter_Tight']"),
]

LABEL_RE = re.compile(
    r"text-\[(?:9|10|11)px\]\s+font-semibold\s+uppercase\s+tracking-\[[0-9.]+em\]"
)


def transform(content: str) -> str:
    for legacy, replacement in REPLACEMENTS:
        content = content.replace(legacy, replacement)
    content = LABEL_RE.sub("ap-eyebrow", content)
    content = content.replace("ap-serif ap-serif", "ap-serif")
    content = content.replace("ap-display ap-serif", "ap-display")
    content = content.replace("ap-serif ap-display", "ap-display")
    return content


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    changed = 0
    for path in sorted((ROOT / "app").rglob("*.py")):
        original = path.read_text(encoding="utf-8")
        updated = transform(original)
        if updated != original:
            changed += 1
            if args.dry_run:
                print(f"~ {path.relative_to(ROOT)}")
            else:
                path.write_text(updated, encoding="utf-8")
    print(f"{changed} fichier(s) mis à jour")


if __name__ == "__main__":
    main()
