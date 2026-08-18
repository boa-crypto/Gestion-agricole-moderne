import reflex as rx

CARD = "rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl"
SELECT = "w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"


def tone_badge(label: rx.Var | str, tone: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/45 w-fit",
        ),
    )


def chip(label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
    )


def section_title(eyebrow: str, title: str, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.span(
            eyebrow,
            class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
        ),
        rx.el.h2(
            title,
            class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
        ),
        rx.el.p(
            hint,
            class_name="text-[11px] font-medium text-emerald-100/45 mt-1",
        ),
        class_name="min-w-0",
    )


def avatar(seed: rx.Var | str, initials: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.image(
            src=rx.Var.create(
                "https://api.dicebear.com/9.x/notionists/svg?seed="
            )
            + seed,
            alt=initials,
            class_name="h-full w-full rounded-full object-cover",
        ),
        class_name="h-10 w-10 shrink-0 overflow-hidden rounded-full border border-lime-300/30 bg-lime-300/10",
    )


def stat_line(
    icon: str, label: rx.Var | str, value: rx.Var | str
) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/80 shrink-0"),
        rx.el.span(
            label,
            class_name="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-100/40",
        ),
        rx.el.span(
            value,
            class_name="text-sm font-medium text-emerald-50 ml-auto text-right truncate",
        ),
        class_name="flex items-center gap-2 w-full min-w-0 border-b border-white/[0.06] py-2",
    )
