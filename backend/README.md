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

## Endpoints tecnicos iniciales

```text
GET /health
GET /ready
GET /version
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
