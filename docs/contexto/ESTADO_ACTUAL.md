# Estado actual de ERClave

## Correcciones de paridad preparadas · CHG-335 · 2026-10-18

El corte Local incluye ocho runtimes en el pipeline (Costing básico), dependencias HTTPS completas, frontend construido una vez y verificado por bytes, readiness DB/head y guard operativo READ ONLY. La configuración conserva usuarios, membresías, perfil, roles personalizados y entitlements. Se corrigieron replay entre actores, intents parciales, retry de código manual y responsive; aceptación HTTP/Chrome real por variantes en [acta](../operaciones/paridad_local_qa_20261018.md). INC-CC20-13-ACTOR-01 está corregida y reprobada en Local. No confundir las variantes comprobadas con aceptación de históricos CC-19 sin procedencia ni UAT QA.

El usuario autorizó **preparar estructura sintética QA y revisar el plan antes de aplicarlo**: [propuesta](../../infra/qa/synthetic-organization-plan.json), un emisor, dos Sociedades MXN/USD propuestas, tres Divisiones y tres centros. Aún faltan baseline privado QA, confirmación de monedas y actores, identidad/variables y aprobaciones separadas de release. QA público observado mantiene siete APIs e57237fe90319f88e1db8ed8d2e686604d2d9c54; no se escribió ni desplegó QA. Accounting y analítica Costing apagados. Los apartados siguientes son cortes previos.

## Preparación de publicación Git · CHG-334 · 2026-10-18

El usuario autorizó subir el repositorio. El candidato conserva CHG-333 validado y añade .gitattributes para preservar los bytes de las fuentes de manuales vinculadas a huellas Word. Se detectó que seis fuentes coincidían con el registro en el workspace, pero sus blobs HEAD estaban normalizados a LF y no coincidían. El commit debe conservar sus bytes aprobados (sin cambio de texto ni Word); comprobar las huellas del índice Git antes de publicarlo. Destino: rama agent/chg-278-qa-release-record en origin. Workflows de despliegue manuales; publicar la rama no promueve QA. CC20-02–16 y CC-19 real mantienen sus pendientes.

## Tres correcciones Local cerradas · CHG-333 · 2026-10-18

`verify` y documentación aprobados: 751 pruebas backend aprobadas, 250 omitidas en la corrida general sin DB y una advertencia existente. Las regresiones focales con PostgreSQL/Emulator y UI se registran por separado en el acta.

INC-CC20-01-DELETE-01 corregida Local: retiro de membresía con auditoría preservada, limpieza Firebase posterior y reintento seguro; invitación/onboarding coordinados con el bloqueo de identidad. Dos manuales recuperaron paridad restaurando CRLF sin cambiar contenido/Word. CHG-323–331 sí existían: formato/posición normalizados; CC20-01 registrado como CHG-332. [Acta de correcciones](../operaciones/correcciones_cc20_01_20261018.md). Focal API91, PostgreSQL6, integración real16 y UI4 aprobadas. CC20-02–16 pendientes; CC-19 real y QA mantienen su alcance. Los apartados siguientes describen sus cortes previos.

## CC20-01 ejecutado Local · 2026-10-18

CC20-01 pasa en Local: 21 comprobaciones con Admin, orden Maintenance, PostgreSQL y Chrome/Firebase SDK reales. Revocación de División, comandos/replays, listado/CSV y preferencia local comprobados; Owner original preservado. [Acta y límites](../operaciones/cc20_01_local_20261018.md). CC20-02–16 siguen por ejecutar. Incidencia auxiliar observada entonces y corregida en CHG-333: DELETE de usuario con auditoría devolvía 500 tras eliminar su identidad Firebase; membresías propias deshabilitadas y sin roles, órdenes propias canceladas. CC-19 y QA sin cambios. Las notas CHG siguientes conservan antecedentes.

## Cierre documental Local para Git - CHG-331 - 2026-10-14

Se regeneraron los siete manuales Word desde sus fuentes vigentes, se comprobó su paridad textual/ZIP/XML/tablas y se revisaron visualmente las 50 páginas renderizadas. Sus huellas se renovaron en el registro documental. Son exportaciones candidatas Local; CC-20 integrado, CC-19 con datos reales y promoción QA permanecen pendientes. La nota CHG-330 siguiente corresponde al estado previo.

## Revisión documental para Git - CHG-330 - 2026-10-14

La fuente Markdown de Administración ya explica el selector de Sociedad y División comprobado en Local. El diagrama backend refleja el head Local `20261014_0062` y la trazabilidad CHG-322 contiene los campos exigidos. El validador documental sólo mantiene siete discrepancias de paridad fuente/Word de cambios Local acumulados; los DOCX siguen clasificados como exportaciones pendientes y no se deben distribuir como edición vigente. No hubo commit ni publicación de rama por esta revisión.

## Selector de contexto corregido en Local - CHG-329 - 2026-10-14

La barra superior permite cambiar Sociedad/División con una lista legible y accesible, sin el buscador genérico comprimido. El cambio consulta `GET /v1/session/context?division_id=...` y guarda la preferencia sólo tras confirmación. Se comprobó en navegador Local con el tenant demo: lista de 3 Divisiones, cambio entre Sociedades, conservación tras recarga y Escape. Centro de costos permanece por División/flujo, no como preferencia global. Sin cambio de API, datos ni QA.

## Configuración sintética Local para CC-19/20 - CHG-328 - 2026-10-14

En el tenant demo `ten_739ee59d765d5e14818674800d` de PostgreSQL Local `127.0.0.1:5434/erclave_local` se crearon por APIs dueñas un Emisor, una Sociedad USD, dos Divisiones y tres Centros de costos activos; se conservaron el Emisor, Sociedad MXN y División existentes. La estructura resultante es 2 Sociedades, 3 Divisiones (dos de la Sociedad MXN y una de la USD) y un Centro por División. Los IDs y equivalencias de esta estructura sintética están en `.local/cc19-demo-local-manifest.json` y `.local/cc19-demo-estructura-local.csv`; son artefactos locales ignorados por Git. Un inventario de solo lectura dejó 38 registros legacy sin contexto/División comprobable en `.local/cc19-demo-excepciones-local.csv`. No se hizo backfill, ni se asignaron maestros o documentos históricos, ni se configuraron cuentas o libros: Accounting sigue planned/apagado. CC-19 de datos reales y CC-20 de aceptación integrada siguen abiertos. No hubo acceso a QA/Producción.

## Preparacion CC-20 - CHG-327 - 2026-10-14

[Matriz y procedimiento de aceptación Local](../operaciones/cc20_aceptacion_integrada_local.md) preparados con 16 casos integrados, precondiciones, evidencia y criterio de cierre. El usuario pidió probar después: ningún caso se ejecutó ni se marcó aprobado en este corte. CC-20 sigue pendiente de ejecución Local; QA conserva su propia matriz. CC-19 continúa sin mapeo real y Accounting apagado.

## Preparacion CC-19 - CHG-326 - 2026-10-14

El usuario confirmo que aun no dispone de la estructura ni del mapeo real. Se preparo [la guia y diagrama](../arquitectura/cc19_mapeos_y_configuracion_contable.md) de equivalencias operativas y configuracion futura de cuentas. CC-19 permanece abierto: no hubo backfill, migracion nueva, escritura de datos, acceso QA ni activacion de Accounting. La operacion debe seguir funcionando sin el modulo contable; el estado implementado Local de CC-21 permanece como se describe abajo.

## Implementación CC-21 - CHG-325 - 2026-10-14

CC-21 implementado solo en Local: Production confirma costo estimado unitario por Division en moneda base de Sociedad y Sales calcula vista previa verificable en borrador/envio, congela al aprobar y copia el snapshot al pedido. Tasa explicita cuando la moneda documental difiere; faltantes permiten aprobar con costo/margen nulos. Migracion aditiva `20261014_0062` up/down/up en PostgreSQL Local, sin backfill. Reportes y UI distinguen historia sin procedencia. Accounting apagado; sin QA ni aceptacion integral CC-20. Pendientes CC-19, CC-20 y Word.

## Estado anterior - CHG-324 - 2026-10-14

Revision CC-21 documentada: el costo estimado de cotizaciones aun no tiene procedencia monetaria confiable y puede compararse indebidamente con el precio documental. El usuario confirmo que la aprobacion debe permitirse con costo/margen estimados nulos cuando falten costo o tasa confirmados. No hubo cambio de runtime, migracion ni ambiente en CHG-324; CC-21 sigue pendiente de implementacion. CC-18 permanece implementado Local y CC-19/20 pendientes.

## Estado anterior - CHG-323 - 2026-10-14

CC-18 implementado solo en Local: Admin asigna folios de Puestos RH, movimientos Inventory, proveedor/requisicion/orden/recepcion Purchasing y orden Maintenance. Modo administrado o manual por tipo; los movimientos internos sin formulario en modo manual usan un codigo estable derivado del origen. Los codigos historicos no se renumeran. Migracion `20261014_0061` up/down/up en PostgreSQL Local. Accounting sigue apagado. No hubo promocion QA ni aceptacion integral CC-20. Continuan revision del costo estimado y datos CC-19.

## Estado anterior - CHG-322 - 2026-10-14

CC-17 implementado solo en Local para la impresion de cotizaciones y ordenes de produccion, con presentacion Admin efectiva por Division y snapshot al aprobar/liberar. Migracion `20261014_0060` up/down/up en PostgreSQL Local. Sin QA, despliegue, datos reales ni activacion de Accounting. CC-18, revision de costo estimado, CC-19 y CC-20 continuan pendientes. La pausa CHG-321 descrita abajo es antecedente y fue levantada por la peticion de implementar CC-17.

## Corte histórico conciliado · 2026-10-12

**Pausa CHG-321:** por solicitud del usuario se detiene el trabajo tras CC-16 Local. CC-17/18, revisión del costo estimado y CC-19/20 permanecen abiertos; [INICIO_SESION](INICIO_SESION.md) conserva el punto exacto de reanudación. No hubo promoción ni activación contable por esta pausa.

**CHG-320 · CC-16 implementado Local:** contexto fijo de orden Maintenance, técnico RH por División y costo laboral conservado; alcance documental/reportes e integración de máquina reforzados. Migración `20261012_0059` up/down/up comprobada. Maintenance50, RH/Production123 y navegador271 aprobadas sin omisiones; verify final aprobó validadores/compilación y backend738 aprobadas/233 omitidas/1 warning sin DB (chg320-verify-final.log). Sin promoción QA. [Contrato y evidencia](../arquitectura/cont_08_mantenimiento_contexto.md). Conserva todos los cortes cerrados siguientes.

Corte anterior conservado: **CHG-319**, CC-15 implementado Local: requisición/OC por División, condiciones explícitas del proveedor, herencia a recepciones incluidas de servicios, alcance e idempotencia. Conserva CC-14 CHG-317 y fabricación CHG-315. La fase sigue abierta: CC-17/18, costo estimado, datos CC-19 y aceptación CC-20. [Punto de reanudación](INICIO_SESION.md).

[Contrato y evidencia de Compras](../arquitectura/cont_08_compras_contexto.md). PostgreSQL Local y pruebas API; navegador interceptado separado de aceptación integrada. Head `20261012_0059`, Accounting apagado.

| Ambiente | Estado documentado | Evidencia y límite |
|---|---|---|
| Local | Árbol sobre HEAD `213f75c` con cambios anteriores sin commit; head Alembic `20261012_0059`. Orden manual dimensionada y moneda de servicios implementadas en Local; fabricación Sales CC-12 implementada y ensayada entre servicios reales. | [CONTROL_CONTABLE](CONTROL_CONTABLE.md), [Production CHG-313](../arquitectura/cont_08_produccion_contexto.md), migraciones y trazabilidad. Volver a comprobar Git y DB antes de operar. |
| QA | Según cierre CHG-280, QA está desplegado en `e57237fe90319f88e1db8ed8d2e686604d2d9c54`, en siete APIs y frontend. La revision vigente de Cloud SQL QA es `20260913_0036`. | [Release 2026-09-14](../operaciones/release_qa_20260914.md). Estado documentado, sin consulta remota en esta conciliación; UAT incompleta. |
| Produccion | No promovida por estos cortes; infraestructura productiva fuera del trabajo autorizado. | [Fronteras de ambientes](../arquitectura/fronteras_ambientes_local_qa_produccion.md). |

La preparación de candidato CONT-01/CHG-290 no se promovió: CHG-291 sustituyó esa siguiente acción por trabajo Local. No existe autorización vigente de despliegue derivada de ese documento.

## Capacidades implementadas y separación organizativa

Las fichas de [módulos](../../modulos/README.md) describen reglas y recorridos. La [matriz CC-01 a CC-20](CONTROL_CONTABLE.md) detalla la relación contable, su dueño, evidencia, brecha y cierre; no debe sustituirse por una suma de notas CHG antiguas.

| Dominio | Implementado y conservado | Límite organizativo vigente en Local |
|---|---|---|
| Administración | Tenant, identidad/permisos, catálogos, folios, organización Sociedad/División/Emisor, scope v2 y configuración por alcance. | Consumidores de impresión/folios y datos reales todavía parciales. Organización nueva es Local, no prueba libro ni QA. |
| Costing | Catálogo básico de centros por División, expuesto por Admin con permisos y estados. | Analítica y Accounting siguen planned, con activación independiente. |
| RH | Áreas, puestos, trabajadores y asignaciones por División con tarifa explícita. | CHG-312 confirma moneda Sociedad en tarifa por División y entrega capacidad nominal con IDs compartidos. CHG-313 integra compromisos laborales en Production y amplía lookup productivo; gates técnicos aprobados; aceptación integrada pendiente. |
| Production | Productos/servicios, máquinas, recetas, validación/planificación, órdenes/etapas, recursos, materiales y evidencia de servicios; asignaciones por División. | CHG-312 confirma tarifa de máquina y consulta capacidad neta global por fecha/División. CHG-313 conecta intento durable, alta manual/liberación, compromisos individuales y costo/contexto para recepción. CHG-315 conecta origen comercial CC-12 y su recepción/entrega real. |
| Inventory | Almacenes/artículos, movimientos inmutables, reversas, saldos/Kardex, reservas, tránsito con recepción/retorno y recepción de terminado/sobrantes. | CHG-307 adapta manuales/reversas y stock de Sales, contexto/costo de Sociedad y filtros. CHG-313 agrega Production/proof, disponibilidad y recepción PT con costo exacto. CHG-317 conecta Maintenance/Purchasing, transferencias misma Sociedad y sobrantes con contexto, costo, alcance y recuperación. |
| Sales | Clientes, cotizaciones, pedidos, entregas y órdenes propias de servicio. | Asignaciones/condiciones por División, cotización→pedido, ciclo de servicios y stock→entrega ya adaptados Local. CHG-314 adapta moneda original/convertida de Servicios (aceptación integrada pendiente); fabricación CC-12 implementada CHG-315 con prueba autenticada y conciliación durable. |
| Purchasing | Proveedores, requisiciones, órdenes, recepciones de bienes y servicios, recuperación de efectos parciales. | Maestro/condiciones por División ya Local; CHG-317 adapta recepción física/costo y prueba origen; requisición/OC y separación integral siguen CC-15. Compra directa API sin alta UI documentada. |
| Maintenance | Correctivos, técnicos, tiempos, bloqueo/liberación de máquina, refacciones/sobrantes y recuperación manual. | CHG-320 implementa contexto, técnicos/tarifas RH, costo laboral y alcance integral; conserva recuperación CC-14. Capacidad sólo Maintenance por persona/día UTC. Resolver no reanuda Production. |
| Reportes/interfaz | 28 reportes operativos CSV por dueño, feedback ES/EN, formularios corregibles, responsive y paginación visual. | Analítica transversal, cursor contractual y cobertura completa de permisos/volumen siguen pendientes. |

La base operativa anterior a la separación incluye el release QA CHG-280. No inferir que sus ampliaciones organizativas posteriores estén en QA. Ventas de servicios, Compras de servicios y tránsito físico ya existen; no volver a listarlos como funcionalidades ausentes por una nota pre-release.

## Evidencia y aceptación

- CHG-314 smoke HTTP: cuatro APIs recargadas; ocho health/login/sesión/contratos aprobados. Una División autorizada con consultas200 vacías de capacidad/máquinas; rechazos401/403/422 esperados. Sin escrituras de negocio; no UAT productiva integrada. Evidencia chg314-http-smoke.log.

- CHG-308 registra 231 pruebas focales PostgreSQL/API, verify 532 aprobadas/152 omitidas, migración up/down vacío/up y smoke Local. No hubo UAT nueva de fabricación ni UI nueva en ese corte.
- CHG-310 registra revisión de implementación y control por submódulo. Los resultados de cada ejecución pertenecen a su corte; [TRAZABILIDAD](../../TRAZABILIDAD.md) conserva esa evidencia.
- QA CHG-280 promovió correctamente el release. CHG-281 aclaró que el texto de evidencia de `OP-000003` sí se guardó; falló el avance de estado por demora RH. Carga/descarga de adjuntos, cierre y otras pruebas autenticadas siguen sin aceptación completa. [Diagnóstico](../auditorias/timeouts_local_2026-09-16.md).
- Guía/matriz QA y Word no equivalen a UAT ni a revisión visual aprobada. Consultar [entrega al tester](../qa/ENTREGA_TESTER.md), [matriz QA](../qa/MATRIZ_EJECUCION_QA.md) y [registro de manuales](../manuales_solucion/REGISTRO.md).

## Evidencia CC-12 · CHG-315

Production137 y Sales/Inventory173 pruebas PostgreSQL/API aprobadas sin omisiones. Navegador completo231 aprobado con APIs interceptadas; 16 pruebas focales finales de visibilidad/recorrido aprobadas. Verify final:596 aprobadas196 omitidas1warning sin DB; validadores/compilación aprobados (chg315-verify.log). Ensayo HTTP real completo con servicios Local recargados: solicitud, orden única, consumo4 unidades, recepción2, entrega2 y costo60MXN→3USD; replays sin duplicados, rechazo de cantidad manipulada y limpieza verificada. Logs chg315-production-tests.log, chg315-sales-inventory-final.log y chg315-http.log. Datos sintéticos no sustituyen aceptación con datos reales CC-19/20.

## Operación y fuentes de autoridad

El [arranque canónico](../../backend/scripts/start_local.ps1) usa PostgreSQL loopback `5434/erclave_local`, Firebase Emulator `demo-erclave` y APIs locales. Ver [inicio de sesión](INICIO_SESION.md), [TENANTS](TENANTS.md) y [fronteras](../arquitectura/fronteras_ambientes_local_qa_produccion.md) antes de escribir. No afirmar disponibilidad actual sin comprobación.

[DECISIONES](DECISIONES.md) responde por qué; [PENDIENTES](PENDIENTES.md) responde qué falta; [CONTROL_CONTABLE](CONTROL_CONTABLE.md) detalla cada integración; [gobierno documental](../arquitectura/gobierno_documentacion_viva.md) establece mantenimiento.

## Historia y sustituciones

El [snapshot anterior](historico/ESTADO_ACTUAL_PRE_CHG311.md) conserva íntegros los cortes, pruebas y revisiones previos. Sus distintas cabezas Local/QA, afirmaciones de tráfico pendiente, catálogos vacíos y mandatos de reanudación no describen el presente. Los handoffs CHG-255/261/269 son históricos; la entrada vigente es INICIO_SESION.

Referencia histórica exigida por el guardrail heredado: CHG-191 registró `admin-service-qa-bo-1-1`, `inventory-service-qa` y `hr-service-qa`. Se conserva para rastreo, **no como revisión desplegada vigente**.
