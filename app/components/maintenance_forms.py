import reflex as rx

from app.components.guide_help import guide_error, help_icon_button
from app.states.maintenance_state import MaintenanceState, Option

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"
_LABEL = "block text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45 mb-1.5"


def _field(label: str, control: rx.Component, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name=_LABEL),
        control,
        rx.el.p(
            hint,
            class_name="text-[10px] font-medium text-emerald-100/35 mt-1",
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
        key=f"mnt-{name}-{MaintenanceState.form_key}",
        class_name=_INPUT,
    )


def _select(
    name: str,
    value: rx.Var,
    options: rx.Var[list[Option]],
    first_option: rx.Component = rx.fragment(),
) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            first_option,
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"mnt-{name}-{MaintenanceState.form_key}",
            class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _modal_shell(
    title: rx.Var | str,
    subtitle: str,
    icon: str,
    body: rx.Component,
    error: rx.Var,
    submit_label: str,
    on_submit: rx.event.EventType,
    on_close: rx.event.EventType,
    topic: str = "maintenance",
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.form(
                rx.el.div(
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
                        class_name="min-w-0 flex-1",
                    ),
                    help_icon_button("maintenance"),
                    class_name="flex items-start gap-3 w-full",
                ),
                body,
                guide_error(error, "maintenance", topic),
                rx.el.div(
                    rx.el.button(
                        "Annuler",
                        type="button",
                        on_click=on_close,
                        class_name="rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-semibold text-emerald-100/70 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon("check", class_name="h-4 w-4 text-[#04140d]"),
                        rx.el.span(submit_label, class_name="text-[#04140d]"),
                        type="submit",
                        class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-5 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                    ),
                    class_name="flex items-center justify-end gap-3 mt-6 border-t border-white/10 pt-5",
                ),
                on_submit=on_submit,
                reset_on_submit=True,
                class_name="w-full",
            ),
            class_name="w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#061a11]/95 p-7 backdrop-blur-2xl",
        ),
        class_name="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm",
    )


def _equipment_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Nom de l'engin",
                _text(
                    "name",
                    MaintenanceState.equipment_form["name"],
                    "Tracteur John Deere 6155R",
                ),
                "Au moins 2 caractères.",
            ),
            _field(
                "Code interne",
                _text("code", MaintenanceState.equipment_form["code"], "M09"),
                "Identifiant court unique.",
            ),
            _field(
                "Catégorie",
                _select(
                    "category",
                    MaintenanceState.equipment_form["category"],
                    MaintenanceState.category_options,
                ),
            ),
            _field(
                "Statut",
                _select(
                    "status",
                    MaintenanceState.equipment_form["status"],
                    MaintenanceState.status_options,
                ),
            ),
            _field(
                "Mode de détention",
                _select(
                    "ownership",
                    MaintenanceState.equipment_form["ownership"],
                    MaintenanceState.ownership_options,
                ),
            ),
            _field(
                "Responsable",
                _select(
                    "responsible_id",
                    MaintenanceState.equipment_form["responsible_id"],
                    MaintenanceState.employee_options,
                    rx.el.option("Sans responsable", value=""),
                ),
                "Salarié référent de la machine.",
            ),
            _field(
                "Marque",
                _text(
                    "brand",
                    MaintenanceState.equipment_form["brand"],
                    "John Deere",
                ),
            ),
            _field(
                "Modèle",
                _text(
                    "model", MaintenanceState.equipment_form["model"], "6155R"
                ),
            ),
            _field(
                "Numéro de série",
                _text(
                    "serial_number",
                    MaintenanceState.equipment_form["serial_number"],
                    "JD6155R-88421",
                ),
            ),
            _field(
                "Immatriculation",
                _text(
                    "registration",
                    MaintenanceState.equipment_form["registration"],
                    "AE-441-KL",
                ),
            ),
            _field(
                "Année",
                _text(
                    "year",
                    MaintenanceState.equipment_form["year"],
                    "2019",
                    "number",
                ),
                "Laisser vide si inconnue.",
            ),
            _field(
                "Puissance (ch)",
                _text(
                    "power_hp",
                    MaintenanceState.equipment_form["power_hp"],
                    "155",
                    "number",
                ),
            ),
            _field(
                "Largeur de travail (m)",
                _text(
                    "working_width_m",
                    MaintenanceState.equipment_form["working_width_m"],
                    "4.5",
                    "number",
                ),
            ),
            _field(
                "Unité de compteur",
                _select(
                    "usage_unit",
                    MaintenanceState.equipment_form["usage_unit"],
                    MaintenanceState.usage_unit_options,
                ),
            ),
            _field(
                "Compteur actuel",
                _text(
                    "usage_counter",
                    MaintenanceState.equipment_form["usage_counter"],
                    "4820",
                    "number",
                ),
            ),
            _field(
                "Emplacement",
                _text(
                    "storage_location",
                    MaintenanceState.equipment_form["storage_location"],
                    "Hangar A - travée 1",
                ),
            ),
            _field(
                "Date d'acquisition",
                _text(
                    "purchase_date",
                    MaintenanceState.equipment_form["purchase_date"],
                    "",
                    "date",
                ),
            ),
            _field(
                "Prix d'achat (€)",
                _text(
                    "purchase_price",
                    MaintenanceState.equipment_form["purchase_price"],
                    "128000",
                    "number",
                ),
            ),
            _field(
                "Valeur résiduelle (€)",
                _text(
                    "residual_value",
                    MaintenanceState.equipment_form["residual_value"],
                    "62000",
                    "number",
                ),
            ),
            _field(
                "Coût horaire (€)",
                _text(
                    "hourly_cost",
                    MaintenanceState.equipment_form["hourly_cost"],
                    "34.5",
                    "number",
                ),
            ),
            _field(
                "Consommation (L/h)",
                _text(
                    "fuel_consumption_l_h",
                    MaintenanceState.equipment_form["fuel_consumption_l_h"],
                    "17.5",
                    "number",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        rx.el.div(
            rx.el.span(
                "Échéances réglementaires et entretien préventif",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
            ),
            rx.el.div(
                _field(
                    "Échéance d'assurance",
                    _text(
                        "insurance_expiry",
                        MaintenanceState.equipment_form["insurance_expiry"],
                        "",
                        "date",
                    ),
                ),
                _field(
                    "Contrôle réglementaire",
                    _text(
                        "inspection_expiry",
                        MaintenanceState.equipment_form["inspection_expiry"],
                        "",
                        "date",
                    ),
                    "VGP, contrôle pulvé, mines…",
                ),
                _field(
                    "Prochain entretien",
                    _text(
                        "next_service_date",
                        MaintenanceState.equipment_form["next_service_date"],
                        "",
                        "date",
                    ),
                ),
                _field(
                    "Seuil compteur entretien",
                    _text(
                        "next_service_counter",
                        MaintenanceState.equipment_form["next_service_counter"],
                        "5000",
                        "number",
                    ),
                ),
                _field(
                    "Intervalle (jours)",
                    _text(
                        "service_interval_days",
                        MaintenanceState.equipment_form[
                            "service_interval_days"
                        ],
                        "180",
                        "number",
                    ),
                    "Utilisé pour recalculer l'échéance après réalisation.",
                ),
                _field(
                    "Intervalle (compteur)",
                    _text(
                        "service_interval_counter",
                        MaintenanceState.equipment_form[
                            "service_interval_counter"
                        ],
                        "500",
                        "number",
                    ),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-3",
            ),
            class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
        ),
        _field(
            "Notes atelier",
            rx.el.textarea(
                name="notes",
                placeholder="Équipements embarqués, historique, contraintes…",
                default_value=MaintenanceState.equipment_form["notes"],
                key=f"mnt-eq-notes-{MaintenanceState.form_key}",
                rows="3",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def _operation_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Intitulé de l'opération",
                _text(
                    "title",
                    MaintenanceState.operation_form["title"],
                    "Vidange 500 h et filtration",
                ),
                "Au moins 3 caractères.",
            ),
            _field(
                "Engin",
                _select(
                    "equipment_id",
                    MaintenanceState.operation_form["equipment_id"],
                    MaintenanceState.equipment_options,
                ),
            ),
            _field(
                "Plan d'entretien lié",
                _select(
                    "schedule_id",
                    MaintenanceState.operation_form["schedule_id"],
                    MaintenanceState.schedule_options,
                    rx.el.option("Hors plan préventif", value=""),
                ),
                "Le plan est recalé à la réalisation.",
            ),
            _field(
                "Nature",
                _select(
                    "kind",
                    MaintenanceState.operation_form["kind"],
                    MaintenanceState.kind_options,
                ),
            ),
            _field(
                "Statut",
                _select(
                    "status",
                    MaintenanceState.operation_form["status"],
                    MaintenanceState.op_status_options,
                ),
            ),
            _field(
                "Priorité",
                _select(
                    "priority",
                    MaintenanceState.operation_form["priority"],
                    MaintenanceState.priority_options,
                ),
            ),
            _field(
                "Date planifiée",
                _text(
                    "scheduled_date",
                    MaintenanceState.operation_form["scheduled_date"],
                    "",
                    "date",
                ),
                "Obligatoire.",
            ),
            _field(
                "Échéance limite",
                _text(
                    "due_date",
                    MaintenanceState.operation_form["due_date"],
                    "",
                    "date",
                ),
            ),
            _field(
                "Date de réalisation",
                _text(
                    "done_date",
                    MaintenanceState.operation_form["done_date"],
                    "",
                    "date",
                ),
                "Renseignée automatiquement si réalisée.",
            ),
            _field(
                "Responsable",
                _select(
                    "responsible_id",
                    MaintenanceState.operation_form["responsible_id"],
                    MaintenanceState.employee_options,
                    rx.el.option("Sans responsable", value=""),
                ),
                "Une affectation est créée pour ce salarié.",
            ),
            _field(
                "Compteur au passage",
                _text(
                    "counter_at_service",
                    MaintenanceState.operation_form["counter_at_service"],
                    "4820",
                    "number",
                ),
            ),
            _field(
                "Immobilisation (h)",
                _text(
                    "downtime_hours",
                    MaintenanceState.operation_form["downtime_hours"],
                    "5",
                    "number",
                ),
            ),
            _field(
                "Main d'œuvre (h)",
                _text(
                    "labor_hours",
                    MaintenanceState.operation_form["labor_hours"],
                    "4",
                    "number",
                ),
            ),
            _field(
                "Coût main d'œuvre (€)",
                _text(
                    "labor_cost",
                    MaintenanceState.operation_form["labor_cost"],
                    "100",
                    "number",
                ),
            ),
            _field(
                "Coût pièces (€)",
                _text(
                    "parts_cost",
                    MaintenanceState.operation_form["parts_cost"],
                    "390",
                    "number",
                ),
            ),
            _field(
                "Coût externe (€)",
                _text(
                    "external_cost",
                    MaintenanceState.operation_form["external_cost"],
                    "0",
                    "number",
                ),
            ),
            _field(
                "Prestataire",
                _text(
                    "provider",
                    MaintenanceState.operation_form["provider"],
                    "Claas Service Beauce",
                ),
                "Obligatoire si opération externalisée.",
            ),
            _field(
                "Référence facture",
                _text(
                    "invoice_reference",
                    MaintenanceState.operation_form["invoice_reference"],
                    "FA-2291",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        rx.el.div(
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    name="is_internal",
                    default_value="1",
                    default_checked=MaintenanceState.operation_form[
                        "is_internal"
                    ]
                    == "1",
                    key=f"mnt-internal-{MaintenanceState.form_key}",
                    class_name="h-4 w-4 accent-lime-300 cursor-pointer",
                ),
                rx.el.span(
                    "Opération réalisée à l'atelier interne",
                    class_name="text-sm font-medium text-emerald-100/75",
                ),
                class_name="flex items-center gap-2.5 cursor-pointer w-fit",
            ),
            rx.el.p(
                "Si le statut est « Réalisée », les échéances de l'engin et du plan préventif sont recalculées automatiquement.",
                class_name="text-[10px] font-medium text-lime-200/70 mt-3",
            ),
            class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
        ),
        rx.el.div(
            _field(
                "Constat de panne",
                rx.el.textarea(
                    name="failure_description",
                    placeholder="Symptômes, circonstances…",
                    default_value=MaintenanceState.operation_form[
                        "failure_description"
                    ],
                    key=f"mnt-failure-{MaintenanceState.form_key}",
                    rows="3",
                    class_name=f"{_INPUT} resize-y",
                ),
            ),
            _field(
                "Travaux réalisés",
                rx.el.textarea(
                    name="work_performed",
                    placeholder="Pièces remplacées, réglages…",
                    default_value=MaintenanceState.operation_form[
                        "work_performed"
                    ],
                    key=f"mnt-work-{MaintenanceState.form_key}",
                    rows="3",
                    class_name=f"{_INPUT} resize-y",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5",
        ),
        _field(
            "Notes",
            rx.el.textarea(
                name="notes",
                placeholder="Commande de pièces, disponibilité de l'engin…",
                default_value=MaintenanceState.operation_form["notes"],
                key=f"mnt-op-notes-{MaintenanceState.form_key}",
                rows="2",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def maintenance_modals() -> rx.Component:
    return rx.fragment(
        rx.cond(
            MaintenanceState.show_equipment_form,
            _modal_shell(
                MaintenanceState.equipment_form_title,
                "Fiche engin",
                "tractor",
                _equipment_body(),
                MaintenanceState.form_error,
                "Enregistrer l'engin",
                MaintenanceState.submit_equipment,
                MaintenanceState.close_equipment_form,
                topic="maintenance",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MaintenanceState.show_operation_form,
            _modal_shell(
                MaintenanceState.operation_form_title,
                "Opération de maintenance",
                "wrench",
                _operation_body(),
                MaintenanceState.operation_error,
                "Enregistrer l'opération",
                MaintenanceState.submit_operation,
                MaintenanceState.close_operation_form,
                topic="dates",
            ),
            rx.fragment(),
        ),
    )
