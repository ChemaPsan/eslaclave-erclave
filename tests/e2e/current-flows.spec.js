const { test, expect } = require("@playwright/test");
const { installLocalAuth, signInAsLocalAdmin } = require("./local-auth");

const MODULES = [
  ["produccion", 5],
  ["almacenes", 5],
  ["recursos-humanos", 4],
  ["ventas", 6],
  ["compras", 4],
  ["mantenimiento", 4]
];

test.beforeEach(async ({ page }) => {
  await installLocalAuth(page);
});

test("autentica en Local y resuelve el contexto del tenant demo", async ({ page }) => {
  await signInAsLocalAdmin(page);
  await expect(page).toHaveTitle("ERClave");
  await expect(page.locator("#contextBranch")).not.toHaveText("Sin sucursal");
  for (const [moduleId] of MODULES) {
    await expect(page.locator(`[data-module-root='${moduleId}']`)).toHaveAttribute("aria-disabled", "false");
  }
});

test("las portadas exponen los 28 reportes y filtros basicos", async ({ page }) => {
  await signInAsLocalAdmin(page);
  let totalReports = 0;
  for (const [moduleId, expectedReports] of MODULES) {
    await page.locator(`[data-module-root='${moduleId}']`).click();
    await expect(page.locator(".module-load-error")).toHaveCount(0);
    const cards = page.locator(".standard-report-card");
    await expect(cards).toHaveCount(expectedReports);
    totalReports += await cards.count();

    const generate = cards.first().getByRole("button", { name: "Generar", exact: true });
    await expect(generate).toBeVisible();
    await generate.click();
    await expect(page.locator("#standardReportForm")).toBeVisible();
    await expect(page.locator("#standardReportForm")).not.toContainText("CSV");
    await page.locator("[data-close-standard-report]").click();
  }
  expect(totalReports).toBe(28);
});

test("todos los submodulos implementados conservan continuidad de carga", async ({ page }) => {
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await signInAsLocalAdmin(page);

  for (const [moduleId] of MODULES) {
    await page.locator(`[data-module-root='${moduleId}']`).click();
    const submodules = page.locator(`[data-module='${moduleId}'][data-submodule-nav]`);
    const count = await submodules.count();
    expect(count).toBeGreaterThan(0);
    for (let index = 0; index < count; index += 1) {
      const target = submodules.nth(index);
      const submoduleId = await target.getAttribute("data-submodule-nav");
      await target.click();
      await expect(page.locator(`[data-module='${moduleId}'][data-submodule-nav='${submoduleId}']`)).toHaveClass(/active/);
      await expect(page.locator(".module-load-error")).toHaveCount(0);
      await expect(page.locator("#modulePanel")).toBeVisible();
    }
  }
  expect(pageErrors).toEqual([]);
});

test("la aplicacion no consume APIs remotas durante la regresion Local", async ({ page }) => {
  const forbiddenRequests = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    const allowedHost = ["127.0.0.1", "localhost"].includes(url.hostname);
    const localFirebaseFixture = url.hostname === "www.gstatic.com";
    if (!allowedHost && !localFirebaseFixture) forbiddenRequests.push(request.url());
  });
  await signInAsLocalAdmin(page);
  await page.locator("[data-module-root='ventas']").click();
  await expect(page.locator(".standard-report-card")).toHaveCount(6);
  expect(forbiddenRequests).toEqual([]);
});

test("los listados extensos se paginan sin perder registros", async ({ page }) => {
  await signInAsLocalAdmin(page);
  await page.evaluate(async () => {
    const root = document.createElement("section");
    root.id = "paginationFixture";
    root.innerHTML = `<div class="catalog-grid">${Array.from({ length: 31 }, (_, index) => `<article>Registro ${index + 1}</article>`).join("")}</div>`;
    document.body.appendChild(root);
    const { installListPagination } = await import("/features/list-pagination.js");
    installListPagination(root, {
      navigation: "Paginacion del listado",
      previous: "Anterior",
      next: "Siguiente",
      summary: "Mostrando {from}-{to} de {total}"
    }, 10);
  });
  const records = page.locator("#paginationFixture article:visible");
  await expect(records).toHaveCount(10);
  await expect(page.locator("#paginationFixture .list-pagination span")).toHaveText("Mostrando 1-10 de 31");
  await page.locator("#paginationFixture [data-page-next]").click();
  await expect(page.locator("#paginationFixture .list-pagination span")).toHaveText("Mostrando 11-20 de 31");
  await expect(records).toHaveCount(10);
});
