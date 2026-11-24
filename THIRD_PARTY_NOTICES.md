# Third-Party Notices

Original documentation, scripts, workflows, and templates in **Chiaki's-video-skill** are released under the **MIT License** (see `LICENSE`).
The following third-party libraries, reference catalogues, textures, and fonts are bundled or adapted under their respective licences:

---

## 1. GSAP 3.15.1 (GreenSock Animation Platform)
- **Location**: `assets/template/lib/gsap/`
- **Copyright**: GreenSock / Webflow
- **License**: GSAP Standard "No Charge" License (see `assets/template/lib/gsap/LICENSE.txt`)
- **Notes**: UMD builds bundled for deterministic offline `file://` playback (`gsap`, `CustomEase`, `SplitText`, `DrawSVGPlugin`, `MorphSVGPlugin`, `MotionPathPlugin`, `Physics2DPlugin`, `TextPlugin`, `CustomBounce`, `CustomWiggle`). `ScrambleTextPlugin` is intentionally omitted for frame determinism.

## 2. mg-styles-15 (Procedural Audio Engine `mgaudio`, Style Catalogue, CC0 Textures)
- **Source**: https://github.com/Vincentwei1021/mg-styles-15
- **Copyright**: Copyright (c) 2026 Vincentwei1021
- **License**: MIT License (see `assets/mgaudio/LICENSE`)
- **Used in**:
  - `assets/mgaudio/` — 48 kHz procedural synth, SFX, mixing & `-14 LUFS` mastering engine
  - `references/mg-styles.md` — 15 motion-design style catalogue (adapted & pruned for 2D workflows)
  - `assets/textures/` — CC0 film grain, dust, paper, and washi overlays

## 3. video-shotcraft (124 Motion-Design Shot Recipes)
- **Source**: https://github.com/hch2025/video-shotcraft
- **Copyright**: Copyright (c) 2025–2026 hch2025
- **License**: Apache License, Version 2.0
- **Used in**: `references/shot-recipes.md` (124 named shot recipes, paraphrased into studio reference format)

## 4. Bundled Open-Source Font Library (`assets/fonts/`)
- **Location**: `assets/fonts/` (59 curated families across Latin, Display, Mono, Pixel, CJK, and Japanese categories)
- **Licenses**: **SIL Open Font License 1.1 (OFL-1.1)** and **Apache License 2.0** only (100% free for personal and commercial video production)
- **Full Attribution**: Each family folder in `assets/fonts/<slug>/` preserves its verbatim `OFL.txt` or `LICENSE.txt`. Machine-readable metadata and per-family designer/license credits are listed in `assets/fonts/catalog.json` and `assets/fonts/catalog.md`. Use `python -I scripts/fonts.py credits <project>` to generate end-credit lines automatically.
- **Template Sample Font**: `assets/template/lib/fonts/BodoniModaItalic_opsz6_w500.ttf` (Bodoni Moda, SIL Open Font License 1.1).

## 5. Self-Contained Anime 19-Part SemanticSam Loader (`scripts/vision/_l2dsam/`) & Optional Vision Weights
- **Location**: `scripts/vision/_l2dsam/`
- **Upstream Sources**:
  - `shitagaki-lab/see-through` (SIGGRAPH 2026 SemanticSam adapter): https://github.com/shitagaki-lab/see-through — **Apache License 2.0**
  - Meta Segment Anything (`segment-anything`) & HQ-SAM (`sam-hq`): **Apache License 2.0**
- **License**: Full verbatim Apache License 2.0 text is bundled at `scripts/vision/_l2dsam/LICENSE`. Modified files (`extend_sam.py`, `sam/build_sam.py`) carry adaptation notices per Apache-2.0 §4(b).
- **On-Demand HuggingFace Weights** (downloaded only when invoking `scripts/vision/cutout.py`, `part_cutout.py`, or `depth.py`):
  - `ZhengPeng7/BiRefNet_HR`, `ZhengPeng7/BiRefNet_HR-matting`, and `joelseytre/toonout` — **MIT License**
  - `24yearsold/l2d_sam_iter2` (`checkpoint-18000.pt`) and `depth-anything/Depth-Anything-V2-Small-hf` — **Apache License 2.0**
