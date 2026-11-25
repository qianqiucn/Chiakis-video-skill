/* look_fx.js — Reusable Material, Print-Plate, Live-Footage Luma Matte, OKLCH Walk & Per-Shot Coat Kit (window.T3.look).
 *
 * Pure deterministic Canvas 2D primitives so textures, live-action footage, print shaders, and optical transitions
 * live INSIDE each shot's physical world (instead of slapping one grey multiply glass sheet over the whole film).
 *
 * Load AFTER engine.js (and lib/motion/moves.js if using T3.look.framed). Zero external dependencies; offline file:// safe.
 *
 * Library IDs (registered in references/motion-library.md):
 *   - trans.ground-walk  : T3.look.okMix(hexA, hexB, k, hintHex, bump)
 *   - trans.luma-matte   : T3.look.lumaMatte(ctx, fromSrc, toSrc, maskImg, opts)
 *   - fx.print-plate     : T3.look.bakePrint(img, h) + T3.look.drawPrint(ctx, baked, mode, opts)
 *
 * Additional helpers:
 *   - T3.look.coat(ctx, f, opts)                       Per-shot paper / 35mm grain / dust / scanline coat (0 = skip layer)
 *   - T3.look.monoSpline(keys)                         Fritsch–Carlson monotone cubic Hermite spline (exact vocal onset lock)
 *   - T3.look.framed(id, src, f, f0, dir, opts)        Living drift + overscan framing via T3.mv.settle (zero parked frames)
 *   - T3.look.tint(canvas, color)                      Cached alpha-recolor helper
 */
(function () {
  'use strict';
  if (!window.T3) throw new Error('look_fx.js: load engine.js before lib/look_fx.js');
  const T3 = window.T3;
  const W0 = 1920, H0 = 1080, PI = Math.PI;
  const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, k) => a + (b - a) * k;

  function mkCv(w, h) {
    const c = document.createElement('canvas');
    c.width = Math.max(1, Math.round(w));
    c.height = Math.max(1, Math.round(h));
    return c;
  }

  function parseHex(h) {
    const s = String(h || '#000000').replace('#', '').trim();
    const full = s.length === 3 ? s.split('').map((ch) => ch + ch).join('') : s.padEnd(6, '0');
    return [parseInt(full.slice(0, 2), 16) || 0, parseInt(full.slice(2, 4), 16) || 0, parseInt(full.slice(4, 6), 16) || 0];
  }

  // ---- 1. OKLCH Perceptual Ground Walk (trans.ground-walk) ----
  const s2l = (c) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const l2s = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055);
  function hexToOkLab(hx) {
    const [r, g, b] = parseHex(hx).map((v) => s2l(v / 255));
    const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
    const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
    const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    return [
      0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
      1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
      0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
    ];
  }
  function okLabToHex([Lv, a, b]) {
    const l = (Lv + 0.3963377774 * a + 0.2158037573 * b) ** 3;
    const m = (Lv - 0.1055613458 * a - 0.0638541728 * b) ** 3;
    const s = (Lv - 0.0894841775 * a - 1.291485548 * b) ** 3;
    const rgb = [
      4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
      -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
      -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
    ];
    return '#' + rgb.map((v) => Math.round(clamp(l2s(clamp(v))) * 255).toString(16).padStart(2, '0')).join('');
  }

  function okMix(hexA, hexB, k, hintHex, bump = 0.08) {
    const q = clamp(k);
    if (q <= 0) return '#' + parseHex(hexA).map((v) => v.toString(16).padStart(2, '0')).join('');
    if (q >= 1) return '#' + parseHex(hexB).map((v) => v.toString(16).padStart(2, '0')).join('');
    const A = hexToOkLab(hexA), B = hexToOkLab(hexB), H = hexToOkLab(hintHex || '#1342FF');
    const ch = (p) => [Math.hypot(p[1], p[2]), Math.atan2(p[2], p[1])];
    const [CA, hA] = ch(A), [CB, hB] = ch(B), hH = ch(H)[1];
    const ua = CA > 0.04, ub = CB > 0.04;
    let h;
    if (ua && ub) {
      let d = hB - hA;
      while (d > PI) d -= 2 * PI;
      while (d < -PI) d += 2 * PI;
      h = hA + d * q;
    } else {
      h = ua ? hA : ub ? hB : hH;
    }
    const C = lerp(CA, CB, q) + bump * Math.sin(PI * q);
    return okLabToHex([lerp(A[0], B[0], q), C * Math.cos(h), C * Math.sin(h)]);
  }

  // ---- 2. Cached Alpha Recoloring ----
  const TINT_CACHE = new WeakMap();
  function tint(canvasOrImg, color) {
    let m = TINT_CACHE.get(canvasOrImg);
    if (!m) TINT_CACHE.set(canvasOrImg, (m = {}));
    if (m[color]) return m[color];
    const w = canvasOrImg.naturalWidth || canvasOrImg.width || 1;
    const h = canvasOrImg.naturalHeight || canvasOrImg.height || 1;
    const o = mkCv(w, h), x = o.getContext('2d');
    x.drawImage(canvasOrImg, 0, 0, w, h);
    x.globalCompositeOperation = 'source-in';
    x.fillStyle = color;
    x.fillRect(0, 0, w, h);
    return (m[color] = o);
  }

  // ---- 3. Stylized Print-Plate Baker & Renderer (fx.print-plate) ----
  const PRINT_CACHE = new Map();
  function bakePrint(img, hTarget = 1080) {
    if (!img) return null;
    const nw = img.naturalWidth || img.width || 0;
    const nh = img.naturalHeight || img.height || 0;
    if (!nw || !nh) return null;
    const ht = Math.round(hTarget || 1080);
    const cacheKey = (img.src || '') + '@' + ht + ':' + nw + 'x' + nh;
    if (img.src && PRINT_CACHE.has(cacheKey)) return PRINT_CACHE.get(cacheKey);

    const sc = ht / nh, w = Math.max(1, Math.round(nw * sc)), h = ht;
    const src = mkCv(w, h), xs = src.getContext('2d');
    xs.drawImage(img, 0, 0, w, h);
    const S = xs.getImageData(0, 0, w, h).data, N = w * h;
    const L = new Float32Array(N), A = new Float32Array(N);
    for (let i = 0; i < N; i++) {
      const a = S[i * 4 + 3] / 255;
      A[i] = a;
      L[i] = a < 0.02 ? 1 : ((0.299 * S[i * 4] + 0.587 * S[i * 4 + 1] + 0.114 * S[i * 4 + 2]) / 255) * a + (1 - a);
    }

    // Blurred continuous tone map so hatching density becomes smooth shading
    const gl = mkCv(w, h), xg = gl.getContext('2d'), gd = xg.createImageData(w, h);
    for (let i = 0; i < N; i++) {
      const v = L[i] * 255;
      gd.data[i * 4] = gd.data[i * 4 + 1] = gd.data[i * 4 + 2] = v;
      gd.data[i * 4 + 3] = 255;
    }
    xg.putImageData(gd, 0, 0);
    const bl = mkCv(w, h), xb = bl.getContext('2d');
    xb.filter = `blur(${Math.max(1.6, ht / 380).toFixed(2)}px)`;
    xb.drawImage(gl, 0, 0);
    const BD = xb.getImageData(0, 0, w, h).data;

    const mkLayer = () => { const c = mkCv(w, h), x = c.getContext('2d'); return { c, x, d: x.createImageData(w, h) }; };
    const K = mkLayer(), SI = mkLayer(), LS = mkLayer(), SH = mkLayer();
    const per = Math.max(5.2, ht / 150), ca = Math.cos(PI / 3), sa = Math.sin(PI / 3);
    for (let i = 0; i < N; i++) {
      const a = A[i];
      if (a < 0.04) continue;
      const lum = L[i], tone = BD[i * 4] / 255;
      const k = clamp((0.66 - lum) / 0.42) * a;
      if (k > 0) { K.d.data[i * 4] = K.d.data[i * 4 + 1] = K.d.data[i * 4 + 2] = 255; K.d.data[i * 4 + 3] = k * 255; }
      SI.d.data[i * 4] = SI.d.data[i * 4 + 1] = SI.d.data[i * 4 + 2] = 255;
      SI.d.data[i * 4 + 3] = clamp(a * 1.4) * 255;
      const xx = i % w, yy = (i / w) | 0;
      const u = (xx * ca + yy * sa) / per, fr = u - Math.floor(u), dist = Math.min(fr, 1 - fr) * per;
      const v = clamp((0.97 - tone) / 0.62), al = clamp(v * per * 0.55 - dist + 0.5) * a;
      if (al > 0) { LS.d.data[i * 4] = LS.d.data[i * 4 + 1] = LS.d.data[i * 4 + 2] = 255; LS.d.data[i * 4 + 3] = al * 255; }
      const sh = clamp((0.6 - tone) / 0.08) * a;
      if (sh > 0) { SH.d.data[i * 4] = SH.d.data[i * 4 + 1] = SH.d.data[i * 4 + 2] = 255; SH.d.data[i * 4 + 3] = sh * 255; }
    }
    K.x.putImageData(K.d, 0, 0); SI.x.putImageData(SI.d, 0, 0); LS.x.putImageData(LS.d, 0, 0); SH.x.putImageData(SH.d, 0, 0);

    const dotPlate = (angDeg, cell, valFn) => {
      const c = mkCv(w, h), x = c.getContext('2d');
      x.fillStyle = '#fff';
      x.beginPath();
      const c2 = Math.cos((angDeg * PI) / 180), s2 = Math.sin((angDeg * PI) / 180);
      const R = Math.hypot(w, h) / 2 + cell;
      for (let v = -R; v < R; v += cell) {
        for (let u = -R; u < R; u += cell) {
          const px = w / 2 + u * c2 - v * s2, py = h / 2 + u * s2 + v * c2;
          if (px < 0 || py < 0 || px >= w || py >= h) continue;
          const idx = (py | 0) * w + (px | 0);
          if (A[idx] < 0.3) continue;
          const tv = clamp(valFn(idx));
          if (tv < 0.04) continue;
          const rad = cell * 0.5 * Math.sqrt(tv) * 1.32;
          x.moveTo(px + rad, py);
          x.arc(px, py, rad, 0, 2 * PI);
        }
      }
      x.fill();
      return c;
    };
    const cell = Math.max(6, ht / 140);
    const dotA = dotPlate(15, cell, (i) => (0.98 - BD[i * 4] / 255) / 0.6);
    const dotK = dotPlate(45, cell, (i) => (0.5 - BD[i * 4] / 255) / 0.35);

    const out = { key: K.c, sil: SI.c, ls: LS.c, shd: SH.c, dotA, dotK, w, h };
    if (img.src) PRINT_CACHE.set(cacheKey, out);
    return out;
  }

  function drawPrint(ctx, B, mode, opts = {}) {
    if (!B) return;
    const a = opts.a || '#1342FF', b = opts.b || '#E81C4F', paper = opts.paper || '#F4EFE6', ink = opts.ink || '#111216';
    const hh = opts.h || B.h, ww = (B.w * hh) / B.h;
    const off = opts.off || 0, ang = opts.ang != null ? opts.ang : -0.62;
    const ox = Math.cos(ang) * off, oy = Math.sin(ang) * off;
    ctx.save();
    ctx.translate(opts.x != null ? opts.x : W0 / 2, opts.y != null ? opts.y : H0 / 2);
    if (opts.rot) ctx.rotate(opts.rot);
    if (opts.flip) ctx.scale(-1, 1);
    if (opts.alpha != null) ctx.globalAlpha *= opts.alpha;
    const x0 = -ww / 2, y0 = -hh / 2;
    const d = (c, dx = 0, dy = 0) => ctx.drawImage(c, x0 + dx, y0 + dy, ww, hh);

    if (mode === 'screen') {
      d(tint(B.sil, b), ox, oy);
      d(tint(B.sil, paper));
      d(tint(B.ls, a));
      d(tint(B.key, ink));
    } else if (mode === 'dots') {
      d(tint(B.sil, paper));
      ctx.save();
      ctx.globalCompositeOperation = 'multiply';
      d(tint(B.dotA, b), ox, oy);
      d(tint(B.dotA, a));
      if (opts.k !== false) d(tint(B.dotK, ink));
      ctx.restore();
      d(tint(B.key, ink));
    } else if (mode === 'neg') {
      d(tint(B.sil, b), ox, oy);
      d(tint(B.sil, ink));
      d(tint(B.ls, a));
      d(tint(B.key, paper));
    } else if (mode === 'sil') {
      ctx.save();
      ctx.globalAlpha *= opts.bAlpha != null ? opts.bAlpha : 0.92;
      d(tint(B.sil, b), ox, oy);
      ctx.restore();
      d(tint(B.sil, a));
      d(tint(B.shd, ink));
      d(tint(B.key, paper));
    } else if (mode === 'two') {
      d(tint(B.sil, paper));
      ctx.save();
      ctx.globalCompositeOperation = 'multiply';
      d(tint(B.ls, b), ox, oy);
      d(tint(B.ls, a), -ox, -oy);
      ctx.restore();
      d(tint(B.key, ink));
    } else {
      d(tint(B.key, ink));
    }
    ctx.restore();
  }

  // ---- 4. Real Live-Action Footage Luminance-Matte Transition (trans.luma-matte) ----
  const MASK_CACHE = new Map();
  let _matteBuf = null;
  function buildAlphaMask(maskImg, opts = {}) {
    const mw = opts.maskWidth || 640, mh = opts.maskHeight || 360;
    const inv = !!opts.invert;
    const thr = opts.threshold != null ? opts.threshold : null;
    const soft = Math.max(0.01, opts.softness != null ? opts.softness : 0.14);
    const key = (maskImg.src || '') + `|${mw}x${mh}|${inv ? 1 : 0}|${thr}|${soft.toFixed(3)}`;
    if (maskImg.src && MASK_CACHE.has(key)) return MASK_CACHE.get(key);

    const c = mkCv(mw, mh), x = c.getContext('2d');
    x.drawImage(maskImg, 0, 0, mw, mh);
    const imgd = x.getImageData(0, 0, mw, mh), d = imgd.data;
    for (let i = 0; i < d.length; i += 4) {
      let lum = (0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]) / 255;
      if (inv) lum = 1 - lum;
      let a;
      if (thr != null) {
        a = clamp((lum - (thr - soft)) / (2 * soft));
      } else {
        // Auto-contrast stretch so white-on-black ink/smoke reveals cleanly to 100%
        a = clamp((lum - 0.08) / 0.78);
      }
      d[i] = d[i + 1] = d[i + 2] = 255;
      d[i + 3] = Math.round(a * 255);
    }
    x.putImageData(imgd, 0, 0);
    if (maskImg.src) {
      if (MASK_CACHE.size > 96) MASK_CACHE.clear();
      MASK_CACHE.set(key, c);
    }
    return c;
  }

  function lumaMatte(ctx, fromSrc, toSrc, maskImg, opts = {}) {
    const w = opts.width || ctx.canvas.width || W0;
    const h = opts.height || ctx.canvas.height || H0;
    if (fromSrc) ctx.drawImage(fromSrc, 0, 0, w, h);
    if (!toSrc || !maskImg) return;
    const mw = maskImg.naturalWidth || maskImg.width || 0;
    if (!mw) return;
    const alphaMask = buildAlphaMask(maskImg, opts);
    if (!_matteBuf || _matteBuf.width !== w || _matteBuf.height !== h) _matteBuf = mkCv(w, h);
    const bx = _matteBuf.getContext('2d');
    bx.save();
    bx.clearRect(0, 0, w, h);
    bx.drawImage(alphaMask, 0, 0, w, h);
    bx.globalCompositeOperation = 'source-in';
    bx.drawImage(toSrc, 0, 0, w, h);
    bx.restore();

    ctx.save();
    if (opts.alpha != null) ctx.globalAlpha *= opts.alpha;
    ctx.drawImage(_matteBuf, 0, 0, w, h);
    ctx.restore();
  }

  // ---- 5. Per-Shot Tactile Material Coat (replaces rigid full-film grey multiply blanket) ----
  const SCAN_CACHE = new Map();
  function getScanPattern(ctx, step = 4) {
    const k = Math.max(2, Math.round(step));
    if (SCAN_CACHE.has(k)) return SCAN_CACHE.get(k);
    const c = mkCv(4, k), x = c.getContext('2d');
    x.fillStyle = 'rgba(10, 12, 18, 0.85)';
    x.fillRect(0, 0, 4, Math.max(1, Math.floor(k / 3)));
    const p = ctx.createPattern(c, 'repeat');
    SCAN_CACHE.set(k, p);
    return p;
  }

  let _coatBuf = null;
  function coat(ctx, f, opts = {}) {
    const w = opts.width || ctx.canvas.width || W0;
    const h = opts.height || ctx.canvas.height || H0;
    const fi = Math.floor(f || 0);
    const jit = opts.jitter != null ? opts.jitter : 8;
    const fg = opts.faceGuard; // optional { x, y, r } soft radial protection over character face

    const ready = (img) => img && ((img.naturalWidth || img.width || 0) > 0);
    const drawLayer = (targetCtx) => {
      if (opts.paper && (opts.paperAlpha == null ? 0.26 : opts.paperAlpha) > 0.004 && ready(opts.paper)) {
        const ox = Math.floor((T3.rand(fi, 23) - 0.5) * jit * 2);
        const oy = Math.floor((T3.rand(fi, 29) - 0.5) * jit * 2);
        targetCtx.save();
        targetCtx.globalCompositeOperation = opts.paperBlend || 'multiply';
        targetCtx.globalAlpha = opts.paperAlpha != null ? opts.paperAlpha : 0.26;
        targetCtx.drawImage(opts.paper, ox - jit, oy - jit, w + jit * 2, h + jit * 2);
        targetCtx.restore();
      }
      if (opts.grain && (opts.grainAlpha == null ? 0.14 : opts.grainAlpha) > 0.004 && ready(opts.grain)) {
        const gx = Math.floor(T3.rand(fi, 11) * 96);
        const gy = Math.floor(T3.rand(fi, 17) * 96);
        targetCtx.save();
        targetCtx.globalCompositeOperation = opts.grainBlend || 'soft-light';
        targetCtx.globalAlpha = opts.grainAlpha != null ? opts.grainAlpha : 0.14;
        targetCtx.drawImage(opts.grain, -gx, -gy, w + 96, h + 96);
        targetCtx.restore();
      }
      if (opts.dust && (opts.dustAlpha == null ? 0.18 : opts.dustAlpha) > 0.004 && ready(opts.dust)) {
        const dx = Math.floor((T3.rand(fi, 37) - 0.5) * 40);
        const dy = Math.floor((T3.rand(fi, 41) - 0.5) * 40);
        targetCtx.save();
        targetCtx.globalCompositeOperation = opts.dustBlend || 'screen';
        targetCtx.globalAlpha = opts.dustAlpha != null ? opts.dustAlpha : 0.18;
        targetCtx.drawImage(opts.dust, dx - 20, dy - 20, w + 40, h + 40);
        targetCtx.restore();
      }
      if (opts.scanline && opts.scanline > 0.004) {
        const pat = getScanPattern(targetCtx, opts.scanlineStep || 4);
        if (pat) {
          targetCtx.save();
          targetCtx.globalAlpha = opts.scanline;
          targetCtx.fillStyle = pat;
          targetCtx.fillRect(0, 0, w, h);
          targetCtx.restore();
        }
      }
    };

    if (!fg) {
      drawLayer(ctx);
      return;
    }
    // With faceGuard: render coat into buffer, softly punch out character face, composite onto ctx
    if (!_coatBuf || _coatBuf.width !== w || _coatBuf.height !== h) _coatBuf = mkCv(w, h);
    const bx = _coatBuf.getContext('2d');
    bx.clearRect(0, 0, w, h);
    drawLayer(bx);
    bx.save();
    bx.globalCompositeOperation = 'destination-out';
    const gr = bx.createRadialGradient(fg.x, fg.y, (fg.r || 160) * 0.35, fg.x, fg.y, fg.r || 160);
    gr.addColorStop(0, `rgba(0,0,0,${fg.strength != null ? fg.strength : 0.85})`);
    gr.addColorStop(1, 'rgba(0,0,0,0)');
    bx.fillStyle = gr;
    bx.fillRect(0, 0, w, h);
    bx.restore();
    ctx.drawImage(_coatBuf, 0, 0, w, h);
  }

  // ---- 6. Monotone Cubic Spline (Fritsch–Carlson) & Continuous Living Frame ----
  function monoSpline(keys) {
    const n = keys.length;
    if (n < 2) return () => (n ? keys[0][1] : 0);
    const xs = keys.map((k) => k[0]), ys = keys.map((k) => k[1]);
    const d = [], m = new Array(n).fill(0);
    for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / Math.max(1e-9, xs[i + 1] - xs[i]));
    m[0] = d[0];
    m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
    // Fritsch–Carlson monotonicity clamp (guarantees zero overshoot across steep/flat vocal pauses)
    for (let i = 0; i < n - 1; i++) {
      if (Math.abs(d[i]) < 1e-12) { m[i] = 0; m[i + 1] = 0; continue; }
      const a = m[i] / d[i], b = m[i + 1] / d[i], s2 = a * a + b * b;
      if (s2 > 9) { const tau = 3 / Math.sqrt(s2); m[i] = tau * a * d[i]; m[i + 1] = tau * b * d[i]; }
    }
    return (f) => {
      if (f <= xs[0]) return ys[0] + (f - xs[0]) * m[0];
      if (f >= xs[n - 1]) return ys[n - 1] + (f - xs[n - 1]) * m[n - 1];
      let i = 0;
      while (i < n - 2 && f > xs[i + 1]) i++;
      const h = Math.max(1e-9, xs[i + 1] - xs[i]);
      const t = (f - xs[i]) / h, t2 = t * t, t3 = t2 * t;
      return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1];
    };
  }

  const FRAME_BUFS = new Map();
  function framed(id, srcCanvas, f, f0, dir = [1, 0], opts = {}) {
    const w = srcCanvas.width || W0, h = srcCanvas.height || H0;
    let out = FRAME_BUFS.get(id);
    if (!out || out.width !== w || out.height !== h) {
      out = mkCv(w, h);
      FRAME_BUFS.set(id, out);
    }
    const x = out.getContext('2d');
    const px = opts.px != null ? opts.px : 22;
    const sc = opts.scale != null ? opts.scale : 0.045;
    let dx = 0, dy = 0, s = 1;
    if (T3.mv && typeof T3.mv.settle === 'function') {
      const st = T3.mv.settle(f, f0, { pxPerSec: px, scale: sc, dir, span: opts.span || 48 });
      dx = st.x; dy = st.y; s = st.s;
    } else {
      const dt = Math.max(0, (f - f0) / (T3.FPS || 24));
      const d = Array.isArray(dir) ? dir : [1, 0];
      const len = Math.hypot(d[0], d[1]) || 1;
      dx = (d[0] / len) * px * Math.min(dt, 2.5);
      dy = (d[1] / len) * px * Math.min(dt, 2.5);
      s = 1 + sc * Math.min(dt / 2, 1.5);
    }
    // Overscan guarantee: scale always covers drift so zero canvas borders ever leak
    const minScale = 1 + (2 * Math.max(Math.abs(dx) / w, Math.abs(dy) / h)) + 0.006;
    const finalS = Math.max(s, minScale);
    x.save();
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.clearRect(0, 0, w, h);
    x.translate(w / 2 + dx, h / 2 + dy);
    x.scale(finalS, finalS);
    x.drawImage(srcCanvas, -w / 2, -h / 2, w, h);
    x.restore();
    return out;
  }

  T3.look = {
    okMix,
    tint,
    bakePrint,
    drawPrint,
    lumaMatte,
    coat,
    monoSpline,
    framed,
  };
})();
