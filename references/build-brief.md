# Builder Brief Template (2D Studio Build)

Copy this template into `<project>/work/brief_<key>.md` and fill in the bracketed fields before launching an Edit or Design craft subagent.

```markdown
# Build Brief — <project> / <act or key>
- **Skill root (`<sk>`)**: <absolute path to Chiaki's-video-skill>
- **Project root (`<proj>`)**: <absolute path to project>
- **Craft**: <Edit / Motion | Graphic Design | Sound>
- **Time span**: <start_s>s – <end_s>s (frames <f0>–<f1> at <FPS> fps; write segment bounds as exact rationals `f0 / FPS`)
- **Visual concept & medium**: <chosen pitch summary, palette hex tokens, curve family from style-grammar.md §6b>
- **Bundled fonts already packed**: <list font families available via T3.fonts.use(...)>

## Files You Own (edit ONLY these)
- Motion sheet (write BEFORE code): `<proj>/work/motion_<key>.md` (or `motion_<key>_design.md`)
- Segment file(s): `<proj>/web/segments/<owned_file>.js`
- Do NOT edit `web/index.html`, `engine.js`, or another craft's segment files.

## Available Local Assets
- 2D textures: `<proj>/web/assets/tex/` (copied from `<sk>/assets/textures/`)
- Client plates / illustrations / audio: `<proj>/web/assets/`

## Ready-to-Run CLI Commands (run without asking)
- Static motion lint (fast, no browser):
  `node "<sk>/scripts/motion_lint.mjs" "<proj>/web/index.html" --segments <your_file.js>`
- Curve sheet + runtime lint (queued):
  `python -X utf8 "<sk>/scripts/run_queue.py" web --lane <key> -- node "<sk>/scripts/motion_lint.mjs" "<proj>/web/index.html" --segments <your_file.js> --curves --out "<proj>/work/motion_<key>"`
- Contact sheet screenshots (queued):
  `python -X utf8 "<sk>/scripts/run_queue.py" web --lane <key> -- node "<sk>/scripts/snap.mjs" "<proj>/web/index.html" "<proj>/work/snaps_<key>" "<f0>-<f1>:6" --sheet preview --fps <FPS>`

## Hard Rules
1. `render(t)` MUST be 100 % pure in `t` (no `Math.random()`, `Date.now()`, `performance.now()`, or mutable frame state).
2. First 15 lines MUST contain `// motion-sheet: ...` and `// motion: ...` citing valid IDs from `references/motion-library.md`.
3. Never hand-roll easing math; use `T3.EZ.*`, `T3.mv.*`, `T3.blur.*`, `T3.twos`, `T3.her.*`, or `T3.EZ.get('M0,0 C...')`.
4. Register ≥ 3 `T3.motionProbe(...)` calls in `init()` sharing the exact pose functions used in `render(t)`.
5. Zero remote fonts (`https://`); use `T3.fonts.use('Family', 'sans-serif')` only.
6. Every landed element needs subtle `move.settle` or live ambient `move.drift` (no frozen frames unless deliberate `Posterize Time` stepping is declared in this brief).
7. Every headless Chrome command MUST go through `scripts/run_queue.py web`.

## Self-Check & Handoff Report (~20 min time-box)
Before reporting done:
1. Run static `motion_lint.mjs` → **0 FAIL**.
2. Generate SVG curve sheet (`--curves`) and inspect `curves.svg` + `lint.txt`.
3. Capture contact sheet via `snap.mjs --sheet` covering **every transition frame pair (`cut-1, cut, cut+1`) AND every subtitle/caption hold midpoint** → **0 render errors, 0 page errors**, visually confirm no black wipe corners, no subtitle-over-foreground collisions, legible emblem contrast, and balanced peak brightness before handing in.
4. Report back with: files touched, motion sheet path, curve sheet path, contact sheet path, any declared departures, and any open issues.
```
