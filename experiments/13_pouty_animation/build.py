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
    "eye_regions": {
        "viewer_left": {
            "clip_y": [133, None],
            "polygons": [
                [(470,151),(471,142),(475,138),(482,136),(489,135),(496,136),(503,138),(510,141),(516,145),(519,150),(516,154),(510,156),(502,158),(493,158),(485,157),(478,155),(473,153)],
                [(463,145),(464,139),(469,136),(474,137),(478,141),(477,147),(473,151),(468,152),(464,149)],  # covers Pouty's full outer lash without reaching the side fringe
                [(464,143),(466,137),(472,133),(480,131),(488,130),(496,130),(503,132),(510,135),(515,139),(518,144),(512,143),(505,140),(498,138),(490,137),(482,138),(474,141),(468,144)],  # Pouty's own upper-lash arc, below the fringe
            ],
            "protect": [
                [(502,116),(504,116),(504,123),(505,130),(505,135),(504,137),(502,134),(502,127)],
            ],
            "feather": 1.0,
        },
        "viewer_right": {
            "clip_y": [128, 151],
            "polygons": [
                [(537,145),(538,137),(542,132),(549,129),(557,127),(566,126),(574,127),(581,129),(585,132),(586,137),(585,143),(581,148),(575,152),(566,155),(557,155),(549,153),(542,150)],
                [(580,137),(582,134),(585,134),(587,137),(587,141),(584,144),(581,143)],  # Pouty's short outer lash tip, inside the hair edge
                [(536,142),(537,136),(541,131),(547,128),(555,126),(564,125),(573,126),(580,128),(584,131),(584,136),(579,135),(572,133),(564,132),(556,133),(549,136),(543,140),(539,145)],  # inner and upper lash, stopping at the hair edge
            ],
            "protect": [
                [(584,125),(588,126),(589,133),(589,145),(588,153),(585,155),(583,150),(584,140)],
            ],
            "feather": 1.0,
        },
    },
    "mouth_polygon": [(523,192),(525,187),(530,184),(537,182),(545,182),(551,185),(554,189),(553,199),(549,205),(542,208),(535,207),(529,203),(525,198)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 566, 215],
    "notes": "Pouty's shallow-lid contours include separate upper-lash arcs and outer tips. The upper boundary is clipped above each lid; the right-eye lower edge is clipped below its lash while the left-eye lower contour stays full to cover the source sclera. Hair and skin preservation is reviewed in the 20x comparisons.",
})
