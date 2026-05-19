# ERClave — Módulo de Costos y Centros de Costos

## 1. Objetivo

El módulo de Costos y Centros de Costos permitirá medir cuánto cuesta producir, operar, vender o prestar un servicio, comparando costos estimados contra costos reales y acumulando información por área, producto, servicio, orden, cliente o centro de negocio.

---

## 2. Alcance

- centros de costos;
- costo estimado;
- costo real;
- costo estándar;
- costo promedio;
- costos por orden;
- costos por producto;
- costos por servicio;
- variaciones;
- rentabilidad;
- asignaciones de gastos;
- costos indirectos;
- análisis por dimensiones.

---

## 3. Centros de costos

Ejemplos iniciales:

- Corte.
- Costura.
- Ensamble.
- Calidad.
- Empaque.
- Administración.
- Ventas.
- Mantenimiento.
- Producción general.
- Servicio técnico.

---

## 4. Dimensiones de análisis

- centro de negocio;
- área;
- producto;
- servicio;
- cliente;
- proveedor;
- orden de producción;
- proyecto;
- almacén;
- máquina;
- responsable;
- periodo.

---

## 5. Tipos de costo

| Tipo | Descripción |
|---|---|
| Costo estimado | Calculado desde receta o planeación. |
| Costo real | Calculado con consumos, tiempos y gastos reales. |
| Costo estándar | Costo de referencia definido por la empresa. |
| Costo promedio | Costo calculado con movimientos históricos. |
| Costo por orden | Costo acumulado en una orden específica. |
| Costo por centro | Costo acumulado por área o centro. |

---

## 6. Componentes de costo

- materia prima;
- herramientas consumibles;
- uso de maquinaria;
- mano de obra directa;
- servicios externos;
- mermas;
- gastos asignados;
- fletes;
- mantenimiento relacionado;
- costos indirectos asignables.

---

## 7. Variaciones

El sistema deberá comparar:

- cantidad estimada vs. cantidad consumida;
- tiempo estimado vs. tiempo real;
- costo estimado vs. costo real;
- merma esperada vs. merma real;
- fecha planeada vs. fecha real;
- margen estimado vs. margen real.

---

## 8. Reglas de negocio

- Todo costo deberá poder rastrearse a una fuente.
- El costo estimado podrá calcularse desde la receta.
- El costo real deberá considerar consumos, tiempos y gastos reales.
- Los gastos indirectos deberán poder asignarse por reglas de prorrateo.
- El costo de venta deberá relacionarse con el producto vendido.
- Las variaciones deberán conservar el detalle que las originó.
- Los centros de costos podrán existir por tenant, centro de negocio o área.
- Todo costo con impacto financiero deberá poder relacionarse con una cuenta contable o quedar como pendiente de mapeo.
- El costo real deberá poder recibir datos desde Almacenes, Producción, Compras y Gastos sin recaptura manual.

---

## 9. Compatibilidad con operación y contabilidad

### Fuentes de costo

El módulo deberá recibir información de:

- recetas para costo estimado;
- consumo de insumos para costo real;
- uso de maquinaria para costo operativo;
- mano de obra para horas hombre;
- compras para costo de adquisición;
- gastos para costos directos e indirectos;
- ventas para costo de venta y margen;
- almacenes para valuación de inventario.

### Salidas hacia otros módulos

Costos deberá entregar:

- costo estimado a Producción y Ventas;
- costo real a Producción, Ventas y Reportes;
- variaciones a Reportes;
- costo de venta a Ventas y Contabilidad;
- centros de costos y dimensiones a Contabilidad.

### Relación contable

Cuando Contabilidad esté activa, Costos deberá permitir mapear:

- costo de producción;
- producto en proceso;
- producto terminado;
- costo de ventas;
- variaciones de producción;
- merma;
- gastos indirectos asignados.

---

## 10. Integraciones

| Módulo | Relación |
|---|---|
| Producción | Costos de orden, mano de obra, maquinaria y merma. |
| Almacenes | Costo de insumos, inventario y producto terminado. |
| Compras | Costo de materiales y servicios adquiridos. |
| Gastos | Gastos directos e indirectos. |
| Ventas | Margen y rentabilidad. |
| Contabilidad | Costo de venta, variaciones, inventario, producto en proceso y centros de costos. |
| Reportes | Dashboards de costos y variaciones. |

---

## 11. Métricas

- costo estimado de producción;
- costo real de producción;
- variación de costo;
- costo por producto;
- costo por servicio;
- costo por centro;
- margen por producto;
- margen por cliente;
- gasto indirecto asignado;
- rentabilidad por periodo.

---

## 12. Pendientes

- Definir método de costeo inicial.
- Definir reglas de prorrateo.
- Definir costo estándar por producto.
- Definir cuentas contables sugeridas por tipo de costo.
- Definir reportes mínimos de costos.
