/* emblem3d.js — a layered 3D emblem in CSS 3D: 3–5 flat planes at different heights. It grows flat from a point,
 * stands up on the beat in 4–5 frames, then sways slowly so the heights read. Load after engine.js.
 *
 *   const em = T3.emblem3d(layer, { x: 960, y: 540, size: 1000, perspective: 1500, planes: [      // in init()
 *     { z: -70, svg: '<circle cx="500" cy="500" r="430" fill="none" stroke="#fff" stroke-dasharray="3 12"/>' },
 *     { z: 0,   src: 'assets/img/mark.png' },                    // square, same framing; or { z, el: someCanvas }
 *     { z: 30,  svg: '<circle cx="500" cy="500" r="56" fill="#FFD38A"/>' },
 *   ] });   // svg is drawn in a size × size box (opts.viewBox to change); opts.W / H if the container isn't 1920 × 1080
 *   em.render(T3.standUp(f, 600, { beat: 606 }));                 // in render(t), f = Math.round(t * T3.FPS)
 *
 * T3.standUp(f, f0, { beat: f0 + 6, up: 5, sway: 1, period: 3 }) → { s, tilt, lift, yaw, pitch }
 *   grows from a point (f0 + 1 → beat) lying back 70 → 78°, stands up over `up` frames, upright exactly on `beat`;
 *   lift rises from below, overshoots a little, settles on the beat; yaw / pitch: slow sway ±9° / ±5° every
 *   `period` seconds (sway: 0 = off).
 * em.render(pose): pose = { s, tilt (deg), lift (× size, + = down), yaw, pitch, roll (deg), x, y (px offset),
 *   opacity (whole emblem), fade: [opacity per plane] }; keys left out = rest, so every call sets the full state.
 * Fade only through pose.opacity / pose.fade: opacity, filter or mask on em.world or em.emb (preserve-3d) flattens the 3D.
 * Plane recipe (z in px): thin ring −70 · dots −30 · main mark 0 · core +30 · tick ring +60.
 */
(function () {
  const E = T3.ease, ramp = T3.ramp, lerp = T3.lerp;

  T3.standUp = function (f, f0, o) {
    o = o || {};
    const beat = o.beat == null ? f0 + 6 : o.beat, up = o.up == null ? 5 : o.up, n = Math.max(1, beat - f0);
    const s = f < f0 ? 0 : 0.02 + 0.98 * E.outExpo(ramp(f, f0 + 1, beat));
    const tilt = f < beat - up
      ? lerp(70, 78, E.outQuad(ramp(f, f0, f0 + Math.min(5, n - up))))                    // lies back further as it grows
      : 78 * (1 - E.inOutCubic(ramp(f, beat - up, beat)));                                 // stands up, upright on the beat
    const lift = T3.tab((f - f0) / n, [[0, 0.06], [0.46, 0.02], [0.77, -0.025], [1, 0]]);
    const w = o.sway == null ? 1 : o.sway, a = (2 * Math.PI * (f - f0)) / T3.FPS / (o.period || 3);
    return { s, tilt, lift, yaw: w * 9 * Math.sin(a), pitch: w * 5 * Math.sin(a + 1.2) };
  };

  T3.emblem3d = function (layer, o) {
    o = Object.assign({ x: 960, y: 540, size: 1000, perspective: 1500, planes: [], W: 1920, H: 1080 }, o || {});
    const S = o.size, vb = o.viewBox || `0 0 ${S} ${S}`;
    const box = (parent, st) => T3.el('div', Object.assign({ position: 'absolute', left: '0px', top: '0px', width: o.W + 'px', height: o.H + 'px' }, st), parent);
    const view = box(layer, { perspective: o.perspective + 'px', perspectiveOrigin: '50% 50%' });
    const world = box(view, { transformStyle: 'preserve-3d', transformOrigin: `${o.x}px ${o.y}px` });          // sway pivots on the emblem
    const emb = T3.el('div', { position: 'absolute', left: o.x - S / 2 + 'px', top: o.y - S / 2 + 'px', width: S + 'px', height: S + 'px', transformStyle: 'preserve-3d' }, world);
    const planes = o.planes.map((p) => {
      const d = T3.el('div', { position: 'absolute', left: '0px', top: '0px', width: S + 'px', height: S + 'px', transform: `translateZ(${p.z || 0}px)` }, emb);
      if (p.svg) d.innerHTML = `<svg width="${S}" height="${S}" viewBox="${vb}" style="position:absolute;left:0;top:0;overflow:visible">${p.svg}</svg>`;
      else if (p.src) T3.el('img', { position: 'absolute', left: '0px', top: '0px', width: S + 'px', height: S + 'px' }, d).src = p.src;
      else if (p.el) d.appendChild(p.el);
      return d;
    });
    const n3 = (v, d) => (v == null ? d : +v).toFixed(3);
    return {
      view, world, emb, planes,
      render(p) {
        p = p || {};
        const s = n3(p.s, 1);
        world.style.transform = `translate3d(${n3(p.x, 0)}px, ${n3(p.y, 0)}px, 0) rotateX(${n3(p.pitch, 0)}deg) rotateY(${n3(p.yaw, 0)}deg)`;
        emb.style.transform = `translateY(${n3((p.lift || 0) * S, 0)}px) rotateX(${n3(p.tilt, 0)}deg) rotateZ(${n3(p.roll, 0)}deg) scale3d(${s}, ${s}, ${s})`;
        view.style.opacity = n3(p.opacity, 1);                                              // the outer view: safe to fade
        planes.forEach((d, i) => { d.style.opacity = n3(p.fade && p.fade[i], 1); });        // planes are flat leaves: safe
      },
    };
  };
})();
