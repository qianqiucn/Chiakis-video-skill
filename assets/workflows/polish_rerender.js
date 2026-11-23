// polish_rerender.js — Stages 10–12 Closed Loop: Independent 7-Dim Scorecard (on V1 render) -> Targeted Polish Round -> Read-Only QC.
// After this workflow finishes, the director re-renders the final 1080p + 2K FLAC master and verifies Gate B2.
// Args: { project, skill, scoreBrief, renderVideo, filesByOwner: [{ owner, files }], skipFixIfPass = true }
const { project, skill, scoreBrief, renderVideo, filesByOwner = [], skipFixIfPass = true } = args;
const P = (f) => `${skill}/references/${f}`;

// 1. Physically read-only Independent 7-Dim Scorecard on the V1 audiovisual render
const scoreV1 = await agent({
  model: "pro",
  role: "独立成片评分员（一版打分）",
  prompt: [
    "你的身份：资深动态设计评委（Motionographer 编辑、Buck / ManvsMachine 创意总监、头部动态设计博主这一级）。片子不是你做的。目标水准是获奖级别的商业作品（house-style §0）。性格：下手要狠、说话要具体、绝不客气虚高；先量规格与曲线图再看画面，按 7 维严格打分（每维 ≥ 8 分及格，不算平均），每项给帧号/秒数证据。",
    `物理只读：严禁编辑任何代码。按 ${scoreBrief} 与 ${P("quality-bar.md")} 严格审查一版带声成片（${renderVideo}）、QA 报告、SVG 曲线图与母带报告，输出 7 维打分表与 Verdict（DELIVER 或 REVISE）并逐条列出所有扣分帧号与可落地的修改建议。`,
  ].join("\n\n"),
});

const passedV1 = /Verdict:\s*DELIVER\b/i.test(String(scoreV1)) && skipFixIfPass;
if (passedV1 || !filesByOwner.length) {
  return { scoreV1, skippedPolish: true, fixes: [], qc: null };
}

// 2. Targeted Polish Round per owning craft/file group (minimal surgical fixes)
const fixes = await Promise.all(
  filesByOwner.map((group) =>
    agent({
      model: "flash",
      role: `定向修改员 · ${group.owner}`,
      prompt: [
        `你的身份：工作室的「${group.owner}」，这段就是你搭的。性格：手稳、克制：改动最小，只修审片单/修改单指明的问题，不碰没问题的帧，不顺手重做整段，交回去之前先跑静态 motion_lint 和局部截图自己验收。`,
        `对照 ${P("crafts.md")} 与 ${scoreBrief}，文件边界：只允许编辑以下文件：${group.files.join(", ")}。`,
        `根据一版独立评分卡的所有扣分项（尤其是 < 8 分维度与明确缺陷）执行一轮最小化定向修复：\n\n${scoreV1}`,
      ].join("\n\n"),
    })
  )
);

// 3. Physically read-only QC Recheck on every fixed item before re-rendering V2 final
const qc = await agent({
  model: "flash",
  role: "复修质检（QC）",
  prompt: [
    "你的身份：工作室交片前的最后一道质检。性格：不讲情面、只认画面：修好了才签字，看不清或没验到就绝不标 ok；手快，每条只截它涉及的帧、原尺寸一张，没修好的记为未通过交主线程。",
    `物理只读：按 ${P("crafts.md")} §6 与 ${P("quality-bar.md")} 对照一版独立评分卡的每一条扣分项，逐条截原尺寸图复验是否彻底修好，输出 PASS / FAIL 清单，确认无误后交总导演执行重渲染与 Gate B2 终验：\n\n${scoreV1}`,
  ].join("\n\n"),
});

return { scoreV1, skippedPolish: false, fixes, qc };
