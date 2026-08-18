"""Utilitaires de géométrie cartographique des parcelles.

Génère et amorce des contours GeoJSON exploitables à partir des données
parcellaires existantes (latitude, longitude, surface, position relative sur
la carte stylisée). Aucun rendu ni requête d'interface ici : uniquement le
schéma de données et son amorçage idempotent.
"""

from __future__ import annotations

import datetime
import json
import math
import random

import reflex as rx
from sqlalchemy import text

# Rayon terrestre moyen utilisé pour convertir mètres <-> degrés.
EARTH_RADIUS_M: float = 6_371_008.8
DEFAULT_LAT: float = 48.2345
DEFAULT_LON: float = 1.8452


def _meters_per_degree(latitude: float) -> tuple[float, float]:
    """Mètres par degré de latitude et de longitude à une latitude donnée."""
    lat_m = math.pi * EARTH_RADIUS_M / 180.0
    lon_m = lat_m * max(math.cos(math.radians(latitude)), 0.05)
    return lat_m, lon_m


def _ring_area_ha(ring: list[list[float]], latitude: float) -> float:
    """Surface approximative (ha) d'un anneau via projection équirectangulaire."""
    lat_m, lon_m = _meters_per_degree(latitude)
    total = 0.0
    count = len(ring)
    for index in range(count - 1):
        x1 = ring[index][0] * lon_m
        y1 = ring[index][1] * lat_m
        x2 = ring[index + 1][0] * lon_m
        y2 = ring[index + 1][1] * lat_m
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0 / 10_000.0


def _zoom_for_area(area_ha: float) -> float:
    """Niveau de zoom raisonnable pour afficher une parcelle entière."""
    if area_ha <= 0:
        return 16.0
    if area_ha < 3:
        return 17.0
    if area_ha < 10:
        return 16.0
    if area_ha < 25:
        return 15.5
    if area_ha < 60:
        return 15.0
    return 14.0


def build_parcel_polygon(
    latitude: float,
    longitude: float,
    area_ha: float,
    seed: int = 0,
    vertices: int = 10,
) -> dict[str, float | str | int | list]:
    """Construit un contour GeoJSON plausible autour d'un point.

    La forme est un polygone légèrement irrégulier (parcelle agricole) dont la
    surface approche `area_ha`. Le résultat est déterministe pour un `seed`
    donné, ce qui rend l'amorçage reproductible.
    """
    lat = latitude if abs(latitude) > 0.0001 else DEFAULT_LAT
    lon = longitude if abs(longitude) > 0.0001 else DEFAULT_LON
    area = area_ha if area_ha > 0 else 1.0
    side_m = math.sqrt(area * 10_000.0)
    lat_m, lon_m = _meters_per_degree(lat)

    rnd = random.Random(seed or 1)
    count = max(4, vertices)
    # Rayon équivalent d'un polygone régulier de même surface que le carré.
    radius_m = side_m / 2.0 * 1.12
    ring: list[list[float]] = []
    for index in range(count):
        angle = 2.0 * math.pi * index / count
        jitter = 1.0 + rnd.uniform(-0.16, 0.16)
        # Léger allongement est-ouest, typique d'un îlot cultivé.
        dx = math.cos(angle) * radius_m * jitter * 1.18
        dy = math.sin(angle) * radius_m * jitter * 0.86
        ring.append([round(lon + dx / lon_m, 6), round(lat + dy / lat_m, 6)])
    ring.append(list(ring[0]))

    computed = _ring_area_ha(ring, lat)
    if computed > 0:
        # Mise à l'échelle pour coller à la surface déclarée.
        factor = math.sqrt(area / computed)
        ring = [
            [
                round(lon + (point[0] - lon) * factor, 6),
                round(lat + (point[1] - lat) * factor, 6),
            ]
            for point in ring
        ]
        ring[-1] = list(ring[0])
        computed = _ring_area_ha(ring, lat)

    lons = [point[0] for point in ring]
    lats = [point[1] for point in ring]
    return {
        "geojson": json.dumps(
            {"type": "Polygon", "coordinates": [ring]}, separators=(",", ":")
        ),
        "center_lat": round(sum(lats[:-1]) / (len(lats) - 1), 6),
        "center_lon": round(sum(lons[:-1]) / (len(lons) - 1), 6),
        "bbox_min_lat": round(min(lats), 6),
        "bbox_min_lon": round(min(lons), 6),
        "bbox_max_lat": round(max(lats), 6),
        "bbox_max_lon": round(max(lons), 6),
        "area_ha": round(computed, 2),
        "vertex_count": len(ring) - 1,
        "zoom": _zoom_for_area(area),
    }


# Colonnes de géométrie attendues sur la table `parcel`.
GEOMETRY_COLUMNS: tuple[str, ...] = (
    "boundary_geojson",
    "center_lat",
    "center_lon",
    "map_zoom",
    "bbox_min_lat",
    "bbox_min_lon",
    "bbox_max_lat",
    "bbox_max_lon",
    "geometry_area_ha",
    "geometry_vertex_count",
    "geometry_source",
    "geometry_srid",
    "geometry_updated_at",
    "geometry_updated_by",
    "geometry_notes",
)


async def geometry_columns_ready(asession) -> bool:
    """Indique si toutes les colonnes de géométrie existent en base.

    L'introspection s'adapte au dialecte : `PRAGMA table_info` sur SQLite,
    `information_schema.columns` ailleurs, afin de ne jamais envoyer de PRAGMA
    à un moteur non SQLite (PostgreSQL notamment).
    """
    connection = await asession.connection()
    dialect = getattr(connection.dialect, "name", "")
    if dialect == "sqlite":
        rows = (
            await asession.execute(text("PRAGMA table_info('parcel')"))
        ).all()
        present = {str(row[1]) for row in rows}
    else:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'parcel'
                    """
                )
            )
        ).all()
        present = {str(row[0]) for row in rows}
    return all(column in present for column in GEOMETRY_COLUMNS)


async def seed_parcel_geometry() -> None:
    """Amorce les contours manquants des parcelles existantes.

    Idempotent : ne touche que les parcelles dont `boundary_geojson` est vide
    ou nul, et ne remplace jamais un contour dessiné ou importé. Si les
    colonnes de géométrie n'existent pas encore, la fonction ne fait rien.
    """
    async with rx.asession() as asession:
        if not await geometry_columns_ready(asession):
            return
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT id, COALESCE(latitude, 0), COALESCE(longitude, 0),
                           COALESCE(area_ha, 0), COALESCE(map_x, 0),
                           COALESCE(map_y, 0), COALESCE(code, '')
                    FROM parcel
                    WHERE COALESCE(boundary_geojson, '') = ''
                       OR COALESCE(geometry_vertex_count, 0) = 0
                    ORDER BY id
                    """
                )
            )
        ).all()
        if not rows:
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        payload: list[dict[str, str | float | int | None]] = []
        for row in rows:
            parcel_id = int(row[0])
            latitude = float(row[1])
            longitude = float(row[2])
            area = float(row[3])
            # Si les coordonnées sont absentes, on dérive un point plausible
            # depuis la position relative de la carte stylisée existante.
            if abs(latitude) < 0.0001 or abs(longitude) < 0.0001:
                latitude = DEFAULT_LAT + (50.0 - float(row[5])) * 0.0006
                longitude = DEFAULT_LON + (float(row[4]) - 50.0) * 0.0009
            shape = build_parcel_polygon(
                latitude, longitude, area, seed=parcel_id * 7919
            )
            payload.append(
                {
                    "pid": parcel_id,
                    "geojson": shape["geojson"],
                    "center_lat": shape["center_lat"],
                    "center_lon": shape["center_lon"],
                    "bbox_min_lat": shape["bbox_min_lat"],
                    "bbox_min_lon": shape["bbox_min_lon"],
                    "bbox_max_lat": shape["bbox_max_lat"],
                    "bbox_max_lon": shape["bbox_max_lon"],
                    "geometry_area_ha": shape["area_ha"],
                    "vertex_count": shape["vertex_count"],
                    "zoom": shape["zoom"],
                    "latitude": round(latitude, 6),
                    "longitude": round(longitude, 6),
                    "updated_at": now,
                    "notes": (
                        f"Contour initial généré pour l'îlot {row[6]} "
                        "à partir des coordonnées et de la surface déclarée."
                    ),
                }
            )

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
                    geometry_area_ha = :geometry_area_ha,
                    geometry_vertex_count = :vertex_count,
                    geometry_source = CASE
                        WHEN COALESCE(geometry_source, 'AUCUNE')
                             IN ('DESSINEE', 'IMPORTEE', 'CADASTRE')
                        THEN geometry_source ELSE 'GENEREE' END,
                    geometry_srid = 4326,
                    geometry_color_hex = COALESCE(
                        NULLIF(geometry_color_hex, ''), '#a3e635'
                    ),
                    geometry_updated_at = :updated_at,
                    geometry_updated_by = 'Amorçage automatique',
                    geometry_notes = :notes,
                    latitude = CASE WHEN COALESCE(latitude, 0) = 0
                        THEN :latitude ELSE latitude END,
                    longitude = CASE WHEN COALESCE(longitude, 0) = 0
                        THEN :longitude ELSE longitude END
                WHERE id = :pid
                """
            ),
            payload,
        )
        await asession.commit()
