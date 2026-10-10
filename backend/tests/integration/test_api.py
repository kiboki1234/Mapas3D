from fastapi.testclient import TestClient

from app.main import app


def test_health_and_provider_contract():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        providers = client.get("/api/providers")
        assert providers.status_code == 200
        assert {item["id"] for item in providers.json()} == {"osm", "overture"}


def test_region_preview_uses_metric_projection():
    with TestClient(app) as client:
        response = client.post(
            "/api/regions/preview",
            json={"latitude": -0.314861, "longitude": -78.443472, "radius_m": 250},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["projected_crs"] == "EPSG:32717"
        assert payload["estimated_area_km2"] > 0

