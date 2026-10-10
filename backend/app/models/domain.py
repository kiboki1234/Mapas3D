from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapely.geometry.base import BaseGeometry


@dataclass(slots=True)
class AttributeValue:
    value: Any
    source: str
    confidence: float | None = None
    estimated: bool = False


@dataclass(slots=True)
class Building:
    id: str
    geometry: BaseGeometry
    provider: str
    original_ids: dict[str, str]
    attributes: dict[str, AttributeValue] = field(default_factory=dict)
    source_records: list[dict[str, Any]] = field(default_factory=list)
    license: str = "unknown"
    confidence: float | None = None
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    validation_status: str = "valid"
    duplicate_of: str | None = None


@dataclass(slots=True)
class Road:
    id: str
    geometry: BaseGeometry
    provider: str
    road_class: str
    name: str | None = None
    width_m: float = 5.0
    license: str = "ODbL-1.0"


@dataclass(slots=True)
class ProviderResult:
    provider: str
    buildings: list[Building]
    roads: list[Road]
    source: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FusedDataset:
    buildings: list[Building]
    roads: list[Road]
    sources: list[dict[str, Any]]
    fusion_decisions: list[dict[str, Any]]
    warnings: list[str]

