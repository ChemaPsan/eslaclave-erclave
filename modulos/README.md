# ERClave — Documentación por módulos

Esta carpeta separa la documentación funcional de ERClave por módulo, para que cada área pueda crecer sin saturar el documento base del proyecto.

El documento base mantiene la visión general, el enfoque modular y el roadmap. Los documentos de esta carpeta deberán usarse para bajar cada módulo a reglas, flujos, catálogos, estados, permisos, métricas y criterios de aceptación.

Regla transversal de selección: maestros y documentos que crecen se consultan mediante búsqueda y resultados acotados, guardando IDs estables; listas cerradas como estatus, tipo o prioridad conservan el selector directo. La cobertura y los criterios completos están en `docs/arquitectura/seleccion_escalable_documentos.md`.

Regla transversal de portada: la raíz de cada módulo operativo consulta reportes estándar propios y no genera acciones operativas. Altas, cambios y transiciones viven en submódulos. Administración es la excepción: su raíz conserva el centro de configuración. Los cruces, tableros configurables y análisis a la medida se reservan para el módulo Reportes, actualmente inactivo. La matriz completa está en `docs/arquitectura/reportes_estandar_por_modulo.md`.

Regla transversal de mutaciones: guardar, crear, editar, eliminar o cambiar estatus muestra inmediatamente un indicador bilingüe de operación en curso y bloquea nuevas activaciones hasta que finaliza la solicitud. El bloqueo se libera también ante error y usa un contador para no ocultarse mientras exista otra mutación pendiente.

## Módulos documentados

| Archivo | Módulo | Propósito |
|---|---|---|
| [00_sinergia_modular.md](00_sinergia_modular.md) | Sinergia modular | Contratos, eventos, validaciones y compatibilidad entre módulos. |
| [01_produccion.md](01_produccion.md) | Producción | Recetas, recursos, órdenes de producción, entregables por área y control operativo. |
| [02_almacenes_inventarios.md](02_almacenes_inventarios.md) | Almacenes e inventarios | Existencias, movimientos, reservas, kardex, ubicaciones, merma y producto terminado. |
| [03_compras_abastecimiento.md](03_compras_abastecimiento.md) | Compras y abastecimiento | Proveedores, requisiciones, órdenes de compra, recepciones y reabastecimiento. |
| [04_ventas_clientes.md](04_ventas_clientes.md) | Ventas y clientes | Clientes, cotizaciones, pedidos, entregas, facturación comercial y margen. |
| [05_gastos_cuentas_por_pagar.md](05_gastos_cuentas_por_pagar.md) | Gastos y cuentas por pagar | XML/PDF, gastos, proveedores, vencimientos, pagos y asignaciones. |
| [06_costos_centros_de_costos.md](06_costos_centros_de_costos.md) | Costos y centros de costos | Costeo estimado, real, variaciones, centros de costos y rentabilidad. |
| [07_reportes_inteligencia_operativa.md](07_reportes_inteligencia_operativa.md) | Reportes e inteligencia operativa | Indicadores, dashboards, reportes configurables y análisis operativo. |
| [08_administracion_configuracion.md](08_administracion_configuracion.md) | Administración y configuración | Roles, permisos, módulos, submódulos, catálogos base y configuración por tenant. |
| [09_contabilidad.md](09_contabilidad.md) | Contabilidad | Cuentas contables, periodos, asientos, anexos, mapeos contables y reportes contables. |
| [10_recursos_humanos.md](10_recursos_humanos.md) | Recursos Humanos | Áreas, puestos, costo por hora, capacidad y elegibilidad para Producción. |
| [11_mantenimiento.md](11_mantenimiento.md) | Mantenimiento | Ordenes correctivas, responsables, tiempos, continuidad productiva y refacciones. |

## Criterio de documentación

Cada módulo deberá documentarse con una estructura similar:

1. Objetivo.
2. Alcance.
3. Funcionalidades.
4. Entidades principales.
5. Flujos.
6. Estados.
7. Reglas de negocio.
8. Roles y permisos.
9. Métricas.
10. Integraciones con otros módulos.
11. Pendientes.

## Estado MVP funcional

| Modulo | Estado actual |
|---|---|
| Produccion | API, persistencia y UI reales en Local y QA: recetas ponderadas, validacion autoritativa, reservas/consumo, capacidad comprometida, avance porcentual y recepcion posterior de producto terminado. |
| Almacenes | Inventory real en Local y QA para almacenes, articulos, movimientos, existencias, Kardex, reservas/consumo, disponibilidad neta, valuacion, concurrencia y recepcion de producto terminado. |
| Ventas | Backend y UI reales en Local y QA para Clientes, Cotizaciones, Pedidos y Entregas hasta `20260818_0020`, con mapeo producto-articulo, sanitizacion, costo por fuente y orquestacion concurrente/reconciliable. Devoluciones y facturacion permanecen `planned`. |
| Administracion | UI y `admin-service` reales en QA para organizacion, usuarios, roles, permisos, entitlements, sesion y backoffice. |
| Recursos Humanos | `hr-service`, schema, contrato, UI, expedientes, elegibilidad productiva y capacidad autoritativa reales en Local y QA. Los datos QA dependen de captura funcional autorizada; no se asumen catalogos vacios. |
| Mantenimiento | Backend, schema, contrato, permisos y UI reales en Local: correctivos manuales o desde Produccion, asignacion RH, tiempos, refacciones, bloqueo seguro y conciliacion durable. |
| Resto de modulos | Mantienen MVP generico para especializarse progresivamente. |

La navegacion efectiva depende de `session/context`, entitlements y permisos. Cada capacidad debe identificarse como QA, Local, mock o futura conforme a `docs/contexto/ESTADO_ACTUAL.md`; el estado no se duplica en fichas de agentes.

## Principio rector

ERClave deberá aprender de los ERP grandes, pero avanzar con una implementación simple, modular y progresiva.
