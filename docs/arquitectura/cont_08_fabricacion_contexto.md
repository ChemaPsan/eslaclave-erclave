# CONT-08 · fabricación comercial por División (CC-12)

Corte CHG-315, Local 2026-10-08. Dueños: Sales, Production e Inventory; custodia de preparación contable y Arquitectura. Ver [control contable](../contexto/CONTROL_CONTABLE.md), [orden productiva](cont_08_produccion_contexto.md), [stock comercial](cont_08_stock_contexto.md) y [tarifas/capacidad](cont_08_tarifas_capacidad.md). Accounting sigue apagado; fabricación y entrega no crean pólizas ni documentos fiscales.

## Recorrido y autoridad

Sales conserva el plan de cumplimiento antes de pedir fabricación. Cada partida de producto puede solicitar producción con la División/Sociedad congeladas del pedido y el costo en moneda de Sociedad. La moneda documental diferente exige tasa explícita; no se deriva del tipo de cambio actual ni del maestro actualizado.

Production consulta la prueba autenticada de Sales antes de crear o convertir la solicitud. Producto, cantidad exacta, unidad y contexto deben coincidir con la partida. La bandeja permite seleccionar receta aprobada compatible y planificar responsables, etapas y días. El pedido y la partida se derivan en servidor; el navegador no cambia su identidad.

La conversión tiene enlace único durable solicitud→orden e intento de creación persistido antes de reservar Inventory. El mismo comando recupera la orden; otra clave no crea una segunda fabricación. Conversión y cancelación usan el mismo bloqueo de solicitud. Si el efecto quedó incierto, se recupera el intento original antes de cancelar o cambiar la clave. Inicio/reanudación revalidan la autoridad comercial y las asignaciones laborales vigentes.

Production dirige recursos/etapas/costo; Inventory confirma consumo y recepción de terminado. Sales consulta el estado productivo y la existencia realmente recibida. Sólo una orden completada con recepción suficiente, mismo artículo/unidad/División y almacén elegible permite conciliar. Una solicitud convertida o una orden terminada por sí solas no representan existencias entregables.

La conciliación persiste intención antes de reservar, recupera la reserva remota ante respuesta perdida y conserva el origen de fabricación en la partida. La entrega reutiliza el circuito de reserva/consumo de Sales. Cancelar un pedido con fabricación activa exige cancelar primero la orden productiva; no se ocultan consumos ni se declara cancelada una fabricación activa.

## Persistencia y datos existentes

- Alembic0054: enlace único a orden, intento y prueba de origen en solicitudes de Production. FK interna al dueño; ninguna FK entre servicios.
- Alembic0055: plan de cumplimiento y conciliación durable por partida en Sales, con clave, huella, prueba, estado y reserva.
- Alembic0056: costo original de entrega de Numeric(18,2) a Numeric(22,6), conservando el rango entero anterior. Primero se conserva el costo original de Inventory; luego se convierte y redondea el importe documental a dos decimales. No se recalcula historia ni se inventan decimales perdidos.

Columnas nuevas compatibles con historia nullable. Downgrade0054/55 rechaza historia que perdería vínculo/intención; downgrade0056 rechaza valores con decimales significativos después del segundo. Usar corrección hacia delante si existen estos datos. No ejecutar helpers históricos de migración tras reiniciar.

## APIs afectadas

Prefijos: Production `/v1/production`, Sales `/v1/sales`, Inventory `/v1/inventory`. Permisos exactos y schemas en los contratos [Production](../../contracts/api/production-service.openapi.yaml), [Sales](../../contracts/api/sales-service.openapi.yaml) e [Inventory](../../contracts/api/inventory-service.openapi.yaml).

| Servicio / método y ruta | Permiso y cambio contractual |
|---|---|
| Production POST /order-requests | sales.order.fulfill; valida prueba Sales, cantidad Decimal y contexto congelado. |
| Production GET /order-requests | production.order.read; búsqueda q, limit/offset, metadatos de paginación, enlace y cantidad original. |
| Production GET /order-requests/{request_id} | production.order.read o production.order.release o sales.order.read o sales.order.fulfill o sales.order.cancel; detalle con enlace y cantidad original. |
| Production GET /order-requests/{request_id}/production-status | production.order.read o production.order.release o sales.order.read o sales.order.fulfill o sales.order.cancel; estado, contexto y costo. |
| Production GET /order-requests/{request_id}/recipes | production.order.validate o production.order.release; catálogo compatible paginado q/limit/offset. |
| Production POST /order-requests/{request_id}/resource-validations | production.order.validate o production.order.release; validación por División y origen autenticado. |
| Production POST /order-requests/{request_id}/orders | production.order.release; conversión durable e idempotente. |
| Production POST /order-requests/{request_id}/cancel | sales.order.cancel; cancelación coordinada con fabricación. |
| Production GET /orders/{order_id} | production.order.read; cantidad original exacta adicional. |
| Production GET /finished-goods-candidates y GET /finished-goods-candidates/{order_id} | inventory.finished_goods_receipt.read o inventory.finished_goods_receipt.receive; proyección mínima de orden completada para recepción con cantidad/costo originales. |
| Sales GET /orders/{order_id}/production-context | sales.order.fulfill o production.order.validate o production.order.release o production.order.start o production.order.resume; query line_id obligatoria, prueba de partida e intención. |
| Sales GET /orders/{order_id}/production-status | sales.order.fulfill; query line_id obligatoria, estado y almacenes con elegibilidad resuelta por backend. |
| Sales POST /orders/{order_id}/production-reconciliations | sales.order.fulfill; partida/almacén, clave obligatoria, recuperación de reserva. |
| Sales POST /orders/{order_id}/fulfillment | sales.order.fulfill; habilita modo production dimensionado, conserva plan y tasa. |
| Sales POST /orders/{order_id}/cancel | sales.order.cancel; coordina cancelación antes de liberar y conserva recuperación. |
| Sales POST /deliveries/{delivery_id}/confirm | inventory.movement.create obligatorio para confirmar salida; sales.delivery.confirm solo recibe sales_warehouse_dispatch_required (403). Conserva precisión original de Inventory antes de conversión. |
| Inventory GET /finished-goods-receipts/{production_order_id}/stock-context | sales.order.fulfill; recepción real y disponibilidad por almacén con alcance. |
| Inventory POST /finished-goods-receipts | inventory.finished_goods_receipt.receive; cantidad exacta y costo/contexto probados de Production. |

Consumidos sin nuevo contrato: sesión/organización Admin; elegibilidad/capacidad RH; validación y compromisos productivos CHG-313; Inventory reservas/consumo/disponibilidad; Production avance de etapas/recursos/completado; Sales alta de entrega. Purchasing, Maintenance, Costing y Accounting no reciben cambios de API en este corte.

## Evidencia y límites

Pruebas focales PostgreSQL/API cubren autoridad, alcance, reintentos, conversión única, carreras, cancelación y costos. Navegador ES/EN verifica captura y transiciones con APIs interceptadas; esa evidencia se distingue del recorrido HTTP con servicios reales. El ejecutable [smoke_cc12_local.py](../../backend/scripts/smoke_cc12_local.py) usa fixtures sintéticos exclusivos del tenant Demo autorizado, APIs loopback, Accounting apagado y limpieza por IDs propios. La evidencia final y resultados exactos viven en [TRAZABILIDAD](../../TRAZABILIDAD.md).

CC-12 no cierra configuración de datos reales CC-19 ni aceptación transversal/QA CC-20. CC-14 conserva pendientes de otros productores, transferencias y retornos; no se reabre el recorrido de fabricación ya adaptado.
