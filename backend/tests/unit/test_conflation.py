from shapely.geometry import Polygon

from app.conflation.service import fuse_results
from app.models.domain import AttributeValue, Building, ProviderResult
from app.projection.service import LocalProjection


def _building(identifier: str, provider: str, geometry: Polygon, **attributes):
    return Building(
        id=identifier,
        geometry=geometry,
        provider=provider,
        original_ids={provider: identifier},
        attributes={key: AttributeValue(value, provider) for key, value in attributes.items()},
        license="ODbL-1.0",
    )


def test_duplicate_is_merged_and_osm_height_enriches_overture_geometry():
    overture = _building(
        "overture-a",
        "overture",
        Polygon([(-78.44352, -0.31490), (-78.44342, -0.31490), (-78.44342, -0.31482), (-78.44352, -0.31482)]),
    )
    osm = _building(
        "osm-b",
        "osm",
        Polygon([(-78.443519, -0.314899), (-78.443421, -0.314899), (-78.443421, -0.314821), (-78.443519, -0.314821)]),
        height=12.0,
    )
    fused = fuse_results(
        [
            ProviderResult("overture", [overture], [], {"provider": "overture"}),
            ProviderResult("osm", [osm], [], {"provider": "osm"}),
        ],
        LocalProjection.at(-0.314861, -78.443472),
        3.0,
        6.0,
    )
    assert len(fused.buildings) == 1
    assert len(fused.fusion_decisions) == 1
    assert fused.buildings[0].provider == "overture"
    assert fused.buildings[0].attributes["height"].value == 12.0
    assert fused.buildings[0].attributes["height"].source == "osm"


def test_adjacent_buildings_are_not_merged():
    first = _building("a", "overture", Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))
    second = _building("b", "osm", Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]))
    projection = LocalProjection.at(0.5, 0.5)
    fused = fuse_results(
        [ProviderResult("overture", [first], [], {}), ProviderResult("osm", [second], [], {})],
        projection,
        3.0,
        6.0,
    )
    assert len(fused.buildings) == 2
    assert all(
        building.attributes["height_type"].value == "footprint_only"
        for building in fused.buildings
    )
    assert all(building.attributes["height"].value == 0 for building in fused.buildings)


def test_replacing_estimated_height_also_replaces_category():
    polygon = Polygon([(0, 0), (.001, 0), (.001, .001), (0, .001)])
    first = _building("a", "overture", polygon)
    first.attributes = {"height": AttributeValue(30, "prediction", estimated=True),
                        "height_type": AttributeValue("estimated", "prediction")}
    second = _building("b", "osm", polygon, height=12)
    fused = fuse_results([ProviderResult("overture", [first], [], {}), ProviderResult("osm", [second], [], {})],
                         LocalProjection.at(0, 0), 3, 6)
    result = fused.buildings[0]
    assert result.attributes["height"].value == 12
    assert result.attributes["height_type"].value == "explicit"
    assert result.attributes["height_type"].source == "osm"
    assert first.attributes["height"].value == 30  # Fusion must not mutate input evidence.


def test_observed_floors_beat_spatial_estimate():
    building = _building("a", "overture", Polygon([(0, 0), (.001, 0), (.001, .001), (0, .001)]), num_floors=3)
    building.attributes["height"] = AttributeValue(25, "prediction", estimated=True)
    fused = fuse_results([ProviderResult("overture", [building], [], {})], LocalProjection.at(0, 0), 3, 6)
    assert fused.buildings[0].attributes["height"].value == 9
    assert fused.buildings[0].attributes["height_type"].value == "derived"


def test_local_geometry_priority_and_namespaced_identifiers():
    first = _building("1", "local:test", Polygon([(0, 0), (.001, 0), (.001, .001), (0, .001)]), height=10)
    second = _building("1", "osm", Polygon([(.0005, .0005), (.0015, .0005), (.0015, .0015), (.0005, .0015)]), height=20)
    fused = fuse_results([ProviderResult("osm", [second], [], {}), ProviderResult("local:test", [first], [], {})], LocalProjection.at(0, 0), 3, 6)
    assert len(fused.buildings) == 2  # Same ID in different sources does not prove equivalence.
    assert fused.buildings[0].provider == "local:test"


def test_already_merged_osm_reference_does_not_absorb_neighbour():
    polygon = Polygon([(0, 0), (.001, 0), (.001, .001), (0, .001)])
    overture = _building("gers", "overture", polygon)
    overture.source_records = [{"dataset": "OpenStreetMap", "record_id": "w10@1"}]
    osm = _building("way/10", "osm", polygon)
    neighbour = _building("way/20", "osm", Polygon([(.0008, 0), (.0018, 0), (.0018, .001), (.0008, .001)]))
    fused = fuse_results([ProviderResult("overture", [overture], [], {}),
                         ProviderResult("osm", [osm, neighbour], [], {})], LocalProjection.at(0, 0), 3, 6)
    assert len(fused.buildings) == 2


def test_equal_observed_height_upgrades_estimate_and_removes_stale_method():
    polygon = Polygon([(0, 0), (.001, 0), (.001, .001), (0, .001)])
    first = _building("a", "overture", polygon)
    first.attributes = {"height": AttributeValue(12, "prediction", estimated=True),
                        "height_type": AttributeValue("estimated", "prediction"),
                        "height_method": AttributeValue("raster prediction", "prediction")}
    second = _building("b", "osm", polygon, height=12)
    fused = fuse_results([ProviderResult("overture", [first], [], {}), ProviderResult("osm", [second], [], {})],
                        LocalProjection.at(0, 0), 3, 6)
    assert not fused.buildings[0].attributes["height"].estimated
    assert fused.buildings[0].attributes["height"].source == "osm"
    assert "height_method" not in fused.buildings[0].attributes

