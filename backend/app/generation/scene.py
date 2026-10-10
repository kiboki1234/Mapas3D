from __future__ import annotations

from typing import Any, Iterable

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from app.models.domain import Building, FusedDataset, Road
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
        "class": road.road_class,
        "name": road.name,
        "source": road.provider,
    }


def build_scene(fused: FusedDataset, projection: LocalProjection) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "coordinate_system": projection.metadata(),
        "buildings": [building_to_scene(item, projection) for item in fused.buildings],
        "roads": [road_to_scene(item, projection) for item in fused.roads],
        "terrain": {"mode": "flat", "elevation_m": 0.0},
    }

