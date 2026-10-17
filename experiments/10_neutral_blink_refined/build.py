#!/usr/bin/env python3
"""Refined neutral blink: thinner, image-specific eyelid masks.

Goals:
- restore the slightly cut-off left eyelash,
- stop replacing unnecessary under-eye skin that created pale bags/color patches,
- preserve the approved talking frame exactly.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE/'output'
OUT.mkdir(exist_ok=True)
BASE = np.array(Image.open(ROOT/'static/sprites/01_neutral_worried.png').convert('RGBA'))
EYES = np.array(Image.open(ROOT/'experiments/04_source_anchored_animation/assets/eyes_closed_donor.png').convert('RGBA'))
TALK = np.array(Image.open(ROOT/'experiments/04_source_anchored_animation/assets/approved_talking.png').convert('RGBA'))
assert BASE.shape == EYES.shape == TALK.shape == (1448,1086,4)
H, W = BASE.shape[:2]

def polygon(points, feather):
    raw = np.zeros((H, W), np.uint8)
    cv2.fillPoly(raw, [np.asarray(points, np.int32)], 255)
    return np.clip(cv2.distanceTransform(raw, cv2.DIST_L2, 5) / feather, 0, 1).astype('float32')

# Image-specific contours chosen after comparing source/donor/blink overlays.
# Left eye: include a tiny dedicated lash-tip polygon so the outer lower lash is not cut off.
LEFT_MAIN = [(482,139),(489,136),(498,136),(508,139),(512,144),
             (511,149),(505,153),(496,154),(488,154),(482,150)]
LEFT_LASH_TIP = [(479,148),(484,146),(487,148),(486,152),(480,153)]
# Right eye: thinner lower boundary to preserve original under-eye shading.
RIGHT_MAIN = [(534,133),(540,128),(551,126),(563,126),(575,127),
              (582,131),(583,137),(579,142),(568,145),(553,145),
              (542,142),(536,138)]
left = np.maximum(polygon(LEFT_MAIN,1.2), polygon(LEFT_LASH_TIP,0.7))
right = polygon(RIGHT_MAIN,1.3)
mask = np.maximum(left, right)

# Same local skin correction idea as experiment 04, but only the thin masks are composited.
corrected = EYES.copy()
for (x0,y0,x1,y1),(a,b,c,d) in [
    ((465,133,517,173),(450,115,520,171)),
    ((533,125,597,163),(524,113,595,164)),
]:
    x = BASE[y0:y1,x0:x1,:3].astype(float)
    y = EYES[y0:y1,x0:x1,:3].astype(float)
    ok = (x.mean(2)>165) & (y.mean(2)>165) & (x.std(2)<50) & (y.std(2)<50)
    assert np.any(ok), 'Cannot compute reliable skin correction'
    offset = np.median((y-x)[ok], axis=0)
    corrected[b:d,a:c,:3] = np.uint8(np.clip(EYES[b:d,a:c,:3].astype(float)-offset,0,255))

blink = BASE.copy()
blink[:,:,:3] = np.uint8(np.clip(
    BASE[:,:,:3].astype(float)*(1-mask[:,:,None]) + corrected[:,:,:3].astype(float)*mask[:,:,None],
    0,255))
combined = blink.copy()
mouth_changed = np.any(TALK[:,:,:3] != BASE[:,:,:3], axis=2)
combined[mouth_changed] = TALK[mouth_changed]
frames = {'neutral': BASE, 'blink_closed': blink, 'talking': TALK, 'blink_talking': combined}
for name, arr in frames.items():
    Image.fromarray(arr, 'RGBA').save(OUT/f'{name}.png', optimize=True)

changed = np.any(blink[:,:,:3] != BASE[:,:,:3], axis=2)
assert np.array_equal(blink[:,:,3], BASE[:,:,3])
assert not (changed & (mask==0)).any()
report = {
    'blink_changed_pixels': int(changed.sum()),
    'blink_outside_mask_pixels': int((changed & (mask==0)).sum()),
    'alpha_preserved': True,
    'approved_talking_exactly_preserved': True,
    'notes': 'Refined thinner eyelid masks to preserve left lash tip and more original under-eye shading.'
}
(OUT/'qa.json').write_text(json.dumps(report, indent=2)+'\n')

def render(arr, box=(430,104,625,234), scale=3):
    im = Image.fromarray(arr,'RGBA').crop(box)
    bg = Image.new('RGBA', im.size, '#eeeeee')
    bg.alpha_composite(im)
    return bg.convert('RGB').resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST)

def gif(name, names, durations):
    images = [render(frames[x]) for x in names]
    sheet = Image.new('RGB', (images[0].width, images[0].height*len(images)))
    for i,im in enumerate(images): sheet.paste(im, (0, i*im.height))
    palette = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    ims = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images]
    ims[0].save(OUT/name, save_all=True, append_images=ims[1:], duration=durations, loop=0, disposal=2, optimize=False)

gif('blink_preview.gif',['neutral','blink_closed','neutral','blink_closed','neutral'],[1200,130,1350,120,1200])
gif('talk_preview.gif',['neutral','talking','neutral','talking','neutral'],[200,190,220,250,600])

# Review images
box=(455,118,603,175)
for name, before, after in [('eyes_8x_inspection.png', BASE, blink)]:
    a = render(before, box, 8)
    b = render(after, box, 8)
    c = Image.new('RGB', (a.width+b.width, a.height+30), '#f7f7f7')
    c.paste(a,(0,30)); c.paste(b,(a.width,30))
    d = ImageDraw.Draw(c)
    d.text((6,7),'Before', fill='#111')
    d.text((a.width+6,7),'Blink', fill='#111')
    c.save(OUT/name, optimize=True)

# separate mask overlay and changed-pixel boundary review
base_bg = Image.new('RGBA', (W,H), '#efefef'); base_bg.alpha_composite(Image.fromarray(BASE,'RGBA'))
arr = np.array(base_bg)
for channel, val in enumerate((45,230,65)):
    arr[:,:,channel][mask>0] = np.uint8(arr[:,:,channel][mask>0]*.55 + val*.45)
Image.fromarray(arr,'RGBA').crop((450,120,605,173)).resize((930,318), Image.Resampling.NEAREST).save(OUT/'feature_masks.png', optimize=True)

m = changed.astype('uint8')*255
boundary = (m>0) & ~(cv2.erode(m, np.ones((3,3), np.uint8))>0)
arr2 = np.array(base_bg)
arr2[boundary] = [0,255,0,255]
Image.fromarray(arr2,'RGBA').crop((450,120,605,173)).resize((930,318), Image.Resampling.NEAREST).save(OUT/'changed_boundary.png', optimize=True)
print(json.dumps(report, indent=2))
