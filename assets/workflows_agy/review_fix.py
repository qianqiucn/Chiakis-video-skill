"""Antigravity run_workflow script: Stage 9 Three-Lens Adversarial Review -> 3 Verifiers -> Fix -> QC.

Args:
  project      (str): absolute path to project
  skill        (str): absolute path to Chiaki's-video-skill
  reviewBrief  (str): path to REVIEW_BRIEF.md
  filesByOwner (list[dict]): [{ "owner": "act1 剪辑合成师", "files": ["web/segments/seg_act1.js"] }, ...]
"""
project = args["project"]
skill = args["skill"]
review_brief = args["reviewBrief"]
files_by_owner = args.get("filesByOwner", [])
P = lambda f: f"{skill}/references/{f}"
STR = {"type": "string"}

LENSES = [
    (
        "rules",
        "规矩审片员（执行监制）",
        "规矩复核员（执行制片）",
        "你的身份：工作室的执行监制，负责让成片守住客户和工作室定下的每一条规矩。性格：较真、记性好、对事不对人：发现违规就直说，但只按条文说话，每条都指明违反 house-style 哪一节哪一句，并附具体帧号。",
        "你的身份：工作室的执行制片，替总导演兼制片人把关规矩，是规矩审片单的复核人。性格：公正、冷静：逐条对照 house-style 原文和截图核实，冤枉人的意见一律驳回。",
    ),
    (
        "tech",
        "技术审片员（技术剪辑师）",
        "技术复核员（技术总监）",
        "你的身份：工作室里最懂技术的剪辑师，十几年 AE / Nuke 合成和调色经验，精通网页 Canvas 2D / CSS 3D 动画、动效曲线与视频编码，每支片交付前的技术质检都由你签字。性格：一丝不苟、只认证据：每条问题写清第几帧、画面哪个位置、量到的数（曲线 Q1、像素越界、帧差、抽帧步长、响度），能截图对比就截图。",
        "你的身份：工作室的技术总监，专门复核技术质检单。性格：多疑、严谨：每条都自己核查截图和曲线数据，复现不出来的一律驳回。",
    ),
    (
        "edit",
        "剪辑感审片员（剪辑指导）",
        "剪辑感复核员（执行导演）",
        "你的身份：工作室的剪辑指导，资深快剪与动态设计导演，做过上百支 PV、MV 和商业片头，最清楚观众会在哪一秒划走。性格：直率、敢说难听话，但每句评价都落到具体帧号、节奏点和具体改法，不说空话。",
        "你的身份：这支片的执行导演，替总导演复核观感上的意见。性格：挑剔但讲理：分清「真问题」和「个人口味」，只有你也能在画面上指出来、观众也会感到的问题才算成立。",
    ),
]

phase("Stage 9a · 3 Independent Read-Only Lenses")
raw_notes = await parallel(
    LENSES,
    lambda lens: agent(
        type_name="chiaki-reviewer",
        model="pro",
        role=lens[1],
        schema=STR,
        prompt="\n\n".join([
            lens[3],
            f"物理只读：严禁修改任何文件。先读 {review_brief}、{P('crafts.md')} §6、{P('house-style.md')}、{P('quality-bar.md')}、{P('style-grammar.md')}，核查项目 {project} 并输出帧级问题单。",
        ]),
    ),
)

phase("Stage 9b · 3 Independent Read-Only Verifiers")
verified = await parallel(
    list(enumerate(LENSES)),
    lambda pair: agent(
        type_name="chiaki-reviewer",
        model="pro",
        role=pair[1][2],
        schema=STR,
        prompt="\n\n".join([
            pair[1][4],
            f"物理只读：先读 {review_brief}、{P('crafts.md')} §6 与 {P('house-style.md')}，逐条核实以下审片单并判定成立或驳回：\n\n{raw_notes[pair[0]]}",
        ]),
    ),
)

confirmed = "\n\n---\n\n".join(str(v) for v in verified)
fixes = []
qc = None

if files_by_owner:
    phase("Stage 9c · Scoped Pre-Render Fixes")
    fixes = await parallel(
        files_by_owner,
        lambda grp: agent(
            type_name="chiaki-builder",
            model="flash",
            role=f"修改员 · {grp['owner']}",
            schema=STR,
            prompt="\n\n".join([
                f"你的身份：工作室的「{grp['owner']}」，这些文件就是你搭的。性格：手稳、克制：改动最小，只修复核成立的问题，不碰没问题的帧，不顺手重做整段，交回去之前先跑静态 motion_lint 和局部截图自己验收。",
                f"对照 {P('crafts.md')} 与 {review_brief}，只允许编辑：{', '.join(grp['files'])}。\n\n复核通过的问题单：\n{confirmed}",
            ]),
        ),
    )

    phase("Stage 9d · Read-Only QC Verification")
    qc = await agent(
        type_name="chiaki-reviewer",
        model="flash",
        role="终审质检（QC）",
        schema=STR,
        prompt="\n\n".join([
            "你的身份：工作室交片前的最后一道质检。性格：不讲情面、只认画面：修好了才签字，看不清或没验到就绝不标 ok；手快，每条只截它涉及的帧、原尺寸一张，没修好的记为未通过交主线程。",
            f"物理只读：按 {P('crafts.md')} §6 与 {P('quality-bar.md')} 逐条复验已成立的问题是否修好，输出 PASS / FAIL 汇总。\n\n复核单：\n{confirmed}",
        ]),
    )

log("Stage 9 review_fix finished")
{"raw_notes": raw_notes, "verified": verified, "fixes": fixes, "qc": qc}
