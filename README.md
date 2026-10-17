# VN artwork — working guide

**Goal:** produce consistent visual-novel character expressions, blinking, and talking frames while preserving the original sprite's identity, hair, skin, pose, clothing, alignment, and transparency.

**AI: start here.** Follow this workflow before trying an older experiment. The highest-quality animation references are:

| Study first | What to learn |
|---|---|
| [12 — Shocked blink and speech](experiments/12_shocked_animation/build.py) · [preview](experiments/12_shocked_animation/preview.jpg) | Source-referenced eye and mouth donors, tight masks, alpha-preserving frames, and reviewed GIFs |
| [11 — refined Happy eyes](experiments/11_happy_eye_refined/build.py) · [preview](experiments/11_happy_eye_refined/preview.jpg) | **Best Happy eye result**: redraw per-eye masks, preserve under-eye skin, extend only the needed lash tip, protect outer-right hair |
| [10 — refined Neutral blink](experiments/10_neutral_blink_refined/build.py) · [preview](experiments/10_neutral_blink_refined/preview.jpg) | The cleanup technique that fixed lash cutoff and pale under-eye patches |
| [09 — natural Happy mouth](experiments/09_happy_imagen_mouth/build.py) · [preview](experiments/09_happy_imagen_mouth/preview.jpg) | Transplant an **image-generated** closed-smile donor instead of deforming the original mouth |
| [13–17 — remaining expression animations](experiments/build_remaining_animations.py) | Five expression-specific blink/speech builds with separate masks and source-state reuse |
| [Static-expression pipeline](static/vn_expression_transplant.py) | Separate, **proven** method for eight non-animated expressions; larger face masks are appropriate *only* there |

Read the relevant ~build.py~ and short experiment README before editing. **Copy the approach, never another expression's mask coordinates.** Historical attempts and failures: [HISTORY.md](HISTORY.md).

## 1. Set up and inspect

```bash
pip install -r requirements.txt
python static/verify.py
python experiments/10_neutral_blink_refined/build.py
python experiments/11_happy_eye_refined/build.py
python experiments/12_shocked_animation/build.py
python experiments/build_remaining_animations.py
python experiments/build_animation_previews.py
# Experiment output/ directories are temporary and ignored by Git.
```

Reviewed, published states are stored under `static/animation/{neutral,happy,shocked,pouty,angry,embarrassed,sad,strained_smile}/` as `idle.png`, `blink.png`, `talking.png`, and `blink_talking.png`. Regenerate the published GIFs from these states with `python experiments/build_animation_previews.py`: each expression gets blink, speech, and combined previews at the source sprite's 1086×1448 resolution, plus `static/animation/all_expressions.gif`, a labeled 3×3 face montage that animates all eight expressions together. PNG state files preserve the source alpha. GIF previews use a fixed opaque light-gray background because GIF transparency cannot retain the sprites' antialiased alpha.

Sources: `static/sprites/01_neutral_worried.png` through `08_strained_smile.png`, all 1086×1448 RGBA. **Never overwrite these sources.** Reuse an original sprite for any state it already represents: Neutral, Pouty, and Sad `idle.png`; Angry, Embarrassed, and Strained Smile `talking.png`; Shocked `idle.png`; and Happy `blink_talking.png` (closed eyes with the original open smile). Experiments 13–17 document the mouth-state choice and expression-specific masks for the remaining five expressions.

For each feature, inspect **source sprite, candidate donor, existing result, and reference masks** at native size and 4–8×. Determine the exact source features to remove, desired donor features to retain, and hair strands crossing the edit.

## 2. Generate a donor using the actual original image

**Mandatory image-reference check — never generate without the actual source image attached to the editor:**

1. Retrieve and verify the exact original sprite PNG. **Inspect the editing tool's real input parameters** before invoking it.
2. **Direct reference-image input available** (for example, `reference_image_paths` in a tool that actually exposes it, such as some Work environments): pass the original PNG through that supported reference-image input and proceed with the edit. Do not assume a mode supports a parameter without checking.
3. **Chat mode, or no supported direct file-reference input:** **STOP and ask the user to upload the necessary original PNG(s) themselves as image attachments in their next message. Do not generate anything yet.** If the user has already attached those images directly, use them instead of asking again.
4. After the user's images are attached, edit **those actual image inputs**. If the editor still cannot access them as references, **STOP and explain the limitation**. Never substitute a text description, a lookalike, or an unrelated expression sheet.

An assistant-rendered PNG, Markdown `![...](sandbox:/...)` link, local path, GitHub URL, or tool preview **does not prove the image was passed to the editing model**. The previously documented two-message *assistant-render → user proceeds* handoff is **not a reliable substitute for a real image reference**. Never claim a reference parameter was used unless the actual call confirms it.

**Donor rules:**

1. Ask for **one narrowly specified change**: eyes open/closed for a blink, or a natural open/closed speaking mouth. Keep head angle, eyelash style, face proportions, eyebrows, hair, skin tone, lighting, lips' position, clothing, pose, framing, and transparent background unchanged. No new blush or altered emotion unless explicitly desired.
2. Inspect the returned image against the source. Reject major geometry, alignment, emotion, hair, or style differences; regenerate or use a better donor. **The generated image is only a donor, not an animation frame.**
3. Existing aligned donors should be reused if their feature is good. The major improvement from Happy 09 to 11 required **no new eye generation**.

Suggested eye prompt: “Edit this exact supplied sprite: [open/close] the eyes naturally while preserving the character, eyelash style, facial expression, brows, hair strands, skin, mouth, pose and framing. Change nothing else.”

Suggested mouth prompt: “Edit this exact supplied sprite: make the mouth [naturally closed in a gentle smile / visibly open for speech], keeping its position, corners, jawline, cheeks and all other features fixed.”

If only a small donor region is needed, store a lossless crop **with its original x/y placement recorded in code**; experiments 09 and 11 reconstruct the donor using ~closed_smile_patch.png~ (67×55 at x=510–576, y=165–219).

## 3. Transplant with per-image, anatomy-following masks

**Central rule: the smallest mask that COMPLETELY replaces the necessary feature — not the smallest mask possible.** A broad mask imports AI-redrawn cheek/skin/hair and creates color patches. An undersized mask cuts lashes or leaves old iris/eyelid remnants.

**Eyes:**
- Trace independent **left and right** polygon contours against the actual original/donor pixels. Include *all* source iris/lash/eyelid pixels that must disappear and the complete donor eye/lash geometry. Don't start with a guessed ellipse.
- Set **upper and lower boundaries separately**. Trim the lower contour especially carefully: keep original under-eye shading and cheek skin wherever possible.
- For an exposed lash corner, add a **tiny separate lash-tip polygon** instead of enlarging the entire eye mask. Subtract/protect nearby hair if it crosses the feature.
- In an explicitly identified outer hair/eye region, retain original pixels where donor differences are small and visually unnecessary; inspect for accidental remnants. Example in experiment 11: a constrained RGB-difference threshold, **not** a generic rule for other faces.

**Mouth:** cover the new lip/inner-mouth geometry and just enough surrounding shading; keep lips centered, chin/jaw, cheek, and hair untouched. A compressed/drawn mouth is **not** a substitute for a convincing image-generated donor.

**Compositing:** feather **inside** the mask (approximately 1–2 original pixels as a starting point), never expand blindly into surrounding skin. Apply small, locally estimated RGB offsets from nearby **skin-only** pixels if donor shade differs (exclude eyelashes, irises, hair and lips). Keep source RGBA alpha and every outside-mask pixel unchanged. Adjust color separately from alignment and mask geometry. Follow the exact code in experiments 10/11.

## 4. Systematic iteration — required, not optional

1. Make a **candidate mask overlay on the source**, alongside source, donor, and current/previous frame. Check every eye/lash and hair intersection.
2. Transplant; save a real rendered full sprite and **4–8× eye/mouth crops**. Open and examine them — do not assess the result from code or QA numbers alone.
3. Produce and inspect the **changed-pixel boundary** overlay. A wide halo beneath an eye or along hair often means excess replacement.
4. Compare **at least a few meaningful variants** when defects remain (e.g. thinner lower-right contour vs fuller upper lash vs separate lash-tip extension). Change one cause at a time; compare the actual images side by side. Don't blindly shrink every polygon.
5. Inspect blink/talk/**combined** animations and individual frames at normal scale and on light/dark backgrounds. Look for eye or mouth shifts, color flicker, hair loss, eyelash clipping, leftover source eyes, unnatural bags, and expression mismatch.
6. Record the concrete defect and refine its specific mask, donor alignment, or local color. Inspect again after every change. Only stop when no obvious visual issues remain and additional automated iterations give negligible gains, or a clearly documented technical limitation blocks them. Suggest manual Krita work **only after** genuine automated iteration reaches that limit.

**Case study:** experiment 10 improved the Neutral left eyelash using its own small extension and preserved under-eye skin. Applying that *method*, with newly drawn polygons, to experiment 11 improved Happy using **the same donor as 09**. The latest under-eye refinement changes **1,384** eye pixels, down from **1,860** (~26% fewer); this is corroborating evidence of a narrower edit, **not** a target metric or proof of quality. Visual comparison remains decisive.

## 5. Validate and deliver

- **Mechanical QA:** same dimensions, original alpha exactly preserved, changes confined to intentional feature regions, untouched hair/body pixel-identical; run the relevant ~build.py~ assertions.
- For experiments 13–17, run `python experiments/verify_remaining_animations.py` after copying the reviewed output files into `static/animation/`.
- Regenerate and validate the large published GIFs with `python experiments/build_animation_previews.py` and `python experiments/verify_remaining_animations.py`.
- **Visual QA (decisive):** source vs result at normal size and 4–8×, mask and changed-boundary overlays, light/dark backgrounds, all animation states and GIF playback. Mechanical QA alone cannot detect a *bad mask*.
- **Preserve all four states** as applicable: eyes open/closed × mouth open/closed. For Happy, the original closed-eye/open-mouth combination needs no synthetic replacement.
- **Be precise about status:** distinguish a promising result from a visually reviewed one and from user approval. If an artifact remains, say exactly where and why.
- **Project hygiene:** track the reviewed final PNG states, supported GIF previews, and compact index preview under `static/animation/`. Keep generated experiment `output/` frames, GIFs, masks, and QA ignored by ~.gitignore~; publish only the selected reviewed copies. Commit source scripts, essential cropped donors, and concise experiment notes as needed. No throwaway test images, duplicate full-body donors, extra instructions, or ZIP bundles in the repository.

## 6. Static expressions and historical research

The eight static expressions in ~static/sprites/~ were produced from one coordinated 4×2 expression sheet using aligned, feathered **broader face transplants**. This pipeline is distinct from animation: static frames tolerate small facial differences while blink/talk toggles expose every mismatch. Verify it with ~python static/verify.py~.

The remaining five animation sets are experiments 13–17: Pouty, Angry, Embarrassed, Sad, and Strained Smile. Their cropped donors, source coordinates, per-expression masks, and build notes are versioned; `python experiments/build_remaining_animations.py` regenerates their four PNG states and review GIFs under each ignored `output/` directory. The publisher script rebuilds the tracked, native-resolution previews from the four PNG states.

For original prompts, archived experiments 01–05, failures to avoid, and early lessons, see [HISTORY.md](HISTORY.md). That document is historical; **this README plus the experiment 10/11 scripts are authoritative for new animation work**.

