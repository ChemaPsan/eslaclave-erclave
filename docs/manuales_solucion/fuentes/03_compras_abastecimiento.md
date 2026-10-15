# Manual funcional de Compras y Abastecimiento

- Audiencia: solicitantes, aprobadores, compradores, receptores y supervisores
- Alcance por ambiente: Local y QA; las capacidades futuras se indican expresamente; versión funcional QA `e57237f`
- Última revisión: 2026-10-14 (folios CC-18 y contexto documental por División implementados sólo Local; aceptación transversal pendiente)
- Capacidades cubiertas: proveedores, requisiciones multipartida, órdenes, preparación de recepciones, confirmación física por Almacén, aceptación de servicios por el solicitante, conciliación y reportes

## Folios de Compras · CC-18 Local

Al crear un proveedor, requisición, orden de compra o recepción, Administración determina si su folio es administrado o manual. En modo administrado, el folio se asigna al guardar y el campo de edición queda bloqueado después. En modo manual debes capturar un código único. Una falla antes de guardar se puede reintentar con la misma operación y clave sin obtener otro folio para ese intento. Los documentos anteriores conservan su folio original; no se renumeran. Esta capacidad nueva sólo está en Local y todavía requiere aceptación integrada antes de QA.

## Condiciones comerciales de cada División

El recorrido documental por División descrito en este manual está implementado Local. No se ha promovido a QA; la aceptación transversal permanece pendiente. La configuración de proveedores conserva su disponibilidad previamente comprobada.

Revisión: 2026-09-28. Alcance: Local de preparación, sin promoción QA/Producción. Audiencia: responsables del catálogo comercial.

Cada División conserva sus propias condiciones. Debes capturarlas completas aunque sean iguales a las de otra División. Cambiar la ficha general no las actualiza. No existe herencia ni copia automática.

1. Abre **Disponibilidad por División** desde la tarjeta y selecciona una asociación existente mediante **Ver / editar**. Si es nueva, guarda primero la asociación.
2. Abre **Condiciones de esta División**. Si aún no se configuró, verás **Pendiente de configurar** y campos vacíos.
3. Selecciona **Moneda** y **Condiciones de pago** de los catálogos vigentes. Captura el **plazo de entrega en días** explícitamente; cero es válido. El plazo debe ser entero entre 0 y 3650 días.
4. Pulsa **Guardar condiciones** y espera la confirmación. **Recargar datos** vuelve a consultar las condiciones guardadas y reemplaza la captura no guardada.
5. **Volver a asignaciones** permite elegir otra División; sus condiciones son independientes.

Consultar requiere `purchasing.supplier.read`; guardar requiere `purchasing.supplier.update`, alcance autorizado y maestro/asociación activos. Los registros inactivos conservan las condiciones para consulta. Si cambia la Sociedad, confirma primero la asociación y después revisa y vuelve a guardar las condiciones.

Un código histórico no vigente permanece visible, pero debes elegir códigos activos al guardar. Si falla el catálogo, la lectura confirmada sigue disponible y el guardado se bloquea; usa **Recargar datos** cuando se recupere. Los errores conservan captura y señalan los campos afectados. Ante conflicto de revisión, recarga y revisa antes de guardar de nuevo.

Las órdenes nuevas conservan las condiciones del proveedor en su División. Editar una orden con el mismo proveedor mantiene las condiciones guardadas; cambiar expresamente el proveedor toma las condiciones actuales del nuevo proveedor. Guardar un plazo no recalcula fechas prometidas. Este flujo no activa Contabilidad ni exige Centro de costos.

## Disponibilidad por División

Revisión: 2026-09-28. Alcance: entorno Local de preparación; no disponible todavía en QA/Producción. Audiencia: responsables del catálogo de proveedors.

Un proveedor conserva un único maestro y puede estar disponible en varias Divisiones. La Sociedad corresponde a la División seleccionada; no se captura manualmente. Las condiciones comerciales de cada División se capturan explícitamente, sin herencia del maestro. El recorrido Local de requisiciones, órdenes y recepciones consume esa separación. Configurar el proveedor no activa Contabilidad.

Para consultar necesitas permiso `purchasing.supplier.read`, módulo activo y alcance organizacional vigente. Guardar requiere `purchasing.supplier.update` y acceso a la División. Para activar una asociación, el proveedor debe estar activo.

1. Abre **Compras → Proveedores** y pulsa **Disponibilidad por División** en la tarjeta.
2. Busca y selecciona la División por código o nombre. Verifica la Sociedad derivada que muestra la pantalla.
3. Elige **Activa** para habilitar disponibilidad. Pulsa **Guardar asignación** y comprueba la confirmación.
4. Para retirar disponibilidad, abre la asociación existente mediante **Ver / editar**, elige **Inactiva** y guarda. El maestro y su historial se conservan.
5. Usa **Anterior/Siguiente** para recorrer los resultados o las asociaciones existentes.

Ante un conflicto de revisión, vuelve a seleccionar la asociación para cargar su estado confirmado antes de editar. Un rechazo conserva la captura; revisa el mensaje y corrige el campo indicado. Si cambia la Sociedad de una División, vuelve a guardar explícitamente la asociación activa para confirmar su disponibilidad. No se exige Centro de costos en este procedimiento.

## Propósito

Compras controla una necesidad desde la requisición hasta la recepción comercial. Conserva proveedor, autorizaciones, precios y saldos pendientes. Inventario sigue siendo autoridad únicamente cuando una partida representa un artículo físico.

## Corregir errores de captura

**Disponible en Local y QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

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
| Contexto de recepción física y tasa de moneda documental a Sociedad | Disponible sólo Local | No promovido |
| División fija de requisición/orden, condiciones conservadas y recepción heredada | Disponible sólo Local | No promovido |
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

1. Abra **Compras > Requisiciones** y capture folio, fecha, prioridad y motivo. En Local seleccione una División autorizada; revise la Sociedad y moneda base derivadas. La División queda fija al guardar.
2. Agregue una o más partidas. No repita el mismo artículo dentro del documento.
3. Defina tipo, unidad, cantidad y necesidad. Para artículos, escriba en el buscador y seleccione el código y nombre correctos; la unidad procede de Inventario. En espacios estrechos el selector ocupa una fila propia. Al elegir **Servicio**, capture descripción y unidad activa sin artículo ni almacén.
4. Guarde el borrador y corríjalo mientras permanezca editable.
5. Pulse **Enviar**. Un aprobador puede **Aprobar** o **Rechazar** con el permiso puntual.

Una requisición aprobada se convierte completa en una orden. La adjudicación parcial a varios proveedores todavía no forma parte del corte. En Local los artículos se consultan para la División elegida. Una requisición histórica sin contexto permanece de sólo lectura en el formulario; solicite revisión antes de intentar continuarla.

## Crear y emitir una orden

1. Desde una requisición aprobada use **Crear orden de compra**.
2. En Local revise la División heredada y seleccione un proveedor disponible en ella. Moneda, condiciones de pago y plazo proceden de sus condiciones de División y se muestran para consulta. Capture el precio unitario de cada partida. En QA permanece el recorrido base anterior.
3. Revise que tipo, unidad y cantidad coincidan exactamente con la requisición.
4. Guarde el borrador; puede editarlo antes de emitir.
5. Pulse **Emitir orden**. Proveedor, partidas, cantidades y precios quedan congelados. En Local se revalida la elegibilidad sin sustituir las condiciones guardadas.

Editar el borrador manteniendo el proveedor conserva sus condiciones originales. Cambiar explícitamente proveedor carga las condiciones actuales del nuevo proveedor en la misma División. Cambiar la requisición durante una nueva captura limpia proveedor y precios: revise y complete esos datos antes de guardar. La División de un documento guardado no se modifica.

La API admite compras directas con motivo, pero su alta no está expuesta en este formulario. Para una orden directa existente creada por un medio autorizado, la aceptación de servicios corresponde al comprador original. No busque una opción de alta directa que esta pantalla no ofrece.

## Preparar la recepción en Compras

1. Abra **Compras > Recepciones** y seleccione una orden emitida.
2. Capture folio de recepción, documento del proveedor y cantidad por partida.
3. Para una partida inventariable, seleccione el almacén destino.
4. Para un servicio, indique la cantidad preparada para aceptación; no capture almacén.
5. Registre la recepción. Queda **Pendiente de confirmación**: esta acción no aumenta existencias ni acepta servicios.

Las cantidades pendientes ya comprometen el saldo de la orden para impedir una segunda recepción sobre la misma cantidad. Puede preparar recepciones parciales sobre el saldo todavía libre, sin duplicar una recepción que espera confirmación.

### División y moneda del costo en Local

La recepción hereda la División, Sociedad y moneda base conservadas en la orden, también cuando sólo contiene servicios. Para bienes físicos seleccione un almacén de esa misma División; compartir moneda o Sociedad no basta. Confirme que el proveedor esté activo y disponible y que su usuario tenga alcance vigente. No elija Sociedad ni moneda base libremente ni las deduzca de la ficha general del proveedor.

Si la moneda de la orden difiere de la moneda de Sociedad, capture **Tipo de cambio a moneda de la Sociedad** como cantidad de moneda de Sociedad por una unidad de moneda de la orden. Debe ser positivo y admite hasta seis decimales. Si ambas monedas coinciden, la tasa es uno. Todos los almacenes de la recepción deben corresponder a la División heredada de la orden.

Por ejemplo, una unidad comprada por 4.12 USD con tasa de 20.123456 MXN por USD se recibe con costo unitario de 82.908639 MXN. El precio original conserva los dos decimales de la orden; el cálculo conserva seis decimales del costo convertido. No se agregan decimales ni tasas a documentos históricos por suposición.

Al guardar se conservan precio y moneda de la orden, tasa, costo convertido y División de cada línea. Almacén usa esos datos para confirmar la recepción; un reintento no recalcula el costo con una configuración posterior. Si falta moneda confirmada en una recepción histórica, solicite revisión y continúe con el mismo documento cuando se resuelva.

Este recorrido está disponible sólo Local; no habilita Contabilidad ni confirma servicios al preparar la recepción. Los documentos históricos sin contexto no reciben División por suposición: se consultan o cancelan con alcance completo, pero requieren revisión antes de editar o preparar nuevas recepciones. Una recepción ya preparada con contexto auténtico conserva su conciliación y costo original.

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

- **División no autorizada o alcance revocado:** solicite revisar su acceso; reintentar la misma operación no recupera permisos retirados.
- **Condiciones del proveedor pendientes:** configure y confirme la asociación y sus condiciones en la División; la ficha general no las sustituye.
- **Revisión histórica requerida:** conserve el documento sin contexto y pida revisión; no asigne una División por suposición.
- **Almacén de otra División:** seleccione uno de la División conservada en la orden.

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


## Demoras de comunicación en Local

Mejora disponible solo en Local, pendiente de QA: la espera de cada petición incluye la descarga de la respuesta. Un fallo conserva la captura mientras permanezca abierto el formulario; no realiza un nuevo envío automáticamente. Consulte el estado del registro antes de repetir una operación cuyo resultado no se confirmó.

## Documentos relacionados

[Registro de esta fuente y su Word](../REGISTRO.md) · [Ficha funcional](../../../modulos/03_compras_abastecimiento.md) · [Estado por ambiente](../../contexto/ESTADO_ACTUAL.md) · [Control de integración por submódulo](../../contexto/CONTROL_CONTABLE.md).
