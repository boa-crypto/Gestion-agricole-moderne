"""Pupitre éditorial du Guide Agricole : registre, fiches et publications."""

import reflex as rx

from app.components.guide_admin_editor import guide_admin_editor
from app.components.guide_admin_versions import (
    guide_admin_versions,
    status_badge,
)
from app.states.guide_admin_state import ContentRow, GuideAdminState

_SELECT = (
    "w-full appearance-none rounded-xl border border-white/10 bg-[#04140d] "
    "py-2.5 pl-3 pr-9 text-sm font-medium text-emerald-50 "
    "focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 "
    "outline-hidden transition-colors cursor-pointer"
)


def _stat(label: str, value: rx.Var | int, caption: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none text-emerald-50",
            ),
            rx.el.span(
                caption,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3",
    )


def _header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("square-pen", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Pupitre éditorial",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h2(
                    "Administration du Guide Agricole",
                    class_name="font-['Instrument_Serif'] text-3xl md:text-4xl text-emerald-50 mt-2",
                ),
                rx.el.p(
                    "Rédiger, relire, publier et archiver les contenus du guide, "
                    "version par version, sans jamais supprimer la mémoire éditoriale.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2 max-w-2xl",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        GuideAdminState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-emerald-100/70",
                        ),
                        rx.icon(
                            "refresh-cw",
                            class_name="h-4 w-4 text-emerald-100/70",
                        ),
                    ),
                    rx.el.span("Recharger le registre"),
                    on_click=GuideAdminState.load_admin,
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-emerald-100/70 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4 stroke-[#04140d]"),
                    rx.el.span(
                        f"Nouveau · {GuideAdminState.kind_label}",
                        class_name="text-[#04140d]",
                    ),
                    on_click=GuideAdminState.start_create(
                        GuideAdminState.content_kind
                    ),
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-start gap-2 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-start justify-between gap-5 w-full",
        ),
        rx.el.div(
            _stat(
                "Brouillons",
                GuideAdminState.status_totals["BROUILLON"],
                "en cours",
            ),
            _stat(
                "Relecture",
                GuideAdminState.status_totals["RELECTURE"],
                "à valider",
            ),
            _stat(
                "Publiés",
                GuideAdminState.status_totals["PUBLIE"],
                "consultables",
            ),
            _stat(
                "Archivés",
                GuideAdminState.status_totals["ARCHIVE"],
                "conservés",
            ),
            _stat("Total", GuideAdminState.status_totals["TOTAL"], "fiches"),
            class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 w-full mt-6",
        ),
        rx.cond(
            GuideAdminState.notice != "",
            rx.el.div(
                rx.icon(
                    "circle-check",
                    class_name="h-4 w-4 stroke-lime-300 shrink-0",
                ),
                rx.el.p(
                    GuideAdminState.notice,
                    class_name="text-[12px] font-semibold text-lime-100/90",
                ),
                class_name="flex items-center gap-2 w-full rounded-2xl border border-lime-300/25 bg-lime-300/[0.07] px-4 py-2.5 mt-4",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 md:p-8 backdrop-blur-xl",
    )


def _kind_tab(item: tuple[str, str, str]) -> rx.Component:
    return rx.el.button(
        rx.icon(
            item[2],
            class_name=rx.cond(
                GuideAdminState.content_kind == item[0],
                "h-4 w-4 text-lime-300",
                "h-4 w-4 text-emerald-100/45",
            ),
        ),
        rx.el.span(item[1]),
        rx.el.span(
            GuideAdminState.kind_totals[item[0]],
            class_name="rounded-full bg-white/10 px-1.5 py-0.5 text-[9px] font-bold text-emerald-100/70 w-fit",
        ),
        on_click=GuideAdminState.set_content_kind(item[0]),
        class_name=rx.cond(
            GuideAdminState.content_kind == item[0],
            "flex items-center gap-2 rounded-full border border-lime-300/45 bg-lime-300/15 px-4 py-2 text-xs font-semibold text-lime-100 transition-colors w-fit",
            "flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-medium text-emerald-100/60 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
        ),
    )


def _filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher un titre, un identifiant, un extrait…",
                default_value=GuideAdminState.search,
                on_change=GuideAdminState.set_search.debounce(400),
                class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/25 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
            ),
            class_name="relative flex-1 min-w-[16rem]",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option("Toutes les catégories", value="TOUS"),
                rx.foreach(
                    GuideAdminState.categories,
                    lambda item: rx.el.option(item["name"], value=item["key"]),
                ),
                value=GuideAdminState.filter_category,
                on_change=GuideAdminState.set_filter_category,
                class_name=_SELECT,
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-emerald-100/45 pointer-events-none",
            ),
            class_name="relative w-full sm:w-56",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option("Tous les statuts", value="TOUS"),
                rx.foreach(
                    GuideAdminState.status_options,
                    lambda option: rx.el.option(option[1], value=option[0]),
                ),
                value=GuideAdminState.filter_status,
                on_change=GuideAdminState.set_filter_status,
                class_name=_SELECT,
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-emerald-100/45 pointer-events-none",
            ),
            class_name="relative w-full sm:w-48",
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-3.5 w-3.5"),
            rx.el.span("Réinitialiser"),
            on_click=GuideAdminState.reset_filters,
            class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
        ),
        class_name="flex flex-wrap items-center gap-2 w-full mt-4",
    )


def _status_select(item: ContentRow) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(
                GuideAdminState.status_options,
                lambda option: rx.el.option(
                    option[1],
                    value=option[0],
                    selected=option[0] == item["status"],
                ),
            ),
            on_change=lambda value: GuideAdminState.set_content_status(
                item["kind"], item["id"], value
            ),
            class_name="appearance-none rounded-full border border-white/10 bg-[#04140d] py-1 pl-3 pr-7 text-[10px] font-bold text-emerald-100/75 focus:border-lime-300/50 outline-hidden cursor-pointer",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3 text-emerald-100/45 pointer-events-none",
        ),
        class_name="relative w-fit",
    )


def _content_row(item: ContentRow, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        item["kind_label"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-bold text-emerald-100/60 w-fit",
                    ),
                    status_badge(item["status_label"], item["tone"]),
                    rx.el.span(
                        item["version_label"],
                        class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-2 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                    ),
                    rx.el.span(
                        item["ref"],
                        class_name="text-[9px] font-mono text-emerald-100/40 truncate",
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 w-full",
                ),
                rx.el.p(
                    item["title"],
                    class_name="text-sm font-semibold text-emerald-50 mt-2",
                ),
                rx.el.p(
                    item["excerpt"],
                    class_name="text-[11px] font-medium text-emerald-100/55 leading-relaxed mt-1.5 line-clamp-2",
                ),
                rx.el.div(
                    rx.el.span(
                        item["category_name"],
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
                    rx.el.span(
                        item["date_label"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/55 w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                _status_select(item),
                rx.el.button(
                    rx.icon("eye", class_name="h-3.5 w-3.5"),
                    rx.el.span("Aperçu"),
                    on_click=GuideAdminState.open_preview(
                        item["kind"], item["id"]
                    ),
                    class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("square-pen", class_name="h-3.5 w-3.5"),
                    rx.el.span("Éditer"),
                    on_click=GuideAdminState.start_edit(
                        item["kind"], item["id"]
                    ),
                    class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[11px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
                ),
                rx.cond(
                    item["status"] != "ARCHIVE",
                    rx.el.button(
                        rx.icon("archive", class_name="h-3.5 w-3.5"),
                        rx.el.span("Archiver"),
                        on_click=GuideAdminState.archive_content(
                            item["kind"], item["id"]
                        ),
                        class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-emerald-100/55 hover:text-red-200 hover:border-red-400/30 transition-colors w-fit",
                    ),
                    rx.el.span(
                        "Archivé",
                        class_name="rounded-full border border-red-400/25 bg-red-500/10 px-3 py-1.5 text-[11px] font-semibold text-red-200/80 w-fit",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2 lg:flex-col lg:items-end shrink-0",
            ),
            class_name="flex flex-col lg:flex-row gap-4 w-full",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def _register() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre des contenus",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    f"{GuideAdminState.kind_label} du guide",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{GuideAdminState.visible_count} fiche(s) affichée(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.nav(
            rx.foreach(GuideAdminState.kind_tabs, _kind_tab),
            aria_label="Types de contenus du guide",
            class_name="flex flex-wrap items-center gap-2 w-full mt-5",
        ),
        _filters(),
        rx.cond(
            GuideAdminState.visible_count > 0,
            rx.el.div(
                rx.foreach(
                    GuideAdminState.items,
                    lambda item: _content_row(item, key=item["id"].to_string()),
                ),
                class_name="flex flex-col gap-3 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("file-search", class_name="h-6 w-6 text-amber-300"),
                rx.el.p(
                    "Aucune fiche ne correspond à ce filtrage éditorial.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-3.5 w-3.5"),
                    rx.el.span("Créer une fiche"),
                    on_click=GuideAdminState.start_create(
                        GuideAdminState.content_kind
                    ),
                    class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-4 py-2 text-[11px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit mt-4",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-14 w-full mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _preview_block(title: str, body: rx.Var, icon: str) -> rx.Component:
    return rx.cond(
        body != "",
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/80"),
                rx.el.span(
                    title,
                    class_name="text-[9px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.p(
                body,
                class_name="text-[12px] font-medium text-emerald-100/70 leading-relaxed whitespace-pre-line mt-1.5",
            ),
            class_name="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3",
        ),
        rx.fragment(),
    )


def _preview() -> rx.Component:
    return rx.cond(
        GuideAdminState.preview_open,
        rx.el.section(
            rx.el.div(
                rx.el.div(
                    rx.icon("eye", class_name="h-4 w-4 text-lime-300"),
                    rx.el.div(
                        rx.el.span(
                            "Aperçu du contenu",
                            class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                        ),
                        rx.el.h3(
                            GuideAdminState.preview["title"],
                            class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-0.5",
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-3.5 w-3.5"),
                        rx.el.span("Fermer"),
                        on_click=GuideAdminState.close_preview,
                        class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-emerald-100/65 hover:text-emerald-50 transition-colors w-fit",
                    ),
                    class_name="flex items-start gap-2.5 w-full",
                ),
                rx.el.div(
                    rx.el.span(
                        GuideAdminState.preview["kind_label"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-bold text-emerald-100/60 w-fit",
                    ),
                    rx.el.span(
                        GuideAdminState.preview["category_name"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/55 w-fit",
                    ),
                    rx.el.span(
                        GuideAdminState.preview["version_label"],
                        class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-2.5 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
                    ),
                    rx.el.span(
                        GuideAdminState.preview["ref"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-mono text-emerald-100/45 w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full mt-3",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                _preview_block(
                    "Résumé", GuideAdminState.preview["summary"], "quote"
                ),
                _preview_block(
                    "Lecture agricole",
                    GuideAdminState.preview["body_farmer"],
                    "tractor",
                ),
                _preview_block(
                    "Lecture AgriPro",
                    GuideAdminState.preview["body_pro"],
                    "database",
                ),
                _preview_block(
                    "Réponse agricole",
                    GuideAdminState.preview["answer_farmer"],
                    "tractor",
                ),
                _preview_block(
                    "Réponse AgriPro",
                    GuideAdminState.preview["answer_pro"],
                    "database",
                ),
                _preview_block(
                    "Définition agricole",
                    GuideAdminState.preview["definition_farmer"],
                    "tractor",
                ),
                _preview_block(
                    "Définition AgriPro",
                    GuideAdminState.preview["definition_pro"],
                    "database",
                ),
                _preview_block(
                    "Énoncé", GuideAdminState.preview["statement"], "scale"
                ),
                _preview_block(
                    "Pourquoi ?",
                    GuideAdminState.preview["rationale"],
                    "circle-help",
                ),
                _preview_block(
                    "Correction",
                    GuideAdminState.preview["remediation"],
                    "wrench",
                ),
                _preview_block(
                    "Objectif", GuideAdminState.preview["objective"], "target"
                ),
                _preview_block(
                    "Résultat attendu",
                    GuideAdminState.preview["expected_result"],
                    "flag",
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-5",
            ),
            class_name="w-full rounded-3xl border border-lime-300/20 bg-[#04140d]/75 p-6 backdrop-blur-xl",
        ),
        rx.fragment(),
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-36 rounded-3xl bg-white/[0.05]"),
        rx.el.div(class_name="animate-pulse h-56 rounded-3xl bg-white/[0.05]"),
        class_name="flex flex-col gap-4 w-full",
    )


def guide_admin() -> rx.Component:
    """Section d'administration éditoriale intégrée au module Guide."""
    return rx.el.div(
        guide_admin_editor(),
        rx.cond(
            GuideAdminState.is_loading,
            _skeleton(),
            rx.el.div(
                _header(),
                guide_admin_versions(),
                _register(),
                _preview(),
                class_name="flex flex-col gap-4 w-full",
            ),
        ),
        class_name="w-full",
    )
