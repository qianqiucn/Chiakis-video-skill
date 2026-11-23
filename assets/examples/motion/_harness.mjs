// _harness.mjs — loads the template's scripts into a Node vm context that stands in for the page, for the lib/motion tests.
// No browser: engine.js, GSAP and lib/motion only need `window` and timers at load. Node >= 22 only.
import vm from 'node:vm';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const SKILL = path.resolve(HERE, '../../..');
export const TPL = path.join(SKILL, 'assets', 'template');
export const read = (rel) => fs.readFileSync(path.join(SKILL, rel), 'utf8');

// opts: which scripts to load, in the page's order (motion-library «Setup»)
export function page(opts = {}) {
  const o = Object.assign({ engine: true, gsap: true, customEase: true, bridge: true, motion: ['ez', 'probe', 'moves'] }, opts);
  const ctx = { console, performance, setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {} };
  ctx.window = ctx; ctx.self = ctx; ctx.addEventListener = () => {};
  vm.createContext(ctx);
  const load = (rel) => vm.runInContext(fs.readFileSync(path.join(TPL, rel), 'utf8'), ctx, { filename: rel });
  ctx.__load = load;
  if (o.engine) load('engine.js');
  if (o.gsap) load('lib/gsap/gsap.min.js');
  if (o.customEase) load('lib/gsap/CustomEase.min.js');
  if (o.bridge && o.gsap && o.engine) load('lib/gsap-bridge.js');
  for (const m of o.motion) load(`lib/motion/${m}.js`);
  return ctx;
}

// a tiny checker: every check prints one line; done() prints the tally and sets the exit code
export function tally(title) {
  let pass = 0, fail = 0;
  console.log(`# ${title}`);
  return {
    ok(name, cond, detail = '') { if (cond) pass++; else fail++; console.log(`${cond ? 'ok  ' : 'FAIL'} ${name}${detail ? '  ' + detail : ''}`); return cond; },
    throws(name, fn, errName = 'T3MotionError') {
      let e = null; try { fn(); } catch (x) { e = x; }
      return this.ok(name, !!e && e.name === errName, e ? `${e.name}: ${String(e.message).slice(0, 110)}` : 'no error thrown');
    },
    done() { console.log(`# ${title}: ${pass} passed, ${fail} failed`); if (fail) process.exitCode = 1; return fail; },
    end() { return this.done(); },
  };
}

export const loadTemplate = () => page({ motion: ['ez', 'probe', 'moves', 'blur', 'timing', 'her2d'] });

// frames from a to b every step, plus extra exact frames; fractional frames are sub-frame samples
export function grid(a, b, step, extra = []) {
  const n = Math.round((b - a) / step), out = [];
  for (let i = 0; i <= n; i++) out.push(a + i * step);
  return out.concat(extra);
}
