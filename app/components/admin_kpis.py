import reflex as rx

from app.states.administration_state import SECTIONS, AdministrationState


def _tile(
    label: str,
    value: rx.Var | str,
    unit: str,
    caption: rx.Var | str,
    icon: str,
    icon_class: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/50",
            ),
            rx.icon(icon, class_name=icon_class),
            class_name="flex items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-3xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-xs font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-4",
        ),
        rx.el.p(
            caption,
            class_name="text-[11px] font-medium text-emerald-100/45 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl hover:border-lime-300/30 transition-colors",
    )


def admin_kpis() -> rx.Component:
    return rx.el.section(
        _tile(
            "Comptes suivis",
            AdministrationState.kpis["users"],
            "utilisateurs",
            AdministrationState.coverage_label,
            "users-round",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "À arbitrer",
            AdministrationState.kpis["suspended"]
            + AdministrationState.kpis["pending"],
            "comptes",
            "Suspendus ou en attente de validation",
            "user-cog",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Équipes agricoles",
            AdministrationState.kpis["teams"],
            "équipes",
            AdministrationState.kpis["parcels"].to_string()
            + " parcelle(s) couverte(s) par affectation",
            "users",
            "h-4 w-4 text-emerald-300",
        ),
        _tile(
            "Fonctions & rôles",
            AdministrationState.kpis["functions"],
            "fonctions",
            AdministrationState.kpis["roles"].to_string()
            + " rôles applicatifs déclarés",
            "briefcase",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Permissions",
            AdministrationState.kpis["permissions"],
            "module × action",
            AdministrationState.kpis["grants"].to_string()
            + " liaisons RBAC accordées",
            "key-round",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Sécurité",
            AdministrationState.kpis["sensitive"],
            "actions sensibles",
            AdministrationState.mfa_label,
            "shield-check",
            "h-4 w-4 text-lime-300",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full",
    )


def _section_button(key: str, label: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(
            icon,
            class_name=rx.cond(
                AdministrationState.section == key,
                "h-4 w-4 text-[#04140d]",
                "h-4 w-4 text-emerald-100/60",
            ),
        ),
        rx.el.span(
            label,
            class_name=rx.cond(
                AdministrationState.section == key,
                "text-sm font-semibold text-[#04140d]",
                "text-sm font-semibold text-emerald-100/70",
            ),
        ),
        on_click=AdministrationState.set_section(key),
        class_name=rx.cond(
            AdministrationState.section == key,
            "flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 transition-colors w-fit",
            "flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 hover:border-lime-300/30 transition-colors w-fit",
        ),
    )


def admin_section_nav() -> rx.Component:
    return rx.el.nav(
        *[_section_button(key, label, icon) for key, label, icon in SECTIONS],
        class_name="flex flex-wrap items-center gap-2 w-full rounded-3xl border border-white/10 bg-white/[0.03] p-3 backdrop-blur-xl",
    )
