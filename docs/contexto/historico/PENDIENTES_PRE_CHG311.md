# Archivo histórico de PENDIENTES.md · corte previo a CHG-311

> **Evidencia histórica, no instrucciones vigentes.** Conserva las notas acumuladas hasta CHG-310, archivadas el 2026-10-07. Las afirmaciones de estado, pendientes y autorizaciones corresponden a sus fechas y pueden estar sustituidas. Volver a la [fuente viva](../PENDIENTES.md) antes de planear o ejecutar. El cuerpo original se conserva; únicamente los enlaces relativos se ajustan a esta ubicación.

# Pendientes priorizados de ERClave

## CHG-310 · Lista conciliada por submódulo · 2026-10-07

El detalle vigente está en [CONTROL_CONTABLE.md](../CONTROL_CONTABLE.md), mantenido por el agente técnico de Contabilidad. Pendientes de implementación: CC-08 moneda de servicios; CC-10 tarifas/capacidad; CC-11/12 fabricación; CC-14 otros flujos Inventory; CC-15 documentos Compras; CC-16 Mantenimiento; CC-17 configuración/impresión; CC-18 folios. CC-19 datos reales y CC-20 aceptación integrada siguen abiertos.

Conservar CC-01–07/09/13: organización, catálogo centros, asignaciones, condiciones, cotización/pedido, stock/entrega y manuales/reversas ya implementados en Local; servicios CC-08 también conserva su separación/ciclo. CONT-09–18 contables posteriores se distinguen en la matriz y no condicionan operar con Accounting apagado. Las notas inferiores son evidencia de sus cortes; no sumarlas como lista vigente. La política CHG-309 está resuelta.


## CHG-309 · Producción: decisión resuelta, implementación pendiente · 2026-10-07

Ya no falta respuesta sobre moneda de tarifas. El usuario confirmó: «sí, en la moneda base de la Sociedad; esto aplica para todo». Regla transversal para costos y tarifas de toda la operación, incluidos materiales, máquinas y mano de obra. Cuando un documento use otra moneda, conservar original y convertido con tipo de cambio explícito. No reinterpretar ni convertir automáticamente historia sin moneda confirmada. Funciona con Accounting apagado. No volver a preguntar esta política; su aplicación completa sigue pendiente de implementación. Continuar la integración de fabricación detallada en INICIO_SESION.md; el mapeo real aún está pendiente.


## Actualización CHG-308 · 2026-10-07

Producción sigue abierto: conectar contexto desde origen/captura a validación y liberación; recursos y capacidad por División, confirmar moneda de tarifas, reservas/consumos/recepción y fabricación de pedido; UI y aceptación integrada. Preparación y guards CHG-308 implementados, no equivalen a cierre. Pregunta sobre tarifas resuelta en CHG-309; demás frentes CHG-307 siguen vigentes. Ver docs/arquitectura/cont_08_produccion_contexto.md.


## Actualización CHG-307 · 2026-10-05

Avance comprobable: stock → reserva → entrega/costo original-convertido implementado Local. Pendiente: fabricación y contexto Production; Inventory transferencias/devoluciones y otros productores; documentos Purchasing y Maintenance; configuración/emisor/impresión; folios; mapeo/backfill reales; aceptación transversal y candidato QA. El mapeo real sigue esperando respuesta. No repetir cotización/pedido/servicios ya cerrados. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


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

Implementado [CONT-05](../../arquitectura/cont_05_catalogo_centros.md): Centros de costos desde Administración → Organización → Divisiones, dueño Costing en API 8014 y esquema propio. Alta/nombre/estado, código automático Admin, permisos puntuales, alcance, revisión, idempotencia y auditoría. Catálogo independiente de analítica y Accounting; obligación sólo por flujo habilitado. Alembic Local `20260927_0040`; sin centros ni estructura ficticios permanentes. Runtime Local recargado; QA/Producción intactos.

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


## CHG-293 — continuar separación después de sesión

- CONT-03 implementado Local; no rehacer decisiones CONT-00 ni repetir conversión de membresía ya v2. Contrato: `docs/arquitectura/cont_03_sesion_alcances.md`.
- Continuar CONT-04 configuración por alcance, CONT-05 catálogo Costing administrado desde Admin y CONT-06 folios. Después CONT-07/08 para maestros y documentos. La autorización Local del usuario sigue vigente; QA sigue fuera de alcance.
- Esperar estructura Sociedad/División/Centro de costos y asignación explícita para migrar los datos operativos existentes. Pregunta enviada al usuario durante CHG-293; no hay respuesta registrada. Se puede continuar código/fixtures reversibles mientras tanto.
- La sesión v2 no filtra por sí sola documentos de los servicios operativos. No presentar separación completa hasta probar rechazos cruzados en cada consumidor de CONT-07/08.
- Contabilidad tiene fichas senior y skill; eventos, libros, periodos, mapeos y pólizas permanecen planned. La cobertura documental de agentes no es una certificación de seguridad de cada endpoint.

## CHG-292 — siguiente corte CONT-03

- CONT-02 implementado Local: APIs/UI, permisos, transición revisada y proyección compatible. No repetir CONT-00 ni volver a pedir decisiones ya resueltas.
- Implementar CONT-03: sociedades/divisiones visibles en sesión, alcance versionado de membresía, selector de División activa, validación backend y conservación de IDs mediante equivalencias. Una nueva División no amplía scopes restringidos.
- CONT-04: configuración por División. CONT-05: Centros de costos en Administración consumiendo Costing. CONT-07/08: selección obligatoria según División activa y propagación a maestros/documentos. CONT-02 todavía no calcula contabilidad.
- Validación de aceptación humana sobre datos de negocio y eventual release QA son tareas distintas; no hay promoción QA autorizada vigente. Los permisos amplios de los adaptadores heredados se conservan explícitamente hasta migrar consumidores/permisos.
- [Contrato y evidencia CONT-02](../../arquitectura/cont_02_administracion_organizacional.md).

## CHG-291 — continuar en Local

- Usuario corrigió «QA» por «Local». La promoción/publicación descrita en CHG-290 deja de ser tarea activa; no pedir otra autorización de QA ni publicar el candidato sin nueva solicitud.
- Local funcionando desde el workspace original en http://127.0.0.1:4173, con siete APIs, PostgreSQL 0037 y Firebase Emulator demo-erclave. Usar las credenciales demo locales definidas por el script canónico; no cuentas QA.
- Nota histórica CHG-291: aquel arranque no implementó CONT-02. APIs/UI y autoridad se completaron posteriormente en CHG-292; Centros de costos/Accounting siguen pendientes.
- Candidato aislado 2a91d19 preservado para referencia; las pruebas de disponibilidad Local no cierran UAT QA ni revisión de manuales.

## CHG-290 — siguiente paso de release

Candidato CONT-01 validado en .local/qa-cont01; pendiente publicar rama/PR/fusión y gates según la guía. Confirmar disponibilidad/SHA actual de las siete APIs (500/503 observado). Resolver explícitamente la configuración obligatoria del pipeline, que modifica catálogo global, permiso Owner en todos los tenants y configuración del demo, o preparar un corte condicional. No ejecutar backfill QA ni promover el working tree completo. Plan: [release CONT-01](../../operaciones/release_qa_20260923_cont01.md).

## CHG-289 — referencia histórica del corte siguiente

- CONT-00 resuelto; CONT-01 implementado Local en `20260922_0037`. No volver a preguntar cardinalidad, dueño del libro, obligatoriedad del Centro de costos o moneda inicial. Las propuestas de múltiples Emisores por Sociedad y libro por Emisor quedan descartadas.
- CONT-02 fue completado en CHG-292: APIs/formularios, moneda/referencias/estados y transición con revisión de cambios posteriores al snapshot.
- CONT-03/04: sesión/scopes y configuración por División. CONT-05: alta clara de Centros de costos en Administración, con catálogo técnico en Costing vía contrato. CONT-07/08: selección obligatoria según División activa, incluida asignación de artículos, y validación backend.
- CONT-12…14: libros por Sociedad; moneda base configurable inicialmente MXN, importes originales, tipo de cambio capturado e importes base congelados. No atribuir contabilidad o conversión implementada por existir `base_currency`.
- El tenant Local revisado está vacío de razones sociales/sucursales. La importación no vacía quedó probada con fixtures reversibles; cualquier futuro conjunto real requiere preview/hashes/resoluciones concretos. No crear datos de organización por inferencia ni promover QA automáticamente.
- Conservan estado los pendientes previos de navegador CHG-284/285, UAT QA y revisión visual de Word. El gate general sin DB no sustituye esas pruebas.

## Antecedentes resueltos de preparación CHG-286 a CHG-288

Las tres preguntas se resolvieron en CHG-289 y el primer corte persistente está implementado Local. El análisis y el preflight previos se conservan como evidencia; sus propuestas de cardinalidad/libro quedan sustituidas por [CONT-00](../../arquitectura/cont_00_decisiones_y_preflight.md). La secuencia restante vive en el [plan vigente](../../arquitectura/plan_preparacion_contabilidad.md).

## CHG-285 — cierre de revisión transversal

- Ejecutar el caso Playwright agregado para referencias históricas de Cliente y Cotización cuando el stack Local aislado esté activo; no atribuirle resultado antes de ejecutarlo.
- Diseñar catálogos fiscales de régimen, país y uso CFDI junto con factura/XML y cuentas por pagar. No agregar listas parciales antes de definir autoridad, vigencia y reglas fiscales.
- Resolver la semántica de categoría, centro de costos y área responsable de Producto/Servicio con negocio antes de convertirlos en catálogos.

## CHG-284 — cierre funcional de catálogos de Proveedor

- Ejecutar el caso Playwright de alta/edición con catálogos dinámicos cuando el stack Local aislado esté levantado; el intento actual se detuvo en preflight y no produjo resultado funcional.
- Antes de promover, probar en QA con rol de Compras que un código activo nuevo aparece, uno inactivo no se ofrece en alta y un valor histórico se conserva al abrir edición. Requiere candidato y autorizaciones de release independientes.
- No quedan cambios de datos ni migraciones asociados a este corte.

## CHG-283 — aplicar el piloto sin sobrecargar la captura

- Producto/Servicio: decidir con negocio qué campos deben exigirse al crear, cuáles son opcionales o derivados y si `Responsable` significa área. No cambiar contrato, persistencia ni textos antes de resolver esa semántica.
- Proveedor: cobertura fija resuelta en Local por CHG-284. La certificación de navegador y QA permanece en el bloque anterior; no reabrir la implementación por la lectura histórica del piloto.
- Ejecutar el nuevo resumen local en sesiones futuras y registrar observaciones UAT con ambiente, SHA y evidencia; la matriz QA conserva sus resultados hasta que se ejecuten casos completos.
- La terminal actual carece de Node/npm estándar. El gate equivalente `tools/verify.js` aprobó con el runtime JavaScript de VS Code; para sesiones futuras conviene disponer de Node/npm estándar y no depender de esa vía excepcional. Las 58 integraciones PostgreSQL omitidas en esta corrida no se atribuyen a este cambio documental.

## CHG-282 — cierre solicitado el 20 de septiembre

- CHG-281: validación Local completada; preparar candidato y promoción QA solo después de documentar el resultado de la prueba autenticada de OP-000003 y revisar el delta frente al SHA QA vigente. Cada gate del pipeline conserva su autorización independiente.
- Documentación: revisar visualmente portada, tablas, listas, saltos y encabezados de los siete manuales Word y la guía Word; corregir y regenerar cualquier defecto antes de distribuirlos. La publicación documental sigue pendiente y no equivale a despliegue de runtime.
- Limitación de esta revisión: no hubo render automatizado disponible, Word COM devolvió `0x80070520` y el primer DOCX estaba bloqueado por otro proceso. No se afirma aprobación visual ni estructural nueva de los ocho archivos.

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

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.

Pendientes de release: UAT del tester, bucket privado dedicado con lifecycle365d/versionado y soft-delete desactivados, política de no respaldar adjuntos más allá de su retención y promoción gobernada. No hay escrituras QA. Las55 integraciones generales previas siguen pendientes; este corte prueba DB/archivos de evidencia de forma focalizada.


## Margen esperado sin tope CHG-273

CHG-273 implementado y migrado solo Local. Pendientes: aceptación del tester y promoción QA autorizada, incluyendo migración0035 antes de exponer la captura sin tope. Las 55 integraciones generales omitidas en CHG-272 no se dan por ejecutadas: este corte sí verifica PostgreSQL real específicamente para margen y reversa. CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.


## Cierre y aceptacion de formularios CHG-272

Cierre tecnico completado: 174 pruebas browser aprobadas (98 offline, incluidos 14 Backoffice; 22 MAIN y 54 regresion), documentacion/trazabilidad, skill, validate y `verify` (262 backend, 55 omitidas sin DB; sintaxis 79). Las integraciones omitidas no se declaran ejecutadas. No quedan gates pendientes de ejecucion de CHG-272.

- Ejecutar UAT del tester y capturar respuesta estructurada/correlacion para identificar la causa exacta del incidente original de Movimientos; no asumirla por la captura.
- Ampliar evidencia negativa de negocio por cada consumidor que se ajuste. Las 54 variantes registradas demuestran wiring, no prueba exhaustiva de todas sus reglas/transiciones.
- Promocion QA y actualizacion de manuales tras release, exclusivamente bajo autorizacion y pipeline; CHG-272 esta solo Local y CHG-271 se preserva como manual de QA vigente.

Detalle, comandos y limites: `docs/auditorias/formularios_feedback_2026-09-13.md`. Los pendientes anteriores no se cierran por este cambio de feedback.

## Manuales y guía del tester CHG-271

CHG-271 sincroniza los siete manuales funcionales Markdown/Word y la guía de pruebas con QA `b63cdad`, revisión documental 2026-09-10. Entrega: `docs/qa/ENTREGA_TESTER.md`; generación reproducible de tablas y procedimientos mediante herramientas documentales. No cambia runtime, contratos, migraciones, datos, permisos ni despliegues. No publica documentos en GitHub.

Incidencia identificada por revisión de código: la bandeja para solicitar sobrantes de Mantenimiento busca `.submodule-screen`, ausente en su render; confirmar/corregir acceso por el agente técnico de Mantenimiento y QA. No se declara disponible el recorrido completo desde pantalla. Compra directa soportada por API pero no expuesta en alta de órdenes de la UI. Ambos límites constan en manuales/guía. UAT autenticada continúa pendiente del tester.


## Estado vigente tras release QA CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff vigente: `docs/contexto/REANUDACION_CHG269.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.

Las notas de preparación y cortes anteriores que siguen son evidencia histórica; no deben disparar un release duplicado.


## Promoción QA en preparación CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Cierre Local CHG-268

Reserva MTO-000001 recuperada y fallo Decimal corregido. Pendientes: confirmación física por Almacén cuando entregue, aceptación manual y promoción gobernada a QA. Reintentos automáticos siguen fuera de alcance; las fallas de existencia/dependencia conservan recuperación manual. Informe: `docs/auditorias/recuperacion_refacciones_2026-09-08.md`.


## Alcance posterior a CHG-264

Entregas parciales elegidas, rechazo de la solicitud productiva, selector de receptor diferente al responsable quedan pendientes. Antes de promocion revisar reservas historicas vencidas e intentos anteriores con respuesta incierta; no se reactivan ni compensan por inferencia. El callback de servicios comerciales Sales a materiales sigue fuera de alcance. Evidencia: `docs/auditorias/materiales_produccion_movimientos_2026-09-08.md`.

## Alcance posterior a la entrega de refacciones CHG-263

- Entregas parciales elegidas por el almacenista y aprobacion separada de la entrega quedan fuera de este corte; la confirmacion actual entrega la solicitud completa.
- Antes de promover, revisar reservas historicas con vencimiento: no reactivar stock expirado. Las solicitudes reservadas sin entrega pueden cancelarse y solicitarse nuevamente; movimientos ya emitidos conservan su historia.
- Operaciones heredadas de entrega con error/resultado incierto requieren revision por Almacen; no se compensan ni se libera la maquina por inferencia. Los reintentos actuales preservan partidas ya confirmadas y claves Inventory.
- La bandeja usa limit/offset; carga sostenida, cursor estable bajo cambios concurrentes y aprobacion QA siguen pendientes.

Ultima actualizacion: 2026-09-07.

## Cobertura posterior a auditoria CHG-262

La auditoria Local de coherencia frontend/backend y sus correcciones estan documentadas en `docs/auditorias/frontend_backend_2026-09-07.md`. No quedan abiertos los 17 grupos de defectos reproducidos en ese corte. Mantener las regresiones de campos/roles al agregar flujos; la cobertura combinatoria completa de perfiles, el volumen y las fallas distribuidas no se sustituyen por esos tests. Los cambios Local no se han promovido a QA.

## Validacion del release QA

0. Completar la matriz UAT del SHA QA `a119ddf5e8d42376b8557b234e15e3681b19c2a7`: permisos, aislamiento entre tenants, dependencias modulares, Compras, Mantenimiento, referencias, reservas/consumos, recepciones, capacidad, valuacion, concurrencia, proteccion de datos e idempotencia.
1. Repetir en QA el onboarding con un tenant ficticio y confirmar recepcion del correo Firebase, incluido folder de spam. Despues validar eliminacion, `firebase_identity_cleanup` y que el tenant deje de aparecer.
2. Diseñar una reconciliacion durable/outbox para invitaciones o limpiezas Firebase pendientes; la respuesta explicita evita el falso fracaso, pero no sustituye un reintento persistente si el cliente pierde la respuesta.
3. Comprobar que el administrador allowlisted accede a Backoffice mientras un owner ordinario conserva `403`, sin persistir tokens ni contraseñas.
4. Comprobar con usuarios de tenants distintos que los siete modulos seleccionan el tenant desde membresias, recargan datos de Cloud SQL y no muestran KPIs/transacciones simuladas; los modulos planeados permanecen inactivos.

## Prioridad siguiente

0. Siguiente evolucion de Mantenimiento tras CHG-257: reintento automatico programado, participantes secundarios y adjuntos; despues abordar preventivos y activos generales. Los reportes operativos basicos de ordenes, indisponibilidad, refacciones y tiempos ya quedaron cerrados.
0.1. Siguiente evolucion de Compras: division/adjudicacion de partidas de una requisicion entre varios proveedores, reintento automatico programado de recepciones `needs_reconciliation` y paginacion server-side antes de promover a QA. CHG-259 ya prueba la recuperacion parcial y corrige partidas sin respuesta; CHG-255 permite servicios sin Inventory. No existe aun adjudicacion parcial, factura ni cuenta por pagar.
1. Siguiente corte de Ventas despues de CHG-255: devoluciones, facturacion/cobranza y callback de Production que convierta solicitudes en partidas entregables y reporte costo real. La ejecucion/aceptacion de servicios ya tiene orden propia; la recepcion de producto terminado permanece cubierta por CHG-222.
2. Evolucionar la paginacion visual transversal de CHG-259 a paginacion contractual con cursor en Clientes, Cotizaciones, Pedidos, Ordenes de servicio y Entregas antes de volumen productivo; el limite preventivo de API permanece en 200.
3. Repetir en Local aislado las dos entradas funcionales que antes quedaron solo en `localStorage` y confirmar en navegador que Movimientos, Inventario y Kardex reflejan el mismo saldo; no copiar esos datos a QA.
4. Completar el catalogo de Articulos para escala server-side; actualmente el corte escalable se concentro en balances de Inventario.
5. Decidir funcionalmente si Categoria se convierte en catalogo jerarquico antes de modelar IDs, padres o migraciones.
6. CHG-264 separa consumo e inicio: pruebas PostgreSQL cubren entrega parcial, bloqueo de inicio/cancelacion, recuperacion y lock; completar carga sostenida y cortes de red reales antes de QA.
7. Capturar y validar areas/puestos QA solamente con datos ficticios y autorizacion explicita; `hr-service` y el entitlement ya estan desplegados, pero sus catalogos permanecen vacios.
8. Paginar el catalogo de articulos elegibles para recetas y exponer disponibilidad agregada server-side para volumen mayor a 200 combinaciones articulo/almacen.
9. Ejecutar la prueba funcional del editor de permisos en QA tras renovar la sesion y confirmar persistencia, concurrencia y rechazo de grants prohibidos.
10. Diseñar la recepcion de merma desde Produccion. La recepcion de producto terminado permanece confirmada por Almacenes mediante `inventory.finished_goods_receipt.receive`; CHG-236 separo esa autoridad de los movimientos generales.
10.1. Evaluar un borrador de orden de Produccion separado de la liberacion. En el runtime vigente, crear la orden valida, reserva y libera en una sola operacion protegida por `production.order.release`.
11. Evolucionar el calendario productivo base lunes-viernes a calendarios tenant configurables con turnos, festivos, ausencias y excepciones por mantenimiento. CHG-241 ya distribuye y compromete capacidad multi-dia; Mantenimiento correctivo aun no modifica automaticamente esa capacidad planeada.
12. Implementar PDF de Pedido y remision/Entrega usando `document.template`, con snapshot o artefacto inmutable; mover el logo a object storage antes de promover la plantilla a QA.
13. Cuando Compras sea operativo, definir la politica de valuacion que actualizara el costo unitario base del articulo desde recepciones u ordenes de compra; por ahora permanece como captura manual de Inventory.
14. Integrar consumidores externos con la reserva central de folios o exigir una credencial interna de confianza; la UI Local ya usa el catalogo, pero los contratos propietarios conservan compatibilidad con clientes API que proporcionan un codigo valido.
15. Estandarizar en backend todas las excepciones de validación y errores inesperados con la envoltura `ErclaveError`; propagar `X-Correlation-Id` entre servicios, exponerlo en CORS y declarar respuestas de error comunes en OpenAPI. CHG-251 ya evita exponer mensajes técnicos en la UI y conserva la referencia disponible, pero no cambia los contratos HTTP de los servicios.
16. Diseñar el modulo Reportes para analitica transversal: XLSX con formato, PDF, constructor, cruces entre propietarios, graficas, vistas guardadas, programacion y distribucion. CHG-257 conserva reportes operativos simples en el servicio propietario y oculta su formato tecnico en la interfaz.

## Fuera del alcance actual

- Crear infraestructura de Produccion antes de autorizacion expresa; los objetivos futuros son RPO 15 minutos y RTO 2 horas.

- Lotes y canales de reserva distintos de ordenes de Produccion o pedidos de Ventas.
- Lotes, series, cuarentena, inventario bloqueado y en transito.
- Carga de datos funcionales, dummy o de volumen en Inventory/RH sobre QA sin una autorizacion especifica.
- Despliegue de frontend o servicios fuera del pipeline y sus aprobaciones protegidas.

## Regla de mantenimiento

Mover un pendiente a `ESTADO_ACTUAL.md` solo cuando este implementado, probado y registrado en `TRAZABILIDAD.md`. Eliminar pendientes obsoletos explicando la decision en trazabilidad.


## Pendientes posteriores a CHG-265

Conectar automáticamente Ventas → Producción → recepción/entrega y materiales de servicios comerciales se mantienen planned. También devoluciones comerciales a proveedor/cliente, entregas productivas/refacciones parcialmente elegidas, aprobación separada, reintentos programados y asignación de usuarios por almacén. Las devoluciones de sobrantes de Producción/Mantenimiento ya tienen solicitud y confirmación por Almacén en Local. No confundirlas con devoluciones comerciales ni merma. Validar volumen y fallos prolongados antes de promoción; QA no recibe este cambio.


## Ajustes UAT Local CHG-266

Los cuatro hallazgos UAT de proveedores, requisiciones, riel de Órdenes y acceso al ciclo de cotizaciones están corregidos en Local. Resta aceptación manual del usuario; no hay autorización de promoción QA. La configuración de permisos del ambiente remoto debe evaluarse dentro de un release autorizado, sin copiar datos Local ni conceder permisos a roles por inferencia.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Solicitudes compactas Local CHG-267

La presentación compacta de solicitudes en Movimientos está implementada en Local. Pendiente aceptación manual del usuario. QA no recibe código ni datos por inferencia; no se amplía este corte a permisos o flujos de almacén.

Evidencia y APIs: `docs/auditorias/almacen_solicitudes_desplegables_2026-09-08.md`.
