# ERClave - APIs MVP

## 1. Objetivo

Este documento define los contratos API iniciales para convertir el modelo de datos MVP en servicios reales.

Aplica a:

- `admin-service`;
- `production-service`;
- `inventory-service`;
- `sales-service`;
- `purchasing-service` (runtime Local en `:8010`; proveedor fiscal, requisicion multipardida y ciclo hasta recepcion implementados, sin despliegue QA/Produccion);
- `maintenance-service` (Local implementado en `8012`; ordenes correctivas, tiempos y refacciones);
- Purchasing Local expone edicion/cancelacion de requisiciones y ordenes, recepcion multipardida y conciliacion manual durable. Inventory aporta `GET /v1/inventory/warehouses/{id}` para validar tenant, estado y destino antes de cada entrada.
- `billing-service`;
- `provisioning-service`;
- `integration-service`.

Mantenimiento expone `GET/POST /v1/maintenance/orders`, lectura/edicion por ID, transiciones idempotentes, tiempos y solicitudes multi-linea de material. RH publica trabajadores con `intervenes_in_maintenance`; Production bloquea/libera maquinas y pausa ordenes; Inventory reserva, consume o libera refacciones. Ninguno admite escritura cruzada ni exito supuesto ante una respuesta incierta.

Estos contratos no sustituyen una especificacion OpenAPI formal. Son la fuente funcional y tecnica para construir los archivos OpenAPI, modelos Pydantic, rutas FastAPI, pruebas de contrato y validadores posteriores.

Diagrama editable:

```text
docs/arquitectura/diagramas/apis_mvp_relaciones.drawio
```

Plan de implementacion relacionado:

```text
docs/arquitectura/plan_implementacion_backend_mvp.md
```

---

## 2. Principios obligatorios

1. Todas las APIs deben usar versionado `/v1`.
2. Toda API operativa debe resolver `tenant_id` desde token, contexto seguro o cliente API autorizado.
3. Ninguna API debe permitir operar datos de otro tenant.
4. Todo endpoint que cambie estado debe validar permisos, modulo activo y reglas backend.
5. Todo endpoint sensible o reintentable debe soportar `Idempotency-Key`.
6. Toda respuesta de lista debe paginar.
7. Toda operacion critica debe auditarse.
8. Todo cruce entre servicios debe usar contrato API o evento, nunca escritura directa a tablas ajenas.
9. Los errores deben seguir formato comun.
10. Los endpoints documentados aqui son MVP; cualquier ampliacion debe actualizar este documento o OpenAPI.

---

## 3. Estandares comunes

### 3.1 Headers requeridos

| Header | Uso |
|---|---|
| `Authorization: Bearer <token>` | Usuario, servicio o API client autenticado. |
| `X-Tenant-Id` | Solo permitido para clientes internos confiables; debe coincidir con permisos del token. |
| `X-Correlation-Id` | Trazabilidad entre servicios. Si no viene, el gateway lo genera. |
| `Idempotency-Key` | Obligatorio en comandos reintentables o con efectos economicos/operativos. |
| `Accept-Language` | Reservado para clientes que lo implementen; el frontend vigente localiza por `error.code` y no depende de este header. |

Regla:

> `X-Tenant-Id` nunca debe ser la unica prueba de tenant. El backend debe validarlo contra token, sesion o API client.

### 3.2 Paginacion

Todas las listas deben aceptar:

```text
limit
cursor
sort
```

Respuesta base:

```json
{
  "data": [],
  "page": {
    "limit": 50,
    "next_cursor": "cursor_siguiente",
    "has_more": true
  }
}
```

Reglas:

- `limit` default: 50.
- `limit` maximo inicial: 200.
- No usar paginacion por pagina numerica para tablas grandes.

### 3.3 Filtros comunes

| Filtro | Uso |
|---|---|
| `q` | Busqueda textual corta. |
| `status` | Filtrar por estatus. |
| `code` | Buscar por codigo exacto o parcial segun endpoint. |
| `created_from` / `created_to` | Rango de creacion. |
| `updated_from` / `updated_to` | Rango de actualizacion. |
| `business_unit_id` | Alcance operativo si aplica. |

### 3.4 Respuesta de recurso

```json
{
  "data": {
    "id": "ps_01J...",
    "tenant_id": "ten_01J...",
    "status": "active",
    "created_at": "2026-06-17T10:00:00Z",
    "updated_at": "2026-06-17T10:00:00Z"
  }
}
```

### 3.5 Errores comunes

`error.code` es el contrato estable consumido por UI y automatizaciones. `message` sirve como diagnóstico del servicio y no se inserta directamente en pantalla; el cliente lo resuelve en ES/EN conforme a `feedback_operativo_y_errores.md`. `correlation_id` debe propagarse y se presenta como referencia sólo cuando el resultado es técnico, inesperado o incierto.

```json
{
  "error": {
    "code": "RECIPE_NOT_APPROVED",
    "message": "La receta no esta aprobada para generar ordenes.",
    "correlation_id": "corr_01J...",
    "details": {}
  }
}
```

| HTTP | Uso |
|---|---|
| `400` | Datos invalidos o regla de negocio incumplida. |
| `401` | Token ausente o invalido. |
| `403` | Sin permiso, modulo inactivo o tenant suspendido. |
| `404` | Recurso no existe dentro del tenant autorizado. |
| `409` | Conflicto de estado, duplicado o idempotencia incompatible. |
| `422` | Solicitud semantica invalida. |
| `429` | Limite de llamadas excedido. |
| `500` | Error interno. |
| `503` | Servicio no disponible. |

### 3.6 Codigos de error iniciales

| Codigo | Servicio |
|---|---|
| `TENANT_NOT_FOUND` | Todos |
| `TENANT_SUSPENDED` | Todos |
| `MODULE_NOT_ENABLED` | Todos |
| `PERMISSION_DENIED` | Todos |
| `IDEMPOTENCY_CONFLICT` | Todos |
| `RESOURCE_NOT_FOUND` | Todos |
| `INVALID_STATUS_TRANSITION` | Todos |
| `DUPLICATE_CODE` | Todos |
| `VALIDATION_ERROR` | Todos |
| `PRODUCT_SERVICE_NOT_ACTIVE` | Produccion/Ventas |
| `RECIPE_NOT_APPROVED` | Produccion |
| `INSUFFICIENT_INVENTORY` | Almacenes |
| `INVENTORY_MOVEMENT_ALREADY_REVERSED` | Almacenes |
| `QUOTE_NOT_APPROVED` | Ventas |
| `PAYMENT_EVENT_ALREADY_PROCESSED` | Billing |
| `PROVISIONING_ALREADY_COMPLETED` | Provisioning |
| `API_SCOPE_DENIED` | Integraciones |
| `API_RATE_LIMIT_EXCEEDED` | Integraciones |
| `PURCHASING_ORDER_NOT_RECEIVABLE` | Compras Local |
| `PURCHASING_RECEIPT_EXCEEDS_OPEN_QUANTITY` | Compras Local |
| `PURCHASING_RECEIPT_NEEDS_RECONCILIATION` | Compras Local |

---

## 4. Autenticacion, autorizacion y permisos

### 4.1 Tipos de actor

| Actor | Descripcion |
|---|---|
| Usuario | Persona autenticada en la app. |
| API client | Integracion externa autorizada por tenant. |
| Servicio interno | Llamada entre servicios con identidad tecnica. |
| Sistema | Jobs, workers o procesos programados. |
| Proveedor externo | Webhook firmado, por ejemplo proveedor de pago. |

### 4.2 Permisos

Formato recomendado:

```text
{module}.{resource}.{action}
```

Ejemplos:

- `production.product_service.read`
- `production.recipe.approve`
- `inventory.movement.create`
- `sales.quote.approve`
- `admin.user.invite`
- `billing.subscription.manage`
- `integrations.api_client.manage`

### 4.3 Validacion obligatoria por endpoint

Cada endpoint debe declarar:

- permiso requerido;
- modulo requerido;
- si requiere tenant activo;
- si requiere `Idempotency-Key`;
- si emite evento;
- si escribe auditoria.

---

## 5. `admin-service`

### 5.1 Responsabilidad

Administra tenants, usuarios, roles, permisos, modulos activos, unidades de negocio y configuracion por tenant.

### 5.2 Endpoints MVP

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET` | `/v1/tenants/{tenant_id}` | interno o `admin.tenant.read` | No | Consultar tenant. |
| `POST` | `/v1/tenants` | interno `provisioning` | Si | Crear tenant desde provisioning. |
| `PATCH` | `/v1/tenants/{tenant_id}` | `admin.tenant.update` | No | Editar datos generales del tenant. |
| `POST` | `/v1/tenants/{tenant_id}/suspend` | `admin.tenant.suspend` | Si | Suspender tenant. |
| `POST` | `/v1/tenants/{tenant_id}/reactivate` | `admin.tenant.reactivate` | Si | Reactivar tenant. |
| `GET` | `/v1/tenants/{tenant_id}/entitlements` | `admin.tenant.read` | No | Consultar modulos y limites del tenant seleccionado. |
| `PUT` | `/v1/tenants/{tenant_id}/entitlements/{module_code}` | interno o `admin.entitlement.manage` | Si | Activar/desactivar modulo. |
| `POST` | `/v1/policy/evaluate` | interno | No | Evaluar permiso y alcance. |
| `GET` | `/v1/users` | `admin.user.read` | No | Listar usuarios del tenant. |
| `POST` | `/v1/users/invitations` | `admin.user.invite` | Si | Invitar usuario. |
| `PATCH` | `/v1/users/{user_id}` | `admin.user.update` | No | Editar usuario. |
| `POST` | `/v1/users/{user_id}/disable` | `admin.user.disable` | Si | Deshabilitar usuario. |
| `GET` | `/v1/roles` | `admin.role.read` | No | Listar roles. |
| `POST` | `/v1/roles` | `admin.role.create` | Si | Crear rol. |
| `PATCH` | `/v1/roles/{role_id}` | `admin.role.update` | No | Editar rol. |
| `GET` | `/v1/permissions` | `admin.role.read` | No | Catalogo tenant-asignable con metadata ES/EN, riesgo y disponibilidad por entitlement. |
| `PUT` | `/v1/roles/{role_id}/permissions` | `admin.role.permissions.manage` | Si | Aplicar asignaciones de un rol con scope, revision esperada y diff auditable. |
| `GET` | `/v1/business-units` | `admin.business_unit.read` | No | Listar unidades de negocio. |
| `POST` | `/v1/business-units` | `admin.business_unit.create` | Si | Crear unidad de negocio. |
| `GET` | `/v1/settings` | `admin.setting.read` | No | Consultar parametros. |
| `PUT` | `/v1/settings/{key}` | `admin.setting.update` | Si | Actualizar parametro. |
| `GET` | `/v1/catalogs/code-sequences` | `admin.setting.read` | No | Consultar configuraciones de folios del tenant. |
| `PATCH` | `/v1/catalogs/code-sequences/{sequence_id}` | `admin.setting.update` | Si | Editar prefijo, separador, siguiente numero, longitud, modo o estatus. |
| `POST` | `/v1/catalogs/code-sequences/{document_type}/next` | permiso de alta del documento consumidor | Si | Reservar el siguiente codigo administrado o validar la captura manual. |

El reemplazo de permisos acepta asignaciones `{permission_id, scope}` y `expected_revision`. El backend bloquea la fila del rol, compara revision, valida clasificacion/asignabilidad y aplica solo agregados, retirados o scopes cambiados. Una revision obsoleta devuelve `409 permission_set_conflict`; reusar `Idempotency-Key` con otro payload devuelve `409 idempotency_key_reused`. El payload legado `permission_ids + scope` es transitorio y no debe usarse por el editor nuevo.

### 5.3 Request ejemplo: crear tenant

```json
{
  "slug": "demo-industrial",
  "commercial_name": "Demo Industrial",
  "legal_name": "Demo Industrial SA de CV",
  "plan_id": "plan_basic",
  "timezone": "America/Mexico_City",
  "locale": "es-MX",
  "source": {
    "type": "provisioning_request",
    "id": "prov_01J..."
  }
}
```

### 5.4 Eventos emitidos

- `tenant.created`
- `tenant.suspended`
- `tenant.reactivated`
- `tenant.modules.updated`
- `user.invited`
- `user.disabled`
- `role.created`
- `role.updated`
- `tenant.setting.updated`

---

## 6. `production-service`

### 6.1 Responsabilidad

Administra productos/servicios, recetas, versiones, recursos productivos, maquinaria, ordenes y avance por etapas.

### 6.2 Endpoints MVP

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET` | `/v1/production/product-services` | `production.product_service.read` | No | Buscar productos/servicios. |
| `POST` | `/v1/production/product-services` | `production.product_service.create` | Si | Crear producto/servicio. |
| `GET` | `/v1/production/product-services/{id}` | `production.product_service.read` | No | Consultar detalle. |
| `PATCH` | `/v1/production/product-services/{id}` | `production.product_service.update` | No | Editar producto/servicio. |
| `PATCH` | `/v1/production/product-services/{id}/status` | `production.product_service.status.update` | Si | Cambiar estatus. |
| `GET` | `/v1/production/product-services/{id}/cost-summary` | `production.product_service.read` | No | Consultar costo estandar resumido. |
| `GET` | `/v1/production/recipes` | `production.recipe.read` | No | Buscar recetas. |
| `POST` | `/v1/production/recipes` | `production.recipe.create` | Si | Crear receta. |
| `GET` | `/v1/production/recipes/{id}` | `production.recipe.read` | No | Consultar receta. |
| `POST` | `/v1/production/recipes/{id}/versions` | `production.recipe.update` | Si | Crear nueva version. |
| `PATCH` | `/v1/production/recipe-versions/{version_id}` | `production.recipe.update` | No | Editar version borrador. |
| `POST` | `/v1/production/recipe-versions/{version_id}/submit` | `production.recipe.submit` | Si | Enviar a aprobacion. |
| `POST` | `/v1/production/recipe-versions/{version_id}/approve` | `production.recipe.approve` | Si | Aprobar version. |
| `POST` | `/v1/production/recipe-versions/{version_id}/obsolete` | `production.recipe.obsolete` | Si | Marcar obsoleta. |
| `POST` | `/v1/production/resource-validations` | `production.order.validate` | Si | Validar recursos para una cantidad, inicio y horizonte de dias productivos; devolver asignacion diaria de mano de obra/maquinaria. |
| `GET` | `/v1/production/orders` | `production.order.read` | No | Buscar ordenes. |
| `POST` | `/v1/production/orders` | `production.order.release` | Si | Validar recursos, reservar y crear la orden ya liberada. |
| `GET` | `/v1/production/finished-goods-candidates[/{id}]` | `inventory.finished_goods_receipt.read` o `.receive` | No | Exponer a Almacenes solo orden terminada, producto vinculado y costo unitario. |
| `GET/POST` | `/v1/production/order-requests` | `production.order.read` / `sales.order.fulfill` | POST | Registrar/listar solicitud de produccion originada por Ventas; no libera una orden automaticamente. |
| `GET` | `/v1/production/orders/{id}` | `production.order.read` | No | Consultar orden. |
| `PATCH` | `/v1/production/orders/{id}/status` | `production.order.release|wait_resources|start|pause|resume|send_to_validation|complete|cancel` | Si | Exigir la capacidad exacta antes de evaluar precondiciones de la transicion. |
| `PATCH` | `/v1/production/orders/{id}/resources/{resource_id}` | `production.order.update` | Si | Registrar cantidad real de mano de obra o maquinaria. |
| `PATCH` | `/v1/production/order-stages/{stage_id}` | `production.order_stage.reset|update|complete|block|skip` | Si | Exigir la capacidad exacta del resultado solicitado. |
| `GET` | `/v1/production/machines` | `production.machine.read` | No | Listar maquinaria. |
| `POST` | `/v1/production/machines` | `production.machine.create` | Si | Crear maquinaria. |
| `PATCH` | `/v1/production/machines/{machine_id}` | `production.machine.update` | No | Editar maquinaria. |

### 6.3 Request ejemplo: crear producto/servicio

```json
{
  "code": "PS-001",
  "name": "Servicio de instalacion",
  "type": "service",
  "category": "Servicios",
  "base_unit": "servicio",
  "target_price": 1500,
  "responsible_area": "Operaciones"
}
```

### 6.4 Request ejemplo: aprobar receta

```json
{
  "approval_notes": "Receta validada para uso operativo.",
  "effective_from": "2026-06-17"
}
```

### 6.5 Request ejemplo: solicitud de orden desde ventas

```json
{
  "sales_order_id": "so_01J...",
  "sales_order_line_id": "sol_01J...",
  "product_service_id": "ps_01J...",
  "quantity": 50,
  "unit": "pieza",
  "requested_due_date": "2026-07-15"
}
```

### 6.6 Reglas backend obligatorias

- Crear receta requiere producto/servicio existente y del mismo tenant.
- Aprobar receta requiere version con recursos y etapas validas.
- Las etapas activas deben tener orden consecutivo y pesos positivos que sumen exactamente 100.
- Editar receta vigente debe crear nueva version o registrar motivo.
- Crear orden requiere receta aprobada.
- Crear orden debe guardar `recipe_snapshot`.
- Crear orden copia peso y area de cada etapa y expone progreso general ponderado.
- Cambiar estatus debe validar transicion.
- Las ordenes en curso no cambian si cambia la receta vigente.

### 6.7 Eventos emitidos

- `product_service.created`
- `product_service.updated`
- `product_service.status_changed`
- `recipe.created`
- `recipe_version.approved`
- `recipe_version.obsoleted`
- `production_order.created`
- `production_order.status_changed`
- `production_order.completed`
- `production_order_stage.status_changed`

---

## 6A. `hr-service`

Es dueno de areas y puestos. Requiere tenant activo, membresia vigente, entitlement `hr` y el permiso exacto.

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET` | `/v1/hr/areas` | `hr.area.read` | No | Listar areas del tenant. |
| `POST` | `/v1/hr/areas` | `hr.area.create` | Si | Crear area independiente. |
| `PATCH` | `/v1/hr/areas/{id}` | `hr.area.update` | Si | Editar o inactivar area. |
| `GET` | `/v1/hr/positions` | `hr.position.read` | No | Listar puestos; admite `area_id` y `production_only`. |
| `POST` | `/v1/hr/positions` | `hr.position.create` | Si | Crear puesto dentro de un area activa existente. |
| `PATCH` | `/v1/hr/positions/{id}` | `hr.position.update` | Si | Editar, mover o inactivar puesto. |
| `GET` | `/v1/hr/production-capacity` | `production.order.validate` o `production.order.release` | No | Calcular capacidad diaria desde trabajadores activos. |

El contrato canonico es `contracts/api/hr-service.openapi.yaml`. Todas las consultas se filtran por tenant y el FK compuesto impide referencias cruzadas.

---

## 7. `inventory-service`

### 7.1 Responsabilidad

Administra almacenes, articulos, ubicaciones, movimientos, existencias, kardex, reservas y lotes.

### 7.2 Endpoints MVP

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET` | `/v1/inventory/warehouses` | `inventory.warehouse.read` | No | Listar almacenes. |
| `POST` | `/v1/inventory/warehouses` | `inventory.warehouse.create` | Si | Crear almacen. |
| `PATCH` | `/v1/inventory/warehouses/{id}` | `inventory.warehouse.update` | No | Editar almacen. |
| `POST` | `/v1/inventory/warehouses/{id}/locations` | `inventory.location.create` | Si | Crear ubicacion. |
| `GET` | `/v1/inventory/items` | `inventory.item.read` | No | Buscar articulos. |
| `POST` | `/v1/inventory/items` | `inventory.item.create` | Si | Crear articulo. |
| `GET` | `/v1/inventory/items/{id}` | `inventory.item.read` | No | Consultar articulo. |
| `PATCH` | `/v1/inventory/items/{id}` | `inventory.item.update` | No | Editar articulo. |
| `POST` | `/v1/inventory/items/{id}/unit-conversion` | `inventory.item.read` | No | Convertir cantidad y costo unitario entre UOM activas compatibles respecto de la unidad base. |
| `GET` | `/v1/inventory/balances` | `inventory.balance.read` | No | Consultar existencias calculadas. |
| `GET` | `/v1/inventory/kardex` | `inventory.kardex.read` | No | Consultar kardex. |
| `GET` | `/v1/inventory/movements` | `inventory.movement.read` | No | Buscar movimientos. |
| `POST` | `/v1/inventory/movements` | `inventory.movement.create` | Si | Registrar movimiento manual. |
| `POST` | `/v1/inventory/movements/{id}/reverse` | `inventory.movement.reverse` | Si | Reversar movimiento. |
| `POST` | `/v1/inventory/availability-checks` | `production.order.validate` o `production.order.release` | Si | Consultar existencia menos reservas y costo promedio. |
| `POST` | `/v1/inventory/consumption-requests` | interno `production` | Si | Registrar consumo solicitado por Produccion. |
| `GET` | `/v1/inventory/finished-goods-receipts` | `inventory.finished_goods_receipt.read` | No | Consultar recepciones agrupadas por orden. |
| `POST` | `/v1/inventory/finished-goods-receipts` | `inventory.finished_goods_receipt.receive` | Si | Confirmar entrada total o parcial usando la proyeccion minima de Produccion. |
| `POST` | `/v1/inventory/reservation-requests` | `production.order.release` | Si | Reservar material por almacen para una orden. |
| `POST` | `/v1/inventory/reservations/{id}/release` | `production.order.cancel`, `sales.order.cancel` o `maintenance.material_request.cancel` | Si | Liberar una reserva desde el comando propietario autorizado. |
| `POST` | `/v1/inventory/reservations/{id}/consume` | `production.order.start|resume`, `sales.delivery.confirm` o `maintenance.order.resolve` | Si | Convertir reserva en salida inmutable desde el comando propietario. |

### 7.3 Request ejemplo: movimiento manual

```json
{
  "movement_type": "positive_adjustment",
  "inventory_item_id": "item_01J...",
  "warehouse_id": "wh_01J...",
  "warehouse_location_id": "loc_01J...",
  "quantity": 10,
  "unit": "pieza",
  "unit_cost": 25.5,
  "reason": "Carga inicial autorizada",
  "source": {
    "type": "manual",
    "id": "initial-load-2026-06"
  }
}
```

### 7.4 Request ejemplo: disponibilidad

```json
{
  "source": {
    "type": "production_order",
    "id": "po_01J..."
  },
  "items": [
    {
      "inventory_item_id": "item_01J...",
      "quantity": 5,
      "unit": "kg"
    }
  ]
}
```

### 7.5 Reglas backend obligatorias

- Kardex y balances no se editan manualmente.
- Todo saldo nace de movimientos.
- Salidas y ajustes negativos no exceden disponible.
- Movimientos registrados no se borran; se reversan.
- Solicitudes externas requieren `source` e `Idempotency-Key`.

### 7.6 Eventos emitidos

- `warehouse.created`
- `inventory_item.created`
- `inventory_item.updated`
- `inventory_movement.recorded`
- `inventory_movement.reversed`
- `inventory_reservation.created`
- `inventory_reservation.released`

---

## 7A. `purchasing-service`

Implementado solo en Local. Es dueno de proveedores, requisiciones multipardida, ordenes de compra y recepciones conciliables; Inventory recibe las entradas mediante contrato.

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET/POST` | `/v1/purchasing/suppliers` | `purchasing.supplier.read|create` | POST | Listar o crear proveedor con perfil fiscal. |
| `PATCH` | `/v1/purchasing/suppliers/{id}` | `purchasing.supplier.update` | Si | Editar maestro y datos fiscales. |
| `GET/POST/PATCH` | `/v1/purchasing/requisitions[/{id}]` | `purchasing.requisition.read|create|update` | Escrituras | Administrar borradores multipardida. |
| `POST` | `/v1/purchasing/requisitions/{id}/{submit|approve|reject|cancel}` | permiso puntual del verbo | Si | Ejecutar cada decision con autoridad independiente. |
| `GET/POST/PATCH` | `/v1/purchasing/orders[/{id}]` | `purchasing.order.read|create|update` | Escrituras | Administrar ordenes y precios por partida. |
| `POST` | `/v1/purchasing/orders/{id}/{issue|cancel}` | `purchasing.order.issue|cancel` | Si | Emitir o cancelar sin borrar evidencia. |
| `GET/POST` | `/v1/purchasing/receipts` | `purchasing.receipt.read|create` | POST | Recibir una o varias partidas en Inventory. |
| `POST` | `/v1/purchasing/receipts/{id}/reconcile` | `purchasing.receipt.reconcile` | Si | Reintentar exclusivamente lineas pendientes. |

## 7B. `maintenance-service`

Implementado solo en Local. Es dueno de la orden correctiva y coordina referencias RH, bloqueo de maquinaria Production y reservas/consumos de refacciones Inventory.

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET/POST/PATCH` | `/v1/maintenance/orders[/{id}]` | `maintenance.order.read|create|update` | Escrituras | Consultar, levantar y documentar una orden. |
| `POST` | `/v1/maintenance/orders/{id}/transitions` | `maintenance.order.request|assign|start|wait_for_parts|resume|resolve|close|reopen|cancel` | Si | Exigir el permiso exacto de la transicion solicitada. |
| `POST` | `/v1/maintenance/orders/{id}/reconcile` | `maintenance.order.reconcile` | Si | Reintentar una operacion externa pendiente. |
| `GET/POST` | `/v1/maintenance/orders/{id}/time-entries` | `maintenance.time.read|create` | POST | Consultar o registrar tiempo del tecnico elegible. |
| `GET/POST` | `/v1/maintenance/orders/{id}/material-requests` | `maintenance.material_request.read|create` | POST | Consultar o reservar solicitud multipardida. |
| `POST` | `/v1/maintenance/material-requests/{id}/cancel` | `maintenance.material_request.cancel` | Si | Liberar reservas activas y cancelar. |
| `POST` | `/v1/maintenance/material-requests/{id}/reconcile` | `maintenance.material_request.reconcile` | Si | Reanudar lineas pendientes con claves estables. |

---

## 8. `sales-service`

### 8.1 Responsabilidad

En el segundo corte Local administra clientes, contactos principales, cotizaciones, pedidos, configuracion de surtido y entregas parciales o totales. Devoluciones permanecen planeadas.

### 8.2 Endpoints MVP

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET` | `/v1/sales/reference-data` | `sales.customer.read` | No | Consultar monedas y condiciones versionadas. |
| `GET` | `/v1/sales/customers` | `sales.customer.read` | No | Buscar clientes. |
| `POST` | `/v1/sales/customers` | `sales.customer.create` | Si | Crear cliente. |
| `GET` | `/v1/sales/customers/{id}` | `sales.customer.read` | No | Consultar cliente. |
| `PATCH` | `/v1/sales/customers/{id}` | `sales.customer.update` | Si | Editar cliente y/o reemplazar contacto principal. |
| `GET` | `/v1/sales/quotes` | `sales.quote.read` | No | Buscar cotizaciones. |
| `POST` | `/v1/sales/quotes` | `sales.quote.create` | Si | Crear cotizacion. |
| `GET` | `/v1/sales/quotes/{id}` | `sales.quote.read` | No | Consultar cotizacion. |
| `PATCH` | `/v1/sales/quotes/{id}` | `sales.quote.update` | Si | Editar y recalcular cotizacion borrador. |
| `POST` | `/v1/sales/quotes/{id}/submit` | `sales.quote.submit` | Si | Marcar cotizada/enviada. |
| `POST` | `/v1/sales/quotes/{id}/approve` | `sales.quote.approve` | Si | Aprobar cotizacion. |
| `POST` | `/v1/sales/quotes/{id}/expire` | `sales.quote.expire` | Si | Marcar vencida. |
| `POST` | `/v1/sales/quotes/{id}/cancel` | `sales.quote.cancel` | Si | Cancelar borrador o cotizacion emitida. |
| `GET/POST` | `/v1/sales/orders` | `sales.order.read/create` | POST | Listar o convertir una cotizacion aprobada una sola vez. |
| `POST` | `/v1/sales/orders/{id}/fulfillment` | `sales.order.fulfill` | Si | Configurar servicio, reservas Inventory o solicitud Production por partida. |
| `POST` | `/v1/sales/orders/{id}/cancel` | `sales.order.cancel` | Si | Cancelar y liberar reservas activas. |
| `GET/POST` | `/v1/sales/deliveries` | `sales.delivery.read/create` | POST | Listar o registrar entrega parcial/total en borrador. |
| `POST` | `/v1/sales/deliveries/{id}/confirm` | `sales.delivery.confirm` | Si | Consumir reservas y recalcular costo/margen real. |
| `POST` | `/v1/sales/deliveries/{id}/cancel` | `sales.delivery.cancel` | Si | Cancelar una entrega borrador. |

La conversion a pedido, el fulfillment y las entregas forman parte del runtime Local desde `20260818_0019`; `20260818_0020` agrega mapeo producto-articulo, reclamos durables, cantidad comprometida y costo real con procedencia. Devoluciones, facturacion y cobranza aun no forman parte del runtime vigente.

### 8.3 Request ejemplo: crear cotizacion

```json
{
  "code": "COT-001",
  "customer_id": "cus_01J...",
  "currency": "MXN",
  "valid_until": "2026-07-17",
  "lines": [
    {
      "product_service_id": "ps_01J...",
      "quantity": 10,
      "unit": "H87",
      "unit_price": 120
    }
  ]
}
```

### 8.5 Reglas backend obligatorias

- Cotizacion requiere cliente activo y responsable RH activo.
- Cotizacion requiere productos/servicios activos, unidad activa igual a su unidad base y partidas no duplicadas.
- Importes, costos snapshot y margen estimado se calculan en backend con aritmetica decimal.
- Solo el borrador es editable; emitir y aprobar revalidan referencias y vigencia.
- Ningun flujo escribe schemas de Admin, RH o Produccion.
- Un producto vendido debe tener un articulo activo de Inventory mapeado por Production y con la misma unidad; Sales no acepta sustituirlo por otro articulo compatible solo por unidad.
- Crear una Entrega serializa Pedido/partidas y descuenta borradores; surtido, cancelacion y confirmacion reclaman estado durable antes de cualquier efecto externo.
- El costo real identifica su fuente: consumo de Inventory o captura operativa de servicio. Production no entrega costo real hasta implementar su callback.

### 8.6 Auditoria y eventos

Los comandos generan `sales.audit_events` e idempotencia persistente. Publicacion outbox/eventos de dominio queda para el corte de integracion posterior.

---

## 9. `billing-service`

### 9.1 Responsabilidad

Administra planes, suscripciones, eventos de pago, activaciones manuales y estado comercial del SaaS.

### 9.2 Endpoints MVP

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET` | `/v1/billing/plans` | publico/controlado | No | Listar planes disponibles. |
| `POST` | `/v1/billing/checkout-sessions` | publico/controlado | Si | Crear sesion de pago. |
| `POST` | `/v1/billing/webhooks/payment-provider` | proveedor firmado | Si | Recibir webhook de pago. |
| `GET` | `/v1/billing/subscriptions` | `billing.subscription.read` | No | Listar suscripciones. |
| `GET` | `/v1/billing/subscriptions/{id}` | `billing.subscription.read` | No | Consultar suscripcion. |
| `POST` | `/v1/billing/manual-activations` | `billing.manual_activation.create` | Si | Crear activacion manual. |
| `POST` | `/v1/billing/manual-activations/{id}/approve` | `billing.manual_activation.approve` | Si | Aprobar activacion manual. |
| `POST` | `/v1/billing/subscriptions/{id}/cancel` | `billing.subscription.cancel` | Si | Cancelar suscripcion. |

### 9.3 Request ejemplo: checkout

```json
{
  "plan_id": "plan_basic",
  "customer_email": "admin@cliente.com",
  "tenant_requested_name": "Cliente Demo",
  "success_url": "https://www.eslaclave.com/checkout/success",
  "cancel_url": "https://www.eslaclave.com/checkout/cancel"
}
```

### 9.4 Request ejemplo: activacion manual

```json
{
  "plan_id": "plan_basic",
  "requested_tenant_name": "Cliente Demo",
  "admin_email": "admin@cliente.com",
  "modules": ["production", "inventory", "sales"],
  "limits": {
    "users": 10,
    "api_calls_month": 0
  },
  "reason": "Contrato firmado fuera de linea"
}
```

### 9.5 Reglas backend obligatorias

- Webhooks deben validar firma del proveedor.
- Eventos de pago se procesan una sola vez.
- Activacion manual requiere responsable, motivo, plan, vigencia y modulos.
- Billing no crea tenants directamente; solicita provisioning.

### 9.6 Eventos emitidos

- `billing.checkout.started`
- `payment_event.received`
- `payment_event.processed`
- `billing.subscription.active`
- `billing.subscription.past_due`
- `billing.subscription.cancelled`
- `manual_activation.approved`

---

## 10. `provisioning-service`

### 10.1 Responsabilidad

Orquesta alta de tenant desde suscripcion activa o activacion manual.

### 10.2 Endpoints MVP

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `POST` | `/v1/provisioning/tenant-requests` | interno `billing` | Si | Solicitar alta de tenant. |
| `GET` | `/v1/provisioning/tenant-requests/{id}` | interno o admin | No | Consultar estado. |
| `POST` | `/v1/provisioning/tenant-requests/{id}/retry` | interno o admin | Si | Reintentar provisioning fallido. |
| `GET` | `/v1/provisioning/tenant-requests/{id}/steps` | interno o admin | No | Consultar pasos. |

### 10.3 Request ejemplo: tenant request

```json
{
  "request_source": "subscription",
  "source_id": "sub_01J...",
  "tenant": {
    "slug": "cliente-demo",
    "commercial_name": "Cliente Demo",
    "timezone": "America/Mexico_City",
    "locale": "es-MX"
  },
  "admin_user": {
    "email": "admin@cliente.com",
    "display_name": "Administrador Cliente"
  },
  "modules": ["production", "inventory", "sales"],
  "limits": {
    "users": 10
  }
}
```

### 10.4 Reglas backend obligatorias

- Debe ser idempotente por `request_source + source_id`.
- Reintentar no debe duplicar tenant ni usuario.
- No enviar contrasenas por correo.
- Crear tenant, entitlements e invitacion mediante `admin-service`.

### 10.5 Eventos emitidos

- `tenant.provisioning.started`
- `tenant.provisioning.step_completed`
- `tenant.provisioning.completed`
- `tenant.provisioning.failed`

---

## 11. `integration-service`

### 11.1 Responsabilidad

Administra clientes API, secretos, scopes, cuotas y uso de integraciones.

### 11.2 Endpoints MVP

| Metodo | Ruta | Permiso | Idempotencia | Proposito |
|---|---|---|---|---|
| `GET` | `/v1/integrations/api-clients` | `integrations.api_client.read` | No | Listar clientes API. |
| `POST` | `/v1/integrations/api-clients` | `integrations.api_client.create` | Si | Crear cliente API. |
| `GET` | `/v1/integrations/api-clients/{id}` | `integrations.api_client.read` | No | Consultar cliente API. |
| `PATCH` | `/v1/integrations/api-clients/{id}` | `integrations.api_client.update` | No | Editar cliente API. |
| `POST` | `/v1/integrations/api-clients/{id}/disable` | `integrations.api_client.disable` | Si | Deshabilitar cliente API. |
| `POST` | `/v1/integrations/api-clients/{id}/secrets` | `integrations.api_client.rotate_secret` | Si | Crear/rotar secreto. |
| `PUT` | `/v1/integrations/api-clients/{id}/scopes` | `integrations.api_client.update` | Si | Reemplazar scopes. |
| `GET` | `/v1/integrations/api-scopes` | `integrations.scope.read` | No | Listar scopes disponibles. |
| `GET` | `/v1/integrations/api-usage` | `integrations.usage.read` | No | Consultar uso de API. |
| `POST` | `/v1/integrations/api-usage` | interno gateway | Si | Registrar uso de API. |

### 11.3 Request ejemplo: crear cliente API

```json
{
  "client_name": "Integracion tienda externa",
  "allowed_origins": ["https://cliente.com"],
  "scopes": [
    "sales.orders.read",
    "inventory.balances.read"
  ],
  "rate_limit": {
    "requests_per_minute": 60,
    "requests_per_month": 10000
  }
}
```

### 11.4 Reglas backend obligatorias

- Secretos nunca se guardan en texto plano.
- Cada cliente API pertenece a un tenant.
- Cada llamada externa valida scope, tenant, estado y cuota.
- Rotar secreto no debe invalidar de golpe integraciones si se define ventana de transicion.

### 11.5 Eventos emitidos

- `api.client.created`
- `api.client.disabled`
- `api.credential.rotated`
- `api.usage.recorded`
- `api.usage.limit_exceeded`

---

## 12. Contratos internos cruzados

### 12.1 Ventas consulta productos de Produccion

```text
GET /v1/production/product-services?q=&status=active&type=
```

Uso:

- cotizaciones;
- pedidos;
- margen estimado.

Regla:

- Ventas puede consultar productos/servicios, pero no editarlos.

### 12.2 Ventas solicita produccion

```text
POST /v1/production/order-requests
```

Uso:

- pedido bajo produccion.

Regla:

- Produccion valida receta aprobada y crea la orden.

### 12.3 Produccion consulta disponibilidad de Almacenes

```text
POST /v1/inventory/availability-checks
```

Uso:

- validar materiales antes de liberar orden.

Regla:

- Almacenes responde disponibilidad; Produccion decide si libera o bloquea orden.

### 12.4 Produccion solicita consumo

```text
POST /v1/inventory/consumption-requests
```

Regla:

- Almacenes registra movimiento; Produccion no descuenta inventario.

### 12.5 Billing solicita Provisioning

```text
POST /v1/provisioning/tenant-requests
```

Regla:

- Billing no crea tenants. Provisioning orquesta.

### 12.6 Provisioning crea tenant en Admin

```text
POST /v1/tenants
POST /v1/users/invitations
PUT /v1/tenants/{tenant_id}/entitlements/{module_code}
```

Regla:

- Admin es fuente de verdad de tenant, usuario y modulos activos.

---

## 13. Eventos y outbox

Todo servicio que cambie estado relevante debe escribir en `audit.outbox_events` dentro de la misma transaccion del cambio.

Estructura minima:

```json
{
  "event_id": "evt_01J...",
  "event_type": "sales_order.created",
  "event_version": "1.0",
  "tenant_id": "ten_01J...",
  "source_service": "sales-service",
  "aggregate_type": "sales_order",
  "aggregate_id": "so_01J...",
  "idempotency_key": "sales_order.created:so_01J...",
  "correlation_id": "corr_01J...",
  "occurred_at": "2026-06-17T10:00:00Z",
  "payload": {}
}
```

Reglas:

- eventos son hechos pasados;
- no deben usarse para pedir permiso;
- deben ser versionados;
- consumidores deben ser idempotentes.

---

## 14. Idempotencia por operacion

| Operacion | Llave sugerida |
|---|---|
| Crear tenant | `tenant:create:{source_type}:{source_id}` |
| Invitar admin inicial | `tenant:{tenant_id}:invite-admin:{email}` |
| Crear producto/servicio | `product_service:create:{tenant_id}:{code}` |
| Aprobar version receta | `recipe_version:approve:{version_id}` |
| Crear orden desde ventas | `production_order:create-from-sales:{sales_order_line_id}` |
| Registrar movimiento externo | `inventory_movement:{source_type}:{source_id}:{source_line_id}:{movement_type}` |
| Convertir cotizacion a pedido | `quote:convert-to-order:{quote_id}` |
| Procesar webhook pago | `payment_event:{provider}:{provider_event_id}` |
| Provisioning request | `provisioning:{request_source}:{source_id}` |
| Registrar uso API | `api_usage:{request_id}` |

Regla:

> Si una operacion puede generar cobro, tenant, orden, movimiento, reserva, pedido o invitacion, debe tener idempotencia.

---

## 15. Seguridad minima por API

- Validar token y tenant en cada request.
- Validar modulo activo por tenant.
- Validar permiso por accion.
- No aceptar `tenant_id` del body como verdad.
- No exponer secretos ni hashes.
- No regresar datos de auditoria sensibles a usuarios no autorizados.
- Enmascarar datos sensibles en logs.
- Validar entrada con Pydantic.
- Usar CORS restrictivo.
- Usar rate limiting en APIs externas.
- Registrar auditoria en acciones criticas.
- Separar credenciales QA y Produccion.

---

## 16. Criterios para OpenAPI

Cada servicio debe generar un archivo:

```text
contracts/api/admin-service.openapi.yaml
contracts/api/production-service.openapi.yaml
contracts/api/inventory-service.openapi.yaml
contracts/api/sales-service.openapi.yaml
contracts/api/billing-service.openapi.yaml
contracts/api/provisioning-service.openapi.yaml
contracts/api/integration-service.openapi.yaml
```

Estado: contratos iniciales creados en `contracts/api/`.

Cada endpoint debe incluir:

- `operationId`;
- tags por recurso;
- parametros de query;
- request body si aplica;
- response `200`/`201`;
- errores `400`, `401`, `403`, `404`, `409`, `422`, `500`;
- header `Idempotency-Key` cuando aplique;
- ejemplo de request y response;
- permisos requeridos en extension `x-permissions`;
- modulo requerido en extension `x-required-module`.

Nota:

- Los dominios en `servers.url` son placeholders hasta comprar/configurar dominio real.
- La implementacion debe tomar el dominio publico desde `ERCLAVE_API_PUBLIC_BASE_URL`.

---

## 17. Criterios de terminado

Este documento se considera suficiente para iniciar OpenAPI cuando:

- cada servicio tiene endpoints MVP;
- cada endpoint declara permiso e idempotencia;
- existen errores comunes;
- existen reglas de paginacion y filtros;
- estan documentados contratos cruzados;
- estan documentadas reglas de seguridad;
- cada operacion critica tiene evento o auditoria;
- ningun endpoint escribe datos de otro servicio.
