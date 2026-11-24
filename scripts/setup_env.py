"""setup_env.py — user-approved dependency & path configurator for Chiaki's-video-skill.

Called by the agent AFTER running `scripts/doctor.py` and asking the user:
  1. Which profile they want:
       - `2d`   : core 2D motion, bundled fonts, mgaudio & MP4 render (`requirements.txt`, ~180 MB)
       - `3d`   : `2d` + Blender path (`CHIAKI_BLENDER`), 3D asset cache (`CHIAKI_ASSETS3D`), optional Blender MCP bridge wiring
       - `full` : `3d` + PyTorch/Vision stack for `vision/cutout.py`, `vision/part_cutout.py` & `vision/depth.py` (+1.5-3 GB)
  2. Where they want virtual environments / caches installed (so nothing fills up C: uninvited).

Never modifies the machine unless executed with explicit user-chosen flags; supports `--dry-run`.

Examples:
  python -X utf8 scripts/setup_env.py --profile 2d --venv "D:/AI/chiaki-venv" --dry-run
  python -X utf8 scripts/setup_env.py --profile 3d --venv "D:/AI/chiaki-venv" --blender "D:/Apps/Blender/blender.exe" --assets3d "D:/Assets/3d" --wire-mcp antigravity
  python -X utf8 scripts/setup_env.py --profile full --current-python --wire-mcp codex
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent


def set_user_env(key: str, val: str, dry: bool):
    if not val:
        return
    if dry:
        print(f"[DRY RUN] Would set user env {key}={val}")
        return
    os.environ[key] = val
    if sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, key, 0, winreg.REG_SZ, val)
        print(f"[OK] Persisted Windows user env: {key}={val}")
    else:
        print(f"[INFO] Add to your ~/.zshrc or ~/.bashrc:\n  export {key}=\"{val}\"")


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def wire_mcp(target: str, py_exe: str, bridge_path: Path, dry: bool):
    if target == "none":
        return
    bridge_posix = bridge_path.resolve().as_posix()
    if target == "antigravity":
        cfg = Path.home() / ".gemini" / "config" / "mcp_config.json"
        if dry:
            print(f"[DRY RUN] Would merge `blender` MCP into {cfg} -> {py_exe} -X utf8 {bridge_posix}")
            return
        cfg.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if cfg.exists() and cfg.read_text(encoding="utf-8").strip():
            data = json.loads(cfg.read_text(encoding="utf-8"))
        servers = data.setdefault("mcpServers", {})
        servers["blender"] = {"command": py_exe, "args": ["-X", "utf8", bridge_posix]}
        cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] Wired Antigravity Blender MCP -> {cfg}")
    elif target == "codex":
        cfg = Path.home() / ".codex" / "config.toml"
        if dry:
            print(f"[DRY RUN] Would add [mcp_servers.blender] to {cfg} -> {py_exe} -X utf8 {bridge_posix}")
            return
        cfg.parent.mkdir(parents=True, exist_ok=True)
        txt = cfg.read_text(encoding="utf-8") if cfg.exists() else ""
        block = (
            "\n[mcp_servers.blender]\n"
            f"command = '{py_exe}'\n"
            f'args = ["-X", "utf8", "{bridge_posix}"]\n'
        )
        if re.search(r"(?m)^\[mcp_servers\.blender\]\s*$", txt):
            txt = re.sub(r"(?ms)^\[mcp_servers\.blender\]\s*\n.*?(?=^\[|\Z)", block.lstrip("\n") + "\n", txt)
        else:
            txt = txt.rstrip() + "\n" + block
        cfg.write_text(txt, encoding="utf-8")
        print(f"[OK] Wired Codex Blender MCP -> {cfg}")
    elif target == "claude":
        cmd = ["claude", "mcp", "add", "blender", "--", py_exe, "-X", "utf8", bridge_posix]
        if dry:
            print("[DRY RUN] Would run:", " ".join(cmd))
            return
        r = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            print("[OK] Wired Claude Code Blender MCP via `claude mcp add`")
        else:
            print("[WARN] `claude` CLI returned non-zero; run manually:", " ".join(cmd))


def main() -> int:
    ap = argparse.ArgumentParser(description="Configure Python venv, dependencies, paths, and Blender MCP for Chiaki's-video-skill")
    ap.add_argument("--profile", choices=("2d", "3d", "full"), required=True, help="Capability tier chosen by the user")
    ap.add_argument("--venv", default="", help="Directory to create/use a Python virtual environment (e.g. D:/AI/chiaki-venv)")
    ap.add_argument("--current-python", action="store_true", help="Install into the current Python interpreter instead of a new venv")
    ap.add_argument("--skip-pip", action="store_true", help="Skip pip install (only configure paths / MCP)")
    ap.add_argument("--blender", default="", help="Path to blender executable to save in CHIAKI_BLENDER")
    ap.add_argument("--assets3d", default="", help="Custom folder for free 3D asset cache (CHIAKI_ASSETS3D)")
    ap.add_argument("--fonts-dir", default="", help="Custom folder for shared font library (CHIAKI_FONTS)")
    ap.add_argument("--memory-dir", default="", help="Custom folder for studio self-iteration memory (CHIAKI_MEMORY_DIR)")
    ap.add_argument("--memory-mode", choices=("", "ask", "auto", "readonly", "off"), default="", help="Initial studio memory switch mode")
    ap.add_argument("--wire-mcp", choices=("none", "antigravity", "codex", "claude"), default="none", help="Safely wire built-in zero-dependency Blender MCP bridge")
    ap.add_argument("--dry-run", action="store_true", help="Print planned actions without installing or editing files")
    args = ap.parse_args()

    if not args.skip_pip and not args.venv and not args.current_python:
        sys.exit("Specify either --venv <path> (recommended) or --current-python (or --skip-pip).")

    target_py = sys.executable
    if args.venv:
        vdir = Path(args.venv).resolve()
        vpy = venv_python(vdir)
        if not vpy.exists():
            if args.dry_run:
                print(f"[DRY RUN] Would create Python venv -> {vdir}")
            else:
                vdir.parent.mkdir(parents=True, exist_ok=True)
                subprocess.check_call([sys.executable, "-m", "venv", str(vdir)])
                print(f"[OK] Created venv -> {vdir}")
        target_py = str(vpy)

    if not args.skip_pip:
        req = ROOT / "requirements.txt"
        cmd_core = [target_py, "-m", "pip", "install", "-r", str(req)]
        if args.dry_run:
            print("[DRY RUN] Would run:", " ".join(cmd_core))
        else:
            subprocess.check_call(cmd_core)
        if args.profile == "full":
            cmd_depth = [target_py, "-m", "pip", "install", "torch", "torchvision", "transformers<5", "timm", "einops", "kornia", "huggingface_hub"]
            if args.dry_run:
                print("[DRY RUN] Would run:", " ".join(cmd_depth))
            else:
                subprocess.check_call(cmd_depth)

    if args.blender:
        set_user_env("CHIAKI_BLENDER", str(Path(args.blender).resolve()), args.dry_run)
    if args.assets3d:
        p = Path(args.assets3d).resolve()
        if not args.dry_run:
            p.mkdir(parents=True, exist_ok=True)
        set_user_env("CHIAKI_ASSETS3D", str(p), args.dry_run)
    if args.fonts_dir:
        p = Path(args.fonts_dir).resolve()
        if not args.dry_run:
            p.mkdir(parents=True, exist_ok=True)
        set_user_env("CHIAKI_FONTS", str(p), args.dry_run)
    if args.memory_dir:
        p = Path(args.memory_dir).resolve()
        if not args.dry_run:
            p.mkdir(parents=True, exist_ok=True)
        set_user_env("CHIAKI_MEMORY_DIR", str(p), args.dry_run)
    if args.memory_mode:
        cmd_mem = [target_py, "-X", "utf8", str(ROOT / "scripts" / "memory.py"), "mode", args.memory_mode]
        if args.memory_dir:
            cmd_mem += ["--dir", str(Path(args.memory_dir).resolve())]
        if args.dry_run:
            print("[DRY RUN] Would run:", " ".join(cmd_mem))
        else:
            subprocess.check_call(cmd_mem)

    bridge = ROOT / "scripts" / "blender" / "mcp_bridge.py"
    if args.wire_mcp != "none":
        wire_mcp(args.wire_mcp, target_py, bridge, args.dry_run)

    if not args.dry_run:
        print("\n=== Re-running doctor.py with configured Python ===")
        subprocess.run([target_py, "-X", "utf8", str(ROOT / "scripts" / "doctor.py")])
    return 0


if __name__ == "__main__":
    sys.exit(main())
