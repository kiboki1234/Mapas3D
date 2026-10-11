from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.cache.service import FileCache
from app.core.config import Settings
from app.models.schemas import BoundingBox
from app.providers.terrain import (
    TerrariumTerrainProvider,
    decode_terrarium,
    web_mercator_tile,
)


def _terrarium_png(elevation_m: float) -> bytes:
    encoded = elevation_m + 32768.0
    red = int(encoded // 256)
    green = int(encoded % 256)
    blue = int(round((encoded - int(encoded)) * 256))
    image = Image.new("RGB", (2, 2), (red, green, blue))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_terrarium_decoder_preserves_metric_elevation():
    values = decode_terrarium(_terrarium_png(2798.25))
    assert values.shape == (2, 2)
    assert values[0, 0] == pytest.approx(2798.25)


def test_web_mercator_tile_for_quito_is_stable():
    x, y = web_mercator_tile(-0.314861, -78.443472, 12)
    assert int(x) == 1155
    assert int(y) == 2051


def test_provider_builds_traceable_grid_without_network(tmp_path, monkeypatch):
    settings = Settings(data_dir=tmp_path, terrain_zoom=12)
    provider = TerrariumTerrainProvider(settings, FileCache(tmp_path / "dem"))
    tile = np.full((256, 256), 2800.0, dtype=np.float32)
    monkeypatch.setattr(provider, "_tile", lambda zoom, x, y: (tile, False, "srtm/N00W079.tif"))
    terrain = provider.fetch(BoundingBox(
        west=-78.445, south=-0.316, east=-78.442, north=-0.313
    ))
    assert terrain.elevations_m.shape == (33, 33)
    assert terrain.reference_elevation_m == pytest.approx(2800.0)
    assert terrain.sample(-0.3145, -78.4435) == pytest.approx(2800.0)
    assert terrain.source["provider"] == "mapzen-terrain"
    assert terrain.source["imagery_sources"] == ["srtm/N00W079.tif"]
