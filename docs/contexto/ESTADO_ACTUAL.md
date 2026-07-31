# Estado actual de ERClave

Ultima actualizacion: 2026-07-31.

## Ambiente local

- Frontend estatico local esperado en `http://127.0.0.1:4173`.
- Admin API local conectada a QA en `http://127.0.0.1:8000` para la validacion funcional autorizada.
- Production API local esperada en `http://127.0.0.1:8002`.
- Inventory API local esperada en `http://127.0.0.1:8004`.
- PostgreSQL portatil aislado para Inventory escucha en `127.0.0.1:5434`, base `erclave_local`.
- Firebase autentica; `admin-service /v1/session/context` resuelve tenant, membresia, modulos, permisos y alcance.

## Cortes funcionales relevantes

### Administracion y permisos

- El editor de permisos de roles trabaja con borrador explicito, busqueda, filtros, agrupacion por modulo/recurso, seleccion masiva visible y resumen de cambios; no incluye plantillas ni presets.
- Los nombres tecnicos se conservan como identificadores de policy, pero la interfaz usa nombres y descripciones ES/EN mantenidos en `admin.permissions`.
- El catalogo remoto requiere tenant y `admin.role.read`; solo expone permisos `tenant` asignables y marca disponibilidad segun el entitlement del modulo.
- Modificar permisos exige `admin.role.permissions.manage`, `expected_revision` e `Idempotency-Key`. El backend aplica diferencias, conserva scopes heredados sin permitir crear nuevos scopes arbitrarios y audita altas/bajas.
- Los grants historicos internos pueden conservarse como relacion para no perder trazabilidad, pero ya no ingresan a `session/context` ni producen autorizacion efectiva. El owner conserva un piso administrativo y no puede inactivarse.
- El payload anterior `permission_ids + scope` permanece compatible y esta deprecado; la interfaz nueva usa `assignments + expected_revision`.
- Mientras un ambiente no tenga `admin.role.permissions.manage`, Roles permite abrir `Ver permisos` en modo de solo lectura y explica por que la edicion permanece bloqueada; no aplica fallback de escritura inseguro.
- La revision vigente es `20260730_0011`; agrega metadata de permisos, revision por rol y registro de comandos idempotentes. El 2026-07-31 se promovio a `erclave_qa` con respaldo previo, seed idempotente ejecutado dos veces y validaciones posteriores aprobadas.

### Produccion

- Productos y servicios se presentan como catalogo maestro antes de consultar ordenes relacionadas.
- Recetas y ordenes cuentan con integracion local/API documentada en trazabilidad.
- Areas y puestos pertenecen al modulo independiente Recursos Humanos, con microfrontend y `hr-service` propios.
- El entitlement `hr` controla la disponibilidad por tenant; alta y edicion usan permisos separados `hr.area.*` y `hr.position.*`.
- El esquema `hr` incorpora aislamiento por tenant, FK compuesto area-puesto, idempotencia y auditoria. El 2026-07-31 se creo vacio en QA mediante la promocion autorizada de migraciones; no se desplego `hr-service` ni se activaron entitlements adicionales.
- PostgreSQL QA conserva seis permisos `hr.*` activos y los permisos `production.labor.*` heredados inactivos. Los catalogos `hr.labor_areas` y `hr.labor_roles` quedaron en cero registros.
- El contrato de production-service esta preparado, pero la persistencia API de areas y puestos sigue pendiente de implementacion backend; no se presenta como remota.
- Las recetas en modo API ya no usan el catalogo fijo de materiales: consumen articulos activos marcados `use_in_recipe` y balances reales de Almacenes.

### Almacenes e inventarios

- `inventory-service` es propietario de almacenes, articulos, movimientos, balances y Kardex.
- El submodulo visible `Inventario` conserva el identificador tecnico `existencias`.
- Inventario consume balances enriquecidos con busqueda, filtros, orden y paginacion server-side.
- La vista usa container queries: colapsa el flujo por defecto, transforma la tabla en tarjetas cuando el panel central se estrecha y mueve Alertas debajo del contenido en viewports intermedios.
- Los movimientos registrados y no reversados son la fuente de verdad.
- `available_quantity = on_hand_quantity` y `reserved_quantity = 0` hasta implementar Reservas.
- La bandera `inventory.items.use_in_recipe` pertenece a la migracion `20260730_0009`; la cabeza acumulada `20260730_0011` fue aplicada en QA el 2026-07-31 con autorizacion explicita. Los catalogos `inventory.warehouses`, `inventory.items` e `inventory.movements` permanecieron en cero registros.
- Inventario muestra con saldo cero los articulos sin movimientos que tengan almacen sugerido.
- La validacion local cubrio 10,000 articulos y 10,000 movimientos; consultar `docs/operaciones/validacion_volumen_inventario_local.md`.

### Interfaz transversal

- El shell, los modulos activos, los catalogos, formularios y modales comparten reglas responsive basadas en el ancho real de su contenedor.
- La guia descriptiva conserva el patron compartido de riel vertical izquierdo y compresion; solo pasa a una columna en anchos estrechos o mediante una excepcion explicita de pantalla.
- En anchos intermedios las colecciones reducen columnas; en anchos estrechos formularios y acciones se apilan sin ocultar su significado.
- El backoffice transforma sus filas de tenants y consumo en tarjetas etiquetadas cuando su panel se estrecha.
- La navegacion movil conserva los submodulos activos, foco visible, salto al contenido y anuncios accesibles de notificaciones.
- `npm.cmd run validate:responsive` protege los contenedores, puntos de accesibilidad y referencias documentales obligatorias.

## Calidad

- La fuente de verdad del resultado automatizado es la ultima ejecucion de `npm.cmd run verify`.
- En el corte CHG-161: 116 pruebas backend aprobadas, una integracion PostgreSQL condicionada omitida en la suite estandar y validada previamente por separado; todos los validadores pasaron.
- El repositorio puede contener cambios locales no confirmados; `session:context` debe mostrar el estado Git real de cada sesion.
- `npm.cmd run session:context` reconstruye la memoria operativa sin mostrar secretos: Git, trazabilidad, migraciones, estado, decisiones, tenants, pendientes y puertos locales.
- `validate-session-context.js` protege la presencia de los documentos y guardrails obligatorios.
- `validate-responsive-ui.js` protege el estandar transversal de interfaz para futuras sesiones.

Este archivo debe describir hechos comprobados, no planes ni aspiraciones.
