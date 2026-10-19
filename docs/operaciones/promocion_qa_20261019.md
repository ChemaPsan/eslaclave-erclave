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
| PR | [#16](https://github.com/ChemaPsan/eslaclave-erclave/pull/16) MERGED por squash; mergeSHA/release_sha=6312fc8e43efa90a82dc84b161abe47d6bab7ad8 |
| CI | Inicial39208234912 para60f698b aprobado; final39210360271 success paraafc05c9 antes de fusionar. PR16 ya no esta abierto |
| Candidato QA | Run39210783602 SUCCESS para 6312fc8e43efa90a82dc84b161abe47d6bab7ad8; qa-build aprobado legitimamente por API, sin deshabilitar protecciones. Ocho imagenes del manifiesto validadas |
| Backup bajo demanda | Backup1792391753356 SUCCESSFUL, final2026-10-19T06:37:24.690Z. La solicitud operation b620c800-2ab4-421b-9881-543900000032 anteriormente pendiente queda resuelta; no equivale a restauracion ensayada |
| Rama de registro | agent/chg336-qa-execution creada desde origin/main=6312fc8e43efa90a82dc84b161abe47d6bab7ad8; este seguimiento documental no modifica el release_sha |
| Evidencia Local previa | Verify833 aprobadas,351 omitidas sin DB,1 advertencia; focales PG/API y aceptación HTTP/Chrome por variantes, [acta CHG-335](paridad_local_qa_20261018.md) |
| Google/QA | Nueva cuenta autenticada: proyecto/Firebase erclave, numero370105017372; IAM, Hosting, instancia DB, politica del secreto, servicios y backups HTTP200. CostingSA GET200 tras su creacion; el404 inicial correspondia a la lectura previa. Metadatos actuales en .local/chg336-gcp-baseline-metadata.json, sin lectura del valor del secreto |
| Variables GitHub | Creadas/verificadas QA_COSTING_API_URL=https://costing-service-qa-370105017372.us-central1.run.app, QA_COSTING_RUNTIME_SERVICE_ACCOUNT=erclave-costing-qa@erclave.iam.gserviceaccount.com y QA_CONFIGURATION_TENANT_ID=ten_739ee59d765d5e14818674800d. Cuenta Costing ya creada segun fila IAM; Costing desplegado con bootstrap inicial segun fila de trafico |
| IAM Costing aplicado | CostingSA creada y confirmada GET200; tres grants minimos aplicados y confirmados: roles/cloudsql.client en proyecto, roles/secretmanager.secretAccessor solo en erclave-database-url-qa y roles/iam.serviceAccountUser al deployer solo sobre CostingSA. Total4 cambios IAM incluyendo identidad; .local/chg336-costing-iam-apply.json status completed_scoped_iam_changes3. El GET404 inmediato tras crear la cuenta fue propagacion transitoria; GET posterior200. Evidencia de intento anterior preservada, replanning hash f29ff344... antes de aplicar grants, sin ampliar otros bindings |
| Inspector ejecutado | Run39211465636 SUCCESS; execution erclave-inspect-baseline-qa-xcdlz,2026-10-19T06:44:34Z. Antes de migrar: head0036, tenant activo, perfil legacy EMPTY, tablas normalizadas ausentes; owner/scopes inventariados en seccion baseline |
| Artefactos inmutables | Imagenes artifact12167249838, ZIP SHA256=4be9b83c70061307638d696e9b9aa79abae82e7f290d714ed10e2d503f2aae78. Frontend artifact12167204077, ZIP SHA256=2aa1b95283b1e2bbfad73e9dbf9926e8d1af0710b8653eba6ffd04f5ff8bbbd5;106 archivos/hashes, ocho URLs y sourceSha verificados (.local/chg336-frontend-verification.json). Todavia no publicado en Hosting |
| Release39211797633 | migrate job SUCCESS: Cloud Run migrate completo06:48:03Z y configure06:49:39Z, cada uno1task/0failed/0retries. Ocho candidatos desplegados y smoke8PASSED. deploy job FAILURE solo en Check tenant operational readiness06:54:32Z: CONFIRMED_SOCIETY_CURRENCIES vacia causa JSONDecodeError antes de crear el job SQL guard. qa-traffic/frontend SKIPPED |
| Trafico efectivo | Siete servicios existentes conservan sus revisiones anteriores100%; candidatos nuevos0% con tag candidate. Costing nuevo tiene bootstrap permitido100% en costing-service-qa-00001-yoz; no afirmar cero trafico total ni promocion conjunta completada |
| Inspector postmigracion | Run39212276418 SUCCESS, execution erclave-inspect-baseline-qa-f2c2x, salida2026-10-19T06:57:54.287661Z: head20261014_0062 real. Tablas normalizadas presentes/vacias y autoridad false; perfil/Owner/scopes/secuencias previas preservados |
| Preservacion verificada | .local/chg336-preservation-verification.json compara baselines: perfil hash93a4ac936447cdca533ad11bc2fd1f094ba6eb9518bd2fe2e0f8cc14e630e2cf identico, rol/scope del unico Owner identicos;15 secuencias previas identicas en configuracion y next;5 nuevas maintenance.order, purchasing.order/receipt/requisition/supplier. No equivale a aceptacion de procedencia de documentos legacy |
| Publico posterior | .local/chg336-public-current.json,06:58:18Z:7 APIs estables oldSHAe572 HTTP200, Costing6312 HTTP200. Hosting env SHA256=3aa14880b3d987c431346b2c2abef55579b5ec51030feac0cd7c0ef4433e1f48 sin cambios, sin URL Costing |
| Login/organizacion | QA_APP_LOGIN_REQUIREDCDPmanual: Owner appQA pendiente en Chrome dedicado; Google Cloud ya resuelto. Helper ORG6POST preparado, no aplicado. Sin Emisor/Sociedades/Divisiones nuevos ni monedas por IDs confirmadas; aceptacion funcional pendiente |
| Validacion final CHG-336 | Implementacion inicial: .local/chg336-verify-final.log,864 aprobadas/352 omitidas sin DB/1 advertencia,30.57s. Registro de ejecucion final: .local/chg336-execution-record-verify-final.log,864 aprobadas/352 omitidas/1 advertencia,43.58s; todos los validadores y compilacion aprobados, documentacion coherente con QA0062. YAML4/Bash29 aprobados;16 huellas fuente/Word intactas. Estas pruebas Local no sustituyen aceptacion funcional QA |

El release_sha definitivo es 6312fc8e43efa90a82dc84b161abe47d6bab7ad8, squash merge de PR16 tras CI aprobado. Candidate run39210783602 usa ese SHA desde main; candidato SUCCESS y artefactos verificados. Conservar ese SHA, run exitoso, ocho digests, frontend/hashes y revisiones previas en release39211797633; el exito de build no acredita promocion. Esta nueva rama de seguimiento documental no reemplaza el candidato certificado.

## Digests aprobados del candidato

Origen: candidato39210783602, artefacto12167249838 y ZIP SHA256 `4be9b83c70061307638d696e9b9aa79abae82e7f290d714ed10e2d503f2aae78`. Registro comun: `us-central1-docker.pkg.dev/erclave/erclave-qa/{servicio}-service@{digest}`. No resolver de nuevo un tag como sustituto.

| Servicio | Digest aprobado |
|---|---|
| admin | `sha256:c3c713c8941280294e922b4f0f38137756ad01876942906d7d06f4e2d6185789` |
| production | `sha256:880266b98772d66ac7f061a0b52067d8a8ee947d4f8df1d9e5fbf83c1088b591` |
| inventory | `sha256:0b3804b5946174b2ce469856e0b226cff3f9fbcf6a7b6e3d00aaaee996d83138` |
| hr | `sha256:1f9a55fa77afc1ef604c32998d8cbacced0c7e15aa42534a64d3e894af1770f2` |
| sales | `sha256:454e63a1dbfae1b24e564d816ea66ae5bdc6bf344fc0b2157771b78052208c0e` |
| purchasing | `sha256:d35d01b437d0dd5049eb5c1e6bad563f12990f03b3f23790accb70637c7b61ce` |
| maintenance | `sha256:c43725d7784f20a27e471096e220b2bbcafd6e3b7e110270915d2b12f2787a5d` |
| costing | `sha256:3be6fcf35845661b6334f5e93e9f9f95aa9e352ed2e7116f1a96ad4024c08a64` |

## Revisiones efectivas despues del despliegue candidato

Evidencia previa conservada en .local/chg336-gcp-pre-deploy-metadata.json. .local/chg336-candidate-technical-smoke.json acredita8/8 candidatos version6312fc8 y ready200; no equivale a aceptacion funcional ni a promocion de las siete URLs estables.

| Servicio | Revision estable anterior100% | Revision candidate nueva0% |
|---|---|---|
| Admin | admin-service-qa-00034-sig | admin-service-qa-00036-vuy |
| Production | production-service-qa-00020-gip | production-service-qa-00022-mid |
| Inventory | inventory-service-qa-00015-suv | inventory-service-qa-00017-pav |
| HR | hr-service-qa-00015-map | hr-service-qa-00017-gow |
| Sales | sales-service-qa-00010-roz | sales-service-qa-00012-tof |
| Purchasing | purchasing-service-qa-00005-gaf | purchasing-service-qa-00007-wux |
| Maintenance | maintenance-service-qa-00005-yij | maintenance-service-qa-00007-gaz |

Costing no tenia revision estable previa: costing-service-qa-00001-yoz recibe100% inicial por bootstrap aprobado. qa-traffic se omitio; no hubo cambio conjunto de trafico estable de los siete servicios existentes ni publicacion de Hosting.

El fallo de06:54:32Z ocurre al deserializar la variable vacia de monedas en Python, antes de gcloud run jobs deploy del guard operativo. No se ejecuto el guard SQL ni se recibio qa_currency_confirmation_required desde ese guard. Resolver IDs reales y variable revisada tras crear Sociedades con actor legitimamente autenticado; conservar SHA/digests y certificar de nuevo las revisiones exactas si se repite deploy. No repetir migracion/configuracion ya terminadas por el fallo posterior.

## Baseline previo a escrituras

1. Consultar versiones públicas actuales y revisiones/imágenes/tráfico Cloud Run; registrar Hosting previo.
2. Verificar Cloud SQL QA, head efectivo y recuperación/PITR antes de migrar0036→0062. Las migraciones se ejecutan sólo mediante el workflow aprobado.
3. Verificar tenant, perfil legacy, autoridad/proyección, IDs/monedas existentes y hashes. Confirmar también las monedas existentes: MXN/USD propuestas no atribuyen moneda a registros históricos.
4. Identificar operadores/testers, roles y scopes; preservar visibilidad wildcard existente y no inventar grants.
5. Inspeccionar identidad/políticas/variables Costing y completar únicamente el mínimo aprobado, sin claves JSON ni lectura del valor del secreto.

Las26 migraciones actúan sobre el esquema global QA. La0061 también añade cinco tipos de secuencia Purchasing/Maintenance a todos los tenants con on-conflict-do-nothing, sin renumerar documentos; este efecto no se limita al tenant de pruebas. Constraints/índices y la ampliación NUMERIC pueden bloquear tablas o reescribirlas. Alembic usa una transacción PostgreSQL y el job tiene timeout10min con PGOPTIONS=-c lock_timeout=5000 -c statement_timeout=480000 (5s de espera de lock y480000ms/8min por sentencia): comprobar backup/PITR y ventana sin escrituras de negocio; tras fallo/timeout verificar head/rollback antes de reintentar, nunca stamp ni downgrade por atajo.

## Inspector gobernado ejecutado; baseline anterior a migracion

El workflow .github/workflows/qa-inspect.yml exige confirmacion INSPECT_ERCLAVE_QA, tenant explicito, mismo SHA del workflow y del candidato exitoso, procedencia del repositorio y manifiesto de ocho imagenes validado sin ejecutar su contenido. Usa solo el digest Admin aprobado, WIF, environment qa-database y secreto QA por referencia; comparte exclusion de concurrencia con release.

El workflow creo/actualizo y ejecuto el job tecnico erclave-inspect-baseline-qa, escritura de configuracion Cloud Run con DB READ ONLY. Run39211465636 y execution erclave-inspect-baseline-qa-xcdlz concluyeron SUCCESS. El inspector no migro, activo estructura, confirmo moneda, asigno scopes ni escribio datos de negocio. La migracion posterior se ejecuta en release39211797633.

backend/scripts/inspect_qa_release_baseline.py acepta solo el socket exacto /cloudsql/erclave:us-central1:erclave-qa-postgres, tenant existente/activo y confirmacion explicita. Abre transaccion REPEATABLE READ READ ONLY y soporta esquema previo a organizacion mediante columnas disponibles. Emite JSON saneado con heads, hashes/IDs/cantidades estructurales, roles, huellas de scopes y secuencias; no exporta nombres, correos, perfil completo ni credenciales. El workflow impone default_transaction_read_only=on, lock_timeout=5s, statement_timeout=120s, task5min y max-retries0. El resumen de scopes es inventario, no aprobacion de alcance ni sustituto del guard operativo.

Metadatos Google confirman Cloud SQL PostgreSQL16 RUNNABLE, backup habilitado y PITR configurado con retencion de logs7dias; backup automatizado enumerado SUCCESSFUL el18oct07:10UTC y backup bajo demanda1792391753356 SUCCESSFUL final19oct06:37:24.690Z. Esto acredita configuracion/listado, no restauracion ensayada ni head SQL. .local/chg336-public-baseline.json del19oct06:16UTC mantiene e57237f en siete APIs. Baseline del inspector antes de migrar: tenant activo, head20260913_0036, perfil legacy EMPTY con SHA256=93a4ac936447cdca533ad11bc2fd1f094ba6eb9518bd2fe2e0f8cc14e630e2cf; tablas normalizadas todavia ausentes. Una membresia Owner activa mem_c221afc467d65083a8ed730d35, rol rol_0040d63992545b9f9db16e1366, scope hash=710ba9304ee30af68f147beae8ba1f3d0edf72044f81a8c7e7929296ecd7efa8 y legacy unrestricted=true. Este permiso existente incluye futuras Divisiones bajo la semantica vigente; no se creo wildcard nuevo ni se modifico metadata. Migracion/configuracion concluyeron SUCCESS. Inspector postmigracion39212276418 SUCCESS confirma head0062; comparacion automatizada de perfil, Owner/scopes y15secuencias previas sin cambios. Tablas normalizadas presentes/vacias, autoridad false. No se atribuye contexto ni moneda a documentos historicos por esta preservacion estructural. No se requiere mapping de un perfil vacio; datos historicos sin procedencia siguen sin atribuirse. Monedas por IDs reales siguen pendientes de crear Sociedades. IAM Costing y tres variables GitHub ya aplicados; datos organizacionales y Hosting pendientes; candidatos8 ya desplegados, siete estables conservados y Costing con bootstrap100% permitido.

Plan estructural actualizado por raiz con baseline verificado y login Owner pendiente: SHA256=cb1714304e4bfe94579f4624fe2a0f20318ae8c293def10fbe22fd8849ec42f1. ORG6POST fue revisado offline y nunca aplicado; seis POST previstos para1Emisor/2Sociedades/3Divisiones, sin IDs reales de Sociedades todavia. El mismo release_sha permanece 6312fc8e43efa90a82dc84b161abe47d6bab7ad8; no fusionar seguimiento documental a main antes de terminar el release porque qa-inspect exige github.sha=release_sha.

El usuario solicito login de la aplicacion QA en Chrome dedicado para ejecutar APIs de organizacion con actor autenticado; la sesion Google Cloud ya esta resuelta. CDP sigue QA_APP_LOGIN_REQUIRED y solicitud de login async pendiente. El login de app/actor debe comprobar tenant y membresia efectiva; Google Cloud autenticado no acredita sesion de la app. No se registra como completado.

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

### Mutaciones tecnicas ejecutadas y lecturas de comprobacion

No se modifica ningun contrato de negocio en este seguimiento. Las siguientes APIs/operaciones administrativas si fueron consumidas, bajo proyecto QA erclave y gates aprobados:

| Sistema | Metodo/ruta u operacion exacta | Alcance efectivo |
|---|---|---|
| GitHub | POST /repos/ChemaPsan/eslaclave-erclave/pulls; PUT /repos/ChemaPsan/eslaclave-erclave/pulls/16/merge | PR16 y squash merge certificado |
| GitHub Actions | POST /repos/ChemaPsan/eslaclave-erclave/actions/workflows/{workflow_id}/dispatches; POST /repos/ChemaPsan/eslaclave-erclave/actions/runs/{run_id}/pending_deployments | candidate39210783602, inspect39211465636/postinspect39212276418 y release39211797633; gates protegidos aprobados sin bypass |
| GitHub variables | POST /repos/ChemaPsan/eslaclave-erclave/actions/variables | Tres variables Costing/tenant creadas y verificadas, sin secretos DB |
| IAM | POST iam.googleapis.com/v1/projects/erclave/serviceAccounts; POST cloudresourcemanager.googleapis.com/v1/projects/erclave:setIamPolicy | Cuenta Costing y cloudsql.client; preserva bindings ajenos |
| Secret Manager | POST secretmanager.googleapis.com/v1/projects/erclave/secrets/erclave-database-url-qa:setIamPolicy | secretAccessor solo sobre ese secreto; valor no leido |
| IAM cuenta | POST iam.googleapis.com/v1/projects/erclave/serviceAccounts/erclave-costing-qa@erclave.iam.gserviceaccount.com:setIamPolicy | serviceAccountUser para deployer solo en CostingSA |
| Cloud SQL Admin | POST sqladmin.googleapis.com/sql/v1beta4/projects/erclave/instances/erclave-qa-postgres/backupRuns | Backup bajo demanda1792391753356 SUCCESSFUL |
| Cloud Run Admin | gcloud run jobs deploy y gcloud run jobs execute | erclave-inspect-baseline-qa; erclave-migrate-qa (alembic upgrade head); erclave-configure-tenant-qa (configure_qa_tenant.py). Inspector postmigracion SUCCESS; no job operational-preflight creado por fallo previo |
| Cloud Run Admin | gcloud run deploy {service}-service-qa --image {digest} --tag candidate | Ocho servicios, siete existentes sin trafico nuevo y Costing bootstrap100%; identidades, secretos por referencia y env del candidato |
| APIs tecnicas de candidatos | GET /health, GET /ready, GET /version en ocho URLs candidate | Smoke8PASSED y comprobacion adicional read-only8/8; SHA6312 y readiness DB compatibles |

Las APIs de negocio POST /v1/organization/fiscal-issuers, POST /v1/organization/societies, POST /v1/organization/divisions y POST /v1/cost-centers no se han ejecutado en este corte. Helper ORG6POST no aplicado; no hay payloads de negocio nuevos, grants de scope ni mapping historico inventado. Trafico y Hosting permanecen en su etapa pendiente, salvo el bootstrap Costing explicitamente registrado.
