# CONT-08 — Tarifas confirmadas y consulta de capacidad por División

CHG-312 · Local · 2026-10-07. Corte CC-10 previo a fabricación CC-11/12. [Control contable](../contexto/CONTROL_CONTABLE.md), [decisión monetaria](../contexto/DECISIONES.md), [RH](../../modulos/10_recursos_humanos.md) y [Producción](../../modulos/01_produccion.md).

## Criterios y propiedad

RH conserva la tarifa del puesto por División y la elegibilidad del trabajador compartido. Production conserva la tarifa y los compromisos de cada máquina física. Admin determina Sociedad/moneda y autoriza alcance. No hay escrituras/FKs entre schemas ni se activa Accounting. Una consulta de capacidad no reserva recursos ni habilita fabricación.

1. Confirmar explícitamente importe y moneda de Sociedad; cero válido, Decimal con hasta seis decimales. Históricos sin confirmación permanecen nulos, sin backfill.
2. Derivar Sociedad desde División autorizada; rechazar moneda diferente, scope ausente/revocado y referencias no elegibles.
3. Preservar moneda histórica; cambios de Sociedad/moneda no reetiquetan tarifas existentes y exigen nueva confirmación antes de usarlas como costo actual.
4. Consultar personas por identidad global y máquinas por identidad física, sin multiplicar capacidad por número de Divisiones.
5. Proteger idempotencia, auditoría y actualización concurrente; conservar captura y precisión en UI ante rechazo.

## Formularios y tarea que resuelve cada campo

| Campo | Uso y origen | Alta/edición/lectura |
|---|---|---|
| División | Contexto autorizado Admin, existente | Puesto compartido; máquina con División fija. Sociedad no se captura. |
| Importe hora RH / minuto máquina | Tarifa operativa, no salario ni asiento | Captura decimal explícita; cero válido. No transformar coste histórico automáticamente. |
| Moneda de Sociedad | Derivada de scope.societies.base_currency | Sólo lectura; backend vuelve a comprobar. No selector independiente. |
| Confirmación de tarifa | Declaración explícita de importe en esa moneda | Casilla no preseleccionada; sin confirmación no se envía actualización monetaria. |
| Fecha de capacidad máquina | Día para calcular compromisos existentes | Fecha requerida para consulta; fines de semana cero bajo calendario base actual. |

Los errores usan código estable ES/EN, foco/ARIA y preservación del borrador. El editor general de máquina no reenvía una tarifa confirmada redondeada al cambiar nombre/otros campos. La tarifa exacta se confirma en su panel específico. Desactivar asignación RH conserva tarifa/moneda históricas.

## Contratos y permisos

| Método y ruta | Permiso | Cambio |
|---|---|---|
| PUT /v1/hr/positions/{resource_id}/division-assignments/{division_id} | hr.position.update | Activo exige hourly_cost_currency_code; servidor guarda Sociedad y fecha de confirmación. |
| GET /v1/hr/positions/{resource_id}/division-assignments | hr.position.read | Devuelve terna monetaria nullable, preservando historia. |
| GET /v1/hr/division-positions | hr.position.read | Tarifas confirmadas vigentes; no proponer tarifa histórica sin moneda. |
| GET /v1/hr/division-production-capacity | hr.position.read o production.order.validate/release | Nueva consulta por division_id: IDs únicos de trabajadores, tarifa y capacidad nominal. |
| POST /v1/production/machines | production.machine.create | Importe Decimal; creación conserva tarifa sin moneda confirmada hasta asignar División y confirmar. |
| PATCH /v1/production/machines/{machine_id} | production.machine.update | cost_currency junto a importe; moneda/Sociedad derivadas y confirmación auditada. |
| GET /v1/production/machines | production.machine.read | Campos monetarios y División; alcance en SQL para máquinas asignadas. |
| GET /v1/production/machines/{machine_id} | production.machine.read o maintenance.order.create | Revalida División de la máquina devuelta; campos de confirmación. |
| GET /v1/production/division-machines | production.machine.read o production.order.validate/release | Nueva consulta division_id/planned_date, resource_id/q/limit/offset; costo vigente y capacidad neta. |

Contratos exactos: [RH OpenAPI](../../contracts/api/hr-service.openapi.yaml), [Production OpenAPI](../../contracts/api/production-service.openapi.yaml). Consumidas sin cambio: Admin GET /v1/session/context; Costing GET /v1/cost-centers/{cost_center_id} cuando se selecciona centro; consultas legacy RH de Production conservan su contrato. APIs Sales/Inventory/Purchasing/Maintenance/Accounting no modificadas.

## Capacidad: nominal frente a neta

RH devuelve capacity_scope=shared_workers y commitments_included=false. Los mismos trabajadores mantienen los mismos IDs/pool al consultar distintas Divisiones. Los minutos son nominales; no sumar filas de diferentes Divisiones ni prometer disponibilidad libre. Production sigue siendo dueño de compromisos y CHG-313 integra en órdenes manuales los compromisos por persona/día con ocupación global; este corte no introduce reservas de personal por División.

Máquinas: capacity_scope=physical_machine y commitments_included=true. Production resta compromisos activos por tenant/machine/fecha, incluidas órdenes anteriores sin contexto; no filtra esos compromisos por División. Sólo máquinas activas, fuera de mantenimiento y con tarifa confirmada en la moneda/Sociedad vigente son elegibles. La consulta no bloquea capacidad; liberación concurrente sigue siendo responsabilidad de la orden.

## Persistencia, historia y recuperación

Alembic 20261007_0051, padre0050. RH position_division_assignments: hourly_cost_currency_code, hourly_cost_society_ref_id y hourly_cost_confirmed_at. Production machines: cost_currency, cost_society_ref_id y cost_confirmed_at. Ternas completas o nulas, códigos de tres letras y Sociedad no vacía; máquina confirmada requiere División. Importe existente Numeric(18,6) no cambia ni se convierte.

Reintentos de máquinas anteriores conservan su snapshot cuando el hash previo, actor e importe lossless coinciden; respuestas nuevas con Decimal string no reciben esa excepción. Capturas históricas que excedían seis decimales pueden ser rechazadas por el schema actual antes del fallback: consultar su resultado previo, sin reinterpretar ni volver a ejecutar la mutación.

Sin defaults monetarios ni backfill. Downgrade bloquea con confirmación o evidencia de confirmación en auditoría; usar forward-fix. Prueba de upgrade/downgrade sin confirmaciones/upgrade realizada sólo en 127.0.0.1:5434/erclave_local, tenant ten_739ee59d765d5e14818674800d. Fixtures de pruebas con rollback; sin cargas de negocio permanentes ni QA.

## Evidencia y límites

Agentes ejecutados: cc10_rh, cc10_production y cc10_ui; revisión cruzada RH→Production/UI y revisión del coordinador de migración, scope y contratos. Aplicadas skills feature/accounting/module-boundaries/db-migration/environment-boundaries/form-contract/form-feedback/qa-evidence/manuales.

Resultados finales en [TRAZABILIDAD](../../TRAZABILIDAD.md): 150 pruebas PostgreSQL conjuntas sin omisiones; 211 pruebas de navegador aislado; verify aprobado con 554 pruebas y 158 omitidas en la ejecución sin base configurada. Migración Local upgrade/downgrade sin confirmación/upgrade aprobada. Las omisiones no equivalen a cobertura aprobada. PostgreSQL y pruebas HTTP con TestClient son distintos del navegador con APIs interceptadas. El arranque fue inicialmente bloqueado y la revisión automática rechazó Bypass. Posteriormente el usuario autorizó explícitamente Bypass sólo para ese proceso: start_local.ps1 ejecutó seeds locales de permisos/demo y levantó ocho APIs, frontend y Emulator. Smoke HTTP real de lectura aprobado: health, login/sesión y catálogos 200; nuevas rutas rechazan División inexistente 403, token ausente 401 y tenant ajeno 422. Sin Divisiones autorizadas: no se ejecutaron consultas positivas con recursos ni escrituras de tarifas por HTTP. Evidencia chg312-start-local.log y chg312-http-smoke.log; tenant demo, HEAD 213f75c con cambios, sin QA/Producción. Word requiere revisión visual según [REGISTRO](../manuales_solucion/REGISTRO.md).

Continuación actual: conservar CHG-313 (consumidor manual CC-11), CHG-314 (moneda Servicios) y [CHG-315 fabricación CC-12](cont_08_fabricacion_contexto.md). Este último tiene recorrido HTTP real aprobado con recursos/costo y recepción/entrega. Continuar otros productores CC-14/15/16 y aceptación transversal CC-20.
