# Fronteras para Local, QA y Produccion

## CC-21 - CHG-325 - Local

Costo estimado de cotizaciones implementado sobre PostgreSQL Local, migracion `20261014_0062` up/down/up y tenant autorizado. Production confirma costo por producto/Division en moneda base de Sociedad. Sales conserva tasa explicita, vista previa y snapshot al aprobar; pedido hereda el snapshot. Falta de costo o tasa permite aprobar con costo/margen estimados nulos. Historia previa queda nullable, sin backfill ni reinterpretacion. No ejecutar migracion ni seed en QA/Produccion por este corte; CC-19 y aceptacion CC-20 pendientes. Accounting apagado.

## CC-18 - CHG-323 - Local

Folios de Puestos RH, movimientos Inventory, proveedor/requisicion/orden/recepcion Purchasing y orden Maintenance conectados con Admin. Migracion `20261014_0061` y pruebas focales solo sobre PostgreSQL Local con tenant autorizado. No ejecutar migracion ni seed en QA/Produccion por este corte; promover solo mediante aceptacion CC-20 y autorizacion de ambiente. Accounting permanece apagado. Historia conserva codigos previos; manuales Word esperan regeneracion y revision visual.

## CC-15 · CHG-319 · Local

[Compras por División](cont_08_compras_contexto.md): Purchasing conserva contexto de requisición/OC/recepción y condiciones explícitas del proveedor congeladas. Admin autoriza; Inventory conserva validación/costo/proof CC-14. Migración `20261012_0058` nullable sin backfill, downgrade protegido con historia. Accounting apagado, sin QA; CC-16 implementado Local CHG-320; CC-17/18 y CC-19/20 abiertos.

## CC-14 · CHG-317 · Local

[Productores, transferencias y sobrantes](cont_08_inventario_productores.md) implementados: Inventory conserva contexto/costo de Purchasing/Maintenance y transferencias misma Sociedad; proofs autenticados, alcance y reintentos. Migración `20261012_0057` nullable sin backfill, downgrade protegido con historia. Sin QA ni Accounting; CC-16 integral y CC-19/20 siguen abiertos; CC-15 implementado CHG-319.



## Estado y fuentes de vigencia

La conciliación por submódulo vive en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md); [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md) distingue Local de QA y [PENDIENTES](../contexto/PENDIENTES.md) fija la continuación. Evidencia de cada corte en [TRAZABILIDAD](../../TRAZABILIDAD.md). No sumar pendientes históricos como trabajo nuevo.

Organización/sesión, [centros CONT-05](cont_05_catalogo_centros.md), asignaciones CONT-07 y [condiciones explícitas sin herencia](cont_07_commercial_condiciones.md) ya están implementados Local. CONT-04 es parcial y CONT-06 sigue abierto. CONT-08 conserva [cotización](cont_08_cotizaciones_contexto.md) → [pedido](cont_08_pedidos_contexto.md), [servicios](cont_08_servicios_contexto.md), [stock/entrega y movimientos manuales](cont_08_stock_contexto.md). [Producción manual CHG-313](cont_08_produccion_contexto.md) y [fabricación comercial CHG-315](cont_08_fabricacion_contexto.md) conectan contexto, recursos, recepción y entrega/costo; recorrido HTTP Local real aprobado, aceptación transversal CC-20 pendiente.

Política CHG-309 confirmada: costos y tarifas en moneda base de Sociedad; documento en otra moneda conserva original, tasa explícita y convertido. Compras CC-15 implementado Local CHG-319; Mantenimiento CC-16 implementado Local CHG-320; Servicios CHG-314 y productores Inventory CHG-317 se conservan; no reinterpretar historia. Analítica Costing y Accounting permanecen planned. Datos reales y aceptación integrada siguen abiertos; estos cortes no fueron promovidos a QA.

## Integración operativa vigente CHG-313/314

[Tarifas CC-10](cont_08_tarifas_capacidad.md), [orden manual CC-11](cont_08_produccion_contexto.md) y [moneda Servicios CC-08](cont_08_servicios_contexto.md) se conservan. CHG-315 conecta [fabricación comercial CC-12](cont_08_fabricacion_contexto.md): prueba Sales, conversión única, conciliación de recepción real y entrega/costo. Head Local0056, sin backfill; recorrido HTTP real aprobado con 60MXN→3USD y limpieza de fixtures verificada. Cada dueño escribe sus tablas; Admin autoriza. Accounting apagado, datos reales CC-19/aceptación transversal CC-20 y QA pendientes.

## Registro de cortes (evidencia histórica)

Los apartados fechados conservan el alcance de su corte; los números de revisión y pendientes citados no son el estado actual.

## Actualización CHG-308 · 2026-10-07

Local `20261007_0050` migrado up/down vacío/up en loopback 5434 y tenant autorizado. Sin backfill ni QA. Preparación Production sin nueva UI ni fabricación dimensionada habilitada. Ver docs/arquitectura/cont_08_produccion_contexto.md.


## Actualización CHG-307 · 2026-10-05

Local head `20261005_0049`, migración probada sólo en loopback 5434 y tenant autorizado. Código stock/moneda no promovido a QA; fixtures con rollback, sin backfill. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


## Actualización CHG-306 · 2026-10-05

Local head `20261005_0048` probado upgrade/downgrade vacío/upgrade en loopback 5434/erclave_local, tenant autorizado. QA/Producción intactos. Inventory requiere destino Sales explícito para futura promoción; no se usó QA.


## Actualización CHG-305 · 2026-10-05

CHG-305 sin migración (head Local 0047); pruebas de servicios en tenant autorizado con rollback y APIs/Emulator loopback. QA/Producción intactos.


## Actualización CHG-304 · 2026-10-05

Local head 20261005_0047, loopback 5434/erclave_local y tenant autorizado; fixtures con rollback, sin datos dimensionados permanentes. QA/Producción intactos.


## Actualización CHG-303 · 2026-10-05

Local head 20261005_0046 aplicado sólo en loopback 5434/erclave_local, tenant autorizado, fixtures con rollback. QA/Producción intactos.



**Corte Local CHG-292 (2026-09-25):** Alembic `20260925_0038`, APIs/UI organizacionales y autoridad normalizada activadas sólo en `127.0.0.1:5434/erclave_local`, tenant demo autorizado. Admin en 8000 usa Firebase Auth Emulator demo-erclave; frontend en 4173. Doce permisos nuevos y grants sólo para el Owner de ese tenant. Ninguna conexión, migración ni promoción QA/Producción en este corte; la revisión QA documentada se mantiene. [Detalle CONT-02](cont_02_administracion_organizacional.md).

> **Estado:** decisiones aprobadas e implementadas en agentes, skills, validadores y pipeline QA.
> **Fecha:** 2026-08-12.
> **Autor del analisis:** Arquitectura transversal ERClave.
> **Efecto normativo:** fuente transversal de fronteras. Este documento no autoriza por si mismo despliegues, migraciones, seeds, cargas de datos ni cambios de infraestructura.

## 1. Objetivo

Definir fronteras inequívocas para los ambientes Local, QA y Produccion, de manera que:

- "levantar en local" nunca implique conectarse silenciosamente a QA;
- se pueda identificar con precision que capacidades estan realmente desplegadas en QA;
- se conozcan los requisitos para promover un corte a Produccion;
- los agentes y skills transversales puedan aplicar las mismas reglas operativas;
- ninguna operacion sobre QA o Produccion ocurra sin autorizacion explicita, evidencia y rollback.

## 2. Hallazgo principal

La documentacion actual mezcla topologia de ejecucion y frontera de datos. Un proceso puede ejecutarse en `127.0.0.1` y, al mismo tiempo, conectarse a Cloud SQL QA o Firebase QA.

Por tanto:

> Un proceso en localhost no es necesariamente parte del ambiente Local.

La frontera debe definirse por el conjunto completo de recursos utilizados:

```text
codigo + configuracion + identidad + datos + secretos + integraciones + observabilidad
```

Si cualquiera de esos recursos pertenece a QA, la ejecucion debe denominarse **local conectado a QA**, nunca simplemente **local**.

## 3. Modelo recomendado de ambientes

| Ambiente | Proposito | Codigo | Datos | Autenticacion | Integraciones |
|---|---|---|---|---|---|
| Local aislado | Desarrollo, debugging y pruebas manuales | Working tree local | PostgreSQL local, fixtures y mocks | Firebase Emulator | Mocks y fakes |
| QA | Validacion integrada del candidato a release | Artefactos candidatos versionados | Cloud SQL QA y datos ficticios controlados | Firebase QA | Servicios QA y sandboxes |
| Produccion | Operacion real de clientes | Los mismos artefactos aprobados en QA | Cloud SQL Prod | Firebase/Identity Prod | Cuentas productivas |

### 3.1 Regla de separacion

- Local, QA y Produccion no comparten bases de datos.
- QA y Produccion no comparten secretos, cuentas de servicio ni integraciones.
- Produccion no depende de recursos QA.
- Local no consume recursos QA o Prod por defecto.
- Toda excepcion debe nombrarse, justificarse y autorizarse expresamente.

## 4. Inventario documentado por ambiente

### 4.1 QA: release estable anterior y migracion observada CHG-336

[Release CHG-280](../operaciones/release_qa_20260914.md): PR #15 fusionado, SHA `e57237fe90319f88e1db8ed8d2e686604d2d9c54`, siete servicios y Hosting, Alembic `20260913_0036`. Es evidencia registrada, no una comprobación remota de esta auditoría. [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md) es autoridad para actualizaciones posteriores.

Actualizacion19oct2026: Cloud SQL head0062 observado por inspector gobernado;7estables mantienen e572/Hosting previo, candidatos8 SHA6312 probados tecnicamente. Costing bootstrap nuevo100%; sin promocion conjunta ni UAT. [Registro CHG-336](../operaciones/promocion_qa_20261019.md). El0036 del release14sept anterior es historico, no head actual.

| Componente o capacidad | Estado confirmado | Evidencia o limite |
|---|---|---|
| Frontend QA | Activo | `https://erclave.web.app` respondio HTTP 200 |
| `admin-service-qa` | Activo | Cloud Run respondio HTTP 200 y reporto ambiente `qa` |
| `production-service-qa` | Activo | Cloud Run respondio HTTP 200 y reporto ambiente `qa` |
| Firebase Auth | Integrado | Login y sesion QA documentados |
| Cloud SQL `erclave_qa` | Migrado CHG-336, sin promocion conjunta | Revision documentada `20261014_0062`; inspector39212276418 SUCCESS06:57:54Z. Perfil/Owner/scopes/15secuencias previas preservados; autoridad organizacionalfalse/tablas vacias |
| Administracion | Real QA | Tenant, sesion, permisos, roles, entitlements y organizacion |
| Productos y servicios | Real QA | API de Produccion desplegada |
| Recetas y versiones | Real QA | Integracion publicada y documentada |
| Ordenes de produccion | Real QA | Ciclo base con reservas/entrega de materiales; la fabricación por Sociedad/División sigue sólo en preparación Local |
| `inventory-service` | Activo QA | Servicio real sobre el SHA certificado vigente |
| Schema `inventory` | Presente en QA | Head DB actual `20261014_0062`, migracion CHG-336 observada; runtime estable previo y candidato separado, sin UAT nueva por este DDL |
| `hr-service` | Activo QA | Servicio real y entitlement estructural activo |
| Schema `hr` | Presente en QA | Head DB actual `20261014_0062`, migracion CHG-336 observada; runtime estable previo y candidato separado, sin UAT nueva por este DDL |
| Ventas | Activo QA | Servicio real; activacion efectiva depende del entitlement |
| Compras | Activo QA | `purchasing-service-qa`, schema propio; Inventory interviene cuando la compra recibe bienes inventariables |
| Mantenimiento | Activo QA | `maintenance-service-qa`, schema propio y dependencias RH e Inventory |
| Gastos, Costos, Contabilidad y Reportes | Demo o futuro | Sin backend certificado en QA |
| Infraestructura de Produccion | No confirmada | No hay evidencia documental de ambiente productivo desplegado |

### 4.2 Interpretacion obligatoria

La existencia de un schema o migracion en Cloud SQL QA no significa que el servicio este desplegado ni que el modulo sea operable.

Un modulo solo se considera real en un ambiente cuando existen y estan validados:

1. frontend consumidor;
2. servicio backend dueño;
3. persistencia y migraciones;
4. autenticacion y autorizacion;
5. entitlement;
6. contratos;
7. pruebas;
8. observabilidad;
9. operacion y rollback.

## 5. Definicion de "levantar en local"

Por defecto, la instruccion **levantar el proyecto en local** debe significar **Local aislado**.

### 5.1 Componentes

| Componente | Direccion recomendada | Datos efectivos | Auth |
|---|---|---|---|
| Frontend | `127.0.0.1:4173` | APIs y mocks locales | Firebase Emulator |
| Admin API | `127.0.0.1:8000` | `erclave_local` | Token del Firebase Emulator + autorizacion ERClave local |
| Production API | `127.0.0.1:8002` | `erclave_local` | Contexto autorizado por Admin local |
| Inventory API | `127.0.0.1:8004` | `erclave_local` | Contexto autorizado por Admin local |
| HR API | `127.0.0.1:8006` | `erclave_local` | Contexto autorizado por Admin local |
| PostgreSQL | `127.0.0.1:5434` | Datos sinteticos | Credencial local |

### 5.2 Secuencia esperada

1. Recuperar contexto del repositorio.
2. Revisar `git status --short`.
3. Identificar el flujo o modulo solicitado.
4. Verificar que toda URL de base y API sea local.
5. Verificar `ERCLAVE_ENVIRONMENT=local`.
6. Verificar que la autenticacion use exclusivamente Firebase Emulator y que la autorizacion se resuelva en `admin-service` local.
7. Levantar PostgreSQL local aislado.
8. Ejecutar migraciones solamente sobre `erclave_local` cuando sean necesarias y esten autorizadas.
9. Aplicar solamente fixtures o seeds locales idempotentes.
10. Levantar siempre `admin-service`.
11. Levantar unicamente los servicios requeridos por el flujo.
12. Mantener en mock los modulos sin backend real.
13. Ejecutar healthchecks.
14. Validar `session/context` con el tenant demo autorizado.
15. Entregar una matriz final de procesos y dependencias efectivas.

### 5.3 Tenant local permitido

| Campo | Valor |
|---|---|
| Nombre | `ERClave Demo QA` |
| Tenant ID | `ten_739ee59d765d5e14818674800d` |

La coincidencia del tenant no autoriza por si misma operaciones sobre QA. En Local debe existir como dato sintetico dentro de `erclave_local`.

### 5.4 Acciones prohibidas por defecto

Al levantar Local no se debe:

- abrir Cloud SQL Auth Proxy;
- conectarse a Cloud SQL QA o Prod;
- consumir APIs QA o Prod;
- usar Firebase Auth QA o Prod;
- usar Secret Manager QA o Prod;
- ejecutar `gcloud` o `firebase deploy`;
- aplicar migraciones o seeds remotos;
- enviar correos reales;
- ejecutar webhooks reales;
- usar cuentas de pago productivas;
- copiar datos productivos;
- publicar, crear releases o modificar infraestructura.

## 6. Variante excepcional: local conectado a QA

Esta variante no debe inferirse de la frase "levantar en local".

Requiere que el usuario autorice explicitamente:

1. el recurso QA que se consumira;
2. si el acceso sera solo lectura o permitira escritura;
3. el tenant efectivo;
4. las rutas o acciones permitidas;
5. el periodo de la sesion;
6. cualquier migracion, seed o carga por separado.

Recomendacion:

> Permitir esta modalidad solamente para diagnostico o validacion controlada, preferentemente en modo de solo lectura.

La decision vigente para el flujo cotidiano es mantener Local completamente separado de QA y usar exclusivamente Firebase Emulator. La variante conectada a QA queda disponible solo mediante autorizacion explicita del usuario para una necesidad concreta.

El cierre debe enumerar todas las peticiones mutantes y escrituras externas realizadas.

## 7. Que debe levantarse en QA

QA debe usar una topologia equivalente a Produccion, con menor capacidad y recursos totalmente separados.

### 7.1 Componentes base

- frontend QA con identificacion visual inequívoca;
- backoffice QA;
- Firebase Auth QA;
- `admin-service-qa`;
- `production-service-qa`;
- Cloud SQL QA;
- Secret Manager QA;
- logs, metricas, errores y alertas QA;
- integraciones sandbox;
- Storage y Pub/Sub QA cuando los contratos los requieran.

### 7.2 Servicios condicionados

- `inventory-service-qa` y `hr-service-qa` ya cumplieron sus gates y estan activos;
- Ventas y servicios futuros solo se activan al cumplir su definicion de modulo real.

### 7.3 Datos permitidos

- tenant demo autorizado;
- tenants desechables y controlados para pruebas de aislamiento;
- datos ficticios;
- seeds administrativos minimos, versionados e idempotentes;
- datasets de volumen expresamente autorizados y con limpieza documentada.

No deben copiarse datos de Produccion salvo un proceso formal de anonimizacion, minimizacion y aprobacion.

## 8. Que debe levantarse en Produccion

Produccion debe contener unicamente capacidades completas, aprobadas y operables.

### 8.1 Componentes obligatorios

- frontend y backoffice productivos;
- autenticacion productiva;
- `admin-service` productivo;
- solamente los microservicios certificados;
- Cloud SQL Prod separado;
- Secret Manager Prod;
- backups y recuperacion a un punto en el tiempo;
- auditoria;
- observabilidad y alertas;
- correo e integraciones productivas;
- Storage y Pub/Sub productivos cuando apliquen.

### 8.2 Componentes prohibidos

No deben presentarse como operativos:

- modulos mock;
- datos de `localStorage` tratados como persistentes;
- acciones visuales sin backend;
- servicios parcialmente desplegados;
- entitlements que habiliten modulos no certificados;
- fixtures, seeds o cuentas demo.

### 8.3 Primer corte productivo

El primer release incluye:

- Administracion;
- Backoffice;
- Produccion;
- Almacenes e Inventario;
- Recursos Humanos;
- Ventas.

La inclusion de RH no autoriza su despliegue inmediato. Antes de Produccion debe desplegarse y certificarse en QA, activar su entitlement de forma controlada y aprobar sus pruebas funcionales, de permisos, aislamiento, migracion, observabilidad y rollback.

Cada modulo debe desplegarse y certificarse completamente en QA antes de su promocion. Los demas modulos y capacidades permanecen fuera del primer release.

## 9. Que se promueve de QA a Produccion

No se debe promover una rama ni reconstruir el codigo despues de aprobar QA. Se deben promover exactamente los mismos artefactos inmutables.

### 9.1 Artefactos promovibles

- imagen de contenedor de cada servicio identificada por digest;
- build estatico del frontend identificado por hash;
- contratos OpenAPI versionados;
- migraciones Alembic exactas;
- manifest de configuracion sin secretos;
- SBOM y resultados de analisis de dependencias;
- evidencia de `npm run verify`;
- pruebas unitarias, integracion, aislamiento y smoke QA;
- release notes;
- matriz de cambios;
- plan de migracion;
- plan de rollback;
- lista de flags y entitlements;
- dashboards, alertas y runbooks;
- aprobaciones funcional, tecnica, de seguridad y de datos.

### 9.2 Elementos que nunca se promueven

- datos QA;
- secrets QA;
- IDs de usuarios QA;
- estado de `localStorage`;
- fixtures o seeds demo;
- URLs QA;
- imagenes reconstruidas despues de aprobar QA;
- funcionalidades locales o hibridas sin certificar.

## 10. Gates de promocion

### 10.1 Entrada a QA

- PR revisado;
- `npm run verify` aprobado;
- OpenAPI, schemas, consumidores y pruebas alineados;
- migracion probada desde la revision anterior y sobre una base limpia;
- pruebas de aislamiento multitenant;
- pruebas negativas de autorizacion;
- escaneo de secretos y dependencias;
- artefacto versionado;
- plan de rollback;
- dataset y tenant QA declarados.

### 10.2 Salida de QA

- smoke tests P0 aprobados;
- casos funcionales aprobados;
- token ausente, token invalido, tenant no miembro, modulo inactivo y permiso faltante probados;
- aislamiento validado con al menos dos tenants;
- idempotencia y concurrencia comprobadas;
- metricas, logs y errores visibles;
- migracion validada con volumen representativo;
- cero defectos P0;
- defectos P1 aceptados expresamente;
- aprobacion funcional y de Arquitectura.

### 10.3 Entrada a Produccion

- mismo digest aprobado en QA;
- ventana y responsable definidos;
- backup vigente;
- restauracion comprobada;
- migracion compatible hacia atras;
- despliegue canary o gradual;
- smoke productivo no destructivo;
- monitoreo reforzado posterior;
- criterios objetivos de rollback.

## 11. Migraciones, seeds y rollback

### 11.1 Migraciones

Aplicar el patron:

```text
expand -> migrate -> contract
```

1. Agregar estructuras compatibles.
2. Desplegar codigo compatible con esquema viejo y nuevo.
3. Ejecutar backfill idempotente y observable.
4. Cambiar lecturas y escrituras.
5. Retirar la estructura anterior en otro release.

Cada migracion debe declarar:

- ambiente y base destino;
- revision actual y objetivo;
- backup;
- tiempo estimado y locks;
- volumen afectado;
- verificaciones posteriores;
- rollback o estrategia de `forward-fix`.

### 11.2 Seeds

| Tipo | Ambiente permitido | Uso |
|---|---|---|
| Seed estructural | Local, QA y eventualmente Prod por pipeline | Permisos y catalogos tecnicos minimos |
| Fixture local | Solo Local | Datos sinteticos de desarrollo |
| Dataset QA | Solo QA | Pruebas funcionales controladas |
| Seed demo | Nunca Prod | Tenant y cuentas de demostracion |

Los catalogos productivos deben tratarse como migracion o provisioning auditado, nunca como seed demo.

### 11.3 Rollback

- Codigo: regresar al digest anterior.
- Frontend: reactivar el artifact anterior.
- Configuracion: restaurar una version controlada.
- Datos: usar PITR, restauracion o `forward-fix`; no depender solamente de `downgrade()`.
- Funcionalidad: desactivar mediante flags o entitlements sin borrar datos.

### 11.4 Objetivos de recuperacion productivos

| Objetivo | Valor aprobado | Interpretacion |
|---|---:|---|
| RPO | 15 minutos | Ante un incidente, la perdida maxima aceptable de datos productivos es de 15 minutos. |
| RTO | 2 horas | El servicio productivo debe poder recuperarse dentro de un maximo de 2 horas. |

Estos objetivos aplican a Produccion. Su arquitectura debe planearse y validarse antes del primer release, pero la infraestructura correspondiente no se implementara hasta que el usuario autorice expresamente la fase productiva. QA debe permitir ensayar restauracion y procedimientos sin crear ni modificar anticipadamente recursos productivos.

## 12. Seguridad y fronteras

- Proyectos GCP separados para QA y Produccion.
- Cuentas de servicio distintas por servicio y ambiente.
- Secretos separados y fuera del repositorio.
- IAM de minimo privilegio.
- Cloud SQL sin exposicion publica amplia.
- CORS sin comodines en QA y Produccion.
- Logs sin tokens, passwords ni PII innecesaria.
- `X-Tenant-Id` selecciona contexto, pero nunca concede autoridad.
- Tenant y actor se resuelven mediante token y membresia.
- Todo repositorio filtra por `tenant_id`.
- Los comandos requieren auditoria, idempotencia y `correlation_id`.
- Ningun servicio escribe el schema de otro servicio.
- Una validacion automatica debe fallar si Local apunta a recursos QA o Prod.

## 13. Observabilidad

Cada servicio debe emitir como minimo:

- ambiente;
- servicio;
- version y revision;
- `correlation_id`;
- `tenant_id` pseudonimizado cuando aplique;
- endpoint u operacion;
- latencia;
- resultado;
- categoria de error.

QA y Produccion deben tener dashboards, alertas y retencion separados.

## 14. Ownership de promocion

| Rol | Responsabilidad |
|---|---|
| Arquitecto SaaS | Fronteras, arquitectura, promocion y excepciones |
| Arquitecto de datos | Modelo, migraciones y compatibilidad |
| Custodio DB | Preflight, backup, ejecucion y postcondiciones |
| Seguridad | IAM, secretos, auth, aislamiento y revision de logs |
| Dueño tecnico del modulo | Artifact, contratos, pruebas y smoke |
| Dueño funcional | Aceptacion del flujo |
| QA y Release | Gates, despliegue, monitoreo y rollback |

## 15. Adopcion en agentes y skills

Las fronteras ya estan implementadas mediante `AGENTS.md`, `AGENTES.md`, `$erclave-environment-boundaries`, `$erclave-qa-release`, `docs/operaciones/flujo_local_a_qa.md` y validadores del repositorio. Las reglas siguientes describen el comportamiento vigente.

### 15.1 Skills transversales vigentes

Activar `$erclave-environment-boundaries` y, para promociones, `$erclave-qa-release` ante instrucciones como:

- "levanta el proyecto";
- "prueba en QA";
- "conecta a QA";
- "migra";
- "ejecuta el seed";
- "despliega";
- "pasa a Produccion".

Las skills deben:

1. clasificar la operacion como lectura, escritura local, escritura QA o escritura Prod;
2. imprimir una matriz efectiva de dependencias;
3. verificar host, puerto, base, proyecto, ambiente y tenant;
4. rechazar recursos QA o Prod cuando se solicito Local;
5. ejecutar solo preflight cuando el usuario solicite un plan;
6. exigir autorizacion separada para deploy, migracion, seed y carga de datos;
7. exigir artefactos, evidencia y rollback;
8. declarar al cierre todas las escrituras externas;
9. detenerse ante discrepancias de ambiente;
10. impedir que `.env` o `localStorage` cambien silenciosamente la frontera.

### 15.2 Estado de adopcion

Ya estan implementados la definicion canonica, agentes transversales, separacion Local/QA, guia QA, workflow manual, bloqueo de configuracion Local remota y sanitizacion runtime del frontend. La promoción compensatoria de tráfico está implementada. Permanecen pendientes el manifest/provenance fuerte de recursos y el checklist productivo final.

## 16. Mantenimiento continuo

- Mantener `ESTADO_ACTUAL.md` como inventario mutable unico.
- Ejecutar `npm.cmd run validate:environment-boundaries` y `validate:local-qa-parity` en cada cambio de ambientes.
- Actualizar el pipeline, sus skills y validadores en el mismo corte.
- Resolver la deuda de atomicidad, provenance, frontend build-once y smoke autenticado antes de Produccion.

## 17. Registro de decisiones

| Tema | Decision | Estado |
|---|---|---|
| Dominio QA | `erclave.web.app` continuara como QA; Produccion usara posteriormente un dominio comprado. | Aprobado |
| Proyectos GCP | QA y Produccion viviran en proyectos GCP distintos. | Aprobado |
| Autenticacion local | Local usara Firebase Emulator exclusivamente. | Aprobado |
| Local conectado a QA | Se permitira solo con autorizacion explicita para una necesidad y alcance concretos. | Aprobado |
| Alcance completo del primer release | Administracion, Backoffice, Produccion, Almacenes/Inventario, RH y Ventas. | Aprobado |
| Backoffice | Formara parte del primer release. | Aprobado |
| Recursos Humanos | Forma parte del primer release y su servicio ya fue desplegado/certificado estructuralmente en QA. | Aprobado y cumplido en QA |
| Inventario | Forma parte del primer release y su servicio ya fue desplegado/certificado estructuralmente en QA. | Aprobado y cumplido en QA |
| RPO productivo | 15 minutos. | Aprobado |
| RTO productivo | 2 horas. | Aprobado |
| Infraestructura RTO/RPO | Se planeara antes del release, pero no se implementara hasta autorizar la fase de Produccion. | Aprobado |
| Aprobador funcional, datos, seguridad y release | El usuario propietario aprobara directamente. | Aprobado |
| Despliegue automatico del frontend | Solo podra ejecutarse despues de pruebas locales y aprobacion directa del usuario. | Aprobado |

### 17.1 Decisiones todavia requeridas

1. Definir dominio productivo cuando sea adquirido.

## 18. Criterio de mantenimiento

Toda modificacion de ambientes debe actualizar este documento, agentes, skills, validadores, runbooks y trazabilidad en el mismo corte; Produccion continúa bloqueada hasta autorizacion explicita y certificacion completa.


## Historial de candidato de continuidad CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Historial de release QA verificado CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff histórico: `docs/contexto/REANUDACION_CHG269.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.
