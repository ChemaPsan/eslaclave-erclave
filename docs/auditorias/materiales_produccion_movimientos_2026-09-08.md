# Materiales de Produccion desde Movimientos — CHG-264

Implementado solo en Local. Peticion: Almacen debe dar salida a materias primas/materiales antes de iniciar la orden de produccion o servicio. Se conserva el trabajo CHG-262/263.

## Comportamiento

1. Crear/liberar una orden con receta valida y reserva materiales, como antes.
2. La orden aparece en **Almacenes → Movimientos → Solicitudes de materiales para produccion**, junto a recepciones y refacciones. Muestra folio, responsable, materiales, cantidades, unidades y almacenes del snapshot autoritativo de asignacion; no expone costos, receta completa ni diagnosticos.
3. Almacen confirma **Autorizar y entregar** para todas las reservas. Inventory emite las salidas; Production conserva referencias y costo real sin cambiar el estado de la orden.
4. Solo despues puede pasar de Liberada/En espera de recursos a **En produccion** (`in_progress`). Una orden sin materiales no requiere entrega. Reanudar, avanzar etapas y completar no descuentan otra vez.
5. Cancelar antes de entregar libera reservas. Cancelar despues conserva salidas; no afirma devolucion. Una entrega iniciada e incompleta exige conciliar desde Almacen antes de cancelar.

Incluye ordenes de productos y servicios con receta dentro de Production. Las ordenes comerciales de servicio de Sales conservan su ciclo sin materiales; no se agrega un dominio nuevo de solicitudes a Sales.

## Fronteras, datos y recuperacion

- `local-write`, PostgreSQL `127.0.0.1:5434/erclave_local`, Firebase Emulator `demo-erclave`, tenant `ten_739ee59d765d5e14818674800d`. No conexiones ni escrituras QA/Produccion.
- Revision `20260908_0031`: `production.material_issues`, FK interna compuesta por tenant/orden, indice de pendientes, referencias externas en JSONB. Sin permisos nuevos, backfill, seeds ni escrituras entre schemas de servicios.
- Lock PostgreSQL de sesion por tenant/orden serializa entrega y transiciones durante las llamadas HTTP sin mantener una transaccion abierta. `processing` se persiste antes del primer consumo; `needs_reconciliation` conserva respuestas completas; `issued` solo cuando todos los materiales tienen cantidad/costo confirmado.
- Clave Inventory estable `production-order-{order_id}-material-start-consume-{reservation_id}`; persiste por reserva y permite recuperar un corte entre consumo y confirmacion local. El plan y las cantidades provienen de reservas, nunca del navegador. El actor autorizado y el responsable designado quedan auditados; los movimientos conservan su actor emisor.
- Inventory exige `inventory.movement.create` para origen productivo y cantidad total. El permiso de iniciar/reanudar ya no otorga salida. Sales mantiene consumo parcial por su propio permiso. Nuevas reservas Production/Maintenance sin fecha explicita no expiran automaticamente; no se reactivan historicas.
- El panel carga por permiso de lectura de movimientos y ambos modulos activos, con limit/offset, carga/vacio/error, confirmacion, reintento, ES/EN y adaptacion al contenedor. Invalida ordenes, movimientos y balances tras entregar.

## APIs afectadas

| Servicio / metodo / ruta | Permiso | Request / response y cambio |
|---|---|---|
| Production `GET /v1/production/warehouse-material-requests` | `inventory.movement.read`; Production+Inventory activos | Nuevo. `limit` 1..100 (25), `offset` >=0; `data` proyeccion minima y `page{limit,offset,has_more}`. |
| Production `POST /v1/production/orders/{order_id}/issue-materials` | `inventory.movement.create`; ambos modulos | Nuevo. Idempotency-Key >=8; sin body o `{}`, campos extra rechazados. `data` con estado reservado/procesando/conciliacion/entregado, responsable y partidas. 403 autoridad/modulo, 404 orden ajena/inexistente, 409 estado/lock/reservas. Fallo de dependencia conserva estado recuperable. |
| Production `PATCH /v1/production/orders/{order_id}/status` | Permiso puntual existente de start/resume/cancel y otras transiciones | Payload/response conservados. Inicio exige entrega ya registrada; no consume. Cancelacion serializada con entrega y bloqueada durante conciliacion. |
| Inventory `POST /v1/inventory/reservations/{id}/consume` | `inventory.movement.create` para production_order/maintenance_order; `sales.delivery.confirm` para sales_order | Payload/response conservados; autoridad por origen y cantidad completa para materiales internos. |
| Inventory `POST /v1/inventory/reservation-requests` | `production.order.release`, `sales.order.fulfill`, `maintenance.material_request.create` existentes | Payload/response conservados. Nuevas reservas productivas sin expires_at no vencen a las 24h. |

Consumidas sin cambio contractual: Inventory `POST /v1/inventory/reservations/{id}/release` (`production.order.cancel`), disponibilidad/reserva al liberar; Admin `GET /v1/session/context` (identidad/membresia/entitlements), consultas existentes de movimientos y balances (sus permisos Inventory), catalogos Production/RH del flujo de liberacion. UI llama HTTP solo desde `frontend/api/production.js`.

APIs no tocadas en CHG-264: Maintenance (CHG-263 preservado), Sales, Purchasing, HR, Admin, recepcion de producto terminado y Backoffice. No hay notificacion externa ni aprobacion adicional fuera de la entrega completa.

## Validacion

`npm.cmd run verify:local` aprobado (296 backend y 33 browser); tras ampliar parametrizacion de cantidad completa/sin vencimiento a Production, `npm.cmd run verify:postgres` aprobado con 297 pruebas sin omisiones. Validadores, contratos, compilacion, sintaxis y documentacion aprobados. Upgrade/downgrade vacio/upgrade comprobados. PostgreSQL cubre bloqueo de inicio, entrega parcial, reintento sin duplicado, costo/actor, aislamiento, lock y recuperacion tras preparar. Browser cubre permisos, reintento, confirmacion por teclado y ES/EN en contenedor estrecho; capturas revisadas.

`backend/scripts/smoke_production_warehouse_local.py` aprobado con Firebase Emulator y servicios HTTP reales: inicio bloqueado, bandeja, entrega, repeticion con nueva clave, orden aun Liberada, inicio posterior y costo real 40; exactamente dos salidas por cuatro unidades. Los builders de pruebas crean fixtures locales; los comandos entrega/inicio son HTTP reales. Limpieza por IDs propios en finally, sin tocar datos del usuario. Sin seeds, QA/Produccion, despliegues, commit, push ni PR.

## Pendientes y rollback

Entrega parcial elegida, rechazo productivo, devoluciones, receptor diferente al responsable, carga sostenida y conciliacion automatica no forman parte del corte. Revisar reservas historicas vencidas e intentos anteriores al cambio antes de promocion; no se compensan ni reactivan por inferencia. Un resultado incierto permanece bloqueado para no permitir inicio sin trazabilidad.

Rollback: preservar CHG-262/263. Conciliar entregas iniciadas y conservar movimientos/auditoria antes de restaurar el codigo anterior. El downgrade elimina solo el registro de coordinacion y su constraint; no revierte salidas fisicas. No usar downgrade con operaciones pendientes o evidencia sin resguardar. QA conserva revision `20260825_0029`.

Agentes consultados documentalmente: negocio/tecnica Production e Inventory, Sinergia, Arquitectura SaaS/API/Datos, Custodio DB, Seguridad, UX/i18n, QA y Gobierno documental en `AGENTES.md`. Sin delegacion. Skills erclave-feature, erclave-environment-boundaries y erclave-db-migration.
