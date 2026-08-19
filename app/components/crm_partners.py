import reflex as rx

from app.components.crm_partner_detail import crm_partner_detail
from app.components.crm_partner_forms import (
    crm_contact_form,
    crm_document_form,
    crm_partner_form,
)
from app.components.crm_partner_list import crm_partner_list
from app.states.crm_partners_state import CrmPartnersState


def crm_partner_workspace(space: str) -> rx.Component:
    """Espace Clients / Fournisseurs / Partenaires : liste + fiche 360°."""
    return rx.el.div(
        rx.cond(
            CrmPartnersState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="h-[42rem] w-full xl:w-[27rem] shrink-0 animate-pulse rounded-3xl border border-white/10 bg-white/[0.04]"
                ),
                rx.el.div(
                    class_name="h-[42rem] flex-1 min-w-0 animate-pulse rounded-3xl border border-white/10 bg-white/[0.04]"
                ),
                class_name="flex flex-col xl:flex-row gap-4 w-full",
            ),
            rx.el.div(
                crm_partner_list(),
                crm_partner_detail(),
                class_name="flex flex-col xl:flex-row gap-4 w-full items-start",
            ),
        ),
        crm_partner_form(),
        crm_contact_form(),
        crm_document_form(),
        on_mount=CrmPartnersState.enter_space(space),
        class_name="w-full",
    )
