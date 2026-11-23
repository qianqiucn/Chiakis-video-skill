// test_load.mjs — lib/motion fails loudly when its setup is wrong, and reports a good load in window.__T3_MOTION
// (motion-library «Setup»): ez.js throws T3MotionError at load without engine.js, GSAP or CustomEase; probe.js without
// engine.js; moves.js without ez.js. The template's default tags load every module with no side effect beyond its own
// names. The lint's side of the setup (scripts/motion_lint.mjs, static scan, temp projects in the OS temp folder): S9, a
// project's lib/motion holds and loads every template module and its copies match (its printed copy command run as
// printed); S10, a hit built by hand is noted; S4, a move entry called but not cited is noted.
// Run: node test_load.mjs   (exit 1 on any failure)
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { page, tally, TPL, SKILL } from './_harness.mjs';

const T = tally('lib/motion load order');
// ---- the template's default tags (assets/template/index.html, comments stripped), in their order
{
  const html = fs.readFileSync(path.join(TPL, 'index.html'), 'utf8').replace(/<!--[\s\S]*?-->/g, '');
  const order = [...html.matchAll(/<script\s+src="lib\/motion\/([\w-]+)\.js"/g)].map((m) => m[1]);
  T.ok('template index.html loads lib/motion ez, probe, moves, blur, timing, her2d by default', order.join(',') === 'ez,probe,moves,blur,timing,her2d', order.join(','));
  let e = null, W = null; try { W = page({ motion: order }); } catch (x) { e = x; }
  T.ok('the template order loads with no error, no clash; __T3_MOTION.modules lists every module once', !e && W.__T3_MOTION.modules.join(',') === order.join(',') && !W.__T3_MOTION.clash && !W.__T3_MOTION.error, e ? `${e.name}: ${e.message}` : W.__T3_MOTION.modules.join(','));
  // side effects of the R2 modules at load: only their own T3 names, nothing else touched
  const B = page(), before = new Map(Object.keys(B.T3).map((k) => [k, B.T3[k]])), globals = new Set(Object.keys(B)), mods = B.__T3_MOTION.modules.join(',');
  for (const m of ['blur', 'timing', 'her2d']) B.__load(`lib/motion/${m}.js`);
  const added = Object.keys(B.T3).filter((k) => !before.has(k)).sort();
  T.ok('blur, timing, her2d add only T3.blur, T3.her, T3.relX, T3.shake, T3.tail, T3.twos', added.join(',') === 'blur,her,relX,shake,tail,twos', added.join(','));
  T.ok('… and leave every earlier T3 property as it was', [...before].every(([k, v]) => B.T3[k] === v));
  T.ok('… add no global and only append to __T3_MOTION.modules', Object.keys(B).every((k) => globals.has(k)) && B.__T3_MOTION.modules.join(',') === mods + ',blur,timing,her2d');
  // meshwarp.js stays optional: without it her2d loads, and only T3.her.warp2 throws when called
  let w = null; try { B.T3.her.warp2({}, {}, {}, null); } catch (x) { w = x; }
  T.ok('without lib/meshwarp.js her2d loads, and T3.her.warp2 throws T3MotionError when called', !B.T3.meshwarp && !!w && w.name === 'T3MotionError', w ? w.message : 'no error');
}
const attempt = (opts) => { let e = null, W = null; try { W = page(opts); } catch (x) { e = x; } return { e, W }; };
const named = (r) => !!r.e && r.e.name === 'T3MotionError';

{
  const W = page();
  T.ok('full page: __T3_MOTION = { lib: 1, gsap: true, modules: ez, probe, moves }', W.__T3_MOTION.lib === 1 && W.__T3_MOTION.gsap === true && W.__T3_MOTION.modules.join(',') === 'ez,probe,moves' && !W.__T3_MOTION.error);
  T.ok('full page: T3.EZ, T3.motionProbe, T3.mv and the bridge all present', !!(W.T3.EZ && W.T3.motionProbe && W.T3.mv && W.T3.gsapSeek && W.gsap && W.CustomEase));
}
{
  const W = page({ bridge: false });
  T.ok('works without gsap-bridge.js too (ez.js only needs gsap + CustomEase)', W.__T3_MOTION.gsap === true && W.T3.EZ.snap(1) === 1);
}
for (const [label, opts, msg] of [
  ['no GSAP', { gsap: false, motion: ['ez'] }, /GSAP is not loaded/],
  ['no CustomEase', { customEase: false, motion: ['ez'] }, /CustomEase is not loaded/],
  ['no engine.js', { engine: false, motion: ['ez'] }, /engine\.js is not loaded/],
]) {
  const r = attempt(opts);
  T.ok(`ez.js, ${label}: throws T3MotionError at load`, named(r) && msg.test(r.e.message), r.e ? `${r.e.name}: ${r.e.message}` : 'no error');
  // the context's window is gone with the throw, so re-run the load by hand to read the flag it left
  if (label !== 'no engine.js') {
    const W = page(Object.assign({}, opts, { motion: [] }));
    let e = null; try { W.__load('lib/motion/ez.js'); } catch (x) { e = x; }
    T.ok(`ez.js, ${label}: leaves __T3_MOTION = { lib: 1, gsap: false, error }`, !!e && W.__T3_MOTION && W.__T3_MOTION.gsap === false && W.__T3_MOTION.lib === 1 && /not loaded/.test(W.__T3_MOTION.error) && !W.T3.EZ);
  }
}
{
  const r = attempt({ motion: ['moves'] });
  T.ok('moves.js without ez.js: throws T3MotionError', named(r) && /ez\.js first/.test(r.e.message), r.e && r.e.message);
  const r2 = attempt({ engine: false, gsap: false, customEase: false, motion: ['probe'] });
  T.ok('probe.js without engine.js: throws T3MotionError', named(r2), r2.e && r2.e.message);
  const r3 = attempt({ motion: ['ez', 'moves', 'probe'] });
  T.ok('probe.js may load before or after moves.js', !r3.e && r3.W.__T3_MOTION.modules.join(',') === 'ez,moves,probe');
}

// ---- the lint: S9 (lib/motion complete, loaded, current) and S10 (a hit built by hand), on temp projects
{
  const L = await import(pathToFileURL(path.join(SKILL, 'scripts', 'motion_lint.mjs')).href);
  const ROOT = fs.mkdtempSync(path.join(os.tmpdir(), 'qcrv_lint_'));
  const TPLM = path.join(TPL, 'lib', 'motion'), MODS = fs.readdirSync(TPLM).filter((n) => n.endsWith('.js'));
  // a segment with nothing to fail: its header, an inline sheet (the 7 columns, one row) and the cited entry's call
  const PLAIN = ['// motion-sheet: inline', '// motion: move.arrive', '/* motion sheet x (edit) · curve family: calm · beat: 12',
    '| moment | element | frames (start / length) | id | ease | stagger / settle | departure and reason |', '|---|---|---|---|---|---|---|',
    '| in | x | 0 / 12 | move.arrive | T3.EZ.snap | — | — |', '*/',
    "(function () { T3.register({ id: 'x', render(t) { return T3.mv.arrive(t * 24, { at: 0 }); } }); })();", ''].join('\n');
  const TORDER = [...fs.readFileSync(path.join(TPL, 'index.html'), 'utf8').replace(/<!--[\s\S]*?-->/g, '').matchAll(/<script\s+src="lib\/motion\/([\w-]+\.js)"/g)].map((m) => m[1]);
  let k = 0;
  // a project: its lib/motion holds `mods` (crlf: line ends turned to CRLF; edit: text added), its page tags `tags`
  // (comment: inside <!-- -->; late: after the segment; shared: loaded from ../shared/lib/motion, a copy of the template's)
  const project = ({ mods = MODS, tags = MODS, comment = [], late = [], crlf = [], edit = {}, seg = PLAIN, shared = [] } = {}) => {
    const web = path.join(ROOT, `p${k++}`, 'web'), md = path.join(web, 'lib', 'motion');
    fs.mkdirSync(path.join(web, 'segments'), { recursive: true });
    if (mods.length) fs.mkdirSync(md, { recursive: true });
    for (const n of mods) {
      let t = fs.readFileSync(path.join(TPLM, n), 'utf8').replace(/\r\n/g, '\n');
      if (crlf.includes(n)) t = t.replace(/\n/g, '\r\n');
      fs.writeFileSync(path.join(md, n), t + (edit[n] || ''));
    }
    for (const n of shared) { const sd = path.join(web, '..', 'shared', 'lib', 'motion'); fs.mkdirSync(sd, { recursive: true }); fs.copyFileSync(path.join(TPLM, n), path.join(sd, n)); }
    const tag = (n) => `<script src="${shared.includes(n) ? '../shared/' : ''}lib/motion/${n}"></script>`;
    const html = ['<!doctype html><html><body>', '<script src="engine.js"></script>', '<script src="lib/gsap/gsap.min.js"></script>',
      '<script src="lib/gsap/CustomEase.min.js"></script>', '<script src="lib/gsap-bridge.js"></script>',
      ...tags.filter((n) => !late.includes(n)).map((n) => (comment.includes(n) ? `<!-- ${tag(n)} -->` : tag(n))),
      '<script src="segments/intro_x.js"></script>', ...late.map(tag), '</body></html>'].join('\n');
    fs.writeFileSync(path.join(web, 'index.html'), html);
    fs.writeFileSync(path.join(web, 'segments', 'intro_x.js'), seg);
    return path.join(web, 'index.html');
  };
  const scan = (pg, o = {}) => L.staticScan(pg, o);
  const s9 = (r, lv) => r.findings.filter((f) => f.check === 'S9' && (!lv || f.level === lv));
  const s10 = (r) => r.findings.filter((f) => f.check === 'S10');
  const last = MODS[MODS.length - 1];
  try {
    let r = scan(project());
    T.ok('S9: a project with every template module, loaded and equal: no S9 and no FAIL at all', s9(r).length === 0 && r.fails === 0, r.findings.map((f) => `${f.level} ${f.check} ${f.msg}`).join(' | '));
    r = scan(project({ mods: MODS.filter((n) => n !== 'her2d.js'), tags: MODS.filter((n) => n !== 'her2d.js') }));
    let f = s9(r, 'FAIL')[0];
    T.ok('S9: her2d.js missing and untagged → FAIL naming it, the copy command from the template and its tag', !!f && /missing her2d\.js/.test(f.msg) && f.msg.includes(`cp '${path.join(TPLM, 'her2d.js').replace(/\\/g, '/')}'`) && /<script src="lib\/motion\/her2d\.js"><\/script>/.test(f.msg), f && f.msg);
    T.ok('S9: … the summary keeps the whole line (copy command included)', L.summaryLines(r).some((l) => l.startsWith('FAIL S9') && l.includes("cp '")));
    r = scan(project({ tags: MODS.filter((n) => n !== 'timing.js') }));
    f = s9(r, 'FAIL')[0];
    T.ok('S9: timing.js present but untagged → FAIL «not loaded by the page: timing.js»', !!f && /not loaded by the page: timing\.js/.test(f.msg), f && f.msg);
    r = scan(project({ comment: ['blur.js'] }));
    f = s9(r, 'FAIL')[0];
    T.ok('S9: a tag inside <!-- --> does not count as loaded', !!f && /not loaded by the page: blur\.js/.test(f.msg), f && f.msg);
    r = scan(project({ edit: { 'moves.js': '\n// an older or edited copy\n' } }));
    f = s9(r, 'WARN')[0];
    T.ok('S9: a copy that differs from the template\'s → WARN naming it (no FAIL at all; lint exit stays 0)', !!f && /differs from the template's: moves\.js/.test(f.msg) && r.fails === 0 && r.warns === 1, r.findings.map((x) => `${x.level} ${x.check} ${x.msg}`).join(' | '));
    const sl = L.summaryLines(r), wi = sl.findIndex((l) => l.startsWith('WARN S9'));
    T.ok('S9: … the summary head counts it, the WARN line comes after the FAILs and before the notes; the motion line counts it',
      /1 WARN/.test(sl[0]) && wi > 0 && sl.slice(1, wi).every((l) => l.startsWith('FAIL')) && !sl.slice(wi + 1).some((l) => l.startsWith('FAIL')) && /1 warn/.test(L.motionLine(r)), sl.join(' ‖ '));
    r = scan(project({ crlf: MODS }));
    T.ok('S9: line ends alone (CRLF copies) are not a difference', s9(r).length === 0, s9(r).map((x) => x.msg).join(' | '));
    r = scan(project({ edit: { 'blur.js': '\n\n' } }));
    T.ok('S9: … nor blank lines added at the end of a copy', s9(r).length === 0, s9(r).map((x) => x.msg).join(' | '));
    r = scan(project({ mods: MODS.filter((n) => n !== 'her2d.js'), shared: ['her2d.js'] }));
    T.ok('S9: a module loaded from another lib/motion folder (../shared/lib/motion/her2d.js) counts as there', s9(r).length === 0, s9(r).map((x) => x.msg).join(' | '));
    r = scan(project({ late: [last] }));
    f = s9(r, 'WARN')[0];
    T.ok(`S9: ${last} tagged after the first segment → WARN «loaded after the first segment»`, !!f && /loaded after the first segment/.test(f.msg) && f.msg.includes(last), f && f.msg);
    r = scan(project({ late: ['ez.js'] }));
    T.ok('S9: a late ez.js is S1\'s FAIL alone, not an S9 WARN too', !s9(r).length && r.findings.some((x) => x.check === 'S1' && x.level === 'FAIL'), r.findings.map((x) => `${x.level} ${x.check} ${x.msg}`).join(' | '));
    // tags to add come in the template's order, missing and unloaded modules together (moves.js after ez.js)
    r = scan(project({ mods: MODS.filter((n) => n !== 'moves.js'), tags: [] }));
    f = s9(r, 'FAIL')[0];
    const shown = f ? [...f.msg.matchAll(/<script src="lib\/motion\/([\w-]+\.js)"><\/script>/g)].map((m) => m[1]) : [];
    T.ok('S9: the tags to add are printed in the template\'s order (missing moves.js among the unloaded ones)', shown.length === TORDER.length && shown.join(',') === TORDER.join(','), shown.join(','));
    // no lib/ at all beside the page: the printed folder command, run in a shell as printed, lands the modules in lib/motion
    const nolib = project({ mods: [], tags: [] });
    r = scan(nolib);
    f = s9(r, 'FAIL')[0];
    const cmd = f && /\((node -e "[^"]+")\)/.exec(f.msg);
    T.ok('S9: no lib/motion folder at all on a strict page → FAIL with one node copy command for the folder', !!cmd && /the folder is missing/.test(f.msg) && /cpSync\(/.test(cmd[1]), f && f.msg);
    if (cmd) {
      const web = path.dirname(nolib), run = spawnSync(cmd[1].replace(/^node /, `"${process.execPath}" `), { shell: true, encoding: 'utf8' });
      const landed = MODS.every((n) => fs.existsSync(path.join(web, 'lib', 'motion', n))) && !MODS.some((n) => fs.existsSync(path.join(web, 'lib', n)));
      r = scan(nolib);
      const left = s9(r, 'FAIL');
      T.ok('S9: … which, run in a shell as printed, puts every module in web/lib/motion (none loose in web/lib); then only the tags are asked for', run.status === 0 && landed && left.length === 1 && !/missing/.test(left[0].msg) && /not loaded by the page/.test(left[0].msg), `${run.status} ${run.stderr || ''} landed=${landed} ${s9(r).map((x) => x.msg).join(' | ')}`);
    }
    // legacy: a temp legacy list holding the project (cutoff far ahead), so its segment is in note mode
    const legPage = project({ mods: MODS.filter((n) => n !== 'her2d.js'), tags: MODS.filter((n) => n !== 'her2d.js') });
    const legList = path.join(ROOT, 'legacy.json');
    const legFor = (pg) => fs.writeFileSync(legList, JSON.stringify({ entries: [{ prefix: path.dirname(pg), date: '2099-12-31', reason: 'test' }] }));
    legFor(legPage); r = scan(legPage, { legacyList: legList });
    T.ok('S9 legacy: an all-legacy page that has begun on lib/motion gets NOTE, never FAIL', !r.strictPage && s9(r).length === 1 && s9(r)[0].level === 'NOTE', s9(r).map((x) => x.level + ' ' + x.msg).join(' | '));
    const oldPage = project({ mods: [], tags: [] });
    legFor(oldPage); r = scan(oldPage, { legacyList: legList });
    T.ok('S9 legacy: an archived film from before the library (no lib/motion at all) gets no S9 (S1 notes it)', s9(r).length === 0 && r.findings.some((x) => x.check === 'S1' && x.level === 'NOTE'));
    // the template's list is read at run time: a skill whose template ships one module more asks for it
    const sk = path.join(ROOT, 'skill'), skm = path.join(sk, 'assets', 'template', 'lib', 'motion');
    fs.mkdirSync(skm, { recursive: true });
    for (const n of MODS) fs.copyFileSync(path.join(TPLM, n), path.join(skm, n));
    fs.writeFileSync(path.join(skm, 'zz_new.js'), '/* a module added later */\n');
    r = scan(project(), { skill: sk, library: path.join(SKILL, 'references', 'motion-library.md') });
    f = s9(r, 'FAIL')[0];
    T.ok('S9: a module added to the template later (another --skill) is asked for by name', !!f && /missing zz_new\.js/.test(f.msg), f && f.msg);
    // S10: a hand-built hit (a 1.14 → 1 punch and a full-frame light fill in one function), and the ways it is answered
    const hitSeg = ({ cites = 'move.arrive', from = 1.14, extra = '', apart = false } = {}) => [
      '// motion-sheet: inline', `// motion: ${cites}`, '(function () {', '  const W = 1920, H = 1080, EZ = T3.EZ;',
      `  function white(c) { ${apart ? "c.fillStyle = '#FFF6EA'; c.fillRect(0, 0, W, H);" : ''} }`,
      '  function hit(c, f, h0) {',
      `    ${apart ? '' : "if (f === h0) { c.fillStyle = '#FFF6EA'; c.fillRect(0, 0, W, H); return; }"}`,
      `    const s = ${from} - ${(from - 1).toFixed(2)} * EZ.at(f, h0 + 1, 7, 'expoOut');${extra}`,
      '    c.setTransform(s, 0, 0, s, 960 - 960 * s, 540 - 540 * s);', '  }',
      "  T3.register({ id: 'x', render(t) {} });", '})();', ''].join('\n');
    r = scan(project({ seg: hitSeg() }));
    f = s10(r)[0];
    T.ok('S10: scale 1.14 → 1 with a full-frame light fill in the same function, no shake → NOTE naming the library moves', s10(r).length === 1 && f.level === 'NOTE' && f.line === 8 && /type\.slam/.test(f.msg) && /fx\.shake/.test(f.msg), f && `:${f.line} ${f.msg}`);
    r = scan(project({ seg: hitSeg({ extra: ' const sh = T3.shake(f, h0 + 1, { amp: 26, dur: 7 });' }) }));
    T.ok('S10: … not when the file calls T3.shake', s10(r).length === 0);
    r = scan(project({ seg: hitSeg({ cites: 'move.arrive, type.slam' }) }));
    T.ok('S10: … not when the header cites type.slam', s10(r).length === 0);
    r = scan(project({ seg: hitSeg({ apart: true }) }));
    T.ok('S10: … not when the fill is drawn in another function', s10(r).length === 0);
    r = scan(project({ seg: hitSeg({ from: 1.05 }) }));
    T.ok('S10: … not for a 5 % push (under 1.1)', s10(r).length === 0);
    r = scan(project({ seg: hitSeg({ extra: ' const sh = shake(f);' }).replace('(function () {', '(function () {\n  function shake(f) { return Math.sin(f * 7) * 9; }') }));
    T.ok('S10: … still noted when the file shakes with a shake of its own (function shake)', s10(r).length === 1, s10(r).map((x) => x.msg).join(' | '));
    r = scan(project({ seg: hitSeg({ extra: ' const sh = DZ.shake(f);' }) }));
    T.ok('S10: … not when it calls another layer\'s shake (DZ.shake)', s10(r).length === 0);
    r = scan(project({ seg: hitSeg().replace('c.setTransform(s, 0, 0, s, 960 - 960 * s, 540 - 540 * s);', 'c.shadowBlur = 40 * s;') }));
    T.ok('S10: … not when the 1.14 → 1 value drives no scale (a glow)', s10(r).length === 0, s10(r).map((x) => x.msg).join(' | '));
    r = scan(project({ seg: hitSeg().replace('c.setTransform(s, 0, 0, s, 960 - 960 * s, 540 - 540 * s);', "el.style.transform = 'scale(' + s + ')';") }));
    T.ok('S10: … noted when the value drives a DOM scale written in a quoted string', s10(r).length === 1, s10(r).map((x) => x.msg).join(' | '));
    const hp = project({ seg: hitSeg() }); legFor(hp); r = scan(hp, { legacyList: legList });
    T.ok('S10: … not in a legacy segment', s10(r).length === 0);
    // S4 the other way: a move entry's call made here, its id not in the header
    const rs4 = (x) => x.findings.filter((y) => y.check === 'S4' && /not in the \/\/ motion: header/.test(y.msg));
    const ARRIVE = 'return T3.mv.arrive(t * 24, { at: 0 });';
    r = scan(project({ seg: PLAIN.replace(ARRIVE, 'T3.shake(t * 24, 3, { amp: 20, dur: 7 }); ' + ARRIVE) }));
    T.ok('S4: T3.shake called with fx.shake left out of the header → NOTE naming fx.shake', rs4(r).length === 1 && rs4(r)[0].level === 'NOTE' && /fx\.shake \(T3\.shake\)/.test(rs4(r)[0].msg), rs4(r).map((x) => x.msg).join(' | '));
    r = scan(project({ seg: PLAIN.replace('// motion: move.arrive', '// motion: move.arrive, fx.shake').replace(ARRIVE, 'T3.shake(t * 24, 3, { amp: 20, dur: 7 }); ' + ARRIVE) }));
    T.ok('S4: … not once the header cites it', rs4(r).length === 0, rs4(r).map((x) => x.msg).join(' | '));
    r = scan(project({ seg: PLAIN.replace(ARRIVE, 'const b = T3.EZ.back(t); T3.motionProbe(\'x\', 0, 9, () => ({ x: b })); ' + ARRIVE) }));
    T.ok('S4: … never for a curve or a curve.* tool (T3.EZ.back is move.pop\'s call; T3.motionProbe is curve.probe\'s)', rs4(r).length === 0, rs4(r).map((x) => x.msg).join(' | '));
    // the skill's own pages pass both, and call no entry they leave uncited
    for (const pg of [path.join(TPL, 'index.html'), path.join(SKILL, 'assets', 'examples', 'motion', 'index.html')]) {
      r = scan(pg);
      T.ok(`S9/S10: ${path.relative(SKILL, pg).replace(/\\/g, '/')} has none (nor an uncited call)`, !r.findings.some((x) => x.check === 'S9' || x.check === 'S10') && !rs4(r).length, r.findings.filter((x) => x.check === 'S9' || x.check === 'S10').concat(rs4(r)).map((x) => x.msg).join(' | '));
    }
  } finally { fs.rmSync(ROOT, { recursive: true, force: true }); }
}
T.done();
