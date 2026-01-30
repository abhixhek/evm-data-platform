with transfers as (
  select
    et.from_address as wallet,
    b.timestamp
  from erc20_transfers et
  join blocks_raw b
    on et.chain_id = b.chain_id
   and et.block_number = b.block_number
),

first_seen as (
  select wallet, min(timestamp) as first_ts
  from transfers
  group by 1
)

select
  date_trunc('day', to_timestamp(first_ts)) as day,
  count(*) as new_wallets
from first_seen
group by 1
order by day desc
limit 30
