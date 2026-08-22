# hr-service

Servicio propietario de áreas laborales, puestos/capacidad nominal y expedientes mínimos de trabajadores por tenant. No administra nómina, asistencia, turnos, documentos adjuntos, beneficiarios ni datos médicos en este corte.

Requiere entitlement `hr`, permisos `hr.area.*` y `hr.position.*`, `Idempotency-Key` en comandos y PostgreSQL mediante `ERCLAVE_HR_DATABASE_URL`.
