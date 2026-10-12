from __future__ import annotations

from typing import Any, Iterable

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from app.models.domain import Building, FusedDataset, Road, TerrainGrid
from app.projection.service import LocalProjection


def iter_polygons(geometry: BaseGeometry) -> Iterable[Polygon]:
    if isinstance(geometry, Polygon):
        yield geometry
    elif isinstance(geometry, MultiPolygon):
        yield from geometry.geoms


def _ring_coordinates(ring: Any) -> list[list[float]]:
    return [[round(float(x), 3), round(float(-y), 3)] for x, y in ring.coords]


def building_to_scene(building: Building, projection: LocalProjection) -> dict[str, Any]:
    geometry = projection.project_geometry(building.geometry)
    polygons = []
    for polygon in iter_polygons(geometry):
        polygons.append(
            {
                "outer": _ring_coordinates(polygon.exterior),
                "holes": [_ring_coordinates(ring) for ring in polygon.interiors],
            }
        )
    attributes = {
        key: {
            "value": attribute.value,
            "source": attribute.source,
            "confidence": attribute.confidence,
            "estimated": attribute.estimated,
        }
        for key, attribute in building.attributes.items()
    }
    return {
        "id": building.id,
        "polygons": polygons,
        "height_m": float(building.attributes["height"].value),
        "height_type": str(building.attributes["height_type"].value),
        "geometry_source": building.provider,
        "original_ids": building.original_ids,
        "attributes": attributes,
        "license": building.license,
        "conflicts": building.conflicts,
    }


def road_to_scene(road: Road, projection: LocalProjection) -> dict[str, Any]:
    geometry = projection.project_geometry(road.geometry)
    return {
        "id": road.id,
        "points": [[round(float(x), 3), round(float(-y), 3)] for x, y in geometry.coords],
        "width_m": road.width_m,
        "width_source": road.width_source,
        "width_estimated": road.width_estimated,
        "class": road.road_class,
        "name": road.name,
        "source": road.provider,
    }


def build_scene(
    fused: FusedDataset,
    projection: LocalProjection,
    terrain: TerrainGrid | None = None,
) -> dict[str, Any]:
    terrain_payload: dict[str, Any] = {"mode": "flat", "elevation_m": 0.0}
    if terrain is not None:
        terrain_payload = {
            "mode": "dem",
            "source": terrain.source,
            "reference_elevation_m": terrain.reference_elevation_m,
            "longitudes": terrain.longitudes.round(8).tolist(),
            "latitudes": terrain.latitudes.round(8).tolist(),
            "elevations_m": terrain.elevations_m.round(3).tolist(),
            "landcover": terrain.landcover.tolist() if terrain.landcover is not None else None,
            "landcover_source": terrain.landcover_source,
        }
    return {
        "schema_version": "1.0",
        "coordinate_system": projection.metadata(),
        "buildings": [building_to_scene(item, projection) for item in fused.buildings],
        "roads": [road_to_scene(item, projection) for item in fused.roads],
        "terrain": terrain_payload,
    }

