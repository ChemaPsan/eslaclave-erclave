# Inicio de sesion ERClave

Este documento define el orden obligatorio para recuperar contexto antes de analizar o modificar el proyecto.

## Secuencia

1. Ejecutar `npm.cmd run session:context` desde la raiz.
2. Leer completamente `AGENTS.md` y las secciones aplicables de `AGENTES.md`.
3. Leer `docs/contexto/ESTADO_ACTUAL.md`, `DECISIONES.md`, `TENANTS.md` y `PENDIENTES.md`.
4. Leer el documento de `modulos/` correspondiente y las fuentes de arquitectura que este referencie.
5. Revisar `git status --short`. Todo cambio previo se considera propiedad del usuario hasta demostrar lo contrario.
6. Identificar microfrontend, servicio, schema, contrato, permisos y agentes especialistas afectados.
7. Confirmar ambiente y `tenant_id` antes de cualquier escritura.
8. Definir criterios de aceptacion y blast radius antes de implementar.

## Cierre obligatorio

Antes de declarar terminado un cambio:

1. actualizar OpenAPI, consumidores, pruebas y documentacion cuando aplique;
2. ejecutar `npm.cmd run verify`;
3. actualizar `ESTADO_ACTUAL.md` y `PENDIENTES.md` si el estado real cambio;
4. registrar el corte en `TRAZABILIDAD.md`;
5. indicar expresamente si hubo migraciones, seeds, despliegues o escrituras externas.

La conversacion es contexto temporal. Estos archivos son la memoria persistente del proyecto.
