from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import triangulate

from app.models.domain import Building, FusedDataset
from app.projection.service import LocalProjection


def _polygons(geometry: BaseGeometry) -> Iterable[Polygon]:
    if isinstance(geometry, Polygon):
        yield geometry
    elif isinstance(geometry, MultiPolygon):
        yield from geometry.geoms


def _triangles_inside(polygon: Polygon) -> list[Polygon]:
    return [triangle for triangle in triangulate(polygon) if polygon.covers(triangle.representative_point())]


def _mesh_for_extrusion(geometry: BaseGeometry, height: float) -> tuple[np.ndarray, np.ndarray]:
    vertices: list[tuple[float, float, float]] = []
    indices: list[int] = []

    def add_triangle(points: list[tuple[float, float, float]], reverse: bool = False) -> None:
        start = len(vertices)
        vertices.extend(points)
        order = [0, 2, 1] if reverse else [0, 1, 2]
        indices.extend(start + value for value in order)

    for polygon in _polygons(geometry):
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


def _mesh_for_surface(geometry: BaseGeometry, elevation: float = 0.02) -> tuple[np.ndarray, np.ndarray]:
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
    binary: bytearray = field(default_factory=bytearray)
    buffer_views: list[dict[str, Any]] = field(default_factory=list)
    accessors: list[dict[str, Any]] = field(default_factory=list)
    meshes: list[dict[str, Any]] = field(default_factory=list)
    nodes: list[dict[str, Any]] = field(default_factory=list)

    def _align(self) -> None:
        while len(self.binary) % 4:
            self.binary.append(0)

    def _append(self, data: bytes, target: int) -> int:
        self._align()
        offset = len(self.binary)
        self.binary.extend(data)
        index = len(self.buffer_views)
        self.buffer_views.append(
            {"buffer": 0, "byteOffset": offset, "byteLength": len(data), "target": target}
        )
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
        position_view = self._append(vertices.tobytes(), 34962)
        index_view = self._append(indices.tobytes(), 34963)
        position_accessor = len(self.accessors)
        self.accessors.append(
            {
                "bufferView": position_view,
                "componentType": 5126,
                "count": len(vertices),
                "type": "VEC3",
                "min": vertices.min(axis=0).astype(float).tolist(),
                "max": vertices.max(axis=0).astype(float).tolist(),
            }
        )
        index_accessor = len(self.accessors)
        self.accessors.append(
            {
                "bufferView": index_view,
                "componentType": 5125,
                "count": len(indices),
                "type": "SCALAR",
                "min": [int(indices.min())],
                "max": [int(indices.max())],
            }
        )
        mesh_index = len(self.meshes)
        self.meshes.append(
            {
                "name": name,
                "primitives": [
                    {
                        "attributes": {"POSITION": position_accessor},
                        "indices": index_accessor,
                        "material": material,
                    }
                ],
            }
        )
        self.nodes.append({"name": name, "mesh": mesh_index, "extras": extras})

    def write(self, path: Path, metadata: dict[str, Any]) -> None:
        materials = [
            {
                "name": "Altura explícita",
                "pbrMetallicRoughness": {"baseColorFactor": [0.12, 0.55, 0.95, 1], "roughnessFactor": 0.82},
                "doubleSided": True,
            },
            {
                "name": "Altura derivada",
                "pbrMetallicRoughness": {"baseColorFactor": [0.18, 0.78, 0.52, 1], "roughnessFactor": 0.82},
                "doubleSided": True,
            },
            {
                "name": "Altura desconocida",
                "pbrMetallicRoughness": {"baseColorFactor": [0.52, 0.57, 0.64, 1], "roughnessFactor": 0.9},
                "doubleSided": True,
            },
            {
                "name": "Carreteras",
                "pbrMetallicRoughness": {"baseColorFactor": [0.10, 0.12, 0.15, 1], "roughnessFactor": 0.95},
                "doubleSided": True,
            },
        ]
        document = {
            "asset": {"version": "2.0", "generator": "City3D Engine 0.1"},
            "scene": 0,
            "scenes": [{"name": "City3D Scene", "nodes": list(range(len(self.nodes))), "extras": metadata}],
            "nodes": self.nodes,
            "meshes": self.meshes,
            "materials": materials,
            "accessors": self.accessors,
            "bufferViews": self.buffer_views,
            "buffers": [{"byteLength": len(self.binary)}],
        }
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
    builder = GlbBuilder()
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


def validate_glb(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("GLB demasiado pequeño")
    magic, version, declared_length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF" or version != 2 or declared_length != len(data):
        raise ValueError("Cabecera GLB inválida")
    json_length, json_type = struct.unpack("<I4s", data[12:20])
    if json_type != b"JSON":
        raise ValueError("Primer chunk GLB no es JSON")
    document = json.loads(data[20 : 20 + json_length].decode("utf-8"))
    if not document.get("scenes") or "asset" not in document:
        raise ValueError("Documento glTF incompleto")
    return {
        "bytes": len(data),
        "meshes": len(document.get("meshes", [])),
        "nodes": len(document.get("nodes", [])),
        "generator": document["asset"].get("generator"),
    }

