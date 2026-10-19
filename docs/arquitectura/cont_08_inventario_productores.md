# CC-14 · Productores, transferencias y sobrantes

## Estado y límites · CHG-317 · 2026-10-12

Implementación Local sobre `20261012_0057`, con Accounting apagado. [Estado](../contexto/ESTADO_ACTUAL.md), [control](../contexto/CONTROL_CONTABLE.md) y [pendientes](../contexto/PENDIENTES.md) conservan la autoridad por ambiente. Se preservan Sales/Production CC-09/11/12/13. [Compras CC-15 CHG-319](cont_08_compras_contexto.md) implementado Local; [Mantenimiento CC-16 CHG-320](cont_08_mantenimiento_contexto.md) implementado Local para órdenes, técnicos y tiempos; CC-19/20 mantienen datos reales y aceptación transversal. No se promovió a QA.

## Contrato funcional

- Inventory es dueño de existencias, reservas, movimientos, transferencias y sobrantes. Purchasing/Maintenance guardan la intención durable antes de llamar a Inventory; éste consulta una prueba de origen autenticada, nunca acepta la División/costo por confianza en el payload.
- Transferencias simples admiten almacenes de Divisiones de la misma Sociedad y moneda, con artículo asignado activo en ambos. Congelan origen y destino. Despacho no es recepción; recepción parcial, solicitud de retorno y retorno usan las cantidades pendientes y el costo original exacto. El operador debe tener alcance sobre ambos extremos. No hay transferencia simple entre Sociedades.
- Sobrantes conservan contexto, cantidad y costo del movimiento emitido. Maintenance confirma coincidencia antes de entrada física. Una recepción pendiente de conciliación reintenta sólo la confirmación del dueño; no duplica stock. Cancelación y replay vuelven a verificar alcance.
- Maintenance deriva contexto del almacén autorizado, contrastándolo con máquina/orden productiva si existe. La solicitud congela ese contexto; proof vincula orden, partida, artículo, almacén, unidad, cantidad y estado. Reserva, salida, liberación y retorno lo conservan. Una reserva Maintenance liberada/vencida no se reactiva ni se recostea mediante reintento.
- Purchasing deriva División/Sociedad del almacén receptor y valida proveedor activo/asignado. Precio y moneda de OC se congelan en la línea de recepción con tipo explícito documental→Sociedad y costo convertido. Misma moneda usa 1; otra moneda exige tasa positiva, hasta seis decimales. No se mezclan monedas de costo distintas en una recepción. El precio OC mantiene su precisión vigente de dos decimales, sin reconstruir precisión histórica; costo convertido conserva seis con HALF_UP. Ejemplo: 4.12 USD × 20.123456 = 82.908639 MXN. No se actualiza automáticamente el costo base del artículo.
- Origen físico de compra: `purchase_receipt`, ID de recepción y de su partida. Inventory comprueba cantidad, unidad, almacén, artículo, fecha, costo, tasa y clave estable contra Purchasing. Índice único tenant/recepción/partida y lock transaccional impiden efectos duplicados; callbacks de prueba no toman el lock de confirmación del productor.
- Historia sin contexto/moneda no se asigna automáticamente. Recepción física Purchasing legacy sin snapshot exige revisión. Transferencia/sobrante legacy no adquiere contexto por dimensionar después el almacén; una nueva escritura incompatible queda bloqueada. No hay backfill.

## Captura y presentación

| Campo | Tarea y autoridad | Alta/reintento/lectura |
|---|---|---|
| Almacén destino de recepción | Define División física; Inventory/Admin validan. | Usa ID estable existente. No se agrega captura redundante de Sociedad/División. |
| `cost_exchange_rate` | Convierte precio documental a moneda Sociedad. | UI ES/EN muestra monedas con datos de sesión/almacén; misma moneda 1 de sólo lectura, otra moneda requiere tasa. API vuelve a validar; errores estructurados conservan captura. |
| Fecha/clave de recepción | Identidad de un intento, no una captura adicional. | El formulario congela fecha y clave mientras la captura no cambia; editar crea otro intento. |
| Contextos y costo | Evidencia del origen, no campos editables de Inventory. | Snapshots persistidos y devueltos en proyecciones; nunca se recalculan al leer o reintentar. |

## APIs afectadas

Todos los endpoints exigen tenant y autenticación existentes; permisos puntuales y alcance se revalidan en backend. No se amplían permisos para sustituir configuración de roles.

| Servicio | Método/ruta | Permiso y delta |
|---|---|---|
| Purchasing | POST `/v1/purchasing/receipts` | `purchasing.receipt.create`; `cost_exchange_rate` opcional en schema/condicional por moneda, snapshot por línea, replay autorizado. |
| Purchasing | GET `/v1/purchasing/receipts`, GET `/v1/purchasing/warehouse-receipts`, POST `/v1/purchasing/receipts/{id}/reconcile` | Permisos existentes de lectura y confirmación física; scope de todos los contextos de recepción antes de paginar, confirmar o devolver replay. |
| Purchasing | GET `/v1/purchasing/receipts/{receipt_id}/lines/{line_id}/inventory-proof` | `inventory.movement.create`; nuevo proof mínimo de intención/costo persistidos, tenant/alcance/estado. |
| Purchasing | GET `/v1/purchasing/reports/{report_code}/export` | `purchasing.receipt.read` para `receipts`; exportación CSV filtra el alcance de la recepción completa antes de devolver filas. Otros reportes conservan sus permisos y contratos. |
| Inventory | POST `/v1/inventory/purchase-receipts` | `inventory.movement.create`; source `purchase_receipt`, proof obligatorio, costo moneda Sociedad, efecto único. |
| Inventory | POST `/v1/inventory/movements` | `inventory.movement.create`; entrada manual y transferencia misma Sociedad con contextos originales, Decimal6, sin suplantar origen de otro módulo. |
| Inventory | GET `/v1/inventory/warehouses` y GET `/v1/inventory/warehouses/{warehouse_id}` | Permisos existentes de catálogo/consumidores; respuesta añade `division_ref_id`, necesaria para derivar contexto. |
| Inventory | GET `/v1/inventory/transfers` | `inventory.movement.read`; filtra ambos extremos antes de paginar, respuesta origen/destino. |
| Inventory | POST `/v1/inventory/transfers/{transfer_id}/{action}` | `inventory.movement.create`; acciones receive/request-return/receive-return, scope y contexto/costo congelados. |
| Inventory | GET/POST `/v1/inventory/material-returns`, GET `/v1/inventory/material-returns/{return_id}`, POST `/v1/inventory/material-returns/{return_id}/receive`, POST `/v1/inventory/material-returns/{return_id}/cancel` | Lectura `inventory.movement.read/create`; solicitud `production.order.update` o `maintenance.material_request.create` según origen, o `inventory.movement.create`; recepción/cancelación `inventory.movement.create`. Contexto/moneda, filtro y proof antes del efecto; recuperación existente conservada. |
| Inventory | POST `/v1/inventory/reservation-requests` | Permiso por origen: `production.order.release`, `sales.order.fulfill`, `maintenance.material_request.create`. Nuevo proof Maintenance; no confianza en contexto enviado. |
| Inventory | POST `/v1/inventory/reservations/{reservation_id}/release` y `/consume` | Permisos existentes por origen/cancelación y `inventory.movement.create` para consumo. Scope del snapshot; Maintenance terminal no se reactiva. |
| Maintenance | GET `/v1/maintenance/orders/{id}/inventory-context` | Nuevo proof; any `maintenance.material_request.create/reconcile/cancel`, `maintenance.order.cancel`, `inventory.movement.create`; `line_id` requerido. |
| Maintenance | POST `/v1/maintenance/orders/{id}/material-requests`; POST `/v1/maintenance/material-requests/{id}/issue`, `/reject`, `/cancel`, `/reconcile` | Permisos existentes create / Inventory movement.create / cancel / reconcile. Snapshot durable y scope antes de comandos/replays. |
| Maintenance | GET `/v1/maintenance/warehouse-material-requests` y `/returnable-materials` | Permisos existentes, bandejas acotadas por contexto. |
| Maintenance | POST `/v1/maintenance/material-returns/validate` y `/reconcile` | Permisos existentes; validate añade contexto/costo original, reconcile los contrasta. |

Consumidas sin cambio contractual: Admin `GET /v1/session/context`; Production `GET /v1/production/machines/{id}` y `GET /v1/production/orders/{id}` para solicitudes vinculadas; requieren sus permisos existentes de lectura (máquinas también admite `maintenance.order.create`). Sales/Production proof y terminado anteriores se conservan. Contabilidad, Costing, RH y libros no cambian por este corte. Los OpenAPI son autoridad para la lista exacta de permisos alternativos de cada operación.

## Persistencia, configuración y rollback

`0057` agrega JSONB nullable: Inventory transfers.destination_context y movements.monetary_snapshot; Purchasing purchase_receipt_lines.inventory_context_snapshot; Maintenance material_requests.organization_context. Inventory añade source_line_id e índice único parcial de recepciones; Maintenance índice tenant/División. Cada dueño conserva sus tablas; sin FKs cruzadas. Modelos y migración reflejan estas expansiones. Downgrade se rechaza si existen snapshots/identidades nuevas; con historia aplicar corrección hacia adelante. El ciclo vacío upgrade/downgrade/upgrade se comprobó sólo en Local.

Inventory requiere `ERCLAVE_PURCHASING_SERVICE_URL`; Local sólo loopback, QA futuro HTTPS explícito mediante pipeline. Se preparó cableado sin ejecutar despliegue. Las pruebas se limitan a `127.0.0.1:5434/erclave_local` y `ten_739ee59d765d5e14818674800d`, con rollback o limpieza de IDs propios; sin tenants temporales ajenos, datos reales ni servicios remotos.

## Evidencia y aceptación

Pruebas PostgreSQL de los tres dueños: snapshots, recepción parcial, retorno, recuperación, carreras, aislamiento, alcance revocado y precisión. Tests API con dependencias controladas verifican identidad de actor, tenant, permisos y proofs manipulados. Navegador usa APIs interceptadas y valida formulario ES/EN, errores, precisión, cambio de moneda e identidad estable de reintentos. Las cifras finales y logs se registran en [CHG-317](../../TRAZABILIDAD.md).

Estas pruebas no son UAT de QA ni certificación del recorrido autenticado entre todos los servicios. Esa aceptación transversal y los datos reales continúan CC-19/20. Los manuales Word son candidatos hasta su revisión visual documentada.
