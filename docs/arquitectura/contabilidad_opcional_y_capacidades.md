# Organización independiente y Contabilidad opcional


CHG-294 · 2026-09-27 · Análisis y criterio de diseño; no activa servicios, capacidades ni entitlements.

## Resultado

La estructura organizacional pertenece a Administración y debe servir a la operación aunque Contabilidad nunca se contrate o active. La preparación de datos no equivale a ejecutar Contabilidad. Una pantalla en Administración tampoco cambia el dueño del dato ni concede permisos sobre otro módulo.

| Capacidad | Superficie | Dueño | Relación con Contabilidad |
|---|---|---|---|
| Emisores, Sociedades, Divisiones, membresías y alcance | Administración | Admin | Independiente; no crea libros ni pólizas. |
| Configuración operativa por División y referencias en documentos | Administración y módulo operativo | Cada servicio escribe sus datos | Independiente; no exige cuentas, periodos ni mapeos contables. |
| Catálogo básico de Centros de costos por División | Administración | Costing por contrato | Independiente de Accounting; requiere capacidad de catálogo implementada y autorizada. |
| Cálculos de costos, prorrateos, variaciones y rentabilidad | Costos | Costing | Se habilitan por su propio módulo; no requieren activar Accounting. |
| Libros por Sociedad, cuentas, periodos, mapeos, pólizas y reportes contables | Contabilidad | Accounting | Sólo con runtime implementado, módulo efectivo y permiso/alcance válidos. |

Implementado Local en [CONT-05](cont_05_catalogo_centros.md): catálogo básico separado de analítica y Accounting, mostrado en Administración y conservado por Costing. Sólo costing.cost_center.read/create/update/status se resuelven mediante disponibilidad Admin; requiere runtime habilitado en ambos servicios, permiso y scope. No se concede el entitlement completo de Costing ni un bypass de permisos. [Matriz de capacidades](matriz_capacidades_organizacionales.md) y [control vigente](../contexto/CONTROL_CONTABLE.md).

La obligatoriedad de Centro de costos ya acordada conserva vigencia en flujos de imputación habilitados. Para tenants sin uso de costos ni contabilidad, no se bloquea la operación ni se exige configurar centros sólo para prepararse. Esta condicionalidad fue confirmada por el usuario en CHG-296: se exige sólo por flujo de imputación habilitado, con validación por consumidor en CONT-07/08. No fabricar un centro predeterminado ni eliminar referencias existentes. Sociedad/División siguen siendo fronteras operativas aunque no haya imputación.

## Estados independientes

1. Implementado: existen runtime, contratos, datos, permisos y evidencia. Una carpeta o manifest planned no cumple esta condición.
2. Disponible para el tenant: entitlement contractual vigente y activación del tenant conforme al contrato de cada capacidad.
3. Autorizado para el usuario: permiso puntual, membresía, tenant y alcance.
4. Configurado para operar: libro, periodos y mapeos válidos cuando el proceso realmente sea contable.

No confundir módulo habilitado con configuración lista. No crear libros para todas las Sociedades al crear una Sociedad. No activar Accounting como dependencia de Producción, Inventario, Ventas, Compras, RH, Mantenimiento o la estructura Admin. Dependencias operativas existentes entre esos módulos siguen vigentes.

## Accounting apagado

La operación sigue sus validaciones propias y conserva dimensiones, importes y snapshots que le correspondan. No llama de forma síncrona a Accounting para poder guardar. No exige cuentas ni periodo contable abierto, no genera pólizas ni corre workers de contabilización, cierres o mapeos para ese tenant. No crea una bandeja de errores contables por documentos producidos fuera del periodo habilitado.

Backend debe rechazar acceso contable directo sin habilitación; ocultar el menú no basta. Jobs, consumidores y reintentos también revalidan estado efectivo del tenant antes de producir efectos. Definir semántica de concurrencia entre desactivación y commit, sin efectos nuevos después del corte confirmado ni doble procesamiento al reactivar.

Conservar documentos y auditoría de sus dueños. El futuro outbox operativo puede existir por integraciones distintas de Accounting, pero no debe transformarse en una cola contable ilimitada para tenants que no usan ese módulo. Definir retención, cobertura y elegibilidad por fecha; no prometer replay de datos que no se conservaron.

## Activación, desactivación e historia

Activación futura: comprobar entitlement/runtime/permisos, seleccionar Sociedades, configurar libros y fecha de inicio, validar periodos/mapeos y ejecutar preflight. El alta de Sociedad no es el alta automática del libro. El documento operativo no queda contabilizado por activar un interruptor.

No contabilizar retrospectivamente toda la historia. Una carga inicial, saldos de apertura o importación histórica exige alcance y fecha explícitos, conciliación y ejecución idempotente; si faltan dimensiones o evidencia, queda excepción visible, sin imputación inventada.

Al desactivar, conservar libros, asientos y referencias; detener efectos nuevos y reintentos contables. El acceso de lectura/exportación histórica requiere política comercial y permisos explícitos: conservar datos no concede acceso a un módulo suspendido. Al reactivar, reconciliar el intervalo deshabilitado antes de decidir qué procesar; nunca ejecutarlo todo automáticamente.

## Responsables y aceptación futura

Administración negocio/técnico y Arquitectura custodian capacidades y activación; Contabilidad negocio/técnico custodia el ciclo contable opcional; Costos custodia catálogo y cálculo; Sinergia evita dependencias circulares; Seguridad cubre API/jobs; Datos/Custodio DB conserva historia; QA verifica combinaciones.

Matriz mínima de pruebas para futuros cortes: operación con Accounting apagado; Costos activo y Accounting apagado; catálogo básico autorizado sin analítica; Accounting habilitado sin configurar; permiso ausente; API directa; job en cola al apagar; suspensión concurrente; reactivación sin duplicados; historia sin replay automático; aislamiento entre tenants y Sociedades. No se declaran ejecutadas por escribir esta matriz.

## Evidencia del repositorio y límites

`frontend/microfrontends/contabilidad/manifest.js` y el manifiesto de Costos declaran planned. El catálogo MVP de Admin (`backend/services/admin-service/app/seeds/catalog.py`) no incorpora Accounting/Costing como módulos implementados. `AdminRepository._validate_module_transition` usa dependencias explícitas; `tenant_modules` distingue status y tenant_enabled. Tener todos los módulos actuales activos no habilita capacidades contables futuras.

CONT-03 prepara organización y sesión; CONT-04/05/07/08 deben respetar esta frontera. CONT-09 y CONT-12/14 deberán incorporar elegibilidad temporal y ciclo de activación antes de publicar efectos contables. Este corte sólo actualiza agentes, skills y diseño: no cambia API, código ejecutable, BD, seeds, runtime ni ambiente.
