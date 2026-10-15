# Pendientes priorizados de ERClave

## Candidato Git - CHG-331 - 2026-10-14

Los siete Word y sus fuentes ya tienen paridad y revisión visual de 50 páginas; las huellas del registro están renovadas. `verify` aprobó con 746 pruebas backend, 244 omitidas por condiciones del entorno y una advertencia de dependencia. El árbol acumulado se inventarió y agrupó como candidato de integración Local. Conservarlo como candidato hasta la aceptación CC-20 y una promoción QA autorizada. El pendiente documental CHG-330 siguiente quedó resuelto por este corte.

## Preparación documental de Git - CHG-330 - 2026-10-14

Regenerar los siete manuales Word desde sus fuentes Markdown actuales, comprobar paridad textual y revisión visual de todas sus páginas, y actualizar las huellas del registro sólo después. Ejecutar de nuevo `validate:documentation` y `verify` antes de tratar el árbol acumulado como candidato. Los Word anteriores siguen siendo exportaciones pendientes; no equivalen a la funcionalidad Local actual.

## Selector de contexto Local - CHG-329 - 2026-10-14

El control recortado de Sociedad/División quedó corregido en Local y comprobado en navegador con el tenant demo. No cambia los pendientes de mapeo real CC-19, fixtures/aceptación CC-20 ni la activación futura de Accounting. Falta aceptación formal de CC-20 y promoción autorizada a QA.

## Demo Local preparado parcialmente - CHG-328 - 2026-10-14

Ya existen 2 Sociedades, 3 Divisiones y 3 Centros de costos activos sintéticos en el tenant demo Local; se registraron sus IDs y 38 excepciones legacy en `.local/cc19-demo-*.csv`. Falta crear asignaciones y condiciones por los APIs de cada dueño, además de los demás fixtures y actores de alcance restringido para ejecutar CC-20. Los datos reales/equivalencias aprobadas y el tratamiento histórico de CC-19 siguen pendientes. Accounting no tiene runtime para guardar libros, cuentas o reglas; la guía CC-19 sólo prepara sus decisiones futuras. La precondición de estructura mencionada en CHG-327 abajo ya quedó cubierta.

## CC-20 preparado para Local - CHG-327 - 2026-10-14

[Matriz de 16 recorridos y procedimiento](../operaciones/cc20_aceptacion_integrada_local.md) preparados; todos permanecen Por ejecutar hasta la sesión Local solicitada después. Faltan fixtures sintéticos de dos Divisiones de una Sociedad y una de otra, actores de alcance distinto y conciliación por dueño; no crear tenants temporales. Resultados de navegador con APIs interceptadas y pruebas focales anteriores no cierran CC-20. QA y datos reales CC-19 son trabajos separados.

## CC-19 - insumos reales pendientes - CHG-326 - 2026-10-14

El usuario aun no cuenta con estructura/equivalencias reales. [Guia con diagrama y matriz de mapeos](../arquitectura/cc19_mapeos_y_configuracion_contable.md) preparada para reunirlas. Para avanzar al backfill: padron aprobado Emisor/Sociedad/Division con moneda base; equivalencias por ID y evidencia de maestros, documentos/partidas y sus vinculos; moneda/tasa historicas confirmadas donde existan; lista de excepciones. Preflight y aprobacion del plan preceden cualquier escritura. Accounting es opcional y su catalogo de cuentas/libros/reglas es una configuracion futura separada. CC-19 no esta cerrado; CC-20 y Word tambien siguen pendientes.

## CC-21 implementado Local - CHG-325 - 2026-10-14

Production conserva costo unitario confirmado por Division/Sociedad y Sales calcula vista previa, refresca en envio/aprobacion, congela procedencia/tasa/convertido por partida y copia al pedido. Cuando falta costo o tasa, costo/margen quedan nulos y la aprobacion continua. Migracion 0062 Local sin backfill. Los siguientes pendientes de fase son CC-19 datos reales y CC-20 aceptacion integrada; Word y promocion QA requieren trabajo propio. La revision CHG-324 siguiente es historica.

## CC-21 - costo estimado de cotizaciones - CHG-324 - 2026-10-14

La revision de codigo y contrato detecto que `standard_cost` de Production no declara moneda/Sociedad, mientras Sales lo compara con el precio de cotizacion y copia el estimado al pedido. Se formaliza CC-21 como adaptacion monetaria pendiente, sin reabrir los recorridos CC-07/08. Regla confirmada: si falta costo o tasa confiable, se puede aprobar con costo y margen estimados nulos. Implementar procedencia/convertido por partida, snapshot, reporte y UI; despues verificar Local. [Revision](../arquitectura/cont_08_costo_estimado_cotizaciones.md). Las secciones siguientes son historicas.


## Estado CC-18 - CHG-323 - 2026-10-14

CC-18 implementado Local para los consumidores definidos en CONT-06. Admin es autoridad de secuencias; cada dueno conserva modo/codigo donde corresponde, sin renumerar historia. Movimientos automaticos Inventory en modo manual usan codigo estable del origen. Pendientes: revision de costo estimado, mapeo de datos reales CC-19, aceptacion integrada CC-20, promocion QA autorizada y regeneracion/verificacion visual de manuales Word. Las secciones CHG-322 y anteriores son historicas.

## Reanudacion CC-17 - CHG-322 - 2026-10-14

La pausa CHG-321 termino por solicitud del usuario. CC-17 esta implementado solo en Local para cotizaciones y ordenes de produccion: Admin resuelve presentacion por Division; Sales congela al aprobar y Production al liberar. Los demas generadores deben definir su integracion al existir. Siguiente trabajo: CC-18 y revision del costo estimado; CC-19 requiere mapeo real y CC-20 aceptacion integrada. La lista CHG-320 siguiente conserva el estado previo al corte.

## Lista vigente conciliada · 2026-10-12

**Pausa CHG-321 solicitada por el usuario:** se conserva CC-16 cerrado sólo en Local y no se inicia otro corte. Al reanudar siguen pendientes, por separado: CC-17 identidad/configuración efectiva de impresión y snapshot histórico; CC-18 consumidores restantes de folios con concurrencia e historia; revisión del costo estimado de cotizaciones según la política monetaria vigente; CC-19 estructura, asignaciones y migración de datos reales con mapeo explícito; CC-20 aceptación integrada y eventual candidato QA autorizado. Ninguno se considera resuelto por las pruebas focales de CC-14/15/16. [Punto de reanudación](INICIO_SESION.md).

**CHG-320 CC-16 implementado Local:** Maintenance50, RH/Production123 y navegador271 aprobadas sin omisiones. Contexto fijo de orden, técnicos/tarifas RH, costo de tiempos, scope integral y materiales heredados. [Evidencia](../arquitectura/cont_08_mantenimiento_contexto.md). Capacidad limitada a Maintenance por trabajador/día UTC; no agenda transversal. CC-17/18, costo estimado, datos CC-19 y aceptación CC-20 siguen pendientes.

Esta lista sustituye la acumulación de pendientes de cortes antiguos. Corte Local CHG-320, conservando CHG-313/314/315; decisión monetaria CHG-309 y conciliación documental CHG-311. Estado/ambientes en [ESTADO_ACTUAL](ESTADO_ACTUAL.md); inventario contable detallado en [CONTROL_CONTABLE](CONTROL_CONTABLE.md). La historia original se conserva en el [snapshot previo a CHG-311](historico/PENDIENTES_PRE_CHG311.md).

La auditoría documental CHG-311 terminó. CHG-312 implementa confirmación de tarifas y consultas por División; CHG-313 conecta orden manual por División e Inventory; CHG-314 adapta moneda de Servicios. CHG-315 cierra fabricación comercial CC-12 con ensayo HTTP real y reintentos sin duplicados. La aceptación transversal continúa CC-20. La separación operativa se termina en Local antes de preparar QA; no se activa Accounting.

**CC-15 CHG-319 implementado Local:** requisiciones/órdenes con contexto y condiciones explícitas, recepciones heredan División y moneda; alcance en comandos, replays, bandejas y CSV. Conservar CC-14 y los snapshots históricos. CC-16 implementado CHG-320. Siguiente desarrollo: CC-17/18 y revisión del costo estimado. Datos CC-19 y aceptación CC-20 permanecen abiertos. [Detalle](../arquitectura/cont_08_compras_contexto.md).

## Estado de cierre de fase · CHG-320

**Fase abierta.** CC-17 para cotizaciones y ordenes de produccion quedo implementado Local CHG-322. Quedan CC-18, revision del costo estimado, datos CC-19 y aceptacion CC-20. Accounting continua apagado. Las referencias CHG-320 anteriores describen el estado previo al corte.

## Separación operativa: siguiente implementación

| Orden de trabajo | Filas de control | Trabajo pendiente; qué conservar |
|---|---|---|
| Tarifas y capacidad | CC-10 | Fuentes y consultas implementadas CHG-312; conservar confirmación monetaria, consulta nominal RH e identificación global y capacidad neta máquina. CHG-313 implementa compromiso/liberación laboral manual; smoke HTTP de lectura aprobado; consulta positiva con recursos y escritura integrada de fabricación aprobadas CHG-315. |
| Fabricación | CC-11/12 | Implementadas orden manual CHG-313 y fabricación comercial CHG-315. Recorrido HTTP real aprobado; conservar intento durable, compromisos laborales, reservas, recepción y costo original/convertido. No desarrollar otra vez; sólo aceptación transversal/datos CC-19/20. |
| Moneda de servicios | CC-08 | Conservar CHG-314 probado de original Sociedad/tasa/convertido y UI; completar aceptación integrada CC-20; conservar ciclo por División y no reinterpretar históricos. Revisar costo estimado de cotización al extender política, sin declarar esa revisión cerrada. |
| Otros productores de Inventarios | CC-14 | Implementado Local CHG-317: Purchasing/Maintenance, transferencias y sobrantes preservan contexto/costo/alcance y recuperación. Conservar pruebas PostgreSQL/API/UI; datos y aceptación transversal siguen CC-19/20. [Detalle](../arquitectura/cont_08_inventario_productores.md). |
| Compras | CC-15 | Implementado Local CHG-319: contexto fijo requisición/OC, condiciones explícitas/snapshot, herencia y alcance integral/CSV. Recepción física/proof CC-14 conservados; datos/aceptación CC-19/20. [Detalle](../arquitectura/cont_08_compras_contexto.md). |
| Mantenimiento | CC-16 implementado Local | CHG-320: contexto, técnicos/tarifas, tiempos y alcance/reportes probados. Preservar recuperación CC-14; aceptación CC-20 pendiente. |
| Configuracion e impresion | CC-17 | Implementado Local CHG-322 para cotizaciones y ordenes de produccion: identidad/plantilla efectiva por Division y snapshot historico. Otros generadores se integraran al existir. |
| Folios | CC-18 | Implementado Local CHG-323 para puestos RH, movimientos Inventory, proveedor/requisición/OC/recepción Purchasing y órdenes Maintenance; preservar histórico. |
| Datos reales | CC-19 | Obtener estructura/asignaciones, previsualizar y migrar con alcance explícito, sin inventar moneda ni mapeo. |
| Aceptación integrada | CC-20 | Recorridos completos, permisos/alcance, reintentos, CSV e historia con Accounting apagado; después candidato QA autorizado. |

No reabrir CC-01–07/09/13 ni el ciclo de CC-08. Los criterios por fila y responsables se mantienen en CONTROL_CONTABLE, sin duplicarlos aquí. La política monetaria y la obligatoriedad de centros ya están resueltas en [DECISIONES](DECISIONES.md).

## Validación, documentación y QA todavía abiertas

- Completar UAT del SHA QA documentado: permisos, aislamiento, dependencias, recepciones, capacidad, valuación, concurrencia, protección de datos e idempotencia. La [matriz QA](../qa/MATRIZ_EJECUCION_QA.md) conserva los resultados reales; no convertir pruebas Local en aceptación remota.
- Retomar prueba autenticada de `OP-000003`: adjuntos/carga/descarga, evidencia final al 100%, regresión de producto, expiración y permisos/aislamiento. El texto sí se guardó según CHG-281; no repetir el diagnóstico superado de CHG-280. Conservar fixtures y registrar su cierre, sin crearlos otra vez por inferencia. Ver [diagnóstico](../auditorias/timeouts_local_2026-09-16.md).
- CHG-281: preparar eventual candidato de tolerancia a demoras sólo tras reconciliar el delta y evidencia. La auditoría documental actual no publica ni autoriza release. No repetir el release CHG-278/280 ni aprovisionar otra vez el bucket ya resuelto.
- CHG-315: recorrido HTTP autenticado real de fabricación→recepción→entrega aprobado, Accounting apagado, 60MXN→3USD y limpieza por IDs propios verificada. PostgreSQL/API y navegador interceptado conservan evidencia separada. Otros recorridos y aceptación transversal continúan CC-20.
- Revisar visualmente portada, tablas, listas, saltos y encabezados de siete manuales Word y guía Word; corregir/regenerar antes de distribución. El registro estructural no sustituye ese control. [Registro de manuales](../manuales_solucion/REGISTRO.md) y [entrega](../qa/ENTREGA_TESTER.md).
- Ejecutar/conciliar evidencia de navegador pendiente de CHG-284/285: proveedor con catálogos dinámicos y referencias históricas de cliente/cotización, en stack Local aislado; luego prueba QA dentro de release autorizado. Preservar implementación existente.
- Confirmar/corregir acceso UI de sobrantes Maintenance: selector `.submodule-screen` identificado en CHG-271; no declarar recorrido completo desde pantalla por existir API. Conservar límite de compra directa: API disponible, alta UI no expuesta.
- Mantener aceptación manual aún sin constancia de cierre para correcciones UAT CHG-266 y presentación compacta CHG-267; la promoción posterior no demuestra aceptación.
- Repetir comprobación de entradas que antes sólo quedaron en `localStorage`: Movimientos, Inventario y Kardex deben mostrar mismo saldo en Local; no copiar datos a QA.
- Pruebas autorizadas de onboarding/correo Firebase, eliminación/cleanup, allowlist Backoffice frente a owner ordinario y editor de permisos (persistencia, concurrencia y grants prohibidos). No persistir credenciales. Para áreas/puestos QA usar únicamente capturas ficticias autorizadas; no asumir que el catálogo continúa vacío.
- Completar carga sostenida, cortes de red reales, perfiles combinados y respuesta incierta de entregas/reservas. Las pruebas PostgreSQL y locks existentes no cierran por sí solas esos escenarios. Reservas vencidas y movimientos históricos no se reactivan ni compensan automáticamente.
- Ampliar evidencia negativa de formularios por consumidor afectado. El registro de 54 variantes prueba wiring, no reglas exhaustivas. Resolver con negocio campos de Producto/Servicio (categoría, área responsable y captura obligatoria/opcional/derivada); centros se rigen por CHG-296, no por obligatoriedad global antigua. [Auditoría piloto](../auditorias/piloto_contrato_formularios_2026-09-20.md).
- Publicación documental pendiente de instrucción expresa. Mantener verificaciones de tooling disponibles; si Node/npm estándar falta, declarar el mecanismo equivalente y sus límites sin atribuir tests omitidos como aprobados.

## Evoluciones funcionales que no deben perderse

Estas son capacidades futuras o endurecimientos, no reconstrucción de submódulos implementados. Su priorización concreta se decide después del bloque activo.

| Dueño | Pendiente funcional/técnico |
|---|---|
| Admin/Identidad | Reconciliación durable/outbox de invitaciones y limpiezas Firebase pendientes; la respuesta explícita no asegura recuperación si el cliente pierde respuesta. |
| Maintenance | Reintento programado, participantes secundarios, adjuntos y después preventivos/activos/garantías. Entrega parcial elegida y aprobación separada de refacciones requieren corte propio. |
| Purchasing | Adjudicación parcial por línea entre proveedores, reintento programado de recepciones y paginación server-side. Factura/CxP/devolución al proveedor no implementadas. Definir política para actualizar costo base Inventory desde compra/recepción; el costo base sigue capturado. |
| Sales | Devoluciones cliente y facturación/cobranza. La conciliación explícita productiva/costo real CC-12 ya está implementada; un callback automático no es requisito de su cierre. Materiales para servicios comerciales siguen fuera del recorrido actual. PDF Pedido/remisión/Entrega con snapshot/artefacto inmutable y logo object storage antes de promover plantilla. |
| Production | Recepción de merma, medición real de eficiencia/mano de obra/maquinaria, borrador separado de liberación, calendarios tenant con turnos/festivos/ausencias/mantenimiento. Entregas parciales elegidas, rechazo productivo y receptor distinto requieren alcance propio. |
| Inventory | Escala server-side de Artículos, paginación de materiales elegibles para recetas y disponibilidad agregada para más de 200 combinaciones artículo/almacén. Cursor estable/carga en bandejas y asignación de usuarios por almacén. Lotes/series/cuarentena/bloqueos adicionales futuros; tránsito físico ya existe. |
| Sales/consumidores | Cursor contractual en Clientes, Cotizaciones, Pedidos, Servicios y Entregas antes de volumen productivo; la paginación visual de 25 no elimina límite API 200. |
| API/transversal | Completar envoltura `ErclaveError`, correlación entre servicios/CORS y respuestas comunes OpenAPI según cobertura pendiente; no duplicar mejoras parciales CHG-281. Consumidores externos de folios usan autoridad central o credencial interna de confianza, manteniendo compatibilidad explícita. |
| Negocio/fiscal | Decidir categoría jerárquica y semántica de área responsable antes de modelar. Diseñar catálogos fiscales/régimen/país/uso CFDI con factura/XML, autoridad y vigencia; no agregar listas parciales. |
| Reporting | XLSX/PDF, constructor, cruces, gráficas, vistas guardadas, programación/distribución; 28 reportes operativos simples por dueño ya están implementados. |

## Contabilidad y límites del alcance

CONT-09–18 (eventos/outbox, libros/cuentas/periodos, pólizas/reversas, fiscal/pagos/CxC/CxP y conciliación) y analítica Costing siguen planned. Su detalle y criterios viven en [CONTROL_CONTABLE](CONTROL_CONTABLE.md) y el [plan CONT](../arquitectura/plan_preparacion_contabilidad.md). No condicionan operación con Accounting apagado.

No crear infraestructura productiva, desplegar fuera del pipeline ni cargar datos QA sin autorización explícita. Los objetivos RPO 15 minutos/RTO 2 horas son futuros. No tratar tránsito, reservas de Maintenance ni sobrantes como ausentes: ya existen con limitaciones separadas.

## Regla de mantenimiento

Cerrar una fila sólo con implementación/evidencia y trazabilidad; si sólo cambia documentación, declarar ese límite. Las notas históricas no vuelven a abrir trabajo cerrado. Una brecha sin evidencia suficiente permanece explícita, con dueño y siguiente validación; no se elimina por antigüedad.
