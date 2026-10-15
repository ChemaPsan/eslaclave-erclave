# Matriz de capacidades organizacionales

**CHG-296 Local:** [CONT-04, infraestructura y primer recorrido de plantilla por alcance](cont_04_configuracion_por_alcance.md), revisión `20260927_0039`. Herencia, override y restauración implementados en Admin; configuración de otros servicios y consumo/snapshots operativos pendientes. No activa Costos ni Accounting.


CHG-296 · 2026-09-27 · Fase 1 aplicada en contrato de sesión. CHG-297 incorpora el catálogo básico [CONT-05](cont_05_catalogo_centros.md); no equivale a analítica de Costos.

El usuario confirmó: catálogo básico en Administración sin activar analítica ni Contabilidad, con Centro de costos obligatorio sólo en flujos de imputación habilitados. Esta decisión sustituye la obligatoriedad incondicional de la preparación anterior. No inventar centros para rellenar datos; conservar referencias históricas.

## Disponibilidad y permisos

| Código de capacidad | Dueño | Disponibilidad del tenant | Permisos de acción | Estado actual |
|---|---|---|---|---|
| organization | admin-service | Admin efectivo | admin.fiscal_issuer.*, admin.society.*, admin.division.* según acción; scope vigente | Implementado Local; capacidades existentes. |
| cost_center_catalog | costing-service | Capacidad básica de Administración; independiente de módulos analíticos | costing.cost_center.read/create/update/status implementados en CONT-05; cada acción valida tenant y División | Implementado Local; requiere flag de despliegue en Admin y Costing, además de Admin activo. |
| costing_analytics | costing-service | Costos efectivo | Permiso puntual del cálculo/reporte futuro | Planned; deshabilitado. |
| accounting | accounting-service | Accounting efectivo | accounting.* puntual por operación futura; configuración y periodo aplicables | Planned; deshabilitado. |

La asociación de catálogo con Admin es de disponibilidad, no ownership ni permiso amplio. CONT-05 extiende la resolución de exactamente los cuatro permisos de ese catálogo para que su módulo técnico Costing no exija habilitar analítica. No modificar todos los permisos Costing para cumplir esta excepción. CHG-297 incorpora los cuatro permisos bajo disponibilidad Admin; otros permisos Costing conservan su módulo.

## Regla por flujo

| Flujo | Centro de costos | Reglas que siempre se conservan |
|---|---|---|
| Crear organización, usuarios o configuración general | No obligatorio por preparación | Tenant, permisos y pertenencia organizacional. |
| Operación sin imputación de Costos/Accounting habilitada | No obligatorio únicamente por preparación | Validaciones propias del módulo; División cuando CONT-07/08 la implemente. |
| Asignar maestro para un flujo de imputación habilitado | Obligatorio en la asignación correspondiente, según CONT-07 | Centro activo de la División; Sociedad derivada; sin duplicar maestro. |
| Consumo, merma, producción, ingreso o gasto con imputación habilitada | Obligatorio en el efecto/línea que corresponda, según CONT-08 y contrato de evento | Validación backend, snapshots, origen y referencias compatibles. |
| Compromiso sin efecto contable, como requisición u orden | No generar póliza por su creación; aplicar imputación presupuestal sólo si existe una política implementada | No inferir reconocimiento ni mapeos. |
| Línea contable con cuenta que requiere centro | Obligatorio al contabilizar | Libro/Sociedad, periodo, balance y referencia válida. |
| Consulta histórica, reversa o devolución | Conservar dimensión y vínculo del origen; reglas de corrección explícitas | No recalcular ni reemplazar dimensiones por configuración actual. |

`enabled_imputation_flows` expresa la política, no activa los flujos. Cada consumidor de CONT-07/08 deberá declarar su condición y validarla en backend. No deducir obligatoriedad sólo de que el menú Contabilidad sea visible, de que exista un centro o de un permiso de lectura.

## Contrato ejecutable de sesión

GET `/v1/session/context` agrega `capability_policy_version: 1`, `cost_center_requirement: enabled_imputation_flows` y `capabilities` por código con `owner_service`, `availability_module`, `implemented`, `available` y `reason`.

Admin calcula estos datos desde el estado del tenant/usuario y los entitlements de la sesión, más la implementación declarada en servidor. No confía en `active_modules` aislado, nombres de roles, parámetros de cliente ni permisos contables para habilitar una capacidad planned. Entitlements ausentes, apagados o duplicados no conceden disponibilidad. Una identidad inactiva no recibe capacidad disponible. No cambia los grants ni el scope del usuario.

`available` no es autorización de una acción, no prueba configuración contable lista y no es un token persistible para jobs. UI, API y procesos futuros deben volver a validar estado, permiso y scope. Crear entidades organizacionales no crea libros. Analítica Costing y Accounting permanecen `not_implemented`; el catálogo básico es independiente y sólo está disponible cuando su runtime se habilita en ambos servicios.

Compatibilidad: campos aditivos; `active_modules`, permisos y scope existentes conservan su formato. Los clientes actuales toleran los campos extra. El contrato de capacidades no exige migración por sí mismo. El piloto CONT-04 del mismo corte aplica la revisión Local 0039 y recarga Admin; evidencia en su documento y TRAZABILIDAD. Pruebas de API con repositorio simulado separadas del smoke HTTP Local con Emulator real.

## Aceptación y continuación

Pruebas: organización con módulos opcionales ausentes; identidad/entitlement apagado; lista active_modules manipulada; duplicados; módulos planned con grants/activación; propiedad Costing y disponibilidad Admin; respuesta HTTP compatible. La disponibilidad nunca sustituye validación por acción.

CONT-04 ya tiene primer recorrido administrativo de plantilla con persistencia propia, herencia visible, override reversible, revisión, auditoría e idempotencia; faltan configuración de otros servicios y consumo operativo con snapshots. CONT-05 ya implementa catálogo y autorización de capacidad básica Local. CONT-07 ya implementa asignaciones y condiciones; CONT-08 es parcial según [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). La asignación de datos existentes sigue pendiente; no bloquea desarrollo independiente.

## APIs afectadas

Modificada Admin GET `/v1/session/context`: sólo campos aditivos de response, autenticación/membresía y query division_id existentes sin cambio; sin permiso nuevo. Consumidas sin cambio: ninguna en este corte. Esa descripción corresponde a CHG-296. CHG-297 agrega esquema/contrato Costing y autoridad de códigos Admin; matriz exacta en CONT-05. APIs operativas y Accounting intactas.
