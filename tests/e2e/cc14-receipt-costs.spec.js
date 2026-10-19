const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
const tenant='ten_739ee59d765d5e14818674800d';

async function setup(page,lang,{currency='USD',physical=true}={}){
  const calls=[];
  const app=fs.readFileSync(path.join(__dirname,'../../frontend/app.js'),'utf8');
  if(!/^initializeAuth\(\);\r?\nrender\(\);/m.test(app))throw new Error('App bootstrap changed');
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url());
    if(url.origin!==origin)return route.abort();
    if(url.pathname==='/env.js')return route.fulfill({contentType:'text/javascript',body:'window.ERCLAVE_CONFIG='+JSON.stringify({apiMode:'api',localPurchasingApiBaseUrl:origin})});
    if(url.pathname==='/app.js')return route.fulfill({contentType:'text/javascript',body:app.replace(/^initializeAuth\(\);\r?\nrender\(\);/m,'// Browser fixture intercepts bootstrap; no authentication/network services.')+'\nwindow.cc14Receipt={state,modules,renderPurchasingSubmodulePanel};'});
    if(req.method()==='POST'){
      calls.push({path:url.pathname,payload:req.postDataJSON(),key:req.headers()['idempotency-key']});
      return route.fulfill({status:422,json:{error:{code:'validation_error',message:'PRIVATE SERVER DIAGNOSTIC',details:{issues:[{loc:['body','cost_exchange_rate'],msg:'PRIVATE SERVER DIAGNOSTIC',type:'value_error'}]}}}});
    }
    if(url.pathname.startsWith('/v1/'))return route.fulfill({json:{data:[]}});
    return route.continue();
  });
  await page.addInitScript(()=>{localStorage.clear();localStorage.setItem('erclave-api-mode','api');});
  await page.goto(origin+'/');await page.waitForFunction(()=>window.cc14Receipt);
  await page.evaluate(({lang,currency,physical,tenant})=>{
    const {state,modules,renderPurchasingSubmodulePanel}=window.cc14Receipt;
    state.lang=lang;state.active='compras';state.activeSubmodule='recepciones';
    state.sessionApi={status:'ready',data:{tenant:{id:tenant},permissions:['purchasing.receipt.create'],scope:{version:2,divisions:[{id:'div-mxn',society_id:'soc-mxn'},{id:'div-usd',society_id:'soc-usd'},{id:'div-eur',society_id:'soc-eur'}],societies:[{id:'soc-mxn',base_currency:'EUR'},{id:'soc-usd',base_currency:'USD'},{id:'soc-eur',base_currency:'EUR'}]}}};
    state.purchasingReceiptSourceOrderId='order';
    state.purchasingApi={...state.purchasingApi,status:'ready',receipts:[],requisitions:[],suppliers:[],orders:[{id:'order',code:'PO-SYNTHETIC',organization_context:{division_ref_id:'div-mxn',society_ref_id:'soc-mxn',cost_currency:'MXN'},currency,status:'issued',lines:[{id:'line',line_type:physical?'inventory_item':'service',description:'Synthetic receipt line',quantity:10,received_quantity:0,unit_code:'H87'}]}],warehouses:[{id:'wh-mxn',code:'MXN-WH',name:'MXN warehouse',status:'active',division_ref_id:'div-mxn'},{id:'wh-usd',code:'USD-WH',name:'USD warehouse',status:'active',division_ref_id:'div-usd'},{id:'wh-eur',code:'EUR-WH',name:'EUR warehouse',status:'active',division_ref_id:'div-mxn'}]};
    renderPurchasingSubmodulePanel(modules.find(m=>m.id==='compras'));
  },{lang,currency,physical,tenant});
  const form=page.locator('#purchasingReceiptForm');
  await expect(form).toBeVisible();
  await form.locator('[name=code]').fill('REC-SYNTHETIC');
  await form.locator('[name=supplier_document_reference]').fill('SUPPLIER-KEEP');
  await form.locator('[name=quantity]').fill('2');
  return {form,calls};
}

for(const lang of ['es','en']){
  test(`CC14 ${lang} receipt conversion requires explicit rate and preserves rejected capture`,async({page})=>{
    const {form,calls}=await setup(page,lang);
    const rate=form.locator('[name=cost_exchange_rate]');
    await form.locator('[name=warehouse_id]').selectOption('wh-mxn');
    await expect(rate).toBeVisible();await expect(rate).toHaveAttribute('required','');
    await expect(form.locator('#receipt-cost-help')).toContainText('1 USD');
    await expect(form.locator('#receipt-cost-help')).toContainText('MXN');
    await form.locator('[type=submit]').click();expect(calls).toHaveLength(0);
    await rate.fill('17.123456');await form.locator('[type=submit]').click();
    await expect.poll(()=>calls.length).toBe(1);
    expect(calls[0].payload.cost_exchange_rate).toBe('17.123456');
    expect(calls[0].payload.lines[0]).toMatchObject({order_line_id:'line',warehouse_id:'wh-mxn',quantity:2});
    await expect(rate).toHaveAttribute('aria-invalid','true');
    await expect(rate).toHaveAttribute('aria-describedby',/receipt-cost-help/);
    await expect(rate).toHaveAttribute('aria-describedby',/field-error-/);
    await expect(rate).toBeFocused();await expect(rate).toHaveValue('17.123456');
    await expect(form.locator('[name=supplier_document_reference]')).toHaveValue('SUPPLIER-KEEP');
    await expect(form.locator('[name=warehouse_id]')).toHaveValue('wh-mxn');
    await expect(form.locator('[name=quantity]')).toHaveValue('2');
    await expect(form).not.toContainText('PRIVATE SERVER DIAGNOSTIC');
    await form.locator('[type=submit]').click();await expect.poll(()=>calls.length).toBe(2);
    expect(calls[1].key).toBe(calls[0].key);
    expect(calls[1].payload).toEqual(calls[0].payload);
    await rate.fill('18.000001');await form.locator('[type=submit]').click();
    await expect.poll(()=>calls.length).toBe(3);
    expect(calls[2].key).not.toBe(calls[1].key);
    expect(calls[2].payload.cost_exchange_rate).toBe('18.000001');
  });
  test(`CC14 ${lang} same-currency receipt rate is readonly one`,async({page})=>{
    const {form,calls}=await setup(page,lang,{currency:'MXN'});
    await form.locator('[name=warehouse_id]').selectOption('wh-mxn');
    const rate=form.locator('[name=cost_exchange_rate]');
    await expect(rate).toHaveValue('1');await expect(rate).toHaveAttribute('readonly','');
    await form.locator('[type=submit]').click();await expect.poll(()=>calls.length).toBe(1);
    expect(calls[0].payload.cost_exchange_rate).toBe('1');
  });
  test(`CC14 ${lang} services omit conversion and warehouse change clears captured rate`,async({page})=>{
    const {form,calls}=await setup(page,lang);
    const rate=form.locator('[name=cost_exchange_rate]');
    await form.locator('[name=warehouse_id]').selectOption('wh-mxn');await rate.fill('17.123456');
    await form.locator('[name=warehouse_id]').selectOption('wh-eur');
    await expect(rate).toHaveValue('');await expect(rate).toHaveAttribute('required','');
    await expect(form.locator('#receipt-cost-help')).toContainText('MXN');
    await form.locator('[type=submit]').click();expect(calls).toHaveLength(0);
    await page.evaluate(()=>{const a=window.cc14Receipt;a.state.purchasingApi.orders[0].lines[0].line_type='service';a.renderPurchasingSubmodulePanel(a.modules.find(m=>m.id==='compras'));});
    const service=page.locator('#purchasingReceiptForm');
    await expect(service.locator('[name=cost_exchange_rate]')).toBeHidden();
    await expect(service.locator('[name=cost_exchange_rate]')).toBeDisabled();
    await service.locator('[name=code]').fill('REC-SERVICE');await service.locator('[name=quantity]').fill('1');
    await service.locator('[type=submit]').click();await expect.poll(()=>calls.length).toBe(1);
    expect(calls[0].payload).not.toHaveProperty('cost_exchange_rate');
  });
}
