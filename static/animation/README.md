# Animation assets and status

The default pose has eight existing expression sets. Each contains four 1086×1448 RGBA states and native-size blink, talk, and combined GIFs. PNGs preserve source transparency; GIFs use an opaque pale-gray matte.

| Set | Original state reused | Implementation / status |
|---|---|---|
| neutral | idle | [10](../../experiments/10_neutral_blink_refined/README.md), established reference |
| happy | blink_talking | [11](../../experiments/11_happy_eye_refined/README.md), established reference; mouth donor from 09 |
| shocked | idle | [12](../../experiments/12_shocked_animation/README.md), established reference |
| pouty | idle | [13](../../experiments/13_pouty_animation/README.md), existing set |
| angry | talking | [14](../../experiments/14_angry_animation/README.md), approved result recorded in `angry/build.json` |
| embarrassed | talking | [15](../../experiments/15_embarrassed_animation/README.md), existing set |
| sad | idle | [16](../../experiments/16_sad_animation/README.md), existing set |
| strained_smile | talking | [17](../../experiments/17_strained_smile_animation/README.md), existing set |

`preview.jpg` and `all_expressions.gif` index the default sets.

Read each set's `build.json` for file identity, source, visual review, and user approval. Treat `existing_snapshot` as an inventory record. Treat unrecorded edit-region coverage as unmeasured.

Builders and preview commands produce candidates under ignored experiment output folders. Publication is explicit through `experiments/publish_artwork.py`; inspect the exact build before recording review. Follow the [production manual](../../README.md).

Track selected states, supported previews, and build records here. Keep alternate renders and review panels in ignored experiment output folders.

