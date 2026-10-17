# Research history and archived methods

**Historical record only.** For new work, follow [README.md](README.md) and the successful experiments 09–11 instead. The notes below preserve early attempts, original prompts (where available), failures, and the proven static-expression method. Words such as "latest" or "current" in archived sections reflect their original time, not present recommendations.

## A. Proven static-expression pipeline — use this

**Exact historical inputs (not re-created):**
- Base RGBA sprite: `static/Melancholic Corporate Sci-Fi Officer.png` (1086×1448).
- Original 4×2 face donor sheet: `static/anime_character_expression_sheet_grid.png` (1402×1122).
- **Unmodified historical script:** `static/vn_expression_transplant.py`.
- All eight final PNGs: `static/sprites/01_neutral_worried.png` … `08_strained_smile.png`.

**Why it worked:** Eight coordinated portraits were generated *together*, then one affine alignment was applied across the sheet; a large feathered face polygon and median sampled RGB correction transferred eyes/brows/mouth together, leaving the original body, hair silhouette and alpha intact. Static sprites tolerate tiny facial motion; blinking/talking toggles do not.

**Reproduce and verify:**

```bash
pip install -r requirements.txt
cd static
python verify.py                  # safely regenerates in temp and pixel-compares all 8 + base
python vn_expression_transplant.py # optional: regenerates full PNG set/previews in static/
```

**Original generation prompt:** NOT preserved verbatim. Suggested reconstruction, **unverified**:

> Using the original clerk as character reference, generate one 4×2 grid of matching close-up portraits: neutral/worried, happy, shocked, pouty, angry, embarrassed, sad, strained smile. Keep identical head angle, framing, hair, earpiece, style and lighting. Vary eyes, brows and mouth naturally. No labels over the artwork.

The exact historical palette image is preserved; it is more reliable than this reconstructed prompt.

## B. Archived animation failures — experiments 01–03

The scripts in `experiments/01`–`03` reproduce unsuccessful approaches; **do not use their outputs as finished sprites.** They share the original sprites from `static/sprites/`. The newer pilot is in `experiments/04`.

**01. Aligned happy donor** — `experiments/01_aligned_happy_blink/build.py`
- Used existing neutral/happy sprite coordinates, per-eye polygons, protected foreground hair, short feather and conservative sampled skin color offsets.
- Technically decent alignment. **Rejected:** smiling/squinting eyelids and blush remain. Use masks/code for *ideas*, not the final eyelid asset.
- [Mask illustration](experiments/01_aligned_happy_blink/eye_mask.png).

**02. Independently generated donors** — `experiments/02_independent_donors/build.py`
- Generated separate closed-eye and talking portraits, then aligned with approximate affine transforms and local masks.
- **Rejected:** eyelids overflow the head and mouth is **horizontally LEFT of the original**. Checking only whether changes fall inside a programmer-defined mask is not meaningful visual QA.
- Prompt type (reconstructed): “Keep the same original character and expression; change only eyes to closed / mouth to open.” **Did not preserve geometry.**

**03. New four-panel palette** — `experiments/03_palette_retry/build.py`
- Prompt (reconstructed): “One aligned sheet: neutral; closed eyes (not smiling); small talking mouth; both; same face proportions, skin, brows, hair; no blush.”
- Four-panel composition looked coherent *within the generated sheet*, but did not align well to original art. New eyelids too thick; hair artifacts; reverted to happy blink; mouth still visibly jumps left in final comparison. **Rejected.**
- [`generated_palette_reference.jpg`](experiments/03_palette_retry/generated_palette_reference.jpg) is a compact visual reference, **not** an exact donor file. `assets/talk_donor.png` is the actual tested mouth donor.

All three archived experiment scripts are **historical algorithms with only file paths / redundant comparison references adapted** for this compact folder layout. Run each from its own folder (`python build.py`) to generate temporary results in its local `output/` directory.

## C. Source-anchored animation pilot — experiment 04 (Oct 2026)

**Key finding 1 — generate donors by editing the exact original sprite, not by free generation.** Pass the **actual PNG** (e.g. `static/sprites/01_neutral_worried.png`, or `02_happy.png` when working on Happy) **as the image-edit input**, request only the required feature change, and preserve face angle, hair, skin, pose, outfit and geometry. The AI result is a **donor**, not a finished replacement frame.

**Critical image-model handoff (verified Oct 16):**
1. Extract the original PNG from the ZIP to a **real, accessible file** and verify the exact path exists.
2. **Explicitly attach/forward that file as the image model's edit input/reference.** Merely inspecting it in Python, reading the ZIP, or mentioning its path in text does **not** forward its pixels.
3. Check the model actually received **that sprite**. On missing-input errors or unrelated-looking output, **stop and fix the handoff**; do not repeatedly generate from descriptions. A successful handoff does not guarantee a faithful edit.

**Color/lighting correction:** AI donors may be paler, rosier, brighter or differently shaded than the original. Before transplantation, sample **matching nearby skin-only areas** on original vs donor (exclude iris, hair, lashes, lips and shadows); estimate a modest per-channel RGB offset (median or locally smoothed/clamped offsets), apply only near the feature, and feather **inside a tight mask**. Preserve the source's alpha and untouched pixels. Compare skin/edge tones and toggle frames at normal size and 4–8× to catch seams/flicker. Color correction fixes shade mismatch, **not** eye/lip geometry or hair defects.

> Suggested prompts for future attempts (**templates, not recovered verbatim historical prompts**):
> - Eyes: “Edit the provided sprite only. Close both eyes as a neutral natural blink; keep mouth, brows, hair strands, earpiece, expression, pose, outfit and framing unchanged. No happy squint, smile or added blush.”
> - Mouth: “Edit the provided sprite only. Open the existing mouth visibly as if speaking, without smiling or shock. Keep eye shape, face, jawline, hair, pose, outfit and framing unchanged. Preserve the original mouth position.”

**Key finding 2 — transplant through the tightest feature-specific masks.**

- For **talking**: cover the open mouth and immediately adjacent lip shading only; never the chin/jaw. Require a visibly different shape while keeping the lip center fixed. The current **two-frame** talking pilot was positively assessed by the user.
- For **blinking**: separate per-eye masks covering eyelid/lashes and the **entire original open-eye/iris geometry** that must disappear. Small masks can expose old lashes; big masks import AI-redrawn hair or cheek. Where an eyelash meets hair, add a tiny lash-area extension **and subtract a protected hair notch**. Keep feathering *inside* each contour, around 1–2 source pixels (specific to sprite resolution).
- Correct donor skin tone locally, composite onto **original RGBA pixels**, leave all other pixels and alpha untouched. Do **not** attempt to hide geometric mismatch by growing the mask. A shape that intersects hair may still need manual editing even if its mask is tiny.

**Result and limits:** Mouth transplantation was easier than blinking. The current blink closes naturally at ordinary size but still has a small residual left-lash/edge artifact. **Manual finishing in Krita is an expected final stage**, not a failure of the general approach. Static-expression transplantation intentionally used a *broader face mask* (section A); do **not** transfer that mask design to animation frames.

**Reproduce pilot:**

```bash
pip install -r requirements.txt
python experiments/04_source_anchored_animation/build.py
# Results in experiments/04_source_anchored_animation/output/
```

The archived pilot supplies the exact source-anchored **closed-eyes donor** and an **approved talking PNG**. The script preserves the approved mouth frame, rebuilds the latest eye mask and outputs sprites, GIF previews, mask overlay, and numerical QA. The talking PNG is a completed transplant, **not a raw generated donor**. See [`previews/talk_preview.gif`](experiments/04_source_anchored_animation/previews/talk_preview.gif), [`previews/blink_preview.gif`](experiments/04_source_anchored_animation/previews/blink_preview.gif) and [`previews/left_mask_overlay.png`](experiments/04_source_anchored_animation/previews/left_mask_overlay.png). Any eye-mask coordinates are **hand-tuned for this exact character/pose**; automatic generalization is not established.

## D. Happy blink/talk prototype — experiment 05 (Oct 16, 2026)

`experiments/05_happy_animation/build.py` regenerates a four-state blink/talk experiment. **Happy's original eyes are CLOSED**, so it uses open eyes from the existing aligned neutral expression; the original Happy sprite itself is the blink frame. An alternate mouth is derived by shrinking the original smile vertically, at the same location. Masks are separate and tightly contoured; script includes local skin RGB correction, image previews, and pixel/alpha QA. The original files are never overwritten.

A separate `assets/ai_open_eyes_candidate.png` was generated **by actually forwarding the original Happy PNG to the image model**. It is a valid same-character edit attempt, but differs slightly in color and other pixels. **Untested as a transplant donor; not used in the prototype**, and not an approved replacement for the source artwork. Unrelated-image failures are excluded from this ZIP. Keep this single representative candidate, the reusable script, and compact previews, **not duplicate base sprites or discarded generations**.

```bash
python experiments/05_happy_animation/build.py
# Output: experiments/05_happy_animation/output/
```

See [`four-state comparison`](experiments/05_happy_animation/output/four_states_face_comparison.png), [`combined GIF`](experiments/05_happy_animation/output/combined_preview.gif), and [`experiment notes`](experiments/05_happy_animation/README.md). Open-eye emotional fit, hair/eyelash edges and mouth skin texture still require subjective review.

## Other approaches explored

Full layered puppets worked technically but required too much manual preparation. Live2D/Spine would also require separating and rigging the artwork. Neither was prioritized.

## What superseded the early animation pilots

- [Experiment 09](experiments/09_happy_imagen_mouth/README.md) replaced the Python-compressed Happy mouth with an image-model closed-smile donor.
- [Experiment 10](experiments/10_neutral_blink_refined/README.md) substantially reduced Neutral's left-lash cutoff and under-eye patches using tighter, eyelid-shaped masks.
- [Experiment 11](experiments/11_happy_eye_refined/README.md) applied the same disciplined mask refinement to Happy, using the **same eye donor** as earlier work. This is the preferred Happy animation example.
