# CONT-03 — Sesión y alcance organizacional

Corte CHG-293, Local. Admin posee membresías y organización; frontend shell muestra el contexto y Administración edita el alcance. No cambia el esquema PostgreSQL: usa `admin.memberships.metadata` existente y conserva revisión Alembic `20260925_0038`.

## Contrato y semántica

`scope.version=2` agrega Sociedades, Divisiones y Emisores visibles, identificadores efectivos, revisión y selección activa. Sólo se devuelven identificadores/nombres/códigos necesarios, no datos fiscales privados. División activa se valida mediante `GET /v1/session/context?division_id=...`; Sociedad y Emisor se derivan. Tenant/usuario inactivos o División fuera del alcance se rechazan. Crear una División no amplía una membresía restringida.

La membresía guarda `society_ids` y `division_ids`. Listas vacías significan acceso operativo por División vacío; `['*']` declara acceso total, incluidas futuras Divisiones. Un wildcard de Divisiones requiere wildcard de Sociedades. Una concesión sólo de Sociedad no incorpora automáticamente todas sus Divisiones. No se usa el nombre Owner para saltar estas reglas. Los permisos del rol y el alcance son controles diferentes.

Se filtran Divisiones o ancestros inactivos. La referencia a Sociedad restringe también una División trasladada: no se concede la nueva Sociedad por conservar el ID de División. Las respuestas v2 nunca fabrican una sucursal Matriz. Tenants sin autoridad organizacional activada conservan el contrato v1; una membresía ya v2 en ellos obtiene alcance vacío hasta la activación revisada.

`branches`, `branch_ids` y `all_branches` se mantienen como proyección para consumidores heredados, preservando IDs de sucursal/razón social mediante equivalencias. Estos aliases no son una nueva autoridad de escritura.

## Migración y recuperación

`backend/scripts/organization_scopes_local.py` sólo admite loopback:5434/erclave_local y el tenant `ten_739ee59d765d5e14818674800d`. Preview de sólo lectura entrega hash y cambios de concesión. Apply exige hash y operador, toma lock organizacional y locks de membresías, conserva `scope_legacy`, metadata ajena y auditoría. Identidades sin equivalencia o metadata malformada se rechazan antes de escribir. La conversión completa es transaccional y la repetición de un preview vacío no escribe.

La semántica histórica sin restricciones o con lista vacía equivalía a todas las sucursales: la conversión la hace wildcard explícito, sin conceder algo que antes estuviera restringido. La lectura compatible traduce los IDs mientras se aplica la conversión; antes de mover recursos entre Sociedades se debe completar la migración para congelar las concesiones. Las nuevas invitaciones se crean con alcance v2 vacío; reinvitación, onboarding repetido y seeds conservan el alcance existente. Ningún arranque debe borrar su versión/revisión.

Rollback funcional: corregir alcance mediante el editor auditado. No restaurar metadata completa de un respaldo viejo sobre cambios posteriores ni volver a un runtime que interprete listas v2 vacías como acceso total. No hay downgrade Alembic en este corte.

## Formulario y contexto activo

| Control | Tarea / contrato | Persistencia y error |
|---|---|---|
| Alcance restringido o total | Decisión administrativa explícita; no se deduce del rol. | PUT versionado; vacío permitido y explicado. |
| Búsqueda de División | Agregar una referencia estable; máximo 10 resultados por consulta; lectura `admin.division.read`. | Sociedad derivada de la referencia; referencias existentes permanecen aunque no estén en resultados. |
| Divisiones asignadas | Revisar o quitar concesiones actuales por identidad visible. | Backend revalida tenant, estado y pertenencia. |
| Selector de contexto | Sociedad / División en una sola etiqueta; evita doble captura incompatible. | Preferencia por tenant y usuario; API confirma División y deriva Sociedad/Emisor. Selección inválida se descarta al refrescar. |

**CHG-329 · Local:** el selector de contexto de la barra superior usa un botón propio y una lista visible con Sociedad, División y código. El antiguo buscador genérico quedaba comprimido y recortaba la lista. El botón anuncia la selección activa, muestra foco y permite cerrar con Escape; al elegir otra División consulta la sesión autorizada antes de guardar la preferencia. Centro de costos no es una selección global de sesión: se administra por División y se consume en los flujos de imputación pertinentes.

El editor requiere `admin.user.read` para consultar y `admin.user.update` para guardar. `expected_revision` impide sobrescribir una edición concurrente; auditoría y clave de idempotencia se guardan en la misma transacción. Repetir el mismo payload conserva clave; cambiarlo genera otra. ES/EN, indicador compartido, captura preservada, fallback general seguro para arrays de referencias y CSS aislado por formulario. Un conflicto pide reabrir para revisar la versión vigente.

## APIs afectadas

| Clase | Método / ruta | Servicio / permiso | Cambio |
|---|---|---|---|
| Modificado | GET `/v1/session/context` | Admin; contexto de identidad/membresía (`internal.session.context.read` documentado) | Query opcional `division_id`; response scope v2 y selección derivada; aliases v1 conservados. |
| Nuevo | GET `/v1/users/{user_id}/organization-scope` | Admin / `admin.user.read` | Configuración versionada, revisión y referencias seleccionadas. |
| Nuevo | PUT `/v1/users/{user_id}/organization-scope` | Admin / `admin.user.update` | Version 2, expected_revision, society_ids, division_ids; responde nueva revisión. Requiere Idempotency-Key. |
| Comportamiento compatible | POST `/v1/users/invitations` | Admin / `admin.user.invite` | Misma request/response; nueva membresía con alcance vacío, reinvitación lo conserva. |
| Comportamiento compatible | POST `/v1/provisioning/tenant-onboarding` | Admin / permiso interno de provisioning existente | Misma request/response; conserva metadata/alcance de membresía existente. |
| Consumido sin cambio | GET `/v1/organization/divisions` | Admin / `admin.division.read` | Búsqueda acotada de referencias activas para el editor. |

Las APIs operativas de Production, Inventory, HR, Sales, Purchasing y Maintenance no cambian en este corte. En el corte CHG-293 sus documentos todavía no aplicaban dimensiones; CONT-07 y varios recorridos CONT-08 ya las incorporaron después. **CONT-03 no certifica separación operativa completa**. Catálogo CONT-05 implementado; configuración y consumidores permanecen parciales según [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). Accounting sigue planned.

## Cobertura y guardianes

Fichas consultadas: Administración negocio/técnica, Contabilidad negocio/técnica, Arquitectura SaaS/API/Datos, Custodio DB, Seguridad, Sinergia, Diseño/i18n, QA/Release y Manuales. Sin delegación. Skills feature, ambientes, migraciones para conversión de metadata, contrato/feedback, evidencia, accounting y module-boundaries. La auditoría de agentes está en [cobertura](cobertura_agentes_modulos.md); no sustituye pruebas de cada módulo.

Evidencia ejecutada, resultados y límites se registran en CHG-293 de `TRAZABILIDAD.md` y `docs/contexto/ESTADO_ACTUAL.md`. Pruebas PostgreSQL usan exclusivamente fixtures del tenant permitido con rollback; browser interceptado no equivale a UAT ni smoke QA.
