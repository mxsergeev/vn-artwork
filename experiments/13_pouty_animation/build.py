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
        [(465,146),(467,141),(471,137),(478,136),(487,136),(496,138),(504,140),(511,143),(514,147),(511,152),(506,156),(497,158),(487,158),(478,155),(470,152)],
        [(537,139),(539,134),(544,130),(551,127),(560,126),(568,128),(575,131),(579,135),(578,139),(573,143),(565,145),(556,145),(548,143),(542,141)],
    ],
    "eye_protect": [[(502,116),(507,116),(513,137),(512,144),(507,143),(504,132)]],
    "mouth_polygon": [(523,192),(525,187),(530,184),(537,182),(545,182),(551,185),(554,189),(553,199),(549,205),(542,208),(535,207),(529,203),(525,198)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 566, 215],
    "notes": "Original pout remains idle; the image-referenced mouth donor opens the pout for speech.",
})
