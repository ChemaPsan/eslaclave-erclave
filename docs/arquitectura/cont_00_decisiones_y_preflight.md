# CONT-00 — Decisiones concretas y preparación de la migración

**Cambio:** CHG-288; decisiones resueltas e implementación inicial en CHG-289

**Fecha:** 2026-09-22

**Estado:** CONT-00 cerrado por respuesta del usuario; CONT-01 implementado sólo en Local como expansión compatible.

**Plan rector:** [plan de preparación contable](plan_preparacion_contabilidad.md).

El usuario resolvió las tres preguntas: un Emisor puede tener varias Sociedades, cada Sociedad tiene un solo Emisor, los libros se llevan por Sociedad, el Centro de costos se da de alta desde Administración por División y su obligatoriedad fue precisada en CHG-296 por flujo de imputación habilitado; los maestros se asignan al Centro de costos de la División activa. La moneda base se configura, inicialmente MXN, y se permiten operaciones en otra moneda capturando tipo de cambio. Esta respuesta sustituye las propuestas anteriores de múltiples Emisores por Sociedad y libro por Emisor.

## 1. Glosario y decisiones vigentes de CONT-00

Las decisiones están cerradas para implementar el plan. Su alcance ejecutado se distingue del comportamiento futuro: CONT-01 aporta persistencia/importación, no formularios, Centros de costos ni asientos.

| ID | Regla de trabajo | Efecto y alcance |
|---|---|---|
| D01 | Corporativo es el tenant. Emisor es identidad fiscal; Sociedad es unidad de gestión; División pertenece a una Sociedad. | Cardinalidad aprobada: Emisor 1:N Sociedad 1:N División 1:N Centro de costos. |
| D02 | Cada Sociedad tiene exactamente un Emisor del mismo tenant. Libro a nivel Sociedad y moneda base configurada. | `societies.issuer_id` obligatorio; sin tabla muchos-a-muchos ni selector de Emisor por operación. Accounting queda pendiente de CONT-12. |
| D03 | Centro de costos obligatorio sólo por flujo de imputación habilitado (precisión confirmada CHG-296). Catálogo básico desde Administración por División, propiedad Costing; Sociedad derivada. Sin imputación habilitada no se exige centro por preparación. | Catálogo/pantalla en CONT-05; asignaciones de maestros en CONT-07; transacciones en CONT-08. Backend valida tenant, scope, División y estado; si el flujo exige centro, sin centro válido no se guarda la operación. Ver [política vigente](matriz_capacidades_organizacionales.md). |
| D04 | Pedido/requisición/orden de compra son compromisos sin póliza. Entrega registra costo; factura cliente, cartera/ingreso/impuestos; recepción proveedor, inventario/gasto contra recepción no facturada; factura proveedor, conciliación/pasivo/impuestos. Horas generan costeo, no nómina automática. | Es la secuencia propuesta por CONT-00. Se materializa en los ejemplos de la sección 2; no se crean eventos ni asientos en este cambio. |
| D05 | Moneda base configurable por Sociedad/libro, inicialmente MXN. Operación en otra moneda conserva importe/moneda original, tipo de cambio y conversión a base. Tipo capturado, positivo y auditable; sin proveedor automático en este corte. | CONT-01 persiste `base_currency=MXN` y valida catálogo Admin al importar. Conversión, Decimal/redondeo y snapshots se implementarán en sus cortes; no recalcular historia con moneda/tasa nuevas. |
| D06 | Transferencia simple entre Divisiones de la misma Sociedad; entre Sociedades, flujo intercompañía. | Conservar esta frontera del plan. No resolver el cambio de Sociedad con un movimiento de almacén ordinario. |
| D07 | Configuración con precedencia Corporativo → Sociedad → División y override explícito. Al confirmar un documento, guardar valores efectivos como snapshot. Las copias son explícitas e independientes del origen. | Concreta CONT-04/17. La lista de parámetros heredables y copiables se define por dueño; no copiar automáticamente recursos físicos, bancos ni usuarios. |
| D08 | Conservar origen y códigos existentes, con equivalencias explícitas para IDs normalizados. Razón social origina Sociedad con Emisor único; Sucursal origina División. | Importación Local implementada en CONT-01, sólo tras revisar hashes y resoluciones. No fusionar RFC ni asignar sucursales huérfanas silenciosamente. |

La superficie de alta de Centros de costos es Administración en CONT-05 Local; se conserva Costing como dueño técnico del catálogo mediante contrato, sin escrituras cruzadas. Admin posee Emisores, Sociedades y Divisiones; Accounting posee libros por Sociedad, cuentas y pólizas. Ningún servicio escribe tablas de otro ni crea FKs entre schemas. La integración de la pantalla Admin con el catálogo propietario ya está implementada en [CONT-05](cont_05_catalogo_centros.md).

## 2. Ejemplos de aceptación propuestos

Ejemplos sintéticos de software, con unidades monetarias abstractas y cuentas simbólicas. No fijan tasas fiscales, cuentas de un cliente ni reglas de cumplimiento. Los mapeos concretos se versionarán en Accounting.

| Hecho | Cargo | Abono | Condición de aceptación |
|---|---|---|---|
| Recepción de material por 100 | Inventario 100 | Recepción no facturada 100 | Documento, tenant, División, Centro de costos y evento trazables. |
| Factura del mismo material, base 100 e impuesto ilustrativo 10 | Recepción no facturada 100; impuesto configurado 10 | Proveedores 110 | Conciliar recepción y factura; el 10 es sólo dato de prueba. |
| Entrega con costo 60 | Costo de venta 60 | Inventario 60 | No reconocer ingreso a partir de cotización o pedido. |
| Factura de venta, base 100 e impuesto ilustrativo 10 | Clientes 110 | Ingreso 100; impuesto configurado 10 | Mantener evento de ingreso separado del costo de la entrega. |
| Consumo productivo de material por 40 | Producción en proceso 40 | Inventario de material 40 | Costo efectivo y dimensiones conservados; no recalcular con tarifa actual. |
| Reversa del consumo anterior | Inventario de material 40 | Producción en proceso 40 | Nuevo evento/asiento ligado al origen; repetición no duplica el efecto. |

Casos límite exigibles en los cortes correspondientes:

- evento repetido: una sola contabilización;
- periodo cerrado: pendiente explícito, sin cambiar fecha silenciosamente;
- referencia de otro tenant o División: rechazo antes de efectos;
- mapeo ausente o empatado: pendiente visible, sin cuenta elegida por inferencia;
- costo, moneda o tipo de cambio faltante: pendiente explicable, nunca cero inventado;
- Emisores con RFC igual: revisión y equivalencia explícita, no fusión automática;
- sucursal sin razón social: propuesta revisable de asignación, sin backfill automático;
- migración repetida: mismos IDs/equivalencias y conteos; cero duplicados;
- cambio del JSON después del preflight: reporte obsoleto; volver a comparar bajo transacción antes de escribir;
- cambios a configuración: afectan operaciones futuras; historia conserva snapshot.

## 3. Preflight implementado en CHG-288

Herramienta: [preflight_organization.py](../../tools/preflight_organization.py). Es un analizador de archivo local que no importa repositorios, no abre conexiones, no genera migraciones y no escribe datos. Revisa el JSON original, ya que `AdminRepository._normalize_organization_profile` filtra entradas que no sean objetos y puede ocultar anomalías para una migración.

Entrada explícita, obtenida por un procedimiento de lectura autorizado o construida como fixture sintético:

```json
{
  "tenant_id": "ten_739ee59d765d5e14818674800d",
  "organization_profile": {
    "corporate": {},
    "legal_entities": [],
    "branches": []
  }
}
```

El contenido de `organization_profile` debe ser el JSONB original, no la respuesta normalizada de sesión. La envoltura identifica el tenant esperado, pero no acredita por sí misma la procedencia o integridad de una exportación. No adjuntar exportaciones con datos personales al repositorio.

Ejecutar desde la raíz, sobre un archivo ya disponible:

```powershell
python tools/preflight_organization.py --input ruta/al/export.json --tenant-id ten_739ee59d765d5e14818674800d
```

El reporte contiene conteos de filas originales, rutas estructuradas, códigos, severidad y SHA-256 del archivo. No imprime nombres, RFC, correos, domicilios ni valores de extensiones desconocidas. No reemplaza ni normaliza el archivo. Rechaza claves JSON duplicadas, números no JSON, entrada inválida y discrepancia del tenant. Señala estados desconocidos, IDs repetidos, códigos por asignar o potencialmente coincidentes, referencias huérfanas, identidad fiscal incompleta y campos aún sin estrategia de conservación.

| Salida | Significado |
|---|---|
| `0 / clean` | No se detectaron anomalías de las reglas revisadas en ese archivo. No equivale a validación fiscal, migración lista ni CONT-00 aprobado. |
| `1 / review_required` | Requiere decidir códigos, asignaciones, conservación de extensiones o datos fiscales incompletos. |
| `2 / blocked` | Hay estructura inválida, IDs ambiguos, tenant distinto o referencias rotas. Entrada ilegible/inválida devuelve `invalid_local_export`. |

`database_checked` y `migration_authorized` siempre son falsos. Un archivo vacío de entidades puede ser estructuralmente correcto; el conteo no demuestra que el tenant esté listo para operar. Campos fiscales incompletos no se convierten en datos inventados. La herramienta no valida catálogos SAT ni pertenencia real consultando una base.

## 4. CONT-01 implementado: expansión e importación compatible

Implementación y procedimiento detallado: [CONT-01](cont_01_estructura_organizacional.md). El corte de persistencia comprende:

1. Modelos/migración Admin de `fiscal_issuers`, `societies`, `divisions`, `organization_imports` y `organization_legacy_mappings`. PK/UK/FK internas compuestas por tenant, código único y un solo `issuer_id` obligatorio por Sociedad.
2. Preflight offline y CLI Local de DB de sólo lectura por defecto. Para aplicar: hashes revisados, lock por tenant, bloqueo de fila original y nueva comprobación antes de escribir.
3. Propuesta de equivalencias por tenant, sin fusión de identidad fiscal ni asignaciones ambiguas. Las sucursales sin razón social necesitan resolución explícita antes del backfill.
4. Expansión compatible: JSON sigue siendo fuente operativa mientras no exista switch completo. No mantener dos autoridades divergentes; CONT-02 definirá escritura y proyección compatibles.
5. Backfill idempotente con huella de origen y bloqueo/control de cambios; abortar si el origen cambió desde la revisión o si existen conflictos con datos ya migrados.
6. Comparar IDs, estados, contactos, conteos y asociaciones; conservar extensiones hasta decidir destino. Ninguna pérdida silenciosa por normalización.
7. Upgrade/downgrade/re-upgrade y constraints probados con PostgreSQL Local. Antes de eliminar tablas con datos, validar que el downgrade no perderá escrituras nuevas.
8. Actualizar modelo de datos, diagrama, contexto y trazabilidad. Las APIs actuales continúan sin cambio hasta su corte propio.

CHG-288 no creó tablas. CHG-289 aplica en Local `20260922_0037`, posterior a `20260913_0036`, sin cambiar el JSON operativo. El tenant autorizado tiene cero razones sociales/sucursales; no se inventaron registros. Ese era el estado del corte CHG-289, no los pendientes actuales; consultar [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). QA continúa documentado en `20260913_0036` sin conexión ni modificación.

## 5. Validación y alcance

- CHG-288: archivos Local, sin DB. CHG-289: PostgreSQL Local `127.0.0.1:5434/erclave_local`, migración y pruebas transaccionales; sin Firebase, APIs ni recursos remotos.
- Tenant de ejemplos: `ten_739ee59d765d5e14818674800d`. Otros identificadores de tenant en pruebas son objetos en memoria para probar rechazo, sin fixtures persistidos.
- Pruebas del analizador: [test_organization_preflight.py](../../backend/services/admin-service/tests/test_organization_preflight.py), incluidas en el descubrimiento backend existente.
- Fichas consultadas: Administración negocio/técnica, Costos, Contabilidad, Datos/Custodio DB, Seguridad, QA y Arquitectura; son perspectivas documentales, sin delegación.
- Skills aplicadas: `erclave-feature`, `erclave-db-migration`, `erclave-environment-boundaries`.
- APIs afectadas: **Ninguna**. Sin contratos modificados ni endpoints invocados.

Las verificaciones de cada corte quedan en CHG-288/289 de [TRAZABILIDAD.md](../../TRAZABILIDAD.md). Las preguntas funcionales fueron respondidas; no volver a solicitarlas. CONT-02 debe completar APIs/formularios y el switch compatible antes de activar las tablas normalizadas como autoridad del runtime.
