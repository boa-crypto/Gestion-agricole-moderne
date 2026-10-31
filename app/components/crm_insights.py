import reflex as rx

from app.states.crm_state import CrmState, Insight


def _icon_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        ("bad", "h-4 w-4 text-[rgb(var(--ap-danger-soft-rgb))]"),
        ("warn", "h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
        ("good", "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
        "h-4 w-4 text-[rgb(var(--ap-sage-rgb))]",
    )


def _card_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "bad",
            "w-full rounded-none border border-[rgb(var(--ap-danger-rgb)/0.25)] bg-[rgb(var(--ap-danger-rgb))]/[0.05] p-4",
        ),
        (
            "warn",
            "w-full rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.05] p-4",
        ),
        "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4",
    )


def _insight_card(item: Insight) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name=_icon_class(item["tone"])),
            rx.el.p(
                item["title"],
                class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))]",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 leading-relaxed",
        ),
        class_name=_card_class(item["tone"]),
    )


def crm_insights() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon("sparkles", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
            rx.el.span(
                "Synthèse intelligente AgriPro",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.span(
                "Analyse locale des données CRM",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.cond(
            CrmState.insights.length() > 0,
            rx.el.div(
                rx.foreach(CrmState.insights, _insight_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 w-full mt-5",
            ),
            rx.el.p(
                "La synthèse s'affichera dès que des transactions seront enregistrées.",
                class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )
