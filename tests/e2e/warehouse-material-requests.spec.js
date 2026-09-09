const {test,expect}=require("@playwright/test");
const fs=require("fs");
const path=require("path");
const {installLocalAuth,signInAsLocalAdmin}=require("./local-auth");
const TENANT="ten_739ee59d765d5e14818674800d";
let requests;
const partRequest=()=>({id:"mmr_browser",order_id:"mwo_browser",order_code:"MT-ALMACEN",order_title:"Reparacion de bomba",assigned_worker_id:"hrw_browser",assigned_worker_name:"Tecnico de mantenimiento",warehouse_id:"wh_browser",warehouse_name:"Refacciones",status:"reserved",pending_operation:null,lines:[{id:"line_a",item_code:"SEL-01",item_name:"Sello mecanico",quantity:2,unit_code:"PZA",line_status:"reserved"},{id:"line_b",item_code:"BAN-02",item_name:"Banda industrial",quantity:1,unit_code:"PZA",line_status:"reserved"}]});

test.beforeEach(async({page})=>{
  requests=[partRequest()];
  await page.route("**/*",route=>["127.0.0.1","localhost"].includes(new URL(route.request().url()).hostname)?route.fallback():route.abort());
  await installLocalAuth(page);
  await page.route(/\/app\.js(?:\?.*)?$/,route=>route.fulfill({contentType:"application/javascript",body:fs.readFileSync(path.join(__dirname,"../../frontend/app.js"),"utf8")+"\nwindow.warehouseAudit={state,navigateTo,render,openMaintenanceActionModal};"}));
  await page.route("**/v1/**",route=>new URL(route.request().url()).port==="9099"||["GET","HEAD","OPTIONS"].includes(route.request().method())?route.fallback():route.fulfill({status:409,contentType:"application/json",body:JSON.stringify({error:{code:"invalid_state"}})}));
  await page.route("**/v1/maintenance/warehouse-material-requests?**",route=>route.fulfill({json:{data:requests,page:{offset:0,limit:25,has_more:false}}}));
  await signInAsLocalAdmin(page);
  await expect.poll(()=>page.evaluate(()=>window.warehouseAudit.state.adminApi.status)).toBe("ready");
  await page.evaluate(()=>{
    const {state}=window.warehouseAudit;
    if(state.sessionApi.data.tenant.id!=="ten_739ee59d765d5e14818674800d")throw Error("Wrong tenant");
    state.inventoryApi={status:"ready",error:""};state.inventoryItems={status:"ready",error:""};state.inventoryMovements={status:"ready",error:""};
    state.finishedGoodsReceipts={status:"ready",orders:[],products:[],summaries:[],error:""};
    window.warehouseAudit.navigateTo({active:"almacenes",activeSubmodule:"movimientos",laborArea:""});
  });
  await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)")).toContainText("MT-ALMACEN");
 await page.locator('.warehouse-pending > summary').click();
});

test("Movimientos muestra la solicitud y confirma una sola salida por entrega",async({page})=>{
  await expect(page.getByRole("heading",{name:"Entradas de produccion terminada",exact:true})).toBeVisible();
  await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)")).toContainText("Sello mecanico");
  await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)")).toContainText("Banda industrial");
  let calls=0;
  await page.route("**/v1/maintenance/material-requests/mmr_browser/issue",async route=>{
    calls++;expect(route.request().headers()["x-tenant-id"]).toBe(TENANT);expect(route.request().headers()["idempotency-key"]).toBeTruthy();
    requests=[];await route.fulfill({json:{data:{...partRequest(),status:"issued"}}});
  });
  await page.locator("[data-issue-warehouse-parts]").click();
  await expect(page.locator("#warehousePartsIssueForm")).toContainText("entrega completa");
  await expect(page.locator("#warehousePartsIssueForm")).toContainText("Técnico asignado");
  await page.locator("#warehousePartsIssueForm button[type=submit]").click();
  await expect(page.locator("#warehousePartsIssueForm")).toHaveCount(0);
  await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)")).toContainText("No hay solicitudes");
  expect(calls).toBe(1);
});

test("una entrega parcial por fallo conserva la solicitud y permite reintentar",async({page})=>{
  await page.route("**/v1/maintenance/material-requests/mmr_browser/issue",route=>{
    requests=[{...partRequest(),status:"needs_reconciliation",pending_operation:"issue",lines:partRequest().lines.map((line,index)=>({...line,line_status:index===0?"issued":"reserved"}))}];
    return route.fulfill({json:{data:requests[0]}});
  });
  await page.locator("[data-issue-warehouse-parts]").click();
  await page.locator("#warehousePartsIssueForm button[type=submit]").click();
  await expect(page.locator("[data-issue-warehouse-parts]")).toHaveText("Reintentar entrega");
  await expect(page.locator("[data-reject-warehouse-parts]")).toHaveCount(0);
  await page.locator("[data-issue-warehouse-parts]").click();
  await expect(page.locator("#warehousePartsIssueForm")).toContainText("sin duplicarlas");
});

test("Almacen rechaza con motivo y libera la solicitud de su bandeja",async({page})=>{
  let reason;
  await page.route("**/v1/maintenance/material-requests/mmr_browser/reject",route=>{
    reason=route.request().postDataJSON().reason;requests=[];return route.fulfill({json:{data:{...partRequest(),status:"cancelled"}}});
  });
  await page.locator("[data-reject-warehouse-parts]").click();
  await page.locator("#warehousePartsIssueForm textarea").fill("Solicitud duplicada");
  await page.locator("#warehousePartsIssueForm button[type=submit]").click();
  await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)")).toContainText("No hay solicitudes");
  expect(reason).toBe("Solicitud duplicada");
});

test("solo lectura conserva cantidades sin acciones y sin abrir ordenes tecnicas",async({page})=>{
  await page.evaluate(()=>{
    const {state,render}=window.warehouseAudit;
    state.sessionApi.data.permissions=state.sessionApi.data.permissions.filter(p=>p!=="inventory.movement.create"&&!p.startsWith("maintenance."));render();
  });
  await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)")).toContainText("Sello mecanico");
  await expect(page.locator("[data-issue-warehouse-parts],[data-reject-warehouse-parts]")).toHaveCount(0);
  await page.evaluate(()=>{const a=window.warehouseAudit;a.state.sessionApi.data.active_modules=a.state.sessionApi.data.active_modules.filter(m=>m!=="maintenance");a.render();});
  await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)")).toHaveCount(0);
});

test("la bandeja y la confirmacion mantienen ES EN en contenedor estrecho",async({page})=>{
  await page.setViewportSize({width:1280,height:900});
  await page.addStyleTag({content:"#modulePanel {width: 520px; max-width: 100%;}"});
  for(const lang of ["es","en"]){
    await page.evaluate(lang=>{window.warehouseAudit.state.lang=lang;window.warehouseAudit.render();},lang);
    await expect(page.locator(".warehouse-parts-queue:not(.warehouse-production-queue) h3")).toHaveText(lang==="es"?"Solicitudes de refacciones":"Spare-parts requests");
    const bounds=await page.locator(".warehouse-parts-queue:not(.warehouse-production-queue)").evaluate(node=>({client:node.clientWidth,scroll:node.scrollWidth}));
    expect(bounds.scroll).toBeLessThanOrEqual(bounds.client+1);
    const action=await page.locator("[data-issue-warehouse-parts]").boundingBox();expect(action.height).toBeLessThan(100);
    await page.screenshot({path:test.info().outputPath(`warehouse-parts-${lang}.png`),fullPage:true});
    await page.locator("[data-issue-warehouse-parts]").click();
    await expect(page.locator("#warehousePartsIssueForm button[type=submit]")).toHaveText(lang==="es"?"Autorizar y entregar":"Authorize and issue");
    await page.locator("#warehousePartsIssueForm .modal-close").click();
  }
});
