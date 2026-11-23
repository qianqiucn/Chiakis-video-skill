/* sequence.js — play an image sequence frame-exactly: stock-footage overlays (ink in water, dust,
 * light leaks, bokeh — bundled assets/textures/ or your project footage) or any frames.
 * Frames are preloaded as <img> elements (so render_fast/snap wait for them) and drawn onto a canvas,
 * so showing frame k is synchronous and identical every time (no async decode flicker).
 *
 *   <script src="lib/sequence.js"></script>                       (after engine.js)
 *   const ink = T3.sequence(layer, { dir: 'assets/fx/ink', count: 60, blend: 'screen', opacity: 0.9 });
 *   render(t, lt) { ink.render(Math.floor(lt * T3.FPS)); }          // local frame index from 0
 *
 * Options: dir, count, ext ('jpg'), pad (3 → f001), blend (CSS mix-blend-mode: screen | lighten |
 * multiply | overlay | normal), opacity, loop ('none' | 'loop' | 'pingpong'), filter (CSS filter,
 * e.g. 'saturate(.7) hue-rotate(-10deg)' to keep it in the piece's grade), x/y/width/height.
 * render(k, opts) also accepts { opacity, transform } per frame (e.g. scale the plume as it grows).
 * frac: true → render(x) with a fractional x blends frames floor(x) and floor(x) + 1 (retimed image sequences
 * that must never park or stutter).
 * mask: 'assets/rel/C10_mask' → keep only what the frame-aligned grey mask sequence shows white (same count and
 * names; maskExt defaults to ext): her, cut out of her own shot frame by frame. Type behind her = the shot, then the
 * type, then the same shot again with `mask` and blend 'normal', rendered with the same frame index and the same
 * transform as the shot underneath (references/graphic-design.md §2).
 */
(function () {
  function lumToAlpha() {                                // one SVG filter per page: alpha = the mask's brightness
    if (document.getElementById('t3-l2a')) return;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '0'); svg.setAttribute('height', '0'); svg.style.position = 'absolute';
    svg.innerHTML = '<filter id="t3-l2a" color-interpolation-filters="sRGB"><feColorMatrix type="luminanceToAlpha"/></filter>';
    document.body.appendChild(svg);
  }
  T3.sequence = function (layer, o) {
    o = Object.assign({ ext: 'jpg', pad: 3, blend: 'screen', opacity: 1, loop: 'none', filter: '', x: 0, y: 0, width: 1920, height: 1080 }, o || {});
    const cv = T3.el('canvas', { position: 'absolute', left: o.x + 'px', top: o.y + 'px', width: o.width + 'px', height: o.height + 'px',
      mixBlendMode: o.blend, opacity: o.opacity, filter: o.filter || 'none', pointerEvents: 'none' }, layer);
    cv.width = o.width; cv.height = o.height;
    const ctx = cv.getContext('2d');
    const hold = T3.el('div', { display: 'none' }, layer);
    const frames = [], masks = [];
    const load = (dir, ext, arr) => {
      for (let i = 1; i <= o.count; i++) {
        const im = document.createElement('img');
        im.src = `${dir}/f${String(i).padStart(o.pad, '0')}.${ext}`;
        hold.appendChild(im); arr.push(im);
      }
    };
    load(o.dir, o.ext, frames);
    if (o.mask) { lumToAlpha(); load(o.mask, o.maskExt || o.ext, masks); }
    let last = -1, mc = null;
    function index(k) {
      const n = o.count;
      if (o.loop === 'loop') return ((k % n) + n) % n;
      if (o.loop === 'pingpong') { const p = 2 * (n - 1) || 1; const m = ((k % p) + p) % p; return m < n ? m : p - m; }
      return Math.max(0, Math.min(n - 1, k));
    }
    const ok = (im) => im.complete && im.naturalWidth > 0;
    const need = (ia, ib) => (o.mask ? [frames[ia], frames[ib], masks[ia], masks[ib]] : [frames[ia], frames[ib]]);
    function cut(ia, ib, fr) {                            // keep only where the mask is white, blended like the frames
      if (!o.mask) return;
      let src = masks[ia];
      if (fr > 0) {
        if (!mc) { mc = document.createElement('canvas'); mc.width = cv.width; mc.height = cv.height; }
        const m = mc.getContext('2d');
        m.globalAlpha = 1; m.drawImage(masks[ia], 0, 0, mc.width, mc.height);
        m.globalAlpha = fr; m.drawImage(masks[ib], 0, 0, mc.width, mc.height); m.globalAlpha = 1;
        src = mc;
      }
      ctx.save(); ctx.globalCompositeOperation = 'destination-in'; ctx.filter = 'url(#t3-l2a)';
      ctx.drawImage(src, 0, 0, cv.width, cv.height); ctx.restore();
    }
    function draw(ia, ib, fr, key) {
      ctx.clearRect(0, 0, cv.width, cv.height); last = -1;
      const all = need(ia, ib);
      if (!all.every(ok)) { all.forEach((im) => { if (!ok(im)) im.addEventListener('load', () => { if (last === -1 && all.every(ok)) draw(ia, ib, fr, key); }, { once: true }); }); return; }
      ctx.globalAlpha = 1; ctx.drawImage(frames[ia], 0, 0, cv.width, cv.height);
      if (fr > 0) { ctx.globalAlpha = fr; ctx.drawImage(frames[ib], 0, 0, cv.width, cv.height); ctx.globalAlpha = 1; }
      cut(ia, ib, fr);
      last = key;
    }
    return {
      canvas: cv,
      render(k, opts) {
        if (opts && opts.opacity != null) cv.style.opacity = opts.opacity;
        if (opts && opts.transform != null) cv.style.transform = opts.transform;
        if (o.frac && k % 1) {                            // frac: frame floor(x), then the next one at alpha = x mod 1
          const k0 = Math.floor(k), fr = Math.round((k - k0) * 100) / 100, ia = index(k0), ib = index(k0 + 1), key = ia + ':' + fr;
          if (key === last && need(ia, ib).every(ok)) return;
          return draw(ia, ib, fr, key);
        }
        const i = index(k);
        if (i === last && need(i, i).every(ok)) return;
        draw(i, i, 0, i);
      },
    };
  };
})();
