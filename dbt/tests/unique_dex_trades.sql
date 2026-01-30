select chain_id, tx_hash, log_index, count(*) as cnt
from {{ ref('dex_trades') }}
group by 1, 2, 3
having count(*) > 1
