/* lib/motion/blur.js — client-approved motion blur as frame functions on a 2D canvas (motion library, release R2)
 *
 * Library ids: fx.shutter, fx.radial
 *   Index: references/motion-library.md (the entries' «Timing (here)» numbers are this file's defaults).
 *   Where blur goes and where it does not: house-style §4.
 *
 * The numbers are pure in the frame: times, weights, spreads and scales come from f and the options only. The canvas
 * functions draw on scratch canvases the size of ctx.canvas, kept between calls (a cache, never state: the picture of
 * frame f is the same in any seek order). Nothing here reads a clock or Math.random.
 * Load after engine.js (no other dependency; GSAP is not needed). A canvas is created only when a canvas function is
 * first called (document.createElement, else OffscreenCanvas); without either it throws T3MotionError then, not at load.
 *
 * API (frozen in the library plan; extras marked +):
 *   T3.blur.shutter(ctx, f, draw, { samples, shutter = 180, align, opaque = false, op = 'source-over', alpha = 1 })
 *       fx.shutter, sub-frame motion blur. Draws `draw` at `samples` sub-frame times, each on its own cleared scratch
 *       canvas (identity transform, alpha 1, source-over, no filter), adds them with 'lighter' at 1/n each (the exact
 *       average of premultiplied colour), then draws the sum on ctx with `op` and `alpha` at the identity transform
 *       (ctx's own state is saved and restored). Returns the canvas it drew (valid until the next call).
 *       draw(c, fs, dt): c = the sample's 2D context, fs = the sample's frame (fractional), dt = fs − f.
 *       The window is shutter/360 of a frame:
 *         180° (the default): samples = 5, align 'center': ±¼ f about f, at the middles of n equal slices
 *                             (house's mblur: dt = −0.25 + 0.5·(i + ½)/n).
 *         360° and over:      samples = 10, align 'trail': from the last frame to this one, at the ends of n slices,
 *                             so the last sample is f itself (house's shutter: f − 1 + (i + 1)/n).
 *       opaque: true (the 360° picture pass): the last sample is drawn again under the sum (destination-over), filling
 *       the bit the 8-bit sum loses, so an opaque picture stays opaque. Skipped with one sample.
 *       samples <= 1: one sample at f, drawn straight on ctx (what house does for a still element): pass
 *       samples: moving ? 5 : 1 so only a moving element pays for the blur.
 *       The house picture pass is { shutter: 360, opaque: true } (10 samples, trailing); its type pass the same without
 *       opaque. Nested calls (a draw that blurs a part of itself) get their own scratch canvases.
 *   T3.blur.radial(ctx, src, { cx, cy, k = 0, copies = 10, spread = 0.22, decay = 0.55, dur = 9, min = 0.004 }) → spread used
 *       fx.radial, radial push blur about (cx, cy) (default: the canvas centre), decaying after the cut. k = frames since
 *       the cut; the spread is spread·e^(−decay·k) for 0 <= k < dur, else 0, and below `min` nothing is drawn (returns 0).
 *       Draws `copies` copies of src on ctx at scales 1 + spread·i/copies about (cx, cy) with opacity 1/(i + 1),
 *       i = 1 … copies, a running mean of the frame and its copies. src = a canvas or image of this frame; null (or
 *       ctx.canvas itself) snapshots ctx.canvas first. cx, cy are in ctx.canvas pixels: the copies are placed with an
 *       absolute transform, and drawn with ctx's own composite op and filter (normally source-over, none).
 *       A blur of a known size, not a decay: { k: 0, spread: s } draws spread s (house sizes its push blur this way).
 *   + T3.blur.times(f, { samples, shutter, align }) → [{ f: fs, dt, w }]: the sample frames and weights (w = 1/n) the
 *       shutter draws, in order. align: 'center' | 'trail' (defaults as above).
 *   + T3.blur.radialSpread(k, { spread, decay, dur }) → the spread at k frames after the cut (0 outside 0 <= k < dur).
 *   + T3.blur.radialLayers(spread, copies = 10) → [{ s, a }]: each copy's scale and opacity, in drawing order.
 *   + T3.blur.push(k, { amount = 0.07, rate = 0.5 }) → scale 1 + amount·(1 − e^(−rate·max(0, k))): the push that
 *       carries the cut's momentum while the radial blur dies (house's 7 % exponential settle; multiply it into the
 *       shot's own scale).
 *
 * Sources (read only; the shapes are reproduced as they are, never re-curved; proven equal in
 * assets/examples/motion/test_blur.mjs, max abs diff <= 1e-9 on the numbers and the same canvas operations):
 *   shutter 180°: house shutter-blur reference (mblur; the TMP / SUB pair, lighter × 1/n).
 *   shutter 360°: house 360-degree opaque shutter reference (NS = 10, accumulate with
 *     the destination-over backing), :999 (picture pass, opaque, only while it moves) and :1004 (type pass, not opaque).
 *   radial: house radial push-blur reference (zoomBlur), used at :540-544 (spread
 *     0.22·e^(−0.55k) for the 9 f after the cut) with the push H1S at :523.
 * Approval: fx.shutter grade A: the client asked for visible drag in the house sample (v5/v6, handoff
 *   trailing opaque backing so full-frame motion stays solid).
 *   fx.radial grade A: the client's remarks on house's last shot and H1 (recorded at intro_gpt.js:478, 521); house v11
 *   signed off as final (memory house-final-test).
 */
(function () {
  'use strict';
  const err = (msg) => Object.assign(new Error('lib/motion/blur.js: ' + msg), { name: 'T3MotionError' });
  const T3 = window.T3;
  if (!T3) throw err('engine.js is not loaded: load it first (motion-library «Setup»)');
  const def = (v, d) => (v == null ? d : v);

  // ---- numbers -----------------------------------------------------------------------------------------------------
  function conf(o) {
    o = o || {};
    const sh = def(o.shutter, 180);
    if (!(sh > 0)) throw err('T3.blur: shutter must be > 0 degrees');
    const wide = sh >= 360, n = Math.max(1, Math.round(def(o.samples, wide ? 10 : 5))), align = def(o.align, wide ? 'trail' : 'center');
    if (align !== 'center' && align !== 'trail') throw err(`T3.blur: align must be 'center' or 'trail', not "${align}"`);
    return { S: sh / 360, n, align };
  }
  function times(f, o) {
    const { S, n, align } = conf(o), out = [];
    for (let i = 0; i < n; i++) {
      let fs, dt;
      if (n === 1) { fs = f; dt = 0; }
      else if (align === 'center') { dt = -S / 2 + S * (i + 0.5) / n; fs = f + dt; }     // house: f + (−0.25 + 0.5·(i + ½)/n)
      else { fs = f - S + S * (i + 1) / n; dt = fs - f; }                                 // house: f − 1 + (i + 1)/n
      out.push({ f: fs, dt, w: 1 / n });
    }
    return out;
  }
  function radialSpread(k, o) {
    o = o || {};
    k = def(k, 0);
    return k >= 0 && k < def(o.dur, 9) ? def(o.spread, 0.22) * Math.exp(-def(o.decay, 0.55) * k) : 0;
  }
  function radialLayers(spread, copies) {
    const N = Math.max(1, Math.round(def(copies, 10))), out = [];
    for (let i = 1; i <= N; i++) out.push({ s: 1 + spread * i / N, a: 1 / (i + 1) });
    return out;
  }
  function push(k, o) {
    o = o || {};
    return 1 + def(o.amount, 0.07) * (1 - Math.exp(-def(o.rate, 0.5) * Math.max(0, def(k, 0))));
  }

  // ---- scratch canvases (a cache by role, nesting depth and size) --------------------------------------------------
  const pool = new Map();
  let depth = 0;
  function makeCanvas(w, h) {
    const d = window.document;
    if (d && typeof d.createElement === 'function') { const c = d.createElement('canvas'); c.width = w; c.height = h; return c; }
    if (typeof window.OffscreenCanvas === 'function') return new window.OffscreenCanvas(w, h);
    throw err('T3.blur needs a canvas: no document and no OffscreenCanvas here');
  }
  function scratch(role, lvl, w, h) {
    const key = role + ':' + lvl + ':' + w + 'x' + h;
    let c = pool.get(key);
    if (!c) { c = makeCanvas(w, h); pool.set(key, c); }
    return c;
  }
  const reset = (x) => { x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.filter = 'none'; };
  function sizeOf(ctx) {
    if (!ctx || !ctx.canvas || typeof ctx.drawImage !== 'function') throw err('T3.blur: ctx must be a 2D canvas context');
    return [ctx.canvas.width, ctx.canvas.height];
  }
  function put(ctx, img, op, alpha) {
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.filter = 'none'; ctx.globalCompositeOperation = op; ctx.globalAlpha = alpha;
    ctx.drawImage(img, 0, 0);
    ctx.restore();
  }

  // ---- fx.shutter --------------------------------------------------------------------------------------------------
  function shutter(ctx, f, draw, o) {
    o = o || {};
    if (typeof draw !== 'function') throw err('T3.blur.shutter(ctx, f, draw, …): draw(c, fs, dt) must be a function');
    const [W, H] = sizeOf(ctx), ts = times(f, o), n = ts.length, op = def(o.op, 'source-over'), alpha = def(o.alpha, 1);
    const lvl = depth++;
    try {
      const sub = scratch('sub', lvl, W, H), S = sub.getContext('2d');
      if (n <= 1) {
        reset(S); S.clearRect(0, 0, W, H); draw(S, ts[0].f, ts[0].dt); reset(S);
        put(ctx, sub, op, alpha);
        return sub;
      }
      const acc = scratch('acc', lvl, W, H), A = acc.getContext('2d');
      reset(A); A.clearRect(0, 0, W, H);
      for (const s of ts) {
        reset(S); S.clearRect(0, 0, W, H); draw(S, s.f, s.dt); reset(S);
        A.globalCompositeOperation = 'lighter'; A.globalAlpha = 1 / n; A.drawImage(sub, 0, 0);
      }
      if (o.opaque) { reset(A); A.globalCompositeOperation = 'destination-over'; A.drawImage(sub, 0, 0); }
      reset(A);
      put(ctx, acc, op, alpha);
      return acc;
    } finally { depth--; }
  }

  // ---- fx.radial ---------------------------------------------------------------------------------------------------
  function radial(ctx, src, o) {
    o = o || {};
    const [W, H] = sizeOf(ctx), sp = radialSpread(o.k, o);
    if (!(sp >= def(o.min, 0.004))) return 0;
    let img = src;
    if (img == null || img === ctx.canvas) {
      const snap = scratch('snap', depth, W, H), s = snap.getContext('2d');
      reset(s); s.globalCompositeOperation = 'copy'; s.drawImage(ctx.canvas, 0, 0); s.globalCompositeOperation = 'source-over';
      img = snap;
    }
    const cx = def(o.cx, W / 2), cy = def(o.cy, H / 2);
    for (const L of radialLayers(sp, o.copies)) {
      const sc = L.s;
      ctx.save(); ctx.globalAlpha = L.a; ctx.setTransform(sc, 0, 0, sc, cx - sc * cx, cy - sc * cy); ctx.drawImage(img, 0, 0); ctx.restore();
    }
    return sp;
  }

  // ---- export: never over another file's T3.blur -------------------------------------------------------------------
  const api = Object.freeze({ shutter, radial, times, radialSpread, radialLayers, push, __t3motion: 'blur' });
  const M = window.__T3_MOTION;
  if (T3.blur != null && T3.blur.__t3motion !== 'blur') {
    const msg = 'lib/motion/blur.js: T3.blur is already defined by another file; left as it is (lib/motion blur not installed)';
    if (M) (M.clash || (M.clash = [])).push('T3.blur');
    if (window.console) console.error(msg);
  } else {
    T3.blur = api;
    if (M && M.modules && !M.modules.includes('blur')) M.modules.push('blur');
  }
})();
