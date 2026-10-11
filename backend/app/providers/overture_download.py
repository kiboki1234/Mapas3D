"""Consulta acotada del SDK oficial, aislada para poder terminar descargas bloqueadas."""
from __future__ import annotations

import contextlib
import json
import socket
import sys


def download(bbox: tuple[float, float, float, float]) -> dict:
    from overturemaps import core

    # urllib (catálogo STAC) no recibe los timeouts de Arrow. El valor solo
    # afecta a este proceso auxiliar, nunca a las otras peticiones del backend.
    socket.setdefaulttimeout(20)
    with contextlib.redirect_stdout(sys.stderr):
        release = core.get_latest_release()
        reader = core.record_batch_reader(
            "building", bbox=bbox, release=release, stac=True,
            connect_timeout=15, request_timeout=30,
        )
        if reader is None:
            raise RuntimeError("El SDK no devolvió un lector; no se guardará como cobertura vacía.")
        table = reader.read_all()
    wanted = [name for name in (
        "id", "geometry", "version", "sources", "names", "subtype", "class",
        "height", "num_floors", "roof_shape", "roof_height", "facade_material", "facade_color",
    ) if name in table.column_names]
    rows = [{key: value.hex() if isinstance(value, bytes) else value
             for key, value in row.items()} for row in table.select(wanted).to_pylist()]
    return {"release": release, "rows": rows}


if __name__ == "__main__":
    try:
        print(json.dumps(download(tuple(json.loads(sys.argv[1])))))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
