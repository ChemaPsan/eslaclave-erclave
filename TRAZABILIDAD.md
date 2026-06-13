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

## Convencion para futuros cambios

Cuando hagamos una edicion nueva, se debe agregar una entrada adicional con el siguiente ID correlativo y dejar claro si el cambio fue funcional, documental, visual o tecnico.
