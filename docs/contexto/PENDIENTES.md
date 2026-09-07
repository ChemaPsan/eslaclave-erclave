# Pendientes priorizados de ERClave

Ultima actualizacion: 2026-09-06.

## Validacion del release QA

0. Completar la matriz UAT del SHA QA `a119ddf5e8d42376b8557b234e15e3681b19c2a7`: permisos, aislamiento entre tenants, dependencias modulares, Compras, Mantenimiento, referencias, reservas/consumos, recepciones, capacidad, valuacion, concurrencia, proteccion de datos e idempotencia.
1. Repetir en QA el onboarding con un tenant ficticio y confirmar recepcion del correo Firebase, incluido folder de spam. Despues validar eliminacion, `firebase_identity_cleanup` y que el tenant deje de aparecer.
2. Diseñar una reconciliacion durable/outbox para invitaciones o limpiezas Firebase pendientes; la respuesta explicita evita el falso fracaso, pero no sustituye un reintento persistente si el cliente pierde la respuesta.
3. Comprobar que el administrador allowlisted accede a Backoffice mientras un owner ordinario conserva `403`, sin persistir tokens ni contraseñas.
4. Comprobar con usuarios de tenants distintos que los siete modulos seleccionan el tenant desde membresias, recargan datos de Cloud SQL y no muestran KPIs/transacciones simuladas; los modulos planeados permanecen inactivos.

## Prioridad siguiente

0. Siguiente evolucion de Mantenimiento tras CHG-257: reintento automatico programado, devolucion de sobrantes, participantes secundarios y adjuntos; despues abordar preventivos y activos generales. Los reportes operativos basicos de ordenes, indisponibilidad, refacciones y tiempos ya quedaron cerrados.
0.1. Siguiente evolucion de Compras: division/adjudicacion de partidas de una requisicion entre varios proveedores, reintento automatico programado de recepciones `needs_reconciliation` y paginacion server-side antes de promover a QA. CHG-259 ya prueba la recuperacion parcial y corrige partidas sin respuesta; CHG-255 permite servicios sin Inventory. No existe aun adjudicacion parcial, factura ni cuenta por pagar.
1. Siguiente corte de Ventas despues de CHG-255: devoluciones, facturacion/cobranza y callback de Production que convierta solicitudes en partidas entregables y reporte costo real. La ejecucion/aceptacion de servicios ya tiene orden propia; la recepcion de producto terminado permanece cubierta por CHG-222.
2. Evolucionar la paginacion visual transversal de CHG-259 a paginacion contractual con cursor en Clientes, Cotizaciones, Pedidos, Ordenes de servicio y Entregas antes de volumen productivo; el limite preventivo de API permanece en 200.
3. Repetir en Local aislado las dos entradas funcionales que antes quedaron solo en `localStorage` y confirmar en navegador que Movimientos, Inventario y Kardex reflejan el mismo saldo; no copiar esos datos a QA.
4. Completar el catalogo de Articulos para escala server-side; actualmente el corte escalable se concentro en balances de Inventario.
5. Decidir funcionalmente si Categoria se convierte en catalogo jerarquico antes de modelar IDs, padres o migraciones.
6. Completar la matriz de fallas de Produccion con una interrupcion entre el consumo de Inventory y la confirmacion `in_progress`, seguida de reintento/reconciliacion con clave estable. CHG-259 ya certifica contencion de reservas/consumos en Inventory y claims concurrentes en Sales, Purchasing y Maintenance; la interrupcion Production-Inventory y la evidencia de carga sostenida siguen pendientes antes de QA.
7. Capturar y validar areas/puestos QA solamente con datos ficticios y autorizacion explicita; `hr-service` y el entitlement ya estan desplegados, pero sus catalogos permanecen vacios.
8. Paginar el catalogo de articulos elegibles para recetas y exponer disponibilidad agregada server-side para volumen mayor a 200 combinaciones articulo/almacen.
9. Ejecutar la prueba funcional del editor de permisos en QA tras renovar la sesion y confirmar persistencia, concurrencia y rechazo de grants prohibidos.
10. Diseñar la recepcion de merma desde Produccion. La recepcion de producto terminado permanece confirmada por Almacenes mediante `inventory.finished_goods_receipt.receive`; CHG-236 separo esa autoridad de los movimientos generales.
10.1. Evaluar un borrador de orden de Produccion separado de la liberacion. En el runtime vigente, crear la orden valida, reserva y libera en una sola operacion protegida por `production.order.release`.
11. Evolucionar el calendario productivo base lunes-viernes a calendarios tenant configurables con turnos, festivos, ausencias y excepciones por mantenimiento. CHG-241 ya distribuye y compromete capacidad multi-dia; Mantenimiento correctivo aun no modifica automaticamente esa capacidad planeada.
12. Implementar PDF de Pedido y remision/Entrega usando `document.template`, con snapshot o artefacto inmutable; mover el logo a object storage antes de promover la plantilla a QA.
13. Cuando Compras sea operativo, definir la politica de valuacion que actualizara el costo unitario base del articulo desde recepciones u ordenes de compra; por ahora permanece como captura manual de Inventory.
14. Integrar consumidores externos con la reserva central de folios o exigir una credencial interna de confianza; la UI Local ya usa el catalogo, pero los contratos propietarios conservan compatibilidad con clientes API que proporcionan un codigo valido.
15. Estandarizar en backend todas las excepciones de validación y errores inesperados con la envoltura `ErclaveError`; propagar `X-Correlation-Id` entre servicios, exponerlo en CORS y declarar respuestas de error comunes en OpenAPI. CHG-251 ya evita exponer mensajes técnicos en la UI y conserva la referencia disponible, pero no cambia los contratos HTTP de los servicios.
16. Diseñar el modulo Reportes para analitica transversal: XLSX con formato, PDF, constructor, cruces entre propietarios, graficas, vistas guardadas, programacion y distribucion. CHG-257 conserva reportes operativos simples en el servicio propietario y oculta su formato tecnico en la interfaz.

## Fuera del alcance actual

- Crear infraestructura de Produccion antes de autorizacion expresa; los objetivos futuros son RPO 15 minutos y RTO 2 horas.

- Lotes y canales de reserva distintos de ordenes de Produccion o pedidos de Ventas.
- Lotes, series, cuarentena, inventario bloqueado y en transito.
- Carga de datos funcionales, dummy o de volumen en Inventory/RH sobre QA sin una autorizacion especifica.
- Despliegue de frontend o servicios fuera del pipeline y sus aprobaciones protegidas.

## Regla de mantenimiento

Mover un pendiente a `ESTADO_ACTUAL.md` solo cuando este implementado, probado y registrado en `TRAZABILIDAD.md`. Eliminar pendientes obsoletos explicando la decision en trazabilidad.
