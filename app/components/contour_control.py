"""Poste de contrôle des contours parcellaires (cartographie AgriPro).

Trois blocs réutilisables, sans nouvelle source de données :
* `contour_control_board()` : synthèse, distributions, filtres, fiches de
  contrôle et décisions traçables ;
* `contour_history_panel()` : journal des décisions de contour ;
* `contour_diagnostic_tile()` : tuile compacte pour le diagnostic / audit.

Identité visuelle inchangée : vert nuit, chlorophylle et ambre, surfaces
vitrées, typographie éditoriale Instrument Serif.
"""

import reflex as rx

from app.components.guide_help import help_icon_button, help_topic_button
from app.states.contour_state import (
    ContourLog,
    ContourRow,
    ContourState,
    ControlDistribution,
)

_INPUT = (
    "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 "
    "text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 "
    "focus:border-lime-300/50 outline-hidden transition-colors"
)

_SELECT = (
    "w-full appearance-none cursor-pointer rounded-xl border border-white/10 "
    "bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 "
    "focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 "
    "outline-hidden transition-colors"
)

_PRIMARY = (
    "flex items-center gap-1.5 rounded-full bg-lime-300 px-3 py-1.5 "
    "text-[11px] font-semibold text-[#04140d] hover:bg-lime-200 "
    "transition-colors w-fit"
)

_GHOST = (
    "flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 "
    "px-3 py-1.5 text-[11px] font-semibold text-emerald-100/70 "
    "hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit"
)


def _badge(tone: rx.Var, label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit whitespace-nowrap",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit whitespace-nowrap",
        ),
    )


def _tone_bar(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("good", "h-full rounded-full bg-lime-300/80"),
        ("warn", "h-full rounded-full bg-amber-300/80"),
        ("bad", "h-full rounded-full bg-red-400/80"),
        "h-full rounded-full bg-white/25",
    )


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "good",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-lime-300/30 bg-lime-300/10 text-lime-200",
        ),
        (
            "warn",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-amber-300/30 bg-amber-300/10 text-amber-200",
        ),
        (
            "bad",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-red-400/30 bg-red-500/10 text-red-300",
        ),
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-emerald-100/60",
    )


def _tile(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3",
    )


def _distribution_row(row: ControlDistribution, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.icon(row["icon"], class_name="h-3.5 w-3.5"),
                class_name=_tone_ring(row["tone"]),
            ),
            rx.el.span(
                row["label"],
                class_name="text-[12px] font-semibold text-emerald-50 truncate text-left",
            ),
            rx.el.span(
                row["value"],
                class_name=rx.cond(
                    row["value"] > 0,
                    "text-[12px] font-bold text-emerald-50 ml-auto",
                    "text-[12px] font-bold text-emerald-100/35 ml-auto",
                ),
            ),
            rx.el.span(
                row["share_pct"],
                class_name="text-[10px] font-semibold text-emerald-100/45 w-9 text-right",
            ),
            class_name="flex items-center gap-2.5 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name=_tone_bar(row["tone"]),
                style={"width": row["share_pct"]},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-2",
        ),
        on_click=ContourState.focus_control(row["key"]),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.02] p-3 hover:border-lime-300/25 transition-colors",
    )


def _gauge() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Taux de contrôle des contours",
                class_name="text-[9px] font-semibold uppercase tracking-[0.24em] text-emerald-100/45",
            ),
            _badge(ContourState.verdict_tone, ContourState.verdict_label),
            class_name="flex flex-wrap items-center justify-between gap-2 w-full",
        ),
        rx.el.div(
            rx.el.span(
                ContourState.control_rate_pct,
                class_name="font-['Instrument_Serif'] text-5xl leading-none text-emerald-50",
            ),
            rx.el.span(
                "des îlots portent une décision de contour",
                class_name="text-[11px] font-medium text-emerald-100/50 mb-1.5",
            ),
            class_name="flex items-end gap-2 w-full mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 via-lime-300 to-amber-300",
                style={"width": ContourState.control_rate_pct},
            ),
            class_name="h-2 w-full rounded-full bg-white/10 mt-4",
        ),
        rx.el.p(
            ContourState.verdict_detail,
            class_name="text-[12px] font-medium text-emerald-100/60 leading-relaxed mt-4",
        ),
        rx.el.div(
            rx.el.span(
                f"{ContourState.kpis['mapped_area']:.1f} ha tracés",
                class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-emerald-100/55 w-fit",
            ),
            rx.el.span(
                f"{ContourState.kpis['gap_area']:.2f} ha d'écart cumulé",
                class_name="rounded-full border border-amber-300/25 bg-amber-300/10 px-2.5 py-1 text-[10px] font-semibold text-amber-200 w-fit",
            ),
            rx.el.span(
                f"écart max {ContourState.kpis['gap_max']:.1f} %",
                class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-emerald-100/55 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4",
        ),
        class_name="w-full xl:w-[24rem] shrink-0 rounded-2xl border border-lime-300/20 bg-[#04140d]/70 p-5",
    )


def _select(
    name: str,
    icon: str,
    value: rx.Var | str,
    on_change: rx.event.EventType,
    first_option: rx.Component,
    options: rx.Var,
) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
        ),
        rx.el.select(
            first_option,
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=name,
            on_change=on_change,
            class_name=_SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-56",
    )


def _filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher un îlot, un code, une localité…",
                default_value=ContourState.search,
                on_change=ContourState.set_search.debounce(400),
                class_name=f"{_INPUT} pl-9",
            ),
            class_name="relative flex-1 min-w-0",
        ),
        _select(
            "contour_control_filter",
            "shapes",
            ContourState.control_filter,
            ContourState.set_control_filter,
            rx.el.option("Tous les statuts de contrôle", value="TOUS"),
            ContourState.control_options,
        ),
        _select(
            "contour_validation_filter",
            "scan-eye",
            ContourState.validation_filter,
            ContourState.set_validation_filter,
            rx.el.option("Toutes les validations", value="TOUS"),
            ContourState.validation_options,
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4"),
            rx.el.span("Réinitialiser"),
            on_click=ContourState.reset_filters,
            class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
        ),
        class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-5",
    )


def _note_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("pen-line", class_name="h-3.5 w-3.5 text-lime-300"),
            rx.el.span(
                "Traçabilité de la décision de contour",
                class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/50",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Qui contrôle ?",
                default_value=ContourState.author_draft,
                on_change=ContourState.set_author_draft.debounce(400),
                class_name=_INPUT,
            ),
            rx.el.input(
                placeholder="Pourquoi cette décision ? (relevé GPS prévu, cadastre confirmé…)",
                default_value=ContourState.note_draft,
                on_change=ContourState.set_note_draft.debounce(400),
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-[14rem_1fr] gap-3 w-full mt-3",
        ),
        rx.el.p(
            "Une vérification à l'écran reste une validation visuelle : elle ne vaut ni relevé cadastral ni mesure GPS.",
            class_name="text-[10px] font-medium text-emerald-100/40 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
    )


def _contour_card(row: ContourRow, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.icon(row["control_icon"], class_name="h-4 w-4"),
                class_name=_tone_ring(row["control_tone"]),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        row["code"],
                        class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/50",
                    ),
                    _badge(row["control_tone"], row["control_label"]),
                    _badge(row["validation_tone"], row["validation_label"]),
                    class_name="flex flex-wrap items-center gap-2 w-full",
                ),
                rx.el.p(
                    row["name"],
                    class_name="font-['Instrument_Serif'] text-xl text-emerald-50 mt-1 truncate",
                ),
                rx.el.p(
                    f"{row['locality']} · {row['source_label']} · {row['vertex_count']} sommets",
                    class_name="text-[11px] font-medium text-emerald-100/45 mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                f"Déclarée {row['declared_area']:.2f} ha",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"Contour {row['computed_area']:.2f} ha",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            _badge(
                rx.cond(row["gap_pct"] > 5.0, "bad", "good"),
                f"Écart {row['gap_label']} · {row['gap_ha']:.2f} ha",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.cond(
                    row["gap_pct"] > 5.0,
                    "h-full rounded-full bg-red-400/80",
                    "h-full rounded-full bg-lime-300/80",
                ),
                style={"width": row["gap_bar_pct"]},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-2",
        ),
        rx.el.div(
            rx.icon(
                "wrench", class_name="h-3 w-3 text-amber-300 shrink-0 mt-0.5"
            ),
            rx.el.p(
                row["recommendation"],
                class_name="text-[11px] font-medium text-amber-100/80 leading-relaxed",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3 py-2 w-full mt-3",
        ),
        rx.cond(
            row["decision_count"] > 0,
            rx.el.div(
                rx.icon("history", class_name="h-3 w-3 text-lime-300 shrink-0"),
                rx.el.p(
                    f"{row['validation_label']} · {row['last_decided_label']} · {row['last_author']} — {row['last_note']}",
                    class_name="text-[10px] font-medium text-emerald-100/55 leading-relaxed",
                ),
                rx.el.span(
                    f"{row['decision_count']} décision(s)",
                    class_name="ml-auto shrink-0 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-semibold text-emerald-100/50 w-fit",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 w-full mt-2",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("scan-eye", class_name="h-3.5 w-3.5"),
                rx.el.span("Marquer vérifié à l'écran"),
                on_click=ContourState.verify_contour(row["id"]),
                class_name=_PRIMARY,
            ),
            rx.el.button(
                rx.icon("map-pin", class_name="h-3.5 w-3.5"),
                rx.el.span("À relever sur le terrain"),
                on_click=ContourState.survey_contour(row["id"]),
                class_name=_GHOST,
            ),
            rx.el.a(
                rx.el.span("Ouvrir l'éditeur de contour"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/cartographie",
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        rx.el.div(
            help_topic_button(
                "cartographie", "geometrie", "Règle de géométrie"
            ),
            rx.cond(
                row["gap_pct"] > 5.0,
                help_topic_button(
                    "cartographie", "surface", "Règle de surface"
                ),
                rx.fragment(),
            ),
            rx.el.a(
                rx.el.span("Guide de la cartographie"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/guide",
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
            ),
            rx.el.a(
                rx.el.span("Chercher cet îlot"),
                rx.icon("radar", class_name="h-3 w-3"),
                href="/recherche",
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-2",
        ),
        rx.el.p(
            f"Géométrie mise à jour : {row['updated_label']} · {row['updated_by']}",
            class_name="text-[10px] font-medium text-emerald-100/35 mt-2",
        ),
        key=key,
        class_name=rx.match(
            row["control_tone"],
            (
                "bad",
                "w-full rounded-2xl border border-red-400/30 bg-red-500/[0.06] p-4",
            ),
            (
                "warn",
                "w-full rounded-2xl border border-amber-300/25 bg-amber-300/[0.05] p-4",
            ),
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
        ),
    )


def contour_control_board() -> rx.Component:
    """Poste de contrôle complet des contours parcellaires."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Contrôle parcellaire · géométrie",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Valider les contours d'îlots",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Chaque îlot reçoit un statut de contrôle et une décision : contour conforme, contour généré à vérifier, écart de surface à arbitrer ou contour à tracer.",
                    class_name="text-sm font-medium text-emerald-100/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    ContourState.today_label,
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
                ),
                help_icon_button("cartographie"),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            _tile(
                "Îlots audités",
                f"{ContourState.kpis['parcels']:.0f}",
                "contours",
            ),
            _tile(
                "Écarts > 5 %",
                f"{ContourState.kpis['ecart']:.0f}",
                "à arbitrer",
            ),
            _tile(
                "À vérifier",
                f"{ContourState.kpis['a_verifier']:.0f}",
                "générés",
            ),
            _tile(
                "Sans contour",
                f"{ContourState.kpis['sans_contour']:.0f}",
                "à tracer",
            ),
            _tile(
                "Vérifiés",
                f"{ContourState.kpis['verifie']:.0f}",
                "à l'écran",
            ),
            _tile(
                "Relevés demandés",
                f"{ContourState.kpis['a_relever']:.0f}",
                "terrain",
            ),
            class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full mt-5",
        ),
        rx.el.div(
            _gauge(),
            rx.el.div(
                rx.el.span(
                    "Répartition des statuts de contrôle",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.div(
                    rx.foreach(
                        ContourState.control_distribution,
                        lambda row: _distribution_row(row, key=row["key"]),
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full mt-3",
                ),
                class_name="flex-1 min-w-0 w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
            ),
            class_name="flex flex-col xl:flex-row gap-3 w-full mt-3",
        ),
        rx.cond(
            ContourState.geometry_ready,
            rx.fragment(),
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 text-amber-300 shrink-0",
                ),
                rx.el.p(
                    "Les colonnes de géométrie sont indisponibles : les contours affichés sont générés à la volée et le contrôle reste indicatif.",
                    class_name="text-xs font-medium text-amber-100/80",
                ),
                class_name="flex items-center gap-2 rounded-2xl border border-amber-300/25 bg-amber-300/[0.07] px-4 py-3 w-full mt-4",
            ),
        ),
        _filters(),
        _note_bar(),
        rx.cond(
            ContourState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-40 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-40 rounded-2xl bg-white/[0.05]"
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-4",
            ),
            rx.cond(
                ContourState.has_items,
                rx.el.div(
                    rx.foreach(
                        ContourState.items,
                        lambda row: _contour_card(
                            row, key=row["id"].to_string()
                        ),
                    ),
                    class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-4",
                ),
                rx.el.div(
                    rx.icon("circle-check", class_name="h-6 w-6 text-lime-300"),
                    rx.el.p(
                        "Aucun îlot ne correspond à ce périmètre de contrôle.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 w-full mt-4",
                ),
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _log_row(item: ContourLog, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-3.5 w-3.5"),
            class_name=_tone_ring(item["tone"]),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["label"],
                    class_name="text-[12px] font-semibold text-emerald-50 truncate",
                ),
                _badge(item["tone"], item["action_label"]),
                rx.el.span(
                    item["date_label"],
                    class_name="text-[10px] font-medium text-emerald-100/40 ml-auto shrink-0",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
            ),
            rx.el.p(
                f"{item['author']} — {item['note']}",
                class_name="text-[11px] font-medium text-emerald-100/50 mt-1 leading-relaxed",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.a(
            rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
            href="/cartographie",
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-emerald-100/60 hover:text-emerald-50 hover:border-lime-300/30 transition-colors",
        ),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-2xl border border-white/10 bg-white/[0.02] p-3",
    )


def contour_history_panel() -> rx.Component:
    """Journal des décisions de contour, réutilisable par le diagnostic."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Historique des décisions",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Journal de contrôle des contours",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Qui a validé quel îlot, quand et pourquoi : la trace rend le contrôle relisible plusieurs campagnes plus tard.",
                    class_name="text-sm font-medium text-emerald-100/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{ContourState.kpis['decisions']:.0f} décision(s) consignée(s)",
                class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[11px] font-bold text-lime-200 w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            ContourState.has_logs,
            rx.el.ul(
                rx.foreach(
                    ContourState.logs,
                    lambda item: _log_row(item, key=item["id"].to_string()),
                ),
                class_name="flex flex-col gap-2 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("history", class_name="h-6 w-6 text-lime-300"),
                rx.el.p(
                    "Aucune décision de contour consignée pour le moment.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 w-full mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def contour_diagnostic_tile() -> rx.Component:
    """Tuile compacte du contrôle des contours pour le diagnostic / audit."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Diagnostic · géométrie parcellaire",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Contrôle des contours d'îlots",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    ContourState.verdict_detail,
                    class_name="text-sm font-medium text-emerald-100/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _badge(ContourState.verdict_tone, ContourState.verdict_label),
                rx.el.a(
                    rx.el.span("Ouvrir la cartographie"),
                    rx.icon("arrow-up-right", class_name="h-3 w-3"),
                    href="/cartographie",
                    class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
                ),
                help_topic_button(
                    "cartographie", "geometrie", "Règle de géométrie"
                ),
                help_icon_button("cartographie"),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            _tile(
                "Taux de contrôle",
                ContourState.control_rate_pct,
                "des îlots",
            ),
            _tile(
                "En attente",
                f"{ContourState.open_total}",
                "décisions",
            ),
            _tile(
                "Écarts > 5 %",
                f"{ContourState.kpis['ecart']:.0f}",
                "îlots",
            ),
            _tile(
                "Écart cumulé",
                f"{ContourState.kpis['gap_area']:.2f}",
                "ha",
            ),
            class_name="grid grid-cols-2 md:grid-cols-4 gap-3 w-full mt-5",
        ),
        rx.el.div(
            rx.foreach(
                ContourState.control_distribution,
                lambda row: _distribution_row(row, key=row["key"]),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 w-full mt-3",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
