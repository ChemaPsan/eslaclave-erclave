# CONT-04 Configuración por alcance

CHG-322 - 2026-10-14 - CC-17 integra consumo y snapshot de cotizaciones y ordenes de produccion en Local. La infraestructura Admin proviene de CHG-296; los demas generadores requieren integracion propia.

## Recorrido implementado

Administración → Organización → Sociedades o Divisiones → Plantilla por alcance. Se necesita lectura del catálogo organizacional para localizar el registro y admin.setting.read para abrir; admin.setting.update para guardar/restaurar. Sociedad/División activas y del tenant; también deben estar activos Sociedad y Emisor padres. Un usuario restringido sólo consulta/ajusta sus Divisiones; ajustar Sociedad requiere alcance global porque afecta también Divisiones no seleccionadas.

La plantilla corporativa actual se mantiene en admin.tenant_settings. El valor resuelto usa Corporativo → Sociedad → División. Cada override reemplaza la plantilla completa, no mezcla campos. La pantalla informa el origen, permite editar colores, pie y numeración, conserva el logo resuelto y ofrece Volver a heredar. No cambia globalmente el formulario corporativo ni permite edición de logos desde este nuevo editor.

Guardar exige expected_revision e Idempotency-Key. Repetición idéntica devuelve resultado anterior; clave con payload diferente y revisión obsoleta se rechazan. Restaurar guarda value null y aumenta la revisión: no borra historia ni permite reutilizar una revisión vieja. Un cambio del padre no altera un override completo; al restaurar se consulta la configuración superior vigente.

El editor ES/EN conserva captura y clave de reintento ante fallos, bloquea controles durante envío y descarta una respuesta si el editor fue cerrado o sustituido. CSS limitado al formulario; prueba en contenedor de 320px. El origen sólo se actualiza tras respuesta confirmada.

## Persistencia y recuperación

Nueva tabla admin.scoped_settings: PK compuesta tenant_id/key/scope_type/scope_ref_id, value JSONB nullable, revision positiva y timestamps. La PK comienza por tenant y cubre la consulta exacta. key queda restringida a document.template en este piloto, scope_type a society/division. FK de tenant dentro del schema Admin; referencia polimórfica de alcance validada contra tablas del mismo tenant en backend. No hay FK ni escritura entre servicios.

Migración 20260927_0039, padre 20260925_0038, aditiva y sin backfill. Plantillas corporativas existentes siguen siendo autoridad del nivel Corporativo. Upgrade/downgrade vacío/upgrade probados en PostgreSQL Local 5434/erclave_local; tenant autorizado verificado antes de escribir. Downgrade rechaza tabla no vacía, incluidos resets, para no destruir historial; recuperación ordinaria mediante comando de restauración o forward-fix.

Comandos, lectura de herencia y cambios corporativos de plantilla usan el bloqueo organizacional del tenant; auditoría/idempotencia y override se guardan en la misma transacción. El permiso y alcance se comprueban en API; las referencias se revalidan dentro de la transacción. No hay retención destructiva de configuración.

## Contrato de formulario

| Control | Propósito | Validación |
|---|---|---|
| Registro Sociedad/División | Define alcance; viene de la lista con código/nombre | Backend valida tenant, estado, padre y alcance. |
| Tres colores | Configuración visual propia | Formato hexadecimal existente; rutas value.primary_color/accent_color/text_color. |
| Pie | Texto de plantilla | Máximo 300, opcional. |
| Numeración | Preferencia de plantilla | Booleano. |
| Guardar ajuste | Crea/reemplaza plantilla completa | Revisión e idempotencia; permiso de actualización. |
| Volver a heredar | Retira ajuste manteniendo revisión/historia | value null; mismo permiso y controles de concurrencia. |

## APIs afectadas

Nuevas Admin GET/PUT `/v1/configuration/document-template/{scope_type}/{scope_id}`. GET requiere admin.setting.read; PUT admin.setting.update e Idempotency-Key. PUT recibe expected_revision y value (plantilla completa o null). Ambos devuelven scope_type/id, revision, override, resolved_from_scope/id y value resuelto. Scope type sólo society/division. Errores 400/403/404/409/422 conforme al sobre existente; configuration_revision_conflict tiene traducción propia.

GET `/v1/session/context` agrega disponibilidad de capacidades conforme a [matriz](matriz_capacidades_organizacionales.md). GET/PUT `/v1/document-template` y PUT `/v1/settings/{key}` conservan su forma; escrituras de document.template toman el mismo bloqueo para ordenar cambios con overrides. La UI organizacional sigue consumiendo GET `/v1/organization/societies` y `/v1/organization/divisions` sin cambios contractuales. APIs operativas ajenas no cambian.

## Límites y siguiente corte

La plantilla por alcance se resuelve en Admin. Cotizaciones y ordenes de produccion consumen plantilla e identidad por Division conforme a CC-17; no se propaga una Division implicita ni se reescriben documentos historicos. Otros generadores incorporaran consumo y snapshot segun su contrato. La separacion operativa completa exige los demas trabajos pendientes.

Faltan catálogo Costing CONT-05, folios CONT-06 y maestros/documentos CONT-07/08. Antes de exigir centros se aplica la política confirmada de flujos habilitados. El patrón deberá trasladarse a tablas de cada servicio dueño; Admin no alojará configuraciones internas ajenas. Ninguna plantilla activa libros, periodos, analítica o Accounting.

Evidencia del corte en TRAZABILIDAD CHG-296: pruebas API/dominio, PostgreSQL con rollback del tenant permitido y navegador interceptado. No equivale a UAT ni a despliegue QA.

## Consumo CC-17 · CHG-322 Local

Admin publica `GET /v1/configuration/document-presentation/division/{division_id}` para consumidores autorizados de cotizaciones u ordenes de produccion. Devuelve la plantilla efectiva completa, su origen y la identidad de Division, Sociedad y Emisor dentro del tenant y alcance permitidos. Sales guarda el snapshot al aprobar la cotizacion; Production lo guarda al liberar la orden. El snapshot es parte de la transaccion del documento, no un override de Admin. La impresion de documentos historicos con snapshot usa ese valor, mientras una cotizacion aun no aprobada consulta el valor vigente. Los documentos anteriores sin snapshot no se reconstruyen con la configuracion actual. Ver [regla documental](plantillas_documentales.md) y [OpenAPI Admin](../../contracts/api/admin-service.openapi.yaml).

Las configuraciones propias de cada servicio siguen siendo propiedad de ese servicio. Esta integracion no traslada condiciones comerciales, tarifas, recursos ni numeracion de documentos a Admin. Otros generadores imprimibles requieren adaptacion explicita al incorporarse; CC-18 trata folios de los dueños restantes.
