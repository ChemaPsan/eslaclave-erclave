# ERClave: instrucciones operativas para Codex

Estas reglas aplican a todo el repositorio. `AGENTES.md` conserva el conocimiento funcional y los roles especializados; este archivo define cómo ejecutar cambios.

## Antes de modificar

1. Leer `AGENTES.md` y el documento del módulo en `modulos/`.
2. Para arquitectura, datos, seguridad o ambientes, consultar los documentos pertinentes en `docs/arquitectura/`.
3. Identificar el módulo, microfrontend, microservicio, dueño del dato, contratos y dependencias afectadas.
4. Revisar `git status --short` y preservar cambios locales ajenos.
5. No inventar reglas de negocio, entidades, permisos ni estados. Registrar supuestos pendientes si la fuente de verdad no los define.

## Reglas obligatorias

- Mantener aislamiento por `tenant_id` en tablas, repositorios, APIs, índices y pruebas.
- Firebase autentica; ERClave resuelve membresías, permisos, entitlements y alcance mediante `admin-service`.
- No escribir datos pertenecientes a otro servicio ni crear FKs entre schemas de servicios.
- Mantener reglas críticas, autorización e idempotencia en backend, no sólo en frontend.
- El consumo HTTP del frontend vive en `frontend/api/`; las pantallas no llaman `fetch` directamente.
- Todo texto visible nuevo o modificado debe existir en español e inglés con las mismas variables.
- Cambios de API deben actualizar OpenAPI, schemas, consumidores y pruebas en el mismo corte.
- Cambios persistentes deben incluir modelo, migración Alembic, índices/constraints, estrategia de datos existentes y prueba.
- No desplegar, migrar QA/Producción, publicar, enviar mensajes ni crear PRs salvo petición explícita.

## Flujo de implementación

1. Definir criterios de aceptación y blast radius.
2. Implementar el corte vertical mínimo completo.
3. Agregar o actualizar pruebas negativas, de permisos, idempotencia y aislamiento según aplique.
4. Actualizar documentación contractual y operativa afectada.
5. Agregar una entrada correlativa a `TRAZABILIDAD.md`. Usar `npm run traceability:draft -- --title "..."` para preparar el borrador.
6. Ejecutar `npm run verify`.

Para funcionalidades completas usar la skill `$erclave-feature`. Para modelos o migraciones usar además `$erclave-db-migration`.

## Criterio de terminado

Un cambio termina sólo cuando cumple los criterios documentados, conserva ownership y aislamiento multitenant, alinea contratos/código/pruebas/documentación, supera `npm run verify` y queda registrado en `TRAZABILIDAD.md`.

## Comandos

```powershell
npm.cmd run validate
npm.cmd run verify
npm.cmd run traceability:draft -- --title "Descripción del cambio"
```

Las pruebas backend usan el intérprete indicado por `PYTHON` cuando exista; en caso contrario usan `python`.
