import reflex as rx

from app.states.employees_state import EmployeesState


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


def workforce_kpis() -> rx.Component:
    return rx.el.section(
        _tile(
            "Effectif suivi",
            f"{EmployeesState.kpis['total']:.0f}",
            "personnes",
            f"{EmployeesState.kpis['active']:.0f} en poste aujourd'hui",
            "users-round",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Absences",
            f"{EmployeesState.kpis['absent']:.0f}",
            "en cours",
            "Congés et arrêts déclarés",
            "user-minus",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Capacité hebdo",
            f"{EmployeesState.kpis['weekly_hours']:.0f}",
            "h / semaine",
            "Volume contractuel cumulé",
            "clock",
            "h-4 w-4 text-emerald-300",
        ),
        _tile(
            "Masse salariale",
            f"{EmployeesState.kpis['weekly_cost']:.0f}",
            "€ / semaine",
            "Coût direct au taux horaire",
            "coins",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Certiphyto",
            f"{EmployeesState.kpis['certified']:.0f}",
            "titulaires",
            f"{EmployeesState.kpis['skills']:.0f} compétences référencées",
            "badge-check",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Affectations 7 j",
            f"{EmployeesState.kpis['assignments']:.0f}",
            "chantiers",
            "Missions proposées ou confirmées",
            "calendar-clock",
            "h-4 w-4 text-lime-300",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full",
    )
