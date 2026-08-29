# Manual funcional de Almacenes e Inventarios

- Audiencia: almacenistas, supervisores y planeadores
- Alcance por ambiente: Local y QA
- Ultima revision: 2026-08-24
- Capacidades cubiertas: articulos, costo unitario, conversiones y vinculo con Produccion

## Proposito

Almacenes conserva identidad logistica, unidad, costo y movimientos. Kardex y existencias son resultados, no campos editables.

## Campos principales

| Campo | Significado |
|---|---|
| Codigo | Identidad logistica; puede venir de Administracion. |
| Unidad base | Unidad en que se controla el articulo. |
| Costo unitario base | Costo manual de un kg, L, pieza u otra unidad base. |
| Usar en receta | Hace elegible el articulo como material. |
| Producto terminado | Puede vincularse por ID a un producto comercial. |

## Crear o editar

1. Seleccione tipo, unidad y almacen sugerido.
2. Capture el costo por una unidad base, no por otra presentacion.
3. Marque **Usar en receta** solo si se consumira como material.
4. Para producto terminado, seleccione opcionalmente el producto de Produccion. El nombre logistico puede diferir del comercial.
5. Si el articulo se crea pero el vinculo falla, reintente sin duplicarlo.

La unidad base debe pertenecer al catalogo activo de Administracion. Cuando un articulo ya tiene movimientos o reservas, la unidad no puede cambiarse porque alteraria la interpretacion de su historia. Los alias heredados reconocidos por Administracion (`LTS` como `LTR` y `MT` como `MTR`) se normalizan sin cambiar cantidades, costo ni identidad. Para cualquier cambio real de unidad, cree un articulo sustituto y regularice las existencias mediante movimientos autorizados.

## Consultar inventario

Los filtros de articulo, almacen y otras entidades son buscables. Al abrir un selector se muestra el catalogo disponible; escriba codigo, nombre u otro dato visible para reducir resultados. Elegir **Todos los almacenes** quita el filtro. La tabla sigue siendo la fuente de existencias calculadas por articulo y almacen.

## Conversiones

Solo se convierten unidades activas, de la misma categoria y con factor estandar. Si un kg cuesta 80, un gramo cuesta 0.08. Si un litro cuesta 50, un mililitro cuesta 0.05.

Cajas, paquetes y unidades personalizadas no se convierten automaticamente porque requieren una equivalencia empresarial futura.

## Reglas e integraciones

Produccion usa el costo unitario base para estimar materiales. Los movimientos con costo construyen valuacion promedio; el costo manual es fallback sin saldo valuado. Compras actualizara el dato desde adquisiciones en un corte futuro. Produccion es propietaria del vinculo producto-articulo.

Una orden liberada crea reservas y reduce la cantidad disponible, no la existencia fisica. La primera entrada de la orden a **En produccion** consume esas reservas y registra una salida inmutable en el almacen que suministro cada material. Reanudar o terminar la orden no vuelve a descontar. Cancelar antes de iniciar libera las reservas; cancelar despues conserva las salidas ya registradas. No registre una salida manual duplicada para el mismo consumo.

## Recibir producto terminado

En Local, consultar pendientes exige `inventory.finished_goods_receipt.read` y confirmar la recepcion fisica exige `inventory.finished_goods_receipt.receive`. El permiso general para crear movimientos no habilita esta accion. Produccion entrega exclusivamente folio, producto vinculado, cantidad, unidad, estado terminado y costo unitario para valuacion; el rol receptor no obtiene la receta, recursos, responsable ni costos totales. Esto permite reservar la confirmacion al rol de almacen definido por cada tenant.

1. Confirme en Produccion que la orden ya esta **Terminada** y que su producto esta vinculado con un articulo activo de tipo producto terminado.
2. Abra **Almacenes > Movimientos**. En **Entradas de produccion terminada** se muestran las ordenes con cantidad pendiente de recibir.
3. Pulse **Recibir producto terminado**.
4. Valide el almacen de destino, capture la cantidad fisicamente recibida, fecha y observaciones.
5. Confirme la entrada. El sistema crea un movimiento ligado a la orden y actualiza existencia, Kardex y cantidad pendiente.

Se permiten recepciones parciales. La suma nunca puede exceder la cantidad terminada; una orden totalmente recibida deja de aparecer como pendiente. El articulo, la unidad y el costo se derivan de maestros y de la orden, no se capturan manualmente. El costo unitario usa el costo real disponible de la orden dividido entre la cantidad producida y, si aun no existe, su costo planeado. Una recepcion reversada vuelve a dejar cantidad pendiente.

## Mensajes frecuentes

- **Unidad incompatible:** seleccione una unidad de la misma categoria.
- **La unidad base no puede cambiar:** el articulo tiene movimientos o reservas. Si no es un alias administrado, use un articulo sustituto y regularice existencias.
- **Conversion no soportada:** use la unidad base o configure una equivalencia futura.
- **Articulo creado; vinculo pendiente:** reintente el vinculo, no cree otro articulo.
- **La orden no esta terminada:** complete y valide primero el flujo de Produccion.
- **Falta vinculo de producto terminado:** vincule el producto comercial con un articulo logistico activo.
- **La cantidad excede lo pendiente:** capture solo el saldo fisicamente pendiente de recibir.

## Cobertura

Revisado con especialistas de Inventarios, Produccion y Ventas. Lotes, series y equivalencias de empaque quedan fuera del corte.
