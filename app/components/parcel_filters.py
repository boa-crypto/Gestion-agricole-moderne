import reflex as rx

from app.states.parcels_state import Option, ParcelsState


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3",
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
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
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
            class_name="w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
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
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Rechercher une parcelle, un code, une localité ou une culture…",
                    default_value=ParcelsState.search,
                    on_change=ParcelsState.set_search.debounce(400),
                    class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
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
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
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
                    class_name="w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full sm:w-56",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=ParcelsState.reset_filters,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-4 w-4 text-[#04140d]"),
                rx.el.span("Nouvelle parcelle", class_name="text-[#04140d]"),
                on_click=ParcelsState.open_parcel_create,
                class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )
