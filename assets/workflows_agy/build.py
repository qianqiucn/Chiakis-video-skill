"""Antigravity run_workflow script: Stage 4 2D Studio Build (Edit + Design -> Dailies -> Fix -> QC).

Args:
  project (str): absolute path to project
  skill   (str): absolute path to Chiaki's-video-skill
  fps     (int): 24 or 30
  acts    (list[dict]): [{ "key", "title", "startF", "endF", "styleTitle", "styleBio", "hasDesign", "briefFile" }]
"""
project = args["project"]
skill = args["skill"]
fps = args.get("fps", 24)
acts = args.get("acts", [])
P = lambda f: f"{skill}/references/{f}"


def build_act(act):
    key = act["key"]
    brief = act["briefFile"]
    style_title = act.get("styleTitle") or "2D 动效剪辑合成师"
    style_bio = act.get("styleBio") or "专攻确定性 Canvas 2D / CSS 3D 动效与快剪节奏"

    craft_fns = [
        lambda: agent(
            type="chiaki-builder",
            model="pro",
            role=f"{key} · 剪辑合成师",
            prompt="\n\n".join([
                f"你的身份：工作室的「{style_title}」，{style_bio}。这段由你剪辑合成、主导 2D 动效与转场总装配。性格：对画面和曲线有洁癖；分镜是起点，节奏、节拍帧号、图层结构先照表做，留出的空间大胆发挥想象力；绝不手写线性或土法缓动公式，所有运动一律先查 motion-library.md、写动效表并挂 T3.motionProbe，交稿前自己跑静态 motion_lint、看 SVG 曲线图和拼图挑一遍毛病。",
                f"先读：{P('crafts.md')} §2、{P('motion-library.md')}、{P('style-grammar.md')}、{brief}。",
                f"只写 {project}/work/motion_{key}.md、{project}/web/segments/seg_{key}.js 与 {project}/web/segments/{key}_handoff.js。",
            ]),
        )
    ]
    if act.get("hasDesign", True):
        craft_fns.append(
            lambda: agent(
                type="chiaki-builder",
                model="flash",
                role=f"{key} · 平面设计师",
                prompt="\n\n".join([
                    "你的身份：工作室的平面设计师，片头字、动态歌词版式、海报结构和装饰图形都出自你手：字体搭配、字号层级、留白对齐、发丝线、标尺、标签、边框和标语卡，画面上的平面设计全归你一个人。性格：先设计后动手，版式与字库没定不写动画；拒绝默认的发光字、PPT 衬条和未打包的远程字体，每一处文字与图形都从本片视觉媒介里长出来；死守可读性与手机端观感，快切歌词必须拆到逐字动态排版（graphic-design §5）；挑字有数，从内置开源字库起步，先写动效表再写代码。",
                    f"先读：{P('crafts.md')} §3、{P('graphic-design.md')}、{P('motion-library.md')}、{brief}。",
                    f"只写 {project}/design/board_{key}.md、{project}/work/motion_{key}_design.md 与 {project}/web/segments/{key}_design.js。",
                ]),
            )
        )

    built = parallel(craft_fns)
    dailies = agent(
        type="chiaki-reviewer",
        model="pro",
        role=f"{key} · 执行导演（一版看样）",
        prompt="\n\n".join([
            "你的身份：工作室的执行导演，替总导演逐段看第一版样片；节奏、曲线和观感先过你这关，全片层面的事交总导演（主线程）。性格：挑剔但讲理：只认画面和曲线图，分清「真问题」和「个人口味」，每条意见都落到具体帧号、归属工种和具体改法；先看动效表和 SVG 曲线图，再看动态片段和关键帧。",
            f"物理只读：核查 {key}（f{act['startF']}–f{act['endF']} @ {fps} fps）的动效表、曲线图与拼图，给出逐条可执行修改单。",
        ]),
    )
    fix = agent(
        type="chiaki-builder",
        model="flash",
        role=f"{key} · 修改员",
        prompt="\n\n".join([
            f"你的身份：工作室的「{style_title}」，这段就是你搭的。性格：手稳、克制：改动最小，只修审片单/修改单指明的问题，不碰没问题的帧，不顺手重做整段，交回去之前先跑静态 motion_lint 和局部截图自己验收。",
            f"按一版看样修改单逐条修复 {key}：\n{dailies}",
        ]),
    )
    qc = agent(
        type="chiaki-reviewer",
        model="flash",
        role=f"{key} · 质检",
        prompt="\n\n".join([
            "你的身份：工作室交片前的最后一道质检。性格：不讲情面、只认画面：修好了才签字，看不清或没验到就绝不标 ok；手快，每条只截它涉及的帧、原尺寸一张，没修好的记为未通过交主线程。",
            f"物理只读：逐条复验修改单：\n{dailies}",
        ]),
    )
    return {"key": key, "built": built, "dailies": dailies, "fix": fix, "qc": qc}


result = parallel([lambda act=a: build_act(act) for a in acts])
