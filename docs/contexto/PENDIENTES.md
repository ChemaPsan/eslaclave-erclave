# Pendientes priorizados de ERClave

Ultima actualizacion: 2026-08-21.

## Preparacion del release QA

0. Construir desde el SHA inmutable de `main` `adb134f7ac8b33b4a842d07db10c9b5f88525f2f` el candidato QA de cinco servicios mediante el gate protegido `qa-build`. La identidad `erclave-sales-qa` y las variables `QA_SALES_RUNTIME_SERVICE_ACCOUNT`/`QA_SALES_API_URL` ya quedaron aprovisionadas y verificadas en CHG-225. Despues de construir, conservar run ID y digests, y probar migraciones, permisos, dependencias modulares, referencias, reservas/consumos, recepcion de producto terminado, capacidad, valuacion, concurrencia, proteccion de datos e idempotencia antes de promoverlo.

1. Promover el candidato posterior a CHG-191 que corrige el aislamiento del arranque Local y la resolucion dinamica del tenant QA; antes, completar PR, CI, candidato inmutable y gates separados.
2. Renovar la sesion Firebase QA y comprobar que el administrador allowlisted accede a Backoffice mientras un owner ordinario conserva `403`, sin persistir tokens ni contraseñas.
3. Comprobar con usuarios de tenants distintos que Admin, Produccion, Inventory, RH y Ventas seleccionan el tenant desde membresias, recargan datos de Cloud SQL y no muestran KPIs/transacciones simuladas; Integraciones permanece inactivo.
4. Ejecutar pruebas funcionales y negativas de permisos/aislamiento antes de considerar el candidato listo para salir de QA.

## Prioridad siguiente

0. Definir el siguiente corte de Ventas tras CHG-204: devoluciones, facturacion/cobranza y callback de Production que convierta solicitudes en partidas entregables y reporte costo real. La recepcion manual, parcial e idempotente de producto terminado quedo cubierta por CHG-222.
1. Agregar paginacion con cursor a Clientes, Cotizaciones, Pedidos y Entregas antes de volumen productivo; el limite preventivo actual permanece en 200.
2. Repetir en Local aislado las dos entradas funcionales que antes quedaron solo en `localStorage` y confirmar en navegador que Movimientos, Inventario y Kardex reflejan el mismo saldo; no copiar esos datos a QA.
3. Completar el catalogo de Articulos para escala server-side; actualmente el corte escalable se concentro en balances de Inventario.
4. Decidir funcionalmente si Categoria se convierte en catalogo jerarquico antes de modelar IDs, padres o migraciones.
5. Ejecutar en PostgreSQL Local pruebas de contencion paralela sobre dos reservas/salidas del mismo articulo y dos ordenes que compiten por la misma capacidad; incluir interrupcion entre el consumo de Inventory y la confirmacion `in_progress` de Production, seguida de reintento/reconciliacion con clave estable. El corte de codigo ya usa bloqueos e idempotencia, pero requiere evidencia de carga antes de QA.
6. Capturar y validar areas/puestos QA solamente con datos ficticios y autorizacion explicita; `hr-service` y el entitlement ya estan desplegados, pero sus catalogos permanecen vacios.
7. Paginar el catalogo de articulos elegibles para recetas y exponer disponibilidad agregada server-side para volumen mayor a 200 combinaciones articulo/almacen.
8. Ejecutar la prueba funcional del editor de permisos en QA tras renovar la sesion y confirmar persistencia, concurrencia y rechazo de grants prohibidos.
9. Diseñar la recepcion de merma desde Produccion y decidir si la recepcion de producto terminado permanece confirmada por Almacenes o admite automatizacion controlada; CHG-222 ya permite recibir parcial o totalmente ordenes terminadas desde Movimientos.
10. Definir calendarios, turnos, ausencias, mantenimiento y capacidad multi-dia. El corte actual compromete minutos por fecha usando trabajadores activos y capacidad diaria de maquinas.
11. Implementar PDF de Pedido y remision/Entrega usando `document.template`, con snapshot o artefacto inmutable; mover el logo a object storage antes de promover la plantilla a QA.
12. Cuando Compras sea operativo, definir la politica de valuacion que actualizara el costo unitario base del articulo desde recepciones u ordenes de compra; por ahora permanece como captura manual de Inventory.
13. Integrar consumidores externos con la reserva central de folios o exigir una credencial interna de confianza; la UI Local ya usa el catalogo, pero los contratos propietarios conservan compatibilidad con clientes API que proporcionan un codigo valido.

## Fuera del alcance actual

- Crear infraestructura de Produccion antes de autorizacion expresa; los objetivos futuros son RPO 15 minutos y RTO 2 horas.

- Lotes y canales de reserva distintos de ordenes de Produccion o pedidos de Ventas.
- Lotes, series, cuarentena, inventario bloqueado y en transito.
- Carga de datos funcionales, dummy o de volumen en Inventory/RH sobre QA sin una autorizacion especifica.
- Despliegue de frontend o servicios fuera del pipeline y sus aprobaciones protegidas.

## Regla de mantenimiento

Mover un pendiente a `ESTADO_ACTUAL.md` solo cuando este implementado, probado y registrado en `TRAZABILIDAD.md`. Eliminar pendientes obsoletos explicando la decision en trazabilidad.
