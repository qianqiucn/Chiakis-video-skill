// Shared helper: one persistent headless Chrome page, driven over the DevTools protocol.
// The page is loaded ONCE; each frame is just T3.seek(t) + a screenshot — no browser restart,
// no reload, no image re-decoding (the old per-frame `chrome --screenshot` launched Chrome
// for every single frame). Needs Node ≥ 22 (global fetch + WebSocket).
//
// Render errors. A segment's render(t) runs inside T3.seek, which the tools call through Runtime.evaluate; Chrome
// returns an exception thrown there in the evaluate reply, NOT as a Runtime.exceptionThrown event, so this helper
// used to drop it, and the frame came out with the broken layer half drawn and every layer above it (higher z)
// left as it was on the previous frame. Now a hook installed before the page's own scripts wraps each segment given
// to T3.register: a throw from its init or render is recorded with the segment id, the frame and file:line, then
// re-thrown, so the page behaves exactly as in the browser. Every seek the helper makes collects them:
//   pg.renderErrors  every record {seg, phase, frame, msg, where}
//   pg.errors        page errors (uncaught exceptions, console.error, a failed evaluate) plus ONE line per kind of
//                    render error, so any caller that prints pg.errors shows it
//   errorReport([pg, …]) / reportLines(rep)  the grouped report snap / render_fast / qa print (frames as runs)
//   pg.scan(f0, f1, fps)  seeks every frame without screenshots (qa.mjs --errors-only, or with --draft)
//
// Motion line (references/motion-library.md «Setup»). After the settle, every page that runs the T3 engine prints ONE
// line per process (render_fast's workers share it): strict or legacy, whether GSAP and T3.EZ are loaded, the static
// lint's FAIL / WARN / NOTE counts (WARN only when there is one; scripts/motion_lint.mjs, no browser, ~10 ms) and the
// command for the full check, e.g.
//   motion: strict page, GSAP ok, lint 0 fail / 2 notes (node <skill>/scripts/motion_lint.mjs …\web\index.html)
// It only prints: it is never a render or page error and changes no exit code (snap.mjs and render_fast.mjs exit as
// before); qa.mjs is the tool that fails on a FAIL (it passes motion: false and prints its own lint). pg.motion holds
// { res, rt, line } (null on a page without the engine, or with motion: false). If motion_lint.mjs is missing or throws,
// the line says so and the page works as before.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

import { spawnSync } from 'node:child_process';

function detectChrome() {
  for (const env of [process.env.CHIAKI_CHROME, process.env.CHROME_PATH, process.env.QCRV_CHROME]) {
    if (env && fs.existsSync(env)) return env;
  }
  const candidates = process.platform === 'win32'
    ? [
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        path.join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe'),
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
        'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
      ]
    : process.platform === 'darwin'
    ? [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      ]
    : ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
  for (const p of candidates) if (p && fs.existsSync(p)) return p;
  for (const bin of ['google-chrome', 'chromium', 'chromium-browser', 'chrome']) {
    const r = spawnSync(process.platform === 'win32' ? 'where' : 'which', [bin], { encoding: 'utf8' });
    const hit = (r.stdout || '').split(/\r?\n/).map((s) => s.trim()).find((s) => s && fs.existsSync(s));
    if (hit) return hit;
  }
  return candidates[0];
}

export const CHROME = detectChrome();
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let _ffCache = null;
export function findFfmpeg() {
  if (_ffCache) return _ffCache;
  for (const env of [process.env.CHIAKI_FFMPEG, process.env.FFMPEG_PATH, process.env.QCRV_FFMPEG]) {
    if (env && fs.existsSync(env)) return (_ffCache = env);
  }
  const probe = spawnSync(process.platform === 'win32' ? 'where' : 'which', ['ffmpeg'], { encoding: 'utf8' });
  const inPath = (probe.stdout || '').split(/\r?\n/).map((s) => s.trim()).find((s) => s && fs.existsSync(s));
  if (inPath) return (_ffCache = inPath);
  for (const py of process.platform === 'win32' ? ['python', 'py'] : ['python3', 'python']) {
    const r = spawnSync(py, ['-c', 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'], { encoding: 'utf8' });
    const hit = (r.stdout || '').trim();
    if (r.status === 0 && hit && fs.existsSync(hit)) return (_ffCache = hit);
  }
  return (_ffCache = 'ffmpeg');
}

/** frames spec "0-100:2,410-434,600" → [0,2,…,100,410,…,434,600] */
export function parseFrames(spec) {
  const out = [];
  for (const part of String(spec).split(',')) {
    const m = /^\s*(\d+)(?:-(\d+))?(?::(\d+))?\s*$/.exec(part);
    if (!m) throw new Error('bad frame spec: ' + part);
    const a = +m[1], b = m[2] ? +m[2] : a, s = m[3] ? +m[3] : 1;
    for (let f = a; f <= b; f += s) out.push(f);
  }
  return out;
}

/** render_fast's worker count: --workers (2 when missing, not a number or below 1), at most QCRV_MAX_WORKERS (the cap
 *  run_queue.py sets for one web slot; ignored unless >= 1); never below 1, so a render always has a worker */
export function workerCount(arg, capEnv = process.env.CHIAKI_MAX_WORKERS || process.env.QCRV_MAX_WORKERS) {
  const c = Math.floor(+capEnv), cap = c >= 1 ? c : Infinity;
  const w = Math.floor(+arg), want = Number.isFinite(w) && w >= 1 ? w : 2;
  return Math.max(1, Math.min(want, cap));
}

// Runs in the page before any of its scripts (Page.addScriptToEvaluateOnNewDocument). Changes nothing the page does:
// every wrapped call re-throws what it caught.
function pageHook() {
  if (window.__cv) return;
  const Q = (window.__cv = { fails: [], hooked: false, seen: undefined });
  // the engine as the page sees it: window.T3, or a top-level let/const T3 (not on window, so the setter below never
  // sees it and its segments go unwrapped, but seek still works)
  const T3of = () => window.T3 || (typeof T3 !== 'undefined' ? T3 : undefined);
  const fps = () => (T3of() && T3of().FPS) || (window.T3_CONFIG && window.T3_CONFIG.fps) || 24;
  const frameOf = (t) => (typeof t === 'number' && isFinite(t) ? Math.floor(t * fps() + 1e-6) : null);
  const where = (e) => {
    for (const s of String((e && e.stack) || '').split('\n').slice(1)) {
      if (s.includes('<anonymous>')) continue;
      const m = /([^\s()]+):(\d+):(\d+)\)?\s*$/.exec(s);
      if (!m) continue;
      let f = m[1]; try { f = decodeURI(f); } catch {}
      return f.split(/[\\/]/).slice(-2).join('/') + ':' + m[2] + ':' + m[3];
    }
    return '';
  };
  const record = (e, seg, phase, t) => {
    if (Q.fails.length > 20000) return;                  // a page broken on every frame of a long film: enough said
    const msg = e && typeof e === 'object' && 'message' in e ? (e.name || 'Error') + ': ' + e.message : 'throw ' + String(e);
    Q.fails.push({ seg: String(seg), phase, frame: frameOf(t), msg, where: where(e) });
    Q.seen = e;
  };
  const wrapSeg = (s) => {
    if (!s || typeof s !== 'object') return;
    for (const k of ['init', 'render']) {
      const fn = s[k];
      if (typeof fn !== 'function' || fn.__cvWrap) continue;
      const w = function (t) {
        try { return fn.apply(this, arguments); }
        catch (e) { if (e !== Q.seen) record(e, s.id == null ? '?' : s.id, k, k === 'render' ? t : null); throw e; }
      };
      w.__cvWrap = 1;
      try { s[k] = w; } catch {}
    }
  };
  const hookT3 = (x) => {
    if (!x || typeof x !== 'object' || typeof x.register !== 'function' || x.register.__cvWrap) return;
    const reg = x.register;
    const r = function (s) { wrapSeg(s); return reg.apply(this, arguments); };
    r.__cvWrap = 1;
    try { x.register = r; Q.hooked = true; } catch {}
  };
  let v;
  try { Object.defineProperty(window, 'T3', { configurable: true, enumerable: true, get() { return v; }, set(x) { v = x; hookT3(x); } }); } catch {}
  Q.seek = (t) => {
    Q.seen = undefined;
    try { T3of().seek(t); } catch (e) { if (e !== Q.seen) record(e, '(engine)', 'seek', t); }
    Q.seen = undefined;
  };
  Q.drain = () => Q.fails.splice(0);
  Q.scan = (f0, f1, rate) => { for (let f = f0; f <= f1; f++) Q.seek((f + 0.5) / rate); return Q.drain(); };
}

export const failKey = (r) => `${r.seg}|${r.phase}|${r.msg}|${r.where}`;
function failLine(r) {
  const who = r.seg === '(engine)' ? 'T3.seek threw outside any segment (engine)' : `segment "${r.seg}" ${r.phase === 'init' ? 'init(layer)' : 'render(t)'} threw`;
  return `${who}, ${r.frame == null ? 'at load' : 'first at f' + r.frame}: ${r.msg}${r.where ? '  @ ' + r.where : ''}`;
}
/** frame numbers → "f24–71, f100" */
export function frameRuns(frames, max = 12) {
  const fs_ = [...new Set(frames)].sort((a, b) => a - b), out = [];
  for (let i = 0; i < fs_.length; i++) {
    let j = i; while (j + 1 < fs_.length && fs_[j + 1] === fs_[j] + 1) j++;
    out.push(i === j ? `f${fs_[i]}` : `f${fs_[i]}–${fs_[j]}`); i = j;
  }
  return out.length > max ? out.slice(0, max).join(', ') + `, … (${out.length - max} more runs)` : out.join(', ');
}

/** Group the errors of one or more pages (open or closed; also the plain objects render_fast --errors-json writes).
 *  → { render: [{seg, phase, msg, where, frames}], page: [text], renderFrames, count } */
export function errorReport(pages) {
  const groups = new Map(), lines = new Set(), msgs = new Set(), errs = []; let notReady = 0;
  for (const p of pages) {
    for (const r of p.renderErrors || []) {
      const k = failKey(r);
      if (!groups.has(k)) groups.set(k, { seg: r.seg, phase: r.phase, msg: r.msg, where: r.where, frames: [] });
      if (r.frame != null) groups.get(k).frames.push(r.frame);
      msgs.add(r.msg);
    }
    for (const l of p.renderLines || []) lines.add(l);
    errs.push(...(p.errors || []));
    if (p.ready === false) notReady++;
  }
  const render = [...groups.values()];
  render.forEach((g) => { g.frames = [...new Set(g.frames)].sort((a, b) => a - b); });
  const page = [...new Set(errs)].filter((e) => !lines.has(e) && !msgs.has(String(e).split('\n')[0].replace(/^Uncaught\s+/, '').trim()));
  if (notReady) page.push('T3_READY never became true within 15 s: boot threw or a T3.hold() is stuck — frames may be blank or fall back');
  const renderFrames = new Set(render.flatMap((g) => g.frames)).size;
  return { render, page, renderFrames, count: render.length + page.length };
}
/** the report as printable lines (empty when clean) */
export function reportLines(rep) {
  const out = [];
  if (rep.render.length) {
    out.push(`RENDER ERRORS: ${rep.render.length} kind(s)${rep.renderFrames ? ` on ${rep.renderFrames} frame(s)` : ''} — on those frames that layer stopped part-way and every layer above it (higher z) was not drawn:`);
    for (const g of rep.render) {
      const who = g.seg === '(engine)' ? 'engine (T3.seek, outside any segment)' : `segment "${g.seg}" ${g.phase === 'init' ? 'init(layer)' : 'render(t)'}`;
      out.push(`  ${who}: ${g.msg}${g.where ? '  @ ' + g.where : ''}`);
      out.push(`      ${g.frames.length ? frameRuns(g.frames) + ` (${g.frames.length} frame${g.frames.length > 1 ? 's' : ''})` : 'at load'}`);
    }
  }
  if (rep.page.length) { out.push('PAGE ERRORS:'); rep.page.forEach((e) => out.push('  ' + e)); }
  return out;
}

// ---- the motion line (header «Motion line»): printing only, never an error, never an exit code
let lintMod = null;
const LINT = fileURLToPath(new URL('./motion_lint.mjs', import.meta.url)).split(path.sep).join('/');
const motionOnce = new Map();                           // page path → Promise<{ res, rt, line } | null>, one line per process
const firstLine = (e) => String((e && e.message) || e).split('\n')[0].slice(0, 160);
async function motionStatus(pageFile, quietEval) {
  // only a page that runs the T3 engine (not fonts.py's specimen sheets)
  if (!(await quietEval('!!(window.T3 || (typeof T3 !== "undefined" && T3))'))) return null;
  const page = path.resolve(pageFile);
  let line, res = null, rt = null;
  try {
    lintMod ||= import('./motion_lint.mjs');
    const L = await lintMod;
    res = L.staticScan(page);                           // synchronous, never throws
    rt = await L.runtimeState({ evaluate: quietEval });
    line = res.error ? `motion: the lint could not finish (${firstLine(res.error)}); run node ${LINT} ${page}` : L.motionLine(res, rt);
  } catch (e) {
    line = `motion: not checked, scripts/motion_lint.mjs did not load (${firstLine(e)})`;
  }
  console.log(line);
  return { res, rt, line };
}

export async function openPage(pageFile, { query = '', settle = 1200, width = 1920, height = 1080, onRenderError = null, motion = true } = {}) {
  const held = process.env.CHIAKI_QUEUE_HELD || process.env.QCRV_QUEUE_HELD || '';
  if (!/(^|,)web:/.test(held)) console.error('[_cdp] headless Chrome started outside scripts/run_queue.py web: run the command through it (references/production.md §2)');
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'chiaki-cdp-'));
  // GPU raster/compositing by default (D3D11 ANGLE on Windows); CHIAKI_CPU=1 forces software (--disable-gpu).
  const useCpu = process.env.CHIAKI_CPU === '1' || process.env.QCRV_CPU === '1';
  const gpu = useCpu ? ['--disable-gpu']
    : process.platform === 'win32'
    ? ['--use-angle=d3d11', '--enable-gpu-rasterization', '--ignore-gpu-blocklist']
    : ['--enable-gpu-rasterization', '--ignore-gpu-blocklist'];
  const proc = spawn(CHROME, ['--headless=new', ...gpu, '--hide-scrollbars', '--mute-audio',
    `--user-data-dir=${prof}`, '--allow-file-access-from-files', '--remote-debugging-port=0', '--disable-lcd-text',
    `--window-size=${width},${height}`, 'about:blank'], { stdio: 'ignore' });
  let port = 0;
  for (let i = 0; i < 150 && !port; i++) {
    try { port = +fs.readFileSync(path.join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch {}
    if (!port) await sleep(100);
  }
  if (!port) { proc.kill(); throw new Error('Chrome did not start'); }
  let wsUrl = null;
  for (let i = 0; i < 100 && !wsUrl; i++) {
    try { const j = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); const p = j.find((x) => x.type === 'page'); if (p) wsUrl = p.webSocketDebuggerUrl; } catch {}
    if (!wsUrl) await sleep(100);
  }
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pend = new Map(); const errors = [];
  const renderErrors = [], renderLines = new Set(), seenKinds = new Set();
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); return; }
    if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a) => a.value ?? a.description).join(' '));
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  const rawEval = (expression) => send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  function addFails(list) {
    for (const r of Array.isArray(list) ? list : []) {
      renderErrors.push(r);
      const k = failKey(r);
      if (seenKinds.has(k)) continue;
      seenKinds.add(k);
      const line = failLine(r); renderLines.add(line); errors.push(line);
      if (onRenderError) onRenderError(r, line);
    }
  }
  const drain = async () => addFails((await rawEval('window.__cv ? window.__cv.drain() : []')).result?.value);
  // an exception inside the expression comes back in the reply, never as an event: record it (with the segment
  // records it produced, when it came from a seek) instead of returning undefined in silence
  const evaluate = async (expression) => {
    const r = await rawEval(expression);
    if (r.exceptionDetails) {
      const before = renderErrors.length;
      await drain();
      if (renderErrors.length === before) errors.push('evaluate threw: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
      return undefined;
    }
    return r.result?.value;
  };

  await send('Runtime.enable'); await send('Page.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `(${pageHook})();` });
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
  const url = 'file:///' + path.resolve(pageFile).replace(/\\/g, '/') + '?still=1&bare=1' + query;
  await send('Page.navigate', { url });
  let ready = false;
  for (let i = 0; i < 300; i++) { if (await evaluate('window.T3_READY===true && document.readyState==="complete"')) { ready = true; break; } await sleep(50); }
  // DOM images + fonts; images created in code (new Image(), textures) get the settle time
  await evaluate('Promise.all([...document.images].map(i=>i.complete?0:new Promise(r=>{i.addEventListener("load",r);i.addEventListener("error",r);}))).then(()=>document.fonts.ready).then(()=>1)');
  await sleep(settle);
  await drain();                                        // init() and the first draw at boot
  // the motion line: rawEval, so nothing it asks can land in errors (which would change snap's or render_fast's exit code)
  let motionInfo = null;
  if (motion !== false) {
    const quietEval = async (x) => { try { const r = await rawEval(x); return r.exceptionDetails ? undefined : r.result?.value; } catch { return undefined; } };
    const key = path.resolve(pageFile).toLowerCase();
    if (!motionOnce.has(key)) motionOnce.set(key, motionStatus(pageFile, quietEval).catch(() => null));
    motionInfo = await motionOnce.get(key);
  }

  async function shot(t, { format = 'jpeg', quality = 95, scale = 1, label = null } = {}) {
    const lab = label == null ? '' : `;(function(){let d=document.getElementById('qcrv-label');if(!d){d=document.createElement('div');d.id='qcrv-label';d.style.cssText='position:fixed;left:8px;top:6px;z-index:99999;font:700 30px Consolas,monospace;color:#ff0;background:rgba(0,0,0,.6);padding:2px 8px';document.body.appendChild(d);}d.textContent=${JSON.stringify(String(label))};})()`;
    addFails(await evaluate(`(window.__cv?window.__cv.seek(${t}):T3.seek(${t}))${lab};new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(window.__cv?window.__cv.drain():[]))))`));
    const p = { format, captureBeyondViewport: false };
    if (format === 'jpeg') p.quality = quality;
    if (scale !== 1) p.clip = { x: 0, y: 0, width, height, scale };
    return Buffer.from((await send('Page.captureScreenshot', p)).data, 'base64');
  }
  /** seek every frame f0..f1 (no paint, no screenshot) and collect render errors; returns the frame count */
  async function scan(f0, f1, fps = 24, chunk = 240) {
    for (let a = f0; a <= f1; a += chunk) addFails(await evaluate(`window.__cv.scan(${a}, ${Math.min(f1, a + chunk - 1)}, ${fps})`));
    return Math.max(0, f1 - f0 + 1);
  }
  async function close() { try { ws.close(); } catch {} proc.kill(); await sleep(300); try { fs.rmSync(prof, { recursive: true, force: true }); } catch {} }
  const hooked = !!(await evaluate('!!(window.__cv && window.__cv.hooked)'));
  if (ready && !hooked) errors.push('render-error hook not installed (T3.register not seen): render errors are reported without their segment');
  return { send, evaluate, shot, scan, drain, errors, renderErrors, renderLines, ready, hooked, close, motion: motionInfo };
}
