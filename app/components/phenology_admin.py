"""Pupitre d'administration du référentiel phénologique (AgriPro).

Administration → Référentiels → Cultures → Phénologie → Stades.
Interface agricole sobre : vert nuit, chlorophylle et ambre, surfaces vitrées,
badges lumineux, Instrument Serif pour les titres.
"""

import reflex as rx

from app.components.design import skeleton_page

from app.components.phenology_admin_forms import (
    phenology_admin_modals,
    phenology_export_panel,
    phenology_import_panel,
)
from app.states.phenology_admin_state import (
    CheckRow,
    PhenologyAdminState,
    ProfileAdminRow,
    RecoAdminRow,
    StageAdminRow,
)


def _badge(tone: str, label: rx.Var | str) -> rx.Component:
    tones: dict[str, str] = {
        "good": "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
        "warn": "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
        "bad": "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit",
        "info": "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit",
        "muted": "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
    }
    return rx.el.span(label, class_name=tones.get(tone, tones["muted"]))


def _stat(label: str, value: rx.Var | int, caption: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-2xl leading-none text-[rgb(var(--ap-paper-rgb))]",
            ),
            rx.el.span(
                caption,
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-3",
    )


def _header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("git-branch", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                    rx.el.span(
                        "Administration · Référentiels · Phénologie",
                        class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb))]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Cycles culturaux et stades phénologiques",
                    class_name="ap-serif text-3xl md:text-4xl text-[rgb(var(--ap-paper-rgb))] mt-2",
                ),
                rx.el.p(
                    "Chaque culture porte son propre cycle : créer, décrire, "
                    "réordonner, désactiver — sans jamais supprimer une donnée "
                    "existante ni transformer une information générale en "
                    "prescription agronomique.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2 max-w-3xl",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        PhenologyAdminState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin stroke-[rgb(var(--ap-paper-muted-rgb)/0.70)]",
                        ),
                        rx.icon(
                            "refresh-cw",
                            class_name="h-4 w-4 stroke-[rgb(var(--ap-paper-muted-rgb)/0.70)]",
                        ),
                    ),
                    rx.el.span("Recharger"),
                    on_click=PhenologyAdminState.load_admin,
                    class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2 text-xs font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4 stroke-[rgb(var(--ap-ink-rgb))]"),
                    rx.el.span("Nouveau profil", class_name="text-[rgb(var(--ap-ink-rgb))]"),
                    on_click=PhenologyAdminState.open_profile_create,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[rgb(var(--ap-accent-rgb))] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[rgb(var(--ap-ink-rgb))] transition-colors hover:bg-[rgb(var(--ap-accent-soft-rgb))]",
                ),
                class_name="flex flex-wrap items-start gap-2 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-start justify-between gap-5 w-full",
        ),
        rx.el.div(
            _stat(
                "Profils actifs",
                PhenologyAdminState.totals["active_profiles"],
                "cycles",
            ),
            _stat(
                "Cultures couvertes",
                PhenologyAdminState.totals["cultures"],
                "référentiels",
            ),
            _stat(
                "Stades actifs",
                PhenologyAdminState.totals["active_stages"],
                "étapes",
            ),
            _stat(
                "Stades sensibles",
                PhenologyAdminState.totals["critical_stages"],
                "à surveiller",
            ),
            _stat(
                "Informations associées",
                PhenologyAdminState.totals["advisory_recommendations"],
                "indicatives",
            ),
            _stat(
                "Changements tracés",
                PhenologyAdminState.totals["changes"],
                "historique",
            ),
            class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full mt-6",
        ),
        rx.cond(
            PhenologyAdminState.notice != "",
            rx.el.div(
                rx.icon(
                    "circle-check",
                    class_name="h-4 w-4 shrink-0 stroke-[rgb(var(--ap-accent-rgb))]",
                ),
                rx.el.p(
                    PhenologyAdminState.notice,
                    class_name="text-[12px] font-semibold text-[rgb(var(--ap-accent-pale-rgb)/0.90)]",
                ),
                class_name="flex items-center gap-2 w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb))]/[0.07] px-4 py-2.5 mt-4",
            ),
            rx.fragment(),
        ),
        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
    )


def _profile_card(profile: ProfileAdminRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.el.div(
                rx.el.span(
                    profile["culture_name"],
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)] truncate",
                ),
                rx.cond(
                    profile["is_default"],
                    _badge("info", "Par défaut"),
                    rx.fragment(),
                ),
                rx.cond(
                    profile["is_active"],
                    _badge("good", "Actif"),
                    _badge("bad", "Désactivé"),
                ),
                class_name="flex flex-wrap items-center gap-1.5 w-full",
            ),
            rx.el.p(
                profile["name"],
                class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-2 text-left",
            ),
            rx.el.p(
                profile["scope_label"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1 text-left",
            ),
            rx.el.div(
                _badge("muted", profile["system_label"]),
                _badge(
                    "muted",
                    f"{profile['active_stages']}/{profile['stage_count']} stades",
                ),
                _badge(
                    "warn",
                    f"{profile['critical_stages']} sensible(s)",
                ),
                class_name="flex flex-wrap items-center gap-1.5 mt-3",
            ),
            on_click=PhenologyAdminState.select_profile(profile["id"]),
            class_name=rx.cond(
                PhenologyAdminState.selected_profile_id == profile["id"],
                "w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.45)] bg-[rgb(var(--ap-accent-rgb))]/[0.09] p-4 text-left transition-colors",
                "w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-4 text-left hover:border-[rgb(var(--ap-accent-rgb)/0.25)] hover:bg-[rgb(var(--ap-surface-high-rgb))] transition-colors",
            ),
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    profile["is_active"],
                    rx.icon(
                        "toggle-right",
                        class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb))]",
                    ),
                    rx.icon(
                        "toggle-left",
                        class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-paper-muted-rgb)/0.50)]",
                    ),
                ),
                rx.el.span(
                    rx.cond(profile["is_active"], "Désactiver", "Réactiver"),
                    class_name="text-[10px]",
                ),
                on_click=PhenologyAdminState.toggle_profile_active(
                    profile["id"], ~profile["is_active"].to(bool)
                ),
                class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit",
            ),
            rx.el.span(
                profile["source"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] truncate",
            ),
            class_name="flex items-center gap-2 w-full px-1 mt-1.5",
        ),
        key=key,
        class_name="flex flex-col w-full",
    )


def _profiles_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.span(
                "Cycles par culture",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.span(
                f"{PhenologyAdminState.profile_count} profil(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            "Aucune liste globale de stades : chaque profil ne concerne que sa "
            "culture.",
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2",
        ),
        rx.el.div(
            rx.foreach(
                PhenologyAdminState.profiles,
                lambda profile: _profile_card(
                    profile, key=profile["id"].to_string()
                ),
            ),
            class_name="flex flex-col gap-3 w-full mt-4 max-h-[46rem] overflow-y-auto pr-1",
        ),
        class_name="w-full xl:w-[24rem] shrink-0 border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-5 xl:border-l xl:border-l-[rgb(var(--ap-paper-rgb)/0.08)] xl:pl-5",
    )


def _stage_row(stage: StageAdminRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                class_name="h-9 w-1 rounded-none shrink-0",
                style={"backgroundColor": stage["color_hex"]},
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        f"#{stage['position']}",
                        class_name="text-[10px] font-bold text-[rgb(var(--ap-accent-rgb)/0.80)]",
                    ),
                    rx.el.span(
                        stage["name"],
                        class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                    ),
                    rx.cond(
                        stage["bbch_code"] != "",
                        _badge("muted", stage["bbch_code"]),
                        rx.fragment(),
                    ),
                    rx.cond(
                        stage["is_critical"],
                        _badge("warn", "Sensible"),
                        rx.fragment(),
                    ),
                    rx.cond(
                        stage["is_active"],
                        _badge("good", "Actif"),
                        _badge("bad", "Désactivé"),
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 min-w-0",
                ),
                rx.el.p(
                    stage["description"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1.5 leading-relaxed line-clamp-2",
                ),
                rx.el.div(
                    _badge("muted", stage["duration_label"]),
                    _badge(
                        "info",
                        f"{stage['recommendation_count']} information(s)",
                    ),
                    rx.cond(
                        stage["guide_article_slug"] != "",
                        _badge(
                            "muted", f"Guide · {stage['guide_article_slug']}"
                        ),
                        _badge("muted", "Guide non relié"),
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("arrow-up", class_name="h-3.5 w-3.5"),
                on_click=PhenologyAdminState.shift_stage(stage["id"], -1),
                title="Monter dans le cycle",
                class_name="flex h-8 w-8 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors",
            ),
            rx.el.button(
                rx.icon("arrow-down", class_name="h-3.5 w-3.5"),
                on_click=PhenologyAdminState.shift_stage(stage["id"], 1),
                title="Descendre dans le cycle",
                class_name="flex h-8 w-8 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors",
            ),
            rx.el.button(
                rx.icon("triangle-alert", class_name="h-3.5 w-3.5"),
                on_click=PhenologyAdminState.toggle_stage_critical(
                    stage["id"], ~stage["is_critical"].to(bool)
                ),
                title="Marquer comme stade sensible",
                class_name=rx.cond(
                    stage["is_critical"],
                    "flex h-8 w-8 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.40)] bg-[rgb(var(--ap-flame-soft-rgb)/0.15)] text-[rgb(var(--ap-flame-tint-rgb))] transition-colors",
                    "flex h-8 w-8 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.86)] hover:text-[rgb(var(--ap-flame-tint-rgb))] hover:border-[rgb(var(--ap-flame-soft-rgb)/0.30)] transition-colors",
                ),
            ),
            rx.el.button(
                rx.cond(
                    stage["is_active"],
                    rx.icon("eye-off", class_name="h-3.5 w-3.5"),
                    rx.icon("eye", class_name="h-3.5 w-3.5"),
                ),
                on_click=PhenologyAdminState.toggle_stage_active(
                    stage["id"], ~stage["is_active"].to(bool)
                ),
                title="Activer ou désactiver (jamais de suppression)",
                class_name="flex h-8 w-8 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors",
            ),
            rx.el.button(
                rx.icon("pencil", class_name="h-3.5 w-3.5"),
                rx.el.span("Éditer", class_name="text-[11px]"),
                on_click=PhenologyAdminState.open_stage_edit(stage["id"]),
                class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1.5 font-semibold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("list-checks", class_name="h-3.5 w-3.5"),
                rx.el.span("Détail", class_name="text-[11px]"),
                on_click=PhenologyAdminState.select_stage(stage["id"]),
                class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1.5 font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 shrink-0",
        ),
        key=key,
        class_name=rx.cond(
            PhenologyAdminState.selected_stage_id == stage["id"],
            "flex flex-col lg:flex-row lg:items-center gap-3 w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb))]/[0.07] p-4",
            "flex flex-col lg:flex-row lg:items-center gap-3 w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-4 hover:border-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors",
        ),
    )


def _stages_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Stades du cycle",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    PhenologyAdminState.selected_profile["name"],
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    PhenologyAdminState.selected_profile["summary"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1.5 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("pencil", class_name="h-3.5 w-3.5"),
                    rx.el.span("Modifier le profil"),
                    on_click=PhenologyAdminState.open_profile_edit,
                    class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2 text-xs font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-ink-rgb))]"),
                    rx.el.span("Ajouter un stade", class_name="text-[rgb(var(--ap-ink-rgb))]"),
                    on_click=PhenologyAdminState.open_stage_create,
                    class_name="flex items-center gap-2 rounded-none bg-[rgb(var(--ap-accent-rgb))] px-4 py-2 text-xs font-semibold hover:bg-[rgb(var(--ap-accent-soft-rgb))] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            PhenologyAdminState.stage_count > 0,
            rx.el.div(
                rx.foreach(
                    PhenologyAdminState.stages,
                    lambda stage: _stage_row(
                        stage, key=stage["id"].to_string()
                    ),
                ),
                class_name="flex flex-col gap-3 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("sprout", class_name="h-6 w-6 stroke-[rgb(var(--ap-accent-rgb))]"),
                rx.el.p(
                    "Ce profil n'a pas encore de stade : ajoutez-les un par un "
                    "ou importez un CSV / JSON.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 text-center max-w-md",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-14 w-full mt-5",
            ),
        ),
        class_name="flex-1 min-w-0 w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
    )


def _reco_card(reco: RecoAdminRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(reco["icon"], class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb))]"),
            rx.el.span(
                reco["domain_label"],
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.cond(
                reco["is_advisory"],
                _badge("info", "Indicative"),
                _badge("bad", "À requalifier"),
            ),
            rx.el.button(
                rx.icon("pencil", class_name="h-3 w-3"),
                rx.el.span("Éditer", class_name="text-[10px]"),
                on_click=PhenologyAdminState.open_reco_edit(reco["id"]),
                class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.p(
            reco["title"],
            class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-1.5",
        ),
        rx.el.p(
            reco["statement"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-1.5 leading-relaxed",
        ),
        rx.el.div(
            _badge("muted", reco["confidence_label"]),
            rx.el.span(
                reco["source"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
        ),
        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.12)] pt-4",
    )


def _stage_detail_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Détail du stade",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    PhenologyAdminState.selected_stage["name"],
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-3.5 w-3.5"),
                rx.el.span("Ajouter une information associée"),
                on_click=PhenologyAdminState.open_reco_create,
                class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-4 py-2 text-xs font-semibold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            PhenologyAdminState.has_stage,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Définition",
                            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                        ),
                        rx.el.p(
                            PhenologyAdminState.stage_preview["description"],
                            class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] mt-1.5 leading-relaxed whitespace-pre-line",
                        ),
                        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-4",
                    ),
                    rx.el.div(
                        rx.el.span(
                            "Comment le reconnaître",
                            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                        ),
                        rx.el.p(
                            PhenologyAdminState.stage_preview["recognition"],
                            class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] mt-1.5 leading-relaxed whitespace-pre-line",
                        ),
                        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-4",
                    ),
                    rx.el.div(
                        rx.el.span(
                            "Points de surveillance",
                            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                        ),
                        rx.el.p(
                            PhenologyAdminState.stage_preview["watchpoints"],
                            class_name="text-[12px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.70)] mt-1.5 leading-relaxed whitespace-pre-line",
                        ),
                        class_name="w-full border-l-2 border-[rgb(var(--ap-flame-soft-rgb))] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.05] pl-3 pr-2 py-3",
                    ),
                    rx.el.div(
                        rx.el.span(
                            "Erreurs fréquentes",
                            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                        ),
                        rx.el.p(
                            PhenologyAdminState.stage_preview["common_errors"],
                            class_name="text-[12px] font-medium text-[rgb(var(--ap-warm-050-rgb)/0.65)] mt-1.5 leading-relaxed whitespace-pre-line",
                        ),
                        class_name="w-full border-l-2 border-[rgb(var(--ap-danger-rgb))] bg-[rgb(var(--ap-flame-strong-rgb))]/[0.05] pl-3 pr-2 py-3",
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full mt-5",
                ),
                rx.el.div(
                    _badge(
                        "muted",
                        PhenologyAdminState.stage_preview["duration_label"],
                    ),
                    _badge(
                        "muted",
                        PhenologyAdminState.stage_preview["system_label"],
                    ),
                    _badge(
                        "muted",
                        PhenologyAdminState.stage_preview["culture_name"],
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full mt-4",
                ),
                rx.cond(
                    PhenologyAdminState.recommendations.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            PhenologyAdminState.recommendations,
                            lambda reco: _reco_card(reco),
                        ),
                        class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full mt-5",
                    ),
                    rx.el.p(
                        "Aucune opération associée à ce stade : ajoutez une "
                        "information générale sourcée si elle existe.",
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
                    ),
                ),
                class_name="w-full",
            ),
            rx.el.p(
                "Sélectionnez un stade pour consulter sa définition et ses "
                "opérations associées.",
                class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
            ),
        ),
        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
    )


def _check_card(item: CheckRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.cond(
                item["ok"],
                rx.icon(
                    "circle-check",
                    class_name="h-4 w-4 shrink-0 stroke-[rgb(var(--ap-accent-rgb))]",
                ),
                rx.icon(
                    "circle-x", class_name="h-4 w-4 shrink-0 stroke-[rgb(var(--ap-danger-soft-rgb))]"
                ),
            ),
            rx.el.span(
                item["label"],
                class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            rx.cond(
                item["ok"],
                _badge("good", "Conforme"),
                _badge("bad", "Non conforme"),
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            item["expectation"],
            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2",
        ),
        rx.el.p(
            item["message"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1.5 leading-relaxed",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1.5 leading-relaxed",
        ),
        key=key,
        class_name=rx.cond(
            item["ok"],
            "w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-accent-rgb))]/[0.05] p-4",
            "w-full rounded-none border border-[rgb(var(--ap-danger-rgb)/0.25)] bg-[rgb(var(--ap-flame-strong-rgb))]/[0.07] p-4",
        ),
    )


def _checks_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Validations finales",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Cohérence stade ↔ culture et garde-fous",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Blé + Tallage accepté, Tomate + Nouaison accepté, "
                    "Olivier + Tallage refusé, historique conservé, "
                    "recommandations non prescriptives.",
                    class_name="text-xs font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.cond(
                    PhenologyAdminState.checks_passed,
                    _badge("good", "Tous les contrôles sont conformes"),
                    _badge(
                        "bad",
                        f"{PhenologyAdminState.failed_checks} contrôle(s) à corriger",
                    ),
                ),
                rx.el.button(
                    rx.icon("shield-check", class_name="h-3.5 w-3.5"),
                    rx.el.span("Relancer les contrôles"),
                    on_click=PhenologyAdminState.run_checks,
                    class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2 text-xs font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(
                PhenologyAdminState.checks,
                lambda item: _check_card(item, key=item["id"]),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-5",
        ),
        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        skeleton_page(2),
        class_name="flex flex-col gap-4 w-full",
    )


def phenology_admin() -> rx.Component:
    """Section complète d'administration du référentiel phénologique."""
    return rx.el.div(
        phenology_admin_modals(),
        rx.cond(
            PhenologyAdminState.is_loading,
            _skeleton(),
            rx.el.div(
                _header(),
                rx.el.div(
                    _profiles_panel(),
                    _stages_panel(),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                _stage_detail_panel(),
                rx.el.div(
                    rx.el.div(
                        phenology_import_panel(),
                        class_name="flex-1 min-w-0",
                    ),
                    rx.el.div(
                        phenology_export_panel(),
                        class_name="flex-1 min-w-0",
                    ),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                _checks_panel(),
                class_name="flex flex-col gap-4 w-full",
            ),
        ),
        class_name="w-full",
    )
