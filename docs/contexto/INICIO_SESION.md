# Inicio de sesion ERClave

## Punto vigente · CHG-335 · plan QA listo para revisión

Continuar desde [acta](../operaciones/paridad_local_qa_20261018.md), [estado](ESTADO_ACTUAL.md) y [pendientes](PENDIENTES.md). Ocho runtimes preparados, frontend inmutable, configuración preservadora, readiness de esquema y guard organizacional READ ONLY. Replay entre actores y recuperaciones parciales corregidos/reprobados Local; consultar evidencia por variante, sin inventar aceptación histórica CC-19 o UI no ejecutada. El usuario eligió preparar estructura sintética QA **para revisión antes de aplicar**; [plan](../../infra/qa/synthetic-organization-plan.json) y monedas MXN/USD aún propuestas. No escribir datos QA ni IAM, PR/merge o gates sin la autorización correspondiente de erclave-qa-release. QA observado sigue e57237f. Fixtures se limpian exclusivamente por IDs propios, sin rebobinar folios ni borrar historia.

## Candidato para Git autorizado · CHG-334

Publicar el candidato Local en origin/agent/chg-278-qa-release-record con las correcciones CHG-332/333 y protección de bytes de fuentes manuales mediante .gitattributes. Antes de commit comprobar sourceSha256 contra blobs del índice Git, no solo contra el workspace. No hay autorización de merge, PR ni promoción derivada de esta publicación. Reanudar después por CC20-02; consultar estado efectivo del remoto.

## Reanudar en CC20-02 · CHG-333 · 2026-10-18

CC20-01 pasa Local (CHG-332) y sus tres pendientes quedaron corregidos Local en [CHG-333](../operaciones/correcciones_cc20_01_20261018.md). Antes de continuar comprobar servicios efectivos y tenant demo. Admin Local se reinició con código nuevo; dos identidades de regresión quedaron sin membresía y sin cuenta Firebase, con registro global deshabilitado y auditoría conservada. Manuales sin cambio semántico/Word; trazabilidad normalizada hasta CHG-333. No hay QA ni migración nueva; Accounting apagado.

## Reanudación después de CC20-01 · 2026-10-18

[CC20-01 pasa Local](../operaciones/cc20_01_local_20261018.md) con 21 comprobaciones integradas y UI de preferencia revocada. No repetirlo por la nota preparatoria CHG-327; continuar CC20-02 tras comprobar servicios/fixtures. Usuario controlador sin cambios; tres membresías de ensayo deshabilitadas, sin roles, y tres órdenes propias canceladas conservadas con auditoría. INC-CC20-01-DELETE-01 corregida Local y correlativos normalizados en CHG-333. El arranque detecta Node/Firebase instalados fuera de PATH y usa configuración CLI bajo .local; revalidar disponibilidad efectiva. Accounting apagado, CC-19 real y QA separados.

## Punto documental CHG-331 - 2026-10-14

Los siete Word fueron regenerados y cotejados con sus fuentes Markdown, renderizados y revisados visualmente (50 páginas). El registro contiene las huellas nuevas. Siguen siendo candidatos del alcance Local; CC-20, CC-19 real y promoción QA mantienen sus propios criterios. CHG-330 siguiente describe el bloqueo anterior ya resuelto.

## Punto documental CHG-330 - 2026-10-14

La revisión previa a Git corrigió el manual Markdown de Administración, el diagrama a head Local `20261014_0062` y la trazabilidad CHG-322. Siete fuentes de manual posteriores a sus Word mantienen `validate:documentation` fallido por paridad; no renovar hashes sin regeneración, cotejo y revisión visual. No se publicó ni desplegó el árbol. Consultar ESTADO_ACTUAL, PENDIENTES y REGISTRO de manuales antes de preparar un candidato.

## Punto vigente CHG-329 - selector organizacional Local - 2026-10-14

El selector de Sociedad/División de la barra superior se separó del buscador genérico que se comprimía y recortaba. En Local se observó la lista de 3 Divisiones, se cambió a la Sociedad demo USD, persistió tras recarga y Escape cerró el menú. Centro de costos sigue siendo catálogo por División, sin selección global. Sin cambios de API, DB o QA. CHG-328 siguiente conserva la preparación de datos demo; CC-19 real y CC-20 siguen abiertos.

## Punto vigente CHG-328 - demo sintético Local - 2026-10-14

El tenant demo Local `ten_739ee59d765d5e14818674800d` tiene 2 Sociedades (MXN/USD), 3 Divisiones y 3 Centros de costos activos después de altas por APIs Admin/Costing. Los IDs y excepciones están en `.local/cc19-demo-local-manifest.json` y `.local/cc19-demo-*.csv` del workspace actual (ignorados por Git). Treinta y ocho registros legacy siguen sin contexto o División comprobable; no se hizo backfill ni se activó Accounting. CC-19 real y CC-20 integrado siguen abiertos; consultar ESTADO_ACTUAL y PENDIENTES. El punto CHG-327 siguiente describe el estado previo.

## Punto vigente CC-20 - CHG-327 - 2026-10-14

El usuario pidió aplicar CC-20 para probar después en Local. [Procedimiento y matriz de 16 casos](../operaciones/cc20_aceptacion_integrada_local.md) preparados; todos Por ejecutar. Antes de la sesión verificar árbol/DB/tenant/servicios, crear sólo fixtures sintéticos por APIs dueñas en tenant autorizado y conservar evidencia por caso. No correr la suite general que crea tenants temporales sin autorización propia. Accounting apagado, CC-19 real separado; no QA ni cierre de CC-20 por esta preparación. CHG-326 siguiente conserva el punto anterior.

## Punto vigente CC-19 - CHG-326 - 2026-10-14

El usuario indico que aun no dispone de datos/equivalencias reales y pidio una guia y diagrama de configuracion contable opcional. Se preparo [CC-19 mapeos y configuracion](../arquitectura/cc19_mapeos_y_configuracion_contable.md); no se hizo backfill ni se cerro CC-19. Retomar con padron de Emisor/Sociedad/Division y equivalencias documentadas por ID. Accounting sigue planned/apagado; la operacion no depende de configurarlo. CC-21 continua implementado Local, CC-20 pendiente. El punto CHG-325 siguiente es historico respecto de esta preparacion.

## Reanudacion vigente - CC-21 - CHG-325 - 2026-10-14

CC-21 implementado solo en Local: costo confirmado de Production por Division y moneda base de Sociedad, vista previa de Sales con tasa explicita, snapshot final al aprobar cotizacion y herencia al pedido. Si falta costo o tasa confiable, la aprobacion continua con estimado y margen nulos. Migracion `20261014_0062` up/down/up en Local autorizado; no QA ni Accounting. Consultar [contrato](../arquitectura/cont_08_costo_estimado_cotizaciones.md), [control](CONTROL_CONTABLE.md), [estado](ESTADO_ACTUAL.md) y [trazabilidad](../../TRAZABILIDAD.md). Siguientes trabajos: datos reales CC-19 y aceptacion integrada CC-20. La revision CHG-324 siguiente es historica.

## Revision CC-21 - CHG-324 - 2026-10-14

La brecha de costo estimado de cotizaciones se formalizo como CC-21. Revision documental completa; implementacion pendiente. `standard_cost` global de Production carece de moneda/Sociedad y Sales lo compara con el precio de cotizacion y copia al pedido. El usuario confirmo aprobar con costo/margen estimados nulos si faltan costo o tasa confiables. Consultar [revision](../arquitectura/cont_08_costo_estimado_cotizaciones.md), [control](CONTROL_CONTABLE.md) y [pendientes](PENDIENTES.md). No hubo cambio de runtime ni ambiente CHG-324; CC-18 sigue Local, CC-19/20 pendientes.


## Reanudacion vigente - CHG-323 - 2026-10-14

CC-18 implementado solo en Local para folios faltantes de RH, Inventory, Purchasing y Maintenance. Usuario confirmo codigo estable derivado del origen para movimientos automaticos Inventory cuando `inventory.movement` esta en modo manual. Migracion `20261014_0061` up/down/up Local; no QA ni Accounting. Continuar con revision de costo estimado, mapeo de datos CC-19 y aceptacion CC-20. Consultar CONTROL_CONTABLE, ESTADO_ACTUAL y TRAZABILIDAD. El apartado CHG-322 siguiente es historico.

## Reanudacion anterior - CHG-322 - 2026-10-14

El usuario reanudo el trabajo con CC-17 y confirmo congelar presentacion al aprobar la cotizacion y al liberar la orden de produccion. El corte esta implementado Local con migracion `20261014_0060`; consultar [CONTROL_CONTABLE](CONTROL_CONTABLE.md), [ESTADO_ACTUAL](ESTADO_ACTUAL.md) y [plantillas](../arquitectura/plantillas_documentales.md). La pausa CHG-321 siguiente es historica. Proximos trabajos: CC-18, costo estimado, datos CC-19 y aceptacion CC-20. No hubo promocion QA ni activacion Accounting.

## Reanudación vigente · CHG-320 · 2026-10-12

**Pausa solicitada · CHG-321 · 2026-10-12.** El usuario dejó expresamente pendiente el trabajo posterior a CC-16. No hay un corte CC-17/18/19/20 en ejecución ni se inició la revisión del costo estimado. Al retomar, comenzar por [PENDIENTES](PENDIENTES.md) y [CONTROL_CONTABLE](CONTROL_CONTABLE.md), comprobar `git status`, HEAD, head Alembic, servicios y ambiente efectivos. El árbol compartido permanece sin commit; no repetir la migración Local0059 ni sus helpers de ensayo. La siguiente implementación propuesta es CC-17, después CC-18 y la revisión monetaria de cotizaciones; CC-19 requiere datos y mapeo reales explícitos, y CC-20 aceptación integrada con evidencia por ambiente. Esta secuencia no autoriza QA, migración de datos reales ni Accounting.

**Evidencia conservada del último corte:** CHG-320 CC-16 implementado Local, Maintenance 50 y RH/Production 123 pruebas con PostgreSQL/API sin omisiones, navegador 271 con APIs interceptadas, y `npm run verify` 738 aprobadas/233 omitidas/1 advertencia en la corrida sin base configurada. Migración `20261012_0059` up/down/up sólo Local. [Trazabilidad](../../TRAZABILIDAD.md) y [contrato CC-16](../arquitectura/cont_08_mantenimiento_contexto.md). Quedan además la revisión visual del Word de Mantenimiento y la aceptación transversal CC-20; la paridad estructural del Word no sustituye esa revisión.

CC-16 implementado Local: [Mantenimiento](../arquitectura/cont_08_mantenimiento_contexto.md) conserva contexto fijo de orden, técnicos y tarifas RH, costo de tiempos, alcance e idempotencia; preserva CC-14 y CC-15 [Purchasing](../arquitectura/cont_08_compras_contexto.md). Head verificado `20261012_0059`; migración aditiva up/down/up sin backfill en loopback5434 y tenant exclusivo. Pruebas PostgreSQL/API y navegador interceptado separadas de CC-20. No se promovió a QA ni se activó Accounting. Revalidar procesos al continuar.

Siguiente desarrollo CC-17/18 y revisión de costo estimado. Conservar CC-10/11/12/14/15/16 implementados. Datos CC-19 y aceptación transversal CC-20 siguen abiertos. Árbol preservado sin commit. Los apartados CHG-315/316 siguientes conservan historia de la pausa anterior. No repetir .local/chg319-migrate.py que esperaba0057.

[Portal documental](../INICIO.md) · [índice clasificado](../INDICE_DOCUMENTAL.md). CHG-311: antes de usar una fuente comprobar vigencia y ambiente; las exportaciones Word se rigen por REGISTRO.

## Punto de pausa anterior · 2026-10-08

Este es el punto de pausa de CHG-315/316. Último corte **CHG-315 implementado en Local**, conservando CHG-313/314, posterior a conciliación documental CHG-311; política monetaria CHG-309. Consultar [estado por ambiente](ESTADO_ACTUAL.md), [pendientes](PENDIENTES.md), [decisiones](DECISIONES.md) y [control contable por submódulo](CONTROL_CONTABLE.md). Las notas acumuladas se conservan en el [archivo histórico](historico/INICIO_SESION_PRE_CHG311.md); no son instrucciones acumulativas.

**Punto de pausa:** CC-12 implementado y recorrido HTTP Local real aprobado. Preservar conversión única, origen autenticado, recuperación, recepción y entrega/costo de [fabricación comercial](../arquitectura/cont_08_fabricacion_contexto.md). En esa pausa quedaba continuar CC-14/15/16; no reimplementar CC-10/11/12 ni el ciclo comercial. El agente técnico de Contabilidad custodia la matriz.


**Cierre antes de reiniciar:** CHG-315 registrado; verify aprobado (596 passed, 196 skipped por suite sin DB, 1 warning), 310 pruebas PostgreSQL/API focales aprobadas y HTTP completo con limpieza verificada. Navegador completo231 y focal final16 aprobados; revisión visual de Word pendiente por LibreOffice ausente. Archivos guardados sin commit; no hay migración ni ensayo en curso. Reanudar por este documento y comprobar procesos antes del arranque canónico.

**Decisión resuelta:** costos y tarifas de materiales, máquinas y mano de obra en moneda base de Sociedad. Otra moneda documental conserva original, convertido y tipo de cambio explícito; misma moneda usa 1. No reinterpretar historia ni preguntar nuevamente la política. Accounting permanece opcional y apagado para esta preparación. Las asignaciones de datos reales siguen pendientes.

## Pausa y cierre de la primera fase · CHG-316

El usuario pausa para reiniciar su computadora. **La fase de preparación y separación operativa con Accounting apagado sigue abierta; CC-12 sí está cerrado en Local.** No interpretar el cierre de fabricación como cierre de toda Contabilidad ni como autorización para habilitarla.

- **Implementación que estaba pendiente en CHG-316:** CC-14 (ahora implementado CHG-317); CC-15 Compras; CC-16 Mantenimiento; CC-17 identidad/configuración/impresión histórica; CC-18 consumidores restantes de folios. Conservar lo ya implementado en cada bloque y consultar el detalle en [CONTROL_CONTABLE](CONTROL_CONTABLE.md).
- **Revisión funcional pendiente:** costo estimado de cotización al extender la política monetaria; no darla por resuelta por cerrar fabricación o Servicios.
- **Datos y aceptación pendientes:** CC-19 estructura/asignaciones e históricos; CC-20 recorridos integrados, permisos, cruces de alcance, reintentos, monedas y preparación de QA. Revisión visual de Word pendiente según su registro.
- **Siguiente trabajo al volver:** comprobar contexto/árbol local y arranque aislado; revisar conjuntamente CC-14/15/16 y ejecutar el siguiente corte vertical con el dueño correspondiente. No repetir CC-10/11/12 ni sus migraciones de ensayo.

Criterios de cierre: completar las brechas funcionales anteriores permite declarar cerrada la implementación de esta fase; completar datos y aceptación permite declarar su cierre integral. El libro, eventos/integración contable futura y activación de Accounting conservan su propio alcance posterior en [CONTROL_CONTABLE](CONTROL_CONTABLE.md); esta pausa no los habilita.

## Secuencia de trabajo

1. Ejecutar `npm.cmd run session:context`; si Node/npm no están disponibles, `python tools/context_brief.py` y registrar la limitación.
2. Leer [AGENTS.md](../../AGENTS.md), los roles pertinentes de [AGENTES.md](../../AGENTES.md), las fuentes de contexto enlazadas arriba y [TENANTS.md](TENANTS.md).
3. Aplicar [gobierno_documentacion_viva.md](../arquitectura/gobierno_documentacion_viva.md), la ficha de [módulo](../../modulos/README.md) y sus contratos. Consultar historia sólo para el corte necesario, contrastándola con fuentes vivas.
4. Revisar `git status --short`: preservar cambios anteriores. HEAD/base y procesos se vuelven a comprobar, no se heredan de una nota.
5. Identificar dueño del dato, servicio, microfrontend, contrato, permisos y dependencias. Registrar `Agentes consultados`, cobertura real y criterios de aceptación.
6. Confirmar ambiente y `tenant_id` antes de escribir datos. Local aislado es PostgreSQL loopback `127.0.0.1:5434/erclave_local`, Firebase Emulator y APIs locales. Único tenant de ensayo autorizado: `ten_739ee59d765d5e14818674800d`.

## Reanudación técnica de Producción

Leer [preparación Production CHG-308](../arquitectura/cont_08_produccion_contexto.md), [contexto e intento durable](../../backend/services/production-service/app/order_context.py) y [migración 0050](../../backend/alembic/versions/20261007_0050_production_context.py). CHG-315 habilita fabricación dimensionada con prueba Sales y enlace durable; consultar el contrato de fabricación enlazado arriba.

El head Local documentado tras CHG-320 es `20261012_0059`; `20261012_0058` corresponde a CHG-319; `20261012_0057` corresponde a CHG-317; `20261008_0056` corresponde a CHG-315. Los ciclos0054/55 y0056 son evidencia previa sin backfill; no repetir el helper chg317-migrate.py que esperaba0056. Comprobar servicios y base después de un reinicio mediante el [arranque Local aislado](../../backend/scripts/start_local.ps1) y las [fronteras de ambientes](../arquitectura/fronteras_ambientes_local_qa_produccion.md). No asumir PIDs/servicios activos. Los helpers `.local/chg308-*.py` son evidencia de la sesión anterior, no un arranque completo; no repetir el helper de migración CHG-308 que esperaba 0049. No repetir ningún helper .local/chg315-migrate*.py: fue una prueba de esta sesión y no es un arranque. No sustituir Local apagado por recursos QA. CHG-312: el usuario autorizó posteriormente ExecutionPolicy Bypass sólo para el proceso de start_local.ps1; arranque canónico y smoke HTTP de lectura aprobados (chg312-start-local.log, chg312-http-smoke.log). Ocho APIs, frontend y Emulator comprobados; seeds locales de permisos/demo ejecutados. En CHG-312 no había Divisiones autorizadas. Smoke CHG-314 después de recargar Production/Inventory/HR/Sales: una División autorizada, consultas200 sin recursos elegibles y contratos nuevos presentes; CHG-315 añadió y aprobó el ciclo HTTP real con recursos sintéticos, recepción y entrega (chg315-http.log), sin conservar fixtures. No cambia la política permanente ni autoriza QA/Producción.

Conservar la evidencia CHG-308 en [trazabilidad](../../TRAZABILIDAD.md): 231 pruebas focales; verify 532 aprobadas/152 omitidas; migración y smoke Local registrados. Son resultados de ese corte, no pruebas nuevas de esta sesión ni UAT de fabricación.

## Cierre obligatorio

Aplicar la matriz de gobierno, actualizar las fuentes realmente afectadas y registrar el corte en [TRAZABILIDAD.md](../../TRAZABILIDAD.md). Ejecutar `npm.cmd run validate:documentation` y `npm.cmd run verify`; cualquier check omitido o fallido se declara. Si cambia feedback, ejecutar `validate:error-feedback` y verificar ES/EN, severidad y restauración del estado rechazado. La entrega distingue APIs afectadas, pruebas nuevas de evidencia histórica, migraciones, seeds, datos y despliegues.

Una tarea documental no autoriza activar Accounting, levantar QA, promover, crear PR ni completar datos reales por inferencia. Los [handoffs históricos](historico/README.md) conservan memoria, pero este archivo dirige la sesión actual.
