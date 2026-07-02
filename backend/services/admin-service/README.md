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

Los permisos MVP se extraen desde:

```text
../../../contracts/api/*.openapi.yaml
```

El extractor vive en:

```text
app/seeds/permissions.py
```

El script idempotente para aplicar seeds vive en:

```text
../../scripts/seed_admin_mvp.py
```

Desde `backend`, con `ERCLAVE_DATABASE_URL` configurado:

```bash
python scripts/seed_admin_mvp.py --dry-run
python scripts/seed_admin_mvp.py
```

El script inserta o actualiza `admin.permissions` usando `ON CONFLICT (code)`, por lo que puede ejecutarse varias veces sin duplicar permisos.

## Seed QA demo

Desde `backend`, con `ERCLAVE_DATABASE_URL` configurado:

```bash
python scripts/seed_admin_qa_demo.py --dry-run
python scripts/seed_admin_qa_demo.py
```

El seed demo crea el tenant `demo-qa`, el usuario `admin.qa@erclave.local`, el rol `owner`, la membresia activa, los modulos activos de QA y las asignaciones de permisos del rol owner. Es idempotente y no crea contrasenas.

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

## Endpoints MVP reales

```text
GET /v1/tenants/{tenant_id}
GET /v1/tenants/{tenant_id}/entitlements
PUT /v1/tenants/{tenant_id}/entitlements/{module_code}
POST /v1/policy/evaluate
GET /v1/users
POST /v1/users/invitations
PATCH /v1/users/{user_id}
POST /v1/users/{user_id}/disable
GET /v1/roles
POST /v1/roles
PATCH /v1/roles/{role_id}
PUT /v1/roles/{role_id}/permissions
GET /v1/permissions
```

Estos endpoints leen y actualizan PostgreSQL por medio de `AdminRepository`. El `PUT` de entitlements permite activar, inactivar o suspender modulos para el tenant QA. Los endpoints de usuarios permiten invitar identidades QA, actualizar nombre/roles de membresia y desactivar membresias sin crear contrasenas ni login real. Los endpoints de roles permiten crear roles, activar/inactivar roles y reemplazar permisos asignados. Los endpoints mutables de tenants siguen pendientes para una fase posterior.

Los endpoints mutables requieren:

```text
Idempotency-Key=<clave_unica_del_comando>
X-Correlation-Id=<id_opcional_para_traza>
```

Cada mutacion registra un evento en `admin.audit_events` con accion, recurso, estado anterior, estado posterior, `correlation_id` e `idempotency_key`.
