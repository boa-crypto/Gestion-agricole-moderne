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
                    class_name="text-xs font-semibold text-[#0A0A08] block",
                ),
                rx.el.span(
                    f"{shape['crop_name']} · {shape['area_ha']:.1f} ha",
                    class_name="text-[10px] font-medium text-[#0A0A08]/70",
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
                class_name="text-[10px] font-semibold text-[#0A0A08]",
            ),
        ),
        center=point,
        radius=6,
        path_options={
            "color": "#FF8A5B",
            "weight": 2,
            "fillColor": "#D8FA5E",
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
                    "color": "#FF8A5B",
                    "weight": 3,
                    "dashArray": "8 6",
                    "fillColor": "#D8FA5E",
                    "fillOpacity": 0.22,
                },
            ),
            rxe.map.polyline(
                positions=CartographyState.draft_points,
                path_options={
                    "color": "#FF8A5B",
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
                "fillColor": "#D8FA5E",
                "fillOpacity": 0.95,
            },
        ),
        rxe.map.marker(
            rxe.map.popup(
                rx.el.div(
                    rx.el.p(
                        "Centre de l’exploitation",
                        class_name="font-semibold text-[#0A0A08]",
                    ),
                    rx.el.p(
                        CartographyState.farm_coordinates_label,
                        class_name="text-xs text-[#0A0A08]/70 mt-1",
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
                        "fillColor": "#9CC3FF",
                        "fillOpacity": 0.95,
                    },
                ),
                rxe.map.marker(
                    rxe.map.popup(
                        rx.el.div(
                            rx.el.p(
                                "Position navigateur",
                                class_name="font-semibold text-[#0A0A08]",
                            ),
                            rx.el.p(
                                CartographyState.browser_coordinates_label,
                                class_name="text-xs text-[#0A0A08]/70 mt-1",
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
                rx.icon("pen-tool", class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
                rx.el.span(
                    "Dessin assisté du contour",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.span(
                CartographyState.draft_state_label,
                class_name=rx.match(
                    CartographyState.draft_state_tone,
                    (
                        "good",
                        "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
                    ),
                    (
                        "warn",
                        "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
                    ),
                    (
                        "info",
                        "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
                    ),
                    "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
                ),
            ),
            rx.el.span(
                CartographyState.parcel_detail["code"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            CartographyState.draw_hint,
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 leading-relaxed mt-2",
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
                    "flex items-center gap-2 rounded-none border border-[#ff8a5b]/40 bg-[#ff8a5b]/15 px-4 py-2.5 text-sm font-semibold text-[#ffdccb] hover:bg-[#ff8a5b]/25 transition-colors w-fit",
                    "flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold text-[#0A0A08] hover:bg-[#e4ff9b] transition-colors w-fit",
                ),
            ),
            rx.el.button(
                rx.icon("undo-2", class_name="h-4 w-4"),
                rx.el.span("Annuler le dernier sommet"),
                on_click=CartographyState.undo_vertex,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/75 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("eraser", class_name="h-4 w-4"),
                rx.el.span("Vider le tracé"),
                on_click=CartographyState.clear_vertices,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/75 hover:border-[#ff8a5b]/30 hover:text-[#f2efe4] transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("check-check", class_name="h-4 w-4"),
                rx.el.span("Terminer le contour"),
                on_click=CartographyState.finish_drawing,
                disabled=~CartographyState.draft_ready,
                class_name=rx.cond(
                    CartographyState.draft_ready,
                    "flex items-center gap-2 rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/15 px-4 py-2.5 text-sm font-semibold text-[#efffc4] hover:bg-[#d8fa5e]/25 transition-colors w-fit",
                    "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/30 cursor-not-allowed w-fit",
                ),
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{CartographyState.draft_vertex_count} sommet(s) posé(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{CartographyState.draft_area_ha:.2f} ha dessinés",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{CartographyState.declared_area:.2f} ha déclarés",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.cond(
                CartographyState.draft_area_ha > 0,
                rx.el.span(
                    f"écart {CartographyState.draft_gap_pct:.1f} %",
                    class_name=rx.cond(
                        CartographyState.draft_gap_tone == "bad",
                        "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2.5 py-1 text-[10px] font-bold text-[#ff9b8c] w-fit",
                        "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2.5 py-1 text-[10px] font-bold text-[#e4ff9b] w-fit",
                    ),
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        class_name="w-full rounded-none border border-[#d8fa5e]/20 bg-[#0A0A08]/70 p-4 mt-5",
    )


def _legend(label: str, dot: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=dot),
        rx.el.span(
            label, class_name="text-[11px] font-medium text-[#c9c5b4]/60"
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-2xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-3",
    )


def map_canvas() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Cartographie parcellaire",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Carte vivante de l'exploitation",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Cliquez un îlot sur la carte pour ouvrir sa fiche complète et son historique d'interventions.",
                    class_name="text-xs font-medium text-[#c9c5b4]/50 mt-2 max-w-xl",
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
                    class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/75 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("zoom-out", class_name="h-4 w-4"),
                    rx.el.span("Vue exploitation"),
                    on_click=rxe.map.api(_MAP_ID).fly_to(
                        CartographyState.farm_center, 14.0
                    ),
                    class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/75 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
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
                    class_name="flex items-center gap-2 rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-4 py-2.5 text-sm font-semibold text-[#e2ecff] hover:bg-[#9cc3ff]/20 transition-colors w-fit",
                ),
                rx.el.div(
                    rx.icon(
                        "layers-3",
                        class_name="h-4 w-4 text-[#d8fa5e] shrink-0",
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
                        class_name="appearance-none cursor-pointer bg-transparent pr-6 text-sm font-semibold text-[#c9c5b4]/80 outline-hidden",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute right-2 h-4 w-4 text-[#c9c5b4]/45",
                    ),
                    class_name="relative flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] pl-3 pr-2 py-2.5",
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
                    rx.icon("building-2", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.div(
                        rx.el.span(
                            "Exploitation",
                            class_name="ap-eyebrow text-[#c9c5b4]/50",
                        ),
                        rx.el.span(
                            CartographyState.farm_coordinates_label,
                            class_name="text-xs font-semibold text-[#f2efe4] mt-0.5",
                        ),
                        class_name="flex flex-col",
                    ),
                    class_name="flex items-center gap-2 min-w-0",
                ),
                rx.el.div(
                    rx.icon("locate-fixed", class_name="h-4 w-4 text-[#9cc3ff]"),
                    rx.el.div(
                        rx.el.span(
                            "Navigateur",
                            class_name="ap-eyebrow text-[#c9c5b4]/50",
                        ),
                        rx.cond(
                            CartographyState.has_browser_location,
                            rx.el.span(
                                CartographyState.browser_coordinates_label,
                                class_name="text-xs font-semibold text-[#e2ecff] mt-0.5",
                            ),
                            rx.el.span(
                                "Autorisation non accordée",
                                class_name="text-xs font-semibold text-[#c9c5b4]/45 mt-0.5",
                            ),
                        ),
                        class_name="flex flex-col",
                    ),
                    class_name="flex items-center gap-2 min-w-0",
                ),
                rx.el.span(
                    CartographyState.location_status,
                    class_name="text-[11px] font-medium text-[#c9c5b4]/55 lg:ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-4 w-full",
            ),
            rx.cond(
                CartographyState.location_error != "",
                rx.el.div(
                    rx.icon(
                        "triangle-alert",
                        class_name="h-3.5 w-3.5 text-[#ff8a5b] shrink-0",
                    ),
                    rx.el.p(
                        CartographyState.location_error,
                        class_name="text-[11px] font-medium text-[#ffdccb]/80",
                    ),
                    class_name="flex items-start gap-2 rounded-none border border-[#ff8a5b]/20 bg-[#ff8a5b]/[0.07] px-3 py-2 mt-3",
                ),
                rx.fragment(),
            ),
            class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] p-4 mt-5",
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
                rx.icon("compass", class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
                rx.el.span(
                    "Nord",
                    class_name="ap-eyebrow text-[#c9c5b4]/70",
                ),
                class_name="pointer-events-none absolute left-4 top-4 z-[500] flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#0A0A08]/80 px-2.5 py-1 ",
            ),
            rx.el.div(
                _legend(
                    "Contour enregistré", "h-2 w-2 rounded-none bg-[#d8fa5e]"
                ),
                _legend(
                    "Contour à tracer",
                    "h-2 w-2 rounded-none border border-dashed border-[#ff8a5b]",
                ),
                _legend(
                    "Parcelle sélectionnée",
                    "h-2 w-2 rounded-none bg-[#b3af9f] ring-2 ring-[#d8fa5e]/50",
                ),
                _legend(
                    "Contour en cours de dessin",
                    "h-2 w-2 rounded-none bg-[#ff8a5b] ring-2 ring-[#ff8a5b]/40",
                ),
                class_name="pointer-events-none absolute left-4 bottom-14 z-[500] flex flex-col gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#0A0A08]/80 px-3 py-2.5 ",
            ),
            rx.cond(
                CartographyState.draw_mode,
                rx.el.div(
                    rx.icon(
                        "pen-tool", class_name="h-3.5 w-3.5 text-[#ff8a5b]"
                    ),
                    rx.el.span(
                        f"Mode dessin · {CartographyState.draft_vertex_count} sommet(s)",
                        class_name="ap-eyebrow text-[#ffdccb]",
                    ),
                    class_name="pointer-events-none absolute right-4 bottom-14 z-[500] flex items-center gap-1.5 rounded-none border border-[#ff8a5b]/30 bg-[#0A0A08]/85 px-3 py-1.5 ",
                ),
                rx.fragment(),
            ),
            class_name=rx.cond(
                CartographyState.draw_mode,
                "relative mt-5 w-full min-w-[300px] min-h-[28rem] h-[38rem] overflow-hidden rounded-none border-2 border-[#ff8a5b]/40 bg-[#e4e2d8] cursor-crosshair",
                "relative mt-5 w-full min-w-[300px] min-h-[28rem] h-[38rem] overflow-hidden rounded-none border border-[#d8fa5e]/15 bg-[#e4e2d8]",
            ),
        ),
        rx.cond(
            CartographyState.geometry_ready,
            rx.fragment(),
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 text-[#ff8a5b] shrink-0",
                ),
                rx.el.p(
                    "Les colonnes de géométrie ne sont pas encore présentes en base : les contours affichés sont générés à la volée et l'enregistrement est désactivé.",
                    class_name="text-xs font-medium text-[#ffdccb]/80",
                ),
                class_name="flex items-center gap-2 rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.07] px-4 py-3 mt-4",
            ),
        ),
        class_name="flex-1 min-w-0 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
