# 字体库全量索引

> 由 `fonts.py` 自动生成（2026-11-23 19:09），不要手改。精选架（★）的用法说明、授权、作者和文件在 `catalog.md`。

共 **59 个家族**（★ 精选架 59 个），按风格组分节；每组精选在前，其余按 Google Fonts 热度排（越靠前越常用）。「样张」一栏是这个家族在 `specimen\all\` 里的那一张，每张 40 个家族、字名写在左边。还没出全量样张：`fonts.py specimen --all`。

找字：Ctrl+F 搜家族名或官方风格标签（英文，见下表）；命令行 `fonts.py search --local --tag Techno --script latin`（--tag 也认中文名：`--tag 科技`），`--text "谁最强"` 按缺字多少排。用：`fonts.py use <项目> "家族名"`；描边、空心字 `fonts.py use <项目> "家族名:900" --static`。

各栏：**官方风格标签** = Google Fonts 的分类（Sans Serif / Serif / Display / Handwriting / Monospace）+ 分数 ≥ 60 的风格标签（只写最后一段，/Sans/Geometric → Geometric），最多 5 个；**文字集**：拉丁、简中、繁中、日文、韩文按字体里实际有的字算（简中 = GB2312 一级字齐全，缺字 = 只有一部分），其余按 Google 的子集；**字重 / 可变**：「100–900 可变」= 一个可变字体文件包含这个范围的所有字重，其余轴（wdth 宽度、opsz 光学尺寸、slnt 倾斜…）用 `font-variation-settings` 调。

标签对照：Business 商务，Competent 稳重，Calm 平静，Sincere 真诚，Vintage 复古，Loud 张扬，Rugged 粗犷，Childlike 童趣，Awkward 笨拙，Artistic 艺术，Stiff 板正，Playful 俏皮，Futuristic 未来感，Happy 欢快，Excited 兴奋，Active 动感，Innovative 新颖，Fancy 华丽，Cute 可爱，Sophisticated 精致，Humanist 人文，Geometric 几何，Neo Grotesque 新怪诞，Grotesque 怪诞，Rounded 圆体，Superellipse 方圆，Glyphic 碑刻，Transitional 过渡衬线，Old Style Garalde 旧式衬线，Modern 现代衬线，Didone 迪多衬线，Scotch 苏格兰衬线，Fat Face 胖脸衬线，Humanist Venetian 威尼斯人文衬线，Clarendon 克拉伦登粗衬线，Handwritten 手写，Informal 随手写，Upright Script 直立手写，Formal 正式花体，Monospace 等宽，Brush 笔刷，Techno 科技，Wacky 古怪，Pixel 像素，Distressed 做旧，Woodtype 木活字，Blobby 圆滚，Blackletter 哥特，Stencil 模板，Medieval 中世纪，Shaded 阴影，Inline 内线，Art Deco 装饰艺术，Tuscan 托斯卡纳，Art Nouveau 新艺术，Valentine's Day 情人节，Holi 洒红节，Diwali 排灯节，Lunar New Year 春节，Kwanzaa 宽扎节，Halloween 万圣节，Christmas 圣诞，Hanukkah 光明节，Learn To Write 习字，Easy Reading 易读，Symbols 符号，Barcode 条码，Redaction 涂黑。

[哥特黑体 5](#blackletter) · [高反差 / 古典衬线 6](#didone) · [窄体粗黑 5](#condensed) · [科技 / 科幻 5](#tech) · [像素 / 点阵 / 数码管 8](#pixel) · [等宽 / 代码 4](#mono) · [笔刷 / 马克笔 / 涂鸦 3](#brush) · [花体 / 连笔手写 2](#script) · [模板字 3](#stencil) · [装饰 / 特效字 6](#decorative) · [中文黑体 2](#cjk-sans) · [中文宋体 / 仿宋 2](#cjk-serif) · [中文书法 / 手写 2](#cjk-calligraphy) · [中文创意标题 3](#cjk-display) · [日文标题 3](#jp-display)

<a id="blackletter"></a>

## 哥特黑体（blackletter）

5 个家族 · 样张 `specimen\all\blackletter_01.png` · 精选架样张 `specimen\blackletter.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Chomsky** | — | 拉丁 | 400 | blackletter_01 |
| ★ **Grenze Gotisch** | Display · Blackletter、Artistic、Loud、Rugged、Stiff | 拉丁 | 100–900 可变 | blackletter_01 |
| ★ **Pirata One** | Display · Blackletter、Artistic、Vintage | 拉丁 | 400 | blackletter_01 |
| ★ **UnifrakturCook** | Display · Blackletter、Artistic、Rugged、Vintage | 拉丁 | 700 | blackletter_01 |
| ★ **UnifrakturMaguntia** | Display · Blackletter、Artistic、Rugged、Sincere、Vintage | 拉丁 | 400 | blackletter_01 |

<a id="didone"></a>

## 高反差 / 古典衬线（didone）

6 个家族 · 样张 `specimen\all\didone_01.png` · 精选架样张 `specimen\didone.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Abril Fatface** | Display · Fat Face、Modern、Loud、Rugged、Vintage | 拉丁 | 400 | didone_01 |
| ★ **Bodoni Moda** | Serif · Didone、Modern、Business、Fancy、Sincere | 拉丁 | 400–900 可变 · 带斜体；opsz 6–96 | didone_01 |
| ★ **Cinzel** | Serif · Old Style Garalde、Competent、Fancy、Loud、Vintage | 拉丁 | 400–900 可变 | didone_01 |
| ★ **Cormorant Garamond** | Serif · Old Style Garalde、Business、Competent、Fancy、Sincere | 拉丁 | 300–700 可变 · 带斜体 | didone_01 |
| ★ **Instrument Serif** | Serif · Modern、Scotch、Sincere、Vintage | 拉丁 | 400 · 带斜体 | didone_01 |
| ★ **Playfair Display** | Serif · Didone、Business、Calm、Competent、Fancy | 拉丁 | 400–900 可变 · 带斜体 | didone_01 |

<a id="condensed"></a>

## 窄体粗黑（condensed）

5 个家族 · 样张 `specimen\all\condensed_01.png` · 精选架样张 `specimen\condensed.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Anton** | Sans Serif · Neo Grotesque、Loud、Rugged | 拉丁 | 400 | condensed_01 |
| ★ **Bebas Neue** | Sans Serif · Neo Grotesque、Rugged | 拉丁 | 400 | condensed_01 |
| ★ **Big Shoulders** | Display · Calm、Loud、Rugged、Stiff | 拉丁 | 100–900 可变；opsz 10–72 | condensed_01 |
| ★ **League Gothic** | Sans Serif · Grotesque、Superellipse、Rugged | 拉丁 | 400；wdth 75–100 | condensed_01 |
| ★ **Oswald** | Sans Serif · Grotesque、Business、Competent、Rugged、Stiff | 拉丁 | 200–700 可变 | condensed_01 |

<a id="tech"></a>

## 科技 / 科幻（tech）

5 个家族 · 样张 `specimen\all\tech_01.png` · 精选架样张 `specimen\tech.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Chakra Petch** | Sans Serif · Techno、Futuristic、Stiff、Vintage | 拉丁 | 300, 400, 500, 600, 700 · 带斜体 | tech_01 |
| ★ **Michroma** | Sans Serif · Techno、Superellipse、Futuristic、Rugged、Stiff | 拉丁 | 400 | tech_01 |
| ★ **Orbitron** | Sans Serif · Techno、Futuristic、Loud、Rugged、Stiff | 拉丁 | 400–900 可变 | tech_01 |
| ★ **Oxanium** | Display · Techno、Superellipse、Futuristic、Stiff | 拉丁 | 200–800 可变 | tech_01 |
| ★ **Rajdhani** | Sans Serif · Superellipse、Calm、Futuristic、Stiff | 拉丁 | 300, 400, 500, 600, 700 | tech_01 |

<a id="pixel"></a>

## 像素 / 点阵 / 数码管（pixel）

8 个家族 · 样张 `specimen\all\pixel_01.png` · 精选架样张 `specimen\pixel.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Doto** | Sans Serif · Pixel、Monospace、Playful | 拉丁 | 100–900 可变；ROND 0–100 | pixel_01 |
| ★ **DSEG7 Classic** | other | 拉丁 | 300, 400, 700 · 带斜体 | pixel_01 |
| ★ **Fusion Pixel 12px Proportional SC** | sans-serif | 简中、繁中、日文、韩文、拉丁 | 400 | pixel_01 |
| ★ **Jacquard 24** | Display · Medieval、Pixel、Awkward、Vintage | 拉丁 | 400 | pixel_01 |
| ★ **Press Start 2P** | Display · Pixel、Techno、Awkward、Vintage | 拉丁 | 400 | pixel_01 |
| ★ **Silkscreen** | Display · Pixel、Techno、Awkward、Futuristic、Rugged | 拉丁 | 400, 700 | pixel_01 |
| ★ **Sixtyfour** | Monospace · Pixel、Monospace、Awkward、Futuristic、Rugged | 拉丁 | 400；SCAN -53–100；BLED 0–100 | pixel_01 |
| ★ **VT323** | Monospace · Pixel、Techno、Monospace、Vintage | 拉丁 | 400 | pixel_01 |

<a id="mono"></a>

## 等宽 / 代码（mono）

4 个家族 · 样张 `specimen\all\mono_01.png` · 精选架样张 `specimen\mono.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **IBM Plex Mono** | Monospace · Neo Grotesque、Monospace、Calm | 拉丁 | 100, 200, 300, 400, 500, 600, 700 · 带斜体 | mono_01 |
| ★ **JetBrains Mono** | Monospace · Geometric、Monospace、Competent、Stiff | 拉丁 | 100–800 可变 · 带斜体 | mono_01 |
| ★ **Share Tech Mono** | Monospace · Neo Grotesque、Superellipse、Monospace、Calm、Futuristic | 拉丁 | 400 | mono_01 |
| ★ **Space Mono** | Monospace · Techno、Grotesque、Neo Grotesque、Monospace、Calm | 拉丁 | 400, 700 · 带斜体 | mono_01 |

<a id="brush"></a>

## 笔刷 / 马克笔 / 涂鸦（brush）

3 个家族 · 样张 `specimen\all\brush_01.png` · 精选架样张 `specimen\brush.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Kaushan Script** | Handwriting · Active、Artistic、Happy、Vintage、Hanukkah | 拉丁 | 400 | brush_01 |
| ★ **Permanent Marker** | Handwriting · Brush、Handwritten、Informal、Active、Artistic | 拉丁 | 400 | brush_01 |
| ★ **Sedgwick Ave Display** | Handwriting · Handwritten、Active、Awkward、Playful、Rugged | 拉丁 | 400 | brush_01 |

<a id="script"></a>

## 花体 / 连笔手写（script）

2 个家族 · 样张 `specimen\all\script_01.png` · 精选架样张 `specimen\script.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Great Vibes** | Handwriting · Formal、Artistic、Fancy、Sophisticated、Vintage | 拉丁 | 400 | script_01 |
| ★ **Yellowtail** | Handwriting · Handwritten、Vintage | 拉丁 | 400 | script_01 |

<a id="stencil"></a>

## 模板字（stencil）

3 个家族 · 样张 `specimen\all\stencil_01.png` · 精选架样张 `specimen\stencil.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Big Shoulders Stencil** | Display · Futuristic、Loud、Rugged、Stiff | 拉丁 | 100–900 可变；opsz 10–72 | stencil_01 |
| ★ **Black Ops One** | Display · Loud、Rugged、Stiff | 拉丁 | 400 | stencil_01 |
| ★ **Saira Stencil** | Display · Artistic、Loud、Rugged、Stiff | 拉丁 | 100–900 可变 · 带斜体；wdth 50–125 | stencil_01 |

<a id="decorative"></a>

## 装饰 / 特效字（decorative）

6 个家族 · 样张 `specimen\all\decorative_01.png` · 精选架样张 `specimen\decorative.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Bungee Shade** | Display · Geometric、Rounded、Innovative、Rugged、Stiff | 拉丁 | 400 | decorative_01 |
| ★ **Faster One** | Display · Active、Awkward、Playful、Rugged、Vintage | 拉丁 | 400 | decorative_01 |
| ★ **Monoton** | Display · Art Deco、Inline、Geometric、Artistic、Awkward | 拉丁 | 400 | decorative_01 |
| ★ **Nabla** | Display · Shaded、Awkward、Futuristic、Innovative、Loud | 拉丁 | 400；EDPT 0–200；EHLT 0–24；彩色 COLRv1 | decorative_01 |
| ★ **Rubik Glitch** | Display · Distressed、Awkward、Playful、Rugged | 拉丁 | 400 | decorative_01 |
| ★ **Tilt Prism** | Display · Artistic、Rugged、Vintage、Kwanzaa | 拉丁 | 400；XROT -45–45；YROT -45–45 | decorative_01 |

<a id="cjk-sans"></a>

## 中文黑体（cjk-sans）

2 个家族 · 样张 `specimen\all\cjk-sans_01.png` · 精选架样张 `specimen\cjk-sans.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Noto Sans SC** | Sans Serif · Humanist、Business、Calm、Competent、Loud | 简中、繁中、日文、拉丁 | 100–900 可变 | cjk-sans_01 |
| ★ **Smiley Sans** | — | 简中、繁中缺字、日文、拉丁 | 400 | cjk-sans_01 |

<a id="cjk-serif"></a>

## 中文宋体 / 仿宋（cjk-serif）

2 个家族 · 样张 `specimen\all\cjk-serif_01.png` · 精选架样张 `specimen\cjk-serif.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Noto Serif SC** | Serif · Transitional、Business、Calm、Competent、Loud | 简中、繁中、日文、拉丁 | 200–900 可变 | cjk-serif_01 |
| ★ **Zhuque Fangsong** | — | 简中、繁中缺字、日文、拉丁 | 400 | cjk-serif_01 |

<a id="cjk-calligraphy"></a>

## 中文书法 / 手写（cjk-calligraphy）

2 个家族 · 样张 `specimen\all\cjk-calligraphy_01.png` · 精选架样张 `specimen\cjk-calligraphy.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Ma Shan Zheng** | Handwriting · Brush、Handwritten、Active、Artistic、Excited | 简中、繁中缺字、拉丁 | 400 | cjk-calligraphy_01 |
| ★ **Zhi Mang Xing** | Handwriting · Handwritten、Active、Artistic、Vintage、Lunar New Year | 简中、繁中缺字、拉丁 | 400 | cjk-calligraphy_01 |

<a id="cjk-display"></a>

## 中文创意标题（cjk-display）

3 个家族 · 样张 `specimen\all\cjk-display_01.png` · 精选架样张 `specimen\cjk-display.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **LXGW Marker Gothic** | Sans Serif · Brush、Geometric、Artistic、Lunar New Year | 简中、繁中、日文、拉丁 | 400 | cjk-display_01 |
| ★ **ZCOOL KuaiLe** | Sans Serif · Playful、Rugged | 简中、繁中缺字、拉丁 | 400 | cjk-display_01 |
| ★ **ZCOOL XiaoWei** | Sans Serif · Calm、Lunar New Year | 简中、繁中缺字、拉丁 | 400 | cjk-display_01 |

<a id="jp-display"></a>

## 日文标题（jp-display）

3 个家族 · 样张 `specimen\all\jp-display_01.png` · 精选架样张 `specimen\jp-display.png`

| 家族 | 官方风格标签 | 文字集 | 字重 / 可变 | 样张 |
|---|---|---|---|---|
| ★ **Dela Gothic One** | Display · Grotesque、Rugged | 简中缺字、繁中缺字、日文、拉丁 | 400 | jp-display_01 |
| ★ **DotGothic16** | Sans Serif · Pixel、Techno、Glyphic、Vintage | 简中缺字、繁中缺字、日文、拉丁 | 400 | jp-display_01 |
| ★ **Rampart One** | Display · Shaded、Playful | 简中缺字、繁中缺字、日文、拉丁 | 400 | jp-display_01 |
