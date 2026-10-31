import reflex as rx

from app.states.guide_state import FaqCard, GuideState


def _faq_row(item: FaqCard, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.el.div(
                rx.icon(
                    "message-circle-question",
                    class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
                ),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
            ),
            rx.el.div(
                rx.el.p(
                    item["question"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] text-left",
                ),
                rx.el.div(
                    rx.el.span(
                        item["category_name"],
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
                    ),
                    rx.el.span(
                        item["audience_label"],
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
                    ),
                    rx.cond(
                        item["is_frequent"],
                        rx.el.span(
                            "Fréquente",
                            class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.35)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.icon(
                "chevron-down",
                class_name=rx.cond(
                    GuideState.open_faq_id == item["id"],
                    "h-4 w-4 text-[rgb(var(--ap-accent-rgb))] rotate-180 transition-transform shrink-0",
                    "h-4 w-4 text-[rgb(var(--ap-paper-muted-rgb)/0.86)] transition-transform shrink-0",
                ),
            ),
            on_click=GuideState.toggle_faq(item["id"]),
            class_name="flex items-start gap-3 w-full text-left",
        ),
        rx.cond(
            GuideState.open_faq_id == item["id"],
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "Réponse agricole",
                        class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.70)]",
                    ),
                    rx.el.p(
                        item["answer_farmer"],
                        class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] leading-relaxed mt-1",
                    ),
                    class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
                ),
                rx.el.div(
                    rx.el.span(
                        "Réponse AgriPro",
                        class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.70)]",
                    ),
                    rx.el.p(
                        item["answer_pro"],
                        class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] leading-relaxed mt-1",
                    ),
                    class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
                ),
                rx.cond(
                    item["module_route"] != "",
                    rx.el.a(
                        rx.el.span("Ouvrir l'écran concerné"),
                        rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                        href=item["module_route"],
                        class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1.5 text-[11px] font-semibold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit shrink-0 self-end",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-col lg:flex-row gap-2 w-full mt-4 pt-4 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name=rx.cond(
            GuideState.open_faq_id == item["id"],
            "w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb))]/[0.05] p-4",
            "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-colors",
        ),
    )


def guide_faq() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "FAQ intelligente",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Les questions posées sur le terrain",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    f"Périmètre : {GuideState.category_label}",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{GuideState.frequent_questions.length()} fréquente(s)",
                    class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                ),
                rx.el.span(
                    f"{GuideState.visible_faq.length()} affichée(s)",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            GuideState.visible_faq.length() > 0,
            rx.el.div(
                rx.foreach(
                    GuideState.visible_faq,
                    lambda item: _faq_row(item, key=item["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("search-x", class_name="h-6 w-6 text-[rgb(var(--ap-flame-soft-rgb))]"),
                rx.el.p(
                    "Aucune question pour cette catégorie.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-12 w-full mt-5",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )
