const { test, expect } = require('@playwright/test');

// Isolated DOM fixtures exercise the real browser helper, not authenticated UAT.
// No application shell, external request or API mutation is allowed.
async function setup(page, markup, lang = 'es') {
  const baseURL = test.info().project.use.baseURL;
  const origin = new URL(baseURL).origin;
  if (!['127.0.0.1','localhost','[::1]'].includes(new URL(origin).hostname)) throw new Error('Fixtures require loopback');
  await page.route('**/*', route => {
    const request = route.request(), url = new URL(request.url());
    if (url.origin !== origin || request.method() !== 'GET') return route.abort();
    if (url.pathname === '/__form_feedback_fixture') return route.fulfill({ contentType: 'text/html', body: '<!doctype html><html><head><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/features/form-feedback.css"></head><body></body></html>' });
    return route.continue();
  });
  await page.goto(`${origin}/__form_feedback_fixture`);
  await page.evaluate(async ({markup, lang}) => {
    document.body.innerHTML = markup;
    window.feedback = await import('/features/form-feedback.js');
    window.bindings = await import('/features/form-bindings.js');
    window.feedback.installFormFeedback({ getLanguage: () => lang });
    document.addEventListener('submit', event => event.preventDefault());
  }, {markup, lang});
}
async function reject(page, issues, extra = {}, formId = 'movementForm') {
  await page.evaluate(({issues,extra,formId}) => window.feedback.renderFormFeedback(document.getElementById(formId), [{code:'validation_failed',status:422,details:{issues},...extra}]), {issues,extra,formId});
}
const reasonForm = `<form id="movementForm"><label><span>Motivo</span><input name="reason" value="ok" aria-describedby="reason-help"></label><small id="reason-help">Help</small><label><span>Quantity</span><input name="quantity" value="20"></label><button>Save</button></form>`;
for (const lang of ['es','en']) {
  test(`${lang}: server fields preserve values, focus, descriptions and correction scope`, async ({page}) => {
    await setup(page,reasonForm,lang);
    await reject(page,[{loc:['body','reason'],type:'string_too_short',ctx:{min_length:3}},{loc:['body','quantity'],type:'greater_than',ctx:{gt:0}}]);
    const reason=page.locator('[name=reason]'), quantity=page.locator('[name=quantity]');
    await expect(reason).toHaveValue('ok'); await expect(quantity).toHaveValue('20');
    await expect(reason).toBeFocused(); await expect(reason).toHaveAttribute('aria-invalid','true');
    await expect(reason).toHaveAttribute('aria-describedby',/reason-help field-error-/);
    await expect(page.locator('[data-field-error]').first()).toHaveText(lang==='es'?'Escribe al menos 3 caracteres.':'Enter at least 3 characters.');
    await page.locator('.form-error-link').nth(1).click(); await expect(quantity).toBeFocused();
    await reason.fill('corrected');
    await expect(reason).not.toHaveAttribute('aria-invalid','true'); await expect(reason).toHaveAttribute('aria-describedby','reason-help');
    await expect(quantity).toHaveAttribute('aria-invalid','true'); await expect(page.locator('[data-field-error]')).toHaveCount(1);
    await quantity.fill('4'); await expect(page.locator('[data-form-feedback]')).toBeHidden();
  });
  test(`${lang}: unresolved and indexed fields remain safe general errors`, async ({page}) => {
    await setup(page,reasonForm,lang);
    await reject(page,[{loc:['body','lines',1,'quantity'],type:'greater_than',ctx:{gt:0}},{loc:['body','server_only'],type:'missing',msg:'reason is wrong'}],{correlationId:'test-ref-123'});
    await expect(page.locator('[aria-invalid=true]')).toHaveCount(0);
    await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'Contacta a soporte':'Contact support');
    await expect(page.locator('[data-form-feedback]')).toContainText('test-ref-123');
    await expect(page.locator('[data-form-feedback]')).toBeFocused();
    await expect(page.locator('[name=reason]')).toHaveValue('ok');
  });
  test(`${lang}: native required email range and hidden controls`, async ({page}) => {
    await setup(page,`<form id="movementForm"><label><span>Name</span><input name="name" required></label><label><span>Email</span><input name="email" type="email" value="bad"></label><label><span>Quantity</span><input name="quantity" type="number" min="1" value="0"></label><label hidden><input name="conditional" required></label><button>Save</button></form>`,lang);
    await page.locator('button').click();
    await expect(page.locator('[name=name]')).toBeFocused();
    await expect(page.locator('[aria-invalid=true]')).toHaveCount(3);
    await expect(page.locator('[name=conditional]')).not.toHaveAttribute('aria-invalid','true');
    await expect(page.locator('[name=conditional]')).toBeHidden();
    await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'correo':'email');
    await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'mayor o igual a 1':'at least 1');
  });
  test(`${lang}: movement business causes are specific`, async ({page}) => {
    await setup(page,`<form id="movementForm"><label><span>Unit</span><input name="unit" value="H87"></label><label><span>Item</span><input name="itemId" value="item-1"></label><label><span>Warehouse</span><input name="warehouseId" value="warehouse-1"></label></form>`,lang);
    await reject(page,[],{code:'movement_unit_must_match_item_base_unit',status:409});
    await expect(page.locator('[name=unit]')).toHaveAttribute('aria-invalid','true');
    await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'unidad base':'base unit');
    await reject(page,[],{code:'movement_reference_inactive',status:409});
    await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'inactivo':'inactive');
    await expect(page.locator('[name=unit]')).not.toHaveAttribute('aria-invalid','true');
  });
}
test('untrusted issue text and correlation reference cannot execute markup',async({page})=>{
  await setup(page,reasonForm);
  await reject(page,[{loc:['body','server_only'],type:'missing',msg:'<img src=x onerror="window.injected=true">'}],{correlationId:'<img src=x onerror="window.injected=true">'});
  await expect(page.locator('img')).toHaveCount(0);
  expect(await page.evaluate(()=>window.injected)).toBeUndefined();
});
test('request ownership stays with originating form and ignores closed forms',async({page})=>{
  await setup(page,`<form id="one"><input name="reason" value="one"><button>Save one</button></form><form id="two"><input name="reason" value="two"><button>Save two</button></form>`);
  await page.evaluate(()=>document.querySelector('#one').addEventListener('submit',()=>{const detail={path:'/no-network',body:{reason:'one'}};window.dispatchEvent(new CustomEvent(window.feedback.FORM_REQUEST_EVENT,{detail}));window.firstContext=detail.context;}));
  await page.locator('#one button').click();
  await page.locator('#two button').click();
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent(window.feedback.FORM_ERROR_EVENT,{detail:{code:'validation_failed',details:{issues:[{loc:['body','reason'],type:'missing'}]},formContext:window.firstContext}})));
  await expect(page.locator('#one [name=reason]')).toHaveAttribute('aria-invalid','true');
  await expect(page.locator('#two [aria-invalid=true]')).toHaveCount(0);
  await page.evaluate(()=>{document.querySelector('#one').remove();window.dispatchEvent(new CustomEvent(window.feedback.FORM_ERROR_EVENT,{detail:{code:'validation_failed',details:{issues:[{loc:['body','reason'],type:'missing'}]},formContext:window.firstContext}}));});
  await expect(page.locator('#two [aria-invalid=true]')).toHaveCount(0);
  await expect(page.locator('#two [name=reason]')).toHaveValue('two');
});
test('explicit array bindings target second line and never the first',async({page})=>{
  await setup(page,`<form id="salesQuoteForm"><div data-quote-line><label><span>First</span><input name="lineQuantity" value="1"></label></div><div data-quote-line><label><span>Second</span><input name="lineQuantity" value="0"></label></div></form>`);
  await page.evaluate(()=>{const form=document.querySelector('form');const context={bindings:window.bindings.captureFormBindings(form,{body:{lines:[{quantity:1},{quantity:0}]}})};window.feedback.renderFormFeedback(form,[{code:'validation_failed',details:{issues:[{loc:['body','lines',1,'quantity'],type:'greater_than',ctx:{gt:0}}]},formContext:context}]);});
  await expect(page.locator('[name=lineQuantity]').nth(0)).not.toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[name=lineQuantity]').nth(1)).toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[name=lineQuantity]').nth(1)).toBeFocused();
});
test('receipt binding follows submitted line identity after zero quantities are filtered',async({page})=>{
  await setup(page,`<form id="purchasingReceiptForm">${['first','second','third'].map((id,i)=>`<div class="purchasing-requisition-line" data-receipt-line data-line-id="${id}" data-remaining="10"><label class="preview-field"><span>Received quantity</span><input name="quantity" type="number" min="0" max="10" step="any" value="${i===1?5:0}"></label><label class="preview-field"><span>Warehouse</span><select name="warehouse_id"><option value="wh">WH</option></select></label></div>`).join('')}</form>`);
  await page.evaluate(()=>{const form=document.querySelector('form');const bindings=window.bindings.captureFormBindings(form,{body:JSON.stringify({lines:[{order_line_id:'second',quantity:5,warehouse_id:'wh'}]})});window.feedback.renderFormFeedback(form,[{details:{issues:[{loc:['body','lines',0,'quantity'],type:'less_than_equal',ctx:{le:4}}]},formContext:{bindings}}]);});
  await expect(page.locator('[data-line-id=second] input')).toBeFocused();
  await expect(page.locator('[data-line-id=first] input')).not.toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[data-line-id=third] input')).not.toHaveAttribute('aria-invalid','true');
});
test('recipe resources use identity and selected stage weight uses area identity',async({page})=>{
  await setup(page,`<form id="recipeForm"><div class="selected-resource-row" data-resource-row="r1"><input name="resource_r1" value="1"></div><div class="selected-resource-row" data-resource-row="r2"><input name="resource_r2" value="2"></div><label class="recipe-area-option"><input type="checkbox" name="stageAreaId" value="a1"><input data-stage-weight value=""></label><label class="recipe-area-option"><input type="checkbox" name="stageAreaId" value="a2" checked><input data-stage-weight value="100"></label></form>`);
  const result=await page.evaluate(()=>{const form=document.querySelector('form');const b=window.bindings.captureFormBindings(form,{body:{resources:[{resource_ref_id:'r2',quantity:2},{resource_ref_id:'r1',quantity:1}],stages:[{labor_area_ref_id:'a2',weight_percent:100}]}});return {first:b['resources.0.quantity']?.name,second:b['resources.1.quantity']?.name,stage:b['stages.0.weight_percent']?.closest('label').querySelector('[name=stageAreaId]').value,unknown:b['stages.1.weight_percent']===undefined};});
  expect(result).toEqual({first:'resource_r2',second:'resource_r1',stage:'a2',unknown:true});
});
test('customer nested contact and corporate setting paths resolve their visible fields',async({page})=>{
  await setup(page,`<form id="salesCustomerForm"><label><span>Email</span><input name="contactEmail" value="customer"></label></form><form data-form="admin-update-corporate"><label><span>Commercial name</span><input name="commercial_name" value="company"></label></form>`);
  const result=await page.evaluate(()=>{const customer=document.querySelector('#salesCustomerForm'),corporate=document.querySelector('[data-form]');const a=window.bindings.captureFormBindings(customer,{body:{primary_contact:{email:'customer'}}});const b=window.bindings.captureFormBindings(corporate,{body:{value:{corporate:{commercial_name:'company'}}}});return {email:a['primary_contact.email']?.name,name:b['value.corporate.commercial_name']?.name,unknown:a['primary_contact.uneditable']===undefined};});
  expect(result).toEqual({email:'contactEmail',name:'commercial_name',unknown:true});
});
test('explicit binding wins and declared missing fields remain correctable',async({page})=>{
  await setup(page,`<form id="movementForm"><input name="reason" value="wrong"><input name="selectedReason" value="correct" data-error-path="reason server_only"></form>`);
  const result=await page.evaluate(()=>{const b=window.bindings.captureFormBindings(document.querySelector('form'),{body:{reason:'correct'}});return {reason:b.reason?.name,missing:b.server_only?.name,unknown:b.undeclared===undefined};});
  expect(result).toEqual({reason:'selectedReason',missing:'selectedReason',unknown:true});
});

// Registered-form contract fixtures use names observed in source templates.
// They prove feedback routing/binding behavior, not complete rendered submit flows or UAT.
const registeredFormCases = [
  ["productionServiceEvidenceForm", "startDescription"],
  [
    "standardReportForm",
    null
  ],
  [
    "admin-invite-user",
    "display_name"
  ],
  [
    "admin-create-role",
    "code"
  ],
  [
    "admin-update-corporate",
    "commercial_name"
  ],
  [
    "admin-create-legal-entity",
    "legal_name"
  ],
  [
    "admin-create-branch",
    "name"
  ],
  [
    "admin-code-sequence",
    "prefix"
  ],
  [
    "admin-create-unit",
    "code"
  ],
  [
    "admin-create-commercial-item",
    "code"
  ],
  [
    "admin-document-template",
    "primary_color"
  ],
  [
    "maintenanceTimeModalForm",
    "time_notes"
  ],
  [
    "maintenanceActionForm",
    "diagnosis"
  ],
  [
    "maintenanceOrderForm",
    "code"
  ],
  [
    "maintenanceMaterialForm",
    "order_id"
  ],
  [
    "maintenanceTimeForm",
    "order_id"
  ],
  [
    "purchasingCancellationForm",
    "reason"
  ],
  [
    "purchasingSupplierForm",
    "tax_id"
  ],
  [
    "purchasingRequisitionForm",
    "code"
  ],
  [
    "purchasingOrderForm",
    "code"
  ],
  [
    "purchasingReceiptForm",
    "code"
  ],
  [
    "serviceOrderPlanForm",
    "scheduled_start_at"
  ],
  [
    "serviceOrderTimeForm",
    "worker_id"
  ],
  [
    "serviceOrderCostForm",
    "cost_type"
  ],
  [
    "serviceOrderEvidenceForm",
    "reference"
  ],
  [
    "serviceTransitionForm",
    "responsible_worker_id"
  ],
  [
    "warehouseProductionIssueForm",
    null
  ],
  [
    "warehousePartsIssueForm",
    "reason"
  ],
  [
    "genericRecordForm",
    "status"
  ],
  [
    "warehouseForm",
    "code"
  ],
  [
    "inventoryItemForm",
    "code"
  ],
  [
    "movementForm",
    "movementType"
  ],
  [
    "salesCustomerForm",
    "code"
  ],
  [
    "salesQuoteForm",
    "code"
  ],
  [
    "finishedGoodsReceiptForm",
    "quantity"
  ],
  [
    "salesOrderForm",
    "code"
  ],
  [
    "salesOrderEditForm",
    "code"
  ],
  [
    "salesDeliveryForm",
    "code"
  ],
  [
    "productServiceForm",
    "kind"
  ],
  [
    "laborAreaForm",
    "code"
  ],
  [
    "salesOrderFulfillmentForm",
    "cancelReason"
  ],
  [
    "adminUnitForm",
    "name_es"
  ],
  [
    "laborRoleForm",
    "position"
  ],
  [
    "workerForm",
    "employee_number"
  ],
  [
    "machineForm",
    "code"
  ],
  [
    "recipeForm",
    "code"
  ],
  [
    "orderForm",
    "code"
  ],
  [
    "order-stage-progress",
    "progressPercent"
  ],
  [
    "auth-email",
    "email"
  ],
  [
    "operational-handoff-dialog",
    "reason"
  ],
  [
    "login",
    "email"
  ],
  [
    "tenant-onboarding",
    "commercial_name"
  ],
  [
    "tenant-search",
    "search"
  ],
  [
    "usage-search",
    "from_date"
  ],
  [
    "tenant-editor",
    "commercial_name"
  ]
];
for (const [key, name] of registeredFormCases) {
  test(`registered form ${key}: field or noneditable requirement preserves its draft`, async ({page}) => {
    await setup(page, `<form id="${key}" data-form="${key}">${name ? `<label><span>Captured value</span><input name="${name}" value="draft"></label>` : ''}</form>`);
    await page.evaluate(({key,name}) => {
      const form=document.getElementById(key), field=name || 'server_only';
      const captured=window.bindings.captureFormBindings(form,{body:{[field]:'draft'}});
      window.feedback.renderFormFeedback(form,[{code:'validation_failed',details:{issues:[{loc:['body',field],type:'missing'}]},formContext:{bindings:captured}}]);
    },{key,name});
    if(name){
      await expect(page.locator('input')).toHaveValue('draft');
      await expect(page.locator('input')).toHaveAttribute('aria-invalid','true');
      await expect(page.locator('input')).toBeFocused();
      await expect(page.locator('.form-error-link')).toHaveCount(1);
    } else {
      await expect(page.locator('[aria-invalid=true]')).toHaveCount(0);
      await expect(page.locator('[data-form-feedback]')).toContainText('soporte');
    }
  });
}
test('hidden item ID resolves visible lookup while unrelated hidden field stays general',async({page})=>{
  await setup(page,`<form id="movementForm"><label class="preview-field entity-lookup"><span>Item</span><input name="itemId" type="hidden" value="item-1"><input id="movementItemSearch" name="item" value="Camera"></label><label hidden><input name="destinationWarehouseId" value="wh-2"></label></form>`);
  await page.evaluate(()=>{const form=document.querySelector('form');const bindings=window.bindings.captureFormBindings(form,{body:{inventory_item_id:'item-1',destination_warehouse_id:'wh-2'}});window.feedback.renderFormFeedback(form,[{details:{issues:[{loc:['body','inventory_item_id'],type:'missing'},{loc:['body','destination_warehouse_id'],type:'missing'}]},formContext:{bindings}}]);});
  await expect(page.locator('#movementItemSearch')).toBeFocused();
  await expect(page.locator('#movementItemSearch')).toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[name=itemId]')).not.toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[name=destinationWarehouseId]')).not.toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[data-form-feedback]')).toContainText('soporte');
});
for (const lang of ['es','en']) {
  test(`${lang}: permission and technical errors never blame an arbitrary field`,async({page})=>{
    await setup(page,reasonForm,lang);
    for(const status of [403,500]){
      await reject(page,[],{code:'unrecognized_test_code',status,message:'reason database password token unsafe'});
      await expect(page.locator('[aria-invalid=true]')).toHaveCount(0);
      await expect(page.locator('[data-form-feedback]')).not.toContainText('database password');
      await expect(page.locator('[name=reason]')).toHaveValue('ok');
      await expect(page.locator('[data-form-feedback]')).toBeVisible();
    }
  });
}

test('missing quantity in a submitted array member resolves its explicit row',async({page})=>{
  await setup(page,`<form id="salesQuoteForm"><div data-quote-line><label><span>First</span><input name="lineQuantity" value="2"></label></div><div data-quote-line><label><span>Second</span><input name="lineQuantity" value=""></label></div></form>`);
  await page.evaluate(()=>{const form=document.querySelector('form');const bindings=window.bindings.captureFormBindings(form,{body:{lines:[{quantity:2},{}]}});window.feedback.renderFormFeedback(form,[{details:{issues:[{loc:['body','lines',1,'quantity'],type:'missing'}]},formContext:{bindings}}]);});
  await expect(page.locator('[name=lineQuantity]').nth(0)).not.toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[name=lineQuantity]').nth(1)).toHaveAttribute('aria-invalid','true');
  await expect(page.locator('[name=lineQuantity]').nth(1)).toBeFocused();
  await expect(page.locator('[data-field-error]')).toHaveText('Completa este campo.');
});

test('reviewer: interaction without request expires before unrelated work',async({page})=>{
  await setup(page,reasonForm);
  await page.locator('[name=reason]').click();
  await expect.poll(()=>page.evaluate(()=>window.feedback.getActiveFeedbackForm()===null)).toBe(true);
  const owned=await page.evaluate(()=>{const detail={path:'/unrelated',body:{reason:'other'}};window.dispatchEvent(new CustomEvent(window.feedback.FORM_REQUEST_EVENT,{detail}));return Boolean(detail.context);});
  expect(owned).toBe(false);
});
test('reviewer: late rejection keeps current edits without marking them invalid',async({page})=>{
  await setup(page,reasonForm);
  await page.evaluate(()=>document.querySelector('form').addEventListener('submit',()=>{const detail={path:'/fixture',body:{reason:'ok'}};window.dispatchEvent(new CustomEvent(window.feedback.FORM_REQUEST_EVENT,{detail}));window.pendingContext=detail.context;}));
  await page.locator('button').click();
  expect(await page.evaluate(()=>Boolean(window.pendingContext?.values))).toBe(true);
  await page.locator('[name=reason]').fill('corrected during request');
  await page.evaluate(()=>{window.dispatchEvent(new CustomEvent(window.feedback.FORM_ERROR_EVENT,{detail:{status:422,code:'validation_failed',details:{issues:[{loc:['body','reason'],type:'string_too_short',ctx:{min_length:3}}]},formContext:window.pendingContext}}));window.dispatchEvent(new CustomEvent(window.feedback.FORM_COMPLETE_EVENT,{detail:window.pendingContext}));});
  await expect(page.locator('[name=reason]')).toHaveValue('corrected during request');
  await expect(page.locator('[aria-invalid=true]')).toHaveCount(0);
  await expect(page.locator('[data-form-feedback]')).toContainText('valores anteriores');
  await expect.poll(()=>page.evaluate(()=>window.feedback.getActiveFeedbackForm()===null)).toBe(true);
});
test('reviewer: known RFC validation uses safe localized rule',async({page})=>{
  await setup(page,`<form id="workerForm"><label><span>RFC</span><input name="rfc" value="bad"></label></form>`);
  await reject(page,[{loc:['body','rfc'],type:'value_error',msg:'Value error, invalid_rfc'}],{},'workerForm');
  await expect(page.locator('[name=rfc]')).toBeFocused();
  await expect(page.locator('[data-field-error]')).toContainText('RFC');
  await expect(page.locator('[data-field-error]')).toContainText('homoclave');
  await expect(page.locator('[data-form-feedback]')).not.toContainText('invalid_rfc');
});
test('reviewer: root stock limit rule identifies both fields',async({page})=>{
  await setup(page,`<form id="inventoryItemForm"><label><span>Minimum</span><input name="minStock" value="10"></label><label><span>Maximum</span><input name="maxStock" value="5"></label></form>`);
  await reject(page,[{loc:['body'],type:'value_error',msg:'Value error, maximum_stock_must_be_greater_than_or_equal_to_minimum_stock'}],{},'inventoryItemForm');
  await expect(page.locator('[aria-invalid=true]')).toHaveCount(2);
  await expect(page.locator('[name=minStock]')).toBeFocused();
  await expect(page.locator('[data-form-feedback]')).toContainText('mayor o igual');
});
test('reviewer: undeclared Pydantic message cannot expose diagnostic',async({page})=>{
  await setup(page,reasonForm);
  await reject(page,[{loc:['body','reason'],type:'value_error',msg:'Value error, backend-secret-url-token-123'}]);
  await expect(page.locator('[data-form-feedback]')).not.toContainText('backend-secret');
  await expect(page.locator('[name=reason]')).toHaveAttribute('aria-invalid','true');
});
test('reviewer: programmatic invalid validation expires without owning later requests',async({page})=>{
  await setup(page,`<form id="movementForm"><label><span>Reason</span><input name="reason" required></label></form>`);
  await page.evaluate(()=>document.querySelector('form').reportValidity());
  await expect(page.locator('[name=reason]')).toHaveAttribute('aria-invalid','true');
  await expect.poll(()=>page.evaluate(()=>window.feedback.getActiveFeedbackForm()===null)).toBe(true);
});
test('reviewer: removed line marks late validation as old draft',async({page})=>{
  await setup(page,`<form id="salesQuoteForm"><div data-quote-line><input name="lineQuantity" value="1"></div><div data-quote-line><input name="lineQuantity" value="0"></div><button>Save</button></form>`);
  await page.evaluate(()=>document.querySelector('form').addEventListener('submit',()=>{const detail={body:{lines:[{quantity:1},{quantity:0}]}};window.dispatchEvent(new CustomEvent(window.feedback.FORM_REQUEST_EVENT,{detail}));window.pendingContext=detail.context;}));
  await page.locator('button').click();
  await page.evaluate(()=>{document.querySelectorAll('[data-quote-line]')[1].remove();window.dispatchEvent(new CustomEvent(window.feedback.FORM_ERROR_EVENT,{detail:{status:422,details:{issues:[{loc:['body','lines',1,'quantity'],type:'greater_than',ctx:{gt:0}}]},formContext:window.pendingContext}}));window.dispatchEvent(new CustomEvent(window.feedback.FORM_COMPLETE_EVENT,{detail:window.pendingContext}));});
  await expect(page.locator('[data-form-feedback]')).toContainText('valores anteriores');
  await expect(page.locator('[aria-invalid=true]')).toHaveCount(0);
  await expect(page.locator('input')).toHaveValue('1');
});

for (const lang of ['es','en']) {
  test(`${lang}: historical base unit and recipe machine conflicts retain actionable copy`, async ({page}) => {
    await setup(page, '<form id="movementForm"><label><span>Unit</span><input name="unit" value="H87"></label></form>', lang);
    await reject(page, [], {code:'item_base_unit_locked_by_movements',status:409});
    await expect(page.locator('[name=unit]')).toHaveAttribute('aria-invalid','true');
    await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'artículo sustituto':'replacement item');
    await reject(page, [], {code:'machine_resource_invalid',status:409});
    await expect(page.locator('[aria-invalid=true]')).toHaveCount(0);
    await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'estado y área':'status and area');
  });
}

for (const lang of ['es','en']) {
  test(`${lang}: lookup custom validity asks for a selected result`, async ({page}) => {
    await setup(page, '<form><label><span>Item</span><span class="entity-select-lookup"><input name="search" value="typed"></span></label><button>Save</button></form>', lang);
    await page.locator('[name=search]').evaluate(input => input.setCustomValidity('Private diagnostic'));
    await page.locator('button').click();
    await expect(page.locator('[data-field-error]')).toHaveText(lang==='es'?'Selecciona un resultado de la lista.':'Select a result from the list.');
    await expect(page.locator('[name=search]')).toBeFocused();
  });
}
