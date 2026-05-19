# ERClave — Módulo de Contabilidad

## 1. Objetivo

El módulo de Contabilidad estará enfocado en registrar, consultar, justificar y analizar los asientos contables generados por la operación de ERClave.

Cada ingreso, gasto, compra, venta, pago, movimiento relevante o ajuste deberá poder mapearse a una cuenta contable. Cada registro contable deberá conservar su anexo o documento soporte para justificar la operación.

Este módulo deberá responder:

> Qué operación ocurrió, cómo se contabilizó, en qué periodo quedó registrada, qué cuentas afectó y con qué documento se justifica.

---

## 2. Alcance

- catálogo de cuentas contables;
- periodos contables;
- asientos contables;
- pólizas o registros contables;
- cargos y abonos;
- anexos por registro;
- mapeo contable de ingresos;
- mapeo contable de gastos;
- mapeo contable de compras;
- mapeo contable de ventas;
- mapeo contable de costos;
- consulta por periodo;
- consulta por cuenta;
- consulta por centro de costos;
- trazabilidad contra documentos origen;
- reportes contables básicos.

---

## 3. Principio contable base

Cada operación contable deberá registrar al menos:

- periodo contable;
- fecha contable;
- fecha de operación;
- tipo de operación;
- documento origen;
- cuenta contable;
- centro de costos, si aplica;
- cargo;
- abono;
- moneda;
- tipo de cambio, si aplica;
- referencia;
- usuario que generó o autorizó;
- anexo o soporte documental;
- estado.

El sistema deberá permitir ver los asientos contables de acuerdo con el periodo seleccionado.

---

## 4. Entidades principales

| Entidad | Descripción |
|---|---|
| Cuenta contable | Cuenta del catálogo contable usada para clasificar operaciones. |
| Catálogo de cuentas | Estructura de cuentas contables del tenant. |
| Periodo contable | Mes, año o rango en el que se registran operaciones. |
| Asiento contable | Conjunto de movimientos contables balanceados. |
| Línea contable | Cargo o abono individual dentro de un asiento. |
| Póliza | Documento contable que agrupa un asiento y sus anexos. |
| Anexo | Evidencia documental que justifica la operación. |
| Mapeo contable | Regla que define qué cuenta se usa para cada tipo de operación. |
| Documento origen | Venta, gasto, compra, pago, ajuste, movimiento o documento operativo que generó contabilidad. |

---

## 5. Catálogo de cuentas

Cada tenant deberá poder configurar su propio catálogo de cuentas contables.

### Datos sugeridos de una cuenta

- código de cuenta;
- nombre;
- tipo de cuenta;
- nivel;
- cuenta padre;
- naturaleza;
- estado;
- moneda, si aplica;
- requiere centro de costos;
- requiere anexo;
- permite movimientos;
- descripción.

### Tipos de cuenta

| Tipo | Ejemplos |
|---|---|
| Activo | Bancos, clientes, inventarios, anticipos. |
| Pasivo | Proveedores, impuestos por pagar, acreedores. |
| Capital | Capital social, utilidades retenidas. |
| Ingreso | Ventas, servicios, otros ingresos. |
| Costo | Costo de ventas, costo de producción. |
| Gasto | Gastos administrativos, ventas, mantenimiento. |
| Orden o control | Cuentas de control o seguimiento interno, si aplica. |

---

## 6. Periodos contables

El módulo deberá permitir trabajar por periodos.

### Estados sugeridos de periodo

| Estado | Descripción |
|---|---|
| Abierto | Permite registrar y modificar asientos autorizados. |
| En revisión | Permite revisión, pero limita cambios operativos. |
| Cerrado | No permite nuevos movimientos ordinarios. |
| Reabierto | Periodo cerrado habilitado temporalmente con autorización. |

### Reglas de periodo

- Un asiento deberá pertenecer a un periodo contable.
- No se deberán registrar movimientos ordinarios en periodos cerrados.
- La reapertura de un periodo deberá requerir permiso especial.
- Los cambios en periodos cerrados deberán auditarse.
- Los reportes deberán poder filtrarse por periodo.

---

## 7. Asientos contables

Un asiento contable deberá estar compuesto por una o varias líneas contables.

### Reglas base

- Todo asiento deberá estar balanceado: total cargos = total abonos.
- Cada línea deberá tener cuenta contable.
- Cada línea podrá tener centro de costos.
- Cada línea podrá relacionarse con un documento origen.
- Cada asiento deberá conservar anexos o referencias.
- No se deberán borrar asientos autorizados; deberán reversarse o cancelarse.

### Estados sugeridos de asiento

| Estado | Descripción |
|---|---|
| Borrador | Asiento en captura o generado automáticamente sin validar. |
| Generado | Asiento creado desde una operación del sistema. |
| Validado | Revisado por usuario autorizado. |
| Contabilizado | Registrado formalmente en el periodo. |
| Reversado | Anulado mediante asiento inverso. |
| Cancelado | Cancelado antes de contabilizarse. |

---

## 8. Anexos contables

Cada registro contable deberá poder tener anexos.

### Tipos de anexo

- XML fiscal;
- PDF de factura;
- comprobante de pago;
- orden de compra;
- recepción;
- pedido de venta;
- cotización;
- contrato;
- evidencia de entrega;
- documento interno;
- archivo complementario.

### Reglas de anexos

- Un asiento podrá tener uno o varios anexos.
- Una línea contable podrá referenciar un anexo específico.
- El sistema deberá conservar la relación entre asiento y documento origen.
- Los anexos no deberán sustituir la trazabilidad del sistema, sino complementarla.
- Los anexos deberán respetar permisos del tenant y del usuario.

---

## 9. Mapeo contable

El mapeo contable definirá qué cuenta se afecta según el tipo de operación.

### Ejemplos de mapeo

| Operación | Cuenta sugerida |
|---|---|
| Venta de producto | Ingresos por ventas. |
| Venta de servicio | Ingresos por servicios. |
| Costo de producto vendido | Costo de ventas. |
| Compra de materia prima | Inventario de materia prima. |
| Consumo de materia prima | Costo de producción o producto en proceso. |
| Gasto de mantenimiento | Gasto de mantenimiento. |
| Gasto de energía | Gasto de energía o costo indirecto. |
| Factura pendiente de pago | Proveedores o cuentas por pagar. |
| Cobranza de cliente | Bancos contra clientes. |
| Pago a proveedor | Proveedores contra bancos. |
| Ajuste de inventario | Inventario contra variación o ajuste. |
| Merma | Costo de merma o variación de producción. |

### Niveles de mapeo

El mapeo podrá definirse por:

- tenant;
- módulo;
- tipo de operación;
- producto;
- servicio;
- categoría de gasto;
- proveedor;
- cliente;
- centro de costos;
- almacén;
- impuesto;
- moneda.

### Reglas de mapeo

- Una operación no deberá contabilizarse sin cuenta contable requerida.
- Si no existe mapeo específico, podrá usarse un mapeo general definido por el tenant.
- Las reglas de mapeo deberán tener vigencia.
- Los cambios de mapeo deberán auditarse.
- El asiento generado deberá conservar la regla de mapeo usada.

### Mapeos mínimos por módulo

| Módulo origen | Mapeos requeridos |
|---|---|
| Ventas | ingresos, clientes/cuentas por cobrar, impuestos, costo de venta, devoluciones. |
| Gastos | gasto por categoría, proveedor/cuenta por pagar, impuestos, pagos. |
| Compras | inventario, proveedor/cuenta por pagar, impuestos, fletes, servicios. |
| Almacenes | inventario, ajustes, merma, transferencias, producto terminado. |
| Producción | consumo de materia prima, producto en proceso, producto terminado, merma. |
| Costos | costo de ventas, variaciones, costos indirectos, centros de costos. |

---

## 10. Flujos principales

### Registro automático desde gasto

1. Se carga o registra un gasto.
2. Se identifica proveedor, concepto, importe e impuestos.
3. Se asigna centro de costos o módulo relacionado.
4. El sistema identifica cuentas contables mediante mapeo.
5. Se genera asiento contable.
6. Se adjuntan XML/PDF como anexos.
7. El asiento queda disponible para validación o contabilización.

### Registro automático desde venta

1. Se registra venta o factura comercial.
2. Se identifica cliente, producto/servicio, importe e impuestos.
3. Se identifican cuentas de ingreso, cliente/cobranza e impuestos.
4. Si aplica, se genera costo de venta.
5. Se genera asiento contable.
6. Se anexan documentos soporte.

### Registro manual

1. Usuario autorizado crea asiento manual.
2. Captura líneas de cargo y abono.
3. Asocia periodo, cuentas, centro de costos y anexos.
4. El sistema valida balance.
5. Usuario valida o contabiliza.

### Reverso

1. Usuario autorizado solicita reverso.
2. El sistema genera asiento inverso.
3. Se conserva relación con asiento original.
4. Ambos registros quedan auditados.

---

## 11. Reportes contables

Reportes iniciales sugeridos:

- asientos por periodo;
- pólizas por periodo;
- movimientos por cuenta;
- movimientos por centro de costos;
- auxiliares contables;
- balanza de comprobación;
- ingresos por cuenta;
- gastos por cuenta;
- cuentas por pagar contables;
- cuentas por cobrar contables;
- movimientos sin anexo;
- operaciones sin mapeo contable;
- asientos descuadrados o pendientes de validar.

---

## 12. Reglas de negocio

- Todo asiento contabilizado deberá estar balanceado.
- Todo movimiento deberá pertenecer a un periodo.
- Cada ingreso y gasto deberá mapearse a una cuenta contable.
- Cada registro deberá poder justificarse con anexo o documento origen.
- Los asientos generados automáticamente deberán poder revisarse antes de contabilizarse, según configuración.
- Los asientos manuales deberán requerir permisos especiales.
- No se deberán eliminar asientos contabilizados.
- Los reversos deberán generar asientos inversos.
- Las cuentas inactivas no deberán aceptar nuevos movimientos.
- Las operaciones sin mapeo deberán quedar pendientes y visibles para corrección.
- Contabilidad no deberá recapturar operaciones ya existentes en otros módulos; deberá recibirlas como documentos origen.
- Un periodo contable cerrado deberá bloquear o advertir operaciones con impacto contable en ese periodo.
- Cada asiento automático deberá conservar referencia al módulo origen, documento origen y regla de mapeo usada.

---

## 13. Contrato de recepción desde otros módulos

Para generar un asiento automático, Contabilidad deberá recibir:

- tenant;
- centro de negocio;
- fecha de operación;
- periodo sugerido;
- módulo origen;
- documento origen;
- tipo de operación;
- importe;
- impuestos;
- moneda;
- centro de costos, si aplica;
- tercero relacionado, si aplica;
- anexos;
- líneas sugeridas o regla de mapeo.

### Respuesta de Contabilidad

Contabilidad deberá responder:

- asiento generado;
- estado contable;
- cuentas afectadas;
- errores de mapeo;
- periodo contable;
- necesidad de revisión;
- referencia para reportes.

---

## 14. Roles y permisos sugeridos

| Rol | Alcance |
|---|---|
| Contador | Consulta, captura, validación y reportes contables. |
| Supervisor contable | Autorización, reversos y cierre de periodos. |
| Administrador financiero | Configuración de cuentas y mapeos. |
| Auditor | Consulta de asientos, anexos y bitácora. |
| Usuario operativo | Puede generar documentos origen, pero no modificar contabilidad. |

### Permisos sugeridos

```text
accounting.accounts.read
accounting.accounts.create
accounting.accounts.update
accounting.entries.read
accounting.entries.create
accounting.entries.validate
accounting.entries.post
accounting.entries.reverse
accounting.periods.close
accounting.periods.reopen
accounting.mappings.update
accounting.attachments.read
```

---

## 15. Integraciones

| Módulo | Relación |
|---|---|
| Ventas | Ingresos, clientes, impuestos, costo de venta y cobranza. |
| Gastos | Gastos, proveedores, impuestos, cuentas por pagar y pagos. |
| Compras | Inventario, proveedores, recepciones y facturas. |
| Almacenes | Inventario, ajustes, merma y costo de movimientos. |
| Producción | Costo de producción, producto en proceso y producto terminado. |
| Costos | Costos reales, variaciones y rentabilidad. |
| Reportes | Balanza, auxiliares, asientos y análisis financiero. |
| Administración | Catálogos, permisos, periodos y configuración por tenant. |

---

## 16. Métricas y controles

- asientos por periodo;
- asientos pendientes de validar;
- operaciones sin mapeo contable;
- registros sin anexo;
- cuentas con movimientos;
- gastos por cuenta;
- ingresos por cuenta;
- variaciones contables;
- periodos abiertos;
- reversos realizados;
- movimientos manuales vs. automáticos.

---

## 17. Pendientes

- Definir catálogo de cuentas inicial sugerido.
- Definir estructura de pólizas.
- Definir reglas fiscales por país.
- Definir reportes contables del MVP.
- Definir si se permitirá exportación a sistemas contables externos.
- Definir reglas de impuestos.
- Definir cierre mensual.
- Definir permisos para reapertura de periodos.
