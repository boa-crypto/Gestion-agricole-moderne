import reflex as rx

CARD = "rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 "
SELECT = "w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors"


def tone_badge(label: rx.Var | str, tone: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/45 w-fit",
        ),
    )


def chip(label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
    )


def section_title(eyebrow: str, title: str, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.span(
            eyebrow,
            class_name="ap-eyebrow text-[#d8fa5e]/80",
        ),
        rx.el.h2(
            title,
            class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
        ),
        rx.el.p(
            hint,
            class_name="text-[11px] font-medium text-[#c9c5b4]/45 mt-1",
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
            class_name="h-full w-full rounded-none object-cover",
        ),
        class_name="h-10 w-10 shrink-0 overflow-hidden rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10",
    )


def stat_line(
    icon: str, label: rx.Var | str, value: rx.Var | str
) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/80 shrink-0"),
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/40",
        ),
        rx.el.span(
            value,
            class_name="text-sm font-medium text-[#f2efe4] ml-auto text-right truncate",
        ),
        class_name="flex items-center gap-2 w-full min-w-0 border-b border-[#f2efe4]/10 py-2",
    )
