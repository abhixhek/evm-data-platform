select chain_id, block_number, count(*) as cnt
from {{ ref('blocks_raw') }}
group by 1, 2
having count(*) > 1
