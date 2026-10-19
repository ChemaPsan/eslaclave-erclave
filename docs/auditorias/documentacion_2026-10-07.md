# Auditoría documental CHG-311 · 2026-10-07

> Evidencia histórica de este corte. Autoridad vigente: [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md), [PENDIENTES](../contexto/PENDIENTES.md) y [gobierno documental](../arquitectura/gobierno_documentacion_viva.md).

## Alcance y evidencia

Auditoría local del inventario documental propio (Markdown, draw.io, Word y canvas), excluyendo dependencias, entornos virtuales, builds y artefactos temporales. El [índice](../INDICE_DOCUMENTAL.md) clasifica cada archivo; no certifica contenido externo ni infraestructura remota. Se contrastaron fuentes vivas con contratos, scripts, migraciones y resultados documentados. Los diagramas conservan clasificación de arquitectura/diseño; no se realizó render visual integral de diagramas ni Word.

Agentes ejecutados: docs_contexto (fuentes vivas/historia), docs_arquitectura (planes, contratos, catálogos y readmes técnicos), docs_modulos_manuales (fichas, fuentes manuales y QA). Coordinador: custodia, navegación, autoridades, automatización y validación final.

## Correcciones verificables

| Problema | Corrección y relación |
|---|---|
| Contexto acumulaba instrucciones vencidas y decisiones resueltas | Fuentes actuales condensadas; originales íntegros conservados en [histórico](../contexto/historico/README.md) |
| CONT-05/07 y pedidos/stock aún aparecían pendientes | Planes, fichas y manuales conciliados con [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md) |
| Centro obligatorio global y moneda no resuelta | Regla condicional296 y política monetaria309 separadas de implementación parcial |
| QA mezclado con capacidades Local | Estado documentado e57237f/0036 separado del head Local0050; sin nueva certificación remota |
| Admin JSON tratado como autoridad y servicio como scaffold | README remite autoridad normalizada CONT-02 y alcance CONT-03 |
| Compras/Mantenimiento sólo Local y semántica antigua de movimientos | Readmes técnicos reconciliados con releases y contratos actuales |
| Guías/manuales sin conexiones y Word presentado como vigente | Enlaces módulo→dueño→contrato→evidencia; Word señalado como exportación pendiente |
| Mandatos antiguos en cabecera de AGENTES | Historia separada; custodia vigente enlazada al portal y al control |
| Archivos nuevos sin índice o enlaces rotos | Registro exhaustivo, índice generado y verificación automática integrada |

## Brechas que no se deben ocultar

- Word: las ocho exportaciones fueron regeneradas y verificadas 8/8 por paridad textual, ZIP y XML. SHA256 de fuentes/Word registrados y comprobados automáticamente. El renderer falló con FileNotFoundError: LibreOffice soffice.exe was not found on PATH; el runtime declara libreOfficeVersion null. Revisión visual pendiente, sin PNG ni certificación de composición. Consultar las fuentes Markdown y REGISTRO.
- UAT: no se ejecutó ni se convirtió evidencia técnica en aceptación funcional. La matriz conserva resultados reales pendientes.
- La política monetaria está decidida, pero recursos/capacidad/fabricación y productores de Inventario siguen parciales; no se implementaron funcionalidades por esta auditoría.
- Relaciones documentales no prueban integridad semántica universal. Ante nuevo cambio los custodios revisan el cuerpo y su evidencia; el script sólo verifica propiedades objetivas.
- Los documentos de visión y requisitos son referencia de diseño, no promesa de funciones desplegadas. Los registros de release, auditoría y reanudación son historia.

## Validación

169 archivos clasificados y enlazados; 13 casos del nuevo control aprobados. Verificación general tools/verify.js aprobada: validadores, compilación y 532 pruebas aprobadas, 152 omitidas, 1 aviso de deprecación; las omisiones no cuentan como aprobaciones. Evidencia chg311-verify.log. Seis diagramas con XML válido; sin render integral. Resultados registrados en CHG-311 de [TRAZABILIDAD](../../TRAZABILIDAD.md). APIs afectadas: Ninguna. Sin migraciones ejecutadas, seeds, despliegues ni cambios a datos.
