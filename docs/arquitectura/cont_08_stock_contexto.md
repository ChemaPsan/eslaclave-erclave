# CONT-08 — Surtido desde existencias y moneda de costo

CHG-307 · 2026-10-05 · Sólo Local, working tree sobre HEAD 213f75c. Continúa CHG-306; no representa cierre de toda la separación operativa ni aprobación para QA.

## Regla confirmada y alcance

El usuario confirmó costo de existencias en moneda base de Sociedad y tipo de cambio explícito cuando el pedido tenga otra moneda. Dirección: **1 unidad de moneda de costo = tipo capturado en moneda del pedido**. Misma moneda implica 1; no hay cotización automática, herencia de condiciones ni activación de Contabilidad/analítica.

Sales congela moneda y tipo al preparar surtido, deriva Sociedad de su División y valida producto elegible en Production. Inventory valida artículo/almacén propios y recibe contexto desde proyección autenticada de Sales. El almacén debe pertenecer a la misma División. El costo original viaja como decimal exacto, independiente de los campos float heredados. Entrega conserva original_actual_cost en moneda de Sociedad y actual_cost en moneda del pedido; conversión una sola vez, redondeo HALF_UP a dos decimales por línea conforme al modelo monetario existente. Se conserva el costo de servicios aceptados al agregar entregas de productos.

Queda habilitado: pedido dimensionado → reserva de stock → entrega → salida por Almacenes → costo original/convertido. Entradas/ajustes positivos manuales en almacenes dimensionados exigen costo unitario explícito en moneda de Sociedad; salidas/ajustes negativos usan costo de stock. Reversas manuales conservan contexto/costo y verifican alcance; movimientos ligados a reservas conservan devolución por dueño.

No se asigna moneda a historia antigua: cualquier movimiento previo del artículo/almacén sin moneda o con otra moneda bloquea nuevas operaciones con operational_cost_history_review_required. El mapeo real sigue pendiente de respuesta; no se inventó backfill. Fabricación, transferencias y demás productores dimensionados siguen bloqueados hasta su integración. Legacy sin División conserva comportamiento por tenant.

## Aislamiento, reintentos y concurrencia

Autorización y alcance preceden efectos y replay. Recurso elegible se revalida en su dueño. Entregas/listas/cola/CSV aplican alcance. Stock se reserva y consume idempotentemente; se conserva clave ante fallo recuperable. Fallo de dependencia deja conciliación y no autoriza duplicar efectos. No hay transacción distribuida ni escrituras entre schemas.

Locks de entrega siguen pedido → entrega, igual que cancelación y servicios. No se cancela una entrega cuya confirmación esté en procesamiento/conciliación. Confirmación pública mantiene el advisory lock existente. Tests PostgreSQL usan rollback y prueban finalización de repositorio, sin ejecutar commits del lock público dentro del fixture.

## Formularios

| Campo | Propósito, autoridad y captura |
|---|---|
| Almacén por línea | Existencias de la misma División. Búsqueda acotada/paginada en Inventory vía Sales; identidad visible, sin selección automática. |
| Cantidad | La pantalla muestra/envía la cantidad pendiente completa; API valida disponibilidad/reserva. No hay captura parcial en esta pantalla. |
| Tipo de cambio | Obligatorio sólo entre monedas distintas; decimal como texto para preservar precisión. Congelado al iniciar surtido. |
| Costo unitario manual | Obligatorio sólo entrada/ajuste positivo dimensionado; admite cero, no copia costo maestro. Salidas no permiten captura. |
| Moneda/División | Sólo lectura, derivadas del dueño; no capturables ni activadoras de Accounting. |

ES/EN, errores por código/campo, captura conservada, retry de consulta y submit, ARIA y contenedor 320 px. No se añaden campos contables al catálogo básico de centros.

## Datos y ambientes

Alembic `20261005_0049`, padre 0048: sales.orders.cost_currency y cost_exchange_rate (NUMERIC 24,12), par nullable condicionado a División, moneda ISO de tres letras y tasa positiva; sales.delivery_lines.original_actual_cost (NUMERIC 18,2) no negativo. organization_context conserva además cost_currency en JSONB de Inventory. Modelos, schema y OpenAPI alineados. Sin backfill ni FKs entre servicios. Downgrade bloqueado si hay importes nuevos; con historia usar forward-fix.

Upgrade/downgrade vacío/upgrade comprobados en loopback 5434/erclave_local, tenant exclusivo ten_739ee59d765d5e14818674800d. QA/Producción intactos. No confundir migración/código Local con despliegue QA.

## APIs afectadas

Todas las rutas siguientes son contratos modificados; headers de autenticación/tenant e idempotencia siguen obligatorios donde corresponden.

| Servicio / método / ruta | Permiso | Cambio |
|---|---|---|
| Sales GET /v1/sales/orders/{order_id}/stock-options | sales.order.fulfill | Nuevo lookup por line_id, q, offset; artículo/almacenes/moneda minimizados. |
| Sales GET /v1/sales/orders/{order_id}/execution-context | sales.order.fulfill | Contexto incluye cost_currency; exige preparación con moneda antes de reserva dimensionada. |
| Sales POST /v1/sales/orders/{order_id}/fulfillment | sales.order.fulfill | cost_exchange_rate opcional en schema, obligatorio entre monedas distintas; stock dimensionado habilitado. |
| Sales GET /v1/sales/orders; GET /v1/sales/orders/{order_id}; POST /v1/sales/orders; POST /v1/sales/orders/{order_id}/cancel | sales.order.read / sales.order.create / sales.order.cancel respectivamente | SalesOrderRead añade cost_currency/cost_exchange_rate nullable; cuerpos existentes sin cambio. |
| Sales GET /v1/sales/deliveries; GET /v1/sales/deliveries/{delivery_id} | sales.delivery.read | Alcance; respuesta añade División/Sociedad/monedas/tasa y costo original por línea. |
| Sales POST /v1/sales/deliveries | sales.delivery.create | Entrega dimensionada habilitada con surtido preparado; respuesta extendida. |
| Sales POST /v1/sales/deliveries/{delivery_id}/confirm | inventory.movement.create, con dependencia Sales sales.delivery.confirm o inventory.movement.create | Despacho, scope, costo original y conversión; request igual. |
| Sales POST /v1/sales/deliveries/{delivery_id}/cancel | sales.delivery.cancel | Scope y bloqueo de confirmación en curso; respuesta extendida. |
| Sales GET /v1/sales/warehouse-deliveries | inventory.movement.read | Alcance antes de paginar. |
| Sales GET /v1/sales/reports/{report_code}/export | permiso del reporte | Entregas filtradas por contexto del pedido; CSV mantiene columnas. |
| Inventory GET /v1/inventory/division-stock | inventory.balance.read o sales.order.fulfill | Nuevo lookup acotado con División/artículo/moneda/stock. |
| Inventory GET /v1/inventory/warehouses/{warehouse_id}/operation-context | inventory.movement.create | Nuevo contexto y moneda para captura manual; legacy retorna null. |
| Inventory POST /v1/inventory/movements | inventory.movement.create | unit_cost decimal, reglas según entrada/salida; respuesta añade original_unit_cost y moneda en contexto. |
| Inventory POST /v1/inventory/movements/{movement_id}/reverse | inventory.movement.reverse | Scope y conservación de contexto/costo original. |
| Inventory GET /v1/inventory/movements; GET /v1/inventory/kardex | inventory.movement.read / inventory.kardex.read respectivamente | original_unit_cost decimal nullable. |
| Inventory POST /v1/inventory/reservation-requests | permiso del source, para Sales sales.order.fulfill | Rechaza historia monetaria incompatible; original_unit_cost decimal en reserva. |
| Inventory POST /v1/inventory/reservations/{reservation_id}/release | permiso del origen, para Sales sales.order.cancel | Respuesta de reserva extendida; request igual. |
| Inventory POST /v1/inventory/reservations/{reservation_id}/consume | inventory.movement.create | Costo exacto y contexto conservados en salida; request igual. |
| Production GET /v1/production/division-product-services | permisos anteriores más sales.order.fulfill | Consulta de elegibilidad para surtido, sin nuevo write. |

Consumidas sin cambio: Admin GET /v1/session/context; Production GET /v1/production/product-services/{product_service_id}; Inventory GET /v1/inventory/items/{item_id}. APIs no tocadas: Admin, HR, Purchasing, Maintenance, Costing y Accounting; el helper compartido valida la forma de societies recibida en sesión.

## Evidencia y límites

Pruebas locales PostgreSQL/API con rollback en tenant autorizado: contexto cruzado, moneda obligatoria, precisión de seis decimales, reversa, historia sin moneda, permiso revocado, costo convertido y replay; confirmación/cancelación excluyentes. Navegador con APIs interceptadas: seis casos focales ES/EN. Ver logs chg307-tests.log, chg307-browser-final.log y chg307-migrate.log. PostgreSQL/API focal: 159 aprobadas sin omisiones (chg307-tests.log). Browser interceptado: 203 aprobadas (chg307-browser-regression.log), más 6 focales repetidas tras ajustar la superficie visual (chg307-browser-final.log). Pantalla principal Almacenes ES/EN: 2 aprobadas (chg307-main-browser.log). npm run verify aprobado: validadores/compilación y 532 passed, 149 skipped en suite general (los skips de integración no se presentan como aprobados). Migración Local up/down vacío/up aprobada; smoke autenticado 401/403/404 y legacy 200, sin registros sintéticos permanentes; APIs Sales/Inventory/Production reiniciadas Local. Captura visual revisada a 320 px. git diff --check sin errores.

No equivale a UAT integrado con datos reales: las autoridades externas de la prueba de Sales están simuladas y el navegador intercepta APIs. CHG-315 añade [fabricación/Production](cont_08_fabricacion_contexto.md) con HTTP real y costo original a seis decimales antes de conversión; faltan otros movimientos/transferencias/devoluciones, Purchasing, Maintenance, configuración/emisor/impresión/folios, mapeo/backfill y aceptación transversal. Fuentes/Word actualizados con paridad textual; revisión visual pendiente según REGISTRO.
