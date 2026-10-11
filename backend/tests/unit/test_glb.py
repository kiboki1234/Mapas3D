from pathlib import Path
from collections import Counter
import json
import struct

import numpy as np
import pytest

from shapely.geometry import LineString, MultiPolygon, Polygon

from app.generation.glb import (
    GlbBuilder, _mesh_for_extrusion, _triangles_inside, export_glb, validate_glb,
)
from app.models.domain import AttributeValue, Building, FusedDataset, Road, TerrainGrid
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


@pytest.mark.parametrize("polygon", [
    Polygon([(0, 0), (20, 0), (20, 10), (0, 10)]),
    Polygon([(0, 0), (0, 10), (20, 10), (20, 0)]),
    Polygon([(0, 0), (20, 0), (20, 4), (6, 4), (6, 15), (0, 15)]),
    Polygon([(0, 0), (30, 0), (30, 20), (0, 20)],
            holes=[[(3, 3), (12, 3), (12, 15), (3, 15)],
                   [(18, 3), (26, 3), (26, 15), (18, 15)]]),
])
def test_extrusion_preserves_footprint_holes_volume_and_closed_edges(polygon):
    triangles = _triangles_inside(polygon)
    assert sum(triangle.area for triangle in triangles) == pytest.approx(polygon.area)
    assert all(polygon.covers(triangle) for triangle in triangles)
    vertices, indices = _mesh_for_extrusion(polygon, 12)
    faces = vertices[indices.reshape(-1, 3)].astype(float)
    volume = np.sum(np.einsum("ij,ij->i", faces[:, 0],
                    np.cross(faces[:, 1], faces[:, 2]))) / 6
    assert volume == pytest.approx(polygon.area * 12)
    edges = Counter()
    for face in faces:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edges[tuple(sorted((tuple(face[a]), tuple(face[b]))))] += 1
    assert set(edges.values()) == {2}
    assert vertices[:, 1].min() == 0
    assert vertices[:, 1].max() == 12


def _builder():
    geometry = MultiPolygon([
        Polygon([(0, 0), (20, 0), (20, 10), (0, 10)]),
        Polygon([(30, 0), (35, 0), (35, 5), (30, 5)]),
    ])
    vertices, indices = _mesh_for_extrusion(geometry, 9)
    builder = GlbBuilder()
    builder.add_mesh("building", vertices, indices, 0, {"feature_id": "test"})
    return builder


def test_source_glb_contains_normals_and_no_synthetic_textures(tmp_path):
    path = tmp_path / "source.glb"
    _builder().write(path, {})
    report = validate_glb(path)
    assert report["textures"] == 0
    assert report["triangles"] == 24
    raw = path.read_bytes()
    json_length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + json_length])
    primitives = document["meshes"][0]["primitives"]
    assert {item["material"] for item in primitives} == {0}
    for primitive in primitives:
        assert set(primitive["attributes"]) == {"POSITION", "NORMAL"}
        assert document["accessors"][primitive["indices"]]["componentType"] == 5123
    assert all(material["pbrMetallicRoughness"]["metallicFactor"] == 0
               for material in document["materials"])


def test_glb_validation_rejects_out_of_range_indices(tmp_path):
    path = tmp_path / "corrupt.glb"
    _builder().write(path, {})
    raw = bytearray(path.read_bytes())
    json_length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + json_length])
    accessor = document["accessors"][document["meshes"][0]["primitives"][0]["indices"]]
    view = document["bufferViews"][accessor["bufferView"]]
    struct.pack_into("<H", raw, 28 + json_length + view["byteOffset"], 65534)
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="Índices"):
        validate_glb(path)


def test_glb_validation_rejects_empty_scene(tmp_path):
    path = tmp_path / "empty.glb"
    GlbBuilder().write(path, {})
    with pytest.raises(ValueError, match="mallas"):
        validate_glb(path)


def test_dem_terrain_changes_ground_height_and_is_exported(tmp_path):
    building = Building(
        id="measured-building",
        geometry=Polygon([
            (-78.44350, -0.31489), (-78.44344, -0.31489),
            (-78.44344, -0.31483), (-78.44350, -0.31483),
        ]),
        provider="osm",
        original_ids={"osm": "way/9"},
        attributes={
            "height": AttributeValue(10.0, "osm"),
            "height_type": AttributeValue("explicit", "osm"),
        },
    )
    terrain = TerrainGrid(
        longitudes=np.array([-78.44360, -78.44335]),
        latitudes=np.array([-0.31500, -0.31470]),
        elevations_m=np.array([[2790.0, 2792.0], [2800.0, 2802.0]], dtype=np.float32),
        reference_elevation_m=2796.0,
        source={
            "provider": "mapzen-terrain",
            "dataset": "Terrarium",
            "vertical_datum": "EGM96",
            "elevation_min_m": 2790.0,
            "elevation_max_m": 2802.0,
        },
    )
    path = tmp_path / "terrain.glb"
    export_glb(
        FusedDataset([building], [], [], [], []),
        LocalProjection.at(-0.314861, -78.443472),
        path,
        {"test": True},
        terrain,
    )
    report = validate_glb(path)
    assert report["meshes"] == 3  # DEM, zócalo de ajuste y edificio.
    raw = path.read_bytes()
    json_length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + json_length])
    assert document["nodes"][0]["extras"]["feature_type"] == "terrain"
    building_node = next(node for node in document["nodes"]
                         if node["extras"].get("feature_type") == "building")
    assert building_node["extras"]["ground_elevation_m"] > 2790
    assert building_node["extras"]["foundation_depth_m"] > 0
    primitive = document["meshes"][building_node["mesh"]]["primitives"][0]
    positions = document["accessors"][primitive["attributes"]["POSITION"]]
    assert positions["max"][1] - positions["min"][1] == pytest.approx(10.0)

