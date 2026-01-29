# Reorg Handling

Canonical chain tracking is recorded in `canonical_blocks` with `(block_number, block_hash, parent_hash)`.
A simple parent-hash check marks blocks as canonical or not within each ingested range.
For full reorg support at scale, add:
- fork point detection
- invalidation of non-canonical partitions
- replay of affected ranges
