const { test, expect } = require('@playwright/test');

async function setup(page, lang = 'es', granted) {
  const origin = new URL(test.info().project.use.baseURL).origin;
  const permissions = granted || ['fiscal_issuer', 'society', 'division'].flatMap(stem => ['read', 'create', 'update', 'status'].map(action => `admin.${stem}.${action}`)).concat('admin.catalog.read');
  const fixture = {
    requests: [], nextError: null, delay: 0,
    rows: {
      'fiscal-issuers': [{ id: 'emi-test', code: 'EMI-000001', legal_name: 'Issuer fixture', status: 'active' }],
      societies: [{ id: 'soc-test', code: 'SOC-000001', name: 'Society fixture', issuer_id: 'emi-test', issuer_name: 'Issuer fixture', base_currency: 'MXN', status: 'active' }],
      divisions: [{ id: 'div-test', code: 'DIV-000001', name: 'Division fixture', society_id: 'soc-test', society_name: 'Society fixture', status: 'active' }]
    }
  };
  await page.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url());
    if (url.origin !== origin) return route.abort();
    if (url.pathname === '/auth.js') return route.fulfill({ contentType: 'application/javascript', body: 'export const getAuthToken=async()=>null;' });
    if (url.pathname === '/__organization_fixture') return route.fulfill({ contentType: 'text/html', body: '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/organization.css"></head><body><main style="max-width:950px;margin:20px auto;padding:12px"></main></body></html>' });
    if (!url.pathname.startsWith('/v1/organization/')) return request.method() === 'GET' ? route.continue() : route.abort();
    const [, , , kind, id, action] = url.pathname.split('/');
    fixture.requests.push({ method: request.method(), url: url.toString(), body: request.postDataJSON(), headers: request.headers() });
    if (request.method() === 'GET') {
      const q = (url.searchParams.get('q') || '').toLowerCase(), offset = Number(url.searchParams.get('offset') || 0), limit = Number(url.searchParams.get('limit') || 25);
      const rows = fixture.rows[kind].filter(row => `${row.code} ${row.name || row.legal_name}`.toLowerCase().includes(q) && (!url.searchParams.get('status') || row.status === url.searchParams.get('status')));
      return route.fulfill({ json: { data: rows.slice(offset, offset + limit), meta: { total: rows.length, offset, limit, code_mode: 'managed' } } });
    }
    if (fixture.delay) await new Promise(resolve => setTimeout(resolve, fixture.delay));
    if (fixture.nextError) { const error = fixture.nextError; fixture.nextError = null; return route.fulfill({ status: error.status, json: { error: { ...error, message: 'PRIVATE SQL DIAGNOSTIC', correlation_id: 'fixture-safe-ref' } } }); }
    const payload = request.postDataJSON() || {};
    let row = fixture.rows[kind].find(row => row.id === id);
    if (!id) { row = { id: `new-${kind}`, code: 'NEW-000001', status: 'active', ...payload }; fixture.rows[kind].push(row); }
    else Object.assign(row, payload, action ? { status: action === 'activate' ? 'active' : 'inactive' } : {});
    if (kind === 'societies') row.issuer_name = fixture.rows['fiscal-issuers'].find(parent => parent.id === row.issuer_id)?.legal_name;
    if (kind === 'divisions') row.society_name = fixture.rows.societies.find(parent => parent.id === row.society_id)?.name;
    return route.fulfill({ status: id ? 200 : 201, json: { data: row } });
  });
  await page.goto(origin + '/__organization_fixture');
  await page.evaluate(async ({ origin, lang, permissions }) => {
    localStorage.setItem('erclave-lang', lang);
    window.ERCLAVE_CONFIG = { localApiBaseUrl: origin };
    const feedback = await import('/features/form-feedback.js'); feedback.installFormFeedback({ getLanguage: () => lang });
    const feature = await import('/features/organization.js');
    const data = { tenant: {}, session: { permissions }, commercialCatalogs: { currencies: [{ code: 'MXN', name_es: 'Peso mexicano', name_en: 'Mexican peso', status: 'active' }, { code: 'USD', name_es: 'Dólar', name_en: 'Dollar', status: 'active' }] } };
    document.querySelector('main').innerHTML = feature.renderOrganizationPanel(data, lang);
    feature.bindOrganizationPanel(document.querySelector('main'), data, lang);
  }, { origin, lang, permissions });
  if (permissions.some(p => p.endsWith('.read') && p !== 'admin.catalog.read')) await expect(page.locator('[data-org-action=create]')).toBeEnabled();
  return fixture;
}

async function createForm(page, kind) {
  await page.locator(`[data-org-kind="${kind}"]`).click();
  await page.locator('[data-org-action=create]').click();
  return page.locator(`[data-form="organization-${kind}"]`);
}

for (const lang of ['es', 'en']) {
  for (const kind of ['fiscal-issuers', 'societies', 'divisions']) {
    test(`${lang} ${kind}: structured error preserves fields, retry and edit use the right payload`, async ({ page }) => {
      const fixture = await setup(page, lang);
      const form = await createForm(page, kind);
      const name = kind === 'fiscal-issuers' ? 'legal_name' : 'name';
      await form.locator(`[name=${name}]`).fill('New organization record');
      if (kind !== 'fiscal-issuers') {
        await form.locator('[name=parent_search]').fill('fixture');
        await form.locator('[data-org-results] button').first().click();
      }
      if (kind === 'societies') await expect(form.locator('[name=base_currency]')).toHaveValue('MXN');
      const field = kind === 'fiscal-issuers' ? 'tax_id' : kind === 'societies' ? 'base_currency' : 'society_id';
      const code = kind === 'fiscal-issuers' ? 'organization_tax_id_duplicate' : kind === 'societies' ? 'organization_currency_invalid' : 'organization_parent_inactive';
      fixture.nextError = { status: 409, code, details: { field } };
      await form.locator('[type=submit]').click();
      const control = form.locator(kind === 'divisions' ? '[name=parent_search]' : `[name=${field}]`);
      await expect(control).toHaveAttribute('aria-invalid', 'true');
      await expect(form.locator(`[name=${name}]`)).toHaveValue('New organization record');
      await expect(form).not.toContainText('PRIVATE SQL');
      await form.locator('[type=submit]').click();
      await expect(form).toHaveCount(0);
      await expect(page.locator('[data-org-list]')).toContainText('New organization record');
      const commands = fixture.requests.filter(row => row.method === 'POST');
      expect(commands).toHaveLength(2);
      expect(commands[0].headers['idempotency-key']).toBe(commands[1].headers['idempotency-key']);
      expect(commands[1].body).not.toHaveProperty('code');
      if (kind === 'societies') expect(commands[1].body).toMatchObject({ issuer_id: 'emi-test', base_currency: 'MXN' });
      if (kind === 'divisions') expect(commands[1].body).toMatchObject({ society_id: 'soc-test' });
      await page.locator(`[data-org-id="new-${kind}"] [data-org-action=edit]`).click();
      const edited = page.locator(`[data-form="organization-${kind}"]`);
      await edited.locator(`[name=${name}]`).fill('Edited record');
      await edited.locator('[type=submit]').click();
      await expect(page.locator('[data-org-list]')).toContainText('Edited record');
      expect(fixture.requests.filter(row => row.method === 'PATCH')[0].body).not.toHaveProperty('code');
    });
  }
  test(`${lang}: required fields and typed parent text cannot be submitted`, async ({ page }) => {
    const fixture = await setup(page, lang);
    const form = await createForm(page, 'divisions');
    await form.locator('[type=submit]').click();
    await expect(form.locator('[name=name]')).toHaveAttribute('aria-invalid', 'true');
    await form.locator('[name=name]').fill('Preserved division');
    await form.locator('[name=parent_search]').fill('not selected');
    await form.locator('[type=submit]').click();
    await expect(form.locator('[name=parent_search]')).toHaveAttribute('aria-invalid', 'true');
    expect(fixture.requests.filter(row => row.method !== 'GET')).toHaveLength(0);
    await form.locator('[name=parent_search]').fill('fixture');
    await form.locator('[data-org-results] button').first().click();
    await expect(form.locator('[name=parent_search]')).not.toHaveAttribute('aria-invalid', 'true');
  });
  test(`${lang}: failed status retains confirmed row and unknown error has safe feedback`, async ({ page }) => {
    const fixture = await setup(page, lang);
    fixture.nextError = { status: 409, code: 'organization_active_dependents' };
    await page.locator('[data-org-action=deactivate]').click();
    await expect(page.locator('[data-org-message]')).toContainText(lang === 'es' ? 'dependen' : 'depend');
    await expect(page.locator('[data-org-action=deactivate]')).toBeEnabled();
    const form = await createForm(page, 'fiscal-issuers');
    await form.locator('[name=legal_name]').fill('Keep this name');
    fixture.nextError = { status: 500, code: 'unknown_server_failure' };
    await form.locator('[type=submit]').click();
    await expect(form.locator('[data-form-feedback]')).toBeVisible();
    await expect(form.locator('[name=legal_name]')).toHaveValue('Keep this name');
    await expect(form).not.toContainText('PRIVATE SQL');
  });
}

test('bounded parent lookup, double submit and responsive container', async ({ page }) => {
  const fixture = await setup(page);
  await page.setViewportSize({ width: 390, height: 844 });
  const form = await createForm(page, 'societies');
  await form.locator('[name=name]').fill('Small screen society');
  await form.locator('[name=parent_search]').fill('fixture');
  await form.locator('[data-org-results] button').click();
  expect(fixture.requests.some(row => row.url.includes('limit=10') && row.url.includes('status=active'))).toBeTruthy();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  const columns = await form.evaluate(node => getComputedStyle(node).gridTemplateColumns.split(' ').length);
  expect(columns).toBe(1);
  fixture.delay = 350;
  await form.evaluate(node => { node.requestSubmit(); node.requestSubmit(); });
  await expect(form).toHaveCount(0);
  expect(fixture.requests.filter(row => row.method === 'POST')).toHaveLength(1);
});

test('read permissions expose only allowed catalogs and no mutation buttons', async ({ page }) => {
  await setup(page, 'en', ['admin.society.read']);
  await expect(page.locator('[data-org-kind]')).toHaveCount(1);
  await expect(page.locator('[data-org-action=create]')).toBeHidden();
  await expect(page.locator('[data-org-action=edit]')).toHaveCount(0);
  await expect(page.locator('[data-org-action=deactivate]')).toHaveCount(0);
});
