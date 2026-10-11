from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient

from app.generation.materials import procedural_textures
from app.generation.validation import validate_glb as validate_glb
from app.models.domain import Building, FusedDataset
from app.projection.service import LocalProjection

GENERATOR_VERSION = "City3D Engine 0.2"


def _polygons(geometry: BaseGeometry) -> Iterable[Polygon]:
    if isinstance(geometry, Polygon):
        yield geometry
    elif isinstance(geometry, MultiPolygon):
        yield from geometry.geoms


def _triangles_inside(polygon: Polygon) -> list[Polygon]:
    # Respeta todo el contorno y los patios, no solo el centro de cada triángulo.
    return [orient(triangle, sign=1.0)
            for triangle in constrained_delaunay_triangles(polygon).geoms]


def _mesh_for_extrusion(geometry: BaseGeometry, height: float) -> tuple[np.ndarray, np.ndarray]:
    vertices: list[tuple[float, float, float]] = []
    indices: list[int] = []

    def add_triangle(points: list[tuple[float, float, float]], reverse: bool = False) -> None:
        start = len(vertices)
        vertices.extend(points)
        order = [0, 2, 1] if reverse else [0, 1, 2]
        indices.extend(start + value for value in order)

    for polygon in _polygons(geometry):
        polygon = orient(polygon, sign=1.0)
        for triangle in _triangles_inside(polygon):
            coords = list(triangle.exterior.coords)[:3]
            add_triangle([(x, height, -y) for x, y in coords])
            add_triangle([(x, 0.0, -y) for x, y in coords], reverse=True)
        rings = [polygon.exterior, *polygon.interiors]
        for ring in rings:
            coords = list(ring.coords)
            for first, second in zip(coords, coords[1:]):
                start = len(vertices)
                vertices.extend(
                    [
                        (first[0], 0.0, -first[1]),
                        (second[0], 0.0, -second[1]),
                        (second[0], height, -second[1]),
                        (first[0], height, -first[1]),
                    ]
                )
                indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])
    return np.asarray(vertices, dtype="<f4"), np.asarray(indices, dtype="<u4")


def _mesh_for_surface(
    geometry: BaseGeometry, elevation: float = 0.02
) -> tuple[np.ndarray, np.ndarray]:
    vertices: list[tuple[float, float, float]] = []
    indices: list[int] = []
    for polygon in _polygons(geometry):
        for triangle in _triangles_inside(polygon):
            start = len(vertices)
            coords = list(triangle.exterior.coords)[:3]
            vertices.extend([(x, elevation, -y) for x, y in coords])
            indices.extend([start, start + 1, start + 2])
    return np.asarray(vertices, dtype="<f4"), np.asarray(indices, dtype="<u4")


@dataclass
class GlbBuilder:
    textured: bool = False
    binary: bytearray = field(default_factory=bytearray)
    buffer_views: list[dict[str, Any]] = field(default_factory=list)
    accessors: list[dict[str, Any]] = field(default_factory=list)
    meshes: list[dict[str, Any]] = field(default_factory=list)
    nodes: list[dict[str, Any]] = field(default_factory=list)

    def _align(self) -> None:
        while len(self.binary) % 4:
            self.binary.append(0)

    def _append(self, data: bytes, target: int | None = None) -> int:
        self._align()
        offset = len(self.binary)
        self.binary.extend(data)
        index = len(self.buffer_views)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        self.buffer_views.append(view)
        return index

    def _attribute(self, values: np.ndarray, kind: str) -> int:
        view = self._append(values.astype("<f4").tobytes(), 34962)
        index = len(self.accessors)
        self.accessors.append({
            "bufferView": view, "componentType": 5126, "count": len(values), "type": kind,
            "min": values.min(axis=0).astype(float).tolist(),
            "max": values.max(axis=0).astype(float).tolist(),
        })
        return index

    def add_mesh(
        self,
        name: str,
        vertices: np.ndarray,
        indices: np.ndarray,
        material: int,
        extras: dict[str, Any],
    ) -> None:
        if len(vertices) == 0 or len(indices) == 0:
            return
        triangles = vertices[indices.reshape(-1, 3)].astype(np.float64)
        crosses = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        lengths = np.linalg.norm(crosses, axis=1)
        if not np.isfinite(triangles).all() or np.any(lengths <= 1e-10):
            raise ValueError(f"Malla {name}: coordenadas inválidas o triángulos degenerados")
        normals = crosses / lengths[:, None]
        flat = triangles.reshape(-1, 3)
        vertex_normals = np.repeat(normals, 3, axis=0)
        # UV en metros: fachadas con proyección horizontal sobre su propia pared.
        horizontal = np.abs(vertex_normals[:, 1]) > 0.5
        u = flat[:, 0] * -vertex_normals[:, 2] + flat[:, 2] * vertex_normals[:, 0]
        uv = np.column_stack((np.where(horizontal, flat[:, 0], u),
                              np.where(horizontal, flat[:, 2], -flat[:, 1]))) / 3.0
        packed = np.column_stack((flat, vertex_normals, uv)).astype("<f4")
        unique, inverse = np.unique(packed, axis=0, return_inverse=True)
        attributes = {"POSITION": self._attribute(unique[:, :3], "VEC3"),
                      "NORMAL": self._attribute(unique[:, 3:6], "VEC3")}
        if self.textured:
            attributes["TEXCOORD_0"] = self._attribute(unique[:, 6:8], "VEC2")
        triangle_indices = inverse.reshape(-1, 3)
        roof_mask = np.abs(normals[:, 1]) > 0.5
        groups = [(material, triangle_indices)]
        if self.textured and material != 3:
            groups = [(material, triangle_indices[~roof_mask]), (4, triangle_indices[roof_mask])]
        primitives = []
        for material_id, group_indices in groups:
            if not len(group_indices):
                continue
            index_type = "<u2" if len(unique) < 65535 else "<u4"
            index_values = group_indices.ravel().astype(index_type)
            accessor = len(self.accessors)
            self.accessors.append({
                "bufferView": self._append(index_values.tobytes(), 34963),
                "componentType": 5123 if index_type == "<u2" else 5125,
                "count": len(index_values), "type": "SCALAR",
                "min": [int(index_values.min())], "max": [int(index_values.max())],
            })
            primitives.append({"attributes": attributes, "indices": accessor,
                               "material": material_id, "mode": 4})
        mesh_index = len(self.meshes)
        self.meshes.append(
            {
                "name": name,
                "primitives": primitives,
            }
        )
        self.nodes.append({"name": name, "mesh": mesh_index, "extras": extras})

    def write(self, path: Path, metadata: dict[str, Any]) -> None:
        materials = [
            {
                "name": "Altura explícita",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.12, 0.55, 0.95, 1], "roughnessFactor": 0.82
                },
                "doubleSided": True,
            },
            {
                "name": "Altura derivada",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.18, 0.78, 0.52, 1], "roughnessFactor": 0.82
                },
                "doubleSided": True,
            },
            {
                "name": "Altura desconocida",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.52, 0.57, 0.64, 1], "roughnessFactor": 0.9
                },
                "doubleSided": True,
            },
            {
                "name": "Carreteras",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.10, 0.12, 0.15, 1], "roughnessFactor": 0.95
                },
                "doubleSided": True,
            },
        ]
        images = []
        if self.textured:
            for name, png in procedural_textures():
                images.append({"name": name, "bufferView": self._append(png),
                               "mimeType": "image/png"})
            materials.append({"name": "Cubiertas planas", "pbrMetallicRoughness": {}})
        for index, mat in enumerate(materials):
            pbr = mat["pbrMetallicRoughness"]
            pbr["metallicFactor"] = 0.0
            mat["doubleSided"] = index == 3
            if self.textured:
                texture_index = 1 if index == 3 else 2 if index == 4 else 0
                pbr["baseColorTexture"] = {"index": texture_index}
                pbr["baseColorFactor"] = [1, 1, 1, 1]
                pbr["roughnessFactor"] = 0.9
                mat["extras"] = {"appearance": "procedural", "observed": False}
        document = {
            "asset": {"version": "2.0", "generator": GENERATOR_VERSION},
            "scene": 0,
            "scenes": [{
                "name": "City3D Scene",
                "nodes": list(range(len(self.nodes))),
                "extras": metadata,
            }],
            "nodes": self.nodes,
            "meshes": self.meshes,
            "materials": materials,
            "accessors": self.accessors,
            "bufferViews": self.buffer_views,
            "buffers": [{"byteLength": len(self.binary)}],
        }
        if images:
            document.update({"images": images,
                             "samplers": [{"magFilter": 9729, "minFilter": 9987,
                                           "wrapS": 10497, "wrapT": 10497}],
                             "textures": [{"sampler": 0, "source": i} for i in range(len(images))]})
        json_chunk = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        while len(json_chunk) % 4:
            json_chunk += b" "
        self._align()
        binary_chunk = bytes(self.binary)
        total_length = 12 + 8 + len(json_chunk) + 8 + len(binary_chunk)
        content = bytearray(struct.pack("<4sII", b"glTF", 2, total_length))
        content.extend(struct.pack("<I4s", len(json_chunk), b"JSON"))
        content.extend(json_chunk)
        content.extend(struct.pack("<I4s", len(binary_chunk), b"BIN\x00"))
        content.extend(binary_chunk)
        path.write_bytes(content)


def _material_for(building: Building) -> int:
    height_type = str(building.attributes["height_type"].value)
    return {"explicit": 0, "derived": 1, "estimated": 1, "unknown": 2}.get(height_type, 2)


def export_glb(
    fused: FusedDataset, projection: LocalProjection, path: Path, metadata: dict[str, Any]
) -> None:
    builder = GlbBuilder(textured=metadata.get("request", {}).get("material_style") == "procedural")
    for building in fused.buildings:
        geometry = projection.project_geometry(building.geometry)
        height = float(building.attributes["height"].value)
        vertices, indices = _mesh_for_extrusion(geometry, height)
        builder.add_mesh(
            building.id,
            vertices,
            indices,
            _material_for(building),
            {
                "feature_id": building.id,
                "geometry_source": building.provider,
                "height_m": height,
                "height_type": str(building.attributes["height_type"].value),
                "original_ids": building.original_ids,
            },
        )
    for road in fused.roads:
        line = projection.project_geometry(road.geometry)
        if not isinstance(line, LineString):
            continue
        surface = line.buffer(road.width_m / 2, cap_style="flat", join_style="mitre")
        vertices, indices = _mesh_for_surface(surface)
        builder.add_mesh(
            road.id,
            vertices,
            indices,
            3,
            {"feature_id": road.id, "source": road.provider, "road_class": road.road_class},
        )
    builder.write(path, metadata)

