# admin-service

Servicio implementado de Administración: tenants, identidad y membresías, roles/permisos, entitlements, configuración, auditoría y autorización transversal. Las capacidades Local y QA se consultan en [ESTADO_ACTUAL](../../../docs/contexto/ESTADO_ACTUAL.md); no se deduce despliegue por existencia de código.

## Autoridad y relaciones

- La identidad global vive en users; memberships vincula usuario y tenant. Los roles se asignan a la membresía.
- En Local Emisores, Sociedades y Divisiones tienen autoridad normalizada; organization.profile es proyección compatible. Ver [CONT-02](../../../docs/arquitectura/cont_02_administracion_organizacional.md).
- Sesión v2 y alcance efectivo por División se rigen por [CONT-03](../../../docs/arquitectura/cont_03_sesion_alcances.md). Un permiso no sustituye el scope; no asumir todas las Divisiones ante alcance vacío.
- Admin es dueño de unidades, monedas, condiciones de pago, numeración y configuración documental. El catálogo de centros se presenta en Admin, pero pertenece a Costing: [ownership](../../../docs/arquitectura/ownership_datos_mvp.md).
- Firebase autentica; membresías, entitlements y permisos pertenecen a ERClave. Backoffice usa una allowlist separada y no concede acceso operativo por sí mismo.

## Contratos y ejecución

El inventario de operaciones, payloads y permisos está en [OpenAPI Admin](../../../contracts/api/admin-service.openapi.yaml). No duplicar aquí listas parciales de endpoints. Las mutaciones aplicables requieren Idempotency-Key, validan autorización y registran auditoría con correlación.

Arranque canónico desde la raíz: backend/scripts/start_local.ps1. Diagnóstico desde backend: uvicorn services.admin_service_adapter:app --reload --port 8000, sólo con configuración Local explícita. Ver [guía backend](../../README.md).

Los permisos se extraen de los contratos mediante [permissions.py](app/seeds/permissions.py); [seed_admin_mvp.py](../../scripts/seed_admin_mvp.py) los sincroniza. El [seed demo](../../scripts/seed_admin_qa_demo.py) declara siete módulos operativos; no demuestra que un ambiente esté desplegado ni autoriza escrituras QA. Aplicar el [flujo gobernado](../../../docs/operaciones/flujo_local_a_qa.md).

## Límites y continuidad

Onboarding e invitación conservan estados de entrega pendiente si el efecto Firebase falla después de persistir. La conciliación durable, endurecimiento service-to-service y aceptación integrada pendientes se siguen en [PENDIENTES](../../../docs/contexto/PENDIENTES.md). Separación y tareas por submódulo: [CONTROL_CONTABLE](../../../docs/contexto/CONTROL_CONTABLE.md).
