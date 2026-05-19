# ERClave — Módulo de Compras y Abastecimiento

## 1. Objetivo

El módulo de Compras y Abastecimiento permitirá controlar necesidades de compra, proveedores, requisiciones, órdenes de compra, recepciones, precios, tiempos de entrega y relación con inventarios, producción y gastos.

---

## 2. Alcance

- proveedores;
- productos o servicios por proveedor;
- requisiciones;
- autorizaciones;
- órdenes de compra;
- recepciones;
- compras parciales;
- compras ligadas a producción;
- compras ligadas a almacén;
- compras ligadas a gastos;
- comparación entre compra, recepción y factura;
- reabastecimiento simple.

---

## 3. Entidades principales

| Entidad | Descripción |
|---|---|
| Proveedor | Persona o empresa que suministra productos o servicios. |
| Requisición | Solicitud interna de compra. |
| Orden de compra | Documento emitido al proveedor. |
| Recepción | Registro de material o servicio recibido. |
| Precio proveedor | Precio negociado por artículo o servicio. |
| Condición de compra | Moneda, plazo, impuestos y forma de pago. |
| Documento fiscal | XML/PDF asociado a la compra. |

---

## 4. Flujo recomendado

1. Se detecta necesidad de compra.
2. Se genera requisición.
3. Se autoriza la requisición, si aplica.
4. Se selecciona proveedor.
5. Se genera orden de compra.
6. Se registra recepción parcial o total.
7. Se valida XML/PDF contra la compra.
8. Se afecta inventario, gasto o cuenta por pagar.

---

## 5. Estados sugeridos

### Requisición

| Estado | Descripción |
|---|---|
| Borrador | Solicitud en captura. |
| Solicitada | Enviada para revisión. |
| Aprobada | Autorizada para compra. |
| Rechazada | No autorizada. |
| Convertida | Generó orden de compra. |
| Cancelada | Cancelada por el solicitante o autorizador. |

### Orden de compra

| Estado | Descripción |
|---|---|
| Borrador | Orden en captura. |
| Enviada | Orden enviada al proveedor. |
| Parcialmente recibida | Algunos artículos fueron recibidos. |
| Recibida | Recepción completa. |
| Facturada | Documento fiscal asociado. |
| Cerrada | Proceso concluido. |
| Cancelada | Orden cancelada. |

---

## 6. Reabastecimiento

El sistema podrá sugerir compras con base en:

- inventario mínimo;
- punto de reorden;
- stock de seguridad;
- demanda por ventas;
- órdenes de producción programadas;
- insumos reservados;
- compras en tránsito;
- tiempo de entrega del proveedor.

La primera versión puede iniciar con alertas simples de bajo inventario y evolucionar hacia planeación de materiales.

---

## 7. Reglas de negocio

- Una orden de compra podrá generarse desde una requisición o de forma directa.
- Una requisición podrá generarse automáticamente desde faltantes detectados por Producción o Almacenes.
- La recepción podrá ser parcial o total.
- Una compra de materia prima deberá poder afectar inventario.
- Una compra de servicio deberá poder afectar gasto o centro de costos.
- Una factura deberá poder compararse contra orden y recepción.
- Las autorizaciones podrán depender de monto, centro de costos o tipo de compra.
- El historial de precios por proveedor deberá conservarse.
- Una compra recibida deberá poder generar cuenta por pagar y asiento contable cuando Contabilidad esté activa.
- Cada recepción deberá conservar documento origen, proveedor, almacén destino y centro de costos si aplica.

---

## 8. Compatibilidad con inventarios, gastos y contabilidad

### Desde faltantes

Si Producción o Almacenes detectan faltantes, Compras deberá poder recibir:

- artículo o recurso requerido;
- cantidad faltante;
- unidad de medida;
- fecha requerida;
- orden de producción o pedido relacionado;
- almacén destino sugerido;
- centro de costos;
- prioridad.

### Al recibir compra

El sistema deberá decidir si la recepción:

- incrementa inventario;
- registra gasto directo;
- registra gasto indirecto;
- crea cuenta por pagar;
- requiere XML/PDF;
- genera asiento contable;
- actualiza costo del artículo.

### Mapeo contable mínimo

Las compras deberán poder mapear:

- inventario de materia prima;
- proveedores o cuentas por pagar;
- impuestos acreditables;
- gastos directos;
- gastos indirectos;
- fletes y servicios asociados.

---

## 9. Integraciones

| Módulo | Relación |
|---|---|
| Producción | Compra de insumos faltantes para órdenes. |
| Almacenes | Recepción y entrada de materiales. |
| Gastos | Registro de facturas y cuentas por pagar. |
| Costos | Costo de materia prima, fletes y servicios. |
| Contabilidad | Asientos de compra, recepción, impuestos y cuentas por pagar. |
| Reportes | Compras pendientes, proveedores, precios y tiempos. |

---

## 10. Métricas

- compras pendientes;
- requisiciones pendientes de autorizar;
- órdenes parcialmente recibidas;
- tiempo promedio de entrega;
- compras por proveedor;
- variación de precio;
- compras por centro de costos;
- compras urgentes;
- cumplimiento de proveedor.

---

## 11. Pendientes

- Definir reglas de autorización.
- Definir relación inicial con XML fiscal.
- Definir catálogo de condiciones de pago.
- Definir si habrá solicitud de cotizaciones.
- Definir manejo de compras recurrentes.
