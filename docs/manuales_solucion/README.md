# Manuales funcionales de la solución ERClave

CHG-331: los siete Word se regeneraron desde las fuentes vigentes, se cotejó su texto y se revisaron visualmente sus 50 páginas. Son candidatos Local; consultar [REGISTRO](REGISTRO.md) para las huellas y el alcance de revisión. CC-20 integrado y la promoción QA siguen pendientes.

CC-17 CHG-322: fuentes Markdown de Produccion, Ventas y Administracion actualizadas para presentacion efectiva y snapshot documental, solo Local. Esta nota conserva el estado anterior a CHG-331.

Biblioteca para usuarios operativos, supervisores y administradores. Cobertura actualizada: **CHG-317 · 2026-10-12**. Consultar [REGISTRO](REGISTRO.md) antes de distribuir.

## Vigencia y ambiente

Las fuentes Markdown describen el recorrido base QA e57237f y ampliaciones explícitas sólo Local. Los siete manuales Word tienen paridad y revisión visual CHG-331; la guía QA Word conserva su registro independiente. Todos son exportaciones candidatas y sus comprobaciones figuran en el registro. [Estado por ambiente](../contexto/ESTADO_ACTUAL.md) y [control por submódulo](../contexto/CONTROL_CONTABLE.md) distinguen lo implementado de lo pendiente. Un despliegue no equivale a aceptación funcional.

CHG-317 incorporó recepción física con origen y conversión explícitos, refacciones por División, transferencias dentro de una Sociedad y sobrantes con costo/contexto conservados. La falta de LibreOffice de ese corte quedó superada para los siete manuales en CHG-331. Datos reales CC-19 y aceptación transversal CC-20 continúan pendientes.

## Organización

- Fuentes Markdown canónicas por módulo y exportaciones Word candidatas enlazadas en [REGISTRO](REGISTRO.md).
- [Plantilla funcional](fuentes/PLANTILLA.md) para nuevos módulos con runtime e interfaz.
- [Fichas de módulos](../../modulos/README.md) para reglas y diseño objetivo; capacidades planned no son instrucciones operativas.

No se mantienen copias por CHG como versiones distribuibles. La historia técnica vive en [TRAZABILIDAD](../../TRAZABILIDAD.md).

## Mantenimiento y control

El Custodio de manuales coordina a negocio/técnico de cada dueño según [AGENTES](../../AGENTES.md), [skill de manuales](../../.agents/skills/erclave-solution-manuals/SKILL.md) y [gobierno documental](../arquitectura/gobierno_documentacion_viva.md).

Al modificar pantallas, campos, estados, permisos, mensajes o integraciones: contrastar fuente con UI, contrato y pruebas; sustituir instrucciones superadas; regenerar Word; revisar todas sus páginas y actualizar registro. Separar validación estructural, visual y aceptación funcional.

Generación: python tools/generate-solution-manuals.py para siete manuales y python tools/generate-qa-document.py para guía. Ambos usan [generador común](../../tools/build-functional-document.py). Aplicar el flujo vigente de documentos antes de modificar DOCX; los bloqueos de herramientas de sesiones anteriores no prueban disponibilidad actual.

## Entrega al tester

[Guía de pruebas](../qa/guia_pruebas_qa_mvp.md), [matriz de ejecución](../qa/MATRIZ_EJECUCION_QA.md) y [entrega al tester](../qa/ENTREGA_TESTER.md) describen alcance QA. Distribuir sólo documentos con ambiente y estado de revisión identificados; un Word previo no sustituye instrucciones Local posteriores.
