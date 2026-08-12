---
name: erclave-db-migration
description: Diseñar, implementar y revisar cambios persistentes seguros de ERClave con SQLAlchemy, PostgreSQL y Alembic. Usar cuando una tarea agregue o cambie tablas, columnas, índices, constraints, modelos, seeds, backfills o relaciones, o cuando se deba diagnosticar drift, aislamiento multitenant, compatibilidad o rollback de una migración.
---

# Cambiar la base de datos ERClave

## Reunir evidencia

0. Usar `$erclave-environment-boundaries`; mostrar host, puerto, base, ambiente y tenant sin secretos.

1. Leer `AGENTS.md` y las secciones de datos en `AGENTES.md`.
2. Leer `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/modelo_datos_mvp.md`, el contrato afectado y migraciones vecinas.
3. Identificar fuente de verdad, schema, servicio dueño, datos existentes, volumen esperado y consumidores.

No inventar entidades o relaciones. Si la documentación es ambigua y la elección cambia datos o compatibilidad, pedir decisión.

## Diseñar

Definir tablas, columnas, tipos, nulabilidad, `tenant_id`, claves, índices compuestos, FKs internas, referencias externas, estados, auditoría, idempotencia, backfill, rollback e impacto contractual.

Toda tabla operativa requiere `tenant_id` salvo excepción documentada. No crear FK entre schemas de servicios. Preferir cambios pequeños, compatibles y reversibles.

## Implementar

1. Modificar el modelo y crear una revisión Alembic con `down_revision` correcto.
2. Escribir `upgrade()` y `downgrade()` reales. Si un rollback seguro no es posible, documentar la recuperación.
3. Separar cambios destructivos mediante expand/migrate/contract.
4. Hacer seeds y backfills idempotentes.
5. Actualizar schemas, repositorios, contratos y documentación dependientes.
6. Agregar pruebas de aislamiento, duplicados y datos existentes.

No aplicar migraciones a QA o Producción sin autorización explícita.

## Validar

- Comprobar cadena Alembic lineal y nombres únicos.
- Comparar modelo y migración.
- Probar upgrade y, cuando sea seguro, downgrade y nuevo upgrade.
- Revisar índices por tenant, estado, fecha y código.
- Comprobar ausencia de fuga entre tenants y FKs cruzadas.
- Comprobar reejecución segura de seeds y backfills.
- Definir consultas de verificación y procedimiento de rollback.

Ejecutar `npm run verify` y registrar riesgos y verificaciones reales en `TRAZABILIDAD.md`.
