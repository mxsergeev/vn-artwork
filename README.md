# VN artwork workflow

Create **poses → expressions → blink/talk animations** without changing artwork that should stay the same. **Judge the actual images first**: a clean-looking result matters more than passing numerical checks.

This is the working guide. For compositing details, see [EDITING_TECHNIQUES.md](EDITING_TECHNIQUES.md). For past experiments, see [HISTORY.md](HISTORY.md).

## Start with the task

1. Find the **exact master** and existing assets. Check the pose/experiment README if one exists.
2. Decide what is needed: **new pose**, **new expression**, **animation**, or **repair**. Do only that work.
3. Work on candidate files under an experiment's ignored `output/` directory; do not overwrite a good source while iterating.
4. Inspect each meaningful result visually. Fix specific visible problems, not imagined numerical imperfections.
5. Deliver the actual images and their accessible paths. Commit/publish when the task requests it.

**Non-negotiable:** preserve character identity, art style, proportions, and all regions not meant to change. Preserve the chosen master's transparency. Keep a previous working candidate until the replacement is visibly better.

## 1. New pose (only when requested)

1. Supply the **existing character image as a real image reference** to the image generator. A file path typed in the prompt is not an attached reference; use the parameters actually supported by the tool. If reference editing is unavailable, report that limitation instead of pretending an unreferenced generation preserves identity.
2. Describe the requested pose and what must remain unchanged: character, face, clothing, style, proportions, and transparency. Body geometry **may change** to achieve the pose.
3. Inspect the full character and enlarged face/hands/clothing. Regenerate or locally fix visible problems.
4. Once accepted, save this pose as the **new master** and record its path in the pose README. Do not build expressions on a provisional pose.

A new pose is not a face transplant: don't force its face/body to fit the old pose's coordinates.

## 2. Expressions

**Always start from the selected pose master.** Generate an expression donor using that master as the image reference. Change eyes, brows, mouth, and supporting facial shading as the emotion requires; preserve pose and identity.

Image generation often shifts facial geometry even with a reference. **Do not simply paste the donor face at the same coordinates.** Use Python to transplant the expression onto the master:

1. **Inspect the donor at native size.** Reject malformed features, a wrong head angle, or incompatible line style *in the region you intend to copy*.
2. **Align it.** Mark corresponding anatomical landmarks (e.g. nose, eye corners, chin) on both images and check an overlay. Each independently generated donor needs its own alignment.
3. **Choose the edit.** Prefer one coherent face patch when the facial geometry and skin boundary match. Otherwise transplant separate eye/brow/mouth regions. Do not cut a feature in half just to hide misalignment.
4. **Remove obsolete features completely**, insert the intended donor pixels, match skin locally, then restore hair or other source foreground that crosses the edit.
5. **Inspect the final composite.** It must look like a single natural face, with no old eyes/mouth, duplicate brows, clipped lashes, hair fragments, visible seams, or smeared skin.

A static expression's **new brows belong to the donor**; do not restore neutral brows over them. Preserve only foreground elements that are meant to survive this particular edit.

Use the [technique guide](EDITING_TECHNIQUES.md#expression-transplant) when placement or compositing needs work. The original successful [expression compositor](static/vn_expression_transplant.py) and [runnable example](experiments/workflow_examples.py) demonstrate a registered broad face patch; their coordinates are **not** reusable on a new pose.

## 3. Blink and talking states

Build on the **finished expression**, never on Neutral or an unfinished donor. Generate/select donors referenced to that finished expression; transplant only the relevant feature.

| Final PNG | Eyes | Mouth |
|---|---|---|
| `idle.png` | Open | Resting |
| `blink.png` | Fully closed | Same resting mouth |
| `talking.png` | Same open eyes | Clearly speaking |
| `blink_talking.png` | Same closed eyes | Same speaking mouth |

- **Blink:** remove the whole old open-eye footprint, including lashes/iris; add clean closed lids. Keep the expression's brows, mouth and foreground hair.
- **Talk:** remove the whole old mouth, add one clearly different speaking mouth. Keep eyes and brows identical.
- **Combined:** apply both edits to the same finished base (or reuse a verified matching state). Hair, body, alignment and shading must not jump between frames.
- A closed eye has **no visible iris, sclera opening or leftover open-eye outline**. An opening during speech must be visibly different from the resting mouth.

Generate the four PNGs first. Then make `blink.gif`, `talk.gif` and `combined.gif` and **inspect their decoded frames**; GIF encoding can introduce colour changes or flicker.

The established [Angry layered-eye builder](experiments/14_angry_animation/angry_visual_blink.py) demonstrates repairing old eyes, inserting lids and restoring foreground hair/brows. Use its technique, **not its coordinates**.

## 4. Review and repair

At **native display size**, check the full character and face. At **4× or larger**, inspect eyes, brows, mouth, hair crossings, and all patch edges. Compare source, donor and final at identical coordinates.

If there is a problem:

1. Name the **visible defect and its location**.
2. Inspect the actual stages: alignment → old-feature removal → new insertion → foreground restoration.
3. Fix the **first stage causing it**; rebuild and compare against the previous best candidate.
4. If two fixes fail, reassess the method or donor rather than repeatedly changing blur/mask values.

**Do not accept:** ghost features, displaced anatomy, doubled lines, clipped lashes/strands, smeared skin, seam edges, changed transparency, wrong states, or animation flicker. Automated diff/hash/mask checks verify integrity, **not visual quality**.

No independent subagent or specific model is required. The agent doing the work must inspect its own result honestly. Don't label visibly flawed or uninspected art as finished.

## 5. Save and publish

- Keep the approved master, selected donors, reproducible builder, and final PNGs. Keep disposable comparisons and failed iterations under ignored `output/`.
- For animations, use [`finish_animation`](experiments/artwork_tools.py) to write four PNG states, three GIF previews and `build.json`. Builder-specific commands are in each experiment README.
- Before publishing, run `python experiments/verify_remaining_animations.py experiments/YOUR_EXPERIMENT/output --check-inputs` and visually inspect the candidate. Existing [`publish_artwork.py`](experiments/publish_artwork.py) requires a **self-completed visual review file** for the six built-in checks; this is a publication-format requirement, **not a separate reviewer**. Run it with `--review-template`, fill the observations/evidence from actual images, record with `--reviewed-by <agent> --review-file <file>`, then publish with `--destination static/animation/NAME`.
- Never claim user approval unless it was actually given. Don't create a second approval requirement when the user already explicitly authorized publication.
- For individual fixes or experiments, **do not force the entire animation/publishing process**. Deliver the changed image and explain any remaining defect briefly.
- If committing to GitHub, verify that the files are actually in the remote repository. Never present an inaccessible local path as a download.

## References

- [Detailed editing techniques](EDITING_TECHNIQUES.md) — use when doing or debugging transplants.
- [Working compositing helpers](experiments/artwork_tools.py) and [reproducible examples](experiments/workflow_examples.py).
- [Published animation index](static/animation/README.md) and [reading-pose master](static/poses/document_reading/README.md).
- [Research history](HISTORY.md) — historical results/failures, **not** current operating rules.

Install `requirements.txt` when running Python builders. From the repository root, use `python -m unittest discover -s experiments/tests -v` when changing shared code; don't rerun the whole suite merely to tweak a sprite.
