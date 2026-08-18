import reflex as rx
import reflex_enterprise as rxe

from app.states.cartography_state import CartographyState, Option, ParcelShape

_SELECT = "w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"


def _select(
    name: str,
    icon: str,
    value: rx.Var | str,
    on_change: rx.event.EventType,
    first_option: rx.Component,
    options: rx.Var[list[Option]],
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
            key=f"{name}-{CartographyState.form_key}",
            on_change=on_change,
            class_name=_SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _parcel_card(shape: ParcelShape, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-full",
            style={"backgroundColor": shape["color"]},
        ),
        rx.el.div(
            rx.el.span(
                shape["code"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/50",
            ),
            rx.cond(
                shape["is_organic"],
                rx.el.span(
                    "BIO",
                    class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                shape["has_geometry"],
                rx.el.span(
                    "TRACÉ",
                    class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit ml-auto",
                ),
                rx.el.span(
                    "À TRACER",
                    class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-1.5 py-0.5 text-[9px] font-bold text-amber-200 w-fit ml-auto",
                ),
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        rx.el.p(
            shape["name"],
            class_name="text-sm font-semibold text-emerald-50 text-left mt-2 truncate w-full",
        ),
        rx.el.div(
            rx.icon("sprout", class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                shape["crop_name"],
                class_name="text-[11px] font-medium text-emerald-100/60 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1.5 min-w-0",
        ),
        rx.el.div(
            rx.icon("sprout", class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                shape["stage_label"],
                class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-2 py-0.5 text-[10px] font-semibold text-lime-200 w-fit truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1.5 min-w-0",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3.5 w-3.5 text-emerald-300/70"),
            rx.el.span(
                shape["locality"],
                class_name="text-[11px] font-medium text-emerald-100/45 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1 min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                f"{shape['area_ha']:.1f} ha",
                class_name="text-[11px] font-semibold text-emerald-100/70",
            ),
            rx.el.span(
                f"{shape['vertex_count']} sommets",
                class_name="text-[11px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                shape["status_label"],
                class_name="text-[10px] font-semibold text-lime-200 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        on_click=[
            CartographyState.select_parcel(shape["id"]),
            rxe.map.api("cartographie-map").fly_to(
                shape["center"], shape["zoom"]
            ),
        ],
        key=key,
        class_name=rx.cond(
            CartographyState.selected_parcel_id == shape["id"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/40 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def map_sidebar() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Îlots",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Parcelles",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                CartographyState.parcel_count,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Rechercher un îlot, un code, une culture…",
                    default_value=CartographyState.search,
                    on_change=CartographyState.set_search.debounce(400),
                    class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
                ),
                class_name="relative w-full",
            ),
            _select(
                "carto_status_filter",
                "flag",
                CartographyState.status_filter,
                CartographyState.set_status_filter,
                rx.el.option("Tous les statuts", value="TOUS"),
                CartographyState.status_options,
            ),
            _select(
                "carto_stage_filter",
                "sprout",
                CartographyState.stage_filter,
                CartographyState.set_stage_filter,
                rx.el.option("Tous les stades", value="TOUS"),
                CartographyState.stage_options,
            ),
            _select(
                "carto_geometry_filter",
                "pen-tool",
                CartographyState.geometry_filter,
                CartographyState.set_geometry_filter,
                rx.el.option("Tous les contours", value="TOUS"),
                CartographyState.geometry_options,
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=CartographyState.reset_filters,
                class_name="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-full",
            ),
            class_name="flex flex-col gap-3 mt-5",
        ),
        rx.cond(
            CartographyState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                class_name="flex flex-col gap-3 mt-5",
            ),
            rx.cond(
                CartographyState.shapes.length() > 0,
                rx.el.div(
                    rx.foreach(
                        CartographyState.shapes,
                        lambda s: _parcel_card(s, key=s["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 mt-5 max-h-[38rem] overflow-y-auto pr-1",
                ),
                rx.el.div(
                    rx.icon("search-x", class_name="h-6 w-6 text-amber-300"),
                    rx.el.p(
                        "Aucun îlot ne correspond aux filtres.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[23rem] shrink-0 rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )
