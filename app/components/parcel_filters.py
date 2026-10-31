import reflex as rx

from app.states.parcels_state import Option, ParcelsState


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-2xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-3",
    )


def _select(
    name: str,
    icon: str,
    default_value: rx.Var | str,
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
            default_value=default_value,
            key=f"{name}-{ParcelsState.form_key}",
            on_change=on_change,
            class_name="w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-56",
    )


def parcel_filters() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            _stat("Parcelles listées", ParcelsState.parcel_count, "îlots"),
            _stat("Surface filtrée", f"{ParcelsState.filtered_area:.1f}", "ha"),
            _stat(
                "Dont conduite bio", f"{ParcelsState.organic_area:.1f}", "ha"
            ),
            _stat("Cultures affichées", ParcelsState.crops_shown, "fiches"),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Rechercher une parcelle, un code, une localité ou une culture…",
                    default_value=ParcelsState.search,
                    on_change=ParcelsState.set_search.debounce(400),
                    class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-3 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors",
                ),
                class_name="relative flex-1 min-w-0",
            ),
            _select(
                "status_filter",
                "flag",
                ParcelsState.status_filter,
                ParcelsState.set_status_filter,
                rx.el.option("Tous les statuts", value="TOUS"),
                ParcelsState.status_options,
            ),
            rx.el.div(
                rx.icon(
                    "sprout",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
                ),
                rx.el.select(
                    rx.el.option("Toutes les cultures", value="TOUTES"),
                    rx.foreach(
                        ParcelsState.species_options,
                        lambda species: rx.el.option(species, value=species),
                    ),
                    name="species_filter",
                    default_value=ParcelsState.species_filter,
                    key=f"species-{ParcelsState.form_key}",
                    on_change=ParcelsState.set_species_filter,
                    class_name="w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full sm:w-56",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=ParcelsState.reset_filters,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-4 w-4 text-[#0A0A08]"),
                rx.el.span("Nouvelle parcelle", class_name="text-[#0A0A08]"),
                on_click=ParcelsState.open_parcel_create,
                class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )
