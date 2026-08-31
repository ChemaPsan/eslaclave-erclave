# Preparacion del candidato QA de siete servicios - 2026-08-31

## Alcance

Preparar, sin ejecutar escrituras externas, el siguiente candidato Local a QA con:

- Admin y Backoffice;
- Produccion;
- Inventarios;
- Recursos Humanos;
- Ventas;
- Compras;
- Mantenimiento;
- frontend sanitizado para las siete APIs.

Produccion permanece fuera de alcance. Esta preparacion no autoriza publicar rama, abrir o fusionar PR, construir imagenes, migrar Cloud SQL, configurar el tenant, crear identidades, desplegar revisiones, mover trafico ni publicar Firebase Hosting.

## Agentes consultados

- Arquitecto senior de plataforma SaaS.
- Ingeniero senior de seguridad, IAM y supply chain.
- Ingeniero senior de QA, validadores y release.
- Arquitecto senior de datos y Custodio DB, por las migraciones `0024` a `0029`.
- Arquitectura API y agentes funcional/tecnico de Compras y Mantenimiento.

No hubo delegacion.

## Delta contra QA certificado

- SHA certificado QA comprobado por `/version` en los cinco servicios: `a6524e44e5df9eaf6232adbe2a70bbfd65516f3c`.
- Revision de base QA: `20260821_0023`.
- Revision objetivo del candidato: `20260825_0029`.
- Migraciones pendientes: Compras `0024` a `0026`, Mantenimiento `0027` y `0028`, capacidad multidia de Produccion `0029`.
- Servicios nuevos para QA: `purchasing-service-qa` y `maintenance-service-qa`.
- El candidato debe producir siete digests; no se reutilizan imagenes reconstruidas despues de la aprobacion.

## Preflight de ambiente

| Elemento | Valor preparado | Estado |
|---|---|---|
| Clasificacion actual | `local-write` sobre archivos del repositorio | Sin escritura QA |
| Proyecto QA | `erclave` | Destino documentado, no conectado |
| Base QA | Cloud SQL `erclave_qa` mediante secreto | No leida ni modificada |
| Tenant estructural | `ERClave Demo QA`, `ten_739ee59d765d5e14818674800d` | Reconciliacion pendiente de gate |
| Auth | Firebase QA + autorizacion ERClave | Sin sesiones ni tokens usados |
| Produccion | Fuera de alcance | Bloqueada |

## Prerrequisitos bloqueantes antes de construir

1. Instalar o exponer Node 20/npm en la terminal de certificacion y ejecutar `npm.cmd run session:context` y `npm.cmd run verify`.
2. Aprovisionar con autorizacion `qa-write` independiente las identidades `erclave-purchasing-qa` y `erclave-maintenance-qa`, sin llaves JSON, con los grants minimos declarados en `infra/qa/identity-plan.json`.
3. Configurar y verificar las variables no secretas `QA_PURCHASING_RUNTIME_SERVICE_ACCOUNT`, `QA_MAINTENANCE_RUNTIME_SERVICE_ACCOUNT`, `QA_PURCHASING_API_URL` y `QA_MAINTENANCE_API_URL`.
4. Registrar las revisiones estables de Cloud Run antes de mover trafico. El preflight publico ya confirmo que los cinco servicios vigentes responden `health=ok`, `ready`, base configurada y el mismo SHA `a6524e44e5df9eaf6232adbe2a70bbfd65516f3c`.
5. Revisar que las pruebas funcionales informadas por el propietario cubren el alcance actual y completar la evidencia automatizada local del SHA final.
6. Fusionar un PR aprobado a `main`; el working tree o una rama sin fusionar no son desplegables.

## Gates y autorizaciones independientes

1. Publicar rama.
2. Abrir PR.
3. Fusionar PR a `main`.
4. Ejecutar `qa-candidate.yml` con `BUILD_ERCLAVE_QA` y el SHA completo.
5. Autorizar `qa-database`: el workflow vigente obliga tanto Alembic `0023 -> 0029` como reconciliacion estructural del tenant.
6. Autorizar `qa-services`: crea siete revisiones candidatas. Compras y Mantenimiento, al no existir, pueden recibir trafico inicial por la restriccion documentada de Cloud Run.
7. Autorizar `qa-traffic` tras registrar las siete revisiones anteriores o la ausencia de revision para servicios nuevos.
8. Autorizar `qa-frontend` para publicar el artefacto sanitizado con siete URLs QA.

Seeds funcionales, datasets, IAM adicional, secretos y Produccion requieren autorizaciones distintas y no forman parte implicita del release.

## Verificacion posterior

- `/health`, `/ready` y `/version` de las siete revisiones candidatas.
- SHA exacto, ambiente `qa`, base configurada y URL publica HTTPS.
- Smoke autenticado positivo y negativo: token ausente/invalido, tenant no miembro, modulo inactivo y permiso faltante.
- Aislamiento con dos tenants desechables autorizados.
- Compras: proveedor a recepcion, idempotencia y conciliacion.
- Mantenimiento: orden correctiva, RH, refacciones, bloqueo/liberacion y conciliacion.
- Frontend publicado sin localhost, Emulator, tenant ni actor demo.
- Persistencia tras recarga y ausencia de datos operativos simulados.

## Rollback

- Servicios existentes: regresar trafico a las revisiones registradas antes del gate.
- Servicios nuevos: desactivar entitlements y retirar trafico; conservar datos para auditoria.
- Frontend: restaurar el release anterior de Firebase Hosting.
- Base: PITR o `forward-fix`; no ejecutar downgrade improvisado despues de admitir escrituras.
- Configuracion: reconciliar entitlements al conjunto anterior de cinco servicios.
