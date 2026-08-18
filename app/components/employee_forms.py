import reflex as rx

from app.components.guide_help import guide_error, help_icon_button
from app.states.employees_state import EmployeesState, Option

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"
_LABEL = "block text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45 mb-1.5"


def _field(label: str, control: rx.Component, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name=_LABEL),
        control,
        rx.el.p(
            hint, class_name="text-[10px] font-medium text-emerald-100/35 mt-1"
        ),
        class_name="w-full min-w-0",
    )


def _text(
    name: str, value: rx.Var, placeholder: str, kind: str = "text"
) -> rx.Component:
    return rx.el.input(
        type=kind,
        name=name,
        placeholder=placeholder,
        default_value=value,
        key=f"emp-{name}-{EmployeesState.form_key}",
        class_name=_INPUT,
    )


def _select(
    name: str, value: rx.Var, options: rx.Var[list[Option]]
) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"emp-{name}-{EmployeesState.form_key}",
            class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Prénom",
                _text(
                    "first_name",
                    EmployeesState.employee_form["first_name"],
                    "Camille",
                ),
                "Au moins 2 caractères.",
            ),
            _field(
                "Nom",
                _text(
                    "last_name",
                    EmployeesState.employee_form["last_name"],
                    "Roux",
                ),
            ),
            _field(
                "Matricule",
                _text(
                    "employee_code",
                    EmployeesState.employee_form["employee_code"],
                    "E08",
                ),
                "Identifiant court unique.",
            ),
            _field(
                "Poste",
                _text(
                    "job_title",
                    EmployeesState.employee_form["job_title"],
                    "Responsable cultures",
                ),
            ),
            _field(
                "Équipe / pôle",
                _text(
                    "team", EmployeesState.employee_form["team"], "Agronomie"
                ),
            ),
            _field(
                "Type de contrat",
                _select(
                    "contract_type",
                    EmployeesState.employee_form["contract_type"],
                    EmployeesState.contract_options,
                ),
            ),
            _field(
                "Statut",
                _select(
                    "status",
                    EmployeesState.employee_form["status"],
                    EmployeesState.status_options,
                ),
            ),
            _field(
                "E-mail",
                _text(
                    "email",
                    EmployeesState.employee_form["email"],
                    "prenom.nom@domaine-vegetal.fr",
                ),
            ),
            _field(
                "Téléphone",
                _text(
                    "phone",
                    EmployeesState.employee_form["phone"],
                    "06 12 34 56 78",
                ),
            ),
            _field(
                "Date d'embauche",
                _text(
                    "hired_on",
                    EmployeesState.employee_form["hired_on"],
                    "",
                    "date",
                ),
            ),
            _field(
                "Fin de contrat",
                _text(
                    "contract_end_on",
                    EmployeesState.employee_form["contract_end_on"],
                    "",
                    "date",
                ),
                "Laisser vide pour un CDI.",
            ),
            _field(
                "Heures hebdomadaires",
                _text(
                    "weekly_hours",
                    EmployeesState.employee_form["weekly_hours"],
                    "35",
                    "number",
                ),
                "Entre 1 et 60 h.",
            ),
            _field(
                "Coût horaire (€)",
                _text(
                    "hourly_cost",
                    EmployeesState.employee_form["hourly_cost"],
                    "22.5",
                    "number",
                ),
            ),
            _field(
                "Échéance Certiphyto",
                _text(
                    "phyto_certificate_expiry",
                    EmployeesState.employee_form["phyto_certificate_expiry"],
                    "",
                    "date",
                ),
            ),
            _field(
                "Contact d'urgence",
                _text(
                    "emergency_contact",
                    EmployeesState.employee_form["emergency_contact"],
                    "Nom · téléphone",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        rx.el.div(
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    name="has_driving_licence",
                    default_value="1",
                    default_checked=EmployeesState.employee_form[
                        "has_driving_licence"
                    ]
                    == "1",
                    key=f"emp-licence-{EmployeesState.form_key}",
                    class_name="h-4 w-4 accent-lime-300 cursor-pointer",
                ),
                rx.el.span(
                    "Titulaire du permis de conduire",
                    class_name="text-sm font-medium text-emerald-100/75",
                ),
                class_name="flex items-center gap-2.5 cursor-pointer w-fit",
            ),
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    name="has_phyto_certificate",
                    default_value="1",
                    default_checked=EmployeesState.employee_form[
                        "has_phyto_certificate"
                    ]
                    == "1",
                    key=f"emp-phyto-{EmployeesState.form_key}",
                    class_name="h-4 w-4 accent-lime-300 cursor-pointer",
                ),
                rx.el.span(
                    "Certiphyto en cours de validité",
                    class_name="text-sm font-medium text-emerald-100/75",
                ),
                class_name="flex items-center gap-2.5 cursor-pointer w-fit",
            ),
            class_name="flex flex-wrap items-center gap-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
        ),
        _field(
            "Notes RH",
            rx.el.textarea(
                name="notes",
                placeholder="Habilitations, souhaits d'évolution, contraintes…",
                default_value=EmployeesState.employee_form["notes"],
                key=f"emp-notes-{EmployeesState.form_key}",
                rows="3",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def employee_modals() -> rx.Component:
    return rx.cond(
        EmployeesState.show_employee_form,
        rx.el.div(
            rx.el.div(
                rx.el.form(
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "user-round",
                                    class_name="h-4 w-4 text-lime-300",
                                ),
                                rx.el.span(
                                    "Fiche salarié",
                                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                                ),
                                class_name="flex items-center gap-2",
                            ),
                            rx.el.h2(
                                EmployeesState.employee_form_title,
                                class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                            ),
                            class_name="min-w-0 flex-1",
                        ),
                        help_icon_button("employes"),
                        class_name="flex items-start gap-3 w-full",
                    ),
                    _body(),
                    guide_error(
                        EmployeesState.form_error, "employes", "habilitation"
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Annuler",
                            type="button",
                            on_click=EmployeesState.close_employee_form,
                            class_name="rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-semibold text-emerald-100/70 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                        ),
                        rx.el.button(
                            rx.icon(
                                "check", class_name="h-4 w-4 text-[#04140d]"
                            ),
                            rx.el.span(
                                "Enregistrer la fiche",
                                class_name="text-[#04140d]",
                            ),
                            type="submit",
                            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-5 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                        ),
                        class_name="flex items-center justify-end gap-3 mt-6 border-t border-white/10 pt-5",
                    ),
                    on_submit=EmployeesState.submit_employee,
                    reset_on_submit=True,
                    class_name="w-full",
                ),
                class_name="w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#061a11]/95 p-7 backdrop-blur-2xl",
            ),
            class_name="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm",
        ),
        rx.fragment(),
    )
