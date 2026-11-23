"""pack_skill.py — package Chiaki's-video-skill into a portable .skill (zip) archive.

Usage:
  python -X utf8 scripts/pack_skill.py [out.skill]          # full package (default: ../Chiaki's-video-skill.skill)
  python -X utf8 scripts/pack_skill.py --lite [out.skill]   # <=200 files for platforms with strict zip file caps
                                                       # (omits raw .ttf/.otf binaries, dev tests, and textures;
                                                       #  keeps scripts/fonts.py + fonts_starter.json + mgaudio + lib/motion)
"""
import os, sys, zipfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache", ".vscode", ".idea"}
SKIP_EXTS = {".pyc", ".pyo", ".nbc", ".nbi"}


def should_include(rel: str, lite: bool) -> bool:
    parts = rel.split("/")
    if any(p in SKIP_DIRS for p in parts):
        return False
    if Path(rel).suffix.lower() in SKIP_EXTS:
        return False
    # Keep exactly one SKILL.md inside .skill archives (exclude nested slash-command SKILL.md)
    if rel.startswith("commands/"):
        return False
    if lite:
        # Keep <= 200 files with exactly 1 SKILL.md for strict upload targets (e.g. claude.ai)
        if rel.startswith("assets/fonts/") and rel != "assets/fonts/catalog.json":
            return False
        if rel.startswith("assets/textures/") and rel != "assets/textures/README.md":
            return False
        if rel.startswith("assets/examples/"):
            return False
        if rel.startswith("assets/mgaudio/tools/"):
            return False
        if rel.startswith("docs/"):
            return False
    return True


def main():
    args = sys.argv[1:]
    lite = "--lite" in args
    args = [a for a in args if a != "--lite"]
    default_name = "Chiaki's-video-skill-lite.skill" if lite else "Chiaki's-video-skill.skill"
    out = Path(args[0]) if args else ROOT.parent / default_name
    out = out.resolve()
    prefix = "Chiaki's-video-skill"

    files = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if should_include(rel, lite):
            files.append((p, f"{prefix}/{rel}"))

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc in files:
            zf.write(src, arc)

    skill_mds = [arc for _, arc in files if arc.endswith("/SKILL.md") or arc == "SKILL.md"]
    sz_mb = out.stat().st_size / 1048576
    print(f"Packed {out}: {len(files)} files, {sz_mb:.2f} MB, SKILL.md={skill_mds}")
    if len(skill_mds) != 1:
        sys.exit(f"FAILED: expected 1 SKILL.md, found {len(skill_mds)}")
    if lite and len(files) > 200:
        sys.exit(f"FAILED: --lite exceeded 200-file cap ({len(files)} files)")
    print("OK")


if __name__ == "__main__":
    main()
