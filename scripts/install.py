"""install.py — unified cross-platform installer for Chiaki's-video-skill.

Automatically installs the core skill AND resolves `<SKILL_DIR>` inside the unified `/chiaki` (`$chiaki`)
command for Antigravity, Codex, and Claude Code — zero path placeholders left behind, zero collisions with
other installed video skills.

Usage:
  python -X utf8 scripts/install.py --target antigravity     # ~/.gemini/config/plugins/chiakis-video-skill (/chiaki)
  python -X utf8 scripts/install.py --target codex           # ~/.codex/skills/chiakis-video-skill + chiaki ($chiaki)
  python -X utf8 scripts/install.py --target claude          # ~/.claude/skills/chiakis-video-skill + commands/chiaki.md (/chiaki)
  python -X utf8 scripts/install.py --target all             # install for Antigravity + Codex + Claude Code
  python -X utf8 scripts/install.py --target codex --dry-run # preview actions without touching disk
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
SKILL_SLUG = "chiakis-video-skill"
VERSION = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8")).get("version", "1.6.2")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def copy_tree(src: Path, dst: Path):
    for p in src.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(src)
        out = dst / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        elif p.is_file():
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)


def copy_skill_payload(skill_dir: Path):
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
    skill_dir.mkdir(parents=True, exist_ok=True)
    for fname in ("SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "requirements.txt"):
        if (ROOT / fname).exists():
            shutil.copy2(ROOT / fname, skill_dir / fname)
    for sub in ("references", "scripts", "assets"):
        copy_tree(ROOT / sub, skill_dir / sub)


def render_command(skill_dir: Path, for_claude_cmd: bool = False) -> str:
    txt = (ROOT / "commands" / "chiaki" / "SKILL.md").read_text(encoding="utf-8")
    txt = txt.replace("<SKILL_DIR>", skill_dir.as_posix())
    if for_claude_cmd:
        # Claude Code ~/.claude/commands/chiaki.md uses plain markdown (strip YAML skill frontmatter)
        if txt.startswith("---"):
            parts = txt.split("---", 2)
            if len(parts) == 3:
                txt = parts[2].lstrip("\r\n")
    return txt


def install_antigravity(dest_override: str | None, dry: bool):
    dest = Path(dest_override).resolve() if dest_override else (Path.home() / ".gemini" / "config" / "plugins" / SKILL_SLUG).resolve()
    skill_dir = dest / "skills" / SKILL_SLUG
    cmd_dir = dest / "skills" / "chiaki"
    hook_script = dest / "hooks" / "chiaki_guard.py"
    hook_cmd = f'"{sys.executable}" -X utf8 "{hook_script.as_posix()}"'

    hooks_obj = {
        "chiaki-video-guard": {
            "PreToolUse": [
                {
                    "matcher": "invoke_subagent|run_command",
                    "hooks": [{"type": "command", "command": hook_cmd}],
                }
            ]
        }
    }
    plugin_obj = {
        "name": SKILL_SLUG,
        "displayName": "Chiaki's-video-skill (Flagship 2D + Blender 3D Video Studio)",
        "version": VERSION,
        "description": "Flagship deterministic 13-stage 2D + 2.5D + Blender 3D motion graphics, fast-cut PV/MV, and kinetic typography studio plugin (/chiaki).",
        "license": "MIT",
    }

    if dry:
        print(f"[DRY RUN] Antigravity plugin -> {dest}")
        print(f"  - Command /chiaki: {cmd_dir / 'SKILL.md'}")
        print(f"  - Core skill:      {skill_dir / 'SKILL.md'}")
        print(f"  - Hooks:           {dest / 'hooks.json'}")
        return

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    cmd_dir.mkdir(parents=True, exist_ok=True)

    (dest / "plugin.json").write_text(json.dumps(plugin_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "hooks.json").write_text(json.dumps(hooks_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    copy_tree(ROOT / "hooks", dest / "hooks")
    copy_tree(ROOT / "rules", dest / "rules")
    copy_tree(ROOT / "agents", dest / "agents")
    if (ROOT / "assets" / "logo.svg").exists():
        (dest / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "assets" / "logo.svg", dest / "assets" / "logo.svg")

    (cmd_dir / "SKILL.md").write_text(render_command(skill_dir), encoding="utf-8", newline="\n")
    copy_skill_payload(skill_dir)

    print(f"[OK] Installed Antigravity plugin (v{VERSION}) -> {dest}")
    print(f"     Command: /chiaki ({cmd_dir / 'SKILL.md'})")
    print(f"     Skill:   {skill_dir / 'SKILL.md'}")


def install_codex(dest_override: str | None, dry: bool):
    base = Path(dest_override).resolve() if dest_override else (Path.home() / ".codex" / "skills").resolve()
    skill_dir = base / SKILL_SLUG
    cmd_dir = base / "chiaki"

    if dry:
        print(f"[DRY RUN] Codex skills -> {base}")
        print(f"  - Command $chiaki: {cmd_dir / 'SKILL.md'}")
        print(f"  - Core skill:      {skill_dir / 'SKILL.md'}")
        return

    base.mkdir(parents=True, exist_ok=True)
    copy_skill_payload(skill_dir)
    if cmd_dir.exists():
        shutil.rmtree(cmd_dir)
    cmd_dir.mkdir(parents=True, exist_ok=True)
    (cmd_dir / "SKILL.md").write_text(render_command(skill_dir), encoding="utf-8", newline="\n")

    print(f"[OK] Installed Codex skill & $chiaki command (v{VERSION}) -> {base}")
    print(f"     Command: $chiaki ({cmd_dir / 'SKILL.md'})")
    print(f"     Skill:   {skill_dir / 'SKILL.md'}")


def install_claude(dest_override: str | None, dry: bool):
    base = Path(dest_override).resolve() if dest_override else (Path.home() / ".claude").resolve()
    skill_dir = base / "skills" / SKILL_SLUG
    cmd_file = base / "commands" / "chiaki.md"

    if dry:
        print(f"[DRY RUN] Claude Code -> {base}")
        print(f"  - Command /chiaki: {cmd_file}")
        print(f"  - Core skill:      {skill_dir / 'SKILL.md'}")
        return

    copy_skill_payload(skill_dir)
    cmd_file.parent.mkdir(parents=True, exist_ok=True)
    cmd_file.write_text(render_command(skill_dir, for_claude_cmd=True), encoding="utf-8", newline="\n")

    print(f"[OK] Installed Claude Code skill & /chiaki command (v{VERSION}) -> {base}")
    print(f"     Command: /chiaki ({cmd_file})")
    print(f"     Skill:   {skill_dir / 'SKILL.md'}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-platform installer for Chiaki's-video-skill")
    ap.add_argument(
        "--target",
        choices=("antigravity", "codex", "claude", "all"),
        default="antigravity",
        help="Target platform (default: antigravity)",
    )
    ap.add_argument("--dest", default="", help="Optional custom destination directory (single target only)")
    ap.add_argument("--dry-run", action="store_true", help="Preview planned paths without writing files")
    ap.add_argument("--skip-doctor", action="store_true", help="Skip automatic post-install dependency check")
    args = ap.parse_args()

    dest = args.dest or None
    if args.target == "all":
        install_antigravity(None, args.dry_run)
        install_codex(None, args.dry_run)
        install_claude(None, args.dry_run)
    elif args.target == "antigravity":
        install_antigravity(dest, args.dry_run)
    elif args.target == "codex":
        install_codex(dest, args.dry_run)
    elif args.target == "claude":
        install_claude(dest, args.dry_run)

    if not args.dry_run and not args.skip_doctor:
        import subprocess
        print("\n=== Post-Install Dependency Check (read-only) ===")
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / "doctor.py")])
        if r.returncode != 0:
            print('\nTip: inside Antigravity / Claude Code / Codex, type `/chiaki 检查依赖` (or `$chiaki 检查依赖`) for the guided setup wizard!')
    return 0


if __name__ == "__main__":
    sys.exit(main())
