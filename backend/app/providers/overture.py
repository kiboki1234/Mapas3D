from __future__ import annotations

from importlib.util import find_spec
import json
from pathlib import Path
import subprocess
import sys
import math
from typing import Any

from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon
from shapely.wkb import loads as load_wkb

from app.cache.service import FileCache
from app.core.errors import ProviderUnavailableError
from app.models.domain import AttributeValue, Building, ProviderResult
from app.models.schemas import BoundingBox, ProviderInfo
from app.providers.base import GeospatialProvider


def overture_available() -> bool:
    return find_spec("overturemaps") is not None


def _source_records(value: Any) -> list[dict[str, Any]]:
    if not value:
        return []
    result = []
    for item in value:
        if isinstance(item, dict):
            result.append(dict(item))
    return result


class OvertureProvider(GeospatialProvider):
    id = "overture"

    def __init__(self, cache: FileCache):
        self.cache = cache

    def info(self) -> ProviderInfo:
        available = overture_available()
        return ProviderInfo(
            id=self.id,
            name="Overture Maps Buildings",
            available=available,
            enabled_by_default=available,
            data_types=["buildings", "building attributes", "GERS"],
            license="ODbL-1.0",
            limitations=[
                "Requiere acceso de red al catálogo STAC y GeoParquet de Overture.",
                "Los contornos derivados de imágenes pueden representar techos y tener menor precisión.",
            ],
            detail=None if available else "Instale el extra backend[overture] para habilitarlo.",
        )

    def _rows(self, bbox: BoundingBox) -> tuple[list[dict[str, Any]], bool]:
        key = self.cache.key("overture-building-v2", bbox.model_dump())
        cached = self.cache.read_json(key)
        if cached is not None:
            rows = cached.get("rows", [])
            for row in rows:
                if isinstance(row.get("geometry"), str):
                    row["geometry"] = bytes.fromhex(row["geometry"])
            return rows, True
        if not overture_available():
            raise ProviderUnavailableError(
                "El cliente oficial overturemaps no está instalado; ejecute el setup con el extra overture."
            )
        try:
            result = subprocess.run(
                [sys.executable, "-m", "app.providers.overture_download", json.dumps(bbox.as_tuple())],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip()[-1500:] or "La descarga Overture falló.")
            payload = json.loads(result.stdout)
            rows = payload["rows"]
            for row in rows:
                row["dataset_release"] = payload.get("release")
            self.cache.write_json(key, {"rows": rows})
            for row in rows:
                if isinstance(row.get("geometry"), str):
                    row["geometry"] = bytes.fromhex(row["geometry"])
            return rows, False
        except subprocess.TimeoutExpired as exc:
            raise ProviderUnavailableError(
                "Overture superó el límite de 120 segundos. Se continuará con las otras fuentes; "
                "puede volver a generar para reintentar."
            ) from exc
        except Exception as exc:  # SDK/network errors vary by Arrow/AWS runtime
            raise ProviderUnavailableError(f"No fue posible consultar Overture: {exc}") from exc

    def fetch(self, bbox: BoundingBox, include_roads: bool = True) -> ProviderResult:
        rows, from_cache = self._rows(bbox)
        buildings: list[Building] = []
        invalid = 0
        versions: set[str] = set()
        releases: set[str] = set()
        for row in rows:
            raw_geometry = row.get("geometry")
            try:
                geometry = load_wkb(raw_geometry) if raw_geometry else None
            except Exception:
                geometry = None
            if geometry is None:
                invalid += 1
                continue
            if not geometry.is_valid:
                geometry = make_valid(geometry)
            if geometry.is_empty or not isinstance(geometry, (Polygon, MultiPolygon)):
                invalid += 1
                continue
            feature_id = str(row.get("id"))
            records = _source_records(row.get("sources"))
            attributes: dict[str, AttributeValue] = {}
            if isinstance(row.get("height"), (float, int)) and math.isfinite(row["height"]) and 0 < row["height"] <= 1000:
                height_records = [item for item in records if str(item.get("property", "")).lstrip("/") == "height"]
                if not height_records:
                    height_records = [item for item in records if not item.get("property")]
                source_names = sorted({str(item.get("dataset")) for item in height_records if item.get("dataset")})
                height_source = "overture:" + ",".join(source_names) if source_names else self.id
                estimated = any(any(token in name.lower() for token in ("microsoft", "google", "ml", "tempo")) for name in source_names)
                attributes["height"] = AttributeValue(
                    float(row["height"]), height_source, estimated=estimated
                )
                attributes["height_type"] = AttributeValue("estimated" if estimated else "explicit", height_source)
                attributes["height_provenance"] = AttributeValue(height_records, self.id)
            if row.get("num_floors") is not None:
                attributes["num_floors"] = AttributeValue(
                    int(row["num_floors"]), self.id
                )
            for key_name in ("subtype", "class", "roof_shape", "roof_height", "facade_material", "facade_color"):
                if row.get(key_name) is not None:
                    attributes[key_name] = AttributeValue(row[key_name], self.id)
            names = row.get("names")
            if isinstance(names, dict):
                primary = names.get("primary")
                if primary:
                    attributes["name"] = AttributeValue(primary, self.id)
            if row.get("version") is not None:
                versions.add(str(row["version"]))
            if row.get("dataset_release"):
                releases.add(str(row["dataset_release"]))
            buildings.append(
                Building(
                    id=f"overture-{feature_id}",
                    geometry=geometry,
                    provider=self.id,
                    original_ids={"gers": feature_id},
                    attributes=attributes,
                    source_records=records,
                    license="ODbL-1.0",
                    confidence=None,
                )
            )
        warnings = []
        if invalid:
            warnings.append(f"Se descartaron {invalid} geometrías Overture inválidas.")
        return ProviderResult(
            provider=self.id,
            buildings=buildings,
            roads=[],
            warnings=warnings,
            source={
                "provider": self.id,
                "dataset": "Overture Buildings",
                "license": "ODbL-1.0",
                "source_url": "https://docs.overturemaps.org/getting-data/overturemaps-py/",
                "release_discovery": "STAC latest",
                "feature_versions": sorted(versions),
                "dataset_releases": sorted(releases),
                "from_cache": from_cache,
                "raw_feature_count": len(rows),
            },
        )

