# Archivo histórico de ESTADO_ACTUAL.md · corte previo a CHG-311

> **Evidencia histórica, no instrucciones vigentes.** Conserva las notas acumuladas hasta CHG-310, archivadas el 2026-10-07. Las afirmaciones de estado, pendientes y autorizaciones corresponden a sus fechas y pueden estar sustituidas. Volver a la [fuente viva](../ESTADO_ACTUAL.md) antes de planear o ejecutar. El cuerpo original se conserva; únicamente los enlaces relativos se ajustan a esta ubicación.

# Estado actual de ERClave

## CHG-310 · Custodia y matriz contable documentadas · 2026-10-07

Se asigna el seguimiento al agente técnico contable existente y se amplía su skill. [CONTROL_CONTABLE.md](../CONTROL_CONTABLE.md) detalla capacidad, brecha, responsable y evidencia por submódulo. Revisión de código Local sobre HEAD 213f75c con cambios anteriores preservados; no hay cambio funcional, migración ni despliegue. Runtime continúa en CHG-308 y head Local documentado `20261007_0050`; decisión monetaria CHG-309 vigente. Las pruebas históricas no se atribuyen a este corte documental.


## CHG-309 · Contexto guardado para reinicio · 2026-10-07

Sólo documentación; runtime/migración sin cambios respecto a CHG-308. El usuario confirmó: «sí, en la moneda base de la Sociedad; esto aplica para todo». Regla transversal para costos y tarifas de toda la operación, incluidos materiales, máquinas y mano de obra. Cuando un documento use otra moneda, conservar original y convertido con tipo de cambio explícito. No reinterpretar ni convertir automáticamente historia sin moneda confirmada. Funciona con Accounting apagado. No volver a preguntar esta política; su aplicación completa sigue pendiente de implementación. Retomar desde INICIO_SESION.md.


## Actualización CHG-308 · 2026-10-07

Local `20261007_0050`: preparación backend de contexto Production y prueba durable de intento, scope de órdenes/comandos/colas/CSV. Fabricación dimensionada aún no habilitada. 231 pruebas focales aprobadas; verify 532 passed/152 skipped y smoke de API recargada aprobado. Decisión sobre moneda de tarifas resuelta posteriormente en CHG-309; la política de existencias CHG-307 sigue confirmada. Ver docs/arquitectura/cont_08_produccion_contexto.md.


## Actualización CHG-307 · 2026-10-05

Local `20261005_0049`: surtido dimensionado desde existencias y entrega con costo original en moneda de Sociedad y conversión explícita al pedido. Entradas manuales dimensionadas requieren costo; historia sin moneda confirmada bloqueada. APIs locales recargadas y smoke autenticado aprobado. Pruebas: 159 PostgreSQL/API, 203 browser y 2 pantalla principal aprobadas; verify 532 passed/149 skipped. No separación completa ni promoción QA. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


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

Verificación CHG-302: focal Local DB/API 42/42 sin omisiones, browser focal 28/28 y transversal 191/191; feedback final 16/16. npm run verify aprobado (527 backend/127 omitidas en gate general). Smoke real de lectura aprobado; sin escrituras HTTP de negocio. Manuales Markdown actualizados, Word pendiente conforme a REGISTRO.

## CHG-301 — Disponibilidad comercial por División (CONT-07 parcial)

[Recorrido Sales/Purchasing](../../arquitectura/cont_07_commercial_asignaciones.md) implementado Local: cliente/proveedor único con asociaciones por División y Sociedad derivada, estado, revisión, idempotencia y auditoría propias. Admin autoriza; sin dependencia de Costing ni activación de Accounting/analítica. Alembic `20260928_0044`, sin backfill/asociaciones permanentes; QA/Producción intactos.

CONT-07 tiene recorridos Inventory/Production/HR/Sales/Purchasing. Condiciones comerciales por alcance y su aplicación a documentos CONT-04/07/08 siguen pendientes; los maestros y documentos anteriores siguen por tenant. No es separación operativa completa. Próximo bloque: reglas comerciales por dueño/alcance y propagación documental; también faltan folios CONT-06 y mapeo real explícito. Evidencia en TRAZABILIDAD CHG-301; apartados inferiores describen su corte histórico.

Verificación CHG-301: npm run verify aprobado (515 backend/121 omitidas en gate general), focal PostgreSQL/API 24/24 sin omisiones, browser focal 12/12 y transversal 175/175. Smoke Local read-only aprobado. Manuales Markdown de Compras/Ventas actualizados; Word pendiente conforme al registro.

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

Verificación final: 421 backend aprobadas/97 omitidas sin DB; 24 focalizadas (3 PostgreSQL con rollback); 130 browser interceptadas. Admin Local recargado en 8000, Emulator real y smoke de sesión/política 200, ruta de configuración 404 ante referencia inexistente y 401 sin token. Sin fixtures permanentes. Captura móvil inspeccionada; no equivale a UAT.

CONT-04 queda parcial a nivel transversal: faltan configuraciones de cada dueño y consumo/snapshots en documentos. Impresiones aún corporativas; no declarar separación completa. Continuar CONT-05/06/07/08 con catálogo básico y obligación sólo por flujo confirmados. Ver TRAZABILIDAD para evidencia final; no hay promoción QA/Producción.


## CHG-296 — disponibilidad de capacidades y política confirmada

El usuario confirma catálogo básico desde Administración sin activar analítica/Accounting, y Centro de costos obligatorio sólo por flujo de imputación habilitado. [Matriz vigente](../../arquitectura/matriz_capacidades_organizacionales.md). Sesión agrega contrato versionado de capacidades en código, con planned apagado aun ante flags/grants; disponibilidad no concede permisos ni prueba configuración lista. El avance CONT-04 y su migración están descritos arriba; no hay seeds ni cambios QA/Producción. Catálogo y propagación siguen pendientes. No repetir la pregunta de obligatoriedad; estructura y asignación de datos existentes todavía pendientes.


## CHG-295 — plan de ejecución modular

Preparado el [plan por fases](../../arquitectura/plan_separacion_modular_y_contabilidad_opcional.md), solicitado por el usuario. Primero contrato de capacidades/obligatoriedad, después CONT-04/05/06/07/08 para separación operativa; eventos y Contabilidad opcional después. Incluye responsables, migración, activación/apagado/reactivación y pruebas con módulos parcialmente activos. No se implementan funciones ni se habilitan módulos en este corte; último runtime CHG-293. La asignación real de datos existentes sigue pendiente, sin impedir trabajo independiente. Próxima entrega: matriz de capacidades y condiciones por flujo antes de CONT-04.


## CHG-294 — Contabilidad opcional y fronteras de activación

Usuario solicita analizar módulos no siempre activos. [Criterio y recomendaciones](../../arquitectura/contabilidad_opcional_y_capacidades.md): organización/operación independientes de Accounting, catálogo básico de centros con dueño Costing y superficie Admin, analítica y contabilidad por activación propia. Skills accounting/module-boundaries y fichas actualizadas. Sin cambios de APIs, runtime, datos ni entitlements; CHG-293 sigue siendo el último corte funcional.

Antes de CONT-05/07/08 concretar autorización de la capacidad básica de centros y política de obligatoriedad cuando no se usan costos/contabilidad. No reinterpretar silenciosamente la obligación anterior ni bloquear operación con un módulo apagado. En futuros eventos/libros definir fecha de inicio, desactivación, jobs e historia sin replay automático. QA/Producción sin cambios.


## CHG-293 — CONT-03 y cobertura de agentes en Local

Sesión v2 con Sociedades/Divisiones/Emisores visibles, selección validada de División y editor de alcance por usuario. Vacío no fabrica Matriz; wildcard explícito conserva acceso total; revisión/idempotencia/auditoría protegen edición. Una membresía del tenant demo `ten_739ee59d765d5e14818674800d` convertida con hash revisado; segundo preview cero cambios. Sin nuevas tablas ni Alembic: Local conserva `20260925_0038`. No se crearon Sociedades/Divisiones ni datos operativos por inferencia.

Fichas contables reforzadas; nuevas skills `erclave-accounting` y `erclave-module-boundaries`; validador verifica pareja por módulo, incluido Mantenimiento. [Cobertura y riesgos](../../arquitectura/cobertura_agentes_modulos.md). Seeds/onboarding conservan alcance existente, con regresión PostgreSQL.

33 pruebas focalizadas aprobadas sin omisiones (incluidas 9 PostgreSQL con rollback), 126 browser aprobadas con APIs interceptadas. Gate final verify aprobado: 404 aprobadas/94 omitidas sin DB, validadores y compilación correctos. Smoke browser Local adicional aprobado con lectura real y captura móvil inspeccionada. No atribuir cobertura DB completa a esas omisiones ni UAT a las pruebas interceptadas.

Stack Local arrancado mediante script canónico: frontend 4173, siete APIs 8000/8002/8004/8006/8008/8010/8012, PostgreSQL 5434 y Firebase Emulator 9099/UI4000. Health de siete APIs y frontend 200. Login real del Emulator, sesión y lectura de alcance 200; selección `default` rechazada 403. Scope v2/revisión1 sobrevivió al seed. El primer intento en sandbox falló por EPERM de Firebase; el arranque elevado posterior fue exitoso. Sin credenciales en evidencia.

La separación de documentos todavía requiere CONT-04/05/07/08. Estructura y asignación de datos existentes solicitadas al usuario, pendientes; no bloquear desarrollo independiente por esa respuesta. Accounting sigue planned. QA/Producción sin conexión, migración ni despliegue en este corte; último QA documentado `e57237f/20260913_0036`, no reconfirmado hoy. [Contrato, APIs y límites](../../arquitectura/cont_03_sesion_alcances.md).

## CHG-292 — CONT-02 implementado en Local

Administración → Organización ya administra Emisores, Sociedades y Divisiones mediante 18 operaciones normalizadas con doce permisos. Cada Sociedad exige un único Emisor y moneda base activa, inicialmente MXN; cada División exige Sociedad. Códigos administrados/manuales, búsqueda acotada, estados, auditoría, idempotencia, referencias por tenant y feedback ES/EN implementados. Las tablas son autoridad después del switch revisado; el JSON queda como proyección compatible y los adaptadores heredados están deprecados.

Alembic Local `20260925_0038` aplicada en `127.0.0.1:5434/erclave_local`. Autoridad activada en el único tenant de prueba autorizado `ten_739ee59d765d5e14818674800d`, con origen vacío, sin fabricar registros de negocio. Doce permisos nuevos sincronizados y concedidos al Owner de ese tenant. Admin local reiniciado con Firebase Emulator demo-erclave. Frontend `http://127.0.0.1:4173`. El resto de servicios conserva el arranque anterior.

Validación focalizada y gates de cierre: ver [CONT-02](../../arquitectura/cont_02_administracion_organizacional.md) y CHG-292 en TRAZABILIDAD. La comprobación con Owner y API/emulador locales confirmó cuatro lecturas organizacionales HTTP 200, tres formularios, validación requerida y contenedor móvil; cero escrituras de negocio y cero errores JavaScript. El SDK de Firebase se adapta en la prueba para usar REST real del emulador. No equivale a aceptación QA ni a un SHA publicado: workspace sobre `213f75c` con cambios sin commit.

Siguiente corte: CONT-03, sesión y alcance por Sociedad/División. Centros de costos siguen en CONT-05; Accounting, libros y afectaciones multimoneda permanecen pendientes. No se consultó ni modificó QA/Producción en CHG-292. Las secciones siguientes conservan el estado de su fecha; la autoridad JSON descrita en CHG-289 ya fue sustituida en Local por este corte.

## CHG-291 — Local aislado levantado; solicitud QA corregida

El usuario aclaró que quería levantar Local, sustituyendo la solicitud QA anterior. Se ejecutó `backend/scripts/start_local.ps1` desde el workspace original, conservando todos sus cambios. Frontend `http://127.0.0.1:4173`; Admin/Production/Inventory/HR/Sales/Purchasing/Maintenance en 8000/8002/8004/8006/8008/8010/8012; Firebase Auth Emulator demo-erclave en 9099 y UI en 4000. PostgreSQL Local existente: 127.0.0.1:5434/erclave_local, Alembic `20260922_0037`.

Antes del arranque se comprobó que la base sólo contenía el tenant autorizado `ten_739ee59d765d5e14818674800d`. El script sincronizó 171 permisos y configuró ese demo con ocho módulos. Se creó la identidad del emulador y se validó login/contexto HTTP 200; sin token, 401. Las siete APIs respondieron 200 a health/ready/version y health declaró ambiente local; frontend y UI del emulador respondieron 200. Versión runtime 0.1.0, no un SHA certificado del working tree. No se ejecutó migración ni backfill nuevos.

La política de PowerShell requirió ejecutar el script con ExecutionPolicy Bypass limitado al proceso; no se cambió la política persistente. No hubo conexiones, cambios ni publicación QA en este arranque. El candidato 2a91d19 sigue sólo Local como preparación histórica, sin publicación pendiente autorizada. CONT-01 sigue siendo estructura de datos; nuevas pantallas y Accounting pendientes.

## CHG-290 — candidato CONT-01 preparado; QA aún no promovido

Commit local certificado: `2a91d196175f589745f0e8831a053138f7475efa` (27 archivos, worktree aislado limpio), sin publicación ni PR. Reanudar desde ese candidato, no desde el árbol completo.

Se creó la rama aislada agent/chg290-cont01-qa en .local/qa-cont01 desde main e57237f. Incluye sólo CONT-00/01, documentación y ajustes mínimos de validadores; el working tree original conserva sus cambios. Verify de esa rama: 344 aprobadas/67 omitidas; 51 focalizadas/cero omitidas (9 PostgreSQL), estado Local intacto tras fixtures. Hosting QA 200; siete APIs 503 y posteriormente 500 el 2026-09-23, SHA actual no confirmado. Sin escrituras QA. El pipeline exige configuración global/tenant además de migración; alcance y siguientes autorizaciones en [release CONT-01](../../operaciones/release_qa_20260923_cont01.md).

## CHG-289 — CONT-00 resuelto y CONT-01 implementado sólo Local

El usuario confirmó Emisor 1:N Sociedad, exactamente un Emisor por Sociedad, libros por Sociedad, Centro de costos obligatorio por División con alta en Administración, selección según División activa y moneda base configurable inicialmente MXN con transacciones en otra moneda/tipo de cambio. Sustituye las propuestas anteriores de libro por Emisor y asociación muchos-a-muchos. No quedan pendientes las tres preguntas de CONT-00.

CONT-01 agrega modelos y revisión Alembic `20260922_0037`, aplicada en PostgreSQL Local `127.0.0.1:5434/erclave_local`, además de importación compatible con equivalencias, snapshots, auditoría, hashes revisados y locks por tenant. `organization.profile` y las APIs actuales conservan autoridad; UI/scopes, Centros de costos y Accounting siguen pendientes en CONT-02…18. Detalle: [CONT-01](../../arquitectura/cont_01_estructura_organizacional.md).

El tenant permitido `ten_739ee59d765d5e14818674800d` tenía cero razones sociales/sucursales. Su perfil quedó intacto y el preview reportó cero registros, sin backfill artificial. Pruebas focalizadas: 51 aprobadas/cero omitidas (30 nuevas, incluidas 9 PostgreSQL, y 21 del preflight previo); fixtures sólo del tenant permitido, revertidos al terminar. Se probaron upgrade/downgrade/re-upgrade, cardinalidad, pertenencia, idempotencia, concurrencia, moneda de catálogo y fallos parciales. `npm.cmd run verify` aprobado: todos los validadores, compilación y 355 backend aprobadas/67 omitidas en la corrida sin DB. De esas 67, las 9 nuevas sí se ejecutaron en la corrida focalizada; las 58 previas no se reejecutaron contra PostgreSQL. Documentación/trazabilidad y `git diff --check` aprobados.

Se inició únicamente PostgreSQL Local existente. Sin APIs/Firebase levantados, seeds, cambios QA/Producción ni despliegues. QA documentado continúa `e57237f/20260913_0036`, sin consulta nueva. Las notas CHG-286 a CHG-288 que describen preguntas abiertas son antecedentes superados por la respuesta registrada aquí.

## CHG-288 — inicio de CONT-00 y preflight organizacional Local

El usuario solicitó aplicar el plan CHG-287. Se preparó el [registro concreto de decisiones y ejemplos](../../arquitectura/cont_00_decisiones_y_preflight.md) y un analizador offline de exportaciones originales de `organization.profile`. Detecta formato inválido, IDs repetidos, referencias huérfanas/ambiguas, discrepancias de tenant y datos que requieren resolución; no normaliza ni modifica el origen. Su reporte no certifica la base ni autoriza migración.

CONT-00 sigue abierto: las preguntas funcionales de estructura Sociedad–Emisor/libro, Centro de costos y moneda/tipo de cambio/redondeo aún no tienen respuesta registrada. CONT-01 tiene especificación preparatoria, sin modelos nuevos ni migración. CONT-02 a CONT-18 siguen pendientes. La cabeza Alembic del repositorio permanece `20260913_0036`; QA documentado continúa `e57237f/0036`, sin verificación remota nueva.

Validación focalizada: 21 pruebas offline aprobadas. `npm.cmd run verify` aprobado: todos los validadores, compilación y 334 pruebas backend aprobadas/58 omitidas sin PostgreSQL. Node 24.19.0/npm 11.17.0 se localizaron fuera del PATH en `AppData/Local/Programs/nodejs`; se usó el Python de `backend/.venv`. `session:context` y `git diff --check` aprobados. Sin stack operativo levantado, conexiones DB, fixtures persistidos, seeds, escrituras QA/Producción ni despliegues. Los 107 cambios locales previos se preservan.

## CHG-287 — plan de trabajo contable por cortes verticales

El análisis CHG-286 se convirtió en un plan de 19 cortes `CONT-00` a `CONT-18`, agrupados en siete hitos: decisiones, organización, costos/dimensiones, eventos, núcleo contable, fiscal/tesorería y escalamiento. Cada corte define persistencia, contratos, formularios, permisos, migración, pruebas y criterio de salida. La estrategia obligatoria para datos es expandir, migrar, exigir y retirar compatibilidad.

El primer bloque no crea asientos: cierra Sociedad–Emisor/libro, normaliza Sociedad/División/Emisor, migra el JSON actual, actualiza sesión/scopes y establece configuración por División. El plan no cambia runtime ni declara Contabilidad implementada. Documento: [plan de trabajo](../../arquitectura/plan_preparacion_contabilidad.md).

## CHG-286 — análisis de preparación para Contabilidad

Se analizó el cambio de estructura hacia Corporativo → Sociedad → División → Centro de costos, con Emisor fiscal asociable a Sociedades. La conclusión es que el sistema todavía no persiste Sociedad, División, Centro de costos o Emisor en los documentos operativos: el alcance actual de sucursal existe en la sesión, mientras razones sociales y sucursales viven dentro del JSON `organization.profile`.

La propuesta conserva `tenant` como Corporativo y frontera de seguridad, normaliza Sociedad/División/Emisor en Administración, mantiene Centro de costos bajo Costing y hace que Accounting consuma eventos económicos inmutables. Antes de implementar debe confirmarse si Sociedad es unidad de gestión y Emisor la identidad fiscal, y si el libro pertenece al Emisor o a la combinación Sociedad–Emisor.

La auditoría también confirmó dos huecos de códigos: `hr.position` tiene secuencia pero Puesto no guarda código; `inventory.movement` tiene secuencia pero el backend genera `MOV-*` aleatorio. Compras y Mantenimiento capturan manualmente varios folios sin secuencia central. No hubo cambios de runtime, API, datos, ambientes ni QA. Detalle: [análisis de impacto](../../auditorias/impacto_preparacion_contabilidad_2026-09-21.md).

## CHG-285 — referencias históricas seguras en Ventas Local

La revisión transversal de selectores confirmó una corrección necesaria en Clientes y Cotizaciones: un código histórico de moneda o condición de pago ausente del catálogo activo podía dejar seleccionada visualmente la primera opción vigente. Ahora el formulario muestra el código histórico como no vigente, lo omite del PATCH mientras no se reemplace y exige una opción activa en altas nuevas. Proveedores reutiliza el mismo tratamiento.

No se encontraron cambios equivalentes necesarios en Administración, Inventarios, RH, Mantenimiento o los selectores cerrados de Producción. Tipos, estados, prioridades y políticas coinciden con enums del backend. Los catálogos fiscales completos se difieren hasta factura/XML, CFDI y cuentas por pagar, todavía `planned`. Evidencia: [auditoría transversal](../../auditorias/catalogos_selectores_transversales_2026-09-20.md).

Validación CHG-285: gate completo aprobado con todos los validadores, compilación y `313 passed, 58 skipped` sin PostgreSQL. Se agregó un caso Playwright para Cliente y Cotización con referencias históricas, pendiente de ejecución cuando el stack Local aislado esté activo. No hubo migración, datos ni cambios en QA/Producción.

## CHG-284 — Proveedores usan catálogos comerciales de Administración en Local

El alta y la edición de proveedores ya consumen monedas y condiciones de pago activas mediante la nueva lectura `GET /v1/purchasing/reference-data`. Purchasing consulta a Administración como autoridad y expone sólo `code`, `name_es` y `name_en`; el frontend conserva valores históricos en edición, elige predeterminados sólo si siguen activos y bloquea la captura con mensaje accionable cuando faltan referencias. La lista de Compras permanece utilizable si falla únicamente esta dependencia.

Administración ahora admite permisos consumidores de proveedor y orden de Compras en los GET de catálogos comerciales. No hay migración ni cambio de payload de proveedor. Contrato Purchasing Local `1.5.0`; QA permanece en `e57237f/0036` y no fue consultado ni modificado.

Validación enfocada: Purchasing API `8 passed`; Admin API `85 passed`; contratos OpenAPI, sintaxis y validador de ciclo de Compras aprobados. Gate completo: todos los validadores, compilación y `313 passed, 58 skipped` sin PostgreSQL. El caso Playwright de catálogos dinámicos quedó agregado, pero su ejecución no inició porque el preflight detectó el stack Local apagado; esto no se registra como resultado del caso.

## CHG-283 — skills de coherencia, contexto y evidencia Local

Se incorporaron `erclave-form-contract`, `erclave-context-reconcile` y `erclave-qa-evidence` para justificar campos, contrastar formularios con contratos/catálogos, resumir el estado del árbol y registrar resultados funcionales sin inferencias. `python tools/context_brief.py` produce un resumen documental de solo lectura y declara que no verifica QA remoto. AGENTS, AGENTES, la skill de funcionalidades, el validador de tooling y el gobierno documental enlazan el nuevo flujo. No cambia runtime, API, datos ni QA.

Verificación CHG-283: tres skills válidas con `quick_validate`, script ejecutado en texto/JSON y gate `tools/verify.js` aprobado mediante el runtime JavaScript de VS Code: todos los validadores, compilación y 310 pruebas backend aprobadas; 58 integraciones omitidas sin PostgreSQL. No se ejecutó `verify:postgres` ni una prueba de navegador en este corte de proceso.

El [piloto de Producto/Servicio y Proveedor](../../auditorias/piloto_contrato_formularios_2026-09-20.md) es una auditoría de código: identifica diferencias de obligatoriedad y cobertura de catálogos, sin declarar defectos reproducidos en navegador. La elección de campos de Producción requiere decisión funcional; el selector de Proveedor necesita un corte posterior con pruebas para usar los catálogos activos de Administración. CHG-280/281/282 y sus pendientes conservan su estado anterior.

## CHG-282 — decisión de cierre para CHG-281 y manuales

Revisión del 20 de septiembre de 2026: CHG-281 conserva su validación Local y aún no tiene un candidato inmutable ni despliegue QA. Se pospone su promoción hasta completar la prueba autenticada de evidencia y avance de OP-000003 y registrar la aceptación o incidencia correspondiente. El release QA vigente sigue siendo `e57237f` con Alembic `20260913_0036`; no se ejecutaron gates, migraciones ni escrituras remotas en esta revisión.

La edición documental CHG-280/281 está preparada en Markdown y DOCX locales. La revisión visual de los ocho Word sigue pendiente: el renderizador carece de dependencias en esta sesión, Word no pudo abrirse mediante automatización y al menos un DOCX estaba bloqueado por otro proceso. No se certifican ni distribuyen como versión visualmente aprobada. La publicación de la actualización documental continúa pendiente.

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

Verify CHG-275 aprobado:292 backend,58 skips sin DB y validadores completos. Word regenerado/verificado estructuralmente; revisión visual pendiente de renderizador, no distribuir como final.

Selección segura:29 aprobadas sin skips (23 DB históricas,3 schemas históricos,3 DB nuevas). De las55 históricas antes omitidas se verificaron26 y quedan29 bloqueadas por fixtures de otros tenants/limpieza amplia. No lanzar verify:postgres completo. Detalle, rollback, matriz API y gates en `docs/operaciones/release_qa_20260914.md`. Sin publicación de rama/PR, migración o deploy QA.


## Evidencia de servicios CHG-274 — solo Local

Validación CHG-274:185 browser aprobadas;19 focalizadas (14 archivo/optimización,3 API y2 PostgreSQL), verify292 aprobadas/58 omitidas en corrida sin DB. Las2 integraciones nuevas sí se ejecutaron por separado, al igual que la de margen del corte anterior;55 generales siguen pendientes. Reversa y expiración reales en fixtures, permisos y tamaños comprobados; revisión visual390/760/1280 y tema oscuro.

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.


## Margen esperado sin tope CHG-273

Validación CHG-273:14 pruebas focalizadas aprobadas, incluida PostgreSQL real;23 browser de contratos y98 feedback aprobadas; verify275 backend aprobado. En la corrida genérica se omiten56 integraciones;1 (margen) se ejecutó aparte contra DB real,55 generales previas siguen pendientes. API Local8002 reiniciada y esquema servido sin máximo100 comprobado.

CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.


## Feedback de formularios solo Local CHG-272

CHG-272 incorpora errores vinculados a controles, resumen accesible, foco y conservacion de captura en el frontend compartido y Backoffice. Registra 54 variantes de formulario y aliases/partidas; catalogo de 244 codigos ES/EN y 95 reglas schema. La skill `erclave-form-feedback` queda obligatoria para ajustes presentes y futuros. Wiring no equivale a cobertura exhaustiva del negocio.

Evidencia final: 174 pruebas browser aprobadas sin duplicados (98 offline, incluidos 14 Backoffice; 22 MAIN sobre once formularios reales ES/EN; 54 de regresion general). Offline se ejecuto en grupos complementarios 94 + 4, ambos exit 0. `npm run verify` y validate aprobados (262 backend, 55 omitidas sin DB; sintaxis 79). Skill valida, diff limpio y revision visual claro/oscuro 390 px y CSS zoom2 aprobada; esta ultima no equivale a zoom real del navegador. Detalle reproducible y APIs: `docs/auditorias/formularios_feedback_2026-09-13.md`.

No cambia backend, contratos, DB, permisos ni datos operativos; sin deploy. QA permanece en CHG-270 `b63cdad`; la edición documental CHG-275 agrega las mejoras Local y conserva la distinción de ambiente. UAT y causa exacta del incidente original pendientes.

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


## Confirmaciones operativas Local CHG-265

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.

Cabeza Alembic Local `20260908_0034`; QA head `20260825_0029`, sin cambios remotos. Migraciones 0032–0034 aplicadas en PostgreSQL loopback `erclave_local`. Verificación Local: 257 pruebas backend (51 omitidas sin DB), 19 integraciones PostgreSQL seleccionadas y 40 pruebas browser aprobadas. Dos smokes HTTP reales y downgrade vacío/upgrade 0034 aprobados; seis APIs Local reiniciadas. Pruebas y limitaciones en el informe CHG-265. Las secciones siguientes conservan evidencia de cortes anteriores.

## Materiales por Almacen antes de iniciar CHG-264

CHG-264 implementa solo en Local la salida completa de materiales desde Movimientos antes de iniciar `in_progress`. Liberar conserva reservas; Almacen confirma entrega con `inventory.movement.create`; Produccion valida cantidades/costos confirmados al iniciar y no consume al iniciar/reanudar. Aplica a productos y servicios con receta, sin agregar materiales a las ordenes comerciales de servicio de Sales. Detalle y matriz API: `docs/auditorias/materiales_produccion_movimientos_2026-09-08.md`.

Cabeza Alembic Local `20260908_0031`; QA conserva `20260825_0029` y el release a119ddf. Migracion Local aplicada, reversa vacia y nueva aplicacion verificadas. APIs Production/Inventory reiniciadas en loopback. Verificacion aprobada: verify:local con 33 pruebas de navegador y suite backend, ampliada y repetida con verify:postgres a 297 pruebas sin omisiones. Smoke HTTP real aprobado (bloqueo, entrega, repeticion, inicio, costo y salidas unicas); no desplegado a QA/Produccion. Se preservan CHG-262 y CHG-263.

## Refacciones desde Movimientos Local CHG-263

- Implementacion Local de bandeja paginada, confirmacion completa de entrega, rechazo con motivo y reintento de partidas pendientes por Almacen. Resolver Mantenimiento ya no genera salidas.
- Contratos Maintenance e Inventory actualizados; permisos existentes, schemas y cabeza Alembic `20260901_0030` conservados. Detalle: `docs/auditorias/refacciones_movimientos_2026-09-07.md`.
- `npm.cmd run verify:local` aprobado: 290 pruebas backend PostgreSQL sin omisiones y 30 de navegador; contratos, validadores, sintaxis y compilacion aprobados. Smoke HTTP real aprobado con reserva, entrega por Almacen, reintento sin duplicado y cierre. Compras/Mantenimiento ya entran a la coleccion general de pytest.
- Se preservan los cambios previos CHG-262. Se reiniciaron solo Inventory y Maintenance Local; fixtures sinteticas del tenant autorizado limpiadas por sus propios IDs. Sin migraciones, seeds, escrituras remotas, commit, push, PR ni promocion QA/Produccion.

> Reanudacion vigente: consultar `docs/contexto/REANUDACION_CHG261.md`. El handoff CHG-255 se conserva solo como evidencia historica del corte previo.

## Auditoria frontend/backend Local CHG-262

- Se corrigieron 17 grupos de desajustes de formularios, campos no persistidos, valores iniciales, ramas condicionales y permisos. Detalle y matriz de APIs: `docs/auditorias/frontend_backend_2026-09-07.md`.
- Produccion, Inventory, RH, Compras, Ventas y Mantenimiento conservan contratos y schemas. Administracion carga consultas por permiso; Backoffice fue recorrido en lectura.
- Evidencia integral: npm.cmd run verify:local aprobado; 245 pruebas backend PostgreSQL sin omisiones y 25 pruebas de navegador aprobadas, incluidos Backoffice y ES/EN en contenedor estrecho. Validadores, contratos, sintaxis y compilacion aprobados.
- Cambios sin commit en el working tree sobre `735312b`. No hubo migraciones, seeds, cargas operativas, escrituras QA/Produccion, despliegue, push ni PR.

## Release QA CHG-254

- El workflow gobernado promovio a QA el SHA inmutable `a119ddf5e8d42376b8557b234e15e3681b19c2a7` con Admin, Produccion, Inventory, RH, Ventas, Compras y Mantenimiento.
- Cloud SQL QA avanzo de `20260821_0023` a `20260825_0029`; la reconciliacion estructural habilito el catalogo real de siete modulos para el tenant `ten_739ee59d765d5e14818674800d`. No se ejecutaron seeds ni se copiaron datos funcionales Local.
- Las identidades runtime de Compras y Mantenimiento usan minimo privilegio, sin llaves administradas por usuario. El primer intento de servicios se detuvo por falta de `iam.serviceAccounts.actAs`; se concedio `roles/iam.serviceAccountUser` al deployer solo sobre las dos identidades nuevas y el reintento concluyo correctamente.
- La verificacion externa aprobo `/health`, `/ready` y `/version` en los siete servicios: todos reportan ambiente `qa`, base configurada y el mismo SHA. `https://erclave.web.app` responde `HTTP 200` y publica las siete URL sanitizadas.
- El candidato fue construido en la ejecucion `33470879111` y promovido en `33473077996`, con aprobaciones independientes para base/configuracion, servicios, trafico y frontend. La evidencia completa esta en `docs/operaciones/resultado_release_qa_20260901.md`.
- UAT funcional queda en curso con el equipo de pruebas; sus observaciones no se consideran defectos confirmados hasta reproducirlas y clasificarlas.

Ultima actualizacion: 2026-09-07.

- CHG-261 deja `docs/contexto/REANUDACION_CHG261.md` como handoff vigente posterior al reinicio, con Git consolidado hasta CHG-260, limites Local/QA, evidencia de validacion y pasos exactos para levantar y verificar el entorno.

## Ambiente local

- El arranque canonico Local aislado opera mediante `backend/scripts/start_local.ps1`: PostgreSQL `erclave_local`, Firebase Auth Emulator `demo-erclave`, frontend y APIs locales.
- Una ejecucion local conectada a cualquier recurso QA debe identificarse como `local conectado a QA` y requiere autorizacion explicita.

- Frontend estatico local esperado en `http://127.0.0.1:4173`.
- CHG-258 presenta la pestana principal como `ERClave` y retira la etiqueta obsoleta `Propuesta Frontend`; Backoffice conserva su titulo propio.
- Admin API local esperada en `http://127.0.0.1:8000` contra PostgreSQL local. La conexion local a QA usada en una validacion autorizada anterior es evidencia historica, no el modo local canonico.
- Production API local esperada en `http://127.0.0.1:8002`.
- Inventory API local esperada en `http://127.0.0.1:8004`.
- HR API local esperada en `http://127.0.0.1:8006`.
- Sales API local esperada en `http://127.0.0.1:8008`; cubre Clientes, Cotizaciones, Pedidos, surtido y Entregas. El mismo servicio esta desplegado en QA dentro del release de siete servicios.
- Purchasing API Local esperada en `http://127.0.0.1:8010`; cubre Proveedores, Requisiciones, Ordenes y Recepciones. El mismo servicio esta desplegado en QA; Produccion permanece fuera de alcance.
- Maintenance API Local esperada en `http://127.0.0.1:8012`; cubre ordenes correctivas, tiempos y solicitudes de refacciones. El mismo servicio esta desplegado en QA; Produccion permanece fuera de alcance.
- PostgreSQL portatil aislado para Inventory escucha en `127.0.0.1:5434`, base `erclave_local`.
- Firebase Auth Emulator escucha en `127.0.0.1:9099` y su UI en `127.0.0.1:4000`; el usuario local `admin.qa@erclave.local` resuelve el tenant demo sin consumir Firebase QA.
- Firebase autentica; `admin-service /v1/session/context` resuelve tenant, membresia, modulos, permisos y alcance.

### Estabilizacion Local CHG-259

- El working tree previo quedo consolidado en el commit local `8dcff6b`; no se publico ni promovio a otro ambiente.
- `npm run verify:postgres` exige `127.0.0.1:5434/erclave_local`, ejecuta toda la suite backend y falla si pytest omite una prueba. `npm run verify:local` agrega la regresion E2E de navegador contra el stack Local completo.
- Playwright cubre autenticacion con Firebase Emulator, resolucion del tenant demo, navegacion de los seis modulos operativos y todos sus submodulos, las 28 tarjetas de reportes y el bloqueo de solicitudes remotas.
- Inventory demuestra bajo PostgreSQL que dos reservas concurrentes no sobrevenden y que dos confirmaciones de consumo producen un solo movimiento. Sales, Purchasing y Maintenance conservan sus pruebas de claims, locks y reconciliacion.
- Compras marca como `failed` toda partida sin respuesta de Inventory, incluso cuando la dependencia devuelve menos resultados que el plan; la conciliacion posterior conserva las partidas ya completadas.
- El frontend inicio la extraccion incremental de `app.js`: estado inicial, feedback de errores y paginacion viven en modulos propios. Los mensajes visibles ya no leen `error.message` directamente.
- Los listados renderizados con mas de 25 elementos muestran paginacion accesible Anterior/Siguiente. La paginacion contractual server-side para catalogos que puedan superar el limite preventivo sigue pendiente antes de volumen productivo.

## Cortes funcionales relevantes

### Reportes estandar por modulo

- CHG-256 implementa solo en Local 28 exportaciones CSV de portada: 5 de Produccion, 5 de Almacenes, 4 de RH, 6 de Ventas, 4 de Compras y 4 de Mantenimiento.
- CHG-257 simplifica la interfaz de esos 28 reportes: tarjetas, modal y confirmacion dicen solo **Generar** o **Reporte generado**, sin presentar el formato tecnico. Los catalogos cerrados son buscables por texto y conservan valores validos por reporte; fechas, busqueda libre y categoria mantienen controles apropiados.
- Cada tarjeta operativa abre un modal bilingue con filtros minimos de periodo, estatus, prioridad, tipo, condicion o busqueda segun aplique. Un resultado sin filas se informa sin descargar archivo.
- Los seis servicios propietarios exponen `GET /v1/{modulo}/reports/{report_code}/export`; cada codigo es fijo, tenant-safe y exige el permiso de lectura existente del recurso. No se agregaron permisos ni lecturas cruzadas entre schemas.
- El CSV usa UTF-8 con BOM, encabezados ES/EN, fechas ISO, numeros crudos, proteccion contra formulas y limite de 50 000 filas. Los reportes de RH, clientes y proveedores minimizan PII y datos fiscales/contacto.
- Administracion conserva su centro de configuracion. El modulo Reportes sigue planeado para XLSX con formato, PDF, cruces entre modulos, tableros, vistas guardadas y distribucion.

### Feedback operativo

- CHG-251 normaliza en Local los errores de API y Firebase mediante un catálogo común ES/EN gobernado por `error.code`; `message` se conserva sólo como diagnóstico y ya no se presenta directamente.
- Las transiciones sensibles de Producción, Ventas, Compras y Mantenimiento distinguen éxito, warning y error; si una mutación falla, el selector o proyección vuelve al estado confirmado. Los errores inesperados pueden mostrar `correlation_id` como referencia de soporte.
- Formularios, toasts y errores de carga declaran semántica ARIA, permanecen visibles según severidad y escapan contenido antes de insertarlo en HTML. `validate:error-feedback` protege estas reglas.

### Compras

- CHG-229 implementa en Local el primer corte supplier-to-receipt mediante `purchasing-service` en `http://127.0.0.1:8010` y schema aislado `purchasing`.
- CHG-230 agrega perfil fiscal editable al maestro de proveedores. Las altas nuevas exigen razon social, RFC, regimen, correo de facturacion y codigo postal fiscal; RFC es unico por tenant y los registros heredados pueden completarse gradualmente.
- CHG-231 habilita en la UI Local requisiciones con multiples partidas buscables. Backend rechaza articulos repetidos en el mismo documento y la conversion a Orden solicita un precio independiente por partida.
- Compras es dueno de proveedores, requisiciones, ordenes, recepciones comerciales, idempotencia y auditoria. Inventory conserva la autoridad exclusiva de articulos, almacenes, movimientos, saldos y Kardex.
- La requisicion transita de borrador a enviada y aprobada/rechazada; una orden solo consume requisicion aprobada o exige motivo de compra directa. Emitir congela la orden para recibir.
- La recepcion rechaza duplicados y sobre-recepcion, admite parcialidad y solicita entradas idempotentes a Inventory. Si la autoridad fisica falla, conserva `needs_reconciliation` visible sin fingir una recepcion completada.
- CHG-232 cierra el flujo source-to-receipt: edita borradores, exige coincidencia exacta requisicion/orden, cancela con motivo, recibe varias partidas, reserva saldo concurrentemente y permite conciliar solo lineas fallidas con claves estables. Inventory expone lectura puntual tenant-safe de almacen para validar la recepcion.
- El catalogo Admin y manifiesto marcan `purchasing` como implementado, con dependencia obligatoria de `inventory`. La UI ofrece flujo bilingue real; reabastecimiento automatico, factura, CxP, pago, devolucion y asiento permanecen planeados.
- CHG-248 incorpora en los cinco submodulos el riel de ayuda transversal bilingue; resume cada recorrido sin alterar permisos, estados ni contratos.
- CHG-250 reemplaza los `prompt()` nativos de cancelacion por un modal ERClave bilingue que exige motivo, conserva los comandos y permisos puntuales existentes y presenta errores dentro del flujo.

### Mantenimiento

- CHG-252 corrige en Local la continuidad de carga del frontend: al terminar las consultas autoritativas, Mantenimiento vuelve a renderizar y deja el estado `Cargando Mantenimiento`; un guardrail evita reintroducir el bloqueo.
- CHG-234 implementa Mantenimiento correctivo en Local: API `8012`, schema `maintenance`, ordenes manuales o ligadas a maquina/Produccion, responsable RH elegible, tiempos y solicitudes multi-linea al almacen de refacciones.
- Solicitar una orden bloquea la maquina y pausa una orden productiva `in_progress`; resolver consume reservas y libera la maquina sin reanudar Produccion. Backoffice ya permite activar el modulo y el tenant demo Local lo tiene activo.
- CHG-235 endurece el flujo en Local con revision `20260824_0028`: conciliacion manual durable, compensacion de reservas al cancelar, rebloqueo al reabrir, revalidacion RH al iniciar, asignacion primaria unica e indices de consulta por orden.
- RH e Inventory son dependencias obligatorias. Production es integracion opcional y sigue siendo autoridad de maquinas y ordenes productivas.
- La UI tolera fallos de catalogos sin perder la lectura de ordenes, respeta permisos de mutacion y distingue exito de `needs_reconciliation`. Este corte esta desplegado en QA; Produccion permanece sin cambios.
- CHG-248 agrega el riel de ayuda transversal bilingue a Ordenes y Refacciones, conservando la regla de no reanudar Produccion automaticamente y la autoridad de Inventory sobre reservas y movimientos.

### Administracion y permisos

- CHG-236 implementa solo en Local autorizacion operativa granular: Produccion separa liberar, esperar recursos, iniciar, pausar, reanudar, enviar a validacion, finalizar y cancelar; cada resultado de etapa tiene permiso propio. Mantenimiento separa sus nueve transiciones y Almacenes separa leer de recibir producto terminado. Compras, Ventas y Recetas ya cumplian el patron y fueron auditados sin cambios de flujo.
- CHG-237 endurece ese corte solo en Local: la autorizacion exacta de Produccion ocurre antes de precondiciones sensibles; Almacenes consume una proyeccion minima de orden terminada en vez de lecturas generales; OpenAPI y runtime comparan tambien sus permisos; y el mapa maestro/manuales quedan sincronizados.
- El backend exige el permiso derivado de la accion solicitada aunque el usuario posea otra capacidad del mismo endpoint. El editor de Roles recibe los permisos desde OpenAPI y no depende de nombres fijos de puestos.

- En Local y QA, Administracion incluye catalogos tenant-safe de unidades, monedas y condiciones de pago. Cada tarjeta abre una vista dedicada; altas/ediciones son idempotentes, correlacionadas y auditadas. CHG-205 endurecio `document.template` con logo reemplazable/eliminable, colores, pie y numeracion compartidos por los PDF de Ventas y Produccion. La UI es bilingue y permission-aware; el backend verifica formato, Base64, firma binaria y limite decodificado de 1 MB del logo. Ambos generadores recuperan el registro API si falta en cache, informan fallos visibles y escapan el contenido operativo antes de insertarlo en el documento.
- Backoffice edita datos basicos del tenant y gobierna sus entitlements contractuales. El administrador del tenant solo cambia `tenant_enabled`; `session/context`, policy y permisos operativos exigen entitlement activo mas preferencia encendida. Los modulos planeados no pueden habilitarse y `admin` es obligatorio. Local esta en Alembic `20260901_0030`; QA permanece en `20260825_0029`.
- En Local y QA, Administracion ofrece el catalogo de folios por tipo documental. Prefijo, separador, siguiente numero, longitud y modo administrado/manual son editables por tenant; la asignacion de un consecutivo es atomica, idempotente y auditada. Los formularios actuales de Produccion, Almacenes, RH y Ventas consumen esa autoridad antes de crear el registro.
- Los contratos OpenAPI parsean como YAML y un validador compara operaciones `implemented` con las rutas FastAPI. Capacidades futuras se marcan `x-implementation-status: planned`.
- Los manifiestos de microfrontend distinguen `implemented`/`planned` y usan permisos puntuales con puntos; en los implementados, `permissions` es el inventario exhaustivo de operaciones OpenAPI implementadas del namespace propietario. El runtime visual actual permanece centralizado en `frontend/app.js` hasta una extraccion modular posterior.
- El editor de permisos de roles trabaja con borrador explicito, busqueda, filtros, agrupacion por modulo/recurso, seleccion masiva visible y resumen de cambios; no incluye plantillas ni presets.
- Los nombres tecnicos se conservan como identificadores de policy, pero la interfaz usa nombres y descripciones ES/EN mantenidos en `admin.permissions`.
- El catalogo remoto requiere tenant y `admin.role.read`; solo expone permisos `tenant` asignables y marca disponibilidad segun el entitlement del modulo.
- Modificar permisos exige `admin.role.permissions.manage`, `expected_revision` e `Idempotency-Key`. El backend aplica diferencias, conserva scopes heredados sin permitir crear nuevos scopes arbitrarios y audita altas/bajas.
- Los grants historicos internos pueden conservarse como relacion para no perder trazabilidad, pero ya no ingresan a `session/context` ni producen autorizacion efectiva. El owner conserva un piso administrativo y no puede inactivarse.
- El payload anterior `permission_ids + scope` permanece compatible y esta deprecado; la interfaz nueva usa `assignments + expected_revision`.
- Mientras un ambiente no tenga `admin.role.permissions.manage`, Roles permite abrir `Ver permisos` en modo de solo lectura y explica por que la edicion permanece bloqueada; no aplica fallback de escritura inseguro.
- La revision vigente de Cloud SQL QA es `20260913_0036`. Los siete servicios publicos reportan el SHA inmutable `b63cdad2fbac423c24460e55582ccfc0003e9924`; la promocion gobernada no copio datos funcionales Local.

### Produccion

- En Local y QA, las ordenes nuevas ya no aceptan responsables libres: exigen trabajadores activos validados por `hr-service`, tanto para responsable general como por etapa, y conservan ID externo mas nombre snapshot.
- CHG-260 corrige exclusivamente la interfaz Local de Productos y servicios: al elegir **Servicio**, el selector enriquecido de articulo de Inventario queda oculto, deshabilitado y sin validacion requerida; el alta envia `inventory_item_id: null`, conforme a la regla autoritativa ya vigente en `production-service`. Los productos fisicos conservan la vinculacion obligatoria.

- Productos y servicios se presentan como catalogo maestro antes de consultar ordenes relacionadas.
- En Local y QA, Productos/Servicios, Recetas/versiones, Maquinaria, Ordenes y etapas persisten mediante `production-service`; la UI recarga PostgreSQL y no degrada silenciosamente a `localStorage` cuando `apiMode=api`. La validacion autoritativa descrita a continuacion esta desplegada en ambos ambientes.
- La version vigente aprobada y el borrador/pendiente mas reciente se distinguen. Las ordenes siempre usan `current_version_id`, guardan snapshots de receta, recursos y costos autoritativos y conservan sus etapas aunque la receta cambie.
- El editor API de Recetas consume materiales activos con `use_in_recipe=true` desde Inventory y puestos productivos/areas activas desde HR. No carga seeds; las etapas nuevas conservan ID externo y nombre snapshot del area mediante la revision Local `20260805_0013`.
- El editor de Recetas separa materiales, mano de obra y maquinaria. Los materiales usan la unidad base de Almacenes; mano de obra y maquinaria se capturan como horas-persona y horas-maquina, con conversion transparente a minutos para el contrato vigente.
- Las horas-persona y horas-maquina aceptan cualquier fraccion decimal, sin saltos obligatorios de 15 minutos; la UI aclara que `0.5 h = 30 min`.
- El buscador de producto/servicio en Recetas presenta nombre y codigo comercial; los IDs tecnicos `prs_*` permanecen ocultos y se usan solo para la relacion interna.
- Las listas, selectores, mensajes y documentos de Recetas ocultan IDs `rec_*`; muestran nombre, codigo del producto y version mientras conservan el ID en relaciones y atributos internos.
- En Local y QA, la receta tiene folio de negocio propio, enumera sus fases y exige que sus pesos activos sumen 100%. La orden conserva ese snapshot y expone avance general ponderado. La seleccion de una version aprobada ya reconoce correctamente la version aprobada retornada por API aunque la proyeccion de cabecera no incluya `current_version_id`.
- El alta y edicion de Maquinaria consulta areas activas de `hr-service`; no permite capturar areas libres y dirige a Areas y puestos cuando el catalogo esta vacio.
- Las transiciones de orden y etapa se validan en backend, son idempotentes y auditadas. Una etapa terminal no vuelve a pendiente; completar todas las etapas lleva la orden a validacion y el cierre es explicito.
- En Local y QA, la validacion ya no acepta disponibilidad ni costos enviados por el navegador. Produccion consulta Inventarios y RH, descuenta reservas/capacidad comprometida por fecha, bloquea capacidad concurrentemente y crea reservas atomicas por almacen antes de liberar la orden.
- La primera entrada de una orden a `in_progress` consume sus reservas como salidas inmutables en los almacenes que las otorgaron y fija el costo real de materiales; reanudar o cerrar no duplica movimientos. En el corte vigente, cerrar exige todas las fases al 100%, pero no obliga a capturar minutos reales de mano de obra/maquinaria; esa medicion queda diferida hasta definir el modelo de eficiencia. `actual_cost` conserva el costo material consumido. Cancelar antes del inicio libera reservas; despues del inicio conserva las salidas fisicas y libera los compromisos de capacidad aplicables.
- Aprobar una receta revalida producto, materiales, unidades, puestos, areas y maquinaria existente no inactiva. Una maquina en mantenimiento puede definir el proceso, pero aporta cero capacidad y bloquea la orden hasta reactivarse. `area_ref_id` sigue recomendado para asignacion/reportes; nombres y costos son snapshots y no se infieren relaciones por texto.
- Areas y puestos pertenecen al modulo independiente Recursos Humanos, con microfrontend y `hr-service` propios.
- En Local y QA, RH administra expedientes minimos de trabajadores con un puesto vigente, identificadores CURP/RFC/NSS validados y datos complementarios opcionales. QA conserva la cabeza Alembic `20260825_0029` y Local esta en `20260901_0030`.
- El entitlement `hr` controla la disponibilidad por tenant; alta y edicion usan permisos separados `hr.area.*` y `hr.position.*`.
- El esquema `hr` incorpora aislamiento por tenant, FK compuesto area-puesto, idempotencia y auditoria. El 2026-07-31 se creo vacio en QA; posteriormente CHG-182 desplego `hr-service` y activo el entitlement estructural sin cargar areas ni puestos.
- El corte estructural CHG-182 dejo seis permisos `hr.*` activos y los permisos `production.labor.*` heredados inactivos. Los catalogos partieron vacios; su contenido actual depende exclusivamente de las capturas UAT autorizadas y no se documenta como constante.
- Produccion consume areas y puestos desde `hr-service`; no los persiste ni escribe su schema.
- Las recetas en modo API ya no usan el catalogo fijo de materiales: consumen articulos activos marcados `use_in_recipe` y balances reales de Almacenes.

### Almacenes e inventarios

- `inventory-service` es propietario de almacenes, articulos, movimientos, balances y Kardex.
- En modo API, el formulario de Movimientos persiste exclusivamente mediante `inventory-service`; al completar el comando invalida y recarga movimientos y balances. `localStorage` queda solo como fallback del modo maqueta y nunca representa un movimiento remoto registrado.
- El submodulo visible `Inventario` conserva el identificador tecnico `existencias`.
- Inventario consume balances enriquecidos con busqueda, filtros, orden y paginacion server-side.
- La vista usa container queries: colapsa el flujo por defecto, transforma la tabla en tarjetas cuando el panel central se estrecha y mueve Alertas debajo del contenido en viewports intermedios.
- Los movimientos registrados y no reversados son la fuente de verdad.
- En Local y QA, cada articulo expone `default_unit_cost_per_base_unit` con semantica explicita de costo por unidad base y un calculador HTTP para conversiones compatibles (por ejemplo kg/g o L/ml). No inventa equivalencias para empaques o unidades personalizadas.
- En Local y QA, `available_quantity = max(on_hand_quantity - reserved_quantity, 0)`. Las reservas activas y no vencidas se muestran por ubicacion y se protegen con bloqueos transaccionales por tenant/articulo/almacen.
- En Local y QA, cada articulo incorpora costo unitario predeterminado; los saldos calculan costo promedio e importe de inventario desde movimientos inmutables. Salidas, transferencias, reversiones y consumos preservan la valuacion y rechazan stock disponible insuficiente.
- La unidad base queda bloqueada despues del primer movimiento; articulos/almacenes inactivos no aceptan movimientos ni reservas y `maximum_stock` no puede ser menor que `minimum_stock`.
- La bandera `inventory.items.use_in_recipe` pertenece a la migracion `20260730_0009`. Los catalogos partieron vacios en QA; desde la promocion `0023`, su contenido depende de las capturas UAT autorizadas y no se documenta como constante.
- Inventario muestra con saldo cero los articulos sin movimientos que tengan almacen sugerido.

### Recursos Humanos

- Areas y puestos son catalogos generales de RH. La bandera `intervenes_in_production=true`, junto con estatus activo, es la unica que hace elegible un puesto y sus trabajadores para recetas y ordenes; crear un puesto nuevo no activa esa bandera por defecto.
- La validacion local cubrio 10,000 articulos y 10,000 movimientos; consultar `docs/operaciones/validacion_volumen_inventario_local.md`.

### Ventas

- En Local y QA, `sales-service` persiste Clientes, Cotizaciones, Pedidos y Entregas mediante las revisiones `20260818_0018`/`0019`/`0020`. CHG-204 cerro el plan correctivo de CHG-203: alta de Entregas, mapeo producto-articulo, sanitizacion, costo real por fuente y orquestacion durable/concurrente.
- Clientes exige codigo estable, contacto principal, moneda/condiciones controladas y responsable seleccionado de trabajadores activos de RH. El perfil fiscal es opcional, pero al iniciarse exige razon social, RFC/ID fiscal y correo de facturacion.
- Cotizaciones exige cliente activo, producto/servicio activo de Produccion y unidad activa de Administracion igual a la unidad base. Backend calcula subtotal, descuentos, total, costo snapshot y margen estimado.
- Los estados reales son borrador, cotizada, aprobada, vencida y cancelada; solo el borrador es editable y emitir/aprobar revalida referencias autoritativas.
- CHG-201 audito la sinergia modular: `sales` declara dependencias efectivas `hr`/`production`; Backoffice, onboarding y Administracion bloquean activaciones o apagados que dejen autoridades rotas, bajo bloqueo transaccional. La API sigue validando modulo y permiso aunque se oculte la UI.
- Los endpoints de lectura no requieren resolver maestros y la UI usa `Promise.allSettled`: una falla de catalogos o autoridades conserva documentos comerciales disponibles y bloquea solamente las mutaciones dependientes.
- El onboarding inserta entitlements antes de poblar permisos del owner. Seleccionar Ventas desde Backoffice incluye RH y Produccion, evitando un tenant activo sin autorizaciones comerciales.
- Pedidos nacen una sola vez de una cotizacion aprobada. Cada producto exige el articulo de Inventory mapeado por Production y puede usar reserva o solicitud de Production; servicios quedan listos. Surtido, cancelacion y confirmacion reclaman estado durable bajo locks, reanudan con claves estables y marcan `needs_reconciliation` tras una interrupcion externa. El costo de `stock` proviene del consumo y el de servicio de captura operativa; Production permanece sin costo real hasta su callback. Devoluciones y facturacion permanecen `planned`.
- QA ya tiene `sales-service` y la cadena comun de migraciones hasta `20260825_0029`; la habilitacion efectiva de Ventas continua dependiendo del entitlement del tenant y de RH/Produccion.
- CHG-250 alinea la verdad visible de Ventas: Pedidos se cuenta como capacidad implementada, se elimina copy planeado obsoleto y `Margen` queda como consulta de solo lectura derivada de Pedidos/Entregas, sin alta generica ni persistencia local de documentos.
- CHG-255 esta aplicado y certificado en PostgreSQL Local con `20260901_0030`: cada partida de servicio de un Pedido confirmado crea una Orden de servicio propia con planeacion, responsable RH, tiempos, costos, evidencia, maquina de estados y aceptacion. Las Entregas conservan exclusivamente productos fisicos. QA permanece en `20260825_0029` y no contiene este corte.

### Compras

- CHG-255 permite activar Compras sin Inventory para tenants que solo adquieren servicios. Cada partida valida una unidad activa de Admin; `inventory_item` exige articulo/almacen y conserva la integracion con Inventory, mientras `service` los prohibe y registra solo recepcion comercial. El cambio esta aplicado y probado en Local con `20260901_0030`; QA no contiene esta ampliacion.

### Interfaz transversal

- CHG-249 aplica una jerarquia visual mas sobria a botones y badges operativos: las acciones secundarias usan superficies neutras, las primarias conservan el acento morado y los estados activo/advertencia/error usan color semantico suave con borde y contraste para tema claro/oscuro. El bloque CSS esta aislado para rollback y conserva targets de 44 px.
- CHG-250 corrige la identidad de los submodulos RH; localiza su guia, resumen de capacidad y estados laborales provenientes de API; completa los nombres ingleses de Mantenimiento y las etiquetas/atributos accesibles del shell. Los nombres y descripciones capturados por el tenant permanecen como datos sin traduccion automatica.

- CHG-227, implementado solo en Local: toda mutacion HTTP iniciada desde el frontend principal o Backoffice muestra una capa de progreso bilingue, marca la pagina con `aria-busy` y bloquea botones, clics y activaciones por teclado mientras la operacion sigue pendiente. Un contador conserva el bloqueo cuando coinciden varias solicitudes y `finally` lo libera ante exito o error, reduciendo comandos duplicados por reintentos del usuario.

- El shell, los modulos activos, los catalogos, formularios y modales comparten reglas responsive basadas en el ancho real de su contenedor.
- La guia descriptiva conserva el patron compartido de riel vertical izquierdo y compresion; solo pasa a una columna en anchos estrechos o mediante una excepcion explicita de pantalla.
- En anchos intermedios las colecciones reducen columnas; en anchos estrechos formularios y acciones se apilan sin ocultar su significado.
- El backoffice transforma sus filas de tenants y consumo en tarjetas etiquetadas cuando su panel se estrecha.
- La navegacion movil conserva los submodulos activos, foco visible, salto al contenido y anuncios accesibles de notificaciones.
- `npm.cmd run validate:responsive` protege los contenedores, puntos de accesibilidad y referencias documentales obligatorias.

## Calidad

- La fuente normativa de ambientes es `docs/arquitectura/fronteras_ambientes_local_qa_produccion.md`; la skill `$erclave-environment-boundaries` aplica su preflight.

- La fuente de verdad del resultado automatizado es la ultima ejecucion de `npm.cmd run verify`.
- En el corte CHG-195: `npm.cmd run verify` aprobo validadores, parseo/paridad OpenAPI, compilacion y `151 passed, 2 skipped`; las dos integraciones PostgreSQL omitidas por el comando general aprobaron aparte contra `erclave_local` con rollback. El smoke autenticado confirmo frontend, cuatro APIs, readiness, sesion y 50 unidades activas en Local.
- En el corte CHG-197: `npm.cmd run verify` aprobo validadores, parseo/paridad OpenAPI, compilacion y `161 passed, 3 skipped`; Alembic actualizo exclusivamente `127.0.0.1:5434/erclave_local` de `20260818_0016` a `20260818_0017`. No hubo QA ni Produccion.
- CHG-198 sincronizo fichas de agentes/modulos, ownership, modelo y diagramas con ese corte y agrego guardrails semanticos. No cambio runtime ni ambientes: las capacidades 0017 continúan exclusivas de Local y QA permanece en `20260805_0013`.
- CHG-199 formalizo el gobierno de documentacion viva y agrego `validate:documentation` al ciclo obligatorio. El control deriva automaticamente la cabeza Alembic, revision QA, ultimo CHG, indice modular y enlaces internos, y verifica que agentes e inicio de sesion mantengan estas reglas.
- CHG-200 implemento el primer corte real de Ventas solo en Local: Clientes/Cotizaciones y revision `20260818_0018`; su evidencia historica permanece en `TRAZABILIDAD.md`.
- CHG-201 audito Ventas y su gobierno modular sin agregar migracion: corrigio dependencias `sales -> hr/production`, permisos de owner en onboarding, lectura parcial por permiso, botones/transiciones, busqueda comercial e idempotencia concurrente. `npm.cmd run verify` aprobo `172 passed, 6 skipped`; las integraciones PostgreSQL adicionales aprobaron `6 passed` y el smoke Firebase valido ambos niveles con estado final restaurado. QA no cambio.
- CHG-202 extiende el runtime Local con la revision `20260818_0019`: Pedidos, surtido por servicio/Inventory/solicitud a Production, Entregas parciales o totales, catalogos comerciales administrables y plantilla documental tenant-safe. `npm.cmd run verify` aprobo `173 passed, 6 skipped`; la integracion PostgreSQL Sales aprobo `11 passed` y el smoke autenticado confirmo frontend/cinco APIs, catalogos, plantilla y lecturas nuevas. Devoluciones permanecen planeadas; QA no cambio.
- CHG-203 audito ese corte sin cambiar runtime: confirmo pruebas verdes y documento bloqueadores de UI, XSS, validaciones, identidad producto-articulo, costo real y consistencia distribuida. En ese punto el segundo corte quedo condicionado a cerrar la auditoria.
- CHG-204 aplico el plan de correccion CHG-203 solo en Local y agrego la revision `20260818_0020`, contratos, UI, pruebas y documentacion sincronizada. `npm.cmd run verify` aprobo `177 passed, 8 skipped` y la integracion PostgreSQL Sales `4 passed`. QA permanece sin Sales y en `20260805_0013`.
- En el corte CHG-164: `npm.cmd run verify` aprobo todos los validadores, compilacion y `121 passed, 1 skipped`; el smoke autenticado del stack local canonico con Firebase Emulator respondio correctamente en los seis modulos activos.
- En el corte CHG-166: `npm.cmd run verify` aprobo contratos, validadores, sintaxis y `126 passed, 1 skipped`; el smoke local creo y recargo producto, maquinaria, receta vigente, orden con snapshots y su ciclo completo de etapas.
- El repositorio puede contener cambios locales no confirmados; `session:context` debe mostrar el estado Git real de cada sesion.
- `npm.cmd run session:context` reconstruye la memoria operativa sin mostrar secretos: Git, trazabilidad, migraciones, estado, decisiones, tenants, pendientes y puertos locales.
- `validate-session-context.js` protege la presencia de los documentos y guardrails obligatorios.
- `validate-responsive-ui.js` protege el estandar transversal de interfaz para futuras sesiones.
- El candidato incorpora un pipeline QA manual en dos fases: construccion inmutable por SHA/digest y promocion con aprobaciones independientes para base, servicios, trafico y frontend.
- La configuracion backend de QA/Produccion rechaza URLs locales, CORS local, autenticacion demo, Firebase sin proyecto y base ausente antes de arrancar.
- El build QA del frontend elimina configuracion local, emulador, tenant y actor; `validate-qa-release-pipeline.js` protege estas fronteras.
- Fuera de localhost, modo API y URLs provienen del artefacto; Firebase identifica al actor y `/v1/session/tenants` resuelve el tenant activo en memoria. Los overrides de `localStorage` no pueden cambiar la frontera QA.
- En modo API, la representacion temporal de catalogos operativos vive solo en memoria y se repuebla desde Admin, Produccion, Inventory y RH. Los datos operativos del navegador no persisten entre sesiones ni se tratan como fuente de verdad.
- La configuracion estructural del tenant QA requiere confirmacion separada, sincroniza el catalogo de permisos y deja activos solamente `admin`, `production`, `inventory` y `hr`; no carga datos funcionales.
- GitHub Pages ya no se publica automaticamente desde `main`; permanece como maqueta manual.
- El 2026-08-08 se aprovisionaron en GCP QA las seis identidades dedicadas de `infra/qa/identity-plan.json`, Artifact Registry `erclave-qa` y Workload Identity Federation limitado a `ChemaPsan/eslaclave-erclave`; los accesos al secreto, Artifact Registry, Cloud SQL, Cloud Run y `actAs` quedaron delimitados por recurso o identidad.
- Los GitHub Environments `qa-build`, `qa-database`, `qa-services`, `qa-traffic` y `qa-frontend` exigen aprobacion de `ChemaPsan`; las variables QA del pipeline quedaron configuradas sin llaves JSON ni URL de base de datos.
- La identidad federada `erclave-github-deployer-qa` tiene `roles/firebasehosting.admin` en el proyecto QA `erclave`; el plan versionado y el validador del pipeline exigen ese permiso minimo para el gate `qa-frontend`.
- Cloud SQL QA exige conexiones cifradas (`ENCRYPTED_ONLY`), tiene PITR activo con siete dias de logs y conserva el backup manual exitoso `1786227437185`, creado antes del endurecimiento.
- El candidato CHG-182 fue construido una sola vez por digest y promovido en QA. Tras CHG-191, `admin-service-qa-bo-1-1` recibe 100% del trafico Admin; `inventory-service-qa-00003-zus`, `hr-service-qa-00003-gor` y `production-service-qa-00008-vuv` conservan 100% en sus servicios. Las cuatro URLs estables aprobaron health, readiness con Cloud SQL y version `4e9c6881dab61239f1abd5fff688019fdd697977`.
- Inventory y RH ya tienen servicio real desplegado en QA y entitlements estructurales activos para `ERClave Demo QA`; sus catalogos permanecen sin carga funcional o dummy. Ventas e Integraciones permanecen inactivos.
- El frontend sanitizado CHG-182 esta publicado en Firebase Hosting QA mediante el gate `qa-frontend` del run `31647661435`. `https://erclave.web.app` responde HTTP 200 y su configuracion runtime publicada referencia exclusivamente las cuatro APIs Cloud Run QA, Firebase QA y ningun tenant/actor local.
- CHG-191 configuro `QA_BACKOFFICE_ADMIN_EMAILS` y el run `31661213987` promovio `admin-service-qa-bo-1-1` mediante `qa-services` y `qa-traffic`. La revision reutiliza la imagen Admin certificada, conserva version CHG-182 y separa la allowlist interna de roles owner; rollback: `admin-service-qa-00017-dih`.
- El 2026-08-12 se repitio una verificacion publica read-only: Admin, Produccion, Inventory y RH respondieron ambiente `qa`, readiness con base configurada y la misma version CHG-182; `https://erclave.web.app/env.js` publica modo API/Firebase y las cuatro URLs QA.
- El candidato local posterior corrige dos huecos de paridad antes del siguiente release: Settings ya no carga silenciosamente `backend/.env`, Local rechaza bases/URLs/Firebase QA, y el frontend QA conserva en memoria el tenant resuelto desde `/v1/session/tenants` sin caer al tenant/actor demo. Estos cambios aun no estan desplegados en QA.
- En los cortes CHG-182 a CHG-190, `npm.cmd run verify` aprobo validadores, compilacion y `135 passed, 1 skipped`; el release QA `31647661435` completo migracion, configuracion, despliegue, smoke, promocion de trafico backend y publicacion del frontend. Los cuatro servicios publicos conservan health, readiness y version `4e9c6881dab61239f1abd5fff688019fdd697977`.

Este archivo debe describir hechos comprobados, no planes ni aspiraciones.

## Evidencia historica incorporada

Las entradas siguientes conservan el estado observado al cerrar cada CHG y no sustituyen el inventario vigente de las secciones anteriores.

# Actualizacion CHG-206 (2026-08-20)

En Local quedó implementada la vinculación guiada de producto terminado entre Almacenes, Producción y Ventas. Producción conserva la referencia autoritativa 1:1; el alta crea un artículo `finishedGood` con la misma unidad y admite identidad logística distinta de la comercial. No hubo migración ni promoción a QA/Producción.
# Actualizacion CHG-207 (2026-08-20)

En Local existe el Custodio de manuales funcionales de la solucion y la skill `$erclave-solution-manuals`. La biblioteca `docs/manuales_solucion/` separa fuentes Markdown revisables de documentos Word generados y registra cobertura, ambiente y dudas funcionales por modulo. CHG-271 mantiene siete manuales funcionales de módulos implementados, sus Word y la guía del tester para QA b63cdad. Los módulos planeados no reciben manual operativo; la cobertura y limitaciones vigentes están en REGISTRO.md.
# Actualizacion CHG-208 (2026-08-20)

En Local, Entregas de Ventas vuelve a mostrar la fecha programada requerida en modo API. Los vinculos Cotizacion -> Pedido y Pedido -> Entrega sustituyen listas extensas por busqueda acotada sobre folio, cliente, producto/servicio, importe o estado, conservando solo documentos elegibles. No cambia API ni persistencia; la paginacion server-side para volumen mayor a 200 permanece pendiente.

# Actualizacion CHG-209 (2026-08-20)

En Local, las referencias crecientes implementadas en Administracion, Produccion, Almacenes, Ventas y Recursos Humanos usan búsqueda acotada con identidad visible e ID estable. Estatus, tipos, prioridades y otros catálogos cerrados conservan selectores directos. El patrón es accesible por teclado, reacciona a catálogos actualizados y cuenta con un validador transversal; no cambia APIs ni persistencia y la paginación server-side para más de 200 candidatos sigue pendiente.

# Actualizacion CHG-210 (2026-08-20)

En Local, la raíz de cada módulo es un centro de reportes estándar de solo lectura. Producción, Almacenes, Recursos Humanos, Ventas y Administración muestran sus catálogos/reportes propios sin botones de alta, captura rápida ni acciones de negocio; el patrón y catálogo mínimo también quedaron definidos para Compras, Gastos, Costos y Contabilidad antes de su activación. Las mutaciones permanecen en submódulos. Reportes continúa inactivo y se reserva para cruces, tableros configurables y análisis especializados. No cambia APIs ni persistencia.

# Actualizacion CHG-212 (2026-08-21)

En Local, Administracion gobierna folios y consecutivos por tenant; Produccion identifica recetas y ordenes con codigos de negocio, exige fases ponderadas al 100% y calcula avance general ponderado; Entregables por area conserva numero, peso y area de la fase. Almacenes expone costo por unidad base y conversiones estandar compatibles. RH mantiene areas y puestos generales y solo comparte con Produccion los marcados explicitamente. Las revisiones `20260821_0021` y `20260821_0022` estan aplicadas solo en PostgreSQL Local; QA permanece en `20260805_0013`.

# Actualizacion CHG-241 (2026-08-25)

En Local, Produccion ya no exige concentrar todos los minutos de mano de obra y maquinaria en una sola fecha. Recetas guardan una duracion sugerida y las ordenes capturan inicio, dias productivos y fecha requerida. Production distribuye capacidad de lunes a viernes, descuenta compromisos activos por dia, devuelve el desglose autoritativo y persiste compromisos diarios bajo bloqueo transaccional. Los materiales se validan y reservan una sola vez. La revision `20260825_0029` esta aplicada solo en `127.0.0.1:5434/erclave_local`; QA y Produccion permanecen sin cambios. Calendarios tenant, turnos, festivos, ausencias y afectacion automatica por mantenimiento siguen pendientes.

# Actualizacion CHG-242 (2026-08-25)

En Local, el editor de Recetas ofrece maquinaria activa y en mantenimiento, incluso si su area RH sigue pendiente. La receta define que equipo requiere el proceso; el estatus operativo se evalua al validar/liberar la orden. Por ello una maquina en mantenimiento puede guardarse en la receta, pero sigue aportando cero minutos y bloquea la orden hasta volver a activa. Maquinaria inactiva o inexistente permanece rechazada. No hubo migracion ni cambios de maestros; QA y Produccion permanecen sin cambios.

# Actualizacion CHG-243 (2026-08-25)

En Local, **Validar definicion** dentro de Recetas comprueba exclusivamente que cada recurso exista y sea elegible y proyecta cantidades/costo; no compara inventario ni horas disponibles. La duracion sugerida solo precarga la futura orden. **Validar orden** conserva la comprobacion autoritativa de materiales, minutos de puestos y maquinas, compromisos existentes y horizonte multi-dia. No hubo migracion ni cambios de datos; QA y Produccion permanecen sin cambios.

# Actualizacion CHG-244 (2026-08-25)

El frontend Local compacta el shell y elimina la identidad generica **Centro operativo** y los badges tecnicos de persistencia. Los indicadores transversales viven ahora encima de **Alertas operativas** y responden al ancho del panel lateral. Los modales adaptan validaciones de recursos y partidas de Compras por su propio contenedor; Mantenimiento y Compras usan tarjetas operativas que apilan identidad, responsable, estados, partidas y acciones sin comprimir palabras. Los controles operativos pequenos conservan un target minimo de 44 px. La cobertura ES/EN activa incluye tambien Compras, Mantenimiento y Recursos Humanos. No hubo cambio de API, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-245 (2026-08-25)

El frontend Local aprovecha mejor la zona superior en todos los modulos y submodulos. Contexto de sesion, sucursal, busqueda y accion contextual comparten una topbar adaptable en escritorio; en ancho intermedio se compactan antes de apilarse. La cabecera blanca previa al hero funciona solo como breadcrumb y retorno, sin repetir el titulo principal; heroes, workspace y paneles reducen su altura y espaciado compartidos. No hubo cambio de API, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-246 (2026-08-25)

En Local, Resolver y Cancelar ordenes de Mantenimiento ya no usan cuadros `prompt()` del navegador. Ambas acciones abren formularios dentro del modal ERClave; Resolver captura diagnostico, causa raiz opcional, trabajo realizado y verificacion, mientras Cancelar solicita el motivo auditable. Validaciones y errores permanecen dentro del formulario. No hubo cambio de API, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-247 (2026-08-25)

En Local, la captura requerida de tiempo de Mantenimiento ya es visible desde cada tarjeta de orden activa mediante **Registrar tiempo**. Resolver muestra el total acumulado y, cuando la orden tiene cero minutos, integra Inicio, Fin y Notas antes de ejecutar la transicion; si el rol carece de `maintenance.time.create`, explica la autoridad faltante. No hubo cambio de contrato, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-211 (2026-08-20)

En Local se revirtió únicamente la portada de Administración: vuelve a mostrar su centro de configuración de organización, usuarios, roles, permisos, módulos activos y catálogos base. Los módulos operativos conservan las portadas de reportes estándar de CHG-210 y Reportes continúa inactivo. La excepción de Administración quedó documentada y protegida por el validador transversal; no cambia APIs ni persistencia.

# Actualizacion CHG-213 (2026-08-21)

En Local se corrigio la apertura de los selectores buscables para mostrar el catalogo completo antes de filtrar. RH devuelve validaciones de expediente accionables sin repetir CURP, RFC o NSS y el formulario declara sus longitudes. Produccion impide elegir materiales con unidades fuera del catalogo activo y explica faltantes autoritativos por recurso antes de asignar el folio de orden. Una orden en espera puede iniciar solo si conserva reservas materiales; liberar reserva, iniciar no descuenta y completar consume las reservas como salidas de Inventario. Los datos demo heredados `LTS`/`MT` y la falta de trabajadores `Fundidor A` no fueron corregidos automaticamente porque son incidencias operativas de maestros. No hubo migracion, despliegue ni escritura en QA/Produccion.

# Actualizacion CHG-214 (2026-08-21)

En Local, la revision `20260821_0023` normalizo de forma transaccional los alias heredados e inequivocos `LTS -> LTR` y `MT -> MTR` en Inventario, Produccion y snapshots de Ventas. Cada fila corregida conserva evidencia en `admin.audit_events`; el downgrade restaura solo las filas registradas que no hayan cambiado despues. La proteccion que impide cambiar realmente la unidad base de un articulo con movimientos o reservas permanece vigente y ahora se explica en espanol/ingles desde la interfaz. `cera_01` conserva identidad, cantidades, costo e historia y ahora usa `LTR`. QA y Produccion permanecen sin cambios en `20260805_0013`.

# Actualizacion CHG-215 (2026-08-21)

En Local, crear o versionar una receta ya no produce `500` cuando incluye maquinaria activa sin referencia estable a un area de RH. Production responde `422 machine_resource_invalid` con una causa operativa segura; la UI excluye esa maquinaria del selector y muestra que debe abrirse en Maquinaria para vincular un area activa. Se conserva la regla de no relacionar maestros automaticamente por nombre. El dato Local `h_002` sigue sin modificarse: su texto de area existe, pero `area_ref_id` permanece vacio hasta confirmacion del operador.

# Actualizacion CHG-216 (2026-08-21)

En codigo Local, la primera transicion de una orden liberada o en espera hacia **En produccion** consume sus reservas por medio de Inventory. Cada reserva genera una salida inmutable en el almacen que la otorgo y devuelve cantidad/costo para el real de materiales. Reanudar, volver desde validacion o completar no genera otra salida; cancelar antes de iniciar libera reservas y cancelar despues conserva los movimientos fisicos. Iniciar una etapa ya no puede saltarse el comando de estatus. No hubo migracion ni mutacion de ordenes, reservas o movimientos existentes; QA/Produccion permanecen sin cambios.

# Actualizacion CHG-217 (2026-08-21)

En Local, el formulario de nueva orden ya no mezcla faltantes calculados por la maqueta con datos reales. En modo API valida localmente solo campos y responsables, y delega existencia disponible, reservas, capacidad laboral y maquinaria a `POST /v1/production/resource-validations`. El modo mock conserva su calculadora local. No cambia contratos, persistencia ni datos; QA/Produccion permanecen sin cambios.

# Actualizacion CHG-218 (2026-08-21)

En Local, **Validar orden** usa la receta maestra recargada y su `currentVersionId` aprobado, no el snapshot transitorio del formulario. Los snapshots historicos permanecen para ordenes creadas y documentos. `rec-000004` ya estaba correctamente activa/aprobada en PostgreSQL; no se modificaron sus datos. No cambia contratos ni persistencia y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-219 (2026-08-21)

En Local se corrigio el cierre de una reserva al consumirla totalmente: Inventory conserva su ultima cantidad positiva como snapshot historico, cambia el estatus a `consumed` y reporta saldo operativo cero. El intento fallido de iniciar `OP-000003` fue revertido completamente por PostgreSQL; la orden sigue en espera, las reservas siguen activas y no existen salidas parciales. No cambia schema ni contrato y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-220 (2026-08-21)

En Local, una orden solo entra a **En validacion** cuando todas sus fases estan terminadas u omitidas; la ultima fase realiza el cambio automaticamente. El selector solo ofrece transiciones validas y muestra **Terminada** cuando tambien se guardo el uso real de mano de obra y maquinaria desde **Cierre/consumos**. `OP-000003` permanece sin mutacion, en validacion con sus dos fases pendientes, y puede recuperarse volviendo a **En produccion**. No cambia schema y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-221 (2026-08-21)

En Local, el avance de una fase se captura como porcentaje: 0% pendiente, 1-99% en proceso y 100% terminada. Todas las fases deben estar al 100% para validar y cerrar; los minutos y el uso real de mano de obra/maquinaria ya no bloquean este corte y quedan diferidos hasta definir el modelo de eficiencia. `OP-000003` ya conserva sus dos fases al 100% y esta lista para terminar despues de recargar. No hubo mutacion de datos, cambio de schema ni escritura en QA/Produccion.

# Actualizacion CHG-222 (2026-08-21)

En Local, **Almacenes > Movimientos** muestra las ordenes de Produccion terminadas con cantidad pendiente. El almacenista confirma almacen, cantidad, fecha y observaciones; Inventory valida la orden y el vinculo por ID, deriva articulo/unidad/costo, registra una entrada trazable y permite parciales sin exceder lo producido. No se recibieron ordenes automaticamente, no hubo migracion y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-223 (2026-08-21)

El reinicio individual de Inventory Local ahora carga y valida explicitamente la base `127.0.0.1:5434/erclave_local`, Firebase Emulator y dependencias loopback antes de iniciar. Se corrigio el `500` causado por un proceso con health activo pero sin URL efectiva de base. El GET autenticado de almacenes devuelve `200`; no se modificaron datos ni QA/Produccion.

# Actualizacion CHG-224 (2026-08-21)

El repositorio queda preparado, pero no autorizado ni desplegado, para un candidato QA de cinco servicios: Admin, Produccion, Inventory, RH y Ventas. El pipeline construye/promueve las cinco imagenes por digest, entrega a Inventory la URL autoritativa de Produccion para recepciones y publica la URL de Ventas en el frontend sanitizado. QA vigente conserva cuatro servicios, version `4e9c6881dab61239f1abd5fff688019fdd697977` y revision documentada `20260805_0013`. Antes de ejecutar se requieren PR/SHA inmutable, identidad `erclave-sales-qa`, variables Sales y aprobaciones separadas de cada gate. No hubo escritura externa.

# Actualizacion CHG-225 (2026-08-21)

El corte CHG-224 ya esta fusionado en `main` con SHA inmutable `adb134f7ac8b33b4a842d07db10c9b5f88525f2f` y su validacion CI concluyo correctamente. En QA se creo la identidad dedicada `erclave-sales-qa@erclave.iam.gserviceaccount.com` sin llaves administradas por usuario; conserva solo `roles/cloudsql.client`, acceso al secreto `erclave-database-url-qa` y `roles/run.invoker` sobre Admin, RH, Produccion e Inventory. GitHub Actions ya contiene las variables no secretas `QA_SALES_RUNTIME_SERVICE_ACCOUNT` y `QA_SALES_API_URL`. No se construyo candidato, no se leyo el secreto, no se ejecuto migracion/configuracion de tenant, no se desplego Cloud Run, no se movio trafico y no se publico frontend.

# Actualizacion CHG-226 (2026-08-23)

El workflow gobernado `32621200718` promovio a QA el SHA inmutable `7aa5c674b605d8268b6bfe00e0812b6a300277cb`, ejecuto Alembic hasta `20260821_0023`, llevo a 100% las revisiones certificadas de cinco servicios y publico el frontend sanitizado en `https://erclave.web.app`. Despues del ajuste de configuracion CHG-226, el trafico actual de Admin apunta a `admin-service-qa-00021-669`; Inventory permanece en `inventory-service-qa-00006-ceb`, RH en `hr-service-qa-00006-xey`, Produccion en `production-service-qa-00011-naj` y Ventas en `sales-service-qa-00001-gez`. Todos conservan el mismo SHA certificado.

Durante UAT, crear y eliminar tenants devolvio `500`. Cloud Logging demostro `INSUFFICIENT_PERMISSION` del Admin SDK de Firebase en la identidad runtime `erclave-admin-qa@erclave.iam.gserviceaccount.com`; no fue un error operativo. Con autorizacion explicita se concedio solamente `roles/firebaseauth.admin` a esa cuenta. El tenant que se intento eliminar ya habia sido borrado en PostgreSQL antes del fallo de limpieza; la identidad Firebase asociada tampoco existia, comprobado con un job efimero sobre la misma imagen, eliminado al terminar. No se cargaron datos ni se modificaron otros tenants.

El primer onboarding posterior respondio `201`, pero no envio correo porque la clave web publica solo llegaba al frontend. Con autorizacion explicita se agrego `ERCLAVE_FIREBASE_WEB_API_KEY` al runtime Admin, se valido la revision `admin-service-qa-00021-669` por URL etiquetada y se promovio al 100% conservando imagen y SHA. El workflow ahora deriva siempre esa variable desde `QA_FIREBASE_API_KEY`; los siguientes onboardings solicitan el correo de restablecimiento a Firebase en vez de devolver solo un enlace manual.

En la rama CHG-226, aun pendiente de una nueva promocion gobernada, Admin traduce fallos Firebase a errores seguros y separa el resultado principal del seguimiento de invitacion/limpieza. El onboarding puede responder `invitation.delivery=pending` si el tenant ya persistio pero la invitacion fallo; el borrado responde `firebase_identity_cleanup.status=completed|pending` sin exponer correos internos ni presentar una limpieza secundaria como fracaso total.

# Actualizacion CHG-238 (2026-08-24)

En Local, Compras expone de forma continua el ciclo ya implementado por API: aprobar una requisicion abre la creacion de orden con la requisicion precargada; crear conserva la orden en borrador; emitir abre la recepcion con la orden seleccionada. Las tarjetas conservan accesos explicitos para retomar el siguiente paso. Formularios y comandos de proveedor, requisicion, orden y recepcion se muestran solo con su permiso puntual. No hubo migracion, cambio de contrato, escritura operativa ni modificacion en QA/Produccion.

# Actualizacion CHG-239 (2026-08-24)

En Local, Mantenimiento hace visible el tecnico asignado y conserva su seleccion al reasignar. Las ordenes elegibles enlazan directamente a **Solicitar refacciones** con el folio precargado; las solicitudes muestran sus partidas y estados. El diagnostico Local confirma que la base vigente no contiene un almacen `spare_parts`, por lo que la UI ahora ofrece abrir su alta en Inventario, preseleccionada correctamente y sujeta a `inventory.warehouse.create`, en vez de ocultar el recorrido. No se crearon maestros automaticamente, no hubo migracion ni cambios en QA/Produccion.

# Actualizacion CHG-240 (2026-08-24)

En Local, **Compras > Ordenes de compra** muestra primero el historial completo sin filtrar estatus y solo presenta el alta cuando hay requisiciones aprobadas pendientes de conversion. El diagnostico autenticado encontro dos OC emitidas (`OC_0001`, `OC_0002`) y ninguna requisicion elegible: `REQ_001`/`REQ_003` ya estan convertidas y `REQ_002` cancelada. **Reabastecimiento** queda visual y semánticamente separado como capacidad planeada; no contiene OC. No hubo escritura operativa, migracion ni cambios en QA/Produccion.


## Ajustes UAT Local CHG-266

CHG-266 implementado solo en Local: Proveedores listado/modal; Requisiciones legible en contenedores estrechos; Control de orden fuera del riel colapsado; acciones y mensajes del ciclo de cotizaciones. Reparación acotada del catálogo y cuatro asignaciones al Owner del tenant ten_739ee59d765d5e14818674800d, por API auditada. Local continúa en 20260908_0034, sin migración de este corte ni promoción QA.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Solicitudes compactas Local CHG-267

CHG-267 implementado solo en Local: Movimientos abre con resumen desplegable cerrado para las siete bandejas y aviso de pendientes; historial visible debajo. Sin contratos, migraciones, permisos ni datos persistentes modificados. Cabeza Local 20260908_0034; QA permanece igual.

Evidencia y APIs: `docs/auditorias/almacen_solicitudes_desplegables_2026-09-08.md`.
