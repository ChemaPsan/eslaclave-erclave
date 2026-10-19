# Manual funcional de Mantenimiento

- Audiencia: solicitantes, coordinadores, técnicos, almacenistas y verificadores
- Alcance por ambiente: Local y QA; las capacidades futuras se indican expresamente
- Última revisión: 2026-10-14 (folios de órdenes administrados/manuales sólo Local)
- Versión funcional de referencia: QA `e57237f`
- Capacidades cubiertas: mantenimiento correctivo, asignación, tiempos, reserva y entrega de refacciones por Almacén, devolución de sobrantes, bloqueo de maquinaria, conciliación y reportes estándar

## Propósito

Mantenimiento registra una falla desde su reporte hasta el cierre verificado. Puede atender una máquina registrada en Producción o una ubicación/objetivo libre. Conserva orden, asignación, tiempo y solicitudes internas; RH, Producción e Inventario mantienen sus propios datos.

## Corregir errores de captura

**Disponible en Local y QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

Los errores de permisos, conexión o reglas generales se muestran como un aviso de la operación. Si no aparece un campo señalado, no cambie datos al azar: revise el aviso y conserve la referencia de correlación para soporte. Corregir un campo no elimina los avisos de los demás. Cerrar el formulario o recargar no garantiza conservar cambios sin guardar.


## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Órdenes correctivas y asignación | Disponible | Disponible |
| Tiempo, diagnóstico, trabajo y verificación | Disponible | Disponible |
| Refacciones multipardida y conciliación manual | Disponible | Disponible |
| Entrega de refacciones confirmada en Movimientos por Almacén | Disponible | Disponible |
| Devolución de sobrantes con recepción de Almacén | API disponible; acceso en pantalla pendiente de validación | API disponible; acceso en pantalla pendiente de validación |
| Reintento manual de reservas/cancelaciones interrumpidas | Disponible | Disponible |
| Refacciones con División, moneda y prueba del documento de origen | Disponible sólo Local | No promovido |
| Orden con División fija, técnico elegible y costo laboral conservado | Disponible sólo Local | No promovido |
| Folios de órdenes gobernados por Administración | Disponible sólo Local | No promovido |
| Bloqueo/liberación de maquinaria | Disponible | Disponible |
| Preventivos, activos generales y adjuntos | No disponible | No disponible |
| Reintento automático programado | No disponible | No disponible |

## Mapa del módulo

- **Órdenes:** reporte, asignación, ejecución, resolución y cierre.
- **Refacciones:** solicitudes multipardida, reserva, consumo, cancelación y conciliación.
- **Portada:** backlog e indicadores estándar de sólo lectura.

## Acceso y preparación

Solicitar, asignar, iniciar, esperar refacciones, reanudar, resolver, cerrar, reabrir y cancelar usan permisos independientes `maintenance.order.*`. Tiempo y refacciones tienen permisos propios. Un técnico puede registrar tiempo sin autoridad para resolver o cerrar.

### Preparación para operar

1. Cree en RH área, puestos y trabajadores activos con **Interviene en mantenimiento**. En Local confirme la asignación del puesto y trabajador en la División y su tarifa explícita en moneda de Sociedad. Cero es válido; una tarifa sin confirmar bloquea el uso nuevo.
2. Para refacciones, cree en Inventario un almacén activo de tipo **Refacciones** y artículos con unidad vigente.
3. Active Mantenimiento; requiere RH e Inventario. Producción es opcional para instalaciones sin maquinaria productiva.
4. En Local, revise con Administración si la secuencia de **Orden de mantenimiento** está activa y en modo administrado o manual.

## Crear y atender una orden

1. Abra **Mantenimiento > Órdenes** y capture objetivo, prioridad, falla, ubicación y seguridad. En Local, para instalación u otro objetivo elija una División autorizada; revise Sociedad y moneda derivadas. Si el folio está en modo manual, capture el código. En modo administrado, Administración lo asigna al guardar y no se edita en el formulario.
2. Para maquinaria, seleccione la máquina: su División física determina el contexto. Si nace desde Producción, conserve la orden origen y su contexto; la máquina debe coincidir. La División queda fija después de guardar.
3. Guarde el borrador y pulse **Solicitar**. Una falla bloqueante solicita pausar/bloquear en Producción.
4. Seleccione un técnico elegible y pulse **Asignar**. En Local busque por identidad en los resultados de RH para esa División; use la paginación si hace falta. Una asignación a otra División no concede elegibilidad aquí.
5. Pulse **Iniciar**. RH vuelve a validar estado y elegibilidad.
6. Registre tiempo desde la tarjeta. Sólo el responsable asignado puede capturarlo; no se admiten intervalos futuros, invertidos o solapados.
7. Solicite refacciones si son necesarias.
8. Verifique que Almacén haya entregado las refacciones solicitadas, o cancele las solicitudes pendientes que ya no se necesitan. Pulse **Resolver** y capture diagnóstico, causa raíz opcional, trabajo realizado y verificación. Debe existir al menos un registro de tiempo.
9. Cierre cuando materiales y efectos externos estén conciliados.

Resolver libera una máquina, pero no reanuda automáticamente la orden productiva. El operador de Producción debe volver a validar recursos. No retire el bloqueo editando la máquina en Producción. Iniciar, reanudar y reabrir exigen que el técnico siga activo y elegible en RH.

En Local, el folio nuevo proviene de Administración y queda fijo en la orden. Si la respuesta se interrumpe, consulte la lista antes de repetir el alta; un reintento con la misma clave conserva la identidad. Una asignación de folio seguida de un fallo de guardado puede dejar un número sin documento. Los folios anteriores se conservan sin renumerar y no se les atribuye retroactivamente un modo de asignación.

### Tiempo y costo laboral en Local

Antes de guardar tiempo revise la tarifa horaria y moneda que muestra RH. Son de sólo lectura. El sistema conserva puesto, revisiones, tarifa, moneda y costo de esa entrada; cambiar después RH no modifica el costo registrado. Si la tarifa cambió durante la captura, revise la condición actual antes de volver a guardar: sus horas y notas se conservan mientras el formulario permanezca abierto.

En Local, los registros nuevos conservan también el código de puesto informado por RH cuando exista. Los tiempos anteriores mantienen su snapshot original; un código ausente no se completa retrospectivamente.

Las fechas se envían con zona horaria y el servidor las normaliza a UTC. El costo usa la duración exacta en segundos por tarifa horaria, dividido entre 3600, con seis decimales. Por ejemplo, treinta minutos a 120.123456 MXN por hora cuestan 60.061728 MXN. Los minutos mostrados no sustituyen ese cálculo.

No registre intervalos solapados de la misma persona en distintas órdenes de Mantenimiento, ni exceda su capacidad diaria confirmada. El día de control se corta a medianoche UTC; un intervalo que cruza ese límite se distribuye entre ambos días. Este control se comparte entre Divisiones dentro de Mantenimiento, pero no reserva agenda conjunta con Ventas o Producción.

Los documentos históricos sin contexto se consultan con alcance completo y conservan sus recuperaciones permitidas. No permiten nuevas asignaciones, tiempos o solicitudes de refacciones por suponer una División: solicite revisión. La revocación de alcance también bloquea reintentos.

## Estados

| Estado | Significado |
|---|---|
| Borrador | Captura editable sin afectar disponibilidad. |
| Solicitada | Falla reportada; puede iniciar orquestación de bloqueo. |
| Asignada | Responsable principal confirmado por RH. |
| En progreso | Trabajo técnico activo. |
| En espera de refacciones | Trabajo detenido; el bloqueo permanece. |
| Resuelta | Trabajo y verificación terminados; integraciones conciliadas. |
| Cerrada | Cierre administrativo definitivo. |
| Cancelada | Solicitud anulada con compensaciones concluidas. |

Flujo principal: `draft -> requested -> assigned -> in_progress -> resolved -> closed`. Desde ejecución puede pasar a espera y reanudar. Reabrir una orden resuelta regresa a ejecución y vuelve a solicitar el bloqueo aplicable.

## Solicitar refacciones

1. Abra **Refacciones** o use **Solicitar refacciones** desde la orden.
2. Seleccione almacén de tipo Refacciones.
3. Agregue una o varias partidas sin repetir artículos.
4. Confirme la reserva. Inventario valida unidad, existencia y disponibilidad.
5. Pida a Almacén abrir **Almacenes > Movimientos > Ver solicitudes > Solicitudes de refacciones**. El almacenista revisa técnico, almacén y partidas y usa **Autorizar y entregar** cuando entrega físicamente todas las piezas.
6. Actualice la orden y confirme que la entrega quedó registrada. **Resolver** comprueba la entrega o cancelación previa y no vuelve a descontar inventario.

Cancelar una solicitud pendiente libera las reservas activas. Almacén también puede **Rechazar solicitud** antes de comenzar la entrega, indicando el motivo; no genera una salida. Una entrega ya iniciada debe conciliarse y no admite rechazo. Cancelar la orden libera lo reservado cuando corresponda y conserva las salidas físicas ya registradas; los sobrantes se devuelven mediante una solicitud separada.

### Contexto de las refacciones en Local

Seleccione un almacén de la misma División conservada en la orden y artículos disponibles allí. La solicitud hereda Sociedad y moneda de costo; compartir moneda o Sociedad con otro almacén no permite cambiar de División. No cambie el destino para sortear un rechazo.

Inventario comprueba la orden y la partida preparadas antes de reservar o entregar. Una dependencia sin respuesta o un permiso revocado bloquea el paso; conserve la solicitud, corrija la causa y use su conciliación. Repetir la misma confirmación no debe generar otra reserva o salida. Una solicitud histórica sin contexto suficiente requiere revisión y no recibe una División o moneda por suposición.

El contexto de órdenes, técnicos, tiempos y refacciones está implementado sólo Local. No habilita Contabilidad ni acredita la aceptación transversal del módulo o su disponibilidad en QA.

## Devolver refacciones sobrantes

**Pendiente de validación funcional de la pantalla en QA.** El flujo de devolución está implementado en la API, pero la revisión de esta versión detectó que la bandeja de solicitud intenta insertarse en un contenedor que no aparece en la pantalla de Mantenimiento. No se considera disponible el recorrido completo de usuario hasta verificar o corregir ese acceso. Si la opción no aparece, repórtelo a soporte; no registre una entrada manual para sustituir el flujo.

El procedimiento funcional que debe comprobarse, cuando el acceso esté disponible, es el siguiente:

1. Con la orden **Resuelta**, **Cerrada** o **Cancelada**, localice **Devolución de materiales sobrantes** en Mantenimiento.
2. Seleccione una refacción que tenga salida confirmada y pulse **Solicitar devolución**.
3. Capture la cantidad sobrante y el motivo, sin exceder lo entregado pendiente de devolver.
4. Entregue el material a Almacén, que confirma **Movimientos > Ver solicitudes > Devoluciones de materiales por recibir > Confirmar recepción física**.
5. La recepción queda vinculada a la salida y Mantenimiento registra cantidad y costo devueltos sin borrar el consumo original.

Solicitar no aumenta existencias. Si no se hará la devolución, Almacén puede cancelar la solicitud aún pendiente con un motivo; si la entrada ya se registró, corresponde continuar su conciliación.

**Conservación del costo sólo Local:** el sobrante conserva División, Sociedad, moneda y costo de la salida confirmada. No se recostea con el maestro actual ni se cambia su alcance histórico. Si la entrada física ya quedó registrada, continúe la conciliación de la devolución existente, sin solicitar otra ni duplicar la recepción.

## Conciliación

Cuando Producción o Inventario no confirman una operación aparece **Requiere conciliación**, una partida fallida o una operación pendiente. Actualice primero para consultar el estado confirmado y continúe según el paso que falló:

| Pendiente | Quién continúa y dónde |
|---|---|
| Reserva interrumpida o fallida | Mantenimiento, en Órdenes, usa **Reintentar reserva**. Si falta existencia, primero debe resolverse el faltante en el almacén indicado. |
| Cancelación interrumpida | Mantenimiento usa **Reintentar cancelación**; Almacén todavía no puede entregar una reserva sin confirmar. |
| Salida incompleta | Almacén usa **Reintentar entrega** en **Movimientos > Solicitudes de refacciones**. |
| Bloqueo o liberación de maquinaria pendiente | La persona autorizada usa **Conciliar** en la orden de Mantenimiento. |
| Devolución recibida pendiente de registrar en la orden | Almacén usa **Continuar confirmación pendiente** sobre la misma devolución. |

El reintento conserva la operación y sus claves; comprueba lo ya registrado y completa sólo lo pendiente. **Procesando** no significa que Almacén pueda entregar ni que las existencias se hayan perdido. No cree otra solicitud ni registre movimientos manuales para destrabarla. Si vuelve a fallar, conserve folio, estado y correlación para soporte. No existe todavía un reintento automático programado.

## Reglas críticas

- Sólo una orden bloqueante activa por máquina.
- El responsable debe permanecer activo y elegible al iniciar, reanudar y reabrir.
- Resolver exige diagnóstico, trabajo, verificación, tiempo y materiales conciliados.
- Cero refacciones es válido; cero tiempo no.
- Cancelar compensa reservas y bloqueos antes de cambiar a estado terminal.
- Reabrir vuelve a bloquear cuando corresponde.
- Ninguna respuesta incierta se presenta como éxito.

## Mensajes frecuentes

- **No hay técnicos elegibles:** revise trabajador, puesto, área y bandera de mantenimiento.
- **Crea primero un almacén de refacciones:** registre o active uno del tipo correcto.
- **Faltan datos para resolver:** complete diagnóstico, trabajo y verificación.
- **Se requiere al menos un registro de tiempo:** use **Registrar tiempo** o capture el intervalo dentro de Resolver si tiene permiso.
- **Refacciones sin entrega confirmada:** Almacén debe atender **Movimientos > Solicitudes de refacciones**. Si ya no se necesitan, Mantenimiento cancela la solicitud pendiente antes de resolver.
- **Reserva fallida o pendiente:** revise saldo y almacén; use **Reintentar reserva** en Mantenimiento. Almacén entrega sólo después de confirmarse la reserva.
- **La máquina pertenece a otra orden:** localice la orden bloqueante activa.
- **Requiere conciliación:** reintente desde la acción visible con el estado confirmado.

## Integraciones y propiedad del dato

RH valida trabajadores; Producción decide bloqueo/liberación de maquinaria y pausa/reanudación; Inventario decide reservas, salidas, costos y almacenes. Mantenimiento conserva referencias externas con snapshots legibles, sin FKs cruzadas. Compras no se activa automáticamente ante faltantes.

## Reportes estándar de portada

La portada genera reportes descargables de órdenes, indisponibilidad de maquinaria, refacciones y tiempos de mano de obra. Los filtros visibles se limitan a periodo, estatus, prioridad, tipo de objetivo o búsqueda según el reporte. Puede escribir para encontrar las opciones disponibles; abra una tarjeta y pulse **Generar**. Un resultado vacío se informa sin descargar archivo.

Los permisos aplicables son `maintenance.order.read`, `maintenance.material_request.read` y `maintenance.time.read`. Esta capacidad está disponible en Local y QA; MTBF, analítica avanzada y distribución permanecen fuera del corte.

## Limitaciones vigentes

No incluye preventivos calendarizados, activos generales con placa o serie, IoT, garantías, proveedores externos, compras automáticas, participantes secundarios, adjuntos, reintento automático programado ni MTBF confiable sin horas reales de operación.

## Soporte

Ejemplo: el técnico solicita un rodamiento y la reserva falla por falta de disponible. Después de corregir el faltante, Mantenimiento usa **Reintentar reserva** sobre la misma solicitud. Almacén confirma la entrega del rodamiento y registra una salida. El técnico completa tiempo, diagnóstico, trabajo y verificación y resuelve la orden; resolver no crea una segunda salida.

Conserve folio de orden, máquina u objetivo, técnico, estado, solicitud de material y correlación. No fuerce cambios en Producción o Inventario para ocultar un pendiente.


## Demoras de comunicación en Local

Mejora disponible solo en Local, pendiente de QA: la espera de cada petición incluye la descarga de la respuesta. Un fallo conserva la captura mientras permanezca abierto el formulario; no realiza un nuevo envío automáticamente. Consulte el estado del registro antes de repetir una operación cuyo resultado no se confirmó.
