# purchasing-service

Duenio de proveedores, requisiciones, ordenes de compra, recepciones y seguimiento de abastecimiento.

No debe registrar pagos ni asientos directamente; debe conectar con gastos, inventario, costos y contabilidad por contratos.

## Estado

Ciclo operativo base implementado en Local y QA según [release documentado](../../../docs/operaciones/release_qa_20260914.md). El runtime FastAPI escucha en `http://127.0.0.1:8010` y persiste en el schema tenant-safe `purchasing`. Compras puede activarse para un tenant de servicios sin habilitar Inventory; las partidas inventariables conservan Inventory como autoridad condicional. Las ampliaciones organizacionales permanecen sólo Local; no hay evidencia de despliegue productivo.

## Primer corte implementado

- proveedores editables con perfil comercial, contacto y perfil fiscal minimo obligatorio (razon social, RFC, regimen, correo de facturacion y codigo postal fiscal);
- requisiciones multipardida y transiciones submit/approve/reject/cancel;
- ordenes desde requisicion aprobada o compra directa justificada, con precio independiente por partida en la UI;
- edicion de borradores, emision y cancelacion auditable de ordenes;
- recepcion comercial parcial/total multipardida de articulos y servicios, con reclamo transaccional del saldo abierto;
- reconciliacion manual idempotente que reintenta solo partidas pendientes contra `inventory-service`.

Admin permanece como autoridad transversal de sesion, permisos, unidades, monedas, condiciones de pago y folios. Inventory es una dependencia condicional exclusiva de partidas `inventory_item`; una partida `service` prohíbe articulo y almacen, y su recepcion comercial no invoca Inventory.

El RFC se normaliza y es unico por tenant. Los registros heredados incompletos siguen siendo legibles y pueden completar su perfil mediante `PATCH /v1/purchasing/suppliers/{id}`; una mutacion fiscal no puede dejar el conjunto obligatorio incompleto.

En Local, los recibos de idempotencia de proveedores, requisiciones, OC y recepciones vinculan el hash al actor autenticado. Otro actor o payload con la misma clave recibe `409` antes de heredar una respuesta o iniciar un efecto. La confirmación guarda el intento y su auditoría antes de llamar a Inventory; un intento pendiente con autor conocido puede retomarse únicamente por ese actor. El alcance vigente se vuelve a validar antes del replay.

Una reconciliación con error conserva su intento y permite al mismo actor y clave retomar únicamente las partidas pendientes. El resultado completado se repite sin nuevos movimientos. Las fechas del recibo usan el mismo formato ISO que la respuesta inicial; las fechas históricas equivalentes se normalizan al devolverlas sin reescribir su historia.

Los recibos históricos conservan su hash: sólo se aceptan si la auditoría prueba un autor único de la operación en la misma transacción. En la reconciliación que cruza transacciones, se exige además el actor reconciliador y la fecha de preparación del recibo congelado, junto con auditoría inequívoca de esa recepción. Un recibo pendiente o histórico sin prueba suficiente permanece bloqueado para revisión; no se atribuye al creador del documento ni al primer usuario que lo reintente. No requiere migración ni cambia los payloads HTTP.

Compras prepara recepciones; Almacén confirma bienes desde su bandeja, y el solicitante original acepta servicios (comprador en compra directa) mediante el contrato Purchasing. La confirmación de bienes orquesta `POST /v1/inventory/purchase-receipts` con origen/partida explícitos; servicios no generan movimiento Inventory. Permisos, transiciones y recuperación: [flujo CHG-265](../../../docs/auditorias/flujos_almacen_mensajes_2026-09-08.md) y [OpenAPI](../../../contracts/api/purchasing-service.openapi.yaml). No equiparar preparación a recepción física.

Una orden ligada a requisicion debe conservar exactamente sus partidas, cantidades, unidades, tipos y descripciones; el precio es el unico dato comercial que se agrega por linea. Los snapshots de articulo se toman desde Inventory. Cada linea de recepcion reserva saldo bajo bloqueo de la orden y usa una clave estable propia, por lo que dobles clics, carreras y conciliaciones no duplican cantidades ni movimientos.

Contrato implementado: `contracts/api/purchasing-service.openapi.yaml`. La ficha funcional y maquinas de estado viven en `modulos/03_compras_abastecimiento.md`.

## Preparación contable y alcance vigente

CC-15 · CHG-319 incorpora [documentos por División y condiciones explícitas](../../../docs/arquitectura/cont_08_compras_contexto.md), sólo Local. Nuevas requisiciones exigen `division_ref_id`; Admin deriva Sociedad y moneda de costo. Las órdenes ligadas heredan contexto, las directas requieren División y motivo. Proveedor/asignación/condiciones de esa División deben estar vigentes: la OC congela `organization_context` y `commercial_terms_snapshot` con moneda, pago, plazo y revisión. Moneda/pago omitidos se derivan; enviados deben coincidir. Editar con el mismo proveedor conserva el snapshot; cambiar proveedor en borrador toma sus condiciones explícitas, sin cambiar origen ni División. Emisión no refresca historia.

El formulario envía `expected_terms_revision` de las condiciones mostradas. Si cambian antes de guardar, el comando rechaza con 409 y conserva captura en lugar de aceptar moneda/pago/plazo distintos silenciosamente. En edición con el mismo proveedor se compara la revisión congelada del documento. El campo es opcional para otros clientes de API.

Recepciones heredan `organization_context` de la OC, incluidos servicios sin Inventory. Bienes exigen almacén de la misma División/Sociedad y conservan conversión/proof/recuperación CC-14. Las listas, bandejas y CSV filtran alcance antes de paginar; comandos y replays revalidan alcance. `GET /v1/purchasing/document-divisions` y `/document-suppliers` ofrecen proyecciones mínimas con permisos documentales existentes; no conceden CRUD de proveedores. Migración `20261012_0058` aditiva y nullable sin backfill, downgrade protegido si hay historia. Legacy sin contexto no se autoasigna: lectura/cancelación requieren alcance completo; nuevas escrituras/conversiones exigen revisión; recuperaciones CC-14 previamente preparadas se conservan. Contrato Local `1.7.0`; datos reales y aceptación integrada permanecen CC-19/20.

Disponibilidad/condiciones por División implementadas Local. El productor físico CC-14 conserva contexto y costo en cada línea de recepción antes de invocar Inventory; CC-15 hereda el contexto de OC y contrasta el almacén autoritativo contra esa División, con alcance vigente y proveedor asignado activo. `ReceiptWrite.cost_exchange_rate` expresa moneda documental→moneda Sociedad congelada: misma moneda usa 1, otra moneda exige tasa explícita positiva de hasta seis decimales. Conserva precio/moneda originales y costo convertido Decimal6, sin reinterpretar recepciones históricas sin snapshot.

`GET /v1/purchasing/receipts/{receipt_id}/lines/{line_id}/inventory-proof` entrega prueba autenticada con permiso `inventory.movement.create` y alcance actual. La confirmación envía origen `purchase_receipt` con identidad de recepción y línea, clave estable y costo Sociedad. Conciliaciones reutilizan el snapshot durable; un origen sin contexto queda pendiente de revisión. Las recepciones de servicios conservan su recorrido sin Inventory. OpenAPI Local vigente: `1.7.0`.

Inventory consulta esta prueba mediante `ERCLAVE_PURCHASING_SERVICE_URL`: loopback `http://127.0.0.1:8010` en Local aislado y HTTPS público configurado explícitamente en un futuro candidato QA/Producción. El workflow manual QA cablea la variable desde `QA_PURCHASING_API_URL`; editar esa configuración no despliega ni cambia el estado QA documentado. El callback sólo lee la prueba persistida: no toma el advisory lock de confirmación ni mantiene una transacción de escritura durante HTTP.

El precio documental conserva la precisión vigente de OC (dos decimales); el snapshot no inventa decimales históricos. La conversión usa tasa de hasta seis decimales y conserva costo base a seis: USD 4.12 × 20.123456 = MXN 82.908639. Una recepción con varias líneas no puede mezclar monedas de Sociedad porque captura una sola tasa; el rechazo identifica la línea/almacén incompatible.

Las consultas de recepciones, bandeja física y CSV filtran por todos los contextos físicos del documento antes de paginar o limitar resultados. No exponen sólo las líneas permitidas de una recepción parcialmente ajena. La confirmación, conciliación y replay revalidan alcance antes de escrituras o devolución de resultados previos; las recepciones físicas históricas sin snapshot requieren alcance completo cuando ya existen contextos organizacionales. Los servicios puros mantienen su regla de solicitante; una recepción mixta debe ser visible íntegramente. `received_at` exige zona explícita (`Z` u offset); las fechas sin zona se rechazan antes de guardar.

El detalle vigente de CC-15 está en [CONTROL_CONTABLE](../../../docs/contexto/CONTROL_CONTABLE.md) y [estado por ambiente](../../../docs/contexto/ESTADO_ACTUAL.md). Esta preparación no activa Accounting ni acredita QA. Factura/CxP, devolución a proveedor y actualización automática del costo base Inventory conservan su alcance futuro.
