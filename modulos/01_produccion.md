# ERClave — Módulo de Producción

## 1. Objetivo

El módulo de Producción será el primer módulo funcional de ERClave. Su objetivo es permitir que una empresa configure recetas de productos o servicios, genere órdenes de producción y controle los recursos necesarios para ejecutar el proceso.

Este módulo deberá responder:

> Qué se va a producir, qué se necesita, cuánto se necesita, quién participa, cuánto tarda, qué cuesta y en qué estado se encuentra.

---

## 2. Alcance inicial

El alcance inicial deberá concentrarse en producción base:

- productos o servicios;
- recetas;
- versiones básicas de receta;
- materias primas;
- herramientas;
- maquinaria;
- mano de obra;
- procesos o etapas;
- órdenes de producción;
- cálculo estimado de recursos;
- asignación por área o responsable;
- costo estimado básico;
- merma estimada;
- estados de orden.

---

## 3. Entidades principales

| Entidad | Descripción |
|---|---|
| Producto/servicio | Elemento que se fabrica, transforma o ejecuta. |
| Receta | Estructura necesaria para producir un producto o ejecutar un servicio. |
| Versión de receta | Variante vigente o histórica de una receta. |
| Recurso | Materia prima, herramienta, maquinaria o mano de obra. |
| Proceso/etapa | Paso operativo dentro de una receta. |
| Orden de producción | Documento operativo que indica qué se debe producir. |
| Entregable por área | Vista o tarea asignada a un responsable o área. |
| Merma | Material desperdiciado o pérdida esperada/real. |
| Centro de costos | Área o unidad donde se acumulan costos. |

---

## 4. Recetas

Una receta deberá permitir registrar:

- producto o servicio asociado;
- versión;
- estado;
- vigencia;
- cantidad base;
- unidad de medida;
- materias primas;
- herramientas;
- maquinaria;
- mano de obra;
- procesos;
- tiempos estimados;
- costos estimados;
- merma esperada;
- rendimiento esperado;
- instrucciones;
- archivos adjuntos;
- responsables o áreas involucradas.

### Estados sugeridos de receta

| Estado | Descripción |
|---|---|
| Borrador | Receta en captura o diseño. |
| Activa | Receta disponible para generar órdenes. |
| Inactiva | Receta no disponible para nuevas órdenes. |
| Reemplazada | Receta sustituida por una nueva versión. |

---

## 5. Órdenes de producción

Una orden de producción deberá generarse a partir de una receta y una cantidad solicitada.

La orden deberá calcular automáticamente:

- cantidad total de insumos;
- tiempo total estimado;
- uso estimado de maquinaria;
- mano de obra estimada;
- costo estimado;
- merma estimada;
- áreas involucradas.

### Datos de una orden

- producto o servicio;
- receta base;
- versión de receta;
- cantidad;
- unidad;
- fecha requerida;
- prioridad;
- responsable general;
- centro de costos;
- almacén origen de insumos;
- almacén destino del producto terminado;
- observaciones;
- estado;
- cliente o pedido asociado, si aplica.

### Estados sugeridos de orden

| Estado | Descripción |
|---|---|
| Borrador | Orden en captura. |
| Programada | Orden aprobada y pendiente de iniciar. |
| En producción | Orden en ejecución. |
| Pausada | Orden detenida temporalmente. |
| Terminada | Producción finalizada. |
| Cancelada | Orden cancelada. |

---

## 6. Entregables por área

La orden deberá poder dividirse en vistas o entregables por área.

### Corte

- cantidad a cortar;
- materiales requeridos;
- medidas;
- fecha límite;
- observaciones;
- responsable.

### Costura o ensamble

- piezas a ensamblar;
- máquinas asignadas;
- tiempo estimado;
- instrucciones;
- responsable.

### Calidad

- cantidad a revisar;
- criterios de aceptación;
- defectos esperados;
- resultado de revisión;
- piezas aprobadas;
- piezas rechazadas.

### Empaque

- cantidad a empacar;
- materiales de empaque;
- etiquetas;
- instrucciones;
- destino.

---

## 7. Reglas de negocio iniciales

- Una orden de producción deberá basarse en una receta activa.
- Si una receta cambia, las órdenes ya generadas deberán conservar la versión usada.
- La cantidad solicitada multiplicará los recursos de la receta.
- Al generar una orden, el sistema deberá validar disponibilidad de materias primas, herramientas y recursos controlables en almacenes.
- Si no hay disponibilidad suficiente, la orden deberá poder quedar como programada con faltantes identificados o generar necesidad de compra.
- La orden deberá poder asociarse a un pedido de venta.
- La orden podrá reservar insumos antes de consumirlos.
- La orden terminada podrá generar entrada a almacén de producto terminado.
- La merma deberá registrarse por orden, insumo, área o proceso.
- Las cancelaciones deberán conservar trazabilidad.
- Si Contabilidad está activa, la orden deberá validar mapeos contables para consumo de insumos, merma, producto en proceso y producto terminado.

---

## 8. Validaciones automáticas con otros módulos

### Al capturar o activar receta

- Validar que materias primas, herramientas, maquinaria y mano de obra existan como recursos configurados.
- Validar unidades de medida compatibles.
- Validar que los insumos inventariables tengan almacén o tipo de almacén permitido.
- Validar que maquinaria y mano de obra tengan centro de costos cuando se usen para costeo.
- Validar que los recursos con impacto contable tengan cuenta o regla de mapeo cuando Contabilidad esté activa.

### Al generar orden de producción

- Consultar inventario disponible en almacenes de materia prima.
- Consultar disponibilidad o asignación de herramientas.
- Identificar faltantes por recurso.
- Reservar insumos si el usuario confirma programación.
- Generar requisición o sugerencia de compra si hay faltantes.
- Calcular costo estimado con datos de receta, inventario, mano de obra y maquinaria.
- Registrar `documento_origen` para futuros movimientos de almacén, costos y contabilidad.

### Al consumir insumos

- Generar salida de inventario.
- Actualizar kardex.
- Alimentar costo real de producción.
- Generar evento para Contabilidad si el tenant tiene el módulo activo.

### Al terminar producción

- Registrar cantidad producida, rechazada y merma.
- Generar entrada a almacén de producto terminado.
- Cerrar o actualizar costo real de la orden.
- Dejar disponible el producto para ventas o inventario.
- Generar asiento contable si aplica.

---

## 9. Integraciones con otros módulos

| Módulo | Relación |
|---|---|
| Almacenes | Reserva y consumo de insumos; entrada de producto terminado. |
| Compras | Solicitud de insumos faltantes. |
| Ventas | Producción bajo pedido o contra demanda. |
| Gastos | Asignación de gastos directos o indirectos. |
| Costos | Costo estimado vs. real. |
| Contabilidad | Asientos por consumo, merma, producto en proceso y producto terminado. |
| Reportes | Productividad, carga, cumplimiento, merma y rentabilidad. |

---

## 10. Métricas

- órdenes programadas;
- órdenes en producción;
- órdenes terminadas;
- producción pendiente;
- tiempo estimado vs. real;
- costo estimado vs. real;
- merma estimada vs. real;
- carga por área;
- horas hombre;
- horas máquina;
- productividad por responsable;
- cumplimiento de fechas.

---

## 11. Pendientes

- Definir modelo de datos detallado.
- Definir pantallas principales.
- Definir permisos por rol.
- Definir criterios de aceptación del MVP.
- Definir reglas para producción parcial.
- Definir reglas para retrabajo y rechazo de calidad.
