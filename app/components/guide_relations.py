import reflex as rx

from app.states.guide_state import GuideState, RelationNode


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "operations",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-amber-300/30 bg-amber-300/10",
        ),
        (
            "humain",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-sky-300/30 bg-sky-300/10",
        ),
        (
            "flotte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-emerald-300/30 bg-emerald-300/10",
        ),
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/30 bg-lime-300/10",
    )


def _tone_icon(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("operations", "h-4 w-4 text-amber-300"),
        ("humain", "h-4 w-4 text-sky-300"),
        ("flotte", "h-4 w-4 text-emerald-300"),
        "h-4 w-4 text-lime-300",
    )


def _chip(label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
    )


def _node_card(node: RelationNode, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.span(
                node["step"],
                class_name="text-[10px] font-bold tracking-[0.18em] text-emerald-100/40",
            ),
            rx.cond(
                node["is_parallel"],
                rx.el.span(
                    "En parallèle",
                    class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-1.5 py-0.5 text-[9px] font-bold text-amber-200 w-fit ml-auto",
                ),
                rx.icon(
                    "arrow-down-right",
                    class_name="h-3 w-3 text-emerald-100/30 ml-auto",
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
                    class_name="text-sm font-semibold text-emerald-50 text-left",
                ),
                rx.el.p(
                    node["route_label"],
                    class_name="text-[10px] font-medium text-emerald-100/45 text-left mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-center gap-3 w-full mt-3",
        ),
        on_click=GuideState.select_relation(node["key"]),
        key=key,
        class_name=rx.cond(
            GuideState.active_relation == node["key"],
            "w-full rounded-2xl border border-lime-300/45 bg-lime-300/[0.09] p-4 text-left ring-2 ring-lime-300/30 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 hover:bg-white/[0.06] transition-all",
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
                    class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-lime-300/80",
                ),
                rx.el.h3(
                    GuideState.active_relation_node["label"],
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.a(
                rx.el.span(GuideState.active_relation_node["route_label"]),
                rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                href=GuideState.active_relation_node["route"],
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-4 py-2 text-[11px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Lecture agricole",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-lime-300/70",
                ),
                rx.el.p(
                    GuideState.active_relation_node["summary_farmer"],
                    class_name="text-[12px] font-medium text-emerald-100/70 leading-relaxed mt-1",
                ),
                class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            rx.el.div(
                rx.el.span(
                    "Lecture AgriPro",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-amber-300/70",
                ),
                rx.el.p(
                    GuideState.active_relation_node["summary_pro"],
                    class_name="text-[12px] font-medium text-emerald-100/70 leading-relaxed mt-1",
                ),
                class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "arrow-down-to-line",
                        class_name="h-3 w-3 text-emerald-100/45",
                    ),
                    rx.el.span(
                        "Ce qui alimente",
                        class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.active_relation_node["inputs"], _chip
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.02] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "arrow-up-from-line",
                        class_name="h-3 w-3 text-emerald-100/45",
                    ),
                    rx.el.span(
                        "Ce qui en découle",
                        class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.active_relation_node["outputs"], _chip
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.02] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("gauge", class_name="h-3 w-3 text-emerald-100/45"),
                    rx.el.span(
                        "Indicateurs suivis",
                        class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.active_relation_node["metrics"], _chip
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.02] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-3",
        ),
        rx.el.button(
            rx.icon("book-open", class_name="h-3.5 w-3.5"),
            rx.el.span("Lire la catégorie du guide associée"),
            on_click=GuideState.select_category(
                GuideState.active_relation_node["category_key"]
            ),
            class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[11px] font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit mt-4",
        ),
        class_name="w-full rounded-3xl border border-lime-300/20 bg-[#04140d]/70 p-5 mt-5",
    )


def guide_relations() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Carte de connaissances vivante",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Relations des données de l'exploitation",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Exploitation → parcelle → culture → campagne → intervention → intrants / main d'œuvre / matériel → coût → récolte → rendement → vente → résultat.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 max-w-3xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{GuideState.relation_chain.length()} maillons cliquables",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
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
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
