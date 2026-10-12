from __future__ import annotations

from io import BytesIO
import math

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject

from app.datasets.store import DatasetStore
from app.models.domain import TerrainGrid
from app.models.schemas import BoundingBox


def _pixel_resolution_m(dataset: rasterio.io.DatasetReader, latitude: float) -> float:
    if dataset.crs and dataset.crs.is_geographic:
        return max(
            abs(dataset.res[1]) * 111_320,
            abs(dataset.res[0]) * 111_320 * math.cos(math.radians(latitude)),
        )
    if dataset.crs:
        return max(abs(dataset.res[0]), abs(dataset.res[1])) * dataset.crs.linear_units_factor[1]
    raise ValueError("Ortofoto sin CRS")


def apply_local_imagery(
    store: DatasetStore, dataset_id: str, bbox: BoundingBox, terrain: TerrainGrid
) -> dict:
    """Recorta una ortofoto declarada, la reproyecta y la deja lista para incrustar en GLB."""
    record = store.get(dataset_id)
    if record["kind"] != "imagery":
        raise ValueError("El dataset seleccionado no es una ortofoto")
    west, south, east, north = record["bounds_wgs84"]
    tolerance = 1e-8
    if (bbox.west < west - tolerance or bbox.south < south - tolerance
            or bbox.east > east + tolerance or bbox.north > north + tolerance):
        raise ValueError("La ortofoto no cubre por completo la región solicitada; recórtela con margen")

    center_latitude = (bbox.south + bbox.north) / 2
    ground_width = (bbox.east - bbox.west) * 111_320 * math.cos(math.radians(center_latitude))
    ground_height = (bbox.north - bbox.south) * 111_320
    with rasterio.Env(GDAL_PAM_ENABLED="NO"):
        with rasterio.open(store.data_path(dataset_id), driver="GTiff") as dataset:
            resolution = _pixel_resolution_m(dataset, center_latitude)
            longest = max(ground_width, ground_height)
            scale = min(1024 / longest, 1 / max(resolution, 0.01))
            width = max(64, min(1024, int(round(ground_width * scale))))
            height = max(64, min(1024, int(round(ground_height * scale))))
            target_transform = from_bounds(
                bbox.west, bbox.south, bbox.east, bbox.north, width, height
            )
            rgb = np.zeros((3, height, width), dtype=np.uint8)
            for band in range(3):
                reproject(
                    rasterio.band(dataset, band + 1),
                    rgb[band],
                    src_transform=dataset.transform,
                    src_crs=dataset.crs,
                    dst_transform=target_transform,
                    dst_crs="EPSG:4326",
                    resampling=Resampling.bilinear,
                )
            source_mask = dataset.dataset_mask()
            alpha = np.zeros((height, width), dtype=np.uint8)
            reproject(
                source_mask,
                alpha,
                src_transform=dataset.transform,
                src_crs=dataset.crs,
                dst_transform=target_transform,
                dst_crs="EPSG:4326",
                resampling=Resampling.nearest,
            )
    coverage = float(np.count_nonzero(alpha) / alpha.size)
    if coverage < 0.999:
        raise ValueError(
            f"La ortofoto contiene zonas sin datos dentro del área ({coverage:.1%} cubierto)"
        )
    image = np.moveaxis(rgb, 0, 2)
    output = BytesIO()
    Image.fromarray(image, mode="RGB").save(output, format="PNG", optimize=True)
    source = {
        **record,
        "provider": f"local:{dataset_id}",
        "dataset": record["name"],
        "texture_size": [width, height],
        "pixel_resolution_m": round(resolution, 3),
        "coverage": coverage,
        "resampling": "bilinear",
        "display_transform": "RGB uint8; no realce radiométrico aplicado",
    }
    terrain.imagery_png = output.getvalue()
    terrain.imagery_source = source
    return source
