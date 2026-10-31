import reflex as rx

from app.states.crm_state import AlertRow, CrmState


def _tone_border(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "bad",
            "w-full rounded-none border border-[#ff6b5a]/30 bg-[#ff6b5a]/[0.06] p-4",
        ),
        (
            "warn",
            "w-full rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/[0.06] p-4",
        ),
        "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def _tone_icon(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        ("bad", "h-4 w-4 text-[#ff9b8c]"),
        ("warn", "h-4 w-4 text-[#ff8a5b]"),
        "h-4 w-4 text-[#d8fa5e]",
    )


def _tone_badge(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "bad",
            "rounded-none border border-[#ff6b5a]/30 bg-[#ff6b5a]/10 px-2.5 py-0.5 text-[10px] font-semibold text-[#ffbcb0] w-fit",
        ),
        (
            "warn",
            "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2.5 py-0.5 text-[10px] font-semibold text-[#ffb894] w-fit",
        ),
        "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/70 w-fit",
    )


def _alert_card(item: AlertRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name=_tone_icon(item["tone"])),
            rx.el.div(
                rx.el.p(
                    item["title"],
                    class_name="text-sm font-semibold text-[#f2efe4]",
                ),
                rx.el.p(
                    item["partner"],
                    class_name="text-[11px] font-semibold text-[#e4ff9b]/80",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(item["badge"], class_name=_tone_badge(item["tone"])),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-2",
        ),
        rx.el.p(
            f"{item['amount']:.0f} DA concernés",
            class_name="text-xs font-bold text-[#f2efe4] mt-2",
        ),
        key=item["key"],
        class_name=_tone_border(item["tone"]),
    )


def crm_alerts() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon("bell-ring", class_name="h-4 w-4 text-[#ff8a5b]"),
            rx.el.span(
                "Centre de décision financier",
                class_name="ap-eyebrow text-[#ff8a5b]/80",
            ),
            rx.el.span(
                f"{CrmState.critical_alerts} critique(s) sur {CrmState.alert_count}",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.cond(
            CrmState.has_alerts,
            rx.el.div(
                rx.foreach(CrmState.alerts, _alert_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 w-full mt-5",
            ),
            rx.el.p(
                "Aucune échéance proche, aucun retard et aucune limite de crédit dépassée.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
