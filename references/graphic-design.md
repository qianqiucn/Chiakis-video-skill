# Graphic design — titles, type, colour, frame layering, helpers
Sections: §1 title and logo builds · §2 title treatments · §3 colour per entry · §4 code-native looks · §5 frame layering · §6 the tagline card · §7 our helpers. Editing and motion (rhythm, cuts, hand-offs, motion curves, her 2D motion) are in `style-grammar.md`, numbered on its own.

Read before designing any type, title, logo moment, layering set or tagline. Measured on the same reference as `style-grammar.md` (editing and motion); house-style.md wins where they differ (its §2 for content, §5 for legibility, §6 for the effects budget).

## 1. Title and logo builds (measured)
The frame counts are the reference's visible fast part; ours lands each move on its curve with a settle (style-grammar §6b).
- Slam: the word scales 1.6 → 1, reaching size in 3–4 f on a snap curve and settling by ≈ 12 f, with bloom and a 1–2-f RGB split; sub-words follow every 3–6 f (Google → GEMINI → outlined "4" draws on → ARGON → glitched ANTIGRAVITY).
- Tumbling letters: each letter a 3D stone block flipping in with motion blur, 3–5 f each, staggered 2–3 f, then a ~7-f hold ("CLAUDE": marble serif ~23 % of frame height, 12–15 px extrusion lit warm).
- Logo assembly (24 f): thin grey outline → solid centre → the 12 rays fill one by one (~9 f) → halftone + ghost wordmark → one RGB-split glitch frame → a dark card wipes down in 3 f → a small italic product name fades in; ~29-f hold.
- Titles often stay on across a flash cut and fade ~1 s later. *Ours*: one title moment (e.g. `T3.stencil`), official names returning in other registers (house-style §2; as type: §5 layer 3(b), 3(d)), the official logo (house-style §2) and the name lettering on the wordmark's skeleton (§2); the logo card is the mark alone, no wordmark (emblem stand-up, §7).

## 2. Title treatments: material × construction × effect × idea
- **Type performs; it is never a caption.** Every type moment does something in its shot on the beat: it builds,
  collides, is lit, pushed, occluded or carried by the picture's motion, and it ranks by size, colour and opacity (one
  lead colour, the rest stepped down). Plain system bold laid flat over a picture, one colour for every line, an
  English line on a solid bar, or a guide line left in the render reads as a slide deck (avoid slide-deck habits).
- Never "stock font + glow" (a glow is one option, never the default; each type moment gets its own treatment: house-style §5); pick one of each, tied to her. The title owns its shot and spans at least about a third of the frame width. Imagination comes before the list below.
- Effect, on top: chromatic split, heat haze, a light sweep through the letters, footage inside the letters (`background-clip:text` / mask), dissolve into particles, scanline jitter, ink bleed, frost, liquid fill, shatter; or invent one. Moderate: the effects budget (house-style §6) still counts.
- Material: stone (noise fill + bevel highlight), brushed metal (stripes + specular sweep), glass (blurred background clipped to the text + rim), neon tube (double stroke + flicker), ink (noisy edge, bleed), paper cut (offset layers + shadow), LED dots, point cloud, circuit traces, holographic (hue shift + scanlines).
- Construction: assembles from particles; carved by a sweeping light; extruded (10–30 stacked copies); decoded glyph by glyph; revealed by a mask; split and slid; ignited letter by letter; slammed with a shake.
- Idea: open source → letters from public code glyphs; reasoning → ghost drafts flicker before the final word; literature → written by a quill stroke.
- Layout, decided first on the style frames: where the type sits in the frame and against her.
  - A grid and margins; a clear size ladder (reference orbit words: lead : satellite : label : sub-label ≈ 4 : 2.7 : 1 : 0.5); an opacity ladder in which the biggest word may be the faintest; room left empty.
  - Its depth, one of four:
    - behind her: a masthead tucked behind her head (the shot, the type, then the same shot again through her mask sequence, `T3.sequence(…, { mask })` with the shot's frame index and transform); usually once per intro;
    - in the scene: lit, in perspective, occluded (composited into a scene's perspective via CSS 3D `multiplane.js` or Canvas 2D skew/mask);
    - on the screen layer beside her;
    - two tapes framing her, one behind and one in front.
  - Screen-layer type stays put while the picture pushes in; scene type moves with the scene.
- **Lyrics** (a PV remake, SKILL.md modes): every sung line carries motion of its own, chosen for what that line says
  (its own material, construction and effect from the lists above), never one caption style run through the song. It
  enters with the line as sung, and a translation rides with it as the secondary line. Overlay type leaves with the
  line; type built into the set (engraved on a plate, lit on a pillar, carved in an object) stays to the end of its
  shot once lit, because it has become part of the place: wiping it at the line's end reads as the set changing under
  a held camera. Two proven print/PV accents (measured on `ref_bakamitai`): **three-state arrival** (blurred accent
  fill → 1-f blank gap → hollow accent outline → solid white with hard accent drop shadow and `±4 px` cyan fringe),
  and **grey pre-hit** (scattered display type flashes in cool desaturated grey for 2–3 f before snapping to saturated
  colour on the downbeat).
- Brand marks: house-style §2 (official marks as they are, the idea in their material, construction and entrance).
- **The model name's lettering follows the official wordmark.** Its letters keep the wordmark's skeleton: proportions,
  stroke contrast, letter shapes. Only material, texture and construction change (carved, woven, lit, cut by the
  medium), because the viewer reads the brand by those letter shapes. Start from the official wordmark file or the
  library face closest to its skeleton (matching the subject's typographic voice), heavy enough to carry the title: a thin,
  wide-tracked outline on a bevelled glass plate reads as dated sci-fi HUD. A display face that distorts a letter (a
  «d» reading as «ð») fails.
- Fonts: open-source faces from the library (`assets/fonts/`: the curated shelf in `catalog.md`, all of Google Fonts in `catalog_all.md` and `specimen\all\`; `fonts.py search --local`), chosen for her world.
  - The face is part of the idea: a gothic idol → a Textura blackletter; a literary world → a Didone or an old-style serif; a terminal → a mono.
  - Per intro one display face, from a style group no other intro uses, plus a label face and a Chinese face when needed.
  - Vary tracking, slant, inline stroke, clip-path cut-outs, `background-clip:text` textures.
  - Stroke or outline only static faces (variable ones show their inner overlap lines): `fonts.py use … "Family:900" --static` cuts one from a variable font.
  - Subset CJK families by pinning needed weights (`"M PLUS Rounded 1c:900"`, `"Noto Sans JP:900"`) with `--text` (or default project subsetting) rather than `--full`: full multi-weight CJK WOFF2 bundles bloat `fontpack.js` past 12 MB and stall packing/boot, while pinned subsets stay near ~1.3 MB with zero missing glyphs (quality-bar.md).
  - Large translucent type in a high-contrast serif takes a static cut at a small optical size: at display sizes the variable face picks its large optical size, whose hairlines vanish once translucent (V8's ghost word read as two slashes until cut at opsz 6). Judge it snapped at its film opacity.
  - Measure a text's width with exactly the font settings it is drawn with: set the font shorthand first, then the figure style and tracking, since the shorthand resets them (on V8's day «1M» ran into «tokens» in the footnote band of v1–v5, until v6).

## 3. Colour per act / theme
Choose one primary hue family per project or act — paired with a clean dark or light ground and one crisp accent — and carry it consistently across type, borders, glows, and overlays. Shift palette deliberately across major musical transitions (e.g. cool desaturated verse → warm high-contrast chorus). Never scatter five unrelated neon accents in a single shot.

## 4. Code-native looks
- ASCII: black, monospace cells ≈ 12 × 20 px (font ≈ 20 px) with a soft glow; ASCII punctuation only (big words built from glyph blocks); glyphs re-picked every frame while shapes stay (shimmer).
  - Colours: mint #9FE0CC / #60A080 early, white #F8F8F8 with #60D0B8 accents later.
  - Colour ASCII of an image: per-cell colours precomputed with ffmpeg (scale to the grid, rawvideo rgb24) → JS array; boost saturation (glow layer `saturate(3.5)`) or it reads grey.
- HUD text: the reference set Bahnschrift, YaHei and Consolas; the locked crystal template's faces are Barlow Condensed, Noto Sans SC and Bodoni Moda italic (scene-template «What it looks like»). An intro takes the nearest open-source library faces (a DIN-style sans, a Chinese sans, a mono) via `fonts.py search --local`. Tiny wide-tracked English sub-labels under Chinese labels.
- Glitch: RGB split = 2 copies offset ±8–14 px, screen blend, 1–2 f; posterise via canvas or an SVG filter; jumping translucent bars from `T3.rand(frame, i)`.

## 5. Frame layering — what makes a frame look edited (5-layer editorial depth)
This section is the home of the layering recipe: four layers, each moving on its own (1–4), plus seasoning on the hits (5–6).
- Learn the grammar (counts as calibration, opacities, placement, timing), never the content; how often: house-style §6.
- The set is a fixed goal, re-skinned by the form (house-style §0).
  - Examples, not recipes: in a loom the ghost word is woven into the ground cloth and the label is a selvedge mark; on lenticular cards the orbit words are printed on cards and the polygons are card edges catching light; in a terminal they are dim scrollback and box-drawing strokes.

1. Moving base: the picture moving in depth (`lib/multiplane.js` / `lib/depth3d.js`), or in an action shot held still the scene with its action (house-style §4).
2. **Translucent materials** at 15–45 %, each drifting or turning slowly at its own depth with the camera (`lib/multiplane.js` / `lib/depth3d.js`),
   behind her or at the edges:
   - objects from the intro's own world, chosen by its theme (the reference: clockwork gears and rings; a loom:
     spools and warp beams; a library: an orrery or star chart; a terminal: circuit wireframes);
   - in a style that fits the form and changes from intro to intro: glowing wire, frosted glass, holographic film,
     brushed metal, lit silk thread, ink wash, cut paper, a point cloud, toon line…; the approved samples
     `texture_pass_v1` (wire on black) and `texture_layers_3shots` (holographic film, frosted glass, lit silk) set the
     restraint, not the look;
   - glass and film light up only near grazing angles (a facing-ratio ramp) with a hairline rim; a face lit flat reads
     as a sticker pasted on the shot;
   - real 3D (an asset-library model rendered by the 3D engineer on black, defocused, composited by the frame's key)
     or blended from `assets/textures/` (`grain/`, `dust/`, `paper/`, `washi/`);
   - keep large graphic ornaments partially framed behind the subject at one side rather than boxing the subject in;
   - also big thin rings and arcs half-hidden in the dark, bokeh, soft rays, dust, a full-width hairline.
   - Rings and hairlines may be code.
   - In a high-key white world, screen-blended footage and 3D renders vanish: multiply them with a tint one step darker (≈ #7E72B8 in a lavender world), or screen white particles over a faint violet shadow layer. A 3D texture layer goes in as masks (body R, edges G), multiplied, the white behind the body softened like frosted glass (`texture_layers_3shots`).
3. Art typography, (a)–(d) (px at 1080p; legibility: house-style §5):
   - (a) the kinetic title stack = the one title moment, one word per beat. The stack is the reference's construction; an intro's title moment may build another way (§2). Its parts:
     - a small letter-spaced brand word (≥ 65 px, the read-text floor, house-style §5);
     - one huge heavy word (~300 px; material, construction and effect from §2: the reference used white, a soft glow and a dot screen);
     - sub-words from her lore (~150 / ≥ 65 px, one with an RGB-split ghost);
     - a giant outlined numeral in a thin coloured stroke behind (the rank or a number from her lore, never a model version; stroke font: §2).
   - (b) orbit words and her label, words from her lore; the model name, a version or the vendor's agent may be among them (house-style §2), never set up as a second title. House-style §5's size floors hold for both: enlarge the whole set together, never just the label.
     - Orbit: a lead word and 2–3 satellites, one per quadrant at staggered heights, hugging the outer edge of her silhouette (never her face or hands).
       - Sizes and opacities: the lead ≈ 10 % H yet the faintest (40–50 %), satellites ≈ 6–7 % H at 40–65 %; orbit words are
         texture, not read text (house-style §5), so nothing the viewer must read rides on them.
       - Look: a pale tint of the primary palette with a faint dark edge, not harsh pure white; matched to the act's typeface (§2).
       - Motion: one per beat, each a 2–3-f fade with de-blur, no scale, no bounce.
     - Label: a ◆ 10–30 px outside her silhouette, a 1–2 px hairline from it out of frame toward the empty side, a heavy name above the line and a thin sub-label below at about half its size (reference: fat Didone caps over a DIN-like light).
       - Motion: the name wipes in with blur over 3 f, the line grows to the edge in ~6 f, all of it leaves on a cut; the next shot may reuse it on the other side.
       - The hairline may cross in front of her; letters may not.
   - (c) punctuation shots. The reference's two:
     - a bright product-UI frame (~6 f, a brightness slap between dark shots). It is the real product: its faces and
       chrome (title bar, sidebar, input), plausible content at real density, built from the real interface (a public
       screenshot as reference or as the screen texture), no personal or account data; a logo and slogan in a box
       reads fake;
     - a tagline card on black (thin sans, the key word in the brand gradient) that collapses into the mark (studied in §6).

     Other pure-type cards:
     - a one-line verdict on black (heavy Chinese, the answer in the accent colour, no data: house-style §2) whose halo opens as an iris into the next shot;
     - an end slate: the mark over the blurred key image, flashing white into the panel;
     - a poster split: half a halftone white field holding the mark and a dark vertical card (type inverts where it crosses the card's edge, a small italic with a hand-drawn underline), the other half her profile looking at it.
   - (d) texture type, cheap and quiet: a giant ghost word cropped by the frame edge (≈ 25–30 % H, only 5–8 % off the background, or 25 % grey, or outline or stripes only), repeated micro-type on tapes, a vertical line of micro-text at the frame edge; behind everything and away from her; it counts as a material (layer 2).
   - (e) per-glyph kinetic typography (fast-cut vocal & lyric PVs): never animate multi-character lyrics as uniform flat phrase blocks on level stripes — and **never lock sung lyric entry frames from drum trackers alone** (`beats.py` / `onsets.py` track percussion, not human voice). Run `scripts/vocal_spec.py` before Gate A, listen to each 3–5 s micro-WAV directly via multimodal `read_file` alongside its 300 Hz–4 kHz spectrogram, and lock every lyric syllable to the real sung onset (±2 f tolerance). Build glyph-level life across four layers:
     1. *3-state hollow-preview relay*: stagger each character `2–3 f` (`hollowLead ≈ 2.5 f`), flashing a `≈ 2.1×` stroke-only outline toward its slot before silky Bezier squash-and-stretch fill (`sy 1.4 → 1.0`, `sx 0.82 → 1.0`, optional bottom `mirrorEcho`) and continuous `±2–3 px` micro-breath;
     2. *kanji-giant / kana-mini sculpture*: split content Kanji (`1.2×–1.5×`) from particles/Kana (`0.68×–0.85×`) with bespoke `(x, y, rot)` around the hero or alternating baseline wave-arcs (`waveY`), wide enough in tracking (`≥ 24 px`) so tilted strokes never collide;
     3. *depth-sandwich occlusion*: place display words between the translucent background wash/petals (tinted glazing petals at ~30 % alpha when overlapping text) and opaque foreground wireframe hands or character edges so typography sits inside real Z-space;
     4. *3D letter Z-scatter*: split climax English lines (`I HATE YOU`) into individual perspective-scaled letters exploding radially toward the lens, led by a 3-f high-contrast B&W negative shockwave before revealing the colour hero;
     5. *Three.js Stylized 3D Typography (`3d.md` §5e)*: when the film selects **全能双 3D 旗舰** or **Three.js 风格化 3D**, elevate hero titles, chorus hooks, and bridges with real vector 3D geometry — pre-bake CJK/JP/Latin glyphs via `scripts/fonts.py glyph3d`, then compose **`T3.three.extrudeText`** (`type.3d-extrude`, `flat`/`toon`+ink/`glass`/`wire` styles), **`T3.three.textRing`** (`type.3d-ring`, 360° lyric ribbon Z-sandwiched behind and across a character cutout), and **`T3.three.textCorridor`** (`type.3d-corridor`, flying 3D lyric poster tunnel) natively inside the 2D `<canvas>` without plastic PBR gloss.
4. Polygon accents (`T3.accents`, lib/accents.js): 4–6 long thin bars at 30–60°, 3–4 px light outline with glow, 15–25 % white fill, crossing the frame around her (off her face), over the shot dimmed to ~40 % under a flat brand-tint layer; each occurrence 1–2 f.
5. Impact frames 冲击帧 (`T3.impact`): 1–2 f of a stark two-tone image (black on white, inverted, brand duotone), often with the polygons on top.
6. Mood inserts: 2–6-f shots that carry only a feeling (a dutch-angle crop of a dark ornate column in silhouette between two glowing panels in the brand tint); no character, no information; their own generated images; 1–3 on fast runs.

Ours, e.g. for Claude: serif italics instead of blackletter; orrery rings, star charts, manuscript lines as materials; shards of the 12-ray emblem as polygons; a Claude Code terminal as the UI frame; her real tagline instead of "Welcome to the … era".

## 6. The tagline / hero statement card
A single crisp statement line on a clean dark or light ground can anchor a pre-drop beat (24–36 f):
- Plain words in off-white (`#E8E8E8`) or ink (`#14161A`); the hero keyword carries a subtle left-to-right palette gradient.
- Per-character de-blur & opacity reveal: each glyph starts `blur(10–14px)` + `opacity: 0` and sharpens cleanly over 5–7 f on a tight 1–1.5 f stagger (`T3.mv.chars` or Canvas per-glyph pass), while the line holds a gentle `move.settle` scale creep (`0.5 %`).
- Keep generous margin (≥ 15 % horizontal breathing room) and zero competing HUD clutter on the tagline frame.

## 7. Our helpers (`lib/choreo.js`, `lib/emblem3d.js`; signatures in each file's header)
| helper | frames | what | typical use |
|---|---|---|---|
| `T3.implode` | 2 out + 4–7 in | letters jump 40 px outward, then fall into a point (far letters start up to 2 f later): the tagline's letters into its full stop; add a 30 % ghost at f − 1 on the fast last frames | a big gesture, usually once |
| `T3.emblem3d` + `T3.standUp` | 5–6 (`beat` = f0 + 6, the default) | the full stop grows into a layered emblem lying back (3–5 planes: ring −70 · dots −30 · mark 0 · core +30 · ticks +60 px per 1000 px), stands up over the last 5 f, upright on the beat, then sways slowly — the logo card; implode + grow ≈ 10–12 f, then the hand-off (a bloom only when it is a flash, house-style §6) | a mark or logo moment, usually once |
| `T3.stencil` | — | the name cut out of a dark plate (a heavy library face passed as `font`; the Segoe UI default is only a fallback; 86 % black, thin white rim); the moving 3D picture shows through the letters; animate `length` (textLength) to spread the spacing | a name or title word over a moving picture |
| `T3.flick` | 4–6 | power-on flicker from a frame table (`'tube'` 6 f, `'soft'` 5 f, `'snap'` 4 f) for a code element's first appearance | a handful of first appearances |
| `T3.preglow` | lead + 4 out | soft light (opacity of a radial-gradient div) rises where an element will appear, peaks on its first frame, dies over 4 f | entrances that deserve weight |
| `T3.decay` | half-life per channel | landing v0 · 2^(−Δf / h), no bounce — e.g. x half-life 1.5 f, scale 3 f | snap-and-settle landings |
| `T3.knockHalo` | — | CSS filter: a dark soft halo only outside translucent glyphs (blur ≈ 7 % of the font size); the glyph at 50 % so the picture shows through | translucent words over busy art |
Typical uses, not slots: a few per intro, wherever they serve the moment (house-style §6).
Type and graphics move through the motion library: arrivals, exits, settles and staggers from `lib/motion` (`T3.mv`,
`T3.EZ`), and every helper above by its id (motion-library.md groups `type`, `move`, `fx`), written into the design
motion sheet before the code.

## 8. Per-Shot Materialization, Print Plates & Tactile Coat (`lib/look_fx.js`)
Texture and print craft belong **inside each shot's physical material**, not slapped uniformly as a grey multiply glass sheet over the entire film:
- **Per-shot tactile coat (`T3.look.coat(ctx, f, { paper, grain, dust, scanline, faceGuard })`, preferred default)**: dial texture shot-by-shot — crisp paper fiber (`paperAlpha: 0.25–0.32`) on print/editorial shots, **zero paper** on deep black vinyl/night/CRT shots (so dark ink stays true black and saturation never washes out), and subtle `faceGuard` radial attenuation over close-up character faces. Reserve a standalone full-film `z = 45` `film_texture.js` layer **only** when every single shot shares an identical paper/35mm medium.
- **Transform raw line-art/illustrations into print materials (`T3.look.bakePrint` + `T3.look.drawPrint`, `fx.print-plate`)**: avoid pasting raw grey line art verbatim for 3 minutes. Bake plates once and alternate cohesive print treatments (`screen` 60° line screen, `dots` duotone halftone, `neg` high-contrast negative on ink, `sil` flat two-plate silhouette, `two` misregistered multiply overprint) paired with **OKLCH ground-walks (`T3.look.okMix`, `trans.ground-walk`)** starting 2–4 f ahead of cuts.
- **Pre-stretch raw paper scans & preserve stepped cadence**: `Paper001_4K_color.jpg` spans only `[236..252]` luma and vanishes under naive `multiply`; run `scripts/prep_texture.py --mode paper` first (`assets/textures/README.md`), step tile offsets with `T3.twos` inside `Posterize Time` passages, and render textured films with `render_fast.mjs --grain`.
