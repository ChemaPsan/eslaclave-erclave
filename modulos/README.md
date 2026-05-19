# ERClave — Documentación por módulos

Esta carpeta separa la documentación funcional de ERClave por módulo, para que cada área pueda crecer sin saturar el documento base del proyecto.

El documento base mantiene la visión general, el enfoque modular y el roadmap. Los documentos de esta carpeta deberán usarse para bajar cada módulo a reglas, flujos, catálogos, estados, permisos, métricas y criterios de aceptación.

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

## Principio rector

ERClave deberá aprender de los ERP grandes, pero avanzar con una implementación simple, modular y progresiva.
