# ERClave - Operaciones

Esta carpeta guarda guias paso a paso para configurar servicios externos, ambientes,
credenciales, bases de datos, despliegues y tareas operativas del proyecto.

La idea es que cualquier integrante pueda repetir una configuracion sin depender de
memoria o instrucciones sueltas en una conversacion.

## Guias disponibles

- `cloud_sql_postgres_qa.md`: crear y conectar una base PostgreSQL QA en Google Cloud SQL.

## Reglas de uso

- No guardar contrasenas, tokens, llaves privadas ni archivos `.env` reales en el repo.
- Usar valores placeholder como `<GCP_PROJECT_ID>` o `<DB_PASSWORD>`.
- Registrar cambios importantes en `TRAZABILIDAD.md`.
- Preferir ambientes separados: local, QA y produccion.
- Para ERClave, la base compartida en la nube debe iniciar como QA, no como produccion.
