---
name: erclave-form-contract
description: Revisar o diseñar formularios ERClave frente a sus contratos de alta, edición, lectura y catálogos; justificar campos y detectar diferencias antes de cambiar la UI o API. Usar al añadir, quitar, exigir o auditar campos y selectores operativos.
---

# Coherencia de formularios y campos

Esta skill decide si la captura sirve al proceso y si lo que promete la pantalla coincide con el backend. Para presentación de errores, foco y conservación de captura, aplicar además `$erclave-form-feedback`. Para un cambio persistente, aplicar `$erclave-db-migration`.

## Delimitar

Identificar formulario, modos alta/edición, módulo dueño, ambiente y consumidores. Leer su ficha en `modulos/`, la pantalla y serialización real, el cliente en `frontend/api/`, los schemas Pydantic, OpenAPI, reglas de repositorio y pruebas. La auditoría `docs/auditorias/frontend_backend_2026-09-07.md` es evidencia histórica, no prueba de un fallo actual.

## Contrastar cada campo afectado

Registrar en una matriz breve: control y nombre de payload; decisión o tarea que permite; origen del valor; comportamiento en alta, edición y lectura; obligatoriedad y condición; tipo, límites, nulos y valor inicial; catálogo y servicio dueño; identidad estable y elegibilidad; permiso; persistencia y consumidores. Seguir el valor desde la captura hasta el registro guardado y de vuelta a la pantalla. Marcar por separado hechos comprobados, hipótesis y decisiones funcionales pendientes.

Para un campo propuesto, comprobar si puede calcularse, heredarse de un catálogo o capturarse más tarde. Elegir entre capturar, derivar, valor inicial explícito, opcional, solo lectura o diferir. No exigir un campo sólo porque existe en la base ni agregarlo sólo para llenar espacio. Si la razón de negocio no está documentada y cambia materialmente el flujo, presentar la decisión concreta al usuario antes de implementarla.

## Probar el recorrido

Verificar alta, edición de un registro existente y lectura tras recarga. Cubrir valores cero, nulos, límites, cambio de rama condicional, catálogo inactivo o valor histórico fuera de la lista corta, permisos y rechazo backend. La UI no debe ofrecer una opción que la API ignora ni perder un código estable al editar. El backend vuelve a validar tenant, código de catálogo y elegibilidad al guardar. Distinguir pruebas con interceptores de integración real.

Entregar la matriz de diferencias con severidad y evidencia, decisiones de campos, corte mínimo de código/contrato/datos/pruebas/documentación y `APIs afectadas`. Mantener el alcance de la solicitud y no escribir QA por una auditoría de formularios.
