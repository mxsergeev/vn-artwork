# Document-reading pose — NOT APPROVED

**The current expression/animation set has unresolved eye seams, lash remnants, and hair/skin joins. Commit 849737b is a WIP checkpoint, not release approval.** Existing files under `static/animation/document_reading/` retain this status.

| Status record | Current information |
|---|---|
| Master | `static/poses/document_reading/neutral.png`, historically reviewed pose. |
| Usable donors | Source-referenced eye/mouth crops in `assets/`; Happy and Shocked open-eye donors were replaced in 849737b. Crop locations and current local shifts are recorded in code and `assets/donor_alignment.json`. |
| Current build | `output/{neutral,happy,shocked}/build.json` after building. Existing static files have snapshot records; the final Happy one-pixel edit was not exported into their PNGs. |
| Defects | Incomplete source-feature removal; rough lash/foreground joins and skin transitions across the five highlighted states. |
| Visual review | User rejected the later repair attempts. Enlarged previews and repeated claims did not establish successful correction. |
| User approval | **NOT APPROVED** for the expression/animation work. Do not infer approval from the neutral master pose or file location. |
| Next action | Before any future artwork repair, trace and solve one marked eye through its actual composition stages. This repository cleanup does not repair the images. |

## Local implementation

`build.py` has per-eye alignment, source-hair restoration, skin tone/join treatment, and bounded retouch operations. These are implementation references to inspect individually. The complete pipeline is not a successful transplant template.

Current residual eye translations (x, y):

| Donor | Left | Right |
|---|---|---|
| Neutral blink | (0, 0) | (−2, 0) |
| Happy open | (0, 0) | (0, 0) |
| Happy blink | (0, −1) | (0, −1) |
| Shocked open | (0, 0) | (0, 0) |
| Shocked blink | (0, −1) | (0, −1) |

The selected Shocked speech donor is `shocked_talk_mouth_v3.png`. Earlier registration metadata remains labeled historical where a replaced donor no longer matches it.

## Command and outputs

```sh
python experiments/13_document_reading_pose/build.py
```

Writes four standard PNGs, native GIFs, copied final feature-review panels, declared regions, and a manifest per expression under ignored `output/`. The combined candidate is `output/all_three_native.gif`. Legacy flat PNG names and detailed decoded review sheets remain local for diagnosis.

Building does not write animation or pose assets under `static/`. Candidates retain NOT APPROVED status. Publication uses the separate command in the [shared workflow](../../README.md), after the defects are resolved and review is recorded.

See the [worked failure](../../EDITING_TECHNIQUES.md#worked-failure-document-reading) and [historical account](../../HISTORY.md#document-reading-failure--849737b). `failure_example.png` is a compact source/donor/final diagnostic, not a donor.
