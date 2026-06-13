# Microfrontends ERClave

Cada modulo debe vivir como microfrontend independiente.

## Contrato minimo

Cada microfrontend debe exponer:

```js
export const manifest = {
  id: "modulo",
  title: "Modulo",
  icon: "XX",
  permissions: ["modulo:read"],
  routes: ["/modulo"]
};

export function mount(container, context) {}
export function unmount() {}
```

## Contexto permitido

El shell puede entregar:

- `apiClient`;
- `eventBus`;
- `i18n`;
- `theme`;
- `permissions`;
- `navigate`;
- `toast`;
- `modal`.

El microfrontend no debe acceder directamente al estado interno del shell ni a datos de otros modulos.

## Estructura sugerida por modulo

```text
{modulo}/
  manifest.js
  index.js
  api.js
  events.js
  views/
  components/
  styles.css
  README.md
```
