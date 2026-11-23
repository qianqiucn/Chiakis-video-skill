"""freesound.py — recorded SFX from Freesound (official API v2): search, fetch into one local library, and keep every
sound's author and licence for the credits card. Run with the vision venv (-I); standard library + ffmpeg.

  freesound.py search "<words>" [--license cc0,by] [--max-dur 6] [--limit 10]
  freesound.py get <id> [--original] [--project <project dir>]
  freesound.py credits <project dir>          # the 音效 lines for the film's credits card
  freesound.py list                           # what the local library holds
  freesound.py auth                           # OAuth2, once: prints the link the client opens and approves
  freesound.py auth --code <code>             # trades the code Freesound then shows for tokens (or <keys>/freesound_code.txt)
  freesound.py auth --status

search: two or three words, source and action ("paper slide"), never mood: every word must match. Freesound's relevance
  order; one line a sound: id · seconds · licence · rating/downloads · author · name. --license takes cc0, by, nc
  (BY-NC: only while the films stay non-commercial); default cc0,by.
get: the HQ preview (ogg ≈ 192 kbps; the key alone allows it), or with --original the uploaded file (wav, flac, aif …;
  OAuth2; 30/min, 500/day), decoded to <lib>/freesound_<id>.wav (48 kHz float). Records page, author, licence, SHA-256
  of the downloaded file, length, peak time (the sync point) and peak dBFS. Sampling+ and any other licence are refused.
Key: env FREESOUND_API_KEY, else ~/.config/chiaki-video/freesound_api_key.txt (never printed), sent as an
  Authorization header, never in a URL. The API is free for non-commercial use only; 60 requests/min, 2000/day.
OAuth2 (originals only): the client id in ~/.config/chiaki-video/freesound_client_id.txt (public: goes in link);
  `auth` writes a PKCE verifier to <keys>/freesound_oauth_pending.json and prints the link; the client signs in and
  approves on freesound.org (never an agent), Freesound shows a code valid 10 minutes, `auth --code` trades it for
  tokens in <keys>/freesound_oauth.json (never printed). The access token lasts 24 h and is refreshed by itself; the
  client can revoke it in the Freesound settings, after which `auth` runs again.
Library: env CHIAKI_SFX or ~/.cache/chiaki-video/sfx (or --lib); <lib>/catalog.json. With --project, get also appends
  the sound to <project>/work/sfx_used.json, which the credits command reads.
"""
import argparse, array, base64, glob, hashlib, json, math, os, secrets, shutil, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://freesound.org/apiv2"
KEYS = os.environ.get("CHIAKI_KEYS_DIR") or os.path.expanduser("~/.config/chiaki-video")
KEY_FILE, CLIENT_ID_FILE = f"{KEYS}/freesound_api_key.txt", f"{KEYS}/freesound_client_id.txt"
OAUTH_FILE, PENDING_FILE, CODE_FILE = f"{KEYS}/freesound_oauth.json", f"{KEYS}/freesound_oauth_pending.json", f"{KEYS}/freesound_code.txt"
REDIRECT = "https://freesound.org/home/app_permissions/permission_granted/"   # Freesound shows the code itself
UA = "quickcut-rank-video-sfx/1.0 (personal non-commercial videos)"
LIC_FILTER = {"cc0": '"Creative Commons 0"', "by": '"Attribution"', "nc": '"Attribution NonCommercial"'}
FIELDS = "id,name,username,license,duration,avg_rating,num_downloads,url,previews,type,samplerate,channels"

ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=("search", "get", "credits", "list", "auth"))
ap.add_argument("args", nargs="*")
ap.add_argument("--license", default="cc0,by"); ap.add_argument("--max-dur", type=float, default=0)
ap.add_argument("--limit", type=int, default=10); ap.add_argument("--project", default="")
ap.add_argument("--original", action="store_true"); ap.add_argument("--code", default="")
ap.add_argument("--status", action="store_true")
ap.add_argument("--lib", default=os.environ.get("CHIAKI_SFX") or os.path.expanduser("~/.cache/chiaki-video/sfx"))
A = ap.parse_args()
LIB = A.lib.replace("\\", "/").rstrip("/")
CAT_PATH = f"{LIB}/catalog.json"


def read1(path, env=""):
    v = os.environ.get(env, "").strip() if env else ""
    if not v and os.path.exists(path): v = open(path, encoding="utf-8-sig").read().strip()
    return v


def key():
    k = read1(KEY_FILE, "FREESOUND_API_KEY")
    if not k: sys.exit(f"no key: the client pastes the Freesound API key into {KEY_FILE} (that line only)")
    return k


def client_id():
    c = read1(CLIENT_ID_FILE, "FREESOUND_CLIENT_ID")
    if not c: sys.exit(f"no client id: copy the «Client id» column of freesound.org/apiv2/apply into {CLIENT_ID_FILE}")
    return c


def http(url, auth="token", timeout=60, data=None):
    h = {"User-Agent": UA}
    if auth == "token": h["Authorization"] = "Token " + key()
    if auth == "bearer": h["Authorization"] = "Bearer " + bearer()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h, data=data), timeout=timeout) as r: return r.read()
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode("utf-8", "replace")
        sys.exit(f"HTTP {e.code} from Freesound: {body}" + ("  (rate limit: wait, never a second key)" if e.code == 429 else ""))


def api(path, **params):
    return json.loads(http(f"{API}/{path}?" + urllib.parse.urlencode(params)).decode("utf-8"))


# ---------------------------------------------------------------- OAuth2 (originals)
def token_call(params):
    """POST to the token endpoint; the client secret only if Freesound asks for it (public clients go without)."""
    for extra in ({}, {"client_secret": key()}):
        req = urllib.request.Request(f"{API}/oauth2/access_token/", headers={"User-Agent": UA},
                                     data=urllib.parse.urlencode({**params, **extra}).encode())
        try:
            with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode("utf-8", "replace")
            if not extra and "invalid_client" in body: continue
            sys.exit(f"token request refused (HTTP {e.code}): {body}")


def save_tokens(d):
    rec = {"access_token": d["access_token"], "refresh_token": d["refresh_token"],
           "expires_at": int(time.time()) + int(d.get("expires_in", 86400)), "scope": d.get("scope", "")}
    tmp = OAUTH_FILE + ".part"; json.dump(rec, open(tmp, "w", encoding="utf-8")); os.replace(tmp, OAUTH_FILE)
    return rec


def bearer():
    if not os.path.exists(OAUTH_FILE): sys.exit("originals need OAuth2: run `freesound.py auth` and have the client approve")
    t = json.load(open(OAUTH_FILE, encoding="utf-8"))
    if t["expires_at"] - 120 < time.time():
        t = save_tokens(token_call({"client_id": client_id(), "grant_type": "refresh_token", "refresh_token": t["refresh_token"]}))
    return t["access_token"]


def auth():
    if A.status:
        if not os.path.exists(OAUTH_FILE): print("not authorised (originals off; previews work with the key)"); return
        t = json.load(open(OAUTH_FILE, encoding="utf-8"))
        left = t["expires_at"] - time.time()
        print(f"authorised; access token {'valid for %.1f h' % (left / 3600) if left > 0 else 'expired (refreshed on next use)'}; refresh token on file")
        return
    code = A.code.strip() or read1(CODE_FILE)
    if not code:                                          # step 1: the link
        cid = client_id()
        verifier = secrets.token_urlsafe(64)[:96]
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        state = secrets.token_urlsafe(16)
        json.dump({"verifier": verifier, "state": state, "made": int(time.time())}, open(PENDING_FILE, "w", encoding="utf-8"))
        print(f"{API}/oauth2/authorize/?" + urllib.parse.urlencode({
            "client_id": cid, "response_type": "code", "redirect_uri": REDIRECT, "state": state,
            "code_challenge": challenge, "code_challenge_method": "S256"}))
        print("the client opens this, signs in, approves; the code Freesound shows goes to `auth --code` within 10 minutes")
        return
    if not os.path.exists(PENDING_FILE): sys.exit("no pending authorisation: run `freesound.py auth` first for a fresh link")
    p = json.load(open(PENDING_FILE, encoding="utf-8"))
    save_tokens(token_call({"client_id": client_id(), "grant_type": "authorization_code", "code": code,
                            "redirect_uri": REDIRECT, "code_verifier": p["verifier"]}))
    for f in (PENDING_FILE, CODE_FILE):
        if os.path.exists(f): os.remove(f)
    print("authorised: tokens saved (not shown); originals on")


# ---------------------------------------------------------------- the library
def lic(url):
    """licence URL -> (class, label): cc0 / by / nc, or None for Sampling+ and anything unknown."""
    u = url.lower()
    ver = next((v for v in ("4.0", "3.0", "2.0", "1.0") if v in u), "")
    if "publicdomain/zero" in u: return "cc0", "CC0"
    if "/by-nc/" in u: return "nc", f"CC BY-NC {ver}".strip()
    if "/by/" in u: return "by", f"CC BY {ver}".strip()
    return None, url


def ffmpeg():
    explicit = ""
    if explicit and os.path.exists(explicit):
        return explicit
    for env in ("CHIAKI_FFMPEG", "FFMPEG_PATH", "QCRV_FFMPEG"):
        v = os.environ.get(env)
        if v and os.path.exists(v):
            return v
    w = shutil.which("ffmpeg")
    if w:
        return w
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    sys.exit("ffmpeg not found: install ffmpeg on PATH or `pip install imageio-ffmpeg`, or set CHIAKI_FFMPEG")


def peak(wav):
    """(peak time s, sample peak dBFS) of the 48 kHz float WAV get writes, channels as recorded (a fold or an upmix
    shifts the level ~3 dB)."""
    b = open(wav, "rb").read(); pos, ch, data = 12, 1, b""
    while pos + 8 <= len(b):
        cid, n = b[pos:pos + 4], int.from_bytes(b[pos + 4:pos + 8], "little")
        if cid == b"fmt ": ch = int.from_bytes(b[pos + 10:pos + 12], "little")
        if cid == b"data": data = b[pos + 8:pos + 8 + n]; break
        pos += 8 + n + (n & 1)
    x = array.array("f"); x.frombytes(data[: len(data) // 4 * 4])
    if not x: return 0.0, -120.0
    i = max(range(len(x)), key=lambda j: abs(x[j]))
    v = abs(x[i])
    return round(i // ch / 48000, 3), (round(20 * math.log10(v), 1) if v > 0 else -120.0)


def catalog():
    return json.load(open(CAT_PATH, encoding="utf-8")) if os.path.exists(CAT_PATH) else {}


def record(rec):
    os.makedirs(LIB, exist_ok=True)
    cat = catalog(); k = f"freesound:{rec['id']}"
    rec["fetched"] = time.strftime("%Y-%m-%d %H:%M"); cat[k] = rec
    tmp = CAT_PATH + ".part"; json.dump(cat, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, CAT_PATH)
    if A.project:
        used_p = f"{A.project.replace(chr(92), '/').rstrip('/')}/work/sfx_used.json"
        os.makedirs(os.path.dirname(used_p), exist_ok=True)
        used = json.load(open(used_p, encoding="utf-8")) if os.path.exists(used_p) else []
        if k not in used: used.append(k)
        json.dump(used, open(used_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return rec


if A.cmd == "auth":
    auth()
elif A.cmd == "search":
    if not A.args: sys.exit('usage: freesound.py search "<words>" [--license cc0,by] [--max-dur 6] [--limit 10]')
    want = [l.strip().lower() for l in A.license.split(",") if l.strip()]
    bad = [l for l in want if l not in LIC_FILTER]
    if bad: sys.exit(f"--license takes cc0, by, nc (got {bad})")
    if "nc" in want: print("note: BY-NC only while the films stay non-commercial")
    f = "license:(" + " OR ".join(LIC_FILTER[l] for l in want) + ")"
    if A.max_dur: f += f" duration:[0 TO {A.max_dur}]"
    d = api("search/", query=" ".join(A.args), filter=f, fields=FIELDS, page_size=min(A.limit, 150))
    print(f"{d['count']} hits" + (f" (first {A.limit})" if d["count"] > A.limit else ""))
    for r in d["results"]:
        print(f"  {r['id']:>8}  {r['duration']:5.1f}s  {lic(r['license'])[1]:13.13s}  {r.get('avg_rating', 0):3.1f}★ "
              f"{r.get('num_downloads', 0):>6}↓  {r['username'][:18]:18s}  {r['name'][:60]}")
elif A.cmd == "get":
    if len(A.args) != 1: sys.exit("usage: freesound.py get <id> [--original] [--project <project dir>]")
    r = api(f"sounds/{int(A.args[0])}/", fields=FIELDS)
    cls, label = lic(r["license"])
    if cls is None: sys.exit(f"refused: licence {label} (only CC0, CC BY, CC BY-NC)")
    if cls == "nc": print("note: BY-NC only while the films stay non-commercial")
    os.makedirs(LIB, exist_ok=True)
    wav = f"{LIB}/freesound_{r['id']}.wav"
    if A.original:
        src, quality = f"{LIB}/freesound_{r['id']}_orig.{(r.get('type') or 'bin').lower()}", "original"
        url, how = f"{API}/sounds/{r['id']}/download/", "bearer"
    else:
        src, quality = f"{LIB}/freesound_{r['id']}.ogg", "preview-hq-ogg"
        url, how = r["previews"]["preview-hq-ogg"], None
    if not os.path.exists(src):
        tmp = src + ".part"
        with open(tmp, "wb") as fh: fh.write(http(url, auth=how, timeout=600))
        os.replace(tmp, src)
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", src, "-ar", "48000", "-c:a", "pcm_f32le", wav], check=True)
    t, db = peak(wav)
    rec = record({"source": "freesound", "id": r["id"], "name": r["name"], "author": r["username"], "license": label,
                  "license_url": r["license"], "page": r["url"], "file": wav, "downloaded": src, "quality": quality,
                  "sha256": hashlib.sha256(open(src, "rb").read()).hexdigest(), "seconds": round(r["duration"], 3),
                  "peak_s": t, "peak_dbfs": db})
    print(json.dumps({k: rec[k] for k in ("id", "name", "author", "license", "page", "quality", "file", "seconds", "peak_s", "peak_dbfs", "sha256")},
                     ensure_ascii=False, indent=1))
    if db < -30: print(f"note: quiet recording ({db} dBFS peak): normalising lifts its noise floor as much; prefer a louder take")
elif A.cmd == "list":
    for k, r in sorted(catalog().items()):
        print(f"{r['id']:>8}  {r['seconds']:5.1f}s  peak {r['peak_s']:6.3f}s  {r['license']:13.13s}  {'orig' if r.get('quality') == 'original' else 'preview':7s}  {r['author'][:18]:18s}  {r['name'][:50]}")
elif A.cmd == "credits":
    if not A.args: sys.exit("usage: freesound.py credits <project dir>")
    used_p = f"{A.args[0].replace(chr(92), '/').rstrip('/')}/work/sfx_used.json"
    cat = catalog(); used = [cat[k] for k in (json.load(open(used_p, encoding="utf-8")) if os.path.exists(used_p) else []) if k in cat]
    if not used: print("(no sounds recorded for this project: pass --project to get)")
    groups = {}
    for r in used: groups.setdefault(r["license"], []).append(r)
    for label in sorted(groups, key=lambda s: (s != "CC0", s)):
        print(f"音效 · Freesound · {label}")
        print("  " + " · ".join(f"“{r['name']}” {r['author']} freesound.org/s/{r['id']}" for r in groups[label]))
