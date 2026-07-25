---
name: erclave-feature
description: Implementar funcionalidades verticales completas de ERClave desde criterios de negocio hasta datos, API, frontend, pruebas, documentación y trazabilidad. Usar cuando se solicite crear, conectar, ampliar o corregir una funcionalidad de cualquier módulo ERP, especialmente si el cambio cruza varias capas o afecta permisos, contratos, i18n o integración entre módulos.
---

# Entregar una funcionalidad ERClave

## Preparar

1. Leer `AGENTS.md`, `AGENTES.md` y `modulos/<modulo>.md`.
2. Leer sólo los documentos de arquitectura relacionados con el cambio.
3. Inspeccionar `git status --short`; preservar trabajo ajeno.
4. Expresar criterios de aceptación verificables.
5. Identificar tenant y actor; dueños de UI, servicio y datos; contratos, permisos, i18n, dependencias, fallos parciales, auditoría y rollback.

Detenerse y pedir decisión sólo si falta una regla de negocio que cambiaría materialmente el resultado.

## Implementar

Trabajar en el corte vertical mínimo completo:

1. Contrato y esquema de entrada/salida.
2. Persistencia y migración cuando aplique.
3. Repositorio y reglas de dominio.
4. Autorización, aislamiento e idempotencia backend.
5. Cliente en `frontend/api/` y UI propietaria.
6. Textos español/inglés.
7. Pruebas del camino feliz y fallos relevantes.
8. Documentación y trazabilidad.

No acoplar microfrontends ni escribir tablas de otro servicio. No confiar en el frontend para reglas críticas. No afirmar que algo fue probado contra QA si sólo se usaron dobles.

## Revisar

- Buscar rutas que omitan autorización o tenant.
- Comprobar que OpenAPI, Pydantic, cliente y pruebas coinciden.
- Probar estados inválidos, duplicados, reintentos y concurrencia cuando apliquen.
- Revisar textos visibles, módulos consumidores y el diff completo.

## Verificar y entregar

1. Ejecutar `npm run traceability:draft -- --title "Título del cambio"`.
2. Incorporar una entrada completa y correlativa en `TRAZABILIDAD.md`.
3. Ejecutar `npm run verify`.
4. Informar resultado, verificaciones ejecutadas y riesgos o pendientes reales.
