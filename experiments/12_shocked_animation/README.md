# Experiment 12 — Shocked blink and speech

Adds eye blinking and mouth movement to the existing `static/sprites/03_shocked.png` expression.

Both donors were edited from the exact original sprite through the image editor's supported `referenced_image_paths` input. Only lossless feature crops are stored here; their source coordinates are recorded in `build.py`. Full-size donor edits and generated frames are omitted from Git.

The first blink mask left a few lower-lash pixels, so the left contour was extended slightly and reviewed at 8×. The first mouth mask left the original lower-mouth shading visible during speech; the mouth contour was extended to cover the complete source mouth and shading. The final four states and all three GIFs were reviewed visually.

Run `python experiments/12_shocked_animation/build.py` from the repository root. Generated frames, GIFs, masks, and QA images go to ignored `output/`.

The build asserts 1086×1448 dimensions, exact source-alpha preservation, and that changes remain inside the eye and mouth masks. `preview.jpg` shows the four states; the individual outputs and QA overlays are reproducible.
