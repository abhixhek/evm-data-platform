import json
import os
from typing import Any, Dict, Optional

from eth_utils import keccak


class ABIRegistry:
    def __init__(self, abi_dir: str) -> None:
        self.abi_dir = abi_dir
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load(self, name: str) -> Dict[str, Any]:
        if name in self._cache:
            return self._cache[name]
        path = os.path.join(self.abi_dir, f"{name}.json")
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self._cache[name] = data
        return data

    @staticmethod
    def event_topic(event_abi: Dict[str, Any]) -> str:
        inputs = ",".join(item["type"] for item in event_abi.get("inputs", []))
        signature = f"{event_abi['name']}({inputs})"
        return "0x" + keccak(text=signature).hex()

    def get_event(self, name: str, event_name: str) -> Optional[Dict[str, Any]]:
        abi = self.load(name)
        for event in abi.get("events", []):
            if event.get("name") == event_name:
                return event
        return None
