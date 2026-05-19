# ERClave — Módulo de Almacenes e Inventarios

## 1. Objetivo

El módulo de Almacenes e Inventarios permitirá controlar existencias, movimientos, ubicaciones, reservas, consumos, producto en proceso, producto terminado, merma y trazabilidad de recursos.

Su propósito es conectar la operación física con producción, compras, ventas y costos.

---

## 2. Alcance

- almacenes configurables;
- tipos de almacén;
- ubicaciones internas;
- existencias;
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
| Ubicación | Espacio interno dentro de un almacén. |
| Artículo | Producto, materia prima, herramienta o recurso inventariable. |
| Existencia | Cantidad disponible o registrada. |
| Movimiento | Entrada, salida, transferencia o ajuste. |
| Reserva | Inventario apartado para venta o producción. |
| Lote | Grupo de artículos con trazabilidad común. |
| Serie | Identificador único de una unidad. |
| Kardex | Historial de movimientos por artículo. |

---

## 5. Movimientos de inventario

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
| Reserva | Aparta inventario para una operación futura. |
| Liberación de reserva | Regresa inventario apartado a disponible. |

---

## 6. Estados de inventario

| Estado | Descripción |
|---|---|
| Disponible | Puede usarse o venderse. |
| Reservado | Apartado para orden o venta. |
| En tránsito | En movimiento entre almacenes. |
| En proceso | Integrado a producción no terminada. |
| Bloqueado | No disponible por revisión, daño o control. |
| Merma | Registrado como desperdicio o pérdida. |

---

## 7. Reglas de negocio

- Todo movimiento deberá tener usuario, fecha, motivo y referencia.
- Todo movimiento deberá conservar `documento_origen`.
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

## 8. Servicios funcionales que debe exponer

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

## 9. Integraciones

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

## 10. Métricas

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

## 11. Pendientes

- Definir si se manejarán lotes desde MVP o fase posterior.
- Definir método de costeo inicial.
- Definir reglas de ubicaciones internas.
- Definir proceso de conteo físico.
- Definir permisos para ajustes y cancelaciones.
