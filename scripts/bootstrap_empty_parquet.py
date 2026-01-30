import os
import pyarrow as pa
import pyarrow.parquet as pq


def write_empty(table_path: str, schema: pa.schema) -> None:
    os.makedirs(os.path.dirname(table_path), exist_ok=True)
    table = pa.Table.from_arrays([pa.array([], type=field.type) for field in schema], schema=schema)
    pq.write_table(table, table_path)


def main() -> None:
    base = os.path.join("warehouse", "lake")

    write_empty(
        os.path.join(base, "bronze", "blocks_raw", "part.parquet"),
        pa.schema(
            [
                ("chain_id", pa.int64()),
                ("block_number", pa.int64()),
                ("block_hash", pa.string()),
                ("parent_hash", pa.string()),
                ("timestamp", pa.int64()),
                ("miner", pa.string()),
                ("gas_used", pa.int64()),
                ("gas_limit", pa.int64()),
                ("base_fee_per_gas", pa.string()),
                ("tx_count", pa.int64()),
                ("observed_at", pa.string()),
            ]
        ),
    )

    write_empty(
        os.path.join(base, "bronze", "transactions_raw", "part.parquet"),
        pa.schema(
            [
                ("chain_id", pa.int64()),
                ("block_number", pa.int64()),
                ("block_hash", pa.string()),
                ("tx_hash", pa.string()),
                ("tx_index", pa.int64()),
                ("from_address", pa.string()),
                ("to_address", pa.string()),
                ("value", pa.string()),
                ("gas", pa.string()),
                ("gas_price", pa.string()),
                ("nonce", pa.int64()),
                ("input", pa.string()),
            ]
        ),
    )

    write_empty(
        os.path.join(base, "bronze", "logs_raw", "part.parquet"),
        pa.schema(
            [
                ("chain_id", pa.int64()),
                ("block_number", pa.int64()),
                ("block_hash", pa.string()),
                ("tx_hash", pa.string()),
                ("tx_index", pa.int64()),
                ("log_index", pa.int64()),
                ("address", pa.string()),
                ("data", pa.string()),
                ("topics", pa.list_(pa.string())),
                ("removed", pa.bool_()),
            ]
        ),
    )

    write_empty(
        os.path.join(base, "bronze", "canonical_blocks", "part.parquet"),
        pa.schema(
            [
                ("chain_id", pa.int64()),
                ("block_number", pa.int64()),
                ("block_hash", pa.string()),
                ("parent_hash", pa.string()),
                ("is_canonical", pa.bool_()),
                ("observed_at", pa.string()),
            ]
        ),
    )

    write_empty(
        os.path.join(base, "silver", "event_erc20_transfer", "part.parquet"),
        pa.schema(
            [
                ("chain_id", pa.int64()),
                ("block_number", pa.int64()),
                ("tx_hash", pa.string()),
                ("log_index", pa.int64()),
                ("contract_address", pa.string()),
                ("from_address", pa.string()),
                ("to_address", pa.string()),
                ("value_raw", pa.string()),
            ]
        ),
    )

    write_empty(
        os.path.join(base, "silver", "event_uniswap_v2_swap", "part.parquet"),
        pa.schema(
            [
                ("chain_id", pa.int64()),
                ("block_number", pa.int64()),
                ("tx_hash", pa.string()),
                ("log_index", pa.int64()),
                ("pair_address", pa.string()),
                ("sender", pa.string()),
                ("to_address", pa.string()),
                ("amount0_in", pa.string()),
                ("amount1_in", pa.string()),
                ("amount0_out", pa.string()),
                ("amount1_out", pa.string()),
            ]
        ),
    )


if __name__ == "__main__":
    main()
