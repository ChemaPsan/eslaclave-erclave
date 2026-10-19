# Plantillas documentales tenant-safe

## Objetivo

Toda salida imprimible o PDF debe compartir la identidad visual configurada por el cliente, sin copiar logos o colores dentro de Ventas, Produccion u otros dominios.

## Autoridad y contrato actual

- Administracion es owner de `document.template` y lo expone mediante `GET/PUT /v1/document-template`.
- La configuracion pertenece al tenant e incluye logo, color primario, color de acento, color de texto, pie y numeracion de pagina.
- Los colores usan `#RRGGBB`. En Local el logo puede guardarse o quitarse como data URL PNG, JPEG o WebP; frontend y backend validan tipo y limite decodificado de 1 MB, y backend comprueba la firma binaria. Antes de QA/Produccion debe migrarse a object storage y conservarse solo una referencia segura.
- Ventas y Produccion leen la plantilla; no pueden modificarla ni mantener una variante oculta.

## Consumidores

El encabezado, pie, colores y logo aplican a cualquier documento generado por el sistema, incluidos:

- cotizaciones, confirmaciones de pedido, remisiones y devoluciones;
- ordenes de produccion, hojas de ruta y reportes de consumo;
- ordenes de compra, recepciones, facturas, reportes y documentos futuros.

En el corte Local la impresion de Cotizaciones y Ordenes de Produccion ya consume la configuracion. Los demas consumidores deben integrarla al implementar su generador PDF.

CC-17 (CHG-322, Local) resuelve la plantilla completa Corporativo → Sociedad → Division junto con la identidad efectiva de Division, Sociedad y Emisor mediante `GET /v1/configuration/document-presentation/division/{division_id}`. Admin exige pertenencia y alcance de la Division, un permiso consumidor de Ventas o Produccion y organizacion activa. El servicio propietario conserva el snapshot en su propio schema: Sales al aprobar la cotizacion y Production en la transaccion que libera la orden. Incluye IDs y nombres/codigos organizacionales, razon social, datos fiscales/domicilio del Emisor y plantilla con su origen. Reintentos recuperan el mismo documento y snapshot; cambios posteriores de Admin no lo reescriben.

La cotizacion en borrador o cotizada consulta la identidad vigente al imprimir. La cotizacion aprobada y la orden liberada imprimen exclusivamente el snapshot guardado. Un documento historico anterior a CC-17 sin snapshot informa indisponibilidad de presentacion y no inventa identidad vigente. Los demas generadores siguen pendientes de una decision por documento y su propia integracion; el contrato de Admin es de lectura y no concede edicion de la plantilla.

Los generadores Local recargan el registro autoritativo cuando el ID solicitado no esta en la cache de presentacion, informan un error visible si deja de existir y escapan todo texto operativo antes de insertarlo en el documento imprimible. Un usuario sin `admin.setting.update` puede consultar la identidad si su permiso consumidor lo permite, pero no recibe controles editables.

## Regla de evolucion

Cada nuevo documento PDF debe declarar en sus criterios de aceptacion: autoridad de datos, plantilla usada, momento del snapshot, permisos de generacion, trazabilidad y prueba visual. Si se requiere conservar exactamente una emision historica, el servicio propietario almacenara un snapshot de la plantilla o el artefacto inmutable; nunca reconstruira historia silenciosamente con la plantilla vigente.
