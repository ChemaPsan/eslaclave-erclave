# Recuperación de refacciones interrumpidas — CHG-268

## Problema y resultado

MTO-000001, «No calienta», tenía una solicitud de 1 H87 de Rodamiento 001 fallida por existencia insuficiente el 6 de septiembre. Un reintento quedó en `processing/reserve` sin terminar su registro de idempotencia. El cliente HTTP de Maintenance intentaba serializar directamente un `Decimal` leído de PostgreSQL: fallaba antes de llamar a Inventory. La pantalla tampoco ofrecía recuperar ese estado interrumpido.

Se corrigió la codificación JSON de cantidades, se incorporó la recuperación manual de reservas/cancelaciones interrumpidas y se recuperó la solicitud existente mediante la API Local. No se registró entrega física.

## Comportamiento y límites

- Maintenance codifica cantidades con `jsonable_encoder`; rechaza números no finitos y convierte errores de serialización en el error recuperable existente. Las fallas de dependencia quedan conciliables.
- `reconcile` admite `needs_reconciliation`, `processing/reserve` y `cancelling/cancel`. Una operación de entrega corresponde a Almacén; esta acción nunca consume inventario.
- Locks de sesión PostgreSQL por tenant/orden y solicitud abarcan creación, reserva, reintento, entrega y cancelación de solicitudes. Un comando concurrente recibe `command_in_progress`; no se mantiene una transacción de datos durante HTTP.
- Una clave de conciliación idéntica sin respuesta puede retomarse bajo el lock. Un hash distinto sigue rechazado. Se conservan claves Inventory por solicitud/partida; las partidas confirmadas se omiten y las respuestas perdidas se recuperan por idempotencia.
- Solicitudes terminales devuelven su estado sin nuevos efectos en Inventory. Las reservas requieren que la orden siga asignada, en proceso o esperando refacciones. Se conserva aislamiento por tenant.
- Mantenimiento → Órdenes/Refacciones muestra **Reintentar reserva** o **Reintentar cancelación**, con `maintenance.material_request.reconcile`. El botón se deshabilita durante el comando y se rehabilita si falla. Mensajes equivalentes ES/EN indican el siguiente paso en Almacenes → Movimientos.
- El reacomodo responsive usa exclusivamente `.maintenance-workspace` y tarjetas de Mantenimiento; no modifica la composición de otros módulos.
- El reintento es manual. Falta de existencia, indisponibilidad o futuras interrupciones aún pueden requerir intervención; no se promete ausencia absoluta de fallas. No se reactivan reservas vencidas ni se alteran movimientos por inferencia.

## Evidencia Local

Ambiente comprobado: APIs loopback, PostgreSQL `127.0.0.1:5434/erclave_local`, Firebase Emulator. Tenant `ten_739ee59d765d5e14818674800d`; actor `usr_595f3cd6d4325901a8dbd028e1`, con permiso existente. Reiniciado únicamente Maintenance en 8012, sin seeds, grants ni migraciones.

Recuperación del 8 de septiembre, 16:38:42, México:

| Evidencia | Antes | Después |
|---|---|---|
| Solicitud `mmr_9bfb818145f946229ea3407884` | `processing/reserve` | `reserved`, sin operación pendiente |
| Partida `mml_a79a0026f1d2483082b4a88a15` | Fallida, sin reserva | Reservada, 1 H87 |
| Reserva Inventory | Ninguna | `rsv_3c6a360a05f34a6c9459c71f78`, única y activa |
| Existencia física / reservada / disponible | 2 / 0 / 2 | 2 / 1 / 1 |
| Movimientos del artículo/almacén | 1 | 1, sin salida adicional |
| Clave de conciliación original | Sin respuesta | Completada; repeticiones sin duplicados |

La bandeja Warehouse devuelve la solicitud `reserved`. El almacenista puede autorizar y entregar; este corte no pulsó esa acción. La orden conserva su estado y técnico.

Cuatro pruebas PostgreSQL seleccionadas aprobadas: interrupción después de confirmar Inventory pero antes de completar Maintenance, replay de la misma/nueva clave, hash distinto, tenant ajeno sin escritura, bloqueo concurrente, reserva parcial, cancelación interrumpida y separación de entrega. Usan únicamente fixtures propias del tenant permitido, limpiadas por sus identificadores. Inventory HTTP se dobla en esas pruebas; la recuperación anterior sí utilizó ambas APIs reales.

Pruebas API de Maintenance: 16 aprobadas, incluidas serialización Decimal real, rechazo de NaN y permiso exacto. Pruebas de navegador añadidas: estados/acciones/permiso ES/EN con panel de 520 px y comando concurrente que rehabilita botón. La regresión general se registra en TRAZABILIDAD.md. El primer script de comprobación usó un nombre de campo incorrecto después de recuperar; se corrigió a `inventory_movement_id` y se verificó el resultado por lectura y replay, sin repetir una reserva nueva.

## APIs afectadas

### Contratos modificados

| Servicio | Método y ruta | Permiso | Cambio |
|---|---|---|---|
| Maintenance | POST `/v1/maintenance/orders/{id}/material-requests` | `maintenance.material_request.create` | Describe exclusión concurrente de creación/reserva. Request/response conservados. |
| Maintenance | POST `/v1/maintenance/material-requests/{id}/reconcile` | `maintenance.material_request.reconcile` | Recupera operaciones interrumpidas y clave pendiente bajo lock; terminales sin efecto. Request/response conservados. |

### Endpoints consumidos o protegidos, sin cambio de contrato

- Inventory: POST `/v1/inventory/reservation-requests` requiere el permiso existente `maintenance.material_request.create` para el solicitante de Mantenimiento; POST `/v1/inventory/reservations/{reservation_id}/release` admite `maintenance.material_request.cancel`, `maintenance.order.cancel` o `inventory.movement.create` para origen Maintenance. Conciliar no concede esos permisos: se preserva la autorización en cada autoridad. El actor Local ya cuenta con los permisos necesarios. Se conservan referencias de origen y claves por partida. GET `/v1/inventory/items/{item_id}` y GET `/v1/inventory/warehouses/{warehouse_id}` validan referencias existentes.
- Maintenance: GET `/v1/maintenance/orders`, GET `/v1/maintenance/orders/{id}/material-requests` y GET `/v1/maintenance/warehouse-material-requests`; consultas y permisos existentes.
- Maintenance: POST `/v1/maintenance/material-requests/{id}/cancel`, `/issue` y `/reject`; comparten exclusión con recuperación. Cancelar conserva `maintenance.material_request.cancel`; entrega/rechazo conserva `inventory.movement.create` y entitlement Maintenance. No se invocaron entrega/rechazo en la recuperación real.
- Admin: GET `/v1/session/context`, sesión y autorización existente.

APIs no tocadas: contratos Inventory, Admin, HR, Production, Purchasing y Sales; rutas planned. No nuevos endpoints, permisos, schemas, migraciones ni escrituras entre servicios.

## Gobierno y rollback

Agentes consultados documentalmente, sin delegación: Mantenimiento e Inventarios negocio/técnico; Arquitectura/API/Datos, Seguridad, Sinergia, UX/i18n, QA y Gobierno documental. Skills `erclave-feature` y `erclave-environment-boundaries`.

Restaurar únicamente el código/documentación de CHG-268 conservando CHG-262–267. No borrar la reserva recuperada ni su evidencia. Si el negocio decide desistir, usar la cancelación de solicitud de Maintenance para liberar mediante Inventory; una entrega posterior se revierte mediante el flujo autorizado correspondiente. Local head `20260908_0034`; QA conserva head `20260825_0029` y release `a119ddf`. Sin cambios remotos ni promoción. Pendiente aceptación manual del usuario y liberación gobernada a QA.
