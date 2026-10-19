---
name: erclave-qa-release
description: Preparar, revisar y promover cambios de ERClave desde Local aislado hacia QA mediante candidatos inmutables, aprobaciones separadas, datos reales persistidos, smoke tests, evidencia y rollback. Usar cuando se pida desplegar o liberar a QA, preparar un candidato, ejecutar qa-candidate o qa-release, crear revisiones Cloud Run, migrar o configurar QA, mover trafico, publicar Firebase Hosting, corregir configuracion Backoffice o comprobar paridad Local-QA.
---

# Liberar ERClave a QA

## Preparar

1. Usar `$erclave-environment-boundaries` si aun no esta activa y leer `docs/operaciones/flujo_local_a_qa.md`, `infra/qa/README.md`, `docs/contexto/ESTADO_ACTUAL.md` y `PENDIENTES.md`.
2. Consultar siempre Arquitectura, Seguridad y QA/Release en `AGENTES.md`. Agregar Datos y Custodio DB si hay migracion/configuracion/datos; API si cambia backend/auth/contrato; negocio y tecnico del modulo si cambia funcionalidad.
3. Ejecutar `npm.cmd run session:context`, revisar Git y consultar `/version` por servicio. Detener la promocion conjunta si no comparten SHA, salvo que exista un plan explicito por servicio; calcular el delta contra cada version certificada.
4. Clasificar cada elemento como codigo, contrato, migracion, configuracion estructural, dato funcional, secreto/IAM, servicio, trafico o frontend.
5. Declarar `Agentes consultados`, ambiente, tenant, mutaciones, aprobaciones, evidencia y rollback antes de escribir.

No inferir autorizacion conjunta: publicar la rama, abrir PR, fusionar, `qa-build`, `qa-database`, `qa-services`, `qa-traffic` y `qa-frontend` son acciones independientes. Un permiso para codigo no autoriza datos, migraciones, IAM ni trafico.

## Certificar Local

1. Usar exclusivamente `backend/scripts/start_local.ps1`, PostgreSQL `erclave_local` y Firebase Emulator `demo-erclave`.
2. Ejecutar `npm.cmd run verify`; rechazar cualquier `ERCLAVE_TEST_DATABASE_URL` que no sea loopback/`erclave_local`.
3. Probar el corte vertical con permisos, rechazo, aislamiento, idempotencia y persistencia tras recarga.
4. Confirmar que modo API no usa mocks, `localStorage`, tenant o actor demo como fuente de verdad.
5. Construir una matriz de capacidades Local/QA; no declarar paridad por pruebas con dobles.

## Construir y promover

1. Solicitar autorizacion antes de publicar la rama, abrir PR o fusionar. Fusionar un PR validado a `main`; no desplegar un working tree ni reconstruir despues de aprobar.
2. Despachar `qa-candidate.yml` con SHA completo y confirmacion. Registrar run, ocho digests (incluido Costing básico), frontend sanitizado y SHA256SUMS; comprobar procedencia y SHA del candidato.
3. Despachar `qa-release.yml` con el mismo `release_sha` y run candidato. Autorizar solo el siguiente gate solicitado.
4. En `qa-database`, ejecutar migracion/configuracion solo si el plan las requiere y fueron autorizadas por separado. Los pasos son condicionales independientes y parten apagados. Configuración exige QA_CONFIGURATION_TENANT_ID existente: actualiza catálogo global y grants de owners de sistema existentes sólo en ese tenant, sin crear/resetear usuarios, membresías, perfil, entitlements ni estructura organizacional. Declarar y autorizar ese alcance; no llamar seeds demo ni fingir que se omitió una escritura ejecutada. Nunca ejecutar Alembic QA desde una terminal local.
5. En `qa-services`, crear revisiones candidatas y probar `/health`, `/ready`, `/version`, configuracion y contratos sin mover trafico cuando el servicio ya existe.
   Exigir también el guard operativo READ ONLY sobre `QA_CONFIGURATION_TENANT_ID`: autoridad/proyección, cadena organizacional activa, monedas explícitas por ID (`QA_CONFIRMED_SOCIETY_CURRENCIES`), scopes efectivos y Owner operativo. DDL no activa organización. Si falta configuración, bloquear tráfico y preparar un plan revisado; no usar default MXN ni ejecutar seeds. La estructura sintética QA tiene su propia autorización y baseline, sin copiar Local.
6. En `qa-traffic`, descargar el manifiesto `qa-candidate-revisions.json` certificado por smoke en qa-services y el de ocho imágenes aprobado. Exigir mismo SHA, revisión, digest resuelto, URL etiquetada y tráfico estable registrado al certificar; no resolver un tag nuevo como sustituto del candidato aprobado. Revalidar identidad y tráfico antes de cada cambio y al terminar. Si falla un servicio, detenerse y restaurar los ya intentados antes de reintentar. Verificar cada revision exacta al 100%.
7. En `qa-frontend`, publicar el artefacto sanitizado y comprobar el contenido realmente servido, no solo el directorio local. El candidato construye el frontend una vez. Release descarga ese artefacto, verifica SHA256SUMS, sourceSha y las ocho URLs antes de DB/deploy; vuelve a verificar hashes antes de Hosting. Detenerse si hay drift de configuración. Comprobar además los bytes realmente servidos.
8. Detenerse si cambia SHA/digest, revision estable, base, tenant, imagen, identidad o configuracion respecto al plan.

## Datos y Backoffice

- QA usa Cloud SQL QA y datos reales persistidos que ya existan; no fabricar datos para aparentar paridad ni copiar/exportar la base Local hacia QA.
- Antes de escribir datos, bloquear el flujo hasta clasificar si se preservan datos existentes, se aplica configuracion estructural o se crean datos funcionales. Para estos ultimos declarar API o comando gobernado, tenant efectivo, objetivo, vigencia, limpieza/rollback y autorizacion propia.
- Seeds demo, cargas funcionales y benchmarks requieren autorizacion propia y nunca son consecuencia implicita de una liberacion.
- La allowlist Backoffice es independiente de roles `owner`. Usar `QA_BACKOFFICE_ADMIN_EMAILS`; nunca hardcodear correos ni conceder ownership de tenant implicitamente.
- Para una correccion solo de allowlist, usar `qa-admin-backoffice-config.yml`: misma imagen certificada, revision a 0%, `qa-services`, validacion, `qa-traffic` y rollback registrado.
- Despues de promover Backoffice, renovar sesion y comprobar manualmente administrador permitido y owner normal rechazado con `403`; no guardar tokens ni contraseñas.

## Cerrar

1. Verificar servicios publicos y frontend. Si el delta toca tenant, auth, permisos, datos o elimina mocks, exigir pruebas autenticadas positivas y negativas, incluyendo dos tenants autorizados; definir identidades y datos desechables sin exponer secretos.
2. Actualizar `ESTADO_ACTUAL.md`, `PENDIENTES.md`, fuentes del modulo y `TRAZABILIDAD.md` con hechos comprobados.
3. Registrar revisiones, SHA/digests, run, gates, tenant, escrituras, datos, pendientes y rollback.
4. Interpretar "igual a Local" como mismo codigo y comportamiento certificado de capacidades habilitadas, no como igualdad de datasets, entitlements o contenido. No afirmarlo si falta una prueba autenticada, si Local contiene una capacidad no desplegada o si QA muestra contenido simulado.
