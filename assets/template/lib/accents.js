/* accents.js — "polygon accents" for fast cuts (graphic-design §5, layer 4): meaningless bright shapes that
 * add energy on strobe runs — the reference throws 4–6 thin outlined bars at random diagonals over a
 * brand-tinted frame. Deterministic: the same frame always draws the same shapes (T3.rand), so scrubbing,
 * snap.mjs and render_fast.mjs agree.
 *
 *   <script src="lib/accents.js"></script>                         (after engine.js)
 *   const acc = T3.accents(layer, { family: 'bars', seed: 7, color: '#FFE2B8', glow: '#F2A14A' });
 *   render(t, lt) { const f = Math.round(t * T3.FPS); acc.render(f, { on: f >= 457 && f < 503, wash: 0.35 }); }
 *
 * Families (design your own per character — the reference's bars are grammar, not a template):
 *   'bars'    long thin rectangles at ±30–60°, light outline + faint fill (the reference's look)
 *   'shards'  slivers radiating from a point off-centre — e.g. fragments of a 12-ray emblem
 *   'frames'  hollow parallelograms / hexagon outlines, a few large, a few small
 *   'mix'     some of each
 * Options: seed, family, count (4–6), hold (frames a set stays before re-rolling, 1–2), color (outline),
 *   glow (shadow colour), fill (fill alpha 0–1, default .18), line (px, default 3.5), washColor (frame tint).
 * render(frame, { on, wash, opacity, family }) — wash = 0–1 opacity of a flat tint drawn first under the shapes.
 * Like flash frames, accents live only 1–3 frames at a time (a subliminal hit, not a graphic): switch `on` for a
 * few frames on a beat, not for whole shots.
 *
 * Impact frames (冲击帧) — 1–2 frames where the current shot turns into a stark two-tone image on a big hit:
 *   T3.impact(el, kind)   kind = 'ink' (hard black-and-white), 'neg' (the same, inverted), 'tint' (amber duotone), null = off
 *   e.g. in render: T3.impact(shotDiv, f === 549 ? 'neg' : f === 550 ? 'ink' : null)
 * Sparingly, only on the strongest hits: overuse kills the impact (how many per intro: house-style §6, the effects budget).
 */
(function () {
  const IMPACT = {
    ink: 'grayscale(1) contrast(9) brightness(1.35)',            // hard black-and-white
    neg: 'grayscale(1) contrast(9) brightness(1.35) invert(1)',  // the same, inverted
    tint: 'grayscale(1) contrast(7) brightness(1.2) sepia(1) saturate(3) hue-rotate(-12deg)'  // amber duotone
  };
  T3.impact = function (el, kind) { el.style.filter = kind ? (IMPACT[kind] || kind) : ''; };
  T3.accents = function (layer, o) {
    o = Object.assign({ seed: 1, family: 'bars', count: 5, hold: 2, color: '#FFFFFF', glow: '#FFFFFF', fill: 0.18,
      line: 3.5, washColor: '#F2A14A', W: 1920, H: 1080 }, o || {});
    const cv = T3.el('canvas', { position: 'absolute', left: 0, top: 0, width: o.W + 'px', height: o.H + 'px', pointerEvents: 'none' }, layer);
    cv.width = o.W; cv.height = o.H;
    const ctx = cv.getContext('2d');
    const R = (k, i, j) => T3.rand(o.seed, k, i, j);           // 0..1, deterministic

    function poly(pts) { ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); }
    function stroke(alpha) {
      ctx.save(); ctx.globalAlpha = alpha * o.fill; ctx.fillStyle = o.color; ctx.fill(); ctx.restore();
      ctx.save(); ctx.globalAlpha = alpha; ctx.lineWidth = o.line; ctx.strokeStyle = o.color;
      ctx.shadowColor = o.glow; ctx.shadowBlur = 14; ctx.lineJoin = 'miter'; ctx.stroke(); ctx.restore();
    }
    function bar(k, i, a) {                                       // long thin rotated rectangle
      const cx = o.W * (0.1 + 0.8 * R(k, i, 1)), cy = o.H * (0.1 + 0.8 * R(k, i, 2));
      const len = 520 + 900 * R(k, i, 3), wid = 34 + 60 * R(k, i, 4);
      const ang = (R(k, i, 5) < 0.5 ? -1 : 1) * (30 + 30 * R(k, i, 6)) * Math.PI / 180;
      const ux = Math.cos(ang), uy = Math.sin(ang), vx = -uy, vy = ux, hl = len / 2, hw = wid / 2;
      poly([[cx - ux * hl - vx * hw, cy - uy * hl - vy * hw], [cx + ux * hl - vx * hw, cy + uy * hl - vy * hw],
            [cx + ux * hl + vx * hw, cy + uy * hl + vy * hw], [cx - ux * hl + vx * hw, cy - uy * hl + vy * hw]]);
      stroke(a);
    }
    function shard(k, i, a, cx, cy) {                             // sliver pointing away from (cx, cy)
      const ang = (i / o.count + 0.13 * R(k, i, 7)) * Math.PI * 2, r0 = 120 + 260 * R(k, i, 8), r1 = r0 + 380 + 520 * R(k, i, 9);
      const w = 0.035 + 0.05 * R(k, i, 10);
      poly([[cx + Math.cos(ang - w) * r0, cy + Math.sin(ang - w) * r0], [cx + Math.cos(ang) * r1, cy + Math.sin(ang) * r1],
            [cx + Math.cos(ang + w) * r0, cy + Math.sin(ang + w) * r0]]);
      stroke(a);
    }
    function frame(k, i, a) {                                     // hollow parallelogram or hexagon
      const cx = o.W * (0.15 + 0.7 * R(k, i, 11)), cy = o.H * (0.15 + 0.7 * R(k, i, 12)), s = 90 + 330 * R(k, i, 13);
      const rot = R(k, i, 14) * Math.PI;
      const n = R(k, i, 15) < 0.5 ? 4 : 6, sk = n === 4 ? 0.45 : 0;
      const pts = [];
      for (let q = 0; q < n; q++) {
        const th = rot + q * 2 * Math.PI / n, rx = s * (n === 4 ? 1.6 : 1), ry = s;
        let x = Math.cos(th) * rx, y = Math.sin(th) * ry; x += y * sk;
        pts.push([cx + x, cy + y]);
      }
      poly(pts); ctx.save(); const f0 = o.fill; o.fill = 0.06; stroke(a); o.fill = f0; ctx.restore();
    }

    return {
      canvas: cv,
      render(f, r) {
        r = r || {};
        ctx.clearRect(0, 0, o.W, o.H);
        if (!r.on) { cv.style.display = 'none'; return; }
        cv.style.display = 'block';
        cv.style.opacity = r.opacity == null ? 1 : r.opacity;
        if (r.wash) { ctx.save(); ctx.globalAlpha = r.wash; ctx.fillStyle = o.washColor; ctx.fillRect(0, 0, o.W, o.H); ctx.restore(); }
        const k = Math.floor(f / Math.max(1, o.hold));              // which set of shapes
        const fam = r.family || o.family;
        const cx = o.W * (0.3 + 0.4 * R(k, 0, 20)), cy = o.H * (0.3 + 0.4 * R(k, 0, 21));
        for (let i = 0; i < o.count; i++) {
          const a = 0.55 + 0.45 * R(k, i, 30);
          const which = fam === 'mix' ? ['bars', 'shards', 'frames'][Math.floor(R(k, i, 31) * 3)] : fam;
          if (which === 'bars') bar(k, i, a);
          else if (which === 'shards') shard(k, i, a, cx, cy);
          else frame(k, i, a);
        }
      }
    };
  };
})();
