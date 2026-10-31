import reflex as rx
import reflex_enterprise as rxe

from app.menu_database import menu_database_lifespan
from app.auth_dispatch import register_loaders
from app.server_guard import install_event_gate
from app.components.menu_auth import guarded_page
from app.states.menu_configuration_state import MenuConfigurationState
from app.components.alerts_panel import alerts_panel
from app.components.calendar_panel import calendar_panel
from app.components.cockpit_header import cockpit_header
from app.components.design import GOOGLE_FONTS_HREF, editorial_styles
from app.components.shell import app_shell
from app.components.cockpit_pulse import cockpit_pulse
from app.components.crops_panel import crops_panel
from app.components.kpi_strip import kpi_strip
from app.components.parcel_map import parcel_map
from app.components.remediation_panels import alert_triage_panel
from app.components.weather_panel import weather_panel
from app.pages.administration import administration_page
from app.pages.audit import audit_page
from app.pages.cartography import cartography_page
from app.pages.catalog import catalog_page
from app.pages.crm import crm_page
from app.pages.configuration import configuration_page
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
from app.states.navigation_state import NavigationState


def cockpit_content() -> rx.Component:
    return app_shell(
        rx.el.div(
            cockpit_header(),
            rx.el.div(
                kpi_strip(),
                parcel_map(),
                rx.el.div(
                    rx.el.div(weather_panel(), class_name="min-w-0 flex-1"),
                    rx.el.div(
                        alerts_panel(),
                        class_name="w-full shrink-0 xl:w-[26rem]",
                    ),
                    class_name="flex w-full flex-col gap-4 xl:flex-row",
                ),
                cockpit_pulse(),
                alert_triage_panel(),
                rx.el.div(
                    calendar_panel(),
                    id="nav-calendrier",
                    class_name="w-full scroll-mt-6",
                ),
                crops_panel(),
                class_name="mt-10 flex w-full flex-col gap-6",
            ),
            class_name="flex w-full flex-col",
        ),
        "cockpit",
    )


def index() -> rx.Component:
    return guarded_page(cockpit_content(), "/")


register_loaders(
    "cockpit",
    NavigationState.refresh_navigation,
    DashboardState.load_dashboard,
    WeatherState.load_weather,
    GuideState.load_guide,
    RemediationState.load_remediation,
    StockState.load_stocks,
    ContourState.load_contours,
    CatalogState.load_catalog,
)
register_loaders(
    "configuration",
    NavigationState.refresh_navigation,
    MenuConfigurationState.load_configuration,
)
register_loaders(
    "parcelles",
    NavigationState.refresh_navigation,
    ParcelsState.load_space,
    CatalogState.load_catalog,
    PhenologyState.load_phenology,
)
register_loaders(
    "referentiel",
    NavigationState.refresh_navigation,
    CatalogBrowserState.load_referentiel,
)
register_loaders(
    "phenologie",
    NavigationState.refresh_navigation,
    PhenologyAdminState.load_admin,
)
register_loaders(
    "traitements",
    NavigationState.refresh_navigation,
    OperationsState.load_operations,
    RemediationState.load_remediation,
    StockState.load_stocks,
)
register_loaders(
    "employes",
    NavigationState.refresh_navigation,
    EmployeesState.load_workforce,
)
register_loaders(
    "maintenance",
    NavigationState.refresh_navigation,
    MaintenanceState.load_fleet,
)
register_loaders(
    "cartographie",
    NavigationState.refresh_navigation,
    CartographyState.load_map,
    ContourState.load_contours,
    RemediationState.load_remediation,
    PhenologyOpsState.load_operational,
)
register_loaders(
    "rapports",
    NavigationState.refresh_navigation,
    PhenologyOpsState.load_operational,
)
register_loaders(
    "charges", NavigationState.refresh_navigation, ExpensesState.load_expenses
)
register_loaders("crm", NavigationState.refresh_navigation, CrmState.load_crm)
register_loaders(
    "recherche",
    NavigationState.refresh_navigation,
    SearchState.load_search,
    PhenologySearchState.load_index,
)
register_loaders(
    "guide",
    NavigationState.refresh_navigation,
    GuideState.load_guide,
    GuideAdminState.load_admin,
)
register_loaders(
    "administration",
    NavigationState.refresh_navigation,
    AdministrationState.load_administration,
)
register_loaders(
    "audit",
    NavigationState.refresh_navigation,
    AuditState.load_audit,
    ContourState.load_contours,
    RemediationState.load_remediation,
    StockState.load_stocks,
    PhenologyOpsState.load_operational,
    SecurityAuditState.load_security,
)


install_event_gate()


app = rxe.App(
    head_components=[
        editorial_styles(),
        rx.el.style(
            "html, body { background-color: #0A0A08 !important; } main { background-attachment: scroll !important; }"
        ),
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
        rx.el.link(href=GOOGLE_FONTS_HREF, rel="stylesheet"),
    ],
    theme=rx.theme(appearance="dark", accent_color="lime", radius="none"),
)
app.register_lifespan_task(menu_database_lifespan)
app.add_page(
    index,
    route="/",
    on_load=NavigationState.enter_page("cockpit"),
)
app.add_page(
    lambda: guarded_page(configuration_page(), "/configuration"),
    route="/configuration",
    title="Configuration & accès — AgriPro",
    on_load=NavigationState.enter_page("configuration"),
)
app.add_page(
    lambda: guarded_page(parcels_page(), "/parcelles"),
    route="/parcelles",
    on_load=NavigationState.enter_page("parcelles"),
)
app.add_page(
    lambda: guarded_page(catalog_page(), "/referentiel"),
    route="/referentiel",
    on_load=NavigationState.enter_page("referentiel"),
)
app.add_page(
    lambda: guarded_page(phenology_admin_page(), "/phenologie"),
    route="/phenologie",
    on_load=NavigationState.enter_page("phenologie"),
)
app.add_page(
    lambda: guarded_page(operations_page(), "/traitements"),
    route="/traitements",
    on_load=NavigationState.enter_page("traitements"),
)
app.add_page(
    lambda: guarded_page(employees_page(), "/employes"),
    route="/employes",
    on_load=NavigationState.enter_page("employes"),
)
app.add_page(
    lambda: guarded_page(maintenance_page(), "/maintenance"),
    route="/maintenance",
    on_load=NavigationState.enter_page("maintenance"),
)
app.add_page(
    lambda: guarded_page(cartography_page(), "/cartographie"),
    route="/cartographie",
    on_load=NavigationState.enter_page("cartographie"),
)
app.add_page(
    lambda: guarded_page(reports_page(), "/rapports"),
    route="/rapports",
    on_load=NavigationState.enter_page("rapports"),
)
app.add_page(
    lambda: guarded_page(expenses_page(), "/charges"),
    route="/charges",
    on_load=NavigationState.enter_page("charges"),
)
app.add_page(
    lambda: guarded_page(crm_page(), "/crm"),
    route="/crm",
    on_load=NavigationState.enter_page("crm"),
)
app.add_page(
    lambda: guarded_page(search_page(), "/recherche"),
    route="/recherche",
    on_load=NavigationState.enter_page("recherche"),
)
app.add_page(
    lambda: guarded_page(guide_page(), "/guide"),
    route="/guide",
    on_load=NavigationState.enter_page("guide"),
)
app.add_page(
    lambda: guarded_page(administration_page(), "/administration"),
    route="/administration",
    on_load=NavigationState.enter_page("administration"),
)
app.add_page(
    lambda: guarded_page(audit_page(), "/audit"),
    route="/audit",
    on_load=NavigationState.enter_page("audit"),
)
