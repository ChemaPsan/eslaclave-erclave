# Verificacion Local integral

## Objetivo

Certificar los flujos actuales sin consumir QA o Produccion. La verificacion usa exclusivamente PostgreSQL `127.0.0.1:5434/erclave_local`, Firebase Auth Emulator y las siete APIs Local.

## Preparacion

1. Levantar el stack con `backend/scripts/start_local.ps1`.
2. Confirmar que el tenant efectivo es `ten_739ee59d765d5e14818674800d`.
3. No iniciar Cloud SQL Proxy ni sobrescribir `ERCLAVE_TEST_DATABASE_URL` con una URL remota.

## Comandos

```powershell
npm.cmd run verify:postgres
npm.cmd run test:e2e:local
npm.cmd run verify:local
```

`verify:postgres` toma la URL explicita o la configuracion Inventory de `backend/.env`, valida host, puerto y base, compila el backend y ejecuta pytest en modo sin omisiones. Los fixtures concurrentes liberan sus conexiones y limpian sus registros de prueba.

`test:e2e:local` realiza un preflight de frontend, Firebase Emulator y las siete APIs. El navegador reemplaza solamente el SDK remoto de Firebase por un adaptador de prueba que obtiene un token real del emulador; las APIs y PostgreSQL siguen siendo las implementaciones Local reales. El recorrido falla si detecta consumo de un host remoto.

## Cobertura minima

- inicio y cierre de la compuerta de autenticacion;
- resolucion de usuario, tenant, sucursal, modulos y permisos;
- portadas de Produccion, Almacenes, RH, Ventas, Compras y Mantenimiento;
- navegacion de todos los submodulos activos sin error de carga;
- 28 tarjetas de reportes y sus filtros basicos;
- paginacion accesible sin perdida de registros;
- idempotencia, aislamiento, concurrencia y recuperacion de repositorios PostgreSQL.

Los datos funcionales no se promueven y el comando no despliega, migra ni publica artefactos.
