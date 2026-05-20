import { modules, erpSubmoduleCatalog } from "./data/modules.js";
import { resourceCatalog, defaultRecipes } from "./data/resources.js";
import { mockDb } from "./data/mockDb.js";
import { translations } from "./i18n/translations.js";
import { calculateRecipe, getProductionModuleData, getResource } from "./utils/production.js";
import { diffDays, formatCurrency, formatNumber, startOfDay } from "./utils/format.js";

const state = {
  active: modules[0].id,
  activeSubmodule: null,
  theme: localStorage.getItem("erclave-theme") || "light",
  lang: localStorage.getItem("erclave-lang") || "es"
};

const shell = document.querySelector(".app-shell");
const moduleNav = document.getElementById("moduleNav");
const modulePanel = document.getElementById("modulePanel");
const flowList = document.getElementById("flowList");
const notificationSummary = document.getElementById("notificationSummary");
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
      state.active = button.dataset.moduleRoot;
      state.activeSubmodule = null;
      render();
    });
  });

  moduleNav.querySelectorAll("[data-submodule-nav]").forEach((button) => {
    button.addEventListener("click", () => {
      state.active = button.dataset.module;
      state.activeSubmodule = button.dataset.submoduleNav;
      render();
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
    state.activeSubmodule = null;
    render();
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
    state.activeSubmodule = null;
    render();
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
  return actions[id] || "";
}

function renderProductionSubmoduleBody(id) {
  const recipes = mockDb.loadRecipes();
  const orders = mockDb.loadOrders();
  if (id === "productos-servicios") return renderProductsServicesScreen(recipes);
  if (id === "recetas") return renderRecipesScreen(recipes);
  if (id === "ordenes") return renderOrdersScreen(orders);
  if (id === "entregables") return renderDeliverablesScreen(orders);
  if (id === "validacion-recursos") return renderValidationScreen(recipes);
  return "";
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
  return `
    <div class="submodule-layout">
      ${renderRecipeList(recipes)}
      <section class="section-card">
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

function renderOrdersScreen(orders) {
  return `
    <div class="submodule-layout">
      <section>
        ${renderOrderList(orders)}
      </section>
      <section class="section-card">
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
    <div class="deliverable-board">
      ${deliverables.map((item) => `
        <article class="deliverable-card">
          <div>
            <span class="muted-label">${item.order} · ${item.quantity}</span>
            <strong>${item.area}</strong>
            <p>${item.product}</p>
          </div>
          <div>
            <span>${item.responsible}</span>
            <span class="chip ${item.status === "En proceso" ? "warning" : ""}">${translateStatus(item.status)}</span>
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

function renderValidationScreen(recipes) {
  return `
    <section class="section-card">
      <p class="helper-copy">${t("validationScreenHelper")}</p>
      ${renderRecipeValidationOnly(recipes)}
    </section>
  `;
}

function bindProductionPanelActions() {
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
  modulePanel.querySelectorAll("[data-action='edit-recipe']").forEach((button) => {
    button.addEventListener("click", () => openRecipeModal(button.dataset.recipeId));
  });
  modulePanel.querySelectorAll("[data-action='delete-recipe']").forEach((button) => {
    button.addEventListener("click", () => deleteRecipe(button.dataset.recipeId));
  });
  modulePanel.querySelectorAll("[data-action='print-order']").forEach((button) => {
    button.addEventListener("click", () => openOrderPrintModal(button.dataset.orderId));
  });
  modulePanel.querySelectorAll("[data-action='advance-order']").forEach((button) => {
    button.addEventListener("click", () => advanceOrderStatus(button.dataset.orderId));
  });
  modulePanel.querySelectorAll("[data-submodule]").forEach((button) => {
    button.addEventListener("click", () => {
      state.active = button.dataset.module || state.active;
      state.activeSubmodule = button.dataset.submodule;
      render();
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
  const validation = calculateRecipe(recipe, validationQuantity);

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
        <span class="chip ${validation.missing.length ? "warning" : "active"}">
          ${validation.missing.length ? "Faltantes detectados" : "Lista para producir"}
        </span>
      </div>
      <p class="helper-copy">La validacion multiplica los recursos de la receta por la cantidad indicada. Materiales, herramientas y maquinaria vienen de Almacenes; mano de obra viene de Recursos Humanos.</p>
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
          .map((order) => `
            <article class="recipe-list-row order-list-row">
              <div>
                <strong>${order.id} · ${order.recipeName}</strong>
                <span>${order.quantity} ${order.unit} · entrega ${order.dueDate || "sin fecha"} · responsable ${order.responsible}</span>
              </div>
              <span class="chip ${order.status === "Terminada" ? "active" : "warning"}">${order.status}</span>
              <div class="row-actions">
                <button class="secondary-action small-action" type="button" data-action="advance-order" data-order-id="${order.id}">Estatus</button>
                <button class="secondary-action small-action" type="button" data-action="print-order" data-order-id="${order.id}">PDF/Imprimir</button>
              </div>
            </article>
          `)
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
            return `
              <article class="recipe-list-row">
                <div>
                  <strong>${recipe.id} · ${recipe.product}</strong>
                  <span>v${recipe.version} · ${recipe.resources.length} recursos · ${recipe.steps.length} etapas · ${formatCurrency(validation.totalCost)}</span>
                </div>
                <span class="chip ${validation.missing.length ? "warning" : "active"}">
                  ${validation.missing.length ? `${validation.missing.length} faltantes` : "Validada"}
                </span>
                <div class="row-actions">
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
    state.active = "produccion";
    state.activeSubmodule = "ordenes";
    render();
  });
}

function buildNotifications() {
  const today = startOfDay(new Date());
  const orders = mockDb.loadOrders();
  const items = [];
  let overdue = 0;
  let dueSoon = 0;
  let missingResources = 0;

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
    "En produccion": { es: "En produccion", en: "In production" },
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

function openRecipeModal(recipeId = null) {
  const existingRecipe = recipeId ? mockDb.findRecipe(recipeId) : null;
  const isEditing = Boolean(existingRecipe);
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
        <label class="preview-field">
          <span>Producto o servicio</span>
          <input name="product" type="text" placeholder="Ej. Playera premium" value="${existingRecipe?.product || ""}" required />
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
          <input name="unit" type="text" value="${existingRecipe?.unit || "pieza"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Centro de costos</span>
          <input name="center" type="text" value="${existingRecipe?.center || "Produccion / Costura"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Cantidad para validar lote simulado</span>
          <input name="simulationQuantity" type="number" min="1" value="${localStorage.getItem("erclave-validation-qty") || 100}" required />
        </label>
      </div>

      <div class="section-title form-section-title">
        <span class="section-icon">▦</span>
        <strong>Recursos por unidad</strong>
      </div>

      <p class="helper-copy">Solo puedes agregar recursos dados de alta previamente en Almacenes o Recursos Humanos. Este mock simula esos catalogos.</p>

      <div class="resource-picker">
        <select id="resourceSelect" aria-label="Seleccionar recurso">
          ${resourceCatalog
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
        <span>Etapas</span>
        <input name="steps" type="text" value="${existingRecipe?.steps?.join(", ") || "Corte, Costura, Calidad, Empaque"}" />
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
  modalContent.querySelector("[data-action='add-resource']").addEventListener("click", addResourceRow);
  modalContent.querySelector("[data-action='preview-recipe']").addEventListener("click", previewRecipeForm);
  modalContent.querySelector("#recipeForm").addEventListener("submit", saveRecipeForm);
  bindResourceRowActions();
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
    product: String(data.get("product") || "").trim(),
    version: Number(data.get("version") || 1),
    quantityBase: Number(data.get("quantityBase") || 1),
    unit: String(data.get("unit") || "").trim(),
    status: recipeId ? (mockDb.findRecipe(recipeId)?.status || "Activa") : "Borrador",
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
  if (!recipe.product) errors.push("Captura el producto o servicio.");
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

  recipe.status = "Activa";
  const exists = Boolean(mockDb.findRecipe(recipe.id));
  if (exists) {
    mockDb.updateRecipe(recipe);
  } else {
    mockDb.addRecipe(recipe);
  }
  localStorage.setItem("erclave-selected-recipe", recipe.id);
  closeModal();
  state.active = "produccion";
  render();
  showToast(`Receta ${recipe.id} ${exists ? "actualizada" : "guardada"} y validada contra almacen.`);
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
                    ${item.id} · ${item.product} · v${item.version}
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
        <strong>Responsables por area</strong>
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
        <span>Entregable operativo por area</span>
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
    status: "Pendiente"
  }));

  return {
    id: `OP-${Date.now().toString().slice(-5)}`,
    recipeId: recipe.id,
    recipeName: recipe.product,
    quantity,
    unit: recipe.unit,
    status: "En produccion",
    priority: String(data.get("priority") || "Media"),
    dueDate: String(data.get("dueDate") || ""),
    center: recipe.center,
    responsible: String(data.get("responsible") || "").trim(),
    areas,
    createdAt: new Date().toISOString().slice(0, 10)
  };
}

function validateOrder(order) {
  const errors = [];
  if (!order.recipeId) errors.push("Selecciona una receta.");
  if (!order.quantity) errors.push("Captura la cantidad.");
  if (!order.dueDate) errors.push("Captura fecha requerida.");
  if (!order.responsible) errors.push("Captura responsable general.");
  if (order.areas.some((area) => !area.responsible)) errors.push("Asigna responsable a cada area.");
  return errors;
}

function previewOrderForm() {
  const form = modalContent.querySelector("#orderForm");
  const order = buildOrderFromForm(form);
  const errors = validateOrder(order);
  renderFormErrors(errors);
  if (errors.length) return;
  const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
  const validation = calculateRecipe(recipe, order.quantity);
  modalContent.querySelector("#orderPreview").innerHTML = `
    <div class="validator-head">
      <div>
        <span class="muted-label">Orden simulada</span>
        <strong>${order.quantity} ${order.unit} · ${formatCurrency(validation.totalCost)}</strong>
      </div>
      <span class="chip ${validation.missing.length ? "warning" : "active"}">
        ${validation.missing.length ? `${validation.missing.length} faltantes` : "Lista para produccion"}
      </span>
    </div>
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
  const statuses = ["En produccion", "Pausada", "Terminada", "Cancelada"];
  const next = statuses[(statuses.indexOf(order.status) + 1) % statuses.length];
  mockDb.updateOrder({ ...order, status: next });
  render();
  showToast(`Orden ${order.id} ahora esta en ${next}.`);
}

function openOrderPrintModal(orderId) {
  const order = mockDb.findOrder(orderId);
  if (!order) return;
  const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
  const validation = calculateRecipe(recipe, order.quantity);
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
        </div>
        <h3>Responsables por area</h3>
        <table>
          <thead>
            <tr><th>Area</th><th>Responsable</th><th>Estado</th></tr>
          </thead>
          <tbody>
            ${order.areas.map((area) => `<tr><td>${area.area}</td><td>${area.responsible}</td><td>${area.status}</td></tr>`).join("")}
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
  renderNav();
  renderPanel();
  renderFlow();
  applyI18n();
}

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
