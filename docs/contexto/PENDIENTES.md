# Pendientes priorizados de ERClave

## Despliegue solicitado CHG-276 — bloqueado por acceso

El usuario autorizó desplegar a QA el 2026-09-14. Rama del candidato `agent/chg-276-qa-release`. Rama publicada y PR #15 abierto en borrador con el delta completo CHG-271–276; no hay nuevo SHA de release ni promoción QA todavía.

Seguridad: el bucket ahora exige exactamente una regla Delete age365 y rechaza reglas adicionales que pudieran borrar antes;24 pruebas focalizadas aprobadas. Fixtures:9 integraciones de Mantenimiento corregidas y aprobadas con IDs/actores propios; quedan20 históricas pendientes (Admin4, Sales5, Purchasing11). Compras usa tenants UUID y limpieza propia. Admin, Sales y Compras exigen ERCLAVE_TEST_ALLOW_TEMP_TENANTS=1 además de loopback5434/erclave_local: habilitar solo tras autorización explícita de tenants temporales, solicitada y pendiente. No se ejecutaron esas20.

GitHub: acceso admin del repositorio comprobado; cinco gates QA conservan required_reviewers/ChemaPsan. Google Cloud: la sesión actual carece de storage.buckets.list en proyecto erclave; se solicitó al usuario iniciar con la cuenta administradora. No se concedió IAM, creó bucket, ejecutó migración ni cambió tráfico/Hosting. QA permanece en la base b63cdad previamente verificada. La revisión visual Word permanece pendiente; binarios no son edición final distribuible.

Rama publicada y PR en borrador creado: https://github.com/ChemaPsan/eslaclave-erclave/pull/15, commit funcional `8f4943fd2a0812e2450c6d5b68c3de8cf63006b5`. CI inicial `34816849209` en ejecución al registrar esta nota; verificar el resultado del último HEAD en el PR, no inferirlo de este registro. No se fusionó main ni ejecutó qa-candidate/qa-release. Despliegue detenido hasta acceso Cloud, autorización de pruebas multitenant y cierre de gates.




## Preparación QA y manuales CHG-275

Revisión 2026-09-14: siete manuales y guía actualizados para Local con capacidades pendientes de QA; 65 casos en guía/matriz (56 base +9 nuevos), sin aceptación inferida. Las siete APIs QA reportan b63cdad en /version. Se preparó QA_EVIDENCE_BUCKET en qa-release; bucket/IAM aún requieren aprovisionamiento autorizado y smoke. Local head `20260913_0036`; QA documentado `20260908_0034` sin cambios.

Selección segura:29 aprobadas sin skips (23 DB históricas,3 schemas históricos,3 DB nuevas). De las55 históricas antes omitidas se verificaron26 y quedan29 bloqueadas por fixtures de otros tenants/limpieza amplia. No lanzar verify:postgres completo. Detalle, rollback, matriz API y gates en `docs/operaciones/release_qa_20260914.md`. Sin publicación de rama/PR, migración o deploy QA.


## Evidencia de servicios CHG-274 — solo Local

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.

Pendientes de release: UAT del tester, bucket privado dedicado con lifecycle365d/versionado y soft-delete desactivados, política de no respaldar adjuntos más allá de su retención y promoción gobernada. No hay escrituras QA. Las55 integraciones generales previas siguen pendientes; este corte prueba DB/archivos de evidencia de forma focalizada.


## Margen esperado sin tope CHG-273

CHG-273 implementado y migrado solo Local. Pendientes: aceptación del tester y promoción QA autorizada, incluyendo migración0035 antes de exponer la captura sin tope. Las 55 integraciones generales omitidas en CHG-272 no se dan por ejecutadas: este corte sí verifica PostgreSQL real específicamente para margen y reversa. CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.


## Cierre y aceptacion de formularios CHG-272

Cierre tecnico completado: 174 pruebas browser aprobadas (98 offline, incluidos 14 Backoffice; 22 MAIN y 54 regresion), documentacion/trazabilidad, skill, validate y `verify` (262 backend, 55 omitidas sin DB; sintaxis 79). Las integraciones omitidas no se declaran ejecutadas. No quedan gates pendientes de ejecucion de CHG-272.

- Ejecutar UAT del tester y capturar respuesta estructurada/correlacion para identificar la causa exacta del incidente original de Movimientos; no asumirla por la captura.
- Ampliar evidencia negativa de negocio por cada consumidor que se ajuste. Las 54 variantes registradas demuestran wiring, no prueba exhaustiva de todas sus reglas/transiciones.
- Promocion QA y actualizacion de manuales tras release, exclusivamente bajo autorizacion y pipeline; CHG-272 esta solo Local y CHG-271 se preserva como manual de QA vigente.

Detalle, comandos y limites: `docs/auditorias/formularios_feedback_2026-09-13.md`. Los pendientes anteriores no se cierran por este cambio de feedback.

## Manuales y guía del tester CHG-271

CHG-271 sincroniza los siete manuales funcionales Markdown/Word y la guía de pruebas con QA `b63cdad`, revisión documental 2026-09-10. Entrega: `docs/qa/ENTREGA_TESTER.md`; generación reproducible de tablas y procedimientos mediante herramientas documentales. No cambia runtime, contratos, migraciones, datos, permisos ni despliegues. No publica documentos en GitHub.

Incidencia identificada por revisión de código: la bandeja para solicitar sobrantes de Mantenimiento busca `.submodule-screen`, ausente en su render; confirmar/corregir acceso por el agente técnico de Mantenimiento y QA. No se declara disponible el recorrido completo desde pantalla. Compra directa soportada por API pero no expuesta en alta de órdenes de la UI. Ambos límites constan en manuales/guía. UAT autenticada continúa pendiente del tester.


## Estado vigente tras release QA CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff vigente: `docs/contexto/REANUDACION_CHG269.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.

Las notas de preparación y cortes anteriores que siguen son evidencia histórica; no deben disparar un release duplicado.


## Promoción QA en preparación CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Cierre Local CHG-268

Reserva MTO-000001 recuperada y fallo Decimal corregido. Pendientes: confirmación física por Almacén cuando entregue, aceptación manual y promoción gobernada a QA. Reintentos automáticos siguen fuera de alcance; las fallas de existencia/dependencia conservan recuperación manual. Informe: `docs/auditorias/recuperacion_refacciones_2026-09-08.md`.


## Alcance posterior a CHG-264

Entregas parciales elegidas, rechazo de la solicitud productiva, selector de receptor diferente al responsable quedan pendientes. Antes de promocion revisar reservas historicas vencidas e intentos anteriores con respuesta incierta; no se reactivan ni compensan por inferencia. El callback de servicios comerciales Sales a materiales sigue fuera de alcance. Evidencia: `docs/auditorias/materiales_produccion_movimientos_2026-09-08.md`.

## Alcance posterior a la entrega de refacciones CHG-263

- Entregas parciales elegidas por el almacenista y aprobacion separada de la entrega quedan fuera de este corte; la confirmacion actual entrega la solicitud completa.
- Antes de promover, revisar reservas historicas con vencimiento: no reactivar stock expirado. Las solicitudes reservadas sin entrega pueden cancelarse y solicitarse nuevamente; movimientos ya emitidos conservan su historia.
- Operaciones heredadas de entrega con error/resultado incierto requieren revision por Almacen; no se compensan ni se libera la maquina por inferencia. Los reintentos actuales preservan partidas ya confirmadas y claves Inventory.
- La bandeja usa limit/offset; carga sostenida, cursor estable bajo cambios concurrentes y aprobacion QA siguen pendientes.

Ultima actualizacion: 2026-09-07.

## Cobertura posterior a auditoria CHG-262

La auditoria Local de coherencia frontend/backend y sus correcciones estan documentadas en `docs/auditorias/frontend_backend_2026-09-07.md`. No quedan abiertos los 17 grupos de defectos reproducidos en ese corte. Mantener las regresiones de campos/roles al agregar flujos; la cobertura combinatoria completa de perfiles, el volumen y las fallas distribuidas no se sustituyen por esos tests. Los cambios Local no se han promovido a QA.

## Validacion del release QA

0. Completar la matriz UAT del SHA QA `a119ddf5e8d42376b8557b234e15e3681b19c2a7`: permisos, aislamiento entre tenants, dependencias modulares, Compras, Mantenimiento, referencias, reservas/consumos, recepciones, capacidad, valuacion, concurrencia, proteccion de datos e idempotencia.
1. Repetir en QA el onboarding con un tenant ficticio y confirmar recepcion del correo Firebase, incluido folder de spam. Despues validar eliminacion, `firebase_identity_cleanup` y que el tenant deje de aparecer.
2. Diseñar una reconciliacion durable/outbox para invitaciones o limpiezas Firebase pendientes; la respuesta explicita evita el falso fracaso, pero no sustituye un reintento persistente si el cliente pierde la respuesta.
3. Comprobar que el administrador allowlisted accede a Backoffice mientras un owner ordinario conserva `403`, sin persistir tokens ni contraseñas.
4. Comprobar con usuarios de tenants distintos que los siete modulos seleccionan el tenant desde membresias, recargan datos de Cloud SQL y no muestran KPIs/transacciones simuladas; los modulos planeados permanecen inactivos.

## Prioridad siguiente

0. Siguiente evolucion de Mantenimiento tras CHG-257: reintento automatico programado, participantes secundarios y adjuntos; despues abordar preventivos y activos generales. Los reportes operativos basicos de ordenes, indisponibilidad, refacciones y tiempos ya quedaron cerrados.
0.1. Siguiente evolucion de Compras: division/adjudicacion de partidas de una requisicion entre varios proveedores, reintento automatico programado de recepciones `needs_reconciliation` y paginacion server-side antes de promover a QA. CHG-259 ya prueba la recuperacion parcial y corrige partidas sin respuesta; CHG-255 permite servicios sin Inventory. No existe aun adjudicacion parcial, factura ni cuenta por pagar.
1. Siguiente corte de Ventas despues de CHG-255: devoluciones, facturacion/cobranza y callback de Production que convierta solicitudes en partidas entregables y reporte costo real. La ejecucion/aceptacion de servicios ya tiene orden propia; la recepcion de producto terminado permanece cubierta por CHG-222.
2. Evolucionar la paginacion visual transversal de CHG-259 a paginacion contractual con cursor en Clientes, Cotizaciones, Pedidos, Ordenes de servicio y Entregas antes de volumen productivo; el limite preventivo de API permanece en 200.
3. Repetir en Local aislado las dos entradas funcionales que antes quedaron solo en `localStorage` y confirmar en navegador que Movimientos, Inventario y Kardex reflejan el mismo saldo; no copiar esos datos a QA.
4. Completar el catalogo de Articulos para escala server-side; actualmente el corte escalable se concentro en balances de Inventario.
5. Decidir funcionalmente si Categoria se convierte en catalogo jerarquico antes de modelar IDs, padres o migraciones.
6. CHG-264 separa consumo e inicio: pruebas PostgreSQL cubren entrega parcial, bloqueo de inicio/cancelacion, recuperacion y lock; completar carga sostenida y cortes de red reales antes de QA.
7. Capturar y validar areas/puestos QA solamente con datos ficticios y autorizacion explicita; `hr-service` y el entitlement ya estan desplegados, pero sus catalogos permanecen vacios.
8. Paginar el catalogo de articulos elegibles para recetas y exponer disponibilidad agregada server-side para volumen mayor a 200 combinaciones articulo/almacen.
9. Ejecutar la prueba funcional del editor de permisos en QA tras renovar la sesion y confirmar persistencia, concurrencia y rechazo de grants prohibidos.
10. Diseñar la recepcion de merma desde Produccion. La recepcion de producto terminado permanece confirmada por Almacenes mediante `inventory.finished_goods_receipt.receive`; CHG-236 separo esa autoridad de los movimientos generales.
10.1. Evaluar un borrador de orden de Produccion separado de la liberacion. En el runtime vigente, crear la orden valida, reserva y libera en una sola operacion protegida por `production.order.release`.
11. Evolucionar el calendario productivo base lunes-viernes a calendarios tenant configurables con turnos, festivos, ausencias y excepciones por mantenimiento. CHG-241 ya distribuye y compromete capacidad multi-dia; Mantenimiento correctivo aun no modifica automaticamente esa capacidad planeada.
12. Implementar PDF de Pedido y remision/Entrega usando `document.template`, con snapshot o artefacto inmutable; mover el logo a object storage antes de promover la plantilla a QA.
13. Cuando Compras sea operativo, definir la politica de valuacion que actualizara el costo unitario base del articulo desde recepciones u ordenes de compra; por ahora permanece como captura manual de Inventory.
14. Integrar consumidores externos con la reserva central de folios o exigir una credencial interna de confianza; la UI Local ya usa el catalogo, pero los contratos propietarios conservan compatibilidad con clientes API que proporcionan un codigo valido.
15. Estandarizar en backend todas las excepciones de validación y errores inesperados con la envoltura `ErclaveError`; propagar `X-Correlation-Id` entre servicios, exponerlo en CORS y declarar respuestas de error comunes en OpenAPI. CHG-251 ya evita exponer mensajes técnicos en la UI y conserva la referencia disponible, pero no cambia los contratos HTTP de los servicios.
16. Diseñar el modulo Reportes para analitica transversal: XLSX con formato, PDF, constructor, cruces entre propietarios, graficas, vistas guardadas, programacion y distribucion. CHG-257 conserva reportes operativos simples en el servicio propietario y oculta su formato tecnico en la interfaz.

## Fuera del alcance actual

- Crear infraestructura de Produccion antes de autorizacion expresa; los objetivos futuros son RPO 15 minutos y RTO 2 horas.

- Lotes y canales de reserva distintos de ordenes de Produccion o pedidos de Ventas.
- Lotes, series, cuarentena, inventario bloqueado y en transito.
- Carga de datos funcionales, dummy o de volumen en Inventory/RH sobre QA sin una autorizacion especifica.
- Despliegue de frontend o servicios fuera del pipeline y sus aprobaciones protegidas.

## Regla de mantenimiento

Mover un pendiente a `ESTADO_ACTUAL.md` solo cuando este implementado, probado y registrado en `TRAZABILIDAD.md`. Eliminar pendientes obsoletos explicando la decision en trazabilidad.


## Pendientes posteriores a CHG-265

Conectar automáticamente Ventas → Producción → recepción/entrega y materiales de servicios comerciales se mantienen planned. También devoluciones comerciales a proveedor/cliente, entregas productivas/refacciones parcialmente elegidas, aprobación separada, reintentos programados y asignación de usuarios por almacén. Las devoluciones de sobrantes de Producción/Mantenimiento ya tienen solicitud y confirmación por Almacén en Local. No confundirlas con devoluciones comerciales ni merma. Validar volumen y fallos prolongados antes de promoción; QA no recibe este cambio.


## Ajustes UAT Local CHG-266

Los cuatro hallazgos UAT de proveedores, requisiciones, riel de Órdenes y acceso al ciclo de cotizaciones están corregidos en Local. Resta aceptación manual del usuario; no hay autorización de promoción QA. La configuración de permisos del ambiente remoto debe evaluarse dentro de un release autorizado, sin copiar datos Local ni conceder permisos a roles por inferencia.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Solicitudes compactas Local CHG-267

La presentación compacta de solicitudes en Movimientos está implementada en Local. Pendiente aceptación manual del usuario. QA no recibe código ni datos por inferencia; no se amplía este corte a permisos o flujos de almacén.

Evidencia y APIs: `docs/auditorias/almacen_solicitudes_desplegables_2026-09-08.md`.
