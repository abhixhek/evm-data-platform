select chain_id, tx_hash, count(*) as cnt
from {{ ref('transactions_raw') }}
group by 1, 2
having count(*) > 1
