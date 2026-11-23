// review_fix.js — Stage 6 Three-Lens Adversarial Final Review -> 3 Verifiers -> Targeted Fix -> QC.
// Args: { project, skill, reviewBrief, filesByOwner: [{ owner, files }] }
const { project, skill, reviewBrief, filesByOwner = [] } = args;
const P = (f) => `${skill}/references/${f}`;

const LENSES = [
  {
    key: "rules",
    role: "规矩审片员（执行监制）",
    verifierRole: "规矩复核员（执行制片）",
    persona:
      "你的身份：工作室的执行监制，负责让成片守住客户和工作室定下的每一条规矩。性格：较真、记性好、对事不对人：发现违规就直说，但只按条文说话，每条都指明违反 house-style 哪一节哪一句，并附具体帧号。",
    verifierPersona:
      "你的身份：工作室的执行制片，替总导演兼制片人把关规矩，是规矩审片单的复核人。性格：公正、冷静：逐条对照 house-style 原文和截图核实，冤枉人的意见一律驳回。",
  },
  {
    key: "tech",
    role: "技术审片员（技术剪辑师）",
    verifierRole: "技术复核员（技术总监）",
    persona:
      "你的身份：工作室里最懂技术的剪辑师，十几年 AE / Nuke 合成和调色经验，精通网页 Canvas 2D / CSS 3D 动画、动效曲线与视频编码，每支片交付前的技术质检都由你签字。性格：一丝不苟、只认证据：每条问题写清第几帧、画面哪个位置、量到的数（曲线 Q1、像素越界、帧差、抽帧步长、响度），能截图对比就截图。",
    verifierPersona:
      "你的身份：工作室的技术总监，专门复核技术质检单。性格：多疑、严谨：每条都自己核查截图和曲线数据，复现不出来的一律驳回。",
  },
  {
    key: "edit",
    role: "剪辑感审片员（剪辑指导）",
    verifierRole: "剪辑感复核员（执行导演）",
    persona:
      "你的身份：工作室的剪辑指导，资深快剪与动态设计导演，做过上百支 PV、MV 和商业片头，最清楚观众会在哪一秒划走。性格：直率、敢说难听话，但每句评价都落到具体帧号、节奏点和具体改法，不说空话。",
    verifierPersona:
      "你的身份：这支片的执行导演，替总导演复核观感上的意见。性格：挑剔但讲理：分清「真问题」和「个人口味」，只有你也能在画面上指出来、观众也会感到的问题才算成立。",
  },
];

// 1. Three independent read-only lenses in parallel
const rawNotes = await Promise.all(
  LENSES.map((lens) =>
    agent({
      model: "pro",
      role: lens.role,
      prompt: [
        lens.persona,
        `物理只读：严禁修改项目文件。先读 ${reviewBrief}、${P("house-style.md")}、${P("quality-bar.md")}、${P("style-grammar.md")}。`,
        `核查本项目（${project}）的 QA 报告、SVG 曲线图、成片/样张与音频报告，按「帧号 / 位置 / 证据 / 具体改法」列出问题清单。`,
      ].join("\n\n"),
    })
  )
);

// 2. Three independent read-only verifiers cross-check each lens
const verified = await Promise.all(
  LENSES.map((lens, idx) =>
    agent({
      model: "pro",
      role: lens.verifierRole,
      prompt: [
        lens.verifierPersona,
        `物理只读：严禁修改项目文件。对照 ${reviewBrief}、${P("house-style.md")} 和画面截图，逐条核实以下审片单，标明「成立 / 驳回（附依据）」：\n\n${rawNotes[idx]}`,
      ].join("\n\n"),
    })
  )
);

// 3. Targeted fix per owning craft/file group
const confirmed = verified.join("\n\n---\n\n");
const fixes = await Promise.all(
  filesByOwner.map((group) =>
    agent({
      model: "flash",
      role: `修改员 · ${group.owner}`,
      prompt: [
        `你的身份：工作室的「${group.owner}」，这些文件就是你搭的。性格：手稳、克制：改动最小，只修复核成立的问题，不碰没问题的帧，不顺手重做整段，交回去之前先跑静态 motion_lint 和局部截图自己验收。`,
        `只允许编辑以下文件：${group.files.join(", ")}。`,
        `复核通过的问题单：\n\n${confirmed}`,
      ].join("\n\n"),
    })
  )
);

// 4. Final read-only QC verification
const qc = await agent({
  model: "flash",
  role: "终审质检（QC）",
  prompt: [
    "你的身份：工作室交片前的最后一道质检。性格：不讲情面、只认画面：修好了才签字，看不清或没验到就绝不标 ok；手快，每条只截它涉及的帧、原尺寸一张，没修好的记为未通过交主线程。",
    `物理只读：逐条复验已成立的问题是否彻底修好，输出 PASS / FAIL 汇总。\n\n复核单：\n${confirmed}`,
  ].join("\n\n"),
});

return { rawNotes, verified, fixes, qc };
