import reflex as rx

from app.states.guide_state import GuideState, RuleCard

_FILTERS: list[tuple[str, str, str]] = [
    ("TOUS", "Toutes", "layers"),
    ("POURQUOI", "Pourquoi ?", "circle-help"),
    ("ATTENTION", "Attention", "triangle-alert"),
    ("COHERENCE", "Cohérence", "scale"),
    ("BONNE_PRATIQUE", "Bonnes pratiques", "sparkles"),
]


def _filter_chip(item: tuple[str, str, str]) -> rx.Component:
    return rx.el.button(
        rx.icon(item[2], class_name="h-3.5 w-3.5"),
        rx.el.span(item[1]),
        on_click=GuideState.set_rule_filter(item[0]),
        class_name=rx.cond(
            GuideState.rule_filter == item[0],
            "flex items-center gap-2 rounded-none border border-[#d8fa5e]/45 bg-[#d8fa5e]/15 px-3 py-1.5 text-xs font-semibold text-[#efffc4] transition-colors w-fit",
            "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 text-xs font-medium text-[#c9c5b4]/60 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
        ),
    )


def _tone_accent(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("bad", "h-1 w-full rounded-none bg-[#ff6b5a]/80"),
        ("warn", "h-1 w-full rounded-none bg-[#ff8a5b]/80"),
        "h-1 w-full rounded-none bg-[#d8fa5e]/80",
    )


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "bad",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10",
        ),
        (
            "warn",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10",
        ),
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10",
    )


def _tone_icon(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("bad", "h-4 w-4 text-[#ff9b8c]"),
        ("warn", "h-4 w-4 text-[#ff8a5b]"),
        "h-4 w-4 text-[#d8fa5e]",
    )


def _block(title: str, body: rx.Var, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3 w-3 text-[#c9c5b4]/45"),
            rx.el.span(
                title,
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.p(
            body,
            class_name="text-[12px] font-medium text-[#c9c5b4]/70 leading-relaxed mt-1",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
    )


def _rule_card(rule: RuleCard, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(class_name=_tone_accent(rule["tone"])),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    rx.cond(
                        rule["kind"] == "POURQUOI",
                        "circle-help",
                        rx.cond(
                            rule["kind"] == "ATTENTION",
                            "triangle-alert",
                            "scale",
                        ),
                    ),
                    class_name=_tone_icon(rule["tone"]),
                ),
                class_name=_tone_ring(rule["tone"]),
            ),
            rx.el.div(
                rx.el.p(
                    rule["title"],
                    class_name="text-sm font-semibold text-[#f2efe4]",
                ),
                rx.el.div(
                    rx.el.span(
                        rule["kind_label"],
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
                    ),
                    rx.el.span(
                        rule["severity_label"],
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
                    ),
                    rx.cond(
                        rule["is_blocking"],
                        rx.el.span(
                            "Bloquante",
                            class_name="rounded-none border border-[#ff6b5a]/35 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffbcb0] w-fit",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rule["code"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-mono text-[#c9c5b4]/45 w-fit whitespace-nowrap",
            ),
            class_name="flex items-start gap-3 w-full mt-4",
        ),
        rx.el.p(
            rule["statement"],
            class_name="text-[13px] font-semibold text-[#f2efe4]/90 leading-relaxed mt-3",
        ),
        rx.el.div(
            _block("Pourquoi", rule["rationale"], "circle-help"),
            _block("Conséquence", rule["consequence"], "octagon-alert"),
            _block("Correction", rule["remediation"], "wrench"),
            class_name="grid grid-cols-1 lg:grid-cols-3 gap-2 w-full mt-3",
        ),
        rx.el.div(
            rx.cond(
                rule["field_reference"] != "",
                rx.el.span(
                    rule["field_reference"],
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-mono text-[#c9c5b4]/50 w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                rule["module_route"] != "",
                rx.el.a(
                    rx.el.span("Ouvrir l'écran concerné"),
                    rx.icon("arrow-up-right", class_name="h-3 w-3"),
                    href=rule["module_route"],
                    class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-3 py-1 text-[10px] font-semibold text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def guide_rules() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Garde-fous éditoriaux",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Pourquoi ? & Attention",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    f"Périmètre : {GuideState.category_label}",
                    class_name="ap-eyebrow text-[#c9c5b4]/40 mt-2",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{GuideState.why_rules.length()} « Pourquoi ? »",
                    class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-3 py-1 text-[11px] font-semibold text-[#e4ff9b] w-fit",
                ),
                rx.el.span(
                    f"{GuideState.warning_rules.length()} « Attention »",
                    class_name="rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-3 py-1 text-[11px] font-semibold text-[#ffb894] w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            *[_filter_chip(item) for item in _FILTERS],
            class_name="flex flex-wrap items-center gap-2 w-full mt-5",
        ),
        rx.cond(
            GuideState.visible_rules.length() > 0,
            rx.el.div(
                rx.foreach(
                    GuideState.visible_rules,
                    lambda rule: _rule_card(rule, key=rule["code"]),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-[#d8fa5e]"),
                rx.el.p(
                    "Aucune règle pour ce périmètre.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 w-full mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
