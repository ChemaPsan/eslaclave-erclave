# CONT-07 — Puestos y trabajadores por División

CHG-300 · 2026-09-27 · Local aislado, working tree sobre HEAD `213f75c`. Fichas consultadas: RH, Administración, Costos y Contabilidad negocio/técnica; Arquitectura SaaS/API, Datos/Custodio DB, Seguridad, Sinergia, Diseño/i18n, Manuales y QA. Skills feature, accounting, module-boundaries, migraciones, ambientes, form-contract/form-feedback, evidencia y manuales. Sin delegación.

## Alcance y propiedad

HR conserva el maestro compartido de puestos y el expediente único de trabajadores. Agrega asignaciones por División, sin inferir adscripciones ni duplicar personas. Admin autoriza tenant, usuario, módulos, permisos y alcance v2; Costing valida el centro opcional por HTTP. No hay FKs ni escrituras cruzadas entre servicios. Sociedad/Emisor se derivan de División, no se capturan.

Este corte implementa preparación CONT-07, no dimensiona todavía nómina, recetas, órdenes ni capacidad comprometida. Los contratos anteriores de capacidad y trabajadores elegibles continúan por tenant; CHG-312 añade [fuente de tarifa confirmada y consulta nominal por División](cont_08_tarifas_capacidad.md), consumida por órdenes manuales dimensionadas en CHG-313. No se conectan automáticamente los nuevos selectores a consumidores de CONT-08. Habilitar una persona en varias Divisiones no multiplica sus minutos disponibles: Production coordina compromisos por persona/fecha en su flujo manual CHG-313; otros consumidores aún deben integrar esa coordinación.

## Reglas y campos

| Campo | Tarea y origen | Persistencia y condición |
|---|---|---|
| División | Disponibilidad del puesto/trabajador; selector autorizado de Admin | PK tenant/recurso/división; varias asignaciones sin duplicar maestro. |
| Costo por hora del puesto | Tarifa de costeo por contexto, no salario | Decimal Numeric(18,6), requerido y no negativo; cero válido, máximo 12 enteros/6 decimales. Se propone tarifa general como valor inicial, queda explícita al guardar. Sin herencia dinámica. |
| Centro predeterminado del puesto | Preparación de imputación, selector Costing activo por División | Referencia opcional y snapshot código/nombre; permiso costing.cost_center.read y catálogo disponible al validar referencia activa. |
| Estado | Habilitar/retirar disponibilidad de la asignación | active/inactive; no altera el maestro. Desactivar conserva tarifa/centro/puesto histórico. |
| Puesto confirmado del trabajador | Evitar heredar elegibilidad al cambiar su puesto | Derivado del expediente, no editable en asignación; se congela labor_position_id al activar/guardar. |
| Revisión | Evitar sobrescribir cambios concurrentes | expected_revision requerido, 0 al crear; sólo servidor incrementa revisión. |

Para activar puesto se exige puesto y área activos. Para activar trabajador se exige trabajador activo, puesto vigente activo, área activa y asignación activa de ese puesto en la misma División. Al cambiar el puesto del expediente, la asignación anterior queda histórica y no concede elegibilidad al nuevo puesto; volver a guardar activa confirma el puesto vigente. Las banderas intervenes_in_production/intervenes_in_maintenance siguen controlando consultas para esos propósitos.

Consultar elegibles revalida estados y la coincidencia del puesto confirmado con el vigente. Cambiar o desactivar maestros no borra asignaciones ni interpreta de nuevo auditorías anteriores. Desactivar permite conservar historia aunque un área, puesto, centro o División ya no esté activo (con acceso histórico autorizado); no permite cambiar simultáneamente tarifa/centro. Reactivar revalida todo.

Centro omitido no consulta Costing. El catálogo básico no activa Accounting/analítica ni hace obligatorio el centro; su obligación depende del futuro flujo habilitado. Worker no captura tarifa ni centro: ambos pertenecen a la asignación del puesto. Costing caído rechaza la validación de un centro seleccionado, conservando transacción y captura.

## Autorización y privacidad

Cada API nueva consulta contexto Admin incluso en demo. Requiere tenant/usuario activos, Admin y HR activos, scope v2 y permiso exacto hr.position.read/update o hr.worker.read/update. No hay grants, seeds ni bypass por rol. División activa para habilitar; alcance limitado sólo ve sus Divisiones efectivas; wildcard explícito permite consultar historia. Fallos de dependencia no devuelven permiso ni catálogo vacío ficticio.

Lectura de asignaciones de trabajador devuelve sólo IDs, estado/revisión y puesto confirmado. Consulta elegible devuelve ID, número de empleado, nombre completo, puesto y División; excluye CURP/RFC/NSS/contacto/salario/tarifa. Auditoría contiene únicamente los campos de asignación, actor y correlación: no copia el expediente. Leer puestos no exige leer expedientes de trabajadores.

## UI y errores

Puestos: RH → Áreas y puestos → detalle del área → tarjeta. Trabajadores: RH → Trabajadores → tarjeta. Acción Asignación por División sólo en API con módulo disponible, scope v2 y permiso de lectura. Escribir exige update correspondiente. ES/EN, búsquedas acotadas/paginadas, datos conservados ante rechazo y clave estable para reintentar el mismo payload.

Tarifa con cero y seis decimales, centro restablecido al cambiar División y tarifa/centro históricos preservados al desactivar. Read-only no ofrece guardado. Cliente específico adapta details.issues[].field de RH a loc sólo para campos explícitos del formulario; no cambia el contrato de errores de los endpoints existentes ni infiere campos desde texto libre. Pruebas reales de navegador comprueban ARIA/foco, captura, permiso, conflicto, error de centro y tarifa, dependencia y ausencia de éxito falso. Layout propio por contenedor 320px, sin cambiar estilos globales.

## Datos y concurrencia

Alembic `20260927_0043`: hr.position_division_assignments y hr.worker_division_assignments, PK tenant/recurso/división, estados acotados/revisión positiva/timestamps, índices tenant/división/estado. Tarifas Numeric(18,6) con constraint no negativo y máximo. FK compuesta interna a labor_roles para puesto y puesto confirmado; FK compuesta a workers para trabajador, con unique tenant/id agregada a workers. IDs externos División/Centro sin FK cruzada.

Escritura bloquea recurso; activación de trabajador toma share lock del puesto y su asignación, y se bloquea lectura del área vigente. Revisión, cambio, auditoría before/after y respuesta idempotente usan la misma transacción HR. Clave por tipo/recurso/División, hash de actor/payload; repetición devuelve respuesta guardada, contenido distinto rechaza 409. Autorización actual previa al replay. Las validaciones HTTP de Admin/Costing no son atómicas con la transacción HR; consumidores futuros deben revalidar antes de efectos operativos.

Sólo PostgreSQL `127.0.0.1:5434/erclave_local` y tenant `ten_739ee59d765d5e14818674800d`, comprobados por guard canónico y preflight. Upgrade/downgrade vacío/upgrade probados. Downgrade toma locks y rechaza si hay asignaciones o auditoría del flujo; con historia se requiere forward-fix. Fixtures sintéticos con rollback; sin datos personales reales, backfill, estructura inferida, seeds ni asignaciones permanentes. QA/Producción intactos.

## APIs afectadas

Nuevas en hr-service. Todas requieren tenant y autorización efectiva; escrituras requieren Idempotency-Key y aceptan X-Correlation-Id.

| Método y ruta | Permiso | Request / response |
|---|---|---|
| GET /v1/hr/organization/divisions | hr.position.read o hr.worker.read | q, limit 1–25, offset; Divisiones efectivas id/code/name/society_id y meta. |
| GET /v1/hr/positions/{resource_id}/division-assignments | hr.position.read | division_id opcional, limit 1–100, offset; asignaciones con tarifa, centro/snapshot, estado/revisión y meta. |
| PUT /v1/hr/positions/{resource_id}/division-assignments/{division_id} | hr.position.update | expected_revision, status, hourly_cost obligatorio, cost_center_ref_id opcional; asignación guardada/revisión. |
| GET /v1/hr/workers/{resource_id}/division-assignments | hr.worker.read | division_id opcional, limit 1–100, offset; asignaciones/puesto confirmado/estado/revisión y meta. |
| PUT /v1/hr/workers/{resource_id}/division-assignments/{division_id} | hr.worker.update | expected_revision y status; asignación guardada con puesto derivado y revisión. |
| GET /v1/hr/division-positions | hr.position.read | division_id requerido, purpose all/production/maintenance, q, limit 1–25, offset; puestos activos asignados, tarifa explícita, centro guardado, flags y meta. |
| GET /v1/hr/division-workers | hr.worker.read | mismos filtros; trabajadores elegibles minimizados y meta. |

Consumidas sin cambio: Admin GET /v1/session/context; Costing GET /v1/cost-centers/{cost_center_id} y GET /v1/cost-centers/eligible (costing.cost_center.read); HR GET /v1/hr/areas, GET /v1/hr/positions y GET /v1/hr/workers para tarjetas (hr.area.read, hr.position.read, hr.worker.read). APIs previas de capacidad/elegibilidad, Production, Inventory, Sales, Purchasing, Maintenance y Accounting no se modifican. CORS HR incorpora PUT para el cliente nuevo.

## Evidencia y continuación

Resultados en TRAZABILIDAD CHG-300 y logs chg300-migrate.log, chg300-tests.log, chg300-browser.log, chg300-smoke.log, chg300-verify.log. Dominio/API con dobles, persistencia PostgreSQL con rollback, UI con interceptores ES/EN y smoke HTTP real Local con Emulator se registran por separado; no equivalen a UAT ni promoción QA.

CONT-07 también tiene asociaciones Sales/Purchasing y condiciones explícitas. CHG-312 confirma moneda de tarifa y agrega consulta nominal por División; CHG-313 integra el consumidor laboral manual, sin duplicar disponibilidad de trabajadores compartidos. Conservar asignaciones RH; otras brechas en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). Manuales: [REGISTRO](../manuales_solucion/REGISTRO.md).
