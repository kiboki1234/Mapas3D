from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

from app.core.errors import ProviderUnavailableError
from app.datasets.store import validate_raster
from app.models.schemas import BoundingBox
from app.providers.raster_dem import copernicus_urls, read_dem_grid


def write_raster(path: Path, values: np.ndarray, bounds=(0, 0, 1, 1), crs="EPSG:4326"):
    with rasterio.open(path, "w", driver="GTiff", width=values.shape[1], height=values.shape[0],
                       count=1, crs=crs, dtype="float32", nodata=-9999,
                       transform=from_bounds(*bounds, values.shape[1], values.shape[0])) as dataset:
        dataset.write(values.astype("float32"), 1)


def test_grid_preserves_north_south_and_metre_units(tmp_path):
    path = tmp_path / "slope.tif"
    values = np.tile(np.linspace(200, 100, 100)[:, None], (1, 100))
    write_raster(path, values)
    terrain = read_dem_grid([path], BoundingBox(west=.1, east=.9, south=.1, north=.9), {}, sample_count=33)
    assert terrain.elevations_m[0].mean() < terrain.elevations_m[-1].mean()
    assert terrain.sample(.5, .5) == pytest.approx(150, abs=.1)
    assert terrain.sample(.8, .5) > terrain.sample(.2, .5)
    assert terrain.source["pixel_resolution_m"] > terrain.source["output_grid_spacing_m"] / 3


def test_nodata_is_not_silently_zero_filled(tmp_path):
    path = tmp_path / "missing.tif"
    values = np.full((100, 100), 150.)
    values[30:70, 30:70] = -9999
    write_raster(path, values)
    with pytest.raises(ProviderUnavailableError, match="sin datos"):
        read_dem_grid([path], BoundingBox(west=.1, east=.9, south=.1, north=.9), {})


def test_outside_extent_is_rejected(tmp_path):
    path = tmp_path / "outside.tif"
    write_raster(path, np.full((10, 10), 100.))
    with pytest.raises(ProviderUnavailableError):
        read_dem_grid([path], BoundingBox(west=2, east=3, south=2, north=3), {})


def test_feet_are_explicitly_converted(tmp_path):
    path = tmp_path / "feet.tif"
    write_raster(path, np.full((10, 10), 100.))
    terrain = read_dem_grid([path], BoundingBox(west=.1, east=.9, south=.1, north=.9), {}, .3048)
    assert terrain.reference_elevation_m == pytest.approx(30.48)


def test_projected_dem_is_reprojected(tmp_path):
    path = tmp_path / "utm.tif"
    write_raster(path, np.full((100, 100), 2500.), bounds=(780000, 9964000, 786000, 9969000), crs="EPSG:32717")
    terrain = read_dem_grid([path], BoundingBox(west=-78.445, east=-78.443, south=-.316, north=-.314), {})
    assert terrain.reference_elevation_m == pytest.approx(2500.)
    assert validate_raster(path)["crs"] == "EPSG:32717"


def test_copernicus_negative_coordinates_and_boundary():
    urls = copernicus_urls(BoundingBox(west=-78.45, east=-78.44, south=-.32, north=-.31))
    assert len(urls) == 1
    assert "S01_00_W079_00" in urls[0]
    assert len(copernicus_urls(BoundingBox(west=-.01, east=.01, south=-.01, north=.01))) == 4
