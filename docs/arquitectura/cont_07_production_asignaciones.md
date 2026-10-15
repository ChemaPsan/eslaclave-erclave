# CONT-07 — Asignaciones de Producción por División

CHG-299 · 2026-09-27 · Local aislado, working tree sobre HEAD `213f75c`. Fichas consultadas: Producción, Administración, Costos y Contabilidad negocio/técnica; Arquitectura SaaS/API, Datos/Custodio DB, Seguridad, Sinergia, Diseño/i18n, Manuales y QA. Skills feature, accounting, module-boundaries, migraciones, ambientes, form-contract/form-feedback, evidencia y manuales. Sin delegación ni certificación de QA.

## Alcance y aceptación

Production conserva una División fija por máquina y asignaciones por División para productos/servicios compartidos. No duplica maestros ni convierte textos heredados en referencias. Admin es autoridad de tenant, membresía, módulos, permisos y scope v2; Costing es autoridad del centro predeterminado opcional. Production guarda sus propios datos, auditoría y recibos idempotentes, sin FKs ni escrituras entre schemas.

La asignación inicial de una máquina requiere alcance completo y production.machine.update; una membresía restringida no puede apropiarse de un recurso heredado pendiente. Una máquina ya asignada exige acceso a su División y no permite cambiarla. La relocalización/corrección queda para un flujo explícito futuro. Se exige máquina activa para asignar; mantenimiento/inactiva se rechazan.

Productos y servicios conservan identidad única, con asignaciones activas/inactivas. La consulta elegible exige maestro y asignación activos, División activa/autorizada y búsqueda acotada. Pending approval/inactive no habilitan asignaciones nuevas. Desactivar conserva centro/snapshot sin consultar Costing; reactivar revalida referencias. Scope vacío no concede acceso a asignaciones ajenas. Un wildcard explícito permite lectura histórica, no habilitación de una División inactiva.

Cada API consulta sesión Admin incluso en demo y exige tenant/usuario activos, módulos Admin y Production activos y permiso puntual. La capacidad de catálogo de centros no concede permisos ni activa Accounting/analítica. Centro omitido no consulta Costing. Centro seleccionado exige costing.cost_center.read, catálogo disponible y centro activo en esa División. Se reutiliza el cliente HTTP compartido con fronteras Local/remoto y fallos cerrados.

## Campos y experiencia

| Campo | Tarea y origen | Contrato |
|---|---|---|
| División de máquina | Ubicación organizacional explícita; selector Admin autorizado | Nullable durante expansión; fija tras primera asignación. No inferir de area_name. |
| División de producto/servicio | Disponibilidad del maestro en un contexto | PK tenant/product_service/division, varias asignaciones sin duplicar ficha. |
| Centro predeterminado | Preparación para imputaciones futuras; selector Costing acotado por División | Opcional, ID estable y snapshot de código/nombre. No migrar cost_center textual automáticamente. |
| Estado | Activar/desactivar disponibilidad de la asignación | active/inactive, sin alterar estado del maestro. Desactivación no cambia referencia histórica. |
| Revisión | Evitar sobrescribir cambios concurrentes | expected_revision requerido; 0 al crear; no editable por el usuario. |

UI ES/EN desde tarjetas de Productos y servicios y Maquinaria, sólo modo API, módulo disponible, scope v2 y lectura correspondiente. Escrituras requieren permiso update. Búsqueda con páginas, selección visible, conservación de captura/clave al reintentar, feedback localizado por código/ruta y layout por contenedor de 320px. Cambiar División limpia centro previo. Sin capacidad/permiso de centros se conserva la referencia existente; guardar activa con referencia requiere validación backend. Sociedad/Emisor se derivan, no se capturan.

## Persistencia y recuperación

Alembic `20260927_0042` agrega machines.division_ref_id nullable y division_revision, constraint de coherencia e índice tenant/División; product_service_division_assignments con PK compuesta, FK interna compuesta al maestro, índice tenant/División/estado, centro/snapshot, revisión positiva y timestamps. Unique tenant/id en product_services soporta la FK. Los modelos de organización describen sólo estas columnas de expansión; los repositorios existentes mantienen sus contratos.

Bloqueo del recurso, comparación de revisión, asignación, auditoría before/after/correlación y respuesta idempotente se guardan en una transacción Production. Clave delimitada por recurso/División y hash de actor/payload; repetición devuelve recibo y reutilización con otro payload rechaza. La autorización actual se comprueba antes del replay. El prefijo de operación acotado soporta IDs de longitud máxima sin superar el campo de 120 caracteres.

Sin atomicidad distribuida con cambios simultáneos en Admin/Costing. La validación corresponde al estado observado por solicitud; futuros consumidores deben revalidar antes de producir efectos. La lectura elegible devuelve el centro predeterminado guardado, no garantiza su vigencia futura.

Migración sólo en PostgreSQL loopback `127.0.0.1:5434/erclave_local`, tenant `ten_739ee59d765d5e14818674800d` comprobado. Upgrade/downgrade vacío/upgrade probados. Downgrade toma locks y se niega con asignaciones o auditoría de este recorrido: conservar historia y usar forward-fix. Fixtures PostgreSQL con rollback; sin seeds, backfill, estructura inventada ni asignaciones permanentes.

## APIs afectadas

Nuevas en production-service; escrituras requieren Idempotency-Key y todas requieren tenant y autorización efectiva.

| Método y ruta | Permiso | Request / response |
|---|---|---|
| GET /v1/production/organization/divisions | production.machine.read o production.product_service.read | q, limit 1–25, offset; data id/code/name/society_id y meta. |
| GET /v1/production/machines/{machine_id}/division | production.machine.read | data machine_id, division_ref_id nullable, revision. |
| PATCH /v1/production/machines/{machine_id}/division | production.machine.update | division_ref_id y expected_revision; misma forma con revisión nueva. |
| GET /v1/production/product-services/{product_service_id}/division-assignments | production.product_service.read | division_id opcional, limit 1–100, offset; asignaciones y meta. |
| PUT /v1/production/product-services/{product_service_id}/division-assignments/{division_id} | production.product_service.update | expected_revision, status y cost_center_ref_id nullable; data asignación con revisión/snapshot. |
| GET /v1/production/division-product-services | production.product_service.read | division_id requerido, q, limit 1–25, offset; maestros activos asignados con centro predeterminado y meta. |

Consumidas sin cambio: Admin GET /v1/session/context; Costing GET /v1/cost-centers/{cost_center_id} y GET /v1/cost-centers/eligible; Production GET /v1/production/machines y GET /v1/production/product-services para tarjetas. Permisos de centros costing.cost_center.read; catálogos production.machine.read/product_service.read. No se modifica Accounting ni APIs operativas de recetas/órdenes/Inventory/HR/Sales/Purchasing/Maintenance.

## Evidencia y pendientes

Pruebas y resultados definitivos en TRAZABILIDAD CHG-299; logs chg299-tests.log, chg299-browser.log, chg299-smoke.log y chg299-verify.log. PostgreSQL prueba persistencia con rollback; navegador con interceptores prueba UI ES/EN, errores, permisos y reintentos; smoke Emulator prueba lectura/rechazos reales. No equivale a UAT.

CONT-07 ya incluye Inventory/Production/HR/Sales/Purchasing y condiciones por División. Recetas/órdenes/capacidad dimensionadas siguen pendientes; CHG-308 prepara contexto sin habilitar fabricación. Conservar estos maestros y cerrar CC-10/11/12 de [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). Backfill real, configuración y folios siguen abiertos. Estado de manuales en [REGISTRO](../manuales_solucion/REGISTRO.md); no atribuir QA a este corte Local.
