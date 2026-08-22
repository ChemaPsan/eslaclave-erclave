# Seleccion escalable de maestros y documentos

## Principio

Un `select` HTML es adecuado para catalogos pequenos y estables. Entidades que crecen con la operacion deben usar busqueda por texto, filtros de negocio, elegibilidad server-side, paginacion y resultados acotados. La UI conserva el ID seleccionado; nunca resuelve relaciones por el texto mostrado.

## Matriz recomendada

| Seleccion | Busqueda principal | Filtros ideales | Orden inicial | Elegibilidad |
|---|---|---|---|---|
| Cliente | codigo, nombre comercial, razon social, RFC, contacto | estatus, responsable, moneda, condiciones | recientes / nombre | activo y mismo tenant |
| Producto o servicio | codigo, nombre, categoria | tipo, estatus, unidad, responsable | relevancia / codigo | activo; producto con articulo terminado vinculado cuando aplique |
| Cotizacion para Pedido | folio, cliente, producto | aprobada, vigencia, responsable, moneda, rango de importe | aprobacion mas reciente | aprobada, vigente y sin pedido activo |
| Pedido para Entrega | folio, cliente, producto | estatus, modo de surtido, fecha prometida, responsable | fecha prometida mas cercana | no cancelado/cerrado y con cantidad entregable |
| Orden de compra | folio, proveedor, articulo | estatus, almacen destino, comprador, fecha esperada | fecha esperada mas cercana | aprobada/abierta y con saldo por recibir |
| Recepcion | orden, proveedor, articulo | almacen, fecha, recepcion parcial | recientes | orden con saldo pendiente |
| Orden de Produccion | folio, producto, receta | estatus, prioridad, responsable, fecha requerida | prioridad y fecha | compatible con la accion solicitada |
| Articulo de Inventario | SKU, nombre, categoria | tipo, estatus, almacen, unidad, politica, disponibilidad | SKU / relevancia | activo y compatible con unidad/operacion |
| Trabajador | nombre, numero, puesto, area | estatus, area, puesto, elegibilidad | nombre | trabajador, puesto y area activos |
| Almacen | codigo, nombre, ubicacion | tipo, estatus, centro | codigo | activo y permitido para la operacion |

## Comportamiento minimo

- Esperar una pausa corta antes de consultar cuando la busqueda sea remota.
- No traer ni renderizar miles de filas; usar cursor y limite.
- Mostrar codigo, nombre, estado y dos datos que expliquen por que elegir el registro.
- Permitir combinar terminos, por ejemplo `cliente vela listo`.
- Mostrar solo elegibles por defecto y ofrecer un filtro explicito para revisar descartados cuando sea util.
- Conservar seleccion por ID, anunciar cero resultados y permitir limpiar.
- Soportar teclado, foco, lectores de pantalla y pantallas angostas.
- Revalidar elegibilidad en backend al guardar porque el estado puede cambiar durante la captura.

## Estado de implementacion

CHG-209 extiende el patrón Local a todas las referencias crecientes presentes en los módulos implementados. El componente transversal conserva el ID en el `select` fuente, permite buscar sin acentos por código o nombre, limita a 20 coincidencias visibles, exige elegir un resultado real, se actualiza cuando cambia el catálogo y admite teclado. Los buscadores especializados de documentos de CHG-208 se conservan porque además calculan elegibilidad y muestran contexto de negocio.

| Modulo | Referencias crecientes cubiertas | Tratamiento |
|---|---|---|
| Administracion | rol, sucursal activa y entidad legal | búsqueda por texto sobre catálogo autorizado |
| Produccion | receta, artículo vinculado, área de maquinaria, recursos, responsable y responsables por etapa | búsqueda por identidad visible; relación guardada por ID |
| Almacenes | artículo, almacén origen/destino, almacén sugerido y filtros de Inventario/Kárdex | búsqueda por código y nombre; backend revalida compatibilidad |
| Ventas | cliente, producto/servicio, responsable, cotización, pedido y almacén de surtido | lookup especializado en documentos y lookup transversal en maestros |
| Recursos Humanos | área y puesto | búsqueda por código, nombre, puesto o área según la etiqueta disponible |
| Backoffice | no existen referencias operativas crecientes en formularios actuales | sin cambio; activar módulos sigue siendo una lista acotada de configuración |
| Compras, Gastos, Costos, Contabilidad y Reportes | flujos todavía planeados | deberán adoptar el patrón al incorporar maestros o documentos reales |

## Catalogos cerrados

Estatus, tipo, prioridad, moneda, condición de pago, política, modo de surtido y otros conjuntos pequeños y gobernados permanecen como `select` nativo. No deben convertirse mecánicamente en buscadores: su lista completa ayuda a comprender las opciones y sus transiciones. Si uno de esos catálogos pasa a ser administrable y crece significativamente, se reclasifica como referencia creciente.

La API mantiene hoy el límite preventivo de 200 en varios catálogos. Antes de superar ese volumen, cada servicio propietario debe exponer búsqueda, filtros y paginación contractual; el componente no sustituye la consulta server-side ni autoriza descargar catálogos completos.

## Regla para cambios futuros

- Toda nueva selección de maestro o documento debe declararse buscable desde el primer corte.
- La relación siempre se guarda por ID estable y se revalida en el backend.
- El resultado debe mostrar una identidad comprensible; nunca un ID técnico aislado.
- Cero coincidencias, registro inelegible y permiso faltante deben tener mensajes distintos.
- El validador `npm.cmd run validate:selectors` protege la cobertura transversal existente.
