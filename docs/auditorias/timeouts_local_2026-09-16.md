# Tiempos de espera entre APIs — CHG-281

> Evidencia histórica: conserva observaciones y decisiones de su fecha; no usar como estado o instrucciones actuales. Consultar [fuente vigente](../contexto/ESTADO_ACTUAL.md).

Estado: implementado y probado solo en Local. QA conserva e57237f. Sin despliegue, cambio de infraestructura, instancia mínima, CPU adicional, tarea programada ni reintentos automáticos nuevos.

## Incidente y causa comprobada

En QA OP-000003, el 15 septiembre a las 10:25:42 America/Mexico_City, POST de evidencia inicial y final respondieron 200. PATCH de estado respondió 503 en 5.305 s. La consulta de trabajadores elegibles de RH respondió 200 en 6.855 s; los registros mostraron arranque de una instancia RH durante la llamada. No fue un error de formato ni una prueba de adjuntos. El diagnóstico se obtuvo en el turno anterior por lectura de Cloud Logging; no se volvió a consultar ni escribir QA en esta implementación.

## Política de código Local

- Autorización: espera por llamada de hasta 10 s; dependencias operativas: hasta 12 s. Configuración validada positiva y acotada. El presupuesto de operación es 25 s y reserva 250 ms antes de cada nueva llamada.
- Middleware mantiene contexto aislado por petición. X-Correlation-Id admite solo identificadores acotados sin saltos de línea. X-Request-Timeout-Ms reduce el presupuesto receptor, nunca lo amplía ni concede acceso. Se propaga únicamente a destinos internos conocidos.
- Transporte compartido: una llamada por intento, correlación, espera ajustada al presupuesto restante, lectura de cuerpo y errores HTTP acotada, máximo 64 KiB para diagnóstico HTTP. El socket de lectura recibe el tiempo restante. Conserva TLS y autorización; no permite acceso si una dependencia falla.
- El presupuesto de backend es cooperativo entre pasos HTTP: no mata transacciones, no revierte un commit ni establece un límite duro al tiempo de DB/CPU. Las consultas/bloqueos y la negociación inicial de conexión pueden requerir límites adicionales por infraestructura/driver; no se afirma un SLA de 25 s.
- El navegador aplica 35 s a autenticación, petición y lectura JSON/binaria, combina cancelación externa y propia y libera listeners/temporizador. Se elimina el fallback automático entre localhost y 127.0.0.1: una invocación no duplica una mutación.
- Fallos de transporte/429/5xx en autorización de Inventory, RH, Maintenance y Purchasing ya no se presentan como falta de permisos. Los 401/403 siguen denegados.
- Diagnóstico nuevo solo en logs Local: servicio enumerado, método, duración, resultado y correlación; sin URL, query, token, actor, tenant ni cuerpo. error.details.dependency_service enumera la dependencia, sin sobrescribir el servicio que atendió la petición.
- Formularios de servicio conservan evidencia ya confirmada; distinguen recepción, cierre y estado confirmado de avance pendiente de comprobar. No afirman que un timeout revirtió una operación. Productos siguen sin evidencia de servicio.

## Cobertura y límites

Se revisaron clientes de Production, Inventory, HR, Sales, Purchasing, Maintenance y retornos compartidos. Admin participa mediante middleware y autorización. No se sustituyeron SDK Firebase/GCS ni se agregaron conexiones compartidas entre tenants, cachés de permisos o reintentos.

Pruebas de transporte con servidor HTTP loopback sintético: demora de 6.86 s, cuerpo lento, goteo, HTTP403/503 con cuerpo lento, presupuesto descendente, rechazo antes de I/O, correlación aislada y ausencia de doble envío. Pruebas browser con interceptores locales: espera en auth/headers/JSON/blob, cancelación, ES/EN y evidencia parcial. No equivalen a una UAT remota ni benchmark de carga.

No se retiró el bloqueo material de Producción: protege consistencia entre comandos. No se agregaron pools ni se cambiaron recursos DB sin mediciones. Una optimización futura de ese bloqueo necesita pruebas de concurrencia propias. No se activan instancias ni monitoreo de pago.

## APIs afectadas

Sin nuevas rutas, permisos, tablas o migraciones. Contrato transversal: cabecera opcional X-Request-Timeout-Ms en middleware (milisegundos, solo reduce presupuesto); propagación X-Correlation-Id y diagnóstico opcional error.details.dependency_service. Aplica a las siete APIs. Corrección de clasificación503 en clientes internos, manteniendo denegaciones401/403.

Consumidores de negocio afectados sin cambiar payload: POST /v1/production/orders/{order_id}/service-evidence/{phase}, PATCH /v1/production/orders/{order_id}/status, PATCH /v1/production/order-stages/{stage_id}; cliente frontend compartido para peticiones y descargas de todos los módulos. No se modificó ninguna API en QA.

## Reversa

Revertir únicamente el corte CHG-281 de transporte, middleware/configuración, clientes, feedback y documentación. No requiere downgrade ni limpieza de datos. Conservar cambios documentales CHG-280 previos. QA no requiere rollback porque no se desplegó.


## Resultados de validación

8 pruebas de transporte aprobadas con HTTP loopback real. Frontend: 107 pruebas offline y 4 pruebas sobre formularios reales de recepción/avance ES/EN aprobadas, salida0; estas últimas interceptan mutaciones y no escriben negocio. Se verifican dos evidencias200 seguidas de status503, captura conservada y cero PATCHstage. Todos los validadores del repositorio aprobaron. `npm run verify` aprobado: 310 pruebas backend y 58 omitidas en modo sin DB. Después, `npm run verify:postgres` aprobado con 368 pruebas, cero omitidas, contra erclave_local en loopback:5434, fixtures temporales y limpieza autorizados previamente. Incluye las 55 integraciones históricas. Una advertencia de deprecación Starlette/httpx, sin fallo. Ocho Word regenerados/verificados estructuralmente; render visual pendiente.
