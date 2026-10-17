#!/usr/bin/env python3
"""Source-anchored eyes + mouth experiment for the provided neutral clerk.

Original: ../../static/sprites/01_neutral_worried.png
Donors: assets/eyes_closed_donor.png (AI image edit of original)
        assets/approved_talking.png (approved mouth-transplanted sprite)

Run from anywhere: python experiments/04_source_anchored_animation/build.py
Requires: numpy, Pillow, opencv-python (../../requirements.txt).
Coordinates and skin correction are specific to ONE 1086x1448 sprite.
The blink is a near-final pilot, NOT a manually finished asset.
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
EYES = np.array(Image.open(HERE/'assets/eyes_closed_donor.png').convert('RGBA'))
TALK = np.array(Image.open(HERE/'assets/approved_talking.png').convert('RGBA'))
assert BASE.shape == EYES.shape == TALK.shape == (1448, 1086, 4)
H, W = BASE.shape[:2]

# Final pilot contour: covers the left eye's upper lash and aperture; subtracts
# a small notch to preserve outer hair. Small iris/lash artifacts remain.
LEFT_MAIN = [(482,136),(488,133),(497,133),(507,136),(511,141),
             (512,147),(508,152),(501,155),(492,156),(486,154),
             (482,149),(481,145)]
LEFT_LASH_CORNER = [(480,148),(482,147),(483,149),(482,151),(480,151)]
LEFT_HAIR_NOTCH = [(474,140),(480,140),(480,156),(474,156)]
RIGHT = [(531,135),(534,128),(545,125),(559,126),(575,126),
         (583,128),(588,135),(588,143),(581,151),(570,157),
         (547,158),(536,151),(532,145)]

def polygon(points, feather):
    raw = np.zeros((H,W), np.uint8)
    cv2.fillPoly(raw, [np.asarray(points,np.int32)], 255)
    # Feather *inside* contours only: no expanding into surrounding hair/jaw.
    return np.clip(cv2.distanceTransform(raw,cv2.DIST_L2,5)/feather,0,1).astype('float32')

left = np.maximum(polygon(LEFT_MAIN,1.5), polygon(LEFT_LASH_CORNER,0.7))
notch = np.zeros((H,W),np.uint8)
cv2.fillPoly(notch, [np.asarray(LEFT_HAIR_NOTCH,np.int32)], 255)
left[notch>0] = 0
limit = np.zeros_like(left)
limit[130:161,474:513] = left[130:161,474:513]
left = limit
right = polygon(RIGHT,2.5)
mask = np.maximum(left,right)

# Match donor skin RGB using light, low-saturation pixels in two source patches.
# Do not overwrite the base outside the final eye mask.
corrected = EYES.copy()
for (x0,y0,x1,y1),(a,b,c,d) in [
    ((465,133,517,173),(450,115,520,171)),
    ((533,125,597,163),(524,113,595,164))]:
    x=BASE[y0:y1,x0:x1,:3].astype(float)
    y=EYES[y0:y1,x0:x1,:3].astype(float)
    ok=(x.mean(2)>165)&(y.mean(2)>165)&(x.std(2)<50)&(y.std(2)<50)
    assert np.any(ok), 'Cannot compute reliable skin correction'
    offset=np.median((y-x)[ok],axis=0)
    corrected[b:d,a:c,:3]=np.uint8(np.clip(EYES[b:d,a:c,:3].astype(float)-offset,0,255))

blink=BASE.copy()
blink[:,:,:3] = np.uint8(np.clip(
    BASE[:,:,:3].astype(float)*(1-mask[:,:,None]) +
    corrected[:,:,:3].astype(float)*mask[:,:,None],0,255))
# Preserve the approved talking frame exactly; compose disjoint feature edits.
combined=blink.copy()
mouth_changed=np.any(TALK[:,:,:3] != BASE[:,:,:3],axis=2)
combined[mouth_changed] = TALK[mouth_changed]
frames={'neutral':BASE,'blink_closed':blink,'talking':TALK,'blink_talking':combined}
for name,arr in frames.items():
    Image.fromarray(arr,'RGBA').save(OUT/f'{name}.png',optimize=True)

# QA checks test locality, not visual perfection; review at 1x and 8x in motion.
changed=np.any(blink[:,:,:3]!=BASE[:,:,:3],axis=2)
assert np.array_equal(blink[:,:,3],BASE[:,:,3])
assert not (changed & (mask==0)).any()
assert not changed[:,:480].any(), 'Unexpected change in outer-left hair'
assert not changed[162:,:530].any(), 'Unexpected change under left eye'
assert np.array_equal(TALK,np.array(Image.open(HERE/'assets/approved_talking.png').convert('RGBA')))
report={
    'blink_changed_pixels':int(changed.sum()),
    'blink_outside_mask_pixels':int((changed&(mask==0)).sum()),
    'alpha_preserved':True,
    'approved_talking_exactly_preserved':True,
    'notes':'Small remaining left lash/hair transition artifact; manual cleanup required.'
}
(OUT/'qa.json').write_text(json.dumps(report,indent=2)+'\n')

# Minimal review images. GIF uses a shared palette to avoid palette flashing.
box=(430,104,625,234)
def render(arr, box=box, scale=3):
    im=Image.fromarray(arr,'RGBA').crop(box)
    bg=Image.new('RGBA', im.size, '#eeeeee')
    bg.alpha_composite(im)
    return bg.convert('RGB').resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)

def gif(name,names,durations):
    images=[render(frames[x]) for x in names]
    sheet=Image.new('RGB',(images[0].width,images[0].height*len(images)))
    for i,im in enumerate(images):sheet.paste(im,(0,i*im.height))
    palette=sheet.quantize(colors=255,method=Image.Quantize.MEDIANCUT)
    ims=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
    ims[0].save(OUT/name,save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2,optimize=False)

gif('blink_preview.gif',['neutral','blink_closed','neutral','blink_closed','neutral'],[1200,130,1350,120,1200])
gif('talk_preview.gif',['neutral','talking','neutral','talking','neutral'],[200,190,220,250,600])

# Mask / original overlay for pixel-level inspection.
mask_overlay=BASE.copy(); on=left>0
for c,v in enumerate((245,45,55)):
    mask_overlay[:,:,c][on]=np.uint8(BASE[:,:,c][on]*.55+v*.45)
Image.fromarray(mask_overlay,'RGBA').crop((455,122,530,172)).resize((600,400),Image.Resampling.NEAREST).save(OUT/'left_mask_overlay.png')
print(json.dumps(report,indent=2))
