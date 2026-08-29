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
| Ventas | clientes; cotizaciones; pedidos; entregas; margen comercial |
| Administracion | Excepcion: conserva su centro de configuracion; sus consultas acompañan las pantallas administrativas |
| Compras | proveedores; requisiciones; ordenes de compra; recepciones |
| Mantenimiento | ordenes/backlog; indisponibilidad; espera de refacciones; tiempos/MTTR; consumo y costo; recurrencia |
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

## Regla para modulos futuros

Todo modulo operativo nuevo debe declarar su catalogo de reportes estandar antes de activar su primera ruta. Si aun no tiene una configuracion propia, la UI genera una definicion conservadora a partir de sus submodulos, pero el equipo debe especializar nombres, dimensiones, filtros, permisos y fuentes antes de certificarlo. Un modulo de gobierno o configuracion puede solicitar una excepcion documentada como Administracion.

Agregar una mutacion a la portada del modulo requiere una nueva decision funcional; no debe introducirse como conveniencia de interfaz. El guardrail `npm.cmd run validate:module-reports` protege esta separacion.

## Evolucion pendiente

Las tarjetas actuales describen las consultas y presentan la vista operativa ya disponible. Filtros ejecutables, paginacion, exportacion PDF/Excel y endpoints agregados se implementaran por servicio propietario cuando cada reporte lo requiera. Los analisis que mezclen propietarios se diseñaran dentro del modulo Reportes y no mediante lecturas cruzadas directas entre schemas.
