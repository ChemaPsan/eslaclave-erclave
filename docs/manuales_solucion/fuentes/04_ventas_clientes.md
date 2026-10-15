# Manual funcional de Ventas y Clientes

- Audiencia: ejecutivos comerciales, aprobadores, responsables de surtido y supervisores de servicio
- Alcance por ambiente: Local y QA; las capacidades futuras se indican expresamente; versión funcional QA `e57237f`
- Última revisión: 2026-10-14 (costo estimado CC-21, costos de Servicios y fabricación por División sólo Local; sin promoción QA)
- Capacidades cubiertas: clientes, cotizaciones, pedidos, surtido por inventario o solicitud a Producción, preparación de entregas, salida física por Almacén, ejecución de servicios y reportes

## Costo estimado de cotizaciones · CC-21 sólo Local

Asigna una División al borrador antes de usar el costo estimado. Sales consulta el costo confirmado de Production para esa División y Sociedad. Si la moneda de cotización difiere de la moneda base de la Sociedad, captura una tasa que indique cuántas unidades de la moneda de cotización corresponden a una unidad de moneda de costo; si coinciden, la tasa es 1. La vista previa de costo y margen se actualiza al guardar contexto, editar y enviar. Al aprobar se consulta de nuevo y se congela el valor; el pedido conserva esa copia. Si falta costo confirmado o tasa, puedes enviar y aprobar con costo y margen sin valor. Los documentos anteriores sin procedencia conservan su historia y no se presentan como estimados verificados en los reportes CSV. Accounting sigue apagado.

## Operación por División y moneda de costo · sólo Local

En Surtimiento del pedido dimensionado seleccione almacén de su División y revise la cantidad pendiente. Cuando difieran las monedas, capture cuántas unidades de moneda del pedido equivalen a una de la Sociedad. La tasa queda fija; entrega conserva original y convertido. La alternativa Solicitar fabricación crea un vínculo con Producción; su recepción se concilia explícitamente antes de entregar. Un error conserva captura para corregir/reintentar.


## Contexto organizacional de cotizaciones (Local, revisión 2026-10-05)

En Cotizaciones abre Contexto organizacional. En un borrador, busca y selecciona División y guarda; requiere cliente y recursos disponibles y condiciones confirmadas. La moneda debe coincidir con el borrador. Consulta Sociedad y copia guardada; Actualizar condiciones sólo funciona en borrador y conserva División/cliente. Si cambia la moneda, prepara otro borrador con importes correctos. Una cotización aprobada con contexto ya puede convertirse en pedido; el pedido conserva esa copia de condiciones. Consulta División, Sociedad y revisión en su ficha y en sus órdenes de servicio. En Local puede cancelarse el pedido con motivo; un fallo conserva la captura para reintentar. El surtimiento desde existencias y sus entregas dimensionadas están habilitados Local; fabricación se solicita, planifica y concilia por el recorrido explícito descrito más adelante. En Órdenes de servicio, consulta el contexto del pedido, planea fechas y busca al responsable dentro de su División. Captura tiempos con tarifa explícita y costos confirmados en moneda base de Sociedad; si difiere de la moneda del pedido, registra una tasa explícita. Se conservan original y convertido. Adjunta evidencia, solicita aceptación y acepta según tus permisos. La aceptación calcula el costo real documental y actualiza la partida de servicio; no activa Contabilidad. Si un recurso deja de estar disponible, se rechaza continuar; aún puedes pausar o cancelar con motivo. Un pedido en cancelación impide nuevas capturas. Las cotizaciones anteriores siguen su flujo hasta asignar contexto.


## Condiciones comerciales de cada División

Revisión: 2026-09-28. Alcance: Local de preparación, sin promoción QA/Producción. Audiencia: responsables del catálogo comercial.

Cada División conserva sus propias condiciones. Debes capturarlas completas aunque sean iguales a las de otra División. Cambiar la ficha general no las actualiza. No existe herencia ni copia automática.

1. Abre **Disponibilidad por División** desde la tarjeta y selecciona una asociación existente mediante **Ver / editar**. Si es nueva, guarda primero la asociación.
2. Abre **Condiciones de esta División**. Si aún no se configuró, verás **Pendiente de configurar** y campos vacíos.
3. Selecciona **Moneda** y **Condiciones de pago** de los catálogos vigentes. Captura el **límite de crédito** explícitamente; cero es válido. El importe de crédito usa la moneda seleccionada, admite hasta dos decimales y debe ser no negativo.
4. Pulsa **Guardar condiciones** y espera la confirmación. **Recargar datos** vuelve a consultar las condiciones guardadas y reemplaza la captura no guardada.
5. **Volver a asignaciones** permite elegir otra División; sus condiciones son independientes.

Consultar requiere `sales.customer.read`; guardar requiere `sales.customer.update`, alcance autorizado y maestro/asociación activos. Los registros inactivos conservan las condiciones para consulta. Si cambia la Sociedad, confirma primero la asociación y después revisa y vuelve a guardar las condiciones.

Un código histórico no vigente permanece visible, pero debes elegir códigos activos al guardar. Si falla el catálogo, la lectura confirmada sigue disponible y el guardado se bloquea; usa **Recargar datos** cuando se recupere. Los errores conservan captura y señalan los campos afectados. Ante conflicto de revisión, recarga y revisa antes de guardar de nuevo.

Los documentos existentes mantienen sus condiciones; en Local, la cotización con contexto guarda las condiciones confirmadas de su División y el pedido conserva esa copia. Guardar un límite de crédito no activa control de saldos ni exposición entre Divisiones. Este flujo no activa Contabilidad ni exige Centro de costos.

## Disponibilidad por División

Revisión: 2026-09-28. Alcance: entorno Local de preparación; no disponible todavía en QA/Producción. Audiencia: responsables del catálogo de clientes.

Un cliente conserva un único maestro y puede estar disponible en varias Divisiones. La Sociedad corresponde a la División seleccionada; no se captura manualmente. Las condiciones comerciales de cada División se capturan explícitamente en el apartado Condiciones comerciales de cada División, sin herencia del maestro. En Local, cotizaciones y pedidos con contexto validan la disponibilidad y condiciones de su División. Los documentos sin contexto mantienen su recorrido previo hasta asignación/migración explícita. Esto no activa Contabilidad.

Para consultar necesitas permiso `sales.customer.read`, módulo activo y alcance organizacional vigente. Guardar requiere `sales.customer.update` y acceso a la División. Para activar una asociación, el cliente debe estar activo.

1. Abre **Ventas → Clientes** y pulsa **Disponibilidad por División** en la tarjeta.
2. Busca y selecciona la División por código o nombre. Verifica la Sociedad derivada que muestra la pantalla.
3. Elige **Activa** para habilitar disponibilidad. Pulsa **Guardar asignación** y comprueba la confirmación.
4. Para retirar disponibilidad, abre la asociación existente mediante **Ver / editar**, elige **Inactiva** y guarda. El maestro y su historial se conservan.
5. Usa **Anterior/Siguiente** para recorrer los resultados o las asociaciones existentes.

Ante un conflicto de revisión, vuelve a seleccionar la asociación para cargar su estado confirmado antes de editar. Un rechazo conserva la captura; revisa el mensaje y corrige el campo indicado. Si cambia la Sociedad de una División, vuelve a guardar explícitamente la asociación activa para confirmar su disponibilidad. No se exige Centro de costos en este procedimiento.


## Propósito

Ventas conserva la relación comercial desde el cliente hasta el cumplimiento del pedido. Las partidas físicas se entregan mediante Inventario o Producción; las partidas de servicio generan una orden operativa propia y nunca aparecen en Entregas.

## Corregir errores de captura

**Disponible en Local y QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

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
| Costos de Servicios por División con original y conversión explícita | Implementado; validación Local | No promovido |
| Fabricación integrada desde pedidos por División | Implementado; validación Local | No promovido |
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

## Fabricar y conciliar una partida por División

**Disponible en Local; no promovido a QA.** Este procedimiento conecta el pedido, la orden productiva, la recepción física y la reserva comercial. No libera ni recibe automáticamente.

1. En **Ventas > Pedidos**, abra el contexto del pedido. En **Fabricación del pedido**, identifique una partida física pendiente. La pantalla conserva producto, cantidad y unidad del pedido.
2. Revise la moneda base de la Sociedad y la moneda del pedido. Si son distintas, capture el **Tipo de cambio**: cuántas unidades de moneda del pedido equivalen a una unidad de la moneda base. Si coinciden se utiliza uno.
3. Pulse **Solicitar fabricación**. El pedido conserva una solicitud vinculada; todavía no hay mercancía reservada para entrega. Las partidas pendientes pueden configurarse en operaciones separadas sin cambiar las ya atendidas.
4. Consulte **Seguimiento de fabricación** y pulse **Actualizar seguimiento**. Con permiso de liberación productiva, **Planificar orden de producción** abre el formulario de Producción; en caso contrario, el responsable de Producción atiende la solicitud en su bandeja.
5. El formulario productivo mantiene División, producto, cantidad y unidad de sólo lectura. Producción selecciona receta, fechas y responsables, valida recursos y genera una única orden para esa solicitud.
6. Una vez terminada la orden, Almacenes confirma la recepción de producto terminado. Vuelva al seguimiento del pedido y actualícelo. Las recepciones insuficientes se muestran sin poder seleccionarlas.
7. Seleccione un **Almacén con recepción de producto terminado** habilitado y pulse **Conciliar recepción de fabricación**. El sistema exige orden terminada, recepción confirmada y existencias suficientes en un almacén elegible de la División. No capture otra cantidad ni un costo sustituto.
8. Tras la conciliación confirmada, prepare la entrega habitual. Almacenes confirma después la salida física; conciliar no descuenta existencias.

Consultar el seguimiento, solicitar fabricación y conciliar requieren `sales.order.fulfill`; la lectura del pedido por sí sola no habilita esas consultas. crear la orden productiva requiere `production.order.release`. La recepción mantiene permisos propios de Almacenes. Tener permiso en Ventas no concede esas otras acciones.

Si no existe recepción suficiente, continúe en Almacenes y vuelva a actualizar; no sume cantidades de varios almacenes para eludir el requisito. Un rechazo conserva la selección o tasa capturada. Si se interrumpe una operación, reintente la misma captura; el sistema recupera el avance confirmado sin duplicar solicitud, orden o reserva. Si el pedido está en cancelación o existe un intento pendiente, resuelva primero la recuperación indicada.

## Entregas físicas

1. Abra **Entregas** y seleccione un pedido con cantidad física disponible.
2. Capture documento, fecha y cantidades parciales o totales.
3. Guarde el documento y revise que no exceda el saldo. Se muestra **Pendiente de entrega**; corresponde al borrador de la entrega.
4. El documento preparado queda pendiente de salida por Almacén. Guardarlo no descuenta inventario.
5. Almacén abre **Almacenes > Movimientos**, despliega el resumen de solicitudes pendientes y entra en **Salidas de pedidos de venta**.
6. Después de revisar y entregar físicamente los productos, el usuario autorizado pulsa **Confirmar salida física** y confirma. Inventario consume las reservas; Ventas actualiza la entrega y recalcula costo y margen real con la procedencia disponible.
7. Si el borrador no debe continuar, Ventas lo cancela antes de la confirmación física.

La entrega necesita reservas comprobables. Una solicitud a Producción no equivale por sí misma a mercancía disponible: en Local, la fabricación por División debe terminarse, recibirse en Inventarios y conciliarse explícitamente antes de preparar el despacho. Si falta surtido, continúe el requisito indicado en el pedido; no registre una salida manual para eludirlo.

Ante una operación incierta, Almacén actualiza las tareas y continúa la misma entrega. Los reintentos conservan el avance por reserva para evitar un segundo consumo. Una entrega ya confirmada no debe capturarse de nuevo.

## Ejecutar una orden de servicio

Este flujo comercial es distinto de una orden de Producción con receta de servicio. La captura inicial/final de fotos y documentos, su optimización y vencimiento a 365 días pertenecen a Producción; no se aplican a esta orden comercial.

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

No incluye devoluciones, factura, cobranza, actualización automática del costo real desde Producción, PDF inmutable de pedido/remisión ni paginación por cursor. El límite preventivo de listados es 200 registros. La fabricación por División tiene planificación, recepción y conciliación explícitas; no son acciones automáticas.

## Soporte

Conserve folio de cliente, cotización, pedido, entrega u orden de servicio; partida; estado; fecha y correlación. Nunca use datos personales reales en pruebas.


## Demoras de comunicación en Local

Mejora disponible solo en Local, pendiente de QA: la espera de cada petición incluye la descarga de la respuesta. Un fallo conserva la captura mientras permanezca abierto el formulario; no realiza un nuevo envío automáticamente. Consulte el estado del registro antes de repetir una operación cuyo resultado no se confirmó.

## Capturar costo original y convertido de servicios

Disponible sólo en Local; sin promoción QA. La División y Sociedad se conservan desde el pedido. Para una nueva entrada de tiempo o costo:

1. Revise la moneda base de Sociedad y la moneda documental mostradas; no son intercambiables.
2. Capture minutos y tarifa por hora, o cantidad y costo unitario según el formulario. La tarifa/costo se expresa en moneda Sociedad, admite cero y hasta seis decimales. No se hereda automáticamente del puesto.
3. Confirme explícitamente que el importe corresponde a la moneda indicada. Si las monedas difieren, capture cuántas unidades de moneda del pedido equivalen a una unidad de moneda Sociedad; la tasa debe ser positiva y admite hasta doce decimales. Si coinciden, la tasa es uno.
4. Guarde y revise la entrada confirmada: se conserva el total original a seis decimales y el convertido documental a dos decimales. Una tasa posterior no reescribe entradas ya guardadas.
5. Continúe con evidencia y aceptación según permisos. Aceptar consolida los importes convertidos del servicio y actualiza el pedido. Si existen entradas anteriores sin moneda confirmada, el sistema exige revisión; no les asigne moneda por inferencia.

Ejemplo: costo original de 10 USD, pedido MXN y tasa 18.5 MXN por USD conserva 10 USD y 185.00 MXN. La tarifa no es un asiento contable y esta captura no cambia precios de venta.

Un rechazo conserva los datos mientras el formulario esté abierto. Corrija moneda, tasa o elegibilidad según el aviso y reintente la misma captura para evitar duplicados. Los documentos sin División conservan su comportamiento anterior; las entradas históricas sin metadatos mantienen sus importes, no se convierten retroactivamente. La fabricación de partidas físicas usa el procedimiento de solicitud, recepción y conciliación descrito en este manual, separado de los servicios.

## Documentos relacionados

[Registro de esta fuente y su Word](../REGISTRO.md) · [Ficha funcional](../../../modulos/04_ventas_clientes.md) · [Estado por ambiente](../../contexto/ESTADO_ACTUAL.md) · [Control de integración por submódulo](../../contexto/CONTROL_CONTABLE.md).

Si una conciliación ya inició y quedó sin respuesta, el seguimiento puede habilitar exclusivamente el almacén guardado para continuar ese intento. Esa opción recupera la reserva existente; no afirma que haya disponibilidad libre para una nueva reserva.

## Imprimir cotizaciones con identidad de Division en Local

En una cotizacion con contexto, la vista de impresion usa plantilla e identidad vigentes de su Division mientras siga sin aprobar. Al aprobar, conserva la presentacion con Emisor, Sociedad y Division; una modificacion posterior en Administracion no cambia la impresion aprobada. Si una cotizacion aprobada antigua no tiene esa copia, el sistema informa que su presentacion historica no esta disponible. No use la plantilla actual para reconstruirla.
