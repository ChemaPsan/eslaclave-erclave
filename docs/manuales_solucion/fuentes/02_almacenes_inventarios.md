# Manual funcional de Almacenes e Inventarios

- Audiencia: almacenistas, supervisores, planeadores y responsables de recepción
- Alcance por ambiente: Local y QA
- Última revisión: 2026-09-06
- Capacidades cubiertas: almacenes, artículos, movimientos, existencias, Kardex, reservas, valuación, recepciones de compra y producto terminado

## Propósito

Almacenes e Inventarios es la autoridad de la existencia física. Los saldos y el Kardex se calculan a partir de movimientos inmutables; no son campos que se editen directamente.

## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Almacenes, artículos y movimientos | Disponible | Disponible |
| Existencias, Kardex y valuación promedio | Disponible | Disponible |
| Reservas/consumos de Producción, Ventas y Mantenimiento | Disponible | Disponible |
| Recepción de compras inventariables | Disponible | Disponible |
| Recepción de producto terminado | Disponible | Disponible |
| Lotes, series, cuarentena y ubicaciones operativas | No disponible | No disponible |

## Mapa del módulo

- **Almacenes:** maestros de ubicación y tipo operativo.
- **Artículos:** identidad logística, unidad, costo y elegibilidad.
- **Movimientos:** entradas, salidas, ajustes, reversas y recepciones especializadas.
- **Inventario:** existencias calculadas por artículo y almacén.
- **Kardex:** historia cronológica y valuada.
- **Portada:** reportes estándar de sólo lectura.

## Conceptos y campos principales

| Campo o concepto | Significado |
|---|---|
| Código | Identidad logística estable; puede asignarse mediante Administración. |
| Unidad base | Unidad en la que se interpreta toda la historia del artículo. |
| Costo unitario base | Referencia manual; la valuación promedio usa movimientos con costo cuando existen. |
| Usar en receta | Permite seleccionar el artículo como material productivo. |
| Producto terminado | Vínculo por ID con un producto comercial de Producción. |
| Existencia | Cantidad física calculada. |
| Reservado | Cantidad apartada por documentos operativos. |
| Disponible | Existencia menos reservas vigentes. |

## Acceso y permisos

Los permisos distinguen lectura, alta, modificación, reversa, reserva y recepciones especializadas. `inventory.movement.create` no concede `inventory.finished_goods_receipt.receive`. Compras y Mantenimiento utilizan permisos propios para solicitar operaciones limitadas; no reciben escritura general sobre Inventario.

## Crear un almacén o artículo

1. Cree el almacén con código, nombre, tipo y estado.
2. Para refacciones, use el tipo estable **Refacciones**; Mantenimiento sólo ofrece almacenes de ese tipo.
3. Cree el artículo con tipo, unidad base, costo y almacén sugerido.
4. Active **Usar en receta** sólo cuando sea material productivo.
5. Para producto terminado, vincúle el producto de Producción por su identidad estable.

La unidad debe existir y estar activa en Administración. Si el artículo ya tiene movimientos o reservas, no puede cambiarse a una unidad diferente. Los alias heredados administrados `LTS -> LTR` y `MT -> MTR` se normalizan sin alterar cantidades. Para un cambio real cree un artículo sustituto y regularice mediante movimientos autorizados.

## Registrar y consultar movimientos

1. Abra **Movimientos** y elija el tipo permitido.
2. Seleccione artículo y almacén mediante los buscadores.
3. Capture cantidad, fecha, costo cuando aplique y referencia del documento.
4. Confirme. La operación actualiza existencia y Kardex de forma atómica.
5. Si un movimiento fue incorrecto, use la reversa autorizada; no edite ni borre la historia.

Use **Inventario** para consultar saldos y **Kardex** para explicar cómo se formaron. Los filtros muestran resultados acotados y conservan los IDs aunque el nombre visible cambie.

## Reservas y consumos

Una reserva reduce disponible, no existencia. El consumo convierte la reserva en salida inmutable. Producción consume al iniciar, Ventas al confirmar una entrega, Mantenimiento al resolver con refacciones y Compras crea entradas al recibir partidas inventariables. Las claves idempotentes evitan duplicar movimientos en un reintento.

## Recibir una compra inventariable

Compras conserva proveedor, orden y recepción comercial. Inventario valida artículo, unidad, almacén y cantidad antes de crear la entrada. Si una recepción multipardida falla parcialmente, los movimientos ya confirmados permanecen y Compras reintenta sólo las líneas pendientes. Las compras de servicios no generan movimientos de Inventario.

## Recibir producto terminado

1. Confirme que la orden de Producción esté **Terminada** y el producto tenga artículo terminado vinculado.
2. Abra **Movimientos > Entradas de producción terminada**.
3. Revise folio, producto, unidad y cantidad pendiente.
4. Seleccione almacén, capture la cantidad físicamente recibida, fecha y observaciones.
5. Confirme la entrada.

Se permiten recepciones parciales y nunca puede superarse lo producido. Una reversa vuelve a incrementar el pendiente. El rol receptor sólo ve la proyección necesaria; no recibe receta, recursos ni costos completos de Producción.

## Conversiones y costos

Sólo se convierten unidades activas de la misma categoría con factor estándar. Cajas, paquetes y presentaciones empresariales requieren equivalencias futuras. El costo manual funciona como referencia cuando no existe saldo valuado; los movimientos con costo construyen el promedio. La política para actualizar costo base desde Compras sigue pendiente.

## Mensajes frecuentes

- **Unidad incompatible:** seleccione una unidad activa de la misma categoría.
- **La unidad base no puede cambiar:** proteja la historia y use un artículo sustituto.
- **Existencia insuficiente:** revise saldo, reservas concurrentes y almacén.
- **Movimiento duplicado:** reintente con la misma operación; no capture otra salida o entrada.
- **Falta vínculo de producto terminado:** relacione el producto con un artículo activo.
- **La cantidad excede lo pendiente:** capture sólo el saldo físicamente recibido.
- **Crea primero un almacén de refacciones:** registre o active uno de tipo `spare_parts`.

## Integraciones y propiedad del dato

Producción solicita reservas, consumos y candidatos de producto terminado; Ventas solicita reservas y consumos para entregas; Compras solicita entradas de recepción; Mantenimiento reserva y consume refacciones. Inventario decide la validez física y conserva el movimiento, costo y Kardex. Ningún consumidor escribe sus tablas.

## Reportes estándar de portada (Local)

La portada genera reportes descargables de almacenes, artículos, saldos de inventario, movimientos/Kardex y críticos con reservas superiores a la existencia. Abra una tarjeta, seleccione los filtros mínimos disponibles y pulse **Generar**. Puede escribir para encontrar tipo, categoría, estatus, condición o movimiento; la búsqueda general acepta texto libre y el periodo usa fechas. Un resultado vacío se informa sin crear archivo.

La descarga usa los permisos existentes `inventory.warehouse.read`, `inventory.item.read`, `inventory.balance.read` o `inventory.kardex.read`. Los reportes operan sólo en Local en este corte y consultan exclusivamente datos propiedad de Inventario.

## Limitaciones vigentes

No incluye lotes, series, cuarentena, inventario bloqueado o en tránsito, ubicaciones operativas detalladas, equivalencias de empaque ni recepción de merma. El catálogo de artículos requiere evolución server-side antes de volúmenes muy altos.

## Soporte

Conserve código de artículo, almacén, referencia documental, fecha y correlación. No modifique la base ni cree movimientos compensatorios improvisados para ocultar una conciliación pendiente.
