# Experiment 14 — Angry animation

The reviewed Angry animation uses the original sprite for the face, hair, brows, and open-mouth expression. Its closed-eye state uses a source-matched closed-eye donor, saved only as the small eye-area crop `assets/eyes_closed_angry_patch.png`.

## Selected blink method

`build.py` first creates the standard Angry states, then `angry_visual_blink.py` replaces the blink states with the reviewed eye-local composite:

1. Place the cropped donor at its original source coordinates; do not transform the whole donor patch.
2. Replace only the two eye-local regions with donor skin, using a small local skin-color correction.
3. Restore the original brow and crossing hair strokes as separate foreground layers.
4. Composite the donor's closed-lid lines over the repaired skin, preserving hair that crosses the eye.
5. Create `blink_talking.png` by applying only the blink's changed eye pixels to the existing idle-mouth state.
6. Regenerate the experiment GIFs from the four resulting states.

Run `python experiments/14_angry_animation/build.py` from the repository root. It writes candidates and review files to the ignored `output/` directory. Copy reviewed states to `static/animation/angry/` only after visual review; regenerate published GIF previews with `python experiments/build_animation_previews.py`.

## Review status

The user visually approved the eye-only blink candidate on 2026-10-18. Review compared the source, prior blink, and new composite at face scale and high zoom. The new candidate removes the open irises, keeps the angry brows and crossing hair in place, and avoids the previous broad skin/hair shift and blurred repair. Integrity checks remain separate from visual approval and do not establish image quality.

The final postprocessor applies the eye composite to the idle mouth for `blink.png` and to the speaking mouth for `blink_talking.png`. It restores the source brow and hair after drawing the lids, and records checksums only after writing the final states and review images. Each build saves before/after face, eye, and mouth sheets plus final source/donor/result reviews under `output/`. The published Angry PNGs and GIFs were refreshed from these final states.
