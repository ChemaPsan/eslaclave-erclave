# Modelo fisico inicial de `admin-service`

Estado: definido para implementacion MVP.

Este documento aterriza el primer modelo fisico real de `admin-service` en PostgreSQL/Cloud SQL. El objetivo es crear la fuente de verdad para tenants, usuarios, roles, permisos, modulos contratados, configuracion organizacional, membresias y auditoria.

## Principios

- `admin-service` es duenio de tenants, usuarios, roles, permisos y modulos activos.
- `admin-service` es duenio del perfil organizacional inicial del tenant mediante `admin.tenant_settings` key `organization.profile`.
- Ningun servicio operativo debe escribir estas tablas directamente.
- Todo dato operable por tenant debe tener separacion clara por `tenant_id`.
- El usuario se modela como identidad global y la relacion con cada tenant vive en `memberships`.
- Las acciones criticas deben registrar `audit_events`.
- Los catalogos de estatus se mantienen como `varchar` con `CHECK` para permitir evolucion controlada sin bloquear el MVP.
- Los campos flexibles usan `jsonb` solo para metadatos, limites o snapshots; no deben esconder reglas criticas.

## Tablas iniciales

| Tabla | Proposito | Tenant scoped |
|---|---|---|
| `admin.tenants` | Cliente/empresa dentro del SaaS. | No; es la raiz del tenant. |
| `admin.users` | Identidad global del usuario. | No; se relaciona por membresias. |
| `admin.memberships` | Relacion usuario-tenant y estatus dentro del tenant. | Si. |
| `admin.roles` | Roles configurables por tenant. | Si. |
| `admin.permissions` | Catalogo global de permisos del sistema. | No. |
| `admin.role_permissions` | Permisos asignados a cada rol. | Si. |
| `admin.membership_roles` | Roles asignados a una membresia. | Si. |
| `admin.tenant_modules` | Modulos activos, suspendidos o inactivos por tenant. | Si. |
| `admin.tenant_settings` | Parametros por tenant; incluye `organization.profile`. | Si. |
| `admin.audit_events` | Bitacora de acciones criticas y cambios administrativos. | Puede ser global o por tenant. |

## Decision sobre usuarios y membresias

Se evita que `users` dependa directamente de `tenant_id`. La razon es que una misma persona puede administrar o participar en mas de una empresa. La identidad vive una sola vez en `admin.users`; su acceso a cada tenant vive en `admin.memberships`.

Ejemplo:

- `admin.users`: `ana@empresa.com`.
- `admin.memberships`: Ana pertenece al tenant A como activa.
- `admin.memberships`: Ana pertenece al tenant B como invitada.

Los permisos efectivos no se leen desde `users`; se resuelven desde:

```text
tenant -> membership -> membership_roles -> roles -> role_permissions -> permissions
```

## Separacion por tenant

Tablas con `tenant_id` obligatorio:

- `roles`;
- `tenant_modules`;
- `memberships`;
- `role_permissions`;
- `membership_roles`.

`audit_events.tenant_id` es nullable porque puede registrar eventos previos a la existencia del tenant, por ejemplo errores de provisioning o acciones internas globales.

## Idempotencia y auditoria

El modelo prepara `audit_events.idempotency_key` y `audit_events.correlation_id` para rastrear comandos criticos.

La idempotencia final se debera complementar con una tabla dedicada de comandos procesados cuando implementemos endpoints mutables como:

- `POST /v1/tenants`;
- `PUT /v1/tenants/{tenant_id}/entitlements/{module_code}`;
- `POST /v1/users/invitations`;
- `POST /v1/roles`;
- `PUT /v1/roles/{role_id}/permissions`.
- `PUT /v1/settings/{key}`.

## Perfil organizacional

Cada tenant debe nacer con:

```text
admin.tenant_settings.key = organization.profile
admin.tenant_settings.module_code = admin
```

Este setting contiene:

- `corporate`: nombre corporativo, razon social principal, RFC, telefono y contacto.
- `legal_entities`: razones sociales del corporativo, datos fiscales y contacto por razon social.
- `branches`: sucursales, matriz, centros de trabajo, almacenes o puntos de venta.

No debe guardarse como fuente de verdad en `admin.tenants.metadata`, Firebase Auth o localStorage. El frontend solo lo presenta y lo actualiza mediante `GET /v1/settings`, `PUT /v1/settings/organization.profile` para corporativo, y endpoints finos de `admin-service` para razones sociales y sucursales.

## Archivos fuente

- ORM: `backend/services/admin-service/app/models.py`
- Migracion: `backend/alembic/versions/20260617_0001_admin_service_initial.py`
- Migracion settings: `backend/alembic/versions/20260705_0003_admin_tenant_settings.py`
- Alembic metadata: `backend/alembic/env.py`
- Catalogo seed MVP: `backend/services/admin-service/app/seeds/catalog.py`

## Catalogo seed de modulos MVP

El primer seed versionado define estos codigos de modulo:

| Codigo | Servicio duenio | Visible como modulo contratable |
|---|---|---|
| `admin` | `admin-service` | No |
| `production` | `production-service` | Si |
| `inventory` | `inventory-service` | Si |
| `sales` | `sales-service` | Si |
| `billing` | `billing-service` | No |
| `provisioning` | `provisioning-service` | No |
| `integrations` | `integration-service` | Si |

Este archivo no escribe datos en base porque el modelo fisico inicial aun no incluye una tabla global `admin.modules`. Los codigos de modulo se usan como catalogo versionado para validar permisos y entitlements por `module_code`.

## Seeds de permisos MVP

Los permisos MVP se extraen de `contracts/api/*.openapi.yaml`, usando la extension `x-permissions` de cada operacion.

Archivos:

- Extractor: `backend/services/admin-service/app/seeds/permissions.py`.
- Runner idempotente: `backend/scripts/seed_admin_mvp.py`.

El runner aplica seeds sobre `admin.permissions` con `ON CONFLICT (code)`, por lo que puede ejecutarse varias veces sin duplicar datos.

Comandos desde `backend`:

```bash
python scripts/seed_admin_mvp.py --dry-run
python scripts/seed_admin_mvp.py
```

## Pendientes inmediatos

1. Definir si agregaremos tabla global `admin.modules` o mantenemos modulos como catalogo en codigo durante el MVP.
2. Implementar repositorios o unidad de trabajo para `admin-service`.
3. Implementar endpoints mutables de tenants y asegurar que `POST /v1/tenants` inicialice `organization.profile`.
4. Agregar tabla de idempotencia para comandos reales.
5. Agregar pruebas de migracion contra PostgreSQL en QA.
