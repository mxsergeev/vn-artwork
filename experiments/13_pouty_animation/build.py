#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "13_pouty_animation",
    "slug": "pouty",
    "source": "static/sprites/04_pouty.png",
    "source_mouth_state": "closed",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_polygons": [
        [(470,151),(471,146),(475,142),(482,140),(489,140),(496,142),(503,144),(509,147),(512,150),(510,153),(504,156),(496,157),(488,157),(480,155),(474,153)],
        [(537,139),(539,134),(544,130),(551,127),(560,126),(568,128),(575,131),(579,135),(578,139),(573,143),(565,145),(556,145),(548,143),(542,141)],
        [(465,148),(470,145),(475,147),(474,152),(469,154),(465,152)],  # tiny, separate outer lash-tip continuation
        [(571,140),(574,136),(580,136),(583,139),(582,143),(578,145),(572,144)],  # tiny outer-corner patch removes source sclera below the brow
    ],
    "eye_protect": [[(502,116),(507,116),(513,137),(512,144),(507,143),(504,132)]],
    "mouth_polygon": [(523,192),(525,187),(530,184),(537,182),(545,182),(551,185),(554,189),(553,199),(549,205),(542,208),(535,207),(529,203),(525,198)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 566, 215],
    "notes": "Redrew the left lid contour to keep fringe and cheek pixels outside the blink mask; a separate tiny polygon preserves the outer lash tip. A tiny outer-corner patch removes the source sclera sliver without touching the brow. The original pout remains idle.",
})
