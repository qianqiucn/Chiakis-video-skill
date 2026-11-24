"""art_gen.py — pluggable Art & Asset stage runner for Chiaki's-video-skill (Python stdlib only).

Supports four clean, vendor-neutral asset sources declared per shot in <project>/work/art_manifest.json:
  - user_files : copy verified client-provided images into web/assets/art/
  - custom_api : OpenAI-Images / Ark-compatible POST endpoint
                 (CHIAKI_IMAGE_API_URL / CHIAKI_IMAGE_API_KEY or CHIAKI_IMAGE_API_KEY_FILE / CHIAKI_IMAGE_MODEL)
  - codex      : OpenAI gpt-image-1 endpoint (OPENAI_API_KEY / CHIAKI_OPENAI_IMAGE_MODEL)
  - gemini     : Gemini multimodal image generation (GEMINI_API_KEY / CHIAKI_GEMINI_IMAGE_MODEL)
  - code_only  : procedural 2D / Blender shot (no bitmap needed)

v1.5.0 upgrades:
  - Per-shot `refs: ["path/to/char_sheet.png", ...]` for multi-reference character & style anchoring
    (passed as base64 data URIs in `image` for custom_api, `inlineData` parts for Gemini, and multipart
    `/v1/images/edits` for OpenAI codex).
  - `--workers N` parallel execution (`ThreadPoolExecutor`) + exponential-backoff retry on HTTP 429/5xx/timeouts.
  - Optional `CHIAKI_IMAGE_API_KEY_FILE` fallback (reads stripped key from local key file).

Usage:
  python -X utf8 scripts/art_gen.py init <project>
  python -X utf8 scripts/art_gen.py check <project>
  python -X utf8 scripts/art_gen.py run <project> [--only <id>] [--workers 3] [--retries 3] [--dry] [--force]
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import mimetypes
import os
import random
import shutil
import socket
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

UA = "chiaki-video-artgen/1.5 (https://github.com/qianqiucn/Chiakis-video-skill)"
RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}

SAMPLE_MANIFEST = {
    "project": "demo_project",
    "defaults": {
        "provider": "user_files",
        "size": "1920x1080",
        "style_bible": "Consistent editorial colour arc, crisp silhouette clarity, zero embedded text or watermarks.",
        "extra_body": {},
    },
    "shots": [
        {
            "id": "act1_hero",
            "act": "act1",
            "provider": "user_files",
            "source": "",
            "refs": [],
            "out": "web/assets/art/act1_hero.png",
            "prompt": "Wide cinematic key visual with clean upper-left negative space for kinetic typography.",
            "needs_depth": False,
            "notes": "Set provider to user_files | gemini | codex | custom_api | code_only; add refs: [...] for character/style anchoring.",
        }
    ],
}


def _read_key_env_or_file(env_key: str, env_file: str = "") -> str:
    val = os.environ.get(env_key, "").strip()
    if val:
        return val
    if env_file:
        fp = os.environ.get(env_file, "").strip()
        if fp and Path(fp).exists():
            for line in Path(fp).read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if "=" in s:
                    k, v = s.split("=", 1)
                    if k.strip().upper() in (env_key, "API_KEY", "KEY", "TOKEN"):
                        return v.strip().strip('"').strip("'")
                return s.strip('"').strip("'")
    return ""


def _resolve_refs(proj: Path, refs: list[str] | None) -> list[Path]:
    out: list[Path] = []
    for raw in refs or []:
        if not raw:
            continue
        p = Path(raw)
        if not p.is_absolute():
            p = (proj / p).resolve()
        if not p.exists():
            raise RuntimeError(f"Reference image not found: {raw} (resolved: {p})")
        out.append(p)
    return out


def _mime_for(path: Path) -> str:
    m, _ = mimetypes.guess_type(str(path))
    return m if m and m.startswith("image/") else "image/png"


def _to_data_uri(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{_mime_for(path)};base64,{b64}"


def _with_retry(fn, retries: int = 3, label: str = "request"):
    last_err = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            last_err = RuntimeError(f"HTTP {e.code} ({label}): {body}")
            if e.code not in RETRYABLE_HTTP or attempt >= retries:
                raise last_err from None
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as e:
            last_err = RuntimeError(f"Network/timeout error ({label}): {e}")
            if attempt >= retries:
                raise last_err from None
        delay = (2.0 ** attempt) + random.uniform(0.2, 0.9)
        print(f"  [RETRY {attempt + 1}/{retries}] {label}: {last_err} -> waiting {delay:.1f}s")
        time.sleep(delay)
    raise last_err  # pragma: no cover


def http_json(url: str, payload: dict, headers: dict, timeout: int = 180, retries: int = 3) -> dict:
    data = json.dumps(payload).encode("utf-8")

    def _do():
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": UA, **headers},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    return _with_retry(_do, retries=retries, label=url)


def http_multipart(
    url: str,
    fields: list[tuple[str, str]],
    files: list[tuple[str, Path]],
    headers: dict,
    timeout: int = 180,
    retries: int = 3,
) -> dict:
    boundary = f"----ChiakiArtGen{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, val in fields:
        chunks.append(f"--{boundary}\r\n".encode("ascii"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(val.encode("utf-8") + b"\r\n")
    for field_name, path in files:
        chunks.append(f"--{boundary}\r\n".encode("ascii"))
        chunks.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'
            f"Content-Type: {_mime_for(path)}\r\n\r\n".encode("utf-8")
        )
        chunks.append(path.read_bytes() + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("ascii"))
    body = b"".join(chunks)

    def _do():
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": UA,
                **headers,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    return _with_retry(_do, retries=retries, label=url)


def download_bytes(url: str, timeout: int = 180, retries: int = 3) -> bytes:
    def _do():
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()

    return _with_retry(_do, retries=retries, label="download")


def _extract_openai_image(res: dict, url: str, retries: int) -> bytes:
    items = res.get("data") or []
    if not items:
        raise RuntimeError(f"No image data returned by {url}: {str(res)[:300]}")
    item = items[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        return download_bytes(item["url"], retries=retries)
    raise RuntimeError(f"Unsupported image response item keys: {list(item.keys())}")


def gen_openai_compat(
    prompt: str,
    size: str,
    url: str,
    key: str,
    model: str,
    refs: list[Path] | None = None,
    extra_body: dict | None = None,
    retries: int = 3,
) -> bytes:
    payload: dict = {"model": model, "prompt": prompt, "size": size, "n": 1}
    if extra_body:
        payload.update(extra_body)
    if refs:
        uris = [_to_data_uri(p) for p in refs]
        payload["image"] = uris if len(uris) > 1 else uris[0]
    res = http_json(url, payload, {"Authorization": f"Bearer {key}"}, retries=retries)
    return _extract_openai_image(res, url, retries=retries)


def gen_codex(
    prompt: str,
    size: str,
    key: str,
    model: str,
    refs: list[Path] | None = None,
    extra_body: dict | None = None,
    retries: int = 3,
) -> bytes:
    if not refs:
        return gen_openai_compat(
            prompt,
            size,
            "https://api.openai.com/v1/images/generations",
            key,
            model,
            refs=None,
            extra_body=extra_body,
            retries=retries,
        )
    url = "https://api.openai.com/v1/images/edits"
    fields = [("model", model), ("prompt", prompt), ("size", size), ("n", "1")]
    for k, v in (extra_body or {}).items():
        fields.append((str(k), str(v)))
    files = [("image[]" if len(refs) > 1 else "image", p) for p in refs]
    res = http_multipart(url, fields, files, {"Authorization": f"Bearer {key}"}, retries=retries)
    return _extract_openai_image(res, url, retries=retries)


def gen_gemini(
    prompt: str,
    key: str,
    model: str,
    refs: list[Path] | None = None,
    retries: int = 3,
) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    parts: list[dict] = []
    for p in refs or []:
        parts.append({
            "inlineData": {
                "mimeType": _mime_for(p),
                "data": base64.b64encode(p.read_bytes()).decode("ascii"),
            }
        })
    parts.append({"text": prompt})
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    res = http_json(url, payload, {"x-goog-api-key": key}, retries=retries)
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
        refs = s.get("refs") or []
        ref_tag = f" refs={len(refs)}" if refs else ""
        if prov == "code_only":
            print(f"  [CODE] {sid:24s} provider=code_only (procedural)")
            continue
        out_rel = s.get("out") or f"web/assets/art/{sid}.png"
        out_p = proj / out_rel
        if out_p.exists() and out_p.stat().st_size > 0:
            kb = out_p.stat().st_size / 1024
            print(f"  [OK]   {sid:24s} provider={prov:10s}{ref_tag:8s} {out_rel} ({kb:.1f} KB)")
        else:
            missing += 1
            print(f"  [MISS] {sid:24s} provider={prov:10s}{ref_tag:8s} expected {out_rel}")
    print(f"\nManifest {mp}: {len(shots)} shot(s), {missing} missing.")
    return 1 if missing else 0


def _process_shot(
    proj: Path,
    s: dict,
    defaults: dict,
    dry: bool,
    force: bool,
    retries: int,
) -> str:
    sid = s.get("id", "?")
    prov = s.get("provider") or defaults.get("provider") or "user_files"
    if prov == "code_only":
        return f"[SKIP] {sid}: code_only"
    out_rel = s.get("out") or f"web/assets/art/{sid}.png"
    out_p = proj / out_rel
    if out_p.exists() and not force:
        return f"[KEEP] {sid}: already exists -> {out_rel}"

    size = s.get("size") or defaults.get("size") or "1920x1080"
    prompt = full_prompt(s, defaults)
    raw_refs = s.get("refs") or defaults.get("refs") or []
    refs = _resolve_refs(proj, raw_refs) if raw_refs else []
    extra_body = {**(defaults.get("extra_body") or {}), **(s.get("extra_body") or {})}

    if dry:
        r_info = f" refs={len(refs)}" if refs else ""
        return f"[DRY]  {sid}: provider={prov} size={size}{r_info} -> {out_rel}"

    out_p.parent.mkdir(parents=True, exist_ok=True)
    if prov == "user_files":
        src = s.get("source") or ""
        src_p = Path(src) if Path(src).is_absolute() else (proj / src)
        if not src or not src_p.exists():
            raise RuntimeError(f"{sid}: provider=user_files but source missing ({src!r}) and {out_rel} not on disk.")
        shutil.copy2(src_p, out_p)
        return f"[COPY] {sid}: {src} -> {out_rel}"
    if prov == "custom_api":
        url = os.environ.get("CHIAKI_IMAGE_API_URL", "").strip()
        key = _read_key_env_or_file("CHIAKI_IMAGE_API_KEY", "CHIAKI_IMAGE_API_KEY_FILE")
        model = s.get("model") or os.environ.get("CHIAKI_IMAGE_MODEL", "").strip()
        if not (url and key and model):
            raise RuntimeError(
                f"{sid}: custom_api requires CHIAKI_IMAGE_API_URL, CHIAKI_IMAGE_API_KEY (or CHIAKI_IMAGE_API_KEY_FILE), and CHIAKI_IMAGE_MODEL."
            )
        out_p.write_bytes(
            gen_openai_compat(prompt, size, url, key, model, refs=refs, extra_body=extra_body, retries=retries)
        )
        return f"[GEN]  {sid}: custom_api ({model}, refs={len(refs)}) -> {out_rel}"
    if prov == "codex":
        key = _read_key_env_or_file("OPENAI_API_KEY", "OPENAI_API_KEY_FILE")
        model = s.get("model") or os.environ.get("CHIAKI_OPENAI_IMAGE_MODEL", "gpt-image-1")
        if not key:
            raise RuntimeError(
                f"{sid}: codex provider requires OPENAI_API_KEY (or use Codex's built-in image tool and place output at {out_rel})."
            )
        out_p.write_bytes(
            gen_codex(prompt, size, key, model, refs=refs, extra_body=extra_body, retries=retries)
        )
        return f"[GEN]  {sid}: codex ({model}, refs={len(refs)}) -> {out_rel}"
    if prov == "gemini":
        key = _read_key_env_or_file("GEMINI_API_KEY", "GEMINI_API_KEY_FILE")
        model = s.get("model") or os.environ.get("CHIAKI_GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
        if not key:
            raise RuntimeError(
                f"{sid}: gemini provider requires GEMINI_API_KEY (or use Antigravity's image-generator tool and place output at {out_rel})."
            )
        out_p.write_bytes(gen_gemini(prompt, key, model, refs=refs, retries=retries))
        return f"[GEN]  {sid}: gemini ({model}, refs={len(refs)}) -> {out_rel}"
    raise RuntimeError(f"{sid}: unknown provider {prov!r} (expected user_files|gemini|codex|custom_api|code_only)")


def cmd_run(proj: Path, only: str, dry: bool, force: bool, workers: int, retries: int) -> int:
    _, data = load_manifest(proj)
    defaults = data.get("defaults") or {}
    shots = data.get("shots") or []
    if only:
        want = {x.strip() for x in only.split(",") if x.strip()}
        shots = [s for s in shots if s.get("id") in want]

    workers = max(1, workers)
    errors: list[str] = []

    if workers == 1 or len(shots) <= 1 or dry:
        for s in shots:
            try:
                print(_process_shot(proj, s, defaults, dry, force, retries))
            except Exception as e:
                print(f"[FAIL] {e}", file=sys.stderr)
                errors.append(str(e))
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            fut_map = {
                ex.submit(_process_shot, proj, s, defaults, dry, force, retries): s.get("id", "?")
                for s in shots
            }
            for fut in concurrent.futures.as_completed(fut_map):
                try:
                    print(fut.result())
                except Exception as e:
                    print(f"[FAIL] {e}", file=sys.stderr)
                    errors.append(str(e))

    return 1 if errors else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Pluggable Art & Asset stage runner for Chiaki's-video-skill")
    ap.add_argument("cmd", choices=("init", "check", "run"))
    ap.add_argument("project", help="Project directory path")
    ap.add_argument("--only", default="", help="Comma-separated shot IDs to process")
    ap.add_argument("--workers", type=int, default=1, help="Parallel worker threads for API calls (default 1)")
    ap.add_argument("--retries", type=int, default=3, help="Exponential-backoff retry attempts on 429/5xx (default 3)")
    ap.add_argument("--dry", action="store_true", help="Preview planned actions without writing files or calling APIs")
    ap.add_argument("--force", action="store_true", help="Overwrite existing output files")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    if a.cmd == "init":
        return cmd_init(proj)
    if a.cmd == "check":
        return cmd_check(proj)
    return cmd_run(proj, a.only, a.dry, a.force, a.workers, a.retries)


if __name__ == "__main__":
    sys.exit(main())
