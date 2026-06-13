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

function renderNav() {
  moduleNav.innerHTML = modules
    .map((module) => {
      const label = state.lang === "en" ? module.titleEn : module.title;
      return `
        <div class="nav-group ${module.id === state.active ? "open" : ""}">
          <button class="nav-button ${module.id === state.active && !state.activeSubmodule ? "active" : ""}" type="button" data-module-root="${module.id}" title="${label}">
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
      navigateTo({ active: button.dataset.moduleRoot, activeSubmodule: null, laborArea: "" });
    });
  });

  moduleNav.querySelectorAll("[data-submodule-nav]").forEach((button) => {
    button.addEventListener("click", () => {
      navigateTo({ active: button.dataset.module, activeSubmodule: button.dataset.submoduleNav, laborArea: "" });
    });
  });
}

function renderSubnav(module) {
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

function renderPanel() {
  const module = { ...(modules.find((item) => item.id === state.active) || modules[0]) };
  if (module.id === "produccion") {
    const production = getProductionModuleData();
    module.table = { ...module.table, rows: production.rows };
    module.records = production.records;
    module.kpis = [
      ["Ordenes activas", String(mockDb.loadOrders().filter((order) => order.status === "En produccion").length), "positive"],
      ["Faltantes", String(production.validation.missing.length), production.validation.missing.length ? "warning" : "positive"],
      [`Costo lote ${Number(localStorage.getItem("erclave-validation-qty") || 100)}`, formatCurrency(production.validation.totalCost), "positive"]
    ];
    if (state.activeSubmodule) {
      renderProductionSubmodulePanel(module);
      return;
    }
  } else if (state.activeSubmodule) {
    renderGenericSubmodulePanel(module);
    return;
  }
  const label = state.lang === "en" ? module.titleEn : module.title;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${module.eyebrow}</p>
        <h2>${label}</h2>
      </div>
      <span class="chip active">${module.status}</span>
    </div>

    <div class="module-summary expanded">
      <div class="module-hero">
        <h1>${label}</h1>
        <p>${module.summary}</p>
        <button class="primary-action hero-action" type="button" data-action="${module.id === "produccion" ? "open-order" : "module-primary"}">
          <span>＋</span>
          <span>${module.primary}</span>
        </button>
      </div>

      <div class="module-kpis">
        ${module.kpis
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
          ${module.workflow.map((step) => `<li>${step}</li>`).join("")}
        </ol>
      </section>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">✓</span>
          <strong>${t("compatibility")}</strong>
        </div>
        <div class="compat-list">
          ${module.validations
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
            ${module.table.columns.map((column) => `<span role="columnheader">${column}</span>`).join("")}
          </div>
          ${module.table.rows
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
        ${module.form
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
      ${module.records
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
  const sampleRows = buildGenericSubmoduleRows(module, submodule);
  const columns = getGenericSubmoduleColumns(module);
  const formFields = getGenericSubmoduleForm(module, submodule);
  const integrations = getGenericSubmoduleIntegrations(module);
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
        <button class="primary-action" type="button" data-action="module-primary">
          <span>＋</span>
          <span>${t("openForm")}</span>
        </button>
      </div>

      <div class="submodule-layout">
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
            ${module.workflow.slice(0, 5).map((step) => `<li>${step}</li>`).join("")}
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

function getGenericSubmodule(module, id) {
  return normalizeSubmodules(module).find((item) => item.id === id) || normalizeSubmodules(module)[0];
}

function buildGenericSubmoduleRows(module, submodule) {
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
  if (state.lang === "en") {
    return [
      [submodule.id.toUpperCase(), submodule.detail, t("recommendedRecords")],
      [`${module.icon}-FLOW`, "Suggested operating flow and validations.", "Ready"],
      [`${module.icon}-SYNC`, "Recommended integration with related modules.", "Draft"]
    ];
  }
  return module.records.length ? module.records : [[submodule.id.toUpperCase(), submodule.detail, t("recommendedRecords")]];
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
            const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
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
    const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
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
    "En proceso": { es: "En proceso", en: "In progress" }
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
  const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
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
  const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
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
  const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
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
  showToast("Este mock de captura inicia con recetas de Produccion.");
});

render();
