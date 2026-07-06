# ERClave Backoffice

Front interno para administradores de EsLaClave. No pertenece al tenant del cliente.

## Uso

Servir la carpeta `frontend` y abrir:

```text
http://localhost:4173/backoffice/
```

El backoffice usa Firebase Auth y llama:

```text
POST /v1/provisioning/tenant-onboarding
```

## Configuracion local

`frontend/backoffice/env.js` define:

```js
window.ERCLAVE_CONFIG = {
  apiMode: "api",
  authMode: "firebase-local",
  apiBaseUrl: "http://127.0.0.1:8010",
  firebaseConfig: {
    apiKey: "...",
    authDomain: "erclave.firebaseapp.com",
    projectId: "erclave",
    storageBucket: "erclave.firebasestorage.app",
    messagingSenderId: "...",
    appId: "..."
  }
};
```

En backend, cuando `ERCLAVE_AUTH_MODE=firebase`, el correo autenticado debe estar en:

```text
ERCLAVE_BACKOFFICE_ADMIN_EMAILS=admin@eslaclave.com,soporte@eslaclave.com
```

Para que Firebase envie el correo de activacion/restablecimiento al owner inicial:

```text
ERCLAVE_FIREBASE_WEB_API_KEY=<firebase-web-api-key>
```

Si esa key no existe, el endpoint devuelve `data.invitation.reset_link`.
