const {test,expect}=require('@playwright/test');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
async function setup(page,lang,{mode='pending',permission=true,scope=true,converted=false,permissions=null}={}){
 const fixture={posts:[],statusReads:0,queueReads:0,eligible:false,created:converted,reconciled:false,error:{status:503,code:'authority_unavailable',details:{}},requestError:null};
 const request={id:'request-a',sales_order_id:'sales-a',sales_order_line_id:'line-a',product_service_id:'product-a',product_service_code:'PR-A',product_service_name:'Product A',quantity:2.5,original_quantity:'2.500000',unit:'H87',requested_due_date:'2026-10-10',status:'pending',organization_context:{division_ref_id:'div-a',society_ref_id:'soc-a',division_code:'DIV-A',division_name:'Division A',cost_currency:'MXN'}};
 const recipe={id:'recipe-a',product_service_id:'product-a',code:'REC-A',name:'Product A recipe',current_version_id:'version-a',versions:[{id:'version-a',status:'approved',base_unit:'H87',stages:[{id:'stage-a',name:'Stage A',status:'active'}]}]};
 await page.route('**/*',async route=>{const req=route.request(),url=new URL(req.url());if(url.origin!==origin)return route.abort();
  if(url.pathname==='/__cc12')return route.fulfill({contentType:'text/html',body:'<meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"><link rel="stylesheet" href="/features/production-fulfillment.css"><link rel="stylesheet" href="/features/production-order-context.css"><main style="max-width:100%;width:320px;padding:12px;box-sizing:border-box"></main><section id="planner" style="max-width:100%;width:320px"></section>'});
  if(url.pathname==='/v1/production/order-requests'){fixture.queueReads++;return route.fulfill({json:{data:[{...request,production_order_id:fixture.created?'production-a':null}],meta:{total:1,limit:25,offset:0}}});}
  if(url.pathname==='/v1/production/order-requests/request-a')return route.fulfill({json:{data:{...request,production_order_id:fixture.created?'production-a':null}}});
  if(url.pathname.endsWith('/recipes'))return route.fulfill({json:{data:[recipe],meta:{total:1,limit:20,offset:0}}});
  if(url.pathname==='/v1/hr/division-workers')return route.fulfill({json:{data:[{id:'worker-a',full_name:'Worker A'}],meta:{total:1}}});
  if(url.pathname.endsWith('/production-status')){fixture.statusReads++;return route.fulfill({json:{data:{order_line_id:'line-a',request_id:'request-a',production_order_id:fixture.created?'production-a':null,production_order_status:fixture.created?'completed':null,organization_context:request.organization_context,quantity:'2.5',unit:'H87',reconciliation_status:fixture.reconciled?'completed':null,warehouses:fixture.created?[{warehouse_id:'warehouse-a',warehouse_code:'WH-A',warehouse_name:'Receipt warehouse',inventory_item_id:'item-a',received_quantity:fixture.eligible?'2.5':'1',unit:'H87',eligible_for_reconciliation:fixture.eligible}]:[]}}});}
  if(req.method()==='POST'){const entry={path:url.pathname,payload:req.postDataJSON(),key:req.headers()['idempotency-key']};fixture.posts.push(entry);
   if(url.pathname.endsWith('/resource-validations'))return route.fulfill({json:{data:{can_release:true,cost_currency:'MXN',original_planned_cost:'100.000000',rows:[]}}});
   const error=fixture.error;if(error)return route.fulfill({status:error.status,json:{error:{code:error.code,message:'PRIVATE SQL',details:error.details||{}}}});
   if(url.pathname.endsWith('/production-reconciliations'))fixture.reconciled=true;if(url.pathname.endsWith('/orders'))fixture.created=true;
   return route.fulfill({json:{data:{id:url.pathname.endsWith('/orders')?'production-a':'sales-a',code:'SAVED'}}});
  }
  return route.continue();
 });
 await page.goto(origin+'/__cc12');await page.evaluate(async({origin,lang,mode,permission,scope,permissions})=>{
  window.ERCLAVE_CONFIG={localSalesApiBaseUrl:origin,localProductionApiBaseUrl:origin,localHrApiBaseUrl:origin};localStorage.setItem('erclave-lang',lang);(await import('/features/form-feedback.js')).installFormFeedback({getLanguage:()=>lang});
  const session={permissions:permissions||(permission?['sales.order.fulfill','sales.order.read','production.order.read','production.order.release']:['sales.order.read']),scope:{version:2,divisions:scope?[{id:'div-a',code:'DIV-A',name:'Division A',society_id:'soc-a'}]:[],societies:[{id:'soc-a',name:'Society A',base_currency:'MXN'}]}};
  window.saved=[];window.openRequest=async id=>{const sourceRequest=await(await import('/api/production.js')).getProductionOrderRequest(id);return(await import('/features/production-order-context.js')).mountProductionOrderForm(document.querySelector('#planner'),session,{lang,today:'2026-10-08',sourceRequest,onSaved:result=>window.saved.push(result)});};
  if(mode==='queue'){(await import('/features/production-request-queue.js')).mountProductionRequestQueue(document.querySelector('main'),session,{lang,onOpen:window.openRequest});return;}
  const order={id:'sales-a',fields:{divisionRefId:'div-a',societyRefId:'soc-a',currency:'USD',lines:[{id:'line-a',productServiceId:'product-a',productServiceName:'Product A',productServiceType:'product',quantity:2.5,deliveredQuantity:0,unit:'H87',fulfillmentMode:mode,productionRequestId:mode==='production'?'request-a':null}]}};
  (await import('/features/sales-production-fulfillment.js')).mountSalesProductionFulfillment(document.querySelector('main'),order,session,{lang,onOpenRequest:window.openRequest,onSaved:result=>window.saved.push(result)});
 },{origin,lang,mode,permission,scope,permissions});return fixture;
}
for(const lang of ['es','en']){
 test(lang+': manufacturing requires explicit exchange rate, rejected capture and stable retry',async({page})=>{
  await page.setViewportSize({width:320,height:900});const state=await setup(page,lang);const form=page.locator('[data-form=sales-production-request]');
  await form.locator('[type=submit]').click();expect(state.posts).toHaveLength(0);await form.locator('[name=cost_exchange_rate]').fill('0.051234567891');state.error={status:422,code:'operational_exchange_rate_invalid',details:{issues:[{loc:['body','cost_exchange_rate'],type:'greater_than',msg:'PRIVATE SQL',ctx:{gt:0}}]}};
  await form.locator('[type=submit]').click();await expect.poll(()=>state.posts.length).toBe(1);await expect(form.locator('[name=cost_exchange_rate]')).toHaveAttribute('aria-invalid','true');await expect(form.locator('[name=cost_exchange_rate]')).toHaveValue('0.051234567891');
  expect(state.posts[0].payload).toEqual({lines:[{order_line_id:'line-a',mode:'production',allocations:[]}],cost_exchange_rate:'0.051234567891'});
  state.error=null;await form.locator('[type=submit]').click();await expect.poll(()=>state.posts.length).toBe(2);expect(state.posts[1].key).toBe(state.posts[0].key);await expect.poll(()=>page.evaluate(()=>window.saved.length)).toBe(1);await expect(form).not.toContainText('PRIVATE SQL');expect(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);
 });
 test(lang+': production completion without sufficient Inventory receipt cannot reconcile; receipt retry is idempotent',async({page})=>{
  const state=await setup(page,lang,{mode:'production',converted:true});const form=page.locator('[data-form=sales-production-reconciliation]');await expect(form.locator('[name=warehouse_id] option')).toHaveCount(2);await expect(form.locator('[name=warehouse_id] option[value=warehouse-a]')).toHaveJSProperty('disabled',true);await form.locator('[name=warehouse_id]').focus();await form.locator('[name=warehouse_id]').press('ArrowDown');await expect(form.locator('[name=warehouse_id]')).toHaveValue('');expect(await form.locator('[name=warehouse_id]').evaluate(n=>n.validity.valueMissing)).toBe(true);await form.evaluate(n=>n.requestSubmit());await expect(form.locator('[type=submit]')).toBeDisabled();expect(state.posts).toHaveLength(0);
  state.eligible=true;await form.locator('[data-refresh]').click();await expect(form.locator('[name=warehouse_id] option[value=warehouse-a]')).toHaveJSProperty('disabled',false);await form.locator('[name=warehouse_id]').selectOption('warehouse-a');state.error={status:403,code:'permission_denied'};await form.locator('[type=submit]').click();await expect.poll(()=>state.posts.length).toBe(1);await expect(form.locator('[name=warehouse_id]')).toHaveValue('warehouse-a');expect(state.posts[0].payload).toEqual({order_line_id:'line-a',warehouse_id:'warehouse-a'});expect(await page.evaluate(()=>window.saved.length)).toBe(0);
  state.error=null;await form.locator('[type=submit]').click();await expect.poll(()=>state.posts.length).toBe(2);expect(state.posts[1].key).toBe(state.posts[0].key);await form.locator('[data-refresh]').click();await expect(form.locator('[type=submit]')).toBeDisabled();await expect(form).toContainText(lang==='en'?'Manufacturing reconciled':'Fabricación conciliada');
 });
 test(lang+': Sales request plans a production order with immutable origin and stable uncertain retry',async({page})=>{
  const state=await setup(page,lang,{mode:'production'});await page.locator('[data-plan]').click();const form=page.locator('[data-form=production-order-context]');await expect(form.locator('[name=division_ref_id]')).toHaveAttribute('readonly','');await expect(form.locator('[name=quantity]')).toHaveValue('2.500000');await expect(form.locator('[name=quantity]')).toHaveAttribute('readonly','');await expect(form.locator('[data-source-product]')).toContainText('PR-A');await expect(form.locator('[data-division-lookup] [data-choice]')).toHaveCount(0);
  await form.locator('[data-recipe-lookup] [data-choice="0"]').click();await form.locator('[data-worker-lookup] [data-choice="0"]').click();await form.locator('[data-stage-lookups] [data-choice="0"]').click();await form.locator('[type=submit]').click();await expect.poll(()=>state.posts.filter(x=>x.path.endsWith('/orders')).length).toBe(1);
  const first=state.posts.find(x=>x.path.endsWith('/orders'));expect(first.payload).toMatchObject({division_ref_id:'div-a',quantity:'2.500000',unit:'H87',recipe_version_id:'version-a'});expect(first.payload).not.toHaveProperty('source_type');expect(first.payload).not.toHaveProperty('source_id');
  state.error=null;await form.locator('[type=submit]').click();await expect.poll(()=>state.posts.filter(x=>x.path.endsWith('/orders')).length).toBe(2);expect(state.posts.filter(x=>x.path.endsWith('/orders'))[1].key).toBe(first.key);expect(state.posts.filter(x=>x.path.endsWith('/resource-validations'))).toHaveLength(1);await expect.poll(()=>page.evaluate(()=>window.saved.length)).toBe(1);
 });
 test(lang+': request queue opens only unconverted authorized origins; missing scope blocks conversion',async({page})=>{
  await setup(page,lang,{mode:'queue',converted:true});await expect(page.locator('[data-requests]')).toContainText('production-a');await expect(page.locator('[data-open-request]')).toHaveCount(0);
  await setup(page,lang,{mode:'queue',scope:false});await page.locator('[data-open-request]').click();await expect(page.locator('#planner [type=submit]')).toBeDisabled();
  await setup(page,lang,{permission:false});await expect(page.locator('[data-form=sales-production-request]')).toHaveCount(0);
 });
 test(lang+': read boundaries do not send forbidden queue or manufacturing status requests',async({page})=>{
  let state=await setup(page,lang,{mode:'queue',permissions:['production.order.release']});await expect(page.locator('[data-production-request-queue]')).toHaveCount(0);expect(state.queueReads).toBe(0);expect(state.posts).toHaveLength(0);
  state=await setup(page,lang,{mode:'production',permissions:['sales.order.read']});await expect(page.locator('[data-sales-production]')).toHaveCount(0);expect(state.statusReads).toBe(0);expect(state.posts).toHaveLength(0);
 });

}
