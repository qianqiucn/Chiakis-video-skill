"""install_agy_plugin.py — Antigravity plugin installer wrapper (delegates to scripts/install.py).

Usage:
  python -X utf8 scripts/install_agy_plugin.py                    # installs to ~/.gemini/config/plugins/chiakis-video-skill
  python -X utf8 scripts/install_agy_plugin.py --dest <dir>       # custom plugin directory
  python -X utf8 scripts/install_agy_plugin.py --dry-run          # preview actions without writing files
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install as _inst


def main() -> int:
    ap = argparse.ArgumentParser(description="Install Chiaki's-video-skill as a native Antigravity plugin")
    ap.add_argument("--dest", default="", help="Target plugin directory (default: ~/.gemini/config/plugins/chiakis-video-skill)")
    ap.add_argument("--dry-run", action="store_true", help="Show planned layout without modifying disk")
    args = ap.parse_args()
    _inst.install_antigravity(args.dest or None, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
