const { test, expect } = require('@playwright/test');
const origin = 'http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);

async function setup(page, lang = 'es', readOnly = false) {
  const fixture = { requests: [], error: null, delay: 0 };
  await page.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url());
    if (url.origin !== origin) return route.abort();
    if (url.pathname === '/auth.js') return route.fulfill({ contentType: 'application/javascript', body: 'export const getAuthToken=async()=>null;' });
    if (url.pathname === '/__scope') return route.fulfill({ contentType: 'text/html', body: '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/organization.css"></head><body><main style="width:320px;max-width:100%;padding:12px"></main></body></html>' });
    if (url.pathname.startsWith('/v1/organization/divisions')) return route.fulfill({ json: { data: [{ id: 'div-new', society_id: 'soc-new', society_name: 'Society New', code: 'DIV-002', name: 'New Division', status: 'active' }], meta: { total: 1 } } });
    if (url.pathname.endsWith('/organization-scope')) {
      if (request.method() === 'GET') return route.fulfill({ json: { data: { version: 2, revision: 4, society_ids: ['soc-old'], division_ids: ['div-old'], divisions: [{ id: 'div-old', society_id: 'soc-old', code: 'DIV-001', name: 'Existing Division', status: 'active' }] } } });
      fixture.requests.push({ payload: request.postDataJSON(), headers: request.headers() });
      if (fixture.delay) await new Promise(resolve => setTimeout(resolve, fixture.delay));
      if (fixture.error) { const error = fixture.error; fixture.error = null; return route.fulfill({ status: error.status, json: { error: { code: error.code, message: 'PRIVATE SQL', correlation_id: 'scope-safe', details: error.details || {} } } }); }
      const { expected_revision, ...payload } = request.postDataJSON();
      return route.fulfill({ json: { data: { ...payload, revision: expected_revision + 1 } } });
    }
    return request.method() === 'GET' ? route.continue() : route.abort();
  });
  await page.goto(origin + '/__scope');
  await page.evaluate(async ({ origin, lang, readOnly }) => {
    localStorage.setItem('erclave-lang', lang); window.ERCLAVE_CONFIG = { localApiBaseUrl: origin };
    (await import('/features/form-feedback.js')).installFormFeedback({ getLanguage: () => lang });
    await (await import('/features/organization-scope.js')).mountScopeEditor(document.querySelector('main'), 'usr-fixture',
      ['admin.user.read', 'admin.division.read', ...(readOnly ? [] : ['admin.user.update'])], lang);
  }, { origin, lang, readOnly });
  await expect(page.locator('[data-form=organization-scope]')).toBeVisible();
  return fixture;
}

for (const lang of ['es', 'en']) {
  test(`${lang}: scope failure preserves existing and searched IDs; retry is idempotent`, async ({ page }) => {
    const fixture = await setup(page, lang);
    await expect(page.locator('[data-scope-selected]')).toContainText('Existing Division');
    await page.locator('[name=division_search]').fill('New');
    await page.locator('[data-scope-search]').click();
    await page.locator('[data-scope-add]').click();
    fixture.error = { status: 503, code: 'service_unavailable' };
    await page.locator('[type=submit]').click();
    await expect(page.locator('[data-scope-selected]')).toContainText('New Division');
    await expect(page.locator('main')).not.toContainText('PRIVATE SQL');
    await expect(page.locator('[role=alert]').first()).toBeVisible();
    await page.locator('[type=submit]').click();
    await expect.poll(() => fixture.requests.length).toBe(2);
    expect(fixture.requests[0].headers['idempotency-key']).toBe(fixture.requests[1].headers['idempotency-key']);
    expect(fixture.requests[1].payload).toEqual({ version: 2, expected_revision: 4, society_ids: ['soc-old', 'soc-new'], division_ids: ['div-old', 'div-new'] });
    await expect(page.locator('[data-scope-message]')).toContainText(lang === 'es' ? 'guardado' : 'saved');
    expect(await page.locator('main').evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
  });

  test(`${lang}: empty grant is explicit; wildcard must be deliberately selected`, async ({ page }) => {
    const fixture = await setup(page, lang);
    await page.locator('[data-scope-remove]').click();
    await page.locator('[type=submit]').click();
    await expect.poll(() => fixture.requests.length).toBe(1);
    expect(fixture.requests[0].payload.division_ids).toEqual([]);
    expect(fixture.requests[0].payload.society_ids).toEqual([]);
    await expect(page.locator('[data-scope-message]')).not.toBeEmpty();
    await page.locator('[name=mode]').selectOption('all');
    await expect(page.locator('[data-scope-restricted]')).toBeHidden();
    await page.locator('[type=submit]').click();
    await expect.poll(() => fixture.requests.length).toBe(2);
    expect(fixture.requests[1].payload).toMatchObject({ expected_revision: 5, society_ids: ['*'], division_ids: ['*'] });
  });

  test(`${lang}: conflict keeps capture; read-only cannot submit`, async ({ page }) => {
    const fixture = await setup(page, lang);
    fixture.error = { status: 409, code: 'organization_scope_conflict' };
    await page.locator('[type=submit]').click();
    await expect(page.locator('[role=alert]').first()).toContainText(lang === 'es' ? 'alcance cambió' : 'scope changed');
    await expect(page.locator('[data-scope-selected]')).toContainText('Existing Division');
    await setup(page, lang, true);
    await expect(page.locator('[type=submit]')).toBeDisabled();
  });
}

test('division choices never invent Matriz and preferences are isolated by tenant and actor', async ({ page }) => {
  await setup(page);
  const result = await page.evaluate(async () => {
    const { availableDivisions, divisionPreferenceKey } = await import('/features/organization-scope.js');
    const context = { tenant: { id: 'one' }, user: { id: 'user' }, scope: { version: 2, divisions: [], societies: [] } };
    return { empty: availableDivisions(context), keys: [divisionPreferenceKey(context), divisionPreferenceKey({ ...context, tenant: { id: 'two' } }), divisionPreferenceKey({ ...context, user: { id: 'other' } })] };
  });
  expect(result.empty).toEqual([]); expect(new Set(result.keys).size).toBe(3);
});
