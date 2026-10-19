const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,lang,{kind='customer',editable=true,catalog=true,all=true}={}){
 const module=kind==='customer'?'sales':'purchasing';
 const state={requests:[],error:null,assignments:[],machine:{machine_id:'resource',division_ref_id:null,revision:0},centerCalls:0};
 const divisions=[{id:'div-a',code:'DIV-A',name:'Division A',society_id:'soc-a'},{id:'div-b',code:'DIV-B',name:'Division B',society_id:'soc-b'}];
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__assignments')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/commercial-organization.css"><main style="width:320px;max-width:100%;background:white;padding:12px;box-sizing:border-box"></main>'});
  if(url.pathname===`/v1/${module}/organization/divisions`){const rows=divisions.filter(row=>(row.code+' '+row.name).includes(url.searchParams.get('q')||''));return route.fulfill({json:{data:rows,meta:{total:rows.length,offset:0,limit:20}}});}
  if(url.pathname.startsWith(`/v1/${module}/${kind}s/`)){
   if(request.method()==='GET')return route.fulfill({json:{data:state.assignments.filter(row=>!url.searchParams.get('division_id')||row.division_ref_id===url.searchParams.get('division_id')),meta:{total:state.assignments.length,offset:0,limit:25}}});
   state.requests.push({payload:request.postDataJSON(),headers:request.headers(),path:url.pathname});
   if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',details:error.details||{},correlation_id:'test-assignment'}}});}
   const payload=request.postDataJSON();let row;
   {const division=url.pathname.split('/').at(-1);row={division_ref_id:division,society_ref_id:division==='div-a'?'soc-a':'soc-b',status:payload.status,revision:payload.expected_revision+1};state.assignments=state.assignments.filter(value=>value.division_ref_id!==division);state.assignments.push(row);}
   return route.fulfill({json:{data:row}});
  }
  return request.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__assignments');
 await page.evaluate(async({origin,lang,kind,editable,catalog,all,divisions,module})=>{
  window.ERCLAVE_CONFIG={localSalesApiBaseUrl:origin,localPurchasingApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  const session={permissions:[`${module}.${kind}.read`,...(editable?[`${module}.${kind}.update`]:[]),...(catalog?['costing.cost_center.read']:[])],scope:{version:2,all_divisions:all,divisions,societies:[{id:"soc-a",code:"SOC-A",name:"Society A"},{id:"soc-b",code:"SOC-B",name:"Society B"}]},capabilities:{cost_center_catalog:{available:catalog}}};
  await (await import('/features/commercial-organization.js')).mountCommercialOrganization(document.querySelector('main'),kind,{id:'resource',code:'RESOURCE-01',commercial_name:'Resource'},session,lang);
 },{origin,lang,kind,editable,catalog,all,divisions,module});return state;
}
for(const kind of ['customer','supplier']) for(const lang of ['es','en']) {
 test(`${kind} ${lang}: retry, derived society, revision and historical deactivation`, async({page})=>{
  const state=await setup(page,lang,{kind,catalog:false});
  const save=page.locator('[data-form=commercial-organization] > [type=submit]');
  await save.click();expect(state.requests).toHaveLength(0);
  await page.locator('[data-assign-lookup] [data-pick="0"]').click();
  await expect(page.locator('[data-assign-society]')).toContainText('SOC-A');
  state.error={status:503,code:'assignment_authority_unavailable'};await save.click();
  await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-assign-division]')).toContainText('DIV-A');
  await save.click();await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');
  expect(state.requests[0].headers['idempotency-key']).toBe(state.requests[1].headers['idempotency-key']);
  expect(state.requests[1].payload).toEqual({expected_revision:0,status:'active'});
  await page.locator('[name=status]').selectOption('inactive');await save.click();
  await expect(page.locator('[data-assign-history]')).toContainText(lang==='es'?'Inactiva':'Inactive');
  expect(state.requests[2].payload).toEqual({expected_revision:1,status:'inactive'});
  expect(state.centerCalls).toBe(0);await expect(page.locator('main')).not.toContainText('PRIVATE SQL');
  expect(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);
  await page.screenshot({path:test.info().outputPath('assignments.png'),fullPage:true});
 });
 test(`${kind} ${lang}: revision conflicts preserve capture; switching division uses a new key`,async({page})=>{
  const state=await setup(page,lang,{kind});const save=page.locator('[data-form=commercial-organization] > [type=submit]');
  state.assignments.push({division_ref_id:'div-b',society_ref_id:'soc-b',status:'inactive',revision:7});
  await page.locator('[data-assign-lookup] [data-pick="0"]').click();
  state.error={status:409,code:'assignment_revision_conflict'};await save.click();
  await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-assign-division]')).toContainText('DIV-A');
  await page.locator('[data-assign-lookup] [data-pick="1"]').click();await expect(page.locator('[data-assign-society]')).toContainText('SOC-B');
  await page.locator('[name=status]').selectOption('active');await save.click();
  await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');
  expect(state.requests[1].payload.expected_revision).toBe(7);expect(state.requests[1].path).toContain('/div-b');
  expect(state.requests[1].headers['idempotency-key']).not.toBe(state.requests[0].headers['idempotency-key']);
 });
 test(`${kind} ${lang}: status validation binds control; read-only cannot mutate`,async({page})=>{
  const state=await setup(page,lang,{kind});await page.locator('[data-assign-lookup] [data-pick="0"]').click();
  state.error={status:422,code:'validation_error',details:{issues:[{loc:['body','status'],type:'literal_error'}]}};
  await page.locator('[data-form=commercial-organization] > [type=submit]').click();
  await expect(page.locator('[name=status]')).toHaveAttribute('aria-invalid','true');await expect(page.locator('[name=status]')).toBeFocused();await expect(page.locator('[name=status]')).toHaveValue('active');
  await setup(page,lang,{kind,editable:false});await expect(page.locator('[type=submit]')).toHaveCount(0);await expect(page.locator('[data-pick]')).toHaveCount(0);await expect(page.locator('[name=status]')).toBeDisabled();
 });
}
