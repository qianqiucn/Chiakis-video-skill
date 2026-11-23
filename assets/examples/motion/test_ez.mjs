// test_ez.mjs — T3.EZ (curve.house) equals GSAP's own eases on a k grid (max abs diff <= 1e-9), clamps k, and its
// helpers (bump, get, at) do what lib/motion/ez.js says. The references are gsap.parseEase / CustomEase.create called here
// directly, plus fresh CustomEase objects built from the same paths (so a wrong path in ez.js would fail).
// Run: node test_ez.mjs   (exit 1 on any failure)
import { page, tally, grid } from './_harness.mjs';

const T = tally('T3.EZ vs gsap.parseEase');
const W = page(), EZ = W.T3.EZ, g = W.gsap, C = W.CustomEase;
const cl = (k) => (k < 0 ? 0 : k > 1 ? 1 : k);
const K = grid(-0.5, 1.5, 1 / 1024, [0, 1, 1 / 6, 1 / 12, 0.5, 1 - 1e-12, 1e-12]);

const REF = {   // the frozen table (library plan §2.2): name → GSAP ease string or CustomEase path
  snap: 'M0,0 C0.05,0.9 0.1,1 1,1', expoOut: 'expo.out', p4out: 'power4.out', quintOut: 'quint.out', p3in: 'power3.in',
  expoIn: 'expo.in', back: 'back.out(1.7)', elastic: 'elastic.out(1,0.45)', sine: 'sine.inOut',
  roll: 'M0,0 C0.55,0 0.35,1 1,1', fly: 'M0,0 C0.45,0 0.15,1 1,1',
};
const maxDiff = (a, b) => { let m = 0; for (const k of K) { const d = Math.abs(a(k) - b(k)); if (!(d <= m)) m = d; } return m; };

T.ok('T3.EZ.names is the frozen list + bump', JSON.stringify([...EZ.names]) === JSON.stringify(Object.keys(REF).concat('bump')), EZ.names.join(','));
let n = 0;
for (const [name, src] of Object.entries(REF)) {
  const isPath = src.startsWith('M');
  const ref = isPath ? C.create('test_' + name, src) : g.parseEase(src);
  const m = maxDiff(EZ[name], (k) => ref(cl(k)));
  T.ok(`EZ.${name} == ${isPath ? 'CustomEase "' + src + '"' : 'gsap.parseEase("' + src + '")'} (k clamped)`, m <= 1e-9, `max |diff| ${m.toExponential(2)} over ${K.length} k`);
  if (isPath) {   // the id ez.js registered resolves through gsap.parseEase as well
    const id = { snap: 't3Snap', roll: 't3Roll', fly: 't3Fly' }[name], m2 = maxDiff(EZ[name], (k) => g.parseEase(id)(cl(k)));
    T.ok(`EZ.${name} == gsap.parseEase("${id}")`, m2 <= 1e-9, `max |diff| ${m2.toExponential(2)}`);
  }
  n++;
}
T.ok('quintOut and p4out are the same numbers (GSAP aliases)', maxDiff(EZ.quintOut, EZ.p4out) === 0);
const mb = maxDiff(EZ.bump, (k) => g.parseEase('back.out(1.7)')(cl(k)) - g.parseEase('power4.out')(cl(k)));
T.ok('EZ.bump == back.out(1.7) − power4.out', mb <= 1e-9, `max |diff| ${mb.toExponential(2)}; bump(0) ${EZ.bump(0)}, bump(1) ${EZ.bump(1)}`);

// clamping: outside [0, 1] the curve holds its end value (GSAP alone would extrapolate a CustomEase or back.out)
T.ok('clamped below 0 and above 1', EZ.names.every((nm) => EZ[nm](-0.3) === EZ[nm](0) && EZ[nm](1.4) === EZ[nm](1)));
T.ok('all start at 0 and end at 1 (bump at 0 and 0)', EZ.names.every((nm) => Math.abs(EZ[nm](0)) < 1e-12 && Math.abs(EZ[nm](1) - (nm === 'bump' ? 0 : 1)) < 1e-12));

// the house reading of the curves (style-grammar §6b, 11-18 rule): arrivals front-loaded, exits back-loaded
const head = EZ.snap(2 / 12), head3 = EZ.snap(3 / 12);
T.ok('snap: 70–90 % of the travel by 2 f of 12', head >= 0.7 && head <= 0.9, `${(100 * head).toFixed(1)} % at 2 f, ${(100 * head3).toFixed(1)} % at 3 f`);
T.ok('p3in and expoIn: under 10 % of the travel by mid-move', EZ.p3in(0.5) < 0.1 && EZ.expoIn(0.5) < 0.1, `p3in ${EZ.p3in(0.5).toFixed(4)}, expoIn ${EZ.expoIn(0.5).toFixed(4)}`);
// the snap path parsed right: an independent cubic-bezier solve (engine.js T3.ease.bezier) within CustomEase's sampling error
const bz = W.T3.ease.bezier(0.05, 0.9, 0.1, 1), mz = maxDiff(EZ.snap, (k) => bz(cl(k)));
T.ok('snap matches an independent bezier solve within 5e-3 (CustomEase samples the path piecewise)', mz < 5e-3, `max |diff| ${mz.toExponential(2)}`);

// get / at
T.ok('get(name) returns the table curve', EZ.names.every((nm) => EZ.get(nm) === EZ[nm]));
const p2 = EZ.get('power2.in'), mp2 = maxDiff(p2, (k) => g.parseEase('power2.in')(cl(k)));
T.ok('get("power2.in") == gsap.parseEase, clamped, cached', mp2 <= 1e-9 && EZ.get('power2.in') === p2 && p2(2) === 1, `max |diff| ${mp2.toExponential(2)}`);
const mad = 'M0,0 C0.6,0 0.9,0.6 1,1', gm = EZ.get(mad), mm = maxDiff(gm, (k) => C.create('test_mad', mad)(cl(k)));
T.ok('get("M0,0 C0.6,0 0.9,0.6 1,1") == CustomEase, cached', mm <= 1e-9 && EZ.get(mad) === gm, `max |diff| ${mm.toExponential(2)}`);
T.ok('get(T3.EZ curve) passes it through', EZ.get(EZ.back) === EZ.back && EZ.get(EZ.get('power2.in')) === EZ.get('power2.in'));
T.throws('get(hand-written function) throws T3MotionError', () => EZ.get((k) => k * 2));
T.throws('get("no.such") throws T3MotionError', () => EZ.get('no.such'));
T.throws('get(42) throws T3MotionError', () => EZ.get(42));
let ma = 0;
for (const f of grid(-5, 30, 0.25)) for (const nm of ['snap', 'expoIn', 'back', 'power2.out']) ma = Math.max(ma, Math.abs(EZ.at(f, 4, 12, nm) - EZ.get(nm)((f - 4) / 12)));
T.ok('at(f, f0, dur, name) == get(name)((f − f0) / dur)', ma === 0);
T.ok('at() defaults to snap', EZ.at(6, 4, 12) === EZ.snap(2 / 12));
T.ok('at() with dur 0 is a cut at f0', EZ.at(3.99, 4, 0) === 0 && EZ.at(4, 4, 0) === 1 && EZ.at(9, 4, -2) === 1);
T.ok('T3.EZ is frozen', Object.isFrozen(EZ));

// information only: why move.rise keeps the classic exponential (GSAP 3.15 normalises expo to meet 0 and 1)
const classic = (k) => (k <= 0 ? 0 : k >= 1 ? 1 : 1 - Math.pow(2, -10 * k));
console.log(`info: GSAP ${g.version} expo.out vs classic 1 − 2^(−10k): max |diff| ${maxDiff(EZ.expoOut, (k) => classic(cl(k))).toFixed(5)} (move.rise keeps the classic curve)`);
T.ok(`${n} table curves checked`, n === 11);
T.done();
