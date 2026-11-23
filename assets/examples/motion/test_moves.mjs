// test_moves.mjs — the house moves (move.arrive, move.leave, move.settle, move.stagger), T3.mv.css, the curve probe
// (curve.probe), purity, and the rules every lib/motion file keeps (no Math.random, no clock, a full header).
// The house rule being checked has its figures in style-grammar §6b; the thresholds below test this library's defaults.
// Run: node test_moves.mjs   (exit 1 on any failure)
import fs from 'node:fs';
import path from 'node:path';
import { page, tally, grid, TPL } from './_harness.mjs';

const T = tally('house moves, css, probe, purity');
const W = page(), mv = W.T3.mv, EZ = W.T3.EZ, probe = W.T3.motionProbe;
const near = (a, b, e = 1e-9) => Math.abs(a - b) <= e;

// ---- move.arrive
{
  const o = { at: 20, from: { x: -300, s: 1.2, r: -6, o: 0 } }, A = (f) => mv.arrive(f, o);
  const p0 = A(20), p1 = A(32), pb = A(10), pa = A(50);
  T.ok('arrive: starts at `from`, holds it before `at`', near(p0.x, -300) && near(p0.s, 1.2) && near(p0.r, -6) && near(p0.o, 0) && near(pb.x, -300));
  T.ok('arrive: lands at rest at at + 12 and stays', [p1, pa].every((p) => near(p.x, 0) && near(p.s, 1) && near(p.r, 0) && near(p.o, 1) && near(p.y, 0)));
  const share2 = 1 - A(22).x / -300, share3 = 1 - A(23).x / -300;
  T.ok('arrive: 70–90 % of the travel in the first 2 f (front-loaded)', share2 >= 0.7 && share2 <= 0.9, `${(100 * share2).toFixed(1)} % at 2 f, ${(100 * share3).toFixed(1)} % at 3 f`);
  const xs = grid(20, 32, 0.25).map((f) => A(f).x), v = xs.slice(1).map((x, i) => x - xs[i]);
  T.ok('arrive: moves one way, never back', v.every((d) => d >= 0));
  T.ok('arrive: speed falls toward the landing (last ¼ f < 1 % of the first)', v[v.length - 1] < 0.01 * v[0], `first ¼ f ${v[0].toFixed(2)} px, last ${v[v.length - 1].toExponential(2)} px`);
  const q = mv.arrive(5, { at: 0, dur: 10, from: { y: 80 }, to: { x: 500, y: 300 } });
  T.ok('arrive: `to` sets the rest pose, `from` fills from it', near(mv.arrive(0, { at: 0, from: { y: 80 }, to: { x: 500, y: 300 } }).x, 500) && near(mv.arrive(0, { at: 0, from: { y: 80 }, to: { x: 500, y: 300 } }).y, 80) && q.y > 80 && q.y < 300);
  T.ok('arrive: ease option takes T3.EZ names', near(mv.arrive(26, { at: 20, from: { x: -100 }, ease: 'p4out' }).x, -100 * (1 - EZ.p4out(0.5))));
  T.throws('arrive: `at` is required', () => mv.arrive(3, { from: { x: 1 } }));
}
// ---- move.leave
{
  const L = (f) => mv.leave(f, { at: 40, to: { x: 400, o: 0 } });
  T.ok('leave: rest until `at`, `to` at at + 8', near(L(39).x, 0) && near(L(40).x, 0) && near(L(48).x, 400) && near(L(48).o, 0) && near(L(60).x, 400));
  const xs = grid(40, 48, 0.25).map((f) => L(f).x), v = xs.slice(1).map((x, i) => x - xs[i]);
  T.ok('leave: speeds up all the way into the cut', v.every((d, i) => i === 0 || d >= v[i - 1] - 1e-12), `first ¼ f ${v[0].toExponential(2)} px, last ${v[v.length - 1].toFixed(2)} px`);
  T.ok('leave: under 10 % of the travel by mid-move', L(44).x < 40, `${(L(44).x / 4).toFixed(2)} % at 4 f`);
  T.ok('leave: `from` sets the start pose', near(mv.leave(0, { at: 0, from: { y: 50 }, to: { x: 10 } }).y, 50));
}
// ---- move.settle
{
  const fps = W.T3.FPS, S = (f, o) => mv.settle(f, 100, Object.assign({ dir: [1, 0] }, o));
  T.ok('settle: nothing before or at the landing', ['x', 'y'].every((c) => S(90)[c] === 0 && S(100)[c] === 0) && S(100).s === 1);
  const v0 = (S(100.01).x - S(100).x) / 0.01;
  T.ok('settle: speed 0 at the landing (no corner after a landing at rest)', v0 < 0.01 * (2 / fps), `${v0.toExponential(2)} px/f`);
  let vmax = 0, tmax = 0;
  for (const f of grid(100, 220, 0.05)) { const v = (S(f + 0.001).x - S(f - 0.001).x) / 0.002; if (v > vmax) { vmax = v; tmax = f - 100; } }
  T.ok('settle: peak speed = pxPerSec (2 px/s at the defaults)', near(vmax * fps, 2, 1e-3), `${(vmax * fps).toFixed(4)} px/s at ${tmax.toFixed(1)} f after landing`);
  const d2 = S(148).x, vLate = (S(220.5).x - S(219.5).x) * fps;
  T.ok('settle: 1–3 px/s over the first 2 s', d2 / 2 >= 1 && d2 / 2 <= 3, `${d2.toFixed(2)} px in 2 s`);
  T.ok('settle: still moving 5 s after landing (>= 25 % of its peak speed)', vLate >= 0.5, `${vLate.toFixed(2)} px/s at 5 s`);
  T.ok('settle: scale +0.5 % at span (48 f), still creeping after', near(S(148).s, 1.005, 1e-12) && S(200).s > 1.005, `s(148) ${S(148).s.toFixed(6)}, s(200) ${S(200).s.toFixed(6)}`);
  const xs = grid(100, 220, 0.25).map((f) => S(f).x), acc = xs.slice(2).map((x, i) => x - 2 * xs[i + 1] + xs[i]);
  T.ok('settle: no constant-speed run (speed changes on every ¼ f)', acc.every((a) => Math.abs(a) > 1e-12));
  T.ok('settle: dir as [x, y], { x, y } and degrees agree', near(S(130, { dir: [0, 1] }).y, S(130, { dir: { x: 0, y: 3 } }).y) && near(S(130, { dir: 90 }).y, S(130, { dir: [0, 1] }).y) && near(S(130, { dir: 90 }).x, 0, 1e-12));
  T.ok('settle: no dir = scale only', mv.settle(130, 100).x === 0 && mv.settle(130, 100).y === 0 && mv.settle(130, 100).s > 1);
  T.throws('settle: a zero dir throws', () => mv.settle(130, 100, { dir: [0, 0] }));
}
// ---- move.stagger
{
  const n = 8, off = Array.from({ length: n }, (_, i) => mv.stagger(i, n)), gaps = off.slice(1).map((o, i) => o - off[i]);
  T.ok('stagger: item 0 at 0, first gap 8, last gap 3', off[0] === 0 && near(gaps[0], 8) && near(gaps[n - 2], 3), gaps.map((g) => g.toFixed(2)).join(' '));
  T.ok('stagger: gaps shrink every step (a cause, not a slide deck)', gaps.every((g, i) => i === 0 || g < gaps[i - 1]));
  T.ok('stagger: one item, or i <= 0, is 0; i past the end holds the last', mv.stagger(0, 1) === 0 && mv.stagger(3, 1) === 0 && mv.stagger(-2, 5) === 0 && mv.stagger(12, n) === off[n - 1]);
  T.ok('stagger: parts 1–2 f apart ({ from: 2, to: 1 })', near(mv.stagger(1, 3, { from: 2, to: 1 }), 2) && near(mv.stagger(2, 3, { from: 2, to: 1 }), 3));
  T.ok('stagger: two items = one gap of `from`', near(mv.stagger(1, 2), 8));
}
// ---- T3.mv.css
{
  let writes = 0;
  const style = new Proxy({}, { set(o, k, v) { writes++; o[k] = v; return true; } }), el = { style };
  mv.css(el, mv.rise(13, { at: 10 }));
  T.ok('css: writes opacity, transform, filter of a rise pose', style.visibility === 'visible' && /^0\.\d{3}$/.test(style.opacity) && /^translate\(0\.00px,\d+\.\d\dpx\)$/.test(style.transform) && /^blur\(\d\.\d\dpx\)$/.test(style.filter), `${style.opacity} | ${style.transform} | ${style.filter}`);
  const w0 = writes; mv.css(el, mv.rise(13, { at: 10 }));
  T.ok('css: an unchanged pose writes nothing', writes === w0);
  mv.css(el, { o: 1, x: 0, y: 0, s: 1, blur: 0 });
  T.ok('css: rest pose = transform none, filter none, opacity 1', style.transform === 'none' && style.filter === 'none' && style.opacity === '1');
  mv.css(el, { x: 3, r: 12.5, s: 1.1 });
  T.ok('css: rotate in degrees, scale after rotate', style.transform === 'translate(3.00px,0.00px) rotate(12.500deg) scale(1.1000)' && style.filter === 'none', style.transform);
  T.ok('css: o <= 0.003 hides and returns false', mv.css(el, { o: 0.001 }) === false && style.visibility === 'hidden');
}
// ---- curve.probe
{
  const fn = (f) => mv.arrive(f, { at: 10, from: { x: -200 } });
  T.ok('probe: returns fn', probe('t.arrive', 8, 26, fn, { kind: 'arrive', seg: 'test' }) === fn);
  const rows = probe.sample('t.arrive');
  T.ok('probe: ¼-frame samples, both ends', rows.length === 73 && rows[0].f === 8 && rows[72].f === 26 && rows.every((r) => near(r.x, fn(r.f).x)), `${rows.length} rows`);
  T.ok('probe: step 1 and an uneven span keep f1', probe('t.leave', 0, 7.5, (f) => mv.leave(f, { at: 2, to: { y: -90 } })) && probe.sample('t.leave', 1).map((r) => r.f).join(',') === '0,1,2,3,4,5,6,7,7.5');
  T.ok('probe: ids in registration order', probe.ids().join(',') === 't.arrive,t.leave');
  probe('t.bad', 0, 4, (f) => ({ x: f > 2 ? NaN : f }));
  T.throws('probe: a NaN sample throws', () => probe.sample('t.bad'));
  T.throws('probe: unknown id throws', () => probe.sample('nope'));
  T.throws('probe: f1 <= f0 throws', () => probe('t.x', 5, 5, fn));
  const all = JSON.parse(JSON.stringify(probe.all()));
  T.ok('probe.all(): JSON-safe, errors reported per probe', all['t.arrive'].samples.length === 73 && all['t.arrive'].meta.kind === 'arrive' && /NaN/.test(all['t.bad'].error), Object.keys(all).join(','));
  T.ok('window.__T3_PROBES holds the registry', W.__T3_PROBES['t.arrive'].f1 === 26 && typeof W.__T3_PROBES['t.arrive'].fn === 'function');
}
// ---- purity: any frame order gives the same numbers
{
  const fns = [(f) => mv.rise(f, { at: 4, out: 30 }), (f) => mv.arrive(f, { at: 6, from: { x: -80, s: 0.9 } }), (f) => mv.leave(f, { at: 20, to: { x: 99 } }), (f) => mv.settle(f, 18, { dir: 45 }), (f) => EZ.at(f, 3, 12, 'elastic')];
  const F = grid(-3, 40, 0.25), fwd = F.map((f) => JSON.stringify(fns.map((h) => h(f))));
  const rev = new Map([...F].reverse().map((f) => [f, JSON.stringify(fns.map((h) => h(f)))]));
  let s = 12345; const shuf = [...F].sort(() => ((s = (s * 16807) % 2147483647) / 2147483647) - 0.5);
  const sh = new Map(shuf.map((f) => [f, JSON.stringify(fns.map((h) => h(f)))]));
  T.ok('pure: forwards, backwards and shuffled frame orders agree', F.every((f, i) => rev.get(f) === fwd[i] && sh.get(f) === fwd[i]), `${F.length} frames × ${fns.length} moves`);
  // R1's six calls stay first and in order; later releases add after them (the full list: test_type.mjs)
  T.ok('T3.mv is frozen and keeps the R1 API', Object.isFrozen(mv) && Object.keys(mv).slice(0, 6).join(',') === 'rise,arrive,leave,settle,stagger,css');
}
// ---- the files themselves: every module in lib/motion
for (const f of fs.readdirSync(path.join(TPL, 'lib', 'motion')).filter((n) => n.endsWith('.js')).sort()) {
  const src = fs.readFileSync(path.join(TPL, 'lib', 'motion', f), 'utf8'), code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  T.ok(`${f}: no Math.random, Date or performance clock in code`, !/Math\.random|\bDate\b|performance\.now/.test(code));
  const head = src.slice(0, src.indexOf('*/'));
  T.ok(`${f}: header names API, library ids, source, approval`, /API/.test(head) && /Library ids?:/.test(head) && /Source/.test(head) && /Approval|approval/.test(head));
}
T.done();
