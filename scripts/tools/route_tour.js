const { chromium: pw } = require('playwright-core');
const chromium = require('@sparticuz/chromium').default;
const fs = require('fs');

// Parcours de toutes les routes protégées : statut HTTP, erreurs console,
// erreurs de page et titre rendu. Sortie JSON sur stdout.
const ROUTES = [
  '/', '/configuration', '/parcelles', '/referentiel', '/phenologie',
  '/traitements', '/employes', '/maintenance', '/cartographie', '/rapports',
  '/charges', '/crm', '/recherche', '/guide', '/administration', '/audit',
];

(async () => {
  const [base = 'http://127.0.0.1:3000', out = '/tmp/shots/tour.json', wait = '4000'] = process.argv.slice(2);
  const exe = await chromium.executablePath();
  const browser = await pw.launch({ args: [...chromium.args, '--no-sandbox'], executablePath: exe, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  await ctx.addCookies([{ name: 'agripro_menu_session', value: 'preview-session', domain: '127.0.0.1', path: '/' }]);
  const report = [];

  for (const route of ROUTES) {
    const page = await ctx.newPage();
    const consoleErrors = new Set();
    const pageErrors = new Set();
    let status = 0;
    page.on('console', m => { if (m.type() === 'error') consoleErrors.add(m.text().slice(0, 160)); });
    page.on('pageerror', e => pageErrors.add(e.message.slice(0, 160)));
    page.on('response', r => { if (r.url().endsWith(route) || r.url() === base + route) status = r.status(); });
    let title = '';
    let h1 = '';
    try {
      const resp = await page.goto(base + route, { waitUntil: 'networkidle', timeout: 45000 });
      status = status || (resp ? resp.status() : 0);
      await page.waitForTimeout(+wait);
      title = await page.title();
      h1 = await page.locator('h1').first().innerText().catch(() => '');
    } catch (err) {
      pageErrors.add('NAV: ' + err.message.slice(0, 120));
    }
    report.push({
      route,
      status,
      title: title.trim(),
      h1: h1.replace(/\s+/g, ' ').trim().slice(0, 80),
      console_errors: [...consoleErrors],
      page_errors: [...pageErrors],
    });
    console.log(`${String(status).padEnd(4)} ${route.padEnd(16)} ${h1.replace(/\s+/g, ' ').trim().slice(0, 48)}`);
    await page.close();
  }

  fs.writeFileSync(out, JSON.stringify(report, null, 2));
  await browser.close();
  const total = report.reduce((n, r) => n + r.console_errors.length + r.page_errors.length, 0);
  console.log(`\nroutes: ${report.length} | statuts: ${[...new Set(report.map(r => r.status))].join(',')} | messages d'erreur: ${total}`);
})();
