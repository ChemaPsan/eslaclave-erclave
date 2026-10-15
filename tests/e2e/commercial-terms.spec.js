const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,kind,lang,{editable=true,values=null,catalogDown=false,assignmentActive=true}={}){
 const module=kind==='customer'?'sales':'purchasing';
 const state={requests:[],error:null,catalogDown,catalogCalls:0,data:{resource_id:'resource',division_ref_id:'div-a',current_society_ref_id:'soc-a',confirmed_society_ref_id:values?'soc-a':null,revision:values?2:0,values,requires_confirmation:!values,assignment_active:assignmentActive}};
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__terms')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/commercial-organization.css"><main style="width:320px;max-width:100%;padding:12px;box-sizing:border-box;background:white"></main>'});
  if(url.pathname===`/v1/${module}/reference-data`){state.catalogCalls++;if(state.catalogDown)return route.fulfill({status:503,json:{error:{code:'assignment_authority_unavailable',message:'PRIVATE SQL'}}});return route.fulfill({json:{data:{currencies:[{code:'MXN',name_es:'Peso mexicano',name_en:'Mexican peso'},{code:'USD',name_es:'Dólar',name_en:'Dollar'}],payment_terms:[{code:'cash',name_es:'Contado',name_en:'Cash'},{code:'net30',name_es:'30 días',name_en:'30 days'}]}}});}
  if(url.pathname.endsWith('/commercial-terms')){
   if(request.method()==='GET')return route.fulfill({json:{data:state.data}});
   state.requests.push({payload:request.postDataJSON(),headers:request.headers()});
   if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',details:error.details||{},correlation_id:'test-terms'}}});}
   const payload=request.postDataJSON();state.data={...state.data,revision:payload.expected_revision+1,values:payload.values,requires_confirmation:false,confirmed_society_ref_id:'soc-a'};return route.fulfill({json:{data:state.data}});
  }
  return request.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__terms');
 await page.evaluate(async({origin,kind,lang,editable,module})=>{
  window.ERCLAVE_CONFIG={localSalesApiBaseUrl:origin,localPurchasingApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  const session={permissions:[`${module}.${kind}.read`,...(editable?[`${module}.${kind}.update`]:[])],scope:{version:2,divisions:[{id:'div-a',code:'DIV-A',name:'Division A',society_id:'soc-a'}]}};
  await (await import('/features/commercial-terms.js')).mountCommercialTerms(document.querySelector('main'),kind,{id:'resource',code:'MASTER',title:'Master',currency:'USD',payment_terms:'net30',credit_limit:'999',lead_time_days:99},'div-a',session,lang);
 },{origin,kind,lang,editable,module});return state;
}
async function fill(page,kind){await page.locator('[name="values.currency"]').selectOption('MXN');await page.locator('[name="values.payment_terms"]').selectOption('cash');await page.locator(`[name="values.${kind==='customer'?'credit_limit':'lead_time_days'}"]`).fill('0');}
for(const kind of ['customer','supplier'])for(const lang of ['es','en']){
 test(`${kind} ${lang}: blank explicit configuration, zero, retry key, saved reload and responsive`,async({page})=>{
  const state=await setup(page,kind,lang);const save=page.locator('[type=submit]'),extra=kind==='customer'?'credit_limit':'lead_time_days';
  await expect(page.locator('[name="values.currency"]')).toHaveValue('');await expect(page.locator(`[name="values.${extra}"]`)).toHaveValue('');
  await save.click();expect(state.requests).toHaveLength(0);await fill(page,kind);
  state.error={status:503,code:'assignment_authority_unavailable'};await save.click();await expect(page.locator('[role=alert]').first()).toBeVisible();
  await expect(page.locator('[name="values.currency"]')).toHaveValue('MXN');await save.click();await expect(page.locator('[data-terms-message]')).toContainText(lang==='es'?'guardadas':'saved');
  expect(state.requests[0].headers['idempotency-key']).toBe(state.requests[1].headers['idempotency-key']);expect(state.requests[1].payload).toEqual({expected_revision:0,values:{currency:'MXN',payment_terms:'cash',[extra]:kind==='customer'?'0':0}});
  await page.locator('[data-terms-reload]').click();await expect(page.locator(`[name="values.${extra}"]`)).toHaveValue('0');
  await expect(page.locator('main')).not.toContainText('PRIVATE SQL');expect(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);
  await page.screenshot({path:test.info().outputPath('explicit-terms.png'),fullPage:true});
  state.error={status:403,code:'permission_denied'};await save.click();await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-terms-message]')).toBeEmpty();
 });
 test(`${kind} ${lang}: nested catalog error and revision conflict preserve values`,async({page})=>{
  const state=await setup(page,kind,lang);await fill(page,kind);
  state.error={status:422,code:'catalog_item_not_found',details:{issues:[{loc:['body','values','currency'],code:'catalog_item_not_found'}]}};
  await page.locator('[type=submit]').click();await expect(page.locator('[name="values.currency"]')).toHaveAttribute('aria-invalid','true');await expect(page.locator('[name="values.currency"]')).toBeFocused();
  state.error={status:409,code:'assignment_revision_conflict'};await page.locator('[type=submit]').click();await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[name="values.payment_terms"]')).toHaveValue('cash');
  await expect(page.locator('[data-terms-message]')).not.toContainText(lang==='es'?'guardadas':'saved');
 });
 test(`${kind} ${lang}: unavailable catalog retains historical values; readonly never loads catalogs`,async({page})=>{
  const values={currency:'OLD',payment_terms:'retired',[kind==='customer'?'credit_limit':'lead_time_days']:12};
  const state=await setup(page,kind,lang,{values,catalogDown:true});await expect(page.locator('[name="values.currency"]')).toHaveValue('OLD');await expect(page.locator('[type=submit]')).toBeDisabled();
  state.catalogDown=false;await page.locator('[data-terms-reload]').click();await expect(page.locator('[type=submit]')).toBeEnabled();await expect(page.locator('[name="values.currency"] option:checked')).toContainText(lang==='es'?'no vigente':'inactive');
  const read=await setup(page,kind,lang,{values,editable:false});expect(read.catalogCalls).toBe(0);await expect(page.locator('[type=submit]')).toHaveCount(0);await expect(page.locator('[name="values.currency"]')).toHaveValue('OLD');
 });
 test(`${kind} ${lang}: inactive assignment shows history and blocks editing`,async({page})=>{
  const state=await setup(page,kind,lang,{assignmentActive:false,values:{currency:'MXN',payment_terms:'cash',[kind==='customer'?'credit_limit':'lead_time_days']:0}});
  await expect(page.locator('[type=submit]')).toBeDisabled();await expect(page.locator('[data-terms-state]')).toContainText(lang==='es'?'Activa':'Activate');expect(state.catalogCalls).toBe(0);expect(state.requests).toHaveLength(0);
 });
}
