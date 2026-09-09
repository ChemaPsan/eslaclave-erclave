const {test,expect}=require('@playwright/test');
const fs=require('fs'),path=require('path');
const {installLocalAuth,signInAsLocalAdmin}=require('./local-auth');
const tenant='ten_739ee59d765d5e14818674800d';
const rows={
 purchase:{id:'receipt_browser',code:'REC-ALMACEN',status:'pending_confirmation',lines:[{description:'Material solicitado',quantity:2,unit_code:'H87',warehouse_ref_id:'wh_browser'}]},
 sales:{id:'delivery_browser',code:'ENT-ALMACEN',order_code:'PED-01',customer_name:'Cliente de prueba',lines:[{description:'Producto para entregar',quantity:2,unit_code:'H87',allocations:[{warehouse_id:'wh_browser',quantity:2}]}]},
 transfer:{id:'transfer_browser',code:'TRA-ALMACEN',status:'in_transit',item_code:'MP-01',item_name:'Materia prima',unit:'H87',origin_name:'Almacén origen',destination_name:'Almacén destino',origin_warehouse_id:'wh_origin',destination_warehouse_id:'wh_destination',quantity:5,received_quantity:1,returned_quantity:0},
 materialReturn:{id:'return_browser',source_code:'OP-SOBRANTE',status:'pending',item_code:'MP-02',item_name:'Sobrante de producción',unit:'H87',quantity:2}
};
test.beforeEach(async({page})=>{
 await page.route('**/*',route=>['localhost','127.0.0.1'].includes(new URL(route.request().url()).hostname)?route.fallback():route.abort());
 await installLocalAuth(page);
 await page.route(/\/app\.js(?:\?.*)?$/,route=>route.fulfill({contentType:'application/javascript',body:fs.readFileSync(path.join(__dirname,'../../frontend/app.js'),'utf8')+'\nwindow.handoffAudit={state,navigateTo,render};'}));
 await page.route('**/v1/**',route=>new URL(route.request().url()).port==='9099'||['GET','HEAD','OPTIONS'].includes(route.request().method())?route.fallback():route.fulfill({status:409,json:{error:{code:'invalid_state'}}}));
 for(const routePath of ['purchasing/warehouse-receipts','sales/warehouse-deliveries','inventory/transfers','inventory/material-returns'])await page.route(`**/v1/${routePath}?**`,route=>route.fulfill({json:{data:[]}}));
 await signInAsLocalAdmin(page);
 await expect.poll(()=>page.evaluate(()=>window.handoffAudit.state.adminApi.status)).toBe('ready');
 await page.evaluate(({rows,tenant})=>{
  const {state,navigateTo}=window.handoffAudit;if(state.sessionApi.data.tenant.id!==tenant)throw Error('Wrong tenant');
  state.inventoryApi={status:'ready',error:''};state.inventoryItems={status:'ready',error:''};state.inventoryMovements={status:'ready',error:''};
  state.finishedGoodsReceipts={status:'ready',orders:[],products:[],summaries:[],error:''};
  state.warehouseMaterialRequests={status:'ready',data:[],page:{offset:0,has_more:false},error:''};
  state.warehouseProductionRequests={status:'ready',data:[],page:{offset:0,has_more:false},error:''};
  state.operationalHandoffs=Object.fromEntries(Object.entries(rows).map(([kind,row])=>[kind,{status:'ready',data:[row],offset:0,error:''}]));
  navigateTo({active:'almacenes',activeSubmodule:'movimientos',laborArea:''});
 },{rows,tenant});
 await expect(page.locator('[data-handoff-kind="purchase"]')).toContainText('REC-ALMACEN');
 await page.locator('.warehouse-pending > summary').click();
});
test('Warehouse confirms purchases and dispatches sales with tenant and idempotency',async({page})=>{
 for(const [kind,url] of [['purchase','purchasing/receipts/receipt_browser/reconcile'],['sales','sales/deliveries/delivery_browser/confirm']]){
  let received=false;await page.route(`**/v1/${url}`,route=>{expect(route.request().headers()['x-tenant-id']).toBe(tenant);expect(route.request().headers()['idempotency-key']).toBeTruthy();received=true;return route.fulfill({json:{data:{status:'completed'}}});});
  await page.locator(`[data-kind="${kind}"][data-handoff-action="receive"]`).click();
  await page.locator('.operational-handoff-dialog button[type=submit]').click();
  await expect(page.locator('.operational-handoff-dialog')).toHaveCount(0);expect(received).toBe(true);
 }
});
test('Transfer receipt sends destination and partial quantity',async({page})=>{
 let body;await page.route('**/v1/inventory/transfers/transfer_browser/receive',route=>{body=route.request().postDataJSON();return route.fulfill({json:{data:{status:'partially_received'}}});});
 await page.locator('[data-kind="transfer"][data-handoff-action="receive"]').click();
 await page.locator('.operational-handoff-dialog [name=quantity]').fill('2');
 await page.locator('.operational-handoff-dialog [name=reason]').fill('Recepción física parcial');
 await page.locator('.operational-handoff-dialog button[type=submit]').click();
 await expect(page.locator('.operational-handoff-dialog')).toHaveCount(0);
 expect(body).toMatchObject({warehouse_id:'wh_destination',quantity:2});
});
test('Read-only Warehouse sees work without confirmation buttons',async({page})=>{
 await page.evaluate(()=>{const {state,render}=window.handoffAudit;state.sessionApi.data.permissions=state.sessionApi.data.permissions.filter(p=>p!=='inventory.movement.create');render();});
 await expect(page.locator('[data-handoff-kind="purchase"]')).toContainText('REC-ALMACEN');
 await expect(page.locator('[data-handoff-action]')).toHaveCount(0);
});
test('ES EN handoffs and keyboard dialogs fit actual narrow containers',async({page})=>{
 await page.setViewportSize({width:1280,height:900});
 await page.addStyleTag({content:'#modulePanel {width:520px;max-width:100%;} #modalContent {width:520px;max-width:100%;}'});
 for(const lang of ['es','en']){
  await page.evaluate(lang=>{window.handoffAudit.state.lang=lang;window.handoffAudit.render();},lang);
  for(const kind of ['purchase','sales','transfer','materialReturn']){
   const queue=page.locator(`[data-handoff-kind="${kind}"]`);
   expect(await queue.evaluate(n=>n.scrollWidth<=n.clientWidth+1)).toBe(true);
   await queue.locator('[data-handoff-action="receive"]').press('Enter');
   const form=page.locator('.operational-handoff-dialog');await expect(form).toBeVisible();
   expect(await form.evaluate(n=>n.scrollWidth<=n.clientWidth+1)).toBe(true);
   await page.screenshot({path:test.info().outputPath(`handoff-${kind}-${lang}.png`),fullPage:true});
   await form.locator('.modal-close').click();
  }
 }
});
test('Blocked transitions show actionable localized feedback and retain the command',async({page})=>{
 await page.route('**/v1/purchasing/receipts/receipt_browser/reconcile',route=>route.fulfill({status:409,json:{error:{code:'purchase_warehouse_receipt_required',message:'DO NOT DISPLAY RAW ERROR'}}}));
 await page.locator('[data-kind="purchase"][data-handoff-action="receive"]').click();
 await page.locator('.operational-handoff-dialog button[type=submit]').click();
 await expect(page.locator('#formErrors')).toContainText('Almacén');
 await expect(page.locator('#formErrors')).not.toContainText('DO NOT DISPLAY');
 await expect(page.locator('.operational-handoff-dialog button[type=submit]')).toBeEnabled();
});
test('Requester accepts purchased services from Purchasing',async({page})=>{
 await page.evaluate(()=>{
  const {state,navigateTo}=window.handoffAudit;
  state.purchasingApi={...state.purchasingApi,status:'ready',suppliers:[],orders:[],receipts:[],requisitions:[],items:[],warehouses:[],errors:{}};
  state.operationalHandoffs.service={status:'ready',offset:0,data:[{id:'service_browser',code:'REC-SERVICIO',lines:[{description:'Servicio solicitado',quantity:1,unit_code:'E48'}]}]};
  navigateTo({active:'compras',activeSubmodule:'recepciones',laborArea:''});
 });
 let accepted=false;await page.route('**/v1/purchasing/receipts/service_browser/accept-services',route=>{accepted=true;return route.fulfill({json:{data:{status:'completed'}}});});
 await page.route('**/v1/purchasing/service-acceptances?**',route=>route.fulfill({json:{data:[]}}));
 await page.locator('[data-kind="service"][data-handoff-action="receive"]').click();
 await expect(page.locator('.operational-handoff-dialog')).toContainText('Servicio solicitado');
 await page.locator('.operational-handoff-dialog button[type=submit]').click();
 await expect(page.locator('.operational-handoff-dialog')).toHaveCount(0);expect(accepted).toBe(true);
});
test('Warehouse cancels a pending return with a reason',async({page})=>{
 let reason;await page.route('**/v1/inventory/material-returns/return_browser/cancel',route=>{reason=route.request().postDataJSON().reason;return route.fulfill({json:{data:{status:'cancelled'}}});});
 await page.locator('[data-kind="materialReturn"][data-handoff-action="cancel"]').click();
 await page.locator('.operational-handoff-dialog [name=reason]').fill('El sobrante se utilizará');
 await page.locator('.operational-handoff-dialog button[type=submit]').click();
 await expect(page.locator('.operational-handoff-dialog')).toHaveCount(0);expect(reason).toBe('El sobrante se utilizará');
});
