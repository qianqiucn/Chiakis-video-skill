/* lib/motion/timing.js — approved timing mechanisms as pure frame functions (motion library, release R2)
 *
 * Library ids: time.twos, time.relief, fx.shake, trans.tail
 *   Index: references/motion-library.md (the entries' «Timing (here)» numbers are this file's defaults).
 *
 * Every function is pure in the frame: frame (or progress) in, a number or a plain object out, nothing kept between
 * calls, no clock, no Math.random (the shake's jitter is engine.js's hash T3.rand). Load after engine.js; nothing else
 * is needed at load. T3.decay (lib/choreo.js) is optional and looked up only when T3.tail is given a { v0, h } tail:
 * without choreo.js that call throws T3MotionError.
 * These are approved shapes kept as they are, per-frame tables and steps included (motion-library: approved code is
 * lifted, never re-curved); a segment that calls them is not hand-rolling eases.
 *
 * API (frozen in the library plan; extras marked +):
 *   T3.twos(f, anchors, { n = 2, end, reach = n + 1 }) → the frame to draw (the stepped clock)
 *       time.twos: the whole picture updates every n frames (held frames repeat the step's first frame), restarting at
 *       each anchor so a landing frame starts a step. anchors = the run's first frame, or [first, landing, …] (any
 *       order; the earliest is where the run starts, so leave out frames before it). Before the run, and from `end`
 *       (exclusive, default never) on, it returns f. Fractional f is fine.
 *       One anchor is the MV's clock: f < f0 ? f : f0 + floor((f − f0)/n)·n.
 *       Multi-anchor stepped clock (pass landing frames to re-anchor steps): an anchor no more than
 *       `reach` frames after a step's start becomes the next step, so with the default reach = n + 1 a one-frame
 *       leftover before an anchor is held by the step before it.
 *       + reach (>= n): reach = n cuts the step before an anchor short instead (a one-frame step).
 *       Only for a PV remake whose original steps (style-grammar §6e); not for shots of ours.
 *   T3.relX(s, n) → fractional frame index 0 … n − 1
 *       time.relief: undoes Blender's SINE ease of a relief sequence, (n − 1)·acos(1 − 2s)/π with s clamped to
 *       [0, 1], so a camera keyed sine in Blender plays at constant speed through T3.sequence (blend floor and
 *       floor + 1 by the fraction). n = the sequence's frame count.
 *   T3.shake(f, f0, { amp, dur = 7, y = 0.7, jitter = 1.6, seed = 31, rot = 0.04, rotSeed = 47 }) → { x, y, r }
 *       fx.shake: a hit shake from f0 for dur frames: size amp·(1 − k)², k = (F − f0)/dur, sides alternating every
 *       frame (by the frame's parity), angle jittered ±jitter/2 rad by T3.rand(F, seed); y is y × the x size;
 *       r (degrees) = (T3.rand(F, rotSeed) − ½)·rot·size. amp (px) is required (e.g. 20–30 px for a heavy drop).
 *       F = Math.round(f) (the engine's frame rounding): the shake is one offset per frame, so sub-frame samples of
 *       one frame (T3.blur.shutter) share it instead of smearing both sides.
 *       Add x, y to the shot's offset, r to its rotation. How many shakes an intro has: house-style §6.
 *   T3.tail(f, fCut, kind = 'afterimage') → opacity 0 … 1
 *       trans.tail: the outgoing picture (or its light) carried over the cut, per frame from fCut, the new shot's first
 *       frame: 'afterimage' 38 / 16 / 5 / 2 % (then 0), the previous picture drawn over the new shot (commonly drawn at
 *       brightness 0.42); 'afterglow' 30 / 14 / 6 / 2 %, a radial glow at the focal point, screen-blended.
 *       Read per whole frame (i = Math.round(f − fCut)); 0 before the cut and after the table.
 *       kind = { v0, h }: a smooth tail v0·2^(−(f − fCut)/h) after the cut via T3.decay (lib/choreo.js), 0 before.
 *   + T3.tail.tables → { afterimage: [...], afterglow: [...] } (frozen copies of the two tables).
 *
 * Sources (read only; proven equal in assets/examples/motion/test_timing.mjs, max abs diff <= 1e-9):
 *   twos: MV house stepped-clock reference (step) and web\segments\K_drop3.js:192-195 (stepN, stepF,
 *     K1_HOLD: the Drop 3 hold clock); landing anchors and reach n + 1 (its "nx − f <= 3"): house
 *     house multi-anchor stepped clock (STEPS4, stepOf).
 *   relX: the skill's house sequence remap formula (locked, untouched; the same formula in house reference
 *     and house reference).
 *   shake: house hit-shake formula (the drop shake, amp 30, 7 f).
 *   tail: house house carry-over tail formula (afterimage) and intro_gpt_handoff.js:10, 22
 *     (afterglow).
 * Approval: time.twos grade A for the MV's stepped Drop 3 (client, 2026-11-14; style-grammar §6e), the landing
 *   re-anchoring B (house sample, never singled out). time.relief, fx.shake, trans.tail grade B: inside house and the
 *   house reference (house checkpoint f4750-4764 for the tails), never named on their own.
 */
(function () {
  'use strict';
  const err = (msg) => Object.assign(new Error('lib/motion/timing.js: ' + msg), { name: 'T3MotionError' });
  const T3 = window.T3;
  if (!T3) throw err('engine.js is not loaded: load it first (motion-library «Setup»)');
  const def = (v, d) => (v == null ? d : v);
  const OWN = 'timing';

  // ---- time.twos ---------------------------------------------------------------------------------------------------
  function anchorList(anchors) {
    const raw = Array.isArray(anchors) ? anchors : [anchors];
    const A = [...new Set(raw.map(Number))].sort((p, q) => p - q);
    if (!A.length || !A.every(Number.isFinite)) throw err('T3.twos(f, anchors, …): anchors = a frame or a list of frames');
    return A;
  }
  function twos(f, anchors, o) {
    o = o || {};
    const A = anchorList(anchors), n = def(o.n, 2), reach = def(o.reach, n + 1), end = def(o.end, Infinity);
    if (!(n > 0)) throw err('T3.twos: n (frames per step) must be > 0');
    if (!(reach >= n)) throw err('T3.twos: reach must be >= n');
    if (f < A[0] || f >= end) return f;
    let i = A.length - 1;
    while (A[i] > f) i--;
    const a = A[i], j = Math.floor((f - a) / n);
    if (i + 1 < A.length) {                                   // the last step before the next anchor stops where it starts
      const J = Math.max(0, Math.ceil((A[i + 1] - a - reach) / n));
      return a + Math.min(j, J) * n;
    }
    return a + j * n;
  }

  // ---- time.relief -------------------------------------------------------------------------------------------------
  function relX(s, n) {
    if (!(n >= 1)) throw err('T3.relX(s, n): n = the sequence frame count (>= 1)');
    return ((n - 1) * Math.acos(1 - 2 * Math.min(1, Math.max(0, s)))) / Math.PI;
  }

  // ---- fx.shake ----------------------------------------------------------------------------------------------------
  function shake(f, f0, o) {
    o = o || {};
    if (!Number.isFinite(o.amp)) throw err('T3.shake(f, f0, { amp, … }): amp (px) is required');
    if (!Number.isFinite(f0)) throw err('T3.shake(f, f0, …): f0 must be a frame');
    const F = Math.round(f), dur = def(o.dur, 7);
    let A = 0;
    if (F >= f0 && F < f0 + dur) A = o.amp * Math.pow(1 - (F - f0) / dur, 2);
    if (!A) return { x: 0, y: 0, r: 0 };
    const R = T3.rand, a = (F % 2 ? 0 : Math.PI) + (R(F, def(o.seed, 31)) - 0.5) * def(o.jitter, 1.6);
    return { x: A * Math.cos(a), y: def(o.y, 0.7) * A * Math.sin(a), r: (R(F, def(o.rotSeed, 47)) - 0.5) * def(o.rot, 0.04) * A };
  }

  // ---- trans.tail --------------------------------------------------------------------------------------------------
  const TABLES = Object.freeze({ afterimage: Object.freeze([0.38, 0.16, 0.05, 0.02, 0, 0]), afterglow: Object.freeze([0.30, 0.14, 0.06, 0.02]) });
  function tail(f, fCut, kind) {
    if (!Number.isFinite(fCut)) throw err('T3.tail(f, fCut, …): fCut = the new shot\'s first frame');
    kind = def(kind, 'afterimage');
    if (typeof kind === 'string') {
      const tb = TABLES[kind];
      if (!tb) throw err(`T3.tail: unknown kind "${kind}" ('afterimage', 'afterglow' or { v0, h })`);
      return tb[Math.round(f - fCut)] || 0;
    }
    if (kind && typeof kind === 'object' && Number.isFinite(kind.v0) && kind.h > 0) {
      const D = T3.decay;
      if (typeof D !== 'function') throw err('T3.tail(f, fCut, { v0, h }) needs T3.decay: load lib/choreo.js');
      return f < fCut ? 0 : D(f, fCut, kind.v0, kind.h);
    }
    throw err('T3.tail: kind = \'afterimage\', \'afterglow\' or { v0, h > 0 }');
  }
  tail.tables = TABLES;

  // ---- export: never over another file's names ---------------------------------------------------------------------
  for (const fn of [twos, relX, shake, tail]) fn.__t3motion = OWN;
  const M = window.__T3_MOTION, clash = [];
  const free = (name) => {
    const cur = T3[name];
    if (cur == null || cur.__t3motion === OWN) return true;
    clash.push('T3.' + name);
    return false;
  };
  if (free('twos')) T3.twos = twos;
  if (free('relX')) T3.relX = relX;
  if (free('shake')) T3.shake = shake;
  if (free('tail')) T3.tail = tail;
  if (clash.length) {
    if (M) (M.clash || (M.clash = [])).push(...clash);
    if (window.console) console.error('lib/motion/timing.js: ' + clash.join(', ') + ' already defined by another file; left as ' + (clash.length > 1 ? 'they are' : 'it is'));
  }
  if (M && M.modules && !M.modules.includes('timing')) M.modules.push('timing');
})();
