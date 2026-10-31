"""Panneaux phénologiques contextuels réutilisables (UI AgriPro).

Lectures uniquement : stade actuel, prochain stade, recommandations
indicatives par domaine (irrigation, fertilisation, traitements/surveillance,
récolte) et alertes contextuelles à vérifier. Aucun bouton ne crée
d'intervention automatiquement.
"""

import reflex as rx

from app.phenology_ops import AlertRow, PlannedRow, RecoRow, StageContextRow
from app.states.phenology_ops_state import PhenologyOpsState

_SELECT = "w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 outline-hidden transition-colors"


def _badge(tone: rx.Var | str, label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
        ),
    )


def _tile(
    label: str, value: rx.Var | str, unit: str, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e] ml-auto"),
            class_name="flex items-start gap-2",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-3xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-3",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] p-4 ",
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
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Parcelle, culture, stade…",
                    default_value=PhenologyOpsState.search,
                    on_change=PhenologyOpsState.set_search.debounce(400),
                    class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-3 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 outline-hidden transition-colors",
                ),
                class_name="relative w-full",
            ),
            rx.el.div(
                rx.icon(
                    "sprout",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
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
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=PhenologyOpsState.reset_filters,
                class_name="flex items-center justify-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-full lg:w-fit",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-3 gap-3 w-full",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )


def _context_row(row: StageContextRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": row["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    row["parcel_code"],
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.p(
                    row["crop_name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{row['culture_name']} · campagne {row['season']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 truncate mt-0.5",
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
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.p(
                    row["stage_name"],
                    class_name="text-sm font-semibold text-[#f2efe4] mt-1 truncate",
                ),
                class_name="min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Prochain stade",
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.p(
                    row["next_stage"],
                    class_name="text-sm font-semibold text-[#f2efe4] mt-1 truncate",
                ),
                class_name="min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Dans le stade",
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.p(
                    f"{row['days_in_stage']} j",
                    class_name="text-sm font-semibold text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Récolte prévue",
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.p(
                    row["harvest_label"],
                    class_name="text-sm font-semibold text-[#f2efe4] mt-1 truncate",
                ),
                class_name="min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                style={"width": row["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-4",
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
                class_name="text-[10px] font-medium text-[#c9c5b4]/45 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def phenology_stage_board() -> rx.Component:
    """État phénologique multi-parcelles / multi-cultures."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Pilotage phénologique",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "État des stades par parcelle et par culture",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Lecture seule : le stade observé, le prochain stade et la durée dans le stade. Aucune intervention n'est créée automatiquement.",
                    class_name="text-xs font-medium text-[#c9c5b4]/50 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{PhenologyOpsState.row_count} culture(s) suivie(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
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
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def _alert_card(alert: AlertRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                alert["icon"], class_name="h-4 w-4 text-[#ff8a5b] shrink-0"
            ),
            _badge(alert["tone"], alert["kind_label"]),
            rx.el.a(
                rx.el.span("Voir le suivi", class_name="text-[#e4ff9b]"),
                rx.icon("arrow-up-right", class_name="h-3 w-3 text-[#e4ff9b]"),
                href=alert["route"],
                class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2.5 py-1 text-[10px] font-semibold hover:bg-[#d8fa5e]/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.p(
            alert["title"],
            class_name="text-sm font-semibold text-[#f2efe4] mt-2",
        ),
        rx.el.p(
            alert["message"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1.5 leading-relaxed",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-4",
    )


def phenology_alerts_panel() -> rx.Component:
    """Alertes contextuelles à vérifier, jamais conclusives."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Anomalies à vérifier",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Alertes phénologiques contextuelles",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Absence d'observation, stade sensible, durée inhabituelle, récolte proche : constats à contrôler sur le terrain.",
                    class_name="text-xs font-medium text-[#c9c5b4]/50 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{PhenologyOpsState.alert_count} constat(s)",
                class_name="rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/10 px-3 py-1 text-[11px] font-semibold text-[#ffb894] w-fit",
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
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def _reco_card(reco: RecoRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(reco["icon"], class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
            rx.el.span(
                reco["domain_label"],
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            _badge("muted", reco["stage_name"]),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.p(
            reco["title"],
            class_name="text-sm font-semibold text-[#f2efe4] mt-1.5",
        ),
        rx.el.p(
            reco["statement"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1.5 leading-relaxed",
        ),
        rx.el.div(
            _badge("info", reco["confidence_label"]),
            rx.el.span(
                reco["source"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 truncate",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-4",
    )


def _domain_block(
    title: str, icon: str, items: rx.Var[list[RecoRow]], route: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-[#d8fa5e]"),
            rx.el.span(
                title,
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.a(
                rx.el.span(
                    "Ouvrir le module", class_name="text-[#c9c5b4]/70"
                ),
                rx.icon(
                    "arrow-up-right", class_name="h-3 w-3 text-[#c9c5b4]/70"
                ),
                href=route,
                class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[10px] font-semibold hover:border-[#d8fa5e]/30 transition-colors w-fit ml-auto",
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
                class_name="text-[11px] font-medium text-[#c9c5b4]/45 mt-3",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def phenology_operations_panel() -> rx.Component:
    """Opérations généralement associées aux stades, par module opérationnel."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Lecture opérationnelle",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Opérations associées aux stades en cours",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                "Informations indicatives : aucune dose, aucun produit phytosanitaire non sourcé, aucune intervention créée automatiquement.",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[10px] font-medium text-[#c9c5b4]/55 w-fit",
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
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def _planned_row(item: PlannedRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            item["parcel_code"],
            class_name="px-4 py-3 text-xs font-semibold text-[#e4ff9b] whitespace-nowrap",
        ),
        rx.el.td(
            item["crop_name"],
            class_name="px-4 py-3 text-xs font-medium text-[#f2efe4]",
        ),
        rx.el.td(
            item["stage_name"],
            class_name="px-4 py-3 text-xs font-medium text-[#c9c5b4]/70",
        ),
        rx.el.td(
            item["expected_label"],
            class_name="px-4 py-3 text-xs font-medium text-[#c9c5b4]/60 whitespace-nowrap",
        ),
        rx.el.td(
            item["observed_label"],
            class_name="px-4 py-3 text-xs font-medium text-[#c9c5b4]/60 whitespace-nowrap",
        ),
        rx.el.td(
            _badge(item["tone"], item["delta_label"]),
            class_name="px-4 py-3",
        ),
        key=key,
        class_name="border-b border-[#f2efe4]/8 even:bg-[#0d0f09] hover:bg-[#16190f] transition-colors",
    )


def phenology_planned_panel() -> rx.Component:
    """Comparaison prévu / réel, uniquement quand les données existent."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Prévision contre réalité",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Calendrier phénologique prévu / réel",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Date attendue calculée depuis le semis et les durées indicatives du référentiel, comparée à l'observation de terrain.",
                    class_name="text-xs font-medium text-[#c9c5b4]/50 mt-2 max-w-2xl",
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
                                class_name="px-4 py-3 text-left ap-eyebrow text-[#c9c5b4]/45",
                            ),
                            rx.el.th(
                                "Culture",
                                class_name="px-4 py-3 text-left ap-eyebrow text-[#c9c5b4]/45",
                            ),
                            rx.el.th(
                                "Stade",
                                class_name="px-4 py-3 text-left ap-eyebrow text-[#c9c5b4]/45",
                            ),
                            rx.el.th(
                                "Prévu",
                                class_name="px-4 py-3 text-left ap-eyebrow text-[#c9c5b4]/45",
                            ),
                            rx.el.th(
                                "Réel",
                                class_name="px-4 py-3 text-left ap-eyebrow text-[#c9c5b4]/45",
                            ),
                            rx.el.th(
                                "Écart",
                                class_name="px-4 py-3 text-left ap-eyebrow text-[#c9c5b4]/45",
                            ),
                            class_name="border-b border-[#f2efe4]/12 bg-[#101208]",
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
                class_name="w-full overflow-x-auto overflow-hidden rounded-none border border-[#f2efe4]/12 mt-5",
            ),
            rx.el.p(
                "Comparaison indisponible : il manque des dates de semis ou des durées indicatives de stade.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
