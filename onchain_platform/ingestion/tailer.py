import argparse
import asyncio
import os
from typing import Optional

from onchain_platform.config import Config
from onchain_platform.ingestion.rpc_client import AsyncRPCClient
from onchain_platform.ingestion.writers.parquet_writer import ParquetWriter
from onchain_platform.planner.plan_ranges import build_ranges
from onchain_platform.ingestion.worker import fetch_range, load_state, save_state


def get_start_block(state_path: str, chain_id: int, explicit_start: Optional[int]) -> int:
    if explicit_start is not None:
        return explicit_start
    state = load_state(state_path)
    chain_state = state.get(str(chain_id), {})
    last_block = chain_state.get("last_block_number")
    if last_block is None:
        raise RuntimeError("No prior state found. Provide --start.")
    return last_block + 1


async def run_tailer(args: argparse.Namespace) -> None:
    config = Config.from_env()
    if not config.rpc_url:
        raise RuntimeError("RPC_URL is required for ingestion. Set it in .env.")

    writer = ParquetWriter(os.path.join(config.warehouse_dir, "lake", "bronze"))
    start_block = get_start_block(args.state, config.chain_id, args.start)

    async with AsyncRPCClient(config.rpc_url, max_concurrency=args.rpc_concurrency) as client:
        latest = await client.get_block_number()
        finalized_end = max(latest - config.finality_depth, 0)
        effective_end = finalized_end
        if args.end is not None:
            effective_end = min(args.end, finalized_end)
        if start_block > effective_end:
            print("No finalized blocks available to tail.")
            return

        ranges = build_ranges(start_block, effective_end, args.chunk)
        state = load_state(args.state)
        for start, end in ranges:
            blocks, txs, logs, canon = await fetch_range(
                client,
                config.chain_id,
                start,
                end,
                args.log_chunk,
            )
            range_tag = f"{start}_{end}.parquet"
            writer.write_rows("blocks_raw", blocks, filename=f"blocks_{range_tag}")
            writer.write_rows("transactions_raw", txs, filename=f"transactions_{range_tag}")
            writer.write_rows("logs_raw", logs, filename=f"logs_{range_tag}")
            writer.write_rows("canonical_blocks", canon, filename=f"canonical_{range_tag}")

            state[str(config.chain_id)] = {
                "last_block_number": end,
                "last_block_hash": canon[-1]["block_hash"] if canon else None,
                "updated_at": blocks[-1]["observed_at"] if blocks else None,
            }
            save_state(args.state, state)

    print("Tailer complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Incremental tailer for finalized blocks.")
    parser.add_argument("--state", default="warehouse/state/canonical_state.json")
    parser.add_argument("--start", type=int, help="Start block (overrides state).")
    parser.add_argument("--end", type=int, help="End block (for testing).")
    parser.add_argument("--chunk", type=int, default=20)
    parser.add_argument("--rpc-concurrency", type=int, default=6)
    parser.add_argument(
        "--log-chunk",
        type=int,
        default=100,
        help="Block range size per eth_getLogs call (lower for free-tier RPCs).",
    )
    args = parser.parse_args()

    asyncio.run(run_tailer(args))


if __name__ == "__main__":
    main()
