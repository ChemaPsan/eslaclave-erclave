const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,lang,{editable=true,status='draft',assigned=false}={}){
 const division={id:'div-a',code:'DIV-A',name:'Division A',society_id:'soc-a'},snapshot={division,terms_revision:3,values:{currency:'MXN',payment_terms:'cash',credit_limit:'0.00'}};
 const state={requests:[],error:null,quote:{id:'quote',code:'QUOTE-01',status,organization_revision:assigned?1:0,division_ref_id:assigned?'div-a':null,society_ref_id:assigned?'soc-a':null,commercial_terms_snapshot:assigned?snapshot:null}};
 await page.route('**/*',async route=>{const request=route.request(),url=new URL(request.url());if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__context')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/commercial-organization.css"><main style="width:320px;max-width:100%;padding:12px;background:white;box-sizing:border-box"></main>'});
  if(url.pathname==='/v1/sales/organization/quote-divisions')return route.fulfill({json:{data:[division],meta:{total:1,offset:0,limit:20}}});
  if(url.pathname==='/v1/sales/quotes/quote')return route.fulfill({json:{data:state.quote}});
  if(url.pathname.endsWith('/organization-context')){state.requests.push({payload:request.postDataJSON(),headers:request.headers()});if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',correlation_id:'quote-test'}}});}state.quote={...state.quote,division_ref_id:'div-a',society_ref_id:'soc-a',organization_revision:state.quote.organization_revision+1,commercial_terms_snapshot:snapshot};return route.fulfill({json:{data:state.quote}});}
  return request.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__context');await page.evaluate(async({origin,lang,editable})=>{window.ERCLAVE_CONFIG={localSalesApiBaseUrl:origin};(await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});await(await import('/features/quote-context.js')).mountQuoteContext(document.querySelector('main'),'quote',{permissions:['sales.quote.read',...(editable?['sales.quote.update']:[])]},lang);},{origin,lang,editable});return state;
}
for(const lang of ['es','en']){
 test(`${lang}: required Division, stable retry, saved snapshot and fixed selection`,async({page})=>{
  const state=await setup(page,lang),save=page.locator('[type=submit]');await save.click();expect(state.requests).toHaveLength(0);await page.locator('[data-pick="0"]').click();state.error={status:503,code:'authority_unavailable'};await save.click();await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-quote-division]')).toContainText('DIV-A');await save.click();await expect(page.locator('[data-quote-message]')).toContainText(lang==='es'?'guardado':'saved');
  expect(state.requests[0].headers['idempotency-key']).toBe(state.requests[1].headers['idempotency-key']);expect(state.requests[1].payload).toEqual({division_ref_id:'div-a',expected_revision:0});await expect(page.locator('[data-pick]')).toHaveCount(0);await expect(page.locator('[data-quote-snapshot]')).toContainText('MXN');
  expect(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);await page.screenshot({path:test.info().outputPath('quote-context.png'),fullPage:true});
  state.error={status:409,code:'quote_context_currency_mismatch'};await save.click();await expect(page.locator('[role=alert]').first()).toContainText(lang==='es'?'moneda':'currency');await expect(page.locator('[data-quote-message]')).toBeEmpty();await expect(page.locator('main')).not.toContainText('PRIVATE SQL');
 });
 test(`${lang}: rejected resource keeps selection and cannot report success`,async({page})=>{
  const state=await setup(page,lang);await page.locator('[data-pick="0"]').click();state.error={status:422,code:'quote_context_resource_unavailable'};await page.locator('[type=submit]').click();await expect(page.locator('[role=alert]').first()).toContainText(lang==='es'?'División':'Division');await expect(page.locator('[data-quote-division]')).toContainText('DIV-A');expect(state.quote.organization_revision).toBe(0);
 });
 test(`${lang}: historical snapshot readonly and issued quote cannot refresh`,async({page})=>{
  await setup(page,lang,{editable:false,assigned:true});await expect(page.locator('[type=submit]')).toHaveCount(0);await expect(page.locator('[data-quote-snapshot]')).toContainText('0.00');await expect(page.locator('[data-pick]')).toHaveCount(0);
  const state=await setup(page,lang,{assigned:true,status:'quoted'});await expect(page.locator('[type=submit]')).toBeDisabled();expect(state.requests).toHaveLength(0);
 });
}
