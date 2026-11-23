/* lib/motion/moves.js — the approved and house moves as pure frame functions (motion library, releases R1 and R2)
 *
 * Library ids: move.rise, move.arrive, move.leave, move.settle, move.stagger (R1); type.chars, type.roll (R2)
 *   Index: references/motion-library.md (the entries say when to use which, and what a film may vary).
 *   type.chars is T3.mv.chars and T3.mv.swap; type.roll is T3.mv.roll.
 *
 * Every function is pure in the frame: f is a frame number (fractional allowed for sub-frame samples), the result is a
 * plain object, and nothing is kept between calls. Progress is k = (f − f0) / dur, clamped, so k(f0) = 0 and
 * k(f0 + dur) = 1; dur <= 0 is a cut at f0. Eases are T3.EZ names (lib/motion/ez.js): any T3.EZ.get argument works.
 * Units: x, y in px; s scale (1 = rest); r in degrees; o opacity 0..1; blur in px.
 *
 * API (frozen in the library plan; extras marked +):
 *   T3.mv.rise(f, { at, dur = 12, dy = 18, fade = 6, blur = 6, blurDur = 7, ease,
 *                   out: { at, dur = 6, dy = −14, blur = 6, ease } }) → { o, x, y, s, blur }
 *       move.rise, the product-film rise: fades in over `fade` f, travels dy → 0 over `dur` f, sharpens blur → 0 over
 *       `blurDur` f; the exit travels 0 → out.dy, fades and blurs over out.dur f, speeding up into the cut.
 *       Defaults are the crisp product-film presets, including their curves: the entrance on the classic
 *       exponential 1 − 2^(−10k) (not GSAP 3.15's normalised expo.out, up to 0.8 % apart), the exit's travel on k², its
 *       fade and blur on k. Passing `ease` / `out.ease` swaps that travel curve for a T3.EZ curve.
 *       + dx (px), s (start scale; start scale), cut (true: appear at `at` with no motion), fIn (the entrance's own
 *         clock, compressed entrance clock: a passage that compresses the entrance passes its compressed frame). at == null: no entrance.
 *       + out: dx, s (end scale), pw (fade and blur on k^pw), cut (vanish at out.at); out may be a number (= out.at).
 *   T3.mv.arrive(f, { at, dur = 12, from: { x, y, s, r, o }, ease = 'snap' }) → { x, y, s, r, o }
 *       move.arrive: from `from` to rest on a front-loaded curve (the default snap curve covers ≈ 82 % of the travel by
 *       2 f of 12, then lands slowly). + to: the rest pose (default x 0, y 0, s 1, r 0, o 1); from's missing fields are to's.
 *   T3.mv.leave(f, { at, dur = 8, to: { x, y, s, r, o }, ease = 'expoIn' }) → { x, y, s, r, o }
 *       move.leave: from rest to `to`, speeding up into the cut. + from: the start pose (default rest).
 *   T3.mv.settle(f, fLand, { pxPerSec = 2, scale = 0.005, dir }) → { x, y, s }
 *       move.settle: the after-push once a move has landed; add it to the landed pose (x, y added, s multiplied).
 *       Its speed rises from 0 at fLand (no corner after a landing that ends at rest), peaks at pxPerSec px/s about
 *       11 f later and then slows over seconds without stopping inside a shot: ≈ 3.4 px in the first 2 s at the
 *       defaults, still ≈ 0.8 px/s after 5 s.
 *       The scale grows by `scale` over the first `span` f (default 48) on the same curve, then keeps creeping.
 *       dir: [dx, dy], { x, y } or an angle in degrees (0 = right, 90 = down); no dir = scale only.
 *       + span = 48, ramp = 3, decay = 120 (frames: the speed's rise and fall times).
 *   T3.mv.stagger(i, n, { from = 8, to = 3 }) → frame offset of item i (0-based) of n
 *       move.stagger: the gap between items shrinks geometrically from `from` to `to` frames (dealt, poured, stamped:
 *       give the batch a cause). The parts of one move use a small from / to (style-grammar §6b). Fractional offsets are fine.
 *   T3.mv.css(el, pose)
 *       Writes a pose to an element: opacity (hidden at <= 0.003), transform translate/rotate/scale (none at rest) and,
 *       when the pose has blur, filter blur. Writes only the styles that changed (cached on el.__t3mv); it owns
 *       those styles, so do not set them on the same element elsewhere. Returns false when the element is hidden.
 *
 *   R2, type motion (per-character rise, prefix-preserving swap, value roll):
 *   T3.mv.chars(f, n, { at, per = 1, …rise, out: { at, per, …rise.out } }) → [ { o, x, y, s, blur } per character ]
 *       type.chars, the per-character rise: character i rises at at + per·i on move.rise's figures (any rise option
 *       passes through: dur, dy, fade, blur, blurDur, dx, s, ease, cut, fIn); the exit starts character i at
 *       out.at + out.per·i on rise's exit figures. n is the word (a string, split into code points code-point array
 *       [...s], or an array of characters) or a character count. at == null: no entrance (the word is already there).
 *       Lay the characters out yourself, one element each, x measured on the whole word so its kerning holds
 *       , and write each pose with T3.mv.css.
 *       + hold (count, or the word it replaces): the first `hold` characters are the prefix this word shares with the
 *         one before it; they appear at `at` as a cut and never move, and the rest start at at + per·(i − hold).
 *       + out.hold (count, or the word that replaces this one): makes the exit a swap: the shared prefix vanishes at
 *         out.at as a cut, the rest leave from out.at − out.lead, out.per apart. Swap exit defaults: per 0.5, lead 2;
 *         a plain exit (no out.hold): per 0.4, lead 0. out may be a number (= out.at).
 *       A word that arrives by one swap and leaves by the next: chars(f, word, { at: S1, hold: before,
 *       out: { at: S2, hold: after } }) gives exactly what the two swaps give it.
 *   T3.mv.swap(f, prev, next, { at, perOut = 0.5, perIn = 1 }) → { prev: [poses], next: [poses], held }
 *       type.chars, the word swap: the prefix both words share (held characters) is cut over at `at` in place, so it
 *       never moves; prev's other characters leave from at − lead, perOut apart, on rise's exit; next's other
 *       characters rise from at, perIn apart. prev has no entrance (it is on screen). prev and next are words.
 *       + lead = 2, in: { rise entrance options }, out: { rise exit options }.
 *   T3.mv.roll(f, { at, dur = 18, from, to, fmt }) → { v, text, o }
 *       type.roll, the instrument-like value roll: from → to on an even deceleration, quad-out 1 − (1 − k)²
 *       (quadratic ease-out; distinct from T3.EZ.roll), so it lands on the beat at at + dur (12–24 f).
 *       from, to: numbers or display strings ('88.8%', '1.2 s', '—', '2025.08.07'): a string's text around its number
 *       stays, the roll keeps the target's decimals, a leading - or − makes it negative , and a
 *       date or a word is not a number. v is the value (null while a non-number shows), text the string to show,
 *       o the text's own opacity (1 except in a word change). Before `at` a change still shows `from` as written.
 *       No from: an entrance from 0 (every value rolls, as the pillar values and the opening's do); with minRoll, a
 *       whole number smaller than minRoll shows at once instead (the panel's footnote row uses minRoll 10).
 *       A change with either side not a number fades `from` out over fadeOut (3) f, then `to` in over fadeIn (4) f.
 *       Equal from and to (as written) is no change. fmt(v) → string replaces the default format
 *       (pre + toFixed(dec) + suf, no "-0").
 *       Tabular digits: give the element font-variant-numeric: tabular-nums  and a fixed width or
 *       right alignment, so the digits do not shift while they roll; write text only when it changed.
 *       A value that changes several times: call roll for the latest change that has begun (its at <= f).
 *       + dec (decimals), minRoll = 0, fadeOut = 3, fadeIn = 4, ease (a T3.EZ curve in place of quad-out).
 *
 * Sources and approval:
 *   rise: the skill's house product-film rise specification (cl, eo, pr, mix :91-97; anim :109-121) and
 *     assets/template/opening/segments/b_open_kit.js:64-95 (OPB.anim :81-87, IN / OUT :89-90), both
 *     locked and left untouched; css from the same files' css / fade / put (house css/fade helper). Grade A: the house motion
 *     sample, approved 2026-11-12 (crafts.md registry v8_motion_b4; preview house motion sample,
 *     reference frames). Proven equal to the source formulas: assets/examples/motion/test_rise.mjs (max abs diff <= 1e-9).
 *   arrive, leave, settle, stagger: house rules (H), whose figures live in style-grammar §6b (the 11-18 curve rule,
 *     written into the skill 2026-11-21, decision D1); the defaults here are this file's own reading of them, and
 *     settle's decaying shape is a design choice of this file. Tests: assets/examples/motion/test_moves.mjs.
 *   chars, swap: house prefix-swap specification (cpLen :264, copied as written; the name characters' in / out timings :271-273),
 *     played through rise formulas. roll: quadratic out (q2o), :122-124
 *     (parseNum, parseBar, fixNum), :346 (the pillar value's entrance roll), :505-515 (the footnote row: entrance,
 *     changes, the 3 f / 4 f word change); also the opening's rolls, b_open_kit.js:434 and b_open_cards.js:104.
 *     All locked and left untouched. Grade B: inside the house motion sample approved 2026-11-12 (crafts.md registry
 *     v8_motion_b4; previews reference frames, the name swap at f993), never named on its own. Proven equal to the source
 *     formulas: assets/examples/motion/test_type.mjs (poses <= 1e-9, roll text character for character).
 *     Not lifted: the pillar value on a model change (value changes use T3.mv.roll quad-out).
 */
(function () {
  'use strict';
  const err = (msg) => Object.assign(new Error('lib/motion/moves.js: ' + msg), { name: 'T3MotionError' });
  const T3 = window.T3;
  if (!T3 || !T3.EZ) {
    if (window.__T3_MOTION) window.__T3_MOTION.error = 'moves.js: T3.EZ missing';
    throw err('T3.EZ is not loaded: load lib/motion/ez.js first (motion-library «Setup»)');
  }
  const EZ = T3.EZ;
  const cl = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
  const pr = (f, f0, d) => (d > 0 ? cl((f - f0) / d) : f >= f0 ? 1 : 0);
  const def = (v, d) => (v == null ? d : v);
  // the approved house curves (classic exponential in, quadratic out), kept as written so rise stays equal to them
  const expohouse = (k) => (k <= 0 ? 0 : k >= 1 ? 1 : 1 - Math.pow(2, -10 * k));
  const sqhouse = (k) => k * k;

  // ---- move.rise ---------------------------------------------------------------------------------------------------
  function rise(f, o) {
    o = o || {};
    let op = 1, x = 0, y = 0, s = 1, bl = 0;
    if (o.at != null) {
      const fi = o.fIn == null ? f : o.fIn;
      if (o.cut) op = fi >= o.at ? 1 : 0;
      else {
        const dur = def(o.dur, 12), ease = o.ease == null ? expohouse : EZ.get(o.ease);
        const k = ease(dur > 0 ? (fi - o.at) / dur : fi >= o.at ? 1 : 0);
        op = pr(fi, o.at, def(o.fade, 6));
        x = def(o.dx, 0) * (1 - k); y = def(o.dy, 18) * (1 - k);
        if (o.s != null) s = o.s + (1 - o.s) * k;
        const b = def(o.blur, 6);
        if (b) bl = b * (1 - pr(fi, o.at, def(o.blurDur, 7)));
      }
    }
    let O = o.out;
    if (typeof O === 'number') O = { at: O };
    if (O && O.at != null && f > O.at - 1e-9) {
      if (O.cut) op = f >= O.at ? 0 : op;
      else {
        const k = pr(f, O.at, def(O.dur, 6)), q = (O.ease == null ? sqhouse : EZ.get(O.ease))(k), kp = O.pw ? Math.pow(k, O.pw) : k;
        op *= 1 - kp;
        x += def(O.dx, 0) * q; y += def(O.dy, -14) * q;
        if (O.s != null) s *= 1 + (O.s - 1) * q;
        const b = def(O.blur, 6);
        if (b) bl += b * kp;
      }
    }
    return { o: op, x, y, s, blur: bl };
  }

  // ---- move.arrive / move.leave ------------------------------------------------------------------------------------
  const REST = { x: 0, y: 0, s: 1, r: 0, o: 1 };
  const mix = (A, B, e) => ({ x: A.x + (B.x - A.x) * e, y: A.y + (B.y - A.y) * e, s: A.s + (B.s - A.s) * e, r: A.r + (B.r - A.r) * e, o: A.o + (B.o - A.o) * e });
  function arrive(f, o) {
    if (!o || o.at == null) throw err('T3.mv.arrive(f, { at, … }): `at` is required');
    const B = Object.assign({}, REST, o.to), A = Object.assign({}, B, o.from);
    return mix(A, B, EZ.at(f, o.at, def(o.dur, 12), def(o.ease, 'snap')));
  }
  function leave(f, o) {
    if (!o || o.at == null) throw err('T3.mv.leave(f, { at, … }): `at` is required');
    const A = Object.assign({}, REST, o.from), B = Object.assign({}, A, o.to);
    return mix(A, B, EZ.at(f, o.at, def(o.dur, 8), def(o.ease, 'expoIn')));
  }

  // ---- move.settle -------------------------------------------------------------------------------------------------
  // speed u(t) = (1 − e^(−t/a)) · e^(−t/b): 0 at landing, a peak, then a slow fall; D(t) is its integral (t in frames)
  const settleD = (t, a, b) => { const c = (a * b) / (a + b); return b * (1 - Math.exp(-t / b)) - c * (1 - Math.exp(-t / c)); };
  const settlePeak = (a, b) => (b / (a + b)) * Math.pow(a / (a + b), a / b);
  function unit(dir) {
    if (dir == null) return null;
    let dx, dy;
    if (typeof dir === 'number') { dx = Math.cos((dir * Math.PI) / 180); dy = Math.sin((dir * Math.PI) / 180); }
    else if (Array.isArray(dir)) { dx = +dir[0]; dy = +dir[1]; }
    else { dx = +dir.x; dy = +dir.y; }
    const L = Math.hypot(dx, dy);
    if (!(L > 0)) throw err('T3.mv.settle: dir must be a non-zero direction ([dx, dy], { x, y } or degrees)');
    return [dx / L, dy / L];
  }
  function settle(f, fLand, o) {
    o = o || {};
    if (fLand == null) throw err('T3.mv.settle(f, fLand, …): `fLand` is required');
    const t = f - fLand;
    if (!(t > 0)) return { x: 0, y: 0, s: 1 };
    const a = def(o.ramp, 3), b = def(o.decay, 120), span = def(o.span, 48), fps = T3.FPS || 24;
    const D = settleD(t, a, b), u = unit(o.dir), px = u ? (def(o.pxPerSec, 2) / fps) * (D / settlePeak(a, b)) : 0;
    return { x: u ? u[0] * px : 0, y: u ? u[1] * px : 0, s: 1 + def(o.scale, 0.005) * (D / settleD(span, a, b)) };
  }

  // ---- move.stagger ------------------------------------------------------------------------------------------------
  function stagger(i, n, o) {
    o = o || {};
    const a = def(o.from, 8), b = def(o.to, 3), m = n - 1;   // m gaps between n items
    if (!(m >= 1) || !(i > 0)) return 0;
    const geo = a > 0 && b > 0, last = Math.min(i, m);
    let off = 0;
    for (let j = 0; j < last; j++) {
      const u = m === 1 ? 0 : j / (m - 1);
      off += geo ? a * Math.pow(b / a, u) : a + (b - a) * u;
    }
    return off;
  }

  // ---- T3.mv.css ---------------------------------------------------------------------------------------------------
  function css(el, p) {
    const c = el.__t3mv || (el.__t3mv = {});
    const set = (k, v) => { if (c[k] !== v) { el.style[k] = v; c[k] = v; } };
    const op = p.o == null ? 1 : p.o;
    if (!(op > 0.003)) { set('visibility', 'hidden'); return false; }
    set('visibility', 'visible');
    set('opacity', op >= 0.998 ? '1' : op.toFixed(3));
    const x = p.x || 0, y = p.y || 0, s = p.s == null ? 1 : p.s, r = p.r || 0;
    const mv = Math.abs(x) > 0.004 || Math.abs(y) > 0.004, zs = Math.abs(s - 1) > 1e-5, rs = Math.abs(r) > 1e-4;
    set('transform', mv || zs || rs ? `translate(${x.toFixed(2)}px,${y.toFixed(2)}px)` + (rs ? ` rotate(${r.toFixed(3)}deg)` : '') + (zs ? ` scale(${s.toFixed(4)})` : '') : 'none');
    if (p.blur != null) set('filter', p.blur > 0.05 ? `blur(${p.blur.toFixed(2)}px)` : 'none');
    return true;
  }

  // ---- type.chars: per-character rise and the word swap (house prefix-swap specification) ----------------------------------------
  const cpLen = (a, b) => { let i = 0; while (i < a.length && i < b.length && a[i] === b[i]) i++; return i; };   // shared prefix length
  const isWord = (w) => typeof w === 'string' || Array.isArray(w);
  const glyphs = (w) => (typeof w === 'string' ? [...w] : w);          // one entry per character, as code points
  const omit = (o, keys) => { const r = {}; for (const k in o) if (!keys.includes(k)) r[k] = o[k]; return r; };
  function chars(f, n, o) {
    o = o || {};
    const word = isWord(n) ? glyphs(n) : null, N = word ? word.length : n;
    if (!(Number.isInteger(N) && N >= 0)) throw err('T3.mv.chars(f, n, …): n is the word (a string or an array of characters) or a character count');
    const prefix = (h, what) => {
      if (h == null) return 0;
      if (isWord(h)) {
        if (!word) throw err(`T3.mv.chars: ${what} given as a word needs the word itself as n`);
        return cpLen(glyphs(h), word);
      }
      if (!(Number.isInteger(h) && h >= 0)) throw err(`T3.mv.chars: ${what} is a character count or a word`);
      return h;
    };
    const pIn = prefix(o.hold, 'hold'), per = def(o.per, 1), inBase = omit(o, ['per', 'hold', 'out']);
    let O = o.out;
    if (typeof O === 'number') O = { at: O };
    const swapOut = !!O && O.hold != null, pOut = O ? prefix(O.hold, 'out.hold') : 0;
    const outBase = O ? omit(O, ['per', 'hold', 'lead']) : null;
    const oPer = O ? def(O.per, swapOut ? 0.5 : 0.4) : 0, lead = O ? def(O.lead, swapOut ? 2 : 0) : 0;
    const res = [];
    for (let i = 0; i < N; i++) {
      const ro = Object.assign({}, inBase);
      if (o.at != null) {
        if (i < pIn) ro.cut = true;                                     // the shared prefix: there at `at`, never moves
        else ro.at = o.at + per * (i - pIn);
      }
      if (O && O.at != null) ro.out = i < pOut ? { at: O.at, cut: true } : Object.assign({}, outBase, { at: O.at - lead + oPer * (i - pOut) });
      res.push(rise(f, ro));
    }
    return res;
  }
  function swap(f, prev, next, o) {
    o = o || {};
    if (o.at == null) throw err('T3.mv.swap(f, prev, next, { at, … }): `at` is required');
    if (!isWord(prev) || !isWord(next)) throw err('T3.mv.swap: prev and next are the two words (strings or arrays of characters)');
    const I = Object.assign(omit(o.in || {}, ['out']), { at: o.at, per: def(o.perIn, 1), hold: prev });
    const O = Object.assign({}, o.out, { at: o.at, per: def(o.perOut, 0.5), lead: def(o.lead, 2), hold: next });
    return { prev: chars(f, prev, { out: O }), next: chars(f, next, I), held: cpLen(glyphs(prev), glyphs(next)) };
  }

  // ---- type.roll: the value roll (house value-roll specification) --------------------------------------------
  const q2o = (k) => { k = cl(k); return 1 - (1 - k) * (1 - k); };                                    // quadratic out
  const parseNum = (s) => { if (s == null || /^\d{4}\.\d\d\.\d\d$/.test(s)) return null; const m = /^([^\d]*)(\d+(?:\.(\d+))?)(.*)$/.exec(String(s)); return m ? { pre: m[1], v: +m[2], dec: m[3] ? m[3].length : 0, suf: m[4] } : null; };   // :122
  const fixNum = (v, dec) => { const t = v.toFixed(dec); return /^-0(\.0+)?$/.test(t) ? t.slice(1) : t; };   // :124
  function numOf(x) {
    if (typeof x === 'number') {
      if (!Number.isFinite(x)) return null;
      const m = /\.(\d+)$/.exec(String(x));
      return { pre: '', v: x, dec: m ? m[1].length : 0, suf: '' };
    }
    if (typeof x !== 'string') return null;
    const n = parseNum(x);
    if (n && /^[-−]$/.test(n.pre.trim())) { n.v = -n.v; n.pre = n.pre.replace(/[-−]/, ''); }   // :123 parseBar's sign
    return n;
  }
  function roll(f, o) {
    o = o || {};
    if (o.at == null) throw err('T3.mv.roll(f, { at, to, … }): `at` is required');
    if (o.to == null) throw err('T3.mv.roll(f, { at, to, … }): `to` is required');
    const at = o.at, dur = def(o.dur, 18), ease = o.ease == null ? q2o : EZ.get(o.ease);
    const fmt = (v, n) => (o.fmt ? String(o.fmt(v)) : n.pre + fixNum(v, o.dec == null ? n.dec : o.dec) + n.suf);
    const show = (x, n) => (n && (o.fmt || o.dec != null || typeof x !== 'string') ? fmt(n.v, n) : String(x));
    const b = numOf(o.to);
    const k = () => (dur > 0 ? (f - at) / dur : f >= at ? 1 : 0);
    if (o.from == null) {                                              // the entrance: from 0 (:346, :508)
      if (!b) return { v: null, text: String(o.to), o: 1 };
      if (!(Math.abs(b.v) >= def(o.minRoll, 0) || b.dec > 0)) return { v: b.v, text: show(o.to, b), o: 1 };
      const v = b.v * ease(k());
      return { v, text: fmt(v, b), o: 1 };
    }
    const a = numOf(o.from);
    if (String(o.from) === String(o.to) || f < at) return { v: a ? a.v : null, text: f < at ? show(o.from, a) : show(o.to, b), o: 1 };
    if (a && b) { const v = a.v + (b.v - a.v) * ease(k()); return { v, text: fmt(v, b), o: 1 }; }   // :511
    const out = def(o.fadeOut, 3), inn = def(o.fadeIn, 4), early = f < at + out;                  // :512, a word change
    const n = early ? a : b;
    return { v: n ? n.v : null, text: early ? show(o.from, a) : show(o.to, b), o: early ? 1 - pr(f, at, out) : pr(f, at + out, inn) };
  }

  T3.mv = Object.freeze({ rise, arrive, leave, settle, stagger, css, chars, swap, roll });
  if (window.__T3_MOTION && window.__T3_MOTION.modules) window.__T3_MOTION.modules.push('moves');
})();
