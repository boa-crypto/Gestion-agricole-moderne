import reflex as rx

from app.admin_users import Option, RbacRow
from app.components.admin_shared import CARD, SELECT, chip, section_title
from app.components.admin_user_detail import activity_row
from app.states.administration_state import AdministrationState


def _role_select() -> rx.Component:
    return rx.el.div(
        rx.icon(
            "shield-check",
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
        ),
        rx.el.select(
            rx.foreach(
                AdministrationState.role_options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name="rbac_role",
            default_value=AdministrationState.rbac_role,
            key=f"rbac-{AdministrationState.form_key}",
            on_change=AdministrationState.set_rbac_role,
            class_name=SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-64",
    )


def _rbac_row(row: RbacRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.icon(row["icon"], class_name="h-4 w-4 text-lime-300"),
                rx.el.div(
                    rx.el.p(
                        row["label"],
                        class_name="text-sm font-semibold text-emerald-50 truncate",
                    ),
                    rx.el.p(
                        row["route"],
                        class_name="text-[10px] font-medium text-emerald-100/35",
                    ),
                    class_name="min-w-0",
                ),
                rx.cond(
                    row["sensitive"],
                    rx.el.span(
                        "SENSIBLE",
                        class_name="rounded-full border border-amber-300/40 bg-amber-300/10 px-1.5 py-0.5 text-[9px] font-bold text-amber-200 w-fit",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(
            rx.cond(
                row["granted_count"] > 0,
                rx.el.div(
                    rx.foreach(row["granted"], chip),
                    class_name="flex flex-wrap items-center gap-1.5",
                ),
                rx.el.span(
                    "Aucun accès",
                    class_name="text-[11px] font-semibold text-emerald-100/35",
                ),
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.span(
                row["granted_count"].to_string()
                + " / "
                + row["total"].to_string(),
                class_name=rx.cond(
                    row["granted_count"] == row["total"],
                    "text-xs font-bold text-lime-200",
                    rx.cond(
                        row["granted_count"] > 0,
                        "text-xs font-bold text-amber-200",
                        "text-xs font-semibold text-emerald-100/35",
                    ),
                ),
            ),
            class_name="px-4 py-3 align-middle text-right whitespace-nowrap",
        ),
        class_name="border-t border-white/[0.06] hover:bg-white/[0.03] transition-colors",
    )


def admin_rbac() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Matrice RBAC",
                "Rôles & permissions",
                "Ce que le rôle peut réellement faire, module par module et action par action.",
            ),
            rx.el.div(
                _role_select(),
                rx.el.span(
                    AdministrationState.rbac_granted.to_string()
                    + " permission(s) accordée(s)",
                    class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-3 py-1.5 text-[11px] font-bold text-lime-200 w-fit",
                ),
                class_name="flex flex-col sm:flex-row items-stretch sm:items-center gap-3",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th(
                            rx.el.div(
                                rx.icon(
                                    "layers", class_name="h-3.5 w-3.5 mr-2"
                                ),
                                rx.el.span("Module AgriPro"),
                                class_name="flex items-center",
                            ),
                            class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
                        ),
                        rx.el.th(
                            rx.el.div(
                                rx.icon(
                                    "key-round", class_name="h-3.5 w-3.5 mr-2"
                                ),
                                rx.el.span("Actions autorisées"),
                                class_name="flex items-center",
                            ),
                            class_name="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
                        ),
                        rx.el.th(
                            "Couverture",
                            class_name="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
                        ),
                        class_name="bg-white/[0.04]",
                    ),
                ),
                rx.el.tbody(
                    rx.foreach(AdministrationState.rbac, _rbac_row),
                ),
                class_name="table-auto w-full min-w-[42rem]",
            ),
            class_name="mt-5 w-full overflow-x-auto overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02]",
        ),
        class_name=f"w-full {CARD}",
    )


def _journal_select(
    name: str,
    icon: str,
    value: rx.Var,
    on_change: rx.event.EventType,
    first_label: str,
    options: rx.Var[list[Option]],
) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
        ),
        rx.el.select(
            rx.el.option(first_label, value="TOUS"),
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"journal-{name}-{AdministrationState.form_key}",
            on_change=on_change,
            class_name=SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-56",
    )


def _journal_filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher un acteur, un objet, un module ou une action…",
                default_value=AdministrationState.journal_search,
                on_change=AdministrationState.set_journal_search.debounce(400),
                class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
            ),
            class_name="relative flex-1 min-w-0",
        ),
        _journal_select(
            "kind",
            "activity",
            AdministrationState.journal_kind,
            AdministrationState.set_journal_kind,
            "Tous les évènements",
            AdministrationState.journal_kinds,
        ),
        _journal_select(
            "module",
            "layers",
            AdministrationState.journal_module,
            AdministrationState.set_journal_module,
            "Tous les modules",
            AdministrationState.journal_modules,
        ),
        rx.el.button(
            rx.icon("shield-alert", class_name="h-4 w-4"),
            rx.el.span("Audit sensible"),
            on_click=AdministrationState.toggle_journal_sensitive,
            class_name=rx.cond(
                AdministrationState.journal_sensitive_only,
                "flex items-center gap-2 rounded-xl border border-amber-300/40 bg-amber-300/10 px-4 py-2.5 text-sm font-semibold text-amber-200 transition-colors w-fit",
                "flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4"),
            rx.el.span("Réinitialiser"),
            on_click=AdministrationState.reset_journal_filters,
            class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
        ),
        rx.el.button(
            rx.icon("download", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span("Exporter (CSV)", class_name="text-[#04140d]"),
            on_click=AdministrationState.export_journal,
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
        ),
        class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-5",
    )


def admin_journal() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Audit",
                "Journal d'activité",
                "Utilisateur → action → objet → date, y compris les refus d'accès.",
            ),
            rx.el.div(
                rx.el.span(
                    AdministrationState.journal_count.to_string()
                    + " évènement(s) affiché(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-bold text-emerald-100/70 w-fit",
                ),
                rx.el.span(
                    AdministrationState.journal_sensitive_count.to_string()
                    + " sensible(s) sur "
                    + AdministrationState.kpis["sensitive_events"].to_string()
                    + " au total",
                    class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1.5 text-[11px] font-bold text-amber-200 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3",
        ),
        _journal_filters(),
        rx.el.p(
            "Périmètre courant : " + AdministrationState.journal_filter_label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40 mt-4",
        ),
        rx.cond(
            AdministrationState.activity.length() > 0,
            rx.el.div(
                rx.foreach(AdministrationState.activity, activity_row),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-4 max-h-[52rem] overflow-y-auto pr-1",
            ),
            rx.el.p(
                "Aucune activité consignée pour ces critères.",
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name=f"w-full {CARD}",
    )
