// 不带帧号标签的原尺寸截帧（png = 无损，逐像素对比用；jpg 质量 95）：node scripts/snap_clean.mjs <page.html> <out.png|jpg> <frame> ["&query=…"]
import fs from 'node:fs';
import { openPage } from './_cdp.mjs';
const [page, out, f, query] = process.argv.slice(2);
const pg = await openPage(page, { query: query || '' });
const png = out.toLowerCase().endsWith('.png');
const buf = await pg.shot((+f + 0.5) / 24, { format: png ? 'png' : 'jpeg', quality: 95, scale: 1 });
fs.writeFileSync(out, buf);
if (pg.errors.length) console.log('PAGE ERRORS:\n  ' + [...new Set(pg.errors)].join('\n  '));
await pg.close();
console.log('ok', out);
