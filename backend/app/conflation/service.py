from __future__ import annotations

from math import sqrt
from typing import Iterable

from shapely.geometry.base import BaseGeometry

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
    first_ids = set(first.original_ids.values())
    second_ids = set(second.original_ids.values())
    if first_ids & second_ids:
        return True
    record_ids = {
        str(item.get("record_id", "")).split("@")[0]
        for item in first.source_records + second.source_records
        if item.get("record_id")
    }
    osm_ids = {
        value.replace("way/", "w").replace("relation/", "r").replace("node/", "n")
        for value in first_ids | second_ids
    }
    return bool(record_ids & osm_ids)


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
    for key, candidate in incoming.attributes.items():
        current = target.attributes.get(key)
        if current is None:
            target.attributes[key] = candidate
            decisions.append({"attribute": key, "action": "filled", "source": candidate.source})
            continue
        if current.value == candidate.value:
            continue
        current_explicit = not current.estimated
        candidate_explicit = not candidate.estimated
        if candidate_explicit and not current_explicit:
            target.attributes[key] = candidate
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
    buildings: Iterable[Building], floor_height_m: float, unknown_height_m: float
) -> None:
    for building in buildings:
        explicit = building.attributes.get("height")
        if explicit and isinstance(explicit.value, (int, float)) and explicit.value > 0:
            building.attributes.setdefault(
                "height_type", AttributeValue("explicit", explicit.source, explicit.confidence)
            )
            continue
        floors = building.attributes.get("num_floors")
        if floors and isinstance(floors.value, (int, float)) and floors.value > 0:
            building.attributes["height"] = AttributeValue(
                float(floors.value) * floor_height_m,
                floors.source,
                confidence=0.72,
                estimated=True,
            )
            building.attributes["height_type"] = AttributeValue("derived", floors.source)
            continue
        building.attributes["height"] = AttributeValue(
            unknown_height_m, "visual-default", confidence=0.0, estimated=True
        )
        building.attributes["height_type"] = AttributeValue("unknown", "visual-default")


def fuse_results(
    results: list[ProviderResult],
    projection: LocalProjection,
    floor_height_m: float,
    unknown_height_m: float,
) -> FusedDataset:
    priority = {"overture": 0, "osm": 1}
    candidates = sorted(
        [building for result in results for building in result.buildings],
        key=lambda item: priority.get(item.provider, 100),
    )
    fused: list[Building] = []
    metric_geometries: list[BaseGeometry] = []
    decisions: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_metric = projection.project_geometry(candidate.geometry)
        matched_index: int | None = None
        evidence: dict[str, object] = {}
        for index, (existing, existing_metric) in enumerate(zip(fused, metric_geometries)):
            if not existing_metric.envelope.intersects(candidate_metric.envelope):
                continue
            duplicate, current_evidence = _is_duplicate(
                existing, existing_metric, candidate, candidate_metric
            )
            if duplicate:
                matched_index = index
                evidence = current_evidence
                break
        if matched_index is None:
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
    _apply_height_policy(fused, floor_height_m, unknown_height_m)
    roads = [road for result in results for road in result.roads]
    return FusedDataset(
        buildings=fused,
        roads=roads,
        sources=[result.source for result in results],
        fusion_decisions=decisions,
        warnings=[warning for result in results for warning in result.warnings],
    )

