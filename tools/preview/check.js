const { chromium: pw } = require('playwright-core');
const chromium = require('@sparticuz/chromium').default;

// Contrôle de fumée : chargement, session, données réelles, thème et routes
// profondes — les quatre prouvent que les événements serveur circulent.
// usage: node check.js <base> <dossier-captures>
(async () => {
  const base = (process.argv[2] || 'http://127.0.0.1:3000').replace(/\/$/, '');
  const shot = process.argv[3] || '/tmp/browser/apercu';
  const email = process.argv[4] || 'studio@agripro.preview';
  const password = process.argv[5] || '';
  const exe = await chromium.executablePath();
  const browser = await pw.launch({
    args: [...chromium.args, '--no-sandbox'],
    executablePath: exe,
    headless: true,
  });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = new Set();
  page.on('console', (m) => { if (m.type() === 'error') errors.add(m.text().slice(0, 110)); });
  page.on('pageerror', (e) => errors.add('pageerror: ' + e.message.slice(0, 110)));

  await page.goto(base + '/', { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
  if (password) {
    await page.locator('#auth-email').waitFor({ timeout: 45000 });
    await page.locator('#auth-email').fill(email);
    await page.locator('#auth-password').fill(password);
    await page.locator('form button[type="submit"]').first().click();
    console.log('connexion : formulaire soumis');
  }
  const connected = await page.getByText('DÉCONNEXION').first()
    .waitFor({ timeout: 45000 }).then(() => true).catch(() => false);
  await page.waitForTimeout(3000);
  console.log('session active :', connected);
  console.log('donnée 155.3 ha :', await page.getByText('155.3').first().isVisible().catch(() => false));
  await page.screenshot({ path: shot + '-cockpit.png' });

  const toggle = page.getByRole('button', { name: /Basculer entre le thème/i }).first();
  await toggle.click().catch(() => {});
  await page.waitForTimeout(900);
  console.log('thème après bascule :', await page.evaluate(() => document.documentElement.dataset.theme || '(vide)'));
  await page.screenshot({ path: shot + '-encre.png' });
  await toggle.click().catch(() => {});
  await page.waitForTimeout(600);

  for (const [route, label] of [['/phenologie', 'Phénologie'], ['/crm', 'CRM'], ['/cartographie', 'Cartographie']]) {
    await page.goto(base + route, { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
    await page.getByText('DÉCONNEXION').first().waitFor({ timeout: 45000 }).catch(() => {});
    await page.waitForTimeout(4000);
    const heading = await page.getByRole('heading').first().innerText().catch(() => '(aucun)');
    console.log(`${label} : ${route} → ${heading.split('\n')[0]}`);
    await page.screenshot({ path: shot + route.replace(/\//g, '-') + '.png' });
  }

  console.log('erreurs console :', errors.size, [...errors].slice(0, 3));
  await browser.close();
})();
