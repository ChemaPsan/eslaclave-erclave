# ERClave - Plan de implementacion backend MVP

## 1. Objetivo

Este documento define el plan recomendado para pasar ERClave de maqueta navegable a backend real en QA, manteniendo la arquitectura SaaS multi-tenant, modular, segura y auditable.

El plan se basa en:

- `docs/arquitectura/qa_prod.md`;
- `docs/arquitectura/ownership_datos_mvp.md`;
- `docs/arquitectura/modelo_datos_mvp.md`;
- `docs/arquitectura/apis_mvp.md`;
- documentos funcionales de `modulos/`;
- criterios de los agentes transversales en `AGENTES.md`.

La meta no es construir todo el ERP de golpe. La meta es lograr el primer corte real:

> Un tenant en QA puede autenticarse, tener modulos activos, operar datos reales de Produccion, consultar/registrar datos minimos de Almacenes y Ventas, y pasar validadores automatizados.

---

## 2. Principios de implementacion

1. Primero plataforma minima, despues modulos.
2. Primero `admin-service`, porque sin tenant, usuarios, permisos y modulos activos no hay SaaS real.
3. Primero QA real para un tenant, despues venta publica automatizada.
4. No migrar toda la maqueta a backend en un solo movimiento.
5. Cada servicio debe iniciar pequeno, con endpoints MVP y reglas criticas.
6. Cada tabla operativa debe tener `tenant_id`.
7. Cada endpoint que cambie estado debe validar permiso y modulo activo.
8. Cada operacion critica debe tener auditoria.
9. Cada comando reintentable debe usar `Idempotency-Key`.
10. Todo lo que siga siendo mock debe quedar declarado.

---

## 3. Stack inicial aprobado

| Capa | Decision inicial |
|---|---|
| Backend | FastAPI |
| Validacion de datos | Pydantic |
| ORM | SQLAlchemy o SQLModel |
| Migraciones | Alembic |
| Base de datos | PostgreSQL en Cloud SQL |
| Deploy backend | Cloud Run |
| Imagenes | Artifact Registry |
| Secretos | Secret Manager |
| Eventos | Pub/Sub con outbox pattern |
| Observabilidad | Cloud Logging, Monitoring, Trace/Error Reporting |
| CI/CD | GitHub Actions con validadores, build y deploy controlado |
| Frontend inicial | Maqueta actual conectada progresivamente por API |

---

## 4. Estructura inicial del repo

Estructura recomendada para iniciar backend real:

```text
backend/
  README.md
  pyproject.toml
  alembic.ini
  alembic/
    env.py
    versions/
  shared/
    config/
    db/
    auth/
    errors/
    logging/
    audit/
    idempotency/
    pagination/
    tenants/
  services/
    admin-service/
      app/
        main.py
        api/
        models/
        schemas/
        repositories/
        services/
        policies/
        events/
        tests/
    production-service/
    inventory-service/
    sales-service/
    billing-service/
    provisioning-service/
    integration-service/
contracts/
  api/
  events/
```

Regla:

- `backend/shared/` puede contener utilidades tecnicas comunes.
- `backend/shared/` no debe contener reglas de negocio especificas de un modulo.
- Cada servicio conserva sus rutas, modelos, reglas y pruebas.

---

## 5. Fases recomendadas

### Fase 0 - Preparacion documental y validadores ligeros

Objetivo:

Preparar el repo para que la implementacion backend no arranque sin contratos base.

Entregables:

- confirmar `ownership_datos_mvp.md`;
- confirmar `modelo_datos_mvp.md`;
- confirmar `apis_mvp.md`;
- confirmar diagramas `.drawio`;
- crear validador documental ligero para arquitectura backend MVP;
- actualizar README con comandos backend cuando exista scaffolding.

Criterio de salida:

- `npm.cmd run validate` pasa;
- docs base existen;
- trazabilidad registra el cambio;
- no hay decisiones de backend fuera de docs.

Estado:

- Ownership definido.
- Modelo de datos definido.
- APIs MVP definidas.
- Diagramas iniciales definidos.
- Validador documental backend y OpenAPI inicial definido.

### Fase 1 - Scaffolding backend base

Objetivo:

Crear la base tecnica comun para levantar servicios FastAPI en local y QA.

Entregables:

- `backend/pyproject.toml`;
- FastAPI base;
- health check comun:
  - `GET /health`;
  - `GET /ready`;
- configuracion por ambiente:
  - local;
  - QA;
  - Produccion;
- conexion PostgreSQL;
- Alembic inicial;
- manejo comun de errores;
- logging estructurado;
- `correlation_id`;
- middleware de tenant placeholder;
- middleware de auditoria placeholder;
- pruebas basicas de arranque.

Estado inicial:

- scaffolding FastAPI creado para `admin-service`;
- configuracion por ambiente creada en `backend/shared/erclave_common/config.py`;
- dominio/API base configurable por `ERCLAVE_API_PUBLIC_BASE_URL`;
- Alembic inicial creado;
- health checks creados;
- middleware inicial de `correlation_id` y tenant placeholder creado.

Primeros endpoints tecnicos:

```text
GET /health
GET /ready
GET /version
```

Criterio de salida:

- servicio de ejemplo levanta localmente;
- migracion inicial vacia corre;
- pruebas backend base pasan;
- Dockerfile o build definido;
- README indica como correr en Windows y Linux.

### Fase 2 - `admin-service` real

Objetivo:

Crear la fuente de verdad para tenants, usuarios, roles, permisos, modulos activos y configuracion.

Motivo:

Sin `admin-service` no se puede validar multi-tenancy ni permisos de forma real.

Entregables:

- schema `admin`;
- migracion inicial fisica creada en `backend/alembic/versions/20260617_0001_admin_service_initial.py` para:
  - `admin.tenants`;
  - `admin.users`;
  - `admin.roles`;
  - `admin.permissions`;
  - `admin.role_permissions`;
  - `admin.memberships`;
  - `admin.membership_roles`;
  - `admin.tenant_modules`;
  - `admin.audit_events`;
- catalogo seed inicial de modulos MVP en `backend/services/admin-service/app/seeds/catalog.py`;
- seeds de permisos MVP;
- endpoints MVP de `admin-service`;
- `POST /v1/policy/evaluate`;
- tenant demo QA;
- usuario admin demo QA;
- roles iniciales;
- validacion de modulo activo.

Endpoints prioritarios:

```text
GET /v1/tenants/{tenant_id}
POST /v1/tenants
GET /v1/tenants/{tenant_id}/entitlements
PUT /v1/tenants/{tenant_id}/entitlements/{module_code}
POST /v1/policy/evaluate
GET /v1/users
POST /v1/users/invitations
GET /v1/roles
POST /v1/roles
PUT /v1/roles/{role_id}/permissions
```

Criterio de salida:

- cada request operativo puede resolver tenant;
- un usuario demo tiene permisos;
- un modulo puede activarse/desactivarse por tenant;
- otro servicio puede consultar permisos o entitlements;
- auditoria registra acciones criticas.

### Fase 3 - Auditoria e idempotencia base

Objetivo:

Crear mecanismos transversales antes de migrar flujos operativos criticos.

Entregables:

- schema `audit`;
- `audit.audit_log`;
- `audit.outbox_events`;
- middleware/helper de auditoria;
- repositorio de idempotencia o convencion por tabla;
- formato estandar de errores;
- formato estandar de eventos;
- prueba de reintento idempotente.

Criterio de salida:

- una accion critica genera auditoria;
- un evento queda en outbox dentro de la transaccion;
- repetir una operacion con la misma llave no duplica efecto;
- errores devuelven `correlation_id`.

### Fase 4 - `production-service` MVP real

Objetivo:

Migrar el primer modulo operativo real: Produccion.

Entregables:

- schema `production`;
- migraciones de:
  - `product_services`;
  - `recipes`;
  - `recipe_versions`;
  - `recipe_resources`;
  - `recipe_stages`;
  - `production_orders`;
  - `production_order_stages`;
  - `labor_areas`;
  - `labor_roles`;
  - `machines`;
- endpoints MVP de productos/servicios;
- endpoints MVP de recetas/versiones;
- endpoints MVP de ordenes;
- endpoints MVP de areas/roles/maquinaria;
- snapshot de receta al crear orden;
- cambios de estatus validados;
- eventos outbox de produccion.

Endpoints prioritarios:

```text
GET /v1/production/product-services
POST /v1/production/product-services
PATCH /v1/production/product-services/{id}
PATCH /v1/production/product-services/{id}/status
POST /v1/production/recipes
POST /v1/production/recipes/{id}/versions
POST /v1/production/recipe-versions/{version_id}/approve
POST /v1/production/orders
PATCH /v1/production/orders/{id}/status
GET /v1/production/labor-areas
POST /v1/production/labor-areas
POST /v1/production/labor-areas/{area_id}/roles
GET /v1/production/machines
POST /v1/production/machines
```

Mock permitido durante esta fase:

- disponibilidad real de inventario;
- consumo real de materiales;
- entrada real de producto terminado;
- costos contables.

Criterio de salida:

- Produccion opera datos reales en QA;
- productos/servicios se crean y editan por API;
- receta aprobada se guarda con version;
- orden conserva snapshot de receta;
- cambios de receta no alteran ordenes en curso;
- frontend puede conectar gradualmente a endpoints reales.

### Fase 5 - `inventory-service` MVP real

Objetivo:

Habilitar almacenes, articulos, movimientos y existencias calculadas.

Entregables:

- schema `inventory`;
- migraciones de:
  - `warehouses`;
  - `warehouse_locations`;
  - `inventory_items`;
  - `inventory_movements`;
  - `inventory_balances`;
  - `inventory_reservations` preparado, aunque pueda quedar deshabilitado;
- endpoints MVP de almacenes;
- endpoints MVP de articulos;
- endpoints MVP de movimientos;
- consulta de existencias;
- consulta de kardex;
- disponibilidad para Produccion/Ventas;
- reverso de movimientos;
- regla de no salida mayor a existencia.

Endpoints prioritarios:

```text
GET /v1/inventory/warehouses
POST /v1/inventory/warehouses
GET /v1/inventory/items
POST /v1/inventory/items
GET /v1/inventory/movements
POST /v1/inventory/movements
POST /v1/inventory/movements/{id}/reverse
GET /v1/inventory/balances
GET /v1/inventory/kardex
POST /v1/inventory/availability-checks
```

Mock permitido durante esta fase:

- reservas automaticas;
- surtido de venta;
- consumo automatico desde orden de produccion.

Criterio de salida:

- existencias nacen de movimientos;
- kardex no tiene captura propia;
- ajustes negativos validan disponibilidad;
- Produccion puede consultar disponibilidad;
- auditoria registra movimientos y reversos.

### Fase 6 - `sales-service` MVP real

Objetivo:

Habilitar clientes, cotizaciones y pedidos comerciales basicos.

Entregables:

- schema `sales`;
- migraciones de:
  - `customers`;
  - `customer_contacts`;
  - `quotes`;
  - `quote_lines`;
  - `sales_orders`;
  - `sales_order_lines`;
  - `delivery_records`;
  - `return_requests` preparado;
- endpoints MVP de clientes;
- endpoints MVP de cotizaciones;
- conversion de cotizacion aprobada a pedido;
- lectura de productos/servicios desde Produccion;
- solicitud de produccion bajo pedido;
- consulta de disponibilidad a Almacenes.

Endpoints prioritarios:

```text
GET /v1/sales/customers
POST /v1/sales/customers
PATCH /v1/sales/customers/{id}
POST /v1/sales/quotes
POST /v1/sales/quotes/{id}/approve
POST /v1/sales/quotes/{id}/convert-to-order
GET /v1/sales/orders
PATCH /v1/sales/orders/{id}
POST /v1/sales/orders/{id}/request-fulfillment
GET /v1/sales/deliveries
```

Mock permitido durante esta fase:

- facturacion fiscal;
- salida real de inventario por entrega;
- devolucion con impacto automatico en inventario;
- contabilidad.

Criterio de salida:

- cotizaciones usan clientes existentes;
- cotizaciones usan productos/servicios existentes;
- cotizacion aprobada no duplica pedidos;
- pedido puede solicitar produccion por contrato;
- pedido no escribe inventario ni produccion directamente.

### Fase 7 - Integracion frontend progresiva

Objetivo:

Conectar la maqueta actual a APIs reales sin romper el prototipo.

Estrategia:

- agregar capa `frontend/api/` o adaptadores por modulo;
- permitir modo mock vs modo API por configuracion;
- migrar pantalla por pantalla;
- conservar datos mock para demo si el ambiente no tiene backend;
- mostrar errores reales de API;
- respetar i18n y UX existentes.

Orden sugerido:

1. login/contexto de tenant;
2. admin basico;
3. Produccion productos/servicios;
4. Produccion recetas;
5. Produccion ordenes;
6. Almacenes catalogos/movimientos;
7. Ventas clientes/cotizaciones/pedidos.

Criterio de salida:

- QA puede operar contra backend real;
- modo mock sigue disponible para maqueta si se decide conservar;
- errores de permisos y tenant se muestran de forma entendible.

### Fase 8 - `billing-service` y `provisioning-service`

Objetivo:

Automatizar adquisicion del producto y alta de tenants cuando el core operativo ya funcione.

Motivo:

No conviene vender publicamente antes de que el ERP real funcione para al menos un tenant QA.

Entregables:

- planes;
- checkout;
- webhooks firmados;
- activacion manual;
- provisioning idempotente;
- invitacion segura del administrador;
- tenant con modulos contratados;
- estado de suscripcion;
- flujo de suspension/reactivacion.

Endpoints prioritarios:

```text
GET /v1/billing/plans
POST /v1/billing/checkout-sessions
POST /v1/billing/webhooks/payment-provider
POST /v1/billing/manual-activations
POST /v1/billing/manual-activations/{id}/approve
POST /v1/provisioning/tenant-requests
POST /v1/provisioning/tenant-requests/{id}/retry
```

Criterio de salida:

- compra en linea puede crear tenant;
- activacion manual crea el mismo resultado que pago confirmado;
- no se envian contrasenas por correo;
- reintentos no duplican tenant;
- se puede suspender/reactivar tenant.

### Fase 9 - `integration-service`

Objetivo:

Habilitar clientes API, scopes, cuotas y medicion de uso.

Entregables:

- clientes API por tenant;
- secretos rotables;
- scopes;
- cuota inicial;
- registro de uso;
- validacion de scope en gateway/middleware.

Criterio de salida:

- un tenant puede crear cliente API;
- las llamadas quedan medidas;
- se bloquea uso sin scope o cuota;
- secretos no se guardan en texto plano.

---

## 6. Que se mantiene mock temporalmente

| Area | Motivo |
|---|---|
| Contabilidad | No es parte del primer backend MVP operativo. |
| Compras | Aun no es modulo activo prioritario. |
| Reservas automaticas | Requieren reglas completas de inventario y ventas. |
| Facturacion fiscal | Depende de proveedor y requisitos fiscales. |
| Reportes avanzados | Requieren datos reales acumulados. |
| Costeo contable | Requiere integracion con inventario, produccion y contabilidad. |
| Billing publico | Se implementa despues del core QA real. |

Regla:

> Todo mock debe estar identificado por ambiente o configuracion. No debe mezclarse silenciosamente con datos reales.

---

## 7. Validadores recomendados

### Ahora, antes de codigo backend pesado

- validar que existan docs base:
  - `ownership_datos_mvp.md`;
  - `modelo_datos_mvp.md`;
  - `apis_mvp.md`;
  - `plan_implementacion_backend_mvp.md`;
- validar que `TRAZABILIDAD.md` este secuencial;
- validar que `apis_mvp.md` contenga los siete servicios MVP;
- validar que `modelo_datos_mvp.md` contenga schemas requeridos;
- validar que no existan archivos temporales de draw.io versionados.

### Cuando existan migraciones/modelos

- validar tablas operativas sin `tenant_id`;
- validar endpoints POST/PATCH criticos sin permisos;
- validar comandos criticos sin `Idempotency-Key`;
- validar migraciones destructivas;
- validar modelos sin auditoria donde aplique;
- validar OpenAPI sin errores estandar;
- validar imports cruzados entre servicios.

---

## 8. Criterios para declarar QA real

QA deja de ser solo maqueta cuando:

- existe backend desplegable;
- existe base PostgreSQL QA separada;
- existe al menos un tenant QA;
- existen usuarios y roles reales;
- Produccion opera contra API real;
- Almacenes opera movimientos reales;
- Ventas crea clientes/cotizaciones/pedidos reales;
- validadores pasan en CI;
- logs y errores pueden revisarse;
- los datos de QA no dependen de `localStorage` como fuente principal;
- los endpoints criticos tienen pruebas basicas.

---

## 9. Criterios para declarar modulo real

Un modulo deja de ser maqueta cuando cumple:

- tiene servicio backend dueno;
- tiene tablas/migraciones propias;
- valida `tenant_id`;
- valida permisos;
- tiene endpoints documentados;
- tiene reglas criticas en backend;
- registra auditoria en acciones sensibles;
- tiene pruebas minimas;
- el frontend puede operar contra API real;
- los mocks restantes estan declarados.

---

## 10. Riesgos principales

| Riesgo | Mitigacion |
|---|---|
| Intentar construir todos los servicios al mismo tiempo | Implementar por fases y declarar mocks temporales. |
| Meter reglas criticas en frontend | Bloquear en revision y mover a backend. |
| Olvidar `tenant_id` | Validadores y convencion de modelos. |
| Duplicar datos por reintentos | Idempotency-Key y pruebas de reintento. |
| Acoplar servicios por base compartida | Schemas separados y sin FK cruzadas. |
| Sobreingenieria temprana | Serverless-first, servicios pequenos y evolucion gradual. |
| Vender antes del core real | Billing/provisioning despues de QA operativo. |
| Migraciones riesgosas | Alembic, backup, rollout en dos pasos y rollback. |

---

## 11. Primer sprint recomendado

Duracion sugerida:

```text
1 a 2 semanas, segun disponibilidad real de desarrollo
```

Objetivo:

Crear base backend local y `admin-service` minimo.

Tareas:

1. Crear estructura `backend/`.
2. Configurar FastAPI.
3. Configurar tooling Python.
4. Configurar Alembic.
5. Crear health checks.
6. Crear conexion PostgreSQL local.
7. Crear migraciones `admin` minimas:
   - tenants;
   - modules;
   - module_entitlements;
   - users;
   - roles;
   - permissions.
8. Crear seeds de permisos/modulos.
9. Implementar `GET /health`.
10. Implementar `GET /v1/tenants/{tenant_id}`.
11. Implementar `GET /v1/tenants/{tenant_id}/entitlements`.
12. Implementar `POST /v1/policy/evaluate` basico.
13. Documentar comandos Windows/Linux.
14. Agregar validacion backend inicial.

Criterio de salida:

- backend levanta localmente;
- migraciones corren;
- tenant demo existe;
- policy evaluate responde;
- validadores pasan.

---

## 12. Decision del arquitecto SaaS

La recomendacion es:

1. No iniciar por billing/provisioning.
2. No iniciar por todos los modulos a la vez.
3. No iniciar por OpenAPI YAML completo antes de tener plan de implementacion.
4. Iniciar por plataforma backend minima.
5. Implementar `admin-service` primero.
6. Convertir Produccion en el primer modulo real.
7. Integrar Almacenes y Ventas despues.
8. Automatizar venta y provisioning cuando el core ya opere en QA.

Frase guia:

> Primero un ERP real para un tenant en QA; despues una maquina comercial para crear muchos tenants.
