"""Unit tests for scripts/memory.py (self-iterating studio memory)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / "scripts" / "memory.py"


def run_mem(*args: str) -> str:
    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(MEM), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return r.stdout


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="chiaki_mem_test_") as td:
        d = Path(td)

        # 1. Default status (ask mode, empty)
        st = json.loads(run_mem("status", "--dir", str(d), "--json"))
        assert st["mode"] == "ask", st
        assert st["preferences"] == 0 and st["mistakes"] == 0 and st["films"] == 0

        # 2. Add preferences + fuzzy CJK dedup
        o1 = run_mem("add-pref", "--dir", str(d), "--category", "audio", "--text", "歌词 PV 默认纯原曲洁净母带，不加额外 swoosh")
        assert "added preference P01" in o1, o1
        o2 = run_mem("add-pref", "--dir", str(d), "--category", "audio", "--text", "歌词 PV 默认纯原曲洁净母带不加额外 swoosh")
        assert "bumped preference P01" in o2 and "hits=2" in o2, o2
        assert (d / "preferences.md").exists()

        # 3. Add mistake + repeat hit triggers skill-upgrade candidate
        m1 = run_mem(
            "add-mistake", "--dir", str(d), "--category", "vision",
            "--trigger", "银白发二次元角色拆头发",
            "--mistake", "使用纯白底导致浅色发梢被吃掉",
            "--rule", "统一用 part_cutout.py 中灰底与 2K 局部放大精修",
        )
        assert "added mistake M01" in m1 and "SKILL-UPGRADE" not in m1, m1
        m2 = run_mem(
            "add-mistake", "--dir", str(d), "--category", "vision",
            "--trigger", "银白发二次元角色拆头发",
            "--mistake", "白底吃掉银发边缘",
            "--rule", "统一用 part_cutout.py 中灰底与 2K 局部放大精修",
        )
        assert "bumped mistake M01" in m2 and "hits=2" in m2 and "SKILL-UPGRADE CANDIDATE" in m2, m2

        # 4. Log film & verify stage context slices
        run_mem(
            "log-film", "--dir", str(d),
            "--title", "Neon Ink PV", "--type", "lyric_pv",
            "--styles", "editorial-print,35mm-contact-sheet",
            "--fonts", "Smiley Sans,Syne",
            "--palette", "#0F172A,#F59E0B",
            "--scores", "9,9,9,8,9,9,9",
        )
        ctx_brief = run_mem("context", "--dir", str(d), "--stage", "brief")
        assert "纯原曲洁净母带" in ctx_brief and "M01" not in ctx_brief, ctx_brief
        ctx_pitch = run_mem("context", "--dir", str(d), "--stage", "pitch")
        assert "Neon Ink PV" in ctx_pitch and "editorial-print" in ctx_pitch, ctx_pitch
        ctx_review = run_mem("context", "--dir", str(d), "--stage", "review")
        assert "M01" in ctx_review and "part_cutout.py" in ctx_review, ctx_review

        # 5. Proposal card in ask mode (preview only without --confirm; writes with --confirm)
        prop_p = d / "proposal.json"
        prop_p.write_text(json.dumps({
            "film": {"title": "Film Two", "type": "promo", "styles": ["kinetic-swiss"], "fonts": ["Oswald"]},
            "preferences": [{"category": "avoid", "text": "讨厌廉价高亮霓虹外发光"}],
            "mistakes": [{"category": "type", "trigger": "描边空心大字", "mistake": "直接描边可变字重导致笔画内叠", "rule": "打包字体加 --static 合并轮廓"}],
        }, ensure_ascii=False), encoding="utf-8")

        dry = run_mem("apply", str(prop_p), "--dir", str(d))
        assert "PENDING CONFIRMATION" in dry, dry
        st_before = json.loads(run_mem("status", "--dir", str(d), "--json"))
        assert st_before["films"] == 1 and st_before["preferences"] == 1

        applied = run_mem("apply", str(prop_p), "--dir", str(d), "--confirm")
        assert "[OK] Applied" in applied and "film:F002" in applied, applied
        st_after = json.loads(run_mem("status", "--dir", str(d), "--json"))
        assert st_after["films"] == 2 and st_after["preferences"] == 2 and st_after["mistakes"] == 2

        # 6. Readonly & off switch behavior
        run_mem("mode", "readonly", "--dir", str(d))
        ro = run_mem("apply", str(prop_p), "--dir", str(d), "--confirm")
        assert "[SKIP]" in ro and "readonly" in ro, ro
        assert run_mem("context", "--dir", str(d), "--stage", "brief").strip() != ""

        run_mem("mode", "off", "--dir", str(d))
        assert run_mem("context", "--dir", str(d), "--stage", "all").strip() == ""
        off_apply = run_mem("apply", str(prop_p), "--dir", str(d), "--confirm")
        assert "[SKIP]" in off_apply and "off" in off_apply, off_apply

        # 7. Auto mode applies without --confirm
        run_mem("mode", "auto", "--dir", str(d))
        auto_out = run_mem("apply", str(prop_p), "--dir", str(d))
        assert "[OK] Applied" in auto_out and "SKILL-UPGRADE CANDIDATE" in auto_out, auto_out

        # 8. Draft post-delivery preference card (Gate B2 Item #6)
        run_mem("mode", "ask", "--dir", str(d))
        card = run_mem("draft-card", "--dir", str(d), "--proposal", str(prop_p), "--title", "星尘破晓")
        assert "下支片想怎么更合你胃口" in card and "确认写入" in card and "Film Two" in card, card
        run_mem("mode", "off", "--dir", str(d))
        card_off = run_mem("draft-card", "--dir", str(d), "--proposal", str(prop_p))
        assert "[SKIP]" in card_off, card_off
        run_mem("mode", "auto", "--dir", str(d))

        # 9. Forget & reset
        run_mem("forget", "P02", "--dir", str(d))
        st_f = json.loads(run_mem("status", "--dir", str(d), "--json"))
        assert st_f["preferences"] == 1
        run_mem("reset", "--yes", "--dir", str(d))
        st_r = json.loads(run_mem("status", "--dir", str(d), "--json"))
        assert st_r["preferences"] == 0 and st_r["mistakes"] == 0 and st_r["films"] == 0 and st_r["mode"] == "auto"

    print("ok   test_memory.py  # 9 studio-memory suites passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
