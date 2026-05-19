# Manual de Identidad y Lineamientos Generales de App

Este manual define una línea visual, funcional y de experiencia reutilizable para nuevas aplicaciones. Su objetivo es servir como guía base para próximos proyectos, sin depender de una industria, módulo o caso de negocio específico.

La identidad propone una experiencia moderna, clara y operativa: una app que se sienta confiable, compacta, fácil de usar y consistente en móvil.

## 1. Concepto General

La app debe sentirse sencilla, pulida y útil desde el primer uso. La interfaz debe priorizar claridad, acciones directas y lectura rápida de información, sin depender de explicaciones largas ni pantallas promocionales.

La identidad combina:

- Morados, violetas y magentas como señal principal de marca.
- Fondos y paneles limpios para mejorar legibilidad.
- Colores semánticos para comunicar estados, alertas y resultados.
- Componentes compactos, responsivos y fáciles de escanear.
- Soporte completo para modo claro, modo oscuro y tema del sistema.
- Soporte de idioma Español e Inglés.

## 2. Principios de Experiencia

- La app debe abrir directamente en una experiencia útil.
- La información importante debe verse con jerarquía clara.
- Las acciones principales deben estar siempre a pocos toques.
- Las pantallas deben funcionar bien en dispositivos pequeños.
- Los controles no deben ocupar tanto espacio que oculten el contenido principal.
- Los textos deben ser breves, directos y localizables.
- Cada módulo debe reutilizar patrones existentes antes de crear flujos nuevos.
- Si la app guarda información local, debe contemplar respaldo y restauración.

## 3. Paleta Principal

| Uso sugerido | Código HEX | RGB |
|---|---|---|
| Morado principal / marca | `#9B0FC9` | 155, 15, 201 |
| Morado intenso | `#6106A0` | 97, 6, 160 |
| Violeta oscuro | `#300C57` | 48, 12, 87 |
| Fondo premium oscuro | `#190F34` | 25, 15, 52 |
| Rosa neón | `#E32BCD` | 227, 43, 205 |
| Rosa brillante / acento | `#F557D3` | 245, 87, 211 |

## 4. Paleta Semántica

Estos colores pueden adaptarse al dominio de cada app, pero deben conservar su intención.

| Uso | Código HEX | Aplicación general |
|---|---|---|
| Éxito / positivo | `#059669` | Confirmaciones, avances, estados correctos |
| Error / negativo | `#DC2626` | Errores, eliminación, estados críticos |
| Advertencia | `#D97706` | Validaciones, atención requerida, avisos suaves |
| Información | `#2563EB` | Ayuda, datos informativos, referencias |
| Completado | `#0F766E` | Procesos finalizados o aprobados |
| Programado / activo | `#6106A0` | Selecciones, recordatorios, elementos activos |

## 5. Neutros y Superficies

### Modo claro

| Uso | Código HEX |
|---|---|
| Blanco limpio | `#FFFFFF` |
| Panel tintado | `#FFF7FF` |
| Fondo de campo | `#F8E8FF` |
| Panel violeta suave | `#F3D8FF` |
| Morado sutil | `#E9C6FF` |
| Borde morado | `#D58AF4` |
| Texto principal | `#1F1233` |
| Texto secundario | `#6B7280` |
| Línea / borde neutro | `#E5E5E5` |

### Modo oscuro

| Uso | Código HEX |
|---|---|
| Fondo de app | `#080A16` |
| Panel principal | `#141827` |
| Panel suave | `#1C2032` |
| Campo / input | `#24283A` |
| Línea / borde | `#34384A` |
| Texto principal | `#F7F3FF` |
| Texto secundario | `#B8AEC8` |

## 6. Gradientes Oficiales

### Gradiente de marca

```css
linear-gradient(135deg, #300C57, #9B0FC9, #F557D3)
```

Uso:

- Encabezados principales.
- Barras superiores.
- Elementos de marca.
- Botones o contenedores destacados cuando se requiere énfasis.

### Fondo de app

```css
linear-gradient(135deg, #190F34, #300C57, #6106A0, #9B0FC9)
```

Uso:

- Fondo general.
- Primer nivel visual detrás de paneles.
- Pantallas principales con estética de marca.

### Panel claro

```css
linear-gradient(135deg, #FFFFFF, #FFF7FF, #FFECFB)
```

Uso:

- Contenedores grandes.
- Superficie principal donde se alojan tabs, cards y listas.

### Panel oscuro

```css
linear-gradient(135deg, #141827, #181B2F, #241737)
```

Uso:

- Contenedores grandes en tema oscuro.
- Pantallas operativas con alto contraste.

## 7. Distribución de Color

### 70% Morado / violeta

- Marca.
- Encabezados.
- Botones principales.
- Selección activa.
- Elementos de navegación.

### 20% Blanco / negro / neutros

- Texto principal.
- Fondos de panel.
- Inputs.
- Listas.
- Contenido operativo.

### 10% Rosa / semánticos

- Acentos.
- Indicadores.
- Alertas suaves.
- Estados positivos o negativos.
- Señales de actividad.

## 8. Perfil y Configuración

Toda app que use esta línea debe contemplar una configuración base para personalización.

Debe permitir configurar:

- Nombre del usuario.
- Idioma.
- Apariencia.

### Nombre

- Nombre inicial recomendado: `Usuario`.
- En actualizaciones se debe conservar el nombre ya guardado.
- El nombre debe mostrarse de forma compacta cuando aparezca en encabezados.

### Idioma

Idiomas contemplados:

- `Español`
- `English`

Reglas:

- Todo texto visible debe venir de una capa de textos localizables.
- No mezclar textos fijos en español dentro de componentes reutilizables.
- Formularios, botones, avisos, exportaciones y notificaciones deben respetar el idioma activo.
- El idioma por defecto debe ser Español, salvo que el proyecto indique otra prioridad.

### Apariencia

Modos contemplados:

- Sistema.
- Claro.
- Oscuro.

Reglas:

- `Sistema` respeta la configuración del dispositivo.
- `Claro` fuerza paleta clara.
- `Oscuro` fuerza paleta oscura.
- Todos los componentes deben obtener colores desde helpers, temas o tokens.
- Evitar colores sueltos dentro de widgets o componentes.
- Inputs, paneles, bordes, textos secundarios y fondos deben adaptarse al tema.

## 9. Arquitectura Visual de Pantallas

### Estructura base

Una pantalla principal debe usar:

- Fondo con gradiente de app o superficie del tema.
- Panel principal redondeado con borde suave cuando la composición lo requiera.
- Encabezado compacto con perfil, contexto o selector principal.
- Tabs, navegación primaria o filtros dentro del área de trabajo.
- Contenido con scroll interno cuando haga falta.
- Botón flotante solo si la acción principal lo justifica.

### Encabezado

El encabezado debe ser compacto y funcional:

- Perfil o contexto a la izquierda.
- Acción, periodo, filtro o selector a la derecha.
- Texto con máximo 1 línea cuando el espacio sea pequeño.
- No repetir el nombre de la sección si una tab, título o navegación ya lo indica.

### Tabs

Las tabs deben:

- Usar contenedor suave (`field` / `darkField`) o equivalente del tema.
- Mostrar estado activo con violeta oscuro o color de marca.
- Ser legibles en pantallas pequeñas.
- Truncar texto si no cabe.
- Evitar alturas excesivas que oculten contenido.

## 10. Componentes

### Botón primario

Uso:

- Guardar.
- Registrar.
- Confirmar.
- Continuar.
- Crear.

Estilo:

- Fondo `#9B0FC9`.
- Texto blanco.
- Peso tipográfico alto.
- Radio recomendado: 12 a 16 px.
- Altura cómoda: 44 a 52 px.

### Botón secundario

Uso:

- Cancelar.
- Cambiar modo.
- Ver detalle.
- Acciones no destructivas.

Estilo:

- Fondo transparente o superficie de campo.
- Borde suave.
- Texto morado o texto principal.

### Botón semántico

Uso:

- Confirmar: verde.
- Eliminar o error: rojo.
- Advertir: naranja.
- Informar: azul.
- Activar o seleccionar: morado.

Regla:

- El color debe comunicar el tipo de acción o estado, no solo decorar.

### Chips / indicadores

Uso:

- Filtros.
- Estados.
- Etiquetas cortas.
- Cantidades pequeñas.
- Señales de actividad.

Reglas:

- Deben ser compactos.
- No deben competir con botones principales.
- Los indicadores visuales deben ser discretos y consistentes.
- Una burbuja con número puede indicar elementos existentes.

### Cards

Uso:

- Resúmenes.
- Acciones de módulo.
- Métricas.
- Elementos repetidos de listas.
- Vista previa de contenido.

Estilo:

- Radio recomendado: 14 a 18 px.
- Borde suave con baja opacidad.
- Sombra ligera si ayuda a separar capas.
- No anidar cards innecesariamente.
- Evitar cards demasiado altas en móvil.

### Inputs

Estilo:

- Fondo de campo en claro y oscuro.
- Borde alineado al tema.
- Radio 12 a 14 px.
- Labels claros y breves.
- Validación con mensajes localizables.

### Bottom sheets

Uso:

- Formularios de registro.
- Edición rápida.
- Selección de opciones.
- Confirmaciones contextuales.

Reglas:

- Fondo alineado al panel del tema.
- Esquinas superiores redondeadas.
- Altura máxima controlada.
- Scroll si el contenido excede pantalla.
- Respetar teclado con padding inferior.

## 11. Navegación Funcional

La navegación debe adaptarse al producto, pero mantener estos principios:

- Priorizar entre 3 y 5 secciones principales.
- Usar nombres cortos en tabs y navegación.
- Reutilizar pantallas existentes antes de crear pantallas nuevas.
- Si una sección funciona como acceso contextual, debe enviar parámetros claros.
- No duplicar lógica de registro, edición o consulta si ya existe un flujo principal.
- Mantener caminos cortos para crear, consultar, editar y volver.

## 12. Módulos y Listas

Cuando una app tenga módulos con registros, tareas, notas, eventos o elementos similares:

- Mostrar el dato principal primero.
- Usar subtítulos para contexto secundario.
- Usar indicadores pequeños para actividad o estado.
- Permitir abrir detalle sin perder el contexto.
- Mantener acciones rápidas compactas.
- Evitar repetir títulos que ya están presentes en tabs o encabezados.

## 13. Calendario o Agenda Opcional

Si el proyecto incluye calendario, agenda o planeación:

- Mostrar indicadores discretos para días o periodos con actividad.
- Evitar controles grandes que oculten el calendario en móvil.
- Usar vista mensual o anual solo si aporta valor al caso de uso.
- Al seleccionar un periodo, mostrar detalle contextual.
- Las acciones rápidas deben reutilizar flujos existentes cuando sea posible.
- Eventos, notas o tareas deben tener título o nombre visible en listas.
- Los checklists deben permitir marcar cada tarea de forma individual.

## 14. Notificaciones

Si el proyecto incluye notificaciones:

- Pedir permisos cuando corresponda.
- Respetar el idioma activo.
- Usar título y cuerpo breves.
- Usar el ícono de launcher de la app.
- Programar horarios razonables según el caso de uso.
- Permitir activar o desactivar notificaciones cuando aplique.

## 15. Respaldo, Datos y Privacidad

Si la app guarda datos locales:

- Debe definir cómo se respaldan.
- Debe definir cómo se restauran.
- Debe avisar si una contraseña o clave no puede recuperarse.
- Debe incluir nuevos módulos en el respaldo.
- Debe evitar subir información sensible a servidores sin explicación clara.

Si la app requiere backend:

- Debe explicar al usuario qué datos se sincronizan.
- Debe manejar errores de conexión.
- Debe conservar una experiencia clara cuando no haya internet, si el proyecto lo permite.

## 16. Iconografía

Usar iconos consistentes con Material / Flutter o la librería visual del proyecto.

Ejemplos generales:

- Perfil: `person`, `settings`.
- Crear: `add`, `add_circle`.
- Guardar: `save`, `check`.
- Editar: `edit`.
- Eliminar: `delete`.
- Buscar: `search`.
- Filtro: `filter_list`.
- Calendario: `calendar_today`, `event`.
- Notas: `sticky_note_2`, `notes`.
- Checklist: `checklist`.
- Respaldo: `backup`, `upload`, `download`.
- Notificación: `notifications`.

Regla:

- Preferir iconos reconocibles sobre texto largo.
- Acompañar iconos con texto cuando la acción no sea obvia.

## 17. Tipografía y Texto

Lineamientos:

- Usar pesos altos para títulos, métricas y acciones.
- Usar texto secundario para ayudas y subtítulos.
- Evitar párrafos largos dentro de la app.
- En cards y botones, máximo 1 o 2 líneas.
- Usar truncado con elipsis cuando el espacio sea limitado.
- No usar tamaños enormes dentro de paneles compactos.

Tono:

- Claro.
- Directo.
- Cercano.
- No técnico.
- Enfocado en la acción.

## 18. Accesibilidad Visual

La app debe cuidar:

- Contraste en claro y oscuro.
- Texto legible.
- Evitar solapamientos.
- Tamaños responsivos.
- Componentes con altura estable.
- Botones tocables cómodos.
- Indicadores visuales discretos pero visibles.

## 19. Recomendaciones de Uso

### Sí usar

- Gradientes elegantes y controlados.
- Contraste alto en botones principales.
- Morado como identificador principal.
- Colores semánticos para estados y acciones.
- Componentes compactos en móvil.
- Textos localizables.
- Paneles limpios y bordes suaves.
- Indicadores pequeños para actividad.

### Evitar

- Saturar toda la interfaz con rosa.
- Usar demasiados tonos sin jerarquía.
- Fondos claros con textos magenta de baja legibilidad.
- Mezclar colores ajenos a la gama principal sin criterio.
- Repetir títulos que ya aparecen en tabs o encabezados.
- Hacer controles grandes que empujen el contenido clave fuera de pantalla.
- Crear formularios duplicados si ya existe un flujo reutilizable.
- Usar textos fijos sin soporte de idioma.
- Incluir reglas de negocio específicas dentro del manual general.

## 20. Checklist para Nuevos Proyectos

Antes de cerrar una nueva app con esta identidad, validar:

- Tiene perfil con nombre, idioma y apariencia si aplica al producto.
- Soporta Español e Inglés.
- Soporta tema claro, oscuro y sistema.
- Usa tokens de color, no colores sueltos.
- Tiene botones primarios, secundarios y semánticos consistentes.
- Las cards y listas son responsivas.
- Los formularios usan bottom sheets o pantallas compactas cuando conviene.
- Las notificaciones respetan idioma y configuración del usuario.
- El respaldo incluye todos los datos locales si la app guarda información.
- La navegación principal es corta y clara.
- Los módulos nuevos no duplican lógica existente.
- En móvil se ve contenido útil en la primera pantalla.
- El manual específico del producto documenta reglas de negocio aparte.
