# Gobierno de documentacion viva

## Objetivo

La documentacion y los agentes son parte del producto. Un cambio no esta terminado si codigo, contratos, datos, interfaz, estado operativo, pendientes, diagramas o instrucciones de agentes describen realidades distintas.

Este documento define que fuentes deben actualizarse, quien las custodia y que controles automaticos bloquean el drift documental.

## Clases de documento

### Fuentes vivas

Describen el estado o las reglas vigentes y deben corregirse en el mismo corte que cambia la realidad:

- `AGENTS.md` y `AGENTES.md`;
- `docs/contexto/ESTADO_ACTUAL.md`, `DECISIONES.md`, `PENDIENTES.md`, `TENANTS.md` e `INICIO_SESION.md`;
- fichas de `modulos/` y su indice;
- documentos de `docs/arquitectura/` que definan ownership, datos, APIs, ambientes o diagramas actuales;
- contratos de `contracts/`;
- runbooks operativos que sigan siendo el procedimiento canonico;
- `TRAZABILIDAD.md`.

### Evidencia historica

Los reportes de una prueba, release, migracion o incidente conservan el estado observado en su fecha. No deben reescribirse para simular que describian una version posterior. Deben identificarse como evidencia historica y enlazar la fuente viva cuando exista riesgo de confusion.

Ejemplos: actas de release, evidencias bajo `docs/qa/`, respaldos y preparaciones fechadas bajo `docs/operaciones/`.

### Objetivos futuros

Las especificaciones futuras deben usar lenguaje explicito como `planned`, `objetivo futuro` o `no implementado`. Nunca deben presentarse como runtime disponible.

## Fuente de verdad por pregunta

| Pregunta | Fuente viva principal |
|---|---|
| Que existe en Local, QA o Produccion | `docs/contexto/ESTADO_ACTUAL.md` |
| Que sigue pendiente | `docs/contexto/PENDIENTES.md`; detalle contable por submódulo en `docs/contexto/CONTROL_CONTABLE.md`, enlazado y conciliado, sin duplicar inventario |
| Por que se tomo una decision | `docs/contexto/DECISIONES.md` |
| Que agente debe revisar el cambio | `AGENTES.md` |
| Como debe trabajar Codex | `AGENTS.md` |
| Quien es dueno del dato | `docs/arquitectura/ownership_datos_mvp.md` |
| Que persiste y en que revision | migraciones Alembic y `docs/arquitectura/modelo_datos_mvp.md` |
| Que contrato HTTP existe | OpenAPI del servicio y `docs/arquitectura/apis_mvp.md` |
| Que cambio introdujo el estado | `TRAZABILIDAD.md` |

## Matriz obligatoria de actualizacion

| Si cambia | Actualizar en el mismo corte |
|---|---|
| API o payload | OpenAPI, schemas, consumidor, pruebas, mapa API y trazabilidad |
| Modelo persistente | modelo, migracion, indices/constraints, documento de datos, estado, rollback y trazabilidad |
| Regla funcional | ficha del modulo, decisiones, pendientes, pruebas y agentes aplicables |
| Integracion entre servicios | ownership, API/evento, diagrama, compensacion/idempotencia y pruebas |
| Estado Local/QA/Produccion | estado actual, pendientes, diagrama, runbook o evidencia de release y trazabilidad |
| Modulo implementado o planeado | manifiesto, contrato, indice de modulos, estado, permisos y agentes |
| Texto o experiencia visible | ES/EN, ficha funcional, responsive/accesibilidad y trazabilidad |
| Campo o selector de formulario | Propósito de negocio, alta/edición/lectura, schema y contrato, catálogo dueño, validación backend, pruebas de recorrido y ficha funcional |
| Resultado UAT o smoke | Caso, ambiente, SHA, rol, pasos, resultado observado y evidencia; actualizar estado sólo si el recorrido completo lo demuestra |
| Regla para agentes o proceso | `AGENTS.md`, `AGENTES.md`, inicio de sesion, validador y trazabilidad |

## Separacion por ambiente

Toda afirmacion mutable debe indicar una de estas categorias:

- **Desplegado en QA:** runtime y revision promovidos mediante el pipeline gobernado.
- **Implementado solo en Local:** codigo y migraciones locales aun no promovidos.
- **Prototipo/mock:** experiencia no autoritativa, sin backend funcional.
- **Objetivo futuro/planned:** contrato o diseño sin runtime disponible.

Una capacidad Local no puede describirse simplemente como real si el contexto puede interpretarse como QA. Un documento historico de QA no se actualiza con capacidades Local posteriores.

## Responsabilidad de los agentes

- El agente de negocio valida reglas, alcance y pendientes del modulo.
- El agente tecnico valida runtime, contratos, persistencia y estado por ambiente.
- El agente técnico de Contabilidad custodia `docs/contexto/CONTROL_CONTABLE.md`: relaciona cada submódulo con dueño, capacidad, brecha, criterio de cierre y evidencia; negocio contable valida reglas y cada dueño valida implementación. Mantiene sus filas y los resúmenes de PENDIENTES/ESTADO alineados cuando cambia el estado, preservando historia en TRAZABILIDAD.
- Arquitectura SaaS valida fronteras y diagramas.
- Arquitectura de datos y Custodio DB validan modelo, migraciones y cabeza vigente.
- Arquitectura API valida OpenAPI y consumidores.
- Seguridad valida permisos, tenant, auditoria y datos sensibles.
- Diseño/i18n valida textos visibles ES/EN y estados de interfaz.
- QA/Release valida que evidencia historica y estado desplegado no se mezclen.
- Sinergia modular y agentes de modulos consumidores validan contratos cruzados.

`Agentes consultados` debe explicar la cobertura real. Una revision posterior se registra como revision complementaria; no se atribuye retroactivamente al cambio original.

## Automatizacion

`npm.cmd run validate:documentation` ejecuta `tools/validators/validate-documentation-freshness.js` y forma parte de `npm.cmd run validate` y `npm.cmd run verify`.

El validador bloquea, como minimo:

- una cabeza Alembic Local distinta entre migraciones, estado y diagrama actual;
- una revision QA distinta entre estado, frontera de ambientes y diagrama;
- un ultimo `CHG` sin campos obligatorios o ausente del estado actual;
- modulos documentados que no aparezcan en el indice;
- fuentes vivas obligatorias ausentes;
- enlaces Markdown locales rotos;
- ausencia de estas reglas en instrucciones de agentes e inicio de sesion.

Los validadores especializados siguen protegiendo OpenAPI/runtime, agentes, i18n, responsive, aislamiento, migraciones y trazabilidad. La automatizacion detecta invariantes objetivas; no sustituye la revision semantica de los agentes.

## Criterio de terminado

Antes de cerrar un cambio:

1. aplicar la matriz correspondiente;
2. eliminar afirmaciones obsoletas de fuentes vivas;
3. conservar sin reescritura engañosa la evidencia historica;
4. registrar `Agentes consultados` y `APIs afectadas`;
5. agregar el `CHG` correlativo;
6. ejecutar `npm.cmd run verify`;
7. informar ambiente, migraciones, seeds, datos y despliegues realmente afectados.

Si una fuente no puede actualizarse en el mismo corte, el cambio queda incompleto y debe registrarse como pendiente explícito; no se permite declarar terminado ignorando el drift.

## Registro, Obsidian y prevención de fuentes obsoletas · CHG-311

El [portal](../INICIO.md) y el [índice](../INDICE_DOCUMENTAL.md) son puntos de entrada. [El registro](../documentacion-registro.json) clasifica cada fuente propia Markdown/draw.io/Word/canvas como vigente, diseño, histórica o exportación pendiente, con custodio y autoridad. Los builds y dependencias no son fuentes documentales.

El custodio de manuales coordina esta cobertura con los agentes de módulo, Arquitectura y QA. Antes de usar un documento, comprobar su clase y ambiente; antes de cerrar un cambio, corregir el cuerpo vigente, relacionar decisión, dueño, contrato y evidencia, y archivar el corte sustituido cuando sea necesario. No añadir un prefacio que contradiga instrucciones antiguas todavía activas.

Al añadir, mover o borrar archivos actualizar el registro y ejecutar npm run docs:index. validate:documentation invoca tools/documentation-map.js y bloquea documentos sin clasificar, duplicados, autoridades inexistentes, historia sin aviso y enlaces locales/índice desactualizados. verify y CI heredan el control. Los enlaces Markdown relativos permiten navegación Obsidian sin configuración personal adicional. No se certifican enlaces remotos, anclas internas, semántica de negocio ni apariencia Word automáticamente.

Las exportaciones Word conservan hashes de fuente/artefacto en el registro. El validador detecta cambios posteriores a la paridad revisada. Ante drift, regenerar y comprobar contenido antes de renovar hashes; un hash nuevo no equivale a revisión visual ni convierte exportación pendiente en publicación final. En CHG-311 paridad textual 8/8 aprobada; renderer bloqueado por ausencia de LibreOffice en runtime.
