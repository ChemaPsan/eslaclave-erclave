# ERClave: instrucciones operativas para Codex

Estas reglas aplican a todo el repositorio. `AGENTES.md` conserva el conocimiento funcional y los roles especializados; este archivo define cómo ejecutar cambios.

## Antes de modificar

1. Ejecutar `npm run session:context` y leer `docs/contexto/INICIO_SESION.md`.
2. Leer `AGENTES.md`, los documentos de `docs/contexto/` y el documento del módulo en `modulos/`.
3. Para arquitectura, datos, seguridad o ambientes, consultar los documentos pertinentes en `docs/arquitectura/`.
4. Identificar el módulo, microfrontend, microservicio, dueño del dato, contratos y dependencias afectadas.
5. Revisar `git status --short` y preservar cambios locales ajenos.
6. No inventar reglas de negocio, entidades, permisos ni estados. Registrar supuestos pendientes si la fuente de verdad no los define.

## Reglas obligatorias

- Antes de levantar servicios, conectar recursos, probar en QA, migrar, ejecutar seeds o desplegar, usar `$erclave-environment-boundaries` y leer `docs/arquitectura/fronteras_ambientes_local_qa_produccion.md`.
- Para preparar, desplegar o verificar un candidato Local→QA, usar además `$erclave-qa-release` y `docs/operaciones/flujo_local_a_qa.md`.
- "Levantar en local" significa Local aislado: PostgreSQL local, APIs locales y Firebase Emulator. No permite Cloud SQL, APIs, Firebase, secretos ni integraciones QA/Produccion.
- "Local conectado a QA" requiere autorizacion explicita por recurso y alcance; migraciones, seeds, cargas, mutaciones y deploys requieren autorizaciones independientes.
- El usuario propietario es el aprobador de releases y del autodeploy del frontend; ninguna promocion ocurre antes de pruebas locales y su aprobacion directa.

- Mantener aislamiento por `tenant_id` en tablas, repositorios, APIs, índices y pruebas.
- Firebase autentica; ERClave resuelve membresías, permisos, entitlements y alcance mediante `admin-service`.
- No escribir datos pertenecientes a otro servicio ni crear FKs entre schemas de servicios.
- Mantener reglas críticas, autorización e idempotencia en backend, no sólo en frontend.
- El consumo HTTP del frontend vive en `frontend/api/`; las pantallas no llaman `fetch` directamente.
- Todo texto visible nuevo o modificado debe existir en español e inglés con las mismas variables.
- Toda interfaz nueva o modificada debe cumplir `docs/arquitectura/estandar_responsive_transversal.md`; ejecutar `npm run validate:responsive` y validar el ancho real del contenedor, no solo el viewport.
- No cambiar globalmente la composicion de componentes compartidos para corregir una sola pantalla. Las excepciones responsive deben usar una clase explicita del modulo o seccion, conservar el patron estandar fuera de ese alcance y quedar documentadas.
- Cambios de API deben actualizar OpenAPI, schemas, consumidores y pruebas en el mismo corte.
- Cambios persistentes deben incluir modelo, migración Alembic, índices/constraints, estrategia de datos existentes y prueba.
- No desplegar, migrar QA/Producción, publicar, enviar mensajes ni crear PRs salvo petición explícita.
- Para desarrollo local, pruebas manuales y datos dummy usar exclusivamente el tenant `ERClave Demo QA` con ID `ten_739ee59d765d5e14818674800d`. No ejecutar seeds, cargas de prueba ni mutaciones de ensayo sobre ningún otro tenant sin autorización explícita del usuario. Antes de una operación que escriba datos, confirmar el `tenant_id`; si no coincide, detenerse.

## Flujo de implementación

1. Definir criterios de aceptación y blast radius.
2. Declarar `Agentes consultados`: negocio/tecnico del modulo y transversales aplicables. Todo release QA incluye Arquitectura, Seguridad y QA/Release.
3. Implementar el corte vertical mínimo completo.
4. Agregar o actualizar pruebas negativas, de permisos, idempotencia y aislamiento según aplique.
5. Actualizar documentación contractual y operativa afectada.
6. Agregar una entrada correlativa a `TRAZABILIDAD.md`. Usar `npm run traceability:draft -- --title "..."` para preparar el borrador.
7. Actualizar `docs/contexto/ESTADO_ACTUAL.md` y `docs/contexto/PENDIENTES.md` cuando cambie el estado real.
8. Ejecutar `npm run verify`.
9. Entregar una seccion `APIs afectadas` que enumere cada metodo y ruta involucrados. Separar: contratos modificados, endpoints consumidos sin cambio y APIs no tocadas. Para cada contrato modificado indicar servicio, permiso y cambio de request/response; si no hubo APIs, escribir explicitamente `Ninguna`.

Para funcionalidades completas usar la skill `$erclave-feature`. Para modelos o migraciones usar además `$erclave-db-migration`.

## Criterio de terminado

Un cambio termina sólo cuando cumple los criterios documentados, conserva ownership y aislamiento multitenant, alinea contratos/código/pruebas/documentación, supera `npm run verify`, queda registrado en `TRAZABILIDAD.md` y la entrega incluye `APIs afectadas`.

## Comandos

```powershell
npm.cmd run validate
npm.cmd run validate:responsive
npm.cmd run verify
npm.cmd run traceability:draft -- --title "Descripción del cambio"
npm.cmd run session:context
```

Las pruebas backend usan el intérprete indicado por `PYTHON` cuando exista; en caso contrario usan `python`.
