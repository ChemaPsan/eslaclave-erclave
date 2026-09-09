# Manuales funcionales de la solución ERClave

Esta biblioteca explica ERClave desde la perspectiva de usuarios operativos, supervisores y administradores. No funciona como bitácora de desarrollo ni como evidencia de release.

## Organización vigente

- `fuentes/`: fuente Markdown canónica y versionable, una por módulo implementado.
- `word/`: un DOCX vigente por módulo, generado desde la fuente canónica.
- `REGISTRO.md`: cobertura, ambiente y limitaciones conocidas.
- `PLANTILLA.md`: estructura para un futuro manual cuando un módulo pase de planeado a implementado.

No se conservan copias `*_CHG-*.docx`: acumulaban cortes parciales, podían circular como instrucciones vigentes y duplicaban contenido que ya pertenece a la fuente canónica. El historial técnico permanece fuera de esta biblioteca.

## Regla de ambiente

Cada manual distingue **Local**, **QA** y capacidades no disponibles. Una funcionalidad preparada en archivos Local no debe anunciarse como existente en QA. Al 6 de septiembre de 2026, QA tiene siete servicios certificados; las órdenes de servicio de Ventas, las compras de servicios sin Inventario y los reportes estándar ejecutables permanecen sólo en Local.

## Mantenimiento

Al cambiar pantallas, campos, estados, permisos, mensajes, dependencias o integraciones:

1. actualizar primero la fuente Markdown;
2. eliminar instrucciones obsoletas en vez de agregar parches históricos;
3. regenerar el DOCX con el mismo nombre canónico;
4. revisar portada, encabezados, tablas, listas, saltos de página y apertura en Word;
5. actualizar `REGISTRO.md`.

Los módulos planeados no reciben un manual operativo hasta contar con interfaz y runtime verificables. Su definición funcional continúa en `modulos/`.
