# EVM Onchain Data Platform (Python + DuckDB + dbt)

A Python-first, reorg-safe **EVM data platform** that ingests public blockchain data, decodes logs into typed events, models curated analytics tables using **dbt + DuckDB**, and publishes **dbt Docs to GitHub Pages** as proof of work.

> Primary audience: Dune Data Platform / blockchain data pipeline interviews (showing ingestion + decoding + lakehouse modeling + documentation).

---

## Live Documentation (Proof of Work)

- dbt Docs (GitHub Pages): `https://<your-github-username>.github.io/<repo-name>/`
- Generated via:
  1) Column-level descriptions in `schema.yml`  
  2) `dbt docs generate` → `target/` (static site artifacts)  
  3) GitHub Actions deploy → GitHub Pages deployment

---

## Why this project exists (Dune alignment)

Dune’s Data Platform needs to:
- Ingest + process **petabytes** of public blockchain data
- Support third-party dataset ingestion
- Power **performant SQL** queries across datasets
- Own components like **ingestion** and **decoding**

This repo demonstrates those same fundamentals in a Python-first implementation:
- Distributed ingestion patterns (sharding, retries, backpressure)
- Blockchain specifics (reorg handling, canonical chain, idempotency)
- Lakehouse-style layers (Bronze/Silver/Gold)
- SQL transformations with dbt, running on DuckDB (fast local analytics engine)
- Enterprise-grade documentation: dbt docs + GitHub Pages

---

## What you get (outcomes)

- ✅ Reorg-safe ingestion of:
  - blocks
  - transactions
  - logs (event topics + data)
- ✅ Decoding layer:
  - ABI registry + versioning per contract/protocol
  - decoded event tables (typed columns)
- ✅ dbt models:
  - curated “Gold” tables like `erc20_transfers`, `dex_trades` (optional)
- ✅ DuckDB queryable warehouse:
  - `analytics.duckdb` file + Parquet datasets
- ✅ Documentation site:
  - `schema.yml` descriptions for **every column**
  - `dbt docs generate` → GitHub Pages deployment

---

## Tech Stack

### Runtime
- Python 3.10+ (recommended 3.11)
- asyncio + aiohttp (high-throughput JSON-RPC)
- DuckDB (local analytical query engine)

### Modeling + Docs
- dbt Core + dbt-duckdb adapter (DuckDB target)
- dbt docs site generated into `target/`

### Storage
- Parquet (canonical “lake” files)
- DuckDB database file (`analytics.duckdb`) for fast querying and dbt models

---

## System Architecture (High level)

**Bronze → Silver → Gold**

1) **Bronze (raw)**
- `blocks_raw`
- `transactions_raw`
- `logs_raw`

2) **Silver (decoded)**
- `event_erc20_transfer`
- `event_uniswap_v2_swap` / `event_uniswap_v3_swap` (optional)

3) **Gold (curated / analytics)**
- `erc20_transfers` (normalized transfers)
- `dex_trades` (unified swaps → trades)
- `wallet_activity_daily` (aggregates)

---

## Data Contracts (keys + invariants)

### Idempotent keys (critical)
- Blocks: `(chain_id, block_number)`
- Transactions: `(chain_id, tx_hash)`
- Logs: `(chain_id, tx_hash, log_index)`  
  - `log_index` is unique within a tx for emitted logs.

### Canonical chain / reorg safety
We maintain a canonical index:
- `canonical_blocks(chain_id, block_number, block_hash, parent_hash, is_canonical, observed_at)`

Rules:
- Newly ingested blocks are **provisional** until finality window N blocks.
- If `parent_hash` mismatch is detected, we:
  1) Find fork point
  2) Mark affected blocks as non-canonical
  3) Re-ingest + rewrite impacted partitions/tables

---

## Repo Structure (planned)

```
evm-duckdb-platform/
  README.md
  docs/
    architecture.md
    reorg_handling.md
    perf_results.md
  onchain_platform/
    planner/
      plan_ranges.py
      checkpoint_store.py
    ingestion/
      rpc_client.py
      worker.py
      writers/
        parquet_writer.py
    decoding/
      abi_registry.py
      decode_worker.py
      decoders/
        erc20.py
        uniswap_v2.py
    quality/
      reconciler.py
  warehouse/
    duckdb/
      analytics.duckdb              # generated
    lake/
      bronze/                       # parquet
      silver/                       # parquet
      gold/                         # parquet
  dbt/
    dbt_project.yml
    profiles.yml.example
    models/
      bronze/
      silver/
      gold/
    schema.yml
  serving/
    queries/
      01_top_tokens.sql
      02_top_wallets.sql
  .github/workflows/
    docs.yml
```

---

## Quickstart (Local)

### 1) Create environment
Use any env manager (venv/uv/poetry). Example using venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2) Install dbt + DuckDB adapter
```bash
pip install dbt-core dbt-duckdb
```

### 3) Configure RPC
Create `.env`:

```bash
CHAIN=ethereum
CHAIN_ID=1
RPC_URL=https://<your-rpc-provider>
FINALITY_DEPTH=64
```

### 4) Run ingestion (example)
Backfill a small range first:

```bash
python -m onchain_platform.planner.plan_ranges --start 19500000 --end 19500100
python -m onchain_platform.ingestion.worker --workers 8
```

Outputs:
- `warehouse/lake/bronze/.../*.parquet`
- `warehouse/duckdb/analytics.duckdb` (optional staging DB)

### 5) Run decoding
```bash
python -m onchain_platform.decoding.decode_worker --protocol erc20
```

Outputs:
- `warehouse/lake/silver/.../*.parquet`

### 6) Run dbt models (DuckDB)
From `dbt/`:

```bash
cd dbt
dbt debug
dbt seed
dbt run
dbt test
```

---

## DuckDB: Query the data (local)

```bash
duckdb warehouse/duckdb/analytics.duckdb
```

Example queries:

```sql
-- Top tokens by transfer count (after modeling)
select token_address, count(*) as transfers
from gold_erc20_transfers
group by 1
order by 2 desc
limit 20;
```

---

## Documentation: “Prove the work” (your stated goal)

### Goal
Generate a documentation site that demonstrates:
- the full lineage (sources → models)
- table + column meaning (human readable)
- test coverage (data quality)
- model graph + dependencies

### Task 1: Write descriptions for every column in `schema.yml`
**Rule:** every model must have:
- model description
- column description (no empty columns)

Example `schema.yml` pattern:

```yaml
version: 2

models:
  - name: silver_event_erc20_transfer
    description: "Decoded ERC20 Transfer events from logs (topic0 = Transfer)."
    columns:
      - name: chain_id
        description: "EVM chain id (e.g., 1 for Ethereum)."
      - name: block_number
        description: "Block height at which the event was emitted."
      - name: tx_hash
        description: "Transaction hash that emitted the log."
      - name: log_index
        description: "Log index within the transaction (unique per tx)."
      - name: contract_address
        description: "Token contract address that emitted Transfer."
      - name: from_address
        description: "Sender address from decoded event args."
      - name: to_address
        description: "Recipient address from decoded event args."
      - name: value_raw
        description: "Raw token amount (integer, before decimals normalization)."
```

### Task 2: Run dbt docs generate
From `dbt/`:

```bash
dbt docs generate
```

This generates static docs artifacts inside `dbt/target/` (including an `index.html`).

To preview locally:

```bash
dbt docs serve --port 8080
```

---

## Deploy dbt Docs to GitHub Pages (target/ → Pages)

### Option A (Recommended): GitHub Actions → GitHub Pages
This avoids committing `target/` to your main branch and uses GitHub Pages “Deploy from Actions”.

1) In GitHub repo:
   - Settings → Pages → Source: **GitHub Actions**

2) Add this workflow: `.github/workflows/docs.yml`

```yaml
name: Deploy dbt docs to GitHub Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install dbt-core dbt-duckdb

      - name: dbt deps
        working-directory: dbt
        run: dbt deps

      - name: dbt docs generate
        working-directory: dbt
        run: dbt docs generate

      - name: Configure Pages
        uses: actions/configure-pages@v5

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: dbt/target

  deploy:
    runs-on: ubuntu-latest
    needs: build
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Option B: Push `target/` to `gh-pages` branch
(Works, but less clean. Option A is preferred.)

---

## dbt Profile (DuckDB)

Create `dbt/profiles.yml` (or use env vars in CI):

```yaml
evm_duckdb_platform:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: ../warehouse/duckdb/analytics.duckdb
      threads: 8
```

Run:

```bash
cd dbt
dbt debug
```

---

## Data Quality & Tests (dbt)

Minimum recommended dbt tests:
- not_null on primary key columns
- unique on composite keys where applicable
- accepted_values for chain_id / protocol identifiers
- freshness checks on incremental models

Example (in `schema.yml`):

```yaml
      - name: tx_hash
        description: "Transaction hash."
        tests:
          - not_null
```

---

## Query Pack (Showcase)

Put queries under `serving/queries/` and reference them in docs:
- `01_top_tokens.sql`
- `02_top_wallets.sql`
- `03_daily_dex_volume.sql`
- `04_new_wallets_by_day.sql`

This makes it easy for reviewers to reproduce outcomes.

---

## Progress Tracker (use this as “where are we?”)

### Milestone 1: Ingestion (Bronze)
- [ ] Range planner + checkpoints
- [ ] Async ingestion worker (blocks/tx/logs)
- [ ] Idempotent writes (keys + upserts strategy)
- [ ] Finality window + reorg detection
- [ ] Backfill script + incremental tailer

### Milestone 2: Decoding (Silver)
- [ ] ABI registry (contract, version, start_block)
- [ ] ERC20 Transfer decoder
- [ ] (Optional) Uniswap v2/v3 swap decoder
- [ ] Unit tests for decoder correctness

### Milestone 3: Modeling (Gold) with dbt + DuckDB
- [ ] Bronze external tables / staging models
- [ ] Silver models for decoded events
- [ ] Gold curated tables + tests
- [ ] Query pack validated against Gold tables

### Milestone 4: Documentation + Proof
- [ ] `schema.yml` has descriptions for every column
- [ ] `dbt docs generate` produces complete lineage + docs
- [ ] GitHub Pages deployed from `dbt/target/` (Actions)
- [ ] Add “Perf results” page (simple benchmarks)

---

## Definition of Done (for interview readiness)

This repo is “done” when:
1) A reviewer can run a small backfill and see parquet outputs
2) Decoded ERC20 transfers exist and are queryable
3) dbt models run + tests pass
4) dbt docs are live on GitHub Pages and explain:
   - tables
   - columns
   - lineage
   - tests
5) There are 5–10 example SQL queries with screenshots or expected outputs

---

## Notes on Scale (how this maps to “petabytes” thinking)

Even though the demo runs locally, the design scales conceptually:
- block range sharding → horizontal ingestion workers
- parquet partitioning + compaction strategy
- immutable raw logs with canonical-chain reconciliation
- dbt models mirror warehouse patterns used at larger scale

---

## License
MIT (recommended for portfolio projects)

---
