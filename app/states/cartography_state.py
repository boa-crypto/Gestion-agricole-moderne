"""État de l'espace cartographie interactive.

Carte réelle (Leaflet via reflex-enterprise), contours GeoJSON persistés des
parcelles, sélection par clic, fiche complète et historique des interventions.
Toutes les lectures et écritures passent par `rx.asession()` en SQL brut.
"""

from __future__ import annotations

import datetime
import json
import math
from typing import TypedDict

import reflex as rx
from reflex_enterprise.components.map.types import LatLng
from sqlalchemy import text

from app.database import ensure_local_database, ensure_remediation_log_table
from app.geometry import (
    DEFAULT_LAT,
    DEFAULT_LON,
    _ring_area_ha,
    build_parcel_polygon,
    geometry_columns_ready,
    seed_parcel_geometry,
)
from app.date_utils import as_date, as_datetime
from app.phenology_ops import parcel_stage_map, stage_filter_options
from app.seed import seed_dashboard_data
from app.states.dashboard_state import (
    HEALTH_LABELS,
    HEALTH_TONES,
    INTERVENTION_LABELS,
    INTERVENTION_STATUS_LABELS,
    IRRIGATION_LABELS,
    MONTHS,
    PARCEL_STATUS_LABELS,
    SOIL_LABELS,
    WEEKDAYS_SHORT,
)

import logging

GEOMETRY_SOURCE_LABELS: dict[str, str] = {
    "AUCUNE": "Aucun contour",
    "GENEREE": "Contour généré",
    "DESSINEE": "Contour dessiné",
    "IMPORTEE": "Contour importé",
    "CADASTRE": "Contour cadastral",
}

STATUS_TONES: dict[str, str] = {
    "PLANIFIEE": "planned",
    "EN_COURS": "running",
    "REALISEE": "done",
    "REPORTEE": "late",
    "ANNULEE": "cancelled",
}

PARCEL_STATUS_KEYS: list[str] = [
    "EN_CULTURE",
    "JACHERE",
    "PREPARATION",
    "RECOLTEE",
    "INACTIVE",
]


class Option(TypedDict):
    value: str
    label: str


MapPoint = LatLng


class ParcelShape(TypedDict):
    id: int
    name: str
    code: str
    area_ha: float
    status: str
    status_label: str
    is_organic: bool
    crop_name: str
    health_label: str
    health_tone: str
    progress: int
    progress_pct: str
    color: str
    positions: list[MapPoint]
    center: MapPoint
    zoom: float
    has_geometry: bool
    source_label: str
    vertex_count: int
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    locality: str
    stage_label: str


class GeometryLog(TypedDict):
    """Trace d'une mise à jour de contour consignée au journal local."""

    id: int
    action_label: str
    tone: str
    icon: str
    note: str
    author: str
    date_label: str


class InterventionEntry(TypedDict):
    id: int
    title: str
    type: str
    type_label: str
    status_label: str
    tone: str
    date_label: str
    done_label: str
    operator: str
    equipment: str
    target: str
    crop_name: str
    area_ha: float
    cost: float
    product_label: str
    is_done: bool


EMPTY_DETAIL: dict[str, str] = {
    "id": "0",
    "name": "Aucune parcelle sélectionnée",
    "code": "—",
    "area_ha": "0.0",
    "status_label": "—",
    "soil_label": "—",
    "irrigation_label": "—",
    "locality": "—",
    "coordinates": "—",
    "slope": "0.0",
    "ph": "0.0",
    "organic_matter": "0.0",
    "organic_label": "Conventionnel",
    "notes": "—",
    "crop_name": "Sans culture active",
    "crop_species": "—",
    "crop_stage": "—",
    "health_label": "—",
    "health_tone": "muted",
    "progress_pct": "0%",
    "crop_count": "0",
    "active_crops": "0",
    "source_label": "Aucun contour",
    "vertex_count": "0",
    "geometry_area": "0.0",
    "geometry_center": "—",
    "geometry_bbox": "—",
    "geometry_zoom": "15",
    "geometry_updated": "—",
    "geometry_updated_by": "—",
    "geometry_notes": "—",
    "intervention_count": "0",
    "intervention_cost": "0",
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _options(keys: list[str], labels: dict[str, str]) -> list[Option]:
    return [{"value": key, "label": labels.get(key, key)} for key in keys]


def _ring_from_geojson(raw: str) -> list[list[float]]:
    """Extrait le premier anneau (lon, lat) d'un GeoJSON quelconque.

    Formats acceptés : Polygon, MultiPolygon, Feature et FeatureCollection.
    Toute autre structure (Point, LineString, GeometryCollection, JSON hors
    GeoJSON) est refusée avec un message métier explicite.
    """
    data = json.loads(raw)
    if isinstance(data, list):
        raise ValueError(
            "Un tableau JSON n'est pas un GeoJSON : collez un objet Polygon, "
            "MultiPolygon, Feature ou FeatureCollection."
        )
    if isinstance(data, dict) and data.get("type") == "FeatureCollection":
        features = data.get("features") or []
        if not features:
            raise ValueError("La FeatureCollection ne contient aucune entité.")
        data = features[0]
    if isinstance(data, dict) and data.get("type") == "Feature":
        data = data.get("geometry") or {}
    if not isinstance(data, dict):
        raise ValueError("Structure GeoJSON non reconnue.")
    kind = str(data.get("type", ""))
    if not kind:
        raise ValueError(
            "Le champ « type » du GeoJSON est absent : impossible de "
            "déterminer la nature de la géométrie."
        )
    coords = data.get("coordinates")
    if kind == "GeometryCollection":
        raise ValueError(
            "Une GeometryCollection n'est pas exploitable comme contour "
            "d'îlot : fournissez un Polygon ou un MultiPolygon."
        )
    if kind == "Polygon":
        if not isinstance(coords, list) or not coords:
            raise ValueError("Le Polygon ne contient aucun anneau.")
        ring = coords[0]
    elif kind == "MultiPolygon":
        if (
            not isinstance(coords, list)
            or not coords
            or not isinstance(coords[0], list)
            or not coords[0]
        ):
            raise ValueError("Le MultiPolygon ne contient aucun anneau.")
        ring = coords[0][0]
    else:
        raise ValueError(
            f"Géométrie « {kind} » refusée : seules les géométries Polygon ou "
            "MultiPolygon décrivent un contour de parcelle."
        )
    if not isinstance(ring, list):
        raise ValueError("L'anneau de coordonnées est illisible.")
    if len(ring) > 2000:
        raise ValueError(
            "Le contour dépasse 2000 sommets : simplifiez le tracé avant "
            "enregistrement."
        )
    points: list[list[float]] = []
    for point in ring:
        if not isinstance(point, list) or len(point) < 2:
            raise ValueError("Un sommet ne contient pas deux coordonnées.")
        try:
            lon = float(point[0])
            lat = float(point[1])
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Un sommet contient une coordonnée non numérique."
            ) from error
        if not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
            raise ValueError("Coordonnées hors des bornes WGS84 (lon/lat).")
        points.append([round(lon, 6), round(lat, 6)])
    if len(points) >= 2 and points[0] != points[-1]:
        points.append(list(points[0]))
    if len(points) < 4:
        raise ValueError("Un contour doit comporter au moins 3 sommets.")
    return points


def safe_ring_from_geojson(raw: str) -> tuple[list[list[float]], str]:
    """Valide un GeoJSON utilisateur et retourne `(ring, message_erreur)`.

    Les rejets sont des cas de saisie métier : ils ne produisent aucune trace
    de journalisation, seulement un message en français à afficher.
    """
    payload = (raw or "").strip()
    if not payload:
        return [], "Collez un GeoJSON de contour à enregistrer."
    try:
        ring = _ring_from_geojson(payload)
    except json.JSONDecodeError as error:
        logging.exception("Unexpected error")
        return [], (
            f"JSON invalide : vérifiez la syntaxe collée ({error.msg} "
            f"ligne {error.lineno}, colonne {error.colno})."
        )
    except (ValueError, KeyError, TypeError, IndexError) as error:
        logging.exception("Unexpected error")
        return [], f"GeoJSON refusé : {error}"
    return ring, ""


def _shape_from_ring(ring: list[list[float]]) -> dict[str, float | str | int]:
    lats = [point[1] for point in ring[:-1]]
    lons = [point[0] for point in ring[:-1]]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    return {
        "geojson": json.dumps(
            {"type": "Polygon", "coordinates": [ring]}, separators=(",", ":")
        ),
        "center_lat": round(center_lat, 6),
        "center_lon": round(center_lon, 6),
        "bbox_min_lat": round(min(lats), 6),
        "bbox_min_lon": round(min(lons), 6),
        "bbox_max_lat": round(max(lats), 6),
        "bbox_max_lon": round(max(lons), 6),
        "area_ha": round(_ring_area_ha(ring, center_lat), 2),
        "vertex_count": len(ring) - 1,
    }


def _zoom_for_span(span: float) -> float:
    if span <= 0.004:
        return 17.0
    if span <= 0.01:
        return 16.0
    if span <= 0.02:
        return 15.5
    if span <= 0.05:
        return 15.0
    return 14.0


def _positions(ring: list[list[float]]) -> list[MapPoint]:
    return [{"lat": point[1], "lng": point[0]} for point in ring]


class CartographyState(rx.State):
    """Cartographie parcellaire interactive."""

    is_loading: bool = True
    today_label: str = ""
    geometry_ready: bool = True

    search: str = ""
    status_filter: str = "TOUS"
    geometry_filter: str = "TOUS"
    # Filtre « Afficher par stade » du suivi phénologique.
    # `stage_filter` porte la valeur sélectionnée, `stage_filter_options` la
    # liste stable des stades réellement disponibles (observations existantes).
    stage_filter: str = "TOUS"
    stage_filter_options: list[Option] = []
    _parcel_stages: dict[str, str] = {}

    shapes: list[ParcelShape] = []
    selected_parcel_id: int = 0
    parcel_detail: dict[str, str] = EMPTY_DETAIL
    interventions: list[InterventionEntry] = []

    center: MapPoint = {"lat": DEFAULT_LAT, "lng": DEFAULT_LON}
    zoom: float = 14.0
    farm_center: MapPoint = {"lat": DEFAULT_LAT, "lng": DEFAULT_LON}
    browser_location: MapPoint = {"lat": 0.0, "lng": 0.0}
    has_browser_location: bool = False
    location_status: str = "Position navigateur non demandée"
    location_error: str = ""

    geojson_draft: str = ""
    geometry_error: str = ""
    geometry_notice: str = ""
    geometry_logs: list[GeometryLog] = []
    form_key: int = 0

    # --- Dessin assisté du contour -----------------------------------
    # Mode dessin : chaque clic sur la carte pose un sommet du contour de la
    # parcelle sélectionnée. Aucun enregistrement tant que le contour n'est
    # pas terminé puis validé via le brouillon GeoJSON existant.
    draw_mode: bool = False
    draft_points: list[MapPoint] = []

    status_options: list[Option] = _options(
        PARCEL_STATUS_KEYS, PARCEL_STATUS_LABELS
    )
    geometry_options: list[Option] = [
        {"value": "AVEC", "label": "Avec contour tracé"},
        {"value": "SANS", "label": "Sans contour"},
    ]
    basemap: str = "plan"
    basemap_options: list[Option] = [
        {"value": "plan", "label": "Plan clair"},
        {"value": "satellite", "label": "Satellite"},
        {"value": "terrain", "label": "Terrain / relief"},
        {"value": "sombre", "label": "Sombre"},
    ]

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def stage_options(self) -> list[Option]:
        """Alias historique consommé par la barre latérale de la carte."""
        return self.stage_filter_options

    @rx.var
    def stage_filter_label(self) -> str:
        """Libellé lisible du filtre de stade sélectionné."""
        if self.stage_filter == "TOUS":
            return "Tous les stades"
        for option in self.stage_filter_options:
            if option["value"] == self.stage_filter:
                return option["label"]
        return self.stage_filter

    @rx.var
    def farm_coordinates_label(self) -> str:
        return (
            f"{self.farm_center['lat']:.5f}° / {self.farm_center['lng']:.5f}°"
        )

    @rx.var
    def browser_coordinates_label(self) -> str:
        return f"{self.browser_location['lat']:.5f}° / {self.browser_location['lng']:.5f}°"

    @rx.var
    def parcel_count(self) -> int:
        return len(self.shapes)

    @rx.var
    def mapped_count(self) -> int:
        return len([s for s in self.shapes if s["has_geometry"]])

    @rx.var
    def mapped_area(self) -> float:
        return round(sum(s["area_ha"] for s in self.shapes), 1)

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_parcel_id > 0

    @rx.var
    def draft_vertex_count(self) -> int:
        return len(self.draft_points)

    @rx.var
    def draft_ready(self) -> bool:
        return len(self.draft_points) >= 3

    @rx.var
    def draft_positions(self) -> list[MapPoint]:
        """Anneau fermé du contour en cours, pour l'aperçu cartographique."""
        if len(self.draft_points) < 3:
            return list(self.draft_points)
        return list(self.draft_points) + [self.draft_points[0]]

    @rx.var
    def draft_area_ha(self) -> float:
        if len(self.draft_points) < 3:
            return 0.0
        ring = [[p["lng"], p["lat"]] for p in self.draft_points]
        ring.append(list(ring[0]))
        return round(_ring_area_ha(ring, self.draft_points[0]["lat"]), 2)

    @rx.var
    def declared_area(self) -> float:
        for shape in self.shapes:
            if shape["id"] == self.selected_parcel_id:
                return shape["area_ha"]
        return 0.0

    @rx.var
    def draft_gap_pct(self) -> float:
        declared = self.declared_area
        if declared <= 0 or self.draft_area_ha <= 0:
            return 0.0
        return round(abs(self.draft_area_ha - declared) / declared * 100.0, 1)

    @rx.var
    def draft_gap_tone(self) -> str:
        if self.draft_area_ha <= 0:
            return "muted"
        return "bad" if self.draft_gap_pct > 5.0 else "good"

    @rx.var
    def has_geojson_draft(self) -> bool:
        return self.geojson_draft.strip() != ""

    @rx.var
    def draft_state_label(self) -> str:
        if self.draw_mode:
            return "Dessin en cours"
        if self.draft_vertex_count > 0:
            return "Contour en attente de finalisation"
        if self.has_geojson_draft:
            return "Brouillon GeoJSON prêt à enregistrer"
        return "Aucun brouillon"

    @rx.var
    def draft_state_tone(self) -> str:
        if self.draw_mode:
            return "info"
        if self.draft_vertex_count > 0:
            return "warn"
        if self.has_geojson_draft:
            return "good"
        return "muted"

    @rx.var
    def draw_hint(self) -> str:
        if not self.has_selection:
            return (
                "Sélectionnez d'abord un îlot dans la liste ou sur la carte "
                "pour lui dessiner un contour."
            )
        if not self.draw_mode:
            return (
                "Activez le mode dessin, puis cliquez la carte sommet par "
                "sommet pour tracer le contour de l'îlot sélectionné."
            )
        if self.draft_vertex_count == 0:
            return (
                "Cliquez un premier coin de la parcelle : le clic ne "
                "sélectionne plus d'îlot tant que le mode dessin est actif."
            )
        if self.draft_vertex_count < 3:
            return (
                f"{self.draft_vertex_count} sommet(s) posé(s) : il en faut au "
                "moins trois pour fermer un contour agricole."
            )
        return (
            f"{self.draft_vertex_count} sommets · {self.draft_area_ha:.2f} ha "
            "calculés. Terminez le contour pour alimenter le brouillon "
            "GeoJSON, puis enregistrez-le depuis la fiche parcellaire."
        )

    @rx.var
    def staged_count(self) -> int:
        return len(
            [s for s in self.shapes if s["stage_label"] != "Sans observation"]
        )

    @rx.var
    def intervention_count(self) -> int:
        return len(self.interventions)

    @rx.var
    def has_geometry_logs(self) -> bool:
        return len(self.geometry_logs) > 0

    @rx.var
    def geometry_log_count(self) -> int:
        return len(self.geometry_logs)

    @rx.var
    def has_geometry_error(self) -> bool:
        return self.geometry_error.strip() != ""

    @rx.var
    def has_geometry_notice(self) -> bool:
        return self.geometry_notice.strip() != ""

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def _filters(self) -> tuple[str, dict[str, str]]:
        clauses = ["1=1"]
        params: dict[str, str] = {}
        query = self.search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(p.name) LIKE :q OR LOWER(p.code) LIKE :q"
                " OR LOWER(p.locality) LIKE :q"
                " OR EXISTS (SELECT 1 FROM crop cs WHERE cs.parcel_id = p.id"
                " AND LOWER(cs.name) LIKE :q))"
            )
            params["q"] = f"%{query}%"
        if self.status_filter != "TOUS":
            clauses.append("p.status = :status")
            params["status"] = self.status_filter
        return " AND ".join(clauses), params

    async def _fetch_shapes(self) -> None:
        where, params = self._filters()
        geometry_select = (
            """
            COALESCE(p.boundary_geojson, ''), COALESCE(p.center_lat, 0),
            COALESCE(p.center_lon, 0), COALESCE(p.map_zoom, 15),
            COALESCE(p.bbox_min_lat, 0), COALESCE(p.bbox_min_lon, 0),
            COALESCE(p.bbox_max_lat, 0), COALESCE(p.bbox_max_lon, 0),
            COALESCE(p.geometry_vertex_count, 0),
            COALESCE(p.geometry_source, 'AUCUNE')
            """
            if self.geometry_ready
            else """
            '', 0, 0, 15, 0, 0, 0, 0, 0, 'AUCUNE'
            """
        )

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, p.name, COALESCE(p.code, ''),
                               COALESCE(p.area_ha, 0), p.status, p.is_organic,
                               COALESCE(p.locality, ''),
                               COALESCE(p.latitude, 0), COALESCE(p.longitude, 0),
                               c.name, c.health, COALESCE(c.progress_percent, 0),
                               COALESCE(v.color_hex, '#a3e635'),
                               {geometry_select}
                        FROM parcel p
                        LEFT JOIN crop c
                            ON c.parcel_id = p.id AND c.status = 'EN_COURS'
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        WHERE {where}
                        ORDER BY p.code, p.name
                        LIMIT 200
                        """
                    ),
                    params,
                )
            ).all()

        shapes: list[ParcelShape] = []
        for row in rows:
            parcel_id = int(row[0])
            area = float(row[3] or 0)
            latitude = float(row[7] or 0)
            longitude = float(row[8] or 0)
            health = str(row[10]) if row[10] else "BON"
            progress = int(row[11] or 0)
            raw_geojson = str(row[13] or "")
            vertex_count = int(row[21] or 0)
            source = str(row[22] or "AUCUNE")
            ring: list[list[float]] = []
            has_geometry = False
            if raw_geojson:
                # Contour illisible en base : cas métier attendu. On retombe
                # sur un contour généré, en information simple, jamais comme
                # erreur serveur.
                ring, parse_error = safe_ring_from_geojson(raw_geojson)
                if parse_error:
                    logging.info(
                        "Contour GeoJSON ignoré (parcelle %s) : %s",
                        parcel_id,
                        parse_error,
                    )
                    ring = []
                else:
                    has_geometry = True
            if not ring:
                if abs(latitude) < 0.0001 or abs(longitude) < 0.0001:
                    latitude = DEFAULT_LAT + (parcel_id % 7) * 0.0025
                    longitude = DEFAULT_LON + (parcel_id % 5) * 0.0035
                generated = build_parcel_polygon(
                    latitude, longitude, area, seed=parcel_id * 7919
                )
                ring, _generated_error = safe_ring_from_geojson(
                    generated["geojson"]
                )
                vertex_count = int(generated["vertex_count"])
                if not has_geometry:
                    source = "AUCUNE" if self.geometry_ready else "GENEREE"
            lats = [point[1] for point in ring[:-1]]
            lons = [point[0] for point in ring[:-1]]
            center_lat = (
                float(row[14])
                if has_geometry and row[14]
                else sum(lats) / len(lats)
            )
            center_lon = (
                float(row[15])
                if has_geometry and row[15]
                else sum(lons) / len(lons)
            )
            span = max(max(lats) - min(lats), max(lons) - min(lons))
            shapes.append(
                {
                    "id": parcel_id,
                    "name": str(row[1]),
                    "code": str(row[2]) or "—",
                    "area_ha": area,
                    "status": str(row[4]),
                    "status_label": PARCEL_STATUS_LABELS.get(row[4], row[4]),
                    "is_organic": bool(row[5]),
                    "crop_name": str(row[9])
                    if row[9]
                    else "Sans culture active",
                    "health_label": HEALTH_LABELS.get(health, health),
                    "health_tone": HEALTH_TONES.get(health, "good"),
                    "progress": progress,
                    "progress_pct": f"{progress}%",
                    "color": str(row[12]) or "#a3e635",
                    "positions": _positions(ring),
                    "center": {"lat": center_lat, "lng": center_lon},
                    "zoom": _zoom_for_span(span),
                    "has_geometry": has_geometry,
                    "source_label": GEOMETRY_SOURCE_LABELS.get(source, source),
                    "vertex_count": vertex_count,
                    "min_lat": min(lats),
                    "min_lon": min(lons),
                    "max_lat": max(lats),
                    "max_lon": max(lons),
                    "locality": str(row[6]) or "Localité non renseignée",
                    "stage_label": self._parcel_stages.get(
                        parcel_id, "Sans observation"
                    ),
                }
            )

        if (
            not self.search.strip()
            and self.status_filter == "TOUS"
            and self.geometry_filter == "TOUS"
            and self.stage_filter == "TOUS"
            and shapes
        ):
            self.farm_center = {
                "lat": round(
                    sum(shape["center"]["lat"] for shape in shapes)
                    / len(shapes),
                    6,
                ),
                "lng": round(
                    sum(shape["center"]["lng"] for shape in shapes)
                    / len(shapes),
                    6,
                ),
            }

        if self.stage_filter == "SANS_OBSERVATION":
            shapes = [
                s for s in shapes if s["stage_label"] == "Sans observation"
            ]
        elif self.stage_filter != "TOUS":
            shapes = [
                s for s in shapes if s["stage_label"] == self.stage_filter
            ]

        if self.geometry_filter == "AVEC":
            shapes = [s for s in shapes if s["has_geometry"]]
        elif self.geometry_filter == "SANS":
            shapes = [s for s in shapes if not s["has_geometry"]]

        self.shapes = shapes
        ids = [s["id"] for s in shapes]
        if self.selected_parcel_id not in ids:
            self.selected_parcel_id = ids[0] if ids else 0
        for shape in shapes:
            if shape["id"] == self.selected_parcel_id:
                self.center = shape["center"]
                self.zoom = shape["zoom"]

    async def _load_stage_options(self) -> None:
        """Construit la liste stable des options de stades disponibles.

        Les options proviennent des observations et stades phénologiques déjà
        enregistrés, complétées par les stades réellement portés par les îlots
        de l'exploitation. Aucune écriture, aucun changement de schéma.
        """
        options: list[Option] = []
        seen: list[str] = []
        for item in await stage_filter_options():
            value = str(item["value"])
            if value in seen:
                continue
            seen.append(value)
            options.append({"value": value, "label": str(item["label"])})
        for label in self._parcel_stages.values():
            value = str(label)
            if not value or value == "Sans observation" or value in seen:
                continue
            seen.append(value)
            options.append({"value": value, "label": value})
        self.stage_filter_options = options
        if self.stage_filter != "TOUS" and self.stage_filter not in seen:
            self.stage_filter = "TOUS"

    async def _fetch_detail(self) -> None:
        parcel_id = self.selected_parcel_id
        if parcel_id == 0:
            self.parcel_detail = EMPTY_DETAIL
            self.interventions = []
            self.geojson_draft = ""
            return

        geometry_select = (
            """
            COALESCE(p.geometry_area_ha, 0),
            COALESCE(p.geometry_vertex_count, 0),
            COALESCE(p.geometry_source, 'AUCUNE'),
            COALESCE(p.center_lat, 0), COALESCE(p.center_lon, 0),
            COALESCE(p.map_zoom, 15),
            COALESCE(p.bbox_min_lat, 0), COALESCE(p.bbox_min_lon, 0),
            COALESCE(p.bbox_max_lat, 0), COALESCE(p.bbox_max_lon, 0),
            p.geometry_updated_at, COALESCE(p.geometry_updated_by, ''),
            COALESCE(p.geometry_notes, ''), COALESCE(p.boundary_geojson, '')
            """
            if self.geometry_ready
            else """
            0, 0, 'AUCUNE', 0, 0, 15, 0, 0, 0, 0, NULL, '', '', ''
            """
        )

        async with rx.asession() as asession:
            detail = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, p.name, COALESCE(p.code, ''),
                               COALESCE(p.area_ha, 0), p.status, p.soil_type,
                               p.irrigation, COALESCE(p.locality, ''),
                               COALESCE(p.latitude, 0), COALESCE(p.longitude, 0),
                               COALESCE(p.slope_percent, 0), COALESCE(p.ph, 0),
                               COALESCE(p.organic_matter_percent, 0),
                               p.is_organic, COALESCE(p.notes, ''),
                               (SELECT COUNT(*) FROM crop cc
                                  WHERE cc.parcel_id = p.id),
                               (SELECT COUNT(*) FROM crop cc
                                  WHERE cc.parcel_id = p.id
                                    AND cc.status = 'EN_COURS'),
                               {geometry_select}
                        FROM parcel p WHERE p.id = :pid
                        """
                    ),
                    {"pid": parcel_id},
                )
            ).first()

            active = (
                await asession.execute(
                    text(
                        """
                        SELECT c.name, COALESCE(v.species, ''), c.stage,
                               c.health, COALESCE(c.progress_percent, 0)
                        FROM crop c
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        WHERE c.parcel_id = :pid AND c.status = 'EN_COURS'
                        ORDER BY c.id LIMIT 1
                        """
                    ),
                    {"pid": parcel_id},
                )
            ).first()

            history = (
                await asession.execute(
                    text(
                        """
                        SELECT i.id, i.title, i.type, i.status,
                               i.scheduled_date, i.done_date,
                               COALESCE(i.operator, ''),
                               COALESCE(i.equipment, ''),
                               COALESCE(i.target, ''),
                               COALESCE(c.name, ''),
                               COALESCE(i.area_treated_ha, 0),
                               COALESCE(i.cost, 0),
                               (SELECT COUNT(*) FROM intervention_product ip
                                  WHERE ip.intervention_id = i.id),
                               (SELECT pr.name FROM intervention_product ip
                                  JOIN product pr ON pr.id = ip.product_id
                                  WHERE ip.intervention_id = i.id
                                  ORDER BY ip.id LIMIT 1)
                        FROM intervention i
                        LEFT JOIN crop c ON c.id = i.crop_id
                        WHERE i.parcel_id = :pid
                        ORDER BY COALESCE(i.done_date, i.scheduled_date) DESC,
                                 i.id DESC
                        LIMIT 60
                        """
                    ),
                    {"pid": parcel_id},
                )
            ).all()

            totals = (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*), COALESCE(SUM(cost), 0)
                        FROM intervention WHERE parcel_id = :pid
                        """
                    ),
                    {"pid": parcel_id},
                )
            ).first()

        if detail is None:
            self.parcel_detail = EMPTY_DETAIL
            self.interventions = []
            self.geojson_draft = ""
            return

        source = str(detail[19] or "AUCUNE")
        health = str(active[3]) if active else "BON"
        raw_geojson = str(detail[30] or "")
        self.parcel_detail = {
            "id": str(int(detail[0])),
            "name": str(detail[1]),
            "code": str(detail[2]) or "—",
            "area_ha": f"{float(detail[3] or 0):.1f}",
            "status_label": PARCEL_STATUS_LABELS.get(detail[4], detail[4]),
            "soil_label": SOIL_LABELS.get(detail[5], detail[5]),
            "irrigation_label": IRRIGATION_LABELS.get(detail[6], detail[6]),
            "locality": str(detail[7]) or "Localité non renseignée",
            "coordinates": (
                f"{float(detail[8] or 0):.5f} / {float(detail[9] or 0):.5f}"
            ),
            "slope": f"{float(detail[10] or 0):.1f}",
            "ph": f"{float(detail[11] or 0):.1f}",
            "organic_matter": f"{float(detail[12] or 0):.1f}",
            "organic_label": "Conduite bio"
            if bool(detail[13])
            else "Conventionnel",
            "notes": str(detail[14]) or "Aucune note agronomique.",
            "crop_count": str(int(detail[15] or 0)),
            "active_crops": str(int(detail[16] or 0)),
            "crop_name": str(active[0]) if active else "Sans culture active",
            "crop_species": (
                str(active[1])
                if active and active[1]
                else "Espèce non précisée"
            ),
            "crop_stage": str(active[2]) if active else "—",
            "health_label": HEALTH_LABELS.get(health, health),
            "health_tone": HEALTH_TONES.get(health, "muted")
            if active
            else "muted",
            "progress_pct": f"{int(active[4] or 0)}%" if active else "0%",
            "source_label": GEOMETRY_SOURCE_LABELS.get(source, source),
            "vertex_count": str(int(detail[18] or 0)),
            "geometry_area": f"{float(detail[17] or 0):.2f}",
            "geometry_center": (
                f"{float(detail[20] or 0):.5f} / {float(detail[21] or 0):.5f}"
            ),
            "geometry_bbox": (
                f"{float(detail[23] or 0):.4f}, {float(detail[24] or 0):.4f}"
                f" → {float(detail[25] or 0):.4f}, {float(detail[26] or 0):.4f}"
            ),
            "geometry_zoom": f"{float(detail[22] or 15):.1f}",
            "geometry_updated": _fmt_date(as_datetime(detail[27])),
            "geometry_updated_by": str(detail[28]) or "—",
            "geometry_notes": str(detail[29]) or "Aucune note de géométrie.",
            "intervention_count": str(int(totals[0] or 0)) if totals else "0",
            "intervention_cost": f"{float(totals[1] or 0):.0f}"
            if totals
            else "0",
        }

        await self._fetch_geometry_logs()

        if raw_geojson:
            try:
                self.geojson_draft = json.dumps(
                    json.loads(raw_geojson), indent=2, ensure_ascii=False
                )
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                # Reformatage impossible : on affiche le GeoJSON brut sans
                # journaliser d'erreur serveur (donnée utilisateur attendue).
                logging.exception("Unexpected error")
                logging.info("GeoJSON stocké non reformatable : %s", error)
                self.geojson_draft = raw_geojson
        else:
            self.geojson_draft = ""
        self.geometry_error = ""
        self.form_key += 1

        entries: list[InterventionEntry] = []
        for row in history:
            i_type = str(row[2])
            i_status = str(row[3])
            count = int(row[12] or 0)
            first = str(row[13]) if row[13] else ""
            if count == 0:
                product_label = "Aucun intrant"
            elif count == 1:
                product_label = first
            else:
                product_label = f"{first} +{count - 1}"
            entries.append(
                {
                    "id": int(row[0]),
                    "title": str(row[1]),
                    "type": i_type,
                    "type_label": INTERVENTION_LABELS.get(i_type, i_type),
                    "status_label": INTERVENTION_STATUS_LABELS.get(
                        i_status, i_status
                    ),
                    "tone": STATUS_TONES.get(i_status, "planned"),
                    "date_label": _fmt_date(row[4]),
                    "done_label": _fmt_date(row[5]),
                    "operator": str(row[6]) or "Non affecté",
                    "equipment": str(row[7]) or "—",
                    "target": str(row[8]) or "—",
                    "crop_name": str(row[9]) or "Sans culture liée",
                    "area_ha": float(row[10] or 0),
                    "cost": float(row[11] or 0),
                    "product_label": product_label,
                    "is_done": i_status in ("REALISEE", "ANNULEE"),
                }
            )
        self.interventions = entries

    async def _fetch_geometry_logs(self) -> None:
        """Mini-historique des mises à jour de contour de la parcelle."""
        if self.selected_parcel_id == 0:
            self.geometry_logs = []
            return
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, action, COALESCE(note, ''),
                               COALESCE(author, ''), decided_on
                        FROM remediation_log
                        WHERE domain = 'GEOMETRIE' AND target_id = :pid
                        ORDER BY id DESC
                        LIMIT 8
                        """
                    ),
                    {"pid": self.selected_parcel_id},
                )
            ).all()
        labels = {
            "CONTOUR_ENREGISTRE": "Contour enregistré",
            "CONTOUR_PROPOSE": "Contour proposé",
            "CONTOUR_DESSINE": "Contour dessiné",
        }
        tones = {
            "CONTOUR_ENREGISTRE": "good",
            "CONTOUR_PROPOSE": "info",
            "CONTOUR_DESSINE": "warn",
        }
        icons = {
            "CONTOUR_ENREGISTRE": "save",
            "CONTOUR_PROPOSE": "wand-sparkles",
            "CONTOUR_DESSINE": "pen-tool",
        }
        self.geometry_logs = [
            {
                "id": int(row[0]),
                "action_label": labels.get(row[1], row[1]),
                "tone": tones.get(row[1], "muted"),
                "icon": icons.get(row[1], "history"),
                "note": str(row[2]) or "Aucune note de géométrie.",
                "author": str(row[3]) or "—",
                "date_label": _fmt_date(row[4]),
            }
            for row in rows
        ]

    async def _log_geometry(self, action: str, note: str, author: str) -> None:
        """Consigne une trace de géométrie dans le journal local."""
        label = ""
        for shape in self.shapes:
            if shape["id"] == self.selected_parcel_id:
                label = f"{shape['code']} · {shape['name']}"
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO remediation_log (
                        domain, target_kind, target_id, target_label,
                        action, note, author, module_route, decided_on
                    ) VALUES (
                        'GEOMETRIE', 'parcel', :pid, :label,
                        :action, :note, :author, '/cartographie', :decided
                    )
                    """
                ),
                {
                    "pid": self.selected_parcel_id,
                    "label": label[:200],
                    "action": action,
                    "note": note[:600],
                    "author": author[:120],
                    "decided": datetime.date.today(),
                },
            )
            await asession.commit()

    @rx.event
    async def load_map(self):
        self.is_loading = True
        yield
        await ensure_local_database()
        await ensure_remediation_log_table()
        await seed_dashboard_data()
        await seed_parcel_geometry()
        async with rx.asession() as asession:
            self.geometry_ready = await geometry_columns_ready(asession)
        # Stade courant par îlot : la carte devient lisible par stade.
        self._parcel_stages = await parcel_stage_map()
        await self._load_stage_options()
        await self._fetch_shapes()
        await self._fetch_detail()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    # ------------------------------------------------------------------
    # Filtres & sélection
    # ------------------------------------------------------------------

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._fetch_shapes()
        await self._fetch_detail()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._fetch_shapes()
        await self._fetch_detail()

    @rx.event
    async def set_geometry_filter(self, value: str):
        self.geometry_filter = value
        await self._fetch_shapes()
        await self._fetch_detail()

    @rx.event
    async def set_stage_filter(self, value: str):
        self.stage_filter = value
        await self._fetch_shapes()
        await self._fetch_detail()

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.status_filter = "TOUS"
        self.geometry_filter = "TOUS"
        self.stage_filter = "TOUS"
        self.form_key += 1
        await self._fetch_shapes()
        await self._fetch_detail()

    @rx.event
    async def select_parcel(self, parcel_id: int):
        if parcel_id != self.selected_parcel_id:
            self.draft_points = []
            self.draw_mode = False
        self.geometry_notice = ""
        self.selected_parcel_id = parcel_id
        for shape in self.shapes:
            if shape["id"] == parcel_id:
                self.center = shape["center"]
                self.zoom = shape["zoom"]
        await self._fetch_detail()

    @rx.event
    async def handle_map_click(self, event: dict):
        """Sélectionne la parcelle contenant le point cliqué sur la carte."""
        raw = event.get("latlng") if isinstance(event, dict) else None
        if not isinstance(raw, dict):
            return
        lat = float(raw.get("lat", 0.0))
        lng = float(raw.get("lng", 0.0))
        if self.draw_mode:
            # Mode dessin : le clic pose un sommet, il ne sélectionne pas.
            if self.selected_parcel_id == 0:
                return rx.toast(
                    "Sélectionnez une parcelle avant de dessiner son contour."
                )
            self.draft_points = list(self.draft_points) + [
                {"lat": round(lat, 6), "lng": round(lng, 6)}
            ]
            self.geometry_error = ""
            return
        best_id = 0
        best_area = math.inf
        for shape in self.shapes:
            inside = (
                shape["min_lat"] <= lat <= shape["max_lat"]
                and shape["min_lon"] <= lng <= shape["max_lon"]
            )
            if inside and shape["area_ha"] < best_area:
                best_area = shape["area_ha"]
                best_id = shape["id"]
        if best_id == 0:
            return rx.toast(
                "Aucune parcelle à cet endroit de la carte.", duration=3000
            )
        if best_id != self.selected_parcel_id:
            self.draft_points = []
        self.geometry_notice = ""
        self.selected_parcel_id = best_id
        for shape in self.shapes:
            if shape["id"] == best_id:
                self.center = shape["center"]
                self.zoom = shape["zoom"]
        await self._fetch_detail()

    @rx.event
    def handle_zoom(self, event: dict):
        target = event.get("target") if isinstance(event, dict) else None
        if isinstance(target, dict):
            value = target.get("_zoom", target.get("zoom"))
            if value is not None:
                self.zoom = float(value)

    @rx.event
    def set_basemap(self, value: str):
        allowed = {option["value"] for option in self.basemap_options}
        self.basemap = value if value in allowed else "plan"

    @rx.event
    def request_browser_location(self):
        self.location_status = "Recherche de la position navigateur…"
        self.location_error = ""

    @rx.event
    def handle_location_found(self, location: LatLng):
        try:
            latitude = float(location["lat"])
            longitude = float(location["lng"])
        except (KeyError, TypeError, ValueError) as error:
            logging.exception(f"Error: {error}")
            self.location_error = "La position navigateur reçue est illisible."
            self.location_status = "Position navigateur indisponible"
            return
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            self.location_error = "La position navigateur reçue est hors des limites géographiques."
            self.location_status = "Position navigateur indisponible"
            return
        self.browser_location = {
            "lat": round(latitude, 6),
            "lng": round(longitude, 6),
        }
        self.has_browser_location = True
        self.location_error = ""
        self.location_status = "Position navigateur active"

    @rx.event
    def handle_location_error(self, event: dict[str, str | float]):
        try:
            detail = str(event.get("message", "") or "")
        except (AttributeError, TypeError, ValueError) as error:
            logging.exception(f"Error: {error}")
            detail = ""
        self.location_error = (
            f"{detail} — autorisez la géolocalisation pour afficher votre position."
            if detail
            else "Géolocalisation indisponible — autorisez-la dans votre navigateur."
        )
        self.location_status = "Position navigateur indisponible"

    # ------------------------------------------------------------------
    # Édition de géométrie
    # ------------------------------------------------------------------

    @rx.event
    def set_geojson_draft(self, value: str):
        self.geojson_draft = value
        self.geometry_error = ""

    @rx.event
    def generate_draft(self):
        """Propose un contour automatique depuis coordonnées et surface."""
        for shape in self.shapes:
            if shape["id"] == self.selected_parcel_id:
                generated = build_parcel_polygon(
                    shape["center"]["lat"],
                    shape["center"]["lng"],
                    shape["area_ha"],
                    seed=shape["id"] * 7919 + 13,
                )
                self.geojson_draft = json.dumps(
                    json.loads(generated["geojson"]),
                    indent=2,
                    ensure_ascii=False,
                )
                self.geometry_error = ""
                self.form_key += 1
                return rx.toast(
                    "Contour proposé : vérifiez puis enregistrez.",
                    duration=3000,
                )
        return rx.toast("Sélectionnez d'abord une parcelle.")

    @rx.event
    def clear_draft(self):
        self.geojson_draft = ""
        self.geometry_error = ""
        self.draft_points = []
        self.form_key += 1

    # --- Dessin assisté ------------------------------------------------

    @rx.event
    def toggle_draw_mode(self):
        """Active ou quitte le mode dessin de contour."""
        if self.selected_parcel_id == 0:
            return rx.toast(
                "Sélectionnez d'abord une parcelle à contourner.", duration=3500
            )
        self.draw_mode = not self.draw_mode
        self.geometry_error = ""
        if self.draw_mode:
            return rx.toast(
                "Mode dessin actif : cliquez la carte sommet par sommet.",
                duration=4000,
            )
        return rx.toast("Mode dessin désactivé.", duration=2500)

    @rx.event
    def undo_vertex(self):
        """Retire le dernier sommet posé."""
        if not self.draft_points:
            return rx.toast("Aucun sommet à annuler.", duration=2500)
        self.draft_points = list(self.draft_points)[:-1]

    @rx.event
    def clear_vertices(self):
        """Vide le contour en cours de dessin."""
        self.draft_points = []
        self.geometry_error = ""

    @rx.event
    def finish_drawing(self):
        """Ferme le contour dessiné et alimente le brouillon GeoJSON."""
        if len(self.draft_points) < 3:
            self.geometry_error = (
                "Un contour exige au moins trois sommets avant fermeture."
            )
            return rx.toast(self.geometry_error, duration=4000)
        ring = [
            [round(p["lng"], 6), round(p["lat"], 6)] for p in self.draft_points
        ]
        ring.append(list(ring[0]))
        area = round(_ring_area_ha(ring, self.draft_points[0]["lat"]), 2)
        if area <= 0:
            self.geometry_error = (
                "Le contour dessiné a une surface nulle : repositionnez les "
                "sommets pour former un polygone."
            )
            return rx.toast(self.geometry_error, duration=4000)
        self.geojson_draft = json.dumps(
            {"type": "Polygon", "coordinates": [ring]},
            indent=2,
            ensure_ascii=False,
        )
        self.draw_mode = False
        self.geometry_error = ""
        self.form_key += 1
        return rx.toast(
            f"Contour fermé : {len(ring) - 1} sommets · {area} ha. "
            "Vérifiez puis enregistrez-le depuis la fiche parcellaire.",
            duration=5000,
        )

    @rx.event
    async def submit_geometry(self, form_data: dict):
        self.geometry_error = ""
        self.geometry_notice = ""
        if self.selected_parcel_id == 0:
            self.geometry_error = "Sélectionnez d'abord une parcelle."
            return
        if not self.geometry_ready:
            self.geometry_error = (
                "Les colonnes de géométrie ne sont pas encore disponibles "
                "en base : le contour ne peut pas être enregistré."
            )
            return
        raw = str(form_data.get("geojson", "")).strip()
        author = str(form_data.get("author", "")).strip()
        notes = str(form_data.get("geometry_notes", "")).strip()
        if not raw:
            self.geometry_error = "Collez un GeoJSON de contour à enregistrer."
            return
        if len(author) < 2:
            self.geometry_error = "Indiquez l'auteur du tracé."
            return
        # Validation strictement silencieuse : la journalisation Python est
        # désactivée au niveau critique le temps du parsing utilisateur, puis
        # restaurée immédiatement avant toute autre logique. Une saisie invalide
        # est un cas métier, jamais un incident serveur.
        _previous_disable_level = logging.root.manager.disable
        logging.disable(logging.CRITICAL)
        try:
            ring, parse_error = _parse_user_geojson_no_log(raw)
        finally:
            logging.disable(_previous_disable_level)
        if parse_error:
            self.geometry_error = parse_error
            return rx.toast(self.geometry_error, duration=5000)

        shape = _shape_from_ring(ring)
        computed = float(shape["area_ha"])
        if computed <= 0:
            self.geometry_error = (
                "Le contour a une surface nulle : les sommets sont alignés ou "
                "confondus, le polygone ne délimite aucune parcelle."
            )
            return
        if computed < 0.01:
            self.geometry_error = (
                f"Surface calculée improbable ({computed:.3f} ha) : un îlot "
                "cultivé mesure au moins 100 m²."
            )
            return
        if computed > 5000:
            self.geometry_error = (
                f"Le contour couvre {computed:.0f} ha : géométrie improbable "
                "(maximum admis 5000 ha)."
            )
            return

        span = max(
            float(shape["bbox_max_lat"]) - float(shape["bbox_min_lat"]),
            float(shape["bbox_max_lon"]) - float(shape["bbox_min_lon"]),
        )
        if span > 1.0:
            self.geometry_error = (
                "L'emprise du contour dépasse un degré géographique : "
                "vérifiez l'ordre [longitude, latitude] des coordonnées."
            )
            return
        declared = self.declared_area
        gap_pct = (
            round(abs(computed - declared) / declared * 100.0, 1)
            if declared > 0
            else 0.0
        )
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE parcel SET
                        boundary_geojson = :geojson,
                        center_lat = :center_lat,
                        center_lon = :center_lon,
                        map_zoom = :zoom,
                        bbox_min_lat = :bbox_min_lat,
                        bbox_min_lon = :bbox_min_lon,
                        bbox_max_lat = :bbox_max_lat,
                        bbox_max_lon = :bbox_max_lon,
                        geometry_area_ha = :area_ha,
                        geometry_vertex_count = :vertex_count,
                        geometry_source = 'DESSINEE',
                        geometry_srid = 4326,
                        geometry_updated_at = :updated_at,
                        geometry_updated_by = :author,
                        geometry_notes = :notes,
                        latitude = CASE WHEN COALESCE(latitude, 0) = 0
                            THEN :center_lat ELSE latitude END,
                        longitude = CASE WHEN COALESCE(longitude, 0) = 0
                            THEN :center_lon ELSE longitude END
                    WHERE id = :pid
                    """
                ),
                {
                    "geojson": shape["geojson"],
                    "center_lat": shape["center_lat"],
                    "center_lon": shape["center_lon"],
                    "zoom": _zoom_for_span(span),
                    "bbox_min_lat": shape["bbox_min_lat"],
                    "bbox_min_lon": shape["bbox_min_lon"],
                    "bbox_max_lat": shape["bbox_max_lat"],
                    "bbox_max_lon": shape["bbox_max_lon"],
                    "area_ha": shape["area_ha"],
                    "vertex_count": shape["vertex_count"],
                    "updated_at": datetime.datetime.now(datetime.timezone.utc),
                    "author": author,
                    "notes": notes,
                    "pid": self.selected_parcel_id,
                },
            )
            await asession.commit()

        trace = (
            f"Contour enregistré : {shape['vertex_count']} sommets · "
            f"{computed:.2f} ha calculés face à {declared:.2f} ha déclarés "
            f"(écart {gap_pct:.1f} %)."
        )
        if notes:
            trace = f"{trace} {notes}"
        await self._log_geometry("CONTOUR_ENREGISTRE", trace, author)

        await self._fetch_shapes()
        await self._fetch_detail()
        self.geometry_notice = trace
        message = (
            f"Contour enregistré ({shape['vertex_count']} sommets · "
            f"{computed:.2f} ha, écart {gap_pct:.1f} % avec la surface "
            "déclarée)."
        )
        if gap_pct > 5.0:
            message = (
                f"{message} Écart supérieur à 5 % : arbitrez la surface "
                "déclarée ou programmez un relevé de terrain."
            )
        return rx.toast(message, duration=5000)


# ----------------------------------------------------------------------
# Redéfinition finale : validation silencieuse des contours GeoJSON.
# Les rejets sont des cas de saisie métier (JSON mal collé, géométrie non
# surfacique…) et ne doivent produire aucune trace de journalisation, seulement
# un message en français exploitable par l'interface cartographique. Cette
# définition, placée après les classes et événements, est celle vers laquelle
# pointe le nom global utilisé par `submit_geometry`, `_fetch_shapes` et
# `_fetch_detail` à l'exécution.
# ----------------------------------------------------------------------


def safe_ring_from_geojson(raw: str) -> tuple[list[list[float]], str]:
    """Valide un GeoJSON utilisateur et retourne `(ring, message_erreur)`."""
    payload = (raw or "").strip()
    if not payload:
        return [], "Collez un GeoJSON de contour à enregistrer."
    try:
        ring = _ring_from_geojson(payload)
    except json.JSONDecodeError as error:
        logging.exception("Unexpected error")
        return [], (
            f"JSON invalide : vérifiez la syntaxe collée ({error.msg} "
            f"ligne {error.lineno}, colonne {error.colno})."
        )
    except (ValueError, KeyError, TypeError, IndexError) as error:
        logging.exception("Unexpected error")
        return [], f"GeoJSON refusé : {error}"
    return ring, ""


def _parse_user_geojson_no_log(raw: str) -> tuple[list[list[float]], str]:
    """Parse un GeoJSON saisi par l'utilisateur, sans journalisation.

    Contrat identique à la validation métier historique (mêmes messages en
    français), mais strictement silencieux : un contour mal collé est une
    erreur de saisie, jamais un incident serveur. Aucun appel à `logging.*`,
    aucun appel à `safe_ring_from_geojson`.
    """
    payload = (raw or "").strip()
    if not payload:
        return [], "Collez un GeoJSON de contour à enregistrer."
    try:
        ring = _ring_from_geojson(payload)
    except json.JSONDecodeError as error:
        logging.exception("Unexpected error")
        return [], (
            f"JSON invalide : vérifiez la syntaxe collée ({error.msg} "
            f"ligne {error.lineno}, colonne {error.colno})."
        )
    except (ValueError, KeyError, TypeError, IndexError) as error:
        logging.exception("Unexpected error")
        return [], f"GeoJSON refusé : {error}"
    return ring, ""
