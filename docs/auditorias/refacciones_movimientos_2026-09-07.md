# Refacciones desde Movimientos de Almacen — CHG-263

Estado: implementado y verificado en Local. QA conserva el release CHG-254.

## Criterios de aceptacion

1. Una solicitud de Mantenimiento aparece en Movimientos junto a la bandeja existente de producto terminado, antes del historial. Muestra orden, tecnico asignado, almacen y todas las partidas/cantidades.
2. Consultar exige `inventory.movement.read`; autorizar/entregar o rechazar exige `inventory.movement.create`. No se requiere leer la orden tecnica. Ambos modulos deben estar activos.
3. La confirmacion entrega la solicitud completa al tecnico asignado y registra la salida en ese momento. Rechazar exige motivo y libera reservas sin salida; una entrega iniciada no se rechaza.
4. Resolver Mantenimiento exige solicitudes entregadas/canceladas y no vuelve a descontar. Conciliar una orden tampoco consume; Almacen reintenta entregas desde su bandeja.
5. Reintentos y concurrencia no duplican movimientos. Una falla parcial queda visible como pendiente, conserva partidas confirmadas y no produce un mensaje de exito.
6. La UI conserva ES/EN, confirmacion, lectura sin acciones, estado vacio/error, paginacion server-side y ancho real del contenedor. La clase exclusiva `warehouse-parts-queue` apila tarjetas/partidas con container query hasta 560 px y evita elipsis en nombres/cantidades; no modifica otras pantallas.

## Ownership y decisiones

- Maintenance sigue siendo propietario de la solicitud y de su orquestacion. Inventory es el unico escritor de reservas y salidas. La pantalla de Almacenes consume una proyeccion minima via el cliente `frontend/api/maintenance.js`.
- Se reutilizan los permisos existentes de Movimientos para esta salida interna. No cambian roles, catalogo de permisos, schema ni revision Alembic; el permiso de recepcion de producto terminado continua separado.
- Autorizar y entregar es una confirmacion unica. No se implementa una aprobacion previa independiente ni captura de cantidades parciales. El receptor es el tecnico asignado por RH en la orden y queda como ID/nombre snapshot en el evento de autorizacion. El actor de Almacen queda tambien en las salidas Inventory.
- El rechazo se conserva como `cancelled` con un evento `maintenance.material_request.reject` y motivo; no introduce un nuevo estado de base.
- Las reservas nuevas de Mantenimiento sin fecha explicita no expiran mientras se espera al almacenista. Se usa `expires_at` nullable existente; las demas fuentes conservan sus reglas. No se reactivan reservas historicas vencidas.

## Concurrencia y recuperacion

El lock de sesion PostgreSQL por tenant/solicitud cubre preparacion, llamada externa y confirmacion. Entrega, rechazo, cancelacion y conciliacion de reservas del tecnico comparten ese lock. La conexion libera el lock al salir y PostgreSQL lo libera si termina la sesion. Una llamada competidora obtiene `command_in_progress`; no ejecuta otro efecto externo.

Antes del primer consumo se persiste `processing/issue`. Los resultados se guardan por ID de partida, no por la posicion de una lista que puede haber cambiado. Un error conserva `needs_reconciliation/issue`; el reintento selecciona solo partidas aun reservadas. Tambien puede reanudar `processing/issue` tras una interrupcion del proceso.

Inventory recibe la clave estable `maintenance-{order_id}-consume-{line_id}`. Si la salida ocurrio pero su respuesta se perdio, la repeticion devuelve el mismo movimiento. La confirmacion de una solicitud ya `issued` no vuelve a llamar a Inventory. La verificacion de origen de la reserva se hace antes de devolver incluso un replay de consumo/liberacion.

Crear solicitudes y resolver comparten un lock de fila de la orden para evitar una nueva solicitud entre la comprobacion de materiales y el cambio definitivo a resuelta.

## Compatibilidad

- Las solicitudes existentes `reserved` pasan a la bandeja sin backfill. Las existentes `issued|cancelled` conservan historia y no aparecen pendientes.
- Las operaciones heredadas `needs_reconciliation/issue` se reintentan con las claves originales. Una orden que conserve un error de integracion tecnico requiere su conciliacion posterior; entregar no libera una maquina por inferencia.
- Las reservas historicas vencidas no se reactivan ni se fuerza stock. Antes de la entrega, una solicitud reservada puede cancelarse y solicitarse nuevamente. Un caso heredado ya en emision con una reserva no consumible requiere revision operativa antes de promover.
- La entrega parcial elegida por el almacenista, devoluciones, aprobacion separada, conciliacion automatica y carga sostenida quedan pendientes. La paginacion usa `limit/offset`, con el orden de creacion e ID.
- Rollback: restaurar conjuntamente el codigo y contratos de este corte preservando CHG-262. No ejecutar downgrade; no revertir movimientos emitidos. Antes de volver al flujo anterior, conciliar las solicitudes con operaciones pendientes.

## APIs afectadas

### Contratos modificados

| Servicio | Metodo y ruta | Permiso | Cambio |
|---|---|---|---|
| Maintenance | `GET /v1/maintenance/warehouse-material-requests` | `inventory.movement.read` | Nuevo. `limit` 1..100 (50 por defecto), `offset` >=0; devuelve `data` con proyeccion y `page` con `has_more`. |
| Maintenance | `POST /v1/maintenance/material-requests/{id}/issue` | `inventory.movement.create` | Nuevo. Sin body o `{}`; rechaza campos extra. Devuelve solicitud `issued` o conciliacion pendiente. |
| Maintenance | `POST /v1/maintenance/material-requests/{id}/reject` | `inventory.movement.create` | Nuevo. Body `reason` recortado, 3..500 caracteres; devuelve cancelacion o conciliacion pendiente. |
| Maintenance | `POST /v1/maintenance/orders/{id}/transitions` | `maintenance.order.{transition}` | Mismo request/response; `resolve` exige `issued|cancelled` y no consume. |
| Maintenance | `POST /v1/maintenance/orders/{id}/reconcile` | `maintenance.order.reconcile` | Mismo request/response; ya no consume materiales. Las entregas las reintenta Almacen. |
| Inventory | `POST /v1/inventory/reservation-requests` | `production.order.release`, `sales.order.fulfill`, `maintenance.material_request.create` | Mismo request/response; origen Maintenance sin fecha explicita conserva `expires_at=null`, sin default de 24 horas. |
| Inventory | `POST /v1/inventory/reservations/{id}/consume` | Segun origen: `production.order.start|resume`, `sales.delivery.confirm`, `inventory.movement.create` | Mismo request/response. Maintenance exige la cantidad completa y autoridad de Almacen; resolver no concede consumo. |
| Inventory | `POST /v1/inventory/reservations/{id}/release` | Segun origen: `production.order.cancel`, `sales.order.cancel`, `maintenance.material_request.cancel` o `inventory.movement.create` | Mismo request/response. Almacen solo libera origen Maintenance; no puede liberar una reserva Maintenance consumida. |

Los comandos exigen tenant, autorizacion e `Idempotency-Key`; la entrega usa ademas identidad estable de solicitud/reserva/partida para el efecto.

### Endpoints consumidos sin cambio contractual

- Maintenance: `GET /v1/maintenance/orders` (`maintenance.order.read`); `POST /v1/maintenance/orders/{id}/material-requests` (`maintenance.material_request.create`); `POST /v1/maintenance/material-requests/{id}/cancel` (`maintenance.material_request.cancel`, ahora serializado con entrega); `POST /v1/maintenance/material-requests/{id}/reconcile` (`maintenance.material_request.reconcile`).
- Inventory: `GET /v1/inventory/movements` (`inventory.movement.read`), `GET /v1/inventory/balances` (`inventory.balance.read`) al invalidar/refrescar vistas. La bandeja de producto terminado y sus endpoints se conservan.
- Admin: `GET /v1/session/context` para identidad, membresia, permisos y modulos. No cambia su contrato.

### APIs no tocadas

No se modifican endpoints de Admin, RH, Production, Purchasing, Sales, Backoffice ni modulos futuros. El smoke reutiliza altas/lecturas/transiciones existentes de RH, Production e Inventory para sus fixtures sinteticas.

## Agentes consultados y ambiente

Consulta documental de las fichas de negocio/tecnica de Mantenimiento e Inventarios; Arquitectura SaaS/API, Seguridad, Sinergia, UX/i18n, QA y Gobierno documental de `AGENTES.md`. Sin delegacion a subagentes. Skills aplicadas: `erclave-feature` y `erclave-environment-boundaries`; instrucciones de migracion revisadas, sin cambio estructural necesario.

Operacion `local-write`: PostgreSQL `127.0.0.1:5434/erclave_local`, APIs loopback y Firebase Auth Emulator `demo-erclave:9099`. Tenant exclusivo `ten_739ee59d765d5e14818674800d`. Pruebas con fixtures acotadas y limpieza de sus propios IDs. El smoke verifica el tenant de la sesion antes de escribir y ya no limpia fixtures de ejecuciones ajenas previas. No hay seeds, migraciones, escrituras remotas, despliegue, commit, push ni PR.

## Validacion

- `npm.cmd run verify:local` aprobado: validadores, contratos OpenAPI/runtime, sintaxis, compilacion, **290 pruebas backend PostgreSQL sin omisiones** y **30 pruebas de navegador**.
- `backend/pyproject.toml` ahora incluye Compras y Mantenimiento en la coleccion por defecto. Antes sus suites se podian ejecutar por ruta, pero no formaban parte de `verify` sin argumentos.
- Smoke HTTP real `backend/scripts/smoke_maintenance_local.py` aprobado: maquina, RH, orden, reserva, bandeja, bloqueo de resolver antes de entregar, entrega, repeticion sin duplicado, resolucion y cierre. Confirma exactamente una salida por las 2 unidades de la fixture y limpia sus propios registros.
- Nuevas regresiones demuestran permisos/entitlements, aislamiento, cantidad completa, origen de reserva, motivo de rechazo, lock concurrente, interrupcion tras preparacion y recuperacion parcial sin repetir partidas confirmadas.
- Cinco pruebas de navegador cubren bandeja junto a recepciones, confirmacion, rechazo, fallos parciales, lectura sin acciones y ES/EN en un contenedor de 520 px. Capturas revisadas visualmente; las mutaciones de estas pruebas son interceptadas.
- `git diff --check` y `npm.cmd run validate:documentation` aprobados. No hay cambio de cabeza Alembic ni recursos remotos.
