import { resourceCatalog, defaultRecipes } from "../data/resources.js";
import { mockDb } from "../data/mockDb.js";
import { getApiMode } from "../api/config.js";

function shouldUseSeedData() {
  return getApiMode() !== "api";
}

let inventoryRecipeResources = [];
let laborRecipeResources = [];
let machineRecipeResources = [];

export function setInventoryRecipeResources(resources) {
  inventoryRecipeResources = Array.isArray(resources) ? resources : [];
}

export function setLaborRecipeResources(resources) {
  laborRecipeResources = Array.isArray(resources) ? resources : [];
}

export function setMachineRecipeResources(resources) {
  machineRecipeResources = Array.isArray(resources) ? resources : [];
}

export function getResource(id) {
  return getRecipeResourceCatalog().find((item) => item.id === id);
}

export function getRecipeResourceCatalog() {
  const inventoryResources = shouldUseSeedData() ? resourceCatalog : inventoryRecipeResources;
  if (!shouldUseSeedData()) return [...inventoryResources, ...laborRecipeResources, ...machineRecipeResources];
  return [
    ...inventoryResources,
    ...mockDb.loadLaborRoles().filter((item) => item.status === "Activo" && item.intervenesInProduction !== false),
    ...mockDb.loadMachines().filter((item) => item.status === "Activo")
  ];
}

export function calculateRecipe(recipe, batchQuantity = 100) {
  const safeRecipe = recipe && typeof recipe === "object" ? recipe : {};
  const resources = Array.isArray(safeRecipe.resources) ? safeRecipe.resources : [];
  const baseQuantity = Math.max(1, Number(safeRecipe.quantityBase || 1));
  const multiplier = Number(batchQuantity || 1) / baseQuantity;
  const rows = resources.map((item) => {
    const resource = getResource(item.resourceId);
    const required = Number(item.quantity) * multiplier;
    const available = resource?.available || 0;
    const cost = required * Number(item.unitCost ?? resource?.cost ?? 0);
    return {
      name: resource?.name || item.resourceName || item.resourceId,
      unit: resource?.unit || item.unit || "",
      type: resource?.type || item.resourceType || "",
      source: resource?.source || "",
      required,
      available,
      cost,
      ok: available >= required
    };
  });

  return {
    rows,
    totalCost: rows.reduce((sum, row) => sum + row.cost, 0),
    missing: rows.filter((row) => !row.ok)
  };
}

export function validateRecipeDefinition(recipe, batchQuantity = 100) {
  const safeRecipe = recipe && typeof recipe === "object" ? recipe : {};
  const resources = Array.isArray(safeRecipe.resources) ? safeRecipe.resources : [];
  const baseQuantity = Math.max(1, Number(safeRecipe.quantityBase || 1));
  const multiplier = Number(batchQuantity || 1) / baseQuantity;
  const rows = resources.map((item) => {
    const resource = getResource(item.resourceId);
    const required = Number(item.quantity) * multiplier;
    const eligible = Boolean(resource) && resource.unitActive !== false;
    return {
      name: resource?.name || item.resourceName || item.resourceId,
      unit: resource?.unit || item.unit || "",
      type: resource?.type || item.resourceType || "",
      source: resource?.source || "Fuera del catalogo elegible",
      required,
      cost: required * Number(item.unitCost ?? resource?.cost ?? 0),
      ok: eligible
    };
  });
  return {
    rows,
    totalCost: rows.reduce((sum, row) => sum + row.cost, 0),
    missing: rows.filter((row) => !row.ok)
  };
}

export function getRecipeApprovalStatus(recipe) {
  return recipe.approvalStatus || (recipe.status === "Activa" ? "Aprobada" : "Borrador");
}

export function isRecipeApproved(recipe) {
  return getRecipeApprovalStatus(recipe) === "Aprobada";
}

export function getRecipeStandardCost(recipe) {
  const baseQuantity = Math.max(1, Number(recipe.quantityBase || 1));
  return calculateRecipe(recipe, baseQuantity).totalCost / baseQuantity;
}

export function getOrderCostSnapshot(order, recipe) {
  const plannedCost = Number(order.plannedCost ?? calculateRecipe(recipe, order.quantity).totalCost);
  const actualCost = order.actualCost == null ? null : Number(order.actualCost);
  return {
    plannedCost,
    actualCost,
    variance: actualCost == null ? null : actualCost - plannedCost,
    variancePct: actualCost == null ? null : plannedCost ? ((actualCost - plannedCost) / plannedCost) * 100 : 0
  };
}

export function getOrderProgressFactor(order) {
  const stages = order.areas || [];
  if (!stages.length) return 1;
  const avgFactor = stages.reduce((sum, stage) => sum + Number(stage.actualCostFactor || 1), 0) / stages.length;
  return avgFactor;
}

export function getOrderProgress(order) {
  const stages = order.areas || [];
  if (!stages.length) return 0;
  return stages.reduce((sum, stage) => sum + Number(stage.progress || (stage.status === "Terminada" ? 100 : 0)), 0) / stages.length;
}

export function getReleaseReview(recipe, quantity) {
  const validation = calculateRecipe(recipe, quantity);
  const issues = [];
  if (!isRecipeApproved(recipe)) issues.push("Receta pendiente de aprobacion");
  validation.missing.forEach((row) => issues.push(`Falta ${row.name}`));
  return {
    validation,
    canRelease: !issues.length,
    issues
  };
}

export function getProductionModuleData() {
  const recipes = mockDb.loadRecipes();
  const orders = mockDb.loadOrders();
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe");
  const activeRecipe = recipes.find((recipe) => recipe.id === selectedRecipeId) || recipes[0] || (shouldUseSeedData() ? defaultRecipes[0] : null);
  const validationQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);
  const validation = activeRecipe ? calculateRecipe(activeRecipe, validationQuantity) : { rows: [], totalCost: 0, missing: [] };

  if (!activeRecipe) {
    return {
      records: [],
      rows: [],
      validation
    };
  }

  return {
    records: [
      ...orders.slice(0, 2).map((order) => [
        order.id,
        `${order.recipeName} · ${order.quantity} ${order.unit}`,
        order.status
      ]),
      ...recipes.slice(0, 3).map((recipe) => [
        recipe.id,
        `${recipe.product} · version ${recipe.version}`,
        recipe.status
      ]),
      [
        "VAL-REC",
        validation.missing.length
          ? `${activeRecipe.product} · ${validation.missing.length} recursos faltantes`
          : `${activeRecipe.product} · recursos suficientes`,
        validation.missing.length ? "Faltante" : "Validada"
      ]
    ],
    rows: [
      ...orders.slice(0, 4).map((order) => {
        const recipe = recipes.find((item) => item.id === order.recipeId) || activeRecipe;
        const calc = calculateRecipe(recipe, order.quantity);
        return [
          order.id,
          `${order.recipeName} · ${order.quantity} ${order.unit}`,
          order.status,
          calc.missing.length ? `${calc.missing.length} faltantes` : "Sin riesgo"
        ];
      })
    ],
    validation
  };
}
