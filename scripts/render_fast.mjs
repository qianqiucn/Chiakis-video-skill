// Fast frame-by-frame render: N persistent headless Chrome pages (scripts/_cdp.mjs) pull frames from a shared
// queue; finished frames are re-ordered in memory and piped straight into ONE ffmpeg that writes the 1080p MP4 and
// the 720p MP4 in the same pass (GPU NVENC when the ffmpeg build has it, else libx264). No frame files on disk unless
// --disk / --keep / --patch-frames is set.
//
// Resilience & Observability (v1.7.1):
//   - Per-worker stage heartbeat (frame, stage: boot/seek+raf/capture/wait-reorder/encode, fps) every 24 frames or 10 s.
//   - Per-frame CDP timeout (--frame-timeout, default 30 s) with automatic Chrome respawn & GPU->CPU software fallback.
//   - No-progress stall watchdog (--stall-timeout, default 60 s): logs exact stuck worker/frame/stage, kills Chrome &
//     ffmpeg cleanly, leaves incomplete output as *.part.mp4 (never corrupts existing deliverables), and exits 1 so
//     scripts/run_queue.py releases its web slot immediately.
//   - Atomic output rename: ffmpeg writes to <out>.part.mp4 and renames to <out> ONLY after ffmpeg exits 0.
//   - Partial revision support: --patch-frames "120-180,500-540" (implies --disk --keep) deletes only those cached
//     frames, re-renders them, and re-encodes; --encode-only re-encodes existing cached frames without launching Chrome.
//
// Page errors: exit 0 = clean, 2 = written but the page threw (NOT deliverable), 1 = failed / stalled.
// Usage:
//   node render_fast.mjs <index.html> <start s> <end s> <out.mp4> [--audio a.wav] [--audio-start 0]
//        [--workers 2] [--fps 24] [--scale 1 | --2k [--max-mb 480]] [--grain] [--cpu] [--disk] [--png] [--keep]
//        [--patch-frames "120-180"] [--encode-only] [--frame-timeout 30] [--stall-timeout 60] [--retries 2]
//        [--progress-every 24] [--no-cpu-fallback] [--query "&x=1"] [--errors-json f]
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { openPage, parseFrames, findFfmpeg, sleep, errorReport, reportLines, failKey, workerCount } from './_cdp.mjs';

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const has = (k) => a.includes(k);
const [page, startS, endS, out] = a;
if (!out || has('-h') || has('--help')) {
  console.log(
    'usage: node render_fast.mjs <index.html> <start> <end> <out.mp4> [--audio f] [--audio-start s]\n' +
    '       [--workers 2] [--fps 24] [--scale 1 | --2k [--max-mb 480]] [--grain] [--cpu]\n' +
    '       [--disk] [--png] [--keep] [--patch-frames "120-180,500-540"] [--encode-only]\n' +
    '       [--frame-timeout 30] [--stall-timeout 60] [--retries 2] [--progress-every 24]\n' +
    '       [--no-cpu-fallback] [--query q] [--errors-json f]'
  );
  process.exit(has('-h') || has('--help') ? 0 : 1);
}

const k2 = has('--2k');
const grain = has('--grain');
const fps = +opt('--fps', 24);
const W = workerCount(opt('--workers', 2));
const scale = k2 ? 4 / 3 : +opt('--scale', 1);
const query = opt('--query', '');
const patchSpec = opt('--patch-frames', '');
const encodeOnly = has('--encode-only');
const disk = has('--disk') || has('--keep') || has('--png') || !!patchSpec || encodeOnly;
const keepFrames = has('--keep') || !!patchSpec || encodeOnly;
const fmt = has('--png') ? 'png' : 'jpeg';
const ext = fmt === 'png' ? 'png' : 'jpg';
const frameTimeoutMs = Math.max(5, +opt('--frame-timeout', 30)) * 1000;
const stallTimeoutMs = Math.max(10, +opt('--stall-timeout', 60)) * 1000;
const maxRetries = Math.max(0, Math.floor(+opt('--retries', 2)));
const progressEvery = Math.max(1, Math.floor(+opt('--progress-every', 24)));
const allowCpuFallback = !has('--no-cpu-fallback');
const forceChromeCpu = process.env.CHIAKI_CPU === '1' || process.env.QCRV_CPU === '1';

const F0 = Math.round(+startS * fps);
const F1 = Math.round(+endS * fps) - 1;
const N = F1 - F0 + 1;
if (!Number.isFinite(N) || N <= 0) {
  console.error(`render_fast: invalid frame range start=${startS} end=${endS} fps=${fps} (N=${N})`);
  process.exit(1);
}

const ff = findFfmpeg();
const nvenc = !has('--cpu') && /h264_nvenc/.test(spawnSync(ff, ['-hide_banner', '-encoders'], { encoding: 'utf8' }).stdout || '');
const outAbs = path.resolve(out);
fs.mkdirSync(path.dirname(outAbs), { recursive: true });
const smallAbs = outAbs.replace(/\.mp4$/i, '') + (k2 ? '_2k.mp4' : '_720p.mp4');
const outTmp = outAbs.replace(/\.mp4$/i, '') + '.part.mp4';
const smallTmp = smallAbs.replace(/\.mp4$/i, '') + '.part.mp4';
const audio = opt('--audio', '');
const dur = (N / fps).toFixed(4);
const aIn = audio ? ['-ss', opt('--audio-start', '0'), '-t', dur, '-i', audio] : [];
const vEnc = (q, big) => nvenc
  ? ['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', String(q), '-b:v', '0', '-maxrate', big ? (grain ? '50M' : '40M') : (grain ? '18M' : '12M'), '-bufsize', big ? (grain ? '100M' : '80M') : (grain ? '36M' : '24M'), '-pix_fmt', 'yuv420p']
  : ['-c:v', 'libx264', '-preset', 'medium', '-crf', String(grain ? q : q + 1), '-pix_fmt', 'yuv420p'];
const aEnc = (br) => (audio ? ['-map', '1:a', '-c:a', 'aac', '-b:a', br, '-shortest'] : []);
// HD colour: JPEG screenshots decode as BT.601 full-range -> accurately map to BT.709 TV range.
const tag = ['-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709'];
const cm = 'in_color_matrix=bt601:out_color_matrix=bt709:flags=bicubic+accurate_rnd+full_chroma_int';
const sp = 'setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709';

// Encode to temporary *.part.mp4 paths first; rename atomically only when ffmpeg succeeds.
const outputs = [];
function encodeArgs(vin) {
  outputs.length = 0;
  if (k2) {
    outputs.push([smallTmp, smallAbs]);
    const mbps = Math.min(grain ? 22 : 15, (+opt('--max-mb', 480) * 8) / +dur - 0.25);
    const rate = [`${mbps.toFixed(2)}M`, `${(2 * mbps).toFixed(2)}M`];
    const enc = nvenc
      ? ['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', grain ? '16' : '19', '-b:v', rate[0], '-maxrate', rate[0], '-bufsize', rate[1], '-pix_fmt', 'yuv420p']
      : ['-c:v', 'libx264', '-preset', 'medium', '-crf', grain ? '16' : '18', '-maxrate', rate[0], '-bufsize', rate[1], '-pix_fmt', 'yuv420p'];
    return [...vin, ...aIn, '-map', '0:v', ...aEnc('192k'), '-vf', `scale=2560:-2:in_range=pc:out_range=tv:${cm},format=yuv420p,${sp}`, ...enc, ...tag, '-movflags', '+faststart', smallTmp];
  }
  if (scale !== 1) {
    outputs.push([smallTmp, smallAbs]);
    return [...vin, ...aIn, '-map', '0:v', ...aEnc('192k'), '-vf', `scale=1280:-2:in_range=pc:out_range=tv:${cm},format=yuv420p,${sp}`, ...vEnc(grain ? 18 : 24, false), ...tag, '-movflags', '+faststart', smallTmp];
  }
  outputs.push([outTmp, outAbs], [smallTmp, smallAbs]);
  return [...vin, ...aIn, '-filter_complex', `[0:v]scale=in_range=pc:out_range=tv:${cm},format=yuv420p,${sp},split=2[big][s];[s]scale=1280:-2:flags=lanczos[sm]`,
    '-map', '[big]', ...aEnc('192k'), ...vEnc(grain ? 17 : 21, true), ...tag, '-movflags', '+faststart', outTmp,
    '-map', '[sm]', ...aEnc('192k'), ...vEnc(grain ? 20 : 27, false), ...tag, '-movflags', '+faststart', smallTmp];
}

console.log(
  `frames ${F0}..${F1} (${N}), workers ${W}, ${disk ? 'disk ' + fmt : 'pipe'}, ${nvenc ? 'NVENC' : 'libx264'}` +
  `${forceChromeCpu ? ', chrome=CPU' : ', chrome=GPU'}` +
  `${scale !== 1 ? ', scale ' + scale : ''}${grain ? ', grain' : ''}` +
  ` (frameTimeout=${frameTimeoutMs / 1000}s, stallTimeout=${stallTimeoutMs / 1000}s)`
);

const t0 = Date.now();
const pages = [];          // every Chrome page opened (for complete error reporting even across respawns)
const livePages = new Set();
const told = new Set();
const onRenderError = (r, line) => { const k = failKey(r); if (!told.has(k)) { told.add(k); console.log('RENDER ERROR ' + line); } };

let next = 0, done = 0, wrote = 0;
let lastProgressAt = Date.now();
let aborted = false, abortReason = '';
let globalPhase = 'init';
let encProc = null;
const workerStates = [];

const elapsedS = () => ((Date.now() - t0) / 1000).toFixed(1);
const fmtWorkers = () => workerStates.map((w) => {
  const st = w.pg ? `${w.stage}:${w.pg.getStage()}` : w.stage;
  const age = ((Date.now() - w.since) / 1000).toFixed(1);
  return `w${w.id}[${w.cpu ? 'cpu' : 'gpu'} f${w.frame ?? '-'} ${st} ${age}s last=f${w.lastDone ?? '-'}]`;
}).join(' ');

function logProgress(tagStr = 'progress') {
  const sec = Math.max(0.05, (Date.now() - t0) / 1000);
  const pct = ((done / Math.max(1, N)) * 100).toFixed(1);
  console.log(`[render_fast +${elapsedS()}s ${tagStr}] ${done}/${N} (${pct}%)${!disk ? ` wrote=${wrote}` : ''} ${(done / sec).toFixed(1)} fps | phase=${globalPhase} | ${fmtWorkers()}`);
}

const markProgress = (w, frame) => {
  done++;
  lastProgressAt = Date.now();
  if (w) { w.lastDone = frame; w.lastDoneAt = lastProgressAt; }
  if (done % progressEvery === 0 || done === N) logProgress();
};

async function openWorkerPage(w, useCpu) {
  w.stage = 'boot'; w.since = Date.now(); w.cpu = useCpu;
  const pg = await openPage(page, { query, onRenderError, callTimeout: frameTimeoutMs, cpu: useCpu });
  pages.push(pg);
  livePages.add(pg);
  w.pg = pg;
  return pg;
}

async function closeWorkerPage(w) {
  const pg = w.pg;
  w.pg = null;
  if (!pg) return;
  livePages.delete(pg);
  try { await pg.close(); } catch {}
}

async function captureWithRetry(w, frame, shotOpts) {
  let attempt = 0;
  let lastErr = null;
  while (attempt <= maxRetries && !aborted) {
    try {
      if (!w.pg || w.pg.isDead()) await openWorkerPage(w, w.cpu);
      w.frame = frame; w.stage = 'shot'; w.since = Date.now();
      return await w.pg.shot((frame + 0.5) / fps, { ...shotOpts, timeoutMs: frameTimeoutMs });
    } catch (err) {
      lastErr = err;
      const stuckStage = w.pg ? w.pg.getStage() : w.stage;
      console.error(`[render_fast +${elapsedS()}s] w${w.id} f${frame} failed on attempt ${attempt + 1}/${maxRetries + 1} (stage=${stuckStage}, cpu=${w.cpu}): ${err.message || err}`);
      await closeWorkerPage(w);
      attempt++;
      if (attempt <= maxRetries && !aborted) {
        if (!w.cpu && allowCpuFallback) {
          w.cpu = true;
          console.error(`[render_fast +${elapsedS()}s] w${w.id} respawning with software fallback (--disable-gpu) for f${frame}`);
        } else {
          console.error(`[render_fast +${elapsedS()}s] w${w.id} respawning Chrome for f${frame}`);
        }
        await sleep(300);
      }
    }
  }
  throw new Error(`w${w.id} failed at f${frame} after ${maxRetries + 1} attempt(s): ${lastErr?.message || lastErr}`);
}

async function cleanupAll(reason) {
  if (aborted) return;
  aborted = true;
  abortReason = reason;
  console.error(`[render_fast +${elapsedS()}s ABORT] ${reason}`);
  console.error(`[render_fast +${elapsedS()}s STATE] done=${done}/${N} wrote=${wrote} phase=${globalPhase} | ${fmtWorkers()}`);
  const partials = outputs.map(([tmp]) => tmp).filter((p) => fs.existsSync(p));
  if (partials.length) console.error(`[render_fast +${elapsedS()}s PARTIAL] incomplete temp output(s) preserved (deliverable untouched): ${partials.join(', ')}`);
  if (encProc && encProc.exitCode === null) {
    try { encProc.stdin.destroy(); } catch {}
    try { encProc.kill(); } catch {}
  }
  await Promise.all([...livePages].map((pg) => pg.close().catch(() => {})));
  livePages.clear();
}

const heartbeat = setInterval(() => {
  if (aborted) return;
  const idleMs = Date.now() - lastProgressAt;
  logProgress(idleMs >= 15000 ? `heartbeat idle=${(idleMs / 1000).toFixed(0)}s` : 'heartbeat');
  if (globalPhase === 'render' && idleMs >= stallTimeoutMs) {
    cleanupAll(`no new frame completed for ${(idleMs / 1000).toFixed(1)}s (stall-timeout=${stallTimeoutMs / 1000}s)`).finally(() => process.exit(1));
  }
}, 5000);
heartbeat.unref();

const onSignal = (sig) => { cleanupAll(`received ${sig}`).finally(() => process.exit(1)); };
process.once('SIGINT', onSignal);
process.once('SIGTERM', onSignal);

try {
  if (!disk) {
    // ---- pipe mode -----------------------------------------------------------------------------------------
    globalPhase = 'render';
    const enc = spawn(ff, ['-hide_banner', '-loglevel', 'error', '-y', ...encodeArgs(['-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-'])], { stdio: ['pipe', 'inherit', 'inherit'] });
    encProc = enc;
    let encErr = null;
    enc.on('error', (e) => { encErr = e; aborted = true; });
    enc.stdin.on('error', (e) => { if (!aborted) { encErr = e; aborted = true; } });
    const encDone = new Promise((res) => enc.on('close', (code) => {
      if (code && !aborted && wrote < N) { encErr = new Error(`ffmpeg exited early (${code}) at wrote=${wrote}/${N}`); aborted = true; }
      res(code);
    }));

    const ready = new Map();
    let writing = false;
    async function flush() {
      if (writing || aborted) return;
      writing = true;
      try {
        while (!aborted && ready.has(F0 + wrote)) {
          const b = ready.get(F0 + wrote);
          ready.delete(F0 + wrote);
          wrote++;
          if (!enc.stdin.write(b)) {
            await new Promise((r) => {
              const doneDrain = () => { enc.off('close', doneDrain); enc.stdin.off('error', doneDrain); r(); };
              enc.stdin.once('drain', doneDrain);
              enc.once('close', doneDrain);
              enc.stdin.once('error', doneDrain);
            });
          }
        }
      } finally {
        writing = false;
      }
    }

    const nWorkers = Math.min(W, N);
    for (let id = 0; id < nWorkers; id++) workerStates.push({ id, frame: null, stage: 'init', since: Date.now(), lastDone: null, lastDoneAt: t0, cpu: forceChromeCpu, pg: null });

    async function worker(w) {
      await openWorkerPage(w, forceChromeCpu);
      while (!aborted && next < N) {
        const i = next++;
        const frame = F0 + i;
        while (!aborted && i - wrote > 240) {
          w.frame = frame; w.stage = 'wait-reorder'; w.since = Date.now();
          await sleep(20);
        }
        if (aborted) break;
        const buf = await captureWithRetry(w, frame, { format: 'jpeg', quality: 95, scale });
        if (aborted) break;
        ready.set(frame, buf);
        markProgress(w, frame);
        w.stage = 'flush'; w.since = Date.now();
        flush();
      }
      w.stage = 'closing'; w.since = Date.now();
      await closeWorkerPage(w);
      w.stage = 'done';
    }

    await Promise.all(workerStates.map(worker));
    if (encErr) throw encErr;
    if (aborted) throw new Error(abortReason || 'aborted');
    globalPhase = 'encode-drain';
    lastProgressAt = Date.now();
    while (!aborted && wrote < N) { await flush(); await sleep(10); }
    enc.stdin.end();
    const code = await encDone;
    if (code) throw new Error('ffmpeg failed (' + code + ')');
  } else {
    // ---- disk mode (resumable & --patch-frames / --encode-only) --------------------------------------------
    const dir = path.join(path.dirname(outAbs), '_frames_' + path.basename(outAbs, path.extname(outAbs)));
    fs.mkdirSync(dir, { recursive: true });
    const fileOf = (f) => path.join(dir, `f${String(f).padStart(6, '0')}.${ext}`);

    if (patchSpec) {
      const patchList = parseFrames(patchSpec).filter((f) => f >= F0 && f <= F1);
      for (const f of patchList) fs.rmSync(fileOf(f), { force: true });
      console.log(`[render_fast] --patch-frames cleared ${patchList.length} frame(s) in ${dir}`);
    }

    const todo = [];
    for (let f = F0; f <= F1; f++) if (!fs.existsSync(fileOf(f)) || fs.statSync(fileOf(f)).size === 0) todo.push(f);
    const reused = N - todo.length;
    done = reused;
    if (reused > 0) console.log(`  ${reused}/${N} frames already on disk: reused${todo.length ? ` (${todo.length} to render)` : ' (encoding directly)'}`);

    if (encodeOnly && todo.length > 0) {
      throw new Error(`--encode-only requested, but ${todo.length} frame(s) are missing in ${dir} (first missing: f${todo[0]})`);
    }

    if (todo.length > 0) {
      globalPhase = 'render';
      const nWorkers = Math.min(W, todo.length);
      for (let id = 0; id < nWorkers; id++) workerStates.push({ id, frame: null, stage: 'init', since: Date.now(), lastDone: null, lastDoneAt: t0, cpu: forceChromeCpu, pg: null });

      async function worker(w) {
        await openWorkerPage(w, forceChromeCpu);
        while (!aborted && next < todo.length) {
          const f = todo[next++];
          const buf = await captureWithRetry(w, f, { format: fmt, scale });
          if (aborted) break;
          const dst = fileOf(f);
          const tmp = dst + '.part';
          fs.writeFileSync(tmp, buf);
          fs.renameSync(tmp, dst);
          markProgress(w, f);
        }
        w.stage = 'closing'; w.since = Date.now();
        await closeWorkerPage(w);
        w.stage = 'done';
      }

      await Promise.all(workerStates.map(worker));
      if (aborted) throw new Error(abortReason || 'aborted');
    }

    globalPhase = 'encode';
    lastProgressAt = Date.now();
    console.log(`[render_fast +${elapsedS()}s] encoding ${N} disk frames -> temporary MP4 ...`);
    const encTimeoutMs = Math.max(120000, N * 500);
    const r = spawnSync(ff, ['-hide_banner', '-loglevel', 'error', '-y', ...encodeArgs(['-framerate', String(fps), '-start_number', String(F0), '-i', path.join(dir, `f%06d.${ext}`)])], { stdio: 'inherit', timeout: encTimeoutMs });
    if (r.error) throw new Error(`ffmpeg encode error: ${r.error.message}`);
    if (r.status) throw new Error(`ffmpeg failed (${r.status})`);
    if (!keepFrames) fs.rmSync(dir, { recursive: true, force: true });
  }

  // Atomic commit: replace deliverables only after clean encode exit 0
  globalPhase = 'commit';
  for (const [tmp, dst] of outputs) {
    if (!fs.existsSync(tmp) || fs.statSync(tmp).size === 0) throw new Error(`missing encoded output ${tmp}`);
    fs.renameSync(tmp, dst);
  }
} catch (err) {
  clearInterval(heartbeat);
  await cleanupAll(err?.message || String(err));
  process.exit(1);
}

clearInterval(heartbeat);
const secs = (Date.now() - t0) / 1000;
for (const [, f] of outputs) if (fs.existsSync(f)) console.log(f, (fs.statSync(f).size / 1048576).toFixed(1) + ' MB');
console.log(`total ${secs.toFixed(1)} s (${(N / Math.max(0.05, secs)).toFixed(1)} frames/s incl. encoding)`);
const rep = errorReport(pages);
reportLines(rep).forEach((l) => console.log(l));
if (opt('--errors-json', '')) fs.writeFileSync(opt('--errors-json'), JSON.stringify(pages.map((p) => ({ renderErrors: p.renderErrors, errors: p.errors, renderLines: [...p.renderLines], ready: p.ready }))));
if (rep.count) { console.log(`render_fast: the page threw (${rep.count} kind(s), above): video written, NOT deliverable; exit 2`); process.exitCode = 2; }
