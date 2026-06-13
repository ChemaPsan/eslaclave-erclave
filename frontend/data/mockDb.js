import { defaultProductsServices, defaultLaborRoles, defaultMachines, defaultRecipes, defaultOrders } from "./resources.js";

export const mockDb = {
  loadProductsServices() {
    const raw = localStorage.getItem("erclave-products-services");
    return raw ? JSON.parse(raw) : defaultProductsServices;
  },
  saveProductsServices(items) {
    localStorage.setItem("erclave-products-services", JSON.stringify(items));
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
    const raw = localStorage.getItem("erclave-labor-roles");
    return raw ? JSON.parse(raw) : defaultLaborRoles;
  },
  saveLaborRoles(items) {
    localStorage.setItem("erclave-labor-roles", JSON.stringify(items));
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
    const raw = localStorage.getItem("erclave-machines");
    return raw ? JSON.parse(raw) : defaultMachines;
  },
  saveMachines(items) {
    localStorage.setItem("erclave-machines", JSON.stringify(items));
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
    const raw = localStorage.getItem("erclave-recipes");
    return raw ? JSON.parse(raw) : defaultRecipes;
  },
  saveRecipes(recipes) {
    localStorage.setItem("erclave-recipes", JSON.stringify(recipes));
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
    const nextRecipes = recipes.length ? recipes : defaultRecipes;
    this.saveRecipes(nextRecipes);
    return nextRecipes;
  },
  findRecipe(recipeId) {
    return this.loadRecipes().find((item) => item.id === recipeId);
  },
  loadOrders() {
    const raw = localStorage.getItem("erclave-orders");
    return raw ? JSON.parse(raw) : defaultOrders;
  },
  saveOrders(orders) {
    localStorage.setItem("erclave-orders", JSON.stringify(orders));
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
  }
};
