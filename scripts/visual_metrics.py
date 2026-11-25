"""visual_metrics.py — Objective pixel- & motion-density diagnostics for rendered MP4 clips.

Measures the visual fundamentals that catch washed-out palettes, missing dark ink,
parked/frozen holds, and "pop-in then freeze" motion waveforms:
  - sat_mean           : mean HSV saturation (0..1; catches faded grey/pastel washes like 0.11)
  - true_black_pct     : % pixels with real dark ink (max(R,G,B) < 60; ignores saturated cobalt/crimson)
  - paper_white_pct    : % pixels with bright paper/highlight (min(R,G,B) > 220)
  - motion_mad_mean    : mean frame-to-frame luminance MAD (0..255; catches overly calm/static sections)
  - motion_mad_p50     : median frame-to-frame luminance MAD
  - still_ratio        : share of frames with MAD < 0.35 (parked art)
  - motion_peaks_per_s : local motion peaks (MAD > 6) per second
  - hard_cuts / cuts_per_10s / longest_shot_s : shot cadence (MAD > 28)
  - long_holds         : frame ranges held > --max-hold-sec with low motion (MAD < 3.0)
  - motion_wave.png    : pure-Pillow per-frame MAD waveform (optional side-by-side vs --ref)

Usage:
  python -X utf8 scripts/visual_metrics.py out/preview_720p.mp4 --out work/metrics
  python -X utf8 scripts/visual_metrics.py out/act3_720p.mp4 --fps 30 --f0 2228 --label "Act 3" --out work/metrics
  python -X utf8 scripts/visual_metrics.py out/act3_720p.mp4 --ref ref.mp4 --ref-from 192.08 --ref-dur 15.25 --out work/metrics
  python -X utf8 scripts/visual_metrics.py out/act3_720p.mp4 --json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def find_ffmpeg() -> str:
    for env in ("CHIAKI_FFMPEG", "FFMPEG_PATH"):
        p = os.environ.get(env)
        if p and os.path.exists(p):
            return p
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
    raise RuntimeError("ffmpeg not found (install ffmpeg on PATH, set CHIAKI_FFMPEG, or `pip install imageio-ffmpeg`)")


def probe_fps(ff: str, path: str) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        cand = Path(ff).with_name("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
        if cand.exists():
            ffprobe = str(cand)
    if ffprobe:
        r = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        txt = (r.stdout or "").strip().splitlines()
        if txt:
            val = txt[0].strip()
            if "/" in val:
                a, b = val.split("/", 1)
                if float(b) > 0:
                    return float(a) / float(b)
            try:
                return float(val)
            except Exception:
                pass
    return 30.0


def grab_frames(ff: str, path: str, fps: float, t0: float = 0.0, dur: float = 0.0, w: int = 320, h: int = 180) -> np.ndarray:
    cmd = [ff, "-v", "error"]
    if t0 > 0:
        cmd += ["-ss", f"{t0:.4f}"]
    if dur > 0:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-i", path, "-vf", f"fps={fps:.4f},scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed for {path}: {r.stderr.decode('utf-8', 'replace')[:300]}")
    raw = r.stdout
    n = len(raw) // (w * h * 3)
    if n < 2:
        raise RuntimeError(f"decoded too few frames ({n}) from {path}")
    return np.frombuffer(raw[: n * w * h * 3], dtype=np.uint8).reshape(n, h, w, 3)


def compute_metrics(fr: np.ndarray, fps: float, label: str, f0: int = 0, max_hold_sec: float = 2.0) -> tuple[dict, np.ndarray]:
    f = fr.astype(np.float32)
    gray = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
    mad = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))

    cuts = [i + 1 for i, v in enumerate(mad) if v > 28.0]
    bounds = [0] + cuts + [len(fr)]
    shots = np.diff(bounds) / fps

    mx = f.max(axis=3)
    mn = f.min(axis=3)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1.0), 0.0).mean(axis=(1, 2))
    # True near-black ink (all three RGB channels dark — never miscounts saturated cobalt/crimson)
    true_black = (mx < 60.0).mean(axis=(1, 2))
    paper_white = (mn > 220.0).mean(axis=(1, 2))

    peaks = [i for i in range(1, len(mad) - 1) if mad[i] > 6.0 and mad[i] >= mad[i - 1] and mad[i] >= mad[i + 1]]
    parked = [f0 + 1 + i for i, x in enumerate(mad) if x < 0.35]

    hold_thresh_frames = max(2, int(round(max_hold_sec * fps)))
    run = 0
    long_holds = []
    for i, x in enumerate(mad):
        if x < 3.0:
            run += 1
            if run == hold_thresh_frames + 1:
                long_holds.append(f0 + i - hold_thresh_frames + 1)
        else:
            run = 0

    secs = len(fr) / fps
    data = {
        "label": label,
        "frames": int(len(fr)),
        "fps": round(float(fps), 3),
        "seconds": round(float(secs), 2),
        "hard_cuts": int(len(cuts)),
        "cuts_per_10s": round(float(len(cuts) / max(secs, 1e-6) * 10.0), 2),
        "longest_shot_s": round(float(shots.max()), 2),
        "motion_mad_mean": round(float(mad.mean()), 2),
        "motion_mad_p50": round(float(np.median(mad)), 2),
        "still_ratio": round(float((mad < 0.35).mean()), 3),
        "motion_peaks_per_s": round(float(len(peaks) / max(secs, 1e-6)), 2),
        "sat_mean": round(float(sat.mean()), 3),
        "true_black_pct": round(float(true_black.mean() * 100.0), 1),
        "paper_white_pct": round(float(paper_white.mean() * 100.0), 1),
        "parked_frame_count": int(len(parked)),
        "parked_frames_sample": parked[:40],
        "long_hold_starts": long_holds[:40],
    }
    return data, mad


def render_wave_png(rows: list[tuple[np.ndarray, str, tuple[int, int, int]]], out_png: Path) -> None:
    row_h, w = 220, 1500
    gap = 20
    img = Image.new("RGB", (w, row_h * len(rows) + gap * max(0, len(rows) - 1)), (250, 248, 242))
    dr = ImageDraw.Draw(img)
    for idx, (m, lab, col) in enumerate(rows):
        y0 = idx * (row_h + gap)
        dr.text((10, y0 + 6), f"{lab}  |  per-frame motion MAD (grey line = 6.0 active threshold)", fill=(20, 22, 26))
        n = max(1, len(m))
        for i, x in enumerate(m):
            xx = int(i / n * (w - 20)) + 10
            hh = int(min(float(x), 60.0) / 60.0 * (row_h - 34))
            dr.line([(xx, y0 + row_h - 6), (xx, y0 + row_h - 6 - hh)], fill=col)
        yy = y0 + row_h - 6 - int(6.0 / 60.0 * (row_h - 34))
        dr.line([(10, yy), (w - 10, yy)], fill=(155, 155, 160))
    img.save(out_png)


def main() -> int:
    ap = argparse.ArgumentParser(description="Objective visual & motion-density metrics for rendered MP4s")
    ap.add_argument("video", help="Path to rendered MP4 clip")
    ap.add_argument("--from", dest="t_from", type=float, default=0.0, help="Start second in video")
    ap.add_argument("--dur", type=float, default=0.0, help="Duration seconds (0 = full clip)")
    ap.add_argument("--fps", type=float, default=0.0, help="Sampling FPS (0 = auto-probe video FPS)")
    ap.add_argument("--f0", type=int, default=0, help="Timeline starting frame index for parked/hold reports")
    ap.add_argument("--label", default="", help="Display label for report & waveform")
    ap.add_argument("--max-hold-sec", type=float, default=2.0, help="Flag low-motion holds longer than N seconds")
    ap.add_argument("--ref", default="", help="Optional reference MP4 for side-by-side waveform comparison")
    ap.add_argument("--ref-from", type=float, default=0.0, help="Start second in reference MP4")
    ap.add_argument("--ref-dur", type=float, default=0.0, help="Duration seconds in reference MP4")
    ap.add_argument("--ref-fps", type=float, default=0.0, help="FPS of reference MP4 (0 = auto-probe)")
    ap.add_argument("--out", default="", help="Output directory for metrics.json + motion_wave.png")
    ap.add_argument("--json", action="store_true", help="Print JSON summary to stdout")
    args = ap.parse_args()

    vp = Path(args.video)
    if not vp.exists():
        sys.exit(f"Video not found: {vp}")
    ff = find_ffmpeg()
    fps = args.fps if args.fps > 0 else probe_fps(ff, str(vp))
    label = args.label or vp.stem

    fr = grab_frames(ff, str(vp), fps=fps, t0=args.t_from, dur=args.dur)
    data, mad = compute_metrics(fr, fps=fps, label=label, f0=args.f0, max_hold_sec=args.max_hold_sec)

    results = [data]
    wave_rows = [(mad, f"{label} ({data['seconds']}s @ {fps:g}fps)", (232, 28, 79))]

    if args.ref:
        rp = Path(args.ref)
        if not rp.exists():
            sys.exit(f"Reference video not found: {rp}")
        rfps = args.ref_fps if args.ref_fps > 0 else probe_fps(ff, str(rp))
        rfr = grab_frames(ff, str(rp), fps=rfps, t0=args.ref_from, dur=args.ref_dur)
        rdata, rmad = compute_metrics(rfr, fps=rfps, label=f"REF: {rp.stem}", f0=0, max_hold_sec=args.max_hold_sec)
        results.insert(0, rdata)
        wave_rows.insert(0, (rmad, f"REF {rp.stem} ({rdata['seconds']}s @ {rfps:g}fps)", (90, 43, 255)))

    if args.out:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        render_wave_png(wave_rows, out_dir / "motion_wave.png")

    if args.json:
        print(json.dumps(results if len(results) > 1 else data, ensure_ascii=False, indent=2))
    else:
        for d in results:
            print(
                f"[{d['label']}] {d['frames']}f ({d['seconds']}s @ {d['fps']:g}fps) | "
                f"sat={d['sat_mean']:.3f} | true_black={d['true_black_pct']:.1f}% | paper={d['paper_white_pct']:.1f}% | "
                f"MAD_mean={d['motion_mad_mean']:.2f} (p50={d['motion_mad_p50']:.2f}) | "
                f"still={d['still_ratio']:.3f} | peaks/s={d['motion_peaks_per_s']:.2f} | "
                f"cuts={d['hard_cuts']} ({d['cuts_per_10s']:.1f}/10s, max_shot={d['longest_shot_s']:.2f}s)"
            )
            if d["parked_frame_count"]:
                print(f"  parked frames (MAD < 0.35): {d['parked_frame_count']} sample={d['parked_frames_sample'][:20]}")
            if d["long_hold_starts"]:
                print(f"  low-motion holds > {args.max_hold_sec:g}s starting at frames: {d['long_hold_starts'][:20]}")
        if args.out:
            print(f"wrote: {Path(args.out) / 'metrics.json'} & {Path(args.out) / 'motion_wave.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
