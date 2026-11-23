"""Beat / accent map for cut timing — standard library only (no numpy).

Claude can't hear music, so this turns the track into numbers: tempo, a beat grid, and
the strongest onsets (drops, hits) as seconds AND 24 fps frame numbers, so cuts, flashes
and title slams can be put on the beat.

Usage:
  python -X utf8 beats.py <audio-or-video> [--from 0] [--to 0] [--fps 24] [--ffmpeg PATH] [--top 40] [--bpm N] [--json PATH]
Prints the report to stdout only; with --json PATH it also writes the same data to that file. --bpm N forces the
tempo (skips detection), for when the accents' spacing disagrees with the estimate.

Method: decode mono 11025 Hz via ffmpeg -> RMS energy per 512-sample hop (~46 ms) ->
onset strength = positive energy rise (log-compressed) -> tempo by autocorrelation over
70–180 BPM -> beat phase that maximises onset strength on the grid -> peak-picked accents.
Treat the output as a strong hint: confirm important sync points with the user's ears.
"""
import argparse, array, glob, json, math, os, shutil, subprocess, sys

SR, HOP = 11025, 512
sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to GBK and garble "≈"


def find_ffmpeg(explicit=""):
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


def decode(ff, src, t0, t1):
    cmd = [ff, "-hide_banner", "-loglevel", "error", "-ss", str(t0)]
    if t1 > 0:
        cmd += ["-to", str(t1)]
    cmd += ["-i", src, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
    a = array.array("h")
    a.frombytes(raw[: len(raw) // 2 * 2])
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=0.0)
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--ffmpeg", default="")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--json", default="")
    ap.add_argument("--bpm", type=float, default=0.0, help="force tempo (skip detection), e.g. when accents' spacing disagrees with the estimate")
    a = ap.parse_args()

    pcm = decode(find_ffmpeg(a.ffmpeg), a.src, a.t0, a.t1)
    n = len(pcm) // HOP
    if n < 20:
        sys.exit("audio too short")
    env = []
    for i in range(n):
        s = 0
        for v in pcm[i * HOP:(i + 1) * HOP]:
            s += v * v
        env.append(math.log1p(math.sqrt(s / HOP)))
    onset = [0.0] + [max(0.0, env[i] - env[i - 1]) for i in range(1, n)]
    # subtract local mean (≈0.5 s) so sustained loud parts don't dominate
    w = 6
    loc = [sum(onset[max(0, i - w):i + w + 1]) / len(onset[max(0, i - w):i + w + 1]) for i in range(n)]
    od = [max(0.0, onset[i] - loc[i]) for i in range(n)]

    hop_s = HOP / SR
    if a.bpm:
        bpm = a.bpm
    else:
        # Fine onset envelope (128-sample hop ≈ 11.6 ms) + comb autocorrelation with fractional
        # lags over 1–4 periods. The old integer-lag search on 46 ms hops rounded 123 BPM to 112.
        fh = 128
        m = len(pcm) // fh
        e2 = []
        for i in range(m):
            s = 0
            for v in pcm[i * fh:(i + 1) * fh]:
                s += v * v
            e2.append(math.log1p(math.sqrt(s / fh)))
        o2 = [0.0] + [max(0.0, e2[i] - e2[i - 1]) for i in range(1, m)]
        w2 = 24
        pre = [0.0]
        for v in o2:
            pre.append(pre[-1] + v)
        o2 = [max(0.0, o2[i] - (pre[min(m, i + w2 + 1)] - pre[max(0, i - w2)]) / (min(m, i + w2 + 1) - max(0, i - w2))) for i in range(m)]
        fs = fh / SR

        def at(x):
            i = int(x); f = x - i
            return o2[i] * (1 - f) + o2[i + 1] * f if i + 1 < m else 0.0

        best = (0, 120.0)
        for bpm10 in range(700, 1801, 2):
            lagf = 60.0 / (bpm10 / 10) / fs
            sc = 0.0
            for mult, wgt in ((1, 1.0), (2, 0.8), (3, 0.6), (4, 0.5)):
                L = lagf * mult
                if L >= m - 2:
                    break
                sc += wgt * sum(o2[i] * at(i - L) for i in range(int(L) + 1, m, 2)) / (m - L)
            if sc > best[0]:
                best = (sc, bpm10 / 10)
        bpm = best[1]
        # prefer the 80–160 BPM octave (cuts are planned per beat)
        while bpm < 80: bpm *= 2
        while bpm > 160: bpm /= 2
    period = 60.0 / bpm
    # phase: try 32 offsets within one period
    phases = []
    for k in range(32):
        ph = period * k / 32
        sc, t = 0.0, ph
        while t < n * hop_s:
            sc += od[min(n - 1, int(round(t / hop_s)))]
            t += period
        phases.append((sc, ph))
    phase = max(phases)[1]
    beats = []
    t = phase
    while t < n * hop_s:
        beats.append(t)
        t += period

    # accents: local maxima of od above mean+2sd, at least 0.25 s apart, strongest first
    mean = sum(od) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in od) / n)
    thr = mean + 2 * sd
    peaks = [i for i in range(1, n - 1) if od[i] >= thr and od[i] >= od[i - 1] and od[i] > od[i + 1]]
    peaks.sort(key=lambda i: -od[i])
    chosen = []
    for i in peaks:
        if all(abs(i - j) * hop_s >= 0.25 for j in chosen):
            chosen.append(i)
        if len(chosen) >= a.top:
            break
    chosen.sort()
    mx = max(od) or 1

    def fmt(sec):
        T = sec + a.t0
        return {"t": round(T, 3), "frame": int(round(T * a.fps))}

    out = {
        "bpm": bpm,
        "beat_period_s": round(period, 4),
        "frames_per_beat": round(period * a.fps, 2),
        "beats": [fmt(b) for b in beats],
        "accents": [dict(fmt(i * hop_s), strength=round(od[i] / mx, 2)) for i in chosen],
    }
    print(f"tempo ≈ {bpm:.1f} BPM  (1 beat = {period:.3f}s = {period * a.fps:.1f} frames @ {a.fps:g}fps)")
    print(f"beat grid starts at {beats[0] + a.t0:.3f}s; {len(beats)} beats")
    print("strongest accents (time s / frame / strength 0-1):")
    for x in out["accents"]:
        print(f"  {x['t']:9.3f}  f{x['frame']:<6d} {x['strength']:.2f}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("wrote", a.json)


if __name__ == "__main__":
    main()
