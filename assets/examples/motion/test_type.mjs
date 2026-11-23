// test_type.mjs — standalone verification of T3.mv.chars, T3.mv.swap, and T3.mv.roll.
import { loadTemplate, tally } from './_harness.mjs';

const T = tally('T3.mv type motion (chars, swap, roll)');
const { T3 } = loadTemplate();

// chars: staggered per-character rise
const c0 = T3.mv.chars(10, 'HELLO', { at: 10, per: 1 });
const c2 = T3.mv.chars(12, 'HELLO', { at: 10, per: 1 });
T.ok('chars returns one entry per code point', c0.length === 5 && c2.length === 5);
T.ok('later characters lag earlier ones', c2[0].o > c2[3].o && c2[0].y < c2[3].y);

// swap: shared prefix stays stationary across the transition
const sw = T3.mv.swap(50, 'CHIAKI 1.0', 'CHIAKI 2.0', { at: 50 });
T.ok('swap preserves shared prefix length ("CHIAKI ")', sw.held === 7);
const before = T3.mv.swap(49, 'CHIAKI 1.0', 'CHIAKI 2.0', { at: 50 });
const after = T3.mv.swap(53, 'CHIAKI 1.0', 'CHIAKI 2.0', { at: 50 });
T.ok('prefix glyphs remain at rest (y=0, o=1) before and after swap',
  before.prev.slice(0, 7).every((g) => g.y === 0 && g.o === 1) &&
  after.next.slice(0, 7).every((g) => g.y === 0 && g.o === 1));
T.ok('differing suffix animates cleanly across swap',
  after.next[7].y > 0 && after.next[7].o < 1);

// roll: quadratic ease-out numeric roll with preserved decimals and prefix/suffix
const rStart = T3.mv.roll(10, { at: 10, dur: 18, to: '98.5%' });
const rMid = T3.mv.roll(19, { at: 10, dur: 18, to: '98.5%' });
const rEnd = T3.mv.roll(28, { at: 10, dur: 18, to: '98.5%' });
T.ok('roll starts at 0.0% and lands exactly on 98.5%', rStart.text === '0.0%' && rEnd.text === '98.5%');
T.ok('roll uses ease-out (midpoint > 70% of target)', parseFloat(rMid.text) > 70 && parseFloat(rMid.text) < 98.5);

// roll handles non-numeric swap cleanly
const rStr = T3.mv.roll(28, { at: 10, dur: 12, to: 'READY' });
T.ok('non-numeric text resolves cleanly', rStr.text === 'READY');

T.end();
