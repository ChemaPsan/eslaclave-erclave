# Pendientes priorizados de ERClave

Ultima actualizacion: 2026-08-12.

## Preparacion del release QA

1. Solicitar autorizacion independiente para `qa-frontend`; el backend CHG-182 ya recibe 100% del trafico en Admin, Produccion, Inventory y RH.
2. Publicar exactamente el artefacto frontend sanitizado del mismo `release_sha`, sin reconstruir configuracion local, mocks ni datos.
3. Tras publicar el frontend, comprobar con sesion Firebase QA que Admin, Produccion, Inventory y RH recargan exclusivamente datos de Cloud SQL y que Ventas/Integraciones permanecen inactivos.
4. Ejecutar pruebas funcionales y negativas de permisos/aislamiento antes de considerar el candidato listo para salir de QA.

## Prioridad siguiente

1. Repetir en Local aislado las dos entradas funcionales que antes quedaron solo en `localStorage` y confirmar en navegador que Movimientos, Inventario y Kardex reflejan el mismo saldo; no copiar esos datos a QA.
2. Completar el catalogo de Articulos para escala server-side; actualmente el corte escalable se concentro en balances de Inventario.
3. Decidir funcionalmente si Categoria se convierte en catalogo jerarquico antes de modelar IDs, padres o migraciones.
4. Validar Almacenes al 100% antes de conectar reservas y consumos automaticos con Produccion.
5. Validar y promover el proceso de `hr-service` y su entitlement solo con autorizacion explicita; el esquema y los permisos ya existen en QA, vacios, pero el servicio no fue desplegado.
6. Paginar el catalogo de articulos elegibles para recetas y exponer disponibilidad agregada server-side para volumen mayor a 200 combinaciones articulo/almacen.
7. Ejecutar la prueba funcional del editor de permisos en el tenant ERClave Demo QA tras renovar la sesion; la migracion, seed y Admin API local conectada a QA ya fueron validados.
8. Disenar el contrato Inventory para reservar/consumir materiales y registrar producto terminado desde una orden; la validacion de Produccion actual solo conserva disponibilidad observada.
9. Definir valuacion de materiales en Inventario/Costos; mientras no exista, el costo planeado usa el costo unitario guardado en la version de receta y puede ser cero para articulos sin valuacion.

## Fuera del alcance actual

- Crear infraestructura de Produccion antes de autorizacion expresa; los objetivos futuros son RPO 15 minutos y RTO 2 horas.

- Reservas reales y calculo de disponible distinto de existencia fisica.
- Lotes, series, cuarentena, inventario bloqueado y en transito.
- Carga de datos funcionales, dummy o de volumen en Inventory/RH sobre QA sin una autorizacion especifica.
- Despliegue de frontend o servicios.

## Regla de mantenimiento

Mover un pendiente a `ESTADO_ACTUAL.md` solo cuando este implementado, probado y registrado en `TRAZABILIDAD.md`. Eliminar pendientes obsoletos explicando la decision en trazabilidad.
