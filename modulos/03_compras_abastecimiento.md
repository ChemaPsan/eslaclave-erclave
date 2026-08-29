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

---

## 12. Primer corte acordado

Estado: implementado en Local y activable desde Backoffice cuando Inventory esta habilitado.

El primer corte operativo cubrira exclusivamente:

1. proveedores activos e inactivos con perfil comercial, contacto y datos fiscales editables;
2. requisiciones multipardida manuales o referenciadas desde un faltante externo;
3. envio, aprobacion, rechazo y cancelacion de requisiciones;
4. orden de compra creada desde requisicion aprobada o como compra directa con motivo auditado;
5. emision y cancelacion de orden;
6. recepcion parcial o total de lineas inventariables contra una orden emitida;
7. solicitud idempotente a Inventory para registrar la entrada en el almacen autorizado.

Factura, XML/PDF, cuenta por pagar, pago, devolucion a proveedor, solicitud de cotizaciones, evaluacion avanzada y asiento contable permanecen `planned`.

## 13. Tipos de linea y ownership

| Tipo | Referencia autoritativa | Resultado del primer corte |
|---|---|---|
| `inventory_item` | Articulo y unidad base de `inventory-service`; unidad activa de Admin | Puede recibirse fisicamente en un almacen mediante contrato de Inventory. |
| `service` | Descripcion snapshot y unidad activa de Admin | Puede requisitarse y ordenarse; la confirmacion financiera queda planeada para Gastos/CxP. |
| `asset` | Objetivo futuro | No admitido hasta definir Activos Fijos, capitalizacion y ownership. |

Compras es dueno de proveedor, requisicion, orden, precio pactado, moneda, condiciones y recepcion comercial. Inventory sigue siendo dueno del articulo, almacen, movimiento fisico, saldo y valuacion. No hay FK ni escritura directa entre schemas.

### Perfil fiscal del proveedor

- Todo proveedor nuevo exige razon social, RFC mexicano, regimen fiscal, correo de facturacion y codigo postal fiscal.
- RFC y correos se normalizan en backend; el RFC es unico dentro del tenant y puede repetirse en otro tenant.
- Domicilio fiscal, contacto, telefono y sitio web complementan el maestro y permanecen editables con `purchasing.supplier.update`.
- Los proveedores heredados sin perfil completo siguen visibles; al tocar cualquier campo fiscal deben completar el conjunto minimo.
- Facturas y documentos fiscales futuros deberan guardar su propio snapshot; nunca dependeran de consultar retrospectivamente el maestro editable.

## 14. Maquinas de estado del primer corte

### Requisicion

```text
draft -> submitted -> approved -> converted
                  \-> rejected
draft|submitted|approved -> cancelled
```

- Solo `draft` se edita.
- Una requisicion contiene una o mas partidas. Cada partida inventariable conserva articulo por ID, descripcion, cantidad y unidad base validada por Inventory.
- El mismo articulo no se repite dentro del documento; su necesidad se consolida ajustando la cantidad de una sola partida.
- La interfaz permite agregar y quitar partidas antes del guardado y muestra todas las partidas en el resumen del documento.
- Aprobar exige al menos una linea valida y permiso propio.
- `converted` es terminal y conserva la orden creada.
- Una requisicion rechazada no se convierte; para corregir se crea una nueva revision/documento en un corte posterior.

### Orden de compra

```text
draft -> issued -> partially_received -> received -> closed
   \-> cancelled       \-> cancelled (solo saldo no recibido)
```

- Solo `draft` se edita.
- Al convertir una requisicion multipardida, cada linea captura su propio precio unitario; no se reutiliza un precio global para articulos distintos.
- Una orden ligada conserva exactamente tipo, articulo, descripcion, cantidad y unidad de cada partida de la requisicion; solo agrega precio negociado. El backend vuelve a validar esta relacion al crear o editar.
- El primer corte convierte todas las partidas seleccionadas a una orden y un proveedor. Dividir una requisicion entre varios proveedores permanece planeado.
- Emitir congela proveedor, moneda, condiciones, precios y cantidades como snapshot.
- No se recibe una orden `draft` o `cancelled`.
- Cancelar despues de una recepcion conserva lo ya recibido y cancela solamente el saldo abierto.

### Recepcion

```text
processing -> completed
          \-> needs_reconciliation
```

- Cada cantidad debe ser positiva y no superar el saldo abierto de su linea.
- Cada linea inventariable exige almacen destino activo y unidad compatible.
- La clave idempotente de entrada a Inventory se deriva de recepcion y linea; un reintento no duplica el movimiento.
- Si Inventory confirma y Compras pierde la respuesta, la recepcion queda `needs_reconciliation`; nunca se revierte el movimiento fisico desde SQL de Compras.
- La recepcion puede registrar varias partidas de una misma orden. El saldo se reclama dentro de la transaccion que bloquea orden y lineas; una segunda solicitud concurrente observa el reclamo pendiente y no puede sobre-recibir.
- Conciliar reintenta solo lineas no completadas y conserva la misma clave de movimiento Inventory; las cantidades ya confirmadas no vuelven a sumarse.

## 15. Permisos del primer corte

| Recurso | Lectura | Comandos |
|---|---|---|
| Proveedor | `purchasing.supplier.read` | `purchasing.supplier.create`, `purchasing.supplier.update` |
| Requisicion | `purchasing.requisition.read` | `create`, `update`, `submit`, `approve`, `reject`, `cancel` |
| Orden | `purchasing.order.read` | `create`, `update`, `issue`, `cancel` |
| Recepcion | `purchasing.receipt.read` | `purchasing.receipt.create`, `purchasing.receipt.reconcile` |

La segregacion no se implementa con nombres fijos de rol. Cada accion usa permiso puntual; una politica futura por monto/centro complementara, no sustituira, el permiso.

## 16. Dependencias de activacion

- `admin`: siempre obligatorio y autoridad de sesion, permisos, unidades, monedas, condiciones de pago y folios.
- `inventory`: dependencia obligatoria del primer corte porque toda recepcion implementada es inventariable.
- `hr`: no es dependencia inicial; el actor autenticado se conserva como solicitante/aprobador/comprador. La seleccion de trabajadores se agregara solo con regla funcional aprobada.
- Gastos, Costos y Contabilidad son consumidores futuros y no bloquean la activacion inicial.

Compras solo cambia de `planned` a `implemented` cuando existan simultaneamente servicio, persistencia/migracion, contrato runtime, permisos, autorizacion, frontend API real, pruebas, observabilidad y rollback Local.

## 17. Continuidad operativa CHG-238

La interfaz hace explicito el recorrido que ya soporta el servicio:

1. una requisicion `submitted` se aprueba con `purchasing.requisition.approve`;
2. al aprobar, quien tambien posea `purchasing.order.create` llega a **Ordenes de compra** con la requisicion precargada;
3. captura folio, proveedor activo y precio unitario de cada partida, y crea la orden en `draft`;
4. quien posea `purchasing.order.issue` emite la orden y congela sus condiciones;
5. quien posea `purchasing.receipt.create` llega a **Recepciones** con la orden precargada y registra cantidades y almacenes destino.

La requisicion aprobada conserva ademas una accion **Crear orden de compra** mientras no haya sido convertida. Crear la orden cambia la requisicion a `converted`; emitir y recibir siguen siendo comandos separados para conservar segregacion de funciones. El frontend oculta cada formulario y transicion sin su permiso puntual, y el backend permanece como autoridad final.

## 18. Separacion OC y Reabastecimiento CHG-240

- **Ordenes de compra** lista primero todas las OC del tenant sin filtro de estatus y muestra folio, fecha, proveedor, importe, partidas, requisicion origen y estado.
- La captura de una nueva OC aparece solo cuando existe al menos una requisicion `approved` pendiente de conversion, o cuando se edita una orden `draft` existente.
- Si no hay candidatas, la pantalla conserva el historial y dirige a Requisiciones; no presenta un selector vacio.
- **Reabastecimiento** es una ruta `planned` distinta. Explica futuras sugerencias por minimos, punto de reorden, demanda, ordenes abiertas y lead time; no lista ni crea OC.
- Los IDs de los cinco submodulos de Compras quedan explicitos en el catalogo de navegacion para evitar depender de la normalizacion del texto visible.
