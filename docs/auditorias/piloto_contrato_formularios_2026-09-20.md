# Piloto de coherencia de formularios y contratos

> Evidencia histórica: conserva observaciones y decisiones de su fecha; no usar como estado o instrucciones actuales. Consultar [fuente vigente](../contexto/ESTADO_ACTUAL.md).

Fecha: 2026-09-20. Alcance: lectura de código Local de Producto/Servicio y Proveedor. No hubo pruebas de navegador, escritura de datos ni consulta QA. Este registro inicia la skill `erclave-form-contract`; sus hallazgos requieren una decisión funcional y pruebas antes de modificar el producto.

## Producto o servicio

Fuentes: `frontend/app.js` (`openProductServiceModal`, `buildProductServiceFromForm`, `saveProductServiceForm`), `frontend/api/production.js`, `backend/services/production-service/app/schemas.py` (`ProductServiceCreateRequest`, `ProductServiceUpdateRequest`) y contrato OpenAPI de Production.

| Observación del código | Estado | Decisión o prueba necesaria |
|---|---|---|
| `type` se elige al crear y queda deshabilitado al editar; PATCH no lo admite. `status` usa una acción distinta. | Coherente en código; corrección histórica CHG-262. | Mantener una prueba de alta/edición y permiso de estatus al tocar este formulario. |
| Producto exige artículo de Inventario compatible; Servicio oculta y limpia ese vínculo. El backend también valida ambas ramas. | Coherente en código. | Probar cambio de tipo antes de guardar, artículo inelegible y rechazo backend. |
| `category`, `cost_center`, `responsible_area` y `description` son obligatorios en pantalla, pero los schemas de alta y edición admiten `null`. | Diferencia comprobada de obligatoriedad; no implica por sí sola un defecto. | Negocio de Producción debe justificar cuáles son indispensables en el alta, cuáles pueden completarse después y cuáles pueden derivarse. |
| El control etiquetado `Responsable` se serializa como `responsible_area`; el reporte backend lo presenta como `Área responsable`. | Diferencia semántica de etiqueta observada en código. | Confirmar si el valor es un área o una persona. No convertirlo en trabajador RH ni cambiar datos históricos por inferencia. |
| `target_price` y `expected_margin` se muestran como captura obligatoria con valor inicial cero; la API acepta ausencia. | Diferencia comprobada de valor inicial. | Confirmar si cero significa decisión explícita o dato aún no definido; probar que editar no sustituya un valor existente. |

## Proveedor

Fuentes: `frontend/app.js` (`openPurchasingSupplierModal`), `frontend/api/purchasing.js`, `backend/services/purchasing-service/app/schemas.py` (`SupplierWrite`, `SupplierUpdate`), `backend/services/purchasing-service/app/api.py` y `docs/catalogos_base.md`.

| Observación del código | Estado | Decisión o prueba necesaria |
|---|---|---|
| El backend exige códigos activos de `currencies` y `payment_terms` en Administración; el alta UI sólo muestra MXN/USD/EUR y contado/crédito 30. | Desajuste de cobertura comprobado en código: un código activo adicional no aparece para alta. | Consultar los catálogos autorizados y mostrar códigos activos; preservar valor histórico al editar. Probar catálogo nuevo e inactivo. |
| La edición inyecta en selectores un código existente ausente de la lista corta. | Protección existente en código; corrección histórica CHG-262. | Mantener prueba de edición sin sustitución silenciosa. |
| Alta exige perfil fiscal completo. El backend exige RFC y los demás campos fiscales al iniciar el perfil. | Coherente para el flujo fiscal mexicano actual. | Cualquier ampliación de país o régimen requiere regla funcional y validación fiscal correspondiente; no ampliar el selector por apariencia. |

### Seguimiento Local CHG-284

El desajuste de cobertura de moneda y condiciones quedó corregido en Local: Purchasing publica referencias activas propias, consultadas desde Administración, y el formulario consume esos valores en alta y edición. Administración autoriza explícitamente a los permisos consumidores de Compras para listar y validar catálogos. Se conserva la inyección del código histórico cuando no aparece en la lista activa. El caso Playwright quedó agregado y pendiente de ejecución con el stack Local aislado encendido; las decisiones de Producto/Servicio continúan abiertas.

## Criterio del siguiente corte

Resolver primero la obligatoriedad y semántica de los campos de Producto/Servicio con negocio. Para Proveedor, corregir la fuente de moneda y condiciones desde el catálogo implementado, sin introducir entradas libres. El corte debe incluir cliente, UI, pruebas conductuales de alta/edición, permisos, valor histórico y documentación. La lectura de código anterior no certifica que el recorrido funcione en navegador o QA.

## APIs afectadas

Contratos modificados: ninguno. Consumidos sin cambio por los formularios: `POST /v1/production/product-services` y `PATCH /v1/production/product-services/{id}` (Production, permisos `production.product_service.create` y `.update`); `POST /v1/purchasing/suppliers` y `PATCH /v1/purchasing/suppliers/{id}` (Purchasing, permisos `purchasing.supplier.create` y `.update`). Esta auditoría no llamó ni modificó endpoints. APIs no tocadas: las demás.
