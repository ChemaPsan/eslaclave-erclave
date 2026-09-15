# Guía de pruebas QA del MVP de ERClave

**Ambiente:** QA base publicada y candidato Local pendiente de promoción
**Aplicación cliente:** https://erclave.web.app
**Backoffice interno:** https://erclave.web.app/backoffice/
**Última actualización:** 2026-09-14
**Versión de referencia:** b63cdad2fbac423c24460e55582ccfc0003e9924

**Candidato:** CHG-272–275; SHA de release y run por asignar después de publicar y fusionar. Los casos QA-FORM-*, QA-MARGIN-* y QA-EVID-* requieren la promoción de este candidato. No certificarlos contra la base anterior.

## 1 Objetivo y alcance de la ejecución

Esta guía permite al tester validar la versión desplegada en QA y registrar evidencia reproducible. Los siete servicios y el frontend fueron publicados; eso no significa que estos casos funcionales ya hayan pasado con usuarios reales. Todos los casos comienzan **Sin ejecutar**.

La regla central es separar la preparación del documento de la confirmación física. Compras prepara una recepción, Ventas prepara una entrega y las áreas operativas solicitan materiales. Almacén confirma los bienes que realmente entran o salen. El solicitante acepta los servicios comprados, que no mueven inventario.

## 2 Funciones disponibles

| Área | Estado en QA | Alcance |
|---|---|---|
| Administración y Backoffice | Desplegado | Sesión, organización, usuarios, roles, permisos, módulos, catálogos y ciclo de tenants. |
| Producción | Desplegado | Productos y servicios con receta, recursos, órdenes, salida previa de materiales, etapas y producto terminado. |
| Almacenes | Desplegado | Artículos, reservas, movimientos, confirmaciones, transferencias, devoluciones de materiales y Kardex. |
| Recursos Humanos | Desplegado | Áreas, puestos, trabajadores, capacidad y elegibilidad operativa. |
| Ventas | Desplegado | Clientes, cotizaciones, pedidos, preparación de entregas y órdenes comerciales de servicio. |
| Compras | Desplegado | Proveedores, requisiciones, órdenes, preparación de recepciones y aceptación de servicios. |
| Mantenimiento | Desplegado | Correctivos, técnicos, tiempo, refacciones, recuperación y sobrantes. |
| Reportes estándar por módulo | Desplegado | Descargas de consulta desde las portadas operativas, según permisos. |
| Gastos, Costos, Contabilidad y Reportes avanzados | No operativo | No certificar transacciones de estos módulos futuros. |

No están incluidos lotes, series, merma, nómina, devoluciones comerciales a cliente/proveedor, factura ni cobranza. Tampoco existe conexión automática completa entre cumplimiento productivo de Ventas y entrega, ni consumo de materiales en las órdenes comerciales de servicio de Ventas. Estas últimas son distintas de los servicios con receta de Producción.

## 3 Preparación y responsabilidades

Use datos ficticios identificados con un prefijo de prueba y las cuentas entregadas por el responsable de QA. El tenant autorizado para datos de desarrollo es **ERClave Demo QA**, ID `ten_739ee59d765d5e14818674800d`; confirme el tenant efectivo antes de capturar. Este documento no autoriza crear otros tenants, modificar datos de clientes, ejecutar semillas, migrar ni desplegar.

Los casos de invitaciones, suspensión, eliminación o aislamiento con dos tenants requieren los recursos y el alcance expresamente autorizados. Si faltan, registre **Bloqueado** y el requisito faltante. No copie la base Local a QA ni use la solicitud histórica de refacciones de Local como dato que deba existir en QA.

Prepare un proveedor, cliente, artículos y almacenes de prueba con saldo conocido; un almacén de tipo Refacciones; unidades activas; personal elegible; una receta aprobada con material; y cuentas con los permisos siguientes. Los nombres de responsabilidad no implican que existan roles predefinidos con todos esos permisos.

| Responsabilidad | Acciones necesarias |
|---|---|
| Administrador | Preparar cuentas, módulos y permisos puntuales; no usar privilegios totales para todas las pruebas. |
| Solicitante de Compras | Crear requisición y aceptar sus servicios comprados. |
| Aprobador y comprador | Aprobar requisición, emitir compra y preparar recepción, según permiso. |
| Almacén | Leer Movimientos y confirmar entradas/salidas con permisos de lectura y creación de movimientos. |
| Producción | Liberar, iniciar, pausar, reanudar, validar y terminar con sus permisos propios. |
| Mantenimiento | Solicitar, asignar, registrar tiempo/refacciones, reintentar y resolver según permiso. |
| Ventas y responsable de servicio | Emitir/aprobar cotización, crear pedido, preparar entrega y ejecutar/aceptar servicio según acción. |
| Usuario de lectura | Consultar sin facultad para confirmar movimientos o cambiar estados. |

Para recibir producto terminado también se necesitan `inventory.finished_goods_receipt.read` y `inventory.finished_goods_receipt.receive`; lectura y creación de movimientos no sustituyen estos permisos especializados.

La aceptación de servicios comprados comprueba la identidad del solicitante original; en compras directas corresponde al comprador. Los permisos de almacén son globales dentro del tenant en este corte; la responsabilidad del almacén destino no implica un alcance técnico individual por almacén.

## 4 Prioridad y registro

- **P0:** pérdida o exposición de datos, duplicación de movimientos, acceso indebido o bloqueo de un flujo principal.
- **P1:** comportamiento funcional incorrecto o una operación inaccesible.
- **P2:** defecto visual o de texto con alternativa operativa.

Registre **Sin ejecutar**, **Pasa**, **Falla**, **Bloqueado** o **No aplica** por caso. No marque Pasa sólo porque la pantalla carga. Para mutaciones, recargue y compare documentos, cantidades y Kardex. Cuando se solicite un reintento, use la misma tarea y su acción; no cree un documento sustituto.

## 5 Recorrido inicial

1. Abra QA y haga recarga forzada. Inicie sesión y confirme empresa, sucursal, módulos y permisos.
2. Consulte una pantalla de cada uno de los siete módulos y abra una portada de reportes.
3. Entre a **Almacenes > Movimientos**. Las solicitudes deben aparecer resumidas y cerradas; abra el panel para consultar las tareas.
4. Abra Proveedores y confirme que entra al listado; **Nuevo proveedor** abre el formulario separado.
5. Consulte una cotización en borrador y las acciones disponibles según su permiso.
6. Recargue, cierre sesión y verifique que no queda acceso operativo a datos protegidos.

Este recorrido comprueba acceso básico. Continúe con los casos siguientes para validar los efectos de negocio.

## 6 Backoffice y acceso inicial

### QA-BO-01 Alta e invitación de tenant

**Prioridad/tipo:** P0 · REAL QA
**Contexto:** convierte un cliente vendido en un espacio aislado y operable.

**Pasos**

Precondición: caso condicionado a autorización explícita para crear un tenant desechable y enviar una invitación al buzón acordado. Sin esa autorización, registrar Bloqueado.

1. Entrar a `/backoffice/` con `<EMAIL_BACKOFFICE_ADMIN>`.
2. Crear un tenant con nombre y slug únicos.
3. Capturar owner, razón social inicial y módulos Administración y Producción.
4. Enviar el alta una sola vez.
5. Revisar el resultado y el buzón del owner.

**Esperado**

- Tenant activo y owner invitado.
- Invitación creada sin duplicar la membresía; si el correo falla, se comunica el pendiente y se sigue el procedimiento de recuperación.
- La liga es HTTPS y nunca contiene `localhost`.
- Repetir accidentalmente la acción no duplica el tenant.

**Por qué se prueba:** un alta incompleta impide comenzar; una duplicada afecta cobro, identidad y aislamiento.

### QA-AUTH-01 Activación del owner

**Prioridad/tipo:** P0 · REAL QA

**Pasos**

1. Abrir una invitación nueva en ventana privada o Safari móvil.
2. Definir una contraseña válida.
3. Confirmar que la redirección termina en `https://erclave.web.app`.
4. Iniciar sesión.

**Esperado**

- No aparece “Safari no pudo conectarse al servidor”.
- El usuario entra al tenant recién creado.
- Administración está disponible y no aparecen datos demo de otra empresa.

**Por qué se prueba:** es el primer momento de verdad del cliente.

Use una invitación nueva; no reutilice enlaces vencidos ni los adjunte como evidencia.

### QA-AUTH-02 Recuperación de contraseña

**Prioridad/tipo:** P0 · REAL QA

1. Solicitar recuperación para un usuario existente.
2. Abrir el correo nuevo y establecer otra contraseña.
3. Entrar con la contraseña nueva.
4. Confirmar que la anterior ya no funciona.

**Esperado:** recuperación completa, redirección pública y sesión del tenant correcto.

**Por qué:** evita que el cliente dependa de soporte para recuperar acceso.

### QA-BO-02 Backoffice restringido

**Prioridad/tipo:** P0 · REAL QA

1. Entrar como owner de un cliente.
2. Abrir `/backoffice/`.

**Esperado:** acceso restringido; no se muestran formularios ni datos internos.

**Por qué:** ser owner de un tenant no convierte al usuario en administrador de EsLaClave.

### QA-SEC-01 Suspensión y reactivación

**Prioridad/tipo:** P0 · REAL QA

Precondición: tenant desechable expresamente autorizado para suspensión; no usar el tenant de operación compartida.

1. Con ese tenant, iniciar sesión como owner.
2. Desde Backoffice, suspender el tenant.
3. Refrescar la sesión del owner e intentar operar.
4. Reactivar desde Backoffice y volver a ingresar.

**Esperado:** suspendido no puede operar; reactivado recupera el acceso autorizado.

**Por qué:** permite controlar el servicio sin borrar información.

### QA-SEC-02 Aislamiento entre tenants

**Prioridad/tipo:** P0 · REAL QA

Precondición: dos tenants y sus identidades autorizados expresamente para esta prueba. Sin ellos, registrar Bloqueado; no crearlos ni escribir en otra empresa por iniciativa propia.

1. Abrir `<TENANT_A>` y `<TENANT_B>` en perfiles separados.
2. Crear una razón social y un producto con nombres claramente distintos en cada tenant.
3. Refrescar y consultar Organización, Usuarios, Productos y Recetas.

**Esperado:** ningún tenant ve, busca ni modifica datos del otro.

**Por qué:** una fuga entre clientes es un incidente crítico de seguridad SaaS.

### QA-BO-03 Ciclo de vida del tenant

**Prioridad/tipo:** P1 · REAL QA

1. Buscar por nombre, slug y razón social.
2. Revisar estado y módulos.
3. Probar suspensión/reactivación.
4. Probar eliminación únicamente con un tenant desechable y autorización del responsable.

**Esperado:** búsquedas correctas; estados coherentes; eliminación irreversible claramente comunicada.

**Por qué:** el equipo interno necesita operar clientes sin afectar al tenant equivocado.

## 7 Administración

**Contexto del módulo:** configura la estructura legal y operativa del cliente y controla quién puede entrar y qué puede hacer. Es transversal a todos los módulos.

### QA-ADM-01 Perfil corporativo

**Prioridad/tipo:** P0 · REAL QA

1. Administración > Organización.
2. Completar o editar los datos corporativos.
3. Guardar, refrescar y volver a iniciar sesión.

**Esperado:** datos persistentes sólo en el tenant actual; validaciones claras en campos obligatorios.

**Por qué:** es la identidad administrativa de la empresa.

### QA-ADM-02 Razón social

**Prioridad/tipo:** P1 · REAL QA

1. Crear una razón social con sus datos obligatorios.
2. Editarla y refrescar.
3. Inactivarla y reactivarla.

**Esperado:** mantiene un ID estable, persiste y cambia de estado sin borrado accidental.

**Por qué:** una empresa puede operar con varias entidades fiscales y conservar historia.

### QA-ADM-03 Sucursal

**Prioridad/tipo:** P1 · REAL QA

1. Crear una sucursal ligada a la razón social de prueba.
2. Editar sus datos.
3. Inactivar y reactivar.

**Esperado:** relación y estados persistentes; no permite asociarla a otro tenant.

**Por qué:** sucursales determinan alcance físico y operativo.

### QA-ADM-04 Invitar y activar usuario

**Prioridad/tipo:** P0 · REAL QA

1. Administración > Usuarios y accesos.
2. Invitar un correo nuevo y asignarle un rol.
3. Completar la invitación desde otro perfil.
4. Entrar y revisar las acciones disponibles.

**Esperado:** sólo ve su tenant y permisos; la membresía pasa de invitada a activa.

**Por qué:** permite delegar operación con mínimo privilegio.

### QA-ADM-05 Deshabilitar usuario

**Prioridad/tipo:** P0 · REAL QA

1. Deshabilitar el usuario de prueba.
2. Refrescar su sesión e intentar entrar.
3. Reactivarlo si la interfaz lo permite.

**Esperado:** acceso bloqueado al deshabilitar; sin afectar a otros usuarios.

**Por qué:** el offboarding rápido protege información del cliente.

### QA-ADM-06 Roles y permisos

**Prioridad/tipo:** P0 · REAL QA

1. Crear un rol de prueba.
2. Asignar permiso de lectura, pero no aprobación de recetas.
3. Asignarlo al usuario desechable.
4. Consultar una receta e intentar aprobarla.

**Esperado:** lectura permitida; aprobación ocultada o rechazada por backend.

**Por qué:** la UI ayuda, pero el backend debe impedir acciones sin permiso.

### QA-ADM-07 Editor matricial de permisos

**Prioridad/tipo:** P0 · REAL QA

1. Abrir un rol personalizado y entrar a **Editar permisos**.
2. Buscar por nombre humano y codigo tecnico en ES y EN.
3. Filtrar por asignados/no asignados/cambios y seleccionar/quitar solo resultados visibles.
4. Confirmar que cambiar filtros o idioma conserva el draft completo.
5. Revisar agregados/retirados y guardar una sola vez.
6. Abrir dos sesiones, guardar en la primera y verificar conflicto de revision en la segunda.

**Esperado:** sin plantillas ni autoasignaciones; scopes no modificados se conservan; filtros no borran permisos ocultos; conflicto no pierde el draft.

### QA-SEC-03 Seguridad al delegar permisos

**Prioridad/tipo:** P0 · AUTOMATICA y REAL QA autorizado

- Sin token, tenant o `admin.role.read`, el catalogo se rechaza.
- Un rol tenant no puede recibir `internal.*`, `public.*`, `external.*` ni permisos no asignables.
- No se pueden agregar permisos de modulos inactivos/suspendidos; asignaciones historicas se conservan sin ser efectivas.
- Mezclar un ID valido y uno prohibido rechaza todo sin cambios.
- `admin.role.update` sin `admin.role.permissions.manage` no permite modificar grants.
- Reintento con misma clave/payload reproduce resultado; misma clave con otro payload devuelve conflicto.

## 8 Producción

**Contexto del módulo:** define productos/servicios, recetas versionadas, maquinaria y órdenes persistidas. Consultar disponibilidad no reserva. Liberar una orden compromete recursos y reserva materiales; Almacén debe confirmar su salida antes de iniciar la ejecución.

### QA-PROD-01 Crear producto o servicio

**Prioridad/tipo:** P0 · REAL QA

1. Producción > Productos y servicios.
2. Crear un registro con código/SKU único, nombre, tipo y unidad.
3. Guardar, refrescar y abrir en otro navegador.
4. Editar e inactivar/restaurar si está disponible.

**Esperado:** persiste en API/QA, conserva ID y muestra estados correctos.

**Por qué:** el catálogo es la base de recetas y futuras ventas/órdenes.

### QA-PROD-02 Validaciones del catálogo

**Prioridad/tipo:** P1 · REAL QA

1. Omitir campos obligatorios.
2. Probar espacios, longitudes límite y un SKU repetido.
3. Corregir el formulario y guardar.

**Esperado:** mensajes comprensibles, sin registros incompletos o duplicados.

**Por qué:** datos maestros inconsistentes contaminan todos los flujos posteriores.

### QA-PROD-03 Crear y editar receta

**Prioridad/tipo:** P0 · REAL QA

1. Seleccionar un producto existente.
2. Crear receta y versión borrador.
3. Agregar recursos y al menos una etapa activa.
4. Capturar cantidades, unidades, merma/rendimiento disponibles.
5. Guardar, refrescar y volver a abrir.

**Esperado:** receta borrador persistente, recursos y etapas íntegros.

**Por qué:** la receta estandariza qué se necesita y cómo se produce.

### QA-PROD-04 Aprobación y versionado

**Prioridad/tipo:** P0 · REAL QA

1. Enviar el borrador a aprobación.
2. Aprobar con usuario autorizado.
3. Intentar modificar directamente la versión aprobada.
4. Editar desde el flujo permitido y comprobar la nueva versión.

**Esperado:** transición `draft → pending_approval → approved`; la versión aprobada es inmutable y la edición crea una nueva versión.

**Por qué:** cambiar una receta histórica alteraría costos y explicaciones de futuras operaciones.

### QA-PROD-05 Reglas negativas de receta

**Prioridad/tipo:** P1 · REAL QA

- Intentar aprobar sin etapas activas.
- Intentar aprobar sin recursos cuando la UI/regla lo exija.
- Hacer doble clic en Guardar/Enviar/Aprobar.
- Repetir una acción después de refrescar.
- Intentar aprobar sin permiso.

**Esperado:** acciones inválidas rechazadas; ningún duplicado; mensajes accionables.

**Por qué:** protege integridad, autorización e idempotencia.

### QA-PROD-06 Materiales antes de iniciar

**P0.** Con receta aprobada, responsable elegible, almacén con saldo y material de prueba, libere una orden. Registre existencia física, reserva y disponible antes/después. Intente iniciar sin entrega.

**Esperado:** se reserva material, pero no se registra salida al liberar. El inicio se bloquea con indicación de que Almacén debe entregar en Movimientos. El selector conserva el estado confirmado.

Abra **Almacenes > Movimientos > Ver solicitudes > Solicitudes de materiales para producción**, localice la orden y confirme su entrega completa. Vuelva a Producción e inicie, pause y reanude.

**Esperado:** una salida por partida, costo vinculado y reserva consumida; iniciar o reanudar no crea otra salida. Repita también con un servicio con receta de Producción. La entrega parcial de estas solicitudes no está implementada.

### QA-PROD-07 Responsable y máquina vigentes

**P0.** Con una orden lista para iniciar o reanudar, use un expediente de prueba y haga que RH lo inhabilite, o genere un bloqueo real de mantenimiento sobre la máquina de prueba. Intente la transición.

**Esperado:** se bloquea con causa, responsable y paso para resolver; conserva el estado anterior. Restablezca la elegibilidad por RH o resuelva el mantenimiento por su flujo, y reintente. No se puede quitar manualmente el bloqueo de mantenimiento desde Maquinaria. Liberar la máquina no reanuda automáticamente Producción.

### QA-PROD-08 Terminar y recibir producto terminado

**P0.** Registre avances y consumos reales permitidos; intente terminar antes de completar los requisitos de fases. Complete el flujo de validación y termine la orden con un producto terminado vinculado.

**Esperado:** terminar prematuramente informa el requisito pendiente. La orden terminada aparece en **Entradas de producción terminada** de Movimientos. Reciba una cantidad parcial válida y luego el saldo. No puede recibirse más de lo producido. El producto terminado sólo aumenta al confirmar la recepción de Almacén.

### QA-PROD-09 Cancelación y recuperación

**P0.** Cancele una orden de prueba antes de la entrega y otra después de una entrega válida. Si una creación muestra recuperación pendiente, continúe desde esa recuperación sin repetir el alta.

**Esperado:** las reservas activas se liberan; las salidas ya realizadas se conservan. Los materiales físicamente sobrantes se devuelven por el caso QA-INV-09. Una recuperación libera sólo el intento fallido sin duplicar órdenes ni reservas. Para fallos inducidos, use exclusivamente un entorno de pruebas controlado; no interrumpa servicios compartidos de QA.

## 9 Almacenes y confirmaciones físicas

### QA-INV-01 Maestros y saldos

**P0.** Cree o use un almacén y artículo de prueba con unidad activa. Busque por código/nombre y recargue. Registre una entrada manual justificada y una salida válida; intente superar el disponible.

**Esperado:** maestros y movimientos persisten; existencia, reserva y disponible se distinguen. El faltante se bloquea sin saldo negativo ni movimiento parcial oculto. No modifique una unidad con historia para corregir una captura.

### QA-INV-02 Solicitudes compactas

**P1.** Abra Movimientos con tareas pendientes y sin ellas; expanda/contraiga el resumen con mouse y teclado. Recargue una bandeja y navegue por sus páginas.

**Esperado:** panel inicialmente cerrado antes del historial, aviso cuando hay pendientes y detalle accesible al abrir. No se presenta el número de una página como total global. Carga o error no deben decir que no hay pendientes. Un fallo de actualización conserva la posibilidad de reintentar.

### QA-INV-03 Recepción de bienes comprados

**P0.** Use la recepción preparada en QA-BUY-03. Confirme desde **Recepciones de compras pendientes** en Movimientos. Recargue Compras, Inventario y Kardex y repita la misma tarea si queda conciliación pendiente.

**Esperado:** la preparación no suma stock; la confirmación de Almacén registra una entrada por partida física y actualiza la recepción comercial. Un reintento no duplica las entradas ya confirmadas. Servicios de una recepción mixta permanecen pendientes de su solicitante.

### QA-INV-04 Salida de un pedido de venta

**P0.** Use una entrega preparada en QA-SALES-04. Desde **Salidas de pedidos de venta**, confirme la salida y vuelva al pedido.

**Esperado:** Ventas no consumió stock al preparar. Almacén registra la salida física y la entrega queda reflejada comercialmente. Repetir una confirmación no duplica la salida ni la cantidad entregada.

### QA-INV-05 Consulta de reservas y Kardex

**P1.** Consulte las reservas de una orden liberada; compare saldo antes de entrega, después de entrega y después de una devolución. Filtre por artículo/almacén y recargue.

**Esperado:** reservar reduce disponible sin reducir existencia; entregar convierte lo reservado en salida; devolver conserva la salida y añade una entrada trazable. El historial no se reemplaza por el último saldo.

### QA-INV-06 Permiso de consulta

**P0.** Con una cuenta de lectura, abra las bandejas y trate de confirmar una tarea. Con apoyo técnico autorizado, compruebe el rechazo del comando sin permiso.

**Esperado:** puede consultar lo autorizado, pero no dar entrada/salida. El backend rechaza aunque se invoque directamente. Tener permisos comerciales de confirmación o conciliación no sustituye `inventory.movement.create`.

### QA-INV-07 Transferencia parcial

**P0.** Transfiera 5 unidades entre dos almacenes de prueba del mismo tenant. Anote ambos saldos. En **Transferencias en tránsito**, el responsable de destino confirma primero 2 y después 3.

**Esperado:** al enviar, origen baja 5 y destino aún no aumenta; al recibir 2, destino aumenta 2 y quedan 3 en tránsito; al completar, aumenta sólo el saldo. No puede confirmarse más del pendiente ni duplicarse una recepción al reintentar.

### QA-INV-08 Rechazo y retorno de transferencia

**P0.** En otra transferencia de 5, reciba 2 y rechace las 3 restantes con motivo. Después, el origen confirma la recepción física de esas 3 devueltas.

**Esperado:** el rechazo no devuelve existencia automáticamente a origen. La entrada de retorno se registra cuando éste recibe. Destino conserva únicamente las 2 recibidas y el historial permite seguir salida, recepción y retorno.

### QA-INV-09 Devolución de sobrantes

**Incidencia conocida por revisión de código:** la bandeja para iniciar devoluciones desde Mantenimiento apunta a un contenedor ausente en su render. Verifique ese acceso primero. Si no aparece, registre la incidencia y marque la variante Mantenimiento Bloqueado; continúe la variante Producción. La API implementada no demuestra que el acceso desde pantalla esté disponible.

**P0.** Con una orden de Producción terminada/cancelada o de Mantenimiento en estado final admitido y material ya emitido, solicite devolver una cantidad menor o igual al saldo retornable. Abra **Devoluciones de materiales por recibir** y confirme en Almacén.

**Esperado:** solicitar no aumenta existencia. Recibir crea la entrada y ajusta una sola vez el costo en el módulo dueño. La salida original permanece. Si queda conciliación, continúe la misma tarea. Rechace exceso sobre lo emitido menos devoluciones vigentes; cancelar una solicitud antes de recibir no mueve stock. Este caso no corresponde a devoluciones comerciales a proveedores o clientes.

### QA-INV-10 Reversa y documentos vinculados

**P0.** Revierta un movimiento manual reversible de prueba y trate de revertir genéricamente una salida vinculada a un flujo operativo.

**Esperado:** el manual conserva original y compensación con saldo correcto. El vinculado exige su flujo propio y no permite ocultar la historia. La recepción de producto terminado conserva su reversa controlada cuando existe saldo disponible.

## 10 Compras y abastecimiento

### QA-BUY-01 Proveedores y requisición legible

**P1.** Abra Proveedores, busque uno existente y pulse **Nuevo proveedor**; cancele y vuelva a abrir. Cree una requisición con varias partidas y busque artículos de nombre largo en pantalla amplia y estrecha.

**Esperado:** la entrada es un listado, la captura ocurre en modal y cancelar no crea registro. El buscador muestra identidad/unidad sin dividir palabras letra por letra ni desbordar. Las partidas físicas obtienen la unidad del artículo; las de servicio usan descripción y unidad activa pertinente; no admiten artículo ni almacén.

### QA-BUY-02 Envío y autorización

**P0.** Cree un borrador, envíelo, apruébelo con permiso y conviértalo a orden de compra. Intente convertir un borrador sin aprobar y repita la conversión de la requisición aprobada.

**Esperado:** se exige el paso de autorización; convertir conserva el origen sin duplicar la compra. Rechazar/cancelar exige la acción y el estado permitidos. Emitir la orden requiere sus datos y permiso; el solicitante no adquiere autorización por haber creado la requisición.

### QA-BUY-03 Preparar recepción mixta

**P0.** Emita una compra con una partida física y otra de servicio. En Recepciones prepare cantidades válidas; asigne almacén sólo al bien. Anote cantidades pendientes y stock.

**Esperado:** la recepción queda pendiente de confirmación, sin entrada física ni servicio aceptado. Cantidades en recepciones pendientes cuentan para evitar sobre-recepción. Continúe el bien en QA-INV-03 y el servicio en QA-BUY-04.

### QA-BUY-04 Aceptación por solicitante

**P0.** Con un usuario distinto al solicitante original, intente aceptar el servicio preparado. Después entre como solicitante y abra **Servicios comprados por aceptar** en Compras; acepte tras verificar que el servicio fue recibido satisfactoriamente.

**Esperado:** otro usuario no puede aceptar sólo por tener permiso de compras. El solicitante original con permiso completa la partida sin entrada a Inventario. Para la variante de compra directa use una orden ya preparada por un medio autorizado: acepta el comprador que la creó. El alta directa no está expuesta en el formulario actual; si falta la orden de prueba, marque esa variante Bloqueado. La recepción mixta se completa cuando bienes y servicios están confirmados por sus responsables.

### QA-BUY-05 Servicios sin Inventario

**P1.** En un contexto expresamente preparado para sólo servicios, cree requisición y compra de servicio con unidad vigente. No cambie módulos de un tenant compartido para improvisar esta precondición.

**Esperado:** se permite el ciclo de servicio sin artículo ni almacén y sin movimientos físicos. Si no existe contexto autorizado, marque Bloqueado. Las partidas físicas siguen requiriendo Inventario.

## 11 Ventas y servicios comerciales

### QA-SALES-01 Cliente y cotización

**P1.** Cree o use un cliente de prueba, genere cotización de varias líneas con descuentos y vigencia, guarde y recargue.

**Esperado:** cliente, líneas, condiciones y totales persisten; la cotización comienza en borrador. El PDF disponible debe coincidir con esos datos sin considerarse factura fiscal.

### QA-SALES-02 Emitir y aprobar cotización

**P0.** En Cotizaciones, con permisos puntuales, abra las acciones del borrador y use **Emitir cotización**; después **Aprobar**. Pruebe con una cuenta sin permiso de emisión/aprobación.

**Esperado:** Borrador pasa a Cotizada y luego Aprobada. Los botones o la ayuda indican el siguiente paso y el permiso que falta; editar no aprueba implícitamente. Una cotización aprobada se convierte una sola vez a pedido. Expirar o cancelar sólo debe permitirse según estado y permiso.

### QA-SALES-03 Estrategia de cumplimiento

**P0.** Convierta la cotización aprobada a pedido y configure una partida física para surtir desde existencia con saldo suficiente. Consulte su reserva y recargue.

**Esperado:** conserva origen, cliente, cantidades y estrategia; no registra salida hasta Almacén. Si una partida se manda a Producción, no suponga una conexión automática completa con entrega: documente el alcance mostrado y siga el manual de Ventas.

### QA-SALES-04 Preparar entrega

**P0.** Prepare una entrega válida sobre el pedido reservado. Con un usuario comercial sin permiso de movimiento revise que no se ofrece la confirmación física y que se indica continuar con Almacén. Con apoyo técnico autorizado, compruebe además el rechazo del comando comercial sin ese permiso.

**Esperado:** la preparación conserva el stock físico; la confirmación comercial sola informa continuar con Almacén. Complete QA-INV-04. No exceda el saldo entregable ni cancele una entrega confirmada para simular devolución.

### QA-SALES-05 Orden comercial de servicio

**P0.** Desde una partida de servicio genere su orden comercial, planifique, asigne responsable RH elegible e inicie. Envíe a aceptación e intente aceptar sin evidencia y sin registros de tiempo o costo: debe rechazarse. Registre después la evidencia requerida y al menos un registro de tiempo o de costo permitido, y acepte con permiso.

**Esperado:** los pasos válidos llevan de borrador a planeada, asignada, en curso, pendiente de aceptación y aceptada. Iniciar/reanudar revalida al responsable. Un salto inválido muestra el requisito y conserva estado. El servicio no genera movimientos ni solicita materiales de receta; la aceptación registra su cumplimiento comercial.

## 12 Mantenimiento

### QA-MTO-01 Correctivo y máquina

**P0.** Cree una orden correctiva de prueba, solicítela, asigne técnico elegible e inicie. Si se vincula a máquina, revise el efecto sobre su disponibilidad y la orden productiva relacionada.

**Esperado:** permisos y transiciones se respetan; el bloqueo pertenece al mantenimiento y no puede quitarse desde edición manual de máquina. El técnico no elegible bloquea inicio/reanudación.

### QA-MTO-02 Solicitar y entregar refacciones

**P0.** Desde Mantenimiento solicite varias refacciones de un almacén de ese tipo y con saldo. Abra **Solicitudes de refacciones** en Movimientos; confirme la entrega completa como Almacén. Registre tiempo y resolución técnica antes de resolver la orden.

**Esperado:** solicitar reserva; Almacén autoriza la entrega y registra las salidas. Resolver no vuelve a consumir. Una solicitud sin entregar impide resolver con explicación de quién debe actuar. Una orden sin refacciones puede resolverse si cumple los demás requisitos, incluido tiempo válido.

### QA-MTO-03 Rechazo y cancelación de solicitud

**P1.** Rechace desde Almacén una solicitud pendiente con motivo y pruebe cancelación de otra desde Mantenimiento con permiso.

**Esperado:** libera las reservas que sigan activas y conserva motivo/historia; no genera salida. No se permite cancelar como si no se hubiera entregado una solicitud ya emitida. Use devolución de sobrantes cuando corresponda.

### QA-MTO-04 Recuperación de reserva interrumpida

**P0.** Si hay una solicitud de prueba fallida o Procesando con reserva pendiente, consulte sus partidas en Mantenimiento y use el reintento permitido después de resolver el faltante o la disponibilidad de la dependencia. Use una interrupción inducida sólo en entorno controlado, nunca apagando QA compartido.

**Esperado:** conserva la solicitud y sus claves; no duplica reservas ni crea una salida. Una vez reservada, Almacén puede entregar. Si lo pendiente es la emisión física, la conciliación corresponde a Almacén en Movimientos. Registre Bloqueado si no hay una precondición controlada para este caso; no use datos de otros usuarios.

### QA-MTO-05 Resolver cerrar y devolver

La parte de devolución desde Mantenimiento depende de la verificación de acceso indicada en QA-INV-09; no use una entrada manual como sustituto.

**P0.** Con tiempo válido, refacciones entregadas y solución técnica, resuelva y cierre con los permisos correspondientes. Intente cerrar mientras haya una conciliación pendiente. Si hay sobrantes en una orden final admitida, ejecute QA-INV-09.

**Esperado:** no cierra con dependencias pendientes; resolver libera la máquina cuando la integración se confirma, sin reanudar automáticamente Producción. La devolución conserva la salida y reduce el costo neto una sola vez.

## 13 Recursos Humanos

### QA-HR-01 Estructura y expediente

**P0.** Cree área, puesto y trabajador ficticios con datos de prueba válidos y permisos separados. Busque por identidad visible, edite y recargue. Pruebe un identificador duplicado o un puesto inactivo.

**Esperado:** el área no se captura como texto libre al crear puesto; el trabajador conserva un puesto vigente. Se validan formato y unicidad sin repetir datos personales en errores. La capacidad usa trabajadores activos y minutos configurados, no una cantidad manual de plazas.

### QA-HR-02 Elegibilidad y capacidad

**P0.** Active las banderas del puesto que correspondan, verifique sus trabajadores en Producción y Mantenimiento y consulte responsables de servicio en Ventas. Inactive sólo un expediente de prueba previamente acordado e intente reanudar su orden.

**Esperado:** trabajador, puesto y área deben estar activos y cumplir la elegibilidad del propósito. La reanudación vuelve a comprobarla; los nombres históricos no sustituyen esa validación. RH no reescribe órdenes al cambiar un maestro.

## 14 Regresión transversal

### QA-REPORT-01 Reportes por módulo

**P1.** En las seis portadas operativas abra reportes, filtre y descargue con permiso; pruebe un filtro sin coincidencias y un usuario sin lectura.

**Esperado:** filtros y columnas corresponden al módulo, datos del tenant y resultados de consulta. No se genera un archivo vacío como si tuviera información. RH excluye identificadores personales; Administración mantiene su centro de configuración. Reportes avanzados sigue fuera del alcance operativo.

### QA-RESP-01 Checklist responsive transversal

**P1.** Pruebe escritorio, ancho intermedio y móvil de 390 px, además de zoom 200%, en español e inglés. Abra/cierre menú y panel lateral; use teclado para modales y buscadores.

**Esperado:** sin scroll horizontal de página ni texto partido letra por letra; el ancho real del panel manda. Revise especialmente riel de Órdenes, listado/modal de Proveedores, partidas y buscador de Requisiciones, acciones de Cotizaciones, solicitudes colapsadas y reportes. Foco visible, etiquetas completas, cierre y acciones alcanzables; objetivos táctiles al menos 44 px o área equivalente. Una tabla con scroll debe conservarlo dentro de su contenedor.

### QA-ERR-01 Mensajes y estados confirmados

**P1.** Intente iniciar sin materiales, resolver sin entrega, aprobar sin permiso, recibir de más y reanudar con responsable inválido. Simule pérdida de conexión en el navegador de prueba y recupérela.

**Esperado:** mensaje claro sobre requisito, responsable y pantalla, sin claves crudas ni error técnico del backend. Mantiene/restaura el estado confirmado, no pierde el formulario innecesariamente y permite reintentar cuando procede. No hay spinner infinito ni aviso de éxito ante fallo.

### QA-IDEM-01 Reintentos y concurrencia

**P0.** En documentos de prueba haga doble clic, recargue después de confirmar y consulte el mismo documento desde dos sesiones autorizadas. Si el equipo técnico prueba claves de idempotencia, debe reutilizar la misma clave sólo para la misma operación/payload.

**Esperado:** una operación efectiva y un historial coherente; los conflictos de revisión o clave se comunican sin sobrescribir silenciosamente ni duplicar reserva, entrada, salida, devolución o costo.

### QA-NAV-01 Sesión idioma y navegación

**P1.** Navegue atrás/adelante, cambie idioma, recargue, cambie contexto autorizado y cierre sesión.

**Esperado:** etiquetas y estados ES/EN completos, datos capturados sin traducción automática, permisos y datos del contexto vigente, ningún acceso operativo después de cerrar sesión.

## 15 Validación del candidato pendiente de promoción

Los casos siguientes comienzan **Sin ejecutar**. Primero confirmar SHA candidato, migraciones y almacenamiento mediante el plan de release.

### QA-FORM-01 Campos y filas en conflicto

**P0.** En cada módulo y Backoffice intente guardar con un campo requerido vacío y un valor inválido. Incluya un buscador de catálogo y una partida.

**Esperado:** Mensaje específico junto al control visible, resumen que lleva al campo, captura conservada y foco accesible. Corregir un campo no borra los demás errores. Registrar módulo y formulario por variante.

### QA-FORM-02 Errores generales y respuesta tardía

**P1.** Pruebe permiso faltante, pérdida de conexión y un rechazo sin campo reconocido. Con apoyo técnico simule una respuesta tardía después de editar la captura.

**Esperado:** Aviso útil sin texto técnico crudo; no promete campos marcados si no existen. Una respuesta anterior no marca campos de la captura nueva. Revise español, inglés, teclado, móvil y tema oscuro.

### QA-MARGIN-01 Margen mayor a 100%

**P0.** Cree o edite producto y servicio de prueba con 400 y 22122.22; guarde, recargue y vuelva a editar. Intente un negativo.

**Esperado:** Persiste el porcentaje sobre costo sin límite de 100; rechaza negativos y valores no finitos. Los pesos de la receta siguen sujetos a sumar 100%.

### QA-EVID-01 Recepción antes de espera o inicio

**P0.** Con una receta de servicio y orden liberada, intente esperar recursos o iniciar sin descripción. Capture luego condiciones iniciales y guarde.

**Esperado:** Bloqueo sin texto de 3–4000 caracteres. Evidencia guardada antes de la transición; las reglas de materiales y recursos siguen vigentes. Reintentar no duplica ni sobrescribe evidencia.

### QA-EVID-02 Cierre en el formulario de avance

**P0.** Avance una etapa intermedia y después la última pendiente al 100%. Pruebe también una orden de servicio activa anterior sin evidencia.

**Esperado:** El cierre se solicita en el mismo formulario al completar el total. Exige recepción y cierre antes de 100% total, validación y terminación. La etapa intermedia no exige cierre si quedan otras pendientes.

### QA-EVID-03 Optimización y límites

**P0.** Suba una foto de cada formato permitido, con orientación y metadatos, y documentos PDF/TXT/DOCX/XLSX. Pruebe más de tres adjuntos por momento, foto mayor de 5 MiB/20 MP, documento mayor de 2 MiB y formato no admitido.

**Esperado:** Fotos guardadas como WebP de hasta 300 KiB y lado máximo 1600, orientadas y sin ubicación; no se almacena original. Rechazo claro por selección inválida, captura conservada. Puede guardar solo texto. Verificación de bytes requiere apoyo técnico.

### QA-EVID-04 Consulta privada y permisos

**P0.** Consulte evidencia después de recargar y descargue con usuario lector autorizado. Pruebe sin sesión, sin permiso y con un ID ajeno a la orden; aislamiento entre tenants solo con recursos autorizados.

**Esperado:** Texto y archivos persistidos, nombre de descarga correcto, permisos efectivos; ninguna descarga pública. Rechazo no revela evidencia de otra orden o tenant.

### QA-EVID-05 Caducidad de todos los adjuntos

**P0.** Equipo técnico: en fixtures Local con reloj/fecha controlados verifique antes y al vencer 365 días. En QA inspeccione política del bucket y smoke con adjuntos desechables autorizados; no envejezca evidencia operativa.

**Esperado:** Desde vencimiento la descarga devuelve 410. Limpieza elimina bytes de fotos y documentos y conserva orden/texto/metadatos. Bucket sin versiones, soft delete, holds o retención adicional; lifecycle Delete age 365. No marcar el borrado anual real QA como observado por una simulación Local.

### QA-EVID-06 Productos y reintentos

**P0.** Complete una orden de producto y una de servicio. En el servicio simule fallo después de guardar recepción y antes de la transición; vuelva a intentar.

**Esperado:** Producto no solicita evidencia. Servicio conserva evidencia aceptada y evita duplicados; un fallo de almacenamiento o transición no se muestra como éxito. Las órdenes comerciales de Ventas no cambian.

## 16 Evidencia y reporte de defectos

Por caso registre ID, resultado, fecha, tester, versión QA, tenant autorizado, rol efectivo, navegador/dispositivo, precondiciones, pasos, esperado y observado. En movimientos incluya folios y cantidades de existencia/reservado/disponible antes y después, además de referencia de Kardex. Adjunte captura o video con el mensaje y correlación cuando exista.

Use títulos como **[QA][Almacenes][P0] Confirmar entrega duplica la salida**. Indique frecuencia e impacto; distinga defecto, dato de prueba faltante y permiso faltante. No adjunte contraseñas, tokens, enlaces vigentes de invitación ni datos personales reales.

## 17 Criterio de salida

La aceptación funcional requiere evidencia de los flujos completos y sus pruebas negativas, sin P0 abiertos ni P1 que bloqueen la operación acordada. Los casos Bloqueado o Sin ejecutar no equivalen a Pasa. Registre qué perfiles, dispositivos y aislamiento entre tenants se probaron realmente. El responsable de QA decide la aceptación con esa evidencia; este paquete no constituye una aprobación automática para Producción.
