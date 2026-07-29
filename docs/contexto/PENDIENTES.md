# Pendientes priorizados de ERClave

Ultima actualizacion: 2026-07-28.

## Prioridad siguiente

1. Validar funcionalmente en navegador la vista Inventario con datos controlados del tenant ERClave Demo QA cuando el usuario autorice la carga necesaria.
2. Completar el catalogo de Articulos para escala server-side; actualmente el corte escalable se concentro en balances de Inventario.
3. Decidir funcionalmente si Categoria se convierte en catalogo jerarquico antes de modelar IDs, padres o migraciones.
4. Validar Almacenes al 100% antes de conectar reservas y consumos automaticos con Produccion.
5. Implementar en production-service la persistencia multitenant de areas y puestos conforme al OpenAPI; el corte actual funciona localmente y no autoriza migraciones en QA.

## Fuera del alcance actual

- Reservas reales y calculo de disponible distinto de existencia fisica.
- Lotes, series, cuarentena, inventario bloqueado y en transito.
- Migracion o seed de Inventory sobre QA.
- Despliegue de frontend o servicios.

## Regla de mantenimiento

Mover un pendiente a `ESTADO_ACTUAL.md` solo cuando este implementado, probado y registrado en `TRAZABILIDAD.md`. Eliminar pendientes obsoletos explicando la decision en trazabilidad.
