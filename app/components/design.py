"""Système de design « Encre & Chlorophylle » de l'édition AgriPro.

Direction artistique : maison d'édition agronomique contemporaine. Papier
encre chaude, filets d'un pixel, angles vifs, typographie éditoriale
(Instrument Serif pour le registre, Inter Tight pour la lecture, JetBrains Mono
pour les données), accent chlorophylle acide et vermillon de signal.

Le module centralise les jetons (couleurs, typographies, filets) et expose les
primitives réutilisées par la coque applicative et les en-têtes de section.
"""

from __future__ import annotations

import reflex as rx

# ---------------------------------------------------------------------------
# Jetons
# ---------------------------------------------------------------------------

INK = "#0A0A08"
INK_DEEP = "#060604"
SURFACE = "#101208"
SURFACE_RAISED = "#14160F"
SURFACE_HIGH = "#191C13"
SURFACE_CONTROL = "#20241A"
PAPER = "#F2EFE4"
PAPER_MUTED = "#C9C5B4"
PAPER_FAINT = "#8F8C7E"
ACCENT = "#D8FA5E"
ACCENT_DEEP = "#B6D93F"
FLAME = "#FF5A2B"
FLAME_SOFT = "#FF8A5B"
SAGE = "#A9C98B"
INFO = "#9CC3FF"
DANGER = "#FF6B5A"

FONT_DISPLAY = "ap-serif"
FONT_SANS = "font-['Inter_Tight']"
FONT_MONO = "font-['JetBrains_Mono']"

LINE = "border-[#F2EFE4]/12"
LINE_SOFT = "border-[#F2EFE4]/8"
LINE_STRONG = "border-[#F2EFE4]/22"

GOOGLE_FONTS_HREF = (
    "https://fonts.googleapis.com/css2"
    "?family=Instrument+Serif:ital@0;1"
    "&family=Inter+Tight:wght@300;400;500;600;700"
    "&family=JetBrains+Mono:wght@300;400;500;600"
    "&display=swap"
)

# ---------------------------------------------------------------------------
# Feuille de style globale
# ---------------------------------------------------------------------------

GLOBAL_CSS = """
:root {
  --ap-ink: #0A0A08;
  --ap-ink-deep: #060604;
  --ap-surface: #101208;
  --ap-surface-raised: #14160F;
  --ap-surface-high: #191C13;
  --ap-paper: #F2EFE4;
  --ap-paper-muted: #C9C5B4;
  --ap-accent: #D8FA5E;
  --ap-accent-deep: #B6D93F;
  --ap-flame: #FF5A2B;
  --ap-sage: #A9C98B;
  --ap-info: #9CC3FF;
  --ap-line: rgba(242, 239, 228, 0.12);
  --ap-line-soft: rgba(242, 239, 228, 0.08);
  --ap-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --ap-sans: 'Inter Tight', 'Inter', system-ui, -apple-system, sans-serif;
  --ap-serif: 'Instrument Serif', 'Times New Roman', Georgia, serif;
}

/* Filet de sécurité : toute couleur Tailwind héritée pointe vers la palette. */
:root {
  --color-lime-100: #EFFFC4;
  --color-lime-200: #E4FF9B;
  --color-lime-300: #D8FA5E;
  --color-lime-400: #C2E847;
  --color-emerald-50: #F2EFE4;
  --color-emerald-100: #C9C5B4;
  --color-emerald-300: #A9C98B;
  --color-amber-200: #FFB894;
  --color-amber-300: #FF8A5B;
  --color-red-300: #FF9B8C;
  --color-red-400: #FF6B5A;
  --color-sky-300: #9CC3FF;
  --color-white: #F2EFE4;
}

html {
  background-color: var(--ap-ink);
  color-scheme: dark;
  -webkit-text-size-adjust: 100%;
}

body {
  background-color: var(--ap-ink);
  color: var(--ap-paper);
  font-family: var(--ap-sans);
  letter-spacing: -0.012em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* Grain d'impression, très discret, au-dessus des surfaces. */
body::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 25;
  pointer-events: none;
  opacity: 0.05;
  mix-blend-mode: soft-light;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='0.55'/%3E%3C/svg%3E");
}

::selection {
  background: var(--ap-accent);
  color: var(--ap-ink);
}

:focus-visible {
  outline: 1px solid var(--ap-accent);
  outline-offset: 3px;
}

* {
  scrollbar-width: thin;
  scrollbar-color: #2B3020 var(--ap-ink);
}

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--ap-ink); }
::-webkit-scrollbar-thumb {
  background: #2B3020;
  border: 3px solid var(--ap-ink);
}

h1, h2, h3, h4 { text-wrap: balance; }
p { text-wrap: pretty; }

table, .ap-tabular { font-variant-numeric: tabular-nums; }

input, select, textarea { font-family: var(--ap-sans); }

/* Primitives éditoriales -------------------------------------------------- */

.ap-mono {
  font-family: var(--ap-mono);
  font-feature-settings: 'ss01' 1, 'zero' 1;
  font-variant-numeric: tabular-nums;
}

.ap-serif {
  font-family: var(--ap-serif);
  font-weight: 400;
  letter-spacing: -0.018em;
}

.ap-eyebrow {
  font-family: var(--ap-mono);
  font-size: 10px;
  line-height: 1;
  letter-spacing: 0.3em;
  text-transform: uppercase;
}

.ap-display {
  font-family: var(--ap-serif);
  letter-spacing: -0.028em;
  line-height: 0.94;
  text-wrap: balance;
}

.ap-italic { font-style: italic; }

.ap-underlink {
  text-decoration: none;
  background-image: linear-gradient(currentColor, currentColor);
  background-size: 100% 1px;
  background-position: 0 100%;
  background-repeat: no-repeat;
  transition: background-size 240ms cubic-bezier(.2, .7, .2, 1);
}
.ap-underlink:hover { background-size: 0% 1px; }

.ap-hairline { border-color: var(--ap-line); }

/* Micro-interactions ------------------------------------------------------ */

.ap-lift {
  transition: border-color 200ms ease, background-color 200ms ease,
    transform 260ms cubic-bezier(.2, .7, .2, 1);
}

@keyframes ap-rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}

.ap-reveal { animation: ap-rise 620ms cubic-bezier(.2, .7, .2, 1) both; }

@keyframes ap-marquee {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
"""


def editorial_styles() -> rx.Component:
    """Feuille de style globale injectée dans le <head> de l'application."""
    return rx.el.style(GLOBAL_CSS)


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def eyebrow(
    text: rx.Var | str,
    *,
    tone: str = "muted",
    class_name: str = "",
) -> rx.Component:
    """Sur-titre mono, précédé d'un carré d'accent (marqueur de maison)."""
    tone_class = {
        "accent": "text-[#D8FA5E]",
        "flame": "text-[#FF8A5B]",
        "paper": "text-[#F2EFE4]",
        "muted": "text-[#C9C5B4]/60",
    }[tone]
    dot_class = {
        "accent": "bg-[#D8FA5E]",
        "flame": "bg-[#FF5A2B]",
        "paper": "bg-[#F2EFE4]",
        "muted": "bg-[#C9C5B4]/40",
    }[tone]
    return rx.el.p(
        rx.el.span("", class_name=f"inline-block h-1.5 w-1.5 {dot_class}"),
        rx.el.span(text),
        class_name=f"ap-eyebrow flex items-center gap-2.5 {tone_class} {class_name}",
    )


def hairline(class_name: str = "") -> rx.Component:
    return rx.el.div(
        class_name=f"h-px w-full bg-[#F2EFE4]/12 {class_name}",
        aria_hidden="true",
    )


def _tone_text(tone: str) -> str:
    return {
        "neutral": "text-[#C9C5B4]",
        "paper": "text-[#F2EFE4]",
        "accent": "text-[#D8FA5E]",
        "flame": "text-[#FF8A5B]",
        "sage": "text-[#A9C98B]",
        "info": "text-[#9CC3FF]",
    }.get(tone, "text-[#C9C5B4]")


def _tone_border(tone: str) -> str:
    return {
        "neutral": "border-[#F2EFE4]/16",
        "paper": "border-[#F2EFE4]/22",
        "accent": "border-[#D8FA5E]/40",
        "flame": "border-[#FF5A2B]/40",
        "sage": "border-[#A9C98B]/40",
        "info": "border-[#9CC3FF]/35",
    }.get(tone, "border-[#F2EFE4]/16")


def tag(
    label: rx.Var | str,
    *,
    tone: str = "neutral",
    icon: str = "",
) -> rx.Component:
    """Étiquette carrée, mono, filet d'un pixel."""
    children: list[rx.Component] = []
    if icon:
        children.append(rx.icon(icon, class_name="h-3 w-3 shrink-0"))
    children.append(rx.el.span(label))
    return rx.el.span(
        *children,
        class_name=(
            "ap-mono inline-flex w-fit items-center gap-1.5 border px-2 py-1 "
            "text-[9px] uppercase tracking-[0.18em] whitespace-nowrap "
            f"{_tone_border(tone)} {_tone_text(tone)}"
        ),
    )


def action_button(
    label: rx.Var | str,
    *,
    icon: str = "",
    on_click=None,
    href: str = "",
    tone: str = "solid",
    type: str = "button",
    disabled=None,
    class_name: str = "",
) -> rx.Component:
    """Bouton carré éditorial : plein chlorophylle ou filet simple."""
    styles = {
        "solid": (
            "border border-[#D8FA5E] bg-[#D8FA5E] text-[#0A0A08] "
            "hover:bg-[#E4FF9B] hover:border-[#E4FF9B]"
        ),
        "outline": (
            "border border-[#F2EFE4]/22 bg-transparent text-[#F2EFE4] "
            "hover:border-[#D8FA5E] hover:text-[#D8FA5E]"
        ),
        "ghost": (
            "border border-transparent bg-transparent text-[#C9C5B4] "
            "hover:text-[#F2EFE4] hover:border-[#F2EFE4]/16"
        ),
        "flame": (
            "border border-[#FF5A2B]/45 bg-[#FF5A2B]/10 text-[#FF8A5B] "
            "hover:bg-[#FF5A2B]/20"
        ),
    }
    children: list[rx.Component] = []
    if icon:
        children.append(rx.icon(icon, class_name="h-3.5 w-3.5 shrink-0"))
    children.append(rx.el.span(label))
    shared = (
        "ap-mono inline-flex w-fit items-center justify-center gap-2 px-3.5 py-2.5 "
        f"text-[10px] uppercase tracking-[0.18em] transition-colors {styles[tone]} "
        "disabled:cursor-not-allowed disabled:opacity-45 "
        f"{class_name}"
    )
    if href:
        return rx.el.a(*children, href=href, class_name=shared)
    return rx.el.button(
        *children,
        type=type,
        on_click=on_click,
        disabled=disabled,
        class_name=shared,
    )


def icon_action(
    icon: str,
    label: rx.Var | str,
    *,
    on_click=None,
    href: str = "",
    class_name: str = "",
) -> rx.Component:
    shared = (
        "ap-mono inline-flex h-9 w-9 shrink-0 items-center justify-center border "
        "border-[#F2EFE4]/16 text-[#C9C5B4] transition-colors "
        "hover:border-[#D8FA5E] hover:text-[#D8FA5E] "
        f"{class_name}"
    )
    if href:
        return rx.el.a(
            rx.icon(icon, class_name="h-4 w-4"),
            href=href,
            title=label,
            aria_label=label,
            class_name=shared,
        )
    return rx.el.button(
        rx.icon(icon, class_name="h-4 w-4"),
        type="button",
        on_click=on_click,
        title=label,
        aria_label=label,
        class_name=shared,
    )


def section_header(
    index: rx.Var | str,
    title: rx.Var | str,
    *,
    description: rx.Var | str = "",
    trailing: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    """Titre de section numéroté, filet supérieur, composition éditoriale."""
    children: list[rx.Component] = [
        rx.el.span(
            index,
            class_name="ap-mono text-[10px] tracking-[0.2em] text-[#D8FA5E]",
        ),
        rx.el.h2(
            title,
            class_name="ap-serif mt-2 text-2xl md:text-3xl text-[#F2EFE4]",
        ),
    ]
    if not isinstance(description, str) or description:
        children.append(
            rx.el.p(
                description,
                class_name="mt-2 max-w-2xl text-[13px] leading-relaxed text-[#C9C5B4]/70",
            )
        )
    right = trailing if trailing is not None else rx.fragment()
    return rx.el.div(
        rx.el.div(
            rx.el.div(*children, class_name="min-w-0"),
            right,
            class_name="flex flex-wrap items-end justify-between gap-4",
        ),
        class_name=f"border-t border-[#F2EFE4]/12 pt-5 {class_name}",
    )


def stat(
    label: rx.Var | str,
    value: rx.Var | str,
    unit: rx.Var | str = "",
    caption: rx.Var | str = "",
    *,
    index: rx.Var | str = "",
    tone: str = "paper",
    icon: rx.Var | str | None = None,
) -> rx.Component:
    """Chiffre éditorial : filet supérieur, valeur en serif, légende mono."""
    value_children: list[rx.Component] = [
        rx.el.span(
            value,
            class_name=(
                "ap-serif block whitespace-nowrap text-[2.35rem] leading-[0.85] "
                f"{_tone_text(tone)}"
            ),
        )
    ]
    if not (isinstance(unit, str) and not unit):
        value_children.append(
            rx.el.span(
                unit,
                class_name=(
                    "ap-mono text-[10px] uppercase tracking-[0.16em] "
                    "text-[#C9C5B4]/55"
                ),
            )
        )
    value_row = rx.el.div(*value_children, class_name="mt-4 flex items-end gap-2")
    marks: list[rx.Component] = []
    if icon is not None:
        marks.append(
            rx.icon(icon, class_name="h-3.5 w-3.5 shrink-0 text-[#C9C5B4]/30")
        )
    if not (isinstance(index, str) and not index):
        marks.append(
            rx.el.span(
                index,
                class_name="ap-mono text-[9px] tracking-[0.2em] text-[#C9C5B4]/30",
            )
        )
    children: list[rx.Component] = [
        rx.el.div(
            rx.el.div(
                rx.el.span(label, class_name="ap-eyebrow text-[#C9C5B4]/55"),
                rx.el.div(*marks, class_name="flex shrink-0 items-start gap-2"),
                class_name="flex items-start justify-between gap-3",
            ),
            value_row,
        )
    ]
    if not isinstance(caption, str) or caption:
        children.append(
            rx.el.p(
                caption,
                class_name="mt-3 text-[11px] leading-relaxed text-[#C9C5B4]/55",
            )
        )
    return rx.el.div(
        *children,
        class_name="group border-t border-[#F2EFE4]/12 pt-4 pb-1",
    )


def meta_row(
    label: rx.Var | str,
    value: rx.Var | str,
    *,
    tone: str = "paper",
) -> rx.Component:
    """Ligne de registre : intitulé mono discret, valeur alignée à droite."""
    value_class = {
        "paper": "text-[#F2EFE4]",
        "flame": "text-[#FF8A5B]",
        "accent": "text-[#D8FA5E]",
        "muted": "text-[#C9C5B4]",
    }.get(tone, "text-[#F2EFE4]")
    return rx.el.div(
        rx.el.span(
            label,
            class_name=(
                "ap-mono text-[9px] uppercase tracking-[0.22em] text-[#C9C5B4]/40"
            ),
        ),
        rx.el.span(
            value,
            class_name=(
                "ap-mono text-right text-[10px] uppercase leading-relaxed "
                "tracking-[0.14em] " + value_class
            ),
        ),
        class_name="flex items-center justify-between gap-6 py-2",
    )


def meta_ledger(*rows: rx.Component, class_name: str = "") -> rx.Component:
    """Registre de métadonnées, filets haut et bas, sans encadré."""
    return rx.el.div(
        *rows,
        class_name=(
            "divide-y divide-[#F2EFE4]/10 border-y border-[#F2EFE4]/12 "
            f"{class_name}"
        ),
    )


def page_hero(
    eyebrow_text: rx.Var | str,
    title: rx.Component | rx.Var | str,
    lede: rx.Var | str,
    *,
    tone: str = "accent",
    meta: rx.Component | None = None,
    actions: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    """En-tête de page unique : sur-titre, titre serif, chapô, registre, actions."""
    has_right = meta is not None or actions is not None
    right_children: list[rx.Component] = []
    if meta is not None:
        right_children.append(meta)
    if actions is not None:
        right_children.append(actions)
    right = (
        rx.el.div(
            *right_children,
            class_name=(
                "flex w-full flex-col gap-5 lg:max-w-sm lg:shrink-0 lg:self-end"
            ),
        )
        if has_right
        else rx.fragment()
    )
    return rx.el.header(
        rx.el.div(
            eyebrow(eyebrow_text, tone=tone),
            rx.el.h1(
                title,
                class_name=(
                    "ap-display mt-5 text-[clamp(2.3rem,4.2vw,3.8rem)] text-[#F2EFE4]"
                ),
            ),
            rx.el.p(
                lede,
                class_name=(
                    "mt-5 max-w-2xl text-[13px] leading-relaxed text-[#C9C5B4]/70"
                ),
            ),
            class_name="min-w-0 max-w-3xl",
        ),
        right,
        class_name=(
            "flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between "
            f"lg:gap-16 {class_name}"
        ),
    )


def index_tab(
    label: rx.Var | str,
    *,
    active,
    on_click=None,
    icon: rx.Var | str | None = None,
    class_name: str = "",
) -> rx.Component:
    """Onglet éditorial : index mono souligné, sans pastille pleine."""
    children: list[rx.Component] = []
    if icon is not None:
        children.append(
            rx.icon(
                icon,
                class_name=rx.cond(
                    active,
                    "h-3.5 w-3.5 shrink-0 text-[#D8FA5E]",
                    "h-3.5 w-3.5 shrink-0 text-[#C9C5B4]/40",
                ),
            )
        )
    children.append(rx.el.span(label))
    return rx.el.button(
        *children,
        type="button",
        on_click=on_click,
        aria_pressed=active,
        class_name=rx.cond(
            active,
            "ap-mono inline-flex items-center gap-2 border-b border-[#D8FA5E] pb-2 "
            "pt-1 text-[10px] uppercase tracking-[0.18em] text-[#D8FA5E] "
            "transition-colors " + class_name,
            "ap-mono inline-flex items-center gap-2 border-b border-transparent pb-2 "
            "pt-1 text-[10px] uppercase tracking-[0.18em] text-[#C9C5B4]/55 "
            "transition-colors hover:border-[#F2EFE4]/30 hover:text-[#F2EFE4] "
            + class_name,
        ),
    )


def index_rail(
    *children: rx.Component,
    label: str = "",
    class_name: str = "",
) -> rx.Component:
    """Bandeau d'onglets éditorial, filet supérieur, retrait régulier."""
    return rx.el.nav(
        *children,
        aria_label=label,
        class_name=(
            "flex w-full flex-wrap items-center gap-x-7 gap-y-2 border-t "
            f"border-[#F2EFE4]/12 pt-3 {class_name}"
        ),
    )


def refresh_button(
    *,
    on_click=None,
    loading=None,
    label: str = "Actualiser",
    class_name: str = "",
) -> rx.Component:
    """Action principale de rafraîchissement, icône animée pendant le chargement."""
    return rx.el.button(
        rx.cond(
            loading,
            rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
            rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
        ),
        rx.el.span(label),
        type="button",
        on_click=on_click,
        disabled=loading,
        class_name=(
            "ap-mono inline-flex w-fit items-center justify-center gap-2 border "
            "border-[#D8FA5E] bg-[#D8FA5E] px-3.5 py-2.5 text-[10px] uppercase "
            "tracking-[0.18em] text-[#0A0A08] transition-colors "
            "hover:border-[#E4FF9B] hover:bg-[#E4FF9B] "
            "disabled:cursor-not-allowed disabled:opacity-45 "
            f"{class_name}"
        ),
    )


def field(
    control: rx.Component,
    *,
    icon: str = "",
    suffix: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    """Champ de saisie à filet unique, sans halo, icône à gauche."""
    children: list[rx.Component] = []
    if icon:
        children.append(
            rx.icon(
                icon,
                class_name=(
                    "pointer-events-none absolute left-3 top-1/2 h-4 w-4 "
                    "-translate-y-1/2 text-[#C9C5B4]/40"
                ),
            )
        )
    children.append(control)
    if suffix is not None:
        children.append(suffix)
    return rx.el.div(*children, class_name=f"relative w-full min-w-0 {class_name}")


def input_class(*, icon: bool = False, extra: str = "") -> str:
    """Classes du champ de saisie éditorial (filet unique, sans halo)."""
    pad = "pl-9" if icon else "pl-3"
    return (
        "w-full border border-[#F2EFE4]/14 bg-[#0F110A] py-2.5 pr-3 "
        f"{pad} text-sm text-[#F2EFE4] outline-hidden transition-colors "
        "placeholder:text-[#C9C5B4]/30 focus:border-[#D8FA5E] "
        f"{extra}"
    )


def select_field(
    *children: rx.Component,
    name: str,
    icon: str = "list-filter",
    default_value=None,
    on_change=None,
    form_key=None,
    width: str = "w-full sm:w-64",
) -> rx.Component:
    """Sélecteur à filet unique, icône à gauche, chevron discret."""
    kwargs = {"name": name}
    if default_value is not None:
        kwargs["default_value"] = default_value
    if on_change is not None:
        kwargs["on_change"] = on_change
    if form_key is not None:
        kwargs["key"] = f"{name}-{form_key}"
    return rx.el.div(
        rx.icon(
            icon,
            class_name=(
                "pointer-events-none absolute left-3 top-1/2 h-4 w-4 "
                "-translate-y-1/2 text-[#C9C5B4]/40"
            ),
        ),
        rx.el.select(
            *children,
            class_name=input_class(
                icon=True, extra="cursor-pointer appearance-none pr-9"
            ),
            **kwargs,
        ),
        rx.icon(
            "chevron-down",
            class_name=(
                "pointer-events-none absolute right-3 top-1/2 h-4 w-4 "
                "-translate-y-1/2 text-[#C9C5B4]/40"
            ),
        ),
        class_name=f"relative {width}",
    )
