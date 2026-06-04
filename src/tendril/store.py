from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class StoreError(Exception):
    """Base error for local Tendril store failures."""


class DuplicateRecordError(StoreError):
    """Raised when a record write would overwrite an existing record."""


class RecordNotFoundError(StoreError):
    """Raised when a requested record does not exist."""


class Store:
    def __init__(self, root: Path | str = ".tendril") -> None:
        self.root = Path(root)

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for collection in [
            "artifacts",
            "proposals",
            "proofs",
            "decisions",
            "topics",
            "meta_changes",
        ]:
            (self.root / collection).mkdir(parents=True, exist_ok=True)
        graph_path = self.root / "graph.json"
        if not graph_path.exists():
            self.write_json(
                graph_path,
                {"nodes": [], "edges": [], "mutations": []},
                overwrite=False,
            )

    def record_path(self, collection: str, record_id: str) -> Path:
        return self.root / collection / f"{record_id}.json"

    def write_record(
        self,
        collection: str,
        record_id: str,
        data: dict[str, Any],
        *,
        overwrite: bool = False,
    ) -> Path:
        self.initialize()
        path = self.record_path(collection, record_id)
        self.write_json(path, data, overwrite=overwrite)
        return path

    def read_record(self, collection: str, record_id: str) -> dict[str, Any]:
        path = self.record_path(collection, record_id)
        if not path.exists():
            raise RecordNotFoundError(f"Unknown {collection.rstrip('s')}: {record_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def record_exists(self, collection: str, record_id: str) -> bool:
        return self.record_path(collection, record_id).exists()

    def read_graph(self) -> dict[str, Any]:
        self.initialize()
        return json.loads((self.root / "graph.json").read_text(encoding="utf-8"))

    def write_graph(self, graph: dict[str, Any]) -> None:
        self.initialize()
        self.write_json(self.root / "graph.json", graph, overwrite=True)

    def write_json(
        self,
        path: Path,
        data: dict[str, Any],
        *,
        overwrite: bool = False,
    ) -> None:
        if path.exists() and not overwrite:
            raise DuplicateRecordError(f"Record already exists: {path}")

        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, path)
