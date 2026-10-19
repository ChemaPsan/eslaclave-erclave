# CC-21 - Costo estimado de cotizaciones

## Implementacion CHG-325 - 2026-10-14 - Local

Production conserva por asignacion activa de producto/servicio a Division un costo unitario estimado confirmado en moneda base de Sociedad, con Sociedad, moneda, revision y fecha de confirmacion. El responsable con permiso `production.product_service.update` puede confirmarlo o retirarlo; cero es valido. El contrato puntual entrega `data: null` a Sales si falta confirmacion, la asignacion/producto esta inactivo o la Sociedad/moneda confirmada ya no corresponde al contexto vigente. El costo global `standard_cost` de receta/producto no adquiere moneda por inferencia.

Sales conserva una tasa explicita para el estimado de una cotizacion dimensionada cuando moneda de Sociedad y moneda documental difieren; si coinciden, la tasa es uno. Al fijar contexto, editar el borrador y enviarlo, vuelve a consultar la fuente por Division y muestra una vista previa. Al aprobar consulta de nuevo y congela el resultado. Cada partida guarda en JSONB el costo unitario e importe originales, Sociedad/moneda, tasa, importe convertido, revision y fecha de fuente; encabezado conserva estado y total. Si falta costo de cualquier partida o tasa, costo/margen total quedan nulos y se permite aprobar. La conversion usa Decimal, original a seis decimales y convertido a dos con HALF_UP; el margen compara importes de moneda documental solo cuando el total esta completo y es distinto de cero.

El pedido copia sin recalcular el snapshot aprobado por encabezado y partida. Su `cost_currency`/`cost_exchange_rate` de surtimiento siguen siendo distintos de la tasa del estimado. Cotizaciones nuevas sin Division no usan `standard_cost` global como costo confiable. Filas historicas mantienen sus numeros y snapshots nulos; la interfaz las marca sin verificacion monetaria y los reportes no deben presentarlas como estimados confirmados. La migracion `20261014_0062` es aditiva/nullable y su downgrade se bloquea cuando existe historia nueva.

Este corte no interpreta costos previos, no activa Accounting y no promueve QA. La aceptacion integrada pertenece a CC-20 y los datos historicos a CC-19. Las fuentes Markdown de manual son vigentes; Word necesita regeneracion y revision visual.

## Revision de 2026-10-14

Esta adaptacion de Sales quedo fuera de la numeracion CC al cerrar CC-07 (cotizacion a pedido) y CC-08 (costo operativo de servicios). Se registra como CC-21 para conservar un criterio de cierre propio. No cambia el estado implementado de esos recorridos ni activa Accounting.

## Hallazgos en Local

1. Sales obtiene `standard_cost` de `production.product_services` mediante `ProductReference`. El contrato no incluye moneda, Sociedad ni confirmacion monetaria de ese importe. El producto es maestro compartido y puede asignarse a varias Divisiones.
2. Al crear o editar partidas, `SalesRepository._write_lines` multiplica ese costo por la cantidad, redondea a dos decimales y lo guarda en `sales.quote_lines.standard_unit_cost_snapshot` y `estimated_cost`. Suma las partidas y calcula margen contra el total documental. No convierte ni verifica que ambos importes tengan la misma moneda.
3. Asignar contexto de Division/Sociedad a la cotizacion no revisa el costo. Enviar y aprobar revalidan producto/unidad y congelan presentacion documental, pero no procedencia monetaria del estimado.
4. El pedido copia costo y margen estimados de la cotizacion aprobada, incluidos sus snapshots por partida. La ruta de surtimiento fija despues `cost_currency` y `cost_exchange_rate` para el costo real, sin reparar el estimado ya copiado.
5. El reporte `commercial-margin` trata `estimated_margin` y `actual_margin`, que ya son porcentajes, como si fueran importes para calcular `margin_percent`. Esta columna puede mostrar un porcentaje incorrecto. La tarjeta de pedido usa cero para estimados nulos.

## Regla vigente y criterio de cierre propuesto

La politica CHG-309 exige costo original en moneda base de Sociedad y tasa explicita cuando la cotizacion usa otra moneda. Un `standard_cost` global sin moneda no demuestra ese origen; tampoco permite inferir tasa desde la moneda del documento. No reinterpretar cotizaciones o pedidos historicos.

Para cerrar CC-21, Sales debe consumir un costo estimado trazable por partida y Sociedad, conservar moneda original, tasa y monto convertido a moneda documental, y calcular margen solo con importes comparables. La tasa usa unidades de moneda documental por una unidad de moneda de costo; si coinciden, es uno. El snapshot de aprobacion y la copia al pedido deben preservar esos valores sin consultar maestros actuales. Si falta un costo confirmado o la tasa, la cotizacion puede aprobarse con costo y margen estimados nulos; el usuario confirmo esta regla el 2026-10-14. Corregir reporte y presentacion de valores nulos como parte del mismo corte. Verificar permisos, idempotencia, precision, historia y moneda distinta en Local antes de considerar QA.

La vista previa debe existir en borrador al fijar la Division, actualizarse al editar/enviar y volver a verificarse al aprobar. Un alta nueva sin Division no presenta como confiable el costo global sin moneda. Production confirma el costo unitario por Division en moneda base de Sociedad; cero es valido y la falta de confirmacion produce estimado nulo. Un cambio posterior del maestro no modifica cotizaciones aprobadas ni pedidos derivados.

## Limites

Esta revision identifica el defecto y su alcance; no implementa calculo nuevo, migracion ni backfill. CC-19 resuelve datos historicos con mapeo real y CC-20 la aceptacion integrada.
