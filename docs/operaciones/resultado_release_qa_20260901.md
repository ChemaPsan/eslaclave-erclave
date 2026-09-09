# Resultado del release QA de siete servicios - 2026-09-01

## Resultado

El SHA inmutable `a119ddf5e8d42376b8557b234e15e3681b19c2a7` fue promovido correctamente al ambiente QA. El release incluye Admin, Produccion, Inventory, RH, Ventas, Compras, Mantenimiento y el frontend sanitizado con las siete URL publicas.

Esta acta es evidencia historica. El estado operativo vigente se mantiene en `../contexto/ESTADO_ACTUAL.md`.

## Ejecuciones y aprobaciones

- Candidato inmutable: GitHub Actions `33470879111`.
- Promocion QA: GitHub Actions `33473077996`.
- Aprobaciones independientes completadas: `qa-build`, `qa-database`, `qa-services`, `qa-traffic` y `qa-frontend`.
- Revision de base aplicada: `20260821_0023 -> 20260825_0029`.
- Tenant reconciliado estructuralmente: `ten_739ee59d765d5e14818674800d`.
- No se ejecutaron seeds ni se copiaron datos funcionales desde Local.

## IAM

Se crearon las identidades runtime `erclave-purchasing-qa` y `erclave-maintenance-qa` sin llaves administradas por usuario. Cada identidad recibio Cloud SQL Client, acceso al secreto de base y Cloud Run Invoker solo sobre sus dependencias.

El primer intento de `qa-services` se detuvo antes de Compras porque `erclave-github-deployer-qa` no tenia `iam.serviceAccounts.actAs` sobre la identidad nueva. Se concedio `roles/iam.serviceAccountUser` al deployer unicamente sobre las identidades de Compras y Mantenimiento. El reintento del trabajo fallido concluyo correctamente; la migracion exitosa no se repitio.

## Verificacion posterior

- `https://erclave.web.app` respondio `HTTP 200`.
- `env.js` publico las siete URL HTTPS y no incluyo localhost, Emulator, tenant ni actor demo.
- Los siete servicios aprobaron `GET /health`, `GET /ready` y `GET /version`.
- Todos reportaron ambiente `qa`, base configurada y version `a119ddf5e8d42376b8557b234e15e3681b19c2a7`.
- El Backoffice mostro Compras y Mantenimiento como modulos reales habilitables; la comprobacion manual de Compras fue confirmada por el propietario.

## Pendiente posterior

El equipo de pruebas ejecutara UAT funcional. Sus observaciones deben reproducirse, clasificarse y resolverse en un candidato posterior; este release no autoriza cambios directos fuera del pipeline gobernado.

## APIs afectadas

Contratos modificados: ninguno. Endpoints verificados sin cambio: `GET /health`, `GET /ready` y `GET /version` de los siete servicios. Las APIs funcionales de Compras y Mantenimiento quedaron disponibles mediante sus contratos OpenAPI ya certificados.

## Rollback documentado

Cloud Run conserva las revisiones anteriores de los cinco servicios existentes y Firebase Hosting conserva el release anterior. Para los servicios nuevos, el rollback operativo consiste en desactivar sus entitlements y retirar trafico. Los cambios de base requieren PITR o `forward-fix`; no se autoriza un downgrade improvisado.
