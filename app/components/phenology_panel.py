"""Section « Suivi phénologique » de la fiche parcelle / culture."""

import reflex as rx

from app.components.phenology_form import phenology_form
from app.components.phenology_rail import phenology_rail
from app.states.phenology_state import (
    GuideLink,
    HistoryRow,
    ObsRow,
    PhenologyState,
    RecoRow,
)


def _tone_badge(tone: rx.Var, label: rx.Var | str) -> rx.Component:
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


def _fact(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-sm font-semibold text-emerald-50 mt-1.5 truncate",
        ),
        class_name="w-full min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
    )


def _header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Suivi phénologique",
                class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
            ),
            rx.el.h3(
                "Cycle de la culture",
                class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
            ),
            rx.el.p(
                f"{PhenologyState.parcel_label} · {PhenologyState.summary['culture_name']}",
                class_name="text-[11px] font-medium text-emerald-100/50 mt-1",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.select(
                    rx.el.option("Culture suivie", value="", disabled=True),
                    rx.foreach(
                        PhenologyState.crop_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    value=PhenologyState.selected_crop_id.to_string(),
                    on_change=PhenologyState.select_crop,
                    class_name="w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2 pl-3 pr-9 text-xs font-medium text-emerald-50 focus:border-lime-300/50 outline-hidden",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full sm:w-72",
            ),
            rx.el.button(
                rx.cond(
                    PhenologyState.is_loading,
                    rx.icon(
                        "loader-circle",
                        class_name="h-3.5 w-3.5 animate-spin text-emerald-100/70",
                    ),
                    rx.icon(
                        "refresh-cw",
                        class_name="h-3.5 w-3.5 text-emerald-100/70",
                    ),
                ),
                rx.el.span("Actualiser", class_name="text-[11px]"),
                on_click=PhenologyState.load_phenology,
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 lg:justify-end",
        ),
        class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
    )


def _profile_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("git-branch", class_name="h-4 w-4 text-lime-300"),
                rx.el.span(
                    PhenologyState.summary["profile_name"],
                    class_name="text-sm font-semibold text-emerald-50",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.div(
                _tone_badge("info", PhenologyState.summary["scope_label"]),
                _tone_badge("muted", PhenologyState.summary["system_label"]),
                rx.cond(
                    PhenologyState.summary["is_critical"] == "1",
                    _tone_badge("warn", "Stade critique"),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-1.5",
            ),
            class_name="flex flex-col sm:flex-row sm:items-center justify-between gap-2 w-full",
        ),
        rx.cond(
            PhenologyState.summary["profile_summary"] != "",
            rx.el.p(
                PhenologyState.summary["profile_summary"],
                class_name="text-[11px] font-medium text-emerald-100/55 mt-2 leading-relaxed",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _summary_grid() -> rx.Component:
    return rx.el.div(
        _fact(
            "Stade actuel",
            PhenologyState.summary["current_stage"],
            "sprout",
        ),
        _fact(
            "Stade précédent",
            PhenologyState.summary["previous_stage"],
            "arrow-left",
        ),
        _fact(
            "Prochain stade",
            PhenologyState.summary["next_stage"],
            "arrow-right",
        ),
        _fact(
            "Progression",
            PhenologyState.summary["progress_pct"],
            "gauge",
        ),
        _fact(
            "Stades réalisés",
            f"{PhenologyState.summary['stages_done']} / {PhenologyState.summary['stage_count']}",
            "list-checks",
        ),
        _fact(
            "Dernière observation",
            PhenologyState.summary["last_observation"],
            "calendar-check",
        ),
        _fact(
            "Observateur",
            PhenologyState.summary["last_observer"],
            "user-round",
        ),
        _fact(
            "Durée dans le stade",
            f"{PhenologyState.summary['days_in_stage']} j",
            "timer",
        ),
        class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full mt-4",
    )


def _status_line() -> rx.Component:
    return rx.el.div(
        _tone_badge(
            PhenologyState.summary["last_status_tone"],
            PhenologyState.summary["last_status"],
        ),
        _tone_badge(
            PhenologyState.summary["duration_tone"],
            PhenologyState.summary["duration_label"],
        ),
        rx.cond(
            PhenologyState.summary["bbch"] != "",
            _tone_badge("muted", PhenologyState.summary["bbch"]),
            rx.fragment(),
        ),
        class_name="flex flex-wrap items-center gap-2 w-full mt-3",
    )


def _reco_card(reco: RecoRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(reco["icon"], class_name="h-3.5 w-3.5 text-lime-300"),
            rx.el.span(
                reco["domain_label"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            reco["title"],
            class_name="text-sm font-semibold text-emerald-50 mt-1.5",
        ),
        rx.el.p(
            reco["statement"],
            class_name="text-[11px] font-medium text-emerald-100/60 mt-1.5 leading-relaxed",
        ),
        rx.el.div(
            _tone_badge("info", reco["confidence_label"]),
            rx.el.span(
                reco["source"],
                class_name="text-[10px] font-medium text-emerald-100/40 truncate",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-white/5",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.02] p-4",
    )


def _recommendations() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Opérations généralement associées",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.span(
                "Informations indicatives, jamais prescriptives",
                class_name="text-[10px] font-medium text-emerald-100/40 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full",
        ),
        rx.cond(
            PhenologyState.recommendations.length() > 0,
            rx.el.div(
                rx.foreach(
                    PhenologyState.recommendations,
                    lambda reco: _reco_card(reco),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-3",
            ),
            rx.el.p(
                "Aucune opération associée à ce stade dans le référentiel.",
                class_name="text-[11px] font-medium text-emerald-100/45 mt-3",
            ),
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-4",
    )


def _guide_card(link: GuideLink) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon("book-open", class_name="h-3.5 w-3.5 text-lime-300"),
            rx.el.span(
                link["title"],
                class_name="text-[12px] font-semibold text-emerald-50 truncate",
            ),
            rx.icon(
                "arrow-up-right",
                class_name="h-3 w-3 shrink-0 text-emerald-100/35 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            link["subtitle"],
            class_name="text-[10px] font-medium text-emerald-100/50 mt-1.5 leading-relaxed",
        ),
        href=link["route"],
        class_name="block w-full rounded-2xl border border-white/10 bg-white/[0.02] p-3 hover:border-lime-300/25 hover:bg-white/[0.05] transition-colors",
    )


def _guide_block() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "Comprendre ce stade — Guide Agricole",
            class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
        ),
        rx.cond(
            PhenologyState.guide_links.length() > 0,
            rx.el.div(
                rx.foreach(
                    PhenologyState.guide_links,
                    lambda link: _guide_card(link),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full mt-3",
            ),
            rx.el.p(
                "Aucun article du Guide rattaché pour l'instant.",
                class_name="text-[11px] font-medium text-emerald-100/45 mt-3",
            ),
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-4",
    )


def _observation_row(obs: ObsRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                obs["stage_name"],
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            _tone_badge(obs["status_tone"], obs["status_label"]),
            _tone_badge("muted", obs["source_label"]),
            rx.el.span(
                rx.cond(
                    obs["time_label"] != "",
                    f"{obs['date_label']} · {obs['time_label']}",
                    obs["date_label"],
                ),
                class_name="text-[10px] font-medium text-emerald-100/45 ml-auto shrink-0",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            obs["comment"],
            class_name="text-[11px] font-medium text-emerald-100/60 mt-2 leading-relaxed",
        ),
        rx.el.div(
            rx.cond(
                obs["vigour"] != "",
                _tone_badge("info", f"Vigueur : {obs['vigour']}"),
                rx.fragment(),
            ),
            rx.cond(
                obs["homogeneity"] != "",
                _tone_badge("info", f"Homogénéité : {obs['homogeneity']}"),
                rx.fragment(),
            ),
            rx.cond(
                obs["anomalies"] != "",
                _tone_badge("warn", f"Anomalies : {obs['anomalies']}"),
                rx.fragment(),
            ),
            rx.cond(
                obs["diseases"] != "",
                _tone_badge("bad", f"Maladies : {obs['diseases']}"),
                rx.fragment(),
            ),
            rx.cond(
                obs["pests"] != "",
                _tone_badge("bad", f"Ravageurs : {obs['pests']}"),
                rx.fragment(),
            ),
            rx.cond(
                obs["water_stress"],
                _tone_badge("warn", "Stress hydrique"),
                rx.fragment(),
            ),
            rx.cond(
                obs["thermal_stress"],
                _tone_badge("warn", "Stress thermique"),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-2",
        ),
        rx.el.div(
            rx.icon("user-round", class_name="h-3 w-3 text-emerald-300/70"),
            rx.el.span(
                obs["observer"],
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                f"{obs['progress']}% du cycle",
                class_name="text-[10px] font-bold text-lime-200 ml-auto",
            ),
            class_name="flex items-center gap-1.5 mt-2 pt-2 border-t border-white/5",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.02] p-3",
    )


def _history_row(item: HistoryRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                class_name="h-2.5 w-2.5 rounded-full bg-lime-300 ring-4 ring-lime-300/15"
            ),
            class_name="relative flex flex-col items-center pt-1.5",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    item["previous_stage"],
                    class_name="text-[11px] font-medium text-emerald-100/50",
                ),
                rx.icon(
                    "arrow-right",
                    class_name="h-3 w-3 text-emerald-100/35",
                ),
                rx.el.span(
                    item["new_stage"],
                    class_name="text-xs font-semibold text-emerald-50",
                ),
                rx.el.span(
                    item["date_label"],
                    class_name="text-[10px] font-medium text-emerald-100/45 ml-auto shrink-0",
                ),
                class_name="flex flex-wrap items-center gap-2 min-w-0",
            ),
            rx.el.p(
                item["comment"],
                class_name="text-[11px] font-medium text-emerald-100/55 mt-1 leading-relaxed",
            ),
            rx.el.div(
                rx.icon("user-round", class_name="h-3 w-3 text-emerald-300/70"),
                rx.el.span(
                    item["author"],
                    class_name="text-[10px] font-medium text-emerald-100/45",
                ),
                class_name="flex items-center gap-1.5 mt-1.5",
            ),
            class_name="min-w-0 flex-1 pb-5",
        ),
        class_name="flex gap-3 w-full",
    )


def _journal() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Observations consignées",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.span(
                    f"{PhenologyState.observation_count} observation(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.cond(
                PhenologyState.observations.length() > 0,
                rx.el.div(
                    rx.foreach(
                        PhenologyState.observations,
                        lambda obs: _observation_row(obs),
                    ),
                    class_name="flex flex-col gap-3 mt-3 max-h-[32rem] overflow-y-auto pr-1",
                ),
                rx.el.p(
                    "Aucune observation pour cette culture : consignez le premier stade.",
                    class_name="text-[11px] font-medium text-emerald-100/45 mt-3",
                ),
            ),
            class_name="flex-1 min-w-0 rounded-2xl border border-white/10 bg-white/[0.03] p-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Historique des changements",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.span(
                    f"{PhenologyState.history_count} changement(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                "L'historique est conservé intégralement : aucune correction n'efface le passé.",
                class_name="text-[10px] font-medium text-emerald-100/40 mt-1.5",
            ),
            rx.cond(
                PhenologyState.history.length() > 0,
                rx.el.div(
                    rx.el.div(
                        class_name="absolute left-[5px] top-2 bottom-2 w-px bg-gradient-to-b from-lime-300/50 via-emerald-400/25 to-transparent",
                    ),
                    rx.foreach(
                        PhenologyState.history,
                        lambda item: _history_row(item),
                    ),
                    class_name="relative flex flex-col mt-4 max-h-[32rem] overflow-y-auto pr-1",
                ),
                rx.el.p(
                    "Aucun changement de stade enregistré.",
                    class_name="text-[11px] font-medium text-emerald-100/45 mt-3",
                ),
            ),
            class_name="w-full xl:w-[26rem] shrink-0 rounded-2xl border border-white/10 bg-white/[0.03] p-4",
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full mt-4",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-24 rounded-2xl bg-white/[0.05]"),
        rx.el.div(class_name="animate-pulse h-40 rounded-2xl bg-white/[0.05]"),
        rx.el.div(class_name="animate-pulse h-56 rounded-2xl bg-white/[0.05]"),
        class_name="flex flex-col gap-4 w-full mt-4",
    )


def _empty() -> rx.Component:
    return rx.el.div(
        rx.icon("sprout", class_name="h-6 w-6 text-lime-300"),
        rx.el.p(
            "Aucun profil phénologique n'est rattaché à cette culture : reliez-la "
            "à une variété du référentiel pour activer le suivi des stades.",
            class_name="text-sm font-medium text-emerald-100/55 mt-3 text-center max-w-lg",
        ),
        rx.el.a(
            rx.el.span("Ouvrir le référentiel", class_name="text-lime-200"),
            rx.icon("arrow-up-right", class_name="h-3.5 w-3.5 text-lime-200"),
            href="/referentiel",
            class_name="flex items-center gap-1.5 rounded-full border border-lime-300/30 bg-lime-300/10 px-3 py-1.5 text-[11px] font-semibold hover:bg-lime-300/20 transition-colors w-fit mt-4",
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.02] py-14 w-full mt-4",
    )


def phenology_panel() -> rx.Component:
    return rx.el.section(
        _header(),
        rx.cond(
            PhenologyState.is_loading,
            _skeleton(),
            rx.cond(
                PhenologyState.has_profile,
                rx.el.div(
                    _profile_block(),
                    _summary_grid(),
                    _status_line(),
                    rx.el.div(phenology_rail(), class_name="w-full mt-4"),
                    _recommendations(),
                    _guide_block(),
                    phenology_form(),
                    _journal(),
                    class_name="flex flex-col w-full",
                ),
                _empty(),
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
