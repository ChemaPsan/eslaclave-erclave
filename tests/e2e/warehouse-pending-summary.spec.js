const {test,expect}=require('@playwright/test');
const fs=require('fs'),path=require('path');
const {installLocalAuth,signInAsLocalAdmin}=require('./local-auth');
test.beforeEach(async({page})=>{
 await page.route('**/*',r=>['127.0.0.1','localhost'].includes(new URL(r.request().url()).hostname)?r.fallback():r.abort());
 await installLocalAuth(page);
 await page.route(/\/app\.js(?:\?.*)?$/,r=>r.fulfill({contentType:'application/javascript',body:fs.readFileSync(path.join(__dirname,'../../frontend/app.js'),'utf8')+'\nwindow.pendingAudit={state,navigateTo,render,loadOperationalHandoff};'}));
 await page.route('**/v1/**',r=>new URL(r.request().url()).port==='9099'||['GET','HEAD','OPTIONS'].includes(r.request().method())?r.fallback():r.fulfill({status:409,json:{error:{code:'invalid_state'}}}));
 await signInAsLocalAdmin(page);
 await expect.poll(()=>page.evaluate(()=>window.pendingAudit.state.adminApi.status)).toBe('ready');
 await page.evaluate(()=>{
  const a=window.pendingAudit,s=a.state;if(s.sessionApi.data.tenant.id!=='ten_739ee59d765d5e14818674800d')throw Error('Wrong tenant');
  s.inventoryApi={status:'ready',error:''};s.inventoryItems={status:'ready',error:''};s.inventoryMovements={status:'ready',error:''};
  s.finishedGoodsReceipts={status:'ready',orders:[],products:[],summaries:[],error:''};
  s.warehouseMaterialRequests={status:'ready',data:[],page:{offset:0,has_more:false},error:''};
  s.warehouseProductionRequests={status:'ready',data:[],page:{offset:0,has_more:false},error:''};
  s.operationalHandoffs=Object.fromEntries(['purchase','sales','transfer','materialReturn'].map(k=>[k,{status:'ready',data:[],offset:0,error:''}]));
  a.navigateTo({active:'almacenes',activeSubmodule:'movimientos',laborArea:''});
 });
});
test('Empty requests start collapsed and history remains visible; keyboard and navigation preserve intent',async({page})=>{
 const details=page.locator('.warehouse-pending'),summary=details.locator(':scope > summary');
 await expect(details).not.toHaveAttribute('open');
 await expect(summary).toContainText('Sin entradas ni salidas pendientes');
 await expect(page.locator('.warehouse-pending-body')).toBeHidden();
 await expect(page.locator('[data-movement-history]')).toBeInViewport();
 await summary.press('Enter');await expect(details).toHaveAttribute('open');
 await page.evaluate(()=>window.pendingAudit.render());await expect(details).toHaveAttribute('open');
 await summary.press('Space');await page.evaluate(()=>window.pendingAudit.render());await expect(details).not.toHaveAttribute('open');
 await summary.click();
 await page.evaluate(()=>{const a=window.pendingAudit;a.navigateTo({active:'almacenes',activeSubmodule:null,laborArea:''});a.navigateTo({active:'almacenes',activeSubmodule:'movimientos',laborArea:''});});
 await expect(details).not.toHaveAttribute('open');
});
test('All seven request sources raise a warning without expanding',async({page})=>{
 for(const kind of ['finished','production','parts','purchase','sales','transfer','materialReturn']){
  await page.evaluate(kind=>{
   const a=window.pendingAudit,s=a.state;
   s.finishedGoodsReceipts.orders=[];s.warehouseProductionRequests.data=[];s.warehouseMaterialRequests.data=[];
   for(const q of Object.values(s.operationalHandoffs))q.data=[];
   const row={id:'pending_uat',code:'DOC-PENDIENTE',order_code:'DOC-PENDIENTE',order_title:'Solicitud',order_id:'ord_uat',product_service_id:'prd_uat',quantity:1,unit:'H87',status:'reserved',lines:[]};
   if(kind==='finished')s.finishedGoodsReceipts.orders=[row];
   else if(kind==='production')s.warehouseProductionRequests.data=[row];
   else if(kind==='parts')s.warehouseMaterialRequests.data=[row];
   else s.operationalHandoffs[kind].data=[row];
   a.render();
  },kind);
  await expect(page.locator('[data-warehouse-pending-status]')).toContainText('Hay entradas o salidas pendientes');
  await expect(page.locator('.warehouse-pending')).not.toHaveAttribute('open');
 }
});
test('Loading, errors and later pages never claim no work; async refresh updates the collapsed summary',async({page})=>{
 for(const [status,error,offset,copy] of [['loading','',0,'Revisando'],['error','Consulta no disponible',0,'No se pudieron'],['ready','',25,'páginas anteriores']]){
  await page.evaluate(({status,error,offset})=>{const a=window.pendingAudit;a.state.operationalHandoffs.purchase={status,error,offset,data:[]};a.render();},{status,error,offset});
  await expect(page.locator('[data-warehouse-pending-status]')).toContainText(copy);
  await expect(page.locator('[data-warehouse-pending-status]')).not.toContainText('Sin entradas');
 }
 await page.route('**/v1/purchasing/warehouse-receipts?**',r=>r.fulfill({json:{data:[{id:'rec_uat',code:'REC-PENDIENTE',lines:[]}]}}));
 await page.evaluate(()=>window.pendingAudit.loadOperationalHandoff('purchase'));
 await expect(page.locator('[data-warehouse-pending-status]')).toContainText('Hay entradas');
 await expect(page.locator('.warehouse-pending')).not.toHaveAttribute('open');
 await page.route('**/v1/purchasing/warehouse-receipts?**',r=>r.fulfill({json:{data:[]}}));
 await page.evaluate(()=>window.pendingAudit.loadOperationalHandoff('purchase'));
 await expect(page.locator('[data-warehouse-pending-status]')).toContainText('Sin entradas');
 await page.evaluate(()=>{const a=window.pendingAudit;a.state.sessionApi.data.permissions=['inventory.movement.read'];a.state.finishedGoodsReceipts.status='idle';a.render();});
 await expect(page.locator('[data-warehouse-pending-status]')).toContainText('Sin entradas');
 await expect(page.locator('[data-handoff-action],[data-issue-warehouse-parts],[data-issue-warehouse-production]')).toHaveCount(0);
});
test('Summary remains readable in ES EN at actual narrow panel widths',async({page})=>{
 await page.setViewportSize({width:1600,height:1000});
 for(const lang of ['es','en'])for(const width of [1100,520,360]){
  await page.evaluate(({lang,width})=>{const a=window.pendingAudit;a.state.lang=lang;a.state.operationalHandoffs.purchase.data=[{id:'rec_uat',code:'REC-PENDIENTE',lines:[]}];a.render();document.querySelector('#modulePanel').style.width=width+'px';}, {lang,width});
  const summary=page.locator('.warehouse-pending > summary');
  const size=await summary.evaluate(n=>({width:n.clientWidth,scroll:n.scrollWidth}));expect(size.scroll).toBeLessThanOrEqual(size.width+1);expect(size.width).toBeGreaterThan(180);
  await expect(page.locator('[data-movement-history]')).toBeInViewport();
  await page.screenshot({path:test.info().outputPath(`pending-${lang}-${width}.png`)});
 }
});

test('Finished goods load failure can be retried after expanding without losing the open state',async({page})=>{
 await page.route('**/v1/production/finished-goods-candidates?**',r=>r.fulfill({json:{data:[]}}));
 await page.route('**/v1/inventory/finished-goods-receipts',r=>r.fulfill({json:{data:[]}}));
 await page.evaluate(()=>{const a=window.pendingAudit;a.state.finishedGoodsReceipts={status:'error',error:'No se pudo consultar la recepción',orders:[],products:[],summaries:[]};a.render();});
 await expect(page.locator('[data-warehouse-pending-status]')).toContainText('No se pudieron');
 await page.locator('.warehouse-pending > summary').click();
 await page.locator('[data-retry-finished-receipts]').click();
 await expect(page.locator('[data-warehouse-pending-status]')).toContainText('Sin entradas');
 await expect(page.locator('.warehouse-pending')).toHaveAttribute('open');
 await expect(page.locator('[data-retry-finished-receipts]')).toHaveCount(0);
});
