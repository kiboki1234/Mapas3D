from pyproj import Transformer
from shapely.geometry import Polygon

from app.projection.service import LocalProjection, bounding_box_from_center, utm_epsg_for


def test_sangolqui_uses_utm_17_south():
    assert utm_epsg_for(-0.314861, -78.443472) == 32717


def test_local_projection_preserves_metric_dimensions():
    projection = LocalProjection.at(-0.314861, -78.443472)
    inverse = Transformer.from_crs(projection.epsg, 4326, always_xy=True)
    easting = projection.origin_easting
    northing = projection.origin_northing
    lonlat = [
        inverse.transform(easting + x, northing + y)
        for x, y in [(0, 0), (20, 0), (20, 10), (0, 10), (0, 0)]
    ]
    local = projection.project_geometry(Polygon(lonlat))
    min_x, min_y, max_x, max_y = local.bounds
    assert max_x - min_x == pytest.approx(20, abs=0.02)
    assert max_y - min_y == pytest.approx(10, abs=0.02)


def test_bounding_box_contains_center():
    bbox = bounding_box_from_center(-0.314861, -78.443472, 250)
    assert bbox.south < -0.314861 < bbox.north
    assert bbox.west < -78.443472 < bbox.east


import pytest


@pytest.mark.parametrize("latitude, epsg", [(86, 32661), (-85, 32761)])
def test_polar_regions_use_ups(latitude, epsg):
    assert LocalProjection.at(latitude, 20).epsg == epsg


def test_antimeridian_crossing_has_actionable_error():
    with pytest.raises(ValueError, match="antimeridiano"):
        bounding_box_from_center(0, 179.9999, 1000)

