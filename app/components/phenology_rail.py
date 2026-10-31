"""Rail visuel du cycle phénologique : centerpiece métier du suivi."""

import reflex as rx

from app.states.phenology_state import PhenologyState, StageRail


def _dot(stage: StageRail) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name=rx.match(
                stage["state"],
                ("done", "h-2.5 w-2.5 rounded-none bg-[#8fb37a]"),
                (
                    "current",
                    "h-3.5 w-3.5 rounded-none bg-[#d8fa5e] ring-4 ring-[#d8fa5e]/25",
                ),
                "h-2.5 w-2.5 rounded-none bg-[#262b1e]",
            ),
        ),
        class_name="flex items-center justify-center h-4",
    )


def _stage_card(stage: StageRail) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": stage["color"]},
        ),
        rx.el.div(
            rx.icon(stage["icon"], class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
            rx.el.span(
                stage["name"],
                class_name="text-[11px] font-semibold text-[#f2efe4] truncate",
            ),
            rx.cond(
                stage["is_critical"],
                rx.el.span(
                    "Critique",
                    class_name="rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#ffb894] w-fit ml-auto shrink-0",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-1.5 mt-2 min-w-0",
        ),
        rx.cond(
            stage["bbch"] != "",
            rx.el.p(
                stage["bbch"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 mt-1",
            ),
            rx.fragment(),
        ),
        rx.el.p(
            stage["duration"],
            class_name="text-[10px] font-medium text-[#c9c5b4]/45 mt-1",
        ),
        rx.cond(
            stage["recognition"] != "",
            rx.el.p(
                stage["recognition"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/55 mt-2 leading-relaxed",
            ),
            rx.fragment(),
        ),
        rx.cond(
            stage["watchpoints"] != "",
            rx.el.div(
                rx.icon("eye", class_name="h-3 w-3 shrink-0 text-[#ff8a5b]/80"),
                rx.el.span(
                    stage["watchpoints"],
                    class_name="text-[10px] font-medium text-[#ffdccb]/60 leading-relaxed",
                ),
                class_name="flex items-start gap-1.5 mt-2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            stage["common_errors"] != "",
            rx.el.div(
                rx.icon(
                    "circle-alert",
                    class_name="h-3 w-3 shrink-0 text-[#ff9b8c]/80",
                ),
                rx.el.span(
                    stage["common_errors"],
                    class_name="text-[10px] font-medium text-[#ffe0da]/55 leading-relaxed",
                ),
                class_name="flex items-start gap-1.5 mt-2",
            ),
            rx.fragment(),
        ),
        class_name=rx.match(
            stage["state"],
            (
                "current",
                "w-[13rem] shrink-0 rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-3 ring-2 ring-[#d8fa5e]/25",
            ),
            (
                "done",
                "w-[13rem] shrink-0 rounded-none border border-[#8fb37a]/25 bg-[#14160f] p-3",
            ),
            "w-[13rem] shrink-0 rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-3 opacity-70",
        ),
    )


def _rail_column(stage: StageRail) -> rx.Component:
    return rx.el.div(
        _dot(stage),
        _stage_card(stage),
        class_name="flex flex-col items-center gap-2 shrink-0",
    )


def phenology_rail() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Rail phénologique",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.span(
                f"{PhenologyState.summary['stages_done']} / {PhenologyState.summary['stage_count']} stades réalisés · {PhenologyState.summary['progress_pct']}",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                style={"width": PhenologyState.summary["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute left-0 right-0 top-[7px] h-px bg-gradient-to-r from-[#8fb37a]/40 via-[#d8fa5e]/30 to-[#20241a]",
            ),
            rx.el.div(
                rx.foreach(
                    PhenologyState.stages,
                    lambda stage: _rail_column(stage),
                ),
                class_name="relative flex items-start gap-3 w-max",
            ),
            class_name="relative w-full overflow-x-auto pb-2 mt-4",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )
