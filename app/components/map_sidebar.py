import reflex as rx
import reflex_enterprise as rxe

from app.states.cartography_state import CartographyState, Option, ParcelShape

_SELECT = "w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors"


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
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
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
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _parcel_card(shape: ParcelShape, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": shape["color"]},
        ),
        rx.el.div(
            rx.el.span(
                shape["code"],
                class_name="ap-eyebrow text-[#c9c5b4]/50",
            ),
            rx.cond(
                shape["is_organic"],
                rx.el.span(
                    "BIO",
                    class_name="rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#e4ff9b] w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                shape["has_geometry"],
                rx.el.span(
                    "TRACÉ",
                    class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#e4ff9b] w-fit ml-auto",
                ),
                rx.el.span(
                    "À TRACER",
                    class_name="rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#ffb894] w-fit ml-auto",
                ),
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        rx.el.p(
            shape["name"],
            class_name="text-sm font-semibold text-[#f2efe4] text-left mt-2 truncate w-full",
        ),
        rx.el.div(
            rx.icon("sprout", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                shape["crop_name"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/60 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1.5 min-w-0",
        ),
        rx.el.div(
            rx.icon("sprout", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                shape["stage_label"],
                class_name="rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-semibold text-[#e4ff9b] w-fit truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1.5 min-w-0",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3.5 w-3.5 text-[#a9c98b]/70"),
            rx.el.span(
                shape["locality"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/45 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-1 min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                f"{shape['area_ha']:.1f} ha",
                class_name="text-[11px] font-semibold text-[#c9c5b4]/70",
            ),
            rx.el.span(
                f"{shape['vertex_count']} sommets",
                class_name="text-[11px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                shape["status_label"],
                class_name="text-[10px] font-semibold text-[#e4ff9b] ml-auto",
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
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-4 text-left ring-2 ring-[#d8fa5e]/40 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 transition-all",
        ),
    )


def map_sidebar() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Îlots",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Parcelles",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                CartographyState.parcel_count,
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-xs font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Rechercher un îlot, un code, une culture…",
                    default_value=CartographyState.search,
                    on_change=CartographyState.set_search.debounce(400),
                    class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-3 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors",
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
                class_name="flex items-center justify-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-full",
            ),
            class_name="flex flex-col gap-3 mt-5",
        ),
        rx.cond(
            CartographyState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
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
                    rx.icon("search-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                    rx.el.p(
                        "Aucun îlot ne correspond aux filtres.",
                        class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[23rem] shrink-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )
