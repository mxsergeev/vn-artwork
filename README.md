# VN artwork — working guide

Create poses, static expressions, and blink/talk animation while preserving character identity and intentional source artwork.

Read this workflow, then the relevant section of [EDITING_TECHNIQUES.md](EDITING_TECHNIQUES.md) and the selected experiment's status. Superseded work is indexed in [HISTORY.md](HISTORY.md).

## Inspect and resume

Identify the master pose, completed expressions, usable donors, current build, unresolved defects, visual review, and recorded user approvals. Inspect the actual images and current Git changes. Resume at the earliest unfinished stage; reuse approved artwork and suitable donors.

**File existence, mechanical integrity, visual review, and user approval are separate facts.** Record local inputs, defects, and status in the experiment README; identify exact artifacts and their provenance in `build.json`.

## Production workflow

| Stage | Action and completion evidence |
|---|---|
| Master pose | Reuse an existing pose, or edit the actual character image to create the requested pose. Review identity, proportions, clothing, framing, and transparency. |
| Expression donor | Edit that exact master to obtain an immediately recognizable emotion with anime-style exaggeration at normal display size. Reject subtle or barely changed expressions. Check the intended transplant region against the [donor-generation criteria](EDITING_TECHNIQUES.md#generate-and-select-donors). |
| Static expression | Align and transplant eyes, brows, mouth, and necessary facial shading onto the master. A broader face selection can be appropriate. Save the finished expression as its own source. |
| Animation donors | Starting from each finished expression, reuse or generate only missing eye/mouth states. Preserve the emotion while making open/closed states clearly distinguishable, following the donor-generation criteria. The generated image supplies donor features. |
| Four states | Build `idle`, `blink`, `talking`, and `blink_talking`. Keep the respective idle/speaking mouth when applying a blink. Reuse any state already represented by the source. |
| Diagnose and review | Start with one feature. Separate old-feature removal, donor insertion, and source foreground restoration. Inspect intermediate stages, final PNGs, and decoded GIFs. |
| Publish | Explicitly copy the selected reviewed candidate into `static/animation/`. Record actual user approval separately when given. |

When generating, pass the actual source through the editing tool's supported image-reference input. Inspect the real tool parameters; a path mentioned in a prompt or an assistant preview is not an image-model input. If the tool cannot access the required reference, obtain a supported attachment before generating. Preserve transparency in final assets. Assess donor quality within the intended transplant region: clothing, body, or background changes outside that region are irrelevant when those pixels will not be copied.

Finish each static expression before building its animation states. Derive those states from that finished expression so its brows, shading, and other expression features survive blink/talk edits. Demonstrate one clean feature transplant before building the full state set.

Select every donor by an explicit path. Do not search alternative folders or silently fall back to another file with the same name. Record the paths and hashes of the inputs actually loaded.

## Working references

| Task | Reference | Scope |
|---|---|---|
| Static expressions | [Historical transplant](static/vn_expression_transplant.py) | Exact reproduction of the original eight sprites; learn broad face alignment and palette matching. |
| Neutral blink | [10](experiments/10_neutral_blink_refined/README.md) | Feature contours, lash coverage, and retained under-eye skin. |
| Happy mouth / eyes | [09](experiments/09_happy_imagen_mouth/README.md) / [11](experiments/11_happy_eye_refined/README.md) | Generated mouth donor and subsequent eye refinement. |
| Shocked | [12](experiments/12_shocked_animation/README.md) | Independent eye and mouth transplants. |
| Layered composition | [Angry 14](experiments/14_angry_animation/README.md) | Skin replacement, donor lids, then original foreground restoration. |

Coordinates and thresholds belong to their images. A source-removal selection may be reused for variants of the same exact master; donor insertion follows each donor's geometry. No uniqueness requirement applies to masks.

## Commands and build records

Install `requirements.txt` in the Python environment used for builds. Commands below run from the repository root.

```sh
python -m pip install -r requirements.txt
python experiments/14_angry_animation/build.py
python experiments/verify_remaining_animations.py experiments/14_angry_animation/output --check-inputs
```

Write candidates to ignored experiment `output/` folders. Add an ignore rule for each new experiment's generated output.

Each final build records source, donor, script, PNG, GIF, region-mask, and review-image hashes after postprocessing. Review records stay attached to unchanged artifacts. A changed candidate requires renewed review; an unchanged rebuild does not erase recorded approval.

To render separate candidate previews:

```sh
python experiments/build_animation_previews.py --source experiments/14_angry_animation/output --output experiments/preview_output/angry
```

These detached previews are exploratory; rebuild the candidate to include its final GIFs in its manifest before reviewing/publishing. With no arguments, the preview script renders all existing default sets and a montage into `experiments/preview_output/`.

After actually inspecting a candidate, record what was reviewed:

```sh
python experiments/publish_artwork.py experiments/14_angry_animation/output --reviewed-by codex --review-note "Describe the inspected regions, decoded frames, outcome, and remaining defects."
python experiments/publish_artwork.py experiments/14_angry_animation/output --destination static/animation/angry
```

Replace the example review note with the actual inspection findings. Use `--approval-note` only to record an actual user statement; use `--not-approved-note` for rejected work. Existing authorization remains valid; do not ask again merely because publication is a separate command. The publisher checks artifact freshness and recorded visual review, and refuses explicitly unapproved artwork.

`python experiments/verify_remaining_animations.py` checks recorded published files without requiring ignored experiment outputs. Add `--check-inputs` when checking a candidate against its current builder. `python static/verify.py` remains the separate historical static-sprite reproduction check.

## Acceptance and repository hygiene

- Review normal-scale readability and fixed-coordinate enlarged crops. Inspect each eye, mouth, all four states, and actual encoded animation for seams, missing/duplicate lines, hair damage, and flicker.
- For a reported defect, show its location, the stage that introduced or preserved it, and a before/after proving that the correction reached the final image. Unchanged output is not a repaired output.
- After two failed attempts at the same defect, revisit the selection, operation order, or donor. Do not repeat contour adjustments without a new diagnosis.
- Integrity checks cover dimensions, decoding, original alpha, source identity, and writes outside declared feature/repair regions. They cannot approve artwork.
- Keep masters, essential donors, builders, selected final assets, and concise status records. Generated alternatives and enlarged review panels belong in ignored output folders. Do not overwrite established artwork as a side effect of building.

Find published sets in the [asset index](static/animation/README.md) and pose inputs in their local README, including [document-reading](static/poses/document_reading/README.md).

