# Architecture

This project implements a Bronze/Silver/Gold lakehouse-style pipeline:

- Bronze: raw blocks, transactions, logs, and canonical index
- Silver: decoded events (e.g., ERC20 Transfer)
- Gold: curated analytics tables

Ingestion is async JSON-RPC with range sharding. Decoding uses ABI-based log parsing.
Modeling is done in dbt + DuckDB, with docs published via GitHub Pages.
