// Render a turntable of the textured GLB via model-viewer (WebGL) + headless Chromium.
// Screenshots N azimuths, saves frames + an animated GIF-like contact sheet input.
const { chromium } = require('playwright-core');
const path = require('path');

const EXE = path.join(process.env.HOME,
  'Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing');
const OUTDIR = path.join(__dirname, 'output', 'spin');
const URL = 'http://localhost:8731/turntable.html';
const AZIMUTHS = [0, 45, 90, 135, 180, 225, 270, 315];

(async () => {
  const browser = await chromium.launch({
    executablePath: EXE,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'],
  });
  const page = await browser.newPage({ viewport: { width: 512, height: 640 }, deviceScaleFactor: 2 });
  page.on('console', m => console.log('  [page]', m.text()));
  await page.goto(URL, { waitUntil: 'load' });
  // wait for model-viewer load event
  await page.waitForFunction('window.__ready === true', { timeout: 60000 });
  await page.waitForTimeout(1500);
  for (const az of AZIMUTHS) {
    await page.evaluate((a) => window.setAzimuth(a), az);
    await page.waitForTimeout(900);
    const f = path.join(OUTDIR, `frame_az${String(az).padStart(3, '0')}.png`);
    await page.locator('#mv').screenshot({ path: f });
    console.log('saved', path.basename(f));
  }
  await browser.close();
  console.log('DONE');
})().catch(e => { console.error('ERR', e); process.exit(1); });
