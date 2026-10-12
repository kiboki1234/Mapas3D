from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from shapely.geometry import shape

from app.core.config import Settings


class DatasetDescription(BaseModel):
    model_config = {"str_strip_whitespace": True}
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["buildings", "dtm", "dsm"]
    license: Literal["CC0-1.0", "CC-BY-4.0", "ODbL-1.0", "CDLA-Permissive-2.0"]
    attribution: str = Field(min_length=1, max_length=500)
    source_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    vertical_datum: str = Field(default="unknown", min_length=1, max_length=80)
    vertical_unit: Literal["m", "ft"] = "m"


def validate_geojson(path: Path) -> dict:
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("El GeoJSON supera 10 MB; recorte la región antes de importar")
    content = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(content, dict) or content.get("type") != "FeatureCollection" or content.get("crs"):
        raise ValueError("Use GeoJSON FeatureCollection RFC 7946 en WGS84, sin miembro crs")
    features = content.get("features")
    if not isinstance(features, list) or not 1 <= len(features) <= 20000:
        raise ValueError("El GeoJSON debe contener entre 1 y 20000 edificios")
    bounds = [180., 90., -180., -90.]
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Registro GeoJSON inválido")
        geometry = shape(feature.get("geometry") or {})
        if geometry.geom_type not in {"Polygon", "MultiPolygon"} or geometry.is_empty or not geometry.is_valid:
            raise ValueError("Se requieren polígonos de edificios válidos y no vacíos")
        if geometry.has_z:
            raise ValueError("Use huellas 2D; indique altura relativa en properties.height_m")
        w, s, e, n = geometry.bounds
        if not all(math.isfinite(v) for v in (w, s, e, n)) or w < -180 or e > 180 or s < -90 or n > 90:
            raise ValueError("Coordenadas fuera de WGS84")
        props = feature.get("properties") or {}
        if not isinstance(props, dict):
            raise ValueError("properties debe ser un objeto")
        for key, maximum in (("height_m", 1000), ("num_floors", 300)):
            value = props.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value <= maximum):
                raise ValueError(f"{key} debe ser un número positivo, máximo {maximum}")
        if "height_estimated" in props and not isinstance(props["height_estimated"], bool):
            raise ValueError("height_estimated debe ser true o false")
        bounds = [min(bounds[0], w), min(bounds[1], s), max(bounds[2], e), max(bounds[3], n)]
    return {"bounds_wgs84": bounds, "feature_count": len(features), "crs": "EPSG:4326"}


def validate_raster(path: Path) -> dict:
    import rasterio
    from rasterio.warp import transform_bounds
    # Driver allowlist: never open VRT/XML or follow embedded external sources.
    with rasterio.open(path, driver="GTiff") as dataset:
        if dataset.driver != "GTiff" or not dataset.crs or dataset.count != 1:
            raise ValueError("El DEM debe ser un GeoTIFF georreferenciado de una banda")
        if dataset.width * dataset.height > 100_000_000:
            raise ValueError("GeoTIFF demasiado grande; recorte la región")
        if dataset.transform.b or dataset.transform.d:
            raise ValueError("Reproyecte el GeoTIFF a una cuadrícula sin rotación")
        if dataset.scales != (1.0,) or dataset.offsets != (0.0,):
            raise ValueError("Convierta primero los valores raster a elevaciones sin escala ni offset")
        bounds = transform_bounds(dataset.crs, "EPSG:4326", *dataset.bounds)
        if not all(math.isfinite(v) for v in bounds):
            raise ValueError("Extensión raster inválida")
        return {"bounds_wgs84": list(bounds), "crs": str(dataset.crs),
                "shape": [dataset.height, dataset.width], "pixel_size_crs": list(dataset.res)}


class DatasetStore:
    def __init__(self, settings: Settings):
        self.root = settings.imports_dir

    def get(self, dataset_id: str) -> dict:
        if not re.fullmatch(r"[a-f0-9]{32}", dataset_id):
            raise ValueError("Identificador de dataset inválido")
        path = self.root / f"{dataset_id}.json"
        if not path.is_file():
            raise ValueError("Dataset local no encontrado; vuelva a importarlo")
        return json.loads(path.read_text(encoding="utf-8"))

    def data_path(self, dataset_id: str) -> Path:
        self.get(dataset_id)
        path = self.root / f"{dataset_id}.data"
        if not path.is_file():
            raise ValueError("Archivo del dataset no encontrado")
        return path

    def list(self) -> list[dict]:
        return [self.get(path.stem) for path in sorted(self.root.glob("*.json"))]
