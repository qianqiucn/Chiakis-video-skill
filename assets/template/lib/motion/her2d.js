/* lib/motion/her2d.js — her 2D shot: the approved hair and veil wave, the two-pass alpha warp, eye states, the group
 * camera and the dust motes, as pure frame functions (motion library, release R2)
 *
 * Library ids: her.wave, her.eyes, her.camera, her.motes
 *   her.wave = T3.her.wave + T3.her.warp2 · her.eyes = T3.her.eyes · her.camera = T3.her.cam · her.motes = T3.her.motes.
 *   Index: references/motion-library.md (group her). The measured reference and what the approved sample proved at 1:1
 *   (plate softened under the veil, difference-matte fringe, static trim in front): style-grammar §6d.
 *
 * Load (in the template's default tags since R2): after engine.js; T3.her.warp2 also needs lib/meshwarp.js
 *   (load order between the two does not matter). Without engine.js this file throws T3MotionError at load. Without
 *   meshwarp.js it loads fine and only T3.her.warp2 throws T3MotionError when called. No GSAP needed: the shapes here are
 *   the approved sample's own cosine and smoothstep, kept as written (never re-curved onto T3.EZ).
 *
 * Every function is pure in the frame: f is a frame number (fractional allowed for sub-frame samples), nothing is kept
 * between calls except T3.her.warp2's cache of each picture's two opaque copies (derived pixels, so the output never
 * depends on call order). Units: layer px = the 1920 × 1080 picture the shot is drawn on, before the camera.
 *
 * API (frozen in the library plan; extras marked +):
 *   T3.her.wave(rig, f, o) → field(x, y) → [dx, dy, pin]
 *       her.wave: the rooted travelling wave at frame f. field takes a point in layer px and returns its displacement in
 *       layer px and the pin weight (0 = held at the root, 1 = free). Pass it to T3.her.warp2, or to a plain T3.meshwarp
 *       whose picture fills its canvas in layer px: mw.render((u, v) => field(u * 1920, v * 1080)).
 *       rig: { root: [[x, y], …] the root polyline in layer px (2+ points); fan: [x, y] (hair) the point the strands
 *         fan out from, whose angle picks each strand's phase; len (veil) the root-to-tail length in px }.
 *       o.preset 'hair' (default) or 'veil'; any field below overrides the preset. Defaults = the approved sample:
 *       hair: period 33 f; tx 26, ty 25.4 (frames of the leftmost and highest swing at s = ref px from the root);
 *         lagX 0.036, lagY 0.0125 f per px further out (3.6 and 1.25 f per 100 px); ref 75; yr 0.4 (vertical =
 *         0.4 × sideways); amp [1.45, 5.2] half-amplitude px, root side → free, over ampLen 520 px (smoothstep);
 *         ampVar 0.18 (± per strand); jitter 1.5 (± f per strand); pin [6, 70] (held within 6 px of the root, free
 *         from 70 px, smoothstep between).
 *       veil: period 31 f; along u = s / rig.len: amp [0.75, 2.75] over ampAt [0.1, 0.65]; tx [22, 33] (root → tail,
 *         on u^1.2), ty [21, 26] (on u²); yr 0.34; pin [5, 65]; tail shiver 0.45 px every shiverPeriod 9 f, travelling
 *         outward over shiverLen 160 px, faded in over shiverAt [0.6, 0.95].
 *       + gain (default 1): multiplies every amplitude (the sample's ?k=3 check for a clean plate = gain 3).
 *       Throws T3MotionError on a bad rig (no root, hair without fan, veil without len) or an unknown preset.
 *   T3.her.warp2(ctx, img, mesh, field) → true, or false while img has not loaded (draws nothing then)
 *       her.wave's warp: a picture with soft alpha (hair, veil) is warped as two opaque pictures, its colour
 *       premultiplied on black and its 1 − alpha, each through T3.meshwarp, then laid on ctx with multiply and then
 *       lighter. That is source-over (base × (1 − a) + colour × a), with no seam where meshwarp's triangles overlap.
 *       ctx must already be opaque under the layer (draw the plate first); ctx.globalAlpha acts as the layer's opacity;
 *       ctx's transform and composite mode are saved and restored.
 *       img: the layer, an Image or canvas aligned with the plate, in its own pixels.
 *       mesh: { box: [x0, y0, x1, y1] the part that moves, in img px (default the whole img); cols = 12, rows = 12
 *         (the sample: hair 46 × 31, veil 48 × 20); scale: [kx, ky] img px → layer px (default: img fills ctx.canvas);
 *         cam: a T3.her.cam pose (the camera is folded into the same single resampling); + seam (T3.meshwarp's);
 *         + fresh: true rebuilds the two opaque copies on every call (an img canvas whose pixels change) }.
 *       field: T3.her.wave's field, any (x, y) → [dx, dy] in layer px, or null.
 *       Throws T3MotionError when lib/meshwarp.js is not loaded.
 *   T3.her.eyes(f, events) → opacity 0..1 of one aligned eye edit (closed eyes, a new gaze), drawn whole over the
 *       picture: the edit differs from it only around the eyes, so the eyes alone change (style-grammar §6d).
 *       events: one event or an array, any order:
 *         { blink: at }  the closed-eyes edit at 50 %, 100 %, 100 %, 50 % on frames at … at + 3; never stretched with the
 *           song. Fractional f holds the frame it falls in (floor).
 *         { gaze: at, dur = 3, to = 1 }  a slow gaze: smoothstep from the current opacity to `to` over dur (2–3) frames.
 *         { glance: at, to = 1 }  a quick one: one frame halfway at `at`, `to` from at + 1 (no drawn middle state).
 *         The long form { kind: 'blink' | 'gaze' | 'glance', at, dur, to } works too. Gazes and glances chain in time
 *         order from opacity 0; a blink lifts the result to at least its own value.
 *   T3.her.cam(f, f0, f1, { zoom = 1.0755, pan = 88.6, over = 0.02 }) → { s, x, y, cx, cy }
 *       her.camera: the whole picture zooms × zoom about (cx, cy) on a cosine from f0 to f1 while it slides `pan` px to
 *       the left (negative: to the right); the plate is over-scaled by `over` so no edge shows. Put f1 past the cut so
 *       the camera is still moving when the shot is cut (the sample: f0 5, f1 40.5, cut at 39).
 *       + panLag = [0.75, 1]: the pan's cosine runs from f0 + panLag[0] to f1 + panLag[1] (the sample's pan trails the
 *         zoom: 5.75 → 41.5). + panY = 0 (px up). + cx = 960, cy = 540.
 *       Screen point of a layer point: (cx + x + s · (X − cx), cy + y + s · (Y − cy)).
 *       + T3.her.cam.pt(c, X, Y) → [sx, sy]: that point (c null = no camera).
 *       + T3.her.cam.matrix(c, kx = 1, ky = kx) → [a, b, c, d, e, f] for ctx.setTransform(...m): the camera with a
 *         picture whose own pixels are kx, ky layer px (a 1672 px plate on the 1920 layer: kx = 1920 / 1672).
 *   T3.her.motes(ctx, f, { n = 8, seed }) → the number of motes drawn
 *       her.motes: dust specks drifting with the wind, each fading in and out over 4 f, wobbling 2.2 px across its path
 *       every 26 f and drawn as 5 samples over ± 1/4 f (its own shutter), so the fast ones streak a little.
 *       Which motes: o.list if given; else, with o.seed, n motes generated from the seed (+ see below); else the
 *       approved sample's eight (T3.her.motes.S9). Positions are in the ctx's current coordinates (the sample draws
 *       with the identity transform on a 1920 × 1080 canvas); + cam: a T3.her.cam pose, so the motes ride the camera.
 *       + list: [{ x, y, vx, vy, r, a, f0, f1, flake }]: (x, y) layer px at frame f0, (vx, vy) px per frame, radius,
 *         opacity, visible f0 … f1 with the fades inside; flake: a small flat flake instead of a round speck.
 *       + generated (this file's own placement, not the sample's hand placement): span = [0, 48] the shot's frames;
 *         box = [0, 0, 1920, 1080] where they cross mid-life; wind = 135 (degrees, 0 = right, 90 = down) ± spread 45;
 *         speed = [1, 9] px per frame; flakes = 1 (the last ones); radius 1.5–2.2 (flake 3.4), opacity 0.45–0.70.
 *       + fade = 4, wobble = 2.2, wobblePeriod = 26, samples = 5, shutter = 0.5 (frames between first and last sample).
 *       + T3.her.motes.at(f, o) → [{ i, flake, x, y, r, al, rot }]: the samples it would draw, in draw order (al = each
 *         sample's opacity, rot = a flake's turn in radians). + T3.her.motes.S9: the sample's eight motes (frozen).
 *
 * Sources (read-only, copied as written; constants that were the shot's own became options with the shot's values):
 *   house 2D hair/veil wave reference: camera 39-46 (cosE, camera, scr),
 *     dist 48-59, hairSway 61-74, veilSway 76-89, motes 91-127, mover (two-pass warp) 129-159, blink 178-182;
 *     the rig it reads is s9_rig.js (window.S9_RIG).
 *   gaze and glance: house eye-state sample:532 (smoothstep over 3 f) and :558 (one 50 % frame), the
 *     4-frame blink again at :560; the same shapes in rank5 intro_cla.js:426, 428 and intro_gpt.js:855, 869-870.
 * Approval: A. The sample her_2d_motion_v1 is approved in crafts.md's registry (her small moves: hair and veil wave, the
 *   eased blink and every eye change; style-grammar §6d). The eye states: the client's rank4 v14 and v15 notes (blink
 *   and gaze eased like the sample, gaze cross-dissolved with no middle drawing), quoted in intro_gpt.js:529-530, 551-557.
 * Tests: assets/examples/motion/test_her2d.mjs (equal to the source formulas, copied verbatim, max abs diff <= 1e-9 on a
 *   frame grid; the warp's mesh and the motes through a recording canvas). Pixel test, kept outside the skill because it
 *   verify visually on separated 2D illustration layers (plate + hair + veil + eyes) on this file
 *   against the approved page).
 */
(function () {
  'use strict';
  const err = (msg) => Object.assign(new Error('lib/motion/her2d.js: ' + msg), { name: 'T3MotionError' });
  const T3 = window.T3;
  if (!T3) throw err('engine.js is not loaded: load it first (motion-library «Setup»)');
  if (T3.her) {
    if (T3.her.__her2d) return;   // loaded twice: keep the first
    throw err('T3.her is already defined by another script; her2d.js does not overwrite it');
  }
  const TAU = Math.PI * 2;
  const def = (v, d) => (v == null ? d : v);
  const sm = (x) => { x = x < 0 ? 0 : x > 1 ? 1 : x; return x * x * (3 - 2 * x); };   // s9_shot.js:23
  const pair = (v, name) => {
    if (typeof v === 'number') return [v, v];
    if (Array.isArray(v) && v.length === 2 && v.every(Number.isFinite)) return v;
    throw err(`option ${name} must be a number or [a, b]`);
  };

  // ---- her.wave: distance to the root polyline (s9_shot.js:49-59, as written) ----------------------------------
  function dist(x, y, poly) {
    let best = 1e9;
    for (let i = 0; i + 1 < poly.length; i++) {
      const x0 = poly[i][0], y0 = poly[i][1], dx = poly[i + 1][0] - x0, dy = poly[i + 1][1] - y0;
      const L2 = dx * dx + dy * dy || 1e-9;
      let t = ((x - x0) * dx + (y - y0) * dy) / L2; t = t < 0 ? 0 : t > 1 ? 1 : t;
      const ex = x - (x0 + t * dx), ey = y - (y0 + t * dy), d = ex * ex + ey * ey;
      if (d < best) best = d;
    }
    return Math.sqrt(best);
  }
  const HAIR = Object.freeze({ period: 33, tx: 26.0, ty: 25.4, lagX: 0.036, lagY: 0.0125, ref: 75, yr: 0.4, amp: [1.45, 5.2],
    ampLen: 520, ampVar: 0.18, jitter: 1.5, pin: [6, 70], gain: 1 });
  const VEIL = Object.freeze({ period: 31, tx: [22, 33], ty: [21, 26], yr: 0.34, amp: [0.75, 2.75], ampAt: [0.1, 0.65], pin: [5, 65],
    shiver: 0.45, shiverPeriod: 9, shiverLen: 160, shiverAt: [0.6, 0.95], gain: 1 });

  function wave(rig, f, o) {
    o = o || {};
    if (!rig || !Array.isArray(rig.root) || rig.root.length < 2) throw err('T3.her.wave(rig, f, o): rig.root must be a polyline [[x, y], …] of 2 or more points in layer px');
    if (!Number.isFinite(f)) throw err('T3.her.wave: f must be a finite frame number');
    const preset = def(o.preset, 'hair');
    if (preset !== 'hair' && preset !== 'veil') throw err(`T3.her.wave: unknown preset "${preset}" (hair or veil)`);
    const p = Object.assign({}, preset === 'veil' ? VEIL : HAIR, o);
    const root = rig.root, P = p.period, g = p.gain, yr = p.yr;
    const pn = pair(p.pin, 'pin'), pin0 = pn[0], pinW = pn[1] - pn[0];
    const am = pair(p.amp, 'amp'), a0 = am[0], aD = am[1] - am[0];
    if (preset === 'veil') {
      // veilSway (s9_shot.js:80-89), the shot's numbers as options
      const len = rig.len;
      if (!(len > 0)) throw err('T3.her.wave: the veil preset needs rig.len (root-to-tail length in px)');
      const ua = pair(p.ampAt, 'ampAt'), u0 = ua[0], uW = ua[1] - ua[0];
      const tx = pair(p.tx, 'tx'), tx0 = tx[0], txD = tx[1] - tx[0], ty = pair(p.ty, 'ty'), ty0 = ty[0], tyD = ty[1] - ty[0];
      const sa = pair(p.shiverAt, 'shiverAt'), sh0 = sa[0], shW = sa[1] - sa[0], sh = p.shiver, shP = p.shiverPeriod, shL = p.shiverLen;
      return function veilField(x, y) {
        const s = dist(x, y, root), u = Math.min(1, s / len);
        const pin = sm((s - pin0) / pinW);
        if (pin <= 0) return [0, 0, 0];
        const amp = (a0 + aD * sm((u - u0) / uW)) * pin * g;
        const tL = tx0 + txD * Math.pow(u, 1.2), tU = ty0 + tyD * u * u;
        let dx = -amp * Math.cos(TAU * (f - tL) / P), dy = -yr * amp * Math.cos(TAU * (f - tU) / P);
        dy += sh * g * sm((u - sh0) / shW) * Math.sin(TAU * (f / shP - s / shL));   // the tail's shiver
        return [dx, dy, pin];
      };
    }
    // hairSway (s9_shot.js:64-74), the shot's numbers as options
    const fan = rig.fan;
    if (!Array.isArray(fan) || !Number.isFinite(fan[0]) || !Number.isFinite(fan[1])) throw err('T3.her.wave: the hair preset needs rig.fan = [x, y], the point the strands fan out from (layer px)');
    const fx = fan[0], fy = fan[1], aLen = p.ampLen, av = p.ampVar, jt = p.jitter, ref = p.ref;
    const tL0 = p.tx, tU0 = p.ty, lagX = p.lagX, lagY = p.lagY;
    return function hairField(x, y) {
      const s = dist(x, y, root);
      const pin = sm((s - pin0) / pinW);                  // held within pin0 px of the root, free from pin1 px
      if (pin <= 0) return [0, 0, 0];
      const a = Math.atan2(y - fy, fx - x);                // across the strands: each strand its own phase
      const amp = (a0 + aD * sm(s / aLen)) * (1 + av * Math.sin(a * 31 + 0.7)) * pin * g;
      const jit = jt * Math.sin(a * 19 + 2.1);             // neighbouring strands ± jitter frames, never in step
      const tL = tL0 + lagX * (s - ref) + jit, tU = tU0 + lagY * (s - ref) + jit;
      return [-amp * Math.cos(TAU * (f - tL) / P), -yr * amp * Math.cos(TAU * (f - tU) / P), pin];
    };
  }

  // ---- her.camera (s9_shot.js:40-46) -------------------------------------------------------------------------------
  const cosE = (f, a, b) => { const k = Math.min(1, Math.max(0, (f - a) / (b - a))); return (1 - Math.cos(Math.PI * k)) / 2; };
  function cam(f, f0, f1, o) {
    o = o || {};
    if (!Number.isFinite(f)) throw err('T3.her.cam: f must be a finite frame number');
    if (!Number.isFinite(f0) || !Number.isFinite(f1) || !(f1 > f0)) throw err('T3.her.cam(f, f0, f1, o): need finite frames with f1 > f0');
    const lag = pair(def(o.panLag, [0.75, 1]), 'panLag');
    if (!(f1 + lag[1] > f0 + lag[0])) throw err('T3.her.cam: panLag leaves the pan no time');
    const S0 = 1 + def(o.over, 0.02), kz = cosE(f, f0, f1), kp = cosE(f, f0 + lag[0], f1 + lag[1]);
    return { s: S0 * (1 + (def(o.zoom, 1.0755) - 1) * kz), x: -def(o.pan, 88.6) * kp, y: -def(o.panY, 0) * kp, cx: def(o.cx, 960), cy: def(o.cy, 540) };
  }
  function pt(c, x, y) {                                   // scr (s9_shot.js:46)
    if (!c) return [x, y];
    const cx = def(c.cx, 960), cy = def(c.cy, 540);
    return [cx + c.x + c.s * (x - cx), cy + c.y + c.s * (y - cy)];
  }
  function matrix(c, kx, ky) {                             // the setTransform of s9_shot.js:175, 184, 188
    kx = def(kx, 1); ky = def(ky, kx);
    if (!c) return [kx, 0, 0, ky, 0, 0];
    const cx = def(c.cx, 960), cy = def(c.cy, 540);
    return [c.s * kx, 0, 0, c.s * ky, cx + c.x - c.s * cx, cy + c.y - c.s * cy];
  }
  cam.pt = pt;
  cam.matrix = matrix;
  Object.freeze(cam);

  // ---- her.wave: the two-pass alpha warp (s9_shot.js:130-159) ------------------------------------------------------
  const ZERO = Object.freeze([0, 0]);
  const off = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
  const copies = new WeakMap();                            // img → Map(key → its two opaque copies and warpers)
  function layer(img, box, cols, rows, seam, W, H, fresh) {
    const key = box.join(',') + '|' + cols + 'x' + rows + '|' + seam + '|' + W + 'x' + H;
    let m = copies.get(img);
    if (!m) copies.set(img, (m = new Map()));
    let L = fresh ? null : m.get(key);
    if (L) return L;
    const [x0, y0, x1, y1] = box, cw = x1 - x0, ch = y1 - y0;
    const col = off(cw, ch), cc = col.getContext('2d');            // colour × a on black, opaque
    cc.fillStyle = '#000'; cc.fillRect(0, 0, cw, ch); cc.drawImage(img, -x0, -y0);
    const tmp = off(cw, ch), tc = tmp.getContext('2d');             // white × (1 − a)
    tc.fillStyle = '#fff'; tc.fillRect(0, 0, cw, ch); tc.globalCompositeOperation = 'destination-out'; tc.drawImage(img, -x0, -y0);
    const inv = off(cw, ch), ic = inv.getContext('2d');             // 1 − a as grey, opaque
    ic.fillStyle = '#000'; ic.fillRect(0, 0, cw, ch); ic.drawImage(tmp, 0, 0);
    const outC = off(W, H), outI = off(W, H), mo = { cols, rows };
    if (seam != null) mo.seam = seam;
    L = { outC, outI, mwC: T3.meshwarp(null, Object.assign({ img: col, canvas: outC }, mo)), mwI: T3.meshwarp(null, Object.assign({ img: inv, canvas: outI }, mo)) };
    if (!fresh) m.set(key, L);
    return L;
  }
  function warp2(ctx, img, mesh, field) {
    if (typeof T3.meshwarp !== 'function') throw err('T3.her.warp2 needs lib/meshwarp.js: load it after engine.js');
    if (!ctx || !ctx.canvas) throw err('T3.her.warp2(ctx, img, mesh, field): ctx must be a 2D canvas context');
    if (!img) throw err('T3.her.warp2: img is missing');
    if (field != null && typeof field !== 'function') throw err('T3.her.warp2: field must be a function (x, y) → [dx, dy] or null');
    const iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;
    if (!(iw > 0 && ih > 0)) return false;                 // not loaded yet: nothing drawn (as T3.meshwarp)
    mesh = mesh || {};
    const box = mesh.box || [0, 0, iw, ih];
    if (!Array.isArray(box) || box.length !== 4 || !(box[2] > box[0] && box[3] > box[1])) throw err('T3.her.warp2: mesh.box must be [x0, y0, x1, y1] with x1 > x0, y1 > y0');
    const W = ctx.canvas.width, H = ctx.canvas.height;
    const sc = mesh.scale == null ? [W / iw, H / ih] : pair(mesh.scale, 'mesh.scale'), KX = sc[0], KY = sc[1];
    const L = layer(img, box, def(mesh.cols, 12), def(mesh.rows, 12), mesh.seam, W, H, !!mesh.fresh);
    const x0 = box[0], y0 = box[1], cw = box[2] - x0, ch = box[3] - y0, c = mesh.cam || null;
    const fn = (u, v) => {
      const lx = (x0 + u * cw) * KX, ly = (y0 + v * ch) * KY, d = field ? field(lx, ly) : ZERO;
      const p = pt(c, lx + d[0], ly + d[1]);
      return [p[0] - u * W, p[1] - v * H];
    };
    L.mwC.render(fn); L.mwI.render(fn);
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(L.outI, 0, 0);
    ctx.globalCompositeOperation = 'lighter'; ctx.drawImage(L.outC, 0, 0);
    ctx.restore();
    return true;
  }

  // ---- her.eyes (s9_shot.js:178; rank4 intro_gpt.js:532, 558, 560) -------------------------------------------------
  const BLINK = [0.5, 1, 1, 0.5];
  function event(e) {
    if (!e || typeof e !== 'object') throw err('T3.her.eyes: an event is { blink: at }, { gaze: at, dur, to }, { glance: at, to } or { kind, at, … }');
    let kind = e.kind, at = e.at;
    if (kind == null) for (const k of ['blink', 'gaze', 'glance']) if (e[k] != null) { kind = k; at = e[k]; }
    if (kind !== 'blink' && kind !== 'gaze' && kind !== 'glance') throw err(`T3.her.eyes: unknown event ${kind == null ? JSON.stringify(e) : `kind "${kind}"`} (blink, gaze, glance)`);
    if (!Number.isFinite(at)) throw err(`T3.her.eyes: the ${kind} event needs a frame number`);
    const dur = def(e.dur, 3), to = def(e.to, 1);
    if (kind === 'gaze' && !(dur > 0)) throw err('T3.her.eyes: a gaze needs dur > 0 (2–3 frames)');
    if (!(to >= 0 && to <= 1)) throw err('T3.her.eyes: `to` is an opacity, 0..1');
    return { kind, at, dur, to };
  }
  function eyes(f, events) {
    if (!Number.isFinite(f)) throw err('T3.her.eyes: f must be a finite frame number');
    const list = (events == null ? [] : Array.isArray(events) ? events : [events]).map(event);
    let blink = 0;
    const steps = [];
    for (const e of list) {
      if (e.kind !== 'blink') { steps.push(e); continue; }
      const i = Math.floor(f - e.at);                      // held per frame: the drawn states are never in-betweened
      if (i >= 0 && i < 4 && BLINK[i] > blink) blink = BLINK[i];
    }
    steps.sort((a, b) => a.at - b.at);
    let v = 0;
    for (const e of steps) {
      if (f < e.at) break;
      let w;
      if (e.kind === 'gaze') { const t = Math.min(1, Math.max(0, (f - e.at) / e.dur)); w = t * t * (3 - 2 * t); }   // rank4 :532
      else w = f >= e.at + 1 ? 1 : 0.5;                                                                     // rank4 :558
      v = v + (e.to - v) * w;
    }
    return v > blink ? v : blink;
  }

  // ---- her.motes (s9_shot.js:92-127) ---------------------------------------------------------------------------------
  const S9 = Object.freeze([
    { x: 1020, y: -6, vx: -0.7, vy: 6.5, r: 1.9, a: 0.70, f0: -4, f1: 34 },
    { x: 1000, y: 70, vx: -5.4, vy: 5.4, r: 2.2, a: 0.65, f0: 22, f1: 44 },
    { x: 868, y: 112, vx: -0.5, vy: 5.5, r: 1.6, a: 0.55, f0: 0, f1: 31 },
    { x: 1520, y: 300, vx: -8.0, vy: 0.5, r: 2.0, a: 0.60, f0: 16, f1: 26 },
    { x: 455, y: 392, vx: -8.8, vy: 0.9, r: 3.4, a: 0.55, f0: -4, f1: 46, flake: 1 },
    { x: 1610, y: 520, vx: -0.9, vy: 0.4, r: 1.5, a: 0.50, f0: -6, f1: 46 },
    { x: 560, y: 610, vx: -2.6, vy: 1.8, r: 2.0, a: 0.45, f0: -6, f1: 46 },
    { x: 760, y: 470, vx: -4.2, vy: 1.3, r: 1.6, a: 0.50, f0: 4, f1: 46 },
  ].map(Object.freeze));
  function rng(seed) {                                     // mulberry32: a seeded sequence, local to one call
    let a = seed | 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function generate(o) {
    const n = def(o.n, 8), R = rng(def(o.seed, 1)), span = pair(def(o.span, [0, 48]), 'span'), box = def(o.box, [0, 0, 1920, 1080]);
    const wind = def(o.wind, 135), spread = def(o.spread, 45), sp = pair(def(o.speed, [1, 9]), 'speed'), flakes = def(o.flakes, 1);
    if (!(n >= 0) || n !== Math.floor(n)) throw err('T3.her.motes: n must be a whole number');
    const lerp = (a, b, k) => a + (b - a) * k, out = [];
    for (let i = 0; i < n; i++) {
      const flake = i >= n - flakes;
      const ang = ((wind + (2 * R() - 1) * spread) * Math.PI) / 180, v = lerp(sp[0], sp[1], R());
      const vx = Math.cos(ang) * v, vy = Math.sin(ang) * v;
      const f0 = span[0] - 6 + R() * (span[1] - span[0]) * 0.5, f1 = Math.min(span[1] + 6, f0 + lerp(10, 52, R()));
      const mx = lerp(box[0], box[2], R()), my = lerp(box[1], box[3], R()), half = (f1 - f0) / 2;
      out.push({ x: mx - vx * half, y: my - vy * half, vx, vy, r: flake ? 3.4 : lerp(1.5, 2.2, R()), a: flake ? 0.55 : lerp(0.45, 0.7, R()), f0, f1, flake: flake ? 1 : 0 });
    }
    return out;
  }
  function motesAt(f, o) {
    o = o || {};
    if (!Number.isFinite(f)) throw err('T3.her.motes: f must be a finite frame number');
    const list = o.list || (o.seed != null ? generate(o) : S9);
    if (!Array.isArray(list)) throw err('T3.her.motes: list must be an array of motes');
    const c = o.cam || null, cs = c ? c.s : 1;
    const fade = def(o.fade, 4), wa = def(o.wobble, 2.2), wp = def(o.wobblePeriod, 26), N = def(o.samples, 5), sh = def(o.shutter, 0.5);
    if (!(N >= 1) || N !== Math.floor(N)) throw err('T3.her.motes: samples must be a whole number >= 1');
    const step = N > 1 ? sh / (N - 1) : 0, first = N > 1 ? sh / 2 : 0, out = [];
    for (let i = 0; i < list.length; i++) {
      const m = list[i];
      const vis = Math.min(sm((f - m.f0) / fade), sm((m.f1 - f) / fade));
      if (vis <= 0) continue;
      for (let k = 0; k < N; k++) {                        // its own shutter: N samples spread over `shutter` frames
        const ff = f - first + step * k, df = ff - m.f0;
        const wob = Math.sin(TAU * (ff / wp + i * 0.37)) * wa;          // a slight sway across its path
        const L = Math.hypot(m.vx, m.vy) || 1;
        const lx = m.x + m.vx * df - (m.vy / L) * wob, ly = m.y + m.vy * df + (m.vx / L) * wob;
        const p = pt(c, lx, ly);
        out.push({ i, flake: !!m.flake, x: p[0], y: p[1], r: m.r * cs, al: m.a * vis / N, rot: 0.6 + ff * 0.09 });
      }
    }
    return out;
  }
  function motes(ctx, f, o) {
    if (!ctx || typeof ctx.createRadialGradient !== 'function') throw err('T3.her.motes(ctx, f, o): ctx must be a 2D canvas context');
    const S = motesAt(f, o);
    ctx.save();
    for (const p of S) {
      const r = p.r, al = p.al;
      if (p.flake) {
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.scale(1.7, 0.75);
        const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r * 1.6);
        g.addColorStop(0, `rgba(255,246,232,${(al * 1.6).toFixed(4)})`); g.addColorStop(0.45, `rgba(255,240,222,${(al * 0.9).toFixed(4)})`); g.addColorStop(1, 'rgba(255,236,215,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r * 1.6, 0, TAU); ctx.fill(); ctx.restore();
      } else {
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 2.2);
        g.addColorStop(0, `rgba(255,248,236,${(al * 1.8).toFixed(4)})`); g.addColorStop(0.35, `rgba(255,242,224,${(al * 0.8).toFixed(4)})`); g.addColorStop(1, 'rgba(255,238,218,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, r * 2.2, 0, TAU); ctx.fill();
      }
    }
    ctx.restore();
    return new Set(S.map((p) => p.i)).size;
  }
  motes.at = motesAt;
  motes.S9 = S9;
  Object.freeze(motes);

  const her = { wave, warp2, eyes, cam, motes };
  Object.defineProperty(her, '__her2d', { value: 1 });   // marks our own T3.her (a second load keeps the first)
  T3.her = Object.freeze(her);
  if (window.__T3_MOTION && window.__T3_MOTION.modules) window.__T3_MOTION.modules.push('her2d');
})();
