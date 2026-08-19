import reflex as rx

from app.states.crm_partners_state import CrmPartnersState


def _text_field(
    label: str,
    name: str,
    value: rx.Var,
    placeholder: str = "",
    input_type: str = "text",
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
        ),
        rx.el.input(
            name=name,
            type=input_type,
            placeholder=placeholder,
            default_value=value,
            key=f"{name}-{value}",
            class_name="w-full rounded-2xl border border-white/10 bg-white/[0.05] px-3 py-2 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/40 focus:outline-hidden mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0",
    )


def _select_field(
    label: str, name: str, value: rx.Var, options: rx.Var
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
        ),
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
                key=f"{name}-{value}",
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


def _textarea_field(label: str, name: str, value: rx.Var) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
        ),
        rx.el.textarea(
            name=name,
            default_value=value,
            key=f"{name}-{value}",
            rows="3",
            class_name="w-full rounded-2xl border border-white/10 bg-white/[0.05] px-3 py-2 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/40 focus:outline-hidden mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0 sm:col-span-2 xl:col-span-3",
    )


def _modal(
    title: rx.Var | str,
    subtitle: str,
    body: rx.Component,
    on_close: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
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
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4 text-emerald-100/70"),
                    type="button",
                    on_click=on_close,
                    class_name="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/[0.05] hover:border-lime-300/35 transition-colors shrink-0",
                ),
                class_name="flex items-start justify-between gap-4 w-full",
            ),
            body,
            class_name="w-full max-w-4xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/12 bg-[#06170f]/95 p-6 backdrop-blur-2xl",
        ),
        class_name="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 sm:p-8",
    )


def crm_partner_form() -> rx.Component:
    return rx.cond(
        CrmPartnersState.form_open,
        _modal(
            CrmPartnersState.form_title,
            "Identité, coordonnées, identifiants fiscaux et conditions commerciales du tiers.",
            rx.el.form(
                rx.cond(
                    CrmPartnersState.form_error != "",
                    rx.el.p(
                        CrmPartnersState.form_error,
                        class_name="w-full rounded-2xl border border-red-400/30 bg-red-400/[0.08] px-4 py-2.5 text-xs font-semibold text-red-200 mt-4",
                    ),
                    rx.fragment(),
                ),
                rx.el.div(
                    _text_field(
                        "Raison sociale *",
                        "legal_name",
                        CrmPartnersState.form["legal_name"],
                        "Nom légal du tiers",
                    ),
                    _text_field(
                        "Nom commercial",
                        "trade_name",
                        CrmPartnersState.form["trade_name"],
                    ),
                    _select_field(
                        "Type de tiers",
                        "kind",
                        CrmPartnersState.form["kind"],
                        CrmPartnersState.kind_options,
                    ),
                    _select_field(
                        "Forme juridique",
                        "legal_form",
                        CrmPartnersState.form["legal_form"],
                        CrmPartnersState.legal_form_options,
                    ),
                    _select_field(
                        "Statut",
                        "status",
                        CrmPartnersState.form["status"],
                        CrmPartnersState.status_options,
                    ),
                    _select_field(
                        "Filière fournisseur",
                        "supplier_domain",
                        CrmPartnersState.form["supplier_domain"],
                        CrmPartnersState.domain_options,
                    ),
                    _text_field(
                        "Catégorie",
                        "category",
                        CrmPartnersState.form["category"],
                        "Grossiste céréales, engrais...",
                    ),
                    _text_field(
                        "Segment",
                        "segment",
                        CrmPartnersState.form["segment"],
                    ),
                    _text_field(
                        "Adresse",
                        "address",
                        CrmPartnersState.form["address"],
                    ),
                    _text_field(
                        "Wilaya", "wilaya", CrmPartnersState.form["wilaya"]
                    ),
                    _text_field(
                        "Commune", "commune", CrmPartnersState.form["commune"]
                    ),
                    _text_field(
                        "Code postal",
                        "postal_code",
                        CrmPartnersState.form["postal_code"],
                    ),
                    _text_field(
                        "Pays", "country", CrmPartnersState.form["country"]
                    ),
                    _text_field(
                        "Téléphone", "phone", CrmPartnersState.form["phone"]
                    ),
                    _text_field(
                        "Téléphone secondaire",
                        "phone_secondary",
                        CrmPartnersState.form["phone_secondary"],
                    ),
                    _text_field(
                        "WhatsApp",
                        "whatsapp",
                        CrmPartnersState.form["whatsapp"],
                    ),
                    _text_field(
                        "E-mail",
                        "email",
                        CrmPartnersState.form["email"],
                        "contact@exemple.dz",
                    ),
                    _text_field(
                        "Site web", "website", CrmPartnersState.form["website"]
                    ),
                    _text_field("NIF", "nif", CrmPartnersState.form["nif"]),
                    _text_field("NIS", "nis", CrmPartnersState.form["nis"]),
                    _text_field(
                        "Registre de commerce",
                        "trade_register",
                        CrmPartnersState.form["trade_register"],
                    ),
                    _text_field(
                        "Identifiant fiscal",
                        "tax_id",
                        CrmPartnersState.form["tax_id"],
                    ),
                    _text_field(
                        "Conditions de paiement",
                        "payment_terms",
                        CrmPartnersState.form["payment_terms"],
                        "30 jours fin de mois",
                    ),
                    _text_field(
                        "Délai de paiement (jours)",
                        "payment_delay_days",
                        CrmPartnersState.form["payment_delay_days"],
                        "30",
                        "number",
                    ),
                    _text_field(
                        "Limite de crédit (DA)",
                        "credit_limit",
                        CrmPartnersState.form["credit_limit"],
                        "0",
                        "number",
                    ),
                    _text_field(
                        "Remise habituelle (%)",
                        "default_discount_percent",
                        CrmPartnersState.form["default_discount_percent"],
                        "0",
                        "number",
                    ),
                    _text_field(
                        "TVA par défaut (%)",
                        "default_vat_rate",
                        CrmPartnersState.form["default_vat_rate"],
                        "19",
                        "number",
                    ),
                    _text_field(
                        "Devise", "currency", CrmPartnersState.form["currency"]
                    ),
                    _select_field(
                        "Mode de paiement préféré",
                        "preferred_payment_method",
                        CrmPartnersState.form["preferred_payment_method"],
                        CrmPartnersState.payment_method_options,
                    ),
                    _text_field(
                        "Personne de contact",
                        "primary_contact_name",
                        CrmPartnersState.form["primary_contact_name"],
                    ),
                    _text_field(
                        "Fonction du contact",
                        "primary_contact_role",
                        CrmPartnersState.form["primary_contact_role"],
                    ),
                    _text_field(
                        "Étiquettes", "tags", CrmPartnersState.form["tags"]
                    ),
                    _textarea_field(
                        "Notes internes",
                        "notes",
                        CrmPartnersState.form["notes"],
                    ),
                    class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-5",
                ),
                rx.el.div(
                    rx.el.button(
                        "Annuler",
                        type="button",
                        on_click=CrmPartnersState.close_form,
                        class_name="rounded-full border border-white/10 bg-white/[0.05] px-5 py-2 text-xs font-semibold text-emerald-100/70 hover:border-lime-300/35 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.cond(
                            CrmPartnersState.is_saving,
                            rx.icon(
                                "loader-circle",
                                class_name="h-4 w-4 animate-spin",
                            ),
                            rx.icon("check", class_name="h-4 w-4"),
                        ),
                        rx.el.span(
                            "Enregistrer", class_name="text-xs font-semibold"
                        ),
                        type="submit",
                        class_name="flex items-center gap-2 rounded-full bg-lime-300 px-5 py-2 text-[#04140d] hover:bg-lime-200 transition-colors w-fit",
                    ),
                    class_name="flex flex-wrap items-center justify-end gap-2 w-full mt-6",
                ),
                on_submit=CrmPartnersState.save_partner,
                class_name="w-full",
            ),
            CrmPartnersState.close_form,
        ),
        rx.fragment(),
    )


def crm_contact_form() -> rx.Component:
    return rx.cond(
        CrmPartnersState.contact_form_open,
        _modal(
            "Contact du tiers",
            "Un tiers peut porter plusieurs contacts : un seul est le contact principal.",
            rx.el.form(
                rx.el.div(
                    _text_field(
                        "Nom *",
                        "last_name",
                        CrmPartnersState.contact_form["last_name"],
                    ),
                    _text_field(
                        "Prénom",
                        "first_name",
                        CrmPartnersState.contact_form["first_name"],
                    ),
                    _text_field(
                        "Fonction",
                        "role",
                        CrmPartnersState.contact_form["role"],
                    ),
                    _text_field(
                        "Téléphone",
                        "phone",
                        CrmPartnersState.contact_form["phone"],
                    ),
                    _text_field(
                        "Mobile",
                        "mobile",
                        CrmPartnersState.contact_form["mobile"],
                    ),
                    _text_field(
                        "WhatsApp",
                        "whatsapp",
                        CrmPartnersState.contact_form["whatsapp"],
                    ),
                    _text_field(
                        "E-mail",
                        "email",
                        CrmPartnersState.contact_form["email"],
                    ),
                    _text_field(
                        "Langue",
                        "language",
                        CrmPartnersState.contact_form["language"],
                    ),
                    _textarea_field(
                        "Notes", "notes", CrmPartnersState.contact_form["notes"]
                    ),
                    class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-5",
                ),
                rx.el.label(
                    rx.el.input(
                        type="checkbox",
                        name="is_primary",
                        default_checked=CrmPartnersState.contact_form[
                            "is_primary"
                        ]
                        != "",
                        class_name="h-4 w-4 rounded border-white/20 bg-white/10 accent-lime-300",
                    ),
                    rx.el.span(
                        "Définir comme contact principal",
                        class_name="text-xs font-semibold text-emerald-100/70",
                    ),
                    class_name="flex items-center gap-2 w-fit mt-4",
                ),
                rx.el.div(
                    rx.el.button(
                        "Annuler",
                        type="button",
                        on_click=CrmPartnersState.close_contact_form,
                        class_name="rounded-full border border-white/10 bg-white/[0.05] px-5 py-2 text-xs font-semibold text-emerald-100/70 hover:border-lime-300/35 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon("check", class_name="h-4 w-4"),
                        rx.el.span(
                            "Enregistrer", class_name="text-xs font-semibold"
                        ),
                        type="submit",
                        class_name="flex items-center gap-2 rounded-full bg-lime-300 px-5 py-2 text-[#04140d] hover:bg-lime-200 transition-colors w-fit",
                    ),
                    class_name="flex flex-wrap items-center justify-end gap-2 w-full mt-6",
                ),
                on_submit=CrmPartnersState.save_contact,
                class_name="w-full",
            ),
            CrmPartnersState.close_contact_form,
        ),
        rx.fragment(),
    )


def crm_document_form() -> rx.Component:
    return rx.cond(
        CrmPartnersState.document_form_open,
        _modal(
            "Document du tiers",
            "Contrats, factures, bons, certificats et documents fiscaux classés dans la fiche.",
            rx.el.form(
                rx.el.div(
                    _text_field(
                        "Titre *",
                        "title",
                        CrmPartnersState.document_form["title"],
                    ),
                    _select_field(
                        "Nature",
                        "kind",
                        CrmPartnersState.document_form["kind"],
                        CrmPartnersState.document_kind_options,
                    ),
                    _text_field(
                        "Référence",
                        "reference",
                        CrmPartnersState.document_form["reference"],
                    ),
                    _text_field(
                        "Auteur",
                        "author",
                        CrmPartnersState.document_form["author"],
                    ),
                    _textarea_field(
                        "Notes",
                        "notes",
                        CrmPartnersState.document_form["notes"],
                    ),
                    class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-5",
                ),
                rx.el.div(
                    rx.el.button(
                        "Annuler",
                        type="button",
                        on_click=CrmPartnersState.close_document_form,
                        class_name="rounded-full border border-white/10 bg-white/[0.05] px-5 py-2 text-xs font-semibold text-emerald-100/70 hover:border-lime-300/35 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon("check", class_name="h-4 w-4"),
                        rx.el.span(
                            "Enregistrer", class_name="text-xs font-semibold"
                        ),
                        type="submit",
                        class_name="flex items-center gap-2 rounded-full bg-lime-300 px-5 py-2 text-[#04140d] hover:bg-lime-200 transition-colors w-fit",
                    ),
                    class_name="flex flex-wrap items-center justify-end gap-2 w-full mt-6",
                ),
                on_submit=CrmPartnersState.save_document,
                class_name="w-full",
            ),
            CrmPartnersState.close_document_form,
        ),
        rx.fragment(),
    )
