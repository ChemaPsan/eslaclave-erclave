# ERClave — Módulo de Reportes e Inteligencia Operativa

## 1. Objetivo

El módulo de Reportes e Inteligencia Operativa permitirá convertir datos de producción, inventario, compras, ventas, gastos y costos en información útil para tomar decisiones.

---

## 2. Alcance

- dashboards;
- reportes estándar;
- reportes configurables;
- filtros guardados;
- exportaciones;
- indicadores por rol;
- análisis por centro de negocio;
- análisis por producto o servicio;
- análisis de rentabilidad;
- análisis de productividad;
- análisis de demanda;
- reportes por periodo.

---

## 3. Reportes iniciales sugeridos

### Producción

- órdenes pendientes;
- órdenes en producción;
- órdenes terminadas;
- cumplimiento de fechas;
- merma por orden;
- productividad por área.

### Inventarios

- inventario disponible;
- inventario reservado;
- inventario bajo mínimo;
- movimientos por almacén;
- kardex por artículo;
- merma por periodo.

### Compras

- órdenes pendientes;
- recepciones parciales;
- compras por proveedor;
- variación de precio;
- tiempos de entrega.

### Ventas

- ventas por periodo;
- ventas por cliente;
- pedidos pendientes;
- entregas pendientes;
- margen por producto;
- margen por cliente.

### Gastos

- gastos por centro de costos;
- gastos por proveedor;
- gastos pendientes de pago;
- gastos por categoría;
- gastos sin asignar.

### Costos

- costo estimado vs. real;
- variaciones;
- rentabilidad;
- costo por centro;
- costo por producto.

### Contabilidad

- asientos por periodo;
- movimientos por cuenta;
- operaciones sin mapeo contable;
- registros sin anexo;
- gastos por cuenta;
- ingresos por cuenta.

---

## 4. Entidades principales

| Entidad | Descripción |
|---|---|
| Reporte | Consulta o vista de información. |
| Dashboard | Agrupación visual de indicadores. |
| Indicador | Métrica de seguimiento. |
| Filtro | Criterio de consulta reutilizable. |
| Exportación | Archivo generado desde datos. |
| Definición de métrica | Regla central para calcular un indicador. |

---

## 5. Reglas de negocio

- Los reportes deberán respetar permisos y alcance del usuario.
- Un usuario solo deberá ver datos de su tenant y centros autorizados.
- Los indicadores deberán tener una definición consistente.
- Los reportes configurables no deberán exponer datos restringidos.
- Las exportaciones deberán registrarse en auditoría si contienen información sensible.
- Los reportes deberán poder filtrarse por periodo, centro, área, producto, servicio y responsable.
- Los reportes deberán usar dimensiones comunes entre módulos: tenant, centro de negocio, centro de costos, periodo, producto, cliente, proveedor, almacén y documento origen.
- Los reportes financieros deberán respetar periodos contables y permisos contables.

---

## 6. Compatibilidad de datos

Para que la reportería funcione sin recaptura, cada módulo deberá entregar datos con dimensiones compatibles.

| Dimensión | Módulos que deben alimentarla |
|---|---|
| Periodo | Ventas, Gastos, Compras, Contabilidad, Producción, Almacenes. |
| Centro de costos | Producción, Gastos, Compras, Costos, Contabilidad. |
| Producto/servicio | Producción, Ventas, Almacenes, Costos. |
| Cliente | Ventas, Contabilidad, Reportes. |
| Proveedor | Compras, Gastos, Contabilidad. |
| Almacén | Almacenes, Producción, Compras, Ventas. |
| Documento origen | Todos los módulos operativos y financieros. |

Los reportes no deberán depender de texto libre cuando exista catálogo o dimensión estructurada.

---

## 7. Customización

La reportería deberá permitir:

- seleccionar columnas;
- guardar filtros;
- exportar resultados;
- configurar rangos de fecha;
- agrupar por dimensión;
- ordenar resultados;
- crear vistas por rol;
- adaptar reportes por cliente en fases futuras.

---

## 8. Integraciones

| Módulo | Relación |
|---|---|
| Producción | Productividad, cumplimiento y merma. |
| Almacenes | Existencias, movimientos y rotación. |
| Compras | Abastecimiento y proveedores. |
| Ventas | Demanda, margen y entregas. |
| Gastos | Egresos y cuentas por pagar. |
| Costos | Rentabilidad y variaciones. |
| Contabilidad | Asientos, cuentas, periodos, anexos y estados contables. |
| Administración | Permisos, roles y visibilidad. |

---

## 9. Métricas clave

- producción pendiente;
- producción terminada;
- inventario disponible;
- inventario comprometido;
- rotación de inventario;
- compras pendientes;
- pedidos pendientes;
- gastos por centro;
- margen por cliente;
- rentabilidad por producto;
- cumplimiento de entregas;
- variación de producción.
- operaciones pendientes de contabilizar;
- operaciones sin mapeo contable;
- asientos por periodo.

---

## 10. Pendientes

- Definir reportes del MVP.
- Definir herramienta de exportación.
- Definir si habrá dashboards embebidos.
- Definir permisos por reporte.
- Definir modelo analítico futuro.

---

## 11. Frontera con reportes estándar

Estado: **inactivo y planeado**.

Cada módulo operativo presenta en su propia raíz los catálogos y reportes estándar que le pertenecen, sin mutaciones. Este módulo no absorbe esas consultas cotidianas. Se reserva para cruces entre módulos, tableros configurables, indicadores avanzados, vistas guardadas, distribución y reportes a la medida.

La matriz transversal y la regla para módulos futuros se mantienen en `docs/arquitectura/reportes_estandar_por_modulo.md`. Ningún dashboard, exportación o consulta especializada de este documento debe presentarse como implementada mientras el módulo permanezca inactivo.
