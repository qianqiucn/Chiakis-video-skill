"""vocal_spec.py — host-aware vocal & lyric timing helper for Chiaki's-video-skill.

Drum/onset trackers (`beats.py`, `onsets.py`) lock percussion transients, NOT human vocal syllables.
Best practice (Stage 1 Dual-Stem Rule): run `scripts/stem_sync.py <song> --out work/stems --fps <FPS>` FIRST,
then feed the isolated dry vocal stem (`work/stems/vocals.wav`) into `vocal_spec.py` (zero drum/synth bleed!),
and feed the isolated instrumental stem (`work/stems/instrumental.wav`) into `beats.py` / `onsets.py`.
Hard Host-Split Rule (rules/AGENTS.md §3):
  - Gemini hosts (native audio/video multimodal): run with `--wav-only` to slice clean 3-6 s mono WAV
    clips quickly, then listen directly via multimodal `read_file` on the WAVs (render spectrograms only
    if double-checking an ambiguous frame boundary).
  - Claude / Codex hosts (traditional spectrum + image workflow): run without `--wav-only` to render
    high-contrast, frame-numbered 300 Hz - 4 kHz vocal spectrograms + syllabic energy envelopes (`spec_*.png`).

Usage:
  python -X utf8 scripts/vocal_spec.py <audio> --out <dir> --fps 24 --wav-only               # Gemini fast micro-WAVs
  python -X utf8 scripts/vocal_spec.py <audio> --out <dir> --fps 24 --ranges 0-5,28-34.5     # Claude/Codex WAV + PNG spec
  python -X utf8 scripts/vocal_spec.py <audio> --out <dir> --fps 24 --ranges f672-f816
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import signal

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _find_ffmpeg(explicit: str = "") -> str:
    if explicit and os.path.exists(explicit):
        return explicit
    for env in ("CHIAKI_FFMPEG", "FFMPEG_PATH"):
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


def _magma_lut() -> np.ndarray:
    """256x3 high-contrast inferno/magma-like RGB lookup table (pure numpy, zero matplotlib dep)."""
    stops = np.array([
        [0.00,   8,   6,  18],
        [0.20,  58,  15,  96],
        [0.45, 165,  38, 102],
        [0.70, 238, 108,  45],
        [0.88, 252, 198,  58],
        [1.00, 255, 252, 210],
    ], dtype=np.float64)
    idx = np.linspace(0.0, 1.0, 256)
    lut = np.zeros((256, 3), dtype=np.uint8)
    for c in range(3):
        lut[:, c] = np.clip(np.interp(idx, stops[:, 0], stops[:, c + 1]), 0, 255).astype(np.uint8)
    return lut


LUT = _magma_lut()


def _parse_ranges(spec: str, total_s: float, fps: float, chunk: float) -> list[tuple[float, float]]:
    if not spec.strip():
        out = []
        t = 0.0
        step = max(1.0, chunk)
        while t < total_s - 0.05:
            out.append((t, min(total_s, t + step)))
            t += step
        return out
    out = []
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok or "-" not in tok:
            continue
        a, b = tok.split("-", 1)
        a, b = a.strip(), b.strip()
        if a.lower().startswith("f") or b.lower().startswith("f"):
            t0 = float(a.lstrip("fF")) / fps
            t1 = float(b.lstrip("fF")) / fps
        else:
            t0, t1 = float(a), float(b)
        t0 = max(0.0, min(total_s, t0))
        t1 = max(t0 + 0.2, min(total_s, t1))
        out.append((t0, t1))
    return out


def _write_wav(path: Path, samples_i16: np.ndarray, sr: int) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples_i16.tobytes())


def _render_spec(
    seg: np.ndarray,
    sr: int,
    t0: float,
    t1: float,
    fps: float,
    max_hz: float,
    out_png: Path,
) -> None:
    dur = max(0.1, t1 - t0)
    # 1024-pt STFT (~23 ms window, ~3 ms hop) gives clean syllabic & formant resolution
    nperseg = 1024
    noverlap = 896
    freqs, times, Sxx = signal.spectrogram(
        seg, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap, mode="magnitude"
    )
    f_mask = freqs <= max_hz
    freqs = freqs[f_mask]
    S = Sxx[f_mask, :]
    db = 20.0 * np.log10(S + 1e-7)
    peak_db = float(np.percentile(db, 99.7))
    lo_db = peak_db - 62.0
    norm = np.clip((db - lo_db) / max(1e-6, peak_db - lo_db), 0.0, 1.0)

    # Vocal formant band (300 - 4000 Hz) syllabic RMS envelope
    v_mask = (freqs >= 300.0) & (freqs <= min(4000.0, max_hz))
    v_energy = np.sqrt(np.mean(S[v_mask, :] ** 2, axis=0)) if np.any(v_mask) else np.zeros(S.shape[1])
    v_peak = float(np.percentile(v_energy, 99.5)) or 1.0
    v_norm = np.clip(v_energy / v_peak, 0.0, 1.0)

    # Canvas geometry
    pad_l, pad_r, pad_t, pad_mid, pad_b = 72, 24, 46, 18, 38
    plot_w = int(np.clip(round(dur * 260), 960, 2200))
    spec_h = 340
    env_h = 96
    W = pad_l + plot_w + pad_r
    H = pad_t + spec_h + pad_mid + env_h + pad_b

    # Upsample spectrogram to (spec_h, plot_w) with 0 Hz at bottom, max_hz at top
    spec_idx = np.clip((norm[::-1, :] * 255.0).round(), 0, 255).astype(np.uint8)
    spec_rgb = LUT[spec_idx]
    spec_img = Image.fromarray(spec_rgb, mode="RGB").resize((plot_w, spec_h), Image.BILINEAR)

    canvas = Image.new("RGB", (W, H), (14, 16, 22))
    canvas.paste(spec_img, (pad_l, pad_t))
    dr = ImageDraw.Draw(canvas)

    # Borders & envelope background
    env_y0 = pad_t + spec_h + pad_mid
    env_y1 = env_y0 + env_h
    dr.rectangle([pad_l, env_y0, pad_l + plot_w, env_y1], fill=(18, 22, 30), outline=(58, 66, 82))
    dr.rectangle([pad_l, pad_t, pad_l + plot_w, pad_t + spec_h], outline=(78, 86, 102))

    # Frequency guides + vocal band bracket (300 - 4000 Hz)
    def y_of_hz(hz: float) -> int:
        return int(round(pad_t + spec_h * (1.0 - hz / max_hz)))

    y_300 = y_of_hz(300.0)
    y_4000 = y_of_hz(min(4000.0, max_hz))
    # Cyan bracket on left edge of plot showing vocal formant range
    dr.rectangle([pad_l - 6, y_4000, pad_l - 2, y_300], fill=(70, 220, 255))

    for hz in (300, 1000, 2000, 3000, 4000):
        if hz > max_hz:
            continue
        yy = y_of_hz(hz)
        col = (70, 220, 255) if hz in (300, 4000) else (130, 140, 160)
        for xx in range(pad_l, pad_l + plot_w, 10):
            dr.line([(xx, yy), (min(pad_l + plot_w, xx + 4), yy)], fill=col, width=1)
        label = f"{hz // 1000}k" if hz >= 1000 else f"{hz}"
        dr.text((10, yy - 6), f"{label}Hz", fill=col)

    # Frame grid & labels
    f_start = int(math.floor(t0 * fps))
    f_end = int(math.ceil(t1 * fps))
    total_f = max(1, f_end - f_start)
    major_step = 6 if total_f <= 160 else 12 if total_f <= 320 else 24
    minor_step = 1 if total_f <= 96 else 2 if total_f <= 200 else 6

    def x_of_frame(fr: float) -> int:
        t = fr / fps
        return int(round(pad_l + (t - t0) / dur * plot_w))

    for fr in range(f_start, f_end + 1):
        xx = x_of_frame(fr)
        if xx < pad_l or xx > pad_l + plot_w:
            continue
        is_major = (fr % major_step == 0)
        is_minor = (fr % minor_step == 0)
        if is_major:
            dr.line([(xx, pad_t - 6), (xx, pad_t + spec_h)], fill=(190, 210, 235), width=1)
            dr.line([(xx, env_y0), (xx, env_y1 + 5)], fill=(115, 130, 155), width=1)
            dr.text((xx - 14, pad_t - 22), f"f{fr}", fill=(245, 232, 170))
            dr.text((xx - 14, env_y1 + 8), f"{fr / fps:.2f}s", fill=(165, 178, 200))
        elif is_minor:
            dr.line([(xx, pad_t - 3), (xx, pad_t)], fill=(110, 120, 140), width=1)
            dr.line([(xx, env_y1), (xx, env_y1 + 3)], fill=(90, 100, 118), width=1)

    # Plot vocal formant energy curve in bottom strip
    if len(times) >= 2:
        pts = []
        for t_rel, val in zip(times, v_norm):
            xx = int(round(pad_l + (t_rel / dur) * plot_w))
            yy = int(round(env_y1 - 4 - val * (env_h - 10)))
            pts.append((xx, yy))
        # Fill under curve lightly
        poly = [(pts[0][0], env_y1 - 1)] + pts + [(pts[-1][0], env_y1 - 1)]
        dr.polygon(poly, fill=(28, 72, 92))
        dr.line(pts, fill=(92, 235, 255), width=2)

    dr.text((pad_l, 8), f"VOCAL SPECTROGRAM (300-4000 Hz highlighted)   f{f_start}-f{f_end} ({t0:.2f}s-{t1:.2f}s @ {fps:g} fps)", fill=(235, 240, 248))
    dr.text((8, env_y0 + 6), "VOCAL", fill=(92, 235, 255))
    dr.text((8, env_y0 + 22), "300-4k", fill=(140, 165, 185))
    dr.text((8, env_y0 + 38), "ENV", fill=(140, 165, 185))

    canvas.save(out_png)


def main() -> int:
    ap = argparse.ArgumentParser(description="Slice vocal micro-WAVs + frame-numbered spectrograms for lyric timing")
    ap.add_argument("audio", help="Input audio file (wav/mp3/flac/mp4)")
    ap.add_argument("--out", required=True, help="Output directory for micro-WAVs and PNG spectrograms")
    ap.add_argument("--fps", type=float, default=24.0, help="Video frame rate (default 24)")
    ap.add_argument("--ranges", default="", help="Comma-separated sec or frame spans, e.g. '0-5,28-34.5' or 'f672-f816'")
    ap.add_argument("--chunk", type=float, default=5.0, help="Auto-slice window in seconds when --ranges is omitted (default 5.0)")
    ap.add_argument("--max-hz", type=float, default=5000.0, help="Top spectrogram frequency in Hz (default 5000)")
    ap.add_argument("--wav-only", action="store_true", help="Slice micro-WAV clips only (fast mode for Gemini native audio listening; skips PNG spectrograms)")
    a = ap.parse_args()

    ff = _find_ffmpeg()
    sr = 44100
    raw = subprocess.run(
        [ff, "-v", "error", "-i", a.audio, "-map", "0:a:0", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
        capture_output=True,
    ).stdout
    if not raw:
        sys.exit(f"Could not decode audio: {a.audio}")

    pcm = np.frombuffer(raw, dtype=np.int16)
    x = pcm.astype(np.float64) / 32768.0
    total_s = len(x) / sr
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    spans = _parse_ranges(a.ranges, total_s, a.fps, a.chunk)
    if not spans:
        sys.exit("No valid time ranges parsed.")

    mode_lbl = "wav-only (Gemini native audio)" if a.wav_only else "wav + spectrogram (Claude/Codex traditional)"
    print(f"vocal_spec [{mode_lbl}]: {Path(a.audio).name} ({total_s:.2f}s @ {a.fps:g} fps) -> {out_dir}")
    for idx, (t0, t1) in enumerate(spans):
        i0 = max(0, int(round(t0 * sr)))
        i1 = min(len(pcm), int(round(t1 * sr)))
        if i1 - i0 < 1024:
            continue
        f0 = int(round(t0 * a.fps))
        f1 = int(round(t1 * a.fps))
        tag = f"{idx:02d}_f{f0:04d}_f{f1:04d}"
        wav_p = out_dir / f"clip_{tag}.wav"
        _write_wav(wav_p, pcm[i0:i1], sr)
        if a.wav_only:
            print(f"  [{idx:02d}] f{f0:4d}-f{f1:4d} ({t0:6.2f}s-{t1:6.2f}s) -> {wav_p.name}")
        else:
            png_p = out_dir / f"spec_{tag}.png"
            _render_spec(x[i0:i1], sr, t0, t1, a.fps, a.max_hz, png_p)
            print(f"  [{idx:02d}] f{f0:4d}-f{f1:4d} ({t0:6.2f}s-{t1:6.2f}s) -> {wav_p.name} + {png_p.name}")

    if a.wav_only:
        print("Gemini host rule: listen directly to each clip_*.wav via multimodal read_file to lock exact sung lyric frames.")
    else:
        print("Claude/Codex host rule: inspect spec_*.png (300-4000 Hz vocal formants + envelope) before locking Gate A lyric frames.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
