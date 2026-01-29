import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


@dataclass(frozen=True)
class Config:
    chain: str
    chain_id: int
    rpc_url: str
    finality_depth: int
    warehouse_dir: str

    @staticmethod
    def from_env() -> "Config":
        if load_dotenv is not None:
            load_dotenv()

        chain = os.getenv("CHAIN", "ethereum")
        chain_id = int(os.getenv("CHAIN_ID", "1"))
        rpc_url = os.getenv("RPC_URL", "")
        finality_depth = int(os.getenv("FINALITY_DEPTH", "64"))
        warehouse_dir = os.getenv("WAREHOUSE_DIR", "warehouse")

        return Config(
            chain=chain,
            chain_id=chain_id,
            rpc_url=rpc_url,
            finality_depth=finality_depth,
            warehouse_dir=warehouse_dir,
        )
