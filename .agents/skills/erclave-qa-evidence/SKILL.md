---
name: erclave-qa-evidence
description: Convertir observaciones y resultados de pruebas funcionales ERClave en casos reproducibles y evidencia trazable, sin confundir smoke parcial, pruebas Local, QA y aceptación. Usar al registrar UAT, incidencias o avances de la matriz QA.
---

# Evidencia funcional sin inferencias

Antes de probar o leer recursos QA, aplicar `$erclave-environment-boundaries`. Esta skill no autoriza crear datos, cambiar estados, cargar archivos ni desplegar. Usar las identidades, tenant y datos autorizados para el caso concreto.

Por caso registrar: ID de la matriz o uno nuevo, fecha, ambiente y SHA observado, rol, precondiciones, pasos, resultado esperado, resultado visto y referencia de evidencia sin secretos. Omitir tokens, contraseñas, datos personales reales y enlaces temporales. Separar observación del usuario, reproducción controlada, prueba automatizada con dobles, prueba integrada y aceptación del tester.

Usar `docs/qa/MATRIZ_EJECUCION_QA.md` y la guía vigente; `python tools/context_brief.py` resume los estados documentados sin ejecutar pruebas nuevas. Cambiar un resultado a `Pasa` o `Falla` sólo cuando se ejecutó el recorrido completo y existe evidencia suficiente; `Bloqueado` exige la precondición faltante. Un smoke parcial queda en observaciones y conserva `Sin ejecutar` para el caso completo. No crear resultados ni porcentajes de cobertura a partir de un deploy o de la presencia de una prueba.

Si aparece una incidencia, enlazar el caso con un diagnóstico reproducible y la capa probable sin afirmar causa no investigada. Después de una corrección, registrar nueva prueba con SHA y ambiente; el resultado anterior permanece como historia. Actualizar estado, pendientes y trazabilidad sólo con hechos comprobados. Informar casos cerrados, bloqueados y próximos pasos con sus límites.
