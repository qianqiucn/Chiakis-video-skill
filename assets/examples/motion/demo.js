// motion-sheet: inline
// motion: move.rise, move.arrive, move.leave, move.settle, move.stagger, curve.house, curve.probe, type.chars, type.roll, her.wave, her.eyes, her.camera, her.motes, fx.shutter, fx.radial, fx.shake, trans.tail, time.twos, time.relief
/* motion sheet · demo of lib/motion R1 (f 0–143) and R2 (f 144–287) · 24 fps, 288 f, no beat grid (a demo, not a film) · curve family: style-grammar §6b hype row
| moment      | element                | frames (start / len) | id                         | ease                    | stagger / settle                    | departure and reason |
|-------------|------------------------|----------------------|----------------------------|-------------------------|-------------------------------------|----------------------|
| lines in    | 5 text lines           | 10 / 12              | move.rise                  | house default (classic expo) | 1 f apart                      | — |
| lines out   | 5 text lines           | 112 / 6              | move.rise (out)            | house default (k²)      | 0.5 f apart                         | — |
| title in    | block, rule, tag       | 12 / 12              | move.arrive                | T3.EZ.snap              | parts 1 f apart; move.settle 2 px/s | — |
| title out   | block, rule, tag       | 116 / 8              | move.leave                 | T3.EZ.expoIn            | 1 f apart                           | — |
| deal        | 8 cards                | 14 / 12 each         | move.arrive, move.stagger  | T3.EZ.snap              | 8 → 3 f; move.settle 0.5 % scale    | — |
| cards out   | 8 cards                | 108 / 8              | move.leave                 | T3.EZ.p3in              | 1 f apart                           | — |
| exit to cut | 3 bars, shot A         | 60 / 8               | move.leave                 | T3.EZ.expoIn            | 1 f apart                           | — |
| next shot   | 3 bars, shot B         | 67 / 14              | move.arrive                | T3.EZ.snap              | 1 f apart; move.settle 2 px/s       | starts 1 f before the cut at 68, so it enters already moving |
| curves      | 12 dots on curve plots | every 36 f           | curve.house                | each T3.EZ curve        | —                                   | the dot's x is the plot's time axis (scan) |
| curve sheet | probe plot             | whole                | curve.probe                | —                       | —                                   | the playhead is the clock (scan) |
R2 page (frames below are local: page frame − 144)
| name chain  | 3 words, per character | 8 / 12, swaps 50, 90; out 128 | type.chars           | house rise (classic expo) | in 1 f a character; out 0.5 f (swap), 0.4 f (plain); prefix held | — |
| word swap   | 2 words                | swap at 70           | type.chars (T3.mv.swap)    | house rise              | perOut 0.5, perIn 1, lead 2         | — |
| values      | 4 values, tabular      | 10 / 18; changes 60, 100 | type.roll              | quad-out (q2o)          | rows 4 f apart                      | a date ↔ dash change fades 3 f out, 4 f in |
| her shot    | hair layer             | whole                | her.wave                   | the sample's wave       | —                                   | gain 3, so the wave reads at panel size |
| her shot    | eye edits              | gaze 36, blink 64, glance back 96, blink 120 | her.eyes | the sample's blink, smoothstep gaze | —                     | — |
| her shot    | whole picture          | 4 → 150              | her.camera                 | the sample's cosine     | —                                   | longer than the sample's 5 → 40.5, so it is still moving at the page's end |
| her shot    | dust                   | whole                | her.motes                  | the sample's wobble and shutter | —                           | seeded placement (her2d's own), not the sample's eight |
| fast pass   | 3 balls                | 12 / 12 in, 60 / 10 out, 90 / 12 in, 130 / 10 out | fx.shutter | T3.EZ.snap, T3.EZ.expoIn | —                     | lane 1 unblurred for comparison |
| cut A → B   | shot B                 | cut 48, k 0–8        | fx.radial                  | the source's decay      | push 7 % (T3.blur.push)             | — |
| cut A → B   | shot A carried over    | 48 / 4               | trans.tail                 | afterimage table        | —                                   | — |
| cut B → A   | glow at the focus      | 96 / 4               | trans.tail                 | afterglow table         | —                                   | — |
| hits        | whole panel            | 72 / 7, 120 / 7      | fx.shake                   | house hit decay         | —                                   | amp 14 (30 px is typical for a full-frame drop) |
| stepped     | 2 dots                 | runs from 8 and 76   | time.twos                  | T3.EZ.sine path         | —                                   | a demo of the clock; the house use is PV remakes only |
| relief      | 24-frame strip         | whole                | time.relief                | T3.EZ.sine keys undone  | —                                   | — |
probes: demo.rise (arrive), demo.rise.out (exit), demo.arrive (arrive), demo.deal (arrive), demo.leave (exit), demo.cut (transition),
        demo2.chars (arrive), demo2.cam (camera), demo2.pass (arrive), demo2.shake (other)
*/
/* demo.js — every lib/motion entry on placeholder shapes (no project art), one panel each, on two pages:
 *   R1 (f 0–143): move.rise (DOM, through T3.mv.css) · move.arrive + move.settle · move.stagger · move.leave and the
 *   next shot · curve.house (the T3.EZ table) · curve.probe (the R1 probes, sampled every ¼ f, with the playhead).
 *   R2 (f 144–287): type.chars and the swap · type.roll (DOM, tabular digits) · her shot (her.wave through warp2,
 *   her.eyes, her.camera, her.motes on drawn placeholder layers) · fx.shutter · fx.radial + trans.tail + fx.shake ·
 *   time.twos + time.relief.
 * Every pose is a pure function of the frame; render() and the probes call the same functions.
 * Open assets/examples/motion/index.html in Chrome; the tests beside it need no browser (node run_tests.mjs).
 */
(function () {
  const FPS = T3.FPS, END = 144, CUT = 68;
  const P = [[40, 96], [660, 96], [1280, 96], [40, 590], [660, 590], [1280, 590]], PW = 600, PH = 460;
  const C = { bg: '#0c0f15', panel: '#141922', line: '#2a3242', text: '#e8edf5', dim: '#8792a6', cyan: '#59d8ff', pink: '#ff6bb5', amber: '#ffc25c', green: '#7dffa8', violet: '#b49bff', red: '#ff7a6b' };
  const UI = (w, px) => `${w} ${px}px "Segoe UI", Arial, sans-serif`;

  // ---- poses (frame → pose); the probes below sample these same functions
  const lineAt = (i) => 10 + i;
  const line = (i) => (f) => T3.mv.rise(f, { at: lineAt(i), out: { at: 112 + 0.5 * i } });
  const title = (i) => (f) => {
    const at = 12 + T3.mv.stagger(i, 3, { from: 1, to: 1 });
    const a = T3.mv.arrive(f, { at, from: { x: -380, s: 1.12, o: 0 } }), st = T3.mv.settle(f, at + 12, { dir: [1, 0] }), l = T3.mv.leave(f, { at: 116 + i, to: { x: 760 } });
    return { x: a.x + st.x + l.x, y: a.y + st.y, s: a.s * st.s, r: 0, o: a.o };
  };
  const card = (i) => (f) => {
    const at = 14 + T3.mv.stagger(i, 8);   // dealt: gaps 8 → 3 f
    const a = T3.mv.arrive(f, { at, from: { y: -300, r: -10 + 3 * i, o: 0 } }), st = T3.mv.settle(f, at + 12), l = T3.mv.leave(f, { at: 108 + i, to: { y: 420 }, ease: 'p3in' });
    return { x: 0, y: a.y + l.y, s: st.s, r: a.r, o: a.o };
  };
  const barA = (i) => (f) => {
    const a = T3.mv.arrive(f, { at: 6 + i, from: { x: -520 } }), st = T3.mv.settle(f, 18 + i, { dir: [1, 0] }), l = T3.mv.leave(f, { at: 60 + i, to: { x: 640 } });
    return { x: a.x + st.x + l.x, y: 0, s: 1, r: 0, o: 1 };
  };
  const barB = (i) => (f) => {
    const a = T3.mv.arrive(f, { at: CUT - 1 + i, dur: 14, from: { x: -520 } }), st = T3.mv.settle(f, CUT + 13 + i, { dir: [1, 0] }), l = T3.mv.leave(f, { at: 116 + i, to: { x: 640 }, ease: 'p3in' });
    return { x: a.x + st.x + l.x, y: 0, s: 1, r: 0, o: 1 };
  };
  const shotAB = (f) => (f < CUT ? barA(0)(f) : barB(0)(f));

  T3.motionProbe('demo.rise', 8, 30, line(0), { kind: 'arrive', seg: 'motion_demo' });
  T3.motionProbe('demo.rise.out', 110, 122, line(0), { kind: 'exit', seg: 'motion_demo' });
  T3.motionProbe('demo.arrive', 10, 60, title(0), { kind: 'arrive', seg: 'motion_demo' });
  T3.motionProbe('demo.deal', 30, 62, card(4), { kind: 'arrive', seg: 'motion_demo' });
  T3.motionProbe('demo.leave', 56, CUT, barA(0), { kind: 'exit', seg: 'motion_demo' });
  T3.motionProbe('demo.cut', 56, 96, shotAB, { kind: 'transition', seg: 'motion_demo' });

  // ---- drawing helpers
  let cv, g, lines = [], sheet = null;
  function panel(n, id, note, bg) {
    const [x, y] = P[n];
    g.fillStyle = bg || C.panel; g.fillRect(x, y, PW, PH);
    g.strokeStyle = C.line; g.lineWidth = 1; g.strokeRect(x + 0.5, y + 0.5, PW - 1, PH - 1);
    g.fillStyle = C.cyan; g.font = UI(700, 24); g.textBaseline = 'alphabetic'; g.fillText(id, x + 20, y + 38);
    g.fillStyle = C.dim; g.font = UI(400, 16); g.fillText(note, x + 20, y + 62);
  }
  function withPose(p, cx, cy, draw) {
    if (!(p.o > 0.003)) return;
    g.save(); g.globalAlpha = Math.min(1, p.o); g.translate(cx + p.x, cy + p.y); g.rotate((p.r || 0) * Math.PI / 180); g.scale(p.s, p.s); draw(); g.restore();
  }
  function rrect(x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
  function clipPanel(n) { const [x, y] = P[n]; g.save(); g.beginPath(); g.rect(x + 1, y + 72, PW - 2, PH - 73); g.clip(); }

  // ---- the curve sheet of this page's probes: sampled once (they are pure), drawn under a moving playhead
  function buildSheet() {
    const cols = [C.cyan, C.pink, C.amber, C.green, C.violet, C.red];
    return T3.motionProbe.ids().filter((id) => id.startsWith('demo.')).map((id, i) => {
      const rows = T3.motionProbe.sample(id), ch = ['x', 'y', 's', 'o'].map((c) => {
        const v = rows.map((r) => r[c]).filter((u) => u != null); return { c, lo: Math.min(...v), hi: Math.max(...v) };
      }).filter((q) => Number.isFinite(q.lo)).sort((a, b) => (b.hi - b.lo) - (a.hi - a.lo))[0];
      const span = ch.hi - ch.lo || 1;
      return { id, col: cols[i % cols.length], ch: ch.c, pts: rows.map((r) => [r.f, (r[ch.c] - ch.lo) / span]) };
    });
  }

  T3.register({
    id: 'motion_demo', start: 0, end: END / FPS, z: 0,
    init(layer) {
      cv = T3.el('canvas', { position: 'absolute', left: 0, top: 0, width: '1920px', height: '1080px' }, layer); cv.width = 1920; cv.height = 1080; g = cv.getContext('2d');
      const box = T3.el('div', { position: 'absolute', left: P[0][0] + 'px', top: P[0][1] + 'px', width: PW + 'px', height: PH + 'px', overflow: 'hidden' }, layer);
      lines = ['ENTRY NAME', 'A SECOND LINE OF SET TYPE', 'LABEL · 03', 'SMALL CAPTION TEXT', '00.0 / 100'].map((s, i) => {
        const e = T3.el('div', { position: 'absolute', left: '40px', top: 96 + i * 66 + 'px', font: UI(i === 0 ? 700 : 600, i === 0 ? 44 : 30), color: i === 0 ? C.text : '#c6cfdc', letterSpacing: '1px', whiteSpace: 'nowrap', visibility: 'hidden' }, box, s);
        return e;
      });
      sheet = buildSheet();
    },
    render(t) {
      const f = Math.round(t * FPS);
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.fillStyle = C.bg; g.fillRect(0, 0, 1920, 1080);
      g.fillStyle = C.text; g.font = UI(700, 30); g.fillText('lib/motion · page 1 · release R1 · every entry on placeholder shapes', 40, 58);
      g.fillStyle = C.dim; g.font = UI(400, 22); g.fillText(`frame ${f} / ${2 * END}   ·   24 fps   ·   assets/examples/motion`, 1290, 58);

      // 1 · move.rise: DOM lines through T3.mv.css
      panel(0, 'move.rise', 'Editorial rise: lines 1 f apart, out 0.5 f apart (T3.mv.rise + T3.mv.css)');
      lines.forEach((e, i) => T3.mv.css(e, line(i)(f)));

      // 2 · move.arrive + move.settle, then move.leave
      panel(1, 'move.arrive + move.settle', 'snap 12 f, parts 1 f apart, then the after-push');
      clipPanel(1);
      { const [x, y] = P[1];
        withPose(title(0)(f), x + 300, y + 230, () => { g.fillStyle = C.cyan; rrect(-200, -60, 400, 120, 16); g.fill(); g.fillStyle = '#081018'; g.font = UI(800, 64); g.textAlign = 'center'; g.fillText('TITLE', 0, 22); g.textAlign = 'left'; });
        withPose(title(1)(f), x + 300, y + 320, () => { g.fillStyle = C.text; g.fillRect(-200, -4, 400, 8); });
        withPose(title(2)(f), x + 300, y + 372, () => { g.fillStyle = C.pink; rrect(-90, -22, 180, 44, 22); g.fill(); g.fillStyle = '#1a0812'; g.font = UI(700, 22); g.textAlign = 'center'; g.fillText('TAG', 0, 8); g.textAlign = 'left'; }); }
      g.restore();

      // 3 · move.stagger: a dealt row
      panel(2, 'move.stagger', 'eight cards dealt, gaps 8 → 3 f, each on snap; out on p3in');
      clipPanel(2);
      { const [x, y] = P[2];
        for (let i = 0; i < 8; i++) withPose(card(i)(f), x + 72 + i * 65, y + 270, () => { g.fillStyle = i % 2 ? C.amber : C.green; rrect(-28, -44, 56, 88, 8); g.fill(); g.fillStyle = '#10130c'; g.font = UI(800, 30); g.textAlign = 'center'; g.fillText(String(i + 1), 0, 11); g.textAlign = 'left'; }); }
      g.restore();

      // 4 · move.leave into a cut, the next shot already moving
      const shotB = f >= CUT;
      panel(3, 'move.leave → cut → move.arrive', 'expoIn into the cut at f 68; shot B enters mid-move', shotB ? '#1b1626' : C.panel);
      clipPanel(3);
      { const [x, y] = P[3], bar = shotB ? barB : barA;
        for (let i = 0; i < 3; i++) withPose(bar(i)(f), x + 300, y + 170 + i * 90, () => { g.fillStyle = shotB ? C.violet : C.cyan; rrect(-220, -26, 440, 52, 26); g.fill(); });
        g.fillStyle = C.dim; g.font = UI(600, 18); g.fillText(shotB ? 'SHOT B' : 'SHOT A', x + 20, y + PH - 20); }
      g.restore();

      // 5 · curve.house: each T3.EZ curve with a dot running along it
      panel(4, 'curve.house', 'T3.EZ: GSAP curves, k clamped; dot cycles every 36 f');
      { const [x0, y0] = P[4], cw = 140, chh = 120;
        T3.EZ.names.forEach((nm, i) => {
          const cx = x0 + 20 + (i % 4) * (cw + 5), cy = y0 + 80 + Math.floor(i / 4) * (chh + 7), mag = nm === 'bump' ? 5 : 1;
          const X = (k) => cx + 10 + k * (cw - 20), Y = (v) => cy + chh - 22 - ((v * mag + 0.2) / 1.5) * (chh - 40);
          g.strokeStyle = C.line; g.strokeRect(cx + 0.5, cy + 0.5, cw - 1, chh - 1);
          g.beginPath(); g.strokeStyle = C.cyan; g.lineWidth = 2;
          for (let s = 0; s <= 60; s++) { const k = s / 60; if (s) g.lineTo(X(k), Y(T3.EZ[nm](k))); else g.moveTo(X(k), Y(T3.EZ[nm](k))); }
          g.stroke(); g.lineWidth = 1;
          const k = Math.min(1, (f % 36) / 24);   // motion-ok: scan the dot's x is the plot's time axis
          g.fillStyle = C.pink; g.beginPath(); g.arc(X(k), Y(T3.EZ[nm](k)), 5, 0, Math.PI * 2); g.fill();
          g.fillStyle = C.text; g.font = UI(600, 15); g.fillText(nm + (mag > 1 ? ' ×5' : ''), cx + 8, cy + chh - 6);
        }); }

      // 6 · curve.probe: this page's probes, normalised, against the frame
      panel(5, 'curve.probe', 'T3.motionProbe.sample, ¼ f; each probe on its widest channel');
      { const [x0, y0] = P[5], L = x0 + 30, R = x0 + PW - 30, top = y0 + 90, bot = y0 + PH - 120;
        const X = (fr) => L + (fr / END) * (R - L), Y = (v) => bot - v * (bot - top);
        g.strokeStyle = C.line; g.strokeRect(L + 0.5, top + 0.5, R - L, bot - top);
        sheet.forEach((s, i) => {
          g.beginPath(); g.strokeStyle = s.col; g.lineWidth = 2;
          s.pts.forEach(([fr, v], j) => (j ? g.lineTo(X(fr), Y(v)) : g.moveTo(X(fr), Y(v)))); g.stroke(); g.lineWidth = 1;
          g.fillStyle = s.col; g.font = UI(600, 15); g.fillText(`${s.id} (${s.ch})`, x0 + 30 + (i % 3) * 185, y0 + PH - 80 + Math.floor(i / 3) * 24);
        });
        g.strokeStyle = C.text; g.beginPath(); g.moveTo(X(f) + 0.5, top); g.lineTo(X(f) + 0.5, bot); g.stroke();   // motion-ok: scan the playhead is the clock
        g.fillStyle = C.dim; g.font = UI(400, 14); g.fillText('f 0', L, bot + 18); g.fillText(`f ${END}`, R - 34, bot + 18); }
    },
  });
})();

// ---- page 2 · release R2: type motion, her 2D shot, blur and timing (lf = page frame − 144) --------------------------
(function () {
  const FPS = T3.FPS, F0 = 144, LEN = 144, EZ = T3.EZ;
  const P = [[40, 96], [660, 96], [1280, 96], [40, 590], [660, 590], [1280, 590]], PW = 600, PH = 460, IH = PH - 72;
  const C = { bg: '#0c0f15', panel: '#141922', line: '#2a3242', text: '#e8edf5', dim: '#8792a6', cyan: '#59d8ff', pink: '#ff6bb5', amber: '#ffc25c', green: '#7dffa8', violet: '#b49bff', red: '#ff7a6b' };
  const UI = (w, px) => `${w} ${px}px "Segoe UI", Arial, sans-serif`;
  const SEG = 'motion_demo_r2';

  // ---- poses (local frame → pose); the probes call the same functions
  // type.chars: a name chain, each word arriving by one swap and leaving by the next; and one T3.mv.swap
  const W0 = 'MODEL ONE', W1 = 'MODEL ONE MAX', W2 = 'MODEL TWO';
  const chain = (lf) => [
    [W0, T3.mv.chars(lf, W0, { at: 8, out: { at: 50, hold: W1 } })],
    [W1, T3.mv.chars(lf, W1, { at: 50, hold: W0, out: { at: 90, hold: W2 } })],
    [W2, T3.mv.chars(lf, W2, { at: 90, hold: W1, out: { at: 128 } })],
  ];
  const round = (lf) => T3.mv.swap(lf, 'ROUND 1', 'ROUND 2', { at: 70 });
  // type.roll: each row rolls for the latest change that has begun
  const ROWS = [
    { label: 'SCORE', steps: [[10, null, '87.4'], [60, '87.4', '91.2']] },
    { label: 'LATENCY', steps: [[14, null, '1.80 s'], [100, '1.80 s', '0.95 s']] },
    { label: 'CHANGE', steps: [[18, null, '-4.2%'], [60, '-4.2%', '3.1%']] },
    { label: 'RELEASE', steps: [[22, null, '2025.08.07'], [100, '2025.08.07', '—']] },
  ];
  const rowRoll = (row, lf) => {
    let s = row.steps[0];
    for (const st of row.steps) if (st[0] <= lf) s = st;
    return T3.mv.roll(lf, s[1] == null ? { at: s[0], to: s[2] } : { at: s[0], from: s[1], to: s[2] });
  };
  const rowPose = (i, lf) => T3.mv.rise(lf, { at: ROWS[i].steps[0][0] - 2, out: { at: 132 + i } });
  // her shot: placeholder layers drawn in init; the rig, the camera and the eye events
  const RIG = { root: [[792, 470], [838, 372], [960, 322], [1082, 372], [1128, 470]], fan: [960, 470] };
  const HAIR_BOX = [600, 290, 1320, 1010];
  const camAt = (lf) => T3.her.cam(lf, 4, 150);
  const GAZE = [{ gaze: 36, dur: 3 }, { glance: 96, to: 0 }], BLINK = [{ blink: 64 }, { blink: 120 }];
  const MOTES = { seed: 5, n: 12, span: [0, LEN] };
  // fx.shutter: one ball passing right, then left, then right again, on house curves
  const passX = (lf) => 70 + 460 * (EZ.at(lf, 12, 12, 'snap') - EZ.at(lf, 60, 10, 'expoIn') + EZ.at(lf, 90, 12, 'snap') - EZ.at(lf, 130, 10, 'expoIn'));
  // fx.radial, trans.tail, fx.shake: cut A → B at 48 and B → A at 96, two hits
  const CUT1 = 48, CUT2 = 96, HITS = [72, 120];
  const shakeAt = (lf) => HITS.map((h) => T3.shake(lf, h, { amp: 14 })).reduce((a, s) => ({ x: a.x + s.x, y: a.y + s.y, r: a.r + s.r }), { x: 0, y: 0, r: 0 });
  // time.twos: the same path on the smooth clock and on twos and threes, runs restarting at 8 and 76
  const swing = (fr) => EZ.at(fr, 8, 60, 'sine') - EZ.at(fr, 76, 60, 'sine');
  const RUNS = [8, 76];

  T3.motionProbe('demo2.chars', F0 + 6, F0 + 30, (f) => { const p = chain(f - F0)[0][1][0]; return { y: p.y, o: p.o }; }, { kind: 'arrive', seg: SEG });
  T3.motionProbe('demo2.cam', F0, F0 + LEN, (f) => { const c = camAt(f - F0); return { x: c.x, s: c.s }; }, { kind: 'camera', seg: SEG });
  T3.motionProbe('demo2.pass', F0 + 8, F0 + 40, (f) => ({ x: passX(f - F0) }), { kind: 'arrive', seg: SEG });
  T3.motionProbe('demo2.shake', F0 + 70, F0 + 82, (f) => shakeAt(f - F0), { kind: 'other', seg: SEG });

  // ---- placeholder art (drawn once, no files): a plate with three eye states, a soft-alpha hair layer
  const mk = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
  function drawPlate(c, eyes) {
    const x = c.getContext('2d'), TAU = Math.PI * 2;
    const bg = x.createLinearGradient(0, 0, 0, 1080); bg.addColorStop(0, '#1d2340'); bg.addColorStop(1, '#3a2a35');
    x.fillStyle = bg; x.fillRect(0, 0, 1920, 1080);
    x.fillStyle = 'rgba(255,214,160,0.10)'; x.beginPath(); x.moveTo(1300, 0); x.lineTo(1700, 0); x.lineTo(1500, 1080); x.lineTo(1100, 1080); x.fill();
    x.fillStyle = '#2b3550'; x.beginPath(); x.ellipse(960, 1180, 560, 330, 0, 0, TAU); x.fill();
    x.fillStyle = '#e9c6b0'; x.fillRect(910, 700, 100, 160); x.beginPath(); x.ellipse(960, 540, 165, 205, 0, 0, TAU); x.fill();
    x.strokeStyle = '#a8645a'; x.lineWidth = 5; x.beginPath(); x.arc(960, 640, 26, 0.2 * Math.PI, 0.8 * Math.PI); x.stroke();
    for (const ex of [893, 1027]) {
      if (eyes === 'closed') { x.strokeStyle = '#3a2430'; x.lineWidth = 6; x.beginPath(); x.arc(ex, 528, 32, 0.18 * Math.PI, 0.82 * Math.PI); x.stroke(); continue; }
      const dx = eyes === 'up' ? 7 : 0, dy = eyes === 'up' ? -7 : 0;
      x.fillStyle = '#fbf7f2'; x.beginPath(); x.ellipse(ex, 545, 36, 19, 0, 0, TAU); x.fill();
      x.fillStyle = '#4a6fa5'; x.beginPath(); x.arc(ex + dx, 545 + dy, 14, 0, TAU); x.fill();
      x.fillStyle = '#10131c'; x.beginPath(); x.arc(ex + dx, 545 + dy, 6.5, 0, TAU); x.fill();
      x.fillStyle = '#ffffff'; x.beginPath(); x.arc(ex + dx + 5, 540 + dy, 3.5, 0, TAU); x.fill();
      x.strokeStyle = '#3a2430'; x.lineWidth = 4; x.beginPath(); x.ellipse(ex, 545, 37, 20, 0, Math.PI * 1.05, Math.PI * 1.95); x.stroke();
    }
  }
  function drawHair(c) {
    const x = c.getContext('2d');
    x.fillStyle = 'rgba(52,36,70,0.96)'; x.beginPath(); x.ellipse(960, 430, 190, 130, 0, Math.PI, Math.PI * 2); x.fill();
    x.lineCap = 'round';
    for (let i = 0; i < 46; i++) {
      const u = i / 45, side = u < 0.5 ? -1 : 1, a = Math.abs(u - 0.5) * 2;   // a: 0 at the parting, 1 at the temples
      const rx = 960 + side * (40 + 150 * a), ry = 330 + 120 * a * a;
      const tx = 960 + side * (200 + 70 * a + 18 * ((i * 7) % 5)), ty = 820 + 30 * ((i * 3) % 4);
      const gr = x.createLinearGradient(rx, ry, tx, ty);
      gr.addColorStop(0, 'rgba(52,36,70,0.95)'); gr.addColorStop(0.7, 'rgba(70,48,92,0.75)'); gr.addColorStop(1, 'rgba(90,64,118,0)');
      x.strokeStyle = gr; x.lineWidth = 14 + 6 * ((i * 5) % 3);
      x.beginPath(); x.moveTo(rx, ry); x.bezierCurveTo(rx + side * 120, ry + 40, tx - side * 10, ty - 260, tx, ty); x.stroke();
    }
  }
  function ball(c, x, y, col) { c.fillStyle = col; c.beginPath(); c.arc(x, y, 28, 0, Math.PI * 2); c.fill(); c.fillStyle = '#0c0f15'; c.fillRect(x - 4, y - 28, 8, 56); }
  function scene(c, lf) {                    // the cut panel's two shots; A pushes in toward the cut, B carries the push
    c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
    const B = lf >= CUT1 && lf < CUT2, cx = PW / 2, cy = IH / 2;
    const s = lf < CUT1 ? 1 + 0.3 * EZ.at(lf, 24, 24, 'expoIn') : B ? T3.blur.push(lf - CUT1) : 1;
    c.fillStyle = B ? '#2a1a12' : '#0f1a26'; c.fillRect(0, 0, PW, IH);
    c.setTransform(s, 0, 0, s, cx - s * cx, cy - s * cy);
    if (B) {
      for (let r = 0; r < 4; r++) for (let q = 0; q < 6; q++) { c.fillStyle = (r + q) % 2 ? C.amber : C.red; c.fillRect(60 + q * 82, 50 + r * 76, 70, 64); }
    } else {
      c.lineWidth = 10; [150, 110, 70, 30].forEach((r, i) => { c.strokeStyle = i % 2 ? C.violet : C.cyan; c.beginPath(); c.arc(cx, cy, r, 0, Math.PI * 2); c.stroke(); });
    }
    c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = C.text; c.font = UI(700, 20); c.fillText(B ? 'SHOT B' : 'SHOT A', 16, IH - 16);
  }

  let cv, g, shot, plate, plateUp, plateShut, hair, pc, pcB, pcA, rowEls = [];
  function panel(n, id, note) {
    const [x, y] = P[n];
    g.fillStyle = C.panel; g.fillRect(x, y, PW, PH);
    g.strokeStyle = C.line; g.lineWidth = 1; g.strokeRect(x + 0.5, y + 0.5, PW - 1, PH - 1);
    g.fillStyle = C.cyan; g.font = UI(700, 24); g.textBaseline = 'alphabetic'; g.fillText(id, x + 20, y + 38);
    g.fillStyle = C.dim; g.font = UI(400, 16); g.fillText(note, x + 20, y + 62);
  }
  function word(chars, poses, x0, y0, px, col) {         // x measured on the whole word, so its spacing holds
    g.font = UI(800, px); g.fillStyle = col;
    for (let i = 0; i < chars.length; i++) {
      const p = poses[i];
      if (!(p.o > 0.003)) continue;
      g.save(); g.globalAlpha = Math.min(1, p.o); g.filter = p.blur > 0.05 ? `blur(${p.blur.toFixed(2)}px)` : 'none';
      g.translate(x0 + g.measureText(chars.slice(0, i).join('')).width + p.x, y0 + p.y); g.scale(p.s, p.s); g.fillText(chars[i], 0, 0); g.restore();
    }
  }

  T3.register({
    id: SEG, start: F0 / FPS, end: (F0 + LEN) / FPS, z: 0,
    init(layer) {
      cv = T3.el('canvas', { position: 'absolute', left: 0, top: 0, width: '1920px', height: '1080px' }, layer); cv.width = 1920; cv.height = 1080; g = cv.getContext('2d');
      shot = mk(1920, 1080); plate = mk(1920, 1080); plateUp = mk(1920, 1080); plateShut = mk(1920, 1080); hair = mk(1920, 1080);
      drawPlate(plate, 'open'); drawPlate(plateUp, 'up'); drawPlate(plateShut, 'closed'); drawHair(hair);
      pc = mk(PW, IH); pcB = mk(PW, IH); pcA = mk(PW, IH);
      const box = T3.el('div', { position: 'absolute', left: P[1][0] + 'px', top: P[1][1] + 72 + 'px', width: PW + 'px', height: IH + 'px', overflow: 'hidden' }, layer);
      rowEls = ROWS.map((r, i) => {
        const row = T3.el('div', { position: 'absolute', left: '40px', top: 30 + i * 84 + 'px', width: '520px', height: '60px', visibility: 'hidden' }, box);
        T3.el('div', { position: 'absolute', left: 0, top: '16px', font: UI(600, 22), color: C.dim, letterSpacing: '2px' }, row, r.label);
        const v = T3.el('div', { position: 'absolute', right: 0, top: 0, font: UI(700, 44), color: C.text, fontVariantNumeric: 'tabular-nums', textAlign: 'right', whiteSpace: 'nowrap' }, row, '');
        return { row, v, text: null };
      });
    },
    render(t) {
      const f = Math.round(t * FPS), lf = f - F0;
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.filter = 'none'; g.fillStyle = C.bg; g.fillRect(0, 0, 1920, 1080);
      g.fillStyle = C.text; g.font = UI(700, 30); g.fillText('lib/motion · page 2 · release R2 · placeholder art, no project files', 40, 58);
      g.fillStyle = C.dim; g.font = UI(400, 22); g.fillText(`frame ${f} / ${F0 + LEN}   ·   24 fps   ·   assets/examples/motion`, 1290, 58);

      // 1 · type.chars: the chain and one swap
      panel(0, 'type.chars', 'in 1 f a letter; the shared prefix holds (T3.mv.chars, T3.mv.swap)');
      { const [x, y] = P[0];
        for (const [w, poses] of chain(lf)) word([...w], poses, x + 40, y + 200, 52, C.text);
        const r = round(lf);
        word([...'ROUND 1'], r.prev, x + 40, y + 330, 40, C.amber); word([...'ROUND 2'], r.next, x + 40, y + 330, 40, C.amber);
        g.fillStyle = C.dim; g.font = UI(400, 15); g.fillText('chain: swaps at 50 and 90, plain exit at 128 · swap: at 70', x + 40, y + PH - 24); }

      // 2 · type.roll: DOM rows with tabular digits
      panel(1, 'type.roll', 'quad-out onto the value; a word change fades 3 f out, 4 f in');
      rowEls.forEach((e, i) => {
        const ok = T3.mv.css(e.row, rowPose(i, lf)), r = rowRoll(ROWS[i], lf);
        if (ok && e.text !== r.text) { e.v.textContent = r.text; e.text = r.text; }
        e.v.style.opacity = r.o;
      });

      // 3 · her shot: plate and eye edits under the camera, the hair through the two-pass warp, the motes
      panel(2, 'her.wave · her.eyes · her.camera · her.motes', 'drawn placeholder layers; wave at gain 3 to read at this size');
      { const x = shot.getContext('2d'), c = camAt(lf);
        x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.fillStyle = '#000'; x.fillRect(0, 0, 1920, 1080);
        x.setTransform(...T3.her.cam.matrix(c)); x.drawImage(plate, 0, 0);
        const up = T3.her.eyes(lf, GAZE), shut = T3.her.eyes(lf, BLINK);
        if (up > 0) { x.globalAlpha = up; x.drawImage(plateUp, 0, 0); }
        if (shut > 0) { x.globalAlpha = shut; x.drawImage(plateShut, 0, 0); }
        x.globalAlpha = 1; x.setTransform(1, 0, 0, 1, 0, 0);
        T3.her.warp2(x, hair, { box: HAIR_BOX, cols: 24, rows: 22, cam: c }, T3.her.wave(RIG, lf, { gain: 3 }));
        T3.her.motes(x, lf, Object.assign({ cam: c }, MOTES));
        const [px, py] = P[2]; g.drawImage(shot, px + 1, py + 72 + (IH - 337.5) / 2, PW - 2, 337.5);
        g.fillStyle = C.dim; g.font = UI(400, 15); g.fillText(`eye edits: gaze ${up.toFixed(2)} · closed ${shut.toFixed(2)} · camera ×${(c.s / 1.02).toFixed(4)}`, px + 20, py + PH - 12); }

      // 4 · fx.shutter: no blur, 180° (5 samples about f), 360° (10 samples ending on f)
      panel(3, 'fx.shutter', 'lanes: none · 180° 5 samples · 360° 10 samples, trailing');
      { const c = pc.getContext('2d'), moving = Math.abs(passX(lf + 0.5) - passX(lf - 0.5)) > 0.25;
        c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.clearRect(0, 0, PW, IH);
        ball(c, passX(lf), 70, C.cyan);
        T3.blur.shutter(c, lf, (s, fs) => ball(s, passX(fs), 190, C.pink), { samples: moving ? 5 : 1 });
        T3.blur.shutter(c, lf, (s, fs) => ball(s, passX(fs), 310, C.amber), { shutter: 360, samples: moving ? 10 : 1 });
        const [x, y] = P[3]; g.drawImage(pc, x, y + 72); }

      // 5 · fx.radial + trans.tail + fx.shake: a cut, its push blur and carried-over picture, then two hits
      panel(4, 'fx.radial · trans.tail · fx.shake', 'cuts at 48 and 96: radial blur, afterimage, afterglow; hits at 72, 120');
      { const c = pcB.getContext('2d');
        scene(c, lf);
        if (lf >= CUT1 && lf < CUT2) {
          T3.blur.radial(c, null, { cx: PW / 2, cy: IH / 2, k: lf - CUT1 });
          const a = T3.tail(lf, CUT1, 'afterimage');
          if (a > 0) { scene(pcA.getContext('2d'), CUT1 - 1); c.globalAlpha = a; c.drawImage(pcA, 0, 0); c.globalAlpha = 1; }
        }
        if (lf >= CUT2) {
          const a = T3.tail(lf, CUT2, 'afterglow');
          if (a > 0) { const gl = c.createRadialGradient(PW / 2, IH / 2, 0, PW / 2, IH / 2, 220); gl.addColorStop(0, `rgba(255,214,160,${a})`); gl.addColorStop(1, 'rgba(255,214,160,0)'); c.globalCompositeOperation = 'screen'; c.fillStyle = gl; c.fillRect(0, 0, PW, IH); c.globalCompositeOperation = 'source-over'; }
        }
        const [x, y] = P[4], sh = shakeAt(lf);
        g.save(); g.beginPath(); g.rect(x + 1, y + 72, PW - 2, IH - 1); g.clip();
        g.translate(x + PW / 2 + sh.x, y + 72 + IH / 2 + sh.y); g.rotate(sh.r * Math.PI / 180); g.drawImage(pcB, -PW / 2, -IH / 2); g.restore(); }

      // 6 · time.twos + time.relief
      panel(5, 'time.twos · time.relief', 'one path on 1s, 2s, 3s · a sine-keyed strip played back even');
      { const [x0, y0] = P[5], L = x0 + 50, Wd = PW - 100;
        const dots = [[lf, '1s', C.cyan], [T3.twos(lf, RUNS), '2s', C.pink], [T3.twos(lf, RUNS, { n: 3 }), '3s', C.amber]];
        dots.forEach(([fr, nm, col], i) => {
          const yy = y0 + 110 + i * 50;
          g.strokeStyle = C.line; g.beginPath(); g.moveTo(L, yy); g.lineTo(L + Wd, yy); g.stroke();
          g.fillStyle = col; g.beginPath(); g.arc(L + swing(fr) * Wd, yy, 12, 0, Math.PI * 2); g.fill();
          g.fillStyle = C.dim; g.font = UI(600, 15); g.fillText(nm, x0 + 16, yy + 5);
        });
        const n = 24, s = EZ.at(lf, 0, LEN - 1, 'sine'), even = T3.relX(s, n), keyed = s * (n - 1), cw = Wd / n;
        [[even, 'relX', 300], [keyed, 'keys', 360]].forEach(([ix, nm, yy]) => {
          const i0 = Math.floor(ix), fr = ix - i0;
          for (let i = 0; i < n; i++) {
            const lit = i === i0 ? 1 - fr : i === i0 + 1 ? fr : 0;
            g.fillStyle = C.line; g.fillRect(L + i * cw + 1, y0 + yy, cw - 2, 34);
            if (lit > 0) { g.globalAlpha = lit; g.fillStyle = C.green; g.fillRect(L + i * cw + 1, y0 + yy, cw - 2, 34); g.globalAlpha = 1; }
          }
          g.fillStyle = C.dim; g.font = UI(600, 15); g.fillText(nm, x0 + 8, y0 + yy + 22);
        });
        g.fillStyle = C.dim; g.font = UI(400, 15); g.fillText(`s ${s.toFixed(3)} → relX ${even.toFixed(2)} (even) · raw keys ${keyed.toFixed(2)}`, L, y0 + PH - 24); }
    },
  });
})();
