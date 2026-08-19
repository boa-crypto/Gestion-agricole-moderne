import reflex as rx

from app.states.crm_state import AlertRow, CrmState


def _tone_border(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "bad",
            "w-full rounded-2xl border border-red-400/30 bg-red-400/[0.06] p-4",
        ),
        (
            "warn",
            "w-full rounded-2xl border border-amber-300/30 bg-amber-300/[0.06] p-4",
        ),
        "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _tone_icon(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        ("bad", "h-4 w-4 text-red-300"),
        ("warn", "h-4 w-4 text-amber-300"),
        "h-4 w-4 text-lime-300",
    )


def _tone_badge(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "bad",
            "rounded-full border border-red-400/30 bg-red-400/10 px-2.5 py-0.5 text-[10px] font-semibold text-red-200 w-fit",
        ),
        (
            "warn",
            "rounded-full border border-amber-300/30 bg-amber-300/10 px-2.5 py-0.5 text-[10px] font-semibold text-amber-200 w-fit",
        ),
        "rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/70 w-fit",
    )


def _alert_card(item: AlertRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name=_tone_icon(item["tone"])),
            rx.el.div(
                rx.el.p(
                    item["title"],
                    class_name="text-sm font-semibold text-emerald-50",
                ),
                rx.el.p(
                    item["partner"],
                    class_name="text-[11px] font-semibold text-lime-200/80",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(item["badge"], class_name=_tone_badge(item["tone"])),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[11px] font-medium text-emerald-100/50 mt-2",
        ),
        rx.el.p(
            f"{item['amount']:.0f} DA concernés",
            class_name="text-xs font-bold text-emerald-50 mt-2",
        ),
        key=item["key"],
        class_name=_tone_border(item["tone"]),
    )


def crm_alerts() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon("bell-ring", class_name="h-4 w-4 text-amber-300"),
            rx.el.span(
                "Centre de décision financier",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/80",
            ),
            rx.el.span(
                f"{CrmState.critical_alerts} critique(s) sur {CrmState.alert_count}",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
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
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
