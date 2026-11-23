(function () {
  let tail, grid, girl;
  T3.register({
    id: 'test', start: 0, end: 4, z: 0,
    init(layer) {
      const bg = T3.el('img', { position: 'absolute', inset: 0, width: '1920px', height: '1080px', objectFit: 'cover' }, layer); bg.src = 'assets/B.jpg';
      // frosted glass panel over the full-bleed art
      T3.el('div', { position: 'absolute', left: '40px', top: '40px', width: '600px', height: '1000px', borderRadius: '6px',
        backdropFilter: 'blur(26px) saturate(0.8) brightness(0.75)', webkitBackdropFilter: 'blur(26px) saturate(0.8) brightness(0.75)',
        background: 'rgba(10,16,34,0.35)', border: '1px solid rgba(255,255,255,0.10)' }, layer, '');
      grid = T3.meshwarp(layer, { src: 'assets/grid.png', x: 700, y: 40, width: 360, height: 480, cols: 12, rows: 16 });
      tail = T3.meshwarp(layer, { src: 'assets/E.jpg', x: 700, y: 560, width: 640, height: 360, cols: 16, rows: 9 });
      girl = T3.meshwarp(layer, { src: 'assets/J.png', x: 1100, y: 0, width: 1920 * 0.42, height: 1080 * 0.42 * 1.0 * 2.3 / 2.3, cols: 14, rows: 14 });
    },
    render(t) {
      grid.render(T3.meshwarp.sway({ t, root: [0.5, 0], dir: [1, 0], amp: 60, speed: 0.5, lag: 0.9 }));
      tail.render(T3.meshwarp.sway({ t, root: [0.0, 0.5], dir: [0.2, 1], amp: 26, speed: 0.4, lag: 0.8 }));
      // only the hair ends / tail of the full-body cutout move (weight ramps in below 45% height)
      girl.render(T3.meshwarp.sway({ t, root: [0.5, 0.2], dir: [1, 0.1], amp: 30, speed: 0.45, lag: 1.0, weight: (u, v) => Math.max(0, Math.min(1, (v - 0.35) / 0.35)) }));
    },
  });
})();
