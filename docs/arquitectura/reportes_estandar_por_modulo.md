# Reportes estandar por modulo

## Decision funcional

La primera vista de cada modulo operativo es un centro de consulta de solo lectura. No crea documentos, movimientos ni maestros y no presenta botones de alta. Las acciones operativas viven exclusivamente en el submodulo que es dueño del proceso.

**Administracion es la excepcion deliberada:** su raiz conserva el centro de configuracion porque usuarios, roles, permisos, organizacion, catalogos y modulos activos se gobiernan desde ahi. Convertir esa portada en reporte impediria administrar el sistema.

Los reportes estandar consultan catalogos, estados y documentos propios de un solo modulo. El modulo independiente **Reportes** se reserva para analisis especializados: cruces entre modulos, tableros configurables, indicadores avanzados, vistas guardadas, distribucion y reportes a la medida. Permanece inactivo en el corte actual.

## Catalogo minimo por modulo

| Modulo | Reportes estandar de portada |
|---|---|
| Produccion | productos y servicios; recetas/versiones; ordenes; entregables por area; maquinaria |
| Almacenes | almacenes; articulos; inventario; movimientos/Kardex; criticos y reservas |
| Recursos Humanos | areas/puestos; trabajadores; capacidad productiva; elegibilidad |
| Ventas | clientes; cotizaciones; pedidos; entregas; margen comercial; ordenes de servicio |
| Administracion | Excepcion: conserva su centro de configuracion; sus consultas acompañan las pantallas administrativas |
| Compras | proveedores; requisiciones; ordenes de compra; recepciones |
| Mantenimiento | ordenes; indisponibilidad; refacciones; tiempos de mano de obra |
| Gastos | documentos; gastos; cuentas por pagar; pagos |
| Costos | centros de costos; costo estimado; costo real; variaciones; rentabilidad |
| Contabilidad | cuentas; periodos; asientos/polizas; mapeos; anexos |
| Reportes | analisis especializados planeados; sin activacion ni datos en este corte |

Los modulos planeados muestran esta definicion solamente como contrato funcional. No se afirma que sus consultas, datos o exportaciones existan antes de que el modulo sea implementado y activado.

## Comportamiento de la portada

- Presenta indicadores de lectura, catalogo de reportes, filtros sugeridos, fuentes propias y una vista previa cuando existen datos.
- No contiene alta rapida, generacion de orden, sincronizacion, captura ni otra mutacion de negocio.
- El boton operativo global se oculta mientras el usuario permanece en la raiz de un modulo operativo.
- Entrar a un submodulo restaura las acciones que correspondan a permisos, estado y reglas del proceso.
- Cada consulta respeta tenant, permisos y alcance. Que una portada sea de solo lectura no elimina la autorizacion requerida por sus endpoints fuente.
- Cero datos se informa como estado vacio y no se sustituye con registros mock en modo API.

## Exportacion estandar implementada en Local

CHG-256 convierte las tarjetas de Produccion, Almacenes, Recursos Humanos, Ventas, Compras y Mantenimiento en consultas ejecutables. Cada tarjeta abre un modal bilingue con solo los filtros indispensables y descarga un CSV desde el servicio propietario. Administracion conserva su excepcion de configuracion y los modulos planeados no ofrecen descargas.

CHG-257 simplifica la experiencia sin cambiar el contrato tecnico: las tarjetas, el modal y la confirmacion muestran solamente **Generar** y **Reporte generado**, sin exponer el formato del archivo al usuario. Los filtros de catalogo cerrado (estatus, prioridad, tipo, moneda, condicion, movimiento, elegibilidad, proposito y objetivo) permiten escribir para buscar y despues seleccionar un valor valido; las fechas conservan su selector nativo, la busqueda general acepta texto libre y categoria ofrece sugerencias sin impedir valores propios del tenant.

| Modulo | Codigos de reporte | Filtros visibles basicos |
|---|---|---|
| Produccion | `product-services`, `recipe-versions`, `orders`, `deliverables-by-area`, `machines` | busqueda, tipo, estatus, prioridad y periodo segun el reporte |
| Almacenes | `warehouses`, `items`, `balances`, `kardex`, `critical-reservations` | busqueda, tipo, categoria, estatus, condicion y periodo segun el reporte |
| Recursos Humanos | `areas-positions`, `workers`, `production-capacity`, `eligibility` | estatus, elegibilidad o proposito; capacidad representa configuracion propia de RH, no compromisos de Produccion |
| Ventas | `customers`, `quotes`, `orders`, `deliveries`, `commercial-margin`, `service-orders` | busqueda, estatus y periodo segun el reporte |
| Compras | `suppliers`, `requisitions`, `orders`, `receipts` | busqueda, moneda, estatus, prioridad y periodo segun el reporte |
| Mantenimiento | `orders`, `downtime`, `spare-parts`, `labor-times` | periodo, estatus, prioridad, objetivo y busqueda segun el reporte |

La ruta uniforme es `GET /v1/{modulo}/reports/{report_code}/export`. El backend valida tenant, modulo y el permiso de lectura exacto asociado al codigo fijo; no acepta SQL, columnas ni fuentes elegidas por el cliente. Cada consulta se limita al schema propietario y no introduce lecturas cruzadas entre servicios.

El CSV usa UTF-8 con BOM para compatibilidad con Excel, dialecto RFC 4180, encabezados ES/EN, fechas ISO y numeros sin formato visual. Las cadenas que podrian interpretarse como formulas se neutralizan. Un resultado vacio responde `204` y la UI lo informa sin descargar un archivo inutil; las consultas se limitan a 50 000 filas y solicitan reducir filtros cuando exceden ese maximo.

No se exportan identificadores sensibles de trabajadores (CURP, RFC, NSS, telefono, correo o domicilio), datos fiscales/contacto innecesarios de clientes ni perfil fiscal/contacto de proveedores. Se reutilizan permisos de lectura existentes; CHG-256 no agrega permisos, migraciones, seeds ni tablas.

## Regla para modulos futuros

Todo modulo operativo nuevo debe declarar su catalogo de reportes estandar antes de activar su primera ruta. Si aun no tiene una configuracion propia, la UI genera una definicion conservadora a partir de sus submodulos, pero el equipo debe especializar nombres, dimensiones, filtros, permisos y fuentes antes de certificarlo. Un modulo de gobierno o configuracion puede solicitar una excepcion documentada como Administracion.

Agregar una mutacion a la portada del modulo requiere una nueva decision funcional; no debe introducirse como conveniencia de interfaz. El guardrail `npm.cmd run validate:module-reports` protege esta separacion.

## Evolucion pendiente

Las tarjetas operativas ya ejecutan filtros basicos y exportan CSV desde el servicio propietario. XLSX con formato, PDF, paginacion avanzada, vistas guardadas, programacion, distribucion, graficas y cruces entre propietarios permanecen fuera de este corte. Esas capacidades se diseñaran dentro del modulo Reportes y no mediante lecturas cruzadas directas entre schemas.
