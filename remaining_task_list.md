# Remaining Task List (Detailed)

This file captures what is still missing compared to `evm_duckdb_platform_README.md`, how each item fits into the current architecture (Bronze/Silver/Gold), and why it improves the pipeline.

## Current baseline (already in repo)
- Bronze ingestion of blocks/transactions/logs to Parquet
- Canonical blocks table with a simple parent-hash check within each range
- ERC20 Transfer decoding to Silver
- Gold model for `erc20_transfers`
- dbt project + docs workflow for GitHub Pages

---

## Milestone 1: Ingestion (Bronze) - Reliability and Reorg Safety

### 1) Finality window enforcement
- Integration:
  - Add a finality-aware staging layer inside `onchain_platform/ingestion/worker.py`.
  - Track `latest_block` via `rpc_client.get_block_number()`.
  - Only mark ranges as canonical once `block_number <= latest_block - FINALITY_DEPTH`.
- Benefit:
  - Prevents finalized data from being overwritten by shallow reorgs.
  - Mirrors production-grade ingestion assumptions.

### 2) Full reorg handling (fork detection + invalidation + replay)
- Integration:
  - Extend `canonical_blocks` with lineage checks across ranges.
  - Add a reorg handler (new module: `onchain_platform/ingestion/reorg.py`) to:
    - detect fork point
    - mark affected blocks as non-canonical
    - re-ingest impacted ranges
  - Update Bronze Parquet partitions for affected blocks.
- Benefit:
  - Correct canonical chain history for analytics and downstream models.

### 3) Idempotent upsert/deduplication strategy
- Integration:
  - Add a merge/compact step for Parquet partitions.
  - Use unique keys defined in README (block_number, tx_hash, log_index) to remove duplicates.
  - Could be a maintenance job: `onchain_platform/ingestion/compactor.py`.
- Benefit:
  - Ensures re-runs do not create duplicates.
  - Makes pipeline safe for retries and backfills.

### 4) Incremental tailer
- Integration:
  - New CLI in `onchain_platform/ingestion/tailer.py`.
  - Uses `canonical_state.json` to resume from last ingested block.
  - Continually ingests recent blocks with finality rules.
- Benefit:
  - Keeps dataset fresh without manual range planning.

---

## Milestone 2: Decoding (Silver) - Protocol Coverage

### 5) ABI registry with versioning and start_block
- Integration:
  - Extend `onchain_platform/decoding/abi_registry.py` to load a registry file (e.g., `registry.json`).
  - Each protocol entry should include contract address, version, start_block, and ABI path.
- Benefit:
  - Supports protocol upgrades and contract migrations cleanly.

### 6) Uniswap v2 and v3 Swap decoders
- Integration:
  - Add decoders in `onchain_platform/decoding/decoders/uniswap_v2.py` and `uniswap_v3.py`.
  - Add ABIs under `onchain_platform/decoding/abis/`.
  - Update `decode_worker.py` to route by `--protocol`.
- Benefit:
  - Enables DEX analytics and richer Gold models.

### 7) Decoder unit tests
- Integration:
  - Add `tests/decoding/test_erc20.py` and `test_uniswap_*.py`.
  - Use known log fixtures and assert decoded outputs.
- Benefit:
  - Guarantees correctness for event decoding (critical for analytics).

---

## Milestone 3: Modeling (Gold) - Analytics Tables

### 8) `dex_trades` Gold model
- Integration:
  - Build a unified model in `dbt/models/gold/dex_trades.sql` from Uniswap v2/v3 swap events.
  - Add descriptions + tests in `dbt/models/schema.yml`.
- Benefit:
  - Canonical DEX trade table used by many analytics queries.

### 9) `wallet_activity_daily` model
- Integration:
  - Aggregate ERC20 transfers and swaps into daily activity.
  - Add model in `dbt/models/gold/wallet_activity_daily.sql`.
- Benefit:
  - Enables wallet activity dashboards and cohort analysis.

### 10) Stronger dbt tests
- Integration:
  - Add `unique` + `not_null` on primary keys.
  - Add `accepted_values` for chain_id.
  - Add basic freshness checks for incremental models.
- Benefit:
  - Enforces data integrity and prevents silent regressions.

---

## Milestone 4: Docs + Proof

### 11) Complete schema.yml coverage
- Integration:
  - Ensure every model/column has descriptions (especially new Gold models).
- Benefit:
  - High-quality dbt docs, strong interview signal.

### 12) Query pack completeness
- Integration:
  - Update `serving/queries/03_daily_dex_volume.sql` and `04_new_wallets_by_day.sql` to real queries.
- Benefit:
  - Demonstrates real analytical outputs against Gold tables.

### 13) Performance benchmarks
- Integration:
  - Add `docs/perf_results.md` with ingestion and dbt timings.
  - Include block range, hardware, and throughput.
- Benefit:
  - Shows awareness of scale and performance considerations.

---

## Recommended Priority Order
1) Finality + reorg handling
2) ABI registry upgrades + Uniswap decoders
3) Gold models + dbt tests
4) Query pack + perf docs

This order gives the best balance of correctness, coverage, and demonstration value for the platform.
