# Happy animation — experiment 05

**Status:** promising prototype, not approved as a final sprite.

Run `python experiments/05_happy_animation/build.py` (requires root `requirements.txt`). Uses the existing aligned `static/sprites/02_happy.png` (original closed eyes and wide smile) and `01_neutral_worried.png` (open-eye donor); both are the **same character** from the proven expression set.

- `output/01_happy_normal.png` — transplanted open eyes, original wide smile
- `static/sprites/02_happy.png` — unchanged original, used as blink frame (not duplicated here)
- `output/03_happy_talking.png` — open eyes, smaller speaking mouth
- `output/04_happy_blink_talking.png` — closed eyes, smaller speaking mouth
- `output/combined_preview.gif`, `blink_preview.gif`, `talk_preview.gif` — animation tests
- `output/four_states_face_comparison.png`, `eyes_8x_inspection.png`, `mouth_8x_inspection.png`, `feature_masks.png`, `QA.json` — inspection and locality/alpha checks

**Method:** hand-tuned per-eye masks excluding hair, local RGB skin adjustment, and a small mouth produced by shrinking Happy's *own* mouth vertically around its original center over inpainted skin. Pixel checks verify unchanged alpha and no changes outside the masks; these cannot establish artistic quality. Open eyes may look too neutral; eyelashes, mask edges, and inpainted skin still need visual/manual review.

**New AI-generated artwork:** `assets/ai_open_eyes_candidate.png` is from a later successful **direct source-image edit**. It matches the character/style but differs from the original in eyes, color and other pixels. **Not used by build.py or validated as a donor**. Retain as one reference for a future donor-transplant iteration; unrelated earlier generations are excluded.
