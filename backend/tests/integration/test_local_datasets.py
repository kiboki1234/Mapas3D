import json

import numpy as np
import pytest
from fastapi.testclient import TestClient
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds

from app.core.config import Settings
from app.datasets.store import DatasetStore
from app.jobs.repository import JobRepository
from app.jobs.service import GenerationService
from app.main import app
from app.models.schemas import BoundingBox, GenerationRequest
from app.providers.local import fetch_local_buildings


DESCRIPTION = {"name": "Catastro de prueba", "kind": "buildings", "license": "CC0-1.0",
               "attribution": "Fixture sintético para pruebas, no usar como datos reales", "source_date": "2026-01-01"}
FEATURES = {"type": "FeatureCollection", "features": [{"type": "Feature", "id": "1",
    "properties": {"height_m": 12, "name": "Prueba"}, "geometry": {"type": "Polygon", "coordinates": [
        [[-.0001, -.0001], [.0001, -.0001], [.0001, .0001], [-.0001, .0001], [-.0001, -.0001]]
    ]}}]}


@pytest.fixture
def client(tmp_path):
    with TestClient(app) as client:
        settings = Settings(data_dir=tmp_path, local_imports_enabled=True)
        app.state.settings = settings
        app.state.generation_service = GenerationService(settings, JobRepository(tmp_path / "jobs.db"), {})
        yield client


def upload(client, content=FEATURES, description=DESCRIPTION):
    return client.post("/api/datasets/local", params={"description": json.dumps(description)},
                       content=json.dumps(content).encode(), headers={"Content-Type": "application/octet-stream"})


def test_import_to_real_glb_flow_without_network(client):
    response = upload(client)
    assert response.status_code == 201, response.text
    dataset_id = response.json()["id"]
    assert len(response.json()["sha256"]) == 64
    assert client.get("/api/datasets/local").json()["datasets"][0]["id"] == dataset_id
    response = client.post("/api/generations", json={"latitude": 0, "longitude": 0, "radius_m": 100,
        "providers": [], "building_dataset_ids": [dataset_id], "include_terrain": False})
    assert response.status_code == 202, response.text
    job_id = response.json()["id"]
    completed = client.get(f"/api/generations/{job_id}").json()
    assert completed["status"] == "completed", completed
    metadata = client.get(f"/api/generations/{job_id}/metadata").json()
    assert metadata["quality"]["height"]["explicit"] == 1
    assert metadata["licenses"][0]["license"] == "CC0-1.0"
    assert "Catastro de prueba" in client.get(f"/api/generations/{job_id}/attributions").text
    assert client.get(f"/api/generations/{job_id}/model").content.startswith(b"glTF")


def test_estimated_height_keeps_its_category(client):
    content = json.loads(json.dumps(FEATURES))
    content["features"][0]["properties"]["height_estimated"] = True
    dataset_id = upload(client, content).json()["id"]
    store = DatasetStore(app.state.settings)
    result = fetch_local_buildings(store, dataset_id, BoundingBox(west=-.1, east=.1, south=-.1, north=.1))
    assert result.buildings[0].attributes["height"].estimated
    assert result.buildings[0].attributes["height_type"].value == "estimated"


def test_bad_geojson_is_rejected_without_leftover_files(client):
    response = upload(client, {"type": "FeatureCollection", "features": []})
    assert response.status_code == 422
    assert list(app.state.settings.imports_dir.iterdir()) == []


def test_invalid_height_and_date_rejected(client):
    content = json.loads(json.dumps(FEATURES))
    content["features"][0]["properties"]["height_m"] = float("nan")
    assert upload(client, content).status_code == 422
    assert upload(client, description={**DESCRIPTION, "source_date": "2026-99-01"}).status_code == 422


def test_closed_imports_and_path_traversal(client):
    app.state.settings.local_imports_enabled = False
    app.state.settings.environment = "production"
    assert upload(client).status_code == 403
    with pytest.raises(ValueError, match="inválido"):
        DatasetStore(app.state.settings).get("../config")


def test_unsupported_license_is_not_accepted(client):
    assert upload(client, description={**DESCRIPTION, "license": "unknown"}).status_code == 422


def test_untrusted_origin_cannot_write_local_files(client):
    response = client.post("/api/datasets/local", params={"description": json.dumps(DESCRIPTION)},
        content=json.dumps(FEATURES), headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 403


def test_size_limit_cleans_up_partial_upload(client):
    app.state.settings.local_import_max_mb = 1
    response = client.post("/api/datasets/local", params={"description": json.dumps(DESCRIPTION)},
                          content=b" " * (1024 * 1024 + 1))
    assert response.status_code == 413
    assert not list(app.state.settings.imports_dir.iterdir())


def test_real_geotiff_upload_validation(client):
    with MemoryFile() as memory:
        with memory.open(driver="GTiff", height=10, width=10, count=1, dtype="float32", crs="EPSG:4326",
                         transform=from_bounds(-.01, -.01, .01, .01, 10, 10)) as dataset:
            dataset.write(np.full((10, 10), 123., dtype="float32"), 1)
        payload = memory.read()
    description = {**DESCRIPTION, "kind": "dtm", "vertical_datum": "EGM2008"}
    response = client.post("/api/datasets/local", params={"description": json.dumps(description)}, content=payload)
    assert response.status_code == 201, response.text
    buildings = upload(client).json()["id"]
    request = {"latitude": 0, "longitude": 0, "radius_m": 100, "providers": [],
        "building_dataset_ids": [buildings], "include_terrain": True,
        "terrain_source": "local", "terrain_dataset_id": response.json()["id"]}
    job_id = client.post("/api/generations", json=request).json()["id"]
    job = client.get(f"/api/generations/{job_id}").json()
    assert job["status"] == "completed", job
    quality = client.get(f"/api/generations/{job_id}/quality").json()
    assert quality["terrain"]["surface_type"] == "DTM"
    assert quality["terrain"]["elevation_min_m"] == pytest.approx(123)


def test_request_rejects_invalid_local_selection():
    with pytest.raises(ValueError):
        GenerationRequest(latitude=0, longitude=0, terrain_source="local")
    with pytest.raises(ValueError):
        GenerationRequest(latitude=0, longitude=0, building_dataset_ids=["../../data"])
    with pytest.raises(ValueError):
        GenerationRequest(latitude=0, longitude=0, include_terrain=False, include_landcover=True)
