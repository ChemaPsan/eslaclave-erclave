# Tenants y ambientes autorizados

## Tenant de desarrollo funcional

| Campo | Valor |
|---|---|
| Nombre | ERClave Demo QA |
| Tenant ID | `ten_739ee59d765d5e14818674800d` |
| Uso | Desarrollo local y pruebas funcionales expresamente autorizadas |

## Reglas obligatorias

- Antes de escribir datos, resolver y mostrar el `tenant_id` efectivo.
- Si no coincide con `ten_739ee59d765d5e14818674800d`, detener la operacion salvo autorizacion explicita para ese tenant.
- El tenant del equipo de QA no recibe datos dummy ni modificaciones exploratorias.
- Una preferencia en `localStorage` no prueba autorizacion; el backend debe validar `session/context`.
- Nunca copiar secretos, tokens, passwords ni URLs con credenciales a estos documentos o a la salida de `session:context`.
- Las migraciones locales autorizadas deben verificar host, puerto y base antes de ejecutarse.
- No ejecutar migraciones, seeds, benchmarks o despliegues sobre Cloud SQL QA o Produccion sin autorizacion explicita y plan de rollback.

Este archivo documenta limites, no concede permisos adicionales.
