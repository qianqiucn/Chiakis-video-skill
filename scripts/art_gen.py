"""art_gen.py — pluggable Art & Asset stage runner for Chiaki's-video-skill (Python stdlib only).

Supports four clean, vendor-neutral asset sources declared per shot in <project>/work/art_manifest.json:
  - user_files : copy verified client-provided images into web/assets/art/
  - custom_api : OpenAI-Images-compatible POST endpoint (CHIAKI_IMAGE_API_URL / CHIAKI_IMAGE_API_KEY / CHIAKI_IMAGE_MODEL)
  - codex      : OpenAI gpt-image-1 endpoint (OPENAI_API_KEY / CHIAKI_OPENAI_IMAGE_MODEL)
  - gemini     : Gemini multimodal image generation (GEMINI_API_KEY / CHIAKI_GEMINI_IMAGE_MODEL)
  - code_only  : procedural 2D / Blender shot (no bitmap needed)

Usage:
  python -X utf8 scripts/art_gen.py init <project>
  python -X utf8 scripts/art_gen.py check <project>
  python -X utf8 scripts/art_gen.py run <project> [--only <id>] [--dry] [--force]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

UA = "chiaki-video-artgen/1.0 (https://github.com/qianqiucn/Chiakis-video-skill)"

SAMPLE_MANIFEST = {
    "project": "demo_project",
    "defaults": {
        "provider": "user_files",
        "size": "1920x1080",
        "style_bible": "Consistent editorial colour arc, crisp silhouette clarity, zero embedded text or watermarks.",
    },
    "shots": [
        {
            "id": "act1_hero",
            "act": "act1",
            "provider": "user_files",
            "source": "",
            "out": "web/assets/art/act1_hero.png",
            "prompt": "Wide cinematic key visual with clean upper-left negative space for kinetic typography.",
            "needs_depth": False,
            "notes": "Set provider to user_files | gemini | codex | custom_api | code_only",
        }
    ],
}


def http_json(url: str, payload: dict, headers: dict, timeout: int = 180) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": UA, **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from None


def download_bytes(url: str, timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def gen_openai_compat(prompt: str, size: str, url: str, key: str, model: str) -> bytes:
    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
    res = http_json(url, payload, {"Authorization": f"Bearer {key}"})
    items = res.get("data") or []
    if not items:
        raise RuntimeError(f"No image data returned by {url}: {str(res)[:300]}")
    item = items[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        return download_bytes(item["url"])
    raise RuntimeError(f"Unsupported image response item keys: {list(item.keys())}")


def gen_gemini(prompt: str, key: str, model: str) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    res = http_json(url, payload, {"x-goog-api-key": key})
    for cand in res.get("candidates", []):
        for part in (cand.get("content") or {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise RuntimeError(f"Gemini returned no inline image part: {str(res)[:300]}")


def full_prompt(shot: dict, defaults: dict) -> str:
    bible = (defaults.get("style_bible") or "").strip()
    p = (shot.get("prompt") or "").strip()
    return f"{bible}\n\n{p}".strip() if bible and p else (p or bible)


def cmd_init(proj: Path) -> int:
    mp = proj / "work" / "art_manifest.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    if mp.exists():
        print(f"Already exists: {mp}")
        return 0
    data = json.loads(json.dumps(SAMPLE_MANIFEST))
    data["project"] = proj.name
    mp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Initialized starter manifest -> {mp}")
    return 0


def load_manifest(proj: Path) -> tuple[Path, dict]:
    mp = proj / "work" / "art_manifest.json"
    if not mp.exists():
        sys.exit(f"Missing {mp} — run `art_gen.py init <project>` or create it during Gate A.")
    return mp, json.loads(mp.read_text(encoding="utf-8"))


def cmd_check(proj: Path) -> int:
    mp, data = load_manifest(proj)
    defaults = data.get("defaults") or {}
    shots = data.get("shots") or []
    missing = 0
    for s in shots:
        sid = s.get("id", "?")
        prov = s.get("provider") or defaults.get("provider") or "user_files"
        if prov == "code_only":
            print(f"  [CODE] {sid:24s} provider=code_only (procedural)")
            continue
        out_rel = s.get("out") or f"web/assets/art/{sid}.png"
        out_p = proj / out_rel
        if out_p.exists() and out_p.stat().st_size > 0:
            kb = out_p.stat().st_size / 1024
            print(f"  [OK]   {sid:24s} provider={prov:10s} {out_rel} ({kb:.1f} KB)")
        else:
            missing += 1
            print(f"  [MISS] {sid:24s} provider={prov:10s} expected {out_rel}")
    print(f"\nManifest {mp}: {len(shots)} shot(s), {missing} missing.")
    return 1 if missing else 0


def cmd_run(proj: Path, only: str, dry: bool, force: bool) -> int:
    _, data = load_manifest(proj)
    defaults = data.get("defaults") or {}
    shots = data.get("shots") or []
    if only:
        want = {x.strip() for x in only.split(",") if x.strip()}
        shots = [s for s in shots if s.get("id") in want]

    for s in shots:
        sid = s.get("id", "?")
        prov = s.get("provider") or defaults.get("provider") or "user_files"
        if prov == "code_only":
            print(f"[SKIP] {sid}: code_only")
            continue
        out_rel = s.get("out") or f"web/assets/art/{sid}.png"
        out_p = proj / out_rel
        if out_p.exists() and not force:
            print(f"[KEEP] {sid}: already exists -> {out_rel}")
            continue
        size = s.get("size") or defaults.get("size") or "1920x1080"
        prompt = full_prompt(s, defaults)
        if dry:
            print(f"[DRY]  {sid}: provider={prov} size={size} -> {out_rel}")
            continue

        out_p.parent.mkdir(parents=True, exist_ok=True)
        if prov == "user_files":
            src = s.get("source") or ""
            if not src or not Path(src).exists():
                sys.exit(f"[FAIL] {sid}: provider=user_files but source missing ({src!r}) and {out_rel} not on disk.")
            shutil.copy2(src, out_p)
            print(f"[COPY] {sid}: {src} -> {out_rel}")
        elif prov == "custom_api":
            url = os.environ.get("CHIAKI_IMAGE_API_URL", "").strip()
            key = os.environ.get("CHIAKI_IMAGE_API_KEY", "").strip()
            model = s.get("model") or os.environ.get("CHIAKI_IMAGE_MODEL", "").strip()
            if not (url and key and model):
                sys.exit(f"[FAIL] {sid}: custom_api requires CHIAKI_IMAGE_API_URL, CHIAKI_IMAGE_API_KEY, and CHIAKI_IMAGE_MODEL.")
            out_p.write_bytes(gen_openai_compat(prompt, size, url, key, model))
            print(f"[GEN]  {sid}: custom_api ({model}) -> {out_rel}")
        elif prov == "codex":
            key = os.environ.get("OPENAI_API_KEY", "").strip()
            model = s.get("model") or os.environ.get("CHIAKI_OPENAI_IMAGE_MODEL", "gpt-image-1")
            if not key:
                sys.exit(f"[FAIL] {sid}: codex provider requires OPENAI_API_KEY (or use Codex's built-in image tool and place output at {out_rel}).")
            out_p.write_bytes(gen_openai_compat(prompt, size, "https://api.openai.com/v1/images/generations", key, model))
            print(f"[GEN]  {sid}: codex ({model}) -> {out_rel}")
        elif prov == "gemini":
            key = os.environ.get("GEMINI_API_KEY", "").strip()
            model = s.get("model") or os.environ.get("CHIAKI_GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
            if not key:
                sys.exit(f"[FAIL] {sid}: gemini provider requires GEMINI_API_KEY (or use Antigravity's image-generator tool and place output at {out_rel}).")
            out_p.write_bytes(gen_gemini(prompt, key, model))
            print(f"[GEN]  {sid}: gemini ({model}) -> {out_rel}")
        else:
            sys.exit(f"[FAIL] {sid}: unknown provider {prov!r} (expected user_files|gemini|codex|custom_api|code_only)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Pluggable Art & Asset stage runner for Chiaki's-video-skill")
    ap.add_argument("cmd", choices=("init", "check", "run"))
    ap.add_argument("project", help="Project directory path")
    ap.add_argument("--only", default="", help="Comma-separated shot IDs to process")
    ap.add_argument("--dry", action="store_true", help="Preview planned actions without writing files or calling APIs")
    ap.add_argument("--force", action="store_true", help="Overwrite existing output files")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    if a.cmd == "init":
        return cmd_init(proj)
    if a.cmd == "check":
        return cmd_check(proj)
    return cmd_run(proj, a.only, a.dry, a.force)


if __name__ == "__main__":
    sys.exit(main())
