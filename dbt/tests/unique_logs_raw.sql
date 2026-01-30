select chain_id, tx_hash, log_index, count(*) as cnt
from {{ ref('logs_raw') }}
group by 1, 2, 3
having count(*) > 1
