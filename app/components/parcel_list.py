import reflex as rx

from app.states.parcels_state import ParcelRow, ParcelsState


def _parcel_card(parcel: ParcelRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-full",
            style={"backgroundColor": parcel["color"]},
        ),
        rx.el.div(
            rx.el.span(
                parcel["code"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/50",
            ),
            rx.cond(
                parcel["is_organic"],
                rx.el.span(
                    "BIO",
                    class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                ),
                rx.fragment(),
            ),
            rx.el.span(
                parcel["status_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        rx.el.p(
            parcel["name"],
            class_name="text-sm font-semibold text-emerald-50 text-left mt-2 truncate w-full",
        ),
        rx.el.div(
            rx.icon("sprout", class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                parcel["active_crop"],
                class_name="text-[11px] font-medium text-emerald-100/60 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1.5 min-w-0",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3.5 w-3.5 text-emerald-300/70"),
            rx.el.span(
                parcel["locality"],
                class_name="text-[11px] font-medium text-emerald-100/45 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1 min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                style={"width": parcel["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{parcel['area_ha']:.1f} ha",
                class_name="text-[11px] font-semibold text-emerald-100/70",
            ),
            rx.el.span(
                f"{parcel['crop_count']} culture(s)",
                class_name="text-[11px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                parcel["progress_pct"],
                class_name="text-[11px] font-bold text-lime-200 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=ParcelsState.select_parcel(parcel["id"]),
        key=key,
        class_name=rx.cond(
            ParcelsState.selected_parcel_id == parcel["id"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/40 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def parcel_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Assolement",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Parcelles",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                ParcelsState.parcel_count,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            ParcelsState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-24 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-24 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-24 rounded-2xl bg-white/[0.05]"
                ),
                class_name="flex flex-col gap-3 mt-5",
            ),
            rx.cond(
                ParcelsState.parcels.length() > 0,
                rx.el.div(
                    rx.foreach(
                        ParcelsState.parcels,
                        lambda p: _parcel_card(p, key=p["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 mt-5 max-h-[46rem] overflow-y-auto pr-1",
                ),
                rx.el.div(
                    rx.icon("search-x", class_name="h-6 w-6 text-amber-300"),
                    rx.el.p(
                        "Aucune parcelle ne correspond aux filtres.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[24rem] shrink-0 rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )
