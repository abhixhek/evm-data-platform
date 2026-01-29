import os
from typing import Any, Dict, Iterable, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq


class ParquetWriter:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir

    def write_rows(
        self,
        table_name: str,
        rows: Iterable[Dict[str, Any]],
        partition_cols: Optional[List[str]] = None,
        filename: Optional[str] = None,
    ) -> str:
        rows_list = list(rows)
        if not rows_list:
            return ""
        table = pa.Table.from_pylist(rows_list)
        table_dir = os.path.join(self.base_dir, table_name)
        os.makedirs(table_dir, exist_ok=True)

        if filename is None:
            filename = "part.parquet"
        output_path = os.path.join(table_dir, filename)

        if partition_cols:
            pq.write_to_dataset(table, root_path=table_dir, partition_cols=partition_cols)
            return table_dir

        pq.write_table(table, output_path)
        return output_path
