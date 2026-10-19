# Flujo canonico de Local a QA

Este procedimiento optimiza una liberacion sin reducir seguridad ni calidad. No autoriza escrituras por si mismo.

## 1. Recuperar contexto y agentes

1. Ejecutar `npm.cmd run session:context` y revisar `git status --short`.
2. Usar `$erclave-environment-boundaries` y `$erclave-qa-release`.
3. Consultar siempre:
   - Arquitecto senior de plataforma SaaS;
   - Ingeniero senior de seguridad, IAM y supply chain;
   - Ingeniero senior de QA, validadores y release.
4. Sumar Datos y Custodio DB para migraciones/configuracion/datos; API para backend/auth/contratos; Administracion para permisos/Backoffice; agentes de negocio y tecnico del modulo para cambios funcionales.
5. Registrar `Agentes consultados` en trazabilidad y entrega.

## 2. Calcular el delta real

Comparar el candidato con el SHA certificado que reporta `/version` en cada servicio QA actualmente publicado. Si no comparten version, detener la promocion conjunta y preparar un delta por servicio. Clasificar cada archivo y efecto:

| Tipo | Gate/autorizacion |
|---|---|
| Codigo, contratos e imagenes | `qa-build` |
| Migracion Alembic | `qa-database`, autorizacion de migracion |
| Permisos/entitlements estructurales | `qa-database`, autorizacion de configuracion |
| Datos funcionales, seeds demo o volumen | Autorizacion de datos independiente; no forman parte implicita del release |
| Revisiones Cloud Run | `qa-services` |
| Trafico Cloud Run | `qa-traffic` |
| Frontend Firebase Hosting | `qa-frontend` |
| IAM, secretos o variables | `qa-write` propio y minimo privilegio |

Publicar una rama, abrir PR y fusionar tambien requieren instruccion explicita. Un gate aprobado no concede los siguientes. Mostrar destino, tenant, mutaciones, evidencia y rollback antes de cada autorizacion.

## 3. Certificar Local aislado

- Arrancar con `backend/scripts/start_local.ps1`.
- Usar PostgreSQL `erclave_local`, Firebase Emulator `demo-erclave`, loopback y datos sinteticos.
- No abrir Cloud SQL Auth Proxy ni cargar `.env` hibridos.
- Ejecutar `npm.cmd run verify`; el comando debe rechazar una URL de pruebas que no sea loopback/`erclave_local`.
- Validar permisos positivos/negativos, aislamiento, idempotencia, errores y persistencia tras recarga.
- En modo API, PostgreSQL/API son la fuente de verdad: sin fallback de escritura a mocks o `localStorage`.

## 4. Preparar candidato

1. Actualizar contratos, pruebas, docs, contexto y `TRAZABILIDAD.md`.
2. Abrir PR y exigir `Complete repository verification` sobre el `main` vigente.
3. Fusionar; usar el SHA completo de `main`.
4. Ejecutar `qa-candidate.yml` con `BUILD_ERCLAVE_QA`.
5. Conservar run ID, SHA y digests exactos. No reconstruir despues de aprobar.

## 5. Promover a QA

1. Ejecutar `qa-release.yml` con el mismo `release_sha`, run candidato y `PROMOTE_ERCLAVE_QA`.
2. Revisar `qa-database`: el job conserva su aprobación de ambiente, pero los inputs `execute_database_migration` y `configure_qa_tenant` habilitan pasos de escritura independientes, apagados por defecto y sujetos a sus autorizaciones. `/ready` remoto verifica conexión y head Alembic de la imagen: omitir una migración requerida impide promover. Configuración exige tenant existente explícito (`QA_CONFIGURATION_TENANT_ID`); sincroniza catálogo global y grants de owners de sistema existentes de ese tenant para módulos efectivos, sin crear/resetear usuarios, membresías, perfil ni entitlements. Nunca ejecutar Alembic QA directamente desde Local.
3. Autorizar `qa-services`; validar candidatos con imagen/digest, ambiente, `/health`, `/ready`, `/version`, auth, CORS y dependencias.
   Antes de tráfico, el job de sólo lectura `check_qa_operational_readiness.py` exige autoridad organizacional coherente, monedas confirmadas en `QA_CONFIRMED_SOCIETY_CURRENCIES`, scopes resolubles y Owner operativo en `QA_CONFIGURATION_TENANT_ID`. Migrar tablas no activa ni configura organización. Si falla, conservar tráfico estable y revisar el plan; sólo usar APIs del candidato para datos/configuración aprobados expresamente. [Plan sintético en revisión](../../infra/qa/synthetic-organization-plan.json).
4. Antes de `qa-traffic`, descargar el manifiesto certificado `qa-candidate-revisions.json`: las ocho revisiones, imagen/digest resuelto, SHA, URL etiquetada y tráfico estable deben coincidir con qa-services. No sustituirlo por el tag actual. Revalidar antes de cada cambio y al terminar; registrar rollback compensatorio. Si una promoción intermedia falla, restaurar los servicios ya intentados antes de reintentar.
5. Verificar 100% de trafico por servicio y repetir smoke en URLs estables.
6. Autorizar `qa-frontend`; comprobar HTTP 200 y el `env.js` realmente publicado: modo API/Firebase, ocho URLs QA y ausencia de Local/Emulator/tenant/actor demo. El candidato construye el frontend sanitizado con SHA256SUMS; release verifica procedencia/SHA, ocho URLs y hashes antes de escrituras y publica ese mismo directorio sin reconstruirlo. Verificar también los bytes servidos tras Hosting.
   El workflow ejecuta `tools/verify-qa-hosting.js` después de publicar; verifica cada archivo servido contra las huellas del candidato y falla si encuentra contenido anterior o distinto. Conservar el release Hosting previo para rollback.

## 6. Paridad funcional y datos

Paridad significa mismo codigo y comportamiento certificado para las capacidades habilitadas; no igualdad de datasets, entitlements o contenido. QA debe ejecutar esas capacidades con APIs reales y Cloud SQL QA. Los catalogos vacios permanecen vacios; no crear registros para aparentar paridad ni copiar/exportar la base Local hacia QA. Sales forma parte del conjunto operativo; el catálogo básico de centros usa el octavo runtime Costing con disponibilidad Admin y permisos puntuales. Analítica Costing, Accounting, Integraciones y otras capacidades planned conservan su activación independiente. No perder funciones Local excluyendo su runtime o dependencias del candidato QA.

Antes de cualquier dato funcional, decidir y registrar: API o comando gobernado, tenant, objetivo, duracion, criterio de limpieza/rollback y autorizacion propia. La ambiguedad de "datos reales" bloquea la escritura; puede significar preservar datos existentes, configuracion estructural o crear registros controlados, pero nunca autoriza una copia de Local.

La aceptacion autenticada debe cubrir:

- tenant seleccionado desde membresias de la sesion, nunca desde un ID demo embebido;
- persistencia entre recarga/sesion cuando se autorizan datos de prueba;
- usuario sin token, token invalido, tenant no miembro, modulo inactivo y permiso faltante;
- aislamiento con dos tenants desechables autorizados;
- ausencia de KPIs, reservas o transacciones simuladas en modulos API.

## 7. Configuracion Backoffice

La allowlist interna no equivale a ser `owner` de un tenant.

1. Configurar `QA_BACKOFFICE_ADMIN_EMAILS` sin hardcodear correos en codigo o seeds.
2. Usar `qa-admin-backoffice-config.yml` con el SHA Admin certificado.
3. `qa-services` crea una revision con la misma imagen, 0% de trafico y estado de rollback.
4. `qa-traffic` promueve solo si no hay drift.
5. Renovar sesion y comprobar: administrador allowlisted accede; owner ordinario recibe `403`.

No guardar passwords, tokens ni URLs con credenciales en Git, logs o artifacts.

## 8. Cierre y rollback

Registrar SHA/digests, runs, revisiones, trafico, frontend, tenant, datos, gates, verificaciones y escrituras externas. Actualizar `ESTADO_ACTUAL.md` únicamente con hechos comprobados y retirar pendientes resueltos.

Rollback:

- servicios/configuracion: revision previa registrada;
- frontend: release anterior de Firebase Hosting;
- datos: PITR o `forward-fix`, nunca downgrade improvisado tras admitir escrituras;
- funcionalidad: entitlement/flag sin borrar historia.

## Deuda de pipeline que no debe olvidarse

- ampliar la promoción compensatoria CHG-269 con simulaciones de fallos del proveedor;
- fortalecer provenance/attestation de artifacts e imagenes;
- agregar reintentos/rollback automatizado a la correccion Backoffice;
- ampliar smoke autenticado, CORS/IAM y post-deploy de Hosting.


## Antecedente histórico: candidato de continuidad CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Release QA verificado CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff histórico: `docs/contexto/REANUDACION_CHG269.md`; retomar desde `docs/contexto/INICIO_SESION.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.

## Preparación CHG-275

Candidato Local CHG-271–275: manuales/formularios, margen sin tope de 100% y evidencia de servicios. Plan histórico de ese corte: `docs/operaciones/release_qa_20260914.md`. Entonces QA estaba en b63cdad; destino Alembic 0036. Consultar ESTADO_ACTUAL para el estado vigente. Configurar y verificar bucket privado dedicado y QA_EVIDENCE_BUCKET antes de promover Production. 29 integraciones históricas requieren corregir fixtures/autorización; no declarar certificación completa ni ejecutar la suite DB indiscriminadamente. Sin despliegue remoto en esta preparación.
