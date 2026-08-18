"""Formulaires et panneaux import/export de l'administration phénologique."""

import reflex as rx

from app.states.phenology_admin_state import PhenologyAdminState

_INPUT = (
    "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm "
    "font-medium text-emerald-50 placeholder:text-emerald-100/25 "
    "focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 "
    "outline-hidden transition-colors"
)
_LABEL = (
    "block text-[10px] font-semibold uppercase tracking-[0.2em] "
    "text-emerald-100/45 mb-1.5"
)


def _field(label: str, control: rx.Component, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name=_LABEL),
        control,
        rx.cond(
            hint != "",
            rx.el.p(
                hint,
                class_name="text-[10px] font-medium text-emerald-100/35 mt-1",
            ),
            rx.fragment(),
        ),
        class_name="w-full min-w-0",
    )


def _text(
    name: str, value: rx.Var, placeholder: str = "", kind: str = "text"
) -> rx.Component:
    return rx.el.input(
        type=kind,
        name=name,
        default_value=value,
        key=f"{PhenologyAdminState.editor_key}-{name}",
        placeholder=placeholder,
        class_name=_INPUT,
    )


def _area(
    name: str, value: rx.Var, placeholder: str = "", rows: str = "3"
) -> rx.Component:
    return rx.el.textarea(
        name=name,
        default_value=value,
        key=f"{PhenologyAdminState.editor_key}-{name}",
        placeholder=placeholder,
        rows=rows,
        class_name=f"{_INPUT} resize-y leading-relaxed",
    )


def _select(name: str, value: rx.Var, options: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(
                options,
                lambda option: rx.el.option(
                    option[1],
                    value=option[0],
                    selected=option[0] == value,
                ),
            ),
            name=name,
            key=f"{PhenologyAdminState.editor_key}-{name}",
            class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _culture_select(value: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.el.option("Choisir une culture…", value="", disabled=True),
            rx.foreach(
                PhenologyAdminState.cultures,
                lambda item: rx.el.option(
                    item["label"],
                    value=item["value"],
                    selected=item["value"] == value,
                ),
            ),
            name="culture_id",
            key=f"{PhenologyAdminState.editor_key}-culture_id",
            class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _check(name: str, value: rx.Var, label: str, hint: str) -> rx.Component:
    return rx.el.label(
        rx.el.input(
            type="checkbox",
            name=name,
            default_value="1",
            default_checked=value == "1",
            key=f"{PhenologyAdminState.editor_key}-{name}",
            class_name="h-4 w-4 shrink-0 accent-lime-300 cursor-pointer mt-0.5",
        ),
        rx.el.div(
            rx.el.span(
                label,
                class_name="text-[12px] font-semibold text-emerald-50",
            ),
            rx.el.p(
                hint,
                class_name="text-[10px] font-medium text-emerald-100/40 mt-0.5",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2.5 cursor-pointer",
    )


def _errors() -> rx.Component:
    return rx.cond(
        PhenologyAdminState.has_errors,
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "octagon-alert",
                    class_name="h-4 w-4 shrink-0 stroke-red-300",
                ),
                rx.el.span(
                    "Enregistrement refusé : corrigez les points suivants.",
                    class_name="text-[11px] font-semibold text-red-200",
                ),
                class_name="flex items-start gap-2",
            ),
            rx.foreach(
                PhenologyAdminState.form_errors,
                lambda message: rx.el.p(
                    message,
                    class_name="text-[11px] font-medium text-red-100/75 mt-1.5 leading-relaxed",
                ),
            ),
            class_name="w-full rounded-xl border border-red-400/30 bg-red-500/10 p-3 mt-4",
        ),
        rx.fragment(),
    )


def _modal(
    title: rx.Var | str,
    subtitle: str,
    icon: str,
    body: rx.Component,
    submit_label: str,
    on_submit: rx.event.EventType,
    on_close: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.form(
                rx.el.div(
                    rx.el.div(
                        rx.icon(icon, class_name="h-4 w-4 text-lime-300"),
                        rx.el.span(
                            subtitle,
                            class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    rx.el.h2(
                        title,
                        class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                    ),
                    class_name="w-full",
                ),
                body,
                _errors(),
                rx.el.div(
                    rx.el.button(
                        "Annuler",
                        type="button",
                        on_click=on_close,
                        class_name="rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-semibold text-emerald-100/70 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon("check", class_name="h-4 w-4 stroke-[#04140d]"),
                        rx.el.span(submit_label, class_name="text-[#04140d]"),
                        type="submit",
                        class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-5 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                    ),
                    class_name="flex flex-wrap items-center justify-end gap-3 w-full border-t border-white/10 pt-5 mt-6",
                ),
                on_submit=on_submit,
                class_name="w-full",
            ),
            class_name="w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#061a11]/95 p-7 backdrop-blur-2xl",
        ),
        class_name="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm",
    )


def _profile_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Nom du profil",
                _text(
                    "name",
                    PhenologyAdminState.profile_draft["name"],
                    "Cycle phénologique du blé",
                ),
                "Vocabulaire agricole compréhensible.",
            ),
            _field(
                "Identifiant technique",
                _text(
                    "key",
                    PhenologyAdminState.profile_draft["key"],
                    "phen-ble",
                ),
                "Minuscules, chiffres et tirets.",
            ),
            _field(
                "Culture du référentiel",
                _culture_select(
                    PhenologyAdminState.profile_draft["culture_id"]
                ),
                "Le cycle reste propre à cette culture.",
            ),
            _field(
                "Système de notation",
                _select(
                    "system",
                    PhenologyAdminState.profile_draft["system"],
                    PhenologyAdminState.system_options,
                ),
                "BBCH n'est jamais imposé à toutes les cultures.",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6",
        ),
        _field(
            "Enchaînement résumé",
            _area(
                "summary",
                PhenologyAdminState.profile_draft["summary"],
                "Germination → Levée → Tallage → …",
            ),
        ),
        _field(
            "Source du référentiel",
            _text(
                "source",
                PhenologyAdminState.profile_draft["source"],
                "Échelle BBCH céréales à paille",
            ),
            "Obligatoire : aucune donnée agronomique inventée.",
        ),
        rx.el.div(
            _check(
                "is_default",
                PhenologyAdminState.profile_draft["is_default"],
                "Profil par défaut de la culture",
                "Utilisé quand aucune variété n'apporte de cycle spécifique.",
            ),
            _check(
                "is_active",
                PhenologyAdminState.profile_draft["is_active"],
                "Profil actif",
                "La désactivation conserve toutes les données existantes.",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4",
        ),
        class_name="w-full",
    )


def _stage_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Nom du stade",
                _text(
                    "name",
                    PhenologyAdminState.stage_draft["name"],
                    "Tallage",
                ),
            ),
            _field(
                "Identifiant technique",
                _text(
                    "key",
                    PhenologyAdminState.stage_draft["key"],
                    "tallage",
                ),
                "Laisser vide pour le déduire du nom.",
            ),
            _field(
                "Code BBCH",
                _text(
                    "bbch_code",
                    PhenologyAdminState.stage_draft["bbch_code"],
                    "BBCH 21-29",
                ),
                "Facultatif selon le système du profil.",
            ),
            _field(
                "Durée indicative minimale (j)",
                _text(
                    "duration_days_min",
                    PhenologyAdminState.stage_draft["duration_days_min"],
                    "30",
                    "number",
                ),
            ),
            _field(
                "Durée indicative maximale (j)",
                _text(
                    "duration_days_max",
                    PhenologyAdminState.stage_draft["duration_days_max"],
                    "70",
                    "number",
                ),
            ),
            _field(
                "Icône",
                _text(
                    "icon",
                    PhenologyAdminState.stage_draft["icon"],
                    "sprout",
                ),
            ),
            _field(
                "Couleur du rail",
                _text(
                    "color_hex",
                    PhenologyAdminState.stage_draft["color_hex"],
                    "#a3e635",
                ),
            ),
            _field(
                "Article du Guide (slug)",
                _text(
                    "guide_article_slug",
                    PhenologyAdminState.stage_draft["guide_article_slug"],
                    "suivre-les-stades",
                ),
                "Alimente « Comprendre ce stade ».",
            ),
            _field(
                "Terme du dictionnaire (slug)",
                _text(
                    "guide_term_slug",
                    PhenologyAdminState.stage_draft["guide_term_slug"],
                    "stade-phenologique",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6",
        ),
        _field(
            "Définition du stade",
            _area(
                "description",
                PhenologyAdminState.stage_draft["description"],
                "Ce qui se passe physiologiquement à ce stade…",
            ),
        ),
        rx.el.div(
            _field(
                "Comment le reconnaître",
                _area(
                    "recognition",
                    PhenologyAdminState.stage_draft["recognition"],
                    "Signes observables sur la plante…",
                ),
            ),
            _field(
                "Points de surveillance",
                _area(
                    "watchpoints",
                    PhenologyAdminState.stage_draft["watchpoints"],
                    "Maladies, ravageurs, stress à observer…",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4",
        ),
        _field(
            "Erreurs fréquentes",
            _area(
                "common_errors",
                PhenologyAdminState.stage_draft["common_errors"],
                "Confusions habituelles à éviter…",
            ),
        ),
        rx.el.div(
            _check(
                "is_critical",
                PhenologyAdminState.stage_draft["is_critical"],
                "Stade sensible",
                "Signalé « stade sensible » dans les modules opérationnels.",
            ),
            _check(
                "is_active",
                PhenologyAdminState.stage_draft["is_active"],
                "Stade actif dans le cycle",
                "Désactiver n'efface ni le stade ni ses observations.",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4",
        ),
        class_name="w-full",
    )


def _reco_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "info", class_name="h-4 w-4 shrink-0 stroke-lime-300 mt-0.5"
            ),
            rx.el.p(
                "Les opérations associées restent des informations générales à "
                "vérifier : aucune dose, aucun produit phytosanitaire non "
                "sourcé, aucune transformation automatique en intervention.",
                class_name="text-[11px] font-medium text-emerald-100/60 leading-relaxed",
            ),
            class_name="flex items-start gap-2.5 w-full rounded-2xl border border-lime-300/25 bg-lime-300/[0.06] p-4 mt-6",
        ),
        rx.el.div(
            _field(
                "Domaine",
                _select(
                    "domain",
                    PhenologyAdminState.reco_draft["domain"],
                    PhenologyAdminState.domain_options,
                ),
            ),
            _field(
                "Niveau de confiance",
                _select(
                    "confidence",
                    PhenologyAdminState.reco_draft["confidence"],
                    PhenologyAdminState.confidence_options,
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4",
        ),
        _field(
            "Titre",
            _text(
                "title",
                PhenologyAdminState.reco_draft["title"],
                "Surveiller la pression foliaire",
            ),
        ),
        _field(
            "Énoncé",
            _area(
                "statement",
                PhenologyAdminState.reco_draft["statement"],
                "Ce qu'il convient d'observer ou d'apprécier sur le terrain…",
                rows="4",
            ),
            "Aucune dose chiffrée n'est acceptée.",
        ),
        rx.el.div(
            _field(
                "Source",
                _text(
                    "source",
                    PhenologyAdminState.reco_draft["source"],
                    "Référentiel agronomique AgriPro",
                ),
            ),
            _field(
                "Article du Guide (slug)",
                _text(
                    "guide_article_slug",
                    PhenologyAdminState.reco_draft["guide_article_slug"],
                    "plan-de-fumure",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4",
        ),
        class_name="w-full",
    )


def phenology_admin_modals() -> rx.Component:
    """Modales d'édition profil, stade et opération associée."""
    return rx.fragment(
        rx.cond(
            PhenologyAdminState.profile_editor_open,
            _modal(
                PhenologyAdminState.profile_editor_title,
                "Référentiel phénologique",
                "git-branch",
                _profile_body(),
                "Enregistrer le profil",
                PhenologyAdminState.submit_profile,
                PhenologyAdminState.close_profile_editor,
            ),
            rx.fragment(),
        ),
        rx.cond(
            PhenologyAdminState.stage_editor_open,
            _modal(
                PhenologyAdminState.stage_editor_title,
                PhenologyAdminState.selected_profile["name"],
                "sprout",
                _stage_body(),
                "Enregistrer le stade",
                PhenologyAdminState.submit_stage,
                PhenologyAdminState.close_stage_editor,
            ),
            rx.fragment(),
        ),
        rx.cond(
            PhenologyAdminState.reco_editor_open,
            _modal(
                PhenologyAdminState.reco_editor_title,
                PhenologyAdminState.selected_stage["name"],
                "list-checks",
                _reco_body(),
                "Enregistrer l'information",
                PhenologyAdminState.submit_recommendation,
                PhenologyAdminState.close_reco_editor,
            ),
            rx.fragment(),
        ),
    )


def phenology_import_panel() -> rx.Component:
    """Import additif CSV / JSON des stades d'un profil."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Importation du référentiel",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Enrichir les stades depuis un CSV ou un JSON",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Import additif : un stade connu est complété, un stade "
                    "inconnu est ajouté à la fin du cycle. Aucune ligne "
                    "existante n'est supprimée.",
                    class_name="text-xs font-medium text-emerald-100/50 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("file-down", class_name="h-3.5 w-3.5"),
                rx.el.span("Charger le modèle CSV"),
                on_click=PhenologyAdminState.load_csv_template,
                class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.el.form(
            rx.el.div(
                _field(
                    "Format",
                    _select(
                        "format",
                        PhenologyAdminState.import_format,
                        PhenologyAdminState.format_options,
                    ),
                ),
                _field(
                    "Profil ciblé",
                    rx.el.p(
                        PhenologyAdminState.selected_profile["name"],
                        class_name="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm font-semibold text-emerald-50 truncate",
                    ),
                    "Les stades sont rattachés à ce profil uniquement.",
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5",
            ),
            _field(
                "Contenu à importer",
                rx.el.textarea(
                    name="payload",
                    default_value=PhenologyAdminState.import_payload,
                    key=f"import-{PhenologyAdminState.editor_key}",
                    rows="8",
                    placeholder=(
                        "key,name,bbch_code,duration_days_min,"
                        "duration_days_max,is_critical,description"
                    ),
                    class_name=f"{_INPUT} font-mono text-[11px] resize-y",
                ),
                "Colonnes reconnues : key, name, bbch_code, description, "
                "recognition, watchpoints, common_errors, duration_days_min, "
                "duration_days_max, is_critical, icon, color_hex, "
                "guide_article_slug, guide_term_slug.",
            ),
            rx.el.button(
                rx.icon("upload", class_name="h-4 w-4 stroke-[#04140d]"),
                rx.el.span(
                    "Lancer l'import additif", class_name="text-[#04140d]"
                ),
                type="submit",
                class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-4",
            ),
            on_submit=PhenologyAdminState.run_import,
            class_name="w-full",
        ),
        rx.cond(
            PhenologyAdminState.import_report.length() > 0,
            rx.el.div(
                rx.el.span(
                    "Rapport d'import",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.foreach(
                    PhenologyAdminState.import_report,
                    lambda line: rx.el.p(
                        line,
                        class_name="text-[11px] font-medium text-emerald-100/65 mt-1.5 leading-relaxed",
                    ),
                ),
                class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def phenology_export_panel() -> rx.Component:
    """Export JSON / CSV des profils, stades et recommandations."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Exportation du référentiel",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Profils, stades et opérations associées",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "L'export conserve la mention « information indicative » "
                    "pour chaque opération associée à un stade.",
                    class_name="text-xs font-medium text-emerald-100/50 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            PhenologyAdminState.format_options,
                            lambda option: rx.el.option(
                                option[1], value=option[0]
                            ),
                        ),
                        value=PhenologyAdminState.export_format,
                        on_change=PhenologyAdminState.set_export_format,
                        class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                    ),
                    class_name="relative w-full sm:w-52",
                ),
                rx.el.button(
                    rx.icon("download", class_name="h-3.5 w-3.5"),
                    rx.el.span("Ce profil"),
                    on_click=PhenologyAdminState.run_export,
                    class_name="flex items-center gap-2 rounded-full border border-lime-300/30 bg-lime-300/10 px-4 py-2 text-xs font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("database", class_name="h-3.5 w-3.5"),
                    rx.el.span("Tout le référentiel"),
                    on_click=PhenologyAdminState.export_all,
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.cond(
            PhenologyAdminState.export_payload != "",
            rx.el.pre(
                PhenologyAdminState.export_payload,
                class_name="w-full max-h-80 overflow-auto rounded-2xl border border-white/10 bg-[#04140d] p-4 text-[11px] font-mono text-emerald-100/70 mt-5 whitespace-pre",
            ),
            rx.el.p(
                "Choisissez un format puis générez l'export : le contenu "
                "s'affiche ici, prêt à être copié.",
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
