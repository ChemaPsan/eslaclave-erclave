const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,lang,{kind='item',editable=true,catalog=true,all=true}={}){
 const state={requests:[],error:null,assignments:[],warehouse:{warehouse_id:'resource',division_ref_id:null,revision:0},centerCalls:0};
 const divisions=[{id:'div-a',code:'DIV-A',name:'Division A',society_id:'soc-a'},{id:'div-b',code:'DIV-B',name:'Division B',society_id:'soc-b'}];
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__assignments')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/inventory-organization.css"><main style="width:320px;max-width:100%;background:white;padding:12px;box-sizing:border-box"></main>'});
  if(url.pathname==='/v1/inventory/organization/divisions'){const rows=divisions.filter(row=>(row.code+' '+row.name).includes(url.searchParams.get('q')||''));return route.fulfill({json:{data:rows,meta:{total:rows.length,offset:0,limit:20}}});}
  if(url.pathname==='/v1/cost-centers/eligible'){state.centerCalls++;return route.fulfill({json:{data:[{id:'cc-'+url.searchParams.get('division_id'),code:'CC-01',name:'Center',division_ref_id:url.searchParams.get('division_id'),status:'active',revision:1}],meta:{total:1,offset:0,limit:20}}});}
  if(url.pathname.startsWith('/v1/inventory/warehouses/')||url.pathname.startsWith('/v1/inventory/items/')){
   if(request.method()==='GET')return route.fulfill({json:kind==='warehouse'?{data:state.warehouse}:{data:state.assignments.filter(row=>!url.searchParams.get('division_id')||row.division_ref_id===url.searchParams.get('division_id')),meta:{total:state.assignments.length,offset:0,limit:25}}});
   state.requests.push({payload:request.postDataJSON(),headers:request.headers(),path:url.pathname});
   if(state.error){const error=state.error;state.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',details:error.details||{},correlation_id:'test-assignment'}}});}
   const payload=request.postDataJSON();let row;
   if(kind==='warehouse'){row={warehouse_id:'resource',division_ref_id:payload.division_ref_id,revision:payload.expected_revision+1};state.warehouse=row;}
   else {const division=url.pathname.split('/').at(-1);row={item_id:'resource',division_ref_id:division,cost_center_ref_id:payload.cost_center_ref_id,cost_center_snapshot:payload.cost_center_ref_id?{id:payload.cost_center_ref_id,code:'CC-01',name:'Center'}:null,status:payload.status,revision:payload.expected_revision+1};state.assignments=state.assignments.filter(value=>value.division_ref_id!==division);state.assignments.push(row);}
   return route.fulfill({json:{data:row}});
  }
  return request.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__assignments');
 await page.evaluate(async({origin,lang,kind,editable,catalog,all,divisions})=>{
  window.ERCLAVE_CONFIG={localInventoryApiBaseUrl:origin,localCostingApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  const session={permissions:[`inventory.${kind}.read`,...(editable?[`inventory.${kind}.update`]:[]),...(catalog?['costing.cost_center.read']:[])],scope:{version:2,all_divisions:all,divisions},capabilities:{cost_center_catalog:{available:catalog}}};
  await (await import('/features/inventory-organization.js')).mountInventoryOrganization(document.querySelector('main'),kind,{id:'resource',code:'RESOURCE-01',name:'Resource'},session,lang);
 },{origin,lang,kind,editable,catalog,all,divisions});return state;
}
for(const lang of ['es','en']){
 test(`${lang}: assignment retry preserves division and optional center; deactivation keeps history`,async({page})=>{
  const state=await setup(page,lang);await page.locator('[data-assign-lookup] [data-pick="0"]').click();
  await expect(page.locator('[data-assign-center-lookup] [data-pick="0"]')).toBeEnabled();await page.locator('[data-assign-center-lookup] [data-pick="0"]').click();
  state.error={status:503,code:'assignment_authority_unavailable'};const save=page.locator('[data-form=inventory-organization] > [type=submit]');await save.click();
  await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-assign-division]')).toContainText('DIV-A');await expect(page.locator('[data-assign-center-area]')).toContainText('CC-01');
  await save.click();await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');
  expect(state.requests[0].headers['idempotency-key']).toBe(state.requests[1].headers['idempotency-key']);expect(state.requests[1].payload).toEqual({expected_revision:0,status:'active',cost_center_ref_id:'cc-div-a'});
  await page.locator('[name=status]').selectOption('inactive');await save.click();await expect(page.locator('[data-assign-history]')).toContainText(lang==='es'?'Inactiva':'Inactive');
  expect(state.requests[2].payload.cost_center_ref_id).toBe('cc-div-a');expect(state.requests[2].payload.expected_revision).toBe(1);
  await expect(page.locator('main')).not.toContainText('PRIVATE SQL');expect(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);
  await page.screenshot({path:test.info().outputPath('assignments.png'),fullPage:true});
 });
 test(`${lang}: center rejection highlights selector and changing division clears selected center`,async({page})=>{
  const state=await setup(page,lang);await page.locator('[data-assign-lookup] [data-pick="0"]').click();await page.locator('[data-assign-center-lookup] [data-pick="0"]').click();
  state.error={status:422,code:'assignment_center_invalid'};await page.locator('[data-form=inventory-organization] > [type=submit]').click();
  await expect(page.locator('[data-assign-center-lookup] [name=q]')).toHaveAttribute('aria-invalid','true');
  await page.locator('[data-assign-lookup] [data-pick="1"]').click();await expect(page.locator('[data-assign-center-area] strong')).toHaveText(lang==='es'?'Sin centro':'No cost center');
  await page.locator('[data-form=inventory-organization] > [type=submit]').click();await expect.poll(()=>state.requests.length).toBe(2);expect(state.requests[1].path).toContain('/div-b');expect(state.requests[1].payload.cost_center_ref_id).toBe(null);
 });
 test(`${lang}: catalog off does not prevent assignment; read-only has no mutations`,async({page})=>{
  const state=await setup(page,lang,{catalog:false});await page.locator('[data-assign-lookup] [data-pick="0"]').click();await page.locator('[data-form=inventory-organization] > [type=submit]').click();await expect(page.locator('[data-assign-message]')).toContainText(lang==='es'?'guardada':'saved');expect(state.centerCalls).toBe(0);expect(state.requests[0].payload.cost_center_ref_id).toBe(null);
  await setup(page,lang,{editable:false});await expect(page.locator('[data-form=inventory-organization] > [type=submit]')).toHaveCount(0);await expect(page.locator('[data-assign-lookup] [data-pick]')).toHaveCount(0);
 });
 test(`${lang}: warehouse assignment becomes fixed and restricted scope cannot claim it`,async({page})=>{
  const state=await setup(page,lang,{kind:'warehouse'});await page.locator('[data-assign-lookup] [data-pick="0"]').click();state.error={status:409,code:'assignment_revision_conflict'};
  await page.locator('[data-form=inventory-organization] > [type=submit]').click();await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-assign-division]')).toContainText('DIV-A');
  await page.locator('[data-form=inventory-organization] > [type=submit]').click();await expect(page.locator('[data-assign-lookup]')).toBeEmpty();await expect(page.locator('[data-form=inventory-organization] > [type=submit]')).toBeHidden();
  expect(state.requests[1].payload).toEqual({expected_revision:0,division_ref_id:'div-a'});
  await setup(page,lang,{kind:'warehouse',all:false});await expect(page.locator('[data-assign-lookup] [data-pick]')).toHaveCount(0);await expect(page.locator('[data-form=inventory-organization] > [type=submit]')).toBeHidden();
 });
}
