import reflex as rx

from app.states.menu_configuration_state import MenuConfigurationState


def menu_row(row) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    rx.cond(row["level"] == 0, "layers", "corner-down-right"),
                    class_name="h-4 w-4 shrink-0 text-lime-300",
                ),
                rx.el.h3(
                    row["label"], class_name="font-semibold text-emerald-50"
                ),
                rx.cond(
                    row["protected"],
                    rx.el.span(
                        "Protégé",
                        class_name="w-fit rounded-lg bg-amber-300/10 px-2 py-1 text-xs text-amber-200",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                f"Clé : {row['key']}",
                class_name="mt-2 break-all text-xs text-emerald-100/75",
            ),
            rx.el.p(
                "Parent : ",
                rx.cond(row["level"] == 0, "—", row["parent"]),
                " · Niveau : ",
                rx.cond(row["level"] == 0, "Principal (0)", "Sous-menu (1)"),
                class_name="mt-1 text-xs text-emerald-100/75",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.span(
                rx.cond(
                    row["enabled"],
                    "Individuel : activé",
                    "Individuel : désactivé",
                ),
                class_name="text-xs text-emerald-100",
            ),
            rx.el.span(
                rx.cond(
                    row["effective"],
                    "Visible dans la navigation",
                    rx.cond(
                        row["enabled"],
                        "Masqué par le parent",
                        "Masqué dans la navigation",
                    ),
                ),
                class_name=rx.cond(
                    row["effective"],
                    "text-xs text-lime-300",
                    "text-xs text-amber-200",
                ),
            ),
            class_name="flex flex-col gap-1 sm:text-right",
        ),
        rx.el.button(
            rx.el.span(
                class_name=rx.cond(
                    row["enabled"],
                    "block h-5 w-5 translate-x-5 rounded-full bg-[#04120c] transition-transform",
                    "block h-5 w-5 translate-x-0 rounded-full bg-emerald-100 transition-transform",
                )
            ),
            role="switch",
            aria_checked=row["enabled"],
            aria_label=f"Activer ou désactiver {row['label']} ({row['key']})",
            title=rx.cond(
                row["protected"],
                "La configuration reste toujours accessible",
                "Modifier l’activation individuelle",
            ),
            on_click=MenuConfigurationState.toggle_menu(row["key"]),
            disabled=row["protected"] | MenuConfigurationState.saving,
            class_name=rx.cond(
                row["enabled"],
                "w-12 shrink-0 rounded-full border border-lime-300 bg-[#a3e635] p-1 focus-visible:outline-2 focus-visible:outline-amber-300 focus-visible:outline-offset-4 disabled:opacity-60",
                "w-12 shrink-0 rounded-full border border-white/30 bg-emerald-950 p-1 focus-visible:outline-2 focus-visible:outline-amber-300 focus-visible:outline-offset-4 disabled:opacity-60",
            ),
        ),
        key=row["key"],
        class_name=rx.cond(
            row["level"] == 0,
            "flex flex-wrap items-center gap-4 border-b border-lime-300/20 bg-lime-300/5 p-5",
            "ml-3 flex flex-wrap items-center gap-4 border-b border-white/10 bg-[#04120c]/30 p-5 sm:ml-8",
        ),
    )


def menu_stats(label: str, count) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="text-xs uppercase tracking-wider text-emerald-100/75",
        ),
        rx.el.p(
            count,
            class_name="mt-2 font-['Instrument_Serif'] text-4xl text-lime-300",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-[#071c13] p-5",
    )


def menu_configuration_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            menu_stats("Total", MenuConfigurationState.total),
            menu_stats("Activés", MenuConfigurationState.active),
            menu_stats("Désactivés", MenuConfigurationState.disabled_count),
            class_name="grid w-full grid-cols-3 gap-3 sm:gap-4",
        ),
        rx.el.div(
            rx.el.label(
                "Rechercher par libellé ou clé",
                html_for="menu-search",
                class_name="block text-sm text-emerald-100",
            ),
            rx.el.div(
                rx.el.input(
                    id="menu-search",
                    placeholder="Ex. récoltes, agricole.parcelles…",
                    default_value=MenuConfigurationState.search,
                    on_change=MenuConfigurationState.set_search.debounce(500),
                    class_name="min-w-0 flex-1 rounded-xl border border-white/20 bg-[#04120c] px-4 py-3 text-sm text-emerald-50 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    aria_label="Effacer la recherche",
                    on_click=MenuConfigurationState.clear_search,
                    class_name="rounded-xl border border-white/20 bg-white/5 p-3 text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                class_name="mt-2 flex gap-2",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "État", class_name="text-xs text-emerald-100/80"
                    ),
                    rx.foreach(
                        ["Tous", "Activés", "Désactivés"],
                        lambda label: rx.el.button(
                            label,
                            aria_pressed=MenuConfigurationState.status_filter
                            == label,
                            on_click=MenuConfigurationState.set_status_filter(
                                label
                            ),
                            class_name=rx.cond(
                                MenuConfigurationState.status_filter == label,
                                "rounded-xl border border-lime-300/40 bg-lime-300/10 px-3 py-2 text-xs text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
                                "rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-emerald-100 focus-visible:outline-2 focus-visible:outline-lime-300",
                            ),
                        ),
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                    role="group",
                    aria_label="Filtrer par état effectif",
                ),
                rx.el.div(
                    rx.el.span(
                        "Niveau", class_name="text-xs text-emerald-100/80"
                    ),
                    rx.foreach(
                        ["Tous", "Principaux", "Sous-menus"],
                        lambda label: rx.el.button(
                            label,
                            aria_pressed=MenuConfigurationState.level_filter
                            == label,
                            on_click=MenuConfigurationState.set_level_filter(
                                label
                            ),
                            class_name=rx.cond(
                                MenuConfigurationState.level_filter == label,
                                "rounded-xl border border-lime-300/40 bg-lime-300/10 px-3 py-2 text-xs text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
                                "rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-emerald-100 focus-visible:outline-2 focus-visible:outline-lime-300",
                            ),
                        ),
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                    role="group",
                    aria_label="Filtrer par niveau",
                ),
                class_name="mt-4 flex flex-wrap gap-5",
            ),
            class_name="my-5 rounded-2xl border border-white/10 bg-[#071c13] p-5",
        ),
        rx.el.p(
            MenuConfigurationState.notice,
            role="status",
            class_name="mb-3 text-sm text-lime-200",
        ),
        rx.el.p(
            f"{MenuConfigurationState.filtered_rows.length()} résultat(s). Les filtres se combinent ; l’état est la visibilité effective.",
            aria_live="polite",
            class_name="mb-4 text-xs text-emerald-100/75",
        ),
        rx.cond(
            MenuConfigurationState.filtered_rows.length() > 0,
            rx.el.div(
                rx.foreach(MenuConfigurationState.filtered_rows, menu_row),
                class_name="w-full overflow-hidden rounded-2xl border border-white/10 bg-[#071c13]",
            ),
            rx.el.div(
                rx.icon(
                    "search-x", class_name="mx-auto h-8 w-8 text-amber-300"
                ),
                rx.el.p(
                    "Aucun menu ne correspond à votre recherche et à vos filtres.",
                    class_name="mt-4 text-sm text-emerald-100",
                ),
                class_name="rounded-2xl border border-white/10 bg-[#071c13] p-10 text-center",
            ),
        ),
        class_name="w-full",
    )
