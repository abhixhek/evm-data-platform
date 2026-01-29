import asyncio
import json
from typing import Any, Dict, List, Optional

import aiohttp


class AsyncRPCClient:
    def __init__(self, rpc_url: str, max_concurrency: int = 8, timeout_seconds: int = 30) -> None:
        self.rpc_url = rpc_url
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_id = 0

    async def __aenter__(self) -> "AsyncRPCClient":
        self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session is not None:
            await self._session.close()

    async def _post(self, payload: Dict[str, Any]) -> Any:
        if self._session is None:
            raise RuntimeError("RPC client not started")
        async with self._semaphore:
            async with self._session.post(self.rpc_url, json=payload) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise RuntimeError(f"RPC error {resp.status}: {text}")
                data = json.loads(text)
                if "error" in data:
                    raise RuntimeError(f"RPC error: {data['error']}")
                return data.get("result")

    async def call(self, method: str, params: Optional[List[Any]] = None) -> Any:
        if params is None:
            params = []
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params}
        return await self._post(payload)

    async def get_block_by_number(self, block_number: int, full_transactions: bool = True) -> Any:
        return await self.call(
            "eth_getBlockByNumber",
            [hex(block_number), full_transactions],
        )

    async def get_block_number(self) -> int:
        result = await self.call("eth_blockNumber")
        return int(result, 16)

    async def get_logs(self, start_block: int, end_block: int) -> Any:
        params = [{"fromBlock": hex(start_block), "toBlock": hex(end_block)}]
        return await self.call("eth_getLogs", params)
