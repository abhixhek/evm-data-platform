select
  chain_id,
  block_number,
  tx_hash,
  log_index,
  pair_address,
  sender,
  to_address,
  amount0_in,
  amount1_in,
  amount0_out,
  amount1_out
from {{ ref('event_uniswap_v2_swap') }}
