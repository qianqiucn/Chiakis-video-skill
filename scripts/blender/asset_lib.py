"""asset_lib.py — use the local 3D asset library (scripts/assets3d.py) inside a Blender script, one line per job.

    import sys; sys.path.append(r"<skill>/scripts/blender"); import asset_lib as AL
    AL.use_hdri(AL.find("polyhaven:studio_small_09"), strength=1.0, rotation=40)     # world light + reflections
    floor.data.materials.append(AL.pbr_material(AL.find("ambientcg:WoodFloor051"), scale=2.0))
    chair = AL.import_model(AL.find("polyhaven:ArmChair_01"), height=0.9)          # list of the new objects

find(key) reads <lib>/catalog.json (key = "<source>:<id>", matching `assets3d.py get`) and returns the local
main file or folder. pbr_material takes a folder of maps and recognises common naming conventions (Poly Haven,
ambientCG, glTF, etc.): colour/diffuse/albedo, normal (OpenGL preferred, DirectX green auto-flipped),
roughness, metal, AO, packed ARM (R=AO, G=roughness, B=metal) and bump-only displacement.

2D cutout character / illustration card inside a built Blender set (references/3d.md §5c):
    card = AL.emissive_card(path_to_rgba_png, width=1.18, location=(0, 0.22, z), glow=0.8, tint=(0.72, 0.6, 1.0))
    sh = AL.contact_shadow(card, surface_z=DESK_Z)     # grounds the card with an alpha-shaped contact shadow
    AL.anime_look(keep=[card], no_ink=[sh])            # optional: Kuwahara + Freestyle silhouette ink on 3D props
"""
import bpy, json, math, os, re
from mathutils import Vector

LIB = (
    os.environ.get("CHIAKI_ASSETS3D")
    or os.path.join(os.path.expanduser("~"), ".cache", "chiaki-video", "assets3d")
).replace("\\", "/").rstrip("/")


def find(key, lib=LIB):
    cat = json.load(open(f"{lib}/catalog.json", encoding="utf-8"))
    if key not in cat: raise KeyError(f"{key} is not in {lib}/catalog.json: fetch it first with assets3d.py get")
    return cat[key]["main"]


def _nodes(owner):
    try: owner.use_nodes = True        # deprecated in Blender 5 (always on); harmless where it still exists
    except Exception: pass
    return owner.node_tree


def use_hdri(path, strength=1.0, rotation=0.0, camera_sees=True, background=(0.02, 0.02, 0.025)):
    sc = bpy.context.scene
    world = sc.world or bpy.data.worlds.new("World"); sc.world = world
    nt = _nodes(world); N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputWorld"); env = N.new("ShaderNodeTexEnvironment"); bg = N.new("ShaderNodeBackground")
    coord = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    env.image = bpy.data.images.load(path, check_existing=True)
    mp.inputs["Rotation"].default_value[2] = math.radians(rotation)
    L.new(coord.outputs["Generated"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], env.inputs["Vector"])
    L.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = strength
    if camera_sees:
        L.new(bg.outputs["Background"], out.inputs["Surface"])
    else:   # light and reflections from the HDRI, while the camera sees a flat colour
        flat = N.new("ShaderNodeBackground"); flat.inputs["Color"].default_value = (*background, 1)
        lp = N.new("ShaderNodeLightPath"); mix = N.new("ShaderNodeMixShader")
        L.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"]); L.new(bg.outputs["Background"], mix.inputs[1]); L.new(flat.outputs["Background"], mix.inputs[2])
        L.new(mix.outputs["Shader"], out.inputs["Surface"])
    return world


MAP_WORDS = {  # slot -> map token at the end of filename only
    "color": {"diff", "diffuse", "albedo", "basecolor", "color", "colour", "col"},
    "normal": {"nor", "normal", "nrm", "normalgl"}, "normal_dx": {"normaldx"},
    "rough": {"rough", "roughness"}, "metal": {"metal", "metallic", "metalness"},
    "ao": {"ao", "ambientocclusion", "occlusion"}, "disp": {"disp", "displacement", "height"},
    "arm": {"arm", "orm", "metallicroughness"},
}
NORMAL_WORDS = {"nor", "normal", "nrm"}
SIZE_TAGS = re.compile(r"\d+k|\d+|\d+bits?|jpe?g|png|exr|tiff?|map")


def _slot(fname):
    words = [w for w in re.split(r"[^a-z0-9]+", os.path.splitext(fname.lower())[0]) if w]
    while words and SIZE_TAGS.fullmatch(words[-1]): words.pop()
    if not words: return None
    w, prev = words[-1], (words[-2] if len(words) > 1 else "")
    if prev in NORMAL_WORDS and w in ("gl", "opengl"): return "normal"
    if prev in NORMAL_WORDS and w in ("dx", "directx"): return "normal_dx"
    return next((slot for slot, ws in MAP_WORDS.items() if w in ws), None)


def _maps(folder):
    found = {}
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith((".jpg", ".jpeg", ".png", ".exr", ".tif", ".tiff")): continue
        slot = _slot(f)
        if slot: found.setdefault(slot, f"{folder}/{f}")
    if "normal" not in found and "normal_dx" in found: found["normal"] = found["normal_dx"]
    return found


def pbr_material(folder, name=None, scale=1.0, disp_strength=0.1):
    folder = folder.replace("\\", "/").rstrip("/")
    m = _maps(folder)
    if "color" not in m: raise FileNotFoundError(f"no colour map in {folder}: {sorted(os.listdir(folder))}")
    mat = bpy.data.materials.new(name or os.path.basename(folder) or "pbr")
    nt = _nodes(mat); N, L = nt.nodes, nt.links
    bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED"); out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    coord = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(coord.outputs["UV"], mp.inputs["Vector"])

    def tex(path, data):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        if data: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], t.inputs["Vector"]); return t

    col = tex(m["color"], False)
    if "ao" in m and "arm" not in m:
        ao = tex(m["ao"], True); mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 0.5; L.new(col.outputs["Color"], mul.inputs["A"]); L.new(ao.outputs["Color"], mul.inputs["B"])
        L.new(mul.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        L.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    if "arm" in m:
        arm = tex(m["arm"], True); sep = N.new("ShaderNodeSeparateColor"); L.new(arm.outputs["Color"], sep.inputs["Color"])
        L.new(sep.outputs["Green"], bsdf.inputs["Roughness"]); L.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    if "rough" in m: L.new(tex(m["rough"], True).outputs["Color"], bsdf.inputs["Roughness"])
    if "metal" in m: L.new(tex(m["metal"], True).outputs["Color"], bsdf.inputs["Metallic"])
    if "normal" in m:
        nm = N.new("ShaderNodeNormalMap"); t = tex(m["normal"], True)
        if m["normal"] == m.get("normal_dx"):   # DirectX -> OpenGL: invert green
            sep = N.new("ShaderNodeSeparateColor"); inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
            comb = N.new("ShaderNodeCombineColor")
            L.new(t.outputs["Color"], sep.inputs["Color"]); L.new(sep.outputs["Green"], inv.inputs[1])
            L.new(sep.outputs["Red"], comb.inputs["Red"]); L.new(inv.outputs["Value"], comb.inputs["Green"]); L.new(sep.outputs["Blue"], comb.inputs["Blue"])
            L.new(comb.outputs["Color"], nm.inputs["Color"])
        else:
            L.new(t.outputs["Color"], nm.inputs["Color"])
        L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if "disp" in m:
        d = N.new("ShaderNodeDisplacement"); d.inputs["Scale"].default_value = disp_strength
        L.new(tex(m["disp"], True).outputs["Color"], d.inputs["Height"]); L.new(d.outputs["Displacement"], out.inputs["Displacement"])
    return mat


def import_model(path, height=None, location=(0, 0, 0), collection=None):
    """Import glTF / GLB / FBX / OBJ / .blend, switch QUATERNION objects to XYZ Euler, scale uniformly to `height` (m),
    and stand the model on z = 0 at `location`. Returns the imported objects."""
    path = path.replace("\\", "/"); ext = os.path.splitext(path)[1].lower()
    before = set(bpy.data.objects)
    if ext in (".gltf", ".glb"): bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".fbx": bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".obj": bpy.ops.wm.obj_import(filepath=path)
    elif ext == ".blend":
        with bpy.data.libraries.load(path, link=False) as (src, dst): dst.objects = list(src.objects)
        coll = collection or bpy.context.scene.collection
        for o in dst.objects:
            if o is not None: coll.objects.link(o)
    else: raise ValueError(f"unsupported model file {path}")
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    for o in new:   # glTF importer leaves QUATERNION rotation on every object: rotation_euler edits silently do nothing
        if o.rotation_mode == "QUATERNION":
            e = o.rotation_quaternion.to_euler("XYZ"); o.rotation_mode = "XYZ"; o.rotation_euler = e
    if height and new:
        bpy.context.view_layer.update()
        zs = [(o.matrix_world @ v.co).z for o in new if o.type == "MESH" for v in o.data.vertices]
        if zs and max(zs) > min(zs):
            k = height / (max(zs) - min(zs))
            for o in roots: o.scale = [s * k for s in o.scale]; o.location = [c * k for c in o.location]
            bpy.context.view_layer.update()
            zmin = min((o.matrix_world @ v.co).z for o in new if o.type == "MESH" for v in o.data.vertices)
            for o in roots: o.location.z -= zmin
    for o in roots:
        o.location.x += location[0]; o.location.y += location[1]; o.location.z += location[2]
    return new


# ---------------------------------------------------------------- 2D cutout card inside a built set (3d.md §5c)
def _node_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    m.node_tree.nodes.clear()
    return m, m.node_tree.nodes, m.node_tree.links


def emissive_card(image_path, width, location, rotation=(math.radians(90), 0, 0), glow=0.8, tint=(0.72, 0.6, 1.0), tint_k=0.35, name="subject"):
    """Place an RGBA 2D illustration cutout as an unlit upright card facing -Y.
    The illustration keeps its own cel shading; glow < 1 and a subtle multiply tint sit it naturally inside a lit/dark set."""
    img = bpy.data.images.load(image_path.replace("\\", "/"), check_existing=True)
    h = width * img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1, location=location, rotation=rotation)
    card = bpy.context.object; card.name = name; card.scale = (width, h, 1)
    m, N, L = _node_mat(name + "_card")
    out = N.new("ShaderNodeOutputMaterial"); tex = N.new("ShaderNodeTexImage"); tex.image = img
    em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    em.inputs["Strength"].default_value = glow
    g = N.new("ShaderNodeMix"); g.data_type = "RGBA"; g.blend_type = "MULTIPLY"; g.inputs["Factor"].default_value = tint_k
    g.inputs["B"].default_value = (*tint, 1)
    L.new(tex.outputs["Color"], g.inputs["A"]); L.new(g.outputs["Result"], em.inputs["Color"]); L.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    L.new(tr.outputs["BSDF"], mix.inputs[1]); L.new(em.outputs["Emission"], mix.inputs[2]); L.new(mix.outputs["Shader"], out.inputs["Surface"])
    try: m.blend_method = "HASHED"
    except Exception: pass
    card.data.materials.append(m); card["card_image"] = img.name
    return card


def contact_shadow(card, surface_z, band=0.035, reach=0.16, strength=0.78, name=None):
    """Build a soft contact-shadow decal on `surface_z` shaped by the card's own alpha near the contact line.
    Lower the card's bottom 2-4 cm below `surface_z` first so edges do not float."""
    import numpy as np
    img = bpy.data.images[card["card_image"]]; iw, ih = img.size
    px = np.empty(iw * ih * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(ih, iw, 4)
    bpy.context.view_layer.update()
    R = card.matrix_world.to_3x3()
    right = R @ Vector((1, 0, 0)); W = right.length; right.normalize()
    up = R @ Vector((0, 1, 0)); H = up.length
    front = R @ Vector((0, 0, 1)); front.z = 0; front.normalize()
    bottom = card.matrix_world.translation - up / 2
    sink = surface_z - bottom.z
    if sink < 0: print(f"contact_shadow: the card's bottom is {-sink:.3f} m ABOVE the surface: lower it first")
    cut = max(0, int(round(sink / H * ih))); rows = px[cut:cut + max(1, int(band / H * ih)), :, 3]
    cov = rows.max(0)
    k = max(3, iw // 60); cov = np.convolve(np.pad(cov, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
    SW, SH = 256, 96
    c = cov[np.linspace(0, iw - 1, SW).astype(int)]
    dist = 1 - np.linspace(0, 1, SH)[:, None]
    dens = np.clip(c[None, :] * (strength * np.exp(-dist / 0.10) + 0.30 * np.exp(-dist / 0.45)), 0, 0.92)
    spx = np.ones((SH, SW, 4), np.float32); spx[..., 3] = dens
    simg = bpy.data.images.new((name or card.name) + "_shadow", SW, SH, alpha=True); simg.pixels.foreach_set(spx.ravel()); simg.pack()
    loc = Vector((bottom.x, bottom.y, surface_z + 0.0015)) + front * (reach / 2 + 0.004)
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(0, 0, math.atan2(right.y, right.x)))
    sh = bpy.context.object; sh.name = (name or card.name) + "_contact"; sh.scale = (W, reach, 1)
    m, N, L = _node_mat(sh.name)
    o = N.new("ShaderNodeOutputMaterial"); t = N.new("ShaderNodeTexImage"); t.image = simg; t.extension = "EXTEND"
    dk = N.new("ShaderNodeBsdfDiffuse"); dk.inputs["Color"].default_value = (0.004, 0.002, 0.008, 1)
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(t.outputs["Alpha"], mx.inputs["Fac"]); L.new(tr.outputs["BSDF"], mx.inputs[1]); L.new(dk.outputs["BSDF"], mx.inputs[2]); L.new(mx.outputs["Shader"], o.inputs["Surface"])
    sh.data.materials.append(m); sh.visible_shadow = False
    return sh


def anime_look(keep=(), no_ink=(), kuwahara=None, ink=True, line=None, ink_color=(0.006, 0.003, 0.012), saturation=1.12, flatten=True, scene=None):
    """Stylise photoreal 3D props toward 2D cel illustration at render time (anisotropic Kuwahara + Freestyle
    silhouette/border ink; Blender 5 compositor node group compatible).
    Set ink=False for quick look-dev passes, and ink=True for finals."""
    sc = scene or bpy.context.scene; W = sc.render.resolution_x
    keep, no_ink = list(keep), list(no_ink)
    skip = {s.material.name for o in keep + no_ink for s in o.material_slots if s.material}
    for o in keep: o.pass_index = 1
    if flatten:
        for mt in bpy.data.materials:
            if mt.name in skip or not mt.node_tree: continue
            for n in mt.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    for l in list(n.inputs["Roughness"].links): mt.node_tree.links.remove(l)
                    n.inputs["Roughness"].default_value = 0.82
                    for nm, v in (("Specular IOR Level", 0.2), ("Coat Weight", 0.0)):
                        if nm in n.inputs: n.inputs[nm].default_value = v
                elif n.type == "NORMAL_MAP": n.inputs["Strength"].default_value = 0.25
                elif n.type == "DISPLACEMENT": n.inputs["Scale"].default_value *= 0.3
    vl = sc.view_layers[0]; vl.use_pass_object_index = True
    if ink:
        hc = bpy.data.collections.get("anime_no_ink") or bpy.data.collections.new("anime_no_ink")
        if hc.name not in sc.collection.children: sc.collection.children.link(hc)
        for o in keep + no_ink:
            for c in list(o.users_collection): c.objects.unlink(o)
            hc.objects.link(o)
        th = line or round(1.5 * W / 960, 2)
        sc.render.use_freestyle = True; sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = th
        vl.use_freestyle = True; fs = vl.freestyle_settings; fs.as_render_pass = True
        ls = fs.linesets.active if len(fs.linesets) else fs.linesets.new("ink")
        ls.select_by_visibility = True; ls.select_by_edge_types = True
        ls.select_silhouette = True; ls.select_border = True; ls.select_crease = False
        ls.select_by_collection = True; ls.collection = hc; ls.collection_negation = "EXCLUSIVE"
        if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new("ink")
        st = ls.linestyle; st.color = ink_color; st.alpha = 0.95; st.thickness = th
    g = bpy.data.node_groups.new("anime_look", "CompositorNodeTree")
    g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = g.nodes, g.links
    rl = N.new("CompositorNodeRLayers"); rl.scene = sc
    kw = N.new("CompositorNodeKuwahara"); kw.inputs["Size"].default_value = int(kuwahara or max(6, round(W / 80)))
    for v in ("Anisotropic", "ANISOTROPIC"):
        try: kw.inputs["Type"].default_value = v; break
        except Exception: pass
    kw.inputs["Uniformity"].default_value = 4; kw.inputs["Sharpness"].default_value = 0.6; kw.inputs["Eccentricity"].default_value = 1.0
    hs = N.new("CompositorNodeHueSat"); hs.inputs["Saturation"].default_value = saturation
    idm = N.new("CompositorNodeIDMask"); idm.inputs["Index"].default_value = 1; idm.inputs["Anti-Alias"].default_value = True
    keepmix = N.new("ShaderNodeMix"); keepmix.data_type = "RGBA"
    out = N.new("NodeGroupOutput")
    bpy.context.view_layer.update()
    L.new(rl.outputs["Image"], kw.inputs["Image"]); L.new(kw.outputs["Image"], hs.inputs["Image"])
    L.new(next(o for o in rl.outputs if o.name in ("Object Index", "IndexOB")), idm.inputs["ID value"])
    L.new(idm.outputs[0], keepmix.inputs["Factor"]); L.new(hs.outputs["Image"], keepmix.inputs[6]); L.new(rl.outputs["Image"], keepmix.inputs[7])
    last = keepmix.outputs[2]
    fso = next((o for o in rl.outputs if "freestyle" in o.name.lower()), None) if ink else None
    if fso is not None:
        inkmix = N.new("ShaderNodeMix"); inkmix.data_type = "RGBA"; sep = N.new("CompositorNodeSeparateColor")
        L.new(fso, sep.inputs[0]); L.new(sep.outputs["Alpha"], inkmix.inputs["Factor"])
        L.new(last, inkmix.inputs[6]); L.new(fso, inkmix.inputs[7]); last = inkmix.outputs[2]
    L.new(last, out.inputs[0])
    sc.compositing_node_group = g
    return g
