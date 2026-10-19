# Candidato QA CONT-01 — CHG-290

> Evidencia histórica: conserva observaciones y decisiones de su fecha; no usar como estado o instrucciones actuales. Consultar [fuente vigente](../contexto/ESTADO_ACTUAL.md).

> CHG-291: el usuario corrigió el destino a Local. Esta preparación se conserva como antecedente; su publicación/promoción ya no es una tarea activa. No se ejecutó ningún gate QA.

Estado: preparado en rama local aislada `agent/chg290-cont01-qa`; no publicado ni desplegado. Solicitud del usuario: levantar CONT-01 en QA. Fecha: 2026-09-23.

Commit local certificado: `2a91d196175f589745f0e8831a053138f7475efa`, 27 archivos, worktree limpio después del commit. Cuerpo de PR preparado en `.local/qa-cont01-pr-body.md`. Pendiente autorización de publicación/PR según la guía; no hay PR ni run nuevo. El documento de este workspace agrega el SHA al registro ya incluido en el candidato, sin alterar ese commit.

## Base y alcance revisable

Base Git: `origin/main` = `e57237fe90319f88e1db8ed8d2e686604d2d9c54`, verificada mediante fetch y GitHub. Worktree: `.local/qa-cont01`. El árbol de trabajo original conserva sus cambios; este candidato incluye solamente:

- Preflight organizacional offline CONT-00 y sus 21 pruebas.
- CONT-01: modelos Admin, importador interno compatible, CLI restringido a Local, 30 pruebas y Alembic `20260922_0037`.
- Decisiones confirmadas, plan contable, modelo/ownership/diagrama y documentación de release.
- Dos ajustes de validadores: lectura independiente de LF/CRLF y cabezas de Alembic contrastadas por el validador documental existente, sin versiones históricas fijas en validate-agents.

Los cambios funcionales locales CHG-281…285 (timeouts, formularios, catálogos y contratos), manuales Word y cambios de skills permanecen fuera del candidato. La historia de trazabilidad describe trabajo del workspace original; no equivale al manifiesto de esta rama.

Agentes consultados: fichas de Arquitectura, Seguridad, QA/Release, Datos, Custodio DB, API y Administración negocio/técnica en `AGENTES.md`; sin delegación. Skills aplicadas: `erclave-environment-boundaries` y `erclave-qa-release`.

## Efectos

| Categoría | Efecto del candidato |
|---|---|
| Código | Añade modelos e importador interno Admin, sin consumidores API nuevos |
| Contratos/frontend | Sin cambios |
| Migración | 0036 → 0037: cinco tablas nuevas en admin, claves/índices por tenant y FKs internas |
| Datos funcionales | Sin backfill, seeds de negocio ni copias Local→QA |
| Autoridad operativa | organization.profile y endpoints actuales permanecen vigentes |
| Configuración de negocio | Centros de costos/UI/scopes y Accounting siguen pendientes |
| Secretos/IAM | No requiere cambios |
| Servicios/tráfico/Hosting | Pipeline existente construye/promueve siete imágenes y publica Hosting; requiere sus gates |

La migración afecta el esquema compartido; no inserta registros de ningún tenant. El CLI de backfill sólo admite `ten_739ee59d765d5e14818674800d` en `127.0.0.1:5434/erclave_local`, nunca QA. No inferir importación remota por desplegar el módulo Python.

## Lecturas QA y disponibilidad

Hosting `https://erclave.web.app/env.js`: HTTP 200; modo API y Firebase, siete URLs HTTPS QA. No se almacenaron credenciales ni tokens de sesión.

Las siete URLs servidas por Hosting, `https://<servicio>-service-qa-kgnfw5neua-uc.a.run.app/version`, respondieron HTTP 503 de Google Frontend el 2026-09-23. Las URLs numéricas históricas tampoco devolvieron versión. No se certifica el SHA ejecutado ni se atribuye el fallo a una causa no comprobada. La lectura debe repetirse antes de promoción y, si persiste, investigar Cloud Run mediante acceso de lectura autorizado.

El [release histórico 34932659212](https://github.com/ChemaPsan/eslaclave-erclave/actions/runs/34932659212) sí registra `preflight`, `migrate`, `deploy_candidate`, `promote_traffic` y `frontend` exitosos. La última revisión QA documentada es `20260913_0036`; no se abrió Cloud SQL en esta preparación. Estas evidencias históricas no sustituyen el estado actual de los servicios.

Reintento posterior del mismo día: HTTP 500 en las siete APIs. Se conserva la evidencia 503 inicial; en ambas consultas faltó un payload de versión. No se realizaron mutaciones QA.

## Limitación real de qa-database

El workflow `qa-release.yml` exige actualmente `execute_database_migration=true` y `configure_qa_tenant=true`. No permite liberar sólo DDL. La configuración ejecuta `seed_admin_mvp.py` y `seed_admin_qa_demo.py`; su alcance comprobado es mayor que crear cinco tablas:

- Actualiza el catálogo global de permisos e inactiva códigos deprecados.
- Asegura `admin.role.permissions.manage` para roles de sistema owner activos **de todos los tenants**, sin filtro por tenant.
- Reconcilia el tenant demo `ten_739ee59d765d5e14818674800d`, usuario/membresía/rol Owner, perfil inicial si falta, módulos y grants. Deja activos admin, production, inventory, hr, sales, purchasing y maintenance; desactiva otros módulos del demo.

CONT-01 no necesita esas escrituras de configuración. No ejecutarlas como consecuencia implícita de la petición de deploy: requieren autorización explícita de ese alcance o un corte previo que haga condicional la configuración. No se han ejecutado. Tampoco se conoce si serían no-op en QA; idempotencia no equivale a ausencia de cambios.

## Gates y secuencia pendiente

1. Validación local aprobada; registrar commit/diff y exigir CI remoto después de publicación.
2. Según la guía del repositorio, obtener autorización concreta de publicación de rama, creación de PR y fusión después del check `Complete repository verification`.
3. Construir con `qa-candidate.yml`, SHA completo y `BUILD_ERCLAVE_QA`; aprobación propia `qa-build`. Conservar run y siete digests.
4. Resolver disponibilidad/versiones y confirmar revisión DB/PITR de QA. No promover conjuntamente sin base certificada ni plan explícito por servicio.
5. Resolver el alcance de configuración descrito arriba; con autorizaciones independientes, despachar `qa-release.yml` con el SHA/run certificados. Nunca usar Alembic, Firebase deploy o gcloud run localmente como sustituto.
6. `qa-services`: candidatos al 0%, comprobar readiness, health y versión. Registrar las siete revisiones estables inmediatamente antes de `qa-traffic`; no reutilizar valores históricos sin contrastar drift.
7. `qa-traffic`: promoción compensatoria y verificación exacta al 100%. `qa-frontend`: publicar/verificar Hosting real. El frontend sigue reconstruyéndose durante release; no atribuirle build-once.

No se sustituyen aprobaciones humanas de GitHub Environments ni se conceden IAM/permisos nuevos para eludirlas.

## Validación y rollback

Candidato aislado: npm.cmd run verify aprobado, todos los validadores y compilación, 344 backend aprobadas/67 omitidas sin DB. Corrida focalizada: 51 aprobadas/cero omitidas, incluidas 9 PostgreSQL; perfil y cinco tablas del tenant Local permitido intactos al terminar. Las 58 integraciones previas omitidas no se reejecutaron con DB. git diff --check aprobado. La corrida CHG-289 del workspace completo obtuvo 355 pruebas backend y 67 omitidas; no se atribuye ese resultado a esta rama reducida. Sus 51 focalizadas incluyeron nueve PostgreSQL contra el tenant Local permitido, con rollback de fixtures.

Rollback de código/tráfico: revisiones estables verificadas antes de promover. Hosting: release anterior. DB: conservar el esquema aditivo sin uso si se restaura el código anterior. Downgrade 0037 sólo admite las cinco tablas vacías y bloquea si existe cualquier fila; después de uso, forward-fix, no borrado de historia. No se ejecuta downgrade remoto en esta preparación.

APIs afectadas: ninguna API funcional modificada. Consumidas sin cambio: `GET /version` de Admin, Production, Inventory, HR, Sales, Purchasing y Maintenance; respuestas 503, sin payload de versión. `GET /env.js` de Hosting respondió 200. Sin UAT autenticada nueva ni prueba con dos tenants.
