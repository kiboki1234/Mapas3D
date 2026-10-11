"""Validación estructural y geométrica del subconjunto GLB emitido por City3D."""
from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import numpy as np


def validate_glb(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 28:
        raise ValueError("GLB demasiado pequeño")
    magic, version, size = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or size != len(data):
        raise ValueError("Cabecera GLB inválida")
    json_size, json_kind = struct.unpack_from("<I4s", data, 12)
    end_json = 20 + json_size
    if json_kind != b"JSON" or json_size % 4 or end_json + 8 > len(data):
        raise ValueError("Chunk JSON inválido")
    document = json.loads(data[20:end_json])
    bin_size, bin_kind = struct.unpack_from("<I4s", data, end_json)
    binary = data[end_json + 8:]
    if bin_kind != b"BIN\x00" or bin_size != len(binary) or bin_size % 4:
        raise ValueError("Chunk binario inválido")
    if not document.get("scenes") or not document.get("meshes"):
        raise ValueError("El GLB no contiene una escena con mallas")
    if document.get("asset", {}).get("version") != "2.0":
        raise ValueError("Versión glTF inválida")
    buffers = document.get("buffers", [])
    if len(buffers) != 1 or buffers[0].get("uri") or buffers[0]["byteLength"] > bin_size:
        raise ValueError("Buffer GLB inválido")
    views = document["bufferViews"]
    for view in views:
        offset = view.get("byteOffset", 0)
        if (view.get("buffer") != 0 or offset < 0 or offset % 4
                or view["byteLength"] <= 0
                or offset + view["byteLength"] > buffers[0]["byteLength"]):
            raise ValueError("BufferView fuera de los límites del GLB")

    def read_accessor(index: int) -> np.ndarray:
        accessor = document["accessors"][index]
        view = views[accessor["bufferView"]]
        dtype = {5126: "<f4", 5125: "<u4", 5123: "<u2"}[accessor["componentType"]]
        columns = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[accessor["type"]]
        count = accessor["count"]
        local_offset = accessor.get("byteOffset", 0)
        required = count * columns * np.dtype(dtype).itemsize
        if count <= 0 or local_offset < 0 or local_offset + required > view["byteLength"]:
            raise ValueError("Accessor fuera de los límites del buffer")
        values = np.frombuffer(binary, dtype=dtype, count=count * columns,
                               offset=view.get("byteOffset", 0) + local_offset)
        values = values.reshape(count, columns)
        if not np.isfinite(values).all():
            raise ValueError("Coordenadas no finitas en el GLB")
        return values

    triangle_count = 0
    vertex_count = 0
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            if primitive.get("mode", 4) != 4:
                raise ValueError("La malla no contiene triángulos")
            attributes = primitive["attributes"]
            positions = read_accessor(attributes["POSITION"])
            normals = read_accessor(attributes["NORMAL"])
            indices = read_accessor(primitive["indices"]).ravel()
            if (
                indices.dtype.kind != "u"
                or len(indices) % 3
                or int(indices.max()) >= len(positions)
            ):
                raise ValueError("Índices de triángulos inválidos")
            if normals.shape != positions.shape or not np.allclose(
                np.linalg.norm(normals, axis=1), 1.0, atol=1e-5
            ):
                raise ValueError("Normales inválidas")
            triangles = positions[indices.reshape(-1, 3)].astype(np.float64)
            crosses = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
            if np.any(np.linalg.norm(crosses, axis=1) <= 1e-10):
                raise ValueError("Triángulos degenerados en el GLB")
            if np.any(np.sum(crosses * normals[indices[::3]], axis=1) <= 0):
                raise ValueError("Normales contrarias a la orientación de las caras")
            material = document["materials"][primitive["material"]]
            texture = material.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            if texture is not None:
                uv = read_accessor(attributes["TEXCOORD_0"])
                if uv.shape != (len(positions), 2):
                    raise ValueError("Coordenadas de textura inválidas")
                document["textures"][texture["index"]]
            triangle_count += len(indices) // 3
            vertex_count += len(positions)
    for image in document.get("images", []):
        view = views[image["bufferView"]]
        offset = view.get("byteOffset", 0)
        if (
            image.get("mimeType") != "image/png"
            or binary[offset:offset + 8] != b"\x89PNG\r\n\x1a\n"
        ):
            raise ValueError("Textura PNG inválida")
    return {"bytes": len(data), "meshes": len(document["meshes"]),
            "nodes": len(document["nodes"]), "triangles": triangle_count,
            "primitive_vertices": vertex_count, "textures": len(document.get("images", [])),
            "generator": document["asset"].get("generator")}
