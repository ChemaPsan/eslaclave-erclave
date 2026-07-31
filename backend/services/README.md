# Microservicios ERClave

Cada microservicio debe ser dueno de su dominio, datos, reglas y API.

## Servicios objetivo

- `production-service`
- `inventory-service`
- `purchasing-service`
- `sales-service`
- `expenses-service`
- `costing-service`
- `reporting-service`
- `admin-service`
- `accounting-service`
- `hr-service`

## Regla de oro

Un servicio no debe modificar directamente la base de datos de otro servicio. Debe comunicarse por API o eventos documentados.

## Cada servicio debe documentar

- entidades propias;
- endpoints;
- eventos publicados;
- eventos consumidos;
- permisos;
- reglas de auditoria;
- pruebas de contrato.
