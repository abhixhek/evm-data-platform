select
  chain_id,
  block_number,
  tx_hash,
  log_index,
  contract_address as token_address,
  from_address,
  to_address,
  value_raw
from {{ ref('event_erc20_transfer') }}
