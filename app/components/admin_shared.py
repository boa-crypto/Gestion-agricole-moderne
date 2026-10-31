import reflex as rx

CARD = "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6 "
SELECT = (
    "w-full cursor-pointer appearance-none border border-[rgb(var(--ap-paper-rgb)/0.21)] "
    "bg-[rgb(var(--ap-surface-faint-rgb))] py-2.5 pl-9 pr-9 text-sm text-[rgb(var(--ap-paper-rgb))] outline-hidden "
    "transition-colors focus:border-[rgb(var(--ap-accent-rgb))]"
)


def tone_badge(label: rx.Var | str, tone: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
        ),
    )


def chip(label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
    )


def section_title(eyebrow: str, title: str, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.span(
            eyebrow,
            class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
        ),
        rx.el.h2(
            title,
            class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
        ),
        rx.el.p(
            hint,
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1",
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
        class_name="h-10 w-10 shrink-0 overflow-hidden rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
    )


def stat_line(
    icon: str, label: rx.Var | str, value: rx.Var | str
) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)] shrink-0"),
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
        ),
        rx.el.span(
            value,
            class_name="text-sm font-medium text-[rgb(var(--ap-paper-rgb))] ml-auto text-right truncate",
        ),
        class_name="flex items-center gap-2 w-full min-w-0 border-b border-[rgb(var(--ap-paper-rgb)/0.15)] py-2",
    )
