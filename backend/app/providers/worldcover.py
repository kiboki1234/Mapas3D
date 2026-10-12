from __future__ import annotations

import math

import numpy as np
from rasterio.enums import Resampling

from app.cache.service import FileCache
from app.models.domain import TerrainGrid
from app.models.schemas import BoundingBox
from app.providers.raster_dem import read_dem_grid

# These are class symbols, never photographic colours or individual trees.
CLASSES = {
    10: ("Arbolado", "006400"), 20: ("Matorral", "ffbb22"),
    30: ("Pastizal", "ffff4c"), 40: ("Cultivo", "f096ff"),
    50: ("Construido", "fa0000"), 60: ("Suelo desnudo", "b4b4b4"),
    70: ("Nieve/hielo", "f0f0f0"), 80: ("Agua permanente", "0064c8"),
    90: ("Humedal herbáceo", "0096a0"), 95: ("Manglar", "00cf75"),
    100: ("Musgo/liquen", "fae6a0"),
}


class WorldCoverProvider:
    def __init__(self, cache: FileCache):
        self.cache = cache

    def apply(self, terrain: TerrainGrid, bbox: BoundingBox) -> dict:
        count = len(terrain.longitudes)
        key = self.cache.key("worldcover-v200-2021-v1", {**bbox.model_dump(), "count": count})
        cached = self.cache.read_json(key)
        if cached:
            terrain.landcover = np.array(cached["classes"], dtype="uint8")
            terrain.landcover_source = {**cached["source"], "from_cache": True}
            return terrain.landcover_source
        urls = []
        for lat in range(math.floor(bbox.south / 3) * 3, math.floor(bbox.north / 3) * 3 + 1, 3):
            for lon in range(math.floor(bbox.west / 3) * 3, math.floor(bbox.east / 3) * 3 + 1, 3):
                tile = f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}{'E' if lon >= 0 else 'W'}{abs(lon):03d}"
                urls.append(f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif")
        if len(urls) > 4:
            raise ValueError("Área WorldCover excesiva")
        source = {"provider": "esa-worldcover", "dataset": "ESA WorldCover 2021 v200",
                  "license": "CC-BY-4.0", "source_date": "2021", "pixel_resolution_m": 10,
                  "source_url": "https://esa-worldcover.org/en/data-access",
                  "tile_urls": urls, "from_cache": False, "resampling": "nearest",
                  "method": "nearest grid node per terrain triangle; thematic approximation",
                  "classification_not_photography": True,
                  "legend": {str(key): value[0] for key, value in CLASSES.items()}}
        grid = read_dem_grid(urls, bbox, source, sample_count=count, resampling=Resampling.nearest)
        classes = grid.elevations_m.astype("uint8")
        if not np.isin(classes, list(CLASSES)).all():
            raise ValueError("WorldCover contiene NoData o clases no reconocidas")
        source["output_grid_spacing_m"] = grid.source["output_grid_spacing_m"]
        terrain.landcover = classes
        terrain.landcover_source = source
        self.cache.write_json(key, {"classes": classes.tolist(), "source": source})
        return source
