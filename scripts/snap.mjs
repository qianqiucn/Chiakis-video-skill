// Fast review screenshots + contact sheet from ONE persistent Chrome page (scripts/_cdp.mjs).
// Usage:
//   node snap.mjs <index.html> <outDir> "<frames>" [--sheet name] [--cols 6] [--scale 0.5] [--query "&beats=1"] [--fps 24] [--png]
//   frames: "0-120:4,286,410-420"  (frame numbers count at --fps (24 unless given; never read from the page): frame f is shot at (f + 0.5) / fps s; label burned into each shot)
// Writes f<NNNNNN>.jpg per frame (half size by default) and, with --sheet, <outDir>/<name>.jpg tiled.
// Prints the page's errors: RENDER ERRORS (a segment's render(t) threw: which segment, which frames, the message and
// file:line) and PAGE ERRORS. Exit code 0 = clean, 2 = shots written but the page threw (fix that before judging the
// shots: the layer that threw is half drawn and the layers above it were not drawn), 1 = usage or Chrome failure.
// Use this in the build/review loop for fast deterministic preview frames and contact sheets.
// Run it through scripts/run_queue.py web (production.md Toolkit «Rules»).
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { openPage, parseFrames, findFfmpeg, errorReport, reportLines } from './_cdp.mjs';

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const [page, outArg, spec] = a;
const outDir = outArg && path.resolve(outArg);   // absolute: ffmpeg's concat list resolves entries relative to itself
if (!spec) { console.log('usage: node snap.mjs <index.html> <outDir> "<frames>" [--sheet name] [--cols 6] [--scale 0.5] [--query "&beats=1"] [--fps 24] [--png]'); process.exit(1); }
const fps = +opt('--fps', 24), scale = +opt('--scale', 0.5), cols = +opt('--cols', 6), sheet = opt('--sheet', '');
const png = a.includes('--png');
let frames;
try {
  frames = parseFrames(spec);
  if (!frames.length) throw new Error('empty frame list');
} catch (err) {
  console.error(`snap.mjs: invalid frame spec "${spec}" (${err.message || err}).`);
  console.error('Hint: argument order is: node snap.mjs <index.html> <outDir> "<frames>" [--sheet name] [--cols 6] [--scale 0.5] [--fps 24]');
  process.exit(1);
}
fs.mkdirSync(outDir, { recursive: true });
const t0 = Date.now();
const pg = await openPage(page, { query: opt('--query', '') });
const files = [];
for (const f of frames) {
  const buf = await pg.shot((f + 0.5) / fps, { format: png ? 'png' : 'jpeg', quality: 90, scale, label: 'f' + f });
  const file = path.join(outDir, `f${String(f).padStart(6, '0')}.${png ? 'png' : 'jpg'}`);
  fs.writeFileSync(file, buf); files.push(file);
}
await pg.close();
const rep = errorReport([pg]);
reportLines(rep).forEach((l) => console.log(l));
console.log(`${frames.length} shots in ${((Date.now() - t0) / 1000).toFixed(1)} s -> ${outDir}`);
if (sheet) {
  const list = path.join(outDir, '_sheet_list.txt');
  fs.writeFileSync(list, files.map((f) => `file '${f.replace(/\\/g, '/')}'\nduration 1`).join('\n') + `\nfile '${files[files.length - 1].replace(/\\/g, '/')}'\n`);
  const rows = Math.ceil(files.length / cols);
  const r = spawnSync(findFfmpeg(), ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list,
    '-vf', `scale=${Math.min(480, Math.round(1920 / cols))}:-2,tile=${cols}x${rows}`, '-frames:v', '1', path.join(outDir, sheet + '.jpg')], { stdio: 'inherit' });
  fs.rmSync(list, { force: true });
  if (!r.status) console.log('sheet ->', path.join(outDir, sheet + '.jpg'));
}
if (rep.count) { console.log(`snap: the page threw (${rep.count} kind(s), above): exit 2`); process.exitCode = 2; }
