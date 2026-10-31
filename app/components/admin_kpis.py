import reflex as rx

from app.components.design import index_tab, stat
from app.states.administration_state import SECTIONS, AdministrationState


def _tile(
    label: str,
    value: rx.Var | str,
    unit: str,
    caption: rx.Var | str,
    icon: str,
    icon_class: str = "",
) -> rx.Component:
    """Chiffre indicateur, registre éditorial : filet, valeur serif, légende."""
    tone = "flame" if "ff8a5b" in icon_class else "paper"
    return stat(label, value, unit, caption, icon=icon, tone=tone)


def _section_title() -> rx.Component:
    return rx.el.div(
        rx.icon("shield-check", class_name="h-4 w-4 text-[#a9c98b]"),
        rx.el.span("Indicateurs de gouvernance", class_name="ap-eyebrow text-[#c9c5b4]/55"),
        class_name="flex w-full items-center gap-2",
    )


def admin_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(),
        rx.el.div(
            _tile(
                "Comptes suivis",
                AdministrationState.kpis["users"],
                "utilisateurs",
                AdministrationState.coverage_label,
                "users-round",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "À arbitrer",
                AdministrationState.kpis["suspended"]
                + AdministrationState.kpis["pending"],
                "comptes",
                "Suspendus ou en attente de validation",
                "user-cog",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Équipes agricoles",
                AdministrationState.kpis["teams"],
                "équipes",
                AdministrationState.kpis["parcels"].to_string()
                + " parcelle(s) couverte(s) par affectation",
                "users",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "Fonctions & rôles",
                AdministrationState.kpis["functions"],
                "fonctions",
                AdministrationState.kpis["roles"].to_string()
                + " rôles applicatifs déclarés",
                "briefcase",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Permissions",
                AdministrationState.kpis["permissions"],
                "module × action",
                AdministrationState.kpis["grants"].to_string()
                + " liaisons RBAC accordées",
                "key-round",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Sécurité",
                AdministrationState.kpis["sensitive"],
                "actions sensibles",
                AdministrationState.mfa_label,
                "shield-check",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            class_name=(
                "grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )


def _section_button(key: str, label: str, icon: str) -> rx.Component:
    return index_tab(
        label,
        active=AdministrationState.section == key,
        on_click=AdministrationState.set_section(key),
        icon=icon,
    )


def admin_section_nav() -> rx.Component:
    return rx.el.nav(
        *[_section_button(key, label, icon) for key, label, icon in SECTIONS],
        class_name=(
            "flex w-full flex-wrap items-center gap-x-6 gap-y-2 "
            "border-b border-[#F2EFE4]/12 pb-1"
        ),
    )
