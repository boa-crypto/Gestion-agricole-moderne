import reflex as rx

from app.states.menu_configuration_state import MenuConfigurationState


def menu_row(row) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    rx.cond(row["level"] == 0, "layers", "corner-down-right"),
                    class_name="h-4 w-4 shrink-0 text-[#d8fa5e]",
                ),
                rx.el.h3(
                    row["label"], class_name="font-semibold text-[#f2efe4]"
                ),
                rx.cond(
                    row["protected"],
                    rx.el.span(
                        "Protégé",
                        class_name="w-fit rounded-none bg-[#ff8a5b]/10 px-2 py-1 text-xs text-[#ffb894]",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                f"Clé : {row['key']}",
                class_name="mt-2 break-all text-xs text-[#c9c5b4]/75",
            ),
            rx.el.p(
                "Parent : ",
                rx.cond(row["level"] == 0, "—", row["parent"]),
                " · Niveau : ",
                rx.cond(row["level"] == 0, "Principal (0)", "Sous-menu (1)"),
                class_name="mt-1 text-xs text-[#c9c5b4]/75",
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
                class_name="text-xs text-[#c9c5b4]",
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
                    "text-xs text-[#d8fa5e]",
                    "text-xs text-[#ffb894]",
                ),
            ),
            class_name="flex flex-col gap-1 sm:text-right",
        ),
        rx.el.button(
            rx.el.span(
                class_name=rx.cond(
                    row["enabled"],
                    "block h-5 w-5 translate-x-5 rounded-none bg-[#0A0A08] transition-transform",
                    "block h-5 w-5 translate-x-0 rounded-none bg-[#c9c5b4] transition-transform",
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
                "w-12 shrink-0 rounded-none border border-[#d8fa5e] bg-[#D8FA5E] p-1 focus-visible:outline-2 focus-visible:outline-[#ff8a5b] focus-visible:outline-offset-4 disabled:opacity-60",
                "w-12 shrink-0 rounded-none border border-[#f2efe4]/30 bg-[#101208] p-1 focus-visible:outline-2 focus-visible:outline-[#ff8a5b] focus-visible:outline-offset-4 disabled:opacity-60",
            ),
        ),
        key=row["key"],
        class_name=rx.cond(
            row["level"] == 0,
            "flex flex-wrap items-center gap-4 border-b border-[#d8fa5e]/20 bg-[#d8fa5e]/5 p-5",
            "ml-3 flex flex-wrap items-center gap-4 border-b border-[#f2efe4]/12 bg-[#0A0A08]/30 p-5 sm:ml-8",
        ),
    )


def menu_stats(label: str, count) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="text-xs uppercase tracking-wider text-[#c9c5b4]/75",
        ),
        rx.el.p(
            count,
            class_name="mt-2 ap-serif text-4xl text-[#d8fa5e]",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-5",
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
                class_name="block text-sm text-[#c9c5b4]",
            ),
            rx.el.div(
                rx.el.input(
                    id="menu-search",
                    placeholder="Ex. récoltes, agricole.parcelles…",
                    default_value=MenuConfigurationState.search,
                    on_change=MenuConfigurationState.set_search.debounce(500),
                    class_name="min-w-0 flex-1 rounded-none border border-[#f2efe4]/22 bg-[#0A0A08] px-4 py-3 text-sm text-[#f2efe4] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    aria_label="Effacer la recherche",
                    on_click=MenuConfigurationState.clear_search,
                    class_name="rounded-none border border-[#f2efe4]/22 bg-[#14160f] p-3 text-[#d8fa5e] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                ),
                class_name="mt-2 flex gap-2",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "État", class_name="text-xs text-[#c9c5b4]/80"
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
                                "rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/10 px-3 py-2 text-xs text-[#e4ff9b] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                                "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-2 text-xs text-[#c9c5b4] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                            ),
                        ),
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                    role="group",
                    aria_label="Filtrer par état effectif",
                ),
                rx.el.div(
                    rx.el.span(
                        "Niveau", class_name="text-xs text-[#c9c5b4]/80"
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
                                "rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/10 px-3 py-2 text-xs text-[#e4ff9b] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                                "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-2 text-xs text-[#c9c5b4] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                            ),
                        ),
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                    role="group",
                    aria_label="Filtrer par niveau",
                ),
                class_name="mt-4 flex flex-wrap gap-5",
            ),
            class_name="my-5 rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-5",
        ),
        rx.el.p(
            MenuConfigurationState.notice,
            role="status",
            class_name="mb-3 text-sm text-[#e4ff9b]",
        ),
        rx.el.p(
            f"{MenuConfigurationState.filtered_rows.length()} résultat(s). Les filtres se combinent ; l’état est la visibilité effective.",
            aria_live="polite",
            class_name="mb-4 text-xs text-[#c9c5b4]/75",
        ),
        rx.cond(
            MenuConfigurationState.filtered_rows.length() > 0,
            rx.el.div(
                rx.foreach(MenuConfigurationState.filtered_rows, menu_row),
                class_name="w-full overflow-hidden rounded-none border border-[#f2efe4]/12 bg-[#14160F]",
            ),
            rx.el.div(
                rx.icon(
                    "search-x", class_name="mx-auto h-8 w-8 text-[#ff8a5b]"
                ),
                rx.el.p(
                    "Aucun menu ne correspond à votre recherche et à vos filtres.",
                    class_name="mt-4 text-sm text-[#c9c5b4]",
                ),
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-10 text-center",
            ),
        ),
        class_name="w-full",
    )
