import json
from pathlib import Path

from app.cache.service import FileCache
from app.core.config import Settings
from app.models.schemas import BoundingBox
from app.providers.osm import OpenStreetMapProvider


def test_osm_fixture_is_normalized(monkeypatch, tmp_path: Path):
    fixture = json.loads((Path(__file__).parents[1] / "fixtures" / "osm_small.json").read_text())
    provider = OpenStreetMapProvider(Settings(data_dir=tmp_path), FileCache(tmp_path / "cache"))
    monkeypatch.setattr(provider, "_download", lambda bbox, roads: (fixture, "fixture", False))
    result = provider.fetch(BoundingBox(west=-78.444, south=-0.316, east=-78.443, north=-0.314))
    assert len(result.buildings) == 1
    assert len(result.roads) == 1
    assert result.buildings[0].attributes["num_floors"].value == 3
    assert result.roads[0].width_m == 6.0


def test_map_api_nodes_are_hydrated_into_way_geometry():
    payload = {
        "elements": [
            {"type": "node", "id": 1, "lat": -0.1, "lon": -78.1},
            {"type": "node", "id": 2, "lat": -0.1, "lon": -78.0},
            {"type": "node", "id": 3, "lat": 0.0, "lon": -78.0},
            {"type": "node", "id": 4, "lat": -0.1, "lon": -78.1},
            {"type": "way", "id": 10, "nodes": [1, 2, 3, 4], "tags": {"building": "yes"}},
            {"type": "way", "id": 11, "nodes": [1, 2], "tags": {"natural": "tree_row"}},
        ]
    }
    hydrated = OpenStreetMapProvider._hydrate_map_api(payload)
    assert len(hydrated["elements"]) == 1
    assert hydrated["elements"][0]["id"] == 10
    assert hydrated["elements"][0]["geometry"][1] == {"lat": -0.1, "lon": -78.0}

