# hr-service

Servicio propietario de áreas laborales, puestos/capacidad nominal y expedientes mínimos de trabajadores por tenant. No administra nómina, asistencia, turnos, documentos adjuntos, beneficiarios ni datos médicos en este corte.

Requiere entitlement `hr`, permisos `hr.area.*` y `hr.position.*`, `Idempotency-Key` en comandos y PostgreSQL mediante `ERCLAVE_HR_DATABASE_URL`.

Los seis comandos de alta/edicion de areas, puestos y trabajadores vinculan actor autenticado, tenant, operacion, clave y payload. Otro actor con la misma clave recibe `409 idempotency_key_reused`; el actor original conserva su replay. Los recibos previos solo se recuperan si `hr.audit_events.created_at` coincide con la transaccion del recibo y su accion `hr.<operacion>` identifica un actor unico coincidente. Las asignaciones por Division ya vinculaban actor en su propia huella. Sin migracion ni cambios de payload publico.

## Preparación contable y alcance vigente

CC-10 agrega confirmación explícita de tarifa Decimal en moneda base de Sociedad para la asignación del puesto, con fecha y Sociedad confirmadas. Los registros históricos sin moneda permanecen sin confirmar. La consulta por División devuelve capacidad declarada y IDs únicos de trabajadores elegibles; no descuenta compromisos ni permite sumar al trabajador compartido como recursos independientes. Véase [CONTROL_CONTABLE](../../../docs/contexto/CONTROL_CONTABLE.md) y [estado por ambiente](../../../docs/contexto/ESTADO_ACTUAL.md). La preparación no activa Accounting.

El contrato [OpenAPI RH](../../../contracts/api/hr-service.openapi.yaml) incluye `GET /v1/hr/division-production-capacity` y la moneda de `PUT /v1/hr/positions/{resource_id}/division-assignments/{division_id}`. `division-positions` sólo ofrece tarifas confirmadas que coinciden con la Sociedad/moneda vigentes; la elegibilidad de trabajadores permanece independiente de costeo. El contrato histórico `/production-capacity` no cambia y la fabricación dimensionada sigue condicionada a sus propios cortes.
