const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,lang){
 const fixture={requests:[],lookups:[],failure:503};
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__stock')return route.fulfill({contentType:'text/html',body:'<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/commercial-organization.css"><main style="width:320px;max-width:100%;box-sizing:border-box;background:var(--panel);color:var(--text);padding:12px"></main>'});
  if(url.pathname.endsWith('/stock-options')){fixture.lookups.push(Object.fromEntries(url.searchParams));return route.fulfill({json:{data:{inventory_item_id:'item',item_code:'ITEM',item_name:'Eligible item',unit:'PZA',cost_currency:'USD',warehouses:[{warehouse_id:'wh',warehouse_code:'WH-A',warehouse_name:'Division A warehouse',available_quantity:'10'}],has_more:false}}});}
  if(url.pathname.endsWith('/fulfillment')){fixture.requests.push({payload:request.postDataJSON(),headers:request.headers()});return fixture.failure?route.fulfill({status:fixture.failure,json:{error:{code:fixture.failure===503?'service_unavailable':'operational_exchange_rate_invalid',message:'PRIVATE SQL',details:fixture.failure===422?{field:'cost_exchange_rate'}:{}}}}):route.fulfill({json:{data:{id:'order'}}});}
  return request.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__stock');
 await page.evaluate(async({origin,lang})=>{
  window.ERCLAVE_CONFIG={localApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);window.stockSaved=0;
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  (await import('/features/scoped-stock-fulfillment.js')).mountScopedStockFulfillment(document.querySelector('main'),{id:'order',fields:{currency:'MXN',divisionRefId:'division-a',lines:[{id:'line',productServiceType:'product',productServiceName:'Stock product',quantity:2,deliveredQuantity:0,unit:'PZA',fulfillmentMode:'pending'}]}},{lang,onSaved:()=>{window.stockSaved++;}});
 },{origin,lang});
 await expect(page.locator('select option')).toHaveCount(2);return fixture;
}
for(const lang of ['es','en']){
 test(`${lang}: scoped stock preserves selection, exchange rate and retry identity`,async({page})=>{
  const fixture=await setup(page,lang),form=page.locator('[data-scoped-stock]'),rate=form.locator('[name=cost_exchange_rate]');
  await expect(rate).toBeVisible();await form.locator('select').selectOption('wh');await rate.fill('20.123456789012');
  await form.locator('[type=submit]').click();await expect(form.locator('[type=submit]')).toBeEnabled();await expect(rate).toHaveValue('20.123456789012');await expect(form.locator('select')).toHaveValue('wh');await expect(form).not.toContainText('PRIVATE SQL');
  await form.locator('[type=submit]').click();await expect.poll(()=>fixture.requests.length).toBe(2);expect(fixture.requests[0].headers['idempotency-key']).toBe(fixture.requests[1].headers['idempotency-key']);expect(fixture.requests[0].payload.cost_exchange_rate).toBe('20.123456789012');
  fixture.failure=422;await form.locator('[type=submit]').click();await expect(rate).toHaveAttribute('aria-invalid','true');await expect.poll(()=>page.evaluate(()=>window.stockSaved)).toBe(0);
  fixture.failure=0;await rate.fill('20');await form.locator('[type=submit]').click();await expect.poll(()=>page.evaluate(()=>window.stockSaved)).toBe(1);expect(fixture.requests.at(-1).headers['idempotency-key']).not.toBe(fixture.requests[0].headers['idempotency-key']);
  expect(await page.locator('main').evaluate(node=>node.scrollWidth<=node.clientWidth+1)).toBe(true);
  await page.screenshot({path:test.info().outputPath('scoped-stock.png'),fullPage:true});
 });
 test(`${lang}: warehouse search keeps the captured warehouse and bounds results`,async({page})=>{
  const fixture=await setup(page,lang);await page.locator('select').selectOption('wh');await page.locator('[data-stock-query]').fill('WH-A');await page.locator('[data-find]').click();await expect.poll(()=>fixture.lookups.length).toBe(2);expect(fixture.lookups[1].q).toBe('WH-A');expect(fixture.lookups[1].line_id).toBe('line');await expect(page.locator('select')).toHaveValue('wh');await expect(page.locator('[data-next]')).toBeDisabled();expect(fixture.requests).toHaveLength(0);
 });
}

for(const lang of ['es','en'])test(`${lang}: manual stock entry captures explicit Society cost`,async({page})=>{
 await page.route('**/*',async route=>{const url=new URL(route.request().url());if(url.hostname!=='127.0.0.1')return route.abort();if(url.pathname==='/__movement')return route.fulfill({contentType:'text/html',body:'<main><form><div class="form-grid"><select name="warehouseId"><option value="wh">WH</option></select><select name="movementType"><option value="entry">Entry</option><option value="exit">Exit</option></select></div><button type="submit">Save</button></form></main>'});if(url.pathname.endsWith('/operation-context'))return route.fulfill({json:{data:{division_ref_id:'div',division_code:'DIV',division_name:'Division',society_ref_id:'soc',cost_currency:'USD'}}});return route.continue();});
 await page.goto(origin+'/__movement');await page.evaluate(async({origin,lang})=>{window.ERCLAVE_CONFIG={localApiBaseUrl:origin};const form=document.querySelector('form');form.onsubmit=e=>e.preventDefault();(await import('/features/movement-cost-context.js')).mountMovementCostContext(form,lang);},{origin,lang});
 await expect(page.locator('[data-movement-currency]')).toContainText('USD');await expect(page.locator('[name=unitCost]')).toBeVisible();await expect(page.locator('[name=unitCost]')).toHaveAttribute('required','');await page.locator('[name=unitCost]').fill('0');expect(await page.locator('form').evaluate(form=>form.checkValidity())).toBe(true);await page.locator('[name=movementType]').selectOption('exit');await expect(page.locator('[name=unitCost]')).toBeHidden();expect(await page.locator('form').evaluate(form=>new FormData(form).has('unitCost'))).toBe(false);
});
