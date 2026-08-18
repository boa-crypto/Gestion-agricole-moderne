"""Compteurs phénologiques et incohérences de stade pour l'audit fonctionnel."""

import reflex as rx

from app.states.phenology_ops_state import IncoherenceRow, PhenologyOpsState


def _counter(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300"),
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-4",
    )


def _issue(item: IncoherenceRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "octagon-alert", class_name="h-4 w-4 text-red-300 shrink-0"
            ),
            rx.el.span(
                f"{item['parcel_code']} · {item['crop_name']}",
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.el.span(
                item["date_label"],
                class_name="text-[10px] font-medium text-emerald-100/45 ml-auto shrink-0",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            item["reason"],
            class_name="text-[11px] font-medium text-red-100/70 mt-1.5 leading-relaxed",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-red-400/25 bg-red-500/[0.06] p-4",
    )


def phenology_audit_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Audit phénologique",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Couverture du suivi des stades",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{PhenologyOpsState.incoherence_count} incohérence(s) de stade",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.el.div(
            _counter(
                "Profils actifs",
                PhenologyOpsState.counters["active_profiles"],
                "git-branch",
            ),
            _counter(
                "Stades actifs",
                PhenologyOpsState.counters["active_stages"],
                "sprout",
            ),
            _counter(
                "Stades sensibles",
                PhenologyOpsState.counters["critical_stages"],
                "triangle-alert",
            ),
            _counter(
                "Observations",
                PhenologyOpsState.counters["observations"],
                "clipboard-pen",
            ),
            _counter(
                "Changements tracés",
                PhenologyOpsState.counters["changes"],
                "history",
            ),
            _counter(
                "Recommandations indicatives",
                PhenologyOpsState.counters["advisory_recommendations"],
                "list-checks",
            ),
            _counter(
                "Cultures sans profil",
                PhenologyOpsState.counters["cultures_without_profile"],
                "circle-slash",
            ),
            _counter(
                "Cultures sans observation",
                PhenologyOpsState.counters["crops_without_observation"],
                "eye-off",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5",
        ),
        rx.el.div(
            rx.el.span(
                "Incohérences détectées",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.cond(
                PhenologyOpsState.incoherences.length() > 0,
                rx.el.div(
                    rx.foreach(
                        PhenologyOpsState.incoherences,
                        lambda item: _issue(item, key=item["id"]),
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3",
                ),
                rx.el.p(
                    "Aucune observation incohérente : chaque stade appartient au profil de sa culture.",
                    class_name="text-[11px] font-medium text-emerald-100/50 mt-3",
                ),
            ),
            class_name="mt-8 border-t border-white/10 pt-6",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
