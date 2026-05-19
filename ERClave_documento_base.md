# ERClave — Documento Base del Proyecto

## 1. Contexto general

**ERClave** será un nuevo proyecto bajo la marca paraguas **EsLaClave**, inspirado en la lógica modular de un ERP, pero pensado para iniciar de forma más simple, flexible y escalable.

El enfoque inicial será la **industria manufacturera**, especialmente fábricas o negocios que requieren controlar su producción, recursos, costos, almacenes y posteriormente procesos administrativos como ventas, gastos, compras y centros de costos.

Aunque el primer enfoque será manufactura, el sistema deberá diseñarse de forma modular para que también pueda adaptarse a empresas que prestan **servicios**, no únicamente a empresas que fabrican productos físicos.

---

## 2. Visión del producto

ERClave busca convertirse en una plataforma modular de gestión operativa y administrativa para empresas que necesitan controlar sus procesos internos sin implementar un ERP complejo, costoso o sobredimensionado.

La primera versión iniciará con un módulo de **Producción**, enfocado en permitir que una empresa configure sus productos o servicios mediante recetas, genere órdenes de producción y obtenga información útil para calcular costos, coordinar áreas y medir la eficiencia operativa.

### Definición inicial

> ERClave será una plataforma modular de gestión operativa y administrativa para empresas manufactureras, fábricas y negocios que producen bienes o prestan servicios bajo procesos repetibles.

### Idea base

> Registrar qué se necesita para producir algo, cuánto se necesita, quién interviene, cuánto tiempo toma, qué recursos consume y cuánto cuesta producirlo.

### Principios funcionales inspirados en ERP empresariales

ERClave tomará como referencia buenas prácticas comunes en ERP empresariales como SAP, Oracle y NetSuite, pero sin intentar replicar su complejidad desde el inicio.

El objetivo será adoptar los principios que hacen valioso a un ERP:

- una sola fuente de verdad para productos, servicios, clientes, proveedores, inventarios, costos y operaciones;
- trazabilidad entre producción, inventario, compras, ventas, gastos y costos;
- procesos configurables por empresa, área, centro de costos y centro de negocio;
- catálogos maestros consistentes;
- estados claros por documento o proceso;
- autorizaciones y responsabilidades por rol;
- reportes operativos y administrativos conectados con la información real;
- capacidad de crecer por módulos sin rehacer el sistema.

ERClave no deberá iniciar como un ERP completo, sino como una plataforma modular que pueda llegar a comportarse como uno conforme se activen nuevos módulos.

---

## 3. Primer módulo: Producción

### Objetivo del módulo

Permitir a la empresa configurar recetas de producción para productos o servicios, generar órdenes de producción a partir de esas recetas y controlar los recursos necesarios para ejecutar el proceso.

El módulo deberá servir como base para que, en futuras etapas, el sistema pueda calcular costos, coordinar áreas, controlar almacenes, registrar ventas, asignar gastos y generar métricas de producción.

---

## 4. Recetas de producción

La receta será la base del módulo de Producción. Representa la estructura necesaria para fabricar un producto o ejecutar un servicio.

Una receta deberá permitir registrar:

- Materias primas.
- Herramientas.
- Maquinaria.
- Mano de obra directa.
- Procesos o etapas.
- Subprocesos.
- Versiones de receta.
- Rendimiento esperado.
- Merma esperada.
- Cantidades.
- Unidades de medida.
- Tiempos de trabajo.
- Costos estimados.
- Responsables o áreas involucradas.
- Instrucciones operativas.
- Archivos adjuntos o especificaciones técnicas.
- Vigencia de la receta.

### Consideraciones adicionales

La receta deberá funcionar como una versión simple de una lista de materiales y ruta de producción.

En ERPs grandes, estos conceptos suelen dividirse en:

- **lista de materiales**: qué insumos componen el producto;
- **ruta de producción**: qué pasos deben ejecutarse;
- **centros de trabajo**: dónde o con qué capacidad se realiza cada paso;
- **versiones**: qué cambios existen entre una receta anterior y una vigente.

Para ERClave, estos conceptos deberán simplificarse en una receta clara, pero preparada para crecer.

---

## 5. Componentes de una receta

### 5.1 Materias primas

Las materias primas representan los insumos consumibles necesarios para fabricar un producto o ejecutar un servicio.

Ejemplo:

| Insumo | Cantidad | Unidad de medida |
|---|---:|---|
| Tela algodón | 2.5 | metros |
| Hilo | 1 | carrete |
| Etiqueta | 1 | pieza |

El sistema deberá permitir manejar diferentes unidades de medida, por ejemplo:

- piezas
- metros
- kilogramos
- litros
- horas
- minutos
- cajas
- paquetes
- unidades personalizadas

---

### 5.2 Herramientas

Las herramientas representan recursos reutilizables que pueden ser necesarios durante la producción, pero que no necesariamente se consumen.

Ejemplo:

| Herramienta | Cantidad requerida | Uso estimado |
|---|---:|---|
| Tijeras industriales | 1 | Durante corte |
| Moldes | 1 | Preparación |

Las herramientas podrán utilizarse para:

- asignación a una orden de producción;
- control de disponibilidad;
- control de préstamo o resguardo;
- asociación con un área o responsable;
- trazabilidad del uso operativo.

---

### 5.3 Maquinaria

La maquinaria representa equipos productivos utilizados durante el proceso.

Ejemplo:

| Máquina | Tiempo de uso | Unidad |
|---|---:|---|
| Máquina recta | 30 | minutos |
| Cortadora industrial | 15 | minutos |
| Máquina overlock | 20 | minutos |

El registro de maquinaria permitirá calcular en el futuro:

- tiempo total de máquina;
- costo por hora máquina;
- disponibilidad de maquinaria;
- carga de trabajo por equipo;
- mantenimiento o uso acumulado;
- capacidad instalada.

---

### 5.4 Mano de obra directa

La mano de obra directa representa a los operadores o trabajadores que participan directamente en el proceso productivo.

Ejemplo:

| Rol / operador | Tiempo requerido | Unidad |
|---|---:|---|
| Operador de corte | 20 | minutos |
| Costurero | 45 | minutos |
| Supervisor | 10 | minutos |

El registro de mano de obra permitirá calcular:

- costo de mano de obra;
- horas hombre;
- productividad;
- tiempos estándar;
- capacidad operativa;
- carga de trabajo por responsable o área.

---

### 5.5 Procesos o etapas

Cada receta podrá dividirse en procesos o etapas.

Ejemplo para producto:

1. Corte.
2. Preparación.
3. Ensamble.
4. Acabado.
5. Revisión de calidad.
6. Empaque.

Ejemplo para servicio:

1. Diagnóstico.
2. Preparación de materiales.
3. Ejecución.
4. Validación.
5. Entrega.

Esta estructura permitirá que ERClave no quede limitado únicamente a manufactura física, sino que también pueda adaptarse a servicios operativos.

---

## 6. Órdenes de producción

Una vez cargada una receta, el usuario podrá generar una orden de producción indicando:

- producto o servicio a producir;
- receta base;
- cantidad de piezas o servicios;
- fecha requerida;
- responsable general;
- áreas involucradas;
- prioridad;
- observaciones;
- centro de costos;
- almacén origen de insumos;
- almacén destino del producto terminado.

### Ejemplo

> Producir 100 playeras modelo básico morado usando la receta “Playera básica algodón”, con entrega el 25 de mayo.

El sistema deberá multiplicar automáticamente los recursos de la receta por la cantidad solicitada.

Ejemplo:

Si una playera requiere:

- 2 metros de tela;
- 30 minutos de costura;
- 1 etiqueta.

Para 100 playeras, la orden deberá calcular:

- 200 metros de tela;
- 3,000 minutos de costura;
- 100 etiquetas.

---

## 7. Entregables por área

La orden de producción deberá poder dividirse por responsables o áreas.

### 7.1 Área de corte

Debe recibir:

- cantidad a cortar;
- materiales requeridos;
- medidas o especificaciones;
- fecha límite;
- observaciones.

### 7.2 Área de costura

Debe recibir:

- piezas a ensamblar;
- máquinas asignadas;
- tiempo estimado;
- responsable;
- instrucciones.

### 7.3 Área de calidad

Debe recibir:

- cantidad a revisar;
- criterios de aceptación;
- defectos esperados o controlables;
- resultado de revisión.

Esto permitirá que cada responsable tenga una vista clara de su trabajo sin necesidad de visualizar toda la operación administrativa.

---

## 8. Almacenes futuros

Desde el diseño inicial, ERClave deberá contemplar la posibilidad de manejar diferentes tipos de almacenes, configurables de acuerdo con la operación de cada empresa.

Tipos posibles:

| Tipo de almacén | Uso |
|---|---|
| Materias primas | Insumos consumibles |
| Herramientas | Recursos reutilizables |
| Maquinaria | Equipos productivos |
| Producto en proceso | Producción incompleta |
| Producto terminado | Inventario listo para venta |
| Desechos | Merma, scrap o desperdicio |
| Refacciones | Piezas para mantenimiento |
| Servicios | Recursos no físicos o capacidades operativas |

### Consideraciones

El sistema no deberá asumir que todos los almacenes se comportan igual.

Ejemplos:

- La materia prima se consume.
- La herramienta se asigna, pero no necesariamente se consume.
- La maquinaria se agenda o se usa por tiempo.
- El producto terminado se incrementa al cerrar producción.
- El desecho puede registrarse como merma.
- Un servicio puede no generar inventario físico, pero sí costos y tiempos.

### Funcionalidades futuras de inventario

Tomando como referencia capacidades comunes de ERP grandes, ERClave deberá considerar gradualmente:

- existencias por almacén;
- existencias por ubicación interna;
- mínimos, máximos y puntos de reorden;
- unidades de compra, almacenamiento y consumo;
- conversiones entre unidades;
- lotes;
- series;
- caducidades, cuando aplique;
- reservas de inventario para órdenes de producción o ventas;
- inventario disponible, apartado, en tránsito y comprometido;
- transferencias entre almacenes;
- conteos físicos;
- ajustes de inventario;
- kardex o historial de movimientos;
- valuación de inventario;
- costo promedio, último costo o costo estándar;
- trazabilidad de insumos hacia producto terminado;
- merma, scrap y desperdicio;
- inventario en proceso;
- inventario en consignación, si aplica en etapas futuras.

### Tipos de movimientos

El sistema deberá poder distinguir movimientos como:

| Movimiento | Descripción |
|---|---|
| Entrada por compra | Incrementa materia prima o recursos comprados. |
| Salida por producción | Consume insumos para una orden. |
| Entrada por producción terminada | Incrementa producto terminado. |
| Transferencia | Mueve inventario entre almacenes o ubicaciones. |
| Ajuste positivo | Corrige inventario agregando cantidad. |
| Ajuste negativo | Corrige inventario disminuyendo cantidad. |
| Merma | Registra desperdicio o pérdida productiva. |
| Devolución | Regresa producto o insumo a un almacén. |
| Reserva | Aparta inventario para una orden o venta. |

### Reglas iniciales recomendadas

- Todo movimiento de inventario deberá tener fecha, usuario, origen, destino, motivo y referencia.
- Los movimientos no deberán borrarse; deberán cancelarse o reversarse para mantener trazabilidad.
- Una orden de producción deberá poder reservar insumos antes de consumirlos.
- El cierre de producción deberá generar entrada de producto terminado, si aplica.
- Las mermas deberán poder asociarse a una orden, área, producto, insumo o responsable.

---

## 9. Ventas

En una etapa posterior, el sistema podrá registrar ventas de productos o servicios.

La venta deberá poder afectar:

- almacén de producto terminado;
- costos del producto vendido;
- ingresos;
- margen;
- centro de costos;
- trazabilidad contra producción.

### Ejemplo

Si se venden 20 piezas de un producto terminado, el sistema deberá poder:

1. descontar 20 piezas del almacén correspondiente;
2. identificar el costo de producción de esas piezas;
3. calcular margen contra precio de venta;
4. asociar la venta a un cliente, pedido o factura.

### Flujo comercial recomendado

ERClave deberá contemplar un flujo comercial gradual:

1. prospecto o cliente;
2. cotización;
3. pedido;
4. reserva de inventario o solicitud de producción;
5. entrega;
6. factura o documento comercial;
7. cobranza;
8. análisis de margen.

No todos los clientes necesitarán todo el flujo. El sistema deberá permitir configurarlo por módulo, plan o tipo de operación.

### Funcionalidades futuras de ventas

- Catálogo de clientes.
- Contactos por cliente.
- Direcciones fiscales y de entrega.
- Condiciones comerciales.
- Listas de precios.
- Descuentos.
- Impuestos.
- Monedas.
- Cotizaciones.
- Pedidos de venta.
- Entregas parciales.
- Devoluciones.
- Notas de crédito, si aplica.
- Asociación de pedidos con órdenes de producción.
- Asociación de pedidos con inventario disponible.
- Margen estimado y margen real.
- Historial de ventas por cliente, producto o servicio.

### Relación ventas-producción

Una venta o pedido deberá poder:

- surtirse desde inventario existente;
- generar una orden de producción;
- reservar producto terminado;
- apartar materia prima;
- indicar fecha prometida;
- alimentar reportes de demanda;
- ayudar a planear compras o producción futura.

### Estados sugeridos de venta

| Estado | Descripción |
|---|---|
| Borrador | Documento en captura. |
| Cotizado | Oferta enviada al cliente. |
| Aprobado | El cliente aceptó la cotización. |
| En preparación | Se está surtiendo o produciendo. |
| Parcialmente entregado | Se entregó una parte. |
| Entregado | Se completó la entrega. |
| Facturado | Se emitió documento fiscal o comercial. |
| Cancelado | Se canceló la operación. |

---

## 10. Compras y abastecimiento

ERClave deberá contemplar un módulo de compras para conectar necesidades de producción, inventario y gastos con proveedores.

### Objetivo

Permitir que la empresa controle qué necesita comprar, a quién se compra, cuándo debe llegar, cuánto cuesta y cómo afecta inventario, gastos o costos de producción.

### Flujo recomendado

1. requisición o solicitud de compra;
2. autorización;
3. cotización de proveedor, si aplica;
4. orden de compra;
5. recepción de mercancía o servicio;
6. validación contra XML/PDF;
7. registro de cuenta por pagar o gasto;
8. afectación a inventario, centro de costos u orden de producción.

### Funcionalidades futuras de compras

- Catálogo de proveedores.
- Productos o servicios por proveedor.
- Precios por proveedor.
- Tiempos de entrega.
- Órdenes de compra.
- Recepciones parciales.
- Compras directas.
- Compras ligadas a producción.
- Compras ligadas a almacén.
- Compras ligadas a gastos.
- Autorizaciones por monto.
- Comparación entre pedido, recepción y factura.
- Historial de compras por proveedor.

### Reabastecimiento

En fases posteriores, el sistema podrá sugerir compras considerando:

- inventario mínimo;
- punto de reorden;
- demanda de ventas;
- órdenes de producción programadas;
- materia prima comprometida;
- tiempos de entrega del proveedor;
- stock de seguridad.

Este concepto permitirá acercarse gradualmente a una lógica de planeación de materiales sin implementar un MRP complejo desde la primera versión.

---

## 11. Gastos, XML y PDF

Para la parte administrativa, ERClave deberá permitir cargar facturas de gastos mediante:

- XML fiscal;
- PDF de soporte;
- orden de compra relacionada, cuando exista;
- centro de costos;
- proveedor;
- concepto de gasto;
- fecha;
- importe;
- impuestos;
- archivo adjunto.

La lectura del XML deberá permitir extraer información como:

- RFC emisor;
- proveedor;
- folio fiscal;
- fecha;
- subtotal;
- impuestos;
- total;
- conceptos;
- método de pago;
- moneda.

Después, el usuario podrá asignar ese gasto a:

- centro de costos;
- orden de producción;
- almacén;
- proyecto;
- área;
- producto;
- servicio.

### Ejemplos

- Una factura de tela puede cargarse como gasto o compra de materia prima y posteriormente afectar el almacén de materias primas.
- Una factura de mantenimiento puede asignarse a una máquina específica.
- Una factura de electricidad puede asignarse a un centro de costos productivo.

### Clasificación de gastos

Los gastos deberán poder clasificarse para generar reportes útiles.

Ejemplos:

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

### Relación con cuentas por pagar

Aunque la contabilidad completa puede quedar para una fase posterior, ERClave deberá preparar la información para:

- identificar facturas pendientes de pago;
- asociar pagos a proveedores;
- consultar vencimientos;
- separar gastos pagados y no pagados;
- relacionar documentos XML/PDF con órdenes de compra;
- detectar diferencias entre compra, recepción y factura.

---

## 12. Centros de costos

Los centros de costos serán esenciales para que ERClave pueda generar métricas reales.

Ejemplos:

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

Esto permitirá saber cuánto cuesta operar cada área y cómo impacta en el costo final del producto o servicio.

### Dimensiones de análisis

Además del centro de costos, ERClave deberá considerar dimensiones para análisis gerencial.

Ejemplos:

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

Estas dimensiones permitirán construir reportes más parecidos a los de un ERP, pero manteniendo una estructura flexible.

---

## 13. Costos y rentabilidad

ERClave deberá evolucionar hacia una lógica de costos que permita comparar lo planeado contra lo real.

### Tipos de costo

| Tipo de costo | Descripción |
|---|---|
| Costo estimado | Calculado desde la receta antes de producir. |
| Costo real | Calculado con consumos, tiempos y gastos reales. |
| Costo estándar | Costo de referencia definido por la empresa. |
| Costo promedio | Costo calculado con base en movimientos históricos. |
| Costo por orden | Costo acumulado en una orden específica. |
| Costo por centro | Costo acumulado por área o centro de negocio. |

### Componentes del costo

El costo de producción podrá integrar:

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

### Variaciones

El sistema deberá poder mostrar diferencias entre:

- cantidad estimada vs. cantidad consumida;
- tiempo estimado vs. tiempo real;
- costo estimado vs. costo real;
- merma esperada vs. merma real;
- fecha planeada vs. fecha real;
- margen estimado vs. margen real.

---

## 14. Métricas futuras

Una vez que existan recetas, órdenes, almacenes, gastos y ventas, el sistema podrá generar métricas como:

| Métrica | Qué responde |
|---|---|
| Costo estimado de producción | ¿Cuánto debería costar producir? |
| Costo real de producción | ¿Cuánto costó realmente? |
| Variación de costo | ¿Dónde hubo desviaciones? |
| Consumo de materia prima | ¿Qué insumos se usaron más? |
| Merma | ¿Cuánto material se desperdició? |
| Horas hombre | ¿Cuánto trabajo humano se utilizó? |
| Horas máquina | ¿Cuánto tiempo se usó maquinaria? |
| Rentabilidad por producto | ¿Qué producto deja más margen? |
| Rentabilidad por servicio | ¿Qué servicio conviene más? |
| Carga por área | ¿Qué área está saturada? |
| Producción pendiente | ¿Qué órdenes siguen abiertas? |
| Producción terminada | ¿Qué ya se puede vender o entregar? |
| Inventario disponible | ¿Qué existencias pueden usarse o venderse? |
| Inventario comprometido | ¿Qué inventario ya está apartado? |
| Rotación de inventario | ¿Qué tan rápido se mueve el inventario? |
| Compras pendientes | ¿Qué falta por recibir? |
| Pedidos pendientes | ¿Qué falta por entregar a clientes? |
| Gastos por centro de costos | ¿Qué área está gastando más? |
| Margen por cliente | ¿Qué clientes son más rentables? |
| Cumplimiento de entregas | ¿Qué porcentaje se entrega a tiempo? |
| Variación de producción | ¿Qué se desvió contra lo planeado? |

---

## 15. Enfoque modular recomendado

Para evitar que el producto inicial sea demasiado grande, se propone dividir ERClave en fases.

### Fase 1 — Producción base

- Alta de productos o servicios.
- Alta de recetas.
- Versiones básicas de recetas.
- Materias primas.
- Herramientas.
- Maquinaria.
- Mano de obra.
- Unidades de medida.
- Generación de órdenes de producción.
- Cálculo estimado de recursos.
- Asignación por área o responsable.
- Estados de producción.
- Costo estimado básico.

### Fase 2 — Almacenes

- Tipos de almacén.
- Entradas y salidas.
- Materia prima.
- Producto terminado.
- Herramientas.
- Merma o desperdicio.
- Movimientos entre almacenes.
- Kardex.
- Reservas para producción.
- Inventario en proceso.
- Ajustes de inventario.

### Fase 3 — Compras y abastecimiento

- Proveedores.
- Requisiciones.
- Órdenes de compra.
- Recepciones.
- Compras ligadas a inventario.
- Compras ligadas a producción.
- Compras ligadas a gastos.
- Sugerencias simples de reabastecimiento.

### Fase 4 — Costos

- Costo por materia prima.
- Costo por hora máquina.
- Costo por hora hombre.
- Costo estimado vs. real.
- Centros de costos.
- Reportes de costo de producción.
- Variaciones.
- Rentabilidad por producto o servicio.

### Fase 5 — Ventas y clientes

- Ventas.
- Clientes.
- Cotizaciones.
- Pedidos.
- Entregas.
- Devoluciones.
- Listas de precios.
- Relación pedido-producción-inventario.

### Fase 6 — Administración y gastos

- Proveedores.
- Gastos.
- Carga de XML y PDF.
- Órdenes de compra.
- Asociación de gastos a centros de costos.
- Cuentas por pagar básicas.
- Vencimientos.
- Validación documental.

### Fase 7 — Inteligencia operativa

- Dashboards.
- Rentabilidad.
- Productividad.
- Planeación de capacidad.
- Reportes por producto, servicio, área o centro de costos.
- Reportes configurables.
- Indicadores por centro de negocio.
- Análisis de demanda.

---

## 16. Definición corta del primer módulo

> El primer módulo de ERClave estará enfocado en la gestión de producción mediante recetas configurables, permitiendo registrar los recursos necesarios para fabricar productos o ejecutar servicios, generar órdenes de producción con cantidades específicas, calcular recursos estimados y asignar actividades a responsables o áreas operativas.

---

## 17. MVP recomendado

Para una primera versión funcional, el MVP deberá concentrarse en las capacidades mínimas necesarias para registrar recetas y generar órdenes de producción.

### Funcionalidades del MVP

1. Catálogo de productos/servicios.
2. Catálogo de unidades de medida.
3. Catálogo de recursos:
   - materia prima;
   - herramienta;
   - maquinaria;
   - mano de obra.
4. Alta de recetas.
5. Detalle de receta por recurso, cantidad, unidad y tiempo.
6. Generación de orden de producción.
7. Multiplicación automática de recursos por cantidad a producir.
8. Estados de la orden:
   - borrador;
   - programada;
   - en producción;
   - terminada;
   - cancelada.
9. Vista o impresión de orden por área/responsable.
10. Cálculo básico de costo estimado.
11. Estados básicos de receta:
   - borrador;
   - activa;
   - inactiva.
12. Identificación de almacén origen y destino, aunque el inventario completo se implemente después.
13. Registro básico de merma estimada.
14. Base para centros de costos.

---

## 18. Nombre funcional del módulo

Nombre recomendado para el primer módulo:

> **ERClave Producción**

Este nombre permite mantener una estructura clara para futuros módulos:

- ERClave Almacenes.
- ERClave Ventas.
- ERClave Compras.
- ERClave Gastos.
- ERClave Costos.
- ERClave Reportes.

---

## 19. Propuesta de descripción comercial

> ERClave Producción ayuda a pequeñas y medianas empresas a controlar sus procesos productivos mediante recetas configurables, órdenes de producción y cálculo de recursos, permitiendo conocer qué se necesita, cuánto cuesta y quién debe ejecutar cada etapa del proceso.

---

## 20. Propuesta de descripción operativa

> ERClave Producción permite convertir recetas de productos o servicios en órdenes de trabajo ejecutables, calculando automáticamente materias primas, herramientas, maquinaria, mano de obra, tiempos y costos estimados de producción.

---

## 21. Relación funcional entre módulos futuros

ERClave deberá buscar que los módulos no vivan aislados.

La relación esperada será:

```text
Ventas
  -> demanda de producto o servicio
  -> reserva de inventario o solicitud de producción

Producción
  -> consumo de materia prima
  -> uso de maquinaria y mano de obra
  -> generación de producto terminado

Almacenes
  -> entradas, salidas, transferencias, reservas y ajustes

Compras
  -> abastecimiento de insumos, herramientas, servicios y gastos

Gastos
  -> asignación a centros de costos, órdenes, productos o servicios

Costos
  -> comparación de costo estimado vs. real

Contabilidad
  -> asientos por periodo
  -> cuentas contables, anexos y trazabilidad financiera

Reportes
  -> visibilidad operativa, financiera y comercial
```

Esta integración gradual será una de las diferencias clave entre ERClave y una herramienta aislada de producción o inventarios.

### Documentación detallada por módulo

Para mantener este documento como visión general, el detalle funcional de cada módulo se documentará en archivos independientes dentro de la carpeta `modulos/`.

| Módulo | Documento |
|---|---|
| Sinergia modular | `modulos/00_sinergia_modular.md` |
| Producción | `modulos/01_produccion.md` |
| Almacenes e inventarios | `modulos/02_almacenes_inventarios.md` |
| Compras y abastecimiento | `modulos/03_compras_abastecimiento.md` |
| Ventas y clientes | `modulos/04_ventas_clientes.md` |
| Gastos y cuentas por pagar | `modulos/05_gastos_cuentas_por_pagar.md` |
| Costos y centros de costos | `modulos/06_costos_centros_de_costos.md` |
| Reportes e inteligencia operativa | `modulos/07_reportes_inteligencia_operativa.md` |
| Administración y configuración | `modulos/08_administracion_configuracion.md` |
| Contabilidad | `modulos/09_contabilidad.md` |

---

## 22. Referencias funcionales de ERP empresarial

Para enriquecer el diseño funcional, se tomaron como referencia capacidades comunes observadas en suites ERP empresariales:

- SAP S/4HANA organiza procesos alrededor de líneas de negocio como finanzas, manufactura, ventas, compras, cadena de suministro y gestión de activos.
- SAP Business One, orientado a pequeñas y medianas empresas, contempla módulos como ventas, compras, inventario, producción, bancos, socios de negocio y finanzas.
- Oracle Fusion Cloud ERP y NetSuite integran procesos como finanzas, compras, inventario, órdenes, manufactura, almacenes, abastecimiento y reportes.

ERClave deberá aprender de estas capacidades, pero mantener una implementación más simple, modular y progresiva.

---

## 23. Pendientes para alimentar posteriormente

Este documento será alimentado posteriormente con:

- Reglas de negocio.
- Modelo de datos.
- Flujos de usuario.
- Pantallas principales.
- Roles y permisos.
- Catálogos iniciales.
- Estados de procesos.
- Criterios de aceptación.
- Requerimientos no funcionales.
- Roadmap por fases.
- Estrategia comercial.
- Costos estimados de infraestructura.
- Arquitectura técnica.
- Diseño de base de datos.
- Integraciones futuras.

---

## 24. Notas iniciales

- El sistema deberá diseñarse de forma modular desde el inicio.
- El primer enfoque será manufactura, pero no deberá limitarse exclusivamente a fabricación de productos físicos.
- Las recetas deberán poder aplicar tanto para productos como para servicios.
- Los almacenes deberán ser configurables según la operación de cada empresa.
- La lectura de XML y PDF será relevante para la etapa administrativa y de gastos.
- Los centros de costos serán un elemento clave para obtener métricas de producción y rentabilidad.
- La primera versión deberá evitar ser demasiado amplia y concentrarse en producción base.
- Las funcionalidades inspiradas en ERP grandes deberán servir como guía de crecimiento, no como obligación de implementar todo en el MVP.
