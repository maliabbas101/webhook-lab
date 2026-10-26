const { chromium } = require('playwright');
const { mkdirSync, renameSync } = require('node:fs');
const assert = require('node:assert/strict');

(async () => {
  mkdirSync('docs', { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    recordVideo: { dir: 'docs', size: { width: 1440, height: 1000 } }
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const pause = () => page.waitForTimeout(2000);
  const run = async expected => {
    const response = page.waitForResponse(r => r.url().endsWith('/api/simulate'));
    await page.locator('#run').click();
    assert.equal((await response).status(), 200);
    await page.waitForFunction(value => document.querySelector('#processed').textContent === value, String(expected));
    await pause();
  };
  await page.goto('http://127.0.0.1:8000');
  await pause();
  await run(1);
  assert.equal(await page.locator('#rows tr').count(), 6);
  await page.screenshot({ path: 'docs/screenshot.png', fullPage: true });
  await page.getByRole('button', { name: 'Duplicates', exact: true }).click();
  await run(1);
  assert.match(await page.locator('#rows').innerText(), /duplicate skipped/);
  await page.locator('#deduplicate').uncheck();
  await run(2);
  await page.locator('#deduplicate').check();
  await page.getByRole('button', { name: 'Outage', exact: true }).click();
  await run(0);
  assert.equal(await page.locator('#failed').innerText(), '2');
  const download = page.waitForEvent('download');
  await page.locator('#export').click();
  await (await download).saveAs('docs/sample-report.json');
  await pause();
  assert.deepEqual(errors, []);
  const videoPath = await page.video().path();
  await context.close();
  renameSync(videoPath, 'docs/demo.webm');
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto('http://127.0.0.1:8000');
  assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await mobile.screenshot({ path: 'docs/mobile.png', fullPage: true });
  await browser.close();
  console.log('Demo recorded; recovery, duplicates, outage, export and mobile checks passed.');
})().catch(error => { console.error(error); process.exit(1); });
