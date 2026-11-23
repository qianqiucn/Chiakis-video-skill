r"""Camera-projection dolly-in template for headless Blender (3D engineer).

Every illustration layer becomes proxy geometry seen from the ORIGINAL camera (exact projective UV in shader),
so frame 1 equals the painting pixel-for-pixel; the camera then dollies forward on a quartic ease-out:
  plate   : 2-px grid displaced along camera rays by eng/rho_plate.npy (wall, midground, floor; design.py)
  shelves : vertical-plane alpha cards for near foreground structures standing on the floor plane
  subject : vertical-plane alpha card standing on the floor at its contact row
  light   : additive breathing glow card for back-lit window / light source
  dust    : 180 camera-facing soft quads in 3 depth layers, slowly settling (linear shape key)

Window light gain per frame: CTRL node group (CONSTANT keys). mode 1 = mask pass (R shelves, G subject, B window).
Run via queue:
  python -X utf8 <skill>/scripts/run_queue.py blender --lane 3d -- \
    blender -b --python dolly_scene.py -- --eng <eng dir> --out <dir> [--frames 1-23] [--passes beauty,mask]
"""
import argparse, json, math, os, sys, time
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--eng", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--frames", default="1-23")
ap.add_argument("--passes", default="beauty,mask")
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--mblur", type=float, default=0.25)       # shutter in frames (0.25 = 90 deg); 0 = off
ap.add_argument("--steps", type=int, default=8)
ap.add_argument("--grid", type=int, default=2)
ap.add_argument("--filter", type=float, default=1.2)
ap.add_argument("--dust", type=int, default=180)
ap.add_argument("--dust-gain", type=float, default=1.0)
ap.add_argument("--glow", type=float, default=0.04)
ap.add_argument("--gains", default="1,1,1,1,1,1.3,1.19,0.775,1,1,1.3,1.3,1,0.775,0.775,1,1,1,1,1,1,1,1")
ap.add_argument("--save-blend", default="")
a = ap.parse_args(argv)

DSG = json.load(open(os.path.join(a.eng, "design.json"), encoding="utf-8"))
F = float(DSG["F"])
TAN = math.tan(math.radians(DSG["pitch_deg"]))
D = 10.0                                     # far-wall centre distance in Blender units
W, H = 1920, 1080


def rowfactor(y):
    return 1.0 / (1.0 + (y - 540.0) * TAN / F)


def travel(n):
    return 0.1309 * (1.0 - (1.0 - (n - 1.0) / 28.0) ** 4)


def ray(px, py, rho):
    z = rho * D
    return ((px - 960.0) / F * z, z, -(py - 540.0) / F * z)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
prefs = bpy.context.preferences.edit

# ---------------------------------------------------------------- camera (original camera = origin, looks +Y)
cd = bpy.data.cameras.new("cam")
cd.sensor_fit = "HORIZONTAL"; cd.sensor_width = 36.0; cd.lens = F / W * 36.0
cd.clip_start = 0.05; cd.clip_end = 200.0
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
prefs.keyframe_new_interpolation_type = "LINEAR"
for n in range(0, 26):                       # one key per frame on the exact curve (no SINE ease)
    cam.location = (0.0, D * travel(n), 0.0)
    cam.keyframe_insert("location", frame=n)

# ---------------------------------------------------------------- control group: mode + window gain
ctrl = bpy.data.node_groups.new("CTRL", "ShaderNodeTree")
for nm in ("mode", "wgain"):
    ctrl.interface.new_socket(name=nm, in_out="OUTPUT", socket_type="NodeSocketFloat")
go = ctrl.nodes.new("NodeGroupOutput")
vmode = ctrl.nodes.new("ShaderNodeValue"); vmode.name = "mode"; vmode.outputs[0].default_value = 0.0
vgain = ctrl.nodes.new("ShaderNodeValue"); vgain.name = "wgain"; vgain.outputs[0].default_value = 1.0
ctrl.links.new(vmode.outputs[0], go.inputs["mode"]); ctrl.links.new(vgain.outputs[0], go.inputs["wgain"])
gains = [float(v) for v in a.gains.split(",")]
prefs.keyframe_new_interpolation_type = "CONSTANT"
for n in range(0, 26):
    vgain.outputs[0].default_value = gains[min(max(n, 1), len(gains)) - 1]
    vgain.outputs[0].keyframe_insert("default_value", frame=n)
prefs.keyframe_new_interpolation_type = "LINEAR"


def img(name, colour=True):
    im = bpy.data.images.load(os.path.join(a.eng, name))
    im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return im


def node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def math_node(nt, op, x, y=None, z=None):
    m = node(nt, "ShaderNodeMath", operation=op)
    for i, v in enumerate((x, y, z)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = float(v)
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def proj_uv(nt):
    """Exact projective UV of the original camera for any geometry shading point."""
    geo = node(nt, "ShaderNodeNewGeometry")
    sep = node(nt, "ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
    u = math_node(nt, "MULTIPLY_ADD", math_node(nt, "DIVIDE", sep.outputs[0], sep.outputs[1]), F / W, 0.5)
    v = math_node(nt, "MULTIPLY_ADD", math_node(nt, "DIVIDE", sep.outputs[2], sep.outputs[1]), F / H, 0.5)
    c = node(nt, "ShaderNodeCombineXYZ"); nt.links.new(u, c.inputs[0]); nt.links.new(v, c.inputs[1])
    return c.outputs[0]


def tex(nt, image, vec):
    t = node(nt, "ShaderNodeTexImage", interpolation="Linear", extension="EXTEND"); t.image = image
    nt.links.new(vec, t.inputs[0])
    return t


def ctrl_node(nt):
    g = node(nt, "ShaderNodeGroup"); g.node_tree = ctrl
    return g


def mix_rgb(nt, fac, c1, c2):
    m = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MIX")
    for sock, v in ((m.inputs[0], fac), (m.inputs[6], c1), (m.inputs[7], c2)):
        if isinstance(v, (tuple, list)):
            sock.default_value = v
        elif isinstance(v, (int, float)):
            sock.default_value = float(v)
        else:
            nt.links.new(v, sock)
    return m.outputs[2]


def new_mat(name, method="DITHERED"):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; nt.nodes.clear()
    try:
        m.surface_render_method = method
    except Exception:
        m.blend_method = "HASHED" if method == "DITHERED" else "BLEND"
    return m, nt


T_PLATE, T_WIN = img("tex_plate.png"), img("tex_win.png", False)
T_SL, T_SR = img("tex_shelfL.png"), img("tex_shelfR.png")
sub_tex = "tex_subject.png" if os.path.exists(os.path.join(a.eng, "tex_subject.png")) else "tex_girl.png"
T_SUB = img(sub_tex)
for t_ in (T_SL, T_SR, T_SUB):
    t_.alpha_mode = "STRAIGHT"

# ---------------------------------------------------------------- plate material (breathing window)
m_plate, nt = new_mat("plate")
uv = proj_uv(nt); tp = tex(nt, T_PLATE, uv); tw = tex(nt, T_WIN, uv)
sw = node(nt, "ShaderNodeSeparateColor"); nt.links.new(tw.outputs["Color"], sw.inputs[0])
cg = ctrl_node(nt)
k = math_node(nt, "MULTIPLY_ADD", math_node(nt, "SUBTRACT", cg.outputs["wgain"], 1.0), sw.outputs[1], 1.0)
lit = node(nt, "ShaderNodeVectorMath", operation="SCALE")
nt.links.new(tp.outputs["Color"], lit.inputs[0]); nt.links.new(k, lit.inputs["Scale"])
maskc = node(nt, "ShaderNodeCombineColor"); nt.links.new(sw.outputs[0], maskc.inputs[2])
col = mix_rgb(nt, cg.outputs["mode"], lit.outputs[0], maskc.outputs[0])
em = node(nt, "ShaderNodeEmission"); nt.links.new(col, em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
out = node(nt, "ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs["Surface"])


def card_mat(name, image, mask_rgb):
    m, nt = new_mat(name, "DITHERED")
    uv = proj_uv(nt); t = tex(nt, image, uv); cg = ctrl_node(nt)
    col = mix_rgb(nt, cg.outputs["mode"], t.outputs["Color"], mask_rgb + (1.0,))
    em = node(nt, "ShaderNodeEmission"); nt.links.new(col, em.inputs["Color"])
    tr = node(nt, "ShaderNodeBsdfTransparent")
    mx = node(nt, "ShaderNodeMixShader")
    nt.links.new(t.outputs["Alpha"], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    out = node(nt, "ShaderNodeOutputMaterial"); nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


m_sl = card_mat("shelfL", T_SL, (1.0, 0.0, 0.0))
m_sr = card_mat("shelfR", T_SR, (1.0, 0.0, 0.0))
m_sub = card_mat("subject", T_SUB, (0.0, 1.0, 0.0))

# window light card: additive soft glow (B of tex_win), warm white, breathes with gain
m_glow, nt = new_mat("glow", "BLENDED")
uv = proj_uv(nt); tw = tex(nt, T_WIN, uv); cg = ctrl_node(nt)
sw = node(nt, "ShaderNodeSeparateColor"); nt.links.new(tw.outputs["Color"], sw.inputs[0])
inten = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", sw.outputs[2], cg.outputs["wgain"]),
                  math_node(nt, "SUBTRACT", 1.0, cg.outputs["mode"]))
em = node(nt, "ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.93, 0.82, 1.0)
nt.links.new(math_node(nt, "MULTIPLY", inten, a.glow), em.inputs["Strength"])
tr = node(nt, "ShaderNodeBsdfTransparent")
add = node(nt, "ShaderNodeAddShader"); nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
out = node(nt, "ShaderNodeOutputMaterial"); nt.links.new(add.outputs[0], out.inputs["Surface"])


# ---------------------------------------------------------------- geometry
def mesh_obj(name, verts, faces, mat, uvs=None, cols=None):
    me = bpy.data.meshes.new(name)
    verts = np.asarray(verts, np.float32).reshape(-1, 3)
    faces = np.asarray(faces, np.int32).reshape(-1, 4)
    me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(faces.size); me.loops.foreach_set("vertex_index", faces.ravel())
    me.polygons.add(len(faces)); me.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
    try:
        me.polygons.foreach_set("loop_total", np.full(len(faces), 4, np.int32))
    except Exception:
        pass
    me.update(calc_edges=True)
    if me.validate(verbose=False):
        print("mesh", name, "needed validation fixes")
    if uvs is not None:
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", np.asarray(uvs, np.float32).ravel())
    if cols is not None:
        at = me.color_attributes.new("dcol", "FLOAT_COLOR", "CORNER")
        at.data.foreach_set("color", np.asarray(cols, np.float32).ravel())
    me.update()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


t0 = time.time()
rho = np.load(os.path.join(a.eng, "rho_plate.npy")).astype(np.float64)
g, m_ = a.grid, 48
xs = np.arange(-m_, W + m_ + 1, g, dtype=np.float64)
ys = np.arange(-m_, H + m_ + 1, g, dtype=np.float64)
X, Y = np.meshgrid(xs, ys)
fx = np.clip(X - 0.5, 0, W - 1.001); fy = np.clip(Y - 0.5, 0, H - 1.001)
x0, y0 = fx.astype(int), fy.astype(int); ax, ay = fx - x0, fy - y0
r = (rho[y0, x0] * (1 - ax) * (1 - ay) + rho[y0, x0 + 1] * ax * (1 - ay) + rho[y0 + 1, x0] * (1 - ax) * ay
     + rho[y0 + 1, x0 + 1] * ax * ay)
z = r * D
verts = np.stack([(X - 960.0) / F * z, z, -(Y - 540.0) / F * z], -1).reshape(-1, 3)
ny, nx = X.shape
idx = np.arange(ny * nx).reshape(ny, nx)
faces = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
plate = mesh_obj("plate", verts, faces, m_plate)
print(f"plate mesh {len(verts)} verts {len(faces)} quads in {time.time() - t0:.1f}s")


def vplane(name, yn, x0_, x1_, y0_, y1_, mat):
    """Vertical world plane at horizontal distance yn (far-wall centre = 1) covering frame-1 box x0..x1, y0..y1."""
    c = [(x0_, y0_), (x1_, y0_), (x1_, y1_), (x0_, y1_)]
    v = [ray(px, py, yn * rowfactor(py)) for px, py in c]
    return mesh_obj(name, np.array(v), [(0, 1, 2, 3)], mat)


yn_s = DSG["yn_shelf"]
yn_h = DSG.get("yn_subject", DSG.get("yn_her"))
vplane("shelfL", yn_s, -70, 600, -70, 1000, m_sl)
vplane("shelfR", yn_s, 1320, 1990, -70, 1000, m_sr)
vplane("subject", yn_h, 860, 1070, 585, 905, m_sub)
vplane("glow", 0.975, -70, 1990, -70, 1150, m_glow)

# ---------------------------------------------------------------- dust: 3 depth layers, slowly settling
rng = np.random.default_rng(7)
layers = [(0.60, 0.70, 0.22), (0.70, 0.82, 0.33), (0.82, 0.95, 0.45)]
dv, df, duv, dcol, dmove = [], [], [], [], []
for i in range(a.dust):
    u = rng.random()
    lo, hi, _ = layers[0] if u < 0.22 else layers[1] if u < 0.55 else layers[2]
    rr = rng.uniform(lo, hi); zz = rr * D
    sx, sy = rng.uniform(-40, W + 40), rng.uniform(-40, H + 40)
    big = rng.random() < 0.10
    dpx = rng.uniform(5.0, 12.0) if big else float(np.clip(rng.lognormal(math.log(2.3), 0.28), 1.4, 3.6))
    peak = (rng.uniform(0.025, 0.06) if big else rng.uniform(0.09, 0.22)) * a.dust_gain
    half = 1.28 * dpx * zz / F
    cx, cy, cz = ray(sx, sy, rr)
    vy_px, vx_px = rng.uniform(0.15, 0.45), rng.uniform(-0.12, 0.12)
    mvx, mvz = vx_px * zz / F * 25.0, -vy_px * zz / F * 25.0
    b = len(dv)
    for qx, qz, uu, vv in ((-1, -1, 0, 0), (1, -1, 1, 0), (1, 1, 1, 1), (-1, 1, 0, 1)):
        dv.append((cx + qx * half, cy, cz + qz * half)); duv.append((uu, vv))
        dcol.append((peak * 1.0, peak * 0.95, peak * 0.86, 1.0)); dmove.append((mvx, 0.0, mvz))
    df.append((b, b + 1, b + 2, b + 3))
m_dust, nt = new_mat("dust", "BLENDED")
at = node(nt, "ShaderNodeAttribute", attribute_name="dcol")
uvn = node(nt, "ShaderNodeUVMap", uv_map="UVMap")
sep = node(nt, "ShaderNodeSeparateXYZ"); nt.links.new(uvn.outputs[0], sep.inputs[0])
du = math_node(nt, "MULTIPLY_ADD", sep.outputs[0], 2.0, -1.0); dv_ = math_node(nt, "MULTIPLY_ADD", sep.outputs[1], 2.0, -1.0)
d2 = math_node(nt, "ADD", math_node(nt, "MULTIPLY", du, du), math_node(nt, "MULTIPLY", dv_, dv_))
fall = math_node(nt, "EXPONENT", math_node(nt, "MULTIPLY", d2, -4.5))
cg = ctrl_node(nt)
st = math_node(nt, "MULTIPLY", fall, math_node(nt, "SUBTRACT", 1.0, cg.outputs["mode"]))
em = node(nt, "ShaderNodeEmission"); nt.links.new(at.outputs["Color"], em.inputs["Color"]); nt.links.new(st, em.inputs["Strength"])
tr = node(nt, "ShaderNodeBsdfTransparent")
add = node(nt, "ShaderNodeAddShader"); nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
out = node(nt, "ShaderNodeOutputMaterial"); nt.links.new(add.outputs[0], out.inputs["Surface"])
if a.dust > 0:
    dust = mesh_obj("dust", np.array(dv), df, m_dust, uvs=duv, cols=dcol)
    dust.shape_key_add(name="Basis", from_mix=False)
    sk = dust.shape_key_add(name="move", from_mix=False)
    co = np.array(dv) + np.array(dmove)
    sk.data.foreach_set("co", co.astype(np.float32).ravel())
    kb = dust.data.shape_keys.key_blocks["move"]; kb.slider_max = 1.0
    kb.value = 0.0; kb.keyframe_insert("value", frame=0)
    kb.value = 1.0; kb.keyframe_insert("value", frame=25)

# ---------------------------------------------------------------- render settings
eng_items = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in eng_items else "BLENDER_EEVEE"
sc.eevee.taa_render_samples = a.samples
for attr, val in (("use_shadows", False), ("use_raytracing", False), ("use_gtao", False), ("use_bloom", False)):
    try:
        setattr(sc.eevee, attr, val)
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.fps = 24
sc.frame_start, sc.frame_end = 1, 23
try:
    sc.render.filter_size = a.filter
except Exception as e:
    print("filter_size:", e)
sc.render.use_motion_blur = a.mblur > 0
if a.mblur > 0:
    sc.render.motion_blur_shutter = a.mblur
    for holder in (sc.render, sc.eevee):
        try:
            holder.motion_blur_position = "START"
        except Exception:
            pass
    try:
        sc.eevee.motion_blur_steps = a.steps
    except Exception as e:
        print("steps:", e)
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.view_settings.exposure = 0.0; sc.view_settings.gamma = 1.0
sc.render.image_settings.file_format = "PNG"          # 16-bit sRGB (Standard view)
sc.render.image_settings.color_depth = "16"
sc.render.image_settings.compression = 15
sc.render.image_settings.color_mode = "RGB"
sc.render.dither_intensity = 0.0
if a.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=a.save_blend)

frames = []
for part in a.frames.split(","):
    if "-" in part:
        s0, s1 = part.split("-"); frames += list(range(int(s0), int(s1) + 1))
    else:
        frames.append(int(part))
for ps in a.passes.split(","):
    vmode.outputs[0].default_value = 1.0 if ps == "mask" else 0.0
    od = os.path.join(a.out, ps); os.makedirs(od, exist_ok=True)
    tt = []
    for n in frames:
        sc.frame_set(n)
        sc.render.filepath = os.path.join(od, f"{ps[0]}_{n:04d}.png")
        t1 = time.time(); bpy.ops.render.render(write_still=True); tt.append(time.time() - t1)
        print(f"{ps} frame {n} cam_y {cam.location.y:.4f} gain {vgain.outputs[0].default_value:.3f} {tt[-1]:.2f}s", flush=True)
    print(f"PASS {ps}: {len(frames)} frames, first {tt[0]:.1f}s, avg {sum(tt) / len(tt):.2f}s, total {sum(tt):.1f}s")
print(f"engine {sc.render.engine}  lens {cd.lens:.3f} mm  total {time.time() - t0:.1f}s")
