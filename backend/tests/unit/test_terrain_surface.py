import numpy as np
import pytest
from shapely.geometry import Polygon

from app.generation.terrain_surface import TerrainSurface


def test_draping_follows_triangle_planes_across_saddle_and_preserves_hole():
    # Celda no coplanar: una interpolación bilineal o un polígono sin cortar
    # atraviesa el relieve; ambos planos deben mantenerse en la exportación.
    vertices = np.array([[0, 0, 0], [10, 0, 0], [0, 0, -10], [10, 20, -10]], dtype="<f4")
    terrain = TerrainSurface(vertices, np.array([0, 1, 2, 1, 3, 2]))
    footprint = Polygon([(-2, -2), (12, -2), (12, 12), (-2, 12)],
                        holes=[[(3, 3), (7, 3), (7, 7), (3, 7)]])
    points, indices = terrain.drape(footprint, offset=0.06)
    area = 0.0
    for face in points[indices.reshape(-1, 3)]:
        xy = face[:, [0, 2]].astype(float)
        xy[:, 1] *= -1
        polygon = Polygon(xy)
        area += polygon.area
        assert footprint.covers(polygon)
        assert all(0 <= coordinate <= 10 for coordinate in xy.ravel())
        for weights in ([1/3, 1/3, 1/3], [0.2, 0.7, 0.1], [1, 0, 0]):
            point = np.array(weights) @ face
            expected = max(0, 2 * (point[0] - point[2] - 10)) + 0.06
            assert point[1] == pytest.approx(expected, abs=2e-6)
        normal = np.cross(face[1] - face[0], face[2] - face[0])
        assert normal[1] > 0
    assert area == pytest.approx(84)


def test_outside_terrain_is_not_extrapolated():
    terrain = TerrainSurface(np.array([[0, 0, 0], [1, 1, 0], [0, 2, -1]]),
                             np.array([0, 1, 2]))
    points, indices = terrain.drape(Polygon([(5, 5), (6, 5), (6, 6), (5, 6)]))
    assert points.shape == (0, 3)
    assert len(indices) == 0


def test_invalid_projected_polygon_is_repaired_before_intersection():
    terrain = TerrainSurface(np.array([[0, 0, 0], [10, 0, 0], [0, 0, -10], [10, 0, -10]]),
                             np.array([0, 1, 2, 1, 3, 2]))
    bowtie = Polygon([(1, 1), (9, 9), (1, 9), (9, 1)])
    assert not bowtie.is_valid
    points, indices = terrain.drape(bowtie)
    area = sum(Polygon(face[:, [0, 2]]).area for face in points[indices.reshape(-1, 3)])
    assert area == pytest.approx(32.0)
