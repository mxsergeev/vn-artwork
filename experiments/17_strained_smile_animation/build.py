#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "17_strained_smile_animation",
    "slug": "strained_smile",
    "source": "static/sprites/08_strained_smile.png",
    "source_mouth_state": "open",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_regions": {
        "viewer_left": {
            "clip_y": [134, None],
            "polygons": [
                [(470,151),(472,142),(478,138),(486,136),(494,136),(501,138),(508,141),(514,145),(519,150),(518,154),(512,157),(504,159),(495,159),(487,157),(479,155),(473,153)],
                [(463,151),(465,146),(470,141),(475,140),(479,144),(478,151),(473,155),(468,156),(464,154)],  # compressed strained-eye lash tip
                [(463,147),(466,140),(472,136),(480,133),(488,131),(496,131),(504,134),(511,138),(517,143),(519,149),(513,148),(506,145),(498,143),(490,143),(482,145),(474,148),(468,151)],  # strained upper lash, fitted to the compressed eye
            ],
            "protect": [
                [(501,116),(503,116),(504,123),(505,130),(506,135),(505,137),(503,134),(502,127)],
            ],
            "feather": 0.95,
        },
        "viewer_right": {
            "clip_y": [130, 152],
            "polygons": [
                [(537,143),(539,134),(545,130),(553,127),(562,126),(571,126),(578,128),(582,131),(585,135),(588,140),(588,147),(584,152),(577,155),(569,156),(560,155),(551,153),(544,149)],
                [(579,138),(581,135),(584,134),(587,137),(588,141),(587,145),(584,147),(580,145)],  # narrow clenched-eye outer corner below the protected strand
                [(536,141),(538,133),(544,128),(552,125),(561,124),(570,124),(578,126),(582,129),(584,134),(580,133),(573,131),(565,130),(557,131),(550,134),(543,138),(539,144)],  # compressed upper lash, separated from outer hair
            ],
            "protect": [
                [(584,125),(588,126),(590,133),(590,143),(589,152),(586,155),(583,151),(584,140)],
            ],
            "feather": 0.95,
        },
    },
    "mouth_polygon": [(507,188),(509,182),(515,179),(527,176),(542,176),(558,179),(570,183),(575,188),(573,195),(568,201),(559,205),(547,208),(535,208),(524,205),(515,202),(509,197)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [510, 176, 580, 215],
    "notes": "Strained Smile uses separate compressed-eye and upper-lash contours fitted to each squint. Per-eye bounds trim the upper hair and the right under-eye edge; the complete left lower contour remains to hide the source eye. The toothy smile remains the talking state.",
})
