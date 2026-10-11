"""Texturas decorativas deterministas; no representan fachadas observadas."""
from __future__ import annotations

import struct
import zlib

import numpy as np


def _png(pixels: np.ndarray) -> bytes:
    height, width, _ = pixels.shape

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    scanlines = b"".join(b"\x00" + row.tobytes() for row in pixels)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b"")
    )


def procedural_textures() -> list[tuple[str, bytes]]:
    """Cada mosaico equivale a 3 m; se comparte por todos los objetos."""
    rng = np.random.default_rng(42)
    facade = np.full((64, 64, 3), [212, 211, 203], dtype=np.uint8)
    facade[:3] = [155, 159, 160]
    facade[14:49, 15:49] = [110, 124, 129]
    facade[17:46, 18:46] = [55, 83, 105]
    facade[17:46, 31:33] = [151, 160, 163]
    facade[30:32, 18:46] = [151, 160, 163]
    asphalt = np.repeat(rng.integers(48, 66, (64, 64, 1), dtype=np.uint8), 3, axis=2)
    roof = np.repeat(rng.integers(123, 143, (64, 64, 1), dtype=np.uint8), 3, axis=2)
    roof[:2] = 92
    roof[:, :2] = 92
    return [("Fachada ilustrativa", _png(facade)), ("Asfalto", _png(asphalt)),
            ("Cubierta plana", _png(roof))]
