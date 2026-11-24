# 字体库目录

> 由 `fonts.py` 自动生成（2026-11-23 19:09），不要手改。用法写进 skill 的 `scripts/fonts_starter.json`（fits），或 `fonts.py get "家族" --fits "…"`。

库：`assets/fonts/`，共 **59 个家族**、100 个字体文件、99 MB。文件路径相对于库目录。全部可免费商用、可做进视频；授权原文在各家族目录里（OFL.txt / LICENSE.txt），入库和每次重写目录时都核对授权原文和字体文件 name 表，对不上的不收；name 表写的是另一种也能商用的授权时照收，授权栏注明，鸣谢按授权文件。

分两层：**精选架** 59 个家族，每个都写了适合什么片子、怎么用，下面按风格组列出；**全量** 59 个（Google Fonts 全部家族 + 精选架），每个家族一行的紧凑索引在 `catalog_all.md`，分页样张在 `specimen\all\`。先在精选架里挑，没有合适的再翻全量。

## 怎么用

1. 挑字：先看 `specimen\<风格组>.png`（精选架）。排具体的标题先跑 `fonts.py specimen --text "谁最强"`（缺的字标红）或 `fonts.py search --local --text "谁最强"`（只列缺字）。精选架里没有合适的：翻全量——`catalog_all.md`（每组精选在前、其余按 Google 热度排，带官方风格标签和样张页码）和 `specimen\all\<风格组>_<页>.png`（每张几十个家族，字名写在左边），或 `fonts.py search --local --group script --tag Handwritten`、`--script zh`、`--tag Techno --var`。库里也没有的：`fonts.py search --group blackletter` 搜在线目录，`fonts.py get "家族名"` 入库。
2. 放进项目：`fonts.py use <项目> "Ma Shan Zheng" "UnifrakturMaguntia"`。字体复制进 `web\assets\fonts\`，`index.html` 自动接好；改了文案再跑一次 `fonts.py use <项目>`（中文字体只含项目里出现过的字）。描边、空心字（`-webkit-text-stroke`、`ctx.strokeText`）用静态字体：`fonts.py use <项目> "Montserrat:900" --static`（从可变字体切出这个字重并合并重叠的轮廓，描边不会在字里露出接缝线）。
3. 页面里：CSS `font-family: 'Ma Shan Zheng', serif;`；canvas `` ctx.font = `120px ${T3.fonts.use('Ma Shan Zheng', 'serif')}` ``。只有一个字重的字体：低于 600 的别写 bold（浏览器会假加粗），600 及以上的本身就是粗体。可变字体用 `font-weight` / `font-variation-settings` 调轴。
4. 片尾鸣谢：`fonts.py credits <项目>`。
5. 全量里的家族用顺手了、想放上精选架：`fonts.py get "家族" --fits "适合什么片子、怎么用"`（已在库里只更新说明，不重下）。

| 风格组 | 精选架 | 全量 | 精选样张 | 全量样张 |
|---|---|---|---|---|
| 哥特黑体（blackletter） | 5 | 5 | specimen/blackletter.png | specimen/all/blackletter_01.png |
| 高反差 / 古典衬线（didone） | 6 | 6 | specimen/didone.png | specimen/all/didone_01.png |
| 窄体粗黑（condensed） | 5 | 5 | specimen/condensed.png | specimen/all/condensed_01.png |
| 科技 / 科幻（tech） | 5 | 5 | specimen/tech.png | specimen/all/tech_01.png |
| 像素 / 点阵 / 数码管（pixel） | 8 | 8 | specimen/pixel.png | specimen/all/pixel_01.png |
| 等宽 / 代码（mono） | 4 | 4 | specimen/mono.png | specimen/all/mono_01.png |
| 笔刷 / 马克笔 / 涂鸦（brush） | 3 | 3 | specimen/brush.png | specimen/all/brush_01.png |
| 花体 / 连笔手写（script） | 2 | 2 | specimen/script.png | specimen/all/script_01.png |
| 模板字（stencil） | 3 | 3 | specimen/stencil.png | specimen/all/stencil_01.png |
| 装饰 / 特效字（decorative） | 6 | 6 | specimen/decorative.png | specimen/all/decorative_01.png |
| 中文黑体（cjk-sans） | 2 | 2 | specimen/cjk-sans.png | specimen/all/cjk-sans_01.png |
| 中文宋体 / 仿宋（cjk-serif） | 2 | 2 | specimen/cjk-serif.png | specimen/all/cjk-serif_01.png |
| 中文书法 / 手写（cjk-calligraphy） | 2 | 2 | specimen/cjk-calligraphy.png | specimen/all/cjk-calligraphy_01.png |
| 中文创意标题（cjk-display） | 3 | 3 | specimen/cjk-display.png | specimen/all/cjk-display_01.png |
| 日文标题（jp-display） | 3 | 3 | specimen/jp-display.png | specimen/all/jp-display_01.png |

## 哥特黑体（blackletter）

样张：`specimen\blackletter.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Chomsky** | 库里最接近原片 Gemini / Argon / Flash / Carbon 那种哥特字的一款：Old English Text 式 Textura（G 字里那道竖笔也和原片一样），类似《纽约时报》报头的老报头体。复刻原片的哥特标题先用它；也适合新闻、编年史、授勋式标题 | 400 | 拉丁 | OFL-1.1 | Fredrick R. Brennan | chomsky/Chomsky.otf |
| **Grenze Gotisch** | 字重 100–900 可变的现代哥特体：同一个词从细到粗做字重动画，适合重金属或赛博哥特风片头 | 100–900 可变 | 拉丁 | OFL-1.1 | Omnibus-Type | grenze-gotisch/GrenzeGotisch-VariableFont_wght.ttf |
| **Pirata One** | 窄身哥特体，可读性最好：小标签、榜单角标、徽章文字，在 HUD 里做标签也不会糊 | 400 | 拉丁 | OFL-1.1（保留名 Pirata） | Rodrigo Fuenzalida、Nicolas Massi | pirata-one/PirataOne-Regular.ttf |
| **UnifrakturCook** | 粗重的德式 Fraktur（只有 700 一个字重，比 Maguntia 黑得多）：海报式大字、印章感标题，可配做旧纸纹或烫金 | 700 | 拉丁 | OFL-1.1（保留名 UnifrakturCook） | j. 'mach' wust、Peter Wiegel | unifrakturcook/UnifrakturCook-Bold.ttf |
| **UnifrakturMaguntia** | 德式 Fraktur（断笔加圆弧，带花式大写）：德国或中欧历史、童话古籍、老报刊和证书、啤酒节或老酒标风的标题，也能做史诗或暗黑风短标题，可配金属渐变或火焰辉光。只排短词，别整词全大写（花式大写连排难认）。它不是原片那种 Old English 式 Textura，要原片的味道用 Chomsky | 400 | 拉丁 | OFL-1.1（保留名 UnifrakturMaguntia） | j. 'mach' wust、Peter Wiegel | unifrakturmaguntia/UnifrakturMaguntia-Regular.ttf |

## 高反差 / 古典衬线（didone）

样张：`specimen\didone.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Abril Fatface** | 胖脸 Didone：海报式冲击标题、排名大数字「No.1」。原片标签「GEMINI」那种粗体大写衬线与它最接近 | 400 | 拉丁 | OFL-1.1（保留名 Abril, Abril Fatface） | TypeTogether | abril-fatface/AbrilFatface-Regular.ttf |
| **Bodoni Moda** | 真正的 Didone，带光学尺寸轴：时尚或奢华感的大标题、大号数字 | 400–900 可变 · 带斜体；opsz 6–96 | 拉丁 | OFL-1.1 | Owen Earl | bodoni-moda/BodoniModa-VariableFont_opsz-wght.ttf<br>bodoni-moda/BodoniModa-Italic-VariableFont_opsz-wght.ttf |
| **Cinzel** | 罗马碑刻式大写：电影预告式史诗标题、加冕或宣言镜头 | 400–900 可变 | 拉丁 | OFL-1.1 | Natanael Gama | cinzel/Cinzel-VariableFont_wght.ttf |
| **Cormorant Garamond** | 古典 Garamond，带斜体：文学、历史、手稿感的字幕和小标题 | 300–700 可变 · 带斜体 | 拉丁 | OFL-1.1 | Christian Thalmann | cormorant-garamond/CormorantGaramond-VariableFont_wght.ttf<br>cormorant-garamond/CormorantGaramond-Italic-VariableFont_wght.ttf |
| **Instrument Serif** | 现代窄衬线，带斜体：极简高级感、科技发布会式引言，可作哥特体的「优雅版」替代 | 400 · 带斜体 | 拉丁 | OFL-1.1 | Rodrigo Fuenzalida、Jordan Egstad | instrument-serif/InstrumentSerif-Regular.ttf<br>instrument-serif/InstrumentSerif-Italic.ttf |
| **Playfair Display** | 高反差衬线，带斜体：优雅型角色（如 Claude）的名字、引言、杂志封面式排版。原片面板「GPT-6」那种窄 Didone：Black 字重横向压到约 78%（CSS scaleX）最接近 | 400–900 可变 · 带斜体 | 拉丁 | OFL-1.1（保留名 Playfair Display） | Claus Eggers Sørensen | playfair-display/PlayfairDisplay-VariableFont_wght.ttf<br>playfair-display/PlayfairDisplay-Italic-VariableFont_wght.ttf |

## 窄体粗黑（condensed）

样张：`specimen\condensed.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Anton** | 窄体粗黑（Impact 的开源替代）：标题砸入、卡点大字、排名数字 | 400 | 拉丁 | OFL-1.1 | Vernon Adams | anton/Anton-Regular.ttf |
| **Bebas Neue** | 全大写窄黑：快切字卡、副标题条、体育或竞技感 | 400 | 拉丁 | OFL-1.1 | Ryoichi Tsunekawa | bebas-neue/BebasNeue-Regular.ttf |
| **Big Shoulders** | 芝加哥招牌风窄黑，字重和光学尺寸都可变：工业或城市感大字、倒计时 | 100–900 可变；opsz 10–72 | 拉丁 | OFL-1.1 | Patric King | big-shoulders/BigShoulders-VariableFont_opsz-wght.ttf |
| **League Gothic** | 复古窄黑，宽度可变：老海报或报纸标题、字宽挤压动画 | 400；wdth 75–100 | 拉丁 | OFL-1.1 | Tyler Finck、Caroline Hadilaksono、Micah Rich | league-gothic/LeagueGothic-Regular-VariableFont_wdth.ttf |
| **Oswald** | 字重可变的窄黑：数据面板标题，或长英文标题需要多种字重时 | 200–700 可变 | 拉丁 | OFL-1.1 | Vernon Adams、Kalapi Gajjar、Cyreal | oswald/Oswald-VariableFont_wght.ttf |

## 科技 / 科幻（tech）

样张：`specimen\tech.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Chakra Petch** | 切角科技体，带斜体：游戏 UI、战斗力数值、警告框 | 300, 400, 500, 600, 700 · 带斜体 | 拉丁 | OFL-1.1 | Cadson Demak | chakra-petch/ChakraPetch-Light.ttf<br>chakra-petch/ChakraPetch-Regular.ttf<br>chakra-petch/ChakraPetch-Medium.ttf<br>…共 10 个 |
| **Michroma** | 超宽科技体：发布会式型号名、宽幅字幕条、汽车或硬件感 | 400 | 拉丁 | OFL-1.1 | Vernon Adams | michroma/Michroma-Regular.ttf |
| **Orbitron** | 几何科幻体：机甲、太空、AI 型号名，HUD 主标题 | 400–900 可变 | 拉丁 | OFL-1.1（保留名 Orbitron） | Matt McInerney | orbitron/Orbitron-VariableFont_wght.ttf |
| **Oxanium** | 方形科幻体，字重可变：赛博朋克 HUD、数据流、加载条文字 | 200–800 可变 | 拉丁 | OFL-1.1 | Severin Meyer | oxanium/Oxanium-VariableFont_wght.ttf |
| **Rajdhani** | 方正窄科技体：HUD 数据标签、参数表、雷达图刻度 | 300, 400, 500, 600, 700 | 拉丁 | OFL-1.1 | Indian Type Foundry | rajdhani/Rajdhani-Light.ttf<br>rajdhani/Rajdhani-Regular.ttf<br>rajdhani/Rajdhani-Medium.ttf<br>…共 5 个 |

## 像素 / 点阵 / 数码管（pixel）

样张：`specimen\pixel.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Doto** | LED 点阵，圆点形状（ROND 轴）和字重都可调：原片同款点阵屏、跑马灯、记分牌 | 100–900 可变；ROND 0–100 | 拉丁 | OFL-1.1 | Óliver Lalan | doto/Doto-VariableFont_ROND-wght.ttf |
| **DSEG7 Classic** | 七段数码管：计分板、倒计时、跑分数字、仪表读数。只有数字和少量字母 | 300, 400, 700 · 带斜体 | 拉丁 | OFL-1.1（保留名 DSEG） | keshikan | dseg7-classic/dseg7-classic-300-normal.ttf<br>dseg7-classic/dseg7-classic-400-normal.ttf<br>dseg7-classic/dseg7-classic-700-normal.ttf<br>…共 6 个 |
| **Fusion Pixel 12px Proportional SC** | 中文像素字（缝合像素）：中文点阵屏、像素游戏对话框、LED 中文字幕。按 12px 的整数倍放大才锐利 | 400 | 拉丁、简中（常用一级字全）、繁中、日文、韩文；汉字 17626 | OFL-1.1（保留名 Fusion Pixel） | TakWolf | fusion-pixel-12px-proportional-sc/fusion-pixel-12px-proportional-sc-400-normal.ttf |
| **Jacquard 24** | 像素化哥特体（织锦图案风格）：把哥特风和像素/LED 风结合，适合游戏化的史诗标签 | 400 | 拉丁 | OFL-1.1 | Sarah Cadigan-Fried | jacquard-24/Jacquard24-Regular.ttf |
| **Press Start 2P** | 8-bit 街机像素体：复古游戏关卡字幕、「GAME OVER」「1UP」式提示 | 400 | 拉丁 | OFL-1.1（保留名 Press Start 2P） | CodeMan38 | press-start-2p/PressStart2P-Regular.ttf |
| **Silkscreen** | 小号像素体：屏幕边角小标签、像素 UI、贴纸角标 | 400, 700 | 拉丁 | OFL-1.1 | Jason Kottke | silkscreen/Silkscreen-Regular.ttf<br>silkscreen/Silkscreen-Bold.ttf |
| **Sixtyfour** | 80 年代电脑字，带扫描线（SCAN）和渗色（BLED）两个轴：CRT 故障、开机画面、复古科技 | 400；SCAN -53–100；BLED 0–100 | 拉丁 | OFL-1.1 | Jens Kutílek | sixtyfour/Sixtyfour-Regular-VariableFont_BLED-SCAN.ttf |
| **VT323** | 老终端点阵：命令行、黑客、系统日志、CRT 显示器画面 | 400 | 拉丁 | OFL-1.1 | Peter Hull | vt323/VT323-Regular.ttf |

## 等宽 / 代码（mono）

样张：`specimen\mono.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **IBM Plex Mono** | 企业感等宽，带斜体：技术报告式字幕、参数表、日志 | 100, 200, 300, 400, 500, 600, 700 · 带斜体 | 拉丁 | OFL-1.1（保留名 Plex） | Mike Abbink、Bold Monday | ibm-plex-mono/IBMPlexMono-Thin.ttf<br>ibm-plex-mono/IBMPlexMono-ExtraLight.ttf<br>ibm-plex-mono/IBMPlexMono-Light.ttf<br>…共 14 个 |
| **JetBrains Mono** | 代码等宽：Claude Code 终端界面、代码雨、命令行打字机效果 | 100–800 可变 · 带斜体 | 拉丁 | OFL-1.1 | JetBrains、Philipp Nurullin、Konstantin Bulenkov | jetbrains-mono/JetBrainsMono-VariableFont_wght.ttf<br>jetbrains-mono/JetBrainsMono-Italic-VariableFont_wght.ttf |
| **Share Tech Mono** | 科幻等宽：HUD 读数、坐标、时间码 | 400 | 拉丁 | OFL-1.1（保留名 Share） | Carrois Apostrophe | share-tech-mono/ShareTechMono-Regular.ttf |
| **Space Mono** | 复古未来等宽：太空或 NASA 风标签、编号、数据卡片 | 400, 700 · 带斜体 | 拉丁 | OFL-1.1 | Colophon Foundry | space-mono/SpaceMono-Regular.ttf<br>space-mono/SpaceMono-Bold.ttf<br>space-mono/SpaceMono-Italic.ttf<br>space-mono/SpaceMono-BoldItalic.ttf |

## 笔刷 / 马克笔 / 涂鸦（brush）

样张：`specimen\brush.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Kaushan Script** | 粗毛刷连写：运动或热血标题、街头海报 | 400 | 拉丁 | OFL-1.1（保留名 Kaushan Script） | Impallari Type | kaushan-script/KaushanScript-Regular.ttf |
| **Permanent Marker** | 马克笔手写：吐槽批注、圈画标注、草稿感 | 400 | 拉丁 | Apache-2.0 | Font Diner | permanent-marker/PermanentMarker-Regular.ttf |
| **Sedgwick Ave Display** | 涂鸦字：街头或嘻哈风、墙面喷漆标题 | 400 | 拉丁 | OFL-1.1 | Pedro Vergani、Kevin Burke | sedgwick-ave-display/SedgwickAveDisplay-Regular.ttf |

## 花体 / 连笔手写（script）

样张：`specimen\script.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Great Vibes** | 优雅花体：颁奖、致敬感场面、片尾签名 | 400 | 拉丁 | OFL-1.1 | Robert Leuschke | great-vibes/GreatVibes-Regular.ttf |
| **Yellowtail** | 复古霓虹手写：80 年代霓虹灯招牌、Vaporwave 风片头 | 400 | 拉丁 | Apache-2.0 | Astigmatic | yellowtail/Yellowtail-Regular.ttf |

## 模板字（stencil）

样张：`specimen\stencil.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Big Shoulders Stencil** | 窄体模板字：集装箱或工厂编号、硬核工业标题 | 100–900 可变；opsz 10–72 | 拉丁 | OFL-1.1 | Patric King | big-shoulders-stencil/BigShouldersStencil-VariableFont_opsz-wght.ttf |
| **Black Ops One** | 军事模板字：作战档案、机密文件、警告标签 | 400 | 拉丁 | OFL-1.1 | James Grieshaber、Eben Sorkin | black-ops-one/BlackOpsOne-Regular.ttf |
| **Saira Stencil** | 宽度和字重都可变的模板字：科技工业风、机身喷涂编号 | 100–900 可变 · 带斜体；wdth 50–125 | 拉丁 | OFL-1.1 | Hector Gatti、Omnibus-Type | saira-stencil/SairaStencil-VariableFont_wdth-wght.ttf<br>saira-stencil/SairaStencil-Italic-VariableFont_wdth-wght.ttf |

## 装饰 / 特效字（decorative）

样张：`specimen\decorative.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Bungee Shade** | 自带立体阴影的招牌字：街头招牌、立体大标题。同家族还有 Outline、Inline、Spice 可另取 | 400 | 拉丁 | OFL-1.1 | David Jonathan Ross | bungee-shade/BungeeShade-Regular.ttf |
| **Faster One** | 速度线字：竞速、冲刺、「最快」类排名，快闪转场 | 400 | 拉丁 | OFL-1.1（保留名 Faster） | Eduardo Tunni | faster-one/FasterOne-Regular.ttf |
| **Monoton** | 多线霓虹描边：迪斯科或复古霓虹灯、开场 Logo 点亮动画（字体文件内的版权行是旧文字，以随包 OFL.txt 为准） | 400 | 拉丁 | OFL-1.1（保留名 Monoton） | Vernon Adams | monoton/Monoton-Regular.ttf |
| **Nabla** | 彩色 3D 等距字（COLRv1，Chrome 能渲染），挤出深度可调（EDPT 轴）：游戏感立体标题、奖杯字 | 400；EDPT 0–200；EHLT 0–24；彩色 COLRv1 | 拉丁 | OFL-1.1 | Arthur Reinders Folmer、Just van Rossum | nabla/Nabla-Regular-VariableFont_EDPT-EHLT.ttf |
| **Rubik Glitch** | 自带故障切片的字：故障转场、信号干扰、系统报错提示 | 400 | 拉丁 | OFL-1.1 | NaN、Luke Prowse | rubik-glitch/RubikGlitch-Regular.ttf |
| **Tilt Prism** | 棱镜描边字，可做 3D 倾斜（XROT/YROT 轴）：标题翻转、伪 3D 转动动画 | 400；XROT -45–45；YROT -45–45 | 拉丁 | OFL-1.1 | Andy Clymer | tilt-prism/TiltPrism-Regular-VariableFont_XROT-YROT.ttf |

## 中文黑体（cjk-sans）

样张：`specimen\cjk-sans.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Noto Sans SC** | 思源黑体（同一设计），字重 100–900 可变：数据面板、字幕、正文的默认中文字体。Win11 自带同名字体，QA 看 T3.fonts.report() | 100–900 可变 | 拉丁、简中（GB2312 全）、繁中、日文；汉字 27558 | OFL-1.1（保留名 Source） | Adobe（西塚涼子 Ryoko Nishizuka、Paul D. Hunt、Sandoll）、Google | noto-sans-sc/NotoSansSC-VariableFont_wght.ttf |
| **Smiley Sans** | 得意黑：自带斜度的窄长黑体，B 站科技区最常见的标题字。中文快切字卡和排名标题的首选（只有一个字重，别写 bold） | 400 | 拉丁、简中（GB2312 全）、繁中缺字（3404/5401）、日文（第一水准汉字 1940/2965）；汉字 8136 | OFL-1.1（保留名 Smiley, 得意黑） | atelierAnchor（oooooohmygosh、Nagisa Chen、Janine Sui、Heda Shi、Jian Li） | smiley-sans/SmileySans-Oblique.ttf |

## 中文宋体 / 仿宋（cjk-serif）

样张：`specimen\cjk-serif.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Noto Serif SC** | 思源宋体（同一设计），字重 200–900 可变：中文大标题的宋体版、纪录片或文学感字幕，Black 字重可做冲击感宋体。Win11 自带同名字体，QA 看 T3.fonts.report() | 200–900 可变 | 拉丁、简中（GB2312 全）、繁中、日文；汉字 27584 | OFL-1.1 | Adobe（西塚涼子 Ryoko Nishizuka、Frank Grießhammer、张文龙 Wenlong Zhang、Sandoll）、Google | noto-serif-sc/NotoSerifSC-VariableFont_wght.ttf |
| **Zhuque Fangsong** | 朱雀仿宋：古籍、公文、历史感的旁白字幕和引文，比宋体清秀。仍是技术预览版 | 400 | 拉丁、简中（GB2312 全）、繁中缺字（5287/5401）、日文；汉字 11088 | OFL-1.1 | Junyi Yu、Yeong-sy Han、Yehang Yin、Jianqiao Li (TrionesType / JadeFoci) | zhuque-fangsong/ZhuqueFangsong-Regular.ttf |

## 中文书法 / 手写（cjk-calligraphy）

样张：`specimen\cjk-calligraphy.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Ma Shan Zheng** | 马善政楷书毛笔：武侠、国风、书法题字、角色称号。覆盖 GB2312，生僻字会缺 | 400 | 拉丁、简中（GB2312 全）、繁中缺字（3328/5401）；汉字 6763 | OFL-1.1 | Ma ShanZheng | ma-shan-zheng/MaShanZheng-Regular.ttf |
| **Zhi Mang Xing** | 志莽行书：潇洒的行书题字、国风片头、印章旁的落款 | 400 | 拉丁、简中（GB2312 全）、繁中缺字（3328/5401）；汉字 6763 | OFL-1.1 | Wei Zhimang | zhi-mang-xing/ZhiMangXing-Regular.ttf |

## 中文创意标题（cjk-display）

样张：`specimen\cjk-display.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **LXGW Marker Gothic** | 霞鹜漫黑：马克笔黑体，适合手绘批注、漫画对白框、吐槽字幕（在线目录只标了繁体，实际含简体） | 400 | 拉丁、简中（GB2312 全）、繁中、日文；汉字 12904 | OFL-1.1 | LXGW | lxgw-marker-gothic/LXGWMarkerGothic-Regular.ttf |
| **ZCOOL KuaiLe** | 站酷快乐体：卡通活泼字，用于轻松向花字、弹幕式字卡 | 400 | 拉丁、简中（GB2312 全）、繁中缺字（3329/5401）；汉字 6766 | OFL-1.1 | Liu Bingke、Yang Kang、Wu Shaojie | zcool-kuaile/ZCOOLKuaiLe-Regular.ttf |
| **ZCOOL XiaoWei** | 站酷小薇 LOGO 体：带衬线味的标题字，适合文艺或品牌感标题 | 400 | 拉丁、简中（GB2312 全）、繁中缺字（3328/5401）；汉字 6763 | OFL-1.1 | Li Dawei | zcool-xiaowei/ZCOOLXiaoWei-Regular.ttf |

## 日文标题（jp-display）

样张：`specimen\jp-display.png`

| 家族 | 适合的片子和用法 | 字重 / 可变轴 | 文字集 | 授权 | 作者 | 文件 |
|---|---|---|---|---|---|---|
| **Dela Gothic One** | 超粗日文黑体：日系动漫或游戏片头大字。缺不少简体字，排中文前先查缺字 | 400 | 拉丁、简中缺字（一级字 2471/3755）、繁中缺字（4757/5401）、日文；汉字 7673 | OFL-1.1 | artakana | dela-gothic-one/DelaGothicOne-Regular.ttf |
| **DotGothic16** | 日文点阵像素：日式 RPG 对话框、街机日文提示。中文像素字用 Fusion Pixel | 400 | 拉丁、简中缺字（一级字 2389/3755）、繁中缺字（4496/5401）、日文；汉字 6715 | OFL-1.1 | Fontworks Inc. | dotgothic16/DotGothic16-Regular.ttf |
| **Rampart One** | 日文立体描边字：日系综艺或玩具感标题。缺部分简体字，只排日文 | 400 | 拉丁、简中缺字（一级字 2389/3755）、繁中缺字（4496/5401）、日文；汉字 6715 | OFL-1.1 | Fontworks Inc. | rampart-one/RampartOne-Regular.ttf |

## 全量：各风格组概览

每个家族一行的索引在 `catalog_all.md`（共 59 个，★ = 精选架）；分页样张 `specimen\all\<风格组>_<页>.png`，每张 40 个家族，顺序和索引一致：精选在前，其余按 Google Fonts 热度排（越靠前越常用）。

| 风格组 | 家族数 | 样张页 | 热度靠前的 | 常见官方风格标签 |
|---|---|---|---|---|
| [哥特黑体（blackletter）](catalog_all.md#blackletter) | 5 | blackletter_01 | Grenze Gotisch、Pirata One、UnifrakturCook、UnifrakturMaguntia | Blackletter（哥特）4 |
| [高反差 / 古典衬线（didone）](catalog_all.md#didone) | 6 | didone_01 | Abril Fatface、Bodoni Moda、Cinzel、Cormorant Garamond、Instrument Serif、Playfair Display | Modern（现代衬线）3、Didone（迪多衬线）2、Old Style Garalde（旧式衬线）2、Fat Face（胖脸衬线）1、Scotch（苏格兰衬线）1 |
| [窄体粗黑（condensed）](catalog_all.md#condensed) | 5 | condensed_01 | Anton、Bebas Neue、Big Shoulders、League Gothic、Oswald | Grotesque（怪诞）2、Neo Grotesque（新怪诞）2、Superellipse（方圆）1 |
| [科技 / 科幻（tech）](catalog_all.md#tech) | 5 | tech_01 | Chakra Petch、Michroma、Orbitron、Oxanium、Rajdhani | Techno（科技）4、Superellipse（方圆）3 |
| [像素 / 点阵 / 数码管（pixel）](catalog_all.md#pixel) | 8 | pixel_01 | Doto、Jacquard 24、Press Start 2P、Silkscreen、Sixtyfour、VT323 | Pixel（像素）6、Monospace（等宽）3、Techno（科技）3、Medieval（中世纪）1 |
| [等宽 / 代码（mono）](catalog_all.md#mono) | 4 | mono_01 | IBM Plex Mono、JetBrains Mono、Share Tech Mono、Space Mono | Monospace（等宽）4、Neo Grotesque（新怪诞）3、Geometric（几何）1、Grotesque（怪诞）1、Superellipse（方圆）1 |
| [笔刷 / 马克笔 / 涂鸦（brush）](catalog_all.md#brush) | 3 | brush_01 | Kaushan Script、Permanent Marker、Sedgwick Ave Display | Handwritten（手写）2、Brush（笔刷）1、Informal（随手写）1 |
| [花体 / 连笔手写（script）](catalog_all.md#script) | 2 | script_01 | Great Vibes、Yellowtail | Formal（正式花体）1、Handwritten（手写）1 |
| [模板字（stencil）](catalog_all.md#stencil) | 3 | stencil_01 | Big Shoulders Stencil、Black Ops One、Saira Stencil |  |
| [装饰 / 特效字（decorative）](catalog_all.md#decorative) | 6 | decorative_01 | Bungee Shade、Faster One、Monoton、Nabla、Rubik Glitch、Tilt Prism | Geometric（几何）2、Art Deco（装饰艺术）1、Distressed（做旧）1、Inline（内线）1、Rounded（圆体）1 |
| [中文黑体（cjk-sans）](catalog_all.md#cjk-sans) | 2 | cjk-sans_01 | Noto Sans SC | Humanist（人文）1 |
| [中文宋体 / 仿宋（cjk-serif）](catalog_all.md#cjk-serif) | 2 | cjk-serif_01 | Noto Serif SC | Transitional（过渡衬线）1 |
| [中文书法 / 手写（cjk-calligraphy）](catalog_all.md#cjk-calligraphy) | 2 | cjk-calligraphy_01 | Ma Shan Zheng、Zhi Mang Xing | Handwritten（手写）2、Brush（笔刷）1 |
| [中文创意标题（cjk-display）](catalog_all.md#cjk-display) | 3 | cjk-display_01 | LXGW Marker Gothic、ZCOOL KuaiLe、ZCOOL XiaoWei | Brush（笔刷）1、Geometric（几何）1 |
| [日文标题（jp-display）](catalog_all.md#jp-display) | 3 | jp-display_01 | Dela Gothic One、DotGothic16、Rampart One | Glyphic（碑刻）1、Grotesque（怪诞）1、Pixel（像素）1、Shaded（阴影）1、Techno（科技）1 |

## 不在库里的免费商用字体（平面设计师不要自己下）

阿里巴巴普惠体 3.0 / 阿里妈妈系列、HarmonyOS Sans、MiSans：协议允许免费用在视频等商业作品里，但都是专有授权——下载或使用即视为同意协议，而且禁止修改、转格式、拆分字体（`fonts.py use` 的子集和 WOFF2 都算），HarmonyOS Sans 和 MiSans 还要求在作品里注明。要用先请主线程问用户本人，确认后整份放进 `manual\`，不走 `fonts.py use`。
