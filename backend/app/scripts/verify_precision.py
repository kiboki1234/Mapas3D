"""Explicit, network-enabled smoke test; never part of the offline test suite.

Run from backend: python -m app.scripts.verify_precision
The default location reuses the ESPE/Sangolqui coordinates already present in City3D.
"""
from __future__ import annotations

import argparse
import json

from app.cache.service import FileCache
from app.core.config import get_settings
from app.jobs.repository import JobRepository
from app.jobs.service import GenerationService
from app.models.schemas import GenerationRequest, JobStatus
from app.providers.registry import build_provider_registry
from app.providers.terrain import TerrariumTerrainProvider


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, default=-.314861)
    parser.add_argument("--longitude", type=float, default=-78.443472)
    parser.add_argument("--radius", type=int, default=250)
    args = parser.parse_args()
    settings = get_settings()
    repository = JobRepository(settings.jobs_database)
    service = GenerationService(settings, repository, build_provider_registry(settings),
        TerrariumTerrainProvider(settings, FileCache(settings.dem_cache_dir)))
    request = GenerationRequest(latitude=args.latitude, longitude=args.longitude, radius_m=args.radius,
        providers=["overture", "osm"], include_terrain=True, terrain_source="auto", include_landcover=True, refresh=True)
    job, _ = service.create(request)
    print(f"Generation: {job.id}", flush=True)
    service.process(job.id)
    result = repository.get(job.id)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    if result.status != JobStatus.completed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
