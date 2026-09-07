# Manual funcional de Producción

- Audiencia: planeadores, supervisores, responsables de etapa y personal de producción
- Alcance por ambiente: Local y QA
- Última revisión: 2026-09-06
- Capacidades cubiertas: productos y servicios, recetas versionadas, maquinaria, planeación multídía, órdenes, etapas y entrega de producto terminado

## Propósito

Producción define qué se fabrica, con qué receta y recursos, durante qué horizonte y cómo se confirma el avance. El servicio conserva la definición productiva y solicita a otros módulos las validaciones que les pertenecen; nunca modifica directamente Inventario o Recursos Humanos.

## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Productos/servicios y recetas versionadas | Disponible | Disponible |
| Órdenes, etapas y avance ponderado | Disponible | Disponible |
| Reservas y consumo de materiales | Disponible | Disponible |
| Capacidad laboral y de maquinaria multídía | Disponible | Disponible |
| Recepción de producto terminado en Almacenes | Disponible | Disponible |
| Calendarios configurables, turnos, festivos y ausencias | No disponible | No disponible |

## Mapa del módulo

- **Productos y servicios:** catálogo maestro productivo.
- **Recetas:** versiones, recursos, fases, pesos y aprobación.
- **Órdenes:** liberación, planeación y transiciones operativas.
- **Entregables por área:** avance y terminación de fases.
- **Maquinaria:** capacidad, área responsable y estado de mantenimiento.
- **Portada:** reportes estándar de sólo lectura; las altas viven en los submódulos.

## Conceptos principales

| Concepto | Significado |
|---|---|
| Producto/servicio | Resultado que Producción puede fabricar o ejecutar. |
| Receta | Definición controlada de materiales, mano de obra, maquinaria y fases. |
| Versión | Corte inmutable usado por una orden; cambios posteriores no alteran la historia. |
| Peso de fase | Contribución de una fase al avance total; las fases activas suman 100%. |
| Orden liberada | Orden creada después de validar y reservar materiales y capacidad. |
| Días productivos | Horizonte usado para distribuir capacidad de lunes a viernes en el corte actual. |

## Acceso, permisos y prerrequisitos

Los permisos son granulares. Crear o editar una receta no concede aprobarla; iniciar una orden no concede terminarla; actualizar avance no concede declarar una etapa terminada. Entre los permisos relevantes están `production.recipe.*`, `production.order.*`, `production.order_stage.*` y `production.machine.*`.

Antes de liberar una orden deben existir:

- producto activo y versión de receta aprobada;
- materiales elegibles de Almacenes con unidad activa;
- puestos, áreas y trabajadores productivos vigentes en RH;
- maquinaria activa o disponible para el horizonte;
- permisos y entitlements vigentes para el tenant.

La alta actual de una orden valida, reserva y nace liberada en una sola operación. No existe todavía un borrador separado de la liberación.

## Crear y aprobar una receta

1. Abra **Producción > Recetas** y seleccione el producto o servicio.
2. Capture o reserve el código según la configuración de Administración.
3. Defina cantidad base, unidad, centro de costos y vigencia.
4. Agregue materiales, puestos y maquinaria mediante los buscadores de catálogo.
5. Defina las fases, áreas responsables y su secuencia.
6. Asigne pesos y confirme que las fases activas sumen 100%.
7. Use **Validar definición**, envíe la versión y apruébela con el permiso correspondiente.

**Validar definición** comprueba identidad, unidad y elegibilidad. La disponibilidad real se evalúa al liberar una orden, porque depende de cantidad, fecha y horizonte. Una receta puede ser válida aunque hoy no exista inventario o capacidad suficiente.

## Liberar y ejecutar una orden

1. Seleccione una receta aprobada, cantidad, inicio planeado, días productivos, fecha requerida, prioridad y responsables.
2. Revise el horizonte y el desglose diario de material, mano de obra y maquinaria.
3. Confirme la liberación. Inventario reserva material y Producción compromete capacidad.
4. Inicie la orden. La primera entrada a **En producción** consume las reservas y crea salidas en Inventario.
5. Actualice cada fase desde **Entregables por área**. El avance general se calcula con sus pesos.
6. Cuando todas las fases lleguen a 100%, envíe o deje pasar la orden a **En validación**.
7. Termine la orden. El cierre consolida costos y no vuelve a descontar materiales.

Una pausa, reanudación o regreso desde validación no crea otra salida. Cancelar antes de iniciar libera reservas; cancelar después conserva las salidas físicas ya registradas.

## Estados de la orden

| Estado | Significado y acciones |
|---|---|
| Liberada | Recursos apartados; puede iniciar, esperar recursos o cancelarse. |
| En espera de recursos | Existe una restricción o conciliación pendiente. |
| En producción | Trabajo activo; los materiales reservados ya fueron consumidos una sola vez. |
| Pausada | Detención temporal con causa; puede reanudarse cuando la restricción desaparece. |
| En validación | Las fases terminaron y el resultado espera revisión. |
| Terminada | Cierre operativo; habilita la recepción física en Almacenes. |
| Cancelada | Estado terminal con reservas compensadas cuando corresponda. |

## Maquinaria y Mantenimiento

Una máquina puede pertenecer a una receta aunque no esté disponible hoy. Si Mantenimiento bloquea una máquina, Producción impide usarla y puede pausar la orden relacionada. Resolver Mantenimiento libera la máquina, pero nunca reanuda automáticamente Producción: el operador debe volver a validar y decidir.

## Producto terminado

Al terminar una orden, Producción expone a Almacenes una proyección mínima: folio, producto vinculado, cantidad, unidad y costo unitario. El almacenista confirma una o varias recepciones. Producción no incrementa existencias por sí misma y no expone receta, responsables o costos completos al rol receptor.

## Mensajes frecuentes

- **Receta aprobada vigente requerida:** seleccione una versión aprobada y activa.
- **Los porcentajes deben sumar 100:** corrija los pesos de fase.
- **Recurso no disponible:** revise existencia, reserva concurrente, trabajador, máquina u horizonte.
- **Capacidad laboral insuficiente:** active trabajadores en el puesto exacto requerido.
- **Unidad de medida no activa:** corrija el artículo o use una unidad vigente; no altere historia con movimientos.
- **Todas las fases deben tener 100%:** regrese a **En producción** y complete las fases pendientes.
- **Maquinaria en mantenimiento:** espere liberación y vuelva a validar la orden.

## Integraciones y propiedad del dato

- Administración es autoridad de unidades, folios, permisos y entitlements.
- RH es autoridad de áreas, puestos, trabajadores y elegibilidad.
- Inventario es autoridad de artículos, almacenes, existencias, reservas, movimientos y Kardex.
- Mantenimiento solicita bloqueo o liberación; Producción decide la transición válida.
- Ventas puede crear solicitudes de producción, pero no libera una orden automáticamente.

## Reportes estándar de portada (Local)

La portada ofrece cinco reportes descargables: productos y servicios, recetas y versiones, órdenes, entregables por área y maquinaria. Abra la tarjeta, capture sólo los filtros necesarios y pulse **Generar**. Puede escribir para encontrar tipo, estatus o prioridad; la búsqueda general acepta texto libre y el periodo usa fechas. Si no hay coincidencias se informa el estado vacío y no se descarga un archivo.

Cada reporte exige el permiso de lectura del recurso: `production.product_service.read`, `production.recipe.read`, `production.order.read` o `production.machine.read`. Estas descargas están disponibles sólo en Local en este corte; Reportes conservará los cruces, gráficas, PDF y Excel con formato.

## Limitaciones vigentes

No están disponibles calendario configurable por tenant, turnos, festivos, ausencias, merma recibida, captura obligatoria de eficiencia real ni borrador separado de liberación. Los análisis configurables pertenecen a Reportes.

## Soporte y trazabilidad visible

Conserve folio de orden, estado, fase, fecha y referencia de correlación cuando aparezca. No registre salidas manuales para corregir una integración pendiente: reintente desde la acción autorizada o escale a soporte.
