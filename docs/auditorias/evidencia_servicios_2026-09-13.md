# Evidencia de servicios — CHG-274

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.

## Flujo implementado

1. La clasificación se resuelve en backend desde la receta y su producto/servicio; no se acepta una bandera enviada por el navegador.
2. Antes de esperar recursos o iniciar, un servicio requiere evidencia escrita inicial. El cambio abre captura de recepción. El acceso directo por API también se bloquea.
3. El formulario de porcentaje despliega la sección de cierre cuando esa actualización completará todas las etapas al100%. Si se inicia directamente desde avance, aparece también recepción pendiente. Registrar100% de una etapa intermedia no exige el cierre de toda la orden.
4. Evidencia se guarda antes del comando. Si el comando falla, la evidencia guardada permanece y el reintento no la duplica. Los dos momentos no se sobrescriben silenciosamente; reenvío idéntico devuelve lo registrado y contenido distinto explica el conflicto. Archivo malformado no cambia el estado ni pierde captura.
5. La orden incluye consulta de evidencia y descarga autenticada; no existen URLs públicas. Se conserva texto, actor y fecha. Las órdenes históricas terminadas no se reabren ni reciben evidencia inventada. OP-000002 permanece terminada; OP-000003 sigue liberada hasta que el usuario opere su flujo.

## Archivos, optimización y caducidad

-  Tres archivos por recepción y tres por cierre. Texto de3 a4000 caracteres, obligatorio; archivos opcionales.
-  Entrada foto5MiB,20 millones de píxeles y una imagen estática. Se corrige orientación EXIF, se reduce a1600px como máximo y se recomprime a WebP <=300KiB con reducción progresiva si es necesario. Solo se escribe la copia optimizada; no se conservan originales, EXIF, GPS o metadatos. Las imágenes corruptas, animadas o excesivas se rechazan con mensaje traducido.
-  Documentos2MiB: PDF, TXT UTF-8, DOCX y XLSX. Se comprueba formato básico/contenedor y se rechazan macros y archivos no permitidos; no es un antivirus. La descarga fuerza attachment/nosniff y no ejecuta ni previsualiza documentos activos.
-  Body HTTP21MiB máximo antes de parsear JSON, también para carga por chunks; cada archivo transporta base64 validado con límites. No se guarda base64 en DB/auditoría.
-  La fecha vence365 días después de la carga. Acceso rechazado al vencimiento incluso antes del borrado físico. Local ejecuta purga al arrancar y cada hora; si está apagado, elimina al siguiente arranque. Limpia también objetos locales huérfanos que superan la retención.
-  QA/Prod usan bucket GCS privado dedicado, acceso público prevenido, acceso uniforme, lifecycle Delete365d, sin versiones, soft-delete ni políticas/holds que impidan borrar. La escritura falla si falta configuración/política. Artefacto: `infra/qa/service-evidence-lifecycle.json`. No se creó/configuró ningún bucket remoto en este corte. GCS aplica borrado según su ventana operativa; la API deniega acceso desde expires_at. Infra debe excluir copias/respaldos de adjuntos que excedan este plazo.
-  Local guarda bytes fuera de frontend en `.local/service-evidence`, ignorado por Git; metadatos y descripción pertenecen exclusivamente al schema production. No copiar ese directorio a QA, imágenes Docker ni repositorios.

## Datos, permisos y reversa

Migración0036 crea `production.service_evidence` (tenant/orden/fase único, texto, actor, fecha, huella para reintento) y `service_evidence_files` (nombre, tipo, tamaño, SHA256, clave privada y vencimiento/borrado). FKs compuestas solo dentro del servicio. Índices por propietario y vencimiento. No modifica datos operativos previos ni hace backfill.

Escritura de recepción requiere `production.order.start` o `production.order.wait_resources`; cierre `production.order_stage.complete`; descarga `production.order.read`, todos con tenant y orden propios. No se agregan permisos ni seeds. Comandos conservan sus permisos originales.

La reversa0036 solo procede con tablas de evidencia vacías; si hay texto registrado se detiene para no perderlo. No borrar evidencia empresarial automáticamente para regresar una migración. Conservación física es parte de la política de adjuntos; no afecta la descripción histórica.

## APIs afectadas

| Método/ruta | Cambio |
|---|---|
| POST /v1/production/orders/{order_id}/service-evidence/{phase} | Nuevo; description y hasta3 files(filename/content_base64), phase start/finish. Devuelve texto/metadatos sin bytes. Permisos anteriores. |
| GET /v1/production/orders/{order_id}/service-evidence/files/{file_id} | Nuevo; descarga autenticada privada;410 vencido,404 fuera de tenant/orden. |
| GET /v1/production/orders y GET /v1/production/orders/{order_id} | Añaden is_service_order y service_evidence. |
| PATCH /v1/production/orders/{order_id}/status | Requisitos de evidencia para órdenes de servicio; payload/permisos originales. |
| PATCH /v1/production/order-stages/{stage_id} | Valida recepción y cierre antes del100% total y transición automática. Payload/permisos originales. |

Otros servicios y órdenes de producto: sin cambios de reglas. Contrato Production actualizado y verificado contra rutas FastAPI.

## Validación y límites

- 16 pruebas focalizadas aprobadas (14 de optimización/almacenamiento y2 PostgreSQL): optimización JPEG/PNG/WebP/HEIC y metadatos, formatos/tamaños, almacenamiento privado, SQL real y archivos. La integración usa únicamente órdenes sintéticas del tenant autorizado, demuestra bloqueos, idempotencia, aislamiento, vencimiento y conservación de texto; limpia sus propios IDs/objetos.
- 3 pruebas API adicionales aprobadas: alta/descarga válidas y headers de nombre/CORS, permisos/rechazo de producto y límite de body previo al parseo.
- 7 pruebas de navegador aprobadas: ES/EN, recepción antes de espera, cierre solo al100%, captura/archivos preservados tras422, reintento sin duplicar recepción, ausencia de campos en producto, evidencia escrita con adjuntos vencidos; ancho390 sin overflow. HTTP de escritura interceptado.
- Regresión completa:185/185 pruebas browser aprobadas (7.6m). `npm run verify` aprobado: validadores/compilación/sintaxis80,292 backend,58 omitidas en corrida sin DB. De esas58, margen(1) y evidencia(2) se probaron aparte en PostgreSQL real;55 generales previas siguen pendientes.
- Reversa0036 ensayada dentro de transacción: downgrade/upgrade sin pérdida con tablas vacías; la prueba verifica bloqueo si ya existe evidencia.
- Capturas de ancho390/760/1280 y oscuro390 inspeccionadas en `docs/auditorias/evidencias/service_evidence_20260913/`. Muestran un rechazo422 simulado para verificar foco/texto/captura; no son un reporte de error real del servicio. El porcentaje usa diseño ampliado solo en órdenes de servicio.

No se declara UAT ni despliegue QA. No se modificaron las órdenes reales del usuario. Conservamos las limitaciones históricas de las55 integraciones generales sin ejecutar; evidencia nueva se prueba contra Local real por selección explícita.
