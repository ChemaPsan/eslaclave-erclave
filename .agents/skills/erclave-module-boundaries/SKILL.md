---
name: erclave-module-boundaries
description: Auditar cobertura de agentes y proteger fronteras funcionales, datos y contratos al agregar un módulo ERClave o modificar integraciones entre módulos. Usar para detectar dominios sin responsables y contratos que crucen ownership; no exige una skill duplicada por cada módulo.
---

# Cobertura y fronteras por módulo

Cruzar `modulos/README.md`, fichas funcionales, `AGENTES.md`, manifiestos frontend, servicios y contratos. Para cada dominio identificar agente de negocio y técnico reales en su sección, fuentes, estado Local/QA/planned y skills aplicables. Un conteo global de encabezados no demuestra que cada módulo tenga ambos roles.

Consultar `docs/arquitectura/cobertura_agentes_modulos.md` como matriz de cobertura y actualizarla si cambia un dueño o ruta. Un módulo sin skill exclusiva puede estar cubierto por skills transversales; crear especialización sólo si contiene invariantes propias que cambian decisiones y no están cubiertas. Diferenciar falta de instrucciones, falta de implementación y falta de evidencia.

Para cada integración registrar productor, consumidor, propietario del dato, API/evento y versión, permisos/entitlement, tenant/alcance, snapshots, idempotencia, error parcial y compensación. El consumidor no escribe tablas del productor ni importa internals de otro microfrontend. Un fallo de dependencia no se convierte en catálogo vacío ni en permiso concedido.

Aplicar `erclave-accounting` si cambia imputación por Sociedad/División/Centro de costos o hechos que alimentarán el libro; mantener Costing, Accounting, Admin y operación separados. Aplicar migraciones, formularios, ambientes y evidencia según el cambio real.

Ejecutar `npm run validate:agents` y `npm run validate:codex-tooling`; revisar semántica además de presencia. Para un cambio implementado cumplir `erclave-feature`, documentación y verify. Reportar hallazgo con módulo, evidencia, impacto, corrección y pendiente verificable. No marcar módulo como seguro únicamente porque tiene dos fichas.

## Capacidades opcionales y ubicación de pantallas

Separar superficie UI, dueño del dato, disponibilidad técnica, entitlement/activación y permiso/alcance. Mostrar configuración de otro dominio en Administración no permite habilitar sus funciones ni escribir su schema. Revisar `docs/arquitectura/contabilidad_opcional_y_capacidades.md` para organización, catálogo básico de centros, Costos y Accounting.

Clasificar cada dependencia como obligatoria o integración opcional antes de agregarla al grafo. Operación y estructura Admin no dependen de activar Accounting. Un módulo opcional apagado no produce efectos ni impone configuración propia al productor. API y jobs revalidan habilitación, no sólo el menú. Definir conservación, lectura histórica autorizada, fecha de inicio y recuperación al reactivar; no replay automático de todo el pasado. Exigir pruebas con combinaciones parciales de módulos, además de todos activos. Una capacidad básica independiente necesita contrato de autorización explícito; no inventar un bypass de entitlement.

Política confirmada CHG-296: catálogo básico disponible desde Administración sin activar analítica/Accounting; Centro de costos obligatorio sólo en flujos de imputación habilitados. Consultar `docs/arquitectura/matriz_capacidades_organizacionales.md`. `capabilities.available` de sesión expresa disponibilidad, nunca autorización de una acción ni configuración lista. No habilitar capacidades planned por flags, roles o permisos.

## Catálogo básico implementado CHG-297

Consultar `docs/arquitectura/cont_05_catalogo_centros.md`. Sólo costing.cost_center.read/create/update/status usan disponibilidad Admin; nunca reclasificar todos los permisos Costing ni activar Accounting. Costing conserva tablas/auditoría; Admin asigna códigos por endpoint dedicado. Disponibilidad requiere runtime habilitado en ambos servicios, permiso y scope efectivo; revalidar elegibilidad en cada futuro consumidor. No afirmar separación de maestros/documentos ni atomicidad distribuida a partir del catálogo.
