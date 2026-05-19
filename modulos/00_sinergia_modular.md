# ERClave — Sinergia, compatibilidad y contratos entre módulos

## 1. Objetivo

Este documento define cómo deberán convivir los módulos de ERClave desde el diseño inicial, para evitar que Producción, Almacenes, Ventas, Compras, Gastos, Costos, Contabilidad y Reportes se construyan como piezas aisladas.

La regla principal será:

> Toda operación relevante deberá poder tener origen, destino, impacto operativo, impacto financiero, trazabilidad, permisos y reportabilidad.

---

## 2. Principios transversales

- Cada registro operativo deberá incluir `tenant_id`.
- Cada registro relevante deberá poder incluir `centro_de_negocio_id`.
- Cada operación deberá conservar un `documento_origen`.
- Cada operación deberá poder generar eventos para otros módulos.
- Los módulos deberán validar si sus dependencias están activas para el tenant.
- Los movimientos no deberán borrarse; deberán cancelarse, reversarse o ajustarse.
- Las operaciones financieras deberán poder mapearse a cuentas contables.
- Los reportes deberán consumir datos con dimensiones comunes.
- Los permisos deberán evaluarse por módulo, submódulo, acción y alcance.

---

## 3. Identificadores comunes obligatorios

Las entidades principales deberán estar preparadas para relacionarse mediante identificadores comunes.

| Campo | Uso |
|---|---|
| tenant_id | Aislamiento del cliente SaaS. |
| centro_de_negocio_id | Alcance operativo o corporativo. |
| documento_origen_tipo | Tipo de documento que originó la operación. |
| documento_origen_id | ID del documento que originó la operación. |
| modulo_origen | Módulo que generó la operación. |
| estado | Estado funcional del registro. |
| moneda | Moneda de la operación. |
| centro_de_costos_id | Acumulación de costos. |
| cuenta_contable_id | Cuenta contable asociada, cuando aplique. |
| usuario_id | Usuario que ejecutó la acción. |
| fecha_operacion | Fecha real de la operación. |
| fecha_registro | Fecha en que se registró en sistema. |

---

## 4. Eventos funcionales recomendados

Los módulos deberán poder publicar o registrar eventos internos para que otros módulos reaccionen.

| Evento | Lo genera | Lo consumen |
|---|---|---|
| receta_activada | Producción | Producción, Costos, Reportes |
| orden_produccion_creada | Producción | Almacenes, Compras, Costos, Reportes |
| orden_produccion_programada | Producción | Almacenes, Compras |
| insumos_reservados | Almacenes | Producción, Costos, Reportes |
| insumos_insuficientes | Almacenes/Producción | Compras, Producción |
| insumos_consumidos | Producción/Almacenes | Costos, Contabilidad, Reportes |
| produccion_terminada | Producción | Almacenes, Costos, Ventas, Contabilidad |
| pedido_venta_aprobado | Ventas | Almacenes, Producción, Costos |
| producto_reservado_para_venta | Almacenes | Ventas, Reportes |
| entrega_realizada | Ventas/Almacenes | Ventas, Costos, Contabilidad, Reportes |
| compra_recibida | Compras/Almacenes | Almacenes, Gastos, Costos, Contabilidad |
| gasto_validado | Gastos | Costos, Contabilidad, Reportes |
| pago_registrado | Gastos/Contabilidad | Contabilidad, Reportes |
| asiento_contable_generado | Contabilidad | Reportes |
| periodo_contable_cerrado | Contabilidad | Todos los módulos con impacto financiero |

---

## 5. Validaciones automáticas entre módulos

### Receta y producción contra almacenes

Al capturar o activar una receta, ERClave deberá poder validar:

- si los recursos existen en catálogos;
- si las unidades de medida son válidas;
- si los insumos están asociados a almacenes permitidos;
- si las herramientas existen y son controlables;
- si maquinaria y mano de obra tienen centro de costos;
- si la receta tiene costo estimado suficiente para reportes.

Al generar una orden de producción, ERClave deberá poder validar:

- inventario disponible de materia prima;
- herramientas disponibles o asignables;
- maquinaria disponible, si se agenda;
- insumos faltantes;
- posibilidad de reserva;
- centro de costos requerido;
- mapeo contable para consumos, merma y producto terminado cuando Contabilidad esté activa.

### Ventas contra inventarios y producción

Al aprobar un pedido, ERClave deberá poder:

- consultar inventario disponible;
- reservar producto terminado;
- generar solicitud de producción si no hay stock suficiente;
- identificar fecha prometida;
- calcular margen estimado;
- validar cuentas contables de ingreso, cliente, impuestos y costo de venta.

### Compras contra almacenes, gastos y contabilidad

Al recibir una compra, ERClave deberá poder:

- generar entrada de inventario si es materia prima o producto almacenable;
- generar gasto o cuenta por pagar si existe documento fiscal;
- asociar XML/PDF como anexo;
- actualizar costo de artículo;
- generar asiento contable cuando el mapeo esté configurado.

### Gastos contra costos y contabilidad

Al validar un gasto, ERClave deberá poder:

- asignarlo a centro de costos, orden, producto, servicio, almacén o proyecto;
- prorratearlo si aplica;
- enviarlo a Costos como gasto directo o indirecto;
- generar asiento contable;
- conservar XML/PDF como anexo contable.

### Inventarios contra costos y contabilidad

Todo movimiento relevante de inventario deberá poder:

- actualizar existencias;
- actualizar kardex;
- alimentar costo real;
- generar asiento contable si corresponde;
- mantener documento origen.

---

## 6. Compatibilidad contable desde el inicio

Aunque Contabilidad se implemente en una fase posterior, los módulos deberán estar preparados para enviar información contable.

Cada operación financiera u operativa con impacto económico deberá poder indicar:

- tipo de operación;
- importe;
- impuesto;
- moneda;
- centro de costos;
- documento origen;
- anexo;
- cuenta contable sugerida o regla de mapeo;
- estado contable:
  - no_aplica;
  - pendiente_mapeo;
  - pendiente_contabilizar;
  - contabilizado;
  - reversado.

---

## 7. Matriz de impactos por operación

| Operación | Inventario | Costos | Contabilidad | Reportes |
|---|---|---|---|---|
| Crear receta | No mueve inventario | Calcula costo estimado | No genera asiento | Alimenta estructura productiva |
| Programar orden | Puede reservar insumos | Calcula costo estimado | Puede validar mapeos | Orden pendiente |
| Consumir insumos | Disminuye inventario | Aumenta costo real | Genera asiento si aplica | Consumo y merma |
| Terminar producción | Aumenta producto terminado | Cierra costo de orden | Genera asiento si aplica | Producción terminada |
| Aprobar pedido | Reserva o solicita producción | Calcula margen estimado | Valida mapeo de venta | Demanda |
| Entregar venta | Disminuye producto terminado | Calcula costo de venta | Genera asiento si aplica | Venta y margen |
| Recibir compra | Aumenta inventario o gasto | Actualiza costos | Genera cuenta por pagar | Compra recibida |
| Validar gasto | No siempre aplica | Asigna gasto | Genera asiento | Gasto por dimensión |
| Registrar pago | No aplica | No siempre aplica | Cancela cuenta por pagar/cobrar | Flujo financiero |
| Ajustar inventario | Ajusta existencias | Genera variación | Genera asiento si aplica | Diferencia inventario |

---

## 8. Dependencias mínimas por módulo

| Módulo | Debe conocer de |
|---|---|
| Producción | Productos, recursos, almacenes, centros de costos, costos y mapeos contables. |
| Almacenes | Artículos, ubicaciones, documentos origen, costos y cuentas contables de inventario. |
| Compras | Proveedores, artículos, almacenes, gastos, cuentas por pagar y mapeos contables. |
| Ventas | Clientes, productos, inventario, producción, costos y cuentas contables de ingreso. |
| Gastos | Proveedores, centros de costos, anexos, cuentas por pagar y mapeos contables. |
| Costos | Producción, almacenes, compras, gastos, ventas y contabilidad. |
| Contabilidad | Cuentas, periodos, anexos y documentos origen de todos los módulos. |
| Reportes | Dimensiones comunes y datos consolidados de todos los módulos. |
| Administración | Tenants, roles, permisos, módulos, submódulos, catálogos y dependencias. |

---

## 9. Reglas de diseño para implementación futura

- No crear un módulo que guarde datos críticos sin `tenant_id`.
- No crear movimientos operativos sin `documento_origen`.
- No crear consumos o entradas de inventario sin posibilidad de costeo.
- No crear ingresos, gastos, compras o ventas sin posibilidad de mapeo contable.
- No permitir que un módulo activo dependa de otro módulo desactivado sin modo degradado definido.
- No calcular reportes desde textos libres si puede usarse catálogo o dimensión.
- No cerrar periodos contables sin validar operaciones pendientes de contabilizar.
- No cancelar documentos con impacto en otro módulo sin generar reverso, ajuste o evento compensatorio.

