# Inicio de sesion ERClave

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
