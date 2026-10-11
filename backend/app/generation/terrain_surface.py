"""Ajuste de capas a los mismos triángulos que se exportan como relieve."""
from __future__ import annotations

import numpy as np
from shapely import constrained_delaunay_triangles, make_valid
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient
from shapely.strtree import STRtree


class TerrainSurface:
    def __init__(self, vertices: np.ndarray, indices: np.ndarray):
        self.faces = vertices[indices.reshape(-1, 3)].astype(np.float64)
        # Trabajar en el plano este/norte, manteniendo el eje Y vertical del GLB.
        self.xy = self.faces[:, :, [0, 2]].copy()
        self.xy[:, :, 1] *= -1
        self.polygons = [Polygon(points) for points in self.xy]
        self.index = STRtree(self.polygons)

    def drape(self, geometry: BaseGeometry, offset: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
        """Recorta por cada cara DEM e interpola en su plano (no bilinealmente).

        Cada triángulo resultante queda íntegramente sobre una cara del terreno.
        El recorte también impide prolongar vías fuera de la cobertura del DEM.
        """
        vertices = []
        if not geometry.is_valid:
            geometry = make_valid(geometry)
        for face_id in sorted(self.index.query(geometry, predicate="intersects")):
            intersection = geometry.intersection(self.polygons[face_id])
            for polygon in _polygon_parts(intersection):
                if polygon.area <= 1e-8:
                    continue
                xy = self.xy[face_id]
                # h = ax + by + c para la cara original.
                plane = np.linalg.solve(np.column_stack((xy, np.ones(3))), self.faces[face_id, :, 1])
                for triangle in constrained_delaunay_triangles(polygon).geoms:
                    points = np.asarray(orient(triangle, sign=1.0).exterior.coords)[:3, :2]
                    heights = points @ plane[:2] + plane[2] + offset
                    face = np.column_stack((points[:, 0], heights, -points[:, 1])).astype("<f4")
                    # Intersecciones minúsculas pueden colapsar al exportar float32.
                    if np.linalg.norm(np.cross(face[1] - face[0], face[2] - face[0])) > 1e-8:
                        vertices.extend(face)
        values = np.asarray(vertices, dtype="<f4").reshape(-1, 3)
        return values, np.arange(len(values), dtype="<u4")


def _polygon_parts(geometry: BaseGeometry):
    if isinstance(geometry, Polygon):
        yield geometry
    elif hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            yield from _polygon_parts(part)
