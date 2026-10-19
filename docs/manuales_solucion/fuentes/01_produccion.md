# Manual funcional de Producción

- Audiencia: planeadores, supervisores, responsables de etapa y personal de producción
- Alcance por ambiente: Local y QA; las capacidades futuras se indican expresamente
- Última revisión: 2026-10-14 (costo estimado confirmado por División sólo Local; sin promoción QA)
- Versión funcional de referencia: QA `e57237f`
- Capacidades cubiertas: productos y servicios, recetas versionadas, maquinaria, planeación multídía, órdenes, etapas, margen sobre costo sin tope, evidencia de recepción y cierre con adjuntos, entrega previa de materiales, devolución de sobrantes, producto terminado y reportes estándar

## Propósito

Producción define qué se fabrica, con qué receta y recursos, durante qué horizonte y cómo se confirma el avance. El servicio conserva la definición productiva y solicita a otros módulos las validaciones que les pertenecen; nunca modifica directamente Inventario o Recursos Humanos.

## Corregir errores de captura

**Disponible en Local y QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

Los errores de permisos, conexión o reglas generales se muestran como un aviso de la operación. Si no aparece un campo señalado, no cambie datos al azar: revise el aviso y conserve la referencia de correlación para soporte. Corregir un campo no elimina los avisos de los demás. Cerrar el formulario o recargar no garantiza conservar cambios sin guardar.


## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Productos/servicios y recetas versionadas | Disponible | Disponible |
| Margen esperado mayor a 100% | Disponible | Desplegado; aceptación funcional pendiente |
| Evidencia inicial/final de servicios y adjuntos con vencimiento | Disponible | Desplegado; aceptación funcional pendiente |
| Órdenes, etapas y avance ponderado | Disponible | Disponible |
| Reservas y salida de materiales confirmada por Almacén antes del inicio | Disponible | Disponible |
| Devolución de sobrantes de órdenes terminadas o canceladas | Disponible | Disponible |
| Capacidad laboral y de maquinaria multídía | Disponible | Disponible |
| Recepción de producto terminado en Almacenes | Disponible | Disponible |
| Órdenes manuales por División y costos originales confirmados | Implementado; validación Local | No promovido |
| Fabricación originada en pedido por División | Implementado; validación Local | No promovido |
| Costo unitario estimado confirmado por División para cotizaciones | Disponible sólo Local | No promovido |
| Calendarios configurables, turnos, festivos y ausencias | No disponible | No disponible |

## Mapa del módulo

- **Productos y servicios:** catálogo maestro productivo.
- **Recetas:** versiones, recursos, fases, pesos y aprobación.
- **Órdenes:** liberación, planeación y transiciones operativas.
- **Entregables por área:** avance y terminación de fases.
- **Maquinaria:** capacidad, área responsable y estado de mantenimiento.
- **Portada:** reportes estándar de sólo lectura; las altas viven en los submódulos.

## Conceptos principales

| Concepto | Significado |
|---|---|
| Producto/servicio | Resultado que Producción puede fabricar o ejecutar. |
| Receta | Definición controlada de materiales, mano de obra, maquinaria y fases. |
| Versión | Corte inmutable usado por una orden; cambios posteriores no alteran la historia. |
| Peso de fase | Contribución de una fase al avance total; las fases activas suman 100%. |
| Orden liberada | Orden creada después de validar y reservar materiales y capacidad. |
| Días productivos | Horizonte usado para distribuir capacidad de lunes a viernes en el corte actual. |

## Acceso y preparación

Los permisos son granulares. Crear o editar una receta no concede aprobarla; iniciar una orden no concede terminarla; actualizar avance no concede declarar una etapa terminada. Entre los permisos relevantes están `production.recipe.*`, `production.order.*`, `production.order_stage.*` y `production.machine.*`.

Antes de liberar una orden deben existir:

- producto activo y versión de receta aprobada;
- materiales elegibles de Almacenes con unidad activa;
- puestos, áreas y trabajadores productivos vigentes en RH;
- maquinaria activa o disponible para el horizonte;
- permisos y entitlements vigentes para el tenant.

La alta actual de una orden valida, reserva y nace liberada en una sola operación. No existe todavía un borrador separado de la liberación.

## Crear y aprobar una receta

1. Abra **Producción > Recetas** y seleccione el producto o servicio.
2. Capture o reserve el código según la configuración de Administración.
3. Defina cantidad base, unidad, centro de costos y vigencia.
4. Agregue materiales, puestos y maquinaria mediante los buscadores de catálogo.
5. Defina las fases, áreas responsables y su secuencia.
6. Asigne pesos y confirme que las fases activas sumen 100%.
7. Use **Validar definición**, envíe la versión y apruébela con el permiso correspondiente.

**Validar definición** comprueba identidad, unidad y elegibilidad. La disponibilidad real se evalúa al liberar una orden, porque depende de cantidad, fecha y horizonte. Una receta puede ser válida aunque hoy no exista inventario o capacidad suficiente.

## Liberar y ejecutar una orden

1. En Local seleccione explícitamente la División autorizada y después una receta aprobada entre las elegibles. Sociedad y moneda de costo se derivan de esa División. Capture cantidad, inicio planeado, días productivos, fecha requerida, prioridad y responsables de esa División. Cambiar División invalida las selecciones y validación anteriores. En QA se conserva el recorrido base.
2. Revise el horizonte y el desglose diario de material, mano de obra y maquinaria. En Local los materiales deben tener existencias/costos compatibles en almacenes de la División y las tarifas de puesto/máquina deben estar confirmadas en moneda Sociedad. Cero es válido; una tarifa histórica sin moneda no es utilizable.
3. Confirme la liberación. Inventario reserva material y Producción compromete capacidad.
4. Pida a Almacén abrir **Almacenes > Movimientos > Ver solicitudes > Solicitudes de materiales para producción**. El almacenista revisa la orden y confirma **Autorizar y entregar** cuando entrega todos los materiales reservados desde los almacenes indicados.
5. Vuelva a **Producción > Órdenes**. Si la receta corresponde a un servicio, registre la evidencia inicial antes de pasar a espera de recursos o iniciar. Inicie la orden. **En producción** exige la salida completa previamente confirmada y vuelve a validar responsables elegibles y maquinaria disponible. En órdenes Local por División también verifica los trabajadores comprometidos y su puesto vigente; reanudar repite esas verificaciones sin cambiar las tarifas históricas. Cambiar el estatus no descuenta inventario.
6. Actualice cada fase desde **Entregables por área**. El avance general se calcula con sus pesos.
7. En servicios, capture primero la evidencia final en el formulario de avance que completa el total. Cuando todas las fases lleguen a 100%, envíe o deje pasar la orden a **En validación**.
8. Termine la orden. El cierre consolida costos y no vuelve a descontar materiales.

Una pausa, reanudación o regreso desde validación no crea otra salida. Cancelar antes de la entrega libera reservas; cancelar después conserva las salidas físicas, aunque la orden todavía no haya iniciado. Si una entrega quedó incompleta, Almacén debe conciliarla antes de continuar. La regla aplica a productos y servicios ejecutados con receta en Producción; las órdenes comerciales de servicio de Ventas tienen su propio flujo.

Si el resultado de un alta es incierto, conserve la captura y reintente la misma operación; no cambie de clave ni cree otra orden. El intento durable permite comprobar las partidas antes de reservar y recuperar una respuesta ya completada sin repetir efectos. Si una creación fallida dejó reservas, use **Creaciones de orden pendientes de recuperar > Recuperar reservas** antes de crear nuevamente. La recuperación corresponde al usuario que hizo el intento; no cree otra orden para ocultar ese pendiente.

## Fabricar una partida de pedido por División

**Disponible en Local; no promovido a QA.** La solicitud comercial fija el producto, la División, la cantidad y la unidad. Producción conserva la decisión de receta, fechas, responsables y liberación.

1. Abra **Producción > Órdenes > Solicitudes desde pedidos**. Busque la solicitud y use **Anterior/Siguiente** cuando haya más resultados. También puede entrar con **Planificar orden de producción** desde el seguimiento del pedido en Ventas si dispone del permiso de liberación.
2. Pulse **Planificar solicitud**. Revise los datos de origen de sólo lectura; no sustituya una partida comercial mediante una orden manual.
3. Seleccione una receta aprobada del producto solicitado y de la División. Capture inicio planeado, días productivos, fecha requerida, prioridad, responsable general y responsables de etapa. Sociedad y moneda del costo se derivan de la División.
4. Use **Validar recursos**. La validación comprueba el pedido de origen, materiales, capacidad y tarifas confirmadas; no genera una orden por sí sola.
5. Pulse **Generar orden**. La liberación vuelve a validar el origen, reserva materiales y compromete capacidad con el mismo criterio que una orden manual por División. Cada solicitud admite una única orden.
6. Ejecute las etapas, entregue materiales y termine la orden mediante el recorrido habitual. Almacenes debe recibir físicamente el producto terminado.
7. Ventas actualiza el seguimiento y concilia la recepción con el pedido. Terminar Producción no habilita por sí solo el despacho comercial.

Consultar la bandeja requiere `production.order.read`; tener sólo permiso de liberación no habilita esa consulta. Generar la orden requiere `production.order.release` y alcance vigente. Si la solicitud ya tiene orden, consulte la existente. Si se canceló o cambió su origen, actualice el seguimiento antes de continuar. Ante una respuesta incierta conserve la captura y reintente; si se informa recuperación pendiente, resuelva ese intento antes de crear otro o cancelar la solicitud.

## Margen esperado de productos y servicios

**Disponible en Local y QA.** En **Productos y servicios**, el campo **Margen esperado %** expresa utilidad esperada sobre el costo. Permite 0%, 100%, 400% y valores mayores, siempre finitos y no negativos. El porcentaje guardado se conserva al consultar o editar el catálogo.

Un costo de $900 con un precio de $200,000 representa aproximadamente 22,122.22% de utilidad sobre costo: (precio menos costo) dividido entre costo, por 100. Un 400% equivale a vender en cinco veces el costo. Es una referencia de planeación; capturar el porcentaje no cambia automáticamente un precio ni comprueba la utilidad real. Los pesos de fases sí deben seguir sumando 100%.

## Evidencia de recepción y cierre de servicios

**Disponible en Local y QA.** Aplica únicamente a órdenes de Producción cuya receta corresponde a un servicio. Las órdenes de producto mantienen su recorrido. Las órdenes comerciales de servicio de Ventas son un flujo distinto.

### Registrar cómo se recibe o inicia

1. Abra la orden de servicio liberada e intente pasarla a **En espera de recursos** o **En producción**.
2. En el formulario de evidencia inicial, describa cómo se recibió el equipo o cómo comienza el trabajo: condiciones, alcance y observaciones relevantes. El texto obligatorio admite entre 3 y 4,000 caracteres sin contar espacios exteriores.
3. Opcionalmente seleccione hasta tres fotos o archivos que documenten esas condiciones.
4. Guarde y continúe. La evidencia se registra primero; la transición todavía debe cumplir los requisitos de materiales, responsables y permisos.

Si la transición falla después de guardar la evidencia, corrija el requisito pendiente y reintente. No capture otra recepción: la evidencia registrada se conserva y no puede sobrescribirse. Si una orden activa anterior a la mejora aún no tiene recepción, el formulario de avance solicita completarla.

### Registrar cómo termina al completar el avance

1. Abra el formulario donde captura el porcentaje de avance de una etapa.
2. Al llevar la última etapa pendiente a 100% y completar el avance total de la orden, se despliega la sección de evidencia final en ese mismo formulario.
3. Describa el resultado, trabajo realizado y condiciones de entrega; agregue opcionalmente hasta tres adjuntos.
4. Guarde. Sin evidencia inicial y final, el sistema impide completar el avance total, enviar a validación o terminar el servicio.

Completar una etapa intermedia no exige evidencia final si quedan otras etapas pendientes. La evidencia de cierre no sustituye la revisión ni los permisos para terminar la orden. Los registros aceptados se conservan sin edición; no cierre el diálogo ni recargue durante la carga.

### Fotos, archivos y conservación

| Tipo | Límite y tratamiento |
|---|---|
| Fotos JPEG, PNG, WebP, HEIC, HEIF, BMP o TIFF | Hasta 5 MiB y 20 megapíxeles por imagen original; una sola imagen estática. Se optimizan automáticamente a WebP de hasta 300 KiB, con lado máximo de 1,600 píxeles y sin metadatos de ubicación. |
| Documentos PDF, TXT en UTF-8, DOCX o XLSX | Hasta 2 MiB por archivo. No se admiten ejecutables, documentos con macros ni formatos distintos de los indicados. |
| Cantidad | Hasta tres adjuntos opcionales en recepción y tres en cierre. El texto es obligatorio aunque no adjunte archivos. |
| Conservación | Todos los adjuntos, incluidas fotos y documentos, vencen a los 365 días desde su carga. La orden, las descripciones y los datos históricos de los adjuntos permanecen. |

El sistema rechaza una imagen que supera los límites de entrada: reduzca su tamaño y vuelva a seleccionarla. Nunca almacena la foto original; guarde una copia por su cuenta si necesita calidad original. En **Evidencia del servicio** puede consultar ambas descripciones, los adjuntos y su vencimiento. Después de vencer, los archivos dejan de descargarse y se eliminan; el texto sigue disponible. La eliminación física del proveedor puede completarse después del vencimiento, pero la descarga se bloquea desde esa fecha.

Si un archivo es inválido, el mensaje indica la selección que debe revisar. Si falla el almacenamiento, conserve el formulario y reintente cuando soporte resuelva el problema. No dé por guardado un adjunto hasta recibir confirmación.

## Estados de la orden

| Estado | Significado y acciones |
|---|---|
| Liberada | Recursos apartados; Almacén entrega materiales antes de iniciar. Puede esperar recursos o cancelarse conforme al estado de entrega. |
| En espera de recursos | Existe una restricción o conciliación pendiente. |
| En producción | Trabajo activo; Almacén ya confirmó la salida completa de los materiales. |
| Pausada | Detención temporal con causa; puede reanudarse cuando la restricción desaparece. |
| En validación | Las fases terminaron y el resultado espera revisión. |
| Terminada | Cierre operativo; habilita la recepción física en Almacenes. |
| Cancelada | Estado terminal con reservas compensadas cuando corresponda. |

## Maquinaria y Mantenimiento

Una máquina puede pertenecer a una receta aunque no esté disponible hoy. Si Mantenimiento bloquea una máquina, Producción impide usarla y puede pausar la orden relacionada. No se puede retirar ese bloqueo editando el estatus de la máquina. Resolver Mantenimiento libera la máquina, pero nunca reanuda automáticamente Producción: el operador debe volver a validar y decidir. Inicio y reanudación comprueban también la elegibilidad del responsable general y de los responsables de fases pendientes en RH.

## Devolver materiales sobrantes

1. Con la orden **Terminada** o **Cancelada**, abra **Producción > Órdenes > Devolución de materiales sobrantes**.
2. Seleccione el material previamente entregado y pulse **Solicitar devolución**.
3. Capture únicamente el sobrante real y el motivo; no exceda la cantidad entregada pendiente de devolver.
4. Entregue físicamente el material a Almacén. El almacenista confirma desde **Movimientos > Ver solicitudes > Devoluciones de materiales por recibir**.
5. Consulte la devolución vinculada y el costo neto de la orden. La salida original y la cantidad entregada se conservan.

La solicitud no aumenta existencias. Si la entrada ya se registró pero falta confirmar en la orden, Almacén usa **Continuar confirmación pendiente** sobre la misma solicitud.

## Producto terminado

Al terminar una orden, Producción expone a Almacenes una proyección mínima: folio, producto vinculado, cantidad, unidad y costo unitario. En el recorrido Local por División incluye el contexto y costo original exacto a seis decimales; Almacén valida artículo y destino elegibles en esa División y toma el costo del productor. No se captura un costo sustituto ni se infiere del maestro. El almacenista confirma una o varias recepciones. Producción no incrementa existencias por sí misma y no expone receta, responsables o costos completos al rol receptor.

## Mensajes frecuentes

- **Receta aprobada vigente requerida:** seleccione una versión aprobada y activa.
- **Los porcentajes deben sumar 100:** corrija los pesos de fase.
- **Recurso no disponible:** revise existencia, reserva concurrente, trabajador, máquina u horizonte.
- **Capacidad laboral insuficiente:** active trabajadores en el puesto exacto requerido.
- **Unidad de medida no activa:** corrija el artículo o use una unidad vigente; no altere historia con movimientos.
- **Todas las fases deben tener 100%:** regrese a **En producción** y complete las fases pendientes.
- **Maquinaria en mantenimiento:** espere liberación y vuelva a validar la orden.
- **Falta la salida completa de materiales:** Almacén debe usar **Autorizar y entregar** en Movimientos; después vuelva a intentar el cambio en Órdenes.
- **Responsable no elegible:** revise en RH el trabajador y su puesto vigente antes de iniciar o reanudar.
- **Entrega pendiente de conciliación:** Almacén debe reintentar la entrega existente; no registre una salida manual adicional.

## Integraciones y propiedad del dato

- Administración es autoridad de unidades, folios, permisos y entitlements.
- RH es autoridad de áreas, puestos, trabajadores y elegibilidad.
- Inventario es autoridad de artículos, almacenes, existencias, reservas, movimientos y Kardex.
- Mantenimiento solicita bloqueo o liberación; Producción decide la transición válida.
- Ventas puede crear solicitudes de producción, pero no libera una orden automáticamente.

## Reportes estándar de portada

La portada ofrece cinco reportes descargables: productos y servicios, recetas y versiones, órdenes, entregables por área y maquinaria. Abra la tarjeta, capture sólo los filtros necesarios y pulse **Generar**. Puede escribir para encontrar tipo, estatus o prioridad; la búsqueda general acepta texto libre y el periodo usa fechas. Si no hay coincidencias se informa el estado vacío y no se descarga un archivo.

Cada reporte exige el permiso de lectura del recurso: `production.product_service.read`, `production.recipe.read`, `production.order.read` o `production.machine.read`. Estas descargas están disponibles en Local y QA; Reportes conservará los cruces, gráficas, PDF y Excel con formato.

## Limitaciones vigentes

No están disponibles calendario configurable por tenant, turnos, festivos, ausencias, merma recibida, captura obligatoria de eficiencia real ni borrador separado de liberación. Los análisis configurables pertenecen a Reportes.

## Ejemplo de entrega y sobrante

Una orden requiere 10 unidades de material. Al liberarla se apartan las 10, sin reducir la existencia física. Almacén entrega las 10 desde Movimientos y entonces Producción inicia. Al terminar quedan 2 sin usar: Producción solicita devolver 2 y Almacén confirma su recepción. Se conserva la salida original de 10, se registra una entrada de 2 y el costo neto refleja la devolución.

## Soporte y trazabilidad visible

Conserve folio de orden, estado, fase, fecha y referencia de correlación cuando aparezca. No registre salidas manuales para corregir una integración pendiente: reintente desde la acción autorizada o escale a soporte.


## Demoras de comunicación en Local

Mejora disponible solo en Local, pendiente de QA: la espera de cada petición incluye la descarga de la respuesta. Un fallo conserva la captura mientras permanezca abierto el formulario; no realiza un nuevo envío automáticamente. Consulte el estado del registro antes de repetir una operación cuyo resultado no se confirmó.

En órdenes de servicio, un aviso distingue la recepción y el cierre escritos ya guardados del avance pendiente de confirmar. Los campos confirmados quedan bloqueados porque la evidencia no se sobrescribe; un fallo posterior no significa que se hayan perdido esos textos.

## Asignar máquinas y productos a Divisiones

Disponible sólo en Local. Las asignaciones y consultas de máquinas respetan División y preparan el alta manual dimensionada Local. No cambian recetas, órdenes o movimientos históricos. No activa Contabilidad ni análisis de Costos.

En Producción → Productos y servicios o Recursos → Maquinaria, abra **Asignación por División** en la tarjeta. Necesita lectura del catálogo y una sesión con alcance organizacional vigente; para guardar necesita además actualizar ese tipo de recurso.

1. Busque una División por código o nombre y selecciónela entre las autorizadas. Sociedad se deriva de esa División.
2. Para una máquina pendiente, un usuario con alcance completo puede guardar su primera División. Después queda fija; solicite revisión si necesita corregir su ubicación. La máquina debe estar activa.
3. Para un producto o servicio, elija opcionalmente un centro predeterminado activo de esa División. **Sin centro** conserva la asignación sin referencia. Cambiar de División limpia la selección anterior.
4. Guarde. El mismo producto/servicio puede tener asignaciones en varias Divisiones sin duplicar su ficha. Sólo los maestros activos permiten activar asignaciones.
5. En **Asignaciones existentes**, abra una asignación para consultar o cambiar su estado. Desactivarla conserva el centro histórico; reactivarla vuelve a validar el recurso, División y centro.

Los centros no son obligatorios por preparar el sistema. Se exigirán únicamente en los flujos de imputación habilitados. Sin acceso al catálogo, se conserva una referencia existente; para validar una asignación activa con centro necesita acceso y disponibilidad de Costing. Desactivar permite conservar historia aunque ese catálogo no esté disponible.

### Confirmar costo estimado para Ventas en Local

1. En **Productos y servicios > Asignación por División**, guarde y seleccione una asignación activa. Revise la Sociedad y su moneda base; el costo se captura por unidad del producto o servicio en esa moneda.
2. Capture el costo unitario con hasta seis decimales y pulse **Confirmar costo**. Cero es válido. Sólo quien puede actualizar el producto o servicio realiza esta acción; un conflicto de revisión requiere volver a abrir la asignación.
3. Para dejar de usarlo en cotizaciones nuevas, pulse **Retirar costo confirmado**. La acción es explícita y no borra documentos anteriores. Una asignación inactiva no ofrece confirmación nueva.

Ventas utiliza sólo la confirmación de la División correspondiente. Si no existe o cambió la Sociedad o su moneda base, el estimado queda pendiente y Ventas no sustituye automáticamente el costo global del maestro. Este costo es una referencia comercial, no el costo real de una orden ni un asiento contable.

Un rechazo conserva la captura. Si existe un conflicto de revisión, vuelva a abrir la asignación para revisar lo guardado antes de reintentar. La falta de permisos requiere un administrador autorizado. El texto de centro de costos del maestro y el área de la máquina son datos heredados: no se convierten automáticamente a estas referencias. Los registros existentes permanecen pendientes hasta asignarlos explícitamente.

## Confirmar la tarifa de una máquina

Disponible sólo en Local. En **Producción → Recursos → Maquinaria**, abra **Asignación por División**. Necesita consultar la máquina y permiso para actualizarla. La División física se asigna explícitamente y después queda fija.

1. Revise la División y la **Moneda base de la Sociedad** mostrada. La moneda se deriva de esa División y no se elige por separado.
2. Capture **Costo por minuto**; cero es válido y se permiten hasta seis decimales. Revise el importe completo antes de confirmar.
3. Marque **Confirmo este importe en la moneda indicada para operaciones futuras**. La casilla inicia sin marcar; guardar la División por sí solo no confirma la moneda.
4. Guarde la tarifa y espere el resultado. Ante rechazo se conserva la captura; revise moneda, permisos y contexto antes de reintentar.

Una tarifa anterior sin moneda confirmada sigue pendiente: no se convierte ni se etiqueta automáticamente. Si la Sociedad o su moneda cambian, vuelva a confirmar explícitamente antes de usar la tarifa como costo vigente. El editor general de la máquina conserva la tarifa confirmada al cambiar nombre, capacidad u otros datos; para modificar el costo utilice este panel específico. La tarifa no es un asiento contable.

## Consultar capacidad de máquinas por División

En el panel **Asignación por División**, seleccione la fecha y consulte la capacidad. La pantalla muestra hasta 25 máquinas elegibles con su tarifa confirmada y minutos disponibles después de compromisos de ese día. La fecha es obligatoria; el calendario base actual tiene capacidad cero los fines de semana.

La consulta considera la misma máquina física y todos sus compromisos activos del día, incluidas órdenes anteriores sin contexto. No libera ni reserva una máquina. Una máquina inactiva, en mantenimiento o sin tarifa confirmada vigente no debe interpretarse como disponible por conservar su registro histórico.

La consulta de RH, en cambio, presenta capacidad nominal de trabajadores compartidos y no descuenta ocupación productiva. No sume sus minutos entre Divisiones ni los interprete como disponibilidad libre. Las órdenes manuales Local combinan esa identidad compartida con compromisos globales por persona/día y los compromisos de máquinas para calcular disponibilidad. Si hay compromisos laborales antiguos sin personas identificadas, se bloquea el solapamiento para revisión; no se asignan personas por inferencia. Cancelar libera capacidad conforme al ciclo de la orden. El calendario sigue de lunes a viernes. Esta consulta por sí sola no reserva recursos. La fabricación desde pedidos se planifica mediante una solicitud vinculada; su recepción y conciliación comercial son pasos explícitos.

## Documentos relacionados

[Registro de esta fuente y su Word](../REGISTRO.md) · [Ficha funcional](../../../modulos/01_produccion.md) · [Estado por ambiente](../../contexto/ESTADO_ACTUAL.md) · [Control de integración por submódulo](../../contexto/CONTROL_CONTABLE.md).

## Imprimir ordenes con identidad de Division en Local

Al liberar una orden con contexto, Produccion conserva la identidad de Emisor, Sociedad, Division y la plantilla efectiva. La impresion posterior usa esa copia, incluso si Administracion cambia la plantilla. Una orden antigua sin copia de presentacion informa que no puede reconstruir su aspecto historico.
