-- Contrato de estos datos: importes brutos, sin reembolsos negativos.
select 'payment' as record_type, cast(payment_id as varchar) as record_id, amount
from {{ ref('stg_payments') }}
where amount < 0

union all

select 'aggregate', payment_method || ':' || order_status, total_amount
from {{ ref('payments_by_method_and_status') }}
where total_amount < 0
