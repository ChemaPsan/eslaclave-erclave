const { defineConfig } = require("@playwright/test");
const staticPort = Number(process.env.ERCLAVE_FORM_TEST_PORT || 4183);
module.exports = defineConfig({
  testDir: "./tests/e2e",
  // CC16 exercises the real Maintenance forms with isolated service responses.
  testMatch: ["cc16-maintenance-context.spec.js", "cc15-purchasing-context.spec.js", "cc14-receipt-costs.spec.js", "cc12-production-fulfillment.spec.js", "cc08-service-costs.spec.js", "cc11-production-order.spec.js", "cc10-resource-rates.spec.js", "scoped-stock-fulfillment.spec.js", "form-feedback.spec.js", "backoffice-form-feedback.spec.js", "api-timeouts.spec.js", "organization.spec.js", "organization-scope.spec.js", "scoped-configuration.spec.js", "cost-centers.spec.js", "inventory-organization.spec.js", "production-organization.spec.js", "hr-organization.spec.js", "commercial-organization.spec.js", "commercial-terms.spec.js", "quote-context.spec.js"],
  outputDir: "test-results/form-feedback-ci",
  workers: 1,
  retries: 0,
  timeout: 30000,
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${staticPort}`,
    headless: true,
    channel: process.env.CI ? undefined : "chrome",
    browserName: "chromium"
  },
  // Static assets only. Tests intercept every API/auth request. No DB or seed.
  webServer: {
    command: `${process.platform === "win32" ? "python" : "python3"} -m http.server ${staticPort} --bind 127.0.0.1 --directory frontend`,
    url: `http://127.0.0.1:${staticPort}`,
    reuseExistingServer: false,
    stderr: "ignore",
    timeout: 15000
  }
});
