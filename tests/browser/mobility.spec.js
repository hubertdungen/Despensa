const {test,expect}=require('@playwright/test');
async function register(page,name){
  await page.goto('/');await page.locator('#auth-toggle').click();
  await page.locator('#username').fill(name);await page.locator('#password').fill('temporary-password-2026');
  await page.locator('#auth-form button[type=submit]').click();await expect(page.locator('#quick-add')).toBeVisible();
}
async function addMilk(page){
  await page.locator('#quick-add input').fill('Leite');await page.locator('#quick-add button').click();
  await page.locator('#f-unit').selectOption('l');await page.locator('#item-form button[type=submit]').click();
  await expect(page.locator('.item')).toHaveCount(1);
}

test('exact nearby branch persists immediately, is visible and is used by a saved plan after reload',async({page,context})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await register(page,'mobility-branches');
  await context.request.put('/api/profile',{data:{home:'Casa teste',home_coords:[-9.1,38.7],work:'Trabalho teste',work_coords:[-9.2,38.8],mobility:{consumption:6,price_mode:'manual',unit_price:1.8}}});
  await page.reload();await addMilk(page);
  await page.locator('.mobile-nav [data-view=profile]').click();
  const branch=page.locator('[data-use-branch="branch:auchan:2"]').first();
  await expect(branch).toBeVisible();await branch.click();
  await expect(page.locator('#saved-branches-panel')).toContainText('Avenida do Teste 22');
  expect((await(await context.request.get('/api/me')).json()).profile.stores.auchan.branch_id).toBe('branch:auchan:2');
  await page.locator('.mobile-nav [data-view=plan]').click();
  await expect(page.locator('.plan-card').first()).toContainText('Avenida do Teste 22');
  await expect(page.locator('.journey-facts').first()).toContainText('0,43'); // 4 km × 6 L/100 km × €1.8
  await expect(page.locator('.plan-total').first()).toContainText('1,33');
  await expect(page.locator('.plan-card').first()).toContainText('Sem trânsito ao vivo');
  let release,entered;const held=new Promise(r=>release=r),requested=new Promise(r=>entered=r);
  await page.route('**/api/plans/select',async route=>{entered();await held;await route.continue();});
  const use=page.locator('[data-select-plan]').first();await use.click();await requested;
  await expect(use).toBeDisabled();await expect(use).toContainText('A guardar plano');release();
  await expect(page.locator('.selected-journey')).toContainText('Plano escolhido');
  await page.locator('.selected-journey summary').click();
  await expect(page.locator('.selected-journey')).toContainText('Avenida do Teste 22');
  await expect(page.locator('.selected-journey .stop-products')).toContainText('Leite');
  await expect(page.locator('.selected-journey .stop-links a').first()).toHaveAttribute('href',/destination=38.72%2C-9.12/);
  await page.reload();await expect(page.locator('.selected-journey')).toContainText('Plano escolhido');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  expect(errors).toEqual([]);
});

test('planning gives immediate busy feedback while a request is pending',async({page})=>{
  await register(page,'mobility-progress');await addMilk(page);
  let release,entered;const held=new Promise(r=>release=r),requested=new Promise(r=>entered=r);
  await page.route('**/api/plans',async route=>{entered();await held;await route.continue();});
  await page.locator('.mobile-nav [data-view=plan]').click();await requested;
  await expect(page.locator('#plan-loading')).toBeVisible();
  await expect(page.locator('[data-action=plan]')).toBeDisabled();
  await expect(page.locator('[data-action=plan]')).toContainText('A comparar');
  release();await expect(page.locator('#plan-loading')).toBeHidden();
  await expect(page.locator('[data-select-plan]').first()).toBeEnabled();
});

test('catalogue fills exact engine consumption, accepts three decimals and real consumption override',async({page,context})=>{
  const vehicle={id:'ademe:fixture',label:'Renault Clio 1.5 dCi Teste',consumption:4.637,fuel:'diesel',unit:'L/100 km',source:'ADEME fixture'};
  await page.route('**/api/vehicles?**',r=>r.fulfill({json:{vehicles:[vehicle]}}));
  await page.route('**/api/vehicles/detail?**',r=>r.fulfill({json:{vehicle}}));
  await page.route('**/api/fuel-prices?**',r=>r.fulfill({json:{prices:{diesel:{unit_price:1.8,observed_on:'2026-10-28',source:'DGEG fixture'}}}}));
  await register(page,'mobility-vehicle');await page.locator('.mobile-nav [data-view=profile]').click();
  await page.locator('#vehicle-query').fill('Renault Clio');await page.locator('#vehicle-search').click();
  await page.locator('[data-vehicle]').click();await expect(page.locator('#m-consumption')).toHaveValue('4.637');
  await expect(page.locator('#m-fuel')).toHaveValue('diesel');
  await page.locator('#fuel-current').click();await expect(page.locator('#fuel-preview')).toContainText('DGEG fixture');
  const response=page.waitForResponse(r=>r.url().endsWith('/api/profile')&&r.request().method()==='PUT');
  await page.locator('#profile-form button[type=submit]').click();expect((await response).status()).toBe(200);
  await expect.poll(()=>page.evaluate(()=>!!state.profileSaving)).toBe(false);
  await expect(page.locator('#m-consumption')).toHaveValue('4.637');
  await page.locator('#m-consumption').fill('5.2');await page.locator('#profile-form button[type=submit]').click();
  await expect.poll(async()=> (await(await context.request.get('/api/me')).json()).profile.mobility.consumption).toBe(5.2);
  await page.locator('#m-fuel').selectOption('electric');
  await expect(page.locator('#m-consumption')).toHaveValue('');
  await expect(page.locator('#m-unit_price')).toHaveValue('');
  await page.locator('#m-mode').selectOption('transit');await expect(page.locator('#m-transit_ticket')).toBeVisible();
  await expect(page.locator('#m-consumption')).toBeHidden();
});

test('the chosen store and price are used at checkout and ticking a purchase keeps the plan valid',async({page,context})=>{
  await register(page,'mobility-checkout');
  await context.request.put('/api/profile',{data:{home:'Casa teste',home_coords:[-9.1,38.7],mobility:{consumption:6,price_mode:'manual',unit_price:1.8}}});
  await page.reload();await addMilk(page);await page.locator('.mobile-nav [data-view=plan]').click();
  await expect(page.locator('[data-toggle-plans]')).toBeVisible();await page.locator('[data-toggle-plans]').click();
  const alternative=page.locator('.plan-card').filter({has:page.locator('header h3').filter({hasText:/^Continente$/})});
  await alternative.locator('[data-select-plan]').click();
  await expect(page.locator('.item-price')).toContainText('Continente');
  await page.locator('[data-check]').click();
  await expect(page.locator('#purchase-store')).toHaveValue('continente');
  await expect(page.locator('#f-paid')).toHaveValue('1.00');
  await page.locator('#purchase-form button[type=submit]').click();
  await expect(page.locator('.item.checked')).toHaveCount(1);
  await expect.poll(async()=> (await(await context.request.get('/api/plans/selected')).json()).selected.stale).toBe(false);
});

test('verified public transport shows schedules and declared fares without inventing kilometres',async({page,context})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await register(page,'mobility-transit');
  await context.request.put('/api/profile',{data:{home:'Casa teste',home_coords:[-9.1,38.7],mobility:{mode:'transit',transit_ticket:1.8}}});
  await page.reload();await addMilk(page);await page.locator('.mobile-nav [data-view=plan]').click();
  const card=page.locator('.plan-card').first();
  await expect(card.locator('.journey-facts')).toContainText('Horários consultados');
  await expect(card.locator('.journey-facts')).toContainText('3,60');
  await expect(card.locator('.journey-facts')).not.toContainText('km');
  await expect(card).not.toContainText('Sem trânsito ao vivo');
  await card.locator('.trip-assumptions summary').click();
  await expect(card.locator('.transit-connections')).toContainText('BUS 7');
  expect(errors).toEqual([]);
});

test('work hours drive a best-moment search whose window becomes the chosen trip',async({page,context})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await register(page,'mobility-windows');
  await context.request.put('/api/profile',{data:{home:'Casa teste',home_coords:[-9.1,38.7],work:'Trabalho teste',work_coords:[-9.2,38.8],
    work_start:'09:00',work_end:'18:00',workdays:[0,1,2,3,4,5,6],mobility:{consumption:6,price_mode:'manual',unit_price:1.8}}});
  await page.reload();await addMilk(page);
  await page.locator('.mobile-nav [data-view=plan]').click();
  await page.locator('[data-action-windows]').click();
  const best=page.locator('.window-card.best');
  await expect(best).toBeVisible({timeout:20000});
  await expect(best.locator('.trip-stops li')).not.toHaveCount(0);
  await best.locator('[data-select-window]').click();
  await expect(page.locator('.selected-journey')).toContainText('Plano escolhido');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  expect(errors).toEqual([]);
});
