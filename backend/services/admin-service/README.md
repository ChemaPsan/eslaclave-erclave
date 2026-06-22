# admin-service

Duenio de tenants, usuarios, roles, permisos, configuracion, modulos activos y politicas globales.

Debe ser consultado por shell, microfrontends y servicios para autorizacion y configuracion.

## Estado

Scaffolding FastAPI inicial con modelo fisico base.

Tablas iniciales:

- `admin.tenants`;
- `admin.users`;
- `admin.roles`;
- `admin.permissions`;
- `admin.role_permissions`;
- `admin.memberships`;
- `admin.membership_roles`;
- `admin.tenant_modules`;
- `admin.audit_events`.

Decision clave: `users` representa la identidad global y `memberships` representa la pertenencia del usuario a un tenant. Los roles se asignan a la membresia, no directamente al usuario global.

## Seeds iniciales

El catalogo inicial de modulos MVP vive en:

```text
app/seeds/catalog.py
```

Modulos incluidos:

- `admin`;
- `production`;
- `inventory`;
- `sales`;
- `billing`;
- `provisioning`;
- `integrations`.

Este archivo aun no inserta datos en base; funciona como fuente versionada para el siguiente paso: script idempotente de seed.

## Ejecutar local

Desde `backend`:

```bash
uvicorn services.admin_service_adapter:app --reload --port 8000
```

Desde esta carpeta:

```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoints tecnicos

```text
GET /health
GET /ready
GET /version
```
