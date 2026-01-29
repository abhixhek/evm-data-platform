import os

import pyarrow.dataset as ds


def count_rows(path: str) -> int:
    if not os.path.exists(path):
        return 0
    dataset = ds.dataset(path, format="parquet")
    return dataset.count_rows()


def main() -> None:
    bronze_logs = count_rows("warehouse/lake/bronze/logs_raw")
    silver_transfers = count_rows("warehouse/lake/silver/event_erc20_transfer")
    print(f"bronze logs: {bronze_logs}")
    print(f"silver erc20 transfers: {silver_transfers}")


if __name__ == "__main__":
    main()
