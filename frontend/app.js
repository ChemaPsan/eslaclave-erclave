import { modules, erpSubmoduleCatalog } from "./data/modules.js";
import { defaultRecipes } from "./data/resources.js";
import { mockDb } from "./data/mockDb.js";
import { translations } from "./i18n/translations.js";
import {
  calculateRecipe,
  getOrderCostSnapshot,
  getOrderProgress,
  getProductionModuleData,
  getRecipeApprovalStatus,
  getRecipeStandardCost,
  getRecipeResourceCatalog,
  getReleaseReview,
  getResource,
  isRecipeApproved
} from "./utils/production.js";
import { diffDays, formatCurrency, formatNumber, startOfDay } from "./utils/format.js";

const state = {
  active: modules[0].id,
  activeSubmodule: null,
  history: [],
  theme: localStorage.getItem("erclave-theme") || "light",
  lang: localStorage.getItem("erclave-lang") || "es"
};

const orderStatusCatalog = ["Liberada", "En espera de recursos", "En produccion", "Pausada", "En validacion", "Terminada", "Cancelada"];
const mvpModuleIds = ["produccion", "almacenes", "ventas"];

const shell = document.querySelector(".app-shell");
const moduleNav = document.getElementById("moduleNav");
const modulePanel = document.getElementById("modulePanel");
const flowList = document.getElementById("flowList");
const notificationSummary = document.getElementById("notificationSummary");
const backButton = document.getElementById("backButton");
const themeToggle = document.getElementById("themeToggle");
const langToggle = document.getElementById("langToggle");
const topbarPrimary = document.querySelector(".topbar .primary-action");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalContent = document.getElementById("modalContent");
const toast = document.getElementById("toast");

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
  return [...modules].sort((a, b) => {
    const aMvpIndex = mvpModuleIds.indexOf(a.id);
    const bMvpIndex = mvpModuleIds.indexOf(b.id);
    const aOrder = aMvpIndex >= 0 ? aMvpIndex : mvpModuleIds.length + modules.findIndex((module) => module.id === a.id);
    const bOrder = bMvpIndex >= 0 ? bMvpIndex : mvpModuleIds.length + modules.findIndex((module) => module.id === b.id);
    return aOrder - bOrder;
  });
}

function renderNav() {
  moduleNav.innerHTML = getNavigationModules()
    .map((module) => {
      const label = state.lang === "en" ? module.titleEn : module.title;
      const isMvpModule = mvpModuleIds.includes(module.id);
      return `
        <div class="nav-group ${module.id === state.active ? "open" : ""} ${isMvpModule ? "" : "coming-soon"}" ${isMvpModule ? "" : `data-tooltip="${t("comingSoon")}"`}>
          <button class="nav-button ${module.id === state.active && !state.activeSubmodule ? "active" : ""} ${isMvpModule ? "" : "disabled-module"}" type="button" data-module-root="${module.id}" title="${isMvpModule ? label : t("comingSoon")}" aria-disabled="${isMvpModule ? "false" : "true"}">
            <span class="nav-icon">${module.icon}</span>
            <span>${label}</span>
            <small class="nav-count">${module.count}</small>
          </button>
          ${renderSubnav(module)}
        </div>
      `;
    })
    .join("");

  moduleNav.querySelectorAll("[data-module-root]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!mvpModuleIds.includes(button.dataset.moduleRoot)) return;
      navigateTo({ active: button.dataset.moduleRoot, activeSubmodule: null, laborArea: "" });
    });
  });

  moduleNav.querySelectorAll("[data-submodule-nav]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!mvpModuleIds.includes(button.dataset.module)) return;
      navigateTo({ active: button.dataset.module, activeSubmodule: button.dataset.submoduleNav, laborArea: "" });
    });
  });
}

function renderSubnav(module) {
  if (!mvpModuleIds.includes(module.id)) return "";
  return `
    <div class="submodule-nav" aria-label="Submodulos de ${module.title}">
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

function renderPanel() {
  const module = { ...(modules.find((item) => item.id === state.active) || modules[0]) };
  if (module.id === "produccion") {
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
  } else if (state.activeSubmodule) {
    renderGenericSubmodulePanel(module);
    return;
  }
  if (module.id !== "produccion") {
    const savedRows = getSavedModuleTableRows(module);
    const savedRecords = getSavedModuleRecordRows(module);
    module.table = { ...module.table, rows: [...savedRows, ...(module.table.rows || [])] };
    if (module.tableEn) module.tableEn = { ...module.tableEn, rows: [...savedRows, ...(module.tableEn.rows || [])] };
    module.records = [...savedRecords, ...(module.records || [])];
    if (module.recordsEn) module.recordsEn = [...savedRecords, ...(module.recordsEn || [])];
  }
  const label = state.lang === "en" ? module.titleEn : module.title;
  const moduleEyebrow = getModuleField(module, "eyebrow");
  const moduleStatus = getModuleField(module, "status");
  const moduleSummary = getModuleField(module, "summary");
  const modulePrimary = getModuleField(module, "primary");
  const moduleKpis = getModuleField(module, "kpis") || [];
  const moduleWorkflow = getModuleField(module, "workflow") || [];
  const moduleValidations = getModuleField(module, "validations") || [];
  const moduleForm = getModuleField(module, "form") || [];
  const moduleRecords = getModuleField(module, "records") || [];
  const moduleTable = getModuleTable(module);

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${moduleEyebrow}</p>
        <h2>${label}</h2>
      </div>
      <span class="chip active">${moduleStatus}</span>
    </div>

    <div class="module-summary expanded">
      <div class="module-hero">
        <h1>${label}</h1>
        <p>${moduleSummary}</p>
        <button class="primary-action hero-action" type="button" data-action="${module.id === "produccion" ? "open-order" : "module-primary"}">
          <span>＋</span>
          <span>${modulePrimary}</span>
        </button>
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

    <div class="module-section-grid">
      <section class="section-card wide">
        <div class="section-title">
          <span class="section-icon">▦</span>
          <strong>${t("submodulesLabel")}</strong>
        </div>
        <div class="submodule-grid">
          ${module.submodules
            .map(([name, detail, id]) => {
              const submoduleId = id || slugify(name);
              const copy = getSubmoduleCopy(module.id, submoduleId, name, detail);
              return `
                <button class="submodule-card" type="button" data-module="${module.id}" data-submodule="${submoduleId}">
                  <strong>${copy.name}</strong>
                  <p>${copy.detail}</p>
                </button>
              `;
            })
            .join("")}
        </div>
      </section>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">↳</span>
          <strong>${t("operatingFlow")}</strong>
        </div>
        <ol class="workflow-list">
          ${moduleWorkflow.map((step) => `<li>${step}</li>`).join("")}
        </ol>
      </section>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">✓</span>
          <strong>${t("compatibility")}</strong>
        </div>
        <div class="compat-list">
          ${moduleValidations
            .map(
              ([name, detail]) => `
                <article>
                  <strong>${name}</strong>
                  <p>${detail}</p>
                </article>
              `
            )
            .join("")}
        </div>
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
            ${moduleTable.columns.map((column) => `<span role="columnheader">${column}</span>`).join("")}
          </div>
          ${moduleTable.rows
            .map(
              (row) => `
                <div class="table-row" role="row">
                  ${row.map((cell) => `<span role="cell">${cell}</span>`).join("")}
                </div>
              `
            )
            .join("")}
        </div>
      </section>

      <section class="section-card form-preview">
        <div class="section-title">
          <span class="section-icon">✎</span>
          <strong>${t("quickCapture")}</strong>
        </div>
        ${moduleForm
          .map(
            ([labelText, value]) => `
              <label class="preview-field">
                <span>${labelText}</span>
                <input type="text" value="${value}" readonly />
              </label>
            `
          )
          .join("")}
        <button class="secondary-action full" type="button" data-action="${module.id === "produccion" ? "open-recipe" : "module-primary"}">${module.id === "produccion" ? t("newRecipe") : t("openForm")}</button>
      </section>
    </div>

    ${module.id === "produccion" ? renderRecipeValidationCard() : ""}

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

  bindProductionPanelActions();
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
  const movements = mockDb.loadModuleRecords(module.id, submodule.id).filter((record) => record.recordType === "inventoryMovement");

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

function renderWarehouseStockPanel(module, submodule) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const warehouseFilter = localStorage.getItem("erclave-stock-warehouse") || "all";
  const search = localStorage.getItem("erclave-stock-search") || "";
  const warehouses = mockDb.loadModuleRecords(module.id, "almacenes").filter((record) => record.recordType === "warehouse");
  const movements = mockDb.loadModuleRecords(module.id, "movimientos").filter((record) => record.recordType === "inventoryMovement");
  const stockRows = filterStockBalances(buildStockBalances(movements), warehouseFilter, search);

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
          <span>${t("calculatedStock")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getWarehouseFlowTitle(submodule), getWarehouseFlowSteps(submodule))}
        <p class="helper-copy">${t("stockHelper")}</p>
        <div class="catalog-toolbar kardex-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="stockSearch" type="search" value="${search}" placeholder="${t("searchStock")}" />
          </label>
          <label class="preview-field compact-filter">
            <span>${t("warehouse")}</span>
            <select id="stockWarehouseFilter">
              <option value="all">${t("allWarehouses")}</option>
              ${warehouses.map((warehouse) => `<option value="${warehouse.id}" ${selectedOption(warehouseFilter, warehouse.id)}>${warehouse.code} - ${warehouse.title}</option>`).join("")}
            </select>
          </label>
        </div>
        <div class="data-table kardex-table" role="table">
          <div class="table-row table-head" role="row">
            <span role="columnheader">${t("item")}</span>
            <span role="columnheader">${t("warehouse")}</span>
            <span role="columnheader">${t("entries")}</span>
            <span role="columnheader">${t("issues")}</span>
            <span role="columnheader">${t("balance")}</span>
            <span role="columnheader">${t("lastMovement")}</span>
            <span role="columnheader">${t("status")}</span>
          </div>
          ${stockRows.length ? stockRows.map(renderStockRow).join("") : renderStockEmptyRow(Boolean(movements.length))}
        </div>
      </section>
    </section>
  `;

  modulePanel.querySelector("[data-action='back-module']").addEventListener("click", () => {
    navigateTo({ active: state.active, activeSubmodule: null, laborArea: "" });
  });
  modulePanel.querySelector("#stockWarehouseFilter").addEventListener("change", (event) => {
    localStorage.setItem("erclave-stock-warehouse", event.target.value);
    render();
  });
  const stockSearch = modulePanel.querySelector("#stockSearch");
  stockSearch.addEventListener("input", (event) => {
    localStorage.setItem("erclave-stock-search", event.target.value);
    render();
    const nextSearch = modulePanel.querySelector("#stockSearch");
    if (nextSearch) {
      nextSearch.focus();
      nextSearch.setSelectionRange(nextSearch.value.length, nextSearch.value.length);
    }
  });
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
            <select id="kardexItemFilter">
              <option value="all">${t("allItems")}</option>
              ${items.map((item) => `<option value="${item.id}" ${selectedOption(itemFilter, item.id)}>${item.code} - ${item.title}</option>`).join("")}
            </select>
          </label>
          <label class="preview-field compact-filter">
            <span>${t("warehouse")}</span>
            <select id="kardexWarehouseFilter">
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
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newCustomer")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesCustomerSearch" type="search" value="${search}" placeholder="${t("searchCustomers")}" />
          </label>
        </div>
        <p class="helper-copy">${t("customerCatalogHelper")}</p>
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
        <span class="muted-label">${record.code} - ${translateCustomerType(record.fields?.customerType)}</span>
        <strong>${record.title}</strong>
        <p>${t("billingProfile")}: ${record.fields?.billingLegalName || t("notDefined")} - ${record.fields?.taxId || t("notDefined")}</p>
        <span class="muted-label">${t("contact")}: ${record.fields?.contactName || t("notDefined")} · ${record.fields?.contactPhone || t("notDefined")}</span>
        <span class="muted-label">${t("commercialEmail")}: ${record.fields?.contactEmail || t("notDefined")}</span>
        <span class="muted-label">${t("paymentTerms")}: ${record.fields?.paymentTerms || t("notDefined")} · ${t("creditLimit")}: ${record.fields?.creditLimit || t("notDefined")}</span>
        <span class="muted-label">${t("billingEmail")}: ${record.fields?.billingEmail || t("notDefined")}</span>
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Activo" ? "active" : record.status === "Bloqueado" ? "warning" : ""}">${translateStatus(record.status)}</span>
        <button class="secondary-action small-action" type="button" data-action="edit-sales-customer" data-record-id="${record.id}">${t("edit")}</button>
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
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newQuote")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesQuoteSearch" type="search" value="${search}" placeholder="${t("searchQuotes")}" />
          </label>
        </div>
        <p class="helper-copy">${t("quoteCatalogHelper")}</p>
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
        <span class="muted-label">${record.code} - ${record.fields?.validUntil || t("notDefined")} - ${getQuoteLines(record).length} ${t("quoteLines")}</span>
        <strong>${record.title}</strong>
        <p>${getQuoteLines(record).map((line) => line.productServiceName).filter(Boolean).slice(0, 2).join(" / ") || t("notDefined")}</p>
        <span class="muted-label">${t("customer")}: ${record.fields?.customerName || t("notDefined")}</span>
        <span class="muted-label">${t("quoteSubtotal")}: ${formatCurrency(Number(record.fields?.subtotal || 0))}</span>
        <span class="muted-label">${t("quoteTotal")}: ${formatCurrency(Number(record.fields?.total || 0))}</span>
        <span class="muted-label">${t("paymentTerms")}: ${record.fields?.paymentTerms || t("notDefined")}</span>
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Aprobado" ? "active" : record.status === "Vencida" ? "warning" : ""}">${translateStatus(record.status)}</span>
        ${record.status === "Aprobado" ? `<button class="secondary-action small-action" type="button" data-action="create-sales-order" data-record-id="${record.id}">${t("createOrder")}</button>` : ""}
        <button class="secondary-action small-action" type="button" data-action="print-sales-quote" data-record-id="${record.id}">${t("quotePdf")}</button>
        <button class="secondary-action small-action" type="button" data-action="edit-sales-quote" data-record-id="${record.id}">${t("edit")}</button>
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
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("newSalesOrder")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesOrderSearch" type="search" value="${search}" placeholder="${t("searchSalesOrders")}" />
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
        <span class="muted-label">${record.code} - ${record.fields?.quoteCode || t("notDefined")} - ${getQuoteLines(record).length} ${t("quoteLines")}</span>
        <strong>${record.title}</strong>
        <p>${getQuoteLines(record).map((line) => line.productServiceName).filter(Boolean).slice(0, 2).join(" / ") || t("notDefined")}</p>
        <span class="muted-label">${t("customer")}: ${record.fields?.customerName || t("notDefined")}</span>
        <span class="muted-label">${t("deliveryPromise")}: ${record.fields?.deliveryPromise || t("notDefined")} · ${t("fulfillmentMode")}: ${record.fields?.fulfillmentMode || t("notDefined")}</span>
        <span class="muted-label">${t("quoteTotal")}: ${formatCurrency(Number(record.fields?.total || 0))} · ${t("estimatedCost")}: ${formatCurrency(Number(record.fields?.estimatedCost || 0))}</span>
        <span class="muted-label">${t("estimatedMargin")}: ${formatNumber(Number(record.fields?.estimatedMargin || 0))}%</span>
        <div class="product-history">
          <div class="product-history-head">
            <span class="muted-label">${t("orderAdjustments")}</span>
            <strong>${adjustments.length}</strong>
          </div>
          <p>${lastAdjustment ? `${formatKardexDate(lastAdjustment.changedAt)} - ${lastAdjustment.reason}` : t("noOrderAdjustments")}</p>
        </div>
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${record.status === "Aprobado" ? "active" : record.status === "Cancelado" ? "warning" : ""}">${translateStatus(record.status)}</span>
        <button class="secondary-action small-action" type="button" data-action="edit-sales-order" data-record-id="${record.id}">${t("edit")}</button>
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
  const orders = mockDb.loadModuleRecords(module.id, "pedidos").filter((record) => record.recordType === "salesOrder");
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
        <button class="primary-action disabled-action" type="button" disabled aria-disabled="true">
          <span>☷</span>
          <span>${t("deliveryManagement")}</span>
        </button>
      </div>

      <section class="section-card catalog-workspace">
        ${renderFlowGuide(getSalesFlowTitle(submodule), getSalesFlowSteps(submodule))}
        <div class="catalog-toolbar kardex-toolbar">
          <label class="search-field catalog-search">
            <span>S</span>
            <input id="salesDeliverySearch" type="search" value="${search}" placeholder="${t("searchDeliveries")}" />
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
  bindProductionPanelActions();
}

function renderSalesDeliveryCard(delivery, order = null) {
  const deliveryStatus = delivery.fields?.deliveryStatus || delivery.status;
  const quoteId = order?.fields?.quoteId || findSalesQuoteByCode(delivery.fields?.quoteCode)?.id || "";
  return `
    <article class="catalog-card clickable-card" data-action="view-delivery-quote" data-quote-id="${quoteId}">
      <div class="catalog-card-main">
        <span class="muted-label">${delivery.code} - ${delivery.fields?.orderCode || t("notDefined")} - ${delivery.fields?.quoteCode || t("notDefined")}</span>
        <strong>${delivery.title}</strong>
        <p>${delivery.fields?.customerName || t("notDefined")}</p>
        <span class="muted-label">${t("deliveryStatus")}: ${translateStatus(deliveryStatus)} · ${t("salesOrderStatus")}: ${translateStatus(order?.status || t("notDefined"))}</span>
        <span class="muted-label">${t("deliveryDate")}: ${delivery.fields?.deliveryDate || t("notDefined")} · ${t("recipient")}: ${delivery.fields?.recipient || t("notDefined")}</span>
        <span class="muted-label">${t("deliveryReference")}: ${delivery.fields?.deliveryReference || t("notDefined")} · ${t("nextDeliveryDate")}: ${delivery.fields?.nextDeliveryDate || t("notDefined")}</span>
        ${delivery.fields?.notes ? `<p>${delivery.fields.notes}</p>` : ""}
      </div>
      <div class="catalog-card-actions">
        <span class="chip ${getDeliveryTone(deliveryStatus)}">${translateStatus(deliveryStatus)}</span>
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

function createRecipeSnapshot(recipe) {
  return {
    id: recipe.id,
    productServiceId: recipe.productServiceId || "",
    product: recipe.product,
    version: recipe.version,
    quantityBase: recipe.quantityBase,
    unit: recipe.unit,
    status: recipe.status,
    approvalStatus: getRecipeApprovalStatus(recipe),
    approvedBy: recipe.approvedBy || "",
    approvedAt: recipe.approvedAt || "",
    changeReason: recipe.changeReason || "",
    center: recipe.center,
    resources: (recipe.resources || []).map((resource) => ({ ...resource })),
    steps: [...(recipe.steps || [])]
  };
}

function getGenericSubmodule(module, id) {
  return normalizeSubmodules(module).find((item) => item.id === id) || normalizeSubmodules(module)[0];
}

function buildGenericSubmoduleRows(module, submodule) {
  const savedRows = getSavedModuleTableRows(module, submodule.id);
  if (savedRows.length) return savedRows;
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
    serial: t("serialPolicy"),
    restricted: t("restrictedPolicy")
  };
  return policyMap[policy] || policy || t("notDefined");
}

function translateInventoryItemType(type) {
  const typeMap = {
    rawMaterial: t("rawMaterialItem"),
    consumable: t("consumableItem"),
    tool: t("toolItem"),
    finishedGood: t("finishedGoodItem"),
    sparePart: t("sparePartItem"),
    serviceSupply: t("serviceSupplyItem")
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

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${t("productionSubmodule")}</p>
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
    return `<button class="primary-action" type="button" data-action="open-labor-role"><span>+</span><span>Nueva area/puesto</span></button>`;
  }
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
  if (id === "maquinaria") return renderMachinesScreen();
  if (id === "ordenes") return renderOrdersScreen(orders);
  if (id === "entregables") return renderDeliverablesScreen(orders);
  if (id === "validacion-recursos") return renderValidationScreen(recipes);
  return "";
}

function renderFlowGuide(title, steps, currentIndex = null) {
  return `
    <details class="flow-guide-card" open>
      <summary class="flow-guide-summary">
        <span class="section-icon">↳</span>
        <strong>${title}</strong>
        <span class="flow-guide-toggle-copy">Ocultar / mostrar</span>
      </summary>
      <div class="flow-guide-steps">
        ${steps.map((step, index) => `
          <article class="flow-guide-step ${currentIndex === index ? "current" : ""}">
            <span>${index + 1}</span>
            <strong>${step.title}</strong>
            <p>${step.detail}</p>
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

  return `
    <section class="section-card catalog-workspace">
      ${renderFlowGuide("Flujo del catalogo maestro", [
        { title: "Alta", detail: "Crear producto o servicio con ficha maestra." },
        { title: "Revision", detail: "Validar SKU, responsable, precio y margen." },
        { title: "Receta", detail: "Generar o editar la receta vigente." },
        { title: "Activo", detail: "Dejar disponible para nuevas ordenes." }
      ])}
      <div class="catalog-toolbar">
        <label class="search-field catalog-search">
          <span>S</span>
          <input id="productServiceSearch" type="search" value="${search}" placeholder="Buscar producto o servicio" />
        </label>
      </div>
      <p class="helper-copy">Este apartado solo administra el catalogo maestro. La estructura de recursos, etapas y tiempos se crea en Recetas.</p>
      <div class="catalog-grid">
        ${filteredItems.map((item) => {
          const history = getProductServiceOrderHistory(item);
          const currentRecipe = getProductServiceCurrentRecipe(item);
          const standardCost = currentRecipe ? getRecipeStandardCost(currentRecipe) : Number(item.standardCost || 0);
          const targetPrice = Number(item.targetPrice || 0);
          const margin = targetPrice && standardCost ? ((targetPrice - standardCost) / targetPrice) * 100 : Number(item.expectedMargin || 0);
          return `
        <article class="catalog-card">
          <div class="catalog-card-main">
            <span class="muted-label">${item.id} - ${item.sku || "SKU pendiente"} - ${item.kind} - ${item.unit}</span>
            <strong>${item.name}</strong>
            <p>${item.description}</p>
            <span class="muted-label">${item.category} - ${item.center} - Responsable: ${item.owner || "Sin asignar"}</span>
            <div class="cost-summary-grid">
              <span><strong>${formatCurrency(standardCost)}</strong>Costo estandar</span>
              <span><strong>${targetPrice ? formatCurrency(targetPrice) : "Pendiente"}</strong>Precio objetivo</span>
              <span><strong>${formatNumber(margin)}%</strong>Margen esperado</span>
            </div>
            <div class="product-history">
              <div class="product-history-head">
                <span class="muted-label">Receta vigente</span>
                <strong>${currentRecipe ? `${currentRecipe.id} v${currentRecipe.version}` : "Sin receta"}</strong>
              </div>
              <p>${currentRecipe ? `${getRecipeApprovalStatus(currentRecipe)} - ${currentRecipe.steps.length} etapas operativas` : "Debe generarse una receta antes de liberar produccion."}</p>
            </div>
            <div class="product-history">
              <div class="product-history-head">
                <span class="muted-label">Historial de ordenes</span>
                <strong>${history.length}</strong>
              </div>
              ${history.length ? `
                <div class="product-history-list">
                  ${history.slice(0, 3).map((order) => `
                    <span>${order.id} - ${order.quantity} ${order.unit} - ${order.status}</span>
                  `).join("")}
                </div>
              ` : `<p>Sin ordenes registradas para este ${item.kind.toLowerCase()}.</p>`}
            </div>
          </div>
          <div class="catalog-card-actions">
            <label class="status-control">
              <span>Estatus</span>
              <select data-action="change-product-service-status" data-product-id="${item.id}">
                ${["Activo", "Inactivo", "En espera de aprobacion"].map((status) => `
                  <option value="${status}" ${item.status === status ? "selected" : ""}>${status}</option>
                `).join("")}
              </select>
            </label>
            <button class="secondary-action small-action" type="button" data-action="edit-product-service" data-product-id="${item.id}">Editar ficha</button>
            ${currentRecipe
              ? `<button class="secondary-action small-action" type="button" data-action="edit-recipe" data-recipe-id="${currentRecipe.id}">Editar receta</button>`
              : `<button class="secondary-action small-action" type="button" data-action="go-recipes-product" data-product-id="${item.id}">Generar receta</button>`}
          </div>
        </article>
      `;
        }).join("")}
      </div>
      ${filteredItems.length ? "" : `<p class="helper-copy">No hay productos o servicios con esa busqueda.</p>`}
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
  const services = [
    { code: "SER-014", name: t("assemblyService"), type: t("repeatableService"), detail: t("assemblyServiceDetail"), status: t("configurable") },
    { code: "SER-022", name: t("specialPacking"), type: t("operationalService"), detail: t("specialPackingDetail"), status: t("activeStatus") }
  ];

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
  const selectedArea = localStorage.getItem("erclave-labor-selected-area");
  if (selectedArea) return renderLaborAreaDetailScreen(selectedArea, roles);

  const search = localStorage.getItem("erclave-labor-area-search") || "";
  const normalizedSearch = search.trim().toLowerCase();
  const areas = [...new Set(roles.map((role) => role.area))];
  const filteredAreas = normalizedSearch
    ? areas.filter((area) => {
        const areaRoles = roles.filter((role) => role.area === area);
        return (
          area.toLowerCase().includes(normalizedSearch) ||
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
      ${renderFlowGuide("Flujo de configuracion de mano de obra", [
        { title: "Area", detail: "Registrar o ubicar el area operativa." },
        { title: "Rol", detail: "Definir puesto o rol requerido." },
        { title: "Capacidad", detail: "Capturar recursos, minutos y costo." },
        { title: "Receta", detail: "Usar el rol como recurso productivo." }
      ])}
      <div class="catalog-toolbar">
        <label class="search-field catalog-search">
          <span>S</span>
          <input id="laborAreaSearch" type="search" value="${search}" placeholder="Buscar area, puesto o rol" />
        </label>
      </div>
      <p class="helper-copy">Consulta areas operativas y entra a cada una para administrar sus puestos, cantidad de recursos, costos y disponibilidad.</p>
      <div class="area-summary-grid">
        ${filteredAreas.map((area) => {
          const areaRoles = roles.filter((role) => role.area === area);
          const totalPeople = areaRoles.reduce((sum, role) => sum + Number(role.quantity || 1), 0);
          const totalMinutes = areaRoles.reduce((sum, role) => sum + Number(role.available || 0), 0);
          return `
            <article class="area-card">
              <div>
                <span class="muted-label">Area operativa</span>
                <strong>${area}</strong>
                <p>${areaRoles.length} puestos/roles - ${totalPeople} recursos - ${formatNumber(totalMinutes)} min/dia</p>
              </div>
              <button class="secondary-action small-action" type="button" data-action="open-labor-area" data-area="${area}">Ver puestos</button>
            </article>
          `;
        }).join("")}
      </div>
      ${filteredAreas.length ? "" : `<p class="helper-copy">No hay areas con esa busqueda.</p>`}
    </section>
  `;
}

function renderLaborAreaDetailScreen(area, roles = mockDb.loadLaborRoles()) {
  const areaRoles = roles.filter((role) => role.area === area);
  const totalPeople = areaRoles.reduce((sum, role) => sum + Number(role.quantity || 1), 0);
  const totalMinutes = areaRoles.reduce((sum, role) => sum + Number(role.available || 0), 0);

  return `
    <section class="section-card catalog-workspace">
      <div class="panel-head compact">
        <div>
          <p class="eyebrow">Area operativa</p>
          <h3>${area}</h3>
        </div>
        <div class="row-actions">
          <button class="primary-action" type="button" data-action="open-labor-role-area" data-area="${area}"><span>+</span><span>Nuevo rol/recurso</span></button>
          <button class="secondary-action" type="button" data-action="back-labor-areas">Todas las areas</button>
        </div>
      </div>
      <div class="area-summary-grid">
        <article class="mini-kpi positive"><span>Puestos/roles</span><strong>${areaRoles.length}</strong></article>
        <article class="mini-kpi positive"><span>Recursos</span><strong>${totalPeople}</strong></article>
        <article class="mini-kpi positive"><span>Capacidad</span><strong>${formatNumber(totalMinutes)} min</strong></article>
      </div>
      <div class="catalog-grid">
        ${areaRoles.map((role) => `
          <article class="catalog-card">
            <div class="catalog-card-main">
              <span class="muted-label">${role.id} - ${role.area}</span>
              <strong>${role.name}</strong>
              <p>${role.position} - ${formatNumber(role.quantity || 1)} personas/recurso.</p>
              <span class="muted-label">${formatNumber(role.minutesPerResource || role.available)} ${role.unit} por recurso - ${formatNumber(role.available)} ${role.unit} totales por dia</span>
              <span class="muted-label">Costo: ${formatCurrency(role.cost)} por ${role.unit}</span>
            </div>
            <div class="catalog-card-actions">
              <span class="chip ${role.status === "Activo" ? "active" : ""}">${role.status}</span>
              <button class="secondary-action small-action" type="button" data-action="edit-labor-role" data-role-id="${role.id}">Abrir rol</button>
            </div>
          </article>
        `).join("")}
      </div>
      ${areaRoles.length ? "" : `<p class="helper-copy">Esta area todavia no tiene puestos registrados.</p>`}
    </section>
  `;
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
  return `
    <div class="submodule-layout">
      <section>
        ${renderOrderList(orders)}
      </section>
      <section class="section-card">
        ${renderFlowGuide("Flujo de estatus de orden", orderStatusCatalog.map((status) => ({
          title: translateStatus(status),
          detail: status === "Liberada"
            ? "Orden autorizada para iniciar."
            : status === "En espera de recursos"
              ? "Falta material, capacidad o confirmacion."
              : status === "En produccion"
                ? "Etapas operativas en ejecucion."
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
      order: order.id,
      product: order.recipeName,
      quantity: `${order.quantity} ${order.unit}`,
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
            <strong>${item.area}</strong>
            <p>${item.product}</p>
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
        { title: "Recursos suficientes", detail: "Validar materiales, mano de obra y maquinaria." },
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
  modulePanel.querySelectorAll("[data-action='open-labor-role-area']").forEach((button) => {
    button.addEventListener("click", () => openLaborRoleModal(null, button.dataset.area));
  });
  modulePanel.querySelectorAll("[data-action='edit-labor-role']").forEach((button) => {
    button.addEventListener("click", () => openLaborRoleModal(button.dataset.roleId));
  });
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
      navigateTo({ active: state.active, activeSubmodule: state.activeSubmodule, laborArea: button.dataset.area });
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
  modulePanel.querySelectorAll("[data-action='change-product-service-status']").forEach((select) => {
    select.addEventListener("change", () => {
      const item = mockDb.findProductService(select.dataset.productId);
      if (!item) return;
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
  const recipe = recipes.find((item) => item.id === selectedRecipeId) || recipes[0] || defaultRecipes[0];
  const validationQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);
  const release = getReleaseReview(recipe, validationQuantity);
  const validation = release.validation;

  return `
      <div class="section-title">
        <span class="section-icon">✓</span>
        <strong>Validacion de receta contra almacen</strong>
      </div>
      <div class="validator-head">
        <div>
          <span class="muted-label">Receta activa</span>
          <strong>${recipe.product}</strong>
        </div>
        <label class="quantity-control recipe-select-control">
          <span>Receta</span>
          <select id="selectedRecipe">
            ${recipes
              .map(
                (item) => `
                  <option value="${item.id}" ${item.id === recipe.id ? "selected" : ""}>
                    ${item.id} · ${item.product}
                  </option>
                `
              )
              .join("")}
          </select>
        </label>
        <label class="quantity-control">
          <span>Cantidad a producir</span>
          <input id="validationQuantity" type="number" min="1" value="${validationQuantity}" />
        </label>
        <span class="chip ${release.canRelease ? "active" : "warning"}">
          ${release.canRelease ? "Lista para liberar" : "Pendiente de liberacion"}
        </span>
      </div>
      <p class="helper-copy">La validacion multiplica los recursos de la receta por la cantidad indicada, revisa aprobacion de receta y calcula costo estandar. Materias primas y consumibles vienen de Almacenes; mano de obra viene de Areas y puestos; maquinaria viene del catalogo de Maquinaria.</p>
      <div class="cost-summary-grid">
        <span><strong>${getRecipeApprovalStatus(recipe)}</strong>Aprobacion</span>
        <span><strong>${formatCurrency(getRecipeStandardCost(recipe))}</strong>Costo estandar unitario</span>
        <span><strong>${formatCurrency(validation.totalCost)}</strong>Costo planeado lote</span>
      </div>
      ${release.issues.length ? `<p class="helper-copy">Pendientes para liberar: ${release.issues.join(", ")}.</p>` : ""}
      <div class="inline-actions">
        <button class="primary-action" type="button" data-action="open-order">Generar orden de produccion</button>
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
                <p>${formatNumber(row.required)} / ${formatNumber(row.available)} ${row.unit}</p>
              </article>
            `
          )
          .join("")}
      </div>
  `;
}

function renderOrderList(orders) {
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
            return `
            <article class="recipe-list-row order-list-row">
              <div>
                <strong>${order.id} · ${order.recipeName}</strong>
                <span>${order.quantity} ${order.unit} · entrega ${order.dueDate || "sin fecha"} · responsable ${order.responsible} · ${order.releaseStatus || "Liberada"}</span>
                <span>Avance ${formatNumber(progress)}% · planeado ${formatCurrency(cost.plannedCost)} · real ${formatCurrency(cost.actualCost)} · variacion ${formatCurrency(cost.variance)} (${formatNumber(cost.variancePct)}%)</span>
                <div class="stage-progress-list">
                  ${(order.areas || []).map((stage, index) => `
                    <button class="stage-pill ${stage.status === "Terminada" ? "done" : stage.status === "En proceso" ? "active" : ""}" type="button" data-action="advance-order-stage" data-order-id="${order.id}" data-stage-index="${index}">
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
                  <select data-action="change-order-status" data-order-id="${order.id}">
                    ${orderStatusCatalog.map((status) => `
                      <option value="${status}" ${order.status === status ? "selected" : ""}>${translateStatus(status)}</option>
                    `).join("")}
                  </select>
                </label>
                <button class="secondary-action small-action" type="button" data-action="print-order" data-order-id="${order.id}">PDF/Imprimir</button>
              </div>
            </article>
          `;
          })
          .join("")}
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
            const validation = calculateRecipe(recipe, Number(localStorage.getItem("erclave-validation-qty") || 100));
            const approvalStatus = getRecipeApprovalStatus(recipe);
            const standardCost = getRecipeStandardCost(recipe);
            return `
              <article class="recipe-list-row">
                <div>
                  <strong>${recipe.id} · ${recipe.product}</strong>
                  <span>v${recipe.version} · ${approvalStatus} · ${recipe.resources.length} recursos · ${recipe.steps.length} etapas genericas · costo estandar ${formatCurrency(standardCost)}</span>
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
      </div>
    </section>
  `;
}

function renderFlow() {
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









function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    toast.hidden = true;
  }, 2600);
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

function openWarehouseModal(module, submodule, recordId = null) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || {};
  const isEditing = Boolean(existingRecord);

  modalContent.innerHTML = `
    <form class="recipe-form" id="warehouseForm">
      <input type="hidden" name="recordId" value="${existingRecord?.id || ""}" />
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
          <input name="code" type="text" value="${existingRecord?.code || ""}" placeholder="ALM-MP-01" required />
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
            <option value="spareParts" ${selectedOption(fields.type, "spareParts")}>${t("spareParts")}</option>
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

function saveWarehouseForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim()) errors.push(t("warehouseCodeRequired"));
  if (!data.name?.trim()) errors.push(t("warehouseNameRequired"));
  if (!data.businessCenter?.trim()) errors.push(t("businessCenterRequired"));
  if (!data.location?.trim()) errors.push(t("warehouseLocationRequired"));
  if (!data.owner?.trim()) errors.push(t("warehouseOwnerRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
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

function openInventoryItemModal(module, submodule, recordId = null) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || {};
  const warehouses = mockDb.loadModuleRecords(module.id, "almacenes").filter((record) => record.recordType === "warehouse");
  const isEditing = Boolean(existingRecord);

  modalContent.innerHTML = `
    <form class="recipe-form" id="inventoryItemForm">
      <input type="hidden" name="recordId" value="${existingRecord?.id || ""}" />
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
          <input name="code" type="text" value="${existingRecord?.code || ""}" placeholder="MAT-001" required />
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
          <input name="unit" type="text" value="${fields.unit || ""}" placeholder="pz" required />
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
            <select name="defaultWarehouseId">
              <option value="">${t("notDefined")}</option>
              ${warehouses.map((warehouse) => `<option value="${warehouse.id}" ${selectedOption(fields.defaultWarehouseId, warehouse.id)}>${warehouse.code} - ${warehouse.title}</option>`).join("")}
            </select>
          ` : `<input name="defaultWarehouseName" type="text" value="${fields.defaultWarehouseName || ""}" placeholder="${t("warehouseNamePlaceholder")}" />`}
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
}

function saveInventoryItemForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim()) errors.push(t("itemCodeRequired"));
  if (!data.name?.trim()) errors.push(t("itemNameRequired"));
  if (!data.unit?.trim()) errors.push(t("unitRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const warehouse = data.defaultWarehouseId ? mockDb.findModuleRecord(module.id, data.defaultWarehouseId) : null;
  const code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
  const defaultWarehouseName = warehouse ? `${warehouse.code} - ${warehouse.title}` : data.defaultWarehouseName?.trim() || "";
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
      minStock: data.minStock || "",
      maxStock: data.maxStock || "",
      policy: data.policy,
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
          <input name="unit" type="text" placeholder="pz" required />
        </label>
        <label class="preview-field">
          <span>${t("warehouse")}</span>
          ${warehouses.length ? `
            <select name="warehouseId" required>
              ${warehouses.map((warehouse) => `<option value="${warehouse.id}">${warehouse.code} - ${warehouse.title}</option>`).join("")}
            </select>
          ` : `<input name="warehouseName" type="text" placeholder="${t("warehouseNamePlaceholder")}" required />`}
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
  form.querySelector("[name='unit']").value = item.fields?.unit || "";
  modalContent.querySelector("#movementItemResults").hidden = true;
}

function syncMovementItemFields(event) {
  const form = event.target.closest("form");
  const item = findInventoryItemByOption(event.target.value);
  form.querySelector("[name='itemId']").value = item?.id || "";
  renderMovementItemLookup(event);
  if (!item) return;
  form.querySelector("[name='unit']").value = item.fields?.unit || "";
}

function saveInventoryMovementForm(event, module, submodule) {
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
  if (["exit", "negativeAdjustment"].includes(data.movementType)) {
    const itemKey = data.itemId || itemName;
    const warehouseKey = data.warehouseId || warehouseName;
    const available = getAvailableStock(itemKey, warehouseKey, data.unit.trim());
    if (available < movementQuantity) {
      renderFormErrors([t("insufficientStock", { available: formatNumber(available), unit: data.unit.trim() })]);
      return;
    }
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
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || {};
  const isEditing = Boolean(existingRecord);

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesCustomerForm">
      <input type="hidden" name="recordId" value="${existingRecord?.id || ""}" />
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
          <input name="code" type="text" value="${existingRecord?.code || ""}" placeholder="CLI-001" required />
        </label>
        <label class="preview-field">
          <span>${t("commercialName")}</span>
          <input name="commercialName" type="text" value="${fields.commercialName || existingRecord?.title || ""}" placeholder="${t("commercialNamePlaceholder")}" required />
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
          <input name="contactName" type="text" value="${fields.contactName || ""}" placeholder="${t("contactPlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("commercialEmail")}</span>
          <input name="contactEmail" type="email" value="${fields.contactEmail || ""}" placeholder="compras@cliente.com" required />
        </label>
        <label class="preview-field">
          <span>${t("phone")}</span>
          <input name="contactPhone" type="tel" value="${fields.contactPhone || ""}" placeholder="+52 55 0000 0000" required />
        </label>
        <label class="preview-field">
          <span>${t("salesOwner")}</span>
          <input name="salesOwner" type="text" value="${fields.salesOwner || ""}" placeholder="${t("salesOwnerPlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("paymentTerms")}</span>
          <input name="paymentTerms" type="text" value="${fields.paymentTerms || ""}" placeholder="${t("paymentTermsPlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("creditLimit")}</span>
          <input name="creditLimit" type="text" value="${fields.creditLimit || ""}" placeholder="$50,000 MXN" />
        </label>
        <label class="preview-field wide-field">
          <span>${t("commercialNotes")}</span>
          <textarea name="commercialNotes" rows="2" placeholder="${t("commercialNotesPlaceholder")}">${fields.commercialNotes || ""}</textarea>
        </label>

        <div class="section-title form-section-title wide-field">
          <span class="section-icon">☷</span>
          <strong>${t("billingProfile")}</strong>
        </div>

        <label class="preview-field">
          <span>${t("billingLegalName")}</span>
          <input name="billingLegalName" type="text" value="${fields.billingLegalName || ""}" placeholder="${t("billingLegalNamePlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("taxId")}</span>
          <input name="taxId" type="text" value="${fields.taxId || ""}" placeholder="XAXX010101000" required />
        </label>
        <label class="preview-field">
          <span>${t("taxRegime")}</span>
          <input name="taxRegime" type="text" value="${fields.taxRegime || ""}" placeholder="${t("taxRegimePlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("cfdiUse")}</span>
          <input name="cfdiUse" type="text" value="${fields.cfdiUse || ""}" placeholder="G03" />
        </label>
        <label class="preview-field">
          <span>${t("billingEmail")}</span>
          <input name="billingEmail" type="email" value="${fields.billingEmail || ""}" placeholder="facturas@cliente.com" required />
        </label>
        <label class="preview-field">
          <span>${t("billingPhone")}</span>
          <input name="billingPhone" type="tel" value="${fields.billingPhone || ""}" placeholder="+52 55 0000 0000" />
        </label>
        <label class="preview-field">
          <span>${t("billingStreet")}</span>
          <input name="billingStreet" type="text" value="${fields.billingStreet || ""}" placeholder="${t("billingStreetPlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("billingExterior")}</span>
          <input name="billingExterior" type="text" value="${fields.billingExterior || ""}" placeholder="123" />
        </label>
        <label class="preview-field">
          <span>${t("billingInterior")}</span>
          <input name="billingInterior" type="text" value="${fields.billingInterior || ""}" placeholder="4B" />
        </label>
        <label class="preview-field">
          <span>${t("billingNeighborhood")}</span>
          <input name="billingNeighborhood" type="text" value="${fields.billingNeighborhood || ""}" placeholder="${t("billingNeighborhoodPlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("billingCity")}</span>
          <input name="billingCity" type="text" value="${fields.billingCity || ""}" placeholder="${t("billingCityPlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("billingState")}</span>
          <input name="billingState" type="text" value="${fields.billingState || ""}" placeholder="${t("billingStatePlaceholder")}" required />
        </label>
        <label class="preview-field">
          <span>${t("billingZipCode")}</span>
          <input name="billingZipCode" type="text" value="${fields.billingZipCode || ""}" placeholder="00000" required />
        </label>
        <label class="preview-field">
          <span>${t("billingCountry")}</span>
          <input name="billingCountry" type="text" value="${fields.billingCountry || "Mexico"}" required />
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

function saveSalesCustomerForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim()) errors.push(t("customerCodeRequired"));
  if (!data.commercialName?.trim()) errors.push(t("commercialNameRequired"));
  if (!data.contactName?.trim()) errors.push(t("contactRequired"));
  if (!data.contactEmail?.trim()) errors.push(t("commercialEmailRequired"));
  if (!data.contactPhone?.trim()) errors.push(t("phoneRequired"));
  if (!data.billingLegalName?.trim()) errors.push(t("billingLegalNameRequired"));
  if (!data.taxId?.trim()) errors.push(t("taxIdRequired"));
  if (!data.billingEmail?.trim()) errors.push(t("billingEmailRequired"));
  if (!data.billingStreet?.trim()) errors.push(t("billingStreetRequired"));
  if (!data.billingCity?.trim()) errors.push(t("billingCityRequired"));
  if (!data.billingState?.trim()) errors.push(t("billingStateRequired"));
  if (!data.billingZipCode?.trim()) errors.push(t("billingZipCodeRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
  }

  const code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
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

function openSalesQuoteModal(module, submodule, recordId = null) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const existingRecord = recordId ? mockDb.findModuleRecord(module.id, recordId) : null;
  const fields = existingRecord?.fields || {};
  const customers = mockDb.loadModuleRecords(module.id, "clientes").filter((record) => record.recordType === "customer");
  const productsServices = mockDb.loadProductsServices();
  const selectedCustomer = fields.customerId ? mockDb.findModuleRecord(module.id, fields.customerId) : null;
  const quoteLines = normalizeQuoteLines(fields);
  const isEditing = Boolean(existingRecord);

  if (!customers.length || !productsServices.length) {
    showToast(!customers.length ? t("quoteRequiresCustomers") : t("quoteRequiresProducts"));
    return;
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesQuoteForm">
      <input type="hidden" name="recordId" value="${existingRecord?.id || ""}" />
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
          <input name="code" type="text" value="${existingRecord?.code || ""}" placeholder="COT-001" required />
        </label>
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            <option value="Borrador" ${selectedOption(existingRecord?.status || "Borrador", "Borrador")}>${t("draftStatus")}</option>
            <option value="Cotizada" ${selectedOption(existingRecord?.status, "Cotizada")}>${t("quotedStatus")}</option>
            <option value="Aprobado" ${selectedOption(existingRecord?.status, "Aprobado")}>${t("approvedStatus")}</option>
            <option value="Vencida" ${selectedOption(existingRecord?.status, "Vencida")}>${t("expiredStatus")}</option>
          </select>
        </label>
        <label class="preview-field product-lookup-field wide-field">
          <span>${t("customer")}</span>
          <input id="quoteCustomerSearch" type="text" value="${selectedCustomer ? formatSalesCustomerOption(selectedCustomer) : ""}" placeholder="${t("customerLookupPlaceholder")}" autocomplete="off" required />
          <input name="customerId" type="hidden" value="${selectedCustomer?.id || ""}" />
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
          <input name="validUntil" type="date" value="${fields.validUntil || ""}" required />
        </label>
        <label class="preview-field">
          <span>${t("deliveryPromise")}</span>
          <input name="deliveryPromise" type="date" value="${fields.deliveryPromise || ""}" />
        </label>
        <label class="preview-field">
          <span>${t("paymentTerms")}</span>
          <input name="paymentTerms" type="text" value="${fields.paymentTerms || selectedCustomer?.fields?.paymentTerms || ""}" placeholder="${t("paymentTermsPlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("currency")}</span>
          <input name="currency" type="text" value="${fields.currency || "MXN"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>${t("notes")}</span>
          <textarea name="notes" rows="3" placeholder="${t("quoteNotesPlaceholder")}">${fields.notes || ""}</textarea>
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
          <button class="lookup-option" type="button" data-sales-customer-id="${customer.id}">
            <strong>${customer.title}</strong>
            <span>${customer.code} - ${customer.fields?.billingLegalName || t("notDefined")} - ${customer.fields?.taxId || t("notDefined")}</span>
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

function renderQuoteLineRow(line = {}, index = 0) {
  const productService = line.productServiceId ? mockDb.findProductService(line.productServiceId) : null;
  return `
    <div class="quote-line-row" data-quote-line>
      <label class="preview-field product-lookup-field quote-line-product">
        <span>${t("productOrService")}</span>
        <input class="quote-product-search" type="text" value="${productService ? formatProductServiceOption(productService) : line.productServiceName || ""}" placeholder="${t("productLookupPlaceholder")}" autocomplete="off" required />
        <input name="lineProductServiceId" type="hidden" value="${line.productServiceId || ""}" />
        <div class="lookup-results quote-product-results" hidden></div>
      </label>
      <label class="preview-field">
        <span>${t("quantity")}</span>
        <input name="lineQuantity" type="number" min="0.01" step="0.01" value="${line.quantity || 1}" required />
      </label>
      <label class="preview-field">
        <span>${t("unit")}</span>
        <input name="lineUnit" type="text" value="${line.unit || productService?.unit || ""}" required />
      </label>
      <label class="preview-field">
        <span>${t("unitPrice")}</span>
        <input name="lineUnitPrice" type="number" min="0" step="0.01" value="${line.unitPrice || productService?.targetPrice || 0}" required />
      </label>
      <label class="preview-field">
        <span>${t("discount")}</span>
        <input name="lineDiscount" type="number" min="0" max="100" step="0.01" value="${line.discount || 0}" />
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
  const matches = getProductServiceMatches(input.value);
  results.hidden = false;
  results.innerHTML = matches.length
    ? matches
        .map((item) => `
          <button class="lookup-option" type="button" data-product-id="${item.id}">
            <strong>${item.name}</strong>
            <span>${item.id} - ${item.kind} - ${item.unit}</span>
          </button>
        `)
        .join("")
    : `<div class="lookup-empty">${t("productLookupEmpty")}</div>`;
}

function selectQuoteProductFromLookup(event) {
  const button = event.target.closest("[data-product-id]");
  if (!button) return;
  const item = mockDb.findProductService(button.dataset.productId);
  if (!item) return;
  const row = button.closest("[data-quote-line]");
  row.querySelector(".quote-product-search").value = formatProductServiceOption(item);
  row.querySelector("[name='lineProductServiceId']").value = item.id;
  row.querySelector("[name='lineUnit']").value = item.unit || "";
  row.querySelector("[name='lineUnitPrice']").value = item.targetPrice || 0;
  row.querySelector(".quote-product-results").hidden = true;
}

function syncQuoteProductFields(event) {
  const row = event.target.closest("[data-quote-line]");
  const item = findProductServiceByOption(event.target.value);
  row.querySelector("[name='lineProductServiceId']").value = item?.id || "";
  renderQuoteProductLookup(event);
  if (!item) return;
  row.querySelector("[name='lineUnit']").value = item.unit || "";
  row.querySelector("[name='lineUnitPrice']").value = item.targetPrice || 0;
}

function saveSalesQuoteForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];

  if (!data.code?.trim()) errors.push(t("quoteCodeRequired"));
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
  const code = data.code.trim().toUpperCase();
  const existingRecord = data.recordId ? mockDb.findModuleRecord(module.id, data.recordId) : null;
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
  const approvedQuotes = mockDb.loadModuleRecords(module.id, "cotizaciones")
    .filter((record) => record.recordType === "quote" && record.status === "Aprobado");
  const selectedQuote = quoteId
    ? approvedQuotes.find((quote) => quote.id === quoteId)
    : approvedQuotes[0];

  if (!approvedQuotes.length || !selectedQuote) {
    showToast(t("salesOrderRequiresApprovedQuote"));
    return;
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesOrderForm">
      <input type="hidden" name="quoteId" value="${selectedQuote.id}" />
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
          <input name="code" type="text" value="" placeholder="PED-001" required />
        </label>
        <label class="preview-field wide-field">
          <span>${t("quoteDocument")}</span>
          <select name="selectedQuoteId" required>
            ${approvedQuotes.map((quote) => `<option value="${quote.id}" ${selectedOption(selectedQuote.id, quote.id)}>${quote.code} - ${quote.fields?.customerName || quote.title} - ${formatCurrency(Number(quote.fields?.total || 0))}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            <option value="Aprobado">${t("approvedStatus")}</option>
            <option value="En preparacion">${t("preparingStatus")}</option>
            <option value="Cancelado">${t("canceledStatus")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("deliveryPromise")}</span>
          <input name="deliveryPromise" type="date" value="${selectedQuote.fields?.deliveryPromise || ""}" />
        </label>
        <label class="preview-field">
          <span>${t("fulfillmentMode")}</span>
          <select name="fulfillmentMode">
            <option value="${t("pendingInventoryReview")}">${t("pendingInventoryReview")}</option>
            <option value="${t("stockFulfillment")}">${t("stockFulfillment")}</option>
            <option value="${t("productionFulfillment")}">${t("productionFulfillment")}</option>
          </select>
        </label>
        <label class="preview-field">
          <span>${t("owner")}</span>
          <input name="owner" type="text" value="${selectedQuote.owner || ""}" />
        </label>
        <label class="preview-field wide-field">
          <span>${t("notes")}</span>
          <textarea name="notes" rows="3" placeholder="${t("salesOrderNotesPlaceholder")}"></textarea>
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
  modalContent.querySelector("[name='selectedQuoteId']").addEventListener("change", (event) => {
    const quote = approvedQuotes.find((item) => item.id === event.target.value);
    if (!quote) return;
    modalContent.querySelector("[name='quoteId']").value = quote.id;
    modalContent.querySelector("[name='deliveryPromise']").value = quote.fields?.deliveryPromise || "";
    modalContent.querySelector("[name='owner']").value = quote.owner || "";
  });
  modalContent.querySelector("#salesOrderForm").addEventListener("submit", (event) => saveSalesOrderForm(event, module, submodule));
}

function saveSalesOrderForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];
  const quote = mockDb.findModuleRecord(module.id, data.quoteId);
  const existingOrder = mockDb.loadModuleRecords(module.id, submodule.id)
    .find((record) => record.recordType === "salesOrder" && record.fields?.quoteId === data.quoteId);

  if (!data.code?.trim()) errors.push(t("salesOrderCodeRequired"));
  if (!quote || quote.status !== "Aprobado") errors.push(t("salesOrderRequiresApprovedQuote"));
  if (existingOrder) errors.push(t("salesOrderQuoteAlreadyUsed"));

  if (errors.length) {
    renderFormErrors(errors);
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
  const label = state.lang === "en" ? module.titleEn : module.title;
  const order = mockDb.findModuleRecord(module.id, orderId);
  if (!order || order.recordType !== "salesOrder") return;
  const fields = order.fields || {};

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesOrderEditForm">
      <input type="hidden" name="orderId" value="${order.id}" />
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
          <input name="code" type="text" value="${order.code || ""}" required />
        </label>
        <label class="preview-field">
          <span>${t("status")}</span>
          <select name="status">
            ${getSalesOrderStatusOptions().map((status) => `<option value="${status}" ${selectedOption(order.status, status)}>${translateStatus(status)}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("deliveryPromise")}</span>
          <input name="deliveryPromise" type="date" value="${fields.deliveryPromise || ""}" />
        </label>
        <label class="preview-field">
          <span>${t("fulfillmentMode")}</span>
          <select name="fulfillmentMode">
            ${getFulfillmentModeOptions().map((mode) => `<option value="${mode}" ${selectedOption(fields.fulfillmentMode, mode)}>${mode}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("owner")}</span>
          <input name="owner" type="text" value="${order.owner || ""}" />
        </label>
        <label class="preview-field wide-field">
          <span>${t("notes")}</span>
          <textarea name="notes" rows="3" placeholder="${t("salesOrderNotesPlaceholder")}">${fields.notes || ""}</textarea>
        </label>
        <label class="preview-field wide-field">
          <span>${t("adjustmentReason")}</span>
          <textarea name="adjustmentReason" rows="3" placeholder="${t("adjustmentReasonPlaceholder")}" required></textarea>
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

function openSalesDeliveryModal(module, submodule, orderId = null) {
  const label = state.lang === "en" ? module.titleEn : module.title;
  const orders = mockDb.loadModuleRecords(module.id, "pedidos").filter((record) => record.recordType === "salesOrder");
  const selectedOrder = orderId
    ? orders.find((order) => order.id === orderId)
    : orders[0];

  if (!orders.length || !selectedOrder) {
    showToast(t("deliveryRequiresSalesOrder"));
    return;
  }

  modalContent.innerHTML = `
    <form class="recipe-form" id="salesDeliveryForm">
      <input type="hidden" name="orderId" value="${selectedOrder.id}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">${label}</p>
          <h2 id="modalTitle">${t("newDelivery")}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <div class="form-grid">
        <label class="preview-field wide-field">
          <span>${t("salesOrder")}</span>
          <select name="selectedOrderId" required>
            ${orders.map((order) => `<option value="${order.id}" ${selectedOption(selectedOrder.id, order.id)}>${order.code} - ${order.fields?.customerName || order.owner} - ${translateStatus(order.status)}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("deliveryStatus")}</span>
          <select name="deliveryStatus">
            ${getDeliveryStatusOptions().map((status) => `<option value="${status}">${translateStatus(status)}</option>`).join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>${t("deliveryDate")}</span>
          <input name="deliveryDate" type="date" value="${new Date().toISOString().slice(0, 10)}" required />
        </label>
        <label class="preview-field">
          <span>${t("recipient")}</span>
          <input name="recipient" type="text" value="${selectedOrder.fields?.customerName || selectedOrder.owner || ""}" placeholder="${t("recipientPlaceholder")}" />
        </label>
        <label class="preview-field">
          <span>${t("deliveryReference")}</span>
          <input name="deliveryReference" type="text" placeholder="REM-001 / guia / evidencia" />
        </label>
        <label class="preview-field">
          <span>${t("nextDeliveryDate")}</span>
          <input name="nextDeliveryDate" type="date" />
        </label>
        <label class="preview-field wide-field">
          <span>${t("deliveryNotes")}</span>
          <textarea name="notes" rows="3" placeholder="${t("deliveryNotesPlaceholder")}"></textarea>
        </label>
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
  modalContent.querySelector("[name='selectedOrderId']").addEventListener("change", (event) => {
    const order = orders.find((item) => item.id === event.target.value);
    if (!order) return;
    modalContent.querySelector("[name='orderId']").value = order.id;
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

function saveSalesDeliveryForm(event, module, submodule) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const errors = [];
  const order = mockDb.findModuleRecord(module.id, data.orderId);

  if (!order || order.recordType !== "salesOrder") errors.push(t("deliveryRequiresSalesOrder"));
  if (!data.deliveryDate) errors.push(t("deliveryDateRequired"));
  if (!getDeliveryStatusOptions().includes(data.deliveryStatus)) errors.push(t("deliveryStatusRequired"));
  if (data.deliveryStatus === "Entrega parcial" && !data.notes?.trim()) errors.push(t("partialDeliveryNotesRequired"));
  if (data.deliveryStatus === "No entregado" && !data.notes?.trim()) errors.push(t("failedDeliveryNotesRequired"));
  if (data.deliveryStatus === "Reprogramado" && !data.nextDeliveryDate) errors.push(t("nextDeliveryDateRequired"));

  if (errors.length) {
    renderFormErrors(errors);
    return;
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
  const existingItem = productServiceId ? mockDb.findProductService(productServiceId) : null;
  const isEditing = Boolean(existingItem);
  modalContent.innerHTML = `
    <form class="recipe-form" id="productServiceForm">
      <input type="hidden" name="productServiceId" value="${existingItem?.id || ""}" />
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
          <input name="name" type="text" value="${existingItem?.name || ""}" placeholder="Ej. Producto o servicio premium" required />
        </label>
        <label class="preview-field">
          <span>SKU / codigo interno</span>
          <input name="sku" type="text" value="${existingItem?.sku || ""}" placeholder="Ej. PROD-INT-001" required />
        </label>
        <label class="preview-field">
          <span>Unidad base</span>
          <input name="unit" type="text" value="${existingItem?.unit || "pieza"}" required />
        </label>
        <label class="preview-field">
          <span>Categoria</span>
          <input name="category" type="text" value="${existingItem?.category || "Produccion"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Centro de costos</span>
          <input name="center" type="text" value="${existingItem?.center || "Produccion / General"}" required />
        </label>
        <label class="preview-field">
          <span>Responsable</span>
          <input name="owner" type="text" value="${existingItem?.owner || "Operacion"}" required />
        </label>
        <label class="preview-field">
          <span>Precio objetivo</span>
          <input name="targetPrice" type="number" min="0" step="0.01" value="${existingItem?.targetPrice || 0}" required />
        </label>
        <label class="preview-field">
          <span>Margen esperado %</span>
          <input name="expectedMargin" type="number" min="0" max="100" step="0.01" value="${existingItem?.expectedMargin || 0}" required />
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
          <input name="description" type="text" value="${existingItem?.description || ""}" placeholder="Uso operativo del producto o servicio" required />
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
    unit: String(data.get("unit") || "").trim(),
    category: String(data.get("category") || "").trim(),
    center: String(data.get("center") || "").trim(),
    owner: String(data.get("owner") || "").trim(),
    standardCost: Number(existingItem?.standardCost || 0),
    targetPrice: Number(data.get("targetPrice") || 0),
    expectedMargin: Number(data.get("expectedMargin") || 0),
    status: String(data.get("status") || existingItem?.status || "Activo"),
    description: String(data.get("description") || "").trim(),
    createdAt: existingItem?.createdAt || new Date().toISOString().slice(0, 10),
    updatedAt: productServiceId ? new Date().toISOString().slice(0, 10) : ""
  };
}

function validateProductService(item) {
  const errors = [];
  if (!item.name) errors.push("Captura el nombre.");
  if (!item.sku) errors.push("Captura el SKU o codigo interno.");
  if (!item.unit) errors.push("Captura la unidad base.");
  if (!item.category) errors.push("Captura la categoria.");
  if (!item.center) errors.push("Captura el centro de costos.");
  if (!item.owner) errors.push("Captura el responsable.");
  if (!item.description) errors.push("Captura la descripcion.");
  return errors;
}

function saveProductServiceForm(event) {
  event.preventDefault();
  const item = buildProductServiceFromForm(event.currentTarget);
  const exists = Boolean(mockDb.findProductService(item.id));
  const errors = validateProductService(item);
  renderFormErrors(errors);
  if (errors.length) return;

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

function openLaborRoleModal(roleId = null, defaultArea = "") {
  const existingRole = roleId ? mockDb.findLaborRole(roleId) : null;
  const isEditing = Boolean(existingRole);
  const contextArea = defaultArea || localStorage.getItem("erclave-labor-selected-area") || "";
  const selectedArea = contextArea || "Costura";
  const lockAreaField = Boolean(contextArea && (!existingRole || existingRole.area === contextArea));
  modalContent.innerHTML = `
    <form class="recipe-form" id="laborRoleForm">
      <input type="hidden" name="roleId" value="${existingRole?.id || ""}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">${isEditing ? "Editar puesto" : "Nueva area y puesto"}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">x</button>
      </div>
      <div class="form-grid">
        <label class="preview-field"><span>Area</span><input name="area" type="text" value="${existingRole?.area || selectedArea}" ${lockAreaField ? "readonly" : ""} required /></label>
        <label class="preview-field"><span>Puesto o rol</span><input name="position" type="text" value="${existingRole?.position || ""}" placeholder="Ej. Costurero" required /></label>
        <label class="preview-field"><span>Nombre para receta</span><input name="name" type="text" value="${existingRole?.name || ""}" placeholder="Ej. Costurero senior" required /></label>
        <label class="preview-field"><span>Cantidad de recursos</span><input name="quantity" type="number" min="1" value="${existingRole?.quantity || 1}" required /></label>
        <label class="preview-field"><span>Minutos por recurso al dia</span><input name="minutesPerResource" type="number" min="1" value="${existingRole?.minutesPerResource || existingRole?.available || 480}" required /></label>
        <label class="preview-field"><span>Costo por minuto</span><input name="cost" type="number" min="0" step="0.01" value="${existingRole?.cost || "2.00"}" required /></label>
        <label class="preview-field"><span>Estatus</span><select name="status"><option ${existingRole?.status === "Activo" ? "selected" : ""}>Activo</option><option ${existingRole?.status === "Inactivo" ? "selected" : ""}>Inactivo</option></select></label>
      </div>
      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-labor-role">Cancelar</button>
        <button class="primary-action" type="submit">${isEditing ? "Actualizar puesto" : "Guardar puesto"}</button>
      </div>
    </form>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-labor-role']").addEventListener("click", closeModal);
  modalContent.querySelector("#laborRoleForm").addEventListener("submit", saveLaborRoleForm);
}

function saveLaborRoleForm(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const roleId = String(data.get("roleId") || "").trim();
  const name = String(data.get("name") || "").trim();
  const area = String(data.get("area") || "").trim();
  const position = String(data.get("position") || "").trim();
  const quantity = Math.max(1, Number(data.get("quantity") || 1));
  const minutesPerResource = Math.max(1, Number(data.get("minutesPerResource") || 1));
  const errors = [];
  if (!area) errors.push("Captura el area.");
  if (!position) errors.push("Captura el puesto o rol.");
  if (!name) errors.push("Captura el nombre para receta.");
  renderFormErrors(errors);
  if (errors.length) return;

  const item = {
    id: roleId || `mo_${slugify(name)}_${Date.now().toString().slice(-4)}`,
    name,
    area,
    position,
    quantity,
    minutesPerResource,
    unit: "min",
    available: quantity * minutesPerResource,
    cost: Number(data.get("cost") || 0),
    type: "Mano de obra",
    source: "Areas y puestos",
    status: String(data.get("status") || "Activo")
  };
  if (roleId) {
    mockDb.updateLaborRole(item);
  } else {
    mockDb.addLaborRole(item);
  }
  closeModal();
  navigateTo({ active: "produccion", activeSubmodule: "areas-puestos", laborArea: item.area });
  showToast(`Puesto ${item.name} ${roleId ? "actualizado" : "guardado"}.`);
}

function openMachineModal(machineId = null) {
  const existingMachine = machineId ? mockDb.findMachine(machineId) : null;
  const isEditing = Boolean(existingMachine);
  modalContent.innerHTML = `
    <form class="recipe-form" id="machineForm">
      <input type="hidden" name="machineId" value="${existingMachine?.id || ""}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">${isEditing ? "Editar maquina" : "Nueva maquina"}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">x</button>
      </div>
      <div class="form-grid">
        <label class="preview-field"><span>Area</span><input name="area" type="text" value="${existingMachine?.area || "Costura"}" required /></label>
        <label class="preview-field"><span>Tipo de maquina</span><input name="machineType" type="text" value="${existingMachine?.machineType || ""}" placeholder="Ej. Costura" required /></label>
        <label class="preview-field"><span>Nombre de maquina</span><input name="name" type="text" value="${existingMachine?.name || ""}" placeholder="Ej. Maquina recta 02" required /></label>
        <label class="preview-field"><span>Minutos disponibles por dia</span><input name="available" type="number" min="1" value="${existingMachine?.available || 480}" required /></label>
        <label class="preview-field"><span>Costo hora/minuto maquina</span><input name="cost" type="number" min="0" step="0.01" value="${existingMachine?.cost || "1.80"}" required /></label>
        <label class="preview-field"><span>Estatus</span><select name="status"><option ${existingMachine?.status === "Activo" ? "selected" : ""}>Activo</option><option ${existingMachine?.status === "Inactivo" ? "selected" : ""}>Inactivo</option><option ${existingMachine?.status === "Mantenimiento" ? "selected" : ""}>Mantenimiento</option></select></label>
      </div>
      <div class="form-errors" id="formErrors" hidden></div>
      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="close-machine">Cancelar</button>
        <button class="primary-action" type="submit">${isEditing ? "Actualizar maquina" : "Guardar maquina"}</button>
      </div>
    </form>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-machine']").addEventListener("click", closeModal);
  modalContent.querySelector("#machineForm").addEventListener("submit", saveMachineForm);
}

function saveMachineForm(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const machineId = String(data.get("machineId") || "").trim();
  const name = String(data.get("name") || "").trim();
  const area = String(data.get("area") || "").trim();
  const machineType = String(data.get("machineType") || "").trim();
  const errors = [];
  if (!area) errors.push("Captura el area.");
  if (!machineType) errors.push("Captura el tipo de maquina.");
  if (!name) errors.push("Captura el nombre de maquina.");
  renderFormErrors(errors);
  if (errors.length) return;

  const item = {
    id: machineId || `maq_${slugify(name)}_${Date.now().toString().slice(-4)}`,
    name,
    area,
    machineType,
    unit: "min",
    available: Number(data.get("available") || 0),
    cost: Number(data.get("cost") || 0),
    type: "Maquinaria",
    source: "Maquinaria",
    status: String(data.get("status") || "Activo")
  };
  if (machineId) {
    mockDb.updateMachine(item);
  } else {
    mockDb.addMachine(item);
  }
  closeModal();
  navigateTo({ active: "produccion", activeSubmodule: "maquinaria", laborArea: "" });
  showToast(`Maquina ${item.name} ${machineId ? "actualizada" : "guardada"}.`);
}

function openRecipeModal(recipeId = null) {
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
  const recipeResources = existingRecipe?.resources?.length
    ? existingRecipe.resources
    : ["tela_algodon", "hilo_morado", "etiqueta", "maquina_recta", "costurero"].map((id) => ({
        resourceId: id,
        quantity: suggestedQuantity(id)
      }));

  modalContent.innerHTML = `
    <form class="recipe-form" id="recipeForm">
      <input type="hidden" name="recipeId" value="${existingRecipe?.id || ""}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">${isEditing ? "Editar receta" : "Nueva receta"}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <div class="form-grid">
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
          <span>Unidad</span>
          <input name="unit" type="text" value="${existingRecipe?.unit || activeProductService?.unit || "pieza"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Centro de costos</span>
          <input name="center" type="text" value="${existingRecipe?.center || activeProductService?.center || "Produccion / Costura"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Cantidad para validar lote simulado</span>
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

      <p class="helper-copy">Solo puedes agregar recursos dados de alta previamente en Almacenes o Recursos Humanos. Este mock simula esos catalogos.</p>

      <div class="resource-picker">
        <select id="resourceSelect" aria-label="Seleccionar recurso">
          ${getRecipeResourceCatalog()
            .map(
              (resource) => `
                <option value="${resource.id}">
                  ${resource.name} · ${resource.type} · ${resource.source}
                </option>
              `
            )
            .join("")}
        </select>
        <button class="secondary-action" type="button" data-action="add-resource">Agregar recurso</button>
      </div>

      <div class="selected-resource-list" id="selectedResourceList">
        ${recipeResources
          .map((item) => renderSelectedResourceRow(item.resourceId, item.quantity))
          .join("")}
      </div>

      <label class="preview-field">
        <span>Etapas operativas genericas</span>
        <input name="steps" type="text" value="${existingRecipe?.steps?.join(", ") || "Preparacion, Ejecucion, Validacion, Entrega"}" />
      </label>

      <div class="form-errors" id="formErrors" hidden></div>

      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="preview-recipe">Validar recursos</button>
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
  modalContent.querySelector("[data-action='add-resource']").addEventListener("click", addResourceRow);
  modalContent.querySelector("[data-action='preview-recipe']").addEventListener("click", previewRecipeForm);
  modalContent.querySelector("#recipeForm").addEventListener("submit", saveRecipeForm);
  bindResourceRowActions();
}

function formatProductServiceOption(item) {
  return `${item.id} - ${item.name} - ${item.kind}`;
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
    [item.id, item.name, item.kind, item.category, item.center]
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
            <span>${item.id} - ${item.kind} - ${item.unit}</span>
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
  form.querySelector("[name='unit']").value = item.unit;
  form.querySelector("[name='center']").value = item.center;
  modalContent.querySelector("#recipeProductResults").hidden = true;
}

function syncRecipeProductFields(event) {
  const form = event.target.closest("form");
  const item = findProductServiceByOption(event.target.value);
  form.querySelector("[name='productServiceId']").value = item?.id || "";
  renderRecipeProductLookup(event);
  if (!item) return;
  form.querySelector("[name='unit']").value = item.unit;
  form.querySelector("[name='center']").value = item.center;
}

function renderSelectedResourceRow(resourceId, quantity = 0) {
  const resource = getResource(resourceId);
  if (!resource) return "";
  return `
    <div class="selected-resource-row" data-resource-row="${resource.id}">
      <div>
        <strong>${resource.name}</strong>
        <span>${resource.type} · ${resource.source} · disponible ${formatNumber(resource.available)} ${resource.unit}</span>
      </div>
      <label>
        <span>Cantidad</span>
        <input name="resource_${resource.id}" type="number" min="0" step="0.01" value="${quantity}" />
      </label>
      <button class="icon-button remove-resource" type="button" data-action="remove-resource" aria-label="Quitar recurso">×</button>
    </div>
  `;
}

function addResourceRow() {
  const select = modalContent.querySelector("#resourceSelect");
  const list = modalContent.querySelector("#selectedResourceList");
  const resourceId = select.value;
  if (list.querySelector(`[data-resource-row="${resourceId}"]`)) {
    showToast("Ese recurso ya esta en la receta.");
    return;
  }
  list.insertAdjacentHTML("beforeend", renderSelectedResourceRow(resourceId, 1));
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
    tela_algodon: 2,
    hilo_morado: 0.18,
    etiqueta: 1,
    tijeras: 0,
    maquina_recta: 30,
    costurero: 45
  };
  return defaults[resourceId] ?? 0;
}

function buildRecipeFromForm(form) {
  const data = new FormData(form);
  const recipeId = String(data.get("recipeId") || "").trim();
  const productServiceId = String(data.get("productServiceId") || "").trim();
  const productService = mockDb.findProductService(productServiceId);
  const selectedRows = [...form.querySelectorAll("[data-resource-row]")];
  const resources = selectedRows
    .map((row) => {
      const resourceId = row.dataset.resourceRow;
      return {
        resourceId,
        quantity: Number(data.get(`resource_${resourceId}`) || 0)
      };
    })
    .filter((item) => item.quantity > 0);

  return {
    id: recipeId || `REC-${Date.now().toString().slice(-5)}`,
    productServiceId,
    product: productService?.name || "",
    version: Number(data.get("version") || 1),
    quantityBase: Number(data.get("quantityBase") || 1),
    unit: String(data.get("unit") || "").trim(),
    status: String(data.get("approvalStatus") || "Borrador") === "Aprobada" ? "Activa" : "Borrador",
    approvalStatus: String(data.get("approvalStatus") || "Borrador"),
    approvedBy: String(data.get("approvalStatus") || "") === "Aprobada" ? "Usuario actual" : "",
    approvedAt: String(data.get("approvalStatus") || "") === "Aprobada" ? new Date().toISOString().slice(0, 10) : "",
    changeReason: String(data.get("changeReason") || "").trim(),
    center: String(data.get("center") || "").trim(),
    resources,
    steps: String(data.get("steps") || "")
      .split(",")
      .map((step) => step.trim())
      .filter(Boolean),
    createdAt: recipeId ? (mockDb.findRecipe(recipeId)?.createdAt || new Date().toISOString().slice(0, 10)) : new Date().toISOString().slice(0, 10)
  };
}

function validateRecipe(recipe) {
  const errors = [];
  if (!recipe.productServiceId || !recipe.product) errors.push("Selecciona un producto o servicio del catalogo.");
  if (!recipe.unit) errors.push("Captura la unidad base.");
  if (!recipe.center) errors.push("Selecciona o captura centro de costos.");
  if (!recipe.resources.length) errors.push("Agrega al menos un recurso con cantidad mayor a cero.");
  if (!recipe.steps.length) errors.push("Captura al menos una etapa.");
  return errors;
}

function renderFormErrors(errors) {
  const box = modalContent.querySelector("#formErrors");
  if (!errors.length) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  box.hidden = false;
  box.innerHTML = errors.map((error) => `<p>${error}</p>`).join("");
}

function previewRecipeForm() {
  const form = modalContent.querySelector("#recipeForm");
  const recipe = buildRecipeFromForm(form);
  const simulationQuantity = Math.max(1, Number(new FormData(form).get("simulationQuantity") || 1));
  const errors = validateRecipe(recipe);
  renderFormErrors(errors);
  if (errors.length) return;

  localStorage.setItem("erclave-validation-qty", simulationQuantity);
  const validation = calculateRecipe(recipe, simulationQuantity);
  modalContent.querySelector("#recipePreview").innerHTML = `
    <div class="validator-head">
      <div>
        <span class="muted-label">Lote simulado</span>
        <strong>${formatNumber(simulationQuantity)} ${recipe.unit} · ${formatCurrency(validation.totalCost)}</strong>
      </div>
      <span class="chip ${validation.missing.length ? "warning" : "active"}">
        ${validation.missing.length ? `${validation.missing.length} faltantes` : "Recursos suficientes"}
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
              <p>${formatNumber(row.required)} / ${formatNumber(row.available)} ${row.unit}</p>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function saveRecipeForm(event) {
  event.preventDefault();
  const recipe = buildRecipeFromForm(event.currentTarget);
  const errors = validateRecipe(recipe);
  renderFormErrors(errors);
  if (errors.length) return;

  const exists = Boolean(mockDb.findRecipe(recipe.id));
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
  showToast(`Receta ${recipe.id} ${exists ? "actualizada" : "guardada"} y validada contra almacen.`);
}

function approveRecipe(recipeId) {
  const recipe = mockDb.findRecipe(recipeId);
  if (!recipe) return;
  mockDb.updateRecipe({
    ...recipe,
    status: "Activa",
    approvalStatus: "Aprobada",
    approvedBy: "Usuario actual",
    approvedAt: new Date().toISOString().slice(0, 10)
  });
  render();
  showToast(`Receta ${recipe.id} aprobada para produccion.`);
}

function deleteRecipe(recipeId) {
  const recipe = mockDb.findRecipe(recipeId);
  if (!recipe) return;
  const hasOrders = mockDb.loadOrders().some((order) => order.recipeId === recipeId);
  if (hasOrders) {
    showToast(`Receta ${recipe.id} tiene ordenes relacionadas; no se puede eliminar.`);
    return;
  }
  const confirmed = window.confirm(`Eliminar la receta ${recipe.id} · ${recipe.product}?`);
  if (!confirmed) return;
  const recipes = mockDb.deleteRecipe(recipeId);
  if (localStorage.getItem("erclave-selected-recipe") === recipeId) {
    localStorage.setItem("erclave-selected-recipe", recipes[0]?.id || defaultRecipes[0].id);
  }
  render();
  showToast(`Receta ${recipe.id} eliminada.`);
}

function openOrderModal() {
  const recipes = mockDb.loadRecipes();
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe") || recipes[0]?.id;
  const recipe = recipes.find((item) => item.id === selectedRecipeId) || recipes[0] || defaultRecipes[0];
  const defaultQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);

  modalContent.innerHTML = `
    <form class="recipe-form" id="orderForm">
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">Generar orden de produccion</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <div class="form-grid">
        <label class="preview-field wide-field">
          <span>Receta</span>
          <select name="recipeId" id="orderRecipeSelect" required>
            ${recipes
              .map(
                (item) => `
                  <option value="${item.id}" ${item.id === recipe.id ? "selected" : ""}>
                    ${item.id} · ${item.product} · v${item.version} · ${getRecipeApprovalStatus(item)}
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
          <span>Fecha requerida</span>
          <input name="dueDate" type="date" value="2026-05-25" required />
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
          <input name="responsible" type="text" value="Mariana Torres" required />
        </label>
      </div>

      <div class="section-title form-section-title">
        <span class="section-icon">↳</span>
        <strong>Responsables por etapa operativa</strong>
      </div>
      <div class="area-assignment-list" id="areaAssignmentList">
        ${renderAreaAssignments(recipe)}
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
    const nextRecipe = mockDb.findRecipe(event.target.value) || defaultRecipes[0];
    modalContent.querySelector("#areaAssignmentList").innerHTML = renderAreaAssignments(nextRecipe);
  });
  modalContent.querySelector("[data-action='preview-order']").addEventListener("click", previewOrderForm);
  modalContent.querySelector("#orderForm").addEventListener("submit", saveOrderForm);
}

function renderAreaAssignments(recipe) {
  const defaults = ["Luis Perez", "Ana Ruiz", "Sofia Mendez", "Carlos Diaz", "Mariana Torres"];
  return (recipe.steps.length ? recipe.steps : ["Produccion"]).map((step, index) => `
    <label class="selected-resource-row area-assignment-row" data-area="${step}">
      <div>
        <strong>${step}</strong>
        <span>Etapa operativa generica de la orden</span>
      </div>
      <input name="area_${slugify(step)}" type="text" value="${defaults[index] || "Responsable"}" required />
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
  const recipe = mockDb.findRecipe(String(data.get("recipeId"))) || defaultRecipes[0];
  const quantity = Math.max(1, Number(data.get("quantity") || 1));
  const areas = (recipe.steps.length ? recipe.steps : ["Produccion"]).map((step) => ({
    area: step,
    responsible: String(data.get(`area_${slugify(step)}`) || "").trim(),
    status: "Pendiente",
    progress: 0,
    actualCostFactor: 1
  }));
  const release = getReleaseReview(recipe, quantity);
  const plannedCost = release.validation.totalCost;

  return {
    id: `OP-${Date.now().toString().slice(-5)}`,
    recipeId: recipe.id,
    recipeVersion: recipe.version,
    recipeSnapshot: createRecipeSnapshot(recipe),
    recipeName: recipe.product,
    quantity,
    unit: recipe.unit,
    status: "Liberada",
    priority: String(data.get("priority") || "Media"),
    dueDate: String(data.get("dueDate") || ""),
    center: recipe.center,
    responsible: String(data.get("responsible") || "").trim(),
    plannedCost,
    actualCost: plannedCost,
    releaseStatus: release.canRelease ? "Liberada" : "Bloqueada",
    areas,
    createdAt: new Date().toISOString().slice(0, 10)
  };
}

function validateOrder(order) {
  const errors = [];
  const recipe = getOrderRecipe(order);
  const release = getReleaseReview(recipe, order.quantity || 1);
  if (!order.recipeId) errors.push("Selecciona una receta.");
  if (!order.quantity) errors.push("Captura la cantidad.");
  if (!order.dueDate) errors.push("Captura fecha requerida.");
  if (!order.responsible) errors.push("Captura responsable general.");
  if (order.areas.some((area) => !area.responsible)) errors.push("Asigna responsable a cada etapa.");
  release.issues.forEach((issue) => errors.push(issue));
  return errors;
}

function previewOrderForm() {
  const form = modalContent.querySelector("#orderForm");
  const order = buildOrderFromForm(form);
  const errors = validateOrder(order);
  renderFormErrors(errors);
  if (errors.length) return;
  const recipe = getOrderRecipe(order);
  const release = getReleaseReview(recipe, order.quantity);
  const validation = release.validation;
  modalContent.querySelector("#orderPreview").innerHTML = `
    <div class="validator-head">
      <div>
        <span class="muted-label">Orden simulada</span>
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

function saveOrderForm(event) {
  event.preventDefault();
  const order = buildOrderFromForm(event.currentTarget);
  const errors = validateOrder(order);
  renderFormErrors(errors);
  if (errors.length) return;
  mockDb.addOrder(order);
  localStorage.setItem("erclave-selected-recipe", order.recipeId);
  localStorage.setItem("erclave-validation-qty", order.quantity);
  closeModal();
  render();
  showToast(`Orden ${order.id} generada en produccion.`);
  openOrderPrintModal(order.id);
}

function advanceOrderStatus(orderId) {
  const order = mockDb.findOrder(orderId);
  if (!order) return;
  const next = orderStatusCatalog[(orderStatusCatalog.indexOf(order.status) + 1) % orderStatusCatalog.length];
  mockDb.updateOrder({ ...order, status: next });
  render();
  showToast(`Orden ${order.id} ahora esta en ${next}.`);
}

function changeOrderStatus(orderId, status) {
  const order = mockDb.findOrder(orderId);
  if (!order || !orderStatusCatalog.includes(status)) return;
  mockDb.updateOrder({ ...order, status });
  render();
  showToast(`Orden ${order.id} ahora esta en ${status}.`);
}

function advanceOrderStage(orderId, stageIndex) {
  const order = mockDb.findOrder(orderId);
  if (!order || !order.areas?.[stageIndex]) return;
  const stages = order.areas.map((stage, index) => {
    if (index !== stageIndex) return stage;
    const nextStatus = stage.status === "Pendiente" ? "En proceso" : stage.status === "En proceso" ? "Terminada" : "Pendiente";
    const progress = nextStatus === "Terminada" ? 100 : nextStatus === "En proceso" ? Math.max(50, Number(stage.progress || 0)) : 0;
    return {
      ...stage,
      status: nextStatus,
      progress,
      actualCostFactor: Number(stage.actualCostFactor || 1)
    };
  });
  const allDone = stages.every((stage) => stage.status === "Terminada");
  const anyActive = stages.some((stage) => stage.status === "En proceso");
  mockDb.updateOrder({
    ...order,
    areas: stages,
    status: allDone ? "Terminada" : anyActive ? "En produccion" : order.status
  });
  render();
  showToast(`${order.id} actualizo la etapa ${order.areas[stageIndex].area}.`);
}

function openOrderPrintModal(orderId) {
  const order = mockDb.findOrder(orderId);
  if (!order) return;
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

      <section class="print-area" id="printArea">
        <div class="print-header">
          <div>
            <strong>ERClave Produccion</strong>
            <span>Orden de produccion</span>
          </div>
          <h1>${order.id}</h1>
        </div>
        <div class="print-grid">
          <p><strong>Producto:</strong> ${order.recipeName}</p>
          <p><strong>Receta:</strong> ${recipe.id} · v${recipe.version}</p>
          <p><strong>Cantidad:</strong> ${order.quantity} ${order.unit}</p>
          <p><strong>Estado:</strong> ${order.status}</p>
          <p><strong>Prioridad:</strong> ${order.priority}</p>
          <p><strong>Fecha requerida:</strong> ${order.dueDate}</p>
          <p><strong>Responsable:</strong> ${order.responsible}</p>
          <p><strong>Centro:</strong> ${order.center}</p>
          <p><strong>Costo planeado:</strong> ${formatCurrency(cost.plannedCost)}</p>
          <p><strong>Costo real:</strong> ${formatCurrency(cost.actualCost)}</p>
        </div>
        <h3>Seguimiento por etapa operativa</h3>
        <table>
          <thead>
            <tr><th>Etapa</th><th>Responsable</th><th>Estado</th><th>Avance</th></tr>
          </thead>
          <tbody>
            ${order.areas.map((area) => `<tr><td>${area.area}</td><td>${area.responsible}</td><td>${area.status}</td><td>${formatNumber(area.progress || (area.status === "Terminada" ? 100 : 0))}%</td></tr>`).join("")}
          </tbody>
        </table>
        <h3>Recursos calculados</h3>
        <table>
          <thead>
            <tr><th>Recurso</th><th>Tipo</th><th>Requerido</th><th>Disponible</th></tr>
          </thead>
          <tbody>
            ${validation.rows.map((row) => `<tr><td>${row.name}</td><td>${row.type}</td><td>${formatNumber(row.required)} ${row.unit}</td><td>${formatNumber(row.available)} ${row.unit}</td></tr>`).join("")}
          </tbody>
        </table>
        <p class="print-total"><strong>Costo estimado:</strong> ${formatCurrency(validation.totalCost)}</p>
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

function openSalesQuotePrintModal(quoteId) {
  const quote = mockDb.findModuleRecord("ventas", quoteId);
  if (!quote) return;
  const customer = quote.fields?.customerId ? mockDb.findModuleRecord("ventas", quote.fields.customerId) : null;
  const lines = getQuoteLines(quote);
  modalContent.innerHTML = `
    <div class="recipe-form print-modal">
      <div class="modal-head no-print">
        <div>
          <p class="eyebrow">${t("newQuote")}</p>
          <h2>${quote.code}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="${t("close")}">x</button>
      </div>

      <section class="print-area" id="printArea">
        <div class="print-header">
          <div>
            <strong>ERClave Ventas</strong>
            <span>${t("quoteDocument")}</span>
          </div>
          <h1>${quote.code}</h1>
        </div>
        <div class="print-grid">
          <p><strong>${t("customer")}:</strong> ${quote.fields?.customerName || t("notDefined")}</p>
          <p><strong>${t("status")}:</strong> ${translateStatus(quote.status)}</p>
          <p><strong>${t("validUntil")}:</strong> ${quote.fields?.validUntil || t("notDefined")}</p>
          <p><strong>${t("deliveryPromise")}:</strong> ${quote.fields?.deliveryPromise || t("notDefined")}</p>
          <p><strong>${t("paymentTerms")}:</strong> ${quote.fields?.paymentTerms || t("notDefined")}</p>
          <p><strong>${t("currency")}:</strong> ${quote.fields?.currency || "MXN"}</p>
          <p><strong>${t("billingLegalName")}:</strong> ${customer?.fields?.billingLegalName || t("notDefined")}</p>
          <p><strong>${t("taxId")}:</strong> ${customer?.fields?.taxId || t("notDefined")}</p>
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
                <td>${line.productServiceName}</td>
                <td>${formatNumber(line.quantity)} ${line.unit}</td>
                <td>${formatCurrency(Number(line.unitPrice || 0))}</td>
                <td>${formatNumber(Number(line.discount || 0))}%</td>
                <td>${formatCurrency(Number(line.total || 0))}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
        ${quote.fields?.notes ? `<p><strong>${t("notes")}:</strong> ${quote.fields.notes}</p>` : ""}
        <p class="print-total"><strong>${t("quoteSubtotal")}:</strong> ${formatCurrency(Number(quote.fields?.subtotal || 0))}</p>
        <p class="print-total"><strong>${t("quoteTotal")}:</strong> ${formatCurrency(Number(quote.fields?.total || 0))}</p>
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
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = dict[node.dataset.i18n] || node.textContent;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = dict[node.dataset.i18nPlaceholder] || node.placeholder;
  });
  langToggle.querySelector(".icon").textContent = state.lang.toUpperCase();
}

function render() {
  shell.dataset.theme = state.theme;
  document.body.dataset.theme = state.theme;
  backButton.disabled = !state.history.length;
  topbarPrimary.querySelector("[data-i18n]").dataset.i18n = state.active === "produccion" ? "newOrder" : "newModuleRecord";
  renderNav();
  renderPanel();
  renderFlow();
  applyI18n();
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

modalBackdrop.addEventListener("click", (event) => {
  if (event.target === modalBackdrop) closeModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modalBackdrop.hidden) closeModal();
});

topbarPrimary.addEventListener("click", () => {
  if (state.active === "produccion") {
    openOrderModal();
    return;
  }
  openGenericRecordModal(state.active, state.activeSubmodule);
});

render();
