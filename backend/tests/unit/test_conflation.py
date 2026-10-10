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

