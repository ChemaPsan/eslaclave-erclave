# Trazabilidad de cambios

Este archivo registra cada ajuste hecho en el repo con nivel de detalle suficiente para auditar qué se cambió, cuándo, por qué, en qué secciones y con qué validacion.

## Regla de uso

Cada cambio relevante debe quedar registrado aqui con:

- fecha y hora local;
- identificador del cambio;
- autor o agente que hizo el ajuste;
- archivos tocados;
- secciones exactas afectadas;
- descripcion precisa del cambio;
- motivo o contexto;
- impacto esperado;
- validacion realizada;
- observaciones o pendientes.

## Formato sugerido por entrada

| Campo | Contenido |
|---|---|
| Fecha | AAAA-MM-DD HH:MM |
| Cambio | ID corto, por ejemplo `CHG-001` |
| Autor | Nombre de la persona o agente |
| Archivos | Lista de archivos modificados |
| Secciones | Titulos, bloques o lineas afectadas |
| Descripcion | Que se cambio exactamente |
| Motivo | Por que se hizo el ajuste |
| Impacto | Efecto esperado en el repo o producto |
| Validacion | Comprobacion realizada despues del cambio |
| Observaciones | Riesgos, notas o pendientes |

## Registro

### CHG-001

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Creacion inicial del archivo de trazabilidad |
| Autor | GitHub Copilot |
| Archivos | `TRAZABILIDAD.md`, `README.md` |
| Secciones | Contenido actual, estructura del proyecto |
| Descripcion | Se agrego este archivo para llevar un historial detallado de cada cambio futuro y se enlazo desde el README para que sea visible desde la portada del proyecto. |
| Motivo | Tener una fuente unica y ordenada para auditar cambios, contexto, alcance y validacion de cada ajuste. |
| Impacto | Facilita seguimiento fino del trabajo y reduce ambiguedad sobre que se toco en cada iteracion. |
| Validacion | Revision manual del contenido y confirmacion de que el README referencia el nuevo archivo. |
| Observaciones | A partir de ahora, cada cambio relevante deberia sumar una nueva fila en este documento. |

### CHG-002

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Separacion de productos/servicios y recetas en Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/data/resources.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Productos y servicios, submodulo Recetas, mock DB local, estilos de catalogo |
| Descripcion | Se agrego un catalogo independiente de productos y servicios con alta y busqueda. El boton Generar receta ahora navega al apartado Recetas con el producto seleccionado como contexto, sin crear recetas desde Productos y servicios. |
| Motivo | Delimitar responsabilidades por submodulo para evitar duplicar funcionalidades y facilitar permisos futuros por rol. |
| Impacto | Productos y servicios queda como catalogo maestro; Recetas conserva la configuracion de recursos, etapas y tiempos. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | La persistencia sigue siendo mock en `localStorage`; queda pendiente prueba visual manual en navegador. |

### CHG-003

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Gestion de estatus e historial en productos y servicios |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Catalogo de Productos y servicios, mock DB local, estilos de tarjetas |
| Descripcion | Se agrego cambio de estatus por producto o servicio con opciones Activo, Inactivo y En espera de aprobacion. Cada tarjeta muestra historial de ordenes relacionadas y se elimino el boton duplicado Dar de alta dentro del apartado. |
| Motivo | Completar la gestion del catalogo maestro sin mezclar alta de recetas y permitir seguimiento operativo por producto o servicio. |
| Impacto | El submodulo ahora permite administrar disponibilidad funcional del producto/servicio y consultar su historial de uso en ordenes. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El historial se calcula contra ordenes mock existentes por nombre de producto o receta asociada. |

### CHG-004

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Selector de catalogo en formulario de recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, construccion y validacion de recetas, historial de productos/servicios |
| Descripcion | El campo Producto o servicio del formulario de receta dejo de ser texto libre y ahora es un selector conectado al catalogo de Productos y servicios. Al cambiar la seleccion se prellenan unidad y centro de costos, y la receta guarda `productServiceId`. |
| Motivo | Asegurar que las recetas solo se creen sobre productos o servicios existentes y mantener separadas las responsabilidades de catalogo y receta. |
| Impacto | Mejora la trazabilidad entre productos/servicios, recetas y ordenes; evita duplicidad o errores por captura manual del nombre. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Las recetas existentes sin `productServiceId` siguen resolviendose por nombre para conservar compatibilidad del mock actual. |

### CHG-005

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Buscador de producto o servicio en recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, selector de producto o servicio |
| Descripcion | El selector de Producto o servicio en recetas se cambio a un campo buscable con `datalist`, permitiendo escribir clave, nombre o tipo para encontrar coincidencias del catalogo de Productos y servicios. |
| Motivo | Facilitar la seleccion cuando existan muchos productos o servicios sin perder la relacion tecnica con el catalogo maestro. |
| Impacto | El usuario puede buscar rapidamente y la receta sigue guardando `productServiceId` solo cuando el producto o servicio coincide con el catalogo. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Si el texto no coincide con una opcion del catalogo, la validacion impide guardar la receta. |

### CHG-006

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Despliegue completo del catalogo buscable en recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, buscador de Producto o servicio, estilos de lookup |
| Descripcion | Se reemplazo el `datalist` nativo por un dropdown propio. Al enfocar el campo vacio muestra todos los productos y servicios; al escribir filtra por clave, nombre, tipo, categoria o centro. |
| Motivo | Permitir seleccion eficiente incluso con cientos de productos y asegurar que el usuario pueda abrir el catalogo completo sin escribir primero. |
| Impacto | El formulario de recetas conserva `productServiceId`, prellena unidad y centro al seleccionar, y mejora la experiencia de busqueda. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El dropdown es local al mock frontend y no requiere dependencias externas. |

### CHG-007

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Scroll interno en buscador de producto o servicio |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, dropdown de Producto o servicio |
| Descripcion | El dropdown del buscador de Producto o servicio ahora flota sobre el formulario, no empuja la pagina hacia abajo y limita la altura visible a aproximadamente cinco registros con scroll interno para el resto. |
| Motivo | Evitar que catalogos grandes deformen el formulario o hagan crecer la pagina al desplegar resultados. |
| Impacto | Mejora la usabilidad del buscador con muchos productos o servicios manteniendo seleccion y filtrado dentro del modal. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El alto visible se controla por CSS con `max-height` y `overflow: auto`. |

### CHG-008

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Separacion de mano de obra y maquinaria fuera de almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/modules.js`, `frontend/data/mockDb.js`, `frontend/data/resources.js`, `frontend/utils/production.js`, `TRAZABILIDAD.md` |
| Secciones | Produccion, Areas y puestos, Maquinaria, catalogo de recursos de recetas |
| Descripcion | Se agregaron subapartados de Areas y puestos y Maquinaria dentro de Produccion. Mano de obra y maquinaria se movieron a catalogos operativos independientes con alta desde modal, mientras Almacenes queda para materias primas, consumibles y herramientas. Las recetas ahora toman recursos desde el catalogo combinado de almacenes, puestos y maquinaria. |
| Motivo | Evitar tratar mano de obra y maquinaria como inventario fisico, y permitir configurar capacidad operativa por area, puesto y equipo. |
| Impacto | Las recetas pueden asignar materias primas, puestos de mano de obra y maquinas desde fuentes separadas; el costeo estimado sigue funcionando con los recursos existentes. |
| Validacion | `node --check frontend/app.js`, `node --check frontend/utils/production.js`, `node --check frontend/data/mockDb.js` y `node --check frontend/data/resources.js` ejecutados sin errores de sintaxis. |
| Observaciones | La disponibilidad de puestos y maquinas se maneja como minutos disponibles por dia dentro del mock local. |

### CHG-009

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Reorden visual de submodulos de Produccion |
| Autor | Codex |
| Archivos | `frontend/data/modules.js`, `TRAZABILIDAD.md` |
| Secciones | Lista de submodulos de Produccion |
| Descripcion | Se movieron Areas y puestos y Maquinaria al final de la lista visual de Produccion, manteniendo intacta la logica funcional. |
| Motivo | Mantener primero el flujo operativo principal y dejar los catalogos de configuracion al final. |
| Impacto | La navegacion queda mas clara: Productos y servicios, Recetas, Ordenes, Entregables, Validacion, Areas y puestos, Maquinaria. |
| Validacion | `node --check frontend/data/modules.js` ejecutado sin errores de sintaxis. |
| Observaciones | Cambio solo visual/de orden, sin modificaciones de comportamiento. |

### CHG-010

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Gestion completa de areas, puestos y cantidad de recursos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/data/resources.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, modal de puesto, catalogo de mano de obra |
| Descripcion | Se agrego resumen por area, edicion de puestos existentes, captura de cantidad de recursos por rol y minutos disponibles por recurso. La capacidad total se calcula como cantidad por minutos por recurso. |
| Motivo | Permitir gestionar varios recursos del mismo puesto y area, por ejemplo 20 costureros en Costura, sin duplicar registros individuales. |
| Impacto | El catalogo de mano de obra ahora representa capacidad real por area/puesto y las recetas validan contra esa capacidad total. |
| Validacion | `node --check frontend/app.js`, `node --check frontend/data/mockDb.js` y `node --check frontend/data/resources.js` ejecutados sin errores de sintaxis. |
| Observaciones | Los roles antiguos sin `quantity` usan fallback visual de 1 recurso para compatibilidad con datos previos en `localStorage`. |

### CHG-011

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Navegacion por areas y detalle de puestos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos |
| Descripcion | La pantalla de Areas y puestos ahora muestra primero un listado de areas con buscador por area, puesto o rol. Al entrar a un area se muestran sus puestos/roles y desde cada rol se abre el formulario de edicion de cantidad, minutos, costo y estatus. |
| Motivo | Facilitar la consulta cuando existan muchas areas y puestos, manteniendo una navegacion jerarquica clara. |
| Impacto | El usuario puede encontrar areas por descripcion o por roles contenidos, entrar al area y editar la capacidad de cada puesto. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El area seleccionada se conserva temporalmente en `localStorage` para mantener el contexto al editar o crear puestos. |

### CHG-012

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Flecha global de retorno entre pantallas |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Topbar, navegacion principal, navegacion interna de modulos |
| Descripcion | Se agrego un boton global de volver en el encabezado y un historial interno de pantallas para retornar a la vista anterior en la navegacion del prototipo. |
| Motivo | Dar una forma consistente de regresar desde cualquier pantalla o subpantalla sin depender solo de botones contextuales. |
| Impacto | La navegacion entre modulos, submodulos, detalle de areas, tarjetas internas y redirecciones despues de guardar ahora queda integrada con una flecha de retorno. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El historial es local al frontend mock y no persiste entre recargas. |

### CHG-013

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Alta contextual de roles desde detalle de area |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, detalle de area, modal de puesto |
| Descripcion | Se agrego un boton en el detalle de cada area para crear un nuevo rol o recurso dentro de esa misma area. El formulario de alta abre con el area precargada y mantiene la edicion existente de roles. |
| Motivo | Permitir agregar puestos o recursos desde el punto donde se consulta el area, sin regresar al listado general ni capturar de nuevo el area manualmente. |
| Impacto | El flujo de Areas y puestos queda mas directo: se entra a un area, se revisan sus roles y desde ahi se agregan nuevos recursos asociados a esa area. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El boton general de Nueva area/puesto se conserva para crear registros desde cero. |

### CHG-014

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Bloqueo de area en alta contextual de rol |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, modal de puesto |
| Descripcion | Cuando se crea un nuevo rol o recurso desde el detalle de un area, el campo Area se muestra precargado y en modo solo lectura. |
| Motivo | Evitar que el usuario cambie el area cuando el alta ya nace dentro de una area especifica. |
| Impacto | El flujo contextual queda mas consistente: desde el detalle de area solo se agregan roles a esa misma area, mientras el alta general conserva el campo editable. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | La edicion de roles existentes mantiene el comportamiento previo. |

### CHG-015

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Estilo global para campos no editables y bloqueo de area al editar rol |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, formularios del sistema |
| Descripcion | Al abrir un rol desde el detalle de un area, el campo Area queda en modo solo lectura tambien durante la edicion. Se agrego un estilo visual global para campos `readonly` y `disabled` dentro de formularios. |
| Motivo | Evitar cambios accidentales de area cuando el usuario ya esta trabajando dentro de un area especifica, y hacer evidente que un campo no se puede modificar. |
| Impacto | Los campos bloqueados ahora se distinguen visualmente por color, borde y patron de fondo. El alta general de Nueva area/puesto conserva el area editable. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | La regla visual aplica a inputs, selects y textareas no editables dentro de `.preview-field`. |

### CHG-016

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Edicion de registros de maquinaria |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Maquinaria, modal de maquina, persistencia mock |
| Descripcion | Se agrego la accion Abrir maquina en cada tarjeta de maquinaria y el modal ahora permite editar area, tipo, nombre, minutos disponibles, costo y estatus de una maquina existente. |
| Motivo | Permitir actualizar horas maquina, costos o datos operativos sin duplicar registros. |
| Impacto | El catalogo de maquinaria puede mantenerse desde la interfaz y conserva el mismo identificador de maquina al editar, evitando romper referencias existentes en recetas. |
| Validacion | `node --check frontend/app.js` y `node --check frontend/data/mockDb.js` ejecutados sin errores de sintaxis. |
| Observaciones | El alta de nueva maquina mantiene el mismo flujo y la edicion reutiliza el formulario existente. |

### CHG-017

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Fortalecimiento gerencial del modulo de Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/resources.js`, `frontend/utils/production.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, Recetas, Validacion, Ordenes, Entregables |
| Descripcion | Se aplicaron cinco mejoras prioritarias: ficha maestra enriquecida de producto/servicio, receta versionada con aprobacion, validacion de liberacion contra receta aprobada y recursos, costo estandar contra costo real, y seguimiento de orden por etapas operativas genericas. |
| Motivo | Convertir Produccion en un flujo mas cercano a gestion ERP: catalogo maestro, receta controlada, liberacion previa, costeo y control de avance sin depender de una industria especifica. |
| Impacto | Las ordenes se liberan solo con receta aprobada y recursos suficientes; los productos muestran costo, margen y receta vigente; las recetas manejan aprobacion; las ordenes muestran avance por etapa y variacion de costo. |
| Validacion | `node --check frontend/app.js`, `node --check frontend/utils/production.js` y `node --check frontend/data/resources.js` ejecutados sin errores de sintaxis. |
| Observaciones | Las etapas se nombran como operativas genericas para mantener el sistema agnostico al producto o industria. |

### CHG-018

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Edicion de productos y servicios existentes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, ficha maestra, recetas relacionadas |
| Descripcion | Se agrego la accion Editar ficha en cada producto/servicio y el modal de catalogo ahora funciona para alta y edicion, precargando tipo, nombre, SKU, unidad, categoria, centro, responsable, precio objetivo, margen, estatus y descripcion. |
| Motivo | Permitir mantener la ficha maestra de productos y servicios sin crear registros duplicados. |
| Impacto | Al editar se conserva el identificador del producto/servicio para no romper recetas u ordenes relacionadas; las recetas vinculadas se sincronizan con nombre, unidad y centro actualizados. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El costo estandar se conserva desde la receta vigente y no se captura manualmente desde la ficha. |

### CHG-019

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Accion contextual de receta vigente y regla de versionamiento para ordenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, Recetas, Ordenes |
| Descripcion | En Productos y servicios, si el producto o servicio ya tiene una receta vigente, la accion ahora muestra Editar receta; si no tiene receta, mantiene Generar receta. |
| Motivo | Evitar duplicidad conceptual: cuando ya existe receta vigente, el flujo correcto es editar/versionar esa receta, no generar otra desde cero. |
| Impacto | El usuario puede ir directo a la receta existente desde la ficha maestra del producto/servicio. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Regla de negocio documentada para implementacion posterior: cuando una receta se actualice o se genere una nueva version, las ordenes en curso deben conservar la receta/version con la que fueron liberadas; los cambios de receta solo aplican para nuevas ordenes. |

### CHG-020

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Catalogo directo de estatus para ordenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Ordenes de produccion |
| Descripcion | Se reemplazo el cambio ciclico de estatus por un selector de catalogo en cada orden. El usuario puede elegir directamente Liberada, En espera de recursos, En produccion, Pausada, En validacion, Terminada o Cancelada. |
| Motivo | Evitar que el usuario tenga que presionar varias veces un boton para llegar al estatus deseado. |
| Impacto | El cambio de estatus de orden es mas rapido y controlado; el avance por etapas operativas se mantiene separado. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El catalogo queda centralizado en frontend para facilitar su futura migracion a configuracion o backend. |

### CHG-021

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Guias visuales de flujo en apartados de Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, Recetas, Areas y puestos, Maquinaria, Ordenes, Entregables, Validacion |
| Descripcion | Se agrego un componente visual de flujo con pasos numerados para que cada apartado con proceso operativo muestre la secuencia que debe seguirse. |
| Motivo | Ayudar a que cualquier usuario entienda que hacer primero, que sigue y como se conectan catalogos, recetas, validacion, ordenes y seguimiento. |
| Impacto | Los apartados ahora muestran cuadros de flujo para catalogo maestro, receta, configuracion de mano de obra, configuracion de maquinaria, estatus de orden, seguimiento por etapa y liberacion. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Las guias usan lenguaje generico de ERP para no depender de una industria especifica. |

### CHG-022

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Guias de flujo laterales y colapsables |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo |
| Descripcion | Las guias visuales de flujo dejaron de mostrarse como bloque horizontal principal y ahora se presentan como panel lateral izquierdo colapsable mediante mostrar/ocultar. |
| Motivo | Evitar que usuarios que ya conocen el flujo vean la guia ocupando el primer renglon de trabajo, manteniendola disponible para consulta. |
| Impacto | Los apartados con flujo operativo conservan la guia, pero el contenido principal queda priorizado a la derecha y la guia puede ocultarse cuando no se necesite. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | En pantallas pequenas el layout vuelve a una sola columna para mantener legibilidad. |

### CHG-023

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Colapso vertical real de guias de flujo |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo colapsables |
| Descripcion | Cuando una guia de flujo se oculta, el layout deja de reservar la columna lateral y la guia se contrae verticalmente como barra compacta superior. |
| Motivo | Evitar que una guia cerrada siga ocupando espacio horizontal util en pantalla. |
| Impacto | El contenido principal recupera el ancho completo al ocultar la guia, mientras la opcion de mostrarla queda disponible. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El cambio se implemento con reglas CSS basadas en el estado cerrado de `details`. |

### CHG-024

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Colapso horizontal de guias de flujo |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo colapsables |
| Descripcion | Las guias de flujo cerradas ahora se contraen horizontalmente como un riel lateral angosto en lugar de convertirse en una barra superior. |
| Motivo | Mantener la guia siempre accesible sin quitar ancho util al contenido principal. |
| Impacto | Al ocultar la guia, el contenido usa casi todo el ancho y la guia queda como tira lateral para volver a abrirla. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El riel lateral usa el estado cerrado de `details` y conserva el comportamiento responsive existente. |

### CHG-025

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Mejora visual del riel colapsado de flujo |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo colapsables |
| Descripcion | El riel cerrado de las guias de flujo ahora se muestra como una pestana lateral con icono, texto corto Abrir flujo y estilo visual integrado al panel. |
| Motivo | Evitar que el titulo largo se vea como texto fuera de contexto cuando la guia esta cerrada. |
| Impacto | La guia cerrada se entiende como una pestaña accionable y ocupa poco espacio sin perder contexto visual. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El titulo completo solo se muestra cuando la guia esta abierta. |

### CHG-026

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Actualizacion documental del modulo de Produccion |
| Autor | Codex |
| Archivos | `modulos/01_produccion.md`, `TRAZABILIDAD.md` |
| Secciones | Documentacion funcional de Produccion |
| Descripcion | Se actualizo el documento del modulo de Produccion para reflejar la maqueta actual: catalogo maestro, recetas aprobables, validacion de liberacion, ordenes, costos, etapas genericas, areas y puestos, maquinaria y reglas de negocio vigentes. |
| Motivo | Mantener alineada la documentacion funcional con lo implementado en la maqueta. |
| Impacto | El documento ahora describe el flujo ERP agnostico y separa claramente catalogos, recetas, recursos, ordenes y seguimiento operativo. |
| Validacion | Revision documental local del archivo `modulos/01_produccion.md`. |
| Observaciones | Se uso texto ASCII para evitar problemas de codificacion en el repositorio. |

### CHG-027

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:14 |
| Cambio | Lista inicial de agentes especializados por modulo |
| Autor | Codex |
| Archivos | `AGENTES.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Nueva matriz de agentes, contenido actual del README, registro de trazabilidad |
| Descripcion | Se agrego una lista de agentes por modulo con dos perfiles por area: agente de negocio y agente tecnico. Cada perfil incluye responsabilidades, preguntas que responde, dependencias y entregables esperados. |
| Motivo | Preparar una estructura de trabajo donde cada modulo tenga especialistas funcionales y tecnicos para revisar cambios, dependencias y pendientes de integracion antes de evolucionar el producto. |
| Impacto | El repo ahora cuenta con una guia clara para consultar agentes por modulo y reducir riesgos al modificar flujos, frontend, datos, API futura o integraciones. |
| Validacion | Revision documental local de `AGENTES.md` y enlace desde `README.md`. |
| Observaciones | Queda pendiente convertir la matriz en prompts o fichas individuales para agentes reales. |

### CHG-028

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:21 |
| Cambio | Entrenamiento conceptual de agentes por modulo |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Base de conocimiento comun, entrenamiento por modulo, fuentes de referencia |
| Descripcion | Se enriquecio la lista de agentes con modelos de referencia y conocimiento especifico por area. Se agregaron criterios de dominio para negocio y tecnica en sinergia modular, produccion, almacenes, compras, ventas, gastos, costos, reportes, administracion y contabilidad. |
| Motivo | Convertir la lista de agentes en una guia de aprendizaje operativo y tecnico basada en mejores practicas documentadas, para que cada agente pueda evaluar cambios con mayor criterio. |
| Impacto | Los agentes ahora tienen una base comun de razonamiento y una ruta de especializacion por modulo, facilitando revisiones futuras de flujos, datos, seguridad, API, reportes e integraciones. |
| Validacion | Revision documental local de `AGENTES.md` y confirmacion de estructura por encabezados. |
| Observaciones | Las fuentes se agregaron como referencias conceptuales; queda pendiente convertir cada perfil en prompt ejecutable o ficha individual. |

### CHG-029

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:28 |
| Cambio | Agente transversal de diseno y experiencia |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Matriz general, base de conocimiento comun, entrenamiento por modulo, agentes transversales |
| Descripcion | Se agrego un agente transversal de Diseno y experiencia con perfil de negocio UX/UI y perfil tecnico de frontend/sistema visual. El agente documenta identidad de marca, paleta, tokens CSS, componentes existentes, responsive, accesibilidad, localizacion y criterios para revisar pantallas de todos los modulos. |
| Motivo | Centralizar el conocimiento visual de ERClave para que cualquier cambio de modulo conserve la identidad de marca, consistencia de componentes y calidad de experiencia operativa. |
| Impacto | Los futuros cambios de interfaz podran revisarse contra un criterio de diseno comun, evitando estilos duplicados, pantallas inconsistentes o rupturas de responsive/tema. |
| Validacion | Revision documental local de `AGENTES.md`, manual de identidad y estilos actuales del frontend. |
| Observaciones | Queda pendiente convertir este agente en checklist ejecutable para revisiones visuales antes de publicar. |

### CHG-030

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Arquitectura objetivo de microservicios y microfrontends |
| Autor | Codex |
| Archivos | `docs/arquitectura/microservicios_microfrontends.md`, `frontend/shell/README.md`, `frontend/microfrontends/README.md`, `frontend/microfrontends/*/manifest.js`, `frontend/microfrontends/registry.js`, `backend/services/README.md`, `backend/services/*/README.md`, `contracts/README.md`, `contracts/api/README.md`, `contracts/events.md`, `contracts/microfrontend.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, frontend shell, microfrontends, microservicios, contratos, eventos, README |
| Descripcion | Se documento la separacion objetivo del sistema en shell frontend, microfrontends por modulo, microservicios por dominio, contratos API/eventos/UI y estrategia progresiva de migracion desde el prototipo actual. Tambien se agregaron manifests iniciales de microfrontends y carpetas base por microservicio. |
| Motivo | Evitar que cambios pequenos en un boton, submodulo o regla afecten todo el sistema, estableciendo ownership, contratos y fronteras claras por modulo. |
| Impacto | El repo ahora tiene una ruta arquitectonica para aislar cambios visuales, funcionales y tecnicos por modulo antes de iniciar la extraccion de codigo desde `frontend/app.js`. |
| Validacion | Revision documental local y confirmacion de que la arquitectura identifica a Produccion como primer candidato de migracion. |
| Observaciones | Queda pendiente ejecutar la fase 2: convertir `frontend/app.js` en shell y mover Produccion a `frontend/microfrontends/produccion/`. |

### CHG-031

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:36 |
| Cambio | Regla de segmentacion obligatoria para agentes |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Base de conocimiento comun, regla obligatoria de segmentacion, entrenamiento de Sinergia y Diseno, checklist antes de actualizar un modulo, fuentes de referencia |
| Descripcion | Se actualizo la guia de agentes para que todos consideren la arquitectura de microservicios y microfrontends antes de validar o ejecutar cambios. Se agregaron preguntas obligatorias sobre modulo dueno, microfrontend, microservicio, contratos, eventos, shell, shared, blast radius y trazabilidad. |
| Motivo | Asegurar que los agentes entiendan la importancia de mantener el sistema segmentado y eviten aprobar cambios que mezclen responsabilidades o afecten otros modulos por acoplamiento. |
| Impacto | Las futuras validaciones de agentes deberan revisar ownership, fronteras, contratos y riesgo de impacto antes de modificar botones, formularios, estados, APIs o eventos. |
| Validacion | Revision documental local de `AGENTES.md` y verificacion de referencias a microfrontends, microservicios, contratos y checklist de segmentacion. |
| Observaciones | Queda pendiente convertir esta regla en checklist automatizable para revisiones de PR o cambios locales. |

### CHG-032

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:41 |
| Cambio | Agente de localizacion Espanol/Ingles |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Matriz general, base de conocimiento comun, entrenamiento de Diseno, agente transversal de Diseno, checklist antes de actualizar un modulo, fuentes de referencia |
| Descripcion | Se amplio el agente transversal de Diseno y experiencia para incluir localizacion bilingue Espanol/Ingles. Se agregaron responsabilidades de lenguaje bilingue, paridad de claves i18n, variables dinamicas, glosario funcional y deteccion de textos hardcodeados. |
| Motivo | Asegurar que todo el sistema pueda traducirse correctamente entre Espanol e Ingles sin romper tono, contexto operativo, botones, tabs, modales, tablas o componentes responsivos. |
| Impacto | Cada cambio de UI debera revisar textos visibles, claves en `frontend/i18n/translations.js`, paridad entre `es` y `en`, variables dinamicas y longitud de traducciones antes de aprobarse. |
| Validacion | Revision documental local de `AGENTES.md` y confirmacion de que `frontend/i18n/translations.js` contiene estructura bilingue `es` y `en`. |
| Observaciones | Queda pendiente automatizar una validacion que compare claves y placeholders entre ambos idiomas. |

### CHG-033

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Validadores automaticos iniciales |
| Autor | Codex |
| Archivos | `package.json`, `tools/validators/shared.js`, `tools/validators/validate-i18n.js`, `tools/validators/validate-architecture.js`, `tools/validators/validate-traceability.js`, `tools/validators/validate-syntax.js`, `tools/validators/validate-all.js`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Scripts npm, validadores, validaciones automaticas en README, registro de trazabilidad |
| Descripcion | Se agrego una primera suite de validadores automaticos sin dependencias externas. Incluye validacion i18n Espanol/Ingles, arquitectura de microfrontends/microservicios, trazabilidad secuencial y sintaxis JavaScript. |
| Motivo | Convertir reglas de `AGENTES.md` en checks ejecutables para detectar problemas antes de aprobar cambios. |
| Impacto | El repo ahora puede ejecutar `npm run validate` y validar reglas basicas de agentes, segmentacion, localizacion, trazabilidad y sintaxis. |
| Validacion | `npm run validate`, `npm run validate:i18n`, `npm run validate:architecture` y `npm run validate:syntax` ejecutados correctamente. |
| Observaciones | Los validadores son una primera capa; despues pueden conectarse a GitHub Actions o ampliarse para revisar diffs por modulo. |

### CHG-034

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Workflow de GitHub Actions para validadores |
| Autor | Codex |
| Archivos | `.github/workflows/validate.yml`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | GitHub Actions, validaciones automaticas, README, trazabilidad |
| Descripcion | Se agrego un workflow independiente de GitHub Actions que ejecuta `npm run validate` en pushes a `main`, pull requests a `main` y ejecucion manual. |
| Motivo | Automatizar las validaciones de agentes, segmentacion, i18n, trazabilidad y sintaxis cada vez que se suban cambios relevantes al repo. |
| Impacto | GitHub podra marcar en verde o rojo los cambios segun pasen los validadores automaticos, reduciendo el riesgo de subir cambios que rompan reglas del repo. |
| Validacion | Revision local del YAML y `npm run validate` ejecutado correctamente antes de agregar el workflow. |
| Observaciones | El workflow usa Node 20 y no requiere instalacion de dependencias porque los validadores no usan paquetes externos. |

### CHG-035

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 11:48 |
| Cambio | MVP de formularios genericos para modulos no Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Render generico de modulos, formularios genericos, persistencia local por modulo/submodulo, traducciones Espanol/Ingles |
| Descripcion | Se agrego una captura funcional generica para los modulos distintos de Produccion. El boton principal del modulo, el boton superior y las pantallas de submodulo abren un formulario reutilizable, guardan registros en `localStorage` por modulo/submodulo y muestran los registros guardados en tablas y listas. |
| Motivo | Avanzar hacia un MVP funcional del resto de modulos usando Produccion como referencia, sin duplicar logica compleja ni agregar alcance excesivo para el nivel actual del sistema. |
| Impacto | Almacenes, Compras, Ventas, Gastos, Costos, Reportes y Contabilidad ya pueden capturar registros basicos y verlos reflejados en la interfaz, manteniendo idioma Espanol/Ingles y estilo visual existente. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Produccion no recibio ajustes funcionales; se mantiene como referencia. La captura generica es intencionalmente simple y queda lista para especializarse modulo por modulo en fases posteriores. |

### CHG-036

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 11:56 |
| Cambio | Alta especializada de almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Almacenes, modal de alta de almacen, tabla de registros, traducciones Espanol/Ingles |
| Descripcion | Se especializo la primera seccion del modulo Almacenes para dar de alta fichas de almacen con codigo, nombre, tipo, estatus, centro de negocio, ubicacion fisica, responsable, capacidad, politica de inventario, permiso de reservas y descripcion. Los registros se guardan en `localStorage` y se muestran en la tabla/lista del submodulo. |
| Motivo | Iniciar el flujo funcional de Almacenes con una ficha maestro de almacen alineada a la documentacion del modulo y a practicas basicas de control de inventario. |
| Impacto | El submodulo Almacenes deja de usar captura generica y ya cuenta con una ficha funcional inicial, manteniendo el diseno de marca, soporte Espanol/Ingles y sin tocar el flujo de Produccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Los submodulos Ubicaciones, Movimientos, Reservas y Kardex conservan por ahora el MVP generico para especializarse en pasos posteriores. |

### CHG-037

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:03 |
| Cambio | Catalogo consultable y flujo colapsable en Almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Modulo Almacenes, submodulo Almacenes, guias de flujo colapsables, catalogo de almacenes |
| Descripcion | Se aplico la logica de guia de flujo colapsable al modulo Almacenes. La primera seccion del modulo ahora muestra un catalogo consultable de almacenes dados de alta, con tarjetas que presentan codigo, tipo, centro, ubicacion, responsable, capacidad, politica, reservas y estatus. |
| Motivo | Alinear Almacenes con el patron visual de Produccion y establecer que la primera seccion funcional de cada modulo permita alta y consulta de registros existentes. |
| Impacto | El usuario puede dar de alta almacenes y consultarlos visualmente desde la misma seccion, mientras los demas submodulos de Almacenes ya muestran guia de flujo colapsable para orientar su operacion futura. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Ubicaciones, Movimientos, Reservas y Kardex siguen usando captura generica; quedan listos para especializacion posterior. |

### CHG-038

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:10 |
| Cambio | Ubicaciones fisicas integradas en ficha de almacen |
| Autor | Codex |
| Archivos | `frontend/data/modules.js`, `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Modulo Almacenes, submodulos, modal de alta de almacen, documentacion funcional |
| Descripcion | Se elimino Ubicaciones como submodulo independiente de Almacenes y se integro como configuracion opcional dentro de la ficha de almacen. El alta de almacen ahora permite capturar zona, pasillo, rack, nivel y posicion como ubicacion fisica inicial opcional. |
| Motivo | Simplificar el MVP y evitar una seccion separada para una configuracion que puede vivir dentro del alta del almacen hasta que el producto requiera un catalogo avanzado de ubicaciones. |
| Impacto | El flujo queda mas simple: primero se crea el almacen y, si aplica, se configura su espacio fisico interno. Movimientos, Reservas y Kardex permanecen como submodulos separados. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Si en una fase posterior se requiere administrar muchas posiciones por almacen, se podra separar Ubicaciones fisicas como catalogo propio. |

### CHG-039

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:15 |
| Cambio | Busqueda y edicion de almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Catalogo de almacenes, modal de almacen, mock DB generico, traducciones Espanol/Ingles |
| Descripcion | Se agrego buscador al catalogo de almacenes para filtrar por codigo, nombre, tipo, ubicacion, responsable, capacidad, espacio fisico y descripcion. Cada tarjeta de almacen ahora incluye accion Editar y el modal de almacen puede precargar datos existentes para actualizar la ficha. |
| Motivo | Permitir consultar rapidamente almacenes cuando el catalogo crezca y mantener fichas existentes sin duplicar registros. |
| Impacto | El submodulo Almacenes permite alta, consulta, busqueda y edicion de almacenes con persistencia local, manteniendo soporte ES/EN y sin afectar Produccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | La edicion conserva `createdAt` y agrega `updatedAt`; queda pendiente auditoria visual o historial de cambios por registro en fases futuras. |

### CHG-040

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:18 |
| Cambio | Registro manual de movimientos de inventario |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Movimientos, modal de movimiento, tabla de movimientos, documentacion funcional |
| Descripcion | Se especializo el submodulo Movimientos para registrar entradas, salidas, transferencias, ajustes positivos y ajustes negativos manuales. El formulario captura documento origen, articulo, cantidad, unidad, almacen, ubicacion fisica opcional, fecha y motivo. |
| Motivo | Permitir operacion manual elemental de inventario mientras las integraciones automaticas con Produccion, Compras y Ventas se implementan en fases posteriores. |
| Impacto | El usuario puede registrar movimientos manuales y consultarlos en tabla/lista dentro de Almacenes, conservando trazabilidad basica y soporte Espanol/Ingles. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Esta version aun no recalcula existencias; el siguiente paso natural es conectar movimientos con disponibilidad, reservas y kardex. |

### CHG-041

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:23 |
| Cambio | Documentacion de catalogos base de Administracion |
| Autor | Codex |
| Archivos | `docs/catalogos_base.md`, `modulos/08_administracion_configuracion.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Catalogos base, Administracion y Configuracion, backlog de configuracion |
| Descripcion | Se agrego un documento dedicado para concentrar los catalogos base que deberan configurarse a nivel Administracion, incluyendo principios, modelo minimo, catalogos transversales, catalogos por modulo, opciones fijas actuales que deberan migrarse y permisos sugeridos. |
| Motivo | Evitar perder contexto sobre los valores configurables que el MVP puede manejar temporalmente como opciones fijas, pero que deberan centralizarse cuando el sistema crezca. |
| Impacto | El equipo cuenta con un mapa claro para implementar despues la pantalla de Catalogos base y migrar configuraciones compartidas sin duplicarlas en cada modulo. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El cambio es documental; no modifica funcionalidad del frontend ni comportamiento de los modulos existentes. |

### CHG-042

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:29 |
| Cambio | Catalogo de articulos en Almacenes |
| Autor | Codex |
| Archivos | `frontend/data/modules.js`, `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Articulos, Almacenes > Movimientos, documentacion funcional |
| Descripcion | Se agrego el submodulo Articulos dentro de Almacenes con alta, consulta, busqueda y edicion de articulos inventariables. El formulario captura codigo, nombre, tipo, categoria, unidad, minimos, maximos, politica de inventario, almacen sugerido, estatus y descripcion. Movimientos ahora usa selector de articulos cuando ya existen articulos registrados, conservando captura manual solo como apoyo temporal. |
| Motivo | Reducir errores de captura en movimientos y preparar el flujo para que, cuando existan usuarios y permisos, solo perfiles autorizados puedan crear o editar articulos. |
| Impacto | Almacenes queda con un catalogo maestro inicial de articulos conectado al registro manual de movimientos, sin recalcular existencias todavia y sin afectar Produccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El catalogo de articulos usa persistencia local del mock DB; en fases posteriores debera conectarse con permisos, lotes/series, existencias y kardex. |

### CHG-043

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:33 |
| Cambio | Busqueda rapida de articulos en movimientos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Movimientos, seleccion de articulos, documentacion funcional |
| Descripcion | Se reemplazo la lista desplegable de articulos en el formulario de movimientos por un campo de busqueda con resultados filtrables por codigo, nombre, tipo, categoria, unidad o almacen sugerido. Al seleccionar un articulo, se guarda su identificador real y se autocompleta la unidad de movimiento. |
| Motivo | Evitar scroll pesado y errores de captura cuando el catalogo tenga cientos de articulos, replicando el patron de seleccion usado en Produccion para asociar productos/servicios a recetas. |
| Impacto | Los operadores pueden encontrar articulos rapidamente y los movimientos quedan ligados a registros autorizados del catalogo cuando este exista. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | La captura manual se conserva solo cuando todavia no hay articulos registrados en el MVP. |

### CHG-044

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:36 |
| Cambio | Reservas deshabilitado para MVP |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Reservas, documentacion funcional |
| Descripcion | Se dejo el submodulo Reservas como pantalla informativa de proximamente. La accion principal queda deshabilitada y no abre formularios ni permite crear registros durante el MVP. |
| Motivo | Evitar apartados de inventario incompletos mientras no existe recalculo real de existencias, consumo de reservas ni conexion con kardex. |
| Impacto | El usuario entiende que Reservas forma parte del alcance futuro, pero no puede operar reservas en esta version. Almacenes, Articulos y Movimientos permanecen funcionales. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Reservas debera activarse en una fase posterior cuando existan existencias calculadas, permisos y consumo/liberacion contra movimientos reales. |

### CHG-045

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:40 |
| Cambio | Kardex como consulta funcional |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Kardex, filtros de consulta, documentacion funcional |
| Descripcion | Se habilito Kardex como pantalla de consulta derivada de Movimientos. La vista permite filtrar por articulo y almacen, buscar por documento, articulo, almacen, tipo de movimiento o motivo, y muestra fecha, documento, movimiento, articulo, almacen, entradas, salidas y saldo calculado por articulo/unidad. |
| Motivo | Kardex debe funcionar como historial auditable, no como formulario. La captura operativa debe ocurrir en Movimientos y Kardex debe reflejarla. |
| Impacto | El usuario puede consultar el historial de inventario sin crear registros desde Kardex. El boton de accion queda como solo consulta y el boton global muestra aviso si se intenta crear desde esa seccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El saldo se calcula a partir de movimientos locales del MVP; transferencias se registran como movimiento auditable sin impacto neto en saldo hasta modelar origen/destino completo. |

### CHG-046

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:47 |
| Cambio | Alta y administracion de clientes en Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Clientes, perfil comercial, perfil de facturacion |
| Descripcion | Se especializo el submodulo Clientes para crear, consultar, buscar y editar clientes. La ficha separa perfil comercial y perfil de facturacion, permitiendo manejar nombre comercial distinto de razon social o nombre fiscal, RFC/ID fiscal, regimen, uso CFDI, email de facturacion y direccion fiscal. |
| Motivo | Iniciar el modulo de Ventas con un maestro de clientes suficientemente controlado para cotizaciones, pedidos y futura facturacion. |
| Impacto | Ventas > Clientes deja de usar captura generica y cuenta con un flujo funcional de alta, consulta, busqueda y edicion de clientes con soporte Espanol/Ingles. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | La informacion fiscal se captura en el MVP, pero aun no emite facturas ni valida RFC contra un servicio fiscal externo. |

### CHG-047

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:53 |
| Cambio | Cotizaciones ligadas a clientes y productos existentes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Cotizaciones, busqueda de clientes, busqueda de productos/servicios |
| Descripcion | Se especializo el submodulo Cotizaciones para crear, consultar, buscar y editar cotizaciones. El formulario exige seleccionar un cliente dado de alta y un producto o servicio existente del catalogo de Produccion mediante busquedas tipo lookup. Tambien captura cantidad, unidad, precio unitario, descuento, vigencia, promesa de entrega, condiciones, moneda y notas. |
| Motivo | Evitar cotizaciones desconectadas de los maestros comerciales y operativos, asegurando que solo se coticen clientes y productos/servicios previamente registrados. |
| Impacto | Ventas > Cotizaciones deja de usar captura generica y ya valida dependencias con Clientes y Produccion. Si no hay clientes registrados, no permite crear cotizacion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El MVP maneja una partida por cotizacion; multiples partidas quedan documentadas como fase posterior. |

### CHG-048

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:55 |
| Cambio | Guias de flujo colapsables para Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Clientes, Cotizaciones, Pedidos, Entregas y Margen |
| Descripcion | Se agregaron guias de flujo colapsables al modulo de Ventas. Clientes y Cotizaciones muestran su flujo dentro de sus pantallas especializadas, y las secciones restantes de Ventas usan la guia de flujo en la vista generica. |
| Motivo | Mantener consistencia visual y funcional con Produccion y Almacenes, dejando claro el orden operativo esperado por submodulo. |
| Impacto | El usuario puede consultar el flujo recomendado de cada seccion de Ventas sin abrir formularios ni perder espacio de trabajo. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El cambio es visual/documental dentro del frontend; no modifica persistencia ni reglas de negocio. |

### CHG-049

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 13:01 |
| Cambio | Cotizaciones multipartida y PDF generico |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Cotizaciones, partidas, PDF generico |
| Descripcion | Se actualizo el formulario de cotizaciones para permitir multiples partidas, cada una ligada a un producto o servicio dado de alta. El sistema calcula subtotal y total sumando partidas, conserva compatibilidad con cotizaciones anteriores de una sola partida y agrega accion PDF para abrir una vista imprimible/guardable como PDF desde el navegador. |
| Motivo | Permitir cotizaciones comerciales mas realistas sin romper la restriccion de usar catalogos maestros para clientes y productos/servicios. |
| Impacto | Las cotizaciones pueden incluir varias partidas, consultarse, editarse y generarse como documento PDF generico. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El PDF es generico y usa la funcion de imprimir/guardar como PDF del navegador; plantillas por tenant quedan para una fase posterior. |

### CHG-050

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 13:44 |
| Cambio | Resumen de estado MVP en documentacion de modulos |
| Autor | Codex |
| Archivos | `modulos/README.md`, `TRAZABILIDAD.md` |
| Secciones | Documentacion por modulos, estado MVP funcional |
| Descripcion | Se agrego un resumen del estado funcional actual por modulo para identificar rapidamente que ya esta implementado en Produccion, Almacenes, Ventas y Administracion, y que modulos conservan MVP generico. |
| Motivo | Mantener contexto documental antes de subir cambios al repositorio y facilitar continuidad de trabajo por modulo. |
| Impacto | La carpeta `modulos/` queda con una vista rapida del avance funcional y de las areas pendientes de especializacion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | No modifica comportamiento del frontend. |

## Convencion para futuros cambios

Cuando hagamos una edicion nueva, se debe agregar una entrada adicional con el siguiente ID correlativo y dejar claro si el cambio fue funcional, documental, visual o tecnico.
