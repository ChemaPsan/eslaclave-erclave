---
name: erclave-environment-boundaries
description: Verificar y proteger las fronteras de Local, QA y Produccion en ERClave. Usar antes de levantar servicios, conectar APIs o bases, ejecutar migraciones, seeds o pruebas, usar Firebase, desplegar, promover releases o realizar cualquier accion que pueda leer o escribir recursos de otro ambiente.
---

# Proteger ambientes ERClave

## Reunir evidencia

1. Leer `AGENTS.md`, `docs/arquitectura/fronteras_ambientes_local_qa_produccion.md`, `docs/contexto/ESTADO_ACTUAL.md` y `docs/contexto/TENANTS.md`.
2. Revisar `git status --short`.
3. Clasificar la operacion como `read-only`, `local-write`, `qa-write` o `prod-write`.
4. Identificar codigo, URLs, bases, identidad, secretos, integraciones, tenant y observabilidad efectivos.

No inferir el ambiente por el host del proceso. Un servicio en localhost que consume un recurso QA es **local conectado a QA**.

## Aplicar la frontera

### Local aislado

- Usar exclusivamente loopback, PostgreSQL `erclave_local` y Firebase Emulator.
- Resolver autorizacion, membresias, permisos y entitlements en `admin-service` local.
- No abrir Cloud SQL Auth Proxy ni consumir APIs, Firebase, secretos o integraciones QA/Prod.
- Usar solamente datos sinteticos y el tenant permitido.

### Local conectado a QA

- Requerir autorizacion explicita del usuario para el recurso, tenant, acciones y duracion.
- Preferir solo lectura.
- Tratar migracion, seed, carga de datos, deploy y mutacion como autorizaciones independientes.

### QA

- Exigir recursos, secretos, identidad y datos QA separados de Produccion.
- Confirmar el tenant efectivo antes de escribir.
- No promover un modulo por la sola existencia de su schema; exigir servicio, contrato, entitlement, pruebas, observabilidad y rollback.

### Produccion

- No crear ni modificar infraestructura sin autorizacion explicita del usuario aprobador.
- Promover los mismos artefactos inmutables certificados en QA.
- No promover datos, secrets, fixtures, URLs ni usuarios QA.
- Exigir backup, RPO de 15 minutos, RTO de 2 horas, smoke no destructivo, monitoreo y rollback.

## Ejecutar preflight

Antes de actuar, mostrar o comprobar ambiente, clasificacion, servicios, base sin credenciales, auth, APIs, tenant, mutaciones y rollback. Detenerse ante cualquier discrepancia. Si el usuario pide solo un plan, realizar unicamente comprobaciones de lectura.

## Promover releases

1. Validar Local con Firebase Emulator.
2. Obtener aprobacion directa del usuario antes de cualquier autodeploy o promocion.
3. Construir una vez y registrar hashes o digests.
4. Desplegar a QA y ejecutar gates funcionales, seguridad, aislamiento, migracion y observabilidad.
5. Promover a Produccion exactamente los artefactos aprobados.

El primer release incluye Produccion, Almacenes, Recursos Humanos, Administracion, Ventas y Backoffice. Cada modulo debe estar desplegado y certificado previamente en QA.

## Cerrar

Informar ambiente y dependencias usados, validaciones, tenant efectivo, escrituras externas, migraciones, seeds, cargas, despliegues, riesgos y rollback.
