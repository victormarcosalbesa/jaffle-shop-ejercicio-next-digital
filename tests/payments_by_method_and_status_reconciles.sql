-- No se debe perder ni duplicar dinero al unir y agregar los pagos.
with recorded as (
    select coalesce(sum(cast(amount as decimal(18, 2))), 0) as amount
    from {{ ref('stg_payments') }}
),
aggregated as (
    select coalesce(sum(total_amount), 0) as amount
    from {{ ref('payments_by_method_and_status') }}
)
select recorded.amount as recorded_amount, aggregated.amount as aggregated_amount
from recorded cross join aggregated
where recorded.amount <> aggregated.amount
