#!/usr/bin/env python3
"""Controlled donor-to-neutral localized transplant; requires cv2, numpy, Pillow."""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
S=R/'assets';O=R/'output';O.mkdir(exist_ok=True);S.mkdir(exist_ok=True)
TARGET=np.asarray(Image.open(R.parent.parent/'static'/'sprites'/'01_neutral_worried.png').convert('RGBA')).copy()
H,W=TARGET.shape[:2]; assert (W,H)==(1086,1448)

# fit corresponding eyelid centers for 2D similarity (scale 0.349+~3.4 degree clockwise)
# left: (132,234)->(485,145), right: (344,190)->(560,134)
blink_affine=np.float32([[0.349,-0.021,443.85],[0.021,0.349,60.65]])
# mouth source center 250,354 -> neutral 527.3,193.2
# match donor mouth to neutral mouth without modifying nose or chin
mouth_affine=np.float32([[0.380,0,438.3],[0,0.380,58.68]])

def poly_mask(polys):
    a=np.zeros((H,W),np.uint8)
    for poly in polys: cv2.fillPoly(a,[np.array(poly,dtype=np.int32)],255)
    return a

EYE_POLYS=[
[(461,150),(465,143),(470,138),(479,135),(491,135),(501,137),(509,141),(517,148),(518,156),(514,161),(504,165),(488,166),(477,163),(466,158)],
[(533,139),(535,131),(545,125),(555,122),(575,122),(586,125),(592,133),(592,145),(585,152),(576,157),(550,158),(539,151)]
]
# Exclude the external right lock and a thin forelock above the right eyelid.
HAIR_PROTECTION=[
[(592,120),(601,122),(604,139),(600,157),(594,173),(586,174),(589,157),(592,144)]
]
# Extra margin around original lips, but completely inside jawline.
MOUTH_POLY=[(506,193),(509,186),(518,182),(532,182),(543,183),(557,187),(563,191),(563,200),(557,205),(542,208),(523,209),(512,205),(507,200)]

def save_comp(name, arr): Image.fromarray(arr,'RGBA').save(O/name,optimize=True)

def make_feature(label,donor_filename,affine,polys,protection=[],margin=3.4,max_color_shift=38):
    donor=np.asarray(Image.open(S/donor_filename).convert('RGBA'))
    warp=cv2.warpAffine(donor[:,:,:3],affine,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
    rough=poly_mask(polys)
    protected=poly_mask(protection)
    # hard exclusion for hair, no feather over protected pixels
    effective=cv2.bitwise_and(rough,cv2.bitwise_not(protected))
    dist=cv2.distanceTransform(effective,cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    weight=np.clip((dist-0.6)/margin,0,1).astype(np.float32)
    weight[(rough==0)|(protected>0)|(TARGET[:,:,3]==0)]=0
    # estimate RGB skin correction on valid skin within mask at least 4 px away from changed lines
    # mask skin where donor and original are relatively bright and untextured
    y1,y2,x1,x2=(116,218,451,599) if label=='eyes' else (181,211,501,553)
    roi=(slice(y1,y2),slice(x1,x2))
    base=TARGET[roi][:,:,:3].astype(np.float32)
    src=warp[roi].astype(np.float32)
    sky=(base.min(2)>90)&(src.min(2)>90)&(base.mean(2)>140)&(src.mean(2)>140)
    # pixels outside feature with low absolute gradient likely skin
    grad=cv2.Sobel(cv2.cvtColor(TARGET[roi][:,:,:3],cv2.COLOR_RGB2GRAY),cv2.CV_32F,1,0,ksize=3)
    gy=cv2.Sobel(cv2.cvtColor(TARGET[roi][:,:,:3],cv2.COLOR_RGB2GRAY),cv2.CV_32F,0,1,ksize=3)
    grad2=np.hypot(grad,gy)
    sky &= grad2<80
    # only near feature, sample known surrounding skin band but avoid art lines
    band=cv2.dilate(rough[roi],np.ones((11,11),np.uint8))>0
    sky &= band
    diff=(base-src)[sky]
    if diff.shape[0]<5: raise RuntimeError(f'Insufficient skin samples {label}')
    delta=np.clip(np.median(diff,axis=0),-max_color_shift,max_color_shift)
    adjusted=np.uint8(np.clip(warp.astype(np.float32)+delta,0,255))
    # For visual fidelity of opaque source, preblend RGB but keep alpha bit-identical.
    result=TARGET.copy();mask=weight[:,:,None]
    result[:,:,:3]=np.uint8(np.clip(TARGET[:,:,:3].astype(np.float32)*(1-mask)+adjusted.astype(np.float32)*mask,0,255))
    overlay=np.zeros_like(TARGET);overlay[:,:,:3]=adjusted;overlay[:,:,3]=np.uint8(np.round(255*weight));overlay[overlay[:,:,3]==0,:3]=0
    changed=np.any(result[:,:,:3]!=TARGET[:,:,:3],2)
    assert not np.any(changed & (rough==0))
    assert not np.any(changed & (protected>0))
    assert not np.any(changed & (TARGET[:,:,3]==0))
    assert np.array_equal(result[:,:,3],TARGET[:,:,3])
    if label=='eyes': allowed=(slice(121,169),slice(458,590))
    else: allowed=(slice(186,210),slice(504,548))
    ys,xs=np.nonzero(changed)
    info={'label':label,'donor':donor_filename,'color_offset_rgb':np.round(delta,1).tolist(),'skin_samples':len(diff),'changed_pixels':int(changed.sum()),'changed_bbox_xyxy':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'modified_outside_mask':0,'modified_protected_hair':0,'source_alpha_preserved':True,'affine':affine.tolist()}
    save_comp(f'{label}_overlay.png',overlay);save_comp(f'{label}_fullframe.png',result)
    Image.fromarray(np.dstack((adjusted,np.uint8(weight*255))),'RGBA').crop((445,111,605,215)).save(O/f'{label}_warped_face_area.png')
    return result,overlay,info,weight,adjusted,rough,protected

blink=make_feature('eyes','left_donor_face.png',blink_affine,EYE_POLYS,HAIR_PROTECTION,margin=3.2)
speech=make_feature('mouth','right_donor_face.png',mouth_affine,[MOUTH_POLY],margin=3.2)
# combine two edits using independent exact source RGB operations rather than double alpha blending
both=blink[0].copy(); w=speech[3][:,:,None];both[:,:,:3]=np.uint8(np.clip(both[:,:,:3].astype(np.float32)*(1-w)+speech[4].astype(np.float32)*w,0,255)); save_comp('eyes_closed_mouth_open_fullframe.png',both)
save_comp('neutral_original.png',TARGET)
qa={'size':[W,H],'features':[blink[2],speech[2]],'independent_masks_nonoverlapping':bool(np.count_nonzero((blink[3]>0)&(speech[3]>0))==0),'identical_fullframe_alpha_all_four_states':all(np.array_equal(x[:,:,3],TARGET[:,:,3]) for x in [blink[0],speech[0],both])}
(O/'qa_report.json').write_text(json.dumps(qa,indent=2))

# previews, use nearest to expose seams
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
def panel(outname,bbox,subjects,mult=5,withmask=False):
    tw=(bbox[2]-bbox[0])*mult;th=(bbox[3]-bbox[1])*mult
    dst=Image.new('RGB',(tw*len(subjects),th+37),(239,239,239));draw=ImageDraw.Draw(dst)
    for i,(name,arr) in enumerate(subjects):
        cropped=Image.fromarray(arr).crop(bbox);bg=Image.new('RGBA',cropped.size,(241,241,241,255));bg.alpha_composite(cropped)
        dst.paste(bg.convert('RGB').resize((tw,th),Image.Resampling.NEAREST),(tw*i,37))
        draw.text((tw*i+12,5),name,font=font,fill=(30,30,30))
    dst.save(O/outname)
panel('eyes_comparison_6x.png',(447,110,600,174), [('Original',TARGET),('New donor',blink[0])],6)
panel('mouth_comparison_8x.png',(493,176,557,216), [('Original',TARGET),('Talking',speech[0])],8)
panel('four_states_4x.png',(444,94,611,216), [('Original',TARGET),('Blink',blink[0]),('Talk',speech[0]),('Both',both)],4)
# gif representing state transitions, scale to useful preview resolution
from PIL import Image
frames=[]
for arr,duration in [(TARGET,950),(speech[0],180),(TARGET,170),(speech[0],180),(TARGET,1000),(blink[0],120),(TARGET,300),(speech[0],140),(both,120),(speech[0],180),(TARGET,1100)]:
    im=Image.fromarray(arr).crop((415,20,667,310)); bg=Image.new('RGBA',im.size,'#f2f2f2'); bg.alpha_composite(im);frames.append(bg.convert('RGB').resize((756,870),Image.Resampling.LANCZOS))
frames[0].save(O/'animation_preview.gif',save_all=True,append_images=frames[1:],duration=[950,180,170,180,1000,120,300,140,120,180,1100],loop=0,optimize=True)
print(json.dumps(qa,indent=2))
