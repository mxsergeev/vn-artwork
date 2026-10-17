#!/usr/bin/env python3
"""Happy blink+talk prototype from the original aligned sprites.

Run: python experiments/05_happy_animation/build.py
The AI-created open-eye image is archived separately as an UNTESTED candidate.
This tested version instead transplants eye pixels from an existing same-sheet sprite.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'output'
OUT.mkdir(exist_ok=True)
SRC = ROOT / 'static' / 'sprites'
BASE = np.array(Image.open(SRC / '02_happy.png').convert('RGBA'))
DONOR = np.array(Image.open(SRC / '01_neutral_worried.png').convert('RGBA'))
H, W = BASE.shape[:2]
assert BASE.shape == DONOR.shape == (1448, 1086, 4)


def shape(points):
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(points, dtype=np.int32)], 255)
    return mask


def feather(mask, pixels=2.3):
    return np.minimum(cv2.distanceTransform(mask, cv2.DIST_L2, 5) / pixels, 1).astype('float32')


def combine(bottom, top, blend):
    out = bottom.copy()
    out[:, :, :3] = np.uint8(np.clip(
        bottom[:, :, :3].astype('float32') * (1 - blend[:, :, None])
        + top[:, :, :3].astype('float32') * blend[:, :, None], 0, 255))
    return out

# Exact hand-tuned masks for this one aligned sprite; intentionally NOT generic.
left = shape([(461, 149), (463, 143), (470, 139), (480, 135),
              (491, 135), (502, 138), (512, 142), (517, 148),
              (517, 153), (514, 159), (504, 165), (493, 168),
              (483, 167), (474, 164), (466, 160), (462, 155)])
right = shape([(529, 136), (532, 131), (538, 127), (550, 124),
               (565, 123), (578, 125), (589, 127), (594, 133),
               (595, 141), (590, 148), (579, 155), (562, 159),
               (547, 159), (537, 155), (531, 148)])
right = cv2.bitwise_and(right, cv2.bitwise_not(shape([
    (590, 119), (603, 122), (605, 137), (600, 155),
    (593, 163), (590, 159), (593, 144), (590, 134)])))
left = cv2.bitwise_and(left, cv2.bitwise_not(shape([
    (451, 143), (463, 140), (469, 146), (466, 159), (461, 162), (452, 159)])))
eye_mask = cv2.bitwise_or(left, right)
eye_w = np.clip(feather(left) + feather(right), 0, 1)

# Local color correction: compare only similar SKIN pixels *outside* masks;
# smooth RGB offsets spatially to retain shading, protect iris/lash/hair by
# capping correction. This is not a proof that shades now match perfectly.
delta = BASE[:, :, :3].astype('float32') - DONOR[:, :, :3].astype('float32')
a = BASE[:, :, :3].astype('int16')
b = DONOR[:, :, :3].astype('int16')
valid = (np.min(a, axis=2) > 105) & (np.min(b, axis=2) > 105)
valid &= (a[:, :, 0] - a[:, :, 2] > 15) & (b[:, :, 0] - b[:, :, 2] > 15)
valid &= (a[:, :, 0] > a[:, :, 1]) & (b[:, :, 0] > b[:, :, 1])
valid &= cv2.dilate(eye_mask, np.ones((9, 9), np.uint8)) == 0
region = np.zeros((H, W), dtype=bool)
region[106:181, 448:608] = True
valid &= region
v = valid.astype('float32')
norm = np.maximum(cv2.GaussianBlur(v, (0, 0), 10), 0.02)
offset = np.zeros((H, W, 3), dtype='float32')
for c in range(3):
    offset[:, :, c] = cv2.GaussianBlur(delta[:, :, c] * v, (0, 0), 10) / norm
corrected = DONOR.copy()
corrected[:, :, :3] = np.uint8(np.clip(
    DONOR[:, :, :3].astype('float32') + np.clip(offset, -25, 25), 0, 255))
opened = combine(BASE, corrected, eye_w)

# Mouth variation = Happy's OWN smile squashed vertically to 60%.
# Repaint original mouth to local surrounding skin only inside the mouth mask,
# then blend the scaled original mouth into the same exact x/y location.
mouth = shape([(520, 190), (523, 186), (531, 183), (542, 181),
               (553, 181), (561, 182), (563, 186), (560, 193),
               (552, 199), (543, 204), (534, 205), (525, 199), (521, 195)])
mbox = (515, 175, 569, 210)
x0, y0, x1, y1 = mbox
mask_crop = cv2.dilate(mouth[y0:y1, x0:x1], np.ones((3, 3), np.uint8))
clean = BASE[:, :, :3].copy()
clean[y0:y1, x0:x1] = cv2.inpaint(BASE[y0:y1, x0:x1, :3], mask_crop, 8, cv2.INPAINT_TELEA)
center_y, scale = 191., .60
ylo, yhi, xx0, xx1 = 182, 204, 516, 566
new_lo = int(np.floor(center_y + (ylo - center_y) * scale))
new_hi = int(np.ceil(center_y + (yhi - center_y) * scale))
gy, gx = np.mgrid[new_lo-2:new_hi+3, xx0:xx1]
mapx = gx.astype('float32')
mapy = center_y + (gy.astype('float32') - center_y) / scale
scaled = cv2.remap(BASE[:, :, :3], mapx, mapy, cv2.INTER_CUBIC,
                   borderMode=cv2.BORDER_REPLICATE)
feature = shape([(522, 190), (525, 187), (532, 185), (542, 183),
                 (552, 182), (560, 183), (558, 190), (552, 197),
                 (542, 202), (532, 198), (525, 195)])
local_w = cv2.remap(feather(feature, 1.5), mapx, mapy, cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT)
local_w = np.clip(local_w, 0, 1)
repaint = clean.astype('float32')
roi = repaint[new_lo-2:new_hi+3, xx0:xx1]
repaint[new_lo-2:new_hi+3, xx0:xx1] = roi * (1-local_w[:, :, None]) + scaled * local_w[:, :, None]
small = BASE.copy()
small[:, :, :3] = np.uint8(np.clip(
    BASE[:, :, :3].astype('float32') * (1-feather(mouth, 2.2)[:, :, None])
    + repaint * feather(mouth, 2.2)[:, :, None], 0, 255))

both = opened.copy()
changed_mouth = feather(mouth, 2.2) > 0
both[changed_mouth, :3] = small[changed_mouth, :3]
frames = {
    '00_original_happy': BASE,
    '01_happy_normal': opened,
    '02_happy_blink': BASE,
    '03_happy_talking': both,
    '04_happy_blink_talking': small,
}
qa = {}
for name, img in frames.items():
    changed = np.any(img[:, :, :3] != BASE[:, :, :3], axis=2)
    allowed = (eye_mask > 0) | (mouth > 0)
    qa[name] = {
        'changed_pixels': int(changed.sum()),
        'changed_outside_masks': int((changed & ~allowed).sum()),
        'alpha_identical': bool(np.array_equal(img[:, :, 3], BASE[:, :, 3]))
    }
    assert qa[name]['changed_outside_masks'] == 0
    assert qa[name]['alpha_identical']
    # Original Happy itself is the closed-eye frame; never duplicate source files.
    if name not in ('00_original_happy', '02_happy_blink'):
        Image.fromarray(img, 'RGBA').save(OUT / (name + '.png'), optimize=True)


def face(img, zoom=4, bbox=(451, 105, 610, 217)):
    cut = Image.fromarray(img, 'RGBA').crop(bbox)
    bg = Image.new('RGBA', cut.size, '#ebebeb')
    bg.alpha_composite(cut)
    return bg.convert('RGB').resize((cut.width * zoom, cut.height * zoom), Image.Resampling.NEAREST)


def animate(name, labels, durations):
    ims = [face(frames[key], 3) for key in labels]
    canvas = Image.new('RGB', (ims[0].width, len(ims)*ims[0].height))
    for i, img in enumerate(ims):
        canvas.paste(img, (0, i*img.height))
    pal = canvas.quantize(colors=255)
    imgs = [img.quantize(palette=pal, dither=Image.Dither.NONE) for img in ims]
    imgs[0].save(OUT / name, save_all=True, append_images=imgs[1:],
                 duration=durations, loop=0, disposal=2, optimize=False)


animate('blink_preview.gif',
        ['01_happy_normal', '02_happy_blink', '01_happy_normal',
         '02_happy_blink', '01_happy_normal'], [1250, 125, 1800, 120, 1600])
animate('talk_preview.gif',
        ['01_happy_normal', '03_happy_talking', '01_happy_normal',
         '03_happy_talking', '01_happy_normal'], [200, 220, 260, 210, 800])
animate('combined_preview.gif',
        ['01_happy_normal', '03_happy_talking', '01_happy_normal',
         '02_happy_blink', '01_happy_normal', '03_happy_talking',
         '04_happy_blink_talking', '03_happy_talking', '01_happy_normal'],
        [450, 210, 240, 130, 350, 270, 130, 260, 1250])

comparison = Image.new('RGB', (2544, 490), '#f7f7f7')
draw = ImageDraw.Draw(comparison)
for i, key in enumerate(['00_original_happy', '01_happy_normal',
                          '03_happy_talking', '04_happy_blink_talking']):
    comparison.paste(face(frames[key]), (i*636, 40))
    draw.text((i*636+10, 10), key, fill='#111111')
comparison.save(OUT / 'four_states_face_comparison.png', optimize=True)
for key, name, bb in [
    ('eyes', 'eyes_8x_inspection.png', (451, 115, 608, 173)),
    ('mouth', 'mouth_8x_inspection.png', (513, 172, 574, 212)),
]:
    a, b = (BASE, opened) if key == 'eyes' else (opened, both)
    ca, cb = face(a, 8, bb), face(b, 8, bb)
    image = Image.new('RGB', (ca.width*2, ca.height+30), '#f7f7f7')
    image.paste(ca, (0, 30)); image.paste(cb, (ca.width, 30))
    dr = ImageDraw.Draw(image)
    dr.text((6, 8), 'Before', fill='#111'); dr.text((ca.width+6, 8), 'After', fill='#111')
    image.save(OUT / name, optimize=True)
ov = BASE.copy()
for col, mask in [((45,230,65), eye_mask > 0), ((50,115,235), mouth > 0)]:
    for c, value in enumerate(col):
        ov[:, :, c][mask] = np.uint8(BASE[:, :, c][mask]*.55+value*.45)
Image.fromarray(ov, 'RGBA').crop((450, 115, 607, 216)).resize(
    (942, 606), Image.Resampling.NEAREST).save(OUT / 'feature_masks.png')
(OUT / 'QA.json').write_text(json.dumps(qa, indent=2)+'\n')
print(json.dumps(qa, indent=2))
