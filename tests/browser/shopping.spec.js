const {test, expect} = require('@playwright/test');

test('mobile list persists, translates and synchronises a change after an offline reload', async ({page, context}) => {
  const errors=[];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await page.locator('#auth-toggle').click();
  await page.locator('#username').fill('browser-test');
  await page.locator('#password').fill('temporary-test-password-2026');
  await expect(page.locator('#password')).toHaveAttribute('type','password');
  await page.locator('#toggle-password').click();
  await expect(page.locator('#password')).toHaveAttribute('type','text');
  await expect(page.locator('#password')).toHaveValue('temporary-test-password-2026');
  await page.locator('#toggle-password').click();
  await expect(page.locator('#password')).toHaveAttribute('type','password');
  await page.locator('#auth-form button[type=submit]').click();
  await expect(page.locator('#quick-add')).toBeVisible();
  await page.locator('#quick-add input').fill('Arroz carolino');
  await page.locator('#quick-add button').click();
  await page.locator('#f-unit').selectOption('kg');
  await page.locator('#f-quantity').fill('2');
  await page.locator('#item-form button[type=submit]').click();
  await expect(page.locator('.item-name')).toHaveText('Arroz carolino');
  await expect.poll(async()=>{
    const r=await context.request.get('/api/items');
    return (await r.json()).items.length;
  }).toBe(1);
  await page.reload();
  await expect(page.locator('.item-name')).toHaveText('Arroz carolino');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
  await page.locator('.mobile-nav [data-view=profile]').click();
  await page.locator('#f-locale').selectOption('es-ES');
  await page.locator('#profile-form button[type=submit]').click();
  await expect(page.locator('html')).toHaveAttribute('lang','es-ES');
  await page.locator('.mobile-nav [data-view=list]').click();
  await expect.poll(async()=>page.evaluate(async()=>!!(await navigator.serviceWorker.getRegistration())?.active), {timeout:30000}).toBe(true);
  await context.setOffline(true);
  await page.reload();
  await expect(page.locator('.item-name')).toHaveText('Arroz carolino');
  await page.locator('[data-check]').click();
  await expect(page.locator('.check.done')).toHaveCount(1);
  await expect(page.locator('.offline-banner')).toBeVisible();
  await context.setOffline(false);
  await expect.poll(async()=>page.evaluate(()=>Object.keys(localStorage).filter(k=>k.endsWith('-queue')).flatMap(k=>JSON.parse(localStorage.getItem(k))).length)).toBe(0);
  const items=await(await context.request.get('/api/items')).json();
  expect(items.items[0].checked).toBe(true);
  expect(errors).toEqual([]);
});

test('keyword suggestions compare milk across stores and quantity controls keep the dialog open',async({page})=>{
  await page.goto('/');await page.locator('#auth-toggle').click();
  await page.locator('#username').fill('keyword-test');await page.locator('#password').fill('temporary-test-password-2026');
  await page.locator('#auth-form button[type=submit]').click();await expect(page.locator('#quick-add')).toBeVisible();
  await page.locator('#quick-add input').fill('Leite');await page.locator('#quick-add button').click();
  await expect(page.locator('[data-suggestion]').first()).toContainText('2 lojas');
  await page.locator('[data-suggestion]').first().click();
  await page.locator('#f-quantity').fill('2');await page.locator('#f-quantity').press('ArrowUp');
  await page.locator('#f-unit').selectOption('l');
  await expect(page.locator('#modal')).toBeVisible();
  await page.locator('#f-quantity').fill('2');
  await page.locator('#item-form button[type=submit]').click();
  await page.locator('.mobile-nav [data-view=explore]').click();
  await expect(page.locator('.comparison-card').first()).toContainText('2 lojas');
  await expect(page.locator('.comparison-row').first()).toContainText('Auchan');
  await expect(page.locator('.comparison-row').first()).toContainText('0,90');
  await page.locator('.mobile-nav [data-view=profile]').click();
  await expect(page.locator('[name="continente-delivery_subscription"]')).toHaveCount(1);
  await expect(page.locator('[name="auchan-delivery_subscription"]')).toHaveCount(0);
  await expect(page.locator('[name$="-extra_km"]')).toHaveCount(0);
  await page.locator('#reference-store').selectOption('continente');
  await page.locator('#profile-form button[type=submit]').click();
  await page.locator('.mobile-nav [data-view=list]').click();
  await expect(page.locator('.item-price')).toContainText('1,80');
  await page.locator('[data-check]').click();await expect(page.locator('#purchase-form')).toBeVisible();
  await page.locator('#purchase-form button[type=submit]').click();
  await expect(page.locator('.savings-stat .number')).toContainText('0,20');
});

test('Authelia identity opens the list directly and Rumo follows the selected month',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},extraHTTPHeaders:{
    'Remote-User':'browser-sso','X-Despensa-Proxy-Token':'browser-test-proxy-secret-'.repeat(3)
  }});
  const page=await context.newPage();await page.goto('http://127.0.0.1:38109/');
  await expect(page.locator('#quick-add')).toBeVisible();
  await expect(page.locator('#auth-form')).toHaveCount(0);
  await expect(page.locator('#budget-source')).toContainText('Rumo');
  const next=`${new Date().getFullYear()+1}-01`;
  await page.locator('#month').fill(next);await page.locator('#month').dispatchEvent('change');
  await expect(page.locator('.stats')).toContainText('420,00');
  await context.close();
});
