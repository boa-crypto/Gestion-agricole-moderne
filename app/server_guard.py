import reflex as rx

import ast
import asyncio
import inspect
import logging
import re
import textwrap
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps

from app.access_reference import all_permissions
from app.menu_policy import resolve_policy
from app.navigation import ENTRY_BY_KEY, ROUTE_MATRIX

VALID_PERMISSIONS = frozenset(all_permissions())
DEDICATED_STATES = frozenset(
    {
        "MenuAuthState",
        "MenuConfigurationState",
        "NavigationState",
        "LoginRedirectState",
    }
)
STATE_MODULES: dict[str, tuple[str, ...]] = {
    "AdministrationState": ("utilisateurs",),
    "AuditState": ("utilisateurs",),
    "CartographyState": ("cartographie",),
    "CatalogBrowserState": ("semences",),
    "CatalogState": ("semences",),
    "ContourState": ("parcelles",),
    "CrmState": ("ventes", "achats", "comptabilite"),
    "CrmPartnersState": ("ventes", "achats", "comptabilite"),
    "CrmRegistersState": ("ventes", "achats", "comptabilite"),
    "DashboardState": ("dashboard",),
    "EmployeesState": ("rh",),
    "ExpensesState": ("comptabilite",),
    "GuideAdminState": ("documents",),
    "GuideState": ("documents",),
    "HelpState": ("documents",),
    "MaintenanceState": ("materiel", "maintenance", "carburant"),
    "OperationsState": ("interventions",),
    "ParcelsState": ("parcelles", "cultures"),
    "PhenologyAdminState": ("parametres",),
    "PhenologyOpsState": ("cultures",),
    "PhenologySearchState": ("cultures",),
    "PhenologyState": ("cultures",),
    "RemediationState": ("dashboard", "stocks", "parcelles"),
    "SearchState": (
        "dashboard",
        "utilisateurs",
        "documents",
        "parcelles",
        "cultures",
        "stocks",
        "rh",
        "materiel",
        "comptabilite",
        "ventes",
        "achats",
    ),
    "SecurityAuditState": ("utilisateurs",),
    "StockState": ("stocks",),
    "WeatherState": ("meteo",),
}
STATE_ROUTES: dict[str, tuple[str, ...]] = {
    "AdministrationState": ("/administration",),
    "AuditState": ("/audit",),
    "CartographyState": ("/cartographie",),
    "CatalogBrowserState": ("/referentiel",),
    "CatalogState": ("/", "/parcelles", "/referentiel", "/traitements"),
    "ContourState": ("/", "/cartographie", "/audit"),
    "CrmState": ("/crm",),
    "CrmPartnersState": ("/crm",),
    "CrmRegistersState": ("/crm",),
    "DashboardState": ("/",),
    "EmployeesState": ("/employes",),
    "ExpensesState": ("/charges",),
    "GuideAdminState": ("/guide",),
    "GuideState": ("/guide", "/"),
    "HelpState": tuple(entry["route"] for entry in ROUTE_MATRIX.values()),
    "MaintenanceState": ("/maintenance",),
    "OperationsState": ("/traitements",),
    "ParcelsState": ("/parcelles",),
    "PhenologyAdminState": ("/phenologie",),
    "PhenologyOpsState": (
        "/rapports",
        "/cartographie",
        "/audit",
        "/traitements",
    ),
    "PhenologySearchState": ("/recherche",),
    "PhenologyState": ("/parcelles",),
    "RemediationState": ("/", "/traitements", "/cartographie", "/audit"),
    "SearchState": ("/recherche",),
    "SecurityAuditState": ("/audit",),
    "StockState": ("/", "/traitements", "/audit"),
    "WeatherState": ("/",),
}


@dataclass(frozen=True)
class EventRule:
    state_name: str
    event_name: str
    modules: tuple[str, ...]
    actions: tuple[str, ...]
    routes: tuple[str, ...]
    mode_field: str = ""


@dataclass(frozen=True)
class CheckedContext:
    state: rx.State
    background: bool


CHECKED_CONTEXT: ContextVar[CheckedContext | None] = ContextVar(
    "agripro_checked_event", default=None
)
EVENT_COVERAGE: dict[str, EventRule] = {}


def business_states() -> list[type[rx.State]]:
    pending = list(rx.State.__subclasses__())
    found: set[type[rx.State]] = set()
    while pending:
        state_class = pending.pop()
        pending.extend(state_class.__subclasses__())
        if (
            state_class.__module__.startswith("app.")
            and state_class.__name__ not in DEDICATED_STATES
        ):
            found.add(state_class)
    return sorted(found, key=lambda state_class: state_class.get_full_name())


def _source(fn) -> str:
    try:
        return textwrap.dedent(inspect.getsource(inspect.unwrap(fn)))
    except (OSError, TypeError):
        logging.exception("Unexpected error")
        return ""


def _effects(fn, state_class, seen: set[int] | None = None) -> str:
    seen = set() if seen is None else seen
    if id(fn) in seen:
        return ""
    seen.add(id(fn))
    source = _source(fn)
    if not source:
        return ""
    tree = ast.parse(source)
    parts = [source]
    globals_map = getattr(inspect.unwrap(fn), "__globals__", {})
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            value = globals_map.get(node.id)
            if isinstance(value, str) and re.search(
                r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b", value, re.I
            ):
                parts.append(value)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = None
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Name
        ):
            if node.func.value.id in (
                "self",
                state_class.__name__,
            ) and node.func.attr.startswith("_"):
                target = getattr(state_class, node.func.attr, None)
        elif isinstance(node.func, ast.Name):
            target = globals_map.get(node.func.id)
        if isinstance(target, rx.event.EventHandler):
            target = inspect.unwrap(target.fn)
        if inspect.isfunction(target) and target.__module__.startswith("app."):
            if not target.__module__.split(".")[-1].startswith(
                "seed"
            ) and target.__module__ not in {
                "app.database",
                "app.menu_database",
                "app.access_control",
            }:
                parts.append(_effects(target, state_class, seen))
    return "\n".join(parts)


def build_rule(
    state_class, name: str, handler: rx.event.EventHandler
) -> EventRule:
    state_name = state_class.__name__
    if state_name not in STATE_MODULES:
        raise RuntimeError(
            f"Business state requires an authorization mapping: {state_name}"
        )
    fn = inspect.unwrap(handler.fn)
    source = _effects(fn, state_class)
    own_source = _source(fn)
    modules = STATE_MODULES[state_name]
    if state_name == "OperationsState":
        if "harvest" in name or "yield" in name:
            modules = ("recoltes",)
        elif "movement" in name or "stock" in name:
            modules = ("stocks",)
        elif name == "load_operations":
            modules = ("interventions", "stocks", "recoltes")
    elif state_name == "MaintenanceState":
        if "equipment" in name:
            modules = ("materiel",)
        elif "usage" in name:
            modules = ("materiel", "carburant")
        elif "cost" in name:
            modules = ("comptabilite",)
        elif (
            "operation" in name
            or "journal" in name
            or name == "set_kind_filter"
        ):
            modules = ("maintenance",)
    elif state_name == "AdministrationState":
        if name in {"complete_intervention", "validate_intervention"}:
            modules = ("utilisateurs", "interventions")
    elif state_name == "RemediationState":
        if "stock" in name:
            modules = ("stocks",)
        elif "contour" in name:
            modules = ("parcelles",)
        elif name in {
            "resolve_alert",
            "follow_alert",
            "watch_alert",
            "document_alert",
        }:
            modules = ("cultures",)
        elif name == "load_remediation":
            modules = ("dashboard", "stocks", "parcelles")
    actions: tuple[str, ...] = ("CONSULTER",)
    mutation = bool(
        re.search(
            r"\b(?:INSERT\s+INTO|UPDATE\s+(?:\w+|\{)|DELETE\s+FROM)\b",
            source,
            re.I,
        )
    )
    calls = set(re.findall(r"\b(?:await\s+)?(\w+)\(", source))
    service_write = any(
        call.startswith(
            (
                "save_",
                "record_",
                "set_profile_",
                "set_stage_",
                "move_stage",
                "import_",
                "create_delegation",
                "revoke_delegation",
                "change_user_status",
                "complete_task",
                "validate_task",
            )
        )
        for call in calls
    )
    if (
        mutation
        or service_write
        or name.startswith(("submit_", "save_", "run_import", "apply_status"))
    ):
        actions = ("MODIFIER",)
    if state_name == "RemediationState" and name == "load_remediation":
        actions = ("CONSULTER",)
        if re.search(r"\bINSERT\s+INTO\b", source, re.I) and not re.search(
            r"\bUPDATE\s+(?:\w+|\{)\b", source, re.I
        ):
            actions = ("CREER",)
        if name.startswith(("submit_", "save_", "create_", "run_import")):
            actions = ("CREER", "MODIFIER")
        if name.startswith(("delete_", "remove_", "archive_")):
            actions = ("SUPPRIMER",)
        elif re.search(
            r"\bDELETE\s+FROM\b", own_source, re.I
        ) and not name.startswith(("submit_", "save_")):
            actions = ("SUPPRIMER",)
    if name.startswith(("export_", "run_export")) or "rx.download(" in source:
        actions = ("EXPORTER",)
    if name.startswith(("validate_", "confirm_")):
        actions = ("VALIDER",)
    if name.startswith(("complete_", "mark_operation_done")):
        actions = ("CLOTURER",)
    if state_name == "StockState" and name in {
        "decide_stock",
        "order_stock",
        "defer_stock",
        "accept_stock",
    }:
        actions = ("MODIFIER",)
    if (
        state_name == "AdministrationState"
        and "delegation" in name
        and name not in {"load_administration"}
    ):
        actions = ("AFFECTER",)
    if (
        state_name == "AdministrationState"
        and name == "revoke_temporary_permission"
    ):
        actions = ("AFFECTER",)
    if (
        state_name == "AdministrationState"
        and name == "expire_temporary_permissions"
    ):
        actions = ("CLOTURER",)
    if (
        state_name in {"ContourState", "RemediationState"}
        and name not in {"load_contours", "load_remediation"}
        and (mutation or service_write)
    ):
        actions = ("MODIFIER",)
    if state_name == "PhenologyState" and name.startswith(
        ("submit_", "save_", "record_")
    ):
        actions = ("CREER",)
    if state_name == "AdministrationState" and name in {
        "set_user_status",
        "apply_status",
    }:
        actions = ("MODIFIER",)
    if state_name == "WeatherState":
        actions = ("CONSULTER",)
    if state_name == "AuditState":
        modules = (
            "utilisateurs",
            "documents",
            "parcelles",
            "cultures",
            "stocks",
        )
    elif state_name == "SearchState":
        modules = tuple(
            sorted(
                {
                    module
                    for module, action in VALID_PERMISSIONS
                    if action == "CONSULTER"
                }
            )
        )
    mode = ""
    modes = re.findall(
        r"self\.(\w*(?:form_mode|editing_id|edit_id))", own_source
    )
    if actions == ("CREER", "MODIFIER") and modes:
        mode = modes[0]
    if state_name == "PhenologyAdminState":
        actions = ("CONSULTER",) if actions == ("CONSULTER",) else ("MODIFIER",)
    if state_name == "CrmRegistersState" and name == "save_operation":
        actions = ("CREER",)
    if state_name == "CrmPartnersState" and name == "save_document":
        actions = ("CREER",)
    if state_name == "SearchState" and name == "load_search":
        actions = ("CONSULTER",)
    for module in modules:
        for action in actions:
            if (module, action) not in VALID_PERMISSIONS:
                if (
                    action not in {"CONSULTER", "EXPORTER", "SUPPRIMER"}
                    and (module, "MODIFIER") in VALID_PERMISSIONS
                ):
                    actions = ("MODIFIER",)
                else:
                    raise RuntimeError(
                        f"Invalid event permission: {state_name}.{name}: {module}:{action}"
                    )
    return EventRule(
        state_name, name, modules, actions, STATE_ROUTES[state_name], mode
    )


@asynccontextmanager
async def _state_access(state, background: bool):
    if background:
        async with state:
            yield
    else:
        yield


async def clear_session_views(
    state, *, clear_token: bool = False, auth_state: object | None = None
) -> None:
    from app.states.menu_auth_state import MenuAuthState
    from app.states.menu_configuration_state import MenuConfigurationState
    from app.states.navigation_state import NavigationState

    auth = (
        auth_state
        if auth_state is not None
        else await state.get_state(MenuAuthState)
    )
    auth.ready = True
    auth.authenticated = False
    auth.admin = False
    auth.email = ""
    auth.permissions = []
    auth.allowed_crm_tabs = []
    auth.has_modules = False
    auth.page_allowed = False
    auth.verified_path = ""
    auth._verified_token = ""
    auth._pending_loader = ""
    auth._dispatch_page = ""
    auth._dispatch_index = 0
    auth._generation += 1
    if clear_token:
        auth.token = ""
    nav = await state.get_state(NavigationState)
    nav.cockpits = []
    nav.visible_navigation = []
    nav.panel_open = False
    nav.mobile_open = False
    config = await state.get_state(MenuConfigurationState)
    config._clear_sensitive()
    for state_class in business_states():
        business = await state.get_state(state_class)
        business.reset()


def _required(
    rule: EventRule, state, args: tuple, kwargs: dict
) -> set[tuple[str, str]]:
    modules = rule.modules
    actions = rule.actions
    if rule.state_name == "PhenologyAdminState" and rule.event_name in {
        "run_export",
        "export_all",
    }:
        return {("parametres", "CONSULTER"), ("rapports", "EXPORTER")}
    if rule.mode_field:
        mode = getattr(state, rule.mode_field, "")
        actions = (
            ("MODIFIER",)
            if mode == "edit" or isinstance(mode, int) and mode > 0
            else ("CREER",)
        )
    if rule.state_name == "CrmRegistersState":
        register = getattr(state, "register", "ventes")
        if rule.event_name == "enter_register":
            register = (
                str(args[0]) if args else str(kwargs.get("register", "ventes"))
            )
        modules = {
            "ventes": ("ventes",),
            "achats": ("achats",),
            "creances": ("comptabilite",),
            "dettes": ("comptabilite",),
            "paiements": ("comptabilite",),
            "rapports": ("rapports", "ventes", "achats", "comptabilite"),
        }.get(register, ())
        if not modules:
            return {("invalid", "CONSULTER")}
        if rule.event_name == "save_operation":
            modules = {
                "sale": ("ventes",),
                "purchase": ("achats",),
                "payment": ("comptabilite",),
            }.get(getattr(state, "form_kind", ""), ())
            if not modules:
                return {("invalid", "CREER")}
        # Options expose all tiers and invoices; reports contain both ledgers.
        if rule.event_name in {"load_registers", "open_form", "save_operation"}:
            return {
                (module, "CONSULTER")
                for module in ("ventes", "achats", "comptabilite")
            } | {(module, action) for module in modules for action in actions}
    if rule.state_name == "CrmPartnersState" and actions != ("CONSULTER",):
        kind = getattr(state, "detail", {}).get("kind", "MIXTE")
        if rule.event_name == "save_partner":
            data = (
                args[0]
                if args and isinstance(args[0], dict)
                else kwargs.get("form_data", {})
            )
            kind = str(data.get("kind", "CLIENT"))
            actions = (
                ("MODIFIER",)
                if getattr(state, "form_mode", "") == "edit"
                else ("CREER",)
            )
        if rule.event_name == "save_contact":
            actions = (
                ("MODIFIER",)
                if getattr(state, "contact_form_mode", "") == "edit"
                else ("CREER",)
            )
        modules = (
            ("ventes",)
            if kind in {"CLIENT", "GROSSISTE", "DISTRIBUTEUR", "REVENDEUR"}
            else ("achats",)
            if kind in {"FOURNISSEUR", "TRANSPORTEUR", "PRESTATAIRE"}
            else ("ventes", "achats")
        )
        # Contacts and archives accept arbitrary record ids. Require both
        # commercial domains rather than trusting the selected detail's kind.
        if rule.event_name != "save_partner":
            modules = ("ventes", "achats")
        elif getattr(state, "form_mode", "") == "edit":
            old_kind = getattr(state, "detail", {}).get("kind", "MIXTE")
            old_modules = (
                ("ventes",)
                if old_kind
                in {"CLIENT", "GROSSISTE", "DISTRIBUTEUR", "REVENDEUR"}
                else ("achats",)
                if old_kind in {"FOURNISSEUR", "TRANSPORTEUR", "PRESTATAIRE"}
                else ("ventes", "achats")
            )
            modules = tuple(set(modules) | set(old_modules))
        if "document" in rule.event_name:
            modules = ("documents",)
        return {(module, "CONSULTER") for module in rule.modules} | {
            (module, action) for module in modules for action in actions
        }
    return {(module, "CONSULTER") for module in modules} | {
        (module, action) for module in modules for action in actions
    }


async def authorize_event(
    state,
    rule: EventRule,
    args: tuple = (),
    kwargs: dict | None = None,
    *,
    background: bool = False,
) -> bool:
    from app.states.menu_auth_state import MenuAuthState
    from app.states.navigation_state import NavigationState
    from app.states.menu_configuration_state import MenuConfigurationState

    kwargs = kwargs or {}
    async with _state_access(state, background):
        auth = await state.get_state(MenuAuthState)
        token = auth.token
        generation = auth._generation
        path = state.router.url.path
        verified = (
            auth.ready
            and auth.authenticated
            and bool(token)
            and token == auth._verified_token
            and auth.verified_path == path
        )
        requested = auth.requested_entry
        required = _required(rule, state, args, kwargs)
    (result,) = await asyncio.gather(
        resolve_policy(token), return_exceptions=True
    )
    if isinstance(result, PermissionError):
        async with _state_access(state, background):
            auth = await state.get_state(MenuAuthState)
            if auth.token == token and auth._generation == generation:
                await clear_session_views(state, clear_token=True)
                auth.error = (
                    "Votre session a expiré. Veuillez vous reconnecter."
                )
        return False
    elif isinstance(result, Exception):
        logging.exception(
            f"Error: authorization verification failed: {type(result).__name__}",
            exc_info=(type(result), result, result.__traceback__),
        )
        async with _state_access(state, background):
            auth = await state.get_state(MenuAuthState)
            if auth.token == token and auth._generation == generation:
                await clear_session_views(state)
                auth.error = (
                    "La vérification des accès est indisponible. Réessayez."
                )
        return False
    else:
        policy = result
    async with _state_access(state, background):
        auth = await state.get_state(MenuAuthState)
        if (
            token != auth.token
            or generation != auth._generation
            or path != state.router.url.path
        ):
            return False
        if not policy["id"] or not policy["active"]:
            await clear_session_views(state, clear_token=True)
            auth.error = "Connexion requise ou compte désactivé."
            return False
        nav = await state.get_state(NavigationState)
        nav._apply_policy(policy)
        auth.permissions = policy["permissions"]
        auth.allowed_crm_tabs = policy["crm_tabs"]
        auth.has_modules = bool(policy["navigation"])
        auth.admin = policy["admin"]
        if not auth.admin:
            config = await state.get_state(MenuConfigurationState)
            config._clear_sensitive()
        entry = ENTRY_BY_KEY.get(requested)
        destination_allowed = bool(
            entry
            and entry["route"] == path
            and any(item["key"] == requested for item in policy["navigation"])
        )
        auth.page_allowed = destination_allowed
        still_verified = (
            auth.ready
            and auth.authenticated
            and auth._verified_token == token
            and auth.verified_path == path
            and auth.requested_entry == requested
        )
        explicit_handler = rule.event_name not in {
            "setvar",
            "reset",
            "set_state",
            "set_actor_id",
            "set_actor_label",
            "set_effective_permissions",
            "set_scope_parcels",
        }
        allowed = (
            verified
            and still_verified
            and explicit_handler
            and destination_allowed
            and path in rule.routes
            and required <= VALID_PERMISSIONS
            and {f"{module}:{action}" for module, action in required}
            <= set(policy["permissions"])
        )
        if not allowed:
            auth._pending_loader = ""
        return bool(allowed)


async def require_service(*permissions: tuple[str, str]) -> None:
    context = CHECKED_CONTEXT.get()
    if context is None:
        raise PermissionError("Une session métier vérifiée est requise.")
    rule = EventRule(
        "Service",
        "service",
        tuple(module for module, _ in permissions),
        ("CONSULTER",),
        tuple(entry["route"] for entry in ROUTE_MATRIX.values()),
    )
    if not await authorize_event(
        context.state, rule, background=context.background
    ):
        raise PermissionError("Accès non autorisé.")
    from app.states.menu_auth_state import MenuAuthState

    async with _state_access(context.state, context.background):
        auth = await context.state.get_state(MenuAuthState)
        if not {f"{module}:{action}" for module, action in permissions} <= set(
            auth.permissions
        ):
            raise PermissionError("Cette opération n'est pas autorisée.")


def checked_service(*permissions: tuple[str, str]):
    def decorate(fn):
        @wraps(fn)
        async def checked(*args, **kwargs):
            await require_service(*permissions)
            return await fn(*args, **kwargs)

        checked._agripro_service_gate = True
        return checked

    return decorate


def wrap_event(handler: rx.event.EventHandler, rule: EventRule) -> None:
    if getattr(handler.fn, "_agripro_event_gate", False):
        return
    implementation = handler.fn
    background = handler.is_background

    @wraps(implementation)
    async def gated(state, *args, **kwargs):
        from app.states.menu_auth_state import MenuAuthState
        from app.auth_dispatch import loader_key

        async with _state_access(state, background):
            auth = await state.get_state(MenuAuthState)
            pending = auth._pending_loader == loader_key(handler)
        if not await authorize_event(
            state, rule, args, kwargs, background=background
        ):
            yield rx.toast(
                "Accès refusé : reconnectez-vous ou vérifiez vos droits pour cette opération.",
                duration=5000,
                close_button=True,
            )
            # A denied optional loader must not prevent authorized later loaders.
            from app.states.menu_auth_state import MenuAuthState

            async with _state_access(state, background):
                auth = await state.get_state(MenuAuthState)
                page, index, generation = (
                    auth._dispatch_page,
                    auth._dispatch_index,
                    auth._generation,
                )
                resume = (
                    pending
                    and auth.authenticated
                    and auth.page_allowed
                    and bool(page)
                )
            if resume:
                yield MenuAuthState.dispatch_loader(page, index + 1, generation)
            return
        if rule.state_name == "AdministrationState":
            from sqlalchemy import text

            async with _state_access(state, background):
                auth = await state.get_state(MenuAuthState)
                email = auth.email.strip().lower()
            async with rx.asession() as session:
                actors = (
                    await session.execute(
                        text(
                            "SELECT id FROM app_user WHERE lower(trim(email)) = :email AND status = 'ACTIF' LIMIT 2"
                        ),
                        {"email": email},
                    )
                ).all()
            async with _state_access(state, background):
                state.actor_id = int(actors[0][0]) if len(actors) == 1 else 0
                state.actor_label = email
        context_token = CHECKED_CONTEXT.set(CheckedContext(state, background))
        try:
            result = implementation(state, *args, **kwargs)
            if inspect.isasyncgen(result):
                async for event in result:
                    yield event
            elif inspect.isawaitable(result):
                event = await result
                if event is not None:
                    yield event
            elif inspect.isgenerator(result):
                for event in result:
                    yield event
            elif result is not None:
                yield result
        except PermissionError:
            logging.exception("Unexpected error")
            yield rx.toast(
                "Cette opération n'est pas autorisée.",
                duration=5000,
                close_button=True,
            )
        finally:
            CHECKED_CONTEXT.reset(context_token)

    gated._agripro_event_gate = True
    gated._agripro_rule = rule
    object.__setattr__(handler, "fn", gated)


def install_event_gate() -> None:
    for state_class in business_states():
        for name, handler in state_class.event_handlers.items():
            if name.startswith("_"):
                continue
            key = f"{state_class.get_full_name()}.{name}"
            if getattr(handler.fn, "_agripro_event_gate", False):
                EVENT_COVERAGE[key] = handler.fn._agripro_rule
                continue
            rule = build_rule(state_class, name, handler)
            wrap_event(handler, rule)
            EVENT_COVERAGE[key] = rule
