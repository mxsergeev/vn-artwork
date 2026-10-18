#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "15_embarrassed_animation",
    "slug": "embarrassed",
    "source": "static/sprites/06_embarrassed.png",
    "source_mouth_state": "open",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_regions": {
        "viewer_left": {
            "polygons": [
                [(470,151),(472,142),(477,138),(485,135),(493,135),(500,137),(507,140),(514,144),(518,149),(516,154),(510,157),(502,158),(493,158),(485,157),(478,155),(473,153)],
                [(463,151),(464,145),(468,140),(473,139),(477,143),(477,150),(472,154),(468,155),(464,154)],  # blush-side lash tip; avoids the fringe
                [(464,148),(466,141),(472,136),(480,132),(488,130),(497,130),(505,133),(512,137),(517,142),(518,148),(512,147),(505,144),(498,142),(490,142),(482,144),(474,147),(468,151)],  # embarrassed upper lash, below the raised brow
            ],
            "protect": [
                [(502,116),(504,116),(505,124),(506,130),(507,135),(506,137),(504,134),(503,128)],
            ],
            "feather": 1.05,
        },
        "viewer_right": {
            "polygons": [
                [(537,143),(539,134),(546,130),(554,128),(563,127),(572,128),(579,130),(583,132),(586,136),(588,141),(588,146),(583,151),(577,153),(568,155),(559,155),(550,153),(543,149)],
                [(580,137),(582,134),(585,133),(588,136),(589,140),(588,144),(585,146),(581,144)],  # lifted outer lash below the protected strand
                [(536,141),(538,134),(544,129),(552,126),(562,125),(571,126),(579,128),(583,131),(584,136),(580,135),(574,133),(566,132),(558,133),(550,136),(543,140),(539,145)],  # raised lash line, separated from outer hair
            ],
            "protect": [
                [(584,125),(588,126),(590,133),(590,143),(589,152),(586,155),(583,151),(584,140)],
            ],
            "feather": 1.0,
        },
    },
    "mouth_polygon": [(523,188),(526,183),(532,181),(541,180),(551,181),(560,184),(564,188),(563,196),(560,201),(552,204),(541,203),(531,201),(526,197),(524,192)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 570, 215],
    "notes": "Embarrassed uses separately traced raised-eye contours and upper-lash arcs, with its lifted outer tips included. The raised brows, hair, blush, and cheek shading remain outside the masks; the source's small open mouth is reused for talking.",
})
