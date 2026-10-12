from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from starlette.concurrency import run_in_threadpool

from app.datasets.store import (
    DatasetDescription,
    DatasetStore,
    validate_geojson,
    validate_imagery_raster,
    validate_raster,
)

router = APIRouter(prefix="/datasets/local", tags=["local datasets"])
_upload_lock = Lock()


def imports_allowed(request: Request) -> bool:
    settings = request.app.state.settings
    origin = request.headers.get("origin")
    if origin and origin not in settings.origins:
        return False
    return settings.local_imports_enabled or (
        settings.environment == "development"
        and request.client is not None
        and request.client.host in {"127.0.0.1", "::1"}
        and request.url.hostname in {"127.0.0.1", "localhost", "::1"}
    )


@router.get("")
def list_datasets(request: Request) -> dict:
    enabled = imports_allowed(request)
    return {"enabled": enabled, "datasets": DatasetStore(request.app.state.settings).list() if enabled else []}


@router.post("", status_code=201)
async def import_dataset(request: Request, description: str = Query(max_length=2500)) -> dict:
    if not imports_allowed(request):
        raise HTTPException(403, "Importación local desactivada en este servidor")
    try:
        info = DatasetDescription.model_validate_json(description)
        date.fromisoformat(info.source_date)
        if info.kind in {"dtm", "dsm"} and info.vertical_datum == "unknown":
            raise ValueError("Indique el datum vertical del DEM; no se puede inferir del CRS horizontal")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not _upload_lock.acquire(blocking=False):
        raise HTTPException(409, "Otra importación está en curso; reintente al terminar")
    settings = request.app.state.settings
    store = DatasetStore(settings)
    dataset_id = uuid4().hex
    temporary = store.root / f"{dataset_id}.upload"
    target = store.root / f"{dataset_id}.data"
    manifest = store.root / f"{dataset_id}.json"
    try:
        store.root.mkdir(parents=True, exist_ok=True)
        used = sum(p.stat().st_size for p in store.root.iterdir() if p.is_file())
        limit = min(settings.local_import_max_mb * 1024**2,
                    settings.local_import_quota_mb * 1024**2 - used)
        if info.kind == "buildings":
            limit = min(limit, 10 * 1024**2)
        if limit <= 0:
            raise HTTPException(413, "La cuota local está llena")
        digest = hashlib.sha256()
        count = 0
        with temporary.open("xb") as output:
            async for chunk in request.stream():
                count += len(chunk)
                if count > limit:
                    raise HTTPException(413, "Archivo demasiado grande o cuota local agotada")
                output.write(chunk)
                digest.update(chunk)
        validator = {
            "buildings": validate_geojson,
            "dtm": validate_raster,
            "dsm": validate_raster,
            "imagery": validate_imagery_raster,
        }[info.kind]
        details = await run_in_threadpool(validator, temporary)
        record = {**info.model_dump(), **details, "id": dataset_id, "sha256": digest.hexdigest(),
                  "size_bytes": count, "imported_at": datetime.now(timezone.utc).isoformat(),
                  "provenance_status": "user-declared; not independently verified"}
        temporary.replace(target)
        manifest.write_text(json.dumps(record, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        return record
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, f"No se pudo validar el archivo: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)
        if not manifest.exists():
            target.unlink(missing_ok=True)
        _upload_lock.release()
