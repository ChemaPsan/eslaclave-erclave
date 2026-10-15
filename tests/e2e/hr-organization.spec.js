const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function confirmActiveRate(page) {
 const form = page.locator('[data-form=hr-organization]');
 await expect(form.locator('[type=submit]')).toBeEnabled();
 const checkbox = form.locator('[name=confirm_rate]');
 if (await checkbox.count() && await form.locator('[name=status]').inputValue() === 'active') {
  await expect(checkbox).toBeEnabled();
  await checkbox.check();
 }
}
async function setup(page,lang,{kind='position',editable=true,catalog=true,all=true}={}){
 const state={requests:[],error:null,assignments:[],machine:{machine_id:'resource',division_ref_id:null,revision:0},centerCalls:0};
 const divisions=[{id:'div-a',code:'DIV-A',name:'Division A',society_id:'soc-a'},{id:'div-b',code:'DIV-B',name:'Division B',society_id:'soc-b'}];
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__assignments')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/hr-organization.css"><main style="width:320px;max-width:100%;background:white;padding:12px;box-sizing:border-box"></main>'});
  if(url.pathname==='/v1/hr/organization/divisions'){const rows=divisions.filter(row=>(row.code+' '+row.name).includes(url.searchParams.get('q')||''));return route.fulfill({json:{data:rows,meta:{total:rows.length,offset:0,limit:20}}});}
  if(url.pathname==='/v1/cost-centers/eligible'){state.centerCalls++;return route.fulfill({json:{data:[{id:'cc-'+url.searchParams.get('division_id'),code:'CC-01',name:'Center',division_ref_id:url.searchParams.get('division_id'),status:'active',revision:1}],meta:{total:1,offset:0,limit:20}}});}
  if(url.pathname.startsWith('/v1/hr/workers/')||url.pathname.startsWith('/v1/hr/positions/')){
   if(request.method()==='GET')return route.fulfill({json:{data:state.assignments.filter(row=>!url.searchParams.get('division_id')||row.division_ref_id===url.searchParams.get('division_id')),meta:{total:state.assignments.length,offset:0,limit:25}}});
   state.requests.push({payload:request.postDataJSON(),headers:request.headers(),path:url.pathname});
   if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',details:error.details||{},correlation_id:'test-assignment'}}});}
   const payload=request.postDataJSON();let row;
   {const division=url.pathname.split('/').at(-1);row={position_id:'resource',worker_id:'resource',labor_position_id:'role',hourly_cost:payload.hourly_cost,hourly_cost_currency_code:payload.hourly_cost_currency_code,division_ref_id:division,cost_center_ref_id:payload.cost_center_ref_id,cost_center_snapshot:payload.cost_center_ref_id?{id:payload.cost_center_ref_id,code:'CC-01',name:'Center'}:null,status:payload.status,revision:payload.expected_revision+1};state.assignments=state.assignments.filter(value=>value.division_ref_id!==division);state.assignments.push(row);}
   return route.fulfill({json:{data:row}});
  }
  return request.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__assignments');
 await page.evaluate(async({origin,lang,kind,editable,catalog,all,divisions})=>{
  window.ERCLAVE_CONFIG={localHrApiBaseUrl:origin,localCostingApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  const session={permissions:[`hr.${kind}.read`,...(editable?[`hr.${kind}.update`]:[]),...(catalog?['costing.cost_center.read']:[])],scope:{version:2,all_divisions:all,divisions,societies:[{id:'soc-a',base_currency:'MXN'},{id:'soc-b',base_currency:'USD'}]},capabilities:{cost_center_catalog:{available:catalog}}};
  await (await import('/features/hr-organization.js')).mountHrOrganization(document.querySelector('main'),kind,{id:'resource',code:'RESOURCE-01',name:'Resource',hourlyCost:'0'},session,lang);
 },{origin,lang,kind,editable,catalog,all,divisions});return state;
}
for(const lang of ['es','en']){
 test(`${lang}: assignment retry preserves division and optional center; deactivation keeps history`,async({page})=>{
  const state=await setup(page,lang);await page.locator('[data-assign-lookup] [data-pick="0"]').click();
  await expect(page.locator('[data-assign-center-lookup] [data-pick="0"]')).toBeEnabled();await page.locator('[data-assign-center-lookup] [data-pick="0"]').click();
  state.error={status:503,code:'assignment_authority_unavailable'};const save=page.locator('[data-form=hr-organization] > [type=submit]');await confirmActiveRate(page);await save.click();
  await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-assign-division]')).toContainText('DIV-A');await expect(page.locator('[data-assign-center-area]')).toContainText('CC-01');
  await confirmActiveRate(page);await save.click();await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');
  expect(state.requests[0].headers['idempotency-key']).toBe(state.requests[1].headers['idempotency-key']);expect(state.requests[1].payload).toEqual({expected_revision:0,status:'active',hourly_cost:'0',hourly_cost_currency_code:'MXN',cost_center_ref_id:'cc-div-a'});
  await page.locator('[name=status]').selectOption('inactive');await confirmActiveRate(page);await save.click();await expect(page.locator('[data-assign-history]')).toContainText(lang==='es'?'Inactiva':'Inactive');
  expect(state.requests[2].payload.cost_center_ref_id).toBe('cc-div-a');expect(state.requests[2].payload.expected_revision).toBe(1);
  await expect(page.locator('main')).not.toContainText('PRIVATE SQL');expect(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);
  await page.screenshot({path:test.info().outputPath('assignments.png'),fullPage:true});
 });
 test(`${lang}: center rejection highlights selector and changing division clears selected center`,async({page})=>{
  const state=await setup(page,lang);await page.locator('[data-assign-lookup] [data-pick="0"]').click();await page.locator('[data-assign-center-lookup] [data-pick="0"]').click();
  state.error={status:422,code:'assignment_center_invalid'};await confirmActiveRate(page);await page.locator('[data-form=hr-organization] > [type=submit]').click();
  await expect(page.locator('[data-assign-center-lookup] [name=q]')).toHaveAttribute('aria-invalid','true');
  await page.locator('[data-assign-lookup] [data-pick="1"]').click();await expect(page.locator('[data-assign-center-area] strong')).toHaveText(lang==='es'?'Sin centro':'No cost center');
  await confirmActiveRate(page);await page.locator('[data-form=hr-organization] > [type=submit]').click();await expect.poll(()=>state.requests.length).toBe(2);expect(state.requests[1].path).toContain('/div-b');expect(state.requests[1].payload.cost_center_ref_id).toBe(null);
 });
 test(`${lang}: catalog off does not prevent assignment; read-only has no mutations`,async({page})=>{
  const state=await setup(page,lang,{catalog:false});await page.locator('[data-assign-lookup] [data-pick="0"]').click();await confirmActiveRate(page);await page.locator('[data-form=hr-organization] > [type=submit]').click();await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');expect(state.centerCalls).toBe(0);expect(state.requests[0].payload.cost_center_ref_id).toBe(null);
  await setup(page,lang,{editable:false});await expect(page.locator('[data-form=hr-organization] > [type=submit]')).toHaveCount(0);await expect(page.locator('[data-assign-lookup] [data-pick]')).toHaveCount(0);
 });
 test(`${lang}: rate errors preserve exact capture and bind to hourly cost`,async({page})=>{
  const state=await setup(page,lang);await page.locator('[data-assign-lookup] [data-pick="0"]').click();
  const rate=page.locator('[name=hourly_cost]'),save=page.locator('[data-form=hr-organization] > [type=submit]');
  await rate.fill('-1');await confirmActiveRate(page);await save.click();expect(state.requests).toHaveLength(0);
  await rate.fill('123.456789');state.error={status:422,code:'invalid_field',details:{issues:[{field:'hourly_cost',code:'invalid_field'}]}};
  await confirmActiveRate(page);await save.click();await expect(rate).toHaveAttribute('aria-invalid','true');await expect(rate).toBeFocused();await expect(rate).toHaveValue('123.456789');
  await confirmActiveRate(page);await save.click();await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');
  expect(state.requests[1].payload.hourly_cost).toBe('123.456789');
  await rate.fill('999');await page.locator('[name=status]').selectOption('inactive');await expect(rate).toHaveValue('123.456789');await expect(rate).toBeDisabled();
  await confirmActiveRate(page);await save.click();expect(state.requests[2].payload.hourly_cost).toBe('123.456789');
 });
 test(`${lang}: worker eligibility rejection keeps division and sends no costing fields`,async({page})=>{
  const state=await setup(page,lang,{kind:'worker'});await page.locator('[data-assign-lookup] [data-pick="0"]').click();
  state.error={status:409,code:'hr_assignment_position_unavailable'};const save=page.locator('[data-form=hr-organization] > [type=submit]');await confirmActiveRate(page);await save.click();
  await expect(page.locator('[role=alert]').first()).toContainText(lang==='es'?'puesto':'position');await expect(page.locator('[data-assign-division]')).toContainText('DIV-A');
  await expect(page.locator('[name=hourly_cost]')).toHaveCount(0);expect(state.centerCalls).toBe(0);
  await confirmActiveRate(page);await save.click();await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');
  expect(state.requests[1].payload).toEqual({expected_revision:0,status:'active'});
  await page.locator('[name=status]').selectOption('inactive');await confirmActiveRate(page);await save.click();await expect(page.locator('[data-assign-history]')).toContainText(lang==='es'?'Inactiva':'Inactive');
  await setup(page,lang,{kind:'worker',editable:false});await expect(page.locator('[data-form=hr-organization] > [type=submit]')).toHaveCount(0);
 });
}
