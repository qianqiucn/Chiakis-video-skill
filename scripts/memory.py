"""memory.py — opt-in, self-iterating studio memory for Chiaki's-video-skill.

Stores lightweight, human-readable studio memory OUTSIDE the skill repository so
upgrading or git-pulling the skill never wipes user preferences, and git status
stays 100% clean with zero privacy leaks. Shared seamlessly across Antigravity,
Claude Code, and Codex.

Default directory: ~/.chiaki-studio/  (override via CHIAKI_MEMORY_DIR or --dir)

Files managed in the memory directory:
  config.json       Switch mode (`ask` | `auto` | `readonly` | `off`) & caps
  preferences.json  Durable user tastes & defaults (capped at 25; mirrored to preferences.md)
  mistakes.json     Actionable [trigger -> mistake -> rule] guardrails (capped at 30; mirrored to mistakes.md)
  film_log.jsonl    Compact 1-line-per-film history for cross-film style/font anti-repetition

Modes (self-iteration switch):
  ask       (default) Read memory at Brief/Pitch/Craft/Review; at Gate B2 emit a concise
            <=5-line candidate card and write only after `--confirm`.
  auto      Read memory and automatically distill/write on Gate B2 delivery.
  readonly  Read preferences/mistakes for this film, but never write back (ideal for client/one-off gigs).
  off       Completely disabled (neither read nor write).

Usage:
  python -X utf8 scripts/memory.py status [--dir PATH] [--json]
  python -X utf8 scripts/memory.py mode <ask|auto|readonly|off> [--dir PATH]
  python -X utf8 scripts/memory.py show [--dir PATH] [--limit 10]
  python -X utf8 scripts/memory.py context --stage <brief|pitch|craft|review|all> [--mode-override M] [--out FILE]
  python -X utf8 scripts/memory.py add-pref --category <aesthetic|audio|motion|delivery|avoid> --text "..."
  python -X utf8 scripts/memory.py add-mistake --trigger "..." --mistake "..." --rule "..." [--category general]
  python -X utf8 scripts/memory.py log-film --title "..." --type "..." [--styles a,b] [--fonts x,y] [--palette #111,#fff] [--scores 9,8,9,8,9,9,9] [--win "..."] [--fix "..."]
  python -X utf8 scripts/memory.py apply <proposal.json> [--confirm] [--mode-override M]
  python -X utf8 scripts/memory.py forget <ID>
  python -X utf8 scripts/memory.py reset --yes
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VALID_MODES = ("ask", "auto", "readonly", "off")
PREF_CATEGORIES = ("aesthetic", "audio", "motion", "delivery", "avoid")
MISTAKE_CATEGORIES = ("general", "motion", "vision", "audio", "type", "3d", "sync", "render")

DEFAULT_CONFIG = {
    "mode": "ask",
    "max_preferences": 25,
    "max_mistakes": 30,
    "skill_upgrade_hit_threshold": 2,
}

MAX_CONTEXT_CHARS = 1800


def today_str() -> str:
    return dt.date.today().isoformat()


def resolve_dir(cli_dir: str = "") -> Path:
    if cli_dir:
        return Path(cli_dir).expanduser().resolve()
    env = os.environ.get("CHIAKI_MEMORY_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".chiaki-studio").resolve()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_config(mdir: Path) -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    raw = _read_json(mdir / "config.json", {})
    if isinstance(raw, dict):
        for k in DEFAULT_CONFIG:
            if k in raw:
                cfg[k] = raw[k]
    if cfg["mode"] not in VALID_MODES:
        cfg["mode"] = "ask"
    return cfg


def load_prefs(mdir: Path) -> list[dict[str, Any]]:
    data = _read_json(mdir / "preferences.json", [])
    return data if isinstance(data, list) else []


def load_mistakes(mdir: Path) -> list[dict[str, Any]]:
    data = _read_json(mdir / "mistakes.json", [])
    return data if isinstance(data, list) else []


def load_films(mdir: Path) -> list[dict[str, Any]]:
    p = mdir / "film_log.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _sync_markdown(mdir: Path, cfg: dict[str, Any], prefs: list[dict[str, Any]], mistakes: list[dict[str, Any]]) -> None:
    mdir.mkdir(parents=True, exist_ok=True)
    p_lines = [
        "# Chiaki Studio — User Preferences",
        "<!-- Auto-synced by scripts/memory.py; manage via `memory.py add-pref` / `forget` / `mode`. -->",
        "",
    ]
    if not prefs:
        p_lines.append("_No saved preferences yet._")
    else:
        for item in prefs:
            p_lines.append(
                f"- **`{item['id']}`** `[{item['category']}]` {item['text']} "
                f"_(hits: {item.get('hits', 1)}, updated: {item.get('last_seen', '')})_"
            )
    (mdir / "preferences.md").write_text("\n".join(p_lines) + "\n", encoding="utf-8")

    thr = int(cfg.get("skill_upgrade_hit_threshold", 2))
    m_lines = [
        "# Chiaki Studio — Never-Repeat Guardrails",
        "<!-- Auto-synced by scripts/memory.py; manage via `memory.py add-mistake` / `forget`. -->",
        "",
    ]
    if not mistakes:
        m_lines.append("_No saved mistake guardrails yet._")
    else:
        for item in mistakes:
            star = " ★ SKILL-UPGRADE CANDIDATE" if int(item.get("hits", 1)) >= thr else ""
            m_lines.append(
                f"- **`{item['id']}`** `[{item.get('category', 'general')}]` "
                f"**When**: {item['trigger']} → **Avoid**: {item['mistake']} → **Rule**: {item['rule']} "
                f"_(hits: {item.get('hits', 1)}, updated: {item.get('last_seen', '')}{star})_"
            )
    (mdir / "mistakes.md").write_text("\n".join(m_lines) + "\n", encoding="utf-8")


def save_prefs(mdir: Path, cfg: dict[str, Any], prefs: list[dict[str, Any]], mistakes: list[dict[str, Any]] | None = None) -> None:
    _write_json(mdir / "preferences.json", prefs)
    _sync_markdown(mdir, cfg, prefs, load_mistakes(mdir) if mistakes is None else mistakes)


def save_mistakes(mdir: Path, cfg: dict[str, Any], mistakes: list[dict[str, Any]], prefs: list[dict[str, Any]] | None = None) -> None:
    _write_json(mdir / "mistakes.json", mistakes)
    _sync_markdown(mdir, cfg, load_prefs(mdir) if prefs is None else prefs, mistakes)


def save_films(mdir: Path, films: list[dict[str, Any]]) -> None:
    mdir.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(f, ensure_ascii=False) for f in films]
    (mdir / "film_log.jsonl").write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")


def _norm_tokens(text: str) -> set[str]:
    s = re.sub(r"[\W_]+", " ", text.lower()).strip()
    toks = set(s.split())
    # Also include 2-gram CJK shingles so Chinese strings deduplicate reliably without external tokenizers
    cjk = "".join(re.findall(r"[\u4e00-\u9fff]+", text))
    if len(cjk) >= 2:
        toks.update(cjk[i : i + 2] for i in range(len(cjk) - 1))
    elif cjk:
        toks.add(cjk)
    return toks


def _jaccard(a: str, b: str) -> float:
    sa, sb = _norm_tokens(a), _norm_tokens(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _next_id(items: list[dict[str, Any]], prefix: str, width: int = 2) -> str:
    best = 0
    pat = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    for it in items:
        m = pat.match(str(it.get("id", "")))
        if m:
            best = max(best, int(m.group(1)))
    return f"{prefix}{best + 1:0{width}d}"


def upsert_pref(mdir: Path, category: str, text: str) -> tuple[str, dict[str, Any], list[str]]:
    cfg = load_config(mdir)
    prefs = load_prefs(mdir)
    clean_text = " ".join(text.strip().split())
    if not clean_text:
        raise ValueError("preference text cannot be empty")
    cat = category if category in PREF_CATEGORIES else "aesthetic"
    evicted: list[str] = []

    for item in prefs:
        if item.get("category") == cat and _jaccard(item.get("text", ""), clean_text) >= 0.72:
            item["hits"] = int(item.get("hits", 1)) + 1
            item["last_seen"] = today_str()
            if len(clean_text) > len(item.get("text", "")):
                item["text"] = clean_text
            save_prefs(mdir, cfg, prefs)
            return "bumped", item, evicted

    entry = {
        "id": _next_id(prefs, "P", 2),
        "category": cat,
        "text": clean_text,
        "hits": 1,
        "created": today_str(),
        "last_seen": today_str(),
    }
    prefs.append(entry)
    cap = int(cfg.get("max_preferences", 25))
    while len(prefs) > cap:
        # Evict lowest-hit oldest entry (never the freshly added item)
        victim = min(prefs[:-1], key=lambda x: (int(x.get("hits", 1)), str(x.get("last_seen", ""))))
        evicted.append(victim["id"])
        prefs.remove(victim)
    save_prefs(mdir, cfg, prefs)
    return "added", entry, evicted


def upsert_mistake(mdir: Path, trigger: str, mistake: str, rule: str, category: str = "general") -> tuple[str, dict[str, Any], list[str], bool]:
    cfg = load_config(mdir)
    mistakes = load_mistakes(mdir)
    tr = " ".join(trigger.strip().split())
    mk = " ".join(mistake.strip().split())
    rl = " ".join(rule.strip().split())
    if not (tr and mk and rl):
        raise ValueError("trigger, mistake, and rule are all required")
    cat = category if category in MISTAKE_CATEGORIES else "general"
    evicted: list[str] = []
    thr = int(cfg.get("skill_upgrade_hit_threshold", 2))

    sig_new = f"{tr} {rl}"
    for item in mistakes:
        sig_old = f"{item.get('trigger', '')} {item.get('rule', '')}"
        if _jaccard(sig_old, sig_new) >= 0.68:
            item["hits"] = int(item.get("hits", 1)) + 1
            item["last_seen"] = today_str()
            if len(rl) > len(item.get("rule", "")):
                item["rule"] = rl
            save_mistakes(mdir, cfg, mistakes)
            return "bumped", item, evicted, int(item["hits"]) >= thr

    entry = {
        "id": _next_id(mistakes, "M", 2),
        "category": cat,
        "trigger": tr,
        "mistake": mk,
        "rule": rl,
        "hits": 1,
        "created": today_str(),
        "last_seen": today_str(),
    }
    mistakes.append(entry)
    cap = int(cfg.get("max_mistakes", 30))
    while len(mistakes) > cap:
        victim = min(mistakes[:-1], key=lambda x: (int(x.get("hits", 1)), str(x.get("last_seen", ""))))
        evicted.append(victim["id"])
        mistakes.remove(victim)
    save_mistakes(mdir, cfg, mistakes)
    return "added", entry, evicted, int(entry["hits"]) >= thr


def append_film(mdir: Path, film: dict[str, Any]) -> dict[str, Any]:
    films = load_films(mdir)
    entry = {
        "id": _next_id(films, "F", 3),
        "date": str(film.get("date") or today_str()),
        "title": str(film.get("title", "")).strip() or "Untitled Film",
        "type": str(film.get("type", "")).strip() or "pv",
        "styles": [s.strip() for s in (film.get("styles") or []) if str(s).strip()],
        "fonts": [s.strip() for s in (film.get("fonts") or []) if str(s).strip()],
        "palette": [s.strip() for s in (film.get("palette") or []) if str(s).strip()],
        "scores": film.get("scores") or {},
        "min_score": film.get("min_score"),
        "key_win": str(film.get("key_win", "")).strip(),
        "key_fix": str(film.get("key_fix", "")).strip(),
    }
    if entry["min_score"] is None and isinstance(entry["scores"], dict) and entry["scores"]:
        vals = [v for v in entry["scores"].values() if isinstance(v, (int, float))]
        if vals:
            entry["min_score"] = min(vals)
    films.append(entry)
    save_films(mdir, films)
    return entry


def build_context(mdir: Path, stage: str, mode_override: str = "") -> str:
    cfg = load_config(mdir)
    eff_mode = mode_override if mode_override in VALID_MODES else cfg["mode"]
    if eff_mode == "off":
        return ""

    prefs = load_prefs(mdir)
    mistakes = load_mistakes(mdir)
    films = load_films(mdir)

    sections: list[str] = []

    if stage in ("brief", "all") and prefs:
        ranked = sorted(prefs, key=lambda x: (-int(x.get("hits", 1)), str(x.get("last_seen", ""))), reverse=False)
        top = ranked[:12]
        lines = [
            "### Studio Memory — User Preferences (current project brief always overrides)",
            *[f"- [{p['category']}] {p['text']}" for p in top],
        ]
        sections.append("\n".join(lines))

    if stage in ("pitch", "all"):
        pitch_lines = []
        recent = films[-3:]
        if recent:
            pitch_lines.append("### Studio Memory — Recent Films (avoid repeating visual form & font pairings)")
            for f in reversed(recent):
                st = ", ".join(f.get("styles", [])) or "n/a"
                fn = ", ".join(f.get("fonts", [])) or "n/a"
                pal = ", ".join(f.get("palette", [])[:4])
                pal_s = f" | palette: {pal}" if pal else ""
                pitch_lines.append(f"- {f['date']} «{f['title']}» ({f['type']}): styles=[{st}] | fonts=[{fn}]{pal_s}")
        taste_prefs = [p for p in prefs if p.get("category") in ("aesthetic", "avoid", "motion")]
        if taste_prefs:
            pitch_lines.append("### Studio Memory — Aesthetic Likes & Hard Dislikes")
            for p in sorted(taste_prefs, key=lambda x: -int(x.get("hits", 1)))[:8]:
                pitch_lines.append(f"- [{p['category']}] {p['text']}")
        if pitch_lines:
            sections.append("\n".join(pitch_lines))

    if stage in ("craft", "review", "all") and mistakes:
        top_m = sorted(mistakes, key=lambda x: (-int(x.get("hits", 1)), x.get("last_seen", "")), reverse=False)[:8]
        hdr = (
            "### Studio Memory — Past Mistakes to Verify Zero Regression"
            if stage == "review"
            else "### Studio Memory — Top Craft Guardrails (never repeat)"
        )
        lines = [hdr]
        for m in top_m:
            lines.append(f"- ({m['id']}, hits={m.get('hits', 1)}) When {m['trigger']} -> {m['rule']} (avoid: {m['mistake']})")
        sections.append("\n".join(lines))

    out = "\n\n".join(sections).strip()
    if len(out) > MAX_CONTEXT_CHARS:
        out = out[: MAX_CONTEXT_CHARS - 20].rstrip() + "\n... (truncated)"
    return out


def _parse_scores(raw: str) -> dict[str, float]:
    raw = raw.strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        return json.loads(raw)
    keys = ["concept", "motion", "rhythm", "type", "depth", "sound", "tech"]
    vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
    return {keys[i]: (int(v) if v.is_integer() else v) for i, v in enumerate(vals[: len(keys)])}


def _format_proposal_card(proposal: dict[str, Any], eff_mode: str, mdir: Path) -> str:
    film = proposal.get("film") or {}
    prefs = proposal.get("preferences") or []
    mistakes = proposal.get("mistakes") or []
    lines = [f"### 本片复盘沉淀候选卡（模式: `{eff_mode}` · 存储: `{mdir}`）"]
    if film:
        st = ", ".join(film.get("styles") or []) or "-"
        fn = ", ".join(film.get("fonts") or []) or "-"
        lines.append(f"1. **作品履历**：《{film.get('title', 'Untitled')}》（{film.get('type', 'pv')}）· 风格 `{st}` · 字体 `{fn}`")
    if prefs:
        p_txt = "；".join(f"[{p.get('category', 'aesthetic')}] {p.get('text', '')}" for p in prefs[:3])
        lines.append(f"2. **拟记住的新偏好（{len(prefs)} 条）**：{p_txt}")
    if mistakes:
        m_txt = "；".join(f"{m.get('trigger', '')} → {m.get('rule', '')}" for m in mistakes[:3])
        lines.append(f"3. **拟沉淀的新避坑（{len(mistakes)} 条）**：{m_txt}")
    if not (film or prefs or mistakes):
        lines.append("- 本片无新增待沉淀条目。")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Self-iterating studio memory manager for Chiaki's-video-skill")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_dir(p):
        p.add_argument("--dir", default="", help="Override memory directory (default ~/.chiaki-studio or $CHIAKI_MEMORY_DIR)")

    p_st = sub.add_parser("status", help="Show switch mode, directory, and entry counts")
    add_dir(p_st)
    p_st.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    p_md = sub.add_parser("mode", help="Set self-iteration switch mode (ask | auto | readonly | off)")
    p_md.add_argument("value", choices=VALID_MODES)
    add_dir(p_md)

    p_sh = sub.add_parser("show", help="Display saved preferences, mistakes, and recent films")
    add_dir(p_sh)
    p_sh.add_argument("--limit", type=int, default=10, help="Max recent films to display")

    p_cx = sub.add_parser("context", help="Emit compact stage-specific memory slice for prompt injection")
    p_cx.add_argument("--stage", choices=("brief", "pitch", "craft", "review", "all"), required=True)
    p_cx.add_argument("--mode-override", default="", choices=("",) + VALID_MODES)
    p_cx.add_argument("--out", default="", help="Optional output file path")
    add_dir(p_cx)

    p_ap = sub.add_parser("add-pref", help="Record or bump a durable user preference")
    p_ap.add_argument("--category", choices=PREF_CATEGORIES, default="aesthetic")
    p_ap.add_argument("--text", required=True)
    add_dir(p_ap)

    p_am = sub.add_parser("add-mistake", help="Record or bump an actionable [trigger -> mistake -> rule] guardrail")
    p_am.add_argument("--trigger", required=True)
    p_am.add_argument("--mistake", required=True)
    p_am.add_argument("--rule", required=True)
    p_am.add_argument("--category", choices=MISTAKE_CATEGORIES, default="general")
    add_dir(p_am)

    p_lf = sub.add_parser("log-film", help="Append a delivered film summary to film_log.jsonl")
    p_lf.add_argument("--title", required=True)
    p_lf.add_argument("--type", default="pv")
    p_lf.add_argument("--styles", default="", help="Comma-separated style forms used")
    p_lf.add_argument("--fonts", default="", help="Comma-separated font families used")
    p_lf.add_argument("--palette", default="", help="Comma-separated hex tokens")
    p_lf.add_argument("--scores", default="", help="7 comma-separated scores (concept..tech) or JSON object")
    p_lf.add_argument("--win", default="", help="Strongest highlight of the film")
    p_lf.add_argument("--fix", default="", help="Key fix made during polish")
    add_dir(p_lf)

    p_ay = sub.add_parser("apply", help="Apply a Stage-13 Gate B2 memory proposal JSON (respects switch mode)")
    p_ay.add_argument("proposal", help="Path to proposal JSON ({film, preferences, mistakes})")
    p_ay.add_argument("--confirm", action="store_true", help="Explicit user confirmation (required in `ask` mode)")
    p_ay.add_argument("--mode-override", default="", choices=("",) + VALID_MODES)
    add_dir(p_ay)

    p_dc = sub.add_parser("draft-card", help="Render the mandatory Stage-13 Gate B2 post-delivery preference ask & candidate memory card")
    p_dc.add_argument("--proposal", default="", help="Optional path to work/memory_proposal.json")
    p_dc.add_argument("--title", default="", help="Optional delivered film title")
    p_dc.add_argument("--mode-override", default="", choices=("",) + VALID_MODES)
    add_dir(p_dc)

    p_fg = sub.add_parser("forget", help="Delete one entry by ID (e.g. P02, M04, F001)")
    p_fg.add_argument("entry_id")
    add_dir(p_fg)

    p_rs = sub.add_parser("reset", help="Clear all studio memory entries (keeps config mode)")
    p_rs.add_argument("--yes", action="store_true", required=True, help="Confirm permanent reset")
    add_dir(p_rs)

    args = ap.parse_args()
    mdir = resolve_dir(args.dir)

    if args.cmd == "status":
        cfg = load_config(mdir)
        prefs = load_prefs(mdir)
        mistakes = load_mistakes(mdir)
        films = load_films(mdir)
        thr = int(cfg.get("skill_upgrade_hit_threshold", 2))
        upgrades = [m["id"] for m in mistakes if int(m.get("hits", 1)) >= thr]
        payload = {
            "dir": str(mdir),
            "initialized": mdir.exists(),
            "mode": cfg["mode"],
            "preferences": len(prefs),
            "max_preferences": cfg["max_preferences"],
            "mistakes": len(mistakes),
            "max_mistakes": cfg["max_mistakes"],
            "films": len(films),
            "skill_upgrade_candidates": upgrades,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(
                f"Studio Memory [{cfg['mode']}] @ {mdir}\n"
                f"  preferences: {len(prefs)}/{cfg['max_preferences']} | "
                f"mistakes: {len(mistakes)}/{cfg['max_mistakes']} | films: {len(films)}"
            )
            if upgrades:
                print(f"  ★ Skill-upgrade candidates (hits >= {thr}): {', '.join(upgrades)}")
        return 0

    if args.cmd == "mode":
        cfg = load_config(mdir)
        cfg["mode"] = args.value
        _write_json(mdir / "config.json", cfg)
        _sync_markdown(mdir, cfg, load_prefs(mdir), load_mistakes(mdir))
        print(f"[OK] Studio memory mode -> {args.value} ({mdir})")
        return 0

    if args.cmd == "show":
        cfg = load_config(mdir)
        prefs = load_prefs(mdir)
        mistakes = load_mistakes(mdir)
        films = load_films(mdir)
        thr = int(cfg.get("skill_upgrade_hit_threshold", 2))
        print(f"=== Chiaki Studio Memory ({cfg['mode']}) @ {mdir} ===")
        print(f"\n[Preferences: {len(prefs)}/{cfg['max_preferences']}]")
        for p in prefs:
            print(f"  {p['id']} [{p['category']}] {p['text']} (hits={p.get('hits', 1)}, {p.get('last_seen', '')})")
        print(f"\n[Mistake Guardrails: {len(mistakes)}/{cfg['max_mistakes']}]")
        for m in mistakes:
            star = " ★ SKILL-UPGRADE CANDIDATE" if int(m.get("hits", 1)) >= thr else ""
            print(f"  {m['id']} [{m.get('category', 'general')}] {m['trigger']} -> {m['rule']} (avoid: {m['mistake']}; hits={m.get('hits', 1)}{star})")
        print(f"\n[Recent Films: {len(films)} total]")
        for f in films[-args.limit :]:
            st = ", ".join(f.get("styles", []))
            fn = ", ".join(f.get("fonts", []))
            print(f"  {f['id']} {f['date']} «{f['title']}» ({f['type']}) styles=[{st}] fonts=[{fn}] min_score={f.get('min_score')}")
        return 0

    if args.cmd == "context":
        txt = build_context(mdir, args.stage, args.mode_override)
        if args.out:
            op = Path(args.out)
            op.parent.mkdir(parents=True, exist_ok=True)
            op.write_text(txt + ("\n" if txt else ""), encoding="utf-8")
        elif txt:
            print(txt)
        return 0

    if args.cmd == "add-pref":
        action, item, evicted = upsert_pref(mdir, args.category, args.text)
        ev = f" (evicted: {', '.join(evicted)})" if evicted else ""
        print(f"[OK] {action} preference {item['id']} [{item['category']}] (hits={item['hits']}){ev}")
        return 0

    if args.cmd == "add-mistake":
        action, item, evicted, upgrade = upsert_mistake(mdir, args.trigger, args.mistake, args.rule, args.category)
        ev = f" (evicted: {', '.join(evicted)})" if evicted else ""
        up = " ★ SKILL-UPGRADE CANDIDATE (consider promoting to skill rules/scripts)" if upgrade else ""
        print(f"[OK] {action} mistake {item['id']} [{item['category']}] (hits={item['hits']}){ev}{up}")
        return 0

    if args.cmd == "log-film":
        film = {
            "title": args.title,
            "type": args.type,
            "styles": [x for x in args.styles.split(",") if x.strip()],
            "fonts": [x for x in args.fonts.split(",") if x.strip()],
            "palette": [x for x in args.palette.split(",") if x.strip()],
            "scores": _parse_scores(args.scores),
            "key_win": args.win,
            "key_fix": args.fix,
        }
        entry = append_film(mdir, film)
        print(f"[OK] logged film {entry['id']} «{entry['title']}» (min_score={entry.get('min_score')})")
        return 0

    if args.cmd == "apply":
        cfg = load_config(mdir)
        eff_mode = args.mode_override if args.mode_override in VALID_MODES else cfg["mode"]
        prop_p = Path(args.proposal)
        if not prop_p.exists():
            sys.exit(f"Proposal file not found: {prop_p}")
        proposal = json.loads(prop_p.read_text(encoding="utf-8"))

        if eff_mode in ("off", "readonly"):
            print(f"[SKIP] Studio memory mode is `{eff_mode}` — not writing proposal to {mdir}.")
            return 0

        if eff_mode == "ask" and not args.confirm:
            print(_format_proposal_card(proposal, eff_mode, mdir))
            print(f"\n[PENDING CONFIRMATION] Re-run with `--confirm` after user approval to write into {mdir}.")
            return 0

        # Ensure config exists
        if not (mdir / "config.json").exists():
            _write_json(mdir / "config.json", cfg)

        written: list[str] = []
        upgrade_alerts: list[str] = []
        if proposal.get("film"):
            f_entry = append_film(mdir, proposal["film"])
            written.append(f"film:{f_entry['id']}")
        for p in proposal.get("preferences") or []:
            act, item, _ = upsert_pref(mdir, p.get("category", "aesthetic"), p.get("text", ""))
            written.append(f"pref:{item['id']}({act})")
        for m in proposal.get("mistakes") or []:
            act, item, _, up = upsert_mistake(
                mdir, m.get("trigger", ""), m.get("mistake", ""), m.get("rule", ""), m.get("category", "general")
            )
            written.append(f"mistake:{item['id']}({act})")
            if up:
                upgrade_alerts.append(f"{item['id']} (hits={item['hits']}): {item['trigger']} -> {item['rule']}")

        print(f"[OK] Applied studio memory proposal ({eff_mode}) -> {', '.join(written) or 'no entries'}")
        for al in upgrade_alerts:
            print(f"  ★ SKILL-UPGRADE CANDIDATE: {al}")
        return 0

    if args.cmd == "draft-card":
        cfg = load_config(mdir)
        eff_mode = args.mode_override if args.mode_override in VALID_MODES else cfg["mode"]
        if eff_mode in ("off", "readonly"):
            print(f"[SKIP] Studio memory mode is `{eff_mode}` — omit post-delivery preference prompt.")
            return 0
        proposal: dict[str, Any] = {}
        if args.proposal:
            pp = Path(args.proposal)
            if pp.exists():
                proposal = json.loads(pp.read_text(encoding="utf-8"))
        title = args.title or (proposal.get("film") or {}).get("title") or "本片"
        lines = [
            "---",
            "### 🧠 下支片想怎么更合你胃口？（可选，10 秒回复即可）",
            "",
            f"《{title}》已完片交付！可以把你的长期偏好记进本地工作室记忆（`{mdir}`，当前模式 `{eff_mode}`，升级 Skill 永不丢失），下支片会越做越懂你：",
            "1. **这次最戳你的地方**？（画风 / 字体 / 节奏 / Three.js 或 Blender 3D 技巧）",
            "2. **下次想少用或避开的雷点**？（比如闪白强度、某类配色、转场或音效习惯）",
            "3. **常驻默认偏好**？（如 3D 引擎规格、24/30 fps、成曲默认纯原曲母带 `pure_song` 等）",
        ]
        if proposal:
            lines.append("")
            lines.append(_format_proposal_card(proposal, eff_mode, mdir))
        if eff_mode == "ask":
            lines.append("")
            lines.append("> 回复「确认写入」或补充你的喜好，我会落盘进长期记忆；回复「跳过」本次不写，随时可用 `/chiaki memory mode off` 关闭。")
        else:
            lines.append("")
            lines.append("> 当前为 `auto` 模式：若你补充新的个人喜好，我会直接更新进长期记忆；随时可用 `/chiaki memory mode ask|off` 切换。")
        print("\n".join(lines))
        return 0

    if args.cmd == "forget":
        eid = args.entry_id.strip().upper()
        cfg = load_config(mdir)
        if eid.startswith("P"):
            prefs = load_prefs(mdir)
            new_p = [p for p in prefs if str(p.get("id", "")).upper() != eid]
            if len(new_p) == len(prefs):
                sys.exit(f"Entry not found: {eid}")
            save_prefs(mdir, cfg, new_p)
            print(f"[OK] Removed preference {eid}")
            return 0
        if eid.startswith("M"):
            mistakes = load_mistakes(mdir)
            new_m = [m for m in mistakes if str(m.get("id", "")).upper() != eid]
            if len(new_m) == len(mistakes):
                sys.exit(f"Entry not found: {eid}")
            save_mistakes(mdir, cfg, new_m)
            print(f"[OK] Removed mistake guardrail {eid}")
            return 0
        if eid.startswith("F"):
            films = load_films(mdir)
            new_f = [f for f in films if str(f.get("id", "")).upper() != eid]
            if len(new_f) == len(films):
                sys.exit(f"Entry not found: {eid}")
            save_films(mdir, new_f)
            print(f"[OK] Removed film log {eid}")
            return 0
        sys.exit(f"Unknown ID prefix `{eid}` (expected P##, M##, or F###)")

    if args.cmd == "reset":
        cfg = load_config(mdir)
        save_prefs(mdir, cfg, [], [])
        save_mistakes(mdir, cfg, [], [])
        save_films(mdir, [])
        print(f"[OK] Cleared all studio memory entries in {mdir} (mode `{cfg['mode']}` preserved)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
