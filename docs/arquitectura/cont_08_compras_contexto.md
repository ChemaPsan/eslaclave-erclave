# CONT-08 · Contexto de Compras

## Vigencia y autoridad

CC-15 · CHG-319 · 2026-10-12. Implementado Local con evidencia focal backend y navegador. Regresión UI completa y gate general aprobados; aceptación transversal CC-20 pendiente. No acredita UAT ni promoción a QA. El ciclo base en QA documentado sigue en `e57237f`. Estado y aceptación: [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md) y [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md).

Amplía [condiciones por División](cont_07_commercial_condiciones.md) y conserva [recepción física y costo CC-14](cont_08_inventario_productores.md). Purchasing posee requisiciones, órdenes y recepciones; Admin gobierna División, Sociedad, moneda base y alcance. Inventory es autoridad de existencias. No activa Accounting, facturas, cuentas por pagar ni folios CC-18.

## Contexto y condiciones conservados

La requisición nueva exige una División autorizada. El servidor deriva su Sociedad y moneda base desde Admin y conserva `organization_context`; el cliente no decide esos valores. La División queda fija al editar. Una orden ligada hereda el contexto de su requisición aprobada y convierte sus partidas completas, sin adjudicación parcial. Una orden directa requiere División explícita y motivo auditable; el alta directa sigue siendo API, sin nuevo formulario.

La orden exige proveedor activo, asociación activa en su División y Sociedad confirmada, con condiciones completas de esa División. Conserva `commercial_terms_snapshot` con `supplier_id`, `terms_revision`, `values` (`currency`, `payment_terms`, `lead_time_days`) y `division` (`id`, `code`, `name`, `society_id`). No hereda condiciones de la ficha global. Los campos moneda/pago enviados deben coincidir con los valores autoritativos; si se omiten, el servidor los obtiene de las condiciones.

Editar con el mismo proveedor conserva el snapshot original, aunque haya cambiado el catálogo. Cambiar explícitamente proveedor captura sus condiciones vigentes en la misma División. Emitir revalida elegibilidad y partidas sin sustituir condiciones históricas ni recalcular precios. El plazo capturado no recalcula automáticamente fechas prometidas.

La recepción hereda el contexto de la orden incluso si sólo contiene servicios. Cada almacén físico debe pertenecer a la misma División; compartir Sociedad o moneda no basta. Conserva moneda/precio documental, moneda de Sociedad, tasa y costo convertido de CC-14. Precio de orden con dos decimales, costo convertido con seis; misma moneda implica tasa uno y otra moneda exige tasa positiva explícita. Reconciliar usa el snapshot y la prueba durable del productor, sin recostear.

## Campos y contrato HTTP

| Recurso/campo | Captura y autoridad | Regla |
|---|---|---|
| Requisición `division_ref_id` | Selección de División autorizada | Obligatoria al crear; omitir en PATCH conserva la existente; no cambiarla. |
| Orden `requisition_id` | Requisición aprobada | Hereda contexto; conserva exactamente todas sus partidas. |
| Orden directa `division_ref_id`, `direct_purchase_reason` | División autorizada y motivo del comprador | Obligatorios sin requisición. |
| Orden `supplier_id` | Proveedor elegible por División | Cambiarlo renueva explícitamente sus condiciones. |
| Orden `currency`, `payment_terms` | Condiciones de División | Opcionales en entrada; discrepancia rechazada con 422. |
| Orden `expected_terms_revision` | Revisión de las condiciones mostradas al seleccionar proveedor | Derivada por UI, sin captura adicional; opcional para otros clientes, mínimo 1. Una revisión distinta del snapshot aplicable rechaza con 409 en `supplier_id` antes de crear efectos. El mismo proveedor en edición compara el snapshot histórico, sin refrescarlo. |
| Documentos `organization_context` | Snapshot generado por servidor | Contexto inmutable; nunca inferido del tenant. |
| Orden `commercial_terms_snapshot` | Snapshot generado por servidor | Preservado con mismo proveedor y al emitir. |
| Recepción `cost_exchange_rate` | Usuario autorizado | Conserva regla CC-14; no reemplaza contexto de orden. |
| Centro de costos | Fuera del flujo habilitado | No se impone como obligatorio. |

Nuevas consultas bajo `/v1/purchasing`: `GET /document-divisions` para permisos `purchasing.requisition.create/update` o `purchasing.order.create/update`, y `GET /document-suppliers` para `purchasing.order.create/update`. Ambas paginan mediante `q`, `limit`, `offset`; proveedores recibe `division_id` y devuelve `commercial_terms.values/revision`. Son proyecciones mínimas para operar documentos, sin conceder administración del maestro. El contrato definitivo de parámetros y respuestas se conserva en [OpenAPI](../../contracts/api/purchasing-service.openapi.yaml).

Se amplían creación/edición/lectura/transiciones de `/requisitions`, `/orders`, `/receipts`, sus bandejas y reportes; no se incorporan permisos nuevos. La confirmación física mantiene `inventory.movement.create`. Aceptar servicios sigue reservado al solicitante original o comprador de una orden directa, con `purchasing.requisition.create` o `purchasing.order.create`; el alcance documental también es obligatorio.

Todos los contratos modificados son del servicio Purchasing, bajo `/v1/purchasing`, con tenant y autenticación vigentes. Métodos/rutas y permisos exactos:

| Método y ruta | Permiso existente | Cambio |
|---|---|---|
| GET `/v1/purchasing/requisitions` | `purchasing.requisition.read` | Filtro de alcance en SQL; respuesta conserva `organization_context` nullable para historia. |
| POST `/v1/purchasing/requisitions` | `purchasing.requisition.create` | Exige División al crear; deriva Sociedad/moneda, valida artículos asignados y congela contexto; digest ligado al actor. |
| PATCH `/v1/purchasing/requisitions/{id}` | `purchasing.requisition.update` | Omitir División conserva la original; cambio rechazado. Alcance antes de efectos/replay. |
| POST `/v1/purchasing/requisitions/{id}/submit` | `purchasing.requisition.submit` | Contexto/alcance y replay autorizado; no exige lectura adicional Inventory al solicitante. |
| POST `/v1/purchasing/requisitions/{id}/approve` | `purchasing.requisition.approve` | Contexto/alcance y replay autorizado; no exige lectura adicional Inventory al aprobador. |
| POST `/v1/purchasing/requisitions/{id}/reject` | `purchasing.requisition.reject` | Contexto/alcance antes de comando/replay, motivo existente. |
| POST `/v1/purchasing/requisitions/{id}/cancel` | `purchasing.requisition.cancel` | Cancelación histórica autorizada; contexto antes de replay y digest por actor para documentos dimensionados. |
| GET `/v1/purchasing/orders` | `purchasing.order.read` | Alcance en SQL, contexto y snapshot de condiciones en respuesta. |
| POST `/v1/purchasing/orders` | `purchasing.order.create` | Hereda requisición o exige División directa; condiciones explícitas congeladas. Moneda/pago opcionales y deben coincidir si se envían; `expected_terms_revision` opcional detecta revisión obsoleta. |
| PATCH `/v1/purchasing/orders/{id}` | `purchasing.order.update` | Origen/División fijos; mismo proveedor conserva condiciones, cambio explícito toma snapshot nuevo. Compara revisión del snapshot aplicable. |
| POST `/v1/purchasing/orders/{id}/issue` | `purchasing.order.issue` | Elegibilidad y catálogos vigentes para emisión nueva; replay no recostea ni recaptura condiciones. |
| POST `/v1/purchasing/orders/{id}/cancel` | `purchasing.order.cancel` | Alcance antes de efectos/replay; historia sin dimensión sólo con alcance completo. |
| GET `/v1/purchasing/receipts` | `purchasing.receipt.read` | Alcance documental incluso servicios; contexto heredado en respuesta. |
| POST `/v1/purchasing/receipts` | `purchasing.receipt.create` | Hereda contexto OC, almacén físico de la misma División y moneda congelada; conserva tasa, claves y recuperación CC-14. |
| GET `/v1/purchasing/receipts/{receipt_id}/lines/{line_id}/inventory-proof` | `inventory.movement.create` | Prueba durable conserva contexto OC y alcance de recepción completa; sin efecto físico. |
| POST `/v1/purchasing/receipts/{id}/reconcile` | Alternativa `purchasing.receipt.reconcile` / `inventory.movement.create`; bienes requieren `inventory.movement.create` | Alcance antes de conciliación/replay, historia CC-14 previamente preparada recuperable. |
| GET `/v1/purchasing/warehouse-receipts` | `inventory.movement.read` | Filtra documento completo antes de paginar. |
| GET `/v1/purchasing/service-acceptances` | `purchasing.requisition.create` o `purchasing.order.create` | Bandeja por solicitante/comprador y alcance del contexto, sin Inventory. |
| POST `/v1/purchasing/receipts/{id}/accept-services` | `purchasing.requisition.create` o `purchasing.order.create` | Además identidad del solicitante/comprador; alcance y replay autorizados antes de aceptación. |
| GET `/v1/purchasing/reports/{report_code}/export` | Según reporte: `purchasing.supplier.read`, `purchasing.requisition.read`, `purchasing.order.read`, `purchasing.receipt.read` | CSV de documentos filtrado por contexto; proveedores conservan contrato compartido. |
| GET `/v1/purchasing/document-divisions` | Una de `purchasing.requisition.create`, `purchasing.requisition.update`, `purchasing.order.create`, `purchasing.order.update` | Nueva proyección acotada: División, Sociedad, moneda de costo y paginación `q/limit/offset`; sin CRUD de proveedores. |
| GET `/v1/purchasing/document-suppliers` | `purchasing.order.create` o `purchasing.order.update` | Nueva búsqueda por `division_id/q/limit/offset`: identidad mínima y condiciones/revisión o confirmación pendiente. |

Consumidas sin cambio contractual: Admin GET `/v1/session/context`, GET `/v1/catalogs/units-of-measure`, GET `/v1/catalogs/units-of-measure/by-code/{code}`, GET `/v1/catalogs/commercial/{catalog_code}` y GET `/v1/catalogs/commercial/{catalog_code}/by-code/{code}`; Inventory GET `/v1/inventory/items/{item_id}`, GET `/v1/inventory/items/{item_id}/division-assignments`, GET `/v1/inventory/division-items`, GET `/v1/inventory/warehouses`, GET `/v1/inventory/warehouses/{warehouse_id}` y POST `/v1/inventory/purchase-receipts`. Conservan permisos existentes de consumidor/catálogo; partidas físicas requieren sus permisos Inventory vigentes, servicios no los añaden. APIs de Sales, Production, RH, Maintenance, Costing, Expenses y Accounting no modificadas.

## Alcance, historia y recuperación

Cada listado, detalle, transición, bandeja, CSV y reintento verifica el alcance organizacional del documento antes de revelar datos o devolver un resultado idempotente. Un permiso de acción no amplía el alcance; ningún nombre de rol lo sustituye. Revocar alcance debe impedir también replay y confirmación de servicios. Recepciones mixtas no permiten revelar partidas fuera del alcance por confirmar sólo un subconjunto.

Los documentos históricos sin contexto permanecen identificables como legacy, sin backfill ni División/moneda inventada. Sólo lectura y cancelación con alcance completo; editar o crear recepciones nuevas exige revisión histórica (`history_review_required`). La recuperación de recepciones preparadas bajo CC-14 conserva su contexto/costo auténtico y su ruta de conciliación existente. La ausencia de datos no autoriza atribuir una Sociedad por defecto.

## Criterios de aceptación y evidencia

Los criterios de Purchasing cubren aislamiento entre Divisiones, scope revocado antes de replay, legacy con/sin contexto de recepción, proveedor inactivo o de otra Sociedad, condiciones incompletas, discrepancia de moneda/pago, conservación con mismo proveedor, cambio explícito de proveedor, compra directa y recepción sólo de servicios. Recepción física debe rechazar almacén de otra División incluso con la misma moneda, impedir sobrerecepción y recuperar el mismo movimiento sin duplicar ni recostear.

UI debe comprobar División fija, Sociedad/moneda derivadas, artículos/proveedores filtrados, condiciones de sólo lectura, almacén heredado, captura conservada y clave estable al reintentar, errores por campo y ES/EN. APIs interceptadas prueban interfaz, no integración real. Los ensayos con PostgreSQL/HTTP deben usar exclusivamente el tenant demo autorizado y recuperación/rollback documentados; no QA ni datos de negocio reales.

Evidencia Local: suite Purchasing **77 aprobadas, 0 omitidas, 1 advertencia** (`chg319-purchasing-terms-tests.log`), incluidas diez pruebas CC-15 PostgreSQL y dos de alcance propio para enviar/aprobar; navegador focal **16 CC-15 + 6 CC-14** aprobadas con APIs interceptadas. Migración `0058` comprobada up/down/up y downgrade con historia protegido en PostgreSQL. Los comandos nuevos de requisiciones/órdenes y cancelaciones dimensionadas vinculan digest al actor: otro actor con la misma clave recibe conflicto y no genera efectos; el replay de recepción CC-14 conserva su contrato. Son pruebas de integración local y de interfaz según su capa, no una UAT transversal. Regresión final de navegador: **255 aprobadas**, 0 fallos/omisiones (`chg319-browser-regression-final.log`), incluidos los controles en panel real de 320 px ES/EN. Verify final aprobado: validadores/documentación, compilación y **727 aprobadas, 223 omitidas, 1 advertencia** sin DB (`chg319-verify-final.log`); omisiones no acreditadas como aprobaciones. Índice173 documentos y diff--check aprobados. `expected_terms_revision` evita aceptar silenciosamente cambios de condiciones entre selección y guardado; PostgreSQL y navegador prueban rechazo sin efectos y captura conservada.

Manual y ficha: [Compras](../../modulos/03_compras_abastecimiento.md), [manual fuente](../manuales_solucion/fuentes/03_compras_abastecimiento.md), [registro Word](../manuales_solucion/REGISTRO.md). Aceptación CC-20 pendiente; QA/Producción sin promoción de este alcance.
