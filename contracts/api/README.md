# Contratos API

Esta carpeta contiene contratos HTTP OpenAPI. Contrato no implica runtime: operaciones futuras declaran `x-implementation-status: planned`; validar rutas implementadas con `python tools/validators/validate_openapi_runtime.py`. Estado de cada dominio en [módulos](../../modulos/README.md).

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
- `purchasing-service`
- `maintenance-service`
- `costing-service` (sólo catálogo básico Local)

## Contratos MVP iniciales

- `admin-service.openapi.yaml`
- `production-service.openapi.yaml`
- `inventory-service.openapi.yaml`
- `sales-service.openapi.yaml`
- `billing-service.openapi.yaml`
- `provisioning-service.openapi.yaml`
- `integration-service.openapi.yaml`
- `hr-service.openapi.yaml`
- `purchasing-service.openapi.yaml`
- `maintenance-service.openapi.yaml`
- `costing-service.openapi.yaml`

Cada contrato debe incluir `operationId`, `x-required-module`, `x-permissions` e `Idempotency-Key` en operaciones de comando.
