# Preparación de promoción QA — 14 septiembre 2026

## Infraestructura de evidencia CHG-277 — promoción pendiente

Acceso Cloud resuelto con la cuenta administradora autorizada. El 2026-09-14 se creó `erclave-qa-service-evidence` en erclave/us-central1: Standard, acceso uniforme y prevención pública enforced, sin versionado, soft delete ni retención bloqueada. Se verificó vacío y una única regla Delete con age 365. GitHub `QA_EVIDENCE_BUCKET=erclave-qa-service-evidence` creada y leída de vuelta.

El usuario autorizó el rol mínimo para `erclave-production-qa@erclave.iam.gserviceaccount.com`: storage.buckets.get y storage.objects.create/get/delete, solo en ese bucket. Rol `projects/erclave/roles/erclaveQaServiceEvidence` creado en disponibilidad general con esos cuatro permisos; asignación directa exclusivamente al bucket guardada y confirmada en consola. No afirmar acceso funcional por health/ready.

Autorizadas las pruebas con tenants temporales UUID y limpieza exclusivamente en loopback5434/erclave_local. `npm run verify:postgres` terminó con **360 aprobadas, cero omitidas** (65.39s); validadores y compilación aprobados. Esto cierra las20 integraciones pendientes y las55 históricas omitidas en la ejecución sin DB. No demuestra UAT ni paridad autenticada QA.

PR #15 sigue en borrador; HEAD publicado dffe7642d57111b94b74d95ec62f252b017c0190, CI34816946232 aprobado. No merge, qa-candidate, qa-release, migración ni tráfico/Hosting. Base QA previamente verificada b63cdad. Pendientes: smoke de adjuntos, pipeline protegido, pruebas autenticadas QA y revisión visual Word. No se crearon datos funcionales QA.

## Base y alcance

Consulta pública de GET /version el 2026-09-14: los siete servicios (Admin, Production, Inventory, RH, Sales, Purchasing y Maintenance) reportan `b63cdad2fbac423c24460e55582ccfc0003e9924`. URLs consultadas: `https://<servicio>-service-qa-370105017372.us-central1.run.app/version`, donde servicio es admin, production, inventory, hr, sales, purchasing o maintenance. No se leyó Cloud SQL ni se escribieron datos QA. Alembic QA documentado: `20260908_0034`; se debe reconfirmar mediante el gate de DB al promover.

Rama Local: `agent/chg-269-qa-promotion`, HEAD previo `f90efbdd1d65fc4f322b6433416f14d3d23682f5`. Los cambios CHG-271–275 siguen en el working tree. Ese HEAD no es el SHA del candidato; asignarlo después de revisión y fusión. El manifiesto Git incluye archivos nuevos no rastreados, no basta `git diff --stat`.

Agentes consultados: fichas de Arquitectura, Seguridad/IAM, QA/Release, APIs, Datos/Custodio DB, Producción negocio/técnico, módulos consumidores y Custodio de manuales en AGENTES.md; auditoría independiente `qa_db_audit` para fixtures históricos. Skills: erclave-environment-boundaries, erclave-qa-release, erclave-solution-manuals y documents.

Ambiente de trabajo: Local aislado. Pruebas con escritura únicamente en loopback:5434/erclave_local, tenant `ten_739ee59d765d5e14818674800d`; fixtures UUID y limpieza por sus IDs. Sin seeds ni copia de datos. Mutaciones remotas actuales: bucket, lifecycle, rol mínimo y binding de bucket QA; variable GitHub. La consulta pública /version es solo lectura.

## Matriz del delta

| Elemento | Local preparado | QA / gate |
|---|---|---|
| Documentación CHG-271 y revisión CHG-275 | Siete manuales, guía, matriz y entrega al tester | Publicación documental pendiente |
| Formularios CHG-272 | Inline, resumen/foco, captura conservada, errores seguros ES/EN; skill obligatoria | Frontend compartido y Backoffice pendientes de qa-frontend |
| Margen CHG-273 | Sin tope de 100%, finito/no negativo, sobre costo | Production API + migración 0035 + frontend |
| Evidencia CHG-274 | Texto inicial/final en servicios, cierre en avance total, fotos optimizadas, adjuntos 365 días | Production API + migración 0036 + bucket privado + frontend |
| Contratos | Production OpenAPI actualizado | Mismo SHA que API y consumidor |
| Configuración CHG-275 | qa-release pasa QA_EVIDENCE_BUCKET a ERCLAVE_EVIDENCE_BUCKET solo en Production y rechaza nombre vacío/inválido | Bucket, lifecycle, variable y rol mínimo configurados; smoke pendiente |
| Datos existentes | 0035 conserva porcentajes; 0036 agrega tablas vacías | No backfill ni evidencia inventada; órdenes activas completan evidencia al continuar |
| Servicios | Siete imágenes y dependencias, nuevas librerías de imagen/Storage en pyproject | qa-build, qa-services y qa-traffic |
| Permisos / tenant | No nuevos permisos de evidencia | Pipeline sigue obligando reconciliación estructural y migración: autorizaciones explícitas de ambos |

## Almacenamiento previo a habilitar evidencia

Nombre creado y confirmado: `erclave-qa-service-evidence`. Variable de repositorio GitHub `QA_EVIDENCE_BUCKET`, nombre sin gs://. Bucket dedicado de QA en la región QA; no reutilizar Firebase Storage ni buckets de backups o Producción.

Requisitos comprobables contra API Storage:

- acceso uniforme por bucket y prevención de acceso público enforced;
- política de `infra/qa/service-evidence-lifecycle.json`: Delete con condición age 365;
- versionado deshabilitado, soft delete en 0, sin retention policy ni event-based holds;
- no reglas adicionales que borren antes de 365 días, backups de binarios ni replicaciones que prolonguen conservación;
- runtime de Production con `storage.buckets.get`, `storage.objects.create`, `storage.objects.get` y `storage.objects.delete` únicamente sobre este bucket, mediante IAM gobernado; el resto de servicios no requiere acceso;
- identidad de migración conserva permisos DB; no necesita acceso a adjuntos. No crear llaves JSON.

El backend valida la política al acceder al almacén. Un /health o /ready correcto no demuestra IAM ni que una carga funcione: antes de mover tráfico exigir carga, consulta y descarga con archivo desechable autorizado usando la revisión candidata. Confirmar nombre, CORS Content-Disposition, ausencia de URL pública y limpieza del fixture. Cloud Run puede escalar a cero: el lifecycle es el respaldo de eliminación física, mientras la API corta descarga en expires_at. La eliminación física GCS es asíncrona, no instantánea al segundo del vencimiento.

CHG-277 creó el bucket y concedió el rol mínimo tras autorización específica; configuración real e identidad registradas arriba. Falta smoke mediante revisión candidata antes del tráfico.

## Migración y rollback

Secuencia 0034 → `20260913_0035` → `20260913_0036`, exclusivamente mediante job protegido qa-database, nunca Alembic QA desde Local. Revisar respaldo/PITR existente y estado antes/después; preservar datos reales. No ejecutar seeds de desarrollo.

0035 convierte margen a NUMERIC sin precisión fija con constraint no negativo/finito. Su downgrade se bloquea si hay porcentajes mayores de 100 o precisión incompatible. 0036 agrega evidencia y archivos tenant-safe; downgrade se bloquea si existe evidencia escrita. Después de admitir escrituras, preferir forward-fix. No borrar texto ni convertir porcentajes para hacer caber un downgrade.

Registrar siete revisiones estables e imágenes exactas antes de qa-traffic. Restaurar tráfico compensatoriamente si hay fallo parcial; restaurar Hosting al release previo si corresponde. **Revertir Production al código anterior suprime las precondiciones de evidencia**: detener las transiciones de servicio mediante el alcance operativo/permisos autorizado durante la contingencia, sin inventar una bandera que no existe. Mantener esquema aditivo y bucket para conservar historia; no eliminar el bucket como rollback.

## Evidencia de pruebas y bloqueos

Verificación general CHG-275: `npm run verify` aprobada, 292 backend, 58 skips por no configurar DB; validadores, sintaxis80 y compilación aprobados. La selección independiente de29 descrita abajo no elimina los29 bloqueos restantes.

Ocho DOCX regenerados, reabiertos y contrastados contra todos los fragmentos Markdown. Revisión visual pendiente: falta renderizador y Word Automation no respondió; no distribuir como versión final hasta cerrar esa revisión.

Corte CHG-274: 185/185 browser y 292 backend aprobadas; corrida genérica omite 58 sin DB. De las 58, tres nuevas (margen/evidencia) ya estaban verificadas aparte. No usar esos skips como certificación integrada.

CHG-275 ejecutó una selección segura de **29 pruebas aprobadas, cero omitidas**: 23 integraciones históricas DB + 3 validaciones de schema históricas + 3 integraciones nuevas margen/evidencia. Se ajustó la fixture warehouse para elegir receta de producto, preservando la prueba de entrega sin exigir evidencia de servicio ajena a su objetivo. Los handoffs con autoridades dobles prueban persistencia del propietario, no comunicación real entre las siete APIs.

Quedan **29 pruebas históricas bloqueadas**: Admin 4 (crean tenants aunque hagan rollback), Ventas repositorio 5 (tenant UUID distinto), Compras repositorio 11 (tenant distinto y borrado completo; prueba adicional de otro tenant), Mantenimiento repositorio 9 (cleanup por diferencia del baseline, puede borrar órdenes concurrentes). No ejecutar verify:postgres completo ni cambiar solo el tenant de esas fixtures: podría borrar información. Corregirlas con IDs/actor/keys únicos y limpieza acotada; los casos de onboarding/multitenant requieren recursos expresamente autorizados o cobertura rediseñada sin afirmar equivalencia. Inventario 9, Production warehouse 6, Compras handoff 2, Ventas handoff 1 y Maintenance recovery/return 5 sí se ejecutaron.

UAT autenticada QA, aislamiento con dos tenants autorizados, smoke de almacenamiento real GCS, nueva revisión visual Word y certificación de las 29 pendientes son gates aún por cerrar. Las pruebas no autorizan escrituras QA adicionales. Ver `docs/qa/MATRIZ_EJECUCION_QA.md`: 56 casos base y 9 del candidato, todos con resultado por registrar.

## Secuencia de promoción preparada

1. Cerrar bloqueos, revisar diff incluyendo archivos nuevos y resultados. Regenerar manuales y revisar sus páginas finales. No distribuir binarios sin revisión visual.
2. Con autorización propia publicar rama, crear PR y fusionar; exigir verify sobre main vigente. Registrar SHA completo final; no desplegar el working tree.
3. Con qa-build aprobado, ejecutar qa-candidate con SHA y BUILD_ERCLAVE_QA. Registrar run y siete digests. No reconstruir imágenes después de aprobación.
4. Completar autorización y verificación de bucket/IAM/variable, luego qa-release con SHA, run y PROMOTE_ERCLAVE_QA. Sus booleanos actuales obligan migración y configuración del tenant: aprobar ambas expresamente.
5. qa-database aplica 0035/0036 y configuración; qa-services crea revisiones candidatas sin tráfico en servicios existentes. Smoke autenticado de evidencia y regresión de producto, permisos y contratos.
6. qa-traffic verifica ausencia de drift, promueve siete revisiones y comprueba 100% exacto. qa-frontend publica artefacto sanitizado y verifica contenido servido. El frontend aún se reconstruye en release; no afirmar build-once.
7. Ejecutar UAT autorizada, llenar matriz con versión real y actualizar estado/manuales por ambiente solo después de evidencia de promoción.

Pendientes de asignar: SHA final, PR, run candidato, digests, nombre e IAM del bucket verificados, run release, revisiones estables/candidatas, versión Hosting, aprobaciones, UAT y aceptación final. Ninguno se sustituye por el HEAD Local.

## APIs afectadas

Esta preparación CHG-275 no agrega endpoints; documenta el contrato del candidato Production:

| Método y ruta | Permiso / contrato |
|---|---|
| POST /v1/production/product-services | production.product_service.create; expected_margin finito >=0 sin máximo 100 |
| PATCH /v1/production/product-services/{product_service_id} | production.product_service.update; misma regla |
| POST /v1/production/orders/{order_id}/service-evidence/{phase} | start: production.order.start o production.order.wait_resources; finish: production.order_stage.complete. Request description y hasta 3 files; response texto/metadatos |
| GET /v1/production/orders/{order_id}/service-evidence/files/{file_id} | production.order.read; binario privado, 410 al vencer |
| GET /v1/production/orders | production.order.read; añade is_service_order/service_evidence |
| GET /v1/production/orders/{order_id} | production.order.read; mismos campos |
| PATCH /v1/production/orders/{order_id}/status | Permiso puntual de la transición existente; agrega requisitos inicial/final solo en servicio |
| PATCH /v1/production/order-stages/{stage_id} | Permiso de actualización/terminación de etapa existente; recepción y cierre antes del 100% total |

Consumidos sin cambio en preparación: GET /version de los siete servicios. Los otros contratos de Admin, Inventory, RH, Sales, Purchasing y Maintenance no cambian por este corte. Feedback de formularios consume endpoints existentes.
