// test_blur.mjs — standalone verification of T3.blur (shutter 180/360, radial blur, push, purity).
import { loadTemplate, tally } from './_harness.mjs';

const T = tally('T3.blur shutter and radial blur');
const { T3 } = loadTemplate();

// 180-degree default shutter: 5 centred taps over [-0.25, +0.25], weights sum to 1
const t180 = T3.blur.times(10);
T.ok('default 180 deg returns 5 centred samples', t180.length === 5 && Math.abs(t180[2].f - 10) <= 1e-9);
T.ok('180 deg weights sum to 1', Math.abs(t180.reduce((a, b) => a + b.w, 0) - 1) <= 1e-9);

// 360-degree trailing shutter: 10 samples ending on f
const t360 = T3.blur.times(10, { shutter: 360 });
T.ok('360 deg defaults to 10 trailing samples ending on f',
  t360.length === 10 && Math.abs(t360[0].f - 9.1) <= 1e-9 && Math.abs(t360[9].f - 10) <= 1e-9);

// Unknown align throws T3MotionError
let threwAlign = false;
try { T3.blur.times(10, { align: 'bad' }); } catch (e) { threwAlign = e.name === 'T3MotionError'; }
T.ok('invalid align throws T3MotionError', threwAlign);

// radialSpread & push formulas
const sp0 = T3.blur.radialSpread(0);
const sp5 = T3.blur.radialSpread(5);
const sp9 = T3.blur.radialSpread(9);
T.ok('radialSpread decays exponentially over 0..8 and zeroes at 9',
  Math.abs(sp0 - 0.22) <= 1e-9 && Math.abs(sp5 - 0.22 * Math.exp(-0.55 * 5)) <= 1e-9 && sp9 === 0);

const layers = T3.blur.radialLayers(0.22);
T.ok('radialLayers yields 10 copies with 1/(i+1) alpha (i=1..10)',
  layers.length === 10 && Math.abs(layers[0].a - 0.5) <= 1e-9 && Math.abs(layers[9].a - 1 / 11) <= 1e-9);

const p0 = T3.blur.push(0), p4 = T3.blur.push(4);
T.ok('T3.blur.push rises smoothly from 1', p0 === 1 && p4 > 1 && p4 < 1.1);

T.end();
