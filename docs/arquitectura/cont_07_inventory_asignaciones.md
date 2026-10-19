# CONT-07 — Primer recorrido de asignaciones en Inventarios

CHG-298 · 2026-09-27 · Local aislado. Agentes consultados: negocio/técnica de Inventarios, Administración, Costos y Contabilidad; Arquitectura/API, Seguridad, Datos/Custodio DB, Sinergia, Diseño/i18n y QA. Skills feature, accounting, module-boundaries, migraciones, ambientes, form-contract/form-feedback, evidencia y manuales. Fichas consultadas como perspectivas, sin delegación.

## Alcance real

Este corte expande maestros y recursos de Inventory: almacén con División explícita y artículo compartido con asignaciones por División. No duplica artículos, no modifica movimientos previos, no cambia saldos/reservas ni crea efectos contables. No completa CONT-07 para Production, HR, Sales y Purchasing ni CONT-08 para documentos.

Los endpoints operativos y catálogos heredados siguen trabajando por tenant. Sus filtros y comandos NO quedan aislados por División por incorporar estas asignaciones. La consulta nueva de artículos disponibles es el contrato de preparación para consumidores posteriores; la migración y exigencia operativa se harán por flujo con evidencia propia.

## Propiedad y autorización

Inventory escribe sus columnas, asignaciones, auditoría e idempotencia. Admin es autoridad de organización/scope; Costing valida centros por HTTP. Sin escrituras ni FKs cruzadas. Sociedad/Emisor no se capturan: se derivan de División en la autoridad. No se añaden permisos; se usan inventory.warehouse.read/update e inventory.item.read/update por acción.

Cada endpoint nuevo consulta sesión Admin, exige tenant/usuario activos, Admin e Inventory activos, permiso y scope v2. No hay bypass demo. Selección de Divisiones filtra únicamente las efectivas del usuario, con búsqueda y páginas de hasta 25. Un wildcard explícito permite consultar asignaciones históricas de Divisiones inactivas; un usuario restringido sólo consulta sus Divisiones efectivas. Altas/reactivaciones requieren División activa. Un almacén ya asignado exige también acceso a su División actual.

La asignación inicial de un almacén sin dimensiones requiere permiso warehouse.update y alcance completo all_divisions. Así una membresía restringida no puede apropiarse de un recurso heredado cuyo origen aún es desconocido. La División del almacén queda fija; una relocalización o corrección posterior requiere un flujo explícito futuro, no reemplazar IDs desde PATCH.

## Campos y formularios

| Campo / tarea | Origen | Persistencia y regla |
|---|---|---|
| División del almacén | Búsqueda de Divisiones autorizadas; nunca inferida de business_center | warehouses.division_ref_id nullable durante expansión; division_revision 0 pendiente, >0 asignada. Fija tras asignar. |
| División del artículo | Selección explícita o asignación existente | Identidad compuesta tenant/item/division. Un maestro puede tener varias asignaciones sin duplicarse. |
| Centro predeterminado | Selector Costing de activos en la División; ID estable y código/nombre visibles | Referencia opcional y snapshot de código/nombre. Revalidar en backend al guardar una asignación activa. |
| Estado de la asignación | Active/inactive | Desactivar conserva centro/snapshot e historia; no permite sustituir la referencia en ese comando. Reactivar vuelve a validar recurso/División/centro. |
| Revisión | Respuesta del servidor | expected_revision requerido: 0 para alta, revisión vigente para cambio. No editable. |

Centro opcional porque aún no hay flujo de imputación habilitado en este corte. La disponibilidad del catálogo básico no activa analítica/Accounting ni convierte el centro en obligatorio. Si no se envía centro, no se consulta Costing; una dependencia opcional caída no impide la asignación sin centro. Si se envía, se exige capacidad de catálogo y costing.cost_center.read, centro activo y de la misma División. El cliente no ofrece texto libre ni reutiliza una selección de otra División.

Sin permiso/capacidad de centros, la pantalla conserva la referencia existente; activarla con un centro necesita la validación correspondiente. Desactivar permite conservar un centro histórico aunque Costing esté caído. La consulta division-items filtra asignaciones e items activos y División efectiva; cost_center_ref_id es el predeterminado guardado, no una certificación de vigencia futura. Cada consumidor debe revalidar el centro antes de usarlo en un efecto habilitado.

En Almacenes → Almacenes o Artículos, cada tarjeta disponible en modo API/sesión v2 ofrece Asignación por División. El formulario conserva selección/clave ante errores, muestra revisión en conflicto mediante mensaje accionable y oculta escrituras sin permiso. Buscadores acotados, ES/EN y contenedor 320px. Un campo de centro rechazado señala el selector; una División histórica no editable usa resumen, sin inventar un campo corregible.

## Persistencia, concurrencia y migración

Alembic `20260927_0041`: columnas nullable/revisión de warehouses e índice por tenant/División; tabla inventory.item_division_assignments con PK tenant/item/division, revisión positiva, estados acotados, índice tenant/division/status y FK compuesta interna a inventory.items. Sin backfill. El texto heredado business_center sigue compatible y no es autoridad organizacional ni se traduce automáticamente a un ID.

Comandos bloquean el recurso dentro de Inventory, validan revisión, guardan auditoría antes/después, correlación y respuesta idempotente en una transacción. La clave se delimita por recurso/División y el hash incluye actor/payload. Repetición devuelve la misma respuesta; payload distinto rechaza con 409. Sin transacción distribuida con Admin/Costing: se valida el estado observado por solicitud. Los flujos operativos futuros deben revalidar al producir sus efectos.

Aplicada sólo en PostgreSQL `127.0.0.1:5434/erclave_local`, tenant permitido `ten_739ee59d765d5e14818674800d` comprobado. Upgrade, downgrade sin asignaciones y nuevo upgrade verificados. Downgrade bloquea con almacenes asignados, asignaciones o auditoría de este flujo; usar forward-fix. Fixtures sintéticos dentro del tenant con rollback. Sin asignaciones permanentes, seeds ni estructura supuesta. QA/Producción intactos.

La dependencia opcional Costing se consulta sólo al validar un centro seleccionado. Fuera de Local requiere URL HTTPS explícita, sin loopback ni credenciales embebidas; configuración ausente o inválida rechaza sin contactar Local. La UI tampoco usa una URL vacía como ruta relativa. Esto no activa Costing ni Accounting.

## APIs afectadas

Todas las rutas siguientes son nuevas en inventory-service; no cambian los cuerpos de catálogos/movimientos anteriores.

| Método y ruta | Permiso | Request / response |
|---|---|---|
| GET /v1/inventory/organization/divisions | inventory.warehouse.read o inventory.item.read | q, limit 1–25, offset; data con id/code/name/society_id y meta. |
| GET /v1/inventory/warehouses/{warehouse_id}/division | inventory.warehouse.read | data warehouse_id, division_ref_id nullable, revision. |
| PATCH /v1/inventory/warehouses/{warehouse_id}/division | inventory.warehouse.update | division_ref_id, expected_revision, Idempotency-Key; misma respuesta con revisión nueva. |
| GET /v1/inventory/items/{item_id}/division-assignments | inventory.item.read | division_id opcional, limit 1–100, offset; data asignaciones y meta. |
| PUT /v1/inventory/items/{item_id}/division-assignments/{division_id} | inventory.item.update | expected_revision, status, cost_center_ref_id nullable; Idempotency-Key; data con estado/revisión/snapshot. |
| GET /v1/inventory/division-items | inventory.item.read | division_id requerido, q, limit 1–25, offset; artículos activos asignados y centro predeterminado guardado. |

Consumidos sin cambio: Admin GET /v1/session/context (identidad/membresía); Costing GET /v1/cost-centers/{cost_center_id} y GET /v1/cost-centers/eligible (costing.cost_center.read); Inventory GET /v1/inventory/warehouses y GET /v1/inventory/items para tarjetas existentes. Accounting, documentos, movimientos, reservas y APIs de otros módulos no se modifican.

## Evidencia y continuación

Ver TRAZABILIDAD CHG-298 y logs chg298-tests.log, chg298-browser.log, chg298-smoke.log, chg298-verify.log. Browser interceptado prueba UI, PostgreSQL rollback prueba persistencia; smoke HTTP Local con Emulator prueba integración de lectura/rechazos. No equivale a UAT ni prueba que un documento ya esté separado.

Las asignaciones de máquinas/productos, puestos/trabajadores y clientes/proveedores ya están implementadas en sus contratos CONT-07. Continuar consumidores y brechas de [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md), no volver a crear esos catálogos. Backfill real, configuración transversal y folios siguen abiertos. Estado de derivados Word en [registro de manuales](../manuales_solucion/REGISTRO.md).
