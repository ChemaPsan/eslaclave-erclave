# Manual funcional de Administración y Backoffice

- Audiencia: administradores del tenant y operadores internos autorizados
- Alcance por ambiente: Local y QA; las capacidades futuras se indican expresamente
- Última revisión: 2026-10-14 (selector de Sociedad y División y folios nuevos sólo Local)
- Versión funcional de referencia: QA e57237f; organización y alcances nuevos sólo en Local
- Capacidades cubiertas: contexto de sesión, organización, usuarios, roles, permisos, módulos, unidades, folios, catálogos, plantilla documental y ciclo de tenants en Backoffice

## Propósito

Administración gobierna quién puede entrar, qué módulos tiene contratados y qué configuración comparte cada tenant. Firebase autentica la identidad; Admin Service decide membresía, tenant activo, permisos, entitlements y alcance.

Backoffice es una aplicación interna separada para alta, configuración, suspensión y eliminación de tenants. Ser owner de una empresa no concede acceso al Backoffice.

## Corregir errores de captura

**Disponible en Local y QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

Los errores de permisos, conexión o reglas generales se muestran como un aviso de la operación. Si no aparece un campo señalado, no cambie datos al azar: revise el aviso y conserve la referencia de correlación para soporte. Corregir un campo no elimina los avisos de los demás. Cerrar el formulario o recargar no garantiza conservar cambios sin guardar.


## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Usuarios, roles y permisos | Disponible | Disponible |
| Entitlements y módulos activos | Disponible | Disponible |
| Unidades, folios y catálogos comerciales | Disponible | Disponible |
| Perfil organizacional | Disponible | Disponible |
| Emisores, Sociedades, Divisiones y alcance por usuario | Disponible | No disponible; conserva entidades legales y sucursales |
| Alta, edición, suspensión y eliminación de tenants | Disponible | Disponible |
| Onboarding automático por checkout/pago | No disponible | No disponible |

## Mapa de Administración

- **Organización:** perfil y, en Local, Emisores, Sociedades y Divisiones. QA conserva entidades legales y sucursales.
- **Usuarios:** invitaciones, estado y membresía.
- **Roles:** definición y matriz de permisos.
- **Módulos activos:** entitlements contratados por tenant.
- **Catálogos base:** unidades, folios, monedas, condiciones, impuestos y otros catálogos implementados.
- **Plantilla documental:** configuración compartida de encabezado, pie y marca.
- **Backoffice:** operación interna sobre tenants.

Administración es la excepción a la portada de reportes: su primera vista es un centro de configuración, no un centro operativo.

## Contexto de sesión y tenant

Al iniciar sesión, ERClave obtiene los tenants donde el usuario tiene membresía. El selector de tenant cambia el contexto completo y obliga a recargar permisos, módulos y datos. El header de tenant es un selector, no una autorización: el backend comprueba que la identidad pertenezca al tenant solicitado.

Un módulo visible requiere tres condiciones: tenant activo, entitlement activo y permiso efectivo. Activar el módulo no concede permisos a roles existentes.

## Usuarios

1. Abra **Administración > Usuarios**.
2. Invite con correo y rol permitidos. En Local una membresía nueva inicia sin Divisiones autorizadas; configure su alcance después.
3. El usuario establece su contraseña mediante Firebase; nunca se envía una contraseña por correo.
4. Actualice rol y estado cuando sea necesario. En Local use el editor de alcance para asignar Divisiones.
5. Use **Deshabilitar** para bloquear acceso conservando evidencia o **Eliminar** cuando corresponda retirar la membresía.

La identidad Firebase sólo se elimina si ya no está compartida con otro tenant. Una respuesta de invitación o limpieza pendiente debe conservarse; el reintento automático durable permanece como mejora futura.

## Sociedades y Divisiones en Local

Una Sociedad agrupa Divisiones y tiene un único Emisor fiscal. Una División identifica la unidad operativa. En **Administración > Organización**, registre primero el Emisor, después la Sociedad y finalmente sus Divisiones. La Sociedad exige Emisor y moneda base; la División exige Sociedad. Use los selectores del catálogo y revise el código y nombre antes de guardar.

Esta estructura y el alcance de sesión están disponibles sólo en Local. La plantilla por alcance y el catálogo básico de Centros de costos ya están disponibles Local. La separación documental es parcial: Ventas, Compras, Mantenimiento y movimientos adaptados de Inventarios tienen recorridos por División; la fabricación comercial conecta solicitud, orden, recepción y conciliación explícitas en Local. La aceptación integrada de esos recorridos sigue pendiente. Cambiar el contexto visible no certifica que todos los documentos estén filtrados por División.

### Cambiar la Sociedad y División activa en Local

1. En la barra superior, pulse **SOCIEDAD / DIVISIÓN**. El botón muestra la Sociedad y División activas.
2. Revise las opciones con nombre y código. Puede buscar por Sociedad, División o código para acortar la lista.
3. Pulse la División deseada. El sistema confirma el alcance con Administración y actualiza el contexto; la marca identifica la opción activa.
4. Si la lista está vacía, solicite a un administrador que revise su acceso a Divisiones. Si el cambio falla, permanece activa la selección anterior.

El menú se cierra con **Escape** o al salir de él. La División elegida se conserva al recargar la sesión del mismo usuario y tenant. El **Centro de costos** no se cambia desde esta barra: es un catálogo y una asignación por División o por documento, según el flujo. Cambiar la División activa no cambia por sí mismo el centro de costos de documentos existentes.

## Folios operativos CC-18 (solo Local)

En Administración, configure por tipo el prefijo, separador, siguiente número y modo administrado o manual. Un operador autorizado ve la secuencia de su documento. En modo administrado, el formulario muestra el folio como asignado automáticamente; en modo manual se captura antes de guardar. Los movimientos generados por otros procesos reciben un código estable del origen si Inventario está en modo manual. Los registros anteriores conservan su código y pueden carecer de modo histórico. La configuración de un tipo no concede permiso para operar otro.

## Asignar acceso a Sociedades y Divisiones en Local

1. Abra **Administración > Usuarios** y seleccione la acción de acceso a Sociedades y Divisiones del usuario.
2. Elija acceso a todas las Divisiones o sólo a las seleccionadas. El acceso total incluye nuevas Divisiones activas; el restringido requiere asignarlas explícitamente.
3. Para restringir, busque una División por código o nombre y revise su Sociedad. Agregue las necesarias o quite las que ya no correspondan.
4. Guarde el alcance. Una selección vacía deja al usuario sin Divisiones autorizadas; conserva los permisos de sus roles.
5. Actualice la sesión del usuario para obtener el alcance vigente. El selector de contexto muestra Sociedad y División; sin opciones no se crea una sucursal «Matriz» automáticamente.

Consultar requiere permiso de lectura de usuarios; guardar requiere actualización de usuarios. Buscar nuevas Divisiones exige lectura del catálogo de Divisiones. Un rol por sí solo no concede acceso a todas ellas.

Si aparece un conflicto por edición simultánea, cierre y reabra el editor para revisar la versión vigente antes de guardar de nuevo. Ante un fallo de conexión, la captura permanece mientras el editor siga abierto. Una División inactiva, ajena al tenant o no autorizada no es válida para seleccionar contexto. Si falla el cambio de contexto, se conserva la selección previamente confirmada.

## Roles y matriz de permisos

1. Abra **Roles** y cree o seleccione un rol.
2. Use **Ver/Editar permisos**.
3. Busque por módulo, recurso o acción.
4. Seleccione exclusivamente las capacidades necesarias y guarde el borrador explícito.

`admin.role.read` permite consultar y `admin.role.permissions.manage` permite reemplazar asignaciones. El sistema rechaza permisos inactivos o grants prohibidos. Las transiciones críticas son independientes: iniciar, completar, cancelar, aprobar, recibir o conciliar no se heredan unas de otras por el nombre del rol.

## Módulos y dependencias

Backoffice y Administración muestran Admin, Producción, Inventario, RH, Ventas, Compras y Mantenimiento como servicios reales del release QA vigente.

- Producción usa RH e Inventario para capacidad y materiales.
- Ventas usa Producción, RH e Inventario según la partida.
- Mantenimiento requiere RH e Inventario; Producción es integración opcional.
- Compras puede activarse sin Inventario cuando sólo se compran servicios; las partidas físicas sí requieren Inventario. Ambas modalidades están disponibles en Local y QA.

No active una dependencia sólo para superar una pantalla: confirme el modelo operativo del tenant y asigne permisos coherentes.

## Unidades de medida

Las unidades tienen código estable, nombre ES/EN, categoría, factor y estado. Los campos operativos guardan el código, no texto libre. La unidad `E48` representa **Unidad de servicio / Service unit** en Local y QA.

Cambiar o inactivar una unidad afecta nuevas capturas, no reescribe documentos históricos. Inventario protege la unidad de artículos con movimientos o reservas.

## Folios y consecutivos

| Campo | Efecto |
|---|---|
| Prefijo | Texto inicial del folio. |
| Separador | Carácter entre prefijo y número. |
| Siguiente número | Próxima reserva; no puede disminuir. |
| Longitud | Dígitos con ceros a la izquierda. |
| Administrado | ERClave reserva de forma atómica e idempotente. |
| Manual | El operador captura y el módulo valida formato/unicidad. |
| Estado | Inactivo impide nuevas asignaciones. |

Abra **Catálogos base > Folios y consecutivos**, edite y guarde. El cambio sólo afecta altas nuevas. Existe el folio `sales.service_order` para órdenes de servicio en Local y QA.

## Permisos para completar los flujos entre áreas

Revise las acciones necesarias en cada rol antes de comenzar las pruebas. El nombre del rol no sustituye los permisos efectivos de la sesión.

- **Almacén:** consultar Movimientos requiere `inventory.movement.read`; confirmar entradas, salidas y tareas físicas requiere `inventory.movement.create`. La confirmación de entrega de refacciones es la autorización operativa de Almacén; no existe un paso adicional de aprobación independiente.
- **Compras:** prepara recepciones con `purchasing.receipt.create`. Tener permiso de conciliación de Compras no autoriza registrar la entrada física. Para servicios comprados se comprueba además que quien acepta sea el solicitante original, o el comprador en una compra directa.
- **Ventas:** prepara entregas con `sales.delivery.create`. El permiso comercial de confirmación por sí solo no sustituye la salida de Almacén. En Cotizaciones, enviar y aprobar requieren `sales.quote.submit` y `sales.quote.approve`, respectivamente.
- **Producción y Mantenimiento:** conservan sus permisos de transición y solicitud; Almacén confirma el material antes del inicio productivo o de la resolución de mantenimiento, según corresponda.

Si falta una acción, revise el permiso puntual en **Roles**, el módulo efectivo y la membresía. Renueve la sesión después del cambio. No conceda todos los permisos ni active módulos adicionales sólo para hacer desaparecer un bloqueo de flujo. QA conserva permisos de Almacén dentro del tenant; en Local, los recorridos dimensionados también validan alcance por División. No hay asignación individual de almacenes por usuario.

## Alta de tenant desde Backoffice

1. Ingrese con un correo interno permitido.
2. Capture nombre comercial, slug, razón social, plan, datos del owner, entidad fiscal y sucursal inicial.
3. Seleccione módulos contratados y revise dependencias.
4. Confirme una sola vez. El alta crea tenant, owner, rol, membresía, entitlements y perfil organizacional.
5. En QA, confirme que Firebase aceptó el correo para que el owner establezca su contraseña; revise spam y recuperación de contraseña.
6. Acceda como owner y confirme tenant, módulos y permisos sin conservar tokens o contraseñas.

## Suspensión reactivación y eliminación

- **Suspender:** bloquea el acceso y conserva configuración.
- **Reactivar:** devuelve acceso cuando el estado y la suscripción lo permiten.
- **Eliminar:** retira configuración administrativa, roles, membresías y entitlements; exige confirmación destructiva.

Después de una eliminación recargue la lista y confirme que el tenant ya no aparezca. La limpieza de datos propiedad de otros servicios debe respetar su ownership y no se sustituye por borrar filas desde Admin.

## Mensajes frecuentes

- **Acceso denegado a Backoffice:** use un correo interno allowlisted; owner no es suficiente.
- **Módulo con dependencias:** revise autoridades requeridas para el flujo real.
- **Permiso no efectivo:** confirme tenant activo, rol, entitlement y sesión renovada.
- **No se puede retroceder la secuencia:** conserve un siguiente número igual o mayor.
- **Secuencia inactiva o no encontrada:** active o configure el tipo documental.
- **Correo no recibido:** revise spam y use recuperación con el correo exacto.
- **Tenant suspendido:** reactívelo antes de probar acceso operativo.

## Limitaciones vigentes

No existe checkout/billing operativo, provisioning service-to-service endurecido, reintento durable de invitaciones/limpiezas Firebase ni sincronización automática con clientes API externos. Gastos, Costos, Reportes avanzados y Contabilidad siguen definidos pero no implementados como servicios operativos.

## Soporte y seguridad

Conserve tenant visible, correo, módulo, rol, acción y referencia de correlación. Nunca comparta tokens, enlaces vigentes de invitación o contraseñas. Para pruebas use sólo datos ficticios y el tenant autorizado para el ambiente.


## Demoras de comunicación en Local

Mejora disponible solo en Local, pendiente de QA: la espera de cada petición incluye la descarga de la respuesta. Un fallo conserva la captura mientras permanezca abierto el formulario; no realiza un nuevo envío automáticamente. Consulte el estado del registro antes de repetir una operación cuyo resultado no se confirmó.


## Preparar una plantilla por Sociedad o División en Local

En **Administración > Organización**, abra Sociedades o Divisiones y use **Plantilla por alcance** en un registro activo. La pantalla indica si hereda de Corporativo/Sociedad o tiene configuración propia. Ajuste colores, pie y numeración; el logo actual se conserva. Guardar crea una plantilla completa para ese alcance. **Volver a heredar** retira el ajuste y muestra la configuración superior vigente.

Consultar requiere lectura de configuración; guardar y restaurar requieren actualización. Un usuario con acceso limitado sólo puede usar sus Divisiones; el ajuste por Sociedad requiere alcance global. Un conflicto pide cerrar y reabrir para revisar la versión vigente; una falla conserva los datos capturados mientras el editor esté abierto.

En Local, este editor define la plantilla por Sociedad o Division. La impresion de cotizaciones con contexto consulta la plantilla e identidad efectivas antes de aprobar y conserva un snapshot al aprobar; la orden de produccion lo conserva al liberar. Cambios posteriores en el editor no modifican esas impresiones historicas. Los demas generadores se integraran por documento. QA no dispone de este recorrido.

## Centros de costos por División — CHG-297 Local

En Organización, abrir Divisiones y elegir Centros de costos en la División correspondiente. Se requiere permiso de lectura de Divisiones y del catálogo. La opción sólo aparece cuando el catálogo básico está disponible.

Escribir el nombre y crear el centro. El sistema asigna el código; la División queda fija. Buscar por nombre/código y filtrar estado. Editar cambia sólo el nombre; desactivar conserva el historial. Una División inactiva no admite altas/reactivaciones. Las acciones dependen de los permisos del usuario. Si falla la solicitud, conservar la captura y reintentar; ante conflicto de revisión, consultar de nuevo antes de editar.

Preparar centros no activa cálculos de Costos ni Contabilidad y no obliga a capturarlos en operaciones sin flujo de imputación habilitado. Las asignaciones a maestros ya existen Local; cada flujo documental debe comprobar su integración. Preparar un centro no implica que todos los documentos lo consuman.

## Documentos relacionados

[Registro de esta fuente y su Word](../REGISTRO.md) · [Ficha funcional](../../../modulos/08_administracion_configuracion.md) · [Estado por ambiente](../../contexto/ESTADO_ACTUAL.md) · [Control de integración por submódulo](../../contexto/CONTROL_CONTABLE.md).
