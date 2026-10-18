# Document-reading pose

| Item | Status |
|---|---|
| Master | [neutral.png](neutral.png) — reviewed document-reading pose, 1086 × 1448 RGBA (unchanged) |
| Master SHA256 | `c381bd610b0753cf74631ac224bba573a0fbfdc240d4df04c9c2015072755a8f` |
| Source expressions | Neutral, Happy, and Shocked |
| Finished animation states | [animation/neutral](animation/neutral), [animation/happy](animation/happy), [animation/shocked](animation/shocked) |
| Each animation set | `idle.png`, `blink.png`, `talking.png`, `blink_talking.png`; `blink.gif`, `talk.gif`, `combined.gif`; `build.json` |
| State canvas | 1086 × 1448 RGBA with unchanged background transparency |

The three animation sets are **pose-specific**. Do not replace assets under `static/animation/`, which belong to the original sprite pose. The reviewed animation states were made by transplanting eye and mouth features into each expression's fixed idle sprite. Their body, clothes, hair, document, and transparency stay unchanged across frames.

`build.json` records frame timing, sequences, and image-integrity checks. The approved source expression PNGs are the `idle.png` files in the three animation folders; **they are not replacements for the historical `neutral.png` master**.

Follow the [production manual](../../../README.md).
