# Animation assets and status

The default pose has eight existing expression sets. Each contains four 1086×1448 RGBA states and native-size blink, talk, and combined GIFs. PNGs preserve source transparency; GIFs use an opaque pale-gray matte.

| Set | Original state reused | Implementation / status |
|---|---|---|
| neutral | idle | [10](../../experiments/10_neutral_blink_refined/README.md), established reference |
| happy | blink_talking | [11](../../experiments/11_happy_eye_refined/README.md), established reference; mouth donor from 09 |
| shocked | idle | [12](../../experiments/12_shocked_animation/README.md), established reference |
| pouty | idle | [13](../../experiments/13_pouty_animation/README.md), existing set |
| angry | talking | [14](../../experiments/14_angry_animation/README.md), user accepted corrected result on 2026-10-18 |
| embarrassed | talking | [15](../../experiments/15_embarrassed_animation/README.md), existing set |
| sad | idle | [16](../../experiments/16_sad_animation/README.md), existing set |
| strained_smile | talking | [17](../../experiments/17_strained_smile_animation/README.md), existing set |
| document_reading/{neutral,happy,shocked} | pose-specific | **NOT APPROVED**: unresolved eye seams, lash remnants, and hair joins; see [status](../../experiments/13_document_reading_pose/README.md) |

`preview.jpg` and `all_expressions.gif` index the default sets. Document-reading has its own `all_three_native.gif` and preview; its presence here does not establish approval.

Each set's `build.json` identifies its current files, source, and recorded status. Initial records of existing assets are labeled `existing_snapshot`: they do not claim a newly reproduced build, fresh visual review, or historically unrecorded approval. Missing historical edit-region coverage is reported as unmeasured.

Builders and preview commands produce candidates under ignored experiment output folders. Publication is explicit through `experiments/publish_artwork.py`; inspect the exact build before recording review. See the shared [workflow](../../README.md) and [editing techniques](../../EDITING_TECHNIQUES.md).

Duplicate versioned repair GIFs and editor backups belong to local experiment output, not this asset collection. Essential sources, selected states, supported previews, and build records are tracked.

