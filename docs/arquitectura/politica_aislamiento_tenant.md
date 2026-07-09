# ERClave - Politica de aislamiento tenant

## 1. Objetivo

ERClave usa un modelo SaaS multi-tenant logico, tambien llamado pooled multi-tenancy:

```text
Una plataforma compartida
Una capa de servicios compartida
Una base de datos compartida por ambiente
Datos separados por tenant_id, permisos y contexto de sesion
```

Esta politica define las reglas minimas para que ese modelo sea seguro y escalable para volumen.

La regla central es:

> Ningun dato operativo puede existir sin `tenant_id`, y ninguna lectura o escritura operativa puede ejecutarse sin contexto de tenant validado.

## 2. Definiciones

| Termino | Definicion |
|---|---|
| Tenant | Empresa, cliente o espacio aislado dentro de ERClave. |
| Identidad global | Persona autenticada una sola vez en ERClave, guardada en `admin.users`. |
| Membresia | Relacion entre una identidad global y un tenant, guardada en `admin.memberships`. |
| Contexto de tenant | Tenant activo, usuario, membresia, roles, permisos, modulos activos y alcance operativo. |
| Dato operativo | Cualquier dato funcional del ERP: catalogos, documentos, movimientos, configuracion, costos, inventario, ventas, compras, produccion, reportes. |
| Backoffice interno | Herramientas de EsLaClave para operar tenants. No pertenece a ningun tenant cliente. |

## 3. Niveles permitidos de aislamiento

ERClave arranca con aislamiento logico compartido:

```text
tenant_id + contexto de sesion + permisos + pruebas anti-fuga
```

No se requiere IP, URL, base de datos o servicio dedicado por cliente para el MVP ni para la estrategia de volumen.

Una excepcion dedicada por cliente solo debe aprobarse si existe una necesidad contractual o regulatoria explicita. No es el camino base del producto.

## 4. Clasificacion de tablas

### 4.1 Tablas globales permitidas

Estas tablas pueden existir sin `tenant_id` porque representan catalogos o identidades globales:

| Tabla | Motivo |
|---|---|
| `admin.tenants` | Registro maestro de tenants. |
| `admin.users` | Identidad global; el acceso real vive en membresias por tenant. |
| `admin.permissions` | Catalogo global de permisos versionados por contrato/API. |

### 4.2 Tablas con `tenant_id` obligatorio

Toda tabla operativa o de configuracion tenant-scoped debe incluir `tenant_id` no nulo.

Ejemplos:

| Area | Tablas |
|---|---|
| Admin tenant-scoped | `admin.roles`, `admin.memberships`, `admin.role_permissions`, `admin.membership_roles`, `admin.tenant_modules`, `admin.tenant_settings`, `admin.tenant_usage_daily`. |
| Produccion | `production.product_services` y futuras tablas de recetas, ordenes, consumos, centros de trabajo y costos. |
| Inventarios | almacenes, existencias, movimientos, lotes, traspasos y kardex. |
| Ventas | clientes, cotizaciones, pedidos, facturas y cobranza. |
| Compras | proveedores, requisiciones, ordenes, recepciones y cuentas por pagar. |

### 4.3 Excepcion controlada: auditoria

`admin.audit_events.tenant_id` puede ser nulo solo para eventos transversales reales, por ejemplo:

- login fallido antes de seleccionar tenant;
- operaciones de backoffice sobre multiples tenants;
- tareas internas de plataforma.

Todo evento que afecte un tenant especifico debe guardar `tenant_id`.

## 5. Reglas para base de datos

1. Toda tabla tenant-scoped debe tener `tenant_id` `NOT NULL`.
2. Toda llave unica de negocio debe incluir `tenant_id`.
3. Todo indice principal de consulta debe iniciar o incluir `tenant_id`.
4. Toda foreign key tenant-scoped debe preservar consistencia dentro del mismo tenant.
5. Las migraciones no deben crear tablas operativas sin `tenant_id`.
6. Las migraciones destructivas siguen prohibidas salvo aprobacion explicita y plan de migracion.
7. Antes de produccion seria, se debe evaluar Row-Level Security para reforzar el aislamiento en PostgreSQL.

Ejemplo correcto:

```sql
unique (tenant_id, code)
index (tenant_id, status)
where tenant_id = :tenant_id and id = :id
```

Ejemplo incorrecto:

```sql
unique (code)
where id = :id
```

## 6. Reglas para APIs

Toda API operativa debe:

1. Exigir tenant activo por header, path o contexto resuelto.
2. Validar que el usuario autenticado pertenece al tenant solicitado.
3. Validar tenant activo.
4. Validar modulo activo si la ruta pertenece a un modulo.
5. Validar permiso efectivo.
6. Pasar `tenant_id` al repositorio como parametro obligatorio.
7. Nunca confiar en `tenant_id` solo porque vino del frontend.

Para MVP local/demo se permite `X-Tenant-Id`, pero debe considerarse un transportador de seleccion, no una autorizacion.

## 7. Reglas para repositorios

Toda funcion de repositorio que lea o escriba datos tenant-scoped debe:

1. Recibir `tenant_id` como argumento requerido.
2. Incluir `tenant_id = :tenant_id` en `select`, `update`, `delete` y verificaciones previas.
3. Usar `on conflict (tenant_id, ...)` para upserts tenant-scoped.
4. Evitar helpers que busquen solo por `id` en tablas tenant-scoped.
5. Devolver `None` o `404` cuando el recurso existe en otro tenant, sin revelar su existencia.

## 8. Reglas para frontend

El frontend puede mejorar experiencia, pero no es barrera de seguridad.

Debe:

1. Resolver tenant desde `session/context` o `session/tenants`.
2. Enviar el tenant activo en llamadas API cuando aplique.
3. Ocultar pantallas o acciones sin permiso, como comodidad visual.
4. No mostrar datos mock en modo API para tenants reales.

No debe:

1. Inventar permisos desde `localStorage`.
2. Usar datos demo cuando el usuario esta autenticado en un tenant real.
3. Mezclar llaves locales entre tenants.

## 9. Reglas para backoffice

El backoffice interno puede operar multiples tenants, pero debe estar separado de la experiencia cliente.

1. Solo correos en `ERCLAVE_BACKOFFICE_ADMIN_EMAILS` pueden usar rutas `/v1/backoffice/*`.
2. Las acciones internas deben auditar actor, tenant afectado, accion e idempotency key cuando aplique.
3. Las pantallas internas no deben renderizarse antes de validar autorizacion contra backend.
4. La creacion como owner de un tenant no otorga acceso al backoffice.

## 10. Pruebas obligatorias anti-fuga

Cada modulo operativo nuevo debe incluir pruebas que creen al menos dos tenants:

```text
Tenant A crea recurso A
Tenant B crea recurso B
Tenant A no puede leer recurso B
Tenant A no puede actualizar recurso B
Tenant A no puede borrar recurso B
Listados de Tenant A no incluyen recursos de Tenant B
Codigos repetidos pueden existir en tenants distintos
```

Estas pruebas deben vivir en el servicio dueño del modulo.

## 11. Validadores automaticos

El repositorio debe mantener validadores que fallen cuando:

1. Una migracion crea una tabla tenant-scoped sin `tenant_id`.
2. Una tabla tenant-scoped define una llave unica de negocio sin `tenant_id`.
3. Un repositorio operativo consulta tablas tenant-scoped sin filtro `tenant_id`.
4. Un servicio operativo no exige contexto de tenant en sus rutas.

Los validadores no sustituyen revision de codigo, pero bloquean errores obvios antes de que lleguen a QA.

## 12. Criterio de listo para funcionalidades ERP

Una funcionalidad ERP cliente puede avanzar cuando:

1. Su modelo fisico cumple esta politica.
2. Sus endpoints reciben o resuelven tenant.
3. Sus repositorios filtran por tenant.
4. Sus pruebas anti-fuga pasan.
5. Su UI usa contexto real de sesion y no datos demo en modo API.

Si falta cualquiera de estos puntos, la funcionalidad no esta lista para multi-tenant logico seguro.
