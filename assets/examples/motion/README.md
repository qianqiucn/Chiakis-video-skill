# 2D Motion Library Demo & Unit Tests

Interactive visual showcase (`index.html`, `demo.js`) and standalone Node ≥ 22 unit tests (`run_tests.mjs`) covering every module in `assets/template/lib/motion/`.

## Visual Demo
Open `index.html` directly in any browser (or render via `scripts/snap.mjs`) to preview `move.rise`, `move.arrive`, `move.leave`, `move.settle`, `move.stagger`, `type.chars`, `type.roll`, `fx.shutter`, `fx.radial`, `fx.shake`, `trans.tail`, `time.twos`, and `her.wave` / `her.eyes` / `her.motes`.

## Unit Tests (Node ≥ 22, zero browser required)
```bash
node assets/examples/motion/run_tests.mjs
```
- `test_ez.mjs`: named GSAP / CustomEase curves (`T3.EZ`) clamping, monotonicity, and custom Bezier parsing.
- `test_moves.mjs`: `arrive`, `leave`, `settle`, `stagger`, `css`, `motionProbe`, and determinism.
- `test_rise.mjs`: `T3.mv.rise` entrance/exit math, exponential/quadratic defaults, custom ease overrides, and purity.
- `test_type.mjs`: `T3.mv.chars`, `T3.mv.swap` (shared prefix lock), and `T3.mv.roll` (tabular decimals).
- `test_blur.mjs`: `T3.blur.shutter` (180° / 360° opaque sub-frame taps) and `T3.blur.radial` / `push`.
- `test_timing.mjs`: `T3.twos` (fractional `Posterize Time` stepping & landing re-anchors), `T3.relX`, `T3.shake`, and `T3.tail`.
- `test_her2d.mjs`: `T3.her.wave`, `T3.her.warp2` (two-pass alpha warp), `T3.her.eyes`, `T3.her.cam`, and `T3.her.motes`.
- `test_load.mjs`: load order guards, error handling, and `scripts/motion_lint.mjs` integration.
