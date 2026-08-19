import reflex as rx
import reflex_enterprise as rxe

from app.components.alerts_panel import alerts_panel
from app.components.calendar_panel import calendar_panel
from app.components.cockpit_header import cockpit_header
from app.components.cockpit_pulse import cockpit_pulse
from app.components.crops_panel import crops_panel
from app.components.kpi_strip import kpi_strip
from app.components.parcel_map import parcel_map
from app.components.remediation_panels import alert_triage_panel
from app.components.side_rail import side_rail
from app.components.weather_panel import weather_panel
from app.pages.administration import administration_page
from app.pages.audit import audit_page
from app.pages.cartography import cartography_page
from app.pages.catalog import catalog_page
from app.pages.crm import crm_page
from app.pages.employees import employees_page
from app.pages.expenses import expenses_page
from app.pages.guide import guide_page
from app.pages.maintenance import maintenance_page
from app.pages.operations import operations_page
from app.pages.parcels import parcels_page
from app.pages.phenology import phenology_admin_page
from app.pages.reports import reports_page
from app.pages.search import search_page
from app.states.administration_state import AdministrationState
from app.states.audit_state import AuditState
from app.states.cartography_state import CartographyState
from app.states.catalog_browser_state import CatalogBrowserState
from app.states.catalog_state import CatalogState
from app.states.contour_state import ContourState
from app.states.crm_state import CrmState
from app.states.dashboard_state import DashboardState
from app.states.employees_state import EmployeesState
from app.states.maintenance_state import MaintenanceState
from app.states.operations_state import OperationsState
from app.states.expenses_state import ExpensesState
from app.states.guide_admin_state import GuideAdminState
from app.states.guide_state import GuideState
from app.states.parcels_state import ParcelsState
from app.states.phenology_admin_state import PhenologyAdminState
from app.states.phenology_ops_state import PhenologyOpsState
from app.states.phenology_search_state import PhenologySearchState
from app.states.phenology_state import PhenologyState
from app.states.remediation_state import RemediationState
from app.states.search_state import SearchState
from app.states.security_audit_state import SecurityAuditState
from app.states.stock_state import StockState
from app.states.weather_state import WeatherState


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("cockpit"),
            cockpit_header(),
            rx.el.div(
                kpi_strip(),
                parcel_map(),
                rx.el.div(
                    rx.el.div(weather_panel(), class_name="flex-1 min-w-0"),
                    rx.el.div(
                        alerts_panel(),
                        class_name="w-full xl:w-[26rem] shrink-0",
                    ),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                cockpit_pulse(),
                alert_triage_panel(),
                calendar_panel(),
                crops_panel(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10 flex flex-col gap-6",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )


app = rxe.App(
    head_components=[
        rx.el.link(
            rel="stylesheet",
            href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
        ),
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap",
            rel="stylesheet",
        ),
    ],
    theme=rx.theme(appearance="light"),
)
app.add_page(
    index,
    route="/",
    on_load=[
        DashboardState.load_dashboard,
        WeatherState.load_weather,
        GuideState.load_guide,
        RemediationState.load_remediation,
        StockState.load_stocks,
        ContourState.load_contours,
        CatalogState.load_catalog,
    ],
)
app.add_page(
    parcels_page,
    route="/parcelles",
    on_load=[
        ParcelsState.load_space,
        CatalogState.load_catalog,
        PhenologyState.load_phenology,
    ],
)
app.add_page(
    catalog_page,
    route="/referentiel",
    on_load=CatalogBrowserState.load_referentiel,
)
app.add_page(
    phenology_admin_page,
    route="/phenologie",
    on_load=PhenologyAdminState.load_admin,
)
app.add_page(
    operations_page,
    route="/traitements",
    on_load=[
        OperationsState.load_operations,
        RemediationState.load_remediation,
        StockState.load_stocks,
    ],
)
app.add_page(
    employees_page,
    route="/employes",
    on_load=EmployeesState.load_workforce,
)
app.add_page(
    maintenance_page,
    route="/maintenance",
    on_load=MaintenanceState.load_fleet,
)
app.add_page(
    cartography_page,
    route="/cartographie",
    on_load=[
        CartographyState.load_map,
        ContourState.load_contours,
        RemediationState.load_remediation,
        PhenologyOpsState.load_operational,
    ],
)
app.add_page(
    reports_page,
    route="/rapports",
    on_load=PhenologyOpsState.load_operational,
)
app.add_page(
    expenses_page,
    route="/charges",
    on_load=ExpensesState.load_expenses,
)
app.add_page(
    crm_page,
    route="/crm",
    on_load=CrmState.load_crm,
)
app.add_page(
    search_page,
    route="/recherche",
    on_load=[SearchState.load_search, PhenologySearchState.load_index],
)
app.add_page(
    guide_page,
    route="/guide",
    on_load=[GuideState.load_guide, GuideAdminState.load_admin],
)
app.add_page(
    administration_page,
    route="/administration",
    on_load=AdministrationState.load_administration,
)
app.add_page(
    audit_page,
    route="/audit",
    on_load=[
        AuditState.load_audit,
        ContourState.load_contours,
        RemediationState.load_remediation,
        StockState.load_stocks,
        PhenologyOpsState.load_operational,
        SecurityAuditState.load_security,
    ],
)
