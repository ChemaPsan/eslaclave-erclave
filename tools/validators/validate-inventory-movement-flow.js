const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "../..");
const app = fs.readFileSync(path.join(root, "frontend/app.js"), "utf8");
const movementFlow = app.split("async function saveInventoryMovementForm", 2)[1]?.split("function openSalesCustomerModal", 1)[0] || "";
const itemFlow = app.split("async function saveInventoryItemForm", 2)[1]?.split("function openInventoryMovementModal", 1)[0] || "";
const recipeFlow = app.split("async function saveRecipeForm", 2)[1]?.split("async function approveRecipe", 1)[0] || "";
const inventoryRepository = fs.readFileSync(path.join(root, "backend/services/inventory-service/app/repositories.py"), "utf8");
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
if (!itemFlow.includes('errorCode === "item_base_unit_locked_by_movements"')) {
  errors.push("Inventory item editing must translate the protected base-unit conflict into an actionable message.");
}
if (!itemFlow.includes('t("itemBaseUnitLockedByHistory")')) {
  errors.push("Inventory item editing must use the localized protected base-unit message.");
}
if (!inventoryRepository.includes("stored_quantity,next_status,remaining=reservation_consumption_state")) {
  errors.push("Full reservation consumption must preserve a positive quantity snapshot before setting status consumed.");
}

if (errors.length) {
  console.error(errors.map((error) => `[ERROR] ${error}`).join("\n"));
  process.exit(1);
}

console.log("[OK] Inventory movements persist through Inventory API and invalidate calculated balances.");
