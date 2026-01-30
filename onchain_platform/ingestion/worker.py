import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from onchain_platform.config import Config
from onchain_platform.ingestion.rpc_client import AsyncRPCClient
from onchain_platform.ingestion.writers.parquet_writer import ParquetWriter
from onchain_platform.planner.checkpoint_store import CheckpointStore, RangeCheckpoint


def hex_to_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    return int(value, 16)


def hex_to_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return str(int(value, 16))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_plans(path: str) -> List[RangeCheckpoint]:
    items: List[RangeCheckpoint] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            data = json.loads(line)
            items.append(RangeCheckpoint(data["start_block"], data["end_block"]))
    return items


def load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_state(path: str, state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def normalize_block(chain_id: int, block: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "chain_id": chain_id,
        "block_number": hex_to_int(block.get("number")),
        "block_hash": block.get("hash"),
        "parent_hash": block.get("parentHash"),
        "timestamp": hex_to_int(block.get("timestamp")),
        "miner": block.get("miner"),
        "gas_used": hex_to_int(block.get("gasUsed")),
        "gas_limit": hex_to_int(block.get("gasLimit")),
        "base_fee_per_gas": hex_to_str(block.get("baseFeePerGas")),
        "tx_count": len(block.get("transactions", [])),
        "observed_at": now_iso(),
    }


def normalize_transactions(chain_id: int, block: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    block_number = hex_to_int(block.get("number"))
    block_hash = block.get("hash")
    for tx in block.get("transactions", []):
        yield {
            "chain_id": chain_id,
            "block_number": block_number,
            "block_hash": block_hash,
            "tx_hash": tx.get("hash"),
            "tx_index": hex_to_int(tx.get("transactionIndex")),
            "from_address": tx.get("from"),
            "to_address": tx.get("to"),
            "value": hex_to_str(tx.get("value")),
            "gas": hex_to_str(tx.get("gas")),
            "gas_price": hex_to_str(tx.get("gasPrice")),
            "nonce": hex_to_int(tx.get("nonce")),
            "input": tx.get("input"),
        }


def normalize_logs(chain_id: int, logs: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for log in logs:
        yield {
            "chain_id": chain_id,
            "block_number": hex_to_int(log.get("blockNumber")),
            "block_hash": log.get("blockHash"),
            "tx_hash": log.get("transactionHash"),
            "tx_index": hex_to_int(log.get("transactionIndex")),
            "log_index": hex_to_int(log.get("logIndex")),
            "address": log.get("address"),
            "data": log.get("data"),
            "topics": log.get("topics"),
            "removed": log.get("removed"),
        }


def canonical_row(chain_id: int, block: Dict[str, Any], is_canonical: bool) -> Dict[str, Any]:
    return {
        "chain_id": chain_id,
        "block_number": hex_to_int(block.get("number")),
        "block_hash": block.get("hash"),
        "parent_hash": block.get("parentHash"),
        "is_canonical": is_canonical,
        "observed_at": now_iso(),
    }


async def fetch_range(
    client: AsyncRPCClient,
    chain_id: int,
    start_block: int,
    end_block: int,
    log_chunk: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    blocks: List[Dict[str, Any]] = []
    txs: List[Dict[str, Any]] = []
    logs: List[Dict[str, Any]] = []
    canon: List[Dict[str, Any]] = []

    previous_hash: Optional[str] = None
    for block_number in range(start_block, end_block + 1):
        block = await client.get_block_by_number(block_number, full_transactions=True)
        if block is None:
            continue
        block_row = normalize_block(chain_id, block)
        blocks.append(block_row)
        txs.extend(list(normalize_transactions(chain_id, block)))

        if previous_hash is None:
            is_canonical = True
        else:
            is_canonical = block.get("parentHash") == previous_hash
        canon.append(canonical_row(chain_id, block, is_canonical))
        previous_hash = block.get("hash")

    if log_chunk <= 0:
        log_chunk = end_block - start_block + 1
    for chunk_start in range(start_block, end_block + 1, log_chunk):
        chunk_end = min(chunk_start + log_chunk - 1, end_block)
        logs_raw = await client.get_logs(chunk_start, chunk_end)
        logs.extend(list(normalize_logs(chain_id, logs_raw)))
    return blocks, txs, logs, canon


async def run_worker(args: argparse.Namespace) -> None:
    config = Config.from_env()
    if not config.rpc_url:
        raise RuntimeError("RPC_URL is required for ingestion. Set it in .env.")
    plans = read_plans(args.plan)
    checkpoint = CheckpointStore(args.checkpoints)
    state = load_state(args.state)

    writer = ParquetWriter(os.path.join(config.warehouse_dir, "lake", "bronze"))

    async with AsyncRPCClient(config.rpc_url, max_concurrency=args.rpc_concurrency) as client:
        latest_block = None
        finalized_end = None
        if not args.ignore_finality:
            latest_block = await client.get_block_number()
            finalized_end = max(latest_block - config.finality_depth, 0)
        for plan in plans:
            if checkpoint.is_done(plan):
                continue
            if finalized_end is not None and plan.end_block > finalized_end:
                print(
                    f"Skipping range {plan.start_block}-{plan.end_block} "
                    f"(finalized_end={finalized_end})."
                )
                continue
            blocks, txs, logs, canon = await fetch_range(
                client,
                config.chain_id,
                plan.start_block,
                plan.end_block,
                args.log_chunk,
            )

            range_tag = f"{plan.start_block}_{plan.end_block}.parquet"
            writer.write_rows("blocks_raw", blocks, filename=f"blocks_{range_tag}")
            writer.write_rows("transactions_raw", txs, filename=f"transactions_{range_tag}")
            writer.write_rows("logs_raw", logs, filename=f"logs_{range_tag}")
            writer.write_rows("canonical_blocks", canon, filename=f"canonical_{range_tag}")

            state[str(config.chain_id)] = {
                "last_block_number": plan.end_block,
                "last_block_hash": canon[-1]["block_hash"] if canon else None,
                "updated_at": now_iso(),
            }
            save_state(args.state, state)
            checkpoint.mark_done([plan])

    print("Ingestion complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Async ingestion worker.")
    parser.add_argument("--plan", default="warehouse/plans/ranges.jsonl")
    parser.add_argument("--checkpoints", default="warehouse/state/checkpoints.json")
    parser.add_argument("--state", default="warehouse/state/canonical_state.json")
    parser.add_argument("--rpc-concurrency", type=int, default=6)
    parser.add_argument(
        "--log-chunk",
        type=int,
        default=100,
        help="Block range size per eth_getLogs call (lower for free-tier RPCs).",
    )
    parser.add_argument(
        "--ignore-finality",
        action="store_true",
        help="Ingest ranges even if they are within the finality depth.",
    )
    args = parser.parse_args()

    asyncio.run(run_worker(args))


if __name__ == "__main__":
    main()
