# Registro de manuales funcionales

Última revisión documental: 2026-09-14.

Se actualizaron las siete fuentes y la guía para el candidato Local. La revisión visual anterior de 47 páginas corresponde al corte del 10 de septiembre y no certifica esta edición. Los resultados funcionales siguen por registrar; los casos nuevos no se presentan como desplegados en QA.

Todos los módulos incorporan instrucciones de corrección de formularios. Producción agrega margen esperado sin tope de negocio, evidencia de recepción y cierre en el avance, límites, optimización, permisos y vencimiento de todos los adjuntos a 365 días.

| Módulo | Fuente canónica | Word vigente | Cobertura actual | Ambiente descrito | Limitaciones principales |
|---|---|---|---|---|---|
| Producción | `fuentes/01_produccion.md` | `word/01_produccion.docx` | Productos, recetas, maquinaria, capacidad multídía, órdenes, salida previa por Almacén, etapas, sobrantes, producto terminado y CSV estándar | Local y QA b63cdad | Calendario configurable, merma y borrador separado de liberación |
| Almacenes | `fuentes/02_almacenes_inventarios.md` | `word/02_almacenes_inventarios.docx` | Almacenes, artículos, movimientos, balances, Kardex, reservas, confirmaciones físicas, transferencias, sobrantes y CSV estándar | Local y QA b63cdad | Lotes, series, cuarentena, empaque y merma |
| Compras | `fuentes/03_compras_abastecimiento.md` | `word/03_compras_abastecimiento.docx` | Proveedores, requisiciones, órdenes, recepciones preparadas, aceptación por solicitante, conciliación y CSV estándar | Local y QA b63cdad | Multi-proveedor, devoluciones, factura, CxP y pagos |
| Ventas | `fuentes/04_ventas_clientes.md` | `word/04_ventas_clientes.docx` | Clientes, cotizaciones, pedidos, surtido, entregas confirmadas por Almacén, órdenes de servicio y CSV estándar | Local y QA b63cdad | Devoluciones, factura, cobranza, PDF y paginación |
| Administración | `fuentes/08_administracion_configuracion.md` | `word/08_administracion_configuracion.docx` | Sesión, organización, usuarios, roles, permisos, módulos, catálogos y Backoffice | Local y QA | Billing/provisioning automático y reconciliación durable Firebase |
| Recursos Humanos | `fuentes/10_recursos_humanos.md` | `word/10_recursos_humanos.docx` | Áreas, puestos, trabajadores, capacidad, elegibilidad operativa y CSV estándar | Local y QA b63cdad | Nómina, ausencias, calendarios y documentos |
| Mantenimiento | `fuentes/11_mantenimiento.md` | `word/11_mantenimiento.docx` | Correctivos, asignación, tiempo, refacciones, bloqueo, entrega por Almacén, recuperación, sobrantes y CSV estándar | Local y QA b63cdad | Preventivos, activos generales, adjuntos y reintento automático programado |

## Módulos sin manual operativo

Gastos/Cuentas por pagar, Costos, Reportes avanzados y Contabilidad continúan definidos como módulos planeados. No se generan manuales Word de uso hasta que exista un runtime y una interfaz verificables; hacerlo antes mezclaría arquitectura objetivo con capacidades disponibles.

## Criterio de vigencia

La pareja `fuentes/<módulo>.md` + `word/<módulo>.docx` es la única versión distribuible. Si una fuente y su Word difieren, prevalece la fuente y el Word debe regenerarse antes de publicarse.

## Referencia y validación funcional

Pendiente funcional identificado: comprobar o corregir el montaje de la bandeja de devolución de sobrantes en Mantenimiento. La API existe, pero el selector usado para insertar la bandeja no corresponde al contenedor renderizado. Responsables: agente técnico de Mantenimiento y QA. El manual y la guía distinguen el procedimiento previsto del acceso aún por validar.

Base desplegada: `b63cdad2fbac423c24460e55582ccfc0003e9924`, desplegada en QA. Los procedimientos se contrastaron con código, interfaz, permisos, contratos y pruebas del corte. La aceptación funcional con usuarios reales permanece pendiente de ejecución por el tester; no se declara aprobada por regenerar estos documentos. La guía de pruebas incluye resultados por registrar y precondiciones explícitas para casos restringidos.

## Validación de esta edición (2026-09-14)

Ocho DOCX regenerados y reabiertos estructuralmente: todos los fragmentos de las ocho fuentes están presentes. **Revisión visual pendiente; no distribuir todavía los Word como edición final**. render_docx.py no pudo iniciar por falta de LibreOffice en el runtime; la alternativa Word Automation quedó bloqueada y se cerró únicamente su instancia de revisión. No se certifican páginas, tablas ni saltos visuales con la comprobación de texto.

Guía y matriz:65 casos únicos (56 base +9 del candidato). Las fuentes Markdown están actualizadas y revisables. Al completar la revisión visual, sustituir este estado por la evidencia real, sin reutilizar la revisión de47 páginas de la edición anterior.
