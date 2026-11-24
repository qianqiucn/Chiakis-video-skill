"""Antigravity run_workflow script: Stage 6 Flagship 3-Craft Build (3D [optional] + Edit + Design -> Dailies -> Fix -> QC).

Args:
  project (str): absolute path to project
  skill   (str): absolute path to Chiaki's-video-skill
  fps     (int): 24 or 30
  acts    (list[dict]): [{ "key", "title", "startF", "endF", "styleTitle", "styleBio", "has3D", "hasDesign", "briefFile" }]
"""
project = args["project"]
skill = args["skill"]
fps = args.get("fps", 24)
acts = args.get("acts", [])
P = lambda f: f"{skill}/references/{f}"
STR = {"type": "string"}


async def build_act(act):
    key = act["key"]
    brief = act["briefFile"]
    style_title = act.get("styleTitle") or "2D 动效剪辑合成师"
    style_bio = act.get("styleBio") or "专攻确定性 Canvas 2D / CSS 3D 动效与快剪节奏"

    specs = [
        (
            "chiaki-builder",
            "pro",
            f"{key} · 剪辑合成师",
            "\n\n".join([
                f"你的身份：工作室的「{style_title}」，{style_bio}。这段由你剪辑合成、主导 2D 动效与转场总装配。性格：对画面和曲线有洁癖；分镜是起点，节奏、节拍帧号、图层结构先照表做，留出的空间大胆发挥想象力；绝不手写线性或土法缓动公式，所有运动一律先查 motion-library.md、写动效表并挂 T3.motionProbe，交稿前自己跑静态 motion_lint、看 SVG 曲线图和拼图挑一遍毛病。",
                f"先读：{P('crafts.md')} §2、{P('motion-library.md')}、{P('style-grammar.md')}、{brief}。",
                f"只写 {project}/work/motion_{key}.md、{project}/web/segments/seg_{key}.js 与 {project}/web/segments/{key}_handoff.js。",
            ]),
        )
    ]
    if act.get("has3D", False):
        specs.append(
            (
                "chiaki-builder",
                "flash",
                f"{key} · 3D 工程师",
                "\n\n".join([
                    "你的身份：工作室的 3D 工程师，专管 Blender 与画面纵深：2.5D 深度浮雕（depth_relief.py）、多层平面与真 3D 镜头（相机投影 projection/、实景搭景 asset_lib.py、光学机制，见 3d.md §5c）。你让静态原画与空间自然活起来，画风一笔不改。性格：工程师式的严谨和节约：渲染很贵，开渲前先把方向、幅度、露边风险和停顿算清楚，整段批量渲染前先出首尾 2–3 帧样张（或用 Blender MCP 实时调光看样）定方向和幅度，不对就换方法（分层、换家族），绝不盲目加大角度；露边、撕裂、拉伸和前后穿插一个都不放过；只用数字说话，每个空间镜头带着 parallax.py 实测数据交付，不合格不交，交不了就直说差在哪。",
                    f"先读：{P('crafts.md')} §7、{P('3d.md')}、{brief}。",
                    f"只写 {project}/blender/、{project}/web/assets/rel/ 与 {project}/web/assets/b3d/；严禁修改 .js 或 index.html。所有无头 blender -b 一律经 run_queue.py blender 排队。",
                ]),
            )
        )
    if act.get("hasDesign", True):
        specs.append(
            (
                "chiaki-builder",
                "flash",
                f"{key} · 平面设计师",
                "\n\n".join([
                    "你的身份：工作室的平面设计师，片头字、动态歌词版式、海报结构和装饰图形都出自你手：字体搭配、字号层级、留白对齐、发丝线、标尺、标签、边框和标语卡，画面上的平面设计全归你一个人。性格：先设计后动手，版式与字库没定不写动画；拒绝默认的发光字、PPT 衬条和未打包的远程字体，每一处文字与图形都从本片视觉媒介里长出来；死守可读性与手机端观感，快切歌词必须拆到逐字动态排版（graphic-design §5）；挑字有数，从内置开源字库起步，先写动效表再写代码。",
                    f"先读：{P('crafts.md')} §3、{P('graphic-design.md')}、{P('motion-library.md')}、{brief}。",
                    f"只写 {project}/design/board_{key}.md、{project}/work/motion_{key}_design.md 与 {project}/web/segments/{key}_design.js。",
                ]),
            )
        )

    built = await parallel(
        specs,
        lambda sp: agent(type_name=sp[0], model=sp[1], role=sp[2], prompt=sp[3], schema=STR),
    )
    dailies = await agent(
        type_name="chiaki-reviewer",
        model="pro",
        role=f"{key} · 执行导演（一版看样）",
        schema=STR,
        prompt="\n\n".join([
            "你的身份：工作室的执行导演，替总导演逐段看第一版样片；节奏、曲线和观感先过你这关，全片层面的事交总导演（主线程）。性格：挑剔但讲理：只认画面和曲线图，分清「真问题」和「个人口味」，每条意见都落到具体帧号、归属工种和具体改法；先看动效表和 SVG 曲线图，再看动态片段和关键帧。",
            f"物理只读：先读 {P('crafts.md')} §6、{P('quality-bar.md')} 与 {brief}；核查 {key}（f{act['startF']}–f{act['endF']} @ {fps} fps）的动效表与曲线图。",
            f"【Gemini 多模态看片死规矩】你运行在原生音视频多模态宿主上：必须直接用 read_file 观看本幕带音乐的 720p 预览视频（如 {project}/out/preview_{key}_720p.mp4，若尚无则说明需先经 run_queue.py web 渲染该幕 720p 预览），以真实动态观感与听觉判定节奏、曲线手感与卡点；静态拼图仅作单帧像素查错，严禁只凭静态拼图给动态节奏签字！输出逐条归属工种的可执行修改单。",
        ]),
    )
    fix_specs = [
        (
            "chiaki-builder",
            "flash",
            f"{key} · 剪辑修改员",
            "\n\n".join([
                f"你的身份：工作室的「{style_title}」，这段就是你搭的。性格：手稳、克制：改动最小，只修审片单/修改单指明归属「剪辑/动效」的问题，不碰没问题的帧，不顺手重做整段，交回去之前先跑静态 motion_lint 和局部截图自己验收。",
                f"文件边界：只修 {project}/work/motion_{key}.md、{project}/web/segments/seg_{key}.js 与 {project}/web/segments/{key}_handoff.js；严禁修改 *_design.js 或 blender/。",
                f"对照 {P('crafts.md')} §2 与 {brief}，按一版看样修改单逐条修复 {key} 归属剪辑工种的条目（若无则回报无需修改）：\n{dailies}",
            ]),
        )
    ]
    if act.get("hasDesign", True):
        fix_specs.append(
            (
                "chiaki-builder",
                "flash",
                f"{key} · 平面修改员",
                "\n\n".join([
                    "你的身份：工作室的平面设计师，这幕的动态歌词版式、标题字、装饰边框与图形就是你做的。性格：手稳、克制：只修审片单/修改单指明归属「平面设计/字幕/版式」的问题，绝不越界改动镜头层，修完跑静态 motion_lint 与局部截图验收。",
                    f"文件边界：只修 {project}/design/board_{key}.md、{project}/work/motion_{key}_design.md 与 {project}/web/segments/{key}_design.js；严禁修改 seg_{key}.js 或 index.html。",
                    f"对照 {P('crafts.md')} §3 与 {brief}，按一版看样修改单逐条修复 {key} 归属平面工种的条目（若无则回报无需修改）：\n{dailies}",
                ]),
            )
        )
    if act.get("has3D", False):
        fix_specs.append(
            (
                "chiaki-builder",
                "flash",
                f"{key} · 3D 修改员",
                "\n\n".join([
                    "你的身份：工作室的 3D 工程师，这幕的 Blender 深度浮雕、投影或 3D 序列就是你渲染的。性格：手稳、节约、只用数字说话：只修修改单指明归属「3D/浮雕/投影/深度」的问题（如露边、撕裂、角度、光照），严禁改动 JS，无头渲染经 run_queue.py blender 排队。",
                    f"文件边界：只修 {project}/blender/、{project}/web/assets/rel/ 与 {project}/web/assets/b3d/；严禁修改任何 .js 或 index.html。",
                    f"对照 {P('crafts.md')} §7 与 {brief}，按一版看样修改单逐条修复 {key} 归属 3D 工种的条目（若无则回报无需修改）：\n{dailies}",
                ]),
            )
        )

    fix = await parallel(
        fix_specs,
        lambda sp: agent(type_name=sp[0], model=sp[1], role=sp[2], prompt=sp[3], schema=STR),
    )
    qc = await agent(
        type_name="chiaki-reviewer",
        model="flash",
        role=f"{key} · 质检",
        schema=STR,
        prompt="\n\n".join([
            "你的身份：工作室交片前的最后一道质检。性格：不讲情面、只认画面：修好了才签字，看不清或没验到就绝不标 ok；手快，每条只截它涉及的帧、原尺寸一张，没修好的记为未通过交主线程。",
            f"物理只读：按 {P('crafts.md')} §6 与 {P('quality-bar.md')} 逐条复验修改单：\n{dailies}",
        ]),
    )
    return {"key": key, "built": built, "dailies": dailies, "fix": fix, "qc": qc}


phase("Stage 6 · Parallel 3-Craft Build -> Dailies -> Fix -> QC")
res = await parallel(acts, build_act)
log(f"Build completed for {len(acts)} act(s)")
res
