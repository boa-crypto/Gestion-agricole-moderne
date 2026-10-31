"""Champs de formulaire du pupitre éditorial du Guide Agricole."""

import reflex as rx

from app.states.guide_admin_state import GuideAdminState

_LABEL = (
    "ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"
)
_INPUT = (
    "w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-ink-rgb))] px-3 py-2.5 text-sm "
    "font-medium text-[rgb(var(--ap-paper-rgb))] placeholder:text-[rgb(var(--ap-paper-muted-rgb)/0.82)] "
    "focus:border-[rgb(var(--ap-accent-rgb)/0.50)] focus:ring-2 focus:ring-[rgb(var(--ap-accent-rgb)/0.20)] "
    "outline-hidden transition-colors"
)


def text_field(
    label: str,
    name: str,
    value: rx.Var,
    placeholder: str = "",
    hint: str = "",
    required: bool = False,
) -> rx.Component:
    return rx.el.label(
        rx.el.div(
            rx.el.span(label, class_name=_LABEL),
            rx.cond(
                required,
                rx.el.span(
                    "obligatoire",
                    class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.input(
            name=name,
            default_value=value,
            key=f"{GuideAdminState.editor_key}-{name}",
            placeholder=placeholder,
            class_name=f"{_INPUT} mt-1.5",
        ),
        rx.cond(
            hint != "",
            rx.el.span(
                hint,
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col w-full",
    )


def number_field(
    label: str,
    name: str,
    value: rx.Var,
    hint: str = "",
) -> rx.Component:
    return rx.el.label(
        rx.el.span(label, class_name=_LABEL),
        rx.el.input(
            name=name,
            type="number",
            min="1",
            max="240",
            default_value=value,
            key=f"{GuideAdminState.editor_key}-{name}",
            class_name=f"{_INPUT} mt-1.5",
        ),
        rx.cond(
            hint != "",
            rx.el.span(
                hint,
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col w-full",
    )


def area_field(
    label: str,
    name: str,
    value: rx.Var,
    placeholder: str = "",
    rows: str = "5",
    hint: str = "",
) -> rx.Component:
    return rx.el.label(
        rx.el.span(label, class_name=_LABEL),
        rx.el.textarea(
            name=name,
            default_value=value,
            key=f"{GuideAdminState.editor_key}-{name}",
            placeholder=placeholder,
            rows=rows,
            class_name=f"{_INPUT} mt-1.5 leading-relaxed resize-y",
        ),
        rx.cond(
            hint != "",
            rx.el.span(
                hint,
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col w-full",
    )


def select_field(
    label: str,
    name: str,
    value: rx.Var,
    options: rx.Var,
) -> rx.Component:
    return rx.el.label(
        rx.el.span(label, class_name=_LABEL),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    options,
                    lambda option: rx.el.option(option[1], value=option[0]),
                ),
                name=name,
                default_value=value,
                key=f"{GuideAdminState.editor_key}-{name}",
                class_name=f"{_INPUT} appearance-none pr-9 cursor-pointer",
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[rgb(var(--ap-paper-muted-rgb)/0.86)] pointer-events-none",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="flex flex-col w-full",
    )


def category_field(value: rx.Var) -> rx.Component:
    return rx.el.label(
        rx.el.span("Catégorie du guide", class_name=_LABEL),
        rx.el.div(
            rx.el.select(
                rx.el.option("Choisir une catégorie…", value="", disabled=True),
                rx.foreach(
                    GuideAdminState.categories,
                    lambda item: rx.el.option(item["name"], value=item["key"]),
                ),
                name="category_key",
                default_value=value,
                key=f"{GuideAdminState.editor_key}-category_key",
                class_name=f"{_INPUT} appearance-none pr-9 cursor-pointer",
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[rgb(var(--ap-paper-muted-rgb)/0.86)] pointer-events-none",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="flex flex-col w-full",
    )


def check_field(
    label: str, name: str, value: rx.Var, hint: str
) -> rx.Component:
    return rx.el.label(
        rx.el.input(
            name=name,
            type="checkbox",
            default_checked=value == "1",
            key=f"{GuideAdminState.editor_key}-{name}",
            class_name="h-4 w-4 shrink-0 rounded border-[rgb(var(--ap-paper-rgb)/0.30)] bg-[rgb(var(--ap-ink-rgb))] accent-[rgb(var(--ap-accent-rgb))] cursor-pointer mt-0.5",
            default_value="1",
        ),
        rx.el.div(
            rx.el.span(
                label,
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))]",
            ),
            rx.el.p(
                hint,
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-0.5",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] px-3 py-2.5 cursor-pointer",
    )
