# ERClave — Módulo de Gastos y Cuentas por Pagar

## 1. Objetivo

El módulo de Gastos y Cuentas por Pagar permitirá registrar, clasificar y asignar gastos mediante XML, PDF y documentos relacionados, conectándolos con centros de costos, órdenes de producción, almacenes, proveedores y proyectos.

---

## 2. Alcance

- carga de XML fiscal;
- carga de PDF de soporte;
- proveedores;
- conceptos de gasto;
- centros de costos;
- órdenes de compra relacionadas;
- gastos directos e indirectos;
- vencimientos;
- pagos;
- cuentas por pagar básicas;
- asignaciones a producción, almacén, producto, servicio o proyecto.

---

## 3. Entidades principales

| Entidad | Descripción |
|---|---|
| Gasto | Registro administrativo de egreso. |
| Documento XML | Comprobante fiscal estructurado. |
| Documento PDF | Soporte visual o administrativo. |
| Proveedor | Emisor del documento o prestador del servicio. |
| Cuenta por pagar | Obligación pendiente de pago. |
| Pago | Registro de liquidación total o parcial. |
| Concepto de gasto | Clasificación del egreso. |
| Asignación | Relación del gasto con centro, orden, producto o servicio. |

---

## 4. Datos extraídos del XML

- RFC emisor;
- proveedor;
- folio fiscal;
- fecha;
- subtotal;
- impuestos;
- total;
- conceptos;
- método de pago;
- moneda;
- uso fiscal, si aplica;
- UUID;
- estado de validación, si aplica.

---

## 5. Clasificación de gastos

| Tipo de gasto | Posible asignación |
|---|---|
| Materia prima | Inventario, producto, orden de producción. |
| Mantenimiento | Máquina, área, centro de costos. |
| Servicios generales | Centro de costos, área o corporativo. |
| Energía | Producción general, centro de costos, planta. |
| Renta | Centro de negocio o corporativo. |
| Flete | Compra, venta, producto o cliente. |
| Herramientas | Almacén de herramientas o gasto operativo. |
| Mano de obra externa | Orden de producción, servicio o proyecto. |

---

## 6. Estados sugeridos

| Estado | Descripción |
|---|---|
| Capturado | Gasto registrado manualmente o por carga. |
| Validado | Información revisada. |
| Asignado | Gasto relacionado con centro, orden o módulo. |
| Pendiente de pago | Documento no pagado. |
| Parcialmente pagado | Tiene pagos parciales. |
| Pagado | Liquidado. |
| Cancelado | Documento cancelado o invalidado. |

---

## 7. Reglas de negocio

- Un gasto podrá existir aunque no tenga orden de compra.
- Un gasto con XML deberá almacenar datos fiscales relevantes.
- Un gasto podrá asignarse a varios centros de costos si se requiere prorrateo.
- Un gasto de materia prima podrá convertirse o relacionarse con entrada de inventario.
- Un gasto de mantenimiento podrá asociarse a una máquina.
- Los pagos deberán conservar historial.
- Las cancelaciones deberán conservar trazabilidad.
- Todo gasto validado deberá poder mapearse a una cuenta contable.
- Todo gasto con documento soporte deberá poder enviarse como anexo a Contabilidad.
- Las operaciones sin mapeo contable deberán quedar pendientes de contabilización.

---

## 8. Compatibilidad con costos y contabilidad

### Al validar gasto

El sistema deberá:

- clasificar el gasto;
- asignarlo a centro de costos, orden, producto, servicio, almacén o proyecto;
- identificar si es directo, indirecto, inventariable o administrativo;
- enviar importes a Costos cuando corresponda;
- generar cuenta por pagar si no está pagado;
- generar asiento contable si el mapeo existe;
- marcarlo como pendiente de mapeo si falta cuenta contable.

### Al registrar pago

El sistema deberá:

- disminuir cuenta por pagar;
- asociar comprobante de pago;
- generar asiento contable;
- conservar trazabilidad con gasto, proveedor y anexo.

---

## 9. Integraciones

| Módulo | Relación |
|---|---|
| Compras | Facturas contra órdenes de compra. |
| Almacenes | Compras que afectan inventario. |
| Producción | Gastos directos de una orden. |
| Costos | Asignación y prorrateo de gastos. |
| Contabilidad | Cuentas por pagar, pagos, anexos, impuestos y asientos. |
| Reportes | Gastos por periodo, proveedor, centro y categoría. |

---

## 10. Métricas

- gastos por centro de costos;
- gastos por proveedor;
- gastos pendientes de pago;
- vencimientos próximos;
- gastos por categoría;
- gastos asignados a producción;
- gastos sin asignar;
- variación de gastos por periodo.

---

## 11. Pendientes

- Definir validación fiscal requerida.
- Definir reglas de prorrateo.
- Definir manejo de pagos parciales.
- Definir integración bancaria futura.
- Definir permisos para cancelar gastos.
