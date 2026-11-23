/* Quick-cut video engine — deterministic timeline for frame-exact motion graphics.
 *
 * Configure BEFORE this script loads:
 *   <script>window.T3_CONFIG = { fps: 24, start: 0, end: 60 };</script>
 * (For a replica, use the SOURCE video's absolute seconds for start/end so storyboard
 *  timestamps map 1:1.)
 *
 * Segment contract (each segment file calls T3.register({...})):
 *   id     : string
 *   start  : second the layer becomes visible
 *   end    : second it hides (exclusive)
 *   z      : stacking order (higher = on top), default 0
 *   init(layer)   : called once; build DOM/canvas inside `layer` (1920x1080 absolute div)
 *   render(t, lt) : called every displayed frame while visible. t = seconds
 *                   (frame-quantised), lt = t - start. MUST be a pure function of t
 *                   (no accumulated state, no Math.random) so scrubbing, ?t= screenshots
 *                   and frame-by-frame rendering all give identical frames.
 *
 * URL params: ?t=<sec> jump there · &still=1 don't autoplay · &bare=1 hide controls, 1:1 stage
 * Keys: Space play/pause · ←/→ one frame · Shift+←/→ one second
 *
 * T3.ease, T3.tab, T3.ramp, T3.lerp and T3.clamp below are mechanisms: they sample and map a progress. The shape of a
 * move comes from the house curves, T3.EZ (lib/motion/ez.js; what a page loads: references/motion-library.md «Setup»).
 */
(function () {
  const cfg = window.T3_CONFIG || {};
  const FPS = cfg.fps || 24, T0 = cfg.start || 0, T1 = cfg.end != null ? cfg.end : 10;
  const segs = [], holds = [];
  const HOLD_S = cfg.holdTimeout || 10;   // < the ~15 s _cdp.mjs (snap / render_fast) waits for T3_READY
  let stage, t = T0, playing = false, last = 0, pending = 0;
  // optional music: T3_CONFIG.audio = 'assets/music.m4a', audioOffset = second in the file at T0.
  // While playing, the audio clock drives t, so picture and music stay in sync.
  const audio = cfg.audio ? new Audio(cfg.audio) : null;
  const aOff = cfg.audioOffset || 0;
  if (audio) audio.preload = 'auto';

  const T3 = (window.T3 = {
    FPS, T0, T1,
    register(s) { segs.push(Object.assign({ z: 0 }, s)); },
    /** hold segment init() and T3_READY until promise p settles (async fonts: lib/fonts.js url faces). Call before DOMContentLoaded.
     *  Never forever: after T3_CONFIG.holdTimeout s (default 10) it console.errors and boots anyway. */
    hold(p) {
      pending++;
      holds.push(Promise.resolve(p).catch((e) => console.error('T3.hold:', (e && e.message) || e)).finally(() => pending--));
      return p;
    },

    // ---- helpers -------------------------------------------------------
    clamp: (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)),
    lerp: (a, b, k) => a + (b - a) * k,
    /** 0→1 as t goes a→b (clamped) */
    ramp(t, a, b) { return b === a ? (t >= b ? 1 : 0) : T3.clamp((t - a) / (b - a)); },
    /** frame index of a time (same rounding the engine uses) */
    frame: (t) => Math.round(t * FPS),
    /** piecewise table lookup: tab(f, [[f0,v0],[f1,v1],...]) linear between keys, held outside */
    tab(x, keys) {
      if (x <= keys[0][0]) return keys[0][1];
      for (let i = 1; i < keys.length; i++) if (x <= keys[i][0]) { const [a, va] = keys[i - 1], [b, vb] = keys[i]; return va + (vb - va) * ((x - a) / (b - a || 1)); }
      return keys[keys.length - 1][1];
    },
    ease: {
      linear: (k) => k,
      inQuad: (k) => k * k,
      outQuad: (k) => 1 - (1 - k) * (1 - k),
      inOutQuad: (k) => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2),
      outCubic: (k) => 1 - Math.pow(1 - k, 3),
      inCubic: (k) => k * k * k,
      inOutCubic: (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
      outExpo: (k) => (k === 1 ? 1 : 1 - Math.pow(2, -10 * k)),
      inExpo: (k) => (k === 0 ? 0 : Math.pow(2, 10 * k - 10)),
      outBack: (k) => { const c = 1.70158; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
      inOutSine: (k) => -(Math.cos(Math.PI * k) - 1) / 2,
      outSine: (k) => Math.sin(k * Math.PI / 2),
      /** AE-style cubic-bezier(x1,y1,x2,y2) → easing fn. e.g. snap = bezier(.05,.9,.1,1), MAD build = bezier(.6,0,.9,.6) */
      bezier(x1, y1, x2, y2) {
        const bx = (t) => 3 * x1 * t * (1 - t) ** 2 + 3 * x2 * t * t * (1 - t) + t ** 3;
        const by = (t) => 3 * y1 * t * (1 - t) ** 2 + 3 * y2 * t * t * (1 - t) + t ** 3;
        return (k) => { let lo = 0, hi = 1; for (let i = 0; i < 24; i++) { const m = (lo + hi) / 2; if (bx(m) < k) lo = m; else hi = m; } return by((lo + hi) / 2); };
      },
      /** damped spring 0→1 (overshoot + settle). freq ≈ oscillations over k∈[0,1], damp 0..1 */
      spring: (k, freq = 2.2, damp = 0.55) => k <= 0 ? 0 : k >= 1 ? 1 : 1 - Math.exp(-damp * 10 * k) * Math.cos(freq * 2 * Math.PI * k),
      /** n discrete steps (ASCII/pixel/mechanical genres) */
      steps: (n) => (k) => Math.floor(k * n) / n,
    },
    /** deterministic pseudo-random in [0,1) from any numbers */
    rand(...n) {
      let h = 2166136261;
      for (const v of n) { h ^= Math.floor(v * 1000) | 0; h = Math.imul(h, 16777619); h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995); h ^= h >>> 15; }
      return (h >>> 0) / 4294967296;
    },
    /** create element with styles: T3.el('div', {left:'10px'}, parent, 'text') */
    el(tag, style, parent, text) {
      const e = document.createElement(tag);
      if (style) Object.assign(e.style, style);
      if (text != null) e.textContent = text;
      if (parent) parent.appendChild(e);
      return e;
    },
    seek(x) { t = T3.clamp(x, T0, T1); draw(); },
    get time() { return t; },
  });

  function q(x) { return Math.floor(x * FPS + 1e-6) / FPS; }

  // ---- check modes (URL): ?beats=1 → beat light (needs T3_CONFIG.bpm, beatOffset = time of
  // beat 0, optional accents: [sec,…]); ?perf=1 → script time per frame (NOT canvas raster or CSS
  // filters like blur/backdrop-filter — those cost more; judge smoothness by playing). Never shown in renders
  // unless the URL asks, so they're safe to leave in.
  let beatUI = null, perfUI = null; const perf = [];
  function checkUI(p) {
    const box = (r) => T3.el('div', Object.assign({ position: 'absolute', zIndex: 9999, font: '600 22px Consolas, monospace', color: '#fff', textShadow: '0 0 4px #000', pointerEvents: 'none' }, r), stage);
    if (p.has('beats') && cfg.bpm) {
      beatUI = box({ right: '24px', top: '24px', textAlign: 'right' });
      beatUI.innerHTML = '<div id="t3-bl" style="width:46px;height:46px;border-radius:50%;margin-left:auto;background:#333"></div><div id="t3-bn"></div>';
    }
    if (p.has('perf')) perfUI = box({ left: '24px', top: '24px', background: 'rgba(0,0,0,.55)', padding: '6px 10px' });
  }
  function drawChecks(tq, ms) {
    if (beatUI) {
      const per = 60 / cfg.bpm, b = (tq - (cfg.beatOffset || 0)) / per, k = Math.floor(b + 1e-6), ph = b - k;
      const acc = (cfg.accents || []).some((a) => Math.abs(tq - a) < 1.5 / FPS);
      const on = ph * per < 3 / FPS;                                    // lit for 3 frames after each beat
      const bl = document.getElementById('t3-bl');
      bl.style.background = acc ? '#ff3b3b' : on ? (k % 4 === 0 ? '#ffd23f' : '#3fe0ff') : '#333';
      bl.style.transform = acc ? 'scale(1.6)' : 'scale(1)';
      document.getElementById('t3-bn').textContent = `拍 ${k}  ·  ${(k / 4 | 0) + 1}.${(k % 4 + 4) % 4 + 1}`;
    }
    if (perfUI) {
      perf.push(ms); if (perf.length > 96) perf.shift();
      const avg = perf.reduce((a, b) => a + b, 0) / perf.length, mx = Math.max(...perf);
      perfUI.textContent = `render ${ms.toFixed(1)} ms · avg ${avg.toFixed(1)} · max ${mx.toFixed(1)} (budget ${(1000 / FPS).toFixed(1)})`;
      perfUI.style.color = avg > 1000 / FPS ? '#ff6b6b' : '#7dff9a';
    }
  }

  function draw() {
    const tq = q(t), t0 = performance.now();
    for (const s of segs) {
      const on = tq >= s.start && tq < s.end;
      s.layer.style.display = on ? 'block' : 'none';
      if (on) s.render(tq, tq - s.start);
    }
    if (beatUI || perfUI) drawChecks(tq, performance.now() - t0);
    const ui = document.getElementById('t3-time');
    if (ui) {
      ui.textContent = `${fmt(tq)}  (片内 ${fmt(tq - T0)})  帧 ${T3.frame(tq)}`;
      document.getElementById('t3-seek').value = tq;
    }
  }
  function fmt(x) { const m = Math.floor(x / 60), s = x - m * 60; return `${m}:${s.toFixed(2).padStart(5, '0')}`; }

  function loop(now) {
    if (playing) {
      if (audio && !audio.paused) t = T0 + audio.currentTime - aOff;
      else t += (now - last) / 1000;
      if (t >= T1) { t = T1; playing = false; if (audio) audio.pause(); }
      draw();
    }
    last = now;
    requestAnimationFrame(loop);
  }

  function fit() {
    const bare = document.body.classList.contains('bare');
    const ui = bare ? 0 : 56;
    const k = bare ? 1 : Math.min(innerWidth / 1920, (innerHeight - ui) / 1080);
    stage.style.transform = `scale(${k})`;
    stage.parentElement.style.width = 1920 * k + 'px';
    stage.parentElement.style.height = 1080 * k + 'px';
  }

  // segment init() and T3_READY wait for T3.hold() promises (async fonts); with nothing held boot runs right away.
  // A hold that never settles (stalled load) must not leave the page blank: after HOLD_S seconds boot anyway, loudly.
  window.addEventListener('DOMContentLoaded', () => {
    if (!holds.length) return boot();
    let timer;
    const late = new Promise((r) => {
      timer = setTimeout(() => {
        console.error(`T3.hold: ${pending} of ${holds.length} held load(s) still pending after ${HOLD_S} s — starting anyway, frames may show fallback fonts`);
        r();
      }, HOLD_S * 1000);
    });
    Promise.race([Promise.all(holds), late]).then(() => { clearTimeout(timer); boot(); });
  });
  function boot() {
    const p = new URLSearchParams(location.search);
    if (p.has('bare')) document.body.classList.add('bare');
    stage = document.getElementById('stage');
    segs.sort((a, b) => a.z - b.z);
    for (const s of segs) {
      s.layer = T3.el('div', { position: 'absolute', left: 0, top: 0, width: '1920px', height: '1080px', overflow: 'hidden', display: 'none' }, stage);
      s.layer.dataset.seg = s.id;
      s.init(s.layer);
    }
    const seek = document.getElementById('t3-seek');
    seek.min = T0; seek.max = T1; seek.step = 1 / FPS;
    seek.addEventListener('input', () => { playing = false; if (audio) audio.pause(); T3.seek(+seek.value); document.getElementById('t3-play').textContent = '播放'; });
    document.getElementById('t3-play').onclick = toggle;
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); toggle(); }
      if (e.code === 'ArrowRight' || e.code === 'ArrowLeft') {
        playing = false; if (audio) audio.pause(); document.getElementById('t3-play').textContent = '播放';
        T3.seek(q(t) + (e.code === 'ArrowRight' ? 1 : -1) * (e.shiftKey ? 1 : 1 / FPS));
      }
    });
    window.addEventListener('resize', fit);
    fit();
    checkUI(p);
    t = p.has('t') ? +p.get('t') : T0;
    draw();
    requestAnimationFrame((n) => { last = n; loop(n); });
    window.T3_READY = true;
  }

  function toggle() {
    if (t >= T1) t = T0;
    playing = !playing;
    if (audio) {
      if (playing) { audio.currentTime = Math.max(0, t - T0 + aOff); audio.play().catch(() => {}); }
      else audio.pause();
    }
    document.getElementById('t3-play').textContent = playing ? '暂停' : '播放';
  }
})();
