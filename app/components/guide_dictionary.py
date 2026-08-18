import reflex as rx

from app.states.guide_state import GuideState, TermCard


def _term_button(term: TermCard, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.span(
                term["term"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.cond(
                term["acronym"] != "",
                rx.el.span(
                    term["acronym"],
                    class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            term["definition_farmer"],
            class_name="text-[11px] font-medium text-emerald-100/50 text-left mt-1 line-clamp-2",
        ),
        on_click=GuideState.select_term(term["slug"]),
        key=key,
        class_name=rx.cond(
            GuideState.active_term["slug"] == term["slug"],
            "w-full rounded-xl border border-lime-300/40 bg-lime-300/[0.07] px-3 py-2.5 text-left transition-all",
            "w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2.5 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def _detail_block(title: str, body: rx.Var, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                title,
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            body,
            class_name="text-sm font-medium text-emerald-100/70 leading-relaxed mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def guide_dictionary() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Dictionnaire interactif",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Le mot juste, dans les deux langues",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{GuideState.visible_terms.length()} entrée(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search",
                        class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
                    ),
                    rx.el.input(
                        placeholder="Filtrer le dictionnaire…",
                        default_value=GuideState.term_query,
                        on_change=GuideState.set_term_query.debounce(300),
                        class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
                    ),
                    class_name="relative w-full",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.visible_terms,
                        lambda t: _term_button(t, key=t["slug"]),
                    ),
                    class_name="flex flex-col gap-2 w-full mt-3 max-h-[34rem] overflow-y-auto pr-1",
                ),
                class_name="w-full xl:w-[22rem] shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        GuideState.active_term["term"],
                        class_name="font-['Instrument_Serif'] text-3xl text-emerald-50",
                    ),
                    rx.cond(
                        GuideState.active_term["acronym"] != "",
                        rx.el.span(
                            GuideState.active_term["acronym"],
                            class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2.5 py-1 text-[11px] font-bold text-lime-200 w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        GuideState.active_term["unit"] != "",
                        rx.el.span(
                            GuideState.active_term["unit"],
                            class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-3 w-full",
                ),
                rx.el.div(
                    _detail_block(
                        "Lecture agricole",
                        GuideState.active_term["definition_farmer"],
                        "tractor",
                    ),
                    _detail_block(
                        "Lecture AgriPro",
                        GuideState.active_term["definition_pro"],
                        "database",
                    ),
                    class_name="grid grid-cols-1 lg:grid-cols-2 gap-3 w-full mt-4",
                ),
                rx.cond(
                    GuideState.active_term["formula"] != "",
                    rx.el.div(
                        rx.icon(
                            "sigma", class_name="h-3.5 w-3.5 text-amber-300"
                        ),
                        rx.el.span(
                            GuideState.active_term["formula"],
                            class_name="text-sm font-mono text-amber-100/90",
                        ),
                        class_name="flex items-center gap-2 rounded-2xl border border-amber-300/25 bg-amber-300/[0.07] px-4 py-3 w-full mt-3",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    GuideState.active_term["example"] != "",
                    rx.el.div(
                        rx.icon(
                            "lightbulb",
                            class_name="h-3.5 w-3.5 text-lime-300 shrink-0",
                        ),
                        rx.el.p(
                            GuideState.active_term["example"],
                            class_name="text-[12px] font-medium text-emerald-100/65",
                        ),
                        class_name="flex items-start gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 w-full mt-3",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    GuideState.active_term["module_route"] != "",
                    rx.el.a(
                        rx.el.span("Voir dans l'application"),
                        rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                        href=GuideState.active_term["module_route"],
                        class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-4 py-2 text-[11px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit mt-4",
                    ),
                    rx.fragment(),
                ),
                class_name="flex-1 min-w-0 rounded-2xl border border-white/10 bg-white/[0.02] p-5",
            ),
            class_name="flex flex-col xl:flex-row gap-4 w-full mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
