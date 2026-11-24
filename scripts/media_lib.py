"""media_lib.py — online & local 2D tactile texture + live-action stock footage manager.

Gives every Chiaki's-video-skill user out-of-the-box access to commercial-safe tactile
textures (paper, surface imperfections, scratches, concrete, fabric, grunge, film grain)
AND live-action stock footage/overlays (ink bleed, smoke, film burn, light leaks, space,
timelapses), automatically cached, prepared (`prep_texture.py` / FFmpeg `T3.sequence` frames),
and credited in `<project>/work/media_used.json`.

Zero-API-key providers (work immediately out of the box):
  - bundled    : 9 built-in CC0 2K/4K grain, dust, paper & washi overlays (`assets/textures/`)
  - ambientcg  : 2,000+ CC0 2K tactile textures & surface imperfections (ambientCG API v2)
  - polyhaven  : 870+ CC0 2K tactile textures (Poly Haven API, single-file direct download)
  - archive    : CC0 / Public Domain / Free Stock MP4 footage on Internet Archive (`stock_footage`)
  - nasa       : Public Domain HD/4K space, earth, nebula & launch MP4 footage (NASA Library)
  - local      : User's own local footage/texture folder (`CHIAKI_FOOTAGE_DIR`)

Optional free-key pro stock providers (30-second free signup for massive 4K overlay libraries):
  - pexels     : Pexels Video & Photo API (`PEXELS_API_KEY` — light leaks, ink, smoke, bokeh, city)
  - pixabay    : Pixabay Video & Photo API (`PIXABAY_API_KEY` — black-bg VFX overlays & footage)

Cache dir: `~/.cache/chiaki-video/media` (override with `CHIAKI_MEDIA_CACHE`).

Usage:
  python -X utf8 scripts/media_lib.py sources
  python -X utf8 scripts/media_lib.py search texture "paper scratches" [--source all] [--limit 8]
  python -X utf8 scripts/media_lib.py search footage "ink smoke" [--source all] [--limit 8]
  python -X utf8 scripts/media_lib.py get ambientcg SurfaceImperfections017 --kind texture --project <proj> [--prep paper]
  python -X utf8 scripts/media_lib.py get polyhaven concrete_wall_008 --kind texture --res 2k --project <proj>
  python -X utf8 scripts/media_lib.py get archive Ink224kRes --kind footage --project <proj> --seq --fps 24 --dur 4 --size 1280x720 --blend screen
  python -X utf8 scripts/media_lib.py get pexels 6313935 --kind footage --project <proj> --seq --fps 24 --dur 5
  python -X utf8 scripts/media_lib.py extract clip.mp4 web/assets/footage/leak01 --fps 24 --dur 5 --size 1280x720 --blend screen
  python -X utf8 scripts/media_lib.py credits <project>
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
BUNDLED_TEX = ROOT / "assets" / "textures"
UA = "ChiakiVideoSkill/1.8 (https://github.com/qianqiucn/Chiakis-video-skill)"

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def cache_root() -> Path:
    env = os.environ.get("CHIAKI_MEDIA_CACHE", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".cache" / "chiaki-video" / "media").resolve()


def read_key(env_name: str, fallback_file: str = "") -> str:
    v = os.environ.get(env_name, "").strip()
    if v:
        return v
    if fallback_file:
        p = Path(fallback_file).expanduser()
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    return ""


def pexels_key() -> str:
    return read_key("PEXELS_API_KEY", "~/.config/chiaki-video/pexels_api_key.txt")


def pixabay_key() -> str:
    return read_key("PIXABAY_API_KEY", "~/.config/chiaki-video/pixabay_api_key.txt")


def local_dir() -> Path | None:
    d = os.environ.get("CHIAKI_FOOTAGE_DIR", "").strip()
    if not d:
        return None
    p = Path(d).expanduser().resolve()
    return p if p.exists() else None


def find_ffmpeg() -> str:
    env = os.environ.get("CHIAKI_FFMPEG", "").strip()
    if env and Path(env).exists():
        return env
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


def http_json(url: str, headers: dict[str, str] | None = None, timeout: int = 18) -> Any:
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_download(url: str, dest: Path, headers: dict[str, str] | None = None, timeout: int = 120) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1024:
        return dest
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    tmp.replace(dest)
    return dest


def slugify(s: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9_-]+", "_", s.strip()).strip("_").lower()
    return out[:48] or "media"


# =====================================================================
# SEARCH PROVIDERS
# =====================================================================

def search_bundled(query: str, limit: int) -> list[dict[str, Any]]:
    if not BUNDLED_TEX.exists():
        return []
    toks = [t for t in re.split(r"[\s,_/-]+", query.lower()) if t]
    out = []
    for p in sorted(BUNDLED_TEX.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS:
            continue
        rel = p.relative_to(BUNDLED_TEX).as_posix()
        hay = rel.lower()
        if not toks or any(t in hay for t in toks):
            out.append({
                "provider": "bundled",
                "id": rel,
                "kind": "texture",
                "title": rel,
                "license": "CC0",
                "info": f"{p.stat().st_size // 1024} KB (local)",
                "url": "",
            })
    return out[:limit]


def search_local(kind: str, query: str, limit: int) -> list[dict[str, Any]]:
    ld = local_dir()
    if not ld:
        return []
    toks = [t for t in re.split(r"[\s,_/-]+", query.lower()) if t]
    out = []
    for p in sorted(ld.rglob("*")):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        k = "footage" if ext in VIDEO_EXTS else ("texture" if ext in IMAGE_EXTS else "")
        if not k or (kind != "all" and k != kind):
            continue
        rel = p.relative_to(ld).as_posix()
        if not toks or any(t in rel.lower() for t in toks):
            out.append({
                "provider": "local",
                "id": rel,
                "kind": k,
                "title": p.name,
                "license": "Local",
                "info": f"{p.stat().st_size / 1048576:.1f} MB",
                "url": str(p),
            })
        if len(out) >= limit:
            break
    return out


def search_ambientcg(query: str, limit: int) -> list[dict[str, Any]]:
    q = urllib.parse.quote(query)
    url = f"https://ambientcg.com/api/v2/full_json?q={q}&limit={limit}&type=Material,Decal,SurfaceImperfection"
    data = http_json(url)
    out = []
    for a in data.get("foundAssets", [])[:limit]:
        aid = a.get("assetId", "")
        if not aid:
            continue
        tags = ", ".join((a.get("tags") or [])[:4])
        out.append({
            "provider": "ambientcg",
            "id": aid,
            "kind": "texture",
            "title": f"{aid} ({tags})" if tags else aid,
            "license": "CC0",
            "info": a.get("dataType", "Material"),
            "url": f"https://ambientcg.com/view?id={aid}",
        })
    return out


_PH_CACHE: dict[str, Any] | None = None


def search_polyhaven(query: str, limit: int) -> list[dict[str, Any]]:
    global _PH_CACHE
    if _PH_CACHE is None:
        _PH_CACHE = http_json("https://api.polyhaven.com/assets?t=textures")
    toks = [t for t in re.split(r"[\s,_/-]+", query.lower()) if t]
    scored = []
    for aid, meta in (_PH_CACHE or {}).items():
        hay = " ".join([
            aid,
            str(meta.get("name", "")),
            " ".join(meta.get("tags") or []),
            " ".join(meta.get("categories") or []),
        ]).lower()
        hits = sum(1 for t in toks if t in hay) if toks else 1
        if hits > 0:
            scored.append((hits, int(meta.get("download_count", 0)), aid, meta))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    out = []
    for _, _, aid, meta in scored[:limit]:
        out.append({
            "provider": "polyhaven",
            "id": aid,
            "kind": "texture",
            "title": str(meta.get("name") or aid),
            "license": "CC0",
            "info": ", ".join((meta.get("categories") or [])[:2]) or "2K/4K",
            "url": f"https://polyhaven.com/a/{aid}",
        })
    return out


def search_archive(query: str, limit: int) -> list[dict[str, Any]]:
    clean_q = re.sub(r'["()]+', " ", query).strip()
    terms = " AND ".join(f'"{t}"' if " " in t else t for t in clean_q.split() if t)
    exclude = '-title:(war OR holocaust OR atrocity OR suicide OR documentary OR newsreel OR nazi OR propaganda)'
    match_part = f" AND (title:({terms}) OR subject:({terms}))" if terms else ""
    q_expr = (
        f'mediatype:movies AND (collection:stock_footage OR subject:"stock footage" OR subject:"free stock footage")'
        f"{match_part} AND {exclude}"
    )
    url = (
        "https://archive.org/advancedsearch.php?q="
        + urllib.parse.quote(q_expr)
        + f"&fl[]=identifier&fl[]=title&fl[]=licenseurl&fl[]=downloads&sort[]=downloads+desc&rows={limit}&output=json"
    )
    data = http_json(url)
    docs = data.get("response", {}).get("docs", [])
    # Fallback broader query if strict stock_footage returns empty
    if not docs and terms:
        q_fb = f'mediatype:movies AND title:({terms}) AND (subject:"stock" OR subject:"overlay" OR subject:"effect" OR subject:"footage" OR title:"free") AND {exclude}'
        url_fb = (
            "https://archive.org/advancedsearch.php?q="
            + urllib.parse.quote(q_fb)
            + f"&fl[]=identifier&fl[]=title&fl[]=licenseurl&fl[]=downloads&sort[]=downloads+desc&rows={limit}&output=json"
        )
        docs = http_json(url_fb).get("response", {}).get("docs", [])

    out = []
    for x in docs[:limit]:
        aid = x.get("identifier", "")
        if not aid:
            continue
        lic_u = str(x.get("licenseurl", ""))
        lic = "CC0/PD" if ("zero" in lic_u or "publicdomain" in lic_u) else ("CC-BY" if "by/" in lic_u else "Archive-Free")
        out.append({
            "provider": "archive",
            "id": aid,
            "kind": "footage",
            "title": str(x.get("title") or aid)[:60],
            "license": lic,
            "info": f"dl={x.get('downloads', 0)}",
            "url": f"https://archive.org/details/{aid}",
        })
    return out


def search_nasa(query: str, limit: int) -> list[dict[str, Any]]:
    q = urllib.parse.quote(query)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=video&page_size={limit}"
    data = http_json(url)
    out = []
    for item in data.get("collection", {}).get("items", [])[:limit]:
        meta = (item.get("data") or [{}])[0]
        nid = meta.get("nasa_id", "")
        if not nid:
            continue
        out.append({
            "provider": "nasa",
            "id": nid,
            "kind": "footage",
            "title": str(meta.get("title") or nid)[:60],
            "license": "PD (NASA)",
            "info": str(meta.get("date_created", ""))[:10],
            "url": f"https://images.nasa.gov/details/{nid}",
        })
    return out


def search_pexels(kind: str, query: str, limit: int) -> list[dict[str, Any]]:
    key = pexels_key()
    if not key:
        return []
    q = urllib.parse.quote(query)
    hdr = {"Authorization": key}
    out = []
    if kind in ("footage", "all"):
        data = http_json(f"https://api.pexels.com/videos/search?query={q}&per_page={limit}", headers=hdr)
        for v in data.get("videos", [])[:limit]:
            out.append({
                "provider": "pexels",
                "id": str(v["id"]),
                "kind": "footage",
                "title": f"Pexels Video #{v['id']} by {v.get('user', {}).get('name', 'Pexels')}",
                "license": "Pexels-Free",
                "info": f"{v.get('width')}x{v.get('height')} {v.get('duration')}s",
                "url": v.get("url", ""),
            })
    if kind in ("texture", "all"):
        data = http_json(f"https://api.pexels.com/v1/search?query={q}&per_page={limit}", headers=hdr)
        for p in data.get("photos", [])[:limit]:
            out.append({
                "provider": "pexels",
                "id": str(p["id"]),
                "kind": "texture",
                "title": (p.get("alt") or f"Pexels Photo #{p['id']}")[:60],
                "license": "Pexels-Free",
                "info": f"{p.get('width')}x{p.get('height')}",
                "url": p.get("url", ""),
            })
    return out[:limit]


def search_pixabay(kind: str, query: str, limit: int) -> list[dict[str, Any]]:
    key = pixabay_key()
    if not key:
        return []
    q = urllib.parse.quote(query)
    out = []
    if kind in ("footage", "all"):
        data = http_json(f"https://pixabay.com/api/videos/?key={key}&q={q}&per_page={min(limit, 20)}")
        for v in data.get("hits", [])[:limit]:
            med = v.get("videos", {}).get("large") or v.get("videos", {}).get("medium") or {}
            out.append({
                "provider": "pixabay",
                "id": str(v["id"]),
                "kind": "footage",
                "title": str(v.get("tags") or f"Pixabay #{v['id']}")[:60],
                "license": "Pixabay-Free",
                "info": f"{med.get('width', '?')}x{med.get('height', '?')} {v.get('duration', '?')}s",
                "url": v.get("pageURL", ""),
            })
    if kind in ("texture", "all"):
        data = http_json(f"https://pixabay.com/api/?key={key}&q={q}&image_type=photo&per_page={min(limit, 20)}")
        for p in data.get("hits", [])[:limit]:
            out.append({
                "provider": "pixabay",
                "id": str(p["id"]),
                "kind": "texture",
                "title": str(p.get("tags") or f"Pixabay #{p['id']}")[:60],
                "license": "Pixabay-Free",
                "info": f"{p.get('imageWidth', '?')}x{p.get('imageHeight', '?')}",
                "url": p.get("pageURL", ""),
            })
    return out[:limit]


# =====================================================================
# DOWNLOAD & PREPARE HELPERS
# =====================================================================

def extract_sequence(
    video_path: Path,
    out_dir: Path,
    fps: int = 24,
    start_s: float = 0.0,
    dur_s: float = 6.0,
    size: str = "1280x720",
    blend: str = "screen",
) -> dict[str, Any]:
    ff = find_ffmpeg()
    if not ff:
        sys.exit("FFmpeg not found (install ffmpeg or `pip install imageio-ffmpeg`) — required for --seq frame extraction.")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("f*.jpg"):
        old.unlink()

    vf_parts = [f"fps={fps}"]
    if size and "x" in size.lower():
        w, h = size.lower().split("x", 1)
        vf_parts.append(f"scale={int(w)}:{int(h)}:force_original_aspect_ratio=decrease")
    cmd = [ff, "-hide_banner", "-loglevel", "error", "-y"]
    if start_s > 0:
        cmd += ["-ss", f"{start_s:g}"]
    cmd += ["-i", str(video_path)]
    if dur_s > 0:
        cmd += ["-t", f"{dur_s:g}"]
    cmd += [
        "-vf", ",".join(vf_parts),
        "-fps_mode", "passthrough",
        "-q:v", "3",
        str(out_dir / "f%04d.jpg"),
    ]
    subprocess.check_call(cmd)
    frames = sorted(out_dir.glob("f*.jpg"))
    if not frames:
        sys.exit(f"FFmpeg extracted 0 frames from {video_path}")

    manifest = {
        "source_video": video_path.name,
        "frames": len(frames),
        "fps": fps,
        "pattern": "f%04d.jpg",
        "start_s": start_s,
        "dur_s": dur_s,
        "size_target": size,
        "blend_hint": blend,
        "t3_example": f"T3.sequence(layer, {{ dir: 'assets/footage/{out_dir.name}', count: {len(frames)}, pad: 4, ext: 'jpg', blend: '{blend}' }})",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def record_usage(project: str, entry: dict[str, Any]) -> None:
    if not project:
        return
    p = Path(project).resolve() / "work" / "media_used.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    items = []
    if p.exists():
        try:
            items = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            items = []
    key = (entry.get("provider"), entry.get("id"), entry.get("local_path"))
    items = [x for x in items if (x.get("provider"), x.get("id"), x.get("local_path")) != key]
    items.append(entry)
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def download_texture(provider: str, asset_id: str, res: str, map_pref: str) -> tuple[Path, dict[str, Any]]:
    cdir = cache_root() / provider / slugify(asset_id)
    cdir.mkdir(parents=True, exist_ok=True)

    if provider == "bundled":
        src = BUNDLED_TEX / asset_id
        if not src.exists():
            # Allow matching by filename
            matches = [p for p in BUNDLED_TEX.rglob("*") if p.is_file() and p.name.lower() == asset_id.lower()]
            if not matches:
                sys.exit(f"Bundled texture not found: {asset_id}")
            src = matches[0]
        return src, {"provider": "bundled", "id": src.relative_to(BUNDLED_TEX).as_posix(), "title": src.name, "license": "CC0", "author": "mg-styles-15 (CC0)", "url": ""}

    if provider == "local":
        ld = local_dir()
        if not ld:
            sys.exit("CHIAKI_FOOTAGE_DIR is not set.")
        src = ld / asset_id
        if not src.exists():
            sys.exit(f"Local texture not found: {src}")
        return src, {"provider": "local", "id": asset_id, "title": src.name, "license": "Local", "author": "User", "url": ""}

    if provider == "polyhaven":
        files = http_json(f"https://api.polyhaven.com/files/{urllib.parse.quote(asset_id)}")
        rk = "1k" if res.lower() == "1k" else "2k"
        order = ["Rough", "Diffuse", "AO"] if map_pref == "rough" else ["Diffuse", "Rough", "AO"]
        chosen_url = ""
        chosen_key = ""
        for k in order:
            blk = files.get(k, {}).get(rk, {})
            if isinstance(blk, dict):
                for ext in ("jpg", "png"):
                    if ext in blk and blk[ext].get("url"):
                        chosen_url = blk[ext]["url"]
                        chosen_key = f"{k.lower()}_{rk}.{ext}"
                        break
            if chosen_url:
                break
        if not chosen_url:
            sys.exit(f"No {rk} Diffuse/Rough texture map found for Poly Haven `{asset_id}`")
        dest = http_download(chosen_url, cdir / f"{slugify(asset_id)}_{chosen_key}")
        return dest, {"provider": "polyhaven", "id": asset_id, "title": asset_id, "license": "CC0", "author": "Poly Haven", "url": f"https://polyhaven.com/a/{asset_id}"}

    if provider == "ambientcg":
        data = http_json(f"https://ambientcg.com/api/v2/full_json?id={urllib.parse.quote(asset_id)}&include=downloadData")
        assets = data.get("foundAssets") or []
        if not assets:
            sys.exit(f"ambientCG asset not found: {asset_id}")
        a = assets[0]
        dls = a.get("downloadFolders", {}).get("default", {}).get("downloadFiletypeCategories", {}).get("zip", {}).get("downloads", [])
        want = "1K-JPG" if res.lower() == "1k" else "2K-JPG"
        pick = next((x for x in dls if x.get("attribute") == want), None) or (dls[0] if dls else None)
        if not pick or not pick.get("downloadLink"):
            sys.exit(f"No ZIP download found for ambientCG `{asset_id}`")
        # Check if extracted image already cached
        existing = sorted([p for p in cdir.glob("*") if p.suffix.lower() in IMAGE_EXTS])
        if existing:
            return existing[0], {"provider": "ambientcg", "id": asset_id, "title": asset_id, "license": "CC0", "author": "ambientCG", "url": f"https://ambientcg.com/view?id={asset_id}"}
        zpath = http_download(pick["downloadLink"], cdir / f"{asset_id}_{pick.get('attribute', '2K')}.zip")
        with zipfile.ZipFile(zpath, "r") as zf:
            imgs = [n for n in zf.namelist() if Path(n).suffix.lower() in IMAGE_EXTS and not Path(n).name.startswith(".")]
            if not imgs:
                sys.exit(f"No image files inside {zpath.name}")
            # Prefer Color -> Roughness -> Opacity -> first image
            pref_pats = ("_roughness", "_opacity", "_color") if map_pref == "rough" else ("_color", "_opacity", "_roughness")
            chosen = None
            for pat in pref_pats:
                chosen = next((n for n in imgs if pat in Path(n).name.lower()), None)
                if chosen:
                    break
            chosen = chosen or imgs[0]
            out_img = cdir / Path(chosen).name
            with zf.open(chosen) as src_f, open(out_img, "wb") as dst_f:
                shutil.copyfileobj(src_f, dst_f)
        # Remove zip after extracting the single 2D map to keep cache slim
        zpath.unlink(missing_ok=True)
        return out_img, {"provider": "ambientcg", "id": asset_id, "title": asset_id, "license": "CC0", "author": "ambientCG", "url": f"https://ambientcg.com/view?id={asset_id}"}

    if provider == "pexels":
        key = pexels_key()
        if not key:
            sys.exit("PEXELS_API_KEY not set (free key at https://www.pexels.com/api/).")
        p = http_json(f"https://api.pexels.com/v1/photos/{urllib.parse.quote(asset_id)}", headers={"Authorization": key})
        u = p.get("src", {}).get("large2x") or p.get("src", {}).get("original")
        dest = http_download(u, cdir / f"pexels_{asset_id}.jpg")
        return dest, {"provider": "pexels", "id": asset_id, "title": p.get("alt") or f"Pexels #{asset_id}", "license": "Pexels-Free", "author": p.get("photographer", "Pexels"), "url": p.get("url", "")}

    if provider == "pixabay":
        key = pixabay_key()
        if not key:
            sys.exit("PIXABAY_API_KEY not set (free key at https://pixabay.com/api/docs/).")
        d = http_json(f"https://pixabay.com/api/?key={key}&id={urllib.parse.quote(asset_id)}")
        hits = d.get("hits") or []
        if not hits:
            sys.exit(f"Pixabay photo not found: {asset_id}")
        p = hits[0]
        u = p.get("largeImageURL") or p.get("webformatURL")
        dest = http_download(u, cdir / f"pixabay_{asset_id}.jpg")
        return dest, {"provider": "pixabay", "id": asset_id, "title": p.get("tags") or f"Pixabay #{asset_id}", "license": "Pixabay-Free", "author": p.get("user", "Pixabay"), "url": p.get("pageURL", "")}

    sys.exit(f"Provider `{provider}` does not support kind=texture")


def download_footage(provider: str, asset_id: str, res: str, subfile: str = "") -> tuple[Path, dict[str, Any]]:
    cdir = cache_root() / provider / slugify(asset_id)
    cdir.mkdir(parents=True, exist_ok=True)

    if provider == "local":
        ld = local_dir()
        if not ld:
            sys.exit("CHIAKI_FOOTAGE_DIR is not set.")
        src = ld / asset_id
        if not src.exists():
            sys.exit(f"Local footage not found: {src}")
        return src, {"provider": "local", "id": asset_id, "title": src.name, "license": "Local", "author": "User", "url": ""}

    if provider == "archive":
        md = http_json(f"https://archive.org/metadata/{urllib.parse.quote(asset_id)}")
        mp4s = [f for f in md.get("files", []) if str(f.get("name", "")).lower().endswith(".mp4")]
        if not mp4s:
            sys.exit(f"No .mp4 files found in archive.org item `{asset_id}`")
        if subfile:
            chosen = next((f for f in mp4s if subfile.lower() in f["name"].lower()), mp4s[0])
        else:
            # Prefer a reasonable HD/4K file under 180 MB so download is fast and crisp
            def score(f):
                sz = int(f.get("size") or 0)
                w = int(f.get("width") or 0)
                ok_sz = 1 if (100_000 < sz < 180_000_000) else 0
                ok_hd = 1 if w >= 1280 else 0
                return (ok_sz, ok_hd, -abs(w - 1920) if w else -9999, -sz)
            mp4s.sort(key=score, reverse=True)
            chosen = mp4s[0]
        fname = chosen["name"]
        dl_url = f"https://archive.org/download/{urllib.parse.quote(asset_id)}/{urllib.parse.quote(fname)}"
        dest = http_download(dl_url, cdir / f"{slugify(Path(fname).stem)}.mp4")
        meta = md.get("metadata") or {}
        lic_u = str(meta.get("licenseurl", ""))
        lic = "CC0/PD" if ("zero" in lic_u or "publicdomain" in lic_u) else ("CC-BY" if "by/" in lic_u else "Archive-Free")
        return dest, {"provider": "archive", "id": asset_id, "title": str(meta.get("title") or asset_id), "license": lic, "author": str(meta.get("creator") or "Internet Archive"), "url": f"https://archive.org/details/{asset_id}"}

    if provider == "nasa":
        d = http_json(f"https://images-api.nasa.gov/search?nasa_id={urllib.parse.quote(asset_id)}&media_type=video")
        items = d.get("collection", {}).get("items") or []
        if not items:
            sys.exit(f"NASA video not found: {asset_id}")
        item = items[0]
        meta = (item.get("data") or [{}])[0]
        manifest = http_json(item["href"])
        mp4s = [u.replace("http://", "https://") for u in manifest if str(u).lower().endswith(".mp4")]
        if not mp4s:
            sys.exit(f"No .mp4 found in NASA manifest for `{asset_id}`")
        pref = ("~medium.mp4", "~large.mp4", "~orig.mp4", "~mobile.mp4") if res.lower() in ("1k", "hd") else ("~orig.mp4", "~large.mp4", "~medium.mp4")
        chosen = next((u for suf in pref for u in mp4s if u.lower().endswith(suf)), mp4s[0])
        dest = http_download(chosen, cdir / f"{slugify(asset_id)}.mp4")
        return dest, {"provider": "nasa", "id": asset_id, "title": str(meta.get("title") or asset_id), "license": "Public Domain (NASA)", "author": "NASA", "url": f"https://images.nasa.gov/details/{asset_id}"}

    if provider == "pexels":
        key = pexels_key()
        if not key:
            sys.exit("PEXELS_API_KEY not set (free key at https://www.pexels.com/api/).")
        v = http_json(f"https://api.pexels.com/videos/videos/{urllib.parse.quote(asset_id)}", headers={"Authorization": key})
        vfiles = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("link")]
        if not vfiles:
            sys.exit(f"No MP4 found for Pexels video `{asset_id}`")
        target_w = 3840 if res.lower() == "4k" else 1920
        vfiles.sort(key=lambda f: (abs(int(f.get("width") or 0) - target_w), -int(f.get("width") or 0)))
        dest = http_download(vfiles[0]["link"], cdir / f"pexels_{asset_id}.mp4")
        return dest, {"provider": "pexels", "id": asset_id, "title": f"Pexels Video #{asset_id}", "license": "Pexels-Free", "author": v.get("user", {}).get("name", "Pexels"), "url": v.get("url", "")}

    if provider == "pixabay":
        key = pixabay_key()
        if not key:
            sys.exit("PIXABAY_API_KEY not set (free key at https://pixabay.com/api/docs/).")
        d = http_json(f"https://pixabay.com/api/videos/?key={key}&id={urllib.parse.quote(asset_id)}")
        hits = d.get("hits") or []
        if not hits:
            sys.exit(f"Pixabay video not found: {asset_id}")
        v = hits[0]
        vids = v.get("videos") or {}
        pick = vids.get("large") or vids.get("medium") or vids.get("small")
        if not pick or not pick.get("url"):
            sys.exit(f"No MP4 URL for Pixabay video `{asset_id}`")
        dest = http_download(pick["url"], cdir / f"pixabay_{asset_id}.mp4")
        return dest, {"provider": "pixabay", "id": asset_id, "title": str(v.get("tags") or f"Pixabay #{asset_id}"), "license": "Pixabay-Free", "author": v.get("user", "Pixabay"), "url": v.get("pageURL", "")}

    sys.exit(f"Provider `{provider}` does not support kind=footage")


# =====================================================================
# CLI
# =====================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="Online & local 2D texture + live-action stock footage library for Chiaki's-video-skill")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sources", help="Show active zero-key and optional-key providers")

    ps = sub.add_parser("search", help="Search online & local textures or live-action stock footage")
    ps.add_argument("kind", choices=("texture", "footage", "all"))
    ps.add_argument("query", help="Search keywords (English works best, e.g. 'paper', 'surface imperfection', 'ink', 'smoke', 'light leak')")
    ps.add_argument("--source", default="all", choices=("all", "bundled", "ambientcg", "polyhaven", "archive", "nasa", "pexels", "pixabay", "local"))
    ps.add_argument("--limit", type=int, default=6, help="Max results per provider (default 6)")
    ps.add_argument("--json", action="store_true")

    pg = sub.add_parser("get", help="Download a texture or footage item (auto-cache, optional prep_texture or --seq frame extraction)")
    pg.add_argument("provider", choices=("bundled", "ambientcg", "polyhaven", "archive", "nasa", "pexels", "pixabay", "local"))
    pg.add_argument("asset_id")
    pg.add_argument("--kind", choices=("texture", "footage", "auto"), default="auto")
    pg.add_argument("--res", default="2k", help="Texture: 1k|2k · Footage: hd|4k")
    pg.add_argument("--map", choices=("color", "rough"), default="color", help="Texture map preference (ambientCG/PolyHaven)")
    pg.add_argument("--prep", choices=("", "paper", "stone", "grain"), default="", help="Auto-run scripts/prep_texture.py on downloaded texture")
    pg.add_argument("--seq", action="store_true", help="For footage: extract deterministic f0001.jpg.. sequence + manifest.json for T3.sequence")
    pg.add_argument("--fps", type=int, default=24)
    pg.add_argument("--from", dest="start_s", type=float, default=0.0)
    pg.add_argument("--dur", type=float, default=6.0, help="Seconds to extract for --seq (default 6.0; 0 = full)")
    pg.add_argument("--size", default="1280x720", help="Target max WxH for --seq frames (default 1280x720)")
    pg.add_argument("--blend", default="screen", choices=("screen", "multiply", "overlay", "normal"))
    pg.add_argument("--file", default="", help="Optional filename substring when an archive.org item has multiple MP4s")
    pg.add_argument("--project", default="", help="Project root (copies into web/assets/tex or web/assets/footage & logs work/media_used.json)")
    pg.add_argument("--out", default="", help="Explicit destination file/folder override")

    pe = sub.add_parser("extract", help="Convert any local MP4/MOV/WebM into a deterministic T3.sequence frame folder")
    pe.add_argument("video")
    pe.add_argument("out_dir")
    pe.add_argument("--fps", type=int, default=24)
    pe.add_argument("--from", dest="start_s", type=float, default=0.0)
    pe.add_argument("--dur", type=float, default=6.0)
    pe.add_argument("--size", default="1280x720")
    pe.add_argument("--blend", default="screen", choices=("screen", "multiply", "overlay", "normal"))

    pc = sub.add_parser("credits", help="Print license & attribution lines from <project>/work/media_used.json")
    pc.add_argument("project")

    args = ap.parse_args()

    if args.cmd == "sources":
        print(f"=== Chiaki Media Library (cache: {cache_root()}) ===")
        print("Zero-Key (ready immediately out of the box):")
        print(f"  [OK] bundled    : 9 built-in CC0 textures ({BUNDLED_TEX})")
        print("  [OK] ambientcg  : 2,000+ CC0 2K tactile textures & surface imperfections")
        print("  [OK] polyhaven  : 870+ CC0 2K tactile textures (direct single-file download)")
        print("  [OK] archive    : Internet Archive CC0/PD stock_footage MP4 clips (ink, smoke, timelapses, film burn)")
        print("  [OK] nasa       : NASA Public Domain HD/4K space, earth & nebula MP4 footage")
        print("Optional Free-Key / Local Pro Libraries:")
        print(f"  [{'OK' if pexels_key() else '--'}] pexels     : {'PEXELS_API_KEY set' if pexels_key() else 'set PEXELS_API_KEY (free at pexels.com/api for 4K light leaks/smoke/city)'}")
        print(f"  [{'OK' if pixabay_key() else '--'}] pixabay    : {'PIXABAY_API_KEY set' if pixabay_key() else 'set PIXABAY_API_KEY (free at pixabay.com/api/docs for black-bg VFX overlays)'}")
        print(f"  [{'OK' if local_dir() else '--'}] local      : {local_dir() if local_dir() else 'set CHIAKI_FOOTAGE_DIR to index your own local stock library'}")
        return 0

    if args.cmd == "search":
        results: list[dict[str, Any]] = []
        src = args.source
        kind = args.kind
        lim = args.limit
        tasks = []
        if kind in ("texture", "all"):
            if src in ("all", "bundled"):
                tasks.append(("bundled", lambda: search_bundled(args.query, lim)))
            if src in ("all", "ambientcg"):
                tasks.append(("ambientcg", lambda: search_ambientcg(args.query, lim)))
            if src in ("all", "polyhaven"):
                tasks.append(("polyhaven", lambda: search_polyhaven(args.query, lim)))
        if kind in ("footage", "all"):
            if src in ("all", "archive"):
                tasks.append(("archive", lambda: search_archive(args.query, lim)))
            if src in ("all", "nasa"):
                tasks.append(("nasa", lambda: search_nasa(args.query, lim)))
        if src in ("all", "pexels") and pexels_key():
            tasks.append(("pexels", lambda: search_pexels(kind, args.query, lim)))
        if src in ("all", "pixabay") and pixabay_key():
            tasks.append(("pixabay", lambda: search_pixabay(kind, args.query, lim)))
        if src in ("all", "local") and local_dir():
            tasks.append(("local", lambda: search_local(kind, args.query, lim)))

        for name, fn in tasks:
            try:
                results.extend(fn())
            except Exception as e:
                print(f"[WARN] {name} search failed: {e}", file=sys.stderr)

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return 0
        if not results:
            print(f"No {kind} matches for {args.query!r}. Tip: try broader English keywords or set PEXELS_API_KEY / PIXABAY_API_KEY.")
            return 0
        print(f"{'PROVIDER:ID':<36} {'KIND':<8} {'LICENSE':<13} {'INFO':<16} TITLE")
        print("-" * 112)
        for r in results:
            pid = f"{r['provider']}:{r['id']}"
            print(f"{pid:<36} {r['kind']:<8} {r['license']:<13} {str(r['info'])[:15]:<16} {r['title']}")
        return 0

    if args.cmd == "get":
        kind = args.kind
        if kind == "auto":
            if args.provider in ("bundled", "ambientcg", "polyhaven"):
                kind = "texture"
            elif args.provider in ("archive", "nasa"):
                kind = "footage"
            else:
                kind = "footage" if args.seq else "texture"

        if kind == "texture":
            cached, meta = download_texture(args.provider, args.asset_id, args.res, args.map)
            dest = cached
            if args.out:
                dest = Path(args.out).resolve()
            elif args.project:
                dest = Path(args.project).resolve() / "web" / "assets" / "tex" / f"{slugify(args.provider + '_' + args.asset_id)}{cached.suffix}"

            if dest != cached:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if args.prep:
                    prep_py = ROOT / "scripts" / "prep_texture.py"
                    subprocess.check_call([
                        sys.executable, "-X", "utf8", str(prep_py), str(cached), str(dest), "--mode", args.prep, "--size", "1920x1080",
                    ])
                else:
                    shutil.copy2(cached, dest)
            elif args.prep:
                out_p = cached.with_name(cached.stem + f"_{args.prep}.png")
                subprocess.check_call([
                    sys.executable, "-X", "utf8", str(ROOT / "scripts" / "prep_texture.py"), str(cached), str(out_p), "--mode", args.prep, "--size", "1920x1080",
                ])
                dest = out_p

            meta["kind"] = "texture"
            meta["local_path"] = str(dest)
            record_usage(args.project, meta)
            print(f"[OK] texture -> {dest} ({meta['license']})")
            return 0

        # kind == "footage"
        cached, meta = download_footage(args.provider, args.asset_id, args.res, args.file)
        slug = slugify(f"{args.provider}_{args.asset_id}")
        if args.seq:
            seq_dir = (
                Path(args.out).resolve()
                if args.out
                else (
                    Path(args.project).resolve() / "web" / "assets" / "footage" / slug
                    if args.project
                    else cached.parent / f"seq_{args.fps}fps"
                )
            )
            mf = extract_sequence(cached, seq_dir, args.fps, args.start_s, args.dur, args.size, args.blend)
            meta["kind"] = "footage_seq"
            meta["local_path"] = str(seq_dir)
            meta["frames"] = mf["frames"]
            record_usage(args.project, meta)
            print(f"[OK] footage sequence ({mf['frames']} f @ {args.fps} fps) -> {seq_dir} ({meta['license']})")
            print(f"     T3.sequence: {mf['t3_example']}")
            return 0

        dest = cached
        if args.out:
            dest = Path(args.out).resolve()
        elif args.project:
            dest = Path(args.project).resolve() / "web" / "assets" / "footage" / f"{slug}.mp4"
        if dest != cached:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cached, dest)
        meta["kind"] = "footage"
        meta["local_path"] = str(dest)
        record_usage(args.project, meta)
        print(f"[OK] footage -> {dest} ({meta['license']})")
        return 0

    if args.cmd == "extract":
        mf = extract_sequence(Path(args.video).resolve(), Path(args.out_dir).resolve(), args.fps, args.start_s, args.dur, args.size, args.blend)
        print(f"[OK] extracted {mf['frames']} frames @ {args.fps} fps -> {args.out_dir}")
        print(f"     T3.sequence: {mf['t3_example']}")
        return 0

    if args.cmd == "credits":
        p = Path(args.project).resolve() / "work" / "media_used.json"
        if not p.exists():
            print("No online/external media logged in work/media_used.json.")
            return 0
        items = json.loads(p.read_text(encoding="utf-8"))
        print("Media & Texture Credits:")
        for it in items:
            u = f" ({it['url']})" if it.get("url") else ""
            print(f"  - {it.get('title', it.get('id'))} — {it.get('author', it.get('provider'))} [{it.get('license', 'Free')}]{u}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
