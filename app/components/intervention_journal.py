import reflex as rx

from app.states.operations_state import JournalRow, Option, OperationsState

_SELECT = "w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"


def _type_icon(type_key: rx.Var, class_name: str) -> rx.Component:
    return rx.match(
        type_key,
        ("SEMIS", rx.icon("sprout", class_name=class_name)),
        ("PLANTATION", rx.icon("shovel", class_name=class_name)),
        ("FERTILISATION", rx.icon("package", class_name=class_name)),
        ("TRAITEMENT_PHYTO", rx.icon("spray-can", class_name=class_name)),
        ("DESHERBAGE", rx.icon("scissors", class_name=class_name)),
        ("IRRIGATION", rx.icon("droplets", class_name=class_name)),
        ("TRAVAIL_DU_SOL", rx.icon("tractor", class_name=class_name)),
        ("OBSERVATION", rx.icon("eye", class_name=class_name)),
        ("RECOLTE", rx.icon("wheat", class_name=class_name)),
        rx.icon("circle-dot", class_name=class_name),
    )


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "done",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            (
                "running",
                "rounded-full border border-emerald-300/30 bg-emerald-300/10 px-2 py-0.5 text-[10px] font-bold text-emerald-200 w-fit",
            ),
            (
                "late",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
            ),
            (
                "cancelled",
                "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-bold text-emerald-100/40 line-through w-fit",
            ),
            "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit",
        ),
    )


def _filter_select(
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
            key=f"{name}-{OperationsState.form_key}",
            on_change=on_change,
            class_name=_SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-52",
    )


def _journal_filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher un chantier, un opérateur, une cible…",
                default_value=OperationsState.search,
                on_change=OperationsState.set_search.debounce(400),
                class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
            ),
            class_name="relative flex-1 min-w-0",
        ),
        _filter_select(
            "type_filter",
            "spray-can",
            OperationsState.type_filter,
            OperationsState.set_type_filter,
            rx.el.option("Tous les types", value="TOUS"),
            OperationsState.type_options,
        ),
        _filter_select(
            "status_filter",
            "flag",
            OperationsState.status_filter,
            OperationsState.set_status_filter,
            rx.el.option("Tous les statuts", value="TOUS"),
            OperationsState.status_options,
        ),
        _filter_select(
            "parcel_filter",
            "map",
            OperationsState.parcel_filter,
            OperationsState.set_parcel_filter,
            rx.el.option("Toutes les parcelles", value="TOUS"),
            OperationsState.parcel_options,
        ),
        _filter_select(
            "period_filter",
            "calendar-range",
            OperationsState.period_filter,
            OperationsState.set_period_filter,
            rx.el.option("Période", value="", disabled=True),
            OperationsState.period_options,
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4"),
            rx.el.span("Réinitialiser"),
            on_click=OperationsState.reset_filters,
            class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
        ),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span("Planifier", class_name="text-[#04140d]"),
            on_click=OperationsState.open_intervention_create,
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
        ),
        class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-5",
    )


def _header_cell(label: str, icon: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/70"),
            rx.el.span(label),
            class_name="flex items-center gap-1.5",
        ),
        class_name=f"px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/45 whitespace-nowrap {extra}",
    )


def _actions(row: JournalRow) -> rx.Component:
    return rx.el.div(
        rx.cond(
            row["is_done"],
            rx.fragment(),
            rx.el.button(
                rx.icon("check", class_name="h-3.5 w-3.5"),
                on_click=OperationsState.mark_done(row["id"]),
                title="Marquer réalisée",
                class_name="flex items-center justify-center h-7 w-7 rounded-lg border border-lime-300/30 bg-lime-300/10 text-lime-200 hover:bg-lime-300/20 transition-colors",
            ),
        ),
        rx.cond(
            row["is_done"],
            rx.fragment(),
            rx.el.button(
                rx.icon("calendar-plus", class_name="h-3.5 w-3.5"),
                on_click=OperationsState.postpone(row["id"]),
                title="Reporter de 7 jours",
                class_name="flex items-center justify-center h-7 w-7 rounded-lg border border-amber-300/30 bg-amber-300/10 text-amber-200 hover:bg-amber-300/20 transition-colors",
            ),
        ),
        rx.el.button(
            rx.icon("pencil", class_name="h-3.5 w-3.5"),
            on_click=OperationsState.open_intervention_edit(row["id"]),
            title="Modifier",
            class_name="flex items-center justify-center h-7 w-7 rounded-lg border border-white/10 bg-white/5 text-emerald-100/70 hover:text-emerald-50 hover:border-lime-300/30 transition-colors",
        ),
        rx.cond(
            row["is_done"],
            rx.fragment(),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                on_click=OperationsState.cancel_intervention(row["id"]),
                title="Annuler",
                class_name="flex items-center justify-center h-7 w-7 rounded-lg border border-red-400/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 transition-colors",
            ),
        ),
        class_name="flex items-center gap-1.5 justify-end",
    )


def _journal_row(row: JournalRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.div(
                    _type_icon(row["type"], "h-4 w-4 text-lime-300"),
                    class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04]",
                ),
                rx.el.div(
                    rx.el.p(
                        row["title"],
                        class_name="text-sm font-semibold text-emerald-50 truncate",
                    ),
                    rx.el.p(
                        f"{row['type_label']} · cible {row['target']}",
                        class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-center gap-2.5 min-w-0",
            ),
            class_name="px-3 py-3 align-middle min-w-[16rem]",
        ),
        rx.el.td(
            rx.el.p(
                row["parcel"],
                class_name="text-xs font-semibold text-emerald-50 truncate",
            ),
            rx.el.p(
                row["crop_name"],
                class_name="text-[10px] font-medium text-emerald-100/45 truncate",
            ),
            class_name="px-3 py-3 align-middle min-w-[11rem]",
        ),
        rx.el.td(
            rx.el.p(
                row["scheduled_label"],
                class_name="text-xs font-semibold text-emerald-50 whitespace-nowrap",
            ),
            rx.el.p(
                rx.cond(
                    row["is_overdue"],
                    f"retard de {row['days_delta'] * -1} j",
                    rx.cond(
                        row["is_done"],
                        f"fait le {row['done_label']}",
                        rx.cond(
                            row["days_delta"] == 0,
                            "aujourd'hui",
                            f"dans {row['days_delta']} j",
                        ),
                    ),
                ),
                class_name=rx.cond(
                    row["is_overdue"],
                    "text-[10px] font-semibold text-red-300 whitespace-nowrap",
                    "text-[10px] font-medium text-emerald-100/45 whitespace-nowrap",
                ),
            ),
            class_name="px-3 py-3 align-middle",
        ),
        rx.el.td(
            _status_badge(row["tone"], row["status_label"]),
            class_name="px-3 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                row["operator"],
                class_name="text-xs font-medium text-emerald-100/70 truncate",
            ),
            rx.el.p(
                row["equipment"],
                class_name="text-[10px] font-medium text-emerald-100/40 truncate",
            ),
            class_name="px-3 py-3 align-middle min-w-[10rem]",
        ),
        rx.el.td(
            rx.el.div(
                rx.cond(
                    row["product_count"] > 0,
                    rx.icon(
                        "flask-conical",
                        class_name="h-3.5 w-3.5 text-amber-300/80",
                    ),
                    rx.icon(
                        "minus", class_name="h-3.5 w-3.5 text-emerald-100/30"
                    ),
                ),
                rx.el.span(
                    row["product_label"],
                    class_name="text-[11px] font-medium text-emerald-100/60 truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            class_name="px-3 py-3 align-middle min-w-[10rem]",
        ),
        rx.el.td(
            rx.el.span(
                f"{row['area_ha']:.1f} ha",
                class_name="text-xs font-medium text-emerald-100/70 whitespace-nowrap",
            ),
            class_name="px-3 py-3 align-middle text-right",
        ),
        rx.el.td(
            rx.el.span(
                f"{row['cost']:.0f} €",
                class_name="text-xs font-semibold text-lime-200 whitespace-nowrap",
            ),
            class_name="px-3 py-3 align-middle text-right",
        ),
        rx.el.td(
            _actions(row),
            class_name="px-3 py-3 align-middle",
        ),
        key=key,
        class_name=rx.cond(
            row["is_overdue"],
            "border-b border-white/5 bg-red-500/[0.05] hover:bg-red-500/[0.09] transition-colors",
            "border-b border-white/5 even:bg-white/[0.02] hover:bg-lime-300/[0.05] transition-colors",
        ),
    )


def intervention_journal() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Journal opérationnel",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Traitements & chantiers",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{OperationsState.journal_count} lignes",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
                ),
                rx.el.span(
                    f"{OperationsState.planned_count} à réaliser",
                    class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1 text-[11px] font-semibold text-amber-200 w-fit",
                ),
                rx.el.span(
                    f"{OperationsState.journal_cost:.0f} € engagés",
                    class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-3 py-1 text-[11px] font-semibold text-lime-200 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        _journal_filters(),
        rx.cond(
            OperationsState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-xl bg-white/[0.05]"
                ),
                class_name="flex flex-col gap-2 mt-6",
            ),
            rx.cond(
                OperationsState.journal.length() > 0,
                rx.el.div(
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    _header_cell("Chantier", "clipboard-list"),
                                    _header_cell(
                                        "Parcelle / culture", "map-pin"
                                    ),
                                    _header_cell("Échéance", "calendar-days"),
                                    _header_cell("Statut", "flag"),
                                    _header_cell("Opérateur", "user-round"),
                                    _header_cell("Intrants", "flask-conical"),
                                    _header_cell(
                                        "Surface", "ruler", "text-right"
                                    ),
                                    _header_cell("Coût", "coins", "text-right"),
                                    _header_cell("Actions", "settings_2"),
                                    class_name="border-b border-white/10 bg-white/[0.03]",
                                ),
                            ),
                            rx.el.tbody(
                                rx.foreach(
                                    OperationsState.journal,
                                    lambda row: _journal_row(
                                        row, key=row["id"].to_string()
                                    ),
                                ),
                            ),
                            class_name="table-auto w-full min-w-[68rem]",
                        ),
                        class_name="overflow-x-auto",
                    ),
                    class_name="mt-6 w-full rounded-2xl border border-white/10 bg-[#03110b]/60 overflow-hidden max-h-[42rem] overflow-y-auto",
                ),
                rx.el.div(
                    rx.icon("search-x", class_name="h-6 w-6 text-amber-300"),
                    rx.el.p(
                        "Aucun chantier ne correspond aux filtres sélectionnés.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-14 mt-6",
                ),
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
