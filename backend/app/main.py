from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.api.datasets import router as datasets_router
from app.cache.service import FileCache
from app.core.config import get_settings
from app.jobs.repository import JobRepository, recover_interrupted_jobs
from app.jobs.service import GenerationService
from app.providers.registry import build_provider_registry
from app.providers.terrain import TerrariumTerrainProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    repository = JobRepository(settings.jobs_database)
    recover_interrupted_jobs(repository)
    providers = build_provider_registry(settings)
    terrain_provider = TerrariumTerrainProvider(settings, FileCache(settings.dem_cache_dir))
    app.state.settings = settings
    app.state.providers = providers
    app.state.generation_service = GenerationService(
        settings, repository, providers, terrain_provider
    )
    provider_cache = FileCache(settings.cache_dir / "providers")
    app.state.provider_cache_stats = provider_cache.stats
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API local para fusionar datos geográficos y generar escenas 3D trazables.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)
app.include_router(datasets_router, prefix=settings.api_prefix)

