// WARNING: never set opacity / filter / mask on mp.world or any preserve-3d node — it flattens the 3D; fade or filter the planes (mp.items[i].e) or mp.view.
/* multiplane.js — "multiplane camera": separate layers (background / mid / character / foreground)
 * placed at different depths in real CSS 3D, then the camera trucks, dollies, orbits through them.
 * Use when you have the scene as separate transparent PNG layers (ask GPT for each layer
 * separately, or cut the character out) — occlusion is perfect, unlike a single depth map.
 *
 *   const mp = T3.multiplane(layer, [
 *     { src: 'assets/img/bg.jpg',   z: 2000 },   // z = distance behind the screen plane (px)
 *     { src: 'assets/img/mid.png',  z: 800  },
 *     { src: 'assets/img/girl.png', z: 0    },   // z 0 = exactly frame-size at rest
 *     { src: 'assets/img/fg.png',   z: -300, blur: 6 },  // negative = in front (bigger, blurred)
 *   ], { perspective: 1200 });
 *   mp.render({ x, y, z, rotY, rotX, roll });     // camera: px slide, px push (+ = forward), degrees
 * Each plane is pre-scaled so that at rest (camera 0) it fills the frame exactly as drawn; the
 * parallax then comes for free from the perspective. Plain <img>/DOM → works on file:// too.
 * Planes may also be any element: { el: someDiv, z } (e.g. code-drawn particles at a depth).
 */
(function () {
  T3.multiplane = function (layer, planes, opt) {
    opt = opt || {};
    const P = opt.perspective || 1200, W = 1920, H = 1080;
    const view = T3.el('div', { position: 'absolute', left: 0, top: 0, width: W + 'px', height: H + 'px', perspective: P + 'px', perspectiveOrigin: '50% 50%', overflow: 'hidden' }, layer);
    const world = T3.el('div', { position: 'absolute', left: 0, top: 0, width: W + 'px', height: H + 'px', transformStyle: 'preserve-3d' }, view);
    const items = planes.map((p) => {
      const e = p.el || T3.el('img', { objectFit: 'cover' }, null);
      if (!p.el) e.src = p.src;
      Object.assign(e.style, { position: 'absolute', left: 0, top: 0, width: W + 'px', height: H + 'px', transformOrigin: '50% 50%', backfaceVisibility: 'hidden' });
      if (p.blur) e.style.filter = `blur(${p.blur}px)`;
      const k = (P + p.z) / P * (p.overscan || 1.1);   // overscan so edges never show during moves
      e.style.transform = `translateZ(${-p.z}px) scale(${k})`;
      world.appendChild(e);
      return { e, p };
    });
    return {
      view, world, items,
      render(c) {
        c = c || {};
        world.style.transform = `translateZ(${c.z || 0}px) rotateX(${c.rotX || 0}deg) rotateY(${c.rotY || 0}deg) rotateZ(${c.roll || 0}deg) translate3d(${-(c.x || 0)}px, ${-(c.y || 0)}px, 0)`;
      },
    };
  };
})();
