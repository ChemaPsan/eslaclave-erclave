import { manifest as produccion } from "./produccion/manifest.js";
import { manifest as almacenes } from "./almacenes/manifest.js";
import { manifest as compras } from "./compras/manifest.js";
import { manifest as ventas } from "./ventas/manifest.js";
import { manifest as gastos } from "./gastos/manifest.js";
import { manifest as costos } from "./costos/manifest.js";
import { manifest as reportes } from "./reportes/manifest.js";
import { manifest as administracion } from "./administracion/manifest.js";
import { manifest as contabilidad } from "./contabilidad/manifest.js";
import { manifest as recursosHumanos } from "./recursos-humanos/manifest.js";

export const microfrontendRegistry = [
  produccion,
  almacenes,
  compras,
  ventas,
  gastos,
  costos,
  reportes,
  administracion,
  recursosHumanos,
  contabilidad
];
