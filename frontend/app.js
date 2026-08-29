import { modules, erpSubmoduleCatalog } from "./data/modules.js";
import { defaultRecipes } from "./data/resources.js";
import { mockDb } from "./data/mockDb.js";
import { translations } from "./i18n/translations.js";
import { getApiErrorTone, getLocalizedErrorMessage } from "./i18n/api-errors.js";
import {
  createTenantBranch,
  createTenantLegalEntity,
  createTenantRole,
  deleteTenantUser,
  disableTenantUser,
  getAdminDashboard,
  getSessionTenants,
  getSessionContext,
  inviteTenantUser,
  replaceTenantRolePermissions,
  setTenantBranchStatus,
  setTenantLegalEntityStatus,
  updateTenantEntitlement,
  updateTenantBranch,
  updateTenantLegalEntity,
  updateTenantRole,
  updateTenantSetting
  ,getUnitsOfMeasure, createUnitOfMeasure, updateUnitOfMeasure,
  createCommercialCatalogItem, updateCommercialCatalogItem, updateDocumentTemplate,
  allocateBusinessCode, updateCodeSequence
} from "./api/admin.js";
import {
  approveProductionRecipeVersion,
  createProductionRecipe,
  createProductionRecipeVersion,
  getProductionCatalog,
  submitProductionRecipeVersion,
  updateProductionRecipeVersion
  ,createProductionProductService, updateProductionProductService, updateProductionProductServiceStatus,
  createProductionMachine, updateProductionMachine, validateProductionResources,
  createProductionOrder, updateProductionOrderStatus, updateProductionOrderResource, updateProductionOrderStage, getProductionProducts, getFinishedGoodsCandidates, getUnlinkedProductionProducts, createAndLinkFinishedGood
} from "./api/production.js";
import { createFinishedGoodsReceipt, createInventoryItem, createInventoryMovement, createInventoryWarehouse, getFinishedGoodsReceipts, getInventoryBalances, getInventoryCatalog, getInventoryItems, getInventoryMovements, updateInventoryItem, updateInventoryWarehouse } from "./api/inventory.js";
import { createHrArea, createHrPosition, getHrAreas, getHrCatalog, updateHrArea, updateHrPosition, getHrWorkers, getProductionEligibleWorkers, getSalesEligibleWorkers, getMaintenanceEligibleWorkers, createHrWorker, updateHrWorker } from "./api/hr.js";
import { approveSalesQuote, cancelSalesQuote, createSalesCustomer, createSalesQuote, expireSalesQuote, getSalesWorkspace, submitSalesQuote, updateSalesCustomer, updateSalesQuote, createSalesOrder, configureSalesOrderFulfillment, cancelSalesOrder, createSalesDelivery, confirmSalesDelivery, cancelSalesDelivery } from "./api/sales.js";
import { cancelPurchasingOrder, cancelPurchasingRequisition, createPurchasingOrder, createPurchasingReceipt, createPurchasingRequisition, createPurchasingSupplier, getPurchasingWorkspace, issuePurchasingOrder, reconcilePurchasingReceipt, transitionPurchasingRequisition, updatePurchasingOrder, updatePurchasingRequisition, updatePurchasingSupplier } from "./api/purchasing.js";
import { cancelMaintenanceMaterialRequest, createMaintenanceMaterialRequest, createMaintenanceOrder, createMaintenanceTime, getMaintenanceOrders, reconcileMaintenanceMaterialRequest, reconcileMaintenanceOrder, transitionMaintenanceOrder, updateMaintenanceOrder } from "./api/maintenance.js";
import { getApiBaseUrl, getApiMode, setApiMode, getDemoActorId, getDemoTenantId, setActiveTenantId, isInventoryApiEnabled } from "./api/config.js";
import { isFirebaseAuthConfigured, onAuthChanged, sendPasswordReset, signInWithEmail, signOutUser } from "./auth.js";
import {
  calculateRecipe,
  validateRecipeDefinition,
  getOrderCostSnapshot,
  getOrderProgress,
  getProductionModuleData,
  getRecipeApprovalStatus,
  getRecipeStandardCost,
  getRecipeResourceCatalog,
  setInventoryRecipeResources,
  setLaborRecipeResources,
  setMachineRecipeResources,
  getReleaseReview,
  getResource,
  isRecipeApproved
} from "./utils/production.js";
import { diffDays, formatCurrency, formatNumber, startOfDay } from "./utils/format.js";
import { installMutationFeedback } from "./utils/mutation-feedback.js";

const state = {
  active: modules[0].id,
  activeSubmodule: null,
  history: [],
  theme: localStorage.getItem("erclave-theme") || "light",
  lang: localStorage.getItem("erclave-lang") || "es",
  adminApi: {
    status: "idle",
    data: null,
    error: ""
  },
  sessionApi: {
    status: "idle",
    data: null,
    error: ""
  },
  productionApi: { status: "idle", error: "" },
  inventoryApi: { status: "idle", error: "" },
  permissionEditor: null,
  inventoryMovements: { status: "idle", error: "" },
  finishedGoodsReceipts: { status: "idle", orders: [], summaries: [], products: [], error: "" },
  inventoryItems: { status: "idle", error: "" },
  inventoryBalances: { status: "idle", data: [], page: {}, error: "", queryKey: "", cursor: "", previousCursors: [] },
  hrApi: { status: "idle", error: "", workers: [] },
  salesApi: { status: "idle", error: "", referenceWarnings: [], workers: [], references: { currencies: [], payment_terms: [] } },
  purchasingApi: { status: "idle", error: "", suppliers: [], requisitions: [], orders: [], receipts: [], items: [], warehouses: [] },
  purchasingSupplierEditId: "",
  purchasingRequisitionEditId: "",
  purchasingOrderEditId: "",
  purchasingOrderSourceRequisitionId: "",
  purchasingReceiptSourceOrderId: "",
  maintenanceApi: { status: "idle", error: "", orders: [], workers: [], machines: [], productionOrders: [], items: [], warehouses: [] },
  maintenanceSourceOrderId: "",
  maintenanceMaterialSourceOrderId: "",
  unitCatalog: { status: "idle", data: [], error: "" },
  tenantResolution: {
    status: "idle",
    tenants: [],
    error: ""
  },
  adminPanel: "organization",
  adminBaseCatalog: null,
  adminDocumentLogo: null,
  auth: {
    status: isFirebaseAuthConfigured() ? "loading" : "disabled",
    user: null,
    email: "",
    error: "",
    notice: ""
  }
};

const orderStatusCatalog = ["Liberada", "En espera de recursos", "En produccion", "Pausada", "En validacion", "Terminada", "Cancelada"];
const fallbackUnitCatalog = Object.freeze([
  {code:"H87",name_es:"Pieza",name_en:"Piece",symbol:"pz"},{code:"KGM",name_es:"Kilogramo",name_en:"Kilogram",symbol:"kg"},{code:"GRM",name_es:"Gramo",name_en:"Gram",symbol:"g"},{code:"LTR",name_es:"Litro",name_en:"Litre",symbol:"L"},{code:"MLT",name_es:"Mililitro",name_en:"Millilitre",symbol:"mL"},{code:"MTR",name_es:"Metro",name_en:"Metre",symbol:"m"},{code:"CMT",name_es:"Centímetro",name_en:"Centimetre",symbol:"cm"},{code:"MIN",name_es:"Minuto",name_en:"Minute",symbol:"min"},{code:"HUR",name_es:"Hora",name_en:"Hour",symbol:"h"},{code:"DAY",name_es:"Día",name_en:"Day",symbol:"d"}
]);
function getUnitCatalog(){return state.adminApi.data?.units?.filter((item)=>item.status==="active")||state.unitCatalog.data?.filter((item)=>item.status==="active")||fallbackUnitCatalog;}
function normalizeUnitCode(value){const raw=String(value||"").trim();return ({pieza:"H87",pza:"H87",pz:"H87",unidad:"C62",servicio:"C62",kg:"KGM",g:"GRM",l:"LTR",ml:"MLT",m:"MTR",cm:"CMT",min:"MIN",hora:"HUR",h:"HUR"})[raw.toLowerCase()]||raw.toUpperCase();}
function unitOptions(selected=""){const units=getUnitCatalog();const normalized=normalizeUnitCode(selected);return units.map((item)=>`<option value="${escapeAttribute(item.code)}" ${item.code.toUpperCase()===normalized?"selected":""}>${escapeHtml(state.lang==="en"?item.name_en:item.name_es)} (${escapeHtml(item.symbol)}) · ${escapeHtml(item.code)}</option>`).join("");}
function codeSequenceConfig(documentType){return (state.adminApi.data?.codeSequences||[]).find((item)=>item.document_type===documentType&&item.status==="active")||null;}
function codeRequestKey(documentType){const value=typeof crypto!=="undefined"&&crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;return `web-code-${documentType}-${value}`;}
async function resolveBusinessCode(documentType,manualCode,requestKey){if(getApiMode()!=="api")return String(manualCode||"").trim().toUpperCase();const allocation=await allocateBusinessCode(documentType,String(manualCode||"").trim()||null,requestKey);return allocation.code;}
function unitSelect(name,selected="",attributes="required"){return `<select name="${name}" ${attributes}>${unitOptions(selected||"H87")}</select>`;}
const mvpModuleIds = ["produccion", "almacenes", "recursos-humanos", "ventas", "compras", "mantenimiento"];
const backendModuleByUiModule = {
  administracion: "admin",
  produccion: "production",
  almacenes: "inventory",
  "recursos-humanos": "hr",
  ventas: "sales",
  compras: "purchasing",
  mantenimiento: "maintenance"
};
const uiModuleByBackendModule = Object.fromEntries(Object.entries(backendModuleByUiModule).map(([ui, backend]) => [backend, ui]));
const tenantModuleDependencies = Object.freeze({ sales: ["hr", "production"], purchasing: ["inventory"], maintenance: ["hr", "inventory"] });
const adminPermissionModuleCatalog = Object.freeze({
  admin: { es: "Administracion", en: "Administration", order: 10 },
  production: { es: "Produccion", en: "Production", order: 20 },
  hr: { es: "Recursos Humanos", en: "Human Resources", order: 25 },
  inventory: { es: "Almacenes", en: "Inventory", order: 30 },
  sales: { es: "Ventas", en: "Sales", order: 40 },
  purchasing: { es: "Compras", en: "Purchasing", order: 45 },
  maintenance: { es: "Mantenimiento", en: "Maintenance", order: 47 },
  billing: { es: "Billing", en: "Billing", order: 50 },
  provisioning: { es: "Provisioning", en: "Provisioning", order: 60 },
  integrations: { es: "Integraciones", en: "Integrations", order: 70 }
});

const shell = document.querySelector(".app-shell");
const moduleNav = document.getElementById("moduleNav");
const modulePanel = document.getElementById("modulePanel");
const flowList = document.getElementById("flowList");
const notificationSummary = document.getElementById("notificationSummary");
const statusStrip = document.querySelector(".status-strip");
const backButton = document.getElementById("backButton");
const themeToggle = document.getElementById("themeToggle");
const langToggle = document.getElementById("langToggle");
const adminShortcut = document.getElementById("adminShortcut");
const topbarPrimary = document.querySelector(".topbar .primary-action");
const authButton = document.getElementById("authButton");
const contextUser = document.getElementById("contextUser");
const contextBranch = document.getElementById("contextBranch");
const branchContext = document.getElementById("branchContext");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalContent = document.getElementById("modalContent");
const toast = document.getElementById("toast");
const authGate = document.getElementById("authGate");

function t(key, values = {}) {
  const template = translations[state.lang]?.[key] || translations.es[key] || key;
  return Object.entries(values).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, value), template);
}

function getScreenSnapshot() {
  return {
    active: state.active,
    activeSubmodule: state.activeSubmodule,
    laborArea: localStorage.getItem("erclave-labor-selected-area") || ""
  };
}

function sameScreen(a, b) {
  return a.active === b.active && a.activeSubmodule === b.activeSubmodule && a.laborArea === b.laborArea;
}

function applyScreenSnapshot(screen) {
  state.active = screen.active;
  state.activeSubmodule = screen.activeSubmodule;
  if (screen.laborArea) {
    localStorage.setItem("erclave-labor-selected-area", screen.laborArea);
  } else {
    localStorage.removeItem("erclave-labor-selected-area");
  }
}

function navigateTo(screen) {
  if (!isModuleAccessible(screen.active)) {
    showToast("Modulo no disponible para este tenant.");
    return;
  }
  const current = getScreenSnapshot();
  if (!sameScreen(current, screen)) {
    state.history.push(current);
  }
  applyScreenSnapshot(screen);
  render();
}

function goBack() {
  const previous = state.history.pop();
  if (!previous) return;
  applyScreenSnapshot(previous);
  render();
}

function normalizeSubmodules(module) {
  return module.submodules.map(([name, detail, id]) => {
    const submoduleId = id || slugify(name);
    return {
      id: submoduleId,
      fallbackName: name,
      fallbackDetail: detail,
      ...getSubmoduleCopy(module.id, submoduleId, name, detail)
    };
  });
}

function getSubmoduleCopy(moduleId, id, fallbackName = "", fallbackDetail = "") {
  const catalogItem = erpSubmoduleCatalog[moduleId]?.[id];
  if (!catalogItem) return { name: fallbackName, detail: fallbackDetail };
  return {
    name: state.lang === "en" ? catalogItem.enName : fallbackName,
    detail: state.lang === "en" ? catalogItem.enDetail : fallbackDetail,
    focus: catalogItem.focus?.[state.lang] || catalogItem.focus?.es || []
  };
}

function getNavigationModules() {
  return modules.filter((module) => module.id !== "administracion").sort((a, b) => {
    const aMvpIndex = mvpModuleIds.indexOf(a.id);
    const bMvpIndex = mvpModuleIds.indexOf(b.id);
    const aOrder = aMvpIndex >= 0 ? aMvpIndex : mvpModuleIds.length + modules.findIndex((module) => module.id === a.id);
    const bOrder = bMvpIndex >= 0 ? bMvpIndex : mvpModuleIds.length + modules.findIndex((module) => module.id === b.id);
    return aOrder - bOrder;
  });
}

installMutationFeedback({ getMessage: () => t("operationInProgress") });

function enhanceEntitySelect(select) {
  if(select.dataset.entityEnhanced==="true")return;
  select.dataset.entityEnhanced="true";
  const wrapper=document.createElement("span"); wrapper.className="entity-select-lookup";
  const input=document.createElement("input"); input.type="search"; input.className="entity-select-search";
  input.placeholder=select.dataset.searchPlaceholder||t("entitySelectorPlaceholder");
  input.setAttribute("role","combobox"); input.setAttribute("aria-autocomplete","list"); input.setAttribute("aria-expanded","false");
  const results=document.createElement("span"); results.className="lookup-results entity-select-results"; results.hidden=true;
  const wasRequired=select.required; if(wasRequired){select.required=false;input.required=true;}
  const sync=()=>{const selected=select.selectedOptions?.[0];if(document.activeElement!==input)input.value=selected&&selected.value?selected.textContent.trim():"";input.disabled=select.disabled;input.placeholder=select.dataset.searchPlaceholder||t("entitySelectorPlaceholder");input.setCustomValidity(wasRequired&&!select.value?t("entitySelectorChooseResult"):"");};
  select.syncEntityLookup=sync;
  select.parentNode.insertBefore(wrapper,select); wrapper.append(input,results,select); select.classList.add("entity-source-select");
  const render=(queryValue=input.value)=>{const query=normalizeDocumentSearch(queryValue);const options=[...select.options].filter(option=>!option.disabled&&normalizeDocumentSearch(option.textContent).includes(query)).slice(0,20);results.innerHTML=options.length?options.map(option=>`<button class="lookup-option" type="button" data-entity-value="${escapeAttribute(option.value)}"><strong>${escapeHtml(option.textContent.trim())}</strong></button>`).join(""):`<span class="lookup-empty">${t("entitySelectorEmpty")}</span>`;results.hidden=false;input.setAttribute("aria-expanded","true");};
  input.addEventListener("focus",()=>{input.select();render("");});
  input.addEventListener("input",()=>{const previous=select.value;const query=normalizeDocumentSearch(input.value);const exact=[...select.options].find(option=>option.value&&normalizeDocumentSearch(option.textContent)===query);select.value=exact?.value||"";sync();render();if(select.value!==previous)select.dispatchEvent(new Event("change",{bubbles:true}));});
  input.addEventListener("keydown",event=>{const buttons=[...results.querySelectorAll("button")];if(event.key==="Escape"){results.hidden=true;input.setAttribute("aria-expanded","false");return;}if(event.key==="ArrowDown"&&buttons.length){event.preventDefault();buttons[0].focus();}});
  results.addEventListener("keydown",event=>{const buttons=[...results.querySelectorAll("button")];const index=buttons.indexOf(document.activeElement);if(event.key==="ArrowDown"&&index<buttons.length-1){event.preventDefault();buttons[index+1].focus();}if(event.key==="ArrowUp"){event.preventDefault();if(index>0)buttons[index-1].focus();else input.focus();}if(event.key==="Escape"){results.hidden=true;input.focus();}});
  results.addEventListener("click",event=>{const button=event.target.closest("[data-entity-value]");if(!button)return;select.value=button.dataset.entityValue;input.value=select.selectedOptions[0]?.textContent.trim()||"";results.hidden=true;input.setAttribute("aria-expanded","false");sync();select.dispatchEvent(new Event("change",{bubbles:true}));});
  select.addEventListener("change",sync);
  sync();
}

function enhanceEntitySelectors(root=document) { root.querySelectorAll("select[data-entity-selector]").forEach(enhanceEntitySelect); }

const entitySelectorObserver=new MutationObserver(records=>records.forEach(record=>{const owner=record.target.matches?.("select[data-entity-selector]")?record.target:record.target.closest?.("select[data-entity-selector]");owner?.syncEntityLookup?.();record.addedNodes.forEach(node=>{if(node.nodeType===1){if(node.matches?.("select[data-entity-selector]"))enhanceEntitySelect(node);enhanceEntitySelectors(node);}});}));
entitySelectorObserver.observe(document.body,{childList:true,subtree:true});
enhanceEntitySelectors();

function getAdminPermissionModuleLabel(moduleCode) {
  return adminPermissionModuleCatalog[moduleCode]?.[state.lang] || moduleCode;
}

function groupAdminPermissions(permissions = []) {
  const grouped = permissions.reduce((groups, permission) => {
    const moduleCode = permission.module_code || "admin";
    groups[moduleCode] = groups[moduleCode] || [];
    groups[moduleCode].push(permission);
    return groups;
  }, {});
  return Object.entries(grouped)
    .sort(([left], [right]) => {
      const leftOrder = adminPermissionModuleCatalog[left]?.order ?? 999;
      const rightOrder = adminPermissionModuleCatalog[right]?.order ?? 999;
      return leftOrder - rightOrder || left.localeCompare(right);
    })
    .map(([moduleCode, modulePermissions]) => ({
      moduleCode,
      label: getAdminPermissionModuleLabel(moduleCode),
      permissions: modulePermissions.slice().sort((left, right) => left.code.localeCompare(right.code))
    }));
}

function getSessionContextData() {
  return getApiMode() === "api" ? state.sessionApi.data : null;
}

function hasPermission(permission) {
  if (getApiMode() !== "api") return true;
  return (getSessionContextData()?.permissions || []).includes(permission);
}

function isAuthRequired() {
  return getApiMode() === "api" && isFirebaseAuthConfigured();
}

function hasApiSessionAccess() {
  return !isAuthRequired() || Boolean(state.auth.user);
}

function hasReadyApiSession() {
  return !isAuthRequired() || (state.sessionApi.status === "ready" && Boolean(state.sessionApi.data));
}

function isApiContextLoading() {
  return getApiMode() === "api" && hasApiSessionAccess() && (
    state.tenantResolution.status === "idle" ||
    state.tenantResolution.status === "loading" ||
    state.sessionApi.status === "idle" ||
    state.sessionApi.status === "loading"
  );
}

function shouldUseSeedModuleData() {
  return getApiMode() !== "api";
}

function getActiveUiModuleIds() {
  const session = getSessionContextData();
  if (!session) return getApiMode() === "api" ? [] : mvpModuleIds;
  return (session.active_modules || []).map((moduleCode) => uiModuleByBackendModule[moduleCode]).filter(Boolean);
}

function isModuleAccessible(moduleId) {
  if (moduleId === "administracion") return true;
  return getActiveUiModuleIds().includes(moduleId);
}

function getModuleAccessState(module) {
  if (!mvpModuleIds.includes(module.id)) return { enabled: false, reason: t("comingSoon") };
  if (getApiMode() !== "api") return { enabled: true, reason: "" };
  if (!hasApiSessionAccess()) return { enabled: false, reason: "Inicia sesion" };
  if (state.sessionApi.status === "loading" || state.sessionApi.status === "idle") {
    return { enabled: false, reason: "Cargando contexto" };
  }
  if (state.sessionApi.status === "error") return { enabled: false, reason: "Contexto no disponible" };
  return isModuleAccessible(module.id)
    ? { enabled: true, reason: "" }
    : { enabled: false, reason: "Modulo inactivo o no contratado" };
}

function renderNav() {
  moduleNav.innerHTML = getNavigationModules()
    .map((module) => {
      const label = state.lang === "en" ? module.titleEn : module.title;
      const access = getModuleAccessState(module);
      return `
        <div class="nav-group ${module.id === state.active ? "open" : ""} ${access.enabled ? "" : "coming-soon"}" ${access.enabled ? "" : `data-tooltip="${access.reason}"`}>
          <button class="nav-button ${module.id === state.active && !state.activeSubmodule ? "active" : ""} ${access.enabled ? "" : "disabled-module"}" type="button" data-module-root="${module.id}" title="${access.enabled ? label : access.reason}" aria-disabled="${access.enabled ? "false" : "true"}">
            <span class="nav-icon">${module.icon}</span>
            <span>${label}</span>
            ${getApiMode() === "api" ? "" : `<small class="nav-count">${module.count}</small>`}
          </button>
          ${renderSubnav(module)}
        </div>
      `;
    })
    .join("");

  moduleNav.querySelectorAll("[data-module-root]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!isModuleAccessible(button.dataset.moduleRoot)) return;
      navigateTo({ active: button.dataset.moduleRoot, activeSubmodule: null, laborArea: "" });
    });
  });

  moduleNav.querySelectorAll("[data-submodule-nav]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!isModuleAccessible(button.dataset.module)) return;
      if (button.dataset.module === "produccion" && button.dataset.submoduleNav === "ordenes") {
        localStorage.removeItem("erclave-production-orders-product");
      }
      navigateTo({ active: button.dataset.module, activeSubmodule: button.dataset.submoduleNav, laborArea: "" });
    });
  });
}

function renderSubnav(module) {
  if (!getModuleAccessState(module).enabled) return "";
  const moduleLabel = state.lang === "en" ? module.titleEn : module.title;
  return `
    <div class="submodule-nav" aria-label="${escapeAttribute(t("submodulesOf", { module: moduleLabel }))}">
      ${normalizeSubmodules(module)
        .map((submodule) => `
            <button class="subnav-button ${state.active === module.id && state.activeSubmodule === submodule.id ? "active" : ""}" type="button" data-module="${module.id}" data-submodule-nav="${submodule.id}">
              <span>${submodule.name}</span>
            </button>
          `)
        .join("")}
    </div>
  `;
}

function getModuleField(module, field) {
  const localizedField = `${field}En`;
  return state.lang === "en" && module[localizedField] !== undefined ? module[localizedField] : module[field];
}

function getModuleTable(module) {
  return getModuleField(module, "table") || { columns: [], rows: [] };
}

const standardReportCatalog = {
  produccion: [
    ["Catálogo de productos y servicios", "Product and service catalog", "Código, nombre, tipo, unidad, estatus y responsable", "Code, name, type, unit, status, and owner"],
    ["Reporte de recetas y versiones", "Recipe and version report", "Producto, versión, vigencia, aprobación y rendimiento", "Product, version, validity, approval, and yield"],
    ["Reporte de órdenes de producción", "Production order report", "Folio, producto, estatus, prioridad, responsable y fechas", "Number, product, status, priority, owner, and dates"],
    ["Reporte de entregables por área", "Deliverables by area report", "Área, etapa, responsable, avance y cumplimiento", "Area, stage, owner, progress, and completion"],
    ["Catálogo de maquinaria", "Machinery catalog", "Código, equipo, área, disponibilidad, costo y estatus", "Code, equipment, area, availability, cost, and status"],
  ],
  almacenes: [
    ["Catálogo de almacenes", "Warehouse catalog", "Código, nombre, tipo, ubicación y estatus", "Code, name, type, location, and status"],
    ["Catálogo de artículos", "Item catalog", "SKU, nombre, tipo, categoría, unidad y política", "SKU, name, type, category, unit, and policy"],
    ["Reporte de inventario", "Inventory report", "Artículo, almacén, existencia, reservado, disponible y valuación", "Item, warehouse, on hand, reserved, available, and valuation"],
    ["Reporte de movimientos y Kárdex", "Movements and ledger report", "Periodo, documento, artículo, almacén, movimiento y cantidad", "Period, document, item, warehouse, movement, and quantity"],
    ["Reporte de críticos y reservas", "Critical stock and reservations report", "Faltantes, mínimos, máximos, reservas, vencimiento y origen", "Shortages, minimums, maximums, reservations, expiry, and source"],
  ],
  "recursos-humanos": [
    ["Catálogo de áreas y puestos", "Area and position catalog", "Área, puesto, estatus, costo por hora y uso productivo", "Area, position, status, hourly cost, and production use"],
    ["Reporte de trabajadores", "Worker report", "Número, nombre, puesto, área, estatus y vigencia", "Number, name, position, area, status, and validity"],
    ["Reporte de capacidad productiva", "Production capacity report", "Fecha, trabajador, puesto, capacidad y compromiso", "Date, worker, position, capacity, and commitment"],
    ["Reporte de elegibilidad", "Eligibility report", "Trabajador, puesto, área, estatus y motivo de elegibilidad", "Worker, position, area, status, and eligibility reason"],
  ],
  ventas: [
    ["Catálogo de clientes", "Customer catalog", "Código, nombre, RFC, responsable, moneda y estatus", "Code, name, tax ID, owner, currency, and status"],
    ["Reporte de cotizaciones", "Quote report", "Folio, cliente, producto, vigencia, importe, margen y estatus", "Number, customer, product, validity, amount, margin, and status"],
    ["Reporte de pedidos", "Order report", "Folio, cliente, producto, surtido, fecha prometida y estatus", "Number, customer, product, fulfillment, promised date, and status"],
    ["Reporte de entregas", "Delivery report", "Folio, pedido, cliente, fecha, cantidad y confirmación", "Number, order, customer, date, quantity, and confirmation"],
    ["Reporte de margen comercial", "Commercial margin report", "Cliente, producto, venta, costo, margen estimado y real", "Customer, product, sales, cost, estimated and actual margin"],
  ],
  administracion: [
    ["Reporte de usuarios y membresías", "Users and memberships report", "Usuario, correo, rol, sucursal, estatus y último acceso", "User, email, role, branch, status, and last access"],
    ["Reporte de roles y permisos", "Roles and permissions report", "Rol, módulo, recurso, acción, alcance y estatus", "Role, module, resource, action, scope, and status"],
    ["Reporte de módulos activos", "Active modules report", "Módulo, entitlement, preferencia, dependencia y disponibilidad", "Module, entitlement, preference, dependency, and availability"],
    ["Catálogo de organización", "Organization catalog", "Razón social, sucursal, ubicación, estatus y configuración", "Legal entity, branch, location, status, and configuration"],
    ["Catálogos base", "Base catalogs", "Unidad, moneda, condición de pago, código y estatus", "Unit, currency, payment terms, code, and status"],
  ],
  compras: [
    ["Catálogo de proveedores", "Supplier catalog", "Código, nombre, condición, tiempo de entrega y estatus", "Code, name, terms, lead time, and status"],
    ["Reporte de requisiciones", "Requisition report", "Folio, solicitante, origen, prioridad, fecha y estatus", "Number, requester, source, priority, date, and status"],
    ["Reporte de órdenes de compra", "Purchase order report", "Folio, proveedor, importe, comprador, entrega y estatus", "Number, supplier, amount, buyer, delivery, and status"],
    ["Reporte de recepciones", "Receipt report", "Orden, proveedor, artículo, cantidad, almacén y diferencia", "Order, supplier, item, quantity, warehouse, and variance"],
  ],
  mantenimiento: [
    ["Reporte de ordenes", "Maintenance order report", "Folio, objetivo, prioridad, responsable, estado y antiguedad", "Number, target, priority, assignee, status, and age"],
    ["Reporte de indisponibilidad", "Downtime report", "Maquina o ubicacion, inicio, resolucion y minutos", "Machine or location, start, resolution, and minutes"],
    ["Reporte de refacciones", "Spare-parts report", "Orden, almacen, articulo, solicitado, reservado, consumido y costo", "Order, warehouse, item, requested, reserved, consumed, and cost"],
    ["Reporte de tiempos", "Maintenance labor report", "Tecnico, orden, intervalo, minutos y MTTR", "Technician, order, interval, minutes, and MTTR"],
  ],
  gastos: [
    ["Reporte documental", "Document report", "Folio, XML/PDF, proveedor, fecha, moneda y validación", "Number, XML/PDF, supplier, date, currency, and validation"],
    ["Reporte de gastos", "Expense report", "Tipo, proveedor, centro, periodo, importe y estatus", "Type, supplier, center, period, amount, and status"],
    ["Reporte de cuentas por pagar", "Accounts payable report", "Proveedor, documento, vencimiento, saldo y estatus", "Supplier, document, due date, balance, and status"],
    ["Reporte de pagos", "Payment report", "Proveedor, documento, fecha, importe, referencia y estatus", "Supplier, document, date, amount, reference, and status"],
  ],
  costos: [
    ["Catálogo de centros de costos", "Cost center catalog", "Código, nombre, responsable, módulo y estatus", "Code, name, owner, module, and status"],
    ["Reporte de costo estimado", "Estimated cost report", "Producto, receta, orden, material, mano de obra y maquinaria", "Product, recipe, order, material, labor, and machinery"],
    ["Reporte de costo real", "Actual cost report", "Orden, consumos, tiempos, gastos, merma y costo total", "Order, consumption, time, expenses, scrap, and total cost"],
    ["Reporte de variaciones", "Variance report", "Objeto, estándar, estimado, real, diferencia y porcentaje", "Object, standard, estimate, actual, difference, and percentage"],
    ["Reporte de rentabilidad", "Profitability report", "Producto, cliente, periodo, ingreso, costo y margen", "Product, customer, period, revenue, cost, and margin"],
  ],
  contabilidad: [
    ["Catálogo de cuentas", "Chart of accounts", "Cuenta, nivel, naturaleza, agrupador y estatus", "Account, level, nature, grouping, and status"],
    ["Reporte de periodos", "Period report", "Ejercicio, periodo, apertura, cierre y estatus", "Fiscal year, period, opening, closing, and status"],
    ["Reporte de asientos y pólizas", "Entries and journals report", "Folio, fecha, origen, cargos, abonos y estatus", "Number, date, source, debits, credits, and status"],
    ["Reporte de mapeos", "Mapping report", "Módulo, operación, cuenta, impuesto, vigencia y estatus", "Module, operation, account, tax, validity, and status"],
    ["Reporte de anexos", "Attachments report", "Documento, origen, tipo, periodo y asociación contable", "Document, source, type, period, and accounting link"],
  ],
  reportes: [
    ["Análisis especializados (planeado)", "Specialized analytics (planned)", "Cruces entre módulos, tableros, constructor, indicadores y exportaciones", "Cross-module analysis, dashboards, builder, indicators, and exports"],
  ],
};

function getStandardReports(module) {
  const configured = standardReportCatalog[module.id];
  if (configured?.length) return configured;
  return normalizeSubmodules(module).map((submodule) => [
    `Reporte de ${submodule.name}`,
    `${submodule.name} report`,
    "Código, estatus, fecha y dimensiones propias del módulo",
    "Code, status, date, and module-specific dimensions",
  ]);
}

function userFacingError(error, fallback = "") {
  return getLocalizedErrorMessage(error, { lang: state.lang, fallback });
}

function showApiError(error, fallback = "") {
  showToast(userFacingError(error, fallback), getApiErrorTone(error));
}

function renderModuleLoadError(module, error, retryAction) {
  const title = state.lang === "en" ? `${module.titleEn || module.title} could not be loaded` : `No se pudo cargar ${module.title}`;
  const retryLabel = state.lang === "en" ? "Retry" : "Reintentar";
  modulePanel.innerHTML = `<section class="section-card module-load-error" role="alert" aria-live="assertive"><strong>${escapeHtml(title)}</strong><p>${escapeHtml(String(error || ""))}</p><button class="secondary-action" data-action="retry-module-api">${retryLabel}</button></section>`;
  modulePanel.querySelector("[data-action='retry-module-api']")?.addEventListener("click", retryAction);
}

function renderPanel() {
  const module = { ...(modules.find((item) => item.id === state.active) || modules[0]) };
  if (!isModuleAccessible(module.id)) {
    renderUnavailableModulePanel(module);
    return;
  }
  if (module.id === "produccion") {
    if (getApiMode() === "api" && state.sessionApi.status === "ready") {
      if (state.productionApi.status === "idle") loadProductionApiData();
      if (state.productionApi.status === "loading" && !mockDb.loadRecipes().length) {
        renderAdminLoadingPanel(module, "Cargando Produccion");
        return;
      }
      if (state.productionApi.status === "error") {
        renderModuleLoadError(module, state.productionApi.error, () => { state.productionApi.status = "idle"; render(); });
        return;
      }
    }
    const production = getProductionModuleData();
    module.table = { ...module.table, rows: production.rows };
    if (module.tableEn) module.tableEn = { ...module.tableEn, rows: production.rows };
    module.records = production.records;
    module.recordsEn = production.records;
    const activeOrderCount = String(mockDb.loadOrders().filter((order) => order.status === "En produccion").length);
    const shortageCount = String(production.validation.missing.length);
    const validationQty = Number(localStorage.getItem("erclave-validation-qty") || 100);
    module.kpis = [
      ["Ordenes activas", activeOrderCount, "positive"],
      ["Faltantes", shortageCount, production.validation.missing.length ? "warning" : "positive"],
      [`Costo lote ${validationQty}`, formatCurrency(production.validation.totalCost), "positive"]
    ];
    module.kpisEn = [
      ["Active orders", activeOrderCount, "positive"],
      ["Shortages", shortageCount, production.validation.missing.length ? "warning" : "positive"],
      [`Batch cost ${validationQty}`, formatCurrency(production.validation.totalCost), "positive"]
    ];
    if (state.activeSubmodule) {
      renderProductionSubmodulePanel(module);
      return;
    }
  } else if (module.id === "recursos-humanos") {
    if (getApiMode() === "api" && state.sessionApi.status === "ready" && state.hrApi.status === "idle") loadHrApiData();
    if (state.hrApi.status === "loading" && !mockDb.loadLaborAreas().length) { renderAdminLoadingPanel(module, "Cargando Recursos Humanos"); return; }
    if (state.hrApi.status === "error") { renderModuleLoadError(module,state.hrApi.error,()=>{state.hrApi.status="idle";render();});return; }
    const areas = mockDb.loadLaborAreas();
    const roles = mockDb.loadLaborRoles();
    module.kpis = [["Areas", String(areas.length), "positive"], ["Puestos", String(roles.length), "positive"], ["Productivos", String(roles.filter((role) => role.intervenesInProduction === true).length), "positive"]];
    module.kpisEn = [["Areas", String(areas.length), "positive"], ["Positions", String(roles.length), "positive"], ["Production", String(roles.filter((role) => role.intervenesInProduction === true).length), "positive"]];
    if (state.activeSubmodule) { renderProductionSubmodulePanel(module); return; }
  } else if (module.id === "administracion") {
    if (state.activeSubmodule) {
      const panelBySubmodule={tenants:"organization",usuarios:"users",roles:"roles","modulos-activos":"modules"};
      state.adminPanel=panelBySubmodule[state.activeSubmodule]||state.adminPanel;
    }
    renderAdminApiPanel(module);
    return;
  } else if (module.id === "ventas" && getApiMode() === "api" && state.sessionApi.status === "ready") {
    if (state.salesApi.status === "idle") loadSalesApiData();
    if (state.salesApi.status === "loading" && !mockDb.loadModuleRecords("ventas").length) { renderAdminLoadingPanel(module, "Cargando Ventas"); return; }
    if (state.salesApi.status === "error") { renderModuleLoadError(module,state.salesApi.error,()=>{state.salesApi.status="idle";render();});return; }
    if (state.activeSubmodule) { renderGenericSubmodulePanel(module); return; }
    const salesRecords=mockDb.loadModuleRecords("ventas");module.kpis=[["Clientes",String(salesRecords.filter(item=>item.recordType==="customer").length),"positive"],["Cotizaciones",String(salesRecords.filter(item=>item.recordType==="quote").length),"positive"],["Pedidos",String(salesRecords.filter(item=>item.recordType==="salesOrder").length),"positive"]];module.kpisEn=[["Customers",module.kpis[0][1],"positive"],["Quotes",module.kpis[1][1],"positive"],["Orders",module.kpis[2][1],"positive"]];
  } else if (module.id === "compras" && getApiMode() === "api" && state.sessionApi.status === "ready") {
    if (state.purchasingApi.status === "idle") loadPurchasingApiData();
    if (state.purchasingApi.status === "loading" && !state.purchasingApi.suppliers.length) { renderAdminLoadingPanel(module, state.lang === "en" ? "Loading Purchasing" : "Cargando Compras"); return; }
    if (state.purchasingApi.status === "error") { renderModuleLoadError(module,state.purchasingApi.error,()=>{state.purchasingApi.status="idle";render();});return; }
    if (state.activeSubmodule) { renderPurchasingSubmodulePanel(module); return; }
    module.kpis=[["Proveedores",String(state.purchasingApi.suppliers.length),"positive"],["Requisiciones",String(state.purchasingApi.requisitions.length),"positive"],["Ordenes abiertas",String(state.purchasingApi.orders.filter(item=>["issued","partially_received"].includes(item.status)).length),"warning"]];
    module.kpisEn=[["Suppliers",module.kpis[0][1],"positive"],["Requisitions",module.kpis[1][1],"positive"],["Open orders",module.kpis[2][1],"warning"]];
  } else if (module.id === "mantenimiento" && getApiMode() === "api" && state.sessionApi.status === "ready") {
    if (state.maintenanceApi.status === "idle") loadMaintenanceApiData();
    if (state.maintenanceApi.status === "loading" && !state.maintenanceApi.orders.length) { renderAdminLoadingPanel(module, state.lang === "en" ? "Loading Maintenance" : "Cargando Mantenimiento"); return; }
    if (state.maintenanceApi.status === "error") { renderModuleLoadError(module,state.maintenanceApi.error,()=>{state.maintenanceApi.status="idle";render();});return; }
    if (state.activeSubmodule) { renderMaintenanceSubmodulePanel(module); return; }
    const open=state.maintenanceApi.orders.filter(item=>!["closed","cancelled"].includes(item.status));module.kpis=[["Ordenes abiertas",String(open.length),"positive"],["Esperando refacciones",String(open.filter(item=>item.status==="waiting_parts").length),"warning"],["Minutos registrados",String(state.maintenanceApi.orders.reduce((sum,item)=>sum+Number(item.total_minutes||0),0)),"positive"]];module.kpisEn=[["Open orders",module.kpis[0][1],"positive"],["Waiting for parts",module.kpis[1][1],"warning"],["Logged minutes",module.kpis[2][1],"positive"]];
  } else if (module.id === "almacenes" && getApiMode() === "api" && isInventoryApiEnabled() && state.sessionApi.status === "ready") {
    if (state.inventoryApi.status === "idle") loadInventoryApiData();
    if (state.inventoryApi.status === "loading" && !mockDb.loadModuleRecords("almacenes").length) {
      renderAdminLoadingPanel(module, "Cargando Almacenes");
      return;
    }
    if (state.inventoryApi.status === "error") {
      renderModuleLoadError(module, state.inventoryApi.error, () => { state.inventoryApi.status = "idle"; render(); });
      return;
    }
    if (state.activeSubmodule) { renderGenericSubmodulePanel(module); return; }
    const warehouseRecords = mockDb.loadModuleRecords("almacenes").filter((record) => record.recordType === "warehouse");
    const warehouseCount = warehouseRecords.length;
    const activeWarehouseCount = warehouseRecords.filter((record) => record.status === "Activo").length;
    module.primary = "Nuevo almacen";
    module.primaryEn = "New warehouse";
    module.kpis = [["Almacenes", String(warehouseCount), "positive"], ["Reservas", "No disponibles", "warning"], ["Almacenes activos", String(activeWarehouseCount), "positive"]];
    module.kpisEn = [["Warehouses", String(warehouseCount), "positive"], ["Reservations", "Unavailable", "warning"], ["Active warehouses", String(activeWarehouseCount), "positive"]];
  } else if (state.activeSubmodule) {
    renderGenericSubmodulePanel(module);
    return;
  }
  if (module.id !== "produccion") {
    const savedRows = getSavedModuleTableRows(module);
    const savedRecords = getSavedModuleRecordRows(module);
    const seedRows = shouldUseSeedModuleData() ? module.table.rows || [] : [];
    const seedRowsEn = shouldUseSeedModuleData() ? module.tableEn?.rows || [] : [];
    const seedRecords = shouldUseSeedModuleData() ? module.records || [] : [];
    const seedRecordsEn = shouldUseSeedModuleData() ? module.recordsEn || [] : [];
    module.table = { ...module.table, rows: [...savedRows, ...seedRows] };
    if (module.tableEn) module.tableEn = { ...module.tableEn, rows: [...savedRows, ...seedRowsEn] };
    module.records = [...savedRecords, ...seedRecords];
    if (module.recordsEn) module.recordsEn = [...savedRecords, ...seedRecordsEn];
  }
  const label = state.lang === "en" ? module.titleEn : module.title;
  const moduleEyebrow = getModuleField(module, "eyebrow");
  const moduleSummary = getModuleField(module, "summary");
  const moduleKpis = getModuleField(module, "kpis") || [];
  const moduleRecords = getModuleField(module, "records") || [];
  const moduleTable = getModuleTable(module);
  const standardReports = getStandardReports(module);

  modulePanel.innerHTML = `
    <div class="module-summary expanded standard-report-summary">
      <div class="module-hero standard-report-hero">
        <p class="eyebrow module-eyebrow">${moduleEyebrow}</p>
        <h1>${label}</h1>
        <p>${moduleSummary}</p>
      </div>

      <div class="module-kpis">
        ${moduleKpis
          .map(
            ([name, value, tone]) => `
              <article class="mini-kpi ${tone}">
                <span>${name}</span>
                <strong>${value}</strong>
              </article>
            `
          )
          .join("")}
      </div>
    </div>

    <div class="module-section-grid standard-report-layout">
      <section class="section-card wide standard-report-section">
        <div class="section-title">
          <span class="section-icon">▦</span>
          <strong>${t("standardReportCatalog")}</strong>
        </div>
        <p class="report-section-help">${t("standardReportCatalogHelp")}</p>
        <div class="standard-report-grid">
          ${standardReports.map(([nameEs,nameEn,filtersEs,filtersEn])=>`
            <article class="standard-report-card">
              <div class="standard-report-card-head"><span class="chip active">${t("standardReport")}</span><span aria-hidden="true">▤</span></div>
              <h3>${escapeHtml(state.lang==="en"?nameEn:nameEs)}</h3>
              <p><strong>${t("suggestedFilters")}:</strong> ${escapeHtml(state.lang==="en"?filtersEn:filtersEs)}</p>
              <small>${t("readOnlyReport")}</small>
            </article>`).join("")}
        </div>
      </section>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">◎</span>
          <strong>${t("moduleSources")}</strong>
        </div>
        <div class="report-source-list">
          ${module.submodules.map(([name,detail,id])=>{const copy=getSubmoduleCopy(module.id,id||slugify(name),name,detail);return `<article><strong>${escapeHtml(copy.name)}</strong><p>${escapeHtml(copy.detail)}</p></article>`;}).join("")}
        </div>
      </section>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">◇</span>
          <strong>${t("reportScope")}</strong>
        </div>
        <div class="compat-list report-scope-list">
          <article><strong>${t("standardReportsTitle")}</strong><p>${t("standardReportScopeDetail")}</p></article>
          <article><strong>${t("specializedReportsTitle")}</strong><p>${t("specializedReportsDetail")}</p><span class="chip warning">${t("inactiveStatus")}</span></article>
        </div>
      </section>
    </div>

    <div class="module-workbench">
      <section class="section-card table-card">
        <div class="section-title">
          <span class="section-icon">☷</span>
          <strong>${t("standardReportPreview")}</strong>
        </div>
          <div class="data-table" role="table">
            <div class="table-row table-head" role="row">
            ${moduleTable.columns.map((column) => `<span role="columnheader">${column}</span>`).join("")}
          </div>
          ${moduleTable.rows.length ? moduleTable.rows
            .map(
              (row) => `
                <div class="table-row" role="row">
                  ${row.map((cell) => `<span role="cell">${cell}</span>`).join("")}
                </div>
              `
            )
            .join("") : `<div class="report-empty-state">${t("standardReportNoData")}</div>`}
        </div>
      </section>
    </div>

    <div class="records module-records">
      ${moduleRecords
        .map(
          ([code, desc, status]) => `
            <article class="record-row">
              <div class="record-main">
                <strong>${code}</strong>
                <span>${desc}</span>
              </div>
              <span class="chip">${status}</span>
            </article>
          `
        )
        .join("")}
    </div>
  `;

}

function renderStatusStrip() {
  if (!statusStrip) return;
  if (shouldUseSeedModuleData()) {
    statusStrip.innerHTML = `
      <article class="metric-card">
        <span class="metric-label" data-i18n="metricProduction">Produccion activa</span>
        <strong>18</strong>
        <small class="trend positive">+12%</small>
      </article>
      <article class="metric-card">
        <span class="metric-label" data-i18n="metricInventory">Inventario critico</span>
        <strong>7</strong>
        <small class="trend warning">3 faltantes</small>
      </article>
      <article class="metric-card">
        <span class="metric-label" data-i18n="metricMargin">Margen estimado</span>
        <strong>32.4%</strong>
        <small class="trend positive">estable</small>
      </article>
      <article class="metric-card">
        <span class="metric-label" data-i18n="metricAccounting">Pendiente contable</span>
        <strong>11</strong>
        <small class="trend danger">requiere mapeo</small>
      </article>
    `;
    return;
  }
  const orders = mockDb.loadOrders();
  const recipes = mockDb.loadRecipes();
  const activeOrders = orders.filter((order) => !["Terminada", "Cancelada"].includes(order.status)).length;
  const missingResources = recipes.reduce((sum, recipe) => {
    const validation = calculateRecipe(recipe, Number(localStorage.getItem("erclave-validation-qty") || 100));
    return sum + validation.missing.length;
  }, 0);
  statusStrip.innerHTML = `
    <article class="metric-card">
      <span class="metric-label" data-i18n="metricProduction">Produccion activa</span>
      <strong>${activeOrders}</strong>
      <small class="trend ${activeOrders ? "positive" : "neutral"}">${activeOrders ? t("activeOrdersInFlow", { count: activeOrders }) : t("noOrders")}</small>
    </article>
    <article class="metric-card">
      <span class="metric-label" data-i18n="metricInventory">Inventario critico</span>
      <strong>${missingResources}</strong>
      <small class="trend ${missingResources ? "warning" : "neutral"}">${missingResources ? t("requiresAttention") : t("noShortages")}</small>
    </article>
    <article class="metric-card">
      <span class="metric-label" data-i18n="metricMargin">Margen estimado</span>
      <strong>0%</strong>
      <small class="trend neutral">${t("noData")}</small>
    </article>
    <article class="metric-card">
      <span class="metric-label" data-i18n="metricAccounting">Pendiente contable</span>
      <strong>0</strong>
      <small class="trend neutral">${t("noData")}</small>
    </article>
  `;
}

function renderUnavailableModulePanel(module) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${state.lang === "en" ? "Module" : "Modulo"}</p>
        <h2>${label}</h2>
      </div>
      <span class="chip warning">Bloqueado</span>
    </div>
    <div class="validation-card danger">
      <strong>Modulo no disponible</strong>
      <p>Este modulo no esta activo para el tenant actual o el contexto de sesion aun no esta disponible.</p>
      <small>${escapeHtml(state.sessionApi.error || "Admin-service define los módulos activos por empresa.")}</small>
    </div>
    <button class="secondary-action" type="button" data-action="go-admin">Ir a Administracion</button>
  `;
  modulePanel.querySelector("[data-action='go-admin']").addEventListener("click", () => {
    navigateTo({ active: "administracion", activeSubmodule: null, laborArea: "" });
  });
}

function getMockAdminDashboard() {
  const tenant = {
    commercial_name: "Cliente piloto",
    legal_name: "Cliente Piloto S.A. de C.V.",
    slug: "demo-local",
    status: "mock",
    locale: "es-MX",
    timezone: "America/Mexico_City"
  };
  return {
    tenant,
    entitlements: [
      { module_code: "production", status: "active" },
      { module_code: "inventory", status: "active" },
      { module_code: "sales", status: "active" }
    ],
    users: [
      { email: "admin.local@erclave.local", display_name: "Admin local", status: "active", roles: ["owner"] }
    ],
    roles: [{ id: "rol_local_owner", code: "owner", name: "Owner", status: "active", permissions: ["admin.tenant.read"] }],
    permissions: [
      { id: "per_local_tenant_read", code: "admin.tenant.read", module_code: "admin", resource: "tenant", action: "read", status: "active" }
    ],
    organization: mockDb.loadAdminOrganization(tenant),
    policy: { allowed: false, reason: "mock_mode", matched_permissions: [] },
    session: null
  };
}

function getAdminPanelData() {
  const data = getApiMode() === "api" ? state.adminApi.data : getMockAdminDashboard();
  if (!data) return data;
  const entitlements = [...(data.entitlements || [])];
  if (!entitlements.some((item) => item.module_code === "hr")) entitlements.push({ module_code: "hr", status: "inactive", tenant_enabled: false, effective_active: false, limits: {} });
  return {
    ...data,
    entitlements: entitlements
      .map((item) => ({ ...item, tenant_enabled: item.tenant_enabled ?? true, effective_active: item.effective_active ?? (item.status === "active" && item.tenant_enabled !== false) }))
      .sort((a, b) => a.module_code.localeCompare(b.module_code))
  };
}

function loadAdminApiDashboard() {
  if (getApiMode() !== "api" || state.adminApi.status === "loading") return;
  if (!hasApiSessionAccess()) return;
  if (!hasReadyApiSession()) return;
  state.adminApi = { status: "loading", data: state.adminApi.data, error: "" };
  render();
  getAdminDashboard()
    .then((data) => {
      if (state.permissionEditor) rebasePermissionEditor(data);
      state.adminApi = { status: "ready", data, error: "" };
      render();
    })
    .catch((error) => {
      if (state.permissionEditor) state.permissionEditor.status = "editing";
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function loadUnitCatalog() {
  if (getApiMode() !== "api" || state.unitCatalog.status !== "idle" || !hasReadyApiSession() || !hasPermission("admin.unit.read")) return;
  state.unitCatalog = {status:"loading",data:state.unitCatalog.data,error:""};
  getUnitsOfMeasure().then((data)=>{state.unitCatalog={status:"ready",data,error:""};}).catch((error)=>{state.unitCatalog={status:"error",data:[],error:error.message||"Unit catalog unavailable"};});
}

function renderAdminEntitlementCard(item, apiMode, apiStatus, entitlements = []) {
  const isApiReady = apiMode === "api" && apiStatus === "ready";
  const isContracted = item.status === "active";
  const nextEnabled = !item.tenant_enabled;
  const effectiveCodes = new Set(entitlements.filter((entry) => entry.effective_active).map((entry) => entry.module_code));
  const missingDependencies = (tenantModuleDependencies[item.module_code] || []).filter((code) => !effectiveCodes.has(code));
  const activeDependents = entitlements.filter((entry) => entry.effective_active && (tenantModuleDependencies[entry.module_code] || []).includes(item.module_code)).map((entry) => entry.module_code);
  const blockedByDependency = nextEnabled ? missingDependencies.length > 0 : activeDependents.length > 0;
  const canToggle = isApiReady && isContracted && item.module_code !== "admin" && !blockedByDependency;
  const dependencyMessage = missingDependencies.length
    ? t("moduleRequiresDependencies", { modules: missingDependencies.join(", ") })
    : activeDependents.length ? t("moduleRequiredByDependents", { modules: activeDependents.join(", ") }) : "";
  return `
    <article class="admin-record compact-admin-record">
      <div class="admin-record-main">
        <strong>${item.module_code}</strong>
        <span>${isContracted ? t("contractedModule") : t("moduleNotContracted")}</span>
        ${dependencyMessage ? `<small>${escapeHtml(dependencyMessage)}</small>` : ""}
      </div>
      <div class="admin-actions">
        <span class="admin-status ${item.effective_active ? "active" : "inactive"}">${item.effective_active ? t("tenantModuleOn") : t("tenantModuleOff")}</span>
        <button class="secondary-action small-action" type="button" data-action="admin-update-entitlement" data-module-code="${item.module_code}" data-next-enabled="${String(nextEnabled)}" title="${escapeAttribute(dependencyMessage)}" ${canToggle ? "" : "disabled"}>
          ${item.tenant_enabled ? t("deactivate") : t("activate")}
        </button>
      </div>
    </article>
  `;
}

function updateAdminEntitlement(moduleCode, enabled) {
  if (getApiMode() !== "api" || state.adminApi.status === "loading") return;
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  updateTenantEntitlement(moduleCode, { enabled })
    .then(() => {
      showToast(t("modulePreferenceUpdated", { module: moduleCode }));
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      state.sessionApi = { status: "idle", data: state.sessionApi.data, error: "" };
      loadSessionContext();
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function getDefaultRoleId(roles) {
  return roles.find((role) => role.code === "owner")?.id || roles[0]?.id || "";
}

function getAdminUserRoleIds(user, roles) {
  const roleCodes = new Set(user.roles || []);
  return roles.filter((role) => roleCodes.has(role.code)).map((role) => role.id);
}

function renderAdminUserCard(user, data, apiMode, apiStatus) {
  const actorId = getDemoActorId();
  const isApiReady = apiMode === "api" && apiStatus === "ready";
  const isCurrentActor = user.id === actorId;
  const canInvite = isApiReady && !isCurrentActor && user.status !== "active";
  const canDisable = isApiReady && !isCurrentActor && user.status === "active";
  const canDelete = isApiReady && !isCurrentActor;
  const roleIds = getAdminUserRoleIds(user, data.roles).join(",");
  return `
    <article class="admin-record">
      <div class="admin-record-main">
        <strong>${user.display_name}</strong>
        <span>${user.email}</span>
      </div>
      <div class="admin-meta-line">
        <span class="admin-status ${user.status}">${user.status}</span>
        <span>${user.roles.join(", ") || "sin rol"}</span>
      </div>
      <div class="admin-actions">
        <button class="secondary-action small-action" type="button" data-action="admin-reinvite-user" data-user-id="${user.id}" data-role-ids="${roleIds}" ${canInvite ? "" : "disabled"}>
          Activar / invitar
        </button>
        <button class="secondary-action small-action" type="button" data-action="admin-disable-user" data-user-id="${user.id}" ${canDisable ? "" : "disabled"}>
          Inactivar
        </button>
        <button class="secondary-action danger-action small-action" type="button" data-action="admin-delete-user" data-user-id="${user.id}" ${canDelete ? "" : "disabled"}>
          Eliminar
        </button>
      </div>
    </article>
  `;
}

function renderAdminInviteForm(data, apiMode, apiStatus) {
  const isApiReady = apiMode === "api" && apiStatus === "ready";
  const defaultRoleId = getDefaultRoleId(data.roles);
  return `
    <form class="admin-form admin-user-form" data-form="admin-invite-user">
      <label>
        <span>Nombre</span>
        <input name="display_name" type="text" placeholder="Nueva persona QA" ${isApiReady ? "" : "disabled"} required />
      </label>
      <label>
        <span>Email</span>
        <input name="email" type="email" placeholder="usuario.qa@erclave.local" ${isApiReady ? "" : "disabled"} required />
      </label>
      <label>
        <span>Rol</span>
        <select name="role_id" data-entity-selector ${isApiReady ? "" : "disabled"}>
          ${data.roles.map((role) => `<option value="${role.id}" ${selectedOption(role.id, defaultRoleId)}>${role.name}</option>`).join("")}
        </select>
      </label>
      <button class="primary-action small-action" type="submit" ${isApiReady ? "" : "disabled"}>Invitar</button>
    </form>
  `;
}

function inviteAdminUser(form) {
  if (getApiMode() !== "api" || state.adminApi.status === "loading") return;
  const formData = new FormData(form);
  const roleId = String(formData.get("role_id") || "");
  const email = String(formData.get("email") || "").trim();
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  inviteTenantUser({
    display_name: String(formData.get("display_name") || "").trim(),
    email,
    role_ids: roleId ? [roleId] : []
  })
    .then((user) => {
      sendPasswordReset(user.email).catch(() => null);
      showToast(`Usuario ${user.email} invitado. Enviamos correo de activacion.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function reinviteAdminUser(userId) {
  if (getApiMode() !== "api" || state.adminApi.status === "loading") return;
  const data = getAdminPanelData();
  const user = data.users.find((item) => item.id === userId);
  if (!user) return;
  const roleIds = getAdminUserRoleIds(user, data.roles);
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  inviteTenantUser({
    display_name: user.display_name,
    email: user.email,
    role_ids: roleIds
  })
    .then((updatedUser) => {
      sendPasswordReset(updatedUser.email).catch(() => null);
      showToast(`Invitacion enviada a ${updatedUser.email}.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function disableAdminUser(userId) {
  if (getApiMode() !== "api" || state.adminApi.status === "loading" || userId === getDemoActorId()) return;
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  disableTenantUser(userId)
    .then((user) => {
      showToast(`Usuario ${user.email} desactivado.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function deleteAdminUser(userId) {
  if (getApiMode() !== "api" || state.adminApi.status === "loading" || userId === getDemoActorId()) return;
  const user = getAdminPanelData().users.find((item) => item.id === userId);
  if (!user) return;
  const confirmed = window.confirm(`Eliminar a ${user.email} de ERClave y Firebase? Necesitara una nueva invitacion para volver.`);
  if (!confirmed) return;
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  deleteTenantUser(userId)
    .then((deletedUser) => {
      showToast(`Usuario ${deletedUser.email} eliminado.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function renderAdminRoleForm(apiMode, apiStatus) {
  const isApiReady = apiMode === "api" && apiStatus === "ready";
  return `
    <form class="admin-form admin-role-form" data-form="admin-create-role">
      <label>
        <span>Codigo</span>
        <input name="code" type="text" placeholder="supervisor" ${isApiReady ? "" : "disabled"} required />
      </label>
      <label>
        <span>Nombre</span>
        <input name="name" type="text" placeholder="Supervisor" ${isApiReady ? "" : "disabled"} required />
      </label>
      <label>
        <span>Descripcion</span>
        <input name="description" type="text" placeholder="Operaciones QA" ${isApiReady ? "" : "disabled"} />
      </label>
      <button class="primary-action small-action" type="submit" ${isApiReady ? "" : "disabled"}>Crear</button>
    </form>
  `;
}

function renderAdminRoleCard(role, data, apiMode, apiStatus) {
  const isApiReady = apiMode === "api" && apiStatus === "ready";
  const canManagePermissions = isApiReady && hasPermission("admin.role.permissions.manage");
  const canViewPermissions = isApiReady && hasPermission("admin.role.read");
  const canUpdateRole = isApiReady && hasPermission("admin.role.update");
  const nextStatus = role.status === "active" ? "inactive" : "active";
  return `
    <article class="admin-record admin-role-record">
      <div class="admin-record-main">
        <strong>${role.name}</strong>
        <span>${role.code}</span>
      </div>
      <div class="admin-meta-line">
        <span class="admin-status ${role.status}">${role.status}</span>
        <span>${(role.permissions || []).length} permisos</span>
      </div>
      <div class="admin-actions">
        <button class="${canManagePermissions ? "primary-action" : "secondary-action"} small-action" type="button" data-action="admin-edit-role-permissions" data-role-id="${role.id}" ${canViewPermissions ? "" : "disabled"} title="${canManagePermissions ? t("editRolePermissions") : t("permissionReadOnlyTitle")}">
          ${canManagePermissions ? t("editRolePermissions") : t("viewRolePermissions")}
        </button>
        <button class="secondary-action small-action" type="button" data-action="admin-toggle-role" data-role-id="${role.id}" data-next-status="${nextStatus}" ${canUpdateRole ? "" : "disabled"}>
          ${role.status === "active" ? "Inactivar" : "Activar"}
        </button>
      </div>
    </article>
  `;
}

function getRoleAssignments(role, permissions) {
  if (Array.isArray(role.permission_assignments)) return role.permission_assignments;
  const codes = new Set(role.permissions || []);
  return permissions.filter((permission) => codes.has(permission.code)).map((permission) => ({
    permission_id: permission.id,
    code: permission.code,
    scope: {}
  }));
}

function openPermissionEditor(roleId) {
  if (!hasPermission("admin.role.read")) return;
  const data = getAdminPanelData();
  const role = data.roles.find((item) => item.id === roleId);
  if (!role) return;
  const assignments = getRoleAssignments(role, data.permissions);
  state.permissionEditor = {
    roleId,
    original: new Map(assignments.map((item) => [item.permission_id, { ...item, scope: item.scope || {} }])),
    draft: new Map(assignments.map((item) => [item.permission_id, { ...item, scope: item.scope || {} }])),
    expectedRevision: role.permission_revision ?? 0,
    search: "",
    filter: "all",
    collapsed: new Set(),
    status: "editing",
    error: "",
    conflict: false
  };
  render();
}

function rebasePermissionEditor(data) {
  const editor = state.permissionEditor;
  if (!editor) return;
  const role = data.roles.find((item) => item.id === editor.roleId);
  if (!role) {
    editor.status = "editing";
    editor.error = t("roleNoLongerAvailable");
    return;
  }
  const serverAssignments = getRoleAssignments(role, data.permissions);
  const nextOriginal = new Map(serverAssignments.map((item) => [item.permission_id, { ...item, scope: item.scope || {} }]));
  const nextDraft = new Map(nextOriginal);
  const touchedIds = new Set([...editor.original.keys(), ...editor.draft.keys()]);
  touchedIds.forEach((permissionId) => {
    const wasSelected = editor.original.has(permissionId);
    const isSelected = editor.draft.has(permissionId);
    if (wasSelected === isSelected) return;
    if (isSelected) nextDraft.set(permissionId, editor.draft.get(permissionId));
    else nextDraft.delete(permissionId);
  });
  editor.original = nextOriginal;
  editor.draft = nextDraft;
  editor.expectedRevision = role.permission_revision;
  editor.status = "editing";
  editor.error = "";
  editor.conflict = false;
}

function getPermissionCopy(permission) {
  const name = state.lang === "en" ? permission.display_name_en : permission.display_name_es;
  const description = state.lang === "en" ? permission.description_en : permission.description_es;
  return { name: name || permission.code, description: description || "" };
}

function permissionChanged(editor, permissionId) {
  return editor.original.has(permissionId) !== editor.draft.has(permissionId);
}

function getPermissionEditorDiff(editor) {
  return {
    added: [...editor.draft.keys()].filter((id) => !editor.original.has(id)),
    removed: [...editor.original.keys()].filter((id) => !editor.draft.has(id))
  };
}

function closePermissionEditorForNavigation() {
  const editor = state.permissionEditor;
  if (!editor) return true;
  const diff = getPermissionEditorDiff(editor);
  if ((diff.added.length || diff.removed.length) && !window.confirm(t("discardPermissionPrompt"))) return false;
  state.permissionEditor = null;
  return true;
}

function getVisibleEditorPermissions(editor, permissions) {
  const query = editor.search.trim().toLocaleLowerCase(state.lang === "en" ? "en-US" : "es-MX");
  return permissions.filter((permission) => {
    const assigned = editor.draft.has(permission.id);
    const changed = permissionChanged(editor, permission.id);
    if (editor.filter === "assigned" && !assigned) return false;
    if (editor.filter === "unassigned" && assigned) return false;
    if (editor.filter === "changes" && !changed) return false;
    const copy = getPermissionCopy(permission);
    return !query || [copy.name, copy.description, permission.code, permission.module_code, permission.resource, permission.action]
      .join(" ").toLocaleLowerCase(state.lang === "en" ? "en-US" : "es-MX").includes(query);
  });
}

function isPermissionAssignable(permission) {
  return permission.available === true && permission.assignable_to_tenant_role === true && permission.status === "active";
}

function renderPermissionEditor(data, apiStatus) {
  const editor = state.permissionEditor;
  const role = data.roles.find((item) => item.id === editor?.roleId);
  if (!editor) return "";
  if (!role) return `<section class="permission-editor recovery-state" role="alert"><p>${t("roleNoLongerAvailable")}</p><button class="secondary-action" type="button" data-action="permission-editor-close">${t("backToRoles")}</button></section>`;
  const visible = getVisibleEditorPermissions(editor, data.permissions);
  const groups = groupAdminPermissions(visible);
  const diff = getPermissionEditorDiff(editor);
  const canManagePermissions = hasPermission("admin.role.permissions.manage");
  const busy = editor.status !== "editing" || apiStatus !== "ready" || !canManagePermissions;
  const permissionById = new Map(data.permissions.map((permission) => [permission.id, permission]));
  const visibleAssignedCount = [...editor.draft.keys()].filter((id) => permissionById.has(id)).length;
  const hiddenAssignedCount = editor.draft.size - visibleAssignedCount;
  const diffNames = (ids) => ids.map((id) => getPermissionCopy(permissionById.get(id) || { code: id }).name);
  return `
    <section class="permission-editor" aria-labelledby="permissionEditorTitle">
      <header class="permission-editor-head">
        <div>
          <button class="secondary-action small-action" type="button" data-action="permission-editor-close">${t("backToRoles")}</button>
          <p class="eyebrow">${t("rolePermissions")}</p>
          <h3 id="permissionEditorTitle">${escapeHtml(role.name)}</h3>
          <p>${t("permissionEditorHelp")}</p>
          ${role.system_role ? `<span class="chip warning">${t("systemRole")}</span>` : ""}
        </div>
        <div class="permission-editor-actions">
          <span class="chip active" aria-live="polite">${t("permissionSelectionCount", { selected: visibleAssignedCount, total: data.permissions.length })}</span>
          ${hiddenAssignedCount ? `<span class="chip warning">${t("hiddenAssignments", { count: hiddenAssignedCount })}</span>` : ""}
          <button class="secondary-action" type="button" data-action="permission-editor-discard" ${diff.added.length || diff.removed.length ? "" : "disabled"}>${t("discardChanges")}</button>
          <button class="primary-action" type="button" data-action="permission-editor-save" ${!busy && (diff.added.length || diff.removed.length) ? "" : "disabled"}>${editor.status === "saving" ? t("saving") : t("saveChanges")}</button>
        </div>
      </header>
      ${editor.error ? `<div class="form-errors permission-editor-error" role="alert"><span>${escapeHtml(editor.error)}</span>${editor.conflict ? `<button class="secondary-action small-action" type="button" data-action="permission-editor-reload">${t("reloadAndCompare")}</button>` : ""}</div>` : ""}
      ${canManagePermissions ? "" : `<div class="validation-card warning permission-readonly-notice" role="status"><strong>${t("permissionReadOnlyTitle")}</strong><p>${t("permissionReadOnlyDetail")}</p></div>`}
      <div class="permission-editor-toolbar">
        <label class="search-field"><span aria-hidden="true">S</span><input type="search" data-permission-search value="${escapeAttribute(editor.search)}" placeholder="${t("searchPermissions")}" aria-label="${t("searchPermissions")}" /></label>
        <label class="preview-field"><span>${t("showPermissions")}</span><select data-permission-filter>
          ${[["all", "allPermissions"], ["assigned", "assignedPermissions"], ["unassigned", "unassignedPermissions"], ["changes", "changedPermissions"]].map(([value, key]) => `<option value="${value}" ${editor.filter === value ? "selected" : ""}>${t(key)}</option>`).join("")}
        </select></label>
        <span>${t("permissionResults", { count: visible.length })}</span>
      </div>
      <div class="permission-editor-bulk" aria-label="${t("visibleBulkActions")}">
        <button class="secondary-action small-action" type="button" data-action="permission-select-visible" ${canManagePermissions ? "" : "disabled"}>${t("selectVisible")}</button>
        <button class="secondary-action small-action" type="button" data-action="permission-clear-visible" ${canManagePermissions ? "" : "disabled"}>${t("clearVisible")}</button>
      </div>
      <div class="permission-editor-modules">
        ${groups.map((group) => renderPermissionModule(group, editor)).join("") || `<p class="empty-state">${t("noPermissionMatches")}</p>`}
      </div>
      <aside class="permission-diff" aria-live="polite" aria-label="${t("pendingChanges")}">
        <strong>${t("pendingChanges")}: ${diff.added.length + diff.removed.length}</strong>
        <span>${t("permissionsAdded", { count: diff.added.length })}: ${escapeHtml(diffNames(diff.added).join(", ") || "-")}</span>
        <span>${t("permissionsRemoved", { count: diff.removed.length })}: ${escapeHtml(diffNames(diff.removed).join(", ") || "-")}</span>
      </aside>
    </section>`;
}

function renderPermissionModule(group, editor) {
  const canManagePermissions = hasPermission("admin.role.permissions.manage");
  const collapsed = editor.collapsed.has(group.moduleCode);
  const assignable = group.permissions.filter(isPermissionAssignable);
  const selected = assignable.filter((permission) => editor.draft.has(permission.id)).length;
  const checked = selected === assignable.length && assignable.length > 0;
  const mixed = selected > 0 && selected < assignable.length;
  const panelId = `permission-module-${String(group.moduleCode).replace(/[^a-z0-9_-]/gi, "-")}`;
  const resources = Object.entries(group.permissions.reduce((map, permission) => {
    const key = permission.resource || t("otherPermissions");
    map[key] = map[key] || [];
    map[key].push(permission);
    return map;
  }, {}));
  return `<section class="permission-module" data-permission-module="${group.moduleCode}">
    <header>
      <button class="permission-module-toggle" type="button" data-action="permission-toggle-module" data-module="${group.moduleCode}" aria-expanded="${!collapsed}" aria-controls="${panelId}">
        <strong>${group.label}</strong><span>${group.permissions.length}</span>
      </button>
      <label class="permission-module-check"><input type="checkbox" data-permission-module-check="${group.moduleCode}" ${checked ? "checked" : ""} data-mixed="${mixed}" ${assignable.length && canManagePermissions ? "" : "disabled"} /><span>${t("selectModuleNamed", { module: group.label })}</span></label>
    </header>
    <div class="permission-resource-list" id="${panelId}" ${collapsed ? "hidden" : ""}>
      ${resources.map(([resource, permissions]) => `<section class="permission-resource"><h4>${escapeHtml(resource)}</h4><div class="permission-action-grid">${permissions.map((permission) => renderPermissionChoice(permission, editor)).join("")}</div></section>`).join("")}
    </div>
  </section>`;
}

function renderPermissionChoice(permission, editor) {
  const copy = getPermissionCopy(permission);
  const disabled = !isPermissionAssignable(permission) || !hasPermission("admin.role.permissions.manage");
  return `<label class="permission-choice ${disabled ? "unavailable" : ""}">
    <input type="checkbox" data-permission-id="${permission.id}" ${editor.draft.has(permission.id) ? "checked" : ""} ${disabled ? "disabled" : ""} />
    <span><strong>${escapeHtml(copy.name)}</strong>${copy.description ? `<small>${escapeHtml(copy.description)}</small>` : ""}<small>${escapeHtml([permission.classification, permission.risk_level].filter(Boolean).join(" · "))}</small><code>${escapeHtml(permission.code)}</code></span>
  </label>`;
}

function createAdminRole(form) {
  if (getApiMode() !== "api" || state.adminApi.status === "loading") return;
  const formData = new FormData(form);
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  createTenantRole({
    code: String(formData.get("code") || "").trim(),
    name: String(formData.get("name") || "").trim(),
    description: String(formData.get("description") || "").trim() || null
  })
    .then((role) => {
      showToast(`Rol ${role.code} creado.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function toggleAdminRole(roleId, status) {
  if (getApiMode() !== "api" || state.adminApi.status === "loading") return;
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  updateTenantRole(roleId, { status })
    .then((role) => {
      showToast(`Rol ${role.code} actualizado.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function updatePermissionDraft(permissionIds, selected) {
  const editor = state.permissionEditor;
  if (!editor || !hasPermission("admin.role.permissions.manage")) return;
  const permissions = new Map(getAdminPanelData().permissions.map((permission) => [permission.id, permission]));
  permissionIds.forEach((permissionId) => {
    const permission = permissions.get(permissionId);
    if (!permission || !isPermissionAssignable(permission)) return;
    if (selected) {
      const original = editor.original.get(permissionId);
      editor.draft.set(permissionId, original || { permission_id: permissionId, code: permission.code, scope: {} });
    } else {
      editor.draft.delete(permissionId);
    }
  });
}

function savePermissionEditor() {
  const editor = state.permissionEditor;
  if (!editor || editor.status === "saving" || !hasPermission("admin.role.permissions.manage")) return;
  editor.status = "saving";
  editor.error = "";
  render();
  replaceTenantRolePermissions(editor.roleId, [...editor.draft.values()].map((assignment) => ({
    permission_id: assignment.permission_id,
    scope: assignment.scope || {}
  })), editor.expectedRevision)
    .then((role) => {
      const assignments = getRoleAssignments(role, getAdminPanelData().permissions);
      editor.original = new Map(assignments.map((item) => [item.permission_id, { ...item, scope: item.scope || {} }]));
      editor.draft = new Map(editor.original);
      editor.expectedRevision = role.permission_revision ?? editor.expectedRevision + 1;
      editor.status = "editing";
      editor.conflict = false;
      showToast(t("rolePermissionsSaved", { role: role.name || role.code }));
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      editor.status = "editing";
      editor.conflict = error.status === 409;
      editor.error = editor.conflict ? t("permissionConflict") : (error.message || t("permissionSaveError"));
      render();
    });
}

function bindPermissionEditorActions() {
  const editor = state.permissionEditor;
  if (!editor) return;
  modulePanel.querySelector("[data-permission-search]")?.addEventListener("input", (event) => {
    editor.search = event.target.value;
    render();
    const next = modulePanel.querySelector("[data-permission-search]");
    next?.focus();
    next?.setSelectionRange(next.value.length, next.value.length);
  });
  modulePanel.querySelector("[data-permission-filter]")?.addEventListener("change", (event) => { editor.filter = event.target.value; render(); });
  modulePanel.querySelectorAll("[data-permission-id]").forEach((input) => input.addEventListener("change", () => { updatePermissionDraft([input.dataset.permissionId], input.checked); render(); }));
  modulePanel.querySelectorAll("[data-mixed='true']").forEach((input) => { input.indeterminate = true; input.setAttribute("aria-checked", "mixed"); });
  modulePanel.querySelectorAll("[data-permission-module-check]").forEach((input) => input.addEventListener("change", () => {
    const ids = getVisibleEditorPermissions(editor, getAdminPanelData().permissions).filter((permission) => permission.module_code === input.dataset.permissionModuleCheck).map((permission) => permission.id);
    updatePermissionDraft(ids, input.checked); render();
  }));
  modulePanel.querySelectorAll("[data-action='permission-toggle-module']").forEach((button) => button.addEventListener("click", () => {
    const moduleCode = button.dataset.module;
    editor.collapsed.has(moduleCode) ? editor.collapsed.delete(moduleCode) : editor.collapsed.add(moduleCode);
    render();
  }));
  modulePanel.querySelector("[data-action='permission-select-visible']")?.addEventListener("click", () => { updatePermissionDraft(getVisibleEditorPermissions(editor, getAdminPanelData().permissions).map((item) => item.id), true); render(); });
  modulePanel.querySelector("[data-action='permission-clear-visible']")?.addEventListener("click", () => { updatePermissionDraft(getVisibleEditorPermissions(editor, getAdminPanelData().permissions).map((item) => item.id), false); render(); });
  modulePanel.querySelector("[data-action='permission-editor-discard']")?.addEventListener("click", () => { editor.draft = new Map(editor.original); editor.error = ""; render(); });
  modulePanel.querySelector("[data-action='permission-editor-save']")?.addEventListener("click", savePermissionEditor);
  modulePanel.querySelector("[data-action='permission-editor-reload']")?.addEventListener("click", () => {
    editor.status = "reloading";
    editor.error = "";
    render();
    loadAdminApiDashboard();
  });
  modulePanel.querySelector("[data-action='permission-editor-close']")?.addEventListener("click", () => {
    const diff = getPermissionEditorDiff(editor);
    if ((diff.added.length || diff.removed.length) && !window.confirm(t("discardPermissionPrompt"))) return;
    state.permissionEditor = null; render();
  });
}

function createLocalId(prefix) {
  const suffix = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  return `${prefix}_${String(suffix).replaceAll("-", "").slice(0, 18)}`;
}

function getDefaultAdminOrganization(tenant = {}) {
  return mockDb.getDefaultAdminOrganization(tenant);
}

function normalizeAdminOrganization(data) {
  const base = getDefaultAdminOrganization(data.tenant);
  const organization = data.organization || {};
  return {
    corporate: { ...base.corporate, ...(organization.corporate || {}) },
    legal_entities: Array.isArray(organization.legal_entities) ? organization.legal_entities : [],
    branches: Array.isArray(organization.branches) ? organization.branches : []
  };
}

function getAdminOrganization() {
  return normalizeAdminOrganization(getAdminPanelData() || getMockAdminDashboard());
}

function getBranchOptions() {
  const sessionBranches = getSessionContextData()?.scope?.branches;
  if (Array.isArray(sessionBranches) && sessionBranches.length) {
    return sessionBranches
      .filter((branch) => branch?.id && branch?.name)
      .map((branch) => ({
        id: branch.id,
        name: branch.name,
        code: branch.code || ""
      }));
  }
  if (isApiContextLoading()) {
    return [{ id: "loading", name: "Cargando sucursal", code: "" }];
  }
  const data = getAdminPanelData() || getMockAdminDashboard();
  const organization = normalizeAdminOrganization(data);
  const branches = organization.branches
    .filter((branch) => branch.name)
    .map((branch) => ({
      id: branch.id || slugify(branch.name),
      name: branch.name,
      code: branch.code || ""
    }));
  if (branches.length) return branches;
  return [{ id: "default", name: "Matriz", code: data.tenant?.commercial_name || "" }];
}

function getSelectedBranch(branches) {
  const savedBranchId = localStorage.getItem("erclave-active-branch-id") || "";
  const selected = branches.find((branch) => branch.id === savedBranchId) || branches[0];
  if (selected?.id && selected.id !== savedBranchId && selected.id !== "loading") {
    localStorage.setItem("erclave-active-branch-id", selected.id);
  }
  return selected;
}

function getContextUserLabel() {
  const sessionUser = getSessionContextData()?.user;
  if (state.auth.user?.email) return state.auth.user.displayName || state.auth.user.email;
  if (sessionUser?.display_name) return sessionUser.display_name;
  if (sessionUser?.email) return sessionUser.email;
  return t("localSession");
}

function renderContextBar() {
  if (!contextUser || !contextBranch || !branchContext) return;
  const branches = getBranchOptions();
  const selectedBranch = getSelectedBranch(branches);
  contextUser.textContent = getContextUserLabel();
  if (branches.length > 1) {
    branchContext.classList.add("is-selectable");
    contextBranch.innerHTML = `
      <select id="branchSelector" data-entity-selector aria-label="${t("selectActiveBranch")}">
        ${branches
          .map((branch) => `<option value="${escapeAttribute(branch.id)}" ${selectedOption(branch.id, selectedBranch.id)}>${escapeAttribute(branch.name)}${branch.code ? ` · ${escapeAttribute(branch.code)}` : ""}</option>`)
          .join("")}
      </select>
    `;
    contextBranch.querySelector("#branchSelector")?.addEventListener("change", (event) => {
      localStorage.setItem("erclave-active-branch-id", event.target.value);
      render();
    });
    return;
  }
  branchContext.classList.remove("is-selectable");
  contextBranch.textContent = selectedBranch.code ? `${selectedBranch.name} · ${selectedBranch.code}` : selectedBranch.name;
}

function getOrganizationContact(payload) {
  return {
    contact_name: String(payload.get("contact_name") || "").trim(),
    contact_email: String(payload.get("contact_email") || "").trim(),
    contact_phone: String(payload.get("contact_phone") || "").trim(),
    contact_position: String(payload.get("contact_position") || "").trim()
  };
}

function saveAdminOrganization(organization, message) {
  if (getApiMode() !== "api") {
    mockDb.saveAdminOrganization(organization);
    showToast(message);
    render();
    return;
  }
  if (state.adminApi.status === "loading") return;
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  updateTenantSetting("organization.profile", { module_code: "admin", value: organization })
    .then(() => {
      showToast(message);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function updateAdminCorporate(form) {
  const formData = new FormData(form);
  const organization = getAdminOrganization();
  const corporate = {
    commercial_name: String(formData.get("commercial_name") || "").trim(),
    legal_name: String(formData.get("legal_name") || "").trim(),
    tax_id: String(formData.get("tax_id") || "").trim(),
    phone: String(formData.get("phone") || "").trim(),
    ...getOrganizationContact(formData)
  };
  saveAdminOrganization({ ...organization, corporate }, "Corporativo actualizado.");
}

function createAdminLegalEntity(form) {
  const formData = new FormData(form);
  const organization = getAdminOrganization();
  const legalEntity = {
    legal_name: String(formData.get("legal_name") || "").trim(),
    tax_id: String(formData.get("tax_id") || "").trim(),
    fiscal_regime: String(formData.get("fiscal_regime") || "").trim(),
    cfdi_usage: String(formData.get("cfdi_usage") || "").trim(),
    fiscal_address: String(formData.get("fiscal_address") || "").trim(),
    ...getOrganizationContact(formData)
  };
  if (getApiMode() === "api") {
    if (state.adminApi.status === "loading") return;
    state.adminApi = { ...state.adminApi, status: "loading", error: "" };
    render();
    createTenantLegalEntity(legalEntity)
      .then((created) => {
        showToast(`Razon social ${created.legal_name} registrada.`);
        state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
        loadAdminApiDashboard();
      })
      .catch((error) => {
        state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
        render();
      });
    return;
  }
  saveAdminOrganization(
    { ...organization, legal_entities: [{ ...legalEntity, id: createLocalId("rso"), status: "active" }, ...organization.legal_entities] },
    `Razon social ${legalEntity.legal_name} registrada.`
  );
}

function createAdminBranch(form) {
  const formData = new FormData(form);
  const organization = getAdminOrganization();
  const branch = {
    name: String(formData.get("name") || "").trim(),
    code: String(formData.get("code") || "").trim(),
    legal_entity_id: String(formData.get("legal_entity_id") || "").trim(),
    address: String(formData.get("address") || "").trim(),
    phone: String(formData.get("phone") || "").trim()
  };
  if (getApiMode() === "api") {
    if (state.adminApi.status === "loading") return;
    state.adminApi = { ...state.adminApi, status: "loading", error: "" };
    render();
    createTenantBranch(branch)
      .then((created) => {
        showToast(`Sucursal ${created.name} registrada.`);
        state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
        loadAdminApiDashboard();
      })
      .catch((error) => {
        state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
        render();
      });
    return;
  }
  saveAdminOrganization({ ...organization, branches: [{ ...branch, id: createLocalId("suc"), status: "active" }, ...organization.branches] }, `Sucursal ${branch.name} registrada.`);
}

function setAdminLegalEntityStatus(legalEntityId, status) {
  const organization = getAdminOrganization();
  if (getApiMode() !== "api") {
    saveAdminOrganization(
      {
        ...organization,
        legal_entities: organization.legal_entities.map((item) => item.id === legalEntityId ? { ...item, status } : item)
      },
      `Razon social ${status === "active" ? "activada" : "inactivada"}.`
    );
    return;
  }
  if (state.adminApi.status === "loading") return;
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  setTenantLegalEntityStatus(legalEntityId, status)
    .then(() => {
      showToast(`Razon social ${status === "active" ? "activada" : "inactivada"}.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function setAdminBranchStatus(branchId, status) {
  const organization = getAdminOrganization();
  if (getApiMode() !== "api") {
    saveAdminOrganization(
      {
        ...organization,
        branches: organization.branches.map((item) => item.id === branchId ? { ...item, status } : item)
      },
      `Sucursal ${status === "active" ? "activada" : "inactivada"}.`
    );
    return;
  }
  if (state.adminApi.status === "loading") return;
  state.adminApi = { ...state.adminApi, status: "loading", error: "" };
  render();
  setTenantBranchStatus(branchId, status)
    .then(() => {
      showToast(`Sucursal ${status === "active" ? "activada" : "inactivada"}.`);
      state.adminApi = { status: "idle", data: state.adminApi.data, error: "" };
      loadAdminApiDashboard();
    })
    .catch((error) => {
      state.adminApi = { status: "error", data: state.adminApi.data, error: error.message || "API unavailable" };
      render();
    });
}

function getAdminCards(data) {
  return [
    {
      id: "organization",
      title: "Organizacion",
      detail: "Corporativo, razones sociales, sucursales y datos fiscales.",
      count: "Base",
      tone: "neutral"
    },
    {
      id: "base-config",
      title: "Configuracion base",
      detail: "Catalogos iniciales y modulos necesarios para operar.",
      count: data.entitlements.filter((item) => item.effective_active).length,
      tone: "active"
    },
    {
      id: "document-templates",
      title: state.lang === "en" ? "Document templates" : "Plantillas documentales",
      detail: state.lang === "en" ? "Logo and colors shared by every generated PDF." : "Logo y colores compartidos por todos los PDF generados.",
      count: "PDF",
      tone: "active"
    },
    {
      id: "users",
      title: "Usuarios",
      detail: "Invitaciones, activacion, inactivacion y eliminacion de accesos.",
      count: data.users.length,
      tone: "active"
    },
    {
      id: "roles",
      title: "Roles",
      detail: "Perfiles operativos y paquetes de permisos por tenant.",
      count: data.roles.length,
      tone: "warning"
    },
    {
      id: "permissions",
      title: "Permisos",
      detail: "Catalogo de permisos efectivos consumido por policy.",
      count: data.permissions.length,
      tone: "active"
    }
  ];
}

function renderAdminHubCards(data) {
  return `
    <div class="admin-hub-grid">
      ${getAdminCards(data).map((card) => `
        <button class="admin-hub-card ${state.adminPanel === card.id ? "selected" : ""}" type="button" data-action="admin-open-panel" data-panel-id="${card.id}">
          <span class="chip ${card.tone === "active" ? "active" : card.tone === "warning" ? "warning" : ""}">${card.count}</span>
          <strong>${card.title}</strong>
          <p>${card.detail}</p>
        </button>
      `).join("")}
    </div>
  `;
}

function renderAdminPanelContent(panelId, data, apiMode, apiStatus) {
  if (!panelId) {
    return `
      <section class="admin-empty-panel">
        <strong>Selecciona una configuracion</strong>
        <p>Administracion funciona como bienvenida operativa: primero define usuarios, roles, permisos, organizacion y catalogos base antes de usar el resto de modulos.</p>
      </section>
    `;
  }
  if (panelId === "users") return renderAdminUsersPanel(data, apiMode, apiStatus);
  if (panelId === "roles") return renderAdminRolesPanel(data, apiMode, apiStatus);
  if (panelId === "permissions") return renderAdminPermissionsPanel(data);
  if (panelId === "organization") return renderAdminOrganizationPanel(data, apiMode, apiStatus);
  if (panelId === "base-config") return renderAdminBaseConfigPanel(data, apiMode, apiStatus);
  if (panelId === "document-templates") return renderAdminDocumentTemplatePanel(data, apiMode, apiStatus);
  return "";
}

function renderAdminUsersPanel(data, apiMode, apiStatus) {
  return `
    <section class="admin-section admin-section-users admin-detail-panel">
      <div class="admin-section-head">
        <div>
          <h3>Usuarios</h3>
          <p>Invita usuarios, reenvia activaciones, inactiva acceso o elimina identidad.</p>
        </div>
        <span class="chip active">${data.users.length}</span>
      </div>
      ${renderAdminInviteForm(data, apiMode, apiStatus)}
      <div class="admin-list">
        ${data.users.map((user) => renderAdminUserCard(user, data, apiMode, apiStatus)).join("")}
      </div>
    </section>
  `;
}

function renderAdminRolesPanel(data, apiMode, apiStatus) {
  if (state.permissionEditor) return `<section class="admin-section admin-section-roles admin-detail-panel">${renderPermissionEditor(data, apiStatus)}</section>`;
  return `
    <section class="admin-section admin-section-roles admin-detail-panel">
      <div class="admin-section-head">
        <div>
          <h3>Roles</h3>
          <p>Define responsabilidades y asigna permisos a cada perfil.</p>
        </div>
        <span class="chip active">${data.roles.length}</span>
      </div>
      ${renderAdminRoleForm(apiMode, apiStatus)}
      <div class="admin-list">
        ${data.roles.map((role) => renderAdminRoleCard(role, data, apiMode, apiStatus)).join("")}
      </div>
    </section>
  `;
}

function renderAdminPermissionsPanel(data) {
  const grouped = groupAdminPermissions(data.permissions);
  return `
    <section class="admin-section admin-detail-panel">
      <div class="admin-section-head">
        <div>
          <h3>Permisos</h3>
          <p>Catalogo tecnico de permisos disponibles para roles y policy.</p>
        </div>
        <span class="chip active">${data.permissions.length}</span>
      </div>
      <div class="admin-permission-grid">
        ${grouped.map(({ moduleCode, label, permissions }) => `
          <article class="admin-record admin-permission-module" data-permission-module="${moduleCode}">
            <div class="admin-record-main">
              <strong>${label}</strong>
              <span>${moduleCode}</span>
              <span>${permissions.length} permisos</span>
            </div>
            <div class="admin-pill-list">
              ${permissions.map((permission) => `<span>${permission.code}</span>`).join("")}
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderAdminOrganizationPanel(data, apiMode, apiStatus) {
  const tenant = data.tenant;
  const organization = normalizeAdminOrganization(data);
  const corporate = organization.corporate;
  const isWritable = apiMode !== "api" || apiStatus === "ready";
  return `
    <section class="admin-section admin-detail-panel">
      <div class="admin-section-head">
        <div>
          <h3>Organizacion</h3>
          <p>Datos generales para operacion, facturacion, razones sociales y sucursales.</p>
        </div>
        <span class="chip active">${tenant.status}</span>
      </div>
      <div class="admin-organization-layout">
        <form class="admin-form admin-organization-form" data-form="admin-update-corporate">
          <div class="admin-form-title">
            <strong>Corporativo</strong>
            <span>Editar y actualizar datos base del tenant.</span>
          </div>
          <label>
            <span>Nombre corporativo</span>
            <input name="commercial_name" type="text" value="${escapeAttribute(corporate.commercial_name)}" ${isWritable ? "" : "disabled"} required />
          </label>
          <label>
            <span>Razon social principal</span>
            <input name="legal_name" type="text" value="${escapeAttribute(corporate.legal_name)}" ${isWritable ? "" : "disabled"} />
          </label>
          <label>
            <span>RFC</span>
            <input name="tax_id" type="text" value="${escapeAttribute(corporate.tax_id)}" ${isWritable ? "" : "disabled"} />
          </label>
          <label>
            <span>Telefono corporativo</span>
            <input name="phone" type="tel" value="${escapeAttribute(corporate.phone)}" ${isWritable ? "" : "disabled"} />
          </label>
          ${renderAdminContactFields(corporate, isWritable)}
          <button class="primary-action small-action" type="submit" ${isWritable ? "" : "disabled"}>Actualizar corporativo</button>
        </form>

        <section class="admin-nested-section">
          <div class="admin-section-head">
            <div>
              <h3>Razones sociales</h3>
              <p>Alta de entidades fiscales del corporativo.</p>
            </div>
            <span class="chip active">${organization.legal_entities.length}</span>
          </div>
          <form class="admin-form admin-organization-form" data-form="admin-create-legal-entity">
            <label>
              <span>Razon social</span>
              <input name="legal_name" type="text" placeholder="Empresa Operadora S.A. de C.V." ${isWritable ? "" : "disabled"} required />
            </label>
            <label>
              <span>RFC</span>
              <input name="tax_id" type="text" placeholder="RFC000000XXX" ${isWritable ? "" : "disabled"} />
            </label>
            <label>
              <span>Regimen fiscal</span>
              <input name="fiscal_regime" type="text" placeholder="601 General de Ley Personas Morales" ${isWritable ? "" : "disabled"} />
            </label>
            <label>
              <span>Uso CFDI default</span>
              <input name="cfdi_usage" type="text" placeholder="G03 Gastos en general" ${isWritable ? "" : "disabled"} />
            </label>
            <label class="wide-field">
              <span>Direccion fiscal</span>
              <input name="fiscal_address" type="text" placeholder="Calle, numero, colonia, CP, ciudad" ${isWritable ? "" : "disabled"} />
            </label>
            ${renderAdminContactFields({}, isWritable)}
            <button class="primary-action small-action" type="submit" ${isWritable ? "" : "disabled"}>Dar de alta razon social</button>
          </form>
          <div class="admin-list">
            ${organization.legal_entities.length ? organization.legal_entities.map((item) => renderAdminLegalEntityCard(item, apiMode, apiStatus)).join("") : renderAdminEmptyRecord("Sin razones sociales registradas.")}
          </div>
        </section>

        <section class="admin-nested-section">
          <div class="admin-section-head">
            <div>
              <h3>Sucursales</h3>
              <p>Matriz, centros de trabajo, almacenes o puntos de venta.</p>
            </div>
            <span class="chip active">${organization.branches.length}</span>
          </div>
          <form class="admin-form admin-organization-form" data-form="admin-create-branch">
            <label>
              <span>Nombre sucursal</span>
              <input name="name" type="text" placeholder="Matriz" ${isWritable ? "" : "disabled"} required />
            </label>
            <label>
              <span>Codigo</span>
              <input name="code" type="text" placeholder="MTY-01" ${isWritable ? "" : "disabled"} />
            </label>
            <label>
              <span>Razon social</span>
              <select name="legal_entity_id" data-entity-selector ${isWritable && organization.legal_entities.length ? "" : "disabled"}>
                <option value="">Sin asignar</option>
                ${organization.legal_entities.map((item) => `<option value="${escapeAttribute(item.id)}">${escapeAttribute(item.legal_name)}</option>`).join("")}
              </select>
            </label>
            <label>
              <span>Telefono</span>
              <input name="phone" type="tel" placeholder="+52 55 0000 0000" ${isWritable ? "" : "disabled"} />
            </label>
            <label class="wide-field">
              <span>Direccion</span>
              <input name="address" type="text" placeholder="Direccion operativa" ${isWritable ? "" : "disabled"} />
            </label>
            <button class="primary-action small-action" type="submit" ${isWritable ? "" : "disabled"}>Dar de alta sucursal</button>
          </form>
          <div class="admin-list">
            ${organization.branches.length ? organization.branches.map((item) => renderAdminBranchCard(item, organization.legal_entities, apiMode, apiStatus)).join("") : renderAdminEmptyRecord("Sin sucursales registradas.")}
          </div>
        </section>
      </div>
    </section>
  `;
}

function renderAdminContactFields(source, isWritable) {
  return `
    <label>
      <span>Nombre contacto</span>
      <input name="contact_name" type="text" value="${escapeAttribute(source.contact_name || "")}" placeholder="Nombre y apellido" ${isWritable ? "" : "disabled"} />
    </label>
    <label>
      <span>Email contacto</span>
      <input name="contact_email" type="email" value="${escapeAttribute(source.contact_email || "")}" placeholder="contacto@empresa.com" ${isWritable ? "" : "disabled"} />
    </label>
    <label>
      <span>Telefono contacto</span>
      <input name="contact_phone" type="tel" value="${escapeAttribute(source.contact_phone || "")}" placeholder="+52 55 0000 0000" ${isWritable ? "" : "disabled"} />
    </label>
    <label>
      <span>Cargo o puesto</span>
      <input name="contact_position" type="text" value="${escapeAttribute(source.contact_position || "")}" placeholder="Direccion administrativa" ${isWritable ? "" : "disabled"} />
    </label>
  `;
}

function renderAdminLegalEntityCard(item, apiMode, apiStatus) {
  const status = item.status || "active";
  const nextStatus = status === "active" ? "inactive" : "active";
  const isWritable = apiMode !== "api" || apiStatus === "ready";
  return `
    <article class="admin-record">
      <div class="admin-record-main">
        <strong>${escapeAttribute(item.legal_name)}</strong>
        <span>${escapeAttribute(item.tax_id || "RFC pendiente")}</span>
      </div>
      <div class="admin-actions">
        <span class="admin-status ${status}">${status}</span>
        <button class="secondary-action small-action" type="button" data-action="admin-toggle-legal-entity" data-legal-entity-id="${escapeAttribute(item.id)}" data-next-status="${nextStatus}" ${isWritable ? "" : "disabled"}>
          ${nextStatus === "active" ? "Activar" : "Inactivar"}
        </button>
      </div>
      <p class="admin-meta-line">${escapeAttribute(item.fiscal_regime || "Regimen pendiente")} · ${escapeAttribute(item.cfdi_usage || "Uso CFDI pendiente")}</p>
      <p class="admin-meta-line">Contacto: ${escapeAttribute(item.contact_name || "Pendiente")} ${item.contact_email ? `· ${escapeAttribute(item.contact_email)}` : ""}</p>
    </article>
  `;
}

function renderAdminBranchCard(item, legalEntities, apiMode, apiStatus) {
  const legalEntity = legalEntities.find((entity) => entity.id === item.legal_entity_id);
  const status = item.status || "active";
  const nextStatus = status === "active" ? "inactive" : "active";
  const isWritable = apiMode !== "api" || apiStatus === "ready";
  return `
    <article class="admin-record">
      <div class="admin-record-main">
        <strong>${escapeAttribute(item.name)}</strong>
        <span>${escapeAttribute(item.code || "Sin codigo")}</span>
      </div>
      <div class="admin-actions">
        <span class="admin-status ${status}">${status}</span>
        <button class="secondary-action small-action" type="button" data-action="admin-toggle-branch" data-branch-id="${escapeAttribute(item.id)}" data-next-status="${nextStatus}" ${isWritable ? "" : "disabled"}>
          ${nextStatus === "active" ? "Activar" : "Inactivar"}
        </button>
      </div>
      <p class="admin-meta-line">${escapeAttribute(item.address || "Direccion pendiente")}</p>
      <p class="admin-meta-line">Razon social: ${escapeAttribute(legalEntity?.legal_name || "Sin asignar")} ${item.phone ? `· ${escapeAttribute(item.phone)}` : ""}</p>
    </article>
  `;
}

function renderAdminEmptyRecord(message) {
  return `
    <article class="admin-record">
      <div class="admin-record-main">
        <strong>${message}</strong>
        <span>Usa el formulario superior para crear el primer registro.</span>
      </div>
    </article>
  `;
}

function renderAdminBaseConfigPanel(data, apiMode, apiStatus) {
  const baseCatalogs = ["businessCenters", "operationalAreas", "unitsOfMeasure", "codeSequences", "taxes", "currencies", "paymentConditions", "warehousesLocations", "documentStatuses"];
  const units = data.units || [];
  if (state.adminBaseCatalog === "units-of-measure") {
    return renderAdminUnitsCatalog(units);
  }
  if (state.adminBaseCatalog === "currencies") return renderAdminCommercialCatalog(data, "currencies");
  if (state.adminBaseCatalog === "payment-terms") return renderAdminCommercialCatalog(data, "payment_terms");
  if (state.adminBaseCatalog === "code-sequences") return renderAdminCodeSequencesCatalog(data.codeSequences || []);
  return `
    <section class="admin-section admin-detail-panel">
      <div class="admin-section-head">
        <div>
          <h3>${t("baseConfiguration")}</h3>
          <p>${t("baseConfigurationHelp")}</p>
        </div>
        <span class="chip active">${baseCatalogs.length}</span>
      </div>
      <div class="admin-list admin-module-list">
        ${baseCatalogs.map((catalog) => catalog === "unitsOfMeasure" ? `
          <button class="admin-record compact-admin-record admin-catalog-entry" type="button" data-action="admin-open-base-catalog" data-catalog-id="units-of-measure">
            <div class="admin-record-main">
              <strong>${t(catalog)}</strong>
              <span>${t("baseCatalogOpen")}</span>
            </div>
            <span class="admin-status ${units.length ? "active" : "invited"}">${units.length ? t("activeUnitsCount", {count: units.filter((item)=>item.status==="active").length}) : t("pending")}</span>
          </button>
        ` : catalog === "codeSequences" ? `
          <button class="admin-record compact-admin-record admin-catalog-entry" type="button" data-action="admin-open-base-catalog" data-catalog-id="code-sequences">
            <div class="admin-record-main"><strong>${t("codeSequences")}</strong><span>${t("baseCatalogOpen")}</span></div>
            <span class="admin-status active">${(data.codeSequences || []).length}</span>
          </button>
        ` : catalog === "currencies" || catalog === "paymentConditions" ? `
          <button class="admin-record compact-admin-record admin-catalog-entry" type="button" data-action="admin-open-base-catalog" data-catalog-id="${catalog==="currencies"?"currencies":"payment-terms"}">
            <div class="admin-record-main"><strong>${t(catalog)}</strong><span>${t("baseCatalogOpen")}</span></div>
            <span class="admin-status active">${(data.commercialCatalogs?.[catalog==="currencies"?"currencies":"payment_terms"]||[]).filter(item=>item.status==="active").length}</span>
          </button>
        ` : `
          <article class="admin-record compact-admin-record">
            <div class="admin-record-main"><strong>${t(catalog)}</strong><span>${t("baseCatalog")}</span></div>
            <span class="admin-status invited">${t("pending")}</span>
          </article>
        `).join("")}
      </div>
      <div class="admin-section-head admin-subsection-head">
        <div>
          <h3>${t("modulesAvailableTitle")}</h3>
          <p>${t("modulesAvailableHelp")}</p>
        </div>
        <span class="chip active">${data.entitlements.filter((item) => item.effective_active).length}</span>
      </div>
      <div class="admin-list admin-module-list">
        ${data.entitlements.map((item) => renderAdminEntitlementCard(item, apiMode, apiStatus, data.entitlements)).join("")}
      </div>
    </section>
  `;
}

function renderAdminCodeSequencesCatalog(sequences) {
  const modules = [...new Set(sequences.map((item) => item.module_code))];
  return `<section class="admin-section admin-detail-panel">
    <div class="admin-section-head">
      <div><p class="eyebrow">${t("baseCatalog")}</p><h3>${t("codeSequences")}</h3><p>${t("codeSequencesHelp")}</p></div>
      <div class="admin-actions"><span class="chip active">${sequences.length}</span><button class="secondary-action small-action" type="button" data-action="admin-close-base-catalog">${t("backToCatalogs")}</button></div>
    </div>
    ${modules.map((moduleCode) => `<div class="admin-section-head admin-subsection-head"><div><h4>${escapeHtml(getAdminPermissionModuleLabel(moduleCode))}</h4></div></div><div class="admin-list admin-module-list">${sequences.filter((item) => item.module_code === moduleCode).map((item) => `<form class="admin-record code-sequence-record" data-form="admin-code-sequence" data-sequence-id="${escapeAttribute(item.id)}">
      <div class="admin-record-main"><strong>${escapeHtml(state.lang === "en" ? item.name_en : item.name_es)}</strong><span>${escapeHtml(item.document_type)} · ${item.mode === "managed" ? t("sequenceManaged") : t("sequenceManual")}</span></div>
      <div class="code-sequence-fields">
        <label><span>${t("sequencePrefix")}</span><input name="prefix" maxlength="24" value="${escapeAttribute(item.prefix)}" ${item.mode === "manual" ? "disabled" : "required"}></label>
        <label><span>${t("sequenceNextNumber")}</span><input name="next_number" type="number" min="1" value="${item.next_number}" ${item.mode === "manual" ? "disabled" : "required"}></label>
        <label><span>${t("sequencePadding")}</span><input name="padding" type="number" min="1" max="12" value="${item.padding}" ${item.mode === "manual" ? "disabled" : "required"}></label>
        <label class="checkbox-field"><input name="managed" type="checkbox" ${item.mode === "managed" ? "checked" : ""}><span>${t("sequenceUseManaged")}</span></label>
      </div>
      ${hasPermission("admin.setting.update") ? `<button class="secondary-action small-action" type="submit">${t("saveChanges")}</button>` : ""}
    </form>`).join("")}</div>`).join("")}
  </section>`;
}

function renderAdminUnitsCatalog(units) {
  const categories = [["count","uomCategoryCount"],["mass","uomCategoryMass"],["length","uomCategoryLength"],["area","uomCategoryArea"],["volume","uomCategoryVolume"],["time","uomCategoryTime"],["package","uomCategoryPackage"],["energy","uomCategoryEnergy"],["power","uomCategoryPower"],["electric","uomCategoryElectric"],["temperature","uomCategoryTemperature"],["pressure","uomCategoryPressure"],["ratio","uomCategoryRatio"],["other","uomCategoryOther"]];
  const categoryLabel = (value) => t(categories.find(([code]) => code === value)?.[1] || "uomCategoryOther");
  return `<section class="admin-section admin-detail-panel">
    <div class="admin-section-head">
      <div><p class="eyebrow">${t("baseCatalog")}</p><h3>${t("unitsOfMeasure")}</h3><p>${t("unitsCatalogHelp")}</p></div>
      <div class="admin-actions"><span class="chip active">${units.length}</span><button class="secondary-action small-action" type="button" data-action="admin-close-base-catalog">${t("backToCatalogs")}</button></div>
    </div>
    ${hasPermission("admin.unit.create") ? `<form class="admin-inline-form" data-form="admin-create-unit">
      <input name="code" maxlength="20" placeholder="${t("unitCodePlaceholder")}" required />
      <input name="name_es" maxlength="120" placeholder="${t("unitNameEs")}" required />
      <input name="name_en" maxlength="120" placeholder="${t("unitNameEn")}" required />
      <input name="symbol" maxlength="24" placeholder="${t("unitSymbol")}" required />
      <select name="category">${categories.map(([value,key])=>`<option value="${value}">${t(key)}</option>`).join("")}</select>
      <input name="decimal_places" type="number" min="0" max="6" value="3" aria-label="${t("unitDecimals")}" required />
      <button class="primary-action small-action" type="submit">${t("addUnit")}</button>
    </form>` : ""}
    <div class="admin-list admin-module-list">
      ${units.map((unit)=>`<article class="admin-record compact-admin-record"><div class="admin-record-main"><strong>${escapeHtml(state.lang==="en"?unit.name_en:unit.name_es)} (${escapeHtml(unit.symbol)})</strong><span>${escapeHtml(unit.code)} · ${escapeHtml(categoryLabel(unit.category))} · ${t("unitDecimalsCount", {count: unit.decimal_places})}${unit.system_default?` · ${t("defaultUnit")}`:` · ${t("customUnit")}`}</span></div><div class="admin-actions"><span class="admin-status ${unit.status}">${unit.status==="active"?t("activeStatus"):t("inactiveStatus")}</span>${hasPermission("admin.unit.update")?`<button class="secondary-action small-action" data-action="admin-edit-unit" data-unit-id="${unit.id}">${t("edit")}</button><button class="secondary-action small-action" data-action="admin-toggle-unit" data-unit-id="${unit.id}" data-next-status="${unit.status==="active"?"inactive":"active"}">${unit.status==="active"?t("deactivate"):t("activate")}</button>`:""}</div></article>`).join("") || renderAdminEmptyRecord(t("unitCatalogEmpty"))}
    </div>
  </section>`;
}

function renderAdminCommercialCatalog(data,catalogCode){
  const items=data.commercialCatalogs?.[catalogCode]||[];const label=catalogCode==="currencies"?(state.lang==="en"?"Currencies":"Monedas"):(state.lang==="en"?"Payment terms":"Condiciones de pago");
  return `<section class="admin-section admin-detail-panel"><div class="admin-section-head"><div><p class="eyebrow">${t("baseCatalog")}</p><h3>${label}</h3><p>${state.lang==="en"?"Tenant-authoritative values used by customers, quotes and orders.":"Valores autoritativos del tenant usados por clientes, cotizaciones y pedidos."}</p></div><div class="admin-actions"><span class="chip active">${items.length}</span><button class="secondary-action small-action" type="button" data-action="admin-close-base-catalog">${t("backToCatalogs")}</button></div></div>${hasPermission("admin.catalog.create")?`<form class="admin-inline-form" data-form="admin-create-commercial-item" data-catalog-code="${catalogCode}"><input name="code" maxlength="40" placeholder="${catalogCode==="currencies"?"MXN":"credit_30"}" required><input name="name_es" maxlength="160" placeholder="Nombre en español" required><input name="name_en" maxlength="160" placeholder="Name in English" required><button class="primary-action small-action" type="submit">${state.lang==="en"?"Add":"Agregar"}</button></form>`:""}<div class="admin-list admin-module-list">${items.map(item=>`<article class="admin-record compact-admin-record"><div class="admin-record-main"><strong>${escapeHtml(state.lang==="en"?item.name_en:item.name_es)}</strong><span>${escapeHtml(item.code)}${item.system_default?" · Predeterminado":""}</span></div><div class="admin-actions"><span class="admin-status ${item.status}">${item.status}</span>${hasPermission("admin.catalog.update")?`<button class="secondary-action small-action" data-action="admin-toggle-commercial-item" data-catalog-code="${catalogCode}" data-item-id="${item.id}" data-next-status="${item.status==="active"?"inactive":"active"}">${item.status==="active"?t("deactivate"):t("activate")}</button>`:""}</div></article>`).join("")||renderAdminEmptyRecord(state.lang==="en"?"No values registered.":"Sin valores registrados.")}</div></section>`;
}

function renderAdminDocumentTemplatePanel(data,apiMode,apiStatus){
  const value=data.documentTemplate||{};const logo=state.adminDocumentLogo===null?value.logo_data_url:state.adminDocumentLogo;const writable=(apiMode!=="api"||apiStatus==="ready")&&hasPermission("admin.setting.update");
  return `<section class="admin-section admin-detail-panel"><div class="admin-section-head"><div><h3>${t("documentIdentityTitle")}</h3><p>${t("documentIdentityHelp")}</p></div><span class="chip active">PDF</span></div><form class="admin-form admin-organization-form document-template-form" data-form="admin-document-template"><label class="wide-field"><span>${t("documentLogoLabel")}</span><input name="logo" type="file" accept="image/png,image/jpeg,image/webp" ${writable?"":"disabled"}></label>${logo?`<div class="wide-field document-template-preview"><img src="${escapeAttribute(logo)}" alt="${escapeAttribute(t("documentLogoAlt"))}">${writable?`<button class="secondary-action small-action" type="button" data-action="remove-document-logo">${t("documentLogoRemove")}</button>`:""}</div>`:""}<label><span>${t("documentPrimaryColor")}</span><input name="primary_color" type="color" value="${escapeAttribute(value.primary_color||"#6106A0")}" ${writable?"":"disabled"}></label><label><span>${t("documentAccentColor")}</span><input name="accent_color" type="color" value="${escapeAttribute(value.accent_color||"#F557D3")}" ${writable?"":"disabled"}></label><label><span>${t("documentTextColor")}</span><input name="text_color" type="color" value="${escapeAttribute(value.text_color||"#190F34")}" ${writable?"":"disabled"}></label><label class="wide-field"><span>${t("documentFooter")}</span><input name="footer_text" maxlength="300" value="${escapeAttribute(value.footer_text||"")}" ${writable?"":"disabled"}></label><label class="document-template-checkbox"><input name="show_page_number" type="checkbox" ${value.show_page_number!==false?"checked":""} ${writable?"":"disabled"}><span>${t("documentShowPageNumber")}</span></label>${writable?`<button class="primary-action small-action" type="submit">${t("documentTemplateSave")}</button>`:""}</form></section>`;
}

function renderAdminApiPanel(module) {
  const data = getAdminPanelData();
  const apiMode = getApiMode();
  const apiStatus = apiMode === "api" ? state.adminApi.status : "mock";
  const label = state.lang === "en" ? module.titleEn : module.title;

  if (isApiContextLoading() || (apiMode === "api" && apiStatus === "loading" && !data)) {
    renderAdminLoadingPanel(module, label);
    return;
  }

  if (apiMode === "api" && !hasReadyApiSession()) {
    const isSignedIn = Boolean(state.auth.user);
    const isResolvingTenant = state.tenantResolution.status === "loading";
    modulePanel.innerHTML = `
      <div class="panel-head">
        <div>
          <p class="eyebrow">${module.eyebrow}</p>
          <h2>${label}</h2>
        </div>
        <span class="chip warning">Bloqueado</span>
      </div>
      <div class="validation-card danger">
        <strong>${isResolvingTenant ? "Resolviendo tenant" : "Acceso no autorizado"}</strong>
        <p>${isResolvingTenant ? "Estamos buscando el tenant activo para tu usuario." : isSignedIn ? "Tu correo autentico correctamente, pero no tiene una sesion ERClave activa para este tenant." : "Inicia sesion con una cuenta autorizada para cargar Administracion."}</p>
        <small>${escapeHtml(state.tenantResolution.error || state.sessionApi.error || state.auth.error || getApiBaseUrl())}</small>
      </div>
      <div class="admin-overview-actions">
        <button class="secondary-action" type="button" data-action="admin-refresh-api">Reintentar</button>
      </div>
    `;
    modulePanel.querySelector("[data-action='admin-refresh-api']").addEventListener("click", () => {
      state.sessionApi = { status: "idle", data: null, error: "" };
      state.adminApi = { status: "idle", data: null, error: "" };
      render();
    });
    return;
  }

  const safeData = data || getMockAdminDashboard();
  const tenant = safeData.tenant;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${module.eyebrow}</p>
        <h2>${label}</h2>
      </div>
      <div class="admin-toolbar">
        <span class="chip ${apiMode === "api" && apiStatus !== "error" ? "active" : "warning"}">${apiMode === "api" ? (getApiBaseUrl().includes("127.0.0.1") || getApiBaseUrl().includes("localhost") ? "API Local" : "API QA") : "Mock"}</span>
        <button class="secondary-action small-action" type="button" data-action="admin-refresh-api">Actualizar</button>
        <button class="secondary-action small-action" type="button" data-action="admin-toggle-api">${apiMode === "api" ? "Mock" : "API"}</button>
      </div>
    </div>

    <div class="admin-welcome">
      <div>
        <p class="eyebrow">Bienvenida y configuracion</p>
        <h1>${tenant.commercial_name}</h1>
        <p>Configura la administracion inicial del sistema antes de operar modulos: usuarios, roles, permisos, organizacion y catalogos base.</p>
      </div>
    </div>

    ${state.adminApi.error ? `<div class="validation-card danger" role="alert"><strong>${getApiBaseUrl().includes("127.0.0.1") || getApiBaseUrl().includes("localhost") ? "API Local" : "API QA"}</strong><p>${escapeHtml(state.adminApi.error)}</p><small>${escapeHtml(getApiBaseUrl())}</small></div>` : ""}
    ${state.sessionApi.error ? `<div class="validation-card danger" role="alert"><strong>Session Context</strong><p>${escapeHtml(state.sessionApi.error)}</p><small>${escapeHtml(getApiBaseUrl())}</small></div>` : ""}

    ${renderAdminHubCards(safeData)}

    <div class="admin-workspace">
      ${renderAdminPanelContent(state.adminPanel || "organization", safeData, apiMode, apiStatus)}
    </div>
  `;

  modulePanel.querySelector("[data-action='admin-toggle-api']").addEventListener("click", () => {
    if (!closePermissionEditorForNavigation()) return;
    setApiMode(apiMode === "api" ? "mock" : "api");
    state.adminApi = { status: "idle", data: null, error: "" };
    if (getApiMode() === "api") {
      loadAdminApiDashboard();
    } else {
      render();
    }
  });

  modulePanel.querySelector("[data-action='admin-refresh-api']").addEventListener("click", () => {
    if (getApiMode() !== "api") setApiMode("api");
    loadAdminApiDashboard();
  });

  modulePanel.querySelectorAll("[data-action='admin-open-panel']").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.panelId !== "roles" && !closePermissionEditorForNavigation()) return;
      state.adminPanel = button.dataset.panelId;
      if (state.adminPanel !== "base-config") state.adminBaseCatalog = null;
      render();
    });
  });

  modulePanel.querySelectorAll("[data-action='admin-open-base-catalog']").forEach((button) => {
    button.addEventListener("click", () => {
      state.adminBaseCatalog = button.dataset.catalogId;
      render();
    });
  });

  modulePanel.querySelector("[data-action='admin-close-base-catalog']")?.addEventListener("click", () => {
    state.adminBaseCatalog = null;
    render();
  });

  modulePanel.querySelector("[data-form='admin-update-corporate']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    updateAdminCorporate(event.currentTarget);
  });

  modulePanel.querySelector("[data-form='admin-create-legal-entity']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    createAdminLegalEntity(event.currentTarget);
  });

  modulePanel.querySelector("[data-form='admin-create-branch']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    createAdminBranch(event.currentTarget);
  });

  modulePanel.querySelectorAll("[data-action='admin-toggle-legal-entity']").forEach((button) => {
    button.addEventListener("click", () => {
      setAdminLegalEntityStatus(button.dataset.legalEntityId, button.dataset.nextStatus);
    });
  });

  modulePanel.querySelectorAll("[data-action='admin-toggle-branch']").forEach((button) => {
    button.addEventListener("click", () => {
      setAdminBranchStatus(button.dataset.branchId, button.dataset.nextStatus);
    });
  });

  modulePanel.querySelectorAll("[data-action='admin-update-entitlement']").forEach((button) => {
    button.addEventListener("click", () => {
      updateAdminEntitlement(button.dataset.moduleCode, button.dataset.nextEnabled === "true");
    });
  });

  modulePanel.querySelector("[data-form='admin-create-unit']")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    try {
      await createUnitOfMeasure({...values, decimal_places:Number(values.decimal_places)});
      showToast(t("unitAdded"));
      await loadAdminApiDashboard();
    } catch (error) { showToast(error.message || t("unitAddError")); }
  });
  modulePanel.querySelectorAll("[data-action='admin-toggle-unit']").forEach((button)=>button.addEventListener("click", async()=>{
    try { await updateUnitOfMeasure(button.dataset.unitId,{status:button.dataset.nextStatus}); showToast(t("unitUpdated")); await loadAdminApiDashboard(); }
    catch(error){ showToast(error.message || t("unitUpdateError")); }
  }));
  modulePanel.querySelectorAll("[data-action='admin-edit-unit']").forEach((button)=>button.addEventListener("click",()=>openAdminUnitModal(button.dataset.unitId)));

  modulePanel.querySelector("[data-form='admin-create-commercial-item']")?.addEventListener("submit",async event=>{event.preventDefault();const form=event.currentTarget;try{await createCommercialCatalogItem(form.dataset.catalogCode,Object.fromEntries(new FormData(form)));showToast("Valor de catálogo agregado.");await loadAdminApiDashboard();}catch(error){showToast(error.message||"No se pudo agregar el valor.");}});
  modulePanel.querySelectorAll("[data-action='admin-toggle-commercial-item']").forEach(button=>button.addEventListener("click",async()=>{try{await updateCommercialCatalogItem(button.dataset.catalogCode,button.dataset.itemId,{status:button.dataset.nextStatus});showToast("Catálogo actualizado.");await loadAdminApiDashboard();}catch(error){showToast(error.message||"No se pudo actualizar el catálogo.");}}));
  modulePanel.querySelectorAll("[data-form='admin-code-sequence']").forEach(form => {
    const managed = form.querySelector("[name='managed']");
    const sync = () => form.querySelectorAll("[name='prefix'],[name='next_number'],[name='padding']").forEach((input) => { input.disabled = !managed.checked; });
    managed?.addEventListener("change", sync);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = new FormData(form);
      try {
        await updateCodeSequence(form.dataset.sequenceId, { mode: managed.checked ? "managed" : "manual", ...(managed.checked ? { prefix: String(values.get("prefix") || "").trim(), next_number: Number(values.get("next_number")), padding: Number(values.get("padding")) } : {}) });
        showToast(t("sequenceUpdated"));
        await loadAdminApiDashboard();
      } catch (error) { showToast(error.message || t("sequenceUpdateError")); }
    });
  });
  modulePanel.querySelector("[data-form='admin-document-template'] [name='logo']")?.addEventListener("change",event=>{const file=event.target.files?.[0];if(!file)return;if(!["image/png","image/jpeg","image/webp"].includes(file.type)){showToast(t("documentLogoTypeError"));event.target.value="";return;}if(file.size>1_000_000){showToast(t("documentLogoSizeError"));event.target.value="";return;}const reader=new FileReader();reader.onerror=()=>showToast(t("documentLogoReadError"));reader.onload=()=>{state.adminDocumentLogo=String(reader.result);render();};reader.readAsDataURL(file);});
  modulePanel.querySelector("[data-action='remove-document-logo']")?.addEventListener("click",()=>{state.adminDocumentLogo="";render();});
  modulePanel.querySelector("[data-form='admin-document-template']")?.addEventListener("submit",async event=>{event.preventDefault();const form=event.currentTarget;const values=new FormData(form);try{await updateDocumentTemplate({logo_data_url:state.adminDocumentLogo===null?(safeData.documentTemplate?.logo_data_url||null):state.adminDocumentLogo||null,primary_color:values.get("primary_color"),accent_color:values.get("accent_color"),text_color:values.get("text_color"),footer_text:String(values.get("footer_text")||"").trim()||null,show_page_number:values.get("show_page_number")==="on"});state.adminDocumentLogo=null;showToast(t("documentTemplateUpdated"));await loadAdminApiDashboard();}catch(error){showToast(error.message||t("documentTemplateUpdateError"));}});

  modulePanel.querySelector("[data-form='admin-invite-user']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    inviteAdminUser(event.currentTarget);
  });

  modulePanel.querySelectorAll("[data-action='admin-reinvite-user']").forEach((button) => {
    button.addEventListener("click", () => {
      reinviteAdminUser(button.dataset.userId);
    });
  });

  modulePanel.querySelectorAll("[data-action='admin-disable-user']").forEach((button) => {
    button.addEventListener("click", () => {
      disableAdminUser(button.dataset.userId);
    });
  });

  modulePanel.querySelectorAll("[data-action='admin-delete-user']").forEach((button) => {
    button.addEventListener("click", () => {
      deleteAdminUser(button.dataset.userId);
    });
  });

  modulePanel.querySelector("[data-form='admin-create-role']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    createAdminRole(event.currentTarget);
  });

  modulePanel.querySelectorAll("[data-action='admin-toggle-role']").forEach((button) => {
    button.addEventListener("click", () => {
      toggleAdminRole(button.dataset.roleId, button.dataset.nextStatus);
    });
  });

  modulePanel.querySelectorAll("[data-action='admin-edit-role-permissions']").forEach((button) => {
    button.addEventListener("click", () => openPermissionEditor(button.dataset.roleId));
  });

  bindPermissionEditorActions();

  if (apiMode === "api" && apiStatus === "idle") {
    loadAdminApiDashboard();
  }
}

function renderAdminLoadingPanel(module, label) {
  const tenantMessage = state.tenantResolution.status === "loading"
    ? "Identificando el tenant asignado a tu usuario."
    : state.sessionApi.status === "loading"
      ? "Cargando permisos, sucursales y modulos activos."
      : "Preparando la configuracion inicial del tenant.";

  modulePanel.innerHTML = `
    <div class="tenant-loading-shell" aria-busy="true">
      <div class="tenant-loading-backdrop" aria-hidden="true">
        <div class="tenant-loading-line wide"></div>
        <div class="tenant-loading-line medium"></div>
        <div class="tenant-loading-card-grid">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div class="tenant-loading-panel"></div>
      </div>
      <div class="tenant-loading-card">
        <p class="eyebrow">${module.eyebrow}</p>
        <h2>${label}</h2>
        <strong>Preparando tu espacio de trabajo</strong>
        <p>${tenantMessage}</p>
        <div class="tenant-loading-progress" aria-hidden="true">
          <span></span>
        </div>
      </div>
    </div>
  `;
}

function loadSessionContext() {
  if (getApiMode() !== "api" || state.sessionApi.status === "loading") return;
  if (!hasApiSessionAccess()) return;
  if (isAuthRequired() && state.tenantResolution.status !== "ready") {
    resolveSessionTenant();
    return;
  }
  state.sessionApi = { status: "loading", data: state.sessionApi.data, error: "" };
  getSessionContext()
    .then((data) => {
      state.sessionApi = { status: "ready", data, error: "" };
      state.productionApi = { status: "idle", error: "" };
      state.inventoryApi = { status: "idle", error: "" };
      state.finishedGoodsReceipts = { status: "idle", orders: [], summaries: [], products: [], error: "" };
      state.salesApi = { status: "idle", error: "", workers: [], references: { currencies: [], payment_terms: [] } };
      if (!isModuleAccessible(state.active)) {
        const firstModule = getActiveUiModuleIds()[0] || "administracion";
        applyScreenSnapshot({ active: firstModule, activeSubmodule: null, laborArea: "" });
      }
      render();
    })
    .catch((error) => {
      state.sessionApi = { status: "error", data: null, error: error.message || "Session context unavailable" };
      render();
    });
}

function mapApiProduct(item) {
  return {
    id: item.id,
    sku: item.code,
    name: item.name,
    kind: item.type === "service" ? "Servicio" : "Producto",
    category: item.category || "Sin categoria",
    unit: item.base_unit,
    status: item.status === "active" ? "Activo" : item.status === "inactive" ? "Inactivo" : "En espera de aprobacion",
    targetPrice: Number(item.target_price || 0),
    standardCost: Number(item.standard_cost || 0),
    center: item.cost_center || "Produccion",
    owner: item.responsible_area || "Sin asignar",
    expectedMargin: Number(item.expected_margin || 0),
    description: item.description || "",
    inventoryItemId: item.inventory_item_id || ""
  };
}

function mapApiRecipe(item, products) {
  const versions = [...(item.versions || [])].sort((a, b) => Number(b.version_number) - Number(a.version_number));
  const currentVersion = versions.find((version) => version.id === item.current_version_id) || versions.find((version) => version.status === "approved") || null;
  const draftVersion = versions.find((version) => ["draft","pending_approval"].includes(version.status)) || null;
  const version = draftVersion || currentVersion || versions[0];
  const product = products.find((entry) => entry.id === item.product_service_id);
  const approval = { draft: "Borrador", pending_approval: "Pendiente de aprobacion", approved: "Aprobada", obsolete: "Obsoleta" };
  return {
    id: item.id,
    code: item.code,
    productServiceId: item.product_service_id,
    product: product?.name || item.name,
    version: version?.version_number || 1,
    versionId: version?.id || "",
    versionStatus: version?.status || "draft",
    currentVersionId: currentVersion?.id || "",
    currentVersion: currentVersion?.version_number || null,
    currentVersionData: currentVersion,
    draftVersionId: draftVersion?.id || "",
    quantityBase: Number(version?.base_quantity || 1),
    suggestedDurationDays: Number(version?.suggested_duration_days || 1),
    unit: version?.base_unit || product?.unit || "pieza",
    status: item.status === "active" ? "Activa" : "Borrador",
    approvalStatus: approval[version?.status] || "Borrador",
    approvedBy: version?.approved_by || "",
    approvedAt: version?.approved_at || "",
    changeReason: version?.change_reason || "",
    center: product?.center || "Produccion",
    resources: (version?.resources || []).map((resource) => ({
      resourceId: resource.resource_ref_id || resource.resource_code,
      resourceCode: resource.resource_code,
      resourceName: resource.resource_name,
      resourceType: resource.resource_type,
      quantity: Number(resource.quantity),
      unit: resource.unit,
      unitCost: Number(resource.unit_cost || 0)
    })),
    steps: (version?.stages || []).filter((stage) => stage.status === "active").map((stage) => stage.name),
    stageDefinitions: (version?.stages || []).filter((stage) => stage.status === "active").map((stage) => ({
      laborAreaId: stage.labor_area_ref_id || "",
      laborAreaName: stage.labor_area_name || stage.name,
      name: stage.name,
      expectedMinutes: stage.expected_minutes,
      weightPercent: Number(stage.weight_percent || 0),
      sortOrder: Number(stage.sort_order || 0)
    })),
    createdAt: new Date().toISOString().slice(0, 10)
  };
}

function mapApiMachine(item){return {id:item.id,code:item.code,name:item.name,areaId:item.area_ref_id||"",area:item.area_name||"",machineType:item.machine_type,unit:"MIN",available:Number(item.available_minutes_per_day||0),cost:Number(item.cost_per_minute||0),type:"Maquinaria",source:"Maquinaria",status:item.status==="active"?"Activo":item.status==="maintenance"?"Mantenimiento":"Inactivo"};}
function mapApiOrderStatus(status){return ({released:"Liberada",waiting_resources:"En espera de recursos",in_progress:"En produccion",paused:"Pausada",in_validation:"En validacion",completed:"Terminada",cancelled:"Cancelada"})[status]||status;}
function toApiOrderStatus(status){return ({Liberada:"released","En espera de recursos":"waiting_resources","En produccion":"in_progress",Pausada:"paused","En validacion":"in_validation",Terminada:"completed",Cancelada:"cancelled"})[status]||status;}
function mapApiStageStatus(status){return ({pending:"Pendiente",in_progress:"En proceso",completed:"Terminada",skipped:"Omitida",blocked:"Bloqueada"})[status]||status;}
function getOrderCloseState(order){
  const stagesComplete=(order.areas||[]).every((stage)=>["Terminada","Omitida"].includes(stage.status));
  return {stagesComplete,ready:stagesComplete};
}
function productionOrderTransitionPermission(currentStatus,targetStatus){
  if(targetStatus==="Liberada")return "production.order.release";
  if(targetStatus==="En espera de recursos")return "production.order.wait_resources";
  if(targetStatus==="En produccion")return ["Liberada","En espera de recursos"].includes(currentStatus)?"production.order.start":"production.order.resume";
  if(targetStatus==="Pausada")return "production.order.pause";
  if(targetStatus==="En validacion")return "production.order.send_to_validation";
  if(targetStatus==="Terminada")return "production.order.complete";
  if(targetStatus==="Cancelada")return "production.order.cancel";
  return "";
}
function productionStagePermission(status){return ({pending:"production.order_stage.reset",in_progress:"production.order_stage.update",completed:"production.order_stage.complete",blocked:"production.order_stage.block",skipped:"production.order_stage.skip"})[status]||"";}
function getOrderStatusOptions(order){
  const transitions={
    Liberada:["En espera de recursos","En produccion","Cancelada"],
    "En espera de recursos":["Liberada","En produccion","Cancelada"],
    "En produccion":["Pausada","Cancelada"],
    Pausada:["En produccion","Cancelada"],
    "En validacion":["En produccion"],
    Terminada:[],Cancelada:[]
  };
  const options=[order.status,...(transitions[order.status]||[])];
  if(order.status==="En validacion"&&getOrderCloseState(order).ready)options.push("Terminada");
  return [...new Set(options)].filter(status=>status===order.status||hasPermission(productionOrderTransitionPermission(order.status,status)));
}
function getOrderCloseHelp(order){
  if(order.status!=="En validacion")return "";
  const close=getOrderCloseState(order);
  if(!close.stagesComplete)return t("orderCloseStagesHelp");
  return t("orderCloseReady");
}
function mapApiOrderRecipeSnapshot(item, fallbackRecipe) {
  const snapshot = item.recipe_snapshot || {};
  const version = (snapshot.versions || []).find((entry) => entry.id === item.recipe_version_id);
  if (!version) return fallbackRecipe || { resources: [], steps: [], quantityBase: 1, unit: item.unit };
  return {
    ...(fallbackRecipe || {}),
    id: snapshot.id || item.recipe_id,
    productServiceId: snapshot.product_service_id || item.product_service_id,
    product: fallbackRecipe?.product || snapshot.name || item.product_service_id,
    version: Number(version.version_number || 1),
    versionId: version.id,
    quantityBase: Number(version.base_quantity || 1),
    suggestedDurationDays: Number(version.suggested_duration_days || 1),
    unit: version.base_unit || item.unit,
    resources: (version.resources || []).map((resource) => ({
      resourceId: resource.resource_ref_id || resource.resource_code,
      resourceCode: resource.resource_code,
      resourceName: resource.resource_name,
      resourceType: resource.resource_type,
      quantity: Number(resource.quantity || 0),
      unit: resource.unit,
      unitCost: Number(resource.unit_cost || 0)
    })),
    steps: (version.stages || []).filter((stage) => stage.status === "active").map((stage) => stage.name)
  };
}
function mapApiOrder(item, recipes){const recipe=recipes.find((entry)=>entry.id===item.recipe_id);const recipeSnapshot=mapApiOrderRecipeSnapshot(item,recipe);return {id:item.id,code:item.code,productServiceId:item.product_service_id,recipeId:item.recipe_id,recipeVersion:recipeSnapshot.version||1,recipeSnapshot,recipeName:recipeSnapshot.product||item.product_service_id,quantity:Number(item.quantity),unit:item.unit,status:mapApiOrderStatus(item.status),priority:({high:"Alta",medium:"Media",low:"Baja"})[item.priority]||item.priority,plannedStartDate:item.planned_start_at?.slice(0,10)||"",plannedEndDate:item.planned_end_date||"",plannedDurationDays:Number(item.planned_duration_days||1),dueDate:item.required_at?.slice(0,10)||"",center:recipeSnapshot.center||"Produccion",responsibleWorkerId:item.responsible_worker_id,responsible:item.responsible_name,plannedCost:Number(item.planned_cost||0),actualCost:item.actual_cost==null?null:Number(item.actual_cost),overallProgress:Number(item.overall_progress_percent||0),resources:(item.resources||[]).map((resource)=>({id:resource.id,type:resource.resource_type,refId:resource.resource_ref_id,code:resource.resource_code,name:resource.resource_name,unit:resource.unit,plannedQuantity:Number(resource.planned_quantity),actualQuantity:resource.actual_quantity==null?null:Number(resource.actual_quantity),unitCost:Number(resource.unit_cost),plannedCost:Number(resource.planned_cost),actualCost:resource.actual_cost==null?null:Number(resource.actual_cost),reservationIds:resource.reservation_ref_ids||[]})),releaseStatus:"Liberada",areas:(item.stages||[]).map((stage)=>({id:stage.id,recipeStageId:stage.recipe_stage_id,area:stage.name,phaseNumber:Number(stage.sort_order||0),weightPercent:Number(stage.weight_percent||0),responsibleWorkerId:stage.responsible_worker_id,responsible:stage.responsible_name||"",status:mapApiStageStatus(stage.status),progress:Number(stage.progress_percent||0),plannedMinutes:stage.planned_minutes,actualMinutes:stage.actual_minutes,actualCostFactor:1})),createdAt:item.created_at?.slice(0,10)||""};}

function loadProductionApiData() {
  if (getApiMode() !== "api" || state.productionApi.status === "loading") return Promise.resolve();
  state.productionApi = { status: "loading", error: "" };
  return getProductionCatalog()
    .then(({ products, recipes, machines, orders }) => {
      const mappedProducts = products.map(mapApiProduct);
      const mappedRecipes = recipes.map((recipe) => mapApiRecipe(recipe, mappedProducts));
      mockDb.saveProductsServices(mappedProducts);
      mockDb.saveRecipes(mappedRecipes);
      mockDb.saveMachines((machines||[]).map(mapApiMachine));
      mockDb.saveOrders((orders||[]).map((order)=>mapApiOrder(order,mappedRecipes)));
      state.productionApi = { status: "ready", error: "" };
      render();
    })
    .catch((error) => {
      state.productionApi = { status: "error", error: error.message || "Production API unavailable" };
      render();
    });
}

function mapInventoryStatus(status) { return status === "active" ? "Activo" : status === "blocked" ? "Bloqueado" : "Inactivo"; }
function loadInventoryApiData() {
  if (getApiMode() !== "api" || !isInventoryApiEnabled() || state.inventoryApi.status === "loading") return Promise.resolve();
  state.inventoryApi = { status: "loading", error: "" };
  return getInventoryCatalog().then(({ warehouses }) => {
    const records = [
      ...warehouses.map((item) => ({id:item.id,code:item.code,moduleId:"almacenes",submoduleId:"almacenes",recordType:"warehouse",title:item.name,detail:item.type,status:mapInventoryStatus(item.status),owner:item.owner||"",fields:{type:item.type,businessCenter:item.business_center,location:item.location,capacity:item.capacity||"",policy:item.inventory_policy,zone:item.zone||"",aisle:item.aisle||"",rack:item.rack||"",level:item.level||"",position:item.position||"",description:item.description||""}}))
    ];
    mockDb.saveModuleRecords("almacenes", records); state.inventoryApi={status:"ready",error:""}; state.inventoryItems={status:"idle",error:""}; state.inventoryMovements={status:"idle",error:""}; state.finishedGoodsReceipts={status:"idle",orders:[],summaries:[],products:[],error:""}; state.inventoryBalances={status:"idle",data:[],page:{},error:"",queryKey:"",cursor:"",previousCursors:[]}; render();
  }).catch((error)=>{state.inventoryApi={status:"error",error:error.message||"Inventory API unavailable"};render();});
}

function loadInventoryItemData() {
  if (getApiMode() !== "api" || !isInventoryApiEnabled() || state.inventoryItems.status === "loading") return Promise.resolve();
  state.inventoryItems={status:"loading",error:""};
  return getInventoryItems().then((response) => {
    const records=mockDb.loadModuleRecords("almacenes");
    const warehouses=records.filter((record)=>record.recordType==="warehouse");
    const warehouseById=Object.fromEntries(warehouses.map((item)=>[item.id,item]));
    const items=(response.data||[]).map((item)=>({id:item.id,code:item.code,moduleId:"almacenes",submoduleId:"articulos",recordType:"inventoryItem",title:item.name,detail:`${item.type} - ${item.base_unit}`,status:mapInventoryStatus(item.status),owner:warehouseById[item.suggested_warehouse_id]?.title||"",fields:{type:item.type,category:item.category||"",unit:item.base_unit,defaultUnitCost:Number(item.default_unit_cost_per_base_unit??item.default_unit_cost??0),minStock:item.minimum_stock,maxStock:item.maximum_stock||"",policy:item.inventory_policy,useInRecipe:Boolean(item.use_in_recipe),defaultWarehouseId:item.suggested_warehouse_id||"",defaultWarehouseName:warehouseById[item.suggested_warehouse_id]?.title||"",description:item.description||""}}));
    mockDb.saveModuleRecords("almacenes",[...records.filter((record)=>record.recordType!=="inventoryItem"),...items]);
    state.inventoryItems={status:"ready",error:""};render();
  }).catch((error)=>{state.inventoryItems={status:"error",error:error.message||"Inventory items unavailable"};render();});
}

function loadInventoryMovementData() {
  if (getApiMode() !== "api" || !isInventoryApiEnabled() || state.inventoryMovements.status === "loading") return Promise.resolve();
  state.inventoryMovements = { status: "loading", error: "" };
  return getInventoryMovements().then((response) => {
    const records = mockDb.loadModuleRecords("almacenes");
    const items = records.filter((record) => record.recordType === "inventoryItem");
    const warehouses = records.filter((record) => record.recordType === "warehouse");
    const itemById = Object.fromEntries(items.map((item) => [item.id,item]));
    const warehouseById = Object.fromEntries(warehouses.map((item) => [item.id,item]));
    const movements = (response.data || []).map((item) => ({id:item.id,code:item.movement_code,moduleId:"almacenes",submoduleId:"movimientos",recordType:"inventoryMovement",title:itemById[item.inventory_item_id]?.title||item.inventory_item_id,detail:`${item.movement_type} - ${item.quantity} ${item.unit}`,status:item.status==="recorded"?"Registrado":"Reversado",owner:warehouseById[item.warehouse_id]?.title||item.warehouse_id,fields:{movementType:item.movement_type,sourceDocument:item.source_id,itemId:item.inventory_item_id,item:itemById[item.inventory_item_id]?.title||item.inventory_item_id,quantity:item.quantity,unit:item.unit,warehouseId:item.warehouse_id,warehouseName:warehouseById[item.warehouse_id]?.title||item.warehouse_id,movementDate:item.occurred_at?.slice(0,10),reason:item.reason||""}}));
    mockDb.saveModuleRecords("almacenes", [...records.filter((record) => record.recordType !== "inventoryMovement"),...movements]);
    state.inventoryMovements={status:"ready",error:""}; render();
  }).catch((error) => { state.inventoryMovements={status:"error",error:error.message||"Inventory movements unavailable"}; render(); });
}

function loadFinishedGoodsReceiptData() {
  if (getApiMode() !== "api" || !isInventoryApiEnabled() || !["inventory.finished_goods_receipt.read","inventory.finished_goods_receipt.receive"].some(hasPermission) || state.finishedGoodsReceipts.status === "loading") return Promise.resolve();
  state.finishedGoodsReceipts = { ...state.finishedGoodsReceipts, status: "loading", error: "" };
  return Promise.all([getFinishedGoodsCandidates(),getFinishedGoodsReceipts()]).then(([candidates,response])=>{
    state.finishedGoodsReceipts={status:"ready",orders:candidates.orders||[],products:candidates.products||[],summaries:response.data||[],error:""};render();
  }).catch((error)=>{state.finishedGoodsReceipts={status:"error",orders:[],products:[],summaries:[],error:error.message||t("finishedGoodsReceiptLoadError")};render();});
}

function loadHrApiData() {
  if (getApiMode() !== "api" || state.hrApi.status === "loading") return Promise.resolve();
  state.hrApi={status:"loading",error:""};
  return Promise.all([getHrCatalog(),getHrWorkers()]).then(([{areas,positions},workers])=>{
    mockDb.saveLaborAreas((areas||[]).map((area)=>({id:area.id,code:area.code,name:area.name,description:area.description||"",status:area.status==="active"?"Activo":"Inactivo"})));
    mockDb.saveLaborRoles((positions||[]).map((position)=>({id:position.id,areaId:position.labor_area_id,area:(areas||[]).find((area)=>area.id===position.labor_area_id)?.name||"",position:position.position,name:position.recipe_name,quantity:position.resource_quantity,minutesPerResource:position.minutes_per_resource,available:position.resource_quantity*position.minutes_per_resource,hourlyCost:Number(position.hourly_cost),cost:Number(position.hourly_cost)/60,unit:"min",type:"Mano de obra",source:"Recursos Humanos",intervenesInProduction:Boolean(position.intervenes_in_production),intervenesInMaintenance:Boolean(position.intervenes_in_maintenance),status:position.status==="active"?"Activo":"Inactivo"})));
    state.hrApi={status:"ready",error:"",workers:workers||[]};render();
  }).catch((error)=>{state.hrApi={status:"error",error:error.message||"HR API unavailable"};render();});
}

const salesCustomerStatusFromApi={prospect:"Prospecto",active:"Activo",inactive:"Inactivo",blocked:"Bloqueado"};
const salesCustomerStatusToApi={Prospecto:"prospect",Activo:"active",Inactivo:"inactive",Bloqueado:"blocked"};
const salesQuoteStatusFromApi={draft:"Borrador",quoted:"Cotizada",approved:"Aprobado",expired:"Vencida",cancelled:"Cancelada"};
const salesOrderStatusFromApi={confirmed:"Confirmado",fulfillment_pending:"Pendiente de surtido",ready:"Listo",partially_delivered:"Parcialmente entregado",delivered:"Entregado",cancelled:"Cancelado"};
const salesDeliveryStatusFromApi={draft:"Pendiente de entrega",confirmed:"Entregado",cancelled:"Cancelado"};
function formatSalesMoney(value,currency="MXN"){return new Intl.NumberFormat(state.lang==="en"?"en-US":"es-MX",{style:"currency",currency}).format(Number(value||0));}
function mapApiSalesCustomer(item){const contact=(item.contacts||[]).find(entry=>entry.is_primary&&entry.status==="active")||(item.contacts||[])[0]||{};const address=item.billing_address||{};return {id:item.id,code:item.code,moduleId:"ventas",submoduleId:"clientes",recordType:"customer",title:item.commercial_name,detail:`${item.legal_name||item.commercial_name} - ${item.tax_id||"Sin perfil fiscal"}`,status:salesCustomerStatusFromApi[item.status]||item.status,owner:item.responsible_worker_name,fields:{customerType:item.customer_type,commercialName:item.commercial_name,contactName:contact.name||"",contactEmail:contact.email||"",contactPhone:contact.phone||"",contactRole:contact.role||"",responsibleWorkerId:item.responsible_worker_id,salesOwner:item.responsible_worker_name,paymentTerms:item.payment_terms,currency:item.currency,creditLimit:Number(item.credit_limit||0),commercialNotes:item.notes||"",billingLegalName:item.legal_name||"",taxId:item.tax_id||"",taxRegime:item.tax_regime||"",cfdiUse:item.cfdi_use||"",billingEmail:item.billing_email||"",billingPhone:item.billing_phone||"",billingStreet:address.street||"",billingExterior:address.exterior_number||"",billingInterior:address.interior_number||"",billingNeighborhood:address.neighborhood||"",billingCity:address.city||"",billingState:address.state||"",billingZipCode:address.postal_code||"",billingCountry:address.country||""},createdAt:item.created_at,updatedAt:item.updated_at};}
function mapApiSalesQuote(item){const lines=(item.lines||[]).map(line=>({productServiceId:line.product_service_id,productServiceName:`${line.product_service_code} - ${line.product_service_name}`,quantity:Number(line.quantity),unit:line.unit,unitPrice:Number(line.unit_price),discount:Number(line.discount_percentage),subtotal:Number(line.subtotal),total:Number(line.total),estimatedCost:line.estimated_cost==null?null:Number(line.estimated_cost)}));return {id:item.id,code:item.code,moduleId:"ventas",submoduleId:"cotizaciones",recordType:"quote",title:`${item.customer_name} - ${lines.length} líneas`,detail:`${formatSalesMoney(item.total,item.currency)} - ${item.valid_until}`,status:salesQuoteStatusFromApi[item.status]||item.status,owner:item.responsible_worker_name,fields:{customerId:item.customer_id,customerName:`${item.customer_code} - ${item.customer_name}`,responsibleWorkerId:item.responsible_worker_id,lines,productServiceId:lines[0]?.productServiceId||"",productServiceName:lines[0]?.productServiceName||"",quantity:lines.reduce((sum,line)=>sum+line.quantity,0),unit:lines[0]?.unit||"",unitPrice:lines[0]?.unitPrice||0,discount:lines[0]?.discount||0,subtotal:Number(item.subtotal),total:Number(item.total),estimatedCost:item.estimated_cost==null?null:Number(item.estimated_cost),estimatedMargin:item.estimated_margin==null?null:Number(item.estimated_margin),validUntil:item.valid_until,deliveryPromise:item.promised_delivery_date||"",paymentTerms:item.payment_terms,currency:item.currency,notes:item.notes||""},createdAt:item.created_at,updatedAt:item.updated_at};}
function mapApiSalesOrder(item){const lines=(item.lines||[]).map(line=>({id:line.id,productServiceId:line.product_service_id,productServiceName:`${line.product_service_code} - ${line.product_service_name}`,productServiceType:line.product_service_type,quantity:Number(line.ordered_quantity),deliveredQuantity:Number(line.delivered_quantity),unit:line.unit,unitPrice:Number(line.unit_price),discount:Number(line.discount_percentage),total:Number(line.total),estimatedCost:line.estimated_cost==null?null:Number(line.estimated_cost),fulfillmentMode:line.fulfillment_mode,fulfillmentStatus:line.fulfillment_status,inventoryItemId:line.inventory_item_id||"",inventoryItemCode:line.inventory_item_code||"",inventoryItemName:line.inventory_item_name||"",reservations:line.reservations||[],productionRequestId:line.production_request_id||""}));return {id:item.id,code:item.code,moduleId:"ventas",submoduleId:"pedidos",recordType:"salesOrder",title:`${item.customer_code} - ${item.customer_name}`,detail:`${item.quote_code} - ${formatSalesMoney(item.total,item.currency)}`,status:salesOrderStatusFromApi[item.status]||item.status,owner:item.responsible_worker_name,fields:{quoteId:item.quote_id,quoteCode:item.quote_code,customerId:item.customer_id,customerName:item.customer_name,lines,subtotal:Number(item.subtotal),total:Number(item.total),currency:item.currency,paymentTerms:item.payment_terms,estimatedCost:item.estimated_cost==null?null:Number(item.estimated_cost),estimatedMargin:item.estimated_margin==null?null:Number(item.estimated_margin),actualCost:item.actual_cost==null?null:Number(item.actual_cost),actualMargin:item.actual_margin==null?null:Number(item.actual_margin),deliveryPromise:item.promised_delivery_date||"",fulfillmentMode:[...new Set(lines.map(line=>line.fulfillmentMode))].join(" / "),fulfillmentState:item.fulfillment_state||"idle",cancellationState:item.cancellation_state||"idle",notes:item.notes||""},createdAt:item.created_at,updatedAt:item.updated_at};}
function mapApiSalesDelivery(item){const lines=(item.lines||[]).map(line=>({id:line.id,orderLineId:line.order_line_id,productServiceId:line.product_service_id,productServiceName:`${line.product_service_code} - ${line.product_service_name}`,quantity:Number(line.quantity),unit:line.unit,actualCost:line.actual_cost==null?null:Number(line.actual_cost),actualCostSource:line.actual_cost_source||""}));return {id:item.id,code:item.code,moduleId:"ventas",submoduleId:"entregas",recordType:"salesDelivery",title:`${item.order_code} - ${item.customer_name}`,detail:`${salesDeliveryStatusFromApi[item.status]||item.status} - ${item.scheduled_date}`,status:salesDeliveryStatusFromApi[item.status]||item.status,owner:item.recipient_name||item.customer_name,fields:{orderId:item.order_id,orderCode:item.order_code,customerName:item.customer_name,deliveryStatus:salesDeliveryStatusFromApi[item.status]||item.status,confirmationState:item.confirmation_state||"idle",deliveryDate:item.scheduled_date,deliveredAt:item.delivered_at||"",recipient:item.recipient_name||"",deliveryReference:item.evidence_reference||"",notes:item.notes||"",lines},createdAt:item.created_at,updatedAt:item.updated_at};}
async function loadSalesApiData() {
  if (getApiMode() !== "api" || state.salesApi.status === "loading") return;
  state.salesApi = { ...state.salesApi, status: "loading", error: "", referenceWarnings: [] };
  const canReadCustomers = hasPermission("sales.customer.read");
  const canReadQuotes = hasPermission("sales.quote.read");
  const canReadOrders = hasPermission("sales.order.read");
  const canReadDeliveries = hasPermission("sales.delivery.read");
  const needsWorkers = ["sales.customer.create", "sales.customer.update", "sales.quote.create", "sales.quote.update"].some(hasPermission);
  const needsQuoteCatalogs = ["sales.quote.create", "sales.quote.update"].some(hasPermission);
  const needsReferences = ["sales.customer.create", "sales.customer.update", "sales.quote.create", "sales.quote.update", "sales.order.create"].some(hasPermission);
  try {
    const workspace = await getSalesWorkspace({ customers: canReadCustomers, quotes: canReadQuotes, orders: canReadOrders, deliveries: canReadDeliveries, references: needsReferences });
    const [workersResult, productsResult, unitsResult] = await Promise.allSettled([
      needsWorkers ? getSalesEligibleWorkers() : Promise.resolve([]),
      needsQuoteCatalogs ? getProductionProducts() : Promise.resolve([]),
      needsQuoteCatalogs ? getUnitsOfMeasure() : Promise.resolve([])
    ]);
    const warnings = [];
    const workers = workersResult.status === "fulfilled" ? workersResult.value : [];
    const products = productsResult.status === "fulfilled" ? productsResult.value : [];
    const units = unitsResult.status === "fulfilled" ? unitsResult.value : [];
    if (workersResult.status === "rejected") warnings.push(t("salesWorkersUnavailable"));
    if (productsResult.status === "rejected") warnings.push(t("salesProductsUnavailable"));
    if (unitsResult.status === "rejected") warnings.push(t("salesUnitsUnavailable"));
    Object.entries(workspace.errors || {}).forEach(([name, message]) => warnings.push(`${name}: ${message}`));
    const previous = mockDb.loadModuleRecords("ventas");
    const keepOrReplace = (name, recordType, values, mapper) => workspace.errors?.[name]
      ? previous.filter((record) => record.recordType === recordType)
      : (values || []).map(mapper);
    const records = [
      ...keepOrReplace("customers", "customer", workspace.customers, mapApiSalesCustomer),
      ...keepOrReplace("quotes", "quote", workspace.quotes, mapApiSalesQuote),
      ...keepOrReplace("orders", "salesOrder", workspace.orders, mapApiSalesOrder),
      ...keepOrReplace("deliveries", "salesDelivery", workspace.deliveries, mapApiSalesDelivery)
    ];
    mockDb.saveModuleRecords("ventas", records);
    if (needsQuoteCatalogs) mockDb.saveProductsServices((products || []).map(mapApiProduct));
    state.unitCatalog = unitsResult.status === "fulfilled"
      ? { status: "ready", data: units || [], error: "" }
      : { status: "error", data: [], error: unitsResult.reason?.message || "Unit catalog unavailable" };
    const references = workspace.errors?.references ? state.salesApi.references : workspace.references;
    state.salesApi = { status: "ready", error: "", referenceWarnings: warnings, workers: workers || [], references: references || { currencies: [], payment_terms: [] } };
  } catch (error) {
    state.salesApi = { ...state.salesApi, status: "error", error: error.message || "Sales API unavailable" };
  }
  render();
}

function renderSalesReferenceWarnings() {
  return (state.salesApi.referenceWarnings || []).length
    ? `<p class="helper-copy">${escapeHtml(state.salesApi.referenceWarnings.join(" "))}</p>`
    : "";
}

function chooseSessionTenant(tenants) {
  const currentTenantId = getDemoTenantId();
  return tenants.find((item) => item.tenant?.id === currentTenantId) || tenants[0] || null;
}

function resolveSessionTenant() {
  if (getApiMode() !== "api" || !hasApiSessionAccess()) return;
  if (!isAuthRequired()) {
    state.tenantResolution = { status: "ready", tenants: [], error: "" };
    loadSessionContext();
    return;
  }
  if (state.tenantResolution.status === "loading") return;
  state.tenantResolution = { status: "loading", tenants: state.tenantResolution.tenants, error: "" };
  getSessionTenants()
    .then((tenants) => {
      const selected = chooseSessionTenant(tenants);
      if (!selected) {
        state.tenantResolution = {
          status: "error",
          tenants: [],
          error: "Tu usuario no tiene tenants activos asignados."
        };
        state.sessionApi = { status: "error", data: null, error: state.tenantResolution.error };
        applyScreenSnapshot({ active: "administracion", activeSubmodule: null, laborArea: "" });
        render();
        return;
      }
      const previousTenantId = getDemoTenantId();
      setActiveTenantId(selected.tenant.id);
      state.tenantResolution = { status: "ready", tenants, error: "" };
      if (previousTenantId !== selected.tenant.id || state.active !== "administracion") {
        applyScreenSnapshot({ active: "administracion", activeSubmodule: null, laborArea: "" });
      }
      loadSessionContext();
    })
    .catch((error) => {
      state.tenantResolution = {
        status: "error",
        tenants: [],
        error: error.message || "No se pudieron resolver los tenants del usuario."
      };
      state.sessionApi = { status: "error", data: null, error: state.tenantResolution.error };
      applyScreenSnapshot({ active: "administracion", activeSubmodule: null, laborArea: "" });
      render();
    });
}

function ensureSessionContext() {
  if (getApiMode() === "api" && hasApiSessionAccess() && state.sessionApi.status === "idle") {
    loadSessionContext();
  }
}

async function loadPurchasingApiData() {
  if (getApiMode() !== "api" || state.purchasingApi.status === "loading") return;
  state.purchasingApi={...state.purchasingApi,status:"loading",error:""};
  try {
    const [workspace,itemResult,catalogResult]=await Promise.all([getPurchasingWorkspace(),getInventoryItems({status:"active"}),getInventoryCatalog()]);
    const critical=Object.entries(workspace.errors||{});
    if(critical.length) throw new Error(critical.map(([name,message])=>`${name}: ${message}`).join(" · "));
    state.purchasingApi={status:"ready",error:"",...workspace,items:itemResult.data||[],warehouses:catalogResult.warehouses||[]};
  } catch(error) { state.purchasingApi={...state.purchasingApi,status:"error",error:error.message||"Purchasing API unavailable"}; }
  render();
}

async function loadMaintenanceApiData(){
  if(getApiMode()!=="api"||state.maintenanceApi.status==="loading")return;
  state.maintenanceApi={...state.maintenanceApi,status:"loading",error:""};
  try{
    const canMutateOrders=hasPermission("maintenance.order.create")||["request","assign","start","wait_for_parts","resume","resolve","close","reopen","cancel"].some(action=>hasPermission(`maintenance.order.${action}`)),canUseTime=hasPermission("maintenance.time.create"),canUseMaterials=hasPermission("maintenance.material_request.create")||hasPermission("maintenance.material_request.cancel")||hasPermission("maintenance.material_request.reconcile");
    const [ordersResult,workersResult,productionResult,itemsResult,catalogResult]=await Promise.allSettled([getMaintenanceOrders(),canMutateOrders||canUseTime?getMaintenanceEligibleWorkers():Promise.resolve([]),canMutateOrders?getProductionCatalog():Promise.resolve({machines:[],orders:[]}),canUseMaterials?getInventoryItems({status:"active"}):Promise.resolve({data:[]}),canUseMaterials?getInventoryCatalog():Promise.resolve({warehouses:[]})]);
    if(ordersResult.status==="rejected")throw ordersResult.reason;
    const workers=workersResult.status==="fulfilled"?workersResult.value:[],production=productionResult.status==="fulfilled"?productionResult.value:{machines:[],orders:[]},items=itemsResult.status==="fulfilled"?itemsResult.value:{data:[]},catalog=catalogResult.status==="fulfilled"?catalogResult.value:{warehouses:[]};
    const warnings=[workersResult,productionResult,itemsResult,catalogResult].filter(result=>result.status==="rejected").map(result=>result.reason?.message||"Catalog unavailable");
    state.maintenanceApi={status:"ready",error:"",warnings,orders:ordersResult.value,workers,machines:production.machines||[],productionOrders:(production.orders||[]).filter(item=>["waiting_resources","in_progress"].includes(item.status)),items:items.data||[],warehouses:(catalog.warehouses||[]).filter(item=>item.status==="active"&&["spare_parts","spareParts"].includes(item.type))};
  }catch(error){state.maintenanceApi={...state.maintenanceApi,status:"error",error:error.message||"Maintenance API unavailable"};}
  render();
}
function maintenanceStatus(value){const map={draft:["Borrador","Draft"],requested:["Solicitada","Requested"],assigned:["Asignada","Assigned"],in_progress:["En proceso","In progress"],waiting_resources:["Esperando recursos","Waiting for resources"],waiting_parts:["Esperando refacciones","Waiting for parts"],resolved:["Resuelta","Resolved"],closed:["Cerrada","Closed"],cancelled:["Cancelada","Cancelled"],processing:["Procesando","Processing"],completed:["Conciliada","Reconciled"],reserved:["Reservada","Reserved"],issued:["Entregada","Issued"],released:["Liberada","Released"],failed:["Fallida","Failed"],cancelling:["Cancelando","Cancelling"],needs_reconciliation:["Requiere conciliacion","Needs reconciliation"]};return (map[value]||[value,value])[state.lang==="en"?1:0];}
function maintenanceTransitionButtons(order,en){if(order.integration_status==="needs_reconciliation")return hasPermission("maintenance.order.reconcile")?`<button class="primary-action small-action" type="button" data-maintenance-transition="reconcile" data-order-id="${escapeAttribute(order.id)}">${en?"Reconcile":"Conciliar"}</button>`:"";const buttons=[];if(order.status==="draft")buttons.push(["request",en?"Request":"Solicitar"]);if(["requested","assigned"].includes(order.status))buttons.push(["assign",order.status==="assigned"?(en?"Reassign":"Reasignar"):(en?"Assign":"Asignar")]);if(order.status==="assigned")buttons.push(["start",en?"Start":"Iniciar"]);if(order.status==="in_progress")buttons.push(["wait_for_parts",en?"Wait for parts":"Esperar refacciones"],["resolve",en?"Resolve":"Resolver"]);if(order.status==="waiting_parts")buttons.push(["resume",en?"Resume":"Reanudar"],["resolve",en?"Resolve":"Resolver"]);if(order.status==="resolved")buttons.push(["close",en?"Close":"Cerrar"],["reopen",en?"Reopen":"Reabrir"]);if(["draft","requested","assigned"].includes(order.status))buttons.push(["cancel",en?"Cancel":"Cancelar"]);return buttons.filter(([action])=>hasPermission(`maintenance.order.${action}`)).map(([action,label])=>`<button class="${action==="resolve"?"primary-action":"secondary-action"} small-action" type="button" data-maintenance-transition="${action}" data-order-id="${escapeAttribute(order.id)}">${label}</button>`).join("");}

function maintenanceDateTimeValue(value=new Date()){
  const date=value instanceof Date?value:new Date(value);
  if(Number.isNaN(date.getTime()))return "";
  return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);
}

function maintenanceTimeFields(order,en){
  const end=new Date(),candidate=order.started_at?new Date(order.started_at):new Date(end.getTime()-60*60000);
  const start=Number.isNaN(candidate.getTime())||candidate>=end?new Date(end.getTime()-60*60000):candidate;
  return `<section class="maintenance-resolution-time"><div class="section-title"><span class="section-icon">&#9201;</span><strong>${en?"Time spent":"Tiempo empleado"}</strong></div><p class="helper-copy">${en?"At least one time entry is required. It will be assigned to the current technician.":"Se requiere al menos un registro de tiempo. Se asignara al tecnico responsable actual."}</p><div class="form-grid"><label class="preview-field"><span>${en?"Technician":"Tecnico"}</span><input value="${escapeAttribute(order.assigned_worker_name||"")}" readonly></label><label class="preview-field"><span>${en?"Current total":"Total actual"}</span><input value="${formatNumber(Number(order.total_minutes||0))} min" readonly></label><label class="preview-field"><span>${en?"Start":"Inicio"}</span><input name="time_started_at" type="datetime-local" value="${maintenanceDateTimeValue(start)}" required></label><label class="preview-field"><span>${en?"End":"Fin"}</span><input name="time_ended_at" type="datetime-local" value="${maintenanceDateTimeValue(end)}" required></label><label class="preview-field wide-field"><span>${en?"Time notes":"Notas del tiempo"}</span><textarea name="time_notes" rows="2" maxlength="1000"></textarea></label></div></section>`;
}

function openMaintenanceTimeModal(order,en){
  modalContent.innerHTML=`<form class="recipe-form" id="maintenanceTimeModalForm"><div class="modal-head"><div><p class="eyebrow">${en?"Maintenance order":"Orden de mantenimiento"}</p><h2 id="modalTitle">${en?"Log time":"Registrar tiempo"}</h2><p class="helper-copy">${escapeHtml(order.code)} &middot; ${escapeHtml(order.title)}</p></div><button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button></div>${maintenanceTimeFields(order,en)}<div class="form-errors" id="formErrors" hidden></div><div class="modal-actions"><button class="secondary-action" type="button" data-action="close-maintenance-time">${t("cancel")}</button><button class="primary-action" type="submit">${en?"Save time":"Guardar tiempo"}</button></div></form>`;
  modalBackdrop.hidden=false;modalContent.querySelector(".modal-close").addEventListener("click",closeModal);modalContent.querySelector("[data-action='close-maintenance-time']").addEventListener("click",closeModal);modalContent.querySelector("#maintenanceTimeModalForm").addEventListener("submit",async event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.currentTarget)),start=new Date(data.time_started_at),end=new Date(data.time_ended_at),errors=[];if(!order.assigned_worker_id)errors.push(en?"Assign a technician before logging time.":"Asigna un tecnico antes de registrar tiempo.");if(!data.time_started_at||!data.time_ended_at||end<=start)errors.push(en?"End must be after start.":"El fin debe ser posterior al inicio.");if(end>new Date())errors.push(en?"End cannot be in the future.":"El fin no puede estar en el futuro.");renderFormErrors(errors);if(errors.length)return;try{await createMaintenanceTime(order.id,{worker_id:order.assigned_worker_id,started_at:start.toISOString(),ended_at:end.toISOString(),notes:data.time_notes.trim()||null});closeModal();await loadMaintenanceApiData();render();showToast(en?"Maintenance time saved.":"Tiempo de mantenimiento guardado.");}catch(error){renderFormErrors([error.message||"Error"]);}});
}

function openMaintenanceActionModal(order,action,en){
  const resolving=action==="resolve",needsTime=resolving&&Number(order.total_minutes||0)<=0,canCreateTime=hasPermission("maintenance.time.create");
  let timeCreated=false;
  modalContent.innerHTML=`<form class="recipe-form" id="maintenanceActionForm">
    <div class="modal-head"><div><p class="eyebrow">${en?"Maintenance order":"Orden de mantenimiento"}</p><h2 id="modalTitle">${resolving?(en?"Resolve order":"Resolver orden"):(en?"Cancel order":"Cancelar orden")}</h2><p class="helper-copy">${escapeHtml(order.code)} &middot; ${escapeHtml(order.title)}</p></div><button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button></div>
    ${resolving?`<p class="helper-copy">${en?"Document the technical result before releasing the equipment and sending the order to validation.":"Documenta el resultado tecnico antes de liberar el equipo y enviar la orden a validacion."}</p><div class="form-grid">
      <label class="preview-field wide-field"><span>${en?"Diagnosis":"Diagnostico"}</span><textarea name="diagnosis" rows="3" maxlength="4000" required>${escapeHtml(order.diagnosis||"")}</textarea><small>${en?"Condition found and scope of the failure.":"Condicion encontrada y alcance de la falla."}</small></label>
      <label class="preview-field wide-field"><span>${en?"Root cause (optional)":"Causa raiz (opcional)"}</span><textarea name="root_cause" rows="2" maxlength="2000">${escapeHtml(order.root_cause||"")}</textarea></label>
      <label class="preview-field wide-field"><span>${en?"Work performed":"Trabajo realizado"}</span><textarea name="work_performed" rows="3" maxlength="4000" required>${escapeHtml(order.work_performed||"")}</textarea><small>${en?"Repair, adjustment or intervention performed.":"Reparacion, ajuste o intervencion realizada."}</small></label>
      <label class="preview-field wide-field"><span>${en?"Verification":"Verificacion"}</span><textarea name="verification_notes" rows="3" maxlength="2000" required>${escapeHtml(order.verification_notes||"")}</textarea><small>${en?"Functional test and result after the intervention.":"Prueba funcional y resultado posterior a la intervencion."}</small></label>
    </div>${needsTime?(canCreateTime?maintenanceTimeFields(order,en):`<div class="form-errors maintenance-time-permission"><p>${en?"This order has no logged time. Ask a user with the maintenance.time.create permission to register it from the order.":"Esta orden no tiene tiempo registrado. Solicita a un usuario con el permiso maintenance.time.create que lo capture desde la orden."}</p></div>`):`<div class="form-notice"><p>${en?`Logged time: ${formatNumber(Number(order.total_minutes))} minutes.`:`Tiempo registrado: ${formatNumber(Number(order.total_minutes))} minutos.`}</p></div>`}`:`<p class="helper-copy">${en?"The reason will remain in the order audit trail.":"El motivo quedara registrado en la trazabilidad de la orden."}</p><div class="form-grid"><label class="preview-field wide-field"><span>${en?"Cancellation reason":"Motivo de cancelacion"}</span><textarea name="reason" rows="3" maxlength="1000" required></textarea></label></div>`}
    <div class="form-errors" id="formErrors" hidden></div><div class="modal-actions"><button class="secondary-action" type="button" data-action="close-maintenance-action">${t("cancel")}</button><button class="primary-action" type="submit">${resolving?(en?"Save and resolve":"Guardar y resolver"):(en?"Confirm cancellation":"Confirmar cancelacion")}</button></div>
  </form>`;
  modalBackdrop.hidden=false;
  modalContent.querySelector(".modal-close").addEventListener("click",closeModal);
  modalContent.querySelector("[data-action='close-maintenance-action']").addEventListener("click",closeModal);
  modalContent.querySelector("#maintenanceActionForm").addEventListener("submit",async event=>{
    event.preventDefault();
    const data=Object.fromEntries(new FormData(event.currentTarget));
    const errors=[];
    if(resolving){if(!data.diagnosis.trim())errors.push(en?"Diagnosis is required.":"El diagnostico es obligatorio.");if(!data.work_performed.trim())errors.push(en?"Work performed is required.":"El trabajo realizado es obligatorio.");if(!data.verification_notes.trim())errors.push(en?"Verification is required.":"La verificacion es obligatoria.");if(needsTime&&!canCreateTime)errors.push(en?"Logged time is required and your role cannot create it.":"Se requiere tiempo registrado y tu rol no puede crearlo.");if(needsTime&&canCreateTime&&!timeCreated){const start=new Date(data.time_started_at),end=new Date(data.time_ended_at);if(!order.assigned_worker_id)errors.push(en?"Assign a technician before logging time.":"Asigna un tecnico antes de registrar tiempo.");if(!data.time_started_at||!data.time_ended_at||end<=start)errors.push(en?"Time end must be after start.":"El fin del tiempo debe ser posterior al inicio.");if(end>new Date())errors.push(en?"Time end cannot be in the future.":"El fin del tiempo no puede estar en el futuro.");}}
    else if(data.reason.trim().length<3)errors.push(en?"Enter a cancellation reason of at least 3 characters.":"Captura un motivo de cancelacion de al menos 3 caracteres.");
    renderFormErrors(errors);if(errors.length)return;
    try{
      let result;
      if(resolving){await updateMaintenanceOrder(order.id,{diagnosis:data.diagnosis.trim(),root_cause:data.root_cause.trim()||null,work_performed:data.work_performed.trim(),verification_notes:data.verification_notes.trim()});if(needsTime&&canCreateTime&&!timeCreated){await createMaintenanceTime(order.id,{worker_id:order.assigned_worker_id,started_at:new Date(data.time_started_at).toISOString(),ended_at:new Date(data.time_ended_at).toISOString(),notes:data.time_notes.trim()||null});timeCreated=true;}result=await transitionMaintenanceOrder(order.id,"resolve",{});}
      else result=await transitionMaintenanceOrder(order.id,"cancel",{reason:data.reason.trim()});
      closeModal();await loadMaintenanceApiData();render();showToast(result.integration_status==="needs_reconciliation"?(en?"The operation still requires reconciliation.":"La operacion aun requiere conciliacion."):(resolving?(en?"Maintenance order resolved.":"Orden de mantenimiento resuelta."):(en?"Maintenance order cancelled.":"Orden de mantenimiento cancelada.")));
    }catch(error){renderFormErrors([...(timeCreated?[en?"Time was saved. Complete the remaining correction and try resolving again.":"El tiempo ya fue guardado. Corrige lo pendiente e intenta resolver nuevamente."]:[]),error.message||"Error"]);}
  });
}
function maintenanceLineMarkup(items,en){return `<div class="purchasing-requisition-line" data-maintenance-material-line><label class="preview-field purchasing-line-item"><span>${en?"Spare part":"Refaccion"}</span><select name="item_id" data-entity-selector required><option value="">${en?"Choose an item":"Selecciona un articulo"}</option>${items.map(item=>`<option value="${escapeAttribute(item.id)}" data-unit="${escapeAttribute(item.base_unit)}">${escapeHtml(item.code)} · ${escapeHtml(item.name)}</option>`).join("")}</select></label><label class="preview-field"><span>${en?"Quantity":"Cantidad"}</span><input name="quantity" type="number" min="0.000001" step="any" required></label><label class="preview-field"><span>${en?"Unit":"Unidad"}</span><input name="unit_code" readonly required></label><button class="secondary-action small-action" type="button" data-remove-maintenance-line>${en?"Remove":"Quitar"}</button></div>`;}
function maintenanceMaterialActions(order,en){return (order.material_requests||[]).map(request=>`<section class="maintenance-material-request"><div class="row-actions"><span class="chip ${request.status==="needs_reconciliation"?"danger":"warning"}">${escapeHtml(request.warehouse_name)} · ${maintenanceStatus(request.status)}</span>${request.status==="needs_reconciliation"&&request.pending_operation!=="issue"&&hasPermission("maintenance.material_request.reconcile")?`<button class="primary-action small-action" type="button" data-reconcile-maintenance-material="${escapeAttribute(request.id)}">${en?"Reconcile parts":"Conciliar refacciones"}</button>`:""}${["reserved","needs_reconciliation","cancelling"].includes(request.status)&&request.pending_operation!=="issue"&&hasPermission("maintenance.material_request.cancel")?`<button class="secondary-action small-action" type="button" data-cancel-maintenance-material="${escapeAttribute(request.id)}">${en?"Cancel parts":"Cancelar refacciones"}</button>`:""}</div><ul class="purchasing-line-summary">${(request.lines||[]).map(line=>`<li><span>${escapeHtml(line.item_code||"")} · ${escapeHtml(line.item_name||"")}</span><strong>${formatNumber(Number(line.quantity))} ${escapeHtml(line.unit_code)} · ${maintenanceStatus(line.line_status)}</strong></li>`).join("")}</ul></section>`).join("");}
function getMaintenanceFlowTitle(id){return state.lang==="en"?(id==="refacciones"?"Spare parts flow":"Corrective orders flow"):(id==="refacciones"?"Flujo de Refacciones":"Flujo de Ordenes correctivas");}
function getMaintenanceFlowSteps(id){const steps={es:{ordenes:[["Reporte","Describir la falla, el objetivo, la prioridad y la seguridad."],["Asignacion","Solicitar la orden y asignar un tecnico elegible de RH."],["Ejecucion","Registrar diagnostico, trabajo, tiempo y refacciones."],["Cierre","Verificar, conciliar y liberar sin reanudar Produccion automaticamente."]],refacciones:[["Orden","Partir de una orden asignada, en proceso o esperando refacciones."],["Almacen","Elegir un almacen activo de tipo Refacciones."],["Reserva","Solicitar partidas y cantidades; Inventario confirma la reserva."],["Conciliacion","Consumir, cancelar o reintentar sin duplicar movimientos."]]},en:{ordenes:[["Report","Describe the fault, target, priority, and safety considerations."],["Assign","Request the order and assign an eligible HR technician."],["Perform","Log diagnosis, work, time, and spare parts."],["Close","Verify, reconcile, and release without automatically resuming Production."]],refacciones:[["Order","Start from an assigned, in-progress, or waiting-for-parts order."],["Warehouse","Choose an active Spare parts warehouse."],["Reserve","Request lines and quantities; Inventory confirms the reservation."],["Reconcile","Consume, cancel, or retry without duplicating movements."]]}};return (steps[state.lang]?.[id]||steps.es[id]||steps.es.ordenes).map(([title,detail])=>({title,detail}));}
function renderMaintenanceSubmodulePanel(module){
  const api=state.maintenanceApi,en=state.lang==="en",id=state.activeSubmodule;
  const workerOptions=api.workers.map(item=>`<option value="${escapeAttribute(item.id)}">${escapeHtml(item.full_name)} · ${escapeHtml(item.position_name)}</option>`).join("");
  const cards=api.orders.map(order=>{const assignedWorkerOptions=api.workers.map(item=>`<option value="${escapeAttribute(item.id)}" ${item.id===order.assigned_worker_id?"selected":""}>${escapeHtml(item.full_name)} · ${escapeHtml(item.position_name)}</option>`).join("");return `<article class="catalog-card maintenance-order-card"><div class="maintenance-order-main"><span class="muted-label">${escapeHtml(order.code)} · ${escapeHtml(order.priority)}</span><strong>${escapeHtml(order.title)}</strong><p>${escapeHtml(order.machine_name_snapshot||order.location)}</p><div class="record-main"><span>${en?"Assigned technician":"Tecnico asignado"}</span><strong>${escapeHtml(order.assigned_worker_name||(en?"Unassigned":"Sin asignar"))}</strong></div></div><div class="maintenance-order-meta"><span class="chip ${order.status==="closed"?"active":"warning"}">${maintenanceStatus(order.status)}</span>${order.integration_status==="needs_reconciliation"?`<span class="chip danger">${maintenanceStatus(order.integration_status)}</span>`:""}<small>${order.total_minutes||0} min · ${(order.material_requests||[]).reduce((sum,request)=>sum+(request.lines?.length||0),0)} ${en?"parts":"refacciones"}</small></div>${hasPermission("maintenance.order.assign")&&["requested","assigned"].includes(order.status)?`<label class="preview-field maintenance-technician-field"><span>${order.status==="assigned"?(en?"Reassign technician":"Reasignar tecnico"):(en?"Technician":"Tecnico")}</span><select data-maintenance-worker-for="${escapeAttribute(order.id)}"><option value="">${en?"Choose a technician":"Selecciona un tecnico"}</option>${assignedWorkerOptions}</select></label>`:""}${maintenanceMaterialActions(order,en)}<div class="row-actions maintenance-order-actions">${["assigned","in_progress","waiting_parts"].includes(order.status)&&hasPermission("maintenance.time.create")?`<button class="secondary-action small-action" type="button" data-log-maintenance-time="${escapeAttribute(order.id)}">${en?"Log time":"Registrar tiempo"}</button>`:""}${["assigned","in_progress","waiting_parts"].includes(order.status)&&hasPermission("maintenance.material_request.create")?`<button class="primary-action small-action" type="button" data-request-maintenance-material="${escapeAttribute(order.id)}">${en?"Request spare parts":"Solicitar refacciones"}</button>`:""}${maintenanceTransitionButtons(order,en)}</div></article>`;}).join("");
  if(id==="ordenes"){
    const sourceOrder=api.productionOrders.find(item=>item.id===state.maintenanceSourceOrderId),sourceMachineId=sourceOrder?.resources?.find(item=>item.resource_type==="machine")?.resource_ref_id||"";const machines=api.machines.map(item=>`<option value="${escapeAttribute(item.id)}" ${item.id===sourceMachineId?"selected":""}>${escapeHtml(item.code)} · ${escapeHtml(item.name)}</option>`).join(""),productionOrders=api.productionOrders.map(item=>`<option value="${escapeAttribute(item.id)}" ${item.id===state.maintenanceSourceOrderId?"selected":""}>${escapeHtml(item.code)} · ${maintenanceStatus(item.status)}</option>`).join("");
    modulePanel.innerHTML=`<div class="panel-head"><div><p class="eyebrow">${en?"Maintenance / Operations":"Mantenimiento / Operacion"}</p><h2>${en?"Corrective orders":"Ordenes correctivas"}</h2></div><button class="secondary-action" data-action="back-module">${t("overview")}</button></div><div class="flow-guided-layout">${renderFlowGuide(getMaintenanceFlowTitle(id),getMaintenanceFlowSteps(id))}<section class="section-card"><form class="form-grid" id="maintenanceOrderForm"><label class="preview-field"><span>${en?"Code":"Folio"}</span><input name="code" required></label><label class="preview-field"><span>${en?"Target":"Objetivo"}</span><select name="target_type"><option value="facility">${en?"Facility":"Instalacion"}</option><option value="other">${en?"Other":"Otro"}</option><option value="production_machine">${en?"Production machine":"Maquina de Produccion"}</option></select></label><label class="preview-field"><span>${en?"Machine":"Maquina"}</span><select name="production_machine_id"><option value="">${en?"Not applicable":"No aplica"}</option>${machines}</select></label><label class="preview-field"><span>${en?"Production order (optional)":"Orden de Produccion (opcional)"}</span><select name="source_production_order_id"><option value="">${en?"Manual report":"Reporte manual"}</option>${productionOrders}</select></label><label class="preview-field"><span>${en?"Priority":"Prioridad"}</span><select name="priority"><option value="low">${en?"Low":"Baja"}</option><option value="medium" selected>${en?"Medium":"Media"}</option><option value="high">${en?"High":"Alta"}</option><option value="critical">${en?"Critical":"Critica"}</option></select></label><label class="preview-field"><span>${en?"Title":"Titulo"}</span><input name="title" maxlength="180" required></label><label class="preview-field wide-field"><span>${en?"Fault description":"Descripcion de la falla"}</span><textarea name="description" maxlength="4000" required></textarea></label><label class="preview-field"><span>${en?"Location":"Ubicacion"}</span><input name="location" maxlength="300" required></label><label class="preview-field"><span>${en?"Safety notes":"Notas de seguridad"}</span><input name="safety_notes" maxlength="2000"></label><div class="wide-field"><button class="primary-action" type="submit">${en?"Create order":"Crear orden"}</button></div></form></section><section class="section-card"><div class="catalog-grid">${cards||`<p>${en?"No maintenance orders yet.":"Aun no hay ordenes de mantenimiento."}</p>`}</div></section></div>`;
    if(!hasPermission("maintenance.order.create"))modulePanel.querySelector("#maintenanceOrderForm")?.closest(".section-card")?.remove();
    modulePanel.querySelector("#maintenanceOrderForm")?.addEventListener("submit",async event=>{event.preventDefault();const d=Object.fromEntries(new FormData(event.currentTarget));const machineId=d.production_machine_id||null,sourceId=d.source_production_order_id||null;try{await createMaintenanceOrder({...d,target_type:machineId?"production_machine":d.target_type,production_machine_id:machineId,source_type:sourceId?"production_order":"manual",source_production_order_id:sourceId,safety_notes:d.safety_notes||null});state.maintenanceSourceOrderId="";await loadMaintenanceApiData();render();showToast(en?"Maintenance order created.":"Orden de mantenimiento creada.");}catch(error){showToast(error.message||"Error");}});
  }else{
    const materialOrders=api.orders.filter(item=>["assigned","in_progress","waiting_parts"].includes(item.status)),orders=materialOrders.map(item=>`<option value="${escapeAttribute(item.id)}" ${item.id===state.maintenanceMaterialSourceOrderId?"selected":""}>${escapeHtml(item.code)} · ${escapeHtml(item.title)}</option>`).join(""),warehouses=api.warehouses.map(item=>`<option value="${escapeAttribute(item.id)}">${escapeHtml(item.code)} · ${escapeHtml(item.name)}</option>`).join("");
    const materialSetup=!materialOrders.length?`<p class="helper-copy">${en?"Assign a technician to an order before requesting parts.":"Asigna un tecnico a una orden antes de solicitar refacciones."}</p>`:!api.warehouses.length?`<div><p class="helper-copy">${en?"An active spare-parts warehouse is required. None exists in Inventory yet.":"Se necesita un almacen activo de tipo Refacciones. Aun no existe ninguno en Inventario."}</p><div class="row-actions">${hasPermission("inventory.warehouse.create")?`<button class="primary-action small-action" type="button" data-open-spare-parts-warehouse>${en?"Create spare-parts warehouse":"Crear almacen de refacciones"}</button>`:`<span class="chip warning">${en?"Ask the Inventory manager to create it.":"Solicita su alta al encargado de Inventario."}</span>`}</div></div>`:!api.items.length?`<div><p class="helper-copy">${en?"Create an active inventory item before requesting it.":"Crea primero un articulo activo en Inventario para poder solicitarlo."}</p>${hasPermission("inventory.item.create")?`<button class="primary-action small-action" type="button" data-open-spare-parts-items>${en?"Create inventory item":"Crear articulo"}</button>`:`<span class="chip warning">${en?"Ask the Inventory manager to create it.":"Solicita su alta al encargado de Inventario."}</span>`}</div>`:`<form class="form-grid" id="maintenanceMaterialForm"><label class="preview-field"><span>${en?"Order":"Orden"}</span><select name="order_id" required><option value="" ${state.maintenanceMaterialSourceOrderId?"":"selected"}>${en?"Choose":"Selecciona"}</option>${orders}</select></label><label class="preview-field"><span>${en?"Spare-parts warehouse":"Almacen de refacciones"}</span><select name="warehouse_id" required><option value="">${en?"Choose":"Selecciona"}</option>${warehouses}</select></label><div class="wide-field"><button class="secondary-action small-action" type="button" data-add-maintenance-line>${en?"Add part":"Agregar refaccion"}</button></div><div class="wide-field purchasing-requisition-lines" id="maintenanceMaterialLines">${maintenanceLineMarkup(api.items,en)}</div><div class="wide-field"><button class="primary-action" type="submit">${en?"Reserve parts":"Solicitar y reservar refacciones"}</button></div></form>`;
    modulePanel.innerHTML=`<div class="panel-head"><div><p class="eyebrow">${en?"Maintenance / Spare parts":"Mantenimiento / Refacciones"}</p><h2>${en?"Labor and spare parts":"Tiempos y refacciones"}</h2></div><button class="secondary-action" data-action="back-module">${t("overview")}</button></div><div class="flow-guided-layout">${renderFlowGuide(getMaintenanceFlowTitle(id),getMaintenanceFlowSteps(id))}<section class="section-card"><h3>${en?"Log labor time":"Registrar tiempo"}</h3><form class="form-grid" id="maintenanceTimeForm"><label class="preview-field"><span>${en?"Order":"Orden"}</span><select name="order_id" required><option value="">${en?"Choose":"Selecciona"}</option>${orders}</select></label><label class="preview-field"><span>${en?"Technician":"Tecnico"}</span><select name="worker_id" required><option value="">${en?"Choose":"Selecciona"}</option>${workerOptions}</select></label><label class="preview-field"><span>${en?"Start":"Inicio"}</span><input name="started_at" type="datetime-local" required></label><label class="preview-field"><span>${en?"End":"Fin"}</span><input name="ended_at" type="datetime-local" required></label><label class="preview-field wide-field"><span>${en?"Notes":"Notas"}</span><input name="notes" maxlength="1000"></label><div class="wide-field"><button class="primary-action" type="submit">${en?"Save time":"Guardar tiempo"}</button></div></form></section><section class="section-card"><h3>${en?"Request spare parts":"Solicitar refacciones"}</h3>${materialSetup}</section><section class="section-card"><div class="catalog-grid">${cards}</div></section></div>`;
    if(!hasPermission("maintenance.time.create"))modulePanel.querySelector("#maintenanceTimeForm")?.closest(".section-card")?.remove();
    if(!hasPermission("maintenance.material_request.create"))modulePanel.querySelector("#maintenanceMaterialForm")?.closest(".section-card")?.remove();
    modulePanel.querySelector("#maintenanceTimeForm")?.addEventListener("submit",async event=>{event.preventDefault();const d=Object.fromEntries(new FormData(event.currentTarget));try{await createMaintenanceTime(d.order_id,{worker_id:d.worker_id,started_at:new Date(d.started_at).toISOString(),ended_at:new Date(d.ended_at).toISOString(),notes:d.notes||null});await loadMaintenanceApiData();render();showToast(en?"Time saved.":"Tiempo guardado.");}catch(error){showToast(error.message||"Error");}});
    const lineContainer=modulePanel.querySelector("#maintenanceMaterialLines");modulePanel.querySelector("[data-add-maintenance-line]")?.addEventListener("click",()=>lineContainer?.insertAdjacentHTML("beforeend",maintenanceLineMarkup(api.items,en)));modulePanel.addEventListener("change",event=>{if(event.target.name==="item_id"){const row=event.target.closest("[data-maintenance-material-line]");row.querySelector('[name="unit_code"]').value=event.target.selectedOptions[0]?.dataset.unit||"";}});modulePanel.addEventListener("click",event=>{const button=event.target.closest("[data-remove-maintenance-line]");if(button&&lineContainer?.querySelectorAll("[data-maintenance-material-line]").length>1)button.closest("[data-maintenance-material-line]").remove();});modulePanel.querySelector("[data-open-spare-parts-warehouse]")?.addEventListener("click",()=>{const inventoryModule=modules.find(item=>item.id==="almacenes"),submodule=getGenericSubmodule(inventoryModule,"almacenes");navigateTo({active:"almacenes",activeSubmodule:"almacenes",laborArea:""});openWarehouseModal(inventoryModule,submodule,null,{type:"spare_parts"});});modulePanel.querySelector("[data-open-spare-parts-items]")?.addEventListener("click",()=>{const inventoryModule=modules.find(item=>item.id==="almacenes"),submodule=getGenericSubmodule(inventoryModule,"articulos");navigateTo({active:"almacenes",activeSubmodule:"articulos",laborArea:""});openInventoryItemModal(inventoryModule,submodule,null,{type:"sparePart"});});modulePanel.querySelector("#maintenanceMaterialForm")?.addEventListener("submit",async event=>{event.preventDefault();const form=event.currentTarget,d=Object.fromEntries(new FormData(form)),lines=[...form.querySelectorAll("[data-maintenance-material-line]")].map(row=>({item_id:row.querySelector('[name="item_id"]').value,quantity:Number(row.querySelector('[name="quantity"]').value),unit_code:row.querySelector('[name="unit_code"]').value}));try{const request=await createMaintenanceMaterialRequest(d.order_id,{warehouse_id:d.warehouse_id,lines});state.maintenanceMaterialSourceOrderId="";await loadMaintenanceApiData();render();showToast(request.status==="needs_reconciliation"?(en?"Some parts require reconciliation.":"Algunas refacciones requieren conciliacion."):(en?"Spare parts requested and reserved.":"Refacciones solicitadas y reservadas."));}catch(error){showToast(error.message||"Error");}});
  }
  modulePanel.querySelector("[data-action='back-module']")?.addEventListener("click",()=>navigateTo({active:"mantenimiento",activeSubmodule:null,laborArea:""}));
  modulePanel.querySelectorAll("[data-request-maintenance-material]").forEach(button=>button.addEventListener("click",()=>{state.maintenanceMaterialSourceOrderId=button.dataset.requestMaintenanceMaterial;navigateTo({active:"mantenimiento",activeSubmodule:"refacciones",laborArea:""});}));
  modulePanel.querySelectorAll("[data-log-maintenance-time]").forEach(button=>button.addEventListener("click",()=>{const order=api.orders.find(item=>item.id===button.dataset.logMaintenanceTime);if(order)openMaintenanceTimeModal(order,en);}));
  modulePanel.querySelectorAll("[data-maintenance-transition]").forEach(button=>button.addEventListener("click",async()=>{const order=api.orders.find(item=>item.id===button.dataset.orderId),action=button.dataset.maintenanceTransition;if(["resolve","cancel"].includes(action)){openMaintenanceActionModal(order,action,en);return;}let extra={};if(action==="assign"){const workerId=modulePanel.querySelector(`[data-maintenance-worker-for="${CSS.escape(order.id)}"]`)?.value;if(!workerId){showToast(en?"Choose a maintenance technician.":"Selecciona un técnico de mantenimiento.","warning");return;}extra.assigned_worker_id=workerId;}try{const result=action==="reconcile"?await reconcileMaintenanceOrder(order.id):await transitionMaintenanceOrder(order.id,action,extra);await loadMaintenanceApiData();render();if(action==="assign"){showToast(en?`Technician assigned: ${result.assigned_worker_name}`:`Técnico asignado: ${result.assigned_worker_name}`,"success");return;}showToast(result.integration_status==="needs_reconciliation"?(en?"The operation still requires reconciliation.":"La operación aún requiere conciliación."):(en?"Maintenance status updated.":"Estado de mantenimiento actualizado."),result.integration_status==="needs_reconciliation"?"warning":"success");}catch(error){showApiError(error,en?"The maintenance status could not be updated.":"No se pudo actualizar el estado de mantenimiento.");}}));
  modulePanel.querySelectorAll("[data-reconcile-maintenance-material]").forEach(button=>button.addEventListener("click",async()=>{try{const result=await reconcileMaintenanceMaterialRequest(button.dataset.reconcileMaintenanceMaterial);await loadMaintenanceApiData();render();showToast(result.status==="needs_reconciliation"?(en?"Parts still require reconciliation.":"Las refacciones aún requieren conciliación."):(en?"Parts reconciled.":"Refacciones conciliadas."),result.status==="needs_reconciliation"?"warning":"success");}catch(error){showApiError(error,en?"The spare-parts request could not be reconciled.":"No se pudo conciliar la solicitud de refacciones.");}}));
  modulePanel.querySelectorAll("[data-cancel-maintenance-material]").forEach(button=>button.addEventListener("click",async()=>{try{const result=await cancelMaintenanceMaterialRequest(button.dataset.cancelMaintenanceMaterial);await loadMaintenanceApiData();render();showToast(result.status==="needs_reconciliation"?(en?"Cancellation requires reconciliation.":"La cancelación requiere conciliación."):(en?"Parts request cancelled.":"Solicitud de refacciones cancelada."),result.status==="needs_reconciliation"?"warning":"success");}catch(error){showApiError(error,en?"The spare-parts request could not be cancelled.":"No se pudo cancelar la solicitud de refacciones.");}}));
}

function purchasingStatus(value){const map={draft:["Borrador","Draft"],submitted:["Enviada","Submitted"],approved:["Aprobada","Approved"],rejected:["Rechazada","Rejected"],converted:["Convertida","Converted"],issued:["Emitida","Issued"],partially_received:["Recepcion parcial","Partially received"],received:["Recibida","Received"],closed:["Cerrada","Closed"],cancelled:["Cancelada","Cancelled"],processing:["Procesando","Processing"],completed:["Completada","Completed"],needs_reconciliation:["Requiere conciliacion","Needs reconciliation"],active:["Activo","Active"],inactive:["Inactivo","Inactive"]};return (map[value]||[value,value])[state.lang==="en"?1:0];}
function openPurchasingCancellationModal(documentType, documentId) {
  const isRequisition = documentType === "requisition";
  const document = (isRequisition ? state.purchasingApi.requisitions : state.purchasingApi.orders).find((item) => item.id === documentId);
  if (!document) {
    showToast(t("purchasingCancellationDocumentMissing"));
    return;
  }
  modalContent.innerHTML = `
    <form class="recipe-form" id="purchasingCancellationForm">
      <div class="modal-head">
        <div>
          <p class="eyebrow">${t("purchasingCancellationEyebrow")}</p>
          <h2 id="modalTitle">${t(isRequisition ? "cancelRequisitionTitle" : "cancelPurchaseOrderTitle")}</h2>
          <p class="helper-copy">${escapeHtml(document.code)}</p>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>
      <p class="helper-copy">${t("purchasingCancellationHelp")}</p>
      <label class="preview-field">
        <span>${t("cancellationReason")}</span>
        <textarea name="reason" rows="4" maxlength="1000" required></textarea>
        <small>${t("purchasingCancellationReasonHelp")}</small>
      </label>
      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-purchasing-cancellation">${t("cancel")}</button>
        <button class="primary-action" type="submit">${t("confirmCancellation")}</button>
      </div>
    </form>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close")?.addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-purchasing-cancellation']")?.addEventListener("click", closeModal);
  modalContent.querySelector("#purchasingCancellationForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const reason = new FormData(event.currentTarget).get("reason")?.trim() || "";
    if (!reason) {
      renderFormErrors([t("cancellationReasonRequired")]);
      return;
    }
    try {
      if (isRequisition) {
        await cancelPurchasingRequisition(documentId, reason);
        state.purchasingRequisitionEditId = "";
      } else {
        await cancelPurchasingOrder(documentId, reason);
        state.purchasingOrderEditId = "";
      }
      closeModal();
      await loadPurchasingApiData();
      showToast(t(isRequisition ? "requisitionCancelled" : "purchaseOrderCancelled"));
    } catch (error) {
      renderFormErrors([userFacingError(error, t("purchasingCancellationFailed"))]);
    }
  });
}
function getPurchasingFlowTitle(title){return state.lang==="en"?`${title} flow`:`Flujo de ${title}`;}
function getPurchasingFlowSteps(id){const steps={es:{proveedores:[["Alta","Registrar perfil comercial, contacto y condiciones."],["Fiscal","Completar razon social, RFC, regimen, correo y codigo postal fiscal."],["Validacion","Revisar moneda, condiciones, plazo y estatus."],["Operacion","Usarlo en ordenes y seguimiento de compras."]],requisiciones:[["Necesidad","Consolidar partidas y fecha requerida."],["Envio","Enviar el borrador para revision."],["Autorizacion","Aprobar, rechazar o cancelar con permiso puntual."],["Conversion","Convertir la requisicion aprobada en orden de compra."]],"ordenes-de-compra":[["Origen","Seleccionar una requisicion aprobada pendiente."],["Proveedor y precio","Elegir proveedor y precio para cada partida."],["Emision","Congelar condiciones y emitir la orden."],["Recepcion","Continuar con la recepcion parcial o total."]],recepciones:[["Orden","Seleccionar una orden emitida con saldo pendiente."],["Partidas","Capturar cantidades y almacenes destino."],["Validacion","Evitar sobre-recepcion y validar referencias de Inventario."],["Conciliacion","Crear entradas o reintentar pendientes sin duplicarlas."]],reabastecimiento:[["Senales","Considerar minimos, reorden, demanda y ordenes abiertas."],["Evaluacion","Cruzar faltantes y tiempo de entrega del proveedor."],["Sugerencia","Preparar una recomendacion futura de compra."],["Decision","Crear una requisicion explicita cuando el flujo sea implementado."]]},en:{proveedores:[["Create","Register commercial profile, contact, and terms."],["Tax profile","Complete legal name, tax ID, regime, billing email, and postal code."],["Validate","Review currency, terms, lead time, and status."],["Operate","Use the supplier in orders and purchasing follow-up."]],requisiciones:[["Need","Consolidate lines and required date."],["Submit","Send the draft for review."],["Authorize","Approve, reject, or cancel with a specific permission."],["Convert","Convert the approved requisition into a purchase order."]],"ordenes-de-compra":[["Source","Select a pending approved requisition."],["Supplier and price","Choose the supplier and price for each line."],["Issue","Freeze terms and issue the order."],["Receive","Continue with a partial or full receipt."]],recepciones:[["Order","Select an issued order with an open balance."],["Lines","Capture quantities and destination warehouses."],["Validate","Prevent over-receipt and validate Inventory references."],["Reconcile","Create entries or retry pending work without duplicates."]],reabastecimiento:[["Signals","Consider minimums, reorder points, demand, and open orders."],["Evaluate","Cross-check shortages and supplier lead time."],["Suggest","Prepare a future purchasing recommendation."],["Decide","Create an explicit requisition once the flow is implemented."]]}};return (steps[state.lang]?.[id]||steps.es[id]||steps.es.proveedores).map(([title,detail])=>({title,detail}));}
function purchasingShell(module,title,help,content,form="",contentFirst=false) { const id=state.activeSubmodule,label=state.lang==="en"?module.titleEn:module.title,list=`<section class="section-card purchasing-records"><div class="catalog-grid">${content||`<p class="helper-copy">${state.lang==="en"?"No records yet.":"Aun no hay registros."}</p>`}</div></section>`;modulePanel.innerHTML=`<div class="panel-head"><div><p class="eyebrow">${escapeHtml(label)} / ${state.lang==="en"?"Operations":"Operacion"}</p><h2>${escapeHtml(title)}</h2></div><button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button></div><section class="submodule-screen"><div class="submodule-screen-head"><div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(help)}</p></div></div><div class="flow-guided-layout">${renderFlowGuide(getPurchasingFlowTitle(title),getPurchasingFlowSteps(id))}${contentFirst?`${list}${form}`:`${form}${list}`}</div></section>`;modulePanel.querySelector("[data-action='back-module']")?.addEventListener("click",()=>navigateTo({active:"compras",activeSubmodule:null,laborArea:""})); }
function purchasingForm(id,fields,button){return `<section class="section-card"><form class="form-grid" id="${id}">${fields}<div class="wide-field inline-actions"><button class="primary-action" type="submit">${escapeHtml(button)}</button></div></form></section>`;}

function renderPurchasingSuppliersPanel(module){
  const api=state.purchasingApi,en=state.lang==="en";
  const editing=api.suppliers.find(item=>item.id===state.purchasingSupplierEditId)||null;
  const value=name=>escapeAttribute(editing?.[name]??"");
  const cards=api.suppliers.map(item=>`<article class="catalog-card">
    <span class="muted-label">${escapeHtml(item.code)} &middot; ${escapeHtml(item.tax_id||(en?"Fiscal profile pending":"Perfil fiscal pendiente"))}</span>
    <strong>${escapeHtml(item.commercial_name)}</strong>
    <p>${escapeHtml(item.legal_name||"")}${item.tax_regime?` &middot; ${en?"Tax regime":"Regimen"} ${escapeHtml(item.tax_regime)}`:""}</p>
    <p>${escapeHtml(item.billing_email||item.email||"")} &middot; ${escapeHtml(item.currency)} &middot; ${escapeHtml(item.payment_terms)} &middot; ${item.lead_time_days} ${en?"days":"dias"}</p>
    <span class="chip ${item.status==="active"?"active":"warning"}">${purchasingStatus(item.status)}</span>
    ${hasPermission("purchasing.supplier.update")?`<button class="secondary-action small-action" type="button" data-edit-supplier="${escapeAttribute(item.id)}">${en?"Edit supplier":"Editar proveedor"}</button>`:""}
  </article>`).join("");
  const fields=`
    <div class="section-title form-section-title wide-field"><span class="section-icon">F</span><strong>${editing?(en?"Edit supplier":"Editar proveedor"):(en?"New supplier":"Nuevo proveedor")}</strong></div>
    <label class="preview-field"><span>${en?"Code":"Codigo"}</span><input name="code" required maxlength="40" value="${value("code")}" ${editing?"readonly":""}></label>
    <label class="preview-field"><span>${en?"Commercial name":"Nombre comercial"}</span><input name="commercial_name" required maxlength="240" value="${value("commercial_name")}"></label>
    <label class="preview-field"><span>${en?"Legal name":"Razon social"}</span><input name="legal_name" required maxlength="240" value="${value("legal_name")}"></label>
    <label class="preview-field"><span>RFC</span><input name="tax_id" required maxlength="13" pattern="[A-Za-z&#209;&#241;&amp;]{3,4}[0-9]{6}[A-Za-z0-9]{3}" value="${value("tax_id")}" placeholder="AAA010101AAA"></label>
    <label class="preview-field"><span>${en?"Tax regime":"Regimen fiscal"}</span><select name="tax_regime" required>
      <option value="601" ${selectedOption(editing?.tax_regime,"601")}>601 &middot; ${en?"General legal entities":"General de Ley Personas Morales"}</option>
      <option value="603" ${selectedOption(editing?.tax_regime,"603")}>603 &middot; ${en?"Nonprofit legal entities":"Personas Morales con Fines no Lucrativos"}</option>
      <option value="605" ${selectedOption(editing?.tax_regime,"605")}>605 &middot; ${en?"Wages and salaries":"Sueldos y Salarios"}</option>
      <option value="606" ${selectedOption(editing?.tax_regime,"606")}>606 &middot; ${en?"Leasing":"Arrendamiento"}</option>
      <option value="612" ${selectedOption(editing?.tax_regime,"612")}>612 &middot; ${en?"Business and professional activities":"Actividades Empresariales y Profesionales"}</option>
      <option value="616" ${selectedOption(editing?.tax_regime,"616")}>616 &middot; ${en?"No tax obligations":"Sin obligaciones fiscales"}</option>
      <option value="626" ${selectedOption(editing?.tax_regime,"626")}>626 &middot; RESICO</option>
    </select></label>
    <label class="preview-field"><span>${en?"Billing email":"Correo de facturacion"}</span><input name="billing_email" type="email" required maxlength="254" value="${value("billing_email")}"></label>
    <label class="preview-field"><span>${en?"Fiscal postal code":"Codigo postal fiscal"}</span><input name="fiscal_postal_code" required inputmode="numeric" pattern="[0-9]{5}" maxlength="5" value="${value("fiscal_postal_code")}"></label>
    <label class="preview-field"><span>${en?"Fiscal country":"Pais fiscal"}</span><select name="fiscal_country"><option value="MX">Mexico</option></select></label>
    <label class="preview-field wide-field"><span>${en?"Fiscal street":"Calle fiscal"}</span><input name="fiscal_street" maxlength="200" value="${value("fiscal_street")}"></label>
    <label class="preview-field"><span>${en?"Exterior number":"Numero exterior"}</span><input name="fiscal_exterior_number" maxlength="40" value="${value("fiscal_exterior_number")}"></label>
    <label class="preview-field"><span>${en?"Interior number":"Numero interior"}</span><input name="fiscal_interior_number" maxlength="40" value="${value("fiscal_interior_number")}"></label>
    <label class="preview-field"><span>${en?"Neighborhood":"Colonia"}</span><input name="fiscal_neighborhood" maxlength="160" value="${value("fiscal_neighborhood")}"></label>
    <label class="preview-field"><span>${en?"Municipality":"Municipio o alcaldia"}</span><input name="fiscal_municipality" maxlength="160" value="${value("fiscal_municipality")}"></label>
    <label class="preview-field"><span>${en?"State":"Estado"}</span><input name="fiscal_state" maxlength="120" value="${value("fiscal_state")}"></label>
    <div class="section-title form-section-title wide-field"><span class="section-icon">C</span><strong>${en?"Commercial contact":"Contacto comercial"}</strong></div>
    <label class="preview-field"><span>${en?"Contact name":"Nombre de contacto"}</span><input name="contact_name" maxlength="200" value="${value("contact_name")}"></label>
    <label class="preview-field"><span>${en?"Contact email":"Correo de contacto"}</span><input name="email" type="email" maxlength="254" value="${value("email")}"></label>
    <label class="preview-field"><span>${en?"Phone":"Telefono"}</span><input name="phone" maxlength="30" value="${value("phone")}"></label>
    <label class="preview-field"><span>${en?"Website":"Sitio web"}</span><input name="website" type="url" maxlength="300" value="${value("website")}"></label>
    <label class="preview-field"><span>${en?"Currency":"Moneda"}</span><select name="currency"><option ${selectedOption(editing?.currency||"MXN","MXN")}>MXN</option><option ${selectedOption(editing?.currency,"USD")}>USD</option><option ${selectedOption(editing?.currency,"EUR")}>EUR</option></select></label>
    <label class="preview-field"><span>${en?"Payment terms":"Condiciones de pago"}</span><select name="payment_terms"><option value="cash" ${selectedOption(editing?.payment_terms||"cash","cash")}>${en?"Cash":"Contado"}</option><option value="credit_30" ${selectedOption(editing?.payment_terms,"credit_30")}>${en?"Net 30":"Credito 30 dias"}</option></select></label>
    <label class="preview-field"><span>${en?"Lead time (days)":"Entrega (dias)"}</span><input name="lead_time_days" type="number" min="0" value="${editing?.lead_time_days??0}"></label>
    <label class="preview-field"><span>${en?"Status":"Estatus"}</span><select name="status"><option value="active" ${selectedOption(editing?.status||"active","active")}>${en?"Active":"Activo"}</option><option value="inactive" ${selectedOption(editing?.status,"inactive")}>${en?"Inactive":"Inactivo"}</option></select></label>
    ${editing?`<button class="secondary-action wide-field" type="button" data-cancel-supplier-edit>${en?"Cancel editing":"Cancelar edicion"}</button>`:""}`;
  const form=purchasingForm("purchasingSupplierForm",fields,editing?(en?"Update supplier":"Actualizar proveedor"):(en?"Save supplier":"Guardar proveedor"));
  purchasingShell(module,en?"Suppliers":"Proveedores",en?"Fiscal identity, commercial contacts and delivery terms.":"Identidad fiscal, contactos comerciales y condiciones de entrega.",cards,form);
  if(!hasPermission(editing?"purchasing.supplier.update":"purchasing.supplier.create"))modulePanel.querySelector("#purchasingSupplierForm")?.closest(".section-card")?.remove();
  modulePanel.querySelectorAll("[data-edit-supplier]").forEach(button=>button.addEventListener("click",()=>{state.purchasingSupplierEditId=button.dataset.editSupplier;render();modulePanel.querySelector("#purchasingSupplierForm")?.scrollIntoView({behavior:"smooth",block:"start"});}));
  modulePanel.querySelector("[data-cancel-supplier-edit]")?.addEventListener("click",()=>{state.purchasingSupplierEditId="";render();});
  modulePanel.querySelector("#purchasingSupplierForm")?.addEventListener("submit",async event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.currentTarget));const payload={...data,tax_id:data.tax_id.toUpperCase().replaceAll("-","").replaceAll(" ",""),lead_time_days:Number(data.lead_time_days)};try{if(editing){delete payload.code;await updatePurchasingSupplier(editing.id,payload);}else await createPurchasingSupplier(payload);state.purchasingSupplierEditId="";await loadPurchasingApiData();showToast(editing?(en?"Supplier updated.":"Proveedor actualizado."):(en?"Supplier saved.":"Proveedor guardado."));}catch(error){showToast(error.message||"Error");}});
}

function purchasingRequisitionLineMarkup(items,en,line={}){
  const options=items.map(item=>`<option value="${escapeAttribute(item.id)}" data-unit="${escapeAttribute(item.base_unit)}" ${selectedOption(line.inventory_item_id,item.id)}>${escapeHtml(item.code)} &middot; ${escapeHtml(item.name)} (${escapeHtml(item.base_unit)})</option>`).join("");
  return `<div class="purchasing-requisition-line" data-requisition-line>
    <label class="preview-field purchasing-line-item"><span>${en?"Inventory item":"Articulo"}</span><select data-entity-selector data-search-placeholder="${en?"Search item by code or name":"Buscar articulo por codigo o nombre"}" name="inventory_item_id" required><option value="" disabled ${line.inventory_item_id?"":"selected"}>${en?"Choose an item":"Selecciona un articulo"}</option>${options}</select></label>
    <label class="preview-field"><span>${en?"Quantity":"Cantidad"}</span><input name="quantity" type="number" min="0.000001" step="any" value="${escapeAttribute(line.quantity??"")}" required></label>
    <label class="preview-field purchasing-line-description"><span>${en?"Description":"Descripcion"}</span><input name="description" maxlength="300" value="${escapeAttribute(line.description??"")}" required></label>
    <label class="preview-field purchasing-line-unit"><span>${en?"Unit":"Unidad"}</span><input name="unit_code" value="${escapeAttribute(line.unit_code??"")}" readonly required></label>
    <button class="secondary-action small-action remove-resource" type="button" data-remove-requisition-line aria-label="${en?"Remove line":"Quitar partida"}">${en?"Remove":"Quitar"}</button>
  </div>`;
}

function renderPurchasingSubmodulePanel(module){
  const api=state.purchasingApi; const id=state.activeSubmodule; const en=state.lang==="en";
  if(id==="proveedores"){
    renderPurchasingSuppliersPanel(module);return;
  }
  if(id==="requisiciones"){
    const editing=api.requisitions.find(x=>x.id===state.purchasingRequisitionEditId)||null;
    const cards=api.requisitions.map(x=>`<article class="catalog-card"><span class="muted-label">${escapeHtml(x.code)} &middot; ${escapeHtml(x.required_date)}</span><strong>${x.lines?.length||0} ${en?"lines":"partidas"}</strong><ul class="purchasing-line-summary">${(x.lines||[]).map(line=>`<li><span>${escapeHtml(line.description)}</span><strong>${formatNumber(Number(line.quantity))} ${escapeHtml(line.unit_code)}</strong></li>`).join("")}</ul><p>${escapeHtml(x.priority)}</p><span class="chip ${x.status==="approved"?"active":"warning"}">${purchasingStatus(x.status)}</span><div class="row-actions">${x.status==="draft"&&hasPermission("purchasing.requisition.update")?`<button class="secondary-action small-action" data-edit-requisition="${escapeAttribute(x.id)}">${en?"Edit":"Editar"}</button>`:""}${x.status==="draft"&&hasPermission("purchasing.requisition.submit")?`<button class="secondary-action small-action" data-purchasing-transition="submit" data-id="${escapeAttribute(x.id)}">${en?"Submit":"Enviar"}</button>`:""}${x.status==="submitted"&&hasPermission("purchasing.requisition.approve")?`<button class="primary-action small-action" data-purchasing-transition="approve" data-id="${escapeAttribute(x.id)}">${en?"Approve":"Aprobar"}</button>`:""}${x.status==="submitted"&&hasPermission("purchasing.requisition.reject")?`<button class="secondary-action small-action" data-purchasing-transition="reject" data-id="${escapeAttribute(x.id)}">${en?"Reject":"Rechazar"}</button>`:""}${x.status==="approved"&&hasPermission("purchasing.order.create")?`<button class="primary-action small-action" data-create-order-from-requisition="${escapeAttribute(x.id)}">${en?"Create purchase order":"Crear orden de compra"}</button>`:""}${["draft","submitted","approved"].includes(x.status)&&hasPermission("purchasing.requisition.cancel")?`<button class="secondary-action small-action" data-cancel-requisition="${escapeAttribute(x.id)}">${en?"Cancel":"Cancelar"}</button>`:""}</div></article>`).join("");
    const today=new Date().toISOString().slice(0,10),editLines=(editing?.lines||[]).map(line=>({...line,inventory_item_id:line.inventory_item_ref_id}));const form=purchasingForm("purchasingRequisitionForm",`<label class="preview-field"><span>${en?"Code":"Codigo"}</span><input name="code" value="${escapeAttribute(editing?.code||"")}" required></label><label class="preview-field"><span>${en?"Required date":"Fecha requerida"}</span><input name="required_date" type="date" min="${today}" value="${escapeAttribute(editing?.required_date||today)}" required></label><label class="preview-field"><span>${en?"Priority":"Prioridad"}</span><select name="priority"><option value="normal" ${editing?.priority==="normal"?"selected":""}>Normal</option><option value="urgent" ${editing?.priority==="urgent"?"selected":""}>${en?"Urgent":"Urgente"}</option></select></label><div class="wide-field purchasing-lines-head"><div><strong>${en?"Requested items":"Articulos solicitados"}</strong><p>${en?"Add every item needed under the same requisition.":"Agrega todos los articulos necesarios en la misma requisicion."}</p></div><button class="secondary-action small-action" type="button" data-add-requisition-line>${en?"Add item":"Agregar articulo"}</button></div><div class="wide-field purchasing-requisition-lines" id="purchasingRequisitionLines">${(editLines.length?editLines:[{}]).map(line=>purchasingRequisitionLineMarkup(api.items,en,line)).join("")}</div>${editing?`<div class="wide-field"><button class="secondary-action" type="button" data-cancel-requisition-edit>${en?"Discard edit":"Descartar edicion"}</button></div>`:""}`,editing?(en?"Update requisition":"Actualizar requisicion"):(en?"Create requisition":"Crear requisicion"));
    purchasingShell(module,en?"Requisitions":"Requisiciones",en?"Request, submit and approve purchasing needs.":"Solicita, envia y aprueba necesidades de compra.",cards,form);
    if(!hasPermission(editing?"purchasing.requisition.update":"purchasing.requisition.create"))modulePanel.querySelector("#purchasingRequisitionForm")?.closest(".section-card")?.remove();
    const requisitionForm=modulePanel.querySelector("#purchasingRequisitionForm"),lineContainer=modulePanel.querySelector("#purchasingRequisitionLines");
    modulePanel.querySelector("[data-add-requisition-line]")?.addEventListener("click",()=>lineContainer.insertAdjacentHTML("beforeend",purchasingRequisitionLineMarkup(api.items,en)));
    lineContainer?.addEventListener("click",event=>{const button=event.target.closest("[data-remove-requisition-line]");if(!button)return;const rows=lineContainer.querySelectorAll("[data-requisition-line]");if(rows.length===1){showToast(en?"A requisition needs at least one line.":"La requisicion necesita al menos una partida.");return;}button.closest("[data-requisition-line]")?.remove();});
    lineContainer?.addEventListener("change",event=>{const select=event.target.closest('select[name="inventory_item_id"]');if(!select)return;const row=select.closest("[data-requisition-line]"),item=api.items.find(value=>value.id===select.value);if(!row||!item)return;row.querySelector('[name="unit_code"]').value=item.base_unit;const description=row.querySelector('[name="description"]');if(!description.value.trim())description.value=item.name;});
    requisitionForm?.addEventListener("submit",async event=>{event.preventDefault();const f=event.currentTarget,d=Object.fromEntries(new FormData(f));const lines=[...f.querySelectorAll("[data-requisition-line]")].map(row=>({line_type:"inventory_item",inventory_item_id:row.querySelector('[name="inventory_item_id"]').value,description:row.querySelector('[name="description"]').value.trim(),quantity:Number(row.querySelector('[name="quantity"]').value),unit_code:row.querySelector('[name="unit_code"]').value}));if(new Set(lines.map(line=>line.inventory_item_id)).size!==lines.length){showToast(en?"The same item cannot be repeated; adjust its quantity in one line.":"No se puede repetir el mismo articulo; ajusta su cantidad en una sola partida.");return;}try{const payload={code:d.code,required_date:d.required_date,priority:d.priority,source_type:"manual",lines};if(editing)await updatePurchasingRequisition(editing.id,payload);else await createPurchasingRequisition(payload);state.purchasingRequisitionEditId="";await loadPurchasingApiData();showToast(editing?(en?"Requisition updated.":"Requisicion actualizada."):(en?`${lines.length} requisition lines created.`:`Requisicion creada con ${lines.length} partidas.`));}catch(error){showToast(error.message||"Error");}});
    modulePanel.querySelectorAll("[data-edit-requisition]").forEach(button=>button.addEventListener("click",()=>{state.purchasingRequisitionEditId=button.dataset.editRequisition;render();}));
    modulePanel.querySelector("[data-cancel-requisition-edit]")?.addEventListener("click",()=>{state.purchasingRequisitionEditId="";render();});
    modulePanel.querySelectorAll("[data-cancel-requisition]").forEach(button=>button.addEventListener("click",()=>openPurchasingCancellationModal("requisition",button.dataset.cancelRequisition)));
    modulePanel.querySelectorAll("[data-create-order-from-requisition]").forEach(button=>button.addEventListener("click",()=>{state.purchasingOrderSourceRequisitionId=button.dataset.createOrderFromRequisition;state.purchasingOrderEditId="";navigateTo({active:"compras",activeSubmodule:"ordenes-de-compra",laborArea:""});}));
    modulePanel.querySelectorAll("[data-purchasing-transition]").forEach(button=>button.addEventListener("click",async()=>{try{const action=button.dataset.purchasingTransition;await transitionPurchasingRequisition(button.dataset.id,action,action==="reject"?(en?"Rejected by buyer":"Rechazada por comprador"):null);await loadPurchasingApiData();if(action==="approve"&&hasPermission("purchasing.order.create")){state.purchasingOrderSourceRequisitionId=button.dataset.id;navigateTo({active:"compras",activeSubmodule:"ordenes-de-compra",laborArea:""});showToast(en?"Requisition approved. Complete supplier and prices to create the order.":"Requisición aprobada. Completa proveedor y precios para crear la orden.","success");return;}showToast(en?"Status updated.":"Estado actualizado.","success");}catch(error){showApiError(error,en?"The requisition status could not be updated.":"No se pudo actualizar el estado de la requisición.");}}));return;
  }
  if(id==="ordenes-de-compra"){
    const editing=api.orders.find(x=>x.id===state.purchasingOrderEditId)||null;
    const pendingRequisitions=api.requisitions.filter(x=>x.status==="approved"),sourceRequisitionId=editing?.requisition_id||state.purchasingOrderSourceRequisitionId||"";
    const cards=`<div class="purchasing-lines-head"><div><strong>${en?`All purchase orders (${api.orders.length})`:`Todas las ordenes de compra (${api.orders.length})`}</strong><p>${en?"Every status is included: draft, issued, partial, received, closed, or cancelled.":"Se incluyen todos los estatus: borrador, emitida, parcial, recibida, cerrada o cancelada."}</p></div></div>`+(api.orders.map(x=>{const requisition=api.requisitions.find(item=>item.id===x.requisition_id);return `<article class="catalog-card"><span class="muted-label">${escapeHtml(x.code)} · ${x.created_at?new Date(x.created_at).toLocaleDateString():""}</span><strong>${escapeHtml(x.supplier_name_snapshot)}</strong><p>${formatCurrency(x.subtotal)} · ${x.lines?.length||0} ${en?"lines":"partidas"}</p><p>${en?"Origin":"Origen"}: ${escapeHtml(requisition?.code||(x.direct_purchase_reason?(en?"Direct purchase":"Compra directa"):(en?"No requisition":"Sin requisicion")))}</p><span class="chip ${["received","closed"].includes(x.status)?"active":"warning"}">${purchasingStatus(x.status)}</span><div class="row-actions">${x.status==="draft"&&hasPermission("purchasing.order.update")?`<button class="secondary-action small-action" data-edit-order="${escapeAttribute(x.id)}">${en?"Edit":"Editar"}</button>`:""}${x.status==="draft"&&hasPermission("purchasing.order.issue")?`<button class="primary-action small-action" data-issue-order="${escapeAttribute(x.id)}">${en?"Issue order":"Emitir orden"}</button>`:""}${["issued","partially_received"].includes(x.status)&&hasPermission("purchasing.receipt.create")?`<button class="primary-action small-action" data-receive-order="${escapeAttribute(x.id)}">${en?"Register receipt":"Registrar recepcion"}</button>`:""}${["draft","issued","partially_received"].includes(x.status)&&hasPermission("purchasing.order.cancel")?`<button class="secondary-action small-action" data-cancel-order="${escapeAttribute(x.id)}">${en?"Cancel":"Cancelar"}</button>`:""}</div></article>`;}).join("")||`<p class="helper-copy">${en?"No purchase orders have been created yet.":"Aun no se han creado ordenes de compra."}</p>`);
    const suppliers=api.suppliers.filter(x=>x.status==="active").map(x=>`<option value="${escapeAttribute(x.id)}" ${editing?.supplier_id===x.id?"selected":""}>${escapeHtml(x.code)} &middot; ${escapeHtml(x.commercial_name)}</option>`).join("");const reqs=api.requisitions.filter(x=>x.status==="approved"||x.id===editing?.requisition_id).map(x=>`<option value="${escapeAttribute(x.id)}" ${sourceRequisitionId===x.id?"selected":""}>${escapeHtml(x.code)} &middot; ${x.lines?.length||0} ${en?"lines":"partidas"}</option>`).join("");
    const orderFields=`<label class="preview-field"><span>${en?"Code":"Codigo"}</span><input name="code" value="${escapeAttribute(editing?.code||"")}" required></label><label class="preview-field"><span>${en?"Approved requisition":"Requisicion aprobada"}</span><select name="requisition_id" data-entity-selector data-search-placeholder="${en?"Search approved requisition":"Buscar requisicion aprobada"}" required ${editing?"disabled":""}><option value="" disabled ${sourceRequisitionId?"":"selected"}>${en?"Choose a requisition":"Selecciona una requisicion"}</option>${reqs}</select></label><label class="preview-field"><span>${en?"Supplier":"Proveedor"}</span><select name="supplier_id" data-entity-selector data-search-placeholder="${en?"Search supplier":"Buscar proveedor"}" required><option value="" disabled ${editing?"":"selected"}>${en?"Choose a supplier":"Selecciona un proveedor"}</option>${suppliers}</select></label><div class="wide-field purchasing-order-prices" id="purchasingOrderPrices"><p class="helper-copy">${en?"Choose a requisition to capture a price for every line.":"Selecciona una requisicion para capturar el precio de cada partida."}</p></div>${editing?`<div class="wide-field"><button class="secondary-action" type="button" data-cancel-order-edit>${en?"Discard edit":"Descartar edicion"}</button></div>`:""}`;
    const creation=editing||pendingRequisitions.length?purchasingForm("purchasingOrderForm",orderFields,editing?(en?"Update purchase order":"Actualizar orden de compra"):(en?"Create purchase order":"Crear orden de compra")):`<section class="section-card"><span class="chip warning">${en?"No pending requisitions":"Sin requisiciones pendientes"}</span><h3>${en?"New purchase order":"Nueva orden de compra"}</h3><p>${en?"There are no approved requisitions pending conversion. Approve a requisition before creating another purchase order.":"No hay requisiciones aprobadas pendientes de convertir. Aprueba una requisicion antes de crear otra orden de compra."}</p>${hasPermission("purchasing.requisition.read")?`<button class="secondary-action" type="button" data-open-pending-purchasing-requisitions>${en?"Review requisitions":"Revisar requisiciones"}</button>`:""}</section>`;
    const form=`<section class="section-card"><div class="purchasing-lines-head"><div><strong>${en?"Purchase orders are operational documents":"Las ordenes de compra son documentos operativos"}</strong><p>${en?"Replenishment is a separate planned feature for automatic reorder suggestions.":"Reabastecimiento es una funcion planeada distinta para sugerencias automaticas por punto de reorden."}</p></div></div></section>`+creation;
    purchasingShell(module,en?"Purchase orders":"Ordenes de compra",en?"Complete history first; create only from approved requisitions pending conversion.":"Primero el historial completo; crea solo desde requisiciones aprobadas pendientes de convertir.",cards,form,true);
    if(!hasPermission(editing?"purchasing.order.update":"purchasing.order.create"))modulePanel.querySelector("#purchasingOrderForm")?.closest(".section-card")?.remove();
    modulePanel.querySelector("[data-open-pending-purchasing-requisitions]")?.addEventListener("click",()=>navigateTo({active:"compras",activeSubmodule:"requisiciones",laborArea:""}));
    const orderForm=modulePanel.querySelector("#purchasingOrderForm"),priceContainer=modulePanel.querySelector("#purchasingOrderPrices"),requisitionSelect=orderForm?.elements.requisition_id;
    const renderOrderPrices=()=>{const req=api.requisitions.find(value=>value.id===(requisitionSelect?.value||editing?.requisition_id));priceContainer.innerHTML=req?`<div class="purchasing-lines-head"><div><strong>${en?"Price by line":"Precio por partida"}</strong><p>${en?"Each requested item keeps its own negotiated price.":"Cada articulo solicitado conserva su precio negociado."}</p></div></div>${req.lines.map((line,index)=>`<label class="resource-input"><span><strong>${escapeHtml(line.description)}</strong><small>${formatNumber(Number(line.quantity))} ${escapeHtml(line.unit_code)}</small></span><input name="unit_price_${index}" data-order-unit-price="${index}" type="number" min="0" step=".01" value="${escapeAttribute(editing?.lines?.[index]?.unit_price??"")}" required aria-label="${en?"Unit price":"Precio unitario"}: ${escapeAttribute(line.description)}"></label>`).join("")}`:`<p class="helper-copy">${en?"Choose a requisition to capture a price for every line.":"Selecciona una requisicion para capturar el precio de cada partida."}</p>`;};
    requisitionSelect?.addEventListener("change",renderOrderPrices);
    if(sourceRequisitionId)renderOrderPrices();
    orderForm?.addEventListener("submit",async event=>{event.preventDefault();const d=Object.fromEntries(new FormData(event.currentTarget)),req=api.requisitions.find(x=>x.id===(d.requisition_id||editing?.requisition_id)),supplier=api.suppliers.find(x=>x.id===d.supplier_id);if(!req||!supplier)return;const payload={code:d.code,requisition_id:req.id,supplier_id:supplier.id,currency:supplier.currency,payment_terms:supplier.payment_terms,lines:req.lines.map((x,index)=>({line_type:x.line_type,inventory_item_id:x.inventory_item_ref_id,description:x.description,quantity:Number(x.quantity),unit_code:x.unit_code,unit_price:Number(event.currentTarget.querySelector(`[data-order-unit-price="${index}"]`).value)}))};try{if(editing)await updatePurchasingOrder(editing.id,payload);else await createPurchasingOrder(payload);state.purchasingOrderEditId="";state.purchasingOrderSourceRequisitionId="";await loadPurchasingApiData();showToast(editing?(en?"Purchase order updated.":"Orden de compra actualizada."):(en?"Purchase order created. Issue it when it is ready to send to the supplier.":"Orden de compra creada. Emitela cuando este lista para enviarse al proveedor."));}catch(error){showToast(error.message||"Error");}});
    modulePanel.querySelectorAll("[data-edit-order]").forEach(button=>button.addEventListener("click",()=>{state.purchasingOrderEditId=button.dataset.editOrder;render();}));modulePanel.querySelector("[data-cancel-order-edit]")?.addEventListener("click",()=>{state.purchasingOrderEditId="";render();});
    modulePanel.querySelectorAll("[data-receive-order]").forEach(button=>button.addEventListener("click",()=>{state.purchasingReceiptSourceOrderId=button.dataset.receiveOrder;navigateTo({active:"compras",activeSubmodule:"recepciones",laborArea:""});}));
    modulePanel.querySelectorAll("[data-cancel-order]").forEach(button=>button.addEventListener("click",()=>openPurchasingCancellationModal("order",button.dataset.cancelOrder)));modulePanel.querySelectorAll("[data-issue-order]").forEach(button=>button.addEventListener("click",async()=>{try{await issuePurchasingOrder(button.dataset.issueOrder);await loadPurchasingApiData();if(hasPermission("purchasing.receipt.create")){state.purchasingReceiptSourceOrderId=button.dataset.issueOrder;navigateTo({active:"compras",activeSubmodule:"recepciones",laborArea:""});showToast(en?"Order issued. Register the supplier receipt when goods arrive.":"Orden emitida. Registra la recepción cuando llegue la mercancía.","success");return;}showToast(en?"Order issued.":"Orden emitida.","success");}catch(error){showApiError(error,en?"The purchase order could not be issued.":"No se pudo emitir la orden de compra.");}}));return;
  }
  if(id==="recepciones"){
    const cards=api.receipts.map(x=>`<article class="catalog-card"><span class="muted-label">${escapeHtml(x.code)}</span><strong>${purchasingStatus(x.status)}</strong><p>${escapeHtml(x.supplier_document_reference||"")} · ${new Date(x.received_at).toLocaleString()}</p><span class="chip ${x.status==="completed"?"active":"warning"}">${purchasingStatus(x.status)}</span>${x.status==="needs_reconciliation"&&hasPermission("purchasing.receipt.reconcile")?`<button class="primary-action small-action" data-reconcile-receipt="${escapeAttribute(x.id)}">${en?"Reconcile":"Conciliar"}</button>`:""}</article>`).join("");
    const sourceOrderId=state.purchasingReceiptSourceOrderId||"",openOrders=api.orders.filter(x=>["issued","partially_received"].includes(x.status)&&x.lines.some(line=>Number(line.received_quantity)<Number(line.quantity))),orderOptions=openOrders.map(order=>`<option value="${escapeAttribute(order.id)}" ${sourceOrderId===order.id?"selected":""}>${escapeHtml(order.code)} · ${order.lines.length} ${en?"lines":"partidas"}</option>`).join("");const warehouses=api.warehouses.filter(x=>x.status==="active").map(x=>`<option value="${escapeAttribute(x.id)}">${escapeHtml(x.code)} · ${escapeHtml(x.name)}</option>`).join("");
    const form=purchasingForm("purchasingReceiptForm",`<label class="preview-field"><span>${en?"Receipt code":"Codigo de recepcion"}</span><input name="code" required></label><label class="preview-field"><span>${en?"Purchase order":"Orden de compra"}</span><select name="purchase_order_id" required><option value="" disabled ${sourceOrderId?"":"selected"}>${en?"Choose an order":"Selecciona una orden"}</option>${orderOptions}</select></label><label class="preview-field"><span>${en?"Supplier document":"Documento proveedor"}</span><input name="supplier_document_reference"></label><div class="wide-field purchasing-requisition-lines" id="purchasingReceiptLines"><p class="helper-copy">${en?"Choose an order and capture one or more received lines.":"Selecciona una orden y captura una o mas partidas recibidas."}</p></div>`,en?"Register receipt":"Registrar recepcion");
    purchasingShell(module,en?"Receipts":"Recepciones",en?"Partial receipts create authoritative Inventory entries.":"Las recepciones parciales crean entradas autoritativas en Inventarios.",cards,form);
    if(!hasPermission("purchasing.receipt.create"))modulePanel.querySelector("#purchasingReceiptForm")?.closest(".section-card")?.remove();
    const receiptForm=modulePanel.querySelector("#purchasingReceiptForm"),receiptLines=modulePanel.querySelector("#purchasingReceiptLines");
    const renderReceiptLines=orderId=>{const order=openOrders.find(value=>value.id===orderId);receiptLines.innerHTML=(order?.lines||[]).filter(line=>Number(line.received_quantity)<Number(line.quantity)).map(line=>{const remaining=Number(line.quantity)-Number(line.received_quantity),inventory=line.line_type==="inventory_item";return `<div class="purchasing-requisition-line" data-receipt-line data-line-id="${escapeAttribute(line.id)}" data-remaining="${remaining}"><div class="purchasing-line-item"><strong>${escapeHtml(line.description)}</strong><small>${en?"Remaining":"Pendiente"}: ${formatNumber(remaining)} ${escapeHtml(line.unit_code)}</small></div><label class="preview-field"><span>${en?"Received quantity":"Cantidad recibida"}</span><input name="quantity" type="number" min="0" max="${remaining}" step="any" value="0"></label>${inventory?`<label class="preview-field"><span>${en?"Warehouse":"Almacen"}</span><select name="warehouse_id"><option value="">${en?"Choose a warehouse":"Selecciona un almacen"}</option>${warehouses}</select></label>`:`<input name="warehouse_id" type="hidden" value="">`}</div>`;}).join("")||`<p class="helper-copy">${en?"This order has no pending lines.":"Esta orden no tiene partidas pendientes."}</p>`;};
    receiptForm?.elements.purchase_order_id.addEventListener("change",event=>renderReceiptLines(event.target.value));
    if(sourceOrderId&&receiptForm)renderReceiptLines(sourceOrderId);
    receiptForm?.addEventListener("submit",async event=>{event.preventDefault();const f=event.currentTarget,d=Object.fromEntries(new FormData(f)),lines=[...f.querySelectorAll("[data-receipt-line]")].map(row=>({order_line_id:row.dataset.lineId,quantity:Number(row.querySelector('[name="quantity"]').value),warehouse_id:row.querySelector('[name="warehouse_id"]').value||null,remaining:Number(row.dataset.remaining)})).filter(line=>line.quantity>0);if(!lines.length){showToast(en?"Capture at least one received quantity.":"Captura al menos una cantidad recibida.");return;}if(lines.some(line=>line.quantity>line.remaining)){showToast(en?"A quantity exceeds its remaining balance.":"Una cantidad excede su saldo pendiente.");return;}const order=openOrders.find(value=>value.id===d.purchase_order_id);if(lines.some(line=>order?.lines.find(value=>value.id===line.order_line_id)?.line_type==="inventory_item"&&!line.warehouse_id)){showToast(en?"Select a warehouse for every inventory line.":"Selecciona un almacen para cada partida inventariable.");return;}try{await createPurchasingReceipt({code:d.code,purchase_order_id:d.purchase_order_id,received_at:new Date().toISOString(),supplier_document_reference:d.supplier_document_reference||null,lines:lines.map(({remaining,...line})=>line)});state.purchasingReceiptSourceOrderId="";await loadPurchasingApiData();showToast(en?`${lines.length} receipt lines registered.`:`Recepcion registrada con ${lines.length} partidas.`);}catch(error){showToast(error.message||"Error");}});
    modulePanel.querySelectorAll("[data-reconcile-receipt]").forEach(button=>button.addEventListener("click",async()=>{try{await reconcilePurchasingReceipt(button.dataset.reconcileReceipt);await loadPurchasingApiData();showToast(en?"Receipt reconciled.":"Recepcion conciliada.");}catch(error){showToast(error.message||"Error");}}));return;
  }
  if(id==="reabastecimiento"){
    const planned=`<article class="catalog-card"><span class="chip warning">${en?"Planned":"Planeado"}</span><strong>${en?"Automatic purchasing suggestions":"Sugerencias automaticas de compra"}</strong><p>${en?"This future flow will analyze minimum stock, reorder points, demand, open purchase orders, and supplier lead time. It does not list or create purchase orders.":"Este flujo futuro analizara minimos, puntos de reorden, demanda, ordenes abiertas y tiempo de entrega del proveedor. No lista ni crea ordenes de compra."}</p></article>`;
    purchasingShell(module,en?"Replenishment":"Reabastecimiento",en?"Planning by stock policy; separate from operational purchase orders.":"Planeacion por politicas de inventario; separado de las ordenes de compra operativas.",planned);return;
  }
  purchasingShell(module,en?"Purchasing":"Compras",en?"This purchasing route is not available.":"Esta ruta de Compras no esta disponible.","");
}

function renderGenericSubmodulePanel(module) {
  const submodule = getGenericSubmodule(module, state.activeSubmodule);
  if (isWarehouseMasterSubmodule(module, submodule)) {
    renderWarehouseCatalogPanel(module, submodule);
    return;
  }
  if (isWarehouseItemsSubmodule(module, submodule)) {
    renderInventoryItemsPanel(module, submodule);
    return;
  }
  if (isWarehouseMovementSubmodule(module, submodule)) {
    renderWarehouseMovementsPanel(module, submodule);
    return;
  }
  if (isWarehouseStockSubmodule(module, submodule)) {
    renderWarehouseStockPanel(module, submodule);
    return;
  }
  if (isWarehouseReservationsSubmodule(module, submodule)) {
    renderWarehouseComingSoonPanel(module, submodule);
    return;
  }
  if (isWarehouseKardexSubmodule(module, submodule)) {
    renderWarehouseKardexPanel(module, submodule);
    return;
  }
  if (isSalesCustomersSubmodule(module, submodule)) {
    renderSalesCustomersPanel(module, submodule);
    return;
  }
  if (isSalesQuotesSubmodule(module, submodule)) {
    renderSalesQuotesPanel(module, submodule);
    return;
  }
  if (isSalesOrdersSubmodule(module, submodule)) {
    renderSalesOrdersPanel(module, submodule);
    return;
  }
  if (isSalesDeliveriesSubmodule(module, submodule)) {
    renderSalesDeliveriesPanel(module, submodule);
    return;
  }
  if (isSalesMarginSubmodule(module, submodule)) {
    renderSalesMarginPanel(module, submodule);
    return;
  }
  const sampleRows = buildGenericSubmoduleRows(module, submodule);
  const columns = getGenericSubmoduleColumns(module);
  const formFields = getGenericSubmoduleForm(module, submodule);
  const integrations = getGenericSubmoduleIntegrations(module);
  const label = state.lang === "en" ? module.titleEn : module.title;
  const flowGuide = getGenericFlowGuide(module, submodule);

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("openForm")}</span>
        </button>
      </div>

      <div class="submodule-layout">
        ${flowGuide}
        <section class="section-card">
          <div class="section-title">
            <span class="section-icon">▦</span>
            <strong>${t("recommendedSetup")}</strong>
          </div>
          <div class="catalog-grid compact-catalog">
            ${submodule.focus
              .map((item) => `
                <article class="catalog-card compact-card">
                  <div>
                    <span class="muted-label">${t("keyData")}</span>
                    <strong>${item}</strong>
                    <p>${submodule.detail}</p>
                  </div>
                </article>
              `)
              .join("")}
          </div>
        </section>

        <section class="section-card">
          <div class="section-title">
            <span class="section-icon">↳</span>
            <strong>${t("operatingFlow")}</strong>
          </div>
          <ol class="workflow-list">
            ${(getModuleField(module, "workflow") || []).slice(0, 5).map((step) => `<li>${step}</li>`).join("")}
          </ol>
        </section>
      </div>

      <div class="module-workbench">
        <section class="section-card table-card">
          <div class="section-title">
            <span class="section-icon">☷</span>
            <strong>${t("workView")}</strong>
          </div>
          <div class="data-table" role="table">
            <div class="table-row table-head" role="row">
              ${columns.map((column) => `<span role="columnheader">${column}</span>`).join("")}
            </div>
            ${sampleRows
              .map((row) => `
                <div class="table-row" role="row">
                  ${row.map((cell) => `<span role="cell">${cell}</span>`).join("")}
                </div>
              `)
              .join("")}
          </div>
        </section>

        <section class="section-card form-preview">
          <div class="section-title">
            <span class="section-icon">✎</span>
            <strong>${t("quickCapture")}</strong>
          </div>
          ${formFields
            .map(([labelText, value]) => `
              <label class="preview-field">
                <span>${labelText}</span>
                <input type="text" value="${value}" readonly />
              </label>
            `)
            .join("")}
          <button class="secondary-action full" type="button" data-action="module-primary">${t("openForm")}</button>
        </section>
      </div>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">✓</span>
          <strong>${t("integrations")}</strong>
        </div>
        <div class="compat-list">
          ${integrations
            .map(([name, detail]) => `
              <article>
                <strong>${name}</strong>
                <p>${detail}</p>
              </article>
            `)
            .join("")}
        </div>
      </section>

      <div class="records module-records">
        ${getGenericSubmoduleRecords(module, submodule)
          .map(([code, desc, status]) => `
            <article class="record-row">
              <div class="record-main">
                <strong>${code}</strong>
                <span>${desc}</span>
              </div>
              <span class="chip">${status}</span>
            </article>
          `)
          .join("")}
      </div>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  bindProductionPanelActions();
}

function renderWarehouseCatalogPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const search = localStorage.getItem("erclave-warehouse-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const warehouses = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "warehouse");
  const filteredWarehouses = normalizedSearch
    ? warehouses.filter((record) =>
        [
          record.code,
          record.title,
          record.status,
          record.owner,
          translateWarehouseType(record.fields?.type),
          record.fields?.businessCenter,
          record.fields?.location,
          record.fields?.capacity,
          record.fields?.zone,
          record.fields?.aisle,
          record.fields?.rack,
          record.fields?.level,
          record.fields?.position,
          record.fields?.description
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch)
      )
    : warehouses;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newWarehouse")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="warehouseSearch" type="search" value="${search}" placeholder="${t("searchWarehouses")}" />
          </label>
        </div>
        <p class="helper-copy">${t("warehouseCatalogHelper")}</p>
        <div class="catalog-grid">
          ${filteredWarehouses.length ? filteredWarehouses.map(renderWarehouseCard).join("") : renderWarehouseEmptyState(Boolean(search))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  const warehouseSearch = modulePanel.querySelector("#warehouseSearch");
  if (warehouseSearch) {
    warehouseSearch.addEventListener("input", (event) => {
      localStorage.setItem("erclave-warehouse-search", event.target.value);
      render();
      const nextSearch = modulePanel.querySelector("#warehouseSearch");
      if (nextSearch) {
        nextSearch.focus();
        nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
      }
    });
  }
  bindProductionPanelActions();
}

function renderWarehouseCard(record) {
  return `
    <article class="catalog-card">
      <div class="catalog-card-main">
        <span class="muted-label">${record.code} - ${translateWarehouseType(record.fields?.type)}</span>
        <strong>${record.title}</strong>
        <p>${record.fields?.businessCenter || ""} - ${record.fields?.location || ""}</p>
        <span class="muted-label">${t("warehouseOwner")}: ${record.owner || t("noRecords")}</span>
        <span class="muted-label">${t("capacity")}: ${record.fields?.capacity || t("notDefined")}</span>
        <span class="muted-label">${t("physicalLocation")}: ${getPhysicalLocationCode(record.fields) || t("notDefined")}</span>
        <span class="muted-label">${t("inventoryPolicy")}: ${translateInventoryPolicy(record.fields?.policy)} · ${t("allowsReservations")}: ${translateYesNo(record.fields?.allowsReservations)}</span>
        ${record.fields?.description ? `<p>${record.fields.description}</p>` : ""}
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Activo" ? "active" : record.status === "Bloqueado" ? "warning" : ""}">${translateStatus(record.status)}</span>
        <button class="secondary-action small-action" type="button" data-action="edit-warehouse" data-record-id="${record.id}">${t("edit")}</button>
      </div>
    </article>
  `;
}

function renderWarehouseEmptyState(hasSearch = false) {
  return `
    <article class="catalog-card compact-card">
      <div>
        <span class="muted-label">${t("noRecords")}</span>
        <strong>${hasSearch ? t("warehouseNoMatchesTitle") : t("warehouseEmptyTitle")}</strong>
        <p>${hasSearch ? t("warehouseNoMatchesDetail") : t("warehouseEmptyDetail")}</p>
      </div>
    </article>
  `;
}

function renderInventoryItemsPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  if (getApiMode() === "api" && isInventoryApiEnabled() && state.inventoryItems.status === "idle") loadInventoryItemData();
  const search = localStorage.getItem("erclave-inventory-item-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const items = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "inventoryItem");
  const filteredItems = normalizedSearch
    ? items.filter((record) =>
        [
          record.code,
          record.title,
          record.status,
          record.owner,
          translateInventoryItemType(record.fields?.type),
          record.fields?.category,
          record.fields?.unit,
          record.fields?.minStock,
          record.fields?.maxStock,
          record.fields?.defaultWarehouseName,
          record.fields?.description
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch)
      )
    : items;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newInventoryItem")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="inventoryItemSearch" type="search" value="${search}" placeholder="${t("searchInventoryItems")}" />
          </label>
        </div>
        <p class="helper-copy">${t("inventoryItemCatalogHelper")}</p>
        <div class="catalog-grid">
          ${filteredItems.length ? filteredItems.map(renderInventoryItemCard).join("") : renderInventoryItemEmptyState(Boolean(search))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  const itemSearch = modulePanel.querySelector("#inventoryItemSearch");
  if (itemSearch) {
    itemSearch.addEventListener("input", (event) => {
      localStorage.setItem("erclave-inventory-item-search", event.target.value);
      render();
      const nextSearch = modulePanel.querySelector("#inventoryItemSearch");
      if (nextSearch) {
        nextSearch.focus();
        nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
      }
    });
  }
  bindProductionPanelActions();
}

function renderInventoryItemCard(record) {
  return `
    <article class="catalog-card">
      <div class="catalog-card-main">
        <span class="muted-label">${record.code} - ${translateInventoryItemType(record.fields?.type)}</span>
        <strong>${record.title}</strong>
        <p>${record.fields?.category || t("notDefined")} - ${record.fields?.unit || t("notDefined")}</p>
        <span class="muted-label">${t("defaultWarehouse")}: ${record.fields?.defaultWarehouseName || t("notDefined")}</span>
        <span class="muted-label">${t("stockRange")}: ${record.fields?.minStock || "0"} / ${record.fields?.maxStock || t("notDefined")}</span>
        <span class="muted-label">${t("inventoryPolicy")}: ${translateInventoryPolicy(record.fields?.policy)}</span>
        <span class="muted-label">${record.fields?.useInRecipe ? t("usedInRecipe") : t("notUsedInRecipe")}</span>
        ${record.fields?.description ? `<p>${record.fields.description}</p>` : ""}
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Activo" ? "active" : record.status === "Bloqueado" ? "warning" : ""}">${translateStatus(record.status)}</span>
        <button class="secondary-action small-action" type="button" data-action="edit-inventory-item" data-record-id="${record.id}">${t("edit")}</button>
      </div>
    </article>
  `;
}

function renderInventoryItemEmptyState(hasSearch = false) {
  return `
    <article class="catalog-card compact-card">
      <div>
        <span class="muted-label">${t("noRecords")}</span>
        <strong>${hasSearch ? t("inventoryItemNoMatchesTitle") : t("inventoryItemEmptyTitle")}</strong>
        <p>${hasSearch ? t("inventoryItemNoMatchesDetail") : t("inventoryItemEmptyDetail")}</p>
      </div>
    </article>
  `;
}

function renderWarehouseMovementsPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  if (getApiMode() === "api" && isInventoryApiEnabled() && state.inventoryItems.status === "idle") loadInventoryItemData();
  if (getApiMode() === "api" && isInventoryApiEnabled() && state.inventoryItems.status === "ready" && state.inventoryMovements.status === "idle") loadInventoryMovementData();
  if (getApiMode() === "api" && isInventoryApiEnabled() && state.inventoryItems.status === "ready" && state.finishedGoodsReceipts.status === "idle") loadFinishedGoodsReceiptData();
  const movements = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "inventoryMovement");
  const receiptRows=getPendingFinishedGoodsReceipts();

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newMovement")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule))}
        <div class="section-heading">
          <div><h3>${t("finishedGoodsReceipts")}</h3><p class="helper-copy">${t("finishedGoodsReceiptsHelp")}</p></div>
        </div>
        ${state.finishedGoodsReceipts.status==="loading"?`<p class="helper-copy">${t("loading")}</p>`:state.finishedGoodsReceipts.error?`<div class="form-errors">${escapeHtml(state.finishedGoodsReceipts.error)}</div>`:receiptRows.length?`<div class="records module-records">${receiptRows.map(renderPendingFinishedGoodsReceipt).join("")}</div>`:`<article class="record-row"><div class="record-main"><strong>${t("noPendingFinishedGoods")}</strong><span>${t("noPendingFinishedGoodsHelp")}</span></div></article>`}
        <hr />
        <h3>${t("movementHistory")}</h3>
        <p class="helper-copy">${t("movementManualHelper")}</p>
        <div class="data-table" role="table">
          <div class="table-row table-head" role="row">
            <span role="columnheader">${t("document")}</span>
            <span role="columnheader">${t("movementType")}</span>
            <span role="columnheader">${t("item")}</span>
            <span role="columnheader">${t("quantity")}</span>
          </div>
          ${movements.length ? movements.map(renderMovementRow).join("") : `
            <div class="table-row" role="row">
              <span role="cell">${t("noRecords")}</span>
              <span role="cell">${t("newMovement")}</span>
              <span role="cell">${t("movementEmptyDetail")}</span>
              <span role="cell">-</span>
            </div>
          `}
        </div>
        <div class="records module-records">
          ${movements.length ? movements.map(renderMovementRecord).join("") : ""}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  bindProductionPanelActions();
}

let inventorySearchTimer;

function getInventoryViewFilters() {
  return {
    q: localStorage.getItem("erclave-stock-search") || "",
    warehouse_id: localStorage.getItem("erclave-stock-warehouse") || "all",
    category: localStorage.getItem("erclave-stock-category") || "all",
    item_type: localStorage.getItem("erclave-stock-type") || "all",
    item_status: localStorage.getItem("erclave-stock-item-status") || "all",
    inventory_policy: localStorage.getItem("erclave-stock-policy") || "all",
    unit: localStorage.getItem("erclave-stock-unit") || "all",
    stock_status: localStorage.getItem("erclave-stock-status") || "all",
    sort: localStorage.getItem("erclave-stock-sort") || "item_code",
    limit: 50,
    cursor: state.inventoryBalances.cursor || ""
  };
}

function inventoryQueryKey(filters) {
  return JSON.stringify(filters);
}

function loadInventoryBalances(filters = getInventoryViewFilters()) {
  const queryKey = inventoryQueryKey(filters);
  if (state.inventoryBalances.status === "loading" && state.inventoryBalances.queryKey === queryKey) return;
  state.inventoryBalances = { ...state.inventoryBalances, status: "loading", error: "", queryKey };
  getInventoryBalances(filters)
    .then((response) => {
      if (state.inventoryBalances.queryKey !== queryKey) return;
      state.inventoryBalances = { ...state.inventoryBalances, status: "ready", data: response.data || [], page: response.page || {}, error: "" };
      render();
    })
    .catch((error) => {
      if (state.inventoryBalances.queryKey !== queryKey) return;
      state.inventoryBalances = { ...state.inventoryBalances, status: "error", data: [], page: {}, error: error.message || t("inventoryLoadError") };
      render();
    });
}

function getInventoryStockStatus(row) {
  if (row.stock_status) return row.stock_status;
  const balance = Number(row.on_hand_quantity ?? row.balance ?? 0);
  const minimum = Number(row.minimum_stock || 0);
  const maximum = row.maximum_stock === null || row.maximum_stock === undefined || row.maximum_stock === "" ? null : Number(row.maximum_stock);
  if (balance < 0) return "negative";
  if (balance === 0) return "zero";
  if (balance < minimum) return "below_minimum";
  if (maximum !== null && balance > maximum) return "above_maximum";
  return "normal";
}

function translateInventoryStockStatus(status) {
  return ({ negative: t("negativeStockStatus"), zero: t("zeroStockStatus"), out_of_stock: t("zeroStockStatus"), below_minimum: t("belowMinimumStatus"), normal: t("normalStockStatus"), available: t("availableStatus"), above_maximum: t("aboveMaximumStatus") })[status] || status;
}

function normalizeInventoryBalance(row) {
  return {
    ...row,
    itemCode: row.item_code || row.code || "",
    itemName: row.item_name || row.name || row.inventory_item_id,
    category: row.category || "",
    itemType: row.item_type || row.type || "",
    itemStatus: row.item_status || "active",
    policy: row.inventory_policy || "",
    warehouseCode: row.warehouse_code || "",
    warehouseName: row.warehouse_name || row.warehouse_id,
    warehouseType: row.warehouse_type || "",
    unit: row.unit || row.base_unit || "",
    balance: Number(row.on_hand_quantity ?? row.balance ?? 0),
    minimum: Number(row.minimum_stock || 0),
    maximum: row.maximum_stock === null || row.maximum_stock === undefined ? null : Number(row.maximum_stock),
    lastMovement: row.last_movement_at || row.last_movement || "",
    status: getInventoryStockStatus(row)
  };
}

function applyLocalInventoryFilters(rows, filters) {
  const normalizedQuery = filters.q.trim().toLocaleLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  return rows.filter((row) => {
    const haystack = [row.itemCode,row.itemName,row.category,row.warehouseCode,row.warehouseName,row.unit].join(" ").toLocaleLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return (!normalizedQuery || haystack.includes(normalizedQuery))
      && (filters.warehouse_id === "all" || row.warehouse_id === filters.warehouse_id || row.warehouseId === filters.warehouse_id)
      && (filters.category === "all" || row.category === filters.category)
      && (filters.item_type === "all" || row.itemType === filters.item_type)
      && (filters.item_status === "all" || row.itemStatus === filters.item_status)
      && (filters.inventory_policy === "all" || row.policy === filters.inventory_policy)
      && (filters.unit === "all" || row.unit === filters.unit)
      && (filters.stock_status === "all" || row.status === filters.stock_status);
  });
}

function renderWarehouseStockPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const filters = getInventoryViewFilters();
  const warehouses = mockDb.loadModuleRecords(module.id, "almacenes").filter((record) => record.recordType === "warehouse");
  const items = mockDb.loadModuleRecords(module.id, "articulos").filter((record) => record.recordType === "inventoryItem");
  const movements = mockDb.loadModuleRecords(module.id, "movimientos").filter((record) => record.recordType === "inventoryMovement");
  const usesApiBalances = getApiMode() === "api" && isInventoryApiEnabled();
  const queryKey = inventoryQueryKey(filters);
  if (usesApiBalances && state.inventoryBalances.queryKey !== queryKey) loadInventoryBalances(filters);
  const rawStockRows = (usesApiBalances
    ? state.inventoryBalances.data
    : buildStockBalances(movements)
  ).map(normalizeInventoryBalance);
  const stockRows = usesApiBalances ? rawStockRows : applyLocalInventoryFilters(rawStockRows, filters);
  const categories = [...new Set([...items.map((item) => item.fields?.category),...stockRows.map((row)=>row.category)].filter(Boolean))].sort();
  const types = [...new Set(["rawMaterial","consumable","tool","finishedGood","sparePart","serviceSupply",...stockRows.map((row)=>row.itemType)].filter(Boolean))];
  const policies = ["standard","lot","serial","restricted"];
  const units = [...new Set([...items.map((item) => item.fields?.unit),...stockRows.map((row)=>row.unit)].filter(Boolean))].sort();
  const activeFilters = Object.entries(filters).filter(([key, value]) => !["limit", "cursor", "sort"].includes(key) && value && value !== "all");

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        <button class="primary-action" type="button" data-action="module-primary">
          <span>☷</span>
          <span>${t("calculatedStock")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule), null, false)}
        <p class="helper-copy">${t("stockHelper")}</p>
        <div class="catalog-toolbar inventory-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="stockSearch" type="search" value="${filters.q}" placeholder="${t("searchStock")}" autocomplete="off" />
          </label>
          <label class="preview-field compact-filter">
            <span>${t("warehouse")}</span>
            <select id="stockWarehouseFilter" data-entity-selector>
              <option value="all">${t("allWarehouses")}</option>
              ${warehouses.map((warehouse) => `<option value="${warehouse.id}" ${selectedOption(filters.warehouse_id, warehouse.id)}>${warehouse.code} - ${warehouse.title}</option>`).join("")}
            </select>
          </label>
          <label class="preview-field compact-filter"><span>${t("inventoryCategory")}</span><input id="stockCategoryFilter" list="inventoryCategoryOptions" value="${filters.category === "all" ? "" : filters.category}" placeholder="${t("allCategories")}" /><datalist id="inventoryCategoryOptions">${categories.map((value) => `<option value="${value}"></option>`).join("")}</datalist></label>
          <label class="preview-field compact-filter"><span>${t("inventoryStockStatus")}</span><select id="stockStatusFilter"><option value="all">${t("allStatuses")}</option>${["negative","out_of_stock","below_minimum","normal","above_maximum"].map((value) => `<option value="${value}" ${selectedOption(filters.stock_status,value)}>${translateInventoryStockStatus(value)}</option>`).join("")}</select></label>
          <label class="preview-field compact-filter"><span>${t("inventorySort")}</span><select id="stockSortFilter">${[["item_code",t("sortItemCode")],["item_name",t("sortItemName")],["on_hand_asc",t("sortStockAscending")],["on_hand_desc",t("sortStockDescending")]].map(([value,text]) => `<option value="${value}" ${selectedOption(filters.sort,value)}>${text}</option>`).join("")}</select></label>
          <details class="inventory-more-filters"><summary>${t("inventoryFilters")}</summary><div class="inventory-filter-grid">
            <label class="preview-field compact-filter"><span>${t("inventoryType")}</span><select id="stockTypeFilter"><option value="all">${t("allTypes")}</option>${types.map((value) => `<option value="${value}" ${selectedOption(filters.item_type,value)}>${translateInventoryItemType(value)}</option>`).join("")}</select></label>
            <label class="preview-field compact-filter"><span>${t("inventoryItemStatus")}</span><select id="stockItemStatusFilter"><option value="all">${t("allStatuses")}</option>${[["active","Activo"],["inactive","Inactivo"],["blocked","Bloqueado"]].map(([value,label]) => `<option value="${value}" ${selectedOption(filters.item_status,value)}>${translateStatus(label)}</option>`).join("")}</select></label>
            <label class="preview-field compact-filter"><span>${t("inventoryPolicyFilter")}</span><select id="stockPolicyFilter"><option value="all">${t("allPolicies")}</option>${policies.map((value) => `<option value="${value}" ${selectedOption(filters.inventory_policy,value)}>${translateInventoryPolicy(value)}</option>`).join("")}</select></label>
            <label class="preview-field compact-filter"><span>${t("inventoryUnitFilter")}</span><select id="stockUnitFilter"><option value="all">${t("allUnits")}</option>${units.map((value) => `<option value="${value}" ${selectedOption(filters.unit,value)}>${value}</option>`).join("")}</select></label>
          </div></details>
        </div>
        <div class="inventory-filter-summary"><span>${t("inventoryResults", { count: stockRows.length })}</span><div class="inventory-filter-chips">${activeFilters.map(([key,value]) => `<button type="button" class="filter-chip" data-clear-stock-filter="${key}">${value}<span aria-hidden="true">×</span></button>`).join("")}</div>${activeFilters.length ? `<button type="button" class="secondary-action small-action" data-action="clear-stock-filters">${t("clearFilters")}</button>` : ""}</div>
        ${usesApiBalances && state.inventoryBalances.status === "loading" ? `<div class="inventory-feedback">${t("inventoryLoading")}</div>` : ""}
        ${usesApiBalances && state.inventoryBalances.status === "error" ? `<div class="inventory-feedback error"><strong>${t("inventoryLoadError")}</strong><span>${state.inventoryBalances.error}</span><button class="secondary-action small-action" data-action="retry-stock-api">${t("inventoryRetry")}</button></div>` : ""}
        <div class="data-table inventory-table" role="table">
          <div class="table-row table-head" role="row">
            <span role="columnheader">${t("inventoryItemColumn")}</span>
            <span role="columnheader">${t("warehouse")}</span>
            <span role="columnheader">${t("unit")}</span>
            <span role="columnheader">${t("physicalStock")}</span>
            <span role="columnheader">${t("stockRange")}</span>
            <span role="columnheader">${t("lastMovement")}</span>
          </div>
          ${stockRows.length ? stockRows.map(renderInventoryBalanceRow).join("") : renderStockEmptyRow(usesApiBalances || Boolean(movements.length))}
        </div>
        ${usesApiBalances ? `<nav class="inventory-pagination" aria-label="${t("inventoryResults", {count:stockRows.length})}"><button class="secondary-action small-action" type="button" data-action="stock-previous" ${state.inventoryBalances.previousCursors.length ? "" : "disabled"}>${t("previousPage")}</button><button class="secondary-action small-action" type="button" data-action="stock-next" ${state.inventoryBalances.page?.next_cursor ? "" : "disabled"}>${t("nextPage")}</button></nav>` : ""}
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  const setFilter = (key, value) => { localStorage.setItem(`erclave-stock-${key}`, value || "all"); state.inventoryBalances={...state.inventoryBalances,status:"idle",cursor:"",previousCursors:[]}; render(); };
  modulePanel.querySelector("#stockWarehouseFilter")?.addEventListener("change", (event) => setFilter("warehouse", event.target.value));
  modulePanel.querySelector("#stockCategoryFilter")?.addEventListener("change", (event) => setFilter("category", event.target.value.trim() || "all"));
  modulePanel.querySelector("#stockStatusFilter")?.addEventListener("change", (event) => setFilter("status", event.target.value));
  modulePanel.querySelector("#stockSortFilter")?.addEventListener("change", (event) => setFilter("sort", event.target.value));
  modulePanel.querySelector("#stockTypeFilter")?.addEventListener("change", (event) => setFilter("type", event.target.value));
  modulePanel.querySelector("#stockItemStatusFilter")?.addEventListener("change", (event) => setFilter("item-status", event.target.value));
  modulePanel.querySelector("#stockPolicyFilter")?.addEventListener("change", (event) => setFilter("policy", event.target.value));
  modulePanel.querySelector("#stockUnitFilter")?.addEventListener("change", (event) => setFilter("unit", event.target.value));
  const stockSearch = modulePanel.querySelector("#stockSearch");
  stockSearch.addEventListener("input", (event) => {
    const value = event.target.value;
    localStorage.setItem("erclave-stock-search", value);
    clearTimeout(inventorySearchTimer);
    inventorySearchTimer = setTimeout(() => { state.inventoryBalances={...state.inventoryBalances,status:"idle",cursor:"",previousCursors:[]}; render(); modulePanel.querySelector("#stockSearch")?.focus(); }, 300);
  });
  modulePanel.querySelectorAll("[data-clear-stock-filter]").forEach((button) => button.addEventListener("click", () => setFilter(({warehouse_id:"warehouse",item_type:"type",item_status:"item-status",inventory_policy:"policy",stock_status:"status"})[button.dataset.clearStockFilter] || button.dataset.clearStockFilter, "all")));
  modulePanel.querySelector("[data-action='clear-stock-filters']")?.addEventListener("click", () => { ["search","warehouse","category","type","item-status","policy","unit","status","sort"].forEach((key) => localStorage.removeItem(`erclave-stock-${key}`)); state.inventoryBalances={status:"idle",data:[],page:{},error:"",queryKey:"",cursor:"",previousCursors:[]}; render(); });
  modulePanel.querySelector("[data-action='retry-stock-api']")?.addEventListener("click", () => { state.inventoryBalances.status="idle"; state.inventoryBalances.queryKey=""; render(); });
  modulePanel.querySelector("[data-action='stock-next']")?.addEventListener("click", () => { const next=state.inventoryBalances.page?.next_cursor;if(!next)return;state.inventoryBalances.previousCursors.push(state.inventoryBalances.cursor||"");state.inventoryBalances.cursor=next;state.inventoryBalances.queryKey="";render(); });
  modulePanel.querySelector("[data-action='stock-previous']")?.addEventListener("click", () => { state.inventoryBalances.cursor=state.inventoryBalances.previousCursors.pop()||"";state.inventoryBalances.queryKey="";render(); });
  modulePanel.querySelectorAll("[data-action='open-stock-kardex']").forEach((button) => button.addEventListener("click", () => {
    localStorage.setItem("erclave-kardex-item", button.dataset.itemId || "all");
    localStorage.setItem("erclave-kardex-warehouse", button.dataset.warehouseId || "all");
    navigateTo({ active: module.id, activeSubmodule: "kardex", laborArea: "" });
  }));
}

function renderInventoryBalanceRow(row) {
  const statusClass = ["negative","zero","out_of_stock","below_minimum"].includes(row.status) ? "warning" : "active";
  return `<div class="table-row" role="row">
    <span role="cell" class="inventory-item-cell" data-label="${t("inventoryItemColumn")}"><strong>${row.itemCode ? `${row.itemCode} · ` : ""}${row.itemName}</strong><small>${row.category || t("notDefined")} · ${translateInventoryItemType(row.itemType)}</small></span>
    <span role="cell" data-label="${t("warehouse")}"><strong>${row.warehouseCode ? `${row.warehouseCode} · ` : ""}${row.warehouseName}</strong></span>
    <span role="cell" data-label="${t("unit")}">${row.unit}</span>
    <span role="cell" data-label="${t("physicalStock")}"><strong>${formatNumber(row.balance)}</strong></span>
    <span role="cell" data-label="${t("stockRange")}"><small>${formatNumber(row.minimum)} / ${row.maximum === null ? "—" : formatNumber(row.maximum)}</small><span class="chip ${statusClass}">${translateInventoryStockStatus(row.status)}</span></span>
    <span role="cell" data-label="${t("lastMovement")}"><small>${formatKardexDate(row.lastMovement)}</small><button type="button" class="inline-action" data-action="open-stock-kardex" data-item-id="${row.inventory_item_id || row.itemId || ""}" data-warehouse-id="${row.warehouse_id || row.warehouseId || ""}">${t("viewKardex")}</button></span>
  </div>`;
}

function buildStockBalances(movements) {
  const balances = new Map();
  movements
    .slice()
    .sort((a, b) => getMovementTimestamp(a) - getMovementTimestamp(b))
    .forEach((record) => {
      const fields = record.fields || {};
      const quantity = Number(fields.quantity || 0);
      const unit = fields.unit || "";
      const signedQuantity = getMovementSignedQuantity(fields.movementType, quantity);
      const itemKey = fields.itemId || fields.item || record.title;
      const warehouseKey = fields.warehouseId || fields.warehouseName || record.owner;
      const balanceKey = `${itemKey}-${warehouseKey}-${unit}`;
      const current = balances.get(balanceKey) || {
        itemId: fields.itemId || "",
        itemName: fields.item || record.title,
        warehouseId: fields.warehouseId || "",
        warehouseName: fields.warehouseName || record.owner || t("notDefined"),
        unit,
        entries: 0,
        issues: 0,
        balance: 0,
        lastMovement: ""
      };
      current.entries += signedQuantity > 0 ? quantity : 0;
      current.issues += signedQuantity < 0 ? quantity : 0;
      current.balance += signedQuantity;
      current.lastMovement = fields.movementDate || record.createdAt || current.lastMovement;
      balances.set(balanceKey, current);
    });
  return [...balances.values()].sort((a, b) => a.itemName.localeCompare(b.itemName));
}

function filterStockBalances(rows, warehouseFilter, search) {
  const normalizedSearch = search.trim().toLowerCase();
  return rows.filter((row) => {
    const matchesWarehouse = warehouseFilter === "all" || row.warehouseId === warehouseFilter;
    const matchesSearch = !normalizedSearch || [
      row.itemName,
      row.warehouseName,
      row.unit,
      getStockStatus(row.balance)
    ]
      .join(" ")
      .toLowerCase()
      .includes(normalizedSearch);
    return matchesWarehouse && matchesSearch;
  });
}

function renderStockRow(row) {
  const status = getStockStatus(row.balance);
  return `
    <div class="table-row" role="row">
      <span role="cell">${row.itemName}</span>
      <span role="cell">${row.warehouseName}</span>
      <span role="cell">${formatNumber(row.entries)} ${row.unit}</span>
      <span role="cell">${formatNumber(row.issues)} ${row.unit}</span>
      <span role="cell">${formatNumber(row.balance)} ${row.unit}</span>
      <span role="cell">${formatKardexDate(row.lastMovement)}</span>
      <span role="cell"><span class="chip ${row.balance > 0 ? "active" : "warning"}">${status}</span></span>
    </div>
  `;
}

function renderStockEmptyRow(hasMovements) {
  return `
    <div class="table-row" role="row">
      <span role="cell">${t("noRecords")}</span>
      <span role="cell">${hasMovements ? t("stockNoMatches") : t("stockEmptyTitle")}</span>
      <span role="cell">-</span>
      <span role="cell">-</span>
      <span role="cell">-</span>
      <span role="cell">${hasMovements ? t("stockNoMatchesDetail") : t("stockEmptyDetail")}</span>
    </div>
  `;
}

function getStockStatus(balance) {
  if (Number(balance || 0) > 0) return t("availableStatus");
  if (Number(balance || 0) < 0) return t("negativeStockStatus");
  return t("zeroStockStatus");
}

function getAvailableStock(itemKey, warehouseKey, unit) {
  const movements = mockDb.loadModuleRecords("almacenes", "movimientos").filter((record) => record.recordType === "inventoryMovement");
  const row = buildStockBalances(movements).find((stock) => {
    const matchesItem = stock.itemId === itemKey || stock.itemName === itemKey;
    const matchesWarehouse = stock.warehouseId === warehouseKey || stock.warehouseName === warehouseKey;
    return matchesItem && matchesWarehouse && stock.unit === unit;
  });
  return Number(row?.balance || 0);
}

function renderWarehouseComingSoonPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        <button class="primary-action disabled-action" type="button" disabled aria-disabled="true">
          <span>＋</span>
          <span>${t("comingSoon")}</span>
        </button>
      </div>

      <section class="section-card coming-soon-card">
        ${renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule))}
        <div class="coming-soon-content">
          <span class="muted-label">${t("mvpUnavailableLabel")}</span>
          <strong>${t("reservationsComingSoonTitle")}</strong>
          <p>${t("reservationsComingSoonDetail")}</p>
          <div class="compat-list">
            <article>
              <strong>${t("currentMvp")}</strong>
              <p>${t("reservationsCurrentMvp")}</p>
            </article>
            <article>
              <strong>${t("futureScope")}</strong>
              <p>${t("reservationsFutureScope")}</p>
            </article>
          </div>
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
}

function renderWarehouseKardexPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  if (getApiMode() === "api" && isInventoryApiEnabled() && state.inventoryItems.status === "idle") loadInventoryItemData();
  if (getApiMode() === "api" && isInventoryApiEnabled() && state.inventoryItems.status === "ready" && state.inventoryMovements.status === "idle") loadInventoryMovementData();
  const itemFilter = localStorage.getItem("erclave-kardex-item") || "all";
  const warehouseFilter = localStorage.getItem("erclave-kardex-warehouse") || "all";
  const search = localStorage.getItem("erclave-kardex-search") || "";
  const items = mockDb.loadModuleRecords(module.id, "articulos").filter((record) => record.recordType === "inventoryItem");
  const warehouses = mockDb.loadModuleRecords(module.id, "almacenes").filter((record) => record.recordType === "warehouse");
  const movements = mockDb.loadModuleRecords(module.id, "movimientos").filter((record) => record.recordType === "inventoryMovement");
  const entries = buildKardexEntries(movements);
  const filteredEntries = filterKardexEntries(entries, itemFilter, warehouseFilter, search);

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        <button class="primary-action disabled-action" type="button" disabled aria-disabled="true">
          <span>☷</span>
          <span>${t("readOnly")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule))}
        <p class="helper-copy">${t("kardexHelper")}</p>
        <div class="catalog-toolbar kardex-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="kardexSearch" type="search" value="${search}" placeholder="${t("searchKardex")}" />
          </label>
          <label class="preview-field compact-filter">
            <span>${t("item")}</span>
            <select id="kardexItemFilter" data-entity-selector>
              <option value="all">${t("allItems")}</option>
              ${items.map((item) => `<option value="${item.id}" ${selectedOption(itemFilter, item.id)}>${item.code} - ${item.title}</option>`).join("")}
            </select>
          </label>
          <label class="preview-field compact-filter">
            <span>${t("warehouse")}</span>
            <select id="kardexWarehouseFilter" data-entity-selector>
              <option value="all">${t("allWarehouses")}</option>
              ${warehouses.map((warehouse) => `<option value="${warehouse.id}" ${selectedOption(warehouseFilter, warehouse.id)}>${warehouse.code} - ${warehouse.title}</option>`).join("")}
            </select>
          </label>
        </div>
        <div class="data-table kardex-table" role="table">
          <div class="table-row table-head" role="row">
            <span role="columnheader">${t("movementDate")}</span>
            <span role="columnheader">${t("document")}</span>
            <span role="columnheader">${t("movementType")}</span>
            <span role="columnheader">${t("item")}</span>
            <span role="columnheader">${t("warehouse")}</span>
            <span role="columnheader">${t("entries")}</span>
            <span role="columnheader">${t("issues")}</span>
            <span role="columnheader">${t("balance")}</span>
          </div>
          ${filteredEntries.length ? filteredEntries.map(renderKardexRow).join("") : renderKardexEmptyRow(Boolean(movements.length))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  modulePanel.querySelector("#kardexItemFilter").addEventListener("change", (event) => {
    localStorage.setItem("erclave-kardex-item", event.target.value);
    render();
  });
  modulePanel.querySelector("#kardexWarehouseFilter").addEventListener("change", (event) => {
    localStorage.setItem("erclave-kardex-warehouse", event.target.value);
    render();
  });
  const kardexSearch = modulePanel.querySelector("#kardexSearch");
  kardexSearch.addEventListener("input", (event) => {
    localStorage.setItem("erclave-kardex-search", event.target.value);
    render();
    const nextSearch = modulePanel.querySelector("#kardexSearch");
    if (nextSearch) {
      nextSearch.focus();
      nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
    }
  });
}

function buildKardexEntries(movements) {
  const balances = new Map();
  return movements
    .slice()
    .sort((a, b) => getMovementTimestamp(a) - getMovementTimestamp(b))
    .map((record) => {
      const quantity = Number(record.fields?.quantity || 0);
      const unit = record.fields?.unit || "";
      const itemKey = record.fields?.itemId || record.fields?.item || record.title;
      const balanceKey = `${itemKey}-${unit}`;
      const previousBalance = balances.get(balanceKey) || 0;
      const signedQuantity = getMovementSignedQuantity(record.fields?.movementType, quantity);
      const nextBalance = previousBalance + signedQuantity;
      balances.set(balanceKey, nextBalance);
      return {
        record,
        entryQuantity: signedQuantity > 0 ? quantity : 0,
        issueQuantity: signedQuantity < 0 ? quantity : 0,
        balance: nextBalance,
        unit
      };
    })
    .reverse();
}

function filterKardexEntries(entries, itemFilter, warehouseFilter, search) {
  const normalizedSearch = search.trim().toLowerCase();
  return entries.filter(({ record }) => {
    const matchesItem = itemFilter === "all" || record.fields?.itemId === itemFilter;
    const matchesWarehouse = warehouseFilter === "all" || record.fields?.warehouseId === warehouseFilter;
    const matchesSearch = !normalizedSearch || [
      record.code,
      record.title,
      record.fields?.sourceDocument,
      record.fields?.item,
      record.fields?.warehouseName,
      translateMovementType(record.fields?.movementType),
      record.fields?.reason
    ]
      .join(" ")
      .toLowerCase()
      .includes(normalizedSearch);
    return matchesItem && matchesWarehouse && matchesSearch;
  });
}

function renderKardexRow(entry) {
  const { record, entryQuantity, issueQuantity, balance, unit } = entry;
  return `
    <div class="table-row" role="row">
      <span role="cell">${formatKardexDate(record.fields?.movementDate || record.createdAt)}</span>
      <span role="cell">${record.fields?.sourceDocument || record.code}</span>
      <span role="cell">${translateMovementType(record.fields?.movementType)}</span>
      <span role="cell">${record.title}</span>
      <span role="cell">${record.fields?.warehouseName || t("notDefined")}</span>
      <span role="cell">${entryQuantity ? `${formatNumber(entryQuantity)} ${unit}` : "-"}</span>
      <span role="cell">${issueQuantity ? `${formatNumber(issueQuantity)} ${unit}` : "-"}</span>
      <span role="cell">${formatNumber(balance)} ${unit}</span>
    </div>
  `;
}

function renderKardexEmptyRow(hasMovements) {
  return `
    <div class="table-row" role="row">
      <span role="cell">${t("noRecords")}</span>
      <span role="cell">${hasMovements ? t("kardexNoMatches") : t("kardexEmptyTitle")}</span>
      <span role="cell">-</span>
      <span role="cell">${hasMovements ? t("kardexNoMatchesDetail") : t("kardexEmptyDetail")}</span>
      <span role="cell">-</span>
      <span role="cell">-</span>
      <span role="cell">-</span>
      <span role="cell">-</span>
    </div>
  `;
}

function getMovementTimestamp(record) {
  return new Date(record.fields?.movementDate || record.createdAt || 0).getTime();
}

function getMovementSignedQuantity(type, quantity) {
  if (type === "entry" || type === "positiveAdjustment") return quantity;
  if (type === "exit" || type === "negativeAdjustment") return -quantity;
  return 0;
}

function formatKardexDate(value) {
  if (!value) return t("notDefined");
  return new Date(value).toLocaleDateString(state.lang === "en" ? "en-US" : "es-MX");
}

function renderSalesCustomersPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const search = localStorage.getItem("erclave-sales-customer-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const customers = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "customer");
  const filteredCustomers = normalizedSearch
    ? customers.filter((record) =>
        [
          record.code,
          record.title,
          record.status,
          record.owner,
          translateCustomerType(record.fields?.customerType),
          record.fields?.commercialName,
          record.fields?.contactName,
          record.fields?.contactEmail,
          record.fields?.contactPhone,
          record.fields?.salesOwner,
          record.fields?.billingLegalName,
          record.fields?.taxId,
          record.fields?.billingEmail,
          record.fields?.billingZipCode,
          record.fields?.billingCity,
          record.fields?.billingState
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch)
      )
    : customers;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        ${hasPermission("sales.customer.create") ? `<button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newCustomer")}</span>
        </button>` : ""}
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesCustomerSearch" type="search" value="${escapeAttribute(search)}" placeholder="${escapeAttribute(t("searchCustomers"))}" />
          </label>
        </div>
        <p class="helper-copy">${t("customerCatalogHelper")}</p>
        ${renderSalesReferenceWarnings()}
        <div class="catalog-grid">
          ${filteredCustomers.length ? filteredCustomers.map(renderSalesCustomerCard).join("") : renderSalesCustomerEmptyState(Boolean(search))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  const customerSearch = modulePanel.querySelector("#salesCustomerSearch");
  customerSearch.addEventListener("input", (event) => {
    localStorage.setItem("erclave-sales-customer-search", event.target.value);
    render();
    const nextSearch = modulePanel.querySelector("#salesCustomerSearch");
    if (nextSearch) {
      nextSearch.focus();
      nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
    }
  });
  bindProductionPanelActions();
}

function renderSalesCustomerCard(record) {
  return `
    <article class="catalog-card">
      <div class="catalog-card-main">
        <span class="muted-label">${escapeHtml(record.code)} - ${escapeHtml(translateCustomerType(record.fields?.customerType))}</span>
        <strong>${escapeHtml(record.title)}</strong>
        <p>${t("billingProfile")}: ${escapeHtml(record.fields?.billingLegalName || t("notDefined"))} - ${escapeHtml(record.fields?.taxId || t("notDefined"))}</p>
        <span class="muted-label">${t("contact")}: ${escapeHtml(record.fields?.contactName || t("notDefined"))} · ${escapeHtml(record.fields?.contactPhone || t("notDefined"))}</span>
        <span class="muted-label">${t("commercialEmail")}: ${escapeHtml(record.fields?.contactEmail || t("notDefined"))}</span>
        <span class="muted-label">${t("paymentTerms")}: ${escapeHtml(record.fields?.paymentTerms || t("notDefined"))} · ${t("creditLimit")}: ${escapeHtml(record.fields?.creditLimit || t("notDefined"))}</span>
        <span class="muted-label">${t("billingEmail")}: ${escapeHtml(record.fields?.billingEmail || t("notDefined"))}</span>
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Activo" ? "active" : record.status === "Bloqueado" ? "warning" : ""}">${escapeHtml(translateStatus(record.status))}</span>
        ${hasPermission("sales.customer.update") ? `<button class="secondary-action small-action" type="button" data-action="edit-sales-customer" data-record-id="${escapeAttribute(record.id)}">${t("edit")}</button>` : ""}
      </div>
    </article>
  `;
}

function renderSalesCustomerEmptyState(hasSearch = false) {
  return `
    <article class="catalog-card compact-card">
      <div>
        <span class="muted-label">${t("noRecords")}</span>
        <strong>${hasSearch ? t("customerNoMatchesTitle") : t("customerEmptyTitle")}</strong>
        <p>${hasSearch ? t("customerNoMatchesDetail") : t("customerEmptyDetail")}</p>
      </div>
    </article>
  `;
}

function renderSalesQuotesPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const search = localStorage.getItem("erclave-sales-quote-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const quotes = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "quote");
  const filteredQuotes = normalizedSearch
    ? quotes.filter((record) =>
        [
          record.code,
          record.title,
          record.status,
          record.owner,
          record.fields?.customerName,
          record.fields?.productServiceName,
          getQuoteLines(record).map((line) => line.productServiceName).join(" "),
          record.fields?.validUntil,
          record.fields?.paymentTerms,
          record.fields?.deliveryPromise,
          record.fields?.notes
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch)
      )
    : quotes;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        ${hasPermission("sales.quote.create") && hasPermission("sales.customer.read") ? `<button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newQuote")}</span>
        </button>` : ""}
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesQuoteSearch" type="search" value="${escapeAttribute(search)}" placeholder="${escapeAttribute(t("searchQuotes"))}" />
          </label>
        </div>
        <p class="helper-copy">${t("quoteCatalogHelper")}</p>
        ${renderSalesReferenceWarnings()}
        <div class="catalog-grid">
          ${filteredQuotes.length ? filteredQuotes.map(renderSalesQuoteCard).join("") : renderSalesQuoteEmptyState(Boolean(search))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  const quoteSearch = modulePanel.querySelector("#salesQuoteSearch");
  quoteSearch.addEventListener("input", (event) => {
    localStorage.setItem("erclave-sales-quote-search", event.target.value);
    render();
    const nextSearch = modulePanel.querySelector("#salesQuoteSearch");
    if (nextSearch) {
      nextSearch.focus();
      nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
    }
  });
  bindProductionPanelActions();
}

function renderSalesQuoteCard(record) {
  return `
    <article class="catalog-card">
      <div class="catalog-card-main">
        <span class="muted-label">${escapeHtml(record.code)} - ${escapeHtml(record.fields?.validUntil || t("notDefined"))} - ${getQuoteLines(record).length} ${t("quoteLines")}</span>
        <strong>${escapeHtml(record.title)}</strong>
        <p>${escapeHtml(getQuoteLines(record).map((line) => line.productServiceName).filter(Boolean).slice(0, 2).join(" / ") || t("notDefined"))}</p>
        <span class="muted-label">${t("customer")}: ${escapeHtml(record.fields?.customerName || t("notDefined"))}</span>
        <span class="muted-label">${t("quoteSubtotal")}: ${formatSalesMoney(record.fields?.subtotal,record.fields?.currency)}</span>
        <span class="muted-label">${t("quoteTotal")}: ${formatSalesMoney(record.fields?.total,record.fields?.currency)}</span>
        <span class="muted-label">${t("paymentTerms")}: ${escapeHtml(record.fields?.paymentTerms || t("notDefined"))}</span>
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Aprobado" ? "active" : record.status === "Vencida" ? "warning" : ""}">${escapeHtml(translateStatus(record.status))}</span>
        ${getApiMode()==="api"&&record.status==="Borrador"&&hasPermission("sales.quote.submit")?`<button class="secondary-action small-action" type="button" data-action="transition-sales-quote" data-transition="submit" data-record-id="${escapeAttribute(record.id)}">Emitir</button>`:""}
        ${getApiMode()==="api"&&record.status==="Cotizada"&&hasPermission("sales.quote.approve")?`<button class="secondary-action small-action" type="button" data-action="transition-sales-quote" data-transition="approve" data-record-id="${escapeAttribute(record.id)}">Aprobar</button>`:""}
        ${getApiMode()==="api"&&["Borrador","Cotizada"].includes(record.status)&&hasPermission("sales.quote.expire")?`<button class="secondary-action small-action" type="button" data-action="transition-sales-quote" data-transition="expire" data-record-id="${escapeAttribute(record.id)}">Vencer</button>`:""}
        ${getApiMode()==="api"&&["Borrador","Cotizada"].includes(record.status)&&hasPermission("sales.quote.cancel")?`<button class="secondary-action small-action" type="button" data-action="transition-sales-quote" data-transition="cancel" data-record-id="${escapeAttribute(record.id)}">Cancelar</button>`:""}
        <button class="secondary-action small-action" type="button" data-action="print-sales-quote" data-record-id="${escapeAttribute(record.id)}">${t("quotePdf")}</button>
        ${record.status==="Borrador"&&hasPermission("sales.quote.update")?`<button class="secondary-action small-action" type="button" data-action="edit-sales-quote" data-record-id="${escapeAttribute(record.id)}">${t("edit")}</button>`:""}
      </div>
    </article>
  `;
}

function renderSalesQuoteEmptyState(hasSearch = false) {
  return `
    <article class="catalog-card compact-card">
      <div>
        <span class="muted-label">${t("noRecords")}</span>
        <strong>${hasSearch ? t("quoteNoMatchesTitle") : t("quoteEmptyTitle")}</strong>
        <p>${hasSearch ? t("quoteNoMatchesDetail") : t("quoteEmptyDetail")}</p>
      </div>
    </article>
  `;
}

function renderSalesOrdersPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const search = localStorage.getItem("erclave-sales-order-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const orders = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "salesOrder");
  const filteredOrders = normalizedSearch
    ? orders.filter((record) =>
        [
          record.code,
          record.title,
          record.status,
          record.owner,
          record.fields?.quoteCode,
          record.fields?.customerName,
          getQuoteLines(record).map((line) => line.productServiceName).join(" "),
          record.fields?.deliveryPromise,
          record.fields?.fulfillmentMode
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch)
      )
    : orders;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        ${hasPermission("sales.order.create") && hasPermission("sales.quote.read") ? `<button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newSalesOrder")}</span>
        </button>` : ""}
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesOrderSearch" type="search" value="${escapeAttribute(search)}" placeholder="${escapeAttribute(t("searchSalesOrders"))}" />
          </label>
        </div>
        <p class="helper-copy">${t("salesOrderHelper")}</p>
        <div class="catalog-grid">
          ${filteredOrders.length ? filteredOrders.map(renderSalesOrderCard).join("") : renderSalesOrderEmptyState(Boolean(search))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  const orderSearch = modulePanel.querySelector("#salesOrderSearch");
  orderSearch.addEventListener("input", (event) => {
    localStorage.setItem("erclave-sales-order-search", event.target.value);
    render();
    const nextSearch = modulePanel.querySelector("#salesOrderSearch");
    if (nextSearch) {
      nextSearch.focus();
      nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
    }
  });
  bindProductionPanelActions();
}

function renderSalesOrderCard(record) {
  const adjustments = record.fields?.adjustments || [];
  const lastAdjustment = adjustments[0];
  return `
    <article class="catalog-card">
      <div class="catalog-card-main">
        <span class="muted-label">${escapeHtml(record.code)} - ${escapeHtml(record.fields?.quoteCode || t("notDefined"))} - ${getQuoteLines(record).length} ${t("quoteLines")}</span>
        <strong>${escapeHtml(record.title)}</strong>
        <p>${escapeHtml(getQuoteLines(record).map((line) => line.productServiceName).filter(Boolean).slice(0, 2).join(" / ") || t("notDefined"))}</p>
        <span class="muted-label">${t("customer")}: ${escapeHtml(record.fields?.customerName || t("notDefined"))}</span>
        <span class="muted-label">${t("deliveryPromise")}: ${escapeHtml(record.fields?.deliveryPromise || t("notDefined"))} · ${t("fulfillmentMode")}: ${escapeHtml(record.fields?.fulfillmentMode || t("notDefined"))}</span>
        <span class="muted-label">${t("quoteTotal")}: ${formatCurrency(Number(record.fields?.total || 0))} · ${t("estimatedCost")}: ${formatCurrency(Number(record.fields?.estimatedCost || 0))}</span>
        <span class="muted-label">${t("estimatedMargin")}: ${formatNumber(Number(record.fields?.estimatedMargin || 0))}%</span>
        <div class="product-history">
          <div class="product-history-head">
            <span class="muted-label">${t("orderAdjustments")}</span>
            <strong>${adjustments.length}</strong>
          </div>
          <p>${lastAdjustment ? `${escapeHtml(formatKardexDate(lastAdjustment.changedAt))} - ${escapeHtml(lastAdjustment.reason)}` : t("noOrderAdjustments")}</p>
        </div>
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Aprobado" ? "active" : record.status === "Cancelado" ? "warning" : ""}">${escapeHtml(translateStatus(record.status))}</span>
        ${getApiMode() !== "api" || hasPermission("sales.order.fulfill") || hasPermission("sales.order.cancel") ? `<button class="secondary-action small-action" type="button" data-action="edit-sales-order" data-record-id="${escapeAttribute(record.id)}">${getApiMode() === "api" ? "Gestionar surtido" : t("edit")}</button>` : ""}
      </div>
    </article>
  `;
}

function renderSalesOrderEmptyState(hasSearch = false) {
  return `
    <article class="catalog-card compact-card">
      <div>
        <span class="muted-label">${t("noRecords")}</span>
        <strong>${hasSearch ? t("salesOrderNoMatchesTitle") : t("salesOrderEmptyTitle")}</strong>
        <p>${hasSearch ? t("salesOrderNoMatchesDetail") : t("salesOrderEmptyDetail")}</p>
      </div>
    </article>
  `;
}

function renderSalesDeliveriesPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const search = localStorage.getItem("erclave-sales-delivery-search") || "";
  const statusFilter = localStorage.getItem("erclave-sales-delivery-status") || "all";
  const normalizedSearch = search.trim().toLowerCase();
  const orders = mockDb.loadModuleRecords(module.id, "pedidos").filter((record) => record.recordType === "salesOrder" && !["Entregado", "Cancelado"].includes(record.status));
  const deliveries = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "salesDelivery");
  const ordersById = new Map(orders.map((order) => [order.id, order]));
  const filteredDeliveries = deliveries
    .filter((delivery) => statusFilter === "all" || delivery.fields?.deliveryStatus === statusFilter)
    .filter((delivery) => {
      const order = ordersById.get(delivery.fields?.orderId);
      return !normalizedSearch || [
        delivery.code,
        delivery.status,
        delivery.title,
        delivery.owner,
        delivery.fields?.orderCode,
        delivery.fields?.quoteCode,
        delivery.fields?.customerName,
        delivery.fields?.deliveryStatus,
        delivery.fields?.recipient,
        delivery.fields?.deliveryReference,
        delivery.fields?.notes,
        order?.status,
        order?.fields?.fulfillmentMode
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedSearch);
    })
    .sort((a, b) => new Date(b.fields?.deliveryDate || b.createdAt || 0) - new Date(a.fields?.deliveryDate || a.createdAt || 0));

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        ${hasPermission("sales.delivery.create") ? `<button class="primary-action" type="button" data-action="register-sales-delivery">
          <span>＋</span><span>${t("newDelivery")}</span>
        </button>` : ""}
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar kardex-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesDeliverySearch" type="search" value="${escapeAttribute(search)}" placeholder="${escapeAttribute(t("searchDeliveries"))}" />
          </label>
          <label class="preview-field compact-filter">
            <span>${t("deliveryStatus")}</span>
            <select id="salesDeliveryStatusFilter">
              <option value="all">${t("allDeliveryStatuses")}</option>
              ${getDeliveryStatusOptions().map((status) => `<option value="${status}" ${selectedOption(statusFilter, status)}>${translateStatus(status)}</option>`).join("")}
            </select>
          </label>
        </div>
        <p class="helper-copy">${t("deliveryHelper")}</p>
        <div class="catalog-grid">
          ${filteredDeliveries.length ? filteredDeliveries.map((delivery) => renderSalesDeliveryCard(delivery, ordersById.get(delivery.fields?.orderId))).join("") : renderSalesDeliveryEmptyState(Boolean(search), Boolean(deliveries.length))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  const deliverySearch = modulePanel.querySelector("#salesDeliverySearch");
  deliverySearch.addEventListener("input", (event) => {
    localStorage.setItem("erclave-sales-delivery-search", event.target.value);
    render();
    const nextSearch = modulePanel.querySelector("#salesDeliverySearch");
    if (nextSearch) {
      nextSearch.focus();
      nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
    }
  });
  modulePanel.querySelector("#salesDeliveryStatusFilter").addEventListener("change", (event) => {
    localStorage.setItem("erclave-sales-delivery-status", event.target.value);
    render();
  });
  modulePanel.querySelectorAll("[data-action='view-delivery-quote']").forEach((element) => {
    element.addEventListener("click", (event) => {
      event.stopPropagation();
      const quoteId = element.dataset.quoteId;
      if (!quoteId) {
        showToast(t("quoteNotFound"));
        return;
      }
      openSalesQuotePrintModal(quoteId);
    });
  });
  modulePanel.querySelectorAll("[data-action='confirm-api-delivery']").forEach(button=>button.addEventListener("click",async event=>{event.stopPropagation();try{await confirmSalesDelivery(button.dataset.deliveryId,"Entrega confirmada con evidencia comercial.");await loadSalesApiData();showToast(state.lang==="en"?"Delivery confirmed and reservations consumed.":"Entrega confirmada y reservas consumidas.","success");}catch(error){showApiError(error,state.lang==="en"?"The delivery could not be confirmed.":"No se pudo confirmar la entrega.");}}));
  modulePanel.querySelectorAll("[data-action='cancel-api-delivery']").forEach(button=>button.addEventListener("click",async event=>{event.stopPropagation();try{await cancelSalesDelivery(button.dataset.deliveryId,"Entrega cancelada por el usuario.");await loadSalesApiData();showToast(state.lang==="en"?"Delivery cancelled.":"Entrega cancelada.","success");}catch(error){showApiError(error,state.lang==="en"?"The delivery could not be cancelled.":"No se pudo cancelar la entrega.");}}));
  bindProductionPanelActions();
}

function getPendingFinishedGoodsReceipts(){
  const summaries=Object.fromEntries((state.finishedGoodsReceipts.summaries||[]).map((item)=>[item.production_order_id,Number(item.received_quantity||0)]));
  const products=Object.fromEntries((state.finishedGoodsReceipts.products||[]).map((item)=>[item.id,item]));
  const items=Object.fromEntries(mockDb.loadModuleRecords("almacenes","articulos").filter((item)=>item.recordType==="inventoryItem").map((item)=>[item.id,item]));
  return (state.finishedGoodsReceipts.orders||[]).map((order)=>{const product=products[order.product_service_id];const item=product?.inventory_item_id?items[product.inventory_item_id]:null;const received=summaries[order.id]||0;return {order,product,item,received,remaining:Math.max(0,Number(order.quantity||0)-received)};}).filter((row)=>row.remaining>0.000001);
}
function renderPendingFinishedGoodsReceipt(row){
  const blocked=!row.product?.inventory_item_id||!row.item||row.item.status!=="Activo"||row.item.fields?.type!=="finishedGood";
  return `<article class="record-row"><div class="record-main"><strong>${escapeHtml(row.order.code)} · ${escapeHtml(row.product?.name||row.order.product_service_id)}</strong><span>${t("finishedGoodsPendingDetail",{received:formatNumber(row.received),remaining:formatNumber(row.remaining),quantity:formatNumber(row.order.quantity),unit:row.order.unit})}</span><span>${blocked?t("finishedGoodsMappingBlocked"):`${escapeHtml(row.item.code)} · ${escapeHtml(row.item.title)}`}</span></div>${blocked?`<span class="chip warning">${t("blockedStatus")}</span>`:hasPermission("inventory.finished_goods_receipt.receive")?`<button class="primary-action small-action" type="button" data-action="receive-finished-good" data-order-id="${escapeAttribute(row.order.id)}">${t("receiveFinishedGood")}</button>`:""}</article>`;
}

function renderSalesDeliveryCard(delivery, order = null) {
  const deliveryStatus = delivery.fields?.deliveryStatus || delivery.status;
  const quoteId = order?.fields?.quoteId || findSalesQuoteByCode(delivery.fields?.quoteCode)?.id || "";
  return `
    <article class="catalog-card clickable-card" data-action="view-delivery-quote" data-quote-id="${escapeAttribute(quoteId)}">
      <div class="catalog-card-main">
        <span class="muted-label">${escapeHtml(delivery.code)} - ${escapeHtml(delivery.fields?.orderCode || t("notDefined"))} - ${escapeHtml(delivery.fields?.quoteCode || t("notDefined"))}</span>
        <strong>${escapeHtml(delivery.title)}</strong>
        <p>${escapeHtml(delivery.fields?.customerName || t("notDefined"))}</p>
        <span class="muted-label">${t("deliveryStatus")}: ${escapeHtml(translateStatus(deliveryStatus))} · ${t("salesOrderStatus")}: ${escapeHtml(translateStatus(order?.status || t("notDefined")))}</span>
        <span class="muted-label">${t("deliveryDate")}: ${escapeHtml(delivery.fields?.deliveryDate || t("notDefined"))} · ${t("recipient")}: ${escapeHtml(delivery.fields?.recipient || t("notDefined"))}</span>
        <span class="muted-label">${t("deliveryReference")}: ${escapeHtml(delivery.fields?.deliveryReference || t("notDefined"))}</span>
        ${delivery.fields?.notes ? `<p>${escapeHtml(delivery.fields.notes)}</p>` : ""}
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${getDeliveryTone(deliveryStatus)}">${translateStatus(deliveryStatus)}</span>
        ${getApiMode()==="api"&&deliveryStatus==="Pendiente de entrega"&&hasPermission("sales.delivery.confirm")?`<button class="primary-action small-action" type="button" data-action="confirm-api-delivery" data-delivery-id="${escapeAttribute(delivery.id)}">Confirmar</button>`:""}
        ${getApiMode()==="api"&&deliveryStatus==="Pendiente de entrega"&&hasPermission("sales.delivery.cancel")?`<button class="secondary-action small-action" type="button" data-action="cancel-api-delivery" data-delivery-id="${escapeAttribute(delivery.id)}">Cancelar</button>`:""}
        <button class="secondary-action small-action" type="button" data-action="view-delivery-quote" data-quote-id="${quoteId}">${t("viewQuote")}</button>
      </div>
    </article>
  `;
}

function renderSalesDeliveryEmptyState(hasSearch = false, hasDeliveries = false) {
  return `
    <article class="catalog-card compact-card">
      <div>
        <span class="muted-label">${t("noRecords")}</span>
        <strong>${hasSearch || hasDeliveries ? t("deliveryNoMatchesTitle") : t("deliveryEmptyTitle")}</strong>
        <p>${hasSearch || hasDeliveries ? t("deliveryNoMatchesDetail") : t("deliveryEmptyDetail")}</p>
      </div>
    </article>
  `;
}

function getDeliveriesForOrder(orderId, deliveries = mockDb.loadModuleRecords("ventas", "entregas").filter((record) => record.recordType === "salesDelivery")) {
  return deliveries
    .filter((delivery) => delivery.fields?.orderId === orderId)
    .sort((a, b) => new Date(b.fields?.deliveryDate || b.createdAt || 0) - new Date(a.fields?.deliveryDate || a.createdAt || 0));
}

function getSalesActualCostSourceLabel(source) {
  const labels = {
    inventory_consumption: t("inventoryConsumptionCostSource"),
    service_capture: t("serviceCaptureCostSource"),
    production_report: t("productionReportCostSource")
  };
  return labels[source] || source;
}

function renderSalesMarginPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const canReadOrders = hasPermission("sales.order.read");
  const canReadDeliveries = hasPermission("sales.delivery.read");
  const orders = canReadOrders
    ? mockDb.loadModuleRecords(module.id, "pedidos").filter((record) => record.recordType === "salesOrder")
    : [];
  const deliveries = canReadDeliveries
    ? mockDb.loadModuleRecords(module.id, "entregas").filter((record) => record.recordType === "salesDelivery")
    : [];
  const ordersWithActualMargin = orders.filter((record) => record.fields?.actualMargin != null);
  const pendingActualMargin = orders.length - ordersWithActualMargin.length;

  const cards = orders.map((record) => {
    const currency = record.fields?.currency || "MXN";
    const relatedDeliveries = getDeliveriesForOrder(record.id, deliveries);
    const actualCostSources = [...new Set(relatedDeliveries
      .flatMap((delivery) => delivery.fields?.lines || [])
      .map((line) => line.actualCostSource)
      .filter(Boolean))]
      .map(getSalesActualCostSourceLabel);
    const hasActualMargin = record.fields?.actualMargin != null;
    const statusTone = record.status === "Entregado" ? "active" : record.status === "Cancelado" ? "danger" : "warning";
    return `
      <article class="catalog-card sales-margin-card">
        <div class="catalog-card-main">
          <span class="muted-label">${escapeHtml(record.code)} &middot; ${escapeHtml(record.fields?.quoteCode || t("notDefined"))}</span>
          <strong>${escapeHtml(record.fields?.customerName || record.title)}</strong>
          <p>${t("salesMarginRevenue")}: ${formatSalesMoney(record.fields?.total, currency)}</p>
          <span class="muted-label">${t("estimatedCost")}: ${record.fields?.estimatedCost == null ? t("notDefined") : formatSalesMoney(record.fields.estimatedCost, currency)} &middot; ${t("estimatedMargin")}: ${record.fields?.estimatedMargin == null ? t("notDefined") : `${formatNumber(record.fields.estimatedMargin)}%`}</span>
          <span class="muted-label">${t("actualCost")}: ${record.fields?.actualCost == null ? t("actualCostPending") : formatSalesMoney(record.fields.actualCost, currency)} &middot; ${t("actualMargin")}: ${hasActualMargin ? `${formatNumber(record.fields.actualMargin)}%` : t("actualMarginPending")}</span>
          <span class="muted-label">${t("actualCostSource")}: ${actualCostSources.length ? escapeHtml(actualCostSources.join(" / ")) : t("actualCostSourcePending")}</span>
        </div>
        <div class="catalog-card-actions">
          <span class="chip ${statusTone}">${escapeHtml(translateStatus(record.status))}</span>
          <span class="chip ${hasActualMargin ? "active" : "warning"}">${hasActualMargin ? t("actualMarginAvailable") : t("actualMarginPending")}</span>
        </div>
      </article>
    `;
  }).join("");

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${label} / ${t("submodule")}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-module">${t("overview")}</button>
    </div>
    <section class="submodule-screen sales-margin-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${t("salesMarginReadOnlyHelp")}</p>
        </div>
      </div>
      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="cost-summary-grid sales-margin-summary">
          <article><span>${t("salesMarginOrdersReviewed")}</span><strong>${orders.length}</strong></article>
          <article><span>${t("salesMarginActualAvailable")}</span><strong>${ordersWithActualMargin.length}</strong></article>
          <article><span>${t("salesMarginActualPending")}</span><strong>${pendingActualMargin}</strong></article>
        </div>
        <div class="inline-actions">
          ${canReadOrders ? `<button class="secondary-action" type="button" data-sales-margin-target="pedidos">${t("reviewSalesOrders")}</button>` : ""}
          ${canReadDeliveries ? `<button class="secondary-action" type="button" data-sales-margin-target="entregas">${t("reviewSalesDeliveries")}</button>` : ""}
        </div>
        ${canReadOrders
          ? `<div class="catalog-grid">${cards || `<p class="helper-copy">${t("salesMarginEmpty")}</p>`}</div>`
          : `<p class="helper-copy">${t("salesMarginPermissionDenied")}</p>`}
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']")?.addEventListener("click", () => navigateTo({ active: "ventas", activeSubmodule: null, laborArea: "" }));
  modulePanel.querySelectorAll("[data-sales-margin-target]").forEach((button) => button.addEventListener("click", () => navigateTo({ active: "ventas", activeSubmodule: button.dataset.salesMarginTarget, laborArea: "" })));
}

function findSalesQuoteByCode(code) {
  const normalizedCode = String(code || "").trim().toLowerCase();
  if (!normalizedCode) return null;
  return mockDb.loadModuleRecords("ventas", "cotizaciones")
    .find((record) => record.recordType === "quote" && record.code.toLowerCase() === normalizedCode);
}

function getDeliveryTone(status) {
  if (status === "Entregado") return "active";
  if (status === "Entrega parcial" || status === "En ruta" || status === "Reprogramado") return "warning";
  if (status === "No entregado" || status === "Cancelado") return "danger";
  return "";
}

function renderMovementRow(record) {
  return `
    <div class="table-row" role="row">
      <span role="cell">${record.code}</span>
      <span role="cell">${translateMovementType(record.fields?.movementType)}</span>
      <span role="cell">${record.title}</span>
      <span role="cell">${record.fields?.quantity || "0"} ${record.fields?.unit || ""}</span>
    </div>
  `;
}

function renderMovementRecord(record) {
  return `
    <article class="record-row">
      <div class="record-main">
        <strong>${record.code}</strong>
        <span>${translateMovementType(record.fields?.movementType)} - ${record.title} - ${record.fields?.warehouseName || t("notDefined")}</span>
      </div>
      <span class="chip ${getMovementTone(record.fields?.movementType)}">${translateStatus(record.status)}</span>
    </article>
  `;
}

function getOrderRecipe(order) {
  return order.recipeSnapshot || mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
}

function formatRecipeDisplayLabel(recipe) {
  const product = recipe?.productServiceId ? mockDb.findProductService(recipe.productServiceId) : null;
  const name = product?.name || recipe?.product || t("recipeProductUnavailable");
  const productLabel = product?.sku ? `${name} - ${product.sku}` : name;
  return recipe?.code ? `${recipe.code} · ${productLabel}` : productLabel;
}

function createRecipeSnapshot(recipe) {
  return {
    id: recipe.id,
    code: recipe.code || "",
    productServiceId: recipe.productServiceId || "",
    product: recipe.product,
    version: recipe.version,
    quantityBase: recipe.quantityBase,
    suggestedDurationDays: recipe.suggestedDurationDays || 1,
    unit: recipe.unit,
    status: recipe.status,
    approvalStatus: getRecipeApprovalStatus(recipe),
    approvedBy: recipe.approvedBy || "",
    approvedAt: recipe.approvedAt || "",
    changeReason: recipe.changeReason || "",
    center: recipe.center,
    resources: (recipe.resources || []).map((resource) => ({ ...resource })),
    steps: [...(recipe.steps || [])],
    stageDefinitions: (recipe.stageDefinitions || []).map((stage) => ({ ...stage }))
  };
}

function getGenericSubmodule(module, id) {
  return normalizeSubmodules(module).find((item) => item.id === id) || normalizeSubmodules(module)[0];
}

function buildGenericSubmoduleRows(module, submodule) {
  const savedRows = getSavedModuleTableRows(module, submodule.id);
  if (savedRows.length) return savedRows;
  if (!shouldUseSeedModuleData()) return [];
  if (state.lang === "en") {
    return (submodule.focus.length ? submodule.focus : [submodule.name]).slice(0, 3).map((item, index) => [
      item,
      submodule.detail,
      index === 0 ? "Required" : "Recommended",
      state.lang === "en" ? module.titleEn : module.title
    ]);
  }
  if (module.table.rows?.length) return module.table.rows;
  return [
    [submodule.name, submodule.detail, t("recommendedRecords"), module.status]
  ];
}

function getGenericSubmoduleColumns(module) {
  if (module.id === "almacenes" && state.activeSubmodule === "almacenes") {
    return state.lang === "en" ? ["Warehouse", "Type", "Location", "Status"] : ["Almacen", "Tipo", "Ubicacion", "Estado"];
  }
  if (state.lang === "en") return ["Item", "Detail", "Status", "Area"];
  return module.table.columns;
}

function getGenericSubmoduleForm(module, submodule) {
  if (state.lang === "en") {
    return [
      ["Reference", submodule.name],
      ["Owner", module.titleEn],
      ["Status", "Draft"],
      ["Notes", "Recommended ERP setup"]
    ];
  }
  return module.form;
}

function getGenericFlowGuide(module, submodule) {
  if (module.id === "almacenes") return renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule));
  if (module.id === "ventas") return renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule));
  return "";
}

function getGenericSubmoduleIntegrations(module) {
  if (state.lang === "en") {
    return module.validations.map(([name]) => [
      translateModuleName(name),
      `Keeps ${module.titleEn.toLowerCase()} synchronized with ${translateModuleName(name).toLowerCase()} documents and operational status.`
    ]);
  }
  return module.validations;
}

function getGenericSubmoduleRecords(module, submodule) {
  const savedRecords = getSavedModuleRecordRows(module, submodule.id);
  if (savedRecords.length) return savedRecords;
  if (!shouldUseSeedModuleData()) return [];
  if (state.lang === "en") {
    return [
      [submodule.id.toUpperCase(), submodule.detail, t("recommendedRecords")],
      [`${module.icon}-FLOW`, "Suggested operating flow and validations.", "Ready"],
      [`${module.icon}-SYNC`, "Recommended integration with related modules.", "Draft"]
    ];
  }
  return module.records.length ? module.records : [[submodule.id.toUpperCase(), submodule.detail, t("recommendedRecords")]];
}

function getSavedModuleTableRows(module, submoduleId = "") {
  return mockDb.loadModuleRecords(module.id, submoduleId).map((record) => {
    const submodule = getGenericSubmodule(module, record.submoduleId);
    if (record.recordType === "warehouse") {
      return [
        record.code,
        translateWarehouseType(record.fields?.type) || record.title,
        record.fields?.location || submodule.name,
        translateStatus(record.status)
      ];
    }
    return [
      record.code,
      record.title,
      translateStatus(record.status),
      submodule.name
    ];
  });
}

function getSavedModuleRecordRows(module, submoduleId = "") {
  return mockDb.loadModuleRecords(module.id, submoduleId).map((record) => [
    record.code,
    record.recordType === "warehouse" ? `${record.title} - ${record.fields?.location || record.detail}` : record.detail,
    translateStatus(record.status)
  ]);
}

function isWarehouseMasterSubmodule(module, submodule) {
  return module?.id === "almacenes" && submodule?.id === "almacenes";
}

function isWarehouseItemsSubmodule(module, submodule) {
  return module?.id === "almacenes" && submodule?.id === "articulos";
}

function isWarehouseMovementSubmodule(module, submodule) {
  return module?.id === "almacenes" && submodule?.id === "movimientos";
}

function isWarehouseStockSubmodule(module, submodule) {
  return module?.id === "almacenes" && submodule?.id === "existencias";
}

function isWarehouseReservationsSubmodule(module, submodule) {
  return module?.id === "almacenes" && submodule?.id === "reservas";
}

function isWarehouseKardexSubmodule(module, submodule) {
  return module?.id === "almacenes" && submodule?.id === "kardex";
}

function isSalesCustomersSubmodule(module, submodule) {
  return module?.id === "ventas" && submodule?.id === "clientes";
}

function isSalesQuotesSubmodule(module, submodule) {
  return module?.id === "ventas" && submodule?.id === "cotizaciones";
}

function isSalesOrdersSubmodule(module, submodule) {
  return module?.id === "ventas" && submodule?.id === "pedidos";
}

function isSalesDeliveriesSubmodule(module, submodule) {
  return module?.id === "ventas" && submodule?.id === "entregas";
}

function isSalesMarginSubmodule(module, submodule) {
  return module?.id === "ventas" && submodule?.id === "margen";
}

function translateWarehouseType(type) {
  const typeMap = {
    rawMaterials: t("rawMaterials"),
    tools: t("toolsWarehouse"),
    workInProcess: t("workInProcess"),
    finishedGoods: t("finishedGoods"),
    scrap: t("scrapWarehouse"),
    spareParts: t("spareParts")
  };
  return typeMap[type] || type;
}

function translateInventoryPolicy(policy) {
  const policyMap = {
    standard: t("standardPolicy"),
    batch: t("batchPolicy"),
    lot: t("batchPolicy"),
    serial: t("serialPolicy"),
    restricted: t("restrictedPolicy")
  };
  return policyMap[policy] || policy || t("notDefined");
}

function translateInventoryItemType(type) {
  const typeMap = {
    rawMaterial: t("rawMaterialItem"),
    raw_material: t("rawMaterialItem"),
    consumable: t("consumableItem"),
    tool: t("toolItem"),
    finishedGood: t("finishedGoodItem"),
    finished_goods: t("finishedGoodItem"),
    sparePart: t("sparePartItem"),
    spare_part: t("sparePartItem"),
    serviceSupply: t("serviceSupplyItem"),
    supply: t("serviceSupplyItem")
  };
  return typeMap[type] || type || t("notDefined");
}

function translateMovementType(type) {
  const typeMap = {
    entry: t("entryMovement"),
    exit: t("exitMovement"),
    transfer: t("transferMovement"),
    positiveAdjustment: t("positiveAdjustment"),
    negativeAdjustment: t("negativeAdjustment")
  };
  return typeMap[type] || type || t("notDefined");
}

function translateCustomerType(type) {
  const typeMap = {
    company: t("companyCustomer"),
    individual: t("individualCustomer"),
    government: t("governmentCustomer"),
    internal: t("internalCustomer")
  };
  return typeMap[type] || type || t("notDefined");
}

function getMovementTone(type) {
  if (type === "exit" || type === "negativeAdjustment") return "warning";
  if (type === "entry" || type === "positiveAdjustment") return "active";
  return "";
}

function translateYesNo(value) {
  if (value === "yes") return t("yes");
  if (value === "no") return t("no");
  return t("notDefined");
}

function getPhysicalLocationCode(fields = {}) {
  return [fields.zone, fields.aisle, fields.rack, fields.level, fields.position].filter(Boolean).join("-");
}

function getWarehouseFlowTitle(submodule) {
  if (state.lang === "en") return `${submodule.name} flow`;
  return `Flujo de ${submodule.name}`;
}

function getSalesFlowTitle(submodule) {
  if (state.lang === "en") return `${submodule.name} flow`;
  return `Flujo de ${submodule.name}`;
}

function getWarehouseFlowSteps(submodule) {
  const steps = {
    es: {
      almacenes: [
        ["Alta", "Registrar codigo, tipo, responsable y politica."],
        ["Espacio fisico", "Configurar zona, pasillo, rack, nivel o posicion si aplica."],
        ["Activacion", "Dejar disponible para existencias, reservas y movimientos."],
        ["Operacion", "Usarlo como origen o destino en inventario."]
      ],
      articulos: [
        ["Alta", "Registrar SKU, nombre, tipo, unidad y almacen sugerido."],
        ["Control", "Definir minimos, maximos, politica y estatus."],
        ["Permisos", "Restringir creacion y edicion a roles autorizados."],
        ["Operacion", "Usarlo como articulo valido en movimientos y reservas."]
      ],
      movimientos: [
        ["Documento", "Capturar tipo y referencia origen."],
        ["Articulo", "Indicar cantidad, almacen y ubicacion."],
        ["Validacion", "Revisar existencia o recepcion."],
        ["Kardex", "Registrar movimiento auditable."]
      ],
      existencias: [
        ["Movimientos", "Tomar entradas, salidas y ajustes registrados."],
        ["Saldo", "Calcular disponibilidad por articulo, almacen y unidad."],
        ["Riesgo", "Detectar saldos cero o negativos."],
        ["Accion", "Corregir solo con nuevos movimientos o ajustes."]
      ],
      reservas: [
        ["Solicitud", "Relacionar orden, pedido o transferencia."],
        ["Disponibilidad", "Confirmar cantidad disponible."],
        ["Reserva", "Apartar inventario."],
        ["Liberacion", "Consumir, entregar o cancelar reserva."]
      ],
      kardex: [
        ["Articulo", "Seleccionar articulo, lote o serie."],
        ["Periodo", "Filtrar fechas y almacen."],
        ["Historial", "Consultar entradas, salidas y ajustes."],
        ["Auditoria", "Revisar documento origen y responsable."]
      ]
    },
    en: {
      almacenes: [
        ["Create", "Register code, type, owner, and policy."],
        ["Physical space", "Configure zone, aisle, rack, level, or position if needed."],
        ["Activate", "Make it available for stock, reservations, and movements."],
        ["Operate", "Use it as inventory origin or destination."]
      ],
      articulos: [
        ["Create", "Register SKU, name, type, unit, and suggested warehouse."],
        ["Control", "Define min, max, policy, and status."],
        ["Permissions", "Restrict create and edit actions to authorized roles."],
        ["Operate", "Use it as a valid item for movements and reservations."]
      ],
      movimientos: [
        ["Document", "Capture type and source reference."],
        ["Item", "Enter quantity, warehouse, and location."],
        ["Validation", "Check stock or receipt."],
        ["Kardex", "Register an auditable movement."]
      ],
      existencias: [
        ["Movements", "Use registered receipts, issues, and adjustments."],
        ["Balance", "Calculate availability by item, warehouse, and unit."],
        ["Risk", "Detect zero or negative balances."],
        ["Action", "Correct only through new movements or adjustments."]
      ],
      reservas: [
        ["Request", "Link order, sales order, or transfer."],
        ["Availability", "Confirm available quantity."],
        ["Reserve", "Hold inventory."],
        ["Release", "Consume, deliver, or cancel reservation."]
      ],
      kardex: [
        ["Item", "Select item, lot, or serial."],
        ["Period", "Filter dates and warehouse."],
        ["History", "Review receipts, issues, and adjustments."],
        ["Audit", "Check source document and owner."]
      ]
    }
  };
  const localeSteps = steps[state.lang]?.[submodule.id] || steps.es[submodule.id] || steps.es.almacenes;
  return localeSteps.map(([title, detail]) => ({ title, detail }));
}

function getSalesFlowSteps(submodule) {
  const steps = {
    es: {
      clientes: [
        ["Alta", "Registrar perfil comercial y datos de contacto."],
        ["Facturacion", "Capturar razon social, RFC y direccion fiscal."],
        ["Validacion", "Revisar condiciones, credito y estatus."],
        ["Operacion", "Usarlo en cotizaciones, pedidos y facturacion."]
      ],
      cotizaciones: [
        ["Cliente", "Seleccionar cliente dado de alta."],
        ["Producto o servicio", "Seleccionar catalogo existente de Produccion."],
        ["Importe", "Capturar cantidad, precio, descuento y vigencia."],
        ["Seguimiento", "Guardar como borrador, cotizada, aprobada o vencida."]
      ],
      pedidos: [
        ["Aprobacion", "Convertir cotizacion aceptada o registrar pedido."],
        ["Disponibilidad", "Validar inventario o necesidad de produccion."],
        ["Compromiso", "Preparar entrega, reserva futura o solicitud productiva."],
        ["Cierre", "Actualizar estado comercial y margen."]
      ],
      entregas: [
        ["Pedido", "Seleccionar pedido aprobado."],
        ["Salida", "Preparar entrega parcial o total."],
        ["Evidencia", "Capturar comprobante o referencia logistica."],
        ["Impacto", "Actualizar inventario, cliente y margen."]
      ],
      margen: [
        ["Venta", "Seleccionar cliente, producto o pedido."],
        ["Costo", "Comparar costo estimado contra real."],
        ["Variacion", "Identificar descuento, flete, merma o reproceso."],
        ["Decision", "Revisar rentabilidad por cliente o producto."]
      ]
    },
    en: {
      clientes: [
        ["Create", "Register commercial profile and contact data."],
        ["Billing", "Capture legal name, tax ID, and fiscal address."],
        ["Validate", "Review terms, credit, and status."],
        ["Operate", "Use it in quotes, orders, and billing."]
      ],
      cotizaciones: [
        ["Customer", "Select a registered customer."],
        ["Product or service", "Select an existing Production catalog item."],
        ["Amount", "Enter quantity, price, discount, and validity."],
        ["Follow-up", "Save as draft, quoted, approved, or expired."]
      ],
      pedidos: [
        ["Approval", "Convert accepted quote or register order."],
        ["Availability", "Validate stock or production need."],
        ["Commitment", "Prepare delivery, future reservation, or production request."],
        ["Close", "Update commercial status and margin."]
      ],
      entregas: [
        ["Order", "Select approved order."],
        ["Issue", "Prepare partial or full delivery."],
        ["Evidence", "Capture proof or logistics reference."],
        ["Impact", "Update inventory, customer, and margin."]
      ],
      margen: [
        ["Sale", "Select customer, product, or order."],
        ["Cost", "Compare estimated and actual cost."],
        ["Variance", "Identify discount, freight, scrap, or rework."],
        ["Decision", "Review profitability by customer or product."]
      ]
    }
  };
  const localeSteps = steps[state.lang]?.[submodule.id] || steps.es[submodule.id] || steps.es.clientes;
  return localeSteps.map(([title, detail]) => ({ title, detail }));
}

function translateModuleName(name) {
  const match = modules.find((module) => module.title === name || module.titleEn === name);
  const aliases = {
    Todos: "All modules",
    Administracion: "Administration"
  };
  return match ? match.titleEn : aliases[name] || name;
}

function renderProductionSubmodulePanel(module) {
  const submodule = getProductionSubmodule(state.activeSubmodule, module);
  const body = renderProductionSubmoduleBody(submodule.id);
  const moduleLabel = state.lang === "en" ? module.titleEn : module.title;
  const submoduleContext = module.id === "produccion" ? t("productionSubmodule") : `${moduleLabel} / ${t("submodule")}`;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${submoduleContext}</p>
        <h2>${submodule.name}</h2>
      </div>
      <button class="secondary-action" type="button" data-action="back-production">${t("overview")}</button>
    </div>

    <section class="submodule-screen">
      <div class="submodule-screen-head">
        <div>
          <h1>${submodule.name}</h1>
          <p>${submodule.detail}</p>
        </div>
        ${renderProductionSubmoduleAction(submodule.id)}
      </div>
      ${body}
    </section>
  `;

  modulePanel.querySelector("[data-action='back-production']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  bindProductionPanelActions();
}

function getProductionSubmodule(id, module = modules[0]) {
  const [name, detail, submoduleId] = module.submodules.find((item) => item[2] === id) || module.submodules[0];
  return { id: submoduleId, ...getSubmoduleCopy(module.id, submoduleId, name, detail) };
}

function renderProductionSubmoduleAction(id) {
  if (["ordenes","entregables","validacion-recursos"].includes(id) && !hasPermission("production.order.release")) return "";
  const actions = {
    "productos-servicios": `<button class="primary-action" type="button" data-action="open-recipe"><span>＋</span><span>${t("newProduct")}</span></button>`,
    recetas: `<button class="primary-action" type="button" data-action="open-recipe"><span>＋</span><span>${t("newRecipe")}</span></button>`,
    ordenes: `<button class="primary-action" type="button" data-action="open-order"><span>＋</span><span>${t("newProductionOrder")}</span></button>`,
    entregables: `<button class="secondary-action" type="button" data-action="open-order">${t("assignOrder")}</button>`,
    "validacion-recursos": `<button class="primary-action" type="button" data-action="open-order"><span>＋</span><span>${t("generateOrder")}</span></button>`
  };
  if (id === "productos-servicios") {
    return `<button class="primary-action" type="button" data-action="open-product-service"><span>+</span><span>Nuevo producto/servicio</span></button>`;
  }
  if (id === "areas-puestos") {
    return `<div class="row-actions">
      ${hasPermission("hr.area.create") ? `<button class="primary-action" type="button" data-action="open-labor-area-form"><span>+</span><span>${t("newLaborArea")}</span></button>` : ""}
      ${hasPermission("hr.position.create") ? `<button class="secondary-action" type="button" data-action="open-labor-role"><span>+</span><span>${t("newLaborRole")}</span></button>` : ""}
    </div>`;
  }
  if (id === "trabajadores") return hasPermission("hr.worker.create") ? `<button class="primary-action" type="button" data-action="open-worker"><span>+</span><span>${t("newWorker")}</span></button>` : "";
  if (id === "maquinaria") {
    return `<button class="primary-action" type="button" data-action="open-machine"><span>+</span><span>Nueva maquina</span></button>`;
  }
  return actions[id] || "";
}

function renderProductionSubmoduleBody(id) {
  const recipes = mockDb.loadRecipes();
  const orders = mockDb.loadOrders();
  if (id === "productos-servicios") return renderProductsServicesCatalogScreen();
  if (id === "recetas") return renderRecipesScreen(recipes);
  if (id === "areas-puestos") return renderLaborRolesScreen();
  if (id === "trabajadores") return renderWorkersScreen();
  if (id === "maquinaria") return renderMachinesScreen();
  if (id === "ordenes") return renderOrdersScreen(orders);
  if (id === "entregables") return renderDeliverablesScreen(orders);
  if (id === "validacion-recursos") return renderValidationScreen(recipes);
  return "";
}

function renderFlowGuide(title, steps, currentIndex = null, open = true) {
  const toggleCopy = state.lang === "en" ? "Hide / show" : "Ocultar / mostrar";
  const openCopy = state.lang === "en" ? "Open flow" : "Abrir flujo";
  return `
    <details class="flow-guide-card" ${open ? "open" : ""}>
      <summary class="flow-guide-summary" data-open-label="${escapeAttribute(openCopy)}">
        <span class="section-icon">↳</span>
        <strong>${escapeHtml(title)}</strong>
        <span class="flow-guide-toggle-copy">${toggleCopy}</span>
      </summary>
      <div class="flow-guide-steps">
        ${steps.map((step, index) => `
          <article class="flow-guide-step ${currentIndex === index ? "current" : ""}">
            <span>${index + 1}</span>
            <strong>${escapeHtml(step.title)}</strong>
            <p>${escapeHtml(step.detail)}</p>
          </article>
        `).join("")}
      </div>
    </details>
  `;
}

function renderProductsServicesCatalogScreen() {
  const search = localStorage.getItem("erclave-product-service-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const items = mockDb.loadProductsServices();
  const filteredItems = normalizedSearch
    ? items.filter((item) =>
        [item.id, item.name, item.kind, item.category, item.center, item.description]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch)
      )
    : items;
  const activeItems = items.filter((item) => item.status === "Activo").length;
  const itemsWithRecipe = items.filter((item) => getProductServiceCurrentRecipe(item)).length;

  return `
    <section class="section-card product-catalog-view">
      <div class="product-catalog-overview">
        <div>
          <span class="eyebrow">${t("masterData")}</span>
          <h3>${t("productCatalogTitle")}</h3>
          <p>${t("productCatalogHelper")}</p>
        </div>
        <div class="product-catalog-stats" aria-label="${t("productCatalogTitle")}">
          <span><strong>${items.length}</strong>${t("catalogRecords")}</span>
          <span><strong>${activeItems}</strong>${t("activeCatalogRecords")}</span>
          <span><strong>${itemsWithRecipe}</strong>${t("withRecipe")}</span>
        </div>
      </div>
      <div class="catalog-toolbar">
        <label class="search-field catalog-search">
          <span>S</span>
          <input id="productServiceSearch" type="search" value="${search}" placeholder="${t("searchProductService")}" />
        </label>
      </div>
      <div class="product-catalog-grid">
        ${filteredItems.map((item) => {
          const history = getProductServiceOrderHistory(item);
          const currentRecipe = getProductServiceCurrentRecipe(item);
          const standardCost = currentRecipe ? getRecipeStandardCost(currentRecipe) : Number(item.standardCost || 0);
          const targetPrice = Number(item.targetPrice || 0);
          const margin = targetPrice && standardCost ? ((targetPrice - standardCost) / targetPrice) * 100 : Number(item.expectedMargin || 0);
          return `
        <article class="product-catalog-card">
          <div class="product-catalog-card-head">
            <div>
              <span class="muted-label">${item.sku || "SKU pendiente"} · ${item.kind}</span>
              <h4>${item.name}</h4>
            </div>
            <label class="status-control compact-status">
              <span>${t("status")}</span>
              <select data-action="change-product-service-status" data-product-id="${item.id}">
                ${["Activo", "Inactivo", "En espera de aprobacion"].map((status) => `
                  <option value="${status}" ${item.status === status ? "selected" : ""}>${status}</option>
                `).join("")}
              </select>
            </label>
          </div>
          <p class="product-catalog-description">${item.description}</p>
          <div class="product-master-data">
            <span><small>${t("unit")}</small><strong>${item.unit}</strong></span>
            <span><small>Categoria</small><strong>${item.category}</strong></span>
            <span><small>Centro de costos</small><strong>${item.center}</strong></span>
            <span><small>${t("owner")}</small><strong>${item.owner || "Sin asignar"}</strong></span>
          </div>
          <div class="cost-summary-grid product-cost-summary">
            <span><strong>${formatCurrency(standardCost)}</strong>${t("standardCost")}</span>
            <span><strong>${targetPrice ? formatCurrency(targetPrice) : "Pendiente"}</strong>${t("targetPrice")}</span>
            <span><strong>${formatNumber(margin)}%</strong>${t("expectedMargin")}</span>
          </div>
          <div class="product-recipe-summary">
            <div>
              <span class="muted-label">${t("currentRecipe")}</span>
              <strong>${currentRecipe ? `${currentRecipe.id} · vigente v${currentRecipe.currentVersion || "sin aprobar"}` : t("noRecipe")}</strong>
              <p>${currentRecipe ? `${currentRecipe.draftVersionId ? `Edicion v${currentRecipe.version} · ` : ""}${getRecipeApprovalStatus(currentRecipe)} · ${currentRecipe.steps.length} etapas operativas` : "Debe generarse antes de liberar produccion."}</p>
            </div>
            <span class="chip ${currentRecipe ? "active" : "warning"}">${currentRecipe ? getRecipeApprovalStatus(currentRecipe) : t("noRecipe")}</span>
          </div>
          <div class="product-catalog-actions">
            <button class="secondary-action small-action" type="button" data-action="edit-product-service" data-product-id="${item.id}">${t("editMasterRecord")}</button>
            ${currentRecipe
              ? `<button class="secondary-action small-action" type="button" data-action="edit-recipe" data-recipe-id="${currentRecipe.id}">${t("editRecipe")}</button>`
              : `<button class="secondary-action small-action" type="button" data-action="go-recipes-product" data-product-id="${item.id}">${t("createRecipe")}</button>`}
            <button class="primary-action small-action product-orders-action" type="button" data-action="view-product-orders" data-product-id="${item.id}">
              <span>${t("viewProductOrders")}</span><strong>${history.length}</strong>
            </button>
          </div>
        </article>
      `;
        }).join("")}
      </div>
      ${filteredItems.length ? "" : `<p class="helper-copy">${t("noCatalogMatches")}</p>`}
    </section>
  `;
}

function getProductServiceCurrentRecipe(item) {
  return mockDb.loadRecipes()
    .filter((recipe) =>
      recipe.productServiceId === item.id ||
      recipe.product.toLowerCase() === item.name.toLowerCase()
    )
    .sort((a, b) => Number(b.version || 0) - Number(a.version || 0))[0];
}

function getProductServiceOrderHistory(item) {
  const recipes = mockDb.loadRecipes();
  const relatedRecipeIds = recipes
    .filter((recipe) =>
      recipe.productServiceId === item.id ||
      recipe.product.toLowerCase() === item.name.toLowerCase()
    )
    .map((recipe) => recipe.id);

  return mockDb.loadOrders().filter((order) =>
    order.recipeName.toLowerCase() === item.name.toLowerCase() ||
    relatedRecipeIds.includes(order.recipeId)
  );
}

function renderProductsServicesScreen(recipes) {
  const products = recipes.map((recipe) => ({
    code: recipe.id.replace("REC", "PROD"),
    name: recipe.product,
    type: t("buildableProduct"),
    detail: t("baseRecipeVersion", {
      version: recipe.version,
      quantity: recipe.quantityBase,
      unit: recipe.unit,
      center: recipe.center
    }),
    status: recipe.status
  }));
  const services = shouldUseSeedModuleData() ? [
    { code: "SER-014", name: t("assemblyService"), type: t("repeatableService"), detail: t("assemblyServiceDetail"), status: t("configurable") },
    { code: "SER-022", name: t("specialPacking"), type: t("operationalService"), detail: t("specialPackingDetail"), status: t("activeStatus") }
  ] : [];

  return `
    <div class="catalog-grid">
      ${[...products, ...services].map((item) => `
        <article class="catalog-card">
          <div>
            <span class="muted-label">${item.code} · ${item.type}</span>
            <strong>${item.name}</strong>
            <p>${item.detail}</p>
          </div>
          <span class="chip ${item.status === "Activo" || item.status === "Activa" || item.status === "Active" ? "active" : ""}">${translateStatus(item.status)}</span>
        </article>
      `).join("")}
    </div>
  `;
}

function renderRecipesScreen(recipes) {
  const selectedProductId = localStorage.getItem("erclave-recipe-product");
  const selectedProduct = selectedProductId ? mockDb.findProductService(selectedProductId) : null;
  return `
    ${selectedProduct ? `
      <section class="section-card recipe-context-card">
        <div>
          <span class="muted-label">Producto/servicio seleccionado</span>
          <strong>${selectedProduct.name}</strong>
          <p>Ahora puedes generar una receta para este ${selectedProduct.kind.toLowerCase()} desde el apartado correcto.</p>
        </div>
        <button class="primary-action" type="button" data-action="open-recipe">Generar receta</button>
      </section>
    ` : ""}
    <div class="submodule-layout">
      ${renderRecipeList(recipes)}
      ${renderFlowGuide("Flujo de receta", [
        { title: "Producto/servicio", detail: "Seleccionar desde catalogo maestro." },
        { title: "Recursos", detail: "Agregar materiales, mano de obra y maquinaria." },
        { title: "Etapas", detail: "Definir etapas operativas genericas." },
        { title: "Costo", detail: "Calcular costo estandar por unidad o lote." },
        { title: "Aprobacion", detail: "Aprobar antes de liberar ordenes." }
      ])}
      <section class="section-card legacy-workflow" hidden>
        <div class="section-title">
          <span class="section-icon">↳</span>
          <strong>${t("expectedStages")}</strong>
        </div>
        <ol class="workflow-list">
          <li>${t("stageProduct")}</li>
          <li>${t("stageResources")}</li>
          <li>${t("stageTimes")}</li>
          <li>${t("stageOwners")}</li>
          <li>${t("stageValidation")}</li>
        </ol>
      </section>
    </div>
  `;
}

function renderLaborRolesScreen() {
  const roles = mockDb.loadLaborRoles();
  const areas = mockDb.loadLaborAreas();
  const selectedAreaId = localStorage.getItem("erclave-labor-selected-area");
  if (selectedAreaId) return renderLaborAreaDetailScreen(selectedAreaId, roles, areas);

  const search = localStorage.getItem("erclave-labor-area-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const filteredAreas = normalizedSearch
    ? areas.filter((area) => {
        const areaRoles = roles.filter((role) => role.areaId === area.id);
        return (
          [area.code, area.name, area.description, area.status].join(" ").toLowerCase().includes(normalizedSearch) ||
          areaRoles.some((role) =>
            [role.name, role.position, role.status]
              .join(" ")
              .toLowerCase()
              .includes(normalizedSearch)
          )
        );
      })
    : areas;

  return `
    <section class="section-card catalog-workspace">
      ${renderFlowGuide(t("laborConfigurationFlow"), [
        { title: t("laborAreaStep"), detail: t("laborAreaStepHelp") },
        { title: t("laborRoleStep"), detail: t("laborRoleStepHelp") },
        { title: t("laborCapacityStep"), detail: t("laborCapacityStepHelp") },
        { title: t("laborRecipeStep"), detail: t("laborRecipeStepHelp") }
      ])}
      <div class="catalog-toolbar">
        <label class="search-field catalog-search">
          <span>S</span>
          <input id="laborAreaSearch" type="search" value="${search}" placeholder="${escapeAttribute(t("searchLaborAreaRole"))}" />
        </label>
      </div>
      <p class="helper-copy">${t("laborAreaScreenHelp")}</p>
      <div class="area-summary-grid">
        ${filteredAreas.map((area) => {
          const areaRoles = roles.filter((role) => role.areaId === area.id);
          const totalPeople = areaRoles.reduce((sum, role) => sum + Number(role.quantity || 1), 0);
          const totalMinutes = areaRoles.reduce((sum, role) => sum + Number(role.available || 0), 0);
          return `
            <article class="area-card">
              <div>
                <span class="muted-label">${t("operationalArea")}</span>
                <strong>${area.name}</strong>
                <span class="muted-label">${area.code} - ${translateStatus(area.status)}</span>
                <p>${area.description || t("noDescription")}</p>
                <p>${t("laborAreaSummary", { positions: areaRoles.length, resources: totalPeople, minutes: formatNumber(totalMinutes) })}</p>
              </div>
              <div class="catalog-card-actions">
                ${hasPermission("hr.area.update") ? `<button class="secondary-action small-action" type="button" data-action="edit-labor-area" data-area-id="${area.id}">${t("editLaborArea")}</button>` : ""}
                <button class="secondary-action small-action" type="button" data-action="open-labor-area" data-area-id="${area.id}">${t("viewLaborRoles")}</button>
              </div>
            </article>
          `;
        }).join("")}
      </div>
      ${filteredAreas.length ? "" : `<p class="helper-copy">${t("laborAreaEmpty")}</p>`}
    </section>
  `;
}

function renderLaborAreaDetailScreen(areaId, roles = mockDb.loadLaborRoles(), areas = mockDb.loadLaborAreas()) {
  const area = areas.find((item) => item.id === areaId) || areas.find((item) => item.name === areaId);
  if (!area) {
    localStorage.removeItem("erclave-labor-selected-area");
    return `<section class="section-card"><strong>${t("laborAreaUnavailable")}</strong><p>${t("laborAreaUnavailableHelp")}</p></section>`;
  }
  const areaRoles = roles.filter((role) => role.areaId === area.id);
  const totalPeople = areaRoles.reduce((sum, role) => sum + Number(role.quantity || 1), 0);
  const totalMinutes = areaRoles.reduce((sum, role) => sum + Number(role.available || 0), 0);

  return `
    <section class="section-card catalog-workspace">
      <div class="panel-head compact">
        <div>
          <p class="eyebrow">${t("operationalArea")}</p>
          <h3>${area.name}</h3>
          <p>${area.code} - ${area.description || t("noDescription")}</p>
        </div>
        <div class="row-actions">
          ${hasPermission("hr.position.create") ? `<button class="primary-action" type="button" data-action="open-labor-role-area" data-area-id="${area.id}"><span>+</span><span>${t("newLaborRole")}</span></button>` : ""}
          ${hasPermission("hr.area.update") ? `<button class="secondary-action" type="button" data-action="edit-labor-area" data-area-id="${area.id}">${t("editLaborArea")}</button>` : ""}
          <button class="secondary-action" type="button" data-action="back-labor-areas">${t("allLaborAreas")}</button>
        </div>
      </div>
      <div class="area-summary-grid">
        <article class="mini-kpi positive"><span>${t("positionsAndRoles")}</span><strong>${areaRoles.length}</strong></article>
        <article class="mini-kpi positive"><span>${t("resources")}</span><strong>${totalPeople}</strong></article>
        <article class="mini-kpi positive"><span>${t("capacity")}</span><strong>${formatNumber(totalMinutes)} ${t("minutesShort")}</strong></article>
      </div>
      <div class="catalog-grid">
        ${areaRoles.map((role) => `
          <article class="catalog-card">
            <div class="catalog-card-main">
              <span class="muted-label">${role.id} - ${area.name}</span>
              <strong>${role.name}</strong>
              <p>${role.position} - ${t("peoplePerResource", { count: formatNumber(role.quantity || 1) })}</p>
              <span class="muted-label">${t("laborRoleDailyCapacity", { perResource: formatNumber(role.minutesPerResource || role.available), total: formatNumber(role.available) })}</span>
              <span class="muted-label">${t("laborRoleHourlyCost")}: ${formatCurrency(role.hourlyCost ?? Number(role.cost || 0) * 60)}</span>
              <span class="muted-label">${role.intervenesInProduction === true ? t("intervenesInProduction") : t("doesNotInterveneInProduction")}</span>
            </div>
            <div class="catalog-card-actions">
              <span class="chip ${role.status === "Activo" ? "active" : ""}">${translateStatus(role.status)}</span>
              ${hasPermission("hr.position.update") ? `<button class="secondary-action small-action" type="button" data-action="edit-labor-role" data-role-id="${role.id}">${t("editLaborRole")}</button>` : ""}
            </div>
          </article>
        `).join("")}
      </div>
      ${areaRoles.length ? "" : `<p class="helper-copy">${t("laborAreaNoRoles")}</p>`}
    </section>
  `;
}

function renderWorkersScreen() {
  const workers=state.hrApi.workers||[];
  return `<section class="section-card catalog-workspace">
    ${renderFlowGuide(t("workerFileFlow"),[{title:t("workerIdentity"),detail:t("workerIdentityHelp")},{title:t("workerPosition"),detail:t("workerPositionHelp")},{title:t("workerEligibility"),detail:t("workerEligibilityHelp")}])}
    <p class="helper-copy">${t("workerPrivacyHelp")}</p>
    <div class="catalog-grid">${workers.map(worker=>`<article class="catalog-card"><div class="catalog-card-main"><span class="muted-label">${escapeHtml(worker.employee_number)} · ${escapeHtml(worker.position_name)}</span><strong>${escapeHtml(worker.full_name)}</strong><p>${escapeHtml(worker.labor_area_name)} · NSS ••••${escapeHtml(worker.nss.slice(-4))}</p><span class="muted-label">${worker.intervenes_in_production?t("productionEligible"):t("notProductionEligible")}</span></div><div class="catalog-card-actions"><span class="chip ${worker.status==="active"?"active":""}">${translateStatus(worker.status)}</span>${hasPermission("hr.worker.update")?`<button class="secondary-action small-action" data-action="edit-worker" data-worker-id="${worker.id}">${t("editWorker")}</button>`:""}</div></article>`).join("")}</div>
    ${workers.length?"":`<p class="helper-copy">${t("noWorkers")}</p>`}
  </section>`;
}

function renderMachinesScreen() {
  const machines = mockDb.loadMachines();
  return `
    <section class="section-card catalog-workspace">
      ${renderFlowGuide("Flujo de configuracion de maquinaria", [
        { title: "Equipo", detail: "Registrar maquina o recurso tecnico." },
        { title: "Capacidad", detail: "Definir minutos disponibles y costo." },
        { title: "Estatus", detail: "Mantener activo, inactivo o mantenimiento." },
        { title: "Receta", detail: "Asignar tiempo maquina en recetas." }
      ])}
      <p class="helper-copy">La maquinaria se administra como capacidad por equipo y area. En recetas se usa por tiempo maquina.</p>
      <div class="catalog-grid">
        ${machines.map((machine) => `
          <article class="catalog-card">
            <div class="catalog-card-main">
              <span class="muted-label">${machine.id} - ${machine.area}</span>
              <strong>${machine.name}</strong>
              <p>${machine.machineType} - ${formatNumber(machine.available)} ${machine.unit} disponibles por dia.</p>
              <span class="muted-label">Costo maquina: ${formatCurrency(machine.cost)} por ${machine.unit}</span>
            </div>
            <div class="catalog-card-actions">
              <span class="chip ${machine.status === "Activo" ? "active" : ""}">${machine.status}</span>
              <button class="secondary-action small-action" type="button" data-action="edit-machine" data-machine-id="${machine.id}">Abrir maquina</button>
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderOrdersScreen(orders) {
  const selectedProductId = localStorage.getItem("erclave-production-orders-product") || "";
  const selectedProduct = selectedProductId ? mockDb.findProductService(selectedProductId) : null;
  const visibleOrders = selectedProduct ? getProductServiceOrderHistory(selectedProduct) : orders;
  return `
    <div class="submodule-layout">
      <section>
        ${selectedProduct ? `
          <div class="section-card product-order-filter">
            <div>
              <span class="eyebrow">${selectedProduct.sku || selectedProduct.kind}</span>
              <strong>${t("productOrdersTitle", { name: selectedProduct.name })}</strong>
              <p>${t("productOrdersHelper")}</p>
            </div>
            <div class="row-actions">
              <button class="secondary-action small-action" type="button" data-action="back-products-catalog">${t("backToCatalog")}</button>
              <button class="secondary-action small-action" type="button" data-action="show-all-production-orders">${t("showAllOrders")}</button>
            </div>
          </div>
        ` : ""}
        ${renderOrderList(visibleOrders, selectedProduct ? t("noProductOrders") : "")}
      </section>
      <section class="section-card">
        ${renderFlowGuide("Flujo de estatus de orden", orderStatusCatalog.map((status) => ({
          title: translateStatus(status),
          detail: status === "Liberada"
            ? "Orden autorizada para iniciar."
            : status === "En espera de recursos"
              ? "Falta material, capacidad o confirmacion."
              : status === "En produccion"
                ? "Etapas en ejecucion; al iniciar se registran las salidas de materiales reservados."
                : status === "Pausada"
                  ? "Detenida temporalmente con causa operativa."
                  : status === "En validacion"
                    ? "En revision antes de cierre."
                    : status === "Terminada"
                      ? "Orden completada y cerrada."
                      : "Orden cancelada sin continuar flujo."
        })))}
        <div class="section-title">
          <span class="section-icon">✓</span>
          <strong>${t("orderControl")}</strong>
        </div>
        <div class="compat-list">
          <article><strong>${t("scheduling")}</strong><p>${t("schedulingDetail")}</p></article>
          <article><strong>${t("statuses")}</strong><p>${t("statusesDetail")}</p></article>
          <article><strong>${t("document")}</strong><p>${t("documentDetail")}</p></article>
        </div>
      </section>
    </div>
  `;
}

function renderDeliverablesScreen(orders) {
  const deliverables = orders.flatMap((order) =>
    order.areas.map((area) => ({
      order: order.code || order.id,
      product: order.recipeName,
      quantity: `${order.quantity} ${order.unit}`,
      orderProgress: Number(order.overallProgress ?? getOrderProgress(order)),
      ...area
    }))
  );

  return `
    <div class="flow-guided-layout">
      ${renderFlowGuide("Flujo de seguimiento por etapa", [
      { title: "Pendiente", detail: "La etapa esta asignada pero aun no inicia." },
      { title: "En proceso", detail: "El responsable ya esta ejecutando la etapa." },
      { title: "Terminada", detail: "La etapa quedo completada para continuar." },
      { title: "Validacion", detail: "La orden pasa a revision antes de cierre." }
    ])}
    <div class="deliverable-board">
      ${deliverables.map((item) => `
        <article class="deliverable-card">
          <div>
            <span class="muted-label">${item.order} · ${item.quantity}</span>
            <strong>${t("recipePhaseNumber")} ${item.phaseNumber || 1}: ${item.area}</strong>
            <p>${item.product}</p>
            <span class="muted-label">${t("recipePhaseWeightLabel",{weight:item.weightPercent||0})} · ${t("orderProgressLabel",{progress:formatNumber(item.orderProgress)})}</span>
            <span class="muted-label">Etapa operativa · avance ${formatNumber(item.progress || (item.status === "Terminada" ? 100 : 0))}%</span>
          </div>
          <div>
            <span>${item.responsible}</span>
            <span class="chip ${item.status === "En proceso" ? "warning" : ""}">${translateStatus(item.status)}</span>
          </div>
        </article>
      `).join("")}
    </div>
    </div>
  `;
}

function renderValidationScreen(recipes) {
  return `
    <section class="section-card flow-guided-layout">
      ${renderFlowGuide("Flujo de liberacion", [
        { title: "Receta aprobada", detail: "Debe existir version vigente y autorizada." },
        { title: "Recursos definidos", detail: "Confirmar que materiales, puestos y maquinaria existan y sean elegibles." },
        { title: "Costo planeado", detail: "Confirmar costo estandar del lote." },
        { title: "Orden liberada", detail: "Crear orden solo cuando no existan bloqueos." }
      ])}
      <div class="flow-guided-content">
        <p class="helper-copy">${t("validationScreenHelper")}</p>
        ${renderRecipeValidationOnly(recipes)}
      </div>
    </section>
  `;
}

function bindProductionPanelActions() {
  modulePanel.querySelectorAll("[data-action='open-product-service']").forEach((button) => {
    button.addEventListener("click", () => openProductServiceModal());
  });
  modulePanel.querySelectorAll("[data-action='edit-product-service']").forEach((button) => {
    button.addEventListener("click", () => openProductServiceModal(button.dataset.productId));
  });
  modulePanel.querySelectorAll("[data-action='open-labor-role']").forEach((button) => {
    button.addEventListener("click", () => openLaborRoleModal());
  });
  modulePanel.querySelectorAll("[data-action='open-labor-area-form']").forEach((button) => {
    button.addEventListener("click", () => openLaborAreaModal());
  });
  modulePanel.querySelectorAll("[data-action='edit-labor-area']").forEach((button) => {
    button.addEventListener("click", () => openLaborAreaModal(button.dataset.areaId));
  });
  modulePanel.querySelectorAll("[data-action='open-labor-role-area']").forEach((button) => {
    button.addEventListener("click", () => openLaborRoleModal(null, button.dataset.areaId));
  });
  modulePanel.querySelectorAll("[data-action='edit-labor-role']").forEach((button) => {
    button.addEventListener("click", () => openLaborRoleModal(button.dataset.roleId));
  });
  modulePanel.querySelectorAll("[data-action='open-worker']").forEach((button) => button.addEventListener("click",()=>openWorkerModal()));
  modulePanel.querySelectorAll("[data-action='edit-worker']").forEach((button) => button.addEventListener("click",()=>openWorkerModal(button.dataset.workerId)));
  modulePanel.querySelectorAll("[data-action='open-machine']").forEach((button) => {
    button.addEventListener("click", () => openMachineModal());
  });
  modulePanel.querySelectorAll("[data-action='edit-machine']").forEach((button) => {
    button.addEventListener("click", () => openMachineModal(button.dataset.machineId));
  });
  modulePanel.querySelectorAll("[data-action='open-recipe']").forEach((button) => {
    button.addEventListener("click", openRecipeModal);
  });
  modulePanel.querySelectorAll("[data-action='open-order']").forEach((button) => {
    button.addEventListener("click", openOrderModal);
  });
  modulePanel.querySelectorAll("[data-action='module-primary']").forEach((button) => {
    button.addEventListener("click", () => openGenericRecordModal(state.active, state.activeSubmodule));
  });
  modulePanel.querySelectorAll("[data-action='edit-warehouse']").forEach((button) => {
    button.addEventListener("click", () => {
      const module = modules.find((item) => item.id === "almacenes");
      const submodule = getGenericSubmodule(module, "almacenes");
      openWarehouseModal(module, submodule, button.dataset.recordId);
    });
  });
  modulePanel.querySelectorAll("[data-action='edit-inventory-item']").forEach((button) => {
    button.addEventListener("click", () => {
      const module = modules.find((item) => item.id === "almacenes");
      const submodule = getGenericSubmodule(module, "articulos");
      openInventoryItemModal(module, submodule, button.dataset.recordId);
    });
  });
  modulePanel.querySelectorAll("[data-action='edit-sales-customer']").forEach((button) => {
    button.addEventListener("click", () => {
      const module = modules.find((item) => item.id === "ventas");
      const submodule = getGenericSubmodule(module, "clientes");
      openSalesCustomerModal(module, submodule, button.dataset.recordId);
    });
  });
  modulePanel.querySelectorAll("[data-action='edit-sales-quote']").forEach((button) => {
    button.addEventListener("click", () => {
      const module = modules.find((item) => item.id === "ventas");
      const submodule = getGenericSubmodule(module, "cotizaciones");
      openSalesQuoteModal(module, submodule, button.dataset.recordId);
    });
  });
  modulePanel.querySelectorAll("[data-action='print-sales-quote']").forEach((button) => {
    button.addEventListener("click", () => openSalesQuotePrintModal(button.dataset.recordId));
  });
  modulePanel.querySelectorAll("[data-action='create-sales-order']").forEach((button) => {
    button.addEventListener("click", () => {
      const module = modules.find((item) => item.id === "ventas");
      const submodule = getGenericSubmodule(module, "pedidos");
      openSalesOrderModal(module, submodule, button.dataset.recordId);
    });
  });
  modulePanel.querySelectorAll("[data-action='edit-sales-order']").forEach((button) => {
    button.addEventListener("click", () => {
      const module = modules.find((item) => item.id === "ventas");
      const submodule = getGenericSubmodule(module, "pedidos");
      openSalesOrderEditModal(module, submodule, button.dataset.recordId);
    });
  });
  modulePanel.querySelectorAll("[data-action='register-sales-delivery']").forEach((button) => {
    button.addEventListener("click", () => {
      const module = modules.find((item) => item.id === "ventas");
      const submodule = getGenericSubmodule(module, "entregas");
      openSalesDeliveryModal(module, submodule, button.dataset.recordId);
    });
  });
  const validationQuantity = modulePanel.querySelector("#validationQuantity");
  if (validationQuantity) {
    validationQuantity.addEventListener("input", (event) => {
      localStorage.setItem("erclave-validation-qty", Math.max(1, Number(event.target.value || 1)));
      render();
    });
  }
  const selectedRecipe = modulePanel.querySelector("#selectedRecipe");
  if (selectedRecipe) {
    selectedRecipe.addEventListener("change", (event) => {
      localStorage.setItem("erclave-selected-recipe", event.target.value);
      render();
    });
  }
  const productServiceSearch = modulePanel.querySelector("#productServiceSearch");
  if (productServiceSearch) {
    productServiceSearch.addEventListener("input", (event) => {
      localStorage.setItem("erclave-product-service-search", event.target.value);
      render();
      const nextSearch = modulePanel.querySelector("#productServiceSearch");
      if (nextSearch) {
        nextSearch.focus();
        nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
      }
    });
  }
  const laborAreaSearch = modulePanel.querySelector("#laborAreaSearch");
  if (laborAreaSearch) {
    laborAreaSearch.addEventListener("input", (event) => {
      localStorage.setItem("erclave-labor-area-search", event.target.value);
      render();
      const nextSearch = modulePanel.querySelector("#laborAreaSearch");
      if (nextSearch) {
        nextSearch.focus();
        nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
      }
    });
  }
  modulePanel.querySelectorAll("[data-action='open-labor-area']").forEach((button) => {
    button.addEventListener("click", () => {
      navigateTo({ active: state.active, activeSubmodule: state.activeSubmodule, laborArea: button.dataset.areaId });
    });
  });
  modulePanel.querySelectorAll("[data-action='back-labor-areas']").forEach((button) => {
    button.addEventListener("click", () => {
      navigateTo({ active: state.active, activeSubmodule: state.activeSubmodule, laborArea: "" });
    });
  });
  modulePanel.querySelectorAll("[data-action='go-recipes-product']").forEach((button) => {
    button.addEventListener("click", () => {
      localStorage.setItem("erclave-recipe-product", button.dataset.productId);
      navigateTo({ active: "produccion", activeSubmodule: "recetas", laborArea: "" });
    });
  });
  modulePanel.querySelectorAll("[data-action='receive-finished-good']").forEach((button)=>button.addEventListener("click",()=>openFinishedGoodsReceiptModal(button.dataset.orderId)));
  modulePanel.querySelectorAll("[data-action='transition-sales-quote']").forEach(button=>{button.addEventListener("click",async()=>{try{const action={submit:submitSalesQuote,approve:approveSalesQuote,expire:expireSalesQuote,cancel:cancelSalesQuote}[button.dataset.transition];await action(button.dataset.recordId);await loadSalesApiData();showToast(state.lang==="en"?"Quote status updated.":"Estado de cotización actualizado.","success");}catch(error){showApiError(error,state.lang==="en"?"The quote status could not be updated.":"No se pudo actualizar la cotización.");}});});
  modulePanel.querySelectorAll("[data-action='view-product-orders']").forEach((button) => {
    button.addEventListener("click", () => {
      localStorage.setItem("erclave-production-orders-product", button.dataset.productId);
      navigateTo({ active: "produccion", activeSubmodule: "ordenes", laborArea: "" });
    });
  });
  modulePanel.querySelectorAll("[data-action='back-products-catalog']").forEach((button) => {
    button.addEventListener("click", () => {
      localStorage.removeItem("erclave-production-orders-product");
      navigateTo({ active: "produccion", activeSubmodule: "productos-servicios", laborArea: "" });
    });
  });
  modulePanel.querySelectorAll("[data-action='show-all-production-orders']").forEach((button) => {
    button.addEventListener("click", () => {
      localStorage.removeItem("erclave-production-orders-product");
      render();
    });
  });
  modulePanel.querySelectorAll("[data-action='change-product-service-status']").forEach((select) => {
    select.addEventListener("change", async () => {
      const item = mockDb.findProductService(select.dataset.productId);
      if (!item) return;
      if (getApiMode() === "api") {
        try {
          const statuses={Activo:"active",Inactivo:"inactive","En espera de aprobacion":"pending_approval"};
          await updateProductionProductServiceStatus(item.id,{status:statuses[select.value]||select.value,reason:"Actualizacion desde catalogo"});
          await loadProductionApiData();
          showToast(`${item.id} actualizado a ${select.value}.`);
        } catch(error) {
          showApiError(error, state.lang === "en" ? "The status could not be updated." : "No se pudo actualizar el estatus.");
          render();
        }
        return;
      }
      mockDb.updateProductService({ ...item, status: select.value });
      render();
      showToast(`${item.id} actualizado a ${select.value}.`);
    });
  });
  modulePanel.querySelectorAll("[data-action='edit-recipe']").forEach((button) => {
    button.addEventListener("click", () => openRecipeModal(button.dataset.recipeId));
  });
  modulePanel.querySelectorAll("[data-action='approve-recipe']").forEach((button) => {
    button.addEventListener("click", () => approveRecipe(button.dataset.recipeId));
  });
  modulePanel.querySelectorAll("[data-action='delete-recipe']").forEach((button) => {
    button.addEventListener("click", () => deleteRecipe(button.dataset.recipeId));
  });
  modulePanel.querySelectorAll("[data-action='print-order']").forEach((button) => {
    button.addEventListener("click", () => openOrderPrintModal(button.dataset.orderId));
  });
  modulePanel.querySelectorAll("[data-action='create-maintenance-from-order']").forEach((button)=>{
    button.addEventListener("click",()=>{state.maintenanceSourceOrderId=button.dataset.orderId;state.maintenanceApi.status="idle";navigateTo({active:"mantenimiento",activeSubmodule:"ordenes",laborArea:""});});
  });
  modulePanel.querySelectorAll("[data-action='change-order-status']").forEach((select) => {
    select.addEventListener("change", () => changeOrderStatus(select.dataset.orderId, select.value));
  });
  modulePanel.querySelectorAll("[data-action='advance-order-stage']").forEach((button) => {
    button.addEventListener("click", () => advanceOrderStage(button.dataset.orderId, Number(button.dataset.stageIndex)));
  });
  modulePanel.querySelectorAll("[data-submodule]").forEach((button) => {
    button.addEventListener("click", () => {
      navigateTo({ active: button.dataset.module || state.active, activeSubmodule: button.dataset.submodule, laborArea: "" });
    });
  });
}

function renderRecipeValidationCard() {
  const recipes = mockDb.loadRecipes();

  return `
    <section class="section-card recipe-validator">
      ${renderRecipeValidationOnly(recipes)}
    </section>
    ${renderOrderList(mockDb.loadOrders())}
    ${renderRecipeList(recipes)}
  `;
}

function renderRecipeValidationOnly(recipes = mockDb.loadRecipes()) {
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe");
  const recipe = recipes.find((item) => item.id === selectedRecipeId) || recipes[0] || (shouldUseSeedModuleData() ? defaultRecipes[0] : null);
  if (!recipe) {
    return `
      <div class="section-title">
        <span class="section-icon">+</span>
        <strong>Sin recetas configuradas</strong>
      </div>
      <p class="helper-copy">Este tenant aun no tiene recetas, recursos ni ordenes de produccion. Crea el primer producto/servicio y su receta para iniciar operaciones.</p>
      <div class="inline-actions">
        <button class="primary-action" type="button" data-action="open-recipe">Nueva receta</button>
      </div>
    `;
  }
  const validationQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);
  const validation = validateRecipeDefinition(recipe, validationQuantity);
  const definitionIssues=[...(!isRecipeApproved(recipe)?["Receta pendiente de aprobacion"]:[]),...validation.missing.map((row)=>`Recurso no elegible: ${row.name}`)];
  const definitionReady=!definitionIssues.length;

  return `
      <div class="section-title">
        <span class="section-icon">✓</span>
        <strong>Validacion de definicion de receta</strong>
      </div>
      <div class="validator-head">
        <div>
          <span class="muted-label">Receta activa</span>
          <strong>${recipe.product}</strong>
        </div>
        <label class="quantity-control recipe-select-control">
          <span>Receta</span>
          <select id="selectedRecipe" data-entity-selector data-search-placeholder="Buscar receta por producto, versión o estatus">
            ${recipes
              .map(
                (item) => `
                  <option value="${item.id}" ${item.id === recipe.id ? "selected" : ""}>
                    ${formatRecipeDisplayLabel(item)}
                  </option>
                `
              )
              .join("")}
          </select>
        </label>
        <label class="quantity-control">
          <span>Cantidad para proyectar costo</span>
          <input id="validationQuantity" type="number" min="1" value="${validationQuantity}" />
        </label>
        <span class="chip ${definitionReady ? "active" : "warning"}">
          ${definitionReady ? "Definicion valida" : "Definicion incompleta"}
        </span>
      </div>
      <p class="helper-copy">Esta validacion confirma que los recursos existan y sean elegibles y proyecta su costo. No compara inventario ni horas disponibles. La orden de produccion valida materiales, capacidad diaria y dias planeados para su fecha real.</p>
      <div class="cost-summary-grid">
        <span><strong>${getRecipeApprovalStatus(recipe)}</strong>Aprobacion</span>
        <span><strong>${formatCurrency(getRecipeStandardCost(recipe))}</strong>Costo estandar unitario</span>
        <span><strong>${formatCurrency(validation.totalCost)}</strong>Costo planeado lote</span>
      </div>
      ${definitionIssues.length ? `<p class="helper-copy">Pendientes de definicion: ${definitionIssues.join(", ")}.</p>` : ""}
      <div class="inline-actions">
        ${hasPermission("production.order.release")?`<button class="primary-action" type="button" data-action="open-order">Generar orden de produccion</button>`:""}
        <button class="secondary-action" type="button" data-action="open-recipe">Nueva receta</button>
      </div>
      <div class="resource-check-grid">
        ${validation.rows
          .map(
            (row) => `
              <article class="resource-check ${row.ok ? "ok" : "risk"}">
                <div>
                  <strong>${row.name}</strong>
                  <span>${row.type} · ${row.source}</span>
                </div>
                <p>${row.ok ? `Existe en catalogo · referencia para ${formatNumber(row.required)} ${row.unit}` : "No existe en el catalogo elegible"}</p>
              </article>
            `
          )
          .join("")}
      </div>
  `;
}

function renderOrderList(orders, emptyMessage = "") {
  return `
    <section class="section-card recipe-list-card">
      <div class="section-title">
        <span class="section-icon">▤</span>
        <strong>Ordenes de produccion</strong>
      </div>
      <div class="recipe-list">
        ${orders
          .map((order) => {
            const recipe = getOrderRecipe(order);
            const cost = getOrderCostSnapshot(order, recipe);
            const progress = getOrderProgress(order);
            const statusOptions = getOrderStatusOptions(order);
            const closeHelp = getOrderCloseHelp(order);
            return `
            <article class="recipe-list-row order-list-row">
              <div>
                <strong>${order.id} · ${order.recipeName}</strong>
                <span>${order.quantity} ${order.unit} · entrega ${order.dueDate || "sin fecha"} · responsable ${order.responsible} · ${order.releaseStatus || "Liberada"}</span>
                <span>Avance ${formatNumber(progress)}% · planeado ${formatCurrency(cost.plannedCost)} · real ${cost.actualCost == null ? "Pendiente" : formatCurrency(cost.actualCost)}${cost.variance == null ? "" : ` · variacion ${formatCurrency(cost.variance)} (${formatNumber(cost.variancePct)}%)`}</span>
                <div class="stage-progress-list">
                  ${(order.areas || []).map((stage, index) => `
                    <button class="stage-pill ${stage.status === "Terminada" ? "done" : stage.status === "En proceso" ? "active" : ""}" type="button" data-action="advance-order-stage" data-order-id="${order.id}" data-stage-index="${index}" title="Pulsa para avanzar esta fase" ${["production.order_stage.reset","production.order_stage.update","production.order_stage.complete","production.order_stage.block","production.order_stage.skip"].some(hasPermission)?"":"disabled"}>
                      <strong>${stage.area}</strong>
                      <span>${stage.status} · ${formatNumber(stage.progress || (stage.status === "Terminada" ? 100 : 0))}%</span>
                    </button>
                  `).join("")}
                </div>
              </div>
              <span class="chip ${order.status === "Terminada" ? "active" : "warning"}">${translateStatus(order.status)}</span>
              <div class="row-actions">
                <label class="status-control compact-status">
                  <span>Estatus</span>
                  <select data-action="change-order-status" data-order-id="${order.id}" ${statusOptions.length===1?"disabled":""}>
                    ${statusOptions.map((status) => `
                      <option value="${status}" ${order.status === status ? "selected" : ""}>${translateStatus(status)}</option>
                    `).join("")}
                  </select>
                </label>
                <button class="secondary-action small-action" type="button" data-action="print-order" data-order-id="${order.id}">PDF/Imprimir</button>
                ${["En espera de recursos","En produccion"].includes(order.status)?`<button class="secondary-action small-action" type="button" data-action="create-maintenance-from-order" data-order-id="${escapeAttribute(order.id)}">${state.lang==="en"?"Maintenance":"Mantenimiento"}</button>`:""}
                ${closeHelp?`<small class="helper-copy">${escapeHtml(closeHelp)}</small>`:""}
              </div>
            </article>
          `;
          })
          .join("")}
        ${orders.length ? "" : `<p class="helper-copy">${emptyMessage || "Todavia no hay ordenes de produccion registradas."}</p>`}
      </div>
    </section>
  `;
}

function renderRecipeList(recipes) {
  return `
    <section class="section-card recipe-list-card">
      <div class="section-title">
        <span class="section-icon">☷</span>
        <strong>Recetas guardadas</strong>
      </div>
      <div class="recipe-list">
        ${recipes
          .map((recipe) => {
            const validation = validateRecipeDefinition(recipe, Number(localStorage.getItem("erclave-validation-qty") || 100));
            const approvalStatus = getRecipeApprovalStatus(recipe);
            const standardCost = getRecipeStandardCost(recipe);
            return `
              <article class="recipe-list-row">
                <div>
                  <strong>${formatRecipeDisplayLabel(recipe)}</strong>
                  <span>${recipe.currentVersion ? `Vigente v${recipe.currentVersion}` : "Sin version vigente"}${recipe.draftVersionId ? ` · Edicion v${recipe.version} (${approvalStatus})` : ` · ${approvalStatus}`} · ${recipe.resources.length} recursos · ${recipe.steps.length} etapas genericas · costo estandar ${formatCurrency(standardCost)}</span>
                </div>
                <span class="chip ${validation.missing.length || !isRecipeApproved(recipe) ? "warning" : "active"}">
                  ${!isRecipeApproved(recipe) ? approvalStatus : validation.missing.length ? `${validation.missing.length} faltantes` : "Lista"}
                </span>
                <div class="row-actions">
                  <button class="secondary-action small-action" type="button" data-action="approve-recipe" data-recipe-id="${recipe.id}">Aprobar</button>
                  <button class="secondary-action small-action" type="button" data-action="edit-recipe" data-recipe-id="${recipe.id}">Editar</button>
                  <button class="secondary-action small-action danger-action" type="button" data-action="delete-recipe" data-recipe-id="${recipe.id}">Eliminar</button>
                </div>
              </article>
            `;
          })
          .join("")}
        ${recipes.length ? "" : `<p class="helper-copy">Todavia no hay recetas configuradas.</p>`}
      </div>
    </section>
  `;
}

function renderFlow() {
  if (state.active === "administracion") {
    flowList.innerHTML = "";
    notificationSummary.innerHTML = "";
    return;
  }
  const notifications = buildNotifications();
  flowList.innerHTML = notifications.items
    .map(
      (item) => `
        <article class="flow-item notification-item ${item.tone}">
          <span class="flow-step">${item.icon}</span>
          <div>
            <strong>${item.title}</strong>
            <p>${item.detail}</p>
          </div>
        </article>
      `
    )
    .join("");
  notificationSummary.innerHTML = renderNotificationSummary(notifications);
  notificationSummary.querySelector("[data-action='open-order']").addEventListener("click", () => {
    navigateTo({ active: "produccion", activeSubmodule: "ordenes", laborArea: "" });
  });
}

function buildNotifications() {
  const today = startOfDay(new Date());
  const orders = mockDb.loadOrders();
  const productsServices = mockDb.loadProductsServices();
  const recipes = mockDb.loadRecipes();
  const items = [];
  let overdue = 0;
  let dueSoon = 0;
  let missingResources = 0;

  if (!shouldUseSeedModuleData() && !orders.length && !productsServices.length && !recipes.length) {
    return { overdue, dueSoon, missingResources, items };
  }

  productsServices
    .filter((item) => item.status === "Activo")
    .forEach((item) => {
      const currentRecipe = recipes.find((recipe) =>
        recipe.productServiceId === item.id ||
        recipe.product.toLowerCase() === item.name.toLowerCase()
      );
      if (!currentRecipe || !isRecipeApproved(currentRecipe)) {
        items.push({
          tone: "warning",
          icon: "R",
          title: `${item.name} sin receta aprobada`,
          detail: "No debe liberarse produccion hasta tener receta vigente y aprobada."
        });
      }
    });

  orders.forEach((order) => {
    const dueDate = order.dueDate ? startOfDay(new Date(`${order.dueDate}T00:00:00`)) : null;
    const isClosed = ["Terminada", "Cancelada"].includes(order.status);
    const recipe = getOrderRecipe(order);
    const validation = calculateRecipe(recipe, order.quantity);

    if (dueDate && !isClosed) {
      const days = diffDays(today, dueDate);
      if (days < 0) {
        const absDays = Math.abs(days);
        overdue += 1;
        items.push({
          tone: "danger",
          icon: "!",
          title: t("overdueOrderTitle", { id: order.id }),
          detail: t("overdueOrderDetail", {
            name: order.recipeName,
            days: absDays,
            dayLabel: t(absDays === 1 ? "day" : "days"),
            responsible: order.responsible
          })
        });
      } else if (days <= 3) {
        dueSoon += 1;
        items.push({
          tone: "warning",
          icon: "T",
          title: t("dueSoonTitle", { id: order.id }),
          detail: t("dueSoonDetail", {
            name: order.recipeName,
            days: days || "0",
            dayLabel: t(days === 1 ? "day" : "days")
          })
        });
      }
    }

    if (!isClosed && validation.missing.length) {
      missingResources += validation.missing.length;
      items.push({
        tone: "warning",
        icon: "R",
        title: t("missingResourcesTitle", { id: order.id }),
        detail: t("missingResourcesDetail", {
          resources: validation.missing.map((row) => row.name).join(", "),
          quantity: order.quantity,
          unit: order.unit
        })
      });
    }

    if (!isClosed && order.priority === "Alta") {
      items.push({
        tone: "info",
        icon: "P",
        title: t("highPriorityTitle", { id: order.id }),
        detail: t("highPriorityDetail", {
          name: order.recipeName,
          status: translateStatus(order.status).toLowerCase(),
          responsible: order.responsible
        })
      });
    }
  });

  if (!overdue) {
    items.push({
      tone: "ok",
      icon: "✓",
      title: t("noOverdueTitle"),
      detail: t("noOverdueDetail")
    });
  }

  if (!items.length) {
    items.push({
      tone: "ok",
      icon: "✓",
      title: t("stableOperationTitle"),
      detail: t("stableOperationDetail")
    });
  }

  return {
    overdue,
    dueSoon,
    missingResources,
    items: items.slice(0, 5)
  };
}

function renderNotificationSummary({ overdue, dueSoon, missingResources }) {
  const tone = overdue ? "danger" : missingResources || dueSoon ? "warning" : "active";
  const label = overdue ? t("attention") : missingResources || dueSoon ? t("review") : t("stable");
  return `
    <div class="panel-head compact">
      <div>
        <p class="eyebrow">${t("summary")}</p>
        <h3>${t("production")}</h3>
      </div>
      <span class="chip ${tone}">${label}</span>
    </div>
    <div class="requirement-row ${overdue ? "risk" : "ok"}">
      <span>${t("overdueOrders")}</span>
      <strong>${overdue}</strong>
    </div>
    <div class="requirement-row ${dueSoon ? "risk" : "ok"}">
      <span>${t("dueSoon")}</span>
      <strong>${dueSoon}</strong>
    </div>
    <div class="requirement-row ${missingResources ? "risk" : "ok"}">
      <span>${t("missingResources")}</span>
      <strong>${missingResources}</strong>
    </div>
    <button class="secondary-action full" type="button" data-action="open-order">${t("reviewOrders")}</button>
  `;
}

function translateStatus(status) {
  const statusMap = {
    active: { es: "Activo", en: "Active" },
    inactive: { es: "Inactivo", en: "Inactive" },
    terminated: { es: "Baja", en: "Terminated" },
    Activo: { es: "Activo", en: "Active" },
    Inactivo: { es: "Inactivo", en: "Inactive" },
    Bloqueado: { es: "Bloqueado", en: "Blocked" },
    Activa: { es: "Activa", en: "Active" },
    Configurable: { es: "Configurable", en: "Configurable" },
    Liberada: { es: "Liberada", en: "Released" },
    "En espera de recursos": { es: "En espera de recursos", en: "Waiting for resources" },
    "En produccion": { es: "En produccion", en: "In production" },
    "En validacion": { es: "En validacion", en: "In validation" },
    Pausada: { es: "Pausada", en: "Paused" },
    Terminada: { es: "Terminada", en: "Finished" },
    Cancelada: { es: "Cancelada", en: "Canceled" },
    Pendiente: { es: "Pendiente", en: "Pending" },
    "En proceso": { es: "En proceso", en: "In progress" },
    Borrador: { es: "Borrador", en: "Draft" },
    "En revision": { es: "En revision", en: "In review" },
    Aprobado: { es: "Aprobado", en: "Approved" },
    Registrado: { es: "Registrado", en: "Registered" },
    Prospecto: { es: "Prospecto", en: "Prospect" },
    Cotizada: { es: "Cotizada", en: "Quoted" },
    Vencida: { es: "Vencida", en: "Expired" },
    "En preparacion": { es: "En preparacion", en: "In preparation" },
    Cancelado: { es: "Cancelado", en: "Canceled" },
    "Pendiente de entrega": { es: "Pendiente de entrega", en: "Pending delivery" },
    "En ruta": { es: "En ruta", en: "Out for delivery" },
    "Entrega parcial": { es: "Entrega parcial", en: "Partial delivery" },
    "Parcialmente entregado": { es: "Parcialmente entregado", en: "Partially delivered" },
    Entregado: { es: "Entregado", en: "Delivered" },
    "No entregado": { es: "No entregado", en: "Not delivered" },
    Reprogramado: { es: "Reprogramado", en: "Rescheduled" }
  };
  return statusMap[status]?.[state.lang] || status;
}









function showToast(message, tone = "info") {
  toast.textContent = message;
  toast.dataset.tone = tone;
  toast.setAttribute("role", tone === "danger" ? "alert" : "status");
  toast.setAttribute("aria-live", tone === "danger" ? "assertive" : "polite");
  toast.hidden = false;
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    toast.hidden = true;
  }, tone === "danger" ? 8000 : tone === "warning" ? 6000 : 3200);
}

function closeModal() {
  modalBackdrop.hidden = true;
  modalContent.innerHTML = "";
}

function getGenericRecordStatusOptions() {
  return [
    ["Borrador", t("draftStatus")],
    ["En revision", t("reviewStatus")],
    ["Aprobado", t("approvedStatus")],
    ["Pendiente", t("pendingStatus")]
  ];
}

function openGenericRecordModal(moduleId = state.active, submoduleId = state.activeSubmodule) {
  const module = modules.find((item) => item.id === moduleId);
  if (!module || module.id === "produccion") return;

  const submodule = submoduleId ? getGenericSubmodule(module, submoduleId) : null;
  if (module.id === "ventas" && submodule?.id === "margen") return;
  if (isWarehouseMasterSubmodule(module, submodule)) {
    openWarehouseModal(module, submodule);
    return;
  }
  if (isWarehouseItemsSubmodule(module, submodule)) {
    openInventoryItemModal(module, submodule);
    return;
  }
  if (isWarehouseMovementSubmodule(module, submodule)) {
    openInventoryMovementModal(module, submodule);
    return;
  }
  if (isWarehouseStockSubmodule(module, submodule)) {
    showToast(t("stockReadOnlyToast"));
    return;
  }
  if (isWarehouseReservationsSubmodule(module, submodule)) {
    showToast(t("reservationsDisabledToast"));
    return;
  }
  if (isWarehouseKardexSubmodule(module, submodule)) {
    showToast(t("kardexReadOnlyToast"));
    return;
  }
  if (isSalesCustomersSubmodule(module, submodule)) {
    openSalesCustomerModal(module, submodule);
    return;
  }
  if (isSalesQuotesSubmodule(module, submodule)) {
    openSalesQuoteModal(module, submodule);
    return;
  }
  if (isSalesOrdersSubmodule(module, submodule)) {
    openSalesOrderModal(module, submodule);
    return;
  }
  if (isSalesDeliveriesSubmodule(module, submodule)) {
    showToast(t("deliveryReadOnlyToast"));
    return;
  }
  const label = state.lang === "en" ? module.titleEn : module.title;
  const fields = submodule ? getGenericSubmoduleForm(module, submodule) : (state.lang === "en" ? getGenericSubmoduleForm(module, normalizeSubmodules(module)[0]) : module.form);
  const fieldRows = fields.slice(0, 6);

  modalContent.innerHTML = `
    <form class="recipe-form" id="genericRecordForm">
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${t("newModuleRecord")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        ${fieldRows
          .map(([fieldLabel, value], index) => `
            <label class="preview-field ${index === fieldRows.length - 1 ? "wide-field" : ""}">
              <span>${fieldLabel}</span>
              <input name="field-${index}" type="text" value="${value || ""}" ${index < 2 ? "required" : ""} />
            </label>
          `)
          .join("")}
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            ${getGenericRecordStatusOptions().map(([value, text]) => `<option value="${value}">${text}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("owner")}</span>
          <input name="owner" type="text" value="${label}" />
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-generic-record">${t("cancel")}</button>
        <button class="primary-action" type="submit">${t("saveRecord")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-generic-record']").addEventListener("click", closeModal);
  modalContent.querySelector("#genericRecordForm").addEventListener("submit", (event) => saveGenericRecordForm(event, module, submodule));
}

function saveGenericRecordForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = [...form.querySelectorAll("input[name^='field-']")].map((input) => input.value.trim());
  const errors = [];

  if (!values[0]) errors.push(t("firstFieldRequired"));
  if (!values[1]) errors.push(t("secondFieldRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const label = state.lang === "en" ? module.titleEn : module.title;
  const submoduleId = submodule?.id || "";
  const code = `${module.icon}-${String(Date.now()).slice(-5)}`;
  const status = new FormData(form).get("status") || "Borrador";
  const record = {
    id: `${module.id}-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId,
    title: values[0],
    detail: values.filter(Boolean).slice(1).join(" - ") || label,
    status,
    owner: new FormData(form).get("owner") || label,
    fields: values,
    createdAt: new Date().toISOString()
  };

  mockDb.addModuleRecord(module.id, record);
  closeModal();
  render();
  showToast(t("recordSaved", { code }));
}

function selectedOption(value, expected) {
  return value === expected ? "selected" : "";
}

function openWarehouseModal(module, submodule, recordId = null, initialFields = {}) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || initialFields;
  const isEditing = Boolean(existingRecord);

  modalContent.innerHTML = `
    <form class="recipe-form" id="warehouseForm">
      <input type="hidden" name="recordId" value="${escapeAttribute(existingRecord?.id || "")}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("inventory.warehouse"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${isEditing ? t("editWarehouse") : t("newWarehouse")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("warehouseCode")}</span>
          <input name="code" type="text" value="${existingRecord?.code || ""}" placeholder="${codeSequenceConfig("inventory.warehouse")?.mode === "managed" ? t("codeAssignedAutomatically") : "ALM-MP-01"}" ${isEditing || codeSequenceConfig("inventory.warehouse")?.mode === "managed" ? "readonly" : ""} />
        </label>
        <label class="preview-field">
          <span>${t("warehouseName")}</span>
          <input name="name" type="text" value="${existingRecord?.title || ""}" placeholder="${t("warehouseNamePlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("warehouseType")}</span>
          <select name="type" required>
            <option value="rawMaterials" ${selectedOption(fields.type, "rawMaterials")}>${t("rawMaterials")}</option>
            <option value="tools" ${selectedOption(fields.type, "tools")}>${t("toolsWarehouse")}</option>
            <option value="workInProcess" ${selectedOption(fields.type, "workInProcess")}>${t("workInProcess")}</option>
            <option value="finishedGoods" ${selectedOption(fields.type, "finishedGoods")}>${t("finishedGoods")}</option>
            <option value="scrap" ${selectedOption(fields.type, "scrap")}>${t("scrapWarehouse")}</option>
            <option value="spare_parts" ${selectedOption(fields.type, "spare_parts")||selectedOption(fields.type, "spareParts")}>${t("spareParts")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("warehouseStatus")}</span>
          <select name="status">
            <option value="Activo" ${selectedOption(existingRecord?.status || "Activo", "Activo")}>${t("activeStatus")}</option>
            <option value="Inactivo" ${selectedOption(existingRecord?.status, "Inactivo")}>${t("inactiveStatus")}</option>
            <option value="Bloqueado" ${selectedOption(existingRecord?.status, "Bloqueado")}>${t("blockedStatus")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("businessCenter")}</span>
          <input name="businessCenter" type="text" value="${fields.businessCenter || ""}" placeholder="${t("businessCenterPlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("warehouseLocation")}</span>
          <input name="location" type="text" value="${fields.location || ""}" placeholder="${t("warehouseLocationPlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("warehouseOwner")}</span>
          <input name="owner" type="text" value="${existingRecord?.owner || ""}" placeholder="${t("warehouseOwnerPlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("capacity")}</span>
          <input name="capacity" type="text" value="${fields.capacity || ""}" placeholder="${t("capacityPlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("inventoryPolicy")}</span>
          <select name="policy">
            <option value="standard" ${selectedOption(fields.policy || "standard", "standard")}>${t("standardPolicy")}</option>
            <option value="batch" ${selectedOption(fields.policy, "batch")}>${t("batchPolicy")}</option>
            <option value="serial" ${selectedOption(fields.policy, "serial")}>${t("serialPolicy")}</option>
            <option value="restricted" ${selectedOption(fields.policy, "restricted")}>${t("restrictedPolicy")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("allowsReservations")}</span>
          <select name="allowsReservations">
            <option value="yes" ${selectedOption(fields.allowsReservations || "yes", "yes")}>${t("yes")}</option>
            <option value="no" ${selectedOption(fields.allowsReservations, "no")}>${t("no")}</option>
          </select>
        </label>
        <div class="section-title form-section-title wide-field">
          <span class="section-icon">▦</span>
          <strong>${t("optionalPhysicalLocation")}</strong>
        </div>
        <p class="helper-copy wide-field">${t("optionalPhysicalLocationHelp")}</p>
        <label class="preview-field">
          <span>${t("zone")}</span>
          <input name="zone" type="text" value="${fields.zone || ""}" placeholder="A" />
        </label>
        <label class="preview-field">
          <span>${t("aisle")}</span>
          <input name="aisle" type="text" value="${fields.aisle || ""}" placeholder="01" />
        </label>
        <label class="preview-field">
          <span>${t("rack")}</span>
          <input name="rack" type="text" value="${fields.rack || ""}" placeholder="R02" />
        </label>
        <label class="preview-field">
          <span>${t("level")}</span>
          <input name="level" type="text" value="${fields.level || ""}" placeholder="N03" />
        </label>
        <label class="preview-field">
          <span>${t("position")}</span>
          <input name="position" type="text" value="${fields.position || ""}" placeholder="P04" />
        </label>
        <label class="preview-field wide-field">
          <span>${t("description")}</span>
          <textarea name="description" rows="3" placeholder="${t("warehouseDescriptionPlaceholder")}">${fields.description || ""}</textarea>
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-warehouse">${t("cancel")}</button>
        <button class="primary-action" type="submit">${isEditing ? t("updateWarehouse") : t("saveWarehouse")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-warehouse']").addEventListener("click", closeModal);
  modalContent.querySelector("#warehouseForm").addEventListener("submit", (event) => saveWarehouseForm(event, module, submodule));
}

async function saveWarehouseForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim() && getApiMode() !== "api") errors.push(t("warehouseCodeRequired"));
  if (!data.name?.trim()) errors.push(t("warehouseNameRequired"));
  if (!data.businessCenter?.trim()) errors.push(t("businessCenterRequired"));
  if (!data.location?.trim()) errors.push(t("warehouseLocationRequired"));
  if (!data.owner?.trim()) errors.push(t("warehouseOwnerRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  let code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
  if (getApiMode() === "api") {
    const payload = {name:data.name.trim(),type:data.type,business_center:data.businessCenter.trim(),location:data.location.trim(),owner:data.owner.trim(),capacity:data.capacity?.trim()||null,inventory_policy:data.policy,zone:data.zone?.trim()||null,aisle:data.aisle?.trim()||null,rack:data.rack?.trim()||null,level:data.level?.trim()||null,position:data.position?.trim()||null,description:data.description?.trim()||null,status:(data.status||"Activo")==="Activo"?"active":(data.status==="Bloqueado"?"blocked":"inactive")};
    try {
      if (existingRecord) await updateInventoryWarehouse(existingRecord.id,payload);
      else {code=await resolveBusinessCode("inventory.warehouse",code,data.codeRequestKey);await createInventoryWarehouse({code,...payload});}
      closeModal(); await loadInventoryApiData(); showToast(t(existingRecord ? "warehouseUpdated" : "warehouseSaved", { code }));
    } catch (error) { renderFormErrors([error.message]); }
    return;
  }
  const record = {
    id: existingRecord?.id || `${module.id}-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId: submodule.id,
    recordType: "warehouse",
    title: data.name.trim(),
    detail: `${translateWarehouseType(data.type)} - ${data.businessCenter} - ${data.location}`,
    status: data.status || "Activo",
    owner: data.owner.trim(),
    fields: {
      type: data.type,
      businessCenter: data.businessCenter.trim(),
      location: data.location.trim(),
      capacity: data.capacity?.trim() || "",
      policy: data.policy,
      allowsReservations: data.allowsReservations,
      zone: data.zone?.trim() || "",
      aisle: data.aisle?.trim() || "",
      rack: data.rack?.trim() || "",
      level: data.level?.trim() || "",
      position: data.position?.trim() || "",
      description: data.description?.trim() || ""
    },
    createdAt: new Date().toISOString()
  };

  if (existingRecord) {
    mockDb.updateModuleRecord(module.id, {
      ...record,
      createdAt: existingRecord.createdAt,
      updatedAt: new Date().toISOString()
    });
  } else {
    mockDb.addModuleRecord(module.id, record);
  }
  closeModal();
  render();
  showToast(t(existingRecord ? "warehouseUpdated" : "warehouseSaved", { code }));
}

async function openInventoryItemModal(module, submodule, recordId = null, initialFields = {}) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || initialFields;
  const warehouses = mockDb.loadModuleRecords(module.id, "almacenes").filter((record) => record.recordType === "warehouse");
  const isEditing = Boolean(existingRecord);
  let productionCandidates=[];
  if (!isEditing && getApiMode()==="api" && isInventoryApiEnabled()) {
    try { productionCandidates=await getUnlinkedProductionProducts(); } catch (_) { productionCandidates=[]; }
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="inventoryItemForm">
      <input type="hidden" name="recordId" value="${escapeAttribute(existingRecord?.id || "")}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("inventory.item"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${isEditing ? t("editInventoryItem") : t("newInventoryItem")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("itemCode")}</span>
          <input name="code" type="text" value="${existingRecord?.code || ""}" placeholder="${codeSequenceConfig("inventory.item")?.mode === "managed" ? t("codeAssignedAutomatically") : "MAT-001"}" ${isEditing || codeSequenceConfig("inventory.item")?.mode === "managed" ? "readonly" : ""} />
        </label>
        <label class="preview-field">
          <span>${t("itemName")}</span>
          <input name="name" type="text" value="${existingRecord?.title || ""}" placeholder="${t("itemPlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("itemType")}</span>
          <select name="type" required>
            <option value="rawMaterial" ${selectedOption(fields.type || "rawMaterial", "rawMaterial")}>${t("rawMaterialItem")}</option>
            <option value="consumable" ${selectedOption(fields.type, "consumable")}>${t("consumableItem")}</option>
            <option value="tool" ${selectedOption(fields.type, "tool")}>${t("toolItem")}</option>
            <option value="finishedGood" ${selectedOption(fields.type, "finishedGood")}>${t("finishedGoodItem")}</option>
            <option value="sparePart" ${selectedOption(fields.type, "sparePart")}>${t("sparePartItem")}</option>
            <option value="serviceSupply" ${selectedOption(fields.type, "serviceSupply")}>${t("serviceSupplyItem")}</option>
          </select>
        </label>
        ${!isEditing ? `<label class="preview-field wide-field" data-production-link-field hidden>
          <span>${t("productionProductLink")}</span>
          <select name="productionProductId" data-entity-selector><option value="">${t("productionProductLinkNone")}</option>${productionCandidates.map(product=>`<option value="${escapeAttribute(product.id)}" data-name="${escapeAttribute(product.name)}" data-category="${escapeAttribute(product.category||"")}" data-unit="${escapeAttribute(product.base_unit)}">${product.code} - ${product.name} · ${product.base_unit}</option>`).join("")}</select>
          <small>${t("productionProductLinkHelp")}</small>
        </label>` : ""}
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            <option value="Activo" ${selectedOption(existingRecord?.status || "Activo", "Activo")}>${t("activeStatus")}</option>
            <option value="Inactivo" ${selectedOption(existingRecord?.status, "Inactivo")}>${t("inactiveStatus")}</option>
            <option value="Bloqueado" ${selectedOption(existingRecord?.status, "Bloqueado")}>${t("blockedStatus")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("itemCategory")}</span>
          <input name="category" type="text" value="${fields.category || ""}" placeholder="${t("itemCategoryPlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("unit")}</span>
          ${unitSelect("unit", fields.unit || "H87")}
        </label>
        <label class="preview-field">
          <span>${t("defaultUnitCost")}</span>
          <input name="defaultUnitCost" type="number" min="0" step="0.000001" value="${escapeAttribute(fields.defaultUnitCost ?? 0)}" required />
          <small>${t("defaultUnitCostHelp")}</small>
        </label>
        <label class="preview-field">
          <span>${t("minStock")}</span>
          <input name="minStock" type="number" min="0" step="0.01" value="${fields.minStock || ""}" placeholder="0" />
        </label>
        <label class="preview-field">
          <span>${t("maxStock")}</span>
          <input name="maxStock" type="number" min="0" step="0.01" value="${fields.maxStock || ""}" placeholder="100" />
        </label>
        <label class="preview-field">
          <span>${t("inventoryPolicy")}</span>
          <select name="policy">
            <option value="standard" ${selectedOption(fields.policy || "standard", "standard")}>${t("standardPolicy")}</option>
            <option value="batch" ${selectedOption(fields.policy, "batch")}>${t("batchPolicy")}</option>
            <option value="serial" ${selectedOption(fields.policy, "serial")}>${t("serialPolicy")}</option>
            <option value="restricted" ${selectedOption(fields.policy, "restricted")}>${t("restrictedPolicy")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("defaultWarehouse")}</span>
          ${warehouses.length ? `
            <select name="defaultWarehouseId" data-entity-selector>
              <option value="">${t("notDefined")}</option>
              ${warehouses.map((warehouse) => `<option value="${warehouse.id}" ${selectedOption(fields.defaultWarehouseId, warehouse.id)}>${warehouse.code} - ${warehouse.title}</option>`).join("")}
            </select>
          ` : `<input name="defaultWarehouseName" type="text" value="${fields.defaultWarehouseName || ""}" placeholder="${t("warehouseNamePlaceholder")}" />`}
        </label>
        <label class="preview-field checkbox-field">
          <input name="useInRecipe" type="checkbox" value="true" ${fields.useInRecipe ? "checked" : ""} />
          <span>${t("useInRecipe")}</span>
        </label>
        <label class="preview-field wide-field">
          <span>${t("description")}</span>
          <textarea name="description" rows="3" placeholder="${t("inventoryItemDescriptionPlaceholder")}">${fields.description || ""}</textarea>
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-inventory-item">${t("cancel")}</button>
        <button class="primary-action" type="submit">${isEditing ? t("updateInventoryItem") : t("saveInventoryItem")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-inventory-item']").addEventListener("click", closeModal);
  modalContent.querySelector("#inventoryItemForm").addEventListener("submit", (event) => saveInventoryItemForm(event, module, submodule));
  const typeSelect=modalContent.querySelector('[name="type"]');
  const linkField=modalContent.querySelector("[data-production-link-field]");
  const syncLinkVisibility=()=>{if(linkField)linkField.hidden=typeSelect.value!=="finishedGood";};
  syncLinkVisibility(); typeSelect.addEventListener("change",syncLinkVisibility);
  modalContent.querySelector('[name="productionProductId"]')?.addEventListener("change",event=>{
    const option=event.target.selectedOptions[0]; const unit=modalContent.querySelector('[name="unit"]');
    if(!option?.value){unit.disabled=false;return;}
    const name=modalContent.querySelector('[name="name"]'); const category=modalContent.querySelector('[name="category"]');
    if(!name.value)name.value=option.dataset.name||""; if(!category.value)category.value=option.dataset.category||""; unit.value=option.dataset.unit; unit.disabled=true;
  });
}

async function saveInventoryItemForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim() && getApiMode() !== "api") errors.push(t("itemCodeRequired"));
  if (!data.name?.trim()) errors.push(t("itemNameRequired"));
  if (!(form.querySelector('[name="unit"]')?.value || data.unit || "").trim()) errors.push(t("unitRequired"));
  if (data.productionProductId && data.status !== "Activo") errors.push(t("productionProductLinkRequiresActive"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const warehouse = data.defaultWarehouseId ? mockDb.findModuleRecord(module.id, data.defaultWarehouseId) : null;
  let code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
  const defaultWarehouseName = warehouse ? `${warehouse.code} - ${warehouse.title}` : data.defaultWarehouseName?.trim() || "";
  if (getApiMode() === "api" && isInventoryApiEnabled()) {
    const selectedProduct=form.querySelector('[name="productionProductId"]')?.value||"";
    const selectedUnit=form.querySelector('[name="unit"]')?.value||data.unit;
    const payload={name:data.name.trim(),type:data.type,category:data.category?.trim()||null,base_unit:selectedUnit.trim(),suggested_warehouse_id:data.defaultWarehouseId||null,minimum_stock:Number(data.minStock||0),maximum_stock:data.maxStock?Number(data.maxStock):0,default_unit_cost:Number(data.defaultUnitCost||0),use_in_recipe:data.useInRecipe==="true",status:(data.status||"Activo")==="Activo"?"active":(data.status==="Bloqueado"?"blocked":"inactive"),description:data.description?.trim()||null};
    try {
      if (existingRecord) await updateInventoryItem(existingRecord.id,payload);
      else if(selectedProduct) {
        code=await resolveBusinessCode("inventory.item",code,data.codeRequestKey);
        const linked=await createAndLinkFinishedGood(selectedProduct,{code,inventory_policy:data.policy==="batch"?"lot":data.policy,...payload});
        mockDb.updateProductService(mapApiProduct(linked.product_service));
        state.productionApi={status:"idle",error:""};
        state.salesApi={...state.salesApi,status:"idle",error:""};
      }
      else { code=await resolveBusinessCode("inventory.item",code,data.codeRequestKey); await createInventoryItem({code,inventory_policy:data.policy==="batch"?"lot":data.policy,...payload}); }
      closeModal();
      await loadInventoryApiData();
      if(selectedProduct) await loadProductionApiData();
      showToast(t(existingRecord ? "inventoryItemUpdated" : "inventoryItemSaved", { code }));
    } catch (error) {
      const errorCode = error?.payload?.error?.code;
      renderFormErrors([errorCode === "item_base_unit_locked_by_movements" ? t("itemBaseUnitLockedByHistory") : error.message]);
    }
    return;
  }
  const record = {
    id: existingRecord?.id || `${module.id}-item-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId: submodule.id,
    recordType: "inventoryItem",
    title: data.name.trim(),
    detail: `${translateInventoryItemType(data.type)} - ${data.unit.trim()} - ${defaultWarehouseName || t("notDefined")}`,
    status: data.status || "Activo",
    owner: defaultWarehouseName || t("notDefined"),
    fields: {
      type: data.type,
      category: data.category?.trim() || "",
      unit: data.unit.trim(),
      defaultUnitCost: Number(data.defaultUnitCost || 0),
      minStock: data.minStock || "",
      maxStock: data.maxStock || "",
      policy: data.policy,
      useInRecipe: data.useInRecipe === "true",
      defaultWarehouseId: data.defaultWarehouseId || "",
      defaultWarehouseName,
      description: data.description?.trim() || ""
    },
    createdAt: new Date().toISOString()
  };

  if (existingRecord) {
    mockDb.updateModuleRecord(module.id, {
      ...record,
      createdAt: existingRecord.createdAt,
      updatedAt: new Date().toISOString()
    });
  } else {
    mockDb.addModuleRecord(module.id, record);
  }
  closeModal();
  render();
  showToast(t(existingRecord ? "inventoryItemUpdated" : "inventoryItemSaved", { code }));
}

function openInventoryMovementModal(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const warehouses = mockDb.loadModuleRecords(module.id, "almacenes").filter((record) => record.recordType === "warehouse");
  const items = mockDb.loadModuleRecords(module.id, "articulos").filter((record) => record.recordType === "inventoryItem");

  modalContent.innerHTML = `
    <form class="recipe-form" id="movementForm">
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${t("newMovement")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("movementType")}</span>
          <select name="movementType" required>
            <option value="entry">${t("entryMovement")}</option>
            <option value="exit">${t("exitMovement")}</option>
            <option value="transfer">${t("transferMovement")}</option>
            <option value="positiveAdjustment">${t("positiveAdjustment")}</option>
            <option value="negativeAdjustment">${t("negativeAdjustment")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("sourceDocument")}</span>
          <input name="sourceDocument" type="text" placeholder="MAN-001" required />
        </label>
        <label class="preview-field product-lookup-field">
          <span>${t("item")}</span>
          ${items.length ? `
            <input id="movementItemSearch" type="text" value="" placeholder="${t("itemLookupPlaceholder")}" autocomplete="off" required />
            <input name="itemId" type="hidden" value="" />
            <div class="lookup-results" id="movementItemResults" hidden></div>
          ` : `<input name="item" type="text" placeholder="${t("itemPlaceholder")}" required />`}
        </label>
        <label class="preview-field">
          <span>${t("quantity")}</span>
          <input name="quantity" type="number" min="0.01" step="0.01" placeholder="1" required />
        </label>
        <label class="preview-field">
          <span>${t("unit")}</span>
          ${unitSelect("unit", "H87")}
        </label>
        <label class="preview-field">
          <span>${t("warehouse")}</span>
          ${warehouses.length ? `
            <select name="warehouseId" data-entity-selector required>
              ${warehouses.map((warehouse) => `<option value="${warehouse.id}">${warehouse.code} - ${warehouse.title}</option>`).join("")}
            </select>
          ` : `<input name="warehouseName" type="text" placeholder="${t("warehouseNamePlaceholder")}" required />`}
        </label>
        <label class="preview-field">
          <span>Almacen destino (solo transferencia)</span>
          <select name="destinationWarehouseId" data-entity-selector>
            <option value="">No aplica</option>
            ${warehouses.map((warehouse) => `<option value="${warehouse.id}">${warehouse.code} - ${warehouse.title}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("physicalLocation")}</span>
          <input name="physicalLocation" type="text" placeholder="A-01-R02" />
        </label>
        <label class="preview-field">
          <span>${t("movementDate")}</span>
          <input name="movementDate" type="date" value="${new Date().toISOString().slice(0, 10)}" required />
        </label>
        <label class="preview-field wide-field">
          <span>${t("reason")}</span>
          <textarea name="reason" rows="3" placeholder="${t("movementReasonPlaceholder")}"></textarea>
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-movement">${t("cancel")}</button>
        <button class="primary-action" type="submit">${t("saveMovement")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-movement']").addEventListener("click", closeModal);
  const movementItemSearch = modalContent.querySelector("#movementItemSearch");
  const movementItemResults = modalContent.querySelector("#movementItemResults");
  if (movementItemSearch && movementItemResults) {
    movementItemSearch.addEventListener("focus", renderMovementItemLookup);
    movementItemSearch.addEventListener("input", syncMovementItemFields);
    movementItemResults.addEventListener("click", selectMovementItemFromLookup);
  }
  modalContent.querySelector("#movementForm").addEventListener("submit", (event) => saveInventoryMovementForm(event, module, submodule));
}

function formatInventoryItemOption(item) {
  return `${item.code} - ${item.title} - ${translateInventoryItemType(item.fields?.type)}`;
}

function findInventoryItemByOption(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return mockDb.loadModuleRecords("almacenes", "articulos").find((item) =>
    item.recordType === "inventoryItem" &&
    (formatInventoryItemOption(item).toLowerCase() === normalized || item.code.toLowerCase() === normalized)
  );
}

function getInventoryItemMatches(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const items = mockDb.loadModuleRecords("almacenes", "articulos").filter((record) => record.recordType === "inventoryItem");
  if (!normalized) return items;
  return items.filter((item) =>
    [
      item.code,
      item.title,
      translateInventoryItemType(item.fields?.type),
      item.fields?.category,
      item.fields?.unit,
      item.fields?.defaultWarehouseName
    ]
      .join(" ")
      .toLowerCase()
      .includes(normalized)
  );
}

function renderMovementItemLookup(event) {
  const input = event.target;
  const results = modalContent.querySelector("#movementItemResults");
  const matches = getInventoryItemMatches(input.value);
  results.hidden = false;
  results.innerHTML = matches.length
    ? matches
        .map((item) => `
          <button class="lookup-option" type="button" data-inventory-item-id="${item.id}">
            <strong>${item.title}</strong>
            <span>${item.code} - ${translateInventoryItemType(item.fields?.type)} - ${item.fields?.unit || t("notDefined")}</span>
          </button>
        `)
        .join("")
    : `<div class="lookup-empty">${t("itemLookupEmpty")}</div>`;
}

function selectMovementItemFromLookup(event) {
  const button = event.target.closest("[data-inventory-item-id]");
  if (!button) return;
  const item = mockDb.findModuleRecord("almacenes", button.dataset.inventoryItemId);
  if (!item) return;
  const form = button.closest("form");
  form.querySelector("#movementItemSearch").value = formatInventoryItemOption(item);
  form.querySelector("[name='itemId']").value = item.id;
  form.querySelector("[name='unit']").value = normalizeUnitCode(item.fields?.unit || "H87");
  modalContent.querySelector("#movementItemResults").hidden = true;
}

function syncMovementItemFields(event) {
  const form = event.target.closest("form");
  const item = findInventoryItemByOption(event.target.value);
  form.querySelector("[name='itemId']").value = item?.id || "";
  renderMovementItemLookup(event);
  if (!item) return;
  form.querySelector("[name='unit']").value = normalizeUnitCode(item.fields?.unit || "H87");
}

async function saveInventoryMovementForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.sourceDocument?.trim()) errors.push(t("sourceDocumentRequired"));
  if (!data.itemId && !data.item?.trim()) errors.push(t("itemRequired"));
  if (!Number(data.quantity || 0)) errors.push(t("quantityRequired"));
  if (!data.unit?.trim()) errors.push(t("unitRequired"));
  if (!data.warehouseId && !data.warehouseName?.trim()) errors.push(t("warehouseRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const warehouse = data.warehouseId ? mockDb.findModuleRecord(module.id, data.warehouseId) : null;
  const item = data.itemId ? mockDb.findModuleRecord(module.id, data.itemId) : null;
  const code = `MOV-${String(Date.now()).slice(-5)}`;
  const warehouseName = warehouse ? `${warehouse.code} - ${warehouse.title}` : data.warehouseName.trim();
  const itemName = item ? `${item.code} - ${item.title}` : data.item.trim();
  const movementQuantity = Number(data.quantity || 0);
  if (data.movementType === "transfer" && (!data.destinationWarehouseId || data.destinationWarehouseId === data.warehouseId)) {
    renderFormErrors([t("transferDestinationRequired")]);
    return;
  }
  if (["exit", "negativeAdjustment"].includes(data.movementType)) {
    const itemKey = data.itemId || itemName;
    const warehouseKey = data.warehouseId || warehouseName;
    const available = getAvailableStock(itemKey, warehouseKey, data.unit.trim());
    if (available < movementQuantity) {
      renderFormErrors([t("insufficientStock", { available: formatNumber(available), unit: data.unit.trim() })]);
      return;
    }
  }
  if (getApiMode() === "api" && isInventoryApiEnabled()) {
    const types = { positiveAdjustment: "positive_adjustment", negativeAdjustment: "negative_adjustment" };
    try {
      const savedMovement = await createInventoryMovement({
        movement_type: types[data.movementType] || data.movementType,
        inventory_item_id: data.itemId,
        warehouse_id: data.warehouseId,
        destination_warehouse_id: data.destinationWarehouseId || null,
        quantity: movementQuantity,
        unit: data.unit.trim(),
        reason: data.reason?.trim() || "Movimiento manual",
        source: { type: "manual", id: data.sourceDocument.trim() },
        occurred_at: `${data.movementDate}T12:00:00Z`
      });
      state.inventoryMovements = { status: "idle", error: "" };
      state.inventoryBalances = { status: "idle", data: [], page: {}, error: "", queryKey: "", cursor: "", previousCursors: [] };
      closeModal();
      await loadInventoryMovementData();
      showToast(t("movementSaved", { code: savedMovement.movement_code }));
    } catch (error) {
      renderFormErrors([error.message || t("inventoryLoadError")]);
    }
    return;
  }
  const record = {
    id: `${module.id}-movement-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId: submodule.id,
    recordType: "inventoryMovement",
    title: itemName,
    detail: `${translateMovementType(data.movementType)} - ${data.quantity} ${data.unit} - ${warehouseName}`,
    status: "Registrado",
    owner: warehouseName,
    fields: {
      movementType: data.movementType,
      sourceDocument: data.sourceDocument.trim(),
      itemId: data.itemId || "",
      item: itemName,
      quantity: data.quantity,
      unit: data.unit.trim(),
      warehouseId: data.warehouseId || "",
      warehouseName,
      physicalLocation: data.physicalLocation?.trim() || "",
      movementDate: data.movementDate,
      reason: data.reason?.trim() || ""
    },
    createdAt: new Date().toISOString()
  };

  mockDb.addModuleRecord(module.id, record);
  closeModal();
  render();
  showToast(t("movementSaved", { code }));
}

function openSalesCustomerModal(module, submodule, recordId = null) {
  const requiredPermission = recordId ? "sales.customer.update" : "sales.customer.create";
  if (getApiMode() === "api" && !hasPermission(requiredPermission)) {
    showToast(t("salesActionDenied"));
    return;
  }
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || {};
  const isEditing = Boolean(existingRecord);
  const salesWorkers=state.salesApi.workers||[];const references=state.salesApi.references||{currencies:[],payment_terms:[]};
  if (getApiMode() === "api" && (!salesWorkers.length || !references.currencies.length || !references.payment_terms.length)) {
    showToast((state.salesApi.referenceWarnings || []).join(" ") || t("salesWorkersUnavailable"));
    return;
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesCustomerForm">
      <input type="hidden" name="recordId" value="${escapeAttribute(existingRecord?.id || "")}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("sales.customer"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${isEditing ? t("editCustomer") : t("newCustomer")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="section-title form-section-title wide-field">
        <span class="section-icon">▦</span>
        <strong>${t("commercialProfile")}</strong>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("customerCode")}</span>
          <input name="code" type="text" value="${escapeAttribute(existingRecord?.code || "")}" placeholder="${codeSequenceConfig("sales.customer")?.mode === "managed" ? t("codeAssignedAutomatically") : "CLI-001"}" ${isEditing || codeSequenceConfig("sales.customer")?.mode === "managed" ? "readonly" : ""} />
        </label>
        <label class="preview-field">
          <span>${t("commercialName")}</span>
          <input name="commercialName" type="text" value="${escapeAttribute(fields.commercialName || existingRecord?.title || "")}" placeholder="${escapeAttribute(t("commercialNamePlaceholder"))}" required />
        </label>
        <label class="preview-field">
          <span>${t("customerType")}</span>
          <select name="customerType" required>
            <option value="company" ${selectedOption(fields.customerType || "company", "company")}>${t("companyCustomer")}</option>
            <option value="individual" ${selectedOption(fields.customerType, "individual")}>${t("individualCustomer")}</option>
            <option value="government" ${selectedOption(fields.customerType, "government")}>${t("governmentCustomer")}</option>
            <option value="internal" ${selectedOption(fields.customerType, "internal")}>${t("internalCustomer")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            <option value="Prospecto" ${selectedOption(existingRecord?.status || "Prospecto", "Prospecto")}>${t("prospectStatus")}</option>
            <option value="Activo" ${selectedOption(existingRecord?.status, "Activo")}>${t("activeStatus")}</option>
            <option value="Inactivo" ${selectedOption(existingRecord?.status, "Inactivo")}>${t("inactiveStatus")}</option>
            <option value="Bloqueado" ${selectedOption(existingRecord?.status, "Bloqueado")}>${t("blockedStatus")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("contact")}</span>
          <input name="contactName" type="text" value="${escapeAttribute(fields.contactName || "")}" placeholder="${escapeAttribute(t("contactPlaceholder"))}" required />
        </label>
        <label class="preview-field">
          <span>${t("commercialEmail")}</span>
          <input name="contactEmail" type="email" value="${escapeAttribute(fields.contactEmail || "")}" placeholder="compras@cliente.com" required />
        </label>
        <label class="preview-field">
          <span>${t("phone")}</span>
          <input name="contactPhone" type="tel" value="${escapeAttribute(fields.contactPhone || "")}" placeholder="+52 55 0000 0000" required />
        </label>
        <label class="preview-field">
          <span>${t("salesOwner")}</span>
          <select name="responsibleWorkerId" data-entity-selector required><option value="">Selecciona una persona activa</option>${salesWorkers.map(worker=>`<option value="${escapeAttribute(worker.id)}" ${selectedOption(fields.responsibleWorkerId,worker.id)}>${escapeHtml(worker.full_name)} · ${escapeHtml(worker.position_name)}</option>`).join("")}</select>
        </label>
        <label class="preview-field">
          <span>${t("paymentTerms")}</span>
          <select name="paymentTerms" required>${references.payment_terms.map(item=>`<option value="${item.code}" ${selectedOption(fields.paymentTerms||"cash",item.code)}>${escapeHtml(state.lang==="en"?item.name_en:item.name_es)}</option>`).join("")}</select>
        </label>
        <label class="preview-field">
          <span>${t("creditLimit")}</span>
          <input name="creditLimit" type="number" min="0" step="0.01" value="${fields.creditLimit || 0}" />
        </label>
        <label class="preview-field">
          <span>${t("currency")}</span>
          <select name="currency" required>${references.currencies.map(item=>`<option value="${item.code}" ${selectedOption(fields.currency||"MXN",item.code)}>${escapeHtml(item.code)} · ${escapeHtml(state.lang==="en"?item.name_en:item.name_es)}</option>`).join("")}</select>
        </label>
        <label class="preview-field wide-field">
          <span>${t("commercialNotes")}</span>
          <textarea name="commercialNotes" rows="2" placeholder="${escapeAttribute(t("commercialNotesPlaceholder"))}">${escapeHtml(fields.commercialNotes || "")}</textarea>
        </label>

        <div class="section-title form-section-title wide-field">
          <span class="section-icon">☷</span>
          <strong>${t("billingProfile")}</strong>
        </div>

        <label class="preview-field">
          <span>${t("billingLegalName")}</span>
          <input name="billingLegalName" type="text" value="${escapeAttribute(fields.billingLegalName || "")}" placeholder="${escapeAttribute(t("billingLegalNamePlaceholder"))}" />
        </label>
        <label class="preview-field">
          <span>${t("taxId")}</span>
          <input name="taxId" type="text" value="${escapeAttribute(fields.taxId || "")}" placeholder="XAXX010101000" />
        </label>
        <label class="preview-field">
          <span>${t("taxRegime")}</span>
          <input name="taxRegime" type="text" value="${escapeAttribute(fields.taxRegime || "")}" placeholder="${escapeAttribute(t("taxRegimePlaceholder"))}" />
        </label>
        <label class="preview-field">
          <span>${t("cfdiUse")}</span>
          <input name="cfdiUse" type="text" value="${escapeAttribute(fields.cfdiUse || "")}" placeholder="G03" />
        </label>
        <label class="preview-field">
          <span>${t("billingEmail")}</span>
          <input name="billingEmail" type="email" value="${escapeAttribute(fields.billingEmail || "")}" placeholder="facturas@cliente.com" />
        </label>
        <label class="preview-field">
          <span>${t("billingPhone")}</span>
          <input name="billingPhone" type="tel" value="${escapeAttribute(fields.billingPhone || "")}" placeholder="+52 55 0000 0000" />
        </label>
        <label class="preview-field">
          <span>${t("billingStreet")}</span>
          <input name="billingStreet" type="text" value="${escapeAttribute(fields.billingStreet || "")}" placeholder="${escapeAttribute(t("billingStreetPlaceholder"))}" />
        </label>
        <label class="preview-field">
          <span>${t("billingExterior")}</span>
          <input name="billingExterior" type="text" value="${escapeAttribute(fields.billingExterior || "")}" placeholder="123" />
        </label>
        <label class="preview-field">
          <span>${t("billingInterior")}</span>
          <input name="billingInterior" type="text" value="${escapeAttribute(fields.billingInterior || "")}" placeholder="4B" />
        </label>
        <label class="preview-field">
          <span>${t("billingNeighborhood")}</span>
          <input name="billingNeighborhood" type="text" value="${escapeAttribute(fields.billingNeighborhood || "")}" placeholder="${escapeAttribute(t("billingNeighborhoodPlaceholder"))}" />
        </label>
        <label class="preview-field">
          <span>${t("billingCity")}</span>
          <input name="billingCity" type="text" value="${escapeAttribute(fields.billingCity || "")}" placeholder="${escapeAttribute(t("billingCityPlaceholder"))}" />
        </label>
        <label class="preview-field">
          <span>${t("billingState")}</span>
          <input name="billingState" type="text" value="${escapeAttribute(fields.billingState || "")}" placeholder="${escapeAttribute(t("billingStatePlaceholder"))}" />
        </label>
        <label class="preview-field">
          <span>${t("billingZipCode")}</span>
          <input name="billingZipCode" type="text" value="${escapeAttribute(fields.billingZipCode || "")}" placeholder="00000" />
        </label>
        <label class="preview-field">
          <span>${t("billingCountry")}</span>
          <input name="billingCountry" type="text" value="${escapeAttribute(fields.billingCountry || "Mexico")}" />
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-sales-customer">${t("cancel")}</button>
        <button class="primary-action" type="submit">${isEditing ? t("updateCustomer") : t("saveCustomer")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-sales-customer']").addEventListener("click", closeModal);
  modalContent.querySelector("#salesCustomerForm").addEventListener("submit", (event) => saveSalesCustomerForm(event, module, submodule));
}

async function saveSalesCustomerForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim() && getApiMode() !== "api") errors.push(t("customerCodeRequired"));
  if (!data.commercialName?.trim()) errors.push(t("commercialNameRequired"));
  if (!data.contactName?.trim()) errors.push(t("contactRequired"));
  if (!data.contactEmail?.trim()) errors.push(t("commercialEmailRequired"));
  if (!data.contactPhone?.trim()) errors.push(t("phoneRequired"));
  if (!data.responsibleWorkerId) errors.push("Selecciona una persona responsable activa de RH.");
  const fiscalStarted=[data.billingLegalName,data.taxId,data.taxRegime,data.cfdiUse,data.billingEmail,data.billingStreet,data.billingCity,data.billingState,data.billingZipCode].some(value=>value?.trim());
  if(fiscalStarted&&!data.billingLegalName?.trim()) errors.push(t("billingLegalNameRequired"));
  if(fiscalStarted&&!data.taxId?.trim()) errors.push(t("taxIdRequired"));
  if(fiscalStarted&&!data.billingEmail?.trim()) errors.push(t("billingEmailRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  let code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
  if(getApiMode()==="api"){
    const payload={commercial_name:data.commercialName.trim(),customer_type:data.customerType,status:salesCustomerStatusToApi[data.status]||"prospect",responsible_worker_id:data.responsibleWorkerId,primary_contact:{name:data.contactName.trim(),email:data.contactEmail.trim(),phone:data.contactPhone.trim()},payment_terms:data.paymentTerms,currency:data.currency,credit_limit:Number(data.creditLimit||0),legal_name:data.billingLegalName?.trim()||null,tax_id:data.taxId?.trim().toUpperCase()||null,tax_regime:data.taxRegime?.trim()||null,cfdi_use:data.cfdiUse?.trim()||null,billing_email:data.billingEmail?.trim()||null,billing_phone:data.billingPhone?.trim()||null,billing_address:fiscalStarted?{street:data.billingStreet?.trim()||null,exterior_number:data.billingExterior?.trim()||null,interior_number:data.billingInterior?.trim()||null,neighborhood:data.billingNeighborhood?.trim()||null,city:data.billingCity?.trim()||null,state:data.billingState?.trim()||null,postal_code:data.billingZipCode?.trim()||null,country:data.billingCountry?.trim()||null}:null,notes:data.commercialNotes?.trim()||null};
    try{if(existingRecord)await updateSalesCustomer(existingRecord.id,payload);else {code=await resolveBusinessCode("sales.customer",code,data.codeRequestKey);await createSalesCustomer({code,...payload});}closeModal();await loadSalesApiData();showToast(t(existingRecord?"customerUpdated":"customerSaved",{code}));}catch(error){renderFormErrors([error.message||"No se pudo guardar el cliente."]);}return;
  }
  const fields = {
    customerType: data.customerType,
    commercialName: data.commercialName.trim(),
    contactName: data.contactName.trim(),
    contactEmail: data.contactEmail.trim(),
    contactPhone: data.contactPhone.trim(),
    salesOwner: data.salesOwner?.trim() || "",
    paymentTerms: data.paymentTerms?.trim() || "",
    creditLimit: data.creditLimit?.trim() || "",
    commercialNotes: data.commercialNotes?.trim() || "",
    billingLegalName: data.billingLegalName.trim(),
    taxId: data.taxId.trim().toUpperCase(),
    taxRegime: data.taxRegime?.trim() || "",
    cfdiUse: data.cfdiUse?.trim() || "",
    billingEmail: data.billingEmail.trim(),
    billingPhone: data.billingPhone?.trim() || "",
    billingStreet: data.billingStreet.trim(),
    billingExterior: data.billingExterior?.trim() || "",
    billingInterior: data.billingInterior?.trim() || "",
    billingNeighborhood: data.billingNeighborhood?.trim() || "",
    billingCity: data.billingCity.trim(),
    billingState: data.billingState.trim(),
    billingZipCode: data.billingZipCode.trim(),
    billingCountry: data.billingCountry?.trim() || "Mexico"
  };
  const record = {
    id: existingRecord?.id || `${module.id}-customer-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId: submodule.id,
    recordType: "customer",
    title: fields.commercialName,
    detail: `${fields.billingLegalName} - ${fields.taxId} - ${fields.contactName}`,
    status: data.status || "Prospecto",
    owner: fields.salesOwner || fields.contactName,
    fields,
    createdAt: new Date().toISOString()
  };

  if (existingRecord) {
    mockDb.updateModuleRecord(module.id, {
      ...record,
      createdAt: existingRecord.createdAt,
      updatedAt: new Date().toISOString()
    });
  } else {
    mockDb.addModuleRecord(module.id, record);
  }
  closeModal();
  render();
  showToast(t(existingRecord ? "customerUpdated" : "customerSaved", { code }));
}

async function openSalesQuoteModal(module, submodule, recordId = null) {
  const requiredPermission = recordId ? "sales.quote.update" : "sales.quote.create";
  if (getApiMode() === "api" && (!hasPermission(requiredPermission) || !hasPermission("sales.customer.read"))) {
    showToast(t("salesActionDenied"));
    return;
  }
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || {};
  const customers = mockDb.loadModuleRecords(module.id, "clientes").filter((record) => record.recordType === "customer" && record.status === "Activo");
  let productsServices = mockDb.loadProductsServices().filter(isSalesProductServiceEligible);
  if (getApiMode()==="api" && !productsServices.length) {
    try {
      const authoritativeProducts=await getProductionProducts();
      mockDb.saveProductsServices(authoritativeProducts.map(mapApiProduct));
      productsServices=mockDb.loadProductsServices().filter(isSalesProductServiceEligible);
    } catch (_) { productsServices=[]; }
  }
  const selectedCustomer = fields.customerId ? mockDb.findModuleRecord(module.id, fields.customerId) : null;
  const quoteLines = normalizeQuoteLines(fields);
  const isEditing = Boolean(existingRecord);

  if (!customers.length || !productsServices.length || (getApiMode() === "api" && !getUnitCatalog().length)) {
    showToast(!customers.length ? t("quoteRequiresCustomers") : t("quoteRequiresProducts"));
    return;
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesQuoteForm">
      <input type="hidden" name="recordId" value="${escapeAttribute(existingRecord?.id || "")}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("sales.quote"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${isEditing ? t("editQuote") : t("newQuote")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("quoteCode")}</span>
          <input name="code" type="text" value="${escapeAttribute(existingRecord?.code || "")}" placeholder="${codeSequenceConfig("sales.quote")?.mode === "managed" ? t("codeAssignedAutomatically") : "COT-001"}" ${isEditing || codeSequenceConfig("sales.quote")?.mode === "managed" ? "readonly" : ""} />
        </label>
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status" disabled>
            <option value="Borrador" ${selectedOption(existingRecord?.status || "Borrador", "Borrador")}>${t("draftStatus")}</option>
            <option value="Cotizada" ${selectedOption(existingRecord?.status, "Cotizada")}>${t("quotedStatus")}</option>
            <option value="Aprobado" ${selectedOption(existingRecord?.status, "Aprobado")}>${t("approvedStatus")}</option>
            <option value="Vencida" ${selectedOption(existingRecord?.status, "Vencida")}>${t("expiredStatus")}</option>
          </select>
        </label>
        <label class="preview-field product-lookup-field wide-field">
          <span>${t("customer")}</span>
          <input id="quoteCustomerSearch" type="text" value="${escapeAttribute(selectedCustomer ? formatSalesCustomerOption(selectedCustomer) : "")}" placeholder="${escapeAttribute(t("customerLookupPlaceholder"))}" autocomplete="off" required />
          <input name="customerId" type="hidden" value="${escapeAttribute(selectedCustomer?.id || "")}" />
          <div class="lookup-results" id="quoteCustomerResults" hidden></div>
        </label>
        <div class="section-title form-section-title wide-field">
          <span class="section-icon">☷</span>
          <strong>${t("quoteLines")}</strong>
        </div>
        <p class="helper-copy wide-field">${t("quoteLinesHelper")}</p>
        <div class="selected-resource-list wide-field" id="quoteLineList">
          ${quoteLines.map((line, index) => renderQuoteLineRow(line, index)).join("")}
        </div>
        <button class="secondary-action wide-field" type="button" data-action="add-quote-line">${t("addQuoteLine")}</button>
        <label class="preview-field">
          <span>${t("validUntil")}</span>
          <input name="validUntil" type="date" value="${escapeAttribute(fields.validUntil || "")}" required />
        </label>
        <label class="preview-field">
          <span>${t("deliveryPromise")}</span>
          <input name="deliveryPromise" type="date" value="${escapeAttribute(fields.deliveryPromise || "")}" />
        </label>
        <label class="preview-field">
          <span>${t("paymentTerms")}</span>
          <select name="paymentTerms">${(state.salesApi.references?.payment_terms||[]).map(item=>`<option value="${item.code}" ${selectedOption(fields.paymentTerms||selectedCustomer?.fields?.paymentTerms||"cash",item.code)}>${escapeHtml(state.lang==="en"?item.name_en:item.name_es)}</option>`).join("")}</select>
        </label>
        <label class="preview-field">
          <span>${t("currency")}</span>
          <select name="currency" required>${(state.salesApi.references?.currencies||[]).map(item=>`<option value="${item.code}" ${selectedOption(fields.currency||selectedCustomer?.fields?.currency||"MXN",item.code)}>${escapeHtml(item.code)} · ${escapeHtml(state.lang==="en"?item.name_en:item.name_es)}</option>`).join("")}</select>
        </label>
        <label class="preview-field wide-field">
          <span>${t("notes")}</span>
          <textarea name="notes" rows="3" placeholder="${escapeAttribute(t("quoteNotesPlaceholder"))}">${escapeHtml(fields.notes || "")}</textarea>
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-sales-quote">${t("cancel")}</button>
        <button class="primary-action" type="submit">${isEditing ? t("updateQuote") : t("saveQuote")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-sales-quote']").addEventListener("click", closeModal);
  modalContent.querySelector("#quoteCustomerSearch").addEventListener("focus", renderQuoteCustomerLookup);
  modalContent.querySelector("#quoteCustomerSearch").addEventListener("input", syncQuoteCustomerFields);
  modalContent.querySelector("#quoteCustomerResults").addEventListener("click", selectQuoteCustomerFromLookup);
  modalContent.querySelector("[data-action='add-quote-line']").addEventListener("click", addQuoteLineRow);
  modalContent.querySelector("#salesQuoteForm").addEventListener("submit", (event) => saveSalesQuoteForm(event, module, submodule));
  bindQuoteLineActions();
}

function formatSalesCustomerOption(customer) {
  return `${customer.code} - ${customer.title} - ${customer.fields?.taxId || t("notDefined")}`;
}

function findSalesCustomerByOption(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return mockDb.loadModuleRecords("ventas", "clientes").find((customer) =>
    customer.recordType === "customer" &&
    (formatSalesCustomerOption(customer).toLowerCase() === normalized || customer.code.toLowerCase() === normalized)
  );
}

function getSalesCustomerMatches(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const customers = mockDb.loadModuleRecords("ventas", "clientes").filter((record) => record.recordType === "customer");
  if (!normalized) return customers;
  return customers.filter((customer) =>
    [
      customer.code,
      customer.title,
      customer.fields?.commercialName,
      customer.fields?.billingLegalName,
      customer.fields?.taxId,
      customer.fields?.contactName,
      customer.fields?.contactEmail
    ]
      .join(" ")
      .toLowerCase()
      .includes(normalized)
  );
}

function renderQuoteCustomerLookup(event) {
  const input = event.target;
  const results = modalContent.querySelector("#quoteCustomerResults");
  const matches = getSalesCustomerMatches(input.value);
  results.hidden = false;
  results.innerHTML = matches.length
    ? matches
        .map((customer) => `
          <button class="lookup-option" type="button" data-sales-customer-id="${escapeAttribute(customer.id)}">
            <strong>${escapeHtml(customer.title)}</strong>
            <span>${escapeHtml(customer.code)} - ${escapeHtml(customer.fields?.billingLegalName || t("notDefined"))} - ${escapeHtml(customer.fields?.taxId || t("notDefined"))}</span>
          </button>
        `)
        .join("")
    : `<div class="lookup-empty">${t("customerLookupEmpty")}</div>`;
}

function selectQuoteCustomerFromLookup(event) {
  const button = event.target.closest("[data-sales-customer-id]");
  if (!button) return;
  const customer = mockDb.findModuleRecord("ventas", button.dataset.salesCustomerId);
  if (!customer) return;
  const form = button.closest("form");
  form.querySelector("#quoteCustomerSearch").value = formatSalesCustomerOption(customer);
  form.querySelector("[name='customerId']").value = customer.id;
  form.querySelector("[name='paymentTerms']").value = customer.fields?.paymentTerms || "";
  modalContent.querySelector("#quoteCustomerResults").hidden = true;
}

function syncQuoteCustomerFields(event) {
  const form = event.target.closest("form");
  const customer = findSalesCustomerByOption(event.target.value);
  form.querySelector("[name='customerId']").value = customer?.id || "";
  renderQuoteCustomerLookup(event);
  if (!customer) return;
  form.querySelector("[name='paymentTerms']").value = customer.fields?.paymentTerms || "";
}

function normalizeQuoteLines(fields = {}) {
  if (Array.isArray(fields.lines) && fields.lines.length) return fields.lines;
  if (fields.productServiceId) {
    return [{
      productServiceId: fields.productServiceId,
      productServiceName: fields.productServiceName || "",
      quantity: fields.quantity || 1,
      unit: fields.unit || "",
      unitPrice: fields.unitPrice || 0,
      discount: fields.discount || 0,
      subtotal: fields.subtotal || 0,
      total: fields.total || 0
    }];
  }
  return [{ productServiceId: "", productServiceName: "", quantity: 1, unit: "", unitPrice: 0, discount: 0 }];
}

function getQuoteLines(record) {
  return normalizeQuoteLines(record?.fields || {});
}

function openFinishedGoodsReceiptModal(orderId){
  const row=getPendingFinishedGoodsReceipts().find((entry)=>entry.order.id===orderId);if(!row||!row.item){showToast(t("finishedGoodsReceiptUnavailable"));return;}
  const warehouses=mockDb.loadModuleRecords("almacenes","almacenes").filter((record)=>record.recordType==="warehouse"&&record.status==="Activo");
  const preferred=row.item.fields?.defaultWarehouseId||warehouses[0]?.id||"";
  modalContent.innerHTML=`<form class="recipe-form" id="finishedGoodsReceiptForm"><div class="modal-head"><div><p class="eyebrow">${t("inventory")}</p><h2>${t("receiveFinishedGood")}</h2></div><button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button></div>
    <input type="hidden" name="productionOrderId" value="${escapeAttribute(row.order.id)}" />
    <section class="section-card"><strong>${escapeHtml(row.order.code)} · ${escapeHtml(row.product.name)}</strong><p>${escapeHtml(row.item.code)} · ${escapeHtml(row.item.title)}</p><p>${t("finishedGoodsPendingDetail",{received:formatNumber(row.received),remaining:formatNumber(row.remaining),quantity:formatNumber(row.order.quantity),unit:row.order.unit})}</p></section>
    <div class="form-grid"><label class="preview-field"><span>${t("warehouse")}</span><select name="warehouseId" data-entity-selector required>${warehouses.map((warehouse)=>`<option value="${escapeAttribute(warehouse.id)}" ${warehouse.id===preferred?"selected":""}>${escapeHtml(warehouse.code)} - ${escapeHtml(warehouse.title)}</option>`).join("")}</select></label>
    <label class="preview-field"><span>${t("receivedQuantity")}</span><input name="quantity" type="number" min="0.000001" max="${row.remaining}" step="any" value="${row.remaining}" required /></label>
    <label class="preview-field"><span>${t("receiptDate")}</span><input name="receivedAt" type="date" value="${new Date().toISOString().slice(0,10)}" required /></label>
    <label class="preview-field wide-field"><span>${t("notes")}</span><textarea name="notes" rows="3" placeholder="${t("finishedGoodsReceiptNotes")}"></textarea></label></div>
    <div class="form-errors" id="formErrors" hidden></div><div class="modal-actions"><button class="secondary-action" type="button" data-action="close-finished-receipt">${t("cancel")}</button><button class="primary-action" type="submit">${t("confirmReceipt")}</button></div></form>`;
  modalBackdrop.hidden=false;modalContent.querySelector(".modal-close").addEventListener("click",closeModal);modalContent.querySelector("[data-action='close-finished-receipt']").addEventListener("click",closeModal);modalContent.querySelector("#finishedGoodsReceiptForm").addEventListener("submit",saveFinishedGoodsReceiptForm);
}

async function saveFinishedGoodsReceiptForm(event){
  event.preventDefault();const form=event.currentTarget;const data=Object.fromEntries(new FormData(form).entries());const quantity=Number(data.quantity||0);
  if(!data.warehouseId||quantity<=0||!data.receivedAt){renderFormErrors([t("finishedGoodsReceiptRequired")]);return;}
  try{const receipt=await createFinishedGoodsReceipt({production_order_id:data.productionOrderId,warehouse_id:data.warehouseId,quantity,received_at:`${data.receivedAt}T12:00:00Z`,notes:data.notes?.trim()||null});state.finishedGoodsReceipts={status:"idle",orders:[],products:[],summaries:[],error:""};state.inventoryMovements={status:"idle",error:""};state.inventoryBalances={status:"idle",data:[],page:{},error:"",queryKey:"",cursor:"",previousCursors:[]};closeModal();await Promise.all([loadInventoryMovementData(),loadFinishedGoodsReceiptData()]);showToast(t("finishedGoodsReceiptSaved",{code:receipt.movement.movement_code}));}catch(error){renderFormErrors([error.message||t("finishedGoodsReceiptSaveError")]);}
}

function isSalesProductServiceEligible(item) {
  return getApiMode() !== "api" || item?.kind === "Servicio" || Boolean(item?.inventoryItemId);
}

function renderQuoteLineRow(line = {}, index = 0) {
  const productService = line.productServiceId ? mockDb.findProductService(line.productServiceId) : null;
  return `
    <div class="quote-line-row" data-quote-line>
      <label class="preview-field product-lookup-field quote-line-product">
        <span>${t("productOrService")}</span>
        <input class="quote-product-search" type="text" value="${escapeAttribute(productService ? formatProductServiceOption(productService) : line.productServiceName || "")}" placeholder="${escapeAttribute(t("productLookupPlaceholder"))}" autocomplete="off" required />
        <input name="lineProductServiceId" type="hidden" value="${escapeAttribute(line.productServiceId || "")}" />
        <div class="lookup-results quote-product-results" hidden></div>
      </label>
      <label class="preview-field">
        <span>${t("quantity")}</span>
        <input name="lineQuantity" type="number" min="0.01" step="0.01" value="${escapeAttribute(line.quantity || 1)}" required />
      </label>
      <label class="preview-field">
        <span>${t("unit")}</span>
        ${unitSelect("lineUnit", line.unit || productService?.unit || "H87")}
      </label>
      <label class="preview-field">
        <span>${t("unitPrice")}</span>
        <input name="lineUnitPrice" type="number" min="0" step="0.01" value="${escapeAttribute(line.unitPrice || productService?.targetPrice || 0)}" required />
      </label>
      <label class="preview-field">
        <span>${t("discount")}</span>
        <input name="lineDiscount" type="number" min="0" max="100" step="0.01" value="${escapeAttribute(line.discount || 0)}" />
      </label>
      <button class="icon-button remove-resource" type="button" data-action="remove-quote-line" aria-label="${t("removeQuoteLine")}">x</button>
    </div>
  `;
}

function addQuoteLineRow() {
  const list = modalContent.querySelector("#quoteLineList");
  list.insertAdjacentHTML("beforeend", renderQuoteLineRow({}, list.querySelectorAll("[data-quote-line]").length));
  bindQuoteLineActions();
}

function bindQuoteLineActions() {
  modalContent.querySelectorAll(".quote-product-search").forEach((input) => {
    input.removeEventListener("focus", renderQuoteProductLookup);
    input.removeEventListener("input", syncQuoteProductFields);
    input.addEventListener("focus", renderQuoteProductLookup);
    input.addEventListener("input", syncQuoteProductFields);
  });
  modalContent.querySelectorAll(".quote-product-results").forEach((results) => {
    results.removeEventListener("click", selectQuoteProductFromLookup);
    results.addEventListener("click", selectQuoteProductFromLookup);
  });
  modalContent.querySelectorAll("[data-action='remove-quote-line']").forEach((button) => {
    button.onclick = () => {
      const rows = modalContent.querySelectorAll("[data-quote-line]");
      if (rows.length <= 1) {
        showToast(t("quoteNeedsOneLine"));
        return;
      }
      button.closest("[data-quote-line]").remove();
    };
  });
}

function renderQuoteProductLookup(event) {
  const input = event.target;
  const row = input.closest("[data-quote-line]");
  const results = row.querySelector(".quote-product-results");
  const matches = getProductServiceMatches(input.value).filter(isSalesProductServiceEligible);
  results.hidden = false;
  results.innerHTML = matches.length
    ? matches
        .map((item) => `
          <button class="lookup-option" type="button" data-product-id="${escapeAttribute(item.id)}">
            <strong>${escapeHtml(item.name)}</strong>
            <span>${escapeHtml(item.sku)} · ${escapeHtml(item.kind)} · ${escapeHtml(item.unit)}</span>
          </button>
        `)
        .join("")
    : `<div class="lookup-empty">${t("productLookupEmpty")}</div>`;
}

function selectQuoteProductFromLookup(event) {
  const button = event.target.closest("[data-product-id]");
  if (!button) return;
  const item = mockDb.findProductService(button.dataset.productId);
  if (!item || !isSalesProductServiceEligible(item)) return;
  const row = button.closest("[data-quote-line]");
  row.querySelector(".quote-product-search").value = formatProductServiceOption(item);
  row.querySelector("[name='lineProductServiceId']").value = item.id;
  row.querySelector("[name='lineUnit']").value = normalizeUnitCode(item.unit || "H87");
  row.querySelector("[name='lineUnitPrice']").value = item.targetPrice || 0;
  row.querySelector(".quote-product-results").hidden = true;
}

function syncQuoteProductFields(event) {
  const row = event.target.closest("[data-quote-line]");
  const candidate = findProductServiceByOption(event.target.value);
  const item = isSalesProductServiceEligible(candidate) ? candidate : null;
  row.querySelector("[name='lineProductServiceId']").value = item?.id || "";
  renderQuoteProductLookup(event);
  if (!item) return;
  row.querySelector("[name='lineUnit']").value = normalizeUnitCode(item.unit || "H87");
  row.querySelector("[name='lineUnitPrice']").value = item.targetPrice || 0;
}

async function saveSalesQuoteForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim() && getApiMode() !== "api") errors.push(t("quoteCodeRequired"));
  if (!data.customerId) errors.push(t("quoteCustomerRequired"));
  if (!data.validUntil) errors.push(t("validUntilRequired"));

  const customer = mockDb.findModuleRecord(module.id, data.customerId);
  if (!customer) errors.push(t("quoteCustomerRequired"));
  const lines = buildQuoteLinesFromForm(form, errors);
  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const subtotal = lines.reduce((sum, line) => sum + line.subtotal, 0);
  const total = lines.reduce((sum, line) => sum + line.total, 0);
  let code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
  if(getApiMode()==="api"){
    const payload={customer_id:customer.id,currency:data.currency,payment_terms:data.paymentTerms,valid_until:data.validUntil,promised_delivery_date:data.deliveryPromise||null,notes:data.notes?.trim()||null,lines:lines.map(line=>({product_service_id:line.productServiceId,quantity:line.quantity,unit:line.unit,unit_price:line.unitPrice,discount_percentage:line.discount}))};
    try{if(existingRecord)await updateSalesQuote(existingRecord.id,payload);else {code=await resolveBusinessCode("sales.quote",code,data.codeRequestKey);await createSalesQuote({code,...payload});}closeModal();await loadSalesApiData();showToast(t(existingRecord?"quoteUpdated":"quoteSaved",{code}));}catch(error){renderFormErrors([error.message||"No se pudo guardar la cotización."]);}return;
  }
  const fields = {
    customerId: customer.id,
    customerName: `${customer.code} - ${customer.title}`,
    lines,
    productServiceId: lines[0]?.productServiceId || "",
    productServiceName: lines[0]?.productServiceName || "",
    quantity: lines.reduce((sum, line) => sum + line.quantity, 0),
    unit: lines[0]?.unit || "",
    unitPrice: lines[0]?.unitPrice || 0,
    discount: lines[0]?.discount || 0,
    subtotal,
    total,
    validUntil: data.validUntil,
    deliveryPromise: data.deliveryPromise || "",
    paymentTerms: data.paymentTerms?.trim() || "",
    currency: data.currency?.trim() || "MXN",
    notes: data.notes?.trim() || ""
  };
  const record = {
    id: existingRecord?.id || `${module.id}-quote-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId: submodule.id,
    recordType: "quote",
    title: `${customer.title} - ${lines.length} ${t("quoteLines")}`,
    detail: `${formatCurrency(total)} - ${fields.validUntil}`,
    status: data.status || "Borrador",
    owner: customer.title,
    fields,
    createdAt: new Date().toISOString()
  };

  if (existingRecord) {
    mockDb.updateModuleRecord(module.id, {
      ...record,
      createdAt: existingRecord.createdAt,
      updatedAt: new Date().toISOString()
    });
  } else {
    mockDb.addModuleRecord(module.id, record);
  }
  closeModal();
  render();
  showToast(t(existingRecord ? "quoteUpdated" : "quoteSaved", { code }));
}

function buildQuoteLinesFromForm(form, errors) {
  const rows = [...form.querySelectorAll("[data-quote-line]")];
  if (!rows.length) errors.push(t("quoteLineRequired"));
  return rows.map((row) => {
    const productServiceId = row.querySelector("[name='lineProductServiceId']").value;
    const productService = productServiceId ? mockDb.findProductService(productServiceId) : null;
    const quantity = Number(row.querySelector("[name='lineQuantity']").value || 0);
    const unit = row.querySelector("[name='lineUnit']").value.trim();
    const unitPrice = Number(row.querySelector("[name='lineUnitPrice']").value || 0);
    const discount = Number(row.querySelector("[name='lineDiscount']").value || 0);
    if (!productService) errors.push(t("quoteProductRequired"));
    if (!quantity) errors.push(t("quantityRequired"));
    if (!unit) errors.push(t("unitRequired"));
    if (unitPrice < 0) errors.push(t("unitPriceRequired"));
    const subtotal = quantity * unitPrice;
    const total = subtotal * (1 - Math.min(Math.max(discount, 0), 100) / 100);
    return {
      productServiceId,
      productServiceName: productService ? `${productService.id} - ${productService.name}` : "",
      quantity,
      unit,
      unitPrice,
      discount,
      subtotal,
      total
    };
  });
}

function openSalesOrderModal(module, submodule, quoteId = null) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const usedQuoteIds=new Set(mockDb.loadModuleRecords(module.id,"pedidos").filter(record=>record.recordType==="salesOrder"&&record.status!=="Cancelado").map(record=>record.fields?.quoteId).filter(Boolean));
  const approvedQuotes = mockDb.loadModuleRecords(module.id, "cotizaciones")
    .filter((record) => record.recordType === "quote" && record.status === "Aprobado" && !usedQuoteIds.has(record.id));
  const selectedQuote = quoteId
    ? approvedQuotes.find((quote) => quote.id === quoteId)
    : approvedQuotes[0];

  if (!approvedQuotes.length || !selectedQuote) {
    showToast(t("salesOrderRequiresApprovedQuote"));
    return;
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesOrderForm">
      <input type="hidden" name="quoteId" value="${escapeAttribute(selectedQuote.id)}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("sales.order"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${t("newSalesOrder")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("salesOrderCode")}</span>
          <input name="code" type="text" value="" placeholder="${codeSequenceConfig("sales.order")?.mode === "managed" ? t("codeAssignedAutomatically") : "PED-001"}" ${codeSequenceConfig("sales.order")?.mode === "managed" ? "readonly" : ""} />
        </label>
        <label class="preview-field wide-field product-lookup-field">
          <span>${t("quoteDocument")}</span>
          <input name="quoteSearch" type="search" value="${escapeAttribute(`${selectedQuote.code} - ${selectedQuote.fields?.customerName||selectedQuote.title}`)}" placeholder="${escapeAttribute(t("quoteLookupPlaceholder"))}" autocomplete="off" required />
          <div class="lookup-results" id="salesOrderQuoteResults" hidden></div>
          <small>${t("quoteLookupHelp")}</small>
        </label>
        ${getApiMode() !== "api" ? `<label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            <option value="Aprobado">${t("approvedStatus")}</option>
            <option value="En preparacion">${t("preparingStatus")}</option>
            <option value="Cancelado">${t("canceledStatus")}</option>
          </select>
        </label>` : ""}
        <label class="preview-field">
          <span>${t("deliveryPromise")}</span>
          <input name="deliveryPromise" type="date" value="${escapeAttribute(selectedQuote.fields?.deliveryPromise || "")}" />
        </label>
        ${getApiMode() !== "api" ? `<label class="preview-field">
          <span>${t("fulfillmentMode")}</span>
          <select name="fulfillmentMode">
            <option value="${escapeAttribute(t("pendingInventoryReview"))}">${t("pendingInventoryReview")}</option>
            <option value="${escapeAttribute(t("stockFulfillment"))}">${t("stockFulfillment")}</option>
            <option value="${escapeAttribute(t("productionFulfillment"))}">${t("productionFulfillment")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("owner")}</span>
          <input name="owner" type="text" value="${escapeAttribute(selectedQuote.owner || "")}" />
        </label>` : ""}
        <label class="preview-field wide-field">
          <span>${t("notes")}</span>
          <textarea name="notes" rows="3" placeholder="${escapeAttribute(t("salesOrderNotesPlaceholder"))}"></textarea>
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-sales-order">${t("cancel")}</button>
        <button class="primary-action" type="submit">${t("saveSalesOrder")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-sales-order']").addEventListener("click", closeModal);
  const quoteSearch=modalContent.querySelector("[name='quoteSearch']");
  const quoteResults=modalContent.querySelector("#salesOrderQuoteResults");
  const showQuotes=()=>renderSalesDocumentLookup(quoteResults,approvedQuotes,quoteSearch.value,"quote");
  quoteSearch.addEventListener("focus",showQuotes);
  quoteSearch.addEventListener("input",()=>{modalContent.querySelector("[name='quoteId']").value="";showQuotes();});
  quoteResults.addEventListener("click",event=>{
    const button=event.target.closest("[data-document-id]"); if(!button)return;
    const quote = approvedQuotes.find((item) => item.id === button.dataset.documentId);
    if (!quote) return;
    modalContent.querySelector("[name='quoteId']").value = quote.id;
    quoteSearch.value=`${quote.code} - ${quote.fields?.customerName||quote.title}`;
    quoteResults.hidden=true;
    modalContent.querySelector("[name='deliveryPromise']").value = quote.fields?.deliveryPromise || "";
    const ownerInput=modalContent.querySelector("[name='owner']");
    if(ownerInput)ownerInput.value=quote.owner||"";
  });
  modalContent.querySelector("#salesOrderForm").addEventListener("submit", (event) => saveSalesOrderForm(event, module, submodule));
}

async function saveSalesOrderForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];
  const quote = mockDb.findModuleRecord(module.id, data.quoteId);
  const existingOrder = mockDb.loadModuleRecords(module.id, submodule.id)
    .find((record) => record.recordType === "salesOrder" && record.fields?.quoteId === data.quoteId);

  if (!data.code?.trim() && getApiMode() !== "api") errors.push(t("salesOrderCodeRequired"));
  if (!quote || quote.status !== "Aprobado") errors.push(t("salesOrderRequiresApprovedQuote"));
  if (existingOrder) errors.push(t("salesOrderQuoteAlreadyUsed"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  if (getApiMode() === "api") {
    try {
      const businessCode=await resolveBusinessCode("sales.order",data.code,data.codeRequestKey);
      await createSalesOrder({code:businessCode,quote_id:data.quoteId,promised_delivery_date:data.deliveryPromise||null,notes:data.notes?.trim()||null});
      closeModal(); await loadSalesApiData(); navigateTo({active:"ventas",activeSubmodule:"pedidos",laborArea:""}); showToast(t("salesOrderSaved",{code:businessCode}));
    } catch (error) { renderFormErrors([error.message||"No se pudo crear el pedido."]); }
    return;
  }

  const lines = getQuoteLines(quote);
  const total = Number(quote.fields?.total || 0);
  const estimatedCost = calculateSalesEstimatedCost(lines);
  const estimatedMargin = total ? ((total - estimatedCost) / total) * 100 : 0;
  const code = data.code.trim().toUpperCase();
  const record = {
    id: `${module.id}-order-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId: submodule.id,
    recordType: "salesOrder",
    title: `${quote.fields?.customerName || quote.owner} - ${lines.length} ${t("quoteLines")}`,
    detail: `${quote.code} - ${formatCurrency(total)} - ${formatNumber(estimatedMargin)}%`,
    status: data.status || "Aprobado",
    owner: data.owner?.trim() || quote.owner,
    fields: {
      quoteId: quote.id,
      quoteCode: quote.code,
      customerId: quote.fields?.customerId || "",
      customerName: quote.fields?.customerName || quote.owner,
      lines,
      subtotal: Number(quote.fields?.subtotal || total),
      total,
      estimatedCost,
      estimatedMargin,
      deliveryPromise: data.deliveryPromise || quote.fields?.deliveryPromise || "",
      fulfillmentMode: data.fulfillmentMode || t("pendingInventoryReview"),
      notes: data.notes?.trim() || ""
    },
    createdAt: new Date().toISOString()
  };

  mockDb.addModuleRecord(module.id, record);
  closeModal();
  navigateTo({ active: "ventas", activeSubmodule: "pedidos", laborArea: "" });
  showToast(t("salesOrderSaved", { code }));
}

function openSalesOrderEditModal(module, submodule, orderId) {
  if (getApiMode() === "api") { openSalesOrderFulfillmentModal(module, orderId); return; }
  const label = state.lang === "en" ? module.titleEn : module.title;
  const order = mockDb.findModuleRecord(module.id, orderId);
  if (!order || order.recordType !== "salesOrder") return;
  const fields = order.fields || {};

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesOrderEditForm">
      <input type="hidden" name="orderId" value="${escapeAttribute(order.id)}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${t("editSalesOrder")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("salesOrderCode")}</span>
          <input name="code" type="text" value="${escapeAttribute(order.code || "")}" required />
        </label>
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            ${getSalesOrderStatusOptions().map((status) => `<option value="${status}" ${selectedOption(order.status, status)}>${translateStatus(status)}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("deliveryPromise")}</span>
          <input name="deliveryPromise" type="date" value="${escapeAttribute(fields.deliveryPromise || "")}" />
        </label>
        <label class="preview-field">
          <span>${t("fulfillmentMode")}</span>
          <select name="fulfillmentMode">
            ${getFulfillmentModeOptions().map((mode) => `<option value="${mode}" ${selectedOption(fields.fulfillmentMode, mode)}>${mode}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("owner")}</span>
          <input name="owner" type="text" value="${escapeAttribute(order.owner || "")}" />
        </label>
        <label class="preview-field wide-field">
          <span>${t("notes")}</span>
          <textarea name="notes" rows="3" placeholder="${escapeAttribute(t("salesOrderNotesPlaceholder"))}">${escapeHtml(fields.notes || "")}</textarea>
        </label>
        <label class="preview-field wide-field">
          <span>${t("adjustmentReason")}</span>
          <textarea name="adjustmentReason" rows="3" placeholder="${escapeAttribute(t("adjustmentReasonPlaceholder"))}" required></textarea>
        </label>
      </div>

      <section class="section-card wide-field">
        <div class="section-title">
          <span class="section-icon">☷</span>
          <strong>${t("adjustmentHistory")}</strong>
        </div>
        <div class="records module-records">
          ${renderSalesOrderAdjustmentHistory(fields.adjustments || [])}
        </div>
      </section>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-sales-order-edit">${t("cancel")}</button>
        <button class="primary-action" type="submit">${t("updateSalesOrder")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-sales-order-edit']").addEventListener("click", closeModal);
  modalContent.querySelector("#salesOrderEditForm").addEventListener("submit", (event) => saveSalesOrderEditForm(event, module, submodule));
}

function getSalesOrderStatusOptions() {
  return [
    "Aprobado",
    "En preparacion",
    "En ruta",
    "Parcialmente entregado",
    "Entregado",
    "No entregado",
    "Reprogramado",
    "Cancelado"
  ];
}

function getFulfillmentModeOptions() {
  return [
    t("pendingInventoryReview"),
    t("stockFulfillment"),
    t("productionFulfillment")
  ];
}

function renderSalesOrderAdjustmentHistory(adjustments = []) {
  if (!adjustments.length) {
    return `
      <article class="record-row">
        <div class="record-main">
          <strong>${t("noOrderAdjustments")}</strong>
          <span>${t("adjustmentHistoryEmpty")}</span>
        </div>
      </article>
    `;
  }
  return adjustments
    .map((adjustment) => `
      <article class="record-row">
        <div class="record-main">
          <strong>${formatKardexDate(adjustment.changedAt)} - ${adjustment.reason}</strong>
          <span>${adjustment.changes.length ? adjustment.changes.map((change) => `${change.label}: ${change.from || t("notDefined")} -> ${change.to || t("notDefined")}`).join(" / ") : t("adjustmentNoteOnly")}</span>
        </div>
        <span class="chip">${adjustment.changedBy}</span>
      </article>
    `)
    .join("");
}

function saveSalesOrderEditForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];
  const order = mockDb.findModuleRecord(module.id, data.orderId);
  if (!order || order.recordType !== "salesOrder") errors.push(t("salesOrderRequired"));
  if (!data.code?.trim()) errors.push(t("salesOrderCodeRequired"));
  if (!data.adjustmentReason?.trim()) errors.push(t("adjustmentReasonRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const nextOrder = buildEditedSalesOrder(order, data);
  mockDb.updateModuleRecord(module.id, nextOrder);
  closeModal();
  render();
  showToast(t("salesOrderUpdated", { code: nextOrder.code }));
}

function buildEditedSalesOrder(order, data) {
  const nextFields = {
    ...order.fields,
    deliveryPromise: data.deliveryPromise || "",
    fulfillmentMode: data.fulfillmentMode || "",
    notes: data.notes?.trim() || ""
  };
  const changes = collectSalesOrderChanges(order, data);
  const adjustment = {
    id: `ADJ-${Date.now().toString().slice(-5)}`,
    changedAt: new Date().toISOString(),
    changedBy: "Usuario actual",
    reason: data.adjustmentReason.trim(),
    changes
  };
  const adjustments = [adjustment, ...(order.fields?.adjustments || [])];

  return {
    ...order,
    code: data.code.trim().toUpperCase(),
    status: data.status || order.status,
    owner: data.owner?.trim() || order.owner,
    detail: `${order.fields?.quoteCode || order.code} - ${formatCurrency(Number(order.fields?.total || 0))} - ${formatNumber(Number(order.fields?.estimatedMargin || 0))}%`,
    fields: {
      ...nextFields,
      adjustments
    },
    updatedAt: new Date().toISOString()
  };
}

function collectSalesOrderChanges(order, data) {
  const checks = [
    { key: "code", label: t("salesOrderCode"), from: order.code || "", to: data.code.trim().toUpperCase() },
    { key: "status", label: t("status"), from: order.status || "", to: data.status || "" },
    { key: "deliveryPromise", label: t("deliveryPromise"), from: order.fields?.deliveryPromise || "", to: data.deliveryPromise || "" },
    { key: "fulfillmentMode", label: t("fulfillmentMode"), from: order.fields?.fulfillmentMode || "", to: data.fulfillmentMode || "" },
    { key: "owner", label: t("owner"), from: order.owner || "", to: data.owner?.trim() || "" },
    { key: "notes", label: t("notes"), from: order.fields?.notes || "", to: data.notes?.trim() || "" }
  ];
  return checks
    .filter((item) => String(item.from || "") !== String(item.to || ""))
    .map(({ label, from, to }) => ({ label, from, to }));
}

function calculateSalesEstimatedCost(lines = []) {
  return lines.reduce((sum, line) => {
    const product = mockDb.findProductService(line.productServiceId);
    const standardCost = Number(product?.standardCost || 0);
    return sum + (standardCost * Number(line.quantity || 0));
  }, 0);
}

function normalizeDocumentSearch(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function getSalesDocumentMatches(records, query) {
  const terms=normalizeDocumentSearch(query).split(/\s+/).filter(Boolean);
  return records.filter(record=>{
    const products=(record.fields?.lines||[]).map(line=>line.productServiceName).join(" ");
    const haystack=normalizeDocumentSearch([record.code,record.title,record.status,record.owner,record.fields?.customerName,record.fields?.quoteCode,products,record.fields?.total].join(" "));
    return terms.every(term=>haystack.includes(term));
  }).slice(0,20);
}

function renderSalesDocumentLookup(results, records, query, kind) {
  const matches=getSalesDocumentMatches(records,query);
  results.hidden=false;
  results.innerHTML=matches.length?matches.map(record=>{
    const products=[...new Set((record.fields?.lines||[]).map(line=>line.productServiceName).filter(Boolean))].slice(0,2).join(" · ");
    const customer=record.fields?.customerName||record.owner||record.title;
    const detail=kind==="quote"?`${customer} · ${formatCurrency(Number(record.fields?.total||0))}`:`${customer} · ${translateStatus(record.status)}`;
    return `<button class="lookup-option" type="button" data-document-id="${escapeAttribute(record.id)}"><strong>${escapeHtml(record.code)} · ${escapeHtml(customer)}</strong><span>${escapeHtml(detail)}${products?` · ${escapeHtml(products)}`:""}</span></button>`;
  }).join(""):`<div class="lookup-empty">${t("documentLookupEmpty")}</div>`;
}

function openSalesDeliveryModal(module, submodule, orderId = null) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const deliveries = mockDb.loadModuleRecords(module.id, "entregas").filter((record) => record.recordType === "salesDelivery" && record.status !== "Cancelada");
  const committedByLine = new Map();
  deliveries.forEach((delivery) => (delivery.fields?.lines || []).forEach((line) => {
    committedByLine.set(line.orderLineId, (committedByLine.get(line.orderLineId) || 0) + Number(line.quantity || 0));
  }));
  const orders = mockDb.loadModuleRecords(module.id, "pedidos").filter((record) =>
    record.recordType === "salesOrder"
      && !["Cancelado", "Entregado"].includes(record.status)
      && record.fields?.cancellationState !== "processing"
      && (record.fields?.lines||[]).some(line=>Number(line.quantity)>Number(line.deliveredQuantity||0)+Number(committedByLine.get(line.id)||0)&&["ready","reserved","partially_delivered"].includes(line.fulfillmentStatus))
  );
  const selectedOrder = orderId
    ? orders.find((order) => order.id === orderId)
    : orders[0];
  const deliverableLines = (selectedOrder?.fields?.lines || []).filter(
    (line) => Number(line.quantity) > Number(line.deliveredQuantity || 0) + Number(committedByLine.get(line.id) || 0)
      && ["ready", "reserved", "partially_delivered"].includes(line.fulfillmentStatus)
  );

  if (!orders.length || !selectedOrder) {
    showToast(t("deliveryRequiresSalesOrder"));
    return;
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesDeliveryForm">
      <input type="hidden" name="orderId" value="${escapeAttribute(selectedOrder.id)}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("sales.delivery"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${t("newDelivery")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("deliveryCode")}</span>
          <input name="code" type="text" maxlength="60" placeholder="${codeSequenceConfig("sales.delivery")?.mode === "managed" ? t("codeAssignedAutomatically") : "ENT-001"}" ${codeSequenceConfig("sales.delivery")?.mode === "managed" ? "readonly" : ""} />
        </label>
        <label class="preview-field wide-field product-lookup-field">
          <span>${t("salesOrder")}</span>
          <input name="orderSearch" type="search" value="${escapeAttribute(`${selectedOrder.code} - ${selectedOrder.fields?.customerName||selectedOrder.owner}`)}" placeholder="${escapeAttribute(t("orderLookupPlaceholder"))}" autocomplete="off" required />
          <div class="lookup-results" id="deliveryOrderResults" hidden></div>
          <small>${t("orderLookupHelp")}</small>
        </label>
        ${getApiMode() !== "api" ? `<label class="preview-field">
          <span>${t("deliveryStatus")}</span>
          <select name="deliveryStatus">
            ${getDeliveryStatusOptions().map((status) => `<option value="${status}">${translateStatus(status)}</option>`).join("")}
          </select>
        </label>` : ""}
        <label class="preview-field">
          <span>${t("deliveryDate")}</span>
          <input name="deliveryDate" type="date" value="${new Date().toISOString().slice(0, 10)}" required />
        </label>
        <label class="preview-field">
          <span>${t("recipient")}</span>
          <input name="recipient" type="text" value="${escapeAttribute(selectedOrder.fields?.customerName || selectedOrder.owner || "")}" placeholder="${escapeAttribute(t("recipientPlaceholder"))}" />
        </label>
        <label class="preview-field">
          <span>${t("deliveryReference")}</span>
          <input name="deliveryReference" type="text" placeholder="REM-001 / guia / evidencia" />
        </label>
        ${getApiMode() !== "api" ? `<label class="preview-field">
          <span>${t("nextDeliveryDate")}</span>
          <input name="nextDeliveryDate" type="date" />
        </label>` : ""}
        <label class="preview-field wide-field">
          <span>${t("deliveryNotes")}</span>
          <textarea name="notes" rows="3" placeholder="${escapeAttribute(t("deliveryNotesPlaceholder"))}"></textarea>
        </label>
        ${getApiMode() === "api" ? `<div class="wide-field records"><strong>Partidas a entregar</strong>${deliverableLines.map((line) => {
          const remaining = Number(line.quantity) - Number(line.deliveredQuantity || 0) - Number(committedByLine.get(line.id) || 0);
          return `<article class="record-row"><div class="record-main"><strong>${escapeHtml(line.productServiceName)}</strong><span>${formatNumber(remaining)} ${escapeHtml(line.unit)} sin comprometer</span></div><label class="preview-field"><span>Cantidad de esta entrega</span><input name="deliveryQuantity-${escapeAttribute(line.id)}" type="number" min="0" max="${remaining}" step="any" value="${remaining}" required /></label>${line.productServiceType === "service" ? `<label class="preview-field"><span>Costo unitario real</span><input name="deliveryActualCost-${escapeAttribute(line.id)}" type="number" min="0" step="0.000001" required /></label>` : ""}</article>`;
        }).join("")}</div>` : ""}
      </div>

      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-sales-delivery">${t("cancel")}</button>
        <button class="primary-action" type="submit">${t("saveDelivery")}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-sales-delivery']").addEventListener("click", closeModal);
  const orderSearch=modalContent.querySelector("[name='orderSearch']");
  const orderResults=modalContent.querySelector("#deliveryOrderResults");
  const showOrders=()=>renderSalesDocumentLookup(orderResults,orders,orderSearch.value,"order");
  orderSearch.addEventListener("focus",showOrders);
  orderSearch.addEventListener("input",()=>{modalContent.querySelector("[name='orderId']").value="";showOrders();});
  orderResults.addEventListener("click",event=>{
    const button=event.target.closest("[data-document-id]");
    if(!button)return;
    const order = orders.find((item) => item.id === button.dataset.documentId);
    if (!order) return;
    if (getApiMode() === "api") {
      openSalesDeliveryModal(module, submodule, order.id);
      return;
    }
    modalContent.querySelector("[name='orderId']").value = order.id;
    orderSearch.value=`${order.code} - ${order.fields?.customerName||order.owner}`;
    orderResults.hidden=true;
    modalContent.querySelector("[name='recipient']").value = order.fields?.customerName || order.owner || "";
  });
  modalContent.querySelector("#salesDeliveryForm").addEventListener("submit", (event) => saveSalesDeliveryForm(event, module, submodule));
}

function getDeliveryStatusOptions() {
  return [
    "Pendiente de entrega",
    "En ruta",
    "Entrega parcial",
    "Entregado",
    "No entregado",
    "Reprogramado",
    "Cancelado"
  ];
}

async function saveSalesDeliveryForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];
  const order = mockDb.findModuleRecord(module.id, data.orderId);

  if (!order || order.recordType !== "salesOrder") errors.push(t("deliveryRequiresSalesOrder"));
  if (!data.deliveryDate) errors.push(t("deliveryDateRequired"));
  if (getApiMode() !== "api" && !getDeliveryStatusOptions().includes(data.deliveryStatus)) errors.push(t("deliveryStatusRequired"));
  if (getApiMode() !== "api" && data.deliveryStatus === "Entrega parcial" && !data.notes?.trim()) errors.push(t("partialDeliveryNotesRequired"));
  if (getApiMode() !== "api" && data.deliveryStatus === "No entregado" && !data.notes?.trim()) errors.push(t("failedDeliveryNotesRequired"));
  if (getApiMode() !== "api" && data.deliveryStatus === "Reprogramado" && !data.nextDeliveryDate) errors.push(t("nextDeliveryDateRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  if (getApiMode() === "api") {
    const lines=(order.fields?.lines||[]).filter(line=>line.quantity>line.deliveredQuantity&&["ready","reserved","partially_delivered"].includes(line.fulfillmentStatus)).map(line=>({order_line_id:line.id,quantity:Number(data[`deliveryQuantity-${line.id}`]||0),actual_unit_cost:line.productServiceType==="service"?Number(data[`deliveryActualCost-${line.id}`]):null})).filter(line=>line.quantity>0);
    if(!lines.length){renderFormErrors(["El pedido no tiene partidas listas o reservadas para entregar."]);return;}
    const invalidLine=lines.find(line=>{const source=(order.fields?.lines||[]).find(item=>item.id===line.order_line_id);return !Number.isFinite(line.quantity)||line.quantity<=0||line.quantity>(Number(source?.quantity||0)-Number(source?.deliveredQuantity||0))||(source?.productServiceType==="service"&&(!Number.isFinite(line.actual_unit_cost)||line.actual_unit_cost<0));});
    if(invalidLine){renderFormErrors(["La cantidad a entregar debe ser mayor a cero y no exceder el pendiente de la partida."]);return;}
    try{const businessCode=await resolveBusinessCode("sales.delivery",data.code,data.codeRequestKey);await createSalesDelivery({code:businessCode,order_id:order.id,scheduled_date:data.deliveryDate,recipient_name:data.recipient?.trim()||null,evidence_reference:data.deliveryReference?.trim()||null,notes:data.notes?.trim()||null,lines});closeModal();await loadSalesApiData();navigateTo({active:"ventas",activeSubmodule:"entregas",laborArea:""});showToast("Entrega registrada como borrador. Confírmala para consumir las reservas.");}catch(error){renderFormErrors([error.message||"No se pudo registrar la entrega."]);}return;
  }

  const code = `ENT-${String(Date.now()).slice(-5)}`;
  const deliveryStatus = data.deliveryStatus || "Pendiente de entrega";
  const deliveryRecord = {
    id: `${module.id}-delivery-${Date.now()}`,
    code,
    moduleId: module.id,
    submoduleId: submodule.id,
    recordType: "salesDelivery",
    title: `${order.code} - ${order.fields?.customerName || order.owner}`,
    detail: `${translateStatus(deliveryStatus)} - ${data.deliveryDate}`,
    status: deliveryStatus,
    owner: data.recipient?.trim() || order.owner,
    fields: {
      orderId: order.id,
      orderCode: order.code,
      quoteCode: order.fields?.quoteCode || "",
      customerName: order.fields?.customerName || order.owner,
      deliveryStatus,
      deliveryDate: data.deliveryDate,
      nextDeliveryDate: data.nextDeliveryDate || "",
      recipient: data.recipient?.trim() || "",
      deliveryReference: data.deliveryReference?.trim() || "",
      notes: data.notes?.trim() || ""
    },
    createdAt: new Date().toISOString()
  };

  mockDb.addModuleRecord(module.id, deliveryRecord);
  mockDb.updateModuleRecord(module.id, {
    ...order,
    status: getSalesOrderStatusFromDelivery(deliveryStatus, order.status),
    fields: {
      ...order.fields,
      deliveryStatus,
      lastDeliveryId: deliveryRecord.id,
      lastDeliveryDate: data.deliveryDate,
      nextDeliveryDate: data.nextDeliveryDate || ""
    },
    updatedAt: new Date().toISOString()
  });
  closeModal();
  navigateTo({ active: "ventas", activeSubmodule: "entregas", laborArea: "" });
  showToast(t("deliverySaved", { code }));
}

function getSalesOrderStatusFromDelivery(deliveryStatus, currentStatus) {
  const statusMap = {
    "Pendiente de entrega": "Aprobado",
    "En ruta": "En ruta",
    "Entrega parcial": "Parcialmente entregado",
    Entregado: "Entregado",
    "No entregado": "No entregado",
    Reprogramado: "Reprogramado",
    Cancelado: "Cancelado"
  };
  return statusMap[deliveryStatus] || currentStatus;
}

function openProductServiceModal(productServiceId = null) {
  if (getApiMode() === "api" && isInventoryApiEnabled() && state.inventoryItems.status === "idle") {
    loadInventoryApiData().then(loadInventoryItemData).then(() => openProductServiceModal(productServiceId));
    return;
  }
  const existingItem = productServiceId ? mockDb.findProductService(productServiceId) : null;
  const isEditing = Boolean(existingItem);
  const inventoryItems = mockDb.loadModuleRecords("almacenes", "articulos").filter((item) => item.recordType === "inventoryItem" && item.status !== "Inactivo");
  const renderInventoryMappingOptions = (unit, selectedId = "") => {
    const matching = inventoryItems.filter((item) => normalizeUnitCode(item.fields?.unit || "") === normalizeUnitCode(unit || ""));
    return `<option value="">${matching.length ? "Seleccionar artículo autoritativo" : "No hay artículos activos con esta unidad"}</option>${matching.map((item) => `<option value="${escapeAttribute(item.id)}" ${selectedOption(selectedId, item.id)}>${escapeHtml(item.code)} - ${escapeHtml(item.title)} (${escapeHtml(item.fields?.unit || "")})</option>`).join("")}`;
  };
  modalContent.innerHTML = `
    <form class="recipe-form" id="productServiceForm">
      <input type="hidden" name="productServiceId" value="${escapeAttribute(existingItem?.id || "")}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("production.product_service"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">${isEditing ? "Editar producto o servicio" : "Nuevo producto o servicio"}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>Tipo</span>
          <select name="kind" required>
            <option ${existingItem?.kind === "Producto" ? "selected" : ""}>Producto</option>
            <option ${existingItem?.kind === "Servicio" ? "selected" : ""}>Servicio</option>
          </select>
        </label>
        <label class="preview-field">
          <span>Nombre</span>
          <input name="name" type="text" value="${escapeAttribute(existingItem?.name || "")}" placeholder="Ej. Producto o servicio premium" required />
        </label>
        <label class="preview-field">
          <span>SKU / codigo interno</span>
          <input name="sku" type="text" value="${escapeAttribute(existingItem?.sku || "")}" placeholder="${codeSequenceConfig("production.product_service")?.mode === "managed" ? t("codeAssignedAutomatically") : "Ej. PROD-INT-001"}" ${isEditing || codeSequenceConfig("production.product_service")?.mode === "managed" ? "readonly" : ""} />
        </label>
        <label class="preview-field">
          <span>Unidad base</span>
          ${unitSelect("unit", existingItem?.unit || "H87")}
        </label>
        <label class="preview-field" data-product-inventory-field>
          <span>Artículo de inventario vinculado</span>
          <select name="inventoryItemId" data-entity-selector>
            ${renderInventoryMappingOptions(existingItem?.unit || "H87", existingItem?.inventoryItemId || "")}
          </select>
        </label>
        <label class="preview-field">
          <span>Categoria</span>
          <input name="category" type="text" value="${escapeAttribute(existingItem?.category || "Produccion")}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Centro de costos</span>
          <input name="center" type="text" value="${escapeAttribute(existingItem?.center || "Produccion / General")}" required />
        </label>
        <label class="preview-field">
          <span>Responsable</span>
          <input name="owner" type="text" value="${escapeAttribute(existingItem?.owner || "Operacion")}" required />
        </label>
        <label class="preview-field">
          <span>Precio objetivo</span>
          <input name="targetPrice" type="number" min="0" step="0.01" value="${escapeAttribute(existingItem?.targetPrice || 0)}" required />
        </label>
        <label class="preview-field">
          <span>Margen esperado %</span>
          <input name="expectedMargin" type="number" min="0" max="100" step="0.01" value="${escapeAttribute(existingItem?.expectedMargin || 0)}" required />
        </label>
        <label class="preview-field">
          <span>Estatus</span>
          <select name="status">
            ${["Activo", "Inactivo", "En espera de aprobacion"].map((status) => `
              <option value="${status}" ${existingItem?.status === status ? "selected" : ""}>${status}</option>
            `).join("")}
          </select>
        </label>
        <label class="preview-field wide-field">
          <span>Descripcion</span>
          <input name="description" type="text" value="${escapeAttribute(existingItem?.description || "")}" placeholder="Uso operativo del producto o servicio" required />
        </label>
      </div>

      <div class="form-errors" id="formErrors" hidden></div>

      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-product-service">Cancelar</button>
        <button class="primary-action" type="submit">${isEditing ? "Actualizar ficha" : "Guardar en catalogo"}</button>
      </div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-product-service']").addEventListener("click", closeModal);
  const kindSelect = modalContent.querySelector("[name='kind']");
  const baseUnitSelect = modalContent.querySelector("[name='unit']");
  const inventorySelect = modalContent.querySelector("[name='inventoryItemId']");
  const syncInventoryMappingOptions = () => {
    const selectedId = inventorySelect.value || existingItem?.inventoryItemId || "";
    inventorySelect.innerHTML = renderInventoryMappingOptions(baseUnitSelect.value, selectedId);
  };
  const syncMappingRequirement = () => {
    const isProduct = kindSelect.value === "Producto";
    inventorySelect.required = isProduct;
    inventorySelect.closest("label").hidden = !isProduct;
    if (!isProduct) inventorySelect.value = "";
  };
  kindSelect.addEventListener("change", syncMappingRequirement);
  baseUnitSelect.addEventListener("change", () => {
    syncInventoryMappingOptions();
    syncMappingRequirement();
  });
  syncInventoryMappingOptions();
  syncMappingRequirement();
  modalContent.querySelector("#productServiceForm").addEventListener("submit", saveProductServiceForm);
}

function buildProductServiceFromForm(form) {
  const data = new FormData(form);
  const productServiceId = String(data.get("productServiceId") || "").trim();
  const existingItem = productServiceId ? mockDb.findProductService(productServiceId) : null;
  const kind = String(data.get("kind") || "Producto");
  const prefix = kind === "Servicio" ? "SER" : "PROD";
  return {
    id: productServiceId || `${prefix}-${Date.now().toString().slice(-5)}`,
    name: String(data.get("name") || "").trim(),
    kind,
    sku: String(data.get("sku") || "").trim(),
    codeRequestKey: String(data.get("codeRequestKey") || ""),
    unit: String(data.get("unit") || "").trim(),
    category: String(data.get("category") || "").trim(),
    center: String(data.get("center") || "").trim(),
    owner: String(data.get("owner") || "").trim(),
    standardCost: Number(existingItem?.standardCost || 0),
    targetPrice: Number(data.get("targetPrice") || 0),
    expectedMargin: Number(data.get("expectedMargin") || 0),
    status: String(data.get("status") || existingItem?.status || "Activo"),
    description: String(data.get("description") || "").trim(),
    inventoryItemId: String(data.get("inventoryItemId") || "").trim(),
    createdAt: existingItem?.createdAt || new Date().toISOString().slice(0, 10),
    updatedAt: productServiceId ? new Date().toISOString().slice(0, 10) : ""
  };
}

function validateProductService(item) {
  const errors = [];
  if (!item.name) errors.push("Captura el nombre.");
  if (!item.sku && getApiMode() !== "api") errors.push("Captura el SKU o codigo interno.");
  if (!item.unit) errors.push("Captura la unidad base.");
  if (!item.category) errors.push("Captura la categoria.");
  if (!item.center) errors.push("Captura el centro de costos.");
  if (!item.owner) errors.push("Captura el responsable.");
  if (!item.description) errors.push("Captura la descripcion.");
  if (item.kind === "Producto" && !item.inventoryItemId) errors.push("Vincula el producto con un artículo activo de Inventario.");
  return errors;
}

async function saveProductServiceForm(event) {
  event.preventDefault();
  const item = buildProductServiceFromForm(event.currentTarget);
  const exists = Boolean(mockDb.findProductService(item.id));
  const errors = validateProductService(item);
  renderFormErrors(errors);
  if (errors.length) return;

  if (getApiMode() === "api") {
    try {
      const payload = {
        name: item.name,
        category: item.category,
        base_unit: item.unit,
        target_price: item.targetPrice,
        responsible_area: item.owner,
        cost_center: item.center,
        expected_margin: item.expectedMargin,
        description: item.description,
        inventory_item_id: item.kind === "Producto" ? item.inventoryItemId : null
      };
      const saved = exists
        ? await updateProductionProductService(item.id, payload)
        : await createProductionProductService({ ...payload, code: await resolveBusinessCode("production.product_service",item.sku,item.codeRequestKey), type: item.kind === "Servicio" ? "service" : "product" });
      const statuses = { Activo: "active", Inactivo: "inactive", "En espera de aprobacion": "pending_approval" };
      if (statuses[item.status] && saved.status !== statuses[item.status]) {
        await updateProductionProductServiceStatus(saved.id, { status: statuses[item.status], reason: "Estatus inicial del catalogo" });
      }
      localStorage.setItem("erclave-product-service-search", "");
      closeModal();
      await loadProductionApiData();
      navigateTo({ active: "produccion", activeSubmodule: "productos-servicios", laborArea: "" });
      showToast(`${item.kind} ${saved.code} ${exists ? "actualizado" : "guardado"} en Production API.`);
    } catch (error) {
      renderFormErrors([error.message || "No se pudo guardar en Production API."]);
    }
    return;
  }

  if (exists) {
    mockDb.updateProductService(item);
  } else {
    mockDb.addProductService(item);
  }
  syncRecipesForProductService(item);
  localStorage.setItem("erclave-product-service-search", "");
  closeModal();
  navigateTo({ active: "produccion", activeSubmodule: "productos-servicios", laborArea: "" });
  showToast(`${item.kind} ${item.id} ${exists ? "actualizado" : "guardado"} en el catalogo.`);
}

function syncRecipesForProductService(item) {
  mockDb.loadRecipes()
    .filter((recipe) => recipe.productServiceId === item.id)
    .forEach((recipe) => {
      mockDb.updateRecipe({
        ...recipe,
        product: item.name,
        unit: item.unit,
        center: item.center
      });
    });
}

function openLaborAreaModal(areaId = null) {
  const existingArea = areaId ? mockDb.findLaborArea(areaId) : null;
  const isEditing = Boolean(existingArea);
  const requiredPermission = isEditing ? "hr.area.update" : "hr.area.create";
  if (!hasPermission(requiredPermission)) {
    showToast("No tienes permiso para realizar esta operacion sobre areas.");
    return;
  }
  modalContent.innerHTML = `
    <form class="recipe-form" id="laborAreaForm">
      <input type="hidden" name="areaId" value="${existingArea?.id || ""}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("hr.area"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${t("humanResources")} - ${t("laborAreaCatalog")}</p>
          <h2 id="modalTitle">${isEditing ? t("editLaborArea") : t("newLaborArea")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">x</button>
      </div>
      <p class="helper-copy">${t("laborAreaFormHelp")}</p>
      <div class="form-grid">
        <label class="preview-field"><span>${t("laborAreaCode")}</span><input name="code" type="text" value="${escapeAttribute(existingArea?.code || "")}" placeholder="${codeSequenceConfig("hr.area")?.mode === "managed" ? t("codeAssignedAutomatically") : "Ej. PROCESO"}" ${isEditing || codeSequenceConfig("hr.area")?.mode === "managed" ? "readonly" : ""} /></label>
        <label class="preview-field"><span>${t("laborAreaName")}</span><input name="name" type="text" value="${escapeAttribute(existingArea?.name || "")}" placeholder="Ej. Proceso" required /></label>
        <label class="preview-field wide-field"><span>${t("laborAreaDescription")}</span><textarea name="description" rows="3" placeholder="Objetivo y alcance operativo del area">${escapeHtml(existingArea?.description || "")}</textarea></label>
        <label class="preview-field"><span>${t("laborAreaStatus")}</span><select name="status"><option ${existingArea?.status === "Activo" ? "selected" : ""}>Activo</option><option ${existingArea?.status === "Inactivo" ? "selected" : ""}>Inactivo</option></select></label>
      </div>
      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-labor-area">${t("cancel")}</button>
        <button class="primary-action" type="submit">${isEditing ? t("updateLaborArea") : t("saveLaborArea")}</button>
      </div>
    </form>`;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-labor-area']").addEventListener("click", closeModal);
  modalContent.querySelector("#laborAreaForm").addEventListener("submit", saveLaborAreaForm);
}

function openSalesOrderFulfillmentModal(module, orderId) {
  if(getApiMode()==="api"&&(state.inventoryApi.status==="idle"||state.inventoryItems.status==="idle")){loadInventoryApiData().then(()=>loadInventoryItemData()).then(()=>openSalesOrderFulfillmentModal(module,orderId));return;}
  const order=mockDb.findModuleRecord(module.id,orderId); if(!order)return;
  const lines=(order.fields?.lines||[]).filter(line=>line.fulfillmentMode==="pending"&&line.fulfillmentStatus==="pending");
  if(!lines.length){showToast("Todas las partidas ya tienen un modo de surtido autoritativo.");return;}
  const inventoryItems=mockDb.loadModuleRecords("almacenes","articulos").filter(record=>record.recordType==="inventoryItem"&&record.status!=="Inactivo");
  const warehouses=mockDb.loadModuleRecords("almacenes","almacenes").filter(record=>record.recordType==="warehouse"&&record.status!=="Inactivo");
  modalContent.innerHTML=`<form class="recipe-form" id="salesOrderFulfillmentForm"><input type="hidden" name="orderId" value="${escapeAttribute(order.id)}"><div class="modal-head"><div><p class="eyebrow">${t("salesOrder")}</p><h2>${escapeHtml(order.code)} · Surtido</h2></div><button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button></div><p class="helper-copy">Cada producto usa exclusivamente el artículo de Inventario vinculado en su ficha. Una partida configurada ya no puede reasignarse.</p><div class="records">${lines.map(line=>{const product=mockDb.findProductService(line.productServiceId);const mappedId=product?.inventoryItemId||"";const mappedItem=inventoryItems.find(item=>item.id===mappedId);return `<article class="record-row fulfillment-line" data-line-id="${escapeAttribute(line.id)}"><div class="record-main"><strong>${escapeHtml(line.productServiceName)}</strong><span>${formatNumber(line.quantity-line.deliveredQuantity)} ${escapeHtml(line.unit)} pendientes</span></div><label class="preview-field"><span>Modo</span><select name="mode-${escapeAttribute(line.id)}">${line.productServiceType==="service"?`<option value="service">Servicio</option>`:`<option value="stock">Existencia</option><option value="production">Producción</option>`}</select></label>${line.productServiceType==="product"?`<label class="preview-field"><span>Artículo vinculado</span><select name="item-${escapeAttribute(line.id)}" required><option value="${escapeAttribute(mappedId)}">${mappedItem?`${escapeHtml(mappedItem.code)} - ${escapeHtml(mappedItem.title)}`:"Producto sin mapeo vigente"}</option></select></label><label class="preview-field"><span>Almacén</span><select name="warehouse-${escapeAttribute(line.id)}"><option value="">Seleccionar</option>${warehouses.map(item=>`<option value="${escapeAttribute(item.id)}">${escapeHtml(item.code)} - ${escapeHtml(item.title)}</option>`).join("")}</select></label>`:""}</article>`;}).join("")}</div><label class="preview-field wide-field"><span>Motivo de cancelación</span><textarea name="cancelReason" rows="2" placeholder="Solo se usa al cancelar"></textarea></label><div class="form-errors" id="formErrors" hidden></div><div class="modal-actions">${hasPermission("sales.order.cancel")?`<button class="secondary-action" type="button" data-action="cancel-api-order">Cancelar pedido</button>`:""}<button class="secondary-action" type="button" data-action="close-api-order">${t("cancel")}</button>${hasPermission("sales.order.fulfill")?`<button class="primary-action" type="submit">Configurar surtido</button>`:""}</div></form>`;
  modalContent.querySelectorAll('select[name^="warehouse-"]').forEach(select=>{select.dataset.entitySelector="";select.dataset.searchPlaceholder="Buscar almacén por código o nombre";enhanceEntitySelect(select);});
  modalBackdrop.hidden=false; modalContent.querySelector(".modal-close").addEventListener("click",closeModal); modalContent.querySelector("[data-action='close-api-order']").addEventListener("click",closeModal);
  modalContent.querySelector("#salesOrderFulfillmentForm").addEventListener("submit",async event=>{event.preventDefault();const form=new FormData(event.currentTarget);const payload={lines:lines.map(line=>{const mode=form.get(`mode-${line.id}`);const remaining=line.quantity-line.deliveredQuantity;return {order_line_id:line.id,mode,allocations:mode==="stock"?[{inventory_item_id:form.get(`item-${line.id}`),warehouse_id:form.get(`warehouse-${line.id}`),quantity:remaining}]:[]};})};if(payload.lines.some(line=>line.mode==="stock"&&(!line.allocations[0].inventory_item_id||!line.allocations[0].warehouse_id))){renderFormErrors(["Selecciona artículo y almacén para cada partida surtida desde existencia."]);return;}try{await configureSalesOrderFulfillment(order.id,payload);closeModal();await loadSalesApiData();showToast("Surtido configurado.");}catch(error){renderFormErrors([error.message||"No se pudo configurar el surtido."]);}});
  modalContent.querySelector("[data-action='cancel-api-order']")?.addEventListener("click",async()=>{const reason=modalContent.querySelector("[name='cancelReason']").value.trim();if(reason.length<3){renderFormErrors(["Captura el motivo de cancelación."]);return;}try{await cancelSalesOrder(order.id,reason);closeModal();await loadSalesApiData();showToast("Pedido cancelado.");}catch(error){renderFormErrors([error.message||"No se pudo cancelar el pedido."]);}});
}

function openAdminUnitModal(unitId) {
  const unit = (getAdminPanelData()?.units || []).find((item) => item.id === unitId);
  if (!unit) return;
  const categories = [["count","uomCategoryCount"],["mass","uomCategoryMass"],["length","uomCategoryLength"],["area","uomCategoryArea"],["volume","uomCategoryVolume"],["time","uomCategoryTime"],["package","uomCategoryPackage"],["energy","uomCategoryEnergy"],["power","uomCategoryPower"],["electric","uomCategoryElectric"],["temperature","uomCategoryTemperature"],["pressure","uomCategoryPressure"],["ratio","uomCategoryRatio"],["other","uomCategoryOther"]];
  modalContent.innerHTML = `<form class="recipe-form" id="adminUnitForm">
    <div class="modal-head"><div><p class="eyebrow">${t("baseCatalog")}</p><h2 id="modalTitle">${t("editUnit")}</h2></div><button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button></div>
    <div class="form-grid">
      <label class="preview-field"><span>${t("stableCode")}</span><input value="${escapeAttribute(unit.code)}" disabled /></label>
      <label class="preview-field"><span>${t("unitNameEs")}</span><input name="name_es" maxlength="120" value="${escapeAttribute(unit.name_es)}" required /></label>
      <label class="preview-field"><span>${t("unitNameEn")}</span><input name="name_en" maxlength="120" value="${escapeAttribute(unit.name_en)}" required /></label>
      <label class="preview-field"><span>${t("unitSymbol")}</span><input name="symbol" maxlength="24" value="${escapeAttribute(unit.symbol)}" required /></label>
      <label class="preview-field"><span>${t("unitCategory")}</span><select name="category">${categories.map(([value,key])=>`<option value="${value}" ${selectedOption(unit.category,value)}>${t(key)}</option>`).join("")}</select></label>
      <label class="preview-field"><span>${t("unitDecimals")}</span><input name="decimal_places" type="number" min="0" max="6" value="${unit.decimal_places}" required /></label>
    </div>
    <div class="modal-actions"><button class="secondary-action" type="button" data-action="close-admin-unit">${t("cancel")}</button><button class="primary-action" type="submit">${t("saveChanges")}</button></div>
  </form>`;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-admin-unit']").addEventListener("click", closeModal);
  modalContent.querySelector("#adminUnitForm").addEventListener("submit", async(event)=>{
    event.preventDefault();
    const values=Object.fromEntries(new FormData(event.currentTarget));
    try { await updateUnitOfMeasure(unit.id,{...values,decimal_places:Number(values.decimal_places)}); closeModal(); showToast(t("unitUpdated")); await loadAdminApiDashboard(); }
    catch(error){ showToast(error.message || t("unitUpdateError")); }
  });
}

async function saveLaborAreaForm(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const areaId = String(data.get("areaId") || "").trim();
  const requiredPermission = areaId ? "hr.area.update" : "hr.area.create";
  if (!hasPermission(requiredPermission)) {
    renderFormErrors(["No tienes permiso para guardar esta area."]);
    return;
  }
  let code = String(data.get("code") || "").trim().toUpperCase();
  const name = String(data.get("name") || "").trim();
  const normalizedCode = code.toLowerCase();
  const normalizedName = name.toLowerCase();
  const duplicate = mockDb.loadLaborAreas().find((area) =>
    area.id !== areaId && (area.code.toLowerCase() === normalizedCode || area.name.toLowerCase() === normalizedName)
  );
  const errors = [];
  if (!code && getApiMode() !== "api") errors.push("Captura el codigo del area.");
  if (!name) errors.push("Captura el nombre del area.");
  if (duplicate) errors.push(t("laborAreaDuplicate"));
  renderFormErrors(errors);
  if (errors.length) return;

  const item = {
    id: areaId || `area_${slugify(code)}_${Date.now().toString().slice(-4)}`,
    code,
    name,
    description: String(data.get("description") || "").trim(),
    status: String(data.get("status") || "Activo")
  };
  if (getApiMode() === "api") {
    try {
      const payload={name:item.name,description:item.description||null,status:item.status==="Activo"?"active":"inactive"};
      if (areaId) await updateHrArea(areaId,payload);
      else {code=await resolveBusinessCode("hr.area",code,String(data.get("codeRequestKey")||""));item.code=code;await createHrArea({code:item.code,name:item.name,description:item.description||null});}
      closeModal();await loadHrApiData();navigateTo({active:"recursos-humanos",activeSubmodule:"areas-puestos",laborArea:areaId||""});showToast(`Area ${item.name} ${areaId?"actualizada":"guardada"}.`);
    } catch(error) { renderFormErrors([error.message]); }
    return;
  }
  if (areaId) mockDb.updateLaborArea(item);
  else mockDb.addLaborArea(item);
  closeModal();
  navigateTo({ active: "recursos-humanos", activeSubmodule: "areas-puestos", laborArea: areaId ? item.id : "" });
  showToast(`Area ${item.name} ${areaId ? "actualizada" : "guardada"}.`);
}

function openLaborRoleModal(roleId = null, defaultAreaId = "") {
  const existingRole = roleId ? mockDb.findLaborRole(roleId) : null;
  const isEditing = Boolean(existingRole);
  const requiredPermission = isEditing ? "hr.position.update" : "hr.position.create";
  if (!hasPermission(requiredPermission)) {
    showToast("No tienes permiso para realizar esta operacion sobre puestos.");
    return;
  }
  const areas = mockDb.loadLaborAreas();
  const contextAreaId = defaultAreaId || localStorage.getItem("erclave-labor-selected-area") || "";
  const selectedAreaId = existingRole?.areaId || contextAreaId || areas.find((area) => area.status === "Activo")?.id || "";
  const selectableAreas = areas.filter((area) => area.status === "Activo" || area.id === selectedAreaId);
  if (!selectableAreas.length) {
    showToast(t("laborAreaRequiredFirst"));
    return;
  }
  modalContent.innerHTML = `
    <form class="recipe-form" id="laborRoleForm">
      <input type="hidden" name="roleId" value="${existingRole?.id || ""}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${t("humanResources")}</p>
          <h2 id="modalTitle">${isEditing ? t("editLaborRole") : t("newLaborRole")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">x</button>
      </div>
      <div class="form-grid">
        <label class="preview-field"><span>${t("laborAreaExisting")}</span><select name="areaId" data-entity-selector required>${selectableAreas.map((area) => `<option value="${area.id}" ${area.id === selectedAreaId ? "selected" : ""}>${area.code} - ${area.name}</option>`).join("")}</select></label>
        <label class="preview-field"><span>${t("laborRolePosition")}</span><input name="position" type="text" value="${existingRole?.position || ""}" placeholder="Ej. Operador" required /></label>
        <label class="preview-field"><span>${t("laborRoleName")}</span><input name="name" type="text" value="${existingRole?.name || ""}" placeholder="Ej. Operador de proceso" required /></label>
        <label class="preview-field"><span>${t("laborRoleQuantity")}</span><input name="quantity" type="number" min="1" value="${existingRole?.quantity || 1}" required /></label>
        <label class="preview-field"><span>${t("laborRoleMinutes")}</span><input name="minutesPerResource" type="number" min="1" value="${existingRole?.minutesPerResource || existingRole?.available || 480}" required /></label>
        <label class="preview-field"><span>${t("laborRoleHourlyCost")}</span><input name="hourlyCost" type="number" min="0" step="0.01" value="${existingRole?.hourlyCost ?? Number(existingRole?.cost || 0) * 60}" required /></label>
        <label class="preview-field checkbox-field"><input name="intervenesInProduction" type="checkbox" value="true" ${existingRole?.intervenesInProduction ? "checked" : ""} /><span>${t("intervenesInProductionQuestion")}</span></label>
        <label class="preview-field checkbox-field"><input name="intervenesInMaintenance" type="checkbox" value="true" ${existingRole?.intervenesInMaintenance ? "checked" : ""} /><span>${t("intervenesInMaintenanceQuestion")}</span></label>
        <label class="preview-field"><span>Estatus</span><select name="status"><option ${existingRole?.status === "Activo" ? "selected" : ""}>Activo</option><option ${existingRole?.status === "Inactivo" ? "selected" : ""}>Inactivo</option></select></label>
      </div>
      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-labor-role">${t("cancel")}</button>
        <button class="primary-action" type="submit">${isEditing ? t("updateLaborRole") : t("saveLaborRole")}</button>
      </div>
    </form>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-labor-role']").addEventListener("click", closeModal);
  modalContent.querySelector("#laborRoleForm").addEventListener("submit", saveLaborRoleForm);
}

async function saveLaborRoleForm(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const roleId = String(data.get("roleId") || "").trim();
  const requiredPermission = roleId ? "hr.position.update" : "hr.position.create";
  if (!hasPermission(requiredPermission)) {
    renderFormErrors(["No tienes permiso para guardar este puesto."]);
    return;
  }
  const name = String(data.get("name") || "").trim();
  const areaId = String(data.get("areaId") || "").trim();
  const area = mockDb.findLaborArea(areaId);
  const position = String(data.get("position") || "").trim();
  const quantity = Math.max(1, Number(data.get("quantity") || 1));
  const minutesPerResource = Math.max(1, Number(data.get("minutesPerResource") || 1));
  const duplicateRole = mockDb.loadLaborRoles().find((role) =>
    role.id !== roleId && role.areaId === areaId && (
      role.name.trim().toLowerCase() === name.toLowerCase() ||
      role.position.trim().toLowerCase() === position.toLowerCase()
    )
  );
  const errors = [];
  if (!area) errors.push(t("laborAreaInvalid"));
  if (!position) errors.push("Captura el puesto o rol.");
  if (!name) errors.push("Captura el nombre para receta.");
  if (duplicateRole) errors.push(t("laborRoleDuplicate"));
  renderFormErrors(errors);
  if (errors.length) return;

  const item = {
    id: roleId || `mo_${slugify(name)}_${Date.now().toString().slice(-4)}`,
    name,
    areaId: area.id,
    area: area.name,
    position,
    quantity,
    minutesPerResource,
    unit: "min",
    available: quantity * minutesPerResource,
    hourlyCost: Number(data.get("hourlyCost") || 0),
    cost: Number(data.get("hourlyCost") || 0) / 60,
    type: "Mano de obra",
    source: "Recursos Humanos",
    intervenesInProduction: data.get("intervenesInProduction") === "true",
    intervenesInMaintenance: data.get("intervenesInMaintenance") === "true",
    status: String(data.get("status") || "Activo")
  };
  if (getApiMode() === "api") {
    try {
      const payload={labor_area_id:item.areaId,position:item.position,recipe_name:item.name,resource_quantity:item.quantity,minutes_per_resource:item.minutesPerResource,hourly_cost:item.hourlyCost,intervenes_in_production:item.intervenesInProduction,intervenes_in_maintenance:item.intervenesInMaintenance,status:item.status==="Activo"?"active":"inactive"};
      if (roleId) await updateHrPosition(roleId,payload);
      else { const {status,...createPayload}=payload;await createHrPosition(createPayload); }
      closeModal();await loadHrApiData();navigateTo({active:"recursos-humanos",activeSubmodule:"areas-puestos",laborArea:item.areaId});showToast(`Puesto ${item.name} ${roleId?"actualizado":"guardado"}.`);
    } catch(error) { renderFormErrors([error.message]); }
    return;
  }
  if (roleId) {
    mockDb.updateLaborRole(item);
  } else {
    mockDb.addLaborRole(item);
  }
  closeModal();
  navigateTo({ active: "recursos-humanos", activeSubmodule: "areas-puestos", laborArea: item.areaId });
  showToast(`Puesto ${item.name} ${roleId ? "actualizado" : "guardado"}.`);
}

function openWorkerModal(workerId=null){
  const worker=(state.hrApi.workers||[]).find(item=>item.id===workerId);const editing=Boolean(worker);const permission=editing?"hr.worker.update":"hr.worker.create";
  if(!hasPermission(permission)){showToast(t("workerPermissionDenied"));return;}
  const positions=mockDb.loadLaborRoles().filter(item=>item.status==="Activo");
  modalContent.innerHTML=`<form class="recipe-form" id="workerForm"><input type="hidden" name="workerId" value="${worker?.id||""}"/><div class="modal-head"><div><p class="eyebrow">${t("humanResources")}</p><h2>${editing?t("editWorker"):t("newWorker")}</h2></div><button class="modal-close" type="button">×</button></div>
  <fieldset><legend>${t("requiredWorkerData")}</legend><div class="form-grid">
  <label class="preview-field"><span>${t("employeeNumber")}</span><input name="employee_number" value="${escapeAttribute(worker?.employee_number||"")}" placeholder="${codeSequenceConfig("hr.worker")?.mode === "managed" ? t("codeAssignedAutomatically") : "EMP-001"}" ${editing?"disabled":codeSequenceConfig("hr.worker")?.mode === "managed"?"readonly":"required"}/></label>
  <label class="preview-field"><span>${t("firstNames")}</span><input name="first_names" value="${escapeAttribute(worker?.first_names||"")}" required/></label>
  <label class="preview-field"><span>${t("firstLastName")}</span><input name="first_last_name" value="${escapeAttribute(worker?.first_last_name||"")}" required/></label>
  <label class="preview-field"><span>${t("secondLastName")}</span><input name="second_last_name" value="${escapeAttribute(worker?.second_last_name||"")}"/></label>
  <label class="preview-field"><span>CURP</span><input name="curp" minlength="18" maxlength="18" pattern="[A-Za-z0-9]{18}" autocapitalize="characters" value="${escapeAttribute(worker?.curp||"")}" ${editing?"disabled":"required"}/><small>${t("workerCurpHelp")}</small></label>
  <label class="preview-field"><span>RFC</span><input name="rfc" minlength="13" maxlength="13" pattern="[A-Za-z&\u00d1\u00f10-9]{13}" autocapitalize="characters" value="${escapeAttribute(worker?.rfc||"")}" ${editing?"disabled":"required"}/><small>${t("workerRfcHelp")}</small></label>
  <label class="preview-field"><span>NSS</span><input name="nss" inputmode="numeric" minlength="11" maxlength="11" pattern="[0-9]{11}" value="${escapeAttribute(worker?.nss||"")}" ${editing?"disabled":"required"}/><small>${t("workerNssHelp")}</small></label>
  <label class="preview-field"><span>${t("hireDate")}</span><input name="hire_date" type="date" value="${worker?.hire_date||""}" ${editing?"disabled":"required"}/></label>
  <label class="preview-field"><span>${t("workerPosition")}</span><select name="labor_position_id" data-entity-selector required><option value="">${t("selectPosition")}</option>${positions.map(item=>`<option value="${item.id}" ${worker?.labor_position_id===item.id?"selected":""}>${escapeHtml(item.position)} · ${escapeHtml(item.area)}</option>`).join("")}</select></label>
  ${editing?`<label class="preview-field"><span>${t("status")}</span><select name="status"><option value="active" ${worker.status==="active"?"selected":""}>${t("activeStatus")}</option><option value="inactive" ${worker.status==="inactive"?"selected":""}>${t("inactiveStatus")}</option><option value="terminated" ${worker.status==="terminated"?"selected":""}>${t("terminatedStatus")}</option></select></label>`:""}
  </div></fieldset><fieldset><legend>${t("optionalWorkerData")}</legend><div class="form-grid">
  ${[["personal_email",t("personalEmail"),"email"],["phone",t("phone"),"tel"],["birth_date",t("birthDate"),"date"],["nationality",t("nationality"),"text"],["marital_status",t("maritalStatus"),"text"],["address",t("address"),"text"],["emergency_contact_name",t("emergencyContact"),"text"],["emergency_contact_phone",t("emergencyPhone"),"tel"]].map(([name,label,type])=>`<label class="preview-field"><span>${label}</span><input name="${name}" type="${type}" value="${escapeAttribute(worker?.[name]||"")}"/></label>`).join("")}</div></fieldset>
  <div class="form-errors" id="formErrors" hidden></div><div class="modal-actions"><button class="secondary-action" type="button" data-action="close-worker">${t("cancel")}</button><button class="primary-action" type="submit">${editing?t("updateWorker"):t("saveWorker")}</button></div></form>`;
  modalBackdrop.hidden=false;modalContent.querySelector("#workerForm").dataset.codeRequestKey=codeRequestKey("hr.worker");modalContent.querySelector(".modal-close").addEventListener("click",closeModal);modalContent.querySelector("[data-action='close-worker']").addEventListener("click",closeModal);modalContent.querySelector("#workerForm").addEventListener("submit",saveWorkerForm);
}
async function saveWorkerForm(event){event.preventDefault();const data=new FormData(event.currentTarget);const workerId=String(data.get("workerId")||"");const value=name=>String(data.get(name)||"").trim();
  const common={first_names:value("first_names"),first_last_name:value("first_last_name"),second_last_name:value("second_last_name")||null,labor_position_id:value("labor_position_id"),personal_email:value("personal_email")||null,phone:value("phone")||null,nationality:value("nationality")||null,marital_status:value("marital_status")||null,address:value("address")||null,emergency_contact_name:value("emergency_contact_name")||null,emergency_contact_phone:value("emergency_contact_phone")||null};
  try{if(workerId)await updateHrWorker(workerId,{...common,status:value("status")});else {const employeeNumber=await resolveBusinessCode("hr.worker",value("employee_number"),event.currentTarget.dataset.codeRequestKey);await createHrWorker({...common,employee_number:employeeNumber,curp:value("curp"),rfc:value("rfc"),nss:value("nss"),hire_date:value("hire_date"),birth_date:value("birth_date")||null});}closeModal();await loadHrApiData();showToast(t(workerId?"workerUpdated":"workerSaved"));}catch(error){renderFormErrors([error.message]);}}

async function openMachineModal(machineId = null) {
  const existingMachine = machineId ? mockDb.findMachine(machineId) : null;
  const isEditing = Boolean(existingMachine);
  let activeAreas;
  try {
    activeAreas = getApiMode() === "api"
      ? (await getHrAreas()).filter((area) => area.status === "active")
      : mockDb.loadLaborAreas().filter((area) => area.status === "Activo");
  } catch (error) {
    showToast(error.message || t("machineAreasLoadError"));
    return;
  }
  const selectedArea = activeAreas.find((area) => area.id === existingMachine?.areaId) || activeAreas.find((area) => area.name === existingMachine?.area);
  const hasActiveAreas = activeAreas.length > 0;
  modalContent.innerHTML = `
    <form class="recipe-form" id="machineForm">
      <input type="hidden" name="machineId" value="${existingMachine?.id || ""}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("production.machine"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">${isEditing ? "Editar maquina" : "Nueva maquina"}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">x</button>
      </div>
      <p class="helper-copy">${t("machineAreaCatalogHelp")}</p>
      <div class="form-grid">
        <label class="preview-field"><span>${t("stableCode")}</span><input name="code" type="text" value="${escapeAttribute(existingMachine?.code || "")}" placeholder="${codeSequenceConfig("production.machine")?.mode === "managed" ? t("codeAssignedAutomatically") : "MAQ-001"}" ${isEditing || codeSequenceConfig("production.machine")?.mode === "managed" ? "readonly" : ""}></label>
        <label class="preview-field"><span>${t("laborAreaExisting")}</span><select name="area" data-entity-selector required ${hasActiveAreas ? "" : "disabled"}>
          <option value="">${t("machineAreaPlaceholder")}</option>
          ${activeAreas.map((area) => `<option value="${escapeAttribute(area.name)}" data-area-id="${area.id}" ${selectedArea?.id === area.id ? "selected" : ""}>${escapeHtml(area.code)} - ${escapeHtml(area.name)}</option>`).join("")}
        </select></label>
        <label class="preview-field"><span>Tipo de maquina</span><input name="machineType" type="text" value="${existingMachine?.machineType || ""}" placeholder="Ej. Equipo de proceso" required /></label>
        <label class="preview-field"><span>Nombre de maquina</span><input name="name" type="text" value="${existingMachine?.name || ""}" placeholder="Ej. Equipo operativo 02" required /></label>
        <label class="preview-field"><span>Minutos disponibles por dia</span><input name="available" type="number" min="1" value="${existingMachine?.available || 480}" required /></label>
        <label class="preview-field"><span>Costo hora/minuto maquina</span><input name="cost" type="number" min="0" step="0.01" value="${existingMachine?.cost || "1.80"}" required /></label>
        <label class="preview-field"><span>Estatus</span><select name="status"><option ${existingMachine?.status === "Activo" ? "selected" : ""}>Activo</option><option ${existingMachine?.status === "Inactivo" ? "selected" : ""}>Inactivo</option><option ${existingMachine?.status === "Mantenimiento" ? "selected" : ""}>Mantenimiento</option></select></label>
      </div>
      ${hasActiveAreas ? "" : `<div class="validation-card warning machine-area-empty"><strong>${t("machineAreaRequiredFirst")}</strong><span>${t("machineAreaRequiredFirstHelp")}</span><button class="secondary-action" type="button" data-action="open-hr-areas">${t("machineGoToHrAreas")}</button></div>`}
      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-machine">Cancelar</button>
        <button class="primary-action" type="submit" ${hasActiveAreas ? "" : "disabled"}>${isEditing ? "Actualizar maquina" : "Guardar maquina"}</button>
      </div>
    </form>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-machine']").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='open-hr-areas']")?.addEventListener("click", () => {
    closeModal();
    navigateTo({ active: "recursos-humanos", activeSubmodule: "areas-puestos", laborArea: "" });
  });
  modalContent.querySelector("#machineForm").addEventListener("submit", saveMachineForm);
}

async function saveMachineForm(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const machineId = String(data.get("machineId") || "").trim();
  const name = String(data.get("name") || "").trim();
  const area = String(data.get("area") || "").trim();
  const selectedAreaOption = event.currentTarget.querySelector('select[name="area"] option:checked');
  const areaId = selectedAreaOption?.dataset.areaId || "";
  const machineType = String(data.get("machineType") || "").trim();
  const errors = [];
  if (!area || !areaId) errors.push(t("machineAreaInvalid"));
  if (!machineType) errors.push("Captura el tipo de maquina.");
  if (!name) errors.push("Captura el nombre de maquina.");
  renderFormErrors(errors);
  if (errors.length) return;

  const item = {
    id: machineId || `maq_${slugify(name)}_${Date.now().toString().slice(-4)}`,
    name,
    areaId,
    area,
    machineType,
    unit: "min",
    available: Number(data.get("available") || 0),
    cost: Number(data.get("cost") || 0),
    type: "Maquinaria",
    source: "Maquinaria",
    status: String(data.get("status") || "Activo")
  };
  if (getApiMode() === "api") {
    try {
      const status={Activo:"active",Inactivo:"inactive",Mantenimiento:"maintenance"}[item.status];
      const payload={name:item.name,machine_type:item.machineType,area_ref_id:item.areaId,area_name:item.area,available_minutes_per_day:item.available,cost_per_minute:item.cost,status};
      if (machineId) await updateProductionMachine(machineId,payload);
      else { const {status:ignored,...createPayload}=payload;const code=await resolveBusinessCode("production.machine",String(data.get("code")||""),String(data.get("codeRequestKey")||""));await createProductionMachine({...createPayload,code}); }
      closeModal();await loadProductionApiData();navigateTo({active:"produccion",activeSubmodule:"maquinaria",laborArea:""});showToast(`Maquina ${item.name} ${machineId?"actualizada":"guardada"} en Production API.`);
    } catch(error) { renderFormErrors([error.message||"No se pudo guardar la maquina."]); }
    return;
  }
  if (machineId) {
    mockDb.updateMachine(item);
  } else {
    mockDb.addMachine(item);
  }
  closeModal();
  navigateTo({ active: "produccion", activeSubmodule: "maquinaria", laborArea: "" });
  showToast(`Maquina ${item.name} ${machineId ? "actualizada" : "guardada"}.`);
}

async function prepareRecipeResourceCatalog() {
  if (getApiMode() !== "api") return { areas: [] };
  const eligibleMachines = mockDb.loadMachines().filter((machine) => machine.status !== "Inactivo");
  const invalidMachineResources = eligibleMachines.filter((machine) => !machine.areaId);
  setMachineRecipeResources(eligibleMachines
    .map((machine) => ({
      ...machine,
      unit: "min",
      resourceType: "machine",
      type: "Maquinaria",
      source: `${machine.area ? `Maquinaria: ${machine.area}` : "Maquinaria: area pendiente"}${machine.status === "Mantenimiento" ? " - En mantenimiento" : ""}`,
      availabilityWarning: machine.status === "Mantenimiento" ? "En mantenimiento; bloqueara la liberacion mientras no vuelva a estar activa." : ""
    })));
  const hrCatalog = isModuleAccessible("recursos-humanos") && hasPermission("hr.position.read")
    ? await getHrCatalog({ production_only: true })
    : { areas: [], positions: [] };
  const activeAreas = (hrCatalog.areas || []).filter((area) => area.status === "active");
  const areaById = new Map(activeAreas.map((area) => [area.id, area]));
  const eligiblePositions = (hrCatalog.positions || [])
    .filter((position) => position.status === "active" && position.intervenes_in_production && areaById.has(position.labor_area_id));
  const productiveAreaIds = new Set(eligiblePositions.map((position) => position.labor_area_id));
  const selectableAreas = activeAreas.filter((area) => productiveAreaIds.has(area.id));
  setLaborRecipeResources(eligiblePositions
    .map((position) => ({
      id: position.id,
      name: position.recipe_name,
      unit: "min",
      available: Number(position.resource_quantity) * Number(position.minutes_per_resource),
      cost: Number(position.hourly_cost) / 60,
      type: "Mano de obra",
      resourceType: "labor",
      source: `Recursos Humanos: ${areaById.get(position.labor_area_id).name}`
    })));
  if (!isInventoryApiEnabled()) {
    setInventoryRecipeResources([]);
    return { areas: selectableAreas, positions: eligiblePositions, invalidMachineResources };
  }
  const [itemsResponse, balancesResponse] = await Promise.all([
    getInventoryItems({ use_in_recipe: true, status: "active" }),
    getInventoryBalances({ limit: 200 })
  ]);
  const balancesByItem = new Map();
  (balancesResponse.data || []).forEach((balance) => {
    const current = balancesByItem.get(balance.inventory_item_id) || { available: 0, warehouses: new Set() };
    current.available += Number(balance.available_quantity || 0);
    if (Number(balance.available_quantity || 0) !== 0) current.warehouses.add(balance.warehouse_name);
    balancesByItem.set(balance.inventory_item_id, current);
  });
  const activeUnitCodes = new Set(getUnitCatalog().map((unit) => normalizeUnitCode(unit.code)));
  const inventoryResources = (itemsResponse.data || []).map((item) => {
    const balance = balancesByItem.get(item.id) || { available: 0, warehouses: new Set() };
    const unit = normalizeUnitCode(item.base_unit);
    return {
      id: item.id,
      name: item.name,
      unit,
      unitActive: activeUnitCodes.has(unit),
      available: balance.available,
      cost: Number(item.default_unit_cost_per_base_unit ?? item.default_unit_cost ?? 0),
      type: translateInventoryItemType(item.type),
      resourceType: "material",
      source: balance.warehouses.size ? `Almacenes: ${[...balance.warehouses].join(", ")}` : "Almacenes"
    };
  });
  setInventoryRecipeResources(inventoryResources);
  return { areas: selectableAreas, positions: eligiblePositions, invalidMachineResources, invalidInventoryResources: inventoryResources.filter((item) => !item.unitActive) };
}

async function openRecipeModal(recipeId = null) {
  let recipeCatalog;
  try {
    recipeCatalog = await prepareRecipeResourceCatalog();
  } catch (error) {
    showToast(error.message || t("recipeResourcesLoadError"));
    return;
  }
  const existingRecipe = recipeId ? mockDb.findRecipe(recipeId) : null;
  const isEditing = Boolean(existingRecipe);
  const selectedProductId = localStorage.getItem("erclave-recipe-product");
  const selectedProduct = !isEditing && selectedProductId ? mockDb.findProductService(selectedProductId) : null;
  const productsServices = mockDb.loadProductsServices();
  const activeProductService =
    productsServices.find((item) => item.id === existingRecipe?.productServiceId) ||
    productsServices.find((item) => item.name === existingRecipe?.product) ||
    selectedProduct ||
    productsServices[0];
  const activeProductLabel = activeProductService
    ? formatProductServiceOption(activeProductService)
    : "";
  const availableResourceIds = new Set(getRecipeResourceCatalog().map((resource) => resource.id));
  const recipeResources = existingRecipe?.resources?.length
    ? existingRecipe.resources.filter((resource) => getApiMode() !== "api" || availableResourceIds.has(resource.resourceId))
    : getApiMode() === "api" ? [] : ["componente_a", "componente_b", "equipo_proceso_a", "operador_proceso"].map((id) => ({
        resourceId: id,
        quantity: suggestedQuantity(id)
      }));
  const activeAreas = getApiMode() === "api"
    ? (recipeCatalog?.areas || [])
    : mockDb.loadLaborAreas().filter((area) => area.status === "Activo");
  const selectedStageIds = new Set((existingRecipe?.stageDefinitions || []).map((stage) => stage.laborAreaId).filter(Boolean));
  const selectedStageNames = new Set(existingRecipe?.steps || []);

  modalContent.innerHTML = `
    <form class="recipe-form" id="recipeForm">
      <input type="hidden" name="recipeId" value="${existingRecipe?.id || ""}" />
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("production.recipe"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">${isEditing ? "Editar receta" : "Nueva receta"}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("recipeBusinessCode")}</span>
          <input name="code" type="text" maxlength="60" value="${escapeAttribute(existingRecipe?.code || "")}" placeholder="${codeSequenceConfig("production.recipe")?.mode === "managed" ? t("codeAssignedAutomatically") : "REC-001"}" ${isEditing || codeSequenceConfig("production.recipe")?.mode === "managed" ? "readonly" : ""} />
          <small>${t("businessCodeHelp")}</small>
        </label>
        <label class="preview-field product-lookup-field">
          <span>Producto o servicio</span>
          <input id="recipeProductSearch" type="text" value="${activeProductLabel}" placeholder="Busca por clave, nombre o tipo" autocomplete="off" required />
          <input name="productServiceId" type="hidden" value="${activeProductService?.id || ""}" />
          <div class="lookup-results" id="recipeProductResults" hidden></div>
        </label>
        <label class="preview-field">
          <span>Version</span>
          <input name="version" type="number" min="1" value="${existingRecipe?.version || 1}" required />
        </label>
        <label class="preview-field">
          <span>Cantidad base</span>
          <input name="quantityBase" type="number" min="1" value="${existingRecipe?.quantityBase || 1}" required />
        </label>
        <label class="preview-field">
          <span>Duracion sugerida (dias productivos)</span>
          <input name="suggestedDurationDays" type="number" min="1" max="365" value="${existingRecipe?.suggestedDurationDays || 1}" required />
          <small>Se propone al crear la orden y puede ajustarse.</small>
        </label>
        <label class="preview-field">
          <span>Unidad</span>
          ${unitSelect("unit", existingRecipe?.unit || activeProductService?.unit || "H87")}
        </label>
        <label class="preview-field wide-field">
          <span>Centro de costos</span>
          <input name="center" type="text" value="${existingRecipe?.center || activeProductService?.center || "Produccion / General"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Cantidad para proyectar costo</span>
          <input name="simulationQuantity" type="number" min="1" value="${localStorage.getItem("erclave-validation-qty") || 100}" required />
        </label>
        <label class="preview-field">
          <span>Estado de aprobacion</span>
          <select name="approvalStatus">
            ${["Borrador", "Pendiente de aprobacion", "Aprobada", "Obsoleta"].map((status) => `
              <option value="${status}" ${getRecipeApprovalStatus(existingRecipe || {}) === status ? "selected" : ""}>${status}</option>
            `).join("")}
          </select>
        </label>
        <label class="preview-field wide-field">
          <span>Motivo de cambio</span>
          <input name="changeReason" type="text" value="${existingRecipe?.changeReason || ""}" placeholder="Ej. Ajuste de costo, mejora de proceso o nueva version" />
        </label>
      </div>

      <div class="section-title form-section-title">
        <span class="section-icon">▦</span>
        <strong>Recursos por unidad</strong>
      </div>

      <p class="helper-copy">${t("recipeEligibleResourcesHelp")}</p>

      ${recipeCatalog?.invalidInventoryResources?.length ? `<div class="validation-card warning"><strong>${t("recipeInactiveUnitTitle")}</strong><p>${t("recipeInactiveUnitHelp")}</p><p>${recipeCatalog.invalidInventoryResources.map((item) => `${escapeHtml(item.name)} (${escapeHtml(item.unit)})`).join(", ")}</p></div>` : ""}

      ${recipeCatalog?.invalidMachineResources?.length ? `<div class="validation-card warning"><strong>${t("recipeMachineAreaMissingTitle")}</strong><p>${t("recipeMachineAreaMissingHelp")}</p><p>${recipeCatalog.invalidMachineResources.map((item) => escapeHtml(item.name)).join(", ")}</p></div>` : ""}

      <div class="recipe-resource-groups">
        ${renderRecipeResourceGroup("material", recipeResources)}
        ${renderRecipeResourceGroup("labor", recipeResources)}
        ${renderRecipeResourceGroup("machine", recipeResources)}
      </div>

      <fieldset class="recipe-area-stages">
        <legend>${t("recipeAreasLegend")}</legend>
        <p class="helper-copy">${t("recipeAreasHelp")}</p>
        ${activeAreas.length ? `<div class="recipe-area-grid">${activeAreas.map((area) => `
          <label class="recipe-area-option">
            <input type="checkbox" name="stageAreaId" value="${area.id}" data-area-name="${escapeAttribute(area.name)}" ${selectedStageIds.has(area.id) || selectedStageNames.has(area.name) ? "checked" : ""} />
            <span class="recipe-area-card">
              <span class="recipe-area-check" aria-hidden="true">✓</span>
              <span><strong>${escapeHtml(area.name)}</strong><small>${escapeHtml(area.code || area.id)}</small></span>
            </span>
            <span class="recipe-stage-weight"><span>${t("recipePhaseWeight")}</span><input data-stage-weight type="number" min="0.01" max="100" step="0.01" value="${escapeAttribute(existingRecipe?.stageDefinitions?.find((stage)=>stage.laborAreaId===area.id||stage.laborAreaName===area.name)?.weightPercent || "")}"><small>%</small></span>
          </label>
        `).join("")}</div>` : `<p class="validation-card warning">${t("recipeAreasEmpty")}</p>`}
      </fieldset>

      <div class="form-errors" id="formErrors" hidden></div>

      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="preview-recipe">Validar definicion</button>
        <button class="primary-action" type="submit">${isEditing ? "Actualizar receta" : "Guardar receta"}</button>
      </div>

      <div class="recipe-preview" id="recipePreview"></div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("#recipeProductSearch").addEventListener("focus", renderRecipeProductLookup);
  modalContent.querySelector("#recipeProductSearch").addEventListener("input", syncRecipeProductFields);
  modalContent.querySelector("#recipeProductResults").addEventListener("click", selectRecipeProductFromLookup);
  modalContent.querySelectorAll("[data-action='add-resource']").forEach((button) => button.addEventListener("click", addResourceRow));
  modalContent.querySelector("[data-action='preview-recipe']").addEventListener("click", previewRecipeForm);
  modalContent.querySelector("#recipeForm").addEventListener("submit", saveRecipeForm);
  modalContent.querySelectorAll('input[name="stageAreaId"]').forEach((checkbox)=>checkbox.addEventListener("change",()=>{const selected=[...modalContent.querySelectorAll('input[name="stageAreaId"]:checked')];const base=selected.length?Math.floor(10000/selected.length)/100:0;selected.forEach((entry,index)=>{entry.closest(".recipe-area-option").querySelector("[data-stage-weight]").value=index===selected.length-1?(100-base*(selected.length-1)).toFixed(2):base.toFixed(2);});modalContent.querySelectorAll('input[name="stageAreaId"]:not(:checked)').forEach((entry)=>{entry.closest(".recipe-area-option").querySelector("[data-stage-weight]").value="";});}));
  bindResourceRowActions();
}

function formatProductServiceOption(item) {
  return `${item.name} - ${item.sku}`;
}

function findProductServiceByOption(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return mockDb.loadProductsServices().find((item) =>
    formatProductServiceOption(item).toLowerCase() === normalized ||
    item.id.toLowerCase() === normalized
  );
}

function getProductServiceMatches(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const items = mockDb.loadProductsServices();
  if (!normalized) return items;
  return items.filter((item) =>
    [item.id, item.sku, item.name, item.kind, item.category, item.center]
      .join(" ")
      .toLowerCase()
      .includes(normalized)
  );
}

function renderRecipeProductLookup(event) {
  const input = event.target;
  const results = modalContent.querySelector("#recipeProductResults");
  const matches = getProductServiceMatches(input.value);
  results.hidden = false;
  results.innerHTML = matches.length
    ? matches
        .map((item) => `
          <button class="lookup-option" type="button" data-product-id="${item.id}">
            <strong>${item.name}</strong>
            <span>${item.sku} · ${item.kind} · ${item.unit}</span>
          </button>
        `)
        .join("")
    : `<div class="lookup-empty">Sin coincidencias en el catalogo.</div>`;
}

function selectRecipeProductFromLookup(event) {
  const button = event.target.closest("[data-product-id]");
  if (!button) return;
  const item = mockDb.findProductService(button.dataset.productId);
  if (!item) return;
  const form = button.closest("form");
  form.querySelector("#recipeProductSearch").value = formatProductServiceOption(item);
  form.querySelector("[name='productServiceId']").value = item.id;
  form.querySelector("[name='unit']").value = normalizeUnitCode(item.unit);
  form.querySelector("[name='center']").value = item.center;
  modalContent.querySelector("#recipeProductResults").hidden = true;
}

function syncRecipeProductFields(event) {
  const form = event.target.closest("form");
  const item = findProductServiceByOption(event.target.value);
  form.querySelector("[name='productServiceId']").value = item?.id || "";
  renderRecipeProductLookup(event);
  if (!item) return;
  form.querySelector("[name='unit']").value = normalizeUnitCode(item.unit);
  form.querySelector("[name='center']").value = item.center;
}

function getRecipeResourceType(item) {
  const catalogItem = getResource(item.resourceId || item.id);
  return catalogItem?.resourceType || item.resourceType || (catalogItem?.type === "Maquinaria" ? "machine" : catalogItem?.type === "Mano de obra" ? "labor" : "material");
}

function renderRecipeResourceGroup(resourceType, recipeResources) {
  const config = {
    material: { icon: "MP", title: t("recipeMaterialsTitle"), help: t("recipeMaterialsHelp"), add: t("recipeAddMaterial"), empty: t("recipeMaterialsEmpty") },
    labor: { icon: "HH", title: t("recipeLaborTitle"), help: t("recipeLaborHelp"), add: t("recipeAddLabor"), empty: t("recipeLaborEmpty") },
    machine: { icon: "HM", title: t("recipeMachinesTitle"), help: t("recipeMachinesHelp"), add: t("recipeAddMachine"), empty: t("recipeMachinesEmpty") }
  }[resourceType];
  const catalog = getRecipeResourceCatalog().filter((resource) => getRecipeResourceType(resource) === resourceType);
  const selectableCatalog = catalog.filter((resource) => resourceType !== "material" || resource.unitActive !== false);
  const selected = recipeResources.filter((resource) => getRecipeResourceType(resource) === resourceType);
  return `
    <section class="recipe-resource-group recipe-resource-group-${resourceType}" aria-labelledby="recipe-resource-${resourceType}-title">
      <div class="recipe-resource-group-head">
        <span class="recipe-resource-type-icon" aria-hidden="true">${config.icon}</span>
        <div><strong id="recipe-resource-${resourceType}-title">${config.title}</strong><p>${config.help}</p></div>
      </div>
      <div class="resource-picker">
        <select id="resourceSelect-${resourceType}" data-entity-selector aria-label="${config.title}" ${selectableCatalog.length ? "" : "disabled"}>
          ${catalog.map((resource) => `<option value="${escapeAttribute(resource.id)}" ${resourceType === "material" && resource.unitActive === false ? "disabled" : ""}>${escapeHtml(resource.name)} · ${escapeHtml(resource.source)}${resourceType === "material" && resource.unitActive === false ? ` · ${t("recipeInactiveUnitOption")}` : ""}</option>`).join("")}
        </select>
        <button class="secondary-action" type="button" data-action="add-resource" data-resource-type="${resourceType}" ${selectableCatalog.length ? "" : "disabled"}>${config.add}</button>
      </div>
      <div class="selected-resource-list" id="selectedResourceList-${resourceType}">
        ${selected.length ? selected.map((item) => renderSelectedResourceRow(item.resourceId, item.quantity, item)).join("") : `<p class="recipe-resource-empty">${config.empty}</p>`}
      </div>
    </section>`;
}

function renderSelectedResourceRow(resourceId, quantity = 0, fallback = {}) {
  const resource = getResource(resourceId) || {
    id: resourceId,
    name: fallback.resourceName || resourceId,
    type: fallback.resourceType || "Recurso",
    source: "Production API",
    available: 0,
    unit: fallback.unit || "",
    cost: Number(fallback.unitCost || 0),
    resourceType: fallback.resourceType || "material"
  };
  const resourceType = getRecipeResourceType(resource);
  const isTimed = resourceType === "labor" || resourceType === "machine";
  const storageFactor = isTimed ? 60 : 1;
  const displayQuantity = Number(quantity || 0) / storageFactor;
  const displayAvailable = Number(resource.available || 0) / storageFactor;
  const displayUnit = resourceType === "labor" ? t("recipeLaborUnit") : resourceType === "machine" ? t("recipeMachineUnit") : resource.unit;
  const quantityLabel = resourceType === "labor" ? t("recipeLaborQuantity") : resourceType === "machine" ? t("recipeMachineQuantity") : `${t("recipeMaterialQuantity")} (${resource.unit})`;
  return `
    <div class="selected-resource-row" data-resource-row="${escapeAttribute(resource.id)}" data-resource-type="${resourceType}" data-storage-factor="${storageFactor}">
      <div>
        <strong>${escapeHtml(resource.name)}</strong>
        <span>${escapeHtml(resource.type)} · ${escapeHtml(resource.source)} · ${t("recipeAvailable")} ${formatNumber(displayAvailable)} ${escapeHtml(displayUnit)}${resourceType === "material" && resource.unitActive === false ? ` · ${t("recipeInactiveUnitOption")}` : ""}</span>
      </div>
      <label>
        <span>${quantityLabel}</span>
        <input name="resource_${escapeAttribute(resource.id)}" type="number" min="0" step="${isTimed ? "any" : "0.01"}" value="${displayQuantity}" />
        ${isTimed ? `<small class="recipe-time-hint">${t("recipeTimeDecimalHelp")}</small>` : ""}
      </label>
      <button class="icon-button remove-resource" type="button" data-action="remove-resource" aria-label="Quitar recurso">×</button>
    </div>
  `;
}

function addResourceRow() {
  const resourceType = this.dataset.resourceType;
  const select = modalContent.querySelector(`#resourceSelect-${resourceType}`);
  const list = modalContent.querySelector(`#selectedResourceList-${resourceType}`);
  const resourceId = select.value;
  if (list.querySelector(`[data-resource-row="${resourceId}"]`)) {
    showToast("Ese recurso ya esta en la receta.");
    return;
  }
  list.querySelector(".recipe-resource-empty")?.remove();
  list.insertAdjacentHTML("beforeend", renderSelectedResourceRow(resourceId, resourceType === "material" ? 1 : 60));
  bindResourceRowActions();
}

function bindResourceRowActions() {
  modalContent.querySelectorAll("[data-action='remove-resource']").forEach((button) => {
    button.onclick = () => {
      button.closest("[data-resource-row]").remove();
    };
  });
}

function suggestedQuantity(resourceId) {
  const defaults = {
    componente_a: 2,
    componente_b: 1,
    empaque_estandar: 1,
    equipo_proceso_a: 30,
    operador_proceso: 45
  };
  return defaults[resourceId] ?? 0;
}

function buildRecipeFromForm(form) {
  const data = new FormData(form);
  const recipeId = String(data.get("recipeId") || "").trim();
  const productServiceId = String(data.get("productServiceId") || "").trim();
  const productService = mockDb.findProductService(productServiceId);
  const selectedRows = [...form.querySelectorAll("[data-resource-row]")];
  const existingRecipe = recipeId ? mockDb.findRecipe(recipeId) : null;
  const stageDefinitions = [...form.querySelectorAll('input[name="stageAreaId"]:checked')].map((input) => ({
    laborAreaId: input.value,
    laborAreaName: input.dataset.areaName,
    name: input.dataset.areaName,
    weightPercent: Number(input.closest(".recipe-area-option").querySelector("[data-stage-weight]")?.value || 0)
  }));
  const resources = selectedRows
    .map((row) => {
      const resourceId = row.dataset.resourceRow;
      const existingResource = existingRecipe?.resources?.find((item) => item.resourceId === resourceId);
      return {
        resourceId,
        quantity: Number(data.get(`resource_${resourceId}`) || 0) * Number(row.dataset.storageFactor || 1),
        resourceCode: existingResource?.resourceCode,
        resourceName: existingResource?.resourceName,
        resourceType: existingResource?.resourceType,
        unit: existingResource?.unit,
        unitCost: existingResource?.unitCost
      };
    })
    .filter((item) => item.quantity > 0);

  return {
    id: recipeId || `REC-${Date.now().toString().slice(-5)}`,
    code: String(data.get("code") || "").trim().toUpperCase(),
    codeRequestKey: String(data.get("codeRequestKey") || ""),
    productServiceId,
    product: productService?.name || "",
    version: Number(data.get("version") || 1),
    quantityBase: Number(data.get("quantityBase") || 1),
    suggestedDurationDays: Math.max(1,Number(data.get("suggestedDurationDays") || 1)),
    unit: String(data.get("unit") || "").trim(),
    status: String(data.get("approvalStatus") || "Borrador") === "Aprobada" ? "Activa" : "Borrador",
    approvalStatus: String(data.get("approvalStatus") || "Borrador"),
    approvedBy: String(data.get("approvalStatus") || "") === "Aprobada" ? "Usuario actual" : "",
    approvedAt: String(data.get("approvalStatus") || "") === "Aprobada" ? new Date().toISOString().slice(0, 10) : "",
    changeReason: String(data.get("changeReason") || "").trim(),
    center: String(data.get("center") || "").trim(),
    resources,
    steps: stageDefinitions.map((stage) => stage.name),
    stageDefinitions,
    createdAt: recipeId ? (mockDb.findRecipe(recipeId)?.createdAt || new Date().toISOString().slice(0, 10)) : new Date().toISOString().slice(0, 10)
  };
}

function toApiRecipeVersionPayload(recipe) {
  return {
    base_quantity: recipe.quantityBase,
    base_unit: normalizeUnitCode(recipe.unit),
    suggested_duration_days: recipe.suggestedDurationDays || 1,
    change_reason: recipe.changeReason || null,
    resources: recipe.resources.map((item, index) => {
      const catalogItem = getResource(item.resourceId);
      return {
        resource_type: item.resourceType || catalogItem?.resourceType || (catalogItem?.type === "Maquinaria" ? "machine" : catalogItem?.type === "Mano de obra" ? "labor" : "other"),
        resource_ref_id: item.resourceId || null,
        resource_code: item.resourceCode || catalogItem?.id || item.resourceId,
        resource_name: item.resourceName || catalogItem?.name || item.resourceId,
        quantity: Number(item.quantity),
        unit: normalizeUnitCode(item.unit || catalogItem?.unit || recipe.unit),
        unit_cost: Number(item.unitCost ?? catalogItem?.cost ?? 0),
        sort_order: index + 1
      };
    }),
    stages: recipe.stageDefinitions.map((stage, index) => ({
      labor_area_ref_id: stage.laborAreaId,
      labor_area_name: stage.laborAreaName,
      name: stage.name,
      expected_minutes: stage.expectedMinutes || null,
      sort_order: index + 1,
      weight_percent: Number(stage.weightPercent),
      status: "active"
    }))
  };
}

function validateRecipe(recipe) {
  const errors = [];
  if (!recipe.productServiceId || !recipe.product) errors.push("Selecciona un producto o servicio del catalogo.");
  if (!recipe.unit) errors.push("Captura la unidad base.");
  if (!recipe.center) errors.push("Selecciona o captura centro de costos.");
  if (!recipe.resources.length) errors.push("Agrega al menos un recurso con cantidad mayor a cero.");
  const invalidMaterialUnits = recipe.resources.map((resource) => getResource(resource.resourceId)).filter((resource) => resource?.resourceType === "material" && resource.unitActive === false);
  if (invalidMaterialUnits.length) errors.push(t("recipeInactiveUnitError").replace("{items}", invalidMaterialUnits.map((item) => `${item.name} (${item.unit})`).join(", ")));
  if (!recipe.steps.length) errors.push("Captura al menos una etapa.");
  const stageWeight = recipe.stageDefinitions.reduce((sum, stage) => sum + Number(stage.weightPercent || 0), 0);
  if (recipe.steps.length && Math.abs(stageWeight - 100) > 0.001) errors.push(t("recipePhaseWeightTotal"));
  return errors;
}

function renderFormErrors(errors) {
  const box = modalContent.querySelector("#formErrors");
  if (!box) return;
  box.setAttribute("role", "alert");
  box.setAttribute("aria-live", "assertive");
  box.setAttribute("tabindex", "-1");
  if (!errors.length) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  box.hidden = false;
  box.innerHTML = errors.map((error) => `<p>${escapeHtml(String(error))}</p>`).join("");
  box.focus({ preventScroll: false });
}

function previewRecipeForm() {
  const form = modalContent.querySelector("#recipeForm");
  const recipe = buildRecipeFromForm(form);
  const simulationQuantity = Math.max(1, Number(new FormData(form).get("simulationQuantity") || 1));
  const errors = validateRecipe(recipe);
  renderFormErrors(errors);
  if (errors.length) return;

  localStorage.setItem("erclave-validation-qty", simulationQuantity);
  const validation = validateRecipeDefinition(recipe, simulationQuantity);
  modalContent.querySelector("#recipePreview").innerHTML = `
    <div class="validator-head">
      <div>
        <span class="muted-label">Vista previa de definicion y costo</span>
        <strong>${formatNumber(simulationQuantity)} ${recipe.unit} · ${formatCurrency(validation.totalCost)}</strong>
      </div>
      <span class="chip ${validation.missing.length ? "warning" : "active"}">
        ${validation.missing.length ? `${validation.missing.length} referencias no elegibles` : "Recursos definidos"}
      </span>
    </div>
    <div class="resource-check-grid compact">
      ${validation.rows
        .map(
          (row) => `
            <article class="resource-check ${row.ok ? "ok" : "risk"}">
              <div>
                <strong>${row.name}</strong>
                <span>${row.type}</span>
              </div>
              <p>${row.ok ? `Existe en catalogo · ${formatRecipeValidationQuantity(row.required, row.type)} ${row.type === "Mano de obra" ? t("recipeLaborUnit") : row.type === "Maquinaria" ? t("recipeMachineUnit") : row.unit} en la proyeccion` : "No existe en el catalogo elegible"}</p>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

async function saveRecipeForm(event) {
  event.preventDefault();
  const recipe = buildRecipeFromForm(event.currentTarget);
  const errors = validateRecipe(recipe);
  renderFormErrors(errors);
  if (errors.length) return;

  const currentRecipe = mockDb.findRecipe(recipe.id);
  const exists = Boolean(currentRecipe);
  if (getApiMode() === "api") {
    try {
      const versionPayload = toApiRecipeVersionPayload(recipe);
      let savedVersion;
      if (!exists) {
        const businessCode = await resolveBusinessCode("production.recipe", recipe.code, recipe.codeRequestKey);
        const created = await createProductionRecipe({
          ...versionPayload,
          product_service_id: recipe.productServiceId,
          code: businessCode,
          name: `Receta ${recipe.product}`
        });
        savedVersion = created.versions?.[0];
      } else if (currentRecipe.versionStatus === "draft") {
        savedVersion = await updateProductionRecipeVersion(currentRecipe.versionId, versionPayload);
      } else {
        savedVersion = await createProductionRecipeVersion(currentRecipe.id, {
          ...versionPayload,
          change_reason: recipe.changeReason || "Nueva version desde frontend"
        });
      }

      if (["Pendiente de aprobacion", "Aprobada"].includes(recipe.approvalStatus) && savedVersion?.status === "draft") {
        savedVersion = await submitProductionRecipeVersion(savedVersion.id);
      }
      if (recipe.approvalStatus === "Aprobada" && savedVersion?.status === "pending_approval") {
        await approveProductionRecipeVersion(savedVersion.id, {
          approval_notes: recipe.changeReason || "Aprobada desde frontend"
        });
      }

      localStorage.removeItem("erclave-recipe-product");
      closeModal();
      await loadProductionApiData();
      navigateTo({ active: "produccion", activeSubmodule: "recetas", laborArea: "" });
      showToast(`${formatRecipeDisplayLabel(recipe)}: receta ${exists ? "actualizada" : "guardada"} en Production API.`);
    } catch (error) {
      renderFormErrors([error?.payload?.error?.code === "machine_resource_invalid" ? t("recipeMachineAreaMissingError") : (error.message || "No se pudo guardar la receta en Production API.")]);
    }
    return;
  }
  if (exists) {
    mockDb.updateRecipe(recipe);
  } else {
    mockDb.addRecipe(recipe);
  }
  const productService = mockDb.findProductService(recipe.productServiceId);
  if (productService) {
    mockDb.updateProductService({
      ...productService,
      standardCost: getRecipeStandardCost(recipe)
    });
  }
  localStorage.setItem("erclave-selected-recipe", recipe.id);
  localStorage.removeItem("erclave-recipe-product");
  closeModal();
  navigateTo({ active: "produccion", activeSubmodule: "recetas", laborArea: "" });
  showToast(`${formatRecipeDisplayLabel(recipe)}: receta ${exists ? "actualizada" : "guardada"} y validada contra almacen.`);
}

async function approveRecipe(recipeId) {
  const recipe = mockDb.findRecipe(recipeId);
  if (!recipe) return;
  if (getApiMode() === "api") {
    try {
      let versionStatus = recipe.versionStatus;
      if (versionStatus === "draft") {
        versionStatus = (await submitProductionRecipeVersion(recipe.versionId)).status;
      }
      if (versionStatus === "pending_approval") {
        await approveProductionRecipeVersion(recipe.versionId, { approval_notes: "Aprobada desde frontend" });
      }
      await loadProductionApiData();
      showToast(`${formatRecipeDisplayLabel(recipe)}: receta aprobada para produccion.`);
    } catch (error) {
      showToast(error.message || "No se pudo aprobar la receta en Production API.");
    }
    return;
  }
  mockDb.updateRecipe({
    ...recipe,
    status: "Activa",
    approvalStatus: "Aprobada",
    approvedBy: "Usuario actual",
    approvedAt: new Date().toISOString().slice(0, 10)
  });
  render();
  showToast(`${formatRecipeDisplayLabel(recipe)}: receta aprobada para produccion.`);
}

function deleteRecipe(recipeId) {
  const recipe = mockDb.findRecipe(recipeId);
  if (!recipe) return;
  if (getApiMode() === "api") {
    showToast("Production API conserva recetas auditables; crea una nueva version en lugar de eliminarla.");
    return;
  }
  const hasOrders = mockDb.loadOrders().some((order) => order.recipeId === recipeId);
  if (hasOrders) {
    showToast(`${formatRecipeDisplayLabel(recipe)} tiene ordenes relacionadas; no se puede eliminar la receta.`);
    return;
  }
  const confirmed = window.confirm(`Eliminar la receta de ${formatRecipeDisplayLabel(recipe)}?`);
  if (!confirmed) return;
  const recipes = mockDb.deleteRecipe(recipeId);
  if (localStorage.getItem("erclave-selected-recipe") === recipeId) {
    localStorage.setItem("erclave-selected-recipe", recipes[0]?.id || (shouldUseSeedModuleData() ? defaultRecipes[0].id : ""));
  }
  render();
  showToast(`${formatRecipeDisplayLabel(recipe)}: receta eliminada.`);
}

function localDateValue(value=new Date()) {
  const adjusted=new Date(value.getTime()-value.getTimezoneOffset()*60000);
  return adjusted.toISOString().slice(0,10);
}

function productionEndDate(startValue,durationDays) {
  let current=new Date(`${startValue}T12:00:00`);
  let remaining=Math.max(1,Number(durationDays)||1);
  while(remaining>0){
    if(current.getDay()!==0&&current.getDay()!==6)remaining-=1;
    if(remaining>0)current.setDate(current.getDate()+1);
  }
  return localDateValue(current);
}

async function openOrderModal() {
  const recipes = mockDb.loadRecipes();
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe") || recipes[0]?.id;
  const recipe = recipes.find((item) => item.id === selectedRecipeId) || recipes[0] || (shouldUseSeedModuleData() ? defaultRecipes[0] : null);
  if (!recipe) {
    showToast("Primero crea una receta para generar ordenes de produccion.");
    return;
  }
  const defaultQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);
  let eligibleWorkers=[];
  try{eligibleWorkers=getApiMode()==="api"?await getProductionEligibleWorkers():(state.hrApi.workers||[]).filter(item=>item.status==="active"&&item.intervenes_in_production);}catch(error){showToast(error.message||"No se pudo cargar el personal elegible.");return;}
  if(!eligibleWorkers.length){showToast("Da de alta trabajadores activos en puestos habilitados para produccion antes de generar una orden.");return;}
  state.hrApi.workers=eligibleWorkers;
  const workerOptions=eligibleWorkers.map(worker=>`<option value="${worker.id}">${escapeHtml(worker.full_name)} · ${escapeHtml(worker.position_name)}</option>`).join("");

  const defaultStartDate=localDateValue();
  const defaultDurationDays=recipe.suggestedDurationDays||1;
  const defaultDueDate=productionEndDate(defaultStartDate,defaultDurationDays);

  modalContent.innerHTML = `
    <form class="recipe-form" id="orderForm">
      <input type="hidden" name="codeRequestKey" value="${escapeAttribute(codeRequestKey("production.order"))}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">Generar orden de produccion</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>${t("productionOrderBusinessCode")}</span>
          <input name="code" type="text" maxlength="60" placeholder="${codeSequenceConfig("production.order")?.mode === "managed" ? t("codeAssignedAutomatically") : "OP-001"}" ${codeSequenceConfig("production.order")?.mode === "managed" ? "readonly" : ""} />
          <small>${t("businessCodeHelp")}</small>
        </label>
        <label class="preview-field wide-field">
          <span>Receta</span>
          <select name="recipeId" id="orderRecipeSelect" data-entity-selector required>
            ${recipes
              .map(
                (item) => `
                  <option value="${item.id}" ${item.id === recipe.id ? "selected" : ""}>
                    ${formatRecipeDisplayLabel(item)} · v${item.version} · ${getRecipeApprovalStatus(item)}
                  </option>
                `
              )
              .join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>Cantidad de piezas/servicios</span>
          <input name="quantity" type="number" min="1" value="${defaultQuantity}" required />
        </label>
        <label class="preview-field">
          <span>Inicio planeado</span>
          <input name="plannedStartDate" type="date" value="${defaultStartDate}" required />
        </label>
        <label class="preview-field">
          <span>Dias productivos</span>
          <input name="plannedDurationDays" type="number" min="1" max="365" value="${defaultDurationDays}" required />
          <small>Capacidad distribuida de lunes a viernes.</small>
        </label>
        <label class="preview-field">
          <span>Fecha requerida</span>
          <input name="dueDate" type="date" value="${defaultDueDate}" required />
        </label>
        <label class="preview-field">
          <span>Prioridad</span>
          <select name="priority">
            <option>Alta</option>
            <option>Media</option>
            <option>Baja</option>
          </select>
        </label>
        <label class="preview-field">
          <span>Responsable general</span>
          <select name="responsibleWorkerId" data-entity-selector required><option value="">Selecciona una persona</option>${workerOptions}</select>
        </label>
      </div>

      <div class="section-title form-section-title">
        <span class="section-icon">↳</span>
        <strong>Responsables por etapa operativa</strong>
      </div>
      <div class="area-assignment-list" id="areaAssignmentList">
        ${renderAreaAssignments(recipe,eligibleWorkers)}
      </div>

      <div class="form-errors" id="formErrors" hidden></div>

      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="preview-order">Validar orden</button>
        <button class="primary-action" type="submit">Generar en produccion</button>
      </div>

      <div class="recipe-preview" id="orderPreview"></div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("#orderRecipeSelect").addEventListener("change", (event) => {
    const nextRecipe = mockDb.findRecipe(event.target.value) || recipe;
    modalContent.querySelector("#areaAssignmentList").innerHTML = renderAreaAssignments(nextRecipe,eligibleWorkers);
    modalContent.querySelector("[name='plannedDurationDays']").value=nextRecipe.suggestedDurationDays||1;
    const start=modalContent.querySelector("[name='plannedStartDate']").value;
    modalContent.querySelector("[name='dueDate']").value=productionEndDate(start,nextRecipe.suggestedDurationDays||1);
  });
  const syncOrderEnd=()=>{const start=modalContent.querySelector("[name='plannedStartDate']").value;const duration=modalContent.querySelector("[name='plannedDurationDays']").value;if(start)modalContent.querySelector("[name='dueDate']").value=productionEndDate(start,duration);};
  modalContent.querySelector("[name='plannedStartDate']").addEventListener("change",syncOrderEnd);
  modalContent.querySelector("[name='plannedDurationDays']").addEventListener("input",syncOrderEnd);
  modalContent.querySelector("[data-action='preview-order']").addEventListener("click", previewOrderForm);
  modalContent.querySelector("#orderForm").addEventListener("submit", saveOrderForm);
}

function renderAreaAssignments(recipe,workers=[]) {
  const options=workers.map(worker=>`<option value="${worker.id}">${escapeHtml(worker.full_name)} · ${escapeHtml(worker.position_name)}</option>`).join("");
  return (recipe.steps.length ? recipe.steps : ["Produccion"]).map((step,index) => `
    <label class="selected-resource-row area-assignment-row" data-area="${step}">
      <div>
        <strong>${t("recipePhaseNumber")} ${index+1}: ${step}</strong>
        <span>${t("recipePhaseWeightLabel",{weight:recipe.stageDefinitions?.[index]?.weightPercent||0})}</span>
      </div>
      <select name="area_${slugify(step)}" data-entity-selector required><option value="">Selecciona una persona</option>${options}</select>
    </label>
  `).join("");
}

function slugify(value) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

function buildOrderFromForm(form) {
  const data = new FormData(form);
  const recipe = mockDb.findRecipe(String(data.get("recipeId"))) || (shouldUseSeedModuleData() ? defaultRecipes[0] : null);
  if (!recipe) return null;
  const quantity = Math.max(1, Number(data.get("quantity") || 1));
  const workers=state.hrApi.workers||[];const workerName=id=>workers.find(item=>item.id===id)?.full_name||id;
  const areas = (recipe.steps.length ? recipe.steps : ["Produccion"]).map((step) => ({
    area: step,
    responsibleWorkerId:String(data.get(`area_${slugify(step)}`)||"").trim(),responsible:workerName(String(data.get(`area_${slugify(step)}`)||"")),
    status: "Pendiente",
    progress: 0,
    actualCostFactor: 1
  }));
  const release = getReleaseReview(recipe, quantity);
  const plannedCost = release.validation.totalCost;

  return {
    id: `OP-${Date.now().toString().slice(-5)}`,
    code: String(data.get("code") || "").trim().toUpperCase(),
    codeRequestKey: String(data.get("codeRequestKey") || ""),
    recipeId: recipe.id,
    recipeVersion: recipe.version,
    recipeSnapshot: createRecipeSnapshot(recipe),
    recipeName: recipe.product,
    quantity,
    unit: recipe.unit,
    status: "Liberada",
    priority: String(data.get("priority") || "Media"),
    plannedStartDate: String(data.get("plannedStartDate") || ""),
    plannedDurationDays: Math.max(1,Number(data.get("plannedDurationDays")||1)),
    plannedEndDate: productionEndDate(String(data.get("plannedStartDate")||localDateValue()),Number(data.get("plannedDurationDays")||1)),
    dueDate: String(data.get("dueDate") || ""),
    center: recipe.center,
    responsibleWorkerId:String(data.get("responsibleWorkerId")||"").trim(),responsible:workerName(String(data.get("responsibleWorkerId")||"")),
    plannedCost,
    actualCost: null,
    releaseStatus: release.canRelease ? "Liberada" : "Bloqueada",
    areas,
    createdAt: new Date().toISOString().slice(0, 10)
  };
}

function validateOrder(order) {
  const errors = [];
  if (!order) return ["Primero crea una receta para generar ordenes de produccion."];
  const recipe = getOrderRecipe(order);
  if (!order.recipeId) errors.push("Selecciona una receta.");
  if (!order.quantity) errors.push("Captura la cantidad.");
  if (!order.plannedStartDate) errors.push("Captura la fecha de inicio planeada.");
  if (!order.plannedDurationDays) errors.push("Captura los dias productivos.");
  if (!order.dueDate) errors.push("Captura fecha requerida.");
  if(order.dueDate&&order.plannedEndDate&&order.dueDate<order.plannedEndDate)errors.push("La fecha requerida no puede ser anterior al fin planeado.");
  if (!order.responsibleWorkerId) errors.push("Selecciona responsable general.");
  if (order.areas.some((area) => !area.responsibleWorkerId)) errors.push("Asigna una persona a cada etapa.");
  if (getApiMode() !== "api") {
    const release = getReleaseReview(recipe, order.quantity || 1);
    release.issues.forEach((issue) => errors.push(issue));
  }
  return errors;
}

function productionValidationErrors(validation) {
  if (validation?.can_release) return [];
  const unavailable = (validation?.rows || []).filter((row) => !row.ok);
  if (!unavailable.length) return [t("orderResourcesUnavailable")];
  return [t("orderResourcesUnavailable"), ...unavailable.map((row) => t("orderResourceShortage")
    .replace("{resource}", row.resource_name || row.resource_code || (state.lang === "en" ? "Resource" : "Recurso"))
    .replace("{required}", formatNumber(row.required_quantity))
    .replace("{available}", formatNumber(row.available_quantity))
    .replaceAll("{unit}", row.unit || ""))];
}

function renderRemoteOrderValidation(order, validation) {
  modalContent.querySelector("#orderPreview").innerHTML=`<div class="validator-head"><div><span class="muted-label">${t("orderAuthoritativeValidation")}</span><strong>${formatNumber(order.quantity)} ${escapeHtml(order.unit)} · ${formatCurrency(validation.planned_cost)}</strong><small>${escapeHtml(validation.planned_start_date)} a ${escapeHtml(validation.planned_end_date)} · ${validation.planned_duration_days} dias productivos · minimo calculado ${validation.minimum_duration_days}</small></div><span class="chip ${validation.can_release?"active":"warning"}">${validation.can_release?t("orderReadyToRelease"):t("orderBlocked")}</span></div><div class="resource-check-grid compact">${(validation.rows||[]).map((row)=>`<article class="resource-check ${row.ok?"ok":"risk"}"><div><strong>${escapeHtml(row.resource_name)}</strong><span>${escapeHtml(row.resource_type)} · ${escapeHtml(row.source)}</span></div><p>${formatNumber(row.required_quantity)} / ${formatNumber(row.available_quantity)} ${escapeHtml(row.unit)}</p>${row.daily_allocations?.length?`<details><summary>Desglose diario</summary>${row.daily_allocations.map((day)=>`<p>${escapeHtml(day.planned_date)}: ${formatNumber(day.allocated_quantity)} asignados / ${formatNumber(day.available_quantity)} disponibles ${escapeHtml(row.unit)}</p>`).join("")}</details>`:""}</article>`).join("")}</div>`;
}

async function previewOrderForm() {
  const form = modalContent.querySelector("#orderForm");
  const order = buildOrderFromForm(form);
  const errors = validateOrder(order);
  renderFormErrors(errors);
  if (errors.length) return;
  const recipe = getApiMode() === "api" ? mockDb.findRecipe(order.recipeId) : getOrderRecipe(order);
  if (getApiMode() === "api") {
    if (!recipe?.currentVersionId) { renderFormErrors(["La validacion requiere una receta aprobada vigente."]);return; }
    try {
      const remote=await validateProductionResources({recipe_version_id:recipe.currentVersionId,quantity:order.quantity,unit:recipe.currentVersionData?.base_unit||order.unit,planned_start_date:order.plannedStartDate,planned_duration_days:order.plannedDurationDays});
      renderRemoteOrderValidation(order,remote);
      renderFormErrors(productionValidationErrors(remote));
    } catch(error) { renderFormErrors([error.message||"No se pudo validar recursos."]); }
    return;
  }
  const release = getReleaseReview(recipe, order.quantity);
  const validation = release.validation;
  modalContent.querySelector("#orderPreview").innerHTML = `
    <div class="validator-head">
      <div>
        <span class="muted-label">Vista previa de la orden</span>
        <strong>${order.quantity} ${order.unit} · ${formatCurrency(validation.totalCost)}</strong>
      </div>
      <span class="chip ${release.canRelease ? "active" : "warning"}">
        ${release.canRelease ? "Lista para liberar" : "Bloqueada"}
      </span>
    </div>
    ${release.issues.length ? `<p class="helper-copy">Pendientes: ${release.issues.join(", ")}.</p>` : ""}
    <div class="resource-check-grid compact">
      ${validation.rows
        .map((row) => `
          <article class="resource-check ${row.ok ? "ok" : "risk"}">
            <div>
              <strong>${row.name}</strong>
              <span>${row.type} · ${row.source}</span>
            </div>
            <p>${formatNumber(row.required)} / ${formatNumber(row.available)} ${row.unit}</p>
          </article>
        `)
        .join("")}
    </div>
  `;
}

function formatRecipeValidationQuantity(quantity, resourceType) {
  return formatNumber(resourceType === "Mano de obra" || resourceType === "Maquinaria" ? Number(quantity) / 60 : quantity);
}

async function saveOrderForm(event) {
  event.preventDefault();
  const order = buildOrderFromForm(event.currentTarget);
  const errors = validateOrder(order);
  renderFormErrors(errors);
  if (errors.length) return;
  if (getApiMode() === "api") {
    const recipe=mockDb.findRecipe(order.recipeId);
    if (!recipe?.currentVersionId) { renderFormErrors(["La orden requiere una version de receta aprobada vigente."]);return; }
    const currentStages=recipe.currentVersionData?.stages?.filter((stage)=>stage.status==="active")||[];
    try {
      const remote=await validateProductionResources({recipe_version_id:recipe.currentVersionId,quantity:order.quantity,unit:recipe.currentVersionData?.base_unit||order.unit,planned_start_date:order.plannedStartDate,planned_duration_days:order.plannedDurationDays});
      renderRemoteOrderValidation(order,remote);
      const availabilityErrors=productionValidationErrors(remote);
      renderFormErrors(availabilityErrors);
      if (availabilityErrors.length) return;
      const businessCode=await resolveBusinessCode("production.order",order.code,order.codeRequestKey);
      const saved=await createProductionOrder({code:businessCode,recipe_version_id:recipe.currentVersionId,quantity:order.quantity,unit:recipe.currentVersionData?.base_unit||order.unit,planned_start_date:order.plannedStartDate,planned_duration_days:order.plannedDurationDays,planned_start_at:new Date(`${order.plannedStartDate}T08:00:00`).toISOString(),required_at:order.dueDate?new Date(`${order.dueDate}T23:59:59`).toISOString():null,priority:({Alta:"high",Media:"medium",Baja:"low"})[order.priority]||"medium",responsible_worker_id:order.responsibleWorkerId,stage_assignments:currentStages.map((stage,index)=>({recipe_stage_id:stage.id,responsible_worker_id:order.areas[index]?.responsibleWorkerId})),source_type:"manual"});
      localStorage.setItem("erclave-selected-recipe",order.recipeId);localStorage.setItem("erclave-validation-qty",order.quantity);closeModal();await loadProductionApiData();showToast(`Orden ${saved.code} generada en Production API.`);openOrderPrintModal(saved.id);
    } catch(error) { renderFormErrors([error?.payload?.error?.code==="resources_unavailable"?t("orderResourcesChanged"):(error.message||"No se pudo generar la orden.")]); }
    return;
  }
  mockDb.addOrder(order);
  localStorage.setItem("erclave-selected-recipe", order.recipeId);
  localStorage.setItem("erclave-validation-qty", order.quantity);
  closeModal();
  render();
  showToast(`Orden ${order.id} generada en produccion.`);
  openOrderPrintModal(order.id);
}

async function changeOrderStatus(orderId, status) {
  const order = mockDb.findOrder(orderId);
  if (!order || !orderStatusCatalog.includes(status)) return;
  if (getApiMode() === "api") {
    if(!hasPermission(productionOrderTransitionPermission(order.status,status)))return;
    try { await updateProductionOrderStatus(orderId,{status:toApiOrderStatus(status),reason:"Cambio operativo desde la orden"});await loadProductionApiData();showToast(status==="En produccion"?t("orderMaterialIssueRegistered",{code:order.code||order.id}):`Orden ${order.id} ahora esta en ${status}.`); }
    catch(error){
      const code=error?.payload?.error?.code;
      const messages={material_consumption_required:t("orderMaterialIssueFailed"),production_stages_incomplete:t("orderStagesIncomplete"),invalid_order_transition:t("orderInvalidTransition")};
      showApiError(error,messages[code]||t("orderInvalidTransition"));
      render();
    }
    return;
  }
  mockDb.updateOrder({ ...order, status });
  render();
  showToast(`Orden ${order.id} ahora esta en ${status}.`);
}

function advanceOrderStage(orderId, stageIndex) {
  const order = mockDb.findOrder(orderId);
  if (!order || !order.areas?.[stageIndex]) return;
  const stage=order.areas[stageIndex];
  if(["Terminada","Omitida"].includes(stage.status)){showToast(t("orderStageTerminal"));return;}
  modalContent.innerHTML=`
    <form class="recipe-form" data-form="order-stage-progress" data-order-id="${escapeAttribute(orderId)}" data-stage-index="${stageIndex}">
      <div class="modal-head"><div><p class="eyebrow">${t("production")}</p><h2>${t("orderStageProgressTitle")}</h2></div><button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button></div>
      <p class="helper-copy"><strong>${escapeHtml(stage.area)}</strong> · ${t("orderStageProgressHelp")}</p>
      <label class="full-field"><span>${t("orderStageProgressLabel")}</span><input name="progressPercent" type="number" min="0" max="100" step="1" value="${escapeAttribute(String(Number(stage.progress||0)))}" required><small>${t("orderStageProgressScale")}</small></label>
      <div class="modal-actions"><button class="secondary-action" type="button" data-action="cancel-stage-progress">${t("cancel")}</button><button class="primary-action" type="submit">${t("orderStageProgressSave")}</button></div>
    </form>`;
  modalBackdrop.hidden=false;
  modalContent.querySelector(".modal-close").addEventListener("click",closeModal);
  modalContent.querySelector("[data-action='cancel-stage-progress']").addEventListener("click",closeModal);
  modalContent.querySelector("[data-form='order-stage-progress']").addEventListener("submit",saveOrderStageProgressForm);
  modalContent.querySelector("[name='progressPercent']").focus();
}

async function saveOrderStageProgressForm(event){
  event.preventDefault();
  const form=event.currentTarget;const order=mockDb.findOrder(form.dataset.orderId);const stageIndex=Number(form.dataset.stageIndex);const stage=order?.areas?.[stageIndex];
  if(!order||!stage)return;
  const progress=Number(new FormData(form).get("progressPercent"));
  if(!Number.isFinite(progress)||progress<0||progress>100){showToast(t("orderStageProgressInvalid"));return;}
  const status=progress===100?"completed":progress===0?"pending":"in_progress";
  if(getApiMode()==="api"){
    if(!hasPermission(productionStagePermission(status)))return;
    try{
      if(progress>0&&order.status!=="En produccion"){
        if(!hasPermission(productionOrderTransitionPermission(order.status,"En produccion")))return;
        await updateProductionOrderStatus(order.id,{status:"in_progress",reason:"Actualizacion de avance por etapa"});
      }
      await updateProductionOrderStage(stage.id,{status,progress_percent:progress,notes:"Porcentaje de avance registrado desde Produccion"});
      closeModal();await loadProductionApiData();showToast(t("orderStageProgressUpdated",{stage:stage.area,progress:formatNumber(progress)}));
    }catch(error){showToast(error?.payload?.error?.code==="material_consumption_required"?t("orderMaterialIssueFailed"):(error.message||t("orderStageProgressSaveError")));}
    return;
  }
  const stages=order.areas.map((item,index)=>index===stageIndex?{...item,status:progress===100?"Terminada":progress===0?"Pendiente":"En proceso",progress}:item);
  const allDone=stages.every((item)=>item.status==="Terminada");
  mockDb.updateOrder({...order,areas:stages,status:allDone?"En validacion":progress>0?"En produccion":order.status});closeModal();render();showToast(t("orderStageProgressUpdated",{stage:stage.area,progress:formatNumber(progress)}));
}

function getDocumentBranding(){const value=state.adminApi.data?.documentTemplate||{};return {logo:value.logo_data_url||"",primary:value.primary_color||"#6106A0",accent:value.accent_color||"#F557D3",text:value.text_color||"#190F34",footer:value.footer_text||"",showPage:value.show_page_number!==false,company:state.adminApi.data?.tenant?.commercial_name||"ERClave"};}
function renderDocumentBrandingHeader(moduleLabel){const brand=getDocumentBranding();return `<div>${brand.logo?`<img class="print-company-logo" src="${escapeAttribute(brand.logo)}" alt="${escapeAttribute(brand.company)}">`:`<strong>${escapeHtml(brand.company)}</strong>`}<span>${escapeHtml(moduleLabel)}</span></div>`;}
function renderDocumentBrandingFooter(){const brand=getDocumentBranding();return brand.footer||brand.showPage?`<footer class="print-document-footer">${escapeHtml(brand.footer)}${brand.showPage?`<span>${state.lang==="en"?"Page":"Página"} <span class="print-page-number"></span></span>`:""}</footer>`:"";}

async function openOrderPrintModal(orderId) {
  let order = mockDb.findOrder(orderId);
  if (!order && getApiMode()==="api") { await loadProductionApiData(); order=mockDb.findOrder(orderId); }
  if (!order) { showToast(t("documentRecordUnavailable")); return; }
  const recipe = getOrderRecipe(order);
  const validation = calculateRecipe(recipe, order.quantity);
  const cost = getOrderCostSnapshot(order, recipe);
  modalContent.innerHTML = `
    <div class="recipe-form print-modal">
      <div class="modal-head no-print">
        <div>
          <p class="eyebrow">Orden de produccion</p>
          <h2>${order.id}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <section class="print-area" id="printArea" style="--document-primary:${getDocumentBranding().primary};--document-accent:${getDocumentBranding().accent};--document-text:${getDocumentBranding().text}">
        <div class="print-header">
          ${renderDocumentBrandingHeader("Producción · Orden de producción")}
          <h1>${escapeHtml(order.code||order.id)}</h1>
        </div>
        <div class="print-grid">
          <p><strong>Producto:</strong> ${escapeHtml(order.recipeName)}</p>
          <p><strong>Receta:</strong> ${escapeHtml(formatRecipeDisplayLabel(recipe))} · v${escapeHtml(recipe.version)}</p>
          <p><strong>Cantidad:</strong> ${formatNumber(order.quantity)} ${escapeHtml(order.unit)}</p>
          <p><strong>Estado:</strong> ${escapeHtml(order.status)}</p>
          <p><strong>Prioridad:</strong> ${escapeHtml(order.priority)}</p>
          <p><strong>Fecha requerida:</strong> ${escapeHtml(order.dueDate)}</p>
          <p><strong>Responsable:</strong> ${escapeHtml(order.responsible)}</p>
          <p><strong>Centro:</strong> ${escapeHtml(order.center)}</p>
          <p><strong>Costo planeado:</strong> ${formatCurrency(cost.plannedCost)}</p>
          <p><strong>Costo real:</strong> ${cost.actualCost == null ? "Pendiente de cierre" : formatCurrency(cost.actualCost)}</p>
        </div>
        ${(order.resources||[]).length?`<h3>Consumo y costo por recurso</h3>
        <table><thead><tr><th>Recurso</th><th>Tipo</th><th>Planeado</th><th>Real</th><th>Costo real</th></tr></thead><tbody>
          ${(order.resources||[]).map((resource)=>`<tr><td>${escapeHtml(resource.name)}</td><td>${escapeHtml(resource.type)}</td><td>${formatNumber(resource.plannedQuantity)} ${escapeHtml(resource.unit)}</td><td>${resource.type==="material"?(resource.actualQuantity==null?"Pendiente":`${formatNumber(resource.actualQuantity)} ${escapeHtml(resource.unit)}`):t("orderTimeMeasurementDeferred")}</td><td>${resource.actualCost==null?"Pendiente":formatCurrency(resource.actualCost)}</td></tr>`).join("")}
        </tbody></table>`:""}
        <h3>Seguimiento por etapa operativa</h3>
        <table>
          <thead>
            <tr><th>Etapa</th><th>Responsable</th><th>Estado</th><th>Avance</th></tr>
          </thead>
          <tbody>
            ${order.areas.map((area) => `<tr><td>${escapeHtml(area.area)}</td><td>${escapeHtml(area.responsible)}</td><td>${escapeHtml(area.status)}</td><td>${formatNumber(area.progress || (area.status === "Terminada" ? 100 : 0))}%</td></tr>`).join("")}
          </tbody>
        </table>
        <h3>Recursos calculados</h3>
        <table>
          <thead>
            <tr><th>Recurso</th><th>Tipo</th><th>Requerido</th><th>Disponible</th></tr>
          </thead>
          <tbody>
            ${validation.rows.map((row) => `<tr><td>${escapeHtml(row.name)}</td><td>${escapeHtml(row.type)}</td><td>${formatNumber(row.required)} ${escapeHtml(row.unit)}</td><td>${formatNumber(row.available)} ${escapeHtml(row.unit)}</td></tr>`).join("")}
          </tbody>
        </table>
        <p class="print-total"><strong>Costo estimado:</strong> ${formatCurrency(validation.totalCost)}</p>
        ${renderDocumentBrandingFooter()}
      </section>

      <div class="modal-actions no-print">
        <button class="secondary-action" type="button" data-action="print-order-now">Imprimir / Guardar PDF</button>
        <button class="primary-action" type="button" data-action="close-print">Cerrar</button>
      </div>
    </div>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-print']").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='print-order-now']").addEventListener("click", () => {
    window.print();
  });
}

async function openSalesQuotePrintModal(quoteId) {
  let quote = mockDb.findModuleRecord("ventas", quoteId);
  if (!quote && getApiMode()==="api") { await loadSalesApiData(); quote=mockDb.findModuleRecord("ventas",quoteId); }
  if (!quote) { showToast(t("documentRecordUnavailable")); return; }
  const customer = quote.fields?.customerId ? mockDb.findModuleRecord("ventas", quote.fields.customerId) : null;
  const lines = getQuoteLines(quote);
  modalContent.innerHTML = `
    <div class="recipe-form print-modal">
      <div class="modal-head no-print">
        <div>
          <p class="eyebrow">${t("newQuote")}</p>
          <h2>${escapeHtml(quote.code)}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <section class="print-area" id="printArea" style="--document-primary:${getDocumentBranding().primary};--document-accent:${getDocumentBranding().accent};--document-text:${getDocumentBranding().text}">
        <div class="print-header">
          ${renderDocumentBrandingHeader(`${state.lang==="en"?"Sales":"Ventas"} · ${t("quoteDocument")}`)}
          <h1>${escapeHtml(quote.code)}</h1>
        </div>
        <div class="print-grid">
          <p><strong>${t("customer")}:</strong> ${escapeHtml(quote.fields?.customerName || t("notDefined"))}</p>
          <p><strong>${t("status")}:</strong> ${escapeHtml(translateStatus(quote.status))}</p>
          <p><strong>${t("validUntil")}:</strong> ${escapeHtml(quote.fields?.validUntil || t("notDefined"))}</p>
          <p><strong>${t("deliveryPromise")}:</strong> ${escapeHtml(quote.fields?.deliveryPromise || t("notDefined"))}</p>
          <p><strong>${t("paymentTerms")}:</strong> ${escapeHtml(quote.fields?.paymentTerms || t("notDefined"))}</p>
          <p><strong>${t("currency")}:</strong> ${escapeHtml(quote.fields?.currency || "MXN")}</p>
          <p><strong>${t("billingLegalName")}:</strong> ${escapeHtml(customer?.fields?.billingLegalName || t("notDefined"))}</p>
          <p><strong>${t("taxId")}:</strong> ${escapeHtml(customer?.fields?.taxId || t("notDefined"))}</p>
        </div>
        <h3>${t("quoteLines")}</h3>
        <table>
          <thead>
            <tr>
              <th>${t("productOrService")}</th>
              <th>${t("quantity")}</th>
              <th>${t("unitPrice")}</th>
              <th>${t("discount")}</th>
              <th>${t("quoteTotal")}</th>
            </tr>
          </thead>
          <tbody>
            ${lines.map((line) => `
              <tr>
                <td>${escapeHtml(line.productServiceName)}</td>
                <td>${formatNumber(line.quantity)} ${escapeHtml(line.unit)}</td>
                <td>${formatSalesMoney(line.unitPrice,quote.fields?.currency)}</td>
                <td>${formatNumber(Number(line.discount || 0))}%</td>
                <td>${formatSalesMoney(line.total,quote.fields?.currency)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
        ${quote.fields?.notes ? `<p><strong>${t("notes")}:</strong> ${escapeHtml(quote.fields.notes)}</p>` : ""}
        <p class="print-total"><strong>${t("quoteSubtotal")}:</strong> ${formatSalesMoney(quote.fields?.subtotal,quote.fields?.currency)}</p>
        <p class="print-total"><strong>${t("quoteTotal")}:</strong> ${formatSalesMoney(quote.fields?.total,quote.fields?.currency)}</p>
        ${renderDocumentBrandingFooter()}
      </section>

      <div class="modal-actions no-print">
        <button class="secondary-action" type="button" data-action="print-quote-now">${t("printSavePdf")}</button>
        <button class="primary-action" type="button" data-action="close-print">${t("close")}</button>
      </div>
    </div>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-print']").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='print-quote-now']").addEventListener("click", () => {
    window.print();
  });
}

function applyI18n() {
  const dict = translations[state.lang];
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = dict[node.dataset.i18n] || node.textContent;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = dict[node.dataset.i18nPlaceholder] || node.placeholder;
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
    node.setAttribute("aria-label", dict[node.dataset.i18nAriaLabel] || node.getAttribute("aria-label") || "");
  });
  document.querySelectorAll("[data-i18n-title]").forEach((node) => {
    node.title = dict[node.dataset.i18nTitle] || node.title;
  });
  langToggle.querySelector(".icon").textContent = state.lang.toUpperCase();
}

function renderAuthControls() {
  if (!authButton) return;
  const enabled = isFirebaseAuthConfigured();
  authButton.hidden = !enabled;
  if (!enabled) return;
  authButton.hidden = !state.auth.user;
  authButton.disabled = state.auth.status === "loading";
  authButton.textContent = t("signOut");
  authButton.title = state.auth.user ? t("signOutUser", { email: state.auth.user.email }) : t("signOut");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeAttribute(value) {
  return escapeHtml(value)
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#39;");
}

function getAuthErrorMessage(error, fallback) {
  return userFacingError(error, fallback);
}

function getPasswordResetNotice(email) {
  return state.lang === "en"
    ? `If an account exists for ${email}, we will send password reset instructions.`
    : `Si existe una cuenta para ${email}, enviaremos instrucciones para restablecer tu contraseña.`;
}

function shouldTreatPasswordResetAsSent(error) {
  return ["auth/user-not-found"].includes(error?.code || "");
}

function renderAuthGate() {
  if (!authGate) return;
  const shouldShow = isAuthRequired() && !state.auth.user;
  authGate.hidden = !shouldShow;
  if (!shouldShow) {
    authGate.innerHTML = "";
    return;
  }
  const isLoading = state.auth.status === "loading";
  const authEmail = escapeAttribute(state.auth.email);
  authGate.innerHTML = `
    <section class="auth-screen" aria-labelledby="authGateTitle">
      <div class="auth-brand-panel">
        <div class="auth-logo-slot">
          <div class="brand-mark">ER</div>
          <div>
            <strong>ERClave</strong>
            <span>Gestion empresarial modular</span>
          </div>
        </div>
        <div class="auth-copy">
          <p class="eyebrow">Plataforma ERClave</p>
          <h1>Tu operacion, clara y conectada.</h1>
          <p>ERClave centraliza procesos, usuarios, sucursales y modulos de negocio en una plataforma SaaS preparada para crecer con cada empresa.</p>
        </div>
        <div class="auth-logo-row" aria-label="Espacio para logos de clientes o partners">
          <span>Logo cliente</span>
          <span>Partner</span>
          <span>QA</span>
        </div>
      </div>
      <div class="auth-card" role="dialog" aria-modal="true" aria-labelledby="authGateTitle">
        <p class="eyebrow">ERClave QA</p>
        <h2 id="authGateTitle">Iniciar sesion</h2>
        <p>Usa el correo autorizado por tu organizacion.</p>
        ${state.auth.error ? `<div class="form-errors" role="alert"><p>${escapeHtml(state.auth.error)}</p></div>` : ""}
        ${state.auth.notice ? `<div class="form-notice" role="status"><p>${escapeHtml(state.auth.notice)}</p></div>` : ""}
        <form class="auth-form" data-form="auth-email">
          <label>
            <span>Correo electronico</span>
            <input type="email" name="email" autocomplete="email" placeholder="nombre@empresa.com" value="${authEmail}" required ${isLoading ? "disabled" : ""}>
          </label>
          <label>
            <span>Contrasena</span>
            <input type="password" name="password" autocomplete="current-password" required ${isLoading ? "disabled" : ""}>
          </label>
          <button class="primary-action full" type="submit" ${isLoading ? "disabled" : ""}>
            ${isLoading ? "Validando..." : "Entrar"}
          </button>
        </form>
        <button class="link-action" type="button" data-action="auth-reset-password" ${isLoading ? "disabled" : ""}>
          Recuperar contrasena
        </button>
        <p class="auth-legal">El acceso queda sujeto a la membresia activa del tenant y a los permisos asignados por tu administrador.</p>
      </div>
    </section>
  `;
  authGate.querySelector("[data-form='auth-email']").addEventListener("submit", handleEmailAuthSubmit);
  authGate.querySelector("[data-action='auth-reset-password']").addEventListener("click", handlePasswordReset);
}

function handleEmailAuthSubmit(event) {
  event.preventDefault();
  if (!isFirebaseAuthConfigured() || state.auth.status === "loading") return;
  const formData = new FormData(event.currentTarget);
  const email = String(formData.get("email") || "").trim().toLowerCase();
  const password = String(formData.get("password") || "");
  if (!email || !password) {
    state.auth = { ...state.auth, status: "error", email, error: state.lang === "en" ? "Email and password are required." : "Correo y contraseña son requeridos.", notice: "" };
    render();
    return;
  }
  state.auth = { ...state.auth, status: "loading", email, error: "", notice: "" };
  render();
  signInWithEmail(email, password).catch((error) => {
    state.auth = {
      status: "error",
      user: null,
      email,
      error: getAuthErrorMessage(error, state.lang === "en" ? "Sign-in failed." : "No se pudo iniciar sesión con correo."),
      notice: ""
    };
    render();
  });
}

function handlePasswordReset() {
  if (!isFirebaseAuthConfigured() || state.auth.status === "loading") return;
  const emailInput = authGate.querySelector("[name='email']");
  const email = String(emailInput?.value || "").trim().toLowerCase();
  if (!email) {
    state.auth = { ...state.auth, status: "error", email, error: state.lang === "en" ? "Enter your email to reset your password." : "Escribe tu correo para recuperar la contraseña.", notice: "" };
    render();
    return;
  }
  state.auth = { ...state.auth, status: "loading", email, error: "", notice: "" };
  render();
  sendPasswordReset(email)
    .then(() => {
      state.auth = {
        status: "signed_out",
        user: null,
        email,
        error: "",
        notice: getPasswordResetNotice(email)
      };
      render();
    })
    .catch((error) => {
      if (shouldTreatPasswordResetAsSent(error)) {
        state.auth = { status: "signed_out", user: null, email, error: "", notice: getPasswordResetNotice(email) };
      } else {
        state.auth = {
          status: "error",
          user: null,
          email,
          error: getAuthErrorMessage(error, state.lang === "en" ? "The password reset email could not be sent." : "No se pudo enviar la recuperación."),
          notice: ""
        };
      }
      render();
    });
}

function handleAuthButton() {
  if (!isFirebaseAuthConfigured() || state.auth.status === "loading") return;
  if (state.auth.user) {
    signOutUser().catch((error) => {
      state.auth = { ...state.auth, error: userFacingError(error, state.lang === "en" ? "Sign-out failed." : "No se pudo cerrar sesión.") };
      render();
    });
  }
}

function initializeAuth() {
  if (!isFirebaseAuthConfigured()) return;
  onAuthChanged((user) => {
    state.auth = {
      status: user ? "ready" : "signed_out",
      user: user ? { email: user.email, displayName: user.displayName } : null,
      email: user?.email || state.auth.email || "",
      error: "",
      notice: ""
    };
    state.adminApi = { status: "idle", data: null, error: "" };
    state.sessionApi = { status: "idle", data: null, error: "" };
    state.tenantResolution = { status: "idle", tenants: [], error: "" };
    if (user) {
      applyScreenSnapshot({ active: "administracion", activeSubmodule: null, laborArea: "" });
    }
    render();
  }).catch((error) => {
    state.auth = {
      status: "error",
      user: null,
      email: state.auth.email || "",
      error: getAuthErrorMessage(error, "Firebase Auth no disponible."),
      notice: ""
    };
    render();
  });
}

function render() {
  shell.dataset.theme = state.theme;
  shell.classList.toggle("admin-focus", state.active === "administracion");
  document.body.dataset.theme = state.theme;
  backButton.disabled = !state.history.length;
  adminShortcut.classList.toggle("active", state.active === "administracion");
  const isReadOnlySalesMargin = state.active === "ventas" && state.activeSubmodule === "margen";
  topbarPrimary.hidden = !state.activeSubmodule || isReadOnlySalesMargin;
  topbarPrimary.querySelector("[data-i18n]").dataset.i18n = state.active === "produccion" ? "newOrder" : "newModuleRecord";
  renderNav();
  renderStatusStrip();
  renderPanel();
  renderFlow();
  renderContextBar();
  renderAuthControls();
  renderAuthGate();
  applyI18n();
  ensureSessionContext();
  loadUnitCatalog();
}

backButton.addEventListener("click", goBack);

themeToggle.addEventListener("click", () => {
  state.theme = state.theme === "light" ? "dark" : "light";
  localStorage.setItem("erclave-theme", state.theme);
  render();
});

langToggle.addEventListener("click", () => {
  state.lang = state.lang === "es" ? "en" : "es";
  localStorage.setItem("erclave-lang", state.lang);
  render();
});

adminShortcut.addEventListener("click", () => {
  navigateTo({ active: "administracion", activeSubmodule: null, laborArea: "" });
});

modalBackdrop.addEventListener("click", (event) => {
  if (event.target === modalBackdrop) closeModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modalBackdrop.hidden) closeModal();
});

topbarPrimary.addEventListener("click", () => {
  if (!state.activeSubmodule) return;
  if (state.active === "ventas" && state.activeSubmodule === "margen") return;
  if (state.active === "produccion") {
    openOrderModal();
    return;
  }
  openGenericRecordModal(state.active, state.activeSubmodule);
});

authButton?.addEventListener("click", handleAuthButton);

initializeAuth();
render();
