# Modulo 11 - Mantenimiento

## Autorizacion operativa Local

Solicitar, asignar, iniciar, esperar refacciones, reanudar, resolver, cerrar, reabrir y cancelar son capacidades independientes `maintenance.order.*`. El backend selecciona la requerida desde la transicion recibida; un tecnico con permiso de iniciar no obtiene por ello permiso de resolver o cerrar.

## Estado y objetivo

Estado: `implemented` en Local desde CHG-234 y endurecido en CHG-235 con la revision `20260824_0028`. El modulo puede activarse desde Backoffice y el tenant demo Local ya lo tiene habilitado; QA y Produccion no cambian.

El modulo controlara mantenimiento correctivo desde el reporte de una falla hasta su cierre verificado, incluyendo responsable, tiempo real, diagnostico, trabajo realizado y refacciones. El primer corte implementable sera correctivo; planes preventivos, recurrencia, garantias y proveedores quedan para cortes posteriores.

## Alcance funcional

- Crear una orden desde Mantenimiento.
- Crear una orden desde una orden de Produccion en `waiting_resources` o `in_progress`.
- Atender una maquina registrada en Production o un objetivo libre de edificio/instalacion sin identificador.
- Asignar un responsable principal de RH elegible para Mantenimiento.
- Registrar diagnostico, causa raiz, trabajo realizado, seguridad, verificacion, inicio/fin y tiempo por persona.
- Solicitar varias refacciones en una misma solicitud interna y conciliarlas con Inventory.
- Bloquear/liberar una maquina y pausar una orden productiva mediante comandos del servicio propietario.
- Consultar ordenes, estados, tiempo acumulado y refacciones desde la interfaz operativa.

Fuera del primer corte: mantenimiento preventivo calendarizado, activos generales con placa/serie, lectura IoT, contratos externos, garantias, compras automaticas y MTBF basado en horas reales de operacion.

## Propiedad y arquitectura

| Dato o regla | Propietario | Regla |
|---|---|---|
| Orden, asignacion, tiempos y solicitud interna de material | `maintenance-service` | Nunca se escriben directamente en otros schemas. |
| Areas, puestos, trabajadores y elegibilidad | `hr-service` | La elegibilidad se declara con `intervenes_in_maintenance`; no se infiere por el nombre del puesto. |
| Maquina y orden productiva | `production-service` | Mantenimiento solicita bloqueo/liberacion; Production decide su transicion valida. |
| Articulo, almacen, existencia, reserva, salida, devolucion y costo | `inventory-service` | Las refacciones se reservan y mueven con comandos idempotentes de Inventory. |

Dependencias duras del modulo: RH e Inventory. Production es una integracion opcional: una empresa puede mantener instalaciones sin contratar Produccion.

Una maquina no se modela como articulo de inventario. En el MVP la referencia identificada es una maquina de Production. Para edificio u otro objetivo se exigen descripcion y ubicacion, sin fabricar un UUID externo. Un futuro modulo de Activos podra sustituir esta referencia libre.

## Agentes especializados

### Agente de negocio de mantenimiento y confiabilidad

Valida criticidad, prioridades, continuidad, seguridad, segregacion de funciones, evidencias de cierre, tiempos, consumos, recurrencia y valor de indicadores. Rechaza automatismos que oculten una maquina insegura o reanuden Produccion sin verificacion.

### Agente tecnico de ordenes e integraciones

Custodia estados, invariantes, idempotencia, concurrencia, auditoria y contratos con RH, Inventory y Production. No permite FK entre schemas propietarios ni efectos externos sin estado durable de reconciliacion.

## Entidades objetivo

| Entidad | Proposito |
|---|---|
| `maintenance.orders` | Folio, objetivo, origen, prioridad, estado, snapshots y resultado tecnico. |
| `maintenance.assignments` | Responsable principal, participantes e historial de asignacion. |
| `maintenance.time_entries` | Tiempo real por trabajador, intervalo y notas. |
| `maintenance.material_requests` | Cabecera de solicitud al almacen de refacciones y estado de conciliacion. |
| `maintenance.material_request_lines` | Articulo, unidad, solicitado, reservado, emitido y costo snapshot. |
| `maintenance.audit_events` | Actor, cambio, motivo, correlacion y antes/despues. |
| `maintenance.idempotency_records` | Repeticion segura de comandos. |

Todas las entidades incluyen `tenant_id`, auditoria temporal y aislamiento por tenant. Las referencias externas se guardan como ID mas snapshot legible, nunca como FK cruzada.

## Objetivos y origenes

`target_type`:

- `production_machine`: exige `production_machine_id`; conserva codigo/nombre como snapshot.
- `facility`: exige descripcion y ubicacion.
- `other`: exige descripcion y ubicacion.

`source_type`:

- `manual`: originada dentro de Mantenimiento.
- `production_order`: conserva referencia y snapshot de la orden productiva que reporto la falla.

## Estados

| Estado | Significado |
|---|---|
| `draft` | Captura editable, aun sin afectar disponibilidad. |
| `requested` | Falla reportada; si bloquea una maquina, empieza la orquestacion con Production. |
| `assigned` | Responsable principal elegible confirmado. |
| `in_progress` | Trabajo tecnico iniciado. |
| `waiting_parts` | Trabajo suspendido por refacciones; la indisponibilidad continua. |
| `resolved` | Trabajo terminado y verificado; tiempos/materiales conciliados y maquina liberable. |
| `closed` | Cierre administrativo definitivo. |
| `cancelled` | Solicitud anulada con motivo y compensaciones concluidas. |

Flujo principal: `draft -> requested -> assigned -> in_progress -> resolved -> closed`.

Alternos:

- `assigned|in_progress -> waiting_parts -> in_progress`.
- `resolved -> in_progress` cuando falla la verificacion.
- `draft|requested|assigned -> cancelled`, siempre que se liberen reservas y bloqueos aplicables.

## Flujos

### Orden manual

1. El usuario selecciona maquina mediante busqueda acotada o captura objetivo libre y ubicacion.
2. Captura prioridad, descripcion y notas de seguridad.
3. Al solicitar, se genera folio y auditoria; una maquina critica se bloquea en Production.
4. Se asigna un trabajador que RH confirme como elegible.
5. El tecnico registra diagnostico, trabajo, tiempos y refacciones.
6. La resolucion exige conciliacion de materiales, al menos un registro de tiempo y verificacion.
7. Se libera la maquina, pero ninguna orden productiva se reanuda automaticamente.

### Desde Produccion

1. La accion aparece solo para ordenes `waiting_resources` o `in_progress` y exige una maquina asociada.
2. Production entrega referencias/snapshots; Mantenimiento crea la orden idempotentemente y el usuario la solicita para comenzar el bloqueo.
3. Production deja `waiting_resources` cuando aun no inicio, o pasa a `paused` si estaba `in_progress`, y marca la maquina `maintenance`.
4. Al resolver, Mantenimiento solicita liberar la maquina.
5. El operador de Produccion revalida recursos y decide reanudar; no existe reanudacion automatica.

### Refacciones

1. El tecnico crea una solicitud multi-linea contra un almacen de tipo estable `spare_parts`.
2. Inventory valida articulo, unidad, almacen y disponibilidad; reserva sin permitir existencia negativa.
3. Al resolver, cada reserva se consume en una salida inmutable con costo snapshot. La devolucion de sobrantes queda para el siguiente corte y nunca editara la salida.
4. Si falta material, la orden puede quedar `waiting_parts`. Elevar la necesidad a Compras sera una accion explicita futura, no automatica.

## Reglas criticas

- Solo una orden bloqueante activa por maquina. Un reporte repetido debe enlazarse o rechazarse, no duplicar indisponibilidad.
- El responsable principal es obligatorio para iniciar y debe seguir elegible/activo en RH.
- Participantes adicionales tambien deben ser elegibles; cada uno registra su propio tiempo.
- `ended_at` debe ser posterior a `started_at`; intervalos duplicados o solapados para la misma persona se rechazan.
- Resolver exige diagnostico, trabajo realizado, verificacion, tiempo y solicitudes de material conciliadas. Cero material es valido y explicito.
- Las operaciones externas usan `Idempotency-Key`, `X-Correlation-ID`, bloqueo concurrente y registro durable. Una respuesta incierta termina en `needs_reconciliation`, nunca en exito supuesto.
- `needs_reconciliation` conserva la operacion exacta pendiente y ofrece un reintento explicito con claves estables por orden, solicitud y partida.
- Reabrir una orden de maquina vuelve a solicitar el bloqueo; cerrar exige que no exista conciliacion pendiente.
- Cancelar una orden compensa primero todas las reservas activas. Una liberacion parcial conserva las lineas restantes para reintento.
- El bloqueo empieza al solicitar una falla bloqueante y termina al resolver/cancelar con compensaciones terminadas.
- Todas las mutaciones muestran indicador de progreso y bloquean clics repetidos conforme a la regla transversal del frontend.

## RH requerido

El tenant configura un area de Mantenimiento, puestos y personal en RH. No se sembraran nombres ni datos personales. Los puestos incorporaran `intervenes_in_maintenance` y RH expondra busqueda acotada de trabajadores elegibles. Si no hay ninguno, el modulo muestra una preparacion pendiente y bloquea la asignacion con explicacion accionable.

## Permisos implementados

- `maintenance.order.read|create|update|transition|reconcile`
- `maintenance.time.read|create`
- `maintenance.material_request.read|create|cancel|reconcile`
- `maintenance.report.read`

Los permisos no fijan roles universales. Cada tenant puede separar solicitante, coordinador, tecnico, almacenista y verificador.

## Reportes estandar

- backlog por estado, prioridad, responsable y antiguedad;
- indisponibilidad por maquina o ubicacion;
- ordenes en espera de refacciones;
- tiempo de mano de obra y MTTR cuando exista muestra suficiente;
- consumo y costo de refacciones;
- recurrencia por maquina/ubicacion y causa.

MTBF queda pendiente hasta contar con horas reales de operacion; no se inferira con calendario.

## Criterios cerrados en el primer corte

- Contrato y persistencia aislada de Maintenance.
- Flujo correctivo manual completo y asignacion contra RH.
- Solicitud multi-linea con reserva, consumo o cancelacion en Inventory.
- Creacion desde Produccion con pausa/bloqueo y liberacion segura.
- UI con busquedas escalables, feedback de mutacion y estados de reconciliacion.
- Pruebas de API y repositorio real para contrato, idempotencia, aislamiento tenant y contencion por maquina.

## Pendientes deliberados

1. Definir la experiencia de preventivos y planes recurrentes.
2. Diseñar Activos para equipos no productivos con identificador, serie, garantia e historial.
3. Definir escalamiento explicito de faltantes hacia Compras.
4. Definir anexos/fotografias con almacenamiento y retencion.
5. Agregar reintento automatico programado de operaciones `needs_reconciliation` y devolucion de sobrantes; el reintento manual ya esta implementado.
6. Incorporar participantes secundarios, adjuntos y reportes analiticos dedicados.

## Ajuste de continuidad CHG-239

- Una orden `assigned`, `in_progress` o `waiting_parts` muestra **Solicitar refacciones** y transporta el folio al submodulo Refacciones.
- El formulario solo reserva contra un almacen activo `spare_parts`. Si el maestro no existe, muestra la causa y, con permiso de Inventario, abre su alta con el tipo correcto precargado.
- Cada solicitud visible enumera codigo, nombre, cantidad, unidad y estado por partida; ya no se reduce a un contador o al nombre del almacen.
- La tarjeta identifica de forma explicita al tecnico asignado. El selector conserva la seleccion vigente y distingue **Reasignar** de la primera asignacion.

## Guias de flujo transversales CHG-248

- Ordenes muestra el recorrido Reporte, Asignacion, Ejecucion y Cierre; el ultimo paso conserva la regla de liberar sin reanudar Produccion automaticamente.
- Refacciones muestra Orden, Almacen, Reserva y Conciliacion, manteniendo Inventory como autoridad de almacenes, reservas y movimientos.
- Ambas rutas reutilizan el riel vertical colapsable estandar, con contenido equivalente ES/EN y reacomodo por ancho real del contenedor.
- La guia es ayuda contextual: no sustituye permisos `maintenance.*`, validaciones backend, conciliacion durable ni evidencia tecnica de cierre.
