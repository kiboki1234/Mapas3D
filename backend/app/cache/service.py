from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class FileCache:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(namespace: str, payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        return f"{namespace}-{hashlib.sha256(encoded).hexdigest()}"

    def path_for(self, key: str, suffix: str = ".json") -> Path:
        safe = "".join(character for character in key if character.isalnum() or character in "-_")
        return self.root / f"{safe}{suffix}"

    def read_json(self, key: str) -> Any | None:
        path = self.path_for(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def write_json(self, key: str, value: Any) -> Path:
        path = self.path_for(key)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
        return path

    def read_bytes(self, key: str, suffix: str) -> bytes | None:
        path = self.path_for(key, suffix)
        try:
            return path.read_bytes() if path.exists() else None
        except OSError:
            return None

    def write_bytes(self, key: str, value: bytes, suffix: str) -> Path:
        path = self.path_for(key, suffix)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(value)
        temporary.replace(path)
        return path

    def stats(self) -> dict[str, int]:
        files = [item for item in self.root.iterdir() if item.is_file()]
        return {"entries": len(files), "bytes": sum(item.stat().st_size for item in files)}

