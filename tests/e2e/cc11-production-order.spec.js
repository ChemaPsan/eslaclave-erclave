const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,lang,{release=true,scope=true}={}){
 const state={validations:[],creates:[],lookups:[],error:null,blocked:false};
 const recipe={id:'recipe-a',code:'REC-A',name:'Product A',current_version_id:'version-a',versions:[{id:'version-a',status:'approved',base_unit:'H87',stages:[{id:'stage-a',name:'Phase A',status:'active'},{id:'stage-b',name:'Phase B',status:'active'}]}]};
 await page.route('**/*',async route=>{
  const req=route.request(),url=new URL(req.url());if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__cc11')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/production-order-context.css"><main style="width:320px;max-width:100%;padding:12px;box-sizing:border-box"></main>'});
  if(url.pathname==='/v1/production/division-recipes'||url.pathname==='/v1/hr/division-workers'){
   state.lookups.push({path:url.pathname,query:Object.fromEntries(url.searchParams)});
   return route.fulfill({json:{data:url.pathname.includes('recipes')?[recipe]:[{id:'worker-'+url.searchParams.get('division_id'),full_name:'Worker '+url.searchParams.get('division_id')}],meta:{total:1,limit:20,offset:0}}});
  }
  if(url.pathname==='/v1/production/resource-validations'){
   const payload=req.postDataJSON();state.validations.push({payload,key:req.headers()['idempotency-key']});
   if(state.error?.where==='validation'){const error=state.error;state.error=null;return route.fulfill({status:422,json:{error:{code:error.code,message:'PRIVATE SQL',details:error.details}}});}
   return route.fulfill({json:{data:{can_release:!state.blocked,cost_currency:payload.division_ref_id==='div-a'?'MXN':'USD',original_planned_cost:'123.456789',rows:[{resource_name:'Material A',required_quantity:2,available_quantity:state.blocked?0:20,unit:'H87',original_total_cost:'123.456789'}]}}});
  }
  if(url.pathname==='/v1/production/orders'){
   const payload=req.postDataJSON();state.creates.push({payload,key:req.headers()['idempotency-key']});
   if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status||503,json:{error:{code:error.code||'assignment_authority_unavailable',message:'PRIVATE SQL',details:error.details||{}}}});}
   return route.fulfill({json:{data:{id:'order-a',code:'OP-A',organization_context:{division_ref_id:payload.division_ref_id,cost_currency:'MXN'}}}});
  }
  return req.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__cc11');await page.evaluate(async({origin,lang,release,scope})=>{
  window.ERCLAVE_CONFIG={localProductionApiBaseUrl:origin,localHrApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  const session={permissions:['production.order.validate',...(release?['production.order.release']:[])],scope:{version:2,divisions:scope?[{id:'div-a',code:'DIV-A',name:'A',society_id:'soc-a'},{id:'div-b',code:'DIV-B',name:'B',society_id:'soc-b'}]:[],societies:[{id:'soc-a',name:'Society A',base_currency:'MXN'},{id:'soc-b',name:'Society B',base_currency:'USD'}]}};
  window.saved=[];await(await import('/features/production-order-context.js')).mountProductionOrderForm(document.querySelector('main'),session,{lang,today:'2026-10-08',onSaved:saved=>window.saved.push(saved)});
 },{origin,lang,release,scope});return state;
}
async function selectResources(page,division=0){
 await page.locator('[data-division-lookup] [data-choice="'+division+'"]').click();
 await page.locator('[data-recipe-lookup] [data-choice="0"]').click();
 await page.locator('[data-worker-lookup] [data-choice="0"]').click();
 await expect(page.locator('[data-stage-lookups] [data-choice="0"]')).toHaveCount(2);
 for(const node of await page.locator('[data-stage-lookups] [data-choice="0"]').all())await node.click();
}
for(const lang of ['es','en']){
 test(lang+': explicit Division, original currency, second-stage errors, stable uncertain replay',async({page})=>{
  const state=await setup(page,lang);await page.locator('[type=submit]').click();expect(state.creates).toHaveLength(0);
  await selectResources(page);await page.locator('[name=quantity]').fill('2.5');
  state.error={status:422,code:'validation_error',details:{issues:[{loc:['body','stage_assignments',1,'responsible_worker_id'],type:'value_error',msg:'PRIVATE SQL'}]}};
  await page.locator('[type=submit]').click();await expect.poll(()=>state.creates.length).toBe(1);
  await expect(page.locator('[data-stage-lookups] input').nth(1)).toHaveAttribute('aria-invalid','true');await expect(page.locator('[data-stage-lookups] input').nth(0)).not.toHaveAttribute('aria-invalid','true');await expect(page.locator('[name=quantity]')).toHaveValue('2.5');
  await page.locator('[type=submit]').click();await expect.poll(()=>state.creates.length).toBe(2);expect(state.creates[1].key).toBe(state.creates[0].key);expect(state.validations).toHaveLength(1);expect(state.creates[1].payload.division_ref_id).toBe('div-a');expect(state.creates[1].payload.stage_assignments[1]).toEqual({recipe_stage_id:'stage-b',responsible_worker_id:'worker-div-a'});
  await expect(page.locator('main')).not.toContainText('PRIVATE SQL');expect(await page.locator('main').evaluate(node=>node.scrollWidth<=node.clientWidth)).toBe(true);
 });
 test(lang+': change Division invalidates preview, recipe and workers while preserving capture',async({page})=>{
  const state=await setup(page,lang);await selectResources(page);await page.locator('[name=quantity]').fill('3');await page.locator('[data-validate]').click();await expect(page.locator('[data-validation-preview]')).toContainText('MXN');
  await page.locator('[data-division-lookup] [data-choice="1"]').click();await expect(page.locator('[data-validation-preview]')).toBeEmpty();await expect(page.locator('[data-worker-lookup]')).toBeEmpty();await expect(page.locator('[name=quantity]')).toHaveValue('3');await expect(page.locator('[data-society-context]')).toContainText('USD');
  await page.locator('[type=submit]').click();expect(state.creates).toHaveLength(0);await page.locator('[data-recipe-lookup] [data-choice="0"]').click();await page.locator('[data-worker-lookup] [data-choice="0"]').click();await expect(page.locator('[data-stage-lookups] [data-choice="0"]')).toHaveCount(2);for(const node of await page.locator('[data-stage-lookups] [data-choice="0"]').all())await node.click();
  state.blocked=true;await page.locator('[type=submit]').click();await expect(page.locator('[data-validation-preview]')).toContainText('USD');expect(state.creates).toHaveLength(0);expect(state.validations.at(-1).payload.division_ref_id).toBe('div-b');expect(state.lookups.filter(row=>row.path.includes('workers')).at(-1).query.division_id).toBe('div-b');
 });
 test(lang+': no scope or release permission cannot create; denial preserves selected resources',async({page})=>{
  await setup(page,lang,{scope:false});await expect(page.locator('[type=submit]')).toBeDisabled();
  await setup(page,lang,{release:false});await expect(page.locator('[type=submit]')).toHaveCount(0);await selectResources(page);await page.locator('[data-validate]').click();await expect(page.locator('[data-validation-preview]')).toContainText('123.456789');
  const state=await setup(page,lang);await selectResources(page);state.error={status:403,code:'permission_denied'};await page.locator('[type=submit]').click();await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-worker-lookup] [data-selected]')).toContainText('Worker div-a');expect(await page.evaluate(()=>window.saved.length)).toBe(0);
 });
}
