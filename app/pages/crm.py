import reflex as rx

from app.components.crm_alerts import crm_alerts
from app.components.crm_charts import crm_charts
from app.components.crm_header import crm_header
from app.components.crm_insights import crm_insights
from app.components.crm_kpis import (
    crm_client_kpis,
    crm_commercial_kpis,
    crm_supplier_kpis,
)
from app.components.crm_partners import crm_partner_workspace
from app.components.crm_registers import crm_registers
from app.components.crm_search import crm_search
from app.components.crm_tops import crm_tops
from app.components.shell import app_shell
from app.states.crm_state import CrmState


def _overview() -> rx.Component:
    return rx.el.div(
        crm_client_kpis(),
        crm_supplier_kpis(),
        crm_commercial_kpis(),
        crm_insights(),
        class_name="flex flex-col gap-6 w-full",
    )


def _content() -> rx.Component:
    return rx.match(
        CrmState.active_tab,
        ("synthese", _overview()),
        (
            "graphiques",
            rx.el.div(
                crm_commercial_kpis(),
                crm_charts(),
                class_name="flex flex-col gap-6 w-full",
            ),
        ),
        ("clients", crm_partner_workspace("clients")),
        ("fournisseurs", crm_partner_workspace("fournisseurs")),
        ("partenaires", crm_partner_workspace("partenaires")),
        ("ventes", crm_registers("ventes")),
        ("achats", crm_registers("achats")),
        ("creances", crm_registers("creances")),
        ("dettes", crm_registers("dettes")),
        ("paiements", crm_registers("paiements")),
        ("rapports", crm_registers("rapports")),
        (
            "tiers",
            rx.el.div(
                crm_tops(),
                crm_insights(),
                class_name="flex flex-col gap-6 w-full",
            ),
        ),
        (
            "alertes",
            rx.el.div(
                crm_alerts(),
                crm_charts(),
                class_name="flex flex-col gap-6 w-full",
            ),
        ),
        ("recherche", crm_search()),
        _overview(),
    )


def crm_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            crm_header(),
            rx.el.div(
                _content(),
                class_name="flex flex-col gap-6 w-full mt-8",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "crm",
    )
