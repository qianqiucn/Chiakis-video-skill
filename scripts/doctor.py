"""doctor.py — one-command environment & bundled-asset check for Chiaki's-video-skill.

Usage:
  python -X utf8 scripts/doctor.py          # human-readable report
  python -X utf8 scripts/doctor.py --json   # structured JSON report for agent setup wizards
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
req_missing: list[str] = []
opt_missing: list[str] = []
checks: list[dict[str, str]] = []
JSON_MODE = False


def _emit(status: str, label: str, detail: str):
    checks.append({"status": status, "label": label, "detail": detail})
    if not JSON_MODE:
        print(f"  [{status:4s}] {label:26s} {detail}")


def ok(label: str, detail: str):
    _emit("OK", label, detail)


def warn(label: str, detail: str):
    _emit("WARN", label, detail)


def fail(label: str, detail: str):
    _emit("FAIL", label, detail)


def check_python():
    v = sys.version_info
    s = f"Python {v.major}.{v.minor}.{v.micro} ({sys.executable})"
    if v >= (3, 10):
        ok("Python >= 3.10", s)
    else:
        fail("Python >= 3.10", f"{s} — upgrade to Python 3.10+")
        req_missing.append("Python >= 3.10")


def check_node():
    node = shutil.which("node")
    if not node:
        fail("Node.js >= 22", "not found on PATH (install from https://nodejs.org/)")
        req_missing.append("Node.js >= 22")
        return
    r = subprocess.run([node, "-v"], capture_output=True, text=True)
    ver = (r.stdout or "").strip()
    m = re.match(r"v(\d+)\.", ver)
    major = int(m.group(1)) if m else 0
    if major >= 22:
        ok("Node.js >= 22", f"{ver} ({node})")
    else:
        fail("Node.js >= 22", f"found {ver}, need >= v22 (built-in WebSocket for headless Chrome CDP)")
        req_missing.append("Node.js >= 22")


def check_chrome():
    for env in ("CHIAKI_CHROME", "CHROME_PATH"):
        p = os.environ.get(env)
        if p and os.path.exists(p):
            ok("Chrome / Edge", f"{p} (via {env})")
            return
    candidates = (
        [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        if sys.platform == "win32"
        else [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
        if sys.platform == "darwin"
        else ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"]
    )
    for p in candidates:
        if p and os.path.exists(p):
            ok("Chrome / Edge", p)
            return
    for b in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        w = shutil.which(b)
        if w:
            ok("Chrome / Edge", w)
            return
    fail("Chrome / Edge", "not detected — install Chrome/Chromium/Edge or set CHIAKI_CHROME")
    req_missing.append("Chrome / Chromium / Edge")


def check_ffmpeg():
    env = os.environ.get("CHIAKI_FFMPEG") or os.environ.get("FFMPEG_PATH")
    if env and os.path.exists(env):
        ok("FFmpeg", env)
        return
    w = shutil.which("ffmpeg")
    if w:
        ok("FFmpeg", w)
        return
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p):
            ok("FFmpeg", f"{p} (via imageio-ffmpeg)")
            return
    except Exception:
        pass
    fail("FFmpeg", "not found — install ffmpeg on PATH or `pip install imageio-ffmpeg`")
    req_missing.append("ffmpeg (or `pip install imageio-ffmpeg`)")


def check_blender():
    found = None
    env = os.environ.get("CHIAKI_BLENDER") or os.environ.get("BLENDER_PATH")
    if env and os.path.exists(env):
        found = env
    else:
        w = shutil.which("blender")
        if w:
            found = w
        else:
            cands = []
            if sys.platform == "win32":
                for base in [Path(r"C:\Program Files\Blender Foundation")]:
                    if base.exists():
                        cands += sorted(base.glob("Blender */blender.exe"), reverse=True)
            elif sys.platform == "darwin":
                cands.append(Path("/Applications/Blender.app/Contents/MacOS/Blender"))
            else:
                cands.append(Path("/usr/bin/blender"))
            for p in cands:
                if p.exists():
                    found = str(p)
                    break
    if found:
        ok("Blender (2.5D / 3D)", found)
    else:
        warn("Blender (2.5D / 3D)", "not found — optional, for depth_relief.py, projection/ & built sets (set CHIAKI_BLENDER or install Blender 4.2+/5.x)")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.25)
    try:
        s.connect(("127.0.0.1", 9876))
        ok("Blender MCP (live)", "listening on 127.0.0.1:9876 (interactive look-dev ready)")
    except Exception:
        warn("Blender MCP (live)", "not running on 127.0.0.1:9876 — optional; headless Blender CLI works without MCP (see README)")
    finally:
        s.close()


def check_py_pkgs():
    groups = [
        ("Fonts (fontTools/brotli/PIL/pathops)", ["fontTools", "brotli", "PIL", "pathops"]),
        ("Video/Beat (numpy/cv2)", ["numpy", "cv2"]),
        ("Audio (mgaudio deps)", ["scipy", "numba", "soundfile", "pedalboard"]),
    ]
    for label, mods in groups:
        miss = []
        for m in mods:
            try:
                importlib.import_module(m)
            except Exception:
                miss.append(m)
        if not miss:
            ok(label, "all installed")
        else:
            warn(label, f"missing: {', '.join(miss)}")
            opt_missing.extend(miss)
    dmiss = []
    for m in ("torch", "transformers"):
        try:
            importlib.import_module(m)
        except Exception:
            dmiss.append(m)
    if not dmiss:
        ok("Vision/Depth AI (optional)", "torch + transformers installed (vision/cutout.py & vision/depth.py ready)")
    else:
        warn("Vision/Depth AI (optional)", f"missing {', '.join(dmiss)} — optional, for vision/cutout.py & vision/depth.py (`pip install torch torchvision \"transformers<5\" timm einops kornia`)")


def check_bundled():
    cat = ROOT / "assets" / "fonts" / "catalog.json"
    if cat.exists():
        n = len(json.loads(cat.read_text(encoding="utf-8")).get("families", {}))
        ok("Bundled Fonts", f"{n} open-source families ready in assets/fonts/")
    else:
        warn("Bundled Fonts", "catalog.json missing (lite install? Run `python scripts/fonts.py get starter`)")
    gsap = ROOT / "assets" / "template" / "lib" / "gsap" / "gsap.min.js"
    ez = ROOT / "assets" / "template" / "lib" / "motion" / "ez.js"
    mg = ROOT / "assets" / "mgaudio" / "mgaudio" / "__init__.py"
    if gsap.exists() and ez.exists():
        ok("2D Motion + GSAP", "assets/template/lib/motion/ + GSAP 3.15.1 present")
    else:
        fail("2D Motion + GSAP", "missing template motion libraries")
        req_missing.append("assets/template/lib/motion")
    if mg.exists():
        ok("Bundled mgaudio", "assets/mgaudio/ present (pure-synth ready)")
    else:
        warn("Bundled mgaudio", "assets/mgaudio/ not found")


def main() -> int:
    global JSON_MODE
    ap = argparse.ArgumentParser(description="Environment & dependency doctor for Chiaki's-video-skill")
    ap.add_argument("--json", action="store_true", help="Output structured JSON for automated setup wizards")
    args = ap.parse_args()
    JSON_MODE = args.json

    if not JSON_MODE:
        print(f"=== Chiaki's-video-skill Doctor ({ROOT}) ===")
    check_python()
    check_node()
    check_chrome()
    check_ffmpeg()
    check_blender()
    check_py_pkgs()
    check_bundled()

    if JSON_MODE:
        payload = {
            "skill_root": str(ROOT),
            "platform": sys.platform,
            "python_executable": sys.executable,
            "env": {
                "CHIAKI_CHROME": os.environ.get("CHIAKI_CHROME", ""),
                "CHIAKI_FFMPEG": os.environ.get("CHIAKI_FFMPEG", ""),
                "CHIAKI_BLENDER": os.environ.get("CHIAKI_BLENDER", ""),
                "CHIAKI_ASSETS3D": os.environ.get("CHIAKI_ASSETS3D", ""),
                "CHIAKI_FONTS": os.environ.get("CHIAKI_FONTS", ""),
            },
            "checks": checks,
            "required_missing": req_missing,
            "python_packages_missing": opt_missing,
            "ready_core": not req_missing,
            "ready_all": not req_missing and not opt_missing,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not req_missing else 1

    print()
    if req_missing:
        print("REQUIRED MISSING:", "; ".join(req_missing))
    if opt_missing:
        print("PYTHON PACKAGES TO INSTALL:")
        print(f'  pip install -r "{ROOT / "requirements.txt"}"')
    if not req_missing and not opt_missing:
        print("ALL READY: your machine can run every 2D motion, font, audio, lint, and MP4 render workflow.")
        return 0
    if not req_missing:
        print("CORE READY (Node + Chrome + FFmpeg OK); install requirements.txt above to enable font subsetting, cadence analysis, and mgaudio.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
