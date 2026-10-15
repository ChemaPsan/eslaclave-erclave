const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");
const { installLocalAuth, signInAsLocalAdmin } = require("./local-auth");

const TENANT = "ten_739ee59d765d5e14818674800d";
// Test-only access to real view functions. No hook is shipped with the application.
const hook = `
window.frontendAudit = {
  state, mockDb, modules, closeModal, renderSalesServiceOrderModal, openSalesServiceTransitionModal, openSalesOrderFulfillmentModal, mapApiSalesOrder, mapApiSalesServiceOrder, renderSalesOrderCard,
  openProductServiceModal, openWarehouseModal, openInventoryItemModal,
  openInventoryMovementModal, openLaborAreaModal, openLaborRoleModal,
  openWorkerModal, openMachineModal, openPurchasingCancellationModal,
  renderPurchasingSubmodulePanel, enhanceEntitySelectors, renderMaintenanceSubmodulePanel,
  loadProductionApiData, loadHrApiData, loadPurchasingApiData,
  openMaintenanceActionModal, renderRecipeList, applyProductionActionPermissions, openRecipeModal, openSalesCustomerModal, openPurchasingSupplierModal, openMaintenanceTimeModal, renderAdminApiPanel, openSalesQuoteModal
};`;

test.beforeEach(async ({ page }) => {
  page.on("pageerror", error => console.error("Local form page error:", error.message));
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
  await page.route("**/v1/catalogs/code-sequences/*/next", route=>route.fulfill({json:{data:{code:"AUDIT-ONLY"}}}));
  await page.route("**/v1/inventory/warehouses/*/operation-context",route=>route.fulfill({json:{data:null}}));
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
    state.purchasingApi={...state.purchasingApi,references:{currencies:[{code:"MXN",name_es:"Peso mexicano",name_en:"Mexican peso"}],payment_terms:[{code:"cash",name_es:"Contado",name_en:"Cash"}]},suppliers:[],orders:[],receipts:[],requisitions:[{id:"req_audit",code:"REQ-AUDIT",required_date:"2026-09-07",priority:"normal",status:"draft",lines:[]}],items:[{id:"itm_audit",code:"MAT-AUDIT",name:"Material prueba",base_unit:"H87"}],warehouses:[]};
  });
});

async function rejectFields(page, path, paths) {
  const requests=[];
  await page.route(`**${path}`, async route=>{
    if(["GET","HEAD","OPTIONS"].includes(route.request().method()))return route.fallback();
    expect(route.request().headers()["x-tenant-id"]).toBe(TENANT);
    requests.push(route.request().postDataJSON());
    await route.fulfill({status:422,json:{detail:paths.map(loc=>({loc:["body",...loc.split(".")],type:"value_error",msg:"PRIVATE SERVER DIAGNOSTIC"}))}});
  });
  return requests;
}
async function assertField(form, selector, value) {
  const field=form.locator(selector);
  await expect(field).toHaveAttribute("aria-invalid","true");
  await expect(field).toHaveAttribute("aria-describedby",/field-error-/);
  if(value!==undefined)await expect(field).toHaveValue(value);
  await expect(form).not.toContainText("PRIVATE SERVER DIAGNOSTIC");
  await expect(form).toBeVisible();
}
for(const lang of ["es","en"]){
  test(`MAIN ${lang} Almacenes movement maps reason and hidden item to visible search`,async({page})=>{
    const requests=await rejectFields(page,"/v1/inventory/movements",["reason","inventory_item_id"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.openInventoryMovementModal(a.modules.find(m=>m.id==="almacenes"),{id:"movimientos"});},lang);
    const f=page.locator("#movementForm");
    await f.locator("[name=sourceDocument]").fill("AUDIT-KEEP");
    await f.locator("#movementItemSearch").fill("MAT-AUDIT");
    await page.locator("[data-inventory-item-id=itm_audit]").click();
    await f.locator("[name=warehouseId]").selectOption("wh_audit");
    await f.locator("[name=quantity]").fill("20");
    await f.locator("[name=reason]").fill("Recepcion prueba");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=reason]","Recepcion prueba");
    await assertField(f,"#movementItemSearch");
    await expect(f.locator("[name=sourceDocument]")).toHaveValue("AUDIT-KEEP");
    await expect(f.locator("[name=destinationWarehouseId]")).toBeHidden();
  });
  test(`MAIN ${lang} Produccion product maps name rejection and preserves capture`,async({page})=>{
    const requests=await rejectFields(page,"/v1/production/product-services/prs_audit",["name"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.openProductServiceModal("prs_audit");},lang);
    const f=page.locator("#productServiceForm");
    await f.locator("[name=name]").fill("Keep product");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=name]","Keep product");
    await expect(f.locator("[name=name]")).toBeFocused();
  });
  test(`MAIN ${lang} RH worker preserves capture on RFC rejection`,async({page})=>{
    const requests=await rejectFields(page,"/v1/hr/workers",["rfc"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.openWorkerModal();},lang);
    const f=page.locator("#workerForm");
    for(const [name,value] of Object.entries({first_names:"Persona",first_last_name:"Prueba",curp:"AAAA000101HDFRRN09",rfc:"AAAA000101ABC",nss:"00000000000",hire_date:"2026-01-01"}))await f.locator(`[name=${name}]`).fill(value);
    await f.locator("[name=labor_position_id]").selectOption("pos_audit");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=rfc]","AAAA000101ABC");
    await expect(f.locator("[name=rfc]")).toBeFocused();
  });
  test(`MAIN ${lang} Mantenimiento order reports title and preserves description`,async({page})=>{
    const requests=await rejectFields(page,"/v1/maintenance/orders",["title"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.state.active="mantenimiento";a.state.activeSubmodule="ordenes";a.state.maintenanceApi={...a.state.maintenanceApi,orders:[],workers:[],machines:[],productionOrders:[],items:[],warehouses:[]};a.renderMaintenanceSubmodulePanel(a.modules.find(m=>m.id==="mantenimiento"));},lang);
    const f=page.locator("#maintenanceOrderForm");
    for(const [name,value] of Object.entries({code:"MTO-AUDIT",title:"Keep maintenance",description:"Keep fault description",location:"Local audit"}))await f.locator(`[name=${name}]`).fill(value);
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=title]","Keep maintenance");
    await expect(f.locator("[name=description]")).toHaveValue("Keep fault description");
  });
  test(`MAIN ${lang} Mantenimiento time maps ended_at alias`,async({page})=>{
    const requests=await rejectFields(page,"/v1/maintenance/orders/mt_audit/time-entries",["ended_at"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.openMaintenanceTimeModal({id:"mt_audit",code:"MTO-AUDIT",title:"Audit",assigned_worker_id:"wrk_audit",assigned_worker_name:"Persona Prueba"},lang==="en");},lang);
    const f=page.locator("#maintenanceTimeModalForm");
    await f.locator("[name=time_notes]").fill("Keep time notes");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=time_ended_at]");
    await expect(f.locator("[name=time_notes]")).toHaveValue("Keep time notes");
  });
}
for(const lang of ["es","en"]){
  test(`MAIN ${lang} Compras supplier maps tax_id and preserves name`,async({page})=>{
    const requests=await rejectFields(page,"/v1/purchasing/suppliers",["tax_id"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.openPurchasingSupplierModal();},lang);
    const f=page.locator("#purchasingSupplierForm");
    for(const [name,value] of Object.entries({code:"SUP-AUDIT",commercial_name:"Keep supplier",legal_name:"Supplier SA",tax_id:"AAA010101AAA",billing_email:"supplier@example.test",fiscal_postal_code:"12345"}))await f.locator(`[name=${name}]`).fill(value);
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=tax_id]","AAA010101AAA");
    await expect(f.locator("[name=commercial_name]")).toHaveValue("Keep supplier");
  });
  test(`MAIN ${lang} Compras receipt filtered second DOM row receives payload index zero error`,async({page})=>{
    const requests=await rejectFields(page,"/v1/purchasing/receipts",["lines.0.quantity"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.state.active="compras";a.state.activeSubmodule="recepciones";a.state.purchasingReceiptSourceOrderId="po_audit";a.state.purchasingApi.orders=[{id:"po_audit",code:"PO-AUDIT",organization_context:{division_ref_id:"div-audit",society_ref_id:"soc-audit",cost_currency:"MXN"},status:"issued",lines:[1,2].map(i=>({id:`line_${i}`,line_type:"service",description:`Service ${i}`,quantity:10,received_quantity:0,unit_code:"E48"}))}];a.renderPurchasingSubmodulePanel(a.modules.find(m=>m.id==="compras"));},lang);
    const f=page.locator("#purchasingReceiptForm"),rows=f.locator("[data-receipt-line]");
    await f.locator("[name=code]").fill("REC-AUDIT");
    await rows.nth(1).locator("[name=quantity]").fill("2");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    expect(requests[0].lines[0].order_line_id).toBe("line_2");
    await assertField(f,"[data-line-id=line_2] [name=quantity]","2");
    await expect(rows.nth(0).locator("[name=quantity]")).not.toHaveAttribute("aria-invalid","true");
  });
  test(`MAIN ${lang} Administracion role keeps rejected fields`,async({page})=>{
    const requests=await rejectFields(page,"/v1/roles",["name"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.state.active="administracion";a.state.adminPanel="roles";a.renderAdminApiPanel(a.modules.find(m=>m.id==="administracion"));},lang);
    const f=page.locator("[data-form=admin-create-role]");
    await f.locator("[name=code]").fill("audit-only");
    await f.locator("[name=name]").fill("Keep role");
    await f.locator("[name=description]").fill("Keep description");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=name]","Keep role");
    await expect(f.locator("[name=description]")).toHaveValue("Keep description");
  });
  test(`MAIN ${lang} Ventas customer maps nested primary_contact email`,async({page})=>{
    const requests=await rejectFields(page,"/v1/sales/customers/customer_audit",["primary_contact.email"]);
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.state.salesApi.workers=[{id:"wrk_audit",full_name:"Persona",position_name:"Tecnico"}];a.state.salesApi.references={currencies:[{code:"MXN",name_es:"Peso",name_en:"Peso"}],payment_terms:[{code:"cash",name_es:"Contado",name_en:"Cash"}]};a.mockDb.saveModuleRecords("ventas",[{id:"customer_audit",code:"CLI-AUDIT",moduleId:"ventas",submoduleId:"clientes",recordType:"customer",status:"Activo",title:"Keep customer",fields:{commercialName:"Keep customer",contactName:"Persona",contactEmail:"customer@example.test",contactPhone:"5555555555",responsibleWorkerId:"wrk_audit",currency:"MXN",paymentTerms:"cash"}}]);a.openSalesCustomerModal(a.modules.find(m=>m.id==="ventas"),{id:"clientes"},"customer_audit");},lang);
    const f=page.locator("#salesCustomerForm");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=contactEmail]","customer@example.test");
    await expect(f.locator("[name=commercialName]")).toHaveValue("Keep customer");
  });
}
for(const lang of ["es","en"]){
  test(`MAIN ${lang} Ventas quote second line gets only its own quantity error`,async({page})=>{
    const requests=await rejectFields(page,"/v1/sales/quotes/quote_audit",["lines.1.quantity"]);
    await page.evaluate(async lang=>{const a=window.frontendAudit;a.state.lang=lang;a.state.salesApi.references={currencies:[{code:"MXN",name_es:"Peso",name_en:"Peso"}],payment_terms:[{code:"cash",name_es:"Contado",name_en:"Cash"}]};a.mockDb.saveModuleRecords("ventas",[{id:"customer_audit",code:"CLI-AUDIT",moduleId:"ventas",submoduleId:"clientes",recordType:"customer",status:"Activo",title:"Cliente",fields:{currency:"MXN",paymentTerms:"cash"}},{id:"quote_audit",code:"COT-AUDIT",moduleId:"ventas",submoduleId:"cotizaciones",recordType:"quote",status:"Borrador",fields:{customerId:"customer_audit",currency:"MXN",paymentTerms:"cash",validUntil:"2026-12-31",lines:[1,2].map(quantity=>({productServiceId:"prs_audit",quantity,unit:"E48",unitPrice:100,discount:0}))}}]);await a.openSalesQuoteModal(a.modules.find(m=>m.id==="ventas"),{id:"cotizaciones"},"quote_audit");},lang);
    const f=page.locator("#salesQuoteForm");
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[data-quote-line]:nth-child(2) [name=lineQuantity]","2");
    await expect(f.locator("[data-quote-line]").first().locator("[name=lineQuantity]")).not.toHaveAttribute("aria-invalid","true");
  });
  test(`MAIN ${lang} Produccion recipe maps resources and second stage by identity`,async({page})=>{
    const requests=await rejectFields(page,"/v1/production/recipes",["resources.1.quantity","stages.1.weight_percent"]);
    await page.route("**/v1/hr/areas",route=>route.fulfill({json:{data:[1,2].map(i=>({id:`area_${i}`,code:`AREA-${i}`,name:`Area ${i}`,status:"active"}))}}));
    await page.route("**/v1/hr/positions?*",route=>route.fulfill({json:{data:[1,2].map(i=>({id:`pos_${i}`,labor_area_id:`area_${i}`,recipe_name:`Technician ${i}`,status:"active",intervenes_in_production:true,resource_quantity:1,minutes_per_resource:480,hourly_cost:10}))}}));
    await page.route("**/v1/inventory/items?*",route=>route.fulfill({json:{data:[1,2].map(i=>({id:`recipe_item_${i}`,name:`Material ${i}`,code:`MAT-${i}`,base_unit:"H87",default_unit_cost:1,status:"active",use_in_recipe:true}))}}));
    await page.route("**/v1/inventory/balances?*",route=>route.fulfill({json:{data:[]}}));
    await page.evaluate(async lang=>{const a=window.frontendAudit;a.state.lang=lang;await a.openRecipeModal();},lang);
    const f=page.locator("#recipeForm");
    for(const i of [1,2]){
      await f.locator("#resourceSelect-material").selectOption(`recipe_item_${i}`);
      await f.locator('[data-action=add-resource][data-resource-type=material]').click();
      await f.locator(`[name=resource_recipe_item_${i}]`).fill(String(i));
      await f.locator(`[name=stageAreaId][value=area_${i}]`).check();
      await f.locator(".recipe-area-option").nth(i-1).locator("[data-stage-weight]").fill("50");
    }
    await f.locator("[type=submit]").click();
    await expect.poll(()=>requests.length).toBe(1);
    await assertField(f,"[name=resource_recipe_item_2]","2");
    await expect(f.locator("[name=resource_recipe_item_1]")).not.toHaveAttribute("aria-invalid","true");
    await expect(f.locator(".recipe-area-option").nth(1).locator("[data-stage-weight]")).toHaveAttribute("aria-invalid","true");
    await expect(f.locator(".recipe-area-option").nth(0).locator("[data-stage-weight]")).not.toHaveAttribute("aria-invalid","true");
  });
}

for(const lang of ["es","en"]){
 test(`CHG304 ${lang} order snapshot, cancellation retry and service execution boundary`,async({page})=>{
  const requests=[];
  await page.route('**/v1/sales/orders/scoped-order/cancel',route=>{requests.push({headers:route.request().headers(),body:route.request().postDataJSON()});return requests.length===3?route.fulfill({status:422,json:{error:{code:'validation_failed',message:'PRIVATE SQL',details:{issues:[{loc:['body','reason'],type:'string_too_short',msg:'PRIVATE SQL',ctx:{min_length:3}}]}}}}):route.fulfill({status:503,json:{error:{code:'authority_unavailable',message:'PRIVATE SQL'}}});});
  await page.evaluate(lang=>{
   const a=window.frontendAudit;a.state.lang=lang;
   a.state.sessionApi.data.permissions=[...a.state.sessionApi.data.permissions,'sales.order.cancel'];
   const item={id:'scoped-order',code:'ORDER-SCOPE',status:'confirmed',quote_id:'quote',quote_code:'QUOTE',customer_code:'CLI',customer_name:'Customer',currency:'MXN',division_ref_id:'div-a',society_ref_id:'soc-a',commercial_terms_snapshot:{division:{code:'DIV-A',name:'Division <script>unsafe</script>'},terms_revision:2,values:{currency:'MXN',payment_terms:'cash',credit_limit:'0.00'}},lines:[]};
   const record=a.mapApiSalesOrder(item);if(!a.renderSalesOrderCard(record).includes(lang==='es'?'División y condiciones':'Division and terms'))throw new Error('Missing contextual action label');a.mockDb.saveModuleRecords('ventas',[record]);a.openSalesOrderFulfillmentModal(a.modules.find(m=>m.id==='ventas'),record.id);
  },lang);
  const form=page.locator('[data-scoped-order]');await expect(form.locator('[data-order-context]')).toContainText('DIV-A');await expect(form.locator('script')).toHaveCount(0);await expect(form.locator('select')).toHaveCount(0);
  await expect(form.locator('[name=reason]')).toHaveAttribute('maxlength','500');await expect(form.locator('[name=reason]')).toHaveAttribute('minlength','3');
  await form.locator('[name=reason]').fill('Cancelación de prueba');await form.locator('[type=submit]').click();await expect(form.locator('[type=submit]')).toBeEnabled();await expect(form.locator('[name=reason]')).toHaveValue('Cancelación de prueba');await expect(form).not.toContainText('PRIVATE SQL');await form.locator('[type=submit]').click();await expect.poll(()=>requests.length).toBe(2);expect(requests[0].headers['idempotency-key']).toBe(requests[1].headers['idempotency-key']);await expect(form.locator('[type=submit]')).toBeEnabled();await form.locator('[type=submit]').click();await assertField(form,'[name=reason]','Cancelación de prueba');
  await page.evaluate(()=>{const a=window.frontendAudit;const order=a.mockDb.findModuleRecord('ventas','scoped-order');a.closeModal();a.state.sessionApi.data.permissions=a.state.sessionApi.data.permissions.filter(p=>!p.startsWith('sales.service_order.'));a.renderSalesServiceOrderModal({...order,id:'service',recordType:'serviceOrder',status:'draft'});});
  await expect(page.locator('#modalContent [data-order-context]')).toContainText('MXN');await expect(page.locator('#modalContent form')).toHaveCount(0);await expect(page.locator('[data-service-transition]')).toHaveCount(0);
  await page.locator('#modalContent').evaluate(n=>n.style.width='320px');expect(await page.locator('[data-order-context]').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);
  await page.screenshot({path:test.info().outputPath('order-context.png'),fullPage:true});
 });
}

for(const lang of ['es','en']){
 test(`CHG305 ${lang} scoped service workers, assignment retry and cost feedback`,async({page})=>{
  const queries=[],requests=[];
  await page.route('**/v1/sales/service-orders/service-scope/eligible-workers?*',route=>{queries.push(new URL(route.request().url()).searchParams.get('q'));return route.fulfill({json:{data:[{id:'worker-a',employee_number:'EMP-A',full_name:'Worker A',position_name:'Role A',division_ref_id:'division-a'}],has_more:false}});});
  await page.route('**/v1/sales/service-orders/service-scope/transitions/assign',route=>{requests.push({headers:route.request().headers(),payload:route.request().postDataJSON()});return route.fulfill({status:503,json:{error:{code:'authority_unavailable',message:'PRIVATE SQL'}}});});
  await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;const record={id:'service-scope',code:'OS-SCOPE',status:'planned',fields:{divisionRefId:'division-a',societyRefId:'society-a',productServiceName:'Service',commercialTermsSnapshot:{division:{code:'DIV-A',name:'Division A'},terms_revision:2,values:{currency:'USD',payment_terms:'cash',credit_limit:'0'}}}};window.scopedService=record;a.renderSalesServiceOrderModal(record);a.openSalesServiceTransitionModal(record,'assign');},lang);
  const form=page.locator('#serviceTransitionForm');await expect(form.locator('[name=responsible_worker_id] option[value=worker-a]')).toHaveCount(1);
  await form.locator('[data-worker-query]').fill('Worker');await form.locator('[data-worker-find]').click();await expect.poll(()=>queries.includes('Worker')).toBe(true);
  await form.locator('[name=responsible_worker_id]').selectOption('worker-a');await form.locator('[type=submit]').click();await expect(form.locator('[type=submit]')).toBeEnabled();await expect(form.locator('[name=responsible_worker_id]')).toHaveValue('worker-a');await form.locator('[type=submit]').click();await expect.poll(()=>requests.length).toBe(2);expect(requests[0].headers['idempotency-key']).toBe(requests[1].headers['idempotency-key']);expect(requests[0].payload).toEqual({responsible_worker_id:'worker-a'});await expect(form).not.toContainText('PRIVATE SQL');
  await page.route('**/v1/sales/service-orders/service-scope/cost-entries',route=>route.fulfill({status:422,json:{detail:[{loc:['body','unit_cost'],type:'greater_than_equal',msg:'PRIVATE SQL',ctx:{ge:0}}]}}));
  await page.evaluate(()=>{window.scopedService.status='in_progress';window.scopedService.fields.currency='USD';window.frontendAudit.state.sessionApi.data.scope={version:2,divisions:[{id:'division-a',society_id:'society-a'}],societies:[{id:'society-a',base_currency:'USD'}]};window.frontendAudit.renderSalesServiceOrderModal(window.scopedService);});
  await expect(page.locator('[data-order-context]')).toContainText('USD');const costs=page.locator('#serviceOrderCostForm');await costs.locator('[name=description]').fill('Explicit cost');await costs.locator('[name=quantity]').fill('2');await costs.locator('[name=unit_cost]').fill('3');await costs.locator('[name=confirm_cost_currency]').check();await costs.locator('[type=submit]').click();await assertField(costs,'[name=unit_cost]','3');await expect(costs.locator('[name=description]')).toHaveValue('Explicit cost');
  const times=page.locator('#serviceOrderTimeForm');await expect(times.locator('[name=worker_id] option[value=worker-a]')).toHaveCount(1);await expect(times.locator('[name=minutes]')).toHaveAttribute('max','1440');
  await page.locator('#modalContent').evaluate(n=>n.style.width='320px');expect(await page.locator('.service-order-modal').evaluate(n=>n.scrollWidth<=n.clientWidth)).toBe(true);await page.screenshot({path:test.info().outputPath('service-context.png'),fullPage:true});
 });
}
