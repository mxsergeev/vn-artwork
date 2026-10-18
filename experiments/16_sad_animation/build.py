#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "16_sad_animation",
    "slug": "sad",
    "source": "static/sprites/07_sad.png",
    "source_mouth_state": "closed",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_regions": {
        "viewer_left": {
            "polygons": [
                [(470,150),(472,141),(478,137),(485,135),(493,135),(500,137),(507,140),(513,144),(518,148),(517,153),(512,156),(504,158),(496,159),(488,158),(480,155),(473,152)],
                [(463,149),(465,144),(469,140),(474,140),(478,144),(477,150),(472,153),(468,154),(464,152)],  # sad outer lashes, above the tear shading
                [(463,146),(466,139),(472,135),(480,131),(488,129),(496,129),(504,132),(511,136),(516,141),(518,147),(512,146),(505,143),(497,141),(489,141),(481,143),(474,146),(468,149)],  # sad upper lash, fitted to the drooped lid
            ],
            "protect": [
                [(500,116),(502,116),(503,123),(504,130),(505,135),(504,137),(502,134),(501,127)],
            ],
            "feather": 0.95,
        },
        "viewer_right": {
            "polygons": [
                [(537,143),(539,134),(545,130),(553,127),(562,126),(571,127),(578,129),(582,131),(585,135),(587,140),(587,145),(583,150),(577,153),(569,155),(560,155),(551,153),(544,149)],
                [(579,137),(581,134),(584,133),(587,136),(588,140),(587,144),(584,146),(580,144)],  # raised drooped outer tip, kept above tear shading
                [(536,141),(538,134),(544,129),(552,126),(561,124),(570,125),(578,127),(582,130),(584,135),(580,134),(573,132),(565,131),(557,132),(550,135),(543,139),(539,145)],  # drooped upper lash, stopping at the hair boundary
            ],
            "protect": [
                [(584,125),(588,126),(590,133),(590,143),(589,152),(586,155),(583,151),(584,140)],
            ],
            "feather": 1.0,
        },
    },
    "mouth_polygon": [(520,190),(523,184),(529,181),(538,179),(548,180),(556,183),(561,188),(560,198),(556,205),(548,210),(539,210),(531,206),(525,202),(521,196)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 570, 215],
    "notes": "Sad's separately traced contours follow the drooped eyes, source upper-lash arcs, and outer tips. The upper boundaries sit below the brows and the lower boundaries stay above tearful shading; the original downturned mouth remains idle.",
})
