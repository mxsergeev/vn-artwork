# Experiment 13 — document-reading pose

Creates a second full-body pose for the clerk: relaxed three-quarter stance, gaze lowered to a blank paper document, neutral expression, transparent background. The reviewed neutral pose is `static/poses/document_reading/neutral.png`.

Happy and shocked donors were edited from that exact pose with the built-in image editor's supported `referenced_image_paths` input. Happy uses a restrained smile; shocked uses widened eyes and a small surprised mouth. The neutral, happy, and shocked blink/talk donors were also source-referenced edits. Raw full-body donors shifted the head consistently; their features were translation-aligned to the neutral pose using OpenCV ECC on stable hair/face pixels, excluding eyes and mouth. The transforms and correlations are in `assets/donor_alignment.json`. Only small lossless feature crops are retained.

The first composite pass exposed hair and lash remnants because the donor face had shifted. Each expression now has independent left/right open-eye and blink contours; no expression reuses another's eye geometry. Each blink mask includes that expression's open-eye footprint plus its own closed-lid contour, so the open eye is fully removed. Small lash-tip shapes cover only the needed corners. The fringe guards follow the source strands: the right guard protects the short strand above the eye and stays off the upper lash line. After the latest 20× review, the Happy and Shocked lower edges were tightened to retain under-eye skin, and each donor and its mask were locally shifted together. Integer nearest-neighbor placement keeps the crop sharp. Local skin-only RGB offsets match donor color without tinting untouched pixels. No brow donor was used because its changes crossed the bangs.

Current local eye offsets (x, y), measured and then reviewed against surrounding hair and eyelid corners:

| Donor | Left eye | Right eye |
|---|---:|---:|
| Neutral blink | (0, 0) | (−2, 0) |
| Happy open | (0, 2) | (−1, 0) |
| Happy blink | (0, 2) | (−1, −1) |
| Shocked open | (2, 1) | (−2, 1) |
| Shocked blink | (2, 0) | (−2, 0) |

The shocked right blink previously sat four pixels above its open donor after local registration; it is now placed at the same horizontal anchor and one pixel above the open donor. The old right fringe rectangle crossed the upper lash at x608–611 while missing the actual strand at x605–606; it was replaced with a narrow strand guard. These changes were checked against the decoded GIF frames, not only the source PNGs.

## Visual diagnosis and acceptance

For each eye edit, review the source, locally aligned and color-matched donor, final composite, expression-specific feature mask, fringe guard, cleanup patch, and changed-pixel boundary together. `output/{neutral,happy,shocked}_{left,right}_eye_20x_review.png` creates that comparison at 20×; the last column calls out donor changes that would spill outside the approved feature and cleanup regions. Use the spill panel to investigate a seam, not as a reason to widen a mask automatically. Preserve source hair/brow strands with their guards, and add a separate cleanup patch outside the feature mask only when the decoded result shows a real join that needs it.

Use the decoded combined GIF as the final reference. The `output/gif_{neutral,happy,shocked}_{left_eye,right_eye,mouth}_20x.png` sheets show only the actual idle, talking, blink, and blink+talk frames at 20×; no in-between frames are generated. For a suspected one- or two-pixel defect, crop that exact coordinate from source, aligned donor, and final at 40× or higher, with a pixel grid. Extend that expression's mask only when the donor contains the intended feature and the result proves the contour clipped it. Remove detached donor specks; draw a tiny tapered lash only when the eyelid edge and adjacent colors support the stroke. Rebuild and inspect the encoded frames after every such change.

The latest 60× source/donor/result comparison found one dark donor pixel at destination (549, 150) that rose above the shocked-left upper lid as a square. The edit leaves that source-skin pixel in place, retains the connected lash contour, and asserts that the square point stays outside the shocked-left mask. The earlier isolated point at (557, 150) also remains excluded.

Shocked speech uses the softer `shocked_talk_mouth_v3.png` donor. Its mask clears both the original closed-mouth line and the entire shocked-O footprint before placing the smaller donor, so neither mouth leaves an edge behind. Happy speech fully replaces every pixel of the separately traced closed-smile footprint while feathering only the surrounding edge. The shocked blink also has independent left/right outside-mask seam cleanup patches: they carry the closed-lid donor across the short crease joins next to each eye, without expanding either feature mask into the fringe. The boxy and vivid candidates remain only as experiment comparisons and are not used by the build. GIF palette sampling gives extra weight to the eyes and mouth so native-size previews preserve those details.

Run from the repository root:

```bash
python experiments/13_document_reading_pose/build.py
```

The ignored `output/` directory contains generated states, three native-size GIFs per expression, an all-three-expression combined GIF, enlarged face/full-body previews, per-expression open/blink mask overlays, changed-pixel boundaries, and QA. The `gif_{neutral,happy,shocked}_{left_eye,right_eye,mouth}_20x.png` reviews are 20× crops decoded from the encoded combined GIFs themselves; `shocked_eyes_animation_20x.gif` animates the two shocked-eye crops at 20× from those same encoded frames. `shocked_blink_seam_masks_24x.png` distinguishes the shocked blink feature contours from the magenta outside-mask cleanup patches. `gif_{neutral,happy,shocked}_both_eyes_12x.png` shows both eyes together across all four encoded states for alignment review. The matching `{neutral,happy,shocked}_eye_masks_20x.png` reviews show each expression's distinct open and blink contours; `*_blink_mask_20x.png` provides the blink-mask overlay. The animation keeps four discrete states (idle, blink, talking, blink+talking) and adds no in-between frames. The build asserts 1086×1448 RGBA dimensions, exact source-alpha preservation, zero changed pixels outside expression-specific feature masks plus the two explicit shocked-blink seam patches, and successful full decoding of every encoded GIF frame before publication. QA reports those outside-feature seam edits separately. Reviewed copies are published under `static/animation/document_reading/`; Happy and Shocked idle poses are also under `static/poses/document_reading/`.

Prompt set: a natural relaxed stance with gaze at the held document; Happy with a warm closed-mouth smile; Shocked with widened eyes and a surprised open mouth; separate one-feature edits for natural blinks and speaking mouths. All edits used the actual local source image or its lossless face crop as an image reference.
