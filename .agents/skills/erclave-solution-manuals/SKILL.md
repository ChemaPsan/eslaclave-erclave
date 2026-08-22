---
name: erclave-solution-manuals
description: Crear, revisar y mantener manuales funcionales de usuario de ERClave por modulo en Markdown y Word. Usar cuando se solicite explicar pantallas, conceptos, campos, estados, flujos, reglas, permisos, mensajes o integraciones desde la perspectiva de uso de la solucion; no usar como bitacora tecnica, reporte de desarrollo o evidencia de release.
---

# Manuales funcionales de ERClave

Produce documentacion de solucion comprensible para usuarios operativos, supervisores y administradores. El manual explica que significa cada elemento, cuando usarlo, que consecuencias tiene y como se relaciona con otros modulos.

## Fuente y salida

- Mantener una fuente Markdown por modulo en `docs/manuales_solucion/fuentes/`.
- Generar el Word correspondiente en `docs/manuales_solucion/word/` mediante `scripts/build_manual_docx.py`.
- No editar el DOCX como unica fuente: todo contenido debe poder reconstruirse desde Markdown.
- Consultar [references/estructura_manual.md](references/estructura_manual.md) al crear un manual o agregar una seccion sustancial.

## Metodo

1. Determinar modulo, audiencia, capacidad y ambiente realmente disponible.
2. Revisar la pantalla y textos visibles, la ficha de `modulos/`, reglas funcionales, permisos y contratos vigentes.
3. Consultar al agente de negocio del modulo para significado, excepciones y consecuencias; consultar al agente tecnico para confirmar comportamiento real. Si hay integraciones, consultar tambien a los modulos consumidores y propietarios del dato.
4. Resolver contradicciones contra fuentes autoritativas. No presentar una capacidad Local, mock o futura como disponible en QA/Produccion.
5. Documentar conceptos, prerequisitos, navegacion, campos, estados y transiciones, procedimiento, resultados, errores frecuentes, permisos e integraciones. Incluir ejemplos funcionales sin datos sensibles.
6. Marcar una duda no resuelta como `Pendiente de validacion funcional`; no inventar comportamiento.
7. Regenerar el DOCX, revisar que abra correctamente y actualizar el registro de cobertura.

## Mantenimiento

Cuando cambien textos, campos, estados, permisos, validaciones, flujos o dependencias visibles, revisar el manual del modulo en el mismo corte. Comparar el manual con interfaz, i18n, OpenAPI y pruebas; eliminar instrucciones obsoletas en vez de acumular parches históricos.

Mantener al inicio de cada fuente: modulo, audiencia, alcance por ambiente, fecha de revision y capacidades cubiertas. El historial tecnico pertenece a `TRAZABILIDAD.md`, no al manual.

## Calidad

- Escribir en español claro; definir siglas y términos la primera vez.
- Explicar cada estado con significado, entrada, acciones permitidas, salida y efectos en otros modulos.
- Separar “qué es” de “cómo se usa”.
- No exponer IDs internos salvo que sean visibles y útiles para soporte.
- No incluir secretos, tokens, contraseñas ni datos personales reales.
- Usar capturas sólo cuando aclaren una tarea y puedan mantenerse; acompañarlas con texto autosuficiente.
- Verificar enlaces, tabla de contenido, encabezados, tablas y saltos de pagina del Word.

## Cierre

Informar manuales creados o actualizados, fuentes consultadas, dudas pendientes, ambiente descrito y ruta de los DOCX generados.
