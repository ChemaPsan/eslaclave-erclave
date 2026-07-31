# Contratos API

Esta carpeta alojara contratos HTTP por microservicio, idealmente en OpenAPI.

## Regla

Cada endpoint debe declarar:

- metodo y ruta;
- permisos requeridos;
- request;
- response;
- errores esperados;
- eventos publicados, si aplica.

## Servicios

- `admin-service`
- `production-service`
- `inventory-service`
- `sales-service`
- `billing-service`
- `provisioning-service`
- `integration-service`
- `hr-service`

## Contratos MVP iniciales

- `admin-service.openapi.yaml`
- `production-service.openapi.yaml`
- `inventory-service.openapi.yaml`
- `sales-service.openapi.yaml`
- `billing-service.openapi.yaml`
- `provisioning-service.openapi.yaml`
- `integration-service.openapi.yaml`
- `hr-service.openapi.yaml`

Cada contrato debe incluir `operationId`, `x-required-module`, `x-permissions` e `Idempotency-Key` en operaciones de comando.
