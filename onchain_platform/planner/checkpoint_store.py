import json
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class RangeCheckpoint:
    start_block: int
    end_block: int

    def key(self) -> str:
        return f"{self.start_block}-{self.end_block}"


class CheckpointStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._data: Dict[str, bool] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            self._data = {}
            return
        with open(self.path, "r", encoding="utf-8") as handle:
            self._data = json.load(handle)

    def _persist(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2)

    def mark_done(self, ranges: Iterable[RangeCheckpoint]) -> None:
        for item in ranges:
            self._data[item.key()] = True
        self._persist()

    def is_done(self, item: RangeCheckpoint) -> bool:
        return self._data.get(item.key(), False)

    def list_done(self) -> List[Tuple[int, int]]:
        done = []
        for key in self._data.keys():
            parts = key.split("-")
            if len(parts) != 2:
                continue
            done.append((int(parts[0]), int(parts[1])))
        return done
