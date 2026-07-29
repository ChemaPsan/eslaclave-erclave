# Guía de pruebas QA del MVP de ERClave

**Ambiente:** QA
**Aplicación cliente:** `https://erclave.web.app`
**Backoffice interno:** `https://erclave.web.app/backoffice/`
**Última actualización:** 2026-07-26

## 1. Objetivo

Esta guía ayuda a una persona de QA a comprobar lo que ERClave puede hacer hoy, entender por qué cada flujo importa para el negocio y evitar confundir una maqueta con una integración terminada.

ERClave es un ERP SaaS modular y multitenant. Cada empresa cliente es un tenant aislado. Firebase comprueba la identidad del usuario; ERClave decide a qué tenant pertenece, qué módulos tiene contratados y qué permisos puede ejercer.

## 2. Cómo interpretar el alcance

Cada caso usa una de estas etiquetas:

| Etiqueta | Significado para QA |
|---|---|
| **REAL QA** | Usa API y base PostgreSQL de QA. Debe persistir entre sesiones, navegadores y dispositivos. |
| **PROTOTIPO LOCAL** | Funciona principalmente en `localStorage`/datos simulados. Evaluar UX, reglas visibles y cálculos; no certificar persistencia multiusuario. |
| **NO DISPONIBLE** | Funcionalidad futura o deshabilitada. Verificar sólo que la interfaz no la presente como terminada. |

### Mapa actual

| Área | Estado | Alcance comprobable |
|---|---|---|
| Autenticación y sesión | REAL QA | Login Firebase, invitación, recuperación, tenant, permisos y módulos contratados. |
| Backoffice | REAL QA | Alta, búsqueda, suspensión, reactivación y eliminación de tenants; uso estimado. |
| Administración | REAL QA | Organización, razones sociales, sucursales, usuarios, roles y permisos. |
| Producción | HÍBRIDO | Productos/servicios y recetas/versiones son reales. Órdenes, recursos operativos, áreas y maquinaria siguen locales. |
| Almacenes | PROTOTIPO LOCAL | UX de almacenes, artículos, movimientos, existencias y kardex. |
| Ventas | PROTOTIPO LOCAL | UX de clientes, cotizaciones, pedidos, ajustes, entregas y PDF. |
| Compras, Gastos, Costos, Reportes y Contabilidad | NO DISPONIBLE/DEMO | Navegación y comunicación visual; no certificar operación ni cifras. |

## 3. Prioridades

- **P0:** bloquea onboarding, login, aislamiento, acceso contratado o puede exponer/perder datos.
- **P1:** rompe una función principal del módulo o una regla de negocio importante.
- **P2:** problema visual, responsive, texto, filtro o experiencia con alternativa disponible.

Estados de ejecución: `Pasa`, `Falla`, `Bloqueado`, `No aplica`.

## 4. Preparación

No guardar contraseñas, tokens ni ligas vigentes de invitación en Git, documentos o tickets.

### Tenant autorizado para desarrollo y datos dummy

En desarrollo local y pruebas con información ficticia se debe trabajar exclusivamente con:

| Campo | Valor autorizado |
|---|---|
| Nombre | `ERClave Demo QA` |
| Tenant ID | `ten_739ee59d765d5e14818674800d` |
| Sucursal de referencia | `Matriz · ERClave Demo QA` |

Antes de capturar, modificar, eliminar, importar o generar datos de prueba, confirmar en la sesión y en la petición que el tenant activo coincide con ese ID. Si aparece cualquier otro tenant, detener la prueba. Los tenants creados para el equipo de QA no deben recibir datos dummy, seeds ni mutaciones de desarrollo salvo autorización explícita.

Preparar:

- `<EMAIL_BACKOFFICE_ADMIN>` y su contraseña.
- Dos tenants desechables: `<TENANT_A>` y `<TENANT_B>`.
- Owners con buzones accesibles: `<OWNER_A>` y `<OWNER_B>`.
- Un usuario invitado desechable.
- Una razón social y una sucursal ficticias.
- Datos de producto, recurso y receta que no sean información sensible.
- Chrome/Edge de escritorio y Safari iPhone; Android Chrome cuando esté disponible.
- Commit/build probado y fecha de ejecución.

Usar ventanas privadas o perfiles separados para probar dos tenants. No eliminar el tenant principal ni usuarios reales.

## 5. Smoke diario (15–20 minutos)

Ejecutar al inicio de una jornada de QA o después de un despliegue:

1. Abrir la aplicación y autenticarse como owner.
2. Confirmar nombre del tenant y módulos contratados.
3. Abrir Administración y cargar Organización, Usuarios y Roles.
4. Abrir Producción > Productos y servicios.
5. Abrir Producción > Recetas y consultar una receta.
6. Refrescar el navegador y comprobar que la sesión/pantalla no quedan rotas.
7. Cerrar sesión y confirmar que no se puede regresar a datos protegidos con “Atrás”.

**Por qué:** detecta rápidamente si identidad, autorización, Admin API, Production API o frontend dejaron de comunicarse.

## 6. Backoffice, onboarding y acceso

### QA-BO-01 — Alta e invitación de tenant

**Prioridad/tipo:** P0 · REAL QA
**Contexto:** convierte un cliente vendido en un espacio aislado y operable.

**Pasos**

1. Entrar a `/backoffice/` con `<EMAIL_BACKOFFICE_ADMIN>`.
2. Crear un tenant con nombre y slug únicos.
3. Capturar owner, razón social inicial y módulos Administración y Producción.
4. Enviar el alta una sola vez.
5. Revisar el resultado y el buzón del owner.

**Esperado**

- Tenant activo y owner invitado.
- Correo recibido una sola vez.
- La liga es HTTPS y nunca contiene `localhost`.
- Repetir accidentalmente la acción no duplica el tenant.

**Por qué se prueba:** un alta incompleta impide comenzar; una duplicada afecta cobro, identidad y aislamiento.

### QA-AUTH-01 — Activación del owner

**Prioridad/tipo:** P0 · REAL QA

**Pasos**

1. Abrir una invitación nueva en ventana privada o Safari móvil.
2. Definir una contraseña válida.
3. Confirmar que la redirección termina en `https://erclave.web.app`.
4. Iniciar sesión.

**Esperado**

- No aparece “Safari no pudo conectarse al servidor”.
- El usuario entra al tenant recién creado.
- Administración está disponible y no aparecen datos demo de otra empresa.

**Por qué se prueba:** es el primer momento de verdad del cliente.

> Las ligas emitidas antes de CHG-139 conservan la redirección antigua; usar siempre un correo nuevo.

### QA-AUTH-02 — Recuperación de contraseña

**Prioridad/tipo:** P0 · REAL QA

1. Solicitar recuperación para un usuario existente.
2. Abrir el correo nuevo y establecer otra contraseña.
3. Entrar con la contraseña nueva.
4. Confirmar que la anterior ya no funciona.

**Esperado:** recuperación completa, redirección pública y sesión del tenant correcto.

**Por qué:** evita que el cliente dependa de soporte para recuperar acceso.

### QA-BO-02 — Backoffice restringido

**Prioridad/tipo:** P0 · REAL QA

1. Entrar como owner de un cliente.
2. Abrir `/backoffice/`.

**Esperado:** acceso restringido; no se muestran formularios ni datos internos.

**Por qué:** ser owner de un tenant no convierte al usuario en administrador de EsLaClave.

### QA-SEC-01 — Suspensión y reactivación

**Prioridad/tipo:** P0 · REAL QA

1. Con un tenant desechable, iniciar sesión como owner.
2. Desde Backoffice, suspender el tenant.
3. Refrescar la sesión del owner e intentar operar.
4. Reactivar desde Backoffice y volver a ingresar.

**Esperado:** suspendido no puede operar; reactivado recupera el acceso autorizado.

**Por qué:** permite controlar el servicio sin borrar información.

### QA-SEC-02 — Aislamiento entre tenants

**Prioridad/tipo:** P0 · REAL QA

1. Abrir `<TENANT_A>` y `<TENANT_B>` en perfiles separados.
2. Crear una razón social y un producto con nombres claramente distintos en cada tenant.
3. Refrescar y consultar Organización, Usuarios, Productos y Recetas.

**Esperado:** ningún tenant ve, busca ni modifica datos del otro.

**Por qué:** una fuga entre clientes es un incidente crítico de seguridad SaaS.

### QA-BO-03 — Ciclo de vida del tenant

**Prioridad/tipo:** P1 · REAL QA

1. Buscar por nombre, slug y razón social.
2. Revisar estado y módulos.
3. Probar suspensión/reactivación.
4. Probar eliminación únicamente con un tenant desechable y autorización del responsable.

**Esperado:** búsquedas correctas; estados coherentes; eliminación irreversible claramente comunicada.

**Por qué:** el equipo interno necesita operar clientes sin afectar al tenant equivocado.

## 7. Administración

**Contexto del módulo:** configura la estructura legal y operativa del cliente y controla quién puede entrar y qué puede hacer. Es transversal a todos los módulos.

### QA-ADM-01 — Perfil corporativo

**Prioridad/tipo:** P0 · REAL QA

1. Administración > Organización.
2. Completar o editar los datos corporativos.
3. Guardar, refrescar y volver a iniciar sesión.

**Esperado:** datos persistentes sólo en el tenant actual; validaciones claras en campos obligatorios.

**Por qué:** es la identidad administrativa de la empresa.

### QA-ADM-02 — Razón social

**Prioridad/tipo:** P1 · REAL QA

1. Crear una razón social con sus datos obligatorios.
2. Editarla y refrescar.
3. Inactivarla y reactivarla.

**Esperado:** mantiene un ID estable, persiste y cambia de estado sin borrado accidental.

**Por qué:** una empresa puede operar con varias entidades fiscales y conservar historia.

### QA-ADM-03 — Sucursal

**Prioridad/tipo:** P1 · REAL QA

1. Crear una sucursal ligada a la razón social de prueba.
2. Editar sus datos.
3. Inactivar y reactivar.

**Esperado:** relación y estados persistentes; no permite asociarla a otro tenant.

**Por qué:** sucursales determinan alcance físico y operativo.

### QA-ADM-04 — Invitar y activar usuario

**Prioridad/tipo:** P0 · REAL QA

1. Administración > Usuarios y accesos.
2. Invitar un correo nuevo y asignarle un rol.
3. Completar la invitación desde otro perfil.
4. Entrar y revisar las acciones disponibles.

**Esperado:** sólo ve su tenant y permisos; la membresía pasa de invitada a activa.

**Por qué:** permite delegar operación con mínimo privilegio.

### QA-ADM-05 — Deshabilitar usuario

**Prioridad/tipo:** P0 · REAL QA

1. Deshabilitar el usuario de prueba.
2. Refrescar su sesión e intentar entrar.
3. Reactivarlo si la interfaz lo permite.

**Esperado:** acceso bloqueado al deshabilitar; sin afectar a otros usuarios.

**Por qué:** el offboarding rápido protege información del cliente.

### QA-ADM-06 — Roles y permisos

**Prioridad/tipo:** P0 · REAL QA

1. Crear un rol de prueba.
2. Asignar permiso de lectura, pero no aprobación de recetas.
3. Asignarlo al usuario desechable.
4. Consultar una receta e intentar aprobarla.

**Esperado:** lectura permitida; aprobación ocultada o rechazada por backend.

**Por qué:** la UI ayuda, pero el backend debe impedir acciones sin permiso.

## 8. Producción

**Contexto del módulo:** define qué producto o servicio ofrece la empresa y estandariza recursos y etapas mediante recetas versionadas. Hoy son reales únicamente Productos y servicios y Recetas.

### QA-PROD-01 — Crear producto o servicio

**Prioridad/tipo:** P0 · REAL QA

1. Producción > Productos y servicios.
2. Crear un registro con código/SKU único, nombre, tipo y unidad.
3. Guardar, refrescar y abrir en otro navegador.
4. Editar e inactivar/restaurar si está disponible.

**Esperado:** persiste en API/QA, conserva ID y muestra estados correctos.

**Por qué:** el catálogo es la base de recetas y futuras ventas/órdenes.

### QA-PROD-02 — Validaciones del catálogo

**Prioridad/tipo:** P1 · REAL QA

1. Omitir campos obligatorios.
2. Probar espacios, longitudes límite y un SKU repetido.
3. Corregir el formulario y guardar.

**Esperado:** mensajes comprensibles, sin registros incompletos o duplicados.

**Por qué:** datos maestros inconsistentes contaminan todos los flujos posteriores.

### QA-PROD-03 — Crear y editar receta

**Prioridad/tipo:** P0 · REAL QA

1. Seleccionar un producto existente.
2. Crear receta y versión borrador.
3. Agregar recursos y al menos una etapa activa.
4. Capturar cantidades, unidades, merma/rendimiento disponibles.
5. Guardar, refrescar y volver a abrir.

**Esperado:** receta borrador persistente, recursos y etapas íntegros.

**Por qué:** la receta estandariza qué se necesita y cómo se produce.

### QA-PROD-04 — Aprobación y versionado

**Prioridad/tipo:** P0 · REAL QA

1. Enviar el borrador a aprobación.
2. Aprobar con usuario autorizado.
3. Intentar modificar directamente la versión aprobada.
4. Editar desde el flujo permitido y comprobar la nueva versión.

**Esperado:** transición `draft → pending_approval → approved`; la versión aprobada es inmutable y la edición crea una nueva versión.

**Por qué:** cambiar una receta histórica alteraría costos y explicaciones de futuras operaciones.

### QA-PROD-05 — Reglas negativas de receta

**Prioridad/tipo:** P1 · REAL QA

- Intentar aprobar sin etapas activas.
- Intentar aprobar sin recursos cuando la UI/regla lo exija.
- Hacer doble clic en Guardar/Enviar/Aprobar.
- Repetir una acción después de refrescar.
- Intentar aprobar sin permiso.

**Esperado:** acciones inválidas rechazadas; ningún duplicado; mensajes accionables.

**Por qué:** protege integridad, autorización e idempotencia.

### QA-PROD-06 — Funciones locales de Producción

**Prioridad/tipo:** P1 · PROTOTIPO LOCAL

Recorrer Órdenes, Entregables, Validación de recursos, Áreas y puestos y Maquinaria. Evaluar formularios, cálculos, estados, impresión y claridad del flujo.

Para **Áreas y puestos** validar además:

- [ ] Nueva área solicita únicamente código, nombre, descripción y estatus; no crea puestos.
- [ ] Nuevo puesto muestra un selector y no permite escribir un área libremente.
- [ ] No puede guardarse un puesto si su `area_id` no existe o pertenece a otro tenant.
- [ ] Código y nombre de área no se duplican ignorando mayúsculas/minúsculas.
- [ ] Renombrar un área conserva sus puestos vinculados por ID.
- [ ] Editar un puesto actualiza cantidad de recursos, minutos, capacidad total, costo y estatus sin crear otra área.
- [ ] Un rol con `production.labor_area.update` puede editar áreas sin obtener `production.labor_role.update`, y viceversa.
- [ ] Alta de área, alta de puesto, edición de área y edición de puesto producen auditoría e idempotencia cuando el backend sea implementado.

**Esperado:** experiencia coherente en el mismo navegador. No exigir sincronización entre dispositivos ni persistencia PostgreSQL.

**Por qué:** permite validar tempranamente el proceso antes de conectar el backend.

## 9. Almacenes

**Contexto del módulo:** representa qué existe, dónde se encuentra y cuánto está disponible. Un error puede detener producción o provocar promesas de venta imposibles.

**Estado:** PROTOTIPO LOCAL.

| ID | Prioridad | Qué probar | Esperado |
|---|---|---|---|
| QA-INV-01 | P1 | Crear, buscar y editar almacén. | Validaciones y datos coherentes en el navegador actual. |
| QA-INV-02 | P1 | Crear artículo con SKU, tipo y unidad. | Registro seleccionable y sin duplicados evidentes. |
| QA-INV-03 | P1 | Entrada, salida, transferencia, ajuste y devolución. | Existencia y kardex cambian conforme al movimiento. |
| QA-INV-04 | P1 | Salida mayor a existencia. | Se bloquea o se comunica claramente el faltante. |
| QA-INV-05 | P2 | Filtros de existencias y kardex. | Resultados y estados vacíos comprensibles. |
| QA-INV-06 | P2 | Reservas. | Debe mostrarse deshabilitado/no disponible, no simular una reserva real. |

No certificar todavía concurrencia, lotes, series, reservas reales ni integración con Producción.

## 10. Ventas

**Contexto del módulo:** convierte la necesidad de un cliente en cotización, pedido y entrega, conservando precio y margen.

**Estado:** PROTOTIPO LOCAL.

| ID | Prioridad | Qué probar | Esperado |
|---|---|---|---|
| QA-SALES-01 | P1 | Crear, buscar y editar cliente. | Validaciones comerciales/fiscales claras. |
| QA-SALES-02 | P1 | Cotización con varias líneas, precios y descuentos. | Totales y margen visibles coherentes. |
| QA-SALES-03 | P1 | Aprobar cotización y crear pedido. | Conserva cliente, líneas, origen y promesa. |
| QA-SALES-04 | P1 | Editar pedido y revisar ajustes. | Bitácora/estado comprensibles. |
| QA-SALES-05 | P2 | Imprimir/generar PDF. | Documento legible y consistente con pantalla. |
| QA-SALES-06 | P2 | Entregas no habilitadas. | No debe aparentar una entrega real ni afectar inventario. |

No certificar todavía reservas, producción automática, facturación, cobranza o integración backend.

## 11. Módulos futuros

Compras, Gastos, Costos, Reportes y Contabilidad deben revisarse sólo como comunicación de producto:

- navegación y etiqueta “Próximamente”;
- ausencia de acciones engañosas;
- datos demo claramente distinguibles;
- estados vacíos para tenants nuevos;
- textos y diseño responsive.

No reportar como defecto la falta de operación que ya esté documentada como futura. Sí reportar si la pantalla hace creer que una transacción se guardó realmente.

## 12. Regresión transversal

| ID | Prioridad | Prueba |
|---|---|---|
| QA-NAV-01 | P1 | Refrescar, navegar atrás/adelante, cerrar sesión y volver a entrar. |
| QA-I18N-01 | P2 | Alternar español/inglés; no debe haber claves crudas, variables perdidas ni textos cortados. |
| QA-RESP-01 | P1 | Login, menús, tablas, formularios y modales en iPhone Safari, Android Chrome y escritorio. |
| QA-ERR-01 | P1 | Desconectar red durante una acción; debe haber error claro, sin spinner infinito ni duplicado al reintentar. |
| QA-IDEM-01 | P0 | Doble clic en alta, invitación y comandos de receta; no debe duplicar. |
| QA-EMPTY-01 | P2 | Tenant nuevo sin datos; mostrar estado vacío, no datos de otra empresa. |
| QA-PERM-01 | P0 | Ocultar acciones no autorizadas y confirmar que la API también las rechaza. |

## 13. Evidencia mínima

Para cada ejecución registrar:

| Campo | Ejemplo |
|---|---|
| Caso | QA-PROD-04 |
| Resultado | Pasa/Falla/Bloqueado/No aplica |
| Ambiente | QA |
| Build/commit | `<BUILD_COMMIT>` |
| Fecha y tester | `<FECHA> / <NOMBRE>` |
| Tenant | ID o slug de prueba, sin secretos |
| Navegador/dispositivo | Safari iPhone 15 / iOS X |
| Evidencia | Captura o video sin contraseña, token ni liga vigente |
| Defecto | URL o ID del ticket |

## 14. Cómo reportar un defecto

**Título**

```text
[QA][Módulo][P0/P1/P2] Resultado observable
```

**Contenido**

1. Ambiente, build/commit, navegador y dispositivo.
2. Tenant de prueba y rol, sin credenciales.
3. Precondición.
4. Pasos mínimos para reproducir.
5. Resultado esperado.
6. Resultado actual.
7. Frecuencia: siempre/intermitente/una vez.
8. Impacto de negocio.
9. Captura, video y mensaje/correlation ID disponible.

Nunca adjuntar contraseña, token Firebase, secreto, datos fiscales reales o enlace de invitación todavía válido.

## 15. Criterio de salida de una liberación

Una liberación candidata puede avanzar cuando:

- todos los P0 del alcance ejecutado pasan;
- no hay fuga entre tenants;
- login, Administración y Producción real pasan el smoke;
- fallos P1 tienen decisión explícita;
- P2 están registrados y priorizados;
- lo local/demo está identificado y no se comunica como persistencia real;
- se guardó evidencia de ambiente, build y dispositivo.

## 16. Validacion local previa de volumen de Inventario

El nombre visible objetivo del modulo es **Inventario**, conservando `existencias` como identificador tecnico de la consulta. Esta decision documental no cambia por si sola el alcance desplegado ni autoriza pruebas sobre QA.

Antes de conectar busqueda, filtros y paginacion server-side, ejecutar localmente:

```powershell
node tools/benchmarks/inventory-volume.js
```

El guardrail usa 10,000 articulos sinteticos por tenant y no requiere red ni credenciales. Debe pasar busqueda parcial, filtros combinados, aislamiento, paginacion sin duplicados y la regla temporal `available_quantity = on_hand_quantity` mientras Reservas no exista.

No ejecutar cargas de volumen, seeds, migraciones ni benchmarks en Cloud SQL QA. Cuando el corte funcional se implemente y se autorice su promocion, agregar casos QA separados para el API real y actualizar el mapa de alcance; hasta entonces esta validacion es exclusivamente local.

## 17. Checklist responsive transversal

Aplicar este checklist a toda pantalla nueva o modificada. La fuente tecnica es `docs/arquitectura/estandar_responsive_transversal.md`.

### Matriz minima

Probar 1,440 x 900, 1,280 x 720, 1,024 x 768, 768 x 1,024, 390 x 844 y 320 x 568. En escritorio repetir a zoom 200%. Si hay tabla operativa movil, probar tambien orientacion horizontal.

No basta cambiar el viewport: reducir el ancho real del panel abriendo sidebar, guia de flujo, alertas u otro panel lateral. Repetir estados amplio, intermedio y estrecho con Espanol e Ingles.

### QA-RESP-02 - Contenedor y estructura

- [ ] El componente cambia por su ancho de contenedor, no solamente por el viewport.
- [ ] No hay scroll horizontal de pagina, superposiciones ni regiones fuera de pantalla.
- [ ] Sidebar, flujo y alertas pueden coexistir sin comprimir el area operativa hasta hacerla inutilizable.
- [ ] Carga, vacio, error, sin permisos y resultados reales conservan la misma calidad responsive.

### QA-RESP-03 - Tablas y colecciones

- [ ] La tabla usa tarjeta, scroll interno o vista reducida de acuerdo con la estrategia documentada.
- [ ] En tarjetas cada valor conserva etiqueta, unidad, estado y accion; no depende de encabezados ocultos.
- [ ] Si existe scroll, queda dentro de la tabla, es perceptible y no oculta acciones esenciales.
- [ ] Identificadores, cantidades y acciones no se cortan ni se solapan.
- [ ] El orden de lectura y tabulacion sigue siendo logico.

### QA-RESP-04 - Texto y localizacion

- [ ] Titulos, breadcrumbs, chips, botones, alertas y ayudas soportan textos ES/EN largos.
- [ ] Correos, URLs, IDs y correlation IDs envuelven o permiten consultar/copiar el valor completo.
- [ ] No hay alturas fijas que corten traducciones o mensajes de validacion.
- [ ] La elipsis, si existe, ofrece acceso al contenido completo.

### QA-RESP-05 - Formularios y acciones

- [ ] Campos pasan a una columna sin perder label, ayuda, error o contexto.
- [ ] Lookups, calendarios, selects y textareas no desbordan.
- [ ] Acciones primaria, secundaria y destructiva conservan orden y significado al apilarse.
- [ ] Modal/drawer permite alcanzar encabezado, cierre, errores y acciones con teclado y tacto.
- [ ] Targets tactiles tienen al menos 44 x 44 CSS px o superficie equivalente.

### QA-RESP-06 - Flujos, filtros y alertas

- [ ] En escritorio e intermedio la guia descriptiva conserva el riel vertical izquierdo y su compresion; no cambia globalmente a barra horizontal.
- [ ] Una excepcion responsive de un modulo no altera el formato de la guia ni otros componentes compartidos en las demas secciones.
- [ ] La guia abierta, cerrada y en transicion no cubre contenido ni deja un control ambiguo.
- [ ] Filtros hacen wrap; filtros secundarios y chips no expulsan acciones del panel.
- [ ] Alertas y banners conservan titulo, mensaje, accion y cierre sin tapar la operacion.
- [ ] El foco es visible y no queda detras de contenido sticky, modal o panel lateral.

### Evidencia

Adjuntar capturas de al menos un estado amplio, uno intermedio y uno estrecho, indicando viewport, ancho aproximado del panel, zoom, idioma, navegador y paneles laterales activos. Registrar como P1 cualquier bloqueo operativo, contenido esencial inaccesible o accion fuera de pantalla; defectos cosmeticos con alternativa pueden clasificarse P2.
