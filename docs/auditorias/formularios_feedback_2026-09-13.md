# Formularios y feedback operativo - CHG-272

Fecha: 2026-09-13. Estado: implementacion y validacion Local completadas; UAT y promocion QA pendientes. Fuente viva: `docs/contexto/ESTADO_ACTUAL.md`.

## Problema y alcance

El reporte del tester en Movimientos mostraba una instruccion generica para revisar campos marcados sin identificar el requisito ni marcar el control. La imagen no permite atribuir la causa original a un campo: no contiene el detalle HTTP rechazado ni los identificadores enviados. CHG-272 corrige el mecanismo transversal; no declara reproducida la causa exacta de aquella peticion QA.

El cliente HTTP compartido conserva el error estructurado y captura el formulario propietario antes de esperar autenticacion o red. `frontend/features/form-feedback.js` resuelve rutas exactas, codigo estable y tipos de validacion. `form-bindings.js` registra 54 variantes de formulario y sus alias de serializacion, controles visibles de lookups y partidas. La presencia en ese registro acredita integracion revisada, no una prueba exhaustiva de todas las reglas de negocio.

El catalogo `frontend/i18n/form-business-errors.js` incorpora 244 codigos con copy ES/EN y 95 reglas para diagnosticos de schema. Estas reglas reconocen literales previamente inventariados mediante una lista cerrada; no interpretan texto diagnostico libre ni lo muestran directamente. Las rutas/codigos desconocidos quedan en un resumen seguro y accionable; no se deduce el campo buscando palabras del mensaje del backend. Los fallos tecnicos, permisos y conflictos no se presentan como errores de captura por defecto.

## Comportamiento Local

- Mensaje junto al control, resumen con enlaces, `aria-invalid`, `aria-describedby` y foco en el primer control corregible. Se conservan las descripciones anteriores y se retiran las marcas propias al corregir.
- Rutas de arrays resueltas por la identidad y el orden realmente enviados. En recepciones, `lines.0` puede corresponder a la segunda fila visible si la primera tiene cantidad cero. Los IDs ocultos de lookups senalan la busqueda visible, no el input oculto.
- El CSS compartido respeta `hidden`: los campos condicionales no aplicables permanecen ocultos y no reciben foco.
- Los formularios conservan valores, selecciones y partidas al fallar. Backoffice evita reconstruir login, onboarding y editor durante el submit/rechazo; los filtros se restauran desde su estado. Las contrasenas permanecen solo en el DOM, sin persistencia en storage.
- El cliente central comunica rechazos a formularios inline y modales antes de que un catch reduzca la informacion a un texto. Los manejadores de formulario reciben el objeto de error.
- Las validaciones de captura no sustituyen la autoridad de los servicios, los permisos, la idempotencia ni el aislamiento por tenant.

## Gobierno y prevencion

La skill `.agents/skills/erclave-form-feedback/SKILL.md` es obligatoria mediante `AGENTS.md` y `AGENTES.md` para cambios de formularios, payloads y feedback, incluidos modulos futuros. Exige rutas estructuradas, fallback seguro, conservacion de captura, ES/EN, teclado/ARIA y evidencia negativa por consumidor.

`validate:form-feedback` revisa instalacion, inventario y enlaces de estilos. `validate:error-feedback` mantiene el contrato semantico. `test:form-feedback` agrega pruebas conductuales independientes de base de datos al flujo de CI. Los validadores estaticos no prueban por si solos que todas las pantallas sean corregibles.

Revisiones de este corte: reglas operativas `AGENTS.md`, fichas `AGENTES.md`, arquitectura de feedback/gobierno documental/fronteras y skill transversal; revision complementaria delegada de Backoffice y de recorridos reales de los siete modulos. No se modifican ownership, reglas de negocio ni contratos.

## Evidencia conductual ejecutada

| Suite | Resultado comprobado | Alcance y limites |
|---|---|---|
| `tests/e2e/module-form-feedback.spec.js` | 22/22, 58.8 s | Once formularios reales por ES/EN, renderer y submit de `app.js`, autenticacion/lecturas Local y rechazos HTTP simulados. No persiste comandos. |
| `tests/e2e/backoffice-form-feedback.spec.js` | 14/14, 12.3 s; incluidos en las 98 offline | Cinco formularios en ES/EN, required multiple, reset de correo, rutas anidadas y captura conservada; autenticacion/API simuladas. No se suman otra vez al total. |
| `npm run test:form-feedback` | 98 aprobadas: 94 en 2.1 min + 4 en 13.2 s; ambos exit 0 | Suite offline combinada con cobertura de helpers, bindings, schema y Backoffice. Ejecuciones complementarias sin duplicar los 14 casos Backoffice. Servidor estatico 4183 cerrado al finalizar. |
| Regresion general previa, ocho archivos | 54/54, 4.3 min; exit 0 | Excluye los tres archivos nuevos form-feedback, backoffice-form-feedback y module-form-feedback. |
| `npm run verify` | Aprobado, exit 0 | Validadores y compilacion; 262 pruebas backend aprobadas, 55 omitidas sin `ERCLAVE_TEST_DATABASE_URL`. Sintaxis de 79 archivos aprobada. No acredita las integraciones omitidas con DB. |
| `npm run validate` final | Aprobado, exit 0 | Todos los validadores, sintaxis 79 y coherencia documental CHG-272. |
| Skill y diff | Aprobados | `quick_validate.py`: Skill is valid; `git diff --check` limpio. |
| Sintaxis de Backoffice y pruebas; `validate:responsive` | Aprobados en revision complementaria | No sustituyen UAT. |

Total browser sin duplicados: **174 pruebas = 98 offline + 22 MAIN + 54 de regresion general**. Los 14 casos Backoffice forman parte de las 98 offline. Los conteos acreditan los escenarios ejecutados, no todas las combinaciones de negocio.

Recorridos reales MAIN verificados:

| Modulo | Formulario | Rechazo y comprobacion |
|---|---|---|
| Almacenes | `movementForm` | `reason` e `inventory_item_id`; lookup visible, cantidad/documento conservados y destino condicional oculto. |
| Produccion | `productServiceForm` | `name`; captura conservada y foco. |
| Produccion | `recipeForm` | `resources.1.quantity` y `stages.1.weight_percent`; solo segundo recurso/etapa, primera fila sin marca. |
| RH | `workerForm` (alta) | `rfc`; captura y foco. El RFC de edicion es inmutable y no se fuerza a ser editable. |
| Mantenimiento | `maintenanceOrderForm` | `title`; descripcion conservada. |
| Mantenimiento | `maintenanceTimeModalForm` | `ended_at` se vincula a `time_ended_at`; notas conservadas. |
| Compras | `purchasingSupplierForm` | `tax_id`; nombre conservado. |
| Compras | `purchasingReceiptForm` | `lines.0.quantity` corresponde a segunda fila DOM tras filtrar ceros; primera fila sin marca. |
| Administracion | `admin-create-role` | `name`; codigo y descripcion conservados. |
| Ventas | `salesCustomerForm` | `primary_contact.email` se vincula a `contactEmail`. |
| Ventas | `salesQuoteForm` | `lines.1.quantity`; segunda partida marcada y primera sin marca. |

Backoffice verifica `login`, `tenant-onboarding`, `tenant-editor`, `tenant-search` y `usage-search`. Las respuestas fallidas se interceptan; los codigos y rutas de prueba ejercitan el consumidor y no afirman que cada rechazo simulado reproduzca una regla real del backend.

Reproduccion desde la raiz, con Node/Python y Chrome disponibles:

```powershell
npm.cmd run validate:form-feedback
npm.cmd run validate:error-feedback
npm.cmd run validate:responsive
npm.cmd run test:form-feedback
npx.cmd playwright test tests/e2e/module-form-feedback.spec.js --reporter=list --output test-results/module-form-feedback
npx.cmd playwright test tests/e2e/backoffice-readonly.spec.js tests/e2e/current-flows.spec.js tests/e2e/frontend-contracts.spec.js tests/e2e/local-uat-layout.spec.js tests/e2e/operational-handoffs.spec.js tests/e2e/production-warehouse-issue.spec.js tests/e2e/warehouse-material-requests.spec.js tests/e2e/warehouse-pending-summary.spec.js --reporter=list --output test-results/general-regression
npm.cmd run validate:documentation
npm.cmd run verify
```

La suite MAIN requiere el stack Local aislado previsto por `tests/e2e/local-preflight.js`; las lecturas se realizan exclusivamente sobre loopback y tenant `ten_739ee59d765d5e14818674800d`. Las mutaciones de negocio no interceptadas se rechazan en el navegador; la numeracion se simula sin reservar folios reales. La suite offline usa servidor estatico loopback y mocks, sin DB ni seeds.

## Evidencia visual

La revision visual confirmada no detecto overflow ni perdida de legibilidad/color en los escenarios capturados:

| Evidencia | Condicion |
|---|---|
| [Claro estrecho](evidencias/form_feedback_20260913/narrow-light.png) | 390 px, tema claro |
| [Oscuro estrecho](evidencias/form_feedback_20260913/narrow-dark.png) | 390 px, tema oscuro |
| [Ampliacion CSS](evidencias/form_feedback_20260913/zoom200-light.png) | Contenedor de 780 px y CSS `zoom: 2` |

La ultima captura prueba ampliacion CSS; no es zoom real del navegador al 200 %. La evidencia visual no sustituye pruebas adicionales de zoom del navegador, tecnologias de asistencia ni UAT.

## APIs afectadas

Contratos modificados: **Ninguno**. No cambia request/response, permisos ni endpoints del backend. El transporte frontend compartido afecta la presentacion de errores de los siete modulos y Backoffice; no se enumeran todas sus rutas como si hubieran sido ejecutadas.

Endpoints consumidos sin cambio y ejercitados por las pruebas negativas reales de pantalla (respuesta HTTP interceptada):

| Servicio | Metodo y ruta | Consumidor |
|---|---|---|
| inventory-service | POST `/v1/inventory/movements` | Entrada de Almacen |
| production-service | PATCH `/v1/production/product-services/{id}` | Producto/servicio |
| production-service | POST `/v1/production/recipes` | Recursos y etapas |
| hr-service | POST `/v1/hr/workers` | Alta de trabajador |
| maintenance-service | POST `/v1/maintenance/orders` | Alta de orden |
| maintenance-service | POST `/v1/maintenance/orders/{id}/time-entries` | Registro de tiempo |
| purchasing-service | POST `/v1/purchasing/suppliers` | Alta de proveedor |
| purchasing-service | POST `/v1/purchasing/receipts` | Recepcion filtrada |
| sales-service | PATCH `/v1/sales/customers/{id}` | Cliente |
| sales-service | PATCH `/v1/sales/quotes/{id}` | Cotizacion |
| admin-service | POST `/v1/roles` | Alta de rol |
| admin-service | POST `/v1/catalogs/code-sequences/{document_type}/next` | Numeracion simulada de altas |
| admin-service / Backoffice | POST `/v1/provisioning/tenant-onboarding` | Onboarding |
| admin-service / Backoffice | PATCH `/v1/backoffice/tenants/{tenant_id}` | Editor de tenant |
| admin-service / Backoffice | GET `/v1/backoffice/tenants`; GET `/v1/backoffice/usage` | Filtros rechazados |

Firebase: login/restablecimiento existentes, con mocks en Backoffice y Firebase Emulator en la suite MAIN. Las lecturas de catalogos y sesion preparan el escenario sin cambios contractuales. APIs no tocadas: implementaciones de los siete servicios, OpenAPI y servicios futuros.

## Limites y pendientes

1. No quedan gates tecnicos pendientes de ejecucion para este corte. Suite offline, MAIN, regresion general, verify, documentacion y skill estan aprobados. Las 55 pruebas backend omitidas sin DB no se presentan como ejecutadas; el corte no modifica backend.
2. UAT con el tester y reproduccion del error exacto de la captura original pendientes. Los 22 casos MAIN cubren once formularios, no todas las transiciones, permisos, combinaciones y reglas de negocio de las 54 variantes registradas.
3. Agregar casos negativos especificos de cualquier formulario/regla que se cambie en el futuro; un formulario registrado no queda automaticamente certificado por las pruebas de otro.
4. Los manuales y la guia CHG-271 describen QA `b63cdad`: se preservan y no se regeneran como si este comportamiento Local ya estuviera publicado. Su siguiente revision depende de una promocion autorizada.
5. Sin despliegues, migraciones, seeds ni escrituras operativas reales en este corte. QA/Produccion no cambian. El release QA de referencia sigue siendo CHG-270; cualquier promocion requiere el flujo gobernado y aprobacion del propietario.

Rollback Local: revertir solamente los archivos del corte CHG-272 preservando los cambios previos CHG-271. No hay rollback de DB ni compensaciones de negocio que ejecutar.
