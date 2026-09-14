# Manuales funcionales de la solución ERClave

Esta biblioteca explica ERClave desde la perspectiva de usuarios operativos, supervisores y administradores. No funciona como bitácora de desarrollo ni como evidencia de release.

**Edición 2026-09-14:** fuentes actualizadas y Word regenerados. Revisión visual pendiente; consultar REGISTRO.md antes de distribuir los binarios.

## Organización vigente

- `fuentes/`: fuente Markdown canónica y versionable, una por módulo implementado.
- `word/`: un DOCX vigente por módulo, generado desde la fuente canónica.
- `REGISTRO.md`: cobertura, ambiente y limitaciones conocidas.
- `PLANTILLA.md`: estructura para un futuro manual cuando un módulo pase de planeado a implementado.

No se conservan copias `*_CHG-*.docx`: acumulaban cortes parciales, podían circular como instrucciones vigentes y duplicaban contenido que ya pertenece a la fuente canónica. El historial técnico permanece fuera de esta biblioteca.

## Regla de ambiente

Cada manual distingue **Local**, **QA** y capacidades no disponibles. Una funcionalidad preparada en archivos Local no debe anunciarse como existente en QA. La revisión del 14 de septiembre de 2026 incorpora las mejoras Local de formularios, margen esperado y evidencia de servicios, señaladas como pendientes de promoción. La base publicada permanece en el release QA `b63cdad`, que incluye los siete servicios, las órdenes de servicio de Ventas, las compras de servicios sin Inventario y los reportes estándar. Desplegado no significa aceptación funcional concluida: el tester debe ejecutar la guía vigente y registrar sus resultados.

## Mantenimiento

Generación vigente: ejecutar `python tools/generate-solution-manuals.py` para los siete manuales y `python tools/generate-qa-document.py` para la guía. Ambos usan `tools/build-functional-document.py`, que convierte las tablas Markdown en tablas Word y conserva la numeración de cada procedimiento. Utilice un intérprete con python-docx y revise visualmente el resultado antes de distribuirlo.

Al cambiar pantallas, campos, estados, permisos, mensajes, dependencias o integraciones:

1. actualizar primero la fuente Markdown;
2. eliminar instrucciones obsoletas en vez de agregar parches históricos;
3. regenerar el DOCX con el mismo nombre canónico;
4. revisar portada, encabezados, tablas, listas, saltos de página y apertura en Word;
5. actualizar `REGISTRO.md`.

Los módulos planeados no reciben un manual operativo hasta contar con interfaz y runtime verificables. Su definición funcional continúa en `modulos/`.

## Entrega al tester

La guía vigente está en `docs/qa/guia_pruebas_qa_mvp.md` y su Word correspondiente. La carpeta de entrega contiene siete manuales Word, la guía de pruebas y un archivo LEEME con alcance, versión y orden sugerido. Las fuentes canónicas permanecen en esta biblioteca; no distribuya documentos históricos como instrucciones vigentes.
