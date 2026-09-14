# Inicio de sesion ERClave

## Despliegue solicitado CHG-276 — en curso

El usuario autorizó desplegar a QA el 2026-09-14. Rama del candidato `agent/chg-276-qa-release`. Se prepara publicación/PR del delta completo CHG-271–276; no hay nuevo SHA de release ni promoción QA todavía.

Seguridad: el bucket ahora exige exactamente una regla Delete age365 y rechaza reglas adicionales que pudieran borrar antes;24 pruebas focalizadas aprobadas. Fixtures:9 integraciones de Mantenimiento corregidas y aprobadas con IDs/actores propios; quedan20 históricas pendientes (Admin4, Sales5, Purchasing11). Compras usa tenants UUID y limpieza propia. Admin, Sales y Compras exigen ERCLAVE_TEST_ALLOW_TEMP_TENANTS=1 además de loopback5434/erclave_local: habilitar solo tras autorización explícita de tenants temporales, solicitada y pendiente. No se ejecutaron esas20.

GitHub: acceso admin del repositorio comprobado; cinco gates QA conservan required_reviewers/ChemaPsan. Google Cloud: la sesión actual carece de storage.buckets.list en proyecto erclave; se solicitó al usuario iniciar con la cuenta administradora. No se concedió IAM, creó bucket, ejecutó migración ni cambió tráfico/Hosting. QA permanece en la base b63cdad previamente verificada. La revisión visual Word permanece pendiente; binarios no son edición final distribuible.



## Preparación QA y manuales CHG-275

Revisión 2026-09-14: siete manuales y guía actualizados para Local con capacidades pendientes de QA; 65 casos en guía/matriz (56 base +9 nuevos), sin aceptación inferida. Las siete APIs QA reportan b63cdad en /version. Se preparó QA_EVIDENCE_BUCKET en qa-release; bucket/IAM aún requieren aprovisionamiento autorizado y smoke. Local head `20260913_0036`; QA documentado `20260908_0034` sin cambios.

Selección segura:29 aprobadas sin skips (23 DB históricas,3 schemas históricos,3 DB nuevas). De las55 históricas antes omitidas se verificaron26 y quedan29 bloqueadas por fixtures de otros tenants/limpieza amplia. No lanzar verify:postgres completo. Detalle, rollback, matriz API y gates en `docs/operaciones/release_qa_20260914.md`. Sin publicación de rama/PR, migración o deploy QA.


## Evidencia de servicios CHG-274 — solo Local

Validación CHG-274:185 browser aprobadas;19 focalizadas (14 archivo/optimización,3 API y2 PostgreSQL), verify292 aprobadas/58 omitidas en corrida sin DB. Las2 integraciones nuevas sí se ejecutaron por separado, al igual que la de margen del corte anterior;55 generales siguen pendientes. Reversa y expiración reales en fixtures, permisos y tamaños comprobados; revisión visual390/760/1280 y tema oscuro.

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.


## Margen esperado sin tope CHG-273

Validación CHG-273:14 pruebas focalizadas aprobadas, incluida PostgreSQL real;23 browser de contratos y98 feedback aprobadas; verify275 backend aprobado. En la corrida genérica se omiten56 integraciones;1 (margen) se ejecutó aparte contra DB real,55 generales previas siguen pendientes. API Local8002 reiniciada y esquema servido sin máximo100 comprobado.

CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.


## Continuidad Local CHG-272: formularios corregibles

Leer `docs/auditorias/formularios_feedback_2026-09-13.md` antes de tocar formularios, validaciones o payloads. Aplicar `.agents/skills/erclave-form-feedback/SKILL.md` conforme a `AGENTS.md`: conservar errores estructurados, rutas exactas e indices enviados, captura, ES/EN, foco y ARIA. No deducir campos por texto diagnostico ni afirmar cobertura total por instalar el helper.

Estado: 54 variantes registradas; 174 pruebas browser aprobadas (98 offline, incluidos 14 Backoffice; 22 MAIN y 54 regresion). `verify` y validate aprobados: 262 backend, 55 omitidas sin DB y sintaxis 79. Skill valida y diff limpio. Sin gates tecnicos pendientes de ejecucion del corte; UAT y promocion QA permanecen pendientes. Preservar CHG-271 y todos los cambios del working tree. Solo Local; no publicar, migrar ni promover por inferencia. QA continua en `b63cdad`; la evidencia UAT sigue pendiente.

## Manuales y guía del tester CHG-271

CHG-271 sincroniza los siete manuales funcionales Markdown/Word y la guía de pruebas con QA `b63cdad`, revisión documental 2026-09-10. Entrega: `docs/qa/ENTREGA_TESTER.md`; generación reproducible de tablas y procedimientos mediante herramientas documentales. No cambia runtime, contratos, migraciones, datos, permisos ni despliegues. No publica documentos en GitHub.

Incidencia identificada por revisión de código: la bandeja para solicitar sobrantes de Mantenimiento busca `.submodule-screen`, ausente en su render; confirmar/corregir acceso por el agente técnico de Mantenimiento y QA. No se declara disponible el recorrido completo desde pantalla. Compra directa soportada por API pero no expuesta en alta de órdenes de la UI. Ambos límites constan en manuales/guía. UAT autenticada continúa pendiente del tester.


## Estado vigente tras release QA CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff vigente: `docs/contexto/REANUDACION_CHG269.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.

Las notas de preparación y cortes anteriores que siguen son evidencia histórica; no deben disparar un release duplicado.


## Promoción QA en preparación CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Continuidad vigente CHG-268

CHG-268 recupera reservas/cancelaciones de refacciones interrumpidas bajo locks por tenant/orden/solicitud y conserva claves Inventory. Corrige serialización Decimal; Mantenimiento ofrece reintento ES/EN con permiso propio, Almacén confirma la entrega por separado. MTO-000001 recuperada en Local: una reserva de 1 H87, existencia física 2, disponible 1, sin salida ni duplicados. Sin migraciones ni permisos nuevos. Detalle: `docs/auditorias/recuperacion_refacciones_2026-09-08.md`.


## Continuacion CHG-264

Materiales de Produccion se entregan desde Movimientos antes del inicio. Leer `docs/auditorias/materiales_produccion_movimientos_2026-09-08.md` y ESTADO_ACTUAL. Cabeza Local `20260908_0034`; preservar CHG-262/263, sin promover por inferencia.

> Continuacion Local CHG-263: la entrega de refacciones se confirma desde Movimientos de Almacen. Consultar `docs/auditorias/refacciones_movimientos_2026-09-07.md`; se conserva el working tree previo de CHG-262 y QA no cambia.

Este documento define el orden obligatorio para recuperar contexto antes de analizar o modificar el proyecto.

> Handoff activo: leer `docs/contexto/REANUDACION_CHG261.md`. El arbol quedo consolidado en commits locales hasta CHG-260; distinguir siempre ese estado Local del release QA inmutable y no promover, migrar ni desplegar por inferencia.

> Continuacion Local CHG-262: leer `docs/auditorias/frontend_backend_2026-09-07.md` y `ESTADO_ACTUAL.md`. Hay correcciones posteriores al handoff CHG-261 en el working tree; el estado limpio de aquel handoff es historico.

## Secuencia

1. Ejecutar `npm.cmd run session:context` desde la raiz.
2. Leer completamente `AGENTS.md` y las secciones aplicables de `AGENTES.md`.
3. Leer `docs/contexto/ESTADO_ACTUAL.md`, `DECISIONES.md`, `TENANTS.md`, `PENDIENTES.md` y cualquier handoff activo enlazado arriba.
4. Leer `docs/arquitectura/gobierno_documentacion_viva.md`, el documento de `modulos/` correspondiente y las fuentes de arquitectura que este referencie.
5. Revisar `git status --short`. Todo cambio previo se considera propiedad del usuario hasta demostrar lo contrario.
6. Identificar microfrontend, servicio, schema, contrato, permisos y agentes especialistas afectados.
7. Registrar `Agentes consultados`; para Local→QA usar Arquitectura, Seguridad y QA/Release como minimo.
8. Confirmar ambiente y `tenant_id` antes de cualquier escritura.
9. Definir criterios de aceptacion y blast radius antes de implementar.

## Cierre obligatorio

Antes de declarar terminado un cambio:

1. aplicar la matriz de `gobierno_documentacion_viva.md` y actualizar OpenAPI, consumidores, pruebas, documentacion y agentes cuando aplique;
2. ejecutar `npm.cmd run validate:documentation` y `npm.cmd run verify`;
3. actualizar `ESTADO_ACTUAL.md` y `PENDIENTES.md` si el estado real cambio;
4. registrar el corte en `TRAZABILIDAD.md`;
5. indicar expresamente si hubo migraciones, seeds, despliegues o escrituras externas.
6. si se modificaron errores, warnings, estados o copy operativo, ejecutar `npm.cmd run validate:error-feedback` y confirmar paridad ES/EN, severidad y restauracion del estado rechazado.

La conversacion es contexto temporal. Estos archivos son la memoria persistente del proyecto.


## Reanudación CHG-265

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.

Preservar CHG-262/263/264 y CHG-265 sin commit. Consultar el informe para pruebas, migraciones y APIs. No promover a QA por inferencia.

Validación CHG-265: 257 backend sin DB (51 omitidas), 19 PostgreSQL seleccionadas, 40 navegador; smokes HTTP y migración reversible vacía aprobados. Consulta informe para alcance y pendientes.


## Ajustes UAT Local CHG-266

Continuar con los ajustes UAT de Proveedores, Requisiciones, Órdenes y Cotizaciones. El Owner Local ya dispone de emitir/aprobar/vencer/cancelar cotizaciones. Recargar frontend y sesión para verlos. Preservar todos los cambios CHG-262–265. Pendiente aceptación manual del usuario antes de cualquier preparación/promoción QA.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Solicitudes compactas Local CHG-267

Preservar CHG-262–266 y la mejora de Movimientos CHG-267: desplegable cerrado al entrar, aviso de pendientes y conservación de apertura al actualizar. Sigue pendiente aceptación manual, sin autorización de promoción QA.

Evidencia y APIs: `docs/auditorias/almacen_solicitudes_desplegables_2026-09-08.md`.
