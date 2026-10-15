---
name: erclave-context-reconcile
description: "Recuperar y conciliar el estado de ERClave antes de planear trabajo o reanudar una sesión: cambios locales, último CHG, versión QA documentada, pendientes y herramientas disponibles. Usar cuando el contexto sea largo, haya cambios locales o existan afirmaciones de estado contradictorias."
---

# Contexto vigente y comprobable

Ejecutar `python tools/context_brief.py` desde la raíz de `eslaclave-erclave`. Es una lectura local sin secretos ni conexiones. Si Node/npm están disponibles, ejecutar también `npm.cmd run session:context` en Windows o `npm run session:context` en otros sistemas según `AGENTS.md`.

Leer la sección vigente de `docs/contexto/ESTADO_ACTUAL.md`, los pendientes, la última entrada de `TRAZABILIDAD.md` y las fichas del módulo afectado. Clasificar cada afirmación como documentada, observada en este turno, probada o pendiente; el script no verifica servicios remotos. No convertir notas históricas de `DECISIONES.md` o auditorías en estado desplegado.

Agrupar los cambios Git por corte y preservar trabajo ajeno. Si varios CHG conviven en el árbol, identificar qué archivos corresponden a la tarea antes de usar borradores de trazabilidad o preparar un candidato. Señalar herramientas ausentes antes de prometer una prueba, render o release.

Entregar un resumen corto de ambiente, versión documentada, evidencia comprobada, dependencias y siguiente acción. Actualizar fuentes vivas sólo cuando una prueba o release cambie el estado real; conservar evidencia histórica con su fecha. Para cualquier conexión o escritura de ambiente, aplicar `$erclave-environment-boundaries` y las autorizaciones de ese flujo.

## Control de vigencia y relaciones

Entrar por [portal](../../../docs/INICIO.md) y [registro](../../../docs/documentacion-registro.json). Usar la autoridad vigente y el ambiente declarado; no promover evidencia histórica, propuestas ni Word pendiente a instrucciones. Si una fuente viva contradice código/contrato/evidencia, corregir el cuerpo y conservar su corte histórico cuando corresponda. Consultar al custodio de manuales, Arquitectura y dueños de módulos; relacionar regla con decisión, contrato y validación.

Al crear/mover/borrar documentación actualizar el registro y ejecutar npm run docs:index; npm run validate:documentation detecta cobertura, clasificación e integridad de enlaces. verify y CI lo ejecutan automáticamente. No declarar semántica, UAT o render visual aprobados por este script.
