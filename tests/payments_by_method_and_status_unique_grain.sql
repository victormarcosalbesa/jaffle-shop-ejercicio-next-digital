-- Cada combinacion de metodo y estado debe aparecer una sola vez.
select payment_method, order_status
from {{ ref('payments_by_method_and_status') }}
group by payment_method, order_status
having count(*) > 1
