# Manual funcional de Mantenimiento

- Audiencia: solicitantes, coordinadores y tecnicos de mantenimiento
- Alcance por ambiente: Local
- Ultima revision: 2026-08-25
- Capacidades cubiertas: ordenes correctivas, asignacion, tiempos, refacciones, bloqueo de maquinaria y conciliacion

## Proposito

Mantenimiento registra una falla desde su reporte hasta el cierre verificado. Puede atender una maquina registrada en Produccion o una ubicacion del edificio sin identificador.

## Preparacion

Cada cambio de estado es asignable por separado en Local: solicitar, asignar, iniciar, esperar refacciones, reanudar, resolver, cerrar, reabrir y cancelar usan permisos `maintenance.order.*` distintos. Un tecnico puede capturar tiempo o iniciar sin recibir automaticamente autoridad para resolver o cerrar.

1. En RH, cree el area y los puestos de Mantenimiento.
2. Marque **Interviene en mantenimiento** en los puestos que pueden recibir ordenes.
3. Mantenga activos el area, puesto y trabajador.
4. En Inventario, cree un almacen activo de tipo **Refacciones** (`spare_parts`) y registre los articulos con su unidad base.
5. Active el modulo desde Backoffice cuando RH e Inventory esten habilitados.

## Levantar y atender una orden

1. Abra **Mantenimiento > Ordenes** y capture folio, objetivo, prioridad, falla, ubicacion y seguridad.
2. Si proviene de Produccion, seleccione una orden elegible y su maquina asociada.
3. Cree la orden y pulse **Solicitar**. La maquina se bloquea; una orden productiva en proceso queda pausada.
4. Seleccione un tecnico elegible y pulse **Asignar**.
5. Pulse **Iniciar**. El sistema vuelve a confirmar que el tecnico siga activo y elegible.
6. Registre el tiempo real desde **Registrar tiempo** en la tarjeta de la orden. Solo el responsable asignado puede capturarlo y no se admiten intervalos futuros o solapados.
7. Pulse **Resolver**. El sistema abre un formulario propio de ERClave; capture diagnostico, causa raiz opcional, trabajo realizado y verificacion. Si la orden aun muestra `0 min`, el mismo formulario solicita inicio, fin y notas y registra el tiempo antes de resolver. Los tres campos operativos son obligatorios y los errores aparecen dentro del formulario, sin cuadros del navegador.
8. Pulse **Cerrar** cuando materiales y efectos externos esten conciliados.

Reabrir una orden resuelta vuelve a bloquear la maquina. Produccion nunca se reanuda automaticamente.

## Solicitar refacciones

1. Abra **Mantenimiento > Refacciones**.
2. Seleccione orden y almacen de refacciones.
3. Agregue una o varias partidas, sin repetir articulos.
4. Reserve. Inventario valida unidad, disponibilidad y existencia neta.
5. Al resolver la orden, las reservas se convierten en salidas de Inventario.

Tambien puede iniciar desde **Mantenimiento > Ordenes** mediante **Solicitar refacciones**. La orden queda precargada. Cada solicitud muestra despues sus partidas, cantidades, unidades y estado.

Si no existe un almacen activo de tipo Refacciones, el sistema explica el faltante. Un usuario con `inventory.warehouse.create` puede abrir desde ahi el alta de Inventario con el tipo correcto precargado; los demas deben solicitarlo al encargado de Inventario.

Cancelar una solicitud libera sus reservas. Cancelar la orden primero compensa todas las solicitudes activas y solo despues cambia el estado de la orden.

## Conciliacion

Si Production o Inventory no confirman una operacion, aparece **Requiere conciliacion**. Use **Conciliar** en la orden o solicitud correspondiente. El reintento conserva la operacion exacta y claves estables, por lo que no duplica bloqueos, reservas ni consumos.

No cierre la orden ni modifique datos directamente en Inventario o Produccion para ocultar el pendiente. Si la conciliacion vuelve a fallar, conserve el estado y revise la disponibilidad del servicio indicado.

## Mensajes frecuentes

- **No hay tecnicos elegibles:** revise trabajador, puesto, area y la casilla de intervencion en RH.
- **La orden dice Asignada pero no veo a quien:** la tarjeta muestra **Tecnico asignado** y el selector conserva la persona vigente; **Reasignar** solo aparece con su permiso.
- **Crea primero un almacen de refacciones:** registre o active un almacen tipo Refacciones en Inventario.
- **Requiere conciliacion:** reintente desde la accion visible; el resultado anterior no se supone exitoso.
- **Materiales no conciliados:** concilie o cancele cada solicitud antes de resolver o cancelar la orden.
- **Faltan datos para resolver:** complete diagnostico, trabajo realizado y verificacion en el formulario de resolucion. Puede corregirlos sin cerrar el formulario.
- **At least one time entry is required:** la orden no tiene tiempo operativo. Use **Registrar tiempo** en su tarjeta o capture Inicio y Fin dentro de **Resolver**. Si su rol no tiene `maintenance.time.create`, solicite la captura a un usuario autorizado.
- **La maquina pertenece a otra orden:** localice la orden bloqueante activa; no fuerce su liberacion.

## Limitaciones

No incluye preventivos calendarizados, activos generales con placa, adjuntos, participantes secundarios, devolucion de sobrantes ni escalamiento automatico hacia Compras.
