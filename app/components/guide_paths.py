import reflex as rx

from app.states.guide_state import GuideState, PathCard, PathStep


def _path_card(path: PathCard, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-full",
            style={"backgroundColor": path["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(path["icon"], class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
            ),
            rx.el.div(
                rx.el.p(
                    path["title"],
                    class_name="text-sm font-semibold text-emerald-50 text-left",
                ),
                rx.el.p(
                    path["subtitle"],
                    class_name="text-[11px] font-medium text-emerald-100/50 text-left mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full mt-3",
        ),
        rx.el.p(
            path["objective"],
            class_name="text-[11px] font-medium text-emerald-100/55 text-left leading-relaxed mt-3",
        ),
        rx.el.div(
            rx.el.span(
                path["audience_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                path["difficulty_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{path['step_count']} étape(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{path['estimated_minutes']} min",
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        on_click=GuideState.select_path(path["slug"]),
        key=key,
        class_name=rx.cond(
            GuideState.active_path_slug == path["slug"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/30 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def _path_step(step: PathStep, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.span(
                step["position"],
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-lime-300/30 bg-lime-300/10 text-[11px] font-bold text-lime-200",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        step["title"],
                        class_name="text-sm font-semibold text-emerald-50",
                    ),
                    rx.cond(
                        step["is_optional"],
                        rx.el.span(
                            "Optionnelle",
                            class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-semibold text-emerald-100/50 w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.span(
                        f"{step['duration_minutes']} min",
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-semibold text-emerald-100/50 w-fit ml-auto",
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full",
                ),
                rx.el.p(
                    step["description"],
                    class_name="text-[12px] font-medium text-emerald-100/65 leading-relaxed mt-2",
                ),
                rx.cond(
                    step["milestone"] != "",
                    rx.el.div(
                        rx.icon(
                            "flag",
                            class_name="h-3.5 w-3.5 text-amber-300 shrink-0",
                        ),
                        rx.el.p(
                            step["milestone"],
                            class_name="text-[11px] font-semibold text-amber-100/85",
                        ),
                        class_name="flex items-start gap-2 rounded-xl border border-amber-300/25 bg-amber-300/[0.07] px-3 py-2 w-full mt-2",
                    ),
                    rx.fragment(),
                ),
                rx.el.div(
                    rx.cond(
                        step["article_slug"] != "",
                        rx.el.button(
                            rx.icon("file-text", class_name="h-3 w-3"),
                            rx.el.span("Lire l'article"),
                            on_click=GuideState.select_article(
                                step["article_slug"]
                            ),
                            class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        step["procedure_slug"] != "",
                        rx.el.button(
                            rx.icon("list-checks", class_name="h-3 w-3"),
                            rx.el.span("Dérouler la procédure"),
                            on_click=GuideState.open_hit(
                                "procedure", step["procedure_slug"]
                            ),
                            class_name="flex items-center gap-1.5 rounded-full border border-amber-300/25 bg-amber-300/10 px-3 py-1 text-[10px] font-semibold text-amber-200 hover:bg-amber-300/20 transition-colors w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        step["module_route"] != "",
                        rx.el.a(
                            rx.el.span("Ouvrir l'écran"),
                            rx.icon("arrow-up-right", class_name="h-3 w-3"),
                            href=step["module_route"],
                            class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit ml-auto",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full mt-3",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.02] p-4",
    )


def _column(title: str, caption: str, icon: str, items: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
            ),
            rx.el.div(
                rx.el.h3(
                    title,
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                ),
                rx.el.p(
                    caption,
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(items, lambda p: _path_card(p, key=p["slug"])),
            class_name="flex flex-col gap-3 w-full mt-4",
        ),
        class_name="flex-1 min-w-0",
    )


def guide_paths() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.span(
                "Parcours guidés",
                class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
            ),
            rx.el.h2(
                "Apprendre l'agriculture, maîtriser AgriPro",
                class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
            ),
            class_name="w-full",
        ),
        rx.el.div(
            _column(
                "Apprendre l'agriculture",
                "Bases de terrain",
                "sprout",
                GuideState.farmer_paths,
            ),
            _column(
                "Maîtriser AgriPro",
                "Pilotage par la donnée",
                "monitor-cog",
                GuideState.pro_paths,
            ),
            class_name="flex flex-col xl:flex-row gap-5 w-full mt-5",
        ),
        rx.cond(
            GuideState.path_steps.length() > 0,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Progression du parcours",
                            class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                        ),
                        rx.el.h3(
                            GuideState.active_path["title"],
                            class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
                        ),
                        rx.el.p(
                            GuideState.active_path["objective"],
                            class_name="text-sm font-medium text-emerald-100/60 mt-2 max-w-2xl",
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    rx.el.span(
                        f"{GuideState.path_steps.length()} étape(s) · {GuideState.active_path['estimated_minutes']} min",
                        class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
                    ),
                    class_name="flex flex-wrap items-start justify-between gap-3 w-full",
                ),
                rx.el.ol(
                    rx.foreach(
                        GuideState.path_steps,
                        lambda s: _path_step(s, key=s["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 w-full mt-5",
                ),
                class_name="w-full rounded-3xl border border-lime-300/20 bg-[#04140d]/70 p-5 mt-5",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
