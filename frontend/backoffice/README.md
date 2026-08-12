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
  authMode: "firebase-emulator",
  localApiBaseUrl: "http://127.0.0.1:8000",
  firebaseAuthEmulatorUrl: "http://127.0.0.1:9099",
  localFirebaseConfig: {
    apiKey: "demo-api-key",
    authDomain: "demo-erclave.localhost",
    projectId: "demo-erclave",
    appId: "demo-erclave-web"
  }
};
```

El frontend local se conecta exclusivamente a Firebase Auth Emulator. La configuracion `firebaseConfig` del proyecto QA solo se usa fuera de `localhost` y `127.0.0.1`.

En backend, cuando `ERCLAVE_AUTH_MODE=firebase`, el correo autenticado debe estar en:

```text
ERCLAVE_BACKOFFICE_ADMIN_EMAILS=admin.qa@erclave.local
```

Para que Firebase envie el correo de activacion/restablecimiento al owner inicial:

```text
ERCLAVE_FIREBASE_WEB_API_KEY=<firebase-web-api-key>
```

Si esa key no existe, el endpoint devuelve `data.invitation.reset_link`.
