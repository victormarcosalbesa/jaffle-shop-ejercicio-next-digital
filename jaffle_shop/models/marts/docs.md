{% docs orders_status %}

Orders can be one of the following statuses:

| status         | description                                                                                                            |
|----------------|------------------------------------------------------------------------------------------------------------------------|
| placed         | The order has been placed but has not yet left the warehouse                                                           |
| shipped        | The order has ben shipped to the customer and is currently in transit                                                  |
| completed      | The order has been received by the customer                                                                            |
| return_pending | The customer has indicated that they would like to return the order, but it has not yet been received at the warehouse |
| returned       | The order has been returned by the customer and received at the warehouse                                              |


{% enddocs %}

{% docs payments_by_method_and_status %}

## Pagos por metodo y estado actual del pedido

Tabla de importes brutos registrados en Jaffle Shop. Cada fila representa una
combinacion existente de `payment_method` y `order_status`; la pareja es su clave
logica. No se generan filas para combinaciones sin pagos.

`total_amount` suma los pagos en AUD, convertidos previamente desde centimos en
`stg_payments`. Incluye credit_card, bank_transfer, coupon y gift_card.
Los datos no contienen confirmacion de cobro ni reembolsos: no se puede calcular
efectivo bancario liquidado ni ingresos netos. Los pedidos devueltos conservan
sus pagos registrados en el grupo returned; no se inventan devoluciones de dinero.

### Relaciones y dependencias

- `stg_customers.customer_id` (1) -> `stg_orders.customer_id` (N).
- `stg_orders.order_id` (1) -> `stg_payments.order_id` (N).
- `stg_orders` y `stg_payments` -> `payments_by_method_and_status`.

Se unen pagos y pedidos por order_id. La unicidad del identificador de pedido y
el test de relacion de cada pago evitan multiplicaciones y exclusiones silenciosas.
El estado es el estado actual del pedido, usado como aproximacion al estado del
envio disponible en el conjunto de datos; no es el estado historico al cobrar.
Los `ref()` hacen visibles las dependencias en el grafo de dbt.

### Actualizacion

Materializacion `table`: reconstruccion completa en cada ejecucion. Si un pedido
pasa de placed a shipped, el importe sale del primer grupo y entra en el segundo.
Tambien desaparecen los grupos que se quedan sin pagos. No se usa append ni un
filtro por order_date: no hay updated_at ni CDC para detectar cambios historicos.
El conjunto de datos es pequeno y recalcularlo entero mantiene la correccion.

La tabla se mantiene actualizada ejecutando periodicamente dbt. El script
`scripts/refresh_payments.ps1` permite repetir la carga de seeds y la construccion
con un intervalo configurable. La frescura depende de ese intervalo, del tiempo
de ejecucion y de la llegada de datos a los CSV; no es procesamiento en tiempo real.
En produccion se sustituirian los seeds por fuentes de ingestion y se programaria
el job con el SLA acordado. Para escalar a incremental haria falta detectar cambios
en pagos y pedidos y recalcular los grupos afectados, incluidos los que desaparecen.

{% enddocs %}
