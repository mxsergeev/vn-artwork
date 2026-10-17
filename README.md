# VN art workflow

**Purpose:** Experiment with AI-assisted character artwork generation and manipulation, particularly consistent expressions, blinking, and talking sprites. This repository preserves reusable methods, scripts, source assets, prototypes, and lessons from failed attempts; it is independent of any application using the artwork.

**Start here.** `static/` contains the proven eight-expression workflow; `experiments/01`–`03` document failed animation attempts; **`experiments/04_source_anchored_animation/`** is the neutral mouth/blink pilot; **`experiments/05_happy_animation/`** is the latest Happy experiment. Original sprites and shared inputs are not duplicated.

## Status (read first)

| Work | Verdict | Evidence |
|---|---|---|
| Eight static expressions | **PROVEN**: all eight regenerate pixel-identically | [`static/expressions_overview.jpg`](static/expressions_overview.jpg) |
| Closed eyes borrowed from happy expression | **PARTIAL**: aligned eyelids, but wrong smiling squint and lingering blush | [`experiments/01_aligned_happy_blink/comparison_4x.png`](experiments/01_aligned_happy_blink/comparison_4x.png) |
| Independently generated blink + talking donors | **FAILED**: eye patch beyond face/head; talking mouth shifted **LEFT** and jumped | [`experiments/02_independent_donors/rejected_by_user.png`](experiments/02_independent_donors/rejected_by_user.png) |
| New four-state palette + two overlays | **FAILED AS FINAL**: heavy lashes/hair artifacts, happy-blink fallback/blush, mouth still shifts left | [`experiments/03_palette_retry/rejected_final_4x.png`](experiments/03_palette_retry/rejected_final_4x.png) |
| Original-anchored, neutral **talking** donor + tight lip mask | **USER-APPROVED pilot**: noticeable opening, mouth anchored, jaw preserved | [`experiments/04_source_anchored_animation/previews/talk_preview.gif`](experiments/04_source_anchored_animation/previews/talk_preview.gif) |
| Original-anchored **closed eyelids** + contoured per-eye masks | **NEARLY WORKING**, not final: substantial improvement, residual left lash/edge artifact; manual finishing still needed | [`experiments/04_source_anchored_animation/previews/blink_preview.gif`](experiments/04_source_anchored_animation/previews/blink_preview.gif) |
| Happy open-eye blink + smaller talking mouth | **PROMISING PROTOTYPE**, not final/approved; uses existing aligned eyes and original Happy mouth; first directly-edited AI donor archived separately and not yet transplanted | [`experiments/05_happy_animation/output/four_states_face_comparison.png`](experiments/05_happy_animation/output/four_states_face_comparison.png) |

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

## E. Mandatory per-image transplantation and visual QA discipline

**Every source/donor pair is unique.** Never reuse or shrink a generic eye/face mask blindly. Analyze the original and donor at native size and 4–8×, separately for each eye/mouth: trace the *complete* replacement feature (including source iris/lashes that must disappear), identify protected hair strands and skin, then design independent, anatomically justified contours. Measure coordinates from the pixels, not a guessed ellipse. Donor alignment/fit and local skin tone must be evaluated separately from mask geometry.

**For every iteration, without exception:**
1. Inspect the original, donor, and candidate mask overlays (including hair-intersection details) before compositing.
2. Transplant using tight feature-specific masks, minimal feathering, preserved source alpha, and only necessary local color correction. Never enlarge a mask merely to hide a geometry mismatch.
3. **Open and inspect the actual rendered sprite** at normal size and 4–8×, on light and dark backgrounds. Do not infer quality from numerical QA.
4. Compare original vs candidate with aligned overlays, difference/highlight maps, and toggled layers. Pay special attention to *unintended* changes in hair, eyelids, cheeks, jaw, and shading, and also to old eye/lash remnants or feature cutoff.
5. Examine the animated blink/talk/combined frames, ideally as GIFs and frame-by-frame. Check flicker, facial motion/warping, mouth centering, and emotional consistency.
6. Identify concrete defects, adjust **that image's** mask/donor alignment/color correction, regenerate, and repeat. Inspect again after each change; a newly introduced defect invalidates the iteration.
7. Stop only when visual comparisons show no obvious defects and successive automated refinements give negligible benefit **or** remaining defects cannot reasonably be corrected with these tools. Report remaining artifacts honestly. Suggest localized Krita cleanup **only after** serious automated iteration reaches that plateau.

**Acceptance is visual, not just mechanical.** Alpha preservation, pixel confinement, and numerical measurements are mandatory sanity checks, **not** evidence that the artwork is clean. Do not hand premature prototypes to the user for discovery of obvious defects. The user remains the final artistic judge; never label an unreviewed animation “approved” or “perfect.”

## F. Masking breakthrough — refined Neutral and Happy experiments

**Key finding: improve the mask before regenerating the donor.** The much cleaner Happy eyes came from reusing the **same source-anchored AI eye donor** with more accurate eye-specific masks. Neutral refinement (experiment 10) demonstrated the method; Happy refinement (experiment 11) confirmed it on a different expression. These newer experiment folders are **local working results, not yet committed to this repository**.

**The rule: use the smallest mask that fully replaces the required feature.** This is *not* the smallest mask possible.

- **Too broad:** imports donor skin, cheeks, and hair, causing under-eye color patches, warping, and flicker.
- **Too narrow:** clips eyelids/lashes or leaves original eye/iris remnants.
- **Correct:** trace each actual eye separately; keep its entire required eye shape, but preserve as much surrounding original skin/hair as possible. Adjust the upper and lower boundaries independently.

**Reproducible tactics from experiments 10–11:**
1. Review source, donor, previous transplant, mask overlay, and **changed-pixel boundary** at 1× and 4–8× *before* editing. A wide halo below the eye is a warning.
2. Use a tightly traced main eyelid polygon; when necessary, add a **tiny, separate lash-tip polygon** rather than enlarging the whole mask.
3. Raise/trim the **lower boundary independently** to preserve original under-eye shading, without cutting the donor iris or eyelid. Protect crossing hair specifically.
4. Where the donor introduces only minor unwanted differences around a protected outer hair/eye boundary, selectively retain original pixels. Keep this constrained to the region and verify it doesn't damage the actual eye.
5. Re-render, compare full face and zoomed crops, overlay changed-pixel edges, inspect blinking/talking GIF frames, and revise. A smaller changed-pixel count is a useful indicator **only if the full feature remains intact**.

**Concrete Happy comparison (same eye donor):** experiment 09 changed **1,860** eye-frame pixels; experiment 11 changed **1,489** (about 20% fewer). Visual inspection, not the count, established that 11 preserved more surrounding skin without obvious clipping. The right eye's lower contour was especially important.

**Mouth lesson:** Compressing or drawing a closed smile with Python produced awkward lip geometry. A **direct source-image edit using the image model** produced a natural closed-Happy-smile donor; transplant only the lip region, keeping the original open-mouth state for talking. The image model must actually receive the original PNG, not merely a path or written description.

**Never transfer mask coordinates between expressions.** Transfer the *inspection and refinement process*. Only suggest manual Krita finishing when automated, visually inspected refinements have genuinely plateaued.

## G. Acceptance rules / next work

1. Judge donor emotion/pose **and** transplant quality independently; the former may look right while the latter leaks pixels.
2. Compare base vs transplant at normal size **and** 4–8×, on both light and dark backgrounds. Toggle as GIF or video: static side-by-sides miss flicker.
3. Reject wrong emotion (happy squint on neutral, shocked mouth), weak mouth delta, drifting mouth, incomplete iris/lashes, hair leakage, jaw changes, or palette artifacts.
4. Pixel checks (alpha identical; changed pixels confined to mask; mouth location stable) are **necessary but insufficient**; masks can contain unwanted hair and a leftover lash can be outside the mask.
5. Iterate on eyelash/hair intersections automatically first; use Krita only after further automated refinements plateau. Validate the combined speaking + blinking frames. Test other expressions/poses separately before promising automation.
6. Keep the proven static-expression pipeline as a reliable fallback while animation techniques remain experimental.

Other explored methods: full layered puppets worked technically but were too manual; Live2D/Spine require artwork separation and rigging. Neither is a current priority.
