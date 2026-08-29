# Manual funcional de Compras y Abastecimiento

- Audiencia: solicitantes, aprobadores, compradores y almacenistas
- Alcance por ambiente: Local
- Ultima revision: 2026-08-24
- Capacidades cubiertas: proveedores, requisiciones, ordenes de compra y recepciones

## Preparacion

Compras requiere Inventory activo. Registre articulos, unidades y almacenes destino en Inventario, y proveedores activos con RFC, razon social, regimen fiscal, correo y codigo postal fiscal.

Cada responsabilidad se asigna por permiso. Aprobar una requisicion no concede crear o emitir ordenes; recibir mercancia tampoco concede cancelar la compra.

## De la requisicion a la orden

1. Abra **Compras > Requisiciones** y capture folio, fecha, prioridad y una o mas partidas.
2. Guarde y pulse **Enviar**.
3. Un usuario con permiso de aprobacion pulsa **Aprobar**.
4. Si ese usuario tambien puede crear ordenes, el sistema abre **Ordenes de compra** con la requisicion seleccionada. Tambien puede retomarla mediante **Crear orden de compra** en la tarjeta aprobada.
5. Capture folio, proveedor y precio unitario de cada partida; guarde la orden.

Crear convierte la requisicion completa y deja la orden en borrador. En este corte una requisicion no se divide entre varios proveedores.

## Emitir y recibir

1. Revise la orden en borrador y pulse **Emitir orden**. Desde ese momento proveedor, condiciones, cantidades y precios quedan congelados.
2. El sistema abre **Recepciones** con la orden seleccionada si cuenta con permiso para recibir.
3. Capture folio de recepcion, documento del proveedor, cantidades recibidas y almacen de cada partida inventariable.
4. Registre la recepcion. Puede repetir el proceso para entregas parciales sin superar el saldo pendiente.

Inventory crea las entradas fisicas. Si una integracion queda incierta, la recepcion aparece como **Requiere conciliacion** y debe reintentarse mediante la accion autorizada; no se corrige directamente en base de datos.

## Consultar todas las ordenes

Abra **Compras > Ordenes de compra**. El historial se presenta antes de la captura e incluye todas las OC, sin importar si estan en borrador, emitidas, parcialmente recibidas, recibidas, cerradas o canceladas.

La seccion **Nueva orden de compra** solo se habilita cuando existe una requisicion aprobada pendiente de convertir. Si no existe, use **Revisar requisiciones** para enviar y aprobar una necesidad. Reabastecimiento es una funcion futura separada y no sustituye el historial de OC.

## Permisos principales

- Requisiciones: `create`, `update`, `submit`, `approve`, `reject`, `cancel`.
- Ordenes: `create`, `update`, `issue`, `cancel`.
- Recepciones: `create`, `reconcile`.
- Proveedores: `create`, `update`.

Todos usan el prefijo `purchasing` y su recurso, por ejemplo `purchasing.order.issue`.

## Limitaciones

Factura XML/PDF, cuentas por pagar, pagos, devoluciones, cotizaciones comparativas, division por proveedor y reabastecimiento automatico permanecen fuera de este corte.
