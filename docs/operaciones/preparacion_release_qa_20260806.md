# Preparacion del candidato QA - 2026-08-06

> Estado: preparacion e inventario en lectura. Este documento no autoriza despliegues, migraciones, seeds, cambios de trafico ni escrituras de datos en QA.

## Candidato local

- Rama: `agent/production-recipes-qa`.
- Base revisada: `origin/main` en `a4c6111`.
- HEAD previo a consolidacion: `5f542af`.
- Alcance acumulado contra `origin/main`: Administracion, Produccion, Inventario, Recursos Humanos, frontend, contratos, migraciones, validadores y documentacion.
- Verificacion del 2026-08-06: validadores y compilacion aprobados; `127 passed, 1 skipped`.
- Cadena nueva de migraciones: `20260730_0011 -> 20260804_0012 -> 20260805_0013`.
- Revision de secretos: las coincidencias corresponden a la configuracion Firebase publica ya versionada y a una credencial sintetica exclusiva del Firebase Emulator local. No se identificaron credenciales privadas nuevas.

## Inventario QA comprobado en lectura

| Recurso | Evidencia |
|---|---|
| Proyecto GCP/Firebase | `erclave`, numero `370105017372`, estado activo |
| Hosting QA | `https://erclave.web.app`, HTTP 200 |
| Admin Cloud Run | `admin-service-qa`, revision `00013-xmz`, 100% del trafico |
| Produccion Cloud Run | `production-service-qa`, revision `00005-bmp`, 100% del trafico |
| Inventory Cloud Run | No existe un servicio `inventory-service-qa` en el inventario actual |
| HR Cloud Run | No existe un servicio `hr-service-qa` en el inventario actual |
| Cloud SQL | `erclave-qa-postgres`, PostgreSQL 16, `us-central1`, estado `RUNNABLE` |
| Base de aplicacion | `erclave_qa` |
| Backups | Habilitados, siete retenidos; los cinco ultimos consultados terminaron correctamente |
| Secret Manager | Existe el secreto `erclave-database-url-qa`; no se consulto su valor |
| Identidad de servicios | Admin y Produccion usan la cuenta de computo predeterminada |

## Healthchecks no destructivos

- Admin: `/health` informa ambiente `qa`; `/ready` informa base configurada.
- Produccion: `/health` informa ambiente `qa`; `/ready` informa base configurada.
- Produccion presenta `api_public_base_url=http://localhost:8000` en `/version`; debe corregirse en el candidato QA.

## Bloqueos antes de desplegar

1. Desplegar y certificar `inventory-service-qa` y `hr-service-qa` antes de Produccion.
2. Corregir la URL publica reportada por Produccion.
3. Revisar Cloud SQL: IPv4 esta habilitado y `sslMode` permite conexiones sin cifrar.
4. Confirmar o habilitar una estrategia de recuperacion puntual; el inventario no demostro PITR activo.
5. Sustituir la cuenta de computo predeterminada por identidades dedicadas de minimo privilegio.
6. Validar la revision Alembic efectiva de `erclave_qa` antes de solicitar autorizacion de migracion.
7. Separar el workflow de GitHub Pages de la promocion gobernada a Firebase Hosting QA.
8. Impedir que `localStorage` sobrescriba modo, tenant, actor o URLs en el dominio QA y evitar persistir caches operativas del modo API en el navegador.
9. Desactivar `sales`, `integrations` y cualquier entitlement sin microservicio real; activar RH solamente junto con `hr-service`.

## Preparacion incorporada el 2026-08-07

- El codigo rechaza la URL local de Produccion y cualquier otra configuracion local al arrancar en QA/Produccion.
- Inventory y RH quedaron incluidos en la construccion y promocion gobernada, pero siguen sin desplegarse.
- El plan de identidades dedicadas y Workload Identity Federation esta declarado, pendiente de aprovisionamiento autorizado.
- El pipeline manual separa imagenes, migracion, revisiones sin trafico, smoke, trafico y frontend.
- El artefacto frontend QA se genera sin localhost, emulador ni IDs locales.
- Fuera de localhost, el frontend usa exclusivamente la configuracion empacada; la cache de datos API vive solo en memoria y se reconstruye desde los servicios.
- La configuracion estructural QA queda gobernada por confirmacion independiente: actualiza permisos, activa `admin`, `production`, `inventory` y `hr`, e inactiva modulos sin backend. No carga datos funcionales.
- GitHub Pages dejo de tener trigger por `push`; esta preparacion no modifico el hosting QA.

Los bloqueos de Cloud SQL, aprovisionamiento IAM, Artifact Registry, GitHub Environments y ejecucion del pipeline permanecen abiertos hasta recibir autorizaciones independientes.

## Rollback disponible

- Cloud Run conserva revisiones anteriores listas para una futura estrategia de retorno de trafico.
- Firebase Hosting debe conservar el release anterior antes de publicar el candidato.
- Cloud SQL tiene backups automatizados recientes; antes de migrar se exigira un backup/checkpoint autorizado y una estrategia de restauracion o `forward-fix`.

## Escrituras externas

Ninguna. El inventario uso exclusivamente APIs de lectura y healthchecks HTTP no destructivos.

## APIs afectadas

- **Contratos modificados:** Ninguno por esta actividad de preparacion.
- **Endpoints consultados sin cambio:** `GET /health`, `GET /ready` y `GET /version` de Admin y Produccion.
- **APIs no tocadas:** APIs funcionales de Admin, Produccion, Inventory, HR y Ventas.
