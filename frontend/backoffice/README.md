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
GET /v1/backoffice/modules
GET /v1/backoffice/tenants
PATCH /v1/backoffice/tenants/{tenant_id}
PATCH /v1/backoffice/tenants/{tenant_id}/status
PUT /v1/backoffice/tenants/{tenant_id}/entitlements/{module_code}
```

Backoffice es la unica interfaz que concede, suspende o retira entitlements. El administrador del tenant solo modifica su preferencia de encendido sobre modulos concedidos. El editor muestra modulos planeados, pero no permite habilitarlos hasta que su runtime sea `implemented`.

El catalogo devuelve dependencias por modulo. Ventas requiere RH y Produccion efectivos: el editor bloquea combinaciones invalidas y el backend vuelve a validarlas transaccionalmente. En onboarding, seleccionar Ventas agrega esas dependencias antes de crear el tenant; los permisos del owner se asignan despues de persistir todos los entitlements activos.

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
