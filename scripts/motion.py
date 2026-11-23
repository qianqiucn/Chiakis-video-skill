"""Motion-curve check: how much the picture moves per frame, and its shape inside shots.

Compares a build against the reference genre so motion follows the style (references/style-grammar.md §6b).
Usage:  python -X utf8 motion.py <video> <start> <dur> [<video2> <start2> <dur2> ...]
Prints per range: mean in-shot motion, variation (CV), front/back ratio (>1 = snaps in then
settles, <1 = starts still then builds), and an ASCII sparkline (cuts = tall spikes).
Metric: mean |frame_n − frame_n−1| luma at 320 px wide (ffmpeg tblend difference + signalstats).
Measured 2026-11-05 on the reference: Gemini idol-stage 7.8 / CV 0.94 / ratio 1.80;
Claude literary MAD 7.9 / 0.77 / 0.64. Our first originals: 10–14 / 0.5–1.2 / ~0.9 (too busy, flat).
"""
import glob, os, shutil, statistics as st, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")


def ffmpeg():
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


def series(ff, src, t0, dur):
    out = subprocess.run([ff, "-hide_banner", "-ss", str(t0), "-t", str(dur), "-i", src, "-vf",
                          "scale=320:-1,format=gray,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                          "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout
    return [float(l.split("=")[1]) for l in out.splitlines() if "YAVG=" in l]


def report(name, v):
    s = sorted(v); thr = s[int(len(s) * 0.94)]
    runs, cur = [], []
    for x in v:
        if x >= thr:
            if len(cur) > 6: runs.append(cur)
            cur = []
        else:
            cur.append(x)
    if len(cur) > 6: runs.append(cur)
    inner = [x for r in runs for x in r] or v
    ratios = [sum(r[:len(r) // 3]) / max(1e-6, sum(r[-(len(r) // 3):])) for r in runs] or [1]
    cv = st.pstdev(inner) / max(1e-6, st.mean(inner))
    print(f"{name}: in-shot motion {st.mean(inner):5.2f} | CV {cv:.2f} | front/back {st.median(ratios):.2f} | shots {len(runs)}")
    bars = " .:-=+*#%@"; mx = s[int(len(s) * 0.97)] or 1
    print("   " + "".join(bars[min(9, int(min(x, mx) / mx * 9.99))] for x in v[:150]))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3 or len(a) % 3:
        sys.exit(__doc__)
    ff = ffmpeg()
    for i in range(0, len(a), 3):
        report(f"{os.path.basename(a[i])}@{a[i+1]}+{a[i+2]}", series(ff, a[i], a[i + 1], a[i + 2]))
