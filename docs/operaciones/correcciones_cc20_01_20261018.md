# Correcciones posteriores a CC20-01 · CHG-333 · 2026-10-18

Evidencia histórica de este corte Local. Fuentes vigentes: [estado](../contexto/ESTADO_ACTUAL.md), [pendientes](../contexto/PENDIENTES.md) y [matriz CC-20](cc20_aceptacion_integrada_local.md). El usuario pidió resolver los tres pendientes antes de continuar; CC20-02 no se ejecutó en este corte.

## Eliminación de usuarios

INC-CC20-01-DELETE-01 corregida solo en Local. `DELETE /v1/users/{user_id}` retira roles y membresía del tenant en una transacción y conserva `admin.users` para las referencias históricas de auditoría. Si ya no existe ninguna membresía, deja la identidad global `disabled`. No borra auditoría ni referencias de autor.

Después del commit se intenta limpiar Firebase bajo un bloqueo de la fila global del usuario. Se revalida si existen otras membresías o una reinvitación. Las invitaciones y el onboarding provisionan su identidad dentro de la sección protegida por el mismo bloqueo; la regresión concurrente comprobó que una invitación espera antes de tocar Firebase. Se conserva el permiso `admin.user.delete` y la autorización se ejecuta también antes del replay.

La respuesta añade `data.firebase_identity_cleanup`, con `status` (`completed`, `pending`, `not_required`) y `error_codes`. Un fallo del proveedor se registra como limpieza pendiente en el recibo existente de `admin.command_idempotency`; la membresía ya retirada no recupera acceso. El mismo `Idempotency-Key` permite reintentar. El recibo vincula usuario y actor; un replay antiguo no retira la membresía reinvitada ni borra su identidad. La UI avisa de la limpieza pendiente en español e inglés. El worker automático de reintentos sigue fuera de este corte.

No hay cambio de esquema ni migración: se usan estados, tablas y bloqueos existentes, con head `20261014_0062`. La autenticación de prueba fue Firebase Auth Emulator `demo-erclave`, APIs y PostgreSQL en loopback; tenant exclusivo `ten_739ee59d765d5e14818674800d`. No hubo acceso QA/Producción ni activación Accounting.

## Manuales

La diferencia de las fuentes 01 Producción y 04 Ventas era exclusivamente LF frente a CRLF. Los textos coincidían con HEAD; las huellas aprobadas correspondían a CRLF. Se restauraron esos bytes sin alterar contenido, Word ni registro.

| Fuente | SHA256 nuevamente coincidente con el registro | Cotejo textual nuevo contra Word |
|---|---|---|
| `01_produccion.md` | `9d7f7bb0a0738c51dfb80f367fee49e700bdaab134789a7cacd991e3ccd7d7a2` | 154 párrafos, 4 tablas / 33 filas |
| `04_ventas_clientes.md` | `45b0da8abc1720f284660a7679fdb20db7f491c68543f2f5983f3c87f77407ab` | 142 párrafos, 2 tablas / 15 filas |

ZIP y XML comprobados íntegros. No hubo render nuevo porque ambos DOCX conservaron exactamente sus bytes; la revisión visual CHG-331 permanece como evidencia histórica, no una nueva revisión en este corte.

## Trazabilidad

CHG-323–331 ya existían en HEAD, al inicio del archivo, con encabezados de nivel 2 y orden descendente. Los lectores exigían nivel 3 y orden ascendente: el diagnóstico previo de registros ausentes era incorrecto. Se movieron los bloques originales completos después de CHG-322 y se normalizaron sus encabezados, sin reconstruir contenido ni inventar pruebas. CC20-01 quedó como CHG-332 y este corte como CHG-333.

## Validación y evidencia

| Comprobación ejecutada | Resultado y alcance |
|---|---|
| API Admin focal | 91 pruebas aprobadas, 1 warning de dependencia. Incluye clave ausente, falta de permiso, error local antes de Firebase, identidad compartida y respuesta pendiente. |
| Repositorio PostgreSQL | 6 casos aprobados, 1 warning, rollback exclusivo del tenant permitido. Auditoría, replay/conflictos, pendiente → reintento, reinvitación protegida y fallo de provisioning. Firebase controlado por callbacks en estos casos. |
| Regresión integrada Local | 16 comprobaciones aprobadas con HTTP autenticado, PostgreSQL y Firebase Emulator reales. DELETE auditado 200; identidad eliminada, auditoría conservada, replay único, clave rechazada para otro usuario; carrera con dos conexiones reales y bloqueo observado en `pg_stat_activity`; reinvitación conserva identidad tras replay antiguo. |
| UI ES/EN | 4 casos aprobados. Login/dashboard Local; SDK de test conectado al Emulator y DELETE simulado para usuario solo en memoria. Aviso pending accesible; 500 conserva usuario y no anuncia éxito ni expone diagnóstico backend. No son una nueva aceptación CC20-16. |

Evidencia integrada: `.local/chg333-20261018222644/{http.json,result.json}`. Scripts de ensayo y reinicio: `.local/chg333_user_lifecycle.py`, `.local/restart_admin_chg333.ps1`. Logs focales: `.local/chg333-admin-api.log`, `.local/chg333-user-deletion-postgres.log`, `.local/chg333-browser.log`. HEAD observado `26e6bb61d5deb73a1965f95a67570d8615fc56e2` más el delta Local de este corte; no se hizo commit ni publicación. Estos artefactos `.local` permanecen ignorados por Git.

Se usaron dos identidades sintéticas propias para la prueba integrada. Ambas terminaron sin membresía, con identidad Firebase eliminada y registro global deshabilitado conservado para auditoría. Los fixtures PostgreSQL focales se revirtieron; las pruebas UI no escribieron usuarios reales. El alcance del Owner original quedó igual. Se reinició únicamente Admin Local para cargar el código corregido.

Gate final aprobado: `npm run verify` terminó con todos los validadores, compilación y backend **751 passed, 250 skipped, 1 warning**, 38.18 s de pytest en la corrida general sin DB. Las 250 omisiones no se cuentan como aprobaciones; los seis casos PostgreSQL focales sí se ejecutaron aparte. Warning existente de Starlette/httpx. `validate:documentation` aprobó contra head Local0062, QA documentado0036 y CHG-333; `git diff --check` pasó. Log: `.local/chg333-verify.log`.

## APIs afectadas

| Clasificación | Servicio, método y ruta | Permiso y contrato |
|---|---|---|
| Contrato modificado | Admin `DELETE /v1/users/{user_id}` | `admin.user.delete`; request sin cambio. Response añade `firebase_identity_cleanup.status/error_codes`; replay durable ligado a actor/usuario, 409 por clave incompatible. |
| Comportamiento interno, payload sin cambio | Admin `POST /v1/users/invitations` | `admin.user.invite`; provisioning protegido por bloqueo, mismos request/response. |
| Comportamiento interno, payload sin cambio | Admin `POST /v1/provisioning/tenant-onboarding` | Allowlist Backoffice existente; mismo bloqueo para provisioning del Owner. No se creó otro tenant en las pruebas. |
| Consumidos sin cambio | Admin `GET /v1/session/context`, `GET /v1/roles`, `PUT /v1/users/{user_id}/organization-scope` | Membresía/alcance, `admin.role.read`, `admin.user.update`; setup y comprobación del ensayo. |
| Consumidos sin cambio | Firebase Auth Emulator: signup, signin, gestión de identidad | Únicamente `demo-erclave` y usuarios sintéticos Local. |
| No tocadas | Contratos Inventory, Production, Sales, Purchasing, Maintenance, RH, Costing y Accounting | Ninguna modificación contractual. |
