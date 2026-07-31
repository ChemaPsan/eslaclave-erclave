# hr-service

Servicio propietario de áreas laborales y puestos/capacidad nominal por tenant. No administra empleados, expedientes, nómina, asistencia ni turnos en este corte.

Requiere entitlement `hr`, permisos `hr.area.*` y `hr.position.*`, `Idempotency-Key` en comandos y PostgreSQL mediante `ERCLAVE_HR_DATABASE_URL`.
