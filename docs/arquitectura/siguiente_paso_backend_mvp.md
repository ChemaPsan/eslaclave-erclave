# ERClave - Siguiente paso tecnico para backend MVP

## 1. Decision del arquitecto SaaS

Para llevar los modulos actuales fuera de la maqueta, el siguiente paso recomendado no es iniciar directamente por tablas ni por endpoints.

El mejor siguiente paso es definir el **contrato arquitectonico del backend MVP**:

1. ownership de datos por servicio;
2. entidades canonicas por modulo;
3. limites entre modulos;
4. eventos y comandos entre modulos;
5. criterios multi-tenant;
6. reglas que deben vivir en backend;
7. despues de eso, modelo de datos y APIs.

Esta secuencia evita que la base de datos se vuelva el punto de acoplamiento de todo el ERP y evita que las APIs nazcan como simples pantallas remotas.

---

## 2. Por que no iniciar solo con base de datos

Disenar primero la base ayuda a visualizar datos, pero en un SaaS multi-tenant puede provocar problemas si se hace antes de definir ownership:

- tablas compartidas sin dueno claro;
- servicios escribiendo datos de otros servicios;
- reglas criticas escondidas en frontend;
- dificultad para separar modulos contratados por plan;
- dificultad para escalar a mas tenants;
- APIs creadas alrededor de tablas, no de flujos de negocio.

La base de datos debe surgir de los agregados y reglas de cada modulo, no al reves.

---

## 3. Por que no iniciar solo con listado de APIs

Listar APIs primero tambien es util, pero si no se define antes el modelo funcional puede generar endpoints incompletos o demasiado acoplados:

- endpoints que mezclan Produccion, Almacenes y Ventas en una sola llamada;
- APIs que permiten estados invalidos;
- operaciones sin idempotencia;
- falta de auditoria;
- endpoints que dependen de datos que no son duenos;
- dificultad para versionar contratos.

Las APIs deben representar comandos, consultas y eventos de negocio, no solo formularios del frontend.

---

## 4. Orden recomendado de trabajo

### Paso 1 - Mapa de dominios y ownership

Definir que servicio es dueno de cada entidad.

| Dominio | Servicio dueno | Responsabilidad principal |
|---|---|---|
| Administracion | `admin-service` | Tenants, usuarios, roles, permisos, modulos activos, planes y parametros. |
| Produccion | `production-service` | Productos/servicios, recetas, versiones, recursos productivos, ordenes y avance por etapas. |
| Almacenes | `inventory-service` | Almacenes, articulos inventariables, movimientos, existencias, kardex, reservas y lotes si aplican. |
| Ventas | `sales-service` | Clientes, cotizaciones, pedidos, entregas, devoluciones y condiciones comerciales. |
| Billing / SaaS | `billing-service` | Suscripciones, cobros, planes, activacion comercial y estado de pago. |
| Provisioning | `provisioning-service` | Alta automatica o manual de tenant, modulos iniciales e invitacion del administrador. |

Regla base:

> Un servicio puede consultar contratos de otro servicio, pero no debe escribir directamente en sus tablas.

### Paso 2 - Entidades canonicas MVP

Definir entidades minimas reales para QA, con `tenant_id`, auditoria y estatus.

| Modulo | Entidades MVP |
|---|---|
| Administracion | tenant, user, role, permission, module_entitlement, business_unit, tenant_setting. |
| Produccion | product_service, recipe, recipe_version, recipe_resource, recipe_stage, production_order, production_order_stage, labor_area, labor_role, machine. |
| Almacenes | warehouse, warehouse_location, inventory_item, inventory_movement, inventory_balance_view, kardex_view. |
| Ventas | customer, customer_contact, quote, quote_line, sales_order, sales_order_line, delivery_view. |
| Billing / SaaS | plan, subscription, payment_event, manual_activation, invoice_reference. |
| Integraciones | api_client, api_scope, api_usage. |

### Paso 3 - Reglas criticas en backend

Identificar reglas que nunca deben quedarse solo en frontend.

| Flujo | Regla backend obligatoria |
|---|---|
| Crear receta | El producto o servicio debe existir y pertenecer al mismo tenant. |
| Aprobar receta | Debe tener recursos, etapas y version valida. |
| Editar receta vigente | Debe crear nueva version o registrar motivo de cambio. |
| Crear orden | Debe usar receta aprobada y guardar snapshot de version. |
| Cambiar orden | Debe validar transicion de estatus. |
| Movimiento inventario | No debe permitir salida mayor a existencia disponible. |
| Kardex | Debe generarse desde movimientos, no capturarse manualmente. |
| Cotizacion | Debe usar cliente y producto/servicio existentes. |
| Pedido | Debe originarse desde cotizacion aprobada o flujo autorizado. |
| Tenant | Debe crearse por pago verificado o activacion manual auditada. |
| API externa | Debe validar `client_id`, scope, tenant, cuota e idempotencia. |

### Paso 4 - Contratos entre modulos

Antes de escribir endpoints finales, definir los contratos que cruzan modulos.

| Origen | Destino | Contrato |
|---|---|---|
| Produccion | Almacenes | Consultar disponibilidad de materiales. |
| Produccion | Almacenes | Solicitar consumo de materiales. |
| Produccion | Almacenes | Registrar entrada de producto terminado. |
| Ventas | Produccion | Solicitar orden bajo pedido cuando no haya inventario. |
| Ventas | Almacenes | Consultar disponibilidad de producto terminado. |
| Ventas | Almacenes | Solicitar reserva o salida futura. |
| Billing | Provisioning | Solicitar alta de tenant por suscripcion activa. |
| Provisioning | Administracion | Crear tenant, admin inicial y modulos contratados. |
| Administracion | Todos | Resolver permisos, modulos activos y parametros por tenant. |

### Paso 5 - Modelo de datos inicial

Con ownership y contratos definidos, ahora si se disena:

- esquema PostgreSQL por servicio o por dominio;
- convencion de `tenant_id`;
- claves externas solo dentro del mismo ownership;
- referencias externas por ID estable, no FK directa entre servicios;
- tablas de auditoria;
- migraciones con Alembic;
- datos semilla para catalogos base.

### Paso 6 - APIs iniciales

Despues del modelo, se documentan APIs por servicio:

- OpenAPI por servicio;
- endpoints de comandos;
- endpoints de consulta;
- errores estandar;
- paginacion, busqueda y filtros;
- idempotency keys en operaciones sensibles;
- versionado `/v1`;
- reglas de autenticacion y autorizacion.

---

## 5. Roadmap recomendado

### Fase A - Documento de ownership y modelo conceptual

Entregables:

- mapa de servicios;
- ownership de entidades;
- entidades MVP por modulo;
- dependencias entre modulos;
- reglas de datos multi-tenant.

Resultado esperado:

> Saber quien es dueno de cada dato antes de disenar tablas o endpoints.

### Fase B - Modelo de datos MVP

Entregables:

- ERD conceptual;
- tablas minimas por servicio;
- campos obligatorios;
- indices base;
- auditoria;
- estrategia de migraciones.

Resultado esperado:

> Tener una base lista para implementarse en PostgreSQL sin romper modularidad.

### Fase C - Contratos API MVP

Entregables:

- OpenAPI inicial por servicio;
- listado de comandos y consultas;
- modelos de request/response;
- errores comunes;
- politicas de paginacion, busqueda e idempotencia.

Resultado esperado:

> Poder construir frontend real y backend real contra contratos versionados.

### Fase D - Eventos y flujos cruzados

Entregables:

- eventos MVP;
- payloads versionados;
- criterios de reintento;
- idempotencia;
- compensaciones;
- auditoria.

Resultado esperado:

> Que Produccion, Almacenes, Ventas y Billing se comuniquen sin escribir datos ajenos.

---

## 6. Primer corte recomendado

El primer documento a crear despues de este debe ser:

```text
docs/arquitectura/ownership_datos_mvp.md
```

Estado: definido en `docs/arquitectura/ownership_datos_mvp.md`.

Debe responder:

- que entidad existe;
- que servicio la posee;
- que modulo la muestra;
- que modulo puede consultarla;
- que modulo puede solicitar cambios;
- cual es su `tenant_id`;
- que eventos emite;
- que reglas backend la protegen.

Despues de ese documento, el segundo debe ser:

```text
docs/arquitectura/modelo_datos_mvp.md
```

Estado: definido en `docs/arquitectura/modelo_datos_mvp.md`.

Y el tercero:

```text
docs/arquitectura/apis_mvp.md
```

---

## 7. Criterio de avance

No se debe declarar listo el diseno backend MVP hasta cumplir:

- cada entidad tiene servicio dueno;
- cada tabla futura tiene `tenant_id` o justificacion para no tenerlo;
- cada flujo critico tiene regla backend;
- cada operacion sensible tiene auditoria;
- cada cruce entre modulos usa API o evento;
- ningun modulo escribe datos de otro modulo;
- QA y Produccion pueden desplegarse con recursos separados;
- existe ruta clara para activar o desactivar modulos por plan.
