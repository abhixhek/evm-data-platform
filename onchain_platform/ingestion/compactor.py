import argparse
import glob
import os
import shutil
from typing import Dict, List, Optional

import duckdb


PRIMARY_KEYS: Dict[str, List[str]] = {
    "blocks_raw": ["chain_id", "block_number"],
    "transactions_raw": ["chain_id", "tx_hash"],
    "logs_raw": ["chain_id", "tx_hash", "log_index"],
    "canonical_blocks": ["chain_id", "block_number", "block_hash"],
}


def build_dedupe_sql(table: str, keys: List[str], order_by: Optional[str]) -> str:
    partition = ", ".join(keys)
    order_clause = f"ORDER BY {order_by} DESC" if order_by else "ORDER BY (SELECT NULL)"
    return (
        f"select * from ("
        f"select *, row_number() over (partition by {partition} {order_clause}) as _rn "
        f"from {table}"
        f") where _rn = 1"
    )


def dedupe_table(source_path: str, output_path: str, keys: List[str]) -> None:
    if not glob.glob(source_path):
        raise FileNotFoundError(f"Missing source path: {source_path}")

    con = duckdb.connect()
    safe_source = source_path.replace("'", "''")
    con.execute(f"create or replace temp view src as select * from read_parquet('{safe_source}')")
    columns = [row[1] for row in con.execute("pragma table_info('src')").fetchall()]
    order_by = "observed_at" if "observed_at" in columns else None
    sql = build_dedupe_sql("src", keys, order_by)

    os.makedirs(output_path, exist_ok=True)
    safe_output = os.path.join(output_path, "part.parquet").replace("'", "''")
    con.execute(f"copy ({sql}) to '{safe_output}' (format parquet)")
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplicate parquet tables by primary keys.")
    parser.add_argument("--table", required=True, choices=PRIMARY_KEYS.keys())
    parser.add_argument("--warehouse-dir", default="warehouse")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    table = args.table
    keys = PRIMARY_KEYS[table]
    source = os.path.join(args.warehouse_dir, "lake", "bronze", table, "*.parquet")
    compacted_root = os.path.join(args.warehouse_dir, "lake", "bronze", f"{table}_compacted")

    dedupe_table(source, compacted_root, keys)

    if args.overwrite:
        original_dir = os.path.join(args.warehouse_dir, "lake", "bronze", table)
        backup_dir = os.path.join(args.warehouse_dir, "lake", "bronze", f"{table}_backup")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        if os.path.exists(original_dir):
            shutil.move(original_dir, backup_dir)
        shutil.move(compacted_root, original_dir)
        print(f"Replaced {table} with deduped parquet (backup at {backup_dir}).")
    else:
        print(f"Wrote deduped parquet to {compacted_root}.")


if __name__ == "__main__":
    main()
