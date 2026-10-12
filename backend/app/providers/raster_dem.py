from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import Window, from_bounds as window_from_bounds

from app.cache.service import FileCache
from app.core.errors import ProviderUnavailableError
from app.datasets.store import DatasetStore
from app.models.domain import TerrainGrid
from app.models.schemas import BoundingBox


def read_dem_grid(paths: list[str | Path], bbox: BoundingBox, source: dict,
                  unit_factor: float = 1.0, sample_count: int = 65,
                  resampling: Resampling = Resampling.bilinear) -> TerrainGrid:
    """Read only intersecting windows and reproject pixel centres to scene grid nodes."""
    dx = (bbox.east - bbox.west) / (sample_count - 1)
    dy = (bbox.north - bbox.south) / (sample_count - 1)
    transform = from_bounds(bbox.west - dx / 2, bbox.south - dy / 2,
                            bbox.east + dx / 2, bbox.north + dy / 2,
                            sample_count, sample_count)
    merged = np.full((sample_count, sample_count), np.nan, dtype="float32")
    resolutions = []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="20",
                      GDAL_HTTP_CONNECTTIMEOUT="10", GDAL_HTTP_MAX_RETRY="1",
                      GDAL_PAM_ENABLED="NO", VSI_CACHE=False):
        for path in paths:
            with rasterio.open(path, driver="GTiff") as dataset:
                if not dataset.crs or dataset.count != 1:
                    raise ValueError("DEM sin CRS o con múltiples bandas")
                bounds = transform_bounds("EPSG:4326", dataset.crs,
                    bbox.west - dx, bbox.south - dy, bbox.east + dx, bbox.north + dy)
                raw = window_from_bounds(*bounds, transform=dataset.transform)
                left, top = max(0, math.floor(raw.col_off) - 2), max(0, math.floor(raw.row_off) - 2)
                right = min(dataset.width, math.ceil(raw.col_off + raw.width) + 2)
                bottom = min(dataset.height, math.ceil(raw.row_off + raw.height) + 2)
                if right <= left or bottom <= top:
                    continue
                if (right - left) * (bottom - top) > 4_000_000:
                    raise ValueError("Recorte DEM superior a 4 millones de píxeles; reduzca el radio")
                window = Window(left, top, right - left, bottom - top)
                data = dataset.read(1, window=window, masked=True).astype("float32").filled(np.nan)
                target = np.full_like(merged, np.nan)
                reproject(data, target, src_transform=dataset.window_transform(window),
                    src_crs=dataset.crs, src_nodata=np.nan, dst_transform=transform,
                    dst_crs="EPSG:4326", dst_nodata=np.nan, resampling=resampling)
                valid = np.isfinite(target)
                merged[valid] = target[valid] * unit_factor
                if dataset.crs.is_geographic:
                    resolutions.append(max(abs(dataset.res[1]) * 111_320,
                        abs(dataset.res[0]) * 111_320 * math.cos(math.radians((bbox.south + bbox.north) / 2))))
                else:
                    resolutions.append(max(dataset.res) * dataset.crs.linear_units_factor[1])
    if not np.isfinite(merged).all():
        missing = round(100 * (1 - np.isfinite(merged).mean()), 1)
        raise ProviderUnavailableError(f"DEM incompleto: {missing}% de muestras sin datos; no se rellenará con ceros")
    if merged.min() < -12000 or merged.max() > 10000:
        raise ValueError("Elevaciones fuera de rango; revise unidades y NoData")
    elevations = merged[::-1].copy()
    reference = float(elevations[sample_count // 2, sample_count // 2])
    info = {**source, "grid_size": [sample_count, sample_count],
            "pixel_resolution_m": round(max(resolutions), 3),
            "output_grid_spacing_m": round(max(dx, dy) * 111_320, 3),
            "elevation_min_m": round(float(elevations.min()), 3),
            "elevation_max_m": round(float(elevations.max()), 3),
            "reference_elevation_m": reference, "resampling": resampling.name, "coverage": 1.0}
    return TerrainGrid(np.linspace(bbox.west, bbox.east, sample_count),
                       np.linspace(bbox.south, bbox.north, sample_count), elevations, reference, info)


def local_terrain(store: DatasetStore, dataset_id: str, bbox: BoundingBox) -> TerrainGrid:
    record = store.get(dataset_id)
    if record["kind"] not in {"dtm", "dsm"}:
        raise ValueError("El dataset seleccionado no contiene elevaciones")
    source = {**record, "provider": f"local:{dataset_id}", "dataset": record["name"],
              "surface_type": record["kind"].upper()}
    grid = read_dem_grid([store.data_path(dataset_id)], bbox, source,
                        0.3048 if record["vertical_unit"] == "ft" else 1.0)
    grid.warnings.append("DEM local: datum, unidades y tipo de superficie declarados por el usuario.")
    if record["kind"] == "dsm":
        grid.warnings.append("DSM local: puede incluir copas y tejados; la base del edificio puede quedar elevada.")
    return grid


def copernicus_urls(bbox: BoundingBox) -> list[str]:
    urls = []
    for lat in range(math.floor(bbox.south), math.floor(bbox.north) + 1):
        for lon in range(math.floor(bbox.west), math.floor(bbox.east) + 1):
            tile = f"Copernicus_DSM_COG_10_{'N' if lat >= 0 else 'S'}{abs(lat):02d}_00_{'E' if lon >= 0 else 'W'}{abs(lon):03d}_00_DEM"
            urls.append(f"https://copernicus-dem-30m.s3.amazonaws.com/{tile}/{tile}.tif")
    if len(urls) > 4:
        raise ValueError("Región DEM excesiva; divida el área en sectores")
    return urls


class CopernicusTerrainProvider:
    id = "copernicus-dem"

    def __init__(self, cache: FileCache):
        self.cache = cache

    def fetch(self, bbox: BoundingBox) -> TerrainGrid:
        key = self.cache.key("copernicus-2021-grid-v1", bbox.model_dump())
        cached = self.cache.read_json(key)
        if cached:
            return TerrainGrid(np.array(cached["lon"]), np.array(cached["lat"]),
                np.array(cached["elevations"], dtype="float32"), cached["reference"],
                {**cached["source"], "from_cache": True}, cached["warnings"])
        urls = copernicus_urls(bbox)
        grid = read_dem_grid(urls, bbox, {
            "provider": self.id, "dataset": "Copernicus DEM GLO-30 Public",
            "version": "2021 release (AWS)", "surface_type": "DSM",
            "vertical_datum": "EGM2008", "vertical_unit": "m",
            "license": "Copernicus DEM License", "source_url": "https://registry.opendata.aws/copernicus-dem/",
            "tile_urls": urls, "from_cache": False,
        })
        grid.warnings.append("Copernicus GLO-30 es un DSM (~30 m), no terreno desnudo: puede incluir edificios y vegetación; no sirve para medir alturas individuales.")
        self.cache.write_json(key, {"lon": grid.longitudes.tolist(), "lat": grid.latitudes.tolist(),
            "elevations": grid.elevations_m.tolist(), "reference": grid.reference_elevation_m,
            "source": grid.source, "warnings": grid.warnings})
        return grid
