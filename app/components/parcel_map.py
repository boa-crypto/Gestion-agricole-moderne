import reflex as rx

from app.states.dashboard_state import DashboardState, ParcelTile


def _tile(parcel: ParcelTile) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    parcel["code"],
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/60",
                ),
                rx.cond(
                    parcel["is_organic"],
                    rx.el.span(
                        "BIO",
                        class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center justify-between gap-2 w-full",
            ),
            rx.el.p(
                parcel["name"],
                class_name="text-sm font-semibold text-emerald-50 text-left leading-tight mt-1",
            ),
            rx.el.p(
                parcel["crop_name"],
                class_name="text-[11px] font-medium text-emerald-100/60 text-left",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-full bg-lime-300",
                    style={"width": parcel["progress_pct"]},
                ),
                class_name="h-1 w-full rounded-full bg-white/10 mt-auto",
            ),
            rx.el.div(
                rx.el.span(
                    f"{parcel['area_ha']:.1f} ha",
                    class_name="text-[10px] font-medium text-emerald-100/70",
                ),
                rx.el.span(
                    parcel["status_label"],
                    class_name="text-[10px] font-medium text-emerald-100/50",
                ),
                class_name="flex items-center justify-between gap-2 w-full mt-1",
            ),
            class_name="flex flex-col h-full w-full",
        ),
        on_click=DashboardState.select_parcel(parcel["id"]),
        style={
            "left": parcel["left"],
            "top": parcel["top"],
            "width": parcel["width"],
            "height": parcel["height"],
            "backgroundColor": parcel["fill"],
            "borderColor": parcel["stroke"],
        },
        class_name=rx.cond(
            DashboardState.selected_parcel_id == parcel["id"],
            "absolute overflow-hidden rounded-2xl border-2 p-3 text-left backdrop-blur-sm ring-2 ring-lime-300/60 transition-all duration-200",
            "absolute overflow-hidden rounded-2xl border p-3 text-left backdrop-blur-sm hover:ring-2 hover:ring-lime-300/30 transition-all duration-200",
        ),
    )


def _detail_row(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/80"),
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
        ),
        rx.el.span(
            value, class_name="text-xs font-semibold text-emerald-50 ml-auto"
        ),
        class_name="flex items-center gap-2 border-b border-white/5 py-2 last:border-b-0",
    )


def _selected_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Parcelle sélectionnée",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.h3(
                DashboardState.selected_parcel["name"],
                class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
            ),
            rx.el.p(
                DashboardState.selected_parcel["crop_name"],
                class_name="text-xs font-medium text-emerald-100/60",
            ),
            class_name="pb-3 border-b border-white/10",
        ),
        rx.el.div(
            _detail_row(
                "Surface",
                f"{DashboardState.selected_parcel['area_ha']:.1f} ha",
                "ruler",
            ),
            _detail_row(
                "Statut", DashboardState.selected_parcel["status_label"], "flag"
            ),
            _detail_row(
                "Sol", DashboardState.selected_parcel["soil_label"], "layers"
            ),
            _detail_row(
                "Irrigation",
                DashboardState.selected_parcel["irrigation_label"],
                "droplets",
            ),
            _detail_row(
                "État sanitaire",
                DashboardState.selected_parcel["health_label"],
                "activity",
            ),
            _detail_row(
                "Avancement",
                DashboardState.selected_parcel["progress_pct"],
                "gauge",
            ),
            class_name="mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl",
    )


def _legend_item(label: str, dot_class: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=dot_class),
        rx.el.span(
            label, class_name="text-[11px] font-medium text-emerald-100/60"
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def parcel_map() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "Cartographie",
                        class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                    ),
                    rx.el.h2(
                        "Assolement de l'exploitation",
                        class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                    ),
                    class_name="min-w-0",
                ),
                rx.el.div(
                    _legend_item(
                        "Parcelle active",
                        "h-2 w-2 rounded-full bg-lime-300",
                    ),
                    _legend_item(
                        "Conduite bio",
                        "h-2 w-2 rounded-full bg-emerald-400",
                    ),
                    _legend_item(
                        "Chantier à venir",
                        "h-2 w-2 rounded-full bg-amber-300",
                    ),
                    class_name="flex flex-wrap items-center gap-4",
                ),
                class_name="flex flex-col md:flex-row md:items-end justify-between gap-4",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="absolute inset-0 bg-[linear-gradient(to_right,rgba(163,230,53,0.07)_1px,transparent_1px),linear-gradient(to_bottom,rgba(163,230,53,0.07)_1px,transparent_1px)] bg-[size:40px_40px]",
                ),
                rx.el.div(
                    class_name="absolute -top-24 -left-16 h-72 w-72 rounded-full bg-emerald-400/10 blur-3xl",
                ),
                rx.el.div(
                    class_name="absolute -bottom-24 right-0 h-72 w-72 rounded-full bg-amber-300/10 blur-3xl",
                ),
                rx.foreach(DashboardState.parcels, lambda p: _tile(p)),
                rx.el.div(
                    rx.icon("compass", class_name="h-3.5 w-3.5 text-lime-300"),
                    rx.el.span(
                        "Nord",
                        class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/60",
                    ),
                    class_name="absolute right-4 top-4 flex items-center gap-1.5 rounded-full border border-white/10 bg-[#04140d]/70 px-2.5 py-1 backdrop-blur-xl",
                ),
                class_name="relative mt-6 w-full min-h-[26rem] h-[34rem] rounded-3xl border border-white/10 bg-[#03110b]/70 overflow-hidden",
            ),
            class_name="flex-1 min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
        ),
        rx.el.div(
            _selected_panel(),
            rx.el.div(
                rx.el.span(
                    "Répartition des espèces",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.foreach(
                    DashboardState.species_mix,
                    lambda s: rx.el.div(
                        rx.el.div(
                            rx.el.span(
                                s["species"],
                                class_name="text-xs font-semibold text-emerald-50 truncate",
                            ),
                            rx.el.span(
                                f"{s['area_ha']:.1f} ha",
                                class_name="text-[11px] font-medium text-emerald-100/50 ml-auto shrink-0",
                            ),
                            class_name="flex items-center gap-2 w-full",
                        ),
                        rx.el.div(
                            rx.el.div(
                                class_name="h-full rounded-full",
                                style={
                                    "width": s["share"],
                                    "backgroundColor": s["color"],
                                },
                            ),
                            class_name="h-1.5 w-full rounded-full bg-white/10 mt-1.5",
                        ),
                        class_name="w-full mt-3",
                    ),
                ),
                class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl",
            ),
            class_name="flex flex-col gap-4 w-full xl:w-80 shrink-0",
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )
