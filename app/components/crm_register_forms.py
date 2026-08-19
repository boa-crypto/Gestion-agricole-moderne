import reflex as rx

from app.states.crm_registers_state import CrmRegistersState, OptionRow


def _label(text: str) -> rx.Component:
    return rx.el.span(
        text,
        class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
    )


def _input(
    label: str,
    name: str,
    value: rx.Var,
    placeholder: str = "",
    input_type: str = "text",
    on_change: rx.event.EventType | None = None,
) -> rx.Component:
    return rx.el.label(
        _label(label),
        rx.el.input(
            name=name,
            type=input_type,
            placeholder=placeholder,
            default_value=value,
            on_change=on_change,
            class_name="w-full rounded-2xl border border-white/10 bg-white/[0.05] px-3 py-2 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/40 focus:outline-hidden mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0",
    )


def _enum_select(label: str, name: str, value: rx.Var, options: rx.Var):
    return rx.el.label(
        _label(label),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    options,
                    lambda item: rx.el.option(
                        item.replace("_", " ").lower(), value=item
                    ),
                ),
                name=name,
                default_value=value,
                key=f"{name}-{CrmRegistersState.form_kind}",
                class_name="w-full appearance-none rounded-2xl border border-white/10 bg-white/[0.05] px-3 py-2 pr-9 text-sm font-medium capitalize text-emerald-50 focus:border-lime-300/40 focus:outline-hidden",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-emerald-100/50",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0",
    )


def _option(item: OptionRow) -> rx.Component:
    return rx.el.option(item["label"], value=item["id"].to_string())


def _entity_select(
    label: str, name: str, placeholder: str, options: rx.Var
) -> rx.Component:
    return rx.el.label(
        _label(label),
        rx.el.div(
            rx.el.select(
                rx.el.option(placeholder, value=""),
                rx.foreach(options, _option),
                name=name,
                key=f"{name}-{CrmRegistersState.form_kind}",
                class_name="w-full appearance-none rounded-2xl border border-white/10 bg-white/[0.05] px-3 py-2 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/40 focus:outline-hidden",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-emerald-100/50",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0 sm:col-span-2",
    )


def _textarea(label: str, name: str, value: rx.Var) -> rx.Component:
    return rx.el.label(
        _label(label),
        rx.el.textarea(
            name=name,
            default_value=value,
            key=f"{name}-{CrmRegistersState.form_kind}",
            rows="3",
            class_name="w-full rounded-2xl border border-white/10 bg-white/[0.05] px-3 py-2 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/40 focus:outline-hidden mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0 sm:col-span-2 xl:col-span-3",
    )


def _transaction_fields() -> rx.Component:
    return rx.el.div(
        _entity_select(
            "Tiers *",
            "partner_id",
            "Sélectionner un client ou un fournisseur",
            CrmRegistersState.partner_options,
        ),
        _input(
            "Date de l'opération *",
            "operation_date",
            CrmRegistersState.form["operation_date"],
            input_type="date",
        ),
        _enum_select(
            "Statut",
            "status",
            CrmRegistersState.form["status"],
            CrmRegistersState.form_status_options,
        ),
        _input(
            "Objet de l'opération",
            "label",
            CrmRegistersState.form["label"],
            "Blé dur récolte 2026, engrais NPK...",
        ),
        _input(
            "Campagne",
            "season",
            CrmRegistersState.form["season"],
            "2025/2026",
        ),
        _input(
            "Quantité *",
            "quantity",
            CrmRegistersState.form["quantity"],
            "0",
            "number",
            lambda value: CrmRegistersState.update_form("quantity", value),
        ),
        _input("Unité", "unit", CrmRegistersState.form["unit"], "t, q, u, L"),
        _input(
            "Prix unitaire (DA) *",
            "unit_price",
            CrmRegistersState.form["unit_price"],
            "0",
            "number",
            lambda value: CrmRegistersState.update_form("unit_price", value),
        ),
        _input(
            "Remise (%)",
            "discount_percent",
            CrmRegistersState.form["discount_percent"],
            "0",
            "number",
            lambda value: CrmRegistersState.update_form(
                "discount_percent", value
            ),
        ),
        _input(
            "TVA (%)",
            "vat_rate",
            CrmRegistersState.form["vat_rate"],
            "19",
            "number",
            lambda value: CrmRegistersState.update_form("vat_rate", value),
        ),
        _enum_select(
            "Mode de règlement",
            "payment_method",
            CrmRegistersState.form["payment_method"],
            CrmRegistersState.method_options,
        ),
        rx.cond(
            CrmRegistersState.form_is_purchase,
            _enum_select(
                "Filière fournisseur",
                "domain",
                CrmRegistersState.form["domain"],
                CrmRegistersState.domain_options,
            ),
            rx.fragment(),
        ),
        _textarea("Notes", "notes", CrmRegistersState.form["notes"]),
        class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-5",
    )


def _payment_fields() -> rx.Component:
    return rx.el.div(
        _entity_select(
            "Tiers *",
            "partner_id",
            "Sélectionner le tiers réglé ou payeur",
            CrmRegistersState.partner_options,
        ),
        _enum_select(
            "Sens du règlement",
            "direction",
            CrmRegistersState.form["direction"],
            CrmRegistersState.direction_options,
        ),
        _entity_select(
            "Facture rattachée",
            "invoice_id",
            "Règlement sans facture",
            CrmRegistersState.invoice_options,
        ),
        _input(
            "Date du règlement *",
            "operation_date",
            CrmRegistersState.form["operation_date"],
            input_type="date",
        ),
        _input(
            "Montant (DA) *",
            "amount",
            CrmRegistersState.form["amount"],
            "0",
            "number",
        ),
        _enum_select(
            "Mode de paiement",
            "payment_method",
            CrmRegistersState.form["payment_method"],
            CrmRegistersState.method_options,
        ),
        _input(
            "Référence",
            "reference",
            CrmRegistersState.form["reference"],
            "N° de chèque, virement...",
        ),
        _input("Banque / caisse", "bank", CrmRegistersState.form["bank"]),
        _textarea("Commentaire", "notes", CrmRegistersState.form["notes"]),
        class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-5",
    )


def crm_register_form() -> rx.Component:
    return rx.cond(
        CrmRegistersState.form_open,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h3(
                            CrmRegistersState.form_title,
                            class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                        ),
                        rx.el.p(
                            "Les montants HT, TVA, TTC et le restant dû sont calculés automatiquement ; l'opération est journalisée dans l'historique du tiers.",
                            class_name="text-[11px] font-medium text-emerald-100/50 mt-1 max-w-xl",
                        ),
                        class_name="min-w-0",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4 text-emerald-100/70"),
                        type="button",
                        on_click=CrmRegistersState.close_form,
                        class_name="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/[0.05] hover:border-lime-300/35 transition-colors shrink-0",
                    ),
                    class_name="flex items-start justify-between gap-4 w-full",
                ),
                rx.el.form(
                    rx.cond(
                        CrmRegistersState.form_error != "",
                        rx.el.p(
                            CrmRegistersState.form_error,
                            class_name="w-full rounded-2xl border border-red-400/30 bg-red-400/[0.08] px-4 py-2.5 text-xs font-semibold text-red-200 mt-4",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        CrmRegistersState.form_is_payment,
                        _payment_fields(),
                        _transaction_fields(),
                    ),
                    rx.cond(
                        CrmRegistersState.form_is_payment,
                        rx.fragment(),
                        rx.el.div(
                            rx.icon(
                                "calculator",
                                class_name="h-3.5 w-3.5 text-lime-300",
                            ),
                            rx.el.span(
                                CrmRegistersState.form_preview,
                                class_name="text-xs font-semibold text-emerald-50",
                            ),
                            class_name="flex items-center gap-2 rounded-2xl border border-lime-300/25 bg-lime-300/[0.06] px-4 py-2.5 w-fit mt-4",
                        ),
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Annuler",
                            type="button",
                            on_click=CrmRegistersState.close_form,
                            class_name="rounded-full border border-white/10 bg-white/[0.05] px-5 py-2 text-xs font-semibold text-emerald-100/70 hover:border-lime-300/35 transition-colors w-fit",
                        ),
                        rx.el.button(
                            rx.cond(
                                CrmRegistersState.is_saving,
                                rx.icon(
                                    "loader-circle",
                                    class_name="h-4 w-4 animate-spin",
                                ),
                                rx.icon("check", class_name="h-4 w-4"),
                            ),
                            rx.el.span(
                                "Enregistrer",
                                class_name="text-xs font-semibold",
                            ),
                            type="submit",
                            class_name="flex items-center gap-2 rounded-full bg-lime-300 px-5 py-2 text-[#04140d] hover:bg-lime-200 transition-colors w-fit",
                        ),
                        class_name="flex flex-wrap items-center justify-end gap-2 w-full mt-6",
                    ),
                    on_submit=CrmRegistersState.save_operation,
                    class_name="w-full",
                ),
                class_name="w-full max-w-4xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/12 bg-[#06170f]/95 p-6 backdrop-blur-2xl",
            ),
            class_name="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 sm:p-8",
        ),
        rx.fragment(),
    )
