"""Antigravity run_workflow script: Stages 11–12 Independent 7-Dim Scorecard -> Targeted Polish Round -> Read-Only QC.

Run after Stage 10 renders the V1 audiovisual film with mastered audio.
Persists structured scorecard JSON (`work/score_<taskId>.json`) and detailed markdown (`work/score_<taskId>.md`)
separately and flags `INCOMPLETE_REVIEW` if any of the 7 dimensions, verdict, or `<!-- SCORE_COMPLETE -->` sentinel
is missing (guards against host gateway truncation / 503).

Args:
  project       (str): absolute path to project
  skill         (str): absolute path to Chiaki's-video-skill
  scoreBrief    (str): path to SCORE_BRIEF.md
  renderVideo   (str): path to rendered V1 MP4 with mastered audio
  filesByOwner  (list[dict]): [{ "owner": "act1 剪辑合成师", "files": ["web/segments/seg_act1.js"] }, ...]
  taskId        (str): optional identifier for persisted score files (default "v1")
  tier          (str): "lite" | "pro" | "ultra" (default "pro"; in lite/pro this serves as the unified post-V1 review+score loop, replacing Stage 9; in lite, optional skipQc=True skips separate QC subagent after consolidated flash fix)
  skipQc        (bool): optional (default True when tier == "lite", else False)
  skipFixIfPass (bool): default True — skip polish ONLY if scorecard is complete AND verdict is DELIVER (all 7 dims >= 8)
"""
import json
import os
import re

project = args["project"]
skill = args["skill"]
score_brief = args["scoreBrief"]
render_video = args["renderVideo"]
files_by_owner = args.get("filesByOwner", [])
task_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(args.get("taskId", "v1"))).strip("_") or "v1"
tier = str(args.get("tier", "pro")).strip().lower()
if tier not in ("lite", "pro", "ultra"):
    tier = "pro"
skip_qc = bool(args.get("skipQc", tier == "lite"))
skip_if_pass = args.get("skipFixIfPass", True)
P = lambda f: f"{skill}/references/{f}"
STR = {"type": "string"}
DIMS = ("concept", "motion", "rhythm", "typography", "depth", "sound", "technical")


def parse_and_save_scorecard(raw_text: str) -> dict:
    txt = str(raw_text or "")
    has_sentinel = "<!-- SCORE_COMPLETE -->" in txt
    parsed = None
    m = re.search(r"```(?:scorecard-json|json)\s*(\{.*?\})\s*```", txt, re.S | re.I)
    if m:
        try:
            parsed = json.loads(m.group(1))
        except Exception:
            parsed = None
    dims = {}
    if isinstance(parsed, dict) and isinstance(parsed.get("dimensions"), dict):
        for k in DIMS:
            v = parsed["dimensions"].get(k)
            if isinstance(v, (int, float)) and 1 <= v <= 10:
                dims[k] = int(round(v))
    verdict = str((parsed or {}).get("verdict") or "").upper()
    if verdict not in ("DELIVER", "REVISE"):
        mv = re.search(r"Verdict:\s*(DELIVER|REVISE)\b", txt, re.I)
        verdict = mv.group(1).upper() if mv else ""

    missing = [k for k in DIMS if k not in dims]
    complete = (not missing) and (verdict in ("DELIVER", "REVISE")) and has_sentinel
    all_ge8 = complete and all(dims[k] >= 8 for k in DIMS)
    if complete and not all_ge8 and verdict == "DELIVER":
        verdict = "REVISE"  # never allow DELIVER when any single dimension < 8

    record = {
        "task_id": task_id,
        "status": "COMPLETE" if complete else "INCOMPLETE_REVIEW",
        "complete": complete,
        "has_sentinel": has_sentinel,
        "missing_dimensions": missing,
        "host_review_mode": (parsed or {}).get("host_review_mode", "unknown"),
        "verdict": verdict or "INCOMPLETE",
        "dimensions": dims,
        "blocking_issues": (parsed or {}).get("blocking_issues", []),
        "render_video": render_video,
    }
    work_dir = os.path.join(project, "work")
    try:
        os.makedirs(work_dir, exist_ok=True)
        with open(os.path.join(work_dir, f"score_{task_id}.json"), "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        with open(os.path.join(work_dir, f"score_{task_id}.md"), "w", encoding="utf-8") as f:
            if not complete:
                f.write(f"> **INCOMPLETE_REVIEW** (task_id={task_id}, missing={missing}, sentinel={has_sentinel})\n\n")
            f.write(txt)
    except OSError:
        pass
    return record


phase(f"Stage 11 · Independent 7-Dim Scorecard ({task_id})")
score_v1 = await agent(
    type_name="chiaki-reviewer",
    model="pro",
    role="独立成片评分员（一版打分）",
    schema=STR,
    prompt="\n\n".join([
        "你的身份：资深动态设计评委（Motionographer 编辑、Buck / ManvsMachine 创意总监、头部动态设计博主这一级）。片子不是你做的。目标水准是获奖级别的商业作品（house-style §0）。性格：下手要狠、说话要具体、绝不客气虚高；先量规格与曲线图再看画面，按 7 维严格打分（每维 ≥ 8 分及格，不算平均），每项给帧号/秒数证据。",
        f"物理只读：严禁编辑任何代码。先读 {score_brief}、{P('crafts.md')} §6、{P('quality-bar.md')} 与旗舰量化标杆 {P('benchmark-quality.md')}，严格审查带声成片（{render_video}）、QA 报告、SVG 曲线图与母带报告。",
        f"【Gemini 多模态看片死规矩】你运行在原生音视频多模态宿主上：必须直接调用 read_file 原生观看 {render_video}（长片可分幕看 720p 片段）并直听高潮歌词微 WAV 核对人声口型与节奏手感；静态拼图仅作单帧像素查错，严禁跳过看视频仅凭静态拼图或频谱打分！",
        f"【防截断输出要求】务必在回复最顶部（前 25 行内）严格按 {score_brief} 输出 ```scorecard-json```（含 task_id='{task_id}'、host_review_mode、verdict 与全部 7 维整数分）、Verdict 行与 7 维总表，再写逐帧详细建议，并在文末以 `<!-- SCORE_COMPLETE -->` 结尾。",
    ]),
)

score_meta = parse_and_save_scorecard(score_v1)
if not score_meta["complete"]:
    log(f"INCOMPLETE_REVIEW ({task_id}): missing={score_meta['missing_dimensions']} verdict={score_meta['verdict']} sentinel={score_meta['has_sentinel']} — saved partial record to work/score_{task_id}.json/.md")
    out = {"status": "INCOMPLETE_REVIEW", "score_meta": score_meta, "score_v1": score_v1, "skipped_polish": True, "fixes": [], "qc": None}
elif (skip_if_pass and score_meta["verdict"] == "DELIVER") or not files_by_owner:
    log(f"Scorecard ({task_id}) passed DELIVER (all 7 dims >= 8) or no editable file groups; skipping polish round")
    out = {"status": "DELIVER", "score_meta": score_meta, "score_v1": score_v1, "skipped_polish": True, "fixes": [], "qc": None}
else:
    phase("Stage 12a · Targeted Polish Round (Scoped Fixers)")
    fixes = await parallel(
        files_by_owner,
        lambda grp: agent(
            type_name="chiaki-builder",
            model="flash",
            role=f"定向修改员 · {grp['owner']}",
            schema=STR,
            prompt="\n\n".join([
                f"你的身份：工作室的「{grp['owner']}」，这段就是你搭的。性格：手稳、克制：改动最小，只修审片单/修改单指明的问题，不碰没问题的帧，不顺手重做整段，交回去之前先跑静态 motion_lint 和局部截图自己验收。",
                f"对照 {P('crafts.md')} 与 {score_brief}，只允许编辑：{', '.join(grp['files'])}。\n\n按一版独立评分卡扣分项执行一轮最小化定向修复：\n{score_v1}",
            ]),
        ),
    )

    if skip_qc:
        qc = None
        log(f"Polish completed ({tier} tier, skipQc=True); run static motion_lint + coordinator spot-check then Stage 13 re-render & Gate B2")
    else:
        phase("Stage 12b · Read-Only QC Recheck Before Re-Render")
        qc = await agent(
            type_name="chiaki-reviewer",
            model="flash",
            role="复修质检（QC）",
            schema=STR,
            prompt="\n\n".join([
                "你的身份：工作室交片前的最后一道质检。性格：不讲情面、只认画面：修好了才签字，看不清或没验到就绝不标 ok；手快，每条只截它涉及的帧、原尺寸一张，没修好的记为未通过交主线程。",
                f"物理只读：按 {P('crafts.md')} §6 与 {P('quality-bar.md')} 逐条复验一版独立评分卡的每一条扣分项是否修好，输出 PASS / FAIL 清单交总导演重渲染与 Gate B2：\n\n{score_v1}",
            ]),
        )
        log("Polish + QC completed; ready for Stage 13 re-render & Gate B2")
    out = {"status": "REVISED", "tier": tier, "score_meta": score_meta, "score_v1": score_v1, "skipped_polish": False, "fixes": fixes, "qc": qc}

out
