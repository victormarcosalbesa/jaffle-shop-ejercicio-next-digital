{{ config(materialized='table') }}

with payments as (

    select * from {{ ref('stg_payments') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

)

select
    payments.payment_method,
    orders.status as order_status,
    sum(cast(payments.amount as decimal(18, 2))) as total_amount

from payments
inner join orders on payments.order_id = orders.order_id

group by
    payments.payment_method,
    orders.status
