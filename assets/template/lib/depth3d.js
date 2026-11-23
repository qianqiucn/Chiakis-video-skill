/* depth3d.js — 2.5D camera moves on a single illustration using its depth map (WebGL2, no library).
 *
 *   <script src="lib/depth3d.js"></script>            (after engine.js)
 *   <script src="assets/tex/E.tex.js"></script>       (window.TEX.E = data-URI; made by scripts/texjs.ps1)
 *   <script src="assets/tex/E_depth.tex.js"></script>
 *
 *   const sc = T3.depth3d(layer, { color: 'E', depth: 'E_depth' });   // in init()
 *   sc.render({ x, y, dolly, zoom, rot, focus, dof, fog, fogColor, exposure });  // in render(t)
 *
 * Camera params (all optional, 0 = rest):
 *   x, y   : camera slide in "screen fractions" (0.03 ≈ a gentle truck). Near things move more.
 *   dolly  : push-in through depth (0.1 = near objects grow ~10% more than far ones)
 *   zoom   : plain lens zoom (1 = none), rot: roll in radians
 *   focus  : depth 0..1 that stays still (default 0.5); parallax pivots around it
 *   dof    : depth-of-field blur strength (0..4 mip levels at max defocus)
 *   fog    : 0..1 mixes far depths toward fogColor [r,g,b] 0..1
 *   exposure: brightness multiplier · depthBlur: depth-map mip bias (default 0.6) · overscan:false disables auto-overscan
 * Depth map: white = near, black = far, same framing as the color image.
 * Why data-URIs: WebGL can't upload file:// images (cross-origin) when the page is double-clicked;
 * data: URIs are always allowed. Rendering is a pure function of the params → frame-exact.
 */
(function () {
  const VS = `#version 300 es
  in vec2 p; out vec2 uv;
  void main(){ uv = p*0.5+0.5; uv.y = 1.0-uv.y; gl_Position = vec4(p,0.,1.); }`;
  const FS = `#version 300 es
  precision highp float;
  in vec2 uv; out vec4 o;
  uniform sampler2D C, D;
  uniform vec2 cam; uniform float dolly, zoom, rot, focus, dof, fog, expo, aspect;
  uniform vec3 fogC;
  uniform float dlod;
  float depthAt(vec2 s){ return texture(D, s, dlod).r; }   // lod 0.5–1.5: blurrier depth = softer tears, sharper = fewer ghost outlines
  void main(){
    // lens: zoom + roll about the centre (aspect-correct)
    vec2 q = uv - 0.5; q.x *= aspect;
    float cs = cos(rot), sn = sin(rot);
    q = mat2(cs, -sn, sn, cs) * q / zoom; q.x /= aspect;
    vec2 u = q + 0.5;
    // inverse parallax: find source s with  s + shift(depth(s)) = u   (fixed-point iterations)
    vec2 s = u;
    for (int i = 0; i < 10; i++) {
      float k = depthAt(s) - focus;
      s = 0.5 + (u - 0.5 - cam * k) / (1.0 + dolly * k);
    }
    float d = depthAt(s);
    float blur = dof * abs(d - focus) * 2.0;
    vec3 col = texture(C, clamp(s, 0.001, 0.999), blur).rgb * expo;
    col = mix(col, fogC, fog * (1.0 - d));
    o = vec4(col, 1.0);
  }`;

  function compile(gl, type, src) {
    const sh = gl.createShader(type); gl.shaderSource(sh, src); gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh));
    return sh;
  }

  T3.depth3d = function (layer, opt) {
    const W = opt.width || 1920, H = opt.height || 1080;
    const cv = T3.el('canvas', { position: 'absolute', left: 0, top: 0, width: W + 'px', height: H + 'px' }, layer);
    cv.width = W; cv.height = H;
    const gl = cv.getContext('webgl2', { preserveDrawingBuffer: true, antialias: false });
    if (!gl) { cv.style.background = '#123'; return { canvas: cv, render() {} }; }
    const pr = gl.createProgram();
    gl.attachShader(pr, compile(gl, gl.VERTEX_SHADER, VS)); gl.attachShader(pr, compile(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(pr); gl.useProgram(pr);
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const U = {}; for (const n of ['C', 'D', 'cam', 'dolly', 'zoom', 'rot', 'focus', 'dof', 'fog', 'expo', 'aspect', 'fogC', 'dlod']) U[n] = gl.getUniformLocation(pr, n);
    let ready = 0, last = null;
    function tex(unit, key) {
      const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 255]));
      const src = (window.TEX && window.TEX[key]) || key;     // key in TEX, or a URL (works under http/--allow-file-access)
      const img = new Image();
      img.onload = () => {
        gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        gl.generateMipmap(gl.TEXTURE_2D);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        ready++; if (last) draw(last);
      };
      img.src = src;
    }
    tex(0, opt.color); tex(1, opt.depth);
    gl.uniform1i(U.C, 0); gl.uniform1i(U.D, 1);
    function draw(c) {
      gl.viewport(0, 0, W, H);
      gl.uniform2f(U.cam, c.x || 0, c.y || 0); gl.uniform1f(U.dolly, c.dolly || 0);
      const fo = c.focus == null ? 0.5 : c.focus, far = Math.max(fo, 1 - fo);
      // auto overscan: enlarge just enough that shifted/dollied content never exposes the frame edge
      const over = c.overscan === false ? 1 : 1 + Math.abs(c.dolly || 0) * far + 2.2 * Math.max(Math.abs(c.x || 0), Math.abs(c.y || 0)) * far;
      gl.uniform1f(U.zoom, (c.zoom || 1) * over); gl.uniform1f(U.dlod, c.depthBlur == null ? 0.6 : c.depthBlur);
      gl.uniform1f(U.rot, c.rot || 0); gl.uniform1f(U.focus, fo); gl.uniform1f(U.dof, c.dof || 0);
      gl.uniform1f(U.fog, c.fog || 0); gl.uniform1f(U.expo, c.exposure == null ? 1 : c.exposure); gl.uniform1f(U.aspect, W / H);
      const f = c.fogColor || [0.02, 0.04, 0.12]; gl.uniform3f(U.fogC, f[0], f[1], f[2]);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
    return { canvas: cv, get ready() { return ready === 2; }, render(c) { last = c || {}; draw(last); } };
  };
})();
