import reflex as rx

from app.states.crm_state import CrmState, Insight


def _icon_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        ("bad", "h-4 w-4 text-red-300"),
        ("warn", "h-4 w-4 text-amber-300"),
        ("good", "h-4 w-4 text-lime-300"),
        "h-4 w-4 text-emerald-300",
    )


def _card_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "bad",
            "w-full rounded-2xl border border-red-400/25 bg-red-400/[0.05] p-4",
        ),
        (
            "warn",
            "w-full rounded-2xl border border-amber-300/25 bg-amber-300/[0.05] p-4",
        ),
        "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _insight_card(item: Insight) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name=_icon_class(item["tone"])),
            rx.el.p(
                item["title"],
                class_name="text-sm font-semibold text-emerald-50",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[11px] font-medium text-emerald-100/55 mt-2 leading-relaxed",
        ),
        class_name=_card_class(item["tone"]),
    )


def crm_insights() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon("sparkles", class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                "Synthèse intelligente AgriPro",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.span(
                "Analyse locale des données CRM",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
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
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
