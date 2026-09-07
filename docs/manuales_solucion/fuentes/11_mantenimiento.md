# Manual funcional de Mantenimiento

- Audiencia: solicitantes, coordinadores, técnicos, almacenistas y verificadores
- Alcance por ambiente: Local y QA
- Última revisión: 2026-09-06
- Capacidades cubiertas: mantenimiento correctivo, asignación, tiempos, refacciones, bloqueo de maquinaria y conciliación

## Propósito

Mantenimiento registra una falla desde su reporte hasta el cierre verificado. Puede atender una máquina registrada en Producción o una ubicación/objetivo libre. Conserva orden, asignación, tiempo y solicitudes internas; RH, Producción e Inventario mantienen sus propios datos.

## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Órdenes correctivas y asignación | Disponible | Disponible |
| Tiempo, diagnóstico, trabajo y verificación | Disponible | Disponible |
| Refacciones multipardida y conciliación manual | Disponible | Disponible |
| Bloqueo/liberación de maquinaria | Disponible | Disponible |
| Preventivos, activos generales y adjuntos | No disponible | No disponible |
| Reintento automático programado | No disponible | No disponible |

## Mapa del módulo

- **Órdenes:** reporte, asignación, ejecución, resolución y cierre.
- **Refacciones:** solicitudes multipardida, reserva, consumo, cancelación y conciliación.
- **Portada:** backlog e indicadores estándar de sólo lectura.

## Acceso, permisos y preparación

Solicitar, asignar, iniciar, esperar refacciones, reanudar, resolver, cerrar, reabrir y cancelar usan permisos independientes `maintenance.order.*`. Tiempo y refacciones tienen permisos propios. Un técnico puede registrar tiempo sin autoridad para resolver o cerrar.

Antes de operar:

1. Cree en RH área, puestos y trabajadores activos con **Interviene en mantenimiento**.
2. Para refacciones, cree en Inventario un almacén activo de tipo **Refacciones** y artículos con unidad vigente.
3. Active Mantenimiento; requiere RH e Inventario. Producción es opcional para instalaciones sin maquinaria productiva.

## Crear y atender una orden

1. Abra **Mantenimiento > Órdenes** y capture objetivo, prioridad, falla, ubicación y seguridad.
2. Para maquinaria, seleccione la máquina; si nace desde Producción, conserve la orden origen.
3. Guarde el borrador y pulse **Solicitar**. Una falla bloqueante solicita pausar/bloquear en Producción.
4. Seleccione un técnico elegible y pulse **Asignar**.
5. Pulse **Iniciar**. RH vuelve a validar estado y elegibilidad.
6. Registre tiempo desde la tarjeta. Sólo el responsable asignado puede capturarlo; no se admiten intervalos futuros, invertidos o solapados.
7. Solicite refacciones si son necesarias.
8. Pulse **Resolver** y capture diagnóstico, causa raíz opcional, trabajo realizado y verificación. Debe existir al menos un registro de tiempo.
9. Cierre cuando materiales y efectos externos estén conciliados.

Resolver libera una máquina, pero no reanuda automáticamente la orden productiva. El operador de Producción debe volver a validar recursos.

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
5. Al resolver, las reservas se consumen en salidas inmutables.

Cancelar una solicitud libera las reservas que sigan activas. Cancelar la orden compensa primero todas las solicitudes. La devolución de sobrantes no está implementada; no edite las salidas para simularla.

## Conciliación

Cuando Producción o Inventario no confirman una operación aparece **Requiere conciliación**. Use **Conciliar** en la orden o solicitud. El reintento conserva la operación y sus claves, por lo que no duplica bloqueo, reserva o consumo. Si vuelve a fallar, mantenga el estado y escale con la correlación.

## Reglas críticas

- Sólo una orden bloqueante activa por máquina.
- El responsable debe permanecer activo y elegible al iniciar.
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
- **Materiales no conciliados:** concilie o cancele cada solicitud antes de resolver/cancelar.
- **La máquina pertenece a otra orden:** localice la orden bloqueante activa.
- **Requiere conciliación:** reintente desde la acción visible con el estado confirmado.

## Integraciones y propiedad del dato

RH valida trabajadores; Producción decide bloqueo/liberación de maquinaria y pausa/reanudación; Inventario decide reservas, salidas, costos y almacenes. Mantenimiento conserva referencias externas con snapshots legibles, sin FKs cruzadas. Compras no se activa automáticamente ante faltantes.

## Reportes estándar de portada (Local)

La portada genera reportes descargables de órdenes, indisponibilidad de maquinaria, refacciones y tiempos de mano de obra. Los filtros visibles se limitan a periodo, estatus, prioridad, tipo de objetivo o búsqueda según el reporte. Puede escribir para encontrar las opciones disponibles; abra una tarjeta y pulse **Generar**. Un resultado vacío se informa sin descargar archivo.

Los permisos aplicables son `maintenance.order.read`, `maintenance.material_request.read` y `maintenance.time.read`. Esta capacidad está disponible sólo en Local; MTBF, analítica avanzada y distribución permanecen fuera del corte.

## Limitaciones vigentes

No incluye preventivos calendarizados, activos generales con placa o serie, IoT, garantías, proveedores externos, compras automáticas, devolución de sobrantes, participantes secundarios, adjuntos, reintento automático programado ni MTBF confiable sin horas reales de operación.

## Soporte

Conserve folio de orden, máquina u objetivo, técnico, estado, solicitud de material y correlación. No fuerce cambios en Producción o Inventario para ocultar un pendiente.
