import argparse
import os
from typing import Any, Dict, List, Optional

import pyarrow.dataset as ds

from onchain_platform.config import Config
from onchain_platform.decoding.abi_registry import ABIRegistry
from onchain_platform.decoding.decoders.erc20 import decode_transfers
from onchain_platform.ingestion.writers.parquet_writer import ParquetWriter


def load_logs(path: str, start_block: Optional[int], end_block: Optional[int]) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    dataset = ds.dataset(path, format="parquet")
    table = dataset.to_table()
    rows = table.to_pylist()
    if start_block is None and end_block is None:
        return rows

    filtered = []
    for row in rows:
        block_number = row.get("block_number")
        if start_block is not None and block_number < start_block:
            continue
        if end_block is not None and block_number > end_block:
            continue
        filtered.append(row)
    return filtered


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode logs into typed events.")
    parser.add_argument("--protocol", default="erc20")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()

    config = Config.from_env()
    bronze_logs_path = os.path.join(config.warehouse_dir, "lake", "bronze", "logs_raw")
    silver_dir = os.path.join(config.warehouse_dir, "lake", "silver")

    logs = load_logs(bronze_logs_path, args.start, args.end)
    if not logs:
        print("No logs found to decode. Run ingestion first.")
        return
    registry = ABIRegistry(os.path.join(os.path.dirname(__file__), "abis"))

    writer = ParquetWriter(silver_dir)

    if args.protocol == "erc20":
        decoded = decode_transfers(registry, logs)
        writer.write_rows("event_erc20_transfer", decoded, filename="erc20_transfer.parquet")
    else:
        raise RuntimeError(f"Unsupported protocol: {args.protocol}")

    print("Decoding complete")


if __name__ == "__main__":
    main()
