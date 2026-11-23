// test_rise.mjs — standalone verification of T3.mv.rise (entrance/exit math, defaults, overrides, purity).
import { loadTemplate, tally } from './_harness.mjs';

const T = tally('T3.mv.rise standalone spec');
const { T3 } = loadTemplate();

const cl = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const eo = (k) => (k <= 0 ? 0 : k >= 1 ? 1 : 1 - Math.pow(2, -10 * k));
const pr = (f, a, d) => (d <= 0 ? (f >= a ? 1 : 0) : cl((f - a) / d));

// Entrance matches classic exponential travel + linear fade/blur
let maxDiff = 0;
for (let f = 0; f <= 30; f += 0.25) {
  const got = T3.mv.rise(f, { at: 10, dur: 12, dy: 18, fade: 6, blur: 6, blurDur: 7 });
  const k = pr(f, 10, 12);
  const expY = 18 * (1 - eo(k));
  const expO = pr(f, 10, 6);
  const expB = 6 * (1 - pr(f, 10, 7));
  maxDiff = Math.max(maxDiff, Math.abs(got.y - expY), Math.abs(got.o - expO), Math.abs(got.blur - expB));
}
T.ok('entrance matches classic exponential travel, fade, and de-blur', maxDiff <= 1e-9, `max |diff| ${maxDiff}`);

// Exit accelerates quadratically and fades out cleanly
let exitDiff = 0;
for (let f = 45; f <= 65; f += 0.25) {
  const got = T3.mv.rise(f, { at: 10, out: { at: 50, dur: 6, dy: -14, blur: 6 } });
  const k = pr(f, 50, 6);
  const expY = -14 * (k * k);
  const expO = 1 - k;
  const expB = 6 * k;
  exitDiff = Math.max(exitDiff, Math.abs(got.y - expY), Math.abs(got.o - expO), Math.abs(got.blur - expB));
}
T.ok('exit matches quadratic acceleration and linear fade/blur', exitDiff <= 1e-9, `max |diff| ${exitDiff}`);

// Custom T3.EZ curve override works
const custom = T3.mv.rise(13, { at: 10, dur: 12, dy: 100, ease: 'snap' });
const expSnap = 100 * (1 - T3.EZ.snap(3 / 12));
T.ok('custom ease override uses T3.EZ', Math.abs(custom.y - expSnap) <= 1e-9);

// Determinism across arbitrary seek orders
const frames = [0, 5, 10, 12.5, 16, 22, 50, 53, 56, 60];
const fwd = frames.map((f) => T3.mv.rise(f, { at: 10, out: { at: 50 } }));
const rev = [...frames].reverse().map((f) => T3.mv.rise(f, { at: 10, out: { at: 50 } })).reverse();
T.ok('pure and deterministic across reversed seek order', JSON.stringify(fwd) === JSON.stringify(rev));

T.end();
