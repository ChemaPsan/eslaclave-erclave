# CONT-08 — Órdenes manuales de Producción por División

CHG-313 · 2026-10-08 · Local, working tree sobre HEAD 213f75c. Integración manual CC-11 implementado Local. CHG-315 conecta fabricación de pedidos Sales; ver [CC-12](cont_08_fabricacion_contexto.md). No sustituye stock/servicios de CHG-305/307.

## Hallazgos y decisión confirmada

CHG-308 preparó un intento durable porque Inventarios necesita comprobar el origen antes de reservar. CHG-313 conecta esa preparación al alta manual: valida recursos en División, registra el intento y sus allocations y sólo entonces solicita reservas. La respuesta completada se recupera antes de repetir consultas o reservas, comprobando primero autorización y hash.

El usuario confirmó: «sí, en la moneda base de la Sociedad; esto aplica para todo». Regla transversal para costos y tarifas de toda la operación, incluidos materiales, máquinas y mano de obra. Cuando un documento use otra moneda, conservar original y convertido con tipo de cambio explícito. No reinterpretar ni convertir automáticamente historia sin moneda confirmada. Funciona con Accounting apagado. No volver a preguntar esta política; su aplicación completa sigue pendiente de implementación. Confirmación registrada en CHG-309; no altera la evidencia histórica del corte CHG-308.

No habilitar fabricación desde pedidos sólo por añadir organization_context. CHG-312 implementó [tarifas y capacidad](cont_08_tarifas_capacidad.md); CHG-313 conecta el consumidor manual. CHG-315 añade solicitud autenticada, propagación de contexto y conciliación de terminado/costo al pedido en CC-12.

## Comportamiento del corte manual

- División explícita en alta y validación; Sociedad y moneda se derivan de Admin. Recetas aprobadas se buscan por producto elegible en División; responsables y etapas usan trabajadores productivos de esa División. Una selección nueva invalida recursos y preview anteriores.
- Materiales: Inventory consulta existencias sólo de almacenes de la División y artículos elegibles, conserva costo original Decimal y rechaza historia monetaria incompatible. La prueba de reserva valida orden, actor, línea, artículo, almacén, cantidad y unidad antes de efectos o replay. Un fallo de dependencia nunca equivale a contexto ausente.
- Máquinas: tarifa confirmada en moneda Sociedad y capacidad física global por fecha, incluyendo compromisos legacy. Mano de obra: tarifa confirmada RH, IDs de personas compartidas y asignación diaria propia en Production. No sumar capacidades por División o puesto que comparten una persona.
- Compromisos laborales individuales se serializan por persona/día junto con locks globales compatibles con órdenes legacy. Un día con mano de obra legacy sin asignación individual se bloquea para revisión; no se inventan personas históricas. Cancelar libera los compromisos; las transiciones mantienen el ciclo de capacidad existente.
- Inicio/reanudación revalidan elegibilidad de los responsables y trabajadores asignados. RH sigue siendo autoridad de pertenencia; Production conserva los compromisos. No hay FK ni escritura entre servicios.
- Costo planificado y costo real exponen originales Decimal junto con proyecciones legacy. Consumo toma costo/contexto confirmados de Inventory. La proyección de terminado entrega costo unitario original a seis decimales; Inventory deriva contexto/costo del productor y valida destino antes de insertar o repetir recepción.
- UI ES/EN conserva captura, errores por etapa y claves de reintento; una respuesta incierta del alta reintenta esa alta sin volver a validar contra sus propias reservas. No cambia la captura de documentos históricos ni habilita fabricación Sales.

## Persistencia y ambiente

Migración0050 conserva contextos JSONB nullable y el intento durable de CHG-308. Migración20261008_0052 agrega production.labor_worker_commitments con FK compuesta interna por tenant/orden, persona/puesto/fecha/minutos/estado e índices de consulta. Reutiliza la unicidad histórica tenant/id de la orden. No rellena históricos. Downgrade bloquea ante cualquier compromiso registrado; forward-fix cuando hay historia.

Local aislado127.0.0.1:5434/erclave_local, único tenant ten_739ee59d765d5e14818674800d. Head0056 vigente; el corte CHG-314/0053 incluye también la adaptación monetaria de Servicios CHG-314. Ciclo0051→0053→0051→0053 aprobado sin nuevos datos inferidos. Fixtures con rollback; sin QA/Producción ni activación Accounting.

## APIs afectadas

Contratos Production, Inventory y HR modificados. Se conservan rutas de contexto CHG-308 y el alcance existente; no se acepta Sociedad/moneda arbitraria del cliente.

| Método/ruta (prefijo /v1/production) | Permiso | Cambio |
|---|---|---|
| GET /orders/{order_id}/reservation-context | production.order.release | Nuevo line_id; snapshot/asignación mínima autenticada del intento o null para intento no registrado. |
| GET /orders; GET /orders/{order_id} | production.order.read | Contexto en respuesta y alcance en lectura; filtro SQL antes de límite. |
| POST /resource-validations | production.order.validate o production.order.release | division_ref_id opcional compatible con API legacy; validación dimensionada agrega contexto, moneda y originales exactos por recurso/total. |
| GET /division-recipes | production.recipe.read o production.order.validate o production.order.release | Nuevo lookup division_id/q/limit/offset de recetas con producto elegible; no amplía maestros. |
| POST /orders | production.order.release | division_ref_id opcional en contrato, explícita en nueva UI manual; contexto derivado y costo original planificado/real en respuesta. Origen Sales dimensionado sigue cerrado. |
| PATCH /orders/{order_id}/status | permiso puntual de estado existente production.order.* | Scope antes del lock/efectos; start/resume revalidan trabajadores asignados. pause/cancel/wait permiten contexto histórico autorizado. |
| PATCH /orders/{order_id}/resources/{resource_id} | production.order.update | Scope del padre antes de modificar recurso. |
| PATCH /order-stages/{stage_id} | production.order_stage.reset/update/complete según estado | Scope del padre antes del comando. |
| GET /warehouse-material-requests | inventory.movement.read | Scope SQL antes de paginar. |
| POST /orders/{order_id}/issue-materials | inventory.movement.create | Scope antes del lock y consumo externo. |
| GET /finished-goods-candidates; GET /finished-goods-candidates/{order_id} | inventory.finished_goods_receipt.read o inventory.finished_goods_receipt.receive | Scope/contexto y original_unit_cost exacto; Inventory consume proyección autoritativa para recepción dimensionada. |
| GET /order-requests; POST /order-requests | production.order.read / sales.order.fulfill respectivamente | Response agrega contexto nullable; listado con alcance, alta dimensionada pendiente. |
| GET /returnable-materials | production.order.update o inventory.movement.read | Scope SQL antes de límite. |
| POST /material-returns/validate | production.order.update o inventory.movement.create | Scope del padre antes de validación. |
| POST /material-returns/reconcile | inventory.movement.create | Scope antes de conciliación local. |
| POST /orders/{order_id}/service-evidence/{phase} | production.order.start/wait_resources o production.order_stage.complete según fase | Scope antes de guardar evidencia. |
| GET /orders/{order_id}/service-evidence/files/{file_id} | production.order.read | Scope antes de descargar. |
| GET /reports/{report_code}/export | permiso puntual del reporte | Scope SQL en órdenes/entregables; formatos CSV iguales. |
| Inventory POST /v1/inventory/availability-checks | production.order.validate o production.order.release | division_ref_id opcional, costo original exacto y moneda por material/allocation. |
| Inventory POST /v1/inventory/reservation-requests | production.order.release para source Production | Entrada sin contexto capturable; consulta la prueba durable de origen antes de reservar. |
| Inventory GET /v1/inventory/finished-goods-receipts | inventory.finished_goods_receipt.read | Filtro de almacenes por scope antes de agregación. |
| Inventory POST /v1/inventory/finished-goods-receipts | inventory.finished_goods_receipt.receive | Deriva contexto/costo exacto del productor; rechaza campos extra de costo/contexto. |
| HR GET /v1/hr/division-workers | producción validate/release/start/resume sólo con purpose=production; consumidores anteriores conservados | Request/response iguales; nuevos consumidores limitados al propósito productivo, módulos activos y alcance. |

Consumidas sin cambio: Admin GET /v1/session/context; HR GET /v1/hr/division-production-capacity; Inventory POST /v1/inventory/reservations/{reservation_id}/consume y /release. Production consulta sus propias máquinas y compromisos; sin escritura directa a otros dueños. Sales sólo cambia en CHG-314 Servicios; Purchasing/Maintenance/Costing/Accounting sin modificaciones en CHG-313.

## Agentes, skills y evidencia

Delegación real a cc10_production, auditoria_ventas_inventario y cc10_ui; raíz integra RH, revisa contratos, migraciones y documentación. Fichas Producción/Inventory/RH/Ventas/Contabilidad y guardianes Arquitectura, Datos/Custodio DB, API, Seguridad, Sinergia, Diseño/i18n, QA/Release y Manuales. Skills feature/accounting/module-boundaries/db-migration/environment-boundaries/qa-evidence/form-contract/form-feedback/context-reconcile/solution-manuals.

Evidencia vigente en curso: chg313-migrate.log (ciclo vacío); chg313-inventory-postgres.log91 aprobadas, sin omisiones; chg313-browser.log6 casos ES/EN aprobados con APIs interceptadas. Production PostgreSQL/API116 aprobadas sin omisiones (chg313-production-tests.log); RH45 aprobadas sin omisiones (chg313-hr-postgres.log). Incluye ciclo release/start/pause/resume/avance/etapa/terminado con owners simulados, y locks con dos conexiones PostgreSQL. Gate final aprobado: verify588 aprobadas175 omitidas1warning; navegador223 aprobadas con APIs interceptadas. No declarar UAT ni integración real HTTP completa. Evidencia histórica CHG-308 se conserva en TRAZABILIDAD, sin reutilizar sus231 pruebas como validación de este corte.

CC-12 implementado CHG-315 con recorrido HTTP real aprobado. Los productores Purchasing/Maintenance, transferencias y sobrantes de CC-14 continúan pendientes. Datos reales y aceptación integrada CC-19/20 no se cierran con mocks o fixtures transaccionales.
