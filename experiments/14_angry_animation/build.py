#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "14_angry_animation",
    "slug": "angry",
    "source": "static/sprites/05_angry.png",
    "source_mouth_state": "open",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_polygons": [
        [(470,152),(472,148),(477,145),(484,143),(492,143),(500,145),(507,148),(511,151),(509,154),(503,156),(495,157),(487,157),(479,155),(473,154)],
        [(540,145),(542,141),(548,138),(555,137),(564,137),(571,139),(577,141),(580,144),(578,147),(572,149),(564,150),(555,149),(548,147),(543,146)],
        [(465,150),(470,147),(474,149),(474,153),(469,155),(465,153)],  # tiny, separate outer lash-tip continuation
        [(571,143),(574,138),(580,138),(583,140),(582,145),(578,147),(572,145)],  # tiny outer-corner patch removes source sclera below the brow
    ],
    "eye_protect": [[(501,116),(506,116),(512,137),(511,144),(506,143),(503,132)]],
    "mouth_polygon": [(520,182),(523,178),(531,176),(543,176),(555,179),(562,183),(564,190),(562,197),(557,202),(549,205),(539,204),(530,202),(524,198),(521,191)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 176, 570, 215],
    "notes": "Tightened each eye contour around the closed lid, preserved the original central bang, raised the right-eye upper boundary below the angry brow, and covered only the tiny outer sclera corner. The source's teeth-baring mouth remains the talking state.",
})
