"""Registre des versions éditoriales et changelog du Guide Agricole."""

import reflex as rx

from app.states.guide_admin_state import (
    ChangelogRow,
    GuideAdminState,
    VersionRow,
)

_INPUT = (
    "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm "
    "font-medium text-emerald-50 placeholder:text-emerald-100/25 "
    "focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 "
    "outline-hidden transition-colors"
)


def status_badge(label: rx.Var, tone: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/35 bg-lime-300/10 px-2.5 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/35 bg-amber-300/10 px-2.5 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
            ),
            (
                "bad",
                "rounded-full border border-red-400/35 bg-red-500/10 px-2.5 py-0.5 text-[10px] font-bold text-red-200 w-fit",
            ),
            "rounded-full border border-white/12 bg-white/5 px-2.5 py-0.5 text-[10px] font-bold text-emerald-100/60 w-fit",
        ),
    )


def _version_card(item: VersionRow, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            class_name=rx.cond(
                item["is_current"],
                "h-1 w-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                "h-1 w-full rounded-full bg-white/10",
            )
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    item["version_label"],
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                ),
                status_badge(item["status_label"], item["tone"]),
                rx.cond(
                    item["is_current"],
                    rx.el.span(
                        "Version courante",
                        class_name="rounded-full border border-lime-300/40 bg-lime-300/15 px-2.5 py-0.5 text-[10px] font-bold text-lime-100 w-fit",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2 w-full",
            ),
            rx.el.p(
                item["title"],
                class_name="text-sm font-semibold text-emerald-50 mt-2",
            ),
            rx.el.p(
                item["summary"],
                class_name="text-[11px] font-medium text-emerald-100/55 leading-relaxed mt-1.5 line-clamp-3",
            ),
            rx.el.div(
                rx.el.span(
                    f"Publiée le {item['published_label']}",
                    class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/55 w-fit",
                ),
                rx.el.span(
                    f"{item['entry_count']} entrée(s) de changelog",
                    class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/55 w-fit",
                ),
                rx.cond(
                    item["author"] != "",
                    rx.el.span(
                        item["author"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/55 w-fit",
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
                        "flex items-center gap-1.5 rounded-full border border-lime-300/45 bg-lime-300/15 px-3 py-1.5 text-[11px] font-semibold text-lime-100 transition-colors w-fit",
                        "flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                    ),
                ),
                rx.cond(
                    item["is_current"],
                    rx.el.button(
                        rx.icon("eye-off", class_name="h-3.5 w-3.5"),
                        rx.el.span("Dépublier"),
                        on_click=GuideAdminState.unpublish_version(item["id"]),
                        class_name="flex items-center gap-1.5 rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1.5 text-[11px] font-semibold text-amber-200 hover:bg-amber-300/20 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon(
                            "badge-check",
                            class_name="h-3.5 w-3.5 stroke-[#04140d]",
                        ),
                        rx.el.span("Publier", class_name="text-[#04140d]"),
                        on_click=GuideAdminState.publish_version(item["id"]),
                        class_name="flex items-center gap-1.5 rounded-full bg-lime-300 px-3 py-1.5 text-[11px] font-semibold hover:bg-lime-200 transition-colors w-fit",
                    ),
                ),
                rx.cond(
                    item["status"] != "ARCHIVE",
                    rx.el.button(
                        rx.icon("archive", class_name="h-3.5 w-3.5"),
                        rx.el.span("Archiver"),
                        on_click=GuideAdminState.archive_version(item["id"]),
                        class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-emerald-100/55 hover:text-red-200 hover:border-red-400/30 transition-colors w-fit ml-auto",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2 w-full mt-4 pt-3 border-t border-white/5",
            ),
            class_name="w-full",
        ),
        key=key,
        class_name=rx.cond(
            item["is_current"],
            "w-full rounded-2xl border border-lime-300/35 bg-lime-300/[0.05] p-4",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
        ),
    )


def _changelog_row(item: ChangelogRow, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.span(
                item["position"],
                class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-lime-300/25 bg-lime-300/10 text-[10px] font-bold text-lime-200",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        item["change_label"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-bold text-emerald-100/65 w-fit",
                    ),
                    rx.el.span(
                        item["entity_type"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-semibold text-emerald-100/50 w-fit",
                    ),
                    rx.el.span(
                        item["entity_ref"],
                        class_name="text-[9px] font-mono text-emerald-100/40 truncate",
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 w-full",
                ),
                rx.el.p(
                    item["summary"],
                    class_name="text-[12px] font-medium text-emerald-100/70 leading-relaxed mt-1.5",
                ),
                rx.cond(
                    item["author"] != "",
                    rx.el.span(
                        item["author"],
                        class_name="text-[10px] font-semibold text-emerald-100/40 mt-1",
                    ),
                    rx.fragment(),
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        key=key,
        class_name="w-full rounded-xl border border-white/10 bg-white/[0.02] p-3",
    )


def _version_form() -> rx.Component:
    return rx.cond(
        GuideAdminState.version_form_open,
        rx.el.form(
            rx.el.div(
                rx.el.label(
                    rx.el.span(
                        "Numéro de version",
                        class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
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
                        class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
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
                        class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
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
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
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
                    class_name="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-emerald-100/65 hover:text-emerald-50 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon(
                        "git-branch-plus",
                        class_name="h-4 w-4 stroke-[#04140d]",
                    ),
                    rx.el.span(
                        "Ouvrir la version", class_name="text-[#04140d]"
                    ),
                    type="submit",
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center justify-end gap-2 w-full mt-3",
            ),
            on_submit=GuideAdminState.create_version,
            reset_on_submit=True,
            class_name="w-full rounded-2xl border border-lime-300/25 bg-[#04140d]/70 p-4 mt-4",
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
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Versions consultables du guide",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    f"Version courante : {GuideAdminState.current_version['version_label']} · {GuideAdminState.current_version['status_label']}",
                    class_name="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40 mt-2",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("git-branch-plus", class_name="h-3.5 w-3.5"),
                rx.el.span("Nouvelle version"),
                on_click=GuideAdminState.toggle_version_form,
                class_name=rx.cond(
                    GuideAdminState.version_form_open,
                    "flex items-center gap-2 rounded-full border border-lime-300/45 bg-lime-300/15 px-4 py-2 text-xs font-semibold text-lime-100 transition-colors w-fit",
                    "flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
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
                    rx.icon("history", class_name="h-4 w-4 text-lime-300"),
                    rx.el.div(
                        rx.el.span(
                            "Historique éditorial",
                            class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/45",
                        ),
                        rx.el.h3(
                            f"{GuideAdminState.selected_version['version_label']} · {GuideAdminState.selected_version['title']}",
                            class_name="font-['Instrument_Serif'] text-xl text-emerald-50 mt-0.5",
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    rx.el.span(
                        f"{GuideAdminState.changelog.length()} entrée(s)",
                        class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
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
                            "file-clock", class_name="h-6 w-6 text-amber-300"
                        ),
                        rx.el.p(
                            "Aucune entrée de changelog sur cette version.",
                            class_name="text-sm font-medium text-emerald-100/55 mt-2 text-center",
                        ),
                        class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 w-full mt-4",
                    ),
                ),
                class_name="flex-1 min-w-0 rounded-2xl border border-white/10 bg-white/[0.02] p-5",
            ),
            class_name="flex flex-col xl:flex-row gap-4 w-full mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
