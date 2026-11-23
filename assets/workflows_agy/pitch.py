"""Antigravity run_workflow script: Stage 2 Pitch Meeting (chiaki-writer, Model=pro).

Args:
  project (str): absolute path to the video project directory
  skill   (str): absolute path to Chiaki's-video-skill
  acts    (list[dict]): [{ "key": "act1", "title": "...", "brief": "..." }, ...]
"""
project = args["project"]
skill = args["skill"]
acts = args.get("acts", [])
P = lambda f: f"{skill}/references/{f}"

ANGLES = [
    (
        "medium",
        "媒介设计师",
        "你是「媒介设计师」：你是工作室的媒介设计师，专门把一整段 2D 片子放进一种触手可及的视觉媒介里讲：印刷画报、胶片印样、暗房显影、字符画、像素掌机、LED 墙、蓝图、漫画分格、示波器、宣纸水墨、霓虹管……媒介本身就是创意。性格：执着于形式纯粹，敢整段不用一张平庸的模板画面。",
    ),
    (
        "stage",
        "演出策划",
        "你是「演出策划」：你是工作室的演出策划，擅长把一支 PV 或片头做成一场事件或演出：舞台聚光、广播插播、倒计时发射、仪式开场、高潮前的一秒静默……用调度、节奏和现场感讲故事。性格：爱制造高潮，懂得什么时候让全场安静；高潮靠节奏反差与画面事件本身，不靠无脑堆闪光和抖动。",
    ),
    (
        "lens",
        "摄影指导",
        "你是「摄影指导」：你是工作室的摄影指导，擅长用一个 2D/2.5D 视角概念撑起整段：连贯横摇的画幅长卷、从微距字迹到全景画面的尺度跳跃、多层景深穿梭（multiplane）、锁定取景框里的情绪调度、俯仰构图反差……视角就是创意。性格：痴迷机位与构图，讨厌平庸居中的 PPT 摆拍；清楚画面来自 2D 图层与代码绘制，所有运镜都落实到具体图层视差、缓动曲线与快门动态模糊，绝不靠拉大单图硬撑。",
    ),
]


def pitch_act(act):
    key, title, brief = act["key"], act["title"], act["brief"]
    pitches = parallel(
        [
            lambda a=ang: agent(
                type="chiaki-writer",
                model="pro",
                role=f"{key} · {a[1]}",
                prompt="\n\n".join([
                    a[2],
                    f"先读：{P('house-style.md')}、{P('script-writing.md')}、{P('mg-styles.md')}、{P('shot-recipes.md')}、{P('crafts.md')} §1。",
                    f"为项目 {project} 的幕次「{title}」（key: {key}）写完整 2D 视觉提案，写入 {project}/work/pitch/{key}_{a[0]}.md。",
                    f"导演简报：{brief}",
                ]),
            )
            for ang in ANGLES
        ]
    )
    pick = agent(
        type="chiaki-writer",
        model="pro",
        role=f"{key} · 创意总监",
        prompt="\n\n".join([
            "你是「创意总监」：你是工作室的创意总监，替总导演兼制片人主持提案会，这几个方案都不是你写的，定稿交总导演签字。你最看重想象力：视觉形式新鲜、紧扣主题/歌词本身、有明确的核心画面机制、看完记得住；其次才是实现成本。性格：眼光挑剔，不和稀泥，敢选最大胆且自洽的那个，同时写清技术风险与执行边界；目标是获奖级别的商业动态设计作品（house-style §0），明确指出每个方案离它差在哪。",
            f"阅读 {project}/work/pitch/{key}_medium.md、{key}_stage.md、{key}_lens.md，选出定稿写入 {project}/work/pitch/{key}_pick.md。",
        ]),
    )
    return {"key": key, "pitches": pitches, "pick": pick}


picks = parallel([lambda act=a: pitch_act(act) for a in acts])
slate = None
if len(acts) > 1:
    slate = agent(
        type="chiaki-writer",
        model="pro",
        role="执行制片 · 全片统筹",
        prompt="\n\n".join([
            "你是「执行制片」：你是工作室的执行制片，替总导演兼制片人统筹整支片的提案。性格：冷静、统筹全局，眼里是整支片的起承转合和节奏变化，而不是某一段的局部得失；核查各幕的视觉媒介、调色弧线、主字体和跨幕转场是否撞车。",
            f"核查所有定稿（{', '.join(a['key'] + '_pick.md' for a in acts)}），输出统筹结论到 {project}/work/pitch/SLATE.md。",
        ]),
    )

result = {"picks": picks, "slate": slate}
