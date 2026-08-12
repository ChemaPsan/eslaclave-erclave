const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "../..");
const app = fs.readFileSync(path.join(root, "frontend/app.js"), "utf8");
const movementFlow = app.split("async function saveInventoryMovementForm", 2)[1]?.split("function openSalesCustomerModal", 1)[0] || "";
const recipeFlow = app.split("async function saveRecipeForm", 2)[1]?.split("async function approveRecipe", 1)[0] || "";
const errors = [];

for (const token of [
  'getApiMode() === "api" && isInventoryApiEnabled()',
  "await createInventoryMovement(",
  'state.inventoryMovements = { status: "idle", error: "" }',
  'state.inventoryBalances = { status: "idle"',
  "await loadInventoryMovementData()"
]) {
  if (!movementFlow.includes(token)) errors.push(`Inventory movement API flow is missing: ${token}`);
}

if (movementFlow.indexOf("await createInventoryMovement(") > movementFlow.indexOf("mockDb.addModuleRecord")) {
  errors.push("Inventory API persistence must run before the mock-only fallback.");
}
if (recipeFlow.includes("createInventoryMovement")) {
  errors.push("Recipe persistence must not contain the inventory movement command.");
}

if (errors.length) {
  console.error(errors.map((error) => `[ERROR] ${error}`).join("\n"));
  process.exit(1);
}

console.log("[OK] Inventory movements persist through Inventory API and invalidate calculated balances.");
