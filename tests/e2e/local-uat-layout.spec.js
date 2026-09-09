const {test,expect}=require('@playwright/test');
const fs=require('fs'),path=require('path');
const {installLocalAuth,signInAsLocalAdmin}=require('./local-auth');
test.beforeEach(async({page})=>{
 await page.route('**/*',route=>['127.0.0.1','localhost'].includes(new URL(route.request().url()).hostname)?route.fallback():route.abort());
 await installLocalAuth(page);
 await page.route(/\/app\.js(?:\?.*)?$/,route=>route.fulfill({contentType:'application/javascript',body:fs.readFileSync(path.join(__dirname,'../../frontend/app.js'),'utf8')+'\nwindow.uat={state,modules,mockDb,navigateTo,render,renderOrdersScreen,renderPurchasingSubmodulePanel,renderSalesQuoteCard,bindProductionPanelActions,enhanceEntitySelectors};'}));
 await page.route('**/v1/**',route=>new URL(route.request().url()).port==='9099'||['GET','HEAD','OPTIONS'].includes(route.request().method())?route.fallback():route.fulfill({status:409,json:{error:{code:'invalid_state'}}}));
 await signInAsLocalAdmin(page);await expect.poll(()=>page.evaluate(()=>window.uat.state.adminApi.status)).toBe('ready');
 await page.evaluate(()=>{
  const {state}=window.uat;if(state.sessionApi.data.tenant.id!=='ten_739ee59d765d5e14818674800d')throw Error('Wrong tenant');
  state.purchasingApi={...state.purchasingApi,status:'ready',suppliers:[{id:'sup_uat',code:'PROV-01',commercial_name:'Proveedor de cera y materiales',legal_name:'Proveedor SA',tax_id:'AAA010101AAA',tax_regime:'601',billing_email:'proveedor@example.com',fiscal_postal_code:'01234',fiscal_country:'MX',currency:'MXN',payment_terms:'cash',lead_time_days:0,status:'active'}],requisitions:[],orders:[],receipts:[],items:[{id:'itm_uat',code:'MAT-CERA',name:'Cera para vela aromática de larga duración',base_unit:'H87'}],warehouses:[],errors:{}};
  state.operationalHandoffs={service:{status:'ready',data:[],offset:0}};
 });
});
test('Suppliers open on the list; create and edit use the dialog and preserve failed input',async({page})=>{
 await page.evaluate(()=>window.uat.navigateTo({active:'compras',activeSubmodule:'proveedores',laborArea:''}));
 await expect(page.locator('#modulePanel')).toContainText('Proveedor de cera');
 await expect(page.locator('#purchasingSupplierForm')).toHaveCount(0);
 await page.locator('[data-open-supplier]').click();await expect(page.locator('#purchasingSupplierForm')).toBeVisible();
 await page.locator('.purchasing-supplier-dialog .modal-close').click();
 await page.locator('[data-edit-supplier="sup_uat"]').click();
 let payload;await page.route('**/v1/purchasing/suppliers/sup_uat',route=>{payload=route.request().postDataJSON();return route.fulfill({status:409,json:{error:{code:'supplier_conflict'}}});});
 await page.locator('#purchasingSupplierForm [name=commercial_name]').fill('Proveedor actualizado');
 await page.locator('#purchasingSupplierForm button[type=submit]').click();
 await expect(page.locator('#formErrors')).toBeVisible();
 expect(payload.commercial_name).toBe('Proveedor actualizado');expect(payload).not.toHaveProperty('code');
 await expect(page.locator('#purchasingSupplierForm [name=commercial_name]')).toHaveValue('Proveedor actualizado');
 await expect(page.locator('#purchasingSupplierForm button[type=submit]')).toBeEnabled();
});
test('Requisition search is readable at real form widths in ES EN',async({page})=>{
 await page.setViewportSize({width:1600,height:1000});
 for(const lang of ['es','en'])for(const width of [1100,780,520,320]){
  await page.evaluate(({lang,width})=>{const a=window.uat;a.state.lang=lang;a.state.active='compras';a.state.activeSubmodule='requisiciones';document.querySelector('#modulePanel').style.width=width+'px';a.renderPurchasingSubmodulePanel(a.modules.find(m=>m.id==='compras'));a.enhanceEntitySelectors();},{lang,width});
  const field=page.locator('[data-requisition-line] .purchasing-line-item');
  await field.locator('input[type=search]').fill('Cera');
  await expect(field.getByRole('button').filter({hasText:'MAT-CERA'})).toBeVisible();
  expect(await field.evaluate(n=>n.clientWidth)).toBeGreaterThan(170);
  const geometry=await page.locator('#purchasingRequisitionForm').evaluate(n=>({width:n.clientWidth,scroll:n.scrollWidth,offenders:[...n.querySelectorAll('*')].filter(c=>c.getBoundingClientRect().right>n.getBoundingClientRect().right+1).map(c=>({tag:c.tagName,cls:c.className,width:c.clientWidth,scroll:c.scrollWidth}))}));
  expect(geometry.scroll,JSON.stringify({lang,width,...geometry})).toBeLessThanOrEqual(geometry.width+1);
  const result=field.getByRole('button').filter({hasText:'MAT-CERA'});
  await result.scrollIntoViewIfNeeded();
  await page.screenshot({path:test.info().outputPath(`requisition-${lang}-${width}.png`)});
  await result.click();
  await expect(field.locator('select')).toHaveValue('itm_uat');
  await expect(page.locator('[data-requisition-line] [name=unit_code]')).toHaveValue('H87');
 }
});

test('New supplier saves the contractual payload and returns to the list',async({page})=>{
 let saved;
 await page.route('**/v1/purchasing/suppliers',route=>{
  if(route.request().method()==='POST'){
   saved={id:'sup_created',...route.request().postDataJSON()};
   expect(route.request().headers()['x-tenant-id']).toBe('ten_739ee59d765d5e14818674800d');
   expect(route.request().headers()['idempotency-key']).toBeTruthy();
   return route.fulfill({status:201,json:{data:saved}});
  }
  return route.fulfill({json:{data:saved?[saved]:[]}});
 });
 await page.evaluate(()=>window.uat.navigateTo({active:'compras',activeSubmodule:'proveedores',laborArea:''}));
 await page.locator('[data-open-supplier]').click();
 for(const [name,value] of Object.entries({code:'PROV-UAT',commercial_name:'Proveedor nuevo UAT',legal_name:'Proveedor SA',tax_id:'AAA010101AAA',billing_email:'proveedor@example.com',fiscal_postal_code:'01234'}))await page.locator(`#purchasingSupplierForm [name=${name}]`).fill(value);
 await page.locator('#purchasingSupplierForm button[type=submit]').click();
 await expect(page.locator('#modalBackdrop')).toBeHidden();
 await expect(page.locator('#modulePanel')).toContainText('Proveedor nuevo UAT');
 expect(saved).toMatchObject({code:'PROV-UAT',currency:'MXN',payment_terms:'cash',lead_time_days:0,tax_regime:'601'});
 await expect(page.locator('#purchasingSupplierForm')).toHaveCount(0);
 await page.evaluate(()=>{window.uat.state.sessionApi.data.permissions=['purchasing.supplier.read'];window.uat.render();});
 await expect(page.locator('[data-open-supplier], [data-edit-supplier]')).toHaveCount(0);
});

test('Local Owner has quote actions and their cards fit narrow containers in ES EN',async({page})=>{
 const permissions=await page.evaluate(()=>window.uat.state.sessionApi.data.permissions);
 for(const action of ['submit','approve','expire','cancel'])expect(permissions).toContain(`sales.quote.${action}`);
 for(const lang of ['es','en']){
  await page.evaluate(lang=>{const a=window.uat;a.state.lang=lang;const panel=document.querySelector('#modulePanel');panel.style.width='320px';panel.innerHTML=a.renderSalesQuoteCard({id:'quote_uat',code:'COT-UAT',title:'Cliente de prueba',status:'Borrador',fields:{lines:[],total:100,currency:'MXN'}});},lang);
  const card=page.locator('.sales-quote-card');
  expect(await card.evaluate(n=>n.scrollWidth<=n.clientWidth+1)).toBe(true);
  await expect(page.locator('[data-transition=submit]')).toBeVisible();
  await page.screenshot({path:test.info().outputPath(`quote-${lang}-320.png`)});
 }
});
test('Collapsing Production flow leaves control text in the main column',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 for(const lang of ['es','en'])for(const width of [1000,520]){
  await page.evaluate(({lang,width})=>{const a=window.uat;a.state.lang=lang;const panel=document.querySelector('#modulePanel');panel.style.width=width+'px';panel.innerHTML=a.renderOrdersScreen([]);},{lang,width});
  const rail=page.locator('.production-orders-layout > .flow-guide-card');
  for(const open of [true,false]){
   await rail.evaluate((n,open)=>n.open=open,open);
   const control=page.locator('.production-orders-layout > .section-card');
   expect(await control.evaluate(n=>n.clientWidth)).toBeGreaterThan(240);
   expect(await control.evaluate(n=>n.scrollWidth<=n.clientWidth+1)).toBe(true);
   await page.screenshot({path:test.info().outputPath(`orders-${lang}-${width}-${open}.png`)});
  }
 }
});
test('Quote permissions explain the next step and issue/approval invoke the correct APIs',async({page})=>{
 const render=async(status,permissions)=>page.evaluate(({status,permissions})=>{const a=window.uat;a.state.sessionApi.data.permissions=permissions;document.querySelector('#modulePanel').innerHTML=a.renderSalesQuoteCard({id:'quote_uat',code:'COT-UAT',title:'Cliente de prueba',status,fields:{lines:[],total:100,currency:'MXN'}});a.bindProductionPanelActions();},{status,permissions});
 await render('Borrador',['sales.quote.read']);await expect(page.locator('.sales-quote-next-step')).toContainText('Tu rol no tiene permiso');await expect(page.locator('[data-transition=submit]')).toHaveCount(0);
 for(const [status,action] of [['Borrador','submit'],['Cotizada','approve']]){
  let called=false;await page.route(`**/v1/sales/quotes/quote_uat/${action}`,route=>{called=true;expect(route.request().headers()['idempotency-key']).toBeTruthy();return route.fulfill({status:409,json:{error:{code:'invalid_quote_transition'}}});});
  await render(status,[`sales.quote.${action}`]);await page.locator(`[data-transition=${action}]`).click();await expect.poll(()=>called).toBe(true);
  await expect(page.locator('.sales-quote-card .chip')).toHaveText(status);
 }
});
test('Supplier dialog adapts independently of the underlying panel in both languages',async({page})=>{
 await page.setViewportSize({width:1280,height:900});
 for(const lang of ['es','en'])for(const width of [480,320]){
  await page.addStyleTag({content:`.modal-sheet {width:${width}px;max-width:100%;}`});
  await page.evaluate(lang=>{window.uat.state.lang=lang;window.uat.navigateTo({active:'compras',activeSubmodule:'proveedores',laborArea:''});},lang);
  await page.locator('[data-open-supplier]').press('Enter');
  expect(await page.locator('#purchasingSupplierForm').evaluate(n=>n.scrollWidth<=n.clientWidth+1)).toBe(true);
  await page.screenshot({path:test.info().outputPath(`supplier-${lang}-${width}.png`)});
  await page.locator('.purchasing-supplier-dialog .modal-close').click();
 }
});
