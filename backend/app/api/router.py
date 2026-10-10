from __future__ import annotations

import math
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.core.config import Settings
from app.jobs.service import GenerationService
from app.models.schemas import (
    GenerationJob,
    GenerationRequest,
    RegionPreviewRequest,
    SearchResult,
)
from app.projection.service import bounding_box_from_center, utm_epsg_for


router = APIRouter()


def get_service(request: Request) -> GenerationService:
    return request.app.state.generation_service


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


@router.get("/health")
def health(request: Request) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "storage": str(settings.data_dir.resolve()),
    }


@router.get("/capabilities")
def capabilities(request: Request) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    cache_stats = request.app.state.provider_cache_stats()
    return {
        "api_version": "1",
        "generation": ["buildings-lod0", "roads", "glb", "metadata", "provenance"],
        "coordinate_systems": ["WGS84", "local UTM"],
        "maximum_radius_m": settings.max_radius_m,
        "terrain": {"implemented": False, "fallback": "flat"},
        "osm2world": {"implemented": False, "mode": "optional future adapter"},
        "cache": cache_stats,
    }


@router.get("/providers")
def providers(request: Request) -> list[dict[str, Any]]:
    return [provider.info().model_dump() for provider in request.app.state.providers.values()]


@router.post("/regions/preview")
def preview_region(
    payload: RegionPreviewRequest,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> dict[str, Any]:
    if payload.radius_m > settings.max_radius_m:
        raise HTTPException(422, f"El radio máximo configurado es {settings.max_radius_m} m")
    bbox = bounding_box_from_center(payload.latitude, payload.longitude, payload.radius_m)
    area_km2 = math.pi * payload.radius_m**2 / 1_000_000
    return {
        "center": {"latitude": payload.latitude, "longitude": payload.longitude},
        "radius_m": payload.radius_m,
        "bounding_box": bbox.model_dump(),
        "projected_crs": f"EPSG:{utm_epsg_for(payload.latitude, payload.longitude)}",
        "estimated_area_km2": round(area_km2, 4),
        "complexity": "low" if payload.radius_m <= 250 else "medium" if payload.radius_m <= 500 else "high",
        "warning": "La complejidad real depende de la densidad de elementos geográficos.",
    }


@router.post("/datasets/inspect")
def inspect_datasets(payload: GenerationRequest, request: Request) -> dict[str, Any]:
    infos = {provider_id: request.app.state.providers[provider_id].info().model_dump() for provider_id in payload.providers}
    return {
        "selected": infos,
        "usable": [key for key, value in infos.items() if value["available"]],
        "unavailable": [key for key, value in infos.items() if not value["available"]],
        "note": "Esta inspección verifica capacidades locales; la descarga se valida al crear el trabajo.",
    }


@router.get("/search", response_model=list[SearchResult])
def search_location(
    q: Annotated[str, Query(min_length=3, max_length=120)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> list[SearchResult]:
    try:
        with httpx.Client(timeout=12, headers={"User-Agent": settings.user_agent}) as client:
            response = client.get(
                settings.nominatim_endpoint,
                params={"q": q, "format": "jsonv2", "limit": 5, "addressdetails": 0},
            )
            response.raise_for_status()
            rows = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, f"La búsqueda geográfica no está disponible: {exc}") from exc
    return [
        SearchResult(
            display_name=item["display_name"],
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            bounding_box=[float(value) for value in item.get("boundingbox", [])],
            category=item.get("type"),
        )
        for item in rows
    ]


@router.post("/generations", response_model=GenerationJob, status_code=202)
def create_generation(
    payload: GenerationRequest,
    background_tasks: BackgroundTasks,
    service: Annotated[GenerationService, Depends(get_service)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> GenerationJob:
    if payload.radius_m > settings.max_radius_m:
        raise HTTPException(422, f"El radio máximo configurado es {settings.max_radius_m} m")
    try:
        job, cache_hit = service.create(payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not cache_hit:
        background_tasks.add_task(service.process, job.id)
    return job


@router.get("/generations/{job_id}", response_model=GenerationJob)
def generation(job_id: str, service: Annotated[GenerationService, Depends(get_service)]) -> GenerationJob:
    job = service.repository.get(job_id)
    if job is None:
        raise HTTPException(404, "Trabajo no encontrado")
    return job


@router.post("/generations/{job_id}/cancel", response_model=GenerationJob)
def cancel_generation(
    job_id: str, service: Annotated[GenerationService, Depends(get_service)]
) -> GenerationJob:
    try:
        return service.cancel(job_id)
    except KeyError as exc:
        raise HTTPException(404, "Trabajo no encontrado") from exc


def _artifact_response(service: GenerationService, job_id: str, artifact: str, media_type: str) -> FileResponse:
    job = service.repository.get(job_id)
    if job is None:
        raise HTTPException(404, "Trabajo no encontrado")
    if job.status.value != "completed":
        raise HTTPException(409, f"El trabajo todavía está en estado {job.status.value}")
    path = job.artifacts.get(artifact)
    if not path:
        raise HTTPException(404, f"Artefacto {artifact} no disponible")
    filenames = {
        "model": f"city3d-{job_id}.glb",
        "metadata": f"city3d-{job_id}-metadata.json",
        "quality": f"city3d-{job_id}-quality.json",
        "sources": f"city3d-{job_id}-sources.json",
        "scene": f"city3d-{job_id}-scene.json",
        "attributions": f"city3d-{job_id}-ATTRIBUTIONS.txt",
    }
    return FileResponse(path, media_type=media_type, filename=filenames[artifact])


@router.get("/generations/{job_id}/model")
def model(job_id: str, service: Annotated[GenerationService, Depends(get_service)]) -> FileResponse:
    return _artifact_response(service, job_id, "model", "model/gltf-binary")


@router.get("/generations/{job_id}/metadata")
def metadata(job_id: str, service: Annotated[GenerationService, Depends(get_service)]) -> FileResponse:
    return _artifact_response(service, job_id, "metadata", "application/json")


@router.get("/generations/{job_id}/quality")
def quality(job_id: str, service: Annotated[GenerationService, Depends(get_service)]) -> FileResponse:
    return _artifact_response(service, job_id, "quality", "application/json")


@router.get("/generations/{job_id}/sources")
def sources(job_id: str, service: Annotated[GenerationService, Depends(get_service)]) -> FileResponse:
    return _artifact_response(service, job_id, "sources", "application/json")


@router.get("/generations/{job_id}/scene")
def scene(job_id: str, service: Annotated[GenerationService, Depends(get_service)]) -> FileResponse:
    return _artifact_response(service, job_id, "scene", "application/json")


@router.get("/generations/{job_id}/attributions")
def attributions(job_id: str, service: Annotated[GenerationService, Depends(get_service)]) -> FileResponse:
    return _artifact_response(service, job_id, "attributions", "text/plain")

