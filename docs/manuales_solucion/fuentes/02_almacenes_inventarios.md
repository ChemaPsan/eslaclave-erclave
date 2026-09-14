# Manual funcional de Almacenes e Inventarios

- Audiencia: almacenistas, supervisores, planeadores y responsables de recepción
- Alcance por ambiente: Local actual y QA; las mejoras pendientes de promoción se indican expresamente
- Última revisión: 2026-09-14
- Versión funcional de referencia: QA `b63cdad`; mejoras Local de formularios, margen y evidencia pendientes de promoción
- Capacidades cubiertas: almacenes, artículos, movimientos, existencias, Kardex, reservas, valuación, solicitudes de entradas y salidas, transferencias en tránsito, devoluciones de materiales y reportes estándar

## Propósito

Almacenes e Inventarios es la autoridad de la existencia física. Los saldos y el Kardex se calculan a partir de movimientos inmutables; no son campos que se editen directamente.

## Corregir errores de captura

**Disponible en Local; pendiente de promoción a QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

Los errores de permisos, conexión o reglas generales se muestran como un aviso de la operación. Si no aparece un campo señalado, no cambie datos al azar: revise el aviso y conserve la referencia de correlación para soporte. Corregir un campo no elimina los avisos de los demás. Cerrar el formulario o recargar no garantiza conservar cambios sin guardar.


## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Almacenes, artículos y movimientos | Disponible | Disponible |
| Existencias, Kardex y valuación promedio | Disponible | Disponible |
| Reservas/consumos de Producción, Ventas y Mantenimiento | Disponible | Disponible |
| Recepción de compras inventariables | Disponible | Disponible |
| Recepción de producto terminado | Disponible | Disponible |
| Salidas de materiales productivos, refacciones y pedidos confirmadas por Almacén | Disponible | Disponible |
| Transferencias con recepción en destino y retorno al origen | Disponible | Disponible |
| Recepción de devoluciones de sobrantes | Disponible | Disponible |
| Lotes, series, cuarentena y ubicaciones operativas | No disponible | No disponible |

## Mapa del módulo

- **Almacenes:** maestros de ubicación y tipo operativo.
- **Artículos:** identidad logística, unidad, costo y elegibilidad.
- **Movimientos:** entradas, salidas, ajustes, reversas y recepciones especializadas.
- **Inventario:** existencias calculadas por artículo y almacén.
- **Kardex:** historia cronológica y valuada.
- **Portada:** reportes estándar de sólo lectura.

## Conceptos y campos principales

| Campo o concepto | Significado |
|---|---|
| Código | Identidad logística estable; puede asignarse mediante Administración. |
| Unidad base | Unidad en la que se interpreta toda la historia del artículo. |
| Costo unitario base | Referencia manual; la valuación promedio usa movimientos con costo cuando existen. |
| Usar en receta | Permite seleccionar el artículo como material productivo. |
| Producto terminado | Vínculo por ID con un producto comercial de Producción. |
| Existencia | Cantidad física calculada. |
| Reservado | Cantidad apartada por documentos operativos. |
| Disponible | Existencia menos reservas vigentes. |

## Acceso y permisos

Los permisos distinguen lectura, alta, modificación, reversa, reserva y recepciones especializadas. Las nuevas bandejas se consultan con `inventory.movement.read` y sus confirmaciones físicas usan `inventory.movement.create`; producto terminado conserva `inventory.finished_goods_receipt.read` para consulta e `inventory.finished_goods_receipt.receive` para recepción. Compras y Mantenimiento utilizan permisos propios para solicitar operaciones limitadas; no reciben escritura general sobre Inventario. Las responsabilidades de almacén origen y destino describen quién debe confirmar físicamente: el sistema autoriza por tenant y permisos, sin membresía individual por almacén en este corte.

## Crear un almacén o artículo

1. Cree el almacén con código, nombre, tipo y estado.
2. Para refacciones, use el tipo estable **Refacciones**; Mantenimiento sólo ofrece almacenes de ese tipo.
3. Cree el artículo con tipo, unidad base, costo y almacén sugerido.
4. Active **Usar en receta** sólo cuando sea material productivo.
5. Para producto terminado, vincúle el producto de Producción por su identidad estable.

La unidad debe existir y estar activa en Administración. Si el artículo ya tiene movimientos o reservas, no puede cambiarse a una unidad diferente. Los alias heredados administrados `LTS -> LTR` y `MT -> MTR` se normalizan sin alterar cantidades. Para un cambio real cree un artículo sustituto y regularice mediante movimientos autorizados.

## Registrar y consultar movimientos

1. Abra **Movimientos**. Para una captura manual, elija el tipo permitido; para un documento de otro módulo, use su solicitud vinculada en el bloque superior.
2. Seleccione artículo y almacén mediante los buscadores.
3. Capture cantidad, fecha, costo cuando aplique y referencia del documento.
4. Confirme. La operación actualiza existencia y Kardex de forma atómica.
5. Si un movimiento manual fue incorrecto y admite reversa, use la acción autorizada; no edite ni borre la historia. Los movimientos vinculados a otros documentos y las transferencias siguen su flujo de confirmación o devolución.

Use **Inventario** para consultar saldos y **Kardex** para explicar cómo se formaron. Los filtros muestran resultados acotados y conservan los IDs aunque el nombre visible cambie.

## Primera vista y solicitudes pendientes

Al entrar a **Movimientos**, el bloque **Solicitudes de entrada y salida** aparece cerrado antes del historial. Muestra **Hay entradas o salidas pendientes** cuando corresponde, o **Sin entradas ni salidas pendientes** cuando las consultas disponibles no tienen tareas. Pulse **Ver solicitudes** para desplegarlo y **Ocultar solicitudes** para regresar a la vista compacta.

Si aparece **Revisando solicitudes…** o un error, aún no hay confirmación de que todo esté atendido. Despliegue, actualice la sección afectada y revise sus páginas con **Anterior/Siguiente**. Las secciones disponibles dependen de sus permisos y módulos activos; el aviso no sustituye revisar el documento ni autoriza una entrada o salida por sí mismo.

## Reservas y consumos

Una reserva reduce disponible, no existencia. El consumo convierte la reserva en salida inmutable cuando Almacén confirma la entrega física. Producción reserva al liberar; Mantenimiento reserva al solicitar piezas; Ventas prepara la entrega de productos reservados. Iniciar Producción o resolver Mantenimiento no vuelve a descontar materiales. Compras prepara recepciones y Almacén confirma los bienes. Reintentar la misma solicitud conserva los movimientos ya registrados.

## Entregar materiales para Producción

1. Despliegue **Solicitudes de materiales para producción** y actualice la lista.
2. Revise folio, responsable, artículos, cantidades y almacenes de origen.
3. Entregue todos los materiales indicados y seleccione **Autorizar y entregar**.
4. Producción podrá iniciar la orden después de completar la salida. Aplica a productos y servicios con receta.

Si una entrega quedó pendiente de conciliación, reintente desde la misma solicitud para completar sólo las salidas faltantes. No vuelva a entregar físicamente lo que ya entregó.

## Autorizar o rechazar refacciones

1. Abra **Solicitudes de refacciones** y revise orden de Mantenimiento, técnico, almacén y partidas.
2. Cuando la reserva esté confirmada y se entreguen todas las piezas, pulse **Autorizar y entregar**. La salida queda registrada y resolver Mantenimiento no vuelve a descontarla.
3. Si corresponde rechazar una solicitud aún no entregada, seleccione **Rechazar solicitud** y capture el motivo. Se liberan las reservas sin crear salidas.

Una reserva fallida o interrumpida debe completarse desde **Mantenimiento > Órdenes** con **Reintentar reserva** o **Reintentar cancelación**, según el pendiente. Almacén no puede entregar una reserva sin confirmar. Si ya comenzó la entrega, no se permite rechazarla: use **Reintentar entrega** para completar únicamente las partidas pendientes.

## Recibir una compra inventariable

1. Compras prepara la recepción con sus partidas, cantidades y almacenes.
2. En **Movimientos > Ver solicitudes > Recepciones de compras pendientes**, revise los bienes contra lo que llegó físicamente.
3. Pulse **Confirmar recepción física** sólo cuando coincidan los bienes recibidos con la solicitud; si hay diferencias, coordine su corrección con Compras antes de confirmar.
4. Consulte la entrada vinculada y la actualización de la recepción.

Si una confirmación multipardida queda incompleta, conserve los movimientos confirmados y use **Continuar confirmación pendiente** desde esta misma bandeja. Los servicios comprados no generan movimientos: los acepta quien los solicitó en Compras; en una compra directa corresponde al comprador.

## Dar salida a un pedido de venta

Ventas prepara la entrega. En **Movimientos > Ver solicitudes > Salidas de pedidos de venta**, revise el pedido, los artículos, cantidades y almacenes. Después de verificar la entrega física, pulse **Confirmar salida física**. La salida actualiza el documento comercial y consume las reservas correspondientes; una falla parcial se continúa desde la misma tarea. Los servicios comerciales se cumplen desde sus órdenes de servicio en Ventas.

## Transferir entre almacenes

1. Registre una **Transferencia** con artículo, almacén origen, un destino diferente, cantidad y motivo. La confirmación descuenta el origen; todavía no incrementa el destino.
2. El responsable del destino abre **Movimientos > Ver solicitudes > Transferencias en tránsito** y revisa origen, destino y saldo pendiente.
3. Al recibir, selecciona **Confirmar recepción física**, captura la cantidad que realmente llegó y las observaciones. Se permiten recepciones parciales hasta agotar el saldo.
4. Si debe regresar el saldo restante, el destino selecciona **Solicitar devolución del saldo**. Esta solicitud no incrementa el origen.
5. Cuando los bienes regresen físicamente, el origen usa **Recibir devolución en origen** e indica lo recibido.

La transferencia permanece pendiente mientras haya saldo en tránsito. Una vez solicitado el retorno del saldo, continúe por devolución al origen. No use una reversa manual para simular una recepción o el retorno.

## Recibir sobrantes de Producción o Mantenimiento

La recepción en Almacén está implementada. El acceso para iniciar una devolución desde Mantenimiento tiene una incidencia de montaje de pantalla pendiente de verificación, descrita en su manual; si no aparece, repórtelo y no sustituya el flujo con una entrada manual.

El área que usó el material solicita una devolución desde su orden terminada o cancelada; Mantenimiento también admite órdenes resueltas o cerradas. En **Devoluciones de materiales por recibir**, revise artículo, cantidad y documento. Pulse **Confirmar recepción física** únicamente después de recibir el sobrante. Se registra una entrada vinculada a la salida original y se concilia la cantidad/costo devuelto en el módulo de origen.

Si el sobrante ya no se devolverá, **Cancelar solicitud de devolución** exige motivo y sólo aplica mientras esté pendiente, antes de registrar la entrada. Si la entrada ya ocurrió y falta conciliación, use **Continuar confirmación pendiente**; no reciba físicamente dos veces ni cree otra solicitud para el mismo material.

## Recibir producto terminado

1. Confirme que la orden de Producción esté **Terminada** y el producto tenga artículo terminado vinculado.
2. Abra **Movimientos > Ver solicitudes > Entradas de producción terminada**.
3. Revise folio, producto, unidad y cantidad pendiente.
4. Seleccione almacén, capture la cantidad físicamente recibida, fecha y observaciones.
5. Confirme la entrada.

Se permiten recepciones parciales y nunca puede superarse lo producido. Una reversa vuelve a incrementar el pendiente. El rol receptor sólo ve la proyección necesaria; no recibe receta, recursos ni costos completos de Producción.

## Conversiones y costos

Sólo se convierten unidades activas de la misma categoría con factor estándar. Cajas, paquetes y presentaciones empresariales requieren equivalencias futuras. El costo manual funciona como referencia cuando no existe saldo valuado; los movimientos con costo construyen el promedio. La política para actualizar costo base desde Compras sigue pendiente.

## Mensajes frecuentes

- **Unidad incompatible:** seleccione una unidad activa de la misma categoría.
- **La unidad base no puede cambiar:** proteja la historia y use un artículo sustituto.
- **Existencia insuficiente:** revise saldo, reservas concurrentes y almacén.
- **Movimiento duplicado:** reintente con la misma operación; no capture otra salida o entrada.
- **Falta vínculo de producto terminado:** relacione el producto con un artículo activo.
- **La cantidad excede lo pendiente:** capture sólo el saldo físicamente recibido.
- **Crea primero un almacén de refacciones:** registre o active uno de tipo `spare_parts`.

## Integraciones y propiedad del dato

Producción solicita reservas y expone materiales/producto terminado; Ventas prepara entregas; Compras prepara recepciones; Mantenimiento solicita refacciones. Almacén confirma las entradas y salidas físicas desde Movimientos. Inventario decide su validez y conserva movimiento, costo y Kardex; cada módulo conserva y concilia su documento. Ningún consumidor escribe las tablas de otro módulo.

## Reportes estándar de portada

La portada genera reportes descargables de almacenes, artículos, saldos de inventario, movimientos/Kardex y críticos con reservas superiores a la existencia. Abra una tarjeta, seleccione los filtros mínimos disponibles y pulse **Generar**. Puede escribir para encontrar tipo, categoría, estatus, condición o movimiento; la búsqueda general acepta texto libre y el periodo usa fechas. Un resultado vacío se informa sin crear archivo.

La descarga usa los permisos existentes `inventory.warehouse.read`, `inventory.item.read`, `inventory.balance.read` o `inventory.kardex.read`. Los reportes operan en Local y QA y consultan exclusivamente datos propiedad de Inventario.

## Limitaciones vigentes

No incluye lotes, series, cuarentena, inventario bloqueado, ubicaciones operativas detalladas, equivalencias de empaque ni recepción de merma. Las transferencias sí conservan saldo en tránsito con recepción o devolución confirmada. El catálogo de artículos requiere evolución server-side antes de volúmenes muy altos.

## Soporte

Ejemplo: al transferir 6 unidades y recibir 4, las 2 restantes sólo regresan al saldo de origen cuando éste confirma su recepción. Conserve artículo, almacén, folio, fecha y correlación para soporte. No modifique la base ni improvise movimientos para ocultar una conciliación pendiente.
