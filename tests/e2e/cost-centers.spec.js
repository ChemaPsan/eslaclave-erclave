const { test, expect } = require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,lang,readOnly=false,inactive=false){
 const fixture={requests:[],error:null,rows:[],queries:[]};
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());
  if(url.hostname!=='127.0.0.1')return route.abort();
  if(url.pathname==='/__centers')return route.fulfill({contentType:'text/html',body:'<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/organization.css"><main class="organization-panel" style="width:320px;max-width:100%;background:white;padding:12px;box-sizing:border-box"></main>'});
  if(url.pathname.startsWith('/v1/cost-centers')){
   if(request.method()==='GET'){fixture.queries.push(url.searchParams.toString());return route.fulfill({json:{data:fixture.rows,meta:{total:fixture.rows.length,limit:25,offset:0}}});}
   fixture.requests.push({payload:request.postDataJSON(),headers:request.headers(),method:request.method(),path:url.pathname});
   if(fixture.error){const error=fixture.error;fixture.error=null;return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',correlation_id:'test-cost',details:error.details||{}}}});}
   const payload=request.postDataJSON();let row;
   if(url.pathname==='/v1/cost-centers'){row={id:'cc',code:'CC-000001',name:payload.name,division_ref_id:payload.division_ref_id,status:'active',revision:1};fixture.rows.push(row);}
   else {row=fixture.rows[0];Object.assign(row,request.method()==='PATCH'?{name:payload.name}:{status:url.pathname.endsWith('/deactivate')?'inactive':'active'});row.revision++;}
   return route.fulfill({status:request.method()==='POST'&&url.pathname==='/v1/cost-centers'?201:200,json:{data:row}});
  }
  return request.method()==='GET'?route.continue():route.abort();
 });
 await page.goto(origin+'/__centers');
 await page.evaluate(async ({origin,lang,readOnly,inactive})=>{
  window.ERCLAVE_CONFIG={localApiBaseUrl:origin,localCostingApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);
  (await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  (await import('/features/cost-centers.js')).mountCostCenters(document.querySelector('main'),{id:'division',code:'DIV-000001',name:'Division',status:inactive?'inactive':'active'},(readOnly?['read']:['read','create','update','status']).map(p=>'costing.cost_center.'+p),lang);
 },{origin,lang,readOnly,inactive});
 await expect(page.locator('[data-cc-search] button')).toBeEnabled();return fixture;
}
for(const lang of ['es','en']){
 test(`${lang}: create retry, edit, rejected transition and history`,async({page})=>{
  const fixture=await setup(page,lang);const name=page.locator('[name=name]'),save=page.locator('[data-form=cost-center] [type=submit]');
  await name.fill('Workshop');fixture.error={status:503,code:'cost_center_authority_unavailable'};await save.click();
  await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(name).toHaveValue('Workshop');await expect(page.locator('main')).not.toContainText('PRIVATE SQL');
  await save.click();await expect(page.locator('[data-cc-id]')).toContainText('Workshop');
  expect(fixture.requests[0].headers['idempotency-key']).toBe(fixture.requests[1].headers['idempotency-key']);
  expect(fixture.requests[1].payload).toEqual({name:'Workshop',division_ref_id:'division'});
  await page.locator('[data-cc-action=edit]').click();await name.fill('Workshop II');await save.click();
  await expect(page.locator('[data-cc-id]')).toContainText('Workshop II');expect(fixture.requests[2].payload).toEqual({name:'Workshop II',expected_revision:1});
  fixture.error={status:409,code:'cost_center_revision_conflict'};await page.locator('[data-cc-action=deactivate]').click();
  await expect(page.locator('[role=alert]').first()).toBeVisible();await expect(page.locator('[data-cc-action=deactivate]')).toBeEnabled();
  await page.locator('[data-cc-action=deactivate]').click();await expect(page.locator('[data-cc-action=activate]')).toBeEnabled();
  expect(fixture.requests[3].headers['idempotency-key']).toBe(fixture.requests[4].headers['idempotency-key']);
  expect(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);
  await page.screenshot({path:test.info().outputPath('cost-centers.png'),fullPage:true});
 });
 test(`${lang}: structured name error attaches to the field and keeps the draft`,async({page})=>{
  const fixture=await setup(page,lang);await page.locator('[name=name]').fill('Kept draft');
  fixture.error={status:422,code:'validation_error',details:{issues:[{loc:['body','name'],type:'string_too_short',ctx:{min_length:1}}]}};
  await page.locator('[data-form=cost-center] [type=submit]').click();
  await expect(page.locator('[name=name]')).toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[name=name]')).toHaveValue('Kept draft');
  await expect(page.locator('main')).not.toContainText('PRIVATE SQL');
 });
 test(`${lang}: read permission, inactive division and bounded server search`,async({page})=>{
  let fixture=await setup(page,lang,true);await expect(page.locator('[data-form=cost-center]')).toHaveCount(0);
  await page.locator('[name=q]').fill('Work');await page.locator('[data-cc-search] button').click();
  await expect.poll(()=>fixture.queries.length).toBe(2);expect(fixture.queries[1]).toContain('division_id=division');expect(fixture.queries[1]).toContain('limit=25');expect(fixture.queries[1]).toContain('q=Work');expect(fixture.requests).toHaveLength(0);
  fixture=await setup(page,lang,false,true);await expect(page.locator('[data-form=cost-center]')).toHaveCount(0);
 });
}

test('Administration only exposes the catalog with capability and read permission',async({page})=>{
 await setup(page,'es',true);
 await page.route('**/v1/organization/divisions?*',route=>route.fulfill({json:{data:[{id:'division',code:'DIV01',name:'Division',status:'active',society_id:'soc',society_name:'Society'}],meta:{total:1,limit:25,offset:0}}}));
 async function mount(available,read){
  await page.evaluate(async({available,read})=>{
   const feature=await import('/features/organization.js');
   const data={tenant:{},session:{permissions:['admin.division.read',...(read?['costing.cost_center.read']:[])],capabilities:{cost_center_catalog:{available}}}};
   document.querySelector('main').innerHTML=feature.renderOrganizationPanel(data,'es');feature.bindOrganizationPanel(document.querySelector('main'),data,'es');
  },{available,read});
  await expect(page.locator('[data-org-id=division]')).toHaveCount(1);
 }
 await mount(false,true);await expect(page.locator('[data-org-action=cost-centers]')).toHaveCount(0);
 await mount(true,false);await expect(page.locator('[data-org-action=cost-centers]')).toHaveCount(0);
 await mount(true,true);await page.locator('[data-org-action=cost-centers]').click();
 await expect(page.locator('.cost-center-panel')).toBeVisible();await expect(page.locator('[data-form=cost-center]')).toHaveCount(0);
});
