const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");
const { installLocalAuth, signInAsLocalAdmin } = require("./local-auth");

const TENANT = "ten_739ee59d765d5e14818674800d";
// Test-only access to real view functions. No hook is shipped with the application.
const hook = `
window.frontendAudit = {
  state, mockDb, modules, closeModal, renderSalesServiceOrderModal, changeOrderStatus, advanceOrderStage, openServiceEvidenceHistory,
  openProductServiceModal, renderProductsServicesCatalogScreen, openWarehouseModal, openInventoryItemModal,
  openInventoryMovementModal, openLaborAreaModal, openLaborRoleModal,
  openWorkerModal, openMachineModal, openPurchasingCancellationModal,
  renderPurchasingSubmodulePanel, enhanceEntitySelectors, renderMaintenanceSubmodulePanel,
  loadProductionApiData, loadHrApiData, loadPurchasingApiData,
  openMaintenanceActionModal, renderRecipeList, applyProductionActionPermissions, openRecipeModal
};`;

test.beforeEach(async ({ page }) => {
  await page.route("**/*", route => {
    const url=new URL(route.request().url());
    if (!["127.0.0.1","localhost"].includes(url.hostname)) return route.abort();
    return route.fallback();
  });
  await installLocalAuth(page);
  await page.route(/\/app\.js(?:\?.*)?$/, route => route.fulfill({
    contentType: "application/javascript",
    body: fs.readFileSync(path.join(__dirname, "../../frontend/app.js"), "utf8") + hook
  }));
  // Fail closed: mutations not explicitly fulfilled by a test cannot reach a service.
  await page.route("**/v1/**", async route => {
    if (new URL(route.request().url()).port === "9099") return route.fallback();
    if (["GET", "HEAD", "OPTIONS"].includes(route.request().method())) return route.fallback();
    expect(route.request().headers()["x-tenant-id"]).toBe(TENANT);
    await route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({error:{code:"invalid_state",message:"internal diagnostic must stay hidden"}}) });
  });
  await signInAsLocalAdmin(page);
  await expect.poll(() => page.evaluate(() => window.frontendAudit.state.adminApi.status)).toBe("ready");
  await page.evaluate(() => {
    const {state,mockDb}=window.frontendAudit;
    if(state.sessionApi.data.tenant.id!=="ten_739ee59d765d5e14818674800d")throw new Error("Wrong Local tenant");
    for(const name of ["productionApi","inventoryApi","inventoryItems","hrApi","purchasingApi","maintenanceApi","salesApi"])state[name]={...state[name],status:"ready"};
    const warehouse={id:"wh_audit",code:"ALM-AUDIT",moduleId:"almacenes",submoduleId:"almacenes",recordType:"warehouse",title:"Almacen prueba",status:"Activo",owner:"Operacion",fields:{type:"rawMaterials",businessCenter:"Operacion",location:"Local",policy:"standard"}};
    const item={id:"itm_audit",code:"MAT-AUDIT",moduleId:"almacenes",submoduleId:"articulos",recordType:"inventoryItem",title:"Material prueba",status:"Activo",fields:{type:"rawMaterial",unit:"H87",policy:"lot",defaultUnitCost:0}};
    mockDb.saveModuleRecords("almacenes",[warehouse,item,{...warehouse,id:"wh_other",code:"OTRO"}]);
    mockDb.saveProductsServices([{id:"prs_audit",sku:"SER-AUDIT",name:"Servicio prueba",kind:"Servicio",unit:"E48",category:"Servicio",center:"Operacion",owner:"Operacion",description:"Prueba",status:"Activo",inventoryItemId:null}]);
    mockDb.saveLaborAreas([{id:"area_audit",code:"AREA",name:"Area prueba",status:"Activo"}]);
    mockDb.saveLaborRoles([{id:"pos_audit",areaId:"area_audit",area:"Area prueba",position:"Tecnico",name:"Tecnico",quantity:1,minutesPerResource:480,hourlyCost:0,status:"Activo"}]);
    state.hrApi.workers=[{id:"wrk_audit",employee_number:"EMP-AUDIT",first_names:"Persona",first_last_name:"Prueba",full_name:"Persona Prueba",curp:"AAAA000101HDFRRN09",rfc:"AAAA000101ABC",nss:"00000000000",hire_date:"2025-01-01",birth_date:"1990-01-01",labor_position_id:"pos_audit",status:"active"}];
    state.purchasingApi={...state.purchasingApi,suppliers:[],orders:[],receipts:[],requisitions:[{id:"req_audit",code:"REQ-AUDIT",required_date:"2026-09-07",priority:"normal",status:"draft",lines:[]}],items:[{id:"itm_audit",code:"MAT-AUDIT",name:"Material prueba",base_unit:"H87"}],warehouses:[]};
  });
});


async function orderFixture(page,lang,isService=true,started=false){
  await page.evaluate(({lang,isService,started})=>{
    const a=window.frontendAudit;a.state.lang=lang;
    a.mockDb.saveOrders([{id:'order_evidence_ui',code:'OP-EVIDENCE',recipeId:'recipe_ui',productServiceId:'prs_audit',isService,serviceEvidence:started?[{phase:'start',description:'Received in good condition',created_at:'2026-09-13T12:00:00Z',files:[]}]:[],status:started?'En produccion':'Liberada',recipeName:'Service test',quantity:1,unit:'E48',areas:[{id:'stage_evidence_ui',area:'Production',status:'Pendiente',progress:0,weightPercent:100}]}]);
  },{lang,isService,started});
}
for(const lang of ['es','en']){
  test(`${lang}: service start requires written evidence before waiting for resources`,async({page})=>{
    await orderFixture(page,lang);
    await page.evaluate(()=>window.frontendAudit.changeOrderStatus('order_evidence_ui','En espera de recursos'));
    const form=page.locator('#productionServiceEvidenceForm');await expect(form).toBeVisible();
    let evidenceCalls=0,statusCalls=0;
    await page.route('**/service-evidence/start',async route=>{
      evidenceCalls++;const body=route.request().postDataJSON();expect(body.description).toBe('Received device with scratches');
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({data:[{phase:'start',description:body.description,created_at:'2026-09-13T12:00:00Z',files:[]}]})});
    });
    await page.route('**/orders/order_evidence_ui/status',async route=>{statusCalls++;await route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:{code:'invalid_order_transition'}})});});
    await form.locator('[type=submit]').click();expect(evidenceCalls).toBe(0);expect(statusCalls).toBe(0);
    await form.locator('textarea').fill('Received device with scratches');await form.locator('[type=submit]').click();
    await expect.poll(()=>statusCalls).toBe(1);await expect(form.locator('textarea')).toHaveValue('Received device with scratches');
    await expect(form.locator('[type=submit]')).toBeEnabled();await form.locator('[type=submit]').click();
    await expect.poll(()=>statusCalls).toBe(2);expect(evidenceCalls).toBe(1);
  });
  test(`${lang}: finish evidence appears at total100 and preserves rejected description/files`,async({page})=>{
    await orderFixture(page,lang,true,true);
    await page.evaluate(()=>window.frontendAudit.advanceOrderStage('order_evidence_ui',0));
    const form=page.locator('[data-form=order-stage-progress]'),finish=page.locator('[data-service-evidence-phase=finish]');
    await expect(finish).toBeHidden();await form.locator('[name=progressPercent]').fill('50');await expect(finish).toBeHidden();
    await form.locator('[name=progressPercent]').fill('100');await expect(finish).toBeVisible();
    let calls=0;
    await page.route('**/service-evidence/finish',async route=>{calls++;const body=route.request().postDataJSON();expect(body.files[0].filename).toBe('result.txt');await route.fulfill({status:422,contentType:'application/json',body:JSON.stringify({detail:[{loc:['body','description'],type:'string_too_short',ctx:{min_length:3}}]})});});
    await form.locator('[type=submit]').click();expect(calls).toBe(0);
    await finish.locator('textarea').fill('Service completed and tested');
    await finish.locator('[type=file]').setInputFiles({name:'result.txt',mimeType:'text/plain',buffer:Buffer.from('Service result')});
    await form.locator('[type=submit]').click();await expect.poll(()=>calls).toBe(1);
    await expect(finish.locator('textarea')).toHaveValue('Service completed and tested');await expect(finish.locator('textarea')).toHaveAttribute('aria-invalid','true');
    expect(await finish.locator('[type=file]').evaluate(input=>input.files.length)).toBe(1);
    await page.setViewportSize({width:390,height:844});
    expect(await form.evaluate(node=>node.scrollWidth<=node.clientWidth+1)).toBe(true);
    if(process.env.ERCLAVE_CAPTURE_EVIDENCE==='1'&&lang==='es'){
      const target=path.join(__dirname,'../../docs/auditorias/evidencias/service_evidence_20260913');fs.mkdirSync(target,{recursive:true});
      for(const width of [390,760,1280]){
        await page.setViewportSize({width,height:950});
        await page.screenshot({path:path.join(target,`finish-${width}.png`)});
      }
      await page.setViewportSize({width:390,height:950});await page.evaluate(()=>document.documentElement.dataset.theme="dark");await page.screenshot({path:path.join(target,"finish-dark-390.png")});
    }
  });
  test(`${lang}: product orders keep the progress form without evidence fields`,async({page})=>{
    await orderFixture(page,lang,false,true);
    await page.evaluate(()=>window.frontendAudit.advanceOrderStage('order_evidence_ui',0));
    await page.locator('[name=progressPercent]').fill('100');await expect(page.locator('[data-service-evidence-phase]')).toHaveCount(0);
  });
}
test('expired attachments keep written evidence and have no download action',async({page})=>{
  await orderFixture(page,'es',true,true);
  await page.evaluate(()=>{const a=window.frontendAudit,o=a.mockDb.findOrder('order_evidence_ui');o.serviceEvidence[0].files=[{id:'expired',filename:'photo.webp',expired:true}];a.mockDb.updateOrder(o);a.openServiceEvidenceHistory(o.id);});
  await expect(page.locator('.service-evidence-description')).toHaveText('Received in good condition');
  await expect(page.locator('[data-evidence-download]')).toHaveCount(0);
  await expect(page.locator('.service-evidence-fields').first()).toContainText('eliminado');
});
