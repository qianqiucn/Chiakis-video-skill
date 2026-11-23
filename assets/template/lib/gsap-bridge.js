/* gsap-bridge.js — use GSAP (the animation library the reference video was built with) inside the
 * deterministic engine. Load order:
 *   <script src="engine.js"></script>
 *   <script src="lib/gsap/gsap.min.js"></script>  (+ any plugins: CustomEase, SplitText, DrawSVGPlugin,
 *   MorphSVGPlugin, MotionPathPlugin, CustomWiggle, CustomBounce, TextPlugin, Physics2DPlugin)
 *   <script src="lib/gsap-bridge.js"></script>
 *   <script src="segments/....js"></script>
 *
 * In a segment:
 *   let tl;
 *   init(layer) { const box = T3.el('div', {...}, layer);
 *                 tl = T3.gsapTimeline().to(box, { x: 600, duration: 0.8, ease: 'expo.out' })
 *                                       .from(chars, { y: 80, opacity: 0, stagger: 0.03 }, 0.2); }
 *   render(t, lt) { T3.gsapSeek(tl, lt); }          // lt = seconds since the segment started
 *
 * Why this is deterministic (each point fixed a failure in the 2026-11-05 test, where frames rendered
 * forwards vs backwards first differed in 14 of 16 frames):
 *  - the global timeline is paused and every bridge timeline is created paused → nothing advances alone;
 *  - `lazy: false` for all tweens → a tween's first render is written immediately (GSAP otherwise defers
 *    it to the next tick, and with the ticker idle the first seeked frame showed the un-animated state);
 *  - on its first seek every timeline is run once to the end and back → all tweens initialise in
 *    timeline order, whatever frame is asked for first;
 *  - Math.random is replaced by a fixed-seed generator → "random(200,600)" values, gsap.utils.random
 *    and stray Math.random calls come out the same on every page load.
 * Still prefer explicit values: function-based props with T3.rand, e.g. x: (i) => 200 + 400 * T3.rand(i, 3).
 * ScrambleTextPlugin is not vendored.
 * Ease names: the named house curves are lib/motion/ez.js (T3.EZ, loaded after this file; which genre takes which:
 * style-grammar §6b). A timeline takes the same GSAP strings, e.g. 'expo.out', 'back.out(1.7)', 'elastic.out(1,0.45)',
 * 'steps(8)' (ASCII/mechanical), or a path through T3.EZ.get('M0,0 C0.05,0.9 0.1,1 1,1').
 */
(function () {
  if (!window.gsap) { console.error('gsap-bridge: load lib/gsap/gsap.min.js first'); return; }
  // fixed-seed Math.random (mulberry32): page init order is fixed, so every load draws the same numbers
  let seed = 0x2f6b9e13;
  Math.random = function () {
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  gsap.globalTimeline.pause();
  gsap.ticker.lagSmoothing(0);
  gsap.defaults({ lazy: false });
  const names = ['CustomEase', 'CustomWiggle', 'CustomBounce', 'SplitText', 'DrawSVGPlugin', 'MorphSVGPlugin',
    'MotionPathPlugin', 'TextPlugin', 'Physics2DPlugin'];
  const plugins = names.map((n) => window[n]).filter(Boolean);
  if (plugins.length) gsap.registerPlugin(...plugins);
  T3.gsapTimeline = (vars) => gsap.timeline(Object.assign({ paused: true }, vars || {}));
  T3.gsapSeek = (tl, sec) => {
    if (!tl.__t3init) { tl.progress(1, true).progress(0, true); tl.__t3init = true; }  // init all tweens in order
    tl.seek(Math.max(0, sec), false);
  };
})();
