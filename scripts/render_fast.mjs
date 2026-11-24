// Fast frame-by-frame render: N persistent headless Chrome pages (scripts/_cdp.mjs) pull frames from a shared
// queue; finished frames are re-ordered in memory and piped straight into ONE ffmpeg that writes the 1080p MP4 and
// the 720p MP4 in the same pass (GPU NVENC when the ffmpeg build has it, else libx264). No frame files on disk.
// Workers: each one is a whole headless Chrome (~0.5–1.5 GB RAM per Chrome worker); the default is 2.
// Run it through scripts/run_queue.py web (production.md Toolkit «Rules»): it caps --workers at 2 and sets
// CHIAKI_MAX_WORKERS, which this script obeys too, so a render that qa.mjs starts inside the slot stays capped; a
// --workers that is missing, valueless, not a number or below 1 means 2 (never 0 workers left waiting forever).
// Page errors: a segment's render(t) that throws is printed the first time it happens and summed up at the end
// (segment, frames, message, file:line); the video is still written. Exit code 0 = clean, 2 = written but the page
// threw (not deliverable: on those frames the broken layer and every layer above it are missing), 1 = failed.
// --errors-json f writes the raw records for qa.mjs.
// Usage:
//   node render_fast.mjs <index.html> <start s> <end s> <out.mp4> [--audio a.wav] [--audio-start 0]
//        [--workers 2] [--fps 24] [--scale 1 | --2k [--max-mb 480]] [--grain] [--cpu] [--disk] [--png] [--keep] [--query "&x=1"]
//        [--errors-json f]
//   --scale 0.5  half-size draft (motion checks, QA): one small MP4 only (<out>_720p.mp4)
//   --2k         the delivery at 2560×1440: frames captured at 4/3 scale, one MP4 (<out>_2k.mp4) whose bitrate is capped
//                at 15 Mbps (22 Mbps with --grain), or lower so the file stays under --max-mb (default 480)
//   --grain      film-grain / paper-texture preservation preset: lower CQ/CRF and higher maxrate so tactile grain
//                and paper fiber overlays survive H.264 compression at 720p, 1080p, and 2K
//   --cpu        libx264 instead of NVENC (smaller files, slower)
//   --disk       old mode: frames to <out dir>/_frames_<name>/ (resumable; --keep keeps them, --png = PNG frames)
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { openPage, findFfmpeg, sleep, errorReport, reportLines, failKey, workerCount } from './_cdp.mjs';

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const has = (k) => a.includes(k);
const [page, startS, endS, out] = a;
if (!out) { console.log('usage: node render_fast.mjs <index.html> <start> <end> <out.mp4> [--audio f] [--audio-start s] [--workers 2] [--fps 24] [--scale 1 | --2k [--max-mb 480]] [--grain] [--cpu] [--disk] [--png] [--keep] [--query q] [--errors-json f]'); process.exit(1); }
const k2 = has('--2k');
const grain = has('--grain');
const fps = +opt('--fps', 24), W = workerCount(opt('--workers', 2)), scale = k2 ? 4 / 3 : +opt('--scale', 1), query = opt('--query', '');
const disk = has('--disk') || has('--keep') || has('--png');
const fmt = has('--png') ? 'png' : 'jpeg', ext = fmt === 'png' ? 'png' : 'jpg';
const F0 = Math.round(+startS * fps), F1 = Math.round(+endS * fps) - 1, N = F1 - F0 + 1;
const ff = findFfmpeg();
const nvenc = !has('--cpu') && /h264_nvenc/.test(spawnSync(ff, ['-hide_banner', '-encoders'], { encoding: 'utf8' }).stdout || '');
const small = out.replace(/\.mp4$/i, '') + (k2 ? '_2k.mp4' : '_720p.mp4');
const audio = opt('--audio', ''), dur = (N / fps).toFixed(4);
const aIn = audio ? ['-ss', opt('--audio-start', '0'), '-t', dur, '-i', audio] : [];
const vEnc = (q, big) => nvenc
  ? ['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', String(q), '-b:v', '0', '-maxrate', big ? (grain ? '50M' : '40M') : (grain ? '18M' : '12M'), '-bufsize', big ? (grain ? '100M' : '80M') : (grain ? '36M' : '24M'), '-pix_fmt', 'yuv420p']
  : ['-c:v', 'libx264', '-preset', 'medium', '-crf', String(grain ? q : q + 1), '-pix_fmt', 'yuv420p'];
const aEnc = (br) => (audio ? ['-map', '1:a', '-c:a', 'aac', '-b:a', br, '-shortest'] : []);
// HD colour: the JPEG frames are BT.601, so the scale converts the matrix to BT.709 (accurate rounding: the fast path
// darkens ≈ 3 levels) and every output is tagged BT.709 (setparams marks the frames, which the encoder follows)
const tag = ['-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709'];
const cm = 'in_color_matrix=bt601:out_color_matrix=bt709:flags=bicubic+accurate_rnd+full_chroma_int';
const sp = 'setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709';
// one ffmpeg, two outputs (or one for drafts), reading frames from `vin`
function encodeArgs(vin) {
  // JPEG screenshots decode as full-range YUV: convert to standard TV range so phones/players show the true levels
  if (k2) {                                            // 2K delivery: native 2560×1440, bitrate capped to the upload limit
    const mbps = Math.min(grain ? 22 : 15, (+opt('--max-mb', 480) * 8) / +dur - 0.25);
    const rate = [`${mbps.toFixed(2)}M`, `${(2 * mbps).toFixed(2)}M`];
    const enc = nvenc ? ['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', grain ? '16' : '19', '-b:v', rate[0], '-maxrate', rate[0], '-bufsize', rate[1], '-pix_fmt', 'yuv420p']
      : ['-c:v', 'libx264', '-preset', 'medium', '-crf', grain ? '16' : '18', '-maxrate', rate[0], '-bufsize', rate[1], '-pix_fmt', 'yuv420p'];
    return [...vin, ...aIn, '-map', '0:v', ...aEnc('192k'), '-vf', `scale=2560:-2:in_range=pc:out_range=tv:${cm},format=yuv420p,${sp}`, ...enc, ...tag, '-movflags', '+faststart', small];
  }
  if (scale !== 1) return [...vin, ...aIn, '-map', '0:v', ...aEnc('192k'), '-vf', `scale=1280:-2:in_range=pc:out_range=tv:${cm},format=yuv420p,${sp}`, ...vEnc(grain ? 18 : 24, false), ...tag, '-movflags', '+faststart', small];
  return [...vin, ...aIn, '-filter_complex', `[0:v]scale=in_range=pc:out_range=tv:${cm},format=yuv420p,${sp},split=2[big][s];[s]scale=1280:-2:flags=lanczos[sm]`,
    '-map', '[big]', ...aEnc('192k'), ...vEnc(grain ? 17 : 21, true), ...tag, '-movflags', '+faststart', out,
    '-map', '[sm]', ...aEnc('192k'), ...vEnc(grain ? 20 : 27, false), ...tag, '-movflags', '+faststart', small];
}
console.log(`frames ${F0}..${F1} (${N}), workers ${W}, ${disk ? 'disk ' + fmt : 'pipe'}, ${nvenc ? 'NVENC' : 'libx264'}${scale !== 1 ? ', scale ' + scale : ''}${grain ? ', grain' : ''}`);
const t0 = Date.now(); const pages = [], told = new Set();
// say each kind of render error once, the moment a worker first meets it (the full list comes at the end)
const onRenderError = (r, line) => { const k = failKey(r); if (!told.has(k)) { told.add(k); console.log('RENDER ERROR ' + line); } };
const open = async () => { const pg = await openPage(page, { query, onRenderError }); pages.push(pg); return pg; };
let next = 0, done = 0;
const tick = () => { if (++done % 120 === 0) console.log(`  ${done}/${N}  ${(done / ((Date.now() - t0) / 1000)).toFixed(1)} frames/s`); };

if (!disk) {
  // ---- pipe mode -------------------------------------------------------------------------------------------
  const enc = spawn(ff, ['-hide_banner', '-loglevel', 'error', '-y', ...encodeArgs(['-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-'])], { stdio: ['pipe', 'inherit', 'inherit'] });
  const encDone = new Promise((res) => enc.on('close', res));
  const ready = new Map(); let wrote = 0, writing = false;
  async function flush() {
    if (writing) return; writing = true;
    while (ready.has(F0 + wrote)) {
      const b = ready.get(F0 + wrote); ready.delete(F0 + wrote); wrote++;
      if (!enc.stdin.write(b)) await new Promise((r) => enc.stdin.once('drain', r));
    }
    writing = false;
  }
  async function worker() {
    const pg = await open();
    while (next < N) {
      const i = next++;
      while (i - wrote > 240) await sleep(20);            // keep the re-order window bounded
      ready.set(F0 + i, await pg.shot((F0 + i + 0.5) / fps, { format: 'jpeg', quality: 95, scale }));
      tick(); flush();
    }
    await pg.close();
  }
  await Promise.all(Array.from({ length: Math.min(W, N) }, worker));
  while (wrote < N) { await flush(); await sleep(10); }
  enc.stdin.end();
  const code = await encDone;
  if (code) throw new Error('ffmpeg failed (' + code + ')');
} else {
  // ---- disk mode (resumable) ---------------------------------------------------------------------------------
  const dir = path.join(path.dirname(path.resolve(out)), '_frames_' + path.basename(out, path.extname(out)));
  fs.mkdirSync(dir, { recursive: true });
  const fileOf = (f) => path.join(dir, `f${String(f).padStart(6, '0')}.${ext}`);
  const todo = []; for (let f = F0; f <= F1; f++) if (!fs.existsSync(fileOf(f)) || fs.statSync(fileOf(f)).size === 0) todo.push(f);
  if (todo.length < N) console.log(`  ${N - todo.length} frames already on disk: reused, so not checked for page errors this run`);
  async function worker() {
    const pg = await open();
    while (next < todo.length) { const f = todo[next++]; fs.writeFileSync(fileOf(f), await pg.shot((f + 0.5) / fps, { format: fmt, scale })); tick(); }
    await pg.close();
  }
  await Promise.all(Array.from({ length: Math.min(W, Math.max(1, todo.length)) }, worker));
  const r = spawnSync(ff, ['-hide_banner', '-loglevel', 'error', '-y', ...encodeArgs(['-framerate', String(fps), '-start_number', String(F0), '-i', path.join(dir, `f%06d.${ext}`)])], { stdio: 'inherit' });
  if (r.status) throw new Error('ffmpeg failed');
  if (!has('--keep')) fs.rmSync(dir, { recursive: true, force: true });
}
const secs = (Date.now() - t0) / 1000;
for (const f of [out, small]) if (fs.existsSync(f) && fs.statSync(f).mtimeMs >= t0) console.log(f, (fs.statSync(f).size / 1048576).toFixed(1) + ' MB');
console.log(`total ${secs.toFixed(1)} s (${(N / secs).toFixed(1)} frames/s incl. encoding)`);
const rep = errorReport(pages);
reportLines(rep).forEach((l) => console.log(l));
if (opt('--errors-json', '')) fs.writeFileSync(opt('--errors-json'), JSON.stringify(pages.map((p) => ({ renderErrors: p.renderErrors, errors: p.errors, renderLines: [...p.renderLines], ready: p.ready }))));
if (rep.count) { console.log(`render_fast: the page threw (${rep.count} kind(s), above): video written, NOT deliverable; exit 2`); process.exitCode = 2; }
