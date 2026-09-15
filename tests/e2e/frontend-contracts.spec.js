const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");
const { installLocalAuth, signInAsLocalAdmin } = require("./local-auth");

const TENANT = "ten_739ee59d765d5e14818674800d";
// Test-only access to real view functions. No hook is shipped with the application.
const hook = `
window.frontendAudit = {
  state, mockDb, modules, closeModal, renderSalesServiceOrderModal,
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

test("Productos/Servicios conserva el tipo inmutable y el estatus separado", async ({page}) => {
  await page.evaluate(()=>window.frontendAudit.openProductServiceModal("prs_audit"));
  await expect(page.locator("#productServiceForm [name=kind]")).toBeDisabled();
  await expect(page.locator("#productServiceForm [name=kind]")).toHaveValue("Servicio");
  await expect(page.locator("#productServiceForm [name=status]")).toBeDisabled();
  await expect(page.locator("[data-product-inventory-field]")).toBeHidden();
  let body;
  await page.route("**/v1/production/product-services/prs_audit",async route=>{body=route.request().postDataJSON();await route.fulfill({status:409,contentType:"application/json",body:JSON.stringify({error:{code:"invalid_state"}})});});
  await page.locator("#productServiceForm button[type=submit]").click();
  await expect.poll(()=>body).toBeTruthy();
  expect(body.inventory_item_id).toBeNull();
  expect(body).not.toHaveProperty("type");
  await expect(page.locator("#productServiceForm")).toBeVisible();
  await expect(page.locator("#formErrors")).toBeVisible();
});

test("las altas solo ofrecen el estatus activo que persiste el contrato",async({page})=>{
  for(const kind of ["warehouse","item","area","position","machine"]){
    await page.evaluate(async kind=>{
      const a=window.frontendAudit,m=a.modules.find(m=>m.id==="almacenes");
      if(kind==="warehouse")a.openWarehouseModal(m,{id:"almacenes"});
      if(kind==="item")await a.openInventoryItemModal(m,{id:"articulos"});
      if(kind==="area")a.openLaborAreaModal();
      if(kind==="position")a.openLaborRoleModal();
      if(kind==="machine")await a.openMachineModal();
    },kind);
    await expect(page.locator("#modalContent [name=status]")).toBeDisabled();
    await expect(page.locator("#modalContent [name=status]")).toHaveValue("Activo");
    await page.evaluate(()=>window.frontendAudit.closeModal());
  }
});

test("editar articulo conserva politica lot y editar trabajador conserva fecha inmutable",async({page})=>{
  await page.evaluate(async()=>{const a=window.frontendAudit;await a.openInventoryItemModal(a.modules.find(m=>m.id==="almacenes"),{id:"articulos"},"itm_audit");});
  await expect(page.locator("#inventoryItemForm [name=policy]")).toHaveValue("batch");
  await expect(page.locator("#inventoryItemForm [name=policy]")).toBeDisabled();
  await page.evaluate(()=>{window.frontendAudit.closeModal();window.frontendAudit.openWorkerModal("wrk_audit");});
  await expect(page.locator("#workerForm [name=birth_date]")).toHaveValue("1990-01-01");
  await expect(page.locator("#workerForm [name=birth_date]")).toBeDisabled();
});

test("cambiar producto terminado a materia prima elimina el vinculo oculto",async({page})=>{
  await page.route("**/v1/production/product-services?*inventory_mapping=missing",route=>route.fulfill({json:{data:[{id:"unlinked",code:"PT",name:"Producto",base_unit:"H87",type:"product",status:"active"}]}}));
  await page.evaluate(async()=>{const a=window.frontendAudit;await a.openInventoryItemModal(a.modules.find(m=>m.id==="almacenes"),{id:"articulos"});});
  const form=page.locator("#inventoryItemForm");
  await form.locator("[name=type]").selectOption("finishedGood");
  await form.locator("[name=productionProductId]").selectOption("unlinked");
  await expect(form.locator("[name=unit]")).toBeDisabled();
  await form.locator("[name=type]").selectOption("rawMaterial");
  await expect(form.locator("[name=productionProductId]")).toBeDisabled();
  await expect(form.locator("[name=productionProductId]")).toHaveValue("");
  await expect(form.locator("[name=unit]")).toBeEnabled();
});

test("salida API consulta al backend aun sin movimientos cargados y restaura rechazo",async({page})=>{
  let payload;
  await page.route("**/v1/inventory/movements",async route=>{if(route.request().method()!=="POST")return route.fallback();payload=route.request().postDataJSON();await route.fulfill({status:409,json:{error:{code:"insufficient_stock",message:"private diagnostic"}}});});
  await page.evaluate(()=>{const a=window.frontendAudit;a.openInventoryMovementModal(a.modules.find(m=>m.id==="almacenes"),{id:"movimientos"});});
  const form=page.locator("#movementForm");
  await form.locator("[name=movementType]").selectOption("transfer");
  await form.locator("[name=destinationWarehouseId]").selectOption("wh_other");
  await form.locator("[name=movementType]").selectOption("exit");
  await expect(form.locator("[name=destinationWarehouseId]")).toBeDisabled();
  await form.locator("[name=sourceDocument]").fill("AUDIT-DOC");
  await form.locator("#movementItemSearch").fill("MAT-AUDIT");
  await page.locator("[data-inventory-item-id=itm_audit]").click();
  await form.locator("[name=warehouseId]").selectOption("wh_audit");
  await form.locator("[name=quantity]").fill("1");
  await form.locator("button[type=submit]").click();
  await expect.poll(()=>payload).toBeTruthy();
  expect(payload.destination_warehouse_id).toBeNull();
  expect(payload.inventory_item_id).toBe("itm_audit");
  await expect(page.locator("#formErrors")).toBeVisible();
  await expect(page.locator("#formErrors")).not.toContainText("private diagnostic");
  await expect(form).toBeVisible();
});

test("Compras recupera unidad autoritativa al alternar servicio y articulo",async({page})=>{
  await page.evaluate(()=>{const a=window.frontendAudit;a.state.active="compras";a.state.activeSubmodule="requisiciones";a.renderPurchasingSubmodulePanel(a.modules.find(m=>m.id==="compras"));});
  const row=page.locator("[data-requisition-line]");
  await row.locator("[name=inventory_item_id]").selectOption("itm_audit");
  await row.locator("[name=line_type]").selectOption("service");
  await expect(row.locator("[name=inventory_item_id]")).toBeDisabled();
  await row.locator("[name=unit_code]").selectOption("E48");
  await row.locator("[name=line_type]").selectOption("inventory_item");
  await expect(row.locator("[name=unit_code]")).toHaveValue("H87");
});

test("cancelacion Compras usa los limites 3 a 500 del contrato",async({page})=>{
  await page.evaluate(()=>window.frontendAudit.openPurchasingCancellationModal("requisition","req_audit"));
  const reason=page.locator("#purchasingCancellationForm [name=reason]");
  await expect(reason).toHaveAttribute("minlength","3");
  await expect(reason).toHaveAttribute("maxlength","500");
  await reason.fill("x");
  await page.locator("#purchasingCancellationForm button[type=submit]").click();
  await expect(page.locator("#purchasingCancellationForm")).toBeVisible();
});

test("Ventas conserva las fechas guardadas al reabrir planeacion de servicio",async({page})=>{
  await page.evaluate(()=>window.frontendAudit.renderSalesServiceOrderModal({id:"svo_audit",code:"OS-AUDIT",status:"planned",fields:{scheduledStartAt:"2026-09-09",scheduledEndAt:"2026-09-10"}}));
  await expect(page.locator("#serviceOrderPlanForm [name=scheduled_start_at]")).toHaveValue("2026-09-09");
  await expect(page.locator("#serviceOrderPlanForm [name=scheduled_end_at]")).toHaveValue("2026-09-10");
});

for(const [module,permission,allowed] of [
  ["production","production.product_service.read","product-services"],
  ["hr","hr.area.read","areas"],
  ["purchasing","purchasing.supplier.read","suppliers"]
])test(`${module}: lectura puntual funciona sin permisos para el resto del modulo`,async({page})=>{
  const requests=[];
  const base={production:8002,hr:8006,purchasing:8010}[module];
  await page.route(`http://127.0.0.1:${base}/v1/${module}/**`,async route=>{
    const resource=new URL(route.request().url()).pathname.split("/")[3];requests.push(resource);
    await route.fulfill({status:resource===allowed?200:403,json:resource===allowed?{data:[]}:{error:{code:"permission_denied"}}});
  });
  const status=await page.evaluate(async({module,permission})=>{
    const a=window.frontendAudit;a.state.sessionApi.data.permissions=[permission];
    if(module==="production")await a.loadProductionApiData();
    if(module==="hr")await a.loadHrApiData();
    if(module==="purchasing")await a.loadPurchasingApiData();
    return a.state[`${module}Api`].status;
  },{module,permission});
  expect(status).toBe("ready");
  expect(requests).toEqual([allowed]);
});

test("Administracion consulta roles sin exigir acceso a usuarios o configuracion",async({page})=>{
  const requested=[];
  await page.route("http://127.0.0.1:8000/v1/**",async route=>{
    const pathname=new URL(route.request().url()).pathname;requested.push(pathname);
    if(pathname==="/v1/session/context")return route.fulfill({json:{data:{tenant:{id:TENANT},permissions:["admin.role.read"]}}});
    const allowed=["/v1/roles","/v1/permissions"].includes(pathname);
    return route.fulfill({status:allowed?200:403,json:allowed?{data:[]}:{error:{code:"permission_denied"}}});
  });
  const data=await page.evaluate(async()=> (await import("/api/admin.js")).getAdminDashboard());
  expect(data.roles).toEqual([]);
  expect(requested.sort()).toEqual(["/v1/permissions","/v1/roles","/v1/session/context"]);
});

test("Mantenimiento puede resolver con diagnostico existente sin permiso de editar",async({page})=>{
  const commands=[];
  await page.route("**/v1/maintenance/orders/mt_audit**",async route=>{
    commands.push({method:route.request().method(),path:new URL(route.request().url()).pathname,payload:route.request().postDataJSON()});
    await route.fulfill({status:409,json:{error:{code:"invalid_order_transition"}}});
  });
  await page.evaluate(()=>{
    const a=window.frontendAudit;a.state.sessionApi.data.permissions=["maintenance.order.read","maintenance.order.resolve"];
    a.openMaintenanceActionModal({id:"mt_audit",code:"MT-AUDIT",title:"Prueba",status:"in_progress",total_minutes:10,diagnosis:"Diagnostico confirmado",work_performed:"Reparacion terminada",verification_notes:"Verificado"},"resolve",false);
  });
  await expect(page.locator("#maintenanceActionForm [name=diagnosis]")).toBeDisabled();
  await page.locator("#maintenanceActionForm button[type=submit]").click();
  await expect.poll(()=>commands.length).toBe(1);
  expect(commands[0]).toEqual({method:"POST",path:"/v1/maintenance/orders/mt_audit/transitions",payload:{transition:"resolve"}});
  await expect(page.locator("#maintenanceActionForm")).toBeVisible();
});

test("Produccion no ofrece aprobar borrador sin enviar ni eliminar una receta API",async({page})=>{
  await page.evaluate(()=>{
    const a=window.frontendAudit;
    a.state.active="produccion";a.state.activeSubmodule="recetas";
    a.state.sessionApi.data.permissions=["production.recipe.read","production.recipe.approve"];
    a.mockDb.saveRecipes([{id:"rec_audit",product:"Prueba",version:1,versionStatus:"draft",approvalStatus:"Borrador",resources:[],steps:[]}]);
    document.querySelector("#modulePanel").innerHTML=a.renderRecipeList(a.mockDb.loadRecipes());
    a.applyProductionActionPermissions();
  });
  for(const action of ["approve-recipe","edit-recipe","delete-recipe"])await expect(page.locator(`[data-action='${action}']`)).toBeDisabled();
});

test("Maquinaria conserva costo cero al editar y servicios limitan tiempo a 1440 minutos",async({page})=>{
  await page.evaluate(async()=>{
    const a=window.frontendAudit;
    a.mockDb.saveMachines([{id:"maq_audit",code:"MAQ-AUDIT",name:"Maquina",area:"Area prueba",areaId:"area_audit",machineType:"Equipo",available:480,cost:0,status:"Activo"}]);
    await a.openMachineModal("maq_audit");
  });
  await expect(page.locator("#machineForm [name=cost]")).toHaveValue("0");
  await page.evaluate(()=>window.frontendAudit.renderSalesServiceOrderModal({id:"svo_audit",code:"OS-AUDIT",status:"in_progress",fields:{}}));
  await expect(page.locator("#serviceOrderTimeForm [name=minutes]")).toHaveAttribute("max","1440");
});

test("formularios corregidos mantienen controles visibles en contenedor estrecho ES/EN",async({page},testInfo)=>{
  for(const lang of ["es","en"]){
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(lang=>{const a=window.frontendAudit;a.state.lang=lang;a.openPurchasingCancellationModal("requisition","req_audit");},lang);
    const reason=page.locator("#purchasingCancellationForm [name=reason]");
    await reason.fill("Motivo de prueba / Test reason");
    await expect(reason).toBeVisible();
    await expect(page.locator("#purchasingCancellationForm button[type=submit]")).toBeVisible();
    const widths=await page.locator("#purchasingCancellationForm").evaluate(form=>({client:form.clientWidth,scroll:form.scrollWidth}));
    expect(widths.scroll).toBeLessThanOrEqual(widths.client+1);
    await page.screenshot({path:testInfo.outputPath(`form-${lang}-390.png`)});
    await page.evaluate(()=>window.frontendAudit.closeModal());
  }
});

test("Recetas conserva campos derivados y ofrece solo aprobaciones autorizadas",async({page})=>{
  await page.evaluate(async()=>{
    const a=window.frontendAudit;
    a.state.sessionApi.data.permissions=a.state.sessionApi.data.permissions.filter(p=>!["production.recipe.submit","production.recipe.approve"].includes(p));
    await a.openRecipeModal();
  });
  for(const name of ["version","center"])await expect(page.locator(`#recipeForm [name=${name}]`)).toHaveAttribute("readonly","");
  await expect(page.locator("#recipeForm [name=approvalStatus]")).toHaveValue("Borrador");
  await expect(page.locator("#recipeForm [name=approvalStatus] option[value=Aprobada]")).toHaveAttribute("disabled","");
  await expect(page.locator("#recipeForm [name=approvalStatus] option[value=Obsoleta]")).toHaveCount(0);
});

test("editar proveedor conserva codigos existentes que no estaban en la lista corta",async({page})=>{
  await page.evaluate(()=>{
    const a=window.frontendAudit;a.state.active="compras";a.state.activeSubmodule="proveedores";
    a.state.purchasingSupplierEditId="sup_audit";
    a.state.purchasingApi.suppliers=[{id:"sup_audit",code:"PROV-AUDIT",commercial_name:"Proveedor",tax_regime:"620",fiscal_country:"US",fiscal_postal_code:"12345-6789",currency:"CAD",payment_terms:"credit_45",status:"active"}];
    a.renderPurchasingSubmodulePanel(a.modules.find(m=>m.id==="compras"));
  });
  await page.locator('[data-edit-supplier="sup_audit"]').click();
  for(const [name,value] of Object.entries({tax_regime:"620",fiscal_country:"US",currency:"CAD",payment_terms:"credit_45"}))await expect(page.locator(`#purchasingSupplierForm [name=${name}]`)).toHaveValue(value);
  await expect(page.locator("#purchasingSupplierForm [name=fiscal_postal_code]")).not.toHaveAttribute("pattern",/.+/);
});

async function renderRecoverableParts(page,status="processing",operation="reserve",lang="es"){
  await page.evaluate(({status,operation,lang})=>{
    const a=window.frontendAudit,s=a.state;s.lang=lang;s.active="mantenimiento";s.activeSubmodule="ordenes";
    s.maintenanceApi={...s.maintenanceApi,status:"ready",workers:[],machines:[],productionOrders:[],orders:[{id:"mwo_recovery",code:"MTO-RECOVERY",title:"Recuperación de refacciones",priority:"medium",location:"Local",status:"waiting_parts",material_requests:[{id:"mmr_recovery",warehouse_name:"Refacciones",status,pending_operation:operation,lines:[{id:"line_recovery",item_code:"ROD-01",item_name:"Rodamiento",quantity:1.125,unit_code:"H87",line_status:"failed"}]}]}]};
    a.renderMaintenanceSubmodulePanel(a.modules.find(m=>m.id==="mantenimiento"));
  },{status,operation,lang});
}

test("recuperacion de refacciones distingue reserva cancelacion entrega y permiso ES EN",async({page})=>{
  await page.setViewportSize({width:1280,height:900});
  await page.addStyleTag({content:"#modulePanel {width:520px;max-width:100%;}"});
  for(const lang of ["es","en"]){
    await renderRecoverableParts(page,"processing","reserve",lang);
    await expect(page.locator("[data-reconcile-maintenance-material]")).toHaveText(lang==="es"?"Reintentar reserva":"Retry reservation");
    const bounds=await page.locator(".maintenance-material-request").evaluate(n=>({client:n.clientWidth,scroll:n.scrollWidth}));
    expect(bounds.scroll).toBeLessThanOrEqual(bounds.client+1);
    await renderRecoverableParts(page,"cancelling","cancel",lang);
    await expect(page.locator("[data-reconcile-maintenance-material]")).toHaveText(lang==="es"?"Reintentar cancelación":"Retry cancellation");
    for(const action of await page.locator(".maintenance-order-actions > button").all())expect((await action.boundingBox()).height).toBeLessThan(80);
    await page.locator(".maintenance-order-card").screenshot({path:test.info().outputPath(`parts-recovery-${lang}.png`)});
  }
  await renderRecoverableParts(page,"processing","issue");
  await expect(page.locator("[data-reconcile-maintenance-material]")).toHaveCount(0);
  await page.evaluate(()=>{const s=window.frontendAudit.state;s.sessionApi.data.permissions=s.sessionApi.data.permissions.filter(p=>p!=="maintenance.material_request.reconcile");});
  await renderRecoverableParts(page);
  await expect(page.locator("[data-reconcile-maintenance-material]")).toHaveCount(0);
});

test("recuperacion de refacciones bloquea doble clic y restaura accion ante concurrencia",async({page})=>{
  let calls=0,finish;
  await page.route("**/v1/maintenance/material-requests/mmr_recovery/reconcile",async route=>{
    calls++;expect(route.request().headers()["x-tenant-id"]).toBe(TENANT);expect(route.request().headers()["idempotency-key"]).toBeTruthy();
    await new Promise(resolve=>finish=resolve);
    await route.fulfill({status:409,json:{error:{code:"command_in_progress",message:"internal diagnostic must stay hidden"}}});
  });
  await renderRecoverableParts(page);
  const button=page.locator("[data-reconcile-maintenance-material]");
  await button.click();await expect(button).toBeDisabled();
  await expect.poll(()=>calls).toBe(1);finish();
  await expect(button).toBeEnabled();
  await expect(page.locator("body")).not.toContainText("internal diagnostic must stay hidden");
  await expect(button).toHaveText("Reintentar reserva");
  expect(calls).toBe(1);
});

for (const lang of ['es','en']) {
  test(`${lang}: expected margin accepts values above 100 without losing rejected input`, async ({page}) => {
    await page.evaluate(lang=>{window.frontendAudit.state.lang=lang;window.frontendAudit.openProductServiceModal('prs_audit');},lang);
    const input=page.locator('#productServiceForm [name=expectedMargin]');
    await expect(input).not.toHaveAttribute('max');
    await expect(page.locator('#expectedMarginHelp')).toContainText('400%');
    let body;
    await page.route('**/v1/production/product-services/prs_audit',async route=>{
      body=route.request().postDataJSON();
      await route.fulfill({status:422,contentType:'application/json',body:JSON.stringify({detail:[{loc:['body','expected_margin'],type:'greater_than_equal',ctx:{ge:0}}]})});
    });
    for (const value of ['400','22122.22','1000000']) {
      await input.fill(value);
      await page.locator('#productServiceForm button[type=submit]').click();
      await expect.poll(()=>body?.expected_margin).toBe(Number(value));
      await expect(input).toHaveValue(value);
      await expect(input).toHaveAttribute('aria-invalid','true');
      await expect(input).toBeFocused();
    }
  });
}

test('expected margin remains the saved percentage in the card and reopened form', async ({page}) => {
  const markup=await page.evaluate(()=>{
    const audit=window.frontendAudit;
    const item=audit.mockDb.findProductService('prs_audit');
    audit.mockDb.updateProductService({...item,expectedMargin:400,standardCost:900,targetPrice:200000});
    audit.openProductServiceModal('prs_audit');
    return audit.renderProductsServicesCatalogScreen();
  });
  await expect(page.locator('#productServiceForm [name=expectedMargin]')).toHaveValue('400');
  expect(markup).toMatch(/400(?:[.,]0+)?%/);
});
