/* three_kit.js — Flagship Stylized Graphic-3D & Dual-3D Toolkit for Chiaki's-video-skill (requires lib/three/three.min.js).
 *
 * Designed specifically so 3D blends seamlessly into 2D kinetic typography PVs, graphic MVs, and Blender-paired films
 * with ZERO "plastic black-bg rotating cube" look and ZERO Chrome WebGL context exhaustion across multi-act timelines.
 *
 * Architecture:
 *   - ONE shared singleton THREE.WebGLRenderer per page (`T3.three.renderer()`), alpha:true, antialias:true,
 *     SRGBColorSpace + NoToneMapping so 2D graphic hex colours match verbatim.
 *   - Every primitive renders deterministically (pure function of frame/params) and blits onto any 2D Canvas ctx
 *     via `T3.three.blit(ctx, scene, camera)`, unlocking pixel-exact Z-sandwich compositing with 2D cutouts!
 *
 * Primitives (registered in references/motion-library.md):
 *   - T3.three.extrudeText(text, opts)     True 3D extruded CJK/JP/Latin typography (fonts.py glyph3d -> flat/toon/glass/wire)
 *   - T3.three.textRing(text, opts)        360° 3D cylindrical lyric ribbon with drawBack() / drawFront() Z-sandwich split
 *   - T3.three.textCorridor(items, opts)   3D kinetic typography tunnel / floating angled lyric poster slabs
 *   - T3.three.prismOverlay(opts)          Real-time chromatic glass prism / refractive crystal bars over live 2D canvas
 *   - T3.three.louverTransition(opts)      z=60 real-perspective 3D mechanical blinds / flipping tile transition
 *   - T3.three.field(opts)                 Stylized 3D graphic horizon grid + InstancedMesh monoliths / wireframes / rings
 *   - T3.three.relief(opts)                Real-time 2.5D depth-map mesh orbit/crane/push (zero-Blender relief & micro-cuts)
 *   - T3.three.stage(opts)                 Lightweight stylized 3D stage with grounded 2D cutout cards & soft contact shadows
 */
(function () {
  if (!window.T3) throw new Error('three_kit.js: load engine.js before lib/three_kit.js');
  const W0 = 1920, H0 = 1080;

  function reqTHREE() {
    if (!window.THREE) throw new Error('three_kit.js: load lib/three/three.min.js before lib/three_kit.js');
    return window.THREE;
  }

  // ---- Singleton Shared WebGLRenderer (prevents Chrome's 8-16 WebGL context limit across multi-act films) ----
  let _renderer = null;
  let _rw = W0, _rh = H0;
  function getRenderer(w = W0, h = H0) {
    const THREE = reqTHREE();
    const scale = Math.max(0.5, Math.min(1.5, +(window.T3_THREE_SCALE || 1)));
    const tw = Math.round(w * scale), th = Math.round(h * scale);
    if (!_renderer) {
      _renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        preserveDrawingBuffer: true,
        powerPreference: 'high-performance',
      });
      _renderer.setPixelRatio(1);
      _renderer.setSize(tw, th, false);
      if ('outputColorSpace' in _renderer && THREE.SRGBColorSpace) {
        _renderer.outputColorSpace = THREE.SRGBColorSpace;
      }
      _renderer.toneMapping = THREE.NoToneMapping;
      _renderer.setClearColor(0x000000, 0);
      _rw = tw; _rh = th;
    } else if (_rw !== tw || _rh !== th) {
      _renderer.setSize(tw, th, false);
      _rw = tw; _rh = th;
    }
    return _renderer;
  }

  function blit(ctx, scene, camera, opts = {}) {
    const w = opts.width || W0, h = opts.height || H0;
    const r = getRenderer(w, h);
    r.setClearColor(opts.clearColor != null ? opts.clearColor : 0x000000, opts.clearAlpha != null ? opts.clearAlpha : 0);
    r.clear(true, true, true);
    r.render(scene, camera);
    ctx.save();
    if (opts.alpha != null) ctx.globalAlpha *= opts.alpha;
    if (opts.composite) ctx.globalCompositeOperation = opts.composite;
    ctx.drawImage(r.domElement, opts.dx || 0, opts.dy || 0, opts.dw || ctx.canvas.width, opts.dh || ctx.canvas.height);
    ctx.restore();
  }

  function mount(layer, opts = {}) {
    const w = opts.width || W0, h = opts.height || H0;
    const cv = T3.el('canvas', { position: 'absolute', left: 0, top: 0, width: w + 'px', height: h + 'px', pointerEvents: 'none' }, layer);
    cv.width = w; cv.height = h;
    const ctx = cv.getContext('2d');
    return {
      canvas: cv,
      ctx,
      clear() { ctx.clearRect(0, 0, w, h); },
      blit(scene, camera, bopts) { blit(ctx, scene, camera, bopts); },
    };
  }

  function makeCamera(opts = {}) {
    const THREE = reqTHREE();
    const cam = new THREE.PerspectiveCamera(opts.fov || 38, (opts.width || W0) / (opts.height || H0), opts.near || 0.05, opts.far || 200);
    cam.position.set(opts.x || 0, opts.y || 0, opts.z != null ? opts.z : 6);
    cam.lookAt(opts.lookX || 0, opts.lookY || 0, opts.lookZ || 0);
    return cam;
  }

  function applyCam(cam, s = {}) {
    if (!s) return;
    if (s.fov != null && cam.fov !== s.fov) { cam.fov = s.fov; cam.updateProjectionMatrix(); }
    if (s.camX != null || s.camY != null || s.camZ != null) {
      cam.position.set(s.camX != null ? s.camX : cam.position.x, s.camY != null ? s.camY : cam.position.y, s.camZ != null ? s.camZ : cam.position.z);
    }
    cam.lookAt(s.lookX || 0, s.lookY || 0, s.lookZ || 0);
    if (s.roll) cam.rotateZ(s.roll);
  }

  function makeToonGradient(THREE, steps = 3) {
    const data = new Uint8Array(steps * 4);
    for (let i = 0; i < steps; i++) {
      const v = Math.round(95 + (160 * i) / Math.max(1, steps - 1));
      data[i * 4] = v; data[i * 4 + 1] = v; data[i * 4 + 2] = v; data[i * 4 + 3] = 255;
    }
    const tex = new THREE.DataTexture(data, steps, 1, THREE.RGBAFormat);
    tex.minFilter = THREE.NearestFilter;
    tex.magFilter = THREE.NearestFilter;
    tex.generateMipmaps = false;
    tex.needsUpdate = true;
    return tex;
  }

  // ---- Auto-winding contour converter for TTF (CW solid) & OTF/CFF (CCW solid) CJK/Latin glyphs ----
  function glyphCmdsToShapes(THREE, cmds, unitScale) {
    const sp = new THREE.ShapePath();
    for (const c of cmds) {
      const op = c[0];
      if (op === 'M') sp.moveTo(c[1] * unitScale, c[2] * unitScale);
      else if (op === 'L') sp.lineTo(c[1] * unitScale, c[2] * unitScale);
      else if (op === 'Q') sp.quadraticCurveTo(c[1] * unitScale, c[2] * unitScale, c[3] * unitScale, c[4] * unitScale);
      else if (op === 'C') sp.bezierCurveTo(c[1] * unitScale, c[2] * unitScale, c[3] * unitScale, c[4] * unitScale, c[5] * unitScale, c[6] * unitScale);
      else if (op === 'Z' && sp.currentPath) sp.currentPath.closePath();
    }
    // Determine solid contour winding automatically from the subpath with largest absolute area
    let maxAbs = -1, solidCW = true;
    for (const sub of sp.subPaths) {
      const pts = sub.getPoints(8);
      if (pts.length < 3) continue;
      const area = THREE.ShapeUtils.area(pts); // <0 means CW in Three.js ShapeUtils
      if (Math.abs(area) > maxAbs) { maxAbs = Math.abs(area); solidCW = area < 0; }
    }
    // In Three.js ShapePath.toShapes(isCCW): pass true when solid shapes are CW? Actually Three.js:
    // isCCW=false expects solid shapes to be CW (area < 0), isCCW=true expects solid shapes to be CCW (area > 0).
    return sp.toShapes(!solidCW);
  }

  // ============================================================================================================
  // 1. T3.three.extrudeText — True 3D Extruded CJK / JP / Latin Typography (flat / toon / glass / wire)
  // ============================================================================================================
  function extrudeText(text, opts = {}) {
    const THREE = reqTHREE();
    const pack = opts.glyphPack || (window.T3_GLYPHS_3D && (window.T3_GLYPHS_3D[opts.font] || Object.values(window.T3_GLYPHS_3D)[0]));
    if (!pack || !pack.glyphs) {
      throw new Error(`T3.three.extrudeText: missing glyph3d pack for "${opts.font || 'default'}". Run: python -X utf8 scripts/fonts.py glyph3d <project> "<Font>" "${text}"`);
    }
    const style = opts.style || 'flat'; // 'flat' | 'toon' | 'glass' | 'wire'
    const size = opts.size || 1.0;
    const depth = opts.depth != null ? opts.depth : size * 0.24;
    const bevel = opts.bevel != null ? opts.bevel : size * 0.022;
    const tracking = opts.tracking != null ? opts.tracking : (opts.letterSpacing != null ? opts.letterSpacing : size * 0.06);
    const unitScale = size / (pack.upm || 1000);
    const faceCol = new THREE.Color(opts.faceColor || '#f7f4ec');
    const sideCol = new THREE.Color(opts.sideColor || '#191d28');
    const edgeCol = new THREE.Color((typeof opts.outline === 'string' ? opts.outline : null) || opts.edgeColor || '#0d1018');
    const accentCol = new THREE.Color(opts.accentColor || '#ff3d68');

    const scene = new THREE.Scene();
    const cam = makeCamera({ fov: opts.fov || 34, z: opts.camZ != null ? opts.camZ : 6.2 });

    // Clean graphic lighting for toon/glass
    const keyL = new THREE.DirectionalLight(0xffffff, 1.35); keyL.position.set(4, 6, 7); scene.add(keyL);
    const rimL = new THREE.DirectionalLight(accentCol, 0.75); rimL.position.set(-5, -2, 3); scene.add(rimL);
    scene.add(new THREE.AmbientLight(0xffffff, 0.65));

    let matFace, matSide;
    if (style === 'flat') {
      // Crisp 2D poster front + subtly directional-shaded contrasting extruded walls (zero plastic glare!)
      matFace = new THREE.MeshBasicMaterial({ color: faceCol });
      matSide = new THREE.ShaderMaterial({
        uniforms: {
          uBase: { value: sideCol },
          uAccent: { value: accentCol },
          uMix: { value: opts.sideShade != null ? opts.sideShade : 0.28 },
        },
        vertexShader: `varying vec3 vN; void main(){ vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
        fragmentShader: `uniform vec3 uBase, uAccent; uniform float uMix; varying vec3 vN;
          void main(){
            float d = clamp(dot(normalize(vN), normalize(vec3(0.55, 0.72, 0.42))), 0.0, 1.0);
            float stepSh = floor(d * 3.0 + 0.35) / 3.0;
            vec3 c = mix(uBase * 0.76, mix(uBase * 1.24, uAccent, uMix), stepSh);
            gl_FragColor = vec4(c, 1.0);
          }`,
      });
    } else if (style === 'toon') {
      const grad = makeToonGradient(THREE, 3);
      matFace = new THREE.MeshToonMaterial({ color: faceCol, gradientMap: grad });
      matSide = new THREE.MeshToonMaterial({ color: sideCol, gradientMap: grad });
    } else if (style === 'glass') {
      const glassMat = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: true,
        uniforms: {
          uFace: { value: faceCol },
          uAccent: { value: accentCol },
          uOpacity: { value: opts.opacity != null ? opts.opacity : 0.86 },
        },
        vertexShader: `varying vec3 vN, vV; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`,
        fragmentShader: `uniform vec3 uFace, uAccent; uniform float uOpacity; varying vec3 vN, vV;
          void main(){
            float fr = pow(1.0 - max(0.0, abs(dot(normalize(vN), normalize(vV)))), 2.2);
            float spec = pow(max(0.0, dot(reflect(-normalize(vec3(0.4,0.8,0.6)), normalize(vN)), normalize(vV))), 18.0);
            vec3 c = mix(uFace * 0.82, uAccent, fr * 0.65) + vec3(1.0) * (spec * 0.85 + fr * 0.35);
            gl_FragColor = vec4(c, clamp(uOpacity * (0.58 + fr * 0.42), 0.0, 1.0));
          }`,
      });
      matFace = glassMat; matSide = glassMat;
    } else {
      // 'wire' — translucent graphic core + razor sharp wireframe edges
      matFace = new THREE.MeshBasicMaterial({ color: faceCol, transparent: true, opacity: opts.coreOpacity != null ? opts.coreOpacity : 0.14, depthWrite: false });
      matSide = matFace;
    }

    const root = new THREE.Group();
    scene.add(root);
    const chars = [...String(text)];
    const glyphs = [];
    const widths = chars.map((ch) => {
      const g = pack.glyphs[ch];
      return g ? (g.w || 600) * unitScale : size * 0.52;
    });
    const totalW = widths.reduce((a, b) => a + b, 0) + Math.max(0, chars.length - 1) * tracking;
    let cursorX = -totalW * 0.5;
    const midY = ((pack.asc || 800) + (pack.desc || -200)) * 0.5 * unitScale;

    for (let i = 0; i < chars.length; i++) {
      const ch = chars[i];
      const gw = widths[i];
      const piv = new THREE.Group();
      const baseX = cursorX + gw * 0.5;
      piv.position.set(baseX, 0, 0);
      piv.userData = { char: ch, index: i, baseX, width: gw };
      const g = pack.glyphs[ch];
      if (g && g.cmds && g.cmds.length) {
        const shapes = glyphCmdsToShapes(THREE, g.cmds, unitScale);
        if (shapes.length) {
          const geo = new THREE.ExtrudeGeometry(shapes, {
            depth,
            bevelEnabled: bevel > 0,
            bevelThickness: bevel,
            bevelSize: bevel * 0.72,
            bevelSegments: style === 'glass' ? 3 : 2,
            curveSegments: 10,
          });
          geo.translate(-gw * 0.5, -midY, -depth * 0.5);
          const mesh = new THREE.Mesh(geo, [matFace, matSide]);
          piv.add(mesh);

          if (style === 'toon' && opts.outline !== false) {
            const outW = opts.outlineWidth || 0.045;
            const outMat = new THREE.MeshBasicMaterial({ color: edgeCol, side: THREE.BackSide });
            const outMesh = new THREE.Mesh(geo, outMat);
            outMesh.scale.set(1 + outW, 1 + outW, 1 + outW * 0.9);
            piv.add(outMesh);
          }
          if (style === 'wire' || opts.edges) {
            const eg = new THREE.EdgesGeometry(geo, style === 'wire' ? 20 : 32);
            const em = new THREE.LineBasicMaterial({ color: style === 'wire' ? faceCol : edgeCol, transparent: true, opacity: style === 'wire' ? 0.95 : 0.7 });
            piv.add(new THREE.LineSegments(eg, em));
          }
        }
      }
      root.add(piv);
      glyphs.push(piv);
      cursorX += gw + tracking;
    }

    return {
      scene, camera: cam, group: root, glyphs, totalWidth: totalW,
      draw(ctx, state = {}) {
        root.position.set(state.x || 0, state.y || 0, state.z || 0);
        root.rotation.set(state.rotX || 0, state.rotY || 0, state.rotZ || 0);
        const sc = state.scale != null ? state.scale : 1;
        root.scale.set(sc, sc, sc);
        if (typeof state.each === 'function') {
          for (let i = 0; i < glyphs.length; i++) state.each(glyphs[i], i, glyphs.length);
        }
        applyCam(cam, state);
        blit(ctx, scene, cam, state);
      },
    };
  }

  // ============================================================================================================
  // 2. T3.three.textRing — 360° 3D Cylindrical Lyric Ribbon with Z-Sandwich Back/Front Split!
  // ============================================================================================================
  function textRing(text, opts = {}) {
    const THREE = reqTHREE();
    const radius = opts.radius || 2.15;
    const height = opts.height || 0.46;
    const repeat = opts.repeat || 3;
    const texW = opts.texW || 2400, texH = opts.texH || 256;

    // Bake ultra-crisp local T3.fonts lyric band onto offscreen canvas, auto-fitting texW so repeats NEVER overlap
    const unit = String(text) + (opts.sep != null ? opts.sep : '  ✦  ');
    const fontStr = opts.font || `900 ${Math.round(texH * 0.56)}px ${window.T3 && T3.fonts ? T3.fonts.use(opts.fontFamily || 'sans-serif', 'sans-serif') : 'sans-serif'}`;
    const cv = document.createElement('canvas');
    const c0 = cv.getContext('2d');
    c0.font = fontStr;
    const measuredUnit = Math.max(1, c0.measureText(unit).width);
    const minTexW = Math.ceil(measuredUnit * repeat * 1.06);
    const finalTexW = Math.min(8192, Math.max(texW, minTexW));
    cv.width = finalTexW; cv.height = texH;
    const c = cv.getContext('2d');
    if (opts.bandColor) {
      c.fillStyle = opts.bandColor;
      c.fillRect(0, 14, finalTexW, texH - 28);
    }
    if (opts.ruleColor !== false) {
      c.fillStyle = opts.ruleColor || opts.color || '#f8f5ee';
      c.fillRect(0, 14, finalTexW, 6);
      c.fillRect(0, texH - 20, finalTexW, 6);
    }
    c.font = fontStr;
    c.textBaseline = 'middle';
    c.textAlign = 'center';
    c.fillStyle = opts.color || '#f8f5ee';
    const step = finalTexW / repeat;
    const maxW = step * 0.94;
    for (let i = 0; i < repeat; i++) {
      c.fillText(unit, step * (i + 0.5), texH * 0.52, maxW);
    }

    const tex = new THREE.CanvasTexture(cv);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    if (THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;

    const geo = new THREE.CylinderGeometry(radius, radius, height, 96, 1, true);
    const matBack = new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.BackSide, depthWrite: false, opacity: opts.backOpacity != null ? opts.backOpacity : 0.72 });
    const matFront = new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.FrontSide, depthWrite: false, opacity: opts.frontOpacity != null ? opts.frontOpacity : 1.0 });

    const sceneBack = new THREE.Scene(), sceneFront = new THREE.Scene();
    const pivotBack = new THREE.Group(), pivotFront = new THREE.Group();
    const meshBack = new THREE.Mesh(geo, matBack);
    const meshFront = new THREE.Mesh(geo, matFront);
    pivotBack.add(meshBack); pivotFront.add(meshFront);
    sceneBack.add(pivotBack); sceneFront.add(pivotFront);
    const cam = makeCamera({ fov: opts.fov || 36, z: opts.camZ != null ? opts.camZ : 6.2 });

    function sync(state = {}) {
      for (const p of [pivotBack, pivotFront]) {
        p.position.set(state.x || 0, state.y || 0, state.z || 0);
        p.rotation.set(state.tiltX || 0, 0, state.tiltZ || 0);
        const sc = state.scale != null ? state.scale : 1;
        p.scale.set(sc, sc, sc);
      }
      meshBack.rotation.y = state.rotY || 0;
      meshFront.rotation.y = state.rotY || 0;
      if (state.backOpacity != null) matBack.opacity = state.backOpacity;
      if (state.frontOpacity != null) matFront.opacity = state.frontOpacity;
      applyCam(cam, state);
    }

    return {
      camera: cam,
      drawBack(ctx, state = {}) { sync(state); blit(ctx, sceneBack, cam, state); },
      drawFront(ctx, state = {}) { sync(state); blit(ctx, sceneFront, cam, state); },
      drawBoth(ctx, state = {}) { sync(state); blit(ctx, sceneBack, cam, state); blit(ctx, sceneFront, cam, state); },
    };
  }

  // ============================================================================================================
  // 3. T3.three.textCorridor — 3D Kinetic Typography Tunnel / Floating Perspective Lyric Poster Slabs
  // ============================================================================================================
  function textCorridor(items, opts = {}) {
    const THREE = reqTHREE();
    const scene = new THREE.Scene();
    if (opts.fogColor) scene.fog = new THREE.Fog(opts.fogColor, opts.fogNear || 4, opts.fogFar || 22);
    const cam = makeCamera({ fov: opts.fov || 44, z: opts.camZ != null ? opts.camZ : 4.5, far: 120 });

    const meshes = [];
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      const cw = it.texW || 1024, ch = it.texH || 420;
      const cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
      const c = cv.getContext('2d');
      // High-craft poster card chrome
      c.fillStyle = it.bg || '#f6f3eb';
      c.fillRect(0, 0, cw, ch);
      c.strokeStyle = it.border || it.fg || '#15171e';
      c.lineWidth = 10;
      c.strokeRect(10, 10, cw - 20, ch - 20);
      if (it.accent) {
        c.fillStyle = it.accent;
        c.fillRect(24, 24, 18, ch - 48);
      }
      c.fillStyle = it.fg || '#15171e';
      c.font = it.font || `900 ${Math.round(ch * 0.34)}px sans-serif`;
      c.textBaseline = 'middle';
      c.textAlign = it.align || 'left';
      const tx = it.align === 'center' ? cw * 0.5 : 68;
      const maxTextW = it.align === 'center' ? cw - 120 : cw - 128;
      c.fillText(it.text || '', tx, it.sub ? ch * 0.42 : ch * 0.52, maxTextW);
      if (it.sub) {
        c.fillStyle = it.subColor || it.accent || '#556070';
        c.font = it.subFont || `700 ${Math.round(ch * 0.13)}px monospace`;
        c.fillText(it.sub, tx, ch * 0.74, maxTextW);
      }
      const tex = new THREE.CanvasTexture(cv);
      if (THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = 8;

      const pw = it.width || 3.4, ph = it.height || pw * (ch / cw);
      const geo = new THREE.PlaneGeometry(pw, ph);
      const mat = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide, transparent: true, opacity: it.opacity != null ? it.opacity : 1 });
      const m = new THREE.Mesh(geo, mat);
      m.position.set(it.x || 0, it.y || 0, it.z != null ? it.z : -i * 3.2);
      m.rotation.set(it.rotX || 0, it.rotY || 0, it.rotZ || 0);
      m.userData = { index: i, basePos: m.position.clone(), baseRot: m.rotation.clone(), spec: it };
      scene.add(m);
      meshes.push(m);
    }

    return {
      scene, camera: cam, cards: meshes,
      draw(ctx, state = {}) {
        if (typeof state.each === 'function') {
          for (let i = 0; i < meshes.length; i++) state.each(meshes[i], i);
        }
        applyCam(cam, state);
        blit(ctx, scene, cam, state);
      },
    };
  }

  // ============================================================================================================
  // 4. T3.three.prismOverlay — Real-Time Chromatic Glass Prism Bars Refracting Live 2D Canvas/Image!
  // ============================================================================================================
  function prismOverlay(opts = {}) {
    const THREE = reqTHREE();
    const scene = new THREE.Scene();
    const cam = makeCamera({ fov: opts.fov || 36, z: opts.camZ != null ? opts.camZ : 6.0 });
    const count = opts.count || 3;
    const dummy = document.createElement('canvas'); dummy.width = 4; dummy.height = 4;
    const bgTex = new THREE.CanvasTexture(dummy);
    bgTex.minFilter = THREE.LinearFilter;
    bgTex.magFilter = THREE.LinearFilter;
    if (THREE.SRGBColorSpace) bgTex.colorSpace = THREE.SRGBColorSpace;

    const prismMat = new THREE.ShaderMaterial({
      transparent: true,
      uniforms: {
        uBg: { value: bgTex },
        uRefract: { value: opts.refract != null ? opts.refract : 0.048 },
        uChroma: { value: opts.chroma != null ? opts.chroma : 0.016 },
        uTint: { value: new THREE.Color(opts.tint || '#dbeafe') },
        uOpacity: { value: opts.opacity != null ? opts.opacity : 0.94 },
      },
      vertexShader: `
        varying vec3 vN, vV;
        varying vec4 vClip;
        void main(){
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          vN = normalize(normalMatrix * normal);
          vV = normalize(-mv.xyz);
          vClip = projectionMatrix * mv;
          gl_Position = vClip;
        }`,
      fragmentShader: `
        uniform sampler2D uBg;
        uniform float uRefract, uChroma, uOpacity;
        uniform vec3 uTint;
        varying vec3 vN, vV;
        varying vec4 vClip;
        void main(){
          vec2 suv = (vClip.xy / vClip.w) * 0.5 + 0.5;
          vec3 N = normalize(vN);
          vec3 V = normalize(vV);
          vec2 off = N.xy * uRefract;
          float r = texture2D(uBg, clamp(suv + off + vec2(uChroma, 0.0), 0.002, 0.998)).r;
          float g = texture2D(uBg, clamp(suv + off, 0.002, 0.998)).g;
          float b = texture2D(uBg, clamp(suv + off - vec2(uChroma, 0.0), 0.002, 0.998)).b;
          vec3 refr = vec3(r, g, b);
          float fr = pow(1.0 - max(0.0, abs(dot(N, V))), 2.6);
          float spec = pow(max(0.0, dot(reflect(-normalize(vec3(0.45, 0.75, 0.5)), N), V)), 28.0);
          vec3 col = mix(refr, uTint, 0.12 + fr * 0.35) + vec3(1.0) * (spec * 0.95 + fr * 0.45);
          gl_FragColor = vec4(col, uOpacity);
        }`,
    });

    const bars = [];
    const shapes = opts.bars || Array.from({ length: count }, (_, i) => ({
      w: 0.42 + (i % 2) * 0.22, h: 4.8, d: 0.42,
      x: (i - (count - 1) * 0.5) * 1.45, y: 0, z: 0.2 * (i % 2),
      rotZ: -0.22,
    }));
    for (const s of shapes) {
      const geo = new THREE.BoxGeometry(s.w || 0.5, s.h || 4.6, s.d || 0.5);
      const m = new THREE.Mesh(geo, prismMat);
      m.position.set(s.x || 0, s.y || 0, s.z || 0);
      m.rotation.set(s.rotX || 0, s.rotY || 0, s.rotZ || 0);
      const eg = new THREE.EdgesGeometry(geo);
      m.add(new THREE.LineSegments(eg, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.55 })));
      scene.add(m);
      bars.push(m);
    }

    return {
      scene, camera: cam, bars, material: prismMat,
      draw(ctx, sourceCanvasOrImg, state = {}) {
        if (sourceCanvasOrImg) {
          bgTex.image = sourceCanvasOrImg;
          bgTex.needsUpdate = true;
        }
        if (state.refract != null) prismMat.uniforms.uRefract.value = state.refract;
        if (state.chroma != null) prismMat.uniforms.uChroma.value = state.chroma;
        if (state.opacity != null) prismMat.uniforms.uOpacity.value = state.opacity;
        if (typeof state.each === 'function') {
          for (let i = 0; i < bars.length; i++) state.each(bars[i], i);
        }
        applyCam(cam, state);
        blit(ctx, scene, cam, state);
      },
    };
  }

  // ============================================================================================================
  // 5. T3.three.louverTransition — z=60 Real-Perspective 3D Mechanical Blinds / Flipping Slats Transition
  // ============================================================================================================
  function louverTransition(opts = {}) {
    const THREE = reqTHREE();
    const slatsN = Math.max(2, opts.count || 10);
    const axis = opts.axis || 'vertical'; // 'vertical' (vertical strips flipping around Y) | 'horizontal'
    const scene = new THREE.Scene();
    const fov = 34;
    const camZ = 5.0;
    const cam = makeCamera({ fov, z: camZ });
    const visH = 2 * Math.tan((fov * Math.PI) / 360) * camZ;
    const visW = visH * (W0 / H0);

    const mkTex = () => {
      const c = document.createElement('canvas'); c.width = 4; c.height = 4;
      const t = new THREE.CanvasTexture(c);
      t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter;
      if (THREE.SRGBColorSpace) t.colorSpace = THREE.SRGBColorSpace;
      return t;
    };
    const texA = mkTex(), texB = mkTex();
    const backCol = new THREE.Color(opts.edgeColor || '#10141c');

    const slats = [];
    for (let i = 0; i < slatsN; i++) {
      const u0 = i / slatsN, u1 = (i + 1) / slatsN;
      const w = axis === 'vertical' ? visW / slatsN : visW;
      const h = axis === 'vertical' ? visH : visH / slatsN;
      const geoA = new THREE.PlaneGeometry(w, h);
      const geoB = new THREE.PlaneGeometry(w, h);
      geoB.rotateY(axis === 'vertical' ? Math.PI : 0);
      if (axis !== 'vertical') geoB.rotateX(Math.PI);

      // Slice UVs cleanly for each slat: geoB is rotated 180 deg and piv rotates 180 deg back (360 deg total),
      // so uvB maps identically to uvA to stay un-mirrored when flipped face-forward.
      const uvA = geoA.attributes.uv;
      const uvB = geoB.attributes.uv;
      for (let k = 0; k < uvA.count; k++) {
        const u = uvA.getX(k), v = uvA.getY(k);
        if (axis === 'vertical') {
          const nu = u0 + u * (u1 - u0);
          uvA.setXY(k, nu, v);
          uvB.setXY(k, nu, v);
        } else {
          const v0 = 1 - u1, v1 = 1 - u0;
          const nv = v0 + v * (v1 - v0);
          uvA.setXY(k, u, nv);
          uvB.setXY(k, u, nv);
        }
      }

      const piv = new THREE.Group();
      if (axis === 'vertical') piv.position.set(-visW * 0.5 + (i + 0.5) * w, 0, 0);
      else piv.position.set(0, visH * 0.5 - (i + 0.5) * h, 0);

      const matA = new THREE.MeshBasicMaterial({ map: texA, side: THREE.FrontSide });
      const matB = new THREE.MeshBasicMaterial({ map: texB, side: THREE.FrontSide });
      const mA = new THREE.Mesh(geoA, matA); mA.position.z = 0.008;
      const mB = new THREE.Mesh(geoB, matB); mB.position.z = -0.008;
      const body = new THREE.Mesh(new THREE.BoxGeometry(w * 0.992, h * 0.992, 0.014), new THREE.MeshBasicMaterial({ color: backCol }));
      piv.add(body, mA, mB);
      scene.add(piv);
      slats.push({ piv, matA, matB, index: i });
    }

    return {
      scene, camera: cam, slats,
      draw(ctx, fromSource, toSource, progress, state = {}) {
        if (fromSource) { texA.image = fromSource; texA.needsUpdate = true; }
        if (toSource) { texB.image = toSource; texB.needsUpdate = true; }
        const stagger = state.stagger != null ? state.stagger : 0.38;
        const p = T3.clamp(progress, 0, 1);
        for (let i = 0; i < slats.length; i++) {
          const delay = (i / Math.max(1, slats.length - 1)) * stagger;
          const local = T3.clamp((p - delay) / Math.max(0.05, 1 - stagger), 0, 1);
          const eased = state.ease ? T3.EZ[state.ease](local) : T3.EZ.snap(local);
          const ang = eased * Math.PI;
          const popZ = Math.sin(eased * Math.PI) * (state.popZ != null ? state.popZ : 0.35);
          if (axis === 'vertical') { slats[i].piv.rotation.y = ang; slats[i].piv.position.z = popZ; }
          else { slats[i].piv.rotation.x = ang; slats[i].piv.position.z = popZ; }
          // Subtle physical brightness dip near edge-on 90 deg for crisp 3D read
          const sh = 0.72 + 0.28 * Math.abs(Math.cos(ang));
          slats[i].matA.color.setRGB(sh, sh, sh);
          slats[i].matB.color.setRGB(sh, sh, sh);
        }
        applyCam(cam, state);
        blit(ctx, scene, cam, state);
      },
    };
  }

  // ============================================================================================================
  // 6. T3.three.field — Stylized 3D Graphic Horizon Grid + InstancedMesh Monoliths & Orbital Rings
  // ============================================================================================================
  function field(opts = {}) {
    const THREE = reqTHREE();
    const scene = new THREE.Scene();
    if (opts.fogColor) scene.fog = new THREE.Fog(opts.fogColor, opts.fogNear || 5, opts.fogFar || 28);
    const cam = makeCamera({ fov: opts.fov || 48, y: opts.camY != null ? opts.camY : 2.1, z: opts.camZ != null ? opts.camZ : 7.5, lookY: opts.lookY != null ? opts.lookY : 0.4 });

    const gridColor = new THREE.Color(opts.gridColor || '#475569');
    const accentCol = new THREE.Color(opts.accentColor || '#ff3d68');
    const blockCol = new THREE.Color(opts.blockColor || '#1e293b');
    const grid = new THREE.GridHelper(opts.gridSize || 44, opts.gridDivs || 36, accentCol, gridColor);
    grid.position.y = opts.floorY != null ? opts.floorY : -1.4;
    scene.add(grid);

    const cols = opts.cols || 9, rows = opts.rows || 5;
    const count = cols * rows;
    const boxGeo = new THREE.BoxGeometry(0.46, 1.0, 0.46);
    const mat = opts.wire
      ? new THREE.MeshBasicMaterial({ color: accentCol, wireframe: true })
      : new THREE.MeshToonMaterial({ color: blockCol, gradientMap: makeToonGradient(THREE, 3) });
    const inst = new THREE.InstancedMesh(boxGeo, mat, count);
    const keyL = new THREE.DirectionalLight(0xffffff, 1.3); keyL.position.set(5, 9, 6); scene.add(keyL);
    scene.add(new THREE.AmbientLight(0xffffff, 0.75));
    scene.add(inst);

    const ringGeo = new THREE.TorusGeometry(opts.ringRadius || 3.4, 0.028, 12, 96);
    const ringMat = new THREE.MeshBasicMaterial({ color: accentCol, transparent: true, opacity: opts.ringOpacity != null ? opts.ringOpacity : 0.78 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.position.set(0, 0.9, -4.0);
    scene.add(ring);

    const dummy = new THREE.Object3D();
    return {
      scene, camera: cam, grid, instanced: inst, ring,
      draw(ctx, state = {}) {
        const phase = state.phase || 0;
        const pulse = state.pulse || 0;
        const floorY = opts.floorY != null ? opts.floorY : -1.4;
        let idx = 0;
        for (let r = 0; r < rows; r++) {
          for (let c = 0; c < cols; c++) {
            const x = (c - (cols - 1) * 0.5) * 1.95;
            const z = -2.5 - r * 2.4 + ((state.scrollZ || 0) % 2.4);
            // Skip center aisle so hero text/character stays clean
            const centerClear = Math.abs(x) < 2.2 ? 0.28 : 1.0;
            const wave = 0.5 + 0.5 * Math.sin(phase * 1.8 + c * 0.65 + r * 0.85);
            const h = (0.35 + wave * 1.85 + pulse * 0.9) * centerClear;
            dummy.position.set(x, floorY + h * 0.5, z);
            dummy.scale.set(1, h, 1);
            dummy.rotation.set(0, state.blockSpin || 0, 0);
            dummy.updateMatrix();
            inst.setMatrixAt(idx++, dummy.matrix);
          }
        }
        inst.instanceMatrix.needsUpdate = true;
        grid.position.z = ((state.scrollZ || 0) % (44 / 36));
        ring.rotation.set(0.38 + Math.sin(phase * 0.7) * 0.14, phase * 0.4, 0.15);
        applyCam(cam, state);
        blit(ctx, scene, cam, state);
      },
    };
  }

  // ============================================================================================================
  // 7. T3.three.relief — Real-Time 2.5D Depth-Map Displaced Mesh (Zero-Blender Relief & Fast Micro-Cuts)
  // ============================================================================================================
  function relief(opts = {}) {
    const THREE = reqTHREE();
    const scene = new THREE.Scene();
    const fov = opts.fov || 36;
    const camZ = 2.78;
    const cam = makeCamera({ fov, z: camZ });
    const aspect = (opts.width || W0) / (opts.height || H0);
    const visH = 2 * Math.tan((fov * Math.PI) / 360) * camZ;
    const visW = visH * aspect;
    const overscan = opts.overscan || 1.14;
    const segX = opts.segX || 192, segY = opts.segY || 108;

    const mkImgTex = (img) => {
      const t = new THREE.Texture(img || document.createElement('canvas'));
      t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter;
      t.needsUpdate = true;
      return t;
    };
    const colTex = mkImgTex(opts.image);
    if (THREE.SRGBColorSpace) colTex.colorSpace = THREE.SRGBColorSpace;
    const depTex = mkImgTex(opts.depth);

    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: colTex },
        uDepth: { value: depTex },
        uStrength: { value: opts.strength != null ? opts.strength : 0.34 },
        uFog: { value: opts.fog || 0 },
        uFogColor: { value: new THREE.Color(opts.fogColor || '#0f172a') },
      },
      vertexShader: `
        uniform sampler2D uDepth;
        uniform float uStrength;
        varying vec2 vUv;
        varying float vD;
        void main(){
          vUv = uv;
          float d = texture2D(uDepth, uv).r;
          vD = d;
          vec3 p = position + vec3(0.0, 0.0, (d - 0.5) * uStrength);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
        }`,
      fragmentShader: `
        uniform sampler2D uColor;
        uniform float uFog;
        uniform vec3 uFogColor;
        varying vec2 vUv;
        varying float vD;
        void main(){
          vec4 c = texture2D(uColor, vUv);
          vec3 rgb = mix(c.rgb, uFogColor, uFog * (1.0 - vD));
          gl_FragColor = vec4(rgb, c.a);
        }`,
    });

    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(visW * overscan, visH * overscan, segX, segY), mat);
    scene.add(mesh);

    return {
      scene, camera: cam, mesh,
      setSources(img, depthImg) {
        if (img) { colTex.image = img; colTex.needsUpdate = true; }
        if (depthImg) { depTex.image = depthImg; depTex.needsUpdate = true; }
      },
      draw(ctx, state = {}) {
        const orbit = ((state.orbit || 0) * Math.PI) / 180;
        const crane = ((state.crane || 0) * Math.PI) / 180;
        const push = state.push || 0;
        const dist = camZ - push;
        cam.position.set(
          Math.sin(orbit) * dist + (state.truck || 0),
          Math.sin(crane) * dist,
          Math.cos(orbit) * Math.cos(crane) * dist
        );
        cam.lookAt(state.targetX || 0, state.targetY || 0, state.targetZ || 0);
        if (state.roll) cam.rotateZ(state.roll);
        if (state.strength != null) mat.uniforms.uStrength.value = state.strength;
        if (state.fog != null) mat.uniforms.uFog.value = state.fog;
        blit(ctx, scene, cam, state);
      },
    };
  }

  // ============================================================================================================
  // 8. T3.three.stage — Lightweight Stylized 3D Stage with Grounded 2D Cutout Cards & Contact Shadows
  // ============================================================================================================
  function stage(opts = {}) {
    const THREE = reqTHREE();
    const scene = new THREE.Scene();
    if (opts.fogColor) scene.fog = new THREE.Fog(opts.fogColor, opts.fogNear || 6, opts.fogFar || 26);
    const cam = makeCamera({ fov: opts.fov || 38, y: opts.camY != null ? opts.camY : 0.4, z: opts.camZ != null ? opts.camZ : 6.0 });
    const keyL = new THREE.DirectionalLight(0xffffff, 1.25); keyL.position.set(4, 7, 6); scene.add(keyL);
    scene.add(new THREE.AmbientLight(0xffffff, 0.72));

    function addCard(img, copts = {}) {
      const tex = new THREE.Texture(img);
      if (THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace;
      tex.needsUpdate = true;
      const aspect = (img.naturalWidth || img.width || 1) / Math.max(1, img.naturalHeight || img.height || 1);
      const h = copts.height || 2.6, w = copts.width || h * aspect;
      const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.02, side: THREE.DoubleSide });
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
      mesh.position.set(copts.x || 0, copts.y || 0, copts.z || 0);
      mesh.rotation.set(copts.rotX || 0, copts.rotY || 0, copts.rotZ || 0);
      scene.add(mesh);
      return mesh;
    }

    return {
      scene, camera: cam, addCard,
      draw(ctx, state = {}) { applyCam(cam, state); blit(ctx, scene, cam, state); },
    };
  }

  T3.three = {
    renderer: getRenderer,
    blit,
    mount,
    makeCamera,
    extrudeText,
    textRing,
    textCorridor,
    prismOverlay,
    louverTransition,
    field,
    relief,
    stage,
  };
})();
