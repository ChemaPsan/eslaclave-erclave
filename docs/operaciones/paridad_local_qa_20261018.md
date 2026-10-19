# Correcciones para paridad Local → QA — CHG-335

> Evidencia histórica del corte 2026-10-18, preparado Local; pendiente de autorizaciones y aceptación QA. Fuente vigente: [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md). No constituye un despliegue ni aceptación completa.

## Ambiente y alcance

Local aislado, PostgreSQL 127.0.0.1:5434/erclave_local, Emulator demo-erclave y tenant exclusivo ten_739ee59d765d5e14818674800d. Agentes ejecutados: manuales_paridad (pipeline, Purchasing y evidencia Production), trazabilidad (validadores, identidades, config, Maintenance y navegador), cc20_integracion (Costing/RH/Inventory/Sales, folios y Production/Maintenance), raíz (configuración, readiness, circuito comercial y gobierno). Mutaciones sólo de código y fixtures sintéticos propios Local; sin PR, merge, IAM, seeds QA ni deploy.

## Correcciones preparadas

| Capacidad | Implementación Local preparada | Estado QA |
|---|---|---|
| Ocho runtimes | Candidato/deploy/smoke/tráfico/rollback incluyen Costing básico | QA aún siete runtimes anteriores; no promovido |
| Centro de costos | URL/flag en Admin y consumidores, secreto específico y cuenta dedicada Costing | Variables/identidad por verificar, aprovisionar y autorizar |
| Dependencias | Production e Inventory → Sales, consumidores → Costing con HTTPS; guards remotos rechazan loopback/emulador | Pendiente desplegar |
| DB readiness | GET /ready remoto consulta conexión y compara Alembic heads de imagen; HTTP503 incompatible | Pendiente desplegar |
| Configuración | Migración/config independientes; catálogo global + owners existentes sólo tenant explícito; sin reset de usuarios/perfil/módulos | Pendiente autorizar/especificar tenant |
| Frontend | Build único en candidato, artefacto SHA256SUMS, procedencia/SHA/URLs antes de escribir, sin reconstrucción en release | Pendiente candidato/Hosting |
| Local | start_local fija service_name y URL por proceso; Costing anterior reiniciado con DB correcta para pruebas | Local aislado |

No se activa analítica Costing ni Accounting por desplegar el catálogo. No se copia la DB Local ni se inventa CC-19 real. Las 26 migraciones 0037–0062 no crean automáticamente la estructura/equivalencias reales de QA.

## Lecturas remotas y configuración pendiente

Preflight 2026-10-18: siete GET /version HTTP200 con e57237fe90319f88e1db8ed8d2e686604d2d9c54; Hosting sin URL Costing. Git remoto main=e57237f y rama publicada=ef15b97. Variables GitHub consultadas por lectura: QA_COSTING_API_URL, QA_COSTING_RUNTIME_SERVICE_ACCOUNT y QA_CONFIGURATION_TENANT_ID ausentes. No se consultó Cloud SQL/PITR ni se otorgaron roles.

Manifiesto revisable: cuenta erclave-costing-qa, cloudsql.client, acceso sólo al secreto erclave-database-url-qa y comunicación Admin; despliegue vía WIF existente y serviceAccountUser según identidad aprobada. Bootstrap Cloud Run nuevo recibe tráfico inicial: requiere autorización explícita y no dispone de revisión anterior; no simular rollback preexistente. Los servicios existentes usan candidatos sin tráfico y rollback de sus revisiones registradas.

## Aceptación Local por variantes

CC20-01 conserva su acta previa. Las nuevas comprobaciones HTTP reales y Chrome se registran por variante en .local/cc20-*; no convertir ejecución parcial en fila completa. Inventory reveló replay entre actores de transferencia, registrado como INC-CC20-13-ACTOR-01 y corregido; regresión distingue actor original, otro actor y scope revocado. Otros dueños recibieron el mismo control y recuperación durable antes de efectos. La matriz conserva variantes pendientes y CC-19 histórico sin procedencia.

Validación focal inicial: 63 pruebas configuración/readiness/reconciliación aprobadas, una advertencia existente; incluye PostgreSQL con rollback en tenant autorizado y conservación de usuarios/membresías/perfil/roles/entitlements. El código y los validadores no equivalen a aceptación QA.

## Gates pendientes y rollback

Completar aceptación aplicable; aprobar PR/merge y SHA final; IAM/variables Costing por alcance propio; qa-build ocho digests y frontend; migración aprobada 0036→0062 y configuración por separado; qa-services con smoke técnico público de revisiones/readiness y posterior aceptación API autenticada independiente; registrar revisiones y qa-traffic; qa-frontend verificar bytes servidos. Preservar datos. Rollback: revisiones exactas previas, Hosting anterior y DB PITR/forward-fix aprobado después de escrituras, sin downgrade improvisado.

## APIs afectadas

- Contrato técnico compartido GET /ready: QA/prod comprueba DB/head Alembic y devuelve HTTP503 si no está listo; mantiene database_configured y añade database_ready. Local conserva la comprobación de configuración.
- RH, Inventory, Sales, Purchasing y Maintenance: vinculación de recibos/intents al actor, scope actual y recuperación parcial; evidencia Production exige el actor original. Sin cambio de payload operativo ni migración. Métodos/rutas/permisos se enumeran más adelante.
- Consumidas sin cambio de negocio durante aceptación: organización/alcance/folios Admin, catálogo básico Costing y operaciones restantes de los dueños; métodos/rutas exactos en los logs HTTP por variante. QA sólo GET /version, GET /env.js y lectura de variables GitHub. Backoffice, Accounting y APIs de otros módulos no reciben cambios de negocio.


## Plan sintético solicitado y prevención de pérdida de operabilidad

El usuario autorizó **preparar el plan y revisarlo antes de aplicar**, no escribir datos QA. [Plan versionado](../../infra/qa/synthetic-organization-plan.json): un emisor sin datos fiscales, dos Sociedades propuestas MXN/USD, tres Divisiones y tres centros. Los IDs/códigos se resuelven por APIs dueñas en QA; no se copian desde Local. La moneda debe confirmarse en la revisión del plan.

0037/38 crean DDL, no activan ni migran la organización. Sin autoridad activa/resoluble, el contrato efectivo sigue V1 y los consumidores V2 rechazan operaciones. El guard de sólo lectura `check_qa_operational_readiness.py` se ejecuta al final de qa-services, antes del tráfico estable: verifica tenant, autoridad/proyección, cadena activa, monedas confirmadas por ID, scopes efectivos y Owner operativo/permisos básicos. Una falla impide promoción. Admin candidato a 0% permite preparar una configuración expresamente aprobada; primera revisión Costing mantiene la excepción de bootstrap ya declarada.

Variable nueva `QA_CONFIRMED_SOCIETY_CURRENCIES`: JSON con TODOS los IDs de Sociedades activas y monedas aprobadas. No rellenarla desde un default del importador. Si hay perfil legado no vacío, detener la activación y revisar su transición/equivalencias; el importador histórico usa MXN y no constituye confirmación monetaria. El plan exige baseline/hashes/IDs antes de aprobación de ejecución; aún no se han leído los datos privados QA.

## Evidencia de este corte

Todos los lotes siguientes son Local aislado, único tenant autorizado y APIs dueñas reales. SQL es de sólo lectura salvo pruebas PG con rollback y limpieza explícita de maestros sintéticos propios por IDs registrada en el lote UI; esa limpieza no altera documentos, stock ni historia monetaria. No contienen tokens en la evidencia registrada.

| Caso / variante | Evidencia ignorada bajo .local | Resultado / límite |
|---|---|---|
| RH/centros e Inventory | cc20-02-04-20261018231246; suplementos 231330 y conciliación 231405 | Decimal6, cero, monedas, centro ajeno/inactivo, multiadscripción, puesto vigente; entrada/reversa, transferencia parcial4/retorno6 con costo7.123456 y stock16/4/0; limpieza a0 |
| Historia tarifaria propia | cc20-02-history-20261018233321/result.json | 4 checks: cambiar tarifa a99.123456 no altera documento/costo laboral congelado; tarifa y estados restaurados |
| Inventory actor/scope/CSV | cc20-02-04-20261018231910 | Legado original200/otro409; nuevo recibo mismo actor estable/otro409; ambos extremos revocados403; Kardex acotado |
| Production manual | cc20-05-08-20261018232329 | Validación60MXN, capacidad, orden/replay, consumo/etapas/cierre y recepción; 503 comercial inicial conservado |
| Sales CC-21 | cc20-06-20261018231601/result.json | 26 checks: MXN, USD con tasa, cero, costo ausente, tasa ausente; aprobación/pedido/snapshots y Accounting apagado |
| Historia/limpieza comercial | cc20-06-supplement-20261018232111/result.json | 26 checks; seis snapshots aprobados inmutables, pedidos propios cancelados y maestros propios inactivos; capturas aprobadas se conservan como historia |
| Stock y entrega | cc20-07-20261018232303/result.json | 9 checks: reserva5, entregas2+3, ledger5in/5out, costo original Decimal6 y convertido USD; saldo/reserva final0 |
| Replays de recibos anteriores a corrección | cc20-07-replay-20261018233811/result.json | 4 checks: surtido y dos entregas actor original200; sin nuevas salidas/recosteo; maestros restaurados inactivos. Intento anterior con maestros inactivos rechazó elegibilidad422, no era defecto de replay |
| Fabricación comercial recuperada | cc20-08-resume-20261018232748/result.json | Mismo pedido/clave tras503: una orden, consumo/recepción/reconciliación/entrega idempotentes;60MXN→3USD |
| Compras mixtas/negativos | cc20-09-10-20261018231802/result-final.json | Requisición→OC→recepción física2+servicio1, condiciones congeladas; negativos de alcance/revisión/sobrerrecepción/moneda |
| Compras USD | cc20-09-fx-20261018232151 | 4 checks: falta tasa422,2USD×17.25=34.5MXN y una recepción/movimiento. Total3unidades propias conservadas porque reversa exige devolución; maestros inactivos |
| Maintenance | cc20-11-20261018231459/result-final.json | Tiempo30min a12.123456/h=6.061728MXN; una reserva/salida5 y sobrante5; cierre y saldo0; máquina bloqueada/liberada y maestros inactivos |
| Folios | cc20-12-20261018232107/result.json | 8 checks: concurrencia/replay/payload, modos managed/manual y consumidor Maintenance. Configuración restaurada; next5→8 sin rebobinar |
| Scope/listas/CSV | cc20-13-14-20261018233145/result.json | 30 checks, cuatro documentos dueños y Kardex Inventory; misma credencial tras revocación, sin mutar snapshots. Rectificación: GET individual de orden Purchasing/movimiento Inventory no existe; detalle desde listado y no usar404/405 de ruta inexistente como prueba de autorización |
| UI y responsive | cc20-16-2026-10-19T05-24-47-755Z/browser.json | 39 checks: ES/EN,7 módulos+catálogo básico, selector/recarga, captura nativa y desktop390px sin desbordes; Administración móvil accesible |
| Impresión | cc20-16-print-2026-10-19T05-28-54-164Z/browser.json | Cotización aprobada y orden Production propias: identidad y colores cotejados con snapshots; dos PDF/capturas |
| Negocio/reintento UI | cc20-16-business-2026-10-19T05-29-18-402Z/browser.json | ES/EN: código duplicado409 conserva captura/foco/alerta; código corregido201 y persistencia tras recarga. Dos clientes y tres maestros propios inactivos por SQL; secuencia restaurada sin avance |
| Actor Sales/RH/Purchasing | cc20-sales-actor-20261018232523; cc20-hr-actor-20261018233056; cc20-purch-actor-20261018233629 | Original/mismo actor permitido, otro409, scope revocado403 cuando corresponde; snapshots intactos, actores/maestros propios limpiados |

Los fallos intermedios de arnés (identidades sintéticas colisionadas, ruta/campo incorrectos, comparación monetaria2dec/Decimal6 y timestamp de auditoría de cada dueño) se conservaron y corrigieron como arnés, sin presentarlos como defectos del producto. Los defectos de producto demostrados fueron actor compartido, retry de código manual, responsive y reconciliación parcial; conservar sus regresiones.

## Comprobaciones técnicas adicionales

- Focal configuración/readiness/reconciliación:63 aprobadas, con PG Local y rollback. Guard operativo:30 aprobadas con PG/READONLY y paquete Admin aislado para evitar colisiones de imports entre servicios.
- Simulación aislada del proveedor Cloud Run: success, partial_failure y costing_partial_failure aprobadas; no cambia Cloud Run real.
- Dos workflows YAML y20 pasos Bash parseados después de añadir el guard; evidencia .local/chg335-pipeline-syntax/result.json. `database_readiness` lee head Local0062 y devuelve verdadero.
- Builder crea106 archivos sanitizados y ocho URLs. Verificador de Hosting rechaza env viejo/SHA incorrecto y acepta bytes exactos en una prueba con fetch sustituido; no equivale a Hosting remoto verificado. El release ejecuta luego `tools/verify-qa-hosting.js` contra el sitio real.
- Primera verify general detectó cuatro fallos por colisión `app.seeds` al importar scripts entre servicios; corregida con paquete de seeds aislado. Registrar la verify final por separado, sin ocultar esa corrida ni atribuir sus skips a pruebas aprobadas.

## Límites vigentes

La prueba de datos históricos reales sin equivalencias CC-19 permanece bloqueada. No hay pruebas de dos tenants QA autorizados ni UAT QA ni ejecución remota del nuevo pipeline. Algunas variantes UI de circuitos complejos se detallan en matriz; los siete tipos de folios ya se comprobaron con consumidores reales managed/manual; no inferir aprobación completa de todas las combinaciones a partir de los casos centrales ni de los dobles unitarios.

## Cierre adicional de recuperación, folios y actor

| Variante | Evidencia Local | Resultado |
|---|---|---|
| Maintenance durable | cc20-13-maintenance-20261018234432/result.json y runtime-final.json | 16 checks HTTP reales: actor original, otro409, transición nueva/legacy, conciliaciones y sobrante Inventory confirmado. Orden propia cancelada y actor retirado; runtime8012 sano |
| Maintenance regresión focal | pruebas test_command_actor_binding y test_maintenance_api; compatibilidad CC16 | 44 aprobadas API/PG y4 compatibilidad. Intents padre antes de releases, transición parcial no sellada, recuperación sin repetir transición y lock sin reentrada por otra sesión. Fallos parciales/carreras focales API/PG, sin inducir transporte integrado |
| Folios seis tipos adicionales | cc20-12-cross-20261018234316/result.json | 100 checks y30 lotes concurrentes: puesto RH, movimiento Inventory, proveedor/requisición/OC/recepción Purchasing managed/manual. Consumidores e Inventory interno manual por origen comprobados; seis configuraciones restauradas, stock propio0 y siete maestros inactivos |
| Historia de folios Purchasing | cc20-12-history-20261018234439/history-codes.json | Sólo lectura: cuatro tipos propios creados antes del cambio conservan IDs y códigos exactos; no acredita legacy sin procedencia |

El intento previo de folios chocó con un RFC sintético existente y restauró configuraciones/stock propio antes de reintentar con otra identidad; no es una incidencia funcional ni autoriza rebobinar next. La verificación general sin DB no ejecuta los casos PostgreSQL: conservar la evidencia focal separada y sus límites.

La revisión independiente de trazabilidad no detectó pérdida funcional nueva en pipeline/configuración/frontend. Se sincronizó el manifiesto IAM propuesto con Admin→Costing y Production/Inventory→Sales; no se otorgaron roles. El builder sólo acepta salidas dedicadas bajo dist o .local para evitar borrar fuentes al limpiar artefactos.

## Inventario de contratos afectados

`GET /ready` en los ocho runtimes es técnico/público: añade `database_ready`; QA/prod devuelve503 si falta DB o el head no coincide con la imagen. Los contratos de negocio siguientes mantienen requests/responses y permisos existentes; cambia la validación de actor del recibo durable y los intents/reintentos parciales descritos. Otro actor recibe409 `idempotency_key_reused`; evidencia Production devuelve403 `idempotency_actor_mismatch`. Scope vigente se comprueba antes de devolver replay; recibos legacy requieren procedencia inequívoca y no se reescriben para inventar autor. Purchasing normaliza timestamps del replay a ISO, conservando instantes y contenido.

| Servicio | Método y ruta | Permiso existente / condición |
|---|---|---|
| hr | POST `/v1/hr/areas` | `hr.area.create` |
| hr | PATCH `/v1/hr/areas/{id}` | `hr.area.update` |
| hr | POST `/v1/hr/positions` | `hr.position.create` |
| hr | PATCH `/v1/hr/positions/{id}` | `hr.position.update` |
| hr | POST `/v1/hr/workers` | `hr.worker.create` |
| hr | PATCH `/v1/hr/workers/{id}` | `hr.worker.update` |
| inventory | POST `/v1/inventory/warehouses` | `inventory.warehouse.create` |
| inventory | PATCH `/v1/inventory/warehouses/{id}` | `inventory.warehouse.update` |
| inventory | POST `/v1/inventory/items` | `inventory.item.create` |
| inventory | PATCH `/v1/inventory/items/{id}` | `inventory.item.update` |
| inventory | POST `/v1/inventory/movements` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/purchase-receipts` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/reservations/{reservation_id}/consume` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/material-returns/{return_id}/receive` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/material-returns/{return_id}/cancel` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/transfers/{transfer_id}/receive` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/transfers/{transfer_id}/request-return` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/transfers/{transfer_id}/receive-return` | `inventory.movement.create` |
| inventory | POST `/v1/inventory/movements/{movement_id}/reverse` | `inventory.movement.reverse` |
| inventory | POST `/v1/inventory/finished-goods-receipts` | `inventory.finished_goods_receipt.receive` |
| inventory | POST `/v1/inventory/material-returns` | `production.order.update OR maintenance.material_request.create OR inventory.movement.create; según origen` |
| inventory | POST `/v1/inventory/reservation-requests` | `production.order.release OR sales.order.fulfill OR maintenance.material_request.create; según origen` |
| inventory | POST `/v1/inventory/reservations/{reservation_id}/release` | `production.order.cancel OR sales.order.cancel OR maintenance.material_request.cancel OR maintenance.order.cancel OR inventory.movement.create; según origen` |
| sales | POST `/v1/sales/customers` | `sales.customer.create` |
| sales | PATCH `/v1/sales/customers/{id}` | `sales.customer.update` |
| sales | POST `/v1/sales/quotes` | `sales.quote.create` |
| sales | PATCH `/v1/sales/quotes/{id}` | `sales.quote.update` |
| sales | POST `/v1/sales/quotes/{quote_id}/submit` | `sales.quote.submit` |
| sales | POST `/v1/sales/quotes/{quote_id}/approve` | `sales.quote.approve` |
| sales | POST `/v1/sales/quotes/{quote_id}/expire` | `sales.quote.expire` |
| sales | POST `/v1/sales/quotes/{quote_id}/cancel` | `sales.quote.cancel` |
| sales | POST `/v1/sales/orders` | `sales.order.create` |
| sales | POST `/v1/sales/orders/{order_id}/fulfillment` | `sales.order.fulfill` |
| sales | POST `/v1/sales/orders/{order_id}/production-reconciliations` | `sales.order.fulfill` |
| sales | POST `/v1/sales/orders/{order_id}/cancel` | `sales.order.cancel` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/plan` | `sales.service_order.plan` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/time-entries` | `sales.service_order.time.create` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/cost-entries` | `sales.service_order.cost.create` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/evidence` | `sales.service_order.evidence.create` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/transitions/assign` | `sales.service_order.assign` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/transitions/start` | `sales.service_order.start` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/transitions/wait` | `sales.service_order.wait` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/transitions/resume` | `sales.service_order.resume` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/transitions/submit_acceptance` | `sales.service_order.submit_acceptance` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/transitions/accept` | `sales.service_order.accept` |
| sales | POST `/v1/sales/service-orders/{service_order_id}/transitions/cancel` | `sales.service_order.cancel` |
| sales | POST `/v1/sales/deliveries` | `sales.delivery.create` |
| sales | POST `/v1/sales/deliveries/{delivery_id}/confirm` | `sales.delivery.confirm OR inventory.movement.create; comprobación adicional inventory.movement.create` |
| sales | POST `/v1/sales/deliveries/{delivery_id}/cancel` | `sales.delivery.cancel` |
| purchasing | POST `/v1/purchasing/suppliers` | `purchasing.supplier.create` |
| purchasing | PATCH `/v1/purchasing/suppliers/{id}` | `purchasing.supplier.update` |
| purchasing | POST `/v1/purchasing/requisitions` | `purchasing.requisition.create` |
| purchasing | PATCH `/v1/purchasing/requisitions/{id}` | `purchasing.requisition.update` |
| purchasing | POST `/v1/purchasing/orders` | `purchasing.order.create` |
| purchasing | PATCH `/v1/purchasing/orders/{id}` | `purchasing.order.update` |
| purchasing | POST `/v1/purchasing/requisitions/{id}/submit` | `purchasing.requisition.submit` |
| purchasing | POST `/v1/purchasing/requisitions/{id}/approve` | `purchasing.requisition.approve` |
| purchasing | POST `/v1/purchasing/requisitions/{id}/reject` | `purchasing.requisition.reject` |
| purchasing | POST `/v1/purchasing/requisitions/{id}/cancel` | `purchasing.requisition.cancel` |
| purchasing | POST `/v1/purchasing/orders/{id}/issue` | `purchasing.order.issue` |
| purchasing | POST `/v1/purchasing/orders/{id}/cancel` | `purchasing.order.cancel` |
| purchasing | POST `/v1/purchasing/receipts` | `purchasing.receipt.create` |
| purchasing | POST `/v1/purchasing/receipts/{id}/reconcile` | `inventory.movement.create; dependency inicial también admite purchasing.receipt.reconcile` |
| purchasing | POST `/v1/purchasing/receipts/{id}/accept-services` | `purchasing.requisition.create OR purchasing.order.create; solicitante original` |
| maintenance | POST `/v1/maintenance/orders` | `maintenance.order.create` |
| maintenance | PATCH `/v1/maintenance/orders/{id}` | `maintenance.order.update` |
| maintenance | POST `/v1/maintenance/orders/{id}/transitions` | `maintenance.order.{transition}` |
| maintenance | POST `/v1/maintenance/orders/{id}/reconcile` | `maintenance.order.reconcile` |
| maintenance | POST `/v1/maintenance/orders/{id}/time-entries` | `maintenance.time.create` |
| maintenance | POST `/v1/maintenance/orders/{id}/material-requests` | `maintenance.material_request.create` |
| maintenance | POST `/v1/maintenance/material-requests/{id}/cancel` | `maintenance.material_request.cancel` |
| maintenance | POST `/v1/maintenance/material-requests/{id}/reconcile` | `maintenance.material_request.reconcile` |
| maintenance | POST `/v1/maintenance/material-requests/{id}/issue` | `inventory.movement.create` |
| maintenance | POST `/v1/maintenance/material-requests/{id}/reject` | `inventory.movement.create` |
| maintenance | POST `/v1/maintenance/material-returns/reconcile` | `inventory.movement.create` |
| production | POST `/v1/production/orders/{order_id}/service-evidence/{phase}` | `start: production.order.start OR production.order.wait_resources; finish: production.order_stage.complete` |

En la tabla, `{id}` representa el identificador del recurso del endpoint; el contrato usa en algunas rutas nombres equivalentes como `item_id`/`warehouse_id`/`quote_id`. Maintenance `{transition}` admite request, assign, start, wait_for_parts, resume, resolve, close, reopen, cancel; exige su permiso puntual. No cambian asignaciones organizacionales, validaciones sin recibo, `unit-conversion`, `availability-checks` ni `production-reservation-rollbacks`. No se introduce endpoint nuevo ni migración. OpenAPI/README de cada dueño describen la semántica nueva.

`GET /v1/production/orders/{order_id}` (`production.order.read`) se verificó para otro actor autorizado sin cambiar la autoría de evidencia; no cambió el contrato de lectura. No se ejecutó GCS ni descarga de archivos. Los logs HTTP de cada lote enumeran métodos/rutas de Admin/Costing y restantes operaciones consumidas sin cambio; Backoffice/Accounting no reciben cambio funcional.

## Recuperación integrada y pausa Production

- Purchasing: el resultado original `cc20-10-transport-20261018234133/result.json` conserva el fallo de igualdad de timestamps. Suplemento `cc20-10-transport-audit-20261018234641/result.json`:11 checks aprobados, fallo de transporte real con0 movimientos, recuperación0/2→2/2 líneas con misma clave/actor y replay idéntico. No se indujo un fallo tras completar sólo1/2 líneas; los parciales por línea conservan su cobertura focal separada. Dos líneas producen exactamente dos movimientos:2 unidades a7.12MXN y3 a5.50MXN; cinco unidades propias conservadas por requerir devolución gobernada. Maestros propios inactivos, Purchasing restaurado a Inventory8004. No confundirlas con las tres unidades de compras de los lotes anteriores.
- Production/Maintenance: `cc20-11-production-20261018234806/result.json`,15 checks, `failure:null`. Orden activa pasa a paused por incidencia; reanudar bloqueada409. Resolver/cerrar libera máquina y hold, mantiene orden paused y no añade transición automática: exactamente un block y un release. Sólo resume explícito permite completar y recibir terminado. Ocho maestros propios inactivos, dos saldos propios0/0; documentos cerrados conservados.
- Evidencia Production:25 focales API/PG con rollback aprobadas en `cc20-production-evidence-combined-tests.log`; incluye GET autorizado del segundo actor. El primer fallo del test nuevo por override de dependencia y la colisión de módulos al combinar se corrigieron en el arnés, no en el runtime. No hay certificación GCS.

## Identidad certificada entre gates

`qa_candidate_identity.ps1` comprueba ocho servicios/revisiones, referencia de imagen por digest, `status.imageDigest`, SHA en ERCLAVE_VERSION y URL etiquetada. Smoke técnico público valida health/ready/version y vuelve a comprobar identidad antes de emitir `qa-candidate-revisions.json`. El artifact certificado se transfiere a qa-traffic junto con las ocho imágenes aprobadas. Promoción compara también el tráfico estable contra lo certificado antes de mutar, revalida identidad/tráfico durante aplicación y al terminar, y revierte en orden inverso todos los servicios intentados si hay fallo. Un tag cambiado con el mismo SHA/digest también se rechaza porque la revisión exacta difiere.

Evidencia `.local/cc20-traffic-manifest-tests.log`: smoke y12 escenarios con proveedor sustituido, sin red ni Cloud Run real. Incluye éxito; dos fallos parcialmente aplicados; drift de tag/digest/SHA/tráfico estable antes de escribir y durante aplicación; drift postflight con rollback. Es regresión del mecanismo, no certificación del proveedor ni de una promoción ejecutada.

La semántica del campo resuelto se contrastó con la [referencia oficial RevisionStatus de Cloud Run v1](https://docs.cloud.google.com/run/docs/reference/rest/v1/namespaces.revisions). El formato real y las identidades existentes de QA deberán observarse durante el release aprobado; no se consultaron recursos privados Cloud Run en este corte.

## Verificación general y huella del código probado

La corrida final `.local/chg335-verify-complete.log` terminó con **833 aprobadas,351 omitidas y1 advertencia existente** (52.07s de backend); validadores y compilación aprobados. No había ERCLAVE_TEST_DATABASE_URL global: los skips no son aprobaciones PostgreSQL. Las suites focales del tenant autorizado conservan su evidencia API/PG independiente; no sumar sus conteos superpuestos. La corrida general inicial fallida por imports y las posteriores832 aprobadas se conservan como antecedentes, no se ocultan.

Revisión final Inventory encontró `PATCH /v1/inventory/items/{item_id}` con un filtro de ValueError que dejaba actor conflict como500; se corrigió exclusivamente a409 `idempotency_key_reused`, manteniendo los422/409 conocidos. Focal API21 aprobadas; incluida en la verify final. Inventory se recargó Local después de coordinar la ventana UI.

Huella de los67 archivos fuente/configuración modificados del workspace: `457088ad8b6956c2f747de8b39e45137ab23aed28d885e40b0e4233b71354a3d`, listado `.local/chg335-source-manifest.json`, HEAD previo ef15b97db6dbc158d8368c6286bf983fa2710ee5. Excluye Markdown de gobierno y evidencia ignorada; no es SHA de commit ni artefacto QA.16 huellas de fuentes/Word coinciden con workspace y blobs HEAD, sin regeneración ni nueva revisión visual. El índice Git se contrasta antes de publicar.

El plan de QA preserva scopes existentes: sus titulares wildcard pueden ver nuevas Divisiones por la semántica vigente, aunque no se edite metadata. El baseline debe registrar y revisar esa visibilidad; no se crean grants wildcard. Monedas propuestas MXN/USD aún requieren confirmación y la estructura no certifica por sí sola maestros/documentos operativos ni historia CC-19.

## Cierre de formularios afectados · 2026-10-19

El corte iniciado el18 continúa y cierra sus comprobaciones finales el19, hora de Ciudad de México. El helper `resolveBusinessCode` tiene12 tipos documentales: Inventory warehouse/item, HR area/worker, Sales customer/quote/order/delivery y Production product_service/machine/recipe/order. Se comprobaron esos12 tipos en ES/EN mediante Chrome y APIs Local reales: Customer en el lote anterior y11 tipos adicionales con66 assertions (22 combinaciones formulario/idioma por3 comprobaciones: rechazo conserva captura/ARIA/foco, retry idéntico estable y corrección que crea/persiste). No equivale a probar todas las ramas o el circuito completo de cada formulario.

Evidencia nueva `.local/cc20-16-code-consumers-*`: lotes2026-10-19T05-49-25-376Z,05-55-01Z,05-56-21Z,05-57-39Z y05-59-59-914Z, entre otros desglosados por el agente en su matriz Local. Las primeras interrupciones de Production coinciden con recarga controlada8002 y se repitieron; otro arranque Chrome no llegó a inicializar ni crear fixtures. Se preservan esos intentos sin presentarlos como fallos del producto ni aprobaciones.

Consolidado `.local/cc20-16-code-consumer-regression-summary.json`: nueve browser.json,22 casos y66 assertions,23 snapshots de configuración restaurados (mode/prefix/separator/padding/status; next nunca disminuye) y huella app.js. Persistencia comprobada por recarga/API; en lotes mixtos algunas PNG conservan sólo el último idioma, mientras DOM/HTTP registran ambos.

La mayoría de duplicados devuelve409; Production order conserva su contrato: primer rechazo422 `production_order_code_already_exists`, retry idéntico409 `production_creation_attempt_failed` con misma CreateKey/payload y sin segunda allocation. Corregir código genera allocation/CreateKey nuevas y crea201; no se cambió esa política de errores.

Límites: Product/Service se ensayó como servicio; la rama Inventory `finished-good-link` requiere producto legado sin vínculo y no puede prepararse mediante las APIs actuales de alta, que exigen mapping. No se fabricó estado inválido por SQL. El formulario de orden Production compartido no certifica por inferencia todas las variantes de solicitud comercial ni la rama antigua inaccesible en modo API; sus recorridos API y límites se conservan separados.

Órdenes UI propias canceladas, recetas propias obsolete y borradores Sales propios cancelados. `.local/cc20-16-prerequisites-20261018235213/cleanup.json` acredita los dos pedidos preparados cancelados, diez maestros propios inactivos y dos balances propios con on_hand0/reserved0; los documentos congelados se conservan. Esto restaura también los ocho maestros reutilizados después de acreditar el cierre CC20-11. No se tocan los saldos de compras previamente declarados que requieren devolución gobernada.

## Cierre de runtimes Local y publicación

`.local/cc20-runtime-final.json`: ocho health200/ok/Local, ocho ready200/ready con database_configured/database_ready verdaderos, ocho service_name y URLs públicas con su puerto correcto. Se verificó mediante whitelist del entorno real de procesos que Firebase usa demo-erclave/Emulator9099, las URLs DB inspeccionadas son127.0.0.1:5434/erclave_local y las dependencias son loopback, sin registrar credenciales. Se preservaron los inventarios previos: sólo Admin carecía del nuevo campo readiness y cuatro servicios conservaban api_public_base_url8000 heredado de helpers de recarga. Después de UI/cleanup se recargaron exclusivamente Admin, Inventory, RH, Sales y Costing con configuración propia; Production/Purchasing/Maintenance conservaron PID. Sin seeds ni escrituras de negocio en esta recarga.

`/ready` Local acredita configuración, no consulta schema; la lectura real DB/head0062 se acredita por separado en `.local/chg335-pipeline-syntax/result.json`. No confundir ambos resultados. El commit de este corte conserva16 huellas fuente/Word comprobadas contra los blobs del índice Git. Publicar únicamente la rama previamente autorizada no abre PR, fusiona ni ejecuta los workflows manuales QA. El SHA y resultado del push se comunican después de comprobar la referencia remota.
