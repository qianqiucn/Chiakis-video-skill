"""skill_check.py — verify consistency, locks, motion-library index, and GitHub hygiene.

Usage:
  python -X utf8 scripts/skill_check.py                      # full consistency + library + workflow + hygiene check
  python -X utf8 scripts/skill_check.py --topic "bezier" "曲线"   # search every rule file for a topic
  python -X utf8 scripts/skill_check.py --dups               # near-duplicate sentences across docs
"""
import glob, hashlib, io, os, re, shutil, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")

FILES = [
    "house-style", "style-grammar", "graphic-design", "motion-library",
    "relief-25d", "mg-styles", "shot-recipes", "script-writing",
    "quality-bar", "crafts", "personas", "build-brief", "production",
]

PRIVATE_LEAK_RE = re.compile(
    r"(C:\\Users\\qianq|C:/Users/qianq|E:\\Claude|E:/Claude|D:\\Tools|D:/Tools|F:\\AI|F:/AI|"
    r"BV1gUxx6dE7X|dashboard-template|opening-template|panel_b\.js|crystal_slab|radar_ticks|"
    r"flagship_watch|codex_lihui|ark_api_key|Artificial Analysis)",
    re.I,
)


def read(p):
    return io.open(p, encoding="utf-8").read()


def texts():
    out = {}
    patterns = [
        ROOT + "/SKILL.md",
        ROOT + "/README.md",
        ROOT + "/references/**/*.md",
        ROOT + "/assets/workflows/*",
        ROOT + "/assets/workflows_agy/*",
        ROOT + "/rules/*.md",
        ROOT + "/agents/*.md",
        ROOT + "/commands/**/*.md",
    ]
    for pat in patterns:
        for p in glob.glob(pat, recursive=True):
            if os.path.isfile(p):
                out[os.path.relpath(p, ROOT).replace("\\", "/")] = read(p)
    return out


def topic(terms):
    t = texts()
    hits = 0
    for name, s in sorted(t.items()):
        for i, line in enumerate(s.split("\n"), 1):
            if any(term.lower() in line.lower() for term in terms):
                hits += 1
                print(f"{name}:{i}: {line.strip()[:220]}")
    print(f"\n{hits} lines mention {terms}.")


def motion_library(problems):
    node = shutil.which("node")
    if not node:
        return "motion library skipped (node not found)"
    r = subprocess.run(
        [node, ROOT + "/scripts/motion_lint.mjs", "--check-library"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        for line in (r.stdout + "\n" + r.stderr).strip().splitlines():
            problems.append("motion-library: " + line)
        return "motion library FAILED"
    last = (r.stdout.strip().splitlines() or ["motion library ok"])[-1]
    return last


def workflow_models(problems):
    # Check JS workflow syntax and model tags
    node = shutil.which("node")
    js_files = sorted(glob.glob(ROOT + "/assets/workflows/*.js"))
    for p in js_files:
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        s = read(p)
        if node:
            chk = subprocess.run(
                [node, "-e", f"new (async()=>{{}}).constructor(require('fs').readFileSync({p!r},'utf8'))"],
                capture_output=True, text=True,
            )
            if chk.returncode != 0:
                problems.append(f"JS syntax error in {rel}: {chk.stderr.strip()[:200]}")
        for m in re.finditer(r"\bagent\s*\(\s*\{", s):
            chunk = s[m.start():m.start() + 500]
            if "model:" not in chunk and "model :" not in chunk:
                problems.append(f"workflow agent() missing explicit model in {rel}")
    # Check AGY Python workflows syntax
    for p in sorted(glob.glob(ROOT + "/assets/workflows_agy/*.py")):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            compile(read(p), rel, "exec")
        except SyntaxError as e:
            problems.append(f"Python syntax error in {rel}: {e}")
    return f"{len(js_files)} JS workflow(s) ok"


def check():
    t = texts()
    problems = []
    heads = {}
    for name, s in t.items():
        if name.endswith(".md"):
            heads[os.path.basename(name)] = set(
                m.group(1) for m in re.finditer(r"^#{2,4}\s+(\d+(?:\.\d+)?[a-z]?)[.\s]", s, re.M)
            )
    ref = re.compile(r"\b(" + "|".join(re.escape(f) for f in FILES) + r")(?:\.md)?`?\s*§\s*(\d+(?:\.\d+)?[a-z]?)")
    for name, s in t.items():
        for m in ref.finditer(s):
            f = m.group(1) + ".md"
            sec = m.group(2)
            if f in heads and sec not in heads[f] and sec.split(".")[0] not in heads[f]:
                problems.append(f"dangling reference: {name} -> {f} §{sec}")

    # Quote markers & terminology
    quote = re.compile("(客户|用户)(说|原话)[：:]?[「“]|原话[：:]?[「“]|the (client|user) said,? [«“\"]")
    for name, s in t.items():
        for i, line in enumerate(s.split("\n"), 1):
            if quote.search(line):
                problems.append(f"client quote marker: {name}:{i}: {line.strip()[:120]}")
            if name.startswith("references/") and "the user" in line:
                problems.append(f'"the user" (write "the client"): {name}:{i}')

    # Hygiene: zero private paths or removed ranking terms across ALL text files
    for pat in [ROOT + "/**/*.md", ROOT + "/**/*.js", ROOT + "/**/*.mjs", ROOT + "/**/*.py", ROOT + "/**/*.json", ROOT + "/**/*.html"]:
        for p in glob.glob(pat, recursive=True):
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            if rel == "scripts/skill_check.py" or "/assets/fonts/" in "/" + rel or "/assets/template/lib/gsap/" in "/" + rel:
                continue
            try:
                txt = read(p)
            except Exception:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                m = PRIVATE_LEAK_RE.search(line)
                if m:
                    problems.append(f"hygiene leak ({m.group(0)}): {rel}:{i}: {line.strip()[:110]}")

    lib_ok = motion_library(problems) + "; " + workflow_models(problems)
    for p in problems:
        print(p)
    if not problems:
        print(f"OK: references resolve, no quotes, zero private leaks, {lib_ok}")
        return 0
    print(f"\n{len(problems)} problem(s)")
    return 1


def dups():
    t = {k: v for k, v in texts().items() if k == "SKILL.md" or k.startswith("references/")}
    norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()
    seen = {}
    found = 0
    for name, s in sorted(t.items()):
        for i, line in enumerate(s.splitlines(), 1):
            clean = line.strip()
            if len(clean) < 55 or clean.startswith(("|", "#", "```", ">")):
                continue
            k = norm(clean)
            if len(k) < 40:
                continue
            if k in seen:
                print(f"DUP: {seen[k]}  ==  {name}:{i}\n  {clean[:140]}")
                found += 1
            else:
                seen[k] = f"{name}:{i}"
    print(f"{found} duplicate line(s)")
    return 1 if found else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--topic":
        topic(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "--dups":
        sys.exit(dups())
    else:
        sys.exit(check())
