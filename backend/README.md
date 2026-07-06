# ERClave - Backend

Backend real de ERClave para mover los modulos MVP fuera de la maqueta.

## Estado actual

Scaffolding inicial con FastAPI para iniciar por `admin-service`.

Incluye:

- configuracion por ambiente;
- health checks;
- manejo comun de errores;
- `correlation_id`;
- placeholder de tenant;
- Alembic inicial conectado al modelo fisico de `admin-service`;
- estructura para servicios FastAPI;
- dominio/API base configurable por variable de ambiente.

Modelo fisico inicial de `admin-service`:

- `admin.tenants`;
- `admin.users`;
- `admin.roles`;
- `admin.permissions`;
- `admin.role_permissions`;
- `admin.memberships`;
- `admin.membership_roles`;
- `admin.tenant_modules`;
- `admin.audit_events`.

Modelo fisico inicial de `production-service`:

- `production.product_services`.

## Dominio configurable

El dominio publico aun no esta comprado. Por eso ningun servicio debe asumir `api.eslaclave.com` como valor fijo.

Usar:

```text
ERCLAVE_API_PUBLIC_BASE_URL
```

Ejemplos:

```text
http://localhost:8000
https://qa-api.example.com
https://api.eslaclave.com
```

Para desarrollo local, `admin-service` permite CORS desde:

```text
http://127.0.0.1:4173
http://localhost:4173
```

Esto permite conectar la maqueta frontend local al backend local sin abrir la API a origenes externos.

## Instalacion local

Desde la raiz del repo:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Ejecutar admin-service

Desde `backend`:

```bash
uvicorn services.admin_service_adapter:app --reload --port 8000
```

Alternativa desde la carpeta del servicio:

```bash
cd services/admin-service
uvicorn app.main:app --reload --port 8000
```

## Ejecutar production-service

Desde `backend`:

```bash
uvicorn services.production_service_adapter:app --reload --port 8002
```

Primer corte real de Produccion:

```text
GET /v1/production/product-services
POST /v1/production/product-services
GET /v1/production/product-services/{product_service_id}
PATCH /v1/production/product-services/{product_service_id}
PATCH /v1/production/product-services/{product_service_id}/status
```

## Endpoints tecnicos iniciales

```text
GET /health
GET /ready
GET /version
```

## Endpoints MVP de admin-service

Primer corte real de lectura, administracion de entitlements y evaluacion de politica:

```text
GET /v1/session/context
GET /v1/tenants/{tenant_id}
POST /v1/tenants
GET /v1/tenants/{tenant_id}/entitlements
PUT /v1/tenants/{tenant_id}/entitlements/{module_code}
POST /v1/policy/evaluate
GET /v1/users
POST /v1/users/invitations
PATCH /v1/users/{user_id}
POST /v1/users/{user_id}/disable
DELETE /v1/users/{user_id}
GET /v1/roles
POST /v1/roles
PATCH /v1/roles/{role_id}
PUT /v1/roles/{role_id}/permissions
GET /v1/permissions
GET /v1/settings
PUT /v1/settings/{key}
```

`GET /v1/session/context`, `GET /v1/users` y `GET /v1/roles` requieren header:

```text
X-Tenant-Id=<tenant_id>
```

En modo local/demo, `GET /v1/session/context` tambien requiere temporalmente:

```text
X-Actor-Id=<user_id>
```

En QA con `ERCLAVE_AUTH_MODE=firebase`, `GET /v1/session/context` requiere:

```text
Authorization=Bearer <firebase_id_token>
```

El servicio verifica el token de Firebase Auth, toma el email autenticado y lo cruza contra `admin.users` y `admin.memberships` del tenant activo. Si la membresia esta invitada, la activa al primer login valido. El endpoint devuelve tenant, usuario, entitlements, permisos efectivos y modulos activos.

Los endpoints mutables de `admin-service` requieren:

```text
Idempotency-Key=<clave_unica_del_comando>
X-Correlation-Id=<id_opcional_para_traza>
```

En QA con `ERCLAVE_AUTH_MODE=firebase`, las mutaciones de entitlements, usuarios y roles tambien validan el permiso efectivo del usuario autenticado contra `admin-service`. En local/demo se conserva el fallback de desarrollo para no bloquear pruebas locales.

Las mutaciones actuales de entitlements, usuarios, roles y settings registran auditoria en `admin.audit_events`. La invitacion de usuarios asegura identidad Firebase cuando el servicio corre en modo Firebase; la eliminacion borra el acceso en ERClave y elimina la identidad Firebase por email. El perfil organizacional del tenant vive en `admin.tenant_settings` con key `organization.profile` y se actualiza via `PUT /v1/settings/organization.profile`.

`POST /v1/tenants` crea tenants desde provisioning de forma idempotente y siempre inicializa `organization.profile`. La autorizacion service-to-service de provisioning queda como siguiente endurecimiento antes de Produccion.

Ejemplo de policy evaluation:

```json
{
  "tenant_id": "ten_...",
  "actor_id": "usr_...",
  "module": "admin",
  "resource": "tenant",
  "action": "read"
}
```

## Migraciones

Configurar primero:

```text
ERCLAVE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/erclave_local
```

Luego ejecutar desde `backend`:

```bash
alembic upgrade head
```

## Seeds MVP de administracion

Los permisos MVP se extraen desde los contratos OpenAPI versionados en
`contracts/api/*.openapi.yaml` y se aplican de forma idempotente sobre
`admin.permissions`.

Con `ERCLAVE_DATABASE_URL` configurado:

```bash
python scripts/seed_admin_mvp.py --dry-run
python scripts/seed_admin_mvp.py
```

El script puede ejecutarse varias veces. Si un permiso ya existe, actualiza sus
metadatos; si no existe, lo inserta.

## Seed QA demo

Despues de aplicar permisos MVP, se puede crear un tenant demo de QA:

```bash
python scripts/seed_admin_qa_demo.py --dry-run
python scripts/seed_admin_qa_demo.py
```

Este seed crea o actualiza:

- tenant `demo-qa`;
- usuario `admin.qa@erclave.local`;
- rol `owner`;
- membresia activa;
- modulos activos `admin`, `production`, `inventory`, `sales` e `integrations`;
- setting inicial `organization.profile` para corporativo, razones sociales y sucursales;
- asignacion del rol owner a todos los permisos activos.

No crea contrasenas ni credenciales de login. El usuario es una identidad de QA para
probar ownership, membresias, roles, permisos y modulos activos.
