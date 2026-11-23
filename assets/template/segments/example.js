// motion-sheet: inline
// motion: move.arrive, move.leave, move.settle, move.stagger, move.drift, trans.flash
/* motion sheet · example (editor/compositor) · curve family: style-grammar §6b, hype row · beat: none (a sample: three shots of 40 f, cuts at 40 and 80)
| moment | element | frames (start / length) | id | ease | stagger / settle | departure and reason |
|---|---|---|---|---|---|---|
| title in | word, rule, tag | 3 / 12 | move.arrive | T3.EZ.snap | parts at 3, 5, 6 (2 f, then 1 f apart); move.settle 3 px/s and 0.5 % | — |
| title out | word, rule, tag | 32 / 8 | move.leave | T3.EZ.expoIn | parts 1 f apart; the cut at 40 falls in the word's fastest frame | — |
| deal | 5 cards | 38 / 12 each | move.arrive, move.stagger | T3.EZ.snap | dealt, gaps 8 → 3 f; move.settle 0.5 % scale | the first card starts 2 f before the cut, so shot B opens moving |
| flash | white layer | 74 / 6 | trans.flash | T3.EZ.p3in | flat white for the last 2 f, hard cut at 80 | — |
| after the flash | shot C | 80 / 3 | trans.flash | T3.EZ power2.out | dark and defocused, clear by 83 | — |
| end card | label, line | 79 / 12 | move.arrive | T3.EZ.snap | parts 1 f apart; move.settle 3 px/s and 0.5 % | starts 1 f before the cut, under the flash |
| air | sheen bands and light pool, one layer per shot | −20, 20, 60 / 80 | move.drift | T3.EZ.sine | never lands: 72 px across its bands, ≥ 1 px/f on screen | the one symmetric curve here, a background's: it runs 20 f past both ends of its shot, so it is never at rest on screen or on a cut |
Probes: example.title.in, example.cards.in, example.end.in (arrivals), example.title.out (exit), example.flash (transition), example.air (ambient)
*/
/* example.js: the house sample segment, 5 s in three shots of 40 f with hard cuts. Copy its habits, not its look.
 *  - Every pose is a pure function of the frame built from lib/motion: T3.mv moves on named T3.EZ curves. No
 *    hand-written ease, no T3.tab keys, no per-frame value table (motion-library «How to use»).
 *  - Arrivals are front-loaded and their parts land a frame or two apart; nothing stops dead after landing (it
 *    settles); a batch staggers on a shrinking interval; exits speed up into the cut; the next shot opens already
 *    moving (style-grammar §6b).
 *  - Every shot keeps one layer that never stops: here each background drifts on T3.EZ.sine (move.drift) over its
 *    shot and 20 f either side. A settle alone (1–3 px/s) is too small for qa's frozen-frame check (half a second with
 *    almost no change on the half-size draft), and a held end card with nothing else moving reads as parked art.
 *  - render() and the six T3.motionProbe calls share the pose functions, so the curve sheet plots what is drawn.
 *    Both checks go through the queue: the lint draws the curve sheet, qa adds the draft (frozen frames, cuts) and the lint:
 *    python -X utf8 <skill>/scripts/run_queue.py web --lane <who> -- node <skill>/scripts/motion_lint.mjs web/index.html --curves
 *    python -X utf8 <skill>/scripts/run_queue.py web --lane <who> -- node <skill>/scripts/qa.mjs web/index.html --to 5
 * Replace or delete it once real segments exist.
 */
(function () {
  const { el } = T3;
  const CUT1 = 40, CUT2 = 80, END = 120;         // shot A f0–39, shot B f40–79, shot C f80–119 (segment frames)
  const SHOTS = [[0, CUT1], [CUT1, CUT2], [CUT2, END]];
  const BG = ['#1b1f3b', '#3b1b2a', '#10141c'];

  // ---- poses: frame → { x, y, s, r, o }; render() and the probes call these same functions
  const titleAt = (i) => 3 + T3.mv.stagger(i, 3, { from: 2, to: 1 });                         // word, rule, tag: 2 f, then 1 f apart
  const TITLE_FROM = [{ x: -140, s: 1.4, o: 0 }, { x: -520, o: 0 }, { y: 36, o: 0 }];
  const title = (i) => (f) => {
    const at = titleAt(i);
    const a = T3.mv.arrive(f, { at, dur: 12, ease: 'snap', from: TITLE_FROM[i] });
    const st = T3.mv.settle(f, at + 12, { dir: [1, 0], pxPerSec: 3 });                        // drifts on the way it came in
    const l = T3.mv.leave(f, { at: CUT1 - 8 + i, dur: 8, ease: 'expoIn', to: { x: 1100 } });  // fastest on the cut
    return { x: a.x + st.x + l.x, y: a.y + st.y, s: a.s * st.s, r: 0, o: a.o };
  };
  const split = (f) => 18 * (1 - T3.EZ.at(f, titleAt(0), 12, 'snap'));                        // RGB split = the word's travel still to go

  const N = 5;
  const cardAt = (i) => CUT1 - 2 + T3.mv.stagger(i, N, { from: 8, to: 3 });                   // dealt: the gaps shrink 8 → 3 f
  const card = (i) => (f) => {
    const at = cardAt(i);
    const a = T3.mv.arrive(f, { at, dur: 12, ease: 'snap', from: { y: 340, r: 12 - 6 * i, o: 0 } });
    const st = T3.mv.settle(f, at + 12, { scale: 0.005 });                                    // no dir: a scale creep only
    return { x: 0, y: a.y, s: a.s * st.s, r: a.r, o: a.o };
  };

  const flash = (f) => (f < CUT2 ? T3.EZ.at(f, CUT2 - 6, 4, 'p3in') : 0);                     // blooms to flat white, holds 2 f, hard cut
  const clear = (f) => T3.EZ.at(f, CUT2, 3, 'power2.out');                                    // shot C opens dark and defocused
  const endAt = (i) => CUT2 - 1 + i;                                                          // starts under the flash; parts 1 f apart
  const end = (i) => (f) => {
    const a = T3.mv.arrive(f, { at: endAt(i), dur: 12, ease: 'snap', from: { y: -70, s: 1.06 } });
    const st = T3.mv.settle(f, endAt(i) + 12, { dir: [0, 1], pxPerSec: 3 });
    return { x: st.x, y: a.y + st.y, s: a.s * st.s, r: 0, o: 1 };
  };

  // the air (move.drift): each shot's background slides across its own bands on one sine that starts 20 f before the
  // shot and ends 20 f after it, so on screen it never slows below ≈ 1 px/f (≈ 1.4 px/f at its fastest)
  const AIR_PAD = 20, AIR_TRAVEL = 72;
  const AIR = [                                   // band angle (CSS deg); dir = the drift across the bands, [sin, −cos] of it
    { deg: 105, dir: [0.966, 0.259], glow: '30% 38%' },                                         // A: right, with the title
    { deg: 15, dir: [0.259, -0.966], glow: '68% 30%' },                                         // B: up, as the cards come
    { deg: 165, dir: [0.259, 0.966], glow: '50% 64%' },                                         // C: down, with the end card's settle
  ];
  const air = (i) => (f) => {
    const [a, b] = SHOTS[i];
    const d = AIR_TRAVEL * (T3.EZ.at(f, a - AIR_PAD, b - a + 2 * AIR_PAD, 'sine') - 0.5);
    return { x: AIR[i].dir[0] * d, y: AIR[i].dir[1] * d };
  };

  let shots, airs, word, red, cyan, rule, tag, cards, ends, fl;
  T3.register({
    id: 'example', start: T3.T0, end: T3.T0 + 5, z: 10,
    init(layer) {
      shots = BG.map((c) => el('div', { position: 'absolute', inset: 0, background: c, display: 'none' }, layer));
      // drawn 160 px past every edge, so the drift never shows a border
      airs = AIR.map((a, i) => el('div', {
        position: 'absolute', inset: '-160px',
        backgroundImage: `radial-gradient(ellipse 900px 640px at ${a.glow}, rgba(255,255,255,0.09), rgba(255,255,255,0) 70%), `
          + `repeating-linear-gradient(${a.deg}deg, rgba(255,255,255,0) 0px, rgba(255,255,255,0.085) 80px, rgba(255,255,255,0) 160px)`,
      }, shots[i]));
      word = el('div', { position: 'absolute', left: 0, top: '340px', width: '1920px', textAlign: 'center', font: '900 200px "Arial Black", Impact, sans-serif', color: '#fff' }, shots[0]);
      red = el('div', { position: 'absolute', inset: 0, color: '#ff2a55', mixBlendMode: 'screen' }, word, 'QUICK CUT');
      cyan = el('div', { position: 'absolute', inset: 0, color: '#2affee', mixBlendMode: 'screen' }, word, 'QUICK CUT');
      el('div', { position: 'relative' }, word, 'QUICK CUT');
      rule = el('div', { position: 'absolute', left: '560px', top: '640px', width: '800px', height: '10px', background: '#fff' }, shots[0]);
      tag = el('div', { position: 'absolute', left: 0, top: '680px', width: '1920px', textAlign: 'center', font: '700 44px Bahnschrift, "Segoe UI", sans-serif', letterSpacing: '12px', color: '#ffd27a' }, shots[0], 'HOUSE SAMPLE');
      cards = Array.from({ length: N }, (_, i) => el('div', { position: 'absolute', left: `${400 + i * 240}px`, top: '380px', width: '200px', height: '300px', borderRadius: '14px', background: i % 2 ? '#ffd27a' : '#f4f6f8', boxShadow: '0 18px 40px rgba(0,0,0,0.45)' }, shots[1]));
      ends = [
        el('div', { position: 'absolute', left: 0, top: '420px', width: '1920px', textAlign: 'center', font: '900 120px "Arial Black", Impact, sans-serif', color: '#f4f6f8' }, shots[2], 'QUICK CUT'),
        el('div', { position: 'absolute', left: 0, top: '580px', width: '1920px', textAlign: 'center', font: '600 36px Bahnschrift, "Segoe UI", sans-serif', letterSpacing: '8px', color: '#8fa3c0' }, shots[2], 'LIB/MOTION · T3.EZ · T3.MV'),
      ];
      fl = el('div', { position: 'absolute', inset: 0, background: '#f2f4f4', opacity: 0 }, layer);
      // the curve sheet (motion-library «Curve sheet»): three arrivals, an exit, the transition and the air
      T3.motionProbe('example.title.in', 0, CUT1 - 8, title(0), { kind: 'arrive', seg: 'example' });
      T3.motionProbe('example.cards.in', CUT1 - 4, CUT2 - 6, card(0), { kind: 'arrive', seg: 'example' });
      T3.motionProbe('example.end.in', CUT2 - 2, END - 1, end(0), { kind: 'arrive', seg: 'example' });
      T3.motionProbe('example.title.out', CUT1 - 10, CUT1, title(0), { kind: 'exit', seg: 'example' });
      T3.motionProbe('example.flash', CUT2 - 8, CUT2 + 4, (f) => ({ o: flash(f) }), { kind: 'transition', seg: 'example' });
      T3.motionProbe('example.air', CUT2, END - 1, air(2), { kind: 'other', seg: 'example' });
    },
    render(t) {
      const f = T3.frame(t) - T3.frame(T3.T0);
      const shot = f < CUT1 ? 0 : f < CUT2 ? 1 : 2;
      shots.forEach((s, i) => { s.style.display = i === shot ? 'block' : 'none'; });
      T3.mv.css(airs[shot], air(shot)(f));
      if (shot === 0) {
        T3.mv.css(word, title(0)(f)); T3.mv.css(rule, title(1)(f)); T3.mv.css(tag, title(2)(f));
        const d = split(f);
        red.style.transform = `translateX(${(-d).toFixed(2)}px)`; cyan.style.transform = `translateX(${d.toFixed(2)}px)`;
      } else if (shot === 1) {
        cards.forEach((c, i) => T3.mv.css(c, card(i)(f)));
      } else {
        ends.forEach((e, i) => T3.mv.css(e, end(i)(f)));
        const k = clear(f);
        shots[2].style.filter = k >= 1 ? 'none' : `blur(${(14 * (1 - k)).toFixed(2)}px) brightness(${(0.35 + 0.65 * k).toFixed(3)})`;
      }
      fl.style.opacity = flash(f).toFixed(3);
    },
  });
})();
