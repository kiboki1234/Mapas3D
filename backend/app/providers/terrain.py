from __future__ import annotations

import math
from io import BytesIO
from typing import Protocol

import httpx
import numpy as np
from PIL import Image

from app.cache.service import FileCache
from app.core.config import Settings
from app.core.errors import ProviderUnavailableError
from app.models.domain import TerrainGrid
from app.models.schemas import BoundingBox


class TerrainProvider(Protocol):
    def fetch(self, bbox: BoundingBox) -> TerrainGrid: ...


def web_mercator_tile(latitude: float, longitude: float, zoom: int) -> tuple[float, float]:
    latitude = max(-85.05112878, min(85.05112878, latitude))
    scale = 2**zoom
    x = (longitude + 180.0) / 360.0 * scale
    y = (
        1.0
        - math.asinh(math.tan(math.radians(latitude))) / math.pi
    ) / 2.0 * scale
    return x, y


def decode_terrarium(image_bytes: bytes) -> np.ndarray:
    """Decodifica Terrain-RGB Terrarium a metros: R*256 + G + B/256 - 32768."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    except Exception as exc:
        raise ValueError(f"Tile DEM inválido: {exc}") from exc
    return rgb[:, :, 0] * 256.0 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768.0


class TerrariumTerrainProvider:
    id = "mapzen-terrain"

    def __init__(self, settings: Settings, cache: FileCache):
        self.settings = settings
        self.cache = cache

    def _tile(self, zoom: int, x: int, y: int) -> tuple[np.ndarray, bool, str | None]:
        key = self.cache.key("terrarium-v1", {"z": zoom, "x": x, "y": y})
        cached = self.cache.read_bytes(key, ".png")
        if cached is not None:
            return decode_terrarium(cached), True, None
        url = self.settings.terrain_tile_endpoint.format(z=zoom, x=x, y=y)
        try:
            with httpx.Client(
                timeout=self.settings.http_timeout_seconds,
                headers={"User-Agent": self.settings.user_agent},
                follow_redirects=True,
            ) as client:
                response = client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"No fue posible descargar el DEM {url}: {exc}") from exc
        if not response.content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ProviderUnavailableError(f"La fuente DEM no devolvió un PNG válido: {url}")
        self.cache.write_bytes(key, response.content, ".png")
        imagery = response.headers.get("x-imagery-sources")
        return decode_terrarium(response.content), False, imagery

    @staticmethod
    def _sample_tile(tile: np.ndarray, tile_x: float, tile_y: float) -> float:
        height, width = tile.shape
        px = min(max((tile_x - math.floor(tile_x)) * width, 0.0), width - 1.0)
        py = min(max((tile_y - math.floor(tile_y)) * height, 0.0), height - 1.0)
        x0, y0 = int(math.floor(px)), int(math.floor(py))
        x1, y1 = min(x0 + 1, width - 1), min(y0 + 1, height - 1)
        tx, ty = px - x0, py - y0
        top = tile[y0, x0] * (1 - tx) + tile[y0, x1] * tx
        bottom = tile[y1, x0] * (1 - tx) + tile[y1, x1] * tx
        return float(top * (1 - ty) + bottom * ty)

    def fetch(self, bbox: BoundingBox) -> TerrainGrid:
        zoom = self.settings.terrain_zoom
        # 33x33 conserva la resolución efectiva SRTM (~30 m) para el radio máximo de 1 km.
        sample_count = 33 if max(bbox.east - bbox.west, bbox.north - bbox.south) < 0.01 else 65
        longitudes = np.linspace(bbox.west, bbox.east, sample_count, dtype=np.float64)
        latitudes = np.linspace(bbox.south, bbox.north, sample_count, dtype=np.float64)
        elevations = np.empty((sample_count, sample_count), dtype=np.float32)
        tiles: dict[tuple[int, int], np.ndarray] = {}
        cached_tiles = 0
        imagery_sources: set[str] = set()
        for row, latitude in enumerate(latitudes):
            for column, longitude in enumerate(longitudes):
                tile_x, tile_y = web_mercator_tile(float(latitude), float(longitude), zoom)
                key = (int(math.floor(tile_x)), int(math.floor(tile_y)))
                if key not in tiles:
                    tile, cached, imagery = self._tile(zoom, *key)
                    tiles[key] = tile
                    cached_tiles += int(cached)
                    if imagery:
                        imagery_sources.update(item.strip() for item in imagery.split(",") if item.strip())
                elevations[row, column] = self._sample_tile(tiles[key], tile_x, tile_y)
        if not np.isfinite(elevations).all():
            raise ProviderUnavailableError("El DEM contiene elevaciones no finitas.")
        center_lat = (bbox.south + bbox.north) / 2
        center_lon = (bbox.west + bbox.east) / 2
        temporary = TerrainGrid(
            longitudes=longitudes,
            latitudes=latitudes,
            elevations_m=elevations,
            reference_elevation_m=0.0,
            source={},
        )
        reference = temporary.sample(center_lat, center_lon)
        resolution_m = (
            math.cos(math.radians(center_lat)) * 2 * math.pi * 6_378_137
            / (256 * 2**zoom)
        )
        source = {
            "provider": self.id,
            "dataset": "Mapzen Terrain Tiles / Terrarium",
            "license": "Multiple open elevation datasets; attribution required",
            "source_url": self.settings.terrain_tile_endpoint,
            "from_cache": cached_tiles == len(tiles),
            "raw_feature_count": len(tiles),
            "zoom": zoom,
            "tile_count": len(tiles),
            "grid_size": [sample_count, sample_count],
            "pixel_resolution_m": round(resolution_m, 2),
            "vertical_datum": "EGM96 geoid for SRTM-derived coverage",
            "imagery_sources": sorted(imagery_sources),
            "elevation_min_m": round(float(elevations.min()), 3),
            "elevation_max_m": round(float(elevations.max()), 3),
            "reference_elevation_m": round(reference, 3),
        }
        return TerrainGrid(
            longitudes=longitudes,
            latitudes=latitudes,
            elevations_m=elevations,
            reference_elevation_m=reference,
            source=source,
        )
