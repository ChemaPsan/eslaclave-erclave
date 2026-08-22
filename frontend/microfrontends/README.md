# Microfrontends ERClave

Cada modulo debe vivir como microfrontend independiente.

## Contrato minimo

Cada microfrontend debe exponer:

```js
export const manifest = {
  id: "modulo",
  title: "Modulo",
  icon: "XX",
  implementationStatus: "implemented",
  permissions: ["module.resource.read"],
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
- `implementationStatus`, con valor `implemented` o `planned`;
- `navigate`;
- `toast`;
- `modal`.

El microfrontend no debe acceder directamente al estado interno del shell ni a datos de otros modulos.

Los manifiestos describen la frontera objetivo. Mientras el shell siga concentrado en `frontend/app.js`, solo los modulos con API real se marcan `implemented`; una carpeta o contrato por si solos no convierten un modulo en funcional.

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
