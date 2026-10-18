from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from artwork_tools import finish_animation
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'output'
OUT.mkdir(exist_ok=True)
BASE=np.array(Image.open(ROOT/'static/sprites/03_shocked.png').convert('RGBA'))
H,W=BASE.shape[:2]
assert BASE.shape==(1448,1086,4)
# Cropped, lossless image-edited donors reconstructed at their recorded source coordinates.
EYES_BOX=(472,117,589,166)
MOUTH_BOX=(522,176,566,212)
eye_patch=np.array(Image.open(HERE/'assets/eyes_closed_patch.png').convert('RGB'))
mouth_patch=np.array(Image.open(HERE/'assets/open_mouth_patch.png').convert('RGB'))
assert eye_patch.shape==(EYES_BOX[3]-EYES_BOX[1],EYES_BOX[2]-EYES_BOX[0],3)
assert mouth_patch.shape==(MOUTH_BOX[3]-MOUTH_BOX[1],MOUTH_BOX[2]-MOUTH_BOX[0],3)
DONOR=BASE.copy(); DONOR[EYES_BOX[1]:EYES_BOX[3],EYES_BOX[0]:EYES_BOX[2],:3]=eye_patch
MOUTH_DONOR=BASE.copy(); MOUTH_DONOR[MOUTH_BOX[1]:MOUTH_BOX[3],MOUTH_BOX[0]:MOUTH_BOX[2],:3]=mouth_patch

def polygon(points):
    m=Image.new('L',(W,H),0)
    ImageDraw.Draw(m).polygon(points,fill=255)
    return m

def feather(mask,width=1.0):
    # Blur an eroded interior and clamp to the hand-drawn contour so no outside pixels change.
    eroded=mask.filter(ImageFilter.MinFilter(3))
    blurred=eroded.filter(ImageFilter.GaussianBlur(width))
    return (np.minimum(np.asarray(blurred),np.asarray(mask)).astype(np.float32)/255)

def save_png(path,array):
    # Write complete PNG bytes before replacing the output, so QA never reads a partial frame.
    buffer=io.BytesIO()
    Image.fromarray(array,'RGBA').save(buffer,format='PNG',optimize=False)
    payload=buffer.getvalue()
    assert payload.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82')
    tmp=path.with_suffix('.png.tmp')
    tmp.write_bytes(payload)
    with Image.open(tmp) as check: check.verify()
    tmp.replace(path)

# Tight, independent contours around each shocked eye. Keep brows and crossing hair outside.
left_raw_img=polygon([
    (477,145),(478,139),(482,134),(489,131),(498,130),(506,132),
    (512,136),(516,141),(516,148),(513,153),(507,160),(502,163),
    (494,164),(487,162),(482,158),(478,152),(477,145)
])
right_raw_img=polygon([
    (536,137),(537,131),(541,126),(548,122),(558,120),(568,121),
    (577,124),(583,129),(585,135),(584,141),(579,146),(570,150),
    (560,151),(550,149),(543,146),(538,142)
])
left_raw=np.asarray(left_raw_img)
right_raw=np.asarray(right_raw_img)
left=feather(left_raw_img,1.0)
right=feather(right_raw_img,1.0)
mask=np.maximum(left,right)

# Use the edited eyelid pixels, but preserve the original sprite's RGBA alpha exactly.
# Donor-wide color differences are not allowed to affect untouched pixels.
out=BASE.copy()
out[:,:,:3]=np.rint(BASE[:,:,:3].astype(np.float32)*(1-mask[:,:,None])+DONOR[:,:,:3].astype(np.float32)*mask[:,:,None]).clip(0,255).astype(np.uint8)
out[:,:,3]=BASE[:,:,3]
changed=np.any(out[:,:,:3]!=BASE[:,:,:3],axis=2)
assert np.array_equal(out[:,:,3],BASE[:,:,3])
assert not np.any(changed & (mask==0))
save_png(OUT/'03_shocked_blink_closed.png',out)

# Tight mouth-only transplant; preserve nearby skin, chin, and the original source alpha.
mouth_raw=polygon([
    (526,187),(529,182),(537,180),(547,179),(556,181),(561,185),
    (563,191),(562,198),(558,204),(552,207),(544,209),(536,207),
    (530,203),(526,198),(525,191)
])
mouth_weight=feather(mouth_raw,1.0)
base_rgb=BASE[:,:,:3].astype(np.float32)
mouth_rgb=MOUTH_DONOR[:,:,:3].astype(np.float32)
# Estimate the donor's local skin shift from nearby skin-only pixels, outside the edit mask.
region=np.zeros((H,W),bool); region[175:213,518:572]=True
mask_dilated=np.asarray(mouth_raw.filter(ImageFilter.MaxFilter(13)))>0
skin=(BASE[:,:,0]>145)&(BASE[:,:,1]>95)&(BASE[:,:,2]>65)
skin&=(BASE[:,:,0].astype(int)-BASE[:,:,1].astype(int)>12)
skin&=(BASE[:,:,1].astype(int)-BASE[:,:,2].astype(int)>5)
donor_skin=(MOUTH_DONOR[:,:,0]>145)&(MOUTH_DONOR[:,:,1]>95)&(MOUTH_DONOR[:,:,2]>65)
donor_skin&=(MOUTH_DONOR[:,:,0].astype(int)-MOUTH_DONOR[:,:,1].astype(int)>12)
donor_skin&=(MOUTH_DONOR[:,:,1].astype(int)-MOUTH_DONOR[:,:,2].astype(int)>5)
sample=region&~mask_dilated&skin&donor_skin
assert sample.sum()>10, 'Insufficient nearby skin pixels for local color check'
skin_offset=np.median(mouth_rgb[sample]-base_rgb[sample],axis=0)
mouth_rgb=np.clip(mouth_rgb-skin_offset,0,255)
talk=BASE.copy()
talk[:,:,:3]=np.rint(BASE[:,:,:3].astype(np.float32)*(1-mouth_weight[:,:,None])+mouth_rgb*mouth_weight[:,:,None]).clip(0,255).astype(np.uint8)
talk[:,:,3]=BASE[:,:,3]
both=out.copy()
both[:,:,:3]=np.rint(out[:,:,:3].astype(np.float32)*(1-mouth_weight[:,:,None])+mouth_rgb*mouth_weight[:,:,None]).clip(0,255).astype(np.uint8)
both[:,:,3]=BASE[:,:,3]
save_png(OUT/'03_shocked_talking.png',talk)
save_png(OUT/'03_shocked_blink_talking.png',both)
talk_changed=np.any(talk[:,:,:3]!=BASE[:,:,:3],axis=2)
both_changed=np.any(both[:,:,:3]!=BASE[:,:,:3],axis=2)
assert not np.any(talk_changed & (mouth_weight==0)), 'Mouth edit escaped its mask'
assert not np.any(both_changed & ~((mask>0)|(mouth_weight>0))), 'Combined edit escaped feature masks'
assert np.array_equal(talk[:,:,3],BASE[:,:,3]) and np.array_equal(both[:,:,3],BASE[:,:,3])

# Mouth-specific QA overlays, following the eye inspection outputs above.
mouth_base_bg=Image.new('RGBA',(W,H),'#eee'); mouth_base_bg.alpha_composite(Image.fromarray(BASE,'RGBA'))
mouth_overlay=np.array(mouth_base_bg)
for c,val in enumerate((45,130,240)):
    mouth_overlay[:,:,c][mouth_weight>0]=np.uint8(mouth_overlay[:,:,c][mouth_weight>0]*.55+val*.45)
mouth_box=(518,174,572,214)
Image.fromarray(mouth_overlay,'RGBA').crop(mouth_box).resize(((mouth_box[2]-mouth_box[0])*8,(mouth_box[3]-mouth_box[1])*8),Image.Resampling.NEAREST).save(OUT/'mouth_feature_mask.png')
talk_boundary_img=Image.fromarray(talk_changed.astype('uint8')*255)
mouth_boundary=talk_changed & (np.asarray(talk_boundary_img.filter(ImageFilter.MinFilter(3)))==0)
mouth_boundary_view=np.array(mouth_base_bg); mouth_boundary_view[mouth_boundary]=[0,255,0,255]
Image.fromarray(mouth_boundary_view,'RGBA').crop(mouth_box).resize(((mouth_box[2]-mouth_box[0])*8,(mouth_box[3]-mouth_box[1])*8),Image.Resampling.NEAREST).save(OUT/'mouth_changed_boundary.png')

def save_gif(filename, frames, durations):
    # Like experiments 10 and 11, flatten onto one matte before palette conversion.
    # GIF transparency is binary and cannot preserve the sprite's antialiased alpha.
    samples=[]
    for frame in frames:
        bg=Image.new('RGBA',(W,H),'#f0f0f0'); bg.alpha_composite(Image.fromarray(frame,'RGBA'))
        samples.append(bg.convert('RGB').resize((272,362),Image.Resampling.BILINEAR))
    montage=Image.new('RGB',(272,362*len(samples)))
    for i,im in enumerate(samples): montage.paste(im,(0,362*i))
    palette=montage.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    indexed=[]
    for frame in frames:
        rgb=Image.new('RGBA',(W,H),'#f0f0f0'); rgb.alpha_composite(Image.fromarray(frame,'RGBA'))
        p=rgb.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE)
        indexed.append(p)
    indexed[0].save(OUT/filename,save_all=True,append_images=indexed[1:],duration=durations,loop=0,disposal=2,optimize=False)

save_gif('shocked_blink.gif',[BASE,out,BASE,out,BASE],[1100,130,1300,130,1100])
save_gif('shocked_mouth.gif',[BASE,talk,BASE,talk,BASE],[240,220,180,260,900])
save_gif('shocked_combined.gif',[BASE,talk,BASE,both,BASE,talk,both,talk,BASE],[450,220,300,130,430,220,130,240,1100])

# Review artifacts: source/donor and final result at enlarged eye scale, feature mask, change boundary.
box=(455,112,603,176); scale=8
views=[]
for arr in (BASE,DONOR,out):
    c=Image.fromarray(arr,'RGBA').crop(box)
    bg=Image.new('RGBA',c.size,'#eeeeee'); bg.alpha_composite(c)
    views.append(bg.convert('RGB').resize((c.width*scale,c.height*scale),Image.Resampling.NEAREST))
canvas=Image.new('RGB',(views[0].width*3,views[0].height+30),'#f7f7f7')
for i,(title,im) in enumerate(zip(('Source','Donor','Transplant'),views)):
    canvas.paste(im,(i*im.width,30)); ImageDraw.Draw(canvas).text((i*im.width+5,6),title,fill='#111')
canvas.save(OUT/'eyes_review.png')
base_bg=Image.new('RGBA',(W,H),'#eee'); base_bg.alpha_composite(Image.fromarray(BASE,'RGBA'))
arr=np.array(base_bg)
for c,val in enumerate((45,220,70)):
    arr[:,:,c][mask>0]=np.uint8(arr[:,:,c][mask>0]*.55+val*.45)
Image.fromarray(arr,'RGBA').crop(box).resize((box[2]-box[0] and (box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST).save(OUT/'feature_mask.png')
changed_img=Image.fromarray(changed.astype('uint8')*255)
boundary=changed & (np.asarray(changed_img.filter(ImageFilter.MinFilter(3)))==0)
arr=np.array(base_bg); arr[boundary]=[0,255,0,255]
Image.fromarray(arr,'RGBA').crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST).save(OUT/'changed_boundary.png')
print({'dimensions': [W,H], 'blink_changed_pixels': int(changed.sum()), 'blink_outside_mask_pixels': int(np.count_nonzero(changed & (mask==0))), 'alpha_identical': bool(np.array_equal(out[:,:,3],BASE[:,:,3])), 'mouth_skin_offset': skin_offset.tolist(), 'talk_changed_pixels': int(np.count_nonzero(np.any(talk[:,:,:3]!=BASE[:,:,:3],axis=2))), 'combined_gifs': 3})

finish_animation(OUT, ROOT/'static/sprites/03_shocked.png',
    {'idle': BASE, 'blink': out, 'talking': talk, 'blink_talking': both},
    {'idle': np.zeros((H, W), bool), 'blink': mask > 0,
     'talking': mouth_weight > 0, 'blink_talking': (mask > 0) | (mouth_weight > 0)},
    inputs=[HERE/'assets/eyes_closed_patch.png', HERE/'assets/open_mouth_patch.png'],
    scripts=[Path(__file__)], reviews=['eyes_review.png', 'feature_mask.png', 'changed_boundary.png'])
