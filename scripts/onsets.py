"""onsets.py — where exactly does a hit land? Run with Python (-X utf8); needs numpy + ffmpeg.

  onsets.py <audio> <from-to> [<from-to> ...] [--fps 24] [--quiet]
      <audio>: any file ffmpeg reads (the FINAL soundtrack of the film); ranges are video frames, e.g. 425-442.
      For each range, per half frame: the low-band envelope (< 150 Hz, 25 ms RMS), broadband spectral flux (> 150 Hz,
      STFT 2048, hop 1 ms, positive differences only) and low-band flux. Then two answers:
        downbeat  = the frame holding the broadband flux peak (clap/snare + full band): put the cut / the slam HERE,
                    i.e. on floor(onset frame), the frame that contains the onset — never a rounded beat-grid frame;
        low rise  = the first frame where the low envelope passes half of its range max (808 or bass slide).
      A low rise several frames before the downbeat is a pre-roll (an 808 sliding in), not the hit.
"""
import argparse, os, shutil, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('audio'); ap.add_argument('ranges', nargs='+'); ap.add_argument('--fps', type=float, default=24.0)
ap.add_argument('--quiet', action='store_true', help='only the two answers per range')
a = ap.parse_args()
def _find_ffmpeg(explicit=""):
    if explicit and os.path.exists(explicit):
        return explicit
    for env in ("CHIAKI_FFMPEG", "FFMPEG_PATH", "QCRV_FFMPEG"):
        v = os.environ.get(env)
        if v and os.path.exists(v):
            return v
    w = shutil.which("ffmpeg")
    if w:
        return w
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    sys.exit("ffmpeg not found: install ffmpeg on PATH or `pip install imageio-ffmpeg`, or set CHIAKI_FFMPEG")

ff = _find_ffmpeg()
SR = 44100
raw = subprocess.run([ff, '-v', 'error', '-i', a.audio, '-map', '0:a:0', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
if not raw: sys.exit('could not decode ' + a.audio)
x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
FPS = a.fps
X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR)
low = np.fft.irfft(np.where(fr < 150, X, 0), n=len(x))
wl = int(SR * 0.025)
lenv = np.sqrt(np.convolve(low ** 2, np.ones(wl) / wl, mode='same'))
lenv = lenv / (lenv.max() or 1) * 100
N, hop = 2048, SR // 1000
win, fb = np.hanning(N), np.fft.rfftfreq(N, 1 / SR)


def flux(i0, i1):   # per 1 ms from sample i0 to i1: broadband (> 150 Hz) and low-band flux
    hi, lo, prev = [], [], None
    for i in range(i0 - 20 * hop, i1, hop):
        seg = x[max(0, i - N // 2): i + N // 2]
        if len(seg) < N: seg = np.pad(seg, (0, N - len(seg)))
        m = np.log1p(np.abs(np.fft.rfft(seg * win)) * 50)
        if prev is not None:
            d = np.maximum(0, m - prev); hi.append(d[fb >= 150].sum()); lo.append(d[fb < 150].sum())
        prev = m
    return np.array(hi[19:]), np.array(lo[19:])


for arg in a.ranges:
    f0, f1 = [float(v) for v in arg.split('-')]
    i0, i1 = int(f0 / FPS * SR), int(f1 / FPS * SR)
    fh, fl = flux(i0, i1)
    if not len(fh): print(f'--- {arg}: outside the audio'); continue
    seg_env = lenv[i0:i1]; half = seg_env.max() / 2
    rise = next((k for k in range(len(seg_env)) if seg_env[k] >= half), None)
    rise_frame = f0 + rise / SR * FPS if rise is not None else None
    # broadband peaks: local maxima of the 1-ms flux that reach 85 % of the range max
    top = fh.max()
    peaks = [(f0 + k / 1000 * FPS, fh[k]) for k in range(1, len(fh) - 1)
             if fh[k] >= 0.85 * top and fh[k] >= fh[k - 1] and fh[k] >= fh[k + 1]]
    peaks = [p for i, p in enumerate(peaks) if not any(abs(p[0] - q[0]) < 1 and q[1] > p[1] for q in peaks)]   # one per frame
    peak_frame = max(peaks, key=lambda p: p[1])[0] if peaks else f0 + int(np.argmax(fh)) / 1000 * FPS
    # an 808 / bass slide makes its own broadband click when it starts: if a peak of about the same height follows the
    # low-band rise by 1.5–6 frames, that later one is the downbeat (rank4 v13: slide at 2123, clap + full band at 2126)
    if rise_frame is not None:
        after = [p for p in peaks if rise_frame + 1.5 <= p[0] <= rise_frame + 6]
        if after: peak_frame = max(after, key=lambda p: p[1])[0]
    rivals = [p for p in peaks if abs(p[0] - peak_frame) >= 1]
    if not a.quiet:
        print(f'--- frames {f0:g}-{f1:g}: per half frame   low env 25 ms | flux > 150 Hz (max in window) | flux < 150 Hz')
        f = f0
        while f < f1:
            j0, j1 = int((f - f0) / FPS * 1000), int((f + 0.5 - f0) / FPS * 1000)
            i = min(int(f / FPS * SR), len(lenv) - 1)
            h = fh[j0:j1].max() if j1 > j0 and j0 < len(fh) else 0
            l = fl[j0:j1].max() if j1 > j0 and j0 < len(fl) else 0
            print(f'  {f:7.1f}  {lenv[i]:5.1f} {"#" * int(lenv[i] / 4):25s} | {h:6.1f} {"*" * int(h / 25):20s} | {l:5.1f}')
            f += 0.5
    msg = f'{arg}: downbeat (broadband flux peak) at frame {peak_frame:.2f} -> cut/slam on f{int(np.floor(peak_frame))}'
    if rise_frame is not None:
        msg += f'; low-band rise at {rise_frame:.2f}' + (f' ({peak_frame - rise_frame:.1f} f earlier: a pre-roll, not the hit)' if peak_frame - rise_frame > 1.5 else '')
    if rivals:
        msg += '\n  other peaks of nearly the same height: ' + ', '.join(f'{p[0]:.2f}' for p in rivals) + ': check this one by eye and ear'
    print(msg)
