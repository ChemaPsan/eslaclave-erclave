# Infraestructura preparada para QA

Esta carpeta declara la configuracion necesaria para preparar el candidato. No autoriza ni ejecuta infraestructura, migraciones, seeds o despliegues por si misma.

## Identidades

`identity-plan.json` reemplaza la cuenta de computo predeterminada por identidades separadas para Admin, Produccion, Inventory, RH, Ventas, Compras, Mantenimiento, migraciones y GitHub Actions. La autenticacion del pipeline usa Workload Identity Federation; no se almacenan llaves JSON.

Antes de aprovisionar se debe revisar el plan con el usuario aprobador y conceder cada rol mediante una actividad `qa-write` independiente.

Antecedente histórico del 2026-08-23 (no inventario vigente): las siete cuentas originales, Artifact Registry `erclave-qa` y el provider WIF limitado a `ChemaPsan/eslaclave-erclave` estan aprovisionados. Compras y Mantenimiento ya forman parte del release documentado de siete servicios; consultar [ESTADO_ACTUAL](../../docs/contexto/ESTADO_ACTUAL.md). Cualquier cambio de IAM se verifica y autoriza por separado. Admin runtime conserva `roles/firebaseauth.admin` porque Backoffice crea, actualiza y elimina identidades Firebase durante el ciclo de vida de tenants; no concede autorizacion ERClave ni acceso a datos operativos. La identidad desplegadora cuenta con `roles/firebasehosting.admin` para publicar exclusivamente mediante el gate `qa-frontend`. No se permiten llaves JSON del pipeline.

## GitHub Environments obligatorios

Cada environment debe requerir aprobacion directa del propietario:

- `qa-build`: publica imagenes candidatas en Artifact Registry.
- `qa-database`: ejecuta la migracion aprobada y, con una confirmacion independiente, reconcilia catálogo global y grants de owners de sistema existentes de un tenant explícito, sin seeds ni reset de datos/entitlements.
- `qa-services`: crea revisiones candidatas. En servicios existentes conserva el trafico vigente; el bootstrap de un servicio inexistente recibe trafico inicial porque Cloud Run no admite `--no-traffic` durante la creacion.
- `qa-traffic`: mueve el trafico despues del smoke.
- `qa-frontend`: publica el artefacto exacto en Firebase Hosting.

Estado comprobado el 2026-08-08: los cinco environments existen y requieren aprobacion de `ChemaPsan`; las variables enumeradas abajo estan configuradas en el repositorio.

## Variables del repositorio

| Variable | Valor esperado o fuente |
|---|---|
| `QA_GCP_PROJECT_ID` | `erclave` |
| `QA_GCP_REGION` | `us-central1` |
| `QA_ARTIFACT_REPOSITORY` | Repositorio Artifact Registry QA aprobado |
| `QA_WORKLOAD_IDENTITY_PROVIDER` | Provider OIDC limitado a `ChemaPsan/eslaclave-erclave` |
| `QA_DEPLOY_SERVICE_ACCOUNT` | Correo de `erclave-github-deployer-qa` |
| `QA_MIGRATOR_SERVICE_ACCOUNT` | Correo de `erclave-migrator-qa` |
| `QA_ADMIN_RUNTIME_SERVICE_ACCOUNT` | Correo de `erclave-admin-qa` |
| `QA_PRODUCTION_RUNTIME_SERVICE_ACCOUNT` | Correo de `erclave-production-qa` |
| `QA_INVENTORY_RUNTIME_SERVICE_ACCOUNT` | Correo de `erclave-inventory-qa` |
| `QA_HR_RUNTIME_SERVICE_ACCOUNT` | Correo de `erclave-hr-qa` |
| `QA_SALES_RUNTIME_SERVICE_ACCOUNT` | Correo de `erclave-sales-qa` |
| `QA_PURCHASING_RUNTIME_SERVICE_ACCOUNT` | Correo de `erclave-purchasing-qa` |
| `QA_MAINTENANCE_RUNTIME_SERVICE_ACCOUNT` | Correo de `erclave-maintenance-qa` |
| `QA_COSTING_RUNTIME_SERVICE_ACCOUNT` | Cuenta dedicada `erclave-costing-qa`; aprovisionamiento y grants mínimos por autorización propia |
| `QA_COSTING_API_URL` | Origen HTTPS de `costing-service-qa`, catálogo básico sin activar analítica |
| `QA_CONFIGURATION_TENANT_ID` | Tenant existente aprobado para reconciliar grants de owners; sin default implícito |
| `QA_CONFIRMED_SOCIETY_CURRENCIES` | JSON de IDs reales de todas las Sociedades activas y moneda explícitamente revisada; requerido por el guard operativo antes de tráfico |
| `QA_CLOUD_SQL_CONNECTION_NAME` | `erclave:us-central1:erclave-qa-postgres` |
| `QA_ADMIN_API_URL` | URL HTTPS estable de Admin QA |
| `QA_PRODUCTION_API_URL` | URL HTTPS estable de Produccion QA |
| `QA_INVENTORY_API_URL` | URL HTTPS estable de Inventory QA |
| `QA_HR_API_URL` | URL HTTPS estable de RH QA |
| `QA_SALES_API_URL` | URL HTTPS estable de Ventas QA |
| `QA_PURCHASING_API_URL` | URL HTTPS estable de Compras QA |
| `QA_MAINTENANCE_API_URL` | URL HTTPS estable de Mantenimiento QA |
| `QA_BACKOFFICE_ADMIN_EMAILS` | Allowlist separada por comas de administradores internos; no concede roles dentro de tenants |
| `QA_FIREBASE_*` | Configuracion web publica del proyecto Firebase `erclave` |

`QA_FIREBASE_API_KEY` se publica en el artefacto frontend y tambien se entrega como `ERCLAVE_FIREBASE_WEB_API_KEY` exclusivamente a Admin. Admin la usa con Identity Toolkit para enviar el correo de restablecimiento al owner durante onboarding; no reemplaza la identidad runtime ni los permisos Firebase Admin.

El secreto `erclave-database-url-qa` permanece exclusivamente en Secret Manager y se monta por referencia. Su valor no pertenece a GitHub.

## Flujo

El procedimiento transversal y la matriz de autorizaciones viven en `docs/operaciones/flujo_local_a_qa.md` y la skill `$erclave-qa-release`.

1. `qa-candidate.yml` exige SHA completo, validacion local equivalente y confirmacion `BUILD_ERCLAVE_QA`; construye ocho imágenes (incluye Costing básico), registra digests y construye una vez el frontend sanitizado con SHA256SUMS.
2. `qa-release.yml` exige el SHA, el run candidato, `PROMOTE_ERCLAVE_QA` y confirmaciones booleanas separadas para migracion y configuracion del tenant.
3. `qa-database` aplica Alembic solamente si su input está habilitado y fue aprobado; configuración es un paso condicional independiente. Un job sin ambos pasos no escribe DB.
4. El job de configuración exige `QA_CONFIGURATION_TENANT_ID` existente/activo y rol owner de sistema existente. En una transacción sincroniza catálogo global, depreca códigos y concede permisos tenant a esos owners sólo para módulos efectivos y Admin (incluye cuatro permisos de centros). Conserva usuarios, membresías, roles personalizados, entitlements, perfil y organización; no ejecuta seed demo ni carga datos funcionales. Los siete módulos operativos y el catálogo básico son capacidades distintas de analítica Costing/Accounting.
5. `qa-services` crea revisiones etiquetadas `candidate`; usa `--no-traffic` en servicios existentes y una excepcion explicita e idempotente para el primer despliegue de un servicio inexistente. Esa primera revision recibe trafico por una restriccion de Cloud Run, antes de que exista un frontend QA promovido que la consuma.
6. Deploy, smoke y tráfico usan el mismo `release_sha` inmutable del candidato. `/ready` remoto consulta DB y compara head Alembic con la imagen; una URL configurada no prueba readiness. Se validan ambiente, SHA y URLs públicas; todas las dependencias reales deben usar HTTPS QA, incluidas Costing y Sales desde Production/Inventory.
7. `qa-traffic` requiere otra aprobacion. Descarga `certified-qa-revisions-<SHA>` producido por smoke en qa-services y el manifiesto de imágenes aprobado. Antes de escribir compara las ocho revisiones exactas, imagen/digest resuelto, SHA, URL y tráfico estable con lo certificado; un tag movido o cambio estable entre gates bloquea sin mutar. Revalida identidad/tráfico durante aplicación y al terminar; verifica cada revisión certificada al100% y revierte los servicios ya intentados si falla.
8. `qa-frontend` descarga el artefacto del candidato, verifica SHA256SUMS y despliega exactamente ese directorio sin reconstruir. Preflight ya verificó run exitoso/procedencia/SHA y coincidencia de las ocho URLs con variables actuales. Verificar contenido servido y registrar rollback Hosting.
9. `qa-admin-backoffice-config.yml` corrige la allowlist de Admin sin reconstruir imagenes: `qa-services` crea una revision sin trafico sobre la imagen certificada y `qa-traffic` la promueve solamente si imagen, version, configuracion y revision de rollback siguen coincidiendo.

Evidencia histórica CHG-191, sustituida por releases posteriores: la variable esta configurada y el run `31661213987` promovio `admin-service-qa-bo-1-1` al 100%; rollback `admin-service-qa-00017-dih`. La prueba funcional autenticada administrador permitido/owner ordinario `403` debe repetirse con sesion renovada y sin almacenar credenciales.

GitHub Pages queda como maqueta manual y ya no se publica automaticamente al cambiar `main`.

## Guard operativo y configuración sintética en revisión · CHG-335

Tras desplegar candidatos y pasar smoke, `erclave-operational-preflight-qa` ejecuta `check_qa_operational_readiness.py` en transacción READ ONLY. Exige tenant explícito, autoridad/proyección organizacional coherente, una cadena Emisor/Sociedad/División activa, monedas confirmadas por ID, scopes efectivos resolubles y un Owner operativo con permisos básicos. Su fallo bloquea `qa-traffic`; no configura ni activa datos. El Admin candidato a 0% permite aplicar después una configuración expresamente aprobada sin sustituir todavía el tráfico estable. Costing nuevo conserva su excepción de primer arranque, que requiere autorización propia.

Las migraciones 0037/38 son DDL y no activan la organización. El usuario confirmó el19oct2026 el [plan sintético](synthetic-organization-plan.json) y pidió su ejecución por etapas: un emisor sin datos fiscales, dos Sociedades MXN/USD, tres Divisiones y tres centros, preservando datos QA previos. Antes de escribir deben completarse baseline/IDs/hashes y revisión de cualquier perfil legado no vacío; no usar moneda implícita ni copiar Local. [Ejecución CHG-336](../../docs/operaciones/promocion_qa_20261019.md). Si hay legacy, el CLI Local no habilita QA: preparar transición gobernada tras revisar mapping.

El frontend se verifica después de publicar con `tools/verify-qa-hosting.js`: compara los archivos realmente servidos por erclave.web.app con las huellas del artefacto inmutable. Un fallo de esa verificación deja release fallido y exige evaluar/restaurar la versión Hosting previa registrada.

### URL Costing antes del primer build

El frontend del candidato requiere `QA_COSTING_API_URL` antes de construir imágenes; no inventar el sufijo opaco de las siete URLs existentes ni desplegar un seed para descubrirlo. Resolver por lectura el número del proyecto `erclave` y registrar el origen determinista `https://costing-service-qa-PROJECT_NUMBER.us-central1.run.app`, según la [documentación oficial de URLs HTTPS de Cloud Run](https://docs.cloud.google.com/run/docs/triggering/https-request). Revisar ese valor junto con la identidad/variable antes de qa-build. Tras el bootstrap aprobado, comprobar ese origen público con health/ready/version y comportamiento autenticado antes de autorizar tráfico/frontend. Si no corresponde al servicio/proyecto/región aprobados, detener el release y volver a construir el candidato con la configuración corregida; no reconstruir sólo el frontend ni cambiar URLs después de certificarlo.

## Rollback

- Servicios: reasignar trafico a las revisiones anteriores registradas antes del release.
- Frontend: restaurar el release previo de Firebase Hosting.
- Backoffice Admin: devolver 100% del trafico a `rollback_revision` registrado por el artefacto del workflow de configuracion.
- Datos: usar restauracion o `forward-fix`; no ejecutar downgrade despues de admitir escrituras sin una decision explicita.


## Historia de releases (no instrucciones pendientes)

Los cortes siguientes se conservan como antecedentes. El [estado vigente documentado](../../docs/contexto/ESTADO_ACTUAL.md) prevalece; esta revisión no consultó infraestructura remota.

### Candidato de continuidad CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


### Release QA verificado CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff de ese corte: `docs/contexto/REANUDACION_CHG269.md`; retomar hoy desde [INICIO_SESION](../../docs/contexto/INICIO_SESION.md). Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.

### Preparación histórica CHG-275

Candidato Local CHG-271–275: manuales/formularios, margen sin tope de 100% y evidencia de servicios. Plan de ese corte: `docs/operaciones/release_qa_20260914.md`. En ese corte QA seguía en b63cdad; destino Alembic 0036. Configurar y verificar bucket privado dedicado y QA_EVIDENCE_BUCKET antes de promover Production. 29 integraciones históricas requieren corregir fixtures/autorización; no declarar certificación completa ni ejecutar la suite DB indiscriminadamente. Sin despliegue remoto en esta preparación.
