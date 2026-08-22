# ERClave - Ownership de datos y contratos MVP

## 1. Objetivo

Este documento define quien es dueno de cada dato del MVP real de ERClave y que contratos deben usar los modulos para comunicarse sin escribir informacion ajena.

Aplica a los primeros dominios que se moveran de maqueta a backend real:

- Administracion;
- Produccion;
- Almacenes;
- Ventas;
- Billing / SaaS;
- Provisioning;
- Integraciones.

La regla central es:

> Cada servicio es dueno de sus datos, sus reglas y sus estados. Los demas servicios solo pueden consultar o solicitar acciones por contratos explicitos.

Complemento recomendado:

- `docs/arquitectura/modelo_multitenant.md` define como se resuelve identidad, tenant, membresias, roles, permisos, entitlements y contratacion en linea.

---

## 2. Principios obligatorios

1. Todo dato operativo de cliente debe pertenecer a un `tenant_id`.
2. Ningun servicio debe escribir directamente tablas de otro servicio.
3. Las referencias entre servicios deben usar IDs estables, no llaves foraneas cruzadas.
4. Cada operacion critica debe registrar auditoria.
5. Las operaciones que puedan repetirse por reintento deben ser idempotentes.
6. Los estados no deben cambiarse libremente; cada servicio debe validar transiciones.
7. Los modulos contratados por tenant deben validarse antes de ejecutar acciones.
8. El frontend nunca debe ser la unica capa que proteja reglas de negocio.

---

## 3. Servicios duenos del MVP

| Servicio | Dominio | Responsabilidad |
|---|---|---|
| `admin-service` | Administracion | Tenants, usuarios, roles, permisos, unidades de negocio, modulos activos y configuracion por tenant. |
| `production-service` | Produccion | Productos/servicios, recetas, versiones de receta, recursos productivos, maquinaria, ordenes y avance por etapas. |
| `inventory-service` | Almacenes | Almacenes, articulos inventariables, ubicaciones, movimientos, existencias, kardex, reservas y valuacion de materiales. |
| `sales-service` | Ventas | Local real: clientes, contactos, cotizaciones, pedidos, surtido y entregas. Devoluciones permanecen planeadas. |
| `billing-service` | Billing / SaaS | Planes comerciales, suscripciones, eventos de pago, activaciones manuales y estado de cobro. |
| `provisioning-service` | Provisioning | Orquestacion de alta de tenant, activacion de modulos e invitacion del administrador inicial. |
| `integration-service` | Integraciones | Clientes API, scopes, cuotas, llaves, uso de API y politicas de integracion. |

---

## 4. Reglas multi-tenant

### 4.1 Datos con `tenant_id`

Deben incluir `tenant_id`:

- usuarios cliente;
- roles cliente;
- permisos asignados;
- productos y servicios;
- recetas y versiones;
- ordenes de produccion;
- areas, roles operativos y maquinaria;
- almacenes, articulos, movimientos y existencias;
- clientes, cotizaciones, pedidos y entregas;
- API clients creados por clientes;
- configuraciones y parametros por tenant.

### 4.2 Datos globales sin `tenant_id`

Pueden no tener `tenant_id` si son gobernados por EsLaClave:

- catalogo global de modulos;
- catalogo global de permisos disponibles;
- planes comerciales base;
- plantillas de roles sugeridos;
- catalogos tecnicos globales;
- versiones de contratos API.

Si un dato global se personaliza para un cliente, la personalizacion debe vivir con `tenant_id`.

### 4.3 Aislamiento minimo

Toda consulta operativa debe filtrar por `tenant_id` desde backend. No basta con ocultar datos en frontend.

Regla:

```text
token -> tenant_id autorizado -> permisos -> modulos activos -> accion permitida -> datos filtrados
```

---

## 5. Ownership de entidades

### 5.1 Administracion

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `tenant` | `admin-service` | `admin-service`, por solicitud de `provisioning-service` | Todos los servicios mediante contrato interno | `tenant.created`, `tenant.suspended`, `tenant.reactivated` |
| `user` | `admin-service` | Usuarios autorizados del tenant y flujos de invitacion | Servicios para autorizacion | `user.invited`, `user.activated`, `user.disabled` |
| `role` | `admin-service` | Administradores del tenant | Todos para validar permisos | `role.created`, `role.updated` |
| `permission` | `admin-service` | EsLaClave como catalogo global | Todos | `permission.catalog.updated` |
| `module_entitlement` | `admin-service` | Backoffice interno; Billing/Provisioning por contrato futuro | Administrador tenant para cambiar solo su preferencia; todos los servicios para autorizar | `tenant.modules.updated` |
| `business_unit` | `admin-service` | Administradores del tenant | Servicios operativos | `business_unit.created`, `business_unit.updated` |
| `tenant_setting` | `admin-service` | Administradores autorizados | Servicios segun parametro | `tenant.setting.updated` |
| `code_sequence` | `admin-service` | Administradores con `admin.setting.update`; consumidores reservan con su permiso de alta | Todos los modulos con documento configurable | `business_code.allocated` auditable |

Reglas:

- ningun usuario cliente accede a consola interna de EsLaClave;
- ningun servicio debe asumir permisos sin validar contra `admin-service` o token autorizado;
- suspender un tenant debe bloquear acciones de escritura y permitir solo accesos definidos por politica.
- Backoffice gobierna `module_entitlement.status`; un administrador del tenant nunca concede, suspende ni retira modulos contratados.
- El tenant solo cambia `tenant_enabled` cuando el entitlement esta `active`; la autorizacion efectiva exige ambas condiciones.
- Retirar un entitlement conserva permisos y datos historicos, pero los excluye de `session/context`, policy y navegacion efectiva.
- Cada modulo conserva ownership de su documento y unicidad de codigo; Admin es propietario exclusivo de la configuracion y reserva atomica del consecutivo. No se comparte una secuencia global entre tenants.

### 5.2 Produccion

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `product_service` | `production-service` | Produccion autorizada | Ventas, Almacenes, Reportes | `product_service.created`, `product_service.updated`, `product_service.status_changed` |
| `recipe` | `production-service` | Produccion autorizada | Produccion, Costos futuro, Ventas para costo estimado | `recipe.created`, `recipe.updated` |
| `recipe_version` | `production-service` | Produccion autorizada | Produccion, Costos futuro | `recipe_version.approved`, `recipe_version.obsoleted` |
| `recipe_resource` | `production-service` | Produccion autorizada | Produccion, Almacenes por consulta de validacion | `recipe_resource.updated` |
| `recipe_stage` | `production-service` | Produccion autorizada | Produccion | `recipe_stage.updated` |
| `production_order` | `production-service` | Produccion; Ventas solo solicita por contrato | Produccion, Ventas, Almacenes, Reportes | `production_order.created`, `production_order.status_changed`, `production_order.completed` |
| `production_order_stage` | `production-service` | Produccion autorizada | Produccion, Reportes | `production_order_stage.status_changed` |
| `machine` | `production-service` | Produccion autorizada | Produccion, Costos futuro | `machine.updated`, `machine.status_changed` |

Reglas:

- Ventas no crea ordenes directamente; solicita orden bajo pedido.
- Almacenes no modifica recetas ni ordenes.
- Produccion es dueno del mapeo estable entre un producto vendible y su articulo de Inventory; valida el ID externo, estado y unidad por API y no escribe el schema `inventory`.
- Si una receta cambia, las ordenes en curso conservan snapshot de la version con la que fueron liberadas.
- Un producto/servicio sin receta aprobada puede venderse solo si la politica del tenant lo permite.

### 5.2.1 Recursos Humanos

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `labor_area` | `hr-service` | RH con permisos `hr.area.*` | RH, Produccion y Costos por contrato | `hr.area.updated` futuro |
| `labor_position` | `hr-service` | RH con permisos `hr.position.*` | RH, Produccion y Costos por contrato | `hr.position.updated` futuro |
| `worker` | `hr-service` | RH con permisos `hr.worker.*` | RH; Produccion mediante proyeccion elegible | `hr.worker.updated` futuro |

Reglas:

- El entitlement `hr` debe estar activo para toda operacion del servicio.
- Produccion y Costos nunca escriben tablas del esquema `hr`.
- Las recetas conservan snapshots; los IDs de RH son referencias externas, no FKs entre esquemas de servicio.
- Produccion valida responsables contra la proyeccion HTTP de trabajadores elegibles y conserva `worker_ref_id` mas nombre snapshot; nunca lee ni escribe `hr.workers` directamente.

### 5.3 Almacenes

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `warehouse` | `inventory-service` | Almacenes autorizados | Produccion, Ventas, Reportes | `warehouse.created`, `warehouse.updated` |
| `warehouse_location` | `inventory-service` | Almacenes autorizados | Almacenes, Produccion, Ventas | `warehouse_location.updated` |
| `inventory_item` | `inventory-service` | Almacenes autorizados | Produccion, Ventas, Reportes | `inventory_item.created`, `inventory_item.updated` |
| `inventory_movement` | `inventory-service` | Almacenes; Produccion/Ventas solicitan por contrato | Almacenes, Reportes, Costos futuro | `inventory_movement.recorded`, `inventory_movement.reversed` |
| `inventory_balance_view` | `inventory-service` | Calculado desde movimientos | Produccion, Ventas, Reportes | No aplica como entidad fuente |
| `kardex_view` | `inventory-service` | Calculado desde movimientos | Almacenes, Auditoria, Reportes | No aplica como entidad fuente |
| `inventory_reservation` | `inventory-service` | Almacenes; Ventas/Produccion solicitan por contrato | Ventas, Produccion, Reportes | `inventory_reservation.created`, `inventory_reservation.released`, `inventory_reservation.consumed` |
| `lot` | `inventory-service` | Almacenes autorizados | Produccion, Ventas si aplica | `lot.created`, `lot.blocked`, `lot.released` |

Reglas:

- Kardex y existencias no se editan manualmente.
- Todo cambio de saldo nace de un movimiento.
- Salidas y ajustes negativos no deben exceder existencia disponible.
- Reservas para ordenes de Produccion y Pedidos de Ventas estan implementadas en codigo Local mediante comandos de reserva, liberacion y consumo parcial/total; QA conserva el corte anterior hasta su promocion.

### 5.4 Ventas

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `customer` | `sales-service` | Ventas autorizadas | Ventas, Reportes, Contabilidad futuro | `customer.created`, `customer.updated`, `customer.status_changed` |
| `customer_contact` | `sales-service` | Ventas autorizadas | Ventas | `customer_contact.updated` |
| `quote` | `sales-service` | Ventas autorizadas | Ventas, Reportes | `quote.created`, `quote.approved`, `quote.expired` |
| `quote_line` | `sales-service` | Ventas autorizadas | Ventas | Incluido en eventos de `quote` |
| `sales_order` | `sales-service` | Ventas autorizadas; una por cotizacion aprobada; estados durables de surtido/cancelacion | Ventas, Produccion, Almacenes, Reportes | Auditoria Local; eventos outbox futuros |
| `sales_order_line` | `sales-service` | Ventas; snapshots y referencias externas de producto/articulo | Ventas, Produccion, Almacenes | Incluido en auditoria del pedido |
| `delivery` | `sales-service` | Ventas autorizadas; reserva cantidad de la partida y confirma bajo reclamo durable | Ventas, Almacenes | Auditoria Local; eventos outbox futuros |
| `return_request` | `sales-service` futuro | Planeado | Ventas, Almacenes futuro | Eventos planeados |

Reglas:

- Una cotizacion debe relacionarse con cliente existente.
- Una cotizacion debe usar productos/servicios existentes de Produccion.
- Un pedido puede solicitar produccion o inventario, pero no modifica directamente ordenes ni movimientos; usa comandos HTTP idempotentes del dueno.
- Una partida de producto solo puede reservar el articulo mapeado por Production. Sales conserva snapshots, mientras Inventory mantiene ownership del maestro, reserva, movimiento y costo de consumo.
- Entregas Local reservan cantidad comercial al crear el borrador y consumen reservas mediante Inventory al confirmar. Servicio exige captura de costo real; Production queda pendiente hasta su callback.
- Surtido, cancelacion y confirmacion guardan reclamo, clave y hash antes del efecto externo; una interrupcion queda visible como `needs_reconciliation` y reanuda con la clave original.

### 5.5 Billing / SaaS

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `plan` | `billing-service` | EsLaClave | Web comercial, Admin interno | `plan.created`, `plan.updated` |
| `subscription` | `billing-service` | Billing por pago o activacion manual | Admin, Provisioning | `billing.subscription.active`, `billing.subscription.past_due`, `billing.subscription.cancelled` |
| `payment_event` | `billing-service` | Webhook de proveedor de pago | Billing, Auditoria | `payment_event.received`, `payment_event.processed`, `payment_event.failed` |
| `manual_activation` | `billing-service` | Equipo interno autorizado | Billing, Admin interno | `manual_activation.approved` |
| `invoice_reference` | `billing-service` | Billing o integracion fiscal futura | Admin interno | `invoice_reference.created` |

Reglas:

- El pago en linea debe validarse por webhook firmado.
- La activacion manual debe registrar responsable, motivo, plan, vigencia y modulos.
- Billing no crea tenants directamente; solicita provisioning.

### 5.6 Provisioning

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `provisioning_request` | `provisioning-service` | Billing o Admin interno | Admin interno, Auditoria | `tenant.provisioning.started`, `tenant.provisioning.completed`, `tenant.provisioning.failed` |
| `provisioning_step` | `provisioning-service` | Provisioning | Admin interno, Auditoria | `tenant.provisioning.step_completed`, `tenant.provisioning.step_failed` |

Reglas:

- Provisioning debe ser idempotente por `subscription_id` o `manual_activation_id`.
- Si falla a mitad, debe poder reintentarse sin duplicar tenant ni usuario admin.
- Debe crear tenant mediante contrato de `admin-service`.

### 5.7 Integraciones

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `api_client` | `integration-service` | Administrador tecnico del tenant | Admin, Auditoria | `api.client.created`, `api.client.disabled` |
| `api_scope` | `integration-service` | EsLaClave como catalogo; tenant asigna permitidos | Gateway, Admin | `api.scope.updated` |
| `api_usage` | `integration-service` | Gateway o middleware de API | Billing, Admin, Reportes | `api.usage.recorded`, `api.usage.limit_exceeded` |
| `api_credential_rotation` | `integration-service` | Administrador tecnico del tenant | Auditoria | `api.credential.rotated` |

Reglas:

- Cada API client pertenece a un `tenant_id`.
- Cada llamada debe validar scope, tenant, estado del cliente API y cuota.
- Las APIs externas nunca deben resolver tenant solo por parametro de URL.

---

## 6. Contratos iniciales entre servicios

### 6.1 Tipos de contrato

| Tipo | Uso | Ejemplo |
|---|---|---|
| Query HTTP | Consultar informacion sin cambiar estado | Ventas consulta productos activos. |
| Command HTTP | Solicitar una accion con validacion del dueno | Ventas solicita crear orden de produccion. |
| Event Pub/Sub | Notificar algo que ya ocurrio | Produccion publica orden terminada. |
| Internal policy check | Validar tenant, permiso o modulo activo | Cualquier servicio valida permisos. |

Regla:

> Si cambia estado, el servicio dueno debe ejecutar la regla y emitir el evento.

### 6.2 Administracion hacia todos

| Contrato | Tipo | Consumidores | Proposito |
|---|---|---|---|
| `GET /v1/tenants/{tenant_id}` | Query HTTP | Todos | Validar existencia, estado y plan del tenant. |
| `GET /v1/tenants/{tenant_id}/entitlements` | Query HTTP | Todos | Conocer modulos activos y limites. |
| `POST /v1/policy/evaluate` | Internal policy check | Todos | Validar accion, modulo, recurso y alcance del usuario. |
| `tenant.modules.updated` | Event Pub/Sub | Todos | Reaccionar a activacion o desactivacion de modulos. |
| `tenant.suspended` | Event Pub/Sub | Todos | Bloquear escrituras del tenant segun politica. |

Payload minimo de `POST /v1/policy/evaluate`:

```json
{
  "tenant_id": "tenant_123",
  "actor_id": "user_456",
  "module": "production",
  "resource": "recipe",
  "action": "approve",
  "scope": {
    "business_unit_id": "bu_001"
  }
}
```

### 6.3 Produccion y Almacenes

| Contrato | Tipo | Quien llama | Dueno ejecutor | Proposito |
|---|---|---|---|---|
| `POST /v1/inventory/availability-checks` | Query HTTP | Produccion | Almacenes | Validar materiales para receta u orden. |
| `POST /v1/inventory/reservation-requests` | Command HTTP Local | Produccion | Almacenes | Reservar material disponible por almacen para una orden. |
| `POST /v1/inventory/reservations/{id}/release` | Command HTTP Local | Produccion | Almacenes | Liberar una reserva al cancelar o compensar una orden. |
| `POST /v1/inventory/reservations/{id}/consume` | Command HTTP Local | Produccion | Almacenes | Convertir la reserva en salida inmutable y conservar su valuacion. |
| `POST /v1/inventory/consumption-requests` | Command HTTP planeado | Produccion | Almacenes | Solicitar consumo directo sin reserva; no implementado. |
| `GET /v1/inventory/finished-goods-receipts` | Query HTTP Local | Almacenes UI | Almacenes | Consultar cantidades recibidas por orden terminada. |
| `POST /v1/inventory/finished-goods-receipts` | Command HTTP Local | Almacenes UI | Almacenes | Confirmar recepcion fisica total o parcial de una orden terminada. |
| `inventory_movement.recorded` | Event Pub/Sub | Almacenes | Almacenes | Notificar movimiento registrado. |
| `production_order.completed` | Event Pub/Sub | Produccion | Produccion | Notificar orden completada para flujos futuros. |

Payload minimo de disponibilidad:

```json
{
  "tenant_id": "tenant_123",
  "source": "production_order",
  "source_id": "po_789",
  "items": [
    {
      "inventory_item_id": "item_001",
      "quantity": 10,
      "unit": "kg"
    }
  ]
}
```

Reglas:

- Produccion no descuenta inventario.
- Almacenes no decide si una orden se libera; solo responde disponibilidad o registra movimientos solicitados.
- Toda solicitud debe incluir `source`, `source_id` e idempotency key.
- La primera entrada de la orden a `in_progress` solicita el consumo de cada reserva; Inventory conserva ownership, usa el almacen de esa reserva y crea una sola salida inmutable. Reanudar o completar no repite la solicitud.

### 6.4 Ventas y Produccion

| Contrato | Tipo | Quien llama | Dueno ejecutor | Proposito |
|---|---|---|---|---|
| `GET /v1/production/product-services` | Query HTTP | Ventas | Produccion | Listar productos/servicios activos vendibles. |
| `GET /v1/production/product-services/{id}/cost-summary` | Query HTTP | Ventas | Produccion | Consultar costo estandar estimado. |
| `POST /v1/production/order-requests` | Command HTTP | Ventas | Produccion | Solicitar orden bajo pedido. |
| `production_order.created` | Event Pub/Sub | Produccion | Produccion | Notificar que se creo orden relacionada con pedido. |
| `production_order.status_changed` | Event Pub/Sub | Produccion | Produccion | Actualizar visibilidad en pedido o entrega futura. |

Payload minimo para solicitud de orden:

```json
{
  "tenant_id": "tenant_123",
  "sales_order_id": "so_1001",
  "sales_order_line_id": "sol_01",
  "product_service_id": "ps_001",
  "quantity": 50,
  "unit": "pieza",
  "requested_due_date": "2026-07-15"
}
```

Reglas:

- Ventas solicita, Produccion decide si puede crear la orden.
- La orden creada debe conservar referencia externa al pedido, pero su ciclo de vida lo controla Produccion.
- Si no existe receta aprobada, Produccion debe rechazar o dejar pendiente segun politica configurada.

### 6.5 Ventas y Almacenes

| Contrato | Tipo | Quien llama | Dueno ejecutor | Proposito |
|---|---|---|---|---|
| `POST /v1/inventory/availability-checks` | Query HTTP | Ventas | Almacenes | Validar producto terminado disponible. |
| `POST /v1/inventory/reservation-requests` | Command HTTP Local | Ventas | Almacenes | Solicitar reserva de producto terminado. |
| `POST /v1/inventory/shipment-requests` | Command HTTP futuro | Ventas | Almacenes | Solicitar salida por entrega. |
| `POST /v1/inventory/return-receipts` | Command HTTP futuro | Ventas | Almacenes | Solicitar entrada por devolucion. |
| `inventory_reservation.created` | Event Pub/Sub futuro | Almacenes | Almacenes | Notificar reserva generada. |
| `inventory_movement.recorded` | Event Pub/Sub | Almacenes | Almacenes | Notificar salida, entrada o devolucion. |

Reglas:

- En MVP inicial, pedidos pueden quedar como "pendiente de validar inventario" si reservas reales no estan habilitadas.
- Ventas no modifica existencias.
- Entregas no deben descontar inventario hasta que Almacenes confirme movimiento.

### 6.6 Billing, Provisioning y Administracion

| Contrato | Tipo | Quien llama | Dueno ejecutor | Proposito |
|---|---|---|---|---|
| `POST /v1/billing/webhooks/payment-provider` | Command HTTP | Proveedor pago | Billing | Recibir evento firmado de pago. |
| `POST /v1/provisioning/tenant-requests` | Command HTTP | Billing | Provisioning | Solicitar alta de tenant por suscripcion o activacion manual. |
| `POST /v1/admin/tenants` | Command HTTP interno | Provisioning | Administracion | Crear tenant. |
| `POST /v1/admin/tenants/{tenant_id}/admin-invitations` | Command HTTP interno | Provisioning | Administracion | Invitar administrador inicial. |
| `billing.subscription.active` | Event Pub/Sub | Billing | Billing | Notificar suscripcion activa. |
| `tenant.provisioning.completed` | Event Pub/Sub | Provisioning | Provisioning | Notificar tenant listo. |
| `tenant.admin.invited` | Event Pub/Sub | Administracion | Administracion | Notificar invitacion enviada. |

Reglas:

- No se envian contrasenas por correo.
- La activacion manual debe producir el mismo contrato que un pago confirmado.
- Provisioning debe reintentar sin duplicar tenant.

---

## 7. Contratos de lectura entre modulos

Estas lecturas son necesarias para el MVP, pero no transfieren ownership.

| Consumidor | Lee de | Datos permitidos |
|---|---|---|
| Ventas | Produccion | Productos/servicios activos, unidad, precio objetivo si existe, costo estandar resumido. |
| Produccion | Almacenes | Disponibilidad de articulos inventariables, almacenes sugeridos, faltantes. |
| Almacenes | Produccion | Referencia de orden, producto terminado esperado, unidad y cantidad. |
| Produccion | Administracion | Permisos, modulos activos, centros de negocio. |
| Almacenes | Administracion | Permisos, modulos activos, centros de negocio. |
| Ventas | Administracion | Permisos, modulos activos, centros de negocio. |
| Billing | Administracion | Tenant existente, estado y modulos activos. |

Regla:

> Leer no significa poseer. Si el dato cambia, lo cambia el servicio dueno.

---

## 8. Eventos MVP sugeridos

### Administracion

- `tenant.created`
- `tenant.suspended`
- `tenant.reactivated`
- `tenant.modules.updated`
- `user.invited`
- `user.activated`
- `role.updated`

### Produccion

- `product_service.created`
- `product_service.updated`
- `recipe_version.approved`
- `recipe_version.obsoleted`
- `production_order.created`
- `production_order.status_changed`
- `production_order.completed`

### Almacenes

- `inventory_item.created`
- `inventory_item.updated`
- `inventory_movement.recorded`
- `inventory_movement.reversed`
- `inventory_reservation.created`
- `inventory_reservation.released`

### Ventas

- `customer.created`
- `quote.created`
- `quote.approved`
- `sales_order.created`
- `sales_order.status_changed`
- `sales_order.fulfillment_requested`

### Billing / Provisioning

- `billing.subscription.active`
- `billing.subscription.past_due`
- `billing.subscription.cancelled`
- `manual_activation.approved`
- `tenant.provisioning.started`
- `tenant.provisioning.completed`
- `tenant.provisioning.failed`

### Integraciones

- `api.client.created`
- `api.client.disabled`
- `api.usage.recorded`
- `api.usage.limit_exceeded`

---

## 9. Estructura minima de eventos

Todo evento debe incluir:

```json
{
  "event_id": "evt_001",
  "event_type": "production_order.created",
  "event_version": "1.0",
  "tenant_id": "tenant_123",
  "occurred_at": "2026-06-16T12:00:00Z",
  "source_service": "production-service",
  "idempotency_key": "production_order.created:po_789:v1",
  "correlation_id": "corr_abc",
  "actor": {
    "type": "user",
    "id": "user_456"
  },
  "payload": {}
}
```

Reglas:

- `event_id` es unico.
- `event_version` permite evolucionar payloads.
- `tenant_id` es obligatorio salvo eventos globales justificados.
- `correlation_id` conecta flujo completo entre servicios.
- `idempotency_key` evita duplicados por reintento.

---

## 10. Politica de errores entre servicios

Los contratos HTTP deben responder errores consistentes.

| Codigo | Uso |
|---|---|
| `400` | Datos invalidos o regla de negocio incumplida. |
| `401` | Sin autenticacion valida. |
| `403` | Usuario, API client o tenant sin permiso. |
| `404` | Recurso no existe dentro del tenant autorizado. |
| `409` | Conflicto de estado, duplicado o idempotencia incompatible. |
| `422` | Solicitud entendible pero semanticamente invalida. |
| `429` | Limite de llamadas o cuota excedida. |
| `500` | Error interno no controlado. |
| `503` | Servicio temporalmente no disponible. |

Respuesta base:

```json
{
  "error": {
    "code": "RECIPE_NOT_APPROVED",
    "message": "La receta no esta aprobada para generar ordenes.",
    "correlation_id": "corr_abc",
    "details": {}
  }
}
```

---

## 11. Reglas anti-acoplamiento

Queda prohibido:

- que Ventas escriba ordenes de Produccion directamente;
- que Produccion descuente inventario directamente;
- que Almacenes modifique recetas;
- que Billing cree usuarios o tenants sin Provisioning/Admin;
- que cualquier modulo lea datos de otro tenant;
- que un microfrontend importe codigo interno de otro microfrontend;
- que una API externa opere sin scope, tenant y auditoria;
- que una regla critica exista solo en frontend.

---

## 12. Resultado esperado

Con este ownership definido, el siguiente documento debe convertir estas entidades y reglas en modelo de datos:

```text
docs/arquitectura/modelo_datos_mvp.md
```

Estado: definido en `docs/arquitectura/modelo_datos_mvp.md`.

Despues, los contratos de esta guia deben convertirse en especificacion inicial de APIs:

```text
docs/arquitectura/apis_mvp.md
```

Estado: definido en `docs/arquitectura/apis_mvp.md`.
