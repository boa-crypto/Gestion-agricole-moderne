"""Panneaux phénologiques contextuels réutilisables (UI AgriPro).

Lectures uniquement : stade actuel, prochain stade, recommandations
indicatives par domaine (irrigation, fertilisation, traitements/surveillance,
récolte) et alertes contextuelles à vérifier. Aucun bouton ne crée
d'intervention automatiquement.
"""

import reflex as rx

from app.phenology_ops import AlertRow, PlannedRow, RecoRow, StageContextRow
from app.states.phenology_ops_state import PhenologyOpsState

_SELECT = "w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 outline-hidden transition-colors"


def _badge(tone: rx.Var | str, label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit",
        ),
    )


def _tile(
    label: str, value: rx.Var | str, unit: str, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
            ),
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300 ml-auto"),
            class_name="flex items-start gap-2",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-3xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-3",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur-xl",
    )


def phenology_kpis() -> rx.Component:
    """Bandeau d'indicateurs phénologiques consolidés."""
    return rx.el.section(
        _tile(
            "Cultures suivies",
            PhenologyOpsState.row_count,
            "fiches culturales",
            "sprout",
        ),
        _tile(
            "Stades observés",
            PhenologyOpsState.observed_count,
            "observations à jour",
            "clipboard-check",
        ),
        _tile(
            "Sans observation",
            PhenologyOpsState.missing_observation_count,
            "à consigner",
            "eye-off",
        ),
        _tile(
            "Stades sensibles",
            PhenologyOpsState.critical_count,
            "à surveiller",
            "triangle-alert",
        ),
        _tile(
            "Avancement moyen",
            f"{PhenologyOpsState.average_progress:.0f}",
            "% du cycle",
            "gauge",
        ),
        _tile(
            "Récoltes proches",
            PhenologyOpsState.harvest_soon_count,
            "sous 21 jours",
            "wheat",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full",
    )


def phenology_filters() -> rx.Component:
    """Filtre « Afficher par stade » et recherche contextuelle."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Parcelle, culture, stade…",
                    default_value=PhenologyOpsState.search,
                    on_change=PhenologyOpsState.set_search.debounce(400),
                    class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden transition-colors",
                ),
                class_name="relative w-full",
            ),
            rx.el.div(
                rx.icon(
                    "sprout",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
                ),
                rx.el.select(
                    rx.el.option("Tous les stades", value="TOUS"),
                    rx.foreach(
                        PhenologyOpsState.stage_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    value=PhenologyOpsState.stage_filter,
                    on_change=PhenologyOpsState.set_stage_filter,
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=PhenologyOpsState.reset_filters,
                class_name="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-full lg:w-fit",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-3 gap-3 w-full",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )


def _context_row(row: StageContextRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-full",
            style={"backgroundColor": row["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    row["parcel_code"],
                    class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-lime-300/80",
                ),
                rx.el.p(
                    row["crop_name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{row['culture_name']} · campagne {row['season']}",
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                _badge(row["status_tone"], row["status_label"]),
                rx.cond(
                    row["is_critical"],
                    _badge("warn", "Stade sensible"),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-1.5 shrink-0",
            ),
            class_name="flex items-start gap-3 mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Stade actuel",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.p(
                    row["stage_name"],
                    class_name="text-sm font-semibold text-emerald-50 mt-1 truncate",
                ),
                class_name="min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Prochain stade",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.p(
                    row["next_stage"],
                    class_name="text-sm font-semibold text-emerald-50 mt-1 truncate",
                ),
                class_name="min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Dans le stade",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.p(
                    f"{row['days_in_stage']} j",
                    class_name="text-sm font-semibold text-emerald-50 mt-1",
                ),
                class_name="min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Récolte prévue",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.p(
                    row["harvest_label"],
                    class_name="text-sm font-semibold text-emerald-50 mt-1 truncate",
                ),
                class_name="min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                style={"width": row["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-4",
        ),
        rx.el.div(
            _badge(row["duration_tone"], row["duration_label"]),
            _badge("muted", row["duration_hint"]),
            rx.cond(
                row["bbch"] != "",
                _badge("muted", row["bbch"]),
                rx.fragment(),
            ),
            rx.el.span(
                f"{row['observed_label']} · {row['observer']}",
                class_name="text-[10px] font-medium text-emerald-100/45 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-white/5",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def phenology_stage_board() -> rx.Component:
    """État phénologique multi-parcelles / multi-cultures."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Pilotage phénologique",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "État des stades par parcelle et par culture",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Lecture seule : le stade observé, le prochain stade et la durée dans le stade. Aucune intervention n'est créée automatiquement.",
                    class_name="text-xs font-medium text-emerald-100/50 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{PhenologyOpsState.row_count} culture(s) suivie(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.cond(
            PhenologyOpsState.rows.length() > 0,
            rx.el.div(
                rx.foreach(
                    PhenologyOpsState.rows,
                    lambda row: _context_row(
                        row, key=row["crop_id"].to_string()
                    ),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-5",
            ),
            rx.el.p(
                "Aucune culture ne correspond à ce filtre de stade.",
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _alert_card(alert: AlertRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                alert["icon"], class_name="h-4 w-4 text-amber-300 shrink-0"
            ),
            _badge(alert["tone"], alert["kind_label"]),
            rx.el.a(
                rx.el.span("Voir le suivi", class_name="text-lime-200"),
                rx.icon("arrow-up-right", class_name="h-3 w-3 text-lime-200"),
                href=alert["route"],
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/30 bg-lime-300/10 px-2.5 py-1 text-[10px] font-semibold hover:bg-lime-300/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.p(
            alert["title"],
            class_name="text-sm font-semibold text-emerald-50 mt-2",
        ),
        rx.el.p(
            alert["message"],
            class_name="text-[11px] font-medium text-emerald-100/55 mt-1.5 leading-relaxed",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.02] p-4",
    )


def phenology_alerts_panel() -> rx.Component:
    """Alertes contextuelles à vérifier, jamais conclusives."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Anomalies à vérifier",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Alertes phénologiques contextuelles",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Absence d'observation, stade sensible, durée inhabituelle, récolte proche : constats à contrôler sur le terrain.",
                    class_name="text-xs font-medium text-emerald-100/50 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{PhenologyOpsState.alert_count} constat(s)",
                class_name="rounded-full border border-amber-300/25 bg-amber-300/10 px-3 py-1 text-[11px] font-semibold text-amber-200 w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.cond(
            PhenologyOpsState.alerts.length() > 0,
            rx.el.div(
                rx.foreach(
                    PhenologyOpsState.alerts,
                    lambda alert: _alert_card(alert, key=alert["key"]),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 mt-5",
            ),
            rx.el.p(
                "Aucune anomalie phénologique à vérifier pour ce périmètre.",
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _reco_card(reco: RecoRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(reco["icon"], class_name="h-3.5 w-3.5 text-lime-300"),
            rx.el.span(
                reco["domain_label"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            _badge("muted", reco["stage_name"]),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.p(
            reco["title"],
            class_name="text-sm font-semibold text-emerald-50 mt-1.5",
        ),
        rx.el.p(
            reco["statement"],
            class_name="text-[11px] font-medium text-emerald-100/55 mt-1.5 leading-relaxed",
        ),
        rx.el.div(
            _badge("info", reco["confidence_label"]),
            rx.el.span(
                reco["source"],
                class_name="text-[10px] font-medium text-emerald-100/40 truncate",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-white/5",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.02] p-4",
    )


def _domain_block(
    title: str, icon: str, items: rx.Var[list[RecoRow]], route: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                title,
                class_name="text-[11px] font-semibold uppercase tracking-[0.22em] text-lime-300/80",
            ),
            rx.el.a(
                rx.el.span(
                    "Ouvrir le module", class_name="text-emerald-100/70"
                ),
                rx.icon(
                    "arrow-up-right", class_name="h-3 w-3 text-emerald-100/70"
                ),
                href=route,
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold hover:border-lime-300/30 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.cond(
            items.length() > 0,
            rx.el.div(
                rx.foreach(items, lambda reco: _reco_card(reco)),
                class_name="grid grid-cols-1 gap-3 mt-3",
            ),
            rx.el.p(
                "Aucune opération associée aux stades en cours pour ce domaine.",
                class_name="text-[11px] font-medium text-emerald-100/45 mt-3",
            ),
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def phenology_operations_panel() -> rx.Component:
    """Opérations généralement associées aux stades, par module opérationnel."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Lecture opérationnelle",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Opérations associées aux stades en cours",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                "Informations indicatives : aucune dose, aucun produit phytosanitaire non sourcé, aucune intervention créée automatiquement.",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium text-emerald-100/55 w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.el.div(
            _domain_block(
                "Irrigation",
                "droplets",
                PhenologyOpsState.irrigation_recommendations,
                "/traitements",
            ),
            _domain_block(
                "Fertilisation",
                "flask-conical",
                PhenologyOpsState.fertilisation_recommendations,
                "/traitements",
            ),
            _domain_block(
                "Traitements & surveillance",
                "shield-check",
                PhenologyOpsState.treatment_recommendations,
                "/traitements",
            ),
            _domain_block(
                "Récolte & travaux",
                "wheat",
                PhenologyOpsState.harvest_recommendations,
                "/traitements",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _planned_row(item: PlannedRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            item["parcel_code"],
            class_name="px-4 py-3 text-xs font-semibold text-lime-200 whitespace-nowrap",
        ),
        rx.el.td(
            item["crop_name"],
            class_name="px-4 py-3 text-xs font-medium text-emerald-50",
        ),
        rx.el.td(
            item["stage_name"],
            class_name="px-4 py-3 text-xs font-medium text-emerald-100/70",
        ),
        rx.el.td(
            item["expected_label"],
            class_name="px-4 py-3 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            item["observed_label"],
            class_name="px-4 py-3 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            _badge(item["tone"], item["delta_label"]),
            class_name="px-4 py-3",
        ),
        key=key,
        class_name="border-b border-white/5 even:bg-white/[0.02] hover:bg-white/[0.05] transition-colors",
    )


def phenology_planned_panel() -> rx.Component:
    """Comparaison prévu / réel, uniquement quand les données existent."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Prévision contre réalité",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Calendrier phénologique prévu / réel",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Date attendue calculée depuis le semis et les durées indicatives du référentiel, comparée à l'observation de terrain.",
                    class_name="text-xs font-medium text-emerald-100/50 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _badge(
                    "warn",
                    f"{PhenologyOpsState.late_count} retard(s) constaté(s)",
                ),
                _badge(
                    "info",
                    f"{PhenologyOpsState.early_count} avance(s) constatée(s)",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.cond(
            PhenologyOpsState.has_planned_data,
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th(
                                "Îlot",
                                class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                            ),
                            rx.el.th(
                                "Culture",
                                class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                            ),
                            rx.el.th(
                                "Stade",
                                class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                            ),
                            rx.el.th(
                                "Prévu",
                                class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                            ),
                            rx.el.th(
                                "Réel",
                                class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                            ),
                            rx.el.th(
                                "Écart",
                                class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                            ),
                            class_name="border-b border-white/10 bg-white/[0.03]",
                        ),
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            PhenologyOpsState.planned,
                            lambda item: _planned_row(item, key=item["key"]),
                        ),
                    ),
                    class_name="table-auto w-full",
                ),
                class_name="w-full overflow-x-auto overflow-hidden rounded-2xl border border-white/10 mt-5",
            ),
            rx.el.p(
                "Comparaison indisponible : il manque des dates de semis ou des durées indicatives de stade.",
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
