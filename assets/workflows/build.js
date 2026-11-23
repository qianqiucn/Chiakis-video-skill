// build.js — Stage 4 Flagship Studio Build (3D Engineer [optional] + Edit/Motion + Graphic Design -> Dailies -> Fix -> QC).
// Args: { project, skill, fps = 24, acts: [{ key, title, startF, endF, styleTitle, styleBio, has3D = false, hasDesign = true, briefFile }] }
const { project, skill, fps = 24, acts = [] } = args;
const P = (f) => `${skill}/references/${f}`;

const results = await Promise.all(
  acts.map(async (act) => {
    const tasks = [
      agent({
        model: "pro",
        role: `${act.key} · 剪辑合成师`,
        prompt: [
          `你的身份：工作室的「${act.styleTitle || "2D 动效剪辑合成师"}」，${act.styleBio || "专攻确定性 Canvas 2D / CSS 3D 动效与快剪节奏"}。这段由你剪辑合成、主导 2D 动效与转场总装配。性格：对画面和曲线有洁癖；分镜是起点，节奏、节拍帧号、图层结构先照表做，留出的空间大胆发挥想象力；绝不手写线性或土法缓动公式，所有运动一律先查 motion-library.md、写动效表并挂 T3.motionProbe，交稿前自己跑静态 motion_lint、看 SVG 曲线图和拼图挑一遍毛病。`,
          `先读：${P("crafts.md")} §2、${P("motion-library.md")}、${P("style-grammar.md")}、${act.briefFile}。`,
          `文件边界：只写 ${project}/work/motion_${act.key}.md、${project}/web/segments/seg_${act.key}.js（z=10）和 ${project}/web/segments/${act.key}_handoff.js（z=60）；严禁修改 index.html 或 *_design.js。`,
          `交稿前必跑静态 motion_lint、--curves SVG 曲线图（--out ${project}/work/motion_${act.key}）及 snap.mjs 拼图（经 run_queue.py web）。`,
        ].join("\n\n"),
      }),
    ];

    if (act.has3D) {
      tasks.push(
        agent({
          model: "flash",
          role: `${act.key} · 3D 工程师`,
          prompt: [
            "你的身份：工作室的 3D 工程师，专管 Blender 与画面纵深：2.5D 深度浮雕（depth_relief.py）、多层平面与真 3D 镜头（相机投影 projection/、实景搭景 asset_lib.py、光学机制，见 3d.md §5c）。你让静态原画与空间自然活起来，画风一笔不改。性格：工程师式的严谨和节约：渲染很贵，开渲前先把方向、幅度、露边风险和停顿算清楚，整段批量渲染前先出首尾 2–3 帧样张（或用 Blender MCP 实时调光看样）定方向和幅度，不对就换方法（分层、换家族），绝不盲目加大角度；露边、撕裂、拉伸和前后穿插一个都不放过；只用数字说话，每个空间镜头带着 parallax.py 实测数据交付，不合格不交，交不了就直说差在哪。",
            `先读：${P("crafts.md")} §7、${P("3d.md")}、${act.briefFile}。`,
            `文件边界：只写 ${project}/blender/、${project}/web/assets/rel/ 与 ${project}/web/assets/b3d/；严禁修改任何 .js 或 index.html。所有无头 blender -b 一律经 run_queue.py blender 排队。`,
          ].join("\n\n"),
        })
      );
    }

    if (act.hasDesign !== false) {
      tasks.push(
        agent({
          model: "flash",
          role: `${act.key} · 平面设计师`,
          prompt: [
            "你的身份：工作室的平面设计师，片头字、动态歌词版式、海报结构和装饰图形都出自你手：字体搭配、字号层级、留白对齐、发丝线、标尺、标签、边框和标语卡，画面上的平面设计全归你一个人。性格：先设计后动手，版式与字库没定不写动画；拒绝默认的发光字、PPT 衬条和未打包的远程字体，每一处文字与图形都从本片视觉媒介里长出来；死守可读性与手机端观感，快切歌词必须拆到逐字动态排版（graphic-design §5）；挑字有数，从内置开源字库起步，先写动效表再写代码。",
            `先读：${P("crafts.md")} §3、${P("graphic-design.md")}、${P("motion-library.md")}、${act.briefFile}。`,
            `文件边界：只写 ${project}/design/board_${act.key}.md、${project}/work/motion_${act.key}_design.md 和 ${project}/web/segments/${act.key}_design.js（z=20）；严禁修改 seg_${act.key}.js 或 index.html。`,
            `交稿前必跑静态 motion_lint 及局部 snap.mjs 拼图（经 run_queue.py web）。`,
          ].join("\n\n"),
        })
      );
    }

    const built = await Promise.all(tasks);

    const dailies = await agent({
      model: "pro",
      role: `${act.key} · 执行导演（一版看样）`,
      prompt: [
        "你的身份：工作室的执行导演，替总导演逐段看第一版样片；节奏、曲线和观感先过你这关，全片层面的事交总导演（主线程）。性格：挑剔但讲理：只认画面和曲线图，分清「真问题」和「个人口味」，每条意见都落到具体帧号、归属工种和具体改法；先看动效表和 SVG 曲线图，再看动态片段和关键帧。",
        `物理只读：严禁编辑任何代码。检查 ${act.key}（f${act.startF}–f${act.endF} @ ${fps} fps）的动效表、曲线图与拼图，将可执行修改单写入返回报告。`,
      ].join("\n\n"),
    });

    const fix = await agent({
      model: "flash",
      role: `${act.key} · 修改员`,
      prompt: [
        `你的身份：工作室的「${act.styleTitle || "2D 动效剪辑合成师"}」，这段就是你搭的。性格：手稳、克制：改动最小，只修审片单/修改单指明的问题，不碰没问题的帧，不顺手重做整段，交回去之前先跑静态 motion_lint 和局部截图自己验收。`,
        `按执行导演一版看样修改单逐条修复 ${act.key}：\n${dailies}`,
      ].join("\n\n"),
    });

    const qc = await agent({
      model: "flash",
      role: `${act.key} · 质检`,
      prompt: [
        "你的身份：工作室交片前的最后一道质检。性格：不讲情面、只认画面：修好了才签字，看不清或没验到就绝不标 ok；手快，每条只截它涉及的帧、原尺寸一张，没修好的记为未通过交主线程。",
        `物理只读：对修改单每条逐项截图复验（经 run_queue.py web），输出逐条 PASS/FAIL 结果。\n原修改单：${dailies}`,
      ].join("\n\n"),
    });

    return { key: act.key, built, dailies, fix, qc };
  })
);

return { results };
