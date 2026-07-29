# Estado actual de ERClave

Ultima actualizacion: 2026-07-28.

## Ambiente local

- Frontend estatico local esperado en `http://127.0.0.1:4173`.
- Admin API local esperada en `http://127.0.0.1:8010`.
- Production API local esperada en `http://127.0.0.1:8002`.
- Inventory API local esperada en `http://127.0.0.1:8004`.
- PostgreSQL portatil aislado para Inventory escucha en `127.0.0.1:5434`, base `erclave_local`.
- Firebase autentica; `admin-service /v1/session/context` resuelve tenant, membresia, modulos, permisos y alcance.

## Cortes funcionales relevantes

### Produccion

- Productos y servicios se presentan como catalogo maestro antes de consultar ordenes relacionadas.
- Recetas y ordenes cuentan con integracion local/API documentada en trazabilidad.
- Areas y puestos son catalogos independientes en el frontend local: el area tiene ID estable y el puesto solo puede seleccionar un area existente.
- Alta y edicion usan permisos separados: `production.labor_area.create/update` y `production.labor_role.create/update`; OpenAPI incluye tambien lecturas independientes.
- El contrato de production-service esta preparado, pero la persistencia API de areas y puestos sigue pendiente de implementacion backend; no se presenta como remota.

### Almacenes e inventarios

- `inventory-service` es propietario de almacenes, articulos, movimientos, balances y Kardex.
- El submodulo visible `Inventario` conserva el identificador tecnico `existencias`.
- Inventario consume balances enriquecidos con busqueda, filtros, orden y paginacion server-side.
- La vista usa container queries: colapsa el flujo por defecto, transforma la tabla en tarjetas cuando el panel central se estrecha y mueve Alertas debajo del contenido en viewports intermedios.
- Los movimientos registrados y no reversados son la fuente de verdad.
- `available_quantity = on_hand_quantity` y `reserved_quantity = 0` hasta implementar Reservas.
- La migracion local vigente es `20260727_0008`; no esta autorizada ni aplicada en QA por este corte.
- La validacion local cubrio 10,000 articulos y 10,000 movimientos; consultar `docs/operaciones/validacion_volumen_inventario_local.md`.

### Interfaz transversal

- El shell, los modulos activos, los catalogos, formularios y modales comparten reglas responsive basadas en el ancho real de su contenedor.
- La guia descriptiva conserva el patron compartido de riel vertical izquierdo y compresion; solo pasa a una columna en anchos estrechos o mediante una excepcion explicita de pantalla.
- En anchos intermedios las colecciones reducen columnas; en anchos estrechos formularios y acciones se apilan sin ocultar su significado.
- El backoffice transforma sus filas de tenants y consumo en tarjetas etiquetadas cuando su panel se estrecha.
- La navegacion movil conserva los submodulos activos, foco visible, salto al contenido y anuncios accesibles de notificaciones.
- `npm.cmd run validate:responsive` protege los contenedores, puntos de accesibilidad y referencias documentales obligatorias.

## Calidad

- La fuente de verdad del resultado automatizado es la ultima ejecucion de `npm.cmd run verify`.
- Al cerrar el corte de Inventario: 103 pruebas backend y todos los validadores aprobados.
- El repositorio puede contener cambios locales no confirmados; `session:context` debe mostrar el estado Git real de cada sesion.
- `npm.cmd run session:context` reconstruye la memoria operativa sin mostrar secretos: Git, trazabilidad, migraciones, estado, decisiones, tenants, pendientes y puertos locales.
- `validate-session-context.js` protege la presencia de los documentos y guardrails obligatorios.
- `validate-responsive-ui.js` protege el estandar transversal de interfaz para futuras sesiones.

Este archivo debe describir hechos comprobados, no planes ni aspiraciones.
