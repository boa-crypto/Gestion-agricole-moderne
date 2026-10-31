import reflex as rx

from app.states.crm_state import CrmState, Insight


def _icon_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        ("bad", "h-4 w-4 text-[#ff9b8c]"),
        ("warn", "h-4 w-4 text-[#ff8a5b]"),
        ("good", "h-4 w-4 text-[#d8fa5e]"),
        "h-4 w-4 text-[#a9c98b]",
    )


def _card_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "bad",
            "w-full rounded-none border border-[#ff6b5a]/25 bg-[#ff6b5a]/[0.05] p-4",
        ),
        (
            "warn",
            "w-full rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.05] p-4",
        ),
        "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def _insight_card(item: Insight) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name=_icon_class(item["tone"])),
            rx.el.p(
                item["title"],
                class_name="text-sm font-semibold text-[#f2efe4]",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-2 leading-relaxed",
        ),
        class_name=_card_class(item["tone"]),
    )


def crm_insights() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon("sparkles", class_name="h-4 w-4 text-[#d8fa5e]"),
            rx.el.span(
                "Synthèse intelligente AgriPro",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.span(
                "Analyse locale des données CRM",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
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
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
