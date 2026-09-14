const { defineConfig } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "./tests/e2e",
  testMatch: ["form-feedback.spec.js", "backoffice-form-feedback.spec.js"],
  outputDir: "test-results/form-feedback-ci",
  workers: 1,
  retries: 0,
  timeout: 30000,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4183",
    headless: true,
    channel: process.env.CI ? undefined : "chrome",
    browserName: "chromium"
  },
  // Static assets only. Tests intercept every API/auth request. No DB or seed.
  webServer: {
    command: `${process.platform === "win32" ? "python" : "python3"} -m http.server 4183 --bind 127.0.0.1 --directory frontend`,
    url: "http://127.0.0.1:4183",
    reuseExistingServer: false,
    stderr: "ignore",
    timeout: 15000
  }
});
