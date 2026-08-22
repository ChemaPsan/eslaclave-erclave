# ERClave

ERClave es una propuesta SaaS modular bajo la marca EsLaClave para gestionar producción, inventarios, compras, ventas, gastos, costos, contabilidad y reportes.

## Contenido actual

- Documentación base del producto.
- Requerimientos no funcionales e infraestructura Google Cloud.
- Documentación funcional por módulos.
- Lista de agentes especializados por modulo en `AGENTES.md`.
- Instrucciones operativas de Codex en `AGENTS.md` y skills del proyecto en `.agents/skills/`.
- Arquitectura objetivo de microservicios y microfrontends en `docs/arquitectura/microservicios_microfrontends.md`.
- Guias operativas paso a paso en `docs/operaciones/`.
- Guia manual de pruebas del alcance real, prototipos y modulos futuros en `docs/qa/guia_pruebas_qa_mvp.md` y version Word en `docs/qa/guia_pruebas_qa_mvp.docx`.
- Mapa de catalogos base para Administracion y Configuracion en `docs/catalogos_base.md`.
- Manual de identidad visual.
- Trazabilidad detallada de cambios en `TRAZABILIDAD.md`.
- Frontend navegable en modo API con caches en memoria; el modo maqueta permanece aislado y no es fuente de verdad en QA.

## Local aislado canonico

Recuperar contexto y arrancar el stack completo con PostgreSQL `erclave_local`, APIs locales y Firebase Emulator:

```powershell
npm.cmd run session:context
backend\scripts\start_local.ps1
```

Abrir `http://127.0.0.1:4173/`. No abrir Cloud SQL Auth Proxy ni reutilizar un `.env` QA para este flujo. Un proceso local que consume cualquier recurso QA se clasifica como `local conectado a QA` y requiere autorizacion explicita.

## Validaciones automaticas

Para ejecutar todas las validaciones:

```bash
npm run validate
```

> Ejecutar desde la raiz del repositorio `eslaclave-erclave`, donde esta `package.json`.
> En Windows PowerShell, si `npm.ps1` esta bloqueado por politicas de ejecucion, usar `npm.cmd run validate`.

Validaciones disponibles:

```bash
npm run validate:agents
npm run validate:local-qa-parity
npm run validate:i18n
npm run validate:active-localization
npm run validate:architecture
npm run validate:backend-scaffold
npm run validate:cross-platform
npm run validate:db-guardrails
npm run validate:openapi
npm run validate:traceability
npm run validate:syntax
```

Estas validaciones convierten reglas de `AGENTES.md` en checks concretos: agentes transversales y por modulo, paridad Espanol/Ingles, fronteras de microfrontends, carpetas de microservicios, scaffolding backend, compatibilidad Linux/Windows/macOS, guardrails de base de datos y migraciones, contratos OpenAPI, trazabilidad y sintaxis JavaScript.

Para ejecutar el criterio completo de terminado (validadores, compilacion Python y pruebas backend):

```bash
npm run verify
```

Para preparar la siguiente entrada de trazabilidad a partir de los cambios detectados por Git:

```bash
npm run traceability:draft -- --title "Descripcion del cambio"
```

El comando muestra el borrador sin modificar archivos. Agregar `--write` lo inserta antes de la convencion final; los campos generados deben revisarse y completarse.

Para regenerar el documento Word QA desde su guia Markdown:

```bash
npm run qa:document
```

En GitHub, el workflow `.github/workflows/validate.yml` ejecuta estas validaciones automaticamente en `push`, `pull_request` y ejecucion manual.

## Desarrollo y liberacion

El script canonico prepara `admin-service`, `production-service`, `inventory-service`, `hr-service`, frontend, base local y usuario del Emulator sin depender de QA. Para una liberacion usar `$erclave-qa-release` y [flujo_local_a_qa.md](docs/operaciones/flujo_local_a_qa.md); no desplegar desde una terminal local como sustituto del pipeline.

El consumo HTTP del frontend debe vivir en `frontend/api/`; las pantallas no deben llamar `fetch` directamente.

## Estructura

```text
frontend/
backend/
contracts/
docs/
  operaciones/
modulos/
tools/
AGENTES.md
ERClave_documento_base.md
ERClave_requerimientos_no_funcionales_e_infraestructura.md
ERClave_funcionalidades_y_valor_para_analisis_de_mercado.md
manual_identidad_paleta_morado.md
TRAZABILIDAD.md
```
