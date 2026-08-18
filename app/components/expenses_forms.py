import reflex as rx

from app.components.guide_help import guide_error, help_icon_button
from app.states.expenses_state import ExpensesState, Option

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden transition-colors"
_SELECT = f"{_INPUT} appearance-none cursor-pointer pr-9"
_LABEL = (
    "text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45"
)


def _field(label: str, control: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.span(label, class_name=_LABEL),
        rx.el.div(control, class_name="w-full mt-2"),
        class_name="w-full min-w-0",
    )


def _text_input(
    name: str,
    placeholder: str,
    value: rx.Var | str = "",
    input_type: str = "text",
) -> rx.Component:
    return rx.el.input(
        type=input_type,
        name=name,
        placeholder=placeholder,
        default_value=value,
        key=f"{name}-{ExpensesState.form_key}",
        class_name=_INPUT,
    )


def _select_input(
    name: str,
    value: rx.Var | str,
    options: rx.Var,
    empty_label: str = "",
) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.cond(
                empty_label != "",
                rx.el.option(empty_label, value=""),
                rx.fragment(),
            ),
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"{name}-{ExpensesState.form_key}",
            class_name=_SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _error(message: rx.Var, topic: str = "montant") -> rx.Component:
    return guide_error(message, "charges", topic)


def _shell(
    open_var: rx.Var,
    title: rx.Var | str,
    subtitle: str,
    icon: str,
    body: rx.Component,
    on_close: rx.event.EventType,
) -> rx.Component:
    return rx.cond(
        open_var,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.icon(icon, class_name="h-5 w-5 text-[#04140d]"),
                            class_name="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-lime-300",
                        ),
                        rx.el.div(
                            rx.el.h3(
                                title,
                                class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                            ),
                            rx.el.p(
                                subtitle,
                                class_name="text-[11px] font-medium text-emerald-100/50 mt-1",
                            ),
                            class_name="min-w-0",
                        ),
                        class_name="flex items-center gap-3 min-w-0",
                    ),
                    rx.el.div(
                        help_icon_button("charges"),
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            on_click=on_close,
                            type="button",
                            class_name="flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-emerald-100/60 hover:text-emerald-50 transition-colors",
                        ),
                        class_name="flex items-center gap-2 ml-auto shrink-0",
                    ),
                    class_name="flex items-center gap-3 w-full pb-5 border-b border-white/10",
                ),
                body,
                class_name="w-full max-w-4xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#04140d]/95 p-6 backdrop-blur-2xl",
            ),
            class_name="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4",
        ),
        rx.fragment(),
    )


def expense_form_dialog() -> rx.Component:
    return _shell(
        ExpensesState.show_expense_form,
        ExpensesState.expense_form_title,
        "Montants, échéances et rattachement métier de la ligne de charge.",
        "receipt-text",
        rx.el.form(
            rx.el.div(
                _field(
                    "Type de charge",
                    _select_input(
                        "expense_type_id",
                        ExpensesState.expense_form["expense_type_id"],
                        ExpensesState.type_options,
                        "Sélectionner un type",
                    ),
                ),
                _field(
                    "Intitulé",
                    _text_input(
                        "label",
                        "Ex. GNR - remplissage cuve",
                        ExpensesState.expense_form["label"],
                    ),
                ),
                _field(
                    "Fournisseur",
                    _text_input(
                        "supplier",
                        "Fournisseur",
                        ExpensesState.expense_form["supplier"],
                    ),
                ),
                _field(
                    "Référence interne",
                    _text_input(
                        "reference",
                        "BL / bon de commande",
                        ExpensesState.expense_form["reference"],
                    ),
                ),
                _field(
                    "Numéro de facture",
                    _text_input(
                        "invoice_reference",
                        "FACT-0000",
                        ExpensesState.expense_form["invoice_reference"],
                    ),
                ),
                _field(
                    "Statut",
                    _select_input(
                        "status",
                        ExpensesState.expense_form["status"],
                        ExpensesState.status_options,
                    ),
                ),
                _field(
                    "Mode de paiement",
                    _select_input(
                        "payment_method",
                        ExpensesState.expense_form["payment_method"],
                        ExpensesState.payment_options,
                    ),
                ),
                _field(
                    "Quantité",
                    _text_input(
                        "quantity",
                        "1",
                        ExpensesState.expense_form["quantity"],
                        "number",
                    ),
                ),
                _field(
                    "Unité",
                    _text_input(
                        "unit",
                        "L, ha, h, forfait…",
                        ExpensesState.expense_form["unit"],
                    ),
                ),
                _field(
                    "Montant HT (€)",
                    _text_input(
                        "amount_ht",
                        "0.00",
                        ExpensesState.expense_form["amount_ht"],
                        "number",
                    ),
                ),
                _field(
                    "TVA (%)",
                    _text_input(
                        "vat_rate",
                        "20",
                        ExpensesState.expense_form["vat_rate"],
                        "number",
                    ),
                ),
                _field(
                    "Date d'engagement",
                    _text_input(
                        "incurred_on",
                        "",
                        ExpensesState.expense_form["incurred_on"],
                        "date",
                    ),
                ),
                _field(
                    "Échéance de règlement",
                    _text_input(
                        "due_date",
                        "",
                        ExpensesState.expense_form["due_date"],
                        "date",
                    ),
                ),
                _field(
                    "Date de paiement",
                    _text_input(
                        "paid_on",
                        "",
                        ExpensesState.expense_form["paid_on"],
                        "date",
                    ),
                ),
                class_name="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5",
            ),
            rx.el.div(
                rx.el.span(
                    "Rattachement métier (facultatif)",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.div(
                    _field(
                        "Parcelle",
                        _select_input(
                            "parcel_id",
                            ExpensesState.expense_form["parcel_id"],
                            ExpensesState.parcel_options,
                            "Aucune parcelle",
                        ),
                    ),
                    _field(
                        "Culture",
                        _select_input(
                            "crop_id",
                            ExpensesState.expense_form["crop_id"],
                            ExpensesState.crop_options,
                            "Aucune culture",
                        ),
                    ),
                    _field(
                        "Salarié",
                        _select_input(
                            "employee_id",
                            ExpensesState.expense_form["employee_id"],
                            ExpensesState.employee_options,
                            "Aucun salarié",
                        ),
                    ),
                    _field(
                        "Engin",
                        _select_input(
                            "equipment_id",
                            ExpensesState.expense_form["equipment_id"],
                            ExpensesState.equipment_options,
                            "Aucun engin",
                        ),
                    ),
                    _field(
                        "Intervention",
                        _select_input(
                            "intervention_id",
                            ExpensesState.expense_form["intervention_id"],
                            ExpensesState.intervention_options,
                            "Aucune intervention",
                        ),
                    ),
                    _field(
                        "Opération de maintenance",
                        _select_input(
                            "maintenance_id",
                            ExpensesState.expense_form["maintenance_id"],
                            ExpensesState.maintenance_options,
                            "Aucune opération",
                        ),
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3",
                ),
                class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
            ),
            _field(
                "Commentaire",
                rx.el.textarea(
                    name="notes",
                    placeholder="Contexte, chantier concerné, condition de règlement…",
                    default_value=ExpensesState.expense_form["notes"],
                    key=f"exp-notes-{ExpensesState.form_key}",
                    rows="3",
                    class_name=_INPUT,
                ),
            ),
            _error(ExpensesState.expense_error, "montant"),
            rx.el.div(
                rx.el.button(
                    rx.el.span("Annuler"),
                    type="button",
                    on_click=ExpensesState.close_expense_form,
                    class_name="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:text-emerald-50 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("check", class_name="h-4 w-4 text-[#04140d]"),
                    rx.el.span(
                        "Enregistrer la dépense", class_name="text-[#04140d]"
                    ),
                    type="submit",
                    class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center justify-end gap-2 mt-5",
            ),
            on_submit=ExpensesState.submit_expense,
            class_name="w-full",
        ),
        ExpensesState.close_expense_form,
    )


def _icon_option(opt: Option) -> rx.Component:
    return rx.el.option(opt["label"], value=opt["value"])


ICON_CHOICES: list[Option] = [
    {"value": "receipt-text", "label": "Facture"},
    {"value": "flask-conical", "label": "Intrants"},
    {"value": "fuel", "label": "Carburant"},
    {"value": "wrench", "label": "Atelier"},
    {"value": "users-round", "label": "Main d'œuvre"},
    {"value": "handshake", "label": "Prestation"},
    {"value": "shield-check", "label": "Assurance"},
    {"value": "zap", "label": "Énergie"},
    {"value": "file-text", "label": "Administratif"},
    {"value": "truck", "label": "Transport"},
]


def type_form_dialog() -> rx.Component:
    return _shell(
        ExpensesState.show_type_form,
        ExpensesState.type_form_title,
        "Personnalisez le plan de charges de l'exploitation.",
        "tags",
        rx.el.form(
            rx.el.div(
                _field(
                    "Nom du type",
                    _text_input(
                        "name",
                        "Ex. Semences fermières",
                        ExpensesState.type_form["name"],
                    ),
                ),
                _field(
                    "Code",
                    _text_input(
                        "code", "SEMF", ExpensesState.type_form["code"]
                    ),
                ),
                _field(
                    "Catégorie comptable",
                    _text_input(
                        "category",
                        "Production végétale",
                        ExpensesState.type_form["category"],
                    ),
                ),
                _field(
                    "Mode de paiement par défaut",
                    _select_input(
                        "default_payment_method",
                        ExpensesState.type_form["default_payment_method"],
                        ExpensesState.payment_options,
                    ),
                ),
                _field(
                    "TVA par défaut (%)",
                    _text_input(
                        "default_vat_rate",
                        "20",
                        ExpensesState.type_form["default_vat_rate"],
                        "number",
                    ),
                ),
                _field(
                    "Couleur du registre",
                    _text_input(
                        "color_hex",
                        "#a3e635",
                        ExpensesState.type_form["color_hex"],
                    ),
                ),
                _field(
                    "Icône",
                    rx.el.div(
                        rx.el.select(
                            rx.foreach(ICON_CHOICES, _icon_option),
                            name="icon",
                            default_value=ExpensesState.type_form["icon"],
                            key=f"type-icon-{ExpensesState.form_key}",
                            class_name=_SELECT,
                        ),
                        rx.icon(
                            "chevron-down",
                            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                        ),
                        class_name="relative w-full",
                    ),
                ),
                class_name="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5",
            ),
            _field(
                "Description",
                rx.el.textarea(
                    name="description",
                    placeholder="Nature des charges regroupées dans ce type…",
                    default_value=ExpensesState.type_form["description"],
                    key=f"type-desc-{ExpensesState.form_key}",
                    rows="3",
                    class_name=_INPUT,
                ),
            ),
            _error(ExpensesState.type_error, "montant"),
            rx.el.div(
                rx.el.button(
                    rx.el.span("Annuler"),
                    type="button",
                    on_click=ExpensesState.close_type_form,
                    class_name="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:text-emerald-50 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("check", class_name="h-4 w-4 text-[#04140d]"),
                    rx.el.span(
                        "Enregistrer le type", class_name="text-[#04140d]"
                    ),
                    type="submit",
                    class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center justify-end gap-2 mt-5",
            ),
            on_submit=ExpensesState.submit_type,
            class_name="w-full",
        ),
        ExpensesState.close_type_form,
    )
