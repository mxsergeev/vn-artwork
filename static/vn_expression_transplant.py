#!/usr/bin/env python3
"""Transplant eight facial expressions onto an unchanged original transparent VN sprite.

Requires Pillow, numpy, and opencv-python.
Put `Melancholic Corporate Sci-Fi Officer.png` and
`anime_character_expression_sheet_grid.png` in the same directory as this script.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'vn_expression_sprites'
OUT.mkdir(exist_ok=True)

original = np.asarray(Image.open(ROOT / 'Melancholic Corporate Sci-Fi Officer.png').convert('RGBA'))
sheet = np.asarray(Image.open(ROOT / 'anime_character_expression_sheet_grid.png').convert('RGB'))
assert original.shape == (1448,1086,4)
assert sheet.shape == (1122,1402,3)
H,W = original.shape[:2]
# Aligned from corresponding source and target eyes, mouth, chin and earpiece.
affine = np.array([[.6674,-.02563,418.8],[.02563,.6674,-7.6]],np.float32)
# Face-only mask: extend outside brows; fade out before original chin/neck.
poly = np.array([(144,147),(184,139),(233,143),(260,158),(272,182),
                 (276,225),(260,270),(242,294),(217,312),(184,314),
                 (153,297),(128,283),(105,265),(92,244),(86,218),
                 (83,187),(104,160)],np.int32)
source_mask = np.zeros((561,350),np.uint8)
cv2.fillPoly(source_mask,[poly],255)
source_mask = cv2.GaussianBlur(source_mask,(0,0),5)
mask = cv2.warpAffine(source_mask,affine,(W,H),flags=cv2.INTER_LINEAR).astype(np.float32)/255.
mask = np.clip(mask,0,1)

# Match palette using corresponding skin samples from unmodified neutral portraits.
sample_xy = [(140,257),(162,277),(237,277),(182,310),(210,265),
             (178,181),(208,162),(153,245),(239,234),(206,272)]
sample_deltas=[]
for x,y in sample_xy:
    dx,dy=np.round(affine@np.array([x,y,1])).astype(int)
    sample_deltas.append(original[dy,dx,:3].astype(np.float32)-sheet[y,x,:3].astype(np.float32))
color_offset=np.median(np.array(sample_deltas),axis=0)

names = ['neutral_worried','happy','shocked','pouty','angry','embarrassed',
         'sad','strained_smile']

font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path,22) if Path(font_path).exists() else ImageFont.load_default()
preview = Image.new('RGB',(4*412,2*448),(241,241,241))
full_preview = Image.new('RGB',(4*400,2*570),(241,241,241))
qa=[]
for idx,name in enumerate(names):
    col,row=idx%4,idx//4
    # Grid separator columns are at 349, 701, 1053. All portraits have fixed
    # close-up framing and same 561-pixel row height.
    start_x=round(col*350.5)
    panel = sheet[row*561:(row+1)*561,start_x:start_x+350]
    assert panel.shape == (561,350,3)
    warped = cv2.warpAffine(panel,affine,(W,H),flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_CONSTANT)
    matched = np.clip(warped.astype(np.float32)+color_offset,0,255)
    output=original.copy()
    output[:,:,:3] = np.clip(original[:,:,:3].astype(np.float32)*(1-mask[:,:,None])+
                             matched*mask[:,:,None],0,255).astype(np.uint8)
    outpath = OUT / f'{idx+1:02d}_{name}.png'
    Image.fromarray(output).save(outpath,optimize=True)

    # Automated QA: original silhouette and alpha bit-for-bit; no changed
    # pixel outside facial patch. In particular, no edits to shoulders.
    unchanged_alpha = np.array_equal(output[:,:,3],original[:,:,3])
    changed = np.any(output[:,:,:3] != original[:,:,:3],axis=2)
    illegal = np.count_nonzero(changed & (mask==0))
    changed_transparent = np.count_nonzero(changed & (original[:,:,3]==0))
    changed_outside_head = np.count_nonzero(changed[225:])
    assert unchanged_alpha and illegal==0 and changed_transparent==0 and changed_outside_head==0, (name,illegal,changed_transparent,changed_outside_head)
    ys,xs=np.where(changed)
    qa.append({'expression':name,'size':[W,H],'alpha_unchanged':unchanged_alpha,
               'changed_transparent_pixels':int(changed_transparent),
               'changed_outside_face_pixels':int(illegal),
               'modified_region_bbox_xyxy':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]})

    # Large, legible face previews; transparency composited only for presentation.
    face = Image.fromarray(output).crop((434,64,640,268)).resize((412,408),Image.Resampling.LANCZOS)
    bg=Image.new('RGBA',face.size,(241,241,241,255)); bg.alpha_composite(face)
    px,py=col*412,row*448
    preview.paste(bg.convert('RGB'),(px,py))
    d=ImageDraw.Draw(preview)
    d.text((px+10,py+410),name.replace('_',' ').title(),fill=(36,36,36),font=font)

    # Full-figure preview, downsampled, with generous margins.
    thumb=Image.fromarray(output).resize((368,491),Image.Resampling.LANCZOS)
    tbg=Image.new('RGBA',thumb.size,(241,241,241,255));tbg.alpha_composite(thumb)
    qx,qy=col*400+16,row*570+10
    full_preview.paste(tbg.convert('RGB'),(qx,qy))
    ImageDraw.Draw(full_preview).text((qx+12,qy+503),name.replace('_',' ').title(),fill=(36,36,36),font=font)

preview.save(ROOT/'vn_expression_faces_preview.png',optimize=True)
full_preview.save(ROOT/'vn_expression_fullbody_preview.png',optimize=True)
Image.fromarray(original).save(OUT/'00_original_unchanged.png',optimize=True)
(OUT/'QA_report.json').write_text(json.dumps({'method':'rigid alignment + face feather mask + median RGB skin palette correction',
                                               'color_offset_rgb':[round(float(v),2) for v in color_offset],
                                               'results':qa},indent=2),encoding='utf8')
print('Applied RGB palette offset:',np.round(color_offset,2))
print('Results:')
for x in qa:print(x)
