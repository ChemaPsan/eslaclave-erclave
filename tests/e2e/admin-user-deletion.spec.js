const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { installLocalAuth, signInAsLocalAdmin } = require('./local-auth');

const tenantId = 'ten_739ee59d765d5e14818674800d';
const fixture = {
  id: 'usr_browser_delete_only',
  display_name: 'Browser deletion fixture',
  email: 'browser-delete-only@example.invalid',
  status: 'active',
  roles: []
};

// Real Local login/dashboard; the user exists only in browser state and DELETE is a double.
for (const lang of ['es', 'en']) {
  for (const outcome of ['cleanup-pending', 'server-error']) {
    test(`${lang}: user deletion ${outcome}`, async ({ page }) => {
      const unexpectedWrites = [];
      const pageErrors = [];
      const deletes = [];
      page.on('pageerror', error => pageErrors.push(error.message));
      await page.route('**/*', route => {
        const url = new URL(route.request().url());
        return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.fallback() : route.abort();
      });
      await installLocalAuth(page);
      await page.route(/\/app\.js(?:\?.*)?$/, route => route.fulfill({
        contentType: 'application/javascript',
        body: fs.readFileSync(path.join(__dirname, '../../frontend/app.js'), 'utf8') + '\nwindow.deletionAudit = {state, render};'
      }));
      await page.route('**/v1/**', async route => {
        const request = route.request();
        const url = new URL(request.url());
        if (['GET', 'HEAD', 'OPTIONS'].includes(request.method())) return route.fallback();
        if (url.port === '9099' && url.pathname.endsWith('/accounts:signInWithPassword')) return route.fallback();
        if (url.origin === 'http://127.0.0.1:8000' && request.method() === 'DELETE' && url.pathname === `/v1/users/${fixture.id}`) {
          deletes.push({ tenant: request.headers()['x-tenant-id'], authorized: Boolean(request.headers().authorization) });
          return route.fulfill(outcome === 'cleanup-pending' ? {
            status: 200,
            json: { data: { ...fixture, status: 'deleted', firebase_identity_cleanup: { status: 'pending', error_codes: ['firebase_identity_unavailable'] } } }
          } : {
            status: 500,
            json: { error: { code: 'service_unavailable', message: 'Raw server diagnostic must not be shown' } }
          });
        }
        unexpectedWrites.push(`${request.method()} ${url.origin}${url.pathname}`);
        return route.abort();
      });

      await signInAsLocalAdmin(page);
      await expect.poll(() => page.evaluate(() => window.deletionAudit.state.adminApi.status)).toBe('ready');
      await page.evaluate(({ lang, fixture, tenantId }) => {
        const { state, render } = window.deletionAudit;
        if (state.sessionApi.data.tenant.id !== tenantId) throw new Error('Unexpected tenant');
        localStorage.setItem('erclave-lang', lang);
        state.lang = lang;
        state.active = 'administracion';
        state.activeSubmodule = null;
        state.adminPanel = 'users';
        state.adminApi.data.users.push(fixture);
        render();
      }, { lang, fixture, tenantId });

      const button = page.locator(`[data-action='admin-delete-user'][data-user-id='${fixture.id}']`);
      await expect(button).toBeEnabled();
      const confirmation = page.waitForEvent('dialog');
      const click = button.click();
      const dialog = await confirmation;
      expect(dialog.type()).toBe('confirm');
      expect(dialog.message()).toContain(fixture.email);
      expect(dialog.message()).toContain(lang === 'es' ? 'Se conserva la auditoría' : 'Audit history is preserved');
      await dialog.accept();
      await click;

      if (outcome === 'cleanup-pending') {
        const toast = page.locator('#toast');
        await expect(toast).toBeVisible();
        await expect(toast).toHaveAttribute('data-tone', 'warning');
        await expect(toast).toHaveAttribute('role', 'status');
        await expect(toast).toHaveAttribute('aria-live', 'polite');
        await expect(toast).toHaveAttribute('aria-atomic', 'true');
        await expect(toast).toHaveText(lang === 'es'
          ? `Usuario ${fixture.email} retirado de este tenant. La limpieza de su identidad Firebase está pendiente.`
          : `User ${fixture.email} removed from this tenant. Firebase identity cleanup is pending.`);
        await expect.poll(() => page.evaluate(() => window.deletionAudit.state.adminApi.status)).toBe('ready');
        await expect(button).toHaveCount(0);
      } else {
        await expect.poll(() => page.evaluate(() => window.deletionAudit.state.adminApi.status)).toBe('error');
        await expect(page.locator('.validation-card.danger[role="alert"]').first()).toBeVisible();
        await expect(page.locator('.admin-record').filter({ hasText: fixture.email })).toBeVisible();
        await expect(page.locator('#toast')).toBeHidden();
        await expect(page.locator('body')).not.toContainText('Raw server diagnostic must not be shown');
        expect(await page.evaluate(id => window.deletionAudit.state.adminApi.data.users.some(user => user.id === id), fixture.id)).toBe(true);
      }
      expect(deletes).toEqual([{ tenant: tenantId, authorized: true }]);
      expect(unexpectedWrites).toEqual([]);
      expect(pageErrors).toEqual([]);
    });
  }
}
