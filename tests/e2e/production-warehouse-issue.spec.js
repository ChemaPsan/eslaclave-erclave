const {test,expect}=require("@playwright/test");
const fs=require("fs");const path=require("path");
const {installLocalAuth,signInAsLocalAdmin}=require("./local-auth");
let requests;
const request=()=>({id:"ord_warehouse_browser",order_code:"OP-MATERIALES",responsible_name:"Responsable de producción",status:"reserved",created_at:"2026-09-08T05:00:00Z",lines:[{id:"material1",item_code:"MP-01",item_name:"Materia prima para producto o servicio",quantity:2,unit_code:"H87",issued:false,allocations:[{warehouse_name:"Almacén de materias primas",quantity:2}]}]});
test.beforeEach(async({page})=>{
  requests=[request()];
  await page.route("**/*",route=>["127.0.0.1","localhost"].includes(new URL(route.request().url()).hostname)?route.fallback():route.abort());
  await installLocalAuth(page);
  await page.route(/\/app\.js(?:\?.*)?$/,route=>route.fulfill({contentType:"application/javascript",body:fs.readFileSync(path.join(__dirname,"../../frontend/app.js"),"utf8")+"\nwindow.issueAudit={state,navigateTo,render};"}));
  await page.route("**/v1/**",route=>new URL(route.request().url()).port==="9099"||["GET","HEAD","OPTIONS"].includes(route.request().method())?route.fallback():route.fulfill({status:409,json:{error:{code:"invalid_state"}}}));
  await page.route("**/v1/production/warehouse-material-requests?**",route=>route.fulfill({json:{data:requests,page:{limit:25,offset:0,has_more:false}}}));
  await signInAsLocalAdmin(page);
  await expect.poll(()=>page.evaluate(()=>window.issueAudit.state.adminApi.status)).toBe("ready");
  await page.evaluate(()=>{
    const {state,navigateTo}=window.issueAudit;
    if(state.sessionApi.data.tenant.id!=="ten_739ee59d765d5e14818674800d")throw Error("Wrong tenant");
    state.inventoryApi={status:"ready",error:""};state.inventoryItems={status:"ready",error:""};state.inventoryMovements={status:"ready",error:""};
    state.finishedGoodsReceipts={status:"ready",orders:[],products:[],summaries:[],error:""};
    state.warehouseMaterialRequests={status:"ready",data:[],page:{offset:0,has_more:false},error:""};
    navigateTo({active:"almacenes",activeSubmodule:"movimientos",laborArea:""});
  });
  await expect(page.locator(".warehouse-production-queue")).toContainText("OP-MATERIALES");
 await page.locator('.warehouse-pending > summary').click();
});

test("Almacen confirma materiales sin iniciar la orden y permite reintentar fallos",async({page})=>{
  let calls=0;
  await page.route("**/v1/production/orders/ord_warehouse_browser/issue-materials",route=>{
    calls++;expect(route.request().headers()["idempotency-key"]).toBeTruthy();
    expect(route.request().headers()["x-tenant-id"]).toBe("ten_739ee59d765d5e14818674800d");
    const result={...request(),status:calls===1?"needs_reconciliation":"issued"};
    requests=calls===1?[result]:[];return route.fulfill({json:{data:result}});
  });
  for(let n=0;n<2;n++){
    await page.locator("[data-issue-warehouse-production]").click();
    await expect(page.locator("#warehouseProductionIssueForm")).toContainText("La orden podrá iniciar después de esta salida");
    await expect(page.locator("#warehouseProductionIssueForm")).toContainText("Almacén de materias primas");
    await page.locator("#warehouseProductionIssueForm button[type=submit]").click();
    await expect(page.locator("#warehouseProductionIssueForm")).toHaveCount(0);
    if(n===0)await expect(page.locator("[data-issue-warehouse-production]")).toHaveText("Reintentar entrega");
  }
  await expect(page.locator(".warehouse-production-queue")).toContainText("No hay solicitudes");
  expect(calls).toBe(2);
});

test("Almacen de solo lectura ve solicitudes sin permisos de Produccion",async({page})=>{
  await page.evaluate(()=>{const {state,render}=window.issueAudit;state.sessionApi.data.permissions=state.sessionApi.data.permissions.filter(p=>!p.startsWith("production.")&&p!=="inventory.movement.create");render();});
  await expect(page.locator(".warehouse-production-queue")).toContainText("MP-01");
  await expect(page.locator("[data-issue-warehouse-production]")).toHaveCount(0);
  await page.evaluate(()=>{const {state,render}=window.issueAudit;state.sessionApi.data.active_modules=state.sessionApi.data.active_modules.filter(m=>m!=="production");render();});
  await expect(page.locator(".warehouse-production-queue")).toHaveCount(0);
});

test("materiales en ES EN con contenedor estrecho y confirmacion por teclado",async({page})=>{
  await page.setViewportSize({width:1280,height:900});
  await page.addStyleTag({content:"#modulePanel {width:520px;max-width:100%;} #modalContent {width:520px;max-width:100%;}"});
  for(const lang of ["es","en"]){
    await page.evaluate(lang=>{window.issueAudit.state.lang=lang;window.issueAudit.render();},lang);
    await expect(page.locator(".warehouse-production-queue h3")).toHaveText(lang==="es"?"Solicitudes de materiales para producción":"Production material requests");
    const bounds=await page.locator(".warehouse-production-queue").evaluate(n=>({client:n.clientWidth,scroll:n.scrollWidth}));
    expect(bounds.scroll).toBeLessThanOrEqual(bounds.client+1);
    await page.locator("[data-issue-warehouse-production]").press("Enter");
    await expect(page.locator("#warehouseProductionIssueForm")).toBeVisible();
    const modalBounds=await page.locator("#warehouseProductionIssueForm").evaluate(n=>({client:n.clientWidth,scroll:n.scrollWidth}));
    expect(modalBounds.scroll).toBeLessThanOrEqual(modalBounds.client+1);
    await page.screenshot({path:test.info().outputPath(`production-materials-${lang}.png`),fullPage:true});
    await page.locator("#warehouseProductionIssueForm .modal-close").click();
  }
});
