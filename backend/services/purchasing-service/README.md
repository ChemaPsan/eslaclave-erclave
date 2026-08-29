# purchasing-service

Duenio de proveedores, requisiciones, ordenes de compra, recepciones y seguimiento de abastecimiento.

No debe registrar pagos ni asientos directamente; debe conectar con gastos, inventario, costos y contabilidad por contratos.

## Estado

Primer corte operativo en Local (`implemented`). El runtime FastAPI escucha en `http://127.0.0.1:8010`, persiste en el schema tenant-safe `purchasing` mediante Alembic `20260824_0026` y puede activarse desde Backoffice cuando `inventory` esta habilitado. QA y Produccion permanecen sin despliegue.

## Primer corte implementado

- proveedores editables con perfil comercial, contacto y perfil fiscal minimo obligatorio (razon social, RFC, regimen, correo de facturacion y codigo postal fiscal);
- requisiciones multipardida y transiciones submit/approve/reject/cancel;
- ordenes desde requisicion aprobada o compra directa justificada, con precio independiente por partida en la UI;
- edicion de borradores, emision y cancelacion auditable de ordenes;
- recepcion parcial/total multipardida, con reclamo transaccional del saldo abierto;
- reconciliacion manual idempotente que reintenta solo partidas pendientes contra `inventory-service`.

Dependencia de activacion: `inventory`. Admin permanece como autoridad transversal de sesion, permisos, unidades, monedas, condiciones de pago y folios.

El RFC se normaliza y es unico por tenant. Los registros heredados incompletos siguen siendo legibles y pueden completar su perfil mediante `PATCH /v1/purchasing/suppliers/{id}`; una mutacion fiscal no puede dejar el conjunto obligatorio incompleto.

Las recepciones inventariables consumen `POST /v1/inventory/purchase-receipts`, una frontera dedicada que solo admite entradas con origen `purchase_order` y partida explicita. El receptor necesita `purchasing.receipt.create`, no autoridad para registrar movimientos manuales arbitrarios.

Una orden ligada a requisicion debe conservar exactamente sus partidas, cantidades, unidades, tipos y descripciones; el precio es el unico dato comercial que se agrega por linea. Los snapshots de articulo se toman desde Inventory. Cada linea de recepcion reserva saldo bajo bloqueo de la orden y usa una clave estable propia, por lo que dobles clics, carreras y conciliaciones no duplican cantidades ni movimientos.

Contrato implementado: `contracts/api/purchasing-service.openapi.yaml`. La ficha funcional y maquinas de estado viven en `modulos/03_compras_abastecimiento.md`.
