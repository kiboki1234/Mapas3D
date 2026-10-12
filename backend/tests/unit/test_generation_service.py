from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings
from app.jobs.repository import JobRepository
from app.jobs.service import GenerationService
from app.models.domain import ProviderResult
from app.models.schemas import (
    BoundingBox,
    GenerationJob,
    GenerationRequest,
    JobStatus,
    ProviderInfo,
)
from app.providers.base import GeospatialProvider


class EmptyProvider(GeospatialProvider):
    id = "osm"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id=self.id,
            name="Fuente vacía",
            available=True,
            enabled_by_default=True,
            data_types=["buildings", "roads"],
            license="ODbL-1.0",
            limitations=[],
        )

    def fetch(self, bbox: BoundingBox, include_roads: bool = True) -> ProviderResult:
        return ProviderResult(
            provider=self.id,
            buildings=[],
            roads=[],
            source={"provider": self.id, "raw_feature_count": 0},
        )


def _service(
    tmp_path: Path, providers: dict[str, GeospatialProvider] | None = None
) -> GenerationService:
    settings = Settings(data_dir=tmp_path)
    repository = JobRepository(tmp_path / "jobs.sqlite3")
    return GenerationService(settings, repository, providers or {})


def _request() -> GenerationRequest:
    return GenerationRequest(
        latitude=-0.314861,
        longitude=-78.443472,
        radius_m=250,
        providers=["osm"],
        include_terrain=False,
    )


def _store_completed_job(
    service: GenerationService, request: GenerationRequest, quality_path: Path
) -> GenerationJob:
    now = datetime.now(timezone.utc)
    job = GenerationJob(
        id="cached-job",
        status=JobStatus.pending,
        progress=0,
        request=request,
        created_at=now,
        updated_at=now,
    )
    service.repository.create(job, service.request_hash(request))
    return service.repository.update(
        job.id,
        status=JobStatus.completed,
        progress=100,
        artifacts={"quality": str(quality_path)},
    )


def test_empty_completed_job_is_not_reused(tmp_path: Path):
    service = _service(tmp_path)
    request = _request()
    quality_path = tmp_path / "empty-quality.json"
    quality_path.write_text(
        json.dumps({"unique_buildings": 0, "roads": 0}), encoding="utf-8"
    )
    _store_completed_job(service, request, quality_path)

    created, cache_hit = service.create(request)

    assert cache_hit is False
    assert created.id != "cached-job"
    assert created.status == JobStatus.pending


def test_completed_job_with_geometry_is_reused(tmp_path: Path):
    service = _service(tmp_path)
    request = _request()
    quality_path = tmp_path / "quality.json"
    quality_path.write_text(
        json.dumps({"unique_buildings": 1, "roads": 0}), encoding="utf-8"
    )
    _store_completed_job(service, request, quality_path)

    cached, cache_hit = service.create(request)

    assert cache_hit is True
    assert cached.id == "cached-job"


def test_generation_fails_when_all_sources_are_empty(tmp_path: Path):
    service = _service(tmp_path, {"osm": EmptyProvider()})
    job, _ = service.create(_request())

    service.process(job.id)

    failed = service.repository.get(job.id)
    assert failed is not None
    assert failed.status == JobStatus.failed
    assert "no devolvieron edificios ni vías" in (failed.error or "")
    assert failed.artifacts == {}


def test_partial_result_after_provider_failure_is_not_reused(tmp_path: Path):
    service = _service(tmp_path)
    request = _request()
    quality_path = tmp_path / "partial-quality.json"
    quality_path.write_text(json.dumps({
        "unique_buildings": 36, "roads": 106,
        "provider_failures": ["overture: network unavailable"],
    }), encoding="utf-8")
    _store_completed_job(service, request, quality_path)
    created, cache_hit = service.create(request)
    assert not cache_hit
    assert created.status == JobStatus.pending


def test_force_regeneration_bypasses_completed_model(tmp_path):
    service = _service(tmp_path)
    request = _request()
    path = tmp_path / "q.json"
    path.write_text(json.dumps({"unique_buildings": 1, "roads": 0}), encoding="utf-8")
    _store_completed_job(service, request, path)
    request.refresh = True
    job, cached = service.create(request)
    assert not cached
    assert job.id != "cached-job"


def test_terrain_fallback_and_optional_landcover_failure(tmp_path, monkeypatch):
    import numpy as np
    from shapely.geometry import box
    from app.models.domain import Building, TerrainGrid

    provider = EmptyProvider()
    monkeypatch.setattr(provider, "fetch", lambda bbox, include_roads: ProviderResult("osm",
        [Building("test", box(-78.4435, -.3149, -78.4434, -.3148), "osm", {"osm": "way/1"})],
        [], {"provider": "osm"}))
    service = _service(tmp_path, {"osm": provider})

    def failure(*args):
        raise RuntimeError("test source offline")

    class Backup:
        def fetch(self, bbox):
            return TerrainGrid(np.linspace(bbox.west, bbox.east, 3), np.linspace(bbox.south, bbox.north, 3),
                np.zeros((3, 3)), 0, {"provider": "mapzen-terrain", "elevation_min_m": 0, "elevation_max_m": 0})

    service.terrain_provider = Backup()
    monkeypatch.setattr(service.copernicus, "fetch", failure)
    monkeypatch.setattr("app.jobs.service.WorldCoverProvider.apply", failure)
    request = _request()
    request.include_terrain = True
    request.include_landcover = True
    job, _ = service.create(request)
    service.process(job.id)
    result = service.repository.get(job.id)
    assert result.status == JobStatus.completed, result.error
    quality = json.loads(Path(result.artifacts["quality"]).read_text(encoding="utf-8"))
    assert len(quality["provider_failures"]) == 2
    assert quality["landcover"] is None
    assert not service._cached_job_has_content(result)
    request.terrain_source = "copernicus"
    job, _ = service.create(request)
    service.process(job.id)
    assert service.repository.get(job.id).status == JobStatus.failed  # Explicit selection is strict.
