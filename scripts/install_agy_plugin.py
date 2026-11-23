"""install_agy_plugin.py — install Chiaki's-video-skill cleanly as a native Antigravity plugin.

Why a small installer?
- Claude Code / Codex expect `SKILL.md` at the repo root.
- Antigravity plugins expect:
    <plugin>/plugin.json
    <plugin>/skills/chiakis-video-skill/SKILL.md (+ references/, scripts/, assets/)
    <plugin>/rules/AGENTS.md
    <plugin>/agents/chiaki-*.md
    <plugin>/hooks.json  (top-level named hook + absolute path to hooks/chiaki_guard.py)

Usage:
  python -X utf8 scripts/install_agy_plugin.py                    # installs to ~/.gemini/config/plugins/chiakis-video-skill
  python -X utf8 scripts/install_agy_plugin.py --dest <dir>       # custom plugin directory
  python -X utf8 scripts/install_agy_plugin.py --dry-run          # preview actions without writing files
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Install Chiaki's-video-skill as a native Antigravity plugin")
    ap.add_argument(
        "--dest",
        default=os.path.join(os.path.expanduser("~"), ".gemini", "config", "plugins", SKILL_SLUG),
        help="Target plugin directory (default: ~/.gemini/config/plugins/chiakis-video-skill)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Show planned layout without modifying disk")
    args = ap.parse_args()

    dest = Path(args.dest).resolve()
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
        "displayName": "Chiaki's-video-skill (2D Motion Video Studio)",
        "version": "1.2.0",
        "description": "Deterministic HTML/JS/Canvas 2D motion graphics, fast-cut PV/MV, kinetic typography, and 2.5D relief studio plugin (/chiaki).",
        "license": "MIT",
    }

    if args.dry_run:
        print(f"[DRY RUN] Would install Antigravity plugin into: {dest}")
        print(f"  - {dest / 'plugin.json'}")
        print(f"  - {dest / 'hooks.json'}  (command: {hook_cmd})")
        print(f"  - {hook_script}")
        print(f"  - {dest / 'rules' / 'AGENTS.md'}")
        print(f"  - {dest / 'agents' / 'chiaki-*.md'}")
        print(f"  - {dest / 'assets' / 'logo.svg'}")
        print(f"  - {cmd_dir / 'SKILL.md'}  (/chiaki unified slash command)")
        print(f"  - {skill_dir / 'SKILL.md'} (+ references/, scripts/, assets/)")
        return 0

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir(parents=True, exist_ok=True)
    cmd_dir.mkdir(parents=True, exist_ok=True)

    # 1. Manifest + hooks + rules + agents + plugin logo
    (dest / "plugin.json").write_text(json.dumps(plugin_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "hooks.json").write_text(json.dumps(hooks_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    copy_tree(ROOT / "hooks", dest / "hooks")
    copy_tree(ROOT / "rules", dest / "rules")
    copy_tree(ROOT / "agents", dest / "agents")
    if (ROOT / "assets" / "logo.svg").exists():
        (dest / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "assets" / "logo.svg", dest / "assets" / "logo.svg")

    # 2. Unified /chiaki command skill with resolved absolute <SKILL_DIR>
    cmd_src = ROOT / "commands" / "chiaki" / "SKILL.md"
    if cmd_src.exists():
        cmd_txt = cmd_src.read_text(encoding="utf-8").replace("<SKILL_DIR>", skill_dir.as_posix())
        (cmd_dir / "SKILL.md").write_text(cmd_txt, encoding="utf-8", newline="\n")

    # 3. Core skill payload under skills/chiakis-video-skill/
    for fname in ("SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "requirements.txt"):
        if (ROOT / fname).exists():
            shutil.copy2(ROOT / fname, skill_dir / fname)
    for sub in ("references", "scripts", "assets"):
        copy_tree(ROOT / sub, skill_dir / sub)

    print(f"Installed Antigravity plugin cleanly -> {dest}")
    print(f"  Command: /chiaki ({cmd_dir / 'SKILL.md'})")
    print(f"  Skill:   {skill_dir / 'SKILL.md'}")
    print(f"  Hook:    {dest / 'hooks.json'}")
    print("Restart or reload plugins in Antigravity Customizations to activate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
