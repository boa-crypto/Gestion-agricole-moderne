import reflex as rx

from app.components.design import stat
from app.states.employees_state import EmployeesState


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
        rx.icon("users-round", class_name="h-4 w-4 text-[#d8fa5e]"),
        rx.el.span("Indicateurs RH", class_name="ap-eyebrow text-[#c9c5b4]/55"),
        class_name="flex w-full items-center gap-2",
    )


def workforce_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(),
        rx.el.div(
            _tile(
                "Effectif suivi",
                f"{EmployeesState.kpis['total']:.0f}",
                "personnes",
                f"{EmployeesState.kpis['active']:.0f} en poste aujourd'hui",
                "users-round",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Absences",
                f"{EmployeesState.kpis['absent']:.0f}",
                "en cours",
                "Congés et arrêts déclarés",
                "user-minus",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Capacité hebdo",
                f"{EmployeesState.kpis['weekly_hours']:.0f}",
                "h/sem",
                "Volume contractuel cumulé",
                "clock",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "Masse salariale",
                f"{EmployeesState.kpis['weekly_cost']:.0f}",
                "€/sem",
                "Coût direct au taux horaire",
                "coins",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Certiphyto",
                f"{EmployeesState.kpis['certified']:.0f}",
                "titulaires",
                f"{EmployeesState.kpis['skills']:.0f} compétences référencées",
                "badge-check",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Affectations 7 j",
                f"{EmployeesState.kpis['assignments']:.0f}",
                "chantiers",
                "Missions proposées ou confirmées",
                "calendar-clock",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            class_name=(
                "grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )
