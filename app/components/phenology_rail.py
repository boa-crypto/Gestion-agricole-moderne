"""Rail visuel du cycle phénologique : centerpiece métier du suivi."""

import reflex as rx

from app.states.phenology_state import PhenologyState, StageRail


def _dot(stage: StageRail) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name=rx.match(
                stage["state"],
                ("done", "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-sage-soft-rgb))]"),
                (
                    "current",
                    "h-3.5 w-3.5 rounded-none bg-[rgb(var(--ap-accent-rgb))] ring-4 ring-[rgb(var(--ap-accent-rgb)/0.25)]",
                ),
                "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-track-soft-rgb))]",
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
            rx.icon(stage["icon"], class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
            rx.el.span(
                stage["name"],
                class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            rx.cond(
                stage["is_critical"],
                rx.el.span(
                    "Critique",
                    class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit ml-auto shrink-0",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-1.5 mt-2 min-w-0",
        ),
        rx.cond(
            stage["bbch"] != "",
            rx.el.p(
                stage["bbch"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1",
            ),
            rx.fragment(),
        ),
        rx.el.p(
            stage["duration"],
            class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1",
        ),
        rx.cond(
            stage["recognition"] != "",
            rx.el.p(
                stage["recognition"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 leading-relaxed",
            ),
            rx.fragment(),
        ),
        rx.cond(
            stage["watchpoints"] != "",
            rx.el.div(
                rx.icon("eye", class_name="h-3 w-3 shrink-0 text-[rgb(var(--ap-flame-soft-rgb)/0.80)]"),
                rx.el.span(
                    stage["watchpoints"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.60)] leading-relaxed",
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
                    class_name="h-3 w-3 shrink-0 text-[rgb(var(--ap-danger-soft-rgb)/0.80)]",
                ),
                rx.el.span(
                    stage["common_errors"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-warm-050-rgb)/0.55)] leading-relaxed",
                ),
                class_name="flex items-start gap-1.5 mt-2",
            ),
            rx.fragment(),
        ),
        class_name=rx.match(
            stage["state"],
            (
                "current",
                "w-[13rem] shrink-0 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb))]/[0.07] p-3 ring-2 ring-[rgb(var(--ap-accent-rgb)/0.25)]",
            ),
            (
                "done",
                "w-[13rem] shrink-0 rounded-none border border-[rgb(var(--ap-sage-soft-rgb)/0.25)] bg-[rgb(var(--ap-surface-raised-rgb))] p-3",
            ),
            "w-[13rem] shrink-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-3 opacity-70",
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
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.span(
                f"{PhenologyState.summary['stages_done']} / {PhenologyState.summary['stage_count']} stades réalisés · {PhenologyState.summary['progress_pct']}",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                style={"width": PhenologyState.summary["progress_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))] mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute left-0 right-0 top-[7px] h-px bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb)/0.40)] via-[rgb(var(--ap-accent-rgb)/0.30)] to-[rgb(var(--ap-surface-control-rgb))]",
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
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4",
    )
