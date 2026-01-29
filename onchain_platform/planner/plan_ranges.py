import argparse
import json
import os
from typing import List, Tuple


def build_ranges(start_block: int, end_block: int, chunk_size: int) -> List[Tuple[int, int]]:
    ranges = []
    current = start_block
    while current <= end_block:
        upper = min(current + chunk_size - 1, end_block)
        ranges.append((current, upper))
        current = upper + 1
    return ranges


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan block ranges for ingestion.")
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--chunk", type=int, default=100)
    parser.add_argument("--out", default="warehouse/plans/ranges.jsonl")
    parser.add_argument("--chain-id", type=int, default=1)
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    ranges = build_ranges(args.start, args.end, args.chunk)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    mode = "a" if args.append else "w"
    with open(args.out, mode, encoding="utf-8") as handle:
        for start, end in ranges:
            handle.write(
                json.dumps(
                    {"chain_id": args.chain_id, "start_block": start, "end_block": end}
                )
                + "\n"
            )

    print(f"Planned {len(ranges)} ranges into {args.out}")


if __name__ == "__main__":
    main()
