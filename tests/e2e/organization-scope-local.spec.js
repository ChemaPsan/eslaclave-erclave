const { test, expect } = require('@playwright/test');
const fs = require('fs'), path = require('path');
const { installLocalAuth, signInAsLocalAdmin } = require('./local-auth');

test('Local Owner opens the real scope editor without business mutations', async ({ page }, testInfo) => {
  const failures = [], writes = [];
  page.on('pageerror', error => failures.push(error.message));
  await page.route('**/*', route => ['127.0.0.1', 'localhost'].includes(new URL(route.request().url()).hostname) ? route.fallback() : route.abort());
  await installLocalAuth(page);
  await page.route(/\/app\.js(?:\?.*)?$/, route => route.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(path.join(__dirname, '../../frontend/app.js'), 'utf8') + '\nwindow.scopeSmoke={state,render};' }));
  await page.route('**/v1/**', route => {
    if (new URL(route.request().url()).port === '9099' || ['GET', 'HEAD', 'OPTIONS'].includes(route.request().method())) return route.fallback();
    writes.push(route.request().url()); return route.abort();
  });
  await signInAsLocalAdmin(page);
  await expect.poll(() => page.evaluate(() => window.scopeSmoke.state.adminApi.status)).toBe('ready');
  await page.evaluate(() => {
    const { state, render } = window.scopeSmoke;
    if (state.sessionApi.data.tenant.id !== 'ten_739ee59d765d5e14818674800d') throw Error('Wrong tenant');
    state.active = 'administracion'; state.activeSubmodule = null; state.adminPanel = 'users'; render();
  });
  await expect(page.locator('[data-action=admin-user-scope]').first()).toBeVisible();
  await page.locator('[data-action=admin-user-scope]').first().click();
  await expect(page.locator('[data-form=organization-scope]')).toBeVisible();
  await expect(page.locator('[name=mode]')).toHaveValue('all');
  await expect(page.locator('[data-scope-restricted]')).toBeHidden();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('[name=mode]').selectOption('restricted');
  await expect(page.locator('[data-scope-restricted]')).toBeVisible();
  expect(await page.locator('[data-form=organization-scope]').evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('scope-editor-local.png') });
  expect(failures).toEqual([]); expect(writes).toEqual([]);
});
