"""Remap the legacy AgriPro palette + surface tokens to the editorial system.

Run once from the repository root:

    python tools/editorial_remap.py [--dry-run]

The editorial direction (« Encre & Chlorophylle ») keeps the agricultural
identity but replaces the glassy dark-green dashboard look with a print-inspired
system: warm near-black paper, hairlines, sharp corners, acid chlorophyll accent
and vermilion signal colour.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_DIRS = ("app",)

# Tailwind colour token -> editorial hex (without the leading '#').
COLOR_TOKENS: dict[str, str] = {
    # Chlorophylle accent
    "lime-100": "EFFFC4",
    "lime-200": "E4FF9B",
    "lime-300": "D8FA5E",
    "lime-400": "C2E847",
    # Paper / ink neutrals (former emerald family)
    "emerald-50": "F2EFE4",
    "emerald-100": "C9C5B4",
    "emerald-200": "B3AF9F",
    "emerald-300": "A9C98B",
    "emerald-400": "8FB37A",
    "emerald-500": "6E9159",
    "emerald-600": "557644",
    "emerald-700": "3E5A31",
    "emerald-800": "26311F",
    "emerald-900": "1A1E14",
    "emerald-950": "101208",
    "green-300": "A9C98B",
    "green-400": "8FB37A",
    "green-500": "6E9159",
    # Signal / alerts (former amber family)
    "amber-50": "FFF1E8",
    "amber-100": "FFDCCB",
    "amber-200": "FFB894",
    "amber-300": "FF8A5B",
    "amber-400": "FF6A38",
    "amber-500": "FF5A2B",
    "amber-600": "E64A1F",
    # States
    "red-100": "FFE0DA",
    "red-200": "FFBCB0",
    "red-300": "FF9B8C",
    "red-400": "FF6B5A",
    "red-500": "F2452C",
    "red-600": "D93A22",
    "red-950": "2A0D08",
    # Informational
    "sky-100": "E2ECFF",
    "sky-200": "C3DAFF",
    "sky-300": "9CC3FF",
    "sky-400": "6EA4F5",
    "orange-200": "FFC9A8",
    "orange-300": "FFA97A",
    "slate-100": "E4E2D8",
    "slate-300": "B5B3A8",
    # Secondary hues kept but muted to stay inside the editorial grid
    "teal-300": "7FD3B9",
    "teal-400": "5FBBA0",
    "violet-300": "B9A8FF",
    "violet-400": "9E8CFF",
    "purple-300": "C6B4F5",
    "purple-400": "AE9AE8",
    "rose-300": "FF9EB4",
    "pink-300": "FF9EC9",
    "fuchsia-300": "E9A3E0",
    "yellow-300": "FFDF9B",
    "yellow-400": "F5CF6A",
}

# Raw hex values used directly in class names.
HEX_TOKENS: dict[str, str] = {
    # Backgrounds / surfaces (former nuit / chlorophylle trio)
    "04140d": "0A0A08",
    "04120c": "0A0A08",
    "020a07": "060604",
    "03110b": "0D0F09",
    "071c13": "14160F",
    "081c13": "14160F",
    "061a11": "101208",
    "0b2418": "16190F",
    "0e2a1b": "191C13",
    "123324": "1E2216",
    # Accent greens
    "a3e635": "D8FA5E",
    "bef264": "E4FF9B",
    "84cc16": "C2E847",
    "65a30d": "B6D93F",
    "4d7c0f": "93AE45",
    "4ade80": "A9C98B",
    "22c55e": "8FB37A",
    "16a34a": "6E9159",
    "15803d": "557644",
    "166534": "3E5A31",
    "34d399": "8FD0B4",
    "14b8a6": "7FD3B9",
    # Signals
    "fbbf24": "FF8A5B",
    "facc15": "FFC46B",
    "f59e0b": "FF6A38",
    "eab308": "F0A84A",
    "a16207": "A9762F",
    "ca8a04": "C4923C",
    "d97706": "DE7233",
    "fb923c": "FF9E7A",
    "f97316": "FF5A2B",
    "78350f": "3F2415",
    "fef08a": "FFE9B8",
    "fde047": "FFDF9B",
    "fde68a": "FFE4C4",
    "dc2626": "E0452C",
    "be123c": "C33A46",
    "fb7185": "FF93A1",
    "f472b6": "FF9EC9",
    # Informational / secondary
    "38bdf8": "9CC3FF",
    "7c3aed": "8E7BFF",
    "a855f7": "B9A8FF",
    "c084fc": "D3C6FF",
    "e2e8f0": "E8E6DC",
    "94a3b8": "A8A79C",
}

# Solid surfaces replacing translucent white washes (Tailwind utility form).
WHITE_SURFACES: dict[str, str] = {
    "bg-white/[0.015]": "bg-[#0C0E08]",
    "bg-white/[0.02]": "bg-[#0D0F09]",
    "bg-white/[0.03]": "bg-[#101208]",
    "bg-white/[0.04]": "bg-[#14160F]",
    "bg-white/[0.05]": "bg-[#16190F]",
    "bg-white/[0.06]": "bg-[#191C13]",
    "bg-white/[0.07]": "bg-[#1B1F14]",
    "bg-white/[0.08]": "bg-[#1E2216]",
    "bg-white/5": "bg-[#14160F]",
    "bg-white/10": "bg-[#20241A]",
    "bg-white/15": "bg-[#262B1E]",
    "bg-white/20": "bg-[#2C3123]",
    "bg-white/25": "bg-[#333927]",
    "bg-white/40": "bg-[#4A5140]",
    "via-white/10": "via-[#20241A]",
    "to-white/10": "to-[#20241A]",
    "border-white/[0.04]": "border-[#F2EFE4]/8",
    "border-white/[0.06]": "border-[#F2EFE4]/10",
    "border-white/[0.08]": "border-[#F2EFE4]/12",
    "border-white/[0.12]": "border-[#F2EFE4]/16",
    "border-white/5": "border-[#F2EFE4]/8",
    "border-white/10": "border-[#F2EFE4]/12",
    "border-white/12": "border-[#F2EFE4]/14",
    "border-white/15": "border-[#F2EFE4]/16",
    "border-white/20": "border-[#F2EFE4]/22",
    "border-white/25": "border-[#F2EFE4]/25",
    "border-white/30": "border-[#F2EFE4]/30",
    "ring-white/10": "ring-[#F2EFE4]/12",
    "divide-white/10": "divide-[#F2EFE4]/12",
    "text-white": "text-[#F2EFE4]",
}

RADIUS_TOKENS = {
    "rounded-3xl": "rounded-none",
    "rounded-2xl": "rounded-none",
    "rounded-xl": "rounded-none",
    "rounded-lg": "rounded-none",
    "rounded-md": "rounded-none",
    "rounded-sm": "rounded-none",
    "rounded-full": "rounded-none",
    "rounded-t-3xl": "rounded-none",
    "rounded-t-2xl": "rounded-none",
    "rounded-b-3xl": "rounded-none",
    "rounded-b-2xl": "rounded-none",
    "rounded-l-xl": "rounded-none",
    "rounded-r-xl": "rounded-none",
}

BLUR_PATTERN = re.compile(r"\bbackdrop-blur(?:-(?:xs|sm|md|lg|xl|2xl|3xl|none))?\b")

FONT_TOKENS = {
    "font-['Inter']": "font-['Inter_Tight']",
    'font-["Inter"]': "font-['Inter_Tight']",
}

COLOR_RE = re.compile(
    r"(?<![\w-])(bg|text|border|from|via|to|ring|outline|fill|stroke|divide"
    r"|shadow|caret|decoration|accent|placeholder)-(lime|emerald|green|amber"
    r"|red|sky|orange|slate|teal|violet|purple|rose|pink|fuchsia|yellow"
    r"|indigo|blue|cyan|gray|zinc|neutral|stone)-(\d{2,3})(/\d{1,3})?"
)


def remap_color_token(match: re.Match[str]) -> str:
    utility, family, shade, opacity = match.groups()
    key = f"{family}-{shade}"
    hex_value = COLOR_TOKENS.get(key)
    if hex_value is None:
        return match.group(0)
    return f"{utility}-[#{hex_value}]{opacity or ''}"


def remap_hex(match: re.Match[str]) -> str:
    value = match.group(1).lower()
    if value not in HEX_TOKENS:
        return match.group(0)
    return f"#{HEX_TOKENS[value]}"


HEX_RE = re.compile(r"#([0-9a-fA-F]{6})(?![0-9a-fA-F])")


def transform(content: str) -> str:
    for legacy, replacement in WHITE_SURFACES.items():
        content = content.replace(legacy, replacement)
    for legacy, replacement in FONT_TOKENS.items():
        content = content.replace(legacy, replacement)
    for legacy, replacement in RADIUS_TOKENS.items():
        content = re.sub(rf"\b{re.escape(legacy)}\b", replacement, content)
    content = BLUR_PATTERN.sub("", content)
    content = COLOR_RE.sub(remap_color_token, content)
    content = HEX_RE.sub(remap_hex, content)
    return content


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    changed = 0
    for directory in TARGET_DIRS:
        for path in sorted((ROOT / directory).rglob("*.py")):
            original = path.read_text(encoding="utf-8")
            updated = transform(original)
            if updated != original:
                changed += 1
                print(f"~ {path.relative_to(ROOT)}")
                if not args.dry_run:
                    path.write_text(updated, encoding="utf-8")
    print(f"{changed} fichier(s) remappé(s)")


if __name__ == "__main__":
    main()
