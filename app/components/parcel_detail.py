import reflex as rx

from app.components.guide_help import guide_error, help_icon_button
from app.states.parcels_state import (
    CropRow,
    ParcelsState,
    RailStep,
    StageLogRow,
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
        class_name="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 min-w-0",
    )


def _rail_step(step: RailStep) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name=rx.match(
                step["state"],
                ("done", "h-2 w-2 rounded-full bg-emerald-400"),
                (
                    "current",
                    "h-2.5 w-2.5 rounded-full bg-lime-300 ring-2 ring-lime-300/40",
                ),
                "h-2 w-2 rounded-full bg-white/15",
            ),
        ),
        rx.el.span(
            step["label"],
            class_name=rx.match(
                step["state"],
                (
                    "done",
                    "text-[10px] font-medium text-emerald-200/70 whitespace-nowrap",
                ),
                (
                    "current",
                    "text-[10px] font-bold text-lime-200 whitespace-nowrap",
                ),
                "text-[10px] font-medium text-emerald-100/30 whitespace-nowrap",
            ),
        ),
        class_name="flex flex-col items-center gap-1.5 shrink-0",
    )


def _health_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
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
            "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit",
        ),
    )


def _crop_card(crop: CropRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                class_name="h-8 w-1 rounded-full shrink-0",
                style={"backgroundColor": crop["color"]},
            ),
            rx.el.div(
                rx.el.p(
                    crop["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{crop['species']} · campagne {crop['season']}",
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _health_badge(crop["health_tone"], crop["health_label"]),
            rx.el.button(
                rx.icon("pencil", class_name="h-3.5 w-3.5"),
                rx.el.span("Modifier", class_name="text-[11px]"),
                on_click=ParcelsState.open_crop_edit(crop["id"]),
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit shrink-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                crop["stage_label"],
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            rx.el.span(
                crop["status_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{crop['area_ha']:.1f} ha",
                class_name="text-[10px] font-semibold text-emerald-100/60",
            ),
            rx.el.span(
                f"Objectif {crop['expected_yield']} t/ha",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                rx.cond(
                    crop["days_left"] > 0,
                    f"Récolte J-{crop['days_left']}",
                    "Échéance atteinte",
                ),
                class_name="text-[10px] font-bold text-amber-200 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute left-0 right-0 top-[3px] h-px bg-white/10",
            ),
            rx.el.div(
                rx.foreach(crop["rail"], lambda step: _rail_step(step)),
                class_name="relative flex items-start justify-between gap-1 w-full overflow-x-auto",
            ),
            class_name="relative mt-4",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                style={"width": crop["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-plus",
                    class_name="h-3.5 w-3.5 text-emerald-300/80",
                ),
                rx.el.span(
                    f"Semis {crop['sowing_label']}",
                    class_name="text-[11px] font-medium text-emerald-100/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.div(
                rx.icon("wheat", class_name="h-3.5 w-3.5 text-amber-300/80"),
                rx.el.span(
                    f"Récolte {crop['harvest_label']}",
                    class_name="text-[11px] font-medium text-emerald-100/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                crop["progress_pct"],
                class_name="text-[11px] font-bold text-lime-200 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 border-t border-white/5 pt-3 mt-3",
        ),
        rx.el.p(
            crop["notes"],
            class_name="text-[11px] font-medium text-emerald-100/45 mt-2 leading-relaxed",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def _timeline_entry(log: StageLogRow, key: str = "") -> rx.Component:
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
                    log["stage_label"],
                    class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
                ),
                rx.el.span(
                    log["crop_name"],
                    class_name="text-xs font-semibold text-emerald-50 truncate",
                ),
                rx.el.span(
                    log["observed_label"],
                    class_name="text-[10px] font-medium text-emerald-100/45 ml-auto shrink-0",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.p(
                log["comment"],
                class_name="text-[11px] font-medium text-emerald-100/55 mt-1 leading-relaxed",
            ),
            rx.el.div(
                rx.icon("user-round", class_name="h-3 w-3 text-emerald-300/70"),
                rx.el.span(
                    log["observer"],
                    class_name="text-[10px] font-medium text-emerald-100/45",
                ),
                class_name="flex items-center gap-1.5 mt-1.5",
            ),
            class_name="min-w-0 flex-1 pb-5",
        ),
        key=key,
        class_name="flex gap-3 w-full",
    )


def _stage_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.select(
                    rx.el.option("Culture observée", value="", disabled=True),
                    rx.foreach(
                        ParcelsState.crop_name_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="crop_id",
                    default_value="",
                    key=f"log-crop-{ParcelsState.form_key}",
                    class_name="w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-3 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 outline-hidden",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.div(
                rx.el.select(
                    rx.foreach(
                        ParcelsState.stage_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="stage",
                    default_value="CROISSANCE",
                    key=f"log-stage-{ParcelsState.form_key}",
                    class_name="w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-3 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 outline-hidden",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.input(
                type="date",
                name="observed_on",
                key=f"log-date-{ParcelsState.form_key}",
                class_name="w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 focus:border-lime-300/50 outline-hidden",
            ),
            rx.el.input(
                name="observer",
                placeholder="Observateur",
                key=f"log-observer-{ParcelsState.form_key}",
                class_name="w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3",
        ),
        rx.el.input(
            name="comment",
            placeholder="Commentaire agronomique (facultatif)",
            key=f"log-comment-{ParcelsState.form_key}",
            class_name="w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden mt-3",
        ),
        guide_error(ParcelsState.stage_error, "parcelles", "dates"),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span("Consigner le stade", class_name="text-[#04140d]"),
            type="submit",
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-3",
        ),
        on_submit=ParcelsState.submit_stage_log,
        reset_on_submit=True,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-4",
    )


def _detail_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    ParcelsState.parcel_detail["code"],
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.span(
                    ParcelsState.parcel_detail["organic_label"],
                    class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.h2(
                ParcelsState.parcel_detail["name"],
                class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
            ),
            rx.el.p(
                f"{ParcelsState.parcel_detail['locality']} · {ParcelsState.parcel_detail['status_label']}",
                class_name="text-xs font-medium text-emerald-100/55 mt-1",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            help_icon_button("parcelles"),
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                rx.el.span("Modifier la parcelle"),
                on_click=ParcelsState.open_parcel_edit,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/75 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("sprout", class_name="h-4 w-4 text-[#04140d]"),
                rx.el.span("Nouvelle culture", class_name="text-[#04140d]"),
                on_click=ParcelsState.open_crop_create,
                class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 pb-5 border-b border-white/10",
    )


def parcel_detail() -> rx.Component:
    return rx.el.section(
        rx.cond(
            ParcelsState.has_selection,
            rx.el.div(
                _detail_header(),
                rx.el.div(
                    _fact(
                        "Surface",
                        f"{ParcelsState.parcel_detail['area_ha']} ha",
                        "ruler",
                    ),
                    _fact(
                        "Type de sol",
                        ParcelsState.parcel_detail["soil_label"],
                        "layers",
                    ),
                    _fact(
                        "Irrigation",
                        ParcelsState.parcel_detail["irrigation_label"],
                        "droplets",
                    ),
                    _fact(
                        "pH / MO",
                        f"{ParcelsState.parcel_detail['ph']} · {ParcelsState.parcel_detail['organic_matter']} %",
                        "flask-conical",
                    ),
                    _fact(
                        "Pente",
                        f"{ParcelsState.parcel_detail['slope']} %",
                        "triangle",
                    ),
                    _fact(
                        "Coordonnées",
                        ParcelsState.parcel_detail["coordinates"],
                        "compass",
                    ),
                    _fact(
                        "Cultures actives",
                        f"{ParcelsState.parcel_detail['active_crops']} / {ParcelsState.parcel_detail['crop_count']}",
                        "sprout",
                    ),
                    _fact(
                        "Avancement moyen",
                        f"{ParcelsState.parcel_detail['avg_progress']} %",
                        "gauge",
                    ),
                    class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5",
                ),
                rx.el.p(
                    ParcelsState.parcel_detail["notes"],
                    class_name="text-[11px] font-medium text-emerald-100/50 mt-3 leading-relaxed",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Fiches culturales",
                            class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                        ),
                        rx.el.div(
                            rx.el.select(
                                rx.el.option(
                                    "Tous les statuts de culture", value="TOUS"
                                ),
                                rx.foreach(
                                    ParcelsState.crop_status_options,
                                    lambda opt: rx.el.option(
                                        opt["label"], value=opt["value"]
                                    ),
                                ),
                                name="crop_status_filter",
                                default_value=ParcelsState.crop_status_filter,
                                key=f"cropstatus-{ParcelsState.form_key}",
                                on_change=ParcelsState.set_crop_status_filter,
                                class_name="w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2 pl-3 pr-9 text-xs font-medium text-emerald-50 focus:border-lime-300/50 outline-hidden",
                            ),
                            rx.icon(
                                "chevron-down",
                                class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-emerald-100/40 pointer-events-none",
                            ),
                            class_name="relative w-full sm:w-64 ml-auto",
                        ),
                        class_name="flex flex-col sm:flex-row sm:items-center gap-3",
                    ),
                    rx.cond(
                        ParcelsState.parcel_crops.length() > 0,
                        rx.el.div(
                            rx.foreach(
                                ParcelsState.parcel_crops,
                                lambda c: _crop_card(
                                    c, key=c["id"].to_string()
                                ),
                            ),
                            class_name="flex flex-col gap-3 mt-4",
                        ),
                        rx.el.div(
                            rx.icon(
                                "sprout",
                                class_name="h-6 w-6 text-lime-300",
                            ),
                            rx.el.p(
                                "Aucune culture pour ce filtre. Créez une fiche culturale pour démarrer le suivi.",
                                class_name="text-sm font-medium text-emerald-100/55 mt-2 text-center max-w-sm",
                            ),
                            class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-10 mt-4",
                        ),
                    ),
                    class_name="mt-8",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Timeline végétale",
                            class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                        ),
                        rx.el.h3(
                            "Suivi des stades culturaux",
                            class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
                        ),
                        class_name="min-w-0",
                    ),
                    _stage_form(),
                    rx.cond(
                        ParcelsState.stage_logs.length() > 0,
                        rx.el.div(
                            rx.el.div(
                                class_name="absolute left-[5px] top-2 bottom-2 w-px bg-gradient-to-b from-lime-300/50 via-emerald-400/25 to-transparent",
                            ),
                            rx.foreach(
                                ParcelsState.stage_logs,
                                lambda log: _timeline_entry(
                                    log, key=log["id"].to_string()
                                ),
                            ),
                            class_name="relative flex flex-col mt-5 pl-0",
                        ),
                        rx.el.p(
                            "Aucun stade consigné pour cette parcelle.",
                            class_name="text-sm font-medium text-emerald-100/50 mt-5",
                        ),
                    ),
                    class_name="mt-8 border-t border-white/10 pt-6",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("map", class_name="h-7 w-7 text-lime-300"),
                rx.el.p(
                    "Sélectionnez une parcelle dans la liste ou créez votre premier îlot.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 text-center max-w-sm",
                ),
                class_name="flex flex-col items-center justify-center py-24",
            ),
        ),
        class_name="flex-1 min-w-0 w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
