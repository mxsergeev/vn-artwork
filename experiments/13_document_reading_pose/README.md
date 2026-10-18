# Experiment 13 — document-reading pose

Creates a second full-body pose for the clerk: relaxed three-quarter stance, gaze lowered to a blank paper document, neutral expression, transparent background. The reviewed neutral pose is `static/poses/document_reading/neutral.png`.

Happy and shocked donors were edited from that exact pose with the built-in image editor's supported `referenced_image_paths` input. Happy uses a restrained smile; shocked uses widened eyes and a small surprised mouth. The neutral, happy, and shocked blink/talk donors were also source-referenced edits. Raw full-body donors shifted the head consistently; their features were translation-aligned to the neutral pose using OpenCV ECC on stable hair/face pixels, excluding eyes and mouth. The transforms and correlations are in `assets/donor_alignment.json`. Only small lossless feature crops are retained.

The first composite pass exposed hair and lash remnants because the donor face had shifted. Each expression has independent left/right open-eye and blink contours; no expression reuses another's eye geometry. Each blink mask includes its expression's open-eye footprint plus its own closed-lid contour, so the open eye is fully removed. Small lash-tip shapes cover only the needed corners. The fringe guards protect hair outside the eye edit; traced foreground strands that cross an eye are allowed to have donor pixels placed underneath them, then the exact source RGBA pixels are composited back on top. This is done with separate per-expression, per-eye masks for Neutral, Happy, and Shocked. The source hair selection uses hand-traced paths plus a brown/charcoal color gate to reject shaded skin. The build records how many donor pixels are actually replaced beneath each strand. Local skin-only RGB offsets match donor color without tinting untouched pixels. No brow donor was used because its changes crossed the bangs.

The initial Happy and Shocked open-eye donors left jagged upper lashes at sprite scale. They were replaced with new edits referenced to the neutral pose. The 40× source/donor comparison was used to register each eye independently. Their open-eye masks include the exact source open-eye footprint, clearing old lash pixels outside the new donor's contour. A later visual review found visible skin seams at the eye joins. The treatment now locally matches donor skin throughout each feature patch, fades the last three source pixels into the exact original skin, and extends a stronger skin-only blend three pixels outside the mask. These corrections exclude linework and the preserved fringe. Foreground strand selection retains lighter brown antialiasing within the hand-traced paths, then restores the original source pixels above each donor. Each lid and lash remains its own aligned donor feature; no whole-face warp or blanket blur is used.

Current local eye offsets (x, y), measured and then reviewed against surrounding hair and eyelid corners:

| Donor | Left eye | Right eye |
|---|---:|---:|
| Neutral blink | (0, 0) | (−2, 0) |
| Happy open | (0, 0) | (0, 0) |
| Happy blink | (0, −1) | (0, −1) |
| Shocked open | (0, 0) | (0, 0) |
| Shocked blink | (0, −1) | (0, −1) |

The shocked right blink previously sat four pixels above its open donor after local registration; it is now placed at the same horizontal anchor and one pixel above the open donor. The old right fringe rectangle crossed the upper lash at x608–611 while missing the actual strand at x605–606; it was replaced with a narrow strand guard. These changes were checked against the decoded GIF frames, not only the source PNGs.

## Visual diagnosis and acceptance

For each eye edit, review the source, locally aligned and color-matched donor, final composite, expression-specific feature mask, fringe guard, cleanup region, and changed-pixel boundary together. `output/{neutral,happy,shocked}_{left,right}_eye_20x_review.png` creates that comparison at 20×. The cleanup overlay shows the skin-only treatment inside and outside the feature contour. Review the actual decoded GIF crops at 20× and use 40× or higher for seams; do not rely on pixel counts as quality evidence. Preserve source hair/brow strands with their guards, and keep any cleanup confined to the visible skin join.

Use the decoded combined GIF as the final reference. The `output/gif_{neutral,happy,shocked}_{left_eye,right_eye,mouth}_20x.png` sheets show only the actual idle, talking, blink, and blink+talk frames at 20×; no in-between frames are generated. For a suspected one- or two-pixel defect, crop that exact coordinate from source, aligned donor, and final at 40× or higher, with a pixel grid. Extend that expression's mask only when the donor contains the intended feature and the result proves the contour clipped it. Remove detached donor specks; draw a tiny tapered lash only when the eyelid edge and adjacent colors support the stroke. Rebuild and inspect the encoded frames after every such change.

The earlier Shocked donor needed hand-added upper-lash pixels; those coordinates were specific to that donor and were removed during replacement. The current review compares each eye at 20× and the encoded combined GIF crops at 20×, with the generated face sheet checked at normal scale. The original foreground-hair traces remain separately layered above the transplanted eyes, and decoded Happy blink crops retain the existing reviewed closed-lid treatment.

Shocked speech uses the softer `shocked_talk_mouth_v3.png` donor. Its mask clears both the original closed-mouth line and the entire shocked-O footprint before placing the smaller donor, so neither mouth leaves an edge behind. Happy speech fully replaces every pixel of the separately traced closed-smile footprint while feathering only the surrounding edge. The shocked blink has independent left/right feature contours; its edge treatment follows the same skin-only local matching used on the other expressions. The boxy and vivid candidates remain only as experiment comparisons and are not used by the build. GIF palette sampling gives extra weight to the eyes and mouth so native-size previews preserve those details.

Run from the repository root:

```bash
python experiments/13_document_reading_pose/build.py
```

The ignored `output/` directory contains generated states, three native-size GIFs per expression, an all-three-expression combined GIF, enlarged face/full-body previews, per-expression open/blink mask overlays, changed-pixel boundaries, and QA. The `gif_{neutral,happy,shocked}_{left_eye,right_eye,mouth}_20x.png` sheets are 20× crops decoded from the encoded combined GIFs; they show idle, talking, blink, and blink+talk. The `gif_{neutral,happy,shocked}_{left_eye,right_eye}_40x.png` sheets show the actual encoded idle and blink frames at 40× for skin-join inspection. `shocked_eyes_animation_20x.gif` animates the two shocked-eye crops from those same encoded frames. `gif_{neutral,happy,shocked}_both_eyes_12x.png` shows both eyes together across all four encoded states for alignment review. The matching `{neutral,happy,shocked}_eye_masks_20x.png` reviews show each expression's distinct open and blink contours; `*_blink_mask_20x.png` provides the blink-mask overlay. The animation keeps four discrete states (idle, blink, talking, blink+talking) and adds no in-between frames. File-integrity checks protect dimensions, alpha, bounded edit regions, and GIF decoding; visual acceptance comes from reviewing the decoded 20× and 40× frames. Reviewed copies are published under `static/animation/document_reading/`; Happy and Shocked idle poses are also under `static/poses/document_reading/`.

Prompt set: a natural relaxed stance with gaze at the held document; Happy with a warm closed-mouth smile; Shocked with widened eyes and a surprised open mouth; separate one-feature edits for natural blinks and speaking mouths. All edits used the actual local source image or its lossless face crop as an image reference.
