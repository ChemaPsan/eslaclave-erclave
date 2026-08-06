# Fronteras para Local, QA y Produccion

> **Estado:** decisiones aprobadas; adopcion normativa en curso.  
> **Fecha:** 2026-08-03.  
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

## 4. Inventario actual confirmado

### 4.1 QA verificado al 3 de agosto de 2026

| Componente o capacidad | Estado confirmado | Evidencia o limite |
|---|---|---|
| Frontend QA | Activo | `https://erclave.web.app` respondio HTTP 200 |
| `admin-service-qa` | Activo | Cloud Run respondio HTTP 200 y reporto ambiente `qa` |
| `production-service-qa` | Activo | Cloud Run respondio HTTP 200 y reporto ambiente `qa` |
| Firebase Auth | Integrado | Login y sesion QA documentados |
| Cloud SQL `erclave_qa` | Migrado | Revision documentada `20260730_0011` |
| Administracion | Real QA | Tenant, sesion, permisos, roles, entitlements y organizacion |
| Productos y servicios | Real QA | API de Produccion desplegada |
| Recetas y versiones | Real QA | Integracion publicada y documentada |
| Ordenes de produccion | Parcial/local | No candidata a Produccion |
| `inventory-service` | Codigo y ejecucion local | No consta despliegue del proceso en QA |
| Schema `inventory` | Presente en QA | Catalogos documentados en cero registros |
| `hr-service` | Codigo y ejecucion local | No desplegado en QA |
| Schema `hr` | Presente en QA | Vacio; entitlement no activado |
| Ventas | Prototipo local | No candidata a Produccion |
| Compras, Gastos, Costos, Contabilidad y Reportes | Demo o futuro | Sin backend productivo certificado |
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

- `inventory-service-qa` solo despues de cumplir sus gates;
- `hr-service-qa` solo despues de cumplir sus gates y decidir el entitlement;
- Ventas y servicios futuros solo al cumplir su definicion de modulo real.

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

## 15. Cambios futuros propuestos para agentes y skills

Esta seccion describe cambios recomendados. No estan aprobados ni implementados.

### 15.1 Skill transversal propuesta

Crear `.agents/skills/erclave-environment-boundaries/SKILL.md` y activarla ante instrucciones como:

- "levanta el proyecto";
- "prueba en QA";
- "conecta a QA";
- "migra";
- "ejecuta el seed";
- "despliega";
- "pasa a Produccion".

La skill debera:

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

### 15.2 Otros cambios propuestos

- Agregar a `AGENTS.md` la definicion canonica de ambientes.
- Agregar las mismas preguntas obligatorias a Arquitectura, Datos, DB, Seguridad y QA/Release.
- Separar "local aislado" de "local conectado a QA".
- Actualizar `docs/arquitectura/qa_prod.md` con el inventario real.
- Actualizar la guia QA para Inventory y RH.
- Crear un manifest versionado de recursos permitidos por ambiente.
- Agregar un validador que detecte URLs QA/Prod en configuracion Local.
- Agregar un validador que detecte `localhost` en builds QA/Prod.
- Crear checklist y plantilla de promocion a Produccion.
- Identificar el workflow de GitHub Pages como publicacion de maqueta, no como pipeline productivo completo.
- Evitar autodeploy de `main` hacia QA si se adopta una promocion gobernada por releases.

## 16. Plan de adopcion propuesto

### Fase 0. Aprobacion conceptual

- Revisar este documento.
- Resolver las decisiones abiertas.
- Corregir alcance y terminologia.
- Aprobar o rechazar formalmente la propuesta.

### Fase 1. Fuente de verdad documental

- Integrar la definicion aprobada en `AGENTS.md` y `AGENTES.md`.
- Actualizar `qa_prod.md`, `ESTADO_ACTUAL.md`, `DECISIONES.md` y `PENDIENTES.md`.
- Registrar trazabilidad.

### Fase 2. Skills y validadores

- Crear `erclave-environment-boundaries`.
- Integrarla con `erclave-feature` y `erclave-db-migration`.
- Agregar manifest por ambiente.
- Agregar validadores de fronteras.

### Fase 3. Arranque local canonico

- Crear un comando unico de preflight y arranque.
- Consolidar variables locales.
- Bloquear QA y Prod.
- Emitir la matriz efectiva de servicios.
- Agregar comando de apagado local seguro.

### Fase 4. Pipeline QA

- Construir artefactos inmutables.
- Desplegar QA desde pipeline.
- Ejecutar migraciones controladas.
- Ejecutar smoke tests.
- Publicar evidencia de release.

### Fase 5. Preparacion de Produccion

- Crear proyecto y recursos productivos separados.
- Definir dominio, IAM, secretos, backups, RTO y RPO.
- Certificar el primer corte.
- Ensayar despliegue y rollback.
- Promover los mismos digests aprobados en QA.

## 17. Registro de decisiones

| Tema | Decision | Estado |
|---|---|---|
| Dominio QA | `erclave.web.app` continuara como QA; Produccion usara posteriormente un dominio comprado. | Aprobado |
| Proyectos GCP | QA y Produccion viviran en proyectos GCP distintos. | Aprobado |
| Autenticacion local | Local usara Firebase Emulator exclusivamente. | Aprobado |
| Local conectado a QA | Se permitira solo con autorizacion explicita para una necesidad y alcance concretos. | Aprobado |
| Alcance completo del primer release | Administracion, Backoffice, Produccion, Almacenes/Inventario, RH y Ventas. | Aprobado |
| Backoffice | Formara parte del primer release. | Aprobado |
| Recursos Humanos | Formara parte del primer release, sujeto a despliegue y certificacion previa en QA. | Aprobado |
| Inventario | Formara parte del primer release, sujeto a despliegue y certificacion previa en QA. | Aprobado |
| RPO productivo | 15 minutos. | Aprobado |
| RTO productivo | 2 horas. | Aprobado |
| Infraestructura RTO/RPO | Se planeara antes del release, pero no se implementara hasta autorizar la fase de Produccion. | Aprobado |
| Aprobador funcional, datos, seguridad y release | El usuario propietario aprobara directamente. | Aprobado |
| Despliegue automatico del frontend | Solo podra ejecutarse despues de pruebas locales y aprobacion directa del usuario. | Aprobado |

### 17.1 Decisiones todavia requeridas

1. Definir dominio productivo cuando sea adquirido.

## 18. Criterio para aprobar esta propuesta

La propuesta puede pasar de borrador a decision vigente cuando:

- el usuario resuelva las decisiones abiertas;
- Arquitectura, Datos, Seguridad y QA/Release validen sus fronteras;
- se acuerde el primer corte productivo;
- se defina la politica de local conectado a QA;
- se identifiquen responsables de aprobacion;
- el documento sea incorporado a las fuentes normativas y a las skills mediante un cambio posterior autorizado.
