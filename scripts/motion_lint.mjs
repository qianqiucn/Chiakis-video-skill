// motion_lint.mjs — the motion check: a page's segments against the motion library (references/motion-library.md).
// Node only (D:/Node/node.exe or node on PATH), so it runs in Codex's sandbox as well. The static scan opens no browser
// (< 1 s); --runtime and --curves open the page through scripts/_cdp.mjs, so run those through scripts/run_queue.py web.
//
// Usage:
//   node motion_lint.mjs <index.html> [--segments a.js,b.js] [--strict] [--runtime] [--curves] [--from s --to s]
//                        [--json out.json] [--out dir]
//   node motion_lint.mjs --check-library            the index against the code (ids, LIB/EXISTING calls, module headers)
//   node motion_lint.mjs --hook                     PostToolUse hook: stdin JSON, prints hookSpecificOutput, always exit 0
//   any mode: --skill <root> (another skill folder) · --library <md> (another index) · --legacy-list <json>
//   --segments  only these files (a bare name is looked up in <page>/segments/, then beside the page; a relative path
//               with a folder, such as segments/x.js, from the page's folder first, then the current one); default: the
//               segments the page loads (script tags under segments/, comments stripped). A file named here that does
//               not exist is a FAIL. The page's other segments are not checked, and --curves leaves their probes out.
//   --runtime   R1 on the opened page;  --curves  R1 + R3 (implies --runtime);  --from/--to (s) keep the probes that
//               overlap that range;  --out  where lint.txt / curves.svg / curves.json go (default <page dir>/tools/out/motion);
//               lint the delivered films' originals with --out somewhere else, never beside them
//
// Mode (motion-library «Setup»): strict by default. A segment is legacy (all its findings NOTE) when the page's folder is
// under a prefix in scripts/motion_legacy.json (as written, or with junctions resolved on both sides: legacyEntry) AND
// the segment file is not newer than that entry's cutoff (`until`, or the end of `date` in local time); or when the page
// sets T3_CONFIG.motionLegacy = '<reason>' (printed as LEGACY by opt-out).
// --strict forces strict. Page-level checks (S1, S9, R1) are FAIL when the page holds at least one strict, non-exempt
// segment (a new segment in an old film needs the library loaded too), NOTE otherwise: an all-legacy page, and a page
// whose segments are all exempt. R1/R3 run
// only on a page with a strict segment.
// Exempt (not checked): files explicitly marked exempt (none by default in Chiaki's-video-skill).
//
// Checks                                                                                        strict          legacy
//   S1 index.html loads gsap, CustomEase, gsap-bridge and lib/motion/ez.js before the first segment FAIL          NOTE
//   S9 lib/motion complete: every module in the template's assets/template/lib/motion/ (listed at run
//      time, so a module added to the template later is asked for too) is in the project's folder
//      (where the page's lib/motion/ez.js tag resolves, else <page>/lib/motion), loaded by the page FAIL          NOTE
//      (a module loaded from another lib/motion folder counts as there); the S9 FAIL names the copy
//      command and the missing tags in the template's order
//      a copy whose text differs from the template's (older, or edited in the project; line ends, BOM
//      and trailing whitespace ignored), or a module tag (not ez.js: S1) after the first checked
//      segment                                                                                       WARN          NOTE
//      (on a page with no strict segment only once the project has begun on the library: a lib/motion/
//      tag, or the folder; an archived film from before it gets S1's note alone)
//   S2 `// motion-sheet:` and `// motion:` within the first 15 lines                                FAIL          NOTE
//   S3 every cited id resolves: library id, «shot-recipes: name», «mg-styles: N Name»; unknown or retired FAIL,
//      pending NOTE (needs the client's word), signature NOTE (helper only), PENDING-LIB NOTE       FAIL/NOTE     NOTE
//   S4 a cited LIB/EXISTING entry's call appears in the file, in full or through a local name
//      (const EZ = T3.EZ, mv = T3.mv; const { arrive } = T3.mv); comments and strings never count    NOTE          NOTE
//      and the other way: a move entry's T3 call made here whose id the header leaves out (curve.*
//      and the entries whose call is a T3.EZ curve are not asked for; 2026-11-21: 6 of the 50 headed
//      segment files, all TOP15's Claude intro and its backups, all real)                            NOTE          —
//   S5 hand-written eases: local ease definitions counted by calls (unused ones listed for deletion),
//      inline smoothsteps, project-local GSAP tables (use T3.EZ)                                     NOTE          NOTE
//   S6 explicit linear: T3.ease.linear, ease 'none'/'linear', T3.tab with >= 3 keys on a motion prop NOTE          NOTE
//   S7 per-frame tables: a numeric array / numeric-keyed object subscripted on the spot by a frame
//      expression (>= 3 values: a three-key ramp written as a table is one), or a named one (>= 4)   NOTE          NOTE
//   S8 the sheet named by `// motion-sheet:` exists (from the project root) and is not empty
//      (`inline` = a /* motion sheet */ block with the 7 columns); its ids include the header's      FAIL/NOTE     —
//   S10 a hit built by hand: a scale punch settling to 1 from >= 1.1 (a − (a−1)·k, 1 + b·(1 − k),
//      lerp(a, 1, k), a [a, …, 1][k] table) that drives a scale (scale( / setTransform( / scale:, on
//      its line or through the name it is assigned to), in the same function as a full-frame light
//      fill (a light fillStyle with fillRect(0, 0, W, H), or the .style of a full-frame light
//      overlay); the whole file is cleared by citing type.slam, fx.shake or fx.impact, or by calling
//      T3.shake or a shake it does not define itself: look the hit up first                         NOTE          —
//      (tuned 2026-11-21 on 256 segment files of the projects and the skill's examples: 5 files, two
//      pieces of code: the TOP15 hits built from expoOut alone, in two backups, and three copies of
//      the old template sample, whose hand-built slam and flash only share a function. Not seen: a
//      hit marked only by a cut, a flash drawn in another function, a punch from a named constant
//      or through mix()/interpolate, a flash colour held in a variable, an overlay styled by cssText)
//   R1 runtime: gsap && CustomEase && T3.EZ && T3.gsapSeek                                         FAIL          —
//   R3 --curves: every probe sampled every 1/4 f → curves.svg + curves.json; an intro segment (strict, citing
//      ids) with no probe, or a probe that throws, FAILs; the shape metrics are NOTEs (unsigned)    FAIL/NOTE     —
//      (the static scan already notes a strict segment with fewer than 3 T3.motionProbe calls)
//   Pages: script tags with comments stripped; <base href> and file:/// sources are followed (V8's pages load another
//   project's segments); a segment is a script under segments/ (else any script outside lib/, assets/, panels/).
// Pragma `// motion-ok: <kind> <reason>` on the line or the line above exempts that line from S5–S7 (kinds: steps scan
// typewriter blink flick stepped measured hold); every pragma is listed in the report; one with no reason or an unknown
// kind exempts nothing.
// Levels: a FAIL fails qa; a WARN or a NOTE does not, and each is answered (quality-bar Gate B1). Output: <= 8 summary
// lines (FAILs, WARNs, then the notes by segment) + the full report (lint.txt). Exit: 0 no FAIL · 1 a FAIL · 2 usage or IO error
// (no page, ids cited while the index is missing, or the scan stopped on an internal error). --hook always exits 0.
//
// For the wiring (_cdp.mjs, qa.mjs): import { staticScan, segmentsOnScreen, runtimeState, lintRuntime, curveSheet,
// motionLine, summaryLines, reportText } from './motion_lint.mjs'. staticScan(page, opts) is synchronous, prints nothing,
// never throws (an internal error comes back as res.error with one NOTE) and takes well under a second (TOP15's
// 24-segment page: ~10 ms). lintRuntime(pg, res) and curveSheet(pg, res, { outDir, from, to, fps, name }) take a page
// already opened by _cdp.mjs openPage, so qa needs no second Chrome; motionLine(res, await runtimeState(pg)) is the one
// line to print. segmentsOnScreen(page, ids) turns the segment ids shown in a span into qa's scope.
// Importing this file runs nothing; it loads _cdp.mjs lazily (only for its own --runtime/--curves), so _cdp.mjs may
// import it. R3 reads T3.motionProbe.all(0.25) (lib/motion/probe.js: { id: { f0, f1, meta: { kind, seg }, samples } or
// { …, error } }); without it, window.__T3_PROBES = { id: { f0, f1, fn, meta } }. meta.seg (the T3.register id) or a
// literal probe id in the file ties a probe to its segment.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const SELF = fileURLToPath(import.meta.url);
const HERE = path.dirname(SELF);
export const SKILL_DIR = path.dirname(HERE);
const GROUPS = ['curve', 'move', 'type', 'her', 'cam', 'trans', 'fx', 'time', 'locked'];
const ID_RE = /^[a-z]+\.[a-z0-9-]+$/;
const ID_IN_TEXT = new RegExp(`(?<![\\w.$/-])(?:${GROUPS.join('|')})\\.[a-z0-9]+(?:-[a-z0-9]+)*(?![\\w$-])`, 'g');
const PRAGMA_KINDS = ['steps', 'scan', 'typewriter', 'blink', 'flick', 'stepped', 'measured', 'hold'];
const FRAME_VAR = /(?<![\w$.])(?:f|ft|fp|f0|fr|fi|fl|lf|ff|frame|frm|t|tt|lt|tau|age|rel|local|df|dt|F)(?![\w$])/;
/** R3 shape thresholds: uncalibrated, so every metric is a NOTE until the director signs them in motion-library «Curve sheet» */
export const R3_THRESHOLDS = Object.freeze({
  signed: false,
  q1ShareMin: 0.6,        // an arrival puts at least this share of its travel in the first quarter (power3.out 0.58, power4.out 0.68, expo.out 0.82)
  arrivalMinF: 8,         // an arrival shorter than this many frames
  constRunF: 6,           // a run of constant velocity this long (frames) …
  constRelTol: 0.002,     // … its speed staying within 0.2 % of itself (a sine shorter than ~6 s never does) …
  constMinV: 0.2,         // … at more than 20 % of the peak speed
  deadStopPxF: 8,         // a dead stop: from more than 8 px/f …
  deadStopRestPxF: 0.5,   // … to less than 0.5 px/f within 1 f, with no settle (< 0.25 px/f) over the next 4 f
  cornerJump: 0.35,       // a corner: speed jumping by more than 35 % of the peak between two 1/4-f samples, mid-move
  symStartV: 0.4,         // a symmetric (in-out) arrival: starts below 40 % of peak speed (it speeds up first), peak in the middle 40 %
  exitEndV: 0.8,          // an exit ends at no less than 80 % of its peak speed (accelerating into the cut)
});

// ---------------------------------------------------------------------------------------------------- small helpers
const readText = (p) => fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '');
const exists = (p) => { try { return fs.existsSync(p); } catch { return false; } };
const normP = (p) => path.resolve(p).replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase();
const within = (d, p) => d === p || d.startsWith(p + '/');
const realMemo = new Map();
/** the real path (junctions and links resolved), normalised; null when the path does not exist */
const realP = (p) => {
  const k = normP(p);
  if (!realMemo.has(k)) { let r = null; try { r = normP(fs.realpathSync.native(path.resolve(p))); } catch {} realMemo.set(k, r); }
  return realMemo.get(k);
};
// as written, or after resolving junctions on both sides: a project moved behind a junction (TOP15, PLAN §7.9) keeps
// its entry whichever of its two paths a tool is given
const under = (dir, prefix) => {
  if (within(normP(dir), normP(prefix))) return true;
  const d = realP(dir), p = realP(prefix);
  return !!(d && p) && within(d, p);
};
const localTime = (ms) => { const d = new Date(ms), p = (n) => String(n).padStart(2, '0'); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())} local`; };
const clip = (s, n = 230) => (s.length > n ? s.slice(0, n - 1) + '…' : s);
function lineIndex(text) { const st = [0]; for (let i = 0; i < text.length; i++) if (text[i] === '\n') st.push(i + 1); return st; }
function lineAt(starts, pos) { let lo = 0, hi = starts.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (starts[m] <= pos) lo = m; else hi = m - 1; } return lo + 1; }
const memo = new Map();
function cached(kind, file, build) {
  let st = null; try { st = fs.statSync(file); } catch {}
  const key = kind + '|' + file, sig = st ? st.mtimeMs + ':' + st.size : 'missing';
  const hit = memo.get(key);
  if (hit && hit.sig === sig) return hit.val;
  const val = build(st ? readText(file) : null);
  memo.set(key, { sig, val });
  return val;
}

/** JS source with comments (and regex-literal bodies) blanked to spaces; strings, line breaks and columns kept */
export function stripJsComments(src) {
  const out = src.split(''), n = src.length, stack = [{ t: 'code', depth: 0 }];
  const kw = new Set(['return', 'typeof', 'instanceof', 'in', 'of', 'new', 'delete', 'void', 'throw', 'case', 'do', 'else', 'yield', 'await']);
  const blank = (a, b) => { for (let k = a; k < b && k < n; k++) if (src[k] !== '\n' && src[k] !== '\r') out[k] = ' '; };
  let i = 0, prev = '', word = '';
  while (i < n) {
    const top = stack[stack.length - 1], c = src[i];
    if (top.t === 'tpl') {
      if (c === '\\') { i += 2; continue; }
      if (c === '`') { stack.pop(); i++; prev = ')'; word = ''; continue; }
      if (c === '$' && src[i + 1] === '{') { stack.push({ t: 'code', depth: 0, tpl: true }); i += 2; prev = '('; word = ''; continue; }
      i++; continue;
    }
    const d = src[i + 1];
    if (c === '/' && d === '/') { let j = i; while (j < n && src[j] !== '\n') j++; blank(i, j); i = j; continue; }
    if (c === '/' && d === '*') { let j = src.indexOf('*/', i + 2); j = j < 0 ? n : j + 2; blank(i, j); i = j; continue; }
    if (c === '"' || c === "'") { let j = i + 1; while (j < n && src[j] !== c && src[j] !== '\n') { if (src[j] === '\\') j++; j++; } i = j + 1; prev = 'a'; word = ''; continue; }
    if (c === '`') { stack.push({ t: 'tpl' }); i++; continue; }
    if (c === '/') {
      if (prev === '' || '(,=:[!&|?{};+-*%<>~^'.includes(prev) || kw.has(word)) {        // a regex literal
        let j = i + 1, cls = false;
        while (j < n && src[j] !== '\n') { const e = src[j]; if (e === '\\') { j += 2; continue; } if (cls) { if (e === ']') cls = false; } else if (e === '[') cls = true; else if (e === '/') break; j++; }
        blank(i + 1, j); j++; while (j < n && /[a-z]/i.test(src[j])) j++; i = j; prev = 'a'; word = ''; continue;
      }
      prev = '/'; word = ''; i++; continue;
    }
    if (c === '{') { top.depth++; prev = '{'; word = ''; i++; continue; }
    if (c === '}') { if (top.tpl && top.depth === 0) { stack.pop(); i++; continue; } top.depth--; prev = '}'; word = ''; i++; continue; }
    if (c === ' ' || c === '\t' || c === '\n' || c === '\r') { i++; continue; }
    if (/[\w$]/.test(c)) { let j = i; while (j < n && /[\w$]/.test(src[j])) j++; word = src.slice(i, j); prev = 'a'; i = j; continue; }
    prev = c; word = ''; i++;
  }
  return out.join('');
}
const stripHtmlComments = (h) => h.replace(/<!--[\s\S]*?-->/g, (m) => m.replace(/[^\n]/g, ' '));

function skipStr(code, i) {
  const q = code[i]; let j = i + 1;
  if (q === '`') {
    while (j < code.length) { const c = code[j]; if (c === '\\') { j += 2; continue; } if (c === '`') return j + 1; if (c === '$' && code[j + 1] === '{') { j = matchClose(code, j + 1) + 1; continue; } j++; }
    return j;
  }
  while (j < code.length && code[j] !== q && code[j] !== '\n') { if (code[j] === '\\') j++; j++; }
  return j + 1;
}
/** code[i] is ( [ or {: the index of its partner */
function matchClose(code, i) {
  let depth = 0;
  for (let j = i; j < code.length; j++) {
    const c = code[j];
    if (c === '"' || c === "'" || c === '`') { j = skipStr(code, j) - 1; continue; }
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') { depth--; if (depth === 0) return j; }
  }
  return code.length - 1;
}
/** end of the expression starting at s: a depth-0 , or ; or closing bracket, or a line end where ASI would end it */
function exprEnd(code, s) {
  let depth = 0;
  for (let j = s; j < code.length; j++) {
    const c = code[j];
    if (c === '"' || c === "'" || c === '`') { j = skipStr(code, j) - 1; continue; }
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') { if (depth === 0) return j; depth--; }
    else if (depth === 0 && (c === ',' || c === ';')) return j;
    else if (depth === 0 && c === '\n') {
      let a = j - 1; while (a > s && /\s/.test(code[a])) a--;
      let b = j + 1; while (b < code.length && /\s/.test(code[b])) b++;
      if (!'=+-*/%&|^,?:(<>[{!~'.includes(code[a]) && !'.?:+-*/%&|^,=<>)]}'.includes(code[b] || '')) return j;
    }
  }
  return code.length;
}

// ---------------------------------------------------------------------------------------------------- T3 through local names
// S4 and the curve-source counts read calls written through local names as well as in full: const EZ = T3.EZ,
// mv = T3.mv; const T = window.T3; const { EZ, mv: M } = T3; const { snap, at } = T3.EZ; a default parameter E = T3.EZ;
// an alias of an alias. Everything is read from comment-stripped code, and a path written inside a '…' or "…" string
// is no use of it.
const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
/** code with the insides of '…' and "…" blanked (quotes, line breaks and columns kept); template literals stay */
function blankStrings(code) {
  const out = code.split('');
  for (let i = 0; i < code.length; i++) {
    const c = code[i];
    if (c === '`') { i = skipStr(code, i) - 1; continue; }
    if (c !== '"' && c !== "'") continue;
    const j = skipStr(code, i);
    for (let k = i + 1; k < j - 1; k++) if (code[k] !== '\n' && code[k] !== '\r') out[k] = ' ';
    i = j - 1;
  }
  return out.join('');
}
/** s split at its depth-0 commas → [{ text, at }] (at = offset in s) */
function splitTop(s) {
  const out = []; let depth = 0, a = 0;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '"' || c === "'" || c === '`') { i = skipStr(s, i) - 1; continue; }
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') depth--;
    else if (c === ',' && depth === 0) { out.push({ text: s.slice(a, i), at: a }); a = i + 1; }
  }
  out.push({ text: s.slice(a), at: a });
  return out;
}
/** local names for T3 paths in one file (code: comments stripped, strings blanked) →
 *  { names: Map(name → { path: 'T3' | 'T3.EZ' | 'T3.EZ.snap' | … }), decl: Set(position of each declared name),
 *    rhs: [[from, to]] the right-hand sides of those declarations (a declaration alone uses nothing) } */
function t3Aliases(code) {
  const names = new Map(), decl = new Set(), rhs = new Map();
  const resolve = (expr) => {                          // "T3.EZ", "window.T3", "(window.T3 || {}).mv", "EZ.snap" (EZ known)
    let x = expr.trim();
    for (let g = 0; g < 4 && x[0] === '('; g++) { const c = matchClose(x, 0); x = (x.slice(1, c).split(/\|\||\?\?/)[0] + x.slice(c + 1)).trim(); }
    x = x.split(/\|\||\?\?/)[0].trim();
    const m = /^(?:(?:window|self|globalThis)\s*\.\s*)?([A-Za-z_$][\w$]*)((?:\s*\.\s*[A-Za-z_$][\w$]*)*)$/.exec(x);
    if (!m) return null;
    const base = m[1] === 'T3' ? 'T3' : names.has(m[1]) ? names.get(m[1]).path : null;
    return base ? base + m[2].replace(/\s+/g, '') : null;
  };
  const bind = (name, p, pos) => {
    if (!p || name === 'T3') return false;            // const T3 = window.T3 is the name itself
    const e = names.get(name);
    if (e && e.path !== p) return false;              // bound to another path elsewhere: keep the first
    if (!e) names.set(name, { path: p });
    decl.add(pos);
    return true;
  };
  const pattern = (pat, at0, p) => {                  // { a, b: c, d = 1, e: { f } } read from path p; at0 = offset of pat
    let any = false;
    for (const it of splitTop(pat)) {
      const t = it.text.trim(), at = at0 + it.at + (it.text.length - it.text.trimStart().length);
      const m = /^([A-Za-z_$][\w$]*)\s*(?:(=)|:\s*)?/.exec(t);
      if (!m || t.startsWith('...')) continue;
      const key = m[1], sub = p + '.' + key;
      if (m[0].length === t.length || m[2]) { any = bind(key, sub, at) || any; continue; }     // key, or key = default
      const rest = t.slice(m[0].length), restAt = at + m[0].length;
      if (rest[0] === '{') { any = pattern(rest.slice(1, matchClose(rest, 0)), restAt + 1, sub) || any; continue; }
      const n = /^([A-Za-z_$][\w$]*)/.exec(rest);                                               // key: name (= default)
      if (n) any = bind(n[1], sub, restAt) || any;
    }
    return any;
  };
  const declare = () => {
    for (const m of code.matchAll(/(?<![\w$.])(?:const|let|var)\s+/g)) {
      let i = m.index + m[0].length;
      for (let guard = 0; guard < 60; guard++) {
        let name = null, pat = null, j;
        if (code[i] === '{' || code[i] === '[') { const c = matchClose(code, i); pat = { open: code[i], text: code.slice(i + 1, c), at: i + 1 }; j = c + 1; }
        else { const n = /^[A-Za-z_$][\w$]*/.exec(code.slice(i, i + 120)); if (!n) break; name = n[0]; j = i + name.length; }
        while (/\s/.test(code[j] || '')) j++;
        let e;
        if (code[j] === '=' && code[j + 1] !== '=' && code[j + 1] !== '>') {
          const s = j + 1; e = exprEnd(code, s);
          const p = resolve(code.slice(s, e));
          if (p && (name ? bind(name, p, i) : pat.open === '{' && pattern(pat.text, pat.at, p))) rhs.set(s, e);
        } else e = exprEnd(code, j);
        if (code[e] !== ',') break;
        i = e + 1; while (/\s/.test(code[i] || '')) i++;
      }
    }
  };
  const assign = () => {                              // EZ = T3.EZ outside a declaration, and default parameters (f, E = T3.EZ)
    for (const m of code.matchAll(/(?<![\w$.])([A-Za-z_$][\w$]*)\s*=(?![=>])/g)) {
      if (/^(?:const|let|var)$/.test(m[1])) continue;
      const s = m.index + m[0].length, e = exprEnd(code, s), p = resolve(code.slice(s, e));
      if (p && bind(m[1], p, m.index)) rhs.set(s, e);
    }
  };
  for (let pass = 0; pass < 3; pass++) { declare(); assign(); }   // an alias of an alias
  return { names, decl, rhs: [...rhs.entries()] };
}
/** a regex source for the ways the file writes path p: T3.EZ.snap, EZ.snap (EZ = T3.EZ), T.EZ.snap (T = window.T3),
 *  snap (const { snap } = T3.EZ) */
function pathRe(A, p) {
  const alts = [`(?<![\\w$])T3${escRe(p.slice(2))}`];
  for (const [name, a] of A.names) {
    if (a.path === p) alts.push(`(?<![\\w$.])${escRe(name)}`);
    else if (p.startsWith(a.path + '.')) alts.push(`(?<![\\w$.])${escRe(name)}${escRe(p.slice(a.path.length))}`);
  }
  return `(?:${alts.join('|')})(?![\\w$])`;
}
/** does the file use path p (or anything under it), in full or through a local name, outside the aliases' own declarations?
 *  codeB: comments stripped, strings blanked */
function usesPath(A, codeB, p) {
  const skip = (i, len) => A.decl.has(i) || A.rhs.some(([s, e]) => i >= s && i < e)
    || /(?<![\w$.])(?:let|var|const)\s+$/.test(codeB.slice(Math.max(0, i - 12), i))                                    // let st; (bound later)
    || (/[{,]\s*$/.test(codeB.slice(Math.max(0, i - 40), i)) && /^\s*:(?!:)/.test(codeB.slice(i + len, i + len + 4)))   // an object key
    || /^\s*=(?![=>])/.test(codeB.slice(i + len, i + len + 4));                                                         // assigned to
  for (const m of codeB.matchAll(new RegExp(pathRe(A, p), 'g'))) if (!skip(m.index, m[0].length)) return true;
  for (const [name, a] of A.names) {
    if (!a.path.startsWith(p + '.')) continue;
    for (const m of codeB.matchAll(new RegExp(`(?<![\\w$.])${escRe(name)}(?![\\w$])`, 'g'))) if (!skip(m.index, m[0].length)) return true;
  }
  return false;
}
/** calls through namespace ns (T3.EZ.x(…), EZ.x(…), x(…) for const { x } = T3.EZ); codeB as above */
function callsThrough(A, codeB, ns) {
  let n = (codeB.match(new RegExp(`${pathRe(A, ns)}\\s*\\.\\s*[A-Za-z_$][\\w$]*\\s*\\(`, 'g')) || []).length;
  for (const [name, a] of A.names) if (a.path.startsWith(ns + '.')) n += (codeB.match(new RegExp(`(?<![\\w$.])(?<!function\\s+)${escRe(name)}\\s*\\(`, 'g')) || []).length;
  return n;
}

// ---------------------------------------------------------------------------------------------------- the skill's texts
function paths(opts = {}) {
  const sk = path.resolve(opts.skill || SKILL_DIR);
  return {
    skill: sk,
    library: path.resolve(opts.library || path.join(sk, 'references', 'motion-library.md')),
    recipes: path.join(sk, 'references', 'shot-recipes.md'),
    styles: path.join(sk, 'references', 'mg-styles.md'),
    lib: path.join(sk, 'assets', 'template', 'lib'),
    legacy: path.resolve(opts.legacyList || path.join(HERE, 'motion_legacy.json')),
  };
}

/** references/motion-library.md → { ok, path, ids: Map(id → entry), problems, mentions } (format: motion-library «Entry format») */
export function loadLibrary(file) {
  return cached('lib', file, (text) => {
    const L = { ok: !!text, path: file, ids: new Map(), problems: [], dups: [], mentions: [], text: text || '' };
    if (!text) return L;
    const lines = text.split(/\r?\n/);
    let section = 'main', secLevel = 99, inFence = false;
    lines.forEach((ln, i) => {
      if (/^\s*```/.test(ln)) { inFence = !inFence; return; }
      if (inFence) return;
      const h = /^(#{1,6})\s+(.*)$/.exec(ln);
      if (h) {
        const lev = h[1].length, title = h[2];
        if (/\bretired\b/i.test(title)) { section = 'retired'; secLevel = lev; }
        else if (/\bpending\b/i.test(title)) { section = 'pending'; secLevel = lev; }
        else if (lev <= secLevel) { section = 'main'; secLevel = 99; }
        return;
      }
      for (const m of ln.matchAll(/`([a-z]+\.[a-z0-9-]+)`/g)) if (GROUPS.includes(m[1].split('.')[0])) L.mentions.push({ id: m[1], line: i + 1 });
      for (const m of ln.matchAll(/«\s*(shot-recipes|mg-styles)\s*:\s*([^»]+?)\s*»/g)) L.mentions.push({ cite: m[1], name: m[2], line: i + 1 });
      const e = /^\s*[-*]\s+\*\*`([^`]+)`\*\*\s*(.*)$/.exec(ln) || (section === 'retired' ? /^\s*[-*]\s+\*{0,2}`([a-z]+\.[a-z0-9-]+)`\*{0,2}\s*(.*)$/.exec(ln) : null);
      if (!e) return;
      const id = e[1].trim(), rest = e[2];
      const f = rest.replace(/^\s*·\s*/, '').split(/\s+·\s+/).map((s) => s.trim()).filter(Boolean);
      const codeField = (f.length ? f[f.length - 1] : '').replace(/`/g, '').trim();
      const ent = { id, line: i + 1, section, name: f[0] || '', grade: '', reuse: '', craft: '', code: codeField, kind: null, module: null, calls: [], reason: '' };
      const g = f.find((x, k) => k > 0 && /^[ABHRP](\/[ABHRP])*(\b|$)/.test(x)); ent.grade = g ? g.split(/\s/)[0] : '';
      ent.reuse = /\bsignature\b/.test(f.slice(1, -1).join(' ')) ? 'signature' : 'craft';
      ent.craft = f[3] || '';
      let m;
      if ((m = /^LIB\s+(\S+)\s*(.*)$/.exec(codeField))) { ent.kind = 'LIB'; ent.module = m[1]; ent.calls = parseCalls(m[2]); }
      else if ((m = /^EXISTING\s+(\S+)\s*(.*)$/.exec(codeField))) { ent.kind = 'EXISTING'; ent.module = m[1]; ent.calls = parseCalls(m[2]); }
      else if ((m = /^PENDING-LIB\s+(\S+)/.exec(codeField))) { ent.kind = 'PENDING-LIB'; ent.module = m[1]; }
      else if (/^LOCKED\b/.test(codeField)) ent.kind = 'LOCKED';
      else if (/^PROSE\b/.test(codeField)) ent.kind = 'PROSE';
      if (section === 'retired') { ent.retired = true; ent.reason = clip(rest.replace(/^[\s·—:-]+/, ''), 140); }
      ent.pending = section === 'pending' || ent.grade === 'P';
      ent.signature = ent.reuse === 'signature';
      if (L.ids.has(id)) L.dups.push({ id, line: i + 1, first: L.ids.get(id).line });
      else L.ids.set(id, ent);
    });
    return L;
  });
}
/** "T3.EZ.back/elastic, T3.mv.swap" → ['T3.EZ.back', 'T3.EZ.elastic', 'T3.mv.swap'] */
function parseCalls(s) {
  const out = [];
  for (const m of String(s).matchAll(/T3(?:\.[A-Za-z_$*][\w$*]*)+(?:\/[A-Za-z_$][\w$]*)*/g)) {
    const [head, ...alts] = m[0].split('/'); out.push(head);
    const base = head.split('.').slice(0, -1).join('.');
    for (const a of alts) out.push(base + '.' + a);
  }
  if (!out.length) for (const m of String(s).matchAll(/\b[a-z][A-Za-z0-9_$]*\b/g)) if (!/^(and|or|the|with|for|only|call|calls)$/.test(m[0])) out.push(m[0]);
  return out;
}
const loadRecipes = (file) => cached('rec', file, (t) => new Set(t ? [...t.matchAll(/\*\*([a-z0-9][a-z0-9-]*)\*\*/g)].map((m) => m[1]) : []));
const loadStyles = (file) => cached('sty', file, (t) => new Set(t ? [...t.matchAll(/\*\*(\d+ [^*\n]+?)\*\*/g)].map((m) => m[1].toLowerCase()) : []));
const openingNames = () => new Set();
export const isExempt = (_name, _opening) => false;

/** scripts/motion_legacy.json → [{ prefix, date, until, cutoff (ms), reason }] */
export function loadLegacy(file) {
  return cached('leg', file, (text) => {
    if (!text) return { ok: false, path: file, entries: [], problems: ['legacy list missing: ' + file] };
    let j; try { j = JSON.parse(text); } catch (e) { return { ok: false, path: file, entries: [], problems: ['legacy list unreadable: ' + e.message] }; }
    const problems = [];
    const entries = (j.entries || []).map((e) => {
      let cutoff = NaN;
      if (e.until) cutoff = Date.parse(e.until);
      else { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(e.date || ''); if (m) cutoff = new Date(+m[1], +m[2] - 1, +m[3], 23, 59, 59, 999).getTime(); }
      if (!Number.isFinite(cutoff)) problems.push(`legacy entry without a usable date: ${e.prefix}`);
      return { prefix: e.prefix, date: e.date, until: e.until || null, cutoff, reason: e.reason || '' };
    });
    return { ok: true, path: file, entries, problems };
  });
}
/** the legacy-list entry a page folder falls under (the folder and the prefixes are compared as written and with
 *  junctions resolved; an entry matched as written goes first, then the longest prefix: TOP15 is listed under both its
 *  paths, so a page reports the entry for the path it was given), or null. Needs only the folder's path: reads nothing inside it. */
export function legacyEntry(pageDir, opts = {}) {
  const leg = loadLegacy(paths(opts).legacy), d = normP(pageDir);
  const raw = (e) => (within(d, normP(e.prefix)) ? 1 : 0);
  return leg.entries.filter((e) => e.prefix && under(pageDir, e.prefix)).sort((a, b) => raw(b) - raw(a) || b.prefix.length - a.prefix.length)[0] || null;
}

// ---------------------------------------------------------------------------------------------------- the page
function parsePage(page) {
  const html = readText(page), clean = stripHtmlComments(html), dir = path.dirname(page), starts = lineIndex(clean);
  const scripts = [], fileOf = (u, from) => { try { return /^file:/i.test(u) ? fileURLToPath(u) : path.resolve(from, decodeURIComponent(u)); } catch { return path.resolve(from, u); } };
  const base = /<base\b[^>]*\bhref\s*=\s*["']([^"']+)["']/i.exec(clean);   // V8's pages load another project's segments
  const baseDir = base ? fileOf(base[1].replace(/[^/\\]*$/, '') || './', dir) : dir;
  for (const m of clean.matchAll(/<script\b([^>]*)>/gi)) {
    const src = /\bsrc\s*=\s*["']([^"']+)["']/i.exec(m[1]);
    if (!src) continue;
    const s = src[1].split(/[?#]/)[0];
    scripts.push({ src: s, abs: fileOf(s, baseDir), line: lineAt(starts, m.index), module: /type\s*=\s*["']module/i.test(m[1]) });
  }
  let segs = scripts.filter((s) => /(^|\/)segments\//.test(s.src) && !s.module);
  if (!segs.length) segs = scripts.filter((s) => !s.module && !/(^|\/)(lib|assets|panels)\//.test(s.src) && !/(^|\/)(engine|data)\.js$/.test(s.src));
  const opt = /motionLegacy\s*["']?\s*[:=]\s*(["'`])((?:\\.|(?!\1)[^\\])*)\1/.exec(clean);   // { motionLegacy: '…' } or T3_CONFIG.motionLegacy = '…'
  return { html, clean, dir, baseDir, scripts, segs, optOut: opt && opt[2].trim() ? opt[2].trim() : null };
}
/** S9: the project's lib/motion against the template's. The template's modules are read from its folder at run time
 *  (a module added to the template later is asked for too); the project's folder is where the page's lib/motion/ez.js
 *  tag resolves (else its first lib/motion/ tag, else <page>/lib/motion). firstSeg: the index in pg.scripts of the first
 *  checked segment (S1's), or -1. → null when the template's folder cannot be read, else { dir, tplDir, order (the
 *  template's modules in its own tag order), missing, unloaded (present, no tag), late (tag after firstSeg), differs,
 *  begun (the page loads something from a lib/motion/ folder, or the project's folder exists) } */
function libMotionState(pg, P, firstSeg) {
  const tplDir = path.join(P.lib, 'motion');
  let mods; try { mods = fs.readdirSync(tplDir).filter((n) => /\.js$/i.test(n)); } catch { return null; }
  if (!mods.length) return null;
  let tagOrder = [];
  try { tagOrder = [...stripHtmlComments(readText(path.join(P.skill, 'assets', 'template', 'index.html'))).matchAll(/<script\b[^>]*\bsrc\s*=\s*["'](?:[^"']*\/)?lib\/motion\/([\w.-]+\.js)["']/gi)].map((m) => m[1].toLowerCase()); } catch {}
  const rank = (n) => { const i = tagOrder.indexOf(n.toLowerCase()); return i < 0 ? tagOrder.length : i; };
  mods.sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
  const tags = pg.scripts.map((s, i) => ({ s, i })).filter(({ s }) => /(^|\/)lib\/motion\/[^/]+\.js$/i.test(s.src));
  const ez = tags.find(({ s }) => /(^|\/)lib\/motion\/ez\.js$/i.test(s.src)) || tags[0];
  const dir = ez ? path.dirname(ez.s.abs) : path.join(pg.baseDir, 'lib', 'motion');
  // line ends, a BOM and trailing whitespace are not a difference
  const text = (p) => readText(p).replace(/\r\n?/g, '\n').trimEnd();
  const out = { dir, tplDir, order: mods, missing: [], unloaded: [], late: [], differs: [], begun: tags.length > 0 || exists(dir) };
  for (const n of mods) {
    // the module's tag in the project's folder, else one loading it from another lib/motion folder (that copy is the one checked)
    const own = path.join(dir, n), t = path.join(tplDir, n);
    const tag = tags.find(({ s }) => normP(s.abs) === normP(own)) || tags.find(({ s }) => path.basename(s.abs).toLowerCase() === n.toLowerCase() && exists(s.abs));
    const f = tag ? tag.s.abs : own;
    if (!exists(f)) out.missing.push(n);
    else if (normP(f) !== normP(t)) { try { if (text(f) !== text(t)) out.differs.push(n); } catch { out.differs.push(n); } }
    if (!tag) { if (exists(f)) out.unloaded.push(n); }
    else if (firstSeg >= 0 && tag.i > firstSeg && !/^ez\.js$/i.test(n)) out.late.push(n);   // a late ez.js is S1's FAIL
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------- one segment
function parseHeader(lines) {
  const head = lines.slice(0, 15);
  let sheet = null, motion = null, sheetLine = null, motionLine = null;
  for (let i = 0; i < head.length; i++) {
    const ln = head[i];
    let m = /^\s*(?:\/\/+|\/?\*+)\s*motion-sheet\s*:\s*(.*?)\s*(?:\*\/)?\s*$/.exec(ln);
    if (m && sheet == null) { sheet = m[1]; sheetLine = i + 1; continue; }
    m = /^\s*(?:\/\/+|\/?\*+)\s*motion\s*:\s*(.*?)\s*(?:\*\/)?\s*$/.exec(ln);
    if (m && motion == null) {
      motion = m[1]; motionLine = i + 1;
      while (/,\s*$/.test(motion) && i + 1 < head.length) {           // a list wrapped onto the next comment lines
        const c = /^\s*(?:\/\/+|\*+)\s*(.*?)\s*(?:\*\/)?\s*$/.exec(head[i + 1]); if (!c) break; motion += ' ' + c[1]; i++;
      }
    }
  }
  return { sheet, motion, sheetLine, motionLine };
}
function splitCites(s) {
  const out = []; let cur = '', depth = 0;
  for (const c of s) {
    if (c === '«' || c === '(') depth++; else if (c === '»' || c === ')') depth = Math.max(0, depth - 1);
    if ((c === ',' || c === ';') && depth === 0) { out.push(cur); cur = ''; } else cur += c;
  }
  out.push(cur);
  return out.map((x) => x.trim()).filter(Boolean);
}
/** one citation → { kind: 'id' | 'recipe' | 'style' | 'none' | 'text', key, raw } */
function parseCite(raw) {
  const t = raw.replace(/^`|`$/g, '').trim();
  let m = /^«?\s*shot-recipes\s*:\s*([^»(]+?)\s*(?:\([^)]*\))?\s*»?$/.exec(t);
  if (m) return { kind: 'recipe', key: m[1].trim(), raw };
  m = /^«?\s*mg-styles\s*:\s*([^»]+?)\s*»?$/.exec(t);
  if (m) return { kind: 'style', key: m[1].trim(), raw };
  if (/^(none|—|-)$/i.test(t)) return { kind: 'none', raw };
  m = /^`?([a-z]+\.[a-z0-9-]+)`?(?:\s.*)?$/.exec(t);
  if (m) return { kind: 'id', key: m[1], raw };
  return { kind: 'text', key: t, raw };
}

const EASE_PATS = [
  ['expo', () => /Math\.pow\(\s*2\s*,\s*-?\s*10|2\s*\*\*\s*\(?\s*-?\s*10/],
  ['power-out', () => /1\s*-\s*Math\.pow\(\s*1\s*-|\(\s*1\s*-\s*([\w$]+)\s*\)\s*\*\s*\(\s*1\s*-\s*\1\s*\)/],
  ['back', () => /1\.70158|2\.5949|(?<![\d.])1\.525(?!\d)/],
  ['smoothstep', () => /([\w$.]+)\s*\*\s*\1\s*\*\s*\(\s*3\s*-\s*2\s*\*\s*\1\s*\)/],
  ['elastic', () => /\(\s*2\s*\*\s*Math\.PI\s*\)\s*\/\s*3|2\.0943/],
  ['power', (one) => one && /Math\.pow\([^;]*?,\s*[2-5](?:\.0+)?\s*\)/],
  ['cubic', (one) => one && /(?<![\w$.])([A-Za-z_$][\w$]*)\s*\*\s*\1\s*\*\s*\1(?![\w$])/],
  ['sine', (one) => one && /Math\.(?:cos|sin)\([^)]*\b(?:Math\.)?PI\b/],
  ['circ', (one) => one && /Math\.sqrt\(\s*1\s*-/],
];
/** local ease definitions: [{ name, prop, line, kinds, symmetric, body: [a, b] }] */
function easeDefs(code, starts) {
  const defs = [];
  const add = (name, params, bodyStart, prop, defPos) => {
    let b0 = bodyStart; while (/\s/.test(code[b0] || '')) b0++;
    const b1 = code[b0] === '{' ? matchClose(code, b0) + 1 : exprEnd(code, b0);
    const body = code.slice(b0, b1), flat = body.replace(/\s+/g, ' ');
    if (flat.length > 240) return;
    const ps = params.split(',').map((p) => p.split('=')[0].trim()).filter(Boolean), one = ps.length === 1;
    let kinds = EASE_PATS.filter(([, re]) => { const r = re(one); return r && r.test(flat); }).map(([k]) => k);
    if (!kinds.length) return;
    if (kinds.length > 1) kinds = kinds.filter((k) => k !== 'power' && k !== 'cubic' || kinds.every((x) => x === 'power' || x === 'cubic'));
    const symmetric = /<\s*0?\.5\s*\?/.test(flat) || kinds.includes('smoothstep') || (kinds.includes('sine') && /Math\.cos/.test(flat) && /0\.5|1\s*-/.test(flat));
    defs.push({ name, prop, line: lineAt(starts, defPos), kinds, symmetric, body: [b0, b1], pos: defPos });
  };
  for (const m of code.matchAll(/(?<![\w$.])([A-Za-z_$][\w$]*)\s*=\s*(?:\(([^()]*)\)|([A-Za-z_$][\w$]*))\s*=>/g)) add(m[1], m[2] != null ? m[2] : m[3], m.index + m[0].length, false, m.index);
  for (const m of code.matchAll(/(?<![\w$.])([A-Za-z_$][\w$]*)\s*=\s*function\s*[\w$]*\s*\(([^()]*)\)\s*(?=\{)/g)) add(m[1], m[2], m.index + m[0].length, false, m.index);
  for (const m of code.matchAll(/\bfunction\s+([A-Za-z_$][\w$]*)\s*\(([^()]*)\)\s*(?=\{)/g)) add(m[1], m[2], m.index + m[0].length, false, m.index);
  for (const m of code.matchAll(/(?<![\w$.?])([A-Za-z_$][\w$]*)\s*:\s*(?:\(([^()]*)\)|([A-Za-z_$][\w$]*))\s*=>/g)) add(m[1], m[2] != null ? m[2] : m[3], m.index + m[0].length, true, m.index);
  const seen = new Set();
  return defs.filter((d) => { const k = d.name + '|' + d.pos; if (seen.has(k)) return false; seen.add(k); return true; });
}
/** declarators whose initialiser builds eases from GSAP (a project-local copy of T3.EZ) */
function localEaseTables(code) {
  const res = [];
  for (const m of code.matchAll(/\b(?:const|let|var)\s+/g)) {
    let i = m.index + m[0].length;
    for (let guard = 0; guard < 50; guard++) {
      const nm = /^([A-Za-z_$][\w$]*)\s*=(?![=>])/.exec(code.slice(i, i + 120));
      if (!nm) break;
      const s = i + nm[0].length, e = exprEnd(code, s);
      if (/\bparseEase\s*\(|\bCustomEase\.create\s*\(/.test(code.slice(s, e))) res.push({ name: nm[1], pos: s });
      if (code[e] !== ',') break;
      i = e + 1; while (/\s/.test(code[i] || '')) i++;
    }
  }
  return res;
}
const GSAP_API = new Set(['parseEase', 'to', 'from', 'fromTo', 'set', 'timeline', 'registerPlugin', 'create', 'utils', 'getProperty', 'quickSetter', 'quickTo', 'ticker', 'defaults', 'globalTimeline', 'config']);
const NUM = '-?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:e-?\\d+)?';      // one way to read each number: no runaway backtracking on long lists
const RE_ARR = new RegExp(`\\[\\s*(?:${NUM}\\s*,\\s*){2,}${NUM}\\s*,?\\s*\\]`, 'g');
const KEY = `["']?-?\\d+(?:\\.\\d+)?["']?`;
const RE_OBJ = new RegExp(`\\{\\s*(?:${KEY}\\s*:\\s*${NUM}\\s*,\\s*){2,}${KEY}\\s*:\\s*${NUM}\\s*,?\\s*\\}`, 'g');
/** per-frame value tables (S7) */
function frameTables(code, starts) {
  const out = [];
  const subscript = (end) => { let j = end; while (/[\s)]/.test(code[j] || '')) j++; if (code[j] !== '[') return null; const k = matchClose(code, j); return code.slice(j + 1, k); };
  const count = (lit) => (lit.match(new RegExp(NUM + '(?=\\s*[,\\]}])', 'g')) || []).length;
  for (const re of [RE_ARR, RE_OBJ]) {
    for (const m of code.matchAll(re)) {
      const before = code.slice(Math.max(0, m.index - 1), m.index);
      if (re === RE_ARR && /[\w$)\]]/.test(before)) continue;                 // a subscript itself, not a literal
      const idx = subscript(m.index + m[0].length), n = count(m[0]);
      if (idx != null && FRAME_VAR.test(idx) && n >= 3) out.push({ line: lineAt(starts, m.index), pos: m.index, n, how: 'inline', idx: idx.trim() });
    }
  }
  for (const m of code.matchAll(/\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?=[[{])/g)) {
    const s = m.index + m[0].length, e = matchClose(code, s), lit = code.slice(s, e + 1);
    RE_ARR.lastIndex = 0; RE_OBJ.lastIndex = 0;
    const whole = (re) => { const r = new RegExp('^' + re.source + '$'); return r.test(lit.trim()); };
    if (!(whole(RE_ARR) || whole(RE_OBJ)) || count(lit) < 4) continue;
    for (const u of code.matchAll(new RegExp(`(?<![\\w$.])${m[1].replace(/\$/g, '\\$')}\\s*\\[`, 'g'))) {
      const j = u.index + u[0].length - 1, idx = code.slice(j + 1, matchClose(code, j));
      if (FRAME_VAR.test(idx)) out.push({ line: lineAt(starts, u.index), pos: u.index, n: count(lit), how: `named ${m[1]} (:${lineAt(starts, s)})`, idx: idx.trim() });
    }
  }
  const seen = new Set();
  return out.filter((t) => { const k = t.pos; if (seen.has(k)) return false; seen.add(k); return true; }).sort((a, b) => a.pos - b.pos);
}

/** a segment's own names (code: comments stripped): its literal probe ids (null for a built one), its literal
 *  T3.register ids, and how many register calls it makes */
function idents(code) {
  const probes = [...code.matchAll(/(?<![\w$])(?:T3\.)?motionProbe\s*\(\s*(?:(["'`])([^"'`]*)(["'`]))?/g)]
    .map((m) => (m[2] && m[1] === m[3] && !m[2].includes('${') ? m[2] : null));      // a built id (template, concatenation) stays null
  const regIds = [...code.matchAll(/\bT3\.register\s*\(\s*\{/g)].map((m) => { const r = /\bid\s*:\s*(["'`])([^"'`]+)\1/.exec(code.slice(m.index, m.index + 400)); return r ? r[2] : null; }).filter(Boolean);
  return { probes, regIds, regCalls: (code.match(/(?<![\w$])register\s*\(/g) || []).length };
}

// S10, a hit built by hand: a scale punch settling to 1 drawn in the same function as a full-frame light fill. Tuned on
// 256 segment files of the projects and the skill's examples (2026-11-21); the header says what it finds and misses.
const HIT_FROM = 1.1;                       // a punch from at least 10 % over size; a 4–6 % push at a cut is a camera move
const HIT_NUM = '(\\d*\\.?\\d+)';
const HIT_PUNCH = [
  [new RegExp(`(?<![\\w$.])${HIT_NUM}\\s*-\\s*${HIT_NUM}\\s*\\*`, 'g'), (m) => (Math.abs(+m[1] - +m[2] - 1) < 1e-6 ? +m[1] : 0)],   // a − (a−1)·k
  [new RegExp(`(?<![\\w$.])1\\s*\\+\\s*${HIT_NUM}\\s*\\*\\s*\\(\\s*1\\s*-`, 'g'), (m) => 1 + +m[1]],                                  // 1 + b·(1 − k)
  [new RegExp(`\\blerp\\s*\\(\\s*${HIT_NUM}\\s*,\\s*1(?:\\.0*)?\\s*,`, 'g'), (m) => +m[1]],                                          // lerp(a, 1, k)
  [/\[\s*(\d*\.?\d+)\s*(?:,\s*\d*\.?\d+\s*){1,8},\s*1(?:\.0*)?\s*\]\s*\[/g, (m) => +m[1]],                                          // [a, …, 1][k]
];
const FULL_RECT = /fillRect\s*\(\s*0\s*,\s*0\s*,\s*(?:W|WW|w|1920|[\w$.]*[wW]idth)\s*,\s*(?:H|HH|h|1080|[\w$.]*[hH]eight)\s*\)/;
/** the lowest of a CSS colour's RGB channels, 0–1 (white = 1); 0 when it cannot be read */
function lightness(c) {
  c = String(c).trim().toLowerCase();
  if (c === 'white') return 1;
  let m = /^#([0-9a-f]{3}|[0-9a-f]{6})(?:[0-9a-f]{1,2})?$/.exec(c);
  if (m) { const h = m[1].length === 3 ? m[1].replace(/./g, '$&$&') : m[1]; return Math.min(...[0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16))) / 255; }
  m = /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/.exec(c);
  return m ? Math.min(+m[1], +m[2], +m[3]) / 255 : 0;
}
/** does the { at c[i] open a function body? (=> {, or ) { whose ( follows no if / for / while / switch / catch / with) */
function opensFunction(c, i) {
  let j = i - 1; while (j >= 0 && /\s/.test(c[j])) j--;
  if (c[j] === '>' && c[j - 1] === '=') return true;
  if (c[j] !== ')') return false;
  let d = 0, k = j;
  for (; k >= 0; k--) { if (c[k] === ')') d++; else if (c[k] === '(' && --d === 0) break; }
  let e = k - 1; while (e >= 0 && /\s/.test(c[e])) e--;
  let s = e; while (s >= 0 && /[\w$]/.test(c[s])) s--;
  return !/^(if|for|while|switch|catch|with)$/.test(c.slice(s + 1, e + 1));
}
/** the position of the innermost function body's { around pos (c: comments stripped, strings blanked), -1 at top level */
function enclosingFn(c, pos) {
  let d = 0;
  for (let i = pos - 1; i >= 0; i--) {
    if (c[i] === '}') d++;
    else if (c[i] === '{') { if (d > 0) d--; else if (opensFunction(c, i)) return i; }
  }
  return -1;
}
/** S10's candidates in one file → [{ line, from, flashLine, flash }] (code: comments stripped; codeB: strings blanked too) */
function handHits(code, codeB, starts) {
  const punches = [], flashes = [];
  for (const [re, from] of HIT_PUNCH) for (const m of codeB.matchAll(re)) { const a = from(m); if (a >= HIT_FROM && a <= 2) punches.push({ pos: m.index, from: a }); }
  // the punch must drive a scale: written inside scale( / setTransform( / scale: on its own line, or assigned to a name
  // that a scale( or setTransform( of the same function reads (a glow, an alpha or a pulse is no hit). Read on `code`,
  // where quoted strings stay, so a DOM transform built as 'scale(' + s + ')' counts; positions are the same in both
  const feeds = (pos) => {
    const ls = code.lastIndexOf('\n', pos) + 1, le = code.indexOf('\n', pos), line = code.slice(ls, le < 0 ? code.length : le);
    if (/\bscale\s*\(|setTransform\s*\(|\bscale\s*:/.test(line)) return true;
    const nm = /([A-Za-z_$][\w$]*)\s*=(?![=>])[^=;]*$/.exec(codeB.slice(ls, pos));
    if (!nm) return false;
    const fn = enclosingFn(codeB, pos), body = fn < 0 ? code : code.slice(fn, matchClose(codeB, fn) + 1);
    return new RegExp(`(?:setTransform|scale)\\s*\\([^)]*(?<![\\w$.])${escRe(nm[1])}(?![\\w$])|\\bscale\\s*:\\s*${escRe(nm[1])}(?![\\w$])`).test(body);
  };
  for (let i = punches.length - 1; i >= 0; i--) if (!feeds(punches[i].pos)) punches.splice(i, 1);
  if (!punches.length) return [];
  for (const m of code.matchAll(/(?<![\w$])fillStyle\s*=\s*([^;\n]*)/g)) {           // canvas: a light fill over the whole frame
    const cols = [...m[1].matchAll(/(['"`])([^'"`]+)\1/g)].map((x) => x[2]).filter((x) => lightness(x) >= 0.85);
    if (!cols.length) continue;
    const after = code.slice(m.index + m[0].length, m.index + m[0].length + 240), next = after.search(/fillStyle\s*=/);
    const lineHead = code.slice(code.lastIndexOf('\n', m.index) + 1, m.index);
    if (FULL_RECT.test(next >= 0 ? after.slice(0, next) : after) && !/globalCompositeOperation\s*=\s*['"`](?:difference|exclusion|xor|destination-)/.test(lineHead)) flashes.push({ pos: m.index, what: cols[0] });
  }
  for (const m of code.matchAll(/(?<![\w$.])([A-Za-z_$][\w$]*)\s*=(?![=>])\s*[^;\n=]*?background(?:Color)?\s*:\s*(['"`])([^'"`]+)\2[^;\n]*/g)) {   // DOM: a full-frame light overlay, met where its style changes
    if (lightness(m[3]) < 0.85 || !/inset\s*:\s*['"`]?0|width\s*:\s*['"`]?(?:100%|1920)/.test(m[0])) continue;
    for (const u of codeB.matchAll(new RegExp(`(?<![\\w$.])${escRe(m[1])}\\.style\\b`, 'g'))) flashes.push({ pos: u.index, what: `${m[1]} (${m[3]})` });
  }
  if (!flashes.length) return [];
  const scope = new Map(), fnOf = (p) => { if (!scope.has(p)) scope.set(p, enclosingFn(codeB, p)); return scope.get(p); };
  const out = [];
  for (const p of punches) {
    const fl = flashes.find((x) => fnOf(x.pos) === fnOf(p.pos));
    if (fl) out.push({ line: lineAt(starts, p.pos), from: p.from, flashLine: lineAt(starts, fl.pos), flash: fl.what });
  }
  return out;
}

/** the S2–S8 and S10 scan of one segment file; ctx: { lib, recipes, styles, projectRoot, mode, strictPage } */
function scanSegment(file, ctx) {
  const src = readText(file), code = stripJsComments(src), starts = lineIndex(code), lines = src.split(/\r?\n/);
  const name = path.basename(file), legacy = ctx.mode === 'legacy';
  const F = [], lv = (strictLevel) => (legacy ? 'NOTE' : strictLevel);
  const add = (check, level, line, msg) => F.push({ check, level, file: name, line: line || null, msg });
  // pragmas
  const pragmas = [], exempt = new Set();
  lines.forEach((ln, i) => {
    const m = /\/\/\s*motion-ok\s*:\s*([A-Za-z-]*)\s*(.*?)\s*$/.exec(ln);
    if (!m) return;
    const kind = m[1].toLowerCase(), reason = m[2].trim(), ok = PRAGMA_KINDS.includes(kind) && reason.length > 0;
    pragmas.push({ file: name, line: i + 1, kind, reason, ok });
    if (ok) { exempt.add(i + 1); exempt.add(i + 2); }
    else add('PRAGMA', 'NOTE', i + 1, `pragma «${clip(ln.trim(), 80)}» exempts nothing: ${PRAGMA_KINDS.includes(kind) ? 'give its reason' : `kind must be one of ${PRAGMA_KINDS.join(' ')}`}`);
  });
  const free = (line) => !exempt.has(line);
  // S2 header
  const hd = parseHeader(lines);
  if (hd.sheet == null || hd.motion == null) {
    const miss = [hd.sheet == null && '// motion-sheet:', hd.motion == null && '// motion:'].filter(Boolean).join(' and ');
    add('S2', lv('FAIL'), null, `no ${miss} header in the first 15 lines (motion-library «How to use»)`);
  }
  // S3 citations
  const cites = hd.motion != null ? splitCites(hd.motion).map(parseCite) : [];
  const ids = cites.filter((c) => c.kind === 'id').map((c) => c.key);
  const resolved = [];
  for (const c of cites) {
    if (c.kind === 'none') continue;
    if (c.kind === 'text') { add('S3', 'NOTE', hd.motionLine, `«${clip(c.raw, 60)}» is not an id or a citation (ignored)`); continue; }
    if (c.kind === 'recipe') { if (!ctx.recipes.has(c.key)) add('S3', lv('FAIL'), hd.motionLine, `unknown recipe «shot-recipes: ${c.key}» (no **${c.key}** in shot-recipes.md)`); continue; }
    if (c.kind === 'style') { if (!ctx.styles.has(c.key.toLowerCase())) add('S3', lv('FAIL'), hd.motionLine, `unknown style «mg-styles: ${c.key}» (no **${c.key}** in mg-styles.md)`); continue; }
    if (!ctx.lib.ok) { ctx.needLibrary = true; continue; }
    const e = ctx.lib.ids.get(c.key);
    if (!e) add('S3', lv('FAIL'), hd.motionLine, `unknown id ${c.key} (not in ${path.basename(ctx.lib.path)})`);
    else if (e.retired) add('S3', lv('FAIL'), hd.motionLine, `retired id ${c.key}: ${e.reason || 'see «Retired»'}`);
    else {
      resolved.push(e);
      if (e.pending) add('S3', 'NOTE', hd.motionLine, `${c.key} is pending: it needs the client's word before it is used`);
      if (e.signature) add('S3', 'NOTE', hd.motionLine, `${c.key} is a signature: reuse its helper only; the look is an earlier film's idea (script-writing §1)`);
      if (e.kind === 'PENDING-LIB') add('S3', 'NOTE', hd.motionLine, `${c.key} has no call yet (PENDING-LIB ${e.module}): build it from its home and Origin line`);
    }
  }
  // S4 calls of cited LIB / EXISTING entries, in full or through a local name (const EZ = T3.EZ, const { arrive } = T3.mv)
  const codeB = blankStrings(code), A = t3Aliases(codeB);
  const calledHere = (e) => e.calls.some((call) => {
    const p = call.replace(/\.\*$/, ''), parts = p.split('.');
    if (parts[0] !== 'T3') return new RegExp(`(?<![\\w$])${escRe(p)}(?![\\w$])`).test(codeB);
    if (usesPath(A, codeB, p)) return true;
    // a curve named in a string: T3.EZ.at(f, f0, dur, 'snap'), EZ.get('snap')
    return parts.length === 3 && parts[1] === 'EZ'
      && new RegExp(`(?:${pathRe(A, 'T3.EZ.at')}|${pathRe(A, 'T3.EZ.get')})\\s*\\([^)]*["'\`]${escRe(parts[2])}["'\`]`).test(code);
  });
  for (const e of resolved) {
    if (e.kind !== 'LIB' && e.kind !== 'EXISTING') continue;
    if (!calledHere(e)) add('S4', 'NOTE', hd.motionLine, `${e.id} is cited but ${e.calls.join(' / ') || e.module} is never called here (a citation proves citing, not use)`);
  }
  // … and the other way: a move entry's call made here whose id the header leaves out (the sheet cannot trace that move).
  // Curves are not moves: curve.* and the entries whose call is a T3.EZ curve (move.pop, move.drift) are never asked for.
  if (!legacy && hd.motion != null && ctx.lib.ok) {
    const cited = new Set(ids), uncited = [];
    for (const e of ctx.lib.ids.values()) {
      if ((e.kind !== 'LIB' && e.kind !== 'EXISTING') || e.retired || cited.has(e.id) || e.id.startsWith('curve.')) continue;
      const calls = e.calls.filter((c) => /^T3\./.test(c) && !/^T3\.EZ\b/.test(c));
      if (calls.length && calledHere({ calls })) uncited.push(`${e.id} (${calls.join(' / ')})`);
    }
    if (uncited.length) add('S4', 'NOTE', hd.motionLine, `called here, not in the // motion: header: ${uncited.join(', ')}; add the ids, and their rows to the sheet (motion-library «How to use»)`);
  }
  // S5 hand-written eases
  const defs = easeDefs(code, starts), bodies = defs.map((d) => d.body);
  const inBody = (pos) => bodies.some(([a, b]) => pos >= a && pos < b);
  const s5 = { defs: [], calls: 0, symmetricCalls: [], unused: [], inline: [], local: [], pragma: 0 };
  for (const d of defs) {
    if (!free(d.line)) { s5.pragma++; continue; }
    const re = d.prop ? new RegExp(`(?<!T3\\.EZ)\\.${d.name}\\s*\\(`, 'g') : new RegExp(`(?<![\\w$.])${d.name.replace(/\$/g, '\\$')}(?![\\w$])`, 'g');
    const callLines = []; let refs = 0;
    for (const m of code.matchAll(re)) {
      if (m.index === d.pos || (!d.prop && Math.abs(m.index - d.pos) < 2)) continue;
      const after = code.slice(m.index + m[0].length, m.index + m[0].length + 3);
      if (!d.prop && /^\s*=(?![=>])/.test(after)) continue;                 // reassignment
      refs++;
      const isCall = d.prop || /^\s*\(/.test(after);
      if (!isCall) continue;
      const ln = lineAt(starts, m.index);
      if (!free(ln)) { s5.pragma++; continue; }
      callLines.push(ln);
    }
    s5.defs.push({ name: d.name, line: d.line, kinds: d.kinds, symmetric: d.symmetric, calls: callLines.length });
    s5.calls += callLines.length;
    if (d.symmetric) s5.symmetricCalls.push(...callLines);
    if (!refs) s5.unused.push(d);
    else if (callLines.length) add('S5', 'NOTE', d.line, `hand-written ease ${d.name} (${d.kinds.join(', ')}${d.symmetric ? ', symmetric in-out' : ''}): ${callLines.length} call(s) at ${callLines.map((l) => ':' + l).join(' ')} → use T3.EZ.<name>`);
  }
  if (s5.unused.length) add('S5', 'NOTE', s5.unused[0].line, `defined, never used: ${s5.unused.map((d) => `${d.name} (:${d.line})`).join(', ')} → delete`);
  if (s5.symmetricCalls.length) add('S5', 'NOTE', null, `symmetric in-out curves on ${s5.symmetricCalls.length} move(s) at ${[...new Set(s5.symmetricCalls)].sort((a, b) => a - b).map((l) => ':' + l).join(' ')}: an arrival is front-loaded, an exit speeds up (style-grammar §6b)`);
  for (const m of code.matchAll(/([\w$.]+)\s*\*\s*\1\s*\*\s*\(\s*3\s*-\s*2\s*\*\s*\1\s*\)/g)) {
    if (inBody(m.index)) continue;
    const ln = lineAt(starts, m.index);
    if (!free(ln)) { s5.pragma++; continue; }
    s5.inline.push(ln); add('S5', 'NOTE', ln, `inline smoothstep (symmetric in-out) → T3.EZ.<name>`);
  }
  for (const t of localEaseTables(code)) {
    let n = 0; const ls = new Set();
    for (const m of code.matchAll(new RegExp(`(?<![\\w$.])${t.name.replace(/\$/g, '\\$')}\\.([A-Za-z_$][\\w$]*)\\s*\\(`, 'g'))) {
      if (GSAP_API.has(m[1])) continue;
      const ln = lineAt(starts, m.index); if (!free(ln)) continue; n++; ls.add(ln);
    }
    if (n) { s5.local.push({ name: t.name, calls: n, line: lineAt(starts, t.pos) }); add('S5', 'NOTE', lineAt(starts, t.pos), `project-local ease table ${t.name} (${n} calls) → use T3.EZ (lib/motion/ez.js; same names)`); }
  }
  // curve sources (report only): calls in full or through a local name, never in a comment or a string
  const cnt = (re) => (codeB.match(re) || []).length;
  const src_ = { ez: callsThrough(A, codeB, 'T3.EZ'), mv: callsThrough(A, codeB, 'T3.mv'), gsap: cnt(/\bgsap\.(?:parseEase|to|from|fromTo|timeline)\s*\(|\bCustomEase\.create\s*\(|\bT3\.gsapTimeline\s*\(/g) };
  // S6 explicit linear
  const destr = (nm) => new RegExp(`\\{[^{}]*\\b${nm}\\b[^{}]*\\}\\s*=\\s*(?:window\\.)?T3\\b`).test(code);
  const s6 = [];
  const linRe = destr('ease') ? /\bT3\.ease\.linear\b|(?<![\w$.])ease\.linear\b/g : /\bT3\.ease\.linear\b/g;
  for (const m of code.matchAll(linRe)) { const ln = lineAt(starts, m.index); if (free(ln)) s6.push([ln, 'T3.ease.linear']); }
  for (const m of code.matchAll(/\bease\s*:\s*(["'`])(none|linear)\1/g)) { const ln = lineAt(starts, m.index); if (free(ln)) s6.push([ln, `ease: '${m[2]}'`]); }
  const tabRe = destr('tab') ? /\bT3\.tab\s*\(|(?<![\w$.])tab\s*\(/g : /\bT3\.tab\s*\(/g;
  for (const m of code.matchAll(tabRe)) {
    const open = m.index + m[0].length - 1, close = matchClose(code, open), args = code.slice(open + 1, close);
    const comma = exprEnd(args, 0); if (args[comma] !== ',') continue;
    let a = comma + 1; while (/\s/.test(args[a] || '')) a++;
    if (args[a] !== '[') continue;
    const arr = args.slice(a + 1, matchClose(args, a)); let keys = 0, depth = 0;
    for (const c of arr) { if (c === '[') { if (depth === 0) keys++; depth++; } else if (c === ']') depth--; }
    const ln = lineAt(starts, m.index), stmt = lines[ln - 1] || '';
    if (keys >= 3 && /opacity|transform|translate|scale|rotate|left|top|\bx\b|\by\b|width|height/i.test(stmt) && free(ln)) s6.push([ln, `T3.tab with ${keys} keys`]);
  }
  for (const [ln, what] of s6.sort((x, y) => x[0] - y[0])) add('S6', 'NOTE', ln, `${what}: a constant-speed move → a T3.EZ curve (or a motion-ok pragma for a mechanism)`);
  // S7 per-frame tables
  const s7 = frameTables(code, starts).filter((t) => free(t.line));
  for (const t of s7) add('S7', 'NOTE', t.line, `per-frame table (${t.n} values, ${t.how}, indexed by [${clip(t.idx, 40)}]) → a T3.EZ curve, or a pragma (blink, flick, measured) with its reason`);
  // S10 a hit built by hand, in a strict segment that cites none of the library's hit entries and calls neither T3.shake
  // (in full or through a local name) nor another layer's shake (DZ.shake(…), a bare shake(…) it does not define); a
  // shake the file writes for itself (function shake, shake = …) clears nothing. The test covers the whole file.
  let s10 = [];
  if (!legacy && !ids.some((id) => id === 'type.slam' || id === 'fx.shake' || id === 'fx.impact')
    && !usesPath(A, codeB, 'T3.shake')
    && !(/\bshake\s*\(/.test(codeB) && !/\bfunction\s+shake\b|(?<![\w$.])shake\s*=(?![=>])/.test(codeB))) s10 = handHits(code, codeB, starts);
  if (s10.length) {
    const h = s10[0], more = s10.length > 1 ? ` (and ${s10.length - 1} more: ${s10.slice(1, 4).map((x) => ':' + x.line).join(' ')})` : '';
    add('S10', 'NOTE', h.line, `a hit built by hand: scale ${h.from} → 1 with a full-frame light fill at :${h.flashLine} in the same function${more}, and no library hit move here: look up type.slam, fx.shake (T3.shake), fx.radial (T3.blur.radial) and move.settle by id and use them (shakes per intro: house-style §6), or give the reason in the motion sheet (motion-library «How to use»)`);
  }
  // probes and register ids
  const { probes, regIds } = idents(code);
  const moving = ids.some((id) => !id.startsWith('locked.')) || cites.some((c) => c.kind === 'recipe' || c.kind === 'style');
  if (!legacy && moving && !probes.length) add('R3', 'NOTE', null, 'no T3.motionProbe here: --curves will fail this segment (motion-library «Curve sheet»: ≥ 3 probes)');
  else if (!legacy && moving && probes.length < 3) add('R3', 'NOTE', null, `${probes.length} T3.motionProbe call(s): the curve sheet wants ≥ 3 (an arrival, an exit, a camera or transition move)`);
  // S8 the motion sheet
  if (!legacy && hd.sheet == null) add('S8', 'FAIL', null, 'no motion sheet: name it on a `// motion-sheet:` line and write it before the code (motion-library «Motion sheet»)');
  if (!legacy && hd.sheet != null) {
    const want = hd.sheet.replace(/^`|`$/g, '').trim();
    let text = null, where = want;
    if (/^inline$/i.test(want)) {
      const blk = /\/\*[\s*]*motion[ -]sheet\b[\s\S]*?\*\//i.exec(src);
      // a table row: 7 cells (6 inner pipes; outer pipes and a leading " * " optional), not the |---| rule; header + a data row
      const rows = blk ? blk[0].split(/\r?\n/).map((l) => l.replace(/^\s*\*?\s?/, '').trim().replace(/^\||\|$/g, ''))
        .filter((l) => (l.match(/\|/g) || []).length >= 6 && !/^[\s|:-]+$/.test(l)) : [];
      if (!blk) add('S8', 'FAIL', hd.sheetLine, '`// motion-sheet: inline` but no /* motion sheet … */ block in the file');
      else if (rows.length < 2) add('S8', 'FAIL', hd.sheetLine, 'the inline motion sheet has no table with the 7 columns (moment · element · frames · id · ease · stagger/settle · departure)');
      else text = blk[0];
      where = 'inline block';
    } else if (!want) add('S8', 'FAIL', hd.sheetLine, '`// motion-sheet:` names no file');
    else {
      const cands = path.isAbsolute(want) ? [want] : [path.join(ctx.projectRoot, want), path.join(ctx.pageDir, want)];
      const hit = cands.find((p) => exists(p) && fs.statSync(p).isFile());
      if (!hit) add('S8', 'FAIL', hd.sheetLine, `motion sheet ${want} not found (looked in ${cands.map((c) => path.dirname(c)).filter((v, i, a) => a.indexOf(v) === i).join(', ')})`);
      else { text = readText(hit); where = hit; if (!text.trim()) { add('S8', 'FAIL', hd.sheetLine, `motion sheet ${want} is empty`); text = null; } }
    }
    if (text) {
      const missing = cites.filter((c) => c.kind === 'id' || c.kind === 'recipe' || c.kind === 'style').filter((c) => {
        const k = c.key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        return !new RegExp(`(^|[^\\w.-])${k}($|[^\\w-])`, 'i').test(text);
      }).map((c) => c.key);
      if (missing.length) add('S8', 'NOTE', hd.sheetLine, `header ids missing from the motion sheet (${path.basename(where)}): ${missing.join(', ')}`);
    }
  }
  return { file, name, mode: ctx.mode, modeWhy: ctx.modeWhy, findings: F, pragmas, header: hd, cites, ids, s5, s6: s6.length, s7, s10, src: src_, probes, regIds, moving };
}

// ---------------------------------------------------------------------------------------------------- the static scan
/**
 * Static scan of a page (S1–S10). Synchronous, prints nothing, never throws.
 * page: index.html (or null in hook mode with opts.segments); opts: { segments: [name|path] (an array, even empty, is
 * the scope; null = the page's own), scope (text: the list was derived by qa, see segmentsOnScreen), strict, skill,
 * library, legacyList, webDir } → { page, pageDir, mode, modeText, scope: { kind: page|named|span, text }, segments,
 * others (the page's segments outside the scope: name, regIds, probes), findings, fails, notes, pragmas, needLibrary, ms, error }
 */
export function staticScan(page, opts = {}) {
  const t0 = Date.now(), P = paths(opts);
  const res = { page: page ? path.resolve(page) : null, pageDir: null, projectRoot: null, mode: 'strict', modeText: '', legacy: null, optOut: null,
    segments: [], findings: [], fails: 0, notes: 0, pragmas: [], library: null, needLibrary: false, strictPage: true, ms: 0, error: null,
    scope: null, others: [] };
  try {
    const pageDir = page ? path.dirname(path.resolve(page)) : path.resolve(opts.webDir || '.');
    res.pageDir = pageDir;
    res.projectRoot = /^web$/i.test(path.basename(pageDir)) ? path.dirname(pageDir) : pageDir;
    const lib = loadLibrary(P.library), recipes = loadRecipes(P.recipes), styles = loadStyles(P.styles), opening = openingNames();
    res.library = { ok: lib.ok, path: lib.path, ids: lib.ids.size };
    const pg = page ? parsePage(path.resolve(page)) : null;
    // which segments: opts.segments (an array, even an empty one) or the page's own. A file the caller named that does
    // not exist is a FAIL (a typo must not pass as "nothing to check"); opts.scope marks a list qa derived itself.
    const named = Array.isArray(opts.segments), callerNamed = named && !opts.scope, asked = new Map();
    let files;
    if (named) {
      files = opts.segments.map((s) => {
        let f, looked;
        if (path.isAbsolute(s)) { f = path.resolve(s); looked = [f]; }
        else if (/[\\/]/.test(s)) { const w = path.resolve(pageDir, s), c = path.resolve(s); f = exists(w) ? w : exists(c) ? c : w; looked = [w, c]; }   // web-relative first (build.js passes segments/x.js)
        else { const a = path.join(pageDir, 'segments', s), b = path.join(pageDir, s); f = exists(a) ? a : exists(b) ? b : a; looked = [a, b]; }
        if (!asked.has(f)) asked.set(f, { arg: s, looked: [...new Set(looked)] });
        return f;
      });
    } else files = pg ? pg.segs.map((s) => s.abs) : [];
    files = [...new Set(files)];
    res.scope = opts.scope ? { kind: 'span', text: String(opts.scope) }
      : named ? { kind: 'named', text: `--segments ${opts.segments.join(', ') || '(none)'}` } : { kind: 'page', text: 'the segments the page loads' };
    // the page's other segments, by name only: the curve sheet leaves their probes out (one sheet per caller)
    if (named && pg) {
      const mine = new Set(files.map(normP)), seen = new Set();
      for (const s of pg.segs) {
        const k = normP(s.abs);
        if (mine.has(k) || seen.has(k) || !exists(s.abs)) continue;
        seen.add(k);
        try { res.others.push(Object.assign({ name: path.basename(s.abs), file: s.abs }, idents(stripJsComments(readText(s.abs))))); } catch {}
      }
    }
    // mode
    const entry = legacyEntry(pageDir, opts);
    res.optOut = !opts.strict && pg && pg.optOut ? pg.optOut : null;
    res.legacy = !opts.strict && entry ? entry : null;
    const segInfo = files.map((f) => {
      const name = path.basename(f);
      if (isExempt(name, opening)) return { file: f, name, exempt: true, mode: 'exempt' };
      if (!exists(f)) return { file: f, name, missing: true, mode: 'missing', asked: callerNamed ? asked.get(f) || null : null };
      if (opts.strict) return { file: f, name, mode: 'strict', modeWhy: '--strict' };
      if (res.optOut) return { file: f, name, mode: 'legacy', modeWhy: 'LEGACY by opt-out: ' + res.optOut };
      if (entry) {
        const mt = fs.statSync(f).mtimeMs;
        if (mt <= entry.cutoff) return { file: f, name, mode: 'legacy', modeWhy: `legacy list: ${entry.prefix} (${entry.until || entry.date})` };
        return { file: f, name, mode: 'strict', modeWhy: `changed ${localTime(mt)} after the legacy cutoff ${entry.until || entry.date}` };
      }
      return { file: f, name, mode: 'strict', modeWhy: 'not on the legacy list' };
    });
    const nStrict = segInfo.filter((s) => s.mode === 'strict').length;
    // page-level checks bind only a page with at least one strict (non-exempt) segment: a page with zero strict segments carries no motion of its own, so its S1/R1 are notes
    res.strictPage = nStrict > 0;
    res.mode = opts.strict ? 'strict' : res.optOut ? 'opt-out' : entry ? (nStrict ? 'mixed' : 'legacy') : 'strict';
    res.modeText = opts.strict ? 'strict (--strict)' : res.optOut ? `LEGACY by opt-out: ${res.optOut}` : entry
      ? (nStrict ? `legacy page with ${nStrict} strict segment(s) (changed after ${entry.until || entry.date})` : `legacy page (${clip(entry.reason, 70)}; until ${entry.until || entry.date})`)
      : 'strict page';
    if (res.mode === 'strict' && !nStrict) res.modeText += ' (no segment of its own to check: page checks are notes)';
    // S1. The libraries must load before the first segment that is checked strictly (locked and legacy segments never
    // call T3.EZ), so an old film's page passes once the tags sit after its GSAP tags and before the new segment.
    if (pg) {
      const pageLevel = res.strictPage ? 'FAIL' : 'NOTE', srcs = pg.scripts.map((s) => s.src);
      const isMode = (m) => (s) => segInfo.some((g) => g.mode === m && normP(g.file) === normP(s.abs));
      let firstSeg = pg.scripts.findIndex(isMode('strict'));
      if (firstSeg < 0) firstSeg = pg.scripts.findIndex(isMode('legacy'));
      if (firstSeg < 0) firstSeg = pg.scripts.findIndex((s) => pg.segs.includes(s));
      const need = [['lib/gsap/gsap.min.js', /(^|\/)gsap(\.min)?\.js$/], ['CustomEase.min.js', /(^|\/)CustomEase(\.min)?\.js$/], ['lib/gsap-bridge.js', /(^|\/)gsap-bridge\.js$/], ['lib/motion/ez.js', /(^|\/)motion\/ez\.js$/]];
      const missing = [], late = [];
      for (const [label, re] of need) {
        const at = srcs.findIndex((s) => re.test(s));
        if (at < 0) missing.push(label); else if (firstSeg >= 0 && at > firstSeg) late.push(`${label} (:${pg.scripts[at].line})`);
      }
      if (missing.length || late.length) res.findings.push({ check: 'S1', level: pageLevel, file: path.basename(page), line: null,
        msg: [missing.length && `not loaded: ${missing.join(', ')}`, late.length && `after the first segment ${pg.scripts[firstSeg].src} (:${pg.scripts[firstSeg].line}): ${late.join(', ')}`].filter(Boolean).join('; ') + ' (motion-library «Setup»)' });
      // S9. Every lib/motion module of the template's, present, current and loaded: a project copied before a module
      // was added, or a copy taken before the template's module grew, leaves the moves it lacks unloaded, and a segment
      // revised later reaches for them. Same page policy as S1; a differing copy or a late tag is a WARN. A page with no
      // strict segment hears of it only once its project has begun on the library (a lib/motion tag or the folder): an
      // archived film from before the library has S1's note and nothing more.
      const st = libMotionState(pg, P, firstSeg);
      if (st && (res.strictPage || st.begun)) {
        const fwd = (p) => p.replace(/\\/g, '/'), jsq = (p) => fwd(p).replace(/'/g, "\\'"), rel = (p) => fwd(path.relative(pg.baseDir, p));
        const all = st.missing.length === st.order.length;
        // the whole folder through node (bash and PowerShell alike; creates lib/ when the page has none, never nests)
        const cp = (ns) => (all && ns === st.missing ? `node -e "require('fs').cpSync('${jsq(st.tplDir)}', '${jsq(st.dir)}', { recursive: true })"`
          : ns.map((n) => `cp '${fwd(path.join(st.tplDir, n))}' '${fwd(st.dir)}/'`).join('; '));
        const at = rel(st.dir) === 'lib/motion' ? '' : ` (${rel(st.dir) || '.'})`;
        const need = st.order.filter((n) => st.missing.includes(n) || st.unloaded.includes(n));   // the template's tag order
        if (need.length) {
          const tagsTxt = need.filter((n) => !pg.scripts.some((s) => normP(s.abs) === normP(path.join(st.dir, n)))).map((n) => `<script src="${rel(path.join(st.dir, n))}"></script>`).join(' ');
          res.findings.push({ check: 'S9', level: pageLevel, file: path.basename(page), line: null, wide: true, msg: [
            `lib/motion${at} incomplete (the template ships ${st.order.map((n) => n.replace(/\.js$/i, '')).join(', ')})`,
            st.missing.length && (all ? `the folder is missing: copy the template's in (${cp(st.missing)})`
              : `missing ${st.missing.join(', ')}: copy ${st.missing.length > 1 ? 'them' : 'it'} from the template (${cp(st.missing)})`),
            st.unloaded.length && `not loaded by the page: ${st.unloaded.join(', ')}`,
            tagsTxt && `then load ${tagsTxt} beside the page's other lib/motion tags, before the first segment, in the template's order`,
          ].filter(Boolean).join('; ') + ' (motion-library «Setup»)' });
        }
        if (st.differs.length || st.late.length) res.findings.push({ check: 'S9', level: res.strictPage ? 'WARN' : 'NOTE', file: path.basename(page), line: null, wide: true, msg: [
          st.differs.length && `lib/motion${at} differs from the template's: ${st.differs.join(', ')} (older, or edited in this project: diff it; to take the template's: ${cp(st.differs)})`,
          st.late.length && `lib/motion loaded after the first segment ${pg.scripts[firstSeg].src} (:${pg.scripts[firstSeg].line}): ${st.late.join(', ')} (a segment that takes these names when it loads gets undefined: move the tags up)`,
        ].filter(Boolean).join('; ') + ' (motion-library «Setup»)' });
      }
    }
    // segments
    const ctx = { lib, recipes, styles, projectRoot: res.projectRoot, pageDir, needLibrary: false };
    for (const s of segInfo) {
      if (s.exempt || s.missing) {
        res.segments.push(s);
        if (s.missing) res.findings.push(s.asked
          ? { check: 'S2', level: 'FAIL', file: s.name, line: null, msg: `segment file not found: --segments names ${s.asked.arg}, but no such file exists; check the name, or leave it out of --segments until it is written (looked for ${s.asked.looked.join(', ')})` }
          : { check: 'S2', level: 'NOTE', file: s.name, line: null, msg: 'segment file not found' });
        continue;
      }
      const r = scanSegment(s.file, Object.assign(ctx, { mode: s.mode, modeWhy: s.modeWhy }));
      res.segments.push(r); res.findings.push(...r.findings); res.pragmas.push(...r.pragmas);
    }
    res.needLibrary = ctx.needLibrary;
    if (ctx.needLibrary) res.findings.push({ check: 'S3', level: res.strictPage ? 'FAIL' : 'NOTE', file: path.basename(P.library), line: null, msg: `library index not found (${P.library}): cited ids cannot be resolved` });
  } catch (e) {
    res.error = String((e && e.stack) || e);
    res.findings.push({ check: '--', level: 'NOTE', file: '(motion_lint)', line: null, msg: 'internal error, scan incomplete: ' + clip(String((e && e.message) || e), 160) });
  }
  recount(res);
  res.ms = Date.now() - t0;
  return res;
}

/**
 * qa's scope for a span of the film, when its caller names no segments: the page's segments whose T3.register id was on
 * screen (ids: the engine layers shown in the span, #stage > [data-seg]). A segment that registers an id that is not a
 * literal is kept, since it cannot be told apart; one that registers nothing (a file still being written) is left out.
 * Exempt segments are left out. Throws on an unreadable page. → { files, kept: [names kept without a literal id], left: [names] }
 */
export function segmentsOnScreen(page, ids, opts = {}) {
  const P = paths(opts), opening = openingNames(), on = new Set(ids), out = { files: [], kept: [], left: [] }, seen = new Set();
  for (const s of parsePage(path.resolve(page)).segs) {
    const k = normP(s.abs), name = path.basename(s.abs);
    if (seen.has(k) || isExempt(name, opening) || !exists(s.abs)) continue;
    seen.add(k);
    let id = null; try { id = idents(stripJsComments(readText(s.abs))); } catch {}
    if (!id) { out.files.push(s.abs); out.kept.push(name); continue; }            // unreadable: the lint reports it
    const hit = id.regIds.some((r) => on.has(r)), unsure = id.regCalls > id.regIds.length;
    if (hit || unsure) { out.files.push(s.abs); if (!hit) out.kept.push(name); } else out.left.push(name);
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------- report text
/** res.fails, res.warns, res.notes from res.findings */
function recount(res) {
  res.fails = res.findings.filter((f) => f.level === 'FAIL').length;
  res.warns = res.findings.filter((f) => f.level === 'WARN').length;
  res.notes = res.findings.filter((f) => f.level === 'NOTE').length;
}
const tally = (res, lower = false) => (lower ? `${res.fails} fail${res.warns ? ` / ${res.warns} warn` : ''} / ${res.notes} notes` : `${res.fails} FAIL${res.warns ? ` / ${res.warns} WARN` : ''} / ${res.notes} NOTE`);
const LEVEL_ORDER = { FAIL: 0, WARN: 1, NOTE: 2 };
const fmt = (f) => clip(`${f.level} ${f.check} ${f.file}${f.line ? ':' + f.line : ''}: ${f.msg}`, f.wide ? 2000 : 230);   // S9 keeps its copy commands and tags
function noteDigest(res) {
  const out = [];
  for (const s of res.segments) {
    if (!s.findings) continue;
    const notes = res.findings.filter((f) => f.level === 'NOTE' && f.file === s.name);   // its static notes and its R3 notes
    if (!notes.length) continue;
    const by = {}; for (const f of notes) by[f.check] = (by[f.check] || 0) + 1;
    const bits = [];
    if (s.s5 && (s.s5.defs.length || s.s5.inline.length || s.s5.local.length)) {
      const b = [];
      if (s.s5.calls) b.push(`${s.s5.defs.filter((d) => d.calls).length} hand eases ×${s.s5.calls} calls${s.s5.symmetricCalls.length ? ` (${s.s5.symmetricCalls.length} symmetric)` : ''}`);
      if (s.s5.unused.length) b.push(`${s.s5.unused.length} unused`);
      if (s.s5.inline.length) b.push(`${s.s5.inline.length} inline smoothstep`);
      for (const t of s.s5.local) b.push(`local ${t.name}.* ×${t.calls}`);
      bits.push('S5 ' + b.join(', '));
    }
    if (s.s6) bits.push(`S6 ${s.s6} linear`);
    if (s.s7 && s.s7.length) bits.push(`S7 ${s.s7.length} frame table(s) ${s.s7.map((t) => ':' + t.line).join(' ')}`);
    if (s.s10 && s.s10.length) bits.push(`S10 hand-built hit :${s.s10[0].line} (look up type.slam, fx.shake)`);
    for (const k of Object.keys(by).sort()) if (!['S5', 'S6', 'S7', 'S10'].includes(k)) bits.push(`${k} ×${by[k]}`);
    out.push(clip(`NOTE ${s.name} [${s.mode}]: ${bits.join('; ')}`));
  }
  const pageNotes = res.findings.filter((f) => f.level === 'NOTE' && !res.segments.some((s) => s.name === f.file && s.findings));
  if (pageNotes.length) out.push(clip(`NOTE page: ${pageNotes.map((f) => `${f.check} ${f.msg}`).join(' · ')}`));
  return out;
}
/** the <= 8 summary lines */
export function summaryLines(res, reportPath = null) {
  const segs = res.segments, n = (m) => segs.filter((s) => s.mode === m).length;
  const head = `motion_lint ${res.page || res.pageDir}: ${res.modeText} · ${segs.length} segment(s): ${n('strict')} strict, ${n('legacy')} legacy, ${n('exempt')} exempt · ${tally(res)}`;
  const body = [...['FAIL', 'WARN'].flatMap((lv) => res.findings.filter((f) => f.level === lv).map(fmt)), ...noteDigest(res)];
  const room = 8 - 1 - (reportPath ? 1 : 0), L = [clip(head, 300)];
  if (body.length > room) { L.push(...body.slice(0, room - 1), `… ${body.length - room + 1} more line(s) in the report`); } else L.push(...body);
  if (reportPath) L.push(`report: ${reportPath}`);
  return L;
}
/** the full report (lint.txt) */
export function reportText(res, extra = []) {
  const L = [`motion_lint ${res.page || res.pageDir}   ${new Date().toISOString()}   (${res.ms} ms static)`, `mode: ${res.modeText}`];
  if (res.scope && res.scope.kind !== 'page') L.push(`scope: ${res.scope.text}${res.others && res.others.length ? ` (the page's ${res.others.length} other segment(s) not checked)` : ''}`);
  if (res.legacy) L.push(`legacy entry: ${res.legacy.prefix} · ${res.legacy.until || res.legacy.date} · ${res.legacy.reason}`);
  L.push(`library: ${res.library ? `${res.library.path} (${res.library.ids} ids)${res.library.ok ? '' : ' MISSING'}` : '?'}`);
  L.push('', 'segments:');
  for (const s of res.segments) {
    if (s.exempt) { L.push(`  ${s.name}  exempt (locked, config only)`); continue; }
    if (s.missing) { L.push(`  ${s.name}  file not found`); continue; }
    L.push(`  ${s.name}  ${s.mode} (${s.modeWhy})  sheet: ${s.header.sheet ?? '—'}  ids: ${s.ids.join(', ') || '—'}  probes: ${s.probes.length}`);
    L.push(`      curve source: T3.EZ ×${s.src.ez}, T3.mv ×${s.src.mv}, GSAP ×${s.src.gsap}, hand eases ${s.s5.defs.length} def / ${s.s5.calls} calls, inline smoothstep ${s.s5.inline.length}, local tables ${s.s5.local.map((t) => `${t.name} ×${t.calls}`).join(', ') || '0'}, linear ${s.s6}, frame tables ${s.s7.length}${s.s5.pragma ? `, ${s.s5.pragma} under pragmas` : ''}`);
  }
  L.push('', `findings: ${tally(res)}`);
  for (const f of [...res.findings].sort((a, b) => (LEVEL_ORDER[a.level] ?? 3) - (LEVEL_ORDER[b.level] ?? 3))) L.push('  ' + `${f.level} ${f.check} ${f.file}${f.line ? ':' + f.line : ''}: ${f.msg}`);
  L.push('', `pragmas (${res.pragmas.length}):`);
  for (const p of res.pragmas) L.push(`  ${p.file}:${p.line}  ${p.kind || '?'}  ${p.reason || '(no reason)'}${p.ok ? '' : '  — exempts nothing'}`);
  if (extra.length) L.push('', ...extra);
  if (res.error) L.push('', 'internal error:', res.error);
  return L.join('\n') + '\n';
}
/** the one line snap / render_fast print for every page they open (_cdp.mjs); rt = runtimeState(pg) or null */
export function motionLine(res, rt = null) {
  const cmd = `node ${SELF.replace(/\\/g, '/')}`;           // the full path: the line is read in a project folder
  const g = rt ? (rt.gsap && rt.customEase && rt.ez && rt.seek ? 'GSAP ok' : `GSAP/T3.EZ missing (${missingParts(rt).join(', ')})`) : 'GSAP not checked';
  const page = res.page || res.pageDir;
  if (res.mode === 'legacy' || res.mode === 'opt-out') return `motion: legacy page (${res.mode === 'opt-out' ? res.modeText : clip(res.legacy.reason, 60) + '; until ' + (res.legacy.until || res.legacy.date)}), lint ${tally(res, true)} (${cmd} ${page})`;
  // a page with no strict segment of its own (the locked opening, section card and outro, a dashboard-only page) needs no
  // GSAP: say so instead of reporting it missing
  if (!res.strictPage) return `motion: ${res.modeText}, lint ${tally(res, true)} (${cmd} ${page})`;
  return `motion: ${res.mode === 'mixed' ? res.modeText : 'strict page'}, ${g}, lint ${tally(res, true)} (${cmd} ${page})`;
}
const missingParts = (rt) => [!rt.gsap && 'gsap', !rt.customEase && 'CustomEase', !rt.ez && 'T3.EZ', !rt.seek && 'T3.gsapSeek'].filter(Boolean);

// ---------------------------------------------------------------------------------------------------- runtime (R1, R3)
const RT_JS = `(() => { const T = window.T3 || (typeof T3 !== 'undefined' ? T3 : null); let m = null;
  try { m = window.__T3_MOTION ? JSON.parse(JSON.stringify(window.__T3_MOTION)) : null; } catch (e) {}
  return { gsap: typeof window.gsap !== 'undefined' && !!window.gsap, customEase: typeof window.CustomEase !== 'undefined' && !!window.CustomEase,
    ez: !!(T && T.EZ), seek: !!(T && T.gsapSeek), probe: !!(T && T.motionProbe), mv: !!(T && T.mv), motion: m, ready: window.T3_READY === true }; })()`;
/** what the page has loaded: { gsap, customEase, ez, seek, probe, mv, motion, ready } (pg = an open _cdp.mjs page) */
export async function runtimeState(pg) {
  try { return (await pg.evaluate(RT_JS)) || null; } catch { return null; }
}
/** R1 on an open page: adds its finding to res (FAIL on a strict page, nothing on an all-legacy page) */
export async function lintRuntime(pg, res) {
  const rt = await runtimeState(pg);
  res.runtime = rt;
  if (!res.strictPage) return rt;
  const miss = rt ? missingParts(rt) : ['the page did not answer'];
  if (miss.length) {
    const why = rt && rt.motion && rt.motion.error ? ` (${clip(rt.motion.error, 120)})` : '';
    res.findings.push({ check: 'R1', level: 'FAIL', file: res.page ? path.basename(res.page) : '(page)', line: null, msg: `GSAP/T3.EZ not loaded at runtime: missing ${miss.join(', ')}${why}: motion-library «Setup»` });
    res.fails++;
  }
  return rt;
}
const PROBE_JS = `(() => { const T = window.T3 || (typeof T3 !== 'undefined' ? T3 : null); const mp = T && T.motionProbe;
  if (mp && typeof mp.all === 'function') { try { return { api: 'T3.motionProbe.all', probes: mp.all(0.25) }; } catch (e) { return { api: 'T3.motionProbe.all', error: String(e && e.message || e), probes: {} }; } }
  const reg = window.__T3_PROBES; if (!reg) return { api: 'none', probes: {} };
  const out = {}; const list = Array.isArray(reg) ? reg : Object.keys(reg).map((k) => Object.assign({ id: k }, reg[k]));
  for (const P of list) { const id = P.id;
    try { const rows = []; for (let f = P.f0; f <= P.f1 + 1e-9; f += 0.25) { const p = P.fn(f); rows.push(typeof p === 'number' ? { f, v: p } : Object.assign({ f }, p)); }
      out[id] = { f0: P.f0, f1: P.f1, meta: P.meta || null, samples: rows }; }
    catch (e) { out[id] = { f0: P.f0, f1: P.f1, meta: P.meta || null, error: String(e && e.message || e) }; } }
  return { api: '__T3_PROBES', probes: out }; })()`;

/** shape metrics of one probe's samples [{ f, x?, y?, s?, r?, o?, v? }] → { channel, kind, dur, q1, notes, … } */
export function probeMetrics(samples, { id = '', kind: kindIn = null } = {}, TH = R3_THRESHOLDS) {
  const rows = (samples || []).filter((r) => r && Number.isFinite(r.f)).sort((a, b) => a.f - b.f);
  const has = (k) => rows.some((r) => Number.isFinite(r[k]));
  const tracks = [];
  if (has('x') || has('y')) tracks.push(['pos', rows.map((r) => [r.x || 0, r.y || 0]), 1, 'px']);
  for (const [k, min, unit] of [['s', 0.002, 'scale'], ['r', 0.2, '°'], ['v', 1e-6, ''], ['o', 0.02, 'opacity']]) if (has(k)) tracks.push([k, rows.map((r) => [Number.isFinite(r[k]) ? r[k] : 0]), min, unit]);
  const dist = (a, b) => Math.hypot(...a.map((v, i) => v - b[i]));
  let main = null;
  for (const [ch, tr, min, unit] of tracks) {
    let tot = 0; for (let i = 1; i < tr.length; i++) tot += dist(tr[i], tr[i - 1]);
    if (tot > min) { main = { ch, tr, tot, unit }; break; }
  }
  const out = { channel: main ? main.ch : null, unit: main ? main.unit : null, kind: null, notes: [], travel: main ? main.tot : 0 };
  if (!main || rows.length < 3) { out.notes.push('no movement in the probe window'); return out; }
  const sp = [], fr = rows.map((r) => r.f);
  for (let i = 1; i < rows.length; i++) sp.push(dist(main.tr[i], main.tr[i - 1]) / Math.max(1e-9, fr[i] - fr[i - 1]));
  const vmax = Math.max(...sp), cum = [0]; for (let i = 0; i < sp.length; i++) cum.push(cum[i] + sp[i] * (fr[i + 1] - fr[i]));
  const tot = cum[cum.length - 1], i0 = cum.findIndex((c) => c >= 0.005 * tot), i1 = cum.findIndex((c) => c >= 0.995 * tot);
  const a = Math.max(0, i0 - 1), b = Math.max(a + 1, i1);                   // speeds a .. b-1 move
  const f0 = fr[a], f1 = fr[b], dur = f1 - f0;
  let ip = a; for (let i = a; i < b; i++) if (sp[i] > sp[ip]) ip = i;
  const peakPos = (fr[ip] - f0) / Math.max(1e-9, dur);
  const fq = f0 + dur / 4, at = (f) => { for (let i = 0; i < fr.length - 1; i++) if (fr[i + 1] >= f) { const u = (f - fr[i]) / Math.max(1e-9, fr[i + 1] - fr[i]); return cum[i] + (cum[i + 1] - cum[i]) * u; } return tot; };
  const q1 = (at(fq) - cum[a]) / Math.max(1e-12, tot);
  const startV = sp[a] / vmax, endV = sp[b - 1] / vmax;
  const hint = String(kindIn || '').toLowerCase() || (/arriv|land|enter|(^|[._-])in($|[._-])|rise|pop|title/i.test(id) ? 'arrive' : /exit|leave|(^|[._-])out($|[._-])|sink|throw/i.test(id) ? 'exit' : /cam|push|pan|dolly|zoom|trans|sheet|orbit|crane/i.test(id) ? 'camera' : '');
  const kind = /^arriv/.test(hint) ? 'arrive' : /^exit|^leave/.test(hint) ? 'exit' : hint ? hint : peakPos < 0.35 ? 'arrive' : peakPos > 0.65 ? 'exit' : 'move';
  Object.assign(out, { kind, f0: +f0.toFixed(2), f1: +f1.toFixed(2), dur: +dur.toFixed(2), q1: +q1.toFixed(3), vmax: +vmax.toFixed(3), startV: +startV.toFixed(3), endV: +endV.toFixed(3), peakPos: +peakPos.toFixed(3) });
  // constant-velocity runs
  // a run where the speed stays within constRelTol of itself for constRunF frames (a long sine's middle is not one)
  const runs = [];
  for (let i = a; i < b; ) {
    if (!(sp[i] > TH.constMinV * vmax)) { i++; continue; }
    let lo = sp[i], hi = sp[i], j = i;
    while (j + 1 < b && Math.max(hi, sp[j + 1]) <= (1 + TH.constRelTol) * Math.min(lo, sp[j + 1])) { j++; lo = Math.min(lo, sp[j]); hi = Math.max(hi, sp[j]); }
    const len = fr[j + 1] - fr[i];
    if (len >= TH.constRunF) { runs.push([+fr[i].toFixed(2), +len.toFixed(2)]); i = j + 1; } else i++;
  }
  // corners: an isolated jump in speed mid-move (the steep head of a snap changes fast but smoothly, so it is none)
  const corners = [];
  for (let i = a + 1; i < b; i++) {
    const d = Math.abs(sp[i] - sp[i - 1]), dp = i >= 2 ? Math.abs(sp[i - 1] - sp[i - 2]) : 0, dn = i + 1 < sp.length ? Math.abs(sp[i + 1] - sp[i]) : 0;
    if (sp[i - 1] > 0.05 * vmax && sp[i] > 0.05 * vmax && d > TH.cornerJump * vmax && d > 3 * Math.max(dp, dn)) corners.push(+fr[i].toFixed(2));
  }
  // dead stop (position only; an exit ends on the cut, so it is never one)
  let dead = null;
  if (main.ch === 'pos' && kind !== 'exit') for (let i = 0; i < sp.length && dead == null; i++) {
    if (sp[i] <= TH.deadStopPxF) continue;
    for (let j = i + 1; j < sp.length && fr[j] - fr[i + 1] <= 1 + 1e-9; j++) {
      if (sp[j] >= TH.deadStopRestPxF) continue;
      const rest = sp.slice(j, sp.length).filter((_, k) => fr[j + k] - fr[j] <= 4);
      if (rest.length >= 4 && Math.max(...rest) < 0.25) dead = +fr[j].toFixed(2);
      break;
    }
  }
  Object.assign(out, { constRuns: runs, corners: corners.slice(0, 20), cornerCount: corners.length, deadStop: dead });
  const N = out.notes;
  if (kind === 'arrive') {
    if (q1 < TH.q1ShareMin) N.push(`arrival puts ${(q1 * 100).toFixed(0)} % of its travel in the first quarter (< ${TH.q1ShareMin * 100} %)`);
    if (startV < TH.symStartV && peakPos >= 0.3 && peakPos <= 0.7) N.push('symmetric in-out arrival (starts from rest, peak mid-move)');
    if (dur < TH.arrivalMinF) N.push(`arrival over ${dur.toFixed(1)} f (< ${TH.arrivalMinF} f)`);
  }
  if (kind === 'exit' && endV < TH.exitEndV) N.push(`exit does not speed up into the cut (ends at ${(endV * 100).toFixed(0)} % of peak speed)`);
  if (runs.length) N.push(`constant velocity for ${runs.map(([f, l]) => `${l} f from f${f}`).join(', ')}`);
  if (dead != null) N.push(`dead stop at f${dead}: > ${TH.deadStopPxF} px/f to rest within 1 f, no settle`);
  if (corners.length) N.push(`${corners.length} velocity corner(s), first at f${corners[0]}`);
  return out;
}

function curvesSvg(list, title) {
  const W = 660, H = 250, cols = 2, pad = 16, rows = Math.max(1, Math.ceil(list.length / cols));
  const col = { x: '#2f6fec', y: '#e8572a', s: '#18a06c', r: '#9b51e0', o: '#8a8a8a', v: '#2f6fec' };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const out = [`<svg xmlns="http://www.w3.org/2000/svg" width="${cols * W}" height="${rows * H + 40}" font-family="Consolas,monospace" font-size="12">`,
    `<rect width="100%" height="100%" fill="#fff"/><text x="${pad}" y="24" font-size="15" font-weight="700">${esc(title)}</text>`];
  list.forEach((p, n) => {
    const ox = (n % cols) * W, oy = 40 + Math.floor(n / cols) * H, px = ox + 48, py = oy + 46, pw = W - 70, ph = H - 104;
    out.push(`<g><rect x="${ox + 6}" y="${oy + 4}" width="${W - 12}" height="${H - 8}" fill="none" stroke="#ddd"/>`);
    out.push(`<text x="${ox + 14}" y="${oy + 22}" font-weight="700">${esc(clip(`${p.id}${p.segment ? '  [' + p.segment + ']' : ''}`, 78))}</text>`);
    if (p.error || !p.samples || !p.samples.length) { out.push(`<text x="${px}" y="${py + 40}" fill="#c00">${esc(clip(p.error || 'no samples', 80))}</text></g>`); return; }
    const S = p.samples, fa = S[0].f, fb = S[S.length - 1].f, X = (f) => px + ((f - fa) / Math.max(1e-9, fb - fa)) * pw;
    out.push(`<rect x="${px}" y="${py}" width="${pw}" height="${ph}" fill="#fafafa" stroke="#ccc"/>`);
    const step = fb - fa > 60 ? 10 : fb - fa > 24 ? 4 : 1;
    for (let f = Math.ceil(fa); f <= fb; f += 1) {
      const major = (f - Math.ceil(fa)) % step === 0;
      out.push(`<line x1="${X(f).toFixed(1)}" y1="${py}" x2="${X(f).toFixed(1)}" y2="${py + ph}" stroke="${major ? '#ddd' : '#f0f0f0'}"/>`);
      if (major) out.push(`<text x="${X(f).toFixed(1)}" y="${py + ph + 13}" text-anchor="middle" fill="#888" font-size="10">${f}</text>`);
    }
    if (p.metrics && p.metrics.f0 != null) for (const f of [p.metrics.f0, p.metrics.f1]) out.push(`<line x1="${X(f).toFixed(1)}" y1="${py}" x2="${X(f).toFixed(1)}" y2="${py + ph}" stroke="#f2b22e" stroke-dasharray="3 3"/>`);
    let lx = px;
    for (const ch of ['x', 'y', 's', 'r', 'o', 'v']) {
      const vals = S.map((r) => r[ch]); if (!vals.some(Number.isFinite)) continue;
      const fin = vals.filter(Number.isFinite), lo = Math.min(...fin), hi = Math.max(...fin); if (hi - lo < 1e-9) continue;
      const pts = S.map((r, i) => Number.isFinite(vals[i]) ? `${X(r.f).toFixed(1)},${(py + ph - ((vals[i] - lo) / (hi - lo)) * ph).toFixed(1)}` : null).filter(Boolean).join(' ');
      out.push(`<polyline points="${pts}" fill="none" stroke="${col[ch]}" stroke-width="1.6"/>`);
      out.push(`<text x="${lx}" y="${py - 6}" fill="${col[ch]}" font-size="11">${ch} ${+lo.toFixed(3)}→${+hi.toFixed(3)}</text>`); lx += 120;
    }
    if (p.speed && p.speed.length) {
      const vm = Math.max(...p.speed.map((s) => s[1]), 1e-9);
      out.push(`<polyline points="${p.speed.map(([f, v]) => `${X(f).toFixed(1)},${(py + ph - (v / vm) * ph).toFixed(1)}`).join(' ')}" fill="none" stroke="#222" stroke-width="1" stroke-dasharray="4 2"/>`);
      out.push(`<text x="${px + pw}" y="${py - 6}" text-anchor="end" fill="#222" font-size="11">- - speed (${p.metrics.channel})</text>`);
    }
    const m = p.metrics || {};
    out.push(`<text x="${ox + 14}" y="${py + ph + 30}" font-size="11">${esc(clip(`${m.kind || '?'} · ${m.dur ?? '?'} f · Q1 ${m.q1 != null ? (m.q1 * 100).toFixed(0) + ' %' : '?'} · peak ${m.vmax ?? '?'} ${m.unit || ''}/f · start ${m.startV ?? '?'} end ${m.endV ?? '?'}`, 100))}</text>`);
    (p.notes || []).slice(0, 2).forEach((t, k) => out.push(`<text x="${ox + 14}" y="${py + ph + 46 + k * 14}" font-size="11" fill="#b4232a">${esc(clip(t, 100))}</text>`));
    out.push('</g>');
  });
  out.push('</svg>');
  return out.join('\n');
}

/** R3 on an open page: samples every probe, writes <name>.svg + <name>.json in outDir, adds findings to res. When res
 *  is scoped (res.others: the page's segments outside it), a probe that belongs to one of those is left out of the sheet
 *  and its findings: one sheet per caller. → { svg, json, probes, left: [ids left out] } */
export async function curveSheet(pg, res, { outDir, from = null, to = null, fps = 24, name = 'curves' } = {}) {
  const got = (await pg.evaluate(PROBE_JS)) || { api: 'none', probes: {} };
  const regToFile = new Map(), idToFile = new Map(), otherReg = new Map(), otherIds = new Map();
  for (const s of res.segments) if (s.regIds) { s.regIds.forEach((r) => regToFile.set(r, s)); (s.probes || []).filter(Boolean).forEach((p) => idToFile.set(p, s)); }
  for (const s of res.others || []) { s.regIds.forEach((r) => otherReg.set(r, s)); s.probes.filter(Boolean).forEach((p) => otherIds.set(p, s)); }
  const F0 = from != null ? from * fps : -Infinity, F1 = to != null ? to * fps : Infinity;
  const list = [], registered = new Map(), left = [];                      // segment name → probes registered (any range)
  for (const [id, P] of Object.entries(got.probes || {})) {
    const ms = P.meta && P.meta.seg;
    const seg = (ms && regToFile.get(ms)) || (!(ms && otherReg.has(ms)) && idToFile.get(id)) || null;
    if (seg) registered.set(seg.name, (registered.get(seg.name) || 0) + 1);
    if (!(P.f1 >= F0 && P.f0 <= F1)) continue;
    if (!seg && ((ms && otherReg.has(ms)) || otherIds.has(id))) { left.push(id); continue; }   // another segment's probe
    const item = { id, segment: seg ? seg.name : (P.meta && P.meta.seg) || null, f0: P.f0, f1: P.f1, meta: P.meta || null, error: P.error || null, samples: P.samples || null };
    if (!item.error && item.samples) {
      item.metrics = probeMetrics(item.samples, { id, kind: P.meta && P.meta.kind });
      item.notes = item.metrics.notes;
      const S = item.samples, ch = item.metrics.channel;
      if (ch) item.speed = S.slice(1).map((r, i) => {
        const p = S[i], d = ch === 'pos' ? Math.hypot((r.x || 0) - (p.x || 0), (r.y || 0) - (p.y || 0)) : Math.abs((r[ch] || 0) - (p[ch] || 0));
        return [+((r.f + p.f) / 2).toFixed(3), +(d / Math.max(1e-9, r.f - p.f)).toFixed(5)];
      });
    }
    list.push(item);
  }
  const strictSeg = (s) => s && s.mode === 'strict';
  for (const p of list) {
    const segObj = res.segments.find((s) => s.name === p.segment);
    const level = (segObj ? strictSeg(segObj) : res.strictPage) ? 'FAIL' : 'NOTE';
    if (p.error) res.findings.push({ check: 'R3', level, file: p.segment || '(page)', line: null, msg: `probe ${p.id} throws: ${clip(p.error, 140)}` });
    else for (const t of p.notes || []) res.findings.push({ check: 'R3', level: 'NOTE', file: p.segment || '(page)', line: null, msg: `${p.id}: ${t}${R3_THRESHOLDS.signed ? '' : ' (thresholds unsigned)'}` });
  }
  for (const s of res.segments) {
    if (!strictSeg(s) || !s.moving) continue;
    const n = registered.get(s.name) || 0;
    if (!n && !(s.probes || []).length) res.findings.push({ check: 'R3', level: 'FAIL', file: s.name, line: null, msg: 'no T3.motionProbe: an intro segment needs ≥ 3 probes (motion-library «Curve sheet»)' });
    else if (!n && (s.probes || []).filter(Boolean).length) res.findings.push({ check: 'R3', level: 'FAIL', file: s.name, line: null, msg: `its probes (${s.probes.filter(Boolean).join(', ')}) never registered at runtime` });
  }
  if (got.error) res.findings.push({ check: 'R3', level: res.strictPage ? 'FAIL' : 'NOTE', file: '(page)', line: null, msg: 'probe registry threw: ' + clip(got.error, 140) });
  recount(res);
  fs.mkdirSync(outDir, { recursive: true });
  const svg = path.join(outDir, name + '.svg'), json = path.join(outDir, name + '.json');
  const scope = res.scope && res.scope.kind !== 'page' ? res.scope.text : null;
  fs.writeFileSync(svg, curvesSvg(list, `curve sheet · ${res.page || res.pageDir}${scope ? ` · ${clip(scope, 90)}` : ''} · ${list.length} probe(s) · 1/4 f · thresholds ${R3_THRESHOLDS.signed ? 'signed' : 'unsigned (notes only)'}`));
  fs.writeFileSync(json, JSON.stringify({ page: res.page, scope, left, generated: new Date().toISOString(), api: got.api, step: 0.25, thresholds: R3_THRESHOLDS,
    probes: list.map(({ speed, ...p }) => p) }, null, 1));
  return { svg, json, probes: list, left };
}

// ---------------------------------------------------------------------------------------------------- --check-library
/** the index against the code. → { lines, fails, notes, counts } */
export function checkLibrary(opts = {}) {
  const P = paths(opts), lib = loadLibrary(P.library), out = { lines: [], fails: 0, notes: 0, counts: {}, ok: lib.ok };
  const say = (lvl, msg) => { out.lines.push(`${lvl} ${msg}`); if (lvl === 'FAIL') out.fails++; else out.notes++; };
  if (!lib.ok) { say('FAIL', `index not found: ${P.library}`); return out; }
  const recipes = loadRecipes(P.recipes), styles = loadStyles(P.styles), libRoot = P.lib;
  if (!lib.ids.size) say('FAIL', `no entries in the «Entry format» (- **\`group.slug\`** · name · grade · reuse · craft · code) in ${P.library}`);
  for (const d of lib.dups) say('FAIL', `duplicate id ${d.id} at :${d.line} (first at :${d.first})`);
  const codeOf = new Map();
  const jsCode = (file) => { if (!codeOf.has(file)) codeOf.set(file, exists(file) ? stripJsComments(readText(file)) : null); return codeOf.get(file); };
  const defined = (code, call) => {
    const parts = call.split('.');
    if (parts[0] !== 'T3') return new RegExp(`\\b${parts[parts.length - 1]}\\b\\s*(?:[:=(]|,|\\})`).test(code);
    const ns = parts.slice(0, Math.max(2, parts.length - 1)).join('\\.');
    if (!new RegExp(`\\b${ns}\\s*=(?!=)`).test(code)) return false;
    if (parts.length === 2) return true;
    const m = parts[parts.length - 1];
    if (m === '*') return true;
    return new RegExp(`function\\s+${m}\\s*\\(|(?<![\\w$])${m}\\s*:|\\.${m}\\s*=(?!=)|(?<![\\w$.])${m}\\s*=(?![=>])|[{,]\\s*${m}\\s*(?=[,}])|["'\`]${m}["'\`]\\s*:`).test(code);
  };
  const usedModules = new Set();
  for (const e of lib.ids.values()) {
    out.counts[e.kind || '?'] = (out.counts[e.kind || '?'] || 0) + 1;
    const loc = `:${e.line} ${e.id}`;
    if (!ID_RE.test(e.id)) say('FAIL', `${loc}: id not of the form group.slug (lower case)`);
    else if (!GROUPS.includes(e.id.split('.')[0]) && !e.retired) say('FAIL', `${loc}: unknown group (${GROUPS.join(', ')})`);
    if (e.retired) continue;
    if (!e.kind) { say('FAIL', `${loc}: code field «${clip(e.code, 50)}» is not LIB / EXISTING / PENDING-LIB / LOCKED / PROSE`); continue; }
    if (e.section === 'main' && e.grade === 'P') say('FAIL', `${loc}: grade P outside «Pending»`);
    if (e.section === 'pending' && e.grade !== 'P') say('NOTE', `${loc}: in «Pending» with grade ${e.grade || '?'} (expected P)`);
    if (!e.grade) say('NOTE', `${loc}: no grade (A B H R P)`);
    if (e.kind === 'LIB' || e.kind === 'EXISTING') {
      const file = e.kind === 'LIB' ? path.join(libRoot, 'motion', e.module) : path.join(libRoot, e.module);
      if (e.kind === 'LIB') usedModules.add(e.module.toLowerCase());
      const code = jsCode(file);
      if (code == null) { say('FAIL', `${loc}: ${e.kind} module ${path.relative(P.skill, file)} does not exist`); continue; }
      if (!e.calls.length) { say('FAIL', `${loc}: ${e.kind} ${e.module} names no call`); continue; }
      for (const c of e.calls) if (!defined(code, c)) say('FAIL', `${loc}: ${c} is not defined in ${path.relative(P.skill, file)}`);
    }
  }
  // the module headers cite ids that exist
  let mods = []; try { mods = fs.readdirSync(path.join(libRoot, 'motion')).filter((n) => n.endsWith('.js')); } catch {}
  for (const n of mods) {
    const src = readText(path.join(libRoot, 'motion', n)), head = (/^\s*\/\*[\s\S]*?\*\//.exec(src) || [''])[0];
    const cited = [...new Set(head.match(ID_IN_TEXT) || [])];
    if (!cited.length) say('NOTE', `lib/motion/${n}: its header cites no library id`);
    for (const id of cited) { const e = lib.ids.get(id); if (!e) say('FAIL', `lib/motion/${n} header cites unknown id ${id}`); else if (e.retired) say('FAIL', `lib/motion/${n} header cites retired id ${id}`); }
    if (!usedModules.has(n.toLowerCase())) say('NOTE', `lib/motion/${n} is named by no LIB entry`);
  }
  // ids and citations mentioned in the index text resolve
  for (const m of lib.mentions) {
    if (m.id && !lib.ids.has(m.id)) say('FAIL', `:${m.line} mentions \`${m.id}\`, which is no entry`);
    if (m.cite === 'shot-recipes') { const k = m.name.replace(/\s*\(.*\)\s*$/, '').trim(); if (!recipes.has(k)) say('FAIL', `:${m.line} «shot-recipes: ${m.name}» does not resolve`); }
    if (m.cite === 'mg-styles' && !styles.has(m.name.toLowerCase())) say('FAIL', `:${m.line} «mg-styles: ${m.name}» does not resolve`);
  }
  const c = out.counts, pend = [...lib.ids.values()].filter((e) => e.pending && !e.retired).length, ret = [...lib.ids.values()].filter((e) => e.retired).length;
  out.lines.unshift(`check-library ${P.library}: ${lib.ids.size} ids (LIB ${c.LIB || 0}, EXISTING ${c.EXISTING || 0}, PENDING-LIB ${c['PENDING-LIB'] || 0}, LOCKED ${c.LOCKED || 0}, PROSE ${c.PROSE || 0}; pending ${pend}, retired ${ret}) · ${out.fails} FAIL / ${out.notes} NOTE`);
  return out;
}

// ---------------------------------------------------------------------------------------------------- --hook
const HOOK_PATH = /[\\/]web[\\/]segments[\\/][^\\/]+\.js$/i;
/** PostToolUse: returns the JSON text to print, or '' (nothing new / not a segment). Never throws. */
export function hookOutput(raw, opts = {}) {
  try {
    const j = JSON.parse(String(raw || '').trim() || '{}');
    const fp = (j && j.tool_input && (j.tool_input.file_path || j.tool_input.path)) || '';
    if (!fp || !HOOK_PATH.test(fp) || !exists(fp)) return '';
    const P = paths(opts), name = path.basename(fp);
    if (isExempt(name, openingNames(P.opening))) return '';
    const webDir = path.dirname(path.dirname(path.resolve(fp))), page = path.join(webDir, 'index.html');
    const res = staticScan(exists(page) ? page : null, Object.assign({}, opts, { segments: [path.resolve(fp)], webDir }));
    const keys = res.findings.map((f) => `${f.level}|${f.check}|${f.file}|${f.msg.replace(/:\d+/g, ':#')}`);
    const dir = path.join(os.tmpdir(), 'qcrv_motion_lint'), cache = path.join(dir, crypto.createHash('sha1').update(normP(fp)).digest('hex') + '.json');
    let prev = []; try { prev = JSON.parse(fs.readFileSync(cache, 'utf8')); } catch {}
    try { fs.mkdirSync(dir, { recursive: true }); fs.writeFileSync(cache, JSON.stringify(keys)); } catch {}
    if (!keys.some((k) => !prev.includes(k))) return '';
    const lines = summaryLines(res).slice(0, 8);
    lines.push(`full check: node ${SELF.replace(/\\/g, '/')} ${(exists(page) ? page : fp).replace(/\\/g, '/')}`);
    return JSON.stringify({ hookSpecificOutput: { hookEventName: 'PostToolUse', additionalContext: `motion lint ${name}:\n` + lines.join('\n') } });
  } catch { return ''; }
}

// ---------------------------------------------------------------------------------------------------- CLI
async function main(argv) {
  const a = argv.slice(2), has = (k) => a.includes(k);
  const opt = (k, d = null) => { const i = a.indexOf(k); return i >= 0 && i + 1 < a.length ? a[i + 1] : d; };
  const common = { skill: opt('--skill'), library: opt('--library'), legacyList: opt('--legacy-list') };
  if (has('--hook')) {
    let raw = ''; try { raw = fs.readFileSync(0, 'utf8'); } catch {}
    const s = hookOutput(raw, common); if (s) process.stdout.write(s + '\n');
    return 0;
  }
  if (has('--check-library')) {
    const r = checkLibrary(common); r.lines.forEach((l) => console.log(l));
    return r.ok ? (r.fails ? 1 : 0) : 2;
  }
  const valued = new Set(['--segments', '--from', '--to', '--json', '--out', '--skill', '--library', '--legacy-list']);
  const pos = a.filter((x, i) => !x.startsWith('--') && !(i > 0 && valued.has(a[i - 1])));
  const page = pos[0];
  if (!page) { console.log('usage: node motion_lint.mjs <index.html> [--segments a.js,b.js] [--strict] [--runtime] [--curves] [--from s --to s] [--json out.json] [--out dir]\n       node motion_lint.mjs --check-library | --hook   (any: --skill <root> --library <md> --legacy-list <json>)'); return 2; }
  if (!exists(page)) { console.log(`motion_lint: page not found: ${page}`); return 2; }
  const segs = has('--segments') ? String(opt('--segments') || '').split(',').map((s) => s.trim()).filter(Boolean) : null;
  if (segs && !segs.length) { console.log('motion_lint: --segments names no file (a,b.js; web-relative paths with forward slashes, or bare names)'); return 2; }
  const res = staticScan(page, Object.assign({}, common, { strict: has('--strict'), segments: segs }));
  const outDir = path.resolve(opt('--out') || path.join(res.pageDir, 'tools', 'out', 'motion'));
  const extra = [];
  const curves = has('--curves'), runtime = curves || has('--runtime');
  if (runtime) {
    if (!res.strictPage) extra.push('runtime: skipped (legacy page: R1 and R3 apply to strict pages)');
    else {
      const { openPage } = await import('./_cdp.mjs');
      const pg = await openPage(page, { settle: 600, motion: false });   // this run prints its own summary, not _cdp's motion line
      try {
        const rt = await lintRuntime(pg, res);
        extra.push(`runtime: ${rt ? JSON.stringify(rt) : 'no answer'}`);
        if (curves) {
          const fps = (await pg.evaluate('(window.T3 && T3.FPS) || (window.T3_CONFIG && T3_CONFIG.fps) || 24')) || 24;
          const cs = await curveSheet(pg, res, { outDir, fps, from: opt('--from') != null ? +opt('--from') : null, to: opt('--to') != null ? +opt('--to') : null });
          extra.push(`curve sheet: ${cs.svg} (${cs.probes.length} probe(s)); data: ${cs.json}`);
          for (const p of cs.probes) extra.push(`  ${p.id} [${p.segment || '?'}] ${p.error ? 'THROWS ' + p.error : `${p.metrics.kind} ${p.metrics.channel} ${p.metrics.dur} f, Q1 ${p.metrics.q1}, peak ${p.metrics.vmax}${p.notes.length ? ' · ' + p.notes.join(' · ') : ''}`}`);
          if (cs.left.length) extra.push(`  left out: ${cs.left.length} probe(s) of the page's other segments (${clip(cs.left.join(', '), 160)})`);
        }
        if (pg.errors.length) extra.push('page errors: ' + pg.errors.slice(0, 5).join(' | '));
      } finally { await pg.close(); }
    }
  }
  let report = null;
  try { fs.mkdirSync(outDir, { recursive: true }); report = path.join(outDir, 'lint.txt'); fs.writeFileSync(report, reportText(res, extra)); }
  catch (e) { console.log(`motion_lint: cannot write the report in ${outDir}: ${e.message}`); }
  if (opt('--json')) fs.writeFileSync(path.resolve(opt('--json')), JSON.stringify(res, null, 1));
  summaryLines(res, report).forEach((l) => console.log(l));
  if (curves) extra.filter((l) => l.startsWith('curve sheet')).forEach((l) => console.log(l));
  if (res.needLibrary || res.error) return 2;                               // the lint could not finish: never a pass
  return res.fails ? 1 : 0;
}

const isMain = (() => { try { return !!process.argv[1] && path.resolve(process.argv[1]).toLowerCase() === SELF.toLowerCase(); } catch { return false; } })();
if (isMain) {
  main(process.argv).then((code) => { process.exitCode = code; }, (e) => {
    if (process.argv.includes('--hook')) { process.exitCode = 0; return; }
    console.log('motion_lint: ' + ((e && e.stack) || e)); process.exitCode = 2;
  });
}
