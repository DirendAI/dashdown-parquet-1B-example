// Capture screenshots of the live dashboard for the Open Data Project Gallery
// submission. Run in CI (the runner has open internet):
//   node scripts/capture_screenshots.mjs <url> <outdir>
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const url = process.argv[2] ?? 'https://direndai.github.io/dashdown-parquet-1B-example/';
const outdir = process.argv[3] ?? 'screenshots';
mkdirSync(outdir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});

await page.goto(url, { waitUntil: 'networkidle', timeout: 90_000 });

// Scroll through the whole page so every chart renders, then settle.
const height = await page.evaluate(() => document.body.scrollHeight);
for (let y = 0; y < height; y += 700) {
  await page.evaluate(v => window.scrollTo(0, v), y);
  await page.waitForTimeout(250);
}
await page.waitForTimeout(4000); // let chart animations finish
await page.evaluate(() => window.scrollTo(0, 0));
await page.waitForTimeout(1000);

// Full-page capture plus viewport-sized tiles to crop from later.
await page.screenshot({ path: `${outdir}/fullpage.png`, fullPage: true });
const tiles = Math.ceil(height / 900);
for (let i = 0; i < tiles; i++) {
  await page.evaluate(v => window.scrollTo(0, v), i * 900);
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${outdir}/tile-${String(i).padStart(2, '0')}.png` });
}

// Save the rendered HTML + text so the commentary can be quoted verbatim.
writeFileSync(`${outdir}/rendered.html`, await page.content());
writeFileSync(`${outdir}/rendered.txt`, await page.evaluate(() => document.body.innerText));

console.log(`Captured fullpage + ${tiles} tiles from ${url} (page height ${height}px)`);
await browser.close();
