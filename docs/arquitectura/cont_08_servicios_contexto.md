# CONT-08 — Ejecución de servicios por División

CHG-314 · 2026-10-08 · Adaptación monetaria Local implementado Local, sobre el ciclo CHG-305. Working tree sobre HEAD 213f75c. Stock/entregas fueron completados después en [CHG-307](cont_08_stock_contexto.md); [fabricación CHG-315](cont_08_fabricacion_contexto.md) implementada Local.

## Comportamiento

Las órdenes de servicio de pedidos dimensionados ya permiten planear, asignar, iniciar, pausar, reanudar, capturar tiempos/costos/evidencia, solicitar aceptación, aceptar y cancelar según sus permisos/estados existentes. Sales obtiene el contexto fijo del pedido; no copia condiciones vigentes ni permite sustituir División/Sociedad. La aceptación actualiza partida, estado/costo/margen del pedido mediante el ciclo existente, conservando el contexto. Pedidos mixtos conservan sus productos pendientes: aceptar el servicio no libera ni surte productos.

Para avanzar o capturar, Admin valida permiso/alcance y Sociedad vigente; Production confirma disponibilidad del servicio; HR confirma trabajadores en la misma División (responsable actual y trabajador capturado cuando aplica). Cliente/asociación deben seguir activos en la transacción propia. Pausar/cancelar sólo requieren alcance y reglas de estado/motivo existentes: permiten detener trabajo aunque el recurso o cliente ya no esté activo. Lectura histórica conserva el contexto sin exigir elegibilidad nueva. Reintentos vuelven a comprobar autorización; no duplican tiempos/costos/evidencia.

Sales bloquea primero el pedido dimensionado y luego el servicio, antes de mutar. Cancelación del pedido en processing/needs_reconciliation/completed o estado cancelled rechaza nuevas operaciones. Este orden serializa aceptación/captura contra cancelación, sin prometer atomicidad distribuida con Admin/HR/Production. La cancelación del pedido mantiene el ciclo anterior y su historia. No hay FK ni escritura entre servicios.

No se activa Accounting ni analítica de Costing. Para entradas nuevas en servicios dimensionados, la tarifa horaria y el costo unitario se confirman en moneda base de la Sociedad. Cada entrada conserva moneda original, moneda documental, importe original Decimal6 y tasa explícita Decimal12; total_cost conserva el importe convertido en moneda del pedido a dos decimales. La tasa expresa unidades de moneda documental por una unidad de moneda original; cuando coinciden, vale uno. Cero es un costo válido. No se heredan tarifas ni se inventan tasas.

La migración0053 agrega metadatos nullable a tiempos y costos; no rellena ni reinterpreta históricos. Entradas antiguas conservan metadatos nulos y su importe previo. Una aceptación nueva de servicio dimensionado con entradas de moneda desconocida exige revisión, evitando mezclar importes no confirmados con convertidos. El flujo legacy sin División conserva el contrato anterior y rechaza metadatos monetarios que pretendan dimensionarlo por captura.

La autorización y el alcance se comprueban antes de un reintento; una respuesta ya completada conserva sus importes originales, aun si la configuración monetaria cambia después. La clave de una captura anterior sin los campos nuevos conserva su fingerprint. No hay conversión automática retroactiva. El downgrade bloquea si existen entradas o auditoría con confirmación monetaria; debe aplicarse forward-fix.

## Formularios y campos

| Campo | Origen/tarea | Contrato |
|---|---|---|
| División/Sociedad/moneda/condiciones | Pedido propietario, sólo lectura | No se envían como reemplazo; moneda visible en contexto e importes históricos. |
| Responsable/trabajador | Búsqueda autorizada en División vía Sales→HR | Selección explícita de ID; q/offset, 20 resultados por página; sin listado tenant-wide en documentos dimensionados. Sin datos personales sensibles. |
| Fechas de planeación | Captura del plan | Fechas requeridas, fin >= inicio según contrato existente. |
| Tiempo/tarifa | Captura operativa explícita | Minutos 1–1440 y tarifa no negativa Decimal18,6; cero válido, moneda base Sociedad confirmada para documentos dimensionados. |
| Cantidad/costo unitario | Captura operativa explícita | Cantidad positiva y costo no negativo Decimal18,6. Importe original a seis decimales; convertido a dos decimales, HALF_UP. |
| Moneda original/tasa | Sociedad derivada y confirmación explícita del usuario | cost_currency obligatoria para nuevas entradas dimensionadas; cost_exchange_rate positiva, hasta doce decimales, obligatoria si moneda distinta; uno si coincide. |
| Evidencia/motivo | Respaldo del trabajo/transición | Campos/estados/obligatoriedad existentes; no nueva regla fiscal o contable. |

Cada formulario conserva una clave por captura para reintentos, bloquea doble envío y conserva datos ante rechazo. Errores con ruta estructurada se vinculan a su control; falta de elegibilidad conjunta servicio/trabajador queda como error general sin inventar campo culpable. ES/EN y contenedor 320px se verifican con pruebas. Las búsquedas fallidas preservan la selección capturada y muestran error; guardar vuelve a validar en backend.

## APIs afectadas

Sales, prefijo /v1/sales:

| Método / ruta | Permiso | Cambio |
|---|---|---|
| GET /service-orders/{service_order_id}/eligible-workers | sales.service_order.assign o sales.service_order.time.create | Nuevo lookup q/offset, hasta 20 opciones y has_more; respuesta minimizada id/employee_number/full_name/position_name/division_ref_id. División derivada del documento, nunca capturada. |
| POST /service-orders/{service_order_id}/plan | sales.service_order.plan | Habilita dimensionados con validación de contexto; payload sin cambio; ServiceOrderRead añade currency y metadatos monetarios nullable de entradas. |
| POST /service-orders/{service_order_id}/time-entries | sales.service_order.time.create | Elegibilidad del trabajador y contexto. Request añade cost_currency/cost_exchange_rate; respuesta de entradas añade cost_currency/document_currency/cost_exchange_rate/original_total_cost, sin cambiar total_cost convertido. |
| POST /service-orders/{service_order_id}/cost-entries | sales.service_order.cost.create | Contexto y lock del pedido. Request añade cost_currency/cost_exchange_rate; respuesta de entradas añade los mismos metadatos monetarios que tiempos. |
| POST /service-orders/{service_order_id}/evidence | sales.service_order.evidence.create | Contexto y lock del pedido; payload sin cambio, respuesta aditiva ServiceOrderRead. |
| POST /service-orders/{service_order_id}/transitions/{action} | sales.service_order.{action} | Ciclo dimensionado; wait/cancel permiten detener sin elegibilidad activa. accept rechaza entradas sin moneda confirmada o con moneda documental incompatible. ServiceOrderRead añade currency del pedido y metadatos de entradas; payload de transición conservado. |
| HR GET /v1/hr/division-workers | hr.worker.read, consumidores previos o sales.service_order.plan/assign/start/resume/submit_acceptance/accept/time.create/cost.create/evidence.create | Amplía consumidores explícitos, manteniendo HR y consumidor Sales activos, tenant/scope. Request/response sin cambio. |
| Production GET /v1/production/division-product-services | production.product_service.read, consumidores previos o los mismos nueve permisos de servicio | Amplía consumidores explícitos para validación, sin dar acceso a mutaciones Production. Request/response sin cambio. |

GET /v1/sales/service-orders y GET /v1/sales/service-orders/{service_order_id} (sales.service_order.read) devuelven currency del pedido y los metadatos nullable de entradas. Las otras operaciones que retornan ServiceOrderRead comparten esa ampliación aditiva.

Consumidas sin modificación: Admin GET /v1/session/context; HR GET /v1/hr/workers/sales-eligible; Sales GET /v1/sales/orders, GET /v1/sales/orders/{order_id} y GET /v1/sales/reports/{report_code}/export. Alcance de lectura/CSV sigue CHG-304. En CHG-305 POST de surtimiento/entregas conservaban bloqueo; CHG-307 ya habilita stock dimensionado. APIs Inventory/Purchasing/Maintenance/Costing/Accounting sin cambios; no se emiten reservas ni solicitudes a Production.

## Evidencia histórica y validación vigente

CHG-314: ciclo Local0051→0053→0051→0053 aprobado en tenant demo, sin inferir datos (chg313-migrate.log). Sales PostgreSQL/API74 aprobadas sin omisiones (chg314-sales-postgres.log); navegador focal6/6 ES/EN con APIs interceptadas (chg314-browser.log). Verify aprobado:588 aprobadas175 omitidas1warning sin DB (chg314-verify.log); navegador transversal223 aprobadas con APIs interceptadas (chg314-browser-complete.log). Cinco fixtures históricos de tenants temporales no se ejecutaron: no se autorizó crear esos tenants.

### Evidencia CHG-305

Local exclusivo loopback PostgreSQL 5434/erclave_local, tenant ten_739ee59d765d5e14818674800d, Emulator 9099. Fixtures con rollback, sin escrituras de negocio permanentes. Fichas consultadas: Ventas, RH, Producción, Inventarios, Administración, Contabilidad negocio/técnica; guardianes Arquitectura/API, Datos/Custodio DB, Seguridad, Sinergia, Diseño/i18n, Manuales y QA. Skills feature/accounting/module-boundaries, ambientes, formularios/feedback, evidencia y manuales aplicadas; sin delegación.

Pruebas PostgreSQL/API focales 110 aprobadas sin omisiones: ciclo completo con costo real 8.00 y conservación del snapshot, repetición, rechazo de recursos/scope, autorización antes de replay, cancelación de padre en curso y lookup minimizado/autorizado. Navegador focal ES/EN 4/4 y transversal 197 aprobadas. Verify: validadores/compilación y 528 aprobadas/144 omitidas sin DB. Smoke Local read-only aprobado tras recargar Sales/HR/Production. Detalle de logs, ajuste del fixture inicial y advertencia de colores del shell en TRAZABILIDAD CHG-305. No certifica UAT. Fuente manual actualizada; Word conserva pendiente de runtime documents y revisión visual.

Continuación vigente: validar la adaptación monetaria CHG-314 y completar fabricación (CC-11/12), documentos Compras y otras brechas de [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). Stock/entrega ya implementados CHG-307. Legacy sin dimensiones sigue por tenant; no declarar separación completa ni promoción QA.
