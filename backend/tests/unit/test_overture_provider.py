import json
import subprocess
import sys
from types import SimpleNamespace

import pytest
from shapely.geometry import Polygon

from app.cache.service import FileCache
from app.core.errors import ProviderUnavailableError
from app.models.schemas import BoundingBox
from app.providers.overture import OvertureProvider
from app.providers.overture_download import download


BBOX = BoundingBox(west=-78.444, east=-78.443, south=-0.315, north=-0.314)


def test_worker_failure_is_not_cached_as_empty_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr("app.providers.overture.overture_available", lambda: True)
    monkeypatch.setattr("app.providers.overture.subprocess.run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=1, stderr="S3 unavailable", stdout=""))
    cache = FileCache(tmp_path)
    with pytest.raises(ProviderUnavailableError, match="S3 unavailable"):
        OvertureProvider(cache).fetch(BBOX)
    assert cache.stats()["entries"] == 0


def test_worker_timeout_is_reported_without_caching(tmp_path, monkeypatch):
    monkeypatch.setattr("app.providers.overture.overture_available", lambda: True)

    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 120
        raise subprocess.TimeoutExpired("overture", 120)

    monkeypatch.setattr("app.providers.overture.subprocess.run", timeout)
    cache = FileCache(tmp_path)
    with pytest.raises(ProviderUnavailableError, match="120 segundos"):
        OvertureProvider(cache).fetch(BBOX)
    assert cache.stats()["entries"] == 0


def test_sdk_missing_reader_is_failure_not_empty_dataset(monkeypatch):
    core = SimpleNamespace(get_latest_release=lambda: "test-release",
                           record_batch_reader=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "overturemaps", SimpleNamespace(core=core))
    monkeypatch.setattr("socket.setdefaulttimeout", lambda timeout: None)
    with pytest.raises(RuntimeError, match="no devolvió un lector"):
        download(BBOX.as_tuple())


def test_height_geometry_release_survive_worker_and_cache(tmp_path, monkeypatch):
    geometry = Polygon([(-78.444, -0.315), (-78.443, -0.315),
                        (-78.443, -0.314), (-78.444, -0.314)])
    payload = {"release": "test-release", "rows": [
        {"id": "test", "geometry": geometry.wkb.hex(), "height": 14.5, "version": 1},
    ]}
    monkeypatch.setattr("app.providers.overture.overture_available", lambda: True)
    monkeypatch.setattr("app.providers.overture.subprocess.run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(payload)))
    provider = OvertureProvider(FileCache(tmp_path))
    first = provider.fetch(BBOX)
    second = provider.fetch(BBOX)
    assert first.buildings[0].geometry.equals(geometry)
    assert second.buildings[0].attributes["height"].value == 14.5
    assert second.source["from_cache"]
    assert second.source["dataset_releases"] == ["test-release"]
