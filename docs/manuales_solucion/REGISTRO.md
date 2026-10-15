# Registro de manuales funcionales

## Siete exportaciones revisadas - CHG-331 - 2026-10-14

Se regeneraron los Word de Producción, Inventarios, Compras, Ventas, Administración, RH y Mantenimiento desde sus fuentes Markdown actuales. Se comprobó la paridad textual, la integridad ZIP/XML y las tablas; se renderizaron con LibreOffice 26.8.1 y se revisaron visualmente sus 50 páginas. No hay páginas vacías ni texto o tablas recortados. Las huellas SHA256 de cada par fuente/Word y la revisión constan en `docs/documentacion-registro.json`.

Los siete Word son **exportaciones candidatas del alcance Local**. Su revisión documental no equivale a la aceptación integrada CC-20 ni a promoción a QA. Las notas de CHG-329 y anteriores describen el estado anterior a esta regeneración.

## Selector organizacional - CHG-329 - 2026-10-14

La fuente Markdown de Administración describe cómo elegir Sociedad y División en la barra superior de Local, buscar por nombre o código, conservar la selección tras recargar y distinguir el Centro de costos. Se contrastó con el recorrido observado en navegador real. El Word de Administración todavía no refleja esta fuente; permanece como exportación pendiente y no se distribuye como guía de CHG-329. La revisión visual de Word sigue pendiente.

## CC-21 - CHG-325 - 2026-10-14

Fuentes Markdown de Produccion y Ventas actualizadas para el costo confirmado por Division, tasa de cotizacion, vista previa, snapshot al aprobar y estimado/margen nulos si falta un dato confiable. Los Word respectivos aun no incluyen CC-21 y no deben distribuirse como guia vigente de este corte. Regeneracion, paridad y revision visual pendientes; usar las fuentes Markdown como referencia funcional actual.

## CC-18 - CHG-323 - 2026-10-14

Fuentes Markdown RH, Inventory, Compras, Mantenimiento y Administracion actualizadas para folios por modo administrado/manual, reintentos e historia Local. Los Word correspondientes aun no incluyen CC-18 y no deben distribuirse como guia vigente de este corte. Regeneracion, paridad y revision visual quedan pendientes; usar las fuentes Markdown como referencia funcional actual.

## CC-17 - CHG-322 - 2026-10-14

Las fuentes Markdown 01 Produccion, 04 Ventas y 08 Administracion describen la presentacion efectiva por Division y el snapshot al liberar/aprobar, solo Local. La fuente 08 retira la indicacion superada de que todas las impresiones usan la plantilla corporativa. Los tres Word anteriores no incluyen este cambio y no deben distribuirse como guia CC-17. Regeneracion, paridad y revision visual quedan pendientes: no hay runtime Node de documentos ni LibreOffice disponibles en esta sesion. Las fuentes Markdown son la guia vigente de este recorrido.

## Control vigente · CHG-320 · 2026-10-12

**Mantenimiento candidato CHG-320:** fuente y Word describen contexto fijo de orden, técnicos RH por División, tarifa/costo de tiempos conservados, capacidad por persona/día UTC dentro de Maintenance y refacciones heredadas. Implementado Local: Maintenance50, RH/Production123 y navegador271 aprobadas sin omisiones; navegador con APIs interceptadas, no UAT. Verify general posterior a esta conciliación. Generación canónica con Python empaquetado Codex 3.12.14, paridad exacta **160 párrafos/celdas y 3 tablas**, ZIP/XML aprobados (`chg320-manual-build.log`, `chg320-manual-parity.log`). Render intentado sobre el Word regenerado: falla `_resolve_soffice`, LibreOffice ausente (`chg320-manual-render.log`); no PNG ni revisión de páginas. Word candidato con revisión visual pendiente. [Contrato CC-16](../arquitectura/cont_08_mantenimiento_contexto.md).

**Compras actualizado como candidato CHG-319:** fuente y Word describen División fija de requisición/orden, proveedor y condiciones por División conservadas, cambio explícito de proveedor, recepción heredada incluso para servicios y revisión de documentos históricos. Implementado sólo Local: backend focal77 aprobadas/0 omitidas/1 advertencia (`chg319-purchasing-terms-tests.log`, incluye diez CC-15 PostgreSQL y dos de alcance propio para enviar/aprobar); navegador focal16 CC-15 +6 CC-14 aprobadas con APIs interceptadas. Regresión UI completa255 aprobadas (`chg319-browser-regression-final.log`); verify727 aprobadas/223 omitidas/1 advertencia sin DB (`chg319-verify-final.log`). Aceptación transversal CC-20 pendiente; no promoción QA. Contrato y criterios: [contexto de Compras](../arquitectura/cont_08_compras_contexto.md).

Generador canónico con Python empaquetado Codex 3.12.14: `chg319-manual-build.log`. Paridad textual exacta de **172 párrafos/celdas y 3 tablas**, integridad ZIP y XML parseable aprobadas: `chg319-manual-parity.log`. Render intentado sobre este Word regenerado: `_resolve_soffice` falla porque `LibreOffice soffice.exe` no está en PATH (`chg319-manual-render.log`). No produjo PNG; ninguna página fue revisada visualmente. Word candidato, revisión visual pendiente. Los registros CHG anteriores siguientes conservan su alcance histórico.

Autoridad: [estado por ambiente](../contexto/ESTADO_ACTUAL.md), [control contable](../contexto/CONTROL_CONTABLE.md), [biblioteca](README.md) y [gobierno documental](../arquitectura/gobierno_documentacion_viva.md). QA documentado e57237f; preparación dimensional posterior sólo Local.

**Inventarios, Compras y Mantenimiento actualizados en CHG-317:** tres fuentes y tres Word incorporan recepciones físicas con prueba de origen, División del almacén y proveedor elegible; tasa explícita de moneda documental a Sociedad; refacciones con contexto confirmado; transferencias dentro de una Sociedad y sobrantes con contexto/costo de salida conservados. El manual de Compras distingue precio documental vigente de dos decimales de costo convertido a seis; señala el rechazo de recepciones que mezclan monedas de Sociedad. CC-15 y CC-16 completos siguen abiertos. No se promueve este alcance a QA ni se presenta como UAT concluida.

Generación con Python empaquetado de Codex 3.12.14 y generador canónico de la skill de manuales: `chg317-manual-build.log`. Paridad textual exacta de **496 párrafos/celdas y 8 tablas**, integridad ZIP y XML parseable aprobadas: `chg317-manual-parity.log`. Render ejecutado sobre el Word regenerado de Inventarios con el renderer empaquetado; falla `_resolve_soffice` por ausencia de `LibreOffice soffice.exe`, evidencia `chg317-manual-render.log`. No se produjeron PNG ni se revisaron páginas. Los tres Word conservan estado candidato con revisión visual pendiente.

**Producción, Inventarios, Ventas y Administración actualizados en CHG-315:** cuatro fuentes y cuatro Word incorporan solicitud de fabricación por partida, planificación productiva con origen de sólo lectura, recepción física y conciliación explícita del pedido, sin captura de cantidad/costo sustitutivos. Incluyen permisos, monedas, reintentos, recepción insuficiente y recuperación de la misma reserva. Los cambios de capacidad/tarifas de RH y Producción de CHG-313 y costos de Servicios de CHG-314 se conservan. Sólo Local; no nueva UAT ni promoción QA. Navegador con APIs interceptadas: 16 pruebas focales finales de permisos y 231 de suite completa previa aprobadas, sin atribuirles integración de servicios reales.

Paridad textual completa de 708 párrafos/celdas, integridad ZIP/XML y 10 tablas aprobadas para los cuatro Word: `chg315-manual-parity.log`; generación: `chg315-manual-build.log`. Render reintentado con Python empaquetado sobre Producción: falta LibreOffice, fallo `_resolve_soffice`; `chg315-manual-render.log`. No se generaron PNG ni se revisaron páginas. Los Word permanecen candidatos, no ediciones visuales aprobadas. La comprobación estructural previa de RH corresponde a `chg314-manual-parity.log`.

**Base editorial CHG-311 — ocho exportaciones regeneradas:** CHG-311 corrige instrucciones superadas en fuentes Markdown de Inventarios, Ventas, Compras y Administración y aclara límites de tarifas de Producción/RH. Los siete manuales y la guía QA se regeneraron con el Python empaquetado de Codex usando los generadores existentes. Una comprobación independiente verificó integridad ZIP, XML parseable y presencia del texto de cada párrafo/celda fuente. No certifica distribución final ni composición visual. Los bloqueos de herramientas anotados abajo pertenecen a sus sesiones y deben reevaluarse con el flujo vigente.

Catálogo básico de Centros de costos implementado Local: procedimiento en Administración; sólo analítica de Costos sigue planned. Gastos, Reporting transversal y Accounting no tienen manual operativo.

### Comprobación real de herramientas en CHG-311

El 2026-10-07 se localizaron y probaron dependencias del runtime Codex 26.1007.11041 en `~/.cache/codex-runtimes/codex-primary-runtime`: Python 3.12.14 con `python-docx` y `pdf2image` disponibles. Por tanto, la falta general de runtime/python-docx de sesiones anteriores no describe esta sesión. El manifiesto declara `libreOfficeVersion: null`.

Se ejecutó el renderer empaquetado `render_docx.py` con ese Python sobre el Word existente de Producción. Terminó con código 1 en `_resolve_soffice`: `FileNotFoundError: LibreOffice soffice.exe was not found on PATH`. No produjo páginas PNG; no hubo revisión visual. Se repitió el render sobre el Word regenerado con el mismo fallo. No se instaló software ni se usó Word/LibreOffice de escritorio como sustituto; paridad textual y estructura se aprobaron por separado. El cierre requiere un runtime de render disponible y revisión de todas las páginas de los ocho documentos.

### Huellas históricas de generación CHG-311 a CHG-320

Las huellas actuales de los siete manuales están en `docs/documentacion-registro.json` tras CHG-331.

Paridad de texto y ZIP/XML aprobados para estas huellas; cualquier cambio posterior de fuente requiere regeneración. La paridad textual no es revisión visual.

| Fuente | SHA256 fuente | SHA256 Word candidato |
|---|---|---|
| docs/manuales_solucion/fuentes/01_produccion.md | `4cbcaed10d2e8408a28e9f86bac1d2549911118999f5cd1047b6dd9a1e620459` | `57b5cef3d23c2fe210ea459aa827025e4b6383d3e34af9d01c7c835c328b4076` |
| docs/manuales_solucion/fuentes/02_almacenes_inventarios.md | `527fc9c212c4da15597a405a4aeacb6b941831c5696668ac3bdce0ef45e480d0` | `69b91378fffc5d78481b50799f06f839f12d02a1db3ec15df2143476708b12f9` |
| docs/manuales_solucion/fuentes/03_compras_abastecimiento.md | `e5e0a7231c6c82efeb819f43cb86ffbb4337ecb8dc90ee6c79582b5edc586968` | `9ee01b5961de2f370596e9bb5643776a9dca366f0a28faa661f727e882810109` |
| docs/manuales_solucion/fuentes/04_ventas_clientes.md | `50158ce1fba1d657160ad0f360a2b7c64a4cce0146acad368bcc45780c2e6253` | `daa72f766d7d95260a8b36cd8816bbdd73839e1ae3656ba53256cbbe44ab1f87` |
| docs/manuales_solucion/fuentes/08_administracion_configuracion.md | `0fd00ee31c4b58377fe411570dce843cf6f972df258a932137de4c49bd991b31` | `5fd26ddf3edcf34d34ccf89c741c8609d8a8abd84f77222335a8bf88cfc26906` |
| docs/manuales_solucion/fuentes/10_recursos_humanos.md | `283300f65950184c165004dc8d051bce9c91c530092ab6e4aef8c8a8a9e04f4c` | `ae28f3f9a565cfa2512f635ec674d4ea511ce0fc09cbb7704246e278eeea31c7` |
| docs/manuales_solucion/fuentes/11_mantenimiento.md | `58d6e35c0a0a5f0a0f30f974a0c41bc1168bf6380ebd63a416aa63952a5cd709` | `29fce7e1d2e644b42d1e9ce71000f1cc7f8a3191f2eddca5ae052ed5f7f6d61b` |
| docs/qa/guia_pruebas_qa_mvp.md | `48e7f439628dba4cfa1c33880a33d57cf572c124381b4d5903b6761523c58b67` | `3cc54fdd178517befe8a0c59e9e0f1aafbe1916a6dca0a857eb33dd45d62b78b` |

## Evidencia de ediciones anteriores

Los apartados siguientes registran lo comprobado o pendiente en cada fecha; no son una lista acumulativa vigente ni nuevas instrucciones de ejecución.

## Actualización CHG-307 · 2026-10-05

Fuentes Ventas/Inventarios actualizadas con stock y moneda explícita. Word pendiente: runtime de documentos no disponible en esta sesión; no se atribuye generación/validación visual a los .docx existentes. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


## Actualización CHG-305 · 2026-10-05

Fuente 04 Ventas actualizada con ejecución de servicios por División. Word pendiente runtime documents/revisión visual; no certificar paridad.


## Actualización CHG-304 · 2026-10-05

Fuente 04 Ventas actualizada con contexto fijo de pedido, consulta de servicios y cancelación. Word pendiente de runtime documents y revisión visual; no certificar paridad.


## Actualización CHG-303 · 2026-10-05

Fuente 04 Ventas actualizada con contexto de cotización. Word pendiente de regeneración con runtime documents y revisión visual; no afirmar paridad Word/Markdown.


## Revisión de condiciones comerciales 2026-09-28 — CHG-302

Fuentes 03/04 actualizadas para opción 2: condiciones completas por División, sin herencia, con procedimientos/permisos/errores/límites Local. Word no regenerado ni revisado visualmente; continúa pendiente por runtime requerido de la skill documents no disponible en esta sesión (python-docx sí disponible). No distribuir Word previo como cobertura de este flujo. Ver fuentes Markdown vigentes.

## Revisión de Compras y Ventas 2026-09-28

Fuentes 03/04 actualizadas para disponibilidad por División/Sociedad derivada en Local (CHG-301). Describe alcance, permisos, activación/desactivación, conflictos y límites de condiciones/documentos. Word no regenerado ni certificado: la skill documents requiere el runtime de artefactos Codex, no disponible en esta sesión; python-docx sí está instalado y no es el bloqueo. Regeneración y revisión visual siguen pendientes; prevalecen estas fuentes Markdown para el nuevo procedimiento. No distribuir los Word previos como edición del nuevo alcance.

## Revisión de Administración 2026-09-27

Fuente de Administración actualizada para organización normalizada, alcances CONT-03 y piloto CONT-04 de plantilla por alcance sólo Local. El Word anterior no incluye aún este procedimiento: regeneración y revisión visual pendientes; prevalece Markdown. QA conserva su comportamiento previo. No distribuir ese Word como manual del nuevo alcance.

## Revisión de cierre 2026-09-20

La edición Markdown y los ocho DOCX generados permanecen como candidatos. No se completó la revisión visual: el renderizador de documentos no arrancó por falta de `pdf2image` y LibreOffice, la automatización de Word devolvió `0x80070520` y `01_produccion.docx` estaba bloqueado por otro proceso al intentar leerlo. La validación estructural del 16 de septiembre sigue siendo la última comprobación completa registrada. No distribuir los Word como edición final hasta renderizar y revisar todas sus páginas.

Revisión histórica de la edición QA: 2026-09-15.

Se revisaron las siete fuentes y la guía contra la versión desplegada en QA. Los resultados funcionales completos siguen por registrar. La revisión documental y el despliegue no sustituyen las pruebas con usuarios, permisos y datos autorizados.

Todos los módulos incorporan instrucciones de corrección de formularios. Producción agrega margen esperado sin tope de negocio, evidencia de recepción y cierre en el avance, límites, optimización, permisos y vencimiento de todos los adjuntos a 365 días.

| Módulo | Fuente canónica | Word candidato revisado en CHG-331 | Cobertura actual | Ambiente descrito | Limitaciones principales |
|---|---|---|---|---|---|
| Producción | [fuentes/01_produccion.md](fuentes/01_produccion.md) | [word/01_produccion.docx](word/01_produccion.docx) | Productos/servicios, margen sin tope, evidencia inicial/final y adjuntos, recetas, maquinaria, capacidad multídía, órdenes, salida previa por Almacén, etapas, sobrantes, producto terminado y CSV estándar | Local y QA e57237f | Calendario configurable, merma y borrador separado de liberación |
| Almacenes | [fuentes/02_almacenes_inventarios.md](fuentes/02_almacenes_inventarios.md) | [word/02_almacenes_inventarios.docx](word/02_almacenes_inventarios.docx) | Almacenes, artículos, movimientos, balances, Kardex, reservas, confirmaciones físicas, transferencias, sobrantes y CSV estándar | Local y QA e57237f | Lotes, series, cuarentena, empaque y merma |
| Compras | [fuentes/03_compras_abastecimiento.md](fuentes/03_compras_abastecimiento.md) | [word/03_compras_abastecimiento.docx](word/03_compras_abastecimiento.docx) | Proveedores, requisiciones, órdenes, recepciones preparadas, aceptación por solicitante, conciliación y CSV estándar | Local y QA e57237f | Multi-proveedor, devoluciones, factura, CxP y pagos |
| Ventas | [fuentes/04_ventas_clientes.md](fuentes/04_ventas_clientes.md) | [word/04_ventas_clientes.docx](word/04_ventas_clientes.docx) | Clientes, cotizaciones, pedidos, surtido, entregas confirmadas por Almacén, órdenes de servicio y CSV estándar | Local y QA e57237f | Devoluciones, factura, cobranza, PDF y paginación |
| Administración | [fuentes/08_administracion_configuracion.md](fuentes/08_administracion_configuracion.md) | [word/08_administracion_configuracion.docx](word/08_administracion_configuracion.docx) | Sesión, organización, usuarios, roles, permisos, módulos, catálogos y Backoffice | Local y QA | Billing/provisioning automático y reconciliación durable Firebase |
| Recursos Humanos | [fuentes/10_recursos_humanos.md](fuentes/10_recursos_humanos.md) | [word/10_recursos_humanos.docx](word/10_recursos_humanos.docx) | Áreas, puestos, trabajadores, capacidad, elegibilidad operativa y CSV estándar | Local y QA e57237f | Nómina, ausencias, calendarios y documentos |
| Mantenimiento | [fuentes/11_mantenimiento.md](fuentes/11_mantenimiento.md) | [word/11_mantenimiento.docx](word/11_mantenimiento.docx) | Correctivos, asignación, tiempo, refacciones, bloqueo, entrega por Almacén, recuperación, sobrantes y CSV estándar | Local y QA e57237f | Preventivos, activos generales, adjuntos y reintento automático programado |

## Módulos sin manual operativo

Gastos/Cuentas por pagar, analítica de Costos, Reportes avanzados y Contabilidad continúan como capacidades planeadas. El catálogo básico Costing se documenta en Administración sólo Local. No se generan manuales Word de uso hasta que exista un runtime y una interfaz verificables; hacerlo antes mezclaría arquitectura objetivo con capacidades disponibles.

## Criterio de vigencia

Sólo una pareja fuente Markdown + Word con paridad y revisión visual comprobadas puede distribuirse como edición final. Si una fuente y su Word difieren, prevalece la fuente y el Word debe regenerarse antes de publicarse.

## Referencia y validación funcional

Pendiente funcional identificado: comprobar o corregir el montaje de la bandeja de devolución de sobrantes en Mantenimiento. La API existe, pero el selector usado para insertar la bandeja no corresponde al contenedor renderizado. Responsables: agente técnico de Mantenimiento y QA. El manual y la guía distinguen el procedimiento previsto del acceso aún por validar.

Base desplegada: `e57237fe90319f88e1db8ed8d2e686604d2d9c54`, desplegada en QA. Los procedimientos se contrastaron con código, interfaz, permisos, contratos y pruebas del corte. La aceptación funcional con usuarios reales permanece pendiente de ejecución por el tester; no se declara aprobada por regenerar estos documentos. La guía de pruebas incluye resultados por registrar y precondiciones explícitas para casos restringidos.

## Validación de esta edición (2026-09-15)

Fuentes contrastadas con las fichas de agentes de negocio/técnicos y del Custodio de manuales, interfaz y textos, contratos y pruebas; en Producción se revisaron además el componente de evidencia y las validaciones de archivos y margen en backend. Los límites de módulos futuros y las dudas funcionales conocidas se mantienen explícitos.

Los ocho DOCX se regeneraron el 15 de septiembre desde las fuentes canónicas con los generadores del repositorio. Comprobación estructural aprobada: integridad ZIP, XML parseable, portada con e57237f y fecha vigente, tablas y título presentes, sin referencia b63cdad ni pie de página QA pendiente. Se corrigieron el pie y los metadatos del generador para no fijar un release obsoleto.

Revisión visual pendiente: no hay LibreOffice/Poppler ni runtime de contenedor disponible; Word instalado no se automatizó. La estructura XML no certifica páginas, tablas o saltos. No distribuir los DOCX como edición visualmente aprobada ni reutilizar la revisión del 10 de septiembre.

Guía y matriz: 65 casos únicos (56 base + 9 de formularios, margen y evidencia). Smoke QA parcial: se observó el formulario nuevo y el rechazo de descripción inicial vacía en OP-000003; no se guardó evidencia, no se probó descarga ni cierre al 100%. La carga automatizada quedó impedida por el permiso de acceso a archivos locales de la extensión del navegador; no se clasifica como fallo del producto. La UAT permanece pendiente; responsables: Producción, QA/Release y los agentes de cada módulo para sus variantes.


Validación transversal CHG-280: `npm run verify` aprobado (validadores, compilación y 302 pruebas backend aprobadas; 58 omitidas al ejecutar sin DB). La corrida PostgreSQL completa de 360 aprobadas/cero omitidas pertenece al release previo, no se repitió por esta edición documental. Skills de manuales y QA/release validadas; diff sin errores. APIs afectadas: ninguna.


## Edición complementaria CHG-281 — 2026-09-16

Siete fuentes agregan la mejora de esperas y resultado incierto exclusivamente Local. Producción explica evidencia confirmada separada del avance. Ocho Word regenerados, ZIP/XML y tablas comprobados; revisión visual sigue pendiente. QA mantiene e57237f. Pruebas y alcance: [auditoría de tiempos](../auditorias/timeouts_local_2026-09-16.md).

CHG-297: fuente 08 Administración actualizada con catálogo básico por División. Word de este avance pendiente de regeneración/revisión visual; no declarado listo para entrega final.

CHG-298: fuente 02 Almacenes actualizada con asignaciones por División. Word pendiente de regeneración/revisión visual: el intérprete disponible no tiene python-docx. No certificado como manual final.

## CHG-299 — Producción por División (Local)

Fuente 01_produccion.md actualizada para máquinas y productos/servicios. Word pendiente de regeneración y revisión visual; la skill documents requiere dependencias del workspace mediante su loader/runtime, no disponible en esta sesión. python-docx sí existe en la venv del repositorio, pero no sustituye ese runtime requerido. No distribuir el Word previo como guía de este nuevo recorrido.

## CHG-300 — RH por División (Local)

Fuente 10_recursos_humanos.md actualizada para tarifa/centro de puestos y elegibilidad de trabajadores por División. Word pendiente de regeneración y revisión visual; permanece el bloqueo del runtime de documentos registrado en CHG-299. No distribuir el Word anterior como guía de este recorrido.
