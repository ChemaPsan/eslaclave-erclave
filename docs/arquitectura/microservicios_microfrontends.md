# ERClave - Arquitectura de microservicios y microfrontends

Este documento define la separacion objetivo de ERClave para que cada modulo pueda evolucionar sin afectar el resto del sistema. La meta no es partir archivos por partirlos; la meta es aislar responsabilidades, contratos, despliegues y cambios.

## Problema actual

El frontend actual funciona como prototipo navegable, pero concentra demasiada responsabilidad en `frontend/app.js`:

- shell de aplicacion;
- navegacion principal;
- render de modulos genericos;
- logica especializada de Produccion;
- modales y formularios;
- acciones de botones;
- validaciones de UI;
- notificaciones;
- traducciones aplicadas en pantalla.

Mientras todo viva junto, un cambio pequeno en un boton, formulario o submodulo puede tener impacto accidental en otras partes.

## Objetivo

ERClave debe evolucionar hacia una arquitectura donde:

- cada modulo de negocio tenga su microfrontend;
- cada modulo de negocio tenga su microservicio;
- el shell no conozca detalles internos de los modulos;
- los modulos se comuniquen por contratos, no por acceso directo a estructuras internas;
- los eventos entre modulos sean explicitos y versionados;
- los cambios de UI queden encapsulados por modulo;
- los cambios de backend queden encapsulados por servicio;
- los contratos permitan probar un modulo sin levantar todo el sistema.

## Principios de separacion

1. Un modulo no debe importar codigo interno de otro modulo.
2. Un modulo no debe escribir directamente datos de otro modulo.
3. Todo cruce entre modulos debe pasar por API, evento o contrato documentado.
4. El shell solo debe manejar navegacion, layout, tema, idioma, sesion y carga de microfrontends.
5. Los microfrontends solo deben renderizar su area y exponer acciones por contrato.
6. Los microservicios son duenos de sus datos y reglas de negocio.
7. Los eventos deben ser idempotentes: repetir el mismo evento no debe duplicar reservas, movimientos, pagos o asientos.
8. Los cambios visuales deben reutilizar tokens y componentes del sistema visual.
9. Cada modulo debe tener pruebas propias y contrato de integracion.
10. Ningun boton critico debe ejecutar logica transversal directamente.

## Capas objetivo

```text
frontend/
  shell/                  Orquestador visual: layout, nav, idioma, tema, sesion.
  microfrontends/
    produccion/
    recursos-humanos/
    almacenes/
    compras/
    ventas/
    gastos/
    costos/
    reportes/
    administracion/
    contabilidad/
  shared/                 Componentes, tokens, i18n, helpers sin reglas de negocio.

backend/
  services/
    production-service/
    hr-service/
    inventory-service/
    purchasing-service/
    sales-service/
    expenses-service/
    costing-service/
    reporting-service/
    admin-service/
    accounting-service/

contracts/
  api/                    OpenAPI o contratos HTTP por servicio.
  events/                 Eventos publicados y consumidos.
  ui/                     Contratos de microfrontends.
```

## Shell frontend

Responsabilidades:

- cargar modulos disponibles;
- renderizar sidebar, topbar, workspace, panel derecho y modales globales;
- manejar tema claro/oscuro;
- manejar idioma;
- manejar sesion y permisos globales;
- resolver rutas;
- montar y desmontar microfrontends;
- publicar eventos globales de UI;
- mostrar errores de carga de modulo.

No debe hacer:

- calcular costos de produccion;
- validar inventario;
- aprobar compras;
- crear asientos contables;
- decidir estados internos de un modulo;
- manipular datos internos de otro microfrontend.

## Contrato de microfrontend

Cada microfrontend debe exponer una interfaz similar:

```js
export const manifest = {
  id: "produccion",
  title: "Produccion",
  icon: "PR",
  implementationStatus: "implemented",
  permissions: ["production.product_service.read"],
  routes: ["/produccion", "/produccion/recetas", "/produccion/ordenes"]
};

export function mount(container, context) {
  // Renderiza el modulo dentro del contenedor asignado por el shell.
}

export function unmount() {
  // Limpia listeners, timers, suscripciones y estado temporal.
}
```

`context` debe entregar solo capacidades controladas:

- `apiClient`: cliente HTTP con base URL y token.
- `eventBus`: publicacion/suscripcion de eventos permitidos.
- `i18n`: traducciones.
- `theme`: tokens y tema activo.
- `permissions`: permisos del usuario.
- `implementationStatus`: distingue `implemented` de `planned`; el manifiesto no prueba que exista runtime.
- `navigate`: navegacion controlada por shell.
- `toast` y `modal`: UI global sin acoplar reglas.

## Microservicios objetivo

| Servicio | Duenio de datos | Eventos que publica | Eventos que consume |
|---|---|---|---|
| production-service | productos/servicios productivos, recetas, ordenes, etapas, consumos | `production.order.created`, `production.order.completed`, `production.resource.shortage.detected` | `inventory.reservation.confirmed`, `purchasing.receipt.completed`, `sales.order.approved` |
| hr-service | areas, puestos, capacidad nominal, costo hora y elegibilidad productiva | `hr.area.updated`, `hr.position.updated` (futuro) | cambios de entitlement y permisos resueltos sin persistir copias |
| inventory-service | almacenes, ubicaciones, existencias, reservas, movimientos, kardex | `inventory.reservation.created`, `inventory.stock.moved`, `inventory.shortage.detected` | `production.order.created`, `purchasing.receipt.completed`, `sales.order.approved` |
| purchasing-service | proveedores, requisiciones, ordenes de compra, recepciones | `purchasing.requisition.created`, `purchasing.order.sent`, `purchasing.receipt.completed` | `inventory.shortage.detected`, `production.resource.shortage.detected` |
| sales-service | Local: clientes, contactos, cotizaciones, pedidos, surtido y entregas; devoluciones planeadas | Eventos comerciales siguen diferidos hasta definir outbox | Validacion sincronica de RH, Produccion, Admin e Inventory; Production recibe solicitudes, no ordenes liberadas |
| expenses-service | XML/PDF, gastos, cuentas por pagar, pagos | `expenses.invoice.registered`, `expenses.payment.completed` | `purchasing.receipt.completed` |
| costing-service | centros de costos, costos estimados, reales, variaciones | `costing.variance.detected`, `costing.cost.updated` | `production.order.completed`, `inventory.stock.moved`, `expenses.invoice.registered` |
| accounting-service | cuentas, periodos, asientos, mapeos, anexos | `accounting.entry.generated`, `accounting.mapping.missing` | eventos contables de ventas, compras, gastos, inventario, costos y produccion |
| reporting-service | datasets, KPIs, dashboards, exportaciones | `reporting.snapshot.updated` | eventos de todos los servicios |
| admin-service | tenants, usuarios, roles, permisos, configuracion | `admin.permission.changed`, `admin.module.enabled` | ninguno critico; provee configuracion a todos |

## Regla de ownership de datos

Cada dato debe tener un unico dueno.

| Dato | Servicio dueno |
|---|---|
| Producto/servicio productivo | production-service |
| Receta | production-service |
| Orden de produccion | production-service |
| Existencia | inventory-service |
| Reserva | inventory-service |
| Kardex | inventory-service |
| Proveedor | purchasing-service |
| Orden de compra | purchasing-service |
| Cliente | sales-service |
| Pedido | sales-service |
| Gasto/XML/PDF | expenses-service |
| Centro de costos | costing-service |
| Asiento contable | accounting-service |
| Usuario/rol/permiso | admin-service |
| KPI calculado | reporting-service |

## Comunicacion entre servicios

Usar tres mecanismos:

- API sincronica: cuando el usuario necesita respuesta inmediata.
- Evento asincronico: cuando otro modulo debe reaccionar sin bloquear al usuario.
- Snapshot o read model: cuando reportes necesitan consultar informacion consolidada.

Ejemplo:

1. Ventas aprueba pedido.
2. sales-service publica `sales.order.approved`.
3. inventory-service intenta reservar stock.
4. Si no hay stock, inventory-service publica `inventory.shortage.detected`.
5. production-service crea necesidad de produccion o compras genera requisicion segun regla.
6. reporting-service actualiza indicadores.

## Microfrontends por modulo

Cada microfrontend debe contener:

```text
frontend/microfrontends/{modulo}/
  manifest.js            Metadata, rutas y permisos.
  index.js               mount/unmount.
  api.js                 Cliente del servicio del modulo.
  events.js              Eventos publicados y escuchados.
  views/                 Pantallas del modulo.
  components/            Componentes propios del modulo.
  styles.css             Solo estilos locales si no existe componente shared.
  README.md              Ownership y reglas de cambio.
```

Regla: si un componente visual se repite en 2 o mas modulos, debe pasar a `frontend/shared/`. Si una regla de negocio se repite, debe vivir en backend o en contrato, no copiada entre microfrontends.

## Estrategia de migracion progresiva

### Fase 1 - Separar fronteras sin romper prototipo

- Documentar arquitectura y ownership.
- Crear carpetas de microfrontends, servicios y contratos.
- Mantener `frontend/app.js` funcionando como shell temporal.
- Identificar funciones de Produccion que deben migrar a `frontend/microfrontends/produccion/`.

### Fase 2 - Convertir app.js en shell

- Extraer navegacion, tema, idioma, toast y modal a `frontend/shell/`.
- Extraer componentes compartidos a `frontend/shared/`.
- Reemplazar renders internos por carga de microfrontends.
- Mantener compatibilidad con datos mock.

### Fase 3 - Migrar Produccion como primer microfrontend

- Mover catalogo, recetas, ordenes, recursos, areas, maquinaria y validacion.
- Exponer `mount/unmount`.
- Crear contrato de API de production-service.
- Agregar pruebas de render y acciones criticas.

### Fase 4 - Separar microservicios por dominio

- Crear servicios con API propia.
- Sustituir `mockDb` por clientes API por modulo.
- Definir eventos.
- Agregar autenticacion, permisos y auditoria.

### Fase 5 - Endurecer integracion

- Pruebas de contrato.
- Versionado de eventos.
- Observabilidad.
- Feature flags por modulo.
- Despliegue independiente.

## Reglas para cambios futuros

Antes de cambiar un boton, formulario o flujo:

1. Identificar microfrontend dueno.
2. Confirmar si el cambio es visual, funcional o de integracion.
3. Revisar si afecta contrato API o evento.
4. Revisar si afecta permisos.
5. Cambiar solo archivos del modulo dueno.
6. Si toca `shared`, justificar porque aplica a mas de un modulo.
7. Probar el modulo aislado y luego el shell.
8. Registrar trazabilidad.

## Primera decision tecnica

El prototipo actual no debe reescribirse completo de golpe. El primer microfrontend candidato debe ser Produccion porque:

- es el modulo mas desarrollado;
- ya tiene submodulos propios;
- ya tiene utilidades separadas en `frontend/utils/production.js`;
- tiene datos mock propios;
- concentra mayor riesgo de que un cambio local afecte otras pantallas.

La migracion debe comenzar por mover Produccion fuera de `frontend/app.js` y dejar `app.js` como shell temporal.
