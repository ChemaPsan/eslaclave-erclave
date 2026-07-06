import { defaultProductsServices, defaultLaborRoles, defaultMachines, defaultRecipes, defaultOrders } from "./resources.js";
import { getApiMode, getConfiguredTenantId, getDemoTenantId } from "../api/config.js";

function shouldUseSeedData() {
  return getApiMode() !== "api" || getDemoTenantId() === getConfiguredTenantId();
}

function storageKey(baseKey) {
  if (shouldUseSeedData()) return baseKey;
  return `${baseKey}-${getDemoTenantId()}`;
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
    const raw = localStorage.getItem(storageKey("erclave-admin-organization"));
    return raw ? JSON.parse(raw) : this.getDefaultAdminOrganization(tenant);
  },
  saveAdminOrganization(organization) {
    localStorage.setItem(storageKey("erclave-admin-organization"), JSON.stringify(organization));
    return organization;
  },
  loadProductsServices() {
    const raw = localStorage.getItem(storageKey("erclave-products-services"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultProductsServices : [];
  },
  saveProductsServices(items) {
    localStorage.setItem(storageKey("erclave-products-services"), JSON.stringify(items));
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
  loadLaborRoles() {
    const raw = localStorage.getItem(storageKey("erclave-labor-roles"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultLaborRoles : [];
  },
  saveLaborRoles(items) {
    localStorage.setItem(storageKey("erclave-labor-roles"), JSON.stringify(items));
  },
  addLaborRole(item) {
    const items = this.loadLaborRoles();
    items.unshift(item);
    this.saveLaborRoles(items);
    return items;
  },
  updateLaborRole(item) {
    const items = this.loadLaborRoles().map((current) => (current.id === item.id ? item : current));
    this.saveLaborRoles(items);
    return items;
  },
  findLaborRole(itemId) {
    return this.loadLaborRoles().find((item) => item.id === itemId);
  },
  loadMachines() {
    const raw = localStorage.getItem(storageKey("erclave-machines"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultMachines : [];
  },
  saveMachines(items) {
    localStorage.setItem(storageKey("erclave-machines"), JSON.stringify(items));
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
    const raw = localStorage.getItem(storageKey("erclave-recipes"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultRecipes : [];
  },
  saveRecipes(recipes) {
    localStorage.setItem(storageKey("erclave-recipes"), JSON.stringify(recipes));
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
    const raw = localStorage.getItem(storageKey("erclave-orders"));
    return raw ? JSON.parse(raw) : shouldUseSeedData() ? defaultOrders : [];
  },
  saveOrders(orders) {
    localStorage.setItem(storageKey("erclave-orders"), JSON.stringify(orders));
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
    const raw = localStorage.getItem(storageKey(`erclave-module-records-${moduleId}`));
    const records = raw ? JSON.parse(raw) : [];
    return submoduleId ? records.filter((item) => item.submoduleId === submoduleId) : records;
  },
  saveModuleRecords(moduleId, records) {
    localStorage.setItem(storageKey(`erclave-module-records-${moduleId}`), JSON.stringify(records));
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
