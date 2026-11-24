"""Antigravity run_workflow script: Stages 11–12 Independent 7-Dim Scorecard -> Targeted Polish Round -> Read-Only QC.

Run after Stage 10 renders the V1 audiovisual film with mastered audio.
After QC passes, the director re-renders the V2 1080p + 2K FLAC final and completes Gate B2.

Args:
  project       (str): absolute path to project
  skill         (str): absolute path to Chiaki's-video-skill
  scoreBrief    (str): path to SCORE_BRIEF.md
  renderVideo   (str): path to rendered V1 MP4 with mastered audio
  filesByOwner  (list[dict]): [{ "owner": "act1 剪辑合成师", "files": ["web/segments/seg_act1.js"] }, ...]
  skipFixIfPass (bool): default True — skip polish if V1 verdict is DELIVER (all 7 dims >= 8)
"""
import re

project = args["project"]
skill = args["skill"]
score_brief = args["scoreBrief"]
render_video = args["renderVideo"]
files_by_owner = args.get("filesByOwner", [])
skip_if_pass = args.get("skipFixIfPass", True)
P = lambda f: f"{skill}/references/{f}"
STR = {"type": "string"}

phase("Stage 11 · Independent 7-Dim Scorecard (V1 Audiovisual Render)")
score_v1 = await agent(
    type_name="chiaki-reviewer",
    model="pro",
    role="独立成片评分员（一版打分）",
    schema=STR,
    prompt="\n\n".join([
        "你的身份：资深动态设计评委（Motionographer 编辑、Buck / ManvsMachine 创意总监、头部动态设计博主这一级）。片子不是你做的。目标水准是获奖级别的商业作品（house-style §0）。性格：下手要狠、说话要具体、绝不客气虚高；先量规格与曲线图再看画面，按 7 维严格打分（每维 ≥ 8 分及格，不算平均），每项给帧号/秒数证据。",
        f"物理只读：严禁编辑任何代码。先读 {score_brief}、{P('crafts.md')} §6 与 {P('quality-bar.md')}，严格审查一版带声成片（{render_video}）、QA 报告、SVG 曲线图与母带报告。",
        f"【Gemini 多模态看片死规矩】你运行在原生音视频多模态宿主上：必须直接调用 read_file 原生观看 {render_video}（长片可分幕看 720p 片段）并直听高潮歌词微 WAV 核对人声口型与节奏手感；静态拼图仅作单帧像素查错，严禁跳过看视频仅凭静态拼图或频谱打分！输出 7 维打分表与 Verdict（DELIVER 或 REVISE），逐条写清扣分帧号与具体改法。",
    ]),
)

if (skip_if_pass and re.search(r"Verdict:\s*DELIVER\b", str(score_v1), re.I)) or not files_by_owner:
    log("V1 scorecard passed DELIVER (or no editable file groups provided); skipping polish round")
    out = {"score_v1": score_v1, "skipped_polish": True, "fixes": [], "qc": None}
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
    out = {"score_v1": score_v1, "skipped_polish": False, "fixes": fixes, "qc": qc}

out
