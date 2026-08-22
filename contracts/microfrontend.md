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
- Los permisos usan exclusivamente los codigos puntuales con puntos publicados por backend; no se admiten alias historicos con `:`.
- `implementationStatus: "planned"` identifica manifiestos estructurales sin runtime completo y evita presentarlos como modulos reales.
