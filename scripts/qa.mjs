// qa.mjs — the automatic checks in one command, before any eye review (Gate B1's mechanical part):
//   Stage 1 [frame-scan]    : errors on EVERY frame (init/render throws via error hook; when --draft is given, seeks every frame)
//   Stage 2 [text-audit]    : on-screen text containing NaN / undefined / null (every --every frames via fast seekOnly, ZERO screenshots!)
//   Stage 3 [motion-lint]   : static checks S1–S10, R1 runtime, and R3 curve sheet (curves.svg + curves.json + lint.txt)
//   Stage 4 [ffmpeg-metrics]: draft render (if no --draft), blackdetect, freezedetect, scene hard cuts vs beat grid, 1-fps YAVG
//   Stage 5 [contact-sheet] : 2-fps contact sheet + final verdict
//
// Resilience (v1.7.1):
//   - Logs start, finish, and elapsed time for EVERY stage.
//   - Incrementally flushes `qa_report.txt` AND `qa_state.json` after EVERY stage (and on SIGINT/SIGTERM/timeout),
//     so an interrupted run preserves every already-computed metric and clearly names `interruptedStage`.
//   - Enforces per-stage ffmpeg/subprocess timeout (--stage-timeout, default 120 s) so no probe can silently hang.
//
// Usage: node qa.mjs <index.html> [--from 0] [--to <T3_CONFIG.end>] [--every 6] [--draft x_720p.mp4] [--cut .32] [--out qa_dir]
//        [--query "&x=1"] [--workers 2] [--stage-timeout 120] [--errors-only] [--segments a.js,segments/b.js | none]
// Run through scripts/run_queue.py web (one browser slot of the machine).
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { openPage, findFfmpeg, errorReport, reportLines } from './_cdp.mjs';

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const page = a[0];
const USAGE = 'usage: node qa.mjs <index.html> [--from s] [--to s] [--every 6] [--draft x_720p.mp4] [--cut .32] [--out dir] [--query q] [--workers 2] [--stage-timeout 120] [--errors-only] [--segments a.js,segments/b.js | none]';
if (!page || a.includes('-h') || a.includes('--help')) { console.log(USAGE); process.exit(a.includes('-h') || a.includes('--help') ? 0 : 1); }

const here = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const outDir = path.resolve(opt('--out', path.join(path.dirname(path.resolve(page)), 'qa')));
const ff = findFfmpeg();
const stageTimeoutMs = Math.max(15, +opt('--stage-timeout', 120)) * 1000;
const report = [];
let bad = 0;
const say = (s) => { console.log(s); report.push(s); };
const query = opt('--query', ''), errorsOnly = a.includes('--errors-only');
let draft = opt('--draft', '');
const segArg = a.includes('--segments') ? String(opt('--segments') || '').trim() : null;
const named = segArg == null ? null : /^none$/i.test(segArg) ? [] : segArg.split(',').map((s) => s.trim()).filter(Boolean);
if (named && !named.length && !/^none$/i.test(segArg)) { console.log(`qa: --segments names no file (give a,b.js, or none)\n${USAGE}`); process.exit(1); }

const nameKey = (list) => {
  const k = list.map((s) => path.basename(s).replace(/\.js$/i, '')).join('+').replace(/[^\w.+-]+/g, '-') || 'none';
  return k.length <= 60 ? k : k.slice(0, 48) + '-' + crypto.createHash('sha1').update(k).digest('hex').slice(0, 8);
};

const tRun0 = Date.now();
const state = {
  page: path.resolve(page),
  draft: draft ? path.resolve(draft) : null,
  fps: null,
  frameRange: null,
  status: 'running',
  currentStage: 'init',
  interruptedStage: null,
  stages: {},
  metrics: {},
  updatedAt: new Date().toISOString(),
};

function flushProgress() {
  if (errorsOnly) return;
  try {
    fs.mkdirSync(outDir, { recursive: true });
    state.updatedAt = new Date().toISOString();
    fs.writeFileSync(path.join(outDir, 'qa_state.json'), JSON.stringify(state, null, 2) + '\n');
    const hdr = state.status === 'completed'
      ? ''
      : `[INCOMPLETE QA — status=${state.status}, currentStage=${state.currentStage}${state.interruptedStage ? `, interruptedStage=${state.interruptedStage}` : ''}]\n`;
    fs.writeFileSync(path.join(outDir, 'qa_report.txt'), hdr + report.join('\n') + '\n');
  } catch {}
}

function beginStage(name, detail = '') {
  state.currentStage = name;
  state.stages[name] = { status: 'running', startedAt: new Date().toISOString(), elapsedSec: null };
  console.log(`[qa +${((Date.now() - tRun0) / 1000).toFixed(1)}s] START ${name}${detail ? ' — ' + detail : ''}`);
  flushProgress();
  return Date.now();
}

function endStage(name, t0, summary = '') {
  const sec = +((Date.now() - t0) / 1000).toFixed(2);
  state.stages[name] = { ...(state.stages[name] || {}), status: 'done', elapsedSec: sec, summary };
  console.log(`[qa +${((Date.now() - tRun0) / 1000).toFixed(1)}s] DONE  ${name} (${sec}s)${summary ? ' — ' + summary : ''}`);
  flushProgress();
}

function failStage(name, t0, errMsg) {
  const sec = +((Date.now() - t0) / 1000).toFixed(2);
  state.status = 'interrupted';
  state.interruptedStage = name;
  state.stages[name] = { ...(state.stages[name] || {}), status: 'failed', elapsedSec: sec, error: errMsg };
  say(`[qa ERROR] stage ${name} failed after ${sec}s: ${errMsg}`);
  flushProgress();
}

let activePg = null;
const onInterrupt = (sig) => {
  state.status = 'interrupted';
  state.interruptedStage = state.currentStage;
  report.push(`[qa INTERRUPTED by ${sig} during stage ${state.currentStage}; prior metrics preserved above]`);
  flushProgress();
  Promise.resolve(activePg?.close()).catch(() => {}).finally(() => process.exit(1));
};
process.once('SIGINT', onInterrupt);
process.once('SIGTERM', onInterrupt);

async function onScreen(pg, F0, F1, fps, chunk = 240) {
  const ids = new Set();
  for (let f0 = F0; f0 <= F1; f0 += chunk) {
    const f1 = Math.min(F1, f0 + chunk - 1);
    const r = await pg.send('Runtime.evaluate', { returnByValue: true, expression: `(() => { const Q = window.__cv;
      if (!Q || !Q.seek || !document.getElementById('stage')) return null; const on = new Set();
      for (let f = ${f0}; f <= ${f1}; f++) { Q.seek((f + 0.5) / ${fps}); for (const l of document.querySelectorAll('#stage > [data-seg]')) if (l.style.display !== 'none') on.add(l.dataset.seg); }
      return [...on]; })()` }, Math.max(30000, stageTimeoutMs)).catch(() => null);
    await pg.drain();
    const v = r && !r.exceptionDetails ? r.result?.value : null;
    if (!Array.isArray(v)) return null;
    v.forEach((x) => ids.add(x));
  }
  return ids;
}

async function motionLint(pg, { curves, from, to, fps, F0, F1, whole, shown }) {
  let L;
  try { L = await import('./motion_lint.mjs'); }
  catch (e) { return { fail: true, fails: 0, tag: '', lines: [`motion lint: scripts/motion_lint.mjs did not load (${String((e && e.message) || e).split('\n')[0]}): not checked, so no pass`] }; }
  const lines = [], legacyList = opt('--legacy-list', null), lo = legacyList ? { legacyList } : {};
  if (legacyList) lines.push(`motion lint: legacy list ${path.resolve(legacyList)} (not the skill's scripts/motion_legacy.json)`);
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
  const quiet = { evaluate: async (x) => { try { const r = await pg.send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true }, Math.max(30000, stageTimeoutMs)); return r.exceptionDetails ? undefined : r.result?.value; } catch { return undefined; } } };
  const extra = [];
  const rt = await L.lintRuntime(quiet, res);
  extra.push(`runtime: ${rt ? JSON.stringify(rt) : 'no answer'}`);
  let cs = null, repFile = null;
  if (res.strictPage) {
    const mdir = opt('--out') ? path.join(outDir, 'motion') : path.join(path.dirname(path.resolve(page)), 'tools', 'out', 'motion');
    const tag = opt('--out') ? '' : suffix;
    if (curves) {
      cs = await L.curveSheet(quiet, res, { outDir: mdir, from, to, fps, name: 'curves' + tag });
      extra.push(`curve sheet: ${cs.svg} (${cs.probes.length} probe(s)); data: ${cs.json}`);
      for (const p of cs.probes) extra.push(`  ${p.id} [${p.segment || '?'}] ${p.error ? 'THROWS ' + p.error : `${p.metrics.kind} ${p.metrics.channel} ${p.metrics.dur} f, Q1 ${p.metrics.q1}, peak ${p.metrics.vmax}${p.notes.length ? ' · ' + p.notes.join(' · ') : ''}`}`);
      if (cs.left.length) extra.push(`  left out: ${cs.left.length} probe(s) of the page's other segments`);
      try { fs.mkdirSync(mdir, { recursive: true }); repFile = path.join(mdir, `lint${tag}.txt`); fs.writeFileSync(repFile, L.reportText(res, extra)); }
      catch (e) { repFile = null; lines.push(`motion lint: cannot write the report in ${mdir}: ${e.message}`); }
    }
  }
  lines.push(...L.summaryLines(res, repFile));
  if (!repFile && lines.some((l) => /more line\(s\) in the report$|…$/.test(l)))
    lines.push(`full report: node ${path.join(here, 'motion_lint.mjs')} ${path.resolve(page)}${segList && segList.length ? ` --segments ${segList.join(',')}` : ''} --out <a folder of yours>`);
  if (cs) lines.push(`curve sheet: ${cs.svg} (${cs.probes.length} probe(s)): read it against style-grammar §6b before the film (motion-library «Curve sheet»)`);
  const broken = res.strictPage && (res.error || res.needLibrary);
  if (broken) lines.push(`motion lint could not finish (${res.error ? String(res.error).split('\n')[0] : 'the library index is missing'}): no pass until it runs`);
  return {
    lines, fails: res.fails, fail: res.fails > 0 || !!broken, sheet: cs ? cs.svg : null,
    warns: res.strictPage ? res.warns : 0,
    tag: legacyList ? ` [motion lint on the test legacy list ${path.resolve(legacyList)}: not a delivery check]` : '',
  };
}

const warnTag = (mot) => (mot.warns ? ` (${mot.warns} motion WARN to answer: Gate B1)` : '');

// ---- Stage 1: open page + frame-scan -----------------------------------------------------------------------
const tS1 = beginStage('1/5:frame-scan');
let pg;
try {
  pg = await openPage(page, { query, motion: false, callTimeout: Math.max(25000, stageTimeoutMs / 2) });
  activePg = pg;
} catch (err) {
  failStage('1/5:frame-scan', tS1, err.message || String(err));
  process.exit(1);
}

const cfg = await pg.evaluate('JSON.stringify(window.T3_CONFIG||{})').then(JSON.parse);
const fps = cfg.fps || 24, from = +opt('--from', cfg.start || 0), to = +opt('--to', cfg.end), every = +opt('--every', 6);
const F0 = Math.round(from * fps), F1 = Math.round(to * fps) - 1;
state.fps = fps;
state.frameRange = [F0, F1];
if (!Number.isFinite(F0) || !Number.isFinite(F1) || F1 < F0) {
  failStage('1/5:frame-scan', tS1, `no frame range (from ${from} s, to ${to} s): give --to (and --from), or put end in T3_CONFIG`);
  await pg.close();
  process.exit(1);
}

const whole = !named && from <= (cfg.start || 0) + 1e-6 && cfg.end != null && to >= cfg.end - 1e-6;
let shown = null;
try {
  if (errorsOnly || draft) {
    if (!named && !whole) shown = await onScreen(pg, F0, F1, fps);
    if (!shown) await pg.scan(F0, F1, fps);
    state.metrics.scannedFrames = F1 - F0 + 1;
    endStage('1/5:frame-scan', tS1, `seeked every frame ${F0}..${F1} (${F1 - F0 + 1} f)`);
  } else {
    endStage('1/5:frame-scan', tS1, 'deferred to Stage 4 draft render');
  }
} catch (err) {
  failStage('1/5:frame-scan', tS1, err.message || String(err));
  await pg.close();
  process.exit(1);
}

if (errorsOnly) {
  const tM = beginStage('3/5:motion-lint', 'errors-only static+runtime');
  const mot = await motionLint(pg, { curves: false, from, to, fps, F0, F1, whole, shown });
  endStage('3/5:motion-lint', tM, `fails=${mot.fails}`);
  await pg.close(); activePg = null;
  const rep = errorReport([pg]);
  console.log(`QA --errors-only ${path.resolve(page)}  frames ${F0}..${F1} @${fps}fps`);
  reportLines(rep).forEach((l) => console.log(l));
  mot.lines.forEach((l) => console.log(l));
  const why = [rep.count && `the page threw (${rep.count} kind(s))`, mot.fail && (mot.fails ? `motion lint ${mot.fails} FAIL` : 'the motion lint did not run')].filter(Boolean);
  console.log((why.length ? `RESULT: ${why.join('; ')}` : 'RESULT: no render or page errors on any frame; motion lint without FAIL') + warnTag(mot) + mot.tag);
  process.exit(why.length ? 1 : 0);
}

fs.mkdirSync(outDir, { recursive: true });
say(`QA ${path.resolve(page)}  frames ${F0}..${F1} @${fps}fps`);

// ---- Stage 2: fast DOM text audit (ZERO screenshots — eliminates 120x double-rAF/capture hang!) ------------
const tS2 = beginStage('2/5:text-audit', `every ${every} f via seekOnly`);
const badText = [];
try {
  let checked = 0;
  for (let f = F0; f <= F1; f += every) {
    await pg.seekOnly((f + 0.5) / fps);
    const hits = (await pg.evaluate(`(()=>{const out=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
      while((n=w.nextNode())){const t=n.nodeValue;if(!/\\b(NaN|undefined|null)\\b/.test(t))continue;const e=n.parentElement;if(!e)continue;
        const r=e.getBoundingClientRect(),cs=getComputedStyle(e);if(r.width<1||r.height<1||cs.visibility==='hidden'||+cs.opacity===0)continue;
        let p=e,vis=true;while(p){const s=getComputedStyle(p);if(s.display==='none'||+s.opacity===0){vis=false;break;}p=p.parentElement;}
        if(vis)out.push(t.trim().slice(0,60));}return out;})()`)) || [];
    if (hits.length) badText.push(`f${f}: ${[...new Set(hits)].join(' | ')}`);
    checked++;
  }
  state.metrics.textCheckedFrames = checked;
  state.metrics.badTextFrames = badText.length;
  say(`text with NaN/undefined/null (every ${every} f): ${badText.length ? badText.length + ' frames' : 'none'}`);
  badText.slice(0, 20).forEach((s) => say('  ' + s));
  if (badText.length) bad++;
  endStage('2/5:text-audit', tS2, `checked ${checked} frames, bad=${badText.length}`);
} catch (err) {
  failStage('2/5:text-audit', tS2, err.message || String(err));
  await pg.close(); activePg = null;
  process.exit(1);
}

// ---- Stage 3: motion-lint + curve sheet --------------------------------------------------------------------
const tS3 = beginStage('3/5:motion-lint', 'static + runtime + curveSheet');
let mot;
try {
  if (!named && !whole && !shown) shown = await onScreen(pg, F0, F1, fps);
  mot = await motionLint(pg, { curves: true, from, to, fps, F0, F1, whole, shown });
  state.metrics.motionFails = mot.fails;
  state.metrics.motionWarns = mot.warns;
  state.metrics.curveSheet = mot.sheet;
  endStage('3/5:motion-lint', tS3, `fails=${mot.fails} warns=${mot.warns}`);
} catch (err) {
  failStage('3/5:motion-lint', tS3, err.message || String(err));
  await pg.close(); activePg = null;
  process.exit(1);
} finally {
  if (activePg) { await pg.close(); activePg = null; }
}

// ---- Stage 4: draft render (if needed) + ffmpeg metrics ----------------------------------------------------
const tS4 = beginStage('4/5:ffmpeg-metrics', draft ? `reusing draft ${path.basename(draft)}` : 'rendering 0.5x draft + ffmpeg probes');
const sources = [pg];
if (!draft) {
  const base = path.join(outDir, 'qa_draft.mp4'), ej = path.join(outDir, 'qa_draft_errors.json');
  fs.rmSync(ej, { force: true });
  const r = spawnSync(process.execPath, [path.join(here, 'render_fast.mjs'), page, String(from), String(to), base, '--scale', '0.5',
    '--fps', String(fps), '--workers', opt('--workers', '2'), '--errors-json', ej, ...(query ? ['--query', query] : [])],
    { encoding: 'utf8', timeout: Math.max(stageTimeoutMs * 3, 300000) });
  if (r.error || (r.status && !(r.status === 2 && fs.existsSync(ej)))) {
    failStage('4/5:ffmpeg-metrics', tS4, `draft render failed: ${r.error ? r.error.message : (r.stdout + r.stderr).slice(-400)}`);
    mot.lines.forEach(say);
    flushProgress();
    process.exit(1);
  }
  try { sources.push(...JSON.parse(fs.readFileSync(ej, 'utf8'))); } catch {}
  fs.rmSync(ej, { force: true });
  draft = base.replace(/\.mp4$/, '_720p.mp4');
  state.draft = path.resolve(draft);
}

const rep = errorReport(sources);
state.metrics.renderErrorKinds = rep.render.length;
state.metrics.pageErrorCount = rep.page.length;
if (!rep.render.length) say('render errors (a segment threw), every frame: none');
if (!rep.page.length) say('page errors: none');
reportLines(rep).forEach(say);
if (rep.render.length) bad++;
if (rep.page.length) bad++;
flushProgress();

function probe(label, vf) {
  const tp = Date.now();
  const r = spawnSync(ff, ['-hide_banner', '-i', draft, '-vf', vf, '-an', '-f', 'null', '-'], { encoding: 'utf8', maxBuffer: 1 << 28, timeout: stageTimeoutMs });
  if (r.error) throw new Error(`ffmpeg ${label} failed/timed out after ${((Date.now() - tp) / 1000).toFixed(1)}s: ${r.error.message}`);
  if (r.status && r.status !== 0) throw new Error(`ffmpeg ${label} exited ${r.status}: ${(r.stderr || '').slice(-300)}`);
  console.log(`[qa +${((Date.now() - tRun0) / 1000).toFixed(1)}s]   probe ${label} ok (${((Date.now() - tp) / 1000).toFixed(2)}s)`);
  return (r.stdout || '') + (r.stderr || '');
}

try {
  const blacks = [...probe('blackdetect', 'blackdetect=d=0.08:pix_th=0.06').matchAll(/black_start:([\d.]+) black_end:([\d.]+)/g)].map((m) => [+m[1], +m[2]]);
  const frz = []; let fs0 = null;
  for (const m of probe('freezedetect', 'freezedetect=n=-55dB:d=0.5').matchAll(/freeze_(start|end): ([\d.]+)/g)) { if (m[1] === 'start') fs0 = +m[2]; else { frz.push([fs0, +m[2]]); fs0 = null; } }
  if (fs0 != null) frz.push([fs0, to - from]);
  for (let i = frz.length - 1; i >= 0; i--) if (blacks.some(([s, e]) => frz[i][0] >= s - 0.09 && frz[i][1] <= e + 0.13)) frz.splice(i, 1);
  const cutTxt = probe('scene-cuts', `select='gt(scene,${opt('--cut', '0.32')})',metadata=print:file=-`);
  const cuts = [...cutTxt.matchAll(/pts_time:([\d.]+)/g)].map((m) => Math.round((+m[1] + from) * fps));
  const fr = (s) => Math.round((s + from) * fps);

  state.metrics.blackStretches = blacks.length;
  state.metrics.frozenStretches = frz.length;
  state.metrics.hardCuts = cuts.length;
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

  const ys = [...probe('signalstats', 'fps=1,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-').matchAll(/YAVG=([\d.]+)/g)].map((m) => Math.round(+m[1]));
  state.metrics.yavgPerSec = ys;
  say(`brightness per second (YAVG 0–255): ${ys.join(' ')}`);
  endStage('4/5:ffmpeg-metrics', tS4, `blacks=${blacks.length} freezes=${frz.length} cuts=${cuts.length}`);
} catch (err) {
  failStage('4/5:ffmpeg-metrics', tS4, err.message || String(err));
  process.exit(1);
}

// ---- Stage 5: contact sheet & final report -----------------------------------------------------------------
const tS5 = beginStage('5/5:contact-sheet');
try {
  const sheet = path.join(outDir, 'qa_sheet.jpg');
  const r = spawnSync(ff, ['-hide_banner', '-loglevel', 'error', '-y', '-i', draft, '-vf', `fps=2,scale=320:-2,tile=8x${Math.max(1, Math.ceil((to - from) * 2 / 8))}`, '-frames:v', '1', sheet], { encoding: 'utf8', timeout: stageTimeoutMs });
  if (r.error || r.status) throw new Error(r.error ? r.error.message : (r.stderr || `exit ${r.status}`));
  state.metrics.contactSheet = sheet;
  say(`contact sheet (2 fps): ${sheet}`);
  mot.lines.forEach(say);
  if (mot.fail) bad++;
  say((bad ? `RESULT: ${bad} problem group(s) to fix${mot.fail ? (mot.fails ? `, the motion lint's ${mot.fails} FAIL among them` : ', the motion lint that did not run among them') : ''}`
    : `RESULT: mechanical checks and the motion lint pass — now look (Gate B1)${mot.sheet ? ', the curve sheet first' : ''}`) + warnTag(mot) + mot.tag);
  state.status = 'completed';
  state.passed = bad === 0;
  endStage('5/5:contact-sheet', tS5, bad ? `FAILED (${bad} issue group(s))` : 'PASS');
} catch (err) {
  failStage('5/5:contact-sheet', tS5, err.message || String(err));
  process.exit(1);
}

process.exit(bad ? 1 : 0);
