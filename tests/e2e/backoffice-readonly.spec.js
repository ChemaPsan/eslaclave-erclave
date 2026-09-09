const {test,expect}=require("@playwright/test");
const {installLocalAuth}=require("./local-auth");

test("Backoffice Local autentica y consulta sus tres secciones sin mutaciones",async({page})=>{
  const remote=[],commands=[],pageErrors=[];
  page.on("pageerror",error=>pageErrors.push(error.message));
  await page.route("**/*",async route=>{
    const request=route.request(),url=new URL(request.url());
    if(!["127.0.0.1","localhost"].includes(url.hostname)){remote.push(url.hostname);return route.abort();}
    if(url.port!=="9099"&&!["GET","HEAD","OPTIONS"].includes(request.method())){commands.push(url.pathname);return route.abort();}
    return route.fallback();
  });
  await installLocalAuth(page);
  await page.goto("/backoffice/");
  await page.locator("[data-form=login] [name=email]").fill("admin.qa@erclave.local");
  await page.locator("[data-form=login] [name=password]").fill("LocalDemo123!");
  await page.locator("[data-form=login] button[type=submit]").click();
  for(const tab of ["onboarding","tenant-admin","usage"]){
    const button=page.locator(`[data-tab='${tab}']`);
    await button.click();
    await expect(button).toHaveClass(/active/);
  }
  await expect(page.locator("[data-form=usage-search]")).toBeVisible();
  expect(remote).toEqual([]);
  expect(commands).toEqual([]);
  expect(pageErrors).toEqual([]);
});
