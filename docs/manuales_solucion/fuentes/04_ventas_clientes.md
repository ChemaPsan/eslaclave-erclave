# Manual funcional de Ventas: codigos de negocio

- Audiencia: ejecutivos y responsables comerciales
- Alcance por ambiente: Local y QA
- Ultima revision: 2026-08-23
- Capacidades cubiertas: codigos de clientes, cotizaciones, pedidos y entregas

## Proposito

Ventas utiliza folios visibles independientes de IDs tecnicos. Administracion puede asignarlos o permitir captura manual.

## Uso

En modo administrado, el codigo se asigna al guardar. En modo manual, capture un valor unico con letras, numeros, punto, guion o guion bajo; Sales lo normaliza a mayusculas.

El codigo comercial y los nombres de producto se conservan en cotizaciones y pedidos. El articulo de Almacenes puede tener otro codigo logistico; la relacion siempre se resuelve por ID, nunca por texto.

## Integraciones y mensajes

Si Administracion no reserva el folio, no se crea el documento. Reintentar con la misma clave obtiene el mismo folio. Cambiar prefijo no altera documentos existentes.

## Cobertura

Aplica a Clientes, Cotizaciones, Pedidos y Entregas Local. Devoluciones y facturacion permanecen planeadas.
