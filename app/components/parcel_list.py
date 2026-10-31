import reflex as rx

from app.components.design import empty_state, skeleton_rows
from app.states.parcels_state import ParcelRow, ParcelsState


def _parcel_card(parcel: ParcelRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": parcel["color"]},
        ),
        rx.el.div(
            rx.el.span(
                parcel["code"],
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.cond(
                parcel["is_organic"],
                rx.el.span(
                    "BIO",
                    class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            rx.el.span(
                parcel["status_label"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        rx.el.p(
            parcel["name"],
            class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] text-left mt-2 truncate w-full",
        ),
        rx.el.div(
            rx.icon("sprout", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)]"),
            rx.el.span(
                parcel["active_crop"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1.5 min-w-0",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-sage-rgb)/0.70)]"),
            rx.el.span(
                parcel["locality"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1 min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                style={"width": parcel["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))] mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{parcel['area_ha']:.1f} ha",
                class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)]",
            ),
            rx.el.span(
                f"{parcel['crop_count']} culture(s)",
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                parcel["progress_pct"],
                class_name="text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=ParcelsState.select_parcel(parcel["id"]),
        key=key,
        class_name=rx.cond(
            ParcelsState.selected_parcel_id == parcel["id"],
            "w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] border-l-2 border-l-[rgb(var(--ap-accent-rgb))] bg-[rgb(var(--ap-accent-rgb))]/[0.07] pl-3 pr-2 pt-4 text-left transition-colors",
            "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 text-left hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-all",
        ),
    )


def parcel_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Assolement",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Parcelles",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                ParcelsState.parcel_count,
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-xs font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            ParcelsState.is_loading,
            rx.el.div(skeleton_rows(3), class_name="flex flex-col gap-3 mt-5"),
            rx.cond(
                ParcelsState.parcels.length() > 0,
                rx.el.div(
                    rx.foreach(
                        ParcelsState.parcels,
                        lambda p: _parcel_card(p, key=p["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 mt-5 max-h-[46rem] overflow-y-auto pr-1",
                ),
                empty_state(
                    "search-x",
                    "Aucune parcelle ne correspond aux filtres.",
                    class_name="mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[24rem] shrink-0 border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
    )
