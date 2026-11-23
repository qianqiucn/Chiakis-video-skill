/* lib/motion/probe.js — curve probes: a segment names the moves it draws, so their curves can be plotted (motion library, R1)
 *
 * Library ids: curve.probe
 *   How many probes a passage needs and of which moves: motion-library «Curve sheet». scripts/motion_lint.mjs --curves
 *   samples every probe and draws tools/out/motion/curves.svg.
 *
 * API (frozen in the library plan; extras marked +):
 *   T3.motionProbe(id, f0, f1, fn, meta?) → fn
 *       Registers (or replaces) probe `id` over frames f0..f1. fn(f) returns the pose drawn at frame f (fractional f allowed):
 *       { x?, y?, s?, r?, o? } in px, px, scale, degrees, opacity; other number fields (blur, …) are kept too.
 *       Register in init() or at file load, and pass the SAME function render() draws with, so the sheet shows what is drawn:
 *         const title = (f) => T3.mv.arrive(f, { at: 40, from: { x: -260 } });
 *         T3.motionProbe('title.arrive', 36, 64, title, { kind: 'arrive', seg: 'intro_x' });   // in render: T3.mv.css(el, title(f))
 *       + meta (optional): { kind: 'arrive' | 'exit' | 'camera' | 'transition' | 'other', seg: '<segment id>' }.
 *       Returning fn lets one line both define and register the move.
 *   T3.motionProbe.sample(id, step = 0.25) → [{ f, x?, y?, … }, …]
 *       Every `step` frames from f0 to f1, both ends included. Throws T3MotionError when the id is unknown, fn throws, or
 *       a sample is not an object with at least one finite number (NaN and ±Infinity fail).
 *   + T3.motionProbe.ids() → [id, …] in registration order.
 *   + T3.motionProbe.all(step = 0.25) → { id: { f0, f1, step, meta, samples } or { f0, f1, meta, error } }: JSON-safe; a probe
 *       that throws is reported in its entry, not thrown (for the lint, which fails it).
 *   window.__T3_PROBES = { id: { id, f0, f1, fn, meta } }: the registry (tools read it; segments write only through T3.motionProbe).
 *   Sampling only calls fn: it never seeks the page or touches the DOM. fn must be pure in f (no state, no Math.random).
 *
 * Source: house 2D motion curve-sheet probe helper
 *   (window.__GEM_PRINT_V10.curves(), quarter-frame samples) and its reader work\gem_print\v9_curves.mjs (via scripts/_cdp.mjs).
 * Approval: house rule (H): the 11-18 curve rule asks for a curve sheet before delivery (in the skill since 2026-11-21, D1).
 *   Tests: assets/examples/motion/test_moves.mjs (probe part).
 */
(function () {
  'use strict';
  const err = (msg) => Object.assign(new Error('lib/motion/probe.js: ' + msg), { name: 'T3MotionError' });
  const T3 = window.T3;
  if (!T3) throw err('engine.js is not loaded: load it first (motion-library «Setup»)');
  const reg = window.__T3_PROBES || (window.__T3_PROBES = {});
  const order = Object.keys(reg);

  function motionProbe(id, f0, f1, fn, meta) {
    if (typeof id !== 'string' || !id.trim()) throw err('T3.motionProbe: the id must be a non-empty string');
    if (!Number.isFinite(f0) || !Number.isFinite(f1) || !(f1 > f0)) throw err(`T3.motionProbe("${id}"): need finite frames with f1 > f0`);
    if (typeof fn !== 'function') throw err(`T3.motionProbe("${id}"): fn must be a function of the frame`);
    if (!reg[id]) order.push(id);
    reg[id] = { id, f0, f1, fn, meta: meta || null };
    return fn;
  }

  function pose(id, f, p) {
    if (!p || typeof p !== 'object') throw err(`probe "${id}" at f${f}: fn returned ${p === null ? 'null' : typeof p}, not a pose object`);
    const row = { f };
    let n = 0;
    for (const k in p) {
      const v = p[k];
      if (typeof v !== 'number') continue;
      if (!Number.isFinite(v)) throw err(`probe "${id}" at f${f}: ${k} = ${v}`);
      row[k] = v; n++;
    }
    if (!n) throw err(`probe "${id}" at f${f}: the pose has no number fields ({ x, y, s, r, o })`);
    return row;
  }

  motionProbe.sample = function (id, step) {
    const P = reg[id];
    if (!P) throw err(`T3.motionProbe.sample: no probe "${id}"`);
    step = step == null ? 0.25 : step;
    if (!(step > 0)) throw err('T3.motionProbe.sample: step must be > 0');
    const n = Math.floor((P.f1 - P.f0) / step + 1e-9), rows = [];
    for (let i = 0; i <= n; i++) {
      const f = P.f0 + i * step;
      rows.push(pose(id, f, P.fn(f)));
    }
    if (P.f0 + n * step < P.f1 - 1e-9) rows.push(pose(id, P.f1, P.fn(P.f1)));
    return rows;
  };
  motionProbe.ids = () => order.filter((id) => reg[id]);
  motionProbe.all = function (step) {
    const out = {};
    for (const id of motionProbe.ids()) {
      const P = reg[id];
      try { out[id] = { f0: P.f0, f1: P.f1, step: step == null ? 0.25 : step, meta: P.meta, samples: motionProbe.sample(id, step) }; }
      catch (e) { out[id] = { f0: P.f0, f1: P.f1, meta: P.meta, error: String((e && e.message) || e) }; }
    }
    return out;
  };

  T3.motionProbe = motionProbe;
  if (window.__T3_MOTION && window.__T3_MOTION.modules) window.__T3_MOTION.modules.push('probe');
})();
