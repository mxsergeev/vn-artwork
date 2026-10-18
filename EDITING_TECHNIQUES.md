# Artwork transplantation and repair

Use this with the [production workflow](README.md). Diagnose the actual pixels before selecting an operation. Work on one eye or mouth until its correction is demonstrated, then extend the method.

## Generate and select donors

### Define the expression and state

Generate clearly readable emotions with **anime-style expressiveness** at the intended display size. Coordinate brows, eyes, and mouth as needed for the requested emotion while preserving character identity and rendering style. A recognizable happy smile is sufficient for Happy; maximum intensity or dramatic changes to every feature are not required. Define the emotion and the required eye/mouth state separately.

| Feature | Required appearance |
|---|---|
| Expression | Clearly recognizable requested emotion: Happy looks happy, Shocked looks surprised, Angry looks angry, and Neutral remains neutral. Stop increasing intensity once the expression reads clearly at the intended display size. |
| Open eyes | Visibly open; an expression-specific squint is acceptable only if it reads clearly as open. |
| Closed eyes | Fully closed lids, with no visible iris or eye opening. Preserve the expression through lid shape and brows. |
| Resting / `closed_mouth` | Closed or barely parted. Shocked may have a tiny opening, but must remain clearly distinct from its talking state. |
| Talking / `open_mouth` | Clearly visible mouth opening at normal display size, while retaining the intended emotion. |

The resting mouth is used in `idle` and `blink`; the talking mouth is used in `talking` and `blink_talking`. Filenames such as `closed_mouth` describe the intended state; they do not prove that the image satisfies it.

Keep expressiveness consistent with the requested animation state: use brows and widened eyes to convey Shocked while keeping resting lips closed or barely parted. Keep Happy recognizably happy with both resting and talking mouths.

### Generate the expression, then its animation variants

Edit the actual master pose to obtain the expression donor. After the static expression is finished, use it as the reference for blink and talking donors. Specify the desired visible features and eye/mouth state. Preserve identity and rendering style in the features to be copied, with geometry suitable for alignment.

Build each expression's animation states from its finished static expression. Preserve its expressive brows, shading, and unaffected features when replacing eyes or mouth; starting every state from Neutral can discard the expression.

Select each donor with an explicit path and record the exact file loaded in the build manifest. Do not resolve a filename by searching multiple directories or silently substitute an older donor.

Use full-canvas donors with the master's framing by default. When one supplies suitable features, crop its existing pixels for transplantation. Changes to clothing, body, background, or other excluded pixels are not grounds to reject it. Final composites preserve the master outside the declared edit regions.

Generate an enlarged face donor only to address a specific visible deficiency in the available donors. Cropping existing pixels preserves their stroke widths; generating a close-up can redraw linework, shading, texture, and proportions at a different scale. Record the source crop bounds and establish the generated crop's mapping to the master. Before transplantation, map it to the master's native scale and inspect geometry, stroke weight, shading, and sharpness against the source. Do not assume that resizing alone restores compatibility.

Example instructions:

- **Shocked resting:** "Clearly surprised anime expression: raised brows, widened eyes, and lips closed or only very slightly parted. Preserve the character's identity and rendering style."
- **Shocked talking:** "Preserve the surprised brows and eyes; make the mouth visibly open and clearly distinguishable from the resting mouth."
- **Happy resting:** "Clearly happy anime expression: a readable closed-mouth smile with raised corners and cheerful, visibly open eyes. Preserve the character's identity and rendering style."
- **Happy blink:** "Preserve the happy smile and brows; fully close both eyes with natural expressive lids, with no visible iris or eye opening."

### Check suitability before compositing

Compare the master and expression donor side by side at the intended display size. If the requested emotion and eye/mouth state read clearly and the features are suitable for transplantation, select the donor and proceed. Regenerate only for a specific visible deficiency, such as an ambiguous emotion, wrong state, damaged contour, or incompatible anatomy/style. Name the deficiency and target it in the next prompt; a vague desire for a stronger expression is insufficient.

Compare resting/talking and open/closed variants side by side at normal display size. Check that each variant conveys the intended emotion and that the eye and mouth states are unambiguous. Inspect enlarged crops for anatomy, line quality, and unwanted changes within the intended transplant region.

Reject ambiguous states, unreadable emotions, or unintended identity/style changes within the features to be copied. Sharpness alone does not make a donor suitable. Reuse existing donors that meet these criteria.

## Separate the selections

| Selection | Coordinates | Includes |
|---|---|---|
| Source removal | Fixed master/source coordinates | Complete old feature, unwanted shadows, and antialiased remnants that must disappear. |
| Donor insertion | Aligned donor coordinates | Desired new feature plus the supporting skin it needs. |
| Source foreground | Fixed master/source coordinates | Identified hair/brows crossing the edit; excludes old eye or mouth linework. |
| Additional cleanup | Explicit target coordinates | Bounded skin reconstruction, seam correction, or line repair beyond the other selections. |

The removal region can be larger than the inserted eyelid. A small closed lid does not describe the full footprint of an open eye. Reuse the same removal geometry where variants truly share the same source. Transform only the donor and its donor selection; do not shift source removal or foreground geometry with it.

For static-expression transplantation, changing eyebrows, eyes, mouth, and expression shading together can require a broad facial patch. Blink/talk transitions need stable surrounding artwork and separate feature treatment. Do not copy a face mask into an animation pipeline.

## Diagnose before editing

Compare the exact source, aligned donor, previous final, and latest final at the same coordinates. Inspect normal-size readability and use enough nearest-neighbor magnification to resolve the marked edge.

| Visible defect | Locate its first appearance | Corrective operation |
|---|---|---|
| Entire feature shifted | Aligned donor | Translate per feature; rotate/scale only if shared anchors warrant it. |
| Corners fit but curve does not | Donor shape | Small controlled reshape, local reconstruction, or a better donor. |
| Old iris/lash/shadow survives | Background removal / initial insertion | Expand the actual removal footprint and reconstruct clean skin beneath the new feature. |
| Desired lash is cut off | Insertion boundary or foreground mask | Recover its donor coverage or repair its endpoint; check whether a hair guard cuts through it. |
| Hair moves or old lash reappears | Foreground restoration | Correct the explicit source selection. Darkness is not proof that a pixel is hair. |
| Skin join is visible | Skin insertion / color treatment | Match skin-only tone and shading; extend bounded repair where necessary. |
| Jagged line or detached fragment | Source, donor, or compositing stage | Select/reconstruct the exact contour. Skin blending does not repair line geometry. |
| Correct PNG, wrong GIF | Encoding or wrong artifact | Decode the delivered file; inspect palette effects and confirm its recorded identity. |

Reject donors with unusable anatomy, the wrong expression, or incompatible style within the intended transplant region. Crisp donor pixels still need alignment and complete source removal. Differences outside the region to be copied do not require regeneration.

## Compose in explicit stages

The working utilities are in [artwork_tools.py](experiments/artwork_tools.py); expression geometry and operation order remain in each builder.

Demonstrate one clean feature transplant through the following stages before expanding to the full state set. Save actual intermediate images for the operations used; a final source/donor/result comparison alone does not show where a defect entered the composition.

1. Align each donor feature using shared landmarks. Closed lids have no iris center; use corners and stable surrounding anchors.
2. Select source foreground separately. Preserve its coverage for restoration after editing the underlying area.
3. Remove the complete unwanted source feature. Use clean aligned donor skin, a locally matched source patch, a reconstructed gradient, or tightly bounded inpainting as appropriate. Review the repaired background before adding the new feature.
4. Insert the donor feature without unnecessary resampling. Avoid fading back to original pixels that still contain the old eye or mouth.
5. Repair the remaining specific join or contour. Keep skin correction off linework; retain intended antialiasing without blurring the artwork.
6. Restore the selected original foreground last. Verify that this does not put the old feature back.

A minimal reusable implementation, with selections already traced and the donor aligned:

```python
from artwork_tools import compose_feature, save_stage_review, region_effect

def transplant_eye(source, donor, clean_skin, removal, insertion, foreground, box, review_path):
    # Coverage arrays must match the canvas and contain values in [0, 1].
    final, allowed, stages = compose_feature(
        source, donor, insertion,
        repair_image=clean_skin,
        removal=removal,
        foreground=foreground,
    )
    save_stage_review(review_path, stages, box, scale=10)
    effect = region_effect(source, final, removal)
    return final, allowed, effect
```

Choose clean repair pixels and selections from the actual images. `align_feature` moves a donor and its selection together; `match_skin` estimates a bounded median RGB offset from explicit skin samples and applies it only to selected skin. `compose_feature` also accepts an ordered `cleanup=[(repair_image, coverage), ...]` before foreground restoration.

The shared animation builder supports optional `eye_layers` / `mouth_layers` dictionaries with those same arguments and an optional affine `alignment`. `insertion` is required; `donor` defaults to the existing corrected donor. Legacy pipelines retain their original arithmetic until deliberately migrated. Overlapping eye/mouth regions require an explicit custom operation order.

## Worked reference: Angry

[The Angry compositor](experiments/14_angry_animation/angry_visual_blink.py) uses a source-matched crop, separate eye-local skin replacement, donor lid strokes, and source brow/hair restoration last. Its builder retains the correct idle/speaking mouth for each blink state.

Run its builder to create `output/angry_layer_stages.png`, fixed-coordinate source/donor/result reviews, four PNG states, GIFs, and a final manifest. Use its layer structure as a reference; trace polygon coordinates and select color thresholds for the actual target image.

## Prove each correction

For every defect record: native-coordinate region, visible symptom, originating stage, intended operation, before/after crop, and remaining issues.

- Use `region_effect` or an equivalent pixel comparison to discover an ineffective operation. If the final target is unchanged, do not report a repair. A nonzero count only establishes that something changed; inspect whether it improved.
- Inspect the final pixels again after all downstream operations. A correct intermediate can be overwritten or covered later.
- Decode the exact delivered GIF. Palette encoding can erase subtle changes; inspect PNG and encoded crops together.
- After two unsuccessful attempts at the same defect, revisit its origin and selection or change the technique/donor. Retain the prior working result.
- A missing stroke may need a small tapered reconstruction based on neighboring line direction, thickness, and color. A missing skin patch may need reconstruction rather than broader blending.
- Record actual review and user approval against the build's artifacts. Do not describe output as seamless while visible defects remain.

Build manifests declare intended feature/cleanup masks independently of the changed pixels. Integrity checks must recompute containment from those masks; creating a permitted region from the observed diff would make the check circular. Neither those checks nor an AI statement replaces visual evidence.
