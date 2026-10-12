from __future__ import annotations

from math import sqrt
from typing import Iterable
from copy import deepcopy
from math import isfinite

from shapely.geometry.base import BaseGeometry
from shapely import STRtree

from app.models.domain import AttributeValue, Building, FusedDataset, ProviderResult
from app.projection.service import LocalProjection


def _iou(first: BaseGeometry, second: BaseGeometry) -> float:
    try:
        intersection = first.intersection(second).area
        union = first.union(second).area
        return intersection / union if union else 0.0
    except Exception:
        return 0.0


def _source_linked(first: Building, second: Building) -> bool:
    if set(first.original_ids.items()) & set(second.original_ids.items()):
        return True
    def osm_references(building: Building) -> set[str]:
        values = [building.original_ids["osm"]] if "osm" in building.original_ids else []
        values.extend(str(item["record_id"]) for item in building.source_records
                      if item.get("record_id") and "openstreetmap" in str(item.get("dataset", "")).lower())
        return {value.split("@")[0].replace("way/", "w").replace("relation/", "r").replace("node/", "n")
                for value in values}
    # Compare the two entities, never a union that can match a source to itself.
    return bool(osm_references(first) & osm_references(second))


def _is_duplicate(
    first: Building,
    first_metric: BaseGeometry,
    second: Building,
    second_metric: BaseGeometry,
) -> tuple[bool, dict[str, float | str]]:
    if _source_linked(first, second):
        return True, {"method": "source_identifier", "iou": _iou(first_metric, second_metric)}
    if not first_metric.bounds or not second_metric.bounds:
        return False, {"method": "invalid_bounds", "iou": 0.0}
    overlap = _iou(first_metric, second_metric)
    if overlap >= 0.75:
        return True, {"method": "iou", "iou": overlap}
    smaller = min(first_metric.area, second_metric.area)
    larger = max(first_metric.area, second_metric.area)
    area_ratio = smaller / larger if larger else 0.0
    centroid_distance = first_metric.centroid.distance(second_metric.centroid)
    scale = sqrt(max(smaller, 1.0))
    duplicate = overlap >= 0.55 and area_ratio >= 0.65 and centroid_distance <= scale * 0.2
    return duplicate, {
        "method": "spatial_evidence",
        "iou": overlap,
        "area_ratio": area_ratio,
        "centroid_distance_m": centroid_distance,
    }


def _merge_attributes(target: Building, incoming: Building) -> list[dict[str, object]]:
    decisions: list[dict[str, object]] = []
    def assign_height_details() -> None:
        for related in ("height_type", "height_provenance", "height_method"):
            target.attributes.pop(related, None)
            if related in incoming.attributes:
                target.attributes[related] = incoming.attributes[related]
    for key, candidate in incoming.attributes.items():
        if key in {"height_type", "height_provenance", "height_method"}:
            continue  # Keep the category coupled to the selected height, not another source.
        current = target.attributes.get(key)
        if current is None:
            target.attributes[key] = candidate
            if key == "height":
                assign_height_details()
            decisions.append({"attribute": key, "action": "filled", "source": candidate.source})
            continue
        if current.value == candidate.value and (current.estimated == candidate.estimated or not current.estimated):
            continue
        current_explicit = not current.estimated
        candidate_explicit = not candidate.estimated
        if candidate_explicit and not current_explicit:
            target.attributes[key] = candidate
            if key == "height":
                assign_height_details()
                target.attributes.setdefault("height_type", AttributeValue("explicit", candidate.source))
            action = "replaced_estimate"
        else:
            action = "kept_existing"
        conflict = {
            "attribute": key,
            "kept": target.attributes[key].value,
            "kept_source": target.attributes[key].source,
            "candidate": candidate.value,
            "candidate_source": candidate.source,
            "action": action,
        }
        target.conflicts.append(conflict)
        decisions.append(conflict)
    target.original_ids.update(incoming.original_ids)
    target.source_records.extend(incoming.source_records)
    return decisions


def _apply_height_policy(
    buildings: Iterable[Building],
    floor_height_m: float,
    unknown_height_m: float,
    height_mode: str,
) -> None:
    for building in buildings:
        explicit = building.attributes.get("height")
        if explicit and isinstance(explicit.value, (int, float)) and isfinite(explicit.value) and explicit.value > 0 and not explicit.estimated:
            building.attributes.setdefault(
                "height_type", AttributeValue("explicit", explicit.source, explicit.confidence)
            )
            continue
        floors = building.attributes.get("num_floors")
        if floors and isinstance(floors.value, (int, float)) and floors.value > 0:
            building.attributes.pop("height_provenance", None)
            building.attributes["height_method"] = AttributeValue(
                {"method": "floor_count_times_configured_height", "floors": floors.value,
                 "floor_height_m": floor_height_m}, floors.source, estimated=True)
            building.attributes["height"] = AttributeValue(
                float(floors.value) * floor_height_m,
                floors.source,
                confidence=None,
                estimated=True,
            )
            building.attributes["height_type"] = AttributeValue("derived", floors.source)
            continue
        if explicit and isinstance(explicit.value, (int, float)) and isfinite(explicit.value) and explicit.value > 0:
            building.attributes["height_type"] = AttributeValue("estimated", explicit.source)
            continue
        if height_mode == "estimated":
            building.attributes["height"] = AttributeValue(
                unknown_height_m, "visual-default", confidence=0.0, estimated=True
            )
            building.attributes["height_type"] = AttributeValue("unknown", "visual-default")
        else:
            # No se inventa volumen: la huella observada se exporta como superficie.
            building.attributes["height"] = AttributeValue(
                0.0, "source-footprint", confidence=None, estimated=False
            )
            building.attributes["height_type"] = AttributeValue(
                "footprint_only", "source-footprint"
            )


def fuse_results(
    results: list[ProviderResult],
    projection: LocalProjection,
    floor_height_m: float,
    unknown_height_m: float,
    height_mode: str = "source",
) -> FusedDataset:
    priority = {"overture": 0, "osm": 1}
    candidates = sorted(
        [deepcopy(building) for result in results for building in result.buildings],
        key=lambda item: -1 if item.provider.startswith("local:") else priority.get(item.provider, 100),
    )
    fused: list[Building] = []
    metric_geometries: list[BaseGeometry] = []
    decisions: list[dict[str, object]] = []
    all_metric = [projection.project_geometry(item.geometry) for item in candidates]
    spatial_index = STRtree(all_metric)
    accepted: dict[int, int] = {}
    for candidate_index, candidate in enumerate(candidates):
        candidate_metric = all_metric[candidate_index]
        matched_index: int | None = None
        evidence: dict[str, object] = {}
        for neighbour in sorted(spatial_index.query(candidate_metric)):
            if int(neighbour) not in accepted:
                continue
            index = accepted[int(neighbour)]
            existing, existing_metric = fused[index], metric_geometries[index]
            duplicate, current_evidence = _is_duplicate(
                existing, existing_metric, candidate, candidate_metric
            )
            if duplicate:
                matched_index = index
                evidence = current_evidence
                break
        if matched_index is None:
            accepted[candidate_index] = len(fused)
            fused.append(candidate)
            metric_geometries.append(candidate_metric)
            continue
        existing = fused[matched_index]
        candidate.duplicate_of = existing.id
        attribute_decisions = _merge_attributes(existing, candidate)
        decisions.append(
            {
                "type": "duplicate_merged",
                "kept_id": existing.id,
                "discarded_id": candidate.id,
                "kept_geometry_source": existing.provider,
                "evidence": evidence,
                "attribute_decisions": attribute_decisions,
            }
        )
    _apply_height_policy(fused, floor_height_m, unknown_height_m, height_mode)
    roads = [road for result in results for road in result.roads]
    return FusedDataset(
        buildings=fused,
        roads=roads,
        sources=[result.source for result in results],
        fusion_decisions=decisions,
        warnings=[warning for result in results for warning in result.warnings],
    )

