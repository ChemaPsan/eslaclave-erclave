# Decisiones vigentes de ERClave

## Arquitectura y ownership

- El frontend consume HTTP exclusivamente mediante `frontend/api/`.
- Cada microservicio escribe solamente su schema y datos propios.
- No se crean FKs entre schemas de servicios distintos.
- Los movimientos de inventario son inmutables: se corrigen con reversa o nuevo ajuste auditable.
- Balances y Kardex son consultas calculadas; no tienen captura directa.
- Los contratos OpenAPI, schemas, consumidores y pruebas cambian en el mismo corte.

## Identidad y autorizacion

- Firebase es proveedor de identidad, no fuente de permisos ni membresias.
- ERClave autoriza mediante `admin-service /v1/session/context`.
- `X-Tenant-Id` selecciona contexto, pero nunca concede autoridad.
- Las APIs aplican permisos y aislamiento aunque el frontend o sus filtros sean manipulados.

## Datos y escalamiento

- PostgreSQL es la fuente transaccional del MVP.
- Toda consulta operativa multi-tenant comienza restringida por `tenant_id`.
- Las listas grandes usan filtros server-side, limites y paginacion estable; no se descargan colecciones completas para filtrarlas en el navegador.
- Categoria de articulos sigue siendo texto libre. Un catalogo jerarquico requiere una decision funcional y migracion posteriores.
- Reservas, bloqueos, transito y cuarentena no deben mostrarse como reales hasta que exista su modelo operativo.
- Las areas laborales son catalogos independientes con ID estable. Los puestos solo pueden vincularse a un `labor_area_id` existente del mismo tenant; nunca crean areas desde texto libre.
- Crear/editar areas y crear/editar puestos usan permisos distintos para que los roles de usuario deleguen cada responsabilidad por separado.
- Areas y puestos pertenecen a `hr-service`, usan permisos `hr.area.*` y `hr.position.*` y requieren el entitlement `hr` activo. Produccion y Costos solo consumen el contrato; no escriben el esquema `hr`.
- Produccion conserva snapshots de los datos laborales utilizados por una receta para que cambios posteriores de costo, capacidad o estatus no alteren historia aprobada.
- El editor de permisos no usa plantillas ni presets: cada rol conserva personalizacion individual. La UI ofrece busqueda, filtros y selecciones masivas explicitas, pero nunca concede permisos por nombre de rol.
- Los codigos de permiso permanecen como contrato; la UI muestra etiquetas/descripciones ES/EN versionadas. Solo permisos clasificados `tenant` y marcados asignables pueden concederse a roles humanos.
- Editar permisos usa draft, diff, guardado unico, revision optimista e idempotencia. Los filtros no limitan el payload ni eliminan asignaciones ocultas; scopes existentes se preservan.
- Un articulo solo es candidato de receta cuando esta activo y tiene `use_in_recipe=true`; la disponibilidad se calcula desde movimientos de todos los almacenes del tenant.
- Inventario incluye articulos sin movimientos con saldo cero cuando tienen almacen sugerido, sin fabricar movimientos ni existencias.

## Ambientes

- Local, QA y Produccion no comparten bases de datos de prueba.
- No se despliega, migra, ejecuta seed ni escribe en QA/Produccion sin autorizacion explicita.
- Las pruebas de volumen y datos dummy se ejecutan solamente en recursos locales aislados y se limpian al terminar.

## Responsive y accesibilidad visual

- Los componentes contenidos en paneles se adaptan mediante CSS Container Queries; los media queries de viewport se reservan para el shell global.
- Cada tabla declara una estrategia compacta: tarjetas con etiquetas, scroll horizontal interno o vista reducida justificada.
- Ningun layout depende de cortar textos traducibles, identificadores, cantidades, errores o acciones esenciales.
- Formularios, flujos, filtros y alertas deben seguir operables cuando sidebar y paneles laterales reduzcan el ancho real del contenido.
- Los breakpoints se eligen donde el contenido se rompe, usando como referencia los estados documentados en `docs/arquitectura/estandar_responsive_transversal.md`.
- QA verifica ancho de contenedor, zoom 200%, teclado, ES/EN y estados carga/vacio/error; probar solo resoluciones de viewport no es suficiente.
- La guia de flujo compartida mantiene el riel vertical izquierdo y su estado comprimido. Las correcciones de una pantalla no pueden modificar globalmente su formato; cualquier excepcion se delimita con una clase especifica.

Una decision nueva o reemplazada debe registrarse tambien en `TRAZABILIDAD.md` y actualizar las fuentes funcionales correspondientes.
