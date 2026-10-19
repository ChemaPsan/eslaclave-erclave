# Promoción QA autorizada · CHG-336 · 2026-10-19

> Evidencia histórica de ejecución de este corte, todavía en curso. Fuente vigente: [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md). Una acción pendiente no se considera ejecutada por figurar en el plan.

## Autorización vigente y alcance

El usuario confirmó que sirven la estructura sintética y las monedas MXN/USD y pidió «si sirven haz los siguientes pasos», después de enumerar PR/checks, merge, identidad/configuración Costing, candidato/promoción y aceptación QA. Esto autoriza avanzar secuencialmente con esas actividades y sustituye el estado preparatorio de CHG-335; se conservan las protecciones reales de GitHub y las condiciones de baseline, identidad y rollback. No solicitar otra vez las autorizaciones ya concedidas.

Tenant previsto exclusivamente `ten_739ee59d765d5e14818674800d`, ERClave Demo QA: verificar existencia e identidad efectiva antes de escribir. Estructura: un Emisor sintético sin validez fiscal, dos Sociedades MXN/USD, tres Divisiones y tres Centros básicos. [Plan](../../infra/qa/synthetic-organization-plan.json). Preservar datos, perfil, miembros/roles/entitlements, contadores, stock, moneda e historia existentes. No copiar Local ni activar analítica Costing o Accounting.

Agentes consultados: Arquitectura, Seguridad/IAM, QA/Release, Datos/Custodio DB, API y dueños Admin/Costing/operativos. Agentes ejecutados: manuales_paridad (orden de release/recursos Google) y trazabilidad (auditoría independiente de alcance/evidencia/baseline); cc20_integracion (inspector gobernado,32 focales y revision); raíz GitHub, integración y gobierno.

## Resultados efectivos

| Actividad | Resultado comprobado |
|---|---|
| Base main al abrir PR | e57237fe90319f88e1db8ed8d2e686604d2d9c54; rama protegida, check Complete repository verification requerido |
| Rama publicada inicial | agent/chg-278-qa-release-record,60f698b7d3ae4f69c1fb630c1d004ed961d2c551 |
| Alcance total inicial | Cinco commits,503 archivos,+58055/-9271 y26 migraciones0037–0062;78 archivos era sólo el último commit CHG-335 |
| PR | [#16](https://github.com/ChemaPsan/eslaclave-erclave/pull/16), abierto por petición del usuario; nueva documentación de autorización se añade a la misma rama |
| CI inicial | Run39208234912: Complete repository verification aprobado para60f698b; incluye navegador aislado, verify y12 escenarios de tráfico. El CI del head definitivo también se exige antes de fusionar |
| Evidencia Local previa | Verify833 aprobadas,351 omitidas sin DB,1 advertencia; focales PG/API y aceptación HTTP/Chrome por variantes, [acta CHG-335](paridad_local_qa_20261018.md) |
| Google/QA | Nueva cuenta autenticada: proyecto/Firebase erclave, numero370105017372; IAM, Hosting, instancia DB, politica del secreto, servicios y backups HTTP200. CostingSA404/NOT_FOUND en este baseline anterior a su creacion. Evidencia .local/chg336-gcp-baseline-metadata.json, sin lectura del valor del secreto |
| Variables GitHub | Creadas/verificadas QA_COSTING_API_URL=https://costing-service-qa-370105017372.us-central1.run.app, QA_COSTING_RUNTIME_SERVICE_ACCOUNT=erclave-costing-qa@erclave.iam.gserviceaccount.com y QA_CONFIGURATION_TENANT_ID=ten_739ee59d765d5e14818674800d. Cuenta Costing ya creada segun fila IAM; servicio Costing aun no desplegado |
| IAM Costing aplicado | CostingSA creada y confirmada GET200; tres grants minimos aplicados y confirmados: roles/cloudsql.client en proyecto, roles/secretmanager.secretAccessor solo en erclave-database-url-qa y roles/iam.serviceAccountUser al deployer solo sobre CostingSA. Total4 cambios IAM incluyendo identidad; .local/chg336-costing-iam-apply.json status completed_scoped_iam_changes3. El GET404 inmediato tras crear la cuenta fue propagacion transitoria; GET posterior200. Evidencia de intento anterior preservada, replanning hash f29ff344... antes de aplicar grants, sin ampliar otros bindings |
| Inspector implementado | qa-inspect.yml e inspect_qa_release_baseline.py, pruebas focales y guard pipeline; validacion final aprobada, ejecucion remota pendiente |
| Validacion final CHG-336 | .local/chg336-verify-final.log:864 aprobadas,352 omitidas sin DB,1 advertencia existente,30.57s backend; YAML4/Bash29 pasos aprobados y head Local0062 leido. No acredita inspeccion SQL ni ejecucion QA |

El release_sha definitivo será el commit fusionado y certificado. No usar por inferencia el head inicial ni la rama main Local atrasada. Mantener SHA, run, ocho digests, artefacto frontend, hashes, revisiones previas y resultados de cada etapa antes de cerrar.

## Baseline previo a escrituras

1. Consultar versiones públicas actuales y revisiones/imágenes/tráfico Cloud Run; registrar Hosting previo.
2. Verificar Cloud SQL QA, head efectivo y recuperación/PITR antes de migrar0036→0062. Las migraciones se ejecutan sólo mediante el workflow aprobado.
3. Verificar tenant, perfil legacy, autoridad/proyección, IDs/monedas existentes y hashes. Confirmar también las monedas existentes: MXN/USD propuestas no atribuyen moneda a registros históricos.
4. Identificar operadores/testers, roles y scopes; preservar visibilidad wildcard existente y no inventar grants.
5. Inspeccionar identidad/políticas/variables Costing y completar únicamente el mínimo aprobado, sin claves JSON ni lectura del valor del secreto.

Las26 migraciones actúan sobre el esquema global QA. La0061 también añade cinco tipos de secuencia Purchasing/Maintenance a todos los tenants con on-conflict-do-nothing, sin renumerar documentos; este efecto no se limita al tenant de pruebas. Constraints/índices y la ampliación NUMERIC pueden bloquear tablas o reescribirlas. Alembic usa una transacción PostgreSQL y el job tiene timeout10min con PGOPTIONS=-c lock_timeout=5000 -c statement_timeout=480000 (5s de espera de lock y480000ms/8min por sentencia): comprobar backup/PITR y ventana sin escrituras de negocio; tras fallo/timeout verificar head/rollback antes de reintentar, nunca stamp ni downgrade por atajo.

## Inspector gobernado implementado; ejecucion pendiente

El workflow .github/workflows/qa-inspect.yml exige confirmacion INSPECT_ERCLAVE_QA, tenant explicito, mismo SHA del workflow y del candidato exitoso, procedencia del repositorio y manifiesto de ocho imagenes validado sin ejecutar su contenido. Usa solo el digest Admin aprobado, WIF, environment qa-database y secreto QA por referencia; comparte exclusion de concurrencia con release.

Al ejecutarse creara/actualizara el job tecnico erclave-inspect-baseline-qa: sera escritura de configuracion Cloud Run, aunque su acceso DB sea READ ONLY. No se ha ejecutado. No migra, activa estructura, confirma moneda, asigna scopes ni escribe datos de negocio.

backend/scripts/inspect_qa_release_baseline.py acepta solo el socket exacto /cloudsql/erclave:us-central1:erclave-qa-postgres, tenant existente/activo y confirmacion explicita. Abre transaccion REPEATABLE READ READ ONLY y soporta esquema previo a organizacion mediante columnas disponibles. Emite JSON saneado con heads, hashes/IDs/cantidades estructurales, roles, huellas de scopes y secuencias; no exporta nombres, correos, perfil completo ni credenciales. El workflow impone default_transaction_read_only=on, lock_timeout=5s, statement_timeout=120s, task5min y max-retries0. El resumen de scopes es inventario, no aprobacion de alcance ni sustituto del guard operativo.

Metadatos Google confirman Cloud SQL PostgreSQL16 RUNNABLE, backup habilitado y PITR configurado con retencion de logs7dias; ultimo backup enumerado SUCCESSFUL el18oct07:10UTC. Esto acredita configuracion/listado, no restauracion ensayada ni head SQL. .local/chg336-public-baseline.json del19oct06:16UTC mantiene e57237f en siete APIs. Pendientes inspector remoto, perfil/mappings/actores y monedas por IDs reales. IAM Costing aplicado con alcance minimo segun la fila anterior; las tres variables GitHub tambien fueron escritas. No se ejecutaron jobs/migracion/datos/servicios/trafico/Hosting QA.

## Orden y condiciones técnicas

- Costing nuevo requiere identidad dedicada y URL pública antes del build único; resolver el número real del proyecto QA y el origen determinista, no adivinar sufijos opacos. Referenciar el secreto QA, sin copiar su valor.
- Construir una vez desde el mergeSHA certificado: ocho imágenes por digest y frontend con SHA256SUMS. Conservar run/procedencia; no reconstruir frontend después de aprobar.
- Migración y reconciliación de permisos son pasos independientes del release. Reconciliación no crea organización ni resetea usuarios/perfil/entitlements.
- Desplegar candidatos sin tráfico estable para los siete servicios existentes. La primera revisión Costing tiene la excepción de bootstrap ya descrita en el plan.
- Si falta estructura, usar las APIs Admin del candidato para el Emisor/Sociedades/Divisiones aprobados. **Perfil legacy no vacío:** OrganizationStore devuelve organization_review_required; el único CLI de backfill existente es Local y rechaza QA. Hace falta revisar mapping/resolutions y preparar un comando QA gobernado con hashes; nunca cambiar su guard ni asumir moneda para activar.
- Costing depende de Admin estable para sesión/códigos V2. Por tanto, sus tres centros se crean después de promover Admin V2 y antes de publicar frontend/UAT, conservando siempre el tenant autorizado. El guard pretráfico exige autoridad/cadena/monedas/scopes/Owner; no exige centros existentes.
- Si el primer release se detiene en el guard por falta de estructura, completar sólo la configuración aprobada y repetir release con el mismo SHA/candidate_run, migración/configuración apagadas cuando ya se ejecutaron. No reconstruir imágenes ni frontend.
- Promover únicamente las revisiones certificadas, verificando drift y rollback. Publicar los bytes exactos del frontend y ejecutar aceptación autenticada QA; no inferir paridad por smoke público o por datos sintéticos Local.

## Evidencia y rollback

Las lecturas privadas y snapshots de políticas se guardan bajo `.local`, sin secretos, tokens ni datos personales. Registrar sólo hashes, IDs técnicos, cantidades y resultado. Preservar las protecciones de rama/environments; si la herramienta no puede satisfacer una aprobación, informar la condición concreta y el siguiente paso necesario sin deshabilitarla.

Servicios: volver a revisiones exactas previas y registrar el estado restaurado; Hosting: release previo. DB tras escrituras: PITR/forward-fix revisado, sin downgrade improvisado. Datos sintéticos nuevos: desactivar únicamente IDs propios cuando sea válido y preservar historia; nunca rebobinar contadores ni borrar documentos.

## APIs afectadas

No se modifica contrato de negocio en este registro. Se consumen GitHub PR/checks/merge/workflows y, según etapas y baseline, APIs Google QA de identidad/configuración y APIs dueñas `POST /v1/organization/fiscal-issuers`, `POST /v1/organization/societies`, `POST /v1/organization/divisions`, `POST /v1/cost-centers`. Permisos de creación puntuales Admin/Costing, tenant efectivo e idempotencia se conservan. Rutas exactas y resultados se agregan conforme se ejecuten; no declarar consumidos endpoints pendientes.
