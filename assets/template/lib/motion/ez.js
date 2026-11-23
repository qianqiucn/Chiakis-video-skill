/* lib/motion/ez.js — the house motion curves, on GSAP (motion library, release R1)
 *
 * Library ids: curve.house, move.pop, move.drift
 *   curve.house is this table; move.pop calls T3.EZ.back / T3.EZ.elastic; move.drift calls T3.EZ.sine.
 *   Index: references/motion-library.md. Which curve fits which genre, and for how many frames: style-grammar §6b.
 *
 * API (frozen in the library plan; every curve clamps k to [0, 1] first, then returns the eased value):
 *   T3.EZ.snap(k)      CustomEase "M0,0 C0.05,0.9 0.1,1 1,1": ≈ 82 % of the travel by k = 1/6, then a long landing (arrivals)
 *   T3.EZ.expoOut(k)   GSAP expo.out                arrivals
 *   T3.EZ.p4out(k)     GSAP power4.out              arrivals
 *   T3.EZ.quintOut(k)  GSAP quint.out               the same numbers as power4.out (GSAP names one curve twice)
 *   T3.EZ.p3in(k)      GSAP power3.in               exits that speed up into the cut
 *   T3.EZ.expoIn(k)    GSAP expo.in                 exits, throws
 *   T3.EZ.back(k)      GSAP back.out(1.7)           pops
 *   T3.EZ.elastic(k)   GSAP elastic.out(1,0.45)     a heavy pop, rarely
 *   T3.EZ.sine(k)      GSAP sine.inOut              background drift and calm genres only (never an arrival: zero speed at both ends)
 *   T3.EZ.roll(k)      CustomEase "M0,0 C0.55,0 0.35,1 1,1": things crossing the frame (a roller, a scan bar, a sweep)
 *   T3.EZ.fly(k)       CustomEase "M0,0 C0.45,0 0.15,1 1,1": a lift-off that speeds away, then a long landing
 *   T3.EZ.bump(k)      back(k) − p4out(k): 0 → a small swell → 0, the after-push of a landing (both start on the same slope)
 *   T3.EZ.get(x)       x = a name above, any GSAP ease string ('power2.in', 'steps(8)'), a path "M0,0 C…", or a T3.EZ curve
 *                      → a cached ease that clamps k; an unknown name or any other function throws T3MotionError
 *                      (a hand-written ease function is refused: curves come from GSAP)
 *   T3.EZ.at(f, f0, dur, name = 'snap')   get(name)(k) with k = (f − f0) / dur, so k(f0) = 0 and k(f0 + dur) = 1;
 *                      dur <= 0 is a cut at f0 (0 before, 1 from f0)
 *   T3.EZ.names        the table's names, in the order above
 *   Note: GSAP 3.15's expo is normalised to meet 0 and 1 exactly, so expo.out is not the classic 1 − 2^(−10k)
 *   (up to 0.8 % of the travel apart). The product-film rise keeps the classic exponential curve: lib/motion/moves.js T3.mv.rise.
 *
 * Load order (motion-library «Setup»): engine.js, lib/gsap/gsap.min.js, lib/gsap/CustomEase.min.js (+ SplitText),
 *   lib/gsap-bridge.js, then this file, lib/motion/probe.js, lib/motion/moves.js, then the segments.
 *   A good load sets window.__T3_MOTION = { lib: 1, gsap: true, modules: ['ez', …] }. Without engine.js, gsap or
 *   CustomEase it sets { lib: 1, gsap: false, error } and throws T3MotionError, so the page fails at load, not mid-film.
 *   Only the ease functions are used (no timeline, no ticker), so a segment's render(t) stays a pure function of t.
 *
 * Source: house 2D motion curve table (named GSAP CustomEase & standard eases)
 *   Curve families and timings are documented in references/style-grammar.md §6b.
 * Approval: house rule (H): references/style-grammar.md §6b.
 *   The table itself is tooling. Tests: assets/examples/motion/test_ez.mjs (equal to gsap.parseEase on a k grid).
 */
(function () {
  'use strict';
  const err = (msg) => Object.assign(new Error('lib/motion/ez.js: ' + msg), { name: 'T3MotionError' });
  const fail = (msg) => {
    const e = err(msg + ' (motion-library «Setup»)');
    window.__T3_MOTION = { lib: 1, gsap: false, error: e.message };
    throw e;
  };
  const T3 = window.T3, g = window.gsap, C = window.CustomEase;
  if (!T3) fail('engine.js is not loaded: load it first');
  if (!g || typeof g.parseEase !== 'function') fail('GSAP is not loaded: add lib/gsap/gsap.min.js before lib/motion/ez.js');
  if (!C || typeof C.create !== 'function') fail('CustomEase is not loaded: add lib/gsap/CustomEase.min.js before lib/motion/ez.js');

  const cl = (k) => (k < 0 ? 0 : k > 1 ? 1 : k);
  const wrap = (fn) => { const e = (k) => fn(cl(k)); e.__t3ez = true; return e; };
  const pe = (name) => wrap(g.parseEase(name));
  const ce = (id, path) => wrap(C.create(id, path));

  const table = {
    snap: ce('t3Snap', 'M0,0 C0.05,0.9 0.1,1 1,1'),
    expoOut: pe('expo.out'),
    p4out: pe('power4.out'),
    quintOut: pe('quint.out'),
    p3in: pe('power3.in'),
    expoIn: pe('expo.in'),
    back: pe('back.out(1.7)'),
    elastic: pe('elastic.out(1,0.45)'),
    sine: pe('sine.inOut'),
    roll: ce('t3Roll', 'M0,0 C0.55,0 0.35,1 1,1'),
    fly: ce('t3Fly', 'M0,0 C0.45,0 0.15,1 1,1'),
  };
  const names = Object.keys(table);
  table.bump = wrap((k) => table.back(k) - table.p4out(k));

  const cache = new Map();
  let nPath = 0;   // ids for path curves: in call order, so the same page gives the same ids
  function get(x) {
    if (typeof x === 'function') {
      if (x.__t3ez) return x;
      throw err('T3.EZ.get: a hand-written ease function is refused; give a T3.EZ name, a GSAP ease string or a path "M0,0 C…"');
    }
    if (typeof x !== 'string' || !x.trim()) throw err('T3.EZ.get: give a curve name, a GSAP ease string or a path "M0,0 C…"');
    if (Object.prototype.hasOwnProperty.call(table, x)) return table[x];
    let e = cache.get(x);
    if (e) return e;
    if (/^\s*M/i.test(x)) e = ce('t3Path' + ++nPath, x);
    else {
      const fn = g.parseEase(x);
      if (typeof fn !== 'function') throw err(`T3.EZ.get: unknown ease "${x}" (T3.EZ.names, or a GSAP ease name)`);
      e = wrap(fn);
    }
    cache.set(x, e);
    return e;
  }
  function at(f, f0, dur, name) {
    return get(name == null ? 'snap' : name)(dur > 0 ? (f - f0) / dur : f >= f0 ? 1 : 0);
  }

  T3.EZ = Object.freeze(Object.assign({}, table, { get, at, names: Object.freeze(names.concat('bump')) }));
  window.__T3_MOTION = { lib: 1, gsap: true, modules: ['ez'] };
})();
