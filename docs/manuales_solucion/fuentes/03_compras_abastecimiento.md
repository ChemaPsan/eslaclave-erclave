# Manual funcional de Compras y Abastecimiento

- Audiencia: solicitantes, aprobadores, compradores, receptores y supervisores
- Alcance por ambiente: compras inventariables en Local y QA; compras de servicios sin Inventario sólo en Local
- Última revisión: 2026-09-06
- Capacidades cubiertas: proveedores, requisiciones multipardida, órdenes, recepciones parciales y conciliación

## Propósito

Compras controla una necesidad desde la requisición hasta la recepción comercial. Conserva proveedor, autorizaciones, precios y saldos pendientes. Inventario sigue siendo autoridad únicamente cuando una partida representa un artículo físico.

## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Proveedores y perfil fiscal | Disponible | Disponible |
| Requisiciones, aprobación y rechazo | Disponible | Disponible |
| Órdenes y recepciones inventariables | Disponible | Disponible |
| Conciliación manual de líneas fallidas | Disponible | Disponible |
| Partidas y recepciones de servicio sin Inventario | Disponible | No disponible en el release vigente |
| Adjudicación de una requisición a varios proveedores | No disponible | No disponible |
| Factura, cuenta por pagar y pago | No disponible | No disponible |

## Mapa del módulo

- **Proveedores:** identidad y perfil fiscal.
- **Requisiciones:** necesidad interna y autorización.
- **Órdenes de compra:** proveedor, condiciones y precio por partida.
- **Recepciones:** recepción comercial parcial o total y conciliación.
- **Portada:** reportes estándar de sólo lectura.

## Conceptos principales

| Concepto | Significado |
|---|---|
| Partida inventariable | Exige artículo y almacén; al recibir genera entrada en Inventario. |
| Partida de servicio | Exige unidad activa, pero prohíbe artículo y almacén; su recepción es comercial. |
| Compra directa | Orden sin requisición; exige motivo explícito. |
| Recepción parcial | Registra sólo una fracción sin exceder el saldo abierto. |
| Requiere conciliación | Una autoridad externa no confirmó una línea; el documento conserva el pendiente exacto. |

## Acceso, permisos y preparación

Cada responsabilidad usa permisos independientes bajo `purchasing.*`: leer o crear proveedor, crear/editar/enviar/aprobar/rechazar/cancelar requisición, crear/editar/emitir/cancelar orden y crear/conciliar recepción. Aprobar no concede emitir; recibir no concede cancelar.

Antes de comprar:

- registre proveedor activo con razón social, RFC, régimen, correo de facturación y código postal fiscal;
- confirme que la unidad exista y esté activa en Administración;
- para una partida inventariable, confirme artículo y almacén activos;
- para un servicio, seleccione el tipo **Servicio** y no capture artículo ni almacén.

Compras puede estar activo sin Inventario en una empresa que sólo compra servicios. Inventario sigue siendo dependencia funcional cuando existen partidas físicas.

## Crear y autorizar una requisición

1. Abra **Compras > Requisiciones** y capture folio, fecha, prioridad y motivo.
2. Agregue una o más partidas. No repita el mismo artículo dentro del documento.
3. Defina tipo, unidad, cantidad y necesidad. Para artículos, seleccione la referencia de Inventario.
4. Guarde el borrador y corríjalo mientras permanezca editable.
5. Pulse **Enviar**. Un aprobador puede **Aprobar** o **Rechazar** con el permiso puntual.

Una requisición aprobada se convierte completa en una orden. La división por proveedor todavía no forma parte del corte.

## Crear y emitir una orden

1. Desde una requisición aprobada use **Crear orden de compra**, o inicie compra directa con motivo.
2. Seleccione proveedor, moneda, condiciones y precio unitario de cada partida.
3. Revise que tipo, unidad y cantidad coincidan exactamente con la requisición.
4. Guarde el borrador; puede editarlo antes de emitir.
5. Pulse **Emitir orden**. Proveedor, partidas, cantidades y precios quedan congelados.

## Recibir productos o servicios

1. Abra **Compras > Recepciones** y seleccione una orden emitida.
2. Capture folio de recepción, documento del proveedor y cantidad por partida.
3. Para una partida inventariable, confirme el almacén destino.
4. Para un servicio, confirme la prestación comercial; no se solicita almacén ni movimiento.
5. Registre. Puede repetir el flujo hasta completar el saldo sin sobre-recepción.

En una recepción multipardida, cada línea conserva su resultado. Si Inventario confirma algunas entradas y falla otra, Compras no revierte lo correcto ni finge éxito total: deja sólo las líneas inciertas en conciliación.

## Estados

| Documento | Estados principales |
|---|---|
| Requisición | Borrador, enviada, aprobada, rechazada, convertida y cancelada. |
| Orden | Borrador, emitida, parcialmente recibida, recibida, cerrada y cancelada. |
| Recepción | Completada o requiere conciliación por línea pendiente. |

Cancelar requiere motivo y conserva la evidencia. Una orden emitida no vuelve a borrador. Las cantidades recibidas nunca pueden superar la orden.

## Conciliación

Use **Conciliar** sólo cuando la recepción muestre el estado correspondiente. El reintento conserva claves estables y procesa exclusivamente las líneas pendientes. No cree otra recepción, no escriba Inventario directamente y no elimine los movimientos ya confirmados.

## Mensajes frecuentes

- **Unidad no activa:** seleccione una unidad vigente de Administración.
- **Partida inventariable incompleta:** seleccione artículo y almacén.
- **Una partida de servicio no admite artículo o almacén:** retire las referencias físicas.
- **La orden no coincide con la requisición:** corrija cantidad, unidad o tipo antes de guardar.
- **La cantidad excede lo pendiente:** capture sólo el saldo abierto.
- **Requiere conciliación:** reintente la línea visible; no duplique la recepción.
- **Proveedor fiscal incompleto:** complete el maestro antes de crear nuevas operaciones.

## Integraciones y propiedad del dato

Administración gobierna unidades, folios, permisos y activación del módulo. Inventario valida y registra únicamente recepciones físicas. Compras conserva la recepción comercial y snapshots legibles. Gastos/Cuentas por pagar, facturas y pagos permanecen fuera del runtime vigente.

## Reportes estándar de portada (Local)

La portada ofrece reportes descargables de proveedores, requisiciones, órdenes de compra y recepciones. Cada tarjeta abre filtros simples de búsqueda, moneda, estatus, prioridad o periodo según corresponda. Puede escribir para encontrar las opciones disponibles y después pulsar **Generar**; si no hay datos coincidentes, la pantalla lo indica sin descargar un archivo. El catálogo de proveedores omite perfil fiscal y contacto innecesarios.

Cada descarga exige el permiso de lectura correspondiente: `purchasing.supplier.read`, `purchasing.requisition.read`, `purchasing.order.read` o `purchasing.receipt.read`. La capacidad está disponible sólo en Local en este corte.

## Limitaciones vigentes

No incluye comparativo de cotizaciones, adjudicación parcial a varios proveedores, devoluciones, XML/PDF fiscal, factura, cuenta por pagar, pago, reabastecimiento automático ni reintento programado. Los listados requieren paginación server-side antes de volumen productivo alto.

## Soporte

Conserve folio de requisición, orden y recepción, proveedor, partida, estado y referencia de correlación. Indique también si la partida era inventariable o de servicio.
