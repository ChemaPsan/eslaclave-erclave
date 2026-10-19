const {test,expect}=require('@playwright/test');
const fs=require('node:fs'),path=require('node:path');
const origin='http://127.0.0.1:'+(process.env.ERCLAVE_FORM_TEST_PORT||4183);
const tenant='ten_739ee59d765d5e14818674800d';
const context=id=>({division_ref_id:'div-'+id,society_ref_id:'soc-'+id,division_code:id.toUpperCase(),division_name:'Division '+id.toUpperCase(),cost_currency:id==='a'?'MXN':'USD'});

async function setup(page,lang,{screen='requisiciones',editing=false,legacy=false}={}){
  const calls=[],reads=[];let rejectField=screen==='requisiciones'?'division_ref_id':'supplier_id',rejectCode='validation_error';
  const app=fs.readFileSync(path.join(__dirname,'../../frontend/app.js'),'utf8');
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url());if(url.origin!==origin)return route.abort();
    if(url.pathname==='/env.js')return route.fulfill({contentType:'text/javascript',body:'window.ERCLAVE_CONFIG='+JSON.stringify({apiMode:'api',localPurchasingApiBaseUrl:origin,localInventoryApiBaseUrl:origin})});
    if(url.pathname==='/app.js')return route.fulfill({contentType:'text/javascript',body:app.replace(/^initializeAuth\(\);\r?\nrender\(\);/m,'// Isolated CC15 browser fixture.')+'\nwindow.cc15={state,modules,renderPurchasingSubmodulePanel};'});
    if(['POST','PATCH','PUT'].includes(req.method())){
      calls.push({path:url.pathname,payload:req.postDataJSON(),key:req.headers()['idempotency-key']});
      return route.fulfill({status:rejectCode==='validation_error'?422:409,json:{error:{code:rejectCode,message:'PRIVATE SERVER',details:{field:rejectField,issues:[{loc:['body',...rejectField.split('.')],type:'value_error',msg:'PRIVATE SERVER'}]}}}});
    }
    if(url.pathname.startsWith('/v1/'))reads.push(url.pathname+url.search);
    if(url.pathname.endsWith('/document-divisions')){
      const rows=['a','b'].map(id=>({id:'div-'+id,code:id.toUpperCase(),name:'Division '+id.toUpperCase(),society_id:'soc-'+id,cost_currency:id==='a'?'MXN':'USD'}));
      return route.fulfill({json:{data:rows.filter(row=>!url.searchParams.get('q')||row.name.includes(url.searchParams.get('q'))),meta:{total:2,limit:20,offset:0}}});
    }
    if(url.pathname.endsWith('/document-suppliers')){
      const d=url.searchParams.get('division_id');const rows=[{id:'supplier-'+d,code:'SUP-'+d,name:'Supplier '+d,division_ref_id:d,society_ref_id:d.replace('div','soc'),commercial_terms:{values:{currency:'USD',payment_terms:'net30',lead_time_days:7},revision:3}}];
      return route.fulfill({json:{data:rows,meta:{total:1,limit:20,offset:0}}});
    }
    if(url.pathname.endsWith('/division-items')){
      const d=url.searchParams.get('division_id');return route.fulfill({json:{data:[{id:'item-'+d,code:'IT-'+d,name:'Item '+d,base_unit:'H87',division_ref_id:d}],meta:{total:1,limit:20,offset:0}}});
    }
    if(url.pathname.startsWith('/v1/'))return route.fulfill({json:{data:[]}});
    return route.continue();
  });
  await page.addInitScript(()=>{localStorage.clear();localStorage.setItem('erclave-api-mode','api');});
  await page.goto(origin+'/');await page.waitForFunction(()=>window.cc15);
  await page.evaluate(({lang,screen,editing,legacy,tenant,contexts})=>{
    const a=window.cc15,s=a.state;s.lang=lang;s.active='compras';s.activeSubmodule=screen;
    s.unitCatalog={status:'ready',data:[{code:'H87',name_en:'Piece',name_es:'Pieza',symbol:'pc',status:'active'},{code:'C62',name_en:'Unit',name_es:'Unidad',symbol:'u',status:'active'}]};
    s.sessionApi={status:'ready',data:{tenant:{id:tenant},permissions:['purchasing.requisition.create','purchasing.requisition.update','purchasing.order.create','purchasing.order.update','purchasing.receipt.create','inventory.item.read'],scope:{version:2,divisions:contexts.map(c=>({id:c.division_ref_id,code:c.division_code,name:c.division_name,society_id:c.society_ref_id})),societies:[{id:'soc-a',base_currency:'EUR'},{id:'soc-b',base_currency:'USD'}]}}};
    const line={id:'line',line_type:'inventory_item',inventory_item_ref_id:'item-div-a',description:'Keep captured item',quantity:'999999999999.123456',unit_code:'H87',unit_price:'12.34'};
    const requisitions=contexts.map((c,i)=>({id:'req-'+i,code:'REQ-'+i,required_date:'2099-01-01',priority:'normal',status:editing&&screen==='requisiciones'?'draft':'approved',organization_context:legacy?null:c,lines:[line]}));
    const order={id:'order',code:'PO-HISTORY',status:'draft',supplier_id:'supplier-div-a',supplier_name_snapshot:'Historical supplier',requisition_id:'req-0',organization_context:legacy?null:contexts[0],commercial_terms_snapshot:{supplier_id:'supplier-div-a',terms_revision:1,values:{currency:'MXN',payment_terms:'cash',lead_time_days:2}},lines:[line]};
    s.purchasingApi={...s.purchasingApi,status:'ready',requisitions,orders:editing&&screen==='ordenes-de-compra'?[order]:[],suppliers:[],receipts:[],items:[{id:'item-div-a',code:'IT-A',name:'Keep captured item',base_unit:'H87'}],warehouses:[]};
    s.purchasingRequisitionEditId=editing&&screen==='requisiciones'?'req-0':'';s.purchasingOrderEditId=editing&&screen==='ordenes-de-compra'?'order':'';s.purchasingOrderSourceRequisitionId=screen==='ordenes-de-compra'?'req-0':'';
    a.renderPurchasingSubmodulePanel(a.modules.find(m=>m.id==='compras'));
  },{lang,screen,editing,legacy,tenant,contexts:[context('a'),context('b')]});
  return {calls,reads,reject:(field,code='validation_error')=>{rejectField=field;rejectCode=code;}};
}

for(const lang of ['es','en']){
  test(`CC15 ${lang} compact real Purchasing panel keeps scoped controls within 320px`,async({page})=>{
    for(const screen of ['requisiciones','ordenes-de-compra']){
      await setup(page,lang,{screen});
      await page.locator('#modulePanel').evaluate(panel=>{panel.style.width='320px';panel.style.maxWidth='320px';panel.style.minWidth='0';panel.style.boxSizing='border-box';});
      const form=page.locator(screen==='requisiciones'?'#purchasingRequisitionForm':'#purchasingOrderForm');
      await expect(form.locator(screen==='requisiciones'?'[name=division_ref_id]':'[name=supplier_id]')).toBeEnabled();
      expect(await page.locator('#modulePanel').evaluate(panel=>Math.round(panel.getBoundingClientRect().width))).toBe(320);
      const overflow=await form.evaluate(form=>({width:form.clientWidth,scroll:form.scrollWidth,children:[...form.querySelectorAll('*')].filter(el=>el.getBoundingClientRect().right>form.getBoundingClientRect().right+1).map(el=>({tag:el.tagName,class:el.className,name:el.name,width:el.getBoundingClientRect().width})).slice(0,12)}));
      expect(overflow.scroll,JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.width+1);
      expect(await form.locator('[data-purchasing-query]').first().evaluate(control=>control.getBoundingClientRect().right<=control.closest('form').getBoundingClientRect().right+1)).toBe(true);
      expect(await form.locator('[hidden]').evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).display==='none'))).toBe(true);
    }
  });
  test(`CC15 ${lang} requisition uses eligible Division and items; rejection preserves exact draft`,async({page})=>{
    const run=await setup(page,lang),form=page.locator('#purchasingRequisitionForm');
    await expect(form.locator('[name=division_ref_id] option[value=div-a]')).toHaveCount(1);
    await form.locator('[name=division_ref_id]').selectOption('div-a');
    await expect(form.locator('[name=inventory_item_id] option[value=item-div-a]')).toHaveCount(1);
    await form.locator('[name=inventory_item_id]').selectOption('item-div-a');
    await form.locator('[name=code]').fill('REQ-KEEP');await form.locator('[name=required_date]').fill('2099-01-01');await form.locator('[name=quantity]').fill('999999999999.123456');
    await expect(form.locator('[name=unit_code]')).toHaveValue('H87');
    await form.locator('[type=submit]').click();await expect.poll(()=>run.calls.length).toBe(1);
    expect(run.calls[0].payload).toMatchObject({division_ref_id:'div-a',lines:[{inventory_item_id:'item-div-a',quantity:'999999999999.123456',unit_code:'H87'}]});
    await expect(form.locator('[name=division_ref_id]')).toHaveAttribute('aria-invalid','true');await expect(form.locator('[name=division_ref_id]')).toBeFocused();
    await expect(form.locator('[name=quantity]')).toHaveValue('999999999999.123456');await expect(form.locator('[name=inventory_item_id]')).toHaveValue('item-div-a');await expect(form).not.toContainText('PRIVATE SERVER');
    await form.locator('[type=submit]').click();await expect.poll(()=>run.calls.length).toBe(2);expect(run.calls[1].key).toBe(run.calls[0].key);
    await form.locator('[name=division_ref_id]').selectOption('div-b');await expect(form.locator('[name=inventory_item_id] option[value=item-div-b]')).toHaveCount(1);
    await expect(form.locator('[name=inventory_item_id]')).toHaveValue('');await expect(form.locator('[name=quantity]')).toHaveValue('999999999999.123456');
    expect(run.reads.some(url=>url.includes('division-items?division_id=div-b'))).toBe(true);
  });
  test(`CC15 ${lang} services requisition does not request Inventory; legacy edit stays blocked`,async({page})=>{
    const run=await setup(page,lang),form=page.locator('#purchasingRequisitionForm');
    await form.locator('[name=line_type]').selectOption('service');
    await form.locator('[name=division_ref_id]').selectOption('div-a');
    await form.locator('[name=code]').fill('REQ-SERVICE');await form.locator('[name=required_date]').fill('2099-01-01');await form.locator('[name=quantity]').fill('1');await form.locator('[name=description]').fill('Service capture');
    await form.locator('[type=submit]').click();await expect.poll(()=>run.calls.length).toBe(1);
    expect(run.reads.some(url=>url.includes('/division-items'))).toBe(false);expect(run.calls[0].payload.lines[0].inventory_item_id).toBeNull();
    await setup(page,lang,{editing:true,legacy:true});await expect(page.locator('#purchasingRequisitionForm [type=submit]')).toBeDisabled();
    await expect(page.locator('#purchasingRequisitionForm [name=division_ref_id]')).toHaveAttribute('readonly','');
  });
  test(`CC15 ${lang} purchase order derives terms and resets supplier when requisition changes`,async({page})=>{
    const run=await setup(page,lang,{screen:'ordenes-de-compra'}),form=page.locator('#purchasingOrderForm');
    run.reject('supplier_id','purchasing_document_terms_changed');
    await expect(form.locator('[name=supplier_id] option[value=supplier-div-a]')).toHaveCount(1);
    await form.locator('[name=supplier_id]').selectOption('supplier-div-a');
    await expect(form.locator('[data-purchasing-order-terms]')).toContainText('USD');await expect(form.locator('[data-purchasing-order-terms]')).toContainText('net30');
    await form.locator('[name=code]').fill('PO-KEEP');await form.locator('[data-order-unit-price]').fill('9999999999999999.99');
    await form.locator('[type=submit]').click();await expect.poll(()=>run.calls.length).toBe(1);
    expect(run.calls[0].payload.expected_terms_revision).toBe(3);expect(run.calls[0].payload.lines[0].quantity).toBe('999999999999.123456');
    expect(run.calls[0].payload).not.toHaveProperty('currency');expect(run.calls[0].payload).not.toHaveProperty('payment_terms');expect(run.calls[0].payload.lines[0].unit_price).toBe('9999999999999999.99');
    await expect(form.locator('[name=supplier_id]')).toHaveAttribute('aria-invalid','true');await expect(form.locator('[name=supplier_id]')).toBeFocused();await expect(form.locator('[data-order-unit-price]')).toHaveValue('9999999999999999.99');
    await form.locator('[type=submit]').click();await expect.poll(()=>run.calls.length).toBe(2);expect(run.calls[1].key).toBe(run.calls[0].key);
    await form.locator('[name=requisition_id]').selectOption('req-1');await expect(form.locator('[name=supplier_id] option[value=supplier-div-b]')).toHaveCount(1);await expect(form.locator('[name=supplier_id]')).toHaveValue('');
    await expect(form.locator('[data-order-unit-price]')).toHaveValue('');await expect(form.locator('[data-purchasing-order-terms]')).not.toContainText('net30');
  });
  test(`CC15 ${lang} same supplier edit keeps frozen commercial snapshot`,async({page})=>{
    const run=await setup(page,lang,{screen:'ordenes-de-compra',editing:true});const form=page.locator('#purchasingOrderForm');
    await expect(form.locator('[name=supplier_id]')).toBeEnabled();await expect(form.locator('[data-purchasing-order-terms]')).toContainText('MXN');await expect(form.locator('[data-purchasing-order-terms]')).toContainText('cash');
    await form.locator('[name=supplier_id]').selectOption('supplier-div-a');await expect(form.locator('[data-purchasing-order-terms]')).toContainText('cash');
    await expect(form.locator('[name=requisition_id]')).toBeDisabled();await expect(form.locator('[data-purchasing-order-context]')).toContainText('Division A');
    await form.locator('[type=submit]').click();await expect.poll(()=>run.calls.length).toBe(1);expect(run.calls[0].payload.expected_terms_revision).toBe(1);
  });
  test(`CC15 ${lang} revoked lookup blocks saving and keeps draft`,async({page})=>{
    const run=await setup(page,lang,{screen:'ordenes-de-compra'}),form=page.locator('#purchasingOrderForm');
    await form.locator('[name=supplier_id]').selectOption('supplier-div-a');
    await form.locator('[name=code]').fill('KEEP-REVOKED');await form.locator('[data-order-unit-price]').fill('1.23');
    await page.route('**/document-suppliers?**',route=>route.fulfill({status:403,json:{error:{code:'forbidden',message:'PRIVATE SCOPE'}}}));
    const lookup=form.locator('[name=supplier_id]').locator('..');await lookup.locator('[data-purchasing-search]').click();
    await expect(lookup.locator('[role=alert]')).toBeVisible();await form.locator('[type=submit]').click();
    expect(run.calls).toHaveLength(0);await expect(form.locator('[name=code]')).toHaveValue('KEEP-REVOKED');await expect(form.locator('[data-order-unit-price]')).toHaveValue('1.23');await expect(form).not.toContainText('PRIVATE SCOPE');
  });
  test(`CC15 ${lang} supplier without confirmed terms cannot create order`,async({page})=>{
    const run=await setup(page,lang,{screen:'ordenes-de-compra'}),form=page.locator('#purchasingOrderForm');
    await page.route('**/document-suppliers?**',route=>route.fulfill({json:{data:[{id:'unconfirmed',code:'PENDING',name:'Pending supplier',commercial_terms:{values:null,requires_confirmation:true}}],meta:{total:1}}}));
    await form.locator('[name=requisition_id]').selectOption('req-1');await form.locator('[name=supplier_id]').selectOption('unconfirmed');
    await form.locator('[name=code]').fill('KEEP-TERMS');await form.locator('[data-order-unit-price]').fill('1.23');await form.locator('[type=submit]').click();
    expect(run.calls).toHaveLength(0);await expect(form.locator('[name=supplier_id]')).toHaveValue('unconfirmed');await expect(form.locator('[name=code]')).toHaveValue('KEEP-TERMS');
  });
  test(`CC15 ${lang} previous Division response cannot restore supplier`,async({page})=>{
    await setup(page,lang,{screen:'ordenes-de-compra'});const form=page.locator('#purchasingOrderForm');
    await expect(form.locator('[name=supplier_id]')).toBeEnabled();
    let release;const held=new Promise(resolve=>release=resolve);let started=false;
    await page.route('**/document-suppliers?**',async route=>{
      if(new URL(route.request().url()).searchParams.get('division_id')!=='div-a')return route.fallback();
      started=true;await held;await route.fulfill({json:{data:[{id:'stale',code:'OLD',name:'Old context',commercial_terms:{values:{currency:'EUR'}}}],meta:{total:1}}});
    });
    await form.locator('[name=supplier_id]').locator('..').locator('[data-purchasing-search]').click();await expect.poll(()=>started).toBe(true);
    await form.locator('[name=requisition_id]').selectOption('req-1');await expect(form.locator('[name=supplier_id] option[value=supplier-div-b]')).toHaveCount(1);
    const staleResponse=page.waitForResponse(response=>response.url().includes('/document-suppliers?')&&new URL(response.url()).searchParams.get('division_id')==='div-a');release();await (await staleResponse).finished();
    await expect(form.locator('[name=supplier_id] option[value=stale]')).toHaveCount(0);await expect(form.locator('[name=supplier_id]')).toHaveValue('');
  });
}
