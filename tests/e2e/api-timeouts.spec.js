const { test, expect } = require('@playwright/test');

test.beforeEach(async ({page}) => {
  const origin = new URL(test.info().project.use.baseURL).origin;
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    if(url.origin !== origin) return route.abort();
    if(url.pathname === '/auth.js') return route.fulfill({contentType:'application/javascript',body:'export const getAuthToken=()=>window.testAuth();'});
    if(url.pathname === '/__timeout_fixture') return route.fulfill({contentType:'text/html',body:'<!doctype html><html><body></body></html>'});
    return route.continue();
  });
  await page.goto(origin + '/__timeout_fixture');
  await page.evaluate(async () => {
    window.testAuth = async () => 'fixture-token';
    window.client = await import('/api/client.js');
  });
  await page.clock.install();
});

for(const step of ['auth','headers','json','blob']) {
  test(`35 second budget includes ${step}, with one attempt`, async ({page}) => {
    await page.evaluate(step => {
      window.calls=0; window.done=null;
      const never=()=>new Promise(()=>{});
      if(step==='auth') window.testAuth=never;
      window.fetch=async () => { window.calls++; if(step==='headers') return never(); return {ok:true,status:200,headers:new Headers(),json:never,blob:never}; };
      window.client.apiRequestAt('http://localhost:9999','/v1/test',{method:'POST',...(step==='blob'?{responseType:'blob'}:{})}).then(()=>window.done='unexpected-success',error=>window.done=error.code);
    },step);
    await page.clock.fastForward(35001);
    await expect.poll(()=>page.evaluate(()=>window.done)).toBe('request_timeout');
    expect(await page.evaluate(()=>window.calls)).toBe(step==='auth'?0:1);
  });
}

test('caller cancellation covers body and never retries mutation',async({page})=>{
  await page.evaluate(()=>{
    window.calls=0;window.done=null;window.cancel=new AbortController();
    window.fetch=async()=>{window.calls++;return {ok:true,status:200,headers:new Headers(),json:()=>new Promise(()=>{})};};
    window.client.apiRequestAt('http://localhost:9999','/v1/test',{method:'PATCH',signal:window.cancel.signal}).catch(error=>window.done=error.code);
  });
  await expect.poll(()=>page.evaluate(()=>window.calls)).toBe(1);
  await page.evaluate(()=>window.cancel.abort());
  await expect.poll(()=>page.evaluate(()=>window.done)).toBe('request_cancelled');
  await page.clock.fastForward(35001);
  expect(await page.evaluate(()=>window.calls)).toBe(1);
});

test('caller signal does not disable own deadline and dependency identity survives',async({page})=>{
  const result=await page.evaluate(async()=>{
    window.fetch=async()=>({ok:false,status:503,headers:new Headers(),json:async()=>({error:{code:'hr_service_unavailable',details:{service:'hr-service',dependency_service:'hr'},correlation_id:'safe-reference'}})});
    try{await window.client.apiRequestAt('http://localhost:9999','/v1/test',{},'Production API');}catch(e){return {service:e.details.service,api:e.details.api_service,dependency:e.details.dependency_service};}
  });
  expect(result).toEqual({service:'hr-service',api:'Production API',dependency:'hr'});
  await page.evaluate(()=>{
    window.fetch=()=>new Promise(()=>{});window.done=null;
    window.client.apiRequestAt('http://localhost:9999','/v1/test',{signal:new AbortController().signal}).catch(error=>window.done=error.code);
  });
  await page.clock.fastForward(35001);
  await expect.poll(()=>page.evaluate(()=>window.done)).toBe('request_timeout');
});

for(const lang of ['es','en']) test(`${lang}: confirmed evidence and uncertain progress remain visible without field blame`,async({page})=>{
  await page.evaluate(async lang=>{
    const {serviceEvidencePartialFeedback}=await import('/features/service-evidence.js');
    const {renderFormFeedback}=await import('/features/form-feedback.js');
    const {translations}=await import('/i18n/translations.js');
    document.body.innerHTML='<form><label>Description<textarea name="startDescription">Received device</textarea></label><button>Save</button></form>';
    window.fetch=async()=>({ok:false,status:503,headers:new Headers(),json:async()=>({error:{code:'hr_service_unavailable',correlation_id:'fixture-reference',message:'private diagnostic'}})});
    try{await window.client.apiRequestAt('http://localhost:9999','/v1/test',{method:'PATCH'});}catch(error){renderFormFeedback(document.querySelector('form'),serviceEvidencePartialFeedback({isService:true,serviceEvidence:[{phase:'start'},{phase:'finish'}]},error,key=>translations[lang][key],{progress:true}),{lang});}
  },lang);
  await expect(page.locator('textarea')).toHaveValue('Received device');
  await expect(page.locator('[aria-invalid=true]')).toHaveCount(0);
  await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'La evidencia de cierre está guardada.':'The completion evidence is saved.');
  await expect(page.locator('[data-form-feedback]')).toContainText(lang==='es'?'Recursos Humanos':'Human resources');
  await expect(page.locator('[data-form-feedback]')).not.toContainText('private diagnostic');
});
