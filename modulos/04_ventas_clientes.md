# ERClave - Ventas y Clientes

## Coherencia de formularios Local (CHG-262)

La planeacion de una orden de servicio usa controles de fecha desde el primer render y conserva las fechas recuperadas del backend. El registro de tiempo respeta el limite contractual de 1440 minutos. Las pruebas nuevas usan respuestas mutantes interceptadas, sin crear ordenes ni registrar costos reales. Evidencia: `docs/auditorias/frontend_backend_2026-09-07.md`.

## Objetivo

Ventas conecta la relacion comercial con los maestros autoritativos de ERClave. El segundo corte real esta desplegado en Local y QA y cubre Clientes, Cotizaciones, Pedidos, surtido y Entregas mediante `sales-service`; no convierte texto libre ni datos del navegador en maestros operativos.

## Alcance por ambiente

| Ambiente | Alcance comprobado |
|---|---|
| Local | API, schema `sales` y migracion `20260901_0030` aplicados y certificados para Clientes, Cotizaciones, Pedidos, Ordenes de servicio y Entregas, con permisos, idempotencia, auditoria y pruebas de integracion. |
| QA | `sales-service` desplegado dentro del release de siete servicios; cadena comun aplicada hasta `20260825_0029`. CHG-255 permanece solo en codigo Local hasta un candidato posterior. La disponibilidad efectiva depende del entitlement del tenant y de RH/Produccion. |
| Produccion | No aprovisionado. |

Devoluciones permanecen `planned`. Pedidos y Entregas ya no escriben mock cuando la interfaz opera en modo API.

## Resultado de auditoria CHG-203

CHG-204 aplico en Local el plan de correccion: la UI permite crear Entregas segun permiso y saldo no comprometido; el contenido comercial se escapa; cada producto exige un articulo autoritativo de Inventory con la misma unidad; y surtido, cancelacion y confirmacion usan reclamos durables, locks y claves estables para reintento/reconciliacion. La promocion a QA conserva sus gates de candidato, object storage y pruebas de ambiente.

El detalle, evidencia y criterios de cierre viven en [`docs/auditorias/ventas_segundo_corte_2026-08-18.md`](../docs/auditorias/ventas_segundo_corte_2026-08-18.md).

### Pedidos, surtido y entregas

- Una cotizacion `approved` se convierte una sola vez en pedido; conserva snapshots comerciales y de costo.
- Cada producto tiene un unico articulo autoritativo de Inventory definido por Produccion. Se surte desde ese articulo con reservas de Inventory o genera una solicitud idempotente a Production. Los servicios quedan listos sin reserva.
- Inventory permite consumo parcial de reservas para entregas parciales; cancelar el pedido libera reservas activas.
- La solicitud a Produccion no simula una orden liberada: Production valida producto, receta aprobada y unidad, y conserva la responsabilidad de planear capacidad y liberar.
- Crear una Entrega bloquea el Pedido y sus partidas, descuenta cantidades ya comprometidas por otros borradores y evita sobreasignacion concurrente.
- Confirmar una Entrega actualiza cantidades y consume reservas con una clave estable. Inventory aporta costo de consumo para `stock`; servicios exigen costo real capturado. Production aun no devuelve costo real y sus partidas permanecen no entregables hasta el callback del siguiente corte.
- Monedas y condiciones de pago son catalogos tenant-safe de Administracion y se revalidan durante el ciclo comercial.
- La captura de Entrega solicita siempre fecha programada, destinatario, referencia, notas y cantidades, tanto en modo API como en la experiencia local.
- La seleccion de Cotizacion para crear Pedido busca por folio, cliente, producto/servicio o importe y muestra solo aprobadas no utilizadas.
- La seleccion de Pedido para crear Entrega busca por folio, cliente, producto/servicio o estado y muestra solo documentos con partidas entregables.

### Ordenes de servicio CHG-255

- Confirmar un Pedido crea una orden de servicio por cada partida `service`, con folio administrado y snapshots del pedido, cliente y servicio. Un reintento no duplica la orden porque la partida es unica por tenant.
- El ciclo es `draft -> planned -> assigned -> in_progress -> on_hold -> in_progress -> pending_acceptance -> accepted`; cancelar es una transicion terminal autorizada por separado.
- Planear conserva fechas y notas; asignar y registrar tiempo validan trabajadores activos mediante la proyeccion minima de RH. Sales guarda IDs externos y snapshots, sin FK ni escritura en `hr`.
- Tiempo, costos y evidencia son registros auditables propios de Sales. La aceptacion exige ejecucion iniciada, al menos un registro de tiempo y nombre de quien acepta; el costo real se recalcula desde tiempos y costos trazables.
- Las partidas de servicio no se surten, no aparecen en Entregas y no generan reservas, consumos ni movimientos de Inventory. Aceptar todas las ordenes de servicio puede completar esa parte del Pedido sin afirmar entrega fisica.

### Seleccion escalable de documentos

Los catalogos pequenos y estables, como estatus, moneda o unidad, pueden usar selectores. Las entidades operativas crecientes no deben renderizar cientos de opciones: clientes, productos, cotizaciones, pedidos, ordenes de compra, recepciones y documentos equivalentes requieren busqueda por texto, filtros de negocio y resultados acotados. Ventas implementa el patron en Local y QA para Cotizacion -> Pedido y Pedido -> Entrega; los modulos aun no especializados deben adoptarlo al construir esos flujos. Para volumen superior al limite preventivo de 200, la busqueda y paginacion deben resolverse en el backend.

### Consulta de Margen CHG-250

- `Margen` es una consulta operativa de solo lectura sobre Pedidos y Entregas propiedad de Sales.
- Presenta venta, costo/margen estimados y costo/margen reales solo cuando la Entrega confirmada aporta una fuente trazable (`inventory_consumption`, `service_capture` o `production_report`).
- No crea registros, no usa el formulario generico y no persiste documentos en `localStorage` cuando `apiMode=api`.
- Los cruces configurables por periodo, producto, cliente u otros modulos permanecen bajo el modulo especializado Reportes.

## Criterios de aceptacion del primer corte

### Clientes

- El codigo es estable, normalizado y unico por tenant.
- Nombre comercial, tipo, contacto principal, condiciones de pago, moneda y responsable son obligatorios.
- El responsable se selecciona de una proyeccion minima de trabajadores activos de RH; puesto y area tambien deben estar activos. Ventas conserva ID externo y nombre snapshot, sin FK ni escritura en `hr`.
- El contacto principal exige nombre, correo valido y telefono.
- El perfil fiscal es opcional. Si se inicia, razon social, RFC/ID fiscal y correo de facturacion son obligatorios; el resto de datos fiscales y direccion es opcional.
- Estados permitidos: `prospect`, `active`, `inactive`, `blocked`.
- Codigo y RFC/ID fiscal no se duplican dentro del tenant.
- Crear y editar exige `Idempotency-Key`, permiso puntual y auditoria.

### Cotizaciones

Clientes, cotizaciones, pedidos y entregas obtienen su codigo desde el catalogo tenant-safe de Administracion cuando el tipo documental esta en modo administrado. El modo manual conserva normalizacion, unicidad e idempotencia dentro de Sales; cambiar el prefijo no renombra documentos ya emitidos.

- Solo se crea para un cliente `active` del mismo tenant.
- Cada partida referencia un producto o servicio `active` de Produccion; no admite nombre libre.
- La unidad se valida contra el catalogo activo de Administracion y debe coincidir con la unidad base autoritativa del producto/servicio. Conversiones de unidad quedan fuera de este corte.
- Moneda y condiciones de pago son referencias activas del catalogo del tenant; MXN/USD/EUR y contado/credito son defaults iniciales, no enums permanentes.
- Cantidad es mayor a cero; precio no es negativo; descuento permanece entre 0 y 100; no se duplica el mismo producto en una cotizacion.
- Backend calcula subtotal, descuento y total por partida y documento. Si Produccion dispone de costo estandar, conserva snapshot, estima costo y margen; el navegador no declara esos resultados.
- La cotizacion conserva snapshots de cliente, responsable, producto, unidad y costo para que cambios maestros futuros no reescriban historia.
- Estados: `draft -> quoted -> approved`; desde `draft` o `quoted` puede pasar a `expired` o `cancelled`. Solo `draft` es editable y una cotizacion vencida no puede emitirse ni aprobarse.
- Emitir y aprobar revalidan cliente, responsable, productos y unidades contra sus autoridades.
- Todos los comandos son idempotentes y auditados.

## Entidades y ownership

| Entidad | Owner | Observacion |
|---|---|---|
| `sales.customers` | Sales | Perfil comercial y fiscal tenant-safe. |
| `sales.customer_contacts` | Sales | Un contacto principal activo por cliente. |
| `sales.quotes` | Sales | Documento, estados, totales y snapshots. |
| `sales.quote_lines` | Sales | Partidas calculadas y costo snapshot. |
| `sales.orders`, `sales.order_lines` | Sales | Pedido, snapshots del articulo y estados durables de surtido/cancelacion originados en una cotizacion aprobada. |
| `sales.order_line_reservations` | Sales | Referencias a reservas propiedad de Inventory y cantidades consumidas. |
| `sales.deliveries`, `sales.delivery_lines` | Sales | Entregas parciales/totales, confirmacion durable, evidencia, costo real y procedencia. |
| `sales.service_orders` | Sales | Ejecucion y aceptacion de cada partida de servicio confirmada. |
| `sales.service_time_entries`, `sales.service_cost_entries`, `sales.service_evidence` | Sales | Tiempo, costos y evidencia trazables de la orden de servicio. |
| `sales.idempotency_records` | Sales | Replay seguro por operacion y tenant. |
| `sales.audit_events` | Sales | Evidencia de comandos y transiciones. |

RH, Produccion y Administracion conservan ownership de trabajadores, productos/servicios y unidades. No hay FK entre schemas de servicios distintos.

## Permisos

- `sales.customer.read`, `sales.customer.create`, `sales.customer.update`.
- `sales.quote.read`, `sales.quote.create`, `sales.quote.update`.
- `sales.quote.submit`, `sales.quote.approve`, `sales.quote.expire`, `sales.quote.cancel`.
- `sales.order.read`, `sales.order.create`, `sales.order.fulfill`, `sales.order.cancel`.
- `sales.delivery.read`, `sales.delivery.create`, `sales.delivery.confirm`, `sales.delivery.cancel`.
- `sales.service_order.read`, `plan`, `assign`, `start`, `wait`, `resume`, `submit_acceptance`, `accept`, `cancel`.
- `sales.service_order.time.create`, `sales.service_order.cost.create`, `sales.service_order.evidence.create`.

Los endpoints de lectura reducida aceptan permisos de Ventas sin conceder acceso al expediente completo de RH ni escritura en otros dominios.

## Sinergia y habilitacion modular

- Backoffice es el unico que concede o retira el entitlement contractual de `sales`; el administrador del tenant solo cambia `tenant_enabled` cuando ese entitlement esta activo.
- Ventas depende de `hr` y `production` efectivos. No puede encenderse si alguno esta apagado y ninguno puede apagarse mientras Ventas permanezca efectivo. `admin` sigue siendo nucleo obligatorio y autoridad del catalogo de unidades.
- El onboarding que selecciona Ventas incluye RH y Produccion, crea primero los entitlements y despues asigna al owner los permisos de todos los modulos activos.
- La API de Ventas vuelve a validar `active_modules` y permiso en cada request autenticado; ocultar el modulo o un boton no se considera control de seguridad.
- La API permite leer documentos independientemente de sus maestros y la UI usa resultados parciales: una falla de Admin/RH/Production conserva Clientes, Cotizaciones, Pedidos o Entregas ya disponibles y bloquea solo la captura que necesita esa autoridad.
- El catalogo de modulos publica `dependencies`, y tanto Backoffice como Administracion explican el bloqueo antes de enviar una combinacion invalida.

## Fuera del segundo corte

- contactos secundarios y direcciones multiples;
- listas de precios, impuestos y tipos de cambio configurables;
- autorizacion de descuentos por umbral;
- devoluciones, facturacion y cobranza;
- conversion automatica de solicitud comercial a orden liberada y recepcion de producto terminado;
- almacenamiento del logo en object storage para QA/Produccion; Local conserva un data URL validado de hasta 1 MB;
- paginacion comercial con cursor para volumen mayor al limite preventivo de 200;
- PDF de Pedido y remision/Entrega con snapshot documental;

Estas capacidades requieren nuevos criterios de aceptacion, contratos propietarios y migraciones. No se implementan como escritura cruzada ni como fallback mock.
# CHG-206: elegibilidad comercial

Ventas conserva la identidad comercial de Producción y usa el artículo vinculado únicamente para surtido. Un producto sólo es surtible cuando apunta a un artículo activo `finishedGood` con la misma unidad; los servicios no requieren artículo.

## CHG-209: seleccion escalable

Clientes, productos/servicios, responsables, cotizaciones, pedidos y almacenes de surtido se seleccionan mediante búsqueda acotada. Los documentos conservan filtros especializados de elegibilidad; las relaciones usan IDs y snapshots visibles. Estatus, moneda, condición de pago y modo de surtido se mantienen como listas cerradas.


## Confirmaciones y recuperaciones Local CHG-265

Ventas prepara entrega; inventory.movement.create confirma salida desde Movimientos. sales.delivery.confirm por sí solo recibe guía para continuar en Almacén. Reintentos conservan las claves durables por reserva. Las partidas sin surtido stock comprobable no se despachan; conectar automáticamente solicitud comercial, Producción y recepción/entrega sigue planned. Inicio/reanudación de servicio comercial revalida responsable RH; no se agregan materiales a ese tipo de orden en este corte.

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.


## Ajustes UAT Local CHG-266

Las tarjetas indican Borrador → Emitir cotización → Cotizada → Aprobar cotización → Aprobada. Emitir requiere sales.quote.submit y aprobar sales.quote.approve. Cuando falte autoridad se orienta a solicitar intervención del usuario autorizado o administrador de roles. La reparación del catálogo/Owner de pruebas fue exclusiva de Local; contratos y ciclo backend no cambian.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Disponibilidad QA CHG-270

Los cambios Local documentados hasta CHG-268 fueron promovidos en el release `b63cdad` a QA el 9 de septiembre de 2026. Salud/readiness/versión y rechazo de accesos no autenticados comprobados; aceptación funcional autenticada pendiente del tester. Datos QA existentes preservados. Evidencia: `docs/operaciones/release_qa_20260908.md`.
