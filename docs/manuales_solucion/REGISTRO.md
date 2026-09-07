# Registro de manuales funcionales

Última revisión documental: 2026-09-06.

| Módulo | Fuente canónica | Word vigente | Cobertura actual | Ambiente descrito | Limitaciones principales |
|---|---|---|---|---|---|
| Producción | `fuentes/01_produccion.md` | `word/01_produccion.docx` | Productos, recetas, maquinaria, capacidad multídía, órdenes, etapas, producto terminado y CSV estándar | Operación Local/QA; CSV sólo Local | Calendario configurable, merma y borrador separado de liberación |
| Almacenes | `fuentes/02_almacenes_inventarios.md` | `word/02_almacenes_inventarios.docx` | Almacenes, artículos, movimientos, balances, Kardex, reservas, recepciones y CSV estándar | Operación Local/QA; CSV sólo Local | Lotes, series, cuarentena, empaque y merma |
| Compras | `fuentes/03_compras_abastecimiento.md` | `word/03_compras_abastecimiento.docx` | Proveedores, requisiciones, órdenes, recepciones, conciliación y CSV estándar | Inventariable Local/QA; servicios y CSV sólo Local | Multi-proveedor, devoluciones, factura, CxP y pagos |
| Ventas | `fuentes/04_ventas_clientes.md` | `word/04_ventas_clientes.docx` | Clientes, cotizaciones, pedidos, surtido, entregas, órdenes de servicio y CSV estándar | Base Local/QA; órdenes de servicio y CSV sólo Local | Devoluciones, factura, cobranza, PDF y paginación |
| Administración | `fuentes/08_administracion_configuracion.md` | `word/08_administracion_configuracion.docx` | Sesión, organización, usuarios, roles, permisos, módulos, catálogos y Backoffice | Local y QA | Billing/provisioning automático y reconciliación durable Firebase |
| Recursos Humanos | `fuentes/10_recursos_humanos.md` | `word/10_recursos_humanos.docx` | Áreas, puestos, trabajadores, capacidad, elegibilidad operativa y CSV estándar | Operación Local/QA; CSV sólo Local | Nómina, ausencias, calendarios y documentos |
| Mantenimiento | `fuentes/11_mantenimiento.md` | `word/11_mantenimiento.docx` | Correctivos, asignación, tiempo, refacciones, bloqueo, conciliación y CSV estándar | Operación Local/QA; CSV sólo Local | Preventivos, activos generales, sobrantes, adjuntos y reintento automático |

## Módulos sin manual operativo

Gastos/Cuentas por pagar, Costos, Reportes avanzados y Contabilidad continúan definidos como módulos planeados. No se generan manuales Word de uso hasta que exista un runtime y una interfaz verificables; hacerlo antes mezclaría arquitectura objetivo con capacidades disponibles.

## Criterio de vigencia

La pareja `fuentes/<módulo>.md` + `word/<módulo>.docx` es la única versión distribuible. Si una fuente y su Word difieren, prevalece la fuente y el Word debe regenerarse antes de publicarse.
