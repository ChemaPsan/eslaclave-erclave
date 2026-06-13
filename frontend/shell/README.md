# Frontend shell

El shell es la capa que carga y coordina microfrontends. Debe manejar:

- layout general;
- sidebar y navegacion;
- tema claro/oscuro;
- idioma;
- sesion;
- permisos globales;
- contenedor donde se monta cada modulo;
- toast y modales globales;
- errores de carga.

No debe contener reglas internas de Produccion, Almacenes, Compras, Ventas, Gastos, Costos, Reportes, Administracion o Contabilidad.

## Estado actual

`frontend/app.js` todavia actua como shell y modulo. En la migracion progresiva debe reducirse hasta quedar solo como orquestador.

## Regla

Si un cambio solo afecta un modulo, no debe tocar el shell salvo que cambie el contrato de carga, navegacion o permisos.
