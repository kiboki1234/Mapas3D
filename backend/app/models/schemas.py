from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class JobStatus(StrEnum):
    pending = "pending"
    downloading = "downloading"
    normalizing = "normalizing"
    merging = "merging"
    processing_terrain = "processing_terrain"
    generating = "generating"
    validating = "validating"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class BoundingBox(BaseModel):
    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def validate_order(self) -> "BoundingBox":
        if self.west >= self.east or self.south >= self.north:
            raise ValueError("El bounding box debe cumplir west < east y south < north")
        return self

    def as_tuple(self) -> tuple[float, float, float, float]:
        return self.west, self.south, self.east, self.north


class RegionPreviewRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: int = Field(default=250, ge=50, le=1000)


class GenerationRequest(RegionPreviewRequest):
    providers: list[Literal["overture", "osm"]] = Field(
        default_factory=lambda: ["overture", "osm"]
    )
    include_buildings: bool = True
    include_roads: bool = True
    include_terrain: bool = True
    include_landcover: bool = False
    terrain_source: Literal["auto", "copernicus", "terrarium", "local"] = "auto"
    terrain_dataset_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    building_dataset_ids: list[str] = Field(default_factory=list, max_length=5)
    refresh: bool = False
    material_style: Literal["source"] = "source"
    height_mode: Literal["source", "estimated"] = "source"
    lod: Literal["lod0", "lod1"] = "lod0"
    floor_height_m: float = Field(default=3.0, ge=2.0, le=6.0)
    unknown_height_m: float = Field(default=6.0, ge=2.0, le=30.0)
    license_profile: Literal["commercial", "research"] = "commercial"

    @field_validator("providers")
    @classmethod
    def unique_providers(cls, value: list[str]) -> list[str]:
        result = list(dict.fromkeys(value))
        return result

    @model_validator(mode="after")
    def validate_inputs(self) -> "GenerationRequest":
        import re
        if self.include_landcover and not self.include_terrain:
            raise ValueError("Active el relieve para representar WorldCover sobre su superficie")
        if not self.providers and not self.building_dataset_ids:
            raise ValueError("Seleccione una fuente o un archivo local de edificios")
        if any(not re.fullmatch(r"[a-f0-9]{32}", item) for item in self.building_dataset_ids):
            raise ValueError("Identificador de dataset inválido")
        if len(set(self.building_dataset_ids)) != len(self.building_dataset_ids):
            raise ValueError("No repita datasets locales")
        if self.include_terrain and self.terrain_source == "local" and not self.terrain_dataset_id:
            raise ValueError("Seleccione un GeoTIFF local para el relieve")
        return self

    @field_validator("material_style", mode="before")
    @classmethod
    def normalize_legacy_material_style(cls, value: str) -> str:
        # Trabajos 0.2 persistidos usaban estilos ilustrativos ya retirados.
        return "source" if value in {"plain", "procedural", "source"} else value


class JobEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: Literal["info", "warning", "error"] = "info"
    message: str


class GenerationJob(BaseModel):
    id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    request: GenerationRequest
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    cancel_requested: bool = False
    cached_from: str | None = None
    events: list[JobEvent] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)


class ProviderInfo(BaseModel):
    id: str
    name: str
    available: bool
    enabled_by_default: bool
    data_types: list[str]
    license: str
    limitations: list[str]
    detail: str | None = None


class SearchResult(BaseModel):
    display_name: str
    latitude: float
    longitude: float
    bounding_box: list[float]
    category: str | None = None
    source: str = "OpenStreetMap Nominatim"


class SourceDataset(BaseModel):
    provider: str
    dataset: str
    version: str | None = None
    license: str
    source_url: str
    downloaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_feature_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

