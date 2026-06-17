# ERClave

ERClave es una propuesta SaaS modular bajo la marca EsLaClave para gestionar producción, inventarios, compras, ventas, gastos, costos, contabilidad y reportes.

## Contenido actual

- Documentación base del producto.
- Requerimientos no funcionales e infraestructura Google Cloud.
- Documentación funcional por módulos.
- Lista de agentes especializados por modulo en `AGENTES.md`.
- Arquitectura objetivo de microservicios y microfrontends en `docs/arquitectura/microservicios_microfrontends.md`.
- Mapa de catalogos base para Administracion y Configuracion en `docs/catalogos_base.md`.
- Manual de identidad visual.
- Trazabilidad detallada de cambios en `TRAZABILIDAD.md`.
- Prototipo frontend navegable con mock DB en `localStorage`.

## Frontend local

Para ver el prototipo:

```bash
cd frontend
python3 -m http.server 4173
```

Abrir:

```text
http://localhost:4173/
```

## Validaciones automaticas

Para ejecutar todas las validaciones:

```bash
npm run validate
```

> Ejecutar desde la raiz del repositorio `eslaclave-erclave`, donde esta `package.json`.
> En Windows PowerShell, si `npm.ps1` esta bloqueado por politicas de ejecucion, usar `npm.cmd run validate`.

Validaciones disponibles:

```bash
npm run validate:i18n
npm run validate:architecture
npm run validate:backend-scaffold
npm run validate:openapi
npm run validate:traceability
npm run validate:syntax
```

Estas validaciones convierten reglas de `AGENTES.md` en checks concretos: paridad Espanol/Ingles, fronteras de microfrontends, carpetas de microservicios, scaffolding backend, contratos OpenAPI, trazabilidad y sintaxis JavaScript.

En GitHub, el workflow `.github/workflows/validate.yml` ejecuta estas validaciones automaticamente en `push`, `pull_request` y ejecucion manual.

## Backend local

El scaffolding FastAPI inicial vive en `backend/` y arranca con `admin-service`.

```bash
cd backend
python -m venv .venv
python -m pip install -e ".[dev]"
uvicorn services.admin_service_adapter:app --reload --port 8000
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn services.admin_service_adapter:app --reload --port 8000
```

El dominio publico todavia no esta comprado. Configurar el valor publico con:

```text
ERCLAVE_API_PUBLIC_BASE_URL
```

## Estructura

```text
frontend/
backend/
contracts/
docs/
modulos/
tools/
AGENTES.md
ERClave_documento_base.md
ERClave_requerimientos_no_funcionales_e_infraestructura.md
ERClave_funcionalidades_y_valor_para_analisis_de_mercado.md
manual_identidad_paleta_morado.md
TRAZABILIDAD.md
```
