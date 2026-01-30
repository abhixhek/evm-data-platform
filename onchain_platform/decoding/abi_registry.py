import json
import os
from typing import Any, Dict, List, Optional

from eth_utils import keccak


class ABIRegistry:
    def __init__(self, abi_dir: str) -> None:
        self.abi_dir = abi_dir
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._registry: Dict[str, List[Dict[str, Any]]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        registry_path = os.path.join(self.abi_dir, "registry.json")
        if not os.path.exists(registry_path):
            self._registry = {}
            return
        with open(registry_path, "r", encoding="utf-8") as handle:
            self._registry = json.load(handle)

    def load(self, name: str) -> Dict[str, Any]:
        filename = name if name.endswith(".json") else f"{name}.json"
        if filename in self._cache:
            return self._cache[filename]
        path = os.path.join(self.abi_dir, filename)
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self._cache[filename] = data
        return data

    @staticmethod
    def event_topic(event_abi: Dict[str, Any]) -> str:
        inputs = ",".join(item["type"] for item in event_abi.get("inputs", []))
        signature = f"{event_abi['name']}({inputs})"
        return "0x" + keccak(text=signature).hex()

    def get_event(
        self,
        protocol: str,
        event_name: str,
        block_number: Optional[int] = None,
        version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        abi = self._resolve_abi(protocol, block_number, version)
        for event in abi.get("events", []):
            if event.get("name") == event_name:
                return event
        return None

    def _resolve_abi(
        self, protocol: str, block_number: Optional[int], version: Optional[str]
    ) -> Dict[str, Any]:
        entries = self._registry.get(protocol)
        if not entries:
            return self.load(protocol)

        if version is not None:
            for entry in entries:
                if entry.get("version") == version:
                    return self.load(entry["abi"])

        if block_number is not None:
            candidates = [entry for entry in entries if entry.get("start_block", 0) <= block_number]
            if candidates:
                chosen = sorted(candidates, key=lambda x: x.get("start_block", 0))[-1]
                return self.load(chosen["abi"])

        chosen = sorted(entries, key=lambda x: x.get("start_block", 0))[-1]
        return self.load(chosen["abi"])
