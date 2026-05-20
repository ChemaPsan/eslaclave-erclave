import { defaultRecipes, defaultOrders } from "./resources.js";

export const mockDb = {
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
