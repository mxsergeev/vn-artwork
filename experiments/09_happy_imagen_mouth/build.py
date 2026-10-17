#!/usr/bin/env python3
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'output'
OUT.mkdir(exist_ok=True)
BASE = np.array(Image.open(ROOT / 'static/sprites/02_happy.png').convert('RGBA'))
EYE_DONOR = np.array(Image.open(ROOT / 'experiments/05_happy_animation/assets/ai_open_eyes_candidate.png').convert('RGBA'))
# The original AI mouth donor changed other parts of the sprite. Only a 67x55
# lip/skin patch is needed; place it at its source coordinates.
_mouth_patch = np.array(Image.open(ROOT / 'experiments/09_happy_imagen_mouth/assets/closed_smile_patch.png').convert('RGB'))
MOUTH_DONOR = BASE.copy()
MOUTH_DONOR[165:220,510:577,:3] = _mouth_patch
assert BASE.shape == EYE_DONOR.shape == MOUTH_DONOR.shape == (1448,1086,4)
H,W = BASE.shape[:2]

def polygon(points):
    m=np.zeros((H,W),dtype='uint8')
    cv2.fillPoly(m,[np.array(points,dtype='int32')],255)
    return m

def feather(m,width=1.4):
    return np.clip(cv2.distanceTransform(m,cv2.DIST_L2,5)/width,0,1).astype('float32')

def composite(bottom, top_rgb, weight):
    out=bottom.copy()
    out[:,:,:3]=np.clip(bottom[:,:,:3].astype('float32')*(1-weight[:,:,None])+top_rgb.astype('float32')*weight[:,:,None],0,255).astype('uint8')
    return out

# image-specific eye masks based on experiment 08, with extra protection on right outer boundary.
left = polygon([
    (477,153),(479,146),(486,141),(492,137),(501,135),
    (509,138),(515,141),(519,145),(520,151),(518,156),
    (513,161),(505,163),(494,163),(485,161),(480,158)
])
right = polygon([
    (546,143),(547,136),(551,130),(557,125),(564,122),
    (574,121),(582,123),(587,127),(589,133),(588,140),
    (585,145),(577,148),(565,149),(554,149),(548,148)
])
eye_mask = cv2.bitwise_or(left,right)
eye_weight = np.maximum(feather(left,1.25), feather(right,1.25))

base_rgb = BASE[:,:,:3].astype('float32')
donor_rgb = EYE_DONOR[:,:,:3].astype('float32')
a = BASE[:,:,:3].astype('int16')
b = EYE_DONOR[:,:,:3].astype('int16')
valid = (np.min(a,axis=2)>105) & (np.min(b,axis=2)>105)
valid &= (a[:,:,0]-a[:,:,2]>15) & (b[:,:,0]-b[:,:,2]>15)
valid &= (a[:,:,0]>a[:,:,1]) & (b[:,:,0]>b[:,:,1])
valid &= (cv2.dilate(eye_mask,np.ones((9,9),np.uint8))==0)
region=np.zeros((H,W),dtype=bool)
region[110:175,451:604]=True
v=(valid & region).astype('float32')
norm=np.maximum(cv2.GaussianBlur(v,(0,0),8),0.02)
offset=np.zeros((H,W,3),dtype='float32')
for c in range(3):
    offset[:,:,c]=cv2.GaussianBlur((base_rgb[:,:,c]-donor_rgb[:,:,c])*v,(0,0),8)/norm
corrected_eye = np.clip(donor_rgb + np.clip(offset,-22,22),0,255)
open_eyes = composite(BASE, corrected_eye, eye_weight)

# preserve source outer-right boundary where donor only causes tiny changes
outer_preserve = polygon([
    (578,122),(592,125),(600,133),(601,145),(598,155),(591,160),(582,159),(578,152),(581,142),(580,132)
])
delta = np.abs(corrected_eye.astype('int16') - base_rgb.astype('int16')).sum(axis=2)
preserve_mask = (outer_preserve>0) & (delta <= 72)  # ~24 avg/channel
open_eyes[preserve_mask,:3] = BASE[preserve_mask,:3]

# tight mouth mask based on actual smile line/inner lip area.
mouth_mask = polygon([
    (521,191),(524,187),(531,184),(541,182),(551,182),
    (559,183),(564,186),(565,191),(562,196),(556,200),
    (548,202),(539,203),(530,201),(524,197),(521,194)
])
# local color correction using nearby skin, excluding mouth area.
mbase = BASE[:,:,:3].astype('float32')
mdonor = MOUTH_DONOR[:,:,:3].astype('float32')
a2 = BASE[:,:,:3].astype('int16')
b2 = MOUTH_DONOR[:,:,:3].astype('int16')
valid2 = (np.min(a2,axis=2)>105) & (np.min(b2,axis=2)>105)
valid2 &= (a2[:,:,0]-a2[:,:,2]>15) & (b2[:,:,0]-b2[:,:,2]>15)
valid2 &= (a2[:,:,0]>a2[:,:,1]) & (b2[:,:,0]>b2[:,:,1])
valid2 &= (cv2.dilate(mouth_mask,np.ones((9,9),np.uint8))==0)
region2=np.zeros((H,W),dtype=bool)
region2[165:220,510:577]=True
v2=(valid2 & region2).astype('float32')
norm2=np.maximum(cv2.GaussianBlur(v2,(0,0),8),0.02)
offset2=np.zeros((H,W,3),dtype='float32')
for c in range(3):
    offset2[:,:,c]=cv2.GaussianBlur((mbase[:,:,c]-mdonor[:,:,c])*v2,(0,0),8)/norm2
corrected_mouth = np.clip(mdonor + np.clip(offset2,-18,18),0,255)
closed_mouth = composite(BASE, corrected_mouth, feather(mouth_mask,1.8))

# combine toggles
idle = closed_mouth.copy()
idle[eye_mask>0,:3] = open_eyes[eye_mask>0,:3]
blink_idle = closed_mouth
speaking = open_eyes
blink_speaking = BASE

frames = {
    '01_happy_idle': idle,
    '02_happy_blink_idle': blink_idle,
    '03_happy_speaking': speaking,
    '04_happy_blink_speaking': blink_speaking,
}
allowed = (eye_mask>0) | (mouth_mask>0) | preserve_mask
qa={}
for key,frame in frames.items():
    diff = np.any(frame[:,:,:3] != BASE[:,:,:3], axis=2)
    qa[key] = {
        'changed_pixels': int(diff.sum()),
        'outside_feature_masks': int(np.count_nonzero(diff & ~allowed)),
        'alpha_identical': bool(np.array_equal(frame[:,:,3], BASE[:,:,3]))
    }
    assert qa[key]['outside_feature_masks']==0
    assert qa[key]['alpha_identical']
    if key != '04_happy_blink_speaking':
        Image.fromarray(frame,'RGBA').save(OUT/(key+'.png'), optimize=True)

# inspections

def face(arr, scale=4, bbox=(451,105,610,217)):
    cut = Image.fromarray(arr,'RGBA').crop(bbox)
    bg=Image.new('RGBA',cut.size,'#efefef')
    bg.alpha_composite(cut)
    return bg.convert('RGB').resize((cut.width*scale, cut.height*scale), Image.Resampling.NEAREST)

def animation(name, ids, durations):
    rendered=[face(frames[k],3) for k in ids]
    palette=Image.new('RGB',(1,1))
    montage=Image.new('RGB',(rendered[0].width, rendered[0].height*len(rendered)))
    for i,im in enumerate(rendered): montage.paste(im,(0,i*im.height))
    palette=montage.quantize(colors=256)
    ims=[im.quantize(palette=palette, dither=Image.Dither.NONE) for im in rendered]
    ims[0].save(OUT/name,save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2,optimize=False)

animation('blink_preview.gif', ['01_happy_idle','02_happy_blink_idle','01_happy_idle','02_happy_blink_idle','01_happy_idle'], [1300,130,1900,130,1400])
animation('talk_preview.gif', ['01_happy_idle','03_happy_speaking','01_happy_idle','03_happy_speaking','01_happy_idle','03_happy_speaking','01_happy_idle'], [220,230,180,250,220,200,1000])
animation('combined_preview.gif', ['01_happy_idle','03_happy_speaking','01_happy_idle','02_happy_blink_idle','01_happy_idle','03_happy_speaking','04_happy_blink_speaking','03_happy_speaking','01_happy_idle'], [450,250,300,130,440,220,130,250,1300])

comparison = Image.new('RGB',(636*4,490),'#f7f7f7')
draw = ImageDraw.Draw(comparison)
for i,key in enumerate(frames):
    comparison.paste(face(frames[key]), (636*i,40))
    draw.text((636*i+10,10), key, fill='#111')
comparison.save(OUT/'four_states_face_comparison.png', optimize=True)

for name,before,after,bb in [
    ('eyes_8x_inspection.png', BASE, open_eyes, (452,115,607,174)),
    ('mouth_8x_inspection.png', BASE, closed_mouth, (514,174,572,215)),
    ('idle_8x_fullface.png', BASE, idle, (451,105,610,217)),
]:
    aimg,bimg = face(before,8,bb), face(after,8,bb)
    c=Image.new('RGB',(aimg.width+bimg.width,aimg.height+30),'#f7f7f7')
    c.paste(aimg,(0,30)); c.paste(bimg,(aimg.width,30))
    d=ImageDraw.Draw(c); d.text((6,7),'Before',fill='#111'); d.text((aimg.width+6,7),'After',fill='#111')
    c.save(OUT/name,optimize=True)

# difference overlay
ov = BASE.copy()
for col,m in [((45,230,65),eye_mask>0),((50,115,235),mouth_mask>0),((240,170,20), preserve_mask)]:
    for c,val in enumerate(col):
        ov[:,:,c][m] = np.uint8(BASE[:,:,c][m]*0.55 + val*0.45)
Image.fromarray(ov,'RGBA').crop((450,115,607,216)).resize((942,606), Image.Resampling.NEAREST).save(OUT/'feature_masks.png', optimize=True)
(OUT/'QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa, indent=2))
