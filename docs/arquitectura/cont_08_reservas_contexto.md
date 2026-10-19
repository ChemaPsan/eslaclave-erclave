# CONT-08 — Contexto de reservas y salidas de Inventarios

**Política vigente:** existencias en moneda base de Sociedad; tipo explícito si pedido usa otra moneda, conservando ambos importes. [CHG-307](cont_08_stock_contexto.md) ya implementó este recorrido. CHG-309 extiende la política a todos los costos/tarifas; aplicación restante y mapeo real en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md).

**Estado posterior CHG-313:** [Producción manual por División](cont_08_produccion_contexto.md) ya conecta su intento durable a reservas y proyecta contexto/costo exacto para recepción de terminado (gates técnicos aprobados; aceptación integrada pendiente). Inventory verifica identidad/línea/asignación y autorización del productor antes de efectos o replay. Un fallo HTTP no equivale a contexto legacy.

**Evidencia histórica CHG-306:** stock/entrega habilitados en [CHG-307](cont_08_stock_contexto.md).

CHG-306 · Local · working tree sobre HEAD 213f75c. Preparación backend del recorrido de productos; no cierra el recorrido pedido → Producción/entrega ni la separación operativa completa.

## Contrato e invariantes

Inventory consulta una proyección mínima del pedido/línea en Sales; el emisor no puede capturar otra Sociedad/División en la reserva. Sales valida permiso, alcance, línea de producto, estado del pedido y ausencia de cancelación. Para pedidos dimensionados exige surtimiento en procesamiento o conciliación; el bloqueo histórico CHG-304 fue retirado para stock en CHG-307, con política monetaria implementada; [fabricación dimensionada CHG-315](cont_08_fabricacion_contexto.md) ya implementada Local.

Inventory valida su propio almacén y asignación activa del artículo bajo locks compartidos, compatibles con las escrituras de asignaciones. Almacén dimensionado exige contexto; contexto ajeno se rechaza. La reserva persiste organization_context (IDs de Sociedad/División y código/nombre congelados) y cada consumo lo copia al movimiento en la misma transacción. No FK ni escritura entre servicios, ni promesa de atomicidad distribuida.

API de reserva exige permiso correspondiente al origen, no cualquier permiso de otro productor. Crear/reintentar/consumir verifica alcance vigente; liberar permite detener con alcance histórico autorizado. Consumo nuevo revalida disponibilidad del artículo; idempotencia no duplica la salida. Movimiento ligado a reserva conserva la prohibición anterior de reversa manual: requiere devolución por su dueño.

Movimientos, kardex, saldos y sus exportaciones filtran almacenes dimensionados por alcance. El filtro SQL ocurre antes de paginar/agregar resultados devueltos. Almacenes antiguos sin División conservan compatibilidad por tenant; no se presume mapeo. Otros endpoints de Inventory y productores aún requieren su propio cierre.

## Persistencia y ambientes

Alembic `20261005_0048`, padre 0047: columna JSONB nullable organization_context en inventory.reservations y inventory.movements, constraints de pares/objeto y índices tenant + División. Sin backfill. Downgrade bloquea si existen snapshots; estrategia con historia: forward-fix. Upgrade/downgrade vacío/upgrade comprobados sólo en PostgreSQL loopback 5434/erclave_local, único tenant ten_739ee59d765d5e14818674800d. Fixtures con rollback, sin nuevos registros de negocio permanentes.

Nuevo destino ERCLAVE_SALES_SERVICE_URL para Inventory, loopback en Local; el consumidor rechaza destino no HTTPS público fuera de Local. QA requiere configurar esa dependencia al preparar candidato; no hubo conexión ni promoción.

## APIs afectadas

| Servicio / método / ruta | Permiso | Request / response |
|---|---|---|
| Sales GET /v1/sales/orders/{order_id}/execution-context | sales.order.fulfill | Nuevo line_id obligatorio; retorna order_id, order_line_id y organization_context nullable, sin cliente, precios ni condiciones. |
| Inventory POST /v1/inventory/reservation-requests | production.order.release / sales.order.fulfill / maintenance.material_request.create, correspondiente al source.type | Request sin nuevo campo; contexto de Sales derivado por HTTP. Respuesta añade organization_context nullable. |
| Inventory POST /v1/inventory/reservations/{reservation_id}/release | production.order.cancel / sales.order.cancel / maintenance.material_request.cancel / maintenance.order.cancel / inventory.movement.create según origen | Request igual; alcance antes de replay, respuesta de reserva añade contexto. |
| Inventory POST /v1/inventory/reservations/{reservation_id}/consume | inventory.movement.create | Request igual; scope y referencias, salida añade contexto inmutable. |
| Inventory GET /v1/inventory/movements | inventory.movement.read | Request igual; movimiento añade contexto nullable y listado filtrado. |
| Inventory GET /v1/inventory/kardex | inventory.kardex.read | Request igual; movimiento añade contexto nullable y listado filtrado. |
| Inventory GET /v1/inventory/balances | inventory.balance.read | Request/response iguales, filtro por alcance antes de paginación. |
| Inventory GET /v1/inventory/reports/{report_code}/export | permiso puntual del reporte | CSV conserva columnas; scope en almacenes/kardex/saldos/reservas críticas, maestros de artículos compartidos sin nuevo filtro. |

El schema compartido MovementRead agrega el campo nullable también donde ya se devuelve un movimiento (alta, reversa, recepción y devoluciones); esas rutas conservan sus reglas y no se declaran dimensionadas por esa adición. Admin GET /v1/session/context consumido sin cambio. Production, Purchasing, Maintenance, HR, Costing y Accounting no modificados en este corte. Lectura y nueva proyección no activan Contabilidad.

## Evidencia y bloqueos de cierre

153 pruebas focales PostgreSQL/API aprobadas sin omisiones: aislamiento, preservación del snapshot, copia al consumo, idempotencia, liberación con artículo inactivo, scopes antes de replay, CSV y proyección mínima protegida. Suite incluye regresión organizacional Sales/Purchasing/HR/Production e Inventory API. Evidencia final/gate en TRAZABILIDAD CHG-306. No certifica navegador, UAT ni QA.

Decisión confirmada: costo de existencias en moneda base de Sociedad y tipo explícito cuando el pedido use otra moneda, conservando importes. Persistencia y conversión de stock implementadas en CHG-307; no reinterpretar historia. Estructura y mapeo reales también solicitados; bloquean migración de datos, no todo desarrollo independiente.

Pendientes vigentes: reservas Maintenance/Purchasing, transferencias, sobrantes y recepciones Compras. Production manual y recepción PT incorporan contexto/moneda CHG-313; [fabricación comercial CHG-315](cont_08_fabricacion_contexto.md) tiene recorrido HTTP real aprobado. Aceptación transversal CC-20 pendiente. Stock/entrega, costo original-convertido y movimientos manuales/reversas ya están implementados CHG-307. Detalle por dueño y criterio de cierre: [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md).
