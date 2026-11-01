const { chromium: pw } = require('playwright-core');
const chromium = require('@sparticuz/chromium').default;

// Parcours d'authentification : écran de connexion, ouverture de session,
// rechargement, déconnexion, reconnexion.
// usage: node check-connexion.js <base> <email> <mot-de-passe> <dossier-captures>
(async () => {
  const base = (process.argv[2] || 'http://127.0.0.1:3000').replace(/\/$/, '');
  const email = process.argv[3] || 'studio@agripro.preview';
  const password = process.argv[4] || '';
  const shot = process.argv[5] || '/tmp/browser/auth';
  if (!password) {
    console.log('mot de passe requis');
    return;
  }
  const exe = await chromium.executablePath();
  const browser = await pw.launch({ args: [...chromium.args, '--no-sandbox'], executablePath: exe, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const connect = async () => {
    await page.locator('#auth-email').fill(email);
    await page.locator('#auth-password').fill(password);
    await page.locator('form button[type="submit"]').first().click();
    await page.getByText('DÉCONNEXION').first().waitFor({ timeout: 45000 });
  };

  await page.goto(base + '/', { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
  await page.locator('#auth-email').waitFor({ timeout: 45000 });
  await page.screenshot({ path: shot + '-1-connexion.png' });
  console.log('1. écran de connexion affiché');

  await connect();
  await page.screenshot({ path: shot + '-2-cockpit.png' });
  console.log('2. session ouverte — cockpit | compte affiché :',
    await page.getByText(email).first().isVisible());

  await page.reload({ waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
  await page.getByText('DÉCONNEXION').first().waitFor({ timeout: 45000 });
  console.log('3. session conservée après rechargement');

  await page.getByText('DÉCONNEXION').first().click();
  await page.locator('#auth-email').waitFor({ timeout: 45000 });
  await page.screenshot({ path: shot + '-3-deconnecte.png' });
  console.log('4. déconnexion — retour à l\'écran de connexion');

  await connect();
  await page.screenshot({ path: shot + '-4-reconnecte.png' });
  console.log('5. reconnexion — cockpit');
  await browser.close();
})();
