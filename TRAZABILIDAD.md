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

### CHG-051

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:25 |
| Cambio | Cierre MVP Produccion, Almacenes y Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/modules.js`, `frontend/i18n/translations.js`, `modulos/README.md`, `modulos/01_produccion.md`, `modulos/02_almacenes_inventarios.md`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion > Ordenes, Almacenes > Existencias y Movimientos, Ventas > Cotizaciones y Pedidos, documentacion de estado MVP |
| Descripcion | Se agrego snapshot de receta/version al generar ordenes de produccion y se bloqueo eliminar recetas con ordenes relacionadas. En Almacenes se agrego el submodulo Existencias como consulta calculada desde Movimientos, con busqueda, filtro por almacen y bloqueo de salidas o ajustes negativos que excedan saldo. En Ventas se especializo Pedidos para crear pedidos desde cotizaciones aprobadas, evitando duplicados y calculando costo/margen estimado desde las partidas. |
| Motivo | Cerrar huecos MVP detectados en los tres modulos ya trabajados sin activar todavia reservas, entregas ni microservicios reales. |
| Impacto | Produccion conserva historia de ordenes aunque cambien recetas; Almacenes gana disponibilidad calculada basica; Ventas pasa de preventa a pedido comercial inicial conectado con cotizaciones. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Entregas, reservas reales, transferencias origen/destino y consumo real de recursos quedan para fases posteriores por requerir contratos con inventario, produccion y ventas. |

### CHG-052

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:40 |
| Cambio | Entregas MVP en Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/README.md`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Entregas, busqueda de pedidos, registro de entrega, estatus de entrega, documentacion MVP |
| Descripcion | Se especializo el submodulo Entregas para buscar pedidos, ver estatus del pedido y registrar entregas con estatus Pendiente de entrega, En ruta, Entrega parcial, Entregado, No entregado, Reprogramado o Cancelado. El formulario guarda fecha, receptor, referencia, nueva fecha cuando aplica y notas; las entregas parciales o no entregadas exigen notas, y las reprogramadas exigen nueva fecha. |
| Motivo | Completar el flujo comercial MVP despues de cotizacion y pedido, permitiendo seguimiento operativo de entrega sin activar todavia inventario/reservas reales. |
| Impacto | Ventas ahora permite dar seguimiento a pedidos desde Entregas, actualizar el estatus comercial del pedido y conservar historial de intentos o entregas registradas. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | La entrega no descuenta inventario ni libera reservas; ese impacto queda para la fase de integracion con Almacenes. Los estatus se simplificaron tomando como referencia patrones de fulfillment/logistica usados por sistemas como Shopify y ERPs operativos. |

### CHG-053

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:52 |
| Cambio | Edicion de pedidos con bitacora de ajustes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/README.md`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Pedidos, edicion de pedido, historial de ajustes, documentacion MVP |
| Descripcion | Se agrego accion Editar en tarjetas de pedido. El formulario permite ajustar codigo, estatus, promesa de entrega, modo de surtido, responsable y notas, exigiendo motivo de ajuste. Cada guardado registra una bitacora dentro del pedido con fecha, usuario, motivo y cambios campo por campo con valor anterior y nuevo. |
| Motivo | Permitir correcciones operativas controladas en pedidos sin perder trazabilidad comercial ni modificar partidas/importes heredados de la cotizacion origen. |
| Impacto | Los pedidos pueden mantenerse actualizados durante el MVP y cada ajuste queda visible desde la tarjeta y el historial de edicion. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Cliente, partidas, subtotal y total permanecen controlados por la cotizacion origen; cambios comerciales de alcance o precio deberan resolverse en fases posteriores con versionamiento formal de pedido/cotizacion. |

### CHG-054

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:59 |
| Cambio | Entregas como vista de gestion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Entregas, filtros de estatus, consulta de entregas, documentacion MVP |
| Descripcion | Se ajusto el submodulo Entregas para funcionar unicamente como vista de gestion y consulta. Ahora lista entregas registradas, permite buscar por pedido, cliente, cotizacion, estatus, receptor, referencia o notas, y agrega filtro por estatus. Se removio la accion de alta desde esta seccion y la accion global muestra aviso de vista de gestion. |
| Motivo | Mantener Entregas como tablero operativo de seguimiento, evitando mezclar captura o cambios de flujo dentro de una vista que debe servir para controlar estatus y revisar historial. |
| Impacto | El usuario puede ver todas las entregas y sus estatus sin abrir formularios desde Entregas; el registro operativo queda reservado al flujo del pedido o a futuras integraciones. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | La funcion de registro de entrega permanece disponible en codigo para integrarse despues desde flujos operativos, pero el apartado Entregas ya no la expone como accion principal. |

### CHG-055

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:06 |
| Cambio | Consulta de cotizacion desde entregas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Entregas, tarjetas de entrega, consulta de cotizacion relacionada |
| Descripcion | Se agrego accion Ver cotizacion en cada tarjeta de entrega y se habilito click sobre la tarjeta para abrir la vista imprimible de la cotizacion relacionada. La relacion se resuelve por el pedido ligado a la entrega o, como compatibilidad, por codigo de cotizacion guardado en la entrega. |
| Motivo | Permitir que la gestion de entregas consulte rapidamente el documento comercial origen sin convertir Entregas en una pantalla de captura. |
| Impacto | El usuario puede revisar la cotizacion asociada desde el tablero de Entregas, conservando el apartado como vista de gestion/consulta. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Si una entrega no tiene pedido/cotizacion resoluble, se muestra aviso de cotizacion no encontrada. |

### CHG-056

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:09 |
| Cambio | Modulos fuera del MVP como Proximamente |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `modulos/README.md`, `TRAZABILIDAD.md` |
| Secciones | Navegacion lateral, modulos activos MVP, estado visual de modulos pendientes |
| Descripcion | Se limitaron como activos los modulos Produccion, Almacenes y Ventas. Los demas modulos quedan sombreados en la navegacion, no despliegan submodulos ni navegan al hacer click, y al pasar el cursor muestran Proximamente. |
| Motivo | Concentrar el trabajo en los modulos ya avanzados para cerrar un MVP funcional y escalable sin distraer con apartados genericos pendientes. |
| Impacto | La experiencia del prototipo comunica con claridad el alcance actual del MVP y evita que usuarios entren a modulos no trabajados. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | La documentacion y estructura tecnica de los modulos pendientes se conserva para retomarlos en fases posteriores. |

### CHG-057

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:11 |
| Cambio | Orden de navegacion MVP |
| Autor | Codex |
| Archivos | `frontend/app.js`, `modulos/README.md`, `TRAZABILIDAD.md` |
| Secciones | Navegacion lateral, orden visual de modulos activos MVP |
| Descripcion | Se ordeno la navegacion para mostrar primero Produccion, Almacenes y Ventas, dejando Compras y el resto de modulos despues como Proximamente. El arreglo base de modulos se conserva y el orden se resuelve al renderizar el sidebar. |
| Motivo | Agrupar al inicio los modulos habilitados y enfocar el prototipo en las areas ya trabajadas para el MVP. |
| Impacto | Ventas aparece antes de Compras en la navegacion, junto con Produccion y Almacenes como modulos activos. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Cambio visual de navegacion; no modifica datos, contratos ni comportamiento interno de modulos. |

### CHG-058

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:17 |
| Cambio | Paridad de localizacion para modulos MVP activos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/modules.js`, `tools/validators/validate-active-module-localization.js`, `tools/validators/validate-all.js`, `package.json`, `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion, Almacenes, Ventas, panel principal de modulo, validadores, agente de diseno/localizacion |
| Descripcion | Se agregaron campos visibles en Ingles para los metadatos principales de Produccion, Almacenes y Ventas, incluyendo resumen, accion primaria, estatus, KPIs, flujo, tabla, validaciones, captura rapida y registros. El render principal ahora consume los campos localizados cuando el idioma activo es Ingles. |
| Motivo | Evitar que etiquetas y textos visibles de los tres modulos activos queden unicamente en Espanol y se ignoren en futuras revisiones del MVP. |
| Impacto | El panel principal de los modulos MVP cambia correctamente entre Espanol e Ingles en sus metadatos visibles, y el pipeline bloquea faltantes de paridad en esos campos. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Los datos operativos creados por usuario o cargados desde simulaciones se mantienen como datos de negocio; la nueva validacion se enfoca en copy visible controlado por `frontend/data/modules.js`. |

### CHG-059

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Compatibilidad Windows en validador de arquitectura |
| Autor | Codex |
| Archivos | `tools/validators/validate-architecture.js`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Validadores, arquitectura de microfrontends |
| Descripcion | Se normalizo la ruta de `registry.js` dentro del validador de arquitectura para que se excluya correctamente tambien en Windows, donde las rutas llegan con separadores `\\`. Tambien se aclaro en README como ejecutar validaciones desde la raiz del repo y que usar en PowerShell. |
| Motivo | Permitir ejecutar `npm.cmd run validate` localmente en PowerShell sin falsos positivos de imports cruzados del propio registro de microfrontends. |
| Impacto | La validacion de arquitectura sigue bloqueando imports cruzados entre microfrontends, pero ya no falla por el archivo `frontend/microfrontends/registry.js` en Windows. |
| Validacion | `npm.cmd run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | En Linux/macOS se conserva `npm run validate`; en PowerShell se recomienda `npm.cmd run validate` si `npm.ps1` esta bloqueado. |

### CHG-060

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Agente transversal de arquitectura SaaS |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes, arquitectura, multi-tenant, QA/Prod |
| Descripcion | Se agrego el Arquitecto senior de plataforma SaaS como agente transversal prioritario, separado de la matriz por modulo, para gobernar decisiones de arquitectura, ambientes, tecnologia, multi-tenancy, seguridad, contratos, CI/CD y migracion desde maqueta a plataforma real. |
| Motivo | Facilitar su consulta frecuente durante la etapa de llevar los modulos MVP a ambientes reales de QA y Produccion. |
| Impacto | Las decisiones tecnicas transversales ahora tienen un agente de referencia visible antes de la matriz modular, con responsabilidades, criterios de rechazo y entregables esperados. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El agente no reemplaza a los agentes tecnicos por modulo; los gobierna cuando una decision afecta plataforma, ambientes, contratos o escalabilidad. |

### CHG-061

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Documentacion y diagrama QA/Prod |
| Autor | Codex |
| Archivos | `docs/arquitectura/qa_prod.md`, `docs/arquitectura/diagramas/arquitectura_qa_prod.drawio`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, QA, Produccion, multi-tenant, CI/CD |
| Descripcion | Se agrego el documento inicial de arquitectura QA/Prod con diagramas Mermaid, principios, ambientes, stack recomendado, estrategia multi-tenant, CI/CD, modulos MVP, contratos, criterios minimos y riesgos. Tambien se agrego un diagrama editable `.drawio` para diagrams.net. |
| Motivo | Dar al arquitecto SaaS una base visual y documental para planear la salida de la maqueta hacia ambientes reales de QA y Produccion. |
| Impacto | El repo ahora contiene documentacion viva en Markdown y un diagrama editable para comunicar la arquitectura inicial de despliegue y operacion. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los diagramas Mermaid viven en Markdown y el archivo `.drawio` puede abrirse desde https://app.diagrams.net/. |

### CHG-062

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Documentacion de onboarding comercial SaaS |
| Autor | Codex |
| Archivos | `docs/arquitectura/onboarding_comercial_saas.md`, `docs/arquitectura/diagramas/onboarding_comercial_saas.drawio`, `docs/arquitectura/qa_prod.md`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, onboarding comercial, billing, provisioning, tenants, APIs |
| Descripcion | Se documento el flujo de contratacion desde la web de EsLaClave: seleccion de plan, pago en linea, webhook, provisioning idempotente, creacion de tenant, invitacion segura del administrador, wizard inicial, portal de desarrollador, credenciales API, scopes, cuotas y metering. Se agrego diagrama editable `.drawio` y se actualizo `qa_prod.md` para incluir billing/provisioning. |
| Motivo | Formalizar el flujo requerido para comprar ERClave en linea y activar tenants reales sin depender de procesos manuales ni enviar contrasenas por correo. |
| Impacto | La arquitectura QA/Prod ahora contempla servicios comerciales transversales y el repo tiene una base para discutir planes, API comercial, monetizacion y alta automatica de clientes. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El diseno propone iniciar con bajo costo y evolucionar a Apigee/monetizacion avanzada cuando el volumen de integraciones lo justifique. |

### CHG-063

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Decision de dominio, DNS y costo operativo inicial |
| Autor | Codex |
| Archivos | `docs/arquitectura/onboarding_comercial_saas.md`, `TRAZABILIDAD.md` |
| Secciones | Dominio, DNS y entrada publica; Decisiones pendientes |
| Descripcion | Se documento la recomendacion de comprar dominio fuera de Google, usar Cloudflare Registrar y Cloudflare DNS para el arranque, mantener la plataforma en Google Cloud, definir subdominios base, acceso por tenant, cobro hibrido y rango mensual estimado para un lanzamiento publico limitado. |
| Motivo | Aterrizar la estrategia comercial y tecnica para publicar ERClave con costos controlados, sin depender de Google Domains/Cloud Domains como ruta principal de registro. |
| Impacto | El roadmap SaaS ahora incluye decisiones iniciales de dominio, DNS, entrada publica, activacion manual o por pago en linea, y presupuesto operativo esperado para hasta 20 tenants iniciales. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los precios reales dependeran del registrador, extension de dominio, proveedor de pagos, trafico, logs, almacenamiento y uso de correo transaccional. |

### CHG-064

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-16 |
| Cambio | Guia del siguiente paso tecnico para backend MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura backend MVP, ownership de datos, modelo conceptual, APIs, eventos |
| Descripcion | Se agrego una guia tecnica que define que el siguiente paso recomendado no es iniciar directo con base de datos ni listado de APIs, sino documentar primero ownership de datos, entidades canonicas, reglas backend, contratos entre modulos y despues derivar modelo de datos y APIs. |
| Motivo | Evitar acoplamiento prematuro entre Produccion, Almacenes, Ventas, Administracion, Billing y Provisioning al pasar de maqueta a backend real multi-tenant. |
| Impacto | El proyecto cuenta con una ruta clara para avanzar hacia `ownership_datos_mvp.md`, `modelo_datos_mvp.md` y `apis_mvp.md` sin romper la separacion modular. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El documento se basa en los modulos actualmente trabajados y en el agente Arquitecto senior de plataforma SaaS. |

### CHG-065

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-16 |
| Cambio | Ownership de datos y contratos MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Ownership de entidades, contratos entre servicios, reglas multi-tenant, eventos MVP |
| Descripcion | Se agrego el documento de ownership de datos y contratos del MVP, definiendo servicios duenos, entidades por dominio, reglas multi-tenant, contratos HTTP/eventos entre Administracion, Produccion, Almacenes, Ventas, Billing, Provisioning e Integraciones, y reglas anti-acoplamiento. Tambien se marco en la guia del siguiente paso que el documento ya fue definido. |
| Motivo | Preparar el diseno de modelo de datos y APIs sobre limites claros de responsabilidad, evitando que los modulos escriban datos ajenos o dependan de reglas solo en frontend. |
| Impacto | El proyecto ya cuenta con la base arquitectonica para derivar `modelo_datos_mvp.md` y `apis_mvp.md` sin romper la separacion modular ni el aislamiento por tenant. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los contratos son iniciales y deberan convertirse despues en especificaciones OpenAPI y eventos versionados. |

### CHG-066

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-16 |
| Cambio | Modelo de datos MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Modelo PostgreSQL MVP, schemas por servicio, entidades, indices, auditoria, outbox, referencias cruzadas |
| Descripcion | Se agrego el modelo de datos MVP para PostgreSQL con estrategia inicial de schemas por servicio, columnas comunes, tablas por dominio, indices multi-tenant, referencias internas y externas, estados iniciales, reglas de integridad backend, auditoria y patron outbox. Tambien se marcaron como definidos los enlaces al modelo desde los documentos de ownership y siguiente paso backend. |
| Motivo | Convertir el ownership y contratos del MVP en una base tecnica concreta para implementar migraciones, modelos backend y APIs sin acoplar servicios ni romper aislamiento por tenant. |
| Impacto | El proyecto ya cuenta con una guia de datos para iniciar Alembic/SQLModel y derivar el documento `apis_mvp.md` con claridad sobre tablas, reglas, snapshots, idempotencia e indices. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El modelo es conceptual-operativo; aun no crea migraciones ni codigo backend. |

### CHG-067

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Agente senior de datos y persistencia |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agente transversal prioritario, arquitectura de datos, persistencia, migraciones, seguridad |
| Descripcion | Se agrego el Arquitecto senior de datos y persistencia como agente transversal especializado en modelado de datos, relaciones, PostgreSQL, Cloud SQL, SQLAlchemy/SQLModel, Alembic, multi-tenancy, auditoria, outbox, indices, migraciones seguras, seguridad y evaluacion de tecnologias de datos. |
| Motivo | Contar con un agente experto que revise la construccion de bases de datos y relaciones con la misma linea etica del proyecto: no inventar, validar fuente de verdad, proteger seguridad, trazabilidad e integridad. |
| Impacto | Las decisiones de base de datos ahora tienen un responsable transversal con criterios de rechazo, preguntas obligatorias y fuentes de verdad documentales antes de aprobar modelos o migraciones. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El agente queda junto al Arquitecto senior de plataforma SaaS porque sus decisiones afectan a todos los modulos. |

### CHG-068

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Contratos API MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/apis_mvp.md`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | APIs por servicio, errores, paginacion, filtros, permisos, idempotencia, contratos cruzados, OpenAPI |
| Descripcion | Se agrego el documento de APIs MVP con contratos iniciales para `admin-service`, `production-service`, `inventory-service`, `sales-service`, `billing-service`, `provisioning-service` e `integration-service`. Incluye headers, paginacion, filtros, errores, permisos, endpoints por servicio, requests ejemplo, reglas backend, eventos, idempotencia y criterios para generar OpenAPI. |
| Motivo | Convertir el modelo de datos y ownership en contratos API iniciales para construir backend real con FastAPI/OpenAPI sin mezclar responsabilidades entre servicios. |
| Impacto | El proyecto ya cuenta con una base para crear especificaciones OpenAPI, modelos Pydantic, rutas FastAPI y pruebas de contrato por servicio. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El documento define contratos MVP de arquitectura; aun no crea archivos OpenAPI YAML ni codigo backend. |

### CHG-069

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Diagrama draw.io de APIs MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/diagramas/apis_mvp_relaciones.drawio`, `docs/arquitectura/apis_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | APIs MVP, relaciones entre servicios, contratos cruzados, eventos y datos |
| Descripcion | Se agrego un diagrama editable `.drawio` con el flujo de entrada por frontend, apps externas y proveedor de pago, API Gateway, servicios MVP, relaciones entre Ventas, Produccion, Almacenes, Billing, Provisioning, Administracion e Integraciones, ademas de Cloud SQL, outbox, Pub/Sub y auditoria. Se enlazo el diagrama desde `apis_mvp.md`. |
| Motivo | Facilitar la revision visual de contratos API y relaciones entre servicios antes de generar especificaciones OpenAPI o implementar backend real. |
| Impacto | El equipo puede abrir el diagrama en diagrams.net para analizar flujos, fronteras de ownership, eventos y dependencias entre servicios. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El diagrama es de arquitectura MVP; no representa aun infraestructura detallada por ambiente ni despliegue real. |

### CHG-070

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Diagrama draw.io de flujo de negocio de adquisicion y uso |
| Autor | Codex |
| Archivos | `docs/arquitectura/diagramas/flujo_negocio_adquisicion_uso.drawio`, `docs/arquitectura/onboarding_comercial_saas.md`, `TRAZABILIDAD.md` |
| Secciones | Onboarding comercial SaaS, flujo de negocio, adquisicion, activacion y uso |
| Descripcion | Se agrego un diagrama editable `.drawio` no tecnico que muestra el flujo de negocio desde descubrimiento del cliente, contratacion en linea o asesorada, confirmacion de pago o activacion manual, creacion del espacio de empresa, invitacion segura del administrador, configuracion inicial y operacion continua en Produccion, Almacenes y Ventas. Se enlazo desde el documento de onboarding comercial SaaS. |
| Motivo | Facilitar la explicacion visual del recorrido del cliente y la usabilidad del producto sin entrar en detalles tecnicos de APIs, infraestructura o servicios. |
| Impacto | El proyecto cuenta con una vista ejecutiva del flujo comercial y de adopcion para revisiones de negocio, ventas y producto. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El diagrama complementa los diagramas tecnicos existentes; no reemplaza arquitectura, APIs ni modelo de datos. |

### CHG-071

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Plan de implementacion backend MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/plan_implementacion_backend_mvp.md`, `docs/arquitectura/apis_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Fases de backend MVP, admin-service, production-service, inventory-service, sales-service, billing/provisioning, integration-service, criterios QA |
| Descripcion | Se agrego el plan de implementacion backend MVP con fases recomendadas para scaffolding FastAPI, admin-service, auditoria/idempotencia, production-service, inventory-service, sales-service, integracion frontend, billing/provisioning e integration-service. Tambien se documentaron mocks temporales, validadores recomendados, criterios para QA real, criterios para modulo real, riesgos y primer sprint sugerido. |
| Motivo | Convertir la arquitectura, ownership, modelo de datos y APIs en una ruta ejecutable para construir el backend real sin sobredimensionar ni mezclar responsabilidades. |
| Impacto | El proyecto ya tiene un plan de trabajo para pasar de maqueta a QA real iniciando por plataforma minima y `admin-service`, antes de automatizar venta publica y provisioning. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El plan no crea codigo backend todavia; sirve como guia para el siguiente sprint tecnico. |

### CHG-072

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Agentes transversales de APIs y QA |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agente transversal prioritario, APIs, contratos backend, QA, validadores, release |
| Descripcion | Se agregaron dos agentes transversales: Arquitecto senior de APIs y contratos backend, enfocado en OpenAPI, FastAPI, permisos, idempotencia, errores y contratos; e Ingeniero senior de QA, validadores y release, enfocado en automatizar reglas objetivas, pruebas, CI/CD, compatibilidad Windows/Linux y criterios de QA/Produccion. |
| Motivo | Completar los agentes necesarios antes de pasar de documentacion a contratos OpenAPI, validadores y scaffolding backend real. |
| Impacto | El proyecto cuenta con criterios explicitos para disenar APIs seguras y para convertir reglas de agentes/documentos en validadores repetibles antes de implementar servicios. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Estos agentes complementan al Arquitecto SaaS y al Arquitecto de datos; no reemplazan a los agentes tecnicos por modulo. |

### CHG-073

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Contratos OpenAPI MVP iniciales |
| Autor | Codex |
| Archivos | `.gitignore`, `contracts/api/README.md`, `contracts/api/admin-service.openapi.yaml`, `contracts/api/production-service.openapi.yaml`, `contracts/api/inventory-service.openapi.yaml`, `contracts/api/sales-service.openapi.yaml`, `contracts/api/billing-service.openapi.yaml`, `contracts/api/provisioning-service.openapi.yaml`, `contracts/api/integration-service.openapi.yaml`, `docs/arquitectura/apis_mvp.md`, `package.json`, `tools/validators/validate-all.js`, `tools/validators/validate-openapi-contracts.js`, `TRAZABILIDAD.md` |
| Secciones | Contratos API, OpenAPI, validadores, API MVP |
| Descripcion | Se crearon los contratos OpenAPI iniciales para los siete servicios MVP: Administracion, Produccion, Almacenes, Ventas, Billing, Provisioning e Integraciones. Tambien se agrego un validador `validate-openapi-contracts.js` que verifica existencia de contratos y metadatos minimos como `operationId`, `x-required-module`, `x-permissions` e `Idempotency-Key`; se conecto al comando general `npm run validate` y se actualizo el README de contratos API. |
| Motivo | Iniciar la implementacion API-first con contratos versionados antes de crear codigo FastAPI, evitando inventar endpoints durante el desarrollo backend. |
| Impacto | El proyecto ya cuenta con una primera version contractual para generar rutas, modelos Pydantic, pruebas de contrato y scaffolding backend por servicio. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los contratos son MVP iniciales y deberan enriquecerse durante la implementacion de cada servicio. |

### CHG-074

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Scaffolding backend base con FastAPI |
| Autor | Codex |
| Archivos | `.gitignore`, `README.md`, `backend/README.md`, `backend/.env.example`, `backend/pyproject.toml`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/.gitkeep`, `backend/shared/erclave_common/*`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/*`, `backend/services/admin-service/tests/test_health.py`, `backend/services/admin_service_adapter.py`, `docs/arquitectura/apis_mvp.md`, `docs/arquitectura/plan_implementacion_backend_mvp.md`, `package.json`, `tools/validators/validate-all.js`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Backend FastAPI, admin-service, configuracion por ambiente, Alembic, health checks, validadores |
| Descripcion | Se creo el scaffolding backend base con FastAPI para `admin-service`, incluyendo estructura de proyecto Python, configuracion por ambiente, variable configurable `ERCLAVE_API_PUBLIC_BASE_URL` para no amarrar el dominio aun no comprado, health checks, manejo comun de errores, middleware de `correlation_id`, placeholder de tenant, Alembic inicial, tests de health y validador `validate-backend-scaffold.js` conectado a `npm run validate`. |
| Motivo | Iniciar la implementacion real del backend siguiendo el plan MVP, sin depender de dominio definitivo y preparando la base tecnica para implementar `admin-service` antes de los modulos operativos. |
| Impacto | El repo ya puede validar que existe el esqueleto backend minimo y cuenta con comandos documentados para levantar FastAPI localmente cuando se instalen dependencias. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro; `python -m py_compile` ejecutado correctamente sobre los archivos Python del scaffolding. |
| Observaciones | Aun no se implementan endpoints funcionales de `admin-service`; solo endpoints tecnicos `/health`, `/ready` y `/version`. |

### CHG-075

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Modelo fisico inicial de admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/models.py`, `backend/alembic/env.py`, `backend/alembic/versions/20260617_0001_admin_service_initial.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/plan_implementacion_backend_mvp.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, modelo fisico, SQLAlchemy, Alembic, multi-tenant, auditoria |
| Descripcion | Se definio el modelo fisico inicial de `admin-service` con SQLAlchemy y migracion Alembic para `admin.tenants`, `admin.users`, `admin.roles`, `admin.permissions`, `admin.role_permissions`, `admin.memberships`, `admin.membership_roles`, `admin.tenant_modules` y `admin.audit_events`. Se documento la decision de usar usuarios globales y membresias por tenant para soportar SaaS multi-tenant sin duplicar identidades. |
| Motivo | Crear la base de datos real de Administracion antes de implementar endpoints, manteniendo ownership claro de tenants, usuarios, permisos, modulos activos y auditoria. |
| Impacto | `admin-service` ya cuenta con una fuente tecnica de verdad para el schema `admin` y Alembic puede apuntar al metadata del servicio. |
| Validacion | `python -m py_compile` ejecutado correctamente sobre los archivos Python nuevos; `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Se agregaron tablas puente `role_permissions` y `membership_roles` porque son necesarias para resolver permisos efectivos por tenant. |

### CHG-076

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Catalogo seed inicial de modulos MVP |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/seeds/__init__.py`, `backend/services/admin-service/app/seeds/catalog.py`, `backend/services/admin-service/README.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/arquitectura/plan_implementacion_backend_mvp.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, seeds, modulos MVP, validadores |
| Descripcion | Se creo el catalogo seed versionado de modulos MVP con `admin`, `production`, `inventory`, `sales`, `billing`, `provisioning` e `integrations`, incluyendo servicio duenio, estatus, visibilidad comercial y orden sugerido. El validador backend ahora verifica que el catalogo exista y contenga los siete modulos esperados. |
| Motivo | Definir la fuente inicial de verdad para codigos de modulo antes de crear permisos, entitlements o scripts de carga a base de datos. |
| Impacto | Los siguientes pasos pueden extraer permisos desde OpenAPI y aplicar seeds idempotentes sin inventar codigos de modulo en cada endpoint. |
| Validacion | `python -m py_compile` ejecutado correctamente sobre el catalogo seed; `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Este cambio no inserta datos en PostgreSQL; prepara el catalogo para el siguiente script seed idempotente. |

### CHG-077

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-22 |
| Cambio | Guias operativas para Cloud SQL PostgreSQL QA |
| Autor | Codex |
| Archivos | `docs/operaciones/README.md`, `docs/operaciones/cloud_sql_postgres_qa.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Documentacion operativa, base PostgreSQL QA, Cloud SQL Auth Proxy, migraciones Alembic |
| Descripcion | Se creo una carpeta de documentacion operativa con una guia paso a paso para crear una base PostgreSQL QA en Google Cloud SQL, conectarse desde Windows, Linux o macOS con Cloud SQL Auth Proxy, configurar `ERCLAVE_DATABASE_URL`, ejecutar Alembic y levantar `admin-service`. |
| Motivo | Facilitar que el ambiente de base de datos en nube pueda configurarse de forma repetible y entendible sin depender de conocimiento previo avanzado de operaciones cloud. |
| Impacto | El proyecto cuenta con una ruta documentada para crear la base QA compartida antes de ejecutar migraciones reales y preparar seeds idempotentes. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | La guia no crea recursos automaticamente ni guarda secretos; usa placeholders para contrasenas, proyecto GCP y connection name. |

### CHG-078

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Seed idempotente de permisos MVP |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/seeds/permissions.py`, `backend/scripts/seed_admin_mvp.py`, `backend/services/admin-service/tests/test_permission_seeds.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/operaciones/cloud_sql_postgres_qa.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, seeds, permisos MVP, OpenAPI, PostgreSQL QA |
| Descripcion | Se creo un extractor de permisos MVP desde `contracts/api/*.openapi.yaml` usando `x-permissions`, junto con un runner idempotente que aplica los permisos sobre `admin.permissions` mediante `INSERT ... ON CONFLICT (code) DO UPDATE`. Tambien se agrego una prueba del extractor y documentacion de ejecucion. |
| Motivo | Poblar la base QA con el catalogo inicial de permisos reales despues de ejecutar la migracion Alembic, sin duplicar registros al reintentar el proceso. |
| Impacto | `admin-service` ya cuenta con un camino repetible para cargar permisos globales MVP en PostgreSQL y preparar roles, policy evaluation y entitlements reales. |
| Validacion | `python -m py_compile` sobre el runner y extractor; `pytest services/admin-service/tests/test_permission_seeds.py`; `python scripts/seed_admin_mvp.py --dry-run`; `npm.cmd run validate`. |
| Observaciones | El seed aplica `admin.permissions`; no crea tenants, roles, membresias ni entitlements. El catalogo de modulos sigue versionado en codigo porque el modelo fisico inicial aun no tiene tabla global `admin.modules`. |

### CHG-079

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Agente custodio de la base de datos ERClave |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, base de datos ERClave, migraciones, validadores, impacto entre schemas |
| Descripcion | Se agrego un agente transversal especializado en la base de datos real de ERClave. Su rol es conocer y proteger schemas, migraciones Alembic, seeds, dependencias entre servicios, drift entre docs/modelos/base, impacto entre schemas y reglas automatizables para evitar que el proyecto crezca rompiendo datos o ownership. |
| Motivo | Cubrir una necesidad mas especifica que el diseno general de datos: vigilancia continua de la base ERClave concreta y automatizacion de alertas cuando un cambio pueda afectar otros schemas, servicios, reportes, permisos o ambientes. |
| Impacto | Los cambios futuros que toquen modelos, migraciones, seeds, contratos persistentes o base QA/Prod deberan considerar a este agente junto con el Arquitecto de datos y el Ingeniero QA. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Este cambio define el rol; los validadores concretos del custodio se implementaran progresivamente conforme existan mas schemas y migraciones. |

### CHG-080

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Validadores de agentes y guardrails de base de datos |
| Autor | Codex |
| Archivos | `.gitignore`, `tools/validators/validate-agents.js`, `tools/validators/validate-db-guardrails.js`, `tools/validators/validate-all.js`, `package.json`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes, validadores, custodio de base de datos, migraciones Alembic, seeds idempotentes |
| Descripcion | Se agregaron validadores automaticos para confirmar que los agentes transversales y por modulo siguen presentes y para revisar guardrails estaticos de base de datos: migraciones Alembic con revision unica, ausencia de operaciones destructivas en `upgrade`, `tenant_id` en tablas administrativas tenant-scoped, ausencia de FK cruzadas, extractor de permisos y seed idempotente con `ON CONFLICT`. |
| Motivo | Convertir al nuevo custodio de base de datos ERClave y las reglas de agentes en checks ejecutables antes de seguir creciendo el backend. |
| Impacto | `npm run validate` ahora falla si se pierde cobertura de agentes o si una migracion/seed rompe reglas basicas de seguridad estructural de la base. |
| Validacion | `npm.cmd run validate:agents`, `npm.cmd run validate:db-guardrails` y `npm.cmd run validate` ejecutados correctamente. |
| Observaciones | Los guardrails actuales son estaticos y no requieren conexion a Cloud SQL. Mas adelante pueden ampliarse con comparacion contra schema real de QA/Prod cuando exista un flujo seguro con credenciales. |

### CHG-081

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Validador de compatibilidad multiplataforma |
| Autor | Codex |
| Archivos | `tools/validators/validate-cross-platform.js`, `tools/validators/validate-all.js`, `package.json`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Validadores, compatibilidad Windows/Linux/macOS, automatizacion, operaciones Cloud SQL |
| Descripcion | Se agrego un validador estatico para proteger la portabilidad del proyecto: revisa que scripts npm, validadores Node y scripts backend no dependan de comandos Windows-only, que la guia Cloud SQL mantenga instrucciones para Windows, Linux y macOS, y que el workflow de GitHub Actions ejecute `npm run validate` sobre Ubuntu. |
| Motivo | Confirmar que lo construido para seeds, validadores y operacion QA pueda mantenerse usable desde Linux, Windows y macOS conforme crezca el equipo o se mueva a CI. |
| Impacto | `npm run validate` ahora alerta si se introduce una dependencia operativa de sistema operativo en scripts compartidos o si se pierde documentacion multiplataforma esencial. |
| Validacion | `npm.cmd run validate:cross-platform` y `npm.cmd run validate` ejecutados correctamente. |
| Observaciones | Los comandos de usuario para activar `.venv`, descargar Cloud SQL Proxy o usar PowerShell siguen documentados por sistema operativo; el validador se enfoca en automatizacion compartida y documentacion minima. |

### CHG-082

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Seed idempotente de tenant demo QA |
| Autor | Codex |
| Archivos | `backend/scripts/seed_admin_qa_demo.py`, `backend/services/admin-service/tests/test_qa_demo_seed.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `docs/operaciones/cloud_sql_postgres_qa.md`, `tools/validators/validate-backend-scaffold.js`, `tools/validators/validate-db-guardrails.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, QA demo, tenants, usuarios, roles, permisos, modulos activos |
| Descripcion | Se creo un script idempotente para poblar QA con el tenant `demo-qa`, usuario `admin.qa@erclave.local`, rol `owner`, membresia activa, modulos activos de QA y asignacion del rol owner a todos los permisos activos. Tambien se agregaron pruebas y guardrails para confirmar que el seed use `ON CONFLICT` en las tablas afectadas. |
| Motivo | Tener un primer tenant real de QA para validar permisos, membresias, roles y modulos activos antes de implementar endpoints funcionales de `admin-service`. |
| Impacto | La base QA puede pasar de estructura y catalogo de permisos a un contexto SaaS minimo operable para pruebas de policy evaluation y futuros endpoints. |
| Validacion | `python -m py_compile` sobre el script; `pytest services/admin-service/tests`; `python scripts/seed_admin_qa_demo.py --dry-run`; `npm.cmd run validate`. |
| Observaciones | El seed demo no crea contrasenas ni credenciales de autenticacion; solo crea identidad, membresia y autorizaciones internas para QA. |

### CHG-083

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Endpoints MVP de lectura de admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/app/main.py`, `backend/services/admin_service_adapter.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, FastAPI, PostgreSQL, tenants, entitlements, policy evaluation, usuarios, roles |
| Descripcion | Se implemento el primer corte funcional de endpoints reales de `admin-service`: `GET /v1/tenants/{tenant_id}`, `GET /v1/tenants/{tenant_id}/entitlements`, `POST /v1/policy/evaluate`, `GET /v1/users` y `GET /v1/roles`. Se agrego repositorio SQL para leer PostgreSQL, schemas Pydantic y pruebas con repositorio falso para validar el contrato sin depender de Cloud SQL en CI. |
| Motivo | Crear la primera API real que el frontend podra consumir antes de migrar pantallas operativas fuera de `mockDb` y `localStorage`. |
| Impacto | `admin-service` deja de ser solo health checks y puede leer tenants, modulos activos, usuarios, roles y evaluar permisos sobre los datos seed de QA. |
| Validacion | `python -m py_compile` sobre los nuevos modulos y adapter; `pytest services/admin-service/tests`; `uvicorn services.admin_service_adapter:app --port 8001` carga correctamente; `npm.cmd run validate`. |
| Observaciones | Los endpoints mutables siguen pendientes. La autenticacion real aun no esta implementada; `X-Tenant-Id` es header operativo temporal para lecturas de usuarios y roles. |

### CHG-084

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Capa frontend API para admin-service |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `frontend/api/client.js`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/data/modules.js`, `backend/services/admin-service/app/main.py`, `README.md`, `backend/README.md`, `tools/validators/validate-active-module-localization.js`, `tools/validators/validate-architecture.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, admin-service, API client, CORS local, Administracion, validadores de arquitectura |
| Descripcion | Se agrego una capa `frontend/api/` para centralizar consumo HTTP, con cliente base, configuracion local y funciones de `admin-service`. Se habilito el modulo visual `Administracion` en la navegacion MVP con un panel hibrido mock/API para tenant, modulos activos, usuarios, roles y policy evaluation. Tambien se habilito CORS local en `admin-service` para permitir llamadas desde el frontend local. |
| Motivo | Conectar el primer bloque real de APIs sin romper la maqueta ni permitir `fetch` dispersos en pantallas. |
| Impacto | El frontend puede empezar a leer datos reales de Cloud SQL QA mediante `admin-service`, conservando fallback mock. La arquitectura ahora exige que nuevas llamadas HTTP pasen por `frontend/api/`. |
| Validacion | `python -m py_compile services/admin-service/app/main.py`; `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate:active-localization`; `npm.cmd run validate`. |
| Observaciones | La conexion API usa el tenant demo QA por defecto. Autenticacion real, manejo de token y despliegue de frontend QA quedan pendientes para siguientes cambios. |

### CHG-085

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Acceso a Administracion desde engrane |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, navegacion, Administracion, shell |
| Descripcion | Se movio el acceso visual de `Administracion` fuera de la lista principal de modulos y se conecto al boton de engrane del footer lateral. El engrane navega al panel de Administracion y queda marcado como activo cuando esa vista esta seleccionada. |
| Motivo | Mantener la barra principal enfocada en modulos operativos y dejar Administracion como configuracion/plataforma accesible desde el icono esperado. |
| Impacto | El panel hibrido mock/API de Administracion sigue disponible, pero ya no aparece como modulo operativo principal. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate:active-localization`; `npm.cmd run validate`. |
| Observaciones | Administracion sigue incluida en validaciones de localizacion activa porque es una vista real conectada al admin-service. |

### CHG-086

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Entitlements operables en admin-service y frontend |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, entitlements, Administracion, API QA, frontend |
| Descripcion | Se implemento `PUT /v1/tenants/{tenant_id}/entitlements/{module_code}` para activar, inactivar o suspender modulos de un tenant usando PostgreSQL. El panel de Administracion ahora muestra acciones por modulo en modo API QA y refresca los datos reales tras cada cambio. |
| Motivo | Pasar el primer bloque de Administracion de lectura real a operacion real, empezando por modulos activos del tenant porque impactan directamente la disponibilidad SaaS y la evaluacion de politicas. |
| Impacto | El tenant demo QA puede administrar entitlements desde el backend y desde la maqueta local sin tocar manualmente Cloud SQL. El frontend conserva modo mock y solo habilita acciones cuando la API QA esta lista. |
| Validacion | `pytest`; `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; prueba real contra Cloud SQL QA cambiando `integrations` a `inactive` y restaurandolo a `active`; `/ready` respondio `ready`. |
| Observaciones | Al cierre de este cambio quedaban pendientes los endpoints mutables de tenants, usuarios y roles. No se agrego migracion porque `admin.tenant_modules` ya incluia `status`, `source` y `limits`. |

### CHG-087

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Usuarios operables en admin-service y panel de Administracion |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, usuarios, membresias, roles de membresia, Administracion, API QA |
| Descripcion | Se implementaron `POST /v1/users/invitations`, `PATCH /v1/users/{user_id}` y `POST /v1/users/{user_id}/disable`. La invitacion crea o actualiza identidad global, crea o reactiva la membresia del tenant y asigna roles de membresia. El panel de Administracion agrega formulario de invitacion y accion de desactivar usuario en modo API QA. |
| Motivo | Continuar la secuencia arquitectonica despues de entitlements: administrar usuarios y membresias antes de avanzar a roles/permisos finos o autenticacion real. |
| Impacto | QA ya puede operar usuarios del tenant demo desde API y frontend local sin introducir contrasenas ni proveedor de identidad. El actor demo queda protegido en UI para evitar desactivar el usuario usado en pruebas de policy evaluation. |
| Validacion | `pytest services/admin-service/tests/test_admin_api.py`; `pytest`; `npm.cmd run validate:syntax`; prueba real contra Cloud SQL QA invitando, editando y desactivando un usuario temporal; `/ready` respondio `ready`. |
| Observaciones | La desactivacion afecta la membresia del tenant, no elimina la identidad global. Quedan pendientes auditoria/idempotencia formal y endpoints mutables de roles. |

### CHG-088

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Auditoria e idempotencia base para mutaciones de admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, auditoria, idempotencia, contratos OpenAPI, Administracion |
| Descripcion | Se agrego validacion obligatoria de `Idempotency-Key` en las mutaciones actuales de entitlements y usuarios. Cada comando registra un evento en `admin.audit_events` dentro de la misma transaccion, con accion, recurso, estado anterior, estado posterior, `correlation_id` e `idempotency_key`. El cliente frontend genera headers por comando y el contrato OpenAPI quedo alineado para `PATCH /v1/users/{user_id}`. |
| Motivo | Cerrar la recomendacion arquitectonica previa antes de avanzar a roles/permisos mutables o migrar modulos operativos, asegurando trazabilidad minima de acciones criticas. |
| Impacto | Las operaciones reales de Administracion quedan auditadas y los reintentos empiezan a portar una clave idempotente verificable. Todavia no existe tabla dedicada de comandos procesados ni respuesta cacheada por idempotency key. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py services/admin_service_adapter.py`; `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate`. `python -m pytest services/admin-service/tests/test_admin_api.py` no se pudo ejecutar porque el ambiente local no tiene instalado `pytest`. |
| Observaciones | La auditoria usa `actor_type='system'` de forma temporal hasta integrar autenticacion real y actor autenticado. |

### CHG-089

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Roles y permisos operables en admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, roles, permisos, policy, auditoria, Administracion |
| Descripcion | Se implementaron `POST /v1/roles`, `PATCH /v1/roles/{role_id}`, `PUT /v1/roles/{role_id}/permissions` y `GET /v1/permissions`. Las mutaciones de roles exigen `Idempotency-Key`, aceptan `X-Correlation-Id` y registran auditoria en `admin.audit_events`. El panel de Administracion permite crear roles, activar/inactivar roles y asignar permisos disponibles desde API QA. |
| Motivo | Completar el nucleo SaaS minimo de Administracion antes de iniciar la migracion de modulos operativos reales. |
| Impacto | QA puede operar roles y permisos sin tocar manualmente Cloud SQL. `POST /v1/policy/evaluate` puede reflejar cambios de permisos hechos desde el propio `admin-service`. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py services/admin_service_adapter.py`; `python -m pytest services/admin-service/tests/test_admin_api.py` con 20 tests correctos; `python -m pytest` con 25 tests correctos; `npm.cmd run validate:syntax`; `npm.cmd run validate`. |
| Observaciones | La UI permite agregar permisos al rol; la remocion fina de permisos queda para un refinamiento posterior junto con actor autenticado real. |

### CHG-090

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Rediseño del panel operativo de Administracion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, panel API QA, UX |
| Descripcion | Se rediseñaron las secciones de modulos activos, usuarios y roles del panel de Administracion para usar un tablero compacto con secciones delimitadas, registros escaneables, badges de estado, formularios integrados y layout responsive. |
| Motivo | Mejorar la legibilidad y operabilidad del panel conectado a `admin-service`, evitando listas extendidas y formularios demasiado dispersos. |
| Impacto | La Administracion en modo API QA conserva las mismas acciones pero se presenta con una interfaz mas clara para probar entitlements, usuarios, roles y permisos. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`. |
| Observaciones | No cambia contratos ni comportamiento backend. |

### CHG-091

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Reacomodo espacial del panel de Administracion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, distribucion, UX |
| Descripcion | Se reemplazo el hero alto por un encabezado operativo mas compacto con KPIs integrados. El cuerpo de Administracion se reacomodo en una grilla de 12 columnas: modulos activos como franja superior, usuarios y roles como paneles balanceados, con listas contenidas y formularios mas compactos. |
| Motivo | Mejorar la distribucion, reducir espacios vacios y aprovechar mejor el ancho disponible durante pruebas de API QA. |
| Impacto | El panel conserva las mismas acciones, pero ahora prioriza lectura rapida y operacion repetida sin crecer verticalmente de forma innecesaria. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`. |
| Observaciones | Cambio visual sin impacto en contratos ni backend. |

### CHG-092

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Correccion responsive del panel de Administracion |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, responsive, UX |
| Descripcion | Se reemplazaron las grillas fijas del panel de Administracion por un flujo fluido de una columna con subgrids `auto-fit`, se redujeron anchos minimos rigidos, se ajustaron KPIs, formularios, registros y acciones para evitar desbordes al cambiar el tamaño de pantalla. |
| Motivo | Evitar que el modulo de Administracion se desordene en ventanas medianas, tablets o pantallas moviles. |
| Impacto | El panel conserva el diseño operativo, pero ahora se mantiene ordenado por defecto: header en una columna, modulos arriba, usuarios y roles apilados, subgrids fluidos y controles a ancho completo en movil. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate`. |
| Observaciones | Cambio visual sin impacto en contratos ni backend. |

### CHG-093

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Prueba API QA real de Administracion |
| Autor | Codex |
| Archivos | `TRAZABILIDAD.md` |
| Secciones | Admin-service, QA real, entitlements, usuarios, roles, permisos, auditoria |
| Descripcion | Se ejecuto un flujo real contra `admin-service` en `http://127.0.0.1:8000` conectado a Cloud SQL QA mediante proxy local. Se valido lectura de tenant, lectura de entitlements, inactivacion/restauracion de `inventory`, lectura de usuarios, invitacion y desactivacion de usuario temporal, lectura de roles, creacion/inactivacion/activacion/inactivacion final de rol temporal, lectura de permisos, asignacion de permiso a rol temporal y `POST /v1/policy/evaluate`. |
| Motivo | Confirmar que el nucleo MVP de Administracion opera contra QA real y no solo mediante tests unitarios o maqueta local. |
| Impacto | Se confirmo persistencia real en Cloud SQL QA, restauracion del modulo `inventory` a `active`, usuario temporal desactivado y rol temporal `codex_qa_1782963345` inactivo. |
| Validacion | Flujo API completo exitoso; `policy.evaluate` respondio `allowed=True`; consulta directa a `admin.audit_events` encontro 9 eventos con `Idempotency-Key` de la corrida `1782963345`. |
| Observaciones | Quedaron datos temporales auditables en QA: usuario `codex.qa.1782963345@erclave.local` desactivado y rol `codex_qa_1782963345` inactivo. |

### CHG-094

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Primer corte backend real de production-service |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260701_0002_production_service_initial.py`, `backend/services/production-service/app/*`, `backend/services/production-service/tests/test_production_api.py`, `backend/services/production_service_adapter.py`, `backend/pyproject.toml`, `backend/README.md`, `backend/services/production-service/README.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Production-service, FastAPI, PostgreSQL, productos/servicios, backend MVP |
| Descripcion | Se creo el primer scaffold funcional de `production-service` con FastAPI, health checks compartidos, repositorio SQL, schemas Pydantic, adapter para Uvicorn, pruebas con repositorio falso y migracion inicial para `production.product_services`. El primer corte implementa `GET/POST /v1/production/product-services`, `GET/PATCH /v1/production/product-services/{product_service_id}` y `PATCH /v1/production/product-services/{product_service_id}/status`. |
| Motivo | Iniciar el primer modulo operativo real despues de validar `admin-service` en QA, empezando por el catalogo de productos/servicios como base para recetas y ordenes. |
| Impacto | El backend ya tiene una frontera real para Produccion sin escribir inventario, costos ni contabilidad. La suite de backend ahora cubre admin-service y production-service. |
| Validacion | `python -m py_compile` sobre los nuevos modulos y migracion; `python -m pytest services/production-service/tests/test_production_api.py` con 8 tests correctos; `python -m pytest` con 33 tests correctos; `npm.cmd run validate`; `alembic upgrade head` aplicado en Cloud SQL QA; prueba API real en `production-service` local puerto `8002` creando, leyendo, actualizando, inactivando, restaurando y buscando `codex_prod_1782964372`. |
| Observaciones | Quedo dato temporal QA `codex_prod_1782964372` activo para validar persistencia. Recetas, versiones, ordenes, areas laborales y maquinaria quedan para cortes posteriores. |

### CHG-095

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Diagramas de estado real backend MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/diagramas/apis_mvp_relaciones.drawio`, `docs/arquitectura/diagramas/estado_actual_backend_mvp.drawio`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, diagramas, backend MVP, QA real |
| Descripcion | Se ajusto el diagrama de APIs MVP y relaciones para distinguir servicios ya operables en QA de servicios objetivo. `admin-service` queda marcado como real para entitlements, usuarios, roles, permisos, policy y auditoria; `production-service` queda marcado como real parcial para `product_services`. Tambien se creo un diagrama nuevo del estado actual backend MVP mostrando frontend local, servicios FastAPI locales, Cloud SQL Auth Proxy, Cloud SQL QA, schemas reales, migraciones, pruebas y validadores. |
| Motivo | Evitar que los diagramas mezclen roadmap objetivo con estado implementado, despues de validar Administracion y el primer corte de Produccion contra QA real. |
| Impacto | El arquitecto puede revisar visualmente que ya existe un nucleo QA real y que recetas, ordenes, inventario, ventas, billing, provisioning e integraciones siguen como fases posteriores. |
| Validacion | `npm.cmd run validate:traceability`; `npm.cmd run validate:architecture`. |
| Observaciones | No cambia contratos, backend ni frontend; es actualizacion documental editable en diagrams.net. |

### CHG-096

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Session Context MVP previo al login |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `frontend/api/admin.js`, `frontend/app.js`, `backend/README.md`, `backend/services/admin-service/README.md`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, session context, permisos, entitlements, frontend, navegacion |
| Descripcion | Se agrego `GET /v1/session/context` para devolver tenant, usuario, entitlements, permisos efectivos y modulos activos usando `X-Tenant-Id` y `X-Actor-Id` como contexto temporal. El frontend en modo API QA carga ese contexto, bloquea modulos inactivos o no contratados y refresca la sesion despues de cambios de entitlements desde Administracion. |
| Motivo | Dar el paso recomendado antes del login completo: eliminar dependencias de navegacion fija y hacer que la app use el contexto real de tenant, usuario, permisos y modulos activos desde `admin-service`. |
| Impacto | Si un modulo se desactiva para el tenant QA, la navegacion del frontend deja de permitir entrada a ese modulo en modo API. Este contrato queda listo para reemplazar `X-Actor-Id` por el subject de un token OIDC/JWT en la fase de login real. |
| Validacion | `python -m pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate:syntax`; `npm.cmd run validate:openapi`. |
| Observaciones | No implementa login ni proveedor de identidad todavia; establece la frontera de sesion que usara el login posterior. |

### CHG-097

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Publicacion QA en Firebase Hosting y Cloud Run |
| Autor | Codex |
| Archivos | `.firebaserc`, `firebase.json`, `backend/Dockerfile`, `backend/services/admin-service/app/main.py`, `backend/services/production-service/app/main.py`, `frontend/env.js`, `frontend/index.html`, `frontend/api/config.js`, `TRAZABILIDAD.md` |
| Secciones | Deploy QA, Firebase Hosting, Cloud Run, Cloud SQL QA, CORS |
| Descripcion | Se preparo el repo para despliegue QA: Firebase Hosting sirve la maqueta desde `frontend`, Cloud Run publica `admin-service-qa` y `production-service-qa`, y el frontend online arranca en modo API apuntando a `admin-service-qa`. Se agrego configuracion runtime `frontend/env.js`, Dockerfile comun para servicios FastAPI y CORS para dominios Firebase `erclave.web.app` / `erclave.firebaseapp.com`. |
| Motivo | Permitir que negocio, arquitectura y comercial revisen la maqueta QA en linea usando el backend QA real sin depender de levantar servicios locales. |
| Impacto | La maqueta queda disponible en `https://erclave.web.app` y consume `admin-service-qa` en Cloud Run conectado a Cloud SQL QA. `production-service-qa` queda publicado para el primer corte real de productos/servicios. |
| Validacion | Deploy exitoso de Cloud Run para `admin-service-qa` y `production-service-qa`; deploy exitoso de Firebase Hosting; smoke test `GET /ready`, `GET /v1/session/context`, `GET /v1/production/product-services`, `curl -I https://erclave.web.app`, CORS preflight desde `https://erclave.web.app`. |
| Observaciones | Los servicios QA estan expuestos sin autenticacion final para facilitar revision temprana. Antes de compartir masivamente conviene agregar control de acceso, login o proteccion temporal. |

### CHG-098

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Login QA con Firebase Auth |
| Autor | Codex |
| Archivos | `backend/pyproject.toml`, `backend/shared/erclave_common/config.py`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/scripts/seed_admin_qa_demo.py`, `backend/README.md`, `contracts/api/admin-service.openapi.yaml`, `frontend/auth.js`, `frontend/api/client.js`, `frontend/api/admin.js`, `frontend/api/config.js`, `frontend/app.js`, `frontend/env.js`, `frontend/index.html`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Firebase Auth, admin-service, session context, frontend QA, Cloud Run, Firebase Hosting |
| Descripcion | Se conecto la maqueta QA con Firebase Auth Web usando Google Sign-In en el frontend y verificacion de Firebase ID tokens en `admin-service`. En `ERCLAVE_AUTH_MODE=firebase`, `GET /v1/session/context` resuelve el usuario por email autenticado y tenant, dejando `X-Actor-Id` como fallback local/demo. El frontend envia `Authorization: Bearer <idToken>`, muestra una puerta de acceso Google en modo API y conserva el modo mock para revision sin backend. |
| Motivo | Pasar del contexto temporal por header a una primera autenticacion real reutilizable para QA, sin perder velocidad de desarrollo local. |
| Impacto | `admin-service-qa` ya rechaza `session/context` sin token, el tenant QA tiene owner corporativo `eslaclavecaf@gmail.com` sembrado como usuario activo, y la maqueta publicada en `https://erclave.web.app` pide login antes de consumir APIs reales. |
| Validacion | `python -m pytest`; `node --check frontend/app.js`; `node --check frontend/auth.js`; `node --check frontend/api/client.js`; deploy Cloud Run `admin-service-qa` revision `admin-service-qa-00002-xmr`; seed QA aplicado via Cloud SQL Auth Proxy; deploy Firebase Hosting; smoke tests `curl -I https://erclave.web.app`, `GET /ready`, `GET /v1/session/context` sin token devuelve 401 `auth_required`, preflight CORS con `Authorization` devuelve 200. |
| Observaciones | Falta inicializar Firebase Authentication y habilitar el proveedor Google en Firebase Console; el intento por API devolvio `CONFIGURATION_NOT_FOUND` porque Auth aun no tiene configuracion inicial en el proyecto. |

### CHG-099

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Modelo multitenant e identidad SaaS |
| Autor | Codex |
| Archivos | `docs/arquitectura/modelo_multitenant.md`, `docs/arquitectura/qa_prod.md`, `docs/arquitectura/ownership_datos_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Multitenant, Firebase Auth, roles, permisos, entitlements, billing, provisioning, contratacion en linea |
| Descripcion | Se documento el modelo multitenant objetivo: Firebase Auth solo resuelve identidad, mientras ERClave gobierna tenant, membresias, roles, permisos efectivos, modulos contratados, limites, estados comerciales y policy. Tambien se aterrizo el flujo de `session/context`, seleccion de tenant, estados de tenant, reglas de contratacion en linea, provisioning idempotente, implicaciones para APIs, datos, frontend y soporte interno. |
| Motivo | Evitar que la incorporacion de Firebase Auth desplace reglas de negocio hacia el proveedor de identidad y dejar claro como escalar a usuarios multiempresa, roles por tenant y compra en linea. |
| Impacto | Arquitectura queda alineada para implementar login real, selector de tenant, autorizacion backend, billing/provisioning y pruebas de aislamiento sin redisenar la base conceptual. |
| Validacion | Documento revisado contra `ownership_datos_mvp.md`, `onboarding_comercial_saas.md`, `modelo_datos_mvp.md` y estado actual de `session/context`. |
| Observaciones | No cambia codigo ni contratos; es definicion arquitectonica para guiar siguientes fases. |

### CHG-100

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Actualizacion de agentes con contexto multitenant |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, plataforma SaaS, datos, APIs, QA, reglas comunes, Administracion |
| Descripcion | Se actualizaron los agentes necesarios para incorporar el modelo multitenant definido: Firebase/Auth solo identifica, mientras ERClave resuelve tenant, membresias, roles, permisos, entitlements, limites, billing/provisioning y policy. Se agregaron preguntas, rechazos y fuentes obligatorias para Arquitectura SaaS, Datos/Persistencia, APIs/Contratos, QA/Release, reglas comunes y Administracion. |
| Motivo | Asegurar que futuras decisiones tecnicas y funcionales no coloquen permisos, modulos contratados o estado comercial en Firebase, frontend o localStorage, y que los agentes protejan usuarios multiempresa y aislamiento por tenant. |
| Impacto | Las revisiones futuras deberan validar `session/context`, membresia activa, rol por tenant, modulo contratado, permiso efectivo, estados comerciales e idempotencia de billing/provisioning antes de aprobar cambios relacionados. |
| Validacion | Revision documental de `AGENTES.md` contra `docs/arquitectura/modelo_multitenant.md`; `npm.cmd run validate:traceability`; `npm.cmd run validate`. |
| Observaciones | No cambia codigo de ejecucion; fortalece criterios de revision y decision. |

### CHG-101

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-03 |
| Cambio | Cierre login local y autorizacion backend comun |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `frontend/env.js`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `TRAZABILIDAD.md` |
| Secciones | Firebase Auth, local demo, admin-service, permisos efectivos, mutaciones, QA |
| Descripcion | Se ajusto la configuracion frontend para que `localhost`/`127.0.0.1` usen backend local y modo demo sin quedar bloqueados por Firebase Auth, mientras `erclave.web.app` conserva `authMode=firebase`. Se agrego una dependencia comun de autorizacion en `admin-service` que, en `ERCLAVE_AUTH_MODE=firebase`, valida token, membresia activa y permiso efectivo antes de ejecutar mutaciones de entitlements, usuarios y roles. |
| Motivo | Cerrar el paso minimo de login QA/local sin bloquear desarrollo, y avanzar al guard backend recomendado para que las acciones criticas no dependan solo de UI o de token autenticado sin permiso. |
| Impacto | Local vuelve a cargar con `http://127.0.0.1:8000` y `X-Actor-Id` demo; QA mantiene Firebase obligatorio. Las mutaciones en QA quedan protegidas por permisos como `admin.entitlement.manage`, `admin.user.invite`, `admin.user.update`, `admin.user.disable`, `admin.role.create` y `admin.role.update`. |
| Validacion | `python -m pytest`; `npm.cmd run validate`; deploy Cloud Run `admin-service-qa` revision `admin-service-qa-00003-cwf`; deploy Firebase Hosting; smoke local `GET /v1/session/context` con `X-Actor-Id`; smoke QA `GET /ready`; `GET /v1/session/context` sin token devuelve 401 `auth_required`; mutacion `PUT /v1/tenants/{tenant_id}/entitlements/inventory` sin token devuelve 401 `auth_required`; intento por API de inicializar Firebase Auth devolvio `CONFIGURATION_NOT_FOUND`, confirmando que falta el paso manual de Firebase Console. |
| Observaciones | Para cerrar login real en QA falta iniciar Firebase Authentication en consola y habilitar Google provider; la automatizacion por API no puede crear la config inicial si Auth no fue inicializado. |

### CHG-102

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Administracion como centro de configuracion inicial |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `contracts/api/admin-service.openapi.yaml`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Administracion, usuarios, roles, permisos, organizacion, configuracion base, Firebase Auth |
| Descripcion | Se rediseño Administracion como hub de configuracion con tarjetas clicables para Usuarios, Roles, Permisos, Organizacion y Configuracion base. Los paneles internos solo se abren al seleccionarlos. Usuarios ahora permite invitar/reactivar enviando correo de activacion, inactivar membresia y eliminar acceso; el backend agrega `DELETE /v1/users/{user_id}`, asegura identidad Firebase al invitar y elimina identidad Firebase por email al borrar. `session/context` activa membresias invitadas cuando el usuario entra con token Firebase valido. |
| Motivo | Convertir Administracion en el modulo de bienvenida/configuracion inicial del sistema, evitando usar espacio en metricas generales y cerrando el flujo operativo de alta, baja y reingreso por invitacion. |
| Impacto | El tenant puede administrar accesos de forma mas clara y preparar organizacion/catalogos base antes de operar otros modulos. La eliminacion de usuario queda protegida por permiso `admin.user.delete`, contrato OpenAPI e idempotencia. En un usuario sin otras membresias, ERClave elimina tambien la identidad global local; en modo Firebase elimina la identidad del proveedor. |
| Validacion | `node --check frontend/app.js`; `node --check frontend/api/admin.js`; `npm.cmd run validate:syntax`; `npm.cmd run validate:openapi`; `npm.cmd run validate`; `ERCLAVE_AUTH_MODE=demo python -m pytest services/admin-service/tests/test_admin_api.py`; `ERCLAVE_AUTH_MODE=demo python -m pytest`; seed local QA `scripts/seed_admin_mvp.py` y `scripts/seed_admin_qa_demo.py` aplicado correctamente con 94 permisos. |
| Observaciones | Los paneles Organizacion y Configuracion base quedan como estructura funcional inicial; sus formularios persistentes se implementaran cuando existan endpoints de tenant settings, razones sociales, sucursales y catalogos base. El seed de permisos y asignaciones del owner se reejecuto en la base QA local para incluir `admin.user.delete`. |

### CHG-103

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Organizacion configurable desde tenant settings |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260705_0003_admin_tenant_settings.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Administracion, Organizacion, Settings, corporativo, razones sociales, sucursales |
| Descripcion | Se implemento persistencia generica de configuraciones por tenant con `admin.tenant_settings` y endpoints `GET /v1/settings` y `PUT /v1/settings/{key}`. El frontend ahora guarda `organization.profile` con formulario editable de corporativo, altas de razones sociales y altas de sucursales. El contacto dejo de ser una seccion independiente y se movio como campos de corporativo y razon social. Se reordeno el hub de Administracion para mostrar primero Organizacion, despues Configuracion base y luego Usuarios, Roles y Permisos. |
| Motivo | Convertir Administracion en la bienvenida real de configuracion del tenant, permitiendo capturar datos corporativos y fiscales antes de operar los demas modulos. |
| Impacto | Los cambios de organizacion quedan persistidos por tenant, auditados por `admin.setting.upsert` y consumidos por el panel al refrescar. En modo mock se mantiene persistencia local para pruebas sin API. |
| Validacion | `node --check frontend/app.js`; `node --check frontend/api/admin.js`; `python -m py_compile` de admin-service y migracion; `ERCLAVE_AUTH_MODE=demo python -m pytest services/admin-service/tests/test_admin_api.py`. |
| Observaciones | Las razones sociales y sucursales se guardan inicialmente dentro de `organization.profile` en JSONB; cuando el modelo fiscal requiera relaciones transaccionales o integracion de facturacion se podran promover a tablas dedicadas. |

### CHG-104

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Agentes y alta de tenants alineados a estructura corporativa |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/scripts/seed_admin_qa_demo.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/models.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/services/admin-service/tests/test_qa_demo_seed.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/modelo_multitenant.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, Administracion, tenant settings, OpenAPI, seed QA, alta de tenants |
| Descripcion | Se actualizaron los agentes para tratar la estructura corporativa como dato central del tenant: corporativo, razones sociales, sucursales y contactos viven en `organization.profile` dentro de `admin.tenant_settings`. Se agrego modelo SQLAlchemy `TenantSetting`, se reforzo el seed QA para inicializar `organization.profile`, se documento el schema en OpenAPI y se agrego `POST /v1/tenants` como primer corte idempotente de provisioning que crea tenant e inicializa el perfil organizacional. |
| Motivo | Evitar que futuras iteraciones pasen por alto la estructura corporativa, la guarden en Firebase/localStorage/metadatos ambiguos o creen tenants sin configuracion base administrativa. |
| Impacto | Los agentes, contratos, docs, seeds, API y base quedan alineados para que cada tenant soporte configuracion organizacional desde su creacion. |
| Validacion | `python -m py_compile` de admin-service, modelos y seed; `npm.cmd run validate:openapi`; `npm.cmd run validate:agents`; `ERCLAVE_AUTH_MODE=demo python -m pytest`. |
| Observaciones | `POST /v1/tenants` conserva pendiente el endurecimiento de autenticacion service-to-service para `internal.provisioning.tenant.create` antes de Produccion. |

### CHG-105

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige base URL local de admin API |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, API QA local, configuracion runtime |
| Descripcion | Se corrigio `getApiBaseUrl()` para que en localhost respete `window.ERCLAVE_CONFIG.apiBaseUrl` y use `http://127.0.0.1:8010` como default local. Tambien se ignora el valor legado `http://127.0.0.1:8000` si quedo persistido en `localStorage`, evitando que el panel de Administracion consuma un admin-service viejo sin endpoints de settings. |
| Motivo | El boton API QA mostraba 404 porque el frontend apuntaba al puerto local anterior `8000`, donde `/v1/settings` no existe, aunque el admin-service vigente esta en `8010`. |
| Impacto | La Administracion local en modo API QA debe cargar contra el admin-service correcto y dejar de mostrar 404 por rutas nuevas. |
| Validacion | `node --check frontend/api/config.js`; smoke `GET http://127.0.0.1:8010/ready`; comparacion manual: `8010/v1/settings` responde 401 por auth, `8000/v1/settings` responde 404 por servicio viejo. |
| Observaciones | Si el navegador conserva modulo JS cacheado, hacer hard refresh. Hay un listener viejo en `8000` reportado por Windows, pero la app local ya no deberia usarlo con esta configuracion. |

### CHG-106

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Administracion sin tablero operativo |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Shell frontend, modulo Administracion, topbar, KPIs, notificaciones |
| Descripcion | Se agrego modo visual `admin-focus` cuando el modulo activo es Administracion. En ese modo se ocultan buscador global, boton Nuevo registro, KPIs superiores y panel lateral de notificaciones/resumen operativo. Tambien se evita renderizar notificaciones mientras Administracion esta activa. |
| Motivo | Administracion debe funcionar como centro de configuracion del sistema, no como tablero operativo de Produccion, Inventario, Ventas o Contabilidad. |
| Impacto | El modulo de Administracion queda enfocado en configuracion: Organizacion, Configuracion base, Usuarios, Roles y Permisos. Los elementos operativos permanecen disponibles en los demas modulos. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate`. |
| Observaciones | Cambio visual/frontend sin impacto en APIs ni base de datos. |

### CHG-107

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Barra global de usuario y sucursal |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Shell frontend, contexto de sesion, sucursal activa, usuario autenticado |
| Descripcion | Se agrego una barra superior discreta global visible en todas las pantallas y modulos. La barra muestra el usuario logueado o usuario de sesion local y la sucursal activa. Si hay mas de una sucursal configurada en `organization.profile`, muestra selector para cambiar la sucursal activa; si hay una sola o ninguna configurada, usa `Matriz` como valor por default. |
| Motivo | Dar contexto operativo constante al usuario sobre con que identidad y sucursal esta trabajando, preparando navegacion futura por sucursal y alcances por usuario. |
| Impacto | Todos los modulos comparten contexto visible de usuario/sucursal sin duplicar controles por pantalla. La seleccion de sucursal se persiste localmente en `erclave-active-branch-id`. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate`. |
| Observaciones | Por ahora el selector toma todas las sucursales configuradas en Organizacion; cuando existan alcances por usuario/sucursal en backend, debe filtrarse desde `session/context` o policy. |

### CHG-108

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Logout discreto en barra de contexto |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Shell frontend, barra global de contexto, sesion |
| Descripcion | Se movio el boton de cerrar sesion desde el topbar principal hacia la barra global de contexto de usuario/sucursal y se ajusto su estilo para que sea un control discreto tipo chip. |
| Motivo | Cerrar sesion pertenece al contexto de usuario y no debe competir visualmente con acciones operativas o de configuracion del modulo activo. |
| Impacto | La barra superior muestra usuario, sucursal y cierre de sesion en un mismo lugar, con menor peso visual. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate`. |
| Observaciones | Cambio visual/frontend sin impacto en APIs ni base de datos. |

### CHG-109

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Normaliza Admin API local a localhost |
| Autor | Codex |
| Archivos | `frontend/env.js`, `frontend/api/config.js`, `frontend/api/client.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, API QA local, fetch diagnostics |
| Descripcion | Se cambio la URL local de Admin API a `http://localhost:8010` cuando la app corre en `localhost`, normalizando overrides que usen `127.0.0.1`. Tambien se mejoro el mensaje de error de `fetch` para mostrar la URL base real y orientar sobre servicio local/cache. |
| Motivo | El navegador mostraba `Failed to fetch` al intentar conectar con la API QA local desde `localhost:4173`, aunque el backend respondia por curl. Alinear host de pagina y API reduce bloqueos/rarezas de navegador y facilita diagnostico. |
| Impacto | El boton API QA debe conectar contra `localhost:8010` y, si falla, mostrar un mensaje accionable en lugar de un error generico. |
| Validacion | `node --check frontend/api/config.js`; `node --check frontend/api/client.js`; `npm.cmd run validate`. |
| Observaciones | `localhost:8010/ready` y preflight CORS desde `localhost:4173` responden correctamente. |

### CHG-110

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Permite Private Network Access en Admin API local |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/main.py`, `frontend/api/client.js`, `TRAZABILIDAD.md` |
| Secciones | Backend Admin API, CORS, API QA local, fetch diagnostics |
| Descripcion | Se habilito `allow_private_network=True` en el CORS del Admin API y se agrego `DELETE` a los metodos permitidos para operaciones administrativas. En el cliente API se agrego fallback local entre `localhost` y `127.0.0.1` cuando `fetch` falla por red, conservando un mensaje diagnostico con URL base y fallback. |
| Motivo | Chrome enviaba un preflight con `Access-Control-Request-Private-Network: true` desde `localhost:4173` hacia `localhost:8010` y Starlette lo rechazaba con `400 Disallowed CORS private-network`, provocando `Failed to fetch` en API QA. |
| Impacto | La Administracion local puede consumir Admin API QA desde el navegador sin bloqueo PNA/CORS y mantiene compatibilidad si el host local se resuelve distinto. |
| Validacion | `python -m py_compile backend/services/admin-service/app/main.py`; `node --check frontend/api/client.js`; `curl -i http://localhost:8010/ready`; preflight `OPTIONS /v1/session/context` desde `Origin: http://localhost:4173` con `Access-Control-Request-Private-Network: true`; `npm.cmd run validate`. |
| Observaciones | Se reinicio el Admin API local en `127.0.0.1:8010`; si el navegador conserva cache de modulos, hacer hard refresh. |

### CHG-111

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Fuerza Admin API local por IPv4 |
| Autor | Codex |
| Archivos | `frontend/env.js`, `frontend/api/config.js`, `frontend/api/client.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, API QA local, diagnostico de red |
| Descripcion | Se cambio la URL base local del Admin API a `http://127.0.0.1:8010` y se dejo la normalizacion local para convertir overrides `localhost` a IPv4. Tambien se amplio el mensaje de error para indicar la URL fallback intentada. |
| Motivo | El navegador continuaba mostrando `Failed to fetch` contra `localhost:8010` aunque los preflights y endpoints respondian por curl. Usar IPv4 explicito evita diferencias de resolucion local entre `localhost`, `::1` y `127.0.0.1`. |
| Impacto | API QA local debe intentar primero `127.0.0.1:8010`, manteniendo fallback hacia `localhost:8010` solo si hiciera falta. |
| Validacion | `node --check frontend/api/config.js`; `node --check frontend/api/client.js`; `curl http://localhost:4173/env.js`; `curl http://localhost:4173/api/config.js`; `npm.cmd run validate`. |
| Observaciones | El Admin API local se dejo escuchando en `0.0.0.0:8010` para aceptar conexiones IPv4 locales. |

### CHG-112

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Serializa carga de Administracion y fija controles laterales |
| Autor | Codex |
| Archivos | `frontend/api/admin.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, API QA local, navegacion lateral |
| Descripcion | Se cambio la carga inicial del dashboard de Administracion de `Promise.all` a requests secuenciales para evitar fallos intermitentes de fetch contra el Admin API local cuando Chrome abre varias conexiones simultaneas. Tambien se hizo sticky el sidebar y su footer para que los controles de tema, idioma y acceso a Administracion permanezcan visibles en escritorio. |
| Motivo | En local el navegador seguia reportando `Failed to fetch` en `/v1/settings` aunque los endpoints y preflights respondian individualmente. Ademas, los controles inferiores del sidebar quedaban accesibles solo al llegar al final de paginas largas. |
| Impacto | API QA local carga de forma mas estable y la navegacion auxiliar del shell queda siempre a mano en pantallas de escritorio. |
| Validacion | `node --check frontend/api/admin.js`; `curl http://localhost:4173/api/admin.js`; `npm.cmd run validate`; smoke `GET http://127.0.0.1:8010/ready`. |
| Observaciones | El Admin API local quedo reiniciado y escuchando en `0.0.0.0:8010`. |

### CHG-113

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige consulta de settings por modulo |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/main.py`, `backend/services/admin-service/app/repositories.py`, `TRAZABILIDAD.md` |
| Secciones | Backend Admin API, settings, PostgreSQL, Administracion |
| Descripcion | Se separo la consulta de `AdminRepository.list_settings()` en dos variantes: una sin filtro de modulo y otra con `module_code = :module_code`. Tambien se dejo el registro de routers antes de middlewares en el bootstrap del Admin API. |
| Motivo | PostgreSQL/psycopg no podia inferir el tipo del parametro en `(:module_code is null or module_code = :module_code)`, causando `500 Internal Server Error` al cargar `/v1/settings?module_code=admin` desde API QA. |
| Impacto | El endpoint de settings de Administracion ya puede devolver `organization.profile` para el tenant QA sin romper la carga del panel. |
| Validacion | `python -m py_compile services/admin-service/app/repositories.py services/admin-service/app/main.py`; ejecucion directa de `repo.list_settings('ten_739ee59d765d5e14818674800d', module_code='admin')`; `curl http://127.0.0.1:8010/ready`; `npm.cmd run validate`. |
| Observaciones | El Admin API local se reinicio despues del cambio y quedo escuchando en `0.0.0.0:8010`. |

### CHG-114

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | APIs finas para razones sociales y sucursales |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `frontend/api/admin.js`, `frontend/app.js`, `contracts/api/admin-service.openapi.yaml`, `backend/services/admin-service/README.md`, `docs/arquitectura/modelo_multitenant.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `TRAZABILIDAD.md` |
| Secciones | Admin API, Administracion, organizacion, razones sociales, sucursales, OpenAPI |
| Descripcion | Se agregaron endpoints para crear, actualizar, activar e inactivar razones sociales y sucursales: `/v1/organization/legal-entities` y `/v1/organization/branches`. Por ahora persisten en `admin.tenant_settings` key `organization.profile`, pero cada accion tiene endpoint propio, idempotencia y auditoria. El frontend usa estas APIs para altas y cambios de estado cuando corre en API QA; en mock conserva persistencia local. |
| Motivo | Administracion necesitaba operaciones reales de alta/actualizacion/activacion/inactivacion para estructura corporativa sin reescribir manualmente todo el JSON desde la UI. |
| Impacto | El tenant QA puede administrar razones sociales y sucursales desde API QA con acciones auditables, manteniendo compatibilidad con el modelo JSONB inicial. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py`; `node --check frontend/api/admin.js`; `node --check frontend/app.js`; `pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate`. |
| Observaciones | Los endpoints usan `admin.setting.update` como permiso vigente. Si mas adelante se requieren permisos granulares, crear `admin.legal_entity.*` y `admin.branch.*` en seed/migracion de permisos. |

### CHG-115

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Actualiza agentes para endpoints finos de organizacion |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, Administracion, estructura corporativa |
| Descripcion | Se actualizaron los agentes para exigir que razones sociales y sucursales se creen, actualicen, activen e inactiven mediante los endpoints finos de `admin-service` (`/v1/organization/legal-entities` y `/v1/organization/branches`) mientras persistan en `organization.profile`. Tambien se agregaron preguntas de revision sobre idempotencia, auditoria, contrato OpenAPI, frontend y tests. |
| Motivo | Evitar que futuros cambios vuelvan a tratar razones sociales y sucursales como reemplazos opacos del JSON completo o como datos locales del frontend. |
| Impacto | Los agentes tecnicos y transversales ahora alinean sus revisiones con el modelo actual: `organization.profile` como almacenamiento inicial y endpoints finos como superficie de mutacion. |
| Validacion | `npm.cmd run validate:agents`; `npm.cmd run validate`. |
| Observaciones | No cambia runtime; es una actualizacion documental/operativa para guiar futuros cambios. |

### CHG-116

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Fortalece session/context con roles, limites y sucursales |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/services/admin-service/app/main.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/services/admin-service/README.md`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/modelo_multitenant.md`, `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Admin API, session/context, roles, entitlements, alcance de sucursales, shell frontend |
| Descripcion | Se extendio `GET /v1/session/context` para devolver roles activos detallados, `entitlement_limits` por modulo y `scope` con sucursales disponibles para la membresia. El alcance de sucursal se calcula desde `membership.metadata.scope.branch_ids` cuando exista y, si no esta configurado, permite todas las sucursales activas de `organization.profile`. El frontend ahora prioriza `session.scope.branches` para la barra global de sucursal y conserva fallback a la organizacion local/mock. |
| Motivo | Convertir `session/context` en la fuente real para usuario, permisos, modulos, limites y sucursal activa, evitando que el shell infiera alcance operativo desde datos locales o desde todo el perfil organizacional. |
| Impacto | La barra global de contexto queda preparada para usuarios con alcance por sucursal. Los servicios y microfrontends pueden consumir limites por modulo y roles explicitos sin recalcularlos en frontend. |
| Validacion | `python -m py_compile services/admin-service/app/main.py services/admin-service/app/schemas.py services/admin-service/app/repositories.py`; `node --check frontend/app.js`; `pytest services/admin-service/tests/test_admin_api.py`. |
| Observaciones | Se reemplazo el parametro directo `allow_private_network` de CORS por un middleware compatible que agrega `Access-Control-Allow-Private-Network` cuando Chrome lo solicita; esto conserva el soporte local sin depender de una version especifica de Starlette. |

### CHG-117

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Endpoint interno de onboarding tenant + owner |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/modelo_multitenant.md`, `TRAZABILIDAD.md` |
| Secciones | Provisioning, Admin API, tenants, owner inicial, organization.profile, modulos activos, Firebase Auth |
| Descripcion | Se agrego `POST /v1/provisioning/tenant-onboarding` como comando idempotente para crear o actualizar tenant por slug, inicializar `organization.profile`, crear o enlazar el usuario owner, crear rol `owner`, asignar permisos activos, crear membresia con alcance de sucursal, habilitar modulos solicitados y auditar la operacion. El request pide datos del tenant, `source`, owner inicial, perfil organizacional y modulos. |
| Motivo | Evitar altas manuales incompletas donde se cree tenant sin usuario owner, sin perfil organizacional, sin modulos o sin roles/permisos. |
| Impacto | El alta de cliente nuevo puede resolverse con un unico comando interno de provisioning y queda preparada para enlazarse a flujos comerciales/billing. El usuario owner queda autenticable en Firebase por email y autorizado en ERClave por membresia/rol. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py`; `pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate:openapi`. |
| Observaciones | En este corte el endpoint conserva pendiente autenticacion service-to-service fuerte antes de Produccion; `ensure_firebase_user` ocurre antes de la transaccion de base, por lo que errores posteriores podrian dejar una identidad Firebase sin membresia y deberan compensarse en la fase de provisioning robusto. |

### CHG-118

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Invitacion Firebase para owner inicial |
| Autor | Codex |
| Archivos | `backend/README.md`, `backend/shared/erclave_common/config.py`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `TRAZABILIDAD.md` |
| Secciones | Firebase Auth, provisioning, tenant onboarding, invitacion owner, configuracion |
| Descripcion | Se agrego soporte para preparar la invitacion de contrasena del owner inicial dentro de `POST /v1/provisioning/tenant-onboarding`. Si `ERCLAVE_FIREBASE_WEB_API_KEY` esta configurado, el backend llama Identity Toolkit para que Firebase envie el correo de recuperacion/activacion; si no existe esa key, genera un `reset_link` con Firebase Admin y lo devuelve en `data.invitation`. |
| Motivo | Completar el flujo de alta tenant + owner para que el usuario no solo exista en Firebase y ERClave, sino que tenga un camino de acceso inicial para definir contrasena. |
| Impacto | El onboarding ahora devuelve `invitation.provider`, `email`, `email_sent`, `delivery` y opcionalmente `reset_link`. QA/Prod pueden mandar correo real configurando `ERCLAVE_FIREBASE_WEB_API_KEY`; local/demo conserva respuesta `disabled`. |
| Validacion | `python -m py_compile services/admin-service/app/auth.py services/admin-service/app/api.py shared/erclave_common/config.py`; `pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate:openapi`. |
| Observaciones | El envio real usa las plantillas SMTP/configuracion de Firebase Authentication. Sigue pendiente un `notification-service` dedicado si se requiere branding, auditoria y reintentos avanzados de correo transaccional. |

### CHG-119

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Front Backoffice interno para alta de tenants |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/README.md`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/shared/erclave_common/config.py`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/modelo_multitenant.md`, `frontend/api/backoffice.js`, `frontend/backoffice/README.md`, `frontend/backoffice/app.js`, `frontend/backoffice/env.js`, `frontend/backoffice/index.html`, `frontend/backoffice/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Backoffice interno, Firebase Auth, provisioning, tenant onboarding, seguridad |
| Descripcion | Se creo `frontend/backoffice/` como front separado para administradores internos de EsLaClave. Incluye login con Firebase, formulario de alta de tenant, owner inicial, datos fiscales, sucursal inicial, modulos contratados y panel de resultado con invitacion. Se agrego `frontend/api/backoffice.js` como frontera API hacia `POST /v1/provisioning/tenant-onboarding`. El backend ahora protege ese endpoint en modo Firebase con allowlist `ERCLAVE_BACKOFFICE_ADMIN_EMAILS`. |
| Motivo | Crear tenants es una operacion de plataforma SaaS y no debe vivir dentro del modulo Administracion del cliente. El backoffice sera tambien la superficie futura para billing/provisioning y soporte interno. |
| Impacto | El equipo interno puede usar una interfaz separada para crear clientes sin entrar a un tenant existente. En QA/Prod el endpoint requiere token Firebase de un correo autorizado; en demo/local conserva flujo de desarrollo. |
| Validacion | `python -m py_compile services/admin-service/app/auth.py services/admin-service/app/api.py shared/erclave_common/config.py`; `pytest services/admin-service/tests/test_admin_api.py`; `node --check frontend/backoffice/app.js`; `node --check frontend/api/backoffice.js`. |
| Observaciones | Para uso local se sirve en `http://localhost:4173/backoffice/`. En Firebase mode configurar `ERCLAVE_BACKOFFICE_ADMIN_EMAILS` y, para correo real del owner, `ERCLAVE_FIREBASE_WEB_API_KEY`. |

### CHG-120

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Configuracion runtime online para Firebase Hosting |
| Autor | Codex |
| Archivos | `frontend/env.js`, `frontend/backoffice/env.js`, `frontend/api/config.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, backoffice, despliegue QA |
| Descripcion | Se actualizo la configuracion runtime del frontend para que Firebase Hosting apunte a `admin-service-qa` y `production-service-qa` en Cloud Run, conservando `localApiBaseUrl` para desarrollo local. `getApiBaseUrl()` ahora prioriza `localApiBaseUrl` cuando se ejecuta en `localhost` o `127.0.0.1`, evitando que la configuracion online rompa pruebas locales. |
| Motivo | Subir el front y backoffice en linea sin que el navegador intente llamar a `localhost` como API QA. |
| Impacto | `https://erclave.web.app/` y `/backoffice/` quedan listos para consumir los servicios QA publicados, mientras que el entorno local mantiene `http://127.0.0.1:8010` por defecto. |
| Validacion | `npm.cmd run validate`; `python -m pytest services/admin-service/tests/test_admin_api.py`; `node --check frontend/api/config.js`. |
| Observaciones | `productionApiBaseUrl` queda configurado para el servicio QA aunque el modulo de Produccion todavia conserva consumo mayormente local/mock en frontend. |

### CHG-121

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Ajusta copy de producto en login |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, autenticacion, experiencia de entrada |
| Descripcion | Se reemplazo el texto descriptivo del mecanismo de login por un mensaje de producto: ERClave como plataforma SaaS modular para centralizar procesos, usuarios, sucursales y modulos de negocio. |
| Motivo | La pantalla de acceso debe presentar brevemente que es ERClave y reforzar marca/eslogan, no explicar la implementacion de autenticacion. |
| Impacto | El panel izquierdo del login comunica valor de negocio antes del formulario de acceso. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate:traceability`. |
| Observaciones | No cambia comportamiento de autenticacion ni permisos. |

### CHG-122

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige preflight private-network de backoffice online |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/main.py`, `backend/services/admin-service/tests/test_admin_api.py`, `TRAZABILIDAD.md` |
| Secciones | Admin API, CORS, backoffice online |
| Descripcion | Se agrego una respuesta explicita para preflight CORS con `Access-Control-Request-Private-Network: true` cuando el origen pertenece a Firebase Hosting autorizado. Esto evita que `CORSMiddleware` rechace la solicitud con `400 Disallowed CORS private-network` antes de que el navegador ejecute `POST /v1/provisioning/tenant-onboarding`. |
| Motivo | Edge/Chrome puede enviar la cabecera private-network en preflight y bloquear el alta de tenant online con `Failed to fetch` aunque la API este disponible. |
| Impacto | El backoffice publicado en `https://erclave.web.app/backoffice/` puede completar el preflight y conectar con `admin-service-qa` para crear tenants. |
| Validacion | `python -m pytest services/admin-service/tests/test_admin_api.py`; `python -m py_compile services/admin-service/app/main.py`; `npm.cmd run validate:traceability`; validacion online del `OPTIONS` private-network posterior al deploy. |
| Observaciones | El cambio se acota a `admin-service`, que es la API consumida por el backoffice interno. |

### CHG-123

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige tipo ambiguo al crear membresia owner |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/repositories.py`, `TRAZABILIDAD.md` |
| Secciones | Admin API, provisioning, tenant onboarding, PostgreSQL |
| Descripcion | Se casteo explicitamente `:status` como `varchar` en el insert de `admin.memberships` usado por `POST /v1/provisioning/tenant-onboarding`. Esto evita el error `psycopg.errors.AmbiguousParameter: inconsistent types deduced for parameter` al calcular `activated_at` con `case when :status = 'active'`. |
| Motivo | El backoffice online ya pasaba CORS, pero el alta de tenant terminaba en `500 Internal Server Error` al crear la membresia inicial del owner. |
| Impacto | El onboarding puede crear la membresia owner con estado `invited` o `active` sin error de tipos en PostgreSQL. |
| Validacion | `python -m pytest services/admin-service/tests/test_admin_api.py`; `python -m py_compile services/admin-service/app/repositories.py`; `npm.cmd run validate:traceability`; deploy y health online de `admin-service-qa`. |
| Observaciones | El intento fallido pudo haber creado o actualizado la identidad Firebase del owner antes de la transaccion de base; el flujo es idempotente y el siguiente intento reutiliza/actualiza esa identidad. |

## Convencion para futuros cambios

Cuando hagamos una edicion nueva, se debe agregar una entrada adicional con el siguiente ID correlativo y dejar claro si el cambio fue funcional, documental, visual o tecnico.
