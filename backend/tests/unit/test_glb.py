from pathlib import Path

from shapely.geometry import LineString, Polygon

from app.generation.glb import export_glb, validate_glb
from app.models.domain import AttributeValue, Building, FusedDataset, Road
from app.projection.service import LocalProjection


def test_glb_contains_building_and_road_meshes(tmp_path: Path):
    building = Building(
        id="test-building",
        geometry=Polygon(
            [
                (-78.44352, -0.31490),
                (-78.44342, -0.31490),
                (-78.44342, -0.31482),
                (-78.44352, -0.31482),
            ]
        ),
        provider="osm",
        original_ids={"osm": "way/1"},
        attributes={
            "height": AttributeValue(12.0, "osm"),
            "height_type": AttributeValue("explicit", "osm"),
        },
    )
    road = Road(
        id="test-road",
        geometry=LineString([(-78.44360, -0.31500), (-78.44330, -0.31470)]),
        provider="osm",
        road_class="residential",
        width_m=6.0,
    )
    fused = FusedDataset([building], [road], [], [], [])
    path = tmp_path / "scene.glb"
    export_glb(fused, LocalProjection.at(-0.314861, -78.443472), path, {"test": True})
    report = validate_glb(path)
    assert report["meshes"] == 2
    assert report["nodes"] == 2
    assert report["bytes"] > 500

