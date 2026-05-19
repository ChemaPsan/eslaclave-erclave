# ERClave — Módulo de Ventas y Clientes

## 1. Objetivo

El módulo de Ventas y Clientes permitirá gestionar clientes, cotizaciones, pedidos, entregas, devoluciones y análisis de margen, conectando la demanda comercial con inventario, producción y costos.

---

## 2. Alcance

- clientes;
- contactos;
- direcciones;
- condiciones comerciales;
- listas de precios;
- cotizaciones;
- pedidos de venta;
- entregas;
- devoluciones;
- relación pedido-producción;
- relación pedido-inventario;
- margen estimado y real;
- historial comercial.

---

## 3. Entidades principales

| Entidad | Descripción |
|---|---|
| Cliente | Persona o empresa que compra productos o servicios. |
| Contacto | Persona relacionada con un cliente. |
| Dirección | Dirección fiscal, entrega o cobranza. |
| Lista de precios | Precios aplicables por cliente, producto o condición. |
| Cotización | Oferta enviada al cliente. |
| Pedido | Solicitud aceptada por el cliente. |
| Entrega | Registro de entrega parcial o total. |
| Devolución | Regreso de producto por parte del cliente. |

---

## 4. Flujo comercial recomendado

1. Se registra prospecto o cliente.
2. Se genera cotización.
3. El cliente aprueba la cotización.
4. Se genera pedido.
5. Se valida inventario disponible.
6. Se reserva inventario o se solicita producción.
7. Se registra entrega parcial o total.
8. Se emite factura o documento comercial, si aplica.
9. Se analiza margen.

---

## 5. Estados sugeridos

| Estado | Descripción |
|---|---|
| Borrador | Documento en captura. |
| Cotizado | Oferta enviada al cliente. |
| Aprobado | Cliente aceptó la cotización. |
| En preparación | Se está surtiendo o produciendo. |
| Parcialmente entregado | Entrega incompleta. |
| Entregado | Entrega completa. |
| Facturado | Documento fiscal o comercial emitido. |
| Cancelado | Operación cancelada. |

---

## 6. Reglas de negocio

- Un pedido podrá surtirse desde inventario o generar producción.
- Un pedido podrá reservar producto terminado.
- Antes de aprobar un pedido, el sistema deberá validar inventario disponible, inventario comprometido y posibilidad de producción.
- Una cotización aceptada deberá poder convertirse en pedido.
- Un pedido podrá tener entregas parciales.
- Las devoluciones deberán afectar inventario y margen.
- El precio podrá depender de lista, cliente, moneda o descuento.
- El margen deberá considerar costo estimado o costo real cuando esté disponible.
- Una venta de servicio podrá no afectar inventario físico, pero sí costos y reportes.
- Una venta deberá poder mapear cuentas contables de ingreso, cliente/cuenta por cobrar, impuestos y costo de venta.

---

## 7. Compatibilidad con producción, inventarios y contabilidad

### Al aprobar pedido

El sistema deberá:

- consultar inventario disponible;
- reservar producto terminado si existe;
- identificar faltantes;
- generar solicitud u orden de producción si no hay existencia suficiente;
- calcular margen estimado;
- validar centro de costos o centro de negocio;
- validar mapeo contable si Contabilidad está activa.

### Al entregar

El sistema deberá:

- generar salida de inventario;
- liberar reserva;
- calcular costo de venta;
- actualizar margen real;
- generar documento origen para Contabilidad;
- generar asiento contable si aplica.

### Al devolver

El sistema deberá:

- registrar devolución;
- definir si el producto vuelve a disponible, bloqueado, merma o revisión;
- ajustar margen;
- generar reverso contable o asiento correspondiente.

---

## 8. Integraciones

| Módulo | Relación |
|---|---|
| Producción | Producción bajo pedido. |
| Almacenes | Reserva, salida y devolución de producto. |
| Costos | Margen estimado y real. |
| Gastos | Fletes, comisiones o gastos comerciales. |
| Contabilidad | Ingresos, cuentas por cobrar, impuestos, costo de venta y reversos. |
| Reportes | Ventas, rentabilidad, cumplimiento y demanda. |

---

## 9. Métricas

- ventas por periodo;
- ventas por cliente;
- ventas por producto o servicio;
- pedidos pendientes;
- entregas pendientes;
- cumplimiento de entrega;
- margen por producto;
- margen por cliente;
- devoluciones;
- productos más vendidos;
- demanda futura.

---

## 10. Pendientes

- Definir si facturación fiscal será propia o integración externa.
- Definir políticas de descuento.
- Definir manejo de monedas.
- Definir reglas de crédito y cobranza.
- Definir campos mínimos de cliente.
