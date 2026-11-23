"""Blender (headless): turn a 2D illustration + its depth map into a displaced 2.5D relief and film it
with a real camera (parallax + depth of field). Renders PNG frames for `assets/template/lib/sequence.js`
(play back with `T3.relX` in `lib/motion/timing.js` to undo Blender's SINE ease).

Usage (run through scripts/run_queue.py blender):
  python -X utf8 scripts/run_queue.py blender --lane relief -- \
      blender -b --python scripts/blender/depth_relief.py -- \
      --image art.png --depth art_depth_soft.png --out web/assets/rel/shot01 --frames 48 --fps 24 \
      [--push 0.35] [--truck 0.12] [--strength 0.35] [--dof 2.8] [--engine eevee|cycles] [--res 1920x1080] [--samples 32] \
      [--orbit -9] [--crane 6] [--target-depth auto] [--target-uv 0.5,0.5]

Key flags:
  --push       Camera travel toward the picture (picture width = 2 units; defaults to 0.08 with orbit/crane, else 0.35).
  --truck      Sideways camera slide (when --orbit and --crane are 0).
  --strength   Relief displacement depth (keep 0.22-0.35 on a softened depth map to avoid rubber-sheet silhouette stretch).
  --dof        Aperture f-stop (0 = off; on this 2-unit set use 0.20-0.35 for visible bokeh/DOF).
  --overscan   Plane scale vs frame (1.15 hides edges up to |orbit|<=16 deg and |crane|<=16 deg).
  --subdiv     Simple subdivision levels (8 = 256x256 grid; 10 = 1024x1024 for fine silhouettes).
  --orbit DEG  Arc left/right around the subject at --target-uv (+ = left->right; background behind pivot slides right).
  --crane DEG  Arc up/down around the same pivot (+ = camera rises; background behind pivot slides up).
  --target-uv  Subject position in image fractions "u,v" from top-left (default "0.5,0.5").

See references/relief-25d.md for camera grammar, depth softening (`vision/depth.py --soften`), and `vision/parallax.py`.
"""
import argparse
import math
import os
import sys
import time
import bpy


def orbit_pose(u, deg, push, dist, pivot, aim0, crane=0.0):
    """Camera and aim positions at ease u (0..1) swinging rigidly about `pivot` then pushing toward it."""
    th, ph = math.radians(deg * (u - 0.5)), math.radians(crane * (u - 0.5))
    px, py, pz = pivot

    def swing(x, y, z):
        dx, dy, dz = x - px, y - py, z - pz
        dy, dz = dy * math.cos(ph) + dz * math.sin(ph), dz * math.cos(ph) - dy * math.sin(ph)
        return px + dx * math.cos(th) - dy * math.sin(th), py + dx * math.sin(th) + dy * math.cos(th), pz + dz

    cx, cy, cz = swing(0.0, -dist, 0.0)
    ax, ay, az = swing(*aim0)
    vx, vy, vz = px - cx, py - cy, pz - cz
    k = push * u / max(math.sqrt(vx * vx + vy * vy + vz * vz), 1e-9)
    return (cx + vx * k, cy + vy * k, cz + vz * k), (ax + vx * k, ay + vy * k, az + vz * k)


argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--image", required=True)
ap.add_argument("--depth", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--frames", type=int, default=48)
ap.add_argument("--fps", type=int, default=24)
ap.add_argument("--push", type=float, default=None)
ap.add_argument("--truck", type=float, default=0.12)
ap.add_argument("--strength", type=float, default=0.35)
ap.add_argument("--dof", type=float, default=2.8)
ap.add_argument("--engine", default="eevee", choices=("eevee", "cycles"))
ap.add_argument("--res", default="1920x1080")
ap.add_argument("--samples", type=int, default=32)
ap.add_argument("--overscan", type=float, default=1.15)
ap.add_argument("--subdiv", type=int, default=8)
ap.add_argument("--orbit", type=float, default=0.0)
ap.add_argument("--crane", type=float, default=0.0)
ap.add_argument("--target-depth", default="auto")
ap.add_argument("--target-uv", default="0.5,0.5")
a = ap.parse_args(argv)
if a.push is None:
    a.push = 0.08 if a.orbit or a.crane else 0.35
W, H = (int(v) for v in a.res.lower().split("x"))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
img = bpy.data.images.load(os.path.abspath(a.image))
dep = bpy.data.images.load(os.path.abspath(a.depth))
dep.colorspace_settings.name = "Non-Color"
aspect = img.size[1] / img.size[0]

# Relief plane: 2 units wide, subdivided, displaced along normal by depth map (white = near = toward camera)
bpy.ops.mesh.primitive_plane_add(size=2)
pl = bpy.context.active_object
pl.scale = (a.overscan, aspect * a.overscan, 1)
bpy.ops.object.transform_apply(scale=True)
pl.rotation_euler = (1.5708, 0, 0)
sub = pl.modifiers.new("sub", "SUBSURF")
sub.subdivision_type = "SIMPLE"
sub.levels = sub.render_levels = a.subdiv
tex = bpy.data.textures.new("depth", "IMAGE")
tex.image = dep
tex.extension = "EXTEND"
disp = pl.modifiers.new("disp", "DISPLACE")
disp.texture = tex
disp.texture_coords = "UV"
disp.strength = a.strength
disp.mid_level = 0.0
disp.direction = "NORMAL"

mat = bpy.data.materials.new("pic")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
emi = nt.nodes.new("ShaderNodeEmission")
ti = nt.nodes.new("ShaderNodeTexImage")
ti.image = img
ti.extension = "EXTEND"
nt.links.new(ti.outputs["Color"], emi.inputs["Color"])
nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
pl.data.materials.append(mat)

# Camera framing the picture (50mm lens on 36mm sensor -> dist = 2.778 units frames 2.0 width exactly)
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
cam_data.lens = 50
cam_data.sensor_width = 36
dist = (cam_data.lens / cam_data.sensor_width) * 2.0
cam.rotation_euler = (1.5708, 0, 0)

if a.orbit or a.crane:
    tu, tv = (float(v) for v in a.target_uv.split(","))
    td = 0.7
    if a.target_depth == "auto":
        try:
            import numpy as np
            dw, dh = dep.size
            px_ = np.empty(dw * dh * dep.channels, np.float32)
            dep.pixels.foreach_get(px_)
            d2 = px_.reshape(dh, dw, dep.channels)[..., 0]
            r0, c0, rr = int((1 - tv) * (dh - 1)), int(tu * (dw - 1)), max(2, dw // 100)
            td = float(np.median(d2[max(0, r0 - rr) : r0 + rr + 1, max(0, c0 - rr) : c0 + rr + 1]))
        except Exception as e:
            print("target-depth auto failed, using 0.7:", e)
    else:
        td = float(a.target_depth)
    pivot = ((tu - 0.5) * 2 * a.overscan, -a.strength * td, (0.5 - tv) * 2 * a.overscan * aspect)
    piv = bpy.data.objects.new("pivot", None)
    piv.location = pivot
    sc.collection.objects.link(piv)
    aim = bpy.data.objects.new("aim", None)
    sc.collection.objects.link(aim)
    con = cam.constraints.new("TRACK_TO")
    con.target = aim
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    if a.dof > 0:
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = a.dof
        cam_data.dof.focus_object = piv
    sc.frame_start, sc.frame_end = 1, a.frames
    for f in range(1, a.frames + 1):
        u = (1 - math.cos(math.pi * (f - 1) / max(1, a.frames - 1))) / 2
        cam.location, aim.location = orbit_pose(u, a.orbit, a.push, dist, pivot, (0.0, pivot[1], 0.0), a.crane)
        cam.keyframe_insert("location", frame=f)
        aim.keyframe_insert("location", frame=f)
    print(
        f"ORBIT {a.orbit:g} deg CRANE {a.crane:g} deg around ({pivot[0]:.3f}, {pivot[1]:.3f}, {pivot[2]:.3f}) "
        f"depth {td:.2f}, travel {math.radians(math.hypot(a.orbit, a.crane)) * (dist - a.strength * td):.3f} u, push {a.push:g}"
    )
else:
    if a.dof > 0:
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = a.dof
        cam_data.dof.focus_distance = dist - a.strength * 0.6
    sc.frame_start, sc.frame_end = 1, a.frames
    for f, (y, x) in ((1, (-dist, -a.truck / 2)), (a.frames, (-dist + a.push, a.truck / 2))):
        cam.location = (x, y, 0)
        cam.keyframe_insert("location", frame=f)
        if a.dof > 0:
            cam_data.dof.focus_distance = (-y) - a.strength * 0.6
            cam_data.dof.keyframe_insert("focus_distance", frame=f)
    fcurves = (
        cam.animation_data.action.fcurves
        if cam.animation_data and cam.animation_data.action and hasattr(cam.animation_data.action, "fcurves")
        else []
    )
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "SINE"
            kp.easing = "EASE_IN_OUT"

sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = a.fps
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"  # preserve illustration colours verbatim (no Filmic/AgX tone shift)

device = "CPU"
if a.engine == "cycles":
    sc.render.engine = "CYCLES"
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "METAL", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
                prefs.refresh_devices()
                gpus = [d for d in prefs.devices if d.type == kind]
                if gpus:
                    for d in prefs.devices:
                        d.use = d.type == kind
                    sc.cycles.device = "GPU"
                    device = f"{kind} {gpus[0].name}"
                    break
            except Exception:
                pass
    except Exception as e:
        print("GPU setup failed (using CPU):", e)
else:
    engines = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = a.samples
    except Exception:
        pass
    device = "GPU (Eevee)"

os.makedirs(a.out, exist_ok=True)
times = []
for f in range(1, a.frames + 1):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(os.path.abspath(a.out), f"f{f:03d}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    times.append(time.time() - t0)
print(
    f"RELIEF engine={sc.render.engine} device={device} {W}x{H} frames={a.frames} "
    f"first={times[0]:.2f}s avg_rest={sum(times[1:]) / max(1, len(times) - 1):.2f}s "
    f"total={sum(times):.1f}s -> {a.out}"
)
