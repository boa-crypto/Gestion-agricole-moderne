"""Registre des versions éditoriales et changelog du Guide Agricole."""

import reflex as rx

from app.states.guide_admin_state import (
    ChangelogRow,
    GuideAdminState,
    VersionRow,
)

_INPUT = (
    "w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-ink-rgb))] px-3 py-2.5 text-sm "
    "font-medium text-[rgb(var(--ap-paper-rgb))] placeholder:text-[rgb(var(--ap-paper-muted-rgb)/0.82)] "
    "focus:border-[rgb(var(--ap-accent-rgb)/0.50)] focus:ring-2 focus:ring-[rgb(var(--ap-accent-rgb)/0.20)] "
    "outline-hidden transition-colors"
)


def status_badge(label: rx.Var, tone: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.35)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2.5 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.35)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2.5 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.35)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2.5 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-warm-150-rgb))] w-fit",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.21)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
        ),
    )


def _version_card(item: VersionRow, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            class_name=rx.cond(
                item["is_current"],
                "h-1 w-full rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                "h-1 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))]",
            )
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    item["version_label"],
                    class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))]",
                ),
                status_badge(item["status_label"], item["tone"]),
                rx.cond(
                    item["is_current"],
                    rx.el.span(
                        "Version courante",
                        class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb)/0.15)] px-2.5 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-pale-rgb))] w-fit",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2 w-full",
            ),
            rx.el.p(
                item["title"],
                class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-2",
            ),
            rx.el.p(
                item["summary"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] leading-relaxed mt-1.5 line-clamp-3",
            ),
            rx.el.div(
                rx.el.span(
                    f"Publiée le {item['published_label']}",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
                ),
                rx.el.span(
                    f"{item['entry_count']} entrée(s) de changelog",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
                ),
                rx.cond(
                    item["author"] != "",
                    rx.el.span(
                        item["author"],
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("history", class_name="h-3.5 w-3.5"),
                    rx.el.span("Changelog"),
                    on_click=GuideAdminState.select_version(item["id"]),
                    class_name=rx.cond(
                        GuideAdminState.selected_version_id == item["id"],
                        "flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.45)] bg-[rgb(var(--ap-accent-rgb)/0.15)] px-3 py-1.5 text-[11px] font-semibold text-[rgb(var(--ap-accent-pale-rgb))] transition-colors w-fit",
                        "flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1.5 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit",
                    ),
                ),
                rx.cond(
                    item["is_current"],
                    rx.el.button(
                        rx.icon("eye-off", class_name="h-3.5 w-3.5"),
                        rx.el.span("Dépublier"),
                        on_click=GuideAdminState.unpublish_version(item["id"]),
                        class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-3 py-1.5 text-[11px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] hover:bg-[rgb(var(--ap-flame-soft-rgb)/0.20)] transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon(
                            "badge-check",
                            class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-ink-rgb))]",
                        ),
                        rx.el.span("Publier", class_name="text-[rgb(var(--ap-ink-rgb))]"),
                        on_click=GuideAdminState.publish_version(item["id"]),
                        class_name="flex items-center gap-1.5 rounded-none bg-[rgb(var(--ap-accent-rgb))] px-3 py-1.5 text-[11px] font-semibold hover:bg-[rgb(var(--ap-accent-soft-rgb))] transition-colors w-fit",
                    ),
                ),
                rx.cond(
                    item["status"] != "ARCHIVE",
                    rx.el.button(
                        rx.icon("archive", class_name="h-3.5 w-3.5"),
                        rx.el.span("Archiver"),
                        on_click=GuideAdminState.archive_version(item["id"]),
                        class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1.5 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] hover:text-[rgb(var(--ap-warm-150-rgb))] hover:border-[rgb(var(--ap-danger-rgb)/0.30)] transition-colors w-fit ml-auto",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2 w-full mt-4 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
            ),
            class_name="w-full",
        ),
        key=key,
        class_name=rx.cond(
            item["is_current"],
            "w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.35)] bg-[rgb(var(--ap-accent-rgb))]/[0.05] p-4",
            "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-colors",
        ),
    )


def _changelog_row(item: ChangelogRow, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.span(
                item["position"],
                class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))]",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        item["change_label"],
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
                    ),
                    rx.el.span(
                        item["entity_type"],
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
                    ),
                    rx.el.span(
                        item["entity_ref"],
                        class_name="text-[9px] font-mono text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 w-full",
                ),
                rx.el.p(
                    item["summary"],
                    class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] leading-relaxed mt-1.5",
                ),
                rx.cond(
                    item["author"] != "",
                    rx.el.span(
                        item["author"],
                        class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1",
                    ),
                    rx.fragment(),
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
    )


def _version_form() -> rx.Component:
    return rx.cond(
        GuideAdminState.version_form_open,
        rx.el.form(
            rx.el.div(
                rx.el.label(
                    rx.el.span(
                        "Numéro de version",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    rx.el.input(
                        name="version_label",
                        default_value=GuideAdminState.next_version_suggestion,
                        key=GuideAdminState.next_version_suggestion,
                        placeholder="1.1.0",
                        class_name=f"{_INPUT} mt-1.5",
                    ),
                    class_name="flex flex-col w-full",
                ),
                rx.el.label(
                    rx.el.span(
                        "Titre de publication",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    rx.el.input(
                        name="title",
                        placeholder="Guide Agricole — campagne suivante",
                        class_name=f"{_INPUT} mt-1.5",
                    ),
                    class_name="flex flex-col w-full",
                ),
                rx.el.label(
                    rx.el.span(
                        "Auteur",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    rx.el.input(
                        name="author",
                        default_value="Cellule agronomique",
                        class_name=f"{_INPUT} mt-1.5",
                    ),
                    class_name="flex flex-col w-full",
                ),
                class_name="grid grid-cols-1 md:grid-cols-3 gap-3 w-full",
            ),
            rx.el.label(
                rx.el.span(
                    "Résumé de la version",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.textarea(
                    name="summary",
                    rows="3",
                    placeholder="Ce que cette version apporte au lecteur agricole et AgriPro.",
                    class_name=f"{_INPUT} mt-1.5 leading-relaxed resize-y",
                ),
                class_name="flex flex-col w-full mt-3",
            ),
            rx.el.div(
                rx.el.button(
                    rx.el.span("Annuler"),
                    type="button",
                    on_click=GuideAdminState.toggle_version_form,
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2 text-xs font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon(
                        "git-branch-plus",
                        class_name="h-4 w-4 stroke-[rgb(var(--ap-ink-rgb))]",
                    ),
                    rx.el.span(
                        "Ouvrir la version", class_name="text-[rgb(var(--ap-ink-rgb))]"
                    ),
                    type="submit",
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[rgb(var(--ap-accent-rgb))] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[rgb(var(--ap-ink-rgb))] transition-colors hover:bg-[rgb(var(--ap-accent-soft-rgb))]",
                ),
                class_name="flex flex-wrap items-center justify-end gap-2 w-full mt-3",
            ),
            on_submit=GuideAdminState.create_version,
            reset_on_submit=True,
            class_name="w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-ink-rgb)/0.70)] p-4 mt-4",
        ),
        rx.fragment(),
    )


def guide_admin_versions() -> rx.Component:
    """Registre des versions publiées, publication et changelog."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre des publications",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Versions consultables du guide",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    f"Version courante : {GuideAdminState.current_version['version_label']} · {GuideAdminState.current_version['status_label']}",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("git-branch-plus", class_name="h-3.5 w-3.5"),
                rx.el.span("Nouvelle version"),
                on_click=GuideAdminState.toggle_version_form,
                class_name=rx.cond(
                    GuideAdminState.version_form_open,
                    "flex items-center gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.45)] bg-[rgb(var(--ap-accent-rgb)/0.15)] px-4 py-2 text-xs font-semibold text-[rgb(var(--ap-accent-pale-rgb))] transition-colors w-fit",
                    "flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-2 text-xs font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit",
                ),
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        _version_form(),
        rx.el.div(
            rx.el.div(
                rx.foreach(
                    GuideAdminState.versions,
                    lambda item: _version_card(
                        item, key=item["id"].to_string()
                    ),
                ),
                class_name="flex flex-col gap-3 w-full xl:w-[30rem] shrink-0 max-h-[36rem] overflow-y-auto pr-1",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("history", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                    rx.el.div(
                        rx.el.span(
                            "Historique éditorial",
                            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                        ),
                        rx.el.h3(
                            f"{GuideAdminState.selected_version['version_label']} · {GuideAdminState.selected_version['title']}",
                            class_name="ap-serif text-xl text-[rgb(var(--ap-paper-rgb))] mt-0.5",
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    rx.el.span(
                        f"{GuideAdminState.changelog.length()} entrée(s)",
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
                    ),
                    class_name="flex items-start gap-2.5 w-full",
                ),
                rx.cond(
                    GuideAdminState.changelog.length() > 0,
                    rx.el.ol(
                        rx.foreach(
                            GuideAdminState.changelog,
                            lambda item: _changelog_row(
                                item, key=item["id"].to_string()
                            ),
                        ),
                        class_name="flex flex-col gap-2 w-full mt-4 max-h-[30rem] overflow-y-auto pr-1",
                    ),
                    rx.el.div(
                        rx.icon(
                            "file-clock", class_name="h-6 w-6 text-[rgb(var(--ap-flame-soft-rgb))]"
                        ),
                        rx.el.p(
                            "Aucune entrée de changelog sur cette version.",
                            class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 text-center",
                        ),
                        class_name="flex flex-col items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-12 w-full mt-4",
                    ),
                ),
                class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.12)] flex-1 min-w-0 pt-5",
            ),
            class_name="flex flex-col xl:flex-row gap-4 w-full mt-5",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )
