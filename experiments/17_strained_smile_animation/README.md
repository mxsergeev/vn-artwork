# Experiment 17 — Strained-smile blink and speech

Adds four source-anchored animation states to `static/sprites/08_strained_smile.png`. The original toothy strained smile is reused for talking; an image-edited tight, closed-mouth variant supplies idle. The eye and mouth masks remain independent and avoid changing the character's tense expression, hair, alpha, or source pixels outside the features.

Run `python experiments/17_strained_smile_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.
