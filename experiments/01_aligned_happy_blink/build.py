#!/usr/bin/env python3
"""Experimental eye-only transplant: neutral eyes -> happy closed-eye donor.

NOT a finished blink asset. Assumes donor and target share pixel-perfect canvas,
which is true of the two expression sprites in the supplied expression ZIP.
No AI generation, affine resampling, mouth/brow edits, or transparency changes.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import json

BASE=Path(__file__).resolve().parent
SRC=BASE.parent.parent/'static'/'sprites'
OUT=BASE/'output'
OUT.mkdir(exist_ok=True)
neutral=np.asarray(Image.open(SRC/'01_neutral_worried.png').convert('RGBA')).copy()
happy=np.asarray(Image.open(SRC/'02_happy.png').convert('RGBA')).copy()
assert neutral.shape==happy.shape == (1448,1086,4)
H,W=neutral.shape[:2]

# Hard hand-calibrated face-specific polygons (image coordinates).
# Located around EYES ONLY, not eyebrow, mouth, ear or hair perimeter.
eyes={
 'image_left_eye': [(464,149),(468,142),(480,137),(491,135),(501,136),(510,140),(516,146),(517,152),(515,160),(508,164),(488,166),(476,164),(468,158)],
 'image_right_eye':[(535,139),(537,131),(547,126),(556,124),(574,124),(587,126),(595,133),(595,144),(588,152),(578,158),(549,157),(541,151)]
}
# Preserve foreground locks whenever the rough oval intersects them.
# Iterative manual masks: NOT meant to apply to a new character or pose.
protected={
 'right_side_lock':[(592,120),(601,122),(604,139),(600,157),(594,173),(586,174),(589,157),(592,144)]
}

def poly_mask(poly):
 a=np.zeros((H,W),dtype=np.uint8)
 cv2.fillPoly(a,[np.array(poly,np.int32)],255)
 return a

rough=np.zeros((H,W),np.uint8)
for poly in eyes.values(): cv2.fillPoly(rough,[np.array(poly,np.int32)],255)
protect=np.zeros((H,W),np.uint8)
for poly in protected.values():cv2.fillPoly(protect,[np.array(poly,np.int32)],255)
# Dilate protected by 1 pixel to retain a meaningful cushion.
protect=cv2.dilate(protect,np.ones((3,3),np.uint8))
# Smooth a small transition ONLY at the target eye edges.
# Separately zero out protected hair, so its pixels remain bit-identical.
raw=cv2.bitwise_and(rough,cv2.bitwise_not(protect))
distance=cv2.distanceTransform(raw, cv2.DIST_L2, 3)
# 0 at the hard polygon border; full coverage inside after ~4 pixels.
weight=np.clip((distance-1.0)/3.2, 0, 1)
weight[protect>0]=0
weight[rough==0]=0
# preserve alpha, and don't touch fully transparent pixels
weight[neutral[:,:,3]==0]=0

# Match color only with carefully chosen skin-only points just outside eyes.
# Values in the two source sprites are similar already; a per-eye correction
# makes the mild pink eye shading less obvious. Use conservative cap to avoid
# shifting the eyelash line hue.
patch=happy[:,:,:3].astype(np.float32).copy()
color_offsets={}
for key,skin_points in {
 'image_left_eye':[(470,136),(479,167),(495,171),(507,167),(479,132)],
 'image_right_eye':[(543,122),(550,164),(575,162),(581,122),(540,160)]
}.items():
 d=np.array([neutral[y,x,:3].astype(float)-happy[y,x,:3].astype(float) for x,y in skin_points])
 delta=np.clip(np.median(d,axis=0),-10,10)
 color_offsets[key]=list(np.round(delta,2))
 boxmask=poly_mask(eyes[key])>0
 patch[boxmask,:]=np.clip(patch[boxmask,:]+delta,0,255)

# Export a transparent overlay: React can layer it above the original sprite,
# and independently above/below a future mouth overlay, without 4-way sprites.
overlay=np.zeros_like(neutral)
overlay[:,:,:3]=np.clip(patch,0,255).astype(np.uint8)
overlay[:,:,3]=np.rint(weight*255).astype(np.uint8)
overlay[overlay[:,:,3]==0,:3]=0
Image.fromarray(overlay).save(OUT/'eyes_closed_overlay.png',optimize=True)
out=np.asarray(Image.alpha_composite(Image.fromarray(neutral),Image.fromarray(overlay))).copy()
# Base face is slightly translucent (alpha=253), not 255. Browser alpha
# compositing can shift it by at most 2/255 in the edited regions.
# The exported static closed sprite keeps the source alpha bit-identical.
out[:,:,3]=neutral[:,:,3]
assert np.array_equal(out[:,:,3],neutral[:,:,3])
changed=np.any(out[:,:,:3]!=neutral[:,:,:3],axis=2)
assert not np.any(changed & (rough==0))
assert not np.any(changed & (protect!=0))
assert not np.any(changed & (neutral[:,:,3]==0))
ys,xs=np.where(changed)
qa={'donor':'02_happy.png', 'target':'01_neutral_worried.png',
    'method':'per-eye 3.2px distance feather polygons + hair exclusion + median skin RGB correction',
    'modified_pixels':int(changed.sum()),
    'modified_bbox': [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
    'alpha_bit_identical': True,
    'runtime_overlay_alpha_note':'Source face alpha is ~253; compositing overlay alone slightly increases alpha (max 2/255) inside eye polygons',
    'modified_outside_eye_polygons':0, 'modified_protected_hair_pixels':0,
    'note':'Automated checks do not establish visual acceptability; eyelid style from smiling expression is a temporary stand-in',
    'skin_color_offset_by_eye':color_offsets}
Image.fromarray(out).save(OUT/'neutral_eyes_closed_experimental.png',optimize=True)
(OUT/'qa.json').write_text(json.dumps(qa,indent=2))
# produce annotated high-resolution comparison
bbox=(448,80,625,185)
scale=4
w=(bbox[2]-bbox[0])*scale;h=(bbox[3]-bbox[1])*scale
canvas=Image.new('RGB',(w*3,h+38),'#ffffff')
for idx,(label,arr) in enumerate([('Original neutral',neutral),('Experimental blink',out),('Happy donor',happy)]):
 pic=Image.fromarray(arr).crop(bbox).convert('RGB').resize((w,h),Image.Resampling.NEAREST)
 canvas.paste(pic,(idx*w,38))
 ImageDraw.Draw(canvas).text((idx*w+8,10),label,fill='black')
canvas.save(OUT/'three_way_eyes_4x.png')
# show actual mask and protect regions using color visualization
mask_preview=Image.fromarray(neutral).crop(bbox).convert('RGB')
rawmask=(weight[bbox[1]:bbox[3],bbox[0]:bbox[2]]>0).astype(np.uint8)
pro=protect[bbox[1]:bbox[3],bbox[0]:bbox[2]]>0
col=np.array(mask_preview).copy()
col[rawmask>0]=np.maximum(col[rawmask>0], [150,40,40]);col[pro]=np.maximum(col[pro],[0,140,255])
Image.fromarray(col).resize((w,h),Image.Resampling.NEAREST).save(OUT/'mask_and_protection.png')
print(json.dumps(qa,indent=2))
