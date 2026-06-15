# ERClave — Módulo de Almacenes e Inventarios

## 1. Objetivo

El módulo de Almacenes e Inventarios permitirá controlar existencias, movimientos, ubicaciones, reservas, consumos, producto en proceso, producto terminado, merma y trazabilidad de recursos.

Su propósito es conectar la operación física con producción, compras, ventas y costos.

---

## 2. Alcance

- almacenes configurables;
- tipos de almacén;
- ubicaciones fisicas internas como configuracion opcional del almacen;
- catalogo maestro de articulos inventariables;
- existencias;
- existencias calculadas desde movimientos;
- entradas;
- salidas;
- transferencias;
- reservas;
- ajustes;
- merma;
- kardex;
- inventario en proceso;
- producto terminado;
- mínimos, máximos y puntos de reorden.

---

## 3. Tipos de almacén

| Tipo | Uso |
|---|---|
| Materias primas | Insumos consumibles. |
| Herramientas | Recursos reutilizables. |
| Maquinaria | Equipos productivos o activos operativos. |
| Producto en proceso | Producción no terminada. |
| Producto terminado | Inventario listo para vender o entregar. |
| Desechos | Merma, scrap o desperdicio. |
| Refacciones | Piezas para mantenimiento. |
| Servicios | Recursos no físicos o capacidades operativas. |

---

## 4. Entidades principales

| Entidad | Descripción |
|---|---|
| Almacén | Contenedor principal de inventario. |
| Ubicación física | Espacio interno opcional dentro de un almacén, como zona, pasillo, rack, nivel o posición. |
| Artículo | Producto, materia prima, herramienta o recurso inventariable autorizado para movimientos. |
| Existencia | Cantidad disponible o registrada. |
| Movimiento | Entrada, salida, transferencia o ajuste. |
| Reserva | Inventario apartado para venta o producción. |
| Lote | Grupo de artículos con trazabilidad común. |
| Serie | Identificador único de una unidad. |
| Kardex | Historial de movimientos por artículo. |

---

## 5. Catalogo de articulos

Antes de registrar movimientos, Almacenes debera contar con un catalogo maestro de articulos inventariables. Esto reduce errores de captura, evita nombres duplicados y prepara el sistema para que solo usuarios autorizados puedan crear o modificar articulos.

En MVP, el submodulo Articulos debera permitir:

- crear articulo;
- consultar articulos existentes;
- buscar por codigo, nombre, tipo, categoria o almacen;
- editar datos principales;
- usar articulos registrados dentro de Movimientos mediante busqueda rapida por codigo, nombre, tipo o categoria;
- mantener estatus activo, inactivo o bloqueado.

Campos base sugeridos:

| Campo | Uso |
|---|---|
| Codigo | SKU o clave interna estable. |
| Nombre | Nombre operativo del articulo. |
| Tipo | Materia prima, consumible, herramienta, producto terminado, refaccion o suministro. |
| Categoria | Agrupacion para reportes o filtros. |
| Unidad | Unidad principal de movimiento. |
| Minimo y maximo | Referencia para reabastecimiento futuro. |
| Politica de inventario | Estandar, lote, serie o restringido. |
| Almacen sugerido | Almacen usual para recepcion o consumo. |
| Estatus | Activo, inactivo o bloqueado. |
| Descripcion | Uso, restricciones, equivalencias o notas. |

Cuando se implemente usuarios y permisos, la creacion y edicion de articulos debera protegerse con permisos como:

```text
warehouses.items.read
warehouses.items.create
warehouses.items.update
warehouses.items.block
```

---

## 6. Movimientos de inventario

En MVP, Almacenes debera permitir registrar movimientos manuales para cubrir operaciones que no vengan aun de otros modulos. Esto es elemental para operacion real, ajustes iniciales, correcciones autorizadas, entradas extraordinarias y salidas no automatizadas.

Los movimientos deberan usar articulos dados de alta en el catalogo maestro cuando existan. Para evitar listas desplegables pesadas con cientos de registros, la seleccion debera hacerse mediante busqueda rapida por codigo, nombre, tipo o categoria. El campo manual solo debera funcionar como apoyo temporal mientras se configura el MVP o para casos excepcionales controlados.

| Movimiento | Descripción |
|---|---|
| Entrada por compra | Incrementa inventario recibido de proveedor. |
| Salida por producción | Consume insumos en una orden. |
| Entrada por producción | Incrementa producto terminado. |
| Transferencia | Mueve inventario entre almacenes o ubicaciones. |
| Ajuste positivo | Corrige inventario agregando cantidad. |
| Ajuste negativo | Corrige inventario disminuyendo cantidad. |
| Merma | Registra desperdicio o pérdida. |
| Devolución de cliente | Regresa producto vendido. |
| Devolución a proveedor | Reduce inventario recibido. |
| Reserva | Aparta inventario para una operación futura. Fuera del MVP funcional inicial. |
| Liberación de reserva | Regresa inventario apartado a disponible. Fuera del MVP funcional inicial. |

### Reservas en MVP

El submodulo Reservas queda documentado como flujo futuro, pero deshabilitado en el MVP. No debera crear, editar ni apartar inventario todavia.

Motivo:

- evitar apartados de inventario sin recalculo real de existencias;
- evitar prometer disponibilidad cuando aun no existe consumo contra movimientos reales;
- mantener el MVP enfocado en alta de almacenes, catalogo de articulos y movimientos manuales.

Cuando se active en fases posteriores, Reservas debera conectarse con existencias, movimientos, kardex, ventas y produccion.

### Kardex en MVP

Kardex queda habilitado como consulta, no como captura. No debera tener formulario propio porque su informacion se genera desde los movimientos registrados.

En el MVP, Kardex debera permitir:

- consultar movimientos historicos;
- filtrar por articulo;
- filtrar por almacen;
- buscar por documento, articulo, almacen, movimiento o motivo;
- ver entradas, salidas y saldo calculado por articulo y unidad.

Kardex no debera crear, editar ni eliminar movimientos. Cualquier correccion debera hacerse desde Movimientos mediante un ajuste autorizado.

---

### Existencias en MVP

Existencias queda habilitado como consulta calculada desde Movimientos. No debera capturar datos directamente ni reemplazar Kardex.

En el MVP, Existencias debera permitir:

- consultar saldo por articulo, almacen y unidad;
- buscar por articulo, almacen, unidad o estado;
- filtrar por almacen;
- identificar saldo disponible, saldo cero o saldo negativo;
- usar movimientos y ajustes como unica forma de corregir saldos.

---

## 7. Estados de inventario

| Estado | Descripción |
|---|---|
| Disponible | Puede usarse o venderse. |
| Reservado | Apartado para orden o venta. |
| En tránsito | En movimiento entre almacenes. |
| En proceso | Integrado a producción no terminada. |
| Bloqueado | No disponible por revisión, daño o control. |
| Merma | Registrado como desperdicio o pérdida. |

---

## 8. Reglas de negocio

- Los articulos deberan darse de alta antes de usarse en movimientos cuando el catalogo ya exista.
- La creacion y edicion de articulos debera estar restringida a roles autorizados.
- Todo movimiento deberá tener usuario, fecha, motivo y referencia.
- Todo movimiento deberá conservar `documento_origen`.
- Los movimientos manuales deberan capturar tipo, articulo, cantidad, unidad, almacen, fecha y motivo.
- Las salidas y ajustes negativos no deberan exceder la existencia calculada para el articulo, almacen y unidad.
- Los movimientos no deberán borrarse; deberán cancelarse o reversarse.
- El inventario disponible deberá descontar reservas.
- Una orden de producción podrá reservar insumos antes del consumo real.
- Una venta podrá reservar producto terminado.
- El cierre de producción podrá generar entrada de producto terminado.
- Los ajustes deberán requerir permiso especial.
- La merma deberá conservar relación con orden, área, producto o insumo.
- Las existencias podrán manejar unidades de compra, almacenamiento y consumo.
- Todo movimiento con impacto económico deberá poder alimentar Costos y Contabilidad.

---

## 9. Servicios funcionales que debe exponer

El módulo de Almacenes deberá estar preparado para responder a otros módulos.

### Consulta de disponibilidad

Deberá permitir consultar:

- existencia total;
- existencia disponible;
- existencia reservada;
- existencia bloqueada;
- existencia en tránsito;
- existencia por almacén;
- existencia por ubicación;
- existencia por lote o serie, si aplica.

### Reserva

Deberá permitir reservar inventario para:

- orden de producción;
- pedido de venta;
- transferencia;
- ajuste autorizado.

### Consumo y salida

Deberá permitir generar salidas desde:

- producción;
- venta;
- ajuste;
- devolución a proveedor;
- merma.

### Entrada

Deberá permitir generar entradas desde:

- compra recibida;
- producción terminada;
- devolución de cliente;
- ajuste positivo;
- transferencia recibida.

### Respuesta a Producción

Cuando Producción solicite validar una receta u orden, Almacenes deberá responder:

- recursos disponibles;
- recursos faltantes;
- almacenes donde existen;
- posibilidad de reserva;
- sustitutos o equivalentes, si se configuran en el futuro.

---

## 10. Integraciones

| Módulo | Relación |
|---|---|
| Producción | Reserva, consumo y entrada de producto terminado. |
| Compras | Recepción de materiales y artículos. |
| Ventas | Reserva, entrega y devolución de producto. |
| Costos | Valuación de inventario y costo de consumo. |
| Gastos | Fletes, almacenaje o costos asignables. |
| Contabilidad | Asientos por entradas, salidas, ajustes, merma e inventario. |
| Reportes | Existencias, rotación, movimientos y mermas. |

---

## 11. Métricas

- inventario disponible;
- inventario reservado;
- inventario en tránsito;
- inventario en proceso;
- valor de inventario;
- rotación;
- artículos bajo mínimo;
- artículos sobre máximo;
- merma por periodo;
- movimientos por almacén;
- diferencias por conteo físico.

---

## 12. Pendientes

- Definir si se manejarán lotes desde MVP o fase posterior.
- Definir método de costeo inicial.
- Definir si ubicaciones fisicas creceran a catalogo independiente en fases posteriores.
- Definir permisos finales para alta, edicion y bloqueo de articulos.
- Definir proceso de conteo físico.
- Definir permisos para ajustes y cancelaciones.
- Definir transferencias con origen y destino completos para afectar saldos por almacen.
