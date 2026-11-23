# Layers demo (2026-11-05)
`demo.js` — one segment showing:
- a full-bleed scene illustration as the background with a **frosted-glass panel** over it
  (`backdrop-filter: blur(26px) saturate(.8) brightness(.75)` + translucent tint + 1 px border) —
  renders correctly in headless Chrome screenshots/renders;
- three `T3.meshwarp` layers: a test grid (rooted at the top), an opaque tail close-up (rooted
  at the left edge), and a full-body RGBA cutout whose hair ends/tail sway via a `weight`
  mask (note: the weight mask also bends the legs — split soft parts into their own layers).
Needs `lib/meshwarp.js` after `engine.js`; image paths (assets/B.jpg, E.jpg, J.png, grid.png)
were from the GLM test project and are not included.
