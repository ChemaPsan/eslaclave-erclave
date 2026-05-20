import { resourceCatalog, defaultRecipes } from "../data/resources.js";
import { mockDb } from "../data/mockDb.js";

export function getResource(id) {
  return resourceCatalog.find((item) => item.id === id);
}

export function calculateRecipe(recipe, batchQuantity = 100) {
  const rows = recipe.resources.map((item) => {
    const resource = getResource(item.resourceId);
    const required = Number(item.quantity) * batchQuantity;
    const available = resource?.available || 0;
    const cost = required * (resource?.cost || 0);
    return {
      name: resource?.name || item.resourceId,
      unit: resource?.unit || "",
      type: resource?.type || "",
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

export function getProductionModuleData() {
  const recipes = mockDb.loadRecipes();
  const orders = mockDb.loadOrders();
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe");
  const activeRecipe = recipes.find((recipe) => recipe.id === selectedRecipeId) || recipes[0] || defaultRecipes[0];
  const validationQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);
  const validation = calculateRecipe(activeRecipe, validationQuantity);

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
