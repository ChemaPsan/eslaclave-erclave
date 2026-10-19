# Archivo histórico de INICIO_SESION.md · corte previo a CHG-311

> **Evidencia histórica, no instrucciones vigentes.** Conserva las notas acumuladas hasta CHG-310, archivadas el 2026-10-07. Las afirmaciones de estado, pendientes y autorizaciones corresponden a sus fechas y pueden estar sustituidas. Volver a la [fuente viva](../INICIO_SESION.md) antes de planear o ejecutar. El cuerpo original se conserva; únicamente los enlaces relativos se ajustan a esta ubicación.

# Inicio de sesion ERClave

## CHG-310 · Custodia contable y seguimiento · 2026-10-07

Leer [CONTROL_CONTABLE.md](../CONTROL_CONTABLE.md) antes de retomar: cada fila distingue implementado, brecha y dueño; preserva cotización/pedido/servicios/stock/manuales ya adaptados. La custodia corresponde al agente técnico contable con su skill. Próxima implementación sigue siendo CC-10/11/12 (tarifas/capacidad/fabricación); CC-08 tiene adaptación monetaria sin reabrir su ciclo. Este corte sólo actualiza documentación y seguimiento; reanudación técnica CHG-309/308 vigente, sin nuevos servicios/migraciones ni UAT. Verificación de regresión del corte documentada en TRAZABILIDAD.


## Punto de reanudación tras reinicio · CHG-309 · 2026-10-07

**Objetivo activo:** completar Producción por Sociedad/División, continuando CHG-308. El usuario reinicia su computadora; esta actualización sólo guarda contexto, no implementa otro bloque.

**Decisión resuelta:** El usuario confirmó: «sí, en la moneda base de la Sociedad; esto aplica para todo». Regla transversal para costos y tarifas de toda la operación, incluidos materiales, máquinas y mano de obra. Cuando un documento use otra moneda, conservar original y convertido con tipo de cambio explícito. No reinterpretar ni convertir automáticamente historia sin moneda confirmada. Funciona con Accounting apagado. No volver a preguntar esta política; su aplicación completa sigue pendiente de implementación.

**Estado real:** CHG-307 cerró stock → reserva → entrega/costo original-convertido en Local. CHG-308 sólo preparó contexto Production, intento durable y controles de alcance; fabricación dimensionada todavía NO habilitada. Alembic Local `20261007_0050`, working tree sobre HEAD 213f75c, con numerosos cambios anteriores sin commit que deben preservarse.

**Próximo trabajo autorizado:** confirmar/capturar moneda de tarifas en sus dueños (RH y máquinas), conectar selección/origen de División a validación y liberación, validar capacidad y recursos por División, conectar intento durable a reservas Inventory, consumo, recepción de terminado y fabricación desde Ventas; completar UI, contratos y pruebas integradas. Consultar agentes y skills transversales. No empezar de nuevo cotización/pedido/servicios/stock ya implementados.

**Archivos de entrada:** `docs/arquitectura/cont_08_produccion_contexto.md`, `backend/services/production-service/app/order_context.py`, `backend/alembic/versions/20261007_0050_production_context.py`, pruebas `test_production_organization.py`; luego API/repos de Production, Inventory, HR y Sales. Helpers `.local/chg308-tests.py`, `.local/chg308-start.py`, `.local/chg308-smoke.py` son referencias de esta sesión, no un arranque completo.

**Evidencia existente (no volver a atribuirla a cambios futuros):** 231 pruebas focales PostgreSQL/API; verify 532 aprobadas/152 omitidas; migración up/down vacío/up y smoke Local aprobados. Logs `chg308-tests.log`, `chg308-verify.log`, `chg308-migrate.log`, `chg308-smoke.log`. No hubo nueva UAT de fabricación ni cambios UI en CHG-308.

**Después del reinicio:** ejecutar contexto y revisar estado Git; comprobar/levantar PostgreSQL Local, Firebase Emulator y servicios con el procedimiento de Local aislado. No asumir que siguen encendidos ni reutilizar PIDs de esta sesión. Verificar 127.0.0.1:5434/erclave_local y tenant `ten_739ee59d765d5e14818674800d` antes de escribir. No reaplicar el helper de migración CHG-308: espera head 0049 y Local ya está en 0050. No usar QA como sustituto de servicios apagados.

**Pendientes que siguen vigentes:** estructura/mapeo reales para backfill; demás flujos Inventory, Compras, Mantenimiento, configuración/emisor/impresión/folios y aceptación transversal. No activar Accounting, no promover QA, no commit/PR ni inventar asignaciones reales.


## Actualización CHG-308 · 2026-10-07

Retomar Producción desde preparación CHG-308, head Local `20261007_0050`. No darla por terminada ni habilitar fabricación por tener snapshot. Decisión monetaria resuelta en CHG-309; aplicar moneda base de Sociedad a todas las tarifas. Preservar CHG-307 y cambios locales anteriores. Ver docs/arquitectura/cont_08_produccion_contexto.md.


## Actualización CHG-307 · 2026-10-05

Retomar desde CHG-307, Local `20261005_0049`. Stock dimensionado y moneda explícita implementados; seguir fabricación/otros módulos y datos reales. No volver a pedir política monetaria: ya confirmada. QA no promovido. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


**Política vigente:** costo en moneda de Sociedad y tipo explícito, implementada para stock en CHG-307. Mapeo real pendiente; no reinterpretar historia.

## CHG-306 — Preparación de reservas por División; separación en curso

Local `20261005_0048`: Inventory conserva contexto validado desde Sales en reservas y salidas; scope en consumo/liberación y lectura de movimientos/kardex/saldos/CSV. Sin backfill, sin activación Accounting ni promoción QA. El surtimiento dimensionado de productos sigue bloqueado: no declarar cierre del recorrido por esta preparación. [Contrato y evidencia](../../arquitectura/cont_08_reservas_contexto.md).

Moneda confirmada: costo en base de Sociedad y tipo explícito, implementación pendiente. Estructura/mapeo reales solicitados para migrar datos. Seguir los nueve frentes del plan: productos; Inventory; Production; Purchasing; Maintenance; configuración/impresión; folios; datos existentes; aceptación transversal. CHG-305 servicios ya cerrado Local; no repetirlo. Notas inferiores son historia de sus cortes, no una lista vigente acumulativa.


## CHG-305 — Ejecución de servicios por División (CONT-08 parcial)

Local head `20261005_0047` sin nueva migración. Servicios dimensionados habilitados: planeación/asignación/ejecución, tiempos/costos/evidencia y aceptación/cancelación; contexto fijo del pedido y recursos elegibles por División. Búsqueda acotada de trabajadores, claves estables por captura, locks pedido→servicio contra cancelación. Contabilidad/analítica no activadas; sin datos de ensayo permanentes, QA/Producción intactos.

Siguiente: propagación del surtimiento de productos a reservas/solicitudes de Producción y entregas; luego Compras. CONT-06, Emisor/impresión y mapeo real pendientes. Legacy sigue por tenant; no separación completa. Ver docs/arquitectura/cont_08_servicios_contexto.md y TRAZABILIDAD CHG-305. Apartados anteriores describen sus cortes.


## CHG-304 — Contexto conservado en pedidos (CONT-08 parcial)

Local `20261005_0047`: conversión de cotización aprobada dimensionada a pedido habilitada. Copia fija de División/Sociedad/condiciones/revisión; las órdenes de servicio consultan el contexto del pedido. Alcance en detalle/listas/reportes y cancelación autorizada. Surtimiento, entregas y ejecución de servicios dimensionados siguen bloqueados antes de efectos. Sin backfill ni datos dimensionados permanentes; Accounting/analítica opcionales, QA/Producción intactos.

Siguiente: propagar contexto a reservas/solicitudes/entregas y ejecución de servicios, luego Compras. CONT-06, Emisor/impresión y mapeo real pendientes. Documentos sin contexto mantienen comportamiento por tenant; no separación completa. Ver docs/arquitectura/cont_08_pedidos_contexto.md y TRAZABILIDAD CHG-304; secciones anteriores son históricas.


## CHG-303 — Contexto explícito en cotizaciones (CONT-08 parcial)

Local `20261005_0046`: cotizaciones borrador permiten asignar División explícita, Sociedad derivada y copia de condiciones comerciales confirmadas. Sin herencia, conversión monetaria ni backfill. La División queda fija; actualización explícita de condiciones sólo en borrador. Cliente, responsable y productos deben estar disponibles en esa División. Lecturas, listado y CSV de cotizaciones dimensionadas respetan alcance. Conversión a pedido bloqueada hasta propagar dimensiones. Cotizaciones heredadas sin contexto mantienen comportamiento por tenant: esto NO completa la separación.

Siguiente bloque: propagar contexto y snapshot a pedidos y documentos descendientes, luego documentos de Compras; siguen pendientes folios CONT-06, emisor/impresión por alcance y mapeo real. Accounting/analítica permanecen opcionales; no se exige centro en esta preparación. QA/Producción intactos. Evidencia y matriz contractual: `docs/arquitectura/cont_08_cotizaciones_contexto.md`, TRAZABILIDAD CHG-303. Apartados anteriores conservan el estado de sus cortes.


## CHG-302 — Condiciones explícitas por División

El usuario confirma opción 2, sin herencia. [Condiciones comerciales](../../arquitectura/cont_07_commercial_condiciones.md) implementadas Local por dueño Sales/Purchasing: moneda/pago y crédito del cliente o plazo del proveedor. Campos vacíos al configurar, persistencia por División, Sociedad confirmada, revisión/idempotencia/auditoría. Cambiar maestro no cambia condiciones guardadas; no se copian defaults. Asociación sin condiciones sigue pendiente de configuración.

Alembic `20260928_0045`, sin backfill ni condiciones permanentes. Accounting/analítica no se activan; QA/Producción intactos. Próximo bloque CONT-08: dimensiones y snapshots explícitos en documentos, validación del contexto/configuración y recursos. Documentos anteriores siguen por tenant; no hay separación operativa completa ni control de exposición crediticia. Folios CONT-06 y mapeo real pendientes. Evidencia CHG-302 en TRAZABILIDAD; apartados inferiores corresponden a sus cortes.

## CHG-301 — Disponibilidad comercial por División (CONT-07 parcial)

[Recorrido Sales/Purchasing](../../arquitectura/cont_07_commercial_asignaciones.md) implementado Local: cliente/proveedor único con asociaciones por División y Sociedad derivada, estado, revisión, idempotencia y auditoría propias. Admin autoriza; sin dependencia de Costing ni activación de Accounting/analítica. Alembic `20260928_0044`, sin backfill/asociaciones permanentes; QA/Producción intactos.

CONT-07 tiene recorridos Inventory/Production/HR/Sales/Purchasing. Condiciones comerciales por alcance y su aplicación a documentos CONT-04/07/08 siguen pendientes; los maestros y documentos anteriores siguen por tenant. No es separación operativa completa. Próximo bloque: reglas comerciales por dueño/alcance y propagación documental; también faltan folios CONT-06 y mapeo real explícito. Evidencia en TRAZABILIDAD CHG-301; apartados inferiores describen su corte histórico.

## CHG-300 — Asignaciones RH por División (CONT-07 parcial)

[Recorrido HR](../../arquitectura/cont_07_hr_asignaciones.md) implementado Local: puestos compartidos con estado, tarifa de costeo explícita y centro opcional por División; trabajadores con elegibilidad ligada a su puesto vigente confirmado. Cambio de puesto requiere reconfirmar asignación; no cambia nómina, recetas ni capacidad comprometida. HR conserva tablas y auditoría, Admin autoriza y Costing valida centros. Alembic `20260927_0043`, sin backfill ni asignaciones permanentes.

CONT-07 tiene recorridos Inventory/Production/HR; siguen Sales/Purchasing. CONT-08 pendiente: APIs/catálogos/documentos anteriores continúan por tenant. Sin aislamiento operativo completo ni activación de Accounting/analítica. Mapeo real de datos pendiente. QA/Producción intactos. Evidencia en TRAZABILIDAD CHG-300; notas inferiores conservan el estado de su corte.

## CHG-299 — Asignaciones de Producción por División (CONT-07 parcial)

[Recorrido Production](../../arquitectura/cont_07_production_asignaciones.md) implementado Local: División fija de máquina y asignaciones de productos/servicios compartidos con centro opcional. Production conserva tablas/auditoría; Admin autoriza scope v2 y Costing valida centros. Alembic `20260927_0042`, sin backfill ni asignaciones de negocio permanentes. Accounting/analítica no se activan.

CONT-07 tiene recorridos Inventory y Production; siguen HR/Sales/Purchasing. CONT-08 pendiente: recetas, órdenes, movimientos y catálogos heredados continúan por tenant; estas asignaciones no acreditan aislamiento operativo completo. Estructura/mapeo reales pendientes. QA/Producción intactos. Evidencia en TRAZABILIDAD CHG-299; apartados anteriores conservan el estado de su corte.

## CHG-298 — Asignaciones de Inventarios por División (CONT-07 parcial)

[Primer recorrido Inventory](../../arquitectura/cont_07_inventory_asignaciones.md) implementado Local: División fija del almacén, asignaciones de artículos compartidos, centro opcional validado por Costing, scope/permisos por API, revisiones, idempotencia y auditoría. Alembic `20260927_0041`, sin backfill ni asignaciones de negocio permanentes. La asignación inicial de almacenes heredados requiere alcance completo. No activa Contabilidad ni analítica.

CONT-07 sigue pendiente en Production/HR/Sales/Purchasing; CONT-08 no iniciado: catálogos, movimientos y documentos heredados aún no se aíslan por División. Nueva consulta de artículos disponibles prepara esa integración. Estructura real y mapeo explícito pendientes antes del backfill. QA/Producción intactos. Evidencia final en TRAZABILIDAD CHG-298; secciones inferiores conservan el estado de su corte.

## CHG-297 — Catálogo básico Local

Implementado [CONT-05](../../arquitectura/cont_05_catalogo_centros.md): Centros de costos desde Administración → Organización → Divisiones, dueño Costing en API 8014 y esquema propio. Alta/nombre/estado, código automático Admin, permisos puntuales, alcance, revisión, idempotencia y auditoría. Catálogo independiente de analítica y Accounting; obligación sólo por flujo habilitado. Alembic Local `20260927_0040`; sin centros ni estructura ficticios permanentes. Runtime Local recargado; QA/Producción intactos. Pruebas: 35 focalizadas (2 PostgreSQL con rollback), suite browser 134 y siete casos finales del catálogo aprobados; verify 442 aprobadas/99 omitidas sin DB. Smoke Emulator/API real sin escrituras de negocio, 200/401/403/404 esperados.

Siguiente: configuración por dueño/consumidor (CONT-04 parcial), folios transversales CONT-06 y asignaciones de maestros/documentos CONT-07/08. La numeración de centros ya tiene autoridad dedicada. Backfill real pendiente de estructura/mapeo explícitos. Manual Word pendiente; fuente actualizada. No declarar separación completa por disponer del catálogo. Evidencia final en TRAZABILIDAD CHG-297; apartados inferiores conservan el estado de su fecha.

## CHG-296 — avance CONT-04 Local

Además de la matriz de capacidades, se implementa [plantilla por Sociedad/División](../../arquitectura/cont_04_configuracion_por_alcance.md): tabla admin.scoped_settings, API GET/PUT, editor desde Organización, herencia visible, revisión/idempotencia/auditoría y restauración sin borrar historial. Alembic Local `20260927_0039` aplicada; upgrade/downgrade vacío/upgrade comprobados. No se crearon datos organizacionales permanentes. Fixtures en el tenant autorizado con rollback.

CONT-04 queda parcial a nivel transversal: faltan configuraciones de cada dueño y consumo/snapshots en documentos. Impresiones aún corporativas; no declarar separación completa. Continuar CONT-05/06/07/08 con catálogo básico y obligación sólo por flujo confirmados. Ver TRAZABILIDAD para evidencia final; no hay promoción QA/Producción.


## CHG-296 — disponibilidad de capacidades y política confirmada

El usuario confirma catálogo básico desde Administración sin activar analítica/Accounting, y Centro de costos obligatorio sólo por flujo de imputación habilitado. [Matriz vigente](../../arquitectura/matriz_capacidades_organizacionales.md). Sesión agrega contrato versionado de capacidades en código, con planned apagado aun ante flags/grants; disponibilidad no concede permisos ni prueba configuración lista. El avance CONT-04 y su migración están descritos arriba; no hay seeds ni cambios QA/Producción. Catálogo y propagación siguen pendientes. No repetir la pregunta de obligatoriedad; estructura y asignación de datos existentes todavía pendientes.


## CHG-295 — plan de ejecución modular

Preparado el [plan por fases](../../arquitectura/plan_separacion_modular_y_contabilidad_opcional.md), solicitado por el usuario. Primero contrato de capacidades/obligatoriedad, después CONT-04/05/06/07/08 para separación operativa; eventos y Contabilidad opcional después. Incluye responsables, migración, activación/apagado/reactivación y pruebas con módulos parcialmente activos. No se implementan funciones ni se habilitan módulos en este corte; último runtime CHG-293. La asignación real de datos existentes sigue pendiente, sin impedir trabajo independiente. Próxima entrega: matriz de capacidades y condiciones por flujo antes de CONT-04.


## CHG-294 — Contabilidad opcional y fronteras de activación

Usuario solicita analizar módulos no siempre activos. [Criterio y recomendaciones](../../arquitectura/contabilidad_opcional_y_capacidades.md): organización/operación independientes de Accounting, catálogo básico de centros con dueño Costing y superficie Admin, analítica y contabilidad por activación propia. Skills accounting/module-boundaries y fichas actualizadas. Sin cambios de APIs, runtime, datos ni entitlements; CHG-293 sigue siendo el último corte funcional.

Antes de CONT-05/07/08 concretar autorización de la capacidad básica de centros y política de obligatoriedad cuando no se usan costos/contabilidad. No reinterpretar silenciosamente la obligación anterior ni bloquear operación con un módulo apagado. En futuros eventos/libros definir fecha de inicio, desactivación, jobs e historia sin replay automático. QA/Producción sin cambios.


## CHG-293 — sesión y alcance Local; continuar CONT-04

Leer [CONT-03](../../arquitectura/cont_03_sesion_alcances.md) y [cobertura de agentes](../../arquitectura/cobertura_agentes_modulos.md). El usuario pidió ejecutar el plan de separación y fortalecer Contabilidad/guardianes; las fichas y skills ya están reforzadas. Sesión v2, editor de membresía y selector validado implementados Local; una membresía del demo fue convertida con hash revisado, sin ampliar su wildcard previo. Seeds y onboarding preservan el alcance. No repetir CONT-00 ni volver a preguntar permiso genérico para continuar Local.

Siguiente CONT-04 configuración, después CONT-05 centros y CONT-07/08 maestros/documentos. Hace falta la estructura y asignación explícita de registros existentes para el backfill operativo; se preguntó al usuario y no se inventaron Sociedades/Divisiones. QA no autorizado. Revisar ESTADO_ACTUAL/PENDIENTES y procesos antes de iniciar servicios otra vez. El fallo inicial del arranque fue del sandbox; el arranque posterior usa sólo recursos Local.

## CHG-292 — continuar desde CONT-03

CONT-02 ya implementa APIs y formularios de Emisor/Sociedad/División en Local. Leer [su contrato](../../arquitectura/cont_02_administracion_organizacional.md), ESTADO_ACTUAL y PENDIENTES antes de cambiar escritores o sesión. Local usa Alembic `20260925_0038`, autoridad normalizada y JSON compatible; no asumir que el JSON sigue siendo editable como estructura. Siguiente: sesión/scopes y División activa (CONT-03). No reabrir decisiones CONT-00; no promover el candidato QA histórico.

## Reanudación CHG-291 — trabajar en Local

La última instrucción corrige QA por Local. El arranque canónico desde el workspace original quedó activo: frontend 4173; APIs 8000/8002/8004/8006/8008/8010/8012; PostgreSQL 5434 erclave_local/0037; Firebase Auth Emulator 9099 y UI 4000. Comprobar procesos antes de volver a ejecutar start_local.ps1, que rechaza puertos ocupados. No reanudar publicación/PR ni gates QA de CHG-290: ese candidato quedó como preparación histórica.

## Reanudación CHG-290

Commit listo: `2a91d196175f589745f0e8831a053138f7475efa`, aún sólo Local. No reconstruir el candidato mezclando cambios previos.

QA solicitado, no promovido. Rama aislada agent/chg290-cont01-qa en .local/qa-cont01; leer docs/operaciones/release_qa_20260923_cont01.md. Certificación: verify 344/67 omitidas y focalizadas 51/cero omitidas. Workspace original preservado. APIs QA 500/503, Hosting 200; se requieren versiones efectivas antes de promoción y resolver el alcance global de configuración obligatoria del pipeline.

## CHG-289 — continuar desde CONT-02; decisiones ya resueltas

CONT-00 cerrado por respuesta directa del usuario: un Emisor para varias Sociedades; una Sociedad con un solo Emisor; libros por Sociedad; centros obligatorios por División dados de alta desde Administración y seleccionados por División activa; moneda base configurable inicialmente MXN y transacciones multimoneda con tipo capturado. No volver a pedir estas respuestas.

CONT-01 implementado Local: leer [estructura organizacional](../../arquitectura/cont_01_estructura_organizacional.md). Alembic Local `20260922_0037` aplicada; JSON actual intacto y aún autoritativo. CONT-02 debe completar APIs/UI y la reconciliación/switch compatible; no activar lectores de las tablas preparadas sin resolver cambios posteriores del JSON. Tenant Local vacío de razones sociales/sucursales; no inventar registros a partir del fallback de sesión.

51 pruebas focalizadas aprobadas/cero omitidas, incluidas 9 PostgreSQL transaccionales. Gate `npm.cmd run verify` aprobado: validadores, compilación y 355 pruebas/67 omitidas sin DB; las 9 nuevas de DB pasaron por separado. Usar Node/npm de `AppData/Local/Programs/nodejs` y Python de `backend/.venv`; el `.env` mezcla una URL QA con la de Inventory Local: seleccionar sólo la Local validada, nunca cargarlo entero para migrar. QA sigue documentado `e57237f/0036`. Las instrucciones CHG-286/287/288 de esperar decisiones son historia, no gates pendientes.

## CHG-288 — ejecución iniciada, decisiones CONT-00 pendientes

Leer primero [CONT-00: decisiones y preflight](../../arquitectura/cont_00_decisiones_y_preflight.md). El usuario ya indicó aplicar el plan; falta su respuesta a las tres preguntas funcionales agrupadas (estructura/libro, Centro de costos y moneda). Registrar la respuesta sin volver a pedir autorización genérica. No iniciar migraciones dependientes hasta cerrar esas reglas.

`tools/preflight_organization.py` analiza un archivo JSON original sin conectarse ni escribir; 21 pruebas focalizadas offline aprobadas. No se ejecutó contra datos reales ni se crearon modelos/Alembic. Usar `backend/.venv/Scripts/python.exe` para pytest; el Python global carece de pytest. Node/npm están instalados en `C:/Users/JoseMaríaPadillaSánc/AppData/Local/Programs/nodejs`, fuera del PATH inicial; añadir esa carpeta al PATH sólo de la sesión permite usar los comandos canónicos. Gate completo `npm.cmd run verify` aprobado: validadores, compilación y 334 pruebas/58 omitidas sin DB. El intento previo con el runtime de VS Code falló al salir de sintaxis y fue sustituido por la ejecución real de Node.

## CHG-287 — ruta de implementación contable

Usar `docs/arquitectura/plan_preparacion_contabilidad.md` como secuencia vigente. Iniciar por `CONT-00` y no crear migraciones hasta ratificar las decisiones que afectan cardinalidades y libros. El primer corte técnico posterior es `CONT-01`, limitado a modelo/migración organizacional con compatibilidad; no mezclarlo con la propagación operativa ni con Accounting.

## CHG-286 — preparación contable pendiente de decisiones

El análisis vigente está en `docs/auditorias/impacto_preparacion_contabilidad_2026-09-21.md`. No asumir que Sociedad, División, Emisor o Centro de costos ya existen como dimensiones persistidas: hoy la organización sigue en `organization.profile` y los documentos operativos continúan esencialmente a nivel tenant. Antes de implementar, cerrar la semántica Sociedad–Emisor y el dueño del libro. El primer corte recomendado es la normalización organizacional y de scopes; Accounting sigue `planned`.

## CHG-285 — selectores revisados

Ventas conserva referencias comerciales históricas sin sustitución silenciosa. La auditoría transversal está en `docs/auditorias/catalogos_selectores_transversales_2026-09-20.md`; no convertir enums cerrados en catálogos. Siguiente comprobación: ejecutar el caso Playwright de Cliente/Cotización con stack Local aislado. QA continúa sin CHG-284/285.

## CHG-284 — siguiente comprobación de Compras

Proveedor usa `GET /v1/purchasing/reference-data` y catálogos comerciales activos de Administración en Local. Para continuar este corte, levantar el stack Local aislado y ejecutar el caso Playwright de proveedor; no interpretar el preflight fallido anterior como fallo de la funcionalidad. QA continúa `e57237f/0036` sin este cambio.

## CHG-283 — rutas rápidas para trabajo nuevo

Al reanudar, ejecutar `npm run session:context`; si falta Node/npm, usar `python tools/context_brief.py` y leer `ESTADO_ACTUAL.md`. El resumen es documental y no verifica QA remoto. Para formularios y campos aplicar `$erclave-form-contract` junto con `$erclave-form-feedback` cuando cambie su validación o feedback. Para resultados UAT aplicar `$erclave-qa-evidence`. El piloto Local de Producto/Servicio y Proveedor está en `docs/auditorias/piloto_contrato_formularios_2026-09-20.md`; sus decisiones funcionales siguen pendientes. Sin cambios de runtime ni QA en CHG-283.

## CHG-282 — cierre editorial y decisión QA

CHG-281 sigue certificado solo en Local. Su promoción QA espera el resultado de la prueba autenticada de OP-000003 y después requiere candidato inmutable y gates independientes del pipeline. La versión QA documentada continúa en e57237f/0036; reconfirmar `/version` antes de cualquier candidato. Los ocho Word siguen pendientes de revisión visual y publicación. La revisión del 20 de septiembre no desplegó ni escribió datos remotos; ver `ESTADO_ACTUAL.md`, `PENDIENTES.md` y `docs/manuales_solucion/REGISTRO.md`.

## CHG-281 — tolerancia a demoras solo Local

Se coordinan esperas de autorización10 s/dependencias12 s con presupuesto cooperativo25 s y frontend35 s (incluye lectura del cuerpo). Una sola llamada por intento, sin reintentos automáticos; correlación entre APIs y diagnóstico nuevo solo Local. El formulario distingue evidencia confirmada de avance cuyo resultado no se ha confirmado. Pruebas con HTTP loopback y browser interceptado; no UAT ni carga QA. No cambios de nube, migraciones o datos. QA permanece e57237f/0036.

Verificación CHG-281: `verify:postgres` aprobado, 368 pruebas/cero omitidas con fixtures temporales Local autorizados y limpieza; 111 pruebas browser aprobadas. Sin cambios remotos.

Incidente previo confirmado: las evidencias escritas de OP-000003 sí se guardaron con200; falló PATCHstatus503 por arranqueRH6.855 s. Las notas CHG-280 de falta de guardado corresponden a su observación anterior. Carga/descarga de adjuntos y cierre QA siguen pendientes. Detalle y límites: [auditoría](../../auditorias/timeouts_local_2026-09-16.md).

## Estado vigente CHG-280 — QA publicado y revisión documental

QA está desplegado en `e57237fe90319f88e1db8ed8d2e686604d2d9c54`: release [34932659212](https://github.com/ChemaPsan/eslaclave-erclave/actions/runs/34932659212) con preflight, migrate, deploy_candidate, promote_traffic y frontend completados correctamente. Las siete APIs públicas reportaron ese SHA y la interfaz publicada muestra el formulario nuevo de evidencia del servicio. La revision vigente de Cloud SQL QA es `20260913_0036`. El frontend se reconstruye durante release; no se afirma identidad build-once.

Feedback de formularios, margen esperado sin máximo 100 y evidencia de servicios ya están desplegados en QA. Pruebas Local registradas: 360 aprobadas, cero omitidas con PostgreSQL, incluidas las 55 integraciones históricas; 185 pruebas browser. Estos resultados no equivalen a UAT autenticada completa en QA.

Smoke QA observado: intentar pasar la orden de servicio a espera de recursos abre recepción/inicio; guardar descripción vacía muestra error junto al control, resumen accesible y mantiene Liberada/0%. La carga sintética no pudo completarse por el permiso de acceso a archivos locales de la extensión Chrome. No se guardó evidencia ni se comprobó descarga, cierre al 100%, expiración remota o aislamiento entre dos tenants en QA.

Fixture autorizado: servicio `prd-000002`, receta `rec-000002` y orden `OP-000003` (`ord_5965211f77a37f8e3220fa8025`), empresa Es La Clave, sucursal Edo. Mex 56495. El ID técnico de tenant no se mostró en UI; no se extrajeron tokens. Conservar los registros para continuar el smoke y registrar su cierre posterior. No repetir la solicitud de cuenta ni crear otra orden por inferencia.

Revisión complementaria de manuales, agentes y arquitectura en CHG-280. Ver [registro de manuales](../../manuales_solucion/REGISTRO.md) y [entrega al tester](../../qa/ENTREGA_TESTER.md) para cobertura, artefactos y límites de revisión. Evidencia de despliegue y revisiones: [release](../../operaciones/release_qa_20260914.md).

### Pendientes vigentes del cierre

- Completar carga y descarga autenticada, evidencia final al 100%, regresión de producto y pruebas de permisos/aislamiento QA con identidades autorizadas; no declarar paridad completa.
- Completar revisión visual de los Word si no hay un renderizador disponible; la validación estructural no la sustituye.
- Mantener separados despliegue exitoso, casos de prueba previstos y aceptación funcional del tester.
- Publicación de esta actualización documental pendiente; no constituye otro despliegue de runtime.

## Antecedentes históricos

Las notas CHG anteriores que siguen describen su fecha de ejecución. Sus menciones de QA anterior, pruebas omitidas, tráfico pendiente o capacidades solo Local quedan sustituidas por el estado vigente anterior y no son instrucciones pendientes de repetir.

## Datos de prueba autorizados CHG-279

El usuario autorizó crear servicio y orden en la sesión QA activa. Consola funcional confirmada como API QA, empresa Es La Clave y sucursal Edo. Mex56495. Se creó servicio `prd-000002` (QA Evidencia servicio e57237f), receta aprobada `rec-000002` / `rec_790f962694ee48cbafca788366` y orden `OP-000003` / `ord_5965211f77a37f8e3220fa8025`. Cantidad1E48, prioridad baja, una etapa Producción, recurso existente Empacador A por6MIN y costo planeado3. No materiales ni movimientos de almacén creados.

Alta mediante formularios/API QA de la sesión autorizada; validación de recursos correcta y persistencia de la orden comprobada tras recarga. Estado Liberada/0%. El identificador técnico del tenant no se mostró en UI; se verificaron empresa, sucursal y cuenta de sesión, sin extraer tokens. Registros quedan disponibles para el smoke, no cancelados ni inactivados todavía. Cierre previsto: conservar referencia de auditoría y cancelar/inactivar los registros de prueba cuando termine la validación.

La página publicada aún sirve el formulario anterior de avance sin campos de evidencia; se abrió y canceló sin guardar. No se cargaron adjuntos ni se comprobó descarga autenticada. El release34932659212 sigue esperando en qa-traffic. La sesión autenticada y fixtures están resueltos; falta habilitar la vía de prueba del candidato sin afirmar que el frontend viejo valida el cambio. No repetir la solicitud de cuenta u orden al usuario.

## Promoción CHG-278 — candidatos verificados, tráfico pendiente

PR #15 fusionado tras CI34931780981 aprobado. SHA inmutable: `e57237fe90319f88e1db8ed8d2e686604d2d9c54`. Candidato34932158226 aprobado, siete imágenes verificadas; archivo del manifiesto SHA256 `50f6df93bd59f09ce3198cf43f1a64cbbb782888bb23a483c28bc7fb256c8cde`.

Release34932659212: preflight, migración/configuración y servicios aprobados. Jobs Cloud Run `erclave-migrate-qa-f8hkh` y `erclave-configure-tenant-qa-cj7hz` completados. Migración aprobada hasta `20260913_0036`. Copia automática de erclave-qa-postgres del14 septiembre completada y PITR habilitado con7 días verificados en consola; no se restauró ni copió DB Local.

Siete revisiones candidatas al0% de tráfico y smoke health/ready/version aprobado. `qa-traffic` pendiente; frontend no ejecutado. El tráfico público conserva b63cdad, verificado antes de crear candidatos. Falta prueba autenticada de carga/descarga de evidencia con cuenta y orden de prueba autorizadas; solicitadas al usuario, no crear fixtures funcionales QA por inferencia. No declarar paridad/UAT completa. Revisión visual Word pendiente.

Local:360 pruebas aprobadas/cero omitidas con PostgreSQL, incluidas las55 históricas. Bucket privado/lifecycle365/IAM mínimo y variable GitHub ya configurados en CHG-277. El usuario autorizó explícitamente publicar identificadores técnicos en el PR público; no se publicaron credenciales.

Evidencia y digests en `docs/operaciones/release_qa_20260914.md`. No aprobar tráfico hasta cerrar el smoke autenticado previsto en el plan. Continuar el mismo run/candidato, sin reconstruir ni ejecutar deploys locales.

## Preparación QA y manuales CHG-275

Revisión 2026-09-14: siete manuales y guía actualizados para Local con capacidades pendientes de QA; 65 casos en guía/matriz (56 base +9 nuevos), sin aceptación inferida. Las siete APIs QA reportan b63cdad en /version. Se preparó QA_EVIDENCE_BUCKET en qa-release; bucket/IAM aún requieren aprovisionamiento autorizado y smoke. Local head `20260913_0036`; QA documentado `20260908_0034` sin cambios.

Selección segura:29 aprobadas sin skips (23 DB históricas,3 schemas históricos,3 DB nuevas). De las55 históricas antes omitidas se verificaron26 y quedan29 bloqueadas por fixtures de otros tenants/limpieza amplia. No lanzar verify:postgres completo. Detalle, rollback, matriz API y gates en `docs/operaciones/release_qa_20260914.md`. Sin publicación de rama/PR, migración o deploy QA.


## Evidencia de servicios CHG-274 — solo Local

Validación CHG-274:185 browser aprobadas;19 focalizadas (14 archivo/optimización,3 API y2 PostgreSQL), verify292 aprobadas/58 omitidas en corrida sin DB. Las2 integraciones nuevas sí se ejecutaron por separado, al igual que la de margen del corte anterior;55 generales siguen pendientes. Reversa y expiración reales en fixtures, permisos y tamaños comprobados; revisión visual390/760/1280 y tema oscuro.

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.


## Margen esperado sin tope CHG-273

Validación CHG-273:14 pruebas focalizadas aprobadas, incluida PostgreSQL real;23 browser de contratos y98 feedback aprobadas; verify275 backend aprobado. En la corrida genérica se omiten56 integraciones;1 (margen) se ejecutó aparte contra DB real,55 generales previas siguen pendientes. API Local8002 reiniciada y esquema servido sin máximo100 comprobado.

CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.


## Continuidad Local CHG-272: formularios corregibles

Leer `docs/auditorias/formularios_feedback_2026-09-13.md` antes de tocar formularios, validaciones o payloads. Aplicar `.agents/skills/erclave-form-feedback/SKILL.md` conforme a `AGENTS.md`: conservar errores estructurados, rutas exactas e indices enviados, captura, ES/EN, foco y ARIA. No deducir campos por texto diagnostico ni afirmar cobertura total por instalar el helper.

Estado: 54 variantes registradas; 174 pruebas browser aprobadas (98 offline, incluidos 14 Backoffice; 22 MAIN y 54 regresion). `verify` y validate aprobados: 262 backend, 55 omitidas sin DB y sintaxis 79. Skill valida y diff limpio. Sin gates tecnicos pendientes de ejecucion del corte; UAT y promocion QA permanecen pendientes. Preservar CHG-271 y todos los cambios del working tree. Solo Local; no publicar, migrar ni promover por inferencia. QA continua en `b63cdad`; la evidencia UAT sigue pendiente.

## Manuales y guía del tester CHG-271

CHG-271 sincroniza los siete manuales funcionales Markdown/Word y la guía de pruebas con QA `b63cdad`, revisión documental 2026-09-10. Entrega: `docs/qa/ENTREGA_TESTER.md`; generación reproducible de tablas y procedimientos mediante herramientas documentales. No cambia runtime, contratos, migraciones, datos, permisos ni despliegues. No publica documentos en GitHub.

Incidencia identificada por revisión de código: la bandeja para solicitar sobrantes de Mantenimiento busca `.submodule-screen`, ausente en su render; confirmar/corregir acceso por el agente técnico de Mantenimiento y QA. No se declara disponible el recorrido completo desde pantalla. Compra directa soportada por API pero no expuesta en alta de órdenes de la UI. Ambos límites constan en manuales/guía. UAT autenticada continúa pendiente del tester.


## Estado vigente tras release QA CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff vigente: `docs/contexto/REANUDACION_CHG269.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.

Las notas de preparación y cortes anteriores que siguen son evidencia histórica; no deben disparar un release duplicado.


## Promoción QA en preparación CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Continuidad vigente CHG-268

CHG-268 recupera reservas/cancelaciones de refacciones interrumpidas bajo locks por tenant/orden/solicitud y conserva claves Inventory. Corrige serialización Decimal; Mantenimiento ofrece reintento ES/EN con permiso propio, Almacén confirma la entrega por separado. MTO-000001 recuperada en Local: una reserva de 1 H87, existencia física 2, disponible 1, sin salida ni duplicados. Sin migraciones ni permisos nuevos. Detalle: `docs/auditorias/recuperacion_refacciones_2026-09-08.md`.


## Continuacion CHG-264

Materiales de Produccion se entregan desde Movimientos antes del inicio. Leer `docs/auditorias/materiales_produccion_movimientos_2026-09-08.md` y ESTADO_ACTUAL. Cabeza Local `20260908_0034`; preservar CHG-262/263, sin promover por inferencia.

> Continuacion Local CHG-263: la entrega de refacciones se confirma desde Movimientos de Almacen. Consultar `docs/auditorias/refacciones_movimientos_2026-09-07.md`; se conserva el working tree previo de CHG-262 y QA no cambia.

Este documento define el orden obligatorio para recuperar contexto antes de analizar o modificar el proyecto.

> Handoff activo: leer `docs/contexto/REANUDACION_CHG261.md`. El arbol quedo consolidado en commits locales hasta CHG-260; distinguir siempre ese estado Local del release QA inmutable y no promover, migrar ni desplegar por inferencia.

> Continuacion Local CHG-262: leer `docs/auditorias/frontend_backend_2026-09-07.md` y `ESTADO_ACTUAL.md`. Hay correcciones posteriores al handoff CHG-261 en el working tree; el estado limpio de aquel handoff es historico.

## Secuencia

1. Ejecutar `npm.cmd run session:context` desde la raiz.
2. Leer completamente `AGENTS.md` y las secciones aplicables de `AGENTES.md`.
3. Leer `docs/contexto/ESTADO_ACTUAL.md`, `DECISIONES.md`, `TENANTS.md`, `PENDIENTES.md` y cualquier handoff activo enlazado arriba.
4. Leer `docs/arquitectura/gobierno_documentacion_viva.md`, el documento de `modulos/` correspondiente y las fuentes de arquitectura que este referencie.
5. Revisar `git status --short`. Todo cambio previo se considera propiedad del usuario hasta demostrar lo contrario.
6. Identificar microfrontend, servicio, schema, contrato, permisos y agentes especialistas afectados.
7. Registrar `Agentes consultados`; para Local→QA usar Arquitectura, Seguridad y QA/Release como minimo.
8. Confirmar ambiente y `tenant_id` antes de cualquier escritura.
9. Definir criterios de aceptacion y blast radius antes de implementar.

## Cierre obligatorio

Antes de declarar terminado un cambio:

1. aplicar la matriz de `gobierno_documentacion_viva.md` y actualizar OpenAPI, consumidores, pruebas, documentacion y agentes cuando aplique;
2. ejecutar `npm.cmd run validate:documentation` y `npm.cmd run verify`;
3. actualizar `ESTADO_ACTUAL.md` y `PENDIENTES.md` si el estado real cambio;
4. registrar el corte en `TRAZABILIDAD.md`;
5. indicar expresamente si hubo migraciones, seeds, despliegues o escrituras externas.
6. si se modificaron errores, warnings, estados o copy operativo, ejecutar `npm.cmd run validate:error-feedback` y confirmar paridad ES/EN, severidad y restauracion del estado rechazado.

La conversacion es contexto temporal. Estos archivos son la memoria persistente del proyecto.


## Reanudación CHG-265

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.

Preservar CHG-262/263/264 y CHG-265 sin commit. Consultar el informe para pruebas, migraciones y APIs. No promover a QA por inferencia.

Validación CHG-265: 257 backend sin DB (51 omitidas), 19 PostgreSQL seleccionadas, 40 navegador; smokes HTTP y migración reversible vacía aprobados. Consulta informe para alcance y pendientes.


## Ajustes UAT Local CHG-266

Continuar con los ajustes UAT de Proveedores, Requisiciones, Órdenes y Cotizaciones. El Owner Local ya dispone de emitir/aprobar/vencer/cancelar cotizaciones. Recargar frontend y sesión para verlos. Preservar todos los cambios CHG-262–265. Pendiente aceptación manual del usuario antes de cualquier preparación/promoción QA.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Solicitudes compactas Local CHG-267

Preservar CHG-262–266 y la mejora de Movimientos CHG-267: desplegable cerrado al entrar, aviso de pendientes y conservación de apertura al actualizar. Sigue pendiente aceptación manual, sin autorización de promoción QA.

Evidencia y APIs: `docs/auditorias/almacen_solicitudes_desplegables_2026-09-08.md`.
