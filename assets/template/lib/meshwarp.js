/* meshwarp.js — bend a separated image layer with a deformable grid, so soft parts (hair,
 * tail, skirt hem, ribbons, a mask strap, a page) really sway instead of a whole-layer skew.
 * No library; works on file:// (drawImage only, no getImageData). Pure function of what you pass.
 *
 *   <script src="lib/meshwarp.js"></script>                       (after engine.js)
 *   const tail = T3.meshwarp(layer, { src: 'assets/img/E_tail.png', cols: 14, rows: 14 });
 *   // in render(t): displacement in px for every grid point (u,v ∈ 0..1 over the image)
 *   tail.render(T3.meshwarp.sway({ t, root: [0.15, 0.2], dir: [0.3, 1], amp: 22, speed: 0.45, lag: 0.9 }));
 *   // or any function: tail.render((u, v) => [dx, dy])
 * T3.meshwarp.sway is a generic sway for soft parts: tails, ribbons, cloth, a strap. Her hair and veil take the approved
 * rooted travelling wave instead, motion-library `her.wave` (T3.her.wave with T3.her.warp2, lib/motion/her2d.js, which
 * draws through this file: load it whenever a page warps her hair or veil).
 *
 * Options: src (image URL) or img (Image/Canvas), x, y, width, height (placement on the 1920×1080
 * layer; default full frame), cols/rows (grid density: 10–16 is plenty), seam (px the triangles
 * overlap to hide hairline seams; default 1.2 — measured vs the unwarped image: 0 px 42 dB,
 * 0.6 px 52.6 dB, 1.2 px 65.4 dB (invisible); on soft alpha edges check for faint doubled lines),
 * canvas (draw into an existing canvas instead).
 * Tips: make the displacement 0 at the attachment point (root) and grow toward the free end, with a
 * phase lag along the length — that is what reads as follow-through. Keep amplitudes small for
 * "lazy" genres (8–25 px at the tip) and larger for wind/hype.
 */
(function () {
  function affine(s0, s1, s2, d0, d1, d2) {
    const sx1 = s1[0] - s0[0], sy1 = s1[1] - s0[1], sx2 = s2[0] - s0[0], sy2 = s2[1] - s0[1];
    const dx1 = d1[0] - d0[0], dy1 = d1[1] - d0[1], dx2 = d2[0] - d0[0], dy2 = d2[1] - d0[1];
    const det = sx1 * sy2 - sx2 * sy1 || 1e-9;
    const a = (dx1 * sy2 - dx2 * sy1) / det, c = (dx2 * sx1 - dx1 * sx2) / det;
    const b = (dy1 * sy2 - dy2 * sy1) / det, d = (dy2 * sx1 - dy1 * sx2) / det;
    return [a, b, c, d, d0[0] - a * s0[0] - c * s0[1], d0[1] - b * s0[0] - d * s0[1]];
  }
  function grow(p, cx, cy, by) { const vx = p[0] - cx, vy = p[1] - cy, l = Math.hypot(vx, vy) || 1; return [p[0] + vx / l * by, p[1] + vy / l * by]; }

  T3.meshwarp = function (layer, o) {
    o = Object.assign({ x: 0, y: 0, width: 1920, height: 1080, cols: 12, rows: 12, seam: 1.2 }, o || {});
    const cv = o.canvas || T3.el('canvas', { position: 'absolute', left: o.x + 'px', top: o.y + 'px', width: o.width + 'px', height: o.height + 'px' }, layer);
    if (!o.canvas) { cv.width = o.width; cv.height = o.height; }
    const ctx = cv.getContext('2d');
    let img = o.img || null, last = null, asked = false;   // `asked`: render() was called before the image loaded
    if (!img) { img = new Image(); img.onload = () => { if (asked) draw(last); }; img.src = o.src; }
    const ready = () => img && (img.naturalWidth || img.width) > 0;

    function draw(fn) {
      last = fn; asked = true;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, cv.width, cv.height);
      if (!ready()) return;
      const iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;   // image fills the canvas box
      const C = o.cols, R = o.rows, P = [];
      for (let j = 0; j <= R; j++) for (let i = 0; i <= C; i++) {
        const u = i / C, v = j / R, dd = fn ? fn(u, v) : [0, 0];
        P.push({ s: [u * iw, v * ih], d: [u * cv.width + dd[0], v * cv.height + dd[1]] });
      }
      const at = (i, j) => P[j * (C + 1) + i];
      const tri = (A, B, Cc) => {
        const m = affine(A.s, B.s, Cc.s, A.d, B.d, Cc.d);
        const cx = (A.d[0] + B.d[0] + Cc.d[0]) / 3, cy = (A.d[1] + B.d[1] + Cc.d[1]) / 3;
        const a = grow(A.d, cx, cy, o.seam), b = grow(B.d, cx, cy, o.seam), c = grow(Cc.d, cx, cy, o.seam);
        ctx.save();
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.lineTo(c[0], c[1]); ctx.closePath(); ctx.clip();
        ctx.setTransform(m[0], m[1], m[2], m[3], m[4], m[5]);
        // draw only the source triangle's bounding box (+2 px) — far cheaper than the whole image
        const x0 = Math.max(0, Math.min(A.s[0], B.s[0], Cc.s[0]) - 2), y0 = Math.max(0, Math.min(A.s[1], B.s[1], Cc.s[1]) - 2);
        const x1 = Math.min(iw, Math.max(A.s[0], B.s[0], Cc.s[0]) + 2), y1 = Math.min(ih, Math.max(A.s[1], B.s[1], Cc.s[1]) + 2);
        if (x1 > x0 && y1 > y0) ctx.drawImage(img, x0, y0, x1 - x0, y1 - y0, x0, y0, x1 - x0, y1 - y0);
        ctx.restore();
      };
      for (let j = 0; j < R; j++) for (let i = 0; i < C; i++) {
        const p00 = at(i, j), p10 = at(i + 1, j), p01 = at(i, j + 1), p11 = at(i + 1, j + 1);
        tri(p00, p10, p11); tri(p00, p11, p01);
      }
    }
    return { canvas: cv, get ready() { return ready(); }, render: draw };
  };

  /** Rooted sway: 0 at `root`, growing toward the free end, with a travelling phase (follow-through).
   *  t: seconds · root: [u,v] attachment point · dir: displacement direction · amp: px at distance 1
   *  speed: cycles per second · lag: phase delay per unit distance (cycles) · power: stiffness curve
   *  weight(u,v) → 0..1 optional mask (e.g. only the hair ends of a full-body layer) */
  T3.meshwarp.sway = function ({ t = 0, root = [0.5, 0], dir = [1, 0], amp = 16, speed = 0.5, lag = 0.8, power = 1.6, weight = null }) {
    const l = Math.hypot(dir[0], dir[1]) || 1, ux = dir[0] / l, uy = dir[1] / l;
    return (u, v) => {
      const d = Math.min(1.5, Math.hypot(u - root[0], v - root[1]));
      const w = (weight ? weight(u, v) : 1) * Math.pow(d, power);
      const s = Math.sin((t * speed - d * lag) * 2 * Math.PI) * amp * w;
      return [s * ux, s * uy];
    };
  };
})();
