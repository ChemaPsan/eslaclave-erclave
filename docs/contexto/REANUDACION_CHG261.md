# Reanudacion despues de reinicio: estado consolidado hasta CHG-261

Fecha del handoff: 2026-09-07.

Este documento es el punto de entrada operativo despues de reiniciar la computadora. Complementa `AGENTS.md`, `AGENTES.md`, `ESTADO_ACTUAL.md`, `DECISIONES.md`, `TENANTS.md`, `PENDIENTES.md` y `TRAZABILIDAD.md`; no sustituye sus reglas.

## Punto exacto de Git

- Repositorio: `eslaclave-erclave`.
- Rama local: `agent/chg-254-qa-release-record`.
- Ultimo commit funcional: `736d8e2 Corrige alta de servicios sin inventario`.
- Commit de estabilizacion: `74dfff5 Estabiliza flujos actuales en Local`.
- Commit de consolidacion previa: `8dcff6b Consolida cambios locales CHG-254 a CHG-258`.
- Base QA publicada: `a119ddf5e8d42376b8557b234e15e3681b19c2a7`.
- Al iniciar este handoff el working tree estaba limpio. CHG-261 agrega solamente este cierre documental y sus referencias; confirmar el nuevo `HEAD` y `git status --short` despues de leerlo.
- No existe push, PR, candidato QA ni despliegue asociado a `8dcff6b`, `74dfff5`, `736d8e2` o CHG-261.

## Frontera de ambiente

El trabajo vigente es **Local aislado**.

- Base: PostgreSQL `127.0.0.1:5434/erclave_local`.
- Revision Local: `20260901_0030`.
- Firebase: Emulator, proyecto dummy `demo-erclave`, puerto `9099` y UI `4000`.
- Tenant permitido para desarrollo/pruebas: `ERClave Demo QA`, ID `ten_739ee59d765d5e14818674800d`.
- Frontend: `127.0.0.1:4173`.
- APIs: Admin `8000`, Production `8002`, Inventory `8004`, RH `8006`, Sales `8008`, Purchasing `8010` y Maintenance `8012`.
- La pestana abierta `cloud-sql-proxy.err.log` no autoriza ni implica una conexion QA. El arranque Local canonico no usa Cloud SQL Auth Proxy.
- El reinicio apagara procesos y emuladores. No intentar recuperar conexiones remotas; levantar de nuevo el stack Local aislado.
- No ejecutar migraciones, seeds, cargas, IAM, workflows, despliegues, cambios de trafico ni Firebase Hosting en QA/Produccion sin una solicitud y autorizaciones nuevas.

## Estado funcional consolidado

### Release QA historico CHG-254

QA conserva el SHA inmutable `a119ddf5e8d42376b8557b234e15e3681b19c2a7`, siete servicios y Alembic `20260825_0029`. La evidencia esta en `docs/operaciones/resultado_release_qa_20260901.md`. No repetir el release. La matriz UAT sigue pendiente segun `PENDIENTES.md`.

### CHG-255: servicios comerciales solo en Local

- Ventas crea y opera Ordenes de servicio desde partidas `service`; estas no generan entregas ni movimientos de Inventory.
- Compras permite requisiciones, ordenes y recepciones comerciales de servicio sin articulo ni almacen.
- Admin incorpora unidad `E48`, folio y permisos relacionados.
- La migracion Local `20260901_0030_sales_service_orders.py` no esta aplicada en QA.

### CHG-256 y CHG-257: reportes estandar solo en Local

- Las seis portadas operativas contienen 28 reportes basicos propios del modulo.
- Cada reporte abre filtros indispensables y genera su archivo; la UI dice solo **Generar**, sin exponer el formato tecnico.
- Los catalogos cerrados de filtros son buscables; fechas y texto conservan controles apropiados.
- El modulo Reportes especializado sigue planeado para analitica transversal, XLSX/PDF, tableros y distribucion.

### CHG-258: identidad de la pestana

La aplicacion principal muestra el titulo `ERClave`; se retiro `Propuesta Frontend`.

### CHG-259: estabilizacion Local

- Playwright automatiza autenticacion con Firebase Emulator, tenant, seis modulos, todos sus submodulos, 28 reportes, aislamiento de red y paginacion.
- `npm.cmd run verify:postgres` exige PostgreSQL Local y falla ante cualquier prueba omitida.
- `npm.cmd run verify:local` compone validadores, backend PostgreSQL y E2E.
- Inventory prueba concurrencia de reservas y consumo idempotente; Sales, Purchasing y Maintenance conservan pruebas de locks, claims y recuperacion.
- Purchasing ya marca como `failed` toda linea sin respuesta de Inventory para permitir conciliacion correcta.
- El frontend extrajo estado inicial, feedback de errores y paginacion desde `app.js`.
- Los listados cargados con mas de 25 registros tienen paginacion visual. La paginacion contractual server-side sigue pendiente para volumen alto.

### CHG-260: alta de Servicios sin Inventory

- La regla backend ya era correcta: un `service` no requiere articulo y debe usar `inventory_item_id: null`; un `product` si requiere un articulo autoritativo compatible.
- Se corrigio el selector enriquecido del formulario de Produccion, que conservaba `required` al cambiar de Producto a Servicio.
- Para Servicio, el campo de Inventory queda oculto, deshabilitado y sin validez pendiente; al volver a Producto recupera la obligatoriedad.
- La prueba de navegador intercepta las dos respuestas mutantes y comprueba el payload sin crear servicios ni consumir folios reales.

## Ultima evidencia de validacion

- Regresion E2E completa: `6 passed`.
- Prueba E2E focal del Servicio sin Inventory: `1 passed`.
- Suite focal de `production-service`: `51 passed`.
- Verificacion PostgreSQL estricta: `245 passed`, cero skips, una advertencia de deprecacion Starlette/httpx sin impacto funcional.
- `npm.cmd run verify`: validadores, contratos OpenAPI, sintaxis, compilacion y pruebas aprobados.
- Trazabilidad secuencial hasta CHG-260 antes de este handoff; CHG-261 registra el cierre documental.

## Como reanudar

Desde la raiz del repositorio:

```powershell
$env:PATH="$env:LOCALAPPDATA\Programs\nodejs;$env:PATH"
git status --short
git log -5 --oneline
npm.cmd run session:context
```

Despues:

1. Leer `AGENTS.md`, `AGENTES.md`, este handoff y el documento del modulo que se vaya a cambiar.
2. Confirmar que no aparezcan cambios inesperados. Preservar cualquier cambio nuevo del usuario.
3. Para levantar Local, usar el arranque canonico documentado en `backend/scripts/start_local.ps1`; comprobar que todas las URLs sigan siendo loopback.
4. Confirmar el tenant `ten_739ee59d765d5e14818674800d` antes de cualquier prueba que escriba.
5. Ejecutar `npm.cmd run verify:local` para repetir PostgreSQL estricto mas navegador cuando el stack completo este activo.
6. Para una verificacion sin navegador usar `npm.cmd run verify:postgres` con PostgreSQL Local activo.
7. Continuar desde `docs/contexto/PENDIENTES.md`; no inferir que una capacidad Local ya existe en QA.

## Pendientes prioritarios reales

- Completar UAT del release QA ya publicado, solo con autorizacion explicita.
- Llevar la paginacion visual a cursores server-side antes de volumen productivo.
- Probar la interrupcion Production-Inventory entre consumo y confirmacion `in_progress`, seguida de reintento/reconciliacion.
- Continuar la separacion incremental de `frontend/app.js`; estado, errores y paginacion ya estan extraidos, pero las vistas de modulo siguen centralizadas.
- Evolucionar Compras y Mantenimiento conforme a la lista priorizada, sin agregar alcance por inferencia.
- Diseñar posteriormente el modulo Reportes especializado; los 28 reportes estandar actuales ya funcionan.

## APIs afectadas por el ultimo corte funcional

- Contratos modificados por CHG-260: ninguno.
- Consumida sin cambio: `POST /v1/production/product-services`, permiso `production.product_service.create`; para `type: service` conserva `inventory_item_id: null`.
- Simulada en E2E sin persistencia: `POST /v1/catalogs/code-sequences/{document_type}/next`.
- Inventory y el resto de contratos no cambiaron.

## Seguridad y recuperacion

- No hay archivos funcionales sin seguimiento que deban rescatarse al reiniciar.
- Logs, entornos virtuales, resultados Playwright, caches y credenciales locales permanecen ignorados por Git.
- No usar `git reset --hard`, `git checkout --` ni limpieza masiva para resolver diferencias futuras.
- El rollback de CHG-260 es revertir `736d8e2`; no hay schema ni datos que revertir.
- La fuente definitiva de cada cambio es `TRAZABILIDAD.md`; el estado por ambiente vive en `ESTADO_ACTUAL.md` y el trabajo futuro en `PENDIENTES.md`.
