// test_timing.mjs — standalone verification of T3.twos, T3.relX, T3.shake, T3.tail.
import { loadTemplate, tally } from './_harness.mjs';

const T = tally('T3 timing helpers (twos, relX, shake, tail)');
const { T3 } = loadTemplate();

// 1. T3.twos — integer and fractional AE Posterize Time stepping
const seq24 = Array.from({ length: 10 }, (_, f) => T3.twos(f, 0, { n: 2 }));
T.ok('24fps->12fps (n=2) steps on twos', JSON.stringify(seq24) === JSON.stringify([0, 0, 2, 2, 4, 4, 6, 6, 8, 8]));

const seq30 = Array.from({ length: 10 }, (_, f) => Math.floor(T3.twos(f, 0, { n: 2.5 })));
// Fractional n=2.5 alternates 3, 2, 3, 2 frames per step
const runs = [];
for (let i = 0; i < seq30.length; i++) {
  if (!runs.length || seq30[i] !== seq30[i - 1]) runs.push(1);
  else runs[runs.length - 1]++;
}
T.ok('30fps->12fps (n=2.5) alternates 3,2,3,2 cadence', JSON.stringify(runs) === JSON.stringify([3, 2, 3, 2]));

// Multi-anchor landing re-anchor
T.ok('multi-anchor re-anchors exactly on landing frame', T3.twos(15, [0, 15], { n: 2 }) === 15);
T.ok('returns raw frame before start and from end onward', T3.twos(3, 10, { n: 2, end: 20 }) === 3 && T3.twos(20, 10, { n: 2, end: 20 }) === 20);

// 2. T3.relX — undoes sine ease across 0..n-1
T.ok('relX maps endpoints and midpoint exactly',
  T3.relX(0, 101) === 0 && Math.abs(T3.relX(0.5, 101) - 50) <= 1e-9 && T3.relX(1, 101) === 100);

// 3. T3.shake — decaying alternating deterministic hit shake
const s0 = T3.shake(20, 20, { amp: 30 });
const s1 = T3.shake(21, 20, { amp: 30 });
const sEnd = T3.shake(27, 20, { amp: 30 });
T.ok('shake peaks on f0, decays and alternates sides, ends at 0',
  Math.hypot(s0.x, s0.y) > Math.hypot(s1.x, s1.y) && s0.x * s1.x <= 0 && sEnd.x === 0 && sEnd.y === 0 && sEnd.r === 0);
T.ok('shake is pure/deterministic (sub-frame shares whole-frame offset)',
  JSON.stringify(T3.shake(20.2, 20, { amp: 30 })) === JSON.stringify(s0));

// 4. T3.tail — afterimage & afterglow tables
const ai = [0, 1, 2, 3, 4].map((k) => T3.tail(100 + k, 100, 'afterimage'));
const ag = [0, 1, 2, 3, 4].map((k) => T3.tail(100 + k, 100, 'afterglow'));
T.ok('afterimage matches 0.38/0.16/0.05/0.02/0', JSON.stringify(ai) === JSON.stringify([0.38, 0.16, 0.05, 0.02, 0]));
T.ok('afterglow matches 0.30/0.14/0.06/0.02/0', JSON.stringify(ag) === JSON.stringify([0.3, 0.14, 0.06, 0.02, 0]));

T.end();
