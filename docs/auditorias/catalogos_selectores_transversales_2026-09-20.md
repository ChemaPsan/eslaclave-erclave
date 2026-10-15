# Auditoría transversal de catálogos y selectores

> Evidencia histórica: conserva observaciones y decisiones de su fecha; no usar como estado o instrucciones actuales. Consultar [fuente vigente](../contexto/ESTADO_ACTUAL.md).

Fecha: 2026-09-20. Alcance: revisión de código Local de los módulos implementados, sin navegador operativo, datos, QA ni Producción. Criterio: distinguir catálogos administrables, referencias de otras entidades y enums cerrados del dominio. No toda lista breve debe convertirse en catálogo.

| Módulo o flujo | Fuente actual | Resultado | Acción de esta fase |
|---|---|---|---|
| Administración: roles, sucursales, entidades legales y módulos | Respuestas autoritativas de Admin | Coherente | Ninguna. |
| Unidades usadas por Producción, Inventarios, Ventas y Compras | Catálogo activo de unidades de Admin y validación backend | Coherente para altas. La política completa de unidades históricas requiere decidir sustitución y bloqueo por movimientos. | No ampliar dentro de este corte. Mantener el tratamiento existente de unidades inactivas y abordarlo sólo con reglas de ciclo de vida. |
| Ventas: monedas y condiciones en Clientes/Cotizaciones | Catálogos activos de Admin vía Sales | Catálogo correcto, pero un código histórico ausente podía hacer que el selector mostrara la primera opción activa. | Corregido en CHG-285: mostrar el código histórico como no vigente, omitirlo del PATCH mientras no se reemplace y exigir una opción activa para altas nuevas. |
| Compras: monedas y condiciones en Proveedores | Catálogos activos de Admin vía Purchasing | Corregido por CHG-284; se confirmó el mismo tratamiento histórico compartido. | Reutilizar el helper de referencias comerciales. |
| Producción: producto/servicio, recetas, órdenes y recursos | Unidades, Inventario, RH y Maquinaria autoritativos; tipo, estatus y prioridad cerrados | Coherente. `category`, `cost_center` y `responsible_area` siguen siendo decisiones funcionales abiertas. | No inventar catálogos ni campos antes de resolver su semántica. |
| Inventarios: tipo, política, movimiento y estatus | Literales de contrato; almacenes, artículos y unidades autoritativos | Coherente | Ninguna. |
| RH: áreas, puestos y trabajadores | Entidades HR autoritativas; estatus cerrados | Coherente | Ninguna. |
| Mantenimiento: objetivo, prioridad, costo y transiciones | Literales del contrato; máquinas, técnicos, artículos, almacenes y órdenes autoritativos | Coherente | Ninguna. |
| Datos fiscales de Cliente y Proveedor | Captura libre/parcial y flujo mexicano actual | Requiere catálogo fiscal y reglas temporales cuando entren CFDI, factura/XML y cuentas por pagar. Ese alcance aún está `planned`. | Diferir hasta el corte fiscal; no agregar listas parciales nuevas. |
| Filtros de reportes | Enums del reporte, valores configurados y códigos ya usados | Coherente | Ninguna. |

## Decisión

La única corrección necesaria para la fase actual fue Ventas, porque Clientes y Cotizaciones ya forman parte del ciclo operativo y una sustitución visual podía alterar un código al guardar. El resto no presenta el mismo desajuste o depende de decisiones de negocio y módulos todavía planeados. Convertir tipos, estados o prioridades en catálogos configurables debilitaría las máquinas de estado y sus validaciones.

## APIs afectadas

CHG-285 no añade ni modifica contratos. El frontend continúa consumiendo `GET /v1/sales/reference-data`, `POST/PATCH /v1/sales/customers` y `POST/PATCH /v1/sales/quotes` con los permisos existentes. En PATCH, `currency` y `payment_terms` se omiten cuando el registro conserva un código histórico no vigente; el backend mantiene el valor actual. Las altas exigen códigos activos. No se llamaron endpoints durante esta auditoría.
