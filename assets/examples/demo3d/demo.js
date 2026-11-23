/* 3D 方案演示（7 s）
 *  A 0–3.5 s  多层摄影机：深海背景 z1500 → 浮游生物粒子层 z650 → 鲸鱼娘 z0 → 前景气泡 z-320（虚化）
 *             镜头推进 + 横移 + 轻微环绕，粒子在不同深度自然产生视差
 *  B 3.5–7 s  深度视差：巨鲸单图 + 深度图，推近 + 横移，焦点从潜艇（远）拉到鲸鱼（近）
 */
(function () {
  const { el, ease, clamp, lerp } = T3;
  const F = (t) => Math.round(t * T3.FPS);
  const SPLIT = 84; // 3.5 s

  // ---------- A: multiplane ----------
  function particleCanvas(n, seed, rMin, rMax, alpha, color) {
    const c = el('canvas', {}); c.width = 1920; c.height = 1080;
    const pts = [];
    for (let i = 0; i < n; i++) pts.push({ x: T3.rand(seed, i, 1) * 1920, y: T3.rand(seed, i, 2) * 1080, r: lerp(rMin, rMax, Math.pow(T3.rand(seed, i, 3), 3)), ph: T3.rand(seed, i, 4) * 6.28, a: alpha * (0.4 + 0.6 * T3.rand(seed, i, 5)) });
    return { c, draw(f) {
      const g = c.getContext('2d'); g.clearRect(0, 0, 1920, 1080);
      for (const p of pts) {
        const y = (p.y - f * (0.6 + p.r * 0.15) + 1080 * 4) % 1080, x = p.x + Math.sin(f * 0.05 + p.ph) * 6;
        const gr = g.createRadialGradient(x, y, 0, x, y, p.r * 2.2);
        gr.addColorStop(0, `rgba(${color},${p.a})`); gr.addColorStop(0.45, `rgba(${color},${p.a * 0.35})`); gr.addColorStop(1, `rgba(${color},0)`);
        g.fillStyle = gr; g.beginPath(); g.arc(x, y, p.r * 2.2, 0, 6.283); g.fill();
      }
    } };
  }
  function bubbleCanvas() {
    const c = el('canvas', {}); c.width = 1920; c.height = 1080;
    const bs = []; for (let i = 0; i < 14; i++) bs.push({ x: T3.rand(9, i, 1) * 1920, y: T3.rand(9, i, 2) * 1300, r: 18 + 70 * T3.rand(9, i, 3), v: 3 + 5 * T3.rand(9, i, 4) });
    return { c, draw(f) {
      const g = c.getContext('2d'); g.clearRect(0, 0, 1920, 1080);
      for (const b of bs) {
        const y = 1250 - ((1300 - b.y + f * b.v) % 1500), x = b.x + Math.sin(f * 0.08 + b.r) * 10;
        g.strokeStyle = 'rgba(190,240,255,0.55)'; g.lineWidth = Math.max(2, b.r * 0.08);
        g.beginPath(); g.arc(x, y, b.r, 0, 6.283); g.stroke();
        const hl = g.createRadialGradient(x - b.r * 0.35, y - b.r * 0.35, 0, x - b.r * 0.35, y - b.r * 0.35, b.r * 0.6);
        hl.addColorStop(0, 'rgba(255,255,255,0.55)'); hl.addColorStop(1, 'rgba(255,255,255,0)');
        g.fillStyle = hl; g.beginPath(); g.arc(x, y, b.r, 0, 6.283); g.fill();
      }
    } };
  }

  let mp, plank, plank2, bub, haze;
  T3.register({
    id: 'mp', start: 0, end: SPLIT / 24, z: 10,
    init(layer) {
      plank = particleCanvas(160, 1, 1.2, 4.5, 0.75, '120,230,255');
      plank2 = particleCanvas(90, 2, 2, 7, 0.55, '150,200,255');
      bub = bubbleCanvas();
      const charImg = el('img', {}); charImg.src = 'assets/img/F_char.png';
      // 角色层整体左移 260px，让她在画面中间偏右
      const charWrap = el('div', {}); charImg.style.cssText = 'position:absolute;left:-200px;top:70px;width:1920px;height:1080px;transform:scale(0.82);transform-origin:60% 45%';
      charWrap.appendChild(charImg);
      mp = T3.multiplane(layer, [
        { src: 'assets/img/F_bg.png', z: 1500, overscan: 1.32 },
        { el: plank2.c, z: 900, overscan: 1.4 },
        { el: plank.c, z: 420, overscan: 1.3 },
        { el: charWrap, z: 0 },
        { el: bub.c, z: -330, blur: 5 },
      ], { perspective: 1100 });
      haze = el('div', { position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 55% 40%, rgba(0,0,0,0) 40%, rgba(2,6,20,0.75) 100%)', pointerEvents: 'none' }, layer);
    },
    render(t) {
      const f = F(t), k = ease.inOutCubic(clamp(f / SPLIT));
      plank.draw(f); plank2.draw(f); bub.draw(f);
      mp.render({ z: lerp(-60, 150, k), x: lerp(-90, 70, k), y: lerp(20, -10, k), rotY: lerp(-6, 4, k), roll: lerp(-0.6, 0.4, k) });
    },
  });

  // ---------- B: depth parallax ----------
  let sc, grain;
  T3.register({
    id: 'depth', start: SPLIT / 24, end: 7, z: 10,
    init(layer) {
      sc = T3.depth3d(layer, { color: 'E', depth: 'E_depth' });
      grain = el('div', { position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 35%, rgba(0,0,0,0) 45%, rgba(1,4,14,0.7) 100%)' }, layer);
    },
    render(t) {
      const f = F(t) - SPLIT, n = 168 - SPLIT, k = ease.inOutQuad(clamp(f / n));
      const rack = ease.inOutCubic(clamp((f - 40) / 8));            // 第 40 帧左右焦点从远处拉到鲸鱼
      sc.render({
        x: lerp(0.013, -0.013, k), y: lerp(0.006, -0.003, k), dolly: lerp(0, 0.08, k), zoom: lerp(1.0, 1.05, k),
        focus: lerp(0.05, 0.85, rack), dof: 2.2, fog: 0.25, fogColor: [0.01, 0.05, 0.14],
      });
    },
  });
})();
