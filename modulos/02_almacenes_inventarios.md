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
| Usar en receta | Autoriza que Produccion ofrezca el articulo como recurso de receta. No modifica existencias. |

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

Los movimientos usan exclusivamente articulos dados de alta en el catalogo maestro. Para evitar listas desplegables pesadas con cientos de registros, la seleccion se realiza mediante busqueda rapida por codigo, nombre, tipo o categoria; el backend vuelve a validar articulo, almacen, unidad y estatus antes de registrar el movimiento.

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
| Reserva | Aparta inventario para una orden de Produccion. Implementada en codigo Local; aun no desplegada en QA. |
| Liberación de reserva | Regresa inventario apartado a disponible cuando una orden se cancela. Implementada para Produccion en codigo Local. |
| Consumo de reserva | Convierte una reserva de Produccion en una salida inmutable cuando la orden inicia por primera vez. Implementado en codigo Local. |

### Reservas por ambiente

El corte Local autoritativo permite a Produccion consultar disponibilidad neta, reservar por almacen, liberar y consumir reservas mediante contratos de `inventory-service`. La disponibilidad descuenta reservas activas no vencidas y las operaciones se serializan por tenant, articulo y almacen.

Limites actuales:

- QA conserva el corte anterior hasta una promocion gobernada;
- no existe todavia una interfaz independiente para administrar reservas manuales;
- Las reservas de pedidos de Ventas estan implementadas en Local y admiten consumo parcial; lotes y otros origenes permanecen futuros;
- la recepcion total o parcial de producto terminado desde ordenes terminadas esta implementada en Local; merma, bloqueos, transito, lotes y series siguen fuera de este corte.

Produccion es consumidor del contrato; Inventory conserva ownership de reservas, movimientos, disponibilidad y valuacion.

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
- Un articulo sin movimientos aparece en Inventario con saldo cero cuando tiene almacen sugerido; el alta del articulo no genera existencias.
- Produccion solo consulta articulos activos con `use_in_recipe=true` y calcula su disponibilidad desde movimientos de cualquier almacen del tenant.
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
- El **costo unitario base** del articulo representa el costo manual de una unidad en la UOM base configurada: por kilogramo si la base es kg, por litro si es L, por pieza si es H87, etcetera.
- Produccion toma ese costo autoritativo para estimar materiales de receta. El frontend no inventa un costo si el articulo no lo tiene.
- La conversion de cantidad y costo solo procede entre UOM activas de la misma categoria y con un factor estandar inequivoco. Kilogramo/gramo y litro/mililitro son ejemplos validos; caja, paquete o unidad personalizada requieren una equivalencia empresarial futura.
- El codigo de almacen y el codigo de articulo se asignan desde el catalogo de folios de Administracion cuando su modo es administrado; en modo manual siguen sujetos a unicidad por tenant.

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

- Definir e implementar lotes, series, cuarentena, bloqueos y transito.
- Definir si ubicaciones fisicas creceran a catalogo independiente en fases posteriores.
- Definir proceso de conteo físico.
- Definir permisos para ajustes y cancelaciones.
- Implementar recepcion de merma desde Produccion.
- Extender reservas a Ventas solo cuando exista su corte vertical real.
- Ejecutar pruebas de contencion paralela con carga antes de promover la revision Local a QA.

---

## 13. Nombre visible y consulta escalable

El modulo conserva el nombre visible **Almacenes** y el identificador tecnico `almacenes`. El submodulo visible **Existencias** se renombra a **Inventario**, conservando `existencias` como su id tecnico. **Almacenes** sigue nombrando el catalogo de espacios fisicos e **Inventario** la consulta calculada de saldos.

Existencias debe buscar parcialmente por codigo o nombre de articulo y almacen. Los filtros de almacen, articulo, unidad, estado del saldo, tipo, categoria, politica y estado del articulo deben ejecutarse en servidor y combinarse con semantica AND. La lista usara paginacion por cursor, orden estable, `limit` default 50 y maximo 200; no se cargara el catalogo completo para filtrarlo en el navegador.

Los indicadores bajo minimo y sobre maximo se calculan usando los campos guardados del articulo. No se persistiran como estados independientes.

En el corte Local autoritativo, `available_quantity = max(on_hand_quantity - reserved_quantity, 0)`. Reservar y consumir se serializa mediante bloqueo transaccional por tenant, articulo y almacen; los reintentos usan fuente e idempotencia estables. La valuacion usa costo promedio derivado de movimientos y un costo predeterminado solo cuando no existe saldo valuado.

El criterio inicial de volumen es consultar correctamente un tenant sintetico con al menos 10,000 articulos, sin duplicados u omisiones al paginar y sin acceder a QA. La especificacion tecnica y el procedimiento reproducible viven en:

- `docs/arquitectura/inventario_consulta_escalable.md`;
- `docs/operaciones/validacion_volumen_inventario_local.md`.
# CHG-206: alta guiada de terminado

Al crear un producto terminado, Almacenes puede seleccionar opcionalmente un producto activo de Producción aún no vinculado. El flujo crea el artículo y solicita a Producción el vínculo autoritativo; no se guardan referencias inversas ni se empata por nombre.

## CHG-209: seleccion escalable

Artículos y almacenes son referencias crecientes: alta, movimientos, Inventario y Kárdex permiten buscarlos por código o nombre y guardan IDs estables. Tipo, estatus, política y estado del saldo permanecen como filtros cerrados. La búsqueda local acotada no sustituye la paginación server-side ya especificada para volumen alto.

## CHG-213: apertura y unidad valida

Al abrir un selector buscable se muestra el catalogo completo antes de aplicar texto de busqueda; la etiqueta seleccionada no debe convertirse en un filtro involuntario. Produccion solo puede usar articulos cuya unidad base exista y este activa en Administracion. La unidad queda bloqueada cuando existe historia de movimientos o reservas; una correccion posterior requiere articulo sustituto y regularizacion autorizada, nunca equivalencia automatica por similitud de codigo.

## CHG-222: recepcion de producto terminado

Almacenes consulta ordenes terminadas y confirma la recepcion fisica total o parcial. Inventory deriva por ID el articulo, unidad y costo, impide exceder la cantidad producida y registra una entrada `production_order_receipt` en Kardex. Una orden totalmente recibida deja de mostrarse como pendiente. Produccion no escribe movimientos ni da por recibido automaticamente el producto.

## CHG-214: alias heredados de unidad

La revision Local `20260821_0023` reconoce exclusivamente dos equivalencias empresariales inequivocas heredadas: `LTS` como `LTR` y `MT` como `MTR`. La normalizacion actualiza de forma atomica el articulo, sus movimientos y los snapshots relacionados, sin cambiar cantidad, costo, identidad ni almacen, y registra una auditoria por fila. Cualquier otro cambio de unidad conserva la regla general: si existen movimientos o reservas, no se permite reinterpretar la historia y se requiere un articulo sustituto con regularizacion autorizada.
