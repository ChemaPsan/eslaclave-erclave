# Preparacion del candidato QA - 2026-08-21

> Estado: **LISTO PARA SOLICITAR `qa-build` / NO CONSTRUIDO / NO DESPLEGADO**. Este expediente no autoriza migraciones, configuracion del tenant, despliegues, cambios de trafico, Firebase Hosting ni carga de datos en QA.

## Resultado ejecutivo

El corte Local acumulado hasta CHG-224 queda preparado para convertirse en un candidato QA inmutable. El pipeline contempla cinco servicios reales: Admin, Produccion, Inventory, RH y Ventas. Tambien transporta las dependencias HTTPS necesarias para que Inventory valide recepciones de producto terminado contra Produccion y para que Ventas consulte sus autoridades.

La promocion aun es **NO-GO**. El SHA inmutable de `main`, la identidad `erclave-sales-qa` y las variables `QA_SALES_RUNTIME_SERVICE_ACCOUNT`/`QA_SALES_API_URL` ya existen y fueron verificados en CHG-225. El siguiente gate independiente es construir el candidato mediante `qa-candidate.yml`; migracion, configuracion, revisiones, trafico y frontend conservan aprobaciones separadas.

## Alcance del candidato

- Migraciones Alembic desde la revision QA `20260805_0013` hasta `20260821_0023`, en una cadena lineal.
- Expedientes de trabajadores, unidades de medida, preferencias modulares y recursos autoritativos.
- Ventas real: clientes, cotizaciones, pedidos, entregas, catalogos, identidad documental y endurecimiento CHG-204.
- Produccion: codigos de receta/orden, fases ponderadas, avance porcentual, consumo de reservas al iniciar y cierre coherente.
- Inventory: costo unitario base, conversiones compatibles, vinculo guiado de producto terminado y recepcion parcial/total confirmada por Almacenes.
- Administracion: folios/consecutivos por tenant y gobierno de modulos.
- Correcciones transversales de selectores, mensajes seguros, permisos, idempotencia, contratos y documentacion funcional.

No incluye Compras, Gastos, Costos, Contabilidad, Reportes especializados, devoluciones, facturacion/cobranza, lotes/series ni automatizacion de merma.

## Estado de QA comprobado en lectura

Comprobacion publica no destructiva del 2026-08-21:

| Componente | Estado observado |
|---|---|
| Firebase Hosting | `https://erclave.web.app`; publica cuatro URLs API y no publica Ventas |
| Admin | `health=ok`, `ready`, ambiente `qa`, version `4e9c6881dab61239f1abd5fff688019fdd697977` |
| Produccion | `health=ok`, `ready`, misma version |
| Inventory | `health=ok`, `ready`, misma version |
| RH | `health=ok`, `ready`, misma version |
| Ventas | No existe en el artefacto frontend QA vigente; se incorpora por primera vez en este candidato |
| Esquema | Revision documentada `20260805_0013`; no se consulto ni modifico Cloud SQL en esta actividad |

La configuracion activa de `gcloud` apunta a otro proyecto y no tiene acceso a `erclave`; CHG-225 uso explicitamente la cuenta QA ya autenticada `eslaclavecaf@gmail.com` y `--project=erclave`, sin cambiar la configuracion activa. Con ese actor se verificaron proyecto, IAM y URLs estables. Los healthchecks publicos tambien fueron exitosos.

## Cambios de preparacion CHG-224

1. `qa-candidate.yml` construye cinco imagenes por SHA y conserva sus digests.
2. `qa-release.yml` exige un manifiesto de cinco imagenes, despliega `sales-service-qa`, incluye Ventas en smoke/promocion y publica su URL en el frontend sanitizado.
3. Inventory recibe `ERCLAVE_PRODUCTION_SERVICE_URL`; Sales recibe las URLs de Admin, RH, Produccion e Inventory.
4. El runtime rechaza URLs locales para esas dependencias en QA/Produccion.
5. El seed estructural habilita solo `admin`, `production`, `inventory`, `hr` y `sales`; no carga transacciones ni maestros funcionales.
6. El plan IAM declara `erclave-sales-qa` con acceso minimo a Cloud SQL, al secreto de base y a las autoridades consumidas.

## Prerrequisitos y autorizaciones

| Paso | Requisito | Tipo de autorizacion | Estado |
|---|---|---|---|
| Consolidar codigo | PR revisado, CI verde y SHA de 40 caracteres | Git/PR | Completo: `adb134f7ac8b33b4a842d07db10c9b5f88525f2f` |
| Aprovisionar identidad Sales | Crear `erclave-sales-qa` y grants declarados | `qa-write` IAM | Completo y verificado; sin llaves de usuario |
| Variables GitHub | `QA_SALES_RUNTIME_SERVICE_ACCOUNT` y `QA_SALES_API_URL` | Configuracion QA | Completo y verificado |
| Construir imagenes | Ejecutar `qa-candidate.yml` con `BUILD_ERCLAVE_QA` | environment `qa-build` | No autorizado |
| Migrar base | Backup/checkpoint verificado y Alembic `0013 -> 0023` | environment `qa-database` | No autorizado |
| Configurar tenant | Sincronizar permisos y cinco entitlements reales | environment `qa-database` | No autorizado |
| Crear revisiones | Cinco servicios por digest, candidate tag | environment `qa-services` | No autorizado |
| Mover trafico | Smoke completo y rollback registrado | environment `qa-traffic` | No autorizado |
| Publicar frontend | Artefacto exacto con cinco URLs QA | environment `qa-frontend` | No autorizado |

No se permite copiar la base Local, sus IDs, contrasenas, tokens, datos demo ni movimientos a QA. Los datos funcionales de prueba se capturan despues de la promocion, con tenant confirmado y autorizacion especifica.

## Matriz minima de certificacion

| Area | Caso critico | Resultado esperado |
|---|---|---|
| Ambiente | `/health`, `/ready`, `/version` en cinco servicios | `qa`, base lista, mismo SHA y URL HTTPS publica |
| Aislamiento | Dos tenants y permisos negativos | Ninguna lectura/escritura cruzada; API rechaza aunque UI oculte |
| Admin | Folios administrados/manuales y concurrencia | Consecutivo unico, idempotente y auditable |
| RH | Alta de trabajador y puestos productivos | Validaciones accionables sin devolver PII; solo puestos marcados llegan a Produccion |
| Inventory | Articulos, costo/unidad, entradas/salidas, filtros y Kardex | Persistencia coherente y bloqueo de unidad con historia |
| Produccion | Receta aprobada, pesos 100%, validacion y orden | Recursos autoritativos explicados; codigo y snapshot correctos |
| Consumo | Orden pasa a En produccion | Una salida por reserva/almacen; reintento no duplica |
| Avance | Fases 0-100% y cierre | Avance general ponderado; no termina con fases menores a 100% |
| Producto terminado | Recepcion parcial y total desde Movimientos | Entrada al articulo vinculado, saldo pendiente correcto y sin excedentes |
| Ventas | Cliente -> Cotizacion -> Pedido -> Entrega | Persistencia real, identidad comercial/logistica y snapshots coherentes |
| Documentos | Identidad PDF tenant-safe | Sin HTML/script ejecutable, logo/tipografia/colores/pie correctos |
| Resiliencia | Doble clic, timeout y reintento | Sin duplicados; mensajes accionables; estados parciales reconciliables |
| Responsive/i18n | Escritorio y movil ES/EN | Selectores buscables, formularios y mensajes utilizables |

Los manuales funcionales de Produccion y Almacenes CHG-222 continúan vigentes; CHG-224 cambia el mecanismo de liberacion, no el comportamiento funcional del operador, por lo que no requiere una nueva version de esos Word.

## Orden gobernado de ejecucion futura

1. Publicar y revisar el PR; registrar SHA completo.
2. Aprovisionar identidad/variables faltantes de Ventas con evidencia.
3. Ejecutar `qa-candidate.yml`; conservar run ID y manifiesto por digest.
4. Verificar backup/checkpoint y aprobar `qa-database`.
5. Ejecutar migracion lineal y configuracion estructural idempotente.
6. Crear las cinco revisiones candidatas sin trafico cuando el servicio ya exista.
7. Ejecutar smoke contra URLs `candidate` y conservar respuesta de version.
8. Registrar revisiones de rollback y aprobar `qa-traffic`.
9. Construir/publicar el frontend sanitizado con cinco URLs.
10. Ejecutar la matriz funcional con datos ficticios autorizados y emitir go/no-go.

## Rollback

- Backend: devolver 100% del trafico a las cinco revisiones estables registradas antes de promover.
- Frontend: restaurar el release anterior de Firebase Hosting.
- Base: preferir `forward-fix`; restaurar backup solo mediante decision explicita. No ejecutar downgrade despues de admitir escrituras sin evaluar perdida de datos.
- Bootstrap de Ventas: al ser servicio nuevo, registrar su primera revision y definir si se deshabilita el entitlement o se retira trafico ante fallo.

## Escrituras externas realizadas

Ninguna. Esta preparacion solo modifico archivos del repositorio y consulto endpoints publicos de salud/version. No ejecuto workflow, migracion, seed, configuracion de tenant, despliegue, trafico ni Hosting.
