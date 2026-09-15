# Continuidad desde otra computadora — CHG-269

Fecha: 2026-09-09. Repositorio: https://github.com/ChemaPsan/eslaclave-erclave.

## Código publicado

Todos los cambios Local CHG-255–268 y la preparación de release CHG-269 están integrados en `main` por el PR #14. Commit funcional de rama `09399db8e4e515a58e308dffe00620132e84d095`; merge/candidato `b63cdad2fbac423c24460e55582ccfc0003e9924`.

```powershell
git clone https://github.com/ChemaPsan/eslaclave-erclave.git
cd eslaclave-erclave
git switch main
npm.cmd run session:context
```

Para un clon existente, revisar primero cambios locales y después `git pull --ff-only origin main`. No ejecutar reset ni sobrescribir trabajo de la otra computadora.

## Ambiente Local en un equipo nuevo

El repositorio conserva código, contratos, migraciones, pruebas, configuración de ejemplo y documentación. `.env`, credenciales, PostgreSQL local, `.venv`, `node_modules`, logs y herramientas temporales no se transfieren por Git.

Preparar dependencias siguiendo `backend/README.md`: Python y entorno virtual con `pip install -e ".[dev]"`, Node, PostgreSQL local `erclave_local` en loopback 5434, Firebase CLI y Java para Emulator. El arranque Windows canónico es `backend/scripts/start_local.ps1`; admite `-PostgresRoot` y exige `.env` Local correcto. Aplicar Alembic solamente sobre la base Local comprobada antes de arrancar una instalación nueva. Nunca copiar configuración QA ni abrir Cloud SQL Proxy para sustituir el entorno Local.

El tenant de ensayo permitido es `ten_739ee59d765d5e14818674800d`. Su dataset Local no es el dataset QA. La reserva recuperada MTO-000001 está en la base de la computadora original; Git no transporta esa operación.

## Release QA

Expediente y estado: `docs/operaciones/release_qa_20260908.md`. Candidato: https://github.com/ChemaPsan/eslaclave-erclave/actions/runs/34389669031. Consultar allí el resultado antes de continuar; no disparar releases duplicados.

El propietario autorizó el 9 de septiembre publicación del repositorio, PR/fusión y promoción QA completa, incluidas migraciones 0030–0034, configuración estructural, servicios, tráfico y Hosting. No autorizó datos funcionales nuevos ni cambios de Producción. Los gates siguen pasando por GitHub Environments y la evidencia debe registrar cada resultado.

Verificación del código: 262 pruebas backend (55 omitidas sin DB general), 54 navegador, controles de CI y dos pruebas de promoción compensatoria aprobadas. Integraciones PostgreSQL seleccionadas y smokes operativos en informes CHG-263–268. UAT autenticada corresponde al tester con sus cuentas y datos QA existentes.


## Cierre confirmado CHG-270

Release QA `34390476667` completado con éxito. Siete servicios al 100% sobre `b63cdad`, base `20260908_0034` y frontend servido idéntico al artefacto en index/env/app/styles. No repetir la promoción; continuar UAT desde https://erclave.web.app. `main` incluye después un commit documental de cierre; ese commit no reconstruye ni cambia el SHA funcional desplegado.
