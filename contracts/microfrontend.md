# Contrato de microfrontend

Cada modulo visual debe poder montarse y desmontarse sin afectar a los demas.

## Manifest

```js
export const manifest = {
  id: "produccion",
  title: "Produccion",
  icon: "PR",
  version: "0.1.0",
  implementationStatus: "implemented",
  permissions: ["production.product_service.read"],
  routes: ["/produccion"]
};
```

## API publica

```js
export function mount(container, context) {}
export function unmount() {}
```

## Reglas

- `mount` solo puede renderizar dentro de `container`.
- `unmount` debe limpiar listeners, timers, suscripciones y estado temporal.
- El modulo no debe consultar elementos globales del DOM salvo los entregados por `context`.
- El modulo no debe cambiar tema, idioma o rutas sin usar `context`.
- El modulo no debe importar codigo interno de otro microfrontend.
- En un manifiesto `implemented`, `permissions` es el inventario exhaustivo de permisos del namespace propietario que aparecen en operaciones OpenAPI implementadas cuyo `x-required-module` corresponde al modulo. No es solo una lista de permisos de entrada o lectura.
- El inventario no incluye permisos de otros namespaces consumidos por integraciones ni operaciones marcadas `x-implementation-status: planned`.
- Los permisos usan exclusivamente los codigos puntuales con puntos publicados por backend; no se admiten alias historicos con `:`.
- Un manifiesto `planned` conserva `permissions: []` hasta que exista runtime implementado.
- `implementationStatus: "planned"` identifica manifiestos estructurales sin runtime completo y evita presentarlos como modulos reales.

`validate-architecture` compara semanticamente cada manifiesto implementado con su OpenAPI propietario y falla ante permisos faltantes o sobrantes.
