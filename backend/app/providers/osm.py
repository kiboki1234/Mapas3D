from __future__ import annotations

import re
from typing import Any

import httpx
from shapely import make_valid
from shapely.geometry import LineString, MultiPolygon, Polygon

from app.cache.service import FileCache
from app.core.config import Settings
from app.core.errors import ProviderUnavailableError
from app.models.domain import AttributeValue, Building, ProviderResult, Road
from app.models.schemas import BoundingBox, ProviderInfo
from app.providers.base import GeospatialProvider


HEIGHT_NUMBER = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace(",", ".")
    feet_inches = re.fullmatch(r"(\d+(?:\.\d+)?)\s*'\s*(\d+(?:\.\d+)?)?\s*\"?", text)
    if feet_inches:
        return float(feet_inches[1]) * .3048 + float(feet_inches[2] or 0) * .0254
    match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*(m|ft|feet)?", text)
    if not match:
        return None  # Ranges, multiple values and unknown units are ambiguous.
    return float(match[1]) * (.3048 if match[2] in {"ft", "feet"} else 1)


def _polygon_from_points(points: list[dict[str, Any]]) -> Polygon | MultiPolygon | None:
    coordinates = [(point.get("lon"), point.get("lat")) for point in points]
    coordinates = [(x, y) for x, y in coordinates if x is not None and y is not None]
    if len(coordinates) < 3:
        return None
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    polygon = Polygon(coordinates)
    if not polygon.is_valid:
        polygon = make_valid(polygon)
    if polygon.is_empty or not isinstance(polygon, (Polygon, MultiPolygon)):
        return None
    return polygon


def _relation_polygon(element: dict[str, Any]) -> Polygon | MultiPolygon | None:
    outers: list[Polygon] = []
    inners: list[Polygon] = []
    for member in element.get("members", []):
        geometry = member.get("geometry") or []
        polygon = _polygon_from_points(geometry)
        if not polygon:
            continue
        target = inners if member.get("role") == "inner" else outers
        if isinstance(polygon, Polygon):
            target.append(polygon)
        else:
            target.extend(list(polygon.geoms))
    if not outers:
        return None
    repaired: list[Polygon] = []
    for outer in outers:
        holes = [list(inner.exterior.coords) for inner in inners if outer.contains(inner.representative_point())]
        candidate = Polygon(outer.exterior.coords, holes)
        valid = make_valid(candidate) if not candidate.is_valid else candidate
        if isinstance(valid, Polygon):
            repaired.append(valid)
        elif isinstance(valid, MultiPolygon):
            repaired.extend(list(valid.geoms))
    if not repaired:
        return None
    return repaired[0] if len(repaired) == 1 else MultiPolygon(repaired)


ROAD_WIDTHS = {
    "motorway": 12.0,
    "trunk": 10.0,
    "primary": 9.0,
    "secondary": 8.0,
    "tertiary": 7.0,
    "residential": 6.0,
    "service": 4.0,
    "footway": 2.0,
    "path": 1.5,
}


class OpenStreetMapProvider(GeospatialProvider):
    id = "osm"

    def __init__(self, settings: Settings, cache: FileCache):
        self.settings = settings
        self.cache = cache

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id=self.id,
            name="OpenStreetMap / Overpass",
            available=True,
            enabled_by_default=True,
            data_types=["buildings", "roads", "attributes"],
            license="ODbL-1.0",
            limitations=[
                "Overpass público está pensado para áreas pequeñas y puede saturarse.",
                "La disponibilidad y completitud varían por región.",
            ],
        )

    def _query(self, bbox: BoundingBox, include_roads: bool) -> str:
        bounds = f"{bbox.south},{bbox.west},{bbox.north},{bbox.east}"
        roads = f'way["highway"]({bounds});' if include_roads else ""
        return (
            "[out:json][timeout:35];("
            f'way["building"]({bounds});'
            f'relation["building"]({bounds});'
            f"{roads}"
            ");out tags geom;"
        )

    def _download(self, bbox: BoundingBox, include_roads: bool) -> tuple[dict[str, Any], str, bool]:
        cache_key = self.cache.key(
            "osm-multisource-v2", {"bbox": bbox.model_dump(), "roads": include_roads}
        )
        cached = self.cache.read_json(cache_key)
        if cached is not None:
            return cached, "cache", True
        query = self._query(bbox, include_roads)
        failures: list[str] = []
        with httpx.Client(
            timeout=self.settings.http_timeout_seconds,
            headers={"User-Agent": self.settings.user_agent},
        ) as client:
            for endpoint in self.settings.overpass_urls:
                try:
                    response = client.post(endpoint, data={"data": query})
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload.get("elements"), list):
                        raise ValueError("Respuesta Overpass sin elements")
                    self.cache.write_json(cache_key, payload)
                    return payload, endpoint, False
                except (httpx.HTTPError, ValueError) as exc:
                    failures.append(f"{endpoint}: {exc}")
            try:
                response = client.get(
                    self.settings.osm_map_endpoint,
                    params={"bbox": ",".join(str(value) for value in bbox.as_tuple())},
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload.get("elements"), list):
                    raise ValueError("Respuesta OSM Map API sin elements")
                payload = self._hydrate_map_api(payload)
                self.cache.write_json(cache_key, payload)
                return payload, self.settings.osm_map_endpoint, False
            except (httpx.HTTPError, ValueError) as exc:
                failures.append(f"{self.settings.osm_map_endpoint}: {exc}")
        raise ProviderUnavailableError("No fue posible obtener datos OSM. " + " | ".join(failures))

    @staticmethod
    def _hydrate_map_api(payload: dict[str, Any]) -> dict[str, Any]:
        """Convierte la respuesta JSON de OSM Map API al subconjunto geométrico usado internamente."""
        elements = payload.get("elements", [])
        nodes = {
            element["id"]: {"lat": element["lat"], "lon": element["lon"]}
            for element in elements
            if element.get("type") == "node" and "lat" in element and "lon" in element
        }
        ways: dict[int, dict[str, Any]] = {}
        for element in elements:
            if element.get("type") != "way":
                continue
            geometry = [nodes[node_id] for node_id in element.get("nodes", []) if node_id in nodes]
            hydrated = {**element, "geometry": geometry}
            ways[element["id"]] = hydrated
        relevant: list[dict[str, Any]] = []
        for element in ways.values():
            tags = element.get("tags", {})
            if "building" in tags or "highway" in tags:
                relevant.append(element)
        for element in elements:
            tags = element.get("tags", {})
            if element.get("type") != "relation" or "building" not in tags:
                continue
            members = []
            for member in element.get("members", []):
                hydrated_member = dict(member)
                if member.get("type") == "way" and member.get("ref") in ways:
                    hydrated_member["geometry"] = ways[member["ref"]].get("geometry", [])
                members.append(hydrated_member)
            relevant.append({**element, "members": members})
        return {**payload, "elements": relevant}

    def fetch(self, bbox: BoundingBox, include_roads: bool = True) -> ProviderResult:
        payload, endpoint, from_cache = self._download(bbox, include_roads)
        buildings: list[Building] = []
        roads: list[Road] = []
        invalid = 0
        for element in payload.get("elements", []):
            tags = element.get("tags", {})
            feature_id = f"{element.get('type', 'unknown')}/{element.get('id')}"
            if "building" in tags:
                geometry = (
                    _relation_polygon(element)
                    if element.get("type") == "relation"
                    else _polygon_from_points(element.get("geometry", []))
                )
                if geometry is None:
                    invalid += 1
                    continue
                attributes: dict[str, AttributeValue] = {
                    "building_class": AttributeValue(tags.get("building", "yes"), self.id),
                }
                name = tags.get("name")
                if name:
                    attributes["name"] = AttributeValue(name, self.id)
                height = _number(tags.get("height"))
                levels = _number(tags.get("building:levels"))
                if height and 0 < height <= 1000:
                    estimated = "estimat" in str(tags.get("source:height", "")).lower()
                    attributes["height"] = AttributeValue(height, self.id, estimated=estimated)
                    attributes["height_type"] = AttributeValue("estimated" if estimated else "explicit", self.id)
                    if tags.get("source:height"):
                        attributes["height_method"] = AttributeValue(tags["source:height"], self.id)
                if levels and 0 < levels <= 300:
                    attributes["num_floors"] = AttributeValue(levels, self.id)
                buildings.append(
                    Building(
                        id=f"osm-{element.get('type')}-{element.get('id')}",
                        geometry=geometry,
                        provider=self.id,
                        original_ids={"osm": feature_id},
                        attributes=attributes,
                        source_records=[{"dataset": "OpenStreetMap", "record_id": feature_id}],
                        license="ODbL-1.0",
                        confidence=None,
                    )
                )
            elif include_roads and "highway" in tags:
                coordinates = [
                    (point.get("lon"), point.get("lat"))
                    for point in element.get("geometry", [])
                    if point.get("lon") is not None and point.get("lat") is not None
                ]
                if len(coordinates) < 2:
                    invalid += 1
                    continue
                road_class = tags.get("highway", "road")
                observed_width = _number(tags.get("width"))
                width = observed_width or ROAD_WIDTHS.get(road_class, 5.0)
                roads.append(
                    Road(
                        id=f"osm-way-{element.get('id')}",
                        geometry=LineString(coordinates),
                        provider=self.id,
                        road_class=road_class,
                        name=tags.get("name"),
                        width_m=max(1.0, min(width, 30.0)),
                        width_source=self.id if observed_width else "road-class-default",
                        width_estimated=observed_width is None,
                    )
                )
        warnings = []
        if invalid:
            warnings.append(f"Se descartaron {invalid} geometrías OSM inválidas o incompletas.")
        estimated_widths = sum(road.width_estimated for road in roads)
        if estimated_widths:
            warnings.append(
                f"{estimated_widths} vías no tenían width; su ancho se derivó de highway."
            )
        return ProviderResult(
            provider=self.id,
            buildings=buildings,
            roads=roads,
            warnings=warnings,
            source={
                "provider": self.id,
                "dataset": "OpenStreetMap",
                "license": "ODbL-1.0",
                "source_url": endpoint,
                "from_cache": from_cache,
                "raw_feature_count": len(payload.get("elements", [])),
            },
        )

