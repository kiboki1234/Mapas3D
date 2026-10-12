import json
import struct

import numpy as np
import pytest

from app.generation.glb import export_glb, validate_glb
from app.models.domain import FusedDataset, TerrainGrid
from app.projection.service import LocalProjection
from app.providers.osm import _number
from app.providers.worldcover import CLASSES, WorldCoverProvider
from app.cache.service import FileCache
from app.models.schemas import BoundingBox


@pytest.mark.parametrize("value, expected", [("10 m", 10), ("10 ft", 3.048), ("6' 2\"", 1.8796),
                                           ("3,5", 3.5), ("5;10", None), ("5-10", None), ("NaN", None), ("12 yards", None)])
def test_osm_units_are_not_silently_misread(value, expected):
    actual = _number(value)
    assert actual is None if expected is None else actual == pytest.approx(expected)


def test_worldcover_exports_class_materials_not_fictional_vegetation(tmp_path):
    terrain = TerrainGrid(np.linspace(0, .001, 3), np.linspace(0, .001, 3), np.zeros((3, 3)), 0,
        {"provider": "test"}, landcover=np.array([[10, 50, 50], [80, 30, 30], [80, 30, 30]]),
        landcover_source={"dataset": "test classification"})
    path = tmp_path / "classified.glb"
    export_glb(FusedDataset([], [], [], [], []), LocalProjection.at(0, 0), path, {}, terrain)
    assert validate_glb(path)["meshes"] == 1
    content = path.read_bytes()
    size = struct.unpack_from("<I", content, 12)[0]
    doc = json.loads(content[20:20 + size])
    assert all(item["name"].startswith("WorldCover") for item in doc["materials"])
    assert len(doc["meshes"][0]["primitives"]) > 1
    assert doc["nodes"][0]["extras"]["landcover_source"]["dataset"] == "test classification"


def test_worldcover_cached_classes_preserved(tmp_path, monkeypatch):
    cache = FileCache(tmp_path)
    terrain = TerrainGrid(np.linspace(0, .001, 3), np.linspace(0, .001, 3), np.zeros((3, 3)), 0, {})
    bbox = BoundingBox(west=0, east=.001, south=0, north=.001)
    key = cache.key("worldcover-v200-2021-v1", {**bbox.model_dump(), "count": 3})
    cache.write_json(key, {"classes": [[10] * 3] * 3, "source": {"dataset": "fixture"}})
    provider = WorldCoverProvider(cache)
    source = provider.apply(terrain, bbox)
    assert source["from_cache"]
    assert np.all(terrain.landcover == 10)
