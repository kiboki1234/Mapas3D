from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
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
    width_source: str = "road-class-default"
    width_estimated: bool = True
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


@dataclass(slots=True)
class TerrainGrid:
    longitudes: np.ndarray
    latitudes: np.ndarray
    elevations_m: np.ndarray
    reference_elevation_m: float
    source: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    landcover: np.ndarray | None = None
    landcover_source: dict[str, Any] | None = None
    imagery_png: bytes | None = None
    imagery_source: dict[str, Any] | None = None

    def sample(self, latitude: float, longitude: float) -> float:
        """Interpolación bilineal sobre la cuadrícula DEM regular."""
        x = float(np.interp(longitude, self.longitudes, np.arange(len(self.longitudes))))
        y = float(np.interp(latitude, self.latitudes, np.arange(len(self.latitudes))))
        x0 = min(max(int(np.floor(x)), 0), len(self.longitudes) - 1)
        y0 = min(max(int(np.floor(y)), 0), len(self.latitudes) - 1)
        x1 = min(x0 + 1, len(self.longitudes) - 1)
        y1 = min(y0 + 1, len(self.latitudes) - 1)
        tx, ty = x - x0, y - y0
        top = self.elevations_m[y0, x0] * (1 - tx) + self.elevations_m[y0, x1] * tx
        bottom = self.elevations_m[y1, x0] * (1 - tx) + self.elevations_m[y1, x1] * tx
        return float(top * (1 - ty) + bottom * ty)

