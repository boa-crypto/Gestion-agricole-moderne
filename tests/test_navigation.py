import reflex as rx
import ast
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from app.navigation import (
    COCKPITS,
    ENTRY_BY_KEY,
    NAVIGATION,
    ROUTE_MATRIX,
    navigation_coverage,
)
from app.states.navigation_state import resolve_navigation_entry


EXPECTED_ROUTES = {
    "/",
    "/parcelles",
    "/referentiel",
    "/phenologie",
    "/traitements",
    "/employes",
    "/maintenance",
    "/cartographie",
    "/rapports",
    "/charges",
    "/crm",
    "/recherche",
    "/guide",
    "/administration",
    "/audit",
}


def test_crm_deep_links_resolve_exact_existing_entries():
    cases = [
        ("/crm?cockpit=achats&vue=achats", "achats.achats"),
        ("/crm?cockpit=financier&vue=creances", "financier.creances"),
        ("/crm?cockpit=achats&vue=fournisseurs", "achats.fournisseurs"),
        (
            "/crm?cockpit=partenaires&vue=fournisseurs",
            "partenaires.fournisseurs",
        ),
    ]
    for href, key in cases:
        query = parse_qs(urlsplit(href).query)
        entry = resolve_navigation_entry(
            "crm", query["cockpit"][0], query["vue"][0]
        )
        assert entry == ENTRY_BY_KEY[key]
        assert entry["href"] == href


def test_invalid_crm_combinations_fall_back_to_synthese():
    for cockpit, tab in [
        ("", ""),
        ("", "achats"),
        ("inconnu", "achats"),
        ("achats", "creances"),
        ("financier", "fournisseurs"),
        ("commercial", "achats"),
        ("achats", "inconnue"),
        ("agricole", "achats"),
        ("infrastructures", "achats"),
        ("elevage", ""),
        ("configuration", "synthese"),
    ]:
        entry = resolve_navigation_entry("crm", cockpit, tab)
        assert entry == ROUTE_MATRIX["crm"]
        assert entry["cockpit"] == "commercial"
        assert entry["tab"] == "synthese"
    assert resolve_navigation_entry("inconnue", "achats", "achats") is None


def test_resolver_preserves_routes_anchors_and_cockpit_only_links():
    for entry in NAVIGATION:
        assert (
            resolve_navigation_entry(
                entry["page"], entry["cockpit"], entry["tab"]
            )
            == entry
        )
    for page, primary in ROUTE_MATRIX.items():
        assert resolve_navigation_entry(page) == primary
    assert resolve_navigation_entry("crm", "achats")["tab"] == "achats"
    for cockpit in COCKPITS:
        if not cockpit["available"]:
            for page, primary in ROUTE_MATRIX.items():
                assert resolve_navigation_entry(page, cockpit["key"]) == primary


def test_all_registered_routes_are_covered():
    tree = ast.parse(Path("app/app.py").read_text())
    routes = {
        keyword.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_page"
        for keyword in node.keywords
        if keyword.arg == "route" and isinstance(keyword.value, ast.Constant)
    }
    assert routes == EXPECTED_ROUTES
    assert navigation_coverage(routes) == {
        "orphan_routes": [],
        "unregistered_routes": [],
    }
    assert {entry["route"] for entry in ROUTE_MATRIX.values()} == routes


def test_only_real_destinations_and_explicit_upcoming_categories():
    assert len(COCKPITS) == 17
    assert {item["key"] for item in COCKPITS if not item["available"]} == {
        "infrastructures",
        "elevage",
        "configuration",
    }
    assert len(ENTRY_BY_KEY) == len(NAVIGATION)
    available = {item["key"] for item in COCKPITS if item["available"]}
    assert {entry["cockpit"] for entry in NAVIGATION} == available
    for entry in NAVIGATION:
        url = urlsplit(entry["href"])
        assert url.path == entry["route"] in EXPECTED_ROUTES
        assert parse_qs(url.query)["cockpit"] == [entry["cockpit"]]
        assert entry["domain"] and entry["label"]
        if entry["tab"]:
            assert entry["route"] == "/crm"
            assert parse_qs(url.query)["vue"] == [entry["tab"]]


def test_existing_section_targets_and_crm_tabs():
    sources = {
        "/traitements": Path("app/pages/operations.py").read_text(),
        "/maintenance": Path("app/pages/maintenance.py").read_text(),
        "/": Path("app/app.py").read_text(),
    }
    crm = Path("app/pages/crm.py").read_text()
    for entry in NAVIGATION:
        if entry["anchor"]:
            assert f'id="{entry["anchor"]}"' in sources[entry["route"]]
        if entry["tab"]:
            assert f'"{entry["tab"]}"' in crm


def test_shared_navigation_layout_and_help_are_preserved():
    rail = Path("app/components/side_rail.py").read_text()
    assert "guide_help_panel()" in rail
    assert "HelpState.toggle_context(active)" in rail
    assert 'href="/recherche"' in rail and 'href="/"' in rail
    assert "focus-visible:outline" in rail
    assert "dialog.content" in rail and "dialog.close" in rail
    for file in [Path("app/app.py"), *Path("app/pages").glob("*.py")]:
        source = file.read_text()
        if "side_rail(" in source:
            assert "xl:pl-72" in source


def test_every_page_initializes_navigation_without_replacing_business_loaders():
    source = Path("app/app.py").read_text()
    for page in ROUTE_MATRIX:
        assert f'NavigationState.enter_page("{page}")' in source
    assert "CrmState.load_crm" in source
    assert "AdministrationState.load_administration" in source
