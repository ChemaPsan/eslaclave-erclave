# sales-service

Servicio real de Ventas. Es dueno de clientes, contactos, cotizaciones, pedidos, ordenes de servicio, entregas, partidas, snapshots comerciales, idempotencia y auditoria dentro del schema `sales`.

## Autor de comandos y recuperacion Local

Los recibos durables vinculan el actor autenticado, tenant, operacion, clave y payload. Otro actor recibe `409 idempotency_key_reused`; el actor original conserva su replay. Las asignaciones organizacionales y condiciones ya incluian actor en su huella. Los nuevos intents de surtido, cancelacion de pedido, confirmacion de entrega y conciliacion de fabricacion vinculan actor antes de efectos externos y registran auditoria de preparacion.

Los recibos anteriores pueden recuperarse solo si `sales.audit_events.occurred_at` identifica un actor unico de la misma operacion/transaccion que `sales.idempotency_records.created_at`. Un intent pendiente anterior sin autor demostrable conserva sus datos y responde el conflicto `409` de conciliacion existente: se requiere revisar autoria explicitamente antes de recuperarlo. No se atribuye al creador del documento ni se continua automaticamente con otro actor. Este control no cambia payloads publicos ni requiere migracion; inventariar estos pendientes es una precondicion de la promocion QA.

Valida responsables mediante RH, productos/servicios mediante Produccion, y unidades/monedas/condiciones de pago mediante Administracion. Orquesta reservas/consumos por API de Inventory y solicitudes idempotentes por API de Production, sin escribir schemas ajenos. Devoluciones y facturacion permanecen planeadas.

Local: `http://127.0.0.1:8008`. QA: desplegado dentro del release vigente de siete servicios. Produccion: no aprovisionado.

`POST /v1/sales/quotes` y `POST /v1/sales/orders` reciben un `code` de negocio obligatorio. El consumidor puede capturarlo o recibirlo de la autoridad central de consecutivos de Admin ya existente; Sales no genera un consecutivo paralelo. Ambos comandos recortan y normalizan el codigo a mayusculas, aceptan exclusivamente `A-Z`, digitos, punto, guion y guion bajo (maximo 60), lo hacen unico por tenant y lo incluyen en la huella idempotente. Reutilizar una `Idempotency-Key` con el mismo payload normalizado reproduce la respuesta; cambiar el codigo con la misma clave se rechaza como conflicto idempotente.

CHG-204 aplico el plan de correccion de CHG-203 en Local con la revision `20260818_0020`: alta de Entregas en UI, mapeo producto-articulo, sanitizacion, lectura parcial resiliente, costo real por fuente y reclamos durables con locks/reintento para surtido, cancelacion y confirmacion. Paginacion, devoluciones/facturacion, callback de Production, PDF de Pedido/Entrega y object storage permanecen fuera de este corte. Ver `docs/auditorias/ventas_segundo_corte_2026-08-18.md`.

CHG-255 agrega en codigo Local el ciclo de ordenes de servicio. Confirmar un Pedido crea exactamente una orden por partida `service`; planear, asignar, iniciar, pausar, reanudar, enviar a aceptacion, aceptar y cancelar usan permisos derivados por accion, idempotencia, bloqueo y auditoria. Los tiempos, costos y evidencias pertenecen a Sales; RH solo valida trabajadores activos mediante su proyeccion minima. Las partidas de servicio no se incluyen en Entregas ni generan movimientos de Inventory.

## Preparación contable y alcance vigente

Condiciones explícitas sin herencia, cotización→pedido, servicios y stock→entrega dimensionados implementados Local. Moneda original/tasa/convertido de Servicios CC-08 implementada CHG-314; fabricación CC-12, conciliación de recepción real y entrega/costo implementadas CHG-315. Véase [CONTROL_CONTABLE](../../../docs/contexto/CONTROL_CONTABLE.md) y [estado por ambiente](../../../docs/contexto/ESTADO_ACTUAL.md). La preparación no activa Accounting.
