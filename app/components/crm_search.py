import reflex as rx

from app.states.crm_state import CrmState, PartnerHit


def _chip(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3 w-3 text-[rgb(var(--ap-accent-rgb))]"),
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] truncate",
        ),
        class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 w-fit max-w-full min-w-0",
    )


def _partner_card(item: PartnerHit) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.el.p(
                    f"{item['code']} · {item['kind_label']}",
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                item["status_label"],
                class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2.5 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-accent-soft-rgb))] w-fit shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            _chip("map-pin", item["city"]),
            _chip("phone", item["phone"]),
            _chip("mail", item["email"]),
            _chip("gauge", f"Score {item['score']}/100"),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "CA",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.span(
                    f"{item['turnover']:.0f} DA",
                    class_name="text-xs font-bold text-[rgb(var(--ap-accent-soft-rgb))]",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.span(
                    "Achats",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.span(
                    f"{item['purchases']:.0f} DA",
                    class_name="text-xs font-bold text-[rgb(var(--ap-flame-tint-rgb))]",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.span(
                    "Créances",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.span(
                    f"{item['outstanding']:.0f} DA",
                    class_name="text-xs font-bold text-[rgb(var(--ap-paper-muted-rgb))]",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.span(
                    "Dettes",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.span(
                    f"{item['debt']:.0f} DA",
                    class_name="text-xs font-bold text-[rgb(var(--ap-paper-muted-rgb))]",
                ),
                class_name="flex flex-col",
            ),
            class_name="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full mt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-3",
        ),
        key=item["id"].to_string(),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors",
    )


def crm_search() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon("radar", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
            rx.el.span(
                "Recherche centralisée des tiers",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.span(
                f"{CrmState.result_count} résultat(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Nom, code, wilaya, commune, téléphone, e-mail, catégorie...",
                default_value=CrmState.search,
                on_change=CrmState.set_search.debounce(400),
                class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2.5 text-sm font-medium text-[rgb(var(--ap-paper-rgb))] placeholder:text-[rgb(var(--ap-paper-muted-rgb)/0.82)] focus:border-[rgb(var(--ap-accent-rgb)/0.40)] focus:outline-hidden",
            ),
            rx.el.button(
                rx.icon("eraser", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-paper-muted-rgb)/0.90)]"),
                rx.el.span(
                    "Réinitialiser",
                    class_name="text-xs font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)]",
                ),
                type="button",
                on_click=CrmState.clear_search,
                class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2.5 hover:border-[rgb(var(--ap-accent-rgb)/0.35)] transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row gap-3 w-full mt-5",
        ),
        rx.cond(
            CrmState.result_count > 0,
            rx.el.div(
                rx.foreach(CrmState.search_results, _partner_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 w-full mt-4",
            ),
            rx.el.p(
                "Aucun tiers ne correspond à cette recherche.",
                class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )
