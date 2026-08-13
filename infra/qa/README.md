# Infraestructura preparada para QA

Esta carpeta declara la configuracion necesaria para preparar el candidato. No autoriza ni ejecuta infraestructura, migraciones, seeds o despliegues por si misma.

## Identidades

`identity-plan.json` reemplaza la cuenta de computo predeterminada por identidades separadas para Admin, Produccion, Inventory, RH, migraciones y GitHub Actions. La autenticacion del pipeline usa Workload Identity Federation; no se almacenan llaves JSON.

Antes de aprovisionar se debe revisar el plan con el usuario aprobador y conceder cada rol mediante una actividad `qa-write` independiente.

Estado comprobado el 2026-08-12: las seis cuentas dedicadas, Artifact Registry `erclave-qa` y el provider WIF limitado a `ChemaPsan/eslaclave-erclave` estan aprovisionados. La identidad desplegadora cuenta con `roles/firebasehosting.admin` para publicar exclusivamente mediante el gate `qa-frontend`. No existen llaves JSON del pipeline.

## GitHub Environments obligatorios

Cada environment debe requerir aprobacion directa del propietario:

- `qa-build`: publica imagenes candidatas en Artifact Registry.
- `qa-database`: ejecuta la migracion aprobada y, con una confirmacion independiente, reconcilia permisos y entitlements estructurales del tenant demo.
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
| `QA_CLOUD_SQL_CONNECTION_NAME` | `erclave:us-central1:erclave-qa-postgres` |
| `QA_ADMIN_API_URL` | URL HTTPS estable de Admin QA |
| `QA_PRODUCTION_API_URL` | URL HTTPS estable de Produccion QA |
| `QA_INVENTORY_API_URL` | URL HTTPS estable de Inventory QA |
| `QA_HR_API_URL` | URL HTTPS estable de RH QA |
| `QA_BACKOFFICE_ADMIN_EMAILS` | Allowlist separada por comas de administradores internos; no concede roles dentro de tenants |
| `QA_FIREBASE_*` | Configuracion web publica del proyecto Firebase `erclave` |

El secreto `erclave-database-url-qa` permanece exclusivamente en Secret Manager y se monta por referencia. Su valor no pertenece a GitHub.

## Flujo

El procedimiento transversal y la matriz de autorizaciones viven en `docs/operaciones/flujo_local_a_qa.md` y la skill `$erclave-qa-release`.

1. `qa-candidate.yml` exige SHA completo, validacion local equivalente y confirmacion `BUILD_ERCLAVE_QA`; construye cuatro imagenes y registra digests.
2. `qa-release.yml` exige el SHA, el run candidato, `PROMOTE_ERCLAVE_QA` y confirmaciones booleanas separadas para migracion y configuracion del tenant.
3. `qa-database` aplica Alembic solamente tras aprobacion.
4. El job estructural idempotente sincroniza permisos y deja activos solamente `admin`, `production`, `inventory` y `hr`; no carga almacenes, articulos, movimientos, areas, puestos, recetas ni ordenes.
5. `qa-services` crea revisiones etiquetadas `candidate`; usa `--no-traffic` en servicios existentes y una excepcion explicita e idempotente para el primer despliegue de un servicio inexistente. Esa primera revision recibe trafico por una restriccion de Cloud Run, antes de que exista un frontend QA promovido que la consuma.
6. El smoke se obtiene del SHA inmutable que ejecuta el workflow y valida ambiente, readiness, SHA candidato y URLs publicas. Las imagenes siguen siendo exactamente los digests asociados a `release_sha`; corregir automatizacion de release no obliga a reconstruirlas.
7. `qa-traffic` requiere otra aprobacion. Antes de escribir, resuelve desde JSON exactamente una revision `candidate` para cada uno de los cuatro servicios; solo con el conjunto completo mueve el trafico y verifica que cada revision certificada reciba 100%.
8. `qa-frontend` construye un artefacto sin localhost/emulador, lo conserva y despliega exactamente ese directorio.
9. `qa-admin-backoffice-config.yml` corrige la allowlist de Admin sin reconstruir imagenes: `qa-services` crea una revision sin trafico sobre la imagen certificada y `qa-traffic` la promueve solamente si imagen, version, configuracion y revision de rollback siguen coincidiendo.

Estado comprobado CHG-191: la variable esta configurada y el run `31661213987` promovio `admin-service-qa-bo-1-1` al 100%; rollback `admin-service-qa-00017-dih`. La prueba funcional autenticada administrador permitido/owner ordinario `403` debe repetirse con sesion renovada y sin almacenar credenciales.

GitHub Pages queda como maqueta manual y ya no se publica automaticamente al cambiar `main`.

## Rollback

- Servicios: reasignar trafico a las revisiones anteriores registradas antes del release.
- Frontend: restaurar el release previo de Firebase Hosting.
- Backoffice Admin: devolver 100% del trafico a `rollback_revision` registrado por el artefacto del workflow de configuracion.
- Datos: usar restauracion o `forward-fix`; no ejecutar downgrade despues de admitir escrituras sin una decision explicita.
