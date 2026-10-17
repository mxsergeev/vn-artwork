#!/usr/bin/env python3
"""Neutral clerk 2-frame blink and talking-mouth pilot.

Phase 1: Reuse the successful aligned happy donor for closed eyes, with
         restricted eye masks and conservative neutral skin correction.
Phase 2: Align the newer speaking-mouth donor around the ORIGINAL mouth center.
Phase 3: QA independently, export full frames + independent overlays.

Deps: Pillow, numpy, opencv-python. Run: python build.py
Coordinates are specific to the provided 1086x1448 clerk and head pose.
"""
from pathlib import Path
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'assets'
OUT = HERE / 'output'
OUT.mkdir(exist_ok=True)
base = np.asarray(Image.open(HERE.parent.parent/'static'/'sprites'/'01_neutral_worried.png').convert('RGBA')).copy()
happy = np.asarray(Image.open(HERE.parent.parent/'static'/'sprites'/'02_happy.png').convert('RGBA')).copy()
donor = np.asarray(Image.open(ASSETS/'talk_donor.png').convert('RGB')).copy()
assert base.shape == happy.shape == (1448,1086,4)
H,W = base.shape[:2]

# Pixel-precise polygons from run_closed_eye_test.py, the previously successful pipeline.
eye_regions = {
    'left':[(464,149),(468,142),(480,137),(491,135),(501,136),(510,140),(516,146),(517,152),(515,160),(508,164),(488,166),(476,164),(468,158)],
    'right':[(535,139),(537,131),(547,126),(556,124),(574,124),(587,126),(595,133),(595,144),(588,152),(578,158),(549,157),(541,151)],
}
right_hair = [(592,120),(601,122),(604,139),(600,157),(594,173),(586,174),(589,157),(592,144)]

def pmask(points):
    arr = np.zeros((H,W),np.uint8)
    cv2.fillPoly(arr,[np.array(points,np.int32)],255)
    return arr

# Phase 1: same geometry and local skin sample correction as proven blink pilot.
rough = np.zeros((H,W),np.uint8)
for poly in eye_regions.values():rough |= pmask(poly)
protect=cv2.dilate(pmask(right_hair),np.ones((3,3),np.uint8))
mask = cv2.bitwise_and(rough,cv2.bitwise_not(protect))
dist = cv2.distanceTransform(mask,cv2.DIST_L2,3)
w_eye = np.clip((dist-1)/3.2,0,1).astype(np.float32)
w_eye[protect>0]=0
w_eye[base[:,:,3]==0]=0

patch = happy[:,:,:3].astype(np.float32).copy()
color_offsets={}
for key,skin_points in {
 'left':[(470,136),(479,167),(495,171),(507,167),(479,132)],
 'right':[(543,122),(550,164),(575,162),(581,122),(540,160)]
}.items():
    delta=np.median(np.array([base[y,x,:3].astype(float)-happy[y,x,:3].astype(float) for x,y in skin_points]),axis=0)
    delta=np.clip(delta,-10,10)
    color_offsets[key]=delta.tolist()
    inside=pmask(eye_regions[key])>0
    patch[inside]=np.clip(patch[inside]+delta,0,255)

# Compose using same alpha operation as first successful script.
eye_layer=np.zeros_like(base)
eye_layer[:,:,:3]=np.clip(patch,0,255).astype(np.uint8)
eye_layer[:,:,3]=np.rint(w_eye*255).astype(np.uint8)
eye_layer[eye_layer[:,:,3]==0,:3]=0
blink=np.asarray(Image.alpha_composite(Image.fromarray(base),Image.fromarray(eye_layer))).copy()
blink[:,:,3]=base[:,:,3]
# Subtle extra green/blue on warm skin only, WITHOUT affecting eyelash ink.
values=blink[:,:,:3].astype(np.float32)
brightness=values.mean(axis=2)
skin=(values[:,:,0]>135)&(values[:,:,1]>100)&(values[:,:,2]>80)&(values[:,:,0]>values[:,:,1])
corrected=np.any(blink[:,:,:3]!=base[:,:,:3],axis=2)
skin_w = np.clip((brightness-130)/60,0,1)*skin*corrected
blink[:,:,:3]=np.clip(values+skin_w[:,:,None]*np.array([-2,10,10],np.float32),0,255).astype(np.uint8)

# Phase 2: speaking-mouth donor is geometrically different; align ONLY local mouth.
source_mouth_center=(278,445)
target_mouth_center=(533,190)  # Re-anchored rightward to fully cover original lip.
scale_x,scale_y=.66,.63
sx,sy=source_mouth_center;tx,ty=target_mouth_center
mat=np.array([[scale_x,0,tx-sx*scale_x],[0,scale_y,ty-sy*scale_y]],np.float32)
warped=cv2.warpAffine(donor,mat,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
mouth_poly=[(500,188),(504,181),(515,176),(527,175),(541,176),(552,180),(559,187),(560,195),(553,202),(540,205),(520,205),(508,201),(502,196)]
mouth_mask=pmask(mouth_poly)
md=cv2.distanceTransform(mouth_mask,cv2.DIST_L2,3)
w_mouth=np.clip((md-1)/3,0,1).astype(np.float32)
# Sample near edge, excluding original dark lip line and generated lip ink.
ring=(md>1)&(md<4.5)&(base[:,:,0]>175)&(base[:,:,1]>110)&(warped[:,:,0]>175)&(warped[:,:,1]>110)
diffs=base[:,:,:3][ring].astype(np.float32)-warped[ring].astype(np.float32)
assert len(diffs)>=20, f'Mouth color samples unexpectedly low: {len(diffs)}'
mouth_offset=np.clip(np.median(diffs,axis=0),-45,45)
talk_patch=np.clip(warped.astype(np.float32)+mouth_offset,0,255)

def add_mouth(on):
    res=on.copy()
    rgb=np.clip(on[:,:,:3].astype(np.float32)*(1-w_mouth[:,:,None])+talk_patch*w_mouth[:,:,None],0,255)
    res[:,:,:3]=rgb.astype(np.uint8)
    return res

talk=add_mouth(base)
both=add_mouth(blink)
frames={'neutral.png':base,'blink.png':blink,'talk.png':talk,'blink_talk.png':both}
for name,frame in frames.items():
    assert np.array_equal(frame[:,:,3],base[:,:,3])
    Image.fromarray(frame).save(OUT/name,optimize=True)

# Overlay is the exact RGB result of a local patch, opaque where changed.
# For a source with alpha 253, browser compositing can increase alpha <=2/255.
def overlay_for(frame):
    res=np.zeros_like(frame)
    diff=np.any(frame[:,:,:3]!=base[:,:,:3],axis=2)&(base[:,:,3]>0)
    res[diff,:3]=frame[diff,:3]
    res[diff,3]=255
    return res
Image.fromarray(overlay_for(blink)).save(OUT/'blink_overlay.png',optimize=True)
Image.fromarray(overlay_for(talk)).save(OUT/'mouth_overlay.png',optimize=True)
# Their alpha masks are non-overlapping: compositing them creates same colors as both.
for name,frame,allowed in [('blink',blink,rough>0),('talk',talk,mouth_mask>0)]:
    changed=np.any(frame[:,:,:3]!=base[:,:,:3],axis=2)
    assert np.count_nonzero(changed&~allowed)==0, f'{name}: changed pixels outside allowed region'
assert np.count_nonzero((rough>0)&(mouth_mask>0))==0
changed_eyes=np.any(blink[:,:,:3]!=base[:,:,:3],axis=2)
changed_mouth=np.any(talk[:,:,:3]!=base[:,:,:3],axis=2)
assert not np.any(changed_eyes&(protect>0))
assert np.array_equal(both[:,:,:3][changed_eyes],blink[:,:,:3][changed_eyes])
assert np.array_equal(both[:,:,:3][changed_mouth],talk[:,:,:3][changed_mouth])
qa={
 'alpha_unchanged_for_all_frames':True,
 'eye_changed_pixels':int(changed_eyes.sum()),
 'mouth_changed_pixels':int(changed_mouth.sum()),
 'eye_changes_outside_original_eye_polygons':int(np.count_nonzero(changed_eyes&(rough==0))),
 'mouth_changes_outside_local_mouth_polygon':int(np.count_nonzero(changed_mouth&(mouth_mask==0))),
 'eye_changes_in_protected_hair':0,
 'eye_and_mouth_regions_disjoint':True,
 'independent_combination_pixel_test':True,
 'eye_donor':'Original pixel-aligned happy donor (new AI closed-eye donor rejected after visual QA)',
 'eye_color_offsets':color_offsets,
 'mouth_donor':'New four-state generated expression palette, third panel',
 'mouth_source_anchor':source_mouth_center,
 'mouth_target_anchor':target_mouth_center,
 'mouth_color_offset':mouth_offset.tolist(),
 'visual_limitation':'Blink retains a slight smiling-squint shape; blush reduction is approximate, not a perfect neutral redraw.'
}
(OUT/'qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
# Face preview -- 4x nearest-neighbor to show actual edges/artifacts, not blur them.
box=(440,89,620,228); z=4
comparison=Image.new('RGB',((box[2]-box[0])*z*4,(box[3]-box[1])*z+35),'white')
for j,(label,arr) in enumerate([('Original',base),('Blink',blink),('Talk',talk),('Both',both)]):
    part=Image.fromarray(arr).crop(box)
    bg=Image.new('RGBA',part.size,(255,255,255,255));bg.alpha_composite(part)
    comparison.paste(bg.convert('RGB').resize((part.width*z,part.height*z),Image.Resampling.NEAREST),(j*part.width*z,35))
    ImageDraw.Draw(comparison).text((j*part.width*z+8,10),label,fill='black')
comparison.save(OUT/'four_states_4x.png',optimize=True)
# Real-size crop previews too.
real=Image.new('RGB',((box[2]-box[0])*4,(box[3]-box[1])+26),'white')
for j,(label,arr) in enumerate([('Original',base),('Blink',blink),('Talk',talk),('Both',both)]):
    part=Image.fromarray(arr).crop(box)
    bg=Image.new('RGBA',part.size,(255,255,255,255));bg.alpha_composite(part)
    real.paste(bg.convert('RGB'),(j*part.width,26))
    ImageDraw.Draw(real).text((j*part.width+2,8),label,fill='black')
real.save(OUT/'four_states_1x.png')
# A small repeating animation with speaking and blinking, for rough transition QA.
sequence=[('neutral.png',850),('talk.png',130),('neutral.png',120),('talk.png',120),('neutral.png',900),('blink.png',130),('neutral.png',800),('talk.png',120),('blink_talk.png',130),('talk.png',180),('neutral.png',1400)]
gifframes=[];dur=[]
for name,ms in sequence:
    part=Image.fromarray(frames[name]).crop(box)
    bg=Image.new('RGBA',part.size,(243,243,243,255));bg.alpha_composite(part)
    gifframes.append(bg.convert('RGB').resize((part.width*2,part.height*2),Image.Resampling.NEAREST));dur.append(ms)
gifframes[0].save(OUT/'preview.gif',save_all=True,append_images=gifframes[1:],duration=dur,loop=0,optimize=False)
print(json.dumps(qa,indent=2))
