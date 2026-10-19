const { test, expect } = require('@playwright/test');
const origin = 'http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page, lang, readOnly = false) {
  const fixture = { requests: [], error: null };
  const value = {primary_color:'#6106A0',accent_color:'#F557D3',text_color:'#190F34',footer_text:'Parent',show_page_number:true,logo_data_url:null};
  await page.route('**/*', async route => {
    const request=route.request(), url=new URL(request.url());
    if(url.hostname!=='127.0.0.1') return route.abort();
    if(url.pathname==='/__config') return route.fulfill({contentType:'text/html',body:'<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/organization.css"><main class="organization-panel" style="width:320px;max-width:100%;margin:0;background:white;padding:12px;box-sizing:border-box"></main>'});
    if(url.pathname.startsWith('/v1/configuration/')) {
      if(request.method()==='GET') return route.fulfill({json:{data:{scope_type:'division',scope_id:'div',revision:0,override:false,resolved_from_scope:'corporate',resolved_from_id:'tenant',value}}});
      fixture.requests.push({payload:request.postDataJSON(),headers:request.headers()});
      if(fixture.error) { const error=fixture.error;fixture.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',correlation_id:'config-test',details:error.details||{}}}}); }
      const data=request.postDataJSON();return route.fulfill({json:{data:{scope_type:'division',scope_id:'div',revision:data.expected_revision+1,override:data.value!==null,resolved_from_scope:data.value?'division':'corporate',resolved_from_id:data.value?'div':'tenant',value:data.value||value}}});
    }
    return request.method()==='GET'?route.continue():route.abort();
  });
  await page.goto(origin+'/__config');
  await page.evaluate(async ({origin,lang,readOnly})=>{
    window.ERCLAVE_CONFIG={localApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
    (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
    await (await import('/features/scoped-configuration.js')).mountScopedConfiguration(document.querySelector('main'),'division',{id:'div',code:'DIV01',name:'Division'},readOnly?['admin.setting.read']:['admin.setting.read','admin.setting.update'],lang,()=>document.querySelector('main').replaceChildren());
  },{origin,lang,readOnly});
  await expect(page.locator('form')).toBeVisible();return fixture;
}
for(const lang of ['es','en']) {
  test(`${lang}: override error preserves capture and key; reset restores inheritance`,async({page})=>{
    const fixture=await setup(page,lang);
    await expect(page.locator('[data-config-origin]')).toContainText(lang==='es'?'Corporativo':'Corporate');
    await page.locator('[name=footer_text]').fill('Own footer');
    fixture.error={status:503,code:'service_unavailable'};
    await page.locator('[type=submit]').click();
    await expect(page.locator('[role=alert]').first()).toBeVisible();
    await expect(page.locator('[name=footer_text]')).toHaveValue('Own footer');
    await expect(page.locator('main')).not.toContainText('PRIVATE SQL');
    await page.locator('[type=submit]').click();
    await expect(page.locator('[data-config-message]')).not.toBeEmpty();
    expect(fixture.requests[0].headers['idempotency-key']).toBe(fixture.requests[1].headers['idempotency-key']);
    await expect(page.locator('[data-config-origin]')).toContainText(lang==='es'?'propia':'Custom');
    await page.locator('[data-config-reset]').click();
    await expect(page.locator('[name=footer_text]')).toHaveValue('Parent');
    expect(fixture.requests[2].payload).toEqual({expected_revision:1,value:null});
    expect(await page.locator('main').evaluate(node=>node.scrollWidth<=node.clientWidth)).toBe(true);
    await page.screenshot({path:test.info().outputPath('configuration.png'),fullPage:true});
  });
  test(`${lang}: conflict is actionable and readonly cannot save`,async({page})=>{
    const fixture=await setup(page,lang);fixture.error={status:409,code:'configuration_revision_conflict'};
    await page.locator('[type=submit]').click();
    await expect(page.locator('[role=alert]').first()).toContainText(lang==='es'?'configuración cambió':'configuration changed');
    await expect(page.locator('[name=footer_text]')).toHaveValue('Parent');
    await setup(page,lang,true);
    await expect(page.locator('[type=submit]')).toBeDisabled();await expect(page.locator('[data-config-reset]')).toBeDisabled();
  });
}
