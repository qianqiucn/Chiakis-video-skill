// polish_rerender.js — Stages 11–12 Closed Loop: Independent 7-Dim Scorecard -> Targeted Polish Round -> Read-Only QC.
// Validates truncation-safe structured scorecard JSON + `<!-- SCORE_COMPLETE -->` sentinel; flags INCOMPLETE_REVIEW if missing.
// Args: { project, skill, scoreBrief, renderVideo, filesByOwner: [{ owner, files }], taskId = "v1", skipFixIfPass = true }
const { project, skill, scoreBrief, renderVideo, filesByOwner = [], taskId = "v1", skipFixIfPass = true } = args;
const P = (f) => `${skill}/references/${f}`;
const DIMS = ["concept", "motion", "rhythm", "typography", "depth", "sound", "technical"];

function parseScorecard(rawText) {
  const txt = String(rawText || "");
  const hasSentinel = txt.includes("<!-- SCORE_COMPLETE -->");
  let parsed = null;
  const m = txt.match(/```(?:scorecard-json|json)\s*(\{[\s\S]*?\})\s*```/i);
  if (m) { try { parsed = JSON.parse(m[1]); } catch {} }
  const dims = {};
  if (parsed && parsed.dimensions && typeof parsed.dimensions === "object") {
    for (const k of DIMS) {
      const v = parsed.dimensions[k];
      if (typeof v === "number" && v >= 1 && v <= 10) dims[k] = Math.round(v);
    }
  }
  let verdict = String((parsed && parsed.verdict) || "").toUpperCase();
  if (verdict !== "DELIVER" && verdict !== "REVISE") {
    const mv = txt.match(/Verdict:\s*(DELIVER|REVISE)\b/i);
    verdict = mv ? mv[1].toUpperCase() : "";
  }
  const missing = DIMS.filter((k) => !(k in dims));
  const complete = missing.length === 0 && (verdict === "DELIVER" || verdict === "REVISE") && hasSentinel;
  const allGe8 = complete && DIMS.every((k) => dims[k] >= 8);
  if (complete && !allGe8 && verdict === "DELIVER") verdict = "REVISE";
  return {
    task_id: taskId,
    status: complete ? verdict : "INCOMPLETE_REVIEW",
    complete,
    has_sentinel: hasSentinel,
    missing_dimensions: missing,
    host_review_mode: (parsed && parsed.host_review_mode) || "unknown",
    verdict: verdict || "INCOMPLETE",
    dimensions: dims,
    blocking_issues: (parsed && parsed.blocking_issues) || [],
  };
}

// 1. Physically read-only Independent 7-Dim Scorecard on the V1 audiovisual render
const scoreV1 = await agent({
  model: "pro",
  role: "独立成片评分员（一版打分）",
  prompt: [
    "你的身份：资深动态设计评委（Motionographer 编辑、Buck / ManvsMachine 创意总监、头部动态设计博主这一级）。片子不是你做的。目标水准是获奖级别的商业作品（house-style §0）。性格：下手要狠、说话要具体、绝不客气虚高；先量规格与曲线图再看画面，按 7 维严格打分（每维 ≥ 8 分及格，不算平均），每项给帧号/秒数证据。",
    `物理只读：严禁编辑任何代码。按 ${scoreBrief} 与 ${P("quality-bar.md")} 严格审查一版带声成片（${renderVideo}）、QA 报告、SVG 曲线图与母带报告（先声明本宿主审片通道 playback/stills/metrics；Gemini 宿主必须直接多模态观看 ${renderVideo} 并直听关键音频，Claude/Codex/WorkBuddy 宿主走传统频谱图 + 转场帧对/关键帧拼图 + 曲线/数值报告）。`,
    `【防截断输出要求】必须在回复最顶部（前 25 行）先输出 \`\`\`scorecard-json\`\`\`（含 task_id='${taskId}'、host_review_mode、verdict 与全部 7 维整数分）、Verdict 行与 7 维总表，其后再写逐帧建议，末尾附 \`<!-- SCORE_COMPLETE -->\`。`,
  ].join("\n\n"),
});

const scoreMeta = parseScorecard(scoreV1);
if (!scoreMeta.complete) {
  return { status: "INCOMPLETE_REVIEW", scoreMeta, scoreV1, skippedPolish: true, fixes: [], qc: null };
}
if ((scoreMeta.verdict === "DELIVER" && skipFixIfPass) || !filesByOwner.length) {
  return { status: scoreMeta.verdict, scoreMeta, scoreV1, skippedPolish: true, fixes: [], qc: null };
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

return { status: "REVISED", scoreMeta, scoreV1, skippedPolish: false, fixes, qc };
