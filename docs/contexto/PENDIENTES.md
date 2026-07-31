# Pendientes priorizados de ERClave

Ultima actualizacion: 2026-07-31.

## Prioridad siguiente

1. Validar funcionalmente en navegador la vista Inventario con datos controlados del tenant ERClave Demo QA cuando el usuario autorice la carga necesaria.
2. Completar el catalogo de Articulos para escala server-side; actualmente el corte escalable se concentro en balances de Inventario.
3. Decidir funcionalmente si Categoria se convierte en catalogo jerarquico antes de modelar IDs, padres o migraciones.
4. Validar Almacenes al 100% antes de conectar reservas y consumos automaticos con Produccion.
5. Validar y promover el proceso de `hr-service` y su entitlement solo con autorizacion explicita; el esquema y los permisos ya existen en QA, vacios, pero el servicio no fue desplegado.
6. Paginar el catalogo de articulos elegibles para recetas y exponer disponibilidad agregada server-side para volumen mayor a 200 combinaciones articulo/almacen.
7. Ejecutar la prueba funcional del editor de permisos en el tenant ERClave Demo QA tras renovar la sesion; la migracion, seed y Admin API local conectada a QA ya fueron validados.

## Fuera del alcance actual

- Reservas reales y calculo de disponible distinto de existencia fisica.
- Lotes, series, cuarentena, inventario bloqueado y en transito.
- Carga de datos funcionales, dummy o de volumen en Inventory/RH sobre QA sin una autorizacion especifica.
- Despliegue de frontend o servicios.

## Regla de mantenimiento

Mover un pendiente a `ESTADO_ACTUAL.md` solo cuando este implementado, probado y registrado en `TRAZABILIDAD.md`. Eliminar pendientes obsoletos explicando la decision en trazabilidad.
