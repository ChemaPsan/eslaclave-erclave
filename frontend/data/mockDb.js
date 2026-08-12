import { defaultProductsServices, defaultLaborAreas, defaultLaborRoles, defaultMachines, defaultRecipes, defaultOrders } from "./resources.js";
import { getApiMode, getDemoTenantId } from "../api/config.js";

function shouldUseSeedData() {
  return getApiMode() !== "api";
}

function storageKey(baseKey) {
  if (shouldUseSeedData()) return baseKey;
  return `${baseKey}-${getDemoTenantId()}`;
}

const apiMemoryStore = new Map();

function readStoredValue(key) {
  return shouldUseSeedData() ? localStorage.getItem(key) : apiMemoryStore.get(key) || null;
}

function writeStoredValue(key, value) {
  if (shouldUseSeedData()) localStorage.setItem(key, value);
  else apiMemoryStore.set(key, value);
}

export const mockDb = {
  getDefaultAdminOrganization(tenant = {}) {
    return {
      corporate: {
        commercial_name: tenant.commercial_name || "Cliente piloto",
        legal_name: tenant.legal_name || "",
        tax_id: "",
        phone: "",
        contact_name: "",
        contact_email: "",
        contact_phone: "",
        contact_position: ""
      },
      legal_entities: [],
      branches: []
    };
  },
  loadAdminOrganization(tenant = {}) {
    const raw = readStoredValue(storageKey("erclave-admin-organization"));
    return raw ? JSON.parse(raw) : this.getDefaultAdminOrganization(tenant);
  },
  saveAdminOrganization(organization) {
    writeStoredValue(storageKey("erclave-admin-organization"), JSON.stringify(organization));
    return organization;
  },
  loadProductsServices() {
    const raw = readStoredValue(storageKey("erclave-products-services"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultProductsServices : [];
  },
  saveProductsServices(items) {
    writeStoredValue(storageKey("erclave-products-services"), JSON.stringify(items));
  },
  addProductService(item) {
    const items = this.loadProductsServices();
    items.unshift(item);
    this.saveProductsServices(items);
    return items;
  },
  updateProductService(item) {
    const items = this.loadProductsServices().map((current) => (current.id === item.id ? item : current));
    this.saveProductsServices(items);
    return items;
  },
  findProductService(itemId) {
    return this.loadProductsServices().find((item) => item.id === itemId);
  },
  loadLaborAreas() {
    const raw = readStoredValue(storageKey("erclave-labor-areas"));
    if (raw) return JSON.parse(raw);
    return shouldUseSeedData() ? [...defaultLaborAreas] : [];
  },
  saveLaborAreas(items) {
    writeStoredValue(storageKey("erclave-labor-areas"), JSON.stringify(items));
  },
  addLaborArea(item) {
    const items = this.loadLaborAreas();
    if (items.some((area) => area.code.toLowerCase() === item.code.toLowerCase() || area.name.toLowerCase() === item.name.toLowerCase())) {
      throw new Error("duplicate_labor_area");
    }
    items.unshift(item);
    this.saveLaborAreas(items);
    return items;
  },
  updateLaborArea(item) {
    const previous = this.findLaborArea(item.id);
    if (!previous) throw new Error("labor_area_not_found");
    if (this.loadLaborAreas().some((area) => area.id !== item.id && (area.code.toLowerCase() === item.code.toLowerCase() || area.name.toLowerCase() === item.name.toLowerCase()))) {
      throw new Error("duplicate_labor_area");
    }
    const items = this.loadLaborAreas().map((current) => (current.id === item.id ? item : current));
    this.saveLaborAreas(items);
    if (previous && previous.name !== item.name) {
      this.saveLaborRoles(this.loadLaborRoles().map((role) => role.areaId === item.id ? { ...role, area: item.name } : role));
    }
    return items;
  },
  findLaborArea(itemId) {
    return this.loadLaborAreas().find((item) => item.id === itemId);
  },
  loadLaborRoles() {
    const raw = readStoredValue(storageKey("erclave-labor-roles"));
    const roles = raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultLaborRoles : [];
    const areas = this.loadLaborAreas();
    let changed = false;
    const migrated = roles.map((role) => {
      if (role.areaId && areas.some((area) => area.id === role.areaId)) return role;
      const area = areas.find((item) => item.name.trim().toLowerCase() === String(role.area || "").trim().toLowerCase());
      if (!area) return role;
      changed = true;
      return { ...role, areaId: area.id, area: area.name };
    });
    if (changed) this.saveLaborRoles(migrated);
    return migrated;
  },
  saveLaborRoles(items) {
    writeStoredValue(storageKey("erclave-labor-roles"), JSON.stringify(items));
  },
  addLaborRole(item) {
    const area = this.findLaborArea(item.areaId);
    if (!area) throw new Error("labor_area_not_found");
    const items = this.loadLaborRoles();
    items.unshift({ ...item, areaId: area.id, area: area.name });
    this.saveLaborRoles(items);
    return items;
  },
  updateLaborRole(item) {
    const area = this.findLaborArea(item.areaId);
    if (!area) throw new Error("labor_area_not_found");
    const items = this.loadLaborRoles().map((current) => (current.id === item.id ? { ...item, areaId: area.id, area: area.name } : current));
    this.saveLaborRoles(items);
    return items;
  },
  findLaborRole(itemId) {
    return this.loadLaborRoles().find((item) => item.id === itemId);
  },
  loadMachines() {
    const raw = readStoredValue(storageKey("erclave-machines"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultMachines : [];
  },
  saveMachines(items) {
    writeStoredValue(storageKey("erclave-machines"), JSON.stringify(items));
  },
  addMachine(item) {
    const items = this.loadMachines();
    items.unshift(item);
    this.saveMachines(items);
    return items;
  },
  updateMachine(item) {
    const items = this.loadMachines().map((current) => (current.id === item.id ? item : current));
    this.saveMachines(items);
    return items;
  },
  findMachine(itemId) {
    return this.loadMachines().find((item) => item.id === itemId);
  },
  loadRecipes() {
    const raw = readStoredValue(storageKey("erclave-recipes"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultRecipes : [];
  },
  saveRecipes(recipes) {
    writeStoredValue(storageKey("erclave-recipes"), JSON.stringify(recipes));
  },
  addRecipe(recipe) {
    const recipes = this.loadRecipes();
    recipes.unshift(recipe);
    this.saveRecipes(recipes);
    return recipes;
  },
  updateRecipe(recipe) {
    const recipes = this.loadRecipes().map((item) => (item.id === recipe.id ? recipe : item));
    this.saveRecipes(recipes);
    return recipes;
  },
  deleteRecipe(recipeId) {
    const recipes = this.loadRecipes().filter((item) => item.id !== recipeId);
    const nextRecipes = recipes.length || !shouldUseSeedData() ? recipes : defaultRecipes;
    this.saveRecipes(nextRecipes);
    return nextRecipes;
  },
  findRecipe(recipeId) {
    return this.loadRecipes().find((item) => item.id === recipeId);
  },
  loadOrders() {
    const raw = readStoredValue(storageKey("erclave-orders"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultOrders : [];
  },
  saveOrders(orders) {
    writeStoredValue(storageKey("erclave-orders"), JSON.stringify(orders));
  },
  addOrder(order) {
    const orders = this.loadOrders();
    orders.unshift(order);
    this.saveOrders(orders);
    return orders;
  },
  updateOrder(order) {
    const orders = this.loadOrders().map((item) => (item.id === order.id ? order : item));
    this.saveOrders(orders);
    return orders;
  },
  findOrder(orderId) {
    return this.loadOrders().find((item) => item.id === orderId);
  },
  loadModuleRecords(moduleId, submoduleId = "") {
    const raw = readStoredValue(storageKey(`erclave-module-records-${moduleId}`));
    const records = raw ? JSON.parse(raw) : [];
    return submoduleId ? records.filter((item) => item.submoduleId === submoduleId) : records;
  },
  saveModuleRecords(moduleId, records) {
    writeStoredValue(storageKey(`erclave-module-records-${moduleId}`), JSON.stringify(records));
  },
  addModuleRecord(moduleId, record) {
    const records = this.loadModuleRecords(moduleId);
    records.unshift(record);
    this.saveModuleRecords(moduleId, records);
    return records;
  },
  updateModuleRecord(moduleId, record) {
    const records = this.loadModuleRecords(moduleId).map((item) => (item.id === record.id ? record : item));
    this.saveModuleRecords(moduleId, records);
    return records;
  },
  findModuleRecord(moduleId, recordId) {
    return this.loadModuleRecords(moduleId).find((item) => item.id === recordId);
  }
};
