"""chiaki_guard.py — portable PreToolUse studio guardrail for Chiaki's-video-skill.

Enforces two high-value invariants at runtime (stdin JSON -> exit 0 allow / exit 2 block with reason):
  1. Scoped `chiaki-*` subagent calls must carry verbatim persona injection (`你的身份：` or `你是「...」：`),
     temperament (`性格：`), explicit craft/brief reference, pinned `Model` (pro/flash/flash_lite), and must
     not route review/verify/QC/score tasks to writable `chiaki-builder`.
  2. Headless-Chrome CLI scripts (`snap.mjs`, `snap_clean.mjs`, `render_fast.mjs`, `qa.mjs`,
     `motion_lint.mjs --curves`) must run through `scripts/run_queue.py web`.

Run self-test:
  python -X utf8 hooks/chiaki_guard.py --self-test
"""
from __future__ import annotations

import json
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VALID_MODELS = {"pro", "flash", "flash_lite"}
CHIAKI_TYPES = {"chiaki-writer", "chiaki-builder", "chiaki-reviewer"}
REVIEW_ROLE_RE = re.compile(r"(审片|复核|质检|评分|打分|看样|review|verify|verifier|qc|score|scorer|dailies)", re.I)
PERSONA_RE = re.compile(r"(你的身份[:：]|你是「[^」]+」[:：]|你是工作室的)")
TEMPERAMENT_RE = re.compile(r"性格[:：]")
CRAFT_OR_BRIEF_RE = re.compile(r"(crafts\.md|house-style\.md|quality-bar\.md|motion-library\.md|brief|REVIEW_BRIEF|SCORE_BRIEF|pitch|storyboard)", re.I)
BROWSER_CLI_RE = re.compile(r"\b(snap|snap_clean|render_fast|qa)\.mjs\b", re.I)
LINT_CURVES_RE = re.compile(r"\bmotion_lint\.mjs\b.*--curves\b", re.I)
QUEUE_RE = re.compile(r"\brun_queue\.py\b", re.I)


def evaluate(payload: dict) -> tuple[bool, str]:
    tool = str(payload.get("tool_name") or payload.get("tool") or "").strip()
    inp = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(inp, dict):
        return True, ""

    if tool == "invoke_subagent":
        tname = str(inp.get("TypeName") or inp.get("type_name") or "").strip()
        if tname not in CHIAKI_TYPES:
            return True, ""
        role = str(inp.get("Role") or inp.get("role") or "")
        prompt = str(inp.get("Prompt") or inp.get("prompt") or "")
        model = str(inp.get("Model") or inp.get("model") or "").strip()

        if tname == "chiaki-builder" and REVIEW_ROLE_RE.search(role):
            return False, (
                f"[chiaki_guard] Blocked: role '{role}' is a review/QC/scoring role and MUST use "
                "physically read-only `chiaki-reviewer`, never writable `chiaki-builder`."
            )
        if model not in VALID_MODELS:
            return False, (
                f"[chiaki_guard] Blocked: `{tname}` call missing explicit pinned Model "
                f"(got {model!r}; expected one of {sorted(VALID_MODELS)} per references/production.md §6)."
            )
        if not (PERSONA_RE.search(prompt) and TEMPERAMENT_RE.search(prompt)):
            return False, (
                f"[chiaki_guard] Blocked: `{tname}` prompt missing verbatim persona & temperament injection "
                "(`你的身份：...性格：...` or `你是「...」：...性格：...` from references/personas.md)."
            )
        if not CRAFT_OR_BRIEF_RE.search(prompt):
            return False, (
                f"[chiaki_guard] Blocked: `{tname}` prompt missing craft card / brief reference "
                "(attach references/crafts.md + brief/REVIEW_BRIEF/SCORE_BRIEF)."
            )
        return True, ""

    if tool == "run_command":
        cmd = str(inp.get("CommandLine") or inp.get("command") or "")
        if not cmd:
            return True, ""
        needs_queue = bool(BROWSER_CLI_RE.search(cmd) or LINT_CURVES_RE.search(cmd))
        if needs_queue and not QUEUE_RE.search(cmd):
            return False, (
                "[chiaki_guard] Blocked: headless-Chrome CLI (`snap.mjs`, `snap_clean.mjs`, `render_fast.mjs`, "
                "`qa.mjs`, or `motion_lint.mjs --curves`) MUST run through `scripts/run_queue.py web`."
            )
        return True, ""

    return True, ""


def self_test() -> int:
    cases = [
        ("allow non-chiaki subagent", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "research", "Prompt": "hi"}}, True),
        ("block missing model", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-builder", "Role": "Edit", "Prompt": "你的身份：x。性格：y。读 crafts.md"}}, False),
        ("block inherit model", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-builder", "Model": "inherit", "Role": "Edit", "Prompt": "你的身份：x。性格：y。读 crafts.md"}}, False),
        ("block naked prompt", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-builder", "Model": "pro", "Role": "Edit", "Prompt": "fix seg.js reading crafts.md"}}, False),
        ("block missing craft", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-builder", "Model": "pro", "Role": "Edit", "Prompt": "你的身份：x。性格：y。"}}, False),
        ("block builder doing review", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-builder", "Model": "pro", "Role": "终审技术审片员", "Prompt": "你的身份：x。性格：y。读 crafts.md"}}, False),
        ("allow valid builder", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-builder", "Model": "pro", "Role": "Act1 剪辑合成师", "Prompt": "你的身份：工作室的2D动效剪辑合成师。性格：对画面有洁癖。先读 crafts.md 与 brief_a.md"}}, True),
        ("allow valid writer", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-writer", "Model": "pro", "Role": "媒介设计师", "Prompt": "你是「媒介设计师」：专门把片子放进一种媒介。性格：执着纯粹。先读 house-style.md"}}, True),
        ("allow valid reviewer", {"tool_name": "invoke_subagent", "tool_input": {"TypeName": "chiaki-reviewer", "Model": "pro", "Role": "独立成片评分员", "Prompt": "你的身份：资深动态设计评委。性格：下手要狠。读 SCORE_BRIEF.md"}}, True),
        ("block unqueued snap", {"tool_name": "run_command", "tool_input": {"CommandLine": "node scripts/snap.mjs web/index.html out 0-10"}}, False),
        ("block unqueued curves", {"tool_name": "run_command", "tool_input": {"CommandLine": "node scripts/motion_lint.mjs web/index.html --curves"}}, False),
        ("allow static lint", {"tool_name": "run_command", "tool_input": {"CommandLine": "node scripts/motion_lint.mjs web/index.html"}}, True),
        ("allow queued snap", {"tool_name": "run_command", "tool_input": {"CommandLine": "python -X utf8 scripts/run_queue.py web --lane a -- node scripts/snap.mjs web/index.html out 0-10"}}, True),
    ]
    failed = 0
    for name, payload, want in cases:
        ok, msg = evaluate(payload)
        if ok != want:
            failed += 1
            print(f"FAIL {name}: got ok={ok} (want {want}) {msg}")
        else:
            print(f"OK   {name}")
    print(f"\n{len(cases) - failed}/{len(cases)} self-tests passed")
    return 1 if failed else 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        return self_test()
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except Exception:
        return 0
    ok, msg = evaluate(payload)
    if not ok:
        sys.stderr.write(msg + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
