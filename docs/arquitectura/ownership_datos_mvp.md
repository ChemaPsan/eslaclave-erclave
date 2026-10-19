# ERClave - Ownership de datos y contratos MVP

## CC-15 · CHG-319 · Local

[Compras por División](cont_08_compras_contexto.md): Purchasing conserva contexto de requisición/OC/recepción y condiciones explícitas del proveedor congeladas. Admin autoriza; Inventory conserva validación/costo/proof CC-14. Migración `20261012_0058` nullable sin backfill, downgrade protegido con historia. Accounting apagado, sin QA; CC-16 implementado Local CHG-320; CC-17/18 y CC-19/20 abiertos.

## CC-14 · CHG-317 · Local

[Productores, transferencias y sobrantes](cont_08_inventario_productores.md) implementados: Inventory conserva contexto/costo de Purchasing/Maintenance y transferencias misma Sociedad; proofs autenticados, alcance y reintentos. Migración `20261012_0057` nullable sin backfill, downgrade protegido con historia. Sin QA ni Accounting; CC-16 integral y CC-19/20 siguen abiertos; CC-15 implementado CHG-319.



## Estado y fuentes de vigencia

La conciliación por submódulo vive en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md); [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md) distingue Local de QA y [PENDIENTES](../contexto/PENDIENTES.md) fija la continuación. Evidencia de cada corte en [TRAZABILIDAD](../../TRAZABILIDAD.md). No sumar pendientes históricos como trabajo nuevo.

Organización/sesión, [centros CONT-05](cont_05_catalogo_centros.md), asignaciones CONT-07 y [condiciones explícitas sin herencia](cont_07_commercial_condiciones.md) ya están implementados Local. CONT-04 es parcial y CONT-06 sigue abierto. CONT-08 conserva [cotización](cont_08_cotizaciones_contexto.md) → [pedido](cont_08_pedidos_contexto.md), [servicios](cont_08_servicios_contexto.md), [stock/entrega y movimientos manuales](cont_08_stock_contexto.md). [Producción manual CHG-313](cont_08_produccion_contexto.md) y [fabricación comercial CHG-315](cont_08_fabricacion_contexto.md) conectan contexto, recursos, recepción y entrega/costo; recorrido HTTP Local real aprobado, aceptación transversal CC-20 pendiente.

Política CHG-309 confirmada: costos y tarifas en moneda base de Sociedad; documento en otra moneda conserva original, tasa explícita y convertido. Compras CC-15 implementado Local CHG-319; Mantenimiento CC-16 implementado Local CHG-320; Servicios CHG-314 y productores Inventory CHG-317 se conservan; no reinterpretar historia. Analítica Costing y Accounting permanecen planned. Datos reales y aceptación integrada siguen abiertos; estos cortes no fueron promovidos a QA.

## Integración operativa vigente CHG-313/314

[Tarifas CC-10](cont_08_tarifas_capacidad.md), [orden manual CC-11](cont_08_produccion_contexto.md) y [moneda Servicios CC-08](cont_08_servicios_contexto.md) se conservan. CHG-315 conecta [fabricación comercial CC-12](cont_08_fabricacion_contexto.md): prueba Sales, conversión única, conciliación de recepción real y entrega/costo. Head Local0056, sin backfill; recorrido HTTP real aprobado con 60MXN→3USD y limpieza de fixtures verificada. Cada dueño escribe sus tablas; Admin autoriza. Accounting apagado, datos reales CC-19/aceptación transversal CC-20 y QA pendientes.

## Registro de cortes (evidencia histórica)

Los apartados fechados conservan el alcance de su corte; los números de revisión y pendientes citados no son el estado actual.

## Actualización CHG-308 · 2026-10-07

Production conserva contexto de documentos/intentos de creación; Admin autoriza. Prueba mínima prepara integración Inventory sin escribir su schema. Tarifas y recursos conservan dueño; costos históricos sin moneda no se reinterpretan. Ver docs/arquitectura/cont_08_produccion_contexto.md.


## Actualización CHG-307 · 2026-10-05

Admin conserva Sociedad/moneda; Inventory costo original, almacén y existencias; Sales congela tipo de cambio y registra costo convertido del pedido. Production sólo valida elegibilidad de producto. Sin escritura entre dueños ni activación contable. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


## Actualización CHG-306 · 2026-10-05

Inventory consulta contexto mínimo de Sales y posee snapshots de reservas/salidas; Admin autoriza scope. Sin escritura ni FK cruzada. Surtimiento dimensionado sigue bloqueado; política monetaria pendiente. Ver cont_08_reservas_contexto.md.


## Actualización CHG-305 · 2026-10-05

Sales conserva ejecución/costos operativos y contexto fijo. HR/Production sólo autorizan elegibilidad HTTP; no se activa Accounting ni analítica Costing.


## Actualización CHG-304 · 2026-10-05

Sales conserva contexto de pedido copiado de cotización; servicios obtienen contexto del pedido. Admin/HR/Production autorizan por HTTP sin escrituras cruzadas. No hay ejecución downstream dimensionada todavía.


## Actualización CHG-303 · 2026-10-05

Sales posee snapshot de cotización. Admin autoriza estructura; RH/Production responden elegibilidad por HTTP. Sin FKs ni escrituras entre servicios.





## CONT-03 / CHG-293 — alcance organizacional

Admin posee `memberships.metadata.scope` v2, revisión, equivalencias y auditoría de concesiones. Shell conserva sólo preferencia por tenant/usuario; Admin valida División y deriva Sociedad/Emisor. Seeds/onboarding no pueden borrar el alcance existente. La persistencia y filtrado de documentos sigue perteneciendo a cada servicio en CONT-07/08; Costing/Accounting no se activan por este corte. [Contrato](cont_03_sesion_alcances.md).

## CONT-02 / CHG-292 — contratos y escritores de organización

Admin es dueño de los formularios, APIs y tablas de Emisor/Sociedad/División, marcador de autoridad, snapshots y proyección heredada. El JSON deja de ser un escritor independiente al activar la estructura; los endpoints deprecados usan el adaptador del servicio. No hay escrituras ni FK a otros schemas. Costing y Accounting conservan sus responsabilidades futuras; sesión/scopes son CONT-03. [Detalle de contratos y límites](cont_02_administracion_organizacional.md).

## Organización y dimensiones CHG-289

Admin posee Emisores, Sociedades, Divisiones y sus equivalencias/importaciones; CONT-01 incorpora esta persistencia sólo en Local, conservando el JSON como autoridad operativa durante la expansión. Un Emisor puede tener varias Sociedades; cada Sociedad tiene un solo Emisor. Accounting será dueño de libros por Sociedad, con moneda base inicialmente MXN; no de libros por Emisor. Costing conserva el catálogo de Centros de costos, con alta solicitada desde Administración mediante contrato y pertenencia obligatoria a División. En CONT-01 estaban pendientes pantalla, scopes, asignaciones y afectaciones. CONT-02 implementa pantalla/API; scopes y afectaciones siguen en sus cortes. No hay escrituras cruzadas. Ver [CONT-01](cont_01_estructura_organizacional.md) y [plan vigente](plan_preparacion_contabilidad.md).

## Entrega previa de materiales CHG-264

CHG-264 implementa en Local y QA la salida completa de materiales desde Movimientos antes de iniciar `in_progress`. Liberar conserva reservas; Almacen confirma entrega con `inventory.movement.create`; Produccion valida cantidades/costos confirmados al iniciar y no consume al iniciar/reanudar. Aplica a productos y servicios con receta, sin agregar materiales a las ordenes comerciales de servicio de Sales. Detalle y matriz API: `docs/auditorias/materiales_produccion_movimientos_2026-09-08.md`.

## Entrega de refacciones Local CHG-263

La UI de Almacenes compone en Movimientos una proyeccion minima de solicitudes pertenecientes a Maintenance. La confirmacion/rechazo del almacenista entra al servicio propietario de la solicitud con su permiso Inventory; Maintenance orquesta los comandos HTTP de Inventory, sin escribir su schema. Inventory conserva stock, costo, reserva y salida; Maintenance conserva estado de solicitud, IDs de movimientos y auditoria del actor, receptor y motivo. La resolucion tecnica queda separada del movimiento fisico.

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
| `sales-service` | Ventas | Local y QA: clientes, contactos, cotizaciones, pedidos, surtido y entregas. El corte CHG-255, ya desplegado en QA, agrega Ordenes de servicio; devoluciones permanecen planeadas. |
| `purchasing-service` | Compras | Local y QA: proveedores, requisiciones, ordenes, recepciones comerciales y reconciliacion con Inventory; El corte CHG-255, ya desplegado en QA, agrega servicios sin movimiento fisico. |
| `maintenance-service` | Mantenimiento | Local y QA: ordenes correctivas, asignaciones, tiempos, solicitudes internas de refacciones y estado de sus efectos. |
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
- Reservas para ordenes de Produccion y Pedidos de Ventas estan implementadas en Local y QA mediante comandos de reserva, liberacion y consumo parcial/total. Cada ambiente conserva datos aislados y QA solo recibe capturas UAT autorizadas.

### 5.4 Compras (primer corte Local)

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `supplier` | `purchasing-service` | Compras autorizadas | Perfil comercial, contacto y fiscal editable; Compras, Gastos y Reportes futuros | `purchasing.supplier.updated` planeado |
| `purchase_requisition` | `purchasing-service` | Solicitante y aprobador mediante permisos puntuales | Compras, Produccion/Inventory por referencia | `purchasing.requisition.created` planeado |
| `purchase_order` | `purchasing-service` | Comprador autorizado | Compras, Inventory, Gastos y Reportes futuros | `purchasing.order.issued` planeado |
| `purchase_receipt` | `purchasing-service` | Receptor autorizado | Compras, Inventory, Gastos futuro | `purchasing.receipt.completed` planeado |
| `inventory_movement` de recepcion | `inventory-service` | Inventory por comando idempotente solicitado por Compras | Compras conserva solo referencia/resultado | `inventory.movement.recorded` |

Reglas:

- Compras no escribe el schema `inventory`; solicita una entrada por contrato y conserva IDs externos.
- Inventory valida articulo, almacen, unidad, cantidad y valuacion fisica. Compras valida proveedor, orden, precio pactado, saldo por recibir y estado comercial.
- Una recepcion que pierde la respuesta despues de confirmar Inventory queda `needs_reconciliation` y reintenta con clave estable; no duplica ni revierte movimientos por SQL cruzado.
- Compras es autoridad del reclamo de saldo y estado de conciliacion; Inventory es autoridad del movimiento. La lectura puntual de almacen y la entrada de compra cruzan exclusivamente por API tenant-safe, nunca por FK o escritura directa.
- Factura, cuenta por pagar, pago, devolucion y asiento permanecen planeados y tendran owners propios.

### 5.5 Ventas

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

### 5.6 Billing / SaaS

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

### 5.7 Provisioning

| Entidad | Servicio dueno | Puede crear/editar | Puede consultar | Eventos principales |
|---|---|---|---|---|
| `provisioning_request` | `provisioning-service` | Billing o Admin interno | Admin interno, Auditoria | `tenant.provisioning.started`, `tenant.provisioning.completed`, `tenant.provisioning.failed` |
| `provisioning_step` | `provisioning-service` | Provisioning | Admin interno, Auditoria | `tenant.provisioning.step_completed`, `tenant.provisioning.step_failed` |

Reglas:

- Provisioning debe ser idempotente por `subscription_id` o `manual_activation_id`.
- Si falla a mitad, debe poder reintentarse sin duplicar tenant ni usuario admin.
- Debe crear tenant mediante contrato de `admin-service`.

### 5.8 Integraciones

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
| `GET /v1/production/finished-goods-candidates[/{id}]` | Query HTTP Local | Almacenes UI/API | Produccion | Entregar solo folio, producto vinculado, cantidad, unidad, estado terminado y costo unitario para recepcion. |
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
- Almacen confirma el consumo de cada reserva desde Movimientos antes de `in_progress`; Inventory conserva ownership, usa el almacen de esa reserva y crea una sola salida inmutable. Iniciar, reanudar o completar no consume.

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
| Almacenes | Produccion | Proyeccion minima de recepcion: referencia de orden, producto terminado vinculado, unidad, cantidad y costo unitario; nunca receta, recursos, responsable ni costos totales. |
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

## 11.1 Ownership implementado de Mantenimiento (Local)

| Entidad o efecto | Owner | Escritura | Consumo |
|---|---|---|---|
| orden, asignacion, tiempo y solicitud interna | `maintenance-service` | usuarios con permisos de Mantenimiento | Mantenimiento y reportes futuros |
| area, puesto, trabajador y elegibilidad | `hr-service` | RH | Mantenimiento por query tenant-safe |
| maquina, estado de maquina y orden productiva | `production-service` | Production mediante comando propietario | Mantenimiento conserva ID/snapshot |
| articulo, almacen, reserva, movimiento y costo | `inventory-service` | Inventory mediante comando propietario | Mantenimiento conserva ID/snapshot/conciliacion |

RH e Inventory son dependencias duras de activacion; Production es integracion opcional. Una ubicacion libre no crea un activo ficticio. Los comandos implementados de bloqueo, liberacion, reserva, consumo y cancelacion son idempotentes; Mantenimiento conserva operacion, intentos y error para reintentar efectos parciales. Devoluciones de sobrantes permanecen planeadas.

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


## Flujo operativo Local CHG-265

Inventory posee transfers, material_returns y reservation_source_rollbacks. Production posee failed_order_creations y material_return_adjustments; Maintenance posee su propia material_return_adjustments; Purchasing conserva receipt/receipt_lines con confirmación por actor. Comunicación de validación/conciliación mediante HTTP, sin FK ni escritura entre schemas.

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.


## Evidencia de servicios CHG-274

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local y QA head `20260913_0036`; release QA `e57237f`, sin aceptación UAT inferida. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.


### Propietario y retención de adjuntos de servicio

Production posee texto, metadatos y objetos privados de la evidencia de sus órdenes. Otros servicios no escriben esas tablas ni acceden directamente al bucket; el consumidor descarga por API autorizada. QA usa `erclave-qa-service-evidence` con acceso uniforme, prevención pública y una única regla Delete age 365, sin versiones, soft delete ni retenciones adicionales. La identidad runtime tiene en ese bucket solamente `storage.buckets.get`, `storage.objects.create`, `storage.objects.get` y `storage.objects.delete`. El backend rechaza con 503 una configuración incompatible.

La retención aplica a todos los adjuntos, no solo fotografías; no elimina evidencia escrita ni orden. La API aplica el vencimiento exacto y el borrado físico usa purga periódica más lifecycle de respaldo. La configuración verificada no certifica por sí misma carga, descarga o aislamiento en QA; consultar los pendientes de smoke y UAT del release.
