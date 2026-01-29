select from_address as wallet, count(*) as transfers
from erc20_transfers
group by 1
order by 2 desc
limit 20;
