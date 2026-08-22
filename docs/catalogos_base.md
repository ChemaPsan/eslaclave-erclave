# ERClave - Catalogos base de Administracion y Configuracion

## 1. Proposito

Este documento concentra los catalogos base que ERClave debera administrar desde el modulo de Administracion y Configuracion.

En Local ya estan implementados `units_of_measure`, `currencies` y `payment_terms`. MXN/USD/EUR y contado/credito a 7/15/30/45/60 dias son defaults iniciales, pero cada tenant puede agregar valores o inactivarlos. Ventas valida codigos activos y no acepta texto libre. Los estados de Cotizacion, Pedido, Entrega y Orden de Produccion son maquinas de estado protegidas, no catalogos editables.

`document.template` es configuracion tenant-safe y no un catalogo: centraliza logo, colores, pie y numeracion para los PDF de Ventas, Produccion y generadores futuros.

El objetivo es no perder contexto de los valores que hoy pueden existir como opciones fijas del MVP, pero que mas adelante deberan poder configurarse por tenant, centro de negocio, modulo, rol o pais.

---

## 2. Principios

- Los catalogos compartidos deberan vivir en Administracion y Configuracion, no duplicados dentro de cada modulo.
- Cada modulo podra consumir catalogos globales y, cuando aplique, catalogos propios del tenant.
- Los valores usados en operaciones historicas no deberan eliminarse; deberan desactivarse.
- Todo catalogo con impacto operativo, contable, fiscal, de costos o permisos debera auditar cambios.
- Los catalogos deberan tener soporte Espanol/Ingles desde su diseno.
- El MVP puede usar opciones fijas mientras la funcionalidad se valida, pero esas opciones deberan quedar identificadas aqui para migrarlas despues.
- Un catalogo debera tener un codigo estable para integraciones, reportes y trazabilidad.

---

## 3. Modelo minimo sugerido

Todo catalogo base deberia considerar estos campos minimos:

| Campo | Uso |
|---|---|
| id | Identificador interno. |
| code | Codigo estable para integraciones, reglas y reportes. |
| nameEs | Nombre visible en Espanol. |
| nameEn | Nombre visible en Ingles. |
| descriptionEs | Descripcion funcional en Espanol. |
| descriptionEn | Descripcion funcional en Ingles. |
| moduleOwner | Modulo responsable del catalogo. |
| scope | Global, tenant, centro de negocio o modulo. |
| status | Activo, inactivo o bloqueado. |
| sortOrder | Orden de visualizacion. |
| isDefault | Marca para valor predeterminado. |
| metadata | Configuracion extra por catalogo cuando aplique. |
| createdAt | Fecha de creacion. |
| updatedAt | Fecha de ultima actualizacion. |
| createdBy | Usuario que creo el registro. |
| updatedBy | Usuario que actualizo el registro. |

---

## 4. Catalogos transversales prioritarios

Estos catalogos son candidatos a implementarse primero porque impactan varios modulos.

| Catalogo | Modulo dueno | Uso principal | Prioridad |
|---|---|---|---|
| Centros de negocio | Administracion | Segmentar operacion, permisos, reportes y configuracion. | Alta |
| Areas o departamentos | Administracion | Asignar usuarios, flujos, costos y responsables. | Alta |
| Roles | Administracion | Controlar acceso funcional por perfil. | Alta |
| Permisos | Administracion | Controlar acciones por modulo, submodulo y alcance. | Alta |
| Unidades de medida | Administracion | Compras, almacenes, produccion, ventas y costos. | Alta |
| Monedas | Administracion | Compras, ventas, gastos, costos y contabilidad. | Alta |
| Impuestos | Administracion | Compras, ventas, gastos y contabilidad. | Alta |
| Prioridades | Administracion | Ordenes, tareas, requisiciones y tickets operativos. | Media |
| Estados operativos compartidos | Administracion | Borrador, en revision, aprobado, cancelado, cerrado. | Media |
| Motivos de cancelacion | Administracion | Trazabilidad de cancelaciones en varios modulos. | Media |
| Idiomas | Administracion | Soporte Espanol/Ingles y futuros idiomas. | Media |

### Unidades de medida implementadas

Administracion es la fuente de verdad tenant-safe de unidades de medida. Cada tenant recibe 50 unidades iniciales basadas en codigos de tres caracteres de UN/CEFACT Recommendation 20 y puede agregar unidades propias sin alterar los codigos predeterminados.

Campos operativos: `code`, `name_es`, `name_en`, `symbol`, `category`, `decimal_places`, `system_default` y `status`. Produccion e Inventarios persisten el codigo estable, no el texto visible. Las altas y actualizaciones rechazan codigos inexistentes o inactivos; un movimiento de inventario debe usar la unidad base del articulo hasta que exista un catalogo explicito de conversiones.

Permisos: `admin.unit.read`, `admin.unit.create` y `admin.unit.update`. La lectura se concede a roles operativos existentes porque el catalogo es dependencia transversal; los roles nuevos deben recibirla de forma explicita si consumen Produccion o Inventarios. Crear o inactivar queda en el rol owner por defecto. Las mutaciones exigen `Idempotency-Key`, aceptan `X-Correlation-Id` y registran antes/despues en auditoria.

---

## 5. Catalogos por modulo

### Produccion

| Catalogo | Uso |
|---|---|
| Tipos de producto o servicio | Clasificar lo que se fabrica, vende o entrega. |
| Categorias de producto o servicio | Agrupar productos/servicios para reportes y reglas. |
| Tipos de recurso | Personas, maquinaria, herramientas, insumos o servicios externos. |
| Areas productivas | Asignar etapas y responsabilidades operativas. |
| Estados de receta | Controlar borrador, activa, inactiva o en revision. |
| Estados de orden de produccion | Controlar planeada, liberada, en proceso, pausada, terminada o cancelada. |
| Motivos de pausa | Documentar interrupciones productivas. |
| Motivos de reproceso | Explicar ajustes, retrabajos o desviaciones. |

### Almacenes e inventarios

| Catalogo | Uso |
|---|---|
| Tipos de almacen | Materia prima, producto terminado, herramienta, cuarentena, devoluciones, etc. |
| Politicas de inventario | Estandar, lote, serie, restringido u otras reglas. |
| Tipos de movimiento | Entrada, salida, transferencia, ajuste positivo y ajuste negativo. |
| Motivos de ajuste | Conteo fisico, merma, dano, correccion, caducidad, devolucion. |
| Estados de almacen | Activo, inactivo, bloqueado. |
| Estados de inventario | Disponible, reservado, retenido, danado, caducado. |
| Tipos de ubicacion fisica | Zona, pasillo, rack, nivel, posicion, bin o area abierta. |

### Compras

| Catalogo | Uso |
|---|---|
| Tipos de proveedor | Insumos, servicios, logistica, mantenimiento, consultoria. |
| Condiciones de pago | Contado, credito, parcialidades u otras condiciones. |
| Metodos de entrega | Recoleccion, entrega proveedor, paqueteria, transporte propio. |
| Estados de requisicion | Borrador, solicitada, aprobada, rechazada, convertida. |
| Estados de orden de compra | Emitida, parcial, recibida, cerrada, cancelada. |
| Motivos de rechazo | Trazabilidad de aprobaciones no autorizadas. |
| Motivos de devolucion a proveedor | Calidad, cantidad, dano, error de pedido. |

### Ventas

| Catalogo | Uso |
|---|---|
| Tipos de cliente | Minorista, mayorista, distribuidor, corporativo, interno. |
| Listas de precio | Precio general, mayoreo, convenio, promocion. |
| Condiciones comerciales | Credito, contado, anticipo, contra entrega. |
| Estados de cotizacion | Borrador, enviada, aceptada, rechazada, vencida. |
| Estados de pedido | Nuevo, confirmado, surtido parcial, entregado, cancelado. |
| Motivos de devolucion | Calidad, error, garantia, dano, cambio. |
| Canales de venta | Mostrador, ecommerce, ejecutivo, marketplace, distribuidor. |

### Gastos

| Catalogo | Uso |
|---|---|
| Tipos de gasto | Operativo, administrativo, venta, mantenimiento, viaje. |
| Categorias de gasto | Agrupacion para autorizaciones, presupuesto y reportes. |
| Metodos de pago | Efectivo, tarjeta, transferencia, cheque, credito. |
| Estados de gasto | Capturado, validado, aprobado, pagado, rechazado. |
| Tipos de comprobante | Factura, recibo, nota, comprobante interno. |
| Motivos de rechazo | Trazabilidad de gastos no aceptados. |

### Costos

| Catalogo | Uso |
|---|---|
| Centros de costo | Agrupar costos por area, centro o proceso. |
| Drivers de prorrateo | Horas, unidades, metros, porcentaje, consumo real. |
| Metodos de costeo | Estandar, promedio, real, estimado. |
| Tipos de variacion | Precio, cantidad, eficiencia, merma, tiempo. |
| Tipos de costo | Material, mano de obra, indirecto, servicio, logistica. |

### Contabilidad

| Catalogo | Uso |
|---|---|
| Cuentas contables | Base para polizas, reportes y mapeos. |
| Periodos contables | Control de apertura, cierre y bloqueo. |
| Tipos de poliza o asiento | Diario, ingreso, egreso, ajuste, cierre. |
| Tipos de documento origen | Compra, venta, gasto, movimiento, produccion, ajuste. |
| Tipos de operacion | Devengo, pago, cobro, ajuste, cancelacion. |
| Estados contables | Pendiente, contabilizado, reversado, bloqueado. |
| Reglas de mapeo contable | Relacionar eventos operativos con cuentas. |

### Reportes

| Catalogo | Uso |
|---|---|
| Dimensiones de reporte | Centro, area, modulo, usuario, cliente, proveedor, producto. |
| Periodicidades | Diario, semanal, mensual, trimestral, anual. |
| Formatos de exportacion | PDF, CSV, Excel u otros. |
| Vistas por rol | Reportes visibles por perfil de usuario. |

---

## 6. Opciones fijas actuales que deberan migrarse a catalogos

Estas opciones pueden existir hoy en el frontend como parte del MVP, pero quedan marcadas para llevarse despues a Administracion y Configuracion.

| Area | Opciones identificadas |
|---|---|
| Almacenes | Tipos de almacen, estados de almacen, politicas de inventario, tipos de movimiento, motivos de movimiento, unidades usadas en movimientos. |
| Produccion | Estados de orden, categorias de producto/servicio, tipos de recurso, prioridades y motivos operativos. |
| Captura generica de modulos | Estados como borrador, pendiente, en revision y aprobado. |
| Transversal | Centros de negocio, areas, unidades de medida, monedas, impuestos, prioridades e idiomas. |

---

## 7. Permisos sugeridos

Los catalogos base deberan tener permisos separados de la operacion diaria.

```text
admin.catalogs.read
admin.catalogs.create
admin.catalogs.update
admin.catalogs.deactivate
admin.catalogs.audit.read
admin.catalogs.import
admin.catalogs.export
```

Cuando un catalogo sea critico para un modulo, podran existir permisos mas especificos:

```text
admin.catalogs.warehouses.update
admin.catalogs.accounting.update
admin.catalogs.taxes.update
admin.catalogs.permissions.update
```

---

## 8. Criterios para convertir una opcion en catalogo

Una opcion fija debera moverse a catalogo administrable cuando cumpla uno o mas criterios:

- Se usa en dos o mas modulos.
- Varia por tenant, centro de negocio, pais o giro.
- Impacta reportes, costos, contabilidad, impuestos o permisos.
- Necesita traduccion Espanol/Ingles.
- Necesita activarse, desactivarse u ordenarse.
- Debe auditarse por cumplimiento, control interno o soporte.
- Sera consumida por API, integraciones o importaciones.

---

## 9. Backlog de implementacion

1. Repetir para cada catalogo pendiente el patron de tarjeta-resumen y vista dedicada ya implementado en Unidades de medida.
2. Mantener `admin-service` como propietario de catalogos transversales y definir ownership explicito para catalogos propios de modulo.
3. Migrar opciones fijas restantes del frontend a lectura desde catalogos.
4. Agregar soporte ES/EN a cada nuevo valor visible.
5. Exigir idempotencia, correlacion y bitacora de cambios en cada catalogo mutable.
6. Agregar importacion/exportacion controlada para cargas iniciales.
7. Agregar validadores para detectar opciones fijas nuevas que deberian declararse en este documento.

