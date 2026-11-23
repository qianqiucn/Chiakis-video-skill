# MG styles: 15 motion-design forms and the techniques that make each one recognisable

A style library for choosing the visual form (medium) of a 15–20 s character intro, and later for any motion-design job. Condensed from mg-styles-15 by Vincentwei1021 (MIT licence), https://github.com/Vincentwei1021/mg-styles-15; rewritten in our own words.

## How to use this file
Find the tone or medium in the finder, then go to that style's H2 heading or grep its bold short name (`**8 Morph**`).
- **Who reads it, when**
  - Pitch writers (SKILL.md step 3, `assets/workflows/pitch.js`): a form for her intro, by tone and medium; the forms earlier films used are listed in script-writing §1, and the pitch avoids them.
  - Director (the genre header, script-writing §0–§1): To use it: pick the form whose idea fits the character, then take its Signatures (the look) into the intro's genre header as the checkable style list, while the actions and curves are looked up in motion-library.md first and its Techniques are borrowed only where the library has no entry; the look described here is a starting point, not a template, and neighbouring intros use different forms. The header adds the transition set (style-grammar §3a) and the curve family (style-grammar §6b).
  - Editor/compositor (crafts.md «Editing and motion»): Techniques for eases, timing and cuts; Sound as the starting palette for the SFX layer.
  - Graphic designer (crafts.md «Graphic design»): the form's type treatment, in Techniques and Route (10 Retro's chrome type, 12 Hanazi's three-layer captions, 3 Isometric's titles on the ground plane).
  - Scorer: style fidelity is judged against the genre header's list (quality-bar.md «Scorecard»).
- **Cite** a style by number and short name: «mg-styles: 8 Morph»; one technique by its words: «mg-styles: 8 Morph, bridge shape».
- **Entry format**, always in this order: the H2 heading `N. 中文名 English name`; a tag line, the bold short name `**N Name**` then ★ fast-cut (if marked), tone, medium; then Used for → Signatures → Techniques → Route → Sound.
- **★ fast-cut** marks the five forms that fit our ranking intros best (cool, high-BPM, fast cuts, house-style §1; the genres in script-writing §1), a pointer, not a default.
- **Frames (24 fps)**: Frame counts are at the source's frame rate (30 fps unless the entry says 24); at our 24 fps multiply by 0.8 and round. 4 3D Render and 5 Cel already say 24.
- **Order**: the approved and house moves in `motion-library.md` come first; a form's techniques are the next resort,
  cited by number and name in the segment's `// motion:` header.
- **Links**: a form's eases are refitted to the genre's curve family (style-grammar §6b) and called through `T3.EZ`, and its cuts the transition set (style-grammar §3a); its Sound line is placed and mastered under house-style §1 (the cue sheet, the timbre test, −14 LUFS) with mgaudio (production.md «Installed on D:»).

**In our films** (pointers; the rules live there): the format's energy (house-style §1); no data in an intro, so a form's charts, counters and number rolls show no scores (house-style §2); the locked dashboard (house-style §6); the layering set and footage in every form (house-style §0).

## Finder
By tone, the character an intro might want; a style may sit under several.
- **Precise / technical / mechanical**: 3 Isometric, 8 Morph, 9 Bauhaus, 13 Sticker Explainer, 15 HUD.
- **Playful / comic / bouncy**: 1 Flat, 5 Cel, 6 Collage, 12 Hanazi, 14 Pixel.
- **Literary / handmade / analogue**: 2 Line Art, 5 Cel, 6 Collage.
- **Retro / an era quoted**: 10 Retro (synthwave, VHS, Y2K), 14 Pixel (8-bit), 6 Collage (Monty Python, Constructivist posters), 9 Bauhaus (Bauhaus and Swiss).
- **Luxury / minimal / premium**: 2 Line Art, 8 Morph, 11 Aurora Glass.
- **Data / HUD / explainer** (no scores in an intro, house-style §2): 15 HUD, 13 Sticker Explainer, 3 Isometric.
- **Sci-fi / cyber / neon**: 15 HUD, 10 Retro.
- **Organic / fluid / tactile**: 7 Liquid, 8 Morph.
- **Beat-driven, music-video energy**: 9 Bauhaus, 8 Morph, 7 Liquid, 6 Collage, 10 Retro.
- **Anime / game**: 5 Cel, 14 Pixel, 15 HUD.
- **Slow and calm** (the format runs cool and high-BPM, house-style §1): 11 Aurora Glass, 2 Line Art.

By medium, what the picture is made of (its route in the entry):
- **Flat vector shapes** (SVG + GSAP): 1 Flat, 8 Morph, 9 Bauhaus.
- **One drawn line or a wireframe** (SVG strokes): 2 Line Art, 15 HUD.
- **Hand-drawn, frame by frame** (Canvas2D brush): 5 Cel.
- **Photo cutouts, paper and stickers** (PNG cutouts in DOM/Canvas): 6 Collage, 13 Sticker Explainer.
- **2.5D & Isometric** (CSS 3D / SVG / WebGL2): 3 Isometric, 15 HUD (flat/wireframe FUI).
- **Shader light and fluid** (WebGL): 7 Liquid, 10 Retro, 11 Aurora Glass.
- **Type over footage** (DOM/SVG captions): 12 Hanazi.
- **Pixels** (low-res Canvas, nearest-neighbour): 14 Pixel.
- **A whole era's media** (VHS, CRT, chrome): 10 Retro, 14 Pixel.

**★ fast-cut**: 5 Cel (anime and manga energy), 8 Morph (one shape becoming the next, the hand-off carrier of style-grammar §3c), 10 Retro (cyber night-city glitch), 14 Pixel (one medium), 15 HUD (the tech skin, an RPG status UI).

## 1. 扁平矢量动画 Flat / Vector 2D Motion Graphics
**1 Flat** · tone: playful, bright · medium: flat vector shapes (SVG)
- **Used for**: the everyday MG baseline (SaaS promos, science explainers, annual-report films); grew out of Google Material and the corporate explainer tradition.
- **Signatures**: solid colour blocks, geometric characters, no or almost no gradients, clean negative space, saturated brand palette, elastic entrances and exits
- **Techniques**:
  - Elastic ease carries the style: overshoot `cubic-bezier(0.34,1.56,0.64,1)` (AE: Bezier handles at 70–85 % influence); every entry is anticipation → burst → rebound.
  - About 10 % squash & stretch on moves; secondary action and follow-through on top.
  - Stagger entries by 2–4 frames, each with its own small overshoot; only one hero moves at any moment.
  - Rig: shape layers parented under null controls; limbs rotate about anchor points (head bob, blink).
  - Cuts are carried by a shape wipe (a colour block sweeps the frame) or by an element flying out; no crossfades.
  - Strictly flat, 5–6 bold colours (e.g. #2B2BFF, #FF5A4E, #FFC62B, #2EE6A8, #FFF6E9, ink #151433).
- **Route**: SVG + GSAP (CustomEase / CustomBounce / MorphSVG), motion blur mb=4 on fast moves; 30 fps.
- **Sound**: upbeat future-bass/pop around 120 BPM; a pop, boing or whoosh on every entry, frame-synced.

## 2. 线条动画 Line Art / Line Animation
**2 Line Art** · tone: luxury, minimal, literary, calm · medium: one drawn line (SVG strokes)
- **Used for**: luxury, finance and architecture brand films and logo animations; one thin line is the only design language, minimal and premium.
- **Signatures**: even-width thin line, one or two colours, lots of negative space, a line that keeps growing, a line-to-fill moment
- **Techniques**:
  - Draw-on is the core: AE Trim Paths 0→100 %; web SVG `stroke-dasharray`/`stroke-dashoffset` from `getTotalLength()`.
  - Stroke width constant for the whole piece (2–4 px; ~3 px in the original), round caps; slight path jitter for a hand-drawn feel.
  - Draw speed eases into each corner with `cubic-bezier(0.65,0,0.35,1)`.
  - One-line story: the tail of each figure is the start of the next, paths joined in advance.
  - Line → fill: once an outline closes, the same path's fill spreads out from an anchor point.
  - A virtual camera follows the glowing pen tip; older segments dim to ~35 %; a final dolly-out shows the whole drawing as a poster.
- **Route**: SVG paths + stroke-dashoffset (getTotalLength) + GSAP, with a virtual camera tracking the pen tip.
- **Sound**: sparse felt piano and a soft string swell; a pen-on-paper whisper whose loudness follows tip speed; a light chime on the fill.

## 3. 等轴 2.5D Isometric / 2.5D
**3 Isometric** · tone: precise, technical, explainer, cute miniature · medium: 2.5D blocks (SVG SSR-matrix faces or CSS-3D multiplane)
- **Used for**: tech architecture diagrams and app feature demos (miniature cities, office cut-aways, server rooms); dense yet cute; School of Motion teaches it as isometric mograph.
- **Signatures**: 30° isometric projection, no vanishing point, miniature scenes, buildings that grow, parallel-track camera moves
- **Techniques**:
  - SSR faces: scale vertical to 86.6 % → shear ±30° → rotate ∓30°; build the three faces separately, then assemble. Shortcut: true 3D with an orthographic camera at 35.264° elevation, 45° azimuth.
  - Fake depth by layer order: z-order = screen y; anything moving along the grid keeps a 2:1 pixel slope.
  - Growth: base lands first, walls `scaleY` up from 0 with overshoot, roof caps 2–3 frames later; ground tiles drop in as a wave from the centre with a small bounce each.
  - Camera only slides the whole group (never rotates); foreground : mid : back parallax 1 : 0.8 : 0.6.
  - Pastel studio palette with soft shadows + AO; titles skewed into iso space and set on the ground plane.
- **Route**: SVG with SSR-matrix isometric faces, or CSS-3D multiplane (`lib/multiplane.js`) + crisp cast shadows.
- **Sound**: bright plucky tech melody (FM marimba/pluck); a soft click/pop on every tile or building landing; airy whoosh on the pull-back.

## 4. 3D 渲染系（C4D/Blender 质感） 3D Render / CGI Motion Design
**4 3D Render** · tone: luxury, tactile, organic · medium: 3D and CGI (Blender)
- **Used for**: high-end product films (phones, drinks, sneakers) and brand idents; tactile soft rubber, glass, metal, cloth with clone arrays and physics.
- **Signatures**: PBR materials, shallow depth of field, soft studio lighting, cloner arrays, soft-body collisions, candy-coloured gummy surfaces
- **Techniques**:
  - MoGraph core: a cloner array animated in waves by Random/Plain effectors (Blender: a Geometry Nodes grid).
  - Material trio: SSS for the gummy look + AO + HDRI with three-point lighting (`scripts/blender/asset_lib.py`); mix SSS gummy, glossy plastic, frosted glass, or chrome.
  - Long-tail ease: 80 % of the distance in the first 20 % of the move, a very slow settle, real motion blur.
  - 24/25 fps film rate + f/1.8-feel shallow DOF, separating it from crisp flat 2D styles.
  - The hero object is the axis; particles/fluid/cloth/clones are choreographed around it (hero drops in with a damped-spring jiggle and displaces the field).
- **Route**: Headless Blender CLI (`scripts/run_queue.py blender -- blender -b --python shot.py`, Cycles GPU with OIDN denoise or EEVEE; live look-dev via Blender MCP) → PNG sequence (`lib/sequence.js`) + HTML/Canvas typography overlay (`z=20`); 24 fps.
- **Sound**: ASMR-style soft thuds, squishes, and bubbly pops over an airy cinematic pad; hits frame-synced to impacts.

## 5. 逐帧手绘 / 线条沸腾 Cel Animation / Frame-by-Frame & Line Boil
**5 Cel** · ★ fast-cut · tone: handmade, playful, anime · medium: hand-drawn frame by frame (Canvas2D brush)
- **Used for**: anti-digital, hand-made charm, either fully frame-by-frame or as frame-by-frame texture over vector animation; Giant Ant and Buck accent their work with cel FX (smoke, splashes, speed lines).
- **Signatures**: lines that keep quivering (boil), on-2s / on-3s timing, smear frames, hand-drawn smoke and splash accents, paper-texture ground
- **Techniques**:
  - Timing at 24 fps: on 2s (effectively 12 fps) by default, on 1s for fast action, on 3s for holds.
  - Fake boil: AE Turbulent Displace (amount 2–5, size 50) + evolution re-randomised every 2 frames + Posterize Time 12 fps. Real boil: 3–4 slightly different line drawings cycled every 2 frames.
  - Smear: on a fast move, stretch the object 150–300 % for exactly one in-between frame.
  - Cel FX layer: hand-drawn frame-by-frame smoke/splash/lightning over the vector subject (Buck-style hybrid).
  - Paper texture multiplied at 10–15 % over everything; fills slightly off-register; 3–4 colour palette.
- **Route**: Canvas2D with a custom variable-width brush (centreline + pressure → outline polygon); boil = 3–4 jitter variants cycled every 2 frames; paper multiply; 24 fps.
- **Sound**: playful jazzy pizzicato/xylophone bed + cartoon SFX (strike, fwoosh, pop, poof, sparkle) on the frame.

## 6. 拼贴剪贴 Collage / Cutout Animation
**6 Collage** · tone: handmade, playful, retro-surreal, music-video · medium: photo cutouts and paper (DOM/Canvas)
- **Used for**: music and streetwear short videos; retro-surreal reassembly of old photos, newsprint and torn paper, rooted in Monty Python and Soviet Constructivist posters, now merged with the magazine look.
- **Signatures**: photo cutouts with white edges, halftone dots, newsprint texture, surreal off-proportion assemblies, stepped stop-motion movement
- **Techniques**:
  - Every cutout gets a 2–4 px white edge (scissor-cut look) + a halftone filter.
  - Print palette discipline: lock ~95 % of the film to paper, ink and one print hue (e.g. archival cream, charcoal, magenta-red + blush), reserving one stark foreign accent (ultramarine or a 2-frame cyan negative flash) for a single climax shot.
  - Puppet joints: anchors at shoulder, elbow and jaw, segment-by-segment rotation; the mouth flaps with 2–3 replacement frames.
  - Deliberately low frame rate: main motion at 12 fps, 10 fps (REC/viewfinder) or 6 fps, with ±2 px jitter, broken by brief full-rate smooth shots or a stepped-to-smooth melt (`style-grammar.md` §6e) before a drop.
  - Shared media shell across cuts: wrap fast cuts inside one continuous 35mm film gate (rounded aperture, cyan-fringed bottom sprockets) or reuse one beat-locked CRT signal-flash precomp (`+14 f`, `+50 f` inside 8-beat pull-outs) so disparate shots read as one reel.
  - Contrast staging: hold a translucent line-art figure dead-still while cycling stark backgrounds every ~6 f (静人动底); swap a standing pose's render style every ~15 f (`lineart → silhouette → tint → duotone`) inside perspective frames; tuck giant type *behind* a foreground cutout figure (depth occlusion) and mirror top lyrics 180° onto the bottom bar like a playing card.
  - Layer stack: paper texture → rotated newsprint / pink cross-grid → big colour shapes → photo cutouts → halftone screen / tape / stickers → grain adjustment layer.
  - Transitions: a hand slaps the element onto the page, whole-page flips/tears, monotone red-sandwich bridges, or defocused foreground petal wipes (`style-grammar.md` §3b).
- **Route**: DOM/Canvas with PNG cutouts (rembg or paper-key alpha), offscreen-cached halftone/newsprint/duotone patterns and `T3.hold()` sprite preloading so deterministic Canvas 2D timelines render smoothly (~40 fps); render at 30 fps while stepping designated passages via `T3.twos`.
- **Sound**: vinyl crackle, jazzy boom-bap bed, paper rustles, scissor snips, slaps, a comic pop on the big reveal.

## 7. 液态流动 Liquid Motion
**7 Liquid** · tone: organic, fluid, music-video · medium: shader fluid (WebGL)
- **Used for**: music videos, food and drink ads, transition packs; shapes flow, string out, drip and fuse; organic, satisfying, high-energy.
- **Signatures**: wavy-edge transitions, stringing and dripping, metaball fusion, trailing secondary droplets, organic curves and never a straight line
- **Techniques**:
  - Liquid wipe: a hand-keyed mask whose wavy front sweeps the frame, with 3–5 phase-offset bulges along the front.
  - Fake metaballs: Gaussian blur (20 px+) → tighten the alpha threshold (AE Levels; web `feColorMatrix`), so shapes stick together when close.
  - Neck → snap → rebound: a thin neck trails as a shape pulls away; at the break both ends rebound for 2–3 frames.
  - Fast-out slow-in `cubic-bezier(0.22,1,0.36,1)`: liquid is flung, never moves at constant speed.
  - Secondary droplets follow 2–3 frames behind the main body; landings squash flat.
  - Specular highlights + fresnel rim so it reads as thick 3D liquid, not flat blobs.
- **Route**: WebGL2 fragment shader with 2D SDF metaballs (smooth-min), fake 3D lighting from field-gradient normals, a text SDF for the logo.
- **Sound**: bubbly gloops, pour, splash, drip, deep bass swell under a glossy synth bed.

## 8. 形变动画 Morphing / Shape Morph
**8 Morph** · ★ fast-cut · tone: precise, premium, beat-driven · medium: flat vector shapes (SVG)
- **Used for**: the core grammar of visual storytelling, one shape turning into the next (phone → map pin, cup → sunset); the hardest-to-fake part of Apple keynotes and premium explainers.
- **Signatures**: continuous outlines with no jumps, intermediate bridging shapes, morphs that travel and rotate, squash & stretch at the moment of change
- **Techniques**:
  - Align paths first: equal vertex counts and matching first-vertex positions (AE: reset First Vertex), or the shape knots.
  - Never morph a complex A→B directly: A → simple bridge (circle/capsule) → B, each half 8–12 frames.
  - 10–15 % squash & stretch and a slight rotation over every morph to hide mechanical interpolation; sub-parts morph in sync.
  - Speed peaks mid-move: `cubic-bezier(0.7,0,0.3,1)` with 3-frame cushions at each end.
  - Web: flubber/polymorph for optimal vertex matching (far better than naive SMIL); check a still at each morph's midpoint for tangles.
  - The background colour field changes with every morph through clean colour-block wipes; morphs land on the beat.
- **Route**: SVG + flubber or GSAP MorphSVGPlugin (tune shapeIndex), colour-field wipes.
- **Sound**: rhythmic plucky arpeggio; one pitched whoosh per morph, landing on the beat.

## 9. 几何构成 / 包豪斯 Geometric / Bauhaus Motion
**9 Bauhaus** · tone: precise, mechanical, modernist, beat-driven · medium: flat geometric shapes on a grid (SVG/Canvas)
- **Used for**: kinetic posters and beat-synced graphics; circles, triangles and rectangles translate, rotate and scale precisely on a strict grid; Bauhaus and Swiss International lineage.
- **Signatures**: basic geometric shapes, limited red/yellow/blue/black palette, strict grid alignment, rotation about geometric pivots, beat-driven modular motion
- **Techniques**:
  - Everything snaps to the grid: travel = an integer number of modules (e.g. 240 px modules), every landing on a grid line.
  - Restrained easing: a library curve in its restrained family (`T3.EZ`, never plain linear for an ordinary move; a mechanical beat needs a named object and a `motion-ok` line); overshoot is banned, the mechanical feel is the point.
  - One action per beat (120 BPM = 0.5 s/beat), shapes appear or flip on the hit: quarter circles rotate 90° about a corner, semicircles slide one module, triangles flip, squares split.
  - Alternate the pivot for rhythm: the shape's own centre, an edge vertex, the frame centre.
  - Generative variants: Processing/p5.js arrays driven by trig phase offsets (phase-shifted cascade waves).
  - Palette: cream #F1E9DA, red #E03C31, yellow #F2B705, blue #1E4FA3, black #111; light paper tooth and print misregistration allowed.
- **Route**: SVG/Canvas + GSAP on a strict modular grid with a 120 BPM beat grid.
- **Sound**: minimal techno/click; each flip a pitched click or blip; kick on the quarters.

## 10. 复古系（80s Synthwave / VHS / Y2K 千禧） Retro: 80s Synthwave / VHS / Y2K
**10 Retro** · ★ fast-cut · tone: retro, neon, cyber, music-video · medium: an era's media: neon grid, chrome, VHS (WebGL + a VHS pass)
- **Used for**: quoting an era's media look wholesale (synthwave neon, VHS tape, Y2K liquid chrome and acid colours); Y2K is back strongly in music videos and streetwear brand films.
- **Signatures**: neon glow, perspective-grid horizon, scanlines and RGB shift, chrome lettering, acid palette, skeuomorphic window UI
- **Techniques**:
  - Synthwave trio: a one-point-perspective grid scrolling toward camera (looped vertical offset); a sunset sun in layered gradient bands; double glow, tight ~4 px bright inner + wide ~30 px low-opacity outer.
  - VHS chain: RGB split (red and blue channels offset 1–2 px) → scanlines (10 % black bars every 2 px) → wave-distortion jitter (1–2 random glitch frame-drops per second) → 4:3 rounded-corner mask.
  - Chrome type: very high-contrast multi-stop metallic gradient + bevel highlight + environment-map reflections, with a glint sweep and lens flare.
  - Y2K motion: pop-up windows, cursor clicks, window drags; the skeuomorphic UI is the story.
  - Unstable frame rate on purpose: drop key passages to 15 fps, or play 2 frames in reverse for tape stutter.
- **Route**: WebGL (perspective grid, sun and mountain shaders) + canvas chrome text + CSS/SVG glow, then a VHS pass.
- **Sound**: synthwave with gated-reverb snare, arpeggiated saw bass, lush pads; big chord + crash on the title slam.

## 11. 弥散渐变 / 玻璃拟态 Gradient Blur (Aurora) & Glassmorphism
**11 Aurora Glass** · tone: luxury, minimal, slow · medium: shader light and frosted glass (WebGL + CSS)
- **Used for**: the default look of 2024–26 tech brand films and AI product launches (pushed by iOS 26 Liquid Glass); slow, translucent, expensive.
- **Signatures**: large blurred colour blobs drifting, frosted glass cards, 1 px highlight edges, low-contrast adjacent hues, a slow breathing rhythm
- **Techniques**:
  - Aurora base: 3–5 solid circles blurred 80–150 px, each drifting on a Bezier path in a 20–40 s loop, blending into a mesh gradient.
  - Glass card: `backdrop-filter: blur(20–40px)` + 5–10 % white fill + 1 px inner stroke of 30 % white + large corner radius.
  - 2–3 adjacent hues only (violet-blue-cyan or orange-pink-red); clashing hues go muddy; bright blobs on a dark ground work better than on light.
  - 3–5 % noise over the whole frame to stop banding.
  - Easing on the gentlest library curves (a `sine` breath: `curve.house`) for the drift of the blobs and the lens; nothing fast; text enters with opacity + 8 px rise only.
  - Hero beat: a liquid-glass lens with true refraction and chromatic dispersion on its rim glides across and magnifies what lies behind.
- **Route**: WebGL aurora mesh-gradient shader + glass refraction (SDF lens, chromatic dispersion) + DOM/CSS backdrop-filter cards.
- **Sound**: ambient cinematic pad, soft shimmer, very subtle UI ticks.

## 12. 综艺花字 Variety Show Kinetic Captions (Hanazi)
**12 Hanazi** · tone: playful, comic · medium: type over footage (DOM/SVG captions)
- **Used for**: emotional decorative captions from TV variety post-production, now the stock packaging of vlogs, pet videos, interviews and comedy remixes (CapCut ships many templates).
- **Signatures**: multi-stroke rounded/heavy type, saturated clashing colours + white edge + drop shadow, elastic pop entrances, appearance tied to a sound hit, hand-drawn symbols (burst frames, sweat drops, sparkles)
- **Techniques**:
  - Three-layer type: fill (gradient allowed) + thick white stroke + coloured outer stroke or drop shadow (stacked CSS `text-shadow` or SVG stroke).
  - Pop: scale 0 → 1.15 → 1.0 in about 8 frames, or per-character bounce staggered by 2 frames, with a slight tilt.
  - Match the emotion: snark = tilted handwriting, surprise = radial burst frame with speed lines, awkwardness = sweat drop.
  - Time each caption to the joke or SFX, landing 2–3 frames after the voice or visual moment.
  - Captions held on screen keep a gentle wiggle so they stay alive.
  - The base layer should feel like footage: slow Ken Burns, handheld shake, snap punch-ins on the moments.
- **Route**: DOM/SVG multi-layer text-stroke caption components + spring pops + SVG burst/sweat/sparkle decorations over a footage layer; the source was vertical 1080×1920.
- **Sound**: bouncy variety bed (pizzicato, bass, claps) + boing, pop, ding, slide whistle, record scratch.

## 13. 粗描边贴纸人科普 MG（回形针/林超风格） Bold-outline Sticker Explainer MG
**13 Sticker Explainer** · tone: technical, serious, explainer · medium: photo stickers and charts on one big canvas (HTML + SVG)
- **Used for**: hardcore science, finance-knowledge and corporate films; made famous by 回形针 PaperClip, extended by 林超-style creators with handwritten boards and formula cards.
- **Signatures**: photos turned into stickers (thick white edge), calm blue-grey / off-white ground, flat icons + exact data charts, big-canvas camera pans and zooms, dense beat-by-beat narration
- **Techniques**:
  - Cut out every photo and give it the same 8–12 px white outline (plus a soft shadow) so sources of different quality match.
  - One super-wide canvas (e.g. 6000×3000 px); a camera layer pans and zooms on long eases, linking many info points in one continuous move.
  - Chart motion: bars grow, numbers count up, paths draw on; charts are exact (bars to scale, numbers consistent).
  - Each narration line brings in a new visual element; the pace is fast.
  - Restrained 2–3 colours + one accent (e.g. #E9EEF2 + slate + #FF5A36), even-weight sans, strict alignment, to keep it serious.
- **Route**: one huge HTML canvas with a camera transform (long eases), SVG charts, photo stickers with a 10 px white outline.
- **Sound**: clean tech-explainer bed, UI clicks, ticking under count-ups, soft whoosh on camera moves.

## 14. 像素风 Pixel Art / 8-bit
**14 Pixel** · ★ fast-cut · tone: retro, playful, game · medium: pixels (low-res Canvas, nearest-neighbour)
- **Used for**: game-channel videos (Minecraft, Terraria, indie games), 8-bit music videos, nostalgic brand marketing.
- **Signatures**: big hard-edged pixels, limited palette (8–32 colours), 8–12 fps sprite animation, dithered gradients, CRT scanline filter
- **Techniques**:
  - Sprite sheets (Aseprite) as frame loops: walk/run 6–8 frames, breathing 2–4 frames; a 16×16–24×24 hero at ~10–12 fps.
  - Nearest-neighbour scaling only (CSS `image-rendering: pixelated`), e.g. 320×180 internal scaled ×6; no anti-aliased edges.
  - Stepped timing with `steps()`, never smooth easing on sprites; integer pixel positions.
  - Parallax scrolling: 3–4 layers (far, mid, near) at different speeds, always moving by whole pixels.
  - Dithered gradients for skies; optional CRT pass (scanlines + barrel distortion + phosphor glow) that must not smear the pixels.
- **Route**: Canvas at 320×180 internal resolution, integer-scaled ×6 with nearest-neighbour; sprites written as pixel arrays in code; PICO-8-like 16–32-colour palette.
- **Sound**: chiptune (pulse lead, triangle bass, noise drums) + jump/coin/chest SFX.

## 15. 赛博朋克 HUD / FUI Cyberpunk HUD / FUI (Fictional UI)
**15 HUD** · ★ fast-cut · tone: data/HUD, technical, sci-fi, game · medium: neon wireframe UI (SVG / Canvas 2D)
- **Used for**: the default "tech" skin for gadget reviews, game edits (Cyberpunk 2077, EVA remixes), military/space science and AI product demos; imitates sci-fi film and game heads-up displays.
- **Signatures**: cyan/orange neon wireframes, lock-on brackets and crosshairs, radar and ring scan loops, monospace data streams and typewriter text, hex grids with glow
- **Techniques**:
  - Wireframes draw on with SVG `stroke-dasharray`/`stroke-dashoffset`, unfolding layer by layer in staggered order.
  - Radar: a `conic-gradient` sweep sector rotating on a loop + blinking target blips; concentric rings with ticks.
  - Number roll: random digits flicker for 3–5 frames, then settle on the real value; typewriter lines with a blinking cursor.
  - Lock-on: four corner brackets shrink onto the target, scale 1.4 → 1.0, fast-out slow-in; then the state flips to the alert colour.
  - Unifying finish: global glow + slight chromatic aberration + scanline overlay; micro-glitches kept rare.
  - Palette: deep teal-black ground, cyan #00E5FF linework, orange/red #FF6A00 alert state.
- **Route**: SVG / Canvas 2D FUI layers; seeded deterministic data streams; glow and scanline post pass.
- **Sound**: darksynth pulse + HUD beeps, scan sweeps, a rising lock-on tone, an alarm on lock.
