import reflex as rx

from app.components.design import action_button, stat
from app.states.parcels_state import Option, ParcelsState


def _stat(
    label: str,
    value: rx.Var | str,
    unit: str,
    index: str,
) -> rx.Component:
    return stat(label, value, unit, index=index)


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
            class_name="w-full cursor-pointer appearance-none border border-[#F2EFE4]/14 bg-[#0F110A] py-2.5 pl-9 pr-9 text-sm text-[#F2EFE4] outline-hidden transition-colors focus:border-[#D8FA5E]",
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
            _stat("Parcelles listées", ParcelsState.parcel_count, "îlots", "01"),
            _stat(
                "Surface filtrée",
                f"{ParcelsState.filtered_area:.1f}",
                "ha",
                "02",
            ),
            _stat(
                "Dont conduite bio",
                f"{ParcelsState.organic_area:.1f}",
                "ha",
                "03",
            ),
            _stat(
                "Cultures affichées",
                ParcelsState.crops_shown,
                "fiches",
                "04",
            ),
            class_name="grid grid-cols-2 gap-x-6 gap-y-8 lg:grid-cols-4 lg:gap-x-8 w-full",
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
                    class_name=(
                        "w-full border border-[#F2EFE4]/14 bg-[#0F110A] py-2.5 pl-9 "
                        "pr-3 text-sm text-[#F2EFE4] outline-hidden transition-colors "
                        "placeholder:text-[#C9C5B4]/35 focus:border-[#D8FA5E]"
                    ),
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
                    class_name="w-full cursor-pointer appearance-none border border-[#F2EFE4]/14 bg-[#0F110A] py-2.5 pl-9 pr-9 text-sm text-[#F2EFE4] outline-hidden transition-colors focus:border-[#D8FA5E]",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full sm:w-56",
            ),
            action_button(
                "Réinitialiser",
                icon="rotate-ccw",
                tone="ghost",
                on_click=ParcelsState.reset_filters,
            ),
            action_button(
                "Nouvelle parcelle",
                icon="plus",
                tone="solid",
                on_click=ParcelsState.open_parcel_create,
            ),
            class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-4",
        ),
        class_name="w-full border-t border-[#F2EFE4]/12 pt-6",
    )
