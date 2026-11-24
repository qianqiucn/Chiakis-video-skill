# Pluggable Art & Asset Stage (`art-pipeline.md` — Stage 4, After Gate A)

Executed **after Gate A locks the storyboard, beat grid, and asset list** — never generate images before Gate A passes, so zero API credits or client time are wasted on discarded shots.

---

## 1. Four Supported Image / Visual Asset Routes
Every illustrated or photographic shot in the shot table declares its `provider` inside `<project>/work/art_manifest.json`. Mix routes freely within the same film:

| `provider` | When to use | How it runs |
|---|---|---|
| **`user_files`** | Client supplies their own illustrations, character sheets, photos, or footage | Copy & verify files into `web/assets/art/` (`scripts/art_gen.py run` or manual copy) |
| **`gemini`** | Client wants Gemini multimodal image generation | `scripts/art_gen.py run` using `GEMINI_API_KEY` (or the host agent's native `image-generator` / `gemini-api` skill) |
| **`codex`** | Client wants OpenAI / Codex image generation (`gpt-image-1`) | `scripts/art_gen.py run` using `OPENAI_API_KEY` (or Codex's built-in image tool) |
| **`custom_api`** | Client brings their own HTTP image API (Seedream, Volcengine Ark, Flux, SiliconFlow, OpenRouter, local ComfyUI OpenAI-compat gateway) | `scripts/art_gen.py run` using `CHIAKI_IMAGE_API_URL`, `CHIAKI_IMAGE_API_KEY`, `CHIAKI_IMAGE_MODEL` |
| **`code_only`** | Pure Canvas 2D / SVG / kinetic typography / Blender procedural set | No bitmap generation needed |

> **Cost & approval boundary**: before running any paid external API (`custom_api`, `gemini`, `codex`), confirm the exact shot count and client authorization from the brief. Never hardcode API keys inside project files or scripts — read them strictly from environment variables.

---

## 2. Manifest Schema (`<project>/work/art_manifest.json`)
Initialize a starter manifest with `python -X utf8 <sk>/scripts/art_gen.py init <project>`:

```json
{
  "project": "my_pv",
  "defaults": {
    "provider": "user_files",
    "size": "1920x1080",
    "style_bible": "Cohesive colour palette, lighting direction, and medium shared across all generated shots",
    "extra_body": {}
  },
  "shots": [
    {
      "id": "act1_hero",
      "act": "act1",
      "provider": "gemini",
      "refs": ["web/assets/art/char_sheet.png"],
      "out": "web/assets/art/act1_hero.png",
      "prompt": "Wide editorial illustration, clean composition with clear upper-left negative space for typography, zero embedded text or watermarks",
      "source": "",
      "needs_depth": true,
      "layers": ["plate", "subject"],
      "notes": "For 2.5D Blender depth relief (--orbit -8)"
    }
  ]
}
```

### CLI Commands (`scripts/art_gen.py`, stdlib only)
```bash
# 1. Create starter manifest
python -X utf8 <sk>/scripts/art_gen.py init <project>

# 2. Preview what will be copied / generated (incl. multi-ref counts) without calling any API
python -X utf8 <sk>/scripts/art_gen.py run <project> --dry

# 3. Execute manifest in parallel with automatic backoff retries on HTTP 429/5xx (skips existing files unless --force)
python -X utf8 <sk>/scripts/art_gen.py run <project> --workers 3 --retries 3

# 4. Verify every manifest asset exists on disk with valid dimensions
python -X utf8 <sk>/scripts/art_gen.py check <project>
```

> **Multi-reference character & style anchoring (`refs`)**: pass one or more local image paths in `"refs": [...]` per shot (e.g. a character turnaround sheet or locked colour key). `art_gen.py` automatically encodes them as base64 data URIs (`image` field for `custom_api` / OpenAI-Ark endpoints), `inlineData` parts (for `gemini`), or multipart `/v1/images/edits` (for `codex`).

---

## 3. Environment Variables for Optional Image APIs
| Variable | Provider | Purpose |
|---|---|---|
| `CHIAKI_IMAGE_API_URL` | `custom_api` | OpenAI-Images-compatible POST endpoint (e.g. `https://.../v1/images/generations`) |
| `CHIAKI_IMAGE_API_KEY` | `custom_api` | Bearer token for your custom image endpoint (or set `CHIAKI_IMAGE_API_KEY_FILE` pointing to a local key file) |
| `CHIAKI_IMAGE_MODEL` | `custom_api` | Model identifier expected by your endpoint |
| `GEMINI_API_KEY` | `gemini` | Google Gemini API key (optional `CHIAKI_GEMINI_IMAGE_MODEL`, default `gemini-2.5-flash-image`, or `GEMINI_API_KEY_FILE`) |
| `OPENAI_API_KEY` | `codex` | OpenAI API key (optional `CHIAKI_OPENAI_IMAGE_MODEL`, default `gpt-image-1`, or `OPENAI_API_KEY_FILE`) |

---

## 4. Visual Acceptance & Pre-Build Prep (Before Stage 6 Build)
Before handing assets to the 3D, Edit, and Design crafts:
1. **Inspect every plate at full size**: confirm zero unwanted gibberish text/watermarks, harmonious palette matching the pitch's hex tokens, and clear negative space where kinetic typography will sit.
2. **Vision cut-outs, 19-part anime split & pixel-aligned clean plates (`scripts/vision/`)** — single canonical toolkit (one tool per job, zero overlap):
   - **Whole foreground RGBA cut-out (`scripts/vision/cutout.py`, MIT, GPU FP16 ~0.8–1.0 s/img + auto edge defringe)**:
     - **`--model toonout`** (`joelseytre/toonout`, 1024px, MIT): **default for stylized anime characters** on dark/busy painted scenes (preserves white sleeves & glowing FX wisps without alpha holes).
     - **`--model hr`** (`ZhengPeng7/BiRefNet_HR`, 2048px, MIT, script default): **default for 2K props, botanicals, objects & clean-ground subjects** (razor-sharp 2048px edges, zero cloth holes).
     - **`--model hr-matting`** (`ZhengPeng7/BiRefNet_HR-matting`, 2048px, MIT): optional specialist **only** for genuinely translucent glass/veils/smoke/real human hair.
     ```bash
     python -X utf8 <sk>/scripts/vision/cutout.py web/assets/art/<id>.png web/assets/art/<id>_rgba.png --model toonout
     python -X utf8 <sk>/scripts/vision/cutout.py web/assets/art/<prop>.png web/assets/art/<prop>_rgba.png --model hr
     ```
   - **Anime 19-part single-layer cut-out & zero-ghosting clean plate (`scripts/vision/part_cutout.py`, self-contained Apache-2.0 `24yearsold/l2d_sam_iter2` + MIT `ToonOut` 2K local zoom, ~1.1–1.4 s/img)**:
     - **Default for hair (`T3.her.wave`) and any character sub-part** (`hair`, `headwear`, `face`, `eyes`, `eyewear`, `ears`, `earwear`, `nose`, `mouth`, `neck`, `neckwear`, `topwear`, `handwear`, `bottomwear`, `legwear`, `footwear`, `tail`, `wings`, `objects`; comma-separated allowed, e.g. `--part hair,headwear`).
     - Preserves **100% original 2K RGB** (zero diffusion redraw distortion), excludes face/eyes/ears/hat/hands/clothes cleanly, sharpens outer hair tips at native 2K via 2nd-pass local-zoom `ToonOut`, filters disconnected lower-body false positives on `hair`, and optionally writes `--clean-plate` (0.04 s outer-background TELEA erasure strictly outside protected body/face/hat masks so animated hair/ponytails never double-ghost) plus `--json` (1920×1080 rig coordinates).
     ```bash
     python -X utf8 <sk>/scripts/vision/part_cutout.py web/assets/art/<id>.png web/assets/art/<id>_hair.png \
       --part hair --clean-plate web/assets/art/<id>_clean.png --json work/<id>_hair_rig.json
     ```
   - **Pixel-aligned clean plate / surgical edit composite (`scripts/vision/pasteback.py`)**: `--align` uses SIFT+RANSAC to cancel AI edit shift/scale drift; `--lf 40` matches low-frequency exposure across the seam (ideal for aligned closed-eye / gaze patches in `T3.her.eyes` or localized retouches):
     ```bash
     python -X utf8 <sk>/scripts/vision/pasteback.py orig.png edit.png diff out.png --align --lf 40 --region x0,y0,x1,y1
     ```
3. **Generate softened 16-bit depth maps** for shots marked `"needs_depth": true`:
   ```bash
   python -X utf8 <sk>/scripts/vision/depth.py web/assets/art/<id>.png work/<id>_depth_soft.png --bits 16 --soften
   ```
4. **Pack local fonts & CC0 textures**: run `scripts/fonts.py use <project> ...` (`--static` for stroked/outlined glyphs), stretch raw paper scans via `scripts/prep_texture.py`, copy chosen overlays from `<sk>/assets/textures/` into `web/assets/tex/`, and fetch any Blender 3D models/HDRIs via `scripts/assets3d.py get ... --project <project>`.
