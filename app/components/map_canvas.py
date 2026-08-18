import reflex as rx
import reflex_enterprise as rxe

from app.states.cartography_state import CartographyState

_MAP_ID = "cartographie-map"


def _polygon(shape: dict[str, rx.Var]) -> rx.Component:
    return rxe.map.polygon(
        rxe.map.tooltip(
            rx.el.div(
                rx.el.span(
                    f"{shape['code']} · {shape['name']}",
                    class_name="text-xs font-semibold text-[#04140d] block",
                ),
                rx.el.span(
                    f"{shape['crop_name']} · {shape['area_ha']:.1f} ha",
                    class_name="text-[10px] font-medium text-[#04140d]/70",
                ),
                class_name="min-w-0",
            ),
        ),
        positions=shape["positions"],
        path_options={
            "color": rx.cond(
                CartographyState.selected_parcel_id == shape["id"],
                "#d9f99d",
                shape["color"],
            ),
            "weight": rx.cond(
                CartographyState.selected_parcel_id == shape["id"], 4, 2
            ),
            "fillColor": shape["color"],
            "fillOpacity": rx.cond(
                CartographyState.selected_parcel_id == shape["id"], 0.5, 0.18
            ),
            "dashArray": rx.cond(shape["has_geometry"], "", "6 6"),
        },
    )


def _draft_vertex(point: dict[str, rx.Var], index: int) -> rx.Component:
    return rxe.map.circle_marker(
        rxe.map.tooltip(
            rx.el.span(
                f"Sommet {index + 1}",
                class_name="text-[10px] font-semibold text-[#04140d]",
            ),
        ),
        center=point,
        radius=6,
        path_options={
            "color": "#fbbf24",
            "weight": 2,
            "fillColor": "#a3e635",
            "fillOpacity": 0.9,
        },
    )


def _draw_overlay() -> rx.Component:
    """Aperçu du contour en cours de dessin (sommets, ligne, polygone)."""
    return rx.fragment(
        rx.cond(
            CartographyState.draft_ready,
            rxe.map.polygon(
                positions=CartographyState.draft_positions,
                path_options={
                    "color": "#fbbf24",
                    "weight": 3,
                    "dashArray": "8 6",
                    "fillColor": "#a3e635",
                    "fillOpacity": 0.22,
                },
            ),
            rxe.map.polyline(
                positions=CartographyState.draft_points,
                path_options={
                    "color": "#fbbf24",
                    "weight": 3,
                    "dashArray": "8 6",
                },
            ),
        ),
        rx.foreach(
            CartographyState.draft_points,
            lambda point, index: _draft_vertex(point, index),
        ),
    )


def _base_layer() -> rx.Component:
    return rx.match(
        CartographyState.basemap,
        (
            "satellite",
            rxe.map.tile_layer(
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
            ),
        ),
        (
            "terrain",
            rxe.map.tile_layer(
                url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                attribution="Map data © OpenStreetMap contributors, SRTM | Map style © OpenTopoMap",
            ),
        ),
        (
            "sombre",
            rxe.map.tile_layer(
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                attribution="© OpenStreetMap contributors © CARTO",
            ),
        ),
        rxe.map.tile_layer(
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
            attribution="© OpenStreetMap contributors © CARTO",
        ),
    )


def _location_layers() -> rx.Component:
    return rx.fragment(
        rxe.map.circle_marker(
            rxe.map.tooltip("Centre de l’exploitation"),
            center=CartographyState.farm_center,
            radius=10,
            path_options={
                "color": "#14532d",
                "weight": 3,
                "fillColor": "#a3e635",
                "fillOpacity": 0.95,
            },
        ),
        rxe.map.marker(
            rxe.map.popup(
                rx.el.div(
                    rx.el.p(
                        "Centre de l’exploitation",
                        class_name="font-semibold text-[#04140d]",
                    ),
                    rx.el.p(
                        CartographyState.farm_coordinates_label,
                        class_name="text-xs text-[#04140d]/70 mt-1",
                    ),
                ),
            ),
            position=CartographyState.farm_center,
        ),
        rx.cond(
            CartographyState.has_browser_location,
            rx.fragment(
                rxe.map.circle_marker(
                    rxe.map.tooltip("Position navigateur"),
                    center=CartographyState.browser_location,
                    radius=9,
                    path_options={
                        "color": "#1d4ed8",
                        "weight": 3,
                        "fillColor": "#38bdf8",
                        "fillOpacity": 0.95,
                    },
                ),
                rxe.map.marker(
                    rxe.map.popup(
                        rx.el.div(
                            rx.el.p(
                                "Position navigateur",
                                class_name="font-semibold text-[#04140d]",
                            ),
                            rx.el.p(
                                CartographyState.browser_coordinates_label,
                                class_name="text-xs text-[#04140d]/70 mt-1",
                            ),
                        ),
                    ),
                    position=CartographyState.browser_location,
                ),
            ),
            rx.fragment(),
        ),
    )


def _draw_toolbar() -> rx.Component:
    """Commandes de dessin de contour, intégrées à l'outil métier."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("pen-tool", class_name="h-3.5 w-3.5 text-lime-300"),
                rx.el.span(
                    "Dessin assisté du contour",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.span(
                CartographyState.draft_state_label,
                class_name=rx.match(
                    CartographyState.draft_state_tone,
                    (
                        "good",
                        "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
                    ),
                    (
                        "warn",
                        "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
                    ),
                    (
                        "info",
                        "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit",
                    ),
                    "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit",
                ),
            ),
            rx.el.span(
                CartographyState.parcel_detail["code"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            CartographyState.draw_hint,
            class_name="text-[11px] font-medium text-emerald-100/55 leading-relaxed mt-2",
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    CartographyState.draw_mode,
                    rx.icon("square-dashed", class_name="h-4 w-4"),
                    rx.icon("pen-tool", class_name="h-4 w-4"),
                ),
                rx.el.span(
                    rx.cond(
                        CartographyState.draw_mode,
                        "Quitter le mode dessin",
                        "Dessiner le contour",
                    )
                ),
                on_click=CartographyState.toggle_draw_mode,
                class_name=rx.cond(
                    CartographyState.draw_mode,
                    "flex items-center gap-2 rounded-xl border border-amber-300/40 bg-amber-300/15 px-4 py-2.5 text-sm font-semibold text-amber-100 hover:bg-amber-300/25 transition-colors w-fit",
                    "flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold text-[#04140d] hover:bg-lime-200 transition-colors w-fit",
                ),
            ),
            rx.el.button(
                rx.icon("undo-2", class_name="h-4 w-4"),
                rx.el.span("Annuler le dernier sommet"),
                on_click=CartographyState.undo_vertex,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/75 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("eraser", class_name="h-4 w-4"),
                rx.el.span("Vider le tracé"),
                on_click=CartographyState.clear_vertices,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/75 hover:border-amber-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("check-check", class_name="h-4 w-4"),
                rx.el.span("Terminer le contour"),
                on_click=CartographyState.finish_drawing,
                disabled=~CartographyState.draft_ready,
                class_name=rx.cond(
                    CartographyState.draft_ready,
                    "flex items-center gap-2 rounded-xl border border-lime-300/40 bg-lime-300/15 px-4 py-2.5 text-sm font-semibold text-lime-100 hover:bg-lime-300/25 transition-colors w-fit",
                    "flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/30 cursor-not-allowed w-fit",
                ),
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{CartographyState.draft_vertex_count} sommet(s) posé(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{CartographyState.draft_area_ha:.2f} ha dessinés",
                class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{CartographyState.declared_area:.2f} ha déclarés",
                class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.cond(
                CartographyState.draft_area_ha > 0,
                rx.el.span(
                    f"écart {CartographyState.draft_gap_pct:.1f} %",
                    class_name=rx.cond(
                        CartographyState.draft_gap_tone == "bad",
                        "rounded-full border border-red-400/30 bg-red-500/10 px-2.5 py-1 text-[10px] font-bold text-red-300 w-fit",
                        "rounded-full border border-lime-300/30 bg-lime-300/10 px-2.5 py-1 text-[10px] font-bold text-lime-200 w-fit",
                    ),
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        class_name="w-full rounded-2xl border border-lime-300/20 bg-[#04140d]/70 p-4 mt-5",
    )


def _legend(label: str, dot: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=dot),
        rx.el.span(
            label, class_name="text-[11px] font-medium text-emerald-100/60"
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3",
    )


def map_canvas() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Cartographie parcellaire",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Carte vivante de l'exploitation",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Cliquez un îlot sur la carte pour ouvrir sa fiche complète et son historique d'interventions.",
                    class_name="text-xs font-medium text-emerald-100/50 mt-2 max-w-xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("crosshair", class_name="h-4 w-4"),
                    rx.el.span("Recentrer"),
                    on_click=rxe.map.api(_MAP_ID).fly_to(
                        CartographyState.center, CartographyState.zoom
                    ),
                    class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/75 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("zoom-out", class_name="h-4 w-4"),
                    rx.el.span("Vue exploitation"),
                    on_click=rxe.map.api(_MAP_ID).fly_to(
                        CartographyState.farm_center, 14.0
                    ),
                    class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/75 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("locate-fixed", class_name="h-4 w-4"),
                    rx.el.span("Me localiser"),
                    on_click=[
                        CartographyState.request_browser_location,
                        rxe.map.api(_MAP_ID).locate(
                            rxe.map.locate_options(
                                set_view=True,
                                max_zoom=16,
                                timeout=10000,
                                enable_high_accuracy=True,
                                watch=False,
                            )
                        ),
                    ],
                    class_name="flex items-center gap-2 rounded-xl border border-sky-300/30 bg-sky-300/10 px-4 py-2.5 text-sm font-semibold text-sky-100 hover:bg-sky-300/20 transition-colors w-fit",
                ),
                rx.el.div(
                    rx.icon(
                        "layers-3",
                        class_name="h-4 w-4 text-lime-300 shrink-0",
                    ),
                    rx.el.select(
                        rx.foreach(
                            CartographyState.basemap_options,
                            lambda option: rx.el.option(
                                option["label"], value=option["value"]
                            ),
                        ),
                        default_value=CartographyState.basemap,
                        on_change=CartographyState.set_basemap,
                        class_name="appearance-none cursor-pointer bg-transparent pr-6 text-sm font-semibold text-emerald-100/80 outline-hidden",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute right-2 h-4 w-4 text-emerald-100/45",
                    ),
                    class_name="relative flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 pl-3 pr-2 py-2.5",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.el.div(
            _stat(
                "Îlots cartographiés",
                CartographyState.mapped_count,
                "avec contour",
            ),
            _stat(
                "Parcelles affichées", CartographyState.parcel_count, "îlots"
            ),
            _stat(
                "Surface affichée",
                f"{CartographyState.mapped_area:.1f}",
                "ha",
            ),
            _stat(
                "Interventions liées",
                CartographyState.intervention_count,
                "chantiers",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full mt-5",
        ),
        _draw_toolbar(),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("building-2", class_name="h-4 w-4 text-lime-300"),
                    rx.el.div(
                        rx.el.span(
                            "Exploitation",
                            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/50",
                        ),
                        rx.el.span(
                            CartographyState.farm_coordinates_label,
                            class_name="text-xs font-semibold text-emerald-50 mt-0.5",
                        ),
                        class_name="flex flex-col",
                    ),
                    class_name="flex items-center gap-2 min-w-0",
                ),
                rx.el.div(
                    rx.icon("locate-fixed", class_name="h-4 w-4 text-sky-300"),
                    rx.el.div(
                        rx.el.span(
                            "Navigateur",
                            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/50",
                        ),
                        rx.cond(
                            CartographyState.has_browser_location,
                            rx.el.span(
                                CartographyState.browser_coordinates_label,
                                class_name="text-xs font-semibold text-sky-100 mt-0.5",
                            ),
                            rx.el.span(
                                "Autorisation non accordée",
                                class_name="text-xs font-semibold text-emerald-100/45 mt-0.5",
                            ),
                        ),
                        class_name="flex flex-col",
                    ),
                    class_name="flex items-center gap-2 min-w-0",
                ),
                rx.el.span(
                    CartographyState.location_status,
                    class_name="text-[11px] font-medium text-emerald-100/55 lg:ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-4 w-full",
            ),
            rx.cond(
                CartographyState.location_error != "",
                rx.el.div(
                    rx.icon(
                        "triangle-alert",
                        class_name="h-3.5 w-3.5 text-amber-300 shrink-0",
                    ),
                    rx.el.p(
                        CartographyState.location_error,
                        class_name="text-[11px] font-medium text-amber-100/80",
                    ),
                    class_name="flex items-start gap-2 rounded-xl border border-amber-300/20 bg-amber-300/[0.07] px-3 py-2 mt-3",
                ),
                rx.fragment(),
            ),
            class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-4 mt-5",
        ),
        rx.el.div(
            rxe.map(
                _base_layer(),
                _location_layers(),
                rx.foreach(CartographyState.shapes, _polygon),
                _draw_overlay(),
                rxe.map.scale_control(position="bottomleft"),
                rxe.map.zoom_control(position="topright"),
                id=_MAP_ID,
                center=CartographyState.center,
                zoom=CartographyState.zoom,
                zoom_control=False,
                height="100%",
                width="100%",
                on_click=CartographyState.handle_map_click,
                on_zoom=CartographyState.handle_zoom.debounce(300),
                on_locationfound=CartographyState.handle_location_found,
                on_locationerror=CartographyState.handle_location_error,
                class_name="h-full w-full",
            ),
            rx.el.div(
                rx.icon("compass", class_name="h-3.5 w-3.5 text-lime-300"),
                rx.el.span(
                    "Nord",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/70",
                ),
                class_name="pointer-events-none absolute left-4 top-4 z-[500] flex items-center gap-1.5 rounded-full border border-white/10 bg-[#04140d]/80 px-2.5 py-1 backdrop-blur-xl",
            ),
            rx.el.div(
                _legend(
                    "Contour enregistré", "h-2 w-2 rounded-full bg-lime-300"
                ),
                _legend(
                    "Contour à tracer",
                    "h-2 w-2 rounded-full border border-dashed border-amber-300",
                ),
                _legend(
                    "Parcelle sélectionnée",
                    "h-2 w-2 rounded-full bg-emerald-200 ring-2 ring-lime-300/50",
                ),
                _legend(
                    "Contour en cours de dessin",
                    "h-2 w-2 rounded-full bg-amber-300 ring-2 ring-amber-300/40",
                ),
                class_name="pointer-events-none absolute left-4 bottom-14 z-[500] flex flex-col gap-1.5 rounded-2xl border border-white/10 bg-[#04140d]/80 px-3 py-2.5 backdrop-blur-xl",
            ),
            rx.cond(
                CartographyState.draw_mode,
                rx.el.div(
                    rx.icon(
                        "pen-tool", class_name="h-3.5 w-3.5 text-amber-300"
                    ),
                    rx.el.span(
                        f"Mode dessin · {CartographyState.draft_vertex_count} sommet(s)",
                        class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-100",
                    ),
                    class_name="pointer-events-none absolute right-4 bottom-14 z-[500] flex items-center gap-1.5 rounded-full border border-amber-300/30 bg-[#04140d]/85 px-3 py-1.5 backdrop-blur-xl",
                ),
                rx.fragment(),
            ),
            class_name=rx.cond(
                CartographyState.draw_mode,
                "relative mt-5 w-full min-w-[300px] min-h-[28rem] h-[38rem] overflow-hidden rounded-3xl border-2 border-amber-300/40 bg-slate-100 cursor-crosshair",
                "relative mt-5 w-full min-w-[300px] min-h-[28rem] h-[38rem] overflow-hidden rounded-3xl border border-lime-300/15 bg-slate-100",
            ),
        ),
        rx.cond(
            CartographyState.geometry_ready,
            rx.fragment(),
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 text-amber-300 shrink-0",
                ),
                rx.el.p(
                    "Les colonnes de géométrie ne sont pas encore présentes en base : les contours affichés sont générés à la volée et l'enregistrement est désactivé.",
                    class_name="text-xs font-medium text-amber-100/80",
                ),
                class_name="flex items-center gap-2 rounded-2xl border border-amber-300/25 bg-amber-300/[0.07] px-4 py-3 mt-4",
            ),
        ),
        class_name="flex-1 min-w-0 w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )
