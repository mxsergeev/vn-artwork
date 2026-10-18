#!/usr/bin/env python3
"""Build the document-reading pose and its expression/animation states.

All image-generated donors were edits of the exact neutral pose. Only small
feature crops are kept; this script reconstructs them at their recorded source
coordinates, applies image-specific masks and local skin color corrections,
and preserves the neutral pose's alpha and all pixels outside those masks.
"""
from pathlib import Path
import io
import json
import shutil

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = HERE / 'assets'
OUT = HERE / 'output'
PUBLISHED = ROOT / 'static/animation/document_reading'
OUT.mkdir(exist_ok=True)

BASE = np.asarray(Image.open(ROOT / 'static/poses/document_reading/neutral.png').convert('RGBA'))
H, W = BASE.shape[:2]
assert BASE.shape == (1448, 1086, 4)

# Lossless donor crop locations in the neutral pose's 1086x1448 canvas.
EYES_BOX = (505, 125, 640, 185)
MOUTH_BOX = (545, 182, 617, 230)


def polygon(points):
    raw = np.zeros((H, W), np.uint8)
    cv2.fillPoly(raw, [np.asarray(points, np.int32)], 255)
    return raw


def exact_pixels(points):
    """Create a raw mask containing only the listed source-image pixels."""
    raw = np.zeros((H, W), np.uint8)
    for x, y in points:
        raw[y, x] = 255
    return raw


def feather(raw, width=1.2):
    """Feather only inward, keeping every changed pixel inside its contour."""
    distance = cv2.distanceTransform(raw, cv2.DIST_L2, 5)
    return np.clip(distance / width, 0, 1).astype(np.float32)


# Feature masks are traced per expression and per eye from aligned
# donor/source overlays. Do not reuse one expression's geometry for another:
# Happy and Shocked have different open-eye extents and their blink donors have
# different lid contours. Each mask follows the lash/sclera/lid shape and keeps
# surrounding bangs, brows, and cheek shading as exact source pixels.
LEFT_OPEN_EYE_CORE = polygon([
    # Keep the upper edge on the actual lash line; the previous contour
    # replaced too much eyelid skin above it.
    (528, 159), (531, 157), (536, 155), (543, 155), (550, 156),
    (558, 158), (565, 160), (570, 161), (568, 165), (562, 168),
    (554, 170), (545, 170), (537, 169), (532, 166),
])
RIGHT_OPEN_EYE_CORE = polygon([
    (588, 158), (591, 156), (598, 154), (607, 154), (614, 156),
    (621, 158), (625, 160), (624, 164), (619, 168), (612, 170),
    (603, 170), (596, 169), (591, 165),
])
# The lash ends are separate, narrow masks. The main eye contour must not be
# widened into bangs just to catch the few outermost lash pixels.
NEUTRAL_LEFT_LASH_TIP_RAW = polygon([
    (567, 156), (570, 157), (573, 159), (574, 161),
    (572, 163), (569, 162), (566, 160),
])
NEUTRAL_RIGHT_LASH_TIP_RAW = polygon([
    (620, 155), (623, 155), (625, 157), (625, 160),
    (623, 162), (620, 160),
])
LEFT_OPEN_EYE = np.maximum(LEFT_OPEN_EYE_CORE, NEUTRAL_LEFT_LASH_TIP_RAW)
RIGHT_OPEN_EYE = np.maximum(RIGHT_OPEN_EYE_CORE, NEUTRAL_RIGHT_LASH_TIP_RAW)
EYE_OPEN_RAW = np.maximum(LEFT_OPEN_EYE, RIGHT_OPEN_EYE)
EYE_OPEN_WEIGHT = np.maximum(feather(LEFT_OPEN_EYE, 1.25), feather(RIGHT_OPEN_EYE, 1.25))

LEFT_BLINK_EYE = polygon([
    (530, 160), (532, 158), (538, 157), (546, 157), (554, 158),
    (561, 160), (567, 162), (568, 164), (564, 167), (557, 169),
    (549, 170), (541, 169), (535, 167), (531, 164),
])
RIGHT_BLINK_EYE = polygon([
    (590, 159), (592, 157), (598, 156), (605, 156), (612, 157),
    (619, 159), (623, 161), (622, 164), (618, 167), (611, 169),
    (603, 170), (597, 168), (592, 165),
])
EYE_BLINK_RAW = np.maximum(LEFT_BLINK_EYE, RIGHT_BLINK_EYE)
EYE_BLINK_WEIGHT = np.maximum(feather(LEFT_BLINK_EYE, 1.15), feather(RIGHT_BLINK_EYE, 1.15))

# Neutral blink replaces the source's open eye plus the neutral lid donor.
NEUTRAL_BLINK_LEFT_RAW = np.maximum(LEFT_BLINK_EYE, LEFT_OPEN_EYE)
NEUTRAL_BLINK_RIGHT_RAW = np.maximum(RIGHT_BLINK_EYE, RIGHT_OPEN_EYE)
# The Neutral open lash sits one pixel above its main contour through this
# short segment. Keep that correction separate so it cannot widen the whole eye.
NEUTRAL_LEFT_UPPER_LASH_RAW = polygon([
    (556, 155), (561, 154), (566, 155), (569, 158),
    (568, 160), (564, 161), (559, 159), (556, 157),
])
NEUTRAL_BLINK_LEFT_RAW = np.maximum(NEUTRAL_BLINK_LEFT_RAW, NEUTRAL_LEFT_UPPER_LASH_RAW)
NEUTRAL_BLINK_RAW = np.maximum(NEUTRAL_BLINK_LEFT_RAW, NEUTRAL_BLINK_RIGHT_RAW)
NEUTRAL_BLINK_WEIGHT = np.maximum(
    feather(NEUTRAL_BLINK_LEFT_RAW, 1.15), feather(NEUTRAL_BLINK_RIGHT_RAW, 1.15)
)
# Fully replace the original open-eye footprint before placing a closed lid.
# The lid donor still feathers only along its added outer contour.
NEUTRAL_BLINK_WEIGHT[LEFT_OPEN_EYE > 0] = 1.0
NEUTRAL_BLINK_WEIGHT[RIGHT_OPEN_EYE > 0] = 1.0

# Happy open eyes: independently traced from the Happy donor. Keep the contour
# inside the lash/sclera shape; the first draft extended the right mask into
# hair and both masks replaced excess upper-lid skin.
HAPPY_OPEN_LEFT_CORE_RAW = polygon([
    (529, 158), (530, 154), (535, 153), (542, 153), (550, 154),
    (557, 155), (564, 157), (570, 159), (572, 161), (569, 164),
    (563, 166), (555, 168), (546, 169), (538, 168), (532, 165),
])
HAPPY_OPEN_RIGHT_CORE_RAW = polygon([
    (592, 163), (594, 160), (599, 158), (606, 158), (613, 159),
    (619, 160), (624, 161), (626, 163), (625, 166), (621, 168),
    (614, 170), (606, 171), (599, 169), (594, 166),
])
HAPPY_LEFT_LASH_TIP_RAW = polygon([
    (567, 156), (570, 157), (573, 159), (574, 161),
    (572, 163), (569, 162), (566, 160),
])
HAPPY_LEFT_OUTER_LASH_RAW = polygon([
    (569, 161), (572, 161), (573, 163), (571, 164), (569, 164),
])
HAPPY_RIGHT_LASH_TIP_RAW = polygon([
    (623, 159), (625, 159), (626, 161), (625, 163), (623, 162),
])
HAPPY_OPEN_LEFT_RAW = np.maximum.reduce((
    HAPPY_OPEN_LEFT_CORE_RAW, HAPPY_LEFT_LASH_TIP_RAW, HAPPY_LEFT_OUTER_LASH_RAW,
))
HAPPY_OPEN_RIGHT_RAW = np.maximum(HAPPY_OPEN_RIGHT_CORE_RAW, HAPPY_RIGHT_LASH_TIP_RAW)
HAPPY_OPEN_RAW = np.maximum(HAPPY_OPEN_LEFT_RAW, HAPPY_OPEN_RIGHT_RAW)
HAPPY_OPEN_WEIGHT = np.maximum(
    feather(HAPPY_OPEN_LEFT_RAW, 1.0), feather(HAPPY_OPEN_RIGHT_RAW, 1.0)
)
# Happy blink has its own two lid contours, then clears the Happy open-eye
# footprint. The slight outer lash extensions are local rather than a larger
# oval around the full eye.
HAPPY_BLINK_LID_LEFT_RAW = polygon([
    (529, 164), (532, 161), (540, 160), (549, 160), (559, 161),
    (567, 163), (571, 165), (568, 168), (560, 170), (551, 171),
    (542, 170), (534, 168),
])
HAPPY_BLINK_LID_RIGHT_RAW = polygon([
    (592, 168), (595, 165), (601, 164), (609, 164), (617, 165),
    (623, 167), (625, 169), (622, 172), (615, 174), (606, 174),
    (598, 172), (593, 170),
])
HAPPY_LEFT_UPPER_LASH_RAW = polygon([
    (557, 155), (562, 154), (567, 155), (569, 158),
    (568, 160), (564, 161), (559, 159), (557, 157),
])
HAPPY_BLINK_LEFT_RAW = np.maximum.reduce((
    HAPPY_OPEN_LEFT_RAW, HAPPY_BLINK_LID_LEFT_RAW, HAPPY_LEFT_UPPER_LASH_RAW,
))
HAPPY_BLINK_RIGHT_RAW = np.maximum(HAPPY_OPEN_RIGHT_RAW, HAPPY_BLINK_LID_RIGHT_RAW)
HAPPY_BLINK_RAW = np.maximum(HAPPY_BLINK_LEFT_RAW, HAPPY_BLINK_RIGHT_RAW)
HAPPY_BLINK_WEIGHT = np.maximum(
    feather(HAPPY_BLINK_LEFT_RAW, 0.95), feather(HAPPY_BLINK_RIGHT_RAW, 0.95)
)
HAPPY_BLINK_WEIGHT[HAPPY_OPEN_LEFT_RAW > 0] = 1.0
HAPPY_BLINK_WEIGHT[HAPPY_OPEN_RIGHT_RAW > 0] = 1.0

# Shocked open eyes: independent, wider contours that stop below the brow.
LEFT_SHOCK_EYE_CORE = polygon([
    (529, 158), (531, 152), (536, 150), (543, 150), (551, 151),
    (559, 153), (566, 156), (572, 159), (574, 162), (571, 165),
    (565, 167), (556, 169), (546, 170), (538, 169), (532, 166),
])
RIGHT_SHOCK_EYE_CORE = polygon([
    (593, 162), (595, 158), (600, 156), (606, 156), (613, 156),
    (619, 157), (624, 159), (626, 161), (625, 164), (621, 167),
    (614, 169), (606, 170), (598, 169), (594, 166),
])
SHOCKED_LEFT_LASH_TIP_RAW = polygon([
    (566, 156), (570, 157), (573, 159), (574, 161),
    (572, 163), (569, 162), (565, 160),
])
SHOCKED_LEFT_OUTER_LASH_RAW = polygon([
    (569, 161), (572, 161), (573, 163), (571, 164), (569, 164),
])
SHOCKED_RIGHT_LASH_TIP_RAW = polygon([
    (620, 155), (623, 155), (625, 157), (625, 160),
    (623, 162), (620, 160),
])
SHOCKED_LEFT_OUTER_LASH_TIP_RAW = polygon([
    # Keep the tiny outer lash pixels while leaving the adjacent fringe strand
    # (x <= 528) untouched.
    (529, 155), (531, 155), (532, 157), (531, 159), (529, 159),
])
SHOCKED_RIGHT_UPPER_LASH_TIP_RAW = polygon([
    # The outer upper lash tip stays separate from the central fringe strand.
    (623, 157), (625, 157), (626, 159), (625, 162), (622, 163), (620, 161),
])
# The 20x donor/result review found a few genuine upper-lash pixels outside the
# two traced shocked contours. Record these as separate, per-eye pixel patches
# in the donor's unshifted coordinates so they move with the local registration.
# Left: retain the antialiased lid connection, but omit the single donor pixel
# that sticks upward as a square and reads as a stray mark in the decoded pose.
# Right: a 3px lid bridge plus two upper tips.
SHOCKED_LEFT_OPEN_LASH_DETAIL_RAW = exact_pixels([
    (540, 149),
])
SHOCKED_RIGHT_OPEN_LASH_DETAIL_RAW = exact_pixels([
    (617, 155), (617, 156), (618, 156), (619, 156), (623, 154),
])
LEFT_SHOCK_EYE = np.maximum.reduce((
    LEFT_SHOCK_EYE_CORE, SHOCKED_LEFT_LASH_TIP_RAW,
    SHOCKED_LEFT_OUTER_LASH_RAW, SHOCKED_LEFT_OUTER_LASH_TIP_RAW,
    SHOCKED_LEFT_OPEN_LASH_DETAIL_RAW,
))
RIGHT_SHOCK_EYE = np.maximum.reduce((
    RIGHT_SHOCK_EYE_CORE, SHOCKED_RIGHT_LASH_TIP_RAW,
    SHOCKED_RIGHT_UPPER_LASH_TIP_RAW, SHOCKED_RIGHT_OPEN_LASH_DETAIL_RAW,
))
SHOCK_EYE_RAW = np.maximum(LEFT_SHOCK_EYE, RIGHT_SHOCK_EYE)
SHOCK_EYE_WEIGHT = np.maximum(feather(LEFT_SHOCK_EYE, 1.25), feather(RIGHT_SHOCK_EYE, 1.25))
# Shocked blink follows the wider Shocked lid donors independently from the
# Neutral and Happy contours.
SHOCKED_BLINK_LID_LEFT_RAW = polygon([
    (529, 163), (533, 160), (543, 159), (553, 159), (563, 160),
    (570, 162), (573, 164), (568, 167), (559, 170), (549, 171),
    (539, 169), (532, 166),
])
SHOCKED_BLINK_LID_RIGHT_RAW = polygon([
    (593, 168), (596, 165), (602, 164), (610, 164), (618, 165),
    (623, 167), (625, 169), (622, 172), (615, 174), (607, 174),
    (599, 172), (594, 170),
])
SHOCKED_BLINK_LEFT_RAW = np.maximum(LEFT_SHOCK_EYE, SHOCKED_BLINK_LID_LEFT_RAW)
SHOCKED_BLINK_RIGHT_RAW = np.maximum(RIGHT_SHOCK_EYE, SHOCKED_BLINK_LID_RIGHT_RAW)
SHOCKED_BLINK_RAW = np.maximum(SHOCKED_BLINK_LEFT_RAW, SHOCKED_BLINK_RIGHT_RAW)
SHOCKED_BLINK_WEIGHT = np.maximum(
    feather(SHOCKED_BLINK_LEFT_RAW, 0.95), feather(SHOCKED_BLINK_RIGHT_RAW, 0.95)
)
SHOCKED_BLINK_WEIGHT[LEFT_SHOCK_EYE > 0] = 1.0
SHOCKED_BLINK_WEIGHT[RIGHT_SHOCK_EYE > 0] = 1.0

# Mouth contours include only a narrow edge around the changed lips, and are
# specific to each expression. In particular, shocked speech is much shorter
# than the surprised O mouth.
NEUTRAL_TALK_RAW = polygon([
    (563, 207), (564, 204), (568, 202), (574, 201), (580, 202),
    (585, 203), (588, 205), (587, 208), (583, 210), (578, 212),
    (572, 212), (567, 210), (564, 208),
])
HAPPY_CLOSED_RAW = polygon([
    (556, 202), (559, 200), (564, 199), (570, 201), (578, 203),
    (584, 203), (589, 201), (591, 203), (589, 206), (585, 208),
    (579, 210), (573, 210), (566, 208), (560, 206), (557, 204),
])
HAPPY_TALK_SHAPE_RAW = polygon([
    (560, 207), (561, 203), (565, 200), (571, 199), (578, 199),
    (584, 201), (588, 203), (590, 206), (588, 210), (584, 213),
    (578, 215), (572, 215), (566, 213), (562, 210),
])
# Talking must remove every pixel of the closed smile first. The former
# talking contour missed the two ends of that smile, leaving a second arc.
HAPPY_TALK_RAW = np.maximum(
    HAPPY_TALK_SHAPE_RAW,
    cv2.dilate(HAPPY_CLOSED_RAW, np.ones((3, 3), np.uint8)),
)
SHOCKED_O_RAW = polygon([
    (560, 208), (561, 204), (564, 201), (569, 199), (576, 199),
    (583, 201), (588, 204), (590, 208), (588, 212), (584, 216),
    (578, 218), (571, 217), (565, 214), (561, 211),
])
SHOCKED_TALK_RAW = polygon([
    # Replace the source closed-mouth line and the full shocked-O footprint.
    # The v3 donor is a smaller, softer speaking shape; clearing the whole
    # previous mouth prevents red O edges from peeking out around it.
    (552, 199), (555, 196), (562, 194), (580, 194), (589, 197),
    (594, 201), (595, 208), (592, 214), (586, 218), (577, 220),
    (566, 219), (558, 216), (553, 211), (551, 205),
])
NEUTRAL_TALK_WEIGHT = feather(NEUTRAL_TALK_RAW, 1.25)
HAPPY_CLOSED_WEIGHT = feather(HAPPY_CLOSED_RAW, 1.25)
HAPPY_TALK_WEIGHT = feather(HAPPY_TALK_RAW, 1.25)
# The source smile must be completely gone in every talking frame. Keep the
# surrounding talking contour feathered, but force full donor coverage over
# each pixel of the individually traced closed-smile footprint.
HAPPY_TALK_WEIGHT[HAPPY_CLOSED_RAW > 0] = 1.0
SHOCKED_O_WEIGHT = feather(SHOCKED_O_RAW, 1.25)
SHOCKED_TALK_WEIGHT = feather(SHOCKED_TALK_RAW, 1.25)
EYE_ANY_RAW = np.maximum.reduce((
    EYE_OPEN_RAW, NEUTRAL_BLINK_RAW, HAPPY_BLINK_RAW, SHOCK_EYE_RAW, SHOCKED_BLINK_RAW,
))
MOUTH_ANY_RAW = np.maximum.reduce((
    NEUTRAL_TALK_RAW, HAPPY_CLOSED_RAW, HAPPY_TALK_RAW, SHOCKED_O_RAW, SHOCKED_TALK_RAW,
))
assert np.all(HAPPY_TALK_RAW[HAPPY_CLOSED_RAW > 0] > 0), 'Happy speech mask must clear the full closed smile.'
assert np.all(HAPPY_TALK_WEIGHT[HAPPY_CLOSED_RAW > 0] == 1.0), 'Happy speech must fully replace closed-smile pixels.'
assert np.all(NEUTRAL_BLINK_WEIGHT[LEFT_OPEN_EYE > 0] == 1.0)
assert np.all(NEUTRAL_BLINK_WEIGHT[RIGHT_OPEN_EYE > 0] == 1.0)
assert np.all(HAPPY_BLINK_WEIGHT[HAPPY_OPEN_LEFT_RAW > 0] == 1.0)
assert np.all(HAPPY_BLINK_WEIGHT[HAPPY_OPEN_RIGHT_RAW > 0] == 1.0)
assert np.all(SHOCKED_BLINK_WEIGHT[LEFT_SHOCK_EYE > 0] == 1.0)
assert np.all(SHOCKED_BLINK_WEIGHT[RIGHT_SHOCK_EYE > 0] == 1.0)

# Local ECC against unchanged skin/jaw landmarks removes remaining fractional
# mouth displacement after whole-face alignment. The selected v3 shocked-talk
# crop is pre-registered against the exact source and needs no second shift.
LOCAL_MOUTH_ALIGN = {
    'neutral_talk_mouth.png': (-0.80, -1.50),
    'happy_mouth.png': (-0.20, -0.53),
    'happy_talk_mouth.png': (-0.19, -0.76),
    'shocked_mouth.png': (-0.90, -1.46),
    'shocked_talk_mouth_v3.png': (0.0, 0.0),
}

# Whole-face ECC leaves small, donor-specific residuals around each eye. These
# integer offsets were rechecked against the adjacent hair and eyelid corners;
# the mask follows the same offset, while each expression keeps its own contour.
LOCAL_EYE_ALIGN = {
    'neutral_blink_eyes.png': ((0, 0), (-2, 0)),
    'happy_eyes.png': ((0, 2), (-1, 0)),
    'happy_blink_eyes.png': ((0, 2), (-1, -1)),
    'shocked_eyes.png': ((2, 1), (-2, 1)),
    'shocked_blink_eyes.png': ((2, 0), (-2, 0)),
}


def translate_mask(raw, shift):
    """Move one hand-traced contour with its donor, without antialiasing it."""
    dx, dy = shift
    return cv2.warpAffine(
        raw, np.asarray([[1, 0, dx], [0, 1, dy]], dtype=np.float32), (W, H),
        flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0,
    )


# The guards prevent the donor from repainting hair outside the eye feature.
# They are not the foreground-hair treatment: strands that overlap the feature
# are extracted from BASE below and restored over the aligned donor afterward.
NEUTRAL_LEFT_FRINGE_GUARD = polygon([
    (520, 143), (528, 143), (528, 150), (527, 157), (526, 165),
    (524, 172), (521, 178), (518, 178), (519, 169), (520, 159), (520, 150),
])
NEUTRAL_RIGHT_FRINGE_GUARD = polygon([(605, 140), (606, 140), (606, 154), (605, 154)])
HAPPY_LEFT_FRINGE_GUARD = polygon([
    (520, 143), (528, 143), (528, 150), (527, 157), (526, 165),
    (524, 172), (521, 178), (518, 178), (519, 169), (520, 159), (520, 150),
])
HAPPY_RIGHT_FRINGE_GUARD = polygon([(605, 140), (606, 140), (606, 154), (605, 154)])
SHOCKED_LEFT_FRINGE_GUARD = polygon([
    (520, 143), (528, 143), (528, 150), (527, 157), (526, 165),
    (524, 172), (521, 178), (518, 178), (519, 169), (520, 159), (520, 150),
])
SHOCKED_RIGHT_FRINGE_GUARD = polygon([(605, 140), (606, 140), (606, 154), (605, 154)])


def protect_fringe(raw, guard):
    return np.where(guard > 0, 0, raw).astype(np.uint8)


# The first-pass contours were traced against the registered donors. Local
# alignment now moves each donor and its contour together. Union the original
# neutral eye footprint back into each open/blink mask so no source lash is
# stranded beneath the moved donor. Each expression remains independently
# traced; its source cleanup is only the small neutral eye footprint.
_neutral_blink_seed = (
    np.maximum(LEFT_BLINK_EYE, NEUTRAL_LEFT_UPPER_LASH_RAW), RIGHT_BLINK_EYE,
)
_happy_open_seed = (HAPPY_OPEN_LEFT_RAW.copy(), HAPPY_OPEN_RIGHT_RAW.copy())
_happy_blink_seed = (
    np.maximum(HAPPY_BLINK_LID_LEFT_RAW, HAPPY_LEFT_UPPER_LASH_RAW),
    HAPPY_BLINK_LID_RIGHT_RAW.copy(),
)
_shocked_open_seed = (LEFT_SHOCK_EYE.copy(), RIGHT_SHOCK_EYE.copy())
_shocked_blink_seed = (
    SHOCKED_BLINK_LID_LEFT_RAW.copy(), SHOCKED_BLINK_LID_RIGHT_RAW.copy(),
)

LEFT_OPEN_EYE = protect_fringe(LEFT_OPEN_EYE, NEUTRAL_LEFT_FRINGE_GUARD)
RIGHT_OPEN_EYE = protect_fringe(RIGHT_OPEN_EYE, NEUTRAL_RIGHT_FRINGE_GUARD)
EYE_OPEN_RAW = np.maximum(LEFT_OPEN_EYE, RIGHT_OPEN_EYE)
NEUTRAL_BLINK_LEFT_RAW = protect_fringe(np.maximum(
    translate_mask(_neutral_blink_seed[0], LOCAL_EYE_ALIGN['neutral_blink_eyes.png'][0]),
    LEFT_OPEN_EYE,
), NEUTRAL_LEFT_FRINGE_GUARD)
NEUTRAL_BLINK_RIGHT_RAW = protect_fringe(np.maximum(
    translate_mask(_neutral_blink_seed[1], LOCAL_EYE_ALIGN['neutral_blink_eyes.png'][1]),
    RIGHT_OPEN_EYE,
), NEUTRAL_RIGHT_FRINGE_GUARD)
HAPPY_OPEN_LEFT_RAW = protect_fringe(np.maximum(
    translate_mask(_happy_open_seed[0], LOCAL_EYE_ALIGN['happy_eyes.png'][0]),
    np.zeros((H, W), np.uint8),
), HAPPY_LEFT_FRINGE_GUARD)
HAPPY_OPEN_RIGHT_RAW = protect_fringe(np.maximum(
    translate_mask(_happy_open_seed[1], LOCAL_EYE_ALIGN['happy_eyes.png'][1]),
    np.zeros((H, W), np.uint8),
), HAPPY_RIGHT_FRINGE_GUARD)
HAPPY_BLINK_LEFT_RAW = protect_fringe(np.maximum(
    translate_mask(_happy_blink_seed[0], LOCAL_EYE_ALIGN['happy_blink_eyes.png'][0]), HAPPY_OPEN_LEFT_RAW,
), HAPPY_LEFT_FRINGE_GUARD)
HAPPY_BLINK_RIGHT_RAW = protect_fringe(np.maximum(
    translate_mask(_happy_blink_seed[1], LOCAL_EYE_ALIGN['happy_blink_eyes.png'][1]), HAPPY_OPEN_RIGHT_RAW,
), HAPPY_RIGHT_FRINGE_GUARD)
LEFT_SHOCK_EYE = protect_fringe(np.maximum(
    translate_mask(_shocked_open_seed[0], LOCAL_EYE_ALIGN['shocked_eyes.png'][0]),
    np.zeros((H, W), np.uint8),
), SHOCKED_LEFT_FRINGE_GUARD)
RIGHT_SHOCK_EYE = protect_fringe(np.maximum(
    translate_mask(_shocked_open_seed[1], LOCAL_EYE_ALIGN['shocked_eyes.png'][1]),
    np.zeros((H, W), np.uint8),
), SHOCKED_RIGHT_FRINGE_GUARD)
# Regression checks for the donor-only upper-lash pixels added after the 20x
# and 40x source/donor/result review. These stay expression- and eye-specific.
assert LEFT_SHOCK_EYE[150, 542] > 0
assert LEFT_SHOCK_EYE[150, 549] == 0, 'Keep the square donor pixel out of the shocked left mask.'
assert all(RIGHT_SHOCK_EYE[y, x] > 0 for x, y in (
    (615, 156), (615, 157), (616, 157), (617, 157), (621, 155),
))
SHOCKED_BLINK_LEFT_RAW = protect_fringe(np.maximum(
    translate_mask(_shocked_blink_seed[0], LOCAL_EYE_ALIGN['shocked_blink_eyes.png'][0]), LEFT_SHOCK_EYE,
), SHOCKED_LEFT_FRINGE_GUARD)
SHOCKED_BLINK_RIGHT_RAW = protect_fringe(np.maximum(
    translate_mask(_shocked_blink_seed[1], LOCAL_EYE_ALIGN['shocked_blink_eyes.png'][1]), RIGHT_SHOCK_EYE,
), SHOCKED_RIGHT_FRINGE_GUARD)


def source_hair_pixels(trace):
    """Extract only dark original hair pixels inside a hand-traced strand path.

    The source RGBA values are retained verbatim. The narrow trace is a spatial
    selection; the color test removes adjacent skin pixels while retaining the
    antialiased brown edge of the hair stroke.
    """
    rgb = BASE[:, :, :3].astype(np.int16)
    trace = trace > 0
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    luminance = (r * 30 + g * 59 + b * 11) // 100
    # The source contains shaded skin inside two of these very narrow traces;
    # luminance alone accidentally classified it as hair and brought back a
    # dark eye pixel in the blink GIF. Keep the brown/charcoal strand core and
    # its darker antialias, excluding the pink skin and eyelash tones.
    hair_tone = (
        (luminance < 178) & (r < 155) & (g < 125)
        & (r - g < 52) & (g - b < 38)
    )
    return np.where(trace & hair_tone, 255, 0).astype(np.uint8)


# Precise foreground strand traces from the exact neutral source. The left
# strand falls across the outer edge of the left eye; the narrow center lock
# crosses its inner lash. The right-side lock crosses the inner corner and the
# outer fringe meets the far lash tip. These masks contain only source hair
# pixels, not the entire eye or eyebrow region.
_LEFT_OUTER_LOCK = source_hair_pixels(polygon([
    (526, 143), (535, 143), (535, 150), (534, 157), (533, 164),
    (532, 171), (530, 178), (526, 178), (527, 169), (528, 160),
    (528, 151),
]))
_LEFT_CENTER_LOCK = source_hair_pixels(polygon([
    # Stop above the source upper-lash line. The earlier tail reached y162 and
    # restored lash pixels into the closed-lid state as a detached dark block.
    (556, 141), (560, 141), (560, 146), (560, 151), (559, 154),
    (557, 154), (556, 149),
]))
_RIGHT_INNER_LOCK = source_hair_pixels(polygon([
    # End above the upper lid as well; only the brown forelock is preserved.
    (603, 139), (609, 139), (609, 145), (608, 150), (607, 153),
    (604, 153), (603, 148), (604, 144),
]))
_RIGHT_OUTER_LOCK = source_hair_pixels(polygon([
    (623, 143), (630, 143), (630, 151), (629, 159), (628, 167),
    (626, 173), (623, 171), (624, 163), (624, 154),
]))


def expression_hair_layer(feature_mask, side):
    """Limit the original strand extraction to pixels the donor can affect."""
    strand = np.maximum(_LEFT_OUTER_LOCK, _LEFT_CENTER_LOCK) if side == 0 else np.maximum(
        _RIGHT_INNER_LOCK, _RIGHT_OUTER_LOCK
    )
    affected = cv2.dilate(feature_mask, np.ones((3, 3), np.uint8)) > 0
    return np.where((strand > 0) & affected, 255, 0).astype(np.uint8)


# Separate source-pixel layers for every expression/eye pair. Their coverage
# follows that expression's own open/blink masks, even where two shapes differ.
NEUTRAL_FOREGROUND_HAIR = (
    expression_hair_layer(NEUTRAL_BLINK_LEFT_RAW, 0),
    expression_hair_layer(NEUTRAL_BLINK_RIGHT_RAW, 1),
)
HAPPY_FOREGROUND_HAIR = (
    expression_hair_layer(np.maximum(HAPPY_OPEN_LEFT_RAW, HAPPY_BLINK_LEFT_RAW), 0),
    expression_hair_layer(np.maximum(HAPPY_OPEN_RIGHT_RAW, HAPPY_BLINK_RIGHT_RAW), 1),
)
SHOCKED_FOREGROUND_HAIR = (
    expression_hair_layer(np.maximum(LEFT_SHOCK_EYE, SHOCKED_BLINK_LEFT_RAW), 0),
    expression_hair_layer(np.maximum(RIGHT_SHOCK_EYE, SHOCKED_BLINK_RIGHT_RAW), 1),
)
FOREGROUND_HAIR_MASKS = {
    'neutral': NEUTRAL_FOREGROUND_HAIR,
    'happy': HAPPY_FOREGROUND_HAIR,
    'shocked': SHOCKED_FOREGROUND_HAIR,
}

# Let the expression donor replace the eye pixels under each traced strand.
# The exact source pixels are composited back in the foreground layer below.
# This is the key separation between the eye edit and the preserved hair.
NEUTRAL_BLINK_LEFT_RAW = np.maximum(NEUTRAL_BLINK_LEFT_RAW, NEUTRAL_FOREGROUND_HAIR[0])
NEUTRAL_BLINK_RIGHT_RAW = np.maximum(NEUTRAL_BLINK_RIGHT_RAW, NEUTRAL_FOREGROUND_HAIR[1])
HAPPY_OPEN_LEFT_RAW = np.maximum(HAPPY_OPEN_LEFT_RAW, HAPPY_FOREGROUND_HAIR[0])
HAPPY_OPEN_RIGHT_RAW = np.maximum(HAPPY_OPEN_RIGHT_RAW, HAPPY_FOREGROUND_HAIR[1])
HAPPY_BLINK_LEFT_RAW = np.maximum(HAPPY_BLINK_LEFT_RAW, HAPPY_FOREGROUND_HAIR[0])
HAPPY_BLINK_RIGHT_RAW = np.maximum(HAPPY_BLINK_RIGHT_RAW, HAPPY_FOREGROUND_HAIR[1])
LEFT_SHOCK_EYE = np.maximum(LEFT_SHOCK_EYE, SHOCKED_FOREGROUND_HAIR[0])
RIGHT_SHOCK_EYE = np.maximum(RIGHT_SHOCK_EYE, SHOCKED_FOREGROUND_HAIR[1])
SHOCKED_BLINK_LEFT_RAW = np.maximum(SHOCKED_BLINK_LEFT_RAW, SHOCKED_FOREGROUND_HAIR[0])
SHOCKED_BLINK_RIGHT_RAW = np.maximum(SHOCKED_BLINK_RIGHT_RAW, SHOCKED_FOREGROUND_HAIR[1])

FOREGROUND_HAIR_RESTORE_STATS = {name: {'pixels_examined': 0, 'donor_pixels_replaced': 0}
                                 for name in FOREGROUND_HAIR_MASKS}


def restore_foreground_hair(canvas, expression):
    """Composite exact source hair RGB/alpha over one expression's eye donor."""
    mask = np.maximum(*FOREGROUND_HAIR_MASKS[expression]) > 0
    out = canvas.copy()
    changed_under_strand = np.any(out[mask][:, :3] != BASE[mask][:, :3], axis=1)
    stats = FOREGROUND_HAIR_RESTORE_STATS[expression]
    stats['pixels_examined'] = max(stats['pixels_examined'], int(mask.sum()))
    stats['donor_pixels_replaced'] = max(
        stats['donor_pixels_replaced'], int(changed_under_strand.sum())
    )
    out[mask] = BASE[mask]
    return out

# Rebuild destination-space contours and opaque replacement weights after each
# expression-specific placement. The open-eye footprints are fully replaced
# during a blink; feathering occurs only on the new outer lid edge.
NEUTRAL_BLINK_RAW = np.maximum(NEUTRAL_BLINK_LEFT_RAW, NEUTRAL_BLINK_RIGHT_RAW)
NEUTRAL_BLINK_WEIGHT = np.maximum(
    feather(NEUTRAL_BLINK_LEFT_RAW, 1.15), feather(NEUTRAL_BLINK_RIGHT_RAW, 1.15)
)
NEUTRAL_BLINK_WEIGHT[LEFT_OPEN_EYE > 0] = 1.0
NEUTRAL_BLINK_WEIGHT[RIGHT_OPEN_EYE > 0] = 1.0
HAPPY_OPEN_RAW = np.maximum(HAPPY_OPEN_LEFT_RAW, HAPPY_OPEN_RIGHT_RAW)
HAPPY_OPEN_WEIGHT = np.maximum(
    feather(HAPPY_OPEN_LEFT_RAW, 1.0), feather(HAPPY_OPEN_RIGHT_RAW, 1.0)
)
HAPPY_BLINK_RAW = np.maximum(HAPPY_BLINK_LEFT_RAW, HAPPY_BLINK_RIGHT_RAW)
HAPPY_BLINK_WEIGHT = np.maximum(
    feather(HAPPY_BLINK_LEFT_RAW, 0.95), feather(HAPPY_BLINK_RIGHT_RAW, 0.95)
)
HAPPY_BLINK_WEIGHT[HAPPY_OPEN_LEFT_RAW > 0] = 1.0
HAPPY_BLINK_WEIGHT[HAPPY_OPEN_RIGHT_RAW > 0] = 1.0
SHOCK_EYE_RAW = np.maximum(LEFT_SHOCK_EYE, RIGHT_SHOCK_EYE)
SHOCK_EYE_WEIGHT = np.maximum(feather(LEFT_SHOCK_EYE, 1.25), feather(RIGHT_SHOCK_EYE, 1.25))
SHOCKED_BLINK_RAW = np.maximum(SHOCKED_BLINK_LEFT_RAW, SHOCKED_BLINK_RIGHT_RAW)
SHOCKED_BLINK_WEIGHT = np.maximum(
    feather(SHOCKED_BLINK_LEFT_RAW, 0.95), feather(SHOCKED_BLINK_RIGHT_RAW, 0.95)
)
SHOCKED_BLINK_WEIGHT[LEFT_SHOCK_EYE > 0] = 1.0
SHOCKED_BLINK_WEIGHT[RIGHT_SHOCK_EYE > 0] = 1.0
# The closed-lid donor leaves a narrow crease transition just beyond the eye
# replacement contours. These are separate, hand-traced cleanup patches for
# each shocked eye. They are deliberately outside the feature masks so the
# donor can carry that short crease into the surrounding skin without widening
# the eye transplant or touching the adjacent fringe.
SHOCKED_BLINK_LEFT_SEAM_REGION = polygon([
    (559, 154), (576, 155), (578, 158), (576, 162),
    (571, 163), (562, 161), (558, 159),
])
SHOCKED_BLINK_RIGHT_SEAM_REGION = polygon([
    (594, 155), (622, 155), (627, 158), (626, 163),
    (620, 164), (599, 162), (593, 160),
])
SHOCKED_BLINK_LEFT_SEAM_RAW = np.where(
    (SHOCKED_BLINK_LEFT_SEAM_REGION > 0) & (SHOCKED_BLINK_LEFT_RAW == 0), 255, 0
).astype(np.uint8)
SHOCKED_BLINK_RIGHT_SEAM_RAW = np.where(
    (SHOCKED_BLINK_RIGHT_SEAM_REGION > 0) & (SHOCKED_BLINK_RIGHT_RAW == 0), 255, 0
).astype(np.uint8)
assert not np.any((SHOCKED_BLINK_LEFT_SEAM_RAW > 0) & (SHOCKED_BLINK_LEFT_RAW > 0))
assert not np.any((SHOCKED_BLINK_RIGHT_SEAM_RAW > 0) & (SHOCKED_BLINK_RIGHT_RAW > 0))
# Neutral and Happy have their own outside-mask cleanup where their closed-lid
# donors meet the source upper-lash line. These narrow regions clear only the
# residual lash crescents; each is clipped against its own blink feature mask.
NEUTRAL_BLINK_LEFT_SEAM_REGION = polygon([
    (536, 151), (546, 150), (553, 152), (556, 155),
    (553, 158), (544, 159), (537, 157),
])
NEUTRAL_BLINK_RIGHT_SEAM_REGION = polygon([
    (603, 156), (612, 155), (621, 157), (625, 160),
    (623, 163), (615, 164), (607, 162),
])
HAPPY_BLINK_LEFT_SEAM_REGION = polygon([
    (535, 151), (545, 150), (553, 152), (556, 155),
    (554, 159), (545, 160), (537, 158),
])
HAPPY_BLINK_RIGHT_SEAM_REGION = polygon([
    (604, 157), (613, 156), (622, 158), (626, 161),
    (623, 164), (615, 165), (607, 163),
])
HAPPY_OPEN_LEFT_SEAM_REGION = polygon([
    (529, 150), (534, 150), (537, 152), (537, 155),
    (534, 156), (530, 154),
])
HAPPY_OPEN_RIGHT_SEAM_REGION = polygon([
    (617, 156), (621, 156), (624, 158), (623, 160),
    (619, 160), (616, 158),
])
NEUTRAL_BLINK_LEFT_SEAM_RAW = np.where(
    (NEUTRAL_BLINK_LEFT_SEAM_REGION > 0) & (NEUTRAL_BLINK_LEFT_RAW == 0), 255, 0
).astype(np.uint8)
NEUTRAL_BLINK_RIGHT_SEAM_RAW = np.where(
    (NEUTRAL_BLINK_RIGHT_SEAM_REGION > 0) & (NEUTRAL_BLINK_RIGHT_RAW == 0), 255, 0
).astype(np.uint8)
HAPPY_BLINK_LEFT_SEAM_RAW = np.where(
    (HAPPY_BLINK_LEFT_SEAM_REGION > 0) & (HAPPY_BLINK_LEFT_RAW == 0), 255, 0
).astype(np.uint8)
HAPPY_BLINK_RIGHT_SEAM_RAW = np.where(
    (HAPPY_BLINK_RIGHT_SEAM_REGION > 0) & (HAPPY_BLINK_RIGHT_RAW == 0), 255, 0
).astype(np.uint8)
HAPPY_OPEN_LEFT_SEAM_RAW = np.where(
    (HAPPY_OPEN_LEFT_SEAM_REGION > 0) & (HAPPY_OPEN_LEFT_RAW == 0), 255, 0
).astype(np.uint8)
HAPPY_OPEN_RIGHT_SEAM_RAW = np.where(
    (HAPPY_OPEN_RIGHT_SEAM_REGION > 0) & (HAPPY_OPEN_RIGHT_RAW == 0), 255, 0
).astype(np.uint8)
for seam_mask, feature_mask in (
    (NEUTRAL_BLINK_LEFT_SEAM_RAW, NEUTRAL_BLINK_LEFT_RAW),
    (NEUTRAL_BLINK_RIGHT_SEAM_RAW, NEUTRAL_BLINK_RIGHT_RAW),
    (HAPPY_BLINK_LEFT_SEAM_RAW, HAPPY_BLINK_LEFT_RAW),
    (HAPPY_BLINK_RIGHT_SEAM_RAW, HAPPY_BLINK_RIGHT_RAW),
    (HAPPY_OPEN_LEFT_SEAM_RAW, HAPPY_OPEN_LEFT_RAW),
    (HAPPY_OPEN_RIGHT_SEAM_RAW, HAPPY_OPEN_RIGHT_RAW),
):
    assert not np.any((seam_mask > 0) & (feature_mask > 0))
EYE_ANY_RAW = np.maximum.reduce((
    EYE_OPEN_RAW, NEUTRAL_BLINK_RAW, HAPPY_BLINK_RAW, SHOCK_EYE_RAW, SHOCKED_BLINK_RAW,
))
assert np.all(NEUTRAL_BLINK_WEIGHT[LEFT_OPEN_EYE > 0] == 1.0)
assert np.all(NEUTRAL_BLINK_WEIGHT[RIGHT_OPEN_EYE > 0] == 1.0)
assert np.all(HAPPY_BLINK_WEIGHT[HAPPY_OPEN_LEFT_RAW > 0] == 1.0)
assert np.all(HAPPY_BLINK_WEIGHT[HAPPY_OPEN_RIGHT_RAW > 0] == 1.0)
assert np.all(SHOCKED_BLINK_WEIGHT[LEFT_SHOCK_EYE > 0] == 1.0)
assert np.all(SHOCKED_BLINK_WEIGHT[RIGHT_SHOCK_EYE > 0] == 1.0)


def load_donor(filename, box):
    patch = np.asarray(Image.open(ASSETS / filename).convert('RGBA'))
    x0, y0, x1, y1 = box
    assert patch.shape == (y1 - y0, x1 - x0, 4), (filename, patch.shape)
    if filename in LOCAL_MOUTH_ALIGN:
        dx, dy = LOCAL_MOUTH_ALIGN[filename]
        warp = np.asarray([[1, 0, dx], [0, 1, dy]], dtype=np.float32)
        patch = cv2.warpAffine(
            patch, warp, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
    donor = BASE.copy()
    donor[y0:y1, x0:x1, :3] = patch[:, :, :3]
    return donor


def load_eye_donor(filename, side):
    """Load one eye donor without resampling its whole-face registration."""
    x0, y0, x1, y1 = EYES_BOX
    patch = np.asarray(Image.open(ASSETS / filename).convert('RGBA'))
    dx, dy = LOCAL_EYE_ALIGN[filename][side]
    warp = np.asarray([[1, 0, dx], [0, 1, dy]], dtype=np.float32)
    aligned = cv2.warpAffine(
        patch, warp, (x1 - x0, y1 - y0), flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_REPLICATE,
    )
    donor = BASE.copy()
    donor[y0:y1, x0:x1, :3] = aligned[:, :, :3]
    return donor


def skin_pixels(rgb):
    r, g, b = rgb[:, :, 0].astype(np.int16), rgb[:, :, 1].astype(np.int16), rgb[:, :, 2].astype(np.int16)
    return (r > 135) & (g > 85) & (b > 55) & (r - g > 12) & (g - b > 4)


def color_correct(donor, raw_mask, box, label, sample_box=None):
    """Match donor RGB to nearby skin-only pixels, outside a dilated feature."""
    x0, y0, x1, y1 = sample_box or box
    region = np.zeros((H, W), bool)
    region[y0:y1, x0:x1] = True
    expanded = cv2.dilate(raw_mask, np.ones((7, 7), np.uint8)) > 0
    valid = region & ~expanded & skin_pixels(BASE[:, :, :3]) & skin_pixels(donor[:, :, :3])
    if int(valid.sum()) < 8:
        valid = region & (raw_mask == 0) & skin_pixels(BASE[:, :, :3]) & skin_pixels(donor[:, :, :3])
    count = int(valid.sum())
    if count:
        delta = donor[:, :, :3].astype(np.float32) - BASE[:, :, :3].astype(np.float32)
        offset = np.median(delta[valid], axis=0)
    else:
        offset = np.zeros(3, np.float32)
    corrected = np.clip(donor[:, :, :3].astype(np.float32) - np.clip(offset, -20, 20), 0, 255)
    return corrected, {'sample_pixels': count, 'donor_minus_source_rgb': [round(float(v), 2) for v in offset]}


def composite(canvas, donor_rgb, weight):
    out = canvas.copy()
    out[:, :, :3] = np.rint(
        canvas[:, :, :3].astype(np.float32) * (1 - weight[:, :, None])
        + donor_rgb.astype(np.float32) * weight[:, :, None]
    ).clip(0, 255).astype(np.uint8)
    out[:, :, 3] = BASE[:, :, 3]
    return out


def save_png(path, array):
    """Write complete PNG bytes atomically so review never sees a partial frame."""
    buffer = io.BytesIO()
    Image.fromarray(array, 'RGBA').save(buffer, format='PNG', optimize=False)
    payload = buffer.getvalue()
    assert payload.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82')
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_bytes(payload)
    with Image.open(tmp) as check:
        check.verify()
    tmp.replace(path)


COLOR_QA = {}


def apply(canvas, filename, box, raw_mask, weight, label):
    donor = load_donor(filename, box)
    donor_rgb, info = color_correct(donor, raw_mask, box, label)
    COLOR_QA[label] = info
    return composite(canvas, donor_rgb, weight)


def apply_eyes(canvas, filename, left_mask, right_mask, label):
    """Composite independently registered and color-matched eye masks."""
    out = canvas
    for side, raw_mask, sample_box in (
        (0, left_mask, (520, 147, 580, 178)),
        (1, right_mask, (580, 147, 635, 178)),
    ):
        donor = load_eye_donor(filename, side)
        donor_rgb, info = color_correct(
            donor, raw_mask, EYES_BOX, f'{label}_{"left" if side == 0 else "right"}',
            sample_box=sample_box,
        )
        COLOR_QA[f'{label}_{"left" if side == 0 else "right"}'] = info
        out = composite(out, donor_rgb, feather(raw_mask, 0.95))
    return out


def apply_shocked_blink_seam_cleanup(canvas, label):
    """Carry the closed-lid donor into two explicit outside-mask seam patches."""
    out = canvas
    specs = (
        (0, SHOCKED_BLINK_LEFT_RAW, SHOCKED_BLINK_LEFT_SEAM_RAW,
         (520, 147, 580, 178), 'left'),
        (1, SHOCKED_BLINK_RIGHT_RAW, SHOCKED_BLINK_RIGHT_SEAM_RAW,
         (580, 147, 635, 178), 'right'),
    )
    for side, feature_mask, seam_mask, sample_box, side_name in specs:
        donor = load_eye_donor('shocked_blink_eyes.png', side)
        donor_rgb, info = color_correct(
            donor, feature_mask, EYES_BOX,
            f'{label}_{side_name}_outside_mask_seam', sample_box=sample_box,
        )
        COLOR_QA[f'{label}_{side_name}_outside_mask_seam'] = info
        # A short inward feather keeps the hand-traced patch edge soft. The
        # patch itself remains disjoint from the feature mask by construction.
        out = composite(out, donor_rgb, feather(seam_mask, 1.5))
    return out


def apply_eye_seam_cleanup(canvas, filename, specs, label):
    """Carry one registered eye donor through its hand-traced edge seams."""
    out = canvas
    for side, feature_mask, seam_mask, sample_box, side_name in specs:
        donor = load_eye_donor(filename, side)
        donor_rgb, info = color_correct(
            donor, feature_mask, EYES_BOX,
            f'{label}_{side_name}_outside_mask_seam', sample_box=sample_box,
        )
        COLOR_QA[f'{label}_{side_name}_outside_mask_seam'] = info
        out = composite(out, donor_rgb, feather(seam_mask, 1.5))
    return out


def make_states():
    neutral_blink = apply_eyes(
        BASE, 'neutral_blink_eyes.png', NEUTRAL_BLINK_LEFT_RAW,
        NEUTRAL_BLINK_RIGHT_RAW, 'neutral_blink_eyes',
    )
    neutral_blink = apply_eye_seam_cleanup(
        neutral_blink, 'neutral_blink_eyes.png', (
            (0, NEUTRAL_BLINK_LEFT_RAW, NEUTRAL_BLINK_LEFT_SEAM_RAW,
             (520, 147, 580, 178), 'left'),
            (1, NEUTRAL_BLINK_RIGHT_RAW, NEUTRAL_BLINK_RIGHT_SEAM_RAW,
             (580, 147, 635, 178), 'right'),
        ), 'neutral_blink_eyes',
    )
    neutral_blink = restore_foreground_hair(neutral_blink, 'neutral')
    neutral_talk = apply(BASE, 'neutral_talk_mouth.png', MOUTH_BOX, NEUTRAL_TALK_RAW, NEUTRAL_TALK_WEIGHT, 'neutral_talk_mouth')
    neutral_blink_talk = apply(neutral_blink, 'neutral_talk_mouth.png', MOUTH_BOX, NEUTRAL_TALK_RAW, NEUTRAL_TALK_WEIGHT, 'neutral_blink_talk_mouth')
    neutral = {
        'idle': BASE,
        'blink': neutral_blink,
        'talking': neutral_talk,
        'blink_talking': neutral_blink_talk,
    }

    happy = apply_eyes(
        BASE, 'happy_eyes.png', HAPPY_OPEN_LEFT_RAW, HAPPY_OPEN_RIGHT_RAW,
        'happy_open_eyes',
    )
    happy = apply_eye_seam_cleanup(
        happy, 'happy_eyes.png', (
            (0, HAPPY_OPEN_LEFT_RAW, HAPPY_OPEN_LEFT_SEAM_RAW,
             (520, 147, 580, 178), 'left'),
            (1, HAPPY_OPEN_RIGHT_RAW, HAPPY_OPEN_RIGHT_SEAM_RAW,
             (580, 147, 635, 178), 'right'),
        ), 'happy_open_eyes',
    )
    happy = restore_foreground_hair(happy, 'happy')
    happy = apply(happy, 'happy_mouth.png', MOUTH_BOX, HAPPY_CLOSED_RAW, HAPPY_CLOSED_WEIGHT, 'happy_closed_mouth')
    happy_blink = apply_eyes(
        happy, 'happy_blink_eyes.png', HAPPY_BLINK_LEFT_RAW,
        HAPPY_BLINK_RIGHT_RAW, 'happy_blink_eyes',
    )
    happy_blink = apply_eye_seam_cleanup(
        happy_blink, 'happy_blink_eyes.png', (
            (0, HAPPY_BLINK_LEFT_RAW, HAPPY_BLINK_LEFT_SEAM_RAW,
             (520, 147, 580, 178), 'left'),
            (1, HAPPY_BLINK_RIGHT_RAW, HAPPY_BLINK_RIGHT_SEAM_RAW,
             (580, 147, 635, 178), 'right'),
        ), 'happy_blink_eyes',
    )
    happy_blink = restore_foreground_hair(happy_blink, 'happy')
    happy_talk = apply(happy, 'happy_talk_mouth.png', MOUTH_BOX, HAPPY_TALK_RAW, HAPPY_TALK_WEIGHT, 'happy_talk_mouth')
    happy_blink_talk = apply(happy_blink, 'happy_talk_mouth.png', MOUTH_BOX, HAPPY_TALK_RAW, HAPPY_TALK_WEIGHT, 'happy_blink_talk_mouth')
    happy_states = {
        'idle': happy,
        'blink': happy_blink,
        'talking': happy_talk,
        'blink_talking': happy_blink_talk,
    }

    shocked_face = apply_eyes(
        BASE, 'shocked_eyes.png', LEFT_SHOCK_EYE, RIGHT_SHOCK_EYE,
        'shocked_open_eyes',
    )
    shocked_face = restore_foreground_hair(shocked_face, 'shocked')
    shocked = apply(shocked_face, 'shocked_mouth.png', MOUTH_BOX, SHOCKED_O_RAW, SHOCKED_O_WEIGHT, 'shocked_surprised_mouth')
    shocked_blink_face = apply_eyes(
        shocked_face, 'shocked_blink_eyes.png', SHOCKED_BLINK_LEFT_RAW,
        SHOCKED_BLINK_RIGHT_RAW, 'shocked_blink_eyes',
    )
    shocked_blink_face = apply_shocked_blink_seam_cleanup(
        shocked_blink_face, 'shocked_blink_eyes'
    )
    shocked_blink_face = restore_foreground_hair(shocked_blink_face, 'shocked')
    shocked_blink = apply_eyes(
        shocked, 'shocked_blink_eyes.png', SHOCKED_BLINK_LEFT_RAW,
        SHOCKED_BLINK_RIGHT_RAW, 'shocked_blink_eyes',
    )
    shocked_blink = apply_shocked_blink_seam_cleanup(
        shocked_blink, 'shocked_blink_eyes'
    )
    shocked_blink = restore_foreground_hair(shocked_blink, 'shocked')
    shocked_talk = apply(shocked_face, 'shocked_talk_mouth_v3.png', MOUTH_BOX, SHOCKED_TALK_RAW, SHOCKED_TALK_WEIGHT, 'shocked_talk_mouth')
    shocked_blink_talk = apply(shocked_blink_face, 'shocked_talk_mouth_v3.png', MOUTH_BOX, SHOCKED_TALK_RAW, SHOCKED_TALK_WEIGHT, 'shocked_blink_talk_mouth')
    shocked_states = {
        'idle': shocked,
        'blink': shocked_blink,
        'talking': shocked_talk,
        'blink_talking': shocked_blink_talk,
    }
    return {'neutral': neutral, 'happy': happy_states, 'shocked': shocked_states}


def render(arr, size=None):
    sprite = Image.fromarray(arr, 'RGBA')
    bg = Image.new('RGBA', sprite.size, '#f0f0f0')
    bg.alpha_composite(sprite)
    rgb = bg.convert('RGB')
    return rgb if size is None else rgb.resize(size, Image.Resampling.LANCZOS)


def save_gif(path, frames, durations, size=None, palette_regions=(), allow_identical_frame_merge=False):
    rendered = [render(frame, size=size) for frame in frames]
    sample_scale = min(1.0, 512 / rendered[0].width, 512 / rendered[0].height)
    sample_size = (max(1, round(rendered[0].width * sample_scale)), max(1, round(rendered[0].height * sample_scale)))
    samples = []
    for index, frame in enumerate(rendered):
        samples.append(frame.resize(sample_size, Image.Resampling.LANCZOS))
        # The full-frame downsample cannot retain enough pixels for eyes and
        # mouths. Weight those regions when learning the shared GIF palette.
        for box, scale in palette_regions:
            crop = frame.crop(box)
            samples.append(crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST))
    sheet = Image.new('RGB', (max(sample.width for sample in samples), sum(sample.height for sample in samples)))
    y = 0
    for sample in samples:
        sheet.paste(sample, (0, y))
        y += sample.height
    palette = sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in rendered]
    tmp = path.with_suffix(path.suffix + '.tmp')
    indexed[0].save(tmp, format='GIF', save_all=True, append_images=indexed[1:], duration=durations, loop=0, disposal=2, optimize=False)
    # Frame count and dimensions alone do not catch truncated compressed image
    # data. Decode every frame before replacing a previously valid preview.
    with Image.open(tmp) as check:
        assert check.size == rendered[0].size, (path.name, check.size, rendered[0].size)
        if allow_identical_frame_merge:
            assert check.n_frames <= len(rendered), (path.name, check.n_frames, len(rendered))
        else:
            assert check.n_frames == len(rendered), (path.name, check.n_frames, len(rendered))
        decoded_duration = 0
        for index in range(check.n_frames):
            check.seek(index)
            check.load()
            decoded_duration += check.info.get('duration', 0)
        assert decoded_duration == sum(durations), (path.name, decoded_duration, sum(durations))
    tmp.replace(path)


def save_all_three_gif(path, states):
    labels = ('idle', 'talking', 'idle', 'blink', 'idle', 'talking', 'blink_talking', 'talking', 'idle')
    durations = (450, 230, 300, 130, 440, 220, 130, 240, 1100)
    frames = []
    for state in labels:
        frame = Image.new('RGBA', (W * 3 + 48, H), '#f0f0f0')
        for index, expression in enumerate(('neutral', 'happy', 'shocked')):
            sprite = Image.fromarray(states[expression][state], 'RGBA')
            frame.alpha_composite(sprite, (24 + index * W, 0))
        frames.append(np.asarray(frame.convert('RGBA')))
    focus = []
    for index in range(3):
        x = 24 + index * W
        focus.extend([
            ((x + 505, 125, x + 640, 185), 2),
            ((x + 545, 182, x + 617, 230), 4),
        ])
    save_gif(path, frames, durations, size=None, palette_regions=focus)


def save_review(states):
    labels = ('idle', 'blink', 'talking', 'blink_talking')
    thumb_size = (260, 347)
    canvas = Image.new('RGB', (thumb_size[0] * 4, (thumb_size[1] + 28) * 3), '#f7f7f7')
    draw = ImageDraw.Draw(canvas)
    for row, expression in enumerate(('neutral', 'happy', 'shocked')):
        for col, state in enumerate(labels):
            x, y = col * thumb_size[0], row * (thumb_size[1] + 28)
            canvas.paste(render(states[expression][state], thumb_size), (x, y + 28))
            draw.text((x + 8, y + 7), f'{expression.title()} · {state.replace("_", " ")}', fill='#222')
    canvas.save(OUT / 'preview_fullbody.jpg', quality=94, optimize=True)

    face_box = (505, 125, 640, 230)
    face_size = ((face_box[2] - face_box[0]) * 3, (face_box[3] - face_box[1]) * 3)
    faces = Image.new('RGB', (face_size[0] * 4, (face_size[1] + 24) * 3), '#f7f7f7')
    d = ImageDraw.Draw(faces)
    for row, expression in enumerate(('neutral', 'happy', 'shocked')):
        for col, state in enumerate(labels):
            cut = Image.fromarray(states[expression][state], 'RGBA').crop(face_box)
            bg = Image.new('RGBA', cut.size, '#f0f0f0')
            bg.alpha_composite(cut)
            x, y = col * face_size[0], row * (face_size[1] + 24)
            faces.paste(bg.convert('RGB').resize(face_size, Image.Resampling.NEAREST), (x, y + 24))
            d.text((x + 6, y + 5), f'{expression.title()} · {state.replace("_", " ")}', fill='#222')
    faces.save(OUT / 'preview_faces.jpg', quality=95, optimize=True)


def save_masks_and_boundaries(states):
    source_bg = Image.new('RGBA', (W, H), '#f0f0f0')
    source_bg.alpha_composite(Image.fromarray(BASE, 'RGBA'))
    over = np.asarray(source_bg).copy()
    for mask, color in ((EYE_ANY_RAW > 0, (35, 210, 70)), (MOUTH_ANY_RAW > 0, (45, 120, 235))):
        for channel, value in enumerate(color):
            over[:, :, channel][mask] = np.uint8(over[:, :, channel][mask] * .5 + value * .5)
    Image.fromarray(over, 'RGBA').crop((515, 130, 630, 225)).resize((920, 760), Image.Resampling.NEAREST).save(OUT / 'feature_masks.png')

    for name in ('happy', 'shocked'):
        changed = np.any(states[name]['idle'][:, :, :3] != BASE[:, :, :3], axis=2).astype(np.uint8)
        boundary = (changed > 0) & (cv2.erode(changed, np.ones((3, 3), np.uint8)) == 0)
        view = np.asarray(source_bg).copy()
        view[boundary] = (0, 255, 0, 255)
        Image.fromarray(view, 'RGBA').crop((515, 130, 630, 225)).resize((920, 760), Image.Resampling.NEAREST).save(OUT / f'{name}_changed_boundary.png')


def save_feature_reviews(states):
    labels = ('idle', 'blink', 'talking', 'blink_talking')
    eye_box = (520, 145, 630, 176)
    mouth_box = (550, 195, 600, 222)
    for name, box, scale, filename in (
        ('eyes', eye_box, 8, 'feature_review_eyes_8x.png'),
        ('mouths', mouth_box, 12, 'feature_review_mouths_12x.png'),
    ):
        width, height = box[2] - box[0], box[3] - box[1]
        panel = (width * scale, height * scale)
        gap = 24
        review = Image.new('RGB', (panel[0] * 4, (panel[1] + gap) * 3), '#f7f7f7')
        draw = ImageDraw.Draw(review)
        for row, expression in enumerate(('neutral', 'happy', 'shocked')):
            for col, state in enumerate(labels):
                cut = Image.fromarray(states[expression][state], 'RGBA').crop(box)
                bg = Image.new('RGBA', cut.size, '#f0f0f0')
                bg.alpha_composite(cut)
                x, y = col * panel[0], row * (panel[1] + gap)
                review.paste(bg.convert('RGB').resize(panel, Image.Resampling.NEAREST), (x, y + gap))
                draw.text((x + 6, y + 5), f'{expression.title()} · {state.replace("_", " ")}', fill='#222')
        review.save(OUT / filename, optimize=True)


def save_blink_mask_reviews():
    """Save source overlays for the expression-specific blink contours."""
    source = Image.new('RGBA', (W, H), '#f0f0f0')
    source.alpha_composite(Image.fromarray(BASE, 'RGBA'))
    for expression, mask in (
        ('neutral', NEUTRAL_BLINK_RAW),
        ('happy', HAPPY_BLINK_RAW),
        ('shocked', SHOCKED_BLINK_RAW),
    ):
        overlay = np.asarray(source).copy()
        selected = mask > 0
        overlay[selected, :3] = np.rint(
            overlay[selected, :3].astype(np.float32) * 0.5
            + np.asarray((35, 210, 70), np.float32) * 0.5
        ).astype(np.uint8)
        Image.fromarray(overlay, 'RGBA').crop((515, 140, 635, 180)).resize(
            (2400, 800), Image.Resampling.NEAREST
        ).save(OUT / f'{expression}_blink_mask_20x.png', optimize=True)


def save_shocked_blink_seam_mask_review(states):
    """Show the core eye mask and separately traced exterior seam patches."""
    regions = (
        ('left', (518, 143, 580, 180), SHOCKED_BLINK_LEFT_RAW, SHOCKED_BLINK_LEFT_SEAM_RAW),
        ('right', (578, 143, 640, 180), SHOCKED_BLINK_RIGHT_RAW, SHOCKED_BLINK_RIGHT_SEAM_RAW),
    )
    scale, gap = 24, 28
    panel_w = max(box[2] - box[0] for _, box, _, _ in regions) * scale
    panel_h = (regions[0][1][3] - regions[0][1][1]) * scale
    review = Image.new('RGB', (panel_w * 2, panel_h + gap), '#f7f7f7')
    draw = ImageDraw.Draw(review)
    state = states['shocked']['blink']
    for index, (side, box, feature_mask, seam_mask) in enumerate(regions):
        overlay = state.copy()
        feature = feature_mask > 0
        seam = seam_mask > 0
        overlay[feature, :3] = np.rint(
            overlay[feature, :3].astype(np.float32) * 0.52
            + np.asarray((45, 200, 80), np.float32) * 0.48
        ).astype(np.uint8)
        overlay[seam, :3] = np.rint(
            overlay[seam, :3].astype(np.float32) * 0.48
            + np.asarray((230, 70, 210), np.float32) * 0.52
        ).astype(np.uint8)
        cut = Image.fromarray(overlay, 'RGBA').crop(box).convert('RGB')
        cut = cut.resize((cut.width * scale, cut.height * scale), Image.Resampling.NEAREST)
        x = index * panel_w
        review.paste(cut, (x, gap))
        draw.text((x + 6, 6), f'Shocked blink · {side} core (green), exterior seam patch (magenta)', fill='#222')
    review.save(OUT / 'shocked_blink_seam_masks_24x.png', optimize=True)


def save_expression_mask_reviews():
    """Show each expression's independent open and blink eye masks at 20x."""
    source = Image.new('RGBA', (W, H), '#f0f0f0')
    source.alpha_composite(Image.fromarray(BASE, 'RGBA'))
    specs = {
        'neutral': (
            (LEFT_OPEN_EYE, RIGHT_OPEN_EYE),
            (NEUTRAL_BLINK_LEFT_RAW, NEUTRAL_BLINK_RIGHT_RAW),
        ),
        'happy': (
            (HAPPY_OPEN_LEFT_RAW, HAPPY_OPEN_RIGHT_RAW),
            (HAPPY_BLINK_LEFT_RAW, HAPPY_BLINK_RIGHT_RAW),
        ),
        'shocked': (
            (LEFT_SHOCK_EYE, RIGHT_SHOCK_EYE),
            (SHOCKED_BLINK_LEFT_RAW, SHOCKED_BLINK_RIGHT_RAW),
        ),
    }
    scale = 20
    eye_boxes = ((518, 143, 580, 180), (578, 143, 640, 180))
    for expression, (open_masks, blink_masks) in specs.items():
        panel_width = max(box[2] - box[0] for box in eye_boxes) * scale
        panel_height = (eye_boxes[0][3] - eye_boxes[0][1]) * scale
        sheet = Image.new('RGB', (panel_width * 2, (panel_height + 30) * 2), '#fafafa')
        draw = ImageDraw.Draw(sheet)
        panels = (
            ('open left', open_masks[0], eye_boxes[0], (40, 190, 80)),
            ('open right', open_masks[1], eye_boxes[1], (40, 190, 80)),
            ('blink left', blink_masks[0], eye_boxes[0], (50, 130, 235)),
            ('blink right', blink_masks[1], eye_boxes[1], (50, 130, 235)),
        )
        for index, (label, mask, box, color) in enumerate(panels):
            overlay = np.asarray(source).copy()
            selected = mask > 0
            overlay[selected, :3] = np.rint(
                overlay[selected, :3].astype(np.float32) * 0.48
                + np.asarray(color, np.float32) * 0.52
            ).astype(np.uint8)
            cut = Image.fromarray(overlay, 'RGBA').crop(box).convert('RGB')
            cut = cut.resize((cut.width * scale, cut.height * scale), Image.Resampling.NEAREST)
            x = (index % 2) * panel_width
            y = (index // 2) * (panel_height + 30)
            sheet.paste(cut, (x, y + 30))
            draw.text((x + 6, y + 6), f'{expression.title()} · {label} mask', fill='#222')
        path = OUT / f'{expression}_eye_masks_20x.png'
        tmp = path.with_suffix('.png.tmp')
        sheet.save(tmp, format='PNG', optimize=False)
        with Image.open(tmp) as check:
            check.verify()
        tmp.replace(path)


def save_gif_detail_reviews():
    """Zoom crops from the actual encoded combined GIFs, not source PNGs."""
    states = (('idle', 0), ('talking', 1), ('blink', 3), ('blink_talking', 6))
    regions = (
        ('left_eye', (518, 143, 580, 180)),
        ('right_eye', (578, 143, 640, 180)),
        ('mouth', (545, 190, 620, 230)),
    )
    scale = 20
    for expression in ('neutral', 'happy', 'shocked'):
        for feature, box in regions:
            panel_size = ((box[2] - box[0]) * scale, (box[3] - box[1]) * scale)
            gap = 24
            review = Image.new(
                'RGB',
                (panel_size[0] * 2, (panel_size[1] + gap) * 2),
                '#f7f7f7',
            )
            draw = ImageDraw.Draw(review)
            for index, (label, frame_index) in enumerate(states):
                # Reopen for each sampled frame so disposal state from a prior
                # seek cannot affect the zoomed GIF review.
                with Image.open(OUT / expression / 'combined.gif') as gif:
                    gif.seek(frame_index)
                    crop = gif.convert('RGB').crop(box).resize(panel_size, Image.Resampling.NEAREST)
                x = (index % 2) * panel_size[0]
                y = (index // 2) * (panel_size[1] + gap)
                review.paste(crop, (x, y + gap))
                draw.text((x + 5, y + 4), f'{expression} · {label}', fill='#222')
            path = OUT / f'gif_{expression}_{feature}_20x.png'
            tmp = path.with_suffix('.png.tmp')
            review.save(tmp, format='PNG', optimize=False)
            with Image.open(tmp) as check:
                check.verify()
            tmp.replace(path)


def save_source_donor_result_reviews(states):
    """Save diagnosis panels from source through the final encoded states.

    These are the primary visual reviews for the pose edit: each feature is
    shown beside its independently aligned/color-matched donor, final state,
    feature/protection/cleanup masks, changed-pixel boundary, and the donor
    pixels that would spill outside the approved edit regions.
    """
    eye_boxes = {
        'left': (518, 143, 580, 180),
        'right': (578, 143, 640, 180),
    }
    eye_specs = {
        'neutral': {
            'left': [('blink', 'neutral_blink_eyes.png', NEUTRAL_BLINK_LEFT_RAW,
                      NEUTRAL_BLINK_LEFT_SEAM_RAW, NEUTRAL_LEFT_FRINGE_GUARD,
                      BASE, states['neutral']['blink'], 0)],
            'right': [('blink', 'neutral_blink_eyes.png', NEUTRAL_BLINK_RIGHT_RAW,
                       NEUTRAL_BLINK_RIGHT_SEAM_RAW, NEUTRAL_RIGHT_FRINGE_GUARD,
                       BASE, states['neutral']['blink'], 1)],
        },
        'happy': {
            'left': [('open', 'happy_eyes.png', HAPPY_OPEN_LEFT_RAW,
                      HAPPY_OPEN_LEFT_SEAM_RAW, HAPPY_LEFT_FRINGE_GUARD,
                      BASE, states['happy']['idle'], 0),
                     ('blink', 'happy_blink_eyes.png', HAPPY_BLINK_LEFT_RAW,
                      HAPPY_BLINK_LEFT_SEAM_RAW, HAPPY_LEFT_FRINGE_GUARD,
                      states['happy']['idle'], states['happy']['blink'], 0)],
            'right': [('open', 'happy_eyes.png', HAPPY_OPEN_RIGHT_RAW,
                       HAPPY_OPEN_RIGHT_SEAM_RAW, HAPPY_RIGHT_FRINGE_GUARD,
                       BASE, states['happy']['idle'], 1),
                      ('blink', 'happy_blink_eyes.png', HAPPY_BLINK_RIGHT_RAW,
                       HAPPY_BLINK_RIGHT_SEAM_RAW, HAPPY_RIGHT_FRINGE_GUARD,
                       states['happy']['idle'], states['happy']['blink'], 1)],
        },
        'shocked': {
            'left': [('open', 'shocked_eyes.png', LEFT_SHOCK_EYE,
                      np.zeros((H, W), np.uint8), SHOCKED_LEFT_FRINGE_GUARD,
                      BASE, states['shocked']['idle'], 0),
                     ('blink', 'shocked_blink_eyes.png', SHOCKED_BLINK_LEFT_RAW,
                      SHOCKED_BLINK_LEFT_SEAM_RAW, SHOCKED_LEFT_FRINGE_GUARD,
                      states['shocked']['idle'], states['shocked']['blink'], 0)],
            'right': [('open', 'shocked_eyes.png', RIGHT_SHOCK_EYE,
                       np.zeros((H, W), np.uint8), SHOCKED_RIGHT_FRINGE_GUARD,
                       BASE, states['shocked']['idle'], 1),
                      ('blink', 'shocked_blink_eyes.png', SHOCKED_BLINK_RIGHT_RAW,
                       SHOCKED_BLINK_RIGHT_SEAM_RAW, SHOCKED_RIGHT_FRINGE_GUARD,
                       states['shocked']['idle'], states['shocked']['blink'], 1)],
        },
    }

    def overlay_masks(source, feature, fringe, cleanup):
        view = source.copy()
        for mask, color in (
            (feature > 0, (35, 205, 75)),
            (fringe > 0, (245, 160, 25)),
            (cleanup > 0, (225, 70, 205)),
        ):
            view[mask, :3] = np.rint(
                view[mask, :3].astype(np.float32) * 0.5
                + np.asarray(color, np.float32) * 0.5
            ).astype(np.uint8)
        return view

    def boundary_overlay(source, result):
        changed = np.any(source[:, :, :3] != result[:, :, :3], axis=2).astype(np.uint8)
        edge = (changed > 0) & (cv2.erode(changed, np.ones((3, 3), np.uint8)) == 0)
        view = source.copy()
        view[edge] = (0, 255, 40, 255)
        return view

    def save_panel(path, rows, box, scale):
        panel_w = (box[2] - box[0]) * scale
        panel_h = (box[3] - box[1]) * scale
        title_h, row_gap = 28, 8
        headings = (
            'input/source', 'aligned + color-matched donor', 'final composite',
            'feature / strand guard / cleanup', 'changed-pixel boundary',
            'donor differences outside approved regions',
        )
        sheet = Image.new(
            'RGB', (panel_w * len(headings), (panel_h + title_h + row_gap) * len(rows)),
            '#fafafa',
        )
        draw = ImageDraw.Draw(sheet)
        for row_idx, (label, source, donor, result, feature, fringe, cleanup) in enumerate(rows):
            y = row_idx * (panel_h + title_h + row_gap)
            views = [
                source,
                donor,
                result,
                overlay_masks(source, feature, fringe, cleanup),
                boundary_overlay(source, result),
            ]
            approved = (feature > 0) | (cleanup > 0)
            unmasked_delta = np.any(donor[:, :, :3] != source[:, :, :3], axis=2) & ~approved
            outside = source.copy()
            outside[unmasked_delta, :3] = (235, 0, 185)
            views.append(outside)
            for col, (view, heading) in enumerate(zip(views, headings)):
                x = col * panel_w
                draw.text((x + 5, y + 5), f'{label} · {heading}', fill='#222')
                crop = Image.fromarray(view, 'RGBA').crop(box).convert('RGB')
                crop = crop.resize((panel_w, panel_h), Image.Resampling.NEAREST)
                sheet.paste(crop, (x, y + title_h))
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.png.tmp')
        sheet.save(tmp, format='PNG', optimize=False)
        with Image.open(tmp) as check:
            check.verify()
        tmp.replace(path)

    review_files = []
    for expression, sides in eye_specs.items():
        for side, specs in sides.items():
            rows = []
            box = eye_boxes[side]
            sample_box = (520, 147, 580, 178) if side == 'left' else (580, 147, 635, 178)
            for label, donor_name, feature, cleanup, fringe, source, result, side_idx in specs:
                aligned = load_eye_donor(donor_name, side_idx)
                corrected_rgb, _ = color_correct(
                    aligned, feature, EYES_BOX,
                    f'review_{expression}_{side}_{label}', sample_box=sample_box,
                )
                corrected = aligned.copy()
                corrected[:, :, :3] = corrected_rgb
                rows.append((label, source, corrected, result, feature, fringe, cleanup))
            path = OUT / f'{expression}_{side}_eye_20x_review.png'
            save_panel(path, rows, box, 20)
            review_files.append(path.name)

    mouth_specs = {
        'neutral': [('talk', 'neutral_talk_mouth.png', NEUTRAL_TALK_RAW,
                     BASE, states['neutral']['talking'])],
        'happy': [('smile', 'happy_mouth.png', HAPPY_CLOSED_RAW,
                   BASE, states['happy']['idle']),
                  ('talk', 'happy_talk_mouth.png', HAPPY_TALK_RAW,
                   states['happy']['idle'], states['happy']['talking'])],
        'shocked': [('surprised O', 'shocked_mouth.png', SHOCKED_O_RAW,
                     BASE, states['shocked']['idle']),
                    ('talk', 'shocked_talk_mouth_v3.png', SHOCKED_TALK_RAW,
                     states['shocked']['idle'], states['shocked']['talking'])],
    }
    mouth_box = (545, 190, 620, 230)
    for expression, specs in mouth_specs.items():
        rows = []
        for label, donor_name, feature, source, result in specs:
            aligned = load_donor(donor_name, MOUTH_BOX)
            corrected_rgb, _ = color_correct(
                aligned, feature, MOUTH_BOX,
                f'review_{expression}_mouth_{label}',
            )
            corrected = aligned.copy()
            corrected[:, :, :3] = corrected_rgb
            rows.append((label, source, corrected, result, feature,
                         np.zeros((H, W), np.uint8), np.zeros((H, W), np.uint8)))
        path = OUT / f'{expression}_mouth_20x_review.png'
        save_panel(path, rows, mouth_box, 20)
        review_files.append(path.name)
    return review_files


def save_shocked_eye_animation_review():
    """Create a 20× animated eye crop from the encoded shocked GIF."""
    regions = ((518, 143, 580, 180), (578, 143, 640, 180))
    scale, gap = 20, 16
    panel_w = max(box[2] - box[0] for box in regions) * scale
    panel_h = (regions[0][3] - regions[0][1]) * scale
    frames, durations = [], []
    with Image.open(OUT / 'shocked/combined.gif') as gif:
        for frame_index in range(gif.n_frames):
            gif.seek(frame_index)
            source = gif.convert('RGBA')
            review = Image.new('RGBA', (panel_w * 2 + gap, panel_h), '#f0f0f0')
            for side, box in enumerate(regions):
                crop = source.crop(box).resize(
                    ((box[2] - box[0]) * scale, (box[3] - box[1]) * scale),
                    Image.Resampling.NEAREST,
                )
                review.alpha_composite(crop, (side * (panel_w + gap), 0))
            frames.append(np.asarray(review, dtype=np.uint8))
            durations.append(gif.info.get('duration', 100))
    path = OUT / 'shocked_eyes_animation_20x.gif'
    save_gif(path, frames, durations, size=None, allow_identical_frame_merge=True)
    with Image.open(path) as check:
        assert check.size == (panel_w * 2 + gap, panel_h), (path.name, check.size)
        assert check.n_frames <= len(frames), (path.name, check.n_frames, len(frames))


def save_foreground_hair_review():
    """Show exact source hair pixels restored over each expression's eye edit."""
    regions = {'left': (518, 143, 580, 180), 'right': (578, 143, 640, 180)}
    scale, label_h, eye_gap, row_gap = 20, 28, 16, 12
    eye_w, eye_h = 62 * scale, 37 * scale
    width = eye_w * 2 + eye_gap
    height = 3 * (eye_h + label_h) + 2 * row_gap
    sheet = Image.new('RGB', (width, height), '#fafafa')
    draw = ImageDraw.Draw(sheet)
    for row, expression in enumerate(('neutral', 'happy', 'shocked')):
        y = row * (eye_h + label_h + row_gap)
        draw.text((4, y + 4), f'{expression.title()} · original source strands restored above the donor', fill='#222')
        for side, box in enumerate(regions.values()):
            x0, y0, x1, y1 = box
            view = BASE[y0:y1, x0:x1].copy()
            mask = FOREGROUND_HAIR_MASKS[expression][side][y0:y1, x0:x1] > 0
            # Cyan identifies the selected coverage; the actual composite uses
            # the exact original source RGBA values without tinting.
            view[mask, :3] = np.rint(
                view[mask, :3].astype(np.float32) * 0.45
                + np.asarray((20, 210, 220), np.float32) * 0.55
            ).astype(np.uint8)
            crop = Image.fromarray(view, 'RGBA').convert('RGB').resize(
                (eye_w, eye_h), Image.Resampling.NEAREST,
            )
            x = side * (eye_w + eye_gap)
            sheet.paste(crop, (x, y + label_h))
            draw.text((x + 4, y + label_h + 4), f'{expression} · {"left" if side == 0 else "right"} hair mask', fill='#222')
    path = OUT / 'foreground_hair_layers_20x.png'
    tmp = path.with_suffix('.png.tmp')
    sheet.save(tmp, format='PNG', optimize=False)
    with Image.open(tmp) as check:
        check.verify()
    tmp.replace(path)
    return path.name


def write_outputs(states):
    qa = {
        'size': [W, H],
        'source_alpha_preserved': True,
        'states': {},
        'color_correction': COLOR_QA,
        'local_mouth_alignment_xy': {name: list(shift) for name, shift in LOCAL_MOUTH_ALIGN.items()},
        'local_eye_alignment_xy': {name: [list(side) for side in shifts] for name, shifts in LOCAL_EYE_ALIGN.items()},
        'expression_masks': {
            'neutral': {
                'open_left_pixels': int(np.count_nonzero(LEFT_OPEN_EYE)),
                'open_right_pixels': int(np.count_nonzero(RIGHT_OPEN_EYE)),
                'blink_left_pixels': int(np.count_nonzero(NEUTRAL_BLINK_LEFT_RAW)),
                'blink_right_pixels': int(np.count_nonzero(NEUTRAL_BLINK_RIGHT_RAW)),
                'blink_seam_cleanup_left_outside_pixels': int(np.count_nonzero(NEUTRAL_BLINK_LEFT_SEAM_RAW)),
                'blink_seam_cleanup_right_outside_pixels': int(np.count_nonzero(NEUTRAL_BLINK_RIGHT_SEAM_RAW)),
            },
            'happy': {
                'open_left_pixels': int(np.count_nonzero(HAPPY_OPEN_LEFT_RAW)),
                'open_right_pixels': int(np.count_nonzero(HAPPY_OPEN_RIGHT_RAW)),
                'blink_left_pixels': int(np.count_nonzero(HAPPY_BLINK_LEFT_RAW)),
                'blink_right_pixels': int(np.count_nonzero(HAPPY_BLINK_RIGHT_RAW)),
                'open_seam_cleanup_left_outside_pixels': int(np.count_nonzero(HAPPY_OPEN_LEFT_SEAM_RAW)),
                'open_seam_cleanup_right_outside_pixels': int(np.count_nonzero(HAPPY_OPEN_RIGHT_SEAM_RAW)),
                'blink_seam_cleanup_left_outside_pixels': int(np.count_nonzero(HAPPY_BLINK_LEFT_SEAM_RAW)),
                'blink_seam_cleanup_right_outside_pixels': int(np.count_nonzero(HAPPY_BLINK_RIGHT_SEAM_RAW)),
            },
            'shocked': {
                'open_left_pixels': int(np.count_nonzero(LEFT_SHOCK_EYE)),
                'open_right_pixels': int(np.count_nonzero(RIGHT_SHOCK_EYE)),
                'blink_left_pixels': int(np.count_nonzero(SHOCKED_BLINK_LEFT_RAW)),
                'blink_right_pixels': int(np.count_nonzero(SHOCKED_BLINK_RIGHT_RAW)),
                'blink_seam_cleanup_left_outside_pixels': int(np.count_nonzero(SHOCKED_BLINK_LEFT_SEAM_RAW)),
                'blink_seam_cleanup_right_outside_pixels': int(np.count_nonzero(SHOCKED_BLINK_RIGHT_SEAM_RAW)),
            },
        },
        'foreground_hair_layers': {
            expression: {
                'left_pixels': int(np.count_nonzero(sides[0])),
                'right_pixels': int(np.count_nonzero(sides[1])),
                **FOREGROUND_HAIR_RESTORE_STATS[expression],
            }
            for expression, sides in FOREGROUND_HAIR_MASKS.items()
        },
        'full_replacement_checks': {
            'neutral_blink_covers_open_left': bool(np.all(NEUTRAL_BLINK_WEIGHT[LEFT_OPEN_EYE > 0] == 1.0)),
            'neutral_blink_covers_open_right': bool(np.all(NEUTRAL_BLINK_WEIGHT[RIGHT_OPEN_EYE > 0] == 1.0)),
            'happy_blink_covers_open_left': bool(np.all(HAPPY_BLINK_WEIGHT[HAPPY_OPEN_LEFT_RAW > 0] == 1.0)),
            'happy_blink_covers_open_right': bool(np.all(HAPPY_BLINK_WEIGHT[HAPPY_OPEN_RIGHT_RAW > 0] == 1.0)),
            'shocked_blink_covers_open_left': bool(np.all(SHOCKED_BLINK_WEIGHT[LEFT_SHOCK_EYE > 0] == 1.0)),
            'shocked_blink_covers_open_right': bool(np.all(SHOCKED_BLINK_WEIGHT[RIGHT_SHOCK_EYE > 0] == 1.0)),
            'happy_talk_covers_closed_smile': bool(np.all(HAPPY_TALK_WEIGHT[HAPPY_CLOSED_RAW > 0] == 1.0)),
        },
        'gifs': {},
    }
    feature_masks = {
        'neutral': (NEUTRAL_BLINK_RAW > 0) | (NEUTRAL_TALK_RAW > 0),
        'happy': (HAPPY_OPEN_RAW > 0) | (HAPPY_BLINK_RAW > 0) | (HAPPY_CLOSED_RAW > 0) | (HAPPY_TALK_RAW > 0),
        'shocked': (SHOCK_EYE_RAW > 0) | (SHOCKED_BLINK_RAW > 0) | (SHOCKED_O_RAW > 0) | (SHOCKED_TALK_RAW > 0),
    }
    explicit_seam_masks = {
        'neutral': (NEUTRAL_BLINK_LEFT_SEAM_RAW > 0) | (NEUTRAL_BLINK_RIGHT_SEAM_RAW > 0),
        'happy': (
            (HAPPY_OPEN_LEFT_SEAM_RAW > 0) | (HAPPY_OPEN_RIGHT_SEAM_RAW > 0)
            | (HAPPY_BLINK_LEFT_SEAM_RAW > 0) | (HAPPY_BLINK_RIGHT_SEAM_RAW > 0)
        ),
        'shocked': (SHOCKED_BLINK_LEFT_SEAM_RAW > 0) | (SHOCKED_BLINK_RIGHT_SEAM_RAW > 0),
    }
    foreground_masks = {
        name: (sides[0] > 0) | (sides[1] > 0)
        for name, sides in FOREGROUND_HAIR_MASKS.items()
    }
    allowed_masks = {
        name: feature_masks[name] | explicit_seam_masks[name] | foreground_masks[name]
        for name in feature_masks
    }
    for expression, group in states.items():
        qa['states'][expression] = {}
        published_folder = PUBLISHED / expression
        published_folder.mkdir(parents=True, exist_ok=True)
        for state, arr in group.items():
            assert arr.shape == BASE.shape
            assert np.array_equal(arr[:, :, 3], BASE[:, :, 3])
            changed = np.any(arr[:, :, :3] != BASE[:, :, :3], axis=2)
            outside_feature = int(np.count_nonzero(changed & ~feature_masks[expression]))
            outside_allowed = int(np.count_nonzero(changed & ~allowed_masks[expression]))
            seam_cleanup_changes = int(np.count_nonzero(changed & explicit_seam_masks[expression]))
            foreground_hair_changes = int(np.count_nonzero(changed & foreground_masks[expression]))
            untracked_outside_feature = int(np.count_nonzero(
                changed & ~feature_masks[expression]
                & ~explicit_seam_masks[expression]
                & ~foreground_masks[expression]
            ))
            assert outside_allowed == 0, (expression, state, outside_allowed)
            assert untracked_outside_feature == 0, (
                expression, state, outside_feature, seam_cleanup_changes,
                foreground_hair_changes, untracked_outside_feature,
            )
            save_png(OUT / f'{expression}_{state}.png', arr)
            save_png(published_folder / f'{state}.png', arr)
            qa['states'][expression][state] = {
                'changed_pixels': int(changed.sum()),
                'changed_outside_feature_masks': outside_feature,
                'changed_in_explicit_outside_mask_seam_cleanup': seam_cleanup_changes,
                'changed_in_foreground_hair_layer': foreground_hair_changes,
                'changed_outside_feature_and_seam_masks': outside_allowed,
                'changed_outside_feature_and_declared_cleanup_layers': untracked_outside_feature,
                'alpha_identical': True,
            }
        folder = OUT / expression
        folder.mkdir(exist_ok=True)
        gifs = {
            'blink.gif': ([group['idle'], group['blink'], group['idle'], group['blink'], group['idle']], [1100, 130, 1300, 130, 1000]),
            'talk.gif': ([group['idle'], group['talking'], group['idle'], group['talking'], group['idle']], [220, 210, 220, 260, 950]),
            'combined.gif': ([group['idle'], group['talking'], group['idle'], group['blink'], group['idle'], group['talking'], group['blink_talking'], group['talking'], group['idle']], [450, 230, 300, 130, 440, 220, 130, 240, 1100]),
        }
        for gif_name, (frames, durations) in gifs.items():
            gif_path = folder / gif_name
            save_gif(gif_path, frames, durations, palette_regions=[
                ((505, 125, 640, 185), 2),
                ((545, 182, 617, 230), 4),
            ])
            shutil.copy2(gif_path, published_folder / gif_name)
            with Image.open(gif_path) as gif:
                assert gif.size == (W, H), (gif_name, gif.size)
                qa['gifs'][f'{expression}/{gif_name}'] = {'size': list(gif.size), 'frames': gif.n_frames}
        if expression != 'neutral':
            save_png(ROOT / f'static/poses/document_reading/{expression}.png', group['idle'])

    all_three_path = OUT / 'all_three_native.gif'
    save_all_three_gif(all_three_path, states)
    shutil.copy2(all_three_path, PUBLISHED / all_three_path.name)
    with Image.open(all_three_path) as gif:
        assert gif.size == (W * 3 + 48, H), gif.size
        qa['gifs']['all_three_native.gif'] = {'size': list(gif.size), 'frames': gif.n_frames}
    save_masks_and_boundaries(states)
    save_review(states)
    save_feature_reviews(states)
    save_blink_mask_reviews()
    save_shocked_blink_seam_mask_review(states)
    save_expression_mask_reviews()
    save_gif_detail_reviews()
    qa['source_donor_result_reviews'] = save_source_donor_result_reviews(states)
    qa['foreground_hair_review'] = save_foreground_hair_review()
    save_shocked_eye_animation_review()
    with Image.open(OUT / 'shocked_eyes_animation_20x.gif') as gif:
        qa['gifs']['shocked_eyes_animation_20x.gif'] = {
            'size': list(gif.size), 'frames': gif.n_frames,
            'source': 'decoded shocked/combined.gif',
        }
    (OUT / 'QA.json').write_text(json.dumps(qa, indent=2) + '\n', encoding='utf-8')
    shutil.copy2(OUT / 'preview_fullbody.jpg', PUBLISHED / 'preview.jpg')
    print(json.dumps(qa, indent=2))


if __name__ == '__main__':
    write_outputs(make_states())
