# Estandar responsive transversal de ERClave

## Objetivo

Toda pantalla debe conservar lectura, operacion y jerarquia cuando convivan sidebar, guia de flujo, panel principal, alertas, filtros o contenido localizado. Una pantalla no se considera responsive solo porque no desborde el viewport.

Este estandar aplica a componentes nuevos y a componentes existentes que sean modificados.

## Regla de contenedor

Los componentes que viven dentro de paneles deben responder al ancho que realmente reciben mediante **CSS Container Queries**. Los media queries de viewport se reservan para el shell global: navegacion principal, sidebar, overlays y distribucion general de la aplicacion.

Cada region reutilizable debe:

1. declarar un contenedor con nombre cuando pueda coexistir con columnas laterales;
2. definir estados amplio, intermedio y compacto a partir de su propio ancho;
3. funcionar tambien cuando se inserta en un modal, drawer o panel dividido;
4. evitar breakpoints ligados a un dispositivo especifico.

Breakpoints de referencia para contenedores, ajustables con evidencia visual:

| Estado | Ancho disponible | Comportamiento esperado |
|---|---:|---|
| Amplio | mas de 1,100 px | Tabla completa, acciones en linea y filtros distribuidos. |
| Intermedio | 821-1,100 px | Menos columnas simultaneas, acciones flexibles y paneles secundarios reubicados. |
| Compacto | 561-820 px | Tabla en tarjetas o scroll controlado, formularios de una o dos columnas. |
| Estrecho | hasta 560 px | Una columna, acciones apiladas y prioridad al contenido esencial. |

No se deben copiar estos valores mecanicamente si el contenido se rompe antes. El breakpoint correcto es donde el componente deja de ser legible u operable.

## Tablas y colecciones

Cada tabla debe elegir y documentar una estrategia:

- **Tarjetas:** preferida para consultas operativas cuando cada fila conserva una identidad clara. Cada valor muestra su etiqueta; no depende del encabezado oculto.
- **Scroll horizontal:** permitido para matrices, comparaciones o datos cuya relacion entre columnas se perderia al apilar. Queda contenido dentro de la tabla, muestra indicio de desplazamiento y mantiene accesibles columnas o acciones esenciales.
- **Vista reducida:** permitida cuando columnas secundarias pueden moverse a detalle expandible sin ocultar datos necesarios para decidir.

Nunca se comprimen columnas hasta cortar identificadores, cantidades o acciones. El modo tarjeta preserva orden semantico, estados, unidades, acciones, foco de teclado y asociaciones accesibles. Vacio, error y carga se adaptan con la misma estrategia que las filas reales.

## Textos largos y localizacion

- Titulos, breadcrumbs, chips, alertas, botones y etiquetas admiten wrap controlado.
- No se usan alturas fijas para regiones con texto traducible.
- Identificadores, correos, URLs y correlation IDs usan `overflow-wrap: anywhere` o una presentacion equivalente que permita copiar el valor completo.
- La elipsis solo se acepta si existe una forma accesible de consultar el texto completo.
- Se prueba espanol, ingles y contenido extremo; no basta lorem ipsum corto.
- Botones con texto largo pueden crecer o apilarse, pero su objetivo tactil no se reduce.

## Formularios y acciones

- Los formularios pasan progresivamente de varias columnas a una columna segun el contenedor.
- Label, ayuda, control y error permanecen juntos; un error no desplaza ni se superpone sobre otro campo.
- Inputs, selects, textareas, lookups y calendarios ocupan el ancho disponible sin desbordar.
- Acciones primarias y destructivas no cambian de significado ni de orden accidentalmente al apilarse.
- Modales y drawers caben en alto y ancho, con scroll interno predecible y cierre siempre alcanzable.
- Targets tactiles miden al menos 44 x 44 CSS px cuando el control no tiene una superficie mayor equivalente.

## Flujos, filtros y alertas

- La guia descriptiva estandar conserva un riel vertical a la izquierda y se comprime mediante su control colapsable. No se convierte globalmente en barra horizontal ni se cambia su jerarquia por una regla transversal.
- Solo en ancho estrecho, cuando dos columnas ya no sean operables, el riel puede entrar al flujo de una columna. Una excepcion anterior a ese punto debe usar una clase propia de pantalla, documentar el motivo y probar que no afecta otros modulos.
- Las guias de flujo no restan al area operativa el ancho minimo necesario. En contenedores intermedios se comprimen conservando el riel; en estrechos se presentan antes o despues del contenido, nunca encima.
- El estado colapsado sigue siendo comprensible, enfocable y accionable.
- Barras de filtros usan wrap; los controles prioritarios aparecen primero y los secundarios pueden pasar a `Mas filtros`.
- Chips de filtros activos se envuelven, se retiran individualmente y no empujan acciones fuera del panel.
- Alertas no cubren formularios, tablas, menus ni botones. En ancho intermedio pueden reubicarse en el flujo; en estrecho ocupan una columna.
- Banners y errores conservan titulo, mensaje, accion y cierre sin truncamiento destructivo.

## Jerarquia del shell y tarjetas operativas

- En escritorio, identidad de sesion, sucursal, salida, busqueda y accion contextual comparten una sola franja superior cuando el contenido cabe. En ancho intermedio se compactan etiquetas y controles antes de crear una fila adicional; en estrecho se apilan sin superposicion.
- La cabecera previa a un hero de submodulo funciona como breadcrumb y retorno, no repite el titulo principal. El hero conserva una sola identidad, descripcion breve y, cuando aplica, la accion contextual.
- Los indicadores transversales viven inmediatamente antes de **Alertas operativas** y responden al ancho real del panel lateral: dos columnas en el aside habitual, cuatro cuando el panel ocupa una fila amplia y una en estrecho.
- El shell no repite una identidad generica encima del titulo activo. Cada pantalla muestra una sola identidad principal y evita badges tecnicos de API, base de datos, mock, QA o persistencia que no cambien una decision del usuario.
- Una tarjeta con identidad, responsable, estados, partidas y acciones no puede reutilizar un `flex` horizontal generico con todos esos elementos como hijos directos. Debe declarar layout operativo propio, agrupar contenido semanticamente y apilarse antes de comprimir palabras o controles.
- Un modal es un contenedor independiente del panel que lo abre. Sus formularios, validaciones y partidas declaran tambien reglas bajo el contenedor del modal; una regla de `module-panel` nunca se considera suficiente para overlays.

## Viewports y combinaciones minimas

Las container queries se validan redimensionando el panel, no solo la ventana. Ademas, QA prueba como minimo:

- 1,440 x 900 y 1,280 x 720 con sidebar y paneles laterales abiertos;
- 1,024 x 768;
- 768 x 1,024;
- 390 x 844;
- 320 x 568;
- zoom del navegador a 200% en escritorio;
- orientacion horizontal movil cuando exista una operacion tabular relevante.

En cada tamano se repite con guia abierta/cerrada, alertas presentes/ausentes, resultados/vacio/error/carga y textos ES/EN.

## Criterio de terminado

No existe scroll horizontal de pagina, superposicion, texto esencial cortado, foco invisible, control inaccesible, accion fuera de pantalla ni cambio de significado entre layouts. Si una tabla usa scroll horizontal, solo su region puede desplazarse.

La evidencia minima incluye capturas de estados amplio, intermedio y estrecho, navegacion por teclado y navegador probado. Una excepcion documenta motivo, alcance, alternativa accesible y deuda de seguimiento.
