/* choreo.js — entrances and exits for code elements (type, marks, HUD bits); load after engine.js.
 * Every helper is a pure function of the frame f (= Math.round(t * T3.FPS)): any seek order gives the same picture.
 *
 * T3.flick(f, f0, table)         power-on flicker for a code element's first appearance (usually a handful per intro):
 *     one level per frame from f0, the last one held, 0 before. table: an array or 'tube' | 'soft' | 'snap'.
 * T3.preglow(f, f0, fPeak, peak = 1, n = 4)   soft light where an element is about to appear: rises f0 → fPeak
 *     (the element's first frame), dies over n frames. Use it as the opacity of a radial-gradient div.
 * T3.decay(f, f0, v0, h)         landing without bounce: v0 · 2^(−(f − f0) / h), exactly 0 after 10 half-lives.
 *     Each channel gets its own half-life: x = X + T3.decay(f, F, -300, 1.5); scale = 1 + T3.decay(f, F, 0.4, 3).
 * T3.implode(f, opts) → { x, y, s: scale, o: opacity, k: progress }   2-frame outward jump, then 4–7 frames into a
 *     point; k >= 1 = absorbed, hide it. Usually once per intro, e.g. the tagline letters collapse into its full stop, which
 *     grows into the emblem (lib/emblem3d.js).
 *     opts = { f0, from: [x, y], to: [x, y], rank: 0 near … 1 far (starts up to 2 f later, lasts 4–7 f),
 *              jump: 40 (px), out: 2 (frames), dur (frames; default 6, or from rank), s1: 0.25 (end scale) }
 *       const p = T3.implode(f, { f0: 300, from: [cx, cy], to: [dotX, dotY], rank: Math.abs(cx - dotX) / 900 });
 *       span.style.transform = `translate(${p.x - cx}px, ${p.y - cy}px) scale(${p.s})`; span.style.opacity = p.k >= 1 ? 0 : p.o;
 *     Fast last frames: also draw a 30 % ghost at T3.implode(f - 1, opts) while k > 0.25 (anti-strobe at 24 fps).
 * T3.knockHalo(layer, id, opts) → 'url(#id)'   CSS filter for translucent type over a picture: a dark soft halo only
 *     OUTSIDE the glyphs; the glyph body keeps `glyph` alpha, so the picture shows through it. id: unique on the page.
 *     opts = { blur: 9 (≈ 7 % of the font size), dy: 3, halo: 0.85 (opacity), glyph: 0.5, color: '#050505' }
 * T3.stencil(layer, opts) → { svg, set(p) }   the name cut out of a dark plate. Build the moving picture in the layer
 *     first (multiplane, depth3d, Blender frames); it shows through the letters.
 *     opts = { text, size: 300, x (centre), y (baseline; default centres the capitals), length (textLength px: spreads
 *              the letter spacing), font: Segoe UI, weight: 700, plateColor: 'rgba(8,8,8,.86)',
 *              rimColor: 'rgba(255,255,255,.6)' or null, rimWidth: 1.5, W: 1920, H: 1080 }
 *     set({ length, x, y, size, plate, rim }) every frame (plate, rim = opacity 0–1); keys left out fall back to opts.
 * Stroked type (the rim, outlines): not Bahnschrift — a variable font, its inner overlap lines show. Use Segoe UI Bold
 * or Arial Black.
 */
(function () {
  const E = T3.ease, ramp = T3.ramp, lerp = T3.lerp;
  const svgEl = (tag, attrs, parent) => {
    const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };

  const TABLES = { tube: [0, 0.8, 0.95, 0, 0.75, 1], soft: [0, 0.45, 0.45, 0.3, 1], snap: [0.5, 1, 0, 1] };
  T3.flick = function (f, f0, table) {
    const tb = (typeof table === 'string' ? TABLES[table] : table) || TABLES.tube;
    const k = Math.floor(f - f0 + 1e-6);
    return k < 0 ? 0 : tb[Math.min(k, tb.length - 1)];
  };

  T3.preglow = function (f, f0, fPeak, peak, n) {
    peak = peak == null ? 1 : peak;
    if (f < f0) return 0;
    if (f < fPeak) return (peak * (f - f0)) / (fPeak - f0);
    return peak * (1 - E.outQuad(ramp(f, fPeak, fPeak + (n == null ? 4 : n))));
  };

  T3.decay = function (f, f0, v0, h) {
    const n = (f - f0) / (h || 1);
    return n <= 0 ? v0 : n >= 10 ? 0 : v0 * Math.pow(2, -n);
  };

  T3.implode = function (f, o) {
    const r = o.rank || 0, f0 = o.f0 + Math.round(2 * r);
    const out = o.out == null ? 2 : o.out, jump = o.jump == null ? 40 : o.jump;
    const dur = o.dur != null ? o.dur : o.rank != null ? 4 + Math.round(3 * r) : 6;
    const dx = o.from[0] - o.to[0], dy = o.from[1] - o.to[1], L = Math.hypot(dx, dy) || 1;
    const j = E.outCubic(ramp(f, f0, f0 + out)), k = E.inCubic(ramp(f, f0 + out, f0 + out + dur));
    const jx = o.from[0] + (dx / L) * jump * j, jy = o.from[1] + (dy / L) * jump * j;   // jump away from the point
    return { x: lerp(jx, o.to[0], k), y: lerp(jy, o.to[1], k), s: lerp(1, o.s1 == null ? 0.25 : o.s1, k), o: 1 - E.inQuad(k), k };
  };

  T3.knockHalo = function (layer, id, o) {
    o = Object.assign({ blur: 9, dy: 3, halo: 0.85, glyph: 0.5, color: '#050505' }, o || {});
    const holder = T3.el('div', { position: 'absolute', width: '0px', height: '0px', overflow: 'hidden' }, layer);
    holder.innerHTML = '<svg width="0" height="0"><defs>' +
      `<filter id="${id}" x="-20%" y="-50%" width="140%" height="200%" color-interpolation-filters="sRGB">` +
      `<feGaussianBlur in="SourceAlpha" stdDeviation="${o.blur}"/><feOffset dy="${o.dy}" result="b"/>` +
      '<feComposite in="b" in2="SourceAlpha" operator="out" result="ring"/>' +             // blurred alpha minus the glyphs
      `<feFlood flood-color="${o.color}" flood-opacity="${o.halo}"/><feComposite in2="ring" operator="in" result="halo"/>` +
      `<feComponentTransfer in="SourceGraphic" result="g"><feFuncA type="linear" slope="${o.glyph}"/></feComponentTransfer>` +
      '<feMerge><feMergeNode in="halo"/><feMergeNode in="g"/></feMerge></filter></defs></svg>';
    return `url(#${id})`;
  };

  let uid = 0;
  T3.stencil = function (layer, o) {
    o = Object.assign({ text: 'NAME', size: 300, x: null, y: null, length: 0, font: "'Segoe UI', Arial, sans-serif", weight: 700,
      plateColor: 'rgba(8,8,8,.86)', rimColor: 'rgba(255,255,255,.6)', rimWidth: 1.5, W: 1920, H: 1080 }, o || {});
    const W = o.W, H = o.H, id = 't3-stencil-' + ++uid;
    const svg = svgEl('svg', { width: W, height: H, style: 'position:absolute;left:0;top:0' }, layer);
    const mask = svgEl('mask', { id, maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, svgEl('defs', {}, svg));
    svgEl('rect', { width: W, height: H, fill: '#fff' }, mask);                         // white = the plate stays
    const word = (parent, attrs) => {
      const t = svgEl('text', Object.assign({ 'text-anchor': 'middle', 'font-family': o.font, 'font-weight': o.weight, lengthAdjust: 'spacing' }, attrs), parent);
      t.textContent = o.text;
      return t;
    };
    const hole = word(mask, { fill: '#000' });                                            // black = a hole in the plate
    const plate = svgEl('rect', { width: W, height: H, fill: o.plateColor, mask: `url(#${id})` }, svg);
    const rim = o.rimColor ? word(svg, { fill: 'none', stroke: o.rimColor, 'stroke-width': o.rimWidth }) : null;
    function set(p) {
      p = p || {};
      const size = p.size != null ? p.size : o.size, L = p.length != null ? p.length : o.length;
      const x = p.x != null ? p.x : o.x != null ? o.x : W / 2;
      const y = p.y != null ? p.y : o.y != null ? o.y : H / 2 + 0.35 * size;
      for (const t of rim ? [hole, rim] : [hole]) {
        t.setAttribute('x', x); t.setAttribute('y', y); t.setAttribute('font-size', size);
        if (L > 0) t.setAttribute('textLength', L); else t.removeAttribute('textLength');
      }
      plate.setAttribute('opacity', p.plate != null ? p.plate : 1);
      if (rim) rim.setAttribute('opacity', p.rim != null ? p.rim : 1);
    }
    set();
    return { svg, set };
  };
})();
