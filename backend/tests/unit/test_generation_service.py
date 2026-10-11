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
