{% docs __overview__ %}
# EVM DuckDB Platform

This page is intentionally minimal. The goal is to show that the pipeline ran, not to overwhelm with walls of text.

## Project summary
- Ingests Ethereum blocks and logs via JSON-RPC into a Parquet lake (Bronze).
- Decodes ERC20 transfers and Uniswap v2 swaps into typed events (Silver).
- Builds curated analytics tables with dbt + DuckDB (Gold).
- Publishes dbt docs to GitHub Pages for proof of work.

## How to navigate
- Open any model to see lineage, columns, and tests.
- Use the search bar for quick access (try “erc20_transfers”).

Full project details live in the repository README.

## Pipeline Metrics (Sample Run)
**Range:** 19,490,000–19,498,999  
**Blocks:** 5,822  
**Transactions:** 1,088,063  
**Logs:** 2,208,560  
**ERC20 Transfers:** 1,015,012  
**Uniswap V2 Swaps:** 125,553  

**dbt tests passed:** 33  
**Docs generated:** OK  

{% enddocs %}
