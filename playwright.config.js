const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests/e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  globalSetup: require.resolve("./tests/e2e/local-preflight"),
  use: {
    baseURL: process.env.ERCLAVE_E2E_BASE_URL || "http://127.0.0.1:4173",
    browserName: "chromium",
    channel: "chrome",
    headless: true,
    locale: "es-MX",
    timezoneId: "America/Mexico_City",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    acceptDownloads: true
  }
});
