const { test, expect } = require("@playwright/test");
const { installLocalAuth } = require("./local-auth");
const tenantId = "ten_739ee59d765d5e14818674800d";
async function setup(page, lang = "es", rejectLogin = false) {
  await page.route("**/*", route => {
    const url = new URL(route.request().url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) return route.abort();
    if (!["GET", "HEAD"].includes(route.request().method())) return route.abort();
    return route.fallback();
  });
  await installLocalAuth(page);
  await page.addInitScript(lang => localStorage.setItem("erclave-lang", lang), lang);
  await page.route("**/identitytoolkit.googleapis.com/**", route => route.fulfill({ status: rejectLogin ? 400 : 200, headers: { "access-control-allow-origin": "*", "access-control-allow-headers": "*" }, json: rejectLogin ? { error: {} } : { email: "admin.qa@erclave.local", idToken: "mock-local-only" } }));
  await page.route("**/v1/**", route => {
    const url = new URL(route.request().url());
    if (url.port !== "8000") return route.fallback();
    const path = url.pathname;
    if (route.request().method() === "OPTIONS") return route.fulfill({ status: 204, headers: { "access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "*" } });
    const data = path === "/v1/backoffice/modules" ? [] : path === "/v1/backoffice/tenants" ? [{ id: tenantId, commercial_name: "ERClave Demo QA", legal_name: "Demo", timezone: "America/Mexico_City", locale: "es-MX", status: "active", entitlements: [] }] : [];
    return route.fulfill({ json: { data }, headers: { "access-control-allow-origin": "*" } });
  });
  await page.goto("/backoffice/");
  await page.locator("[name=email]").fill("admin.qa@erclave.local");
  await page.locator("[name=password]").fill("Local-Only-Password");
  await page.locator("[data-form=login] [type=submit]").click();
  if (!rejectLogin) await expect(page.locator("[data-tab=onboarding]")).toBeVisible();
}
async function reject(page, path, loc) {
  await page.route(`**${path}`, route => route.fulfill({ status: 422, headers: { "access-control-allow-origin": "*" }, json: { detail: [{ loc: ["body", ...loc], type: "string_too_short", ctx: { min_length: 3 }, msg: "DO NOT DISPLAY SERVER DIAGNOSTIC" }] } }));
}
for (const lang of ["es", "en"]) {
  test(`Backoffice ${lang}: onboarding retains values and maps nested owner rejection`, async ({ page }) => {
    await setup(page, lang);
    await reject(page, "/v1/provisioning/tenant-onboarding", ["owner", "display_name"]);
    const form = page.locator("[data-form=tenant-onboarding]");
    await form.locator("[name=commercial_name]").fill("Demo unchanged");
    await form.locator("[name=owner_name]").fill("Jo");
    await form.locator("[name=owner_email]").fill("owner@example.test");
    await form.locator("[name=module_inventory]").check();
    await form.locator("[type=submit]").click();
    await expect(form.locator("[name=owner_name]")).toHaveAttribute("aria-invalid", "true");
    await expect(form.locator("[name=owner_name]")).toBeFocused();
    await expect(form.locator("[name=owner_name]")).toHaveAttribute("aria-describedby", /field-error-/);
    await expect(form.locator("[role=alert]")).toContainText(lang === "en" ? "Review the following to continue:" : "Revisa lo siguiente para continuar:");
    await expect(form.locator("[name=commercial_name]")).toHaveValue("Demo unchanged");
    await expect(form.locator("[name=owner_email]")).toHaveValue("owner@example.test");
    await expect(form.locator("[name=module_inventory]")).toBeChecked();
    await expect(form).not.toContainText("DO NOT DISPLAY SERVER DIAGNOSTIC");
    await form.locator("[name=owner_name]").fill("John");
    await expect(form.locator("[name=owner_name]")).not.toHaveAttribute("aria-invalid", "true");
  });
  test(`Backoffice ${lang}: tenant editor retains rejected edits`, async ({ page }) => {
    await setup(page, lang);
    await page.locator("[data-tab=tenant-admin]").click();
    await page.locator("[data-action=manage-tenant]").click();
    await reject(page, `/v1/backoffice/tenants/${tenantId}`, ["commercial_name"]);
    const form = page.locator("[data-form=tenant-editor]");
    await form.locator("[name=commercial_name]").fill("Jo");
    await form.locator("[name=legal_name]").fill("Keep this edit");
    await form.locator("[type=submit]").click();
    await expect(form.locator("[name=commercial_name]")).toHaveAttribute("aria-invalid", "true");
    await expect(form.locator("[name=legal_name]")).toHaveValue("Keep this edit");
    await expect(form.locator("[name=commercial_name]")).toBeFocused();
    await expect(form.locator("[type=submit]")).toBeEnabled();
  });
  test(`Backoffice ${lang}: rejected login keeps capture only in live DOM`, async ({ page }) => {
    await setup(page, lang, true);
    const form = page.locator("[data-form=login]");
    await expect(form.locator("[role=alert]")).toBeVisible();
    await expect(form.locator("[name=email]")).toHaveValue("admin.qa@erclave.local");
    await expect(form.locator("[name=password]")).toHaveValue("Local-Only-Password");
    expect(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).not.toContain("Local-Only-Password");
    await expect(form.locator("[type=submit]")).toBeEnabled();
  });
}

for (const lang of ["es", "en"]) {
  for (const query of [
    { tab: "tenant-admin", form: "tenant-search", field: "search", value: "Keep search", path: "/v1/backoffice/tenants", type: "string_too_long", ctx: { max_length: 5 } },
    { tab: "usage", form: "usage-search", field: "from_date", value: "2026-09-01", path: "/v1/backoffice/usage", type: "value_error", ctx: {} }
  ]) {
    test(`Backoffice ${lang}: ${query.form} restores filters and field feedback`, async ({ page }) => {
      await setup(page, lang);
      await page.locator(`[data-tab=${query.tab}]`).click();
      const form = page.locator(`[data-form=${query.form}]`);
      await expect(form.locator("[type=submit]")).toBeEnabled();
      await page.route(`**${query.path}?*`, route => route.fulfill({ status: 422, headers: { "access-control-allow-origin": "*" }, json: { detail: [{ loc: ["query", query.field], type: query.type, ctx: query.ctx }] } }));
      await form.locator(`[name=${query.field}]`).fill(query.value);
      await form.locator("[type=submit]").click();
      await expect(form.locator(`[name=${query.field}]`)).toHaveAttribute("aria-invalid", "true");
      await expect(form.locator(`[name=${query.field}]`)).toHaveValue(query.value);
      await expect(form.locator(`[name=${query.field}]`)).toBeFocused();
    });
  }
}

for (const lang of ["es", "en"]) {
  test(`Backoffice ${lang}: native required feedback blocks onboarding submission`, async ({ page }) => {
    await setup(page, lang);
    let commands = 0;
    page.on("request", request => { if (new URL(request.url()).pathname === "/v1/provisioning/tenant-onboarding") commands++; });
    const form = page.locator("[data-form=tenant-onboarding]");
    await form.locator("[name=plan_id]").fill("Keep draft");
    await form.locator("[type=submit]").click();
    await expect(form.locator("[name=commercial_name]")).toHaveAttribute("aria-invalid", "true");
    await expect(form.locator("[name=owner_name]")).toHaveAttribute("aria-invalid", "true");
    await expect(form.locator("[name=owner_email]")).toHaveAttribute("aria-invalid", "true");
    await expect(form.locator("[name=commercial_name]")).toBeFocused();
    await expect(form.locator("[name=plan_id]")).toHaveValue("Keep draft");
    expect(commands).toBe(0);
  });
  test(`Backoffice ${lang}: reset only validates email and preserves password`, async ({ page }) => {
    await setup(page, lang, true);
    const form = page.locator("[data-form=login]");
    await expect(form.locator("[type=submit]")).toBeEnabled();
    await form.locator("[name=email]").fill("");
    await form.locator("[data-action=reset]").click();
    await expect(form.locator("[name=email]")).toHaveAttribute("aria-invalid", "true");
    await expect(form.locator("[name=password]")).not.toHaveAttribute("aria-invalid", "true");
    await expect(form.locator("[name=password]")).toHaveValue("Local-Only-Password");
  });
}
