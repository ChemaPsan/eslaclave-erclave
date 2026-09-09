# Promoción QA de CHG-255–268 — CHG-269

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

## Validación y pendientes de ejecución

Local aislado: 54 pruebas navegador aprobadas; verify, compilación y validadores aprobados; 262 backend y 55 omitidas por no habilitar DB general. La evidencia PostgreSQL seleccionada y smokes reales de CHG-263–268 permanece en sus informes; no se repiten seeds ni suites con fixtures de otros tenants. Dos pruebas de promoción compensatoria aprobadas. CI repetirá verify y las pruebas de tráfico sobre el SHA publicado.

Pendiente: registrar PR, SHA final, runs, digests, revisiones, Alembic aplicado, resultado Hosting y smoke posterior. Las verificaciones HTTP públicas no equivalen a UAT autenticada de todos los flujos; el tester realizará la aceptación funcional con sus cuentas y datos QA existentes. No se crean segundos tenants ni identidades de prueba por esta liberación.

## Rollback

Servicios: usar las revisiones exactas guardadas; el script compensa automáticamente un fallo parcial. Hosting: release anterior. Base: forward-fix/PITR con decisión expresa, sin downgrade improvisado después de admitir escrituras. Las migraciones añaden estructuras; no se borra historia ni se trasladan datos Local.

## Agentes y APIs afectadas

Consulta documental sin delegación: Arquitectura, Seguridad/IAM, QA/Release, API, Datos/Custodio DB, Sinergia, UX/i18n y negocio/técnicos de Administración, Producción, Inventarios, RH, Ventas, Compras y Mantenimiento. Skills erclave-environment-boundaries, erclave-qa-release y erclave-db-migration.

Este corte de release no cambia contratos funcionales adicionales. Promueve los contratos Maintenance/Inventory/Production/Purchasing/Sales/HR detallados en los informes CHG-255–268. Consume GET `/health`, `/ready`, `/version` y `/openapi.json` de las siete APIs, y los workflows protegidos de GitHub. Configuración de Inventory modifica su destino HTTP Maintenance; conserva métodos, payloads y permisos. APIs funcionales Admin y rutas planned no reciben cambios contractuales adicionales.
