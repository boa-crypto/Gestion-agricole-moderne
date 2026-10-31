import reflex as rx

from app.states.guide_state import GuideState, RelationNode


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "operations",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)]",
        ),
        (
            "humain",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)]",
        ),
        (
            "flotte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-sage-rgb)/0.30)] bg-[rgb(var(--ap-sage-rgb)/0.10)]",
        ),
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
    )


def _tone_icon(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("operations", "h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
        ("humain", "h-4 w-4 text-[rgb(var(--ap-info-rgb))]"),
        ("flotte", "h-4 w-4 text-[rgb(var(--ap-sage-rgb))]"),
        "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
    )


def _chip(label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
    )


def _node_card(node: RelationNode, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.span(
                node["step"],
                class_name="text-[10px] font-bold tracking-[0.18em] text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.cond(
                node["is_parallel"],
                rx.el.span(
                    "En parallèle",
                    class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit ml-auto",
                ),
                rx.icon(
                    "arrow-down-right",
                    class_name="h-3 w-3 text-[rgb(var(--ap-paper-muted-rgb)/0.82)] ml-auto",
                ),
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(node["icon"], class_name=_tone_icon(node["tone"])),
                class_name=_tone_ring(node["tone"]),
            ),
            rx.el.div(
                rx.el.p(
                    node["label"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] text-left",
                ),
                rx.el.p(
                    node["route_label"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-left mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-center gap-3 w-full mt-3",
        ),
        on_click=GuideState.select_relation(node["key"]),
        key=key,
        class_name=rx.cond(
            GuideState.active_relation == node["key"],
            "w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.45)] bg-[rgb(var(--ap-accent-rgb))]/[0.09] p-4 text-left ring-2 ring-[rgb(var(--ap-accent-rgb)/0.30)] transition-all",
            "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 text-left hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] hover:bg-[rgb(var(--ap-surface-high-rgb))] transition-all",
        ),
    )


def _detail() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    GuideState.active_relation_node["icon"],
                    class_name=_tone_icon(
                        GuideState.active_relation_node["tone"]
                    ),
                ),
                class_name=_tone_ring(GuideState.active_relation_node["tone"]),
            ),
            rx.el.div(
                rx.el.span(
                    f"Étape {GuideState.active_relation_node['step']} de la chaîne de données",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h3(
                    GuideState.active_relation_node["label"],
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.a(
                rx.el.span(GuideState.active_relation_node["route_label"]),
                rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                href=GuideState.active_relation_node["route"],
                class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-4 py-2 text-[11px] font-semibold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Lecture agricole",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.70)]",
                ),
                rx.el.p(
                    GuideState.active_relation_node["summary_farmer"],
                    class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] leading-relaxed mt-1",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Lecture AgriPro",
                    class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.70)]",
                ),
                rx.el.p(
                    GuideState.active_relation_node["summary_pro"],
                    class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] leading-relaxed mt-1",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "arrow-down-to-line",
                        class_name="h-3 w-3 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    rx.el.span(
                        "Ce qui alimente",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.active_relation_node["inputs"], _chip
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "arrow-up-from-line",
                        class_name="h-3 w-3 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    rx.el.span(
                        "Ce qui en découle",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.active_relation_node["outputs"], _chip
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("gauge", class_name="h-3 w-3 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"),
                    rx.el.span(
                        "Indicateurs suivis",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.active_relation_node["metrics"], _chip
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-3",
        ),
        rx.el.button(
            rx.icon("book-open", class_name="h-3.5 w-3.5"),
            rx.el.span("Lire la catégorie du guide associée"),
            on_click=GuideState.select_category(
                GuideState.active_relation_node["category_key"]
            ),
            class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit mt-4",
        ),
        class_name="w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-ink-rgb)/0.70)] p-5 mt-5",
    )


def guide_relations() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Carte de connaissances vivante",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Relations des données de l'exploitation",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Exploitation → parcelle → culture → campagne → intervention → intrants / main d'œuvre / matériel → coût → récolte → rendement → vente → résultat.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[rgb(var(--ap-paper-muted-rgb)/0.90)] max-w-3xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{GuideState.relation_chain.length()} maillons cliquables",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(
                GuideState.relation_chain,
                lambda node: _node_card(node, key=node["key"]),
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-3 w-full mt-5",
        ),
        _detail(),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )
