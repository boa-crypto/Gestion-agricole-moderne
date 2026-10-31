import reflex as rx

from app.components.design import empty_state
from app.components.guide_help import guide_error, help_icon_button
from app.states.cartography_state import (
    CartographyState,
    GeometryLog,
    InterventionEntry,
)

_INPUT = "w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-ink-rgb))] px-3 py-2.5 text-sm font-medium text-[rgb(var(--ap-paper-rgb))] placeholder:text-[rgb(var(--ap-paper-muted-rgb)/0.82)] focus:border-[rgb(var(--ap-accent-rgb)/0.50)] outline-hidden transition-colors"


def _fact(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)]"),
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-1.5 truncate",
        ),
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3 min-w-0",
    )


def _health_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
        ),
    )


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "done",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "running",
                "rounded-none border border-[rgb(var(--ap-sage-rgb)/0.30)] bg-[rgb(var(--ap-sage-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-paper-soft-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "late",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "cancelled",
                "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] line-through w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit whitespace-nowrap",
        ),
    )


def _type_icon(type_key: rx.Var, class_name: str) -> rx.Component:
    return rx.match(
        type_key,
        ("SEMIS", rx.icon("sprout", class_name=class_name)),
        ("PLANTATION", rx.icon("shovel", class_name=class_name)),
        ("FERTILISATION", rx.icon("package", class_name=class_name)),
        ("TRAITEMENT_PHYTO", rx.icon("spray-can", class_name=class_name)),
        ("DESHERBAGE", rx.icon("scissors", class_name=class_name)),
        ("IRRIGATION", rx.icon("droplets", class_name=class_name)),
        ("TRAVAIL_DU_SOL", rx.icon("tractor", class_name=class_name)),
        ("OBSERVATION", rx.icon("eye", class_name=class_name)),
        ("RECOLTE", rx.icon("wheat", class_name=class_name)),
        rx.icon("circle-dot", class_name=class_name),
    )


def _timeline_entry(item: InterventionEntry, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                class_name=rx.cond(
                    item["is_done"],
                    "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-accent-rgb))] ring-4 ring-[rgb(var(--ap-accent-rgb)/0.15)]",
                    "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-flame-soft-rgb))] ring-4 ring-[rgb(var(--ap-flame-soft-rgb)/0.15)]",
                )
            ),
            class_name="relative flex flex-col items-center pt-1.5",
        ),
        rx.el.div(
            rx.el.div(
                _type_icon(item["type"], "h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.span(
                    item["title"],
                    class_name="text-xs font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                _status_badge(item["tone"], item["status_label"]),
                rx.el.span(
                    item["date_label"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] ml-auto shrink-0",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.p(
                f"{item['type_label']} · {item['crop_name']} · cible {item['target']}",
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-1 truncate",
            ),
            rx.el.div(
                rx.icon("user-round", class_name="h-3 w-3 text-[rgb(var(--ap-sage-rgb)/0.70)]"),
                rx.el.span(
                    item["operator"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.icon(
                    "flask-conical",
                    class_name="h-3 w-3 text-[rgb(var(--ap-flame-soft-rgb)/0.70)] ml-2",
                ),
                rx.el.span(
                    item["product_label"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
                ),
                rx.el.span(
                    f"{item['area_ha']:.1f} ha · {item['cost']:.0f} €",
                    class_name="text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] ml-auto shrink-0",
                ),
                class_name="flex items-center gap-1.5 mt-1.5 min-w-0",
            ),
            class_name="min-w-0 flex-1 pb-5",
        ),
        key=key,
        class_name="flex gap-3 w-full",
    )


def _draft_status() -> rx.Component:
    """État du brouillon de contour : dessin en cours et GeoJSON prêt."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "État du brouillon de contour",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.span(
                CartographyState.draft_state_label,
                class_name=rx.match(
                    CartographyState.draft_state_tone,
                    (
                        "good",
                        "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit ml-auto",
                    ),
                    (
                        "warn",
                        "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit ml-auto",
                    ),
                    (
                        "info",
                        "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit ml-auto",
                    ),
                    "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit ml-auto",
                ),
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.div(
            _fact(
                "Sommets dessinés",
                CartographyState.draft_vertex_count,
                "git-commit-horizontal",
            ),
            _fact(
                "Surface dessinée",
                f"{CartographyState.draft_area_ha:.2f} ha",
                "shapes",
            ),
            _fact(
                "Surface déclarée",
                f"{CartographyState.declared_area:.2f} ha",
                "ruler",
            ),
            _fact(
                "Écart de contrôle",
                f"{CartographyState.draft_gap_pct:.1f} %",
                "scan-eye",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3",
        ),
        rx.el.p(
            CartographyState.draw_hint,
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] leading-relaxed mt-3",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 mt-8",
    )


def _geometry_tone(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "good",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] text-[rgb(var(--ap-accent-soft-rgb))]",
        ),
        (
            "warn",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] text-[rgb(var(--ap-flame-tint-rgb))]",
        ),
        (
            "info",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] text-[rgb(var(--ap-info-soft-rgb))]",
        ),
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
    )


def _geometry_log_row(item: GeometryLog, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-3.5 w-3.5"),
            class_name=_geometry_tone(item["tone"]),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    item["action_label"],
                    class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-rgb))]",
                ),
                rx.el.span(
                    item["author"],
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
                ),
                rx.el.span(
                    item["date_label"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] ml-auto shrink-0",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
            ),
            rx.el.p(
                item["note"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] leading-relaxed mt-1",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
    )


def _geometry_history() -> rx.Component:
    """Mini-historique des mises à jour de contour de la parcelle."""
    return rx.el.div(
        rx.el.div(
            rx.icon("history", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
            rx.el.span(
                "Historique de la géométrie",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.span(
                f"{CartographyState.geometry_log_count} trace(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.cond(
            CartographyState.has_geometry_notice,
            rx.el.div(
                rx.icon(
                    "circle-check",
                    class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    CartographyState.geometry_notice,
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-accent-pale-rgb)/0.85)] leading-relaxed",
                ),
                class_name="flex items-start gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb))]/[0.07] px-3 py-2 w-full mt-3",
            ),
            rx.fragment(),
        ),
        rx.cond(
            CartographyState.has_geometry_logs,
            rx.el.ul(
                rx.foreach(
                    CartographyState.geometry_logs,
                    lambda item: _geometry_log_row(
                        item, key=item["id"].to_string()
                    ),
                ),
                class_name="flex flex-col gap-2 w-full mt-3",
            ),
            rx.el.p(
                "Aucune mise à jour de contour consignée pour cet îlot : "
                "l'enregistrement d'un GeoJSON ou d'un tracé alimentera cette "
                "trace.",
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] leading-relaxed mt-3",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 mt-8",
    )


def _geometry_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.span(
                "Éditeur de contour GeoJSON",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.div(
                help_icon_button("cartographie"),
                rx.el.button(
                    rx.icon("wand-sparkles", class_name="h-3.5 w-3.5"),
                    rx.el.span("Proposer un contour", class_name="text-[11px]"),
                    type="button",
                    on_click=CartographyState.generate_draft,
                    class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("eraser", class_name="h-3.5 w-3.5"),
                    rx.el.span("Vider", class_name="text-[11px]"),
                    type="button",
                    on_click=CartographyState.clear_draft,
                    class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-flame-soft-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.el.p(
            "Collez un Polygon / MultiPolygon (ou une Feature) en coordonnées WGS84 [longitude, latitude]. La surface, l'emprise et le centre sont recalculés automatiquement.",
            class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2 leading-relaxed",
        ),
        rx.el.textarea(
            name="geojson",
            placeholder='{"type": "Polygon", "coordinates": [[[1.845, 48.234], ...]]}',
            default_value=CartographyState.geojson_draft,
            key=f"geojson-{CartographyState.form_key}",
            rows="8",
            class_name=f"{_INPUT} font-mono text-[11px] resize-y mt-3",
        ),
        rx.el.div(
            rx.el.input(
                name="author",
                placeholder="Auteur du tracé",
                default_value="Cartographie interne",
                key=f"author-{CartographyState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                name="geometry_notes",
                placeholder="Note de géométrie (relevé GPS, cadastre…)",
                key=f"gnotes-{CartographyState.form_key}",
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3",
        ),
        guide_error(
            CartographyState.geometry_error, "cartographie", "geometrie"
        ),
        rx.el.button(
            rx.icon("save", class_name="h-4 w-4 text-[rgb(var(--ap-ink-rgb))]"),
            rx.el.span(
                "Enregistrer le contour de la parcelle",
                class_name="text-[rgb(var(--ap-ink-rgb))]",
            ),
            type="submit",
            class_name="flex items-center gap-2 rounded-none bg-[rgb(var(--ap-accent-rgb))] px-4 py-2.5 text-sm font-semibold hover:bg-[rgb(var(--ap-accent-soft-rgb))] transition-colors w-fit mt-3",
        ),
        on_submit=CartographyState.submit_geometry,
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 mt-8",
    )


def _detail_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    CartographyState.parcel_detail["code"],
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.span(
                    CartographyState.parcel_detail["organic_label"],
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
                ),
                rx.el.span(
                    CartographyState.parcel_detail["source_label"],
                    class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.h2(
                CartographyState.parcel_detail["name"],
                class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
            ),
            rx.el.p(
                f"{CartographyState.parcel_detail['locality']} · {CartographyState.parcel_detail['status_label']}",
                class_name="text-xs font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-1",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Culture active",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.p(
                    CartographyState.parcel_detail["crop_name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.div(
                    _health_badge(
                        CartographyState.parcel_detail["health_tone"],
                        CartographyState.parcel_detail["health_label"],
                    ),
                    rx.el.span(
                        CartographyState.parcel_detail["progress_pct"],
                        class_name="text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))]",
                    ),
                    class_name="flex items-center gap-2 mt-2",
                ),
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-4 py-3 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        class_name="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-[rgb(var(--ap-paper-rgb)/0.18)]",
    )


def map_parcel_detail() -> rx.Component:
    return rx.el.section(
        rx.cond(
            CartographyState.has_selection,
            rx.el.div(
                _detail_header(),
                rx.el.div(
                    _fact(
                        "Surface déclarée",
                        f"{CartographyState.parcel_detail['area_ha']} ha",
                        "ruler",
                    ),
                    _fact(
                        "Type de sol",
                        CartographyState.parcel_detail["soil_label"],
                        "layers",
                    ),
                    _fact(
                        "Irrigation",
                        CartographyState.parcel_detail["irrigation_label"],
                        "droplets",
                    ),
                    _fact(
                        "pH / MO",
                        f"{CartographyState.parcel_detail['ph']} · {CartographyState.parcel_detail['organic_matter']} %",
                        "flask-conical",
                    ),
                    _fact(
                        "Pente",
                        f"{CartographyState.parcel_detail['slope']} %",
                        "triangle",
                    ),
                    _fact(
                        "Coordonnées",
                        CartographyState.parcel_detail["coordinates"],
                        "compass",
                    ),
                    _fact(
                        "Cultures",
                        f"{CartographyState.parcel_detail['active_crops']} / {CartographyState.parcel_detail['crop_count']}",
                        "sprout",
                    ),
                    _fact(
                        "Stade en cours",
                        CartographyState.parcel_detail["crop_stage"],
                        "gauge",
                    ),
                    class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5",
                ),
                rx.el.div(
                    rx.el.span(
                        "Métadonnées de géométrie",
                        class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                    ),
                    rx.el.div(
                        _fact(
                            "Surface du contour",
                            f"{CartographyState.parcel_detail['geometry_area']} ha",
                            "shapes",
                        ),
                        _fact(
                            "Sommets",
                            CartographyState.parcel_detail["vertex_count"],
                            "git-commit-horizontal",
                        ),
                        _fact(
                            "Centre cartographique",
                            CartographyState.parcel_detail["geometry_center"],
                            "crosshair",
                        ),
                        _fact(
                            "Zoom conseillé",
                            CartographyState.parcel_detail["geometry_zoom"],
                            "zoom-in",
                        ),
                        _fact(
                            "Emprise",
                            CartographyState.parcel_detail["geometry_bbox"],
                            "scan",
                        ),
                        _fact(
                            "Mise à jour",
                            CartographyState.parcel_detail["geometry_updated"],
                            "history",
                        ),
                        _fact(
                            "Auteur",
                            CartographyState.parcel_detail[
                                "geometry_updated_by"
                            ],
                            "user-round",
                        ),
                        _fact(
                            "Projection",
                            "EPSG:4326 · WGS84",
                            "globe",
                        ),
                        class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3",
                    ),
                    rx.el.p(
                        CartographyState.parcel_detail["geometry_notes"],
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-3 leading-relaxed",
                    ),
                    class_name="mt-8 border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
                ),
                rx.el.p(
                    CartographyState.parcel_detail["notes"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-3 leading-relaxed",
                ),
                _draft_status(),
                _geometry_form(),
                _geometry_history(),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Historique parcellaire",
                            class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                        ),
                        rx.el.span(
                            f"{CartographyState.parcel_detail['intervention_count']} interventions · {CartographyState.parcel_detail['intervention_cost']} € engagés",
                            class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
                        ),
                        class_name="flex flex-wrap items-center gap-3",
                    ),
                    rx.cond(
                        CartographyState.interventions.length() > 0,
                        rx.el.div(
                            rx.el.div(
                                class_name="absolute left-[5px] top-2 bottom-2 w-px bg-gradient-to-b from-[rgb(var(--ap-accent-rgb)/0.50)] via-[rgb(var(--ap-sage-soft-rgb)/0.25)] to-transparent",
                            ),
                            rx.foreach(
                                CartographyState.interventions,
                                lambda item: _timeline_entry(
                                    item, key=item["id"].to_string()
                                ),
                            ),
                            class_name="relative flex flex-col mt-5",
                        ),
                        rx.el.p(
                            "Aucune intervention enregistrée sur cette parcelle.",
                            class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4",
                        ),
                    ),
                    class_name="mt-8 border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
                ),
                class_name="w-full",
            ),
            empty_state(
                "map-pinned",
                "Cliquez une parcelle sur la carte ou dans la liste pour afficher sa fiche complète.",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )
