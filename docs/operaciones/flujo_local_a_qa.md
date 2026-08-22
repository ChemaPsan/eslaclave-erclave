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

Comparar el candidato con el SHA certificado que reporta `/version` en cada servicio QA. Si los cuatro servicios no comparten version, detener la promocion conjunta y preparar un delta por servicio. Clasificar cada archivo y efecto:

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
2. Autorizar `qa-database` solo si el delta necesita migracion/configuracion. Hoy `qa-release.yml` obliga Alembic y reconciliacion estructural juntos en cada release; hasta volverlos condicionales, exponer la limitacion y pedir autorizacion explicita para ambos. Nunca ejecutar Alembic QA directamente desde Local.
3. Autorizar `qa-services`; validar candidatos con imagen/digest, ambiente, `/health`, `/ready`, `/version`, auth, CORS y dependencias.
4. Antes de `qa-traffic`, confirmar que las revisiones estables no cambiaron, registrar las cuatro revisiones previas y definir rollback compensatorio. Si una promocion intermedia falla, restaurar los servicios ya modificados antes de reintentar.
5. Verificar 100% de trafico por servicio y repetir smoke en URLs estables.
6. Autorizar `qa-frontend`; comprobar HTTP 200 y el `env.js` realmente publicado: modo API/Firebase, cuatro URLs QA y ausencia de Local/Emulator/tenant/actor demo. El pipeline actual reconstruye el frontend en release; no declarar identidad build-once hasta construirlo en el candidato y verificar su hash al publicar.

## 6. Paridad funcional y datos

Paridad significa mismo codigo y comportamiento certificado para las capacidades habilitadas; no igualdad de datasets, entitlements o contenido. QA debe ejecutar esas capacidades con APIs reales y Cloud SQL QA. Los catalogos vacios permanecen vacios; no crear registros para aparentar paridad ni copiar/exportar la base Local hacia QA. Ventas, Integraciones y capacidades futuras continuan desactivadas hasta tener backend certificado.

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

- hacer atomica o compensatoria la promocion multi-servicio;
- construir el frontend una sola vez en el candidato y verificar su hash al publicar;
- fortalecer provenance/attestation de artifacts e imagenes;
- separar migracion y configuracion de tenant como jobs condicionales;
- agregar reintentos/rollback automatizado a la correccion Backoffice;
- ampliar smoke autenticado, CORS/IAM y post-deploy de Hosting.
