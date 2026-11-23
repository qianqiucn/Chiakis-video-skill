// qa.mjs — the automatic checks in one command, before any eye review (Gate B1's mechanical part):
//   1. errors on EVERY frame: a segment's render(t) or init that throws (segment, frames, message, file:line; on those
//      frames that layer stops part-way and the layers above it are not drawn) and other page JS errors — caught while
//      the draft renders, or by seeking every frame when --draft is given; on-screen text containing NaN / undefined /
//      null (every --every frames, one Chrome)
//   2. a half-size draft (render_fast --scale .5, or --draft <existing.mp4>) analysed by ffmpeg:
//      black stretches (blackdetect), parked / frozen stretches (freezedetect), every hard cut (scene score) and
//      whether it sits on the beat grid of T3_CONFIG (bpm, beatOffset), plus a 1-fps brightness strip.
//   3. the motion lint (scripts/motion_lint.mjs, references/motion-library.md «Setup») on the page already open: the
//      static checks S1–S10, R1 (GSAP, CustomEase, T3.EZ, T3.gsapSeek loaded) and, unless --errors-only, R3's curve sheet
//      (curves.svg + curves.json + lint.txt in <--out>/motion; without --out in <page dir>/tools/out/motion, their names
//      carrying the scope: curves_<segment names>.svg, curves_f<from>-<to>.svg, so callers in parallel never overwrite
//      each other's). Its summary goes into the output and qa_report.txt. A page with no strict segment (a delivered film
//      on scripts/motion_legacy.json, an opt-out) gets its notes printed and nothing
//      written; a strict segment inside a legacy film is checked strictly, here only (snap and render_fast only print
//      their motion line).
//      Scope: the lint checks the caller's own segments, so builders working on one page at once never fail each other's
//      qa on a half-written file: the files of --segments; without it, the segments on screen inside --from/--to (their
//      T3.register ids, read while every frame of the span is seeked); the whole page only when the run covers the whole
//      film (T3_CONFIG start to end). Page checks (S1, R1) stay; render and page errors (item 1) are never scoped.
// Usage: node qa.mjs <index.html> [--from 0] [--to <T3_CONFIG.end>] [--every 6] [--draft x_720p.mp4] [--cut .32] [--out qa_dir]
//        [--query "&x=1"] [--workers 2] [--errors-only] [--segments a.js,segments/b.js | none]
//   --errors-only  only the every-frame error scan (one Chrome, no screenshots, no draft) and the motion lint without
//                  the curve sheet; when to run it: production.md Toolkit «Rules»
//   --segments     the caller's own segment files, the forms motion_lint.mjs --segments takes (web-relative with forward
//                  slashes, or bare names); a file named that does not exist fails. none = a caller with no segment of its
//                  own (e.g. an audio or graphic asset pass): the lint checks no segment, its page checks are notes
//   (the checker's own tests pass --legacy-list <json>, another legacy list: the RESULT line then names it and says it
//   is no delivery check)
// Exit code 1 = something to fix (errors, bad text, unexpected freeze, a motion lint FAIL or a lint that could not
// finish, or no frame range: T3_CONFIG has no end and no --to was given, so nothing would be scanned). Cuts off the grid
// are listed, not failed: half-beat bursts are fine — read the list and ask "why does it cut here?".
// Run it through scripts/run_queue.py web (production.md Toolkit «Rules»): one browser slot of the machine.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { openPage, findFfmpeg, errorReport, reportLines } from './_cdp.mjs';

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const page = a[0];
const USAGE = 'usage: node qa.mjs <index.html> [--from s] [--to s] [--every 6] [--draft x_720p.mp4] [--cut .32] [--out dir] [--query q] [--workers 2] [--errors-only] [--segments a.js,segments/b.js | none]';
if (!page) { console.log(USAGE); process.exit(1); }
const here = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const outDir = path.resolve(opt('--out', path.join(path.dirname(path.resolve(page)), 'qa')));
const ff = findFfmpeg(); const report = []; let bad = 0;
const say = (s) => { console.log(s); report.push(s); };
const query = opt('--query', ''), errorsOnly = a.includes('--errors-only');
let draft = opt('--draft', '');
// the caller's own segments (header, item 3 «Scope»): null = not given
const segArg = a.includes('--segments') ? String(opt('--segments') || '').trim() : null;
const named = segArg == null ? null : /^none$/i.test(segArg) ? [] : segArg.split(',').map((s) => s.trim()).filter(Boolean);
if (named && !named.length && !/^none$/i.test(segArg)) { console.log(`qa: --segments names no file (give a,b.js, or none)\n${USAGE}`); process.exit(1); }
const nameKey = (list) => {                   // file-name part for the outputs of one caller: intro_gpt+intro_gpt_handoff
  const k = list.map((s) => path.basename(s).replace(/\.js$/i, '')).join('+').replace(/[^\w.+-]+/g, '-') || 'none';
  return k.length <= 60 ? k : k.slice(0, 48) + '-' + crypto.createHash('sha1').update(k).digest('hex').slice(0, 8);
};

// the segment ids on screen in frames F0..F1 (the engine shows a segment's layer, #stage > [data-seg], while
// start <= t < end), seeking every frame through the error hook exactly as pg.scan does, so its render errors are
// collected the same way and it can stand in for pg.scan; null when the page cannot say
async function onScreen(F0, F1, fps, chunk = 240) {
  const ids = new Set();
  for (let f0 = F0; f0 <= F1; f0 += chunk) {
    const f1 = Math.min(F1, f0 + chunk - 1);
    const r = await pg.send('Runtime.evaluate', { returnByValue: true, expression: `(() => { const Q = window.__cv;
      if (!Q || !Q.seek || !document.getElementById('stage')) return null; const on = new Set();
      for (let f = ${f0}; f <= ${f1}; f++) { Q.seek((f + 0.5) / ${fps}); for (const l of document.querySelectorAll('#stage > [data-seg]')) if (l.style.display !== 'none') on.add(l.dataset.seg); }
      return [...on]; })()` }).catch(() => null);
    await pg.drain();
    const v = r && !r.exceptionDetails ? r.result?.value : null;
    if (!Array.isArray(v)) return null;
    v.forEach((x) => ids.add(x));
  }
  return ids;
}

// ---- 3. the motion lint, run on the open page before it closes (header, item 3) -------------------------------
// → { lines, fail, fails }; never throws. A lint that could not finish on a page with strict segments is a fail.
async function motionLint({ curves, from, to, fps, F0, F1, whole, shown }) {
  let L;
  try { L = await import('./motion_lint.mjs'); }
  catch (e) { return { fail: true, fails: 0, tag: '', lines: [`motion lint: scripts/motion_lint.mjs did not load (${String((e && e.message) || e).split('\n')[0]}): not checked, so no pass`] }; }
  const lines = [], legacyList = opt('--legacy-list', null), lo = legacyList ? { legacyList } : {};
  if (legacyList) lines.push(`motion lint: legacy list ${path.resolve(legacyList)} (not the skill's scripts/motion_legacy.json)`);
  // scope: the caller's files, else the segments on screen in the span, else (the whole film) the page's own
  let suffix = '', segList = null;
  if (named) {
    lo.segments = named; segList = named; suffix = '_' + nameKey(named);
    lines.push(named.length ? `motion lint scope: --segments ${named.join(', ')}` : 'motion lint scope: --segments none (no segment of the caller\'s own: its page checks are notes)');
  } else if (!whole) {
    suffix = `_f${F0}-${F1}`;
    let sc = null;
    if (shown) { try { sc = L.segmentsOnScreen(path.resolve(page), [...shown], lo); } catch {} }
    if (sc) {
      const rel = (f) => path.relative(path.dirname(path.resolve(page)), f).replace(/\\/g, '/');
      lo.segments = sc.files; lo.scope = `the segment(s) on screen in f${F0}–${F1}`; segList = sc.files.map(rel);
      lines.push(`motion lint scope: the segment(s) on screen in f${F0}–${F1}: ${segList.join(', ') || 'none of their own'}`
        + `${sc.kept.length ? ` (${sc.kept.join(', ')}: register id not a literal, kept)` : ''}${sc.left.length ? `; ${sc.left.length} other segment(s) of the page not checked` : ''}; --segments names your own`);
    } else lines.push(`motion lint scope: the whole page (the segments on screen in f${F0}–${F1} could not be read)`);
  }
  const res = L.staticScan(path.resolve(page), lo);
  // the page's own answers, read without touching pg.errors (an evaluate that throws would show up as a page error)
  const quiet = { evaluate: async (x) => { try { const r = await pg.send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true }); return r.exceptionDetails ? undefined : r.result?.value; } catch { return undefined; } } };
  const extra = [];
  const rt = await L.lintRuntime(quiet, res);           // R1: a FAIL only on a page with a strict segment
  extra.push(`runtime: ${rt ? JSON.stringify(rt) : 'no answer'}`);
  let cs = null, report = null;
  if (res.strictPage) {
    // with --out the folder is the caller's own; without it the names carry the scope (one sheet per caller)
    const mdir = opt('--out') ? path.join(outDir, 'motion') : path.join(path.dirname(path.resolve(page)), 'tools', 'out', 'motion');
    const tag = opt('--out') ? '' : suffix;
    if (curves) {
      cs = await L.curveSheet(quiet, res, { outDir: mdir, from, to, fps, name: 'curves' + tag });
      extra.push(`curve sheet: ${cs.svg} (${cs.probes.length} probe(s)); data: ${cs.json}`);
      for (const p of cs.probes) extra.push(`  ${p.id} [${p.segment || '?'}] ${p.error ? 'THROWS ' + p.error : `${p.metrics.kind} ${p.metrics.channel} ${p.metrics.dur} f, Q1 ${p.metrics.q1}, peak ${p.metrics.vmax}${p.notes.length ? ' · ' + p.notes.join(' · ') : ''}`}`);
      if (cs.left.length) extra.push(`  left out: ${cs.left.length} probe(s) of the page's other segments`);
      try { fs.mkdirSync(mdir, { recursive: true }); report = path.join(mdir, `lint${tag}.txt`); fs.writeFileSync(report, L.reportText(res, extra)); }
      catch (e) { report = null; lines.push(`motion lint: cannot write the report in ${mdir}: ${e.message}`); }
    }
  }
  lines.push(...L.summaryLines(res, report));
  if (!report && lines.some((l) => /more line\(s\) in the report$|…$/.test(l)))   // no lint.txt here (--errors-only, or no strict segment), and lines left out or cut
    lines.push(`full report: node ${path.join(here, 'motion_lint.mjs')} ${path.resolve(page)}${segList && segList.length ? ` --segments ${segList.join(',')}` : ''} --out <a folder of yours>`);
  if (cs) lines.push(`curve sheet: ${cs.svg} (${cs.probes.length} probe(s)): read it against style-grammar §6b before the film (motion-library «Curve sheet»)`);
  const broken = res.strictPage && (res.error || res.needLibrary);
  if (broken) lines.push(`motion lint could not finish (${res.error ? String(res.error).split('\n')[0] : 'the library index is missing'}): no pass until it runs`);
  return { lines, fails: res.fails, fail: res.fails > 0 || !!broken, sheet: cs ? cs.svg : null,
    warns: res.strictPage ? res.warns : 0,   // a WARN passes qa but is answered (Gate B1): the RESULT line counts it
    tag: legacyList ? ` [motion lint on the test legacy list ${path.resolve(legacyList)}: not a delivery check]` : '' };
}

const warnTag = (mot) => (mot.warns ? ` (${mot.warns} motion WARN to answer: Gate B1)` : '');

// ---- 1. errors + text ---------------------------------------------------------------------------------------
const pg = await openPage(page, { query, motion: false });   // qa prints its own motion lint (item 3), after R1 and R3
const cfg = await pg.evaluate('JSON.stringify(window.T3_CONFIG||{})').then(JSON.parse);
const fps = cfg.fps || 24, from = +opt('--from', cfg.start || 0), to = +opt('--to', cfg.end), every = +opt('--every', 6);
const F0 = Math.round(from * fps), F1 = Math.round(to * fps) - 1;
if (!Number.isFinite(F0) || !Number.isFinite(F1) || F1 < F0) {   // nothing to scan is not a pass
  console.log(`qa: no frame range (from ${from} s, to ${to} s): give --to (and --from), or put end in T3_CONFIG; exit 1`);
  await pg.close();
  process.exit(1);
}
// the whole film (T3_CONFIG start to end): the lint takes the whole page; a span takes the segments on screen in it
const whole = !named && from <= (cfg.start || 0) + 1e-6 && cfg.end != null && to >= cfg.end - 1e-6;
let shown = null;                              // segment ids on screen in F0..F1, read only when the scope needs them
if (errorsOnly || draft) {                     // no draft render to watch every frame: seek every frame here
  const t1 = Date.now();
  if (!named && !whole) shown = await onScreen(F0, F1, fps);    // the same seeks as pg.scan, plus which layers show
  if (!shown) await pg.scan(F0, F1, fps);
  console.log(`seeked every frame ${F0}..${F1} in ${((Date.now() - t1) / 1000).toFixed(1)} s`);
}
if (errorsOnly) {
  const mot = await motionLint({ curves: false, from, to, fps, F0, F1, whole, shown });
  await pg.close();
  const rep = errorReport([pg]);
  console.log(`QA --errors-only ${path.resolve(page)}  frames ${F0}..${F1} @${fps}fps`);
  reportLines(rep).forEach((l) => console.log(l));
  mot.lines.forEach((l) => console.log(l));
  const why = [rep.count && `the page threw (${rep.count} kind(s))`, mot.fail && (mot.fails ? `motion lint ${mot.fails} FAIL` : 'the motion lint did not run')].filter(Boolean);
  console.log((why.length ? `RESULT: ${why.join('; ')}` : 'RESULT: no render or page errors on any frame; motion lint without FAIL') + warnTag(mot) + mot.tag);
  process.exit(why.length ? 1 : 0);
}
fs.mkdirSync(outDir, { recursive: true });
const badText = [];
for (let f = F0; f <= F1; f += every) {
  await pg.shot((f + 0.5) / fps, { scale: 0.1 });
  const hits = (await pg.evaluate(`(()=>{const out=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
    while((n=w.nextNode())){const t=n.nodeValue;if(!/\\b(NaN|undefined|null)\\b/.test(t))continue;const e=n.parentElement;if(!e)continue;
      const r=e.getBoundingClientRect(),cs=getComputedStyle(e);if(r.width<1||r.height<1||cs.visibility==='hidden'||+cs.opacity===0)continue;
      let p=e,vis=true;while(p){const s=getComputedStyle(p);if(s.display==='none'||+s.opacity===0){vis=false;break;}p=p.parentElement;}
      if(vis)out.push(t.trim().slice(0,60));}return out;})()`)) || [];
  if (hits.length) badText.push(`f${f}: ${[...new Set(hits)].join(' | ')}`);
}
if (!named && !whole && !shown) shown = await onScreen(F0, F1, fps);
const mot = await motionLint({ curves: true, from, to, fps, F0, F1, whole, shown });
await pg.close();

// ---- 2. draft video (its render seeks every frame, so it also reports every frame's errors) ----------------------
const sources = [pg];
if (!draft) {
  const base = path.join(outDir, 'qa_draft.mp4'), ej = path.join(outDir, 'qa_draft_errors.json');
  fs.rmSync(ej, { force: true });
  const r = spawnSync(process.execPath, [path.join(here, 'render_fast.mjs'), page, String(from), String(to), base, '--scale', '0.5',
    '--workers', opt('--workers', '2'), '--errors-json', ej, ...(query ? ['--query', query] : [])], { encoding: 'utf8' });
  if (r.status && !(r.status === 2 && fs.existsSync(ej))) { say('draft render failed:\n' + r.stdout + r.stderr); mot.lines.forEach(say); process.exit(1); }
  try { sources.push(...JSON.parse(fs.readFileSync(ej, 'utf8'))); } catch {}
  fs.rmSync(ej, { force: true });
  draft = base.replace(/\.mp4$/, '_720p.mp4');
}
const rep = errorReport(sources);
say(`QA ${path.resolve(page)}  frames ${F0}..${F1} @${fps}fps`);
if (!rep.render.length) say('render errors (a segment threw), every frame: none');
if (!rep.page.length) say('page errors: none');
reportLines(rep).forEach(say);
if (rep.render.length) bad++;
if (rep.page.length) bad++;
say(`text with NaN/undefined/null (every ${every} f): ${badText.length ? badText.length + ' frames' : 'none'}`);
badText.slice(0, 20).forEach((s) => say('  ' + s)); if (badText.length) bad++;

const probe = (vf) => { const r = spawnSync(ff, ['-hide_banner', '-i', draft, '-vf', vf, '-an', '-f', 'null', '-'], { encoding: 'utf8', maxBuffer: 1 << 28 }); return (r.stdout || '') + (r.stderr || ''); };
const blacks = [...probe('blackdetect=d=0.08:pix_th=0.06').matchAll(/black_start:([\d.]+) black_end:([\d.]+)/g)].map((m) => [+m[1], +m[2]]);
const frz = []; let fs0 = null;
for (const m of probe('freezedetect=n=-55dB:d=0.5').matchAll(/freeze_(start|end): ([\d.]+)/g)) { if (m[1] === 'start') fs0 = +m[2]; else { frz.push([fs0, +m[2]]); fs0 = null; } }
if (fs0 != null) frz.push([fs0, to - from]);
// a freeze that lies inside a black stretch is an intended fade-to-black, not parked art
for (let i = frz.length - 1; i >= 0; i--) if (blacks.some(([s, e]) => frz[i][0] >= s - 0.09 && frz[i][1] <= e + 0.13)) frz.splice(i, 1);
const cutTxt = probe(`select='gt(scene,${opt('--cut', '0.32')})',metadata=print:file=-`);
const cuts = [...cutTxt.matchAll(/pts_time:([\d.]+)/g)].map((m) => Math.round((+m[1] + from) * fps));
const fr = (s) => Math.round((s + from) * fps);
say(`black stretches ≥ 2 f: ${blacks.length ? blacks.map(([s, e]) => `f${fr(s)}–${fr(e) - 1}`).join(', ') : 'none'}`);
say(`frozen ≥ 12 f (parked art?): ${frz.length ? frz.map(([s, e]) => `f${fr(s)}–${fr(e) - 1}`).join(', ') : 'none'}`);
if (frz.length) bad++;
if (cfg.bpm) {
  const per = 60 / cfg.bpm, off = cfg.beatOffset || 0;
  const beatPos = (f) => ((f / fps - off) / per);
  const onGrid = [], half = [], offGrid = [];
  for (const c of cuts) {
    const b = beatPos(c), d1 = Math.abs(b - Math.round(b)) * per * fps, d2 = Math.abs(b * 2 - Math.round(b * 2)) * per / 2 * fps;
    (d1 <= 1.01 ? onGrid : d2 <= 1.01 ? half : offGrid).push(c);
  }
  say(`hard cuts: ${cuts.length} (on a beat ±1 f: ${onGrid.length}, on a half beat: ${half.length}, off the grid: ${offGrid.length})`);
  if (offGrid.length) say('  off the grid: ' + offGrid.map((c) => `f${c} (beat ${beatPos(c).toFixed(2)})`).join(', '));
} else say(`hard cuts: ${cuts.length} (no bpm in T3_CONFIG, grid not checked): ${cuts.join(', ')}`);
const ys = [...probe('fps=1,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-').matchAll(/YAVG=([\d.]+)/g)].map((m) => Math.round(+m[1]));
say(`brightness per second (YAVG 0–255): ${ys.join(' ')}`);
const sheet = path.join(outDir, 'qa_sheet.jpg');
spawnSync(ff, ['-hide_banner', '-loglevel', 'error', '-y', '-i', draft, '-vf', `fps=2,scale=320:-2,tile=8x${Math.ceil((to - from) * 2 / 8)}`, '-frames:v', '1', sheet]);
say(`contact sheet (2 fps): ${sheet}`);
mot.lines.forEach(say);
if (mot.fail) bad++;
say((bad ? `RESULT: ${bad} problem group(s) to fix${mot.fail ? (mot.fails ? `, the motion lint's ${mot.fails} FAIL among them` : ', the motion lint that did not run among them') : ''}`
  : `RESULT: mechanical checks and the motion lint pass — now look (Gate B1)${mot.sheet ? ', the curve sheet first' : ''}`) + warnTag(mot) + mot.tag);
fs.writeFileSync(path.join(outDir, 'qa_report.txt'), report.join('\n') + '\n');
process.exit(bad ? 1 : 0);
