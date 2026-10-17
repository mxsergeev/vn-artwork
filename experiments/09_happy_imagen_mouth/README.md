# Experiment 09 — Happy closed-smile donor

Replaces the distorted Python-compressed idle smile with a source-anchored AI-edited **closed smile**. The original Happy mouth remains the speaking frame. Reuses the eye donor already stored in experiment 05.

**Source:** `static/sprites/02_happy.png`. **Mouth donor:** `assets/closed_smile_patch.png` (the exact 67×55 RGB crop at x=510–576, y=165–219 from the edited full-body donor). The full-body donor was deliberately not duplicated; the crop reproduces the original experiment pixel-for-pixel.

Run from the repository root: `python experiments/09_happy_imagen_mouth/build.py`.

The script generates four mouth/eye states, animated previews, mask overlays, and QA into `output/` (ignored by Git). **The masks are specific to this image; do not reuse their coordinates blindly.** The cleaner Happy eye masks are in experiment 11.
