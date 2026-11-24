// Clean full-resolution screenshots (no burned-in frame label) via scripts/_cdp.mjs.
// Supports BOTH a single frame file AND a frame list written into an output directory:
//   Single clean frame:  node scripts/snap_clean.mjs <index.html> <out.png|jpg> <frame> [--fps 24] [--query "&x=1"]
//   Clean frame list:    node scripts/snap_clean.mjs <index.html> <outDir> "0,48,120-124" [--fps 24] [--png] [--query "&x=1"]
//   Labelled sheet:      node scripts/snap.mjs <index.html> <outDir> "0-120:4" --sheet s1 --cols 6 --fps 24
// Run through scripts/run_queue.py web (references/production.md §2).
import fs from 'node:fs';
import path from 'node:path';
import { openPage, parseFrames, errorReport, reportLines } from './_cdp.mjs';

const USAGE = [
  'Usage (choose the mode that matches your task):',
  '  1) Single clean still : node scripts/snap_clean.mjs web/index.html out/f048.png 48 --fps 24',
  '  2) Clean frame list   : node scripts/snap_clean.mjs web/index.html out/stills "0,48,120" --fps 24 --png',
  '  3) Labelled sheet     : node scripts/snap.mjs web/index.html out/snaps "0-240:8" --sheet s1 --cols 6 --fps 24',
  'Options: [--fps 24] [--scale 1] [--png] [--query "&x=1"]',
].join('\n');

const a = process.argv.slice(2);
const has = (k) => a.includes(k);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
if (has('-h') || has('--help')) { console.log(USAGE); process.exit(0); }

// Collect positional args (skip flags and their values)
const flagTakesVal = new Set(['--fps', '--scale', '--query']);
const pos = [];
for (let i = 0; i < a.length; i++) {
  if (flagTakesVal.has(a[i])) { i++; continue; }
  if (a[i].startsWith('--')) continue;
  pos.push(a[i]);
}
const [page, outArg, frameSpec, legacyQuery] = pos;
if (!page || !outArg || !frameSpec) {
  console.error('snap_clean.mjs: missing required arguments.\n' + USAGE);
  process.exit(1);
}

const fps = +opt('--fps', 24);
const scale = +opt('--scale', 1);
const query = opt('--query', legacyQuery || '');
if (!Number.isFinite(fps) || fps <= 0) {
  console.error(`snap_clean.mjs: invalid --fps "${opt('--fps', '')}".\n` + USAGE);
  process.exit(1);
}

let frames;
try {
  frames = parseFrames(frameSpec);
  if (!frames.length) throw new Error('empty frame spec');
} catch (err) {
  console.error(`snap_clean.mjs: invalid frame spec "${frameSpec}" (${err.message || err}).\n` + USAGE);
  process.exit(1);
}

const isSingleFile = /\.(png|jpe?g)$/i.test(outArg);
if (isSingleFile && frames.length > 1) {
  console.error(`snap_clean.mjs: "${outArg}" is a single image file, but "${frameSpec}" expands to ${frames.length} frames. Pass an output directory instead.\n` + USAGE);
  process.exit(1);
}

const png = isSingleFile ? outArg.toLowerCase().endsWith('.png') : has('--png');
const ext = png ? 'png' : 'jpg';
const pg = await openPage(page, { query });

try {
  if (isSingleFile) {
    fs.mkdirSync(path.dirname(path.resolve(outArg)), { recursive: true });
    const buf = await pg.shot((frames[0] + 0.5) / fps, { format: png ? 'png' : 'jpeg', quality: 95, scale });
    fs.writeFileSync(outArg, buf);
    console.log('ok', outArg);
  } else {
    const outDir = path.resolve(outArg);
    fs.mkdirSync(outDir, { recursive: true });
    for (const f of frames) {
      const buf = await pg.shot((f + 0.5) / fps, { format: png ? 'png' : 'jpeg', quality: 95, scale });
      const dst = path.join(outDir, `f${String(f).padStart(6, '0')}.${ext}`);
      fs.writeFileSync(dst, buf);
    }
    console.log(`ok ${frames.length} clean still(s) -> ${outDir}`);
  }
} finally {
  await pg.close();
}

const rep = errorReport([pg]);
reportLines(rep).forEach((l) => console.log(l));
if (rep.count) {
  console.log(`snap_clean: the page threw (${rep.count} kind(s), above): exit 2`);
  process.exitCode = 2;
}
