# ERClave — Módulo de Ventas y Clientes

## 1. Objetivo

El módulo de Ventas y Clientes permitirá gestionar clientes, cotizaciones, pedidos, entregas, devoluciones y análisis de margen, conectando la demanda comercial con inventario, producción y costos.

---

## 2. Alcance

- clientes;
- contactos;
- direcciones;
- perfil comercial del cliente;
- perfil fiscal o de facturacion del cliente;
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
| Cliente | Persona o empresa que compra productos o servicios. Debe conservar perfil comercial y perfil fiscal/facturacion. |
| Contacto | Persona relacionada con un cliente. |
| Dirección | Dirección fiscal, entrega o cobranza. |
| Perfil comercial | Datos usados para vender, cotizar, dar seguimiento y gestionar relacion comercial. |
| Perfil de facturacion | Datos fiscales usados para facturar o emitir documentos fiscales/comerciales. |
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

## 5. Alta de clientes

En MVP, el submodulo Clientes debera permitir:

- crear cliente;
- consultar clientes existentes;
- buscar por nombre comercial, razon social, RFC/ID fiscal, contacto, email, telefono o ejecutivo;
- editar datos comerciales y fiscales;
- mantener estatus de prospecto, activo, inactivo o bloqueado.

La ficha de cliente debera separar dos perfiles:

### Perfil comercial

Se usa para operacion de ventas, seguimiento y relacion con el cliente.

| Campo | Uso |
|---|---|
| Codigo de cliente | Clave interna estable. |
| Nombre comercial | Nombre con el que se identifica al cliente en la operacion diaria. |
| Tipo de cliente | Empresa, persona fisica, gobierno o interno. |
| Contacto | Persona principal para ventas o compras. |
| Email comercial | Medio de contacto operativo. |
| Telefono | Contacto rapido. |
| Ejecutivo comercial | Responsable interno del seguimiento. |
| Condiciones de pago | Contado, credito, parcialidades u otro acuerdo. |
| Limite de credito | Referencia para control comercial futuro. |
| Notas comerciales | Preferencias, horarios, acuerdos o restricciones. |

### Perfil de facturacion

Se usa para facturas, documentos fiscales o integraciones contables. Puede ser diferente al perfil comercial porque una empresa puede operar con un nombre comercial y facturar con otra razon social, persona fisica o persona moral.

| Campo | Uso |
|---|---|
| Razon social o nombre fiscal | Nombre oficial para facturacion. |
| RFC / ID fiscal | Identificador fiscal. |
| Regimen fiscal | Regimen aplicable cuando se use facturacion fiscal. |
| Uso CFDI | Uso fiscal requerido para facturacion en Mexico, si aplica. |
| Email de facturacion | Correo para envio de facturas o comprobantes. |
| Telefono de facturacion | Contacto de area administrativa. |
| Direccion fiscal | Calle, numero, colonia, ciudad, estado, codigo postal y pais. |

---

## 6. Cotizaciones

En MVP, el submodulo Cotizaciones debera permitir crear y consultar cotizaciones multipartida usando solo informacion previamente dada de alta:

- cliente existente del submodulo Clientes;
- una o varias partidas con producto o servicio existente del catalogo de Produccion;
- cantidad por partida;
- unidad por partida;
- precio unitario por partida;
- descuento por partida;
- vigencia;
- promesa de entrega;
- condiciones de pago;
- moneda;
- notas comerciales.

La cotizacion no debera permitir capturar clientes, productos o servicios como texto libre. Esto evita cotizaciones desconectadas de los maestros comerciales y operativos.

Reglas iniciales:

- Si no existe al menos un cliente, no se podra crear cotizacion.
- Si no existe al menos un producto o servicio, no se podra crear cotizacion.
- Al seleccionar cliente, se deberan sugerir condiciones de pago si existen.
- Al seleccionar producto o servicio, se deberan sugerir unidad y precio objetivo si existen.
- El subtotal y total se calculan sumando las partidas.
- La cotizacion debera permitir generar un PDF generico mediante impresion/guardar como PDF del navegador.
- La cotizacion podra estar en estado borrador, cotizada, aprobada o vencida.

---

## 7. Estados sugeridos

| Estado | Descripción |
|---|---|
| Prospecto | Cliente en proceso de validacion comercial o fiscal. |
| Borrador | Documento en captura. |
| Cotizado | Oferta enviada al cliente. |
| Aprobado | Cliente aceptó la cotización. |
| En preparación | Se está surtiendo o produciendo. |
| Parcialmente entregado | Entrega incompleta. |
| Entregado | Entrega completa. |
| Facturado | Documento fiscal o comercial emitido. |
| Cancelado | Operación cancelada. |

---

## 8. Reglas de negocio

- Un cliente podra tener nombre comercial distinto a la razon social o nombre fiscal.
- La informacion de facturacion debera validarse antes de emitir documentos fiscales.
- La creacion y edicion de clientes debera quedar restringida a usuarios autorizados cuando exista modulo de usuarios/permisos.
- Una cotizacion debera relacionarse con un cliente dado de alta.
- Una cotizacion debera usar productos o servicios dados de alta.
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

## 9. Compatibilidad con producción, inventarios y contabilidad

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

## 10. Integraciones

| Módulo | Relación |
|---|---|
| Producción | Producción bajo pedido. |
| Almacenes | Reserva, salida y devolución de producto. |
| Costos | Margen estimado y real. |
| Gastos | Fletes, comisiones o gastos comerciales. |
| Contabilidad | Ingresos, cuentas por cobrar, impuestos, costo de venta y reversos. |
| Reportes | Ventas, rentabilidad, cumplimiento y demanda. |

---

## 11. Métricas

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

## 12. Pendientes

- Definir si facturación fiscal será propia o integración externa.
- Definir políticas de descuento.
- Definir manejo de monedas.
- Definir reglas de crédito y cobranza.
- Definir permisos finales para alta, edicion y bloqueo de clientes.
- Definir plantillas avanzadas de PDF por tenant o marca en una fase posterior.
