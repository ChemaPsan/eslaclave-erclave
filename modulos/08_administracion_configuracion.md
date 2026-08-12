# ERClave — Módulo de Administración y Configuración

## 1. Objetivo

El módulo de Administración y Configuración permitirá controlar la configuración funcional del sistema por tenant, módulos, submódulos, usuarios, roles, permisos, centros de negocio, catálogos y parámetros operativos.

Este módulo será transversal y deberá soportar el crecimiento modular de ERClave.

---

## 2. Alcance

- tenants;
- centros de negocio;
- áreas;
- usuarios;
- roles;
- permisos;
- módulos;
- submódulos;
- catálogos base;
- unidades de medida;
- idiomas;
- monedas;
- configuraciones por módulo;
- bitácora de cambios;
- parámetros por tenant.

---

## 3. Entidades principales

| Entidad | Descripción |
|---|---|
| Tenant | Cliente o empresa que usa ERClave. |
| Centro de negocio | Unidad operativa dentro del tenant. |
| Área | División funcional interna. |
| Usuario | Persona con acceso al sistema. |
| Rol | Conjunto de permisos. |
| Permiso | Acción autorizada sobre un recurso. |
| Módulo | Bloque funcional principal. |
| Submódulo | Funcionalidad dentro de un módulo. |
| Catálogo | Lista administrable de valores. |
| Parámetro | Configuración específica del tenant o módulo. |

---

## 4. Modularidad

ERClave deberá permitir:

- n módulos;
- n submódulos por módulo;
- activación por tenant;
- activación por plan;
- permisos por rol;
- permisos por centro de negocio;
- configuración por cliente;
- dependencias entre módulos.

### Ejemplo

```text
Modulo: Producción
  Submódulo: Productos y servicios
  Submódulo: Recetas
  Submódulo: Ordenes de producción
  Submódulo: Asignación por área
  Submódulo: Costeo estimado
```

---

## 5. Roles iniciales sugeridos

| Rol | Alcance |
|---|---|
| Propietario del tenant | Control general del cliente. |
| Administrador corporativo | Control sobre varios centros de negocio. |
| Administrador de centro | Control limitado a un centro. |
| Supervisor de producción | Gestión operativa de producción. |
| Operador | Ejecución de tareas asignadas. |
| Compras | Gestión de requisiciones y órdenes. |
| Ventas | Gestión comercial. |
| Finanzas/Gastos | Gestión de gastos y pagos. |
| Consulta/reportes | Solo lectura y reportes autorizados. |
| Integrador técnico | Gestión de apps/API según permisos. |

---

## 6. Reglas de negocio

- Ningún usuario cliente deberá acceder a la consola interna de EsLaClave.
- Los usuarios solo deberán ver información de su tenant.
- Los permisos deberán considerar módulo, submódulo, acción y alcance.
- Algunos roles podrán crear usuarios, pero solo dentro de su alcance.
- Los módulos desactivados no deberán mostrarse ni permitir operación.
- Los catálogos podrán tener valores globales y valores propios del tenant.
- Los cambios de configuración relevantes deberán auditarse.
- Las dependencias entre módulos deberán estar configuradas para evitar operaciones incompletas.
- Si un módulo depende de otro no contratado, deberá existir modo degradado definido.
- Los catálogos compartidos deberán ser reutilizados por todos los módulos para evitar duplicidad.

---

## 7. Permisos sugeridos

Los permisos deberán nombrarse de forma consistente.

Ejemplos:

```text
production.recipes.read
production.recipes.create
production.recipes.update
production.orders.approve
warehouses.movements.create
purchases.orders.approve
sales.orders.cancel
expenses.documents.validate
reports.costs.read
admin.users.create
```

---

## 8. Catálogos base

Los catalogos base son configuraciones transversales que deberan administrarse desde este modulo para evitar valores duplicados o quemados dentro de cada modulo funcional.

La referencia ampliada se documenta en `docs/catalogos_base.md`.

| Grupo | Catalogos iniciales |
|---|---|
| Transversales | centros de negocio, areas, roles, permisos, unidades de medida, monedas, impuestos, prioridades, idiomas. |
| Produccion | tipos de producto/servicio, tipos de recurso, estados de receta, estados de orden, motivos de pausa, motivos de reproceso. |
| Almacenes | tipos de almacen, politicas de inventario, tipos de movimiento, motivos de ajuste, estados de inventario, tipos de ubicacion fisica. |
| Compras | tipos de proveedor, condiciones de pago, metodos de entrega, estados de requisicion, estados de orden de compra, motivos de rechazo. |
| Ventas | tipos de cliente, listas de precio, condiciones comerciales, estados de cotizacion, estados de pedido, canales de venta. |
| Gastos | tipos de gasto, categorias de gasto, metodos de pago, estados de gasto, tipos de comprobante, motivos de rechazo. |
| Costos | centros de costo, drivers de prorrateo, metodos de costeo, tipos de variacion, tipos de costo. |
| Contabilidad | cuentas contables, periodos contables, tipos de poliza, tipos de documento origen, tipos de operacion, estados contables, reglas de mapeo contable. |

---

## 9. Dependencias funcionales entre módulos

Administración deberá permitir configurar dependencias como:

| Módulo | Dependencias recomendadas |
|---|---|
| Producción | Almacenes, Costos, Centros de costos. |
| Almacenes | Catálogo de productos/recursos, Costos. |
| Compras | Proveedores, Almacenes, Gastos, Contabilidad opcional. |
| Ventas | Clientes, Almacenes, Producción opcional, Costos, Contabilidad opcional. |
| Gastos | Proveedores, Centros de costos, Contabilidad opcional. |
| Costos | Producción, Almacenes, Compras, Gastos, Ventas. |
| Contabilidad | Cuentas contables, periodos, anexos y mapeos. |
| Reportes | Todos los módulos activos y permisos. |

### Reglas de activación

- Un módulo podrá activarse aunque otro no esté contratado solo si existe un modo degradado funcional.
- Si Contabilidad está activa, Ventas, Gastos, Compras, Almacenes y Costos deberán validar mapeos contables.
- Si Almacenes está activo, Producción y Ventas deberán usar reservas y movimientos reales.
- Si Costos está activo, Producción, Compras, Gastos y Ventas deberán alimentar costos reales.
- Si Reportes está activo, todos los módulos deberán enviar dimensiones comunes.

---

## 10. Integraciones

| Módulo | Relación |
|---|---|
| Todos los módulos | Control de permisos, catálogos y configuración. |
| Infraestructura SaaS | Tenants, planes, módulos activos y límites. |
| APIs | Scopes, apps externas y permisos técnicos. |
| Reportes | Alcance de visibilidad por rol. |

---

## 11. Pendientes

- Definir matriz inicial de permisos.
- Definir roles del MVP.
- Definir catálogo de módulos y submódulos.
- Definir qué configuraciones serán por tenant.
- Definir bitácora de cambios administrativos.
- Construir la pantalla `Administracion > Catalogos base`.
- Migrar opciones fijas del MVP a catalogos administrables cuando el flujo lo requiera.

---

## 12. Editor de permisos por rol

El editor administra un rol a la vez y conserva personalizacion permiso por permiso. No incluye plantillas, presets ni seleccion automatica basada en el nombre del rol.

Flujo:

1. Abrir un rol y seleccionar **Editar permisos**.
2. Cargar el catalogo completo asignable y las asignaciones actuales con su `scope`.
3. Buscar por nombre humano, descripcion o codigo tecnico; filtrar por asignados, no asignados o cambios.
4. Seleccionar o quitar permisos individuales, por modulo o solo sobre resultados visibles.
5. Revisar el resumen de permisos agregados y retirados.
6. Guardar una sola vez con revision esperada e idempotencia.

Reglas:

- Los nombres visibles usan verbo + objeto en Espanol/Ingles; el codigo estable permanece como detalle tecnico.
- Filtrar o colapsar un modulo nunca altera permisos ocultos.
- Los permisos de un modulo inactivo se conservan como configuracion historica, pero no pueden agregarse ni ejecutarse hasta reactivarlo.
- Permisos `internal`, `public` o de credenciales de integracion no son asignables a roles humanos del tenant.
- Un permiso nuevo aparece desmarcado; no se agrega implicitamente a roles existentes.
- La UI mantiene `original` y `draft`; salir con cambios exige confirmar descarte.
- El backend rechaza revision obsoleta, permiso no asignable, modulo no disponible, rol de otro tenant o intento inseguro sobre rol de sistema.
- El guardado aplica diferencias y conserva `scope` de asignaciones no modificadas.
- La auditoria registra actor, revision anterior/nueva, agregados, retirados y scopes modificados.

Responsive y accesibilidad:

- En contenedor amplio se usa matriz por recurso y accion.
- En contenedor estrecho cada recurso se transforma en tarjeta etiquetada sin scroll horizontal de pagina.
- Checkboxes nativos, labels completos, foco visible, controles de modulo con estado mixto y resumen `aria-live`.
