const { test, expect } = require('@playwright/test');
const origin = 'http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page, lang, kind, editable = true) {
 const state = { requests: [], queries: [], error: null, assignments: [{division_ref_id:'div-a',revision:1,status:'active',hourly_cost:'123.456789',hourly_cost_currency_code:null}], machine:{id:'machine-a',division_ref_id:'div-a',cost_per_minute:'0.123456',cost_currency:null} };
 await page.route('**/*', async route => {
  const req=route.request(), url=new URL(req.url()); if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__rates')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/hr-organization.css"><link rel="stylesheet" href="/features/production-organization.css"><main style="width:320px;max-width:100%;padding:12px;box-sizing:border-box"></main>'});
  if(url.pathname.includes('/organization/divisions'))return route.fulfill({json:{data:[{id:'div-a',code:'DIV-A',name:'A',society_id:'soc-a'}],meta:{total:1}}});
  if(url.pathname.includes('division-production-capacity')||url.pathname.includes('division-machines')){
   state.queries.push(Object.fromEntries(url.searchParams));
   if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL'}}});}
   return route.fulfill({json:{data:kind==='position'?[{position_name:'Operator',active_worker_count:1,available_minutes:480,hourly_cost:'123.456789',hourly_cost_currency_code:'MXN'}]:[{code:'M-A',name:'Machine',available_minutes:'420',cost_per_minute:'0.123456',cost_currency:'MXN'}],meta:{total:1}}});
  }
  if(url.pathname.includes('/division-assignments')||url.pathname==='/v1/production/machines/machine-a'){
   if(req.method()==='GET')return route.fulfill({json:kind==='position'?{data:state.assignments,meta:{total:1}}:{data:state.machine}});
   state.requests.push({payload:req.postDataJSON(),key:req.headers()['idempotency-key']});
   if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',details:error.details||{}}}});}
   const payload=req.postDataJSON(); if(kind==='position'){state.assignments=[{...state.assignments[0],...payload,revision:2}];return route.fulfill({json:{data:state.assignments[0]}});}
   state.machine={...state.machine,...payload};return route.fulfill({json:{data:state.machine}});
  }
  return req.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__rates');
 await page.evaluate(async({origin,lang,kind,editable})=>{
  window.ERCLAVE_CONFIG={localHrApiBaseUrl:origin,localProductionApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  const session={permissions:[kind==='position'?'hr.position.read':'production.machine.read',...(editable?[kind==='position'?'hr.position.update':'production.machine.update']:[])],scope:{version:2,divisions:[{id:'div-a',code:'DIV-A',name:'A',society_id:'soc-a'}],societies:[{id:'soc-a',base_currency:'MXN'}]}};
  if(kind==='position')await(await import('/features/hr-organization.js')).mountHrOrganization(document.querySelector('main'),'position',{id:'position-a',name:'Operator'},session,lang);
  else await(await import('/features/machine-rate.js')).mountMachineRate(document.querySelector('main'),'machine-a',session,lang);
 },{origin,lang,kind,editable});
 if(kind==='position')await page.locator('[data-edit="0"]').click();
 return state;
}
for(const lang of ['es','en'])for(const kind of ['position','machine']){
 test(lang+' '+kind+': legacy currency requires confirmation; rejection preserves exact rate and retry',async({page})=>{
  const state=await setup(page,lang,kind), form=page.locator(kind==='position'?'[data-form=hr-organization]':'[data-form=machine-rate]');
  const rate=form.locator(kind==='position'?'[name=hourly_cost]':'[name=cost_per_minute]'), currency=form.locator(kind==='position'?'[name=hourly_cost_currency_code]':'[name=cost_currency]'), confirm=form.locator('[name=confirm_rate]'), save=form.locator('[type=submit]');
  await expect(currency).toHaveValue('MXN');await expect(currency).toHaveAttribute('readonly','');await expect(confirm).not.toBeChecked();
  await save.click();expect(state.requests).toHaveLength(0);
  await rate.fill('123.456789');await confirm.check();state.error={status:422,code:kind==='position'?'hr_tariff_currency_mismatch':'operational_cost_currency_mismatch'};await save.click();
  await expect(form.locator('[role=alert]').first()).toBeVisible();await expect(rate).toHaveValue('123.456789');await expect(currency).toHaveAttribute('aria-invalid','true');await expect(page.locator('main')).not.toContainText('PRIVATE SQL');
  await save.click();await expect.poll(()=>state.requests.length).toBe(2);expect(state.requests[0].key).toBe(state.requests[1].key);
  expect(state.requests[1].payload[kind==='position'?'hourly_cost':'cost_per_minute']).toBe('123.456789');expect(state.requests[1].payload[kind==='position'?'hourly_cost_currency_code':'cost_currency']).toBe('MXN');
  await expect(confirm).not.toBeChecked();await confirm.check();await save.click();await expect.poll(()=>state.requests.length).toBe(3);expect(state.requests[2].key).not.toBe(state.requests[1].key);expect(await page.locator('main').evaluate(node=>node.scrollWidth<=node.clientWidth)).toBe(true);
 });
 test(lang+' '+kind+': denied mutation preserves capture and capacity requests explicit Division',async({page})=>{
  const state=await setup(page,lang,kind), form=page.locator(kind==='position'?'[data-form=hr-organization]':'[data-form=machine-rate]');
  await form.locator('[name=confirm_rate]').check();state.error={status:403,code:'permission_denied'};await form.locator('[type=submit]').click();await expect(form.locator('[role=alert]').first()).toBeVisible();await expect(form.locator('[name=confirm_rate]')).toBeChecked();
  if(kind==='position')await page.locator('[data-rate-capacity]').click();else{await page.locator('[name=planned_date]').fill('2026-10-08');await page.locator('[data-form=machine-capacity] [type=submit]').click();}
  await expect.poll(()=>state.queries.length).toBe(1);expect(state.queries[0].division_id).toBe('div-a');if(kind==='machine')expect(state.queries[0].planned_date).toBe('2026-10-08');
  await expect(page.locator(kind==='position'?'[data-rate-capacity-result]':'[data-machine-capacity-result]')).toContainText(kind==='position'?'480':'420');
  await setup(page,lang,kind,false);await expect(page.locator(kind==='position'?'[data-form=hr-organization] [type=submit]':'[data-form=machine-rate] [type=submit]')).toHaveCount(0);
 });
}
