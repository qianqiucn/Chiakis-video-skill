"""stem_sync.py — Stage-1 vocal/instrumental stem separation & dual-stem timing tool for Chiaki's-video-skill.

Why separate stems BEFORE storyboarding or cutting any song/lyric PV:
  1. Pure instrumental stem (`instrumental.wav`) -> crisp <130 Hz kick transients, clean `beats.py` / `onsets.py`
     without vocal sibilance contamination, AND automatic per-section local BPM drift detection.
  2. Pure dry vocal stem (`vocals.wav`) -> silence-bounded lyric phrase islands, razor-sharp 180-4500 Hz
     syllable onset peaks, crystal-clear dry-vocal micro-WAVs (Gemini native listening) & clean spectrograms
     (Claude/Codex), plus optional `faster-whisper` word timestamps cross-snapped to dry vocal attacks.

Backends (auto-detected, zero-config):
  - `audio-separator` (recommended, MIT): defaults to SOTA `vocals_mel_band_roformer.ckpt` (or `--fast` for
    lightweight 60 MB ONNX `UVR-MDX-NET-Inst_HQ_3.onnx`). Auto-uses NVIDIA CUDA / Apple MPS if available.
  - `demucs` (fallback, MIT): `htdemucs --two-stems=vocals`.
  - `dsp` (emergency fallback via `--fallback-dsp` only): pure FFmpeg/numpy Mid-Side + band split when no AI
    separator is installed (explicitly tagged as fallback; install `audio-separator` for studio separation).

Supports delegating separation / Whisper to a dedicated venv via `--stem-python` or `CHIAKI_STEM_PYTHON`.

Usage:
  python -X utf8 scripts/stem_sync.py song.wav --out work/stems --fps 30
  python -X utf8 scripts/stem_sync.py song.wav --out work/stems --fps 30 --whisper --lang ja --lyrics lyrics.txt
  python -X utf8 scripts/stem_sync.py song.wav --out work/stems --fps 24 --fast
  python -X utf8 scripts/stem_sync.py song.wav --out work/stems --fps 30 --vocals work/stems/vocals.wav --instrumental work/stems/instrumental.wav --whisper
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DEFAULT_MODEL = "vocals_mel_band_roformer.ckpt"
FAST_MODEL = "UVR-MDX-NET-Inst_HQ_3.onnx"


def _find_ffmpeg(explicit: str = "") -> str:
    if explicit and os.path.exists(explicit):
        return explicit
    for env in ("CHIAKI_FFMPEG", "FFMPEG_PATH"):
        v = os.environ.get(env, "").strip()
        if v and os.path.exists(v):
            return v
    w = shutil.which("ffmpeg")
    if w:
        return w
    # Check sibling bin/ next to venv (common in standalone audio-separator installs)
    for cand in (
        Path(sys.executable).resolve().parent / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"),
        Path(sys.executable).resolve().parent.parent.parent / "bin" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"),
    ):
        if cand.exists():
            return str(cand)
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    sys.exit("ffmpeg not found: install ffmpeg on PATH or `pip install imageio-ffmpeg`, or set CHIAKI_FFMPEG")


def _default_model_dir() -> Path:
    env_dir = os.environ.get("CHIAKI_STEM_MODELS", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    hf = os.environ.get("HF_HOME", "").strip()
    if hf:
        return (Path(hf).expanduser().resolve() / "chiaki-stems")
    return (Path.home() / ".chiaki-studio" / "stem-models").resolve()


def _ensure_ffmpeg_on_path(ff_path: str, shim_root: Path) -> str:
    """Guarantee an executable literally named `ffmpeg`/`ffmpeg.exe` is on PATH for audio-separator/pydub."""
    existing = shutil.which("ffmpeg")
    if existing:
        return existing
    ff = Path(ff_path).resolve()
    target_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    if ff.name.lower() == target_name:
        os.environ["PATH"] = str(ff.parent) + os.pathsep + os.environ.get("PATH", "")
        return str(ff)
    bin_dir = shim_root / "_bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / target_name
    if not shim.exists():
        shutil.copy2(ff, shim)
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    return str(shim)


def _python_has(py_exe: str, mod: str) -> bool:
    if Path(py_exe).resolve() == Path(sys.executable).resolve():
        return importlib.util.find_spec(mod) is not None
    try:
        r = subprocess.run(
            [py_exe, "-c", f"import importlib.util, sys; sys.exit(0 if importlib.util.find_spec({mod!r}) else 1)"],
            capture_output=True,
            timeout=15,
        )
        return r.returncode == 0
    except Exception:
        return False


def _resolve_stem_python(explicit: str) -> str:
    for cand in (explicit.strip(), os.environ.get("CHIAKI_STEM_PYTHON", "").strip()):
        if cand and os.path.exists(cand):
            return str(Path(cand).resolve())
    return sys.executable


def _decode_mono_f32(ff: str, audio_path: Path, sr: int = 24000) -> np.ndarray:
    raw = subprocess.run(
        [ff, "-v", "error", "-i", str(audio_path), "-map", "0:a:0", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        capture_output=True,
        check=True,
    ).stdout
    if not raw:
        sys.exit(f"Could not decode audio: {audio_path}")
    return np.frombuffer(raw, dtype=np.float32)


def _worker_separate_audio_separator(
    audio_path: Path, out_dir: Path, model_dir: Path, model_name: str, ff_path: str
) -> tuple[Path, Path]:
    _ensure_ffmpeg_on_path(ff_path, model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "_raw_stems"
    raw_dir.mkdir(parents=True, exist_ok=True)

    from audio_separator.separator import Separator

    sep = Separator(
        model_file_dir=str(model_dir),
        output_dir=str(raw_dir),
        output_format="WAV",
        log_level=20,
    )
    sep.load_model(model_name)
    produced = sep.separate(str(audio_path))
    paths = [Path(p) if os.path.isabs(p) else (raw_dir / p) for p in produced]

    voc_src = None
    ins_src = None
    for p in paths:
        low = p.name.lower()
        if "(vocals)" in low or "(vocal)" in low:
            voc_src = p
        elif any(tok in low for tok in ("(instrumental)", "(other)", "(no_vocals)", "(no vocals)", "(accompaniment)", "(backing)")):
            ins_src = p
    if (voc_src is None or ins_src is None) and len(paths) == 2:
        # Fallback if a model uses non-parenthesized suffixes (strip model_name first so 'vocals_mel_band_roformer' doesn't false-match)
        m_stem = Path(model_name).stem.lower()
        for p in paths:
            cleaned = p.name.lower().replace(m_stem, "")
            if voc_src is None and "vocal" in cleaned and "no_vocal" not in cleaned and "no vocal" not in cleaned:
                voc_src = p
            elif ins_src is None:
                ins_src = p
    if voc_src is None or ins_src is None:
        sys.exit(f"audio-separator output could not be classified into vocals/instrumental: {[p.name for p in paths]}")

    voc_dst = out_dir / "vocals.wav"
    ins_dst = out_dir / "instrumental.wav"
    shutil.move(str(voc_src), str(voc_dst))
    shutil.move(str(ins_src), str(ins_dst))
    try:
        shutil.rmtree(raw_dir, ignore_errors=True)
    except Exception:
        pass
    return voc_dst, ins_dst


def _separate_demucs(audio_path: Path, out_dir: Path, py_exe: str, model_name: str, ff_path: str) -> tuple[Path, Path]:
    _ensure_ffmpeg_on_path(ff_path, out_dir)
    raw_dir = out_dir / "_demucs_tmp"
    raw_dir.mkdir(parents=True, exist_ok=True)
    dm_model = model_name if model_name.startswith("htdemucs") or model_name.startswith("mdx") else "htdemucs"
    cmd = [py_exe, "-m", "demucs", "--two-stems=vocals", "-n", dm_model, "-o", str(raw_dir), str(audio_path)]
    subprocess.run(cmd, check=True)
    stem_folder = raw_dir / dm_model / audio_path.stem
    voc_src = stem_folder / "vocals.wav"
    ins_src = stem_folder / "no_vocals.wav"
    if not voc_src.exists() or not ins_src.exists():
        sys.exit(f"demucs did not produce expected vocals.wav / no_vocals.wav under {stem_folder}")
    voc_dst = out_dir / "vocals.wav"
    ins_dst = out_dir / "instrumental.wav"
    shutil.move(str(voc_src), str(voc_dst))
    shutil.move(str(ins_src), str(ins_dst))
    shutil.rmtree(raw_dir, ignore_errors=True)
    return voc_dst, ins_dst


def _separate_dsp_fallback(audio_path: Path, out_dir: Path, ff_path: str) -> tuple[Path, Path]:
    """Emergency zero-AI fallback: Mid-band center-weighted vocal proxy + low/side-weighted drum/backing proxy."""
    voc_dst = out_dir / "vocals.wav"
    ins_dst = out_dir / "instrumental.wav"
    # Center-weighted vocal formant pass (180-4500 Hz)
    subprocess.run(
        [
            ff_path, "-v", "error", "-y", "-i", str(audio_path),
            "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=180,lowpass=f=4500",
            "-ar", "44100", "-c:a", "pcm_s16le", str(voc_dst),
        ],
        check=True,
    )
    # Full low-end + stereo sides for percussion / backing proxy
    subprocess.run(
        [
            ff_path, "-v", "error", "-y", "-i", str(audio_path),
            "-filter_complex",
            "[0:a]lowpass=f=220[lo];[0:a]highpass=f=220,stereotools=mlev=0.15:slev=1.2[hi];[lo][hi]amix=inputs=2:normalize=0",
            "-ar", "44100", "-c:a", "pcm_s16le", str(ins_dst),
        ],
        check=True,
    )
    return voc_dst, ins_dst


def _worker_whisper(
    voc_wav: Path,
    out_json: Path,
    whisper_dir: Path,
    whisper_model: str,
    lang: str,
    lyrics_text: str,
    fps: float,
    ff_path: str,
) -> None:
    from faster_whisper import WhisperModel

    device = "cpu"
    compute_type = "int8"
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            device = "cuda"
            compute_type = "float16"
    except Exception:
        pass

    whisper_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    # Decode directly via FFmpeg to 16 kHz mono float32 (bypasses PyAV 24-bit/Windows bugs)
    audio_16k = _decode_mono_f32(ff_path, voc_wav, sr=16000)
    kwargs: dict = {
        "word_timestamps": True,
        "vad_filter": False,
        "beam_size": 5,
        "condition_on_previous_text": True,
    }
    if lang and lang != "auto":
        kwargs["language"] = lang
    if lyrics_text.strip():
        kwargs["initial_prompt"] = lyrics_text.strip()

    def _run_transcribe(dev: str, ctype: str):
        print(f"[stem_sync] Loading faster-whisper '{whisper_model}' ({dev}/{ctype})...", flush=True)
        model = WhisperModel(whisper_model, device=dev, compute_type=ctype, download_root=str(whisper_dir))
        segs_iter, inf = model.transcribe(audio_16k, **kwargs)
        return list(segs_iter), inf

    try:
        segments, info = _run_transcribe(device, compute_type)
    except Exception as e:
        if device == "cuda":
            print(f"[stem_sync] CUDA whisper failed ({e}); falling back to int8 CPU...", flush=True)
            segments, info = _run_transcribe("cpu", "int8")
        else:
            raise
    rows = []
    for seg in segments:
        words = []
        for w in (seg.words or []):
            words.append({
                "word": w.word.strip(),
                "start_s": round(float(w.start), 3),
                "end_s": round(float(w.end), 3),
                "start_f": int(round(float(w.start) * fps)),
                "end_f": int(round(float(w.end) * fps)),
                "prob": round(float(w.probability), 3),
            })
        rows.append({
            "start_f": int(round(float(seg.start) * fps)),
            "end_f": int(round(float(seg.end) * fps)),
            "start_s": round(float(seg.start), 3),
            "end_s": round(float(seg.end), 3),
            "text": seg.text.strip(),
            "words": words,
        })
    payload = {
        "fps": fps,
        "language": getattr(info, "language", lang),
        "language_probability": round(float(getattr(info, "language_probability", 0.0)), 3),
        "whisper_model": whisper_model,
        "segments": rows,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def analyze_instrumental_kicks(ins_wav: Path, ff_path: str, fps: float, out_json: Path) -> dict:
    """Measure clean <130 Hz kick drum transients & per-section local BPM drift on isolated instrumental stem."""
    sr = 24000
    y = _decode_mono_f32(ff_path, ins_wav, sr=sr)
    dur_s = len(y) / sr
    n_f = int(math.floor(dur_s * fps))
    hop = sr / fps
    win = np.hanning(1024).astype(np.float32)
    freqs = np.fft.rfftfreq(1024, 1.0 / sr)
    low_m = (freqs >= 35.0) & (freqs <= 130.0)

    low_e = np.zeros(n_f, dtype=np.float32)
    for i in range(n_f):
        c = int(round((i + 0.5) * hop))
        a = max(0, c - 512)
        seg = np.zeros(1024, dtype=np.float32)
        ch = y[a : min(len(y), a + 1024)]
        seg[: len(ch)] = ch
        low_e[i] = float(np.sqrt(np.mean(np.abs(np.fft.rfft(seg * win))[low_m] ** 2)))

    low_flux = np.maximum(0.0, np.diff(low_e, prepend=low_e[0]))
    thr = float(np.percentile(low_flux, 88)) if n_f > 10 else 0.0
    min_gap = max(6, int(round(fps * 0.28)))  # <= ~214 BPM max kick density

    kicks: list[int] = []
    for i in range(2, n_f - 2):
        if low_flux[i] > thr and low_flux[i] >= low_flux[i - 2 : i + 3].max():
            if not kicks or (i - kicks[-1]) >= min_gap:
                kicks.append(i)

    # Estimate global beat spacing from inter-kick intervals in 75-185 BPM band
    lo_step = fps * 60.0 / 185.0
    hi_step = fps * 60.0 / 75.0
    diffs = [kicks[i + 1] - kicks[i] for i in range(len(kicks) - 1)]
    valid_diffs = [d for d in diffs if lo_step <= d <= hi_step]
    if valid_diffs:
        med_step = float(np.median(valid_diffs))
        inliers = [d for d in valid_diffs if abs(d - med_step) <= max(1.5, med_step * 0.10)]
        global_step = float(np.mean(inliers)) if inliers else med_step
        global_bpm = 60.0 * fps / global_step
    else:
        global_step = 0.0
        global_bpm = 0.0

    # Optimal global grid phase against all kicks
    global_phase = 0.0
    if global_step > 0 and kicks:
        best_err = 1e9
        for ph in np.linspace(0.0, global_step, 64, endpoint=False):
            errs = [abs(((k - ph + global_step / 2) % global_step) - global_step / 2) for k in kicks]
            m = float(np.median(errs))
            if m < best_err:
                best_err = m
                global_phase = float(ph)

    # Local 30-second windows to detect tempo drift (e.g. Chorus 2 vs Final Chorus)
    win_s = 30.0
    sections = []
    drift_warnings = []
    t = 0.0
    while t < dur_s - 4.0:
        t1 = min(dur_s, t + win_s)
        fa, fb = int(round(t * fps)), int(round(t1 * fps))
        ks = [k for k in kicks if fa <= k < fb]
        ds = [ks[i + 1] - ks[i] for i in range(len(ks) - 1) if lo_step <= (ks[i + 1] - ks[i]) <= hi_step]
        if len(ds) >= 4 and global_step > 0:
            in_ds = [d for d in ds if abs(d - global_step) <= max(2.0, global_step * 0.14)]
            local_step = float(np.mean(in_ds)) if len(in_ds) >= 3 else float(np.median(ds))
            local_bpm = 60.0 * fps / local_step
            signed_errs = [((k - global_phase + global_step / 2) % global_step) - global_step / 2 for k in ks]
            med_err = float(np.median(signed_errs))
            sec = {
                "range_s": [round(t, 2), round(t1, 2)],
                "range_f": [fa, fb],
                "kick_count": len(ks),
                "local_bpm": round(local_bpm, 2),
                "mean_step_f": round(local_step, 3),
                "vs_global_median_err_f": round(med_err, 2),
            }
            sections.append(sec)
            if abs(local_bpm - global_bpm) >= 0.45 or abs(med_err) >= 1.5:
                drift_warnings.append(
                    f"f{fa}-f{fb} ({t:.0f}-{t1:.0f}s): local {local_bpm:.2f} BPM vs global {global_bpm:.2f} BPM (median err {med_err:+.1f} f)"
                )
        t += win_s

    payload = {
        "source": str(ins_wav),
        "fps": fps,
        "duration_s": round(dur_s, 3),
        "total_frames": n_f,
        "global_bpm_est": round(global_bpm, 2),
        "global_step_f": round(global_step, 4),
        "global_phase_f": round(global_phase, 3),
        "kick_count": len(kicks),
        "kicks": kicks,
        "sections": sections,
        "drift_warnings": drift_warnings,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def analyze_dry_vocals(
    voc_wav: Path, ff_path: str, fps: float, out_dir: Path, chunk_s: float = 10.0, render_charts: bool = True
) -> tuple[dict, np.ndarray, list[int]]:
    """Compute per-frame dB + 180-4500 Hz syllable flux on isolated dry vocals; slice WAVs & charts."""
    sr = 24000
    y = _decode_mono_f32(ff_path, voc_wav, sr=sr)
    dur_s = len(y) / sr
    n_f = int(math.floor(dur_s * fps))
    hop = sr / fps

    win = np.hanning(1024).astype(np.float32)
    freqs = np.fft.rfftfreq(1024, 1.0 / sr)
    v_mask = (freqs >= 180.0) & (freqs <= 4500.0)

    rms_db = np.zeros(n_f, dtype=np.float32)
    spec = np.zeros((n_f, int(v_mask.sum())), dtype=np.float32)
    for i in range(n_f):
        c = int(round((i + 0.5) * hop))
        a = max(0, c - 512)
        seg = np.zeros(1024, dtype=np.float32)
        ch = y[a : min(len(y), a + 1024)]
        seg[: len(ch)] = ch
        r = float(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        rms_db[i] = 20.0 * math.log10(r)
        mag = np.abs(np.fft.rfft(seg * win))[v_mask]
        spec[i] = np.log1p(mag * 40.0)

    flux = np.zeros(n_f, dtype=np.float32)
    if n_f > 1:
        flux[1:] = np.maximum(0.0, spec[1:] - spec[:-1]).mean(axis=1)
    flux_norm = flux / (float(np.percentile(flux, 98)) + 1e-6)

    active = rms_db > -36.0
    strong_frames = int(np.sum(rms_db > -34.0))
    vocal_active_s = strong_frames / fps if fps > 0 else 0.0
    vocal_active_ratio = strong_frames / max(1, n_f)
    vocal_peak_db = float(rms_db.max()) if n_f > 0 else -120.0
    gap_merge = max(4, int(round(fps * 0.17)))
    min_pk_gap = max(3, int(round(fps * 0.12)))

    phrases = []
    all_onsets: list[int] = []
    i = 0
    while i < n_f:
        if active[i]:
            j = i
            while j < n_f:
                if active[j]:
                    j += 1
                else:
                    k = j
                    while k < min(n_f, j + gap_merge) and not active[k]:
                        k += 1
                    if k < n_f and active[k]:
                        j = k
                    else:
                        break
            if j - i >= 3:
                peaks = []
                for p in range(max(1, i), min(n_f - 1, j)):
                    rms_jump = float(rms_db[p] - rms_db[max(0, p - 2)])
                    is_pk = (flux_norm[p] >= flux_norm[p - 1] and flux_norm[p] >= flux_norm[p + 1] and flux_norm[p] > 0.22)
                    is_attack = (rms_jump > 6.5 and rms_db[p] > -30.0 and rms_db[p] >= rms_db[p - 1])
                    if is_pk or is_attack:
                        if not peaks or (p - peaks[-1]) >= min_pk_gap:
                            peaks.append(p)
                phrases.append({
                    "id": f"P{len(phrases) + 1:02d}",
                    "start_f": i,
                    "end_f": j,
                    "start_s": round(i / fps, 3),
                    "end_s": round(j / fps, 3),
                    "peak_db": round(float(rms_db[i:j].max()), 1),
                    "syllable_onsets": peaks,
                })
                all_onsets.extend(peaks)
            i = j
        else:
            i += 1

    has_vocals = (vocal_peak_db > -30.0) and (len(phrases) >= 1) and ((vocal_active_s >= 1.2) or (vocal_active_ratio >= 0.03))
    track_type = "vocal_song" if has_vocals else "instrumental"

    slices = []
    if has_vocals:
        charts_dir = out_dir / "vocal_charts"
        charts_dir.mkdir(parents=True, exist_ok=True)
        chunk_f = max(int(round(chunk_s * fps)), int(round(fps * 3)))
        smax = max(1.0, float(np.percentile(spec, 99.5))) if n_f > 0 else 1.0

        for c_idx, a in enumerate(range(0, n_f, chunk_f)):
            b = min(n_f, a + chunk_f)
            wav_p = charts_dir / f"dry_{c_idx:02d}_f{a:04d}_f{b:04d}.wav"
            subprocess.run(
                [
                    ff_path, "-v", "error", "-y",
                    "-ss", f"{a / fps:.4f}", "-t", f"{(b - a) / fps:.4f}",
                    "-i", str(voc_wav), "-ac", "1", "-ar", "24000", "-sample_fmt", "s16", str(wav_p),
                ],
                check=True,
            )
            entry = {"wav": str(wav_p), "start_f": a, "end_f": b}

            if render_charts:
                from PIL import Image, ImageDraw
                px_per_f = 6
                W = (b - a) * px_per_f
                H_spec, H_env, H_hdr = 200, 110, 40
                H = H_hdr + H_spec + H_env
                sub = np.clip(spec[a:b] / smax, 0.0, 1.0)
                # Vectorized spectrogram RGB rendering (fast pure numpy)
                spec_t = sub[:, ::-1].T  # (freq_bins, frames)
                r = np.clip(spec_t * 320.0, 0, 255).astype(np.uint8)
                g = np.clip(np.maximum(0.0, spec_t - 0.25) * 280.0, 0, 255).astype(np.uint8)
                bl = np.clip(spec_t * 160.0 + np.where(spec_t > 0.1, 60.0, 0.0), 0, 255).astype(np.uint8)
                rgb = np.stack([r, g, bl], axis=-1)
                spec_im = Image.fromarray(rgb, mode="RGB").resize((W, H_spec), Image.BILINEAR)

                im = Image.new("RGB", (W, H), (14, 15, 20))
                im.paste(spec_im, (0, H_hdr))
                dr = ImageDraw.Draw(im)

                y0_env = H_hdr + H_spec
                for idx_i in range(b - a):
                    x0 = idx_i * px_per_f
                    db = max(-55.0, min(0.0, float(rms_db[a + idx_i])))
                    h_db = int(((db + 55.0) / 55.0) * (H_env - 12))
                    col_bar = (60, 180, 255) if rms_db[a + idx_i] > -36.0 else (45, 50, 62)
                    dr.rectangle([x0, y0_env + H_env - h_db, x0 + px_per_f - 2, y0_env + H_env], fill=col_bar)
                    fl = min(1.0, float(flux_norm[a + idx_i]))
                    if fl > 0.22 and rms_db[a + idx_i] > -36.0:
                        h_fl = int(fl * (H_env - 16))
                        dr.rectangle([x0 + 1, y0_env + H_env - h_fl, x0 + px_per_f - 2, y0_env + H_env], fill=(255, 60, 100))

                for f_abs in range(a - (a % 5), b + 1, 5):
                    if f_abs < a:
                        continue
                    xx = (f_abs - a) * px_per_f
                    major = (f_abs % 10 == 0)
                    dr.line([(xx, H_hdr), (xx, H)], fill=(120, 125, 140) if major else (45, 48, 58))
                    if major:
                        dr.text((xx + 2, 4), f"f{f_abs}", fill=(255, 240, 100))
                        dr.text((xx + 2, 20), f"{f_abs / fps:.1f}s", fill=(160, 180, 220))

                for p in phrases:
                    for pk in p["syllable_onsets"]:
                        if a <= pk < b:
                            xx = (pk - a) * px_per_f
                            dr.line([(xx, H_hdr), (xx, H)], fill=(255, 80, 120), width=1)
                    if a <= p["start_f"] < b:
                        xx = (p["start_f"] - a) * px_per_f
                        dr.line([(xx, H_hdr), (xx, H)], fill=(80, 255, 130), width=2)

                png_p = charts_dir / f"dry_{c_idx:02d}_f{a:04d}_f{b:04d}.png"
                im.save(png_p)
                entry["png"] = str(png_p)
            slices.append(entry)

    payload = {
        "source": str(voc_wav),
        "fps": fps,
        "duration_s": round(dur_s, 3),
        "total_frames": n_f,
        "has_vocals": has_vocals,
        "track_type": track_type,
        "vocal_active_s": round(vocal_active_s, 2),
        "vocal_active_ratio": round(vocal_active_ratio, 4),
        "vocal_peak_db": round(vocal_peak_db, 1),
        "phrase_count": len(phrases),
        "syllable_onset_count": len(all_onsets),
        "phrases": phrases,
        "slices": slices,
    }
    (out_dir / "vocal_phrases.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload, rms_db, all_onsets


def snap_whisper_to_dry_onsets(whisper_json: Path, rms_db: np.ndarray, onsets: list[int], fps: float) -> dict:
    """Cross-check Whisper timestamps against dry-vocal RMS & flux peaks to flag leading-breath padding."""
    data = json.loads(whisper_json.read_text(encoding="utf-8"))
    n_f = len(rms_db)
    onset_arr = np.array(onsets, dtype=np.int32) if onsets else np.array([], dtype=np.int32)

    breath_flags = 0
    for seg in data.get("segments", []):
        sf = int(seg["start_f"])
        if 0 <= sf < n_f and float(rms_db[sf]) < -40.0:
            # Find first audible frame (>= -34 dB) after Whisper's breath-padded segment start
            k = sf
            while k < min(n_f, sf + int(round(fps * 1.0))) and rms_db[k] < -34.0:
                k += 1
            if k < n_f and rms_db[k] >= -34.0:
                seg["audible_start_f"] = int(k)
                seg["leading_silence_f"] = int(k - sf)
                breath_flags += 1
        for w in seg.get("words", []):
            wf = int(w["start_f"])
            if len(onset_arr) > 0:
                idx = int(np.argmin(np.abs(onset_arr - wf)))
                near = int(onset_arr[idx])
                if abs(near - wf) <= 5:
                    w["snapped_start_f"] = near
                    w["snap_delta_f"] = near - wf
    data["leading_breath_segments_flagged"] = breath_flags
    whisper_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-1 vocal/instrumental stem separation & dual-stem timing")
    ap.add_argument("audio", nargs="?", default="", help="Input song/audio file (wav/mp3/flac/mp4)")
    ap.add_argument("--out", required=True, help="Output directory for stems & timing reports")
    ap.add_argument("--fps", type=float, default=30.0, help="Video frame rate (default 30)")
    ap.add_argument("--backend", choices=("auto", "audio-separator", "demucs", "dsp"), default="auto")
    ap.add_argument("--model", default="", help=f"Separator model filename (default: {DEFAULT_MODEL}; with --fast: {FAST_MODEL})")
    ap.add_argument("--fast", action="store_true", help=f"Use lightweight 60 MB ONNX model ({FAST_MODEL}) instead of Mel-Band RoFormer")
    ap.add_argument("--model-dir", default="", help="Cache directory for separator & whisper weights (default: CHIAKI_STEM_MODELS or ~/.chiaki-studio/stem-models)")
    ap.add_argument("--stem-python", default="", help="Optional alternate Python executable that has audio-separator/demucs/faster-whisper installed")
    ap.add_argument("--vocals", default="", help="Use an already-separated dry vocal WAV (skip separation)")
    ap.add_argument("--instrumental", default="", help="Use an already-separated instrumental WAV (skip separation)")
    ap.add_argument("--force", action="store_true", help="Re-run stem separation even if vocals.wav & instrumental.wav already exist")
    ap.add_argument("--whisper", action="store_true", help="Run faster-whisper word-level alignment on isolated dry vocals")
    ap.add_argument("--whisper-model", default="medium", help="faster-whisper model size (default: medium)")
    ap.add_argument("--whisper-dir", default="", help="Optional cache directory for faster-whisper weights (default: <model-dir>/whisper)")
    ap.add_argument("--ffmpeg", default="", help="Optional explicit ffmpeg executable path")
    ap.add_argument("--lang", default="auto", help="Language code for Whisper (e.g. ja, zh, en, ko, auto)")
    ap.add_argument("--lyrics", default="", help="Optional plain-text lyrics file used as Whisper initial_prompt")
    ap.add_argument("--chunk", type=float, default=10.0, help="Dry vocal slice window in seconds (default 10.0)")
    ap.add_argument("--no-charts", action="store_true", help="Skip dry-vocal PNG charts (still writes dry_*.wav slices)")
    ap.add_argument("--fallback-dsp", action="store_true", help="Allow DSP proxy fallback if neither audio-separator nor demucs is installed")
    # Internal worker hooks for cross-venv execution
    ap.add_argument("--_worker-separate", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--_worker-whisper", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    model_dir = Path(args.model_dir).expanduser().resolve() if args.model_dir else _default_model_dir()
    if args.whisper_dir:
        whisper_dir = Path(args.whisper_dir).expanduser().resolve()
    elif os.environ.get("CHIAKI_WHISPER_MODELS", "").strip():
        whisper_dir = Path(os.environ["CHIAKI_WHISPER_MODELS"]).expanduser().resolve()
    elif (model_dir.parent / "whisper_models").exists():
        whisper_dir = (model_dir.parent / "whisper_models").resolve()
    else:
        whisper_dir = model_dir / "whisper"
    ff = _find_ffmpeg(args.ffmpeg)
    worker_env = {**os.environ, "CHIAKI_FFMPEG": ff}

    if args._worker_separate:
        model_name = args.model or (FAST_MODEL if args.fast else DEFAULT_MODEL)
        _worker_separate_audio_separator(Path(args.audio).resolve(), out_dir, model_dir, model_name, ff)
        return 0

    if args._worker_whisper:
        lyrics_text = Path(args.lyrics).read_text(encoding="utf-8", errors="replace") if args.lyrics and os.path.exists(args.lyrics) else ""
        _worker_whisper(Path(args.vocals).resolve(), out_dir / "vocal_words.json", whisper_dir, args.whisper_model, args.lang, lyrics_text, args.fps, ff)
        return 0

    stem_py = _resolve_stem_python(args.stem_python)
    voc_wav = Path(args.vocals).expanduser().resolve() if args.vocals else (out_dir / "vocals.wav")
    ins_wav = Path(args.instrumental).expanduser().resolve() if args.instrumental else (out_dir / "instrumental.wav")

    backend_used = "preexisting"
    model_name = args.model or (FAST_MODEL if args.fast else DEFAULT_MODEL)

    if args.force or not (voc_wav.exists() and ins_wav.exists()):
        if not args.audio or not os.path.exists(args.audio):
            sys.exit(f"Input audio not found: {args.audio}")
        audio_p = Path(args.audio).expanduser().resolve()

        chosen = args.backend
        if chosen == "auto":
            if _python_has(stem_py, "audio_separator"):
                chosen = "audio-separator"
            elif _python_has(stem_py, "demucs"):
                chosen = "demucs"
            elif args.fallback_dsp:
                chosen = "dsp"
            else:
                sys.exit(
                    "No AI stem separator installed (`audio-separator` or `demucs` not found).\n"
                    "Install with `python -X utf8 scripts/setup_env.py --profile 2d --venv <dir>` (includes audio-separator + faster-whisper),\n"
                    "or point `CHIAKI_STEM_PYTHON` to an existing venv, or pass `--fallback-dsp` for a rough non-AI band split."
                )

        print(f"[stem_sync] Separating {audio_p.name} via {chosen} (model={model_name}, python={stem_py})...", flush=True)
        if chosen == "audio-separator":
            if Path(stem_py).resolve() == Path(sys.executable).resolve():
                voc_wav, ins_wav = _worker_separate_audio_separator(audio_p, out_dir, model_dir, model_name, ff)
            else:
                cmd = [
                    stem_py, "-X", "utf8", str(Path(__file__).resolve()),
                    str(audio_p), "--out", str(out_dir), "--model-dir", str(model_dir),
                    "--model", model_name, "--ffmpeg", ff, "--_worker-separate",
                ]
                subprocess.run(cmd, check=True, env=worker_env)
                voc_wav, ins_wav = out_dir / "vocals.wav", out_dir / "instrumental.wav"
            backend_used = f"audio-separator:{model_name}"
        elif chosen == "demucs":
            voc_wav, ins_wav = _separate_demucs(audio_p, out_dir, stem_py, model_name, ff)
            backend_used = f"demucs:{model_name}"
        else:
            voc_wav, ins_wav = _separate_dsp_fallback(audio_p, out_dir, ff)
            backend_used = "dsp-fallback (NON-AI PROXY)"

    print(f"[stem_sync] Analyzing pure instrumental kicks -> {out_dir / 'kick_grid.json'}", flush=True)
    kick_report = analyze_instrumental_kicks(ins_wav, ff, args.fps, out_dir / "kick_grid.json")

    print(f"[stem_sync] Analyzing isolated dry vocals -> {out_dir / 'vocal_phrases.json'}", flush=True)
    vocal_report, rms_db, all_onsets = analyze_dry_vocals(
        voc_wav, ff, args.fps, out_dir, chunk_s=args.chunk, render_charts=not args.no_charts
    )

    has_vocals = bool(vocal_report.get("has_vocals", False))
    whisper_report = None
    if args.whisper and not has_vocals:
        print(
            f"[stem_sync] Auto-detected pure instrumental track "
            f"(vocal_active={vocal_report['vocal_active_s']:.2f}s / {vocal_report['vocal_active_ratio']*100:.1f}%, peak={vocal_report['vocal_peak_db']:.1f} dB); "
            f"skipping dry-vocal charts & Whisper.",
            flush=True,
        )
    elif args.whisper:
        if not _python_has(stem_py, "faster_whisper"):
            print("[stem_sync] WARN: --whisper requested but `faster-whisper` is not installed; skipping word alignment.", file=sys.stderr)
        else:
            w_json = out_dir / "vocal_words.json"
            if Path(stem_py).resolve() == Path(sys.executable).resolve():
                lyrics_text = Path(args.lyrics).read_text(encoding="utf-8", errors="replace") if args.lyrics and os.path.exists(args.lyrics) else ""
                _worker_whisper(voc_wav, w_json, whisper_dir, args.whisper_model, args.lang, lyrics_text, args.fps, ff)
            else:
                cmd = [
                    stem_py, "-X", "utf8", str(Path(__file__).resolve()),
                    "--out", str(out_dir), "--vocals", str(voc_wav), "--fps", str(args.fps),
                    "--model-dir", str(model_dir), "--whisper-dir", str(whisper_dir),
                    "--whisper-model", args.whisper_model, "--lang", args.lang,
                    "--ffmpeg", ff, "--_worker-whisper",
                ]
                if args.lyrics:
                    cmd += ["--lyrics", str(Path(args.lyrics).expanduser().resolve())]
                subprocess.run(cmd, check=True, env=worker_env)
            whisper_report = snap_whisper_to_dry_onsets(w_json, rms_db, all_onsets, args.fps)

    summary = {
        "backend": backend_used,
        "fps": args.fps,
        "has_vocals": has_vocals,
        "track_type": vocal_report["track_type"],
        "vocal_active_s": vocal_report["vocal_active_s"],
        "vocal_active_ratio": vocal_report["vocal_active_ratio"],
        "vocals_wav": str(voc_wav),
        "instrumental_wav": str(ins_wav),
        "kick_grid_json": str(out_dir / "kick_grid.json"),
        "vocal_phrases_json": str(out_dir / "vocal_phrases.json"),
        "vocal_words_json": str(out_dir / "vocal_words.json") if whisper_report else "",
        "global_bpm_est": kick_report["global_bpm_est"],
        "kick_count": kick_report["kick_count"],
        "drift_warnings": kick_report["drift_warnings"],
        "phrase_count": vocal_report["phrase_count"],
        "syllable_onset_count": vocal_report["syllable_onset_count"],
    }
    (out_dir / "stem_sync.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Compact human/agent summary markdown
    track_badge = (
        f"`vocal_song` (has_vocals=true · active `{vocal_report['vocal_active_s']:.1f}s` / `{vocal_report['vocal_active_ratio']*100:.1f}%`)"
        if has_vocals
        else f"`instrumental` (has_vocals=false · active `{vocal_report['vocal_active_s']:.2f}s` / `{vocal_report['vocal_active_ratio']*100:.1f}%` — pure instrumental auto-detected, vocal charts/Whisper skipped)"
    )
    md_lines = [
        "# Stage-1 Dual-Stem Audio Sync Summary",
        "",
        f"- **Track Type**: {track_badge}",
        f"- **Backend**: `{backend_used}` · **FPS**: `{args.fps:g}`",
        f"- **Pure Instrumental (for beats/kicks)**: `{ins_wav}`",
        f"- **Pure Dry Vocals (for lyrics/ear/spec)**: `{voc_wav}`",
        f"- **Kick Grid**: `~{kick_report['global_bpm_est']:.2f} BPM` (`{kick_report['kick_count']}` kicks detected, step `{kick_report['global_step_f']:.3f} f`)",
        f"- **Dry Vocal Phrases**: `{vocal_report['phrase_count']}` phrases · `{vocal_report['syllable_onset_count']}` syllable onset peaks",
    ]
    if kick_report["drift_warnings"]:
        md_lines.append("")
        md_lines.append("## Local Tempo Drift Warnings (DO NOT use one flat BPM formula across the whole song!)")
        for w in kick_report["drift_warnings"]:
            md_lines.append(f"- {w}")
    if whisper_report:
        md_lines.append(f"- **Whisper Word Alignment**: `{len(whisper_report.get('segments', []))} segments` -> `vocal_words.json` (leading-breath segments flagged: `{whisper_report.get('leading_breath_segments_flagged', 0)}`)")
    beat_target = ins_wav if has_vocals else (Path(args.audio).resolve() if args.audio and os.path.exists(args.audio) else ins_wav)
    md_lines += [
        "",
        "## Recommended Next Commands",
        f"- Beat grid: `python -X utf8 <sk>/scripts/beats.py \"{beat_target}\" --fps {args.fps:g} --json work/beats.json`",
        f"- Exact drop/hit onsets: `python -X utf8 <sk>/scripts/onsets.py \"{beat_target}\" <f0-f1> --fps {args.fps:g}`",
    ]
    if has_vocals:
        md_lines.append(f"- Tight lyric micro-WAVs / dry specs (pure vocals): `python -X utf8 <sk>/scripts/vocal_spec.py \"{voc_wav}\" --out work/vocal --fps {args.fps:g} [--wav-only]`")
    (out_dir / "stem_sync_summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("\n".join(md_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
