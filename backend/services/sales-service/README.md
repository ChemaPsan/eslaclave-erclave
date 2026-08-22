# sales-service

Servicio Local real del segundo corte de Ventas. Es dueno de clientes, contactos, cotizaciones, pedidos, entregas, partidas, snapshots comerciales, idempotencia y auditoria dentro del schema `sales`.

Valida responsables mediante RH, productos/servicios mediante Produccion, y unidades/monedas/condiciones de pago mediante Administracion. Orquesta reservas/consumos por API de Inventory y solicitudes idempotentes por API de Production, sin escribir schemas ajenos. Devoluciones y facturacion permanecen planeadas.

Local: `http://127.0.0.1:8008`. QA/Produccion: no desplegado.

`POST /v1/sales/quotes` y `POST /v1/sales/orders` reciben un `code` de negocio obligatorio. El consumidor puede capturarlo o recibirlo de una futura autoridad central de consecutivos; Sales no genera un consecutivo paralelo. Ambos comandos recortan y normalizan el codigo a mayusculas, aceptan exclusivamente `A-Z`, digitos, punto, guion y guion bajo (maximo 60), lo hacen unico por tenant y lo incluyen en la huella idempotente. Reutilizar una `Idempotency-Key` con el mismo payload normalizado reproduce la respuesta; cambiar el codigo con la misma clave se rechaza como conflicto idempotente.

CHG-204 aplico el plan de correccion de CHG-203 en Local con la revision `20260818_0020`: alta de Entregas en UI, mapeo producto-articulo, sanitizacion, lectura parcial resiliente, costo real por fuente y reclamos durables con locks/reintento para surtido, cancelacion y confirmacion. Paginacion, devoluciones/facturacion, callback de Production, PDF de Pedido/Entrega y object storage permanecen fuera de este corte. Ver `docs/auditorias/ventas_segundo_corte_2026-08-18.md`.
