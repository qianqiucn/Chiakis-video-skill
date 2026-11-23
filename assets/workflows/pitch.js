// pitch.js — Stage 2 Pitch Meeting for 2D video acts (3 competing angles -> Creative Director -> Executive Producer).
// Args: { project, skill, acts: [{ key, title, brief }] }
const { project, skill, acts = [] } = args;
const P = (f) => `${skill}/references/${f}`;

const ANGLES = [
  {
    key: "medium",
    role: "媒介设计师",
    persona:
      "你是「媒介设计师」：你是工作室的媒介设计师，专门把一整段 2D 片子放进一种触手可及的视觉媒介里讲：印刷画报、胶片印样、暗房显影、字符画、像素掌机、LED 墙、蓝图、漫画分格、示波器、宣纸水墨、霓虹管……媒介本身就是创意。性格：执着于形式纯粹，敢整段不用一张平庸的模板画面。",
  },
  {
    key: "stage",
    role: "演出策划",
    persona:
      "你是「演出策划」：你是工作室的演出策划，擅长把一支 PV 或片头做成一场事件或演出：舞台聚光、广播插播、倒计时发射、仪式开场、高潮前的一秒静默……用调度、节奏和现场感讲故事。性格：爱制造高潮，懂得什么时候让全场安静；高潮靠节奏反差与画面事件本身，不靠无脑堆闪光和抖动。",
  },
  {
    key: "lens",
    role: "摄影指导",
    persona:
      "你是「摄影指导」：你是工作室的摄影指导，擅长用一个 2D/2.5D/3D 视角概念撑起整段：连贯横摇的画幅长卷、从微距字迹到全景空间的尺度跳跃、多层景深穿梭（multiplane）、Blender 镜头投影推入（projection）或实景 3D 搭景穿越、俯仰构图反差……视角就是创意。性格：痴迷机位与构图，讨厌平庸居中的 PPT 摆拍；清楚不同景深手段的边界：穿越真实空间上 Blender 投影或实景搭景，单图景深上浮雕或分层视差，所有运镜都落实到具体视差、缓动曲线与快门动态模糊，绝不靠拉大单图硬撑。",
  },
];

const picks = await Promise.all(
  acts.map(async (act) => {
    const pitches = await Promise.all(
      ANGLES.map((ang) =>
        agent({
          model: "pro",
          role: `${act.key} · ${ang.role}`,
          prompt: [
            ang.persona,
            `先读：${P("house-style.md")}、${P("script-writing.md")}、${P("mg-styles.md")}、${P("shot-recipes.md")}、${P("crafts.md")} §1。`,
            `任务：为项目 ${project} 的幕次「${act.title}」（key: ${act.key}）写一份完整 2D 视觉提案，写入 ${project}/work/pitch/${act.key}_${ang.key}.md。`,
            `导演简报：${act.brief}`,
            `要求：明确视觉媒介、调色板 Hex、内置开源字体搭配（assets/fonts/catalog.md）、核心 2D 动效机制（style-grammar §6b）、跨幕转场与风险；不写代码。`,
          ].join("\n\n"),
        })
      )
    );

    const pick = await agent({
      model: "pro",
      role: `${act.key} · 创意总监`,
      prompt: [
        "你是「创意总监」：你是工作室的创意总监，替总导演兼制片人主持提案会，这几个方案都不是你写的，定稿交总导演签字。你最看重想象力：视觉形式新鲜、紧扣主题/歌词本身、有明确的核心画面机制、看完记得住；其次才是实现成本。性格：眼光挑剔，不和稀泥，敢选最大胆且自洽的那个，同时写清技术风险与执行边界；目标是获奖级别的商业动态设计作品（house-style §0），明确指出每个方案离它差在哪。",
        `读完三份提案：${ANGLES.map((a) => `${project}/work/pitch/${act.key}_${a.key}.md`).join("、")}，对照 ${P("house-style.md")} 选出主方案，写定稿说明到 ${project}/work/pitch/${act.key}_pick.md。`,
      ].join("\n\n"),
    });
    return { key: act.key, pitches, pick };
  })
);

let slate = null;
if (acts.length > 1) {
  slate = await agent({
    model: "pro",
    role: "执行制片 · 全片统筹",
    prompt: [
      "你是「执行制片」：你是工作室的执行制片，替总导演兼制片人统筹整支片的提案。性格：冷静、统筹全局，眼里是整支片的起承转合和节奏变化，而不是某一段的得失；核查各幕的视觉媒介、调色弧线、主字体和跨幕转场是否撞车。",
      `审阅所有幕次定稿：${acts.map((a) => `${project}/work/pitch/${a.key}_pick.md`).join("、")}，输出全片冲突核查与节奏统筹到 ${project}/work/pitch/SLATE.md。`,
    ].join("\n\n"),
  });
}

return { picks, slate };
