# Programmatic sprite-editing techniques — required field guide

**Purpose:** Make precise expression, blink, and mouth edits without warping the source artwork. This guide complements [README.md](README.md). **Read it before implementing or refining any sprite edit. Diagnose the defect, select the applicable technique(s), then verify the pixels.** Do not treat a mask-only compositor as the whole editing workflow.

## 1. Diagnose before changing code

Study the **exact original sprite, donor, rendered result, and prior working states** together. At native size and 5×/10×/15×/20× (or more), check the eye corners, eyelid/lash contours, eyebrow placement, hair crossings, skin, mouth, and frame-to-frame stability.

| Symptom | First investigate | Preferred technique |
|---|---|---|
| Whole eyelid/lashes are offset | Donor landmarks vs. source landmarks | Independent **per-eye alignment** |
| Corners align but eyelid arc is wrong | Donor shape, not mask width | **Small local warp**, or a better donor |
| Hair or brow shifts/disappears | Foreground elements baked into donor | **Preserve original hair/brow as a foreground layer** |
| Open-eye lashes/iris remain behind blink | Original eye wasn't fully removed | **Background cleanup** plus correctly sized transplant |
| Lash tip is abruptly cut | Donor/mask coverage or missing artwork | **Extend the mask** or **draw a tiny replacement stroke** |
| Skin has a color rectangle/seam | Shade/lighting mismatch | **Local skin-only color matching** / selective retouch |
| Broken hair line or isolated glitch | A few damaged source pixels | **Clone/heal or precise drawing** |
| Eye looks unlike the original | Donor is fundamentally unsuitable | **Reject/regenerate donor** or reconstruct the specific lid |

**Stop repeatedly tuning polygon vertices if the donor's geometry is wrong.** A mask can choose pixels, but cannot correctly position or reshape a misaligned eyelid.

Use only techniques warranted by the observed defect; **not every technique is needed for every expression**. Record the defect, its cause, chosen operation, and before/after comparison. If a hypothesis fails, revisit the diagnosis rather than repeating the same kind of adjustment.

## 2. Prepare a suitable donor

- Prefer an image-edit donor made from the **actual matching source**, not a newly invented face. Keep original identity, hair, brows, color, pose, scale, alpha, and framing.
- Compare the donor with the source **before** constructing masks. Discard a donor with major anatomy/style changes; don't attempt to rescue it by shrinking the mask.
- Use source-anchored, lossless PNG crops with explicit original coordinates. Keep eye/mouth donors and their transformations separate.
- A good closed-eye donor only needs to provide a usable eyelid/lash feature: preserve original skin/hair wherever feasible.

## 3. Independently align each eye (before masking)

**When:** The donor eyelid or eyelashes are shifted relative to the eye corners or brows.

1. Identify corresponding landmarks in **source and donor**: inner/outer eye corners, lash anchor points, and useful brow/hair junctions. Inspect them visually; do not assume one fixed crop location fits every expression.
2. For each eye, estimate a **translation**, then rotate/scale only if needed. Use `cv2.warpAffine()`, or `cv2.estimateAffinePartial2D()` when sufficient reliable correspondences exist. Store transform parameters per expression/per eye.
3. Transform the **donor feature and its coordinates/mask together**. Align one eye at a time; avoid distorting hair or cheeks alongside the eyelid.
4. Compare landmarks and lash geometry again at 10–20× before deciding where the mask goes.

*Illustrative example, **not repository coordinates***: if the donor's corners are at (544,147) and (584,145), while the corresponding target corners are (540,145) and (580,143), shift the donor 4 px left and 2 px up.

**Caution:** A closed eye does not have an iris center to align with the open eye; use meaningful shared anchors. Wrong landmarks produce worse results than a small residual offset.

## 4. Locally reshape incompatible eyelids (only if needed)

**When:** Both corners now fit, but the donor's eyelid curve/height still differs.

- Keep the corner anchors fixed; move a few intermediate points to adjust the arc. E.g. lower the middle of the upper eyelid 2 px while keeping both endpoints.
- Use a small piecewise-affine transform, thin-plate spline, or controlled `cv2.remap()` displacement field **within the feature area**; inspect line thickness, lash taper, and antialiasing after resampling.
- Reject large deformations. A new donor or precise redrawing is usually better than aggressively stretching eyelashes.

**Not for:** An entire eye that is merely translated, or damage caused by replacing original hair.

## 5. Restore original hair and eyebrows above the donor

**When:** The donor redraws overlapping fringe, hair strands, or brows, causing shifting or seams.

Treat the composition as distinct layers, from top to bottom:

1. **Original foreground hair/brow pixels**, extracted with tightly traced alpha/coverage.
2. **Aligned donor eyelid/lashes**.
3. **Clean original skin/background**, without remnants of the open eye.

In Python, build the original foreground extraction from the source RGBA, with a **separate, precise hair/brow coverage mask**, then alpha-composite it *over* the donor. Reuse **original pixels**, not donor-rendered replacements, wherever original strands must stay exact. Use Pillow or NumPy alpha compositing.

Where hair partially covers the original open eye, preserve the hair first, then repair underlying exposed skin. If the source does not contain the hidden artwork, a small reconstruction may be necessary.

**Do not:** Just paste all original eye-region pixels above the donor: that will restore the old eye too. Do not confuse a foreground-protection mask with the transplant mask.

## 6. Remove old eye artifacts and repair background

**When:** Original iris, sclera, eyelashes, or mismatched skin remain visible beside/under the transplanted eyelid.

- Work **under the preserved foreground layer** and **before** adding the donor.
- For tiny skin gaps, sample nearby intact *source skin*, clone a comparable patch, interpolate a local gradient, or use `cv2.inpaint()` on a tightly defined defect.
- Preserve local shading; avoid smearing hair lines, brows, or lashes. Simple sampled gradients can outperform general-purpose inpainting on flat-shaded anime skin.

*Example:* A 6×3 px group of old eyelashes remains under the new closed lid. Reconstruct those skin pixels, composite the donor, and then restore original hair above it.

**AI inpainting:** A last-resort option for small regions with genuinely missing image content. It can invent inconsistent strokes or alter the style; inspect strictly.

## 7. Draw or retouch tiny missing details

**When:** A lash tip, eyelid corner, or hair segment is missing, broken, or sharply truncated.

- Find the intact endpoint, local tangent, color, and stroke width.
- Draw a short tapered Bézier or polyline segment with Pillow/OpenCV or a vector path rasterized at higher resolution, then downsample for antialiasing.
- Repair *only* the needed pixels and check normal-size readability and 20× contour quality.

*Example:* If a lash is cut off 3–5 px short of its intended tip, extend the stroke instead of enlarging the entire mask into nearby hair.

This is **precise local reconstruction**, not a request to redraw a whole AI-generated face with Python.

## 8. Match skin color and remove seams

**When:** Alignment and geometry are correct, but donor skin produces a patch or brightness transition.

1. Sample source/donor correspondence in **skin-only** regions surrounding the join. Exclude eyelids, irises, lashes, hair, brows, and lips.
2. Apply a small RGB offset or locally varying shading correction **to the donor skin only**; feather where appropriate.
3. Inspect light/dark backgrounds and the changed-pixel boundary. Where a remaining seam lies *outside* the main transplant mask, make a **separate, explicit local cleanup region**.

`cv2.seamlessClone()` / Poisson blending can help with broad smooth tonal transitions, but it may soften or discolor thin anime linework. Prefer constrained corrections around sharp lashes/hair; use seamless blending only after visual comparison proves it superior.

## 9. Masks still matter — but they are not the solution to every defect

- Trace **independent left/right eye and applicable mouth masks per expression/pose**, using *aligned* donor and original pixels. A shared code path is fine; shared mask shapes are not.
- Choose contours that remove the complete old feature and retain every new eyelid/lash/lip pixel. Keep untouched under-eye skin, brows, and hair.
- Feather minimally, preferably inward. Inspect both too-small masks (cropped lashes/old iris remains) and too-large masks (imported donor skin/hair).
- **Allow carefully scoped edits outside the main mask** when needed for hair restoration, skin repair, seam removal, or direct pixel retouch. Declare those as independent cleanup regions and record their purpose.
- Mechanical pixel-containment QA should ensure nothing changes outside the **union of intended feature regions and declared cleanup regions**, and check original transparency, donor bounds, dimensions, and unaffected content. Update any validator that assumes every legitimate edit must lie within the *old* feature mask; do not bypass validation or allow uncontrolled global edits.
- **`outside_feature_mask_pixels == 0` by itself is almost guaranteed for a mask-based compositor. It is not proof of visual correctness.** Distinct masks/hashes and pixel counts are not quality evidence either.

## 10. Required iteration and acceptance procedure

For **each** expression/pose/state being edited:

1. **Diagnose** the concrete defect on source, donor, and current result. Pick the targeted technique from §1, not a reflexive mask tweak.
2. **Align** the donor before tracing/updating the mask; preserve overlapping source hair/brows and reconstruct exposed background where required.
3. **Composite and retouch**: precise mask, local shape repair, color correction, or explicitly bounded cleanup as needed.
4. Save **real** review images: source / aligned donor / final composite / mask and protective layers / changed boundary / original-vs-result. Review both eyes separately and the mouth at **5×, 10×, 15×, 20×, or higher**, plus normal scale.
5. Inspect **all four PNG states** and blink/talk/combined GIFs. Compare frames at fixed coordinates to find movement, flicker, cropped lines, leftover old artwork, or hair/skin damage. Rebuild and reinspect after *every* change.
6. **Fail** any result with visible warping, eyebrow/hair mismatch, clipping, jarring color seam, or state-to-state misalignment. Compare before/after pixels; revert regressions. Mark an unresolved defect explicitly, rather than calling it verified.

**Suggested controlled experiment:** Fix only the **Angry right-eye blink** first. Compare (a) current mask-only result, (b) independently aligned donor, and (c) aligned donor + preserved original hair + targeted cleanup. Carry successful techniques to other expressions *only after* the actual frames visibly improve.

**Guiding principle:** `donor assessment → alignment → preserve foreground → clean background → transplant → targeted retouch → visual review`. Automated assertions certify file/integrity properties; **visual inspection certifies the artwork**. Python can implement the editing operations, but cannot guarantee that AI-selected landmarks, masks, or strokes are artistically correct.
