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
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-sm font-semibold text-[#f2efe4] mt-1.5 truncate",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 min-w-0",
    )


def _rail_step(step: RailStep) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name=rx.match(
                step["state"],
                ("done", "h-2 w-2 rounded-none bg-[#8fb37a]"),
                (
                    "current",
                    "h-2.5 w-2.5 rounded-none bg-[#d8fa5e] ring-2 ring-[#d8fa5e]/40",
                ),
                "h-2 w-2 rounded-none bg-[#262b1e]",
            ),
        ),
        rx.el.span(
            step["label"],
            class_name=rx.match(
                step["state"],
                (
                    "done",
                    "text-[10px] font-medium text-[#b3af9f]/70 whitespace-nowrap",
                ),
                (
                    "current",
                    "text-[10px] font-bold text-[#e4ff9b] whitespace-nowrap",
                ),
                "text-[10px] font-medium text-[#c9c5b4]/30 whitespace-nowrap",
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
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
        ),
    )


def _crop_card(crop: CropRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                class_name="h-8 w-1 rounded-none shrink-0",
                style={"backgroundColor": crop["color"]},
            ),
            rx.el.div(
                rx.el.p(
                    crop["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{crop['species']} · campagne {crop['season']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _health_badge(crop["health_tone"], crop["health_label"]),
            rx.el.button(
                rx.icon("pencil", class_name="h-3.5 w-3.5"),
                rx.el.span("Modifier", class_name="text-[11px]"),
                on_click=ParcelsState.open_crop_edit(crop["id"]),
                class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit shrink-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                crop["stage_label"],
                class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            rx.el.span(
                crop["status_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{crop['area_ha']:.1f} ha",
                class_name="text-[10px] font-semibold text-[#c9c5b4]/60",
            ),
            rx.el.span(
                f"Objectif {crop['expected_yield']} t/ha",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                rx.cond(
                    crop["days_left"] > 0,
                    f"Récolte J-{crop['days_left']}",
                    "Échéance atteinte",
                ),
                class_name="text-[10px] font-bold text-[#ffb894] ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute left-0 right-0 top-[3px] h-px bg-[#20241a]",
            ),
            rx.el.div(
                rx.foreach(crop["rail"], lambda step: _rail_step(step)),
                class_name="relative flex items-start justify-between gap-1 w-full overflow-x-auto",
            ),
            class_name="relative mt-4",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                style={"width": crop["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-plus",
                    class_name="h-3.5 w-3.5 text-[#a9c98b]/80",
                ),
                rx.el.span(
                    f"Semis {crop['sowing_label']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.div(
                rx.icon("wheat", class_name="h-3.5 w-3.5 text-[#ff8a5b]/80"),
                rx.el.span(
                    f"Récolte {crop['harvest_label']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                crop["progress_pct"],
                class_name="text-[11px] font-bold text-[#e4ff9b] ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 border-t border-[#f2efe4]/8 pt-3 mt-3",
        ),
        rx.el.p(
            crop["notes"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/45 mt-2 leading-relaxed",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def _timeline_entry(log: StageLogRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                class_name="h-2.5 w-2.5 rounded-none bg-[#d8fa5e] ring-4 ring-[#d8fa5e]/15"
            ),
            class_name="relative flex flex-col items-center pt-1.5",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    log["stage_label"],
                    class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
                ),
                rx.el.span(
                    log["crop_name"],
                    class_name="text-xs font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.span(
                    log["observed_label"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 ml-auto shrink-0",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.p(
                log["comment"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1 leading-relaxed",
            ),
            rx.el.div(
                rx.icon("user-round", class_name="h-3 w-3 text-[#a9c98b]/70"),
                rx.el.span(
                    log["observer"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45",
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
                    class_name="w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-3 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 outline-hidden",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
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
                    class_name="w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-3 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 outline-hidden",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.input(
                type="date",
                name="observed_on",
                key=f"log-date-{ParcelsState.form_key}",
                class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] px-3 py-2.5 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 outline-hidden",
            ),
            rx.el.input(
                name="observer",
                placeholder="Observateur",
                key=f"log-observer-{ParcelsState.form_key}",
                class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] px-3 py-2.5 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 outline-hidden",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3",
        ),
        rx.el.input(
            name="comment",
            placeholder="Commentaire agronomique (facultatif)",
            key=f"log-comment-{ParcelsState.form_key}",
            class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] px-3 py-2.5 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 outline-hidden mt-3",
        ),
        guide_error(ParcelsState.stage_error, "parcelles", "dates"),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4 text-[#0A0A08]"),
            rx.el.span("Consigner le stade", class_name="text-[#0A0A08]"),
            type="submit",
            class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit mt-3",
        ),
        on_submit=ParcelsState.submit_stage_log,
        reset_on_submit=True,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 mt-4",
    )


def _detail_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    ParcelsState.parcel_detail["code"],
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.span(
                    ParcelsState.parcel_detail["organic_label"],
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.h2(
                ParcelsState.parcel_detail["name"],
                class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
            ),
            rx.el.p(
                f"{ParcelsState.parcel_detail['locality']} · {ParcelsState.parcel_detail['status_label']}",
                class_name="text-xs font-medium text-[#c9c5b4]/55 mt-1",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            help_icon_button("parcelles"),
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                rx.el.span("Modifier la parcelle"),
                on_click=ParcelsState.open_parcel_edit,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/75 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("sprout", class_name="h-4 w-4 text-[#0A0A08]"),
                rx.el.span("Nouvelle culture", class_name="text-[#0A0A08]"),
                on_click=ParcelsState.open_crop_create,
                class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 pb-5 border-b border-[#f2efe4]/12",
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
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-3 leading-relaxed",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Fiches culturales",
                            class_name="ap-eyebrow text-[#d8fa5e]/80",
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
                                class_name="w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2 pl-3 pr-9 text-xs font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 outline-hidden",
                            ),
                            rx.icon(
                                "chevron-down",
                                class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#c9c5b4]/40 pointer-events-none",
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
                                class_name="h-6 w-6 text-[#d8fa5e]",
                            ),
                            rx.el.p(
                                "Aucune culture pour ce filtre. Créez une fiche culturale pour démarrer le suivi.",
                                class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 text-center max-w-sm",
                            ),
                            class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-10 mt-4",
                        ),
                    ),
                    class_name="mt-8",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Timeline végétale",
                            class_name="ap-eyebrow text-[#d8fa5e]/80",
                        ),
                        rx.el.h3(
                            "Suivi des stades culturaux",
                            class_name="ap-serif text-2xl text-[#f2efe4] mt-1",
                        ),
                        class_name="min-w-0",
                    ),
                    _stage_form(),
                    rx.cond(
                        ParcelsState.stage_logs.length() > 0,
                        rx.el.div(
                            rx.el.div(
                                class_name="absolute left-[5px] top-2 bottom-2 w-px bg-gradient-to-b from-[#d8fa5e]/50 via-[#8fb37a]/25 to-transparent",
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
                            class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
                        ),
                    ),
                    class_name="mt-8 border-t border-[#f2efe4]/12 pt-6",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("map", class_name="h-7 w-7 text-[#d8fa5e]"),
                rx.el.p(
                    "Sélectionnez une parcelle dans la liste ou créez votre premier îlot.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 text-center max-w-sm",
                ),
                class_name="flex flex-col items-center justify-center py-24",
            ),
        ),
        class_name="flex-1 min-w-0 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
