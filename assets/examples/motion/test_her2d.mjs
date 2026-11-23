// test_her2d.mjs — standalone verification of T3.her (wave, eyes, cam, motes, error guards, purity).
import { loadTemplate, tally } from './_harness.mjs';

const T = tally('T3.her 2D character layer staging');
const { T3 } = loadTemplate();

// 1. Hair wave: pinned near root, flowing free outward, deterministic
const rigHair = { root: [[900, 300], [1020, 310]], fan: [960, 260] };
const field0 = T3.her.wave(rigHair, 12, { preset: 'hair' });
const atRoot = field0(960, 305);
const atTip = field0(960, 720);
T.ok('hair wave pins at root (pin=0, zero displacement)', atRoot[2] === 0 && atRoot[0] === 0 && atRoot[1] === 0);
T.ok('hair wave flows freely at tip (pin=1, non-zero displacement)', atTip[2] === 1 && Math.hypot(atTip[0], atTip[1]) > 0.1);

// Veil preset works and rejects bad rigs
const rigVeil = { root: [[800, 200], [1100, 200]], len: 600 };
const veilField = T3.her.wave(rigVeil, 15, { preset: 'veil' });
T.ok('veil wave returns valid displacement', veilField(950, 650)[2] === 1);
let threwBadRig = false;
try { T3.her.wave({}, 0); } catch (e) { threwBadRig = e.name === 'T3MotionError'; }
T.ok('bad rig throws T3MotionError', threwBadRig);

// 2. Eye states: 4-frame blink 0.5 / 1 / 1 / 0.5
const blink = [-1, 0, 1, 2, 3, 4].map((k) => T3.her.eyes(50 + k, { kind: 'blink', at: 50 }));
T.ok('blink matches [0, 0.5, 1, 1, 0.5, 0]', JSON.stringify(blink) === JSON.stringify([0, 0.5, 1, 1, 0.5, 0]));

// 3. Group camera: smooth cosine move, deterministic
const camA = T3.her.cam(0, 0, 48);
const camB = T3.her.cam(24, 0, 48);
const camC = T3.her.cam(48, 0, 48);
T.ok('her.cam progresses monotonically from start to end',
  camA.s <= camB.s && camB.s <= camC.s && JSON.stringify(T3.her.cam(24, 0, 48)) === JSON.stringify(camB));

// 4. Dust motes: pure frame function drawing deterministic particles onto a 2D context
function mockCtx() {
  const ops = [];
  return {
    ops,
    canvas: { width: 1920, height: 1080 },
    globalAlpha: 1,
    fillStyle: '',
    save() {}, restore() {}, translate() {}, rotate() {}, scale() {},
    createRadialGradient() { return { addColorStop() {} }; },
    beginPath() {}, fill() { ops.push('fill'); },
    arc(x, y, r) { ops.push([+x.toFixed(3), +y.toFixed(3), +r.toFixed(3)]); },
  };
}
const c1 = mockCtx(), c2 = mockCtx();
const n1 = T3.her.motes(c1, 20);
const n2 = T3.her.motes(c2, 20);
T.ok('her.motes draws deterministically onto a 2D canvas context', n1 > 0 && n1 === n2 && JSON.stringify(c1.ops) === JSON.stringify(c2.ops));

T.end();
