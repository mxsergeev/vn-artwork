"""Diagnostic registration of expression donors to the document-reading master.

Candidate-only tooling: do not publish, do not modify the neutral master.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MASTER = ROOT / "static/poses/document_reading/neutral.png"
OUT = HERE / "candidate_review"
OUT.mkdir(exist_ok=True)


def load(p):
    return np.asarray(Image.open(p).convert("RGBA"))


master = load(MASTER)
assert master.shape == (1448,1086,4)
box = (480, 90, 686, 260)
head = (409, 5, 709, 280)


def align_to_master(donor, label):
    # Restrict correspondences to stable head and hair detail; expressions are free to change.
    def keypoints(im):
        x0,y0,x1,y1=head
        grey=cv2.cvtColor(im[y0:y1,x0:x1,:3], cv2.COLOR_RGB2GRAY)
        sift = cv2.SIFT_create(nfeatures=3500, contrastThreshold=0.012)
        kp,des=sift.detectAndCompute(grey,None)
        for p in kp: p.pt = (p.pt[0]+x0,p.pt[1]+y0)
        return kp,des
    src_kp,src_d=keypoints(master)
    don_kp,don_d=keypoints(donor)
    matcher=cv2.BFMatcher()
    paired=matcher.knnMatch(don_d,src_d,k=2)
    good=[m for m,n in paired if m.distance < 0.77*n.distance]
    D=np.float32([don_kp[m.queryIdx].pt for m in good])
    S=np.float32([src_kp[m.trainIdx].pt for m in good])
    M,inliers=cv2.estimateAffinePartial2D(D,S,method=cv2.RANSAC,ransacReprojThreshold=2.5,confidence=.995)
    if M is None:raise RuntimeError(label+" insufficient registration")
    keep=inliers.ravel()>0
    print(label,"matches",len(good),"inliers",int(keep.sum()),"matrix",M.tolist())
    residual=np.linalg.norm((D[keep] @ M[:,:2].T + M[:,2])-S[keep], axis=1)
    print(label,"residual median",float(np.median(residual)), "maximum",float(np.max(residual)))
    h,w=master.shape[:2]
    rgba = cv2.warpAffine(donor,M,(w,h),flags=cv2.INTER_LINEAR)
    return rgba,M,D[keep],S[keep]


def shown(im, crop=box, magnification=3):
    part = Image.fromarray(im).crop(crop).convert("RGBA")
    bg=Image.new("RGBA",part.size,"#eeeeee")
    bg.alpha_composite(part)
    return bg.convert("RGB").resize((part.width*magnification,part.height*magnification),Image.Resampling.NEAREST)



def polygon_mask(points):
    out = np.zeros(master.shape[:2], np.uint8)
    cv2.fillPoly(out,[np.array(points,np.int32)],255)
    return out


# Regions independently measured against the native master; not copied from other poses.
LEFT_EYE=[(536,151),(542,148),(554,149),(568,150),(579,148),(588,148),
          (592,156),(590,172),(586,182),(575,185),(557,185),(542,182),
          (537,175),(536,162)]
RIGHT_EYE=[(592,153),(600,148),(612,148),(625,145),(632,148),(635,155),
           (634,169),(631,177),(626,184),(605,185),(596,179),(591,168)]
# All mouth selection vertices are inside the master jawline. Never copy donor hair.
MOUTH=[(553,202),(558,199),(572,198),(589,198),(596,201),(596,207),
       (592,214),(586,219),(572,222),(559,218),(553,211)]

def skin_pixels(rgb):
    arr=rgb.astype(np.int16)
    r,g,b=arr[:,:,0],arr[:,:,1],arr[:,:,2]
    return (r>145)&(g>110)&(b>89)&(r-g>10)&(g-b>3)&(r-g<90)

def transplant(source, aligned, name):
    result=source.copy()
    regions = [("left_eye",LEFT_EYE),("right_eye",RIGHT_EYE),("mouth",MOUTH)]
    complete=np.zeros(source.shape[:2],np.uint8)
    stage_names=[]
    for region_name, points in regions:
        mask=polygon_mask(points)
        complete=cv2.bitwise_or(complete,mask)
        clean=(mask>0)&skin_pixels(source[:,:,:3])&skin_pixels(aligned[:,:,:3])
        # Choose clean skin from outer portion; exclude eyelash and mouth strokes.
        clean &= (np.min(source[:,:,:3],axis=2)>95)&(np.min(aligned[:,:,:3],axis=2)>95)
        if clean.sum()>12:
            delta=np.median(source[:,:,:3][clean].astype(float)-aligned[:,:,:3][clean].astype(float),axis=0)
        else: delta=np.zeros(3)
        delta=np.clip(delta,-9,9)
        print(name,region_name,"skin pixel count",int(clean.sum()),"RGB bias",delta.tolist())
        corrected=aligned[:,:,:3].astype(np.float32).copy()
        donor_skin=skin_pixels(aligned[:,:,:3])
        corrected[donor_skin]=np.clip(corrected[donor_skin]+delta,0,255)
        # Full coverage through the old/new features; feather only along clean-skin boundary.
        # Distance transform works within the polygon without writing outside it.
        distance=cv2.distanceTransform(mask,cv2.DIST_L2,3)
        a=np.clip(distance/3.0,0,1)[:,:,None]
        result[:,:,:3]=np.rint(result[:,:,:3].astype(float)*(1-a)+corrected*a).astype(np.uint8)
        stage_names.append((region_name,result.copy()))
    assert np.array_equal(result[:,:,3],source[:,:,3])
    changed=np.any(result[:,:,:3]!=source[:,:,:3],axis=2)
    assert not (changed & (complete==0)).any()
    Image.fromarray(result).save(OUT/(name+".png"))
    # Mask preview shows exactly the intended replacement footprint.
    highlight=source.copy()
    hint=complete>0
    highlight[:,:,:3][hint]=(source[:,:,:3][hint].astype(float)*0.45 + np.array([40,245,60])*.55).astype("uint8")
    Image.fromarray(highlight).crop(box).save(OUT/(name+"_mask_face.png"))
    return result,highlight,stage_names

all_panels=[("Neutral",shown(master))]
for name in ("happy","shocked"):
    donor=load(HERE/"assets"/(name+"_donor.png"))
    aligned,M,D,S=align_to_master(donor,name)
    final,mask,stages=transplant(master,aligned,name)
    all_panels.extend([("Original "+name,shown(donor)),("Aligned "+name,shown(aligned))])
    # 50% overlap makes double contours in unchanged anatomy visible.
    overlay=master.copy()
    overlay[:,:,:3]=np.clip(master[:,:,:3].astype(float)*.5 + aligned[:,:,:3].astype(float)*.5,0,255).astype("uint8")
    all_panels.append(("Overlay "+name,shown(overlay)))
    all_panels.extend([("Final "+name,shown(final)),("Mask "+name,shown(mask))])

    # A fixed-coordinate diagnostic of the actual donor, selection and delivered sprite.
    eye_crop=(527,134,646,194)
    lip_crop=(544,190,618,232)
    panels = [("source",master),("registered donor",aligned),("selected",mask),("final",final)]
    for part,rect in [("eyes",eye_crop),("mouth",lip_crop)]:
        zz=6
        panel_w=(rect[2]-rect[0])*zz
        panel_h=(rect[3]-rect[1])*zz
        review=Image.new("RGB",(panel_w*4,panel_h+22),"#eeeeee")
        writer=ImageDraw.Draw(review)
        for j,(label,art) in enumerate(panels):
            review.paste(shown(art,crop=rect,magnification=zz),(panel_w*j,22))
            writer.text((j*panel_w+7,5),label,fill="black")
        review.save(OUT/(name+"_"+part+"_review.png"))
    Image.fromarray(aligned).crop(box).save(OUT/(name+"_aligned_face.png"))
    # Diagnostic anchor/match marks on the source and aligned donor, sample for visual checking.
    marks=shown(master,crop=head,magnification=2)
    d=ImageDraw.Draw(marks)
    for xy in S[:50]:
        x,y=xy
        d.ellipse((2*(x-head[0])-2,2*(y-head[1])-2,2*(x-head[0])+2,2*(y-head[1])+2), fill="#17cf4d")
    marks.save(OUT/(name+"_matches.png"))

width=max(p.width for _,p in all_panels)
height=max(p.height for _,p in all_panels)
rows=(len(all_panels)+3)//4
board=Image.new("RGB",(width*4,(height+12)*rows),"#eeeeee")
draw=ImageDraw.Draw(board)
for i,(title,im) in enumerate(all_panels):
    x=(i%4)*width;y=(i//4)*(height+12)
    board.paste(im,(x,y+12))
    draw.text((x+8,y),title,fill="#000000")
board.save(OUT/"registration_compare.png")
print("saved", sorted(p.name for p in OUT.glob("*.png")))
