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
    "style_bible": "Cohesive colour palette, lighting direction, and medium shared across all generated shots"
  },
  "shots": [
    {
      "id": "act1_hero",
      "act": "act1",
      "provider": "gemini",
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

# 2. Preview what will be copied / generated without calling any API
python -X utf8 <sk>/scripts/art_gen.py run <project> --dry

# 3. Execute manifest (skips files that already exist unless --force)
python -X utf8 <sk>/scripts/art_gen.py run <project>

# 4. Verify every manifest asset exists on disk with valid dimensions
python -X utf8 <sk>/scripts/art_gen.py check <project>
```

---

## 3. Environment Variables for Optional Image APIs
| Variable | Provider | Purpose |
|---|---|---|
| `CHIAKI_IMAGE_API_URL` | `custom_api` | OpenAI-Images-compatible POST endpoint (e.g. `https://.../v1/images/generations`) |
| `CHIAKI_IMAGE_API_KEY` | `custom_api` | Bearer token for your custom image endpoint |
| `CHIAKI_IMAGE_MODEL` | `custom_api` | Model identifier expected by your endpoint |
| `GEMINI_API_KEY` | `gemini` | Google Gemini API key (optional model override `CHIAKI_GEMINI_IMAGE_MODEL`, default `gemini-2.5-flash-image`) |
| `OPENAI_API_KEY` | `codex` | OpenAI API key (optional model override `CHIAKI_OPENAI_IMAGE_MODEL`, default `gpt-image-1`) |

---

## 4. Visual Acceptance & Pre-Build Prep (Before Stage 5 Build)
Before handing assets to the 3D, Edit, and Design crafts:
1. **Inspect every plate at full size**: confirm zero unwanted gibberish text/watermarks, harmonious palette matching the pitch's hex tokens, and clear negative space where kinetic typography will sit.
2. **Prepare separated layers** (when a shot uses `lib/multiplane.js`, `T3.her.wave`, `projection/`, or `AL.emissive_card`): verify clean alpha edges with zero white/green fringe.
3. **Generate softened 16-bit depth maps** for shots marked `"needs_depth": true`:
   ```bash
   python -X utf8 <sk>/scripts/vision/depth.py web/assets/art/<id>.png work/<id>_depth_soft.png --bits 16 --soften
   ```
4. **Pack local fonts & CC0 textures**: run `scripts/fonts.py use <project> ...`, copy chosen overlays from `<sk>/assets/textures/` into `web/assets/tex/`, and fetch any Blender 3D models/HDRIs via `scripts/assets3d.py get ... --project <project>`.
