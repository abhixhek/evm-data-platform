# EVM Data Platform – Blockchain DE Project

Welcome! This project started as a personal challenge:

> Could I build a mini data platform that ingests Ethereum blocks, decodes contract events and serves SQL on a datalake?

I wanted to simulate, at a smaller scale, the kind of systems Dune engineers work on. Along the way I picked up a lot about asynchronous programming, Parquet, dbt and the quirks of public blockchain data.

The code here provides a minimal, working implementation of:
- async JSON-RPC ingestion (blocks/tx/logs)
- reorg-aware canonical index
- ERC20 Transfer decoding
- dbt + DuckDB modeling scaffolding
- GitHub Pages workflow for dbt docs

## Why I built this?

I've always been fascinated by how Dune turns raw blockchain data into dashboards anyone can query. Dune’s job description talks about ingesting petabytes of data, letting third parties onboard new data sources and making SQL fast and accessible. To prepare for that role I decided to get my hands dirty and build a prototype. The result is this repository: a pipeline that fetches Ethereum blocks via JSON‑RPC, stores them in a Parquet lake, decodes ERC‑20 transfers and Uniswap swaps, defines dbt models and includes some example analytics queries.

## What’s inside

Here’s a quick overview of the main pieces you’ll find here:

- Range planning and ingestion – A planner script breaks a large block range into smaller chunks and writes them to a plan_ranges.jsonl file. The ingestion worker reads this plan, uses an asyncio.Semaphore to fire concurrent RPC requests, normalises the responses, handles chain re‑orgs by checking parent hashes and writes block, transaction and log data to a Parquet “bronze” lake.

- Canonical chain and finality – Keeping track of the canonical chain matters when you ingest data while the chain is still growing. The ingestion worker stores a simple canonical index and skips ranges that haven’t reached finality.

- Event decoding – To turn raw logs into something humans can understand, I load ABIs into an ABIRegistry and register decoders for common events like ERC‑20 transfers and Uniswap V2 swaps. The decode worker reads the bronze logs, decodes them and writes them into a “silver” Parquet lake.

- dbt models and tests – In the dbt/ folder you’ll find models that treat the bronze and silver Parquet files as tables, plus some “gold” models that aggregate the data (for example, erc20_transfers and dex_trades). Tests ensure uniqueness and column constraints.

- Sample SQL queries – The serving/queries directory contains some queries I wrote to explore the data: top tokens by transfer count, busiest wallets, daily DEX volume and so on. They run in DuckDB and show how you might use this platform for analytics.

- CI/CD and docs – A GitHub Actions workflow installs dependencies, bootstraps empty Parquet data for docs, runs dbt docs generate and publishes the result to GitHub Pages. I wanted to demonstrate some operational readiness.

## Architecture in plain words

I didn’t try to simulate a full‑blown distributed system, but the pieces here mirror what you’d see in a bigger platform. A planner breaks up the problem, ingestion workers fetch blocks concurrently and write them to a datalake, decoders enrich the data, dbt models create views, and SQL queries sit on top. If you wanted to scale this, you could run multiple workers, partition the chain across machines or push the data into a proper Delta or Iceberg lake.

```
+-------------+           +----------------------+           +--------------+
| Range Plan  |   -->     | Ingestion Worker     |   -->     | Bronze Lake   |
| (JSONL)     |           | (async RPC, Parquet) |           | (Parquet)     |
+-------------+           +----------+-----------+           +------+-------+
                               |                        |
                          +----v------+            +-----v------+
                          | Finality  |            | Canonical   |
                          | & Reorg   |            | Index       |
                          +-----------+            +-------------+
                               |                        |
+------------------+        +---v-----------+       +-----v------+
| ABIRegistry &    | <----- | Decode Worker |  -->  | Silver Lake |
| Decoders         |        +---------------+       +------------+
                               |
                          +----v------+
                          | dbt Models|
                          +-----------+
                               |
                          +----v------+       +-------------+
                          | Analytic  |  -->  | Serving SQL |
                          | Queries   |       | & Docs      |
                          +-----------+       +-------------+
```

- Planning – plan_ranges.py slices a block range into small intervals and writes a plan to disk. A CheckpointStore tracks progress, so you can resume ingestion if it stops midway.

- Ingestion – worker.py reads the plan, calls eth_getBlockByNumber, eth_getLogs etc., normalises the JSON and writes Parquet files in a bronze folder. It also maintains a canonical index to handle re‑orgs.

- Decoding – decode_worker.py reads the log Parquet files, loads the relevant ABIs and decodes events into structured rows.

- Modeling & testing – dbt models build curated tables on top of the raw data and run tests to catch errors.

- Serving & docs – DuckDB queries run against the curated tables, and dbt docs generate produces documentation for the models.

## Getting started

If you want to play with this yourself, here’s how:

- Set up your RPC endpoint – Copy .env.example to .env and set RPC_URL to a mainnet endpoint. Adjust FINALITY_DEPTH if you want to wait more or fewer blocks before considering a range final.

- Install dependencies – pip install -r requirements.txt then pip install dbt-core dbt-duckdb.

- Plan your ranges – For example:

```
python onchain_platform/planner/plan_ranges.py --start 0 --end 10000 --chunk 100
```

- Run the ingestion worker –

```
python onchain_platform/ingestion/worker.py
```

Use ingestion/tailer.py to tail new blocks.

- Decode events –

```
python onchain_platform/decoding/decode_worker.py --protocol erc20
python onchain_platform/decoding/decode_worker.py --protocol uniswap_v2
```

- Build models – In the dbt/ directory, run dbt run and then dbt test.

- Explore – Use DuckDB to run the queries in serving/queries, or write your own.

## Future work

I see plenty of ways this could grow:

- Add decoders for more contracts (e.g., ERC‑721 transfers, newer DEX protocols).

- Port the ingestion worker to a distributed framework like Ray or Apache Beam.

- Switch the storage layer to Delta or Iceberg for schema evolution and ACID.

- Build simple bots or agents that watch the chain and automatically update the ingestion plan.

I built this project to learn and to demonstrate the skills Dune is looking for. If you’re interested in how it works or want to discuss improvements, feel free to reach out!
