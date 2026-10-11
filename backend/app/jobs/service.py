from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.conflation.service import fuse_results
from app.core.config import Settings
from app.core.errors import GenerationCancelledError
from app.data_quality.service import analyze_quality
from app.generation.glb import GENERATOR_VERSION, export_glb, validate_glb
from app.generation.scene import build_scene
from app.jobs.repository import JobRepository
from app.licensing.registry import attribution_text, provider_license, validate_profile
from app.models.domain import ProviderResult, TerrainGrid
from app.models.schemas import GenerationJob, GenerationRequest, JobEvent, JobStatus
from app.projection.service import LocalProjection, bounding_box_from_center
from app.providers.base import GeospatialProvider
from app.providers.terrain import TerrainProvider


class GenerationService:
    def __init__(
        self,
        settings: Settings,
        repository: JobRepository,
        providers: dict[str, GeospatialProvider],
        terrain_provider: TerrainProvider | None = None,
    ):
        self.settings = settings
        self.repository = repository
        self.providers = providers
        self.terrain_provider = terrain_provider

    @staticmethod
    def request_hash(request: GenerationRequest) -> str:
        payload = GENERATOR_VERSION + ":" + request.model_dump_json(exclude_none=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _cached_job_has_content(job: GenerationJob) -> bool:
        """Evita reutilizar escenas vacías creadas durante fallos transitorios de red."""
        if not job.artifacts or not all(Path(path).exists() for path in job.artifacts.values()):
            return False
        quality_path = job.artifacts.get("quality")
        if not quality_path:
            return False
        try:
            quality = json.loads(Path(quality_path).read_text(encoding="utf-8"))
            if not isinstance(quality, dict):
                return False
            # Una fuente fallida debe poder recuperarse en la siguiente generación.
            if quality.get("provider_failures") or any(
                event.level == "warning" and "El proveedor " in event.message
                for event in job.events
            ):
                return False
            return int(quality.get("unique_buildings", 0)) > 0 or int(quality.get("roads", 0)) > 0
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False

    def create(self, request: GenerationRequest) -> tuple[GenerationJob, bool]:
        validate_profile(request.providers, request.license_profile)
        key = self.request_hash(request)
        cached = self.repository.find_completed(key)
        if cached and self._cached_job_has_content(cached):
            return cached, True
        now = datetime.now(timezone.utc)
        job = GenerationJob(
            id=str(uuid4()),
            status=JobStatus.pending,
            progress=0,
            request=request,
            created_at=now,
            updated_at=now,
            events=[JobEvent(message="Trabajo registrado.")],
        )
        self.repository.create(job, key)
        return job, False

    def cancel(self, job_id: str) -> GenerationJob:
        job = self.repository.get(job_id)
        if job is None:
            raise KeyError(job_id)
        if job.status in {JobStatus.completed, JobStatus.failed, JobStatus.cancelled}:
            return job
        return self.repository.update(
            job_id,
            cancel_requested=True,
            event=JobEvent(level="warning", message="Cancelación solicitada; se aplicará en el siguiente punto seguro."),
        )

    def _check_cancelled(self, job_id: str) -> None:
        job = self.repository.get(job_id)
        if job and job.cancel_requested:
            raise GenerationCancelledError("Trabajo cancelado por el usuario.")

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        temporary.replace(path)

    def process(self, job_id: str) -> None:
        job = self.repository.get(job_id)
        if job is None or job.status != JobStatus.pending:
            return
        request = job.request
        output_dir = self.settings.generated_dir / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            bbox = bounding_box_from_center(request.latitude, request.longitude, request.radius_m)
            projection = LocalProjection.at(request.latitude, request.longitude)
            license_warnings = validate_profile(request.providers, request.license_profile)
            self.repository.update(
                job_id,
                status=JobStatus.downloading,
                progress=10,
                event=JobEvent(message="Consultando proveedores geográficos seleccionados."),
            )
            results: list[ProviderResult] = []
            provider_failures: list[str] = []
            for provider_id in request.providers:
                self._check_cancelled(job_id)
                provider = self.providers[provider_id]
                if not provider.info().available:
                    provider_failures.append(f"{provider_id}: {provider.info().detail}")
                    continue
                try:
                    result = provider.fetch(bbox, request.include_roads)
                    if not request.include_buildings:
                        result.buildings = []
                    results.append(result)
                    self.repository.update(
                        job_id,
                        event=JobEvent(
                            message=(
                                f"{provider.info().name}: {len(result.buildings)} edificios y "
                                f"{len(result.roads)} vías obtenidos."
                            )
                        ),
                    )
                except Exception as exc:
                    provider_failures.append(f"{provider_id}: {exc}")
                    self.repository.update(
                        job_id,
                        event=JobEvent(
                            level="warning", message=f"El proveedor {provider_id} falló: {exc}"
                        ),
                    )
            if not results:
                raise RuntimeError("Ningún proveedor produjo datos utilizables. " + " | ".join(provider_failures))
            self._check_cancelled(job_id)
            self.repository.update(
                job_id,
                status=JobStatus.normalizing,
                progress=45,
                event=JobEvent(message="Geometrías validadas y normalizadas en WGS84."),
            )
            self.repository.update(
                job_id,
                status=JobStatus.merging,
                progress=55,
                event=JobEvent(message="Resolviendo duplicados y procedencia por atributo."),
            )
            fused = fuse_results(
                results,
                projection,
                request.floor_height_m,
                request.unknown_height_m,
                request.height_mode,
            )
            fused.warnings.extend(license_warnings)
            fused.warnings.extend(provider_failures)
            if not fused.buildings and not fused.roads:
                failure_detail = (
                    " " + " | ".join(provider_failures) if provider_failures else ""
                )
                raise RuntimeError(
                    "Las fuentes seleccionadas no devolvieron edificios ni vías. "
                    "El resultado vacío no se guardará en caché; intente nuevamente o use "
                    f"OpenStreetMap.{failure_detail}"
                )
            terrain: TerrainGrid | None = None
            if request.include_terrain:
                if self.terrain_provider is None:
                    raise RuntimeError("El relieve fue solicitado, pero no hay proveedor DEM configurado.")
                self.repository.update(
                    job_id,
                    status=JobStatus.processing_terrain,
                    progress=65,
                    event=JobEvent(message="Descargando y muestreando elevaciones DEM reales."),
                )
                terrain = self.terrain_provider.fetch(bbox)
                fused.sources.append(terrain.source)
                fused.warnings.extend(terrain.warnings)
                self.repository.update(
                    job_id,
                    event=JobEvent(
                        message=(
                            "Relieve DEM preparado: "
                            f"{terrain.source['elevation_min_m']}–"
                            f"{terrain.source['elevation_max_m']} m sobre el datum vertical."
                        )
                    ),
                )
            quality = analyze_quality(results, fused, terrain)
            quality["provider_failures"] = provider_failures
            scene = build_scene(fused, projection, terrain)
            self._check_cancelled(job_id)
            self.repository.update(
                job_id,
                status=JobStatus.generating,
                progress=72,
                event=JobEvent(message="Generando mallas 3D y paquete de trazabilidad."),
            )
            generated_at = datetime.now(timezone.utc).isoformat()
            metadata = {
                "schema_version": "1.0",
                "generator_version": GENERATOR_VERSION,
                "appearance": {
                    "style": request.material_style,
                    "observed_geometry": True,
                    "photorealistic": False,
                    "description": (
                        "Los colores codifican procedencia/calidad. No se presentan texturas "
                        "sintéticas como fachadas observadas."
                    ),
                },
                "generation_id": job_id,
                "generated_at": generated_at,
                "request": request.model_dump(),
                "bounding_box": bbox.model_dump(),
                "coordinate_system": projection.metadata(),
                "sources": fused.sources,
                "licenses": [
                    provider_license(item)
                    for item in [
                        *request.providers,
                        *(["mapzen-terrain"] if terrain is not None else []),
                    ]
                ],
                "quality": quality,
                "fusion_decisions": fused.fusion_decisions,
                "object_mapping": {
                    building.id: building.original_ids for building in fused.buildings
                },
                "limitations": [
                    *([] if terrain is not None else [
                        "El relieve no fue solicitado; la base de la escena es plana."
                    ]),
                    "Los edificios sin altura ni pisos observados se muestran solo como huella.",
                    "Las alturas derivadas de pisos usan la conversión indicada por el usuario.",
                    "La implantación usa la cota máxima del DEM bajo la huella; los zócalos son ajustes geométricos, no cimentaciones medidas.",
                    "El DEM representa el terreno, no la superficie de techos ni vegetación.",
                    "La cobertura observada no equivale a completitud respecto al mundo real.",
                ],
            }
            paths = {
                "scene": output_dir / "scene.json",
                "metadata": output_dir / "metadata.json",
                "quality": output_dir / "quality.json",
                "sources": output_dir / "sources.json",
                "model": output_dir / "city3d.glb",
                "attributions": output_dir / "ATTRIBUTIONS.txt",
            }
            self._write_json(paths["scene"], scene)
            self._write_json(paths["metadata"], metadata)
            self._write_json(paths["quality"], quality)
            self._write_json(paths["sources"], fused.sources)
            paths["attributions"].write_text(
                attribution_text(request.providers, terrain is not None), encoding="utf-8"
            )
            export_glb(fused, projection, paths["model"], metadata, terrain)
            self.repository.update(
                job_id,
                status=JobStatus.validating,
                progress=92,
                event=JobEvent(message="Validando estructura del archivo GLB."),
            )
            validation = validate_glb(paths["model"])
            if validation["meshes"] == 0:
                raise ValueError("La generación no produjo mallas exportables.")
            metadata["glb_validation"] = validation
            self._write_json(paths["metadata"], metadata)
            self.repository.update(
                job_id,
                status=JobStatus.completed,
                progress=100,
                artifacts={key: str(path.resolve()) for key, path in paths.items()},
                event=JobEvent(
                    message=(
                        f"Escenario completado: {quality['unique_buildings']} edificios, "
                        f"{quality['roads']} vías y {validation['meshes']} mallas GLB."
                    )
                ),
            )
        except GenerationCancelledError as exc:
            self.repository.update(
                job_id,
                status=JobStatus.cancelled,
                progress=0,
                error=str(exc),
                event=JobEvent(level="warning", message=str(exc)),
            )
        except Exception as exc:
            self.repository.update(
                job_id,
                status=JobStatus.failed,
                error=str(exc),
                event=JobEvent(level="error", message=f"La generación falló: {exc}"),
            )

