# -*- coding: utf-8 -*-
r"""fonts.py — 字体库工具（平面设计师用）：在线搜字 → 下载入库（记作者、授权）→ 放进项目（子集 + 页面加载代码）→ 样张。

只收能免费商用、能做进视频的字体：OFL-1.1、Apache-2.0、UFL-1.0、CC0、MIT、Unlicense、IPA。不登录、不买、不碰授权不明的站。
库：默认 <skill>/assets/fonts（环境变量 CHIAKI_FONTS 可改）。<家族>\ 放字体文件和授权原文；catalog.json 是索引，catalog.md 是给人看的
目录（按风格组），specimen\ 是样张。运行：python -X utf8 scripts/fonts.py <子命令> …

  search [关键词] [--group 组] [--cat serif|sans|display|handwriting|mono] [--script zh|tc|jp|ko|latin]
         [--tag Techno] [--var] [--color] [-n 30] [--refresh]
         搜在线目录：Google Fonts 全部（带官方风格标签）+ Fontsource 独有的 + fonts_starter.json 里的 GitHub 字体
  search --local [关键词] [--group 组] [--tag Techno] [--script zh|tc|jp|ko|latin|cyrillic|arabic…] [--cat …] [--var]
         [--text "谁最强"] [-n 50]   只搜库里的（精选架 ★ 在前，其余按 Google 热度）；--text 按缺字多少排，列出缺哪些字
         --tag 写英文或中文都行（Techno = 科技；写「衬线」= 中文名里带衬线的几个标签）；关键词也搜标签的中文名
  get <家族 …|starter> [--group 组] [--fits "适合什么片子、怎么用"] [--pick 文件名,…] [--designers-en "A,B"] [--force]
      写了 --fits 的家族上精选架（catalog.md 带用法说明的那部分）；没写的进全量索引（catalog_all.md）
  get --all-google [--jobs 4] [--retries 3] [--limit N] [--estimate]
      Google Fonts 全部家族逐个走上面同一套下载和授权核对；已在库里的跳过（中断了再跑同一条就从断点续上），网络错误
      自动重试，核对不过的记下来跳过。每个家族一行进度，日志和失败清单在 <库>\_logs\。--estimate 只估算大小和用时、不下载
  get --url <字体或 zip 直链> --family 名 --license OFL-1.1 --license-url <授权原文直链>
      [--designers "甲,乙"] [--designers-en "Jia,Yi"] [--home 主页] [--pick 文件名,…] [--group 组] [--fits …]
      授权硬核对：授权原文必须是该授权的正文，不分大小写、不管换行和 Markdown 排版。OFL 要有标题、Version 1.1 和正文
      Permission & Conditions 一节（只有开头一句声明不算），Apache 要有 TERMS AND CONDITIONS FOR USE…，MIT 要有 THE SOFTWARE
      IS PROVIDED；声明 MIT/Unlicense/CC0/IPA 时原文里不能混着 OFL、Apache 等别的授权，字体文件 name 表也只能写同一种或不写。
      name 表 13/14 写着允许列表以外的授权（GPL、CC BY…），或 0/13/14 有「仅限个人使用」「不可商用」一类限制，也不收。
      不收 = 什么都不写进库、退出码 1。name 表写的是另一种也在允许列表里的授权（OFL 字体写着 Apache 之类）照收，条目 note
      记一句、鸣谢按授权文件。catalog 每次重写目录也核对一遍（这种提示不算失败）。
      --designers-en：片尾英文鸣谢用的作者名（作者名是中文时必给，英文行里不能有中文和全角标点）
  use <项目> [家族[:字重] …] [--full | --subset] [--static] [--alias 页面里的名字] [--text "额外的字"] [--remove 家族] [--check]
      复制进 <项目>\web\assets\fonts\（中文按项目里出现的字做子集，WOFF2），写 fontpack.js，index.html 接好；不给家族 = 按新文案重做
      --static：描边 / 空心字用。从库里的可变字体切出写明的那个字重（"Montserrat:900"），其余轴取默认值，并合并重叠的
      轮廓（可变字体的笔画是叠着画的，描边会露出字里的接缝线）；静态字体也合并一遍。不用另外下载
  specimen [--group 组,…] [--family 家族,…] [--text "样字"] [--out 文件.png]    样张 PNG（红字 = 这个字体缺的字）
      不给 --family 时只画精选架：specimen\<组>.png；--family 可以是库里任何家族，出到 specimen\family_<家族名>.png
      （不会盖掉组样张）；--text 默认只排精选架，加 --all 排全库
  specimen --all [--group 组,…] [--per-page 40]   全量分页样张 specimen\all\<组>_<页>.png（每行左边写字名），顺序和
      catalog_all.md 一致，画完把页码写回 catalog_all.md。中日韩字体排本文字（下面一行小字英文）；拉丁字母齐全的排一句
      英文，Google 记的主文字是别的（天城、泰、阿拉伯…）就在下面小一行排它自己的字母；其余文字用它自己的字母
  credits <项目>        片尾鸣谢（中英）
  groups                风格组一览
  catalog [--rescan]    重写 catalog.md（精选架 + 各组概览）和 catalog_all.md（全量索引）（--rescan 重新读字体文件）；
                        同时重算保留名、核对全库授权，有核对不过的退出码 1
"""
import argparse
import array
import base64
import bisect
import csv
import datetime
import html
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.client import HTTPException      # not `import http.client`: the module's own http() would shadow it

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')   # -I ignores PYTHONUTF8; the console default is GBK
    except Exception:  # noqa: BLE001
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
LIB = os.environ.get('CHIAKI_FONTS') or os.environ.get('CHIAKI_FONTS') or os.path.join(SKILL, 'assets', 'fonts')
STARTER = os.path.join(HERE, 'fonts_starter.json')
LIB_JS = os.path.join(SKILL, 'assets', 'template', 'lib', 'fonts.js')
CDP = os.path.join(HERE, '_cdp.mjs')
_RQ = None


def run_queue():
    """scripts/run_queue.py, the machine-wide queue every headless Chrome goes through (production.md Toolkit «Rules»),
    loaded by its path: python -X utf8 keeps this folder off sys.path."""
    global _RQ
    if _RQ is None:
        spec = importlib.util.spec_from_file_location('run_queue', os.path.join(HERE, 'run_queue.py'))
        _RQ = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_RQ)
    return _RQ


CATALOG = os.path.join(LIB, 'catalog.json')
CATALOG_MD = os.path.join(LIB, 'catalog.md')
CATALOG_ALL_MD = os.path.join(LIB, 'catalog_all.md')
SPECIMEN = os.path.join(LIB, 'specimen')
SPECIMEN_ALL = os.path.join(SPECIMEN, 'all')
SPEC_PAGES = os.path.join(SPECIMEN_ALL, '_pages.json')     # family → sheet name, written by specimen --all
CACHE = os.path.join(LIB, '_cache')
LOGS = os.path.join(LIB, '_logs')
CMAP_INDEX = os.path.join(LIB, '_index', 'cmaps.json')    # every face's character set, so --text needs no font parsing
UA = 'chiaki-video-fonts/1.0 (local 2D video pipeline)'
GF_META = 'https://fonts.google.com/metadata/fonts'
GF_LIST = 'https://fonts.google.com/download/list?family='
GF_TAGS = 'https://raw.githubusercontent.com/google/fonts/main/tags/all/families.csv'
FS_API = 'https://api.fontsource.org/v1/fonts'

LICENSES = {'OFL-1.1': 'SIL Open Font License 1.1', 'Apache-2.0': 'Apache License 2.0', 'UFL-1.0': 'Ubuntu Font Licence 1.0',
            'CC0-1.0': 'CC0 1.0', 'MIT': 'MIT License', 'Unlicense': 'The Unlicense', 'IPA': 'IPA Font License 1.0'}
LICENSE_FILE = {'OFL-1.1': 'OFL.txt', 'UFL-1.0': 'UFL.txt'}            # others: LICENSE.txt
# Hard check: the licence text must hold each of these. Matched against lic_flat(text) — HTML entities decoded, Markdown
# markup dropped, whitespace collapsed, lower case — so a reflowed or Markdown copy reads like the plain one. Licences
# with conditions (OFL, Apache, UFL, MIT) also need a phrase from the body: a copyright header or a "Licensed under …"
# notice already names the licence and its version, and the file goes into every project that uses the font.
LICENSE_PROOF = {
    'OFL-1.1': [('SIL Open Font License', r'sil open font licen[cs]e'), ('Version 1.1 / v1.1', r'\b(?:version|v) ?1\.1\b'),
                ('Permission & Conditions（OFL 正文那一节）', r'\bpermission ?(?:&|and) ?conditions\b')],
    'Apache-2.0': [('Apache License', r'apache licen[cs]e'), ('Version 2.0', r'\bversion 2\.0\b'),
                   ('TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION（Apache 正文）',
                    r'\bterms and conditions for use, reproduction,? and distribution\b')],
    'UFL-1.0': [('UBUNTU FONT LICENCE Version 1.0', r'ubuntu font licen[cs]e,? version 1\.0\b'),
                ('PERMISSION & CONDITIONS（UFL 正文那一节）', r'\bpermission ?(?:&|and) ?conditions\b')],
    'CC0-1.0': [('CC0 1.0 Universal', r'\bcc0 1\.0 universal\b')],
    'MIT': [('Permission is hereby granted, free of charge', r'\bpermission is hereby granted, free of charge\b'),
            ('THE SOFTWARE IS PROVIDED', r'\bthe software is provided\b')],     # the OFL says THE FONT SOFTWARE IS PROVIDED
    'Unlicense': [('This is free and unencumbered', r'\bthis is free and unencumbered\b')],
    'IPA': [('IPA Font License Agreement', r'\bipa font license agreement\b')]}
# Declared MIT / Unlicense / CC0 / IPA: the text must not be (or carry) another licence as well. The OFL's own PERMISSION &
# CONDITIONS starts "Permission is hereby granted, free of charge" like MIT, and a repository's MIT file often covers its code.
STRICT_LICENSES = ('MIT', 'Unlicense', 'CC0-1.0', 'IPA')
LICENSE_FOREIGN = [('SIL Open Font License', r'\bopen font licen[cs]e\b'), ('Apache License', r'\bapache licen[cs]e\b'),
                   ('Ubuntu Font Licence', r'\bubuntu font licen[cs]e\b'),
                   ('GNU General Public License', r'\bgnu (?:lesser |library |affero )?general public licen[cs]e\b')]
# Cross-check: what name IDs 13/14 inside the font files say. A licence outside the allowed list (and not the declared one)
# → refused; another allowed one → kept with a note (Roboto Condensed: OFL.txt, name table Apache). Declared MIT /
# Unlicense / CC0 / IPA and the font names something else → refused (the font's own word beats a repository's file).
NAME_LICENSE = [('OFL-1.1', r'open\s*font\s*licen[cs]e|\bOFL\b|scripts\.sil\.org|openfontlicense\.org'),
                ('Apache-2.0', r'apache\s+licen[cs]e|apache\.org/licenses'),
                ('UFL-1.0', r'ubuntu\s+font\s+licen[cs]e|font\.ubuntu\.com/(?:ufl|licen)'),
                ('MIT', r'(?-i:\bMIT\b)|opensource\.org/licenses/mit|'       # MIT's grant, not the OFL's "…a copy of the Font Software"
                        r'permission\s+is\s+hereby\s+granted,?\s+free\s+of\s+charge,?\s+to\s+any\s+person\s+obtaining\s+a\s+copy\s+of\s+this\s+software'),
                ('CC0-1.0', r'\bCC0\b|creativecommons\.org/publicdomain/zero'),
                ('Unlicense', r'\bunlicense\b|unlicense\.org|free and unencumbered'),
                ('IPA', r'\bIPA\s+font\s+licen[cs]e|ipa\.go\.jp|opensource\.org/licenses/IPA'),
                ('GPL', r'\b[AL]?GPL\b|GNU\s+(?:Lesser\s+|Library\s+|Affero\s+)?General\s+Public'),
                ('CC BY', r'creativecommons\.org/licenses/|\bCC[- ]BY\b|Creative\s+Commons\s+Attribution')]
# Restrictions in name IDs 0/13/14 → refused. First the harmless pairs are blanked out: "personal and commercial use",
# "commercial or non-commercial purposes" (the Unlicense and the IPA agreement both say that) — unless "not for" / "no"
# comes before or "is not / requires …" after. (?<!non…) keeps the "commercial" inside "non-commercial" from starting one.
_USE = r'(?:\s+(?:use|usage|purposes?|projects?|works?))?'
_PERS = r'(?:personal|private|non[\s-]?commercial(?:ly)?)'
_COMM = r'(?<!non)(?<!non-)(?<!non\s)commercial(?:ly)?'
_AND = r'\s*(?:and/or|and|or|&|/|\+)\s*(?:for\s+)?'
_CREDIT = r'(?!\s+(?:be\s+)?(?:an?\s+|the\s+)?(?:attribut|credit|acknowledg|mention|copyright|notice))'   # "requires attribution": fine
_NOT = r'(?:is\s+|are\s+)?(?:strictly\s+)?(?:not\b(?!\s+(?:restricted|limited|prohibited|forbidden)\b)|prohibited|forbidden|' \
       rf'disallowed|(?:requires?|requiring|needs?|must)\b{_CREDIT})'
NAME_BENIGN = rf'(?<!not for )(?<!no )\b(?:{_PERS}{_USE}{_AND}{_COMM}|{_COMM}{_USE}{_AND}{_PERS}){_USE}\b(?!{_USE}\s*[:\-–]?\s*{_NOT})'
NAME_RESTRICT = (r'personal[\s-]+(?:use|usage|purposes?|projects?)\b|\bfor\s+(?:personal|private)(?:\s*(?:and|&|or|/)|'
                 r'\s+(?:use|usage|purposes?|projects?|only)\b)|\bfree\s+for\s+(?:personal|private)\b|non[\s-]?commercial|'
                 r'\bnot\s+for\s+commercial|'
                 r'\bno\s+(?:(?:personal|private)\s*(?:or|and|&|/)\s*)?commercial\s+(?:use|usage|purposes?|projects?|works?)\b|'
                 rf'\bcommercial\s+(?:use|usage|purposes?)\s*[:\-–]?\s*{_NOT}|\bby[\s-]nc\b|\bpaid\s+licen[cs]e|'
                 r'\b(?:purchase|buy)\s+(?:a\s+|the\s+)?(?:\w+\s+)?licen[cs]e|donationware|freeware|shareware|demo\s+version|'
                 r'trial\s+version|evaluation\s+(?:copy|version|only)|\bEULA\b|end[\s-]+user\s+licen[cs]e|commercial\s+licen[cs]e')

# 风格组：key, 中文名, 在线目录里怎么认（Google Fonts 官方标签 ≥ 60 分 / 分类 / 名字 / 可变轴 / 文字）
GROUPS = [
    ('blackletter', '哥特黑体', {'tags': ['/Theme/Blackletter', '/Theme/Medieval']}),
    ('didone', '高反差 / 古典衬线', {'tags': ['/Serif/Didone', '/Serif/Fat Face', '/Serif/Modern', '/Serif/Old Style Garalde',
                                       '/Serif/Transitional', '/Serif/Scotch']}),
    ('condensed', '窄体粗黑', {'name': r'condensed|compressed|narrow', 'not': r'expanded|extended|\bwide', 'wdth': 80}),
    ('tech', '科技 / 科幻', {'tags': ['/Theme/Techno', '/Expressive/Futuristic']}),
    ('pixel', '像素 / 点阵 / 数码管', {'tags': ['/Theme/Pixel'], 'name': r'pixel|dseg|segment|\bdot'}),
    ('mono', '等宽 / 代码', {'cat': ['Monospace']}),
    ('brush', '笔刷 / 马克笔 / 涂鸦', {'tags': ['/Theme/Brush', '/Theme/Distressed']}),
    ('script', '花体 / 连笔手写', {'tags': ['/Script/Formal', '/Script/Handwritten', '/Script/Informal', '/Script/Upright Script']}),
    ('stencil', '模板字', {'tags': ['/Theme/Stencil']}),
    ('decorative', '装饰 / 特效字', {'tags': ['/Theme/Shaded', '/Theme/Inline', '/Theme/Art Deco', '/Theme/Art Nouveau',
                                        '/Theme/Woodtype', '/Theme/Tuscan', '/Theme/Wacky', '/Theme/Blobby'], 'color': True}),
    ('cjk-sans', '中文黑体', {'script': 'zh', 'cat': ['Sans Serif']}),
    ('cjk-serif', '中文宋体 / 仿宋', {'script': 'zh', 'cat': ['Serif']}),
    ('cjk-calligraphy', '中文书法 / 手写', {'script': 'zh', 'cat': ['Handwriting']}),
    ('cjk-display', '中文创意标题', {'script': 'zh', 'cat': ['Display']}),
    ('jp-display', '日文标题', {'script': 'jp'}),
    ('other', '无衬线 / 其他', {}),       # what no rule above takes: in practice the plain Sans Serif families
]
GROUP_ZH = {g: z for g, z, _ in GROUPS}
GROUP_RULE = {g: r for g, _, r in GROUPS}
GROUP_ORDER = [g for g, _, _ in GROUPS]
THEME_FIRST = ('blackletter', 'pixel', 'stencil')   # a theme tag ≥ 60 here outranks Script / Techno tags and the Monospace category
CATS = {'serif': 'Serif', 'sans': 'Sans Serif', 'sans-serif': 'Sans Serif', 'display': 'Display', 'handwriting': 'Handwriting',
        'mono': 'Monospace', 'monospace': 'Monospace'}
SCRIPTS = {'zh': 'zh', 'sc': 'zh', 'hans': 'zh', 'cn': 'zh', 'tc': 'tc', 'hant': 'tc', 'jp': 'jp', 'ja': 'jp', 'ko': 'ko',
           'kr': 'ko', 'latin': 'latin', 'en': 'latin'}
BASE_CHARS = set(chr(c) for c in range(0x20, 0x7F)) | set('，。、！？：；“”‘’（）《》〈〉【】「」『』…—～·￥％＋－×÷＝°±№→←↑↓★☆●○■□▲△◆◇♪・ー')
TEXT_EXT = ('.js', '.mjs', '.html', '.htm', '.json', '.txt', '.md', '.csv', '.tsv', '.srt', '.vtt', '.ass', '.css', '.svg', '.xml')
WEIGHT_WORDS = [('extralight', 200), ('ultralight', 200), ('semibold', 600), ('demibold', 600), ('extrabold', 800),
                ('ultrabold', 800), ('hairline', 100), ('thin', 100), ('light', 300), ('regular', 400), ('book', 400),
                ('normal', 400), ('medium', 500), ('bold', 700), ('black', 900), ('heavy', 900)]
SAMPLES = {
    'zh': ('排行榜第一名 谁最强', '数据雷达 综合得分 98.7 · AI 模型 2026 年度榜单'),
    'tc': ('排行榜第一名 誰最強', '數據雷達 綜合得分 98.7 · AI 模型 2026'),
    'jp': ('最強ランキング 第一位', 'ひらがな カタカナ 漢字 98.7 · AI 2026'),
    'latin': ('GEMINI No.1 Argon', 'The quick brown fox jumps over 0123456789 · 98.7%'),
    'digits': ('88:88 98.7', '-1234.5 0123456789'),
}


# ---------------------------------------------------------------------------------------------------------------- utils
def say(*a):
    print(*a, flush=True)


def today():
    return datetime.date.today().isoformat()


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'font'


def clean_name(name):
    """Google's NotoSansSC[wght].ttf / Doto-VariableFont_ROND,wght.ttf → shell- and glob-safe names."""
    n = os.path.basename(name).replace('[', '-').replace(']', '').replace(',', '-').replace(' ', '-')
    return re.sub(r'-{2,}', '-', n)


def write_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f'{path}.{os.getpid()}-{threading.get_ident()}.part'
    with open(tmp, 'wb') as f:
        f.write(data.encode('utf-8') if isinstance(data, str) else data)
    for i in range(40):     # Windows: replacing fails while another process (a search, the virus scanner) has it open
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == 39:
                os.remove(tmp)
                raise
            time.sleep(0.25)


def http(url, tries=3, timeout=180):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404, 410):
                raise
            last = e
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(1.5 * (i + 1))
    raise last


def cached(name, url, refresh=False, days=7):
    p = os.path.join(CACHE, name)
    if not refresh and os.path.exists(p) and time.time() - os.path.getmtime(p) < days * 86400:
        with open(p, 'rb') as f:
            return f.read()
    try:
        data = http(url)
    except Exception as e:  # noqa: BLE001
        if os.path.exists(p):
            say(f'  （{name} 联网失败，用旧缓存：{e}）')
            with open(p, 'rb') as f:
                return f.read()
        raise SystemExit(f'取不到 {url}：{e}')
    write_atomic(p, data)
    return data


def fmt_mb(n):
    return f'{n / 1048576:.1f} MB' if n >= 1048576 else f'{n / 1024:.0f} KB'


def wrange(w):
    p = [float(x) for x in str(w).split()]
    return p[0], p[-1]


def file_url(path):
    return 'file:///' + urllib.parse.quote(os.path.abspath(path).replace('\\', '/'), safe='/:')


# ------------------------------------------------------------------------------------------------------ online catalogs
_GF, _TAGS, _FS = None, None, None


def gf_meta(refresh=False):
    global _GF
    if _GF is None:
        t = cached('gf_metadata.json', GF_META, refresh).decode('utf-8')
        _GF = {x['family']: x for x in json.loads(t[t.index('{'):])['familyMetadataList']}
    return _GF


def gf_tags(refresh=False):
    global _TAGS
    if _TAGS is None:
        _TAGS = {}
        for r in csv.reader(io.StringIO(cached('gf_tags.csv', GF_TAGS, refresh).decode('utf-8'))):
            if len(r) >= 4 and r[2].startswith('/'):
                try:
                    v = float(r[3])
                except ValueError:
                    continue
                d = _TAGS.setdefault(r[0], {})
                d[r[2]] = max(d.get(r[2], 0), v)
    return _TAGS


def fs_list(refresh=False):
    global _FS
    if _FS is None:
        _FS = json.loads(cached('fontsource.json', FS_API, refresh).decode('utf-8'))
    return _FS


def load_starter():
    with open(STARTER, encoding='utf-8') as f:
        return json.load(f)


def gf_scripts(x):
    subs, ps = set(x.get('subsets') or []), x.get('primaryScript') or ''
    s = []
    if 'chinese-simplified' in subs or ps == 'Hans':
        s.append('zh')
    if subs & {'chinese-traditional', 'chinese-hongkong'} or ps == 'Hant':
        s.append('tc')
    if 'japanese' in subs or ps in ('Jpan', 'Hira'):
        s.append('jp')
    if 'korean' in subs or ps == 'Kore':
        s.append('ko')
    if 'latin' in subs:
        s.append('latin')
    return s


def name_scripts(name, group=''):
    n = f' {name} '
    s = []
    if re.search(r'\b(SC|CN|GB|Hans)\b', n) or group.startswith('cjk'):
        s.append('zh')
    if re.search(r'\b(TC|HK|Hant)\b', n):
        s.append('tc')
    if re.search(r'\b(JP|Jpan)\b', n) or group == 'jp-display':
        s.append('jp')
    if re.search(r'\b(KR|Kore)\b', n):
        s.append('ko')
    return s + ['latin']


def gf_record(fam, x=None):
    x = x or gf_meta()[fam]
    return {'family': fam, 'source': 'Google Fonts', 'category': x.get('category') or '', 'scripts': gf_scripts(x),
            'tags': gf_tags().get(fam, {}), 'axes': x.get('axes') or [], 'styles': list((x.get('fonts') or {}).keys()),
            'designers': x.get('designers') or [], 'color': bool(x.get('colorCapabilities')), 'pop': x.get('popularity') or 9999,
            'subsets': [s for s in x.get('subsets') or [] if s != 'menu'], 'primary_script': x.get('primaryScript') or ''}


_GF_OFF = None


def gf_meta_offline():
    """the cached Google Fonts metadata, however old, never from the network ({} without a cache): popularity, subsets
    and primary script for library entries that predate those fields (the curated shelf), in search / catalog / specimen."""
    global _GF_OFF
    if _GF_OFF is None:
        if _GF is not None:
            _GF_OFF = _GF
        else:
            try:
                with open(os.path.join(CACHE, 'gf_metadata.json'), encoding='utf-8') as f:
                    t = f.read()
                _GF_OFF = {x['family']: x for x in json.loads(t[t.index('{'):])['familyMetadataList']}
            except (OSError, ValueError, KeyError):
                _GF_OFF = {}
    return _GF_OFF


def gf_info(e):
    """(popularity rank, subsets, primary script) of a library entry: its own fields, else the cached metadata."""
    if 'pop' in e:
        return e['pop'], e.get('subsets') or [], e.get('primary_script') or ''
    x = gf_meta_offline().get(e['family']) if e.get('source') == 'Google Fonts' else None
    if not x:
        return 9999, [], ''
    return x.get('popularity') or 9999, [s for s in x.get('subsets') or [] if s != 'menu'], x.get('primaryScript') or ''


def tag_score(g, r):
    return max([r.get('tags', {}).get(t, 0) for t in (GROUP_RULE.get(g) or {}).get('tags', [])] or [0])


def group_score(g, r):
    rule = GROUP_RULE.get(g) or {}
    sc = r.get('scripts') or []
    cjk, jp = ('zh' in sc or 'tc' in sc), 'jp' in sc
    if 'script' in rule:
        if (rule['script'] == 'zh' and not cjk) or (rule['script'] == 'jp' and (not jp or cjk and 'zh' in sc)):
            return 0
        if 'cat' in rule and r.get('category') not in rule['cat']:
            return 0
        return 100
    if 'not' in rule and re.search(rule['not'], r['family'], re.I):
        return 0
    best = tag_score(g, r)
    if best >= 60:
        return best
    if cjk or jp:
        return 0
    if 'name' in rule and re.search(rule['name'], r['family'], re.I):
        return 70
    # a wdth axis alone proves little (plenty of text families have one): counts for Display faces only
    # (a family named condensed / compressed / narrow already scored above)
    if 'wdth' in rule and r.get('category') == 'Display' and \
            any(a.get('tag') == 'wdth' and a.get('min', 100) <= rule['wdth'] for a in r.get('axes') or []):
        return 65
    if rule.get('color') and r.get('color'):
        return 60
    if 'cat' in rule and r.get('category') in rule['cat']:
        return 60
    return 0


def auto_group(r):
    sc = r.get('scripts') or []
    if re.search(r'pixel|dseg', r['family'], re.I):
        return 'pixel'
    if 'zh' in sc or 'tc' in sc:
        return {'Sans Serif': 'cjk-sans', 'Serif': 'cjk-serif', 'Handwriting': 'cjk-calligraphy'}.get(r.get('category'), 'cjk-display')
    if 'jp' in sc:
        return 'jp-display'
    theme = max((tag_score(g, r), -i, g) for i, g in enumerate(THEME_FIRST))
    if theme[0] >= 60:                     # Fruktur: Blackletter 90 beats Script 100; VT323: Pixel beats Monospace
        return theme[2]
    if r.get('category') == 'Monospace':   # before Techno tags (Ubuntu Mono) or a wdth axis (Inconsolata)
        return 'mono'
    best, bg = 0, None
    for g in GROUP_ORDER:
        if g.startswith(('cjk', 'jp')) or g == 'other':
            continue
        s = group_score(g, r)
        if s > best:
            best, bg = s, g
    return bg or {'Monospace': 'mono', 'Handwriting': 'script', 'Display': 'decorative', 'Serif': 'didone'}.get(r.get('category'), 'other')


def online_records(refresh=False):
    meta, fsl = gf_meta(refresh), fs_list(refresh)
    gf_tags(refresh)
    fs_by = {x['family'].lower(): x for x in fsl}
    out, seen = [], set()
    starter = {e['family'].lower(): e for e in load_starter()}
    for e in starter.values():
        if e.get('src') in ('url', 'zip', 'fs'):
            f2 = fs_by.get(e['family'].lower()) or {}
            out.append({'family': e['family'], 'source': 'Fontsource' if e['src'] == 'fs' else 'GitHub', 'category': '',
                        'scripts': name_scripts(e['family'], e['group']), 'tags': {}, 'axes': [], 'styles': [],
                        'license': norm_license(e.get('license') or f2.get('license')) or '?', 'designers': e.get('designers') or [],
                        'color': False, 'pop': 0, 'group': e['group']})
            seen.add(e['family'].lower())
    for fam, x in meta.items():
        r = gf_record(fam, x)
        r['license'] = norm_license((fs_by.get(fam.lower()) or {}).get('license')) or 'OFL/Apache'
        r['group'] = starter[fam.lower()]['group'] if fam.lower() in starter else auto_group(r)
        out.append(r)
        seen.add(fam.lower())
    fscat = {'sans-serif': 'Sans Serif', 'serif': 'Serif', 'display': 'Display', 'handwriting': 'Handwriting',
             'monospace': 'Monospace', 'other': 'Display'}
    for x in fsl:
        if x.get('type') == 'google' or x['family'].lower() in seen:
            continue
        r = {'family': x['family'], 'source': 'Fontsource', 'id': x['id'], 'category': fscat.get(x.get('category'), 'Display'),
             'scripts': name_scripts(x['family']), 'tags': {}, 'axes': [], 'license': norm_license(x.get('license')) or x.get('license'),
             'styles': [f'{w}{"i" if s == "italic" else ""}' for w in x.get('weights') or [] for s in x.get('styles') or []],
             'designers': [], 'color': False, 'pop': 5000}
        r['group'] = auto_group(r)
        out.append(r)
    return out


def norm_license(x):
    s = (x or '').strip().lower()
    if not s:
        return None
    if 'ofl' in s or 'open font' in s:
        return 'OFL-1.1'
    if 'apache' in s:
        return 'Apache-2.0'
    if 'ufl' in s or 'ubuntu' in s:
        return 'UFL-1.0'
    if s.startswith('cc0'):
        return 'CC0-1.0'
    if s == 'mit':
        return 'MIT'
    if 'unlicense' in s:
        return 'Unlicense'
    if s.startswith('ipa'):
        return 'IPA'
    return None


def styles_label(styles):
    ws = sorted({int(re.sub(r'\D', '', s) or 400) for s in styles})
    it = any(s.endswith('i') for s in styles)
    if not ws:
        return ''
    w = str(ws[0]) if len(ws) == 1 else (f'{ws[0]}–{ws[-1]}' if len(ws) > 3 else ','.join(map(str, ws)))
    return w + (' +斜' if it else '')


# -------------------------------------------------------------------------------------------------------------- search
def tag_test(want):
    """--tag → a test on one tag path ('/Theme/Techno'). English: any part of the path, as before (Techno, /Theme/);
    Chinese: the names in TAG_ZH, whole (科技 → Techno) or in part (衬线 → every tag whose Chinese name has it)."""
    w = want.strip()
    ens = {en.lower() for en, zh in TAG_ZH.items() if zh == w} or {en.lower() for en, zh in TAG_ZH.items() if w in zh}
    if ens:
        return lambda t: t.rsplit('/', 1)[-1].lower() in ens
    w = w.lower()
    return lambda t: w in t.lower()


def tags_zh(tags):
    """the Chinese names of tag paths, for keyword search (科技 finds /Theme/Techno)."""
    return ' '.join(TAG_ZH.get(t.rsplit('/', 1)[-1], '') for t in tags)


def tag_hint(want):
    """what to say when no tag at all matches --tag (a style group's name gets pointed to --group)."""
    w = want.strip()
    gs = [f'--group {g}（{z}）' for g, z, _ in GROUPS if w and (w in z or w.lower() == g)]
    return (f'没有「{want}」这个风格标签' + (f'；风格组里有：{"、".join(gs)}' if gs else '') +
            '。标签写英文或中文都行：' + '，'.join(f'{k} {v}' for k, v in TAG_ZH.items()))


def cmd_search(a):
    if a.local:
        return search_local(a)
    if not (a.words or a.group or a.cat or a.script or a.tag or a.var or a.color):
        raise SystemExit('给个关键词或筛选条件，例如：search --group blackletter / search --script zh --cat handwriting / search neon\n'
                         '风格组：' + '、'.join(f'{g}（{z}）' for g, z, _ in GROUPS))
    if a.group and a.group not in GROUP_RULE:
        raise SystemExit(f'没有风格组 {a.group}；可选：{", ".join(GROUP_ORDER)}')
    a.n = a.n or 30
    recs = online_records(a.refresh)
    have = {k.lower() for k in load_catalog()['families']}
    q = ' '.join(a.words).lower()
    tag_ok = tag_test(a.tag) if a.tag else None
    if tag_ok and not any(tag_ok(t) for r in recs for t, v in r.get('tags', {}).items() if v >= 50):
        raise SystemExit(tag_hint(a.tag))
    hits = []
    for r in recs:
        score = 50
        if a.group:
            score = 100 if r.get('group') == a.group else group_score(a.group, r)
            if not score:
                continue
        if a.cat and r.get('category') != CATS.get(a.cat.lower(), a.cat):
            continue
        if a.script and SCRIPTS.get(a.script.lower(), a.script.lower()) not in (r.get('scripts') or []):
            continue
        if tag_ok and not any(tag_ok(t) and v >= 50 for t, v in r.get('tags', {}).items()):
            continue
        if a.var and not r.get('axes'):
            continue
        if a.color and not r.get('color'):
            continue
        if q:
            ts = [t for t, v in r.get('tags', {}).items() if v >= 50]
            blob = ' '.join([r['family'], ' '.join(r.get('designers') or []), ' '.join(ts), tags_zh(ts)]).lower()
            if q not in blob:
                continue
            if q in r['family'].lower():
                score += 30
        hits.append((score, r))
    hits.sort(key=lambda h: (-h[0], h[1].get('pop', 9999)))
    say(f'{"":2}{"家族":32} {"风格组":14} {"分类":11} {"文字":12} {"字重/可变轴":22} {"授权":10} {"来源":10} 作者')
    for _, r in hits[:a.n]:
        axes = ' '.join(f"{x['tag']}{x['min']:g}-{x['max']:g}" for x in r.get('axes') or [])
        w = axes or styles_label(r.get('styles') or [])
        say(f"{'✓' if r['family'].lower() in have else ' ':2}{r['family'][:32]:32} {GROUP_ZH.get(r.get('group'), '')[:14]:14} "
            f"{r.get('category', '')[:11]:11} {','.join(r.get('scripts') or [])[:12]:12} {w[:22]:22} {str(r.get('license') or '')[:10]:10} "
            f"{r['source'].replace('Google Fonts', 'Google')[:10]:10} {', '.join(r.get('designers') or [])[:40]}")
    say(f'共 {len(hits)} 个（显示前 {min(a.n, len(hits))} 个；✓ = 已在库里）。下载：fonts.py get "家族名"，入库后 fonts.py specimen --family "家族名" 看样。')


_CMAPS = {}


def cmap_of(path):
    if path not in _CMAPS:
        from fontTools.ttLib import TTFont
        f = TTFont(path, lazy=True, fontNumber=0)
        _CMAPS[path] = set(f.getBestCmap() or {})
        f.close()
    return _CMAPS[path]


# Character index (<库>\_index\cmaps.json): every face's code points as runs [start, end, …] (uint32, base64), keyed by
# the face's path in the library and checked against its size + mtime. Written while scanning (get, catalog --rescan),
# filled in on first use for faces it lacks. search --local --text over two thousand families reads this one file
# instead of opening three thousand fonts.
_IDX, _IDX_DIRTY, _IDX_LOCK, _IDX_RANGES = None, False, threading.RLock(), {}
_NO_RANGES = (array.array('I'), array.array('I'))


def idx_faces():
    global _IDX
    with _IDX_LOCK:
        if _IDX is None:
            try:
                with open(CMAP_INDEX, encoding='utf-8') as f:
                    d = json.load(f)
                _IDX = d['faces'] if d.get('v') == 1 else {}
            except (OSError, ValueError, KeyError):
                _IDX = {}
        return _IDX


def face_sig(path):
    st = os.stat(path)
    return f'{st.st_size}:{int(st.st_mtime)}'


def pack_ranges(cps):
    a, run = array.array('I'), None
    for c in sorted(cps):
        if run and c == run[1] + 1:
            run[1] = c
        else:
            if run:
                a.extend(run)
            run = [c, c]
    if run:
        a.extend(run)
    if sys.byteorder != 'little':
        a.byteswap()
    return base64.b64encode(a.tobytes()).decode('ascii')


def unpack_ranges(s):
    a = array.array('I')
    a.frombytes(base64.b64decode(s))
    if sys.byteorder != 'little':
        a.byteswap()
    return a[0::2], a[1::2]


def idx_put(rel, path, cps):
    global _IDX_DIRTY
    rec = {'sig': face_sig(path), 'r': pack_ranges(cps)}
    faces = idx_faces()
    with _IDX_LOCK:
        faces[rel] = rec
        _IDX_RANGES.pop(rel, None)
        _IDX_DIRTY = True


def face_ranges(rel):
    """(starts, ends) of a library face's character set — from the index, else read from the font (and indexed)."""
    r = _IDX_RANGES.get(rel)
    if r is not None:
        return r
    path = os.path.join(LIB, rel)
    try:
        rec = idx_faces().get(rel)
        if not rec or rec.get('sig') != face_sig(path):
            idx_put(rel, path, cmap_of(path))
            rec = idx_faces()[rel]
        r = unpack_ranges(rec['r'])
    except Exception:  # noqa: BLE001 — a missing or unreadable file: every character counts as missing
        r = _NO_RANGES
    _IDX_RANGES[rel] = r
    return r


def has_cp(r, c):
    i = bisect.bisect_right(r[0], c) - 1
    return i >= 0 and c <= r[1][i]


def idx_save(keep=None):
    """write the index if it changed; keep = the face paths still in the catalog (others are dropped)."""
    global _IDX_DIRTY
    if _IDX is None:
        return
    with _IDX_LOCK:
        if keep is not None:
            for k in [k for k in _IDX if k not in keep]:
                del _IDX[k]
                _IDX_DIRTY = True
        if not _IDX_DIRTY:
            return
        data = json.dumps({'v': 1, 'faces': _IDX}, separators=(',', ':'))
        _IDX_DIRTY = False
    write_atomic(CMAP_INDEX, data)


def family_missing(e, text):
    """characters of `text` that no face of the family has (spaces ignored)."""
    rs = [face_ranges(f['file']) for f in e['faces']]
    return ''.join(dict.fromkeys(ch for ch in text if not ch.isspace() and not any(has_cp(r, ord(ch)) for r in rs)))


def has_script(e, sc):
    c = e['faces'][0]['cov']
    return {'zh': c['gb1'] >= 2500, 'tc': c['big5'] >= 2500, 'jp': c['kana'] >= 150, 'ko': c['hangul'] >= 2000,
            'latin': c['latin'] >= 60}.get(sc, False)


def local_script_ok(e, want):
    """--script for library entries: zh / tc / jp / ko / latin from the font's own characters; any other value is a Google
    Fonts subset (cyrillic, greek, vietnamese, arabic, devanagari, thai…) or its Chinese name (西里尔、阿拉伯…)."""
    sc = SCRIPTS.get(want.lower())
    if sc:
        return has_script(e, sc)
    w = want.lower()
    subs = gf_info(e)[1]
    return any(s == w or s.startswith(w) or SUBSET_ZH.get(s) == want for s in subs)


def search_local(a):
    t0 = time.time()
    cat = load_catalog()
    if not cat['families']:
        raise SystemExit(f'库是空的：先 fonts.py get starter（库在 {LIB}）')
    if a.group and a.group not in GROUP_RULE:
        raise SystemExit(f'没有风格组 {a.group}；可选：{", ".join(GROUP_ORDER)}')
    q = ' '.join(a.words).lower()
    tag_ok = tag_test(a.tag) if a.tag else None
    if tag_ok and not any(tag_ok(t) for e in cat['families'].values() for t in e.get('tags') or []):
        raise SystemExit(tag_hint(a.tag))
    rows = []
    for fam, e in cat['families'].items():
        if a.group and e['group'] != a.group:
            continue
        if a.cat and e.get('category') != CATS.get(a.cat.lower(), a.cat):
            continue
        if tag_ok and not any(tag_ok(t) for t in e.get('tags') or []):
            continue
        if a.var and not any(' ' in f['weight'] or f['axes'] for f in e['faces']):
            continue
        if a.color and not e.get('color'):
            continue
        if a.script and not local_script_ok(e, a.script):
            continue
        gz = GROUP_ZH.get(e['group'], '')
        if '无' not in q:            # '衬线' must not find the sans group by its name '无衬线 / 其他'
            gz = gz.replace('无衬线', '')
        if q and q not in ' '.join([fam, e.get('fits', ''), ' '.join(e.get('designers', [])), e['group'], gz,
                                    e.get('category') or '', ' '.join(e.get('tags') or []), tags_zh(e.get('tags') or [])]).lower():
            continue
        miss = family_missing(e, a.text) if a.text else None
        rows.append((e, miss))
    # --script zh / tc / jp / ko: the fullest coverage first (a Japanese font has 2500+ of the common hanzi too)
    cov = {'zh': lambda c: -(c['gb1'] + c['gb2']), 'tc': lambda c: -c['big5'], 'jp': lambda c: -(c['jis1'] + c['kana']),
           'ko': lambda c: -c['hangul']}.get(SCRIPTS.get((a.script or '').lower()), lambda c: 0)
    rank = {e['family']: (cov(e['faces'][0]['cov']), not is_curated(e), gf_info(e)[0], e['family'].lower()) for e, _ in rows}
    rows.sort(key=lambda r: ((len(r[1]),) if a.text else ()) + rank[r[0]['family']])
    idx_save()                      # faces indexed on the way (first --text after an old get): next time it is instant
    n = len(rows) if a.n == 0 else (a.n or 50)
    say(f'{"":2}{"家族":32} {"风格组":14} {"字重 / 可变":18} {"文字集":28} ' + ('缺字' if a.text else '用法（★ 精选架）/ 官方分类和风格标签'))
    for e, miss in rows[:n]:
        if a.text:
            tail = '全有' if not miss else f'缺 {len(miss)}：{miss[:30]}'
        else:
            tail = e['fits'][:60] if is_curated(e) else ' · '.join(filter(None, [e.get('category'), '、'.join(tags_short(e, 4))]))
        ws = e['weights']
        if len(ws) > 18 and '可变' not in ws:      # "100, 200, 300, …, 900 · 带斜体" → "100–900（9 个）+斜"
            nums = re.findall(r'\d+', ws.split('·')[0])
            ws = f'{nums[0]}–{nums[-1]}（{len(nums)} 个）' + ('+斜' if '斜' in ws else '')
        say(f"{'★' if is_curated(e) else ' ':2}{e['family'][:32]:32} {GROUP_ZH.get(e['group'], e['group'])[:14]:14} "
            f"{ws[:18]:18} {scripts_short(e)[:28]:28} {tail}")
    say(f'共 {len(rows)} 个' + (f'（显示前 {n} 个，-n 0 = 全部）' if n < len(rows) else '') + f'，{time.time() - t0:.1f}s。' +
        ('看效果：fonts.py specimen --text "…" --family "A,B"（缺的字标红）' if a.text else
         '看样：fonts.py specimen --family "家族名"；全量分页样张在 specimen\\all\\（页码见 catalog_all.md）'))


# --------------------------------------------------------------------------------------------------------- face scanning
_COV = None


def cov_sets():
    """GB2312 一级/二级、Big5 常用字、JIS X 0208 第一水准：判断一个字体是不是真能排简中/繁中/日文。"""
    global _COV
    if _COV is None:
        gb1, gb2, big5, jis1 = [], [], [], []
        for hi in range(0xB0, 0xF8):
            for lo in range(0xA1, 0xFF):
                try:
                    (gb1 if hi < 0xD8 else gb2).append(ord(bytes((hi, lo)).decode('gb2312')))
                except UnicodeDecodeError:
                    pass
        for hi in range(0xA4, 0xC7):
            for lo in list(range(0x40, 0x7F)) + list(range(0xA1, 0xFF)):
                if (hi, lo) > (0xC6, 0x7E):
                    break
                try:
                    big5.append(ord(bytes((hi, lo)).decode('big5')))
                except UnicodeDecodeError:
                    pass
        for hi in range(0xB0, 0xD0):
            for lo in range(0xA1, 0xFF):
                try:
                    jis1.append(ord(bytes((hi, lo)).decode('euc_jp')))
                except UnicodeDecodeError:
                    pass
        _COV = {'gb1': gb1, 'gb2': gb2, 'big5': big5, 'jis1': jis1,
                'latin': [ord(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789']}
    return _COV


def weight_from_name(fname):
    tail = re.split(r'[-_]', os.path.splitext(os.path.basename(fname).lower())[0])[-1]
    return next((v for k, v in WEIGHT_WORDS if k in tail), None)


def scan_face(path, rel):
    from fontTools.ttLib import TTFont
    f = TTFont(path, lazy=True, fontNumber=0)
    names = f['name']

    def nm(i):
        r = names.getName(i, 3, 1, 0x409) or names.getName(i, 1, 0, 0) or next((x for x in names.names if x.nameID == i), None)
        try:
            return r.toUnicode().strip() if r else ''
        except Exception:  # noqa: BLE001
            return ''
    cps = set(f.getBestCmap() or {})
    idx_put(rel, path, cps)
    axes = [{'tag': x.axisTag, 'min': x.minValue, 'def': x.defaultValue, 'max': x.maxValue} for x in f['fvar'].axes] if 'fvar' in f else []
    w = next((x for x in axes if x['tag'] == 'wght'), None)
    os2 = f['OS/2'] if 'OS/2' in f else None
    weight = f"{w['min']:g} {w['max']:g}" if w else str(max(1, min(1000, os2.usWeightClass if os2 else 400)))
    if weight in ('250', '275') and weight_from_name(path) in (100, 200):   # the old Windows GDI trick: Thin = 250, ExtraLight = 275
        weight = str(weight_from_name(path))                                # (Fira Sans, Lato, Barlow…): CSS and "Lato:100" mean 100
    wd = next((x for x in axes if x['tag'] == 'wdth'), None)
    color = (f"COLRv{f['COLR'].version}" if 'COLR' in f else 'SVG' if 'SVG ' in f else 'CBDT' if 'CBDT' in f else
             'sbix' if 'sbix' in f else None)
    C = cov_sets()
    cov = {k: sum(1 for c in C[k] if c in cps) for k in ('latin', 'gb1', 'gb2', 'big5', 'jis1')}
    cov['digits'] = sum(1 for c in range(0x30, 0x3A) if c in cps)
    cov['kana'] = sum(1 for c in cps if 0x3041 <= c <= 0x30FA)
    cov['hangul'] = sum(1 for c in cps if 0xAC00 <= c <= 0xD7A3)
    out = {'file': rel, 'bytes': os.path.getsize(path), 'name': nm(16) or nm(1), 'weight': weight,
           'style': 'italic' if 'italic' in os.path.basename(path).lower() else 'normal',
           'stretch': f"{wd['min']:g}% {wd['max']:g}%" if wd else None, 'axes': axes, 'glyphs': f['maxp'].numGlyphs,
           'color': color, 'hanzi': sum(1 for c in cps if 0x4E00 <= c <= 0x9FFF or 0x3400 <= c <= 0x4DBF), 'cov': cov,
           'copyright': nm(0), 'designer': nm(9), 'version': nm(5), 'license_desc': nm(13)[:160], 'license_url': nm(14)}
    f.close()
    return out


def scan_faces(d, names, sl):
    faces = [scan_face(os.path.join(d, n), f'{sl}/{n}') for n in names]
    seen = {}
    for fc in faces:                       # two statics with the same CSS weight+style would shadow each other
        if ' ' in fc['weight']:
            continue
        k = (fc['weight'], fc['style'])
        if k in seen:
            for x in (seen[k], fc):
                w = weight_from_name(x['file'])
                if w:
                    x['weight'] = str(w)
        seen[k] = fc
    faces.sort(key=lambda x: (x['style'] != 'normal', wrange(x['weight'])[0]))
    return faces


def script_labels(c, hanzi):
    L = []
    if c['latin'] >= 60:
        L.append('拉丁')
    elif c['digits'] == 10:
        L.append('数字和少量字母')
    if c['gb1'] >= 3740:
        L.append('简中（GB2312 全）' if c['gb1'] + c['gb2'] >= 6740 else '简中（常用一级字全）')
    elif c['gb1'] >= 800:
        L.append(f'简中缺字（一级字 {c["gb1"]}/3755）')
    if c['big5'] >= 5380:
        L.append('繁中')
    elif c['big5'] >= 2000:
        L.append(f'繁中缺字（{c["big5"]}/5401）')
    if c['kana'] >= 150:
        L.append('日文' if c['jis1'] >= 2950 else f'日文（第一水准汉字 {c["jis1"]}/2965）')
    if c['hangul'] >= 2000:
        L.append('韩文')
    return L or ['（极少字符）']


def weights_label(faces):
    var = [f for f in faces if ' ' in f['weight']]
    if var:
        lo = min(wrange(f['weight'])[0] for f in var)
        hi = max(wrange(f['weight'])[1] for f in var)
        s = f'{lo:g}–{hi:g} 可变'
    else:
        s = ', '.join(dict.fromkeys(f['weight'] for f in faces if f['style'] == 'normal')) or ', '.join(dict.fromkeys(f['weight'] for f in faces))
    if any(f['style'] == 'italic' for f in faces) and any(f['style'] == 'normal' for f in faces):
        s += ' · 带斜体'
    return s


def axes_of(faces):
    ax = {}
    for f in faces:
        for x in f['axes']:
            lo, de, hi = ax.get(x['tag'], (x['min'], x['def'], x['max']))
            ax[x['tag']] = (min(lo, x['min']), de, max(hi, x['max']))
    return ax


RFN_KEY = re.compile(r'Reserved\s+Font\s+Names?\s*[:：]?\s*', re.I)
RFN_QUOTED = re.compile(r'\s*(?:,|，|、|;|\band\b|&)?\s*(?:"([^"\n]{1,40})"|“([^”\n]{1,40})”|\'([^\'\n]{1,40})\'|‘([^’\n]{1,40})’|'
                        r'<([^<>\n]{1,40})>|《([^》\n]{1,40})》)')
RFN_BARE = re.compile(r'[^\s"“\'‘<《(.,;:][^\n.,;"“”\'‘’<>()]{0,39}')


def rfn_ok(n, bare):
    if not 0 < len(n) <= 40 or re.search(r'reserved\s+font|copyright\s+holder', n, re.I):    # the OFL template's <…>
        return False
    return not bare or (len(n) > 1 and len(n.split()) <= 5 and (n[0].isupper() or n[0].isdigit() or not n[0].isascii())
                        and not re.search(r'\b(?:refers?|unless|may|shall|is|are)\b', n, re.I))


def rfn_of(*texts):
    """OFL reserved font names from licence headers and name-table copyright strings. Three spellings:
    quoted ("Abril" and "Abril Fatface" / 'Pirata' / “…”), bare up to . , ; or line end (… Name UnifrakturCook.),
    angle brackets (<Smiley> and <得意黑>). Only the part before the licence body is read (it quotes its own terms)."""
    out = []
    for text in texts:
        head = re.split(r'This Font Software is licen[cs]ed|SIL OPEN FONT LICENSE|PREAMBLE', text or '', maxsplit=1)[0]
        for m in RFN_KEY.finditer(head):
            pos, names = m.end(), []
            while (q := RFN_QUOTED.match(head, pos)):
                names.append(next(g for g in q.groups() if g is not None).strip())
                pos = q.end()
            if names:
                out += [n for n in names if rfn_ok(n, False)]
            elif (b := RFN_BARE.match(head, pos)):
                out += [n.strip() for n in re.split(r'\s+and\s+|\s*&\s*', b.group(0)) if rfn_ok(n.strip(), True)]
    return sorted(set(out))


def name_strings(src, ids=(0, 13, 14)):
    """{nameID: [distinct strings, every platform and language]} — src is a path or a file object."""
    from fontTools.ttLib import TTFont
    f = TTFont(src, lazy=True, fontNumber=0)
    out = {}
    try:
        for r in f['name'].names if 'name' in f else []:
            if r.nameID in ids:
                try:
                    s = r.toUnicode().strip()
                except Exception:  # noqa: BLE001
                    continue
                if s and s not in out.setdefault(r.nameID, []):
                    out[r.nameID].append(s)
    finally:
        f.close()
    return out


def lic_flat(text):
    """licence text → one lower-case line for LICENSE_PROOF: HTML entities decoded, Markdown markup (# * _ ` ~ > | = \\
    and --- rules) dropped, whitespace collapsed. "## SIL Open Font License v1.1" reads like "SIL OPEN FONT LICENSE Version 1.1"."""
    s = re.sub(r'[#*_`~>|=\\]+|-{2,}', ' ', html.unescape(text or ''))
    return re.sub(r'\s+', ' ', s).strip().lower()


def name_restriction(s):
    """the first personal-use / non-commercial / freeware / EULA kind of phrase in a name-table string, with the rest of
    its clause (≤ 60 characters), or None. NAME_BENIGN pairs are blanked first (same length, so positions still match)."""
    s = re.sub(r'\s+', ' ', s or '')
    m = re.search(NAME_RESTRICT, re.sub(NAME_BENIGN, lambda b: ' ' * len(b.group(0)), s, flags=re.I), re.I)
    if not m:
        return None
    end = m.end() + re.search(r'[.;!?。；]|$', s[m.end():]).start()
    return s[m.start():min(end, m.start() + 60)].strip()


def license_check(lic, text, names):
    """(problems, notes); no problems = OK. text: the licence file; names: name_strings() of each font file.
    Problems (refused): the text doesn't prove the declared licence (or, for MIT / Unlicense / CC0 / IPA, also carries
    another one); name IDs 13/14 name a licence outside the allowed list and not the declared one, or — declared MIT /
    Unlicense / CC0 / IPA — any other licence; 0/13/14 carry a personal-use / non-commercial / freeware / EULA restriction.
    Notes (kept): 13/14 name another licence that is also on the allowed list (OFL.txt, name table Apache)."""
    if lic not in LICENSE_PROOF:
        return [f'授权「{lic}」不在允许列表（{", ".join(LICENSES)}）'], []
    flat = lic_flat(text)
    bad = [f'授权原文里没有「{label}」' for label, rx in LICENSE_PROOF[lic] if not re.search(rx, flat)]
    if lic in STRICT_LICENSES:
        bad += [f'授权原文里还有「{label}」，像是别的授权的原文，和声明的 {lic} 对不上' for label, rx in LICENSE_FOREIGN
                if re.search(rx, flat)]
    notes = []
    for ns in names:
        said = re.sub(r'\s+', ' ', ' '.join(ns.get(13, []) + ns.get(14, [])))
        r = next(filter(None, map(name_restriction, ns.get(13, []) + ns.get(14, []) + ns.get(0, []))), None)
        hit = [k for k, rx in NAME_LICENSE if re.search(rx, said, re.I)]
        if r:
            bad.append(f'字体文件 name 表写着「{r}」')
        if not hit or lic in hit:
            continue
        if lic in STRICT_LICENSES or any(k not in LICENSES for k in hit):
            bad.append(f'字体文件 name 表 13/14 说是 {"/".join(hit)}，和声明的 {lic} 对不上：{said[:120]}' +
                       (f'（声明 {lic} 时字体文件得写同一种或不写：按字体文件写的授权申报，附它的原文）' if lic in STRICT_LICENSES and
                        all(k in LICENSES for k in hit) else ''))
        else:
            notes.append(f'name 表写 {"/".join(hit)}，授权文件是 {lic}，{"两" if len(hit) == 1 else "几"}种都能商用，鸣谢按授权文件')
    return list(dict.fromkeys(bad)), list(dict.fromkeys(notes))


def license_problems(lic, text, names):
    """[] = OK (license_check without the notes)."""
    return license_check(lic, text, names)[0]


LOSSY_NOTE = '英文鸣谢略去了中文名：补 designers_en'


def set_note(e, lic_notes=None):
    """e['note'] = the licence notes + the lossy-English-credit reminder, '；'-joined. lic_notes None = keep the licence
    notes already in e['note'] (metadata-only update)."""
    if lic_notes is None:
        lic_notes = license_notes(e)
    e['note'] = '；'.join(list(lic_notes) + ([LOSSY_NOTE] if en_lossy(e) else []))
    return e


def license_notes(e):
    return [p for p in (e.get('note') or '').split('；') if p.strip() and 'designers_en' not in p]


def family_rfn(lic_text, names):
    return rfn_of(lic_text, *[s for ns in names for s in ns.get(0, []) + ns.get(13, [])])


def summarize(e):
    """recompute the family-level fields from e['faces'] (after get or catalog --rescan)."""
    faces = e['faces']
    e['weights'] = weights_label(faces)
    e['styles'] = sorted({f['style'] for f in faces})
    e['axes'] = {k: list(v) for k, v in axes_of(faces).items()}
    e['color'] = next((f['color'] for f in faces if f['color']), None)
    e['hanzi'] = max(f['hanzi'] for f in faces)
    e['scripts'] = script_labels(faces[0]['cov'], e['hanzi'])
    e['bytes'] = sum(f['bytes'] for f in faces)
    lic = LICENSES.get(e['license'], e['license'])
    e['credit_zh'] = f"字体 {e['family']}：{'、'.join(e['designers'])}（{lic}）"
    e['credit_en'] = credit_en(e, lic)
    return e


# not allowed in the English credit line: CJK punctuation / kana / ideographs, Hangul, compatibility and vertical forms,
# full-width forms, ideograph extensions B+
CJK_FW = re.compile('[' + ''.join(f'{chr(a)}-{chr(b)}' for a, b in ((0x2E80, 0x9FFF), (0xAC00, 0xD7AF), (0xF900, 0xFAFF),
                    (0xFE10, 0xFE1F), (0xFE30, 0xFE4F), (0xFF00, 0xFFEF), (0x20000, 0x3FFFF))) + ']')
FW_ASCII = str.maketrans({'（': ' (', '）': ') ', '，': ', ', '、': ', ', '：': ': ', '；': '; ', '！': '! ', '？': '? ', '　': ' ',
                          '「': '"', '」': '"', '『': '"', '』': '"', '《': '"', '》': '"', '【': '[', '】': ']'})


def credit_en(e, lic):
    """English credit: designers_en when given. Otherwise designers with full-width punctuation made ASCII and CJK
    characters left out (en_lossy() says so — add designers_en to fonts_starter.json or get --designers-en)."""
    names = []
    for d in e.get('designers_en') or e['designers']:
        s = re.sub(r'\s+', ' ', CJK_FW.sub(' ', d.translate(FW_ASCII)))
        s = re.sub(r'\s+([),.;:!?\]])', r'\1', re.sub(r'([(\[])\s+', r'\1', s))
        s = re.sub(r'\(\)|\[\]', '', s).strip(' ,;:-')
        if s:
            names.append(s)
    return f"Font: {e['family']}" + (f" by {', '.join(names)}" if names else '') + f" — {lic}"


def en_lossy(e):
    return bool(CJK_FW.search(' '.join(e.get('designers_en') or e['designers']).translate(FW_ASCII)))


# ------------------------------------------------------------------------------------------------------------- get
def resolve_target(name, starter):
    k = name.strip().lower()
    if k in starter:
        return dict(starter[k])
    meta = gf_meta()
    for fam in meta:
        if fam.lower() == k:
            return {'family': fam, 'src': 'gf'}
    for x in fs_list():
        if x.get('type') != 'google' and (x['family'].lower() == k or x['id'] == k):
            return {'family': x['family'], 'src': 'fs', 'id': x['id']}
    sugg = [f for f in meta if k in f.lower()][:8]
    raise LookupError(f'找不到「{name}」' + (f'，是不是：{"、".join(sugg)}' if sugg else '，先用 fonts.py search 找'))


def plan_for(e):
    src = e.get('src') or 'gf'
    if src == 'gf':
        x = gf_meta().get(e['family'])
        if not x:
            raise LookupError(f'Google Fonts 上没有 {e["family"]}')
        t = http(GF_LIST + urllib.parse.quote(e['family'])).decode('utf-8')
        man = json.loads(t[t.index('{'):])['manifest']
        refs = [r for r in man['fileRefs'] if r['filename'].lower().endswith(('.ttf', '.otf'))]
        if e.get('pick'):
            refs = [r for r in refs if os.path.basename(r['filename']) in e['pick'] or clean_name(r['filename']) in e['pick']]
        else:   # the variable file(s) hold every weight; statics only for families without one
            refs = [r for r in refs if 'variablefont' in r['filename'].lower() or '[' in r['filename']] or \
                   [r for r in refs if '/' not in r['filename'].strip('/')] or refs
        lic = next((f for f in man['files'] if f['filename'] in ('OFL.txt', 'LICENSE.txt', 'UFL.txt')), None)
        if not lic:
            raise ValueError('下载清单里没有授权文件')
        rec = gf_record(e['family'], x)
        return {'files': [(r['url'], r['filename']) for r in refs], 'license': {'OFL.txt': 'OFL-1.1', 'LICENSE.txt': 'Apache-2.0',
                'UFL.txt': 'UFL-1.0'}[lic['filename']], 'license_text': lic['contents'], 'designers': e.get('designers') or x.get('designers') or [],
                'home': 'https://fonts.google.com/specimen/' + e['family'].replace(' ', '+'), 'source': 'Google Fonts',
                'category': x.get('category') or '', 'record': rec}
    if src == 'fs':
        d = json.loads(http(FS_API + '/' + e['id']).decode('utf-8'))
        files = []
        for w, styles in d['variants'].items():
            for st, subs in styles.items():
                sub = subs.get(d.get('defSubset')) or next(iter(subs.values()))
                files.append((sub['url']['ttf'], f"{e['id']}-{w}-{st}.ttf"))
        return {'files': files, 'license': norm_license(d.get('license') or e.get('license')),
                'license_url': e.get('license_url') or f'https://cdn.jsdelivr.net/npm/@fontsource/{e["id"]}/LICENSE',
                'designers': e.get('designers') or [], 'home': e.get('home') or f'https://fontsource.org/fonts/{e["id"]}',
                'source': 'Fontsource（jsDelivr）', 'category': d.get('category', '')}
    if src in ('url', 'zip'):
        first = e['files'][0] if src == 'url' else e['url']
        m = re.match(r'https://github\.com/([^/]+/[^/]+)/', first)
        p = {'license': norm_license(e.get('license')), 'license_url': e.get('license_url'), 'designers': e.get('designers') or [],
             'home': e.get('home') or (f'https://github.com/{m.group(1)}' if m else first),
             'source': f'GitHub Releases：{m.group(1)}' if m else '直链', 'category': ''}
        if src == 'url':
            p['files'] = [(u, urllib.parse.unquote(u.rsplit('/', 1)[-1])) for u in e['files']]
        else:
            p['files'], p['zip'], p['pick'] = [], e['url'], e.get('pick') or []
        return p
    raise ValueError('未知来源 ' + src)


def fetch_family(e):
    plan = plan_for(e)
    lic = plan.get('license')
    if lic not in LICENSES:
        raise ValueError(f'授权「{e.get("license") or lic}」不在允许列表（{", ".join(LICENSES)}），不收')
    sl = slug(e['family'])
    d = os.path.join(LIB, sl)
    blobs = [(clean_name(name), http(url)) for url, name in plan['files']]   # kept in memory until the licence checks pass
    zip_lics = []
    if plan.get('zip'):
        z = zipfile.ZipFile(io.BytesIO(http(plan['zip'])))
        infos = [i for i in z.infolist() if not i.is_dir() and '__MACOSX' not in i.filename]
        pick = set(plan['pick']) or {os.path.basename(i.filename) for i in infos if i.filename.lower().endswith('.ttf')} or \
            {os.path.basename(i.filename) for i in infos if i.filename.lower().endswith('.otf')}
        got = set()
        for i in infos:
            base = os.path.basename(i.filename)
            if base in pick and base not in got:
                blobs.append((clean_name(base), z.read(i)))
                got.add(base)
            elif re.match(r'(ofl|licen[cs]e)', base, re.I) and base.lower().endswith(('.txt', '.md', 'ofl', 'license', 'licence')):
                zip_lics.append(z.read(i).decode('utf-8', 'replace'))
        if pick - got:
            raise ValueError('压缩包里没有：' + ', '.join(sorted(pick - got)))
    lic_text = plan.get('license_text')
    if not lic_text and plan.get('license_url'):
        try:
            lic_text = http(plan['license_url']).decode('utf-8', 'replace')
        except Exception:  # noqa: BLE001
            lic_text = None
    if not lic_text:        # declared source unreachable → the zip's own licence file that proves the declared licence
        lic_text = next((t for t in zip_lics if not license_problems(lic, t, [])), zip_lics[0] if zip_lics else None)
    if not lic_text:
        raise ValueError('拿不到授权原文，不收')
    names = [name_strings(io.BytesIO(data)) for _, data in blobs]
    bad, lic_notes = license_check(lic, lic_text, names)
    if bad:                 # nothing has been written to the library yet
        raise ValueError('授权核对不过，不收：' + '；'.join(bad))
    for n, data in blobs:
        write_atomic(os.path.join(d, n), data)
    lic_file = LICENSE_FILE.get(lic, 'LICENSE.txt')
    write_atomic(os.path.join(d, lic_file), lic_text)
    faces = scan_faces(d, [n for n, _ in blobs], sl)
    rec = plan.get('record')
    designers = plan['designers'] or [faces[0]['designer'] or faces[0]['copyright'][:80] or '?']
    if not e.get('group'):
        e['group'] = auto_group(rec) if rec else ('cjk-display' if faces[0]['cov']['gb1'] >= 2500 else
                                                   'jp-display' if faces[0]['cov']['kana'] >= 150 else 'other')
    entry = {'family': e['family'], 'slug': sl, 'group': e['group'], 'fits': e.get('fits') or '',
             'category': plan.get('category') or '', 'tags': sorted(t for t, v in (rec or {}).get('tags', {}).items()
                                                                    if v >= 60 and not t.startswith('/Quality')),
             'source': plan['source'], 'source_url': plan['home'], 'designers': designers, 'license': lic,
             'license_file': f'{sl}/{lic_file}', 'rfn': family_rfn(lic_text, names), 'copyright': faces[0]['copyright'],
             'faces': faces, 'added': today(), 'note': ''}
    if e.get('designers_en'):
        entry['designers_en'] = e['designers_en']
    if rec:     # for the full index: Google's popularity rank (sort order), subsets and main script (文字集)
        entry.update(pop=rec['pop'], subsets=rec['subsets'], primary_script=rec['primary_script'])
    summarize(entry)
    return set_note(entry, lic_notes)


def fetch_many(entries):
    if any((e.get('src') or 'gf') == 'gf' for e in entries):
        gf_meta(), gf_tags()
    cov_sets()

    def job(e):
        t0 = time.time()
        try:
            return e, fetch_family(e), None, time.time() - t0
        except Exception as ex:  # noqa: BLE001
            return e, None, ex, time.time() - t0
    done, failed = [], []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for e, entry, err, dt in ex.map(job, entries):
            if err:
                failed.append((e['family'], err))
                say(f'  失败 {e["family"]}：{err}')
            else:
                done.append(entry)
                say(f'  入库 {e["family"][:34]:34} {len(entry["faces"]):2} 个文件 {fmt_mb(entry["bytes"]):>8}  {entry["license"]:10} '
                    f'{GROUP_ZH[entry["group"]]}  {dt:4.1f}s')
                for nt in filter(None, entry['note'].split('；')):
                    say(f'       提示：{nt}')
    return done, failed


def cmd_get(a):
    if a.all_google:
        if a.targets or a.url:
            raise SystemExit('get --all-google 不和家族名、--url 一起用')
        return get_all_google(a)
    starter = {e['family'].lower(): e for e in load_starter()}
    unknown = []
    if a.url:
        if not (a.family and a.license and a.license_url):
            raise SystemExit('get --url 还要 --family、--license（如 OFL-1.1）、--license-url（授权原文直链）')
        e = {'family': a.family, 'license': a.license, 'license_url': a.license_url, 'home': a.home,
             'designers': [x.strip() for x in (a.designers or '').split(',') if x.strip()]}
        if not e['designers'] and a.designers_en:
            e['designers'] = [x.strip() for x in a.designers_en.split(',') if x.strip()]
        if a.url.lower().split('?')[0].endswith('.zip'):
            e.update(src='zip', url=a.url, pick=[x.strip() for x in (a.pick or '').split(',') if x.strip()])
        else:
            e.update(src='url', files=[a.url])
        entries = [e]
    else:
        if not a.targets:
            raise SystemExit('要下载什么？fonts.py get "Pirata One" 或 fonts.py get starter（首批清单）')
        entries = []
        for t in a.targets:
            if t.lower() == 'starter':
                entries += [dict(x) for x in load_starter()]
            else:
                try:
                    entries.append(resolve_target(t, starter))
                except LookupError as ex:
                    unknown.append(t)
                    say(f'  {ex}')
        if not entries:
            return 1
    if a.designers_en and len(entries) != 1:
        raise SystemExit('--designers-en 是某一个家族的作者英文名，只能配一个家族')
    for e in entries:
        if a.group:
            e['group'] = a.group
        if a.fits:
            e['fits'] = a.fits
        if a.pick and not a.url:
            e['pick'] = [x.strip() for x in a.pick.split(',') if x.strip()]
        if a.designers_en:
            e['designers_en'] = [x.strip() for x in a.designers_en.split(',') if x.strip()]
    if a.group and a.group not in GROUP_RULE:
        raise SystemExit(f'没有风格组 {a.group}；可选：{", ".join(GROUP_ORDER)}')
    cat = load_catalog()
    todo = []
    for e in entries:
        old = cat['families'].get(e['family'])
        if old and not a.force and all(os.path.exists(os.path.join(LIB, f['file'])) for f in old['faces']):
            # metadata only (group, usage notes, designers → credit lines); files stay as they are
            old['group'], old['fits'] = e.get('group') or old['group'], e.get('fits') or old.get('fits', '')
            for k in ('designers', 'designers_en'):
                if e.get(k) and e[k] != old.get(k):
                    old[k] = e[k]
            set_note(summarize(old))
            say(f'  已在库里 {e["family"]}（只更新了说明；重下加 --force）' + (f'（{LOSSY_NOTE}）' if en_lossy(old) else ''))
        else:
            todo.append(e)
    t0 = time.time()
    done, failed = fetch_many(todo) if todo else ([], [])
    for entry in done:
        cat['families'][entry['family']] = entry
    save_catalog(cat)
    write_md(cat)
    n = len(cat['families'])
    say(f'完成：新入库 {len(done)} 个，失败 {len(failed)} 个，用时 {time.time() - t0:.0f}s。库里共 {n} 个家族 → {CATALOG_MD}')
    if done:
        say('看样：fonts.py specimen --family "' + ','.join(x['family'] for x in done[:3]) + '"')
    return 1 if failed or unknown else 0


# -------------------------------------------------------------------------------------------- get --all-google (batch)
FAIL_KIND = {'licence': '授权核对不过（现有检查不收，跳过）', 'missing': 'Google Fonts 上找不到',
             'net': '网络（重试后仍失败，再跑一次会重试）', 'other': '其他（字体文件读不了等）'}


def fail_kind(ex):
    """licence / missing are final; net (timeouts, resets, 5xx, 429, a garbled manifest, a locked file) is worth retrying."""
    if isinstance(ex, urllib.error.HTTPError):
        return 'missing' if ex.code in (404, 410) else 'net'
    if type(ex) is LookupError:            # plan_for's own "Google Fonts 上没有 …" — not its subclasses
        return 'missing'
    if isinstance(ex, KeyError):           # a manifest without its usual fields: an error page, worth another try
        return 'net'
    if isinstance(ex, LookupError):        # IndexError and the like: a broken file or a bug, not the network
        return 'other'
    if isinstance(ex, json.JSONDecodeError) or 'substring not found' in str(ex):    # an error page instead of the manifest
        return 'net'
    if isinstance(ex, ValueError):
        return 'licence' if '授权' in str(ex) else 'other'
    if isinstance(ex, (urllib.error.URLError, HTTPException, OSError)):    # OSError: ConnectionError, TimeoutError, ssl
        return 'net'
    return 'other'


def gf_todo(cat, starter):
    """(every Google Fonts family, most popular first; entries still to fetch; families already in the library)."""
    meta = gf_meta()
    have = {}
    for f, e in cat['families'].items():
        have.setdefault(f.lower(), e)
        have.setdefault(e['slug'], e)
    fams = sorted(meta, key=lambda f: (meta[f].get('popularity') or 9999, f.lower()))
    todo, skip = [], []
    for f in fams:
        old = have.get(f.lower()) or have.get(slug(f))
        if old and all(os.path.exists(os.path.join(LIB, x['file'])) for x in old['faces']):
            skip.append(f)
            continue
        e = dict(starter.get(f.lower()) or {'family': f, 'src': 'gf'})
        e['family'], e['src'] = f, 'gf'
        for k in ('group', 'fits', 'designers', 'designers_en'):     # files gone, entry still there: keep its curation
            if old and old.get(k) and not e.get(k):
                e[k] = old[k]
        todo.append(e)
    return fams, todo, skip


def get_all_google(a):
    jobs, tries = max(1, min(a.jobs or 4, 16)), max(1, a.retries or 3)
    starter = {e['family'].lower(): e for e in load_starter()}
    cat = load_catalog()
    fams, todo, skip = gf_todo(cat, starter)
    gf_tags()
    if a.limit:
        todo = todo[:a.limit]
    if a.estimate:
        return estimate_google(fams, todo, skip, jobs)
    cov_sets()
    os.makedirs(LOGS, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    logp = os.path.join(LOGS, f'get-all-google-{stamp}.log')
    lock = threading.Lock()
    logf = open(logp, 'a', encoding='utf-8')

    def out(s):
        with lock:
            say(s)
            logf.write(s + '\n')
            logf.flush()
    N, t0 = len(fams), time.time()
    out(f'Google Fonts 目录 {N} 个家族：已在库里 {len(skip)} 个（跳过），这次要下 {len(todo)} 个，{jobs} 路并行，'
        f'每个家族最多试 {tries} 次。库 {LIB}，日志 {logp}')
    k = 0
    for f in skip:
        k += 1
        out(f'[{k:>4}/{N}] 跳过 {f}（已在库里）')
    stop = threading.Event()

    def job(e):
        d = os.path.join(LIB, slug(e['family']))
        existed, t1, n = os.path.isdir(d), time.time(), 0
        while True:
            n += 1
            try:
                return e, fetch_family(e), None, n, time.time() - t1
            except Exception as ex:  # noqa: BLE001
                kind = fail_kind(ex)
                if kind != 'net' or n >= tries or stop.is_set():
                    if not existed and os.path.isdir(d):      # written, then failed (scan error, disk): leave no half family
                        shutil.rmtree(d, ignore_errors=True)
                    return e, None, ex, n, time.time() - t1
                wait = (60 if isinstance(ex, urllib.error.HTTPError) and ex.code in (403, 429) else 10) * n
                out(f'       重试 {e["family"]}（第 {n} 次失败：{str(ex)[:120]}；{wait}s 后再试）')
                if stop.wait(wait):
                    return e, None, ex, n, time.time() - t1
    added, failed, got = [], [], 0
    last, unsaved = time.time(), 0
    ex = ThreadPoolExecutor(max_workers=jobs)
    futs = [ex.submit(job, e) for e in todo]
    i = 0
    try:
        for fu in as_completed(futs):
            e, entry, err, n, dt = fu.result()
            i, k = i + 1, k + 1
            el = time.time() - t0
            eta = el / i * (len(todo) - i)
            head = f'[{k:>4}/{N} {k * 100 // N:3d}% 已用 {hms(el)} 还要约 {hms(eta)}]'
            if err:
                kind = fail_kind(err)
                failed.append({'family': e['family'], 'kind': kind, 'error': str(err)[:500], 'tries': n})
                out(f'{head} 失败 {e["family"]}：{FAIL_KIND[kind]}：{str(err)[:200]}')
                continue
            cat['families'][entry['family']] = entry
            added.append(entry['family'])
            got += entry['bytes']
            unsaved += 1
            out(f'{head} 入库 {entry["family"][:34]:34} {len(entry["faces"]):2} 个文件 {fmt_mb(entry["bytes"]):>8}  '
                f'{entry["license"]:10} {GROUP_ZH[entry["group"]]}  {dt:4.1f}s' + (f'（试了 {n} 次）' if n > 1 else ''))
            for nt in filter(None, entry['note'].split('；')):
                out(f'       提示：{nt}')
            if unsaved >= 25 or (unsaved and time.time() - last > 60):     # resumable: what is saved is skipped next time
                save_catalog(cat)
                last, unsaved = time.time(), 0
    except KeyboardInterrupt:
        stop.set()
        ex.shutdown(wait=False, cancel_futures=True)
        out('中断了：已入库的都已保存，再跑同一条命令从断点续上')
    else:
        ex.shutdown(wait=True)
    save_catalog(cat)
    write_md(cat)
    el = time.time() - t0
    lib_bytes = sum(e['bytes'] for e in cat['families'].values())
    rep = {'started': stamp, 'seconds': round(el), 'gf_families': N, 'skipped': len(skip), 'planned': len(todo),
           'added': added, 'failed': failed, 'bytes_added': got, 'library_families': len(cat['families']),
           'library_bytes': lib_bytes, 'jobs': jobs, 'tries': tries}
    repp = os.path.join(LOGS, f'get-all-google-{stamp}.json')
    write_atomic(repp, json.dumps(rep, ensure_ascii=False, indent=1))
    rest = N - len(skip) - len(todo)            # left out by --limit
    out(f'完成：Google Fonts {N} 个家族 — 已在库里跳过 {len(skip)}，新入库 {len(added)}，失败 {len(failed)}'
        + (f'，没轮到 {len(todo) - i}' if i < len(todo) else '') + (f'，--limit 没排进这次的 {rest}' if rest else '')
        + f'。这次下载 {fmt_mb(got)}，用时 {hms(el)}。')
    by = {}
    for x in failed:
        by.setdefault(x['kind'], []).append(x['family'])
    for kind, names in by.items():
        out(f'  {FAIL_KIND[kind]} {len(names)} 个：' + '、'.join(names[:40]) + ('…' if len(names) > 40 else ''))
    out(f'库里共 {len(cat["families"])} 个家族、{fmt_mb(lib_bytes)} → {CATALOG_MD}、{CATALOG_ALL_MD}')
    out(f'失败清单和原因：{repp}' + ('；网络失败的再跑一次同一条命令会重试' if by.get('net') else ''))
    out('出全量分页样张：fonts.py specimen --all')
    logf.close()
    return 130 if stop.is_set() else (1 if failed else 0)


def hms(s):
    s = int(s)
    return f'{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}' if s >= 3600 else f'{s // 60}:{s % 60:02d}'


def head_size(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD'), timeout=60) as r:
        return int(r.headers.get('Content-Length') or 0)


def estimate_google(fams, todo, skip, jobs):
    """--estimate: every manifest (the same file choice as get) + a HEAD per file for its size; then a short real
    download of a few files to measure throughput at this --jobs. Nothing is written to the library."""
    t0 = time.time()
    if not todo:
        say(f'Google Fonts 目录 {len(fams)} 个家族：全部已在库里，不用下。')
        return 0
    say(f'Google Fonts 目录 {len(fams)} 个家族：已在库里 {len(skip)} 个，要下 {len(todo)} 个。读下载清单、问每个文件多大…')
    plans, errs, lat = {}, [], []

    def one(e):
        t1 = time.time()
        for n in range(3):
            try:
                p = plan_for(e)
                files = [(u, name, head_size(u)) for u, name in p['files']]
                return e['family'], files, None, time.time() - t1
            except Exception as ex:  # noqa: BLE001
                if fail_kind(ex) != 'net' or n == 2:
                    return e['family'], None, ex, time.time() - t1
                time.sleep(3 * (n + 1))
    with ThreadPoolExecutor(max_workers=max(jobs, 8)) as ex:
        for i, (fam, files, err, dt) in enumerate(ex.map(one, todo), 1):
            lat.append(dt)
            if err:
                errs.append((fam, fail_kind(err), str(err)[:160]))
            else:
                plans[fam] = files
            if i % 200 == 0:
                say(f'  {i}/{len(todo)}  {hms(time.time() - t0)}')
    files = [x for fs in plans.values() for x in fs]
    total, nfiles = sum(s for _, _, s in files), len(files)
    big = sorted(((sum(s for _, _, s in fs), fam, len(fs)) for fam, fs in plans.items()), reverse=True)
    # throughput sample: a spread of 300 KB – 4 MB files; when everything left is smaller, the largest few
    sample = sorted((x for x in files if 300_000 <= x[2] <= 4_000_000), key=lambda x: x[0])[::97][:jobs * 3]
    small = not sample
    if small:
        sample = sorted((x for x in files if x[2] > 0), key=lambda x: -x[2])[:jobs * 3]

    def grab(x):
        try:
            return len(http(x[0]))
        except Exception:  # noqa: BLE001 — a sample that fails only makes the measurement smaller
            return 0
    sb, bw = 0, 0.0
    if sample:
        t1 = time.time()
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            sb = sum(ex.map(grab, sample))
        bw = sb / max(time.time() - t1, 0.001)
    per_fam = sum(lat) / max(len(lat), 1)       # manifest + HEADs ≈ the requests get makes besides the downloads
    scan = 0.25     # licence check + scan per family. Errs long: 2026-11-06, 1898 families at --jobs 4, estimate 4:36, real 2:21
    rest = len(plans) * (per_fam + scan) / jobs
    unknown = sum(1 for _, _, sz in files if not sz)
    if unknown and unknown == nfiles:
        say(f'估算：{len(plans)} 个家族、{nfiles} 个文件，大小未知（服务器没给文件大小）')
    else:
        say(f'估算：{len(plans)} 个家族、{nfiles} 个文件、共 {fmt_mb(total)}（D 盘留够 {fmt_mb(total * 1.1)} 就行）'
            + (f'；另有 {unknown} 个文件没问到大小，不在总数里' if unknown else ''))
    if bw:
        say(f'  试下载 {len(sample)} 个文件 {fmt_mb(sb)}' + ('（剩下的文件都不到 300 KB，测的是最大的几个，速度偏保守）' if small else '') +
            f'：{jobs} 路并行约 {bw / 1048576:.1f} MB/s；每个家族的清单请求约 {per_fam:.2f}s')
        say(f'  预计用时约 {hms(total / bw + rest)}（下载 {hms(total / bw)} + 清单和核对 {hms(rest)}，--jobs {jobs}）')
    else:
        say(f'  没测到下载速度（{"试下载的文件一个也没下下来" if sample else "没有能试下载的文件"}），下载时间不估；'
            f'清单和核对约 {hms(rest)}（--jobs {jobs}）')
    if big:
        say(f'  最大的 {min(10, len(big))} 个家族：' + '；'.join(f'{fam} {fmt_mb(s)}（{n} 个文件）' for s, fam, n in big[:10]))
    for fam, kind, msg in errs:
        say(f'  估算时就失败：{fam}：{FAIL_KIND[kind]}：{msg}')
    say(f'（估算本身用时 {hms(time.time() - t0)}）真下载：fonts.py get --all-google --jobs {jobs}')
    return 0


# ---------------------------------------------------------------------------------------------------------- catalog
def load_catalog():
    if os.path.exists(CATALOG):
        with open(CATALOG, encoding='utf-8') as f:
            return json.load(f)
    return {'version': 1, 'families': {}}


def gkey(e):
    return (GROUP_ORDER.index(e['group']) if e.get('group') in GROUP_ORDER else 99, e['family'].lower())


def save_catalog(cat):
    cat['version'], cat['library'] = 1, LIB
    cat['updated'] = datetime.datetime.now().isoformat(timespec='seconds')
    cat['families'] = dict(sorted(cat['families'].items(), key=lambda kv: gkey(kv[1])))
    write_atomic(CATALOG, json.dumps(cat, ensure_ascii=False, indent=1))
    idx_save()       # no pruning here: a batch scans families before they reach the catalog


def md_cell(s):
    return str(s or '').replace('|', '\\|').replace('\n', ' ')


def is_curated(e):
    """精选架: families someone wrote a usage note for (fonts_starter.json fits, or get --fits); the rest is the full index."""
    return bool(e.get('fits'))


SPEC_PER_PAGE = 40
# Google Fonts subsets → 文字集 in the full index. '' = covered otherwise (Latin and CJK are judged from the font's own
# characters) or not a script; a subset missing here counts towards "+N 种文字".
SUBSET_ZH = {'latin': '', 'latin-ext': '', 'cyrillic-ext': '', 'greek-ext': '', 'chinese-simplified': '', 'chinese-traditional': '',
             'chinese-hongkong': '', 'japanese': '', 'korean': '', 'kana-extended': '', 'math': '', 'symbols': '', 'symbols2': '',
             'music': '', 'braille': '', 'menu': '', 'cyrillic': '西里尔', 'greek': '希腊', 'vietnamese': '越南', 'arabic': '阿拉伯',
             'hebrew': '希伯来', 'devanagari': '天城', 'thai': '泰', 'bengali': '孟加拉', 'tamil': '泰米尔', 'telugu': '泰卢固',
             'kannada': '卡纳达', 'malayalam': '马拉雅拉姆', 'gujarati': '古吉拉特', 'gurmukhi': '古木基', 'oriya': '奥里亚',
             'sinhala': '僧伽罗', 'khmer': '高棉', 'lao': '老挝', 'myanmar': '缅甸', 'tibetan': '藏', 'georgian': '格鲁吉亚',
             'armenian': '亚美尼亚', 'ethiopic': '埃塞俄比亚', 'mongolian': '蒙古', 'syriac': '叙利亚', 'thaana': '它拿',
             'cherokee': '切罗基', 'canadian-aboriginal': '加拿大原住民', 'tifinagh': '提非纳', 'adlam': '阿德拉姆', 'emoji': 'emoji'}
SUBSET_POS = {s: i for i, s in enumerate(SUBSET_ZH)}
TAG_ZH = {'Business': '商务', 'Competent': '稳重', 'Calm': '平静', 'Sincere': '真诚', 'Vintage': '复古', 'Loud': '张扬',
          'Rugged': '粗犷', 'Childlike': '童趣', 'Awkward': '笨拙', 'Artistic': '艺术', 'Stiff': '板正', 'Playful': '俏皮',
          'Futuristic': '未来感', 'Happy': '欢快', 'Excited': '兴奋', 'Active': '动感', 'Innovative': '新颖', 'Fancy': '华丽',
          'Cute': '可爱', 'Sophisticated': '精致', 'Humanist': '人文', 'Geometric': '几何', 'Neo Grotesque': '新怪诞',
          'Grotesque': '怪诞', 'Rounded': '圆体', 'Superellipse': '方圆', 'Glyphic': '碑刻', 'Transitional': '过渡衬线',
          'Old Style Garalde': '旧式衬线', 'Modern': '现代衬线', 'Didone': '迪多衬线', 'Scotch': '苏格兰衬线', 'Fat Face': '胖脸衬线',
          'Humanist Venetian': '威尼斯人文衬线', 'Clarendon': '克拉伦登粗衬线', 'Handwritten': '手写', 'Informal': '随手写',
          'Upright Script': '直立手写', 'Formal': '正式花体', 'Monospace': '等宽', 'Brush': '笔刷', 'Techno': '科技',
          'Wacky': '古怪', 'Pixel': '像素', 'Distressed': '做旧', 'Woodtype': '木活字', 'Blobby': '圆滚', 'Blackletter': '哥特',
          'Stencil': '模板', 'Medieval': '中世纪', 'Shaded': '阴影', 'Inline': '内线', 'Art Deco': '装饰艺术',
          'Tuscan': '托斯卡纳', 'Art Nouveau': '新艺术', "Valentine's Day": '情人节', 'Holi': '洒红节', 'Diwali': '排灯节',
          'Lunar New Year': '春节', 'Kwanzaa': '宽扎节', 'Halloween': '万圣节', 'Christmas': '圣诞', 'Hanukkah': '光明节',
          'Learn To Write': '习字', 'Easy Reading': '易读', 'Symbols': '符号', 'Barcode': '条码', 'Redaction': '涂黑'}
TAG_FIRST = ('/Theme/', '/Script/', '/Sans/', '/Serif/', '/Slab/', '/Monospace/', '/Special use/', '/Purpose/', '/Expressive/')


def all_order(cat):
    """{group: [entries]} in the order of catalog_all.md and specimen\\all\\: curated first, then by Google popularity."""
    by = {}
    for e in cat['families'].values():
        by.setdefault(e['group'], []).append(e)
    for es in by.values():
        es.sort(key=lambda e: (not is_curated(e), 0 if is_curated(e) else gf_info(e)[0], e['family'].lower()))
    return {g: by[g] for g in GROUP_ORDER + sorted(set(by) - set(GROUP_ORDER)) if g in by}


def sheet_names(order, per):
    """(family → sheet name like 'tech_03', group → number of sheets)."""
    pages, counts = {}, {}
    for g, es in order.items():
        counts[g] = (len(es) + per - 1) // per
        for i, e in enumerate(es):
            pages[e['family']] = f'{g}_{i // per + 1:02d}'
    return pages, counts


def load_pages():
    try:
        with open(SPEC_PAGES, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def tags_short(e, n=5):
    ts = sorted(e.get('tags') or [], key=lambda t: (next((i for i, p in enumerate(TAG_FIRST) if t.startswith(p)), 99), t))
    return list(dict.fromkeys(t.rsplit('/', 1)[-1] for t in ts))[:n]


def scripts_short(e):
    """compact 文字集: CJK and Latin from the font's own characters, the rest from Google's subsets."""
    c = e['faces'][0]['cov']
    L = []
    if c['gb1'] >= 3740:
        L.append('简中')
    elif c['gb1'] >= 800:
        L.append('简中缺字')
    if c['big5'] >= 5380:
        L.append('繁中')
    elif c['big5'] >= 2000:
        L.append('繁中缺字')
    if c['kana'] >= 150:
        L.append('日文')
    if c['hangul'] >= 2000:
        L.append('韩文')
    if c['latin'] >= 60:
        L.append('拉丁')
    elif c['digits'] == 10 and not L:
        L.append('数字')
    subs = gf_info(e)[1]
    more = [SUBSET_ZH[s] for s in sorted((s for s in subs if SUBSET_ZH.get(s)), key=SUBSET_POS.get)]   # common scripts first
    other = sum(1 for s in subs if s not in SUBSET_ZH)
    L += more[:4]
    if len(more) > 4 or other:
        L.append(f'+{len(more) - 4 + other if len(more) > 4 else other} 种文字')
    return '、'.join(L) or '（极少字符）'


def weights_short(e):
    ax = [f'{t} {v[0]:g}–{v[2]:g}' for t, v in e['axes'].items() if t != 'wght']
    s = e['weights'] + (('；' + '；'.join(ax[:3]) + (f'；…共 {len(ax)} 个轴' if len(ax) > 3 else '')) if ax else '')
    return s + (f'；彩色 {e["color"]}' if e.get('color') else '')


def write_md(cat):
    """catalog.md: the curated shelf (usage notes, by group) + an overview of every group; catalog_all.md: every family."""
    fams = list(cat['families'].values())
    nfiles = sum(len(e['faces']) for e in fams)
    size = sum(e['bytes'] for e in fams)
    cur = [e for e in fams if is_curated(e)]
    order = all_order(cat)
    pinfo = load_pages()
    per = pinfo.get('per_page') or SPEC_PER_PAGE
    pages, counts = sheet_names(order, per)
    rendered = pinfo.get('pages') or {}
    L = ['# 字体库目录', '',
         f'> 由 `fonts.py` 自动生成（{datetime.datetime.now():%Y-%m-%d %H:%M}），不要手改。用法写进 skill 的 `scripts/fonts_starter.json`（fits），'
         '或 `fonts.py get "家族" --fits "…"`。', '',
         f'库：`{LIB}`，共 **{len(fams)} 个家族**、{nfiles} 个字体文件、{size / 1048576:.0f} MB。文件路径相对于库目录。'
         '全部可免费商用、可做进视频；授权原文在各家族目录里（OFL.txt / LICENSE.txt），入库和每次重写目录时都核对授权原文和字体文件 name 表，'
         '对不上的不收；name 表写的是另一种也能商用的授权时照收，授权栏注明，鸣谢按授权文件。', '',
         f'分两层：**精选架** {len(cur)} 个家族，每个都写了适合什么片子、怎么用，下面按风格组列出；**全量** {len(fams)} 个'
         '（Google Fonts 全部家族 + 精选架），每个家族一行的紧凑索引在 `catalog_all.md`，分页样张在 `specimen\\all\\`。'
         '先在精选架里挑，没有合适的再翻全量。', '',
         '## 怎么用', '',
         '1. 挑字：先看 `specimen\\<风格组>.png`（精选架）。排具体的标题先跑 `fonts.py specimen --text "谁最强"`（缺的字标红）'
         '或 `fonts.py search --local --text "谁最强"`（只列缺字）。精选架里没有合适的：翻全量——`catalog_all.md`（每组精选在前、'
         '其余按 Google 热度排，带官方风格标签和样张页码）和 `specimen\\all\\<风格组>_<页>.png`（每张几十个家族，字名写在左边），'
         '或 `fonts.py search --local --group script --tag Handwritten`、`--script zh`、`--tag Techno --var`。'
         '库里也没有的：`fonts.py search --group blackletter` 搜在线目录，`fonts.py get "家族名"` 入库。',
         '2. 放进项目：`fonts.py use <项目> "Ma Shan Zheng" "UnifrakturMaguntia"`。字体复制进 `web\\assets\\fonts\\`，'
         '`index.html` 自动接好；改了文案再跑一次 `fonts.py use <项目>`（中文字体只含项目里出现过的字）。'
         '描边、空心字（`-webkit-text-stroke`、`ctx.strokeText`）用静态字体：`fonts.py use <项目> "Montserrat:900" --static`'
         '（从可变字体切出这个字重并合并重叠的轮廓，描边不会在字里露出接缝线）。',
         "3. 页面里：CSS `font-family: 'Ma Shan Zheng', serif;`；canvas `` ctx.font = `120px ${T3.fonts.use('Ma Shan Zheng', 'serif')}` ``。"
         '只有一个字重的字体：低于 600 的别写 bold（浏览器会假加粗），600 及以上的本身就是粗体。'
         '可变字体用 `font-weight` / `font-variation-settings` 调轴。',
         '4. 片尾鸣谢：`fonts.py credits <项目>`。',
         '5. 全量里的家族用顺手了、想放上精选架：`fonts.py get "家族" --fits "适合什么片子、怎么用"`（已在库里只更新说明，不重下）。', '',
         '| 风格组 | 精选架 | 全量 | 精选样张 | 全量样张 |', '|---|---|---|---|---|']
    by = {}
    for e in cur:
        by.setdefault(e['group'], []).append(e)
    for g in order:
        n = counts[g]
        L.append(f'| {GROUP_ZH.get(g, g)}（{g}） | {len(by.get(g, []))} | {len(order[g])} | '
                 f'{f"specimen/{g}.png" if g in by else "—"} | specimen/all/{g}_01.png' + (f' … _{n:02d}.png' if n > 1 else '') + ' |')
    for g in GROUP_ORDER:
        if g not in by:
            continue
        L += ['', f'## {GROUP_ZH[g]}（{g}）', '', f'样张：`specimen\\{g}.png`', '',
              '| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |', '|---|---|---|---|---|---|---|']
        for e in sorted(by[g], key=lambda x: x['family'].lower()):
            ax = '；'.join(f'{t} {v[0]:g}–{v[2]:g}' for t, v in e['axes'].items() if t != 'wght')
            w = e['weights'] + (f'；{ax}' if ax else '') + (f'；彩色 {e["color"]}' if e.get('color') else '')
            sc = '、'.join(e['scripts']) + (f'；汉字 {e["hanzi"]}' if e['hanzi'] else '')
            lic = e['license'] + (f'（保留名 {", ".join(e["rfn"])}）' if e.get('rfn') else '') + \
                ''.join(f'<br>注：{n}' for n in license_notes(e))
            files = [f['file'] for f in e['faces']]
            fl = '<br>'.join(files if len(files) <= 4 else files[:3] + [f'…共 {len(files)} 个'])
            L.append(f"| **{md_cell(e['family'])}** | {md_cell(e.get('fits') or '（待补：get --fits）')} | {md_cell(w)} | {md_cell(sc)} | "
                     f"{md_cell(lic)} | {md_cell('、'.join(e['designers']))} | {md_cell(fl)} |")
    L += ['', '## 全量：各风格组概览', '',
          f'每个家族一行的索引在 `catalog_all.md`（共 {len(fams)} 个，★ = 精选架）；分页样张 `specimen\\all\\<风格组>_<页>.png`，'
          f'每张 {per} 个家族，顺序和索引一致：精选在前，其余按 Google Fonts 热度排（越靠前越常用）。', '',
          '| 风格组 | 家族数 | 样张页 | 热度靠前的 | 常见官方风格标签 |', '|---|---|---|---|---|']
    for g, es in order.items():
        top = sorted((e for e in es if e.get('source') == 'Google Fonts'), key=lambda e: gf_info(e)[0])[:8]
        tc = {}
        for e in es:      # classification and theme tags; the Expressive ones (Business, Calm…) say little here
            for t in {t.rsplit('/', 1)[-1] for t in e.get('tags') or [] if not t.startswith(('/Expressive/', '/Seasonal/'))}:
                tc[t] = tc.get(t, 0) + 1
        common = sorted(tc.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        n = counts[g]
        L.append(f'| [{GROUP_ZH.get(g, g)}（{g}）](catalog_all.md#{g}) | {len(es)} | {g}_01' + (f' … {g}_{n:02d}' if n > 1 else '') +
                 f" | {md_cell('、'.join(e['family'] for e in top))} | {md_cell('、'.join(f'{t}（{TAG_ZH.get(t, t)}）{k}' for t, k in common))} |")
    L += ['', '## 不在库里的免费商用字体（平面设计师不要自己下）', '',
          '阿里巴巴普惠体 3.0 / 阿里妈妈系列、HarmonyOS Sans、MiSans：协议允许免费用在视频等商业作品里，但都是专有授权——'
          '下载或使用即视为同意协议，而且禁止修改、转格式、拆分字体（`fonts.py use` 的子集和 WOFF2 都算），'
          'HarmonyOS Sans 和 MiSans 还要求在作品里注明。要用先请主线程问用户本人，确认后整份放进 `manual\\`，不走 `fonts.py use`。', '']
    write_atomic(CATALOG_MD, '\n'.join(L))
    write_all_md(cat, order, pages, counts, per, rendered, pinfo.get('rendered'))


def write_all_md(cat, order, pages, counts, per, rendered, when):
    fams = cat['families']
    stale = sum(1 for f, p in pages.items() if rendered.get(f) != p)
    L = ['# 字体库全量索引', '',
         f'> 由 `fonts.py` 自动生成（{datetime.datetime.now():%Y-%m-%d %H:%M}），不要手改。精选架（★）的用法说明、授权、作者和文件在 `catalog.md`。', '',
         f'共 **{len(fams)} 个家族**（★ 精选架 {sum(1 for e in fams.values() if is_curated(e))} 个），按风格组分节；每组精选在前，'
         '其余按 Google Fonts 热度排（越靠前越常用）。「样张」一栏是这个家族在 `specimen\\all\\` 里的那一张，'
         f'每张 {per} 个家族、字名写在左边。' + (f'样张是 {when} 出的' + (f'，之后有 {stale} 个家族的页码变了或是新入库的：重跑 '
                                                                    '`fonts.py specimen --all`' if stale else '，和本索引一致') + '。'
                                                   if when else '还没出全量样张：`fonts.py specimen --all`。'), '',
         '找字：Ctrl+F 搜家族名或官方风格标签（英文，见下表）；命令行 `fonts.py search --local --tag Techno --script latin`'
         '（--tag 也认中文名：`--tag 科技`），'
         '`--text "谁最强"` 按缺字多少排。用：`fonts.py use <项目> "家族名"`；描边、空心字 `fonts.py use <项目> "家族名:900" --static`。', '',
         '各栏：**官方风格标签** = Google Fonts 的分类（Sans Serif / Serif / Display / Handwriting / Monospace）+ 分数 ≥ 60 的风格标签'
         '（只写最后一段，/Sans/Geometric → Geometric），最多 5 个；**文字集**：拉丁、简中、繁中、日文、韩文按字体里实际有的字算'
         '（简中 = GB2312 一级字齐全，缺字 = 只有一部分），其余按 Google 的子集；**字重 / 可变**：「100–900 可变」= 一个可变字体文件包含'
         '这个范围的所有字重，其余轴（wdth 宽度、opsz 光学尺寸、slnt 倾斜…）用 `font-variation-settings` 调。', '',
         '标签对照：' + '，'.join(f'{k} {v}' for k, v in TAG_ZH.items()) + '。', '',
         ' · '.join(f'[{GROUP_ZH.get(g, g)} {len(es)}](#{g})' for g, es in order.items()), '']
    for g, es in order.items():
        n = counts[g]
        L += [f'<a id="{g}"></a>', '', f'## {GROUP_ZH.get(g, g)}（{g}）', '',
              f'{len(es)} 个家族 · 样张 `specimen\\all\\{g}_01.png`' + (f' … `{g}_{n:02d}.png`' if n > 1 else '') +
              (f' · 精选架样张 `specimen\\{g}.png`' if any(is_curated(e) for e in es) else ''), '',
              '| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |', '|---|---|---|---|---|']
        for e in es:
            tags = '、'.join(tags_short(e))
            kind = e.get('category') or ''
            L.append(f"| {'★ ' if is_curated(e) else ''}**{md_cell(e['family'])}** | {md_cell(kind + (' · ' if kind and tags else '') + tags) or '—'} | "
                     f"{md_cell(scripts_short(e))} | {md_cell(weights_short(e))} | {pages[e['family']]} |")
        L.append('')
    write_atomic(CATALOG_ALL_MD, '\n'.join(L))


def cmd_catalog(a):
    cat = load_catalog()
    if a.rescan:
        cov_sets()
        for e in cat['families'].values():
            d = os.path.join(LIB, e['slug'])
            e['faces'] = scan_faces(d, [os.path.basename(f['file']) for f in e['faces']], e['slug'])
            summarize(e)
        say(f'重读了 {len(cat["families"])} 个家族的字体文件')
    bad, lossy, noted = [], [], []
    for e in cat['families'].values():      # every run: reserved names + the same licence checks as get
        p = os.path.join(LIB, e['license_file'])
        text = None
        if os.path.exists(p):
            with open(p, encoding='utf-8', errors='replace') as f:
                text = f.read()
        names, probs = [], []
        for fc in e['faces']:
            try:
                names.append(name_strings(os.path.join(LIB, fc['file'])))
            except Exception as ex:  # noqa: BLE001
                probs.append(f'读不了字体文件 {fc["file"]}（{ex}），核对不了')
        e['rfn'] = family_rfn(text, names)
        if text is None:
            probs.append(f'授权文件不见了：{e["license_file"]}')
            set_note(e)
        else:
            p2, notes = license_check(e['license'], text, names)
            probs += p2
            set_note(e, notes)
            noted += [(e['family'], n) for n in notes]
        if probs:
            bad.append((e['family'], probs))
        if en_lossy(e):
            lossy.append(e['family'])
    save_catalog(cat)
    idx_faces()
    idx_save(keep={f['file'] for e in cat['families'].values() for f in e['faces']})   # drop faces no longer in the library
    write_md(cat)
    say(f'{CATALOG_MD}（{len(cat["families"])} 个家族，{sum(1 for e in cat["families"].values() if e.get("rfn"))} 个带保留名）')
    for fam, probs in bad:
        say(f'  ！授权核对不过 {fam}：' + '；'.join(probs))
    for fam, n in noted:                    # kept: only worth a look, not a failure
        say(f'  提示 {fam}：{n}')
    if lossy:
        say('  英文鸣谢略去了中文名（补 designers_en）：' + '、'.join(lossy))
    return 1 if bad else 0


def cmd_groups(a):
    cat = load_catalog()
    n = {}
    for e in cat['families'].values():
        n[e['group']] = n.get(e['group'], 0) + 1
    for g, z, rule in GROUPS:
        how = ('、'.join(t.split('/')[-1] for t in rule.get('tags', [])) or
               ('文字 ' + rule['script'] + (' + ' + '/'.join(rule['cat']) if rule.get('cat') else '') if rule.get('script') else '') or
               ('/'.join(rule.get('cat', [])) or
                ('名字含 condensed/compressed/narrow（不含 expanded/extended/wide），或 Display 类带宽度轴' if rule.get('name') else '其余')))
        say(f'{g:16} {z:16} 库里 {n.get(g, 0):2} 个   在线目录按：{how}')
    say('自动分组的先后：名字含 pixel/dseg → 中文 / 日文 → 哥特、像素、模板标签 ≥ 60 → Monospace → 其余按分数高低')


# --------------------------------------------------------------------------------------------------------------- use
def web_root(p):
    p = os.path.abspath(p)
    if os.path.isfile(p) and p.lower().endswith('.html'):
        return os.path.dirname(p), p
    for c in (os.path.join(p, 'web'), p):
        if os.path.isfile(os.path.join(c, 'index.html')):
            return c, os.path.join(c, 'index.html')
    raise SystemExit(f'找不到 index.html：给项目目录（里面有 web\\index.html）或 web 目录。收到：{p}')


def project_chars(web, fdir):
    chars, skip = set(), os.path.normcase(os.path.abspath(fdir))
    # lib/fonts.js is ours and never drawn; it is copied in after this scan, so counting it made `use --check` cry "stale"
    own_js = os.path.normcase(os.path.abspath(os.path.join(web, 'lib', 'fonts.js')))
    for root, dirs, files in os.walk(web):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'gsap') and not d.startswith('_frames')
                   and os.path.normcase(os.path.abspath(os.path.join(root, d))) != skip]
        for fn in files:
            if fn.lower().endswith(TEXT_EXT) and os.path.normcase(os.path.abspath(os.path.join(root, fn))) != own_js:
                p = os.path.join(root, fn)
                try:
                    if os.path.getsize(p) <= 30_000_000:
                        with open(p, encoding='utf-8', errors='ignore') as f:
                            chars.update(f.read())
                except OSError:
                    pass
    return {c for c in chars if c == ' ' or (c.isprintable() and not c.isspace())}


def parse_spec(s):
    m = re.match(r'^(.*?)(?::(\d{3}|italic|\d{3}i(?:talic)?))?$', s.strip())
    return m.group(1).strip(), (m.group(2) or None)


def select_faces(e, sel):
    if not sel:
        return e['faces']
    it = 'i' in sel
    w = int(re.sub(r'\D', '', sel) or 0)
    out = [f for f in e['faces'] if (not w or wrange(f['weight'])[0] <= w <= wrange(f['weight'])[1])
           and (f['style'] == 'italic') == it]
    if not out:
        raise SystemExit(f'{e["family"]} 没有 {sel}；有：' + '、'.join(f"{f['weight']} {f['style']}" for f in e['faces']))
    return out


def find_family(cat, name):
    k = name.lower()
    return next((e for f, e in cat['families'].items() if f.lower() == k or e['slug'] == slug(name)), None)


def pack_face(src, mode, chars, pin=None):
    """(woff2 bytes, glyph-mapped chars kept, kept string or '', notes). pin = {'wght': 900}: a static cut for outline
    text (use --static), see make_static()."""
    from fontTools.ttLib import TTFont, woff2
    if mode == 'full' and pin is None:
        if src.lower().endswith('.woff2'):
            with open(src, 'rb') as f:
                return f.read(), len(cmap_of(src)), '', []
        buf = io.BytesIO()
        woff2.compress(src, buf)                       # lossless: same tables, brotli
        return buf.getvalue(), len(cmap_of(src)), '', []
    f = TTFont(src, recalcTimestamp=False)
    cmap = f.getBestCmap() or {}
    want = ''
    if mode == 'subset':          # subset first: instancing and merging a few hundred glyphs beats a 30 000-glyph CJK font
        from fontTools import subset as fts
        want = ''.join(sorted(c for c in chars if ord(c) in cmap))
        o = fts.Options()
        o.layout_features, o.name_IDs, o.name_languages = ['*'], ['*'], ['*']
        o.name_legacy, o.notdef_outline, o.legacy_kern = True, True, True
        s = fts.Subsetter(o)
        s.populate(text=want)
        s.subset(f)
    notes = make_static(f, pin) if pin is not None else []
    buf = io.BytesIO()
    f.flavor = 'woff2'
    f.save(buf)
    f.close()
    return buf.getvalue(), (len(want) if mode == 'subset' else len(cmap)), want, notes


def make_static(f, pin):
    """in place: a variable font → the static instance at `pin` (axes not given: their default), then overlapping
    contours merged. Variable fonts draw a stroke over a stroke (the bar of an A over its legs); filled that is
    invisible, but -webkit-text-stroke / ctx.strokeText outline every contour and the overlaps show as seams inside the
    letters. A static font is only merged. Needs skia-pathops (pip install skia-pathops). → notes for the report."""
    try:
        import pathops  # noqa: F401
    except ImportError:
        raise SystemExit('--static 要合并轮廓，需要 skia-pathops：pip install skia-pathops')
    from fontTools.ttLib.removeOverlaps import removeOverlaps
    notes = []
    if 'fvar' in f:
        from fontTools.varLib import instancer
        limits = {}
        for ax in f['fvar'].axes:
            v = pin.get(ax.axisTag)
            limits[ax.axisTag] = ax.defaultValue if v is None else min(max(float(v), ax.minValue), ax.maxValue)
            if v is not None and limits[ax.axisTag] != float(v):
                notes.append(f'{ax.axisTag} {v} 超出范围，用了 {limits[ax.axisTag]:g}')
        instancer.instantiateVariableFont(f, limits, inplace=True, overlap=instancer.OverlapMode.KEEP_AND_DONT_SET_FLAGS)
        notes.append('切自可变字体：' + '，'.join(f'{k} {v:g}' for k, v in limits.items()))
    try:
        removeOverlaps(f)
    except Exception as ex:  # noqa: BLE001 — a glyph pathops cannot merge: keep it as drawn, say which
        removeOverlaps(f, ignoreErrors=True)
        notes.append(f'有字形合并轮廓失败，保留原样（{str(ex)[:80]}）')
    return notes


def system_fonts():
    names = set()
    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                k = winreg.OpenKey(hive, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts')
            except OSError:
                continue
            i = 0
            while True:
                try:
                    v = winreg.EnumValue(k, i)[0]
                except OSError:
                    break
                for part in re.sub(r'\s*\((TrueType|OpenType|All res)\)\s*$', '', v).split(' & '):
                    names.add(part.strip().lower())
                i += 1
    except ImportError:
        pass
    return names


def ensure_tags(index):
    with open(index, encoding='utf-8') as f:
        s = f.read()
    comments = [(m.start(), m.end()) for m in re.finditer(r'<!--.*?-->', s, re.S)]
    live = lambda m: not any(a <= m.start() < b for a, b in comments)  # noqa: E731
    has = lambda pat: any(live(m) for m in re.finditer(pat, s))         # noqa: E731
    need = []
    if not has(r'<script[^>]*src=["\']lib/fonts\.js["\']'):
        need.append('<script src="lib/fonts.js"></script>')
    if not has(r'<script[^>]*src=["\']assets/fonts/fontpack\.js["\']'):
        need.append('<script src="assets/fonts/fontpack.js"></script>')
    if not need:
        return '已接好（lib/fonts.js、assets/fonts/fontpack.js 都在）'
    eng = next((m for m in re.finditer(r'<script[^>]*src=["\'][^"\']*engine\.js["\'][^>]*>\s*</script>', s) if live(m)), None)
    if not eng:
        return '没找到 engine.js 的 <script>，请手动在它后面加：' + ' '.join(need)
    s = s[:eng.end()] + '\n' + '\n'.join(need) + s[eng.end():]
    write_atomic(index, s)
    return '已在 engine.js 后加 ' + '、'.join(re.search(r'src="([^"]+)"', x).group(1) for x in need)


def ensure_lib(web):
    dst = os.path.join(web, 'lib', 'fonts.js')
    with open(LIB_JS, 'rb') as f:
        new = f.read()
    if os.path.exists(dst):
        with open(dst, 'rb') as f:
            if f.read() == new:
                return 'lib/fonts.js 已是最新'
        write_atomic(dst, new)
        return 'lib/fonts.js 已更新到 skill 版本'
    write_atomic(dst, new)
    return 'lib/fonts.js 已复制进项目'


def cmd_use(a):
    web, index = web_root(a.project)
    fdir = os.path.join(web, 'assets', 'fonts')
    mpath = os.path.join(fdir, 'fonts.json')
    man = {'fonts': [], 'extra_text': ''}
    if os.path.exists(mpath):
        with open(mpath, encoding='utf-8') as f:
            man = json.load(f)
    cat = load_catalog()
    for name in a.remove or []:
        n0 = len(man['fonts'])
        man['fonts'] = [x for x in man['fonts'] if name.lower() not in (x['family'].lower(), (x.get('alias') or '').lower())]
        say(f'  已移除 {name}' if len(man['fonts']) < n0 else f'  项目里没有 {name}')
    starter = None
    if a.alias and len(a.families) != 1:
        say('  --alias 只能配一个家族，这次忽略')
    for spec in a.families:
        fam, sel = parse_spec(spec)
        e = find_family(cat, fam)
        if not e:
            say(f'  库里还没有「{fam}」，先下载入库…')
            starter = starter or {x['family'].lower(): x for x in load_starter()}
            try:
                done, failed = fetch_many([resolve_target(fam, starter)])
            except LookupError as ex:
                raise SystemExit(str(ex))
            if failed:
                raise SystemExit(f'「{fam}」下载失败')
            for entry in done:
                cat['families'][entry['family']] = entry
            save_catalog(cat)
            write_md(cat)
            e = find_family(cat, fam)
        item = {'family': e['family'], 'select': sel, 'mode': 'full' if a.full else 'subset' if a.subset else 'auto',
                'alias': a.alias if a.alias and len(a.families) == 1 else None}
        if a.static:              # kept in fonts.json: a later `use <项目>` (refresh) cuts it static again
            item['static'] = True
        man['fonts'] = [x for x in man['fonts'] if not (x['family'] == item['family'] and x.get('alias') == item['alias'])] + [item]
    if a.text:
        man['extra_text'] = ''.join(sorted(set(man.get('extra_text', '')) | set(a.text)))
    if not man['fonts']:
        raise SystemExit('项目里还没有字体：fonts.py use <项目> "家族名" …')
    text_chars = project_chars(web, fdir) | set(man.get('extra_text', ''))     # what the project really writes
    chars = text_chars | BASE_CHARS                                            # + ASCII and common punctuation
    if a.check:
        return check_stale(man, chars)
    os.makedirs(fdir, exist_ok=True)
    sysf = system_fonts()
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    js, rows, total, notes = [], [], 0, []
    for item in man['fonts']:
        e = cat['families'].get(item['family'])
        if not e:
            say(f'  ！库里找不到 {item["family"]}，跳过（catalog.json 被改过？）')
            continue
        reg = item.get('alias') or e['family']
        item['faces'], item['credit_zh'], item['credit_en'] = [], e['credit_zh'], e['credit_en']
        sel, static = item.get('select'), bool(item.get('static'))
        faces = select_faces(e, sel)
        want_w = int(re.sub(r'\D', '', sel) or 0) if sel else 0
        if static and not want_w and any(' ' in f['weight'] for f in faces):
            raise SystemExit(f'--static 要写切哪个字重：fonts.py use <项目> "{e["family"]}:900" --static')
        for face in faces:
            src = os.path.join(LIB, face['file'])
            mode = item['mode'] if item['mode'] != 'auto' else ('subset' if face['hanzi'] >= 1000 or face['bytes'] > 2_000_000 else 'full')
            wl, pin = face['weight'], None
            if static:            # one weight, every other axis at its default, overlapping contours merged
                wl = str(want_w or int(float(face['weight'].split()[0])))
                pin = {'wght': int(wl)}
            elif want_w and ' ' in face['weight']:
                notes.append(f"{reg}:{want_w} 放进去的是整个可变字体（{face['weight'].replace(' ', '–')}，页面按 font-weight 取字重）；"
                             f"描边或空心字加 --static，切成 {want_w} 的静态字体并合并轮廓，字里不露接缝线")
            out = f"{slug(reg)}-{wl.replace(' ', '-')}{'-italic' if face['style'] == 'italic' else ''}{'-static' if static else ''}.woff2"
            data, kept, kept_chars, pnotes = pack_face(src, mode, chars, pin)
            write_atomic(os.path.join(fdir, out), data)
            total += len(data)
            meta = {'family': reg, 'name': e['family'], 'weight': wl, 'style': face['style']}
            if face.get('stretch') and not static:
                meta['stretch'] = face['stretch']
            meta.update(file=out, author='、'.join(e['designers']), license=LICENSES.get(e['license'], e['license']), credit=e['credit_zh'])
            desc = (f'子集 {kept} 个字' if mode == 'subset' else f'完整（{kept} 个字符）') + ('·静态切片' if static else '')
            if pnotes:
                notes.append(f"{reg} {wl} 静态切片：" + '；'.join(pnotes))
            js.append(f"// {e['family']} {wl} {face['style']} — {desc}, WOFF2 {fmt_mb(len(data))}")
            js.append('T3.fonts.add(' + json.dumps(meta, ensure_ascii=False)[:-1] + ', "data": "' + base64.b64encode(data).decode('ascii') + '"});')
            cps = cmap_of(src)
            if face['hanzi'] >= 1000:
                miss = [c for c in text_chars if (0x3400 <= ord(c) <= 0x9FFF or 0x3040 <= ord(c) <= 0x30FF) and ord(c) not in cps]
            elif face['cov']['latin'] >= 60:
                miss = [c for c in text_chars if c.isascii() and c.isalnum() and ord(c) not in cps]
            else:
                miss = []
            item['faces'].append({'src': face['file'], 'out': out, 'weight': wl, 'style': face['style'], 'mode': mode,
                                  'kept': kept, 'kept_chars': kept_chars, 'bytes': len(data), **({'static': True} if static else {})})
            rows.append((reg, wl, face['style'], desc, len(data), ''.join(sorted(miss))))
        shutil.copyfile(os.path.join(LIB, e['license_file']), os.path.join(fdir, f"LICENSE-{e['slug']}.txt"))
        if e['family'].lower() in sysf and not item.get('alias'):
            notes.append(f"本机装了同名系统字体「{e['family']}」：本机上加载失败也看不出来。QA 看 T3.fonts.report() 的 status，"
                         f"或改用别名：fonts.py use <项目> \"{e['family']}\" --alias \"QC {e['family']}\"")
        ws = {f['weight'] for f in item['faces']}              # the weights this page really gets
        if len(ws) == 1 and ' ' not in next(iter(ws)):
            w = int(float(next(iter(ws))))                     # Chrome fakes bold only when bold is asked of a face < 600
            notes.append(f"{reg} 只有 {w} 一个字重：别写 bold，否则浏览器假加粗" if w < 600 else
                         f"{reg} 只有 {w} 一个字重，本身就是粗体：font-weight 写多少都用这一款，不会假加粗")
    head = [f'// fontpack.js — 由 scripts/fonts.py use 生成（{stamp}），不要手改；改了文案再跑一次 fonts.py use <项目>。',
            f'// {len(rows)} 个字面，共 {fmt_mb(total)}。片尾鸣谢：T3.fonts.credits()',
            "if (!window.T3 || !T3.fonts) throw new Error('assets/fonts/fontpack.js: load engine.js and lib/fonts.js first');"]
    write_atomic(os.path.join(fdir, 'fontpack.js'), '\n'.join(head + js) + '\n')
    man.update(generated=stamp, library=LIB, chars=len(chars))
    write_atomic(mpath, json.dumps(man, ensure_ascii=False, indent=1))
    credits = list(dict.fromkeys(x[k] for k in ('credit_zh', 'credit_en') for x in man['fonts'] if x.get(k)))
    write_atomic(os.path.join(fdir, 'CREDITS.txt'), '\n'.join(credits) + '\n\n子集/WOFF2 只为本项目渲染视频而生成，不要单独分发这些字体文件。\n')
    lib_st, tag_st = ensure_lib(web), ensure_tags(index)
    say(f'项目 {web}')
    for reg, wl, style, desc, n, miss in rows:
        say(f"  {reg[:34]:34} {wl:>8} {style:6} {desc:16} WOFF2 {fmt_mb(n):>7}" +
            (f'  项目文字里有、它没有的 {len(miss)} 个：{miss[:40]}' if miss else ''))
    say(f'  写好 assets/fonts/fontpack.js（{fmt_mb(total)}）、fonts.json、CREDITS.txt、LICENSE-*.txt；{lib_st}；index.html {tag_st}')
    say('页面里这样用：')
    for x in man['fonts']:
        reg = x.get('alias') or x['family']
        say(f"  CSS  font-family: '{reg}', serif;      canvas  ctx.font = `120px ${{T3.fonts.use('{reg}', 'serif')}}`;")
    for nt in dict.fromkeys(notes):
        say('  注意：' + nt)
    say('片尾鸣谢：')
    for c in credits:
        say('  ' + c)
    say('改了文案后再跑一次：fonts.py use <项目>（不带家族名 = 按新文字重做子集）；只查不写：fonts.py use <项目> --check')
    return 0


def check_stale(man, chars):
    """--check: does every subset still hold every character the project's files now contain? (writes nothing)"""
    if not any(item.get('faces') for item in man['fonts']):
        say('还没打包过：先跑 fonts.py use <项目>')
        return 1
    stale = []
    for item in man['fonts']:
        for fc in item.get('faces', []):
            if fc['mode'] == 'subset':
                need = {c for c in chars if ord(c) in cmap_of(os.path.join(LIB, fc['src']))} - set(fc.get('kept_chars', ''))
                if need:
                    stale.append((item.get('alias') or item['family'], fc['weight'], ''.join(sorted(need))))
    for fam, w, need in stale:
        say(f'  过期 {fam} {w}：新文字里有 {len(need)} 个字不在子集里：{need[:40]}')
    say('需要重跑 fonts.py use <项目>' if stale else '子集是最新的')
    return 1 if stale else 0


def cmd_credits(a):
    web, _ = web_root(a.project)
    mpath = os.path.join(web, 'assets', 'fonts', 'fonts.json')
    if not os.path.exists(mpath):
        raise SystemExit('这个项目还没用库里的字体（没有 assets/fonts/fonts.json）')
    with open(mpath, encoding='utf-8') as f:
        man = json.load(f)
    for line in dict.fromkeys(x[k] for k in ('credit_zh', 'credit_en') for x in man['fonts'] if x.get(k)):
        say(line)


# ------------------------------------------------------------------------------------------------------------ specimen
SPEC_CSS = """
html,body{margin:0;background:#0f1117;width:1800px}
section{width:1800px;box-sizing:border-box;padding:26px 34px 34px;background:#0f1117;color:#e8eaf0;font-family:'Microsoft YaHei','Segoe UI',sans-serif}
h1{margin:0 0 12px;font-size:30px;color:#ffd84a;font-weight:700}h1 small{margin-left:14px;font-size:17px;color:#8f97aa;font-weight:400}
.row{display:flex;border-top:1px solid #262b38;padding:14px 0 12px}
.meta{width:430px;flex:none;padding-right:20px;font-size:15px;line-height:1.5;color:#98a1b4}
.meta b{display:block;font-size:22px;color:#fff;margin-bottom:2px}.meta .bad,.meta .miss{color:#ff5d5d}
.s{flex:1;min-width:0;overflow:hidden}.ln{white-space:nowrap;line-height:1.22;color:#fff}.ln+.ln{color:#cfd5e4}
.lab{font:600 13px Consolas,monospace;color:#7fd68a;margin-right:12px;vertical-align:middle}
.m{color:#ff4d4d}
"""

SPEC_JS = r"""
(async function () {
  const S = window.SPEC, mk = (t, c, p) => { const e = document.createElement(t); if (c) e.className = c; p.appendChild(e); return e; };
  const added = new Set();
  for (const sec of S.sections) for (const r of sec.rows) if (!added.has(r.alias)) {
    added.add(r.alias);
    for (const f of r.faces) T3.fonts.add(Object.assign({ family: r.alias, name: r.family }, f));
  }
  await Promise.allSettled(window.__H);
  await document.fonts.ready;
  const st = {};
  for (const x of T3.fonts.report()) (st[x.name] = st[x.name] || []).push(x.status);
  const res = { failed: [], missing: {} };
  for (const sec of S.sections) {
    const el = mk('section', '', document.body);
    el.dataset.out = sec.out;
    el.innerHTML = sec.head;
    for (const r of sec.rows) {
      const row = mk('div', 'row', el), meta = mk('div', 'meta', row), s = mk('div', 's', row);
      meta.innerHTML = r.meta;
      const ok = (st[r.family] || []).length && st[r.family].every((x) => x === 'loaded');
      if (!ok) { res.failed.push(r.family); mk('div', 'bad', meta).textContent = '加载失败：' + (st[r.family] || ['?']).join(','); }
      let first = null;
      for (const ln of r.lines) {
        const d = mk('div', 'ln', s);
        if (ln.label) mk('span', 'lab', d).textContent = ln.label;
        const t = mk('span', '', d);
        t.style.cssText = `font-family:'${r.alias}',monospace;font-size:${ln.size}px;font-weight:${ln.weight};font-style:${ln.style || 'normal'};font-variation-settings:${ln.vs || 'normal'}`;
        const miss = new Set(T3.fonts.missing(r.alias, ln.text, { weight: ln.weight, style: ln.style || 'normal' }));
        if (first === null) first = [...miss];
        let run = '';
        for (const ch of ln.text) {
          if (miss.has(ch)) { if (run) t.append(run); run = ''; mk('span', 'm', t).textContent = ch; } else run += ch;
        }
        if (run) t.append(run);
      }
      if (first && first.length) { mk('div', 'miss', meta).textContent = `缺 ${first.length} 字：${first.join('')}（红字是后备字体）`; res.missing[r.family] = first.join(''); }
    }
  }
  window.SPEC_RESULT = res;
  window.T3_READY = true;
})();
"""

NODE_SHOT = r"""
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const cfg = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
const { openPage } = await import(pathToFileURL(cfg.cdp).href);
const pg = await openPage(cfg.html, { width: cfg.width, height: 1000, settle: 300 });
for (let i = 0; i < 600 && !(await pg.evaluate('window.T3_READY === true')); i++) await new Promise((r) => setTimeout(r, 200));
const info = JSON.parse(await pg.evaluate('JSON.stringify(window.SPEC_RESULT || null)'));
const rects = JSON.parse(await pg.evaluate("JSON.stringify([...document.querySelectorAll('section[data-out]')].map((s) => { const r = s.getBoundingClientRect(); return { out: s.dataset.out, x: r.left + scrollX, y: r.top + scrollY, w: Math.ceil(r.width), h: Math.ceil(r.height) }; }))"));
const shots = [];
for (const r of rects) {
  const res = await pg.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: r.x, y: r.y, width: r.w, height: r.h, scale: 1 } });
  fs.writeFileSync(r.out, Buffer.from(res.data, 'base64'));
  shots.push([r.out, r.w, r.h]);
}
const errors = [...new Set(pg.errors)];
await pg.close();
console.log('@@RESULT@@' + JSON.stringify({ info, shots, errors }));
"""


def sample_kind(e):
    c = e['faces'][0]['cov']
    if e['group'] == 'jp-display':
        return 'jp'
    if e['group'].startswith('cjk') or c['gb1'] >= 2500:
        return 'zh'
    if c['kana'] >= 150:
        return 'jp'
    if c['big5'] >= 2500:
        return 'tc'
    if c['latin'] < 40 and c['digits'] >= 10:
        return 'digits'
    return 'latin'


def near_weight(e, target, style='normal'):
    faces = [f for f in e['faces'] if f['style'] == style] or e['faces']
    best = None
    for f in faces:
        lo, hi = wrange(f['weight'])
        w = min(max(target, lo), hi)
        if best is None or abs(w - target) < abs(best - target):
            best = w
    return int(best)


def spec_row(e, text=None):
    big, small = (text, text) if text else SAMPLES[sample_kind(e)]
    wb, wr = near_weight(e, 900 if not text else 700), near_weight(e, 400)
    lines = [{'text': big, 'size': 84 if text else 72, 'weight': wb}]
    if not text or wr != wb:
        lines.append({'text': small, 'size': 40 if text else 30, 'weight': wr})
    if not text:
        extra = [(t, v) for t, v in e['axes'].items() if t not in ('wght', 'ital', 'slnt', 'opsz')][:2]
        for t, (lo, _de, hi) in extra:
            v = lo if t == 'wdth' else hi
            lines.append({'text': big, 'size': 48, 'weight': wb, 'vs': f"'{t}' {v:g}", 'label': f'{t} {v:g}'})
        if 'italic' in e['styles'] and 'normal' in e['styles']:
            lines.append({'text': small, 'size': 30, 'weight': near_weight(e, 400, 'italic'), 'style': 'italic', 'label': 'italic'})
    esc = html.escape
    meta = (f"<b>{esc(e['family'])}</b><div>{esc(GROUP_ZH.get(e['group'], e['group']))} · {esc(e['weights'])}"
            + (f" · {esc(e['color'])}" if e.get('color') else '') + '</div>'
            + f"<div>{esc('、'.join(e['scripts']))}" + (f"（汉字 {e['hanzi']}）" if e['hanzi'] else '') + '</div>'
            + f"<div>{esc(e['license'])} · {esc('、'.join(e['designers'])[:70])}</div>"
            + f"<div>{len(e['faces'])} 个文件 · {fmt_mb(e['bytes'])}</div>")
    faces = [{'url': file_url(os.path.join(LIB, f['file'])), 'weight': f['weight'], 'style': f['style'],
              **({'stretch': f['stretch']} if f.get('stretch') else {})} for f in e['faces']]
    return {'family': e['family'], 'alias': 'spec-' + e['slug'], 'faces': faces, 'meta': meta, 'lines': lines}


def safe_file(s):
    return re.sub(r'[<>:"/\\|?*\s]+', '_', s).strip('_')[:40] or 'text'


def cmd_specimen(a):
    cat = load_catalog()
    fams = list(cat['families'].values())
    if not fams:
        raise SystemExit(f'库是空的：先 fonts.py get starter（库在 {LIB}）')
    if a.all and not (a.family or a.text):
        return specimen_all(cat, a)
    if a.family:
        want = [x.strip().lower() for x in a.family.split(',') if x.strip()]
        fams = [e for e in fams if e['family'].lower() in want or e['slug'] in want]
        if not fams:
            raise SystemExit('库里没有这些家族：' + a.family)
    elif not a.all:              # the curated shelf, as specimen\<group>.png always was; --all widens --text to everything
        fams = [e for e in fams if is_curated(e)]
    if a.group:
        gs = [x.strip() for x in a.group.split(',')]
        fams = [e for e in fams if e['group'] in gs]
        if not fams:
            raise SystemExit(f'精选架的 {a.group} 组里没有家族：全量分页样张用 fonts.py specimen --all --group {a.group}')
    os.makedirs(SPECIMEN, exist_ok=True)
    sections = []
    esc = html.escape
    if a.text:
        if not (a.family or a.group):     # all library fonts that can set at least most of the text
            chars = [c for c in dict.fromkeys(a.text) if not c.isspace()]
            fams = [e for e in fams if len(family_missing(e, a.text)) <= len(chars) // 2]
            if not a.all:
                more = sum(1 for e in cat['families'].values() if not is_curated(e)
                           and len(family_missing(e, a.text)) <= len(chars) // 2)
                if more:
                    say(f'  这里只画精选架的 {len(fams)} 个；全量里还有 {more} 个也能排这段字：加 --all（或 --group 缩小范围）')
        fams.sort(key=lambda e: (len(family_missing(e, a.text)), gkey(e)))
        base = a.out or os.path.join(SPECIMEN, 'text_' + safe_file(a.text) + '.png')
        parts = [fams[i:i + 12] for i in range(0, len(fams), 12)]
        for i, part in enumerate(parts):
            out = base if len(parts) == 1 else re.sub(r'(\.png)?$', f'_{i + 1}.png', base, count=1)
            head = f'<h1>「{esc(a.text)}」<small>{len(fams)} 个字体{f"（第 {i + 1}/{len(parts)} 张）" if len(parts) > 1 else ""} · 红字 = 这个字体缺这个字，显示的是后备字体</small></h1>'
            sections.append({'out': out, 'head': head, 'rows': [spec_row(e, a.text) for e in part]})
    elif a.family:      # its own file: with two thousand families in the library this must never replace a group sheet
        fams.sort(key=gkey)
        base = a.out or os.path.join(SPECIMEN, 'family_' + safe_file(','.join(e['family'] for e in fams)) + '.png')
        parts = [fams[i:i + 12] for i in range(0, len(fams), 12)]
        for i, part in enumerate(parts):
            out = base if len(parts) == 1 else re.sub(r'(\.png)?$', f'_{i + 1}.png', base, count=1)
            head = (f'<h1>{esc("、".join(e["family"] for e in part))}<small>{len(fams)} 个家族' +
                    (f'（第 {i + 1}/{len(parts)} 张）' if len(parts) > 1 else '') + ' · 红字 = 缺字（显示的是后备字体）</small></h1>')
            sections.append({'out': out, 'head': head, 'rows': [spec_row(e) for e in part]})
    else:
        by = {}
        for e in fams:
            by.setdefault(e['group'], []).append(e)
        for g in GROUP_ORDER:
            if g not in by:
                continue
            rows = sorted(by[g], key=lambda e: e['family'].lower())
            parts = [rows[i:i + 12] for i in range(0, len(rows), 12)]
            for i, part in enumerate(parts):
                name = g if len(parts) == 1 else f'{g}_{i + 1}'
                out = a.out if (a.out and len(by) == 1 and len(parts) == 1) else os.path.join(SPECIMEN, name + '.png')
                head = f'<h1>{esc(GROUP_ZH[g])} {g}<small>{len(rows)} 个家族 · 库 {esc(LIB)} · 红字 = 缺字（显示的是后备字体）</small></h1>'
                sections.append({'out': out, 'head': head, 'rows': [spec_row(e) for e in part]})
    for s in sections:
        os.makedirs(os.path.dirname(os.path.abspath(s['out'])), exist_ok=True)
        s['out'] = os.path.abspath(s['out'])
    page = os.path.join(SPECIMEN, '_specimen_page.html')
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>' + SPEC_CSS + '</style>'
           '<script>window.__H = []; window.T3 = { seek() {}, hold(p) { window.__H.push(p); return p; } };</script>'
           f'<script src="{file_url(LIB_JS)}"></script>'
           '<script>window.SPEC = ' + json.dumps({'sections': sections}, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
           '</head><body><script>' + SPEC_JS + '</script></body></html>')
    write_atomic(page, doc)
    cfgp = os.path.join(SPECIMEN, '_specimen_job.json')
    write_atomic(cfgp, json.dumps({'cdp': CDP, 'html': page, 'width': 1800}))
    t0 = time.time()
    with run_queue().slot('web', 'fonts.py specimen', say=say) as s:
        r = s.run([shutil.which('node') or 'node', '--input-type=module', '-e', NODE_SHOT, cfgp], timeout=900)
    line = next((x for x in r.stdout.splitlines() if x.startswith('@@RESULT@@')), None)
    if not line:
        raise SystemExit('出样张失败：\n' + r.stdout[-2000:] + r.stderr[-2000:])
    res = json.loads(line[len('@@RESULT@@'):])
    for out, w, h in res['shots']:
        say(f'  {out}  {w}×{h}')
    info = res.get('info') or {}
    if info.get('failed'):
        say('  加载失败：' + '、'.join(info['failed']))
    if a.text and info.get('missing'):
        ok = [e['family'] for e in fams if e['family'] not in info['missing']]
        say(f'  「{a.text}」不缺字的：' + ('、'.join(ok) or '（没有）'))
    errs = [x for x in res.get('errors') or [] if 'T3.fonts.use' not in x]
    if errs:
        say('  页面报错：\n    ' + '\n    '.join(errs[:10]))
    say(f'{len(res["shots"])} 张样张，{sum(len(s["rows"]) for s in sections)} 行，用时 {time.time() - t0:.0f}s')
    idx_save()
    return 1 if info.get('failed') or errs else 0


# ------------------------------------------------------------------------------------------------ specimen --all (sheets)
SPEC_ALL_CSS = """
html,body{margin:0;background:#0f1117;width:1800px}
section{width:1800px;box-sizing:border-box;padding:22px 30px 24px;background:#0f1117;color:#e8eaf0;font-family:'Microsoft YaHei','Segoe UI',sans-serif}
h1{margin:0 0 10px;font-size:28px;color:#ffd84a;font-weight:700}h1 small{margin-left:14px;font-size:16px;color:#8f97aa;font-weight:400}
.row{display:flex;align-items:center;border-top:1px solid #262b38;padding:7px 0 6px;min-height:60px}
.meta{width:420px;flex:none;padding-right:18px;font-size:13px;line-height:1.42;color:#98a1b4;overflow:hidden;white-space:nowrap}
.meta b{display:block;font-size:20px;line-height:1.3;color:#fff;overflow:hidden;text-overflow:ellipsis}
.meta b i{font-style:normal;color:#ffd84a;margin-right:6px}.meta .bad{color:#ff5d5d}
.s{flex:1;min-width:0;overflow:hidden}.ln{white-space:nowrap;line-height:1.28;color:#fff}
.ln2{white-space:nowrap;line-height:1.3;color:#aab3c5;margin-top:1px}.m{color:#ff4d4d}
"""

SPEC_ALL_JS = r"""
(async function () {
  const S = window.SPEC, mk = (t, c, p) => { const e = document.createElement(t); if (c) e.className = c; p.appendChild(e); return e; };
  for (const r of S.rows) for (const f of r.faces) T3.fonts.add(Object.assign({ family: r.alias, name: r.family }, f));
  await Promise.allSettled(window.__H);
  await document.fonts.ready;
  const st = {};
  for (const x of T3.fonts.report()) (st[x.family] = st[x.family] || []).push(x.status);
  const res = { failed: [], tall: [] }, el = mk('section', '', document.body), cx = document.createElement('canvas').getContext('2d');
  el.innerHTML = S.head;
  for (const r of S.rows) {
    const row = mk('div', 'row', el), meta = mk('div', 'meta', row), s = mk('div', 's', row);
    meta.innerHTML = r.meta;
    const ok = (st[r.alias] || []).length && st[r.alias].every((x) => x === 'loaded');
    if (!ok) { res.failed.push(r.family); mk('div', 'bad', meta).textContent = '加载失败：' + (st[r.alias] || ['?']).join(','); }
    r.lines.forEach((ln, i) => {
      const d = mk('div', i ? 'ln2' : 'ln', s), miss = new Set(ln.miss);
      d.style.cssText = `font-family:'${r.alias}',monospace;font-size:${ln.size}px;font-weight:${ln.weight};font-style:${ln.style}`;
      let run = '';
      for (const ch of ln.text) { if (miss.has(ch)) { if (run) d.append(run); run = ''; mk('span', 'm', d).textContent = ch; } else run += ch; }
      if (run) d.append(run);
      // a font whose ascent / descent sit oddly (Noto Sans Siddham, Nastaliq, stacked Indic marks…) puts the ink outside the
      // fixed line height, where .s clips it or the next line covers it: pad that line by the overshoot. Under 1 px is
      // anti-aliasing, not worth a taller row; lines that fit keep their layout.
      cx.font = `${ln.style} ${ln.weight} ${ln.size}px '${r.alias}', monospace`;
      const m = cx.measureText(ln.text), lh = parseFloat(getComputedStyle(d).lineHeight);
      const base = (lh - m.fontBoundingBoxAscent - m.fontBoundingBoxDescent) / 2 + m.fontBoundingBoxAscent;
      const up = m.actualBoundingBoxAscent - base, down = base + m.actualBoundingBoxDescent - lh;
      if (up > 1) d.style.paddingTop = Math.ceil(up + 1) + 'px';
      if (down > 1) d.style.paddingBottom = Math.ceil(down + 1) + 'px';
      if ((up > 1 || down > 1) && !res.tall.includes(r.family)) res.tall.push(r.family);
    });
  }
  window.SPEC_RESULT = res;
  window.T3_READY = true;
})();
"""

NODE_SHOT_ALL = r"""
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const cfg = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
const { openPage, sleep } = await import(pathToFileURL(cfg.cdp).href);
const url = (p) => 'file:///' + p.replace(/\\/g, '/');
const pg = await openPage(cfg.jobs[0].html, { width: cfg.width, height: 1000, settle: 100 });
for (let j = 0; j < cfg.jobs.length; j++) {
  const job = cfg.jobs[j], e0 = pg.errors.length, t0 = Date.now();
  if (j > 0) {
    await pg.evaluate('window.T3_READY = false');
    await pg.send('Page.navigate', { url: url(job.html) });
  }
  let ready = false;
  for (let i = 0; i < 1200 && !ready; i++) {
    ready = await pg.evaluate(`window.T3_READY === true && document.readyState === 'complete' && location.pathname.endsWith(${JSON.stringify('/' + job.html.split(/[\\/]/).pop())})`).catch(() => false);
    if (!ready) await sleep(100);
  }
  const info = JSON.parse(await pg.evaluate('JSON.stringify(window.SPEC_RESULT || null)'));
  const r = JSON.parse(await pg.evaluate("JSON.stringify((() => { const s = document.querySelector('section'); if (!s) return null; const b = s.getBoundingClientRect(); return { x: b.left + scrollX, y: b.top + scrollY, w: Math.ceil(b.width), h: Math.ceil(b.height) }; })())"));
  if (r) {
    const res = await pg.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: r.x, y: r.y, width: r.w, height: r.h, scale: 1 } });
    fs.writeFileSync(job.out, Buffer.from(res.data, 'base64'));
  }
  console.log('@@SHEET@@' + JSON.stringify({ out: job.out, ready, info, w: r && r.w, h: r && r.h, ms: Date.now() - t0, errors: [...new Set(pg.errors.slice(e0))] }));
}
await pg.close();
console.log('@@DONE@@');
"""

ALL_SAMPLES = {'latin': 'The Quick Brown Fox Jumps Over the Lazy Dog 0123456789',
               'zh': '排行榜第一名 谁最强 数据雷达 综合得分 98.7', 'tc': '排行榜第一名 誰最強 數據雷達 綜合得分 98.7',
               'jp': '最強ランキング 第一位 ひらがな カタカナ 漢字', 'ko': '최강 랭킹 제1위 데이터 레이더 종합 점수',
               'digits': '88:88 98.7 -1234.5 0123456789'}
# main letters of a script (ISO 15924, Google's primaryScript) → where to take a sample from the font itself
SCRIPT_BLOCK = {'Arab': (0x0620, 0x064A), 'Hebr': (0x05D0, 0x05EA), 'Deva': (0x0904, 0x0939), 'Beng': (0x0985, 0x09B9),
                'Guru': (0x0A05, 0x0A39), 'Gujr': (0x0A85, 0x0AB9), 'Orya': (0x0B05, 0x0B39), 'Taml': (0x0B85, 0x0BB9),
                'Telu': (0x0C05, 0x0C39), 'Knda': (0x0C85, 0x0CB9), 'Mlym': (0x0D05, 0x0D3A), 'Sinh': (0x0D85, 0x0DC6),
                'Thai': (0x0E01, 0x0E2E), 'Laoo': (0x0E81, 0x0EAE), 'Tibt': (0x0F40, 0x0F6C), 'Mymr': (0x1000, 0x102A),
                'Geor': (0x10D0, 0x10FA), 'Ethi': (0x1200, 0x135A), 'Khmr': (0x1780, 0x17B3), 'Cyrl': (0x0410, 0x044F),
                'Grek': (0x0391, 0x03C9), 'Armn': (0x0531, 0x0586), 'Thaa': (0x0780, 0x07A5), 'Syrc': (0x0710, 0x072F),
                'Cher': (0x13A0, 0x13F5), 'Cans': (0x1401, 0x166C), 'Tfng': (0x2D30, 0x2D67), 'Mong': (0x1820, 0x1878)}
SKIP_BLOCKS = ((0, 0x36F), (0x1E00, 0x1EFF), (0x2000, 0x2BFF), (0x2E80, 0x9FFF), (0xAC00, 0xDFFF), (0xE000, 0xF8FF),
               (0xFB00, 0xFFFF), (0xF0000, 0x10FFFF))


def iter_cps(r, lo=0, hi=0x10FFFF, cap=20000):
    n = 0
    for s, t in zip(*r):
        for c in range(max(s, lo), min(t, hi) + 1):
            yield c
            n += 1
            if n >= cap:
                return


def own_sample(r, ps, n=30):
    """a run of the font's own letters: its main script's block, else its densest block outside Latin / CJK / symbols."""
    if ps in SCRIPT_BLOCK:
        cps = list(iter_cps(r, *SCRIPT_BLOCK[ps]))
    else:
        cps = []
    if len(cps) < 6:
        blocks = {}
        for c in iter_cps(r):
            if not any(a <= c <= b for a, b in SKIP_BLOCKS):
                blocks.setdefault(c >> 7, []).append(c)
        cps = max(blocks.values(), key=len) if blocks else [c for c in iter_cps(r, 0x21, 0x10FFFF, 200)]
    letters = [c for c in cps if unicodedata.category(chr(c))[0] == 'L'] or \
        [c for c in cps if unicodedata.category(chr(c))[0] not in 'ZCM'] or \
        [c for c in cps if c > 0x20]    # scripts newer than this Python's Unicode tables (Todhri, Sunuwar…) read as unassigned
    letters = letters[:n]
    return ' '.join(''.join(chr(c) for c in letters[i:i + 6]) for i in range(0, len(letters), 6))


def sheet_face(e):
    """the face a sheet row is drawn with: upright, nearest to 400 (one face per family keeps a sheet light)."""
    faces = [f for f in e['faces'] if f['style'] == 'normal'] or e['faces']

    def dist(f):
        lo, hi = wrange(f['weight'])
        return abs(min(max(400, lo), hi) - 400)
    f = min(faces, key=dist)
    lo, hi = wrange(f['weight'])
    return f, int(min(max(400, lo), hi))


def all_row(e):
    face, w = sheet_face(e)
    r = face_ranges(face['file'])
    c, ps = face['cov'], gf_info(e)[2]
    latin = c['latin'] >= 40
    other_ps = bool(ps) and ps not in ('Latn', 'Hans', 'Hant', 'Jpan', 'Hira', 'Kore')   # Google's main script: not Latin / CJK
    if e['group'] == 'jp-display':
        kind = 'jp'
    elif e['group'].startswith('cjk'):
        kind = 'zh' if c['gb1'] >= 3740 or (c['gb1'] >= 2500 and c['big5'] < 5000) else 'tc'
    elif c['hangul'] >= 2000:
        kind = 'ko'
    elif c['kana'] >= 150:
        kind = 'jp'
    elif c['gb1'] >= 2500:
        kind = 'zh'
    elif c['big5'] >= 2500:
        kind = 'tc'
    elif c['latin'] >= 60:      # a full Latin set: the English line on top even when Google files it under another script
        kind = 'latin'          # (Poppins, Kanit, Cairo, Rajdhani — designers set them in Latin as often as not)
    elif other_ps:
        kind = 'own'
    elif latin:
        kind = 'latin'
    elif c['digits'] >= 10 and not e.get('color'):
        kind = 'digits'
    else:
        kind = 'own'
    first = own_sample(r, ps) if kind == 'own' else ALL_SAMPLES[kind]
    texts = [(first, 44 if kind in ('latin', 'digits') else 40)]
    if kind not in ('latin', 'digits') and latin:
        texts.append((ALL_SAMPLES['latin'], 22))
    elif kind == 'latin' and other_ps:          # …and a line of its own script under it
        own = own_sample(r, ps)
        if any(not any(a <= ord(ch) <= b for a, b in SKIP_BLOCKS) for ch in own if not ch.isspace()):   # not Latin again
            texts.append((own, 24))
    style = face['style']
    lines = [{'text': t, 'size': s, 'weight': w, 'style': style,
              'miss': [ch for ch in dict.fromkeys(t) if not ch.isspace() and not has_cp(r, ord(ch))]} for t, s in texts]
    pop = gf_info(e)[0]
    esc = html.escape
    meta = (f"<b>{'<i>★</i>' if is_curated(e) else ''}{esc(e['family'])}</b>"
            f"<div>{f'热度 #{pop} · ' if pop < 9999 else ''}{esc(e.get('category') or GROUP_ZH.get(e['group'], ''))} · {esc(e['weights'])}"
            + (f" · {esc(e['color'])}" if e.get('color') else '') + '</div>'
            f"<div>{esc(scripts_short(e))}</div>")
    f = {'url': file_url(os.path.join(LIB, face['file'])), 'weight': face['weight'], 'style': style,
         **({'stretch': face['stretch']} if face.get('stretch') else {})}
    return {'family': e['family'], 'alias': 'spec-' + e['slug'], 'faces': [f], 'meta': meta, 'lines': lines}


def specimen_all(cat, a):
    per = max(5, min(a.per_page or SPEC_PER_PAGE, 80))
    order = all_order(cat)
    pages, counts = sheet_names(order, per)
    gs = [x.strip() for x in a.group.split(',')] if a.group else list(order)
    bad = [g for g in gs if g not in order]
    if bad:
        raise SystemExit(f'库里没有这些风格组：{", ".join(bad)}；有：{", ".join(order)}')
    work = os.path.join(SPECIMEN_ALL, '_work')
    os.makedirs(work, exist_ok=True)
    esc = html.escape
    jobs = []
    for g in gs:
        es, n = order[g], counts[g]
        for i in range(n):
            part = es[i * per:(i + 1) * per]
            name = f'{g}_{i + 1:02d}'
            head = (f'<h1>{esc(GROUP_ZH.get(g, g))} {g} · 第 {i + 1}/{n} 张<small>本组 {len(es)} 个家族里的第 {i * per + 1}–'
                    f'{i * per + len(part)} 个 · ★ = 精选架（catalog.md 有用法） · 其余按 Google 热度排 · 红字 = 缺字</small></h1>')
            spec = {'head': head, 'rows': [all_row(e) for e in part]}
            page = os.path.join(work, name + '.html')
            write_atomic(page, '<!doctype html><html><head><meta charset="utf-8"><style>' + SPEC_ALL_CSS + '</style>'
                         '<script>window.__H = []; window.T3 = { seek() {}, hold(p) { window.__H.push(p); return p; } };</script>'
                         f'<script src="{file_url(LIB_JS)}"></script>'
                         '<script>window.SPEC = ' + json.dumps(spec, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
                         '</head><body><script>' + SPEC_ALL_JS + '</script></body></html>')
            jobs.append({'html': page, 'out': os.path.join(SPECIMEN_ALL, name + '.png'), 'name': name, 'n': len(part)})
    idx_save()
    cfgp = os.path.join(work, '_job.json')
    write_atomic(cfgp, json.dumps({'cdp': CDP, 'width': 1800, 'jobs': jobs}))
    say(f'全量样张：{len(gs)} 个风格组、{len(jobs)} 张（每张最多 {per} 个家族）→ {SPECIMEN_ALL}')
    t0 = time.time()
    done, failed, errs, tall, k = [], [], [], [], 0
    with run_queue().slot('web', 'fonts.py specimen all', say=say) as s:
        p = s.popen([shutil.which('node') or 'node', '--input-type=module', '-e', NODE_SHOT_ALL, cfgp],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        for line in p.stdout:
            if not line.startswith('@@SHEET@@'):
                continue
            x = json.loads(line[len('@@SHEET@@'):])
            k += 1
            nf = (x.get('info') or {}).get('failed') or []
            failed += nf
            tall += (x.get('info') or {}).get('tall') or []
            errs += [m for m in x.get('errors') or [] if 'T3.fonts.use' not in m]
            if x.get('ready') and x.get('h'):
                done.append(os.path.basename(x['out'])[:-4])
            say(f"  [{k:>3}/{len(jobs)}] {x['out']}  {x.get('w')}×{x.get('h')}  {x['ms'] / 1000:.1f}s" +
                ('' if x.get('ready') else '  ！没等到页面画完') + (f"  加载失败：{'、'.join(nf)}" if nf else ''))
        p.wait()
    if p.returncode:
        say('  出图进程报错：' + (p.stderr.read() or '')[-1500:])
    for g in gs:                                   # a group that shrank leaves no stale last sheets behind
        for fn in os.listdir(SPECIMEN_ALL):
            m = re.fullmatch(re.escape(g) + r'_(\d+)\.png', fn)
            if m and int(m.group(1)) > counts[g]:
                os.remove(os.path.join(SPECIMEN_ALL, fn))
    old = load_pages().get('pages') or {}
    keep = {f: s for f, s in old.items() if f in pages and s.rsplit('_', 1)[0] not in gs}
    keep.update({f: s for f, s in pages.items() if s in done})
    write_atomic(SPEC_PAGES, json.dumps({'rendered': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'per_page': per,
                                         'pages': keep}, ensure_ascii=False, indent=0))
    if p.returncode == 0 and len(done) == len(jobs):
        shutil.rmtree(work, ignore_errors=True)
    write_md(cat)
    say(f'{len(done)}/{len(jobs)} 张，用时 {hms(time.time() - t0)}；页码已写进 {CATALOG_ALL_MD}')
    if tall:
        say(f'  {len(tall)} 个家族的字形高出行高（字体的上下边距特殊），这几行已加高、字没被裁：' + '、'.join(tall[:12]) +
            ('…' if len(tall) > 12 else ''))
    if failed:
        say(f'  加载失败的家族 {len(failed)} 个：' + '、'.join(failed))
    if errs:
        say('  页面报错：\n    ' + '\n    '.join(list(dict.fromkeys(errs))[:10]))
    return 1 if failed or errs or len(done) < len(jobs) else 0


# --------------------------------------------------------------------------------------------------------------- main
def main(argv=None):
    p = argparse.ArgumentParser(prog='fonts.py', description='字体库：search / get / use / specimen / credits / groups / catalog',
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest='cmd')
    s = sub.add_parser('search', help='搜在线目录（--local 搜库里）')
    s.add_argument('words', nargs='*')
    s.add_argument('--group')
    s.add_argument('--cat')
    s.add_argument('--script')
    s.add_argument('--tag')
    s.add_argument('--var', action='store_true')
    s.add_argument('--color', action='store_true')
    s.add_argument('--local', action='store_true')
    s.add_argument('--text')
    s.add_argument('-n', type=int)
    s.add_argument('--refresh', action='store_true')
    g = sub.add_parser('get', help='下载入库')
    g.add_argument('targets', nargs='*')
    g.add_argument('--group')
    g.add_argument('--fits')
    g.add_argument('--pick')
    g.add_argument('--force', action='store_true')
    g.add_argument('--url')
    g.add_argument('--family')
    g.add_argument('--license')
    g.add_argument('--license-url')
    g.add_argument('--designers')
    g.add_argument('--designers-en')
    g.add_argument('--home')
    g.add_argument('--all-google', action='store_true')
    g.add_argument('--jobs', type=int)
    g.add_argument('--retries', type=int)
    g.add_argument('--limit', type=int)
    g.add_argument('--estimate', action='store_true')
    u = sub.add_parser('use', help='放进项目')
    u.add_argument('project')
    u.add_argument('families', nargs='*')
    u.add_argument('--full', action='store_true')
    u.add_argument('--subset', action='store_true')
    u.add_argument('--static', action='store_true')
    u.add_argument('--alias')
    u.add_argument('--text')
    u.add_argument('--remove', action='append')
    u.add_argument('--check', action='store_true')
    sp = sub.add_parser('specimen', help='样张 PNG')
    sp.add_argument('--group')
    sp.add_argument('--family')
    sp.add_argument('--text')
    sp.add_argument('--out')
    sp.add_argument('--all', action='store_true')
    sp.add_argument('--per-page', type=int)
    c = sub.add_parser('credits', help='片尾鸣谢')
    c.add_argument('project')
    sub.add_parser('groups', help='风格组一览')
    ca = sub.add_parser('catalog', help='重写 catalog.md')
    ca.add_argument('--rescan', action='store_true')
    a = p.parse_args(argv)
    if not a.cmd:
        say(__doc__)
        return 0
    return {'search': cmd_search, 'get': cmd_get, 'use': cmd_use, 'specimen': cmd_specimen, 'credits': cmd_credits,
            'groups': cmd_groups, 'catalog': cmd_catalog}[a.cmd](a) or 0


if __name__ == '__main__':
    sys.exit(main())
