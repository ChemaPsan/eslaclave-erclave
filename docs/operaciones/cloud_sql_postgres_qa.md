# Crear PostgreSQL QA en Google Cloud SQL

Esta guia explica como crear una base PostgreSQL en la nube para trabajar ERClave
desde Windows, Linux o macOS sin depender de una base local distinta en cada equipo.

El objetivo es crear un ambiente QA compartido:

```text
Instancia: erclave-qa-postgres
Base: erclave_qa
Usuario app: erclave_app
Conexion local: 127.0.0.1:5432 via Cloud SQL Auth Proxy
```

No uses esta base como produccion. Es para desarrollo/QA mientras el backend real
madura.

## Fuentes oficiales

- Crear instancias Cloud SQL PostgreSQL:
  `https://docs.cloud.google.com/sql/docs/postgres/create-instance`
- Crear bases de datos Cloud SQL PostgreSQL:
  `https://docs.cloud.google.com/sql/docs/postgres/create-manage-databases`
- Crear usuarios Cloud SQL PostgreSQL:
  `https://docs.cloud.google.com/sql/docs/postgres/create-manage-users`
- Conectar con Cloud SQL Auth Proxy:
  `https://docs.cloud.google.com/sql/docs/postgres/connect-auth-proxy`

## 0. Datos que debes decidir

Llena estos valores antes de empezar:

```text
GCP_PROJECT_ID=<tu-proyecto-gcp>
REGION=us-central1
INSTANCE_NAME=erclave-qa-postgres
DATABASE_NAME=erclave_qa
DATABASE_USER=erclave_app
DATABASE_PASSWORD=<contrasena-segura-no-commitear>
POSTGRES_VERSION=POSTGRES_16
```

Recomendacion inicial:

- Region: `us-central1`.
- PostgreSQL: `POSTGRES_16`.
- Instancia pequena para QA.
- Conexion local usando Cloud SQL Auth Proxy.

## 1. Instalar herramientas

Instala Google Cloud CLI:

```text
https://cloud.google.com/sdk/docs/install
```

Verifica que existe:

```bash
gcloud --version
```

Inicia sesion:

```bash
gcloud auth login
gcloud init
```

Selecciona el proyecto:

```bash
gcloud config set project <GCP_PROJECT_ID>
```

Habilita la API de Cloud SQL:

```bash
gcloud services enable sqladmin.googleapis.com
```

## 2. Crear instancia Cloud SQL PostgreSQL

Opcion recomendada para QA pequena:

```bash
gcloud sql instances create erclave-qa-postgres \
  --database-version=POSTGRES_16 \
  --region=us-central1 \
  --tier=db-g1-small \
  --storage-size=10GB \
  --storage-type=SSD \
  --backup-start-time=07:00 \
  --availability-type=ZONAL
```

Notas:

- `ZONAL` reduce costo para QA. Produccion deberia evaluar alta disponibilidad.
- `db-g1-small` es suficiente para arrancar QA; se puede subir despues.
- No abras IP publica con redes amplias como `0.0.0.0/0`.

Espera a que la instancia termine de crearse:

```bash
gcloud sql instances describe erclave-qa-postgres
```

## 3. Crear base de datos

```bash
gcloud sql databases create erclave_qa \
  --instance=erclave-qa-postgres
```

## 4. Crear usuario de aplicacion

No pongas la contrasena real en archivos del repo.

Linux/macOS:

```bash
read -s DB_PASSWORD
gcloud sql users create erclave_app \
  --instance=erclave-qa-postgres \
  --password="$DB_PASSWORD"
```

Windows PowerShell:

```powershell
$DB_PASSWORD = Read-Host "Password de erclave_app" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($DB_PASSWORD)
$DB_PASSWORD_PLAIN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
gcloud sql users create erclave_app --instance=erclave-qa-postgres --password="$DB_PASSWORD_PLAIN"
Remove-Variable DB_PASSWORD_PLAIN
```

## 5. Obtener el connection name

```bash
gcloud sql instances describe erclave-qa-postgres \
  --format="value(connectionName)"
```

Guarda el resultado. Tiene esta forma:

```text
<GCP_PROJECT_ID>:<REGION>:erclave-qa-postgres
```

En esta guia lo llamaremos:

```text
INSTANCE_CONNECTION_NAME=<GCP_PROJECT_ID>:us-central1:erclave-qa-postgres
```

## 6. Instalar Cloud SQL Auth Proxy

La opcion mas simple es descargar el binario oficial por sistema operativo.

Linux 64-bit:

```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.22.1/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
```

macOS Intel:

```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.22.1/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy
```

macOS Apple Silicon:

```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.22.1/cloud-sql-proxy.darwin.arm64
chmod +x cloud-sql-proxy
```

Windows 64-bit:

```text
Descarga:
https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.22.1/cloud-sql-proxy.x64.exe

Renombra el archivo a:
cloud-sql-proxy.exe
```

## 7. Abrir el proxy local

Abre una terminal dedicada y dejala abierta.

Linux/macOS:

```bash
./cloud-sql-proxy --port 5432 <INSTANCE_CONNECTION_NAME>
```

Windows PowerShell:

```powershell
.\cloud-sql-proxy.exe --port 5432 <INSTANCE_CONNECTION_NAME>
```

Si ya tienes PostgreSQL local usando `5432`, usa otro puerto, por ejemplo `5433`:

```bash
./cloud-sql-proxy --port 5433 <INSTANCE_CONNECTION_NAME>
```

En ese caso cambia tambien el puerto en `ERCLAVE_DATABASE_URL`.

## 8. Probar conexion con psql

Con el proxy abierto:

```bash
psql "host=127.0.0.1 port=5432 dbname=erclave_qa user=erclave_app password=<DATABASE_PASSWORD>"
```

Dentro de `psql`, prueba:

```sql
select current_database(), current_user;
```

Sal con:

```text
\q
```

Si no tienes `psql`, puedes instalar PostgreSQL client en tu equipo o usar una herramienta visual como DBeaver apuntando a:

```text
Host: 127.0.0.1
Port: 5432
Database: erclave_qa
User: erclave_app
Password: <DATABASE_PASSWORD>
```

## 9. Configurar ERClave

No guardes el `.env` real en Git.

Desde `backend/`, crea un archivo local `.env` tomando como base `.env.example`:

```text
ERCLAVE_ENVIRONMENT=qa
ERCLAVE_DATABASE_URL=postgresql+psycopg://erclave_app:<DATABASE_PASSWORD>@127.0.0.1:5432/erclave_qa
ERCLAVE_API_PUBLIC_BASE_URL=http://localhost:8000
```

Si tu password tiene caracteres especiales como `@`, `#`, `/`, `:`, conviene codificarlo para URL o cambiarlo por uno compatible.

## 10. Instalar dependencias backend

Desde `backend/`:

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 11. Ejecutar migraciones Alembic

Con el proxy abierto y el `.env` configurado:

```bash
cd backend
alembic upgrade head
```

Verifica que la migracion aplico:

```bash
alembic current
```

La primera migracion debe crear el schema `admin` y sus tablas iniciales.

## 12. Levantar admin-service

Con el proxy abierto:

```bash
cd backend
uvicorn services.admin_service_adapter:app --reload --port 8000
```

Prueba:

```text
http://localhost:8000/health
http://localhost:8000/ready
http://localhost:8000/version
```

## 13. Checklist rapido

- Google Cloud CLI instalado.
- Proyecto GCP seleccionado.
- Cloud SQL Admin API habilitada.
- Instancia `erclave-qa-postgres` creada.
- Base `erclave_qa` creada.
- Usuario `erclave_app` creado.
- Cloud SQL Auth Proxy descargado.
- Proxy corriendo en `127.0.0.1:5432`.
- `ERCLAVE_DATABASE_URL` configurado solo localmente.
- `alembic upgrade head` ejecutado.
- `admin-service` responde `/health`.

## Problemas comunes

### El puerto 5432 ya esta ocupado

Usa `5433` para el proxy y cambia la URL:

```text
ERCLAVE_DATABASE_URL=postgresql+psycopg://erclave_app:<DATABASE_PASSWORD>@127.0.0.1:5433/erclave_qa
```

### `gcloud` no encuentra el proyecto

Ejecuta:

```bash
gcloud auth login
gcloud config set project <GCP_PROJECT_ID>
gcloud projects describe <GCP_PROJECT_ID>
```

### El proxy dice que no tiene permisos

Tu cuenta necesita permiso para conectar a Cloud SQL. Para QA, pide o asigna un rol con permiso `cloudsql.instances.connect`, por ejemplo `Cloud SQL Client`.

### Alembic no conecta

Revisa:

- que el proxy siga abierto;
- que el puerto de la URL coincida con el puerto del proxy;
- que usuario, password y base sean correctos;
- que estes ejecutando desde `backend/`.

## Siguiente paso despues de esta guia

Cuando la base QA este creada y migrada, aplica los seeds MVP de administracion:

```text
cd backend
python scripts/seed_admin_mvp.py --dry-run
python scripts/seed_admin_mvp.py
python scripts/seed_admin_qa_demo.py --dry-run
python scripts/seed_admin_qa_demo.py
```

El comando requiere `ERCLAVE_DATABASE_URL` configurado y el Cloud SQL Auth Proxy abierto.
