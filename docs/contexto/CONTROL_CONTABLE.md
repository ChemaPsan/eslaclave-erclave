# Control de preparación e integración contable

## Continuidad después de las correcciones · CHG-333

[Tres pendientes resueltos Local](../operaciones/correcciones_cc20_01_20261018.md): baja de membresía auditada, paridad de manuales y lectura de trazabilidad. Conserva CC20-01 aprobado Local; CC-20 permanece abierto por CC20-02–16. No modifica reglas contables, datos reales CC-19, head0062 ni despliegue QA.

## Aceptación CC-20 parcial comprobada · 2026-10-18

CC20-01 pasa en Local con evidencia integrada Admin/Maintenance y navegador real: selección y revocación de alcance, denegación de detalle/comandos/replays, exclusión de CSV y preferencia UI revalidada. [Acta](../operaciones/cc20_01_local_20261018.md). CC-20 permanece abierto para CC20-02–16 y alcance transversal CC20-13. Incidencia auxiliar de borrado de usuario con auditoría registrada y corregida Local en CHG-333; no implica activar Accounting ni completar CC-19. La preparación CHG-327 siguiente describe el estado anterior al ensayo.

## Configuración demo Local - CHG-328 - 2026-10-14

El tenant demo Local ahora tiene 2 Sociedades, 3 Divisiones y un Centro de costos activo por División, creados por Admin/Costing. La estructura habilita la preparación de casos entre Divisiones/Sociedades, pero aún faltan asignaciones, condiciones, actores restringidos y aceptación CC-20. Treinta y ocho registros legacy permanecen como excepciones sin backfill; CC-19 real sigue abierto. Accounting no tiene runtime y no se configuraron libros/cuentas/reglas.

## Preparacion CC-20 - CHG-327 - 2026-10-14

[Matriz de aceptación Local](../operaciones/cc20_aceptacion_integrada_local.md) lista para ejecutar después: 16 casos entre dueños, permisos y alcance, moneda, reintentos, CSV, historia y operación con Accounting apagado. Ninguno se ejecutó ni se marcó Pasa. La fila CC-20 permanece abierta y la matriz QA del ambiente publicado no cambia.

## Preparacion de datos CC-19 - CHG-326 - 2026-10-14

El usuario aun no dispone del padron ni las equivalencias reales. [Guia CC-19](../arquitectura/cc19_mapeos_y_configuracion_contable.md) separa mapeo operativo por registro de configuracion futura del modulo Accounting, con diagrama, roles de cuentas y preflight. La fila CC-19 de la matriz sigue abierta; no hubo backfill ni activacion contable. Operacion con Accounting apagado continua segun sus propias reglas.

## Implementacion CC-21 - CHG-325 - 2026-10-14

CC-21 implementado solo en Local. Production confirma costo unitario por Division en moneda base de Sociedad; Sales obtiene fuente autorizada, convierte con tasa explicita, calcula vista previa en borrador/envio y congela el estimado al aprobar. Pedido copia snapshots JSONB, separados de moneda/tasa del costo real. Falta de costo/tasa produce estimado/margen nulos sin bloquear aprobacion. El costo global sin moneda no se usa en documentos nuevos; reportes/UI distinguen historia sin snapshot. Migracion 0062 up/down/up Local sin backfill. CC-19/20, QA y Word pendientes. [Contrato](../arquitectura/cont_08_costo_estimado_cotizaciones.md). La revision CHG-324 siguiente es historica.

## Revision CC-21 - CHG-324 - 2026-10-14

La revision del costo estimado de cotizaciones se registra como CC-21, separado de CC-07/08 ya implementados. Sales usa hoy un `standard_cost` global de Production sin moneda/Sociedad y lo compara con el precio documental; asignar Division o aprobar no corrige la procedencia. El pedido copia ese estimado. El usuario confirmo permitir aprobacion con costo/margen nulos cuando falte costo confirmado o tasa. La implementacion monetaria CC-21 queda pendiente; esta revision no altera runtime ni historia. [Hallazgos y criterio](../arquitectura/cont_08_costo_estimado_cotizaciones.md).


## Actualizacion CC-18 - CHG-323 - 2026-10-14

CC-18 queda implementado solo en Local para Puestos RH, movimientos Inventory, proveedor/requisicion/orden/recepcion Purchasing y orden Maintenance. Admin asigna folios por tipo con permisos del consumidor e idempotencia; el dueno fija el codigo al crear y conserva el modo cuando aplica. En modo manual, movimientos internos Inventory sin captura reciben un codigo determinista del origen. Historia nullable sin renumeracion. Migracion 0061 probada up/down/up en PostgreSQL Local; pruebas focales por dueno, sin QA ni UAT integrado. Accounting apagado. Revision del costo estimado y CC-19/20 siguen pendientes. Las secciones CHG-322 y anteriores son historicas.

## Actualizacion CC-17 - CHG-322 - 2026-10-14

CC-17 queda implementado **solo en Local para los dos generadores imprimibles existentes**, cotizacion y orden de produccion. Admin entrega plantilla e identidad efectivas por Division con alcance y permiso consumidor; Sales congela al aprobar y Production al liberar. Cada dueno guarda su snapshot JSONB; impresiones historicas usan ese valor y los registros anteriores sin snapshot no se reconstruyen. Migracion 0060 probada up/down/up en PostgreSQL Local. Otros documentos todavia no tienen generador integrado y deben definir su propio consumo; CC-18, revision de costo estimado y CC-19/20 siguen abiertos. La fila historica CHG-320 de abajo describe el estado anterior a este corte.

## Corte histórico previo a CC-18 y CC-21 · CHG-322

Al cierre de CHG-322, CC-12 y CC-17 para cotizaciones/órdenes de producción estaban implementados Local; CC-18 y la revisión de costo estimado seguían abiertos. Ambos se resolvieron después en CHG-323 y CHG-325, como indican las secciones superiores. CC-19/20 separan datos y aceptación del desarrollo. Accounting sigue apagado.

## Qué hace cada dueño respecto a Contabilidad

| Dueño | Responsabilidad y dato que conserva | Relación con contabilidad; límites |
|---|---|---|
| Administración | Tenant, Sociedad, Emisor, División, permisos, alcance, configuración y autoridad de códigos. | Provee identidad/moneda y autorización. Dar de alta una Sociedad no crea un libro. |
| Costing | Catálogo de Centros de costos por División; analítica de costos como capacidad independiente futura. | El catálogo básico ya existe. No escribe pólizas ni activa Accounting. |
| RH | Trabajadores, puestos, asignaciones, tarifas y autoridad de capacidad laboral. | Aporta elegibilidad y tarifa confirmada; tiempo laboral no equivale a nómina o asiento. |
| Inventory | Existencias, reservas, movimientos, consumos, retornos y valuación operativa. | Conserva costo y moneda originales; futuros eventos no sustituyen movimientos ni crean efectos duplicados. |
| Production | Productos/servicios, maquinaria, recetas, órdenes, avances y costo productivo. | Coordina recursos; Inventory confirma movimientos. Fabricación/preparación no equivale a contabilización. |
| Sales | Cliente, condiciones, cotización, pedido, servicio y entrega comercial. | Conserva contexto y costo original/convertido; pedido no equivale automáticamente a factura/ingreso/CxC. |
| Purchasing | Proveedor, condiciones, requisición, OC y recepción comercial. | Inventory confirma bienes y solicitante acepta servicios. OC no equivale a factura/pasivo/CxP. |
| Maintenance | Orden correctiva, técnicos, tiempos, refacciones y recuperación. | Propaga imputación de origen y consumo; no escribe tablas RH, Inventory ni libro. |
| Expenses | Gastos/documentos/pagos futuros. | Planned; no asumir extracción fiscal, CxP o pagos por existir ficha o contrato. |
| Accounting | Libros por Sociedad, cuentas, periodos, mapeos, pólizas, reversas y conciliación futuros. | Planned; no escribe documentos operativos. Reconocimiento y reglas fiscales se definirán en su corte, no por analogía. |
| Reportes | Consultas operativas de cada dueño; inteligencia transversal futura. | Lecturas/reportes no prueban separación de productores; alcance también en CSV. Reporting transversal sigue planned. |

## Matriz vigente: preservar lo hecho y cerrar sólo la brecha

En todas las filas, los datos reales y la aceptación integrada son pendientes transversales CC-19/20. No repetirlos como nueva implementación de cada catálogo.

| ID / corte | Submódulo y dueño | Estado comprobado; conservar | Brecha y criterio de cierre | Fuente de implementación |
|---|---|---|---|---|
| CC-01 · CONT-01/02/03 | Organización/sesión · Admin | Implementado Local: Sociedades, Emisores, Divisiones, APIs/UI, scope v2 y selección activa. | No rehacer; mapear datos reales y comprobar cada consumidor, sin ampliar scopes por crear Divisiones. | [Organización](../../backend/services/admin-service/app/organization_store.py), [scope](../../backend/services/admin-service/app/organization_scope.py) |
| CC-02 · CONT-05 | Centros · Costing/Admin | Implementado Local: catálogo por División, código automático, permisos, revisión, estados y auditoría. | No rehacer; revalidar centro en consumidores donde el flujo habilitado lo exija. Analítica/libro no incluidos. | [Contrato y evidencia](../arquitectura/cont_05_catalogo_centros.md) |
| CC-03 · CONT-07 | Almacenes/artículos · Inventory | Implementado Local: almacén con División fija, artículo compartido con asignaciones y centro opcional. | No duplicar maestros; conservar consumidores CC-14 implementados CHG-317, preservar CC-13 y tratar historia en CC-19. | [Asignaciones](../../backend/services/inventory-service/app/organization_store.py) |
| CC-04 · CONT-07 | Productos/servicios/máquinas · Production | Implementado Local: asignaciones de productos/servicios y División fija de máquinas. | No rehacer; validar elegibilidad en orden/receta y moneda de tarifa CC-10/11. | [Asignaciones](../../backend/services/production-service/app/organization_store.py) |
| CC-05 · CONT-07 | Puestos/trabajadores · RH | Implementado Local: asignaciones, puesto confirmado y tarifa Decimal por División; trabajador compartido. | No rehacer tarifa/asignaciones/moneda confirmada CC-10; consumidor laboral CC-11 y fabricación CC-12 implementados. Datos reales y aceptación CC-19/20. | [Asignaciones RH](../../backend/services/hr-service/app/organization_store.py) |
| CC-06 · CONT-07 | Clientes/proveedores y condiciones · Sales/Purchasing | Implementado Local: identidad única, disponibilidad por División y moneda/pago/crédito o plazo explícitos sin herencia. | No rehacer. Consumir condiciones Purchasing en documentos CC-15; crédito capturado no prueba control de exposición. | [Condiciones y evidencia](../arquitectura/cont_07_commercial_condiciones.md) |
| CC-07 · CONT-08 | Cotización → pedido · Sales | Implementado Local para documentos con contexto: División fija, Sociedad derivada, snapshots, elegibilidad, scope y copia al pedido. | No rehacer conversión. Legacy pendiente CC-19; fabricación CC-12. Revisar costo estimado al extender política monetaria; no declarar esa revisión terminada. | [Cotizaciones](../../backend/services/sales-service/app/quote_context.py), [pedidos](../arquitectura/cont_08_pedidos_contexto.md) |
| CC-08 · CONT-08 | Servicios comerciales · Sales | Separación/ciclo implementados; CHG-314 añade original Sociedad, tasa y convertido por entrada. Implementado Local y pruebas técnicas aprobadas. | No rehacer adaptación monetaria. Aceptación integrada CC-20 y revisión específica del costo estimado de cotización pendientes. Historia sin moneda permanece nullable y bloquea aceptación nueva dimensionada; tratamiento explícito CC-19. No reconstruir ciclo. | [Contexto](../../backend/services/sales-service/app/service_context.py), [schemas](../../backend/services/sales-service/app/schemas.py), [regla previa del corte](../arquitectura/cont_08_servicios_contexto.md) |
| CC-09 · CONT-08 | Stock → reserva → entrega · Sales/Inventory | Implementado Local CHG-307, incluido costo original/convertido y reintentos. | No rehacer. Fabricación separada CC-12; aceptación/datos CC-19/20. | [Stock](../../backend/services/sales-service/app/stock_context.py), [evidencia](../arquitectura/cont_08_stock_contexto.md) |
| CC-10 · CONT-08/CHG-312 | Tarifas/capacidad · RH/Production | Implementadas Local las fuentes: tarifa Decimal/moneda Sociedad confirmada, historial nullable, consultas por División. RH entrega capacidad nominal/IDs compartidos; máquinas descuentan compromisos globales por fecha. | Conservar fuentes nuevas; consumidor manual de compromiso laboral implementado CHG-313; fabricación comercial CC-12 implementada CHG-315. RH no promete capacidad neta ni reserva personas. Consulta positiva y escritura integrada de fabricación aprobadas CHG-315; aceptación transversal CC-20 pendiente. | [Contrato y evidencia](../arquitectura/cont_08_tarifas_capacidad.md) |
| CC-11 · CONT-08 | Receta, orden y liberación · Production | CHG-313 conecta alta/validación manual, recursos por División, compromisos por persona/día e intento durable antes de reserva. Implementado Local para origen manual; aceptación integrada pendiente. | Gates técnicos de inicio/reanudación y costo/terminado aprobados; completar aceptación real integrada CC-20. Preservar alta manual y pruebas de reintento; origen comercial implementado CHG-315. No recrear infraestructura CHG-308. | [Preparación](../../backend/services/production-service/app/order_context.py), [consumidor API](../../backend/services/production-service/app/api.py) |
| CC-12 · CONT-08 | Pedido fabricado y terminado · Sales/Production/Inventory | Implementado Local CHG-315: prueba comercial autenticada, conversión única durable, recepción real, conciliación/reserva y entrega con costo original/convertido. | Recorrido HTTP real aprobado: 60MXN→3USD, reintentos sin duplicar stock; pruebas negativas/carreras y navegador. No reimplementar. Datos reales/aceptación transversal y QA quedan CC-19/20. | [Contrato y evidencia](../arquitectura/cont_08_fabricacion_contexto.md) |
| CC-13 · CONT-08 | Manuales/reversas/Kardex/saldos · Inventory | Implementado Local CHG-307: contexto, costo de Sociedad y filtros para recorrido adaptado. | No rehacer entradas/salidas/ajustes/reversas; historia incompatible requiere tratamiento explícito CC-19. | [Repositorio](../../backend/services/inventory-service/app/repositories.py), [contexto](../../backend/services/inventory-service/app/reservation_context.py) |
| CC-14 · CONT-08 | Transferencias, sobrantes, reservas otros productores, recepciones · Inventory y productor | Implementado Local CHG-317: proof durable Purchasing/Maintenance, conversión recepción a Sociedad, transferencias entre Divisiones misma Sociedad, sobrantes con costo/contexto originales y scope. Production/Sales conservados. | PostgreSQL, API y navegador interceptado; reintentos/carreras sin duplicados, alcance revocado, precisión y reservas Maintenance terminales sin reactivación. Datos/aceptación transversal CC-19/20; no equivale a cerrar documentos CC-15/16 ni QA. | [Contrato y evidencia](../arquitectura/cont_08_inventario_productores.md) |
| CC-15 · CONT-08 | Requisición/OC/recepción · Purchasing | Implementado Local CHG-319: División fija, Sociedad/moneda derivadas, condiciones explícitas congeladas, herencia a recepción incluso servicios; alcance de comandos/replays/listas/bandejas/CSV. | Conservar implementación y recuperación CC-14. Historia sin contexto no se autoasigna; datos y aceptación integrada siguen CC-19/20. No implica factura/CxP, devolución proveedor, folios CC-18 ni QA. | [Contrato y evidencia](../arquitectura/cont_08_compras_contexto.md) |
| CC-16 · CONT-08 | Correctivos/técnicos/tiempos/refacciones · Maintenance | CHG-320 integrado Implementado Local: contexto fijo, RH por División, tarifa/costo de tiempos, scope integral y refacciones heredadas. Conserva CC-14 y recuperación. | Pruebas Maintenance50, RH/Production123 y navegador271 aprobadas. Capacidad por persona/día UTC sólo Maintenance; sin reserva global Sales/Production. Datos CC-19 y aceptación CC-20 separados. | [Contrato/evidencia](../arquitectura/cont_08_mantenimiento_contexto.md), [schemas](../../backend/services/maintenance-service/app/schemas.py), [persistencia](../../backend/services/maintenance-service/app/repositories.py) |
| CC-17 - CONT-04 | Configuracion/emisor/impresion - Admin y duenos Sales/Production | Implementado Local CHG-322 para cotizacion y orden de produccion: plantilla e identidad efectivas por Division, snapshot al aprobar/liberar e impresion historica sin reconstruccion. | Otros generadores requieren integracion propia al existir; Word candidato, CC-20/QA pendientes. | [Regla](../arquitectura/plantillas_documentales.md), [resolver](../../backend/services/admin-service/app/scoped_configuration.py) |
| CC-18 · CONT-06 | Folios · Admin y cada dueño | Implementado Local CHG-323 para hr.position, inventory.movement, purchasing.supplier/requisition/order/receipt y maintenance.order. | Aceptacion CC-20, QA y documentos Word pendientes. Instrumentos de pago pertenecen al corte futuro. | [Autoridad](../../backend/services/admin-service/app/repositories.py), [plan CONT-06](../arquitectura/plan_preparacion_contabilidad.md) |
| CC-19 · migración transversal | Datos reales · Admin/Datos y dueños | Pendiente de configuración/mapeo; existen herramientas organizacionales, no backfill operativo completo. | Obtener estructura/asignaciones reales, previsualizar y migrar según alcance autorizado; conservar IDs/historia y tratar moneda no confirmada. No asignar automáticamente por tenant ni inventar Sociedad/División. | [Reanudación](INICIO_SESION.md), [plan de migración](../arquitectura/plan_preparacion_contabilidad.md) |
| CC-20 · aceptación transversal | QA/Seguridad/Sinergia y dueños | Pendiente de aceptación integrada y candidato QA; existen pruebas focales y browser interceptado. | Probar recorridos completos, permisos/alcance revocado, cruces, reintentos, CSV e historia con Accounting apagado; registrar evidencia por ambiente. Promoción requiere proceso autorizado. | [Estado](ESTADO_ACTUAL.md), [matriz QA](../qa/MATRIZ_EJECUCION_QA.md) |
| CC-21 - CONT-08 | Costo estimado de cotizaciones - Sales/Production | Implementado Local CHG-325: fuente confirmada por Division/Sociedad, tasa explicita, vista previa y snapshot al aprobar; pedido copia. | Historia nullable sin reinterpretacion, Word, QA y aceptacion CC-20 pendientes. | [Contrato](../arquitectura/cont_08_costo_estimado_cotizaciones.md) |

## Integración y libro futuros: no mezclarlos con separación operativa

Accounting y analítica Costing permanecen planned; la separación anterior funciona con Accounting apagado. El catálogo de centros no cambia ese estado. Evidencia: [capacidades](../../backend/services/admin-service/app/capabilities.py), [manifiesto contable](../../frontend/microfrontends/contabilidad/manifest.js), [servicio contable previsto](../../backend/services/accounting-service/README.md).

| Corte | Responsable y trabajo futuro | Criterio antes de declararlo implementado |
|---|---|---|
| CONT-09/10/11 | Dueños operativos + Arquitectura/API + Contabilidad: contrato de eventos económicos, outbox y productores Inventory/Production/Sales/Purchasing/Maintenance. | Identidad idempotente, momento económico confirmado, moneda/dimensiones, recuperación y conciliación documento → evento; sin contabilización fuera de activación. |
| CONT-12/13/14 | Accounting: libros por Sociedad, cuentas, periodos, mapeos, pólizas y reversas. | Asientos balanceados/inmutables, mapeo faltante visible, cierre/reapertura y activación/desactivación/reactivación probados. |
| CONT-15/16 | Dueños fiscal/comercial/Expenses/Accounting: fiscal, instrumentos de pago, facturación, CxC/CxP y dinero según plan. | Ownership y reconocimiento acordados, reglas fiscales verificadas cuando se implementen y conciliación de pagos. No asumirlos por una entrega/recepción operativa. |
| CONT-17/18 | Admin/dueños + Accounting/Reportes: copias de configuración, reportes y conciliación/cierre del programa. | Permisos y alcance de copia, historia estable y totales explicables por Sociedad, documento y moneda. |

Analítica de Costos necesita su propia entrega vertical. Devoluciones comerciales cliente/proveedor, nómina, preventivos, activos y otras funciones futuras no se contabilizan como reconstrucción de los flujos ya existentes. Ver [plan original CONT](../arquitectura/plan_preparacion_contabilidad.md) para alcance, sin convertir sus notas antiguas en pendientes actuales.

## Decisiones vigentes y mantenimiento del control

- Libro por Sociedad; Sociedad tiene un Emisor; División pertenece a Sociedad; centro pertenece a División. Admin/Costing/Accounting mantienen ownership separado.
- Centro obligatorio sólo en flujos de imputación habilitados. Catálogo básico disponible sin analítica ni Accounting.
- CHG-309 resuelto: costos y tarifas en moneda base de Sociedad para materiales, máquinas y mano de obra. Otra moneda documental conserva original, tasa explícita y convertido. Aplicación completa aún pendiente; no preguntar de nuevo ni reinterpretar historia sin moneda confirmada.
- Condiciones comerciales explícitas por División, sin herencia del maestro. No confundir esto con herencia de plantilla administrativa.
- Antes de asignar trabajo, leer la fila y evidencia. Distinguir maestro, consumidor, moneda, pruebas y despliegue; no reabrir un flujo cerrado por faltar una adaptación transversal.
- Al cambiar una fila: dueño técnico aporta rutas/contrato y pruebas; negocio valida regla/momento; custodio actualiza brecha y cierre, concilia PENDIENTES/ESTADO y registra CHG. QA distingue test simulado, DB, UAT y release. Una contradicción o evidencia insuficiente queda explícita, nunca se cierra por texto.
- Preservar CC-12 implementado CHG-315 junto con CHG-313/314; conservar CC-14 CHG-317 y conservar CC-15 CHG-319 y CC-16 CHG-320; continuar CC-17/18. CC-17/18 y mapeo CC-19 se coordinan sin repetir CC-01–09/13. CC-08 tiene adaptación monetaria Local probada; datos/aceptación CC-19/20 no se cierran por ello.

## Evidencia de esta conciliación

Revisión de código y contratos por tres agentes: Ventas/Inventory; Production/RH; Purchasing/Maintenance, más revisión principal Admin/Costing/folios/impresión y fichas contables/guardianes. No prueba nueva de funcionalidad por haber creado este control.

Evidencia histórica CHG-308: 231 pruebas focales; verify 532 aprobadas/152 omitidas. Las omisiones no son aprobaciones y esos resultados no certifican trabajos futuros. Validaciones propias de CHG-310: skill válida, agentes/tooling y coherencia documental aprobados; verify final aprobó validadores/compilación y 532 pruebas, con 152 omitidas y una advertencia. Suite sin DB, no UAT/browser nuevo ni aceptación de fabricación. Evidencia chg310-verify-final.log y TRAZABILIDAD; no hay migración, seed, activación contable ni despliegue en este corte.

### Referencias focales para comprobar cada capacidad

Estas referencias identifican pruebas existentes y el corte de origen; no afirman que se hayan ejecutado en CHG-310.

| Filas | Corte y pruebas que debe consultar el custodio |
|---|---|
| CC-01 | CHG-292/293: [comandos organizacionales](../../backend/services/admin-service/tests/test_organization_commands.py), [scope](../../backend/services/admin-service/tests/test_organization_scope.py), [scope PostgreSQL](../../backend/services/admin-service/tests/test_organization_scope_postgres.py). |
| CC-02 | CHG-297: [centros](../../backend/services/costing-service/tests/test_cost_centers.py), [autoridad de códigos](../../backend/services/admin-service/tests/test_cost_center_authority.py). |
| CC-03/09/13 | CHG-298/306/307: [Inventory organización/contexto/moneda](../../backend/services/inventory-service/tests/test_inventory_organization.py). Preservar capacidades previas; historia y aceptación integral siguen CC-19/20. |
| CC-14 | CHG-317: [proofs](../../backend/services/inventory-service/tests/test_cc14_proofs.py), [transferencias](../../backend/services/inventory-service/tests/test_cc14_handoffs.py), [sobrantes](../../backend/services/inventory-service/tests/test_cc14_returns.py) y [recepciones Purchasing](../../backend/services/purchasing-service/tests/test_receipt_context.py). Implementado Local con evidencia en TRAZABILIDAD; no equivale a UAT QA ni separación integral CC-15/16. |
| CC-04/10/11/12 | CHG-299/308: [Production asignaciones e intento/contexto](../../backend/services/production-service/tests/test_production_organization.py). Preparación probada no equivale a fabricación integrada. |
| CC-05/10 | CHG-300: [RH asignaciones, precisión y elegibilidad](../../backend/services/hr-service/tests/test_hr_organization.py). La consulta nominal y confirmación monetaria se implementaron en CHG-312; no confundir con aceptación integrada. |
| CC-06/07/08/09/15 | CHG-301–307: [Sales organización/recorridos](../../backend/services/sales-service/tests/test_sales_organization.py), [Purchasing proveedores/condiciones](../../backend/services/purchasing-service/tests/test_purchasing_organization.py). No cerrar documentos Purchasing ni moneda de servicios por estos resultados. |
| CC-17 | CHG-296 Admin y CHG-322 consumidor/snapshot: [configuracion por alcance](../../backend/services/admin-service/tests/test_scoped_configuration.py), [Sales](../../backend/services/sales-service/tests/test_sales_organization.py) y [Production](../../backend/services/production-service/tests/test_production_organization.py). |
| CC-18 | CHG-323: [Admin](../../backend/services/admin-service/tests/test_admin_api.py), [RH](../../backend/services/hr-service/tests), [Inventory](../../backend/services/inventory-service/tests), [Purchasing](../../backend/services/purchasing-service/tests), [Maintenance](../../backend/services/maintenance-service/tests). Evidencia y limites en TRAZABILIDAD. |


### Evidencia nueva CHG-313/314

326 pruebas focales PostgreSQL/API en ejecuciones por dueño (Production116,Inventory91,RH45,Sales74), sin omisiones; navegador transversal223 aprobadas con APIs interceptadas; verify588 aprobadas175 omitidas1warning sin DB. Logs y límites en TRAZABILIDAD. Smoke HTTP read-only tras recarga Local aprobado: una División autorizada, capacidad/máquinas200 vacías; no UAT de escritura ni ciclo real entre servicios.
