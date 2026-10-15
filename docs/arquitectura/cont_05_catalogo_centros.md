# CONT-05 — Catálogo básico de Centros de costos

CHG-297 · 2026-09-27 · Local aislado. Agentes consultados: negocio/técnica de Costos, Administración y Contabilidad; Arquitectura/API, Seguridad, Datos/Custodio DB, Sinergia, Diseño/i18n y QA. Aplican skills feature, accounting, module-boundaries, ambientes, migraciones, form-contract/form-feedback y manuales.

## Capacidad y propiedad

Administración → Organización → Divisiones → Centros de costos presenta el catálogo. `costing-service` (Local 8014) posee `costing.cost_centers`, `command_receipts` y `audit_events`; Admin posee organización, permisos y numeración. No hay escritura ni FK entre schemas. Sociedad y Emisor se derivan de la División, sin campos duplicados.

`ERCLAVE_COST_CENTER_CATALOG_ENABLED` debe estar activo en Admin y Costing; su valor predeterminado es false para no anunciar runtime aún no desplegado. `start_local.ps1` lo habilita y configura `ERCLAVE_COSTING_DATABASE_URL` explícita. El cliente Local usa loopback 8014; otros ambientes requieren `costingApiBaseUrl` explícita. No hay fallback a QA ni a una base de otro servicio.

Exactamente `costing.cost_center.read/create/update/status` pertenecen al catálogo de permisos disponible con Admin. No se reclasifica todo Costing. Cada solicitud consulta sesión Admin, verifica tenant/usuario activos, permiso puntual, capacidad disponible y scope v2. No basta Owner, un header de actor ni activar analítica. El modo demo también consulta la autoridad Admin. UI exige además `admin.division.read` para entrar por Organización.

Analítica de Costos y Accounting permanecen planned/deshabilitados. El manifiesto del módulo analítico no pasa a implemented por este catálogo. Centro obligatorio sólo según el futuro flujo de imputación habilitado; el alta de catálogo no exige centros en documentos actuales ni crea libros/pólizas.

## Comportamiento y formularios

Alta: nombre obligatorio, División fijada por contexto, código automático `CC-000001` mediante autoridad Admin. Edición: sólo nombre, con `expected_revision`. Código y División son inmutables. Estado: activar/desactivar, sin borrar historia. Búsqueda por código/nombre, estado y paginación servidor; consulta elegible sólo devuelve activos de una División vigente y autorizada. Rechaza límite excesivo, scope ajeno, campos extra y código manual.

El scope de sesión contiene Divisiones efectivas activas. Usuarios restringidos pierden acceso cuando la autoridad deja de incluir la División; un wildcard explícito puede consultar historia inactiva, pero no crear/reactivar/seleccionar en una División inactiva. No ampliar ese acceso por rol. Cada solicitud usa el estado observado en Admin; no hay transacción distribuida que bloquee una desactivación concurrente en ambos servicios. Los consumidores futuros deben revalidar elegibilidad antes de sus propios efectos.

Comandos: `Idempotency-Key` requerido, hash de actor/acción/payload/ID, revisión optimista, bloqueo transaccional por tenant, respuesta reproducible y auditoría/receipt atómicos en Costing. Clave reutilizada con otro payload da 409. Admin reserva el código con clave estable derivada del comando; reintento de una respuesta perdida no consume otro número. Una reserva puede sobrevivir a una falla posterior de Costing: se admiten huecos, nunca se recuperan números automáticamente. No se promete atomicidad entre servicios.

UI ES/EN conserva captura y clave al fallar, traduce códigos seguros, mantiene estado confirmado ante transición rechazada, oculta mutaciones sin permiso y se adapta a contenedor 320px. No captura código ni Sociedad/Emisor libres.

## Persistencia y migración

Revisión `20260927_0040`, aditiva, aplicada exclusivamente a `127.0.0.1:5434/erclave_local` tras verificar único tenant `ten_739ee59d765d5e14818674800d`. Claves/índices por tenant, unicidad de código, estado y revisión positivos. Sin backfill ni centro predeterminado. Downgrade sólo con las tres tablas vacías; bloquea si existe historia, usar forward-fix.

Se probaron upgrade, downgrade vacío y nuevo upgrade. Fixtures PostgreSQL con rollback dentro del tenant autorizado. Seed Local de cuatro permisos y asignación al Owner existente mediante comando Admin auditado, preservando permisos/alcances previos; sin activar módulos analíticos. No se crean Sociedades, Divisiones ni centros permanentes ficticios. QA/Producción sin cambios.

## APIs afectadas

| Servicio | Método/ruta | Permiso | Contrato |
|---|---|---|---|
| Costing | GET /v1/cost-centers | costing.cost_center.read | Lista acotada con division_id, q, status, limit, offset; data/meta. |
| Costing | GET /v1/cost-centers/eligible | costing.cost_center.read | division_id obligatorio, sólo activos y División efectiva; máximo 25. |
| Costing | GET /v1/cost-centers/{cost_center_id} | costing.cost_center.read | Identidad, código, nombre, División, estado y revisión. |
| Costing | POST /v1/cost-centers | costing.cost_center.create | name/division_ref_id; Idempotency-Key; 201. |
| Costing | PATCH /v1/cost-centers/{cost_center_id} | costing.cost_center.update | name/expected_revision; Idempotency-Key. |
| Costing | POST /v1/cost-centers/{cost_center_id}/activate | costing.cost_center.status | expected_revision; Idempotency-Key. |
| Costing | POST /v1/cost-centers/{cost_center_id}/deactivate | costing.cost_center.status | expected_revision; Idempotency-Key. |
| Admin | POST /v1/cost-center-codes/next | costing.cost_center.create | Nueva autoridad dedicada; sin captura manual, Idempotency-Key, asignación managed. |
| Admin | GET /v1/session/context | Autenticación/membresía vigente | Forma intacta; catálogo implemented=true, available depende de flag/Admin/identidad. |
| Admin | POST /v1/catalogs/code-sequences/{document_type}/next | Permisos existentes sin ampliar | Misma forma; rechaza costing.cost_center con 422 y remite a autoridad dedicada. |
| Admin | PATCH /v1/catalogs/code-sequences/{sequence_id} | admin.setting.update | Misma forma; no permite modo manual para centros. |

Consumidos sin cambio: GET /v1/organization/divisions desde UI; sesión Admin por cada request de Costing. APIs de Accounting, operaciones de Inventory/Production/HR/Sales/Purchasing/Maintenance sin cambios en este corte. Contratos completos en OpenAPI Admin/Costing.

## Validación y límites

Evidencia final en TRAZABILIDAD CHG-297 y logs chg297-tests.log, chg297-browser.log, chg297-verify.log. Pruebas de navegador interceptadas prueban comportamiento del cliente y no equivalen a UAT del tenant. Smoke HTTP Local sólo lectura y rechazos; sin fixtures de negocio permanentes. Fuente Markdown del manual actualizada; Word pendiente de regeneración y revisión visual.

Continuación: completar CONT-04 en consumidores/configuración de cada dueño, CONT-06 y brechas CONT-08 de [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). CONT-07 asignaciones/condiciones ya está implementado Local; no repetirlo. La estructura real y su mapeo siguen pendientes antes del backfill. Este catálogo no acredita separación operativa completa ni contabilidad implementada.
