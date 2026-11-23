/* lib/fonts.js — fonts from the house library (assets/fonts/) inside the page. Same result in a double-clicked
 * index.html, snap.mjs and render_fast.mjs, and every face is ready BEFORE any segment's init() runs, so text that
 * init() measures or bakes into a canvas already uses the real font.
 *
 * Don't hand-write <link> / @font-face for library fonts. Run (vision python):
 *   python -X utf8 scripts/fonts.py use <project> "UnifrakturMaguntia" "Ma Shan Zheng"
 * It copies the fonts into web/assets/fonts/ (CJK faces subset to the characters found in the project's files, WOFF2),
 * writes web/assets/fonts/fontpack.js (one T3.fonts.add({…, data: base64}) per face) and puts, right after engine.js:
 *   <script src="lib/fonts.js"></script>
 *   <script src="assets/fonts/fontpack.js"></script>
 * Copy changed afterwards? Run `fonts.py use <project>` again (no names = refresh): a subset only holds what it saw.
 *
 * In segments:
 *   CSS / T3.el():  fontFamily: T3.fonts.use('Ma Shan Zheng', 'serif')      → "'Ma Shan Zheng', serif"
 *   canvas:         ctx.font = `120px ${T3.fonts.use('UnifrakturMaguntia', 'serif')}`
 *   T3.fonts.missing(family, text, {weight, style}) → characters the face lacks (they would fall back silently)
 *   T3.fonts.credits()  → ['字体 Family：作者（licence）', …]  for the end credits
 *   T3.fonts.report()   → [{family, weight, style, status, alsoInstalledOnSystem, …}]  QA: every status must be 'loaded'
 *   T3.fonts.ready      → Promise, resolves when every face has loaded
 * Single-weight fonts below 600 (most display / CJK calligraphy faces): don't ask for bold, Chrome fakes it by smearing
 * strokes. A single face of 600+ (UnifrakturCook 700) is the bold already: any font-weight uses it unchanged.
 * Outline / hollow text (-webkit-text-stroke, ctx.strokeText): a variable font draws strokes over strokes, and an outline
 * shows those overlaps as seams inside the letters. Pack a static cut instead — it is instanced from the library's
 * variable font at that weight (other axes at their default) with the overlapping contours merged, no extra download:
 *   python -X utf8 scripts/fonts.py use <project> "Montserrat:900" --static
 * The page then has Montserrat at 900 only. To keep the variable Montserrat as well, give the cut its own name:
 *   python -X utf8 scripts/fonts.py use <project> "Montserrat:900" --static --alias "Montserrat Outline"
 *
 * Low level (fontpack.js uses it): T3.fonts.add({ family, data | url, weight, style, stretch, unicodeRange,
 *   featureSettings, name, author, license, credit, file })
 *   data = base64 → FontFace from bytes: loaded at once, any browser, file:// without flags.
 *   url  = 'assets/fonts/x.woff2' → loads async; T3.hold() makes the engine wait with init() and T3_READY (10 s at most).
 *          Local files only: an address on another host (https://…, //…, \\server\…) throws — house rule, no web fonts.
 *   Variable fonts: weight as a range, '100 900' (one number makes Chrome fake-bold the default instance);
 *   a wdth axis: stretch '75% 100%'.
 */
(function () {
  const T3 = window.T3;
  if (!T3) throw new Error('lib/fonts.js: load engine.js first');
  const recs = [], seen = new Map();
  const DESC = ['weight', 'style', 'stretch', 'unicodeRange', 'featureSettings', 'display'];
  const GENERIC = /^(serif|sans-serif|monospace|cursive|fantasy|system-ui|ui-\w+|math|emoji|fangsong)$/i;
  const q = (f) => `'${String(f).replace(/'/g, "\\'")}'`;
  const bytesOf = (b64) => (Uint8Array.fromBase64 ? Uint8Array.fromBase64(b64) : Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)));

  // Is `family` an installed system font? Then a failed load would still look right on THIS machine only
  // (Windows 11 ships Noto Sans SC / Noto Serif SC). Probed before the family's first face is added.
  function systemHas(family) {
    const c = Object.assign(document.createElement('canvas'), { width: 400, height: 60 }).getContext('2d', { willReadFrequently: true });
    const px = (f) => { c.clearRect(0, 0, 400, 60); c.font = `40px ${f}`; c.fillText('Hg字永9', 4, 46); return c.getImageData(0, 0, 400, 60).data; };
    const a = px(`${q(family)}, monospace`), b = px('monospace');
    for (let i = 3; i < a.length; i += 4) if (a[i] !== b[i]) return true;
    return false;
  }
  // the registered family first, the library name second: with "Montserrat" (variable) and a --static cut packed as
  // "Montserrat Outline", use('Montserrat') must not land on the cut because its library name is Montserrat too
  const find = (f) => recs.find((r) => r.family === f) || recs.find((r) => r.name === f);
  // House rule: no web fonts. Judged on the resolved address, so //host, https:host and \\host (a network share on
  // Windows) are caught as well; the page's own http origin (a local preview server) is allowed.
  function webFont(url) {
    let u;
    try { u = new URL(String(url).trim(), document.baseURI); } catch (e) { return false; }
    return (u.protocol === 'file:' && !!u.host) || (/^(https?|ftp|wss?):$/.test(u.protocol) && u.origin !== location.origin);
  }

  function add(o) {
    if (!o || !o.family || (o.data == null && o.url == null && o.buffer == null)) throw new Error('T3.fonts.add: need family and data | url');
    if (o.url != null && webFont(o.url))
      throw new Error(`T3.fonts.add: '${o.family}' url ${o.url} is a web font — refused (house rule: library fonts only). Run: python -X utf8 scripts/fonts.py use <project> "${o.family}"`);
    const desc = {};
    for (const k of DESC) if (o[k] != null) desc[k] = String(o[k]);
    const prev = recs.find((r) => r.family === o.family);
    const system = prev ? prev.system : systemHas(o.family);
    const src = o.data != null ? bytesOf(o.data) : o.buffer != null ? o.buffer : `url(${JSON.stringify(o.url)})`;
    const t0 = performance.now();
    const face = new FontFace(o.family, src, desc);
    document.fonts.add(face);
    const r = { family: o.family, name: o.name || o.family, weight: desc.weight || '400', style: desc.style || 'normal',
      file: o.file || o.url || '(data)', author: o.author, license: o.license, credit: o.credit, face, system,
      sync: face.status === 'loaded', ms: 0 };
    r.promise = face.load().then(
      () => { r.ms = +(performance.now() - t0).toFixed(1); },
      (e) => console.error(`T3.fonts: '${o.family}' ${r.weight} ${r.style} failed to load (${r.file}): ${(e && e.message) || e}`));
    if (!r.sync) {
      if (T3.hold) T3.hold(r.promise);
      else console.error(`T3.fonts: '${o.family}' loads async (url) but this engine.js has no T3.hold — frames may show the fallback font. Use fonts.py use (data) or the current engine.js`);
    }
    recs.push(r);
    return face;
  }

  // Per character: draw it with the face + fallback A, then with the face + fallback B. A glyph the face really has
  // never changes; a missing one shows the two different fallbacks.
  function missing(family, text, opt = {}) {
    const fam = (find(family) || { family }).family;
    const size = opt.size || 48, w = size * 2, h = size * 2, weight = opt.weight || 400, style = opt.style || 'normal';
    const c = Object.assign(document.createElement('canvas'), { width: w, height: h }).getContext('2d', { willReadFrequently: true });
    const draw = (ch, fb) => { c.clearRect(0, 0, w, h); c.font = `${style} ${weight} ${size}px ${q(fam)}, ${fb}`; c.fillText(ch, size / 4, size * 1.3); return c.getImageData(0, 0, w, h).data; };
    const out = [];
    for (const ch of new Set(String(text))) {
      if (!ch.trim()) continue;
      const a = draw(ch, "SimSun, 'Courier New'"), b = draw(ch, "'Microsoft YaHei', Impact");
      for (let i = 3; i < a.length; i += 4) if (a[i] !== b[i]) { out.push(ch); break; }
    }
    return out;
  }

  // CSS / canvas font-family string. A name that is neither loaded here nor installed is a typo or a font that was
  // never packed: say so once (snap.mjs / render_fast.mjs print it under PAGE ERRORS) instead of falling back silently.
  function use(family, fallback = 'sans-serif') {
    const r = find(family);
    if (!r && !GENERIC.test(family) && !seen.has(family)) {
      seen.set(family, true);
      if (!systemHas(family)) console.error(`T3.fonts.use: '${family}' is not loaded — run: python -X utf8 scripts/fonts.py use <project> "${family}"`);
    }
    return `${q(r ? r.family : family)}, ${fallback}`;
  }

  T3.fonts = {
    add,
    use,
    missing,
    load(list) { return Promise.all(list.map(add).map((f) => f.loaded.catch(() => {}))); },
    get ready() { return Promise.all(recs.map((r) => r.promise)).then(() => document.fonts.ready); },
    credits: () => [...new Map(recs.map((r) => [r.name, r.credit || `${r.name} — ${r.author || '?'} · ${r.license || '?'}`])).values()],
    report: () => recs.map(({ family, name, weight, style, file, sync, ms, face, system }) =>
      ({ family, name, weight, style, file, sync, ms, status: face.status, alsoInstalledOnSystem: system })),
  };
})();
