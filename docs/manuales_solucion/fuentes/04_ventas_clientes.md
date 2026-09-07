# Manual funcional de Ventas y Clientes

- Audiencia: ejecutivos comerciales, aprobadores, responsables de surtido y supervisores de servicio
- Alcance por ambiente: clientes, cotizaciones, pedidos y entregas en Local y QA; órdenes de servicio sólo en Local
- Última revisión: 2026-09-06
- Capacidades cubiertas: clientes, cotizaciones, pedidos, surtido por inventario o producción, entregas y ejecución de servicios

## Propósito

Ventas conserva la relación comercial desde el cliente hasta el cumplimiento del pedido. Las partidas físicas se entregan mediante Inventario o Producción; las partidas de servicio generan una orden operativa propia y nunca aparecen en Entregas.

## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Clientes y contacto principal | Disponible | Disponible |
| Cotizaciones y aprobación | Disponible | Disponible |
| Pedidos y surtido por inventario/producción | Disponible | Disponible |
| Entregas parciales y confirmación | Disponible | Disponible |
| Órdenes de servicio, tiempos, costos y evidencia | Disponible | No disponible en el release vigente |
| Devoluciones, factura y cobranza | No disponible | No disponible |

## Mapa del módulo

- **Clientes:** maestro y contacto principal.
- **Cotizaciones:** propuesta comercial versionada por estado.
- **Pedidos:** conversión de cotización aprobada y estrategia de cumplimiento.
- **Órdenes de servicio:** ejecución, responsable, tiempo, costo, evidencia y aceptación; sólo Local.
- **Entregas:** documentos parciales o totales para partidas físicas.
- **Portada:** indicadores y reportes estándar de sólo lectura.

## Códigos y propiedad de referencias

Los folios visibles son independientes de los IDs técnicos. En modo administrado se reservan al guardar; en modo manual se captura un código único, normalizado a mayúsculas. Un reintento con la misma clave recupera el mismo folio. Cambiar el prefijo no renombra documentos existentes.

Ventas conserva snapshots comerciales de producto, cliente, precio y unidad. Producción e Inventario pueden usar códigos distintos; la relación siempre se realiza por ID estable, no por coincidencia de texto.

## Acceso y prerrequisitos

Los permisos se separan por recurso y acción: `sales.customer.*`, `sales.quote.*`, `sales.order.*`, `sales.delivery.*` y, para el corte Local, `sales.service_order.*`. Aprobar una cotización no concede configurar surtido; confirmar una entrega no concede cancelar el pedido; registrar tiempo de servicio no concede aceptarlo.

Antes de vender:

- configure folios, monedas y condiciones comerciales en Administración;
- mantenga productos/servicios activos en Producción;
- para surtido físico, vincule el producto con un artículo activo de Inventario y la misma unidad;
- para servicios, disponga de trabajadores activos elegibles en RH.

## Cliente y cotización

1. Cree el cliente y su contacto principal.
2. Abra **Cotizaciones** y seleccione cliente, vigencia, moneda y condiciones.
3. Agregue partidas con producto o servicio, cantidad, precio, descuento e impuestos permitidos.
4. Guarde el borrador y revise totales.
5. Envíe la cotización y apruébela con la autoridad correspondiente.
6. Si vence o deja de aplicar, use la transición explícita; no borre el documento.

## Convertir a pedido y definir cumplimiento

Una cotización aprobada se convierte una sola vez. El pedido conserva snapshots y saldos por partida.

- **Inventario:** reserva un artículo ya existente para entrega.
- **Producción:** crea una solicitud para que Producción valide receta y libere una orden; Ventas no la libera directamente.
- **Servicio:** en Local, confirmar el pedido crea exactamente una orden de servicio por cada partida de tipo servicio.

Las partidas de servicio no admiten el modo histórico `service` dentro de fulfillment, no generan reservas, movimientos o Entregas y se atienden desde **Órdenes de servicio**.

## Entregas físicas

1. Abra **Entregas** y seleccione un pedido con cantidad física disponible.
2. Capture documento, fecha y cantidades parciales o totales.
3. Guarde el borrador y revise que no exceda el saldo.
4. Confirme. Inventario consume reservas y Sales recalcula costo/margen real con la procedencia disponible.
5. Si el borrador no debe continuar, cancélelo antes de confirmar.

## Ejecutar una orden de servicio

1. Abra **Ventas > Órdenes de servicio** y seleccione la orden creada desde el pedido.
2. Planee fechas y responsable; RH valida que el trabajador permanezca activo y elegible.
3. Use **Asignar** e **Iniciar** con los permisos puntuales.
4. Registre tiempos, costos y evidencia. Cada registro conserva actor, fecha e idempotencia.
5. Si existe una pausa operativa, use **Poner en espera** y después **Reanudar**.
6. Envíe a aceptación y confirme **Aceptar** cuando el cliente o responsable valide el resultado.
7. Si se cancela, documente el motivo; el estado es terminal.

## Estados principales

| Documento | Estados |
|---|---|
| Cotización | Borrador, enviada/cotizada, aprobada, vencida y cancelada. |
| Pedido | Confirmado, en cumplimiento, parcial, completado o cancelado según sus partidas. |
| Entrega | Borrador, confirmada o cancelada. |
| Orden de servicio | Borrador, planeada, asignada, en curso, en espera, pendiente de aceptación, aceptada o cancelada. |

El ciclo principal de servicio es: `draft -> planned -> assigned -> in_progress -> pending_acceptance -> accepted`. Desde `in_progress` puede pasar a `on_hold` y volver; `cancelled` es terminal.

## Mensajes frecuentes

- **No se pudo reservar el folio:** revise la secuencia de Administración y reintente la misma operación.
- **Producto sin artículo vinculado:** complete el vínculo en Producción/Inventario antes del surtido.
- **Unidad incompatible:** el producto y artículo deben compartir la unidad estable.
- **Cantidad superior al saldo:** reduzca la entrega o revise confirmaciones anteriores.
- **Trabajador no elegible:** active trabajador, puesto y área en RH y confirme la elegibilidad comercial.
- **Transición no permitida:** recargue el estado y use una acción válida para ese momento.
- **Operación incierta:** conserve el estado confirmado y la referencia de correlación; no repita con otra clave.

## Integraciones y propiedad del dato

Administración gobierna folios, catálogos y permisos; Producción conserva productos, recetas y solicitudes productivas; Inventario conserva reservas, consumos y movimientos; RH valida responsables de servicio. Ventas conserva cliente, cotización, pedido, entrega y orden de servicio, sin FKs ni escrituras cruzadas.

## Reportes estándar de portada (Local)

La portada permite generar reportes descargables de clientes, cotizaciones, pedidos, entregas, margen comercial y órdenes de servicio. Abra la tarjeta, aplique búsqueda, estatus o periodo cuando aparezcan y pulse **Generar**. Puede escribir para encontrar un estatus; la búsqueda general acepta texto libre. Los reportes de clientes omiten RFC, contacto y domicilio; los demás usan snapshots comerciales necesarios. Si no existen coincidencias, no se crea un archivo vacío.

Se reutilizan `sales.customer.read`, `sales.quote.read`, `sales.order.read`, `sales.delivery.read` y `sales.service_order.read`. Las descargas son Local en este corte; el análisis transversal y los libros Excel con formato permanecen en el futuro módulo Reportes.

## Limitaciones vigentes

No incluye devoluciones, factura, cobranza, callback de costo real de Producción, PDF inmutable de pedido/remisión ni paginación por cursor. El límite preventivo de listados es 200 registros. Las órdenes de servicio de este manual están preparadas sólo en Local y no deben presentarse como disponibles en QA.

## Soporte

Conserve folio de cliente, cotización, pedido, entrega u orden de servicio; partida; estado; fecha y correlación. Nunca use datos personales reales en pruebas.
