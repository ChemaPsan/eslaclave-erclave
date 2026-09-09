# Confirmaciones de Almacén y mensajes de flujo — CHG-265

## Alcance y criterios de aceptación

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.

- Preparar una recepción/entrega no modifica inventario; confirmarla requiere Almacén.
- Servicios comprados solo los acepta el solicitante original; compra directa, el comprador.
- Transferir resta origen, recibir suma destino; retorno requiere recepción en origen.
- Devolver sobrantes no excede lo emitido y conserva historial; costo se ajusta una vez en el propietario.
- Reintentos, errores parciales y concurrencia no duplican movimientos; actor y tenant se verifican.
- Inicio/reanudación rechaza máquinas bloqueadas y responsables no elegibles con guía ES/EN.
- Reversar un movimiento manual mantiene saldo correcto; documentos vinculados requieren su flujo propio.

## Ambiente, agentes y datos

Local aislado: PostgreSQL 127.0.0.1:5434/erclave_local, APIs loopback, Firebase Emulator demo-erclave. Único tenant de escritura: ten_739ee59d765d5e14818674800d. Sin seeds, promoción, QA/Producción, commit, push ni PR. Agentes consultados documentalmente: negocio/técnicos de los seis módulos y Arquitectura/API/Datos, Custodio DB, Seguridad, Sinergia, UX/i18n, QA, Gobierno documental. Skills erclave-feature, erclave-environment-boundaries y erclave-db-migration.

0032 preserva recepciones históricas y crea transferencias nuevas en tránsito; 0033 separa devolución física de ajustes de propietarios; 0034 conserva intentos fallidos y tombstone contra reservas tardías. Local head 20260908_0034; QA head 20260825_0029. Downgrade protegido: conciliar pendientes y resguardar historial antes de revertir; no compensar stock por eliminar tablas. Recuperación operativa usa reintento manual con clave durable.

## APIs afectadas

Todas las rutas usan X-Tenant-Id y autorización ERClave. Comandos persistentes usan Idempotency-Key; validaciones de devolución son consultas POST sin mutación ni clave. Los permisos alternativos del contrato se complementan con validación de actor/origen; purchasing.receipt.reconcile y sales.delivery.confirm solos reciben el mensaje de continuar con Almacén. Las bandejas se acotan por limit/offset. La tabla incluye operaciones nuevas o con permisos, validación, respuesta o semántica modificados en este corte.

### Contratos modificados

| Servicio | Método y ruta | Permisos declarados (alternativas) | Request/response o comportamiento |
|---|---|---|---|
| inventory | `GET /v1/inventory/warehouses` | inventory.movement.create, inventory.movement.read, inventory.warehouse.read, maintenance.material_request.create, maintenance.material_request.read | Warehouses |
| inventory | `POST /v1/inventory/warehouses` | inventory.warehouse.create | Create Warehouse |
| inventory | `GET /v1/inventory/warehouses/{id}` | inventory.warehouse.read, maintenance.material_request.create, purchasing.receipt.create | Get one tenant warehouse for Inventory or Purchasing validation. |
| inventory | `PATCH /v1/inventory/warehouses/{id}` | inventory.warehouse.update | Update warehouse. |
| inventory | `POST /v1/inventory/warehouses/{id}/locations` | inventory.location.create | Create warehouse location. |
| inventory | `GET /v1/inventory/movements` | inventory.movement.read | Movements |
| inventory | `POST /v1/inventory/movements` | inventory.movement.create | A transfer records only its outgoing movement; the destination must confirm receipt through the transfer workflow. Reversal compensators and reversed originals both remain in the authoritative ledger. |
| inventory | `POST /v1/inventory/purchase-receipts` | inventory.movement.create | Warehouse-only physical purchase receipt; Purchasing preparation does not create stock. Stable receipt-line idempotency keys prevent duplicate entries. |
| inventory | `GET /v1/inventory/transfers` | inventory.movement.read | Transfers |
| inventory | `GET /v1/inventory/material-returns` | inventory.movement.read | Material Returns |
| inventory | `POST /v1/inventory/material-returns` | inventory.movement.create, maintenance.material_request.create, production.order.update | Request Material Return |
| inventory | `GET /v1/inventory/material-returns/{return_id}` | inventory.movement.create, inventory.movement.read | Material Return |
| inventory | `POST /v1/inventory/material-returns/{return_id}/receive` | inventory.movement.create | Receive Material Return |
| inventory | `POST /v1/inventory/material-returns/{return_id}/cancel` | inventory.movement.create | Cancel Material Return |
| inventory | `POST /v1/inventory/transfers/{transfer_id}/{action}` | inventory.movement.create | Transfer Action |
| inventory | `POST /v1/inventory/movements/{movement_id}/reverse` | inventory.movement.reverse | Reverse Movement |
| inventory | `POST /v1/inventory/reservations/{reservation_id}/release` | inventory.movement.create, maintenance.material_request.cancel, maintenance.order.cancel, production.order.cancel, sales.order.cancel | Maintenance order cancellation may release its unissued parts reservations. Production creation recovery uses the separate proven-failure rollback endpoint. |
| inventory | `POST /v1/inventory/reservations/{reservation_id}/consume` | inventory.movement.create | Warehouse authority is required for production, maintenance and sales stock issues. Source ownership and full-quantity requirements for production/maintenance remain enforced. |
| inventory | `POST /v1/inventory/production-reservation-rollbacks` | production.order.release | Rollback Production Reservations |
| production | `POST /v1/production/orders/{order_id}/issue-materials` | inventory.movement.create | No business payload. Stable order/reservation keys recover crashes and repeated calls without duplicate movements. Starting/resuming never consumes. Issuance does not change order status. Actor and designated order owner are audited. |
| production | `GET /v1/production/orders` | production.order.read | List Orders |
| production | `POST /v1/production/orders` | production.order.release | HR and resource validation precede creation. Failed creation records a recovery owned by its actor; rollback releases only that failed source and prevents late reservation writes. |
| production | `PATCH /v1/production/orders/{id}/resources/{resource_id}` | production.order.update | Record actual labor or machine usage for operational costing. |
| production | `GET /v1/production/machines` | production.machine.read | List machines. |
| production | `POST /v1/production/machines` | production.machine.create | Create machine. |
| production | `GET /v1/production/machines/{machine_id}` | maintenance.order.create, production.machine.read | Get Machine |
| production | `PATCH /v1/production/machines/{machine_id}` | production.machine.update | A machine held by Maintenance cannot have its status changed manually; Maintenance must release the hold. |
| production | `POST /v1/production/machines/{machine_id}/maintenance-block` | maintenance.order.reopen, maintenance.order.request | Mark a machine in maintenance and pause an eligible linked Production order. |
| production | `POST /v1/production/machines/{machine_id}/maintenance-release` | maintenance.order.cancel, maintenance.order.resolve | Return a maintained machine to active without automatically resuming Production. |
| production | `GET /v1/production/orders/{order_id}` | production.order.read | Get Order |
| production | `PATCH /v1/production/orders/{order_id}/status` | production.order.cancel, production.order.complete, production.order.pause, production.order.release, production.order.resume, production.order.send_to_validation, production.order.start, production.order.wait_resources | Starting/resuming requires issued materials, active machines without maintenance holds, and currently eligible HR assignees. Workflow errors include stable codes and transition context. |
| production | `GET /v1/production/returnable-materials` | inventory.movement.read, production.order.update | Returnable Materials |
| production | `POST /v1/production/material-returns/validate` | inventory.movement.create, production.order.update | Validate Material Return |
| production | `POST /v1/production/material-returns/reconcile` | inventory.movement.create | Reconcile Material Return |
| production | `GET /v1/production/failed-order-creations` | production.order.release | Failed Order Creations |
| production | `GET /v1/production/failed-order-creations/{order_id}` | production.order.release | Failed Order Creation |
| production | `POST /v1/production/failed-order-creations/{order_id}/recover` | production.order.release | Recover Order Creation |
| purchasing | `GET /v1/purchasing/receipts` | purchasing.receipt.read | Receipts |
| purchasing | `POST /v1/purchasing/receipts` | purchasing.receipt.create | Prepares a pending_confirmation receipt without receiving goods or accepting services. Pending quantities count against over-receipt checks. Warehouse confirms inventory lines; the original requisition requester (buyer for direct purchases) accepts service lines. |
| purchasing | `POST /v1/purchasing/receipts/{id}/reconcile` | inventory.movement.create, purchasing.receipt.reconcile | Warehouse confirms/retries inventory lines only. The legacy purchasing.receipt.reconcile permission is recognized but alone returns purchase_warehouse_receipt_required; inventory.movement.create is required to post stock. Service lines remain pending requester acceptance. |
| purchasing | `GET /v1/purchasing/warehouse-receipts` | inventory.movement.read | Warehouse Receipts |
| purchasing | `GET /v1/purchasing/service-acceptances` | purchasing.order.create, purchasing.requisition.create | Service Acceptances |
| purchasing | `POST /v1/purchasing/receipts/{id}/accept-services` | purchasing.order.create, purchasing.requisition.create | Accept Receipt Services |
| sales | `GET /v1/sales/service-orders` | sales.service_order.read |  |
| sales | `GET /v1/sales/service-orders/{id}` | sales.service_order.read |  |
| sales | `POST /v1/sales/service-orders/{id}/plan` | sales.service_order.plan |  |
| sales | `POST /v1/sales/service-orders/{id}/time-entries` | sales.service_order.time.create |  |
| sales | `POST /v1/sales/service-orders/{id}/cost-entries` | sales.service_order.cost.create |  |
| sales | `POST /v1/sales/service-orders/{id}/evidence` | sales.service_order.evidence.create |  |
| sales | `GET /v1/sales/deliveries` | sales.delivery.read |  |
| sales | `POST /v1/sales/deliveries` | sales.delivery.create |  |
| sales | `GET /v1/sales/deliveries/{id}` | sales.delivery.read |  |
| sales | `POST /v1/sales/deliveries/{id}/cancel` | sales.delivery.cancel |  |
| sales | `POST /v1/sales/service-orders/{service_order_id}/transitions/{action}` | sales.service_order.assign, sales.service_order.start, sales.service_order.wait, sales.service_order.resume, sales.service_order.submit_acceptance, sales.service_order.accept, sales.service_order.cancel | Start and resume revalidate the assigned worker through HR. Invalid transitions return workflow and requested_status details for actionable localized guidance. |
| sales | `POST /v1/sales/deliveries/{delivery_id}/confirm` | inventory.movement.create, sales.delivery.confirm | Warehouse dispatch confirmation. A sales.delivery.confirm-only user receives sales_warehouse_dispatch_required. Inventory authority performs the physical issue and Sales records fulfillment using the existing durable retry keys. |
| sales | `GET /v1/sales/warehouse-deliveries` | inventory.movement.read | Warehouse Deliveries |
| maintenance | `GET /v1/maintenance/orders` | maintenance.order.read | Orders |
| maintenance | `POST /v1/maintenance/orders` | maintenance.order.create | Create Order |
| maintenance | `GET /v1/maintenance/orders/{id}` | maintenance.order.read | Get Order |
| maintenance | `PATCH /v1/maintenance/orders/{id}` | maintenance.order.update | Update Order |
| maintenance | `POST /v1/maintenance/orders/{id}/transitions` | maintenance.order.request, maintenance.order.assign, maintenance.order.start, maintenance.order.wait_for_parts, maintenance.order.resume, maintenance.order.resolve, maintenance.order.close, maintenance.order.reopen, maintenance.order.cancel | Transition Order |
| maintenance | `POST /v1/maintenance/orders/{id}/reconcile` | maintenance.order.reconcile | Retry the durable pending Production operation; material issues must be reconciled by Warehouse from Movements. |
| maintenance | `GET /v1/maintenance/orders/{id}/time-entries` | maintenance.time.read |  |
| maintenance | `POST /v1/maintenance/orders/{id}/time-entries` | maintenance.time.create |  |
| maintenance | `GET /v1/maintenance/orders/{id}/material-requests` | maintenance.material_request.read |  |
| maintenance | `POST /v1/maintenance/orders/{id}/material-requests` | maintenance.material_request.create | Create a multi-line internal request against a spare-parts warehouse. |
| maintenance | `GET /v1/maintenance/returnable-materials` | inventory.movement.read, maintenance.material_request.create | Returnable Materials |
| maintenance | `POST /v1/maintenance/material-returns/validate` | inventory.movement.create, maintenance.material_request.create | Validate Material Return |
| maintenance | `POST /v1/maintenance/material-returns/reconcile` | inventory.movement.create | Reconcile Material Return |
| hr | `GET /v1/hr/workers/production-eligible` | production.order.release, production.order.resume, production.order.start | Production Workers |
| hr | `GET /v1/hr/workers/maintenance-eligible` | maintenance.order.assign, maintenance.order.reopen, maintenance.order.resume, maintenance.order.start, maintenance.time.create | Maintenance Workers |
| hr | `GET /v1/hr/workers/sales-eligible` | sales.customer.create, sales.customer.update, sales.order.create, sales.quote.approve, sales.quote.create, sales.quote.submit, sales.quote.update, sales.service_order.assign, sales.service_order.resume, sales.service_order.start, sales.service_order.time.create | Sales Workers |

### Consumidos sin cambio

- Admin: GET /v1/session/context y GET /v1/catalogs/units-of-measure/by-code/{code}; autenticación, membresías, permisos y entitlements conservados. Clientes de sesión/unidades existentes.
- Inventory: GET /v1/inventory/items/{item_id}, POST /v1/inventory/availability-checks, POST /v1/inventory/reservation-requests; validación de artículos y reservas mediante sus permisos de consulta/comando existentes. POST reserva agrega bloqueo interno contra creaciones fallidas sin cambiar payload.
- Production: GET /v1/production/orders/{order_id} y GET /v1/production/finished-goods-candidates/{id} siguen respaldando recepción de producto terminado; no se escribe otro schema.

### APIs no tocadas

Admin/Backoffice y servicios planned: sin cambios en este corte. Los cambios locales previos CHG-262/263/264 se preservan. No cambian interfaces externas, Firebase ni APIs QA.

## Verificación

Browser usa Firebase/Admin Local y comandos HTTP interceptados; no demuestra por sí solo el circuito distribuido. Integración PostgreSQL usa fixtures del tenant autorizado y limpieza exacta de sus registros. La suite general sin ERCLAVE_TEST_DATABASE_URL omite integraciones que requieren base; no se presenta como prueba PostgreSQL total.

## Límites y pendientes

La conexión automática Ventas–Producción–entrega y materiales de servicios comerciales permanecen planned. No se implementan devoluciones comerciales a proveedor/cliente, merma ni aprobación separada de la entrega. Reversa genérica protege documentos vinculados; su protección no significa que todos esos flujos de devolución ya existan. El alcance por almacén conserva permisos globales del tenant; no se creó asignación individual de almacenes. Recepción parcial aplica a transferencias; solicitudes productivas/refacciones se emiten completas. Pendientes: carga sostenida, interrupciones prolongadas y certificación QA tras aprobación.

La recepción de producto terminado conserva su reversa controlada cuando hay saldo disponible: Inventory recalcula su propio acumulado efectivo. No hay una cantidad recibida escrita en Production que requiera callback. El informe de refacciones distingue cantidad emitida, cantidad devuelta y costo neto.

## Resultados finales Local

- `npm run verify`: todos los validadores, compilación y 257 pruebas backend aprobados. 51 integraciones omitidas en esa ejecución por no configurar base; se ejecutó por separado el conjunto PostgreSQL afectado.
- PostgreSQL Local: 19 pruebas aprobadas en cinco servicios, con permisos, actor solicitante, tenant ajeno de solo lectura negativa, reintentos, concurrencia, cancelación de devolución, compensación y costo. Fixture cleanup exclusivamente por IDs/actores propios.
- Playwright: 40 pruebas del recorrido completo aprobadas; 7 nuevas cubren recepción, salida, transferencia parcial, rol de lectura, ES/EN y contenedor real de 520px, errores, aceptación de servicios y cancelación de devolución. Capturas revisadas.
- HTTP real con Firebase Emulator/Admin Local: `smoke_production_warehouse_local.py` certifica bloqueo, salida, inicio y devolución Inventory→Production con costo neto y entrada única; `smoke_operational_handoffs_local.py` certifica preparación sin stock, recepción única, rechazo a no solicitante y aceptación de servicio de recepción mixta.
- Alembic: downgrade Local vacío de 0034 a 0031 y upgrade a 0034 aprobados, con guardas de historial. Sin seeds ni recursos remotos.
- Regresiones encontradas y corregidas: las bandejas actualizan su propio contenedor al cargar para conservar formularios; resolver Mantenimiento conserva su comando propio; permisos OpenAPI mantienen formato compatible con el lector de seeds existente.
- Limitación de evidencia: Sales usa integración PostgreSQL con doble de Inventory para despacho; los dos smokes HTTP descritos sí cruzan servicios reales. No se afirma certificación QA ni estrés distribuido.
