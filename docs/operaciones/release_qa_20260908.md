# Promoción QA de CHG-255–268 — CHG-269

Estado final, CHG-270: release completado el 9 de septiembre de 2026; siete APIs y Hosting verificados sobre `b63cdad`. El apartado «Resultado verificado» registra ejecuciones, digests, revisiones y rollback. Los apartados iniciales documentan el plan ejecutado.

## Candidato y alcance

Solicitud del propietario: promover todos los cambios Local a QA para el tester. Base verificada por GET `/version` de las siete APIs el 8 de septiembre: `a119ddf5e8d42376b8557b234e15e3681b19c2a7`, coincidente con `main` remoto. El candidato incorpora los commits locales posteriores y el conjunto CHG-262–268 del working tree.

Incluye servicios comerciales, 28 reportes de módulo, coherencia frontend/backend, solicitudes y entregas por Almacén, recepciones de compras y aceptación de servicios por el solicitante, transferencias y devoluciones, recuperación de operaciones, mensajes ES/EN y responsive. Detalle contractual en los informes de `docs/auditorias/` y contratos OpenAPI.

## Frontera y mutaciones

- QA: proyecto `erclave`, región `us-central1`, Cloud SQL `erclave-qa-postgres` / `erclave_qa`; Firebase Hosting `https://erclave.web.app`; siete servicios `*-service-qa`. Producción queda fuera.
- Datos actuales se preservan. No se copia Local ni se cargan documentos de prueba. Configuración estructural del tenant `ten_739ee59d765d5e14818674800d` mediante el job gobernado existente: catálogo de permisos, owner demo y entitlements de siete módulos. No se cambia la allowlist Backoffice ni IAM.
- Alembic avanza `20260825_0029` → `20260908_0034`: 0030 órdenes comerciales de servicio/folios/unidad E48; 0031 entregas de materiales; 0032 recepciones y transferencias; 0033 devoluciones y ajustes del propietario; 0034 recuperación de creación fallida. Son cambios de estructura y configuración; no entregan, reciben ni corrigen documentos históricos por inferencia.
- Publicación mediante rama/PR validado, SHA de main, `qa-candidate` y `qa-release`. El pipeline exige confirmaciones de migración y configuración además de gates `qa-build`, `qa-database`, `qa-services`, `qa-traffic`, `qa-frontend`.
- El frontend se construye durante release con configuración QA sanitizada; se registra esta limitación existente y no se afirma identidad build-once para Hosting.

## Ajustes indispensables del release

Inventario ahora consume Maintenance para devoluciones: se configura `ERCLAVE_MAINTENANCE_SERVICE_URL` en QA y Settings rechaza una URL local para esa dependencia. Se prueba el rechazo sin conectar recursos remotos.

La promoción registra las siete revisiones anteriores en `qa-traffic-rollback.json`, comprueba drift antes de cada cambio y verifica 100% en cada destino. Ante fallo restaura y verifica el tráfico de todos los servicios intentados, incluido aquel cuya respuesta pudo perderse. Conserva el artefacto incluso si el job falla. Pruebas sin acceso cloud cubren éxito y fallo parcial después de aplicar tráfico.

## Validación Local previa al release

Local aislado: 54 pruebas navegador aprobadas; verify, compilación y validadores aprobados; 262 backend y 55 omitidas por no habilitar DB general. La evidencia PostgreSQL seleccionada y smokes reales de CHG-263–268 permanece en sus informes; no se repiten seeds ni suites con fixtures de otros tenants. Dos pruebas de promoción compensatoria aprobadas. CI repetirá verify y las pruebas de tráfico sobre el SHA publicado.

PR, SHA final, runs, digests, revisiones, Alembic aplicado, resultado Hosting y smoke posterior están registrados en el cierre CHG-270. Las verificaciones HTTP públicas no equivalen a UAT autenticada de todos los flujos; el tester realizará la aceptación funcional con sus cuentas y datos QA existentes. No se crearon segundos tenants ni identidades de prueba por esta liberación.

## Rollback

Servicios: usar las revisiones exactas guardadas; el script compensa automáticamente un fallo parcial. Hosting: release anterior. Base: forward-fix/PITR con decisión expresa, sin downgrade improvisado después de admitir escrituras. Las migraciones añaden estructuras; no se borra historia ni se trasladan datos Local.

## Agentes y APIs afectadas

Consulta documental sin delegación: Arquitectura, Seguridad/IAM, QA/Release, API, Datos/Custodio DB, Sinergia, UX/i18n y negocio/técnicos de Administración, Producción, Inventarios, RH, Ventas, Compras y Mantenimiento. Skills erclave-environment-boundaries, erclave-qa-release y erclave-db-migration.

Este corte de release no cambia contratos funcionales adicionales. Promueve los contratos Maintenance/Inventory/Production/Purchasing/Sales/HR detallados en los informes CHG-255–268. Consume GET `/health`, `/ready`, `/version` y `/openapi.json` de las siete APIs, y los workflows protegidos de GitHub. Configuración de Inventory modifica su destino HTTP Maintenance; conserva métodos, payloads y permisos. APIs funcionales Admin y rutas planned no reciben cambios contractuales adicionales.


## Resultado verificado el 9 de septiembre — CHG-270

Release completado. PR #14: https://github.com/ChemaPsan/eslaclave-erclave/pull/14. SHA funcional `b63cdad2fbac423c24460e55582ccfc0003e9924`; build https://github.com/ChemaPsan/eslaclave-erclave/actions/runs/34389669031 y promoción https://github.com/ChemaPsan/eslaclave-erclave/actions/runs/34390476667, ambos exitosos. Gates build/database/services/traffic/frontend aprobados bajo autorización explícita del propietario del 9 de septiembre.

Alembic hasta `20260908_0034`: ejecución `erclave-migrate-qa-6tzpq` exitosa. Configuración estructural: `erclave-configure-tenant-qa-krkjg` exitosa. Sin carga de datos funcionales, copia de Local, cambios IAM ni recursos de Producción.

Las siete URLs estables aprobaron GET health/ready/version/openapi.json con el SHA exacto. Solicitudes sin token y con token inválido a rutas protegidas devolvieron 401/403, nunca datos. Esto no sustituye las pruebas autenticadas de permisos/multitenant ni UAT de documentos; esas aceptaciones siguen pendientes con el tester.

Hosting https://erclave.web.app sirvió index.html, env.js, app.js y styles.css con SHA-256 idéntico al artefacto publicado. Configuración API/Firebase y siete URLs QA, sin localhost, Emulator, tenant ni actor demo. Se conserva la limitación build-during-release del frontend.

### Revisiones y rollback exactos

| Servicio | Revisión al 100% | Tráfico anterior |
|---|---|---|
| admin-service-qa | `admin-service-qa-00032-mot` | `admin-service-qa-00030-pox=100` |
| inventory-service-qa | `inventory-service-qa-00013-wuf` | `inventory-service-qa-00011-fac=100` |
| hr-service-qa | `hr-service-qa-00013-rib` | `hr-service-qa-00011-rul=100` |
| production-service-qa | `production-service-qa-00018-six` | `production-service-qa-00016-zab=100` |
| sales-service-qa | `sales-service-qa-00008-qid` | `sales-service-qa-00006-gaf=100` |
| purchasing-service-qa | `purchasing-service-qa-00003-jev` | `purchasing-service-qa-00001-guf=100` |
| maintenance-service-qa | `maintenance-service-qa-00003-gih` | `maintenance-service-qa-00001-wim=100` |

Artefacto de evidencia `qa-traffic-rollback-b63cdad2fbac423c24460e55582ccfc0003e9924`, ID `10120005130`. No se necesitó compensación. La base se recupera mediante forward-fix/PITR con decisión expresa; Hosting conserva su release anterior.

### Imágenes inmutables

```text
ADMIN_IMAGE=us-central1-docker.pkg.dev/erclave/erclave-qa/admin-service@sha256:7c9e547a09944e885369bca5756fcc802e50a9380da7d585723ea363b9affe81
PRODUCTION_IMAGE=us-central1-docker.pkg.dev/erclave/erclave-qa/production-service@sha256:86f40001149d491e70a6aa8cc3a174f3641d8cc014e1bc62e2b11a073b895761
INVENTORY_IMAGE=us-central1-docker.pkg.dev/erclave/erclave-qa/inventory-service@sha256:caad6e6998e6c8b151cf482b61ac15199cc7b33fa9eeb88a800513ff503ebec3
HR_IMAGE=us-central1-docker.pkg.dev/erclave/erclave-qa/hr-service@sha256:2d1b1b6803a7514200e87c9ee905e31de375c164aa8f5c5dfdae7f705eb871c0
SALES_IMAGE=us-central1-docker.pkg.dev/erclave/erclave-qa/sales-service@sha256:37c2d69ff14359eeedd1773f1eb1119d1a44b383c94e5a6b0ac74e3f4a1865b5
PURCHASING_IMAGE=us-central1-docker.pkg.dev/erclave/erclave-qa/purchasing-service@sha256:3012606b91d69f8a7d25b999a7fff43ca9217a345a1e3ad2358f58602faebec9
MAINTENANCE_IMAGE=us-central1-docker.pkg.dev/erclave/erclave-qa/maintenance-service@sha256:0f2353b3f087cc77804e29aa63747646a65f58e95187cb9abbec3dcfeab9c759
```

### Hashes del frontend servido

- `index.html`: `ef002f61c53370231aa6e3aaee0ca900fdafd843313677bbf98e80ff0f5e6a63`.
- `env.js`: `3aa14880b3d987c431346b2c2abef55579b5ec51030feac0cd7c0ef4433e1f48`.
- `app.js`: `9ff86f346e19f341b47d55d85456764ad2b071221f388ec069cc8f6900f55415`.
- `styles.css`: `15e7f9f465e7b8a7aeceed043e3020072ca70b05d0b1718998ea37b19070c193`.
