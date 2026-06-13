# Eventos entre modulos

Formato sugerido:

```json
{
  "id": "evt_001",
  "type": "production.order.created",
  "version": 1,
  "occurredAt": "2026-06-13T10:28:00-06:00",
  "tenantId": "tenant_001",
  "source": "production-service",
  "correlationId": "corr_001",
  "payload": {}
}
```

## Reglas

- Todo evento debe tener `id`, `type`, `version`, `occurredAt`, `tenantId`, `source`, `correlationId` y `payload`.
- Los consumidores deben ser idempotentes.
- Los eventos no deben depender de campos visuales del frontend.
- Los eventos deben representar hechos pasados, no instrucciones.

## Eventos iniciales

| Evento | Publica | Consumen |
|---|---|---|
| `sales.order.approved` | sales-service | inventory-service, production-service, reporting-service |
| `inventory.shortage.detected` | inventory-service | purchasing-service, production-service, reporting-service |
| `production.order.created` | production-service | inventory-service, costing-service, reporting-service |
| `production.order.completed` | production-service | inventory-service, costing-service, accounting-service, reporting-service |
| `purchasing.receipt.completed` | purchasing-service | inventory-service, expenses-service, costing-service, reporting-service |
| `expenses.invoice.registered` | expenses-service | costing-service, accounting-service, reporting-service |
| `costing.variance.detected` | costing-service | reporting-service, accounting-service |
| `accounting.entry.generated` | accounting-service | reporting-service |
