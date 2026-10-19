# Historia de revisiones de agentes hasta CHG-310

> Evidencia histórica; no usar como instrucciones vigentes. Consultar [AGENTES](../../../AGENTES.md) y [ESTADO_ACTUAL](../ESTADO_ACTUAL.md).


## Decisión transversal CHG-309 · 2026-10-07

El usuario confirmó: «sí, en la moneda base de la Sociedad; esto aplica para todo». Regla transversal para costos y tarifas de toda la operación, incluidos materiales, máquinas y mano de obra. Cuando un documento use otra moneda, conservar original y convertido con tipo de cambio explícito. No reinterpretar ni convertir automáticamente historia sin moneda confirmada. Funciona con Accounting apagado. No volver a preguntar esta política; su aplicación completa sigue pendiente de implementación. Producción sigue en implementación; retomar desde docs/contexto/INICIO_SESION.md.


## Actualización CHG-308 · 2026-10-07

Producción negocio/técnica y guardianes revisados: no liberar fabricación antes de validar capacidad/recursos por División y moneda de tarifas; snapshot e intento durable son preparación. Inventory debe comprobar origen antes de reserva. Fichas de RH/Ventas/Contabilidad, Arquitectura/Datos/DB/API/Seguridad/Sinergia/UX/QA/Manuales consultadas; sin delegación. Ver docs/arquitectura/cont_08_produccion_contexto.md.


## Actualización CHG-307 · 2026-10-05

Fichas consultadas: negocio/técnico Ventas, Inventarios, Producción y Contabilidad; Arquitectura, Datos/Custodio DB, API, Seguridad, Diseño/i18n, QA/Release, Sinergia modular, Formularios y Manuales. Custodiar costo original por Sociedad en Inventory, conversión explícita/fija en Sales; no habilitar fabricación ni backfill por analogía con stock. Revisión documental, no agentes ejecutados en paralelo. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


## Actualización CHG-306 · 2026-10-05

Inventarios/Ventas negocio y técnica, Contabilidad y guardianes API/Arquitectura/Datos/Seguridad/Sinergia/QA consultados sin delegación. Preservar proyección mínima de origen, snapshot por reserva/salida, scopes antes de replay y compatibilidad explícita. No habilitar surtimiento dimensionado hasta cerrar propagación y moneda de costos. Ver docs/arquitectura/cont_08_reservas_contexto.md.


## Actualización CHG-305 · 2026-10-05

Ventas protege ejecución dimensionada, snapshot fijo, costo explícito en moneda del pedido y locks pedido→servicio contra cancelación. RH/Production validan recursos en División con permisos puntuales del consumidor activo. Guardianes API/Seguridad cubren lookup acotado/minimizado y autorización antes de replay; pausa/cancelación permiten detener recursos no vigentes. Consultar docs/arquitectura/cont_08_servicios_contexto.md.


## Actualización CHG-304 · 2026-10-05

Ventas: preservar snapshot aprobado al convertir, scope en pedidos/servicios y CSV, revalidación antes de replay y efectos. RH/Production: admitir sales.order.create para lookup de elegibilidad con consumidor activo. Guardián de fronteras: impedir surtimiento/entregas/ejecución dimensionados hasta implementar propagación; cancelación del pedido mantiene historia. Ver docs/arquitectura/cont_08_pedidos_contexto.md.


## Actualización CHG-303 · 2026-10-05

Ventas negocio/técnica: contexto explícito en borrador, moneda coincidente sin conversión, División fija, snapshot actualizable sólo en borrador. RH/Producción: elegibilidad exacta por resource_id para consumidor Sales activo. Guardianes API/Seguridad/Datos: scope también en CSV, locks ordenados, idempotencia, downgrade con historia bloqueado. CONT-08 sigue parcial; no habilitar conversión dimensionada hasta propagar contexto.


**CHG-298:** Inventarios, Administración, Costos y Contabilidad con Seguridad/Datos/Sinergia aplican [CONT-07 Inventory parcial](../../../docs/arquitectura/cont_07_inventory_asignaciones.md). Inventory es dueño de asignaciones; Admin valida División/scope, Costing valida centro opcional. No inferir aislamiento de movimientos ni backfill desde este catálogo. Nuevas APIs sin bypass demo; almacén pendiente sólo se asigna con alcance completo y permiso puntual.

**CHG-297:** Costos/Administración/Contabilidad y guardianes consultan [CONT-05](../../../docs/arquitectura/cont_05_catalogo_centros.md). Catálogo básico implementado Local en Costing, permisos costing.cost_center.read/create/update/status con disponibilidad Admin, sin ampliar Costing analítico. Admin numera, Costing guarda; scope vigente en cada solicitud. CONT-04 transversal y CONT-06/07/08 pendientes.

**CHG-296:** Administración, Contabilidad y Sinergia aplican la [matriz de capacidades](../../../docs/arquitectura/matriz_capacidades_organizacionales.md). Catálogo básico en Admin, dueño Costing, sin analítica/Accounting implícitos. Centro obligatorio sólo por flujo habilitado, confirmado por usuario. Disponibilidad de sesión no concede permiso ni sustituye chequeos de API/jobs. CONT-04/05 y propagación pendientes.


**CONT-03 / CHG-293:** Administración y Seguridad consultan `docs/arquitectura/cont_03_sesion_alcances.md`: sesión v2, scope vacío sin Divisiones, wildcard explícito, revisión/idempotencia y conservación de alcance ante seed/onboarding. Contabilidad negocio/técnica se refuerza con `$erclave-accounting`; cobertura de todos los módulos y guardianes en `docs/arquitectura/cobertura_agentes_modulos.md` y `$erclave-module-boundaries`. CONT-04/05/07/08 siguen pendientes; no atribuir aislamiento de documentos a la sesión.

**Actualización CONT-02 / CHG-292:** Administración negocio/técnica, API, Seguridad, Datos/Custodio DB, Diseño/i18n y QA consultan `docs/arquitectura/cont_02_administracion_organizacional.md`. Emisores/Sociedades/Divisiones ya tienen APIs/UI Local, doce permisos, autoridad normalizada y proyección compatible. Head Local `20260925_0038`. CONT-03 será sesión/scopes; Centros de costos (Costing) y libros por Sociedad (Accounting) continúan pendientes. No repetir decisiones CONT-00 ni tratar el JSON como escritor independiente tras activar. Los apartados CHG-289 siguientes describen el corte previo al switch.

Estado desplegado y pendientes: `docs/contexto/ESTADO_ACTUAL.md` y `docs/operaciones/release_qa_20260914.md`. El despliegue técnico no equivale a smoke autenticado ni aceptación UAT. Las notas CHG posteriores conservan historia de revisión; no sustituyen el estado vigente.

Reglas persistentes: bucket de evidencia privado con política única Delete age 365. Fixtures multitenant de Admin/Sales/Purchasing requieren autorización explícita y `ERCLAVE_TEST_ALLOW_TEMP_TENANTS=1`; no basta `ERCLAVE_TEST_TENANT_ID`. Maintenance limpia solo sus IDs y actores.



## Historial de revisión de fichas

Las secciones CHG-265 a CHG-274 siguientes conservan el estado observado en cada corte. Sus revisiones y pendientes no son el inventario operativo vigente; consultar `docs/contexto/ESTADO_ACTUAL.md`.

## Actualización de fichas operativas CHG-265

Consultados documentalmente agentes de negocio/técnicos Producción, Inventarios, Compras, Ventas, Mantenimiento y RH; transversales Arquitectura/API/Datos, Custodio DB, Seguridad, Sinergia, UX/i18n, QA y Gobierno documental. Sin delegación.

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.

Fichas de Inventarios y Sinergia deben conservar recepción/expedición explícitas, transferencia en tránsito y ajustes mediante propietarios HTTP. Compras distingue recepción física de aceptación por solicitante. Producción/Mantenimiento conservan salida original y costo neto de retornos. Seguridad verifica actor/origen/tenant y locks; UX muestra mensajes estables ES/EN. QA usa Local aislado y limpieza por IDs propios; no ejecutar suites históricas que escriban otros tenants.


## Ajustes UAT Local CHG-266

Fichas de Producción/Compras y UX/frontend: conservar contenido operativo fuera del riel colapsable; listado inicial de Proveedores, formulario modal y búsqueda de requisición legible por ancho real. Ventas/Administración/Seguridad: emitir y aprobar son permisos independientes; orientar cuando falten y diagnosticar catálogo/asignación efectivos sin bypass por nombre de rol. La reparación del Owner demo CHG-266 solo aplica a Local; no autoriza grants o seeds remotos. QA/Gobierno documental: contrastar ES/EN, rechazo sin pérdida de captura y evidencia Local antes de promoción.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Solicitudes compactas Local CHG-267

Inventarios/Sinergia y UX/frontend deben mantener las solicitudes antes del historial, cerradas al entrar y con resumen de pendientes. Seguridad/QA deben comprobar que ocultar detalles no cambia autorización ni efectos, que errores/carga no aparentan ausencia de trabajo y que cada actualización parcial refresca el resumen. Gobierno documental conserva evidencia Local y contratos/diagramas sin cambios.

Evidencia y APIs: `docs/auditorias/almacen_solicitudes_desplegables_2026-09-08.md`.


## Recuperación de refacciones Local CHG-268

CHG-268 recupera reservas/cancelaciones de refacciones interrumpidas bajo locks por tenant/orden/solicitud y conserva claves Inventory. Corrige serialización Decimal; Mantenimiento ofrece reintento ES/EN con permiso propio, Almacén confirma la entrega por separado. MTO-000001 recuperada en Local: una reserva de 1 H87, existencia física 2, disponible 1, sin salida ni duplicados. Sin migraciones ni permisos nuevos. Detalle: `docs/auditorias/recuperacion_refacciones_2026-09-08.md`.


## Candidato de continuidad CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Release QA verificado CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff vigente: `docs/contexto/REANUDACION_CHG269.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.

## Documentación funcional QA CHG-271

El Custodio de manuales y los agentes de negocio/técnicos de los siete módulos revisan los manuales contra el release QA b63cdad. Se regeneran Word y guía del tester; APIs sin cambios. Incidencia por verificar: montaje de bandeja de sobrantes de Mantenimiento. Compras directas: API disponible, alta UI no expuesta. El estado desplegado no equivale a UAT aprobada. Registro en docs/manuales_solucion/REGISTRO.md y entrega en docs/qa/ENTREGA_TESTER.md.


## Productos y servicios: margen esperado CHG-273

CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.


## Evidencia de servicios CHG-274

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.


## Revisión complementaria CHG-281 Local

Arquitectura/API, Seguridad, QA y Producción revisan presupuestos HTTP, correlación, cuerpo lento y éxito parcial. No agregar reintentos ni alterar recursos Cloud en este corte. Cliente compartido impacta los siete módulos; mantener separación de error de permisos y dependencia. Ver docs/auditorias/timeouts_local_2026-09-16.md.
