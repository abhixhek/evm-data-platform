with swaps as (
  select
    dt.chain_id,
    dt.tx_hash,
    dt.block_number,
    dt.amount0_out,
    dt.amount1_out,
    b.timestamp
  from dex_trades dt
  join blocks_raw b
    on dt.chain_id = b.chain_id
   and dt.block_number = b.block_number
),

daily as (
  select
    date_trunc('day', to_timestamp(timestamp)) as day,
    count(*) as trades,
    sum(
      coalesce(try_cast(amount0_out as double), 0)
      + coalesce(try_cast(amount1_out as double), 0)
    ) as volume_raw_out
  from swaps
  group by 1
)

select *
from daily
order by day desc
limit 30
