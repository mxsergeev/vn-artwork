# Experiment 11 — refined Happy eyes (preferred)

**Current best Happy result**, confirmed by visual comparison. Uses the **same eye donor** as experiments 05/09, but improves the result with narrower eye-specific contours: raised lower-right boundary, small separate left-lash extension, and selective protection of the original outer-right hair/skin pixels. The eyes changed 1,489 source pixels versus 1,860 in experiment 09, without the earlier obvious clipping.

Mouth behavior is unchanged from experiment 09: AI-edited natural closed smile at idle, original open Happy mouth while speaking. This script references the shared eye donor from experiment 05 and the **small, source-anchored mouth patch** from experiment 09, rather than duplicating full-body PNGs.

Run: `python experiments/11_happy_eye_refined/build.py`. Review generated `output/` frames, mask overlays, and all GIFs; numerical QA is necessary but insufficient. Coordinates are specific to this source/donor pair.
