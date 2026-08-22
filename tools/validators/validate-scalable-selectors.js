const { fail, ok, readText } = require("./shared");

const frontend = readText("frontend/app.js");
const styles = readText("frontend/styles.css");
const translations = readText("frontend/i18n/translations.js");
const architecture = readText("docs/arquitectura/seleccion_escalable_documentos.md");
const errors = [];

for (const token of [
  "function enhanceEntitySelect",
  "MutationObserver",
  "aria-autocomplete",
  "entitySelectorChooseResult",
  "entity-select-results",
  'input.addEventListener("focus",()=>{input.select();render("");})',
]) {
  if (!frontend.includes(token) && !styles.includes(token)) errors.push(`Reusable entity selector is missing ${token}.`);
}

for (const selector of [
  'name="role_id" data-entity-selector',
  'id="branchSelector" data-entity-selector',
  'name="legal_entity_id" data-entity-selector',
  'id="stockWarehouseFilter" data-entity-selector',
  'id="kardexItemFilter" data-entity-selector',
  'id="kardexWarehouseFilter" data-entity-selector',
  'id="selectedRecipe" data-entity-selector',
  'name="productionProductId" data-entity-selector',
  'name="defaultWarehouseId" data-entity-selector',
  'name="warehouseId" data-entity-selector',
  'name="destinationWarehouseId" data-entity-selector',
  'name="responsibleWorkerId" data-entity-selector',
  'name="inventoryItemId" data-entity-selector',
  'name="areaId" data-entity-selector',
  'name="labor_position_id" data-entity-selector',
  'name="area" data-entity-selector',
  'data-entity-selector aria-label="${config.title}"',
  'name="recipeId" id="orderRecipeSelect" data-entity-selector',
  'select[name^="warehouse-"]',
]) {
  if (!frontend.includes(selector)) errors.push(`Growing reference is not wired as searchable: ${selector}.`);
}

for (const token of ["entitySelectorPlaceholder", "entitySelectorEmpty", "entitySelectorChooseResult"]) {
  const occurrences = translations.split(token).length - 1;
  if (occurrences < 2) errors.push(`Selector translation ${token} is not bilingual.`);
}

for (const token of ["Catalogos cerrados", "Administracion", "Produccion", "Almacenes", "Ventas", "Recursos Humanos"]) {
  if (!architecture.includes(token)) errors.push(`Selector audit documentation is missing ${token}.`);
}

if (errors.length) fail("scalable selector validation failed", errors);
else ok("growing entity selectors use the searchable pattern and fixed catalogs remain explicitly documented.");
