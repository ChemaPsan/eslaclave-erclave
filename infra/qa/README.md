# Infraestructura preparada para QA

Esta carpeta declara la configuracion necesaria para preparar el candidato. No autoriza ni ejecuta infraestructura, migraciones, seeds o despliegues por si misma.

## Identidades

`identity-plan.json` reemplaza la cuenta de computo predeterminada por identidades separadas para Admin, Produccion, Inventory, RH, migraciones y GitHub Actions. La autenticacion del pipeline usa Workload Identity Federation; no se almacenan llaves JSON.

Antes de aprovisionar se debe revisar el plan con el usuario aprobador y conceder cada rol mediante una actividad `qa-write` independiente.

Estado comprobado el 2026-08-08: las seis cuentas dedicadas, Artifact Registry `erclave-qa` y el provider WIF limitado a `ChemaPsan/eslaclave-erclave` estan aprovisionados. No existen llaves JSON del pipeline.

## GitHub Environments obligatorios

Cada environment debe requerir aprobacion directa del propietario:

- `qa-build`: publica imagenes candidatas en Artifact Registry.
- `qa-database`: ejecuta la migracion aprobada.
- `qa-services`: crea revisiones sin trafico.
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
| `QA_FIREBASE_*` | Configuracion web publica del proyecto Firebase `erclave` |

El secreto `erclave-database-url-qa` permanece exclusivamente en Secret Manager y se monta por referencia. Su valor no pertenece a GitHub.

## Flujo

1. `qa-candidate.yml` exige SHA completo, validacion local equivalente y confirmacion `BUILD_ERCLAVE_QA`; construye cuatro imagenes y registra digests.
2. `qa-release.yml` exige el SHA, el run candidato y `PROMOTE_ERCLAVE_QA`.
3. `qa-database` aplica Alembic solamente tras aprobacion.
4. `qa-services` crea revisiones etiquetadas `candidate` sin trafico.
5. El smoke valida ambiente, readiness, SHA y URLs publicas.
6. `qa-traffic` requiere otra aprobacion para mover trafico.
7. `qa-frontend` construye un artefacto sin localhost/emulador, lo conserva y despliega exactamente ese directorio.

GitHub Pages queda como maqueta manual y ya no se publica automaticamente al cambiar `main`.

## Rollback

- Servicios: reasignar trafico a las revisiones anteriores registradas antes del release.
- Frontend: restaurar el release previo de Firebase Hosting.
- Datos: usar restauracion o `forward-fix`; no ejecutar downgrade despues de admitir escrituras sin una decision explicita.
