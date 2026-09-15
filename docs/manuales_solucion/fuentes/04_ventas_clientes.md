# Manual funcional de Ventas y Clientes

- Audiencia: ejecutivos comerciales, aprobadores, responsables de surtido y supervisores de servicio
- Alcance por ambiente: Local actual y QA; las mejoras pendientes de promoción se indican expresamente; versión funcional QA `b63cdad`
- Última revisión: 2026-09-14
- Capacidades cubiertas: clientes, cotizaciones, pedidos, surtido por inventario o solicitud a Producción, preparación de entregas, salida física por Almacén, ejecución de servicios y reportes

## Propósito

Ventas conserva la relación comercial desde el cliente hasta el cumplimiento del pedido. Las partidas físicas se entregan mediante Inventario o Producción; las partidas de servicio generan una orden operativa propia y nunca aparecen en Entregas.

## Corregir errores de captura

**Disponible en Local; pendiente de promoción a QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

Los errores de permisos, conexión o reglas generales se muestran como un aviso de la operación. Si no aparece un campo señalado, no cambie datos al azar: revise el aviso y conserve la referencia de correlación para soporte. Corregir un campo no elimina los avisos de los demás. Cerrar el formulario o recargar no garantiza conservar cambios sin guardar.


## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Clientes y contacto principal | Disponible | Disponible |
| Cotizaciones y aprobación | Disponible | Disponible |
| Pedidos y surtido por inventario/producción | Disponible | Disponible |
| Entregas parciales y confirmación | Disponible | Disponible |
| Órdenes de servicio, tiempos, costos y evidencia | Disponible | Disponible |
| Salida física por Almacén y reportes estándar | Disponible | Disponible |
| Devoluciones, factura y cobranza | No disponible | No disponible |

## Mapa del módulo

- **Clientes:** maestro y contacto principal.
- **Cotizaciones:** propuesta comercial versionada por estado.
- **Pedidos:** conversión de cotización aprobada y estrategia de cumplimiento.
- **Órdenes de servicio:** ejecución, responsable, tiempo, costo, evidencia y aceptación.
- **Entregas:** documentos parciales o totales para partidas físicas.
- **Portada:** indicadores y reportes estándar de sólo lectura.

## Códigos y propiedad de referencias

Los folios visibles son independientes de los IDs técnicos. En modo administrado se reservan al guardar; en modo manual se captura un código único, normalizado a mayúsculas. Un reintento con la misma clave recupera el mismo folio. Cambiar el prefijo no renombra documentos existentes.

Ventas conserva snapshots comerciales de producto, cliente, precio y unidad. Producción e Inventario pueden usar códigos distintos; la relación siempre se realiza por ID estable, no por coincidencia de texto.

## Acceso y prerrequisitos

Los permisos se separan por recurso y acción: `sales.customer.*`, `sales.quote.*`, `sales.order.*`, `sales.delivery.*` y `sales.service_order.*`. Aprobar una cotización no concede configurar surtido; registrar tiempo de servicio no concede aceptarlo. Ventas prepara el documento con `sales.delivery.create`, pero Almacén confirma la salida física con `inventory.movement.create`. Tener únicamente `sales.delivery.confirm` no permite sustituir la confirmación de Almacén.

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
5. En la tarjeta en **Borrador**, pulse **Emitir cotización** para pasar a **Cotizada**. Requiere `sales.quote.submit`.
6. En **Cotizada**, un usuario con `sales.quote.approve` pulsa **Aprobar cotización**. Sólo entonces queda **Aprobada** y puede generar un pedido.
7. Si vence o deja de aplicar, use la transición explícita; no borre el documento.

No existe un salto directo de Borrador a Aprobada. La tarjeta explica la siguiente acción y orienta cuando falta permiso: solicite la intervención de una persona autorizada o la revisión de permisos en Administración. Editar sólo está disponible en Borrador. Emitir y aprobar revalidan vigencia, cliente, responsable, productos y unidades; si falta un requisito, corrija lo indicado antes de reintentar.

## Convertir a pedido y definir cumplimiento

Una cotización aprobada se convierte una sola vez. El pedido conserva snapshots y saldos por partida.

- **Inventario:** reserva un artículo ya existente para entrega.
- **Producción:** crea una solicitud para que Producción valide receta y libere una orden; Ventas no la libera directamente.
- **Servicio:** confirmar el pedido crea exactamente una orden de servicio por cada partida de tipo servicio.

Las partidas de servicio se atienden desde **Órdenes de servicio**; no generan reservas, movimientos ni Entregas. Estas órdenes comerciales son distintas de las órdenes de Producción de tipo servicio con receta: el flujo comercial no incorpora entrega de materiales en esta versión.

## Entregas físicas

1. Abra **Entregas** y seleccione un pedido con cantidad física disponible.
2. Capture documento, fecha y cantidades parciales o totales.
3. Guarde el documento y revise que no exceda el saldo. Se muestra **Pendiente de entrega**; corresponde al borrador de la entrega.
4. El documento preparado queda pendiente de salida por Almacén. Guardarlo no descuenta inventario.
5. Almacén abre **Almacenes > Movimientos**, despliega el resumen de solicitudes pendientes y entra en **Salidas de pedidos de venta**.
6. Después de revisar y entregar físicamente los productos, el usuario autorizado pulsa **Confirmar salida física** y confirma. Inventario consume las reservas; Ventas actualiza la entrega y recalcula costo y margen real con la procedencia disponible.
7. Si el borrador no debe continuar, Ventas lo cancela antes de la confirmación física.

La entrega necesita surtido por existencias y reservas comprobables. Una solicitud a Producción no equivale por sí misma a mercancía disponible para despacho: la conexión automática entre esa solicitud, la recepción de producto terminado y la entrega comercial sigue pendiente. Si falta surtido, continúe el requisito indicado en el pedido; no registre una salida manual para eludirlo.

Ante una operación incierta, Almacén actualiza las tareas y continúa la misma entrega. Los reintentos conservan el avance por reserva para evitar un segundo consumo. Una entrega ya confirmada no debe capturarse de nuevo.

## Ejecutar una orden de servicio

1. Abra **Ventas > Órdenes de servicio** y seleccione la orden creada desde el pedido.
2. Planee fechas y responsable; RH valida que el trabajador permanezca activo y elegible.
3. Use **Asignar** e **Iniciar** con los permisos puntuales. Al iniciar y reanudar se vuelve a comprobar la elegibilidad del responsable en RH; una asignación anterior no evita esa revisión.
4. Registre tiempos, costos y evidencia. Cada registro conserva actor, fecha e idempotencia.
5. Si existe una pausa operativa, use **Poner en espera** y después **Reanudar**.
6. Envíe a aceptación y confirme **Aceptar** cuando el cliente o responsable valide el resultado.
7. Si se cancela, documente el motivo; el estado es terminal.

## Estados principales

| Documento | Estados |
|---|---|
| Cotización | Borrador: captura editable; Cotizada: emitida, espera aprobación; Aprobada: puede generar pedido; Vencida y Cancelada: no continúan al pedido. |
| Pedido | Confirmado: creado; Pendiente de surtido: falta completar cumplimiento; Listo: puede continuar; Parcialmente entregado: falta saldo; Entregado: cumplimiento terminado; Cancelado: no continúa. |
| Entrega | Pendiente de entrega: documento en borrador preparado para Almacén; Entregado: confirmación y salida registradas; Cancelado: no se despacha. Si la confirmación se interrumpe, la misma tarea conserva su progreso para reintento. |
| Orden de servicio | Borrador, planeada, asignada, en curso, en espera, pendiente de aceptación, aceptada o cancelada. |

El ciclo principal de servicio es: `draft -> planned -> assigned -> in_progress -> pending_acceptance -> accepted`. Desde `in_progress` puede pasar a `on_hold` y volver; `cancelled` es terminal.

## Mensajes frecuentes

- **No se pudo reservar el folio:** revise la secuencia de Administración y reintente la misma operación.
- **Producto sin artículo vinculado:** complete el vínculo en Producción/Inventario antes del surtido.
- **Unidad incompatible:** el producto y artículo deben compartir la unidad estable.
- **Cantidad superior al saldo:** reduzca la entrega o revise confirmaciones anteriores.
- **Trabajador no elegible:** active trabajador, puesto y área en RH y confirme la elegibilidad comercial.
- **Transición no permitida:** recargue el estado y use una acción válida para ese momento.
- **Cotización aún en Borrador:** una persona con permiso debe emitirla; después corresponde aprobarla. Editar o imprimir el PDF no cambia su estado.
- **Salida de Almacén requerida:** la entrega comercial está preparada; un usuario autorizado debe confirmar los productos desde **Movimientos > Salidas de pedidos de venta**.
- **Surtido pendiente:** revise la configuración y reservas del pedido antes de preparar o confirmar la entrega.
- **Responsable ya no elegible:** revise trabajador, puesto y área con RH antes de iniciar o reanudar; cambiar el estado comercial no corrige el maestro de personal.
- **Operación incierta:** conserve el estado confirmado y la referencia de correlación; no repita con otra clave.

## Integraciones y propiedad del dato

Administración gobierna folios, catálogos y permisos; Producción conserva productos, recetas y solicitudes productivas; Inventario conserva reservas, consumos y movimientos; RH valida responsables de servicio. Ventas conserva cliente, cotización, pedido, entrega y orden de servicio, sin FKs ni escrituras cruzadas.

## Reportes estándar de portada

La portada permite generar reportes descargables de clientes, cotizaciones, pedidos, entregas, margen comercial y órdenes de servicio. Abra la tarjeta, aplique búsqueda, estatus o periodo cuando aparezcan y pulse **Generar**. Puede escribir para encontrar un estatus; la búsqueda general acepta texto libre. Los reportes de clientes omiten RFC, contacto y domicilio; los demás usan snapshots comerciales necesarios. Si no existen coincidencias, no se crea un archivo vacío.

Se reutilizan `sales.customer.read`, `sales.quote.read`, `sales.order.read`, `sales.delivery.read` y `sales.service_order.read`. Las descargas están disponibles en Local y QA; el análisis transversal y los libros Excel con formato permanecen en el futuro módulo Reportes.

## Limitaciones vigentes

No incluye devoluciones, factura, cobranza, actualización automática del costo real desde Producción, PDF inmutable de pedido/remisión ni paginación por cursor. El límite preventivo de listados es 200 registros. Tampoco automatiza el recorrido completo desde la solicitud comercial a Producción hasta su recepción y entrega al cliente.

## Soporte

Conserve folio de cliente, cotización, pedido, entrega u orden de servicio; partida; estado; fecha y correlación. Nunca use datos personales reales en pruebas.
