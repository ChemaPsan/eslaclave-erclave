# ERClave — Requerimientos no funcionales, infraestructura y arquitectura SaaS

## 1. Objetivo del documento

Este documento complementa el documento base de ERClave con consideraciones no funcionales, arquitectura técnica, infraestructura, seguridad, autenticación, ambientes, modularidad, suscripciones, integraciones y criterios iniciales para operar el sistema como un SSaaS escalable.

El propósito es definir una base técnica que permita construir ERClave como una plataforma modular, segura, extensible y de bajo mantenimiento operativo.

---

## 2. Naturaleza del producto

ERClave será un producto **SaaS multi-tenant**.

Esto significa que:

- varios clientes podrán operar dentro de una misma plataforma;
- cada cliente deberá estar aislado lógica y operativamente;
- cada cliente tendrá sus propios usuarios, módulos, permisos, configuración, datos y planes contratados;
- la infraestructura deberá crecer bajo demanda;
- el producto deberá poder activar o desactivar módulos según el plan, contrato o configuración comercial;
- el sistema deberá permitir integraciones externas mediante APIs controladas, seguras y medibles.

### Conceptos principales

| Concepto | Descripción |
|---|---|
| Tenant | Cliente o empresa que usa ERClave. |
| Centro de negocio | Unidad operativa dentro de un cliente. Puede representar sucursal, planta, fábrica, línea de negocio o unidad administrativa. |
| Corporativo | Nivel superior que agrupa varios centros de negocio de un mismo cliente. |
| Usuario cliente | Usuario creado dentro del tenant de un cliente. |
| Administrador EsLaClave | Usuario interno de EsLaClave con acceso a consola administrativa global. |
| Módulo | Bloque funcional principal, por ejemplo Producción, Almacenes, Ventas o Gastos. |
| Submódulo | Funcionalidad interna de un módulo, por ejemplo Recetas, Órdenes de Producción o Catálogo de Recursos. |
| App externa | Aplicación de terceros o del propio cliente que consume las APIs de ERClave. |

---

## 3. Idiomas e internacionalización

Todo el sistema deberá soportar al menos:

- Español.
- Inglés.

### Requerimientos

- La interfaz deberá permitir cambiar de idioma.
- El idioma podrá definirse por usuario.
- El tenant podrá tener un idioma predeterminado.
- Los textos visibles no deberán estar escritos directamente en el código de interfaz.
- Los correos, notificaciones, reportes y documentos exportables deberán poder generarse en el idioma configurado.
- Las fechas, monedas, separadores numéricos y formatos deberán adaptarse a la región del usuario o tenant.

### Recomendación técnica

Implementar internacionalización desde el inicio usando archivos de traducción por clave.

Ejemplo conceptual:

```text
production.orders.title = Ordenes de producción
production.orders.title = Production orders
```

No se recomienda dejar la traducción para una etapa posterior, porque afecta pantallas, validaciones, correos, reportes, documentos y nombres comerciales de módulos.

---

## 4. Elasticidad, escalabilidad y bajo mantenimiento

ERClave deberá diseñarse con una arquitectura elástica, capaz de crecer automáticamente según demanda y reducir capacidad cuando la demanda baje.

### Objetivos

- Evitar administración manual de servidores.
- Reducir mantenimiento de infraestructura.
- Soportar crecimiento gradual por clientes, usuarios, módulos e integraciones.
- Pagar de forma más proporcional al uso real.
- Separar componentes críticos para escalar cada parte según su carga.

### Recomendación principal

Usar una arquitectura **cloud managed / serverless-first**.

Esto no significa que todo deba ser funciones aisladas, sino que la infraestructura base debe apoyarse en servicios administrados con escalamiento automático.

### Arquitectura recomendada

| Capa | Recomendación |
|---|---|
| Frontend web | Firebase Hosting o Cloud Run con Cloud CDN. |
| Backend API | Python con FastAPI sobre Cloud Run. |
| Gestión de APIs | Apigee para APIs públicas/comerciales; Google Cloud API Gateway como opción ligera inicial. |
| Base de datos principal | Cloud SQL for PostgreSQL; Cloud Spanner si se requiere escala horizontal global. |
| Archivos | Cloud Storage para PDFs, XML, adjuntos y exportaciones. |
| Colas/eventos | Pub/Sub, Eventarc, Cloud Tasks y Cloud Scheduler. |
| Autenticación | Google Cloud Identity Platform con OIDC/OAuth 2.0. |
| Autorización fina | RBAC/ABAC en aplicación, apoyado por IAM donde aplique. |
| Observabilidad | Cloud Logging, Cloud Monitoring, Cloud Trace, Error Reporting y OpenTelemetry. |

---

## 5. Lenguaje y framework recomendados

### Recomendación

La mejor opción inicial para el backend funcional es **Python con FastAPI**.

### Motivos

- Python permite desarrollo rápido y claro.
- FastAPI es adecuado para APIs modernas, documentación automática y validación de contratos.
- Tiene buen soporte para OpenAPI, lo cual ayuda a exponer APIs para clientes e integradores.
- Es compatible con despliegues en contenedores y funciones serverless.
- Facilita tareas futuras de reporteo, análisis de datos, automatización, lectura de XML/PDF e inteligencia operativa.
- El ecosistema de Python es fuerte para procesamiento documental, datos, reportes y posibles funciones de IA.

### Alternativas consideradas

| Opción | Ventaja | Riesgo o desventaja |
|---|---|---|
| Python + FastAPI | Rápido, moderno, excelente para APIs y datos. | Requiere disciplina en arquitectura para proyectos grandes. |
| Python + Django | Muy sólido para administración, ORM y producto monolítico modular. | Puede ser más pesado si se busca API-first puro. |
| Node.js + NestJS | Muy bueno para APIs empresariales y equipos frontend/fullstack. | Menos conveniente para procesamiento de datos/XML/PDF avanzado. |
| Java / Kotlin + Spring | Robusto para enterprise. | Mayor costo de desarrollo y operación inicial. |
| Go | Excelente rendimiento y bajo consumo. | Menor velocidad para construir funcionalidades administrativas complejas. |

### Decisión inicial recomendada

Usar:

- **Python 3.x**.
- **FastAPI** para backend API.
- **SQLAlchemy o SQLModel** para acceso a datos.
- **Alembic** para migraciones.
- **Pydantic** para validación.
- **OpenAPI** como contrato público de APIs.

Si se necesita una consola administrativa interna muy rápida, se puede evaluar Django Admin para herramientas internas, pero sin acoplar el producto principal a un admin monolítico rígido.

---

## 6. Infraestructura cloud recomendada

### Opción recomendada: Google Cloud

ERClave deberá construirse principalmente sobre el ecosistema de **Google Cloud**.

Google Cloud es una opción fuerte para ERClave por su integración entre servicios serverless, datos, analítica, APIs, identidad, observabilidad, automatización y herramientas administradas. También permite mantener una arquitectura elástica con bajo mantenimiento operativo usando servicios como Cloud Run, Cloud SQL, Cloud Storage, Pub/Sub, Apigee, BigQuery y Looker.

### Servicios sugeridos

| Necesidad | Servicio Google recomendado |
|---|---|
| CDN y hosting frontend | Firebase Hosting, Cloud Run, Cloud CDN y Cloud Load Balancing |
| Backend API | Cloud Run con Python/FastAPI |
| Funciones event-driven | Cloud Functions cuando convenga una función aislada |
| APIs públicas/comerciales | Apigee |
| APIs internas o MVP ligero | Google Cloud API Gateway |
| Base de datos relacional | Cloud SQL for PostgreSQL |
| Base de datos relacional a escala global | Cloud Spanner con interfaz PostgreSQL, si el volumen lo justifica |
| Cache | Memorystore for Redis / Valkey |
| Archivos XML/PDF | Cloud Storage |
| Eventos | Pub/Sub y Eventarc |
| Tareas asíncronas | Cloud Run Jobs, Cloud Tasks, Cloud Scheduler y Pub/Sub |
| Autenticación | Identity Platform |
| Identidad interna EsLaClave | Cloud Identity / Google Workspace |
| Autorización | RBAC/ABAC en aplicación + IAM para recursos cloud |
| Secretos | Secret Manager |
| Llaves | Cloud KMS |
| Seguridad perimetral | Cloud Armor + Cloud Load Balancing |
| Logs y métricas | Cloud Logging + Cloud Monitoring |
| Trazas y errores | Cloud Trace + Error Reporting + OpenTelemetry |
| Analítica/reportes | BigQuery + Looker / Looker Studio |
| ETL/ELT y datos | Dataflow, Dataplex, Dataform o BigQuery scheduled queries |
| CI/CD | Cloud Build, Artifact Registry y Cloud Deploy |
| Infraestructura como código | Terraform o Google Cloud Infrastructure Manager |

### Patrón recomendado

Para el MVP:

```text
Frontend web
  -> Firebase Hosting / Cloud CDN
  -> Google Cloud API Gateway o Apigee
  -> Cloud Run con Python FastAPI
  -> Cloud SQL for PostgreSQL
  -> Cloud Storage para documentos
  -> Pub/Sub / Cloud Tasks para procesos asíncronos
```

Para crecimiento:

```text
Frontend web
  -> Apigee
  -> Servicios por dominio
     - Producción
     - Almacenes
     - Costos
     - Ventas
     - Gastos
     - Contabilidad
     - Reportes
  -> Pub/Sub / Eventarc para eventos internos
  -> APIs públicas versionadas
  -> Portal de desarrolladores
  -> BigQuery / Looker para analítica
```

### Serverless vs contenedores

Para ERClave se recomienda una estrategia híbrida:

- **Cloud Run** para APIs principales en FastAPI, servicios internos, webhooks y workers con escalamiento automático.
- **Cloud Functions** para funciones pequeñas y event-driven cuando sea más simple que desplegar un servicio completo.
- **Cloud Run Jobs** para procesos batch, cierres, importaciones, exportaciones, procesamiento masivo de XML/PDF o tareas programadas.
- **Pub/Sub, Eventarc, Cloud Tasks y Cloud Scheduler** para desacoplar eventos, automatizaciones, tareas diferidas y procesos programados.

Esta combinación mantiene bajo mantenimiento sin encerrar todo el producto en un solo estilo de cómputo.

### Decisión recomendada para ERClave

Para el inicio se recomienda:

- Cloud Run como runtime principal del backend.
- Cloud SQL for PostgreSQL como base relacional inicial.
- Cloud Storage para documentos.
- Pub/Sub y Cloud Tasks para asincronía.
- Identity Platform para autenticación de usuarios.
- Apigee para la estrategia comercial de APIs, especialmente cuando se venda consumo a terceros.
- BigQuery y Looker/Looker Studio para reportería conforme crezca el volumen.

---

## 7. Modelo SaaS multi-tenant

ERClave deberá soportar multi-tenancy desde el diseño inicial.

### Recomendación inicial

Usar un modelo **pooled multi-tenant con aislamiento lógico fuerte**.

Esto significa:

- una misma infraestructura puede servir a varios clientes;
- las tablas principales tendrán `tenant_id`;
- cada consulta deberá filtrar obligatoriamente por tenant;
- se deberán implementar pruebas y controles para evitar fuga de datos entre clientes;
- los archivos en almacenamiento deberán separarse por tenant;
- los logs y auditoría deberán incluir tenant, usuario, app y ambiente.

### Posible evolución

Para clientes grandes o regulados, se podrá ofrecer aislamiento superior:

| Nivel | Descripción | Uso recomendado |
|---|---|---|
| Pooled | Varios tenants comparten infraestructura y base de datos con separación lógica. | MVP y clientes estándar. |
| Bridge | Infraestructura compartida, pero base de datos o esquema separado por cliente. | Clientes medianos con más control. |
| Silo | Infraestructura dedicada por cliente. | Clientes enterprise, requerimientos legales o alto volumen. |

La plataforma debe diseñarse para iniciar con pooled, pero sin cerrar la puerta a bridge o silo en planes superiores.

---

## 8. Modularidad funcional

ERClave será modular.

Deberá permitir:

- n módulos;
- n submódulos por módulo;
- activación o desactivación por tenant;
- activación o desactivación por plan contratado;
- permisos por rol, usuario, centro de negocio y corporativo;
- configuración por cliente sin modificar código;
- crecimiento progresivo del producto sin rehacer la arquitectura.

### Ejemplo

```text
Modulo: Producción
  Submódulo: Productos y servicios
  Submódulo: Recetas
  Submódulo: Ordenes de producción
  Submódulo: Asignación por área
  Submódulo: Costeo estimado

Modulo: Almacenes
  Submódulo: Catálogo de almacenes
  Submódulo: Entradas
  Submódulo: Salidas
  Submódulo: Movimientos
  Submódulo: Merma
```

### Requerimiento técnico

Debe existir un catálogo central de módulos y submódulos:

| Campo | Descripción |
|---|---|
| module_key | Identificador técnico estable. |
| name_es | Nombre en español. |
| name_en | Nombre en inglés. |
| status | Activo, beta, deprecated. |
| dependencies | Otros módulos requeridos. |
| plan_availability | Planes donde puede activarse. |

---

## 9. Roles, permisos y alcance organizacional

El sistema deberá controlar permisos en varios niveles.

### Niveles de alcance

| Nivel | Descripción |
|---|---|
| Plataforma | Acceso interno de EsLaClave. |
| Tenant | Acceso a toda la empresa cliente. |
| Corporativo | Acceso a grupo de centros de negocio. |
| Centro de negocio | Acceso limitado a una unidad operativa. |
| Área | Acceso limitado a una función interna, por ejemplo Corte o Calidad. |
| Usuario | Permisos específicos asignados a una persona. |

### Tipos de roles cliente

Ejemplos iniciales:

- Propietario del tenant.
- Administrador corporativo.
- Administrador de centro de negocio.
- Supervisor de producción.
- Operador.
- Consulta/reportes.
- Integrador técnico.

### Creación de usuarios por clientes

Algunos roles cliente podrán crear usuarios, pero siempre dentro de sus alcances.

Ejemplos:

- Un administrador corporativo puede crear usuarios para varios centros de negocio autorizados.
- Un administrador de centro de negocio solo puede crear usuarios dentro de su centro.
- Un supervisor puede invitar operadores si el tenant tiene habilitada esa capacidad.
- Ningún cliente puede crear usuarios administradores de EsLaClave.

### Recomendación de autorización

Combinar:

- **RBAC** para permisos por rol.
- **ABAC** para condiciones por tenant, centro de negocio, módulo, plan, ambiente y propiedad del recurso.

Ejemplo conceptual:

```text
El usuario puede aprobar una orden de producción si:
- pertenece al mismo tenant;
- tiene permiso production.orders.approve;
- el módulo Producción está activo;
- la orden pertenece a un centro de negocio dentro de su alcance;
- la orden está en estado programada o en producción.
```

---

## 10. Login y consola administrativa EsLaClave

Deberá existir un sistema paralelo de administración interna.

### Separación requerida

| Plano | Usuarios | Propósito |
|---|---|---|
| Aplicación cliente | Usuarios de clientes | Operación diaria del SaaS. |
| Consola EsLaClave | Administradores internos | Administración global, soporte, facturación, tenants, planes, módulos, auditoría e integraciones. |

### Reglas

- Ningún cliente deberá tener acceso a la consola administrativa de EsLaClave.
- La consola EsLaClave deberá tener dominio o ruta separada.
- Los administradores internos deberán usar autenticación fuerte con MFA obligatorio.
- Todas las acciones administrativas deberán registrarse en auditoría.
- El acceso de soporte a datos de cliente deberá ser controlado, justificado y auditable.

### Funciones de la consola EsLaClave

- Alta, baja y suspensión de tenants.
- Configuración de planes.
- Activación de módulos y submódulos.
- Gestión de límites por tenant.
- Administración de suscripciones.
- Revisión de consumo de APIs.
- Alta y revocación de apps externas.
- Impersonación controlada para soporte, si se decide permitirla.
- Auditoría de actividad.
- Gestión de ambientes de clientes.

---

## 11. Suscripciones y cobro

ERClave deberá poder cobrarse por suscripción.

### Modelos posibles

| Modelo | Descripción |
|---|---|
| Suscripción fija | El cliente paga una cuota mensual/anual por plan. |
| Por módulos | El cliente paga según módulos contratados. |
| Por usuarios | El precio depende del número de usuarios activos. |
| Por centros de negocio | El precio depende del número de centros habilitados. |
| Por consumo | El cliente paga por uso de APIs, automatizaciones, documentos procesados o volumen operativo. |
| Híbrido | Plan base más cargos variables por consumo. |

### Recomendación comercial inicial

Implementar un modelo híbrido:

- plan base por tenant;
- módulos incluidos según plan;
- usuarios incluidos con posibilidad de usuarios extra;
- centros de negocio incluidos con posibilidad de centros extra;
- consumo adicional para APIs, integraciones y automatizaciones.

### Cobro directo o desde la web

Se recomienda soportar ambos caminos:

1. **Cobro asistido por EsLaClave** para clientes empresariales, contratos especiales, pagos por transferencia o facturación manual.
2. **Cobro self-service desde la web** para clientes pequeños o medianos que puedan contratar con tarjeta o medios digitales.

### Recomendación técnica de pagos

Dentro del ecosistema Google, se deberá evaluar **Google Cloud Marketplace** para comercializar ERClave como SaaS B2B cuando el mercado objetivo sean empresas que ya compran soluciones mediante Google Cloud.

Google Cloud Marketplace puede ayudar con:

- publicación comercial del producto;
- venta a clientes empresariales;
- planes;
- contratos;
- suscripciones empresariales;
- relación con cuentas Google Cloud de clientes.

Para cobro self-service desde la web con tarjeta, métodos locales, facturación flexible o cobro directo fuera de Google Cloud Marketplace, es posible que se requiera integrar un proveedor de pagos especializado. Esta decisión deberá tomarse según país, medios de pago, facturación fiscal y estrategia comercial.

El sistema deberá contemplar:

- suscripciones;
- cambios de plan;
- portal de cliente;
- facturación recurrente;
- cargos de uso;
- webhooks de pagos;
- actualización de métodos de pago;
- cancelaciones y renovaciones.

El sistema interno de ERClave no debe depender únicamente del proveedor de pagos para saber qué puede usar un cliente. ERClave deberá tener una capa propia de **entitlements**.

### Entitlements

Los entitlements definen qué puede usar un tenant.

Ejemplos:

```text
tenant_abc:
  plan: profesional
  modules:
    production: true
    warehouses: true
    costs: false
  limits:
    users: 50
    business_centers: 3
    api_requests_monthly: 100000
```

---

## 12. APIs, integraciones y cobro por consumo

ERClave deberá exponer sus capacidades funcionales mediante APIs para que clientes e integradores puedan conectar otros sistemas sin intervención técnica constante de EsLaClave.

### Objetivo

Que casi todo el backend funcional pueda consumirse como API:

- productos;
- servicios;
- recetas;
- órdenes de producción;
- almacenes;
- movimientos;
- costos;
- ventas;
- gastos;
- reportes;
- catálogos;
- documentos;
- webhooks;
- automatizaciones.

### Modelo de consumo

El cliente principal tendrá funcionalidades base según su plan. Si requiere integraciones, automatizaciones o consumo externo, podrá contratar capacidad de API.

### Registro de apps externas

Deberá existir un portal o sección para registrar aplicaciones externas.

Cada app tendrá:

| Campo | Descripción |
|---|---|
| app_id | Identificador público de la app. |
| client_id | Identificador OAuth de cliente. |
| client_secret | Secreto de cliente, solo visible al crearse o rotarse. |
| tenant_id | Cliente al que pertenece o al que se conecta. |
| allowed_scopes | Permisos autorizados. |
| allowed_environments | Dev, QA, Prod del cliente. |
| status | Activa, suspendida, revocada. |
| rate_limit | Límite de solicitudes. |
| quota | Cuota mensual o por periodo. |
| webhook_urls | URLs de callback autorizadas. |

### Autenticación recomendada para APIs

Usar **OAuth 2.0 / OIDC** con tokens de corta duración.

En Google Cloud, la recomendación será:

- **Identity Platform** para autenticación de usuarios humanos.
- **Apigee** para administrar APIs comerciales, productos de API, apps de desarrollador, cuotas, analítica, seguridad y portal de desarrolladores.
- **IAM** para permisos entre servicios internos de Google Cloud.
- **Service accounts** para comunicación interna entre servicios propios.

#### Para usuarios humanos

Usar:

- Authorization Code Flow con PKCE.
- MFA configurable u obligatorio según rol.
- Refresh tokens con rotación.
- Sesiones con expiración.
- Detección de actividad sospechosa.

#### Para integraciones máquina a máquina

Usar:

- Client Credentials Flow.
- Client ID y Client Secret por app.
- Scopes específicos.
- Tokens JWT de corta duración.
- Rotación de secretos.
- Revocación inmediata.
- Rate limits y cuotas por app.

Para APIs públicas/comerciales, Apigee deberá administrar el registro de apps, credenciales, productos de API, cuotas, límites, analítica y políticas de seguridad. El backend en Cloud Run deberá validar el contexto recibido y aplicar autorización de negocio por tenant, módulo, plan y alcance.

### No usar API keys como autenticación principal

Las API keys pueden servir para identificación, medición o compatibilidad, pero no deben ser el mecanismo principal de seguridad.

El mecanismo principal debe ser:

- OAuth 2.0;
- JWT firmados;
- scopes;
- validación de tenant;
- autorización por políticas;
- límites de consumo;
- auditoría.

### Scopes recomendados

Ejemplos:

```text
production:recipes:read
production:recipes:write
production:orders:read
production:orders:write
warehouses:movements:read
warehouses:movements:write
reports:read
admin:users:read
```

### Validaciones obligatorias en cada request

Cada petición API deberá validar:

1. Token válido y no expirado.
2. Firma del token.
3. Emisor autorizado.
4. Audiencia correcta.
5. App activa.
6. Tenant autorizado.
7. Ambiente autorizado.
8. Scopes suficientes.
9. Módulo activo para el tenant.
10. Plan vigente.
11. Límite de consumo disponible.
12. Política de autorización del recurso.

### Cobro por consumo de APIs

Se deberá registrar consumo por:

- tenant;
- app;
- endpoint;
- módulo;
- ambiente;
- fecha/hora;
- tipo de operación;
- volumen procesado;
- resultado;
- costo unitario, si aplica.

Ejemplo:

```text
tenant_id: ten_123
app_id: app_456
environment: prod
endpoint: POST /production/orders
module: production
units: 1
billable: true
```

### Portal de desarrolladores

Para minimizar intervención técnica de EsLaClave, se recomienda crear un portal de desarrolladores donde el cliente pueda:

- consultar documentación API;
- crear apps;
- obtener client ID;
- rotar secretos;
- configurar scopes;
- ver consumo;
- configurar webhooks;
- consultar logs de integración;
- descargar SDKs o ejemplos;
- probar endpoints en sandbox;
- consultar errores comunes.

En el ecosistema Google, este portal deberá apoyarse preferentemente en las capacidades de Apigee Developer Portal o en un portal propio conectado con Apigee.

---

## 13. Seguridad

La seguridad debe ser parte central del diseño, no una capa posterior.

### Requerimientos mínimos

- HTTPS obligatorio.
- MFA para administradores EsLaClave.
- MFA configurable para clientes y obligatorio para roles sensibles.
- Tokens de corta duración.
- Refresh tokens con rotación.
- Secretos en vault administrado.
- Cifrado en reposo y en tránsito.
- Auditoría de acciones críticas.
- Separación estricta por tenant.
- Backups automáticos.
- Cloud Armor para protección perimetral.
- Rate limiting por usuario, app, tenant y endpoint.
- Protección contra fuerza bruta.
- Validación de archivos XML/PDF.
- Escaneo básico de archivos subidos.
- Principio de mínimo privilegio.
- Gestión de vulnerabilidades en dependencias.
- Ambientes separados.
- Uso de Secret Manager para secretos.
- Uso de Cloud KMS para llaves.
- Uso de IAM con mínimo privilegio.
- Uso de service accounts por servicio.
- Uso de VPC Service Controls cuando se requiera mayor aislamiento de datos.
- Uso de Security Command Center en etapas avanzadas.

### Auditoría requerida

Registrar al menos:

- inicio de sesión;
- cambios de contraseña;
- creación de usuarios;
- cambios de roles;
- activación o desactivación de módulos;
- alta o revocación de apps externas;
- generación y rotación de secretos;
- cambios de plan;
- acciones administrativas internas;
- acceso de soporte a datos de cliente;
- operaciones críticas de producción, almacén, ventas, gastos y costos.

---

## 14. Reportería y customización

La reportería deberá ser flexible y fácil de adaptar.

### Necesidades

- Reportes estándar por módulo.
- Reportes configurables por cliente.
- Filtros guardados.
- Exportación a Excel, CSV y PDF.
- Dashboards por rol.
- Métricas por centro de negocio.
- Reportes por rango de fechas.
- Reportes por producto, servicio, área, responsable o centro de costos.
- Posibilidad de adaptar reportes sin modificar código central.

### Recomendación técnica

Separar la reportería operativa de la base transaccional.

Arquitectura sugerida:

```text
Base transaccional
  -> Pub/Sub / Dataflow / procesos ELT
  -> BigQuery
  -> Looker / Looker Studio / APIs de reportes
  -> dashboards / exportaciones
```

### Opciones de infraestructura

| Opción | Uso recomendado |
|---|---|
| Vistas SQL y consultas parametrizadas | MVP y reportes básicos. |
| BigQuery | Reportes avanzados, alto volumen, histórico e inteligencia operativa. |
| Looker | BI empresarial, modelo semántico, métricas gobernadas y dashboards embebibles. |
| Looker Studio | Dashboards rápidos, internos o de bajo costo. |
| Motor propio de reportes | Cuando se requiera control total de permisos, formato y comercialización. |

### Recomendación por fases

Para MVP:

- reportes desde PostgreSQL con vistas controladas;
- exportaciones CSV/XLSX/PDF;
- filtros guardados por usuario.

Para crecimiento:

- réplica o pipeline hacia BigQuery;
- dashboards embebidos con Looker o portal propio;
- definición de métricas centralizada;
- report builder por cliente o por equipo EsLaClave.

---

## 15. Ambientes internos

ERClave deberá tener tres ambientes internos mínimos:

| Ambiente | Uso |
|---|---|
| Dev | Desarrollo activo, pruebas técnicas y experimentación. |
| QA | Validación funcional, pruebas de regresión, demos internas y pruebas antes de producción. |
| Prod | Operación real de clientes. |

### Reglas

- Dev, QA y Prod deben estar separados.
- Prod no debe compartir base de datos con Dev o QA.
- Las credenciales deben ser distintas por ambiente.
- Los secretos deben gestionarse por ambiente.
- Los dominios deben ser distintos.
- Los datos productivos no deben copiarse a Dev/QA sin anonimización.
- Los despliegues deben seguir un flujo controlado: Dev -> QA -> Prod.

---

## 16. Ambientes para clientes

ERClave deberá contemplar la posibilidad de habilitar ambientes para clientes.

### Ambientes posibles por cliente

| Ambiente cliente | Uso |
|---|---|
| Dev | Pruebas técnicas del cliente o integrador. |
| QA / Sandbox | Validación de procesos, integraciones y capacitación. |
| Prod | Operación real. |

### Recomendación

No todos los clientes necesitan tres ambientes. Debe ofrecerse según plan o contrato.

Ejemplo:

| Plan | Ambientes incluidos |
|---|---|
| Básico | Prod |
| Profesional | QA + Prod |
| Enterprise | Dev + QA + Prod |

### Consideraciones técnicas

Cada ambiente cliente debe tener:

- configuración independiente;
- apps externas independientes;
- tokens independientes;
- límites de consumo independientes;
- datos separados;
- URLs diferenciadas;
- auditoría por ambiente;
- posibilidad de resetear datos en Dev/QA sin afectar Prod.

Ejemplo de URLs:

```text
https://app.erclave.com
https://qa.app.erclave.com
https://dev.app.erclave.com

https://api.erclave.com
https://qa.api.erclave.com
https://dev.api.erclave.com
```

Para clientes enterprise se podrá evaluar:

```text
https://cliente.qa.erclave.com
https://cliente.erclave.com
```

---

## 17. Estrategia de datos

### Base principal

Usar **Cloud SQL for PostgreSQL** como base relacional principal para el MVP y primeras fases.

Motivos:

- integridad transaccional;
- modelo relacional adecuado para ERP/SaaS;
- soporte maduro para reportes;
- compatibilidad con herramientas BI;
- soporte para JSON cuando se requiera flexibilidad controlada;
- ecosistema amplio con Python.

### Evolución para escala alta

Si ERClave crece a un volumen donde Cloud SQL ya no sea suficiente por concurrencia, multi-región, disponibilidad global o particionamiento complejo, se deberá evaluar **Cloud Spanner**.

Cloud Spanner no debe ser la primera opción para el MVP por complejidad y costo, pero sí es una alternativa natural dentro de Google Cloud para una plataforma SaaS que requiera escala horizontal relacional.

### Separación por tenant

Cada tabla sensible deberá incluir `tenant_id`, salvo catálogos globales explícitos.

Ejemplos de tablas globales:

- módulos;
- submódulos;
- planes;
- idiomas;
- países;
- monedas.

Ejemplos de tablas por tenant:

- usuarios cliente;
- productos;
- recetas;
- órdenes;
- almacenes;
- movimientos;
- gastos;
- clientes comerciales;
- proveedores;

### Archivos

Los archivos deberán almacenarse fuera de la base de datos, en almacenamiento de objetos.

Ejemplo:

```text
gs://erclave-prod-documents/tenant_id/module/entity/file
```

---

## 18. Versionamiento de APIs

Las APIs públicas deberán estar versionadas.

Ejemplo:

```text
/v1/production/orders
/v1/warehouses/movements
```

### Reglas

- No romper contratos existentes sin nueva versión.
- Publicar documentación OpenAPI.
- Mantener changelog para integradores.
- Definir fechas de deprecación.
- Ofrecer ambiente sandbox para pruebas.

---

## 19. Observabilidad y operación

El sistema deberá poder responder rápidamente:

- qué tenant tiene errores;
- qué endpoint está fallando;
- qué integración consume demasiado;
- qué módulo tiene mayor carga;
- qué usuario ejecutó una acción;
- cuánto cuesta operar por tenant;
- qué ambiente está afectado.

### Métricas mínimas

- latencia por endpoint;
- errores por endpoint;
- consumo por tenant;
- consumo por app externa;
- uso de base de datos;
- tareas en cola;
- fallos de webhooks;
- costo estimado por servicio;
- uso de almacenamiento;
- actividad por módulo.

### Herramientas Google recomendadas

- Cloud Logging para logs centralizados.
- Cloud Monitoring para métricas, alertas y SLOs.
- Cloud Trace para trazabilidad de solicitudes.
- Error Reporting para agrupación de errores.
- Cloud Audit Logs para actividad administrativa y acceso a recursos.
- OpenTelemetry para instrumentación portable.

---

## 20. Cumplimiento y privacidad

Aunque el alcance legal deberá definirse posteriormente, desde el diseño inicial se deberán contemplar:

- protección de datos personales;
- control de acceso;
- bitácora de auditoría;
- retención y eliminación de datos;
- backups;
- restauración ante desastre;
- términos de servicio;
- aviso de privacidad;
- contratos de procesamiento de datos si aplica;
- localización de datos según mercado objetivo.

---

## 21. Recomendación de arquitectura inicial para MVP

### Stack recomendado

| Capa | Tecnología recomendada |
|---|---|
| Frontend | React / Next.js |
| Backend | Python + FastAPI |
| Base de datos | Cloud SQL for PostgreSQL |
| Infraestructura | Google Cloud serverless/managed |
| Runtime backend | Cloud Run |
| APIs | Apigee + OpenAPI; Google Cloud API Gateway para MVP ligero |
| Autenticación | Identity Platform |
| Autorización | RBAC/ABAC con políticas centralizadas |
| Archivos | Cloud Storage |
| Eventos | Pub/Sub + Eventarc |
| Jobs | Cloud Run Jobs + Cloud Tasks + Cloud Scheduler |
| Reportes MVP | PostgreSQL views + exportaciones |
| Reportes avanzados | BigQuery + Looker / Looker Studio |
| Pagos | Google Cloud Marketplace para SaaS B2B; proveedor externo solo si se requiere cobro web directo |
| Observabilidad | Cloud Logging, Cloud Monitoring, Cloud Trace, Error Reporting + OpenTelemetry |
| Secretos | Secret Manager |
| Seguridad perimetral | Cloud Armor |
| IaC | Terraform o Google Cloud Infrastructure Manager |
| CI/CD | Cloud Build + Artifact Registry + Cloud Deploy |

### Forma inicial recomendada

Para iniciar rápido sin comprometer el futuro:

```text
Monolito modular API-first
```

Esto significa:

- un backend principal organizado por dominios;
- módulos separados internamente;
- una sola base de datos principal;
- contratos API claros;
- eventos internos para tareas asíncronas;
- posibilidad futura de separar servicios si el crecimiento lo justifica.

No se recomienda iniciar con microservicios puros desde el día uno, porque aumentaría complejidad operativa, costos y tiempos de desarrollo antes de validar el producto.

---

## 22. Riesgos y decisiones pendientes

### Riesgos

- Diseñar permisos simples al inicio y después no poder soportar corporativos, centros de negocio o integraciones.
- No separar bien tenant, ambiente y app externa.
- Usar API keys como seguridad principal.
- Mezclar datos productivos con datos de prueba.
- Construir reportes directamente sobre tablas transaccionales sin una estrategia de evolución.
- No definir entitlements propios y depender completamente del proveedor de pagos.
- Dejar internacionalización para el final.

### Decisiones pendientes

- Estrategia de proyectos Google Cloud por ambiente y por cliente enterprise.
- Proveedor de identidad definitivo dentro de Google: Identity Platform para clientes y Cloud Identity/Google Workspace para administradores internos.
- Estrategia de cobro: Google Cloud Marketplace como opción preferente dentro del ecosistema Google, y definición de alternativa si se requiere cobro web directo no cubierto por Marketplace.
- Nivel de aislamiento inicial por tenant.
- Planes comerciales iniciales.
- Módulos incluidos por plan.
- Límite de usuarios por plan.
- Límite de centros de negocio por plan.
- Políticas de consumo de API.
- Si habrá portal de desarrolladores desde MVP o fase posterior.
- Uso de Apigee desde MVP o adopción posterior.
- Herramienta de BI embebido: Looker, Looker Studio o motor propio de reportes.

---

## 23. Fuentes técnicas consultadas

- Cloud Run autoscaling: https://cloud.google.com/run/docs/about-instance-autoscaling
- Identity Platform OIDC: https://cloud.google.com/identity-platform/docs/web/oidc
- Apigee API Management: https://cloud.google.com/apigee/docs
- Cloud SQL for PostgreSQL high availability: https://cloud.google.com/sql/docs/postgres/high-availability
- Cloud SQL read pool autoscaling: https://cloud.google.com/sql/docs/postgres/read-pool-autoscaling
- Cloud Spanner PostgreSQL interface: https://cloud.google.com/spanner/docs/postgresql-interface
- Pub/Sub event-driven architecture: https://cloud.google.com/solutions/event-driven-architecture-pubsub
- BigQuery with Looker Studio: https://cloud.google.com/bigquery/docs/bi-engine-looker-studio
- Cloud Logging: https://cloud.google.com/logging/docs
- Cloud Monitoring: https://cloud.google.com/monitoring/docs
- Google Cloud Marketplace SaaS products: https://cloud.google.com/marketplace/docs/partners/integrated-saas
- Google Cloud Marketplace pricing plans: https://cloud.google.com/marketplace/docs/billing/pricing-plans-by-product-type
- Google Cloud Marketplace billing: https://cloud.google.com/marketplace/docs/billing
