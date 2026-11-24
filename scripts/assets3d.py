"""assets3d.py — 3D engineer's free asset library: search four open 3D libraries, download into one local cache,
and record every asset's author and licence for end credits. Standard library only; run with `python -X utf8`.

  python -X utf8 scripts/assets3d.py search <source|all> "<words>" [--kind hdri|texture|model] [--license cc0,by] [--limit 8]
  python -X utf8 scripts/assets3d.py get <source> <id> [--res 1k|2k|4k] [--format gltf|blend] [--project <project dir>]
  python -X utf8 scripts/assets3d.py credits <project dir>          # end-credit lines for borrowed 3D assets
  python -X utf8 scripts/assets3d.py list [--source s]              # list locally cached assets

Sources:
  polyhaven  HDRIs, PBR textures, models · CC0 · no account · API terms ask for a named client and a
             «Poly Haven» credit (the credits command adds it)
  ambientcg  PBR materials, HDRIs · CC0 · no account
  sketchfab  models · each model carries its own CC licence (--license by,cc0 filters) · searching
             needs no account; downloading uses the user's API token
  blenderkit free models, materials, HDRIs · royalty-free or CC0 · searching needs no account;
             downloading uses the user's API key

Optional tokens (never typed by an agent): put them in <lib>/tokens.json as
  {"sketchfab": "...", "blenderkit": "..."}
or set environment variables SKETCHFAB_TOKEN / BLENDERKIT_API_KEY.

Library directory: CHIAKI_ASSETS3D or ~/.cache/chiaki-video/assets3d (override with --lib).
<lib>/catalog.json holds one record per downloaded asset (source, id, name, kind, author, licence, page, local files).
With --project, `get` appends the asset to <project>/work/assets3d_used.json for the `credits` command.
"""
import argparse, hashlib, json, os, re, sys, time, urllib.parse, urllib.request, uuid, zipfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

UA = "chiaki-video-assets3d/1.0 (https://github.com/qianqiucn/Chiakis-video-skill)"
DEFAULT_LIB = os.environ.get("CHIAKI_ASSETS3D") or os.path.join(os.path.expanduser("~"), ".cache", "chiaki-video", "assets3d")

ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=("search", "get", "credits", "list"))
ap.add_argument("args", nargs="*")
ap.add_argument("--kind", default=""); ap.add_argument("--license", default=""); ap.add_argument("--limit", type=int, default=8)
ap.add_argument("--res", default="1k"); ap.add_argument("--format", default="gltf"); ap.add_argument("--project", default="")
ap.add_argument("--source", default=""); ap.add_argument("--lib", default=DEFAULT_LIB)
A = ap.parse_args()
LIB = A.lib.replace("\\", "/").rstrip("/")
os.makedirs(f"{LIB}/cache", exist_ok=True)
CAT_PATH = f"{LIB}/catalog.json"


def http(url, headers=None, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def jget(url, headers=None):
    return json.loads(http(url, headers).decode("utf-8"))


def fetch(url, dest, md5=None, headers=None):
    """Download to dest (skipped when already present with matching md5); returns dest."""
    if os.path.exists(dest) and (not md5 or hashlib.md5(open(dest, "rb").read()).hexdigest() == md5):
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    with open(tmp, "wb") as f: f.write(http(url, headers, timeout=600))
    if md5 and hashlib.md5(open(tmp, "rb").read()).hexdigest() != md5:
        os.remove(tmp); raise RuntimeError(f"md5 mismatch for {url}")
    os.replace(tmp, dest)
    return dest


def tokens():
    t = {}
    p = f"{LIB}/tokens.json"
    if os.path.exists(p):
        try: t = json.load(open(p, encoding="utf-8"))
        except Exception as e: sys.exit(f"{p} is not valid JSON: {e}")
    t.setdefault("sketchfab", os.environ.get("SKETCHFAB_TOKEN", ""))
    t.setdefault("blenderkit", os.environ.get("BLENDERKIT_API_KEY", ""))
    return t


def catalog():
    return json.load(open(CAT_PATH, encoding="utf-8")) if os.path.exists(CAT_PATH) else {}


def record(rec):
    cat = catalog(); key = f"{rec['source']}:{rec['id']}"
    rec["fetched"] = time.strftime("%Y-%m-%d %H:%M"); cat[key] = rec
    tmp = CAT_PATH + ".part"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cat, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, CAT_PATH)
    if A.project:
        used_p = f"{A.project.replace(chr(92), '/').rstrip('/')}/work/assets3d_used.json"
        os.makedirs(os.path.dirname(used_p), exist_ok=True)
        raw = json.load(open(used_p, encoding="utf-8")) if os.path.exists(used_p) else {}
        if isinstance(raw, list):
            # Upgrade legacy list-of-keys format seamlessly into self-contained metadata dict
            used = {k: {m: cat[k].get(m, "") for m in ("source", "id", "name", "kind", "author", "license", "page")} for k in raw if k in cat}
        else:
            used = dict(raw)
        used[key] = {m: rec.get(m, "") for m in ("source", "id", "name", "kind", "author", "license", "page")}
        with open(used_p, "w", encoding="utf-8") as fh:
            json.dump(used, fh, ensure_ascii=False, indent=1)
    return rec


def words(q): return [w for w in re.split(r"[\s,]+", q.lower()) if w]


# ---------------------------------------------------------------- Poly Haven
PH_KIND = {"hdri": "hdris", "texture": "textures", "model": "models"}
PH_TYPE = {0: "hdri", 1: "texture", 2: "model"}


def ph_index(kind):
    p = f"{LIB}/cache/polyhaven_{kind}.json"
    if not os.path.exists(p) or time.time() - os.path.getmtime(p) > 86400:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(jget(f"https://api.polyhaven.com/assets?t={PH_KIND[kind]}"), fh)
    return json.load(open(p, encoding="utf-8"))


def ph_search(q, kinds):
    out, ws = [], words(q)
    for k in kinds:
        for aid, a in ph_index(k).items():
            hay = " ".join([aid, a.get("name", "")] + a.get("tags", []) + a.get("categories", [])).lower()
            score = sum(1 for w in ws if w in hay)
            if score:
                out.append((score, a.get("download_count", 0), {
                    "source": "polyhaven", "id": aid, "name": a.get("name", aid), "kind": k,
                    "author": ", ".join(a.get("authors", {})), "license": "CC0",
                    "extra": ", ".join(a.get("categories", [])[:3]),
                }))
    return [r for _, _, r in sorted(out, key=lambda t: (-t[0], -t[1]))]


def ph_get(aid):
    info = jget(f"https://api.polyhaven.com/info/{aid}")
    files = jget(f"https://api.polyhaven.com/files/{aid}")
    kind = PH_TYPE.get(info.get("type"), "model"); res = A.res.lower(); d = f"{LIB}/polyhaven/{PH_KIND[kind]}/{aid}/{res}"
    got = []
    if kind == "hdri":
        f = files["hdri"][res]["hdr"]; got.append(fetch(f["url"], f"{d}/{os.path.basename(f['url'])}", f.get("md5")))
    elif kind == "texture":
        for m in ("Diffuse", "nor_gl", "Rough", "arm", "AO", "Metal", "Displacement"):
            if m in files and res in files[m]:
                fm = files[m][res]; f = fm.get("jpg") or fm.get("png") or next(iter(fm.values()))
                got.append(fetch(f["url"], f"{d}/{os.path.basename(f['url'])}", f.get("md5")))
    else:
        fmt = A.format if A.format in files else "gltf"
        f = files[fmt][res][fmt]; main = fetch(f["url"], f"{d}/{os.path.basename(f['url'])}", f.get("md5")); got.append(main)
        for rel, inc in (f.get("include") or {}).items():
            fetch(inc["url"], f"{d}/{rel}", inc.get("md5"))
    return record({
        "source": "polyhaven", "id": aid, "name": info.get("name", aid), "kind": kind,
        "author": ", ".join(info.get("authors", {})), "license": "CC0",
        "page": f"https://polyhaven.com/a/{aid}", "res": res,
        "main": d if kind == "texture" or not got else got[0], "files": got,
    })


# ---------------------------------------------------------------- ambientCG
def acg_search(q, kinds):
    types = {"texture": "Material", "hdri": "HDRI"}
    out = []
    for k in kinds:
        if k not in types: continue
        d = jget(f"https://ambientcg.com/api/v2/full_json?type={types[k]}&q={urllib.parse.quote(q)}&limit={A.limit}&sort=Popular&include=tagData")
        for a in d.get("foundAssets", []):
            out.append({
                "source": "ambientcg", "id": a["assetId"], "name": a["assetId"], "kind": k,
                "author": "ambientCG", "license": "CC0", "extra": ", ".join(a.get("tags", [])[:4]),
            })
    return out


def acg_get(aid):
    d = jget(f"https://ambientcg.com/api/v2/full_json?id={urllib.parse.quote(aid)}&include=downloadData")
    if not d.get("foundAssets"): sys.exit(f"ambientcg: no asset {aid}")
    a = d["foundAssets"][0]; want = A.res.upper() + "-JPG"
    dl = []
    for folder in a.get("downloadFolders", {}).values():
        for cat in folder.get("downloadFiletypeCategories", {}).values(): dl += cat.get("downloads", [])
    pick = next((x for x in dl if x["attribute"] == want), None) or next((x for x in dl if x["attribute"].endswith("-JPG")), None) or (dl[0] if dl else None)
    if not pick: sys.exit(f"ambientcg: {aid} has no download")
    d0 = f"{LIB}/ambientcg/{aid}/{pick['attribute']}"; z = f"{d0}.zip"
    fetch(pick["downloadLink"], z)
    with zipfile.ZipFile(z) as zf: zf.extractall(d0)
    files = sorted(f"{d0}/{n}" for n in os.listdir(d0))
    kind = "hdri" if a.get("dataType") == "HDRI" else "texture"
    main = next((f for f in files if f.lower().endswith((".exr", ".hdr"))), d0) if kind == "hdri" else d0
    return record({
        "source": "ambientcg", "id": aid, "name": aid, "kind": kind,
        "author": "ambientCG", "license": "CC0", "page": f"https://ambientcg.com/view?id={aid}",
        "res": pick["attribute"], "main": main, "files": files,
    })


# ---------------------------------------------------------------- Sketchfab
SF_LIC = {"cc0": "cc0", "by": "by", "by-sa": "by-sa", "by-nd": "by-nd", "by-nc": "by-nc", "by-nc-sa": "by-nc-sa", "by-nc-nd": "by-nc-nd"}


def sf_search(q, kinds):
    if kinds and "model" not in kinds: return []
    lic = [l for l in A.license.split(",") if l in SF_LIC] or [""]
    out = []
    for l in lic:
        url = f"https://api.sketchfab.com/v3/search?type=models&downloadable=true&count={A.limit}&q={urllib.parse.quote(q)}" + (f"&license={l}" if l else "")
        for m in jget(url).get("results", []):
            L = m.get("license") or {}
            out.append({
                "source": "sketchfab", "id": m["uid"], "name": m["name"], "kind": "model",
                "author": m["user"].get("displayName") or m["user"]["username"],
                "license": L.get("label", "?") if isinstance(L, dict) else str(L),
                "extra": f"{m.get('faceCount', '?')} faces",
            })
    return out


def sf_get(uid):
    tok = tokens()["sketchfab"]
    info = jget(f"https://api.sketchfab.com/v3/models/{uid}")
    if not tok: sys.exit("sketchfab: downloading needs your API token in tokens.json (or SKETCHFAB_TOKEN); search works without it")
    d = jget(f"https://api.sketchfab.com/v3/models/{uid}/download", {"Authorization": f"Token {tok}"})
    g = d.get("gltf") or d.get("glb")
    if not g: sys.exit(f"sketchfab: {uid} offers no glTF download: {list(d)}")
    d0 = f"{LIB}/sketchfab/{uid}"; z = fetch(g["url"], f"{d0}/model.zip")
    with zipfile.ZipFile(z) as zf: zf.extractall(d0)
    main = next((os.path.join(r, f).replace("\\", "/") for r, _, fs in os.walk(d0) for f in fs if f.lower().endswith((".gltf", ".glb"))), d0)
    L = info.get("license") or {}
    return record({
        "source": "sketchfab", "id": uid, "name": info.get("name", uid), "kind": "model",
        "author": (info.get("user") or {}).get("displayName") or (info.get("user") or {}).get("username", "?"),
        "license": L.get("label", "?") if isinstance(L, dict) else str(L),
        "page": info.get("viewerUrl", f"https://sketchfab.com/3d-models/{uid}"),
        "main": main, "files": [main],
    })


# ---------------------------------------------------------------- BlenderKit
BK_KIND = {"model": "model", "texture": "material", "hdri": "hdr"}


def bk_search(q, kinds):
    out = []
    for k in kinds or ("model",):
        if k not in BK_KIND: continue
        url = f"https://www.blenderkit.com/api/v1/search/?query={urllib.parse.quote(q)}+asset_type:{BK_KIND[k]}+is_free:true&page_size={A.limit}"
        for a in jget(url).get("results", []):
            out.append({
                "source": "blenderkit", "id": a["assetBaseId"], "name": a.get("name", ""), "kind": k,
                "author": (a.get("author") or {}).get("fullName", "?"), "license": a.get("license", "?"),
                "extra": ", ".join(sorted({f.get("fileType", "") for f in a.get("files", []) if f.get("fileType") in ("blend", "gltf")})),
            })
    return out


def bk_get(base_id):
    key = tokens()["blenderkit"]
    res = jget(f"https://www.blenderkit.com/api/v1/search/?query=asset_base_id:{base_id}").get("results", [])
    if not res: sys.exit(f"blenderkit: no asset {base_id}")
    a = res[0]
    if not key: sys.exit("blenderkit: downloading needs your API key in tokens.json (or BLENDERKIT_API_KEY); search works without it")
    want = "gltf" if A.format == "gltf" else "blend"
    f = next((x for x in a.get("files", []) if x.get("fileType") == want), None) or next((x for x in a.get("files", []) if x.get("fileType") == "blend"), None)
    if not f: sys.exit(f"blenderkit: {base_id} has no {want} file")
    meta = jget(f["downloadUrl"] + ("&" if "?" in f["downloadUrl"] else "?") + f"scene_uuid={uuid.uuid4()}", {"Authorization": f"Bearer {key}"})
    url = meta.get("filePath")
    if not url: sys.exit(f"blenderkit: no file path in the reply: {meta}")
    d0 = f"{LIB}/blenderkit/{base_id}"
    name = (re.sub(r"[^\w.-]+", "_", a.get("name", base_id))[:60].strip("._") or base_id) + (".blend" if f["fileType"] == "blend" else ".zip")
    p = fetch(url, f"{d0}/{name}")
    with open(p, "rb") as fh: head = fh.read(8)
    ext = ".zip" if head[:2] == b"PK" else ".glb" if head[:4] == b"glTF" else ".blend" if head[:7] == b"BLENDER" else os.path.splitext(p)[1]
    if not p.endswith(ext):
        q = os.path.splitext(p)[0] + ext; os.replace(p, q); p = q
    main = p
    if p.endswith(".zip"):
        with zipfile.ZipFile(p) as zf: zf.extractall(d0)
        main = next((os.path.join(r, x).replace("\\", "/") for r, _, fs in os.walk(d0) for x in fs if x.lower().endswith((".gltf", ".glb"))), d0)
    return record({
        "source": "blenderkit", "id": base_id, "name": a.get("name", base_id),
        "kind": {"material": "texture", "hdr": "hdri"}.get(a.get("assetType"), "model"),
        "author": (a.get("author") or {}).get("fullName", "?"), "license": a.get("license", "?"),
        "page": f"https://www.blenderkit.com/asset-gallery-detail/{a.get('id', base_id)}/",
        "main": main, "files": [main],
    })


SEARCH = {"polyhaven": ph_search, "ambientcg": acg_search, "sketchfab": sf_search, "blenderkit": bk_search}
GET = {"polyhaven": ph_get, "ambientcg": acg_get, "sketchfab": sf_get, "blenderkit": bk_get}

if A.cmd == "search":
    if len(A.args) < 2: sys.exit('usage: assets3d.py search <source|all> "<words>" [--kind ...]')
    src, q = A.args[0], " ".join(A.args[1:])
    kinds = [A.kind] if A.kind else ["model", "texture", "hdri"]
    lic = [l.strip().lower() for l in A.license.split(",") if l.strip()]
    for s in (SEARCH if src == "all" else {src: SEARCH[src]}):
        try: rows = SEARCH[s](q, kinds)
        except Exception as e: print(f"[{s}] search failed: {e}"); continue
        if lic and s != "sketchfab":
            rows = [r for r in rows if any(l in r["license"].lower().replace(" ", "") for l in lic) or ("cc0" in lic and r["license"] == "CC0")]
        print(f"[{s}] {len(rows)} hits" + (f" (first {A.limit})" if len(rows) > A.limit else ""))
        for r in rows[:A.limit]:
            print(f"  {r['id']:40.40s}  {r['kind']:7s}  {r['license']:28.28s}  {r['author'][:24]:24s}  {r['name'][:40]}  {r['extra'][:40]}")
elif A.cmd == "get":
    if len(A.args) != 2: sys.exit("usage: assets3d.py get <source> <id> [--res 1k] [--format gltf|blend] [--project dir]")
    rec = GET[A.args[0]](A.args[1])
    print(json.dumps({k: rec[k] for k in ("source", "id", "name", "kind", "author", "license", "page", "main")}, ensure_ascii=False, indent=1))
elif A.cmd == "list":
    for k, r in sorted(catalog().items()):
        if A.source and r["source"] != A.source: continue
        print(f"{k:50.50s}  {r['kind']:7s}  {r['license']:24.24s}  {r['author'][:24]:24s}  {r['main']}")
elif A.cmd == "credits":
    if not A.args: sys.exit("usage: assets3d.py credits <project dir>")
    used_p = f"{A.args[0].replace(chr(92), '/').rstrip('/')}/work/assets3d_used.json"
    cat = catalog()
    raw = json.load(open(used_p, encoding="utf-8")) if os.path.exists(used_p) else {}
    if isinstance(raw, dict):
        # Self-contained per-project records work even when CHIAKI_ASSETS3D is unset or moved
        used = [v if isinstance(v, dict) else cat[k] for k, v in raw.items() if isinstance(v, dict) or k in cat]
    else:
        used = [cat[k] for k in raw if k in cat]
    models = [r for r in used if r["kind"] == "model"]
    if models:
        by_src = {}
        for r in models: by_src.setdefault((r["source"], r["license"]), []).append(r)
        for (s, lic), rs in by_src.items():
            label = {"sketchfab": "Sketchfab", "blenderkit": "BlenderKit", "polyhaven": "Poly Haven"}.get(s, s)
            print(f"3D 模型 · {label} · {lic}")
            print("  " + " · ".join(f"“{r['name']}” {r['author']}" for r in rs))
    tex = sorted({{"polyhaven": "Poly Haven", "ambientcg": "ambientCG", "blenderkit": "BlenderKit"}.get(r["source"], r["source"]) for r in used if r["kind"] != "model"})
    if tex:
        print("贴图与环境 · CC0" if all(r["license"] == "CC0" for r in used if r["kind"] != "model") else "贴图与环境")
        print("  " + " · ".join(tex))
    if not used: print("(no assets recorded for this project: pass --project to get)")
