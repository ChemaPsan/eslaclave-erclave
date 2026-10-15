# CONT-02 — Administración de la organización

Fecha: 2026-09-25. Corte CHG-292, sólo Local. Dueños: microfrontend Administración, admin-service y schema `admin`. Continúa [CONT-01](cont_01_estructura_organizacional.md); continuado por [CONT-03 implementado](cont_03_sesion_alcances.md). Pendientes vigentes en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md).

## Resultado y límites

Administración → Organización ofrece Emisores, Sociedades y Divisiones con búsqueda, paginación, alta, edición y activación/desactivación. Un Emisor tiene varias Sociedades; cada Sociedad exige un único Emisor y moneda base del catálogo Admin, inicialmente MXN. Cada División exige Sociedad. Datos fiscales y contactos se guardan en Emisor; no se duplican en el formulario de Sociedad.

Las tablas normalizadas pasan a ser autoridad por tenant mediante un marcador explícito. `organization.profile` queda como proyección compatible; conserva IDs heredados y campos extendidos. El perfil corporativo continúa editable. Los formularios/API antiguos siguen disponibles y deprecados; sus comandos actualizan las tablas y reconstruyen la proyección en la misma transacción. No existe eliminación física de estos maestros.

Este corte no implementa libros, asientos, transacciones en moneda extranjera, Centros de costos, asignaciones operativas ni alcance por División. La sesión conserva temporalmente su contrato de sucursales. CONT-03 implementará alcance/selección activa y CONT-05 el alta de Centros de costos en Administración mediante Costing. Los datos fiscales opcionales no certifican habilitación CFDI.

## Contrato de formularios

| Formulario / campo | Tarea y fuente | Alta / edición / lectura |
|---|---|---|
| Todos: código | Identidad visible administrada por `admin.code_sequences`; EMI/SOC/DIV con seis dígitos por defecto | Inmutable tras alta. Capturable únicamente si la secuencia está en modo manual; el listado informa `meta.code_mode`. Secuencia creada al primer alta; se configura con el catálogo existente de consecutivos. No se consume un número hasta guardar con éxito. |
| Emisor: razón social | Identificar entidad fiscal | Obligatoria, 1–240 caracteres; modificable y visible. |
| Emisor: RFC/identificación fiscal | Evitar duplicar la misma entidad fiscal dentro del tenant | Opcional para conservar preparación e importaciones incompletas. Se normaliza a mayúsculas; duplicado no vacío rechazado. No se impone RFC mexicano a emisores de otros países. |
| Emisor: régimen, uso CFDI, domicilio | Conservar configuración fiscal existente | Opcionales; régimen/uso hasta 80, domicilio hasta 2000 caracteres. No se inventa un catálogo fiscal nuevo. |
| Emisor: CP y país fiscal | Completar localización fiscal | Opcionales; CP hasta 20, país de dos letras mayúsculas. Persistencia nueva en revisión 0038. |
| Emisor: nombre, correo, teléfono, puesto del contacto | Reutilizar los contactos existentes | Opcionales; hasta 240 caracteres salvo teléfono 80. El formulario valida formato de correo. |
| Sociedad: nombre | Identificar unidad de gestión y futuro libro | Obligatorio 1–240; sin recapturar razón social/RFC. |
| Sociedad: Emisor | Elegir su único emisor fiscal | ID obligatorio; búsqueda de activos por código/nombre, máximo 10 resultados. El servicio comprueba tenant y estado. Edición conserva referencia si no cambia. |
| Sociedad: moneda base | Configurar moneda del futuro libro | Código obligatorio del catálogo Admin activo, MXN inicial. Edición conserva moneda anterior al no cambiarla. No se crean afectaciones contables. |
| División: nombre y Sociedad | Identidad y pertenencia organizacional | Obligatorios; búsqueda de Sociedades activas, máximo 10. ID estable; muestra identidad visible. |
| División: domicilio, teléfono | Conservar datos operativos de sucursal | Opcionales, hasta 2000/80 caracteres. |
| Todos: estado | Controlar disponibilidad sin eliminar historial | Activo al crear; acciones separadas para activar/desactivar, con permiso de estado. |
| Corporativo | Mantener datos generales existentes del tenant | Panel desplegable; sigue usando `PUT /v1/settings/{key}` y permiso existente. |

Los listados consultan 25 registros por página, admiten `q`, `status`, `parent_id`, `limit` máximo 100 y `offset`. La UI sólo muestra catálogos con permiso de lectura y acciones autorizadas. Crear una relación requiere lectura del catálogo padre; crear Sociedad requiere lectura de monedas. Editar permite mantener referencias sin ese permiso, pero no elegir otras. Búsqueda fallida, validación 422/409 y fallo desconocido mantienen captura, enlazan rutas de campo conocidas y no muestran diagnósticos del servidor. Una clave de idempotencia se conserva al reintentar el mismo payload; cambiarlo genera otra clave. No hay reintento automático de comandos.

CSS está limitado a `.organization-panel`, usa tokens de marca y container queries a 600 px. No cambia componentes de otros módulos. Textos ES/EN en `frontend/i18n/organization.js`; errores estables en el catálogo transversal.

## Persistencia, transición y recuperación

Revisión `20260925_0038`, padre `20260922_0037`: dos columnas opcionales de Emisor y tabla `admin.organization_authorities`. El marcador tiene PK/FK por tenant, hashes del origen y de la proyección, origen original completo, snapshot anterior archivado si se reconcilió, operador y fecha de activación. No hay FK ni escritura entre schemas de servicios.

1. El CLI Local realiza preview del perfil original y exige hashes de origen/plan y operador para `--activate`. Sólo acepta el tenant `ten_739ee59d765d5e14818674800d` en loopback:5434/erclave_local, sin overrides por querystring.
2. Bajo el mismo lock por tenant de CONT-01, revalida el origen. Si existe snapshot preparado, compara tablas y equivalencias con su plan revisado. No sobrescribe tablas editadas fuera del flujo.
3. Si sólo cambió el origen, archiva snapshot/tablas anteriores y reconstruye el destino en la misma transacción. Referencias huérfanas o identidad fiscal compartida requieren las resoluciones explícitas existentes; no se infieren.
4. Activa autoridad, audita el cambio y genera la proyección. Las tablas vacías y un origen vacío pueden activarse al primer comando: no hay identidades que inferir.
5. Cada comando normalizado o adaptado toma lock, verifica que la proyección no fue alterada fuera del servicio, valida la clave/payload, escribe tablas, auditoría y proyección, y completa idempotencia dentro de la misma transacción.
6. Repetir activación exige hashes revisados y proyección intacta. Una diferencia se rechaza; no se “repara” sobrescribiendo silenciosamente.

Las equivalencias mantienen IDs antiguos al cambiar el padre. La proyección conserva extensiones del perfil y de sus registros. Al editar datos fiscales desde `legal-entities`, un Emisor compartido produce conflicto: se debe editar desde Emisores para evitar una modificación fiscal implícita de otras Sociedades.

CP/país fiscal existentes como extensiones se promueven a las columnas nuevas al activar, manteniendo el plan histórico CONT-01. Valores incompatibles entre alias requieren revisión; nunca se descartan al reconstruir la proyección.

No se puede desactivar un Emisor con Sociedades activas, ni una Sociedad con Divisiones activas. Crear, activar o reasignar un hijo exige padre activo del mismo tenant. Las dependencias con asignaciones operativas futuras se incorporan en sus cortes correspondientes. `PUT settings/organization.profile` no puede reemplazar las colecciones normalizadas; un tenant con organización activada/importada no puede borrarse físicamente desde Backoffice, devuelve conflicto para conservar historial.

El downgrade 0038 funciona sólo con marcador vacío y sin CP/país capturados; después de activar exige corrección hacia adelante. El downgrade 0037 sigue bloqueando tablas pobladas. Recuperación: conservar snapshots/auditoría, conciliar la diferencia identificada y aplicar una corrección revisada; no borrar organización viva ni restaurar un JSON obsoleto. El snapshot archivado no es un botón de rollback de datos nuevos.

## APIs afectadas

Todas las rutas siguientes pertenecen a **admin-service**, requieren autenticación y tenant activo con Administración habilitada. Mutaciones nuevas requieren `Idempotency-Key`; `X-Correlation-Id` es opcional. Respuestas de alta/edición/estado: `{data: registro}`; listados: `{data: [...], meta: {total,limit,offset,code_mode}}`. Todos los IDs se resuelven dentro del tenant, nunca por ID global.

### Contratos nuevos

| Método | Ruta | Permiso | Request / response |
|---|---|---|---|
| GET | `/v1/organization/fiscal-issuers` | `admin.fiscal_issuer.read` | Filtros y página de Emisores. |
| POST | `/v1/organization/fiscal-issuers` | `admin.fiscal_issuer.create` | Razón social, código manual opcional y campos fiscales/contacto; devuelve Emisor. |
| GET | `/v1/organization/fiscal-issuers/{record_id}` | `admin.fiscal_issuer.read` | Emisor del tenant. |
| PATCH | `/v1/organization/fiscal-issuers/{record_id}` | `admin.fiscal_issuer.update` | Campos fiscales/contacto modificados; código no editable. |
| POST | `/v1/organization/fiscal-issuers/{record_id}/activate` | `admin.fiscal_issuer.status` | Sin body; devuelve Emisor activo. |
| POST | `/v1/organization/fiscal-issuers/{record_id}/deactivate` | `admin.fiscal_issuer.status` | Sin body; valida dependientes. |
| GET | `/v1/organization/societies` | `admin.society.read` | Filtros y página de Sociedades con nombre de Emisor. |
| POST | `/v1/organization/societies` | `admin.society.create` | Nombre, único `issuer_id`, `base_currency` MXN por defecto y código manual opcional. |
| GET | `/v1/organization/societies/{record_id}` | `admin.society.read` | Sociedad del tenant. |
| PATCH | `/v1/organization/societies/{record_id}` | `admin.society.update` | Nombre/Emisor/moneda modificados; no admite null ni código. |
| POST | `/v1/organization/societies/{record_id}/activate` | `admin.society.status` | Sin body; exige Emisor activo. |
| POST | `/v1/organization/societies/{record_id}/deactivate` | `admin.society.status` | Sin body; valida Divisiones activas. |
| GET | `/v1/organization/divisions` | `admin.division.read` | Filtros y página de Divisiones con nombre de Sociedad. |
| POST | `/v1/organization/divisions` | `admin.division.create` | Nombre, `society_id`, domicilio/teléfono y código manual opcional. |
| GET | `/v1/organization/divisions/{record_id}` | `admin.division.read` | División del tenant. |
| PATCH | `/v1/organization/divisions/{record_id}` | `admin.division.update` | Nombre/Sociedad/domicilio/teléfono modificados; identidad obligatoria. |
| POST | `/v1/organization/divisions/{record_id}/activate` | `admin.division.status` | Sin body; exige Sociedad activa. |
| POST | `/v1/organization/divisions/{record_id}/deactivate` | `admin.division.status` | Sin body; conserva historial. |

### Contratos existentes con comportamiento compatible actualizado

| Método | Ruta | Permiso conservado | Cambio |
|---|---|---|---|
| POST | `/v1/organization/legal-entities` | `admin.setting.update` | Deprecado. Adaptador crea Emisor y Sociedad, proyecta respuesta heredada. |
| PATCH | `/v1/organization/legal-entities/{legal_entity_id}` | `admin.setting.update` | Deprecado. Adaptador; bloquea edición fiscal de Emisor compartido. |
| POST | `/v1/organization/legal-entities/{legal_entity_id}/activate` | `admin.setting.update` | Deprecado. Estado de Sociedad con validación de padre. |
| POST | `/v1/organization/legal-entities/{legal_entity_id}/deactivate` | `admin.setting.update` | Deprecado. Estado de Sociedad con validación de dependientes. |
| POST | `/v1/organization/branches` | `admin.setting.update` | Deprecado. Adaptador exige Sociedad y crea División. |
| PATCH | `/v1/organization/branches/{branch_id}` | `admin.setting.update` | Deprecado. Actualiza División conservando ID legado. |
| POST | `/v1/organization/branches/{branch_id}/activate` | `admin.setting.update` | Deprecado. Activa División con padre activo. |
| POST | `/v1/organization/branches/{branch_id}/deactivate` | `admin.setting.update` | Deprecado. Desactiva División. |
| PUT | `/v1/settings/{key}` | `admin.setting.update` | Para organization.profile protege arrays normalizados; admite datos corporativos y conserva extensiones. Request/response sin cambio. |
| DELETE | `/v1/backoffice/tenants/{tenant_id}` | Allowlist Backoffice existente | Conflicto `organization_tenant_in_use` si existe autoridad/importación; no borra el historial. Request/response de éxito sin cambio. |

**Compatibilidad de autorización:** `admin.setting.update` conserva deliberadamente su capacidad histórica mediante estos ocho adaptadores durante la transición. Los doce permisos nuevos gobiernan las rutas normalizadas. Retirar adaptadores o migrar permisos/scopes heredados exige un corte explícito; no interpretar un rol con `admin.setting.update` como sólo lectura de organización. Todos los adaptadores mantienen aislamiento y reglas de dominio normalizadas.

### Consumidas sin cambio

`GET /v1/session/context` (sesión autorizada), `GET /v1/settings?module_code=admin` (`admin.setting.read`), `GET /v1/catalogs/commercial/currencies?include_inactive=true` (`admin.catalog.read`) y `GET /v1/catalogs/code-sequences` (`admin.setting.read`) siguen formando parte del dashboard. La UI corporativa consume el PUT anterior. No se modificaron contratos ni runtime de Production, Inventory, HR, Sales, Purchasing, Maintenance, Costing o Accounting en CHG-292.

## Evidencia Local

Base de trabajo `213f75c` más cambios locales no confirmados; no equivale a un SHA publicado. Tenant permitido: `ten_739ee59d765d5e14818674800d`. Migración 0038 aplicada en loopback:5434/erclave_local. Preview real sin Emisores/Sociedades/Divisiones; autoridad activada con hashes revisados, sin inventar datos de negocio. Doce permisos nuevos sincronizados y concedidos exclusivamente al Owner de ese tenant. Admin reiniciado en 8000 con Firebase Emulator demo-erclave, no con QA.

| Caso | Precondición / pasos | Esperado y observado | Evidencia / alcance |
|---|---|---|---|
| CONT02-DB | Tenant Local; transacción revertida. Crear Emisor, dos Sociedades, División; editar/reasignar/desactivar/reintentar | Un único Emisor por Sociedad, MXN activo, búsqueda paginada, proyección y auditoría atómicas; conflictos con campos estables; mismo comando no duplica | 94 pruebas focalizadas aprobadas incluyendo CONT-00/01 y CONT-02; 27 integraciones PostgreSQL revertidas. `test_organization_commands.py`, `test_organization_migration.py`, `test_organization_preflight.py`. |
| CONT02-MIG | Preparar JSON y shadow sintéticos; cambiar origen, activar y reintentar; manipular destino/proyección; downgrade vacío y con autoridad | Archiva snapshot, preserva IDs/extensiones, rechaza destino/proyección modificados y downgrade con datos | Incluido en pruebas focalizadas. No demuestra migración de un conjunto productivo real. |
| CONT02-AUTH | TestClient con roles controlados, 18 operaciones; sin token, tenant ajeno de sólo lectura, permiso incorrecto | 401/403/404 según frontera; `admin.setting.update` no autoriza rutas nuevas; schema rechaza IDs/valores inválidos | Dobles sólo de identidad/contexto. Pruebas positivas de API usan repositorio/PostgreSQL reales con rollback. |
| CONT02-UI | Chrome con APIs simuladas; ES/EN, tres formularios, guardar/reintentar/editar, referencias, 409/500, doble envío | Conserva captura y foco/ARIA, payload estable, referencias limitadas, no muestra SQL; vista móvil sin desbordamiento | 12 pruebas aprobadas en `organization.spec.js`, log local `chg292-browser.log`. |
| CONT02-LOCAL | Owner del demo, login contra Firebase Auth Emulator y lecturas reales de Admin; formularios vacíos en escritorio/móvil | Tres catálogos y formularios disponibles; validación requerida sin escritura de negocio; cuatro lecturas organizacionales 200 y cero errores JavaScript | Capturas locales `.local/cont02-{fiscal-issuers,societies,divisions}-{desktop,mobile}.png`; el adaptador del SDK Firebase usa REST real del emulador. No se persistieron altas sintéticas mediante browser. |

Los resultados anteriores no actualizan aceptación QA/UAT. No se conectó ni desplegó QA/Producción. Gates generales y comprobación final se registran en [TRAZABILIDAD](../../TRAZABILIDAD.md).

Regresión completa: `npm.cmd run test:form-feedback` aprobó 119 pruebas con APIs simuladas. `npm.cmd run verify` aprobó validadores (incluidos documentación, responsive y OpenAPI), compilación y 380 pruebas backend; 85 integraciones omitidas en ese comando sin DB. Las 27 organizacionales de esas omisiones pasaron por separado; las otras 58 no se reejecutaron contra PostgreSQL en este corte.
