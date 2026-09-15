# Manual funcional de Compras y Abastecimiento

- Audiencia: solicitantes, aprobadores, compradores, receptores y supervisores
- Alcance por ambiente: Local actual y QA; las mejoras pendientes de promoción se indican expresamente; versión funcional QA `b63cdad`
- Última revisión: 2026-09-14
- Capacidades cubiertas: proveedores, requisiciones multipartida, órdenes, preparación de recepciones, confirmación física por Almacén, aceptación de servicios por el solicitante, conciliación y reportes

## Propósito

Compras controla una necesidad desde la requisición hasta la recepción comercial. Conserva proveedor, autorizaciones, precios y saldos pendientes. Inventario sigue siendo autoridad únicamente cuando una partida representa un artículo físico.

## Corregir errores de captura

**Disponible en Local; pendiente de promoción a QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

Los errores de permisos, conexión o reglas generales se muestran como un aviso de la operación. Si no aparece un campo señalado, no cambie datos al azar: revise el aviso y conserve la referencia de correlación para soporte. Corregir un campo no elimina los avisos de los demás. Cerrar el formulario o recargar no garantiza conservar cambios sin guardar.


## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Proveedores y perfil fiscal | Disponible | Disponible |
| Requisiciones, aprobación y rechazo | Disponible | Disponible |
| Órdenes y recepciones inventariables | Disponible | Disponible |
| Conciliación manual de líneas fallidas | Disponible | Disponible |
| Partidas y aceptación de servicios sin Inventario | Disponible | Disponible |
| Confirmación de bienes por Almacén y reportes estándar | Disponible | Disponible |
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
| Partida inventariable | Exige artículo y, al preparar la recepción, almacén destino; genera entrada sólo cuando Almacén confirma los bienes. |
| Partida de servicio | Exige unidad activa, pero prohíbe artículo y almacén; el solicitante original acepta la prestación recibida. |
| Compra directa | Orden sin requisición; exige motivo explícito. |
| Recepción parcial | Registra sólo una fracción sin exceder el saldo abierto. |
| Requiere conciliación | Una autoridad externa no confirmó una línea; el documento conserva el pendiente exacto. |

## Acceso y preparación

Cada responsabilidad usa permisos independientes bajo `purchasing.*`: leer o crear proveedor, crear/editar/enviar/aprobar/rechazar/cancelar requisición, crear/editar/emitir/cancelar orden y crear/conciliar recepción. Aprobar no concede emitir; recibir no concede cancelar.

Preparar una recepción requiere `purchasing.receipt.create`. Confirmar o reintentar sus bienes corresponde a Almacén con `inventory.movement.create`; `purchasing.receipt.reconcile` por sí solo no autoriza la entrada física. La aceptación de servicios requiere ser el solicitante original de la requisición, o el comprador que creó la orden si fue directa, y contar con `purchasing.requisition.create` o `purchasing.order.create`. El nombre del rol no sustituye estos permisos ni permite aceptar servicios ajenos.

Antes de comprar:

- registre proveedor activo con razón social, RFC, régimen, correo de facturación y código postal fiscal;
- confirme que la unidad exista y esté activa en Administración;
- para una partida inventariable, confirme artículo y almacén activos;
- para un servicio, seleccione el tipo **Servicio** y no capture artículo ni almacén.

Compras puede estar activo sin Inventario en una empresa que sólo compra servicios. Inventario sigue siendo dependencia funcional cuando existen partidas físicas.

## Registrar o editar un proveedor

1. Abra **Compras > Proveedores**. La primera vista muestra el listado existente.
2. Pulse **Nuevo proveedor** para abrir el formulario en una ventana, o **Editar** en un proveedor existente.
3. Complete los datos comerciales, fiscales y de contacto. Revise moneda, condiciones, plazo y estatus.
4. Pulse **Guardar proveedor**. Al guardar se actualiza el listado; si hay un error, la ventana conserva la captura para corregirla.

Crear y editar requieren permisos distintos. Un proveedor heredado puede seguir visible con información fiscal incompleta; al modificar sus campos fiscales debe completar el conjunto obligatorio.

## Crear y autorizar una requisición

1. Abra **Compras > Requisiciones** y capture folio, fecha, prioridad y motivo.
2. Agregue una o más partidas. No repita el mismo artículo dentro del documento.
3. Defina tipo, unidad, cantidad y necesidad. Para artículos, escriba en el buscador y seleccione el código y nombre correctos; la unidad procede de Inventario. En espacios estrechos el selector ocupa una fila propia. Al elegir **Servicio**, capture descripción y unidad activa sin artículo ni almacén.
4. Guarde el borrador y corríjalo mientras permanezca editable.
5. Pulse **Enviar**. Un aprobador puede **Aprobar** o **Rechazar** con el permiso puntual.

Una requisición aprobada se convierte completa en una orden. La división por proveedor todavía no forma parte del corte.

## Crear y emitir una orden

1. Desde una requisición aprobada use **Crear orden de compra**.
2. Seleccione proveedor, moneda, condiciones y precio unitario de cada partida.
3. Revise que tipo, unidad y cantidad coincidan exactamente con la requisición.
4. Guarde el borrador; puede editarlo antes de emitir.
5. Pulse **Emitir orden**. Proveedor, partidas, cantidades y precios quedan congelados.

La API admite compras directas con motivo, pero su alta no está expuesta en este formulario. Para una orden directa existente creada por un medio autorizado, la aceptación de servicios corresponde al comprador original. No busque una opción de alta directa que esta pantalla no ofrece.

## Preparar la recepción en Compras

1. Abra **Compras > Recepciones** y seleccione una orden emitida.
2. Capture folio de recepción, documento del proveedor y cantidad por partida.
3. Para una partida inventariable, seleccione el almacén destino.
4. Para un servicio, indique la cantidad preparada para aceptación; no capture almacén.
5. Registre la recepción. Queda **Pendiente de confirmación**: esta acción no aumenta existencias ni acepta servicios.

Las cantidades pendientes ya comprometen el saldo de la orden para impedir una segunda recepción sobre la misma cantidad. Puede preparar recepciones parciales sobre el saldo todavía libre, sin duplicar una recepción que espera confirmación.

## Confirmar bienes y aceptar servicios

**Bienes físicos — Almacén:** abra **Almacenes > Movimientos**, despliegue el resumen de solicitudes pendientes y busque **Recepciones de compras pendientes**. Revise el folio, las partidas, las cantidades y el destino; después de recibir físicamente los bienes pulse **Confirmar recepción física** y confirme. Se registran las entradas y se actualizan las líneas de Compras.

**Servicios — solicitante:** abra **Compras > Requisiciones > Servicios comprados por aceptar**. La misma sección aparece en **Órdenes de compra** y **Recepciones**. La lista muestra las tareas del solicitante original; en una compra directa corresponde al comprador que creó la orden. Revise lo prestado y pulse **Aceptar servicio recibido** únicamente cuando lo haya recibido satisfactoriamente. Esto completa las partidas de servicio sin crear movimientos de Inventario.

Una recepción mixta termina cuando ambas responsabilidades confirman sus respectivas partidas. Por ejemplo, para diez piezas y una instalación, Almacén confirma las diez piezas y el solicitante acepta la instalación. Ninguno puede cerrar la parte del otro sólo por haber confirmado la propia.

## Estados

| Documento | Estados principales |
|---|---|
| Requisición | Borrador, enviada, aprobada, rechazada, convertida y cancelada. |
| Orden | Borrador, emitida, parcialmente recibida, recibida, cerrada y cancelada. |
| Recepción | Pendiente de confirmación mientras existan bienes o servicios sin confirmar; completada cuando todas las partidas terminaron; requiere conciliación si una confirmación dejó resultados inciertos. |

Cancelar requiere motivo y conserva la evidencia. Una orden emitida no vuelve a borrador. Las cantidades recibidas nunca pueden superar la orden.

## Conciliación

Si una confirmación falla, actualice las tareas para consultar el estado confirmado. Almacén continúa las partidas físicas desde **Movimientos**; el solicitante continúa sus servicios desde **Servicios comprados por aceptar**. El reintento de la misma tarea procesa sólo las líneas pendientes y conserva las entradas ya registradas. No cree otra recepción ni registre una entrada manual para suplirla. Si una parte ya terminó y otra espera a su responsable, el estado pendiente es normal y no indica un error.

## Mensajes frecuentes

- **Unidad no activa:** seleccione una unidad vigente de Administración.
- **Partida inventariable incompleta:** seleccione artículo y almacén.
- **Una partida de servicio no admite artículo o almacén:** retire las referencias físicas.
- **La orden no coincide con la requisición:** corrija cantidad, unidad o tipo antes de guardar.
- **La cantidad excede lo pendiente:** capture sólo el saldo abierto.
- **Requiere conciliación:** reintente la línea visible; no duplique la recepción.
- **Proveedor fiscal incompleto:** complete el maestro antes de crear nuevas operaciones.
- **Confirmación de Almacén requerida:** Compras ya preparó el documento; un usuario autorizado de Almacén debe continuar en **Movimientos**.
- **Aceptación del solicitante requerida:** entre con el usuario que solicitó la requisición o, para compra directa, con el comprador original. Aprobar la compra no concede aceptar el servicio por otra persona.
- **Hay cantidades pendientes de confirmar:** revise las recepciones existentes antes de volver a capturar el mismo saldo.

## Integraciones y propiedad del dato

Administración gobierna unidades, folios, permisos y activación del módulo. Inventario valida y registra únicamente recepciones físicas. Compras conserva la recepción comercial y snapshots legibles. Gastos/Cuentas por pagar, facturas y pagos permanecen fuera del runtime vigente.

## Reportes estándar de portada

La portada ofrece reportes descargables de proveedores, requisiciones, órdenes de compra y recepciones. Cada tarjeta abre filtros simples de búsqueda, moneda, estatus, prioridad o periodo según corresponda. Puede escribir para encontrar las opciones disponibles y después pulsar **Generar**; si no hay datos coincidentes, la pantalla lo indica sin descargar un archivo. El catálogo de proveedores omite perfil fiscal y contacto innecesarios.

Cada descarga exige el permiso de lectura correspondiente: `purchasing.supplier.read`, `purchasing.requisition.read`, `purchasing.order.read` o `purchasing.receipt.read`. La capacidad está disponible en Local y QA.

## Limitaciones vigentes

No incluye comparativo de cotizaciones, adjudicación parcial a varios proveedores, devoluciones, XML/PDF fiscal, factura, cuenta por pagar, pago, reabastecimiento automático ni reintento programado. Los listados requieren paginación server-side antes de volumen productivo alto.

## Soporte

Conserve folio de requisición, orden y recepción, proveedor, partida, estado y referencia de correlación. Indique también si la partida era inventariable o de servicio.
